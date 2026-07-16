# Domain 23, Chapter 23B — Advanced OSINT Tradecraft, Counter-Intelligence, and Social Engineering Defense

> **Scope.** Advanced OSINT methodology: Maltego transform architecture (custom transforms via Python TRX/Java API, Maltego CE vs XL vs commercial licensing, graph analysis algorithms for infrastructure pivoting, entity weight and link analysis, transform hub ecosystem, custom entity types), SOCMINT (social media intelligence — automated collection frameworks, bot network fingerprinting, coordinated inauthentic behavior detection, influence operation attribution, platform API restrictions post-2023 and scraping alternatives), dark web intelligence (Tor hidden services enumeration via OnionScan/Ahmia/TORCH, .onion indexing and correlation, dark web marketplace tradecraft — credential shops, initial access brokers, RaaS affiliate programs, HUMINT integration with technical collection, operational security for dark web researchers), deep web and paste site monitoring (Pastebin/GitHub gists/Ghostbin/Rentry, automated leak detection with TheHive/Cortex analyzers, regex-based credential and secrets scanning). Advanced infrastructure analysis: passive DNS (SecurityTrails historical DNS, Farsight DNSDB, SilentPush), infrastructure pivoting methodology (IP to ASN to netblock to linked domains to co-hosted infrastructure), WHOIS privacy piercing (historical WHOIS correlation, registrant email clustering, registration timing analysis), TLS certificate intelligence (JA3/JA4 fingerprinting for server and client profiling, certificate transparency log monitoring for brand protection and subdomain discovery, Censys certificate search, JARM active fingerprinting), hosting infrastructure fingerprinting (cloud provider identification, CDN detection, shared hosting correlation, IP reputation feeds). OSINT for attack surface management: continuous external attack surface discovery (ProjectDiscovery toolchain — subfinder/httpx/nuclei/katana/chaos, commercial ASM platforms — CrowdStrike Falcon Surface, Microsoft Defender EASM, Mandiant ASM, Palo Alto Cortex Xpanse), exposed credential monitoring (breach databases, stealer log analysis, combo list correlation, Genesis Market/Russian Market successors, InfoStealer malware output parsing), exposed API discovery (Swagger/OpenAPI endpoint discovery, GraphQL introspection exploitation, undocumented API enumeration via fuzzing), cloud asset discovery (S3 bucket enumeration, Azure blob storage, GCS public dataset exposure, public Lambda/Cloud Function URLs, exposed Kubernetes dashboards and etcd). Counter-OSINT and operational security: minimizing organizational digital footprint (DNS record hygiene, CT log monitoring and pre-certificate strategies, metadata scrubbing from documents and images, employee social media policy enforcement), counter-reconnaissance detection (honeypot domains and canary DNS records, login page monitoring for credential stuffing detection, enumeration detection through rate limiting and behavioral analysis, deception technology integration), personal OPSEC for security practitioners (persona separation, secure communication, device compartmentalization, travel security). Social engineering defense architecture: email security gateway architecture (Proofpoint, Mimecast, Microsoft Defender for Office 365 — sandboxing, URL rewriting, attachment detonation, DMARC enforcement at p=reject, ARC for mailing lists), phishing simulation programs (design methodology, behavioral metrics, progressive difficulty frameworks, reporting culture), SE-resistant authentication (FIDO2/WebAuthn deep dive — attestation types, assertion flow, resident keys, passkeys, platform vs roaming authenticators, conditional UI), insider threat programs (behavioral indicators, UBA/UEBA platforms, DLP integration, legal and privacy frameworks), physical security convergence (badge system monitoring, CCTV analytics with behavioral AI, visitor management, secure facility design, SCIF requirements). Influence operations and disinformation: nation-state information operations (Russian IRA/Doppelganger campaigns, Chinese Spamouflage/50 Cent Army, Iranian IUVM, coordinated inauthentic behavior detection with Graphika/Stanford Internet Observatory methodologies), deepfake detection and authentication (audio and video deepfake generation techniques, detection via temporal inconsistency and frequency-domain analysis, media provenance with C2PA/Content Credentials, synthetic media threats to BEC and vishing), brand impersonation and typosquatting defense (CT log monitoring automation, domain monitoring services, UDRP and URS takedown processes, phishing kit detection).

**Audience.** Security architects, threat intelligence analysts, red team operators, OSINT practitioners, SOC leadership, and CISO-level decision makers responsible for social engineering defense programs and external attack surface management.

**Prerequisites.** Domain 23 Chapter 23A (social engineering tactics — pretexting, spear-phishing, MFA fatigue, SIM swapping, vishing, BEC, consent phishing, USB attacks, physical SE; OSINT fundamentals — domain/DNS recon, subdomain enumeration, network scanning, email recon, social media OSINT, image OSINT, source code OSINT, Maltego/SpiderFoot/recon-ng basics, physical OSINT). Familiarity with Domain 9 Chapter 9A (DNS and TLS fundamentals) and Domain 8 Chapter 8A (web security, OAuth flows) is assumed.

---

## 1. Advanced OSINT Methodology

### 1.1 Maltego transform architecture and custom development

Chapter 23A introduced Maltego as a graph-based visual link analysis platform. This section examines the internal architecture that makes Maltego powerful for infrastructure pivoting and how to extend it beyond the built-in transform set. Maltego operates on a data model consisting of entities (nodes in the graph — domains, IP addresses, email addresses, persons, organizations, phone numbers, hashes, and dozens of other types) and transforms (functions that take one entity type as input and produce one or more entities as output). The transform is the atomic unit of OSINT automation in Maltego: a transform takes a domain entity and returns its DNS A records as IP address entities; another transform takes an IP address entity and returns its WHOIS registration as a registrant entity; a third takes a registrant email and returns other domains registered with the same email. By chaining transforms, the analyst builds a graph that reveals relationships invisible in tabular data — the same registrant email across twenty domains, a single IP address hosting infrastructure for three apparently unrelated campaigns, a phone number linking a persona to a corporate registration.

The transform execution architecture follows a client-server model. When the analyst runs a transform in the Maltego client (the desktop application), the client serializes the input entity (including its properties — for a domain entity, properties include the domain name, DNS records, creation date, and any analyst-added notes) into an XML message and sends it to a Transform Distribution Server (TDS). The TDS routes the request to the appropriate transform server — which may be Paterva's (now Maltego Technologies') cloud infrastructure for built-in transforms, a third-party transform hub provider (such as Shodan, VirusTotal, Have I Been Pwned, or PassiveTotal/RiskIQ), or a locally-hosted transform server for custom transforms. The transform server processes the input, queries its data source (an API, a database, a web scraper), and returns the results as XML entities. The Maltego client renders these new entities as nodes in the graph, with edges connecting them to the input entity.

The Transform Hub is the ecosystem that makes Maltego extensible. As of 2025, the Transform Hub includes over forty data providers: Shodan (network scanning data — converts IP addresses to open ports, banners, and vulnerabilities), VirusTotal (malware and URL scanning — converts file hashes, domains, and IPs to detection results and behavioral indicators), Have I Been Pwned (breach data — converts email addresses to breach records), Censys (certificate and host scanning), SecurityTrails (historical DNS and WHOIS), Social Links (social media intelligence — converts usernames and phone numbers to social media profiles), Pipl (people search — converts names and emails to identity records), and many others. Each hub integration requires a subscription (both to the data provider's API and, for some hubs, a separate Maltego hub license). The commercial licensing model is tiered: Maltego CE (Community Edition) provides limited transforms and a maximum of twelve entities per transform result; Maltego Pro provides unlimited entities and access to the full Transform Hub; Maltego Enterprise adds collaboration features (shared graphs, team workspaces), API access for automation, and integration with SIEM/SOAR platforms.

For bespoke OSINT requirements, analysts write custom transforms. The primary development framework is the Maltego TRX (Transform) library for Python, which provides a structured interface for building local transforms. A custom transform is a Python script that inherits from the `Transform` base class and implements a `do_transform` method. The method receives the input entity, performs whatever data collection logic the analyst needs (API calls, database queries, web scraping, file parsing), and returns output entities via the `MaltegoTransform` response object. The transform is registered with the Maltego client via a local transform server (iTDS — Internal Transform Distribution Server) or directly as a local transform (pointing the client to the Python script). The TRX library handles XML serialization/deserialization, entity property mapping, and error handling.

A concrete example illustrates the pattern. Suppose an analyst needs a transform that takes a domain entity, queries the SecurityTrails API for historical DNS records, and returns all IP addresses the domain has ever resolved to (not just current resolution — historical passive DNS). The following Python TRX transform implements this:

```python
# transforms/HistoricalDNS.py — Maltego TRX custom transform
# Queries SecurityTrails API for historical A records of a domain entity.

import requests
from maltego_trx.maltego import MaltegoMsg, MaltegoTransform
from maltego_trx.transform import DiscoverableTransform

SECTRAILS_API_KEY = "__REDACTED__"  # load from env or vault in production
SECTRAILS_BASE = "https://api.securitytrails.com/v1"


class HistoricalDNS(DiscoverableTransform):
    """
    Input:  maltego.Domain
    Output: maltego.IPv4Address (one per unique historical A record)
    """

    @classmethod
    def create_entities(cls, request: MaltegoMsg, response: MaltegoTransform):
        domain = request.Value  # e.g. "target.example.com"

        headers = {"apikey": SECTRAILS_API_KEY, "Accept": "application/json"}
        url = f"{SECTRAILS_BASE}/history/{domain}/dns/a"
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()

        seen_ips = set()
        for record in data.get("records", []):
            for value in record.get("values", []):
                ip = value.get("ip")
                if ip and ip not in seen_ips:
                    seen_ips.add(ip)
                    entity = response.addEntity("maltego.IPv4Address", ip)
                    entity.addProperty(
                        "first_seen",
                        "First Seen",
                        "loose",
                        record.get("first_seen", "unknown"),
                    )
                    entity.addProperty(
                        "last_seen",
                        "Last Seen",
                        "loose",
                        record.get("last_seen", "unknown"),
                    )
                    # Link analysis weight: more recent records get higher weight
                    entity.setLinkLabel(
                        f"{record.get('first_seen','?')} → {record.get('last_seen','?')}"
                    )
                    entity.setWeight(100)  # max weight for direct DNS evidence
```

The transform server is started with the TRX CLI, which registers all discoverable transforms and exposes them on a local HTTP endpoint:

```bash
# Install the TRX library and start the local transform server
pip install maltego-trx
python -m maltego_trx.transform project --name HistoricalDNSProject
cd HistoricalDNSProject
# Place HistoricalDNS.py in the transforms/ directory, then:
python project.py runserver --port 8080
# Register in Maltego client: New Local Transform → URL = http://localhost:8080/run/HistoricalDNS
```

The `setWeight()` call in the code above controls entity weighting in the graph. Maltego uses entity weight (0-100) and link weight to drive its analytical algorithms. When running centrality analysis, entities with higher weights and more weighted connections score higher as hub nodes. When the analyst applies the "shortest path" algorithm between two entities, the path traversal respects link weights — a path through high-weight links (shared registrant email, same WHOIS organization) is preferred over a path through low-weight links (shared hosting IP on a large CDN). Configuring weights programmatically in custom transforms ensures that the automated graph analysis produces analytically meaningful results rather than treating all connections as equal.

The analyst then runs a second transform on each historical IP address — perhaps a reverse DNS lookup or a WHOIS transform — to identify other domains that shared the same IP during the same time period. This temporal-overlap analysis is how infrastructure pivoting chains are built: domain A resolved to IP X from January to March 2024; during that same period, domain B (a known command-and-control domain from a threat intelligence feed) also resolved to IP X; therefore domain A is likely associated with the same threat actor. This kind of temporal pivot is impossible with simple point-in-time DNS lookups and is the core value of passive DNS data in intelligence analysis.

The Java-based transform API (the original Maltego transform development kit) remains available for environments where transforms need to integrate with Java-based enterprise systems (LDAP directories, Java-based SIEM APIs, Hadoop/Spark clusters for large-scale data processing), but the Python TRX library has become the standard for new custom transform development due to its lower complexity and the availability of Python libraries for virtually every OSINT data source.

Graph analysis within Maltego goes beyond visual inspection. The platform provides algorithmic analysis capabilities including shortest-path computation (finding the minimum number of link hops between two entities — useful for understanding how closely related two apparently separate infrastructure elements are), centrality analysis (identifying entities with the most connections — the hub nodes that tie a campaign's infrastructure together), clustering (grouping entities by connectivity density — revealing operational groupings within a large graph), and link weighting (assigning confidence values to entity relationships based on evidence strength — a shared WHOIS registrant email is a stronger link than a shared hosting IP, which might be coincidental on shared hosting). These algorithms transform a visual graph from an overwhelming hairball of nodes and edges into an analytically meaningful structure where the most important relationships are quantified and ranked.

### 1.2 Social media intelligence (SOCMINT)

Social media intelligence collection has undergone a fundamental shift since 2023. The major platforms — X (formerly Twitter), Meta (Facebook/Instagram), LinkedIn, TikTok, and Reddit — have systematically restricted or eliminated their public APIs, dramatically increasing the cost and difficulty of programmatic data collection. Twitter's API v2, which replaced the free Academic Research API track, introduced pricing tiers that start at $100/month for Basic access (limited to 10,000 tweets/month read access) and reach $42,000/month for Enterprise access. Meta's CrowdTangle, the primary tool for researchers studying Facebook and Instagram content, was shut down on 14 August 2024 and replaced with the Meta Content Library, which requires academic affiliation and a formal application process. LinkedIn has aggressively pursued legal action against scrapers (hiQ Labs v. LinkedIn, which was remanded by the Supreme Court and ultimately settled in LinkedIn's favor), and its API provides minimal public data access. TikTok's Research API, launched under regulatory pressure, provides limited access to public video metadata but excludes comments, user profiles, and network data.

These API restrictions have pushed SOCMINT collection toward three alternative approaches, each with distinct operational and legal considerations. The first is browser automation using tools like Playwright, Puppeteer, or Selenium to simulate human browsing behavior and extract data from rendered pages. This approach is technically reliable for small-scale collection but faces challenges at scale: platforms deploy bot detection (CAPTCHAs, browser fingerprinting via JavaScript challenges, behavioral analysis of scroll patterns and click timing, and IP reputation checks against known datacenter and VPN ranges). Effective browser automation for SOCMINT requires rotating residential proxies, realistic browser fingerprints (canvas fingerprint randomization, WebGL renderer spoofing, timezone and language consistency), and human-like interaction patterns (randomized delays between actions, natural scroll velocities, session duration variation). Tools like undetected-chromedriver (a patched Chromium distribution that removes automation indicators such as `navigator.webdriver = true`) address some detection vectors, but the arms race between platforms and scrapers is continuous.

The following Playwright skeleton demonstrates the structural pattern for resilient SOCMINT collection with anti-detection measures. This is an architectural reference, not a turnkey scraper — production collectors require platform-specific selectors, authentication handling, and legal review:

```python
# socmint_collector.py — SOCMINT browser-automation skeleton (Playwright)
# Demonstrates anti-detection patterns; requires platform-specific adaptation.

import asyncio
import json
import random
from pathlib import Path
from playwright.async_api import async_playwright

PROXY_POOL = [
    "http://user:pass@resi-proxy-1.example.com:8080",
    "http://user:pass@resi-proxy-2.example.com:8080",
]
OUTPUT_DIR = Path("./collected_data")
OUTPUT_DIR.mkdir(exist_ok=True)


async def human_delay(min_ms: int = 800, max_ms: int = 3000) -> None:
    """Randomized delay simulating human interaction cadence."""
    await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)


async def collect_profile(playwright, target_url: str) -> dict:
    proxy = random.choice(PROXY_POOL)
    browser = await playwright.chromium.launch(
        headless=True,
        proxy={"server": proxy},
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
        ],
    )
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        timezone_id="America/New_York",
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    # Mask navigator.webdriver and other automation fingerprints
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    """)
    page = await context.new_page()
    await page.goto(target_url, wait_until="networkidle")
    await human_delay()

    # ---- Platform-specific extraction goes here ----
    # page_content = await page.content()
    # parse with BeautifulSoup / CSS selectors / XPath
    result = {"url": target_url, "status": "collected"}

    await browser.close()
    return result


async def main():
    targets = ["https://platform.example.com/user/target_handle"]
    async with async_playwright() as pw:
        for url in targets:
            data = await collect_profile(pw, url)
            out_file = OUTPUT_DIR / f"{hash(url)}.json"
            out_file.write_text(json.dumps(data, indent=2))
            await human_delay(2000, 5000)  # inter-target delay
```

The second approach leverages platform-specific unofficial APIs — the internal APIs that the platforms' own mobile applications and web frontends use. These APIs are undocumented, require reverse-engineering the platform's client application (inspecting network traffic from the mobile app using a proxy like mitmproxy or Burp Suite, then replicating the authentication flow and API call patterns), and are subject to change without notice. For X/Twitter, the GraphQL API that the web client uses provides more data than the official API v2 at no cost, but requires session cookies from an authenticated account and mimicking the web client's request headers (including the `x-csrf-token`, `authorization` bearer token derived from the session, and the `x-client-transaction-id`). For Instagram, the private API (used by the mobile app) returns full user profiles, follower/following lists, and post engagement data. For LinkedIn, the Voyager API (the internal API used by the LinkedIn web application) provides access to profile data, connection networks, and company information. Using these unofficial APIs carries legal risk (potential violation of the Computer Fraud and Abuse Act or equivalent legislation, terms-of-service violations, and potential civil liability), and the data obtained through them may not be admissible in legal proceedings depending on jurisdiction.

The third approach is purchasing access from commercial SOCMINT providers who have established data-sharing agreements with platforms or who aggregate data from multiple sources. Companies such as Brandwatch, Sprinklr, Meltwater, and Flashpoint/Echosec maintain large-scale social media data repositories and provide API access to their customers (typically under enterprise licensing with usage-based pricing). For security-specific SOCMINT, Flashpoint's Echosec platform and the now-ZeroFox platform provide social media monitoring focused on threat intelligence use cases — brand impersonation detection, executive threat monitoring, and exposure identification. These commercial platforms abstract away the collection challenges but introduce vendor lock-in and may not cover niche platforms (Telegram, Discord, 4chan, specialized forums) that are increasingly important for threat intelligence.

Bot network analysis and coordinated inauthentic behavior (CIB) detection represent the analytical dimension of SOCMINT. Bot networks on social media serve multiple purposes: amplifying messages (astroturfing), suppressing opposing messages (brigading), harvesting credentials (phishing via social media DMs), and establishing sock puppet identities for social engineering. Detecting bot accounts involves analyzing behavioral signals: posting frequency and temporal patterns (bot accounts often post at regular intervals or during time periods inconsistent with the account's claimed timezone), content originality (bots frequently repost or slightly modify content from other accounts), network structure (bot networks exhibit unusual connectivity patterns — many accounts following the same small set of accounts, or clusters of accounts that were all created within a short time window), linguistic patterns (automated translation artifacts, grammatically correct but semantically odd phrasing, repetitive sentence structures across accounts), and profile metadata (default profile pictures, incomplete biographies, creation dates clustering around specific periods). The Indiana University Observatory on Social Media (OSoMe) developed Botometer (formerly BotOrNot), a machine-learning classifier that scores Twitter/X accounts on a bot-likelihood scale based on over 1,200 features including user metadata, friends, network structure, temporal activity patterns, and content/language analysis. While Botometer's accuracy has degraded as bot operators adapt their tactics and as X's API restrictions limit the features available for classification, the analytical framework it established — multi-feature behavioral classification combining network, temporal, and content signals — remains the foundation for CIB detection.

Graph-based CIB detection uses network analysis to identify coordinated clusters. The following pattern constructs a co-amplification graph and extracts suspicious clusters using community detection:

```python
# cib_graph_analysis.py — Coordinated inauthentic behavior detection via
# co-amplification network analysis.  Requires: networkx, python-louvain.

import networkx as nx
import community as community_louvain  # python-louvain
from collections import defaultdict
from datetime import datetime, timedelta

def build_co_amplification_graph(
    posts: list[dict],
    window: timedelta = timedelta(seconds=60),
) -> nx.Graph:
    """
    Build undirected graph where nodes = accounts, edges = co-amplification
    within `window` of each other on the same content (URL, hashtag, etc.).
    `posts` schema: {"account_id", "shared_url", "timestamp"(ISO)}.
    """
    G = nx.Graph()
    # Group posts by shared URL/hashtag
    by_content: dict[str, list] = defaultdict(list)
    for p in posts:
        by_content[p["shared_url"]].append(p)

    for url, group in by_content.items():
        group.sort(key=lambda x: x["timestamp"])
        for i, p1 in enumerate(group):
            t1 = datetime.fromisoformat(p1["timestamp"])
            for p2 in group[i + 1 :]:
                t2 = datetime.fromisoformat(p2["timestamp"])
                if t2 - t1 > window:
                    break
                a, b = p1["account_id"], p2["account_id"]
                if a == b:
                    continue
                if G.has_edge(a, b):
                    G[a][b]["weight"] += 1
                else:
                    G.add_edge(a, b, weight=1)
    return G


def detect_clusters(G: nx.Graph, min_size: int = 5) -> list[set]:
    """Return Louvain communities with >= min_size accounts."""
    partition = community_louvain.best_partition(G, weight="weight")
    clusters: dict[int, set] = defaultdict(set)
    for node, comm_id in partition.items():
        clusters[comm_id].add(node)
    return [c for c in clusters.values() if len(c) >= min_size]


# Usage:
# G = build_co_amplification_graph(collected_posts)
# suspicious = detect_clusters(G, min_size=10)
# for cluster in suspicious:
#     print(f"Cluster of {len(cluster)} accounts: {cluster}")
```

Clusters of accounts that repeatedly amplify the same content within tight time windows — especially when the accounts share creation-date ranges and have sparse organic engagement — are strong CIB candidates. The analyst then manually validates the cluster by inspecting profile content, checking for copy-paste text patterns, and looking for shared infrastructure indicators (same link-shortener, same landing pages, same profile picture generation artifacts).

Influence operation detection at scale, as practiced by organizations like Graphika, the Stanford Internet Observatory (SIO), and the Atlantic Council's Digital Forensic Research Lab (DFRLab), combines SOCMINT collection with network analysis and content analysis. The methodology involves identifying seed accounts (known inauthentic accounts, typically identified through platform disclosures or investigative journalism), mapping their network connections (followers, following, mentions, retweets/reposts, reply chains), identifying clusters of accounts with similar behavioral patterns (co-creation, co-amplification, shared content sources), and then analyzing the content they produce and amplify to characterize the operation's objectives and probable attribution. The Stanford Internet Observatory's analysis of the Chinese Spamouflage network, for instance, identified over 4,000 accounts across X, Facebook, YouTube, and TikTok that were coordinated through shared content templates, synchronized posting times, and a common infrastructure of websites that hosted the source content. This kind of cross-platform analysis requires combining data from multiple collection sources and normalizing entity identifiers (a single operator might use different usernames on different platforms but share phone numbers, email addresses, profile images, or posting patterns that link the accounts).

### 1.3 Dark web intelligence

Conducting intelligence operations on Tor hidden services requires a fundamentally different approach from surface-web OSINT. The .onion addressing scheme uses the public key of the hidden service as its address (v3 .onion addresses are 56-character base32 encodings of the service's Ed25519 public key, an SHA-3 hash checksum, and a version byte), which means there is no centralized directory (no equivalent of DNS WHOIS or domain registrars) and no way to enumerate all hidden services by querying an authority. Hidden service discovery relies on a combination of indexing, crawling, monitoring, and human intelligence.

Indexing services aggregate known .onion addresses. Ahmia (ahmia.fi) is the most established Tor search engine, indexing .onion sites that do not explicitly opt out (via a `robots.txt` equivalent for Tor, the `x-onion-location` header). TORCH (TOR Search Engine) provides a larger but less curated index. Dark.fail and Dread (a Reddit-like forum operating as a hidden service) serve as directories for marketplace URLs, which change frequently as marketplaces rotate their onion addresses to evade law enforcement takedowns and DDoS attacks. OnionScan, developed by Sarah Jamie Lewis, is an automated scanner that probes .onion services for operational security failures: exposed Apache `mod_status` pages (revealing the server's real IP address through the `ServerName` directive), SSH fingerprints (which can be correlated with surface-web SSH scans from Shodan or Censys to identify the server's clearnet IP), PGP keys (whose key IDs and user IDs might be linked to clearnet identities), Bitcoin addresses (which can be traced through blockchain analysis), and EXIF metadata in hosted images (which might contain GPS coordinates or device identifiers). OnionScan's findings have been used in multiple law enforcement investigations to deanonymize hidden service operators.

OnionScan operates through the local Tor SOCKS proxy and produces structured JSON reports per scanned address. A typical scanning workflow:

```bash
# Ensure Tor is running and SOCKS5 proxy is available (default 127.0.0.1:9050)
systemctl start tor

# Scan a single .onion address — JSON output includes OPSEC findings
onionscan --jsonReport --simpleReport=false \
  http://exampleonionaddr.onion > scan_result.json

# Batch-scan a list of known addresses
while IFS= read -r addr; do
  echo "[*] Scanning: $addr"
  onionscan --jsonReport --simpleReport=false \
    --torProxyAddress 127.0.0.1:9050 \
    --timeout 120 \
    "http://${addr}" > "scans/${addr}.json" 2>&1
  sleep 5  # rate-limit to avoid overloading Tor circuits
done < onion_targets.txt

# Parse results for OPSEC failures — real IP exposure via Apache mod_status,
# SSH fingerprints, PGP keys, EXIF data, open directories, Bitcoin addresses
jq 'select(.identifierReport.emailAddresses != null)
    | {onion: .hiddenService, emails: .identifierReport.emailAddresses}' \
  scans/*.json

jq 'select(.identifierReport.bitcoinAddresses != null)
    | {onion: .hiddenService, btc: .identifierReport.bitcoinAddresses}' \
  scans/*.json

# Cross-reference discovered SSH fingerprints with Shodan
# to find the clearnet IP behind a hidden service
jq -r '.identifierReport.sshKey // empty' scans/*.json | while read -r fp; do
  echo "[*] Searching Shodan for SSH fingerprint: $fp"
  shodan search "ssh.fingerprint:${fp}" --fields ip_str,port,org
done
```

The cross-reference between OnionScan's SSH fingerprint output and Shodan/Censys surface-web scans is one of the most effective deanonymization techniques. If a hidden service operator runs SSH on the same server (a common OPSEC failure), the SSH host key fingerprint is identical on both the .onion service and the clearnet IP, creating a deterministic link between the anonymous and non-anonymous identities.

Dark web marketplace monitoring is a critical intelligence function for enterprise security teams because these marketplaces are where compromised credentials, stolen data, initial network access, and attack tools are traded. The marketplace ecosystem has evolved through several generations — from Silk Road (seized 2013) through AlphaBay (seized 2017) and Hydra (seized 2022) to current marketplaces like STYX, BlackForums, and BreachForums (reconstituted after multiple seizures). The most security-relevant marketplace categories for enterprise defenders are credential shops (where stolen usernames, passwords, session cookies, and authentication tokens are sold, typically harvested by InfoStealer malware such as RedLine, Raccoon, Vidar, and Lumma — see Domain 11 Chapter 11A §3 for malware families), initial access brokers (IABs — actors who gain unauthorized access to corporate networks via exploited VPN appliances, RDP brute-forcing, or phished credentials, and then sell that access to ransomware operators or other attackers; IABs typically advertise access by industry vertical, revenue of the target company, and type of access — VPN, RDP, Citrix, webshell — with prices ranging from $500 for small-company RDP access to $50,000+ for domain admin access to Fortune 500 organizations), and Ransomware-as-a-Service (RaaS) affiliate programs (where ransomware operators recruit affiliates who carry out the actual intrusions, with the operator providing the ransomware payload, the negotiation infrastructure, and the payment processing in exchange for a percentage of the ransom — typically 20-30% for the operator and 70-80% for the affiliate; prominent RaaS operations as of 2025 include LockBit, BlackCat/ALPHV successors, Akira, and Play).

HUMINT integration with technical dark web collection is essential because the most valuable intelligence on dark web forums is not publicly posted but exchanged in private messages, invite-only channels, and vetting-required communities. Technical collection (crawling, scraping, API monitoring) captures the publicly visible layer — marketplace listings, forum posts, vendor profiles — but the strategic intelligence (an IAB discussing a new exploit before it is listed publicly, a RaaS operation planning a campaign against a specific industry sector, or a data breach being privately shopped before public listing) often requires human sources with established access and reputation in these communities. Law enforcement and intelligence agencies maintain undercover personas in dark web forums as standard operational practice, but enterprise threat intelligence teams typically rely on commercial providers (Flashpoint, Recorded Future, DarkOwl, ZeroFox, KELA) who combine technical collection with analyst expertise and, in some cases, confidential human sources. The legal and ethical boundaries here are significant: purchasing data from dark web marketplaces, even for defensive intelligence purposes, may constitute trafficking in stolen data under computer fraud statutes; interacting with threat actors may expose the organization to entrapment accusations if the intelligence is later used in legal proceedings; and maintaining undercover personas requires operational security discipline that most corporate security teams lack.

Operational security for dark web researchers deserves emphasis because failures in researcher OPSEC can compromise investigations and endanger personnel. Best practices include using dedicated hardware (a laptop that is never connected to the corporate network and has no personally identifiable configuration — no corporate VPN client, no personal email accounts, no browser profiles linked to the researcher's real identity), running Tails OS or Whonix (which route all traffic through Tor and leave no persistent data on the device), using the Tor Browser without modifications (because browser fingerprinting can identify unique browser configurations — installing plugins, changing default window sizes, or modifying about:config settings creates fingerprint-unique browser instances), never authenticating to any service using real credentials while connected to Tor, and maintaining strict persona separation (the forum accounts used for dark web research must have no connection to the researcher's real identity — different email addresses, different PGP keys, different writing style, different timezone indicators in posting patterns). The researcher should also be aware that some dark web forums require a proof-of-work entry process (demonstrating technical capability by solving challenges, providing samples of stolen data, or having an existing member vouch for the applicant), and engaging with these processes raises ethical and legal questions that must be addressed by the organization's legal counsel before field work begins.

### 1.4 Deep web and paste site monitoring

Paste sites — Pastebin, GitHub Gists, Ghostbin (defunct as of 2022, with spiritual successors like Rentry and PrivateBin), Dpaste, and dozens of smaller sites — are a primary channel for data leaks, credential dumps, and threat actor communications. When an attacker exfiltrates a database or harvests credentials, the data is often first posted to a paste site (either as proof of the breach to attract buyers, or as the full dump itself for smaller datasets). Similarly, threat actors use paste sites for dead drops (posting encrypted messages that only the intended recipient can decrypt), for sharing tool configurations (Cobalt Strike Malleable C2 profiles, phishing kit configurations, exploit code), and for posting reconnaissance data about targets.

Automated monitoring of paste sites requires continuous collection and analysis. The Pastebin API (for Pro subscribers) provides access to the "Scraping API" (`https://scrape.pastebin.com/api_scraping.php`), which returns the most recent public pastes at a configurable interval (minimum 1 second between requests). Each response includes the paste's key (unique identifier), title, user (if not anonymous), size, language (if specified by the poster), and URL. The monitoring system must: poll the API at regular intervals (the recommended interval is 1-2 seconds to capture the full paste stream — at approximately 500-1,000 new pastes per minute during peak hours, polling less frequently risks missing short-lived pastes that are subsequently deleted), retrieve the full content of each paste, analyze the content against a library of regular expressions and detection rules, and alert when a match is found.

The regex patterns for credential and secret detection form the core detection engine. These patterns must balance precision (avoiding false positives on code examples, documentation, or test fixtures) with recall (catching real credentials in varied formats):

```python
# paste_monitor_patterns.py — Regex patterns for credential/secret detection
# in paste site monitoring.  Each pattern includes context for triage.

import re
from dataclasses import dataclass

@dataclass
class DetectionRule:
    name: str
    pattern: re.Pattern
    severity: str  # CRITICAL, HIGH, MEDIUM
    description: str

RULES: list[DetectionRule] = [
    # ---- Cloud provider credentials ----
    DetectionRule(
        name="aws_access_key",
        pattern=re.compile(r"(?<![A-Za-z0-9/+=])(AKIA[A-Z0-9]{16})(?![A-Za-z0-9/+=])"),
        severity="CRITICAL",
        description="AWS IAM access key ID (starts with AKIA)",
    ),
    DetectionRule(
        name="aws_secret_key",
        pattern=re.compile(
            r"(?<![A-Za-z0-9/+=])([A-Za-z0-9/+=]{40})(?![A-Za-z0-9/+=])"
        ),
        severity="HIGH",
        description="Potential AWS secret key (40-char base64; high FP — correlate with AKIA nearby)",
    ),
    DetectionRule(
        name="gcp_api_key",
        pattern=re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
        severity="HIGH",
        description="Google Cloud API key",
    ),
    DetectionRule(
        name="azure_storage_key",
        pattern=re.compile(
            r"DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{88};EndpointSuffix="
        ),
        severity="CRITICAL",
        description="Azure Storage connection string with account key",
    ),

    # ---- Version control tokens ----
    DetectionRule(
        name="github_pat",
        pattern=re.compile(r"ghp_[A-Za-z0-9_]{36}"),
        severity="CRITICAL",
        description="GitHub personal access token (classic)",
    ),
    DetectionRule(
        name="github_fine_grained",
        pattern=re.compile(r"github_pat_[A-Za-z0-9_]{22}_[A-Za-z0-9_]{59}"),
        severity="CRITICAL",
        description="GitHub fine-grained personal access token",
    ),
    DetectionRule(
        name="gitlab_pat",
        pattern=re.compile(r"glpat-[A-Za-z0-9\-_]{20,}"),
        severity="CRITICAL",
        description="GitLab personal access token",
    ),

    # ---- Private keys ----
    DetectionRule(
        name="rsa_private_key",
        pattern=re.compile(r"-----BEGIN RSA PRIVATE KEY-----"),
        severity="CRITICAL",
        description="PEM-encoded RSA private key header",
    ),
    DetectionRule(
        name="ec_private_key",
        pattern=re.compile(r"-----BEGIN EC PRIVATE KEY-----"),
        severity="CRITICAL",
        description="PEM-encoded EC private key header",
    ),
    DetectionRule(
        name="openssh_private_key",
        pattern=re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----"),
        severity="CRITICAL",
        description="OpenSSH private key header",
    ),

    # ---- Database connection strings ----
    DetectionRule(
        name="postgres_uri",
        pattern=re.compile(
            r"postgres(?:ql)?://[^:]+:[^@]+@[^/]+(?::\d+)?/\w+"
        ),
        severity="HIGH",
        description="PostgreSQL connection URI with embedded password",
    ),
    DetectionRule(
        name="mongodb_uri",
        pattern=re.compile(
            r"mongodb(?:\+srv)?://[^:]+:[^@]+@[^/]+"
        ),
        severity="HIGH",
        description="MongoDB connection URI with embedded password",
    ),

    # ---- Messaging / SaaS tokens ----
    DetectionRule(
        name="slack_token",
        pattern=re.compile(r"xox[bpors]-[0-9]+-[0-9]+-[A-Za-z0-9]+"),
        severity="HIGH",
        description="Slack API token (bot, user, or workspace)",
    ),
    DetectionRule(
        name="stripe_secret",
        pattern=re.compile(r"sk_live_[A-Za-z0-9]{24,}"),
        severity="CRITICAL",
        description="Stripe live secret key",
    ),

    # ---- Organization-specific (customize per engagement) ----
    DetectionRule(
        name="org_email_domain",
        pattern=re.compile(r"[a-zA-Z0-9_.+-]+@targetcorp\.com", re.IGNORECASE),
        severity="MEDIUM",
        description="Email address matching monitored domain",
    ),
]


def scan_content(text: str) -> list[tuple[DetectionRule, list[str]]]:
    """Return list of (rule, matches) for all rules that fire on `text`."""
    findings = []
    for rule in RULES:
        matches = rule.pattern.findall(text)
        if matches:
            findings.append((rule, matches))
    return findings
```

The paste polling loop integrates these patterns with the Pastebin Scraping API and forwards detections to TheHive for incident triage:

```python
# paste_poller.py — Pastebin Scraping API monitor with TheHive alert creation.
# Requires: requests, thehive4py

import time
import requests
from thehive4py.api import TheHiveApi
from thehive4py.models import Alert, AlertArtifact
from paste_monitor_patterns import scan_content

PASTEBIN_SCRAPE_URL = "https://scrape.pastebin.com/api_scraping.php"
PASTEBIN_RAW_URL = "https://scrape.pastebin.com/api_scrape_item.php"
POLL_INTERVAL = 2  # seconds

THEHIVE_URL = "https://thehive.internal.example.com"
THEHIVE_KEY = "__REDACTED__"
hive = TheHiveApi(THEHIVE_URL, THEHIVE_KEY)

seen_keys: set[str] = set()

while True:
    try:
        resp = requests.get(
            PASTEBIN_SCRAPE_URL, params={"limit": 100}, timeout=10
        )
        pastes = resp.json()
    except Exception as exc:
        print(f"[!] Scrape API error: {exc}")
        time.sleep(POLL_INTERVAL)
        continue

    for paste in pastes:
        key = paste.get("key", "")
        if key in seen_keys:
            continue
        seen_keys.add(key)

        try:
            raw = requests.get(
                PASTEBIN_RAW_URL, params={"i": key}, timeout=10
            ).text
        except Exception:
            continue

        findings = scan_content(raw)
        if not findings:
            continue

        # Build TheHive alert
        artifacts = []
        descriptions = []
        for rule, matches in findings:
            descriptions.append(
                f"**{rule.name}** ({rule.severity}): {len(matches)} match(es)"
            )
            for m in matches[:5]:  # cap artifacts per rule
                artifacts.append(AlertArtifact(dataType="other", data=m))

        alert = Alert(
            title=f"Paste leak: {paste.get('title', key)[:80]}",
            description=(
                f"Paste URL: https://pastebin.com/{key}\n\n"
                + "\n".join(descriptions)
            ),
            type="paste-monitor",
            source="pastebin",
            sourceRef=key,
            severity=2 if any(r.severity == "CRITICAL" for r, _ in findings) else 1,
            artifacts=artifacts,
        )
        hive.create_alert(alert)
        print(f"[+] Alert created for paste {key}: {[r.name for r, _ in findings]}")

    time.sleep(POLL_INTERVAL)
```

Detection rules for paste monitoring fall into several categories. Credential detection rules look for patterns matching usernames/email addresses paired with passwords, password hashes, API keys, cloud service credentials, private keys, and database connection strings. Organization-specific rules match company domain names, employee email addresses, internal hostnames, project names, and proprietary terminology. Threat intelligence rules match known indicators of compromise (hashes, IP addresses, domain names from threat feeds), attacker tool configurations (Cobalt Strike team server configurations, Metasploit resource scripts), and communication patterns (Base64-encoded messages with specific header formats used by particular threat actor groups).

Integration with TheHive and Cortex provides an incident response workflow for paste site detections. TheHive is an open-source Security Incident Response Platform (SIRP) that manages security incidents as cases with observables (IOCs), tasks, and analyst notes. Cortex is TheHive's companion analysis engine, providing automated observable analysis through analyzers — modular analysis plugins that enrich observables with context. When the paste monitoring system detects a match, it creates a TheHive alert containing the paste URL, the matched content, the rule that triggered, and the timestamp. The TheHive analyst triages the alert, and if it represents a genuine leak, promotes it to a case. Cortex analyzers then automatically enrich the observables extracted from the paste: email addresses are checked against HIBP, domain names are resolved and checked against threat intelligence feeds, IP addresses are geolocated and checked against abuse databases, and file hashes are submitted to VirusTotal. This automated enrichment accelerates the analyst's assessment and provides the context needed to determine the leak's severity and scope.

GitHub Gists require separate monitoring because they exist outside the Pastebin ecosystem and are frequently used for credential leaks (developers accidentally committing API keys in code snippets), tool sharing (attack scripts and configurations), and data exfiltration. GitHub's public event stream (available via the GitHub Events API at `https://api.github.com/events`) includes `GistEvent` events for public gist creation and updates. Additionally, tools like truffleHog and Gitleaks (covered in Domain 23 Chapter 23A §2.7) scan GitHub repositories for committed secrets, but gist-specific monitoring requires dedicated collection because gists are not associated with repositories and do not appear in repository-focused scanning. The GitHub search API (`https://api.github.com/search/code`) can be used to search gist content for specific patterns, though rate limiting (30 requests per minute for authenticated requests) constrains the throughput of this approach.

---

## 2. Advanced Infrastructure Analysis

### 2.1 Passive DNS and historical resolution data

Passive DNS (pDNS) data is collected by sensors positioned at recursive DNS resolvers that record every DNS query and response passing through the resolver. Unlike active DNS queries (running `dig` against a domain's authoritative nameserver, which returns only the current state), passive DNS provides a historical record of DNS resolutions — every IP address a domain has resolved to, every domain that has resolved to a given IP address, and the time ranges during which each resolution was active. This temporal dimension is what makes passive DNS the most powerful single data source for infrastructure pivoting.

The major passive DNS data providers each have distinct collection architectures and coverage characteristics. Farsight DNSDB (now operated by DomainTools following the Farsight Security acquisition) is the largest passive DNS database, with collection sensors deployed at hundreds of recursive resolvers worldwide. DNSDB provides both forward lookups (domain to historical IPs) and inverse lookups (IP to historical domains — also called "rdata" queries). The inverse lookup capability is particularly valuable: given an IP address associated with a known threat, the analyst can retrieve all domains that have ever resolved to that IP, immediately identifying additional infrastructure the threat actor may have used. DNSDB's API supports time-fencing queries (specifying `time_first_after` and `time_last_before` parameters to constrain results to a specific time window), which is essential for reducing false positives in infrastructure pivoting — a domain that resolved to the same IP as a malicious domain but ten years earlier is almost certainly coincidental, while a domain that co-resolved during the same six-month window is a strong indicator of related infrastructure.

Querying the DNSDB API for forward and inverse lookups:

```bash
# DNSDB API queries via curl — requires DNSDB_API_KEY
export DNSDB_API_KEY="__REDACTED__"

# Forward lookup: all historical A records for a domain
curl -s -H "X-API-Key: ${DNSDB_API_KEY}" \
  "https://api.dnsdb.info/dnsdb/v2/lookup/rrset/name/suspicious-target.com/A" \
  | jq '.obj | {rrname, rdata, time_first: (.time_first | todate), time_last: (.time_last | todate)}'

# Inverse lookup: all domains that have resolved to a specific IP
curl -s -H "X-API-Key: ${DNSDB_API_KEY}" \
  "https://api.dnsdb.info/dnsdb/v2/lookup/rdata/ip/198.51.100.42" \
  | jq '.obj | {rrname, rdata, time_first: (.time_first | todate), time_last: (.time_last | todate)}'

# Time-fenced inverse: only domains co-hosted on 198.51.100.42 during 2024
curl -s -H "X-API-Key: ${DNSDB_API_KEY}" \
  "https://api.dnsdb.info/dnsdb/v2/lookup/rdata/ip/198.51.100.42?time_first_after=1704067200&time_last_before=1735689600" \
  | jq '.obj.rrname'
```

SecurityTrails provides historical DNS data with a more accessible API and pricing model than DNSDB. The SecurityTrails API (`https://api.securitytrails.com/v1/history/{domain}/dns/{type}`) returns historical A, AAAA, MX, NS, SOA, and TXT records with first-seen and last-seen timestamps. SecurityTrails also provides a "domain search" capability that finds domains matching specific criteria (registered with a particular registrar, hosted on a particular IP range, using specific name servers, or containing specific WHOIS registrant information), which supports the clustering analysis described in section 2.3 below. SilentPush is a newer entrant in the passive DNS market that focuses on predictive threat intelligence — identifying domains and IP addresses that are likely to become malicious based on infrastructure patterns that historically correlate with malicious use (bulk domain registration, specific hosting providers preferred by threat actors, DNS configuration patterns associated with phishing kits, and certificate issuance timing relative to domain registration).

A Python function demonstrating the SecurityTrails historical DNS pivot and temporal correlation:

```python
# sectrails_pivot.py — Infrastructure pivoting via SecurityTrails historical DNS.
# Identifies domains that co-resolved to the same IP during overlapping windows.

import requests
from datetime import datetime
from collections import defaultdict

ST_KEY = "__REDACTED__"
ST_BASE = "https://api.securitytrails.com/v1"
HEADERS = {"apikey": ST_KEY, "Accept": "application/json"}


def get_historical_ips(domain: str) -> list[dict]:
    """Return historical A records for a domain: [{ip, first_seen, last_seen}]."""
    r = requests.get(
        f"{ST_BASE}/history/{domain}/dns/a", headers=HEADERS, timeout=30
    )
    r.raise_for_status()
    results = []
    for rec in r.json().get("records", []):
        for val in rec.get("values", []):
            results.append({
                "ip": val["ip"],
                "first_seen": rec.get("first_seen", ""),
                "last_seen": rec.get("last_seen", ""),
            })
    return results


def get_domains_on_ip(ip: str) -> list[str]:
    """Reverse lookup: domains currently or historically associated with an IP."""
    r = requests.get(
        f"{ST_BASE}/search/list",
        headers=HEADERS,
        json={"filter": {"ipv4": ip}},
        timeout=30,
    )
    r.raise_for_status()
    return [rec["hostname"] for rec in r.json().get("records", [])]


def temporal_overlap(a_first: str, a_last: str, b_first: str, b_last: str) -> bool:
    """Return True if two date ranges overlap."""
    fmt = "%Y-%m-%d"
    try:
        return (
            datetime.strptime(a_first, fmt) <= datetime.strptime(b_last, fmt)
            and datetime.strptime(b_first, fmt) <= datetime.strptime(a_last, fmt)
        )
    except ValueError:
        return False  # missing date data — skip


def pivot_from_domain(seed_domain: str) -> dict[str, list[str]]:
    """
    Given a seed domain, find co-hosted domains with temporal overlap.
    Returns {ip: [co-hosted domains]} for each historical IP.
    """
    pivots: dict[str, list[str]] = defaultdict(list)
    seed_records = get_historical_ips(seed_domain)
    for rec in seed_records:
        co_domains = get_domains_on_ip(rec["ip"])
        for d in co_domains:
            if d == seed_domain:
                continue
            d_records = get_historical_ips(d)
            for d_rec in d_records:
                if d_rec["ip"] == rec["ip"] and temporal_overlap(
                    rec["first_seen"], rec["last_seen"],
                    d_rec["first_seen"], d_rec["last_seen"],
                ):
                    pivots[rec["ip"]].append(d)
                    break
    return dict(pivots)
```

The infrastructure pivoting methodology using passive DNS follows a systematic expansion pattern. The analyst starts with a known indicator — a domain observed in a phishing email, a C2 address extracted from malware analysis (see Domain 11 Chapter 11A §4 for C2 extraction techniques), or an IP address observed in network logs. From this seed indicator, the pivoting chain proceeds: query passive DNS for all IPs the seed domain has resolved to (historical A records); for each IP, query passive DNS inversely for all other domains that have resolved to the same IP during overlapping time periods; for each co-hosted domain, check if it appears in threat intelligence feeds, if it was registered with the same registrant information, or if it shares other infrastructure characteristics (same name servers, same SSL certificates, same hosting provider); recursively expand from each newly-identified related domain. This expansion must be bounded — without constraints, the graph grows exponentially and becomes analytically useless. Bounding strategies include: limiting expansion depth (typically two to three hops from the seed), filtering by time window (only considering co-resolutions within a defined period), filtering by hosting type (excluding shared hosting IP ranges where co-location is meaningless — large shared hosting providers may have thousands of unrelated domains per IP), and filtering by threat intelligence correlation (only expanding through nodes that have independent indicators of malicious activity).

### 2.2 WHOIS privacy piercing and registrant correlation

Modern WHOIS data has been significantly redacted since the implementation of GDPR in May 2018 and the subsequent ICANN Temporary Specification (now the Registration Data Policy). Registrant names, email addresses, phone numbers, and physical addresses are typically replaced with "REDACTED FOR PRIVACY" or the registrar's privacy service contact. This redaction has made WHOIS-based attribution more difficult but has not eliminated it — historical WHOIS data (collected before GDPR redaction), registration pattern analysis, and indirect correlation techniques remain effective.

Historical WHOIS databases (maintained by DomainTools, SecurityTrails, WhoisXMLAPI, and others) preserve WHOIS records from before GDPR redaction. For domains registered before May 2018, these databases contain the original registrant information — name, organization, email, phone, and address. Even for domains registered after GDPR, historical WHOIS captures can reveal brief windows where registrant data was exposed (some registrars had implementation gaps where new registrations were briefly visible with full contact data before privacy protection activated, or where privacy protection lapsed during domain renewal). DomainTools' WHOIS History API provides a chronological sequence of all WHOIS records for a domain, showing when registrant information changed, when privacy protection was added or removed, and when the domain transferred between registrars.

Registrant email clustering is the most powerful WHOIS-based attribution technique. Even when a threat actor uses fake names and addresses, they often reuse the same email address to register multiple domains (because creating and managing many email addresses adds operational complexity). The following Python implementation demonstrates automated registrant clustering using the SecurityTrails API:

```python
# whois_cluster.py — Registrant email clustering for attribution.
# Groups domains by shared historical WHOIS registrant email.

import requests
from collections import defaultdict

ST_KEY = "__REDACTED__"
ST_BASE = "https://api.securitytrails.com/v1"
HEADERS = {"apikey": ST_KEY, "Accept": "application/json"}


def get_whois_history(domain: str) -> list[dict]:
    """Retrieve historical WHOIS records for a domain."""
    r = requests.get(
        f"{ST_BASE}/history/{domain}/whois",
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("result", {}).get("items", [])


def extract_emails(whois_records: list[dict]) -> set[str]:
    """Extract all registrant emails from WHOIS history."""
    emails = set()
    for record in whois_records:
        contact = record.get("registrant", {}) or {}
        email = contact.get("email", "")
        if email and "REDACTED" not in email.upper() and "@" in email:
            emails.add(email.lower())
    return emails


def reverse_whois_by_email(email: str) -> list[str]:
    """Find all domains registered with a given email address."""
    r = requests.get(
        f"{ST_BASE}/search/list",
        headers=HEADERS,
        json={"filter": {"whois_email": email}},
        timeout=30,
    )
    r.raise_for_status()
    return [rec["hostname"] for rec in r.json().get("records", [])]


def cluster_domains(seed_domains: list[str]) -> dict[str, list[str]]:
    """
    Given seed domains, find all registrant emails and expand
    to the full portfolio of domains per email.
    """
    email_to_domains: dict[str, list[str]] = defaultdict(list)
    processed_emails: set[str] = set()

    for domain in seed_domains:
        history = get_whois_history(domain)
        emails = extract_emails(history)
        for email in emails:
            if email in processed_emails:
                continue
            processed_emails.add(email)
            related = reverse_whois_by_email(email)
            email_to_domains[email].extend(related)

    return dict(email_to_domains)


# Usage:
# clusters = cluster_domains(["suspicious-domain-1.com", "known-c2.net"])
# for email, domains in clusters.items():
#     print(f"Registrant {email}: {len(domains)} domains")
#     for d in sorted(domains):
#         print(f"  - {d}")
```

This technique was central to numerous threat actor attributions — for example, Mandiant's (then FireEye's) 2013 APT1 report used WHOIS registrant email clustering to link dozens of C2 domains to a small number of operators, which combined with other evidence (domain registration times correlated with Chinese business hours, hosting on Chinese IP ranges, and registrant emails appearing in Chinese-language forums) supported attribution to PLA Unit 61398.

Registration timing analysis reveals operational patterns. When a threat actor registers a batch of domains for a campaign (phishing domains for a spear-phishing operation, C2 domains for a malware campaign, watering-hole domains for a strategic web compromise), the registrations often cluster in time — multiple domains registered within minutes or hours of each other, frequently using the same registrar and payment method. This temporal clustering, combined with shared registrar and name server information, creates a signature that identifies campaign infrastructure even when registrant details are redacted. The creation timestamps from WHOIS records (which are not redacted under GDPR) are the primary data point for this analysis.

Name server correlation is another pivot point. Threat actors who operate their own DNS infrastructure (rather than using the registrar's default name servers) will assign their domains to name servers they control. Querying for all domains delegated to the same name servers identifies the full infrastructure cluster. This technique is particularly effective against sophisticated threat actors who use custom name server configurations — the name servers themselves become fingerprints of the actor's operational infrastructure.

### 2.3 TLS certificate intelligence and fingerprinting

TLS certificates are rich intelligence sources because they contain structured metadata (subject common name, subject alternative names, issuer, validity period, public key parameters, serial number) and because Certificate Transparency (CT) logs provide a near-complete public record of all certificates issued by trusted certificate authorities (as mandated by the Chrome CT policy since April 2018 and Apple's CT policy since October 2018 — see Domain 9 Chapter 9A §3 for CT fundamentals). This section examines advanced techniques for extracting intelligence from certificates beyond the basic CT log searches covered in Chapter 23A.

JA3 and JA4 fingerprinting are passive techniques for identifying the software that initiates or terminates TLS connections. JA3 (developed by John Althouse, Jeff Atkinson, and Josh Atkins at Salesforce) generates a fingerprint from the TLS ClientHello message: specifically, the TLS version, the cipher suites offered, the extensions present, the elliptic curves supported, and the elliptic curve point formats. These values are concatenated and hashed with MD5 to produce a 32-character fingerprint. Because different TLS implementations (and different versions of the same implementation) produce different ClientHello messages, the JA3 fingerprint identifies the TLS library and often the specific application — a Cobalt Strike beacon using the WinHTTP library produces a different JA3 fingerprint than a Chrome browser, which produces a different fingerprint than a Python requests library. The significance for threat intelligence is that JA3 fingerprints can identify malicious clients (C2 beacons, exploit tools, automated scanners) in network traffic even when the traffic is encrypted and the destination IP is not yet known to be malicious. Defenders can collect JA3 fingerprints at network monitoring points and correlate them with known-malicious fingerprints from threat intelligence feeds.

Generating and using JA3/JA4 fingerprints from packet captures:

```bash
# Extract JA3 hashes from a pcap using Zeek (formerly Bro)
zeek -r capture.pcap local "Log::default_rotation_interval=0secs"
# JA3 hashes appear in ssl.log:
# fields: ts uid id.orig_h id.orig_p id.resp_h id.resp_p ... ja3 ja3s
cat ssl.log | zeek-cut ja3 ja3s server_name id.orig_h | sort | uniq -c | sort -rn

# Extract JA3 from live traffic using tshark
tshark -i eth0 -Y "tls.handshake.type == 1" \
  -T fields -e ip.src -e tls.handshake.ja3_full -e tls.handshake.ja3 \
  2>/dev/null

# Generate JA4 fingerprints using the ja4 tool (FoxIO)
# https://github.com/FoxIO-LLC/ja4
ja4 -r capture.pcap
# Output: JA4=t13d191000_hash_hash  (human-readable prefix + hashed components)

# Search for known-malicious JA3 fingerprints (e.g. Cobalt Strike default)
# Common Cobalt Strike JA3 (varies by version and Malleable C2 profile):
grep -c "72a589da586844d7f0818ce684948eea" ssl.log
# Metasploit Meterpreter reverse_https:
grep -c "5d65ea3ab1d764ee2e32f4a9a9f56950" ssl.log
```

JA3S is the server-side complement: it fingerprints the TLS ServerHello message (which the server sends in response to the ClientHello), capturing the server's chosen TLS version, cipher suite, and extensions. The combination of JA3 (client) and JA3S (server) fingerprints provides a unique session characterization that can identify specific client-server pairs.

JA4 (and the broader JA4+ family — JA4, JA4S, JA4H, JA4L, JA4X, JA4SSH) is the successor to JA3, developed by John Althouse at FoxIO. JA4 addresses several limitations of JA3: it uses a human-readable format (rather than an opaque MD5 hash) that includes the TLS version, protocol (TCP/QUIC), SNI presence, number of cipher suites, number of extensions, ALPN value, and a truncated SHA256 hash of the sorted cipher suites and extensions. The sorted hashing is important — JA3's hash changed when the same client listed cipher suites in a different order (which can happen due to session randomization), producing false negatives. JA4's sorted approach produces stable fingerprints regardless of ordering. JA4X fingerprints TLS certificates themselves (using the issuer and subject field values and extensions), and JA4SSH fingerprints SSH sessions (using the client and server key exchange parameters).

JARM (by Salesforce) takes an active approach: it sends a series of ten specifically crafted TLS ClientHello probes to a server and fingerprints the server's responses. Each probe uses a different TLS version, cipher suite list, and extension set, and the server's response to each probe (the chosen cipher, TLS version, and extensions in the ServerHello) is concatenated to form a 62-character fingerprint. Because different server implementations respond differently to these probes, JARM identifies the TLS server software and configuration.

```bash
# JARM scanning — active TLS server fingerprinting
# https://github.com/salesforce/jarm

# Scan a single target
python3 jarm.py target.example.com

# Scan a list of IPs/domains from a file
python3 jarm.py -i targets.txt -o jarm_results.csv

# Compare against known C2 fingerprints
# Cobalt Strike default JARM (varies by version; common 4.x patterns):
# 07d14d16d21d21d07c42d41d00041d24a458a375eef0c576d23a7bab9a9fb1
# Search Shodan for matching JARM fingerprints:
shodan search "ssl.jarm:07d14d16d21d21d07c42d41d00041d24a458a375eef0c576d23a7bab9a9fb1"

# Scan an IP range for C2 servers using JARM + comparison
for ip in $(cat suspicious_ips.txt); do
  result=$(python3 jarm.py "$ip" 2>/dev/null | awk '{print $2}')
  if echo "$result" | grep -qF "07d14d16d21d21d07c"; then
    echo "[!] Potential Cobalt Strike: $ip — JARM: $result"
  fi
done
```

This is particularly useful for identifying C2 servers — Cobalt Strike team servers, Metasploit Meterpreter listeners, and other offensive tools have distinctive JARM fingerprints that persist even when the operator changes IP addresses, domain names, and TLS certificates. The Cobalt Strike default JARM fingerprint (which varies slightly between Cobalt Strike versions but shares common prefix patterns) has been widely published and is used by threat intelligence teams to scan for exposed C2 infrastructure (see Domain 11 Chapter 11A §4 for C2 framework identification). Defenders should note that sophisticated operators can modify their C2 server configurations to alter the JARM fingerprint — Cobalt Strike's Malleable C2 profiles can configure the TLS library parameters, and putting the team server behind a reverse proxy (NGINX, Caddy, or Cloudflare) replaces the C2 server's JARM fingerprint with the proxy's.

Certificate transparency monitoring for brand protection involves continuously querying CT logs for newly-issued certificates. The CertStream library provides a real-time websocket feed of every certificate logged to CT logs, enabling instant detection of suspicious issuances:

```python
# certstream_monitor.py — Real-time CT log monitoring for brand impersonation.
# Detects typosquatting, homoglyph, and combo-squatting certificates.

import certstream
import Levenshtein  # python-Levenshtein
import re
import json
from datetime import datetime, timezone

MONITORED_DOMAINS = ["targetcorp.com", "targetcorp.io", "targetbrand.com"]
ALERT_THRESHOLD = 3  # Levenshtein distance threshold for fuzzy match
COMBO_KEYWORDS = ["login", "secure", "verify", "portal", "update", "account"]


def is_suspicious(cert_domain: str) -> tuple[bool, str]:
    """Check if a certificate domain is suspicious relative to monitored domains."""
    cert_clean = cert_domain.lstrip("*.").lower()
    for monitored in MONITORED_DOMAINS:
        # Exact substring match (brand name embedded in another domain)
        brand_base = monitored.split(".")[0]
        if brand_base in cert_clean and cert_clean != monitored:
            return True, f"brand-embed:{monitored}"
        # Levenshtein fuzzy match
        dist = Levenshtein.distance(cert_clean, monitored)
        if 0 < dist <= ALERT_THRESHOLD:
            return True, f"typosquat(dist={dist}):{monitored}"
        # Combo-squatting: brand + keyword
        for kw in COMBO_KEYWORDS:
            if brand_base in cert_clean and kw in cert_clean:
                return True, f"combo-squat:{brand_base}+{kw}"
    return False, ""


def on_cert(message, context):
    if message["message_type"] != "certificate_update":
        return
    leaf = message["data"]["leaf_cert"]
    all_domains = leaf.get("all_domains", [])
    for domain in all_domains:
        suspicious, reason = is_suspicious(domain)
        if suspicious:
            alert = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "domain": domain,
                "reason": reason,
                "issuer": leaf.get("issuer", {}).get("O", "unknown"),
                "fingerprint": leaf.get("fingerprint", ""),
                "all_sans": all_domains,
            }
            print(json.dumps(alert))
            # Forward to SIEM / TheHive / Slack webhook in production


certstream.listen_for_events(on_cert, url="wss://certstream.calidog.io/")
```

Censys provides a complementary API for historical certificate search — querying certificates by subject, issuer, fingerprint, or key parameters:

```bash
# Censys certificate search via CLI (requires censys Python package)
pip install censys

# Search for certificates mentioning a target organization
censys search "services.tls.certificates.leaf.subject.common_name: targetcorp" \
  --index-type hosts --fields ip,services.port,services.tls.certificates.leaf.subject.common_name

# Search for certificates with specific JA4X fingerprint
censys search "services.tls.certificates.leaf.fingerprint: SHA256_HASH_HERE" \
  --index-type hosts

# Programmatic Censys API query
python3 -c "
from censys.search import CensysHosts
h = CensysHosts()
for page in h.search('services.tls.certificates.leaf.subject.common_name: targetcorp', pages=2):
    for host in page:
        print(host['ip'], host.get('services', [{}])[0].get('port', '?'))
"
```

### 2.4 Hosting infrastructure fingerprinting

Beyond individual server identification, infrastructure fingerprinting at the hosting level reveals patterns about an actor's operational preferences and constraints. Cloud provider identification determines whether a target IP address belongs to AWS, Azure, GCP, Oracle Cloud, DigitalOcean, Linode, Vultr, or other providers by checking the IP against the published IP ranges that cloud providers maintain (AWS publishes its IP ranges at `https://ip-ranges.amazonaws.com/ip-ranges.json`; Azure at `https://www.microsoft.com/en-us/download/details.aspx?id=56519`; GCP at `https://www.gstatic.com/ipranges/cloud.json`). The `ipinfo.io` API and MaxMind GeoIP databases provide ASN and organization information that maps IPs to hosting providers. This intelligence informs both defensive (understanding where attacker infrastructure is hosted for takedown requests) and offensive (understanding the target's cloud footprint for attack surface assessment) operations.

CDN detection identifies whether a domain is served through a content delivery network (Cloudflare, Akamai, Fastly, AWS CloudFront, Azure CDN, Cloudflare). CDNs are significant for OSINT because they mask the origin server's IP address — all requests are handled by the CDN's edge servers, and the origin IP is not visible in DNS records. Techniques for identifying the origin IP behind a CDN include: querying historical DNS records from before the CDN was deployed (using passive DNS databases), looking for subdomains that bypass the CDN (mail servers, FTP servers, development instances that point directly to the origin), checking DNS records for direct A record entries alongside CNAME records pointing to the CDN, and exploiting information disclosure in server headers or error pages that reveal the origin IP. Censys and Shodan scans can identify servers that present the same TLS certificate as the CDN-protected domain but are accessed directly (not through the CDN), revealing the origin IP. SecurityTrails' IP Neighbors feature identifies other domains hosted on the same server, which may include domains that are not CDN-protected and thus expose the shared origin IP.

Shared hosting correlation determines whether multiple domains share the same physical or virtual server. On shared hosting, reverse DNS lookups and reverse IP lookups (querying which domains resolve to a given IP address) reveal co-hosted domains. Censys provides a "hosts" search that returns all domains associated with an IP address based on TLS certificates, HTTP responses, and reverse DNS. This correlation is most useful when a known malicious domain is co-hosted with other domains — the co-hosted domains may be additional campaign infrastructure, or the hosting pattern may reveal the actor's operational preferences (preferred hosting provider, geographic region, payment method through registrar correlation). However, analysts must be cautious about false positives on shared hosting — tens of thousands of unrelated legitimate websites may share a single IP on a large shared hosting provider, and co-location alone is not evidence of relation.

---

## 3. OSINT for Attack Surface Management

### 3.1 Continuous external attack surface discovery

Attack surface management (ASM) has evolved from periodic penetration testing engagements to continuous, automated discovery and monitoring of an organization's externally-visible assets. The distinction is significant: a penetration test provides a point-in-time assessment, while ASM provides ongoing visibility into assets as they appear, change, and (ideally) are decommissioned. This is critical because organizations' external attack surfaces are dynamic — cloud instances are spun up by development teams without security review, marketing campaigns launch microsites on new domains, acquisitions bring entire new networks into scope, and shadow IT creates assets that the security team does not know about.

The ProjectDiscovery toolchain has become the de facto open-source ASM framework. The toolchain consists of several purpose-built tools designed to work together. `subfinder` performs passive subdomain enumeration by querying multiple data sources (CT logs, DNS aggregators, search engine cache, threat intelligence feeds, web archive APIs) and merging the results. Unlike brute-force subdomain enumeration (which sends millions of DNS queries and is noisy), subfinder's passive approach generates no traffic to the target and is therefore stealthy. `httpx` probes discovered subdomains with HTTP/HTTPS requests and extracts metadata (HTTP status codes, page titles, content length, server headers, TLS certificate information, response body hashes, and technology detection via Wappalyzer signatures). `nuclei` is a vulnerability scanner that uses template-based detection — each vulnerability check is defined in a YAML template that specifies the request to send and the response pattern to match. The nuclei template library (maintained by the ProjectDiscovery community) contains over 8,000 templates covering specific CVEs (CVE-2023-22515 for Confluence authentication bypass, CVE-2024-1709 for ConnectWise ScreenConnect path traversal, CVE-2023-46805/CVE-2024-21887 for Ivanti Connect Secure chained RCE, among thousands of others), misconfigurations, exposed panels, default credentials, and information disclosure. `katana` is a web crawler that discovers URLs, endpoints, JavaScript files, and API references by crawling discovered web applications. `chaos` is ProjectDiscovery's managed subdomain data service that provides pre-computed subdomain datasets for bug bounty programs and ASM.

The complete ProjectDiscovery ASM pipeline:

```bash
# ============================================================
# ProjectDiscovery ASM Pipeline — full workflow
# ============================================================

# Phase 1: Passive subdomain enumeration
subfinder -d target.com -all -recursive -o subdomains_raw.txt
# -all: use all sources (including those requiring API keys configured in
#        ~/.config/subfinder/provider-config.yaml)
# -recursive: enumerate subdomains of discovered subdomains

# Deduplicate and sort
sort -u subdomains_raw.txt > subdomains.txt
echo "[*] Discovered $(wc -l < subdomains.txt) unique subdomains"

# Phase 2: HTTP probing — identify live web services
httpx -l subdomains.txt -o alive.txt \
  -status-code -title -tech-detect -tls-probe -web-server \
  -content-length -follow-redirects -threads 50
# Output includes: URL, status code, page title, detected technologies,
# TLS certificate info, server header, content length

# Phase 3: Web crawling — discover endpoints, JS files, API references
katana -list alive.txt -depth 3 -js-crawl -known-files all \
  -output crawled_urls.txt -concurrency 20
# -js-crawl: parse JavaScript files for additional URLs/endpoints
# -known-files: check for robots.txt, sitemap.xml, .well-known, etc.

# Phase 4: Vulnerability scanning — template-based detection
nuclei -l alive.txt -t cves/ -severity critical,high \
  -o vuln_findings.txt -rate-limit 100 -bulk-size 25
# Scan for misconfigurations and exposed panels separately
nuclei -l alive.txt -t misconfiguration/ -t exposed-panels/ \
  -o misconfig_findings.txt -rate-limit 100

# Phase 5: Technology-specific scans based on httpx tech-detect output
grep -i "wordpress" alive.txt | cut -d' ' -f1 | \
  nuclei -t technologies/wordpress/ -o wp_findings.txt
grep -i "apache" alive.txt | cut -d' ' -f1 | \
  nuclei -t technologies/apache/ -o apache_findings.txt

# Phase 6: Screenshot capture for manual review
gowitness file -f alive.txt --threads 10 \
  --screenshot-path ./screenshots/

# Phase 7: Consolidate results
echo "=== ASM Summary ==="
echo "Subdomains:       $(wc -l < subdomains.txt)"
echo "Live hosts:       $(wc -l < alive.txt)"
echo "Crawled URLs:     $(wc -l < crawled_urls.txt)"
echo "Critical/High:    $(wc -l < vuln_findings.txt)"
echo "Misconfigurations: $(wc -l < misconfig_findings.txt)"
```

Commercial ASM platforms provide enterprise-grade capabilities on top of similar discovery techniques. CrowdStrike Falcon Surface (formerly Reposify) combines internet scanning with the CrowdStrike threat intelligence corpus to identify exposed assets and correlate them with known attacker tactics. Microsoft Defender EASM (External Attack Surface Management) discovers assets through DNS enumeration, web crawling, certificate analysis, and cloud provider integration (Azure, AWS, GCP), and maps them to the organization's known asset inventory to identify shadow IT. Mandiant ASM (formerly Intrigue) performs recursive infrastructure discovery — starting from seed domains and IP ranges, it discovers linked assets through DNS, WHOIS, certificate, and web content analysis, progressively building a graph of the organization's external footprint. Palo Alto Cortex Xpanse uses internet-wide scanning (similar to Shodan/Censys but proprietary) to maintain a real-time inventory of all internet-facing assets attributable to a given organization, with automated policy enforcement (alerting when assets violate security policies, such as an exposed RDP service or an unpatched web server).

### 3.2 Exposed credential monitoring

Credential exposure represents one of the most immediate and exploitable attack surface elements. Exposed credentials come from multiple sources: data breaches (where an attacker exfiltrates a database of user credentials from a compromised service), InfoStealer malware (which harvests credentials from infected endpoints — browser-saved passwords, autofill data, session cookies, cryptocurrency wallets, and VPN/SSH credentials), and accidental exposure (developers committing API keys to public repositories, employees posting credentials in public paste sites, or credentials appearing in public documents).

Breach database monitoring involves tracking known data breaches and checking whether the organization's email domains appear in the breached data. Have I Been Pwned (HIBP), operated by Troy Hunt, is the most established breach notification service — organizations can register their email domains and receive notifications when employee email addresses appear in newly-ingested breach data. HIBP's "Pwned Passwords" service provides a k-anonymity-based API for checking whether specific passwords appear in known breach datasets (the client sends the first five characters of the SHA-1 hash, and the server returns all matching hashes — the client checks locally, so the full password hash is never transmitted). For enterprise deployment, HIBP's domain search API and Splunk/SIEM integration enable automated alerting when employee credentials are exposed.

InfoStealer log analysis has become a critical intelligence function since 2022 as InfoStealer malware has proliferated. InfoStealers like RedLine, Raccoon Stealer, Vidar, Meta Stealer, and Lumma Stealer infect endpoints (typically via malvertising, cracked software downloads, or phishing) and harvest all stored credentials, cookies, autofill data, and cryptocurrency wallets. The harvested data is uploaded to the stealer operator's command-and-control server and then sold on dark web marketplaces and Telegram channels (see Domain 11 Chapter 11A §3 for malware family details). The Genesis Market (seized by the FBI in April 2023 via "Operation Cookie Monster") was the most sophisticated credential marketplace — it sold complete browser profiles (cookies, fingerprints, and saved passwords) as "bots," allowing buyers to clone the victim's browser session and bypass authentication (including session-based MFA) without knowing the password. After Genesis Market's seizure, its role was partially filled by the Russian Market and successor platforms.

For enterprise security teams, monitoring InfoStealer output requires access to stealer log data, which is available through several channels: commercial threat intelligence providers (Flare, SpyCloud, Hudson Rock, KELA, and Recorded Future all ingest and index stealer logs, providing searchable databases where organizations can query for their employee email domains, corporate SSO domains, and VPN hostnames), government sharing programs (some CERTs and ISACs share stealer log data with affected organizations), and direct monitoring of Telegram channels and dark web forums where stealer operators and resellers post sample data. When an organization's credentials are found in stealer logs, the response is urgent: the affected user's password must be reset, their active sessions must be revoked (simply changing the password does not invalidate existing session cookies, which the stealer has already exfiltrated), their endpoint must be investigated for active malware infection, and any accounts accessible with the stolen credentials must be audited for unauthorized access.

### 3.3 Exposed API discovery

Modern web applications expose APIs that represent a significant and often poorly-understood component of the attack surface. Many organizations have undocumented or forgotten APIs — internal APIs that were inadvertently exposed to the internet, development/staging APIs with weaker authentication, deprecated API versions that remain accessible, and third-party API integrations that expose more data than intended.

Swagger/OpenAPI endpoint discovery exploits the common practice of publishing API documentation alongside the API itself. The Swagger UI (a JavaScript-based API documentation viewer) is frequently deployed at predictable paths: `/swagger`, `/swagger-ui`, `/swagger-ui.html`, `/api-docs`, `/v2/api-docs`, `/v3/api-docs`, `/openapi.json`, `/openapi.yaml`, and `/docs`. When discovered, the OpenAPI specification document enumerates every API endpoint, its HTTP method, request parameters, authentication requirements, and response schemas — providing a complete roadmap for API testing.

```bash
# Automated Swagger/OpenAPI endpoint discovery using nuclei
nuclei -l alive.txt -t http/exposed-panels/swagger-api.yaml -o swagger_found.txt

# Manual probing for common API documentation paths
while IFS= read -r host; do
  for path in /swagger /swagger-ui /swagger-ui.html /api-docs /v2/api-docs \
              /v3/api-docs /openapi.json /openapi.yaml /docs /redoc; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${host}${path}")
    if [ "$code" = "200" ]; then
      echo "[+] API docs found: ${host}${path} (HTTP ${code})"
    fi
  done
done < alive.txt
```

The discovery of an authenticated API's OpenAPI spec does not necessarily grant access (the endpoints still require valid authentication tokens), but it reveals the API's structure, which informs targeted testing — the attacker knows exactly which endpoints exist, what parameters they accept, and what data they return, eliminating the need for blind fuzzing.

GraphQL introspection is an analogous exposure in GraphQL APIs. GraphQL's introspection feature allows clients to query the API's schema — the types, fields, queries, mutations, and subscriptions it supports — by sending a special introspection query. In production deployments, introspection should be disabled, but many GraphQL APIs leave introspection enabled:

```bash
# GraphQL introspection query — retrieve the complete schema
curl -s -X POST https://target.example.com/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "{ __schema { queryType { name } mutationType { name } types { name kind fields { name type { name kind ofType { name } } } } } }"
  }' | python3 -m json.tool

# Full introspection with input types and enums (for comprehensive mapping)
curl -s -X POST https://target.example.com/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query IntrospectionQuery { __schema { queryType { name } mutationType { name } subscriptionType { name } types { ...FullType } directives { name description locations args { ...InputValue } } } } fragment FullType on __Type { kind name description fields(includeDeprecated: true) { name description args { ...InputValue } type { ...TypeRef } isDeprecated deprecationReason } inputFields { ...InputValue } interfaces { ...TypeRef } enumValues(includeDeprecated: true) { name description isDeprecated deprecationReason } possibleTypes { ...TypeRef } } fragment InputValue on __InputValue { name description type { ...TypeRef } defaultValue } fragment TypeRef on __Type { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } }"
  }' > graphql_schema.json

# Visualize with graphql-voyager or process with InQL (Burp extension)
# InQL standalone CLI mode:
inql -t https://target.example.com/graphql -o ./graphql_output/
```

Tools like graphql-voyager visualize introspection results as an interactive graph, and InQL (a Burp Suite extension) automates GraphQL reconnaissance including introspection, query building, and batch querying. Exploiting GraphQL introspection is discussed in detail in Domain 8 Chapter 8B §4.

### 3.4 Cloud asset discovery

Cloud environments introduce unique attack surface elements because cloud services are provisioned programmatically and at scale, creating assets that may escape traditional asset inventory processes. The most commonly exposed cloud assets are storage objects, compute endpoints, and management interfaces.

S3 bucket enumeration targets Amazon Web Services' Simple Storage Service, where data exposure incidents have been so frequent that they constitute their own category of breach. S3 buckets can be public (accessible without authentication), and organizations frequently misconfigure bucket policies to allow public read or public list access.

```bash
# S3 bucket enumeration with cloud_enum
# https://github.com/initstring/cloud_enum
python3 cloud_enum.py -k targetcorp -k target-corp -k targetcorporation \
  --disable-azure --disable-gcp -o s3_results.txt
# -k: keyword mutations for bucket name guessing

# S3Scanner — dedicated S3 bucket permission checker
# https://github.com/sa7mon/S3Scanner
python3 s3scanner.py --buckets-file bucket_names.txt --out-file s3scan_results.txt
# Tests: ListBucket, GetBucketAcl, PutObject permissions

# Manual S3 bucket existence and permissions check via AWS CLI
aws s3 ls s3://targetcorp-backup --no-sign-request 2>&1
aws s3 ls s3://targetcorp-logs --no-sign-request 2>&1
# --no-sign-request: anonymous access (no AWS credentials needed)
# "AccessDenied" = bucket exists but is private
# "NoSuchBucket"  = bucket does not exist
# Listing output     = bucket is publicly listable (finding!)

# Azure Blob Storage enumeration
# Blobs accessible at: https://{account}.blob.core.windows.net/{container}
for account in targetcorp targetcorpstorage targetcorpdata; do
  for container in public data backups logs images static; do
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
      "https://${account}.blob.core.windows.net/${container}?restype=container&comp=list")
    if [ "$code" = "200" ]; then
      echo "[+] Public Azure blob: ${account}/${container}"
    fi
  done
done

# GCS (Google Cloud Storage) bucket enumeration
for bucket in targetcorp targetcorp-data targetcorp-backup; do
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 \
    "https://storage.googleapis.com/${bucket}")
  if [ "$code" = "200" ] || [ "$code" = "403" ]; then
    echo "[*] GCS bucket exists: ${bucket} (HTTP ${code})"
  fi
done
```

Exposed Kubernetes dashboards and etcd instances represent a high-severity cloud exposure. The Kubernetes Dashboard (a web-based management UI) is sometimes exposed to the internet without authentication (or with a default/weak authentication configuration), allowing any attacker to view and modify the cluster's workloads, deployments, secrets, and configuration. The etcd key-value store (Kubernetes' backend state store) listens on port 2379 by default and, if exposed without TLS client certificate authentication (a condition exacerbated by vulnerabilities such as CVE-2023-44487, the HTTP/2 rapid-reset attack that could DoS exposed API servers, and CVE-2022-3294 which allowed node-level credential escalation), allows unauthenticated reading of the entire cluster state — including Kubernetes Secrets (which may contain database passwords, API keys, TLS certificates, and other sensitive data, typically Base64-encoded but not encrypted at rest unless envelope encryption is configured). Shodan and Censys queries for exposed Kubernetes dashboards (`http.title:"Kubernetes Dashboard"`) and etcd instances (`port:2379 "etcdserver"`) consistently return thousands of results, indicating widespread misconfiguration (see Domain 10 Chapter 10B §2 for Kubernetes security architecture).

---

## 4. Counter-OSINT and Operational Security

### 4.1 Minimizing organizational digital footprint

Defensive OSINT — reducing the information available to attackers — is the mirror image of offensive OSINT collection. Every piece of information an attacker can collect about an organization's infrastructure, employees, technology stack, and operational patterns reduces the cost and increases the success probability of an attack. Organizational digital footprint reduction involves systematically identifying and removing or restricting the information that is unnecessarily exposed.

DNS record hygiene is the first layer. Organizations should audit their DNS zones to identify and remove records that expose internal infrastructure: HINFO records (which specify the host's operating system and hardware — rarely used today but sometimes present in legacy zones), TXT records containing internal information (SPF records that enumerate all email-sending infrastructure, including internal mail servers and cloud services; DKIM selector names that reveal the email provider; verification records for cloud services that confirm the organization's use of specific SaaS platforms), and dangling CNAME records (CNAMEs pointing to deprovisioned cloud resources, which are vulnerable to subdomain takeover — an attacker can claim the deprovisioned resource and serve content under the organization's subdomain). DNS zone transfer restrictions (disabling AXFR/IXFR to unauthorized requestors) prevent attackers from obtaining the complete zone file. NSEC/NSEC3 configuration in DNSSEC-signed zones should use NSEC3 (with opt-out and salt) rather than NSEC, because NSEC records can be walked to enumerate all records in the zone (a process called NSEC walking, where the attacker queries for a non-existent name, receives the NSEC record pointing to the next name in the zone, queries for a non-existent name after that, and so on until the entire zone is enumerated).

Concrete DNS hardening measures and the configuration changes that implement them:

```bash
# Audit DNS zone for information leakage
# 1. Check for zone transfer misconfiguration
dig @ns1.targetcorp.com targetcorp.com AXFR
# If this returns records, zone transfer is open — must restrict.

# 2. Check for HINFO records (should not exist in production zones)
dig @ns1.targetcorp.com targetcorp.com HINFO
dig @ns1.targetcorp.com targetcorp.com ANY  # enumerate all record types

# 3. Check for dangling CNAMEs (subdomain takeover vectors)
# Export all CNAME records and verify targets still exist
dig @ns1.targetcorp.com targetcorp.com AXFR | grep CNAME | while read -r line; do
  target=$(echo "$line" | awk '{print $NF}')
  if ! dig +short "$target" A | grep -q '.'; then
    echo "[!] Dangling CNAME: $line"
  fi
done

# 4. NSEC3 configuration for DNSSEC (BIND example)
# In the zone signing configuration, use NSEC3 to prevent zone walking:
# dnssec-signzone -3 $(head -c 16 /dev/urandom | xxd -p) \  # random salt
#   -H 10 \   # hash iterations
#   -A -o targetcorp.com \
#   db.targetcorp.com

# 5. Restrict zone transfers in BIND named.conf:
# zone "targetcorp.com" {
#     type master;
#     file "db.targetcorp.com";
#     allow-transfer { 198.51.100.2; 198.51.100.3; };  # secondary NS only
#     allow-query { any; };
# };
```

Certificate transparency monitoring serves both offensive and defensive purposes. Offensively, defenders monitor CT logs for unauthorized or suspicious certificate issuance (as discussed in section 2.3). Defensively, organizations should be aware that every certificate they issue is logged in CT logs and publicly visible — this means that issuing a certificate for `internal-admin.staging.corp.example.com` reveals the existence of that hostname to anyone searching CT logs. Strategies for minimizing CT-based exposure include: using wildcard certificates (`*.example.com`) for internal subdomains (so the CT log entry does not reveal specific hostnames), using private CAs (whose certificates are not submitted to public CT logs) for purely internal services, and considering the use of pre-certificates with redaction (a proposed but not widely implemented CT feature that would allow redacting the left-most label of a domain name in CT log entries).

Metadata scrubbing prevents information leakage through document and image metadata. Office documents (Word, Excel, PowerPoint) embed metadata including author name, organization name, software version, template path (which may reveal internal file server names), revision history (which may contain previously-deleted content), and comments. PDF files embed creator application, author, creation/modification timestamps, and producer information. Images (JPEG, TIFF, HEIC) embed EXIF metadata including camera model, GPS coordinates, timestamps, and sometimes the device's serial number. Organizations should implement metadata scrubbing at egress points (email gateways, web upload handlers, document management systems) using tools like `mat2` (Metadata Anonymisation Toolkit — a Python tool that strips metadata from multiple file formats), `exiftool` (for image metadata removal), and the built-in document inspector in Microsoft Office. Group Policy can enforce metadata removal for Office documents at the organizational level, and DLP solutions can detect and block outbound documents containing specific metadata fields.

Employee social media policy enforcement addresses the human dimension of digital footprint reduction. Employees who post about their work on LinkedIn, X/Twitter, or personal blogs inadvertently reveal: the technology stack the organization uses (an engineer posting about migrating to Kubernetes reveals the infrastructure platform; a developer's GitHub profile showing contributions to the company's open-source projects reveals the programming languages and frameworks in use), the organization's security tooling (a SOC analyst posting about their experience with CrowdStrike or Splunk reveals the defensive tools an attacker would need to evade), organizational structure (LinkedIn profiles reveal reporting relationships, team sizes, and project names), and personnel changes (job postings reveal technology decisions and potential security gaps — a job posting for a "Palo Alto firewall administrator" reveals both the firewall vendor and a possible staffing gap). Security awareness training should include OPSEC guidance for social media, and the security team should conduct periodic OSINT assessments of the organization's social media exposure using the same techniques an attacker would use (LinkedIn scraping for employee enumeration, GitHub org analysis for technology stack identification, job posting analysis for infrastructure intelligence).

### 4.2 Counter-reconnaissance detection

Detecting attacker reconnaissance before it progresses to exploitation provides the earliest possible warning of a targeted attack. Counter-reconnaissance techniques create tripwires that alert defenders when an attacker probes the organization's perimeter.

Honeypot domains are registered domains that resemble the organization's legitimate domains (typosquatting variants, old/deprecated domains, domains mentioned in historical documents but no longer in use) but are configured solely to detect attacker interest. Any DNS queries for these domains, any HTTP requests to them, or any emails sent to addresses at these domains are inherently suspicious because no legitimate user or system should be interacting with them. The domains should resolve to honeypot infrastructure (servers that log all interactions in detail) and should be monitored through DNS query logs (if the organization operates its own recursive resolvers) or through managed DNS services that provide query analytics. When an attacker performing DNS enumeration (subfinder, amass, massdns) discovers and probes a honeypot domain, the DNS query and subsequent HTTP request generate an alert. This detection occurs during the reconnaissance phase — before the attacker has identified and begun exploiting a real target.

Canary DNS records follow the same principle at the DNS record level. The organization adds DNS records (A records, TXT records, MX records) that serve no legitimate purpose but will be discovered by an attacker performing DNS enumeration. For example, a TXT record containing a fake AWS access key (a canary token — services like Thinkst Canary and canarytokens.org generate tokens that trigger alerts when used) will be discovered by an attacker who enumerates TXT records looking for cloud credentials. When the attacker attempts to use the fake AWS key, the canary token service alerts the security team. Similarly, A records pointing to internal honeypot IP addresses will generate alerts when an attacker scans those IPs after discovering them through DNS enumeration.

Setting up canary DNS records and honeypot infrastructure:

```bash
# 1. Generate canary tokens via canarytokens.org API or Thinkst Canary
# AWS key canary — generates a fake AKIA key that alerts on use
curl -s -X POST https://canarytokens.org/generate \
  -d "type=aws-id&email=soc-alerts@targetcorp.com&memo=DNS+TXT+canary"
# Returns: {"aws_access_key_id": "AKIAIOSFODNN7EXAMPLE", ...}

# 2. Add canary TXT record to DNS zone
# In the zone file (or via DNS provider API):
# _internal-config.targetcorp.com  TXT  "aws_access_key_id=AKIAIOSFODNN7EXAMPLE"
# _internal-config.targetcorp.com  TXT  "aws_secret_access_key=FAKEKEY..."
# Attackers enumerating TXT records will find and try to use these keys.

# 3. Create a honeypot subdomain with a canary web server
# admin-portal.targetcorp.com  A  198.51.100.99  (honeypot IP)
# Any request to admin-portal.targetcorp.com triggers an alert.

# 4. Deploy a simple canary web server (Flask example for logging)
# canary_server.py:
# from flask import Flask, request
# import json, datetime
# app = Flask(__name__)
# @app.route('/', defaults={'path': ''})
# @app.route('/<path:path>')
# def catch_all(path):
#     alert = {
#         "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
#         "source_ip": request.remote_addr,
#         "method": request.method,
#         "path": f"/{path}",
#         "headers": dict(request.headers),
#         "user_agent": request.user_agent.string,
#     }
#     # Forward to SIEM / Slack / TheHive
#     print(json.dumps(alert))
#     return "<html><body>Access Denied</body></html>", 403
```

Enumeration detection through behavioral analysis identifies reconnaissance by analyzing the patterns of incoming requests. Web application firewalls (WAFs) and rate-limiting infrastructure can detect enumeration patterns: rapid sequential requests to predictable URL patterns (directory brute-forcing), requests for paths associated with known reconnaissance tools (the nuclei scanner sends requests with characteristic User-Agent strings and URL patterns, as does Nmap's HTTP scripts), high volumes of requests returning 404 responses (indicating directory or file enumeration), and requests for administrative paths (`/admin`, `/wp-admin`, `/manager/html`, `/.git/config`, `/server-status`). Rate limiting and behavioral detection should be configured at the reverse proxy layer:

```nginx
# nginx — enumeration detection via rate limiting and 404 monitoring.
# Place in http {} block of nginx.conf.

# Rate limit zone: 10 requests/second per IP, burst of 20
limit_req_zone $binary_remote_addr zone=recon_detect:10m rate=10r/s;

server {
    listen 443 ssl;
    server_name www.targetcorp.com;

    # Apply rate limiting
    limit_req zone=recon_detect burst=20 nodelay;
    limit_req_status 429;

    # Log 404s to a separate file for analysis
    # High 404 rates from a single IP = probable enumeration
    map $status $is_404 {
        404 1;
        default 0;
    }
    access_log /var/log/nginx/recon_404.log combined if=$is_404;

    # Block requests for known recon tool signatures
    if ($http_user_agent ~* "(nuclei|sqlmap|nikto|dirbuster|gobuster|ffuf|wfuzz)") {
        return 403;
    }

    # Honeypot paths — any request here is suspicious, log and block
    location ~* ^/(\.git|\.env|wp-admin|phpmyadmin|server-status|actuator) {
        access_log /var/log/nginx/honeypot_hits.log combined;
        return 403;
    }
}
```

When these patterns are detected, the response should be graduated: initial slow-down (rate limiting), then temporary blocking, then permanent blocking and alerting. The detection should feed into the SIEM for correlation with other indicators (the same source IP appearing in DNS query logs, firewall logs, and web server logs within a short time window is a strong indicator of active reconnaissance). Integration with deception technology (Domain 27 Chapter 27A §6) extends this concept by presenting the attacker with convincing but false information — fake login pages that capture submitted credentials, fake API endpoints that return plausible but fabricated data, and fake internal documents seeded with canary tokens that alert when opened.

### 4.3 Personal OPSEC for security practitioners

Security professionals — particularly offensive operators (red team members, penetration testers, vulnerability researchers) and those involved in threat intelligence, incident response, and law enforcement liaison — face personal security risks that require explicit operational security measures. Threat actors who discover they are being investigated may attempt to identify and intimidate the investigators. Doxing (publishing a security researcher's personal information — home address, family members, phone numbers — on attacker forums) is a real and documented risk, as are SWATting (filing a false emergency report to send armed police to the researcher's home) and targeted harassment.

Persona separation is the foundational OPSEC practice. Security practitioners should maintain strict separation between their professional and personal online identities. The professional identity (used for security research publications, conference presentations, bug bounty reports, and threat intelligence sharing) should not be linkable to the personal identity (personal social media, family connections, home address). This requires: using separate email addresses (a professional email that does not contain the person's real name or link to personal accounts), separate phone numbers (a VoIP number for professional use, not the personal mobile number), separate devices (a dedicated laptop for security research that does not contain personal data, browser profiles, or saved passwords for personal services), and separate network connections (not conducting sensitive research from the home IP address, which can be correlated with the researcher's physical location via ISP WHOIS records). The professional persona's online presence should be audited periodically using the same OSINT techniques covered in this chapter — searching for cross-references between the professional and personal identities, checking for metadata leaks in published documents, and verifying that conference registration data (which may include real names and addresses) is not publicly accessible.

Device compartmentalization extends persona separation to hardware. A researcher conducting dark web investigations should use a dedicated device (not a VM on their work laptop, which risks information leakage through clipboard sharing, shared filesystems, and DNS query correlation) running a privacy-focused operating system (Tails for ephemeral sessions — all state is lost on shutdown, preventing forensic recovery; Qubes OS for compartmentalized persistent sessions — each activity runs in a separate VM with strict network and file isolation). The research device should connect to the internet through a dedicated connection (a separate ISP, a mobile hotspot with a prepaid SIM purchased with cash, or a VPN termination point that is not associated with the researcher's personal or corporate identity). Physical security of the research device is also important — the device should use full-disk encryption (LUKS on Linux, FileVault on macOS, BitLocker on Windows — with a strong passphrase, not a PIN), and should be stored securely when not in active use.

Secure communication channels for coordinating sensitive security operations (incident response involving active threat actors, threat intelligence sharing with law enforcement, coordinating vulnerability disclosures with affected vendors) should use end-to-end encrypted messaging (Signal is the standard recommendation for its strong cryptographic protocol, minimal metadata retention, and disappearing messages feature). Email, even when encrypted with PGP/GPG, leaks metadata (sender, recipient, subject line, timestamps) that can reveal operational patterns. For the most sensitive communications, practitioners should use Signal on the dedicated research device, with a phone number that is not linked to their personal identity.

---

## 5. Social Engineering Defense Architecture

### 5.1 Email security gateway architecture

Email remains the primary vector for social engineering attacks — phishing, BEC, malware delivery, and credential harvesting all primarily reach targets via email. Enterprise email security architecture deploys multiple layers of defense: the email security gateway (ESG), email authentication protocols, sandboxing/detonation systems, URL rewriting and time-of-click analysis, and user reporting mechanisms.

The enterprise ESG market is dominated by three vendors for large organizations: Proofpoint Email Protection, Mimecast, and Microsoft Defender for Office 365 (MDO). Proofpoint is the market leader for Fortune 500 organizations, with strength in targeted attack protection (its TAP module uses NexusAI — a machine learning engine trained on Proofpoint's global email telemetry of over 2.8 billion emails per day — to identify previously unknown threats), URL defense (rewriting URLs in emails to route clicks through Proofpoint's proxy for real-time analysis at time of click, not just time of delivery), and attachment defense (sandboxing attachments in a cloud-based environment that executes them and observes behavior for up to two minutes, with analysis for anti-sandbox evasion techniques such as time delays, mouse movement checks, and environment fingerprinting). Mimecast provides similar capabilities with stronger integration for Microsoft 365 environments, including a unified archive for email, IM, and social media content. Microsoft Defender for Office 365 (Plan 2) is the native email security solution for Microsoft 365, with Safe Links (URL rewriting and time-of-click verification), Safe Attachments (sandbox detonation), and anti-phishing policies (impersonation protection using mailbox intelligence to detect senders pretending to be internal executives).

The ESG processes inbound email through a multi-stage pipeline. The connection filter checks the sending IP address against reputation databases (Spamhaus ZEN, Barracuda BRBL, Proofpoint's dynamic reputation system), rate-limits connections from individual IPs (to throttle spam campaigns), and checks SPF alignment (whether the sending IP is authorized by the sender's domain SPF record). The content filter analyzes the email header, body, and attachments: it checks for known-malicious indicators (sender addresses from blocklists, URLs matching phishing domains from threat intelligence feeds, attachment hashes matching known malware), applies machine learning classifiers to detect BEC (analyzing linguistic patterns characteristic of impersonation — urgency language, executive name spoofing, wire transfer requests, reply-to mismatches), and identifies suspicious patterns (emails claiming to be from an internal sender but originating from an external IP, emails with look-alike domains, and emails with brand impersonation). The sandbox (or detonation chamber) executes attachments and visits URLs in an instrumented virtual environment, observing for malicious behavior — file downloads, command execution, registry modification, network connections to known-malicious infrastructure, and credential harvesting page characteristics. The sandbox results inform the delivery decision: deliver (clean), quarantine (suspicious), or block (malicious).

DMARC enforcement at `p=reject` is the strongest email authentication posture, instructing receiving mail servers to reject any email that fails both SPF and DKIM alignment for the organization's domain. The progression from monitoring to enforcement:

```dns
; DMARC deployment progression — DNS TXT records at _dmarc.targetcorp.com
; Each stage requires monitoring aggregate reports (rua) before advancing.

; Stage 1: Monitor mode — collect data, no enforcement (3-6 weeks)
_dmarc.targetcorp.com. TXT "v=DMARC1; p=none; rua=mailto:dmarc-reports@targetcorp.com; ruf=mailto:dmarc-forensics@targetcorp.com; fo=1"
; fo=1: generate forensic reports on any SPF or DKIM failure (not just both)

; Stage 2: Quarantine — failed messages go to spam (4-8 weeks)
_dmarc.targetcorp.com. TXT "v=DMARC1; p=quarantine; pct=25; rua=mailto:dmarc-reports@targetcorp.com; ruf=mailto:dmarc-forensics@targetcorp.com"
; pct=25: apply quarantine to 25% of failing messages initially, ramp up

; Stage 3: Quarantine at 100%
_dmarc.targetcorp.com. TXT "v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc-reports@targetcorp.com"

; Stage 4: Reject — full enforcement
_dmarc.targetcorp.com. TXT "v=DMARC1; p=reject; rua=mailto:dmarc-reports@targetcorp.com; ruf=mailto:dmarc-forensics@targetcorp.com"

; Supporting SPF record — enumerate ALL authorized senders
targetcorp.com. TXT "v=spf1 mx include:_spf.google.com include:spf.protection.outlook.com include:sendgrid.net include:mail.zendesk.com -all"
; CRITICAL: use -all (hard fail), not ~all (soft fail).  ~all does not block.

; DKIM — configured per email provider.  Example selector record:
google._domainkey.targetcorp.com. TXT "v=DKIM1; k=rsa; p=MIIBIjANBgkqh..."

; ARC — Authenticated Received Chain for mailing lists.
; ARC is configured on the mailing list server, not in DNS.
; The list server signs ARC-Authentication-Results, ARC-Message-Signature,
; and ARC-Seal headers, preserving the original authentication chain
; through forwarding that would otherwise break DKIM.
```

The transition from `p=none` to `p=reject` typically takes 3-6 months for large organizations with complex email ecosystems. ARC (Authenticated Received Chain) extends DMARC's applicability to mailing list and forwarding scenarios where the intermediate server modifies the email (breaking DKIM signatures) — ARC allows the intermediate server to attest that the email passed authentication when it was originally received, preserving the authentication chain through forwarding.

### 5.2 Phishing simulation programs

Phishing simulation — sending realistic but benign phishing emails to employees and measuring their response — is a core component of security awareness programs. However, poorly designed phishing simulations can undermine trust, create a hostile work environment, and fail to produce meaningful behavioral change. The design methodology and metrics framework are as important as the technical platform.

Effective phishing simulation programs follow a progressive difficulty framework. The initial baseline assessment uses obvious phishing indicators (misspelled sender domain, generic greeting, grammatically awkward body, suspicious URL) to establish the organization's baseline click rate. Subsequent campaigns progressively increase in sophistication: intermediate campaigns use plausible pretexts (IT department password resets, HR benefits enrollment, package delivery notifications) with subtle indicators (hover-over URL mismatch, slight sender domain variation); advanced campaigns use highly targeted pretexts (referencing real projects, using real executive names, mimicking actual organizational communications) that require careful examination to identify as phishing; and expert-level campaigns simulate state-of-the-art attacks (conversation hijacking in real email threads, consent phishing via OAuth, QR code phishing or "quishing"). Each difficulty level should be clearly defined and consistently applied, and employees should receive immediate, non-punitive feedback when they click — a landing page explaining what the phishing indicators were, how to identify them in the future, and how to report suspicious emails.

The metrics framework should measure behavioral change, not just click rates. Key metrics include: click rate (percentage of employees who clicked the phishing link — the most basic metric), report rate (percentage of employees who reported the email as suspicious using the organization's phishing report button — more important than click rate because it measures the desired behavior), time-to-report (how quickly the first employee reports the phishing email — a metric of organizational awareness velocity), susceptibility by department/role/location (identifying which organizational segments need additional training), repeat offender rate (percentage of employees who fail multiple simulations — these individuals may need targeted one-on-one training or additional technical controls on their accounts), and trend analysis (tracking metrics over time to measure program effectiveness). A mature phishing simulation program targets a click rate below five percent and a report rate above seventy percent. The report rate is the more important metric because a single reporter enables the SOC to investigate and block the phishing campaign for the entire organization, while a low click rate without reporting means each employee is independently defending themselves without contributing to organizational defense.

The behavioral analysis dimension of phishing simulation uses the data to understand why employees fall for specific pretexts. Correlating click rates with simulation variables (pretext type, difficulty level, time of day, day of week, and employee demographics) reveals patterns: employees may be more susceptible to IT-themed pretexts than HR-themed ones, or click rates may spike on Monday mornings when employees are processing weekend email backlogs. These insights inform both training content (focusing on the pretexts that employees are most susceptible to) and technical controls (deploying additional protection for the attack vectors that employees are least able to resist).

### 5.3 SE-resistant authentication: FIDO2/WebAuthn deep dive

Phishing-resistant authentication is the single most effective technical control against credential-based social engineering. FIDO2 (Fast IDentity Online 2) is the umbrella term for the WebAuthn API (which runs in the browser) and the CTAP2 protocol (Client to Authenticator Protocol, which communicates between the browser and the authenticator device). Together, they implement a public-key authentication scheme that is fundamentally resistant to phishing because the authentication credential is bound to the origin (domain name) of the relying party — a credential created for `login.example.com` cannot be used on `login.examp1e.com` (a phishing site), even if the user is tricked into visiting the phishing site and initiating authentication.

The WebAuthn registration flow (attestation) creates a new credential. The following JavaScript demonstrates the browser-side registration and authentication flows:

```javascript
// WebAuthn Registration (Attestation) — browser-side code.
// The server provides the options; the browser mediates with the authenticator.

async function registerCredential() {
  // Server generates these options (challenge must be cryptographically random)
  const publicKeyCredentialCreationOptions = {
    challenge: new Uint8Array(32),  // filled by server — crypto random
    rp: {
      name: "Target Corp",
      id: "login.targetcorp.com",   // RP ID — credential is bound to this origin
    },
    user: {
      id: new Uint8Array(16),       // server-generated opaque user handle
      name: "user@targetcorp.com",
      displayName: "Jane Engineer",
    },
    pubKeyCredParams: [
      { alg: -7,  type: "public-key" },   // ES256 (ECDSA P-256)
      { alg: -257, type: "public-key" },   // RS256 (RSASSA-PKCS1-v1_5)
    ],
    authenticatorSelection: {
      authenticatorAttachment: "cross-platform",  // hardware security key
      // "platform" for biometric (Touch ID, Windows Hello)
      residentKey: "preferred",       // discoverable credential (passkey)
      userVerification: "required",   // PIN or biometric on the authenticator
    },
    attestation: "direct",  // request attestation statement from authenticator
    // "none" = no attestation (simpler), "enterprise" = device identification
    timeout: 60000,
  };

  const credential = await navigator.credentials.create({
    publicKey: publicKeyCredentialCreationOptions,
  });
  // credential.response.attestationObject contains:
  //   - authData (RP ID hash, flags, sign count, credential public key)
  //   - attestation statement (proof of authenticator identity)
  // Send to server for verification and storage.
  return credential;
}


// WebAuthn Authentication (Assertion) — phishing-resistant login.
async function authenticateCredential() {
  const publicKeyCredentialRequestOptions = {
    challenge: new Uint8Array(32),  // server-generated challenge
    rpId: "login.targetcorp.com",
    allowCredentials: [],  // empty = discoverable credential / passkey flow
    // Populate with credential IDs for non-discoverable credentials:
    // [{ id: credentialId, type: "public-key", transports: ["usb","nfc"] }]
    userVerification: "required",
    timeout: 60000,
  };

  const assertion = await navigator.credentials.get({
    publicKey: publicKeyCredentialRequestOptions,
  });
  // assertion.response.authenticatorData includes:
  //   - RP ID hash (MUST match the current origin — this is the phishing defense)
  //   - flags (user presence, user verification)
  //   - sign count (replay detection)
  // assertion.response.signature: signed over clientDataJSON + authenticatorData
  // Send to server; server verifies signature with stored public key.
  return assertion;
}
```

The relying party sends a `PublicKeyCredentialCreationOptions` object to the browser via the `navigator.credentials.create()` API, specifying the relying party ID (the domain name), user information, supported cryptographic algorithms (ES256 — ECDSA with P-256 is the most common, followed by RS256 — RSASSA-PKCS1-v1_5 with SHA-256), and attestation preference (none, indirect, direct, or enterprise). The browser forwards the request to the authenticator (a hardware security key like a YubiKey, a platform authenticator like Windows Hello or Apple Touch ID/Face ID, or a software authenticator), which generates a new key pair, stores the private key (either on the authenticator device for hardware keys, or in the platform's secure enclave — TPM, Secure Enclave, or Android Keystore — for platform authenticators), and returns the public key along with an attestation statement (which proves the authenticator's identity and, for enterprise attestation, the authenticator's model, firmware version, and FIDO certification level). The relying party stores the public key, credential ID, and user association.

The critical security property is that the origin and relying party ID are included in the signed data — if the user is on a phishing site (different origin), the authenticator either refuses to find a matching credential (because no credential was created for the phishing domain) or the signature will not verify (because the signed origin does not match the legitimate site's origin). This makes FIDO2 fundamentally immune to phishing — the user cannot inadvertently authenticate to a fake site because the cryptographic binding to the legitimate domain prevents it.

Passkeys extend FIDO2 by enabling credential synchronization across devices. Traditional FIDO2 credentials (bound to a specific hardware authenticator) have a recoverability problem — if the user loses their security key, they lose access (unless they registered multiple keys or set up recovery codes). Passkeys solve this by storing the private key in a cloud-synchronized credential manager (Apple Keychain for iOS/macOS, Google Password Manager for Android/Chrome, or 1Password/Dashlane for cross-platform). The private key is encrypted with the user's device credentials and synchronized via the platform vendor's cloud infrastructure. Passkeys maintain the phishing resistance of FIDO2 (the credential is still bound to the relying party's origin) while improving usability (no separate hardware device needed, automatic availability across the user's devices). The security tradeoff is that the private key is now stored in a cloud service (protected by the vendor's infrastructure security and the user's platform account security) rather than in a hardware secure element that never exports the key. For high-security environments, hardware-bound credentials (security keys with the `authenticatorAttachment: "cross-platform"` option) remain the recommended choice because the private key provably never leaves the hardware device.

### 5.4 Insider threat programs

Insider threats encompass malicious insiders (employees who intentionally harm the organization — stealing data for personal gain, sabotaging systems out of grievance, or acting on behalf of a competitor or foreign intelligence service), negligent insiders (employees who accidentally cause harm through careless behavior — clicking phishing links, misconfiguring systems, sharing sensitive data inappropriately), and compromised insiders (employees whose accounts or devices have been taken over by an external attacker — through credential theft, social engineering, or malware). Insider threat programs must address all three categories through a combination of behavioral monitoring, technical controls, and organizational measures.

User Behavior Analytics (UBA) and User and Entity Behavior Analytics (UEBA) platforms establish baseline behavioral profiles for each user and detect deviations that may indicate insider threat activity. The behavioral signals analyzed include: access patterns (a user accessing files or systems they have never accessed before, accessing data outside their normal working hours, or accessing large volumes of data in a short period), data movement (a user uploading large amounts of data to external cloud storage, sending large email attachments to personal email accounts, or copying data to USB devices), authentication anomalies (a user logging in from an unusual location or device, using multiple accounts, or failing MFA verification repeatedly), and communication anomalies (a user communicating with external entities not associated with their job function, or a user's email communication patterns changing significantly). UEBA platforms (Securonics, Microsoft Sentinel UEBA, Exabeam, Splunk UBA) assign risk scores to users based on the aggregation of these signals, with alerts generated when scores exceed defined thresholds. The risk scoring must be calibrated to the organization's environment to minimize false positives — an engineer who routinely accesses large datasets will trigger different thresholds than an administrative assistant.

DLP (Data Loss Prevention) integration with the insider threat program provides the technical control layer. DLP systems (Microsoft Purview DLP, Symantec DLP, Forcepoint DLP, Digital Guardian) monitor data in motion (email, web uploads, cloud storage synchronization), data at rest (file servers, databases, cloud storage), and data in use (endpoint monitoring of file access, clipboard operations, screen captures, and printing). DLP policies are defined based on data classification — the organization must first classify its data (PII, financial data, intellectual property, trade secrets, regulated data) and assign sensitivity levels, and the DLP system then enforces policies based on the data's classification (blocking or alerting on attempts to move highly sensitive data to unauthorized destinations). The effectiveness of DLP depends entirely on the accuracy and completeness of data classification — if sensitive data is not classified, DLP cannot protect it.

Legal and privacy considerations constrain insider threat monitoring. In many jurisdictions (particularly the European Union under GDPR, and various US states with employee privacy laws), monitoring employee behavior (email content, browsing history, file access, location) is subject to legal requirements: employees must be notified that monitoring occurs (typically through acceptable use policies and employment agreements), monitoring must be proportionate to the legitimate security interest, and collected data must be handled in accordance with data protection regulations (access-controlled, retained for defined periods, and deleted when no longer needed). The organization's legal counsel and privacy office must be involved in the design and deployment of insider threat monitoring programs to ensure compliance. Employee works councils (in EU jurisdictions) may have co-determination rights over monitoring systems and must be consulted.

### 5.5 Physical security convergence

The convergence of physical and cybersecurity recognizes that attackers do not respect the organizational boundary between the physical security team (responsible for access control, surveillance, and facility protection) and the cybersecurity team (responsible for network, endpoint, and data security). Social engineering attacks frequently combine physical and cyber elements — tailgating to gain physical access, then connecting a rogue device to the network; cloning a badge to access a server room, then exfiltrating data from a physically-accessed server; or impersonating a vendor to gain escorted access to a restricted area, then installing a wireless implant (see Domain 20 Chapter 20A §3 for RF implant techniques and Domain 14 Chapter 14A §2 for on-premises Active Directory attacks enabled by physical access).

Integrated badge system monitoring correlates physical access events with cyber access events. When an employee's badge is used to enter the building at the front door, the security operations center (SOC) should expect to see that employee's account authenticate to the network within a reasonable time window. If the badge is used but no network authentication follows, the badge may have been cloned. If a network authentication occurs from inside the building but no badge entry was recorded, the user may have tailgated. If an employee's badge shows them entering one building while their account authenticates from a different geographic location, the account may be compromised. These cross-domain correlations require integration between the physical access control system (PACS — vendors include HID Global, LenelS2, Genetec, AMAG) and the SIEM/SOAR platform (Domain 31 Chapter 31A §2), with correlation rules that generate alerts for impossible-travel scenarios and badge-to-network timing anomalies.

CCTV analytics with behavioral AI apply computer vision and machine learning to surveillance footage to detect security-relevant behaviors: tailgating (two people passing through a door on a single badge swipe), loitering (a person remaining in a sensitive area for an unusual duration), unauthorized area access (a person entering an area without appropriate badge verification), and suspicious object placement (leaving a package or device in an unusual location). Modern video analytics platforms (Briefcam, Avigilon, Milestone XProtect with analytics plugins) perform these detections in real-time and generate alerts to the security operations center. The integration with cybersecurity is bidirectional: cyber alerts can trigger physical security responses (locking down a floor when a critical security incident is detected), and physical alerts can trigger cyber responses (disabling network ports in an area where a tailgater was detected).

Secure facility design integrates physical security requirements from the earliest architectural phase. For the most sensitive environments (data centers, SOCs, intelligence analysis facilities), design follows SCIF (Sensitive Compartmented Information Facility) standards (ICD 705 — Intelligence Community Directive 705, which specifies construction standards for facilities handling classified information). SCIF requirements include: RF shielding (TEMPEST protection — preventing electromagnetic emanations that could be intercepted to reconstruct displayed information or keyboard input, as discussed in Domain 20 Chapter 20A §5), sound attenuation (preventing conversations from being overheard through walls, ceilings, or duct work), visual protection (preventing observation through windows or gaps), access control (two-person integrity rules, badge plus PIN plus biometric authentication), and electronic device restrictions (no personal electronic devices, no wireless devices, no cameras). While full SCIF construction is only necessary for classified environments, the principles of layered physical security, RF awareness, and electronic device control apply broadly to high-security commercial facilities.

---

## 6. Influence Operations and Disinformation Defense

### 6.1 Nation-state information operations

Information operations — the use of information and information systems to influence, disrupt, or deceive target populations — have become a standard component of nation-state military and intelligence strategy. Understanding these operations is necessary for enterprise security because organizations can be targeted (disinformation campaigns designed to damage a company's reputation, manipulate its stock price, or undermine public trust in its products) and because the techniques used in information operations (fake social media accounts, deepfake media, phishing campaigns) overlap with the techniques used in cyber attacks targeting the enterprise.

Russian information operations provide the most documented case studies. The Internet Research Agency (IRA), based in Saint Petersburg, Russia, was a professional troll farm that employed hundreds of operatives to create fake social media accounts, pose as American citizens, and post divisive content on Facebook, X/Twitter, Instagram, and YouTube. The IRA's operation during the 2016 US presidential election was extensively documented by the Mueller investigation, the Senate Intelligence Committee, and academic researchers. The IRA created approximately 3,500 Facebook accounts and 470 Facebook pages, purchased over 3,500 Facebook advertisements, generated content that was shared by over 126 million Facebook users, and operated Twitter accounts that produced over 10 million tweets. The operation's sophistication included creating both left-wing and right-wing personas to amplify existing societal divisions, organizing real-world events (political rallies) through the fake accounts, and using targeted advertising to reach specific demographic groups in swing states. After the IRA was sanctioned and its operations disrupted, Russian information operations evolved into the Doppelganger campaign (discovered in 2022), which used AI-generated content, typosquatting news domains (creating domains resembling legitimate news outlets like The Washington Post, Fox News, and Bild, and publishing fabricated articles), and automated social media amplification through botnets.

Chinese information operations have different characteristics and objectives. The 50 Cent Army (named for the alleged per-post payment to online commentators) refers to Chinese government-affiliated commentators who post on domestic social media platforms to shape public opinion. For international audiences, the Spamouflage network (identified by Graphika in 2019 and expanded analysis by the Stanford Internet Observatory) operates across X/Twitter, Facebook, YouTube, TikTok, and Reddit, producing pro-China and anti-US content. The Spamouflage network is characterized by low sophistication but high volume: accounts post in English but with Chinese-language grammatical patterns, content is often directly translated from Chinese-language source material, and engagement (likes, shares, comments) is largely from other accounts in the network rather than genuine users, limiting actual influence but creating a visible presence. Chinese information operations have expanded to include: targeting specific narratives (COVID-19 origins, Xinjiang, Hong Kong, Taiwan), co-opting existing communities (infiltrating Reddit and Discord communities related to target topics), and exploiting legitimate platform features (YouTube's algorithm promoting engagement-optimized content, TikTok's content recommendation system).

Iranian information operations, conducted through organizations like the International Union of Virtual Media (IUVM) and traced by organizations including FireEye/Mandiant and the University of Oxford's Computational Propaganda Project, target both domestic and international audiences. Iranian operations focus on promoting Iranian foreign policy objectives (particularly in the Middle East), attacking Saudi Arabia and Israel, and amplifying anti-US sentiment. The tactics include creating fake news websites that mimic legitimate outlets, operating social media accounts that impersonate journalists and activists, and amplifying authentic content from aligned voices rather than generating entirely fabricated content. Iranian operations are generally less sophisticated than Russian operations but are persistent and have adapted to platform enforcement actions by rapidly creating replacement accounts and migrating between platforms.

Coordinated inauthentic behavior (CIB) detection at the enterprise level requires monitoring for campaigns that target the organization specifically. Signs of a targeted information operation include: sudden appearance of multiple social media accounts posting negative content about the organization (especially if the accounts share creation dates, posting patterns, or content templates), fabricated news articles appearing on typosquatting news domains, fake reviews on business review platforms (Google, Glassdoor, Trustpilot), manufactured controversy on Reddit or industry forums, and deepfake audio/video of executives (discussed in section 6.2 below). Enterprise brand monitoring services (Brandwatch, Meltwater, ZeroFox, Flashpoint) provide detection capabilities for these scenarios, and the response playbook should include: documenting the campaign (preserving evidence with timestamps and screenshots), reporting to the affected platforms (using platform-specific inauthentic behavior reporting channels), notifying law enforcement if the campaign appears to be state-sponsored or constitutes fraud, and issuing public communications if the campaign gains sufficient traction to affect stakeholders.

### 6.2 Deepfake detection and media authentication

Synthetic media — AI-generated or AI-manipulated audio, images, and video — presents a growing threat to social engineering defense because it undermines the assumption that seeing and hearing are reliable forms of verification. Deepfake technology has progressed rapidly: face-swapping in video (using generative adversarial networks or diffusion models to replace one person's face with another's in a video, preserving the source video's expressions and head movements), voice cloning (using text-to-speech models trained on a few seconds to a few minutes of the target's voice to generate speech in the target's voice saying arbitrary text), and full video generation (generating entirely synthetic video of a person speaking from a text prompt or audio input). The barrier to entry has dropped dramatically — open-source tools like DeepFaceLab, FaceFusion, and various Stable Diffusion checkpoints enable face-swapping with consumer hardware, and commercial voice cloning services (ElevenLabs, Respeecher, Resemble.AI) can clone a voice from a short audio sample.

The social engineering implications are direct. Voice deepfakes enable enhanced vishing: the attacker clones an executive's voice from public sources (earnings calls, conference presentations, media interviews, podcasts) and calls an employee while impersonating the executive, instructing them to transfer funds, share credentials, or take other actions. This has moved from theoretical to operational — in 2019, the CEO of a UK energy company was defrauded of approximately $243,000 when he received a phone call from what he believed was his boss (the CEO of the parent company), instructing him to wire funds to a Hungarian supplier. The voice was a deepfake generated from publicly available recordings. In 2024, a Hong Kong multinational lost approximately $25 million when an employee in the finance department participated in a video conference call with what appeared to be the company's CFO and several other executives — all deepfakes generated in real-time. The employee, seeing familiar faces and hearing familiar voices, executed the requested wire transfers without additional verification.

Detection of deepfake media employs multiple approaches. Frequency-domain analysis exploits the fact that GAN-generated images and face-swapped video frames contain statistical artifacts not present in authentic media. The discrete Fourier transform (DFT) of a GAN-generated image reveals spectral peaks at specific frequencies corresponding to the generator's upsampling architecture (transposed convolution layers produce periodic checkerboard patterns in the frequency domain). The following analysis pipeline demonstrates the technique:

```python
# deepfake_frequency_analysis.py — Frequency-domain deepfake detection.
# GAN-generated images exhibit characteristic spectral artifacts.

import numpy as np
from PIL import Image
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt


def compute_azimuthal_average(spectrum_2d: np.ndarray) -> np.ndarray:
    """Compute radially-averaged power spectrum (1D from 2D FFT magnitude)."""
    h, w = spectrum_2d.shape
    cy, cx = h // 2, w // 2
    Y, X = np.ogrid[:h, :w]
    R = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2).astype(int)
    max_r = min(cy, cx)
    radial_mean = np.zeros(max_r)
    for r in range(max_r):
        mask = R == r
        if mask.any():
            radial_mean[r] = spectrum_2d[mask].mean()
    return radial_mean


def analyze_image(image_path: str, output_path: str) -> dict:
    """
    Compute 2D FFT and radial power spectrum of an image.
    GAN artifacts manifest as peaks in the radial spectrum that deviate
    from the natural 1/f falloff characteristic of real photographs.
    """
    img = Image.open(image_path).convert("L")  # grayscale
    arr = np.array(img, dtype=np.float64)

    # 2D FFT, shift DC to center, compute log magnitude
    fft2 = np.fft.fft2(arr)
    fft_shifted = np.fft.fftshift(fft2)
    magnitude = np.log1p(np.abs(fft_shifted))

    # Radial average
    radial = compute_azimuthal_average(magnitude)

    # Natural images follow ~1/f power law.  GAN artifacts cause
    # deviations (peaks) at specific frequencies.
    freqs = np.arange(len(radial))
    # Fit 1/f baseline on low frequencies (skip DC)
    low = slice(5, len(radial) // 4)
    log_f = np.log(freqs[low])
    log_p = np.log(radial[low] + 1e-10)
    slope, intercept = np.polyfit(log_f, log_p, 1)
    baseline = np.exp(intercept) * (freqs + 1e-10) ** slope
    residual = radial - baseline
    peak_score = np.max(np.abs(residual[10:])) / np.std(residual[10:])

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    axes[0].imshow(arr, cmap="gray")
    axes[0].set_title("Input")
    axes[1].imshow(magnitude, cmap="viridis")
    axes[1].set_title("2D FFT Magnitude")
    axes[2].plot(freqs, radial, label="Radial spectrum")
    axes[2].plot(freqs, baseline, "--", label="1/f baseline")
    axes[2].set_title(f"Radial Spectrum (peak z={peak_score:.1f})")
    axes[2].legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    return {"peak_z_score": float(peak_score), "slope": float(slope)}

# Usage:
# result = analyze_image("suspect_headshot.jpg", "analysis.png")
# if result["peak_z_score"] > 4.0:
#     print("[!] Frequency anomaly detected — likely synthetic/GAN-generated")
```

Visual deepfake detection analyzes video for temporal inconsistencies (flickering at face boundaries, inconsistent blinking patterns — early deepfake models did not accurately model blinking, though newer models have corrected this), spatial inconsistencies (asymmetric facial features, inconsistent lighting between the face and background, teeth and hair rendering artifacts), and frequency-domain artifacts. Audio deepfake detection analyzes speech for prosody anomalies (unnatural rhythm, stress patterns, or intonation), spectral artifacts (frequency-domain patterns characteristic of speech synthesis), and environmental inconsistencies (the generated voice may not exhibit the room acoustics, background noise, or microphone characteristics expected of the claimed recording environment). Microsoft's Video Authenticator, Intel's FakeCatcher, and academic tools from the MIT Media Lab and the University of Buffalo provide automated deepfake detection capabilities, though detection accuracy degrades as generation techniques improve — the arms race between generation and detection is ongoing.

Media provenance — proving the authenticity and origin of media rather than trying to detect forgery — is the complementary approach. The C2PA (Coalition for Content Provenance and Authenticity, founded by Adobe, Arm, Intel, Microsoft, and Truepic) developed the Content Credentials standard, which embeds cryptographically signed metadata into media files at the point of capture. A C2PA-enabled camera or smartphone signs the captured image/video with a hardware-backed key at the moment of capture, recording the device identity, capture timestamp, GPS location, and camera settings. Subsequent edits (crops, filters, color correction) are recorded as signed edit operations, creating a chain of provenance from capture through publication. The viewer can verify the provenance chain to confirm that the media originated from a known device and has a documented edit history.

```bash
# C2PA Content Credentials verification using the c2patool CLI
# https://github.com/contentauth/c2patool

# Verify Content Credentials in an image
c2patool verify photo.jpg
# Output: manifest store with signing certificates, assertions (capture device,
# GPS, timestamp, edit history), and validation status.

# Display full manifest chain
c2patool manifest photo.jpg --output manifest.json
# Inspect: jq '.assertions[] | {label, data}' manifest.json

# Check if an image has been modified since signing
c2patool verify --strict photo.jpg
# --strict: fail if any assertion cannot be validated or chain is broken

# For media WITHOUT Content Credentials:
# Absence of credentials is a signal but not proof of forgery —
# most legitimate media does not yet carry C2PA metadata.
# Combine with frequency-domain analysis (above) for assessment.
```

The Content Credentials standard has been adopted by Adobe (integrated into Photoshop, Lightroom, and Firefly), Leica (in the M11-P camera), Sony, Nikon, Canon, and integrated into social media platforms (LinkedIn and Instagram display Content Credentials when present). The limitation is adoption: Content Credentials only work if the entire chain — capture, editing, distribution, and display — supports the standard, and deepfake media does not carry Content Credentials (which is itself a signal, but absence of credentials cannot be treated as proof of forgery since most legitimate media also does not yet carry credentials).

### 6.3 Brand impersonation and typosquatting defense

Brand impersonation — creating fake websites, social media accounts, email addresses, or mobile apps that impersonate a legitimate organization — enables phishing, credential harvesting, malware distribution, and fraud. Defending against brand impersonation requires proactive monitoring, rapid detection, and effective takedown processes. This section focuses on the defensive architecture rather than the offensive techniques, which were covered in Domain 23 Chapter 23A §1.2.

Certificate transparency monitoring, as discussed in section 2.3, provides one detection channel. When a phishing actor registers a typosquatting domain and obtains a TLS certificate (which they must do to serve HTTPS content and avoid browser security warnings), the certificate appears in CT logs. Monitoring CT logs with fuzzy matching rules (detecting certificates for domains that are visually or phonetically similar to the organization's domains) provides early warning of phishing infrastructure preparation — often before the phishing emails are sent. The monitoring system should generate alerts with sufficient context for the analyst to assess the threat: the certificate's subject, issuer, issuance date, associated IP address (from DNS lookup), and a screenshot of the website (if it is already serving content). Automated screenshot collection (using headless browsers like Playwright or Puppeteer to capture the page as rendered) is critical because phishing pages often closely replicate the legitimate site's visual appearance, and the analyst needs to see the content to assess whether it is a genuine phishing page or a legitimate entity with a coincidentally similar domain.

Domain monitoring services go beyond CT log monitoring to cover domain registration events, DNS changes, and web content monitoring. Services from vendors like PhishLabs (now part of Fortra), Bolster, Proofpoint (via its Domain Fraud Monitoring module), and MarkMonitor monitor newly-registered domains against the organization's brand terms and domain portfolio, using multiple matching techniques: exact match (the organization's name or primary domain in a new registration), fuzzy match (Levenshtein distance, keyboard-proximity typos, common misspelling patterns), homoglyph match (Unicode characters that visually resemble Latin characters), and combo match (the organization's name combined with common phishing terms — `login`, `secure`, `verify`, `update`, `portal`). When a potentially infringing domain is detected, the service provides risk scoring based on the domain's configuration (Does it have MX records suggesting email capability? Does it have an A record pointing to active hosting? Does its web content replicate the organization's site?), and the security team triages alerts based on this scoring.

Takedown processes for confirmed brand impersonation involve multiple channels. For domain takedowns, the UDRP (Uniform Domain-Name Dispute-Resolution Policy, administered by WIPO) provides a formal arbitration process for .com/.net/.org and most gTLDs, with decisions typically rendered within 60 days. For faster action, the URS (Uniform Rapid Suspension System) provides a quicker process (typically 18-20 days) for clear-cut cases of abusive registration but only suspends the domain (does not transfer it). For ccTLDs, each country code registry has its own dispute resolution process. For urgent takedowns (active phishing campaigns), direct contact with the registrar's abuse team (identified via the WHOIS `abuse@` contact) and the hosting provider's abuse team is faster than formal dispute resolution — many registrars and hosting providers will suspend a domain within hours of receiving a well-documented phishing report with screenshots, URLs, and victim reports. For phishing pages hosted on legitimate services (Google Sites, Microsoft Azure, AWS, Cloudflare Pages), the respective cloud provider's abuse reporting process should be used. Anti-phishing organizations (APWG — Anti-Phishing Working Group) aggregate phishing reports and distribute blocklist data to browsers and email gateways, which provides broad protection even before the phishing domain is taken down.

Phishing kit detection extends the defense beyond individual domains to the tools that phishing actors use. Phishing kits — packaged software that creates convincing replicas of target websites and harvests submitted credentials — are sold on dark web forums and Telegram channels. Each kit has characteristic fingerprints: specific HTML structures, JavaScript patterns (credential exfiltration code, anti-bot evasion code, geolocation-based targeting code), CSS files, and image resources. Some kits include telemetry that sends harvested credentials not only to the operator but also to the kit author (a backdoor in the phishing kit — the kit author steals the credentials that the kit operator steals from victims). Security researchers analyze phishing kits to extract these fingerprints, which are then used to detect new deployments of the same kit across different domains. Proofpoint, Recorded Future, and Group-IB maintain phishing kit databases that map kit fingerprints to threat actor groups, enabling attribution and tracking of phishing campaigns at the operator level rather than the domain level.

---

## 7. Cross-Domain Integration and Defensive Maturity

### 7.1 Connecting OSINT to threat intelligence operations

The intelligence gathered through the techniques described in this chapter — infrastructure pivoting chains, dark web monitoring, credential exposure alerts, social media intelligence, and influence operation detection — reaches its full value only when integrated into the organization's threat intelligence program (Domain 25 Chapter 25A §3). The Diamond Model of intrusion analysis provides the framework for this integration: OSINT findings populate the model's four vertices (adversary, infrastructure, capability, victim) and the analyst uses the model to pivot between vertices. A credential exposure in a stealer log (victim vertex) leads to identification of the stealer C2 server (infrastructure vertex), which through passive DNS pivoting reveals other C2 domains (infrastructure expansion), which through JARM fingerprinting identifies the C2 framework (capability vertex), which through threat intelligence correlation attributes the operation to a specific threat group (adversary vertex). Each pivot expands the organization's understanding of the threat and enables defensive actions: blocking the C2 infrastructure, hunting for the stealer malware on endpoints, resetting compromised credentials, and deploying detection rules for the specific TTPs associated with the attributed threat group.

Detection engineering (Domain 27 Chapter 27A §4) consumes OSINT outputs directly. CT log monitoring generates detection rules for newly-identified phishing domains (blocking the domains in DNS sinkholes, web proxies, and email gateways). JARM and JA3 fingerprints generate network detection rules (alerting on TLS sessions matching known-malicious fingerprints). Stealer log monitoring generates identity-based detections (monitoring for authentication from compromised accounts and triggering step-up authentication or account lockout). Dark web IAB listing monitoring generates hunting hypotheses (if an IAB advertises access to the organization's industry sector and geographic region, the security team should proactively hunt for indicators of initial access — unexpected VPN connections, new remote access tools, lateral movement patterns).

The defensive architecture described in section 5 — email security gateways, phishing simulations, FIDO2 authentication, insider threat monitoring, and physical security convergence — forms the protective layer that the OSINT and threat intelligence layer informs and directs. Deception technology (Domain 27 Chapter 27A §6) closes the loop by generating intelligence from attacker interactions with honeypots and canary tokens, feeding this intelligence back into the OSINT analysis pipeline for further pivoting and attribution. This bidirectional flow — OSINT informing defenses, and deception-generated intelligence informing OSINT — creates a continuously improving defensive posture where each attacker interaction generates intelligence that strengthens detection and prevention capabilities.

### 7.2 Maturity model for social engineering defense

Organizations progress through maturity levels in social engineering defense. At the foundational level, the organization has deployed email security gateways, conducts annual phishing awareness training, and has basic DMARC (at `p=none`) and MFA (push-based) deployed. At the managed level, DMARC is enforced at `p=reject`, MFA uses number matching, phishing simulations run quarterly with progressive difficulty, credential exposure monitoring is active, and the security team performs periodic OSINT assessments of the organization's external footprint. At the advanced level, authentication is phishing-resistant (FIDO2/passkeys for all external-facing and high-privilege access), ASM runs continuously with automated alerting, dark web monitoring covers credential shops and IAB listings, insider threat monitoring (UEBA) is deployed, physical and cyber security are integrated in the SOC, and CT log monitoring detects brand impersonation in near-real-time. At the optimized level, the organization operates an integrated intelligence-driven defense where OSINT collection, threat intelligence analysis, detection engineering, and deception technology form a continuous feedback loop, influence operation monitoring protects the organization's brand and reputation, and the security team has the capability to attribute and track threat actors across campaigns.

Each maturity level builds on the previous one, and attempting to implement advanced capabilities without the foundational and managed layers in place results in gaps that attackers will exploit. An organization with sophisticated dark web monitoring but no DMARC enforcement has visibility into threats but lacks the basic controls to prevent the most common attack vector. The maturity model provides a roadmap for incremental capability development, with each level reducing the organization's risk exposure to social engineering and OSINT-enabled attacks.

---

## 8. OSINT Detection Engineering

Where section 3 described the ProjectDiscovery toolchain for attack surface discovery and section 7.1 discussed integrating OSINT outputs into the threat intelligence program, this section focuses on building detection and alerting pipelines that transform raw OSINT collection into actionable SOC alerts — data broker monitoring, credential leak detection, brand impersonation domain alerting, leaked source code detection, YARA rules for identifying OSINT tool artifacts on compromised hosts, and continuous attack surface delta monitoring.

### 8.1 Data broker monitoring and PII exposure alerting

Data brokers aggregate and sell personal information — names, addresses, phone numbers, employment history, relatives, and in some cases email addresses and partial financial data — scraped from public records, social media, and commercial data partnerships. For organizations, data broker exposure of employees (particularly executives, security staff, and personnel with elevated access) creates a pretext-enrichment pipeline: an attacker purchasing a data broker report on a target obtains the social context (home address, family members, previous employers, estimated income, property records) needed to construct convincing pretexts for spear-phishing, vishing, and physical social engineering.

Automated monitoring requires querying data broker APIs (where available) or scraping data broker sites for the organization's personnel. The following Python script implements a monitoring workflow that checks multiple data broker sources and generates alerts when new PII exposure is detected:

```python
# data_broker_monitor.py — Automated data broker exposure monitoring.
# Checks a list of personnel against known data broker APIs and generates
# alerts when new exposure is detected.

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

STATE_FILE = Path(os.environ.get("BROKER_STATE_FILE", "/opt/osint-monitor/state/broker_exposure.json"))
ALERT_WEBHOOK = os.environ["ALERT_WEBHOOK_URL"]  # Slack / Teams / TheHive webhook

# Data broker sources — each implements a check(person) -> list[ExposureRecord]
BROKER_SOURCES = {
    "beenverified": {
        "base_url": "https://api.beenverified.com/v2",
        "api_key_env": "BEENVERIFIED_API_KEY",
    },
    "spokeo": {
        "base_url": "https://api.spokeo.com/v1",
        "api_key_env": "SPOKEO_API_KEY",
    },
    "intelius": {
        "base_url": "https://api.intelius.com/v1",
        "api_key_env": "INTELIUS_API_KEY",
    },
}


def load_personnel(path: str = "/opt/osint-monitor/config/personnel.json") -> list[dict]:
    """Load monitored personnel list.  Schema: [{"name": "...", "email": "...", "role": "..."}]"""
    with open(path) as f:
        return json.load(f)


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def fingerprint(record: dict) -> str:
    """Deterministic hash of an exposure record for dedup."""
    canonical = json.dumps(record, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def query_broker(source_name: str, config: dict, person: dict) -> list[dict]:
    """Query a single data broker API for a person.  Returns raw exposure records."""
    api_key = os.environ.get(config["api_key_env"])
    if not api_key:
        logger.warning("No API key for %s — skipping", source_name)
        return []
    try:
        resp = requests.get(
            f"{config['base_url']}/person/search",
            params={"name": person["name"], "email": person.get("email", "")},
            headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])
    except requests.RequestException as exc:
        logger.error("Broker %s query failed for %s: %s", source_name, person["name"], exc)
        return []


def send_alert(person: dict, source: str, new_records: list[dict]) -> None:
    """Send an alert for newly-discovered PII exposure."""
    payload = {
        "text": (
            f"*Data Broker Exposure Alert*\n"
            f"Person: {person['name']} ({person.get('role', 'unknown role')})\n"
            f"Source: {source}\n"
            f"New records: {len(new_records)}\n"
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
            f"Action: Review exposure and initiate opt-out if warranted."
        ),
    }
    try:
        requests.post(ALERT_WEBHOOK, json=payload, timeout=10)
    except requests.RequestException as exc:
        logger.error("Alert delivery failed: %s", exc)


def run_cycle() -> None:
    personnel = load_personnel()
    state = load_state()

    for person in personnel:
        person_key = person["email"]
        if person_key not in state:
            state[person_key] = {}

        for source_name, config in BROKER_SOURCES.items():
            records = query_broker(source_name, config, person)
            known_fps = set(state[person_key].get(source_name, []))
            new_records = []
            new_fps = []

            for record in records:
                fp = fingerprint(record)
                if fp not in known_fps:
                    new_records.append(record)
                    new_fps.append(fp)

            if new_records:
                logger.info(
                    "New exposure: %s on %s — %d records",
                    person["name"], source_name, len(new_records),
                )
                send_alert(person, source_name, new_records)

            state[person_key][source_name] = list(known_fps | set(new_fps))
            time.sleep(2)  # rate-limit courtesy

    save_state(state)
    logger.info("Cycle complete — %d personnel checked", len(personnel))


if __name__ == "__main__":
    run_cycle()
```

Deploy the monitor as a cron job or systemd timer running weekly. The state file tracks previously-seen exposure records to suppress duplicate alerts; only genuinely new exposure generates notifications. Priority personnel (executives, security team, finance, HR) should be checked first and with higher alert severity.

### 8.2 Credential leak detection with HIBP API integration

Section 3.2 discussed breach database monitoring conceptually. This subsection provides the operational detection pipeline — integrating HIBP's domain-search and Pwned Passwords APIs into the SOC alerting workflow so that credential exposure generates actionable alerts with automated response actions.

The HIBP domain-search API (available with an enterprise subscription) enables monitoring all email addresses under one or more organizational domains. The API returns a list of breaches affecting each email address, including the breach name, date, data classes exposed (email, password, phone, physical address, etc.), and whether the breach data is verified or unverified (paste-based). The detection pipeline polls the HIBP API on a schedule, compares results against a state baseline, and generates tiered alerts based on the breach data classes:

```python
# hibp_domain_monitor.py — Credential exposure monitoring via HIBP domain search API.
# Generates SIEM-ingestible alerts for newly-exposed credentials.

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

HIBP_API_KEY = os.environ["HIBP_API_KEY"]
HIBP_BASE = "https://haveibeenpwned.com/api/v3"
MONITORED_DOMAINS = os.environ.get("HIBP_DOMAINS", "example.com").split(",")
STATE_DIR = Path(os.environ.get("HIBP_STATE_DIR", "/opt/osint-monitor/state/hibp"))
SIEM_WEBHOOK = os.environ["SIEM_INGEST_WEBHOOK"]  # e.g., Splunk HEC or Elastic webhook

HEADERS = {
    "hibp-api-key": HIBP_API_KEY,
    "User-Agent": "OrgBreachMonitor/1.0",
    "Accept": "application/json",
}

# Severity mapping based on exposed data classes
CRITICAL_DATA_CLASSES = {"Passwords", "Password hints", "Credit cards", "Bank account numbers",
                         "Social security numbers", "Government issued IDs"}
HIGH_DATA_CLASSES = {"Phone numbers", "Physical addresses", "Dates of birth",
                     "Security questions and answers", "Auth tokens"}


def get_domain_breaches(domain: str) -> list[dict]:
    """Retrieve all breached accounts for a domain via HIBP domain search."""
    url = f"{HIBP_BASE}/breacheddomain/{domain}"
    resp = requests.get(url, headers=HEADERS, timeout=60)
    if resp.status_code == 404:
        return []  # no breaches — clean domain
    resp.raise_for_status()
    # Response: { "alias1": [breach_list], "alias2": [breach_list], ... }
    results = []
    for alias, breaches in resp.json().items():
        email = f"{alias}@{domain}"
        for breach in breaches:
            results.append({"email": email, "breach": breach})
    return results


def classify_severity(data_classes: list[str]) -> str:
    """Classify alert severity based on exposed data classes."""
    class_set = set(data_classes)
    if class_set & CRITICAL_DATA_CLASSES:
        return "critical"
    if class_set & HIGH_DATA_CLASSES:
        return "high"
    return "medium"


def load_known(domain: str) -> set:
    path = STATE_DIR / f"{domain}.json"
    if path.exists():
        with open(path) as f:
            return set(json.load(f))
    return set()


def save_known(domain: str, known: set) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_DIR / f"{domain}.json", "w") as f:
        json.dump(sorted(known), f)


def emit_siem_alert(record: dict, severity: str) -> None:
    """Send a structured alert to the SIEM for automated triage."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "hibp_domain_monitor",
        "severity": severity,
        "email": record["email"],
        "breach_name": record["breach"],
        "alert_type": "credential_exposure",
        "action_required": (
            "force_password_reset" if severity == "critical"
            else "notify_user_and_monitor"
        ),
    }
    try:
        requests.post(SIEM_WEBHOOK, json={"event": event}, timeout=10)
    except requests.RequestException as exc:
        logger.error("SIEM ingest failed: %s", exc)


def monitor() -> None:
    for domain in MONITORED_DOMAINS:
        logger.info("Checking domain: %s", domain)
        known = load_known(domain)
        records = get_domain_breaches(domain)

        for record in records:
            key = f"{record['email']}:{record['breach']}"
            if key not in known:
                severity = classify_severity(
                    record.get("data_classes", ["Email addresses"])
                )
                logger.info("New exposure: %s in %s [%s]", record["email"], record["breach"], severity)
                emit_siem_alert(record, severity)
                known.add(key)

        save_known(domain, known)
        logger.info("Domain %s: %d total exposure records tracked", domain, len(known))


if __name__ == "__main__":
    monitor()
```

Automated response tiers based on HIBP alert severity:

| Severity | Data classes exposed | Automated response |
|----------|---------------------|--------------------|
| Critical | Passwords, credit cards, SSNs, government IDs | Force password reset, revoke active sessions, trigger MFA re-enrollment, create P1 incident |
| High | Phone numbers, physical addresses, auth tokens, DOB | Notify user, flag account for step-up authentication, create P2 incident |
| Medium | Email addresses only (no passwords) | Log for trending, include in next awareness communication |

The Pwned Passwords API provides a complementary detection channel. During password change events, the identity provider can check the new password against the HIBP Pwned Passwords database using the k-anonymity API (the client sends the first five characters of the SHA-1 hash, the server returns all matching hash suffixes, and the client checks locally — the full password is never transmitted). This prevents employees from selecting passwords that already appear in known breach datasets, regardless of whether the organization's own domain was involved. Azure AD / Entra ID Password Protection and on-premises AD password filters integrate this check natively.

### 8.3 Brand impersonation domain detection pipeline

Section 6.3 described brand impersonation defense concepts and takedown processes. This subsection provides the automated detection pipeline — using `dnstwist` for permutation generation, certstream for real-time CT monitoring, and a delta-alerting architecture that generates SOC-actionable alerts for newly-registered lookalike domains.

The pipeline operates in two modes: scheduled batch scanning (daily `dnstwist` runs against the organization's domain portfolio) and real-time streaming (certstream monitoring for CT-logged certificates matching the organization's brand terms). The batch scan catches domains that were registered without certificates; the real-time stream catches domains the moment a certificate is issued.

```bash
#!/usr/bin/env bash
# brand_impersonation_scan.sh — Scheduled batch scan for lookalike domains.
# Run via cron: 0 6 * * * /opt/osint-monitor/scripts/brand_impersonation_scan.sh
# Dependencies: dnstwist (pip install dnstwist), jq, httpx (ProjectDiscovery)

set -euo pipefail

DOMAINS_FILE="/opt/osint-monitor/config/monitored_domains.txt"
OUTPUT_DIR="/opt/osint-monitor/output/brand_scan"
STATE_DIR="/opt/osint-monitor/state/brand_scan"
ALERT_WEBHOOK="${ALERT_WEBHOOK_URL:?Missing ALERT_WEBHOOK_URL}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
SCAN_DATE=$(date -u +"%Y-%m-%d")

mkdir -p "${OUTPUT_DIR}" "${STATE_DIR}"

while IFS= read -r domain; do
    [[ -z "${domain}" || "${domain}" =~ ^# ]] && continue
    echo "[*] Scanning lookalikes for: ${domain}"

    SCAN_FILE="${OUTPUT_DIR}/${domain}_${SCAN_DATE}.json"
    STATE_FILE="${STATE_DIR}/${domain}.known.txt"
    touch "${STATE_FILE}"

    # Generate all permutations, check registration, resolve DNS, capture WHOIS
    dnstwist --registered --format json --nameservers 1.1.1.1,8.8.8.8 \
        --tld-dict /opt/osint-monitor/config/tld_dict.txt \
        "${domain}" > "${SCAN_FILE}" 2>/dev/null

    # Extract newly-registered domains not in previous state
    jq -r '.[].domain' "${SCAN_FILE}" | sort -u > "/tmp/${domain}_current.txt"
    NEW_DOMAINS=$(comm -23 "/tmp/${domain}_current.txt" <(sort -u "${STATE_FILE}"))

    if [[ -n "${NEW_DOMAINS}" ]]; then
        NEW_COUNT=$(echo "${NEW_DOMAINS}" | wc -l)
        echo "[!] ${NEW_COUNT} new lookalike domains for ${domain}"

        # Probe new domains for live HTTP services
        echo "${NEW_DOMAINS}" | httpx -silent -status-code -title -tech-detect \
            -follow-redirects -threads 10 -o "/tmp/${domain}_alive.txt" 2>/dev/null

        # Generate alert payload
        ALERT_BODY=$(jq -n \
            --arg domain "${domain}" \
            --arg count "${NEW_COUNT}" \
            --arg ts "${TIMESTAMP}" \
            --arg domains "$(echo "${NEW_DOMAINS}" | head -20)" \
            '{text: ("*Brand Impersonation Alert*\nProtected domain: " + $domain + "\nNew lookalikes: " + $count + "\nTimestamp: " + $ts + "\nDomains (first 20):\n```\n" + $domains + "\n```\nAction: Triage in brand protection queue.")}')

        curl -sS -X POST -H "Content-Type: application/json" \
            -d "${ALERT_BODY}" "${ALERT_WEBHOOK}" > /dev/null
    fi

    # Update state file with all known domains
    cat "/tmp/${domain}_current.txt" "${STATE_FILE}" | sort -u > "${STATE_FILE}.tmp"
    mv "${STATE_FILE}.tmp" "${STATE_FILE}"

    rm -f "/tmp/${domain}_current.txt" "/tmp/${domain}_alive.txt"
done < "${DOMAINS_FILE}"

echo "[*] Brand impersonation scan complete: ${TIMESTAMP}"
```

The real-time certstream integration (building on the certstream monitor in section 2.3) adds immediate alerting:

```python
# brand_certstream_alerter.py — Real-time CT log monitoring for brand impersonation.
# Extends the certstream_monitor.py from §2.3 with SOC-grade alerting.

import json
import os
import re
from datetime import datetime, timezone

import certstream
import requests
from Levenshtein import distance as levenshtein_distance

PROTECTED_DOMAINS = os.environ.get("PROTECTED_DOMAINS", "example.com,example.org").split(",")
PROTECTED_BRANDS = os.environ.get("PROTECTED_BRANDS", "example,exmpl").split(",")
ALERT_WEBHOOK = os.environ["ALERT_WEBHOOK_URL"]
MAX_LEVENSHTEIN = int(os.environ.get("MAX_LEVENSHTEIN_DISTANCE", "3"))

# Pre-compile homoglyph mapping for fast lookup
HOMOGLYPHS = {
    "a": ["а", "ɑ", "α"],  # Cyrillic а, Latin alpha, Greek alpha
    "e": ["е", "ё", "ε"],
    "o": ["о", "ο", "ø"],
    "c": ["с", "ϲ"],
    "p": ["р", "ρ"],
    "i": ["і", "ι", "ı"],
    "l": ["ӏ", "ℓ", "1"],
    "s": ["ѕ", "ꜱ"],
    "d": ["ԁ", "ɗ"],
    "n": ["ո", "ñ"],
}


def normalize_homoglyphs(domain: str) -> str:
    """Replace common homoglyph characters with their ASCII equivalents."""
    result = domain
    for ascii_char, homoglyphs in HOMOGLYPHS.items():
        for hg in homoglyphs:
            result = result.replace(hg, ascii_char)
    return result


def is_suspicious(domain: str) -> tuple[bool, str]:
    """Check if a domain is suspicious relative to protected brands."""
    normalized = normalize_homoglyphs(domain.lower())
    base = normalized.split(".")[0]  # strip TLD

    for protected in PROTECTED_DOMAINS:
        protected_base = protected.split(".")[0]
        dist = levenshtein_distance(base, protected_base)
        if 0 < dist <= MAX_LEVENSHTEIN:
            return True, f"levenshtein({base},{protected_base})={dist}"

    for brand in PROTECTED_BRANDS:
        if brand in base and base != brand:
            # Brand term embedded in a different domain
            return True, f"brand_embed({brand} in {base})"

    # Combo keywords: brand + phishing terms
    phish_terms = re.compile(r"(login|secure|verify|update|portal|account|auth|signin|sso|reset)")
    for brand in PROTECTED_BRANDS:
        if brand in base and phish_terms.search(base):
            return True, f"brand_combo({brand}+phishing_term in {base})"

    return False, ""


def on_cert(message, context):
    if message["message_type"] != "certificate_update":
        return

    all_domains = message["data"]["leaf_cert"]["all_domains"]
    for domain in all_domains:
        domain = domain.lstrip("*.")
        suspicious, reason = is_suspicious(domain)
        if suspicious:
            alert = {
                "text": (
                    f"*CT Log Brand Alert*\n"
                    f"Domain: `{domain}`\n"
                    f"Reason: {reason}\n"
                    f"Issuer: {message['data']['leaf_cert'].get('issuer', {}).get('O', 'unknown')}\n"
                    f"SANs: {', '.join(all_domains[:5])}\n"
                    f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
                    f"Action: Investigate and initiate takedown if confirmed."
                ),
            }
            try:
                requests.post(ALERT_WEBHOOK, json=alert, timeout=10)
            except requests.RequestException:
                pass  # logged by upstream handler


if __name__ == "__main__":
    certstream.listen_for_events(on_cert, url="wss://certstream.calidog.io/")
```

### 8.4 Leaked source code and secrets detection

Beyond paste site monitoring (covered in section 1.6 with the Pastebin/GitHub Gist poller), organizations must monitor for leaked proprietary source code appearing on public repositories, code-sharing platforms, and dark web forums. The threat model is twofold: an employee or contractor accidentally pushes proprietary code to a personal GitHub repository (the most common case), or an attacker who has exfiltrated source code publishes it for sale or as proof of breach.

The detection pipeline combines GitHub code search API monitoring, Gitleaks for secrets-in-code detection, and custom Sigma rules for SIEM correlation:

```bash
#!/usr/bin/env bash
# source_leak_monitor.sh — Monitor GitHub for leaked proprietary code.
# Searches GitHub code search for organization-specific identifiers
# (internal package names, proprietary API endpoints, unique comments/headers).

set -euo pipefail

GITHUB_TOKEN="${GITHUB_TOKEN:?Missing GITHUB_TOKEN}"
SEARCH_TERMS_FILE="/opt/osint-monitor/config/code_signatures.txt"
STATE_FILE="/opt/osint-monitor/state/github_code_leaks.json"
ALERT_WEBHOOK="${ALERT_WEBHOOK_URL:?Missing ALERT_WEBHOOK_URL}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# code_signatures.txt contains unique strings that identify proprietary code:
# - Internal package names: "com.example.internal.auth"
# - Proprietary API paths: "/api/v3/internal/billing"
# - Copyright headers: "Copyright 2024 Example Corp. CONFIDENTIAL"
# - Internal domain references: "internal.example.corp"

[ -f "${STATE_FILE}" ] || echo '{}' > "${STATE_FILE}"

while IFS= read -r term; do
    [[ -z "${term}" || "${term}" =~ ^# ]] && continue

    echo "[*] Searching GitHub for: ${term}"

    # GitHub code search — exclude known org repos
    RESULTS=$(curl -sS -H "Authorization: Bearer ${GITHUB_TOKEN}" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/search/code?q=$(python3 -c "import urllib.parse; print(urllib.parse.quote('\"${term}\" -org:our-org'))")&per_page=10" \
        2>/dev/null)

    TOTAL=$(echo "${RESULTS}" | jq -r '.total_count // 0')

    if [[ "${TOTAL}" -gt 0 ]]; then
        # Check if these are new findings
        KNOWN_COUNT=$(jq -r --arg t "${term}" '.[$t] // 0' "${STATE_FILE}")
        if [[ "${TOTAL}" -gt "${KNOWN_COUNT}" ]]; then
            NEW_COUNT=$((TOTAL - KNOWN_COUNT))
            REPOS=$(echo "${RESULTS}" | jq -r '.items[:5] | .[] | .repository.full_name' | sort -u)

            ALERT_BODY=$(jq -n \
                --arg term "${term}" \
                --arg count "${NEW_COUNT}" \
                --arg repos "${REPOS}" \
                --arg ts "${TIMESTAMP}" \
                '{text: ("*Source Code Leak Alert*\nSearch term: `" + $term + "`\nNew matches: " + $count + "\nRepositories:\n```\n" + $repos + "\n```\nTimestamp: " + $ts + "\nAction: Verify leak, initiate DMCA takedown if confirmed.")}')

            curl -sS -X POST -H "Content-Type: application/json" \
                -d "${ALERT_BODY}" "${ALERT_WEBHOOK}" > /dev/null

            # Update state
            jq --arg t "${term}" --argjson c "${TOTAL}" '.[$t] = $c' \
                "${STATE_FILE}" > "${STATE_FILE}.tmp"
            mv "${STATE_FILE}.tmp" "${STATE_FILE}"
        fi
    fi

    sleep 6  # GitHub code search rate limit: 10 requests/minute
done < "${SEARCH_TERMS_FILE}"

echo "[*] Source leak scan complete: ${TIMESTAMP}"
```

### 8.5 YARA rules for OSINT tool artifacts

When performing incident response or insider threat investigations, detecting OSINT tool artifacts on a compromised or suspect host indicates that the adversary (or insider) conducted reconnaissance. These YARA rules identify output files, workspace databases, and configuration artifacts from common OSINT frameworks:

```
rule SpiderFoot_Workspace_Database
{
    meta:
        author      = "Security Engineering"
        description = "Detects SpiderFoot SQLite workspace databases indicating OSINT collection activity"
        date        = "2025-06-15"
        reference   = "https://github.com/smicallef/spiderfoot"
        severity    = "high"

    strings:
        $header     = "SQLite format 3" ascii
        $table1     = "tbl_scan_config" ascii
        $table2     = "tbl_scan_results" ascii
        $table3     = "tbl_scan_log" ascii
        $sf_marker  = "SpiderFoot" ascii wide
        $module_ref = "sfp_" ascii    // SpiderFoot module prefix

    condition:
        $header at 0 and ($sf_marker or (2 of ($table1, $table2, $table3))) and $module_ref
}

rule Maltego_Graph_Export
{
    meta:
        author      = "Security Engineering"
        description = "Detects Maltego graph export files (.mtgl / .mtgx) indicating link analysis activity"
        date        = "2025-06-15"
        reference   = "https://www.maltego.com"
        severity    = "high"

    strings:
        $xml_header    = "<?xml" ascii
        $maltego_ns    = "maltego" ascii nocase
        $graph_entity  = "<MaltegoEntity" ascii
        $graph_edge    = "<MaltegoLink" ascii
        $transform_ref = "<TransformOutput" ascii
        $entity_type1  = "maltego.IPv4Address" ascii
        $entity_type2  = "maltego.Domain" ascii
        $entity_type3  = "maltego.EmailAddress" ascii
        $entity_type4  = "maltego.Person" ascii

    condition:
        $xml_header at 0 and $maltego_ns and
        ($graph_entity or $graph_edge or $transform_ref) and
        (2 of ($entity_type1, $entity_type2, $entity_type3, $entity_type4))
}

rule ReconNG_Workspace
{
    meta:
        author      = "Security Engineering"
        description = "Detects recon-ng workspace databases indicating structured OSINT collection"
        date        = "2025-06-15"
        reference   = "https://github.com/lanmaster53/recon-ng"
        severity    = "high"

    strings:
        $header    = "SQLite format 3" ascii
        $table1    = "domains" ascii
        $table2    = "hosts" ascii
        $table3    = "contacts" ascii
        $table4    = "credentials" ascii
        $table5    = "pushpins" ascii
        $table6    = "ports" ascii
        $reconng1  = "recon-ng" ascii
        $reconng2  = "recon/" ascii

    condition:
        $header at 0 and (3 of ($table1, $table2, $table3, $table4, $table5, $table6))
        and ($reconng1 or $reconng2)
}

rule Amass_Output_JSON
{
    meta:
        author      = "Security Engineering"
        description = "Detects Amass JSON output files from subdomain enumeration campaigns"
        date        = "2025-06-15"
        reference   = "https://github.com/owasp-amass/amass"
        severity    = "medium"

    strings:
        $amass_field1 = "\"name\":" ascii
        $amass_field2 = "\"domain\":" ascii
        $amass_field3 = "\"addresses\":" ascii
        $amass_field4 = "\"tag\":" ascii
        $amass_field5 = "\"sources\":" ascii
        $amass_source = "\"CertSpotter\"" ascii
        $amass_source2 = "\"SecurityTrails\"" ascii
        $amass_source3 = "\"Subfinder\"" ascii

    condition:
        filesize < 100MB and
        (4 of ($amass_field1, $amass_field2, $amass_field3, $amass_field4, $amass_field5)) and
        (1 of ($amass_source, $amass_source2, $amass_source3))
}

rule TheHarvester_Output
{
    meta:
        author      = "Security Engineering"
        description = "Detects theHarvester output files indicating email and subdomain reconnaissance"
        date        = "2025-06-15"
        reference   = "https://github.com/laramies/theHarvester"
        severity    = "medium"

    strings:
        $marker1  = "theHarvester" ascii nocase
        $marker2  = "theharvester" ascii
        $section1 = "[*] Emails found:" ascii
        $section2 = "[*] Hosts found:" ascii
        $section3 = "[*] IPs found:" ascii
        $section4 = "Searching" ascii
        $source1  = "baidu" ascii nocase
        $source2  = "bing" ascii nocase
        $source3  = "certspotter" ascii nocase
        $source4  = "crtsh" ascii nocase

    condition:
        ($marker1 or $marker2) and
        (2 of ($section1, $section2, $section3, $section4)) and
        (1 of ($source1, $source2, $source3, $source4))
}
```

Deploy these YARA rules in the endpoint detection pipeline (YARA scanning in CrowdStrike Falcon, Elastic Defend, or Velociraptor) to detect OSINT tool artifacts during routine host scanning and incident response triage. A positive match on a user workstation that is not assigned to the red team or the threat intelligence team warrants immediate investigation as a potential insider threat or compromised-host indicator.

### 8.6 Attack surface delta monitoring architecture

Section 3 detailed the ProjectDiscovery toolchain for point-in-time ASM scanning. Operationalizing ASM requires a delta-monitoring architecture that tracks state over time, detects changes (new subdomains, removed hosts, changed technologies, new open ports, certificate changes), and generates prioritized alerts for the SOC. The architecture consists of three layers: collection (scheduled scan execution), state management (database tracking asset inventory over time), and alerting (delta computation and notification).

```yaml
# docker-compose.yml — ASM delta monitoring stack
# Components: scheduler (cron), scanner (ProjectDiscovery), state DB (PostgreSQL),
# alerter (Python delta engine), dashboard (Grafana)

version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: asm_state
      POSTGRES_USER: asm
      POSTGRES_PASSWORD_FILE: /run/secrets/pg_password
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    secrets:
      - pg_password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U asm -d asm_state"]
      interval: 10s
      retries: 5

  scanner:
    build:
      context: ./scanner
      dockerfile: Dockerfile
    volumes:
      - scan_output:/opt/scans
      - ./config:/opt/config:ro
    environment:
      - SUBFINDER_CONFIG=/opt/config/subfinder-config.yaml
    depends_on:
      postgres:
        condition: service_healthy

  delta-engine:
    build:
      context: ./delta-engine
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://asm:${PG_PASSWORD}@postgres:5432/asm_state
      ALERT_WEBHOOK_URL: ${ALERT_WEBHOOK_URL}
      SCAN_OUTPUT_DIR: /opt/scans
    volumes:
      - scan_output:/opt/scans:ro
    depends_on:
      postgres:
        condition: service_healthy

  grafana:
    image: grafana/grafana:11.0-oss
    ports:
      - "3000:3000"
    volumes:
      - ./grafana/dashboards:/var/lib/grafana/dashboards
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - postgres

volumes:
  pgdata:
  scan_output:

secrets:
  pg_password:
    file: ./secrets/pg_password.txt
```

```sql
-- sql/init.sql — ASM state database schema

CREATE TABLE IF NOT EXISTS assets (
    id              BIGSERIAL PRIMARY KEY,
    domain          TEXT NOT NULL,
    subdomain       TEXT NOT NULL,
    ip_address      INET,
    http_status     INTEGER,
    page_title      TEXT,
    server_header   TEXT,
    technologies    TEXT[],       -- detected technologies (httpx tech-detect)
    tls_issuer      TEXT,
    tls_expiry      TIMESTAMPTZ,
    first_seen      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    removed_at      TIMESTAMPTZ,  -- NULL = still present
    UNIQUE(domain, subdomain)
);

CREATE TABLE IF NOT EXISTS asset_changes (
    id              BIGSERIAL PRIMARY KEY,
    asset_id        BIGINT REFERENCES assets(id),
    change_type     TEXT NOT NULL CHECK (change_type IN (
                        'new_asset', 'removed_asset', 'ip_change',
                        'tech_change', 'status_change', 'cert_change'
                    )),
    old_value       TEXT,
    new_value       TEXT,
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    alerted         BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_assets_domain ON assets(domain);
CREATE INDEX idx_assets_last_seen ON assets(last_seen);
CREATE INDEX idx_changes_detected ON asset_changes(detected_at);
CREATE INDEX idx_changes_unalerted ON asset_changes(alerted) WHERE NOT alerted;
```

The delta engine compares each scan's results against the database state, computes changes, inserts change records, and fires alerts. New assets and IP changes receive highest priority because they indicate infrastructure expansion (potentially shadow IT or attacker staging). Technology changes (a server switching from nginx to Apache, or a new technology appearing like phpMyAdmin or Kubernetes Dashboard) indicate configuration drift that may introduce vulnerabilities.

### 8.7 Dark web monitoring architecture

Dark web monitoring extends the paste site monitoring described in section 1.6 to .onion hidden services, dark web forums, and marketplace platforms. The architectural challenge is operational: the monitoring infrastructure must access Tor hidden services at scale while maintaining operational security (the monitoring system should not be attributable to the organization). The architecture separates the collection layer (Tor-connected crawlers), the analysis layer (content matching, NER extraction, threat scoring), and the alerting layer (SOC integration).

The collection layer uses a pool of Tor SOCKS proxies with rotating circuits to avoid rate limiting and detection by forum anti-automation defenses. Each crawler instance connects through a dedicated Tor circuit, configured with a separate SocksPort and control port:

```
# /etc/tor/torrc.d/crawler_pool.conf — Multi-circuit Tor configuration
# Each SocksPort maps to an independent Tor circuit for isolation.

SocksPort 9050   # Circuit 1
SocksPort 9052   # Circuit 2
SocksPort 9054   # Circuit 3
SocksPort 9056   # Circuit 4

ControlPort 9051
HashedControlPassword 16:__REDACTED_HASH__

# Rotate circuits every 10 minutes
MaxCircuitDirtiness 600

# Entry guard configuration — use 3 guards for diversity
NumEntryGuards 3

# Disable DNS over Tor exit to prevent leaks
DNSPort 0

# Logging — audit-safe, no content logging
Log notice file /var/log/tor/notices.log
SafeLogging 1
```

The analysis layer processes crawled content against organization-specific detection rules:

```python
# darkweb_analyzer.py — Content analysis engine for dark web monitoring.
# Matches crawled forum posts and marketplace listings against org-specific indicators.

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

import requests


class ThreatCategory(Enum):
    CREDENTIAL_SALE = "credential_sale"
    IAB_LISTING = "initial_access_broker"
    DATA_LEAK = "data_leak"
    RANSOMWARE_LISTING = "ransomware_listing"
    EXPLOIT_SALE = "exploit_sale"
    INSIDER_RECRUITMENT = "insider_recruitment"


@dataclass
class Detection:
    category: ThreatCategory
    confidence: float  # 0.0 - 1.0
    matched_terms: list[str]
    source_url: str
    snippet: str  # redacted excerpt for analyst review
    timestamp: str


ORG_DOMAINS = os.environ.get("ORG_DOMAINS", "example.com").split(",")
ORG_NAMES = os.environ.get("ORG_NAMES", "Example Corp,ExampleCo").split(",")
ORG_ASSET_PATTERNS = [
    re.compile(r"(?:vpn|rdp|citrix|pulse|fortinet)\.(?:" + "|".join(re.escape(d) for d in ORG_DOMAINS) + r")", re.I),
    re.compile(r"(?:" + "|".join(re.escape(n) for n in ORG_NAMES) + r")", re.I),
]

IAB_INDICATORS = re.compile(
    r"(?:selling\s+access|initial\s+access|rdp\s+access|vpn\s+access|"
    r"domain\s+admin|citrix\s+access|network\s+access|"
    r"revenue\s+\$?\d+[MmBb]|employees?\s+\d{3,})",
    re.I,
)

CREDENTIAL_INDICATORS = re.compile(
    r"(?:combolist|combo\s+list|email:pass|user:pass|"
    r"database\s+dump|sql\s+dump|leak(?:ed)?|breach(?:ed)?|"
    r"stealer\s+log|redline|raccoon|vidar|lumma)",
    re.I,
)

RANSOMWARE_INDICATORS = re.compile(
    r"(?:lockbit|alphv|blackcat|cl0p|play\s+ransomware|"
    r"ransom(?:ware)?|data\s+published|leak\s+site|"
    r"negotiation|decrypt(?:or|ion)|proof\s+of\s+(?:files?|data))",
    re.I,
)

ALERT_WEBHOOK = os.environ["ALERT_WEBHOOK_URL"]


def analyze_content(content: str, source_url: str) -> list[Detection]:
    """Analyze a dark web page/post for organization-relevant threats."""
    detections = []
    now = datetime.now(timezone.utc).isoformat()

    # Check for org-specific asset references
    org_match = False
    matched_terms = []
    for pattern in ORG_ASSET_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            org_match = True
            matched_terms.extend(matches)

    if not org_match:
        return []  # content does not reference our organization

    # Classify threat category
    if CREDENTIAL_INDICATORS.search(content):
        detections.append(Detection(
            category=ThreatCategory.CREDENTIAL_SALE,
            confidence=0.85 if len(matched_terms) > 1 else 0.6,
            matched_terms=matched_terms[:10],
            source_url=source_url,
            snippet=content[:500],
            timestamp=now,
        ))

    if IAB_INDICATORS.search(content):
        detections.append(Detection(
            category=ThreatCategory.IAB_LISTING,
            confidence=0.9,  # IAB listings with org name are high-confidence
            matched_terms=matched_terms[:10],
            source_url=source_url,
            snippet=content[:500],
            timestamp=now,
        ))

    if RANSOMWARE_INDICATORS.search(content):
        detections.append(Detection(
            category=ThreatCategory.RANSOMWARE_LISTING,
            confidence=0.95,
            matched_terms=matched_terms[:10],
            source_url=source_url,
            snippet=content[:500],
            timestamp=now,
        ))

    return detections


def alert_detection(det: Detection) -> None:
    severity = "critical" if det.confidence >= 0.8 else "high"
    payload = {
        "text": (
            f"*Dark Web Detection [{severity.upper()}]*\n"
            f"Category: {det.category.value}\n"
            f"Confidence: {det.confidence:.0%}\n"
            f"Matched: {', '.join(det.matched_terms[:5])}\n"
            f"Source: `{det.source_url}`\n"
            f"Timestamp: {det.timestamp}\n"
            f"Action: Escalate to threat intelligence team."
        ),
    }
    requests.post(ALERT_WEBHOOK, json=payload, timeout=10)
```

Dark web monitoring platforms (Recorded Future, Flashpoint, DarkOwl, Searchlight Cyber, KELA) provide commercial alternatives with pre-indexed dark web data, eliminating the need to operate Tor crawling infrastructure. These platforms index thousands of forums, marketplaces, and Telegram channels and provide API-based alerting when organization-specific terms appear. The trade-off is cost (enterprise subscriptions run $50K-$200K+/year) versus the operational complexity and OPSEC risk of self-hosted crawling.

---

## 9. Advanced OSINT Tradecraft

This section deepens the operational tradecraft beyond the introductory sock puppet and OPSEC coverage in Chapter 23A §2.4-2.5, covering the full lifecycle management of collection personas, purpose-built collection infrastructure, advanced geolocation intelligence, and financial OSINT methodology.

### 9.1 Sock puppet lifecycle management

Chapter 23A §2.4 introduced sock puppets — fictitious online identities used for OSINT collection. This section covers the full operational lifecycle: creation, aging, persona development, compartmentation, and retirement. The distinction between a hastily-created throwaway account and a mature, operationally-useful sock puppet is the same distinction between a noisy vulnerability scan and a stealthy red team engagement — the former gets detected and blocked, the latter achieves its collection objective.

**Creation phase.** Each sock puppet requires a foundation of independent infrastructure that cannot be correlated to the operator's real identity or to other sock puppets. The infrastructure stack per persona:

| Layer | Implementation | Isolation requirement |
|-------|---------------|----------------------|
| Email | ProtonMail or Tutanota, registered over Tor | Unique per persona; no recovery email linking |
| Phone | Prepaid SIM (cash-purchased) or virtual number (MySudo, Hushed) | Unique per persona; never used for personal calls |
| VPN exit | Dedicated VPN service or self-hosted WireGuard on a VPS | Exit node geolocated to persona's claimed location |
| Browser | Dedicated Firefox profile or Chromium instance with unique fingerprint | Canvas, WebGL, timezone, language, installed fonts must match persona |
| Payment | Privacy.com virtual card or prepaid debit card (if paid services needed) | Funded without linking to personal accounts |
| Device | Ideally a dedicated device; at minimum, a dedicated VM with clean snapshot | No cross-contamination with other personas or real identity |

**Aging phase.** New accounts are flagged by platform anti-abuse systems (social media platforms, forums, marketplaces). An aged account — one with months of consistent activity — avoids these filters and is trusted by community members. The aging protocol:

1. **Month 1-2.** Create the account. Complete profile with AI-generated photo (verify via reverse image search that the photo is not indexed), bio consistent with the target community, and a plausible posting history. Post 2-3 times per week with low-stakes content (sharing news articles, commenting on trending topics, asking genuine questions). Follow/friend 20-50 accounts in the target community. Respond to comments to build engagement metrics.

2. **Month 3-4.** Increase activity frequency. Join groups, forums, or channels relevant to the target community. Share original content (opinions, analysis) that establishes the persona as a knowledgeable community member. Begin building direct-message relationships with key members.

3. **Month 5-6.** The persona is now established and can be deployed operationally. Connection requests to targets are more likely to be accepted because the account has a visible history, mutual connections, and community credibility.

**Operational security during active use.** Every interaction with the sock puppet must occur through the persona's dedicated infrastructure stack. The cardinal rules:

```text
# Sock puppet OPSEC checklist — verify before every session

1. VPN/Tor active and exit node matches persona's geography
2. Correct browser profile loaded (check: about:config → general.useragent.override)
3. System clock set to persona's timezone
4. No tabs/windows open with real identity accounts
5. No clipboard content from real identity work
6. Screen sharing / recording disabled
7. WebRTC leak test passed (verify via browserleaks.com/webrtc)
8. DNS leak test passed (verify via dnsleaktest.com)
9. Canvas fingerprint consistent (verify via browserleaks.com/canvas)
10. Activity log updated with session timestamp and actions taken
```

**Retirement.** When a sock puppet is compromised (someone in the target community expresses suspicion, the account receives a platform warning, or the collection objective is achieved and the persona is no longer needed), the retirement protocol prevents correlation:

1. Gradually reduce activity over 2-4 weeks (sudden disappearance after active engagement is conspicuous).
2. Delete or archive all direct messages.
3. Remove profile photo and identifying information.
4. If the platform allows, deactivate rather than delete (deletion is sometimes irreversible and prevents forensic review of the persona's history if needed).
5. Destroy the associated infrastructure: close the email account, destroy the virtual number, wipe the browser profile, delete the VPN/VPS instance.
6. Record the retirement in the operational log with the date, reason, and any intelligence indicators that the persona was burned.

### 9.2 OSINT collection infrastructure

Beyond individual sock puppet infrastructure, a mature OSINT practice requires purpose-built collection infrastructure that supports multiple concurrent operations with appropriate compartmentation.

**VPN and Tor configuration for anonymous research.** For general OSINT collection (querying public databases, browsing websites, accessing APIs), a commercial VPN is sufficient — the threat model is preventing the target from seeing the operator's organizational IP address, not defeating nation-state adversaries. Select VPN providers that have been independently audited for no-logging compliance (Mullvad, IVPN, ProtonVPN). For high-sensitivity collection (dark web research, accessing adversary-controlled infrastructure, investigating nation-state actors), Tor provides stronger anonymity guarantees — but Tor exit traffic is visible to exit node operators, so never transmit credentials or sensitive data over Tor without end-to-end encryption (HTTPS).

The collection workstation should run Whonix (a two-VM architecture where all traffic is forced through Tor by the gateway VM, preventing application-level leaks), Tails (an amnesic live operating system that routes all traffic through Tor and leaves no persistent state), or at minimum a hardened Linux VM with iptables rules that drop all non-VPN/non-Tor traffic:

```bash
#!/usr/bin/env bash
# osint_workstation_firewall.sh — iptables killswitch for OSINT workstation.
# Ensures ALL traffic routes through the VPN tunnel. If VPN drops, traffic is blocked.
# Run as root on the OSINT VM.

set -euo pipefail

VPN_INTERFACE="wg0"                # WireGuard interface; change to tun0 for OpenVPN
VPN_SERVER_IP="198.51.100.1"       # VPN server's public IP
VPN_SERVER_PORT="51820"            # WireGuard port
LAN_SUBNET="10.0.0.0/8"           # Allow local network for DHCP/DNS

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F

# Default policy: DROP everything
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established/related connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow traffic to VPN server (to establish the tunnel)
iptables -A OUTPUT -d "${VPN_SERVER_IP}" -p udp --dport "${VPN_SERVER_PORT}" -j ACCEPT

# Allow all traffic through VPN interface
iptables -A OUTPUT -o "${VPN_INTERFACE}" -j ACCEPT
iptables -A INPUT -i "${VPN_INTERFACE}" -j ACCEPT

# Allow LAN (DHCP, local DNS)
iptables -A OUTPUT -d "${LAN_SUBNET}" -j ACCEPT
iptables -A INPUT -s "${LAN_SUBNET}" -j ACCEPT

# Block IPv6 entirely (prevent leaks)
ip6tables -P INPUT DROP
ip6tables -P FORWARD DROP
ip6tables -P OUTPUT DROP
ip6tables -A INPUT -i lo -j ACCEPT
ip6tables -A OUTPUT -o lo -j ACCEPT

echo "[*] VPN killswitch active. All non-VPN traffic is blocked."
echo "[*] VPN interface: ${VPN_INTERFACE}"
echo "[*] VPN server: ${VPN_SERVER_IP}:${VPN_SERVER_PORT}"
```

**Browser fingerprint management.** Modern websites and platforms fingerprint browsers using dozens of signals: User-Agent string, screen resolution, installed fonts, canvas rendering, WebGL renderer, AudioContext fingerprint, timezone, language, installed plugins, hardware concurrency (CPU cores), device memory, and platform. A sock puppet's browser fingerprint must be consistent across sessions (so the platform sees the same "device" each time) and distinct from the operator's real browser and from other sock puppets. Tools for fingerprint management:

- **Multilogin / GoLogin / AdsPower**: Commercial anti-detect browsers that generate unique, consistent browser fingerprints per profile. Each profile appears as a distinct device to fingerprinting scripts. Profiles persist across sessions and can be exported/imported for team use.
- **Firefox Multi-Account Containers with manual configuration**: Less robust but free. Each container isolates cookies and storage, but the browser fingerprint (canvas, WebGL, fonts) is shared across containers. Supplement with the `CanvasBlocker` extension for canvas/WebGL randomization.
- **Playwright/Puppeteer with custom fingerprints**: For automated collection, programmatically configure browser fingerprint parameters via launch flags and page evaluations.

### 9.3 Geolocation intelligence

Geolocation intelligence — determining the physical location associated with digital artifacts (photographs, IP addresses, network infrastructure) or physical observations (satellite imagery, street-level photography) — is a core OSINT tradecraft skill that supports both offensive reconnaissance and defensive investigation.

**Photo geolocation methodology (GeoGuessr-style analysis).** When EXIF GPS metadata is not available (stripped or never recorded), geolocation relies on visual analysis. The systematic approach:

1. **Language and script.** Signs, menus, labels, billboards — identify the script (Latin, Cyrillic, Arabic, CJK, Devanagari) and the specific language. This narrows the search to a country or region.
2. **Driving side and vehicle types.** Left-hand traffic (UK, Japan, Australia, India, Southeast Asia, parts of Africa) vs. right-hand traffic. Vehicle makes, models, and license plate formats identify countries.
3. **Infrastructure clues.** Road markings, traffic signs (shapes, colors, pictograms follow regional conventions — Vienna Convention signs for Europe, MUTCD for North America), power line configurations, architectural styles, vegetation types.
4. **Sun position.** For photos with visible shadows, the sun's position indicates latitude (high sun = tropical, low sun = high latitude) and time of day (combined with shadow direction, indicates east/west orientation).
5. **Business names and phone numbers.** Country dialing codes (phone numbers starting with +7 for Russia/Kazakhstan, +44 for UK), business chains with limited geographic presence.
6. **Satellite imagery cross-reference.** Once the candidate region is narrowed, cross-reference visible landmarks (buildings, road layouts, water features, terrain) with Google Earth Pro or Sentinel Hub satellite imagery.

```bash
# EXIF extraction and GPS coordinate parsing
exiftool -gps:all -DateTimeOriginal -Make -Model photo.jpg

# If GPS coordinates are present, reverse geocode:
LAT=$(exiftool -n -GPSLatitude photo.jpg | awk '{print $NF}')
LON=$(exiftool -n -GPSLongitude photo.jpg | awk '{print $NF}')

# Reverse geocode via Nominatim (OpenStreetMap)
curl -sS "https://nominatim.openstreetmap.org/reverse?lat=${LAT}&lon=${LON}&format=jsonv2" \
    -H "User-Agent: OSINTResearch/1.0" | jq '{address: .address, display_name: .display_name}'

# Sentinel Hub satellite imagery access (requires free/commercial account)
# API: https://services.sentinel-hub.com/api/v1/
# Useful for verifying geolocation hypotheses with recent satellite imagery
# Compare building layouts, road networks, water features

# Google Earth Pro (desktop) provides historical imagery timeline
# for temporal analysis — comparing a photo's season/construction state
# with satellite imagery from different dates
```

**IP geolocation beyond MaxMind.** Commercial IP geolocation databases (MaxMind GeoIP2, IP2Location, ipinfo.io) provide city-level accuracy for most IP addresses, but accuracy varies significantly. For infrastructure pivoting, combine multiple geolocation sources and cross-reference with WHOIS registration data, BGP routing data (the AS that announces the IP prefix often provides geographic hints via the AS name and organization), and reverse DNS hostnames (many ISPs encode geographic information in PTR records: `host-198-51-100-1.newyork.res.rr.com`). For cloud-hosted infrastructure, IP geolocation indicates the cloud region (us-east-1, eu-west-1) rather than the operator's physical location.

### 9.4 Financial OSINT

Financial OSINT — intelligence derived from publicly available corporate filings, financial records, and business registries — supports both organizational reconnaissance (understanding a target's corporate structure, key personnel, financial health, and business relationships) and threat intelligence (identifying shell companies used for money laundering, tracing cryptocurrency transactions, and mapping corporate ownership structures).

**Corporate registry analysis.** Most jurisdictions maintain public business registries that disclose incorporation details, registered agents, directors, officers, and in some cases beneficial owners. Key registries:

| Jurisdiction | Registry | URL | Data available |
|-------------|----------|-----|---------------|
| United States | SEC EDGAR | sec.gov/edgar | Public company filings (10-K, 10-Q, 8-K, proxy statements, insider trading) |
| United States | State SOS | varies by state | Business entity registration, registered agent, officers/directors |
| United Kingdom | Companies House | companieshouse.gov.uk | Full company details, directors, PSC (persons with significant control), annual accounts |
| European Union | EU Business Registers | e-justice.europa.eu/content_find_a_company-489-en.do | Cross-border company search |
| Global (aggregator) | OpenCorporates | opencorporates.com | 200M+ company records aggregated from worldwide registries |

**SEC EDGAR filing mining.** For US-listed companies and their subsidiaries, SEC filings contain a wealth of intelligence:

```bash
# SEC EDGAR full-text search for a company
# EDGAR EFTS (Full-Text Search System) indexes all filings
curl -sS "https://efts.sec.gov/LATEST/search-index?q=%22Example+Corp%22&dateRange=custom&startdt=2024-01-01&enddt=2025-01-01&forms=10-K,10-Q,8-K" \
    -H "User-Agent: CompanyResearch analyst@example.com" | jq '.hits.hits[:5]'

# Download a specific company's recent filings via CIK (Central Index Key)
# First, find the CIK:
curl -sS "https://www.sec.gov/cgi-bin/browse-edgar?company=example+corp&CIK=&type=10-K&dateb=&owner=include&count=10&search_text=&action=getcompany" \
    -H "User-Agent: CompanyResearch analyst@example.com"

# XBRL financial data (machine-readable) for a specific CIK
CIK="0001234567"
curl -sS "https://data.sec.gov/api/xbrl/companyfacts/CIK${CIK}.json" \
    -H "User-Agent: CompanyResearch analyst@example.com" | \
    jq '.facts."us-gaap" | keys[:20]'

# Extract key financial metrics from XBRL data
curl -sS "https://data.sec.gov/api/xbrl/companyfacts/CIK${CIK}.json" \
    -H "User-Agent: CompanyResearch analyst@example.com" | \
    jq '{
        revenue: .facts."us-gaap".Revenues.units.USD[-1],
        net_income: .facts."us-gaap".NetIncomeLoss.units.USD[-1],
        total_assets: .facts."us-gaap".Assets.units.USD[-1],
        employees: .facts."dei".EntityNumberOfEmployees.units.pure[-1]
    }'
```

**Beneficial ownership research.** The Corporate Transparency Act (CTA, effective January 2024 in the United States, though enforcement status fluctuates due to legal challenges) requires most US entities to report beneficial ownership information to FinCEN (Financial Crimes Enforcement Network). Until the FinCEN database is broadly accessible, beneficial ownership research relies on aggregating data from corporate registries (directors and officers), SEC filings (insider ownership disclosures in proxy statements and Form 4 filings), UK Companies House PSC registers (persons with significant control — those holding >25% shares or voting rights), and commercial services (Dun & Bradstreet, Bureau van Dijk/Moody's Orbis) that aggregate ownership data across jurisdictions.

For OSINT practitioners, the OpenCorporates API provides the most accessible cross-jurisdictional corporate data:

```bash
# OpenCorporates API — search for a company across all jurisdictions
curl -sS "https://api.opencorporates.com/v0.4/companies/search?q=Example+Corp&api_token=${OPENCORPORATES_TOKEN}" | \
    jq '.results.companies[:5] | .[] | {name: .company.name, jurisdiction: .company.jurisdiction_code, status: .company.current_status, incorporation_date: .company.incorporation_date, registered_address: .company.registered_address_in_full}'

# Get officers/directors for a specific company
curl -sS "https://api.opencorporates.com/v0.4/companies/us_de/1234567/officers?api_token=${OPENCORPORATES_TOKEN}" | \
    jq '.results.officers[] | {name: .officer.name, position: .officer.position, start_date: .officer.start_date}'
```

Financial OSINT feeds into attack surface assessment (identifying subsidiaries and acquisitions that may have weaker security postures), social engineering pretext development (impersonating auditors, regulators, or business partners identified through corporate filings), and threat actor attribution (tracing infrastructure ownership through shell companies and nominee directors).

---

## 10. SE Defense Program Management

Sections 5 and 7 established the technical architecture and maturity model for social engineering defense. This section addresses the program management layer — the metrics, processes, governance structures, and organizational capabilities needed to sustain and continuously improve a social engineering defense program. Chapter 23A §7 provided the foundational KPIs and maturity model; this section builds on that foundation with program-level operational detail.

### 10.1 Phishing resilience trending and statistical analysis

Raw phishing simulation metrics (click rate, report rate, credential submission rate) are useful for point-in-time assessment but insufficient for program management. The program manager needs trending analysis that distinguishes genuine improvement from statistical noise, identifies departments or roles that are plateauing or regressing, and provides the data needed to justify budget allocation for targeted interventions.

**Statistical significance testing.** When comparing phishing simulation results across campaigns (e.g., Q1 click rate of 12% vs. Q2 click rate of 9%), the program manager must determine whether the observed change represents genuine improvement or falls within the expected variance for the sample size. The recommended approach uses a two-proportion z-test:

```python
# phishing_stats.py — Statistical analysis of phishing simulation trends.
# Determines whether changes between campaigns are statistically significant.

import math
from dataclasses import dataclass


@dataclass
class CampaignResult:
    name: str
    emails_sent: int
    clicks: int
    reports: int
    credential_submissions: int
    mean_time_to_report_minutes: float

    @property
    def click_rate(self) -> float:
        return self.clicks / self.emails_sent if self.emails_sent else 0.0

    @property
    def report_rate(self) -> float:
        return self.reports / self.emails_sent if self.emails_sent else 0.0

    @property
    def submission_rate(self) -> float:
        return self.credential_submissions / self.emails_sent if self.emails_sent else 0.0


def two_proportion_z_test(p1: float, n1: int, p2: float, n2: int) -> tuple[float, bool]:
    """
    Two-proportion z-test. Returns z-score and whether the difference
    is significant at the 95% confidence level (|z| > 1.96).

    p1, n1: proportion and sample size for campaign 1 (baseline)
    p2, n2: proportion and sample size for campaign 2 (current)
    """
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 0.0, False
    z = (p1 - p2) / se
    return z, abs(z) > 1.96


def analyze_trend(baseline: CampaignResult, current: CampaignResult) -> dict:
    """Compare two campaigns and determine statistical significance of changes."""
    click_z, click_sig = two_proportion_z_test(
        baseline.click_rate, baseline.emails_sent,
        current.click_rate, current.emails_sent,
    )
    report_z, report_sig = two_proportion_z_test(
        baseline.report_rate, baseline.emails_sent,
        current.report_rate, current.emails_sent,
    )

    return {
        "baseline": baseline.name,
        "current": current.name,
        "click_rate_change": f"{baseline.click_rate:.1%} → {current.click_rate:.1%}",
        "click_rate_significant": click_sig,
        "click_rate_z_score": round(click_z, 2),
        "report_rate_change": f"{baseline.report_rate:.1%} → {current.report_rate:.1%}",
        "report_rate_significant": report_sig,
        "report_rate_z_score": round(report_z, 2),
        "mttr_change": (
            f"{baseline.mean_time_to_report_minutes:.0f}min → "
            f"{current.mean_time_to_report_minutes:.0f}min"
        ),
        "interpretation": _interpret(click_z, click_sig, report_z, report_sig),
    }


def _interpret(click_z: float, click_sig: bool, report_z: float, report_sig: bool) -> str:
    parts = []
    if click_sig and click_z > 0:
        parts.append("Click rate IMPROVED (statistically significant)")
    elif click_sig and click_z < 0:
        parts.append("Click rate REGRESSED (statistically significant)")
    else:
        parts.append("Click rate change NOT statistically significant")

    if report_sig and report_z < 0:
        parts.append("Report rate IMPROVED (statistically significant)")
    elif report_sig and report_z > 0:
        parts.append("Report rate REGRESSED (statistically significant)")
    else:
        parts.append("Report rate change NOT statistically significant")

    return "; ".join(parts)


# Example usage
if __name__ == "__main__":
    q1 = CampaignResult("Q1-2025", 5000, 600, 1500, 300, 45.0)
    q2 = CampaignResult("Q2-2025", 5200, 420, 2080, 180, 22.0)
    result = analyze_trend(q1, q2)
    for k, v in result.items():
        print(f"  {k}: {v}")
```

**Executive reporting framework.** Board and C-suite audiences require different data than the SOC. The executive report should include: (1) a single resilience score that aggregates click rate, report rate, and mean-time-to-report into an index (0-100) for month-over-month comparison; (2) benchmarking against industry peers (vendors like KnowBe4, Proofpoint Security Awareness, and Cofense provide industry benchmark data by sector and company size); (3) risk-quantified impact — translate simulation metrics into estimated financial exposure using a model such as FAIR (Factor Analysis of Information Risk), e.g., "at the current click rate and credential submission rate, the organization faces an estimated annualized loss exposure of $X for BEC attacks"; (4) a heatmap of departmental performance showing which business units are above and below target; (5) ROI on the awareness program expressed as cost-per-employee versus reduction in estimated risk.

### 10.2 Vishing and physical SE simulation programs

Email phishing simulations are the most common form of SE testing, but sophisticated threat actors use vishing (voice phishing) and physical social engineering as primary attack vectors — particularly against organizations with strong email security controls. A comprehensive SE defense program must simulate these vectors.

**Vishing simulation program design.** Vishing simulations are more operationally complex than email phishing because they require live operators (or increasingly, AI-generated voice interaction) and introduce legal and ethical considerations that email phishing does not.

Program structure:

1. **Scope definition.** Identify target groups (help desk, IT support, finance, executive assistants, front desk). Define approved pretexts (IT support callback, vendor payment verification, executive assistant impersonation, building maintenance request). Prohibit pretexts that could cause genuine distress.

2. **Caller infrastructure.** Use a dedicated SIP trunk with configurable caller ID (legally — caller ID spoofing for authorized internal testing is permissible under US law per 47 U.S.C. § 227(e) when not for fraud or harm; consult counsel for jurisdiction-specific guidance). Record all calls (with appropriate consent/notification per jurisdiction — one-party vs. two-party consent states).

3. **Scoring rubric.** Score each call on a standardized scale:
   - **Verification performed**: Did the target verify the caller's identity? (callback to known number, challenge question, manager confirmation)
   - **Information disclosed**: Did the target disclose sensitive information? (password, account details, internal system names, personnel information)
   - **Process followed**: Did the target follow the documented procedure for the request type?
   - **Escalation triggered**: Did the target report the call as suspicious to the security team?

4. **Metrics.** Track vishing-specific KPIs: verification rate (percentage of targets who performed verification), information disclosure rate, process compliance rate, and escalation rate. Trending analysis follows the same statistical methodology as §10.1.

**Physical SE simulation program.** Physical social engineering simulations test the organization's physical access controls, employee vigilance, and security culture. Simulations include tailgating attempts, badge cloning, impersonation (delivery drivers, technicians, auditors), and USB drop tests. These are typically conducted by the internal red team or a contracted physical penetration testing firm and require explicit written authorization (as described in Chapter 23A §7.4).

Physical simulation metrics: tailgating success rate (percentage of attempts where the tester gained unauthorized building access), challenge rate (percentage of encounters where an employee challenged the tester's identity or right to be in the area), time-to-detection (how long the tester operated inside the facility before being challenged or reported), and badge-check compliance rate (percentage of employees who checked the tester's badge when entering secured areas).

### 10.3 Security culture measurement frameworks

Phishing simulation metrics measure behavior during simulated attacks but do not capture the broader security culture — employees' attitudes, beliefs, norms, and intentions regarding security behavior. A security culture measurement program uses surveys, behavioral indicators, and organizational metrics to assess and track cultural factors that predict security behavior.

**Survey instruments.** The Security Culture Framework (CLTRe/KnowBe4) measures seven dimensions: Attitudes (employees' feelings about security), Behaviors (employees' security actions in daily work), Cognition (employees' understanding of security threats and policies), Communication (quality of security communication within the organization), Compliance (employees' knowledge and adherence to policies), Norms (perceived social norms around security behavior), and Responsibilities (clarity of security role expectations). The survey is administered annually or semi-annually, with a target response rate of at least 60% for statistical validity. Results are segmented by department, role level, tenure, and geography.

**Behavioral indicators beyond simulations.** Supplement simulation data with operational metrics that reflect organic security behavior:

| Indicator | What it measures | Collection source |
|-----------|-----------------|-------------------|
| Suspicious email report volume (organic, non-simulation) | Employee willingness to report real threats | Email security gateway / phishing report button telemetry |
| Badge challenge reports | Physical security vigilance | Physical security incident reports |
| Password policy compliance | Credential hygiene | Identity provider audit logs |
| Security training completion rate | Engagement with security program | LMS data |
| Voluntary security champion participation | Grassroots security advocacy | Security ambassador program enrollment |
| Shadow IT discovery rate | Willingness to follow procurement process | CASB / SaaS discovery tools |
| Mean time to patch personal devices (BYOD) | Individual device hygiene | MDM telemetry |

### 10.4 Executive protection programs

Senior executives are disproportionately targeted by social engineering because of their authority (a request from the CEO carries inherent urgency and compliance pressure), their access (executives typically have broad system and data access), their public profile (board memberships, conference appearances, media interviews, and social media activity provide extensive pretext material), and the financial impact (BEC targeting the CFO or controller can result in multi-million-dollar losses).

**Digital executive protection.** A layered approach to reducing executives' digital attack surface and hardening their accounts:

1. **PII suppression.** Engage a data broker removal service (DeleteMe, Optery, Privacy Duck) to submit opt-out requests across major data brokers on behalf of each executive. Monitor removal completion and re-appearance (data brokers frequently re-acquire data). The data broker monitoring pipeline from §8.1 should include all executives as priority-monitored personnel.

2. **Account hardening.** Enforce phishing-resistant MFA (FIDO2 hardware keys — YubiKey or similar) on all executive accounts. Disable SMS-based MFA to prevent SIM-swapping attacks (§23A 1.4). Enable Conditional Access policies that restrict executive account access to managed devices, compliant endpoints, and approved geographies. Configure impossible travel detection for executive identities.

3. **Communication verification.** Establish out-of-band verification protocols for executive-originated requests involving wire transfers, vendor changes, personnel actions, or sensitive data disclosure. The protocol must use a pre-established verification channel (a specific phone number, a dedicated Signal thread, a face-to-face confirmation) that cannot be spoofed by an attacker who has compromised the executive's email.

4. **Social media monitoring.** Monitor social media platforms for fake accounts impersonating executives (LinkedIn impersonation is particularly effective because connection requests from apparent executives have high acceptance rates). Automated monitoring scripts can track new account creation using the executive's name, photo, and company affiliation.

5. **Travel security.** For executives traveling to high-risk destinations, provide burner devices (clean laptop and phone with no organizational data, configured for the destination's network environment), travel-specific VPN configurations, and a check-in protocol with the security team.

**Physical executive protection** falls outside this chapter's scope but interfaces with the digital program: home address suppression from public records, residential security assessments, and secure transportation arrangements for public events.

### 10.5 Third-party and vendor SE risk assessment

The organization's social engineering defense is only as strong as its weakest partner. Vendors, contractors, and business partners with access to organizational systems, data, or processes are viable social engineering targets — an attacker may compromise a vendor's email account and use that trusted relationship to spear-phish the organization (vendor email compromise, a variant of BEC). Assessing and managing vendor SE risk requires extending the organization's SE defense program beyond its own employees.

**Vendor SE risk assessment framework.** Evaluate each vendor on the following dimensions:

| Dimension | Assessment criteria | Evidence required |
|-----------|-------------------|-------------------|
| Email security | DMARC policy (p=reject required), SPF strict mode, DKIM signing | DMARC/SPF/DKIM record check via DNS |
| MFA deployment | Type of MFA deployed (phishing-resistant preferred), coverage (all users vs. subset) | Vendor attestation or SOC 2 Type II report |
| Awareness program | Phishing simulation frequency, click rate metrics, training program description | Vendor-provided metrics or third-party assessment |
| Incident response | SE-specific IR procedures, notification timeline for compromised accounts | IR plan review, contractual notification SLAs |
| Access scope | What organizational systems/data the vendor can access, principle of least privilege | Access review documentation |

**Contractual controls.** Include SE defense requirements in vendor contracts and MSAs:

- Mandatory DMARC enforcement at `p=reject` for all domains used in communication with the organization.
- Mandatory phishing-resistant MFA for all vendor personnel with access to organizational systems.
- Notification obligation within 24 hours if any vendor account with organizational access is suspected compromised.
- Right to conduct SE testing (phishing, vishing) against vendor personnel who interact with the organization, with vendor consent documented in the contract.
- Annual attestation of SE awareness training completion for vendor personnel in scope.

**Vendor communication verification.** For high-risk vendor interactions (invoice submission, bank detail changes, contract modifications, data requests), implement verification protocols that mirror the executive protection protocols from §10.4: out-of-band verification via a pre-established channel, dual-authorization for financial transactions, and automated domain-age checks on sender domains (alert when an email from a vendor domain is less than 30 days old, which may indicate a newly-registered lookalike domain).

The vendor SE risk assessment integrates with the organization's third-party risk management (TPRM) program and should be reassessed annually or when the vendor's access scope changes. Critical vendors (those with broad system access, financial transaction authority, or access to sensitive data) receive quarterly reassessment and are included in the organization's SE simulation scope (with contractual authorization).
