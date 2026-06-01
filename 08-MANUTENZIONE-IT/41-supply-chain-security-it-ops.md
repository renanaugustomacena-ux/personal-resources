# Supply Chain Security in IT Operations — Software, Hardware, and Service Provider Risk

> **Modulo 41** · **Tempo:** 240 min · **Aggiornamento:** 2026-05-07

## Idee guida

1. **You don't need to breach the castle if you poison the well.** Attackers compromise one supplier to reach thousands of downstream targets — the economics overwhelmingly favor supply chain attacks over direct intrusion.
2. **Trust is transitive, but verification must not be.** Every artifact — source, binary, container image, firmware, service — requires independent cryptographic verification at every boundary crossing.
3. **SBOM is not optional; it is the foundation.** You cannot secure what you cannot enumerate. A complete Software Bill of Materials is the prerequisite for vulnerability management, license compliance, and incident response.
4. **Hardware and firmware are software you forgot to audit.** Below the OS lies an entire attack surface — BMC, UEFI, TPM, NIC firmware — that persists across reinstalls and often lacks monitoring entirely.
5. **Third-party risk is your risk.** A vendor's breach is your breach. Contractual controls, continuous monitoring, and verified attestations are the minimum — not annual questionnaires.

---

## Indice

1. [Panoramica Supply Chain Risk](#1-panoramica-supply-chain-risk)
2. [Software Supply Chain](#2-software-supply-chain)
3. [SLSA Framework and Build Integrity](#3-slsa-framework-and-build-integrity)
4. [Container and Image Supply Chain](#4-container-and-image-supply-chain)
5. [Hardware Supply Chain](#5-hardware-supply-chain)
6. [Service Provider and Third-Party Risk](#6-service-provider-and-third-party-risk)
7. [Vulnerability Disclosure and Coordination](#7-vulnerability-disclosure-and-coordination)
8. [Detection and Monitoring](#8-detection-and-monitoring)
9. [Governance and Compliance](#9-governance-and-compliance)
10. [Sicurezza della Pipeline CI/CD](#10-sicurezza-della-pipeline-cicd)
11. [Software Composition Analysis Avanzata](#11-software-composition-analysis-avanzata)
12. [Framework di Valutazione del Rischio Vendor](#12-framework-di-valutazione-del-rischio-vendor)
13. [Laboratorio](#13-laboratorio)

---

## 1. Panoramica Supply Chain Risk

### Tassonomia degli Attacchi Supply Chain

Supply chain attacks target the trust relationships between an organization and its suppliers — software vendors, hardware manufacturers, service providers, open-source maintainers. Rather than attacking the target directly, adversaries compromise an upstream component that the target already trusts, inheriting its access and permissions.

The attack taxonomy breaks into four primary vectors:

| Vector | Mechanism | Example |
|--------|-----------|---------|
| **Software** | Malicious code injected into source, build, or distribution | SolarWinds SUNBURST, 3CX, xz-utils |
| **Hardware** | Implants, modified firmware, counterfeit components | UEFI rootkits, BMC backdoors |
| **Firmware** | Persistence below OS in device firmware | LoJax (APT28), CosmicStrand |
| **Service Provider** | Compromise of MSP/SaaS/cloud to pivot to customers | Kaseya VSA, CodeCov |

Each vector has distinct detection challenges. Software supply chain attacks are the most common because they scale: one compromised package reaches every downstream consumer automatically.

### Incidenti Reali — Casi di Studio

#### SolarWinds SUNBURST (2020)

APT29 (Cozy Bear, attributed to Russia's SVR) compromised the SolarWinds Orion build system and injected the SUNBURST backdoor into updates shipped between March and June 2020. The malware was digitally signed with SolarWinds' legitimate certificate, making it invisible to signature-based detection.

**Technical mechanism:** The attackers modified the `SolarWinds.Orion.Core.BusinessLayer.dll` during the build process. SUNBURST performed DNS beaconing to `avsvmcloud[.]com`, encoding victim hostnames in DNS CNAME queries. After a dormancy period of approximately two weeks, it activated C2 communication over HTTP mimicking legitimate Orion Improvement Program traffic.

**Impact:** ~18,000 organizations installed the backdoor. Active exploitation confirmed in ~100 organizations including US Treasury, Commerce, DHS, FireEye, and Microsoft. FireEye's detection of their own red team tools being exfiltrated led to the discovery.

**Lessons:** Build system compromise is catastrophic. Signed binaries are not proof of integrity — they prove the build system signed something. Build provenance and hermetic builds would have detected the injection.

#### Kaseya VSA (July 2021)

REvil ransomware group exploited CVE-2021-30116 (authentication bypass) in Kaseya VSA, an RMM (Remote Monitoring and Management) tool used by MSPs (Managed Service Providers). By compromising a single MSP tool, they pushed ransomware to approximately 1,500 downstream businesses.

**Attack chain:** Authentication bypass → upload malicious update → VSA agents execute payload on all managed endpoints → ransomware deployment. The attackers specifically targeted the MSP trust architecture — VSA agents run with SYSTEM/root privileges on managed endpoints.

**Lessons:** MSP compromise is a force multiplier. RMM tools are effectively supply chain infrastructure — they have kernel-level access to every managed endpoint.

#### 3CX Desktop App (March 2023)

Lazarus Group (DPRK) executed a cascading supply chain attack: they first compromised Trading Technologies' X_TRADER application, which a 3CX employee had installed. Through that initial compromise, they gained access to 3CX's build environment and injected malicious code into the 3CX Desktop App, a VoIP client with approximately 600,000 customers.

**Technical mechanism:** The Windows installer bundled a trojanized `ffmpeg.dll` that loaded an encrypted payload from `d3dcompiler_47.dll`. The payload performed C2 communication via GitHub, fetching encrypted icon files containing actual C2 URLs.

**Significance:** This was the first publicly documented case of one supply chain attack enabling another — a cascading supply chain compromise. The X_TRADER compromise was the initial vector into 3CX.

#### CodeCov Bash Uploader (January-April 2021)

Attackers modified CodeCov's Bash Uploader script — a CI/CD component used by thousands of projects to upload test coverage reports. The modified script exfiltrated environment variables (including CI/CD secrets, API tokens, and credentials) from every CI pipeline that executed it.

**Technical mechanism:** The attackers altered the script hosted at `codecov.io/bash` to add a single `curl` line that posted all environment variables to an attacker-controlled server. The modification was possible because the uploader script was fetched at runtime via `curl | bash` — a pattern that bypasses any integrity verification.

**Duration:** The compromise persisted for over two months before detection by a customer who noticed unexpected network connections during CI runs.

**Lessons:** `curl | bash` is an anti-pattern. Every CI/CD dependency must have pinned versions, integrity verification (checksums), and network egress controls.

#### Log4Shell — CVE-2021-44228 (December 2021)

Not a supply chain *attack* in the traditional sense but a supply chain *vulnerability*: a critical RCE in Apache Log4j 2, a ubiquitous Java logging library embedded as a transitive dependency in hundreds of thousands of applications. The vulnerability allowed arbitrary code execution via JNDI lookup injection in logged strings.

**Impact:** CVSS 10.0. Affected virtually every Java application using Log4j 2.x (versions 2.0-beta9 through 2.14.1). Organizations could not determine exposure without a complete SBOM — many did not know they used Log4j at all because it was a transitive dependency of other libraries.

**Lessons:** Transitive dependency visibility is critical. Without an SBOM, you cannot even begin incident response for supply chain vulnerabilities. The Log4Shell response cost the industry billions precisely because most organizations lacked dependency inventories.

#### MOVEit Transfer — CVE-2023-34362 (May 2023)

Cl0p ransomware gang exploited a SQL injection zero-day in Progress Software's MOVEit Transfer, a managed file transfer (MFT) application widely used for secure file exchange. The vulnerability allowed unauthenticated access to the database and remote code execution.

**Impact:** Over 2,600 organizations compromised, affecting approximately 90 million individuals. Victims included Shell, British Airways, the BBC, US government agencies, and major financial institutions. Cl0p used the access for data exfiltration and extortion, not encryption.

**Pattern:** This exemplifies service provider supply chain risk — organizations trusted MOVEit as secure infrastructure for sensitive file transfers, and a single vulnerability in that shared service exposed all of them simultaneously.

#### xz-utils Backdoor — CVE-2024-3094 (March 2024)

A sophisticated, long-term social engineering campaign to backdoor `xz-utils`, a compression library linked by `liblzma` and used (indirectly) by OpenSSH on systemd-based Linux distributions.

**Timeline:**
- 2021: "Jia Tan" (JiaT75) begins contributing to xz-utils
- 2022: Coordinated pressure campaign (sockpuppet accounts) pushes the lone maintainer to add Jia Tan as co-maintainer
- February 2024: Malicious test files (`bad-3-corrupt_lzma2.xz`, `good-large_compressed.lzma`) containing the backdoor payload added to releases 5.6.0 and 5.6.1
- 29 March 2024: Andres Freund (Microsoft engineer) discovers the backdoor while investigating a 500ms SSH login latency regression during PostgreSQL benchmarking

**Technical mechanism:** The backdoor was hidden in binary test fixture files, extracted during the build process by a modified `build-to-host.m4` script. The payload hooked `RSA_public_decrypt` via the IFUNC (indirect function) mechanism in `liblzma`. When `sshd` was linked against `liblzma` (via `libsystemd` → `liblzma` dependency chain), the backdoor intercepted SSH authentication, allowing the attacker to execute arbitrary commands before authentication.

**Detection:** Pure accident. Freund noticed a 500ms latency increase in SSH logins, traced it to CPU consumption in `liblzma`, and discovered the obfuscated payload. Automated tooling did not catch this — it was discovered through performance profiling.

**Significance:** This is the most sophisticated open-source supply chain attack discovered to date. It involved years of social engineering, multiple sockpuppet accounts, and a technically complex payload that would have given the attacker pre-authentication RCE on most Linux servers.

#### Polyfill.io — Compromissione del Dominio CDN (Giugno 2024)

Nel febbraio 2024, un'azienda cinese (Funnull) ha acquisito il dominio `polyfill.io` e l'account GitHub associato alla popolare libreria Polyfill.js, utilizzata per garantire la compatibilita' con browser obsoleti. Dopo l'acquisizione, l'azienda ha modificato lo script servito dal CDN `cdn.polyfill[.]io` per iniettare codice malevolo nei siti web che lo incorporavano.

**Meccanismo tecnico:** Lo script modificato reindirizzava selettivamente gli utenti verso siti di gioco d'azzardo e pagine truffa. Il codice malevolo si attivava solo in determinate condizioni — controllava lo user-agent del browser, l'ora del giorno e la geolocalizzazione dell'utente per evitare di colpire ricercatori di sicurezza e ambienti di analisi. La natura condizionale del payload rendeva la detection particolarmente difficile tramite scanner automatici.

**Impatto:** L'attacco ha colpito oltre 100.000 siti web che incorporavano la libreria dal CDN compromesso. Tra i siti colpiti figuravano portali governativi, istituzioni finanziarie e piattaforme di e-commerce.

**Attribuzione:** Indagini successive hanno rivelato collegamenti con la Corea del Nord. L'ecosistema di gioco d'azzardo collegato all'attacco faceva capo al gruppo Suncity, utilizzato come veicolo per il riciclaggio di volumi ingenti di criptovaluta verso lo stato nordcoreano.

**Risposta:** Namecheap ha rimosso il dominio polyfill.io. Cloudflare, Google e Fastly hanno creato mirror sicuri degli script per prevenire ulteriore sfruttamento. La lezione critica: le dipendenze servite da CDN esterni rappresentano un vettore di attacco supply chain tanto quanto le dipendenze installate via package manager. Lo script era fetched a runtime — nessuna verifica di integrita', nessun pinning della versione, nessun controllo del contenuto.

**Mitigazioni raccomandate:**
- Ospitare localmente (self-host) tutte le librerie JavaScript critiche invece di affidarsi a CDN di terze parti
- Implementare Subresource Integrity (SRI) con hash SHA-384/SHA-512 per ogni script caricato da CDN
- Monitorare continuamente la proprieta' dei domini dei CDN utilizzati
- Utilizzare Content Security Policy (CSP) per limitare le origini degli script consentiti
- Valutare se la dipendenza e' ancora necessaria — nel caso di Polyfill.js, la maggior parte dei browser moderni non ne ha bisogno

#### tj-actions/changed-files — Compromissione di GitHub Actions (Marzo 2025)

Il 14 marzo 2025, un attacco supply chain ha compromesso la GitHub Action `tj-actions/changed-files`, utilizzata in oltre 23.000 repository. Gli attaccanti hanno modificato il codice dell'Action e aggiornato multipli tag di versione puntandoli a un commit malevolo, causando l'esecuzione di uno script che esfiltrava segreti CI/CD tramite i log dei workflow.

**Catena d'attacco dettagliata:**
1. **6 dicembre 2024:** L'attaccante ha sfruttato un workflow vulnerabile con trigger `pull_request_target` per rubare il Personal Access Token (PAT) di un maintainer attraverso una pull request malevola inviata dall'account disposable `randolzflow`
2. **La compromissione potrebbe essersi originata da un attacco separato a `reviewdog/actions-setup@v1`** — formando un attacco supply chain a cascata (cascading supply chain attack)
3. **14 marzo 2025:** Il PAT compromesso del bot `tj-actions-bot` e' stato utilizzato per modificare il repository tj-actions/changed-files, iniettando codice che esponeva tutti i segreti del runner CI nei log del workflow
4. **I tag di versione esistenti (v35, v44, ecc.) sono stati ri-puntati al commit malevolo**, colpendo tutti i repository che utilizzavano tag mutabili invece di hash del commit

**Impatto:** Inizialmente si temeva l'esposizione di segreti per tutti i 23.000+ repository dipendenti. L'analisi successiva ha confermato che 218 repository hanno effettivamente esposto segreti sensibili — inclusi access key AWS, GitHub PAT, token npm e chiavi private RSA.

**Lezioni critiche:**
- I tag Git sono mutabili — possono essere spostati su commit arbitrari senza preavviso
- Il pinning tramite hash del commit SHA e' l'unica difesa affidabile contro il tag-jacking
- Il trigger `pull_request_target` in GitHub Actions concede permessi di scrittura al workflow dal fork — un vettore di attacco ben documentato ma ancora diffuso
- Le Action di terze parti nella pipeline CI/CD sono dipendenze supply chain a tutti gli effetti

**Mitigazioni implementate:**
- GitHub ha introdotto (agosto 2025) una policy che supporta il blocco e il SHA-pinning delle Actions a livello organizzativo
- CISA ha emesso un advisory ufficiale (18 marzo 2025) classificando l'incidente come compromissione supply chain
- La community OpenSSF ha pubblicato una guida per i maintainer sulla sicurezza delle pipeline CI/CD post-incidente

#### Ultralytics — Compromissione del Pacchetto PyPI tramite GitHub Actions (Dicembre 2024)

Il pacchetto YOLO di Ultralytics, il framework di computer vision piu' diffuso su PyPI con circa 80 milioni di download mensili, e' stato compromesso attraverso un attacco di script injection in GitHub Actions.

**Meccanismo tecnico:** Gli attaccanti hanno sfruttato una vulnerabilita' nel workflow GitHub Actions del progetto che utilizzava il trigger `pull_request_target` con permessi di lettura/scrittura. Attraverso la cache di GitHub Actions, gli attaccanti sono riusciti a rubare il token di upload PyPI e hanno pubblicato quattro versioni contenenti un cryptominer.

**Errore nella risposta all'incidente:** I maintainer del progetto non hanno localizzato correttamente la compromissione. La versione 8.3.42, rilasciata il 5 dicembre 2024 come presunta correzione, conteneva ancora lo stesso codice malevolo. Solo la versione 8.3.43, pubblicata lo stesso giorno, era effettivamente pulita.

**Lezioni:**
- I trigger `pull_request_target` in combinazione con GitHub Actions cache possono consentire la compromissione della pipeline di pubblicazione
- L'incident response deve includere la verifica indipendente che gli artefatti pubblicati siano effettivamente puliti
- I token di pubblicazione sui package registry devono avere scoping granulare (per-progetto, con scadenza temporale)
- PyPI ha introdotto successivamente il supporto per Trusted Publishers (OIDC), eliminando la necessita' di token statici

### Tendenze degli Attacchi Supply Chain 2024-2026

L'analisi degli incidenti recenti rivela tendenze emergenti che definiscono il panorama delle minacce:

| Tendenza | Descrizione | Esempi |
|----------|-------------|--------|
| **Attacchi a cascata** | Una compromissione supply chain ne abilita un'altra | X_TRADER→3CX, reviewdog→tj-actions |
| **Acquisizione di infrastruttura** | Acquisto di dominio/progetto legittimo per sfruttare la fiducia esistente | Polyfill.io (acquisto dominio CDN) |
| **Social engineering dei maintainer** | Pressione prolungata su maintainer solitari per ottenere accesso | xz-utils (campagna di 3 anni) |
| **Compromissione CI/CD** | Attacco alla pipeline di build/pubblicazione piuttosto che al codice sorgente | Ultralytics, CodeCov |
| **Tag mutabili come vettore** | Ri-puntamento di tag di versione su commit malevoli | tj-actions/changed-files |
| **Targeting di dipendenze transitive** | Compromissione di librerie profondamente innestate nell'albero delle dipendenze | event-stream (2018), ua-parser-js (2021) |

**Statistiche chiave 2024-2025:**
- Gli attacchi supply chain software rilevati nel 2024 sono raddoppiati rispetto al 2023 (SecurityScorecard)
- Il 50% di tutte le violazioni dell'ultimo anno e' avvenuto tramite vulnerabilita' di terze parti (SecurityScorecard Threat Intelligence Report 2024)
- Le organizzazioni con programmi di Third-Party Risk Management (TPRM) continui individuano e fermano le minacce il 43% piu' velocemente rispetto a quelle che si affidano a revisioni periodiche

### Supply Chain in MITRE ATT&CK

MITRE ATT&CK explicitly catalogs supply chain compromise under **Initial Access**:

| Technique ID | Name | Description |
|-------------|------|-------------|
| **T1195** | Supply Chain Compromise | Parent technique |
| T1195.001 | Compromise Software Dependencies and Development Tools | Malicious code in libraries, SDKs, dev tools |
| T1195.002 | Compromise Software Supply Chain | Trojanized application updates or installers |
| T1195.003 | Compromise Hardware Supply Chain | Hardware implants or modified firmware |

Additional relevant techniques that supply chain attacks frequently use post-compromise:

- **T1199** (Trusted Relationship) — leveraging vendor access
- **T1078** (Valid Accounts) — using stolen credentials from supply chain compromise
- **T1059** (Command and Scripting Interpreter) — payload execution
- **T1071** (Application Layer Protocol) — C2 communication blended with legitimate traffic

### Modello Economico degli Attacchi Supply Chain

Why do attackers target suppliers? The economics are compelling:

**Cost-benefit analysis for attackers:**

| Factor | Direct Attack | Supply Chain Attack |
|--------|---------------|---------------------|
| Targets reached per operation | 1 | 100-18,000+ |
| Amortized cost per victim | High | Very low |
| Detection difficulty | Moderate | Very high (trusted channel) |
| Dwell time | Weeks-months | Months-years |
| Credential requirement | Target-specific | Supplier-specific |

**The multiplier effect:** Compromising one supplier with 1,000 customers effectively multiplies the attacker's reach by 1,000× at no additional marginal cost. The SolarWinds operation compromised one build system and reached 18,000 organizations.

**Trust exploitation:** Supply chain artifacts (signed updates, trusted packages, vendor-managed agents) bypass perimeter defenses, endpoint detection, and user vigilance. They arrive through trusted channels and execute with trusted privileges.

**Asymmetric defense cost:** The attacker needs to find one weak link in any supplier. The defender must secure every supplier in their entire chain — and their suppliers' suppliers (transitive supply chain risk).

### NIST C-SCRM (Cyber Supply Chain Risk Management)

NIST's Cybersecurity Supply Chain Risk Management framework (codified in SP 800-161 Rev. 1) establishes a structured approach:

**Core principles:**
1. **Visibility** — know your suppliers and their suppliers (multi-tier)
2. **Assessment** — evaluate risk at each tier
3. **Mitigation** — contractual, technical, and procedural controls
4. **Monitoring** — continuous, not periodic
5. **Response** — incident response plans that include supply chain scenarios

**C-SCRM integration points:**
- Enterprise Risk Management (ERM)
- Acquisition/procurement processes
- System Development Life Cycle (SDLC)
- Information security management
- Incident response and contingency planning

---

## 2. Software Supply Chain

### Rischi nella Gestione delle Dipendenze

#### Transitive Dependencies

Modern applications have deep dependency trees. A typical Node.js project with 20 direct dependencies may pull in 800+ transitive dependencies. Each of these is a potential attack surface.

```
your-app
├── express@4.18.2 (direct - you chose this)
│   ├── accepts@1.3.8 (transitive - you never evaluated this)
│   │   ├── mime-types@2.1.35
│   │   │   └── mime-db@1.52.0
│   ├── body-parser@1.20.2
│   │   ├── bytes@3.1.2
│   │   ├── content-type@1.0.5
│   │   ├── depd@2.0.0
│   │   └── ... 15 more
│   └── ... 28 more packages
└── ... your other 19 direct deps with similar trees
```

**Risk:** You audit `express`. You probably do not audit `mime-db@1.52.0`. Neither does anyone else. Maintainers of transitive dependencies are frequently solo developers with no security review process.

#### Dependency Confusion

First documented by Alex Birsan (2021), dependency confusion exploits the resolution order of package managers when both public and private registries are configured. If an internal package `@company/auth-utils` exists on a private registry, an attacker can publish `auth-utils` (without the scope) on npm with a higher version number. Misconfigured package managers will pull the public (malicious) version.

**Mitigation:**
- Always use scoped packages (`@company/package-name`)
- Configure `.npmrc` / `pip.conf` / `settings.xml` to pin private registry for scoped names
- Claim your internal package names on public registries (defensive registration)
- Use lockfiles and verify integrity hashes

#### Typosquatting

Attackers publish packages with names similar to popular ones: `lodahs` instead of `lodash`, `python-dateutils` instead of `python-dateutil`. Users who mistype a package name install malware.

**Scale:** npm has seen hundreds of typosquatting packages. PyPI has experienced similar campaigns. The `ua-parser-js` (npm) maintainer account was compromised in 2021, and the legitimate package itself was trojaned — proving that even correctly-named packages are not safe.

### Sicurezza dei Package Manager

| Package Manager | Known Vulnerability Vectors | Key Mitigations |
|----------------|----------------------------|-----------------|
| **npm** | `postinstall` scripts execute arbitrary code on `npm install`; dependency confusion; typosquatting at scale | `--ignore-scripts`, lockfile integrity (`npm ci`), `npm audit`, `.npmrc` registry pinning |
| **PyPI** | `setup.py` executes arbitrary code on install; no mandatory signing; namespace squatting | `--no-build-isolation`, PEP 740 attestations, `pip-audit`, hash-checking mode |
| **Maven Central** | Coordinate hijacking; dependency scope confusion; pom.xml manipulation | Dependency verification, Gradle verification metadata, dependency locking |
| **NuGet** | Package substitution; `<contentFiles>` and build targets execute code at build time | Signed package enforcement, `nuget verify`, locked mode |
| **crates.io** | `build.rs` executes at compile time; name squatting | `cargo-vet`, `cargo-deny`, `cargo-audit` |

**Common mitigations across all ecosystems:**
1. Pin exact versions in lockfiles — never float on ranges in production
2. Verify checksums/hashes against published values
3. Review dependency changes in PRs (automated diff tools)
4. Limit install-time script execution
5. Use a private registry or proxy (Artifactory, Nexus, Verdaccio) with upstream caching and policy enforcement

### SBOM — Software Bill of Materials

An SBOM is a complete, machine-readable inventory of all components (direct and transitive) in a software artifact. It is the prerequisite for supply chain security — you cannot protect what you cannot enumerate.

**NTIA minimum elements for SBOM:**
- Supplier name
- Component name and version
- Unique identifier (PURL, CPE)
- Dependency relationships
- Author of SBOM data
- Timestamp

#### CycloneDX Format (OWASP)

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
  "version": 1,
  "metadata": {
    "timestamp": "2026-05-07T10:00:00Z",
    "tools": [
      {
        "vendor": "CycloneDX",
        "name": "cyclonedx-npm",
        "version": "1.16.0"
      }
    ],
    "component": {
      "type": "application",
      "name": "my-application",
      "version": "3.2.1"
    }
  },
  "components": [
    {
      "type": "library",
      "name": "express",
      "version": "4.18.2",
      "purl": "pkg:npm/express@4.18.2",
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ],
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "a1b2c3d4e5f6..."
        }
      ]
    }
  ],
  "dependencies": [
    {
      "ref": "pkg:npm/my-application@3.2.1",
      "dependsOn": [
        "pkg:npm/express@4.18.2"
      ]
    }
  ]
}
```

#### SPDX Format (Linux Foundation, ISO 5962:2021)

```
SPDXVersion: SPDX-2.3
DataLicense: CC0-1.0
SPDXID: SPDXRef-DOCUMENT
DocumentName: my-application-sbom
DocumentNamespace: https://example.com/sbom/my-application-3.2.1
Creator: Tool: syft-0.100.0
Created: 2026-05-07T10:00:00Z

PackageName: express
SPDXID: SPDXRef-Package-express
PackageVersion: 4.18.2
PackageDownloadLocation: https://registry.npmjs.org/express/-/express-4.18.2.tgz
FilesAnalyzed: false
PackageChecksum: SHA256: a1b2c3d4e5f6...
PackageLicenseConcluded: MIT
PackageLicenseDeclared: MIT
ExternalRef: PACKAGE-MANAGER purl pkg:npm/express@4.18.2

Relationship: SPDXRef-DOCUMENT DESCRIBES SPDXRef-Package-my-application
Relationship: SPDXRef-Package-my-application DEPENDS_ON SPDXRef-Package-express
```

**CycloneDX vs SPDX:** CycloneDX is purpose-built for security and focuses on vulnerability correlation (via PURL/CPE). SPDX has broader scope including license compliance and is an ISO standard. Both are acceptable; choose based on tooling ecosystem. CycloneDX has better integration with vulnerability databases; SPDX has stronger legal/compliance tooling.

### Vulnerability Scanning

#### Trivy (Aqua Security)

```bash
# Scan a container image
trivy image --severity HIGH,CRITICAL myregistry.io/app:v3.2.1

# Scan a filesystem (project directory)
trivy fs --scanners vuln,secret,misconfig ./

# Scan an SBOM
trivy sbom ./sbom.cdx.json

# Generate SBOM in CycloneDX format
trivy image --format cyclonedx --output sbom.cdx.json myregistry.io/app:v3.2.1

# Scan with exit code for CI/CD gating
trivy image --exit-code 1 --severity CRITICAL myregistry.io/app:v3.2.1
```

#### Grype (Anchore)

```bash
# Scan an image
grype myregistry.io/app:v3.2.1

# Scan a directory
grype dir:./

# Scan an SBOM (from Syft)
syft myregistry.io/app:v3.2.1 -o cyclonedx-json > sbom.cdx.json
grype sbom:./sbom.cdx.json

# Output in table format with only critical/high
grype myregistry.io/app:v3.2.1 --only-fixed --fail-on high
```

#### Snyk

```bash
# Test project dependencies
snyk test

# Monitor project (continuous)
snyk monitor

# Test a container image
snyk container test myregistry.io/app:v3.2.1

# Test IaC files
snyk iac test ./terraform/

# Generate SBOM
snyk sbom --format=cyclonedx1.4+json > sbom.cdx.json
```

#### npm audit

```bash
# Standard audit
npm audit

# Production dependencies only
npm audit --omit=dev

# JSON output for pipeline integration
npm audit --json

# Fix automatically (when possible)
npm audit fix

# Audit with severity threshold
npm audit --audit-level=high
```

### Conformita' delle Licenze e Rischio Legale

License compliance is a supply chain risk vector often overlooked by security teams but critical to legal and business risk:

| License Type | Risk Level | Implication |
|-------------|-----------|-------------|
| MIT, BSD, Apache 2.0 | Low | Permissive; minimal obligations |
| LGPL | Medium | Dynamic linking generally safe; static linking may trigger copyleft |
| GPL v2/v3 | High | Copyleft; derivative works must be GPL-licensed |
| AGPL v3 | Very High | Network use triggers copyleft; SaaS services must release source |
| SSPL, BSL | High | Non-OSI; may conflict with commercial use |
| No license | Critical | No license = all rights reserved; legally unusable |

**Tooling for license scanning:**
- `license-checker` (npm) — scan node_modules
- `pip-licenses` (Python) — scan installed packages
- `cargo-deny` (Rust) — deny specific licenses in CI
- FOSSA, Snyk — commercial license compliance platforms

---

## 3. SLSA Framework and Build Integrity

### Livelli SLSA

SLSA (Supply-chain Levels for Software Artifacts, pronounced "salsa") is a framework for ensuring the integrity of software artifacts throughout the supply chain. The original specification (v0.1) defined four levels; the v1.0 specification reorganized into Build tracks with three levels, but the four-level model remains widely referenced.

#### Original SLSA Levels (v0.1)

| Level | Requirements | Protects Against |
|-------|-------------|------------------|
| **SLSA 1** | Build process documented, provenance generated automatically | Mistakes, undocumented builds |
| **SLSA 2** | Build service used (not developer laptop), signed provenance | Tampering after build |
| **SLSA 3** | Hardened build platform, non-falsifiable provenance, verified source | Compromised build environment |
| **SLSA 4** | Hermetic, reproducible builds, two-person review, pinned dependencies | Sophisticated insider threats |

#### SLSA v1.0 Build Track

| Level | Key Requirements |
|-------|-----------------|
| **Build L1** | Provenance exists — the package has documented build provenance stating what was built and where |
| **Build L2** | Hosted build platform — builds run on a hosted service, provenance is signed by that service |
| **Build L3** | Hardened builds — the build platform provides strong isolation, non-falsifiable provenance, prevents cross-build contamination |

### Build Provenance

Build provenance is a signed attestation documenting how an artifact was produced: source repository, builder identity, build configuration, input materials, and output artifacts.

**SLSA Provenance v1 example (in-toto Statement format):**

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "myapp",
      "digest": {
        "sha256": "a1b2c3d4e5f6789..."
      }
    }
  ],
  "predicateType": "https://slsa.dev/provenance/v1",
  "predicate": {
    "buildDefinition": {
      "buildType": "https://github.com/slsa-framework/slsa-github-generator/go@v1",
      "externalParameters": {
        "source": {
          "uri": "git+https://github.com/org/repo@refs/heads/main",
          "digest": {
            "sha1": "abc123..."
          }
        }
      },
      "internalParameters": {},
      "resolvedDependencies": []
    },
    "runDetails": {
      "builder": {
        "id": "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@refs/tags/v1.9.0"
      },
      "metadata": {
        "invocationId": "https://github.com/org/repo/actions/runs/12345",
        "startedOn": "2026-05-07T10:00:00Z",
        "finishedOn": "2026-05-07T10:05:00Z"
      }
    }
  }
}
```

### Build Ermetici — Ambienti di Build Riproducibili

A hermetic build uses only explicitly declared inputs — no network access during build, no ambient environment leakage, fully deterministic. If two different people build the same source at the same commit, they produce bit-identical artifacts.

**Requirements for hermetic builds:**
1. All dependencies vendored or fetched and cached before build starts
2. No network access during compilation/linking
3. No reliance on system time, locale, or hostname
4. Deterministic compilers and build tools (pinned versions)
5. Isolated filesystem (container or sandbox)

**Bazel hermetic build configuration:**

```python
# WORKSPACE.bazel
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# Pin every external dependency with sha256
http_archive(
    name = "com_google_protobuf",
    sha256 = "abc123def456...",
    strip_prefix = "protobuf-25.1",
    urls = ["https://github.com/protocolbuffers/protobuf/releases/download/v25.1/protobuf-25.1.tar.gz"],
)
```

### Integrita' del Sorgente

**Signed commits with GPG/SSH:**

```bash
# Configure Git to sign commits with SSH key
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true

# Verify a signed commit
git log --show-signature -1

# Verify all commits in a range
git log --show-signature main..feature-branch
```

**Branch protection requirements for supply chain integrity:**
- Require signed commits
- Require pull request reviews (minimum two approvers)
- Require status checks to pass (CI/CD, linting, tests)
- Dismiss stale reviews on new pushes
- Restrict who can push to protected branches
- Require linear history (no merge commits)

### Ecosistema Sigstore

Sigstore provides keyless signing infrastructure for software artifacts. The triad:

#### cosign — Container/Artifact Signing

```bash
# Sign a container image (keyless, OIDC-based)
cosign sign myregistry.io/app:v3.2.1

# Sign with a key pair
cosign generate-key-pair
cosign sign --key cosign.key myregistry.io/app:v3.2.1

# Verify signature
cosign verify --certificate-identity user@example.com \
  --certificate-oidc-issuer https://accounts.google.com \
  myregistry.io/app:v3.2.1

# Attach and verify an SBOM
cosign attach sbom --sbom sbom.cdx.json myregistry.io/app:v3.2.1
cosign verify --certificate-identity user@example.com \
  --certificate-oidc-issuer https://accounts.google.com \
  myregistry.io/app:sha256-<digest>.sbom

# Sign a blob (arbitrary file)
cosign sign-blob --output-signature app.sig --output-certificate app.cert app.tar.gz
cosign verify-blob --signature app.sig --certificate app.cert \
  --certificate-identity user@example.com \
  --certificate-oidc-issuer https://accounts.google.com \
  app.tar.gz
```

#### Rekor — Transparency Log

Rekor is an append-only transparency log (inspired by Certificate Transparency) that records signing events. Every cosign signature is automatically recorded in Rekor, providing tamper-evident evidence of when an artifact was signed.

```bash
# Search Rekor for entries related to an artifact
rekor-cli search --sha "sha256:a1b2c3d4..."

# Get a specific log entry
rekor-cli get --uuid 24296fb24b8ad77aa1b2c3d4e5f6...

# Verify inclusion proof
rekor-cli verify --artifact app.tar.gz --signature app.sig --pki-format x509 --public-key app.cert
```

#### Fulcio — Certificate Authority

Fulcio is a free CA that issues short-lived (10-minute) code signing certificates tied to OIDC identities. No long-lived signing keys to manage or rotate — the identity is bound to the signer's email/CI identity at signing time.

**Flow:** Developer authenticates via OIDC (GitHub, Google, Microsoft) → Fulcio issues a short-lived certificate binding the OIDC identity to an ephemeral key → cosign uses the certificate to sign → the signing event is recorded in Rekor → the certificate expires, but the Rekor entry proves the signature was valid at signing time.

#### Gitsign

```bash
# Install and configure Gitsign
git config --global gpg.x509.program gitsign
git config --global gpg.format x509
git config --global commit.gpgsign true

# Commits are now signed via Fulcio
git commit -m "feat: add supply chain verification"

# Verify a Gitsign-signed commit
gitsign verify --certificate-identity=user@example.com \
  --certificate-oidc-issuer=https://accounts.google.com \
  HEAD
```

### Framework di Attestazione in-toto

in-toto is a framework for securing the software supply chain by defining, verifying, and enforcing the integrity of each step in the pipeline. It defines:

- **Layouts** — the supply chain owner defines which steps must happen, in what order, and by whom
- **Links** — each step produces a signed attestation of its inputs and outputs
- **Verification** — at deployment, the complete chain of links is verified against the layout

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "myapp-linux-amd64",
      "digest": { "sha256": "abc123..." }
    }
  ],
  "predicateType": "https://in-toto.io/attestation/scai/attribute-report/v0.2",
  "predicate": {
    "attributes": [
      {
        "attribute": "PASSED_VULNERABILITY_SCAN",
        "evidence": {
          "name": "trivy-scan-result.json",
          "digest": { "sha256": "def456..." }
        }
      }
    ]
  }
}
```

---

## 4. Container and Image Supply Chain

### Provenienza delle Immagini Base

Base image selection determines the security floor of every container built on top of it:

| Source | Trust Level | Update Cadence | Use Case |
|--------|------------|----------------|----------|
| **Docker Official Images** | High — Docker-reviewed Dockerfiles | Regular, varies by image | General purpose, well-documented |
| **Verified Publishers** | Medium-High — vendor-maintained | Vendor-determined | Vendor-specific tooling |
| **Chainguard Images** | Very High — minimal, SBOM-included, signed, daily rebuilds | Daily | Security-critical workloads |
| **Distroless (Google)** | High — no shell, no package manager | Periodic | Production runtime containers |
| **scratch** | N/A — empty filesystem | N/A | Statically compiled binaries |
| **Random Docker Hub images** | Low — unverified, potentially malicious | Unknown | Never in production |

**Best practice:** Start from Chainguard or distroless images for production. Use multi-stage builds so the final image contains only the runtime and the application binary — no build tools, no compilers, no package managers.

### Firma delle Immagini con cosign e Notary

```bash
# Sign with cosign (keyless)
cosign sign myregistry.io/app@sha256:abc123...

# Sign with cosign (key-based, for air-gapped environments)
cosign generate-key-pair
cosign sign --key cosign.key myregistry.io/app@sha256:abc123...

# Verify before deployment
cosign verify --certificate-identity ci-build@org.iam.gserviceaccount.com \
  --certificate-oidc-issuer https://accounts.google.com \
  myregistry.io/app@sha256:abc123...
```

**Notary v2 (notation):** The CNCF standard for OCI artifact signing:

```bash
# Sign with notation
notation sign myregistry.io/app@sha256:abc123...

# Verify with a trust policy
notation verify myregistry.io/app@sha256:abc123...
```

### Admission Control — Solo Immagini Firmate in Kubernetes

**Kyverno policy to enforce signed images:**

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
spec:
  validationFailureAction: Enforce
  background: false
  rules:
    - name: verify-cosign-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "myregistry.io/*"
          attestors:
            - entries:
                - keyless:
                    subject: "ci-build@org.iam.gserviceaccount.com"
                    issuer: "https://accounts.google.com"
                    rekor:
                      url: https://rekor.sigstore.dev
```

**Sigstore Policy Controller (Kubernetes native):**

```yaml
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata:
  name: signed-images-only
spec:
  images:
    - glob: "myregistry.io/**"
  authorities:
    - keyless:
        identities:
          - issuer: "https://accounts.google.com"
            subject: "ci-build@org.iam.gserviceaccount.com"
        ctlog:
          url: https://rekor.sigstore.dev
```

### Build Multi-Stage per Ridurre la Superficie d'Attacco

```dockerfile
# Stage 1: Build
FROM golang:1.22-bookworm AS builder
WORKDIR /build
COPY go.mod go.sum ./
RUN go mod download && go mod verify
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-s -w" -trimpath -o /app ./cmd/server

# Stage 2: Runtime (distroless)
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app /app
USER nonroot:nonroot
ENTRYPOINT ["/app"]
```

**Key principles:**
- Build tools never reach the final image
- `CGO_ENABLED=0` eliminates libc dependency for Go
- `-trimpath` removes local filesystem paths from the binary
- `nonroot` user by default in distroless images
- No shell available = no shell-based exploitation

### Immagini Distroless e Scratch

**Distroless:** Contains only the runtime (e.g., glibc, ca-certificates, tzdata) and nothing else. No shell, no package manager, no coreutils. Attackers who achieve RCE cannot escalate easily because basic tools are absent.

**scratch:** An empty filesystem. Only works for statically compiled binaries. The absolute minimum attack surface.

```dockerfile
FROM scratch
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app /app
USER 65534:65534
ENTRYPOINT ["/app"]
```

### Sicurezza del Registry — Harbor con Vulnerability Scanning

Harbor (CNCF graduated project) provides:
- Automatic vulnerability scanning (integrated with Trivy)
- Image signing (cosign/Notary)
- Replication across registries
- RBAC access control
- Retention policies
- Immutable artifact tags (prevent overwriting `latest`)

**Harbor scanning policy configuration:**

```yaml
# harbor-project-config.yaml
project:
  name: production
  auto_scan: true
  severity_policy: high  # Block images with HIGH or CRITICAL vulnerabilities
  content_trust: true     # Require signed images
  prevent_vul: true
  reuse_sys_cve_allowlist: true
```

### Pipeline di Promozione Immagini

A promotion pipeline gates image progression through environments:

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│   DEV    │───▶│ STAGING  │───▶│   PROD   │
│ Registry │    │ Registry │    │ Registry │
└──────────┘    └──────────┘    └──────────┘
     │               │               │
  Build +          Gate:           Gate:
  Unit Test      - Vuln scan      - Signed by CI
  SBOM gen       - SBOM verify    - No CRITICAL vulns
  Sign           - Integration    - Approved by human
                   tests          - Promotion attestation
                 - Sign (staging)
```

Each promotion adds an attestation. The production admission controller verifies the full chain: build provenance, vulnerability scan results, staging test attestation, and human approval.

---

## 5. Hardware Supply Chain

### Rischi di Impianti Hardware

Hardware supply chain compromise operates below the visibility of nearly all software-based security controls.

**Bloomberg/Supermicro controversy (2018):** Bloomberg BusinessWeek alleged that Chinese intelligence had inserted tiny surveillance chips onto Supermicro server motherboards destined for Apple and Amazon. Both companies, Supermicro, and intelligence agencies publicly denied the claims. The allegations were never independently verified. However, the scenario itself is technically feasible and within known state-actor capabilities.

**NSA TAO (Tailored Access Operations) catalog:** Leaked in 2013 (Der Spiegel), the catalog documented hardware implants including:
- **COTTONMOUTH** — USB connector implant providing wireless bridge
- **DEITYBOUNCE** — Dell BIOS implant providing persistent backdoor
- **IRONCHEF** — HP Proliant server implant in BIOS
- **JETPLOW** — Cisco ASA/PIX firmware implant

These are known capabilities from 2008-2013 documentation. Current capabilities are presumed to be significantly more advanced.

**Practical implications:** Organizations in high-threat environments (government, defense, critical infrastructure, financial) must consider hardware interdiction as a real threat. Commercial organizations face lower but non-zero risk, primarily from counterfeit components.

### Attacchi al Firmware

Firmware attacks are particularly dangerous because they:
1. Persist across OS reinstalls and disk replacements
2. Execute before the OS and thus before any OS-level security
3. Often have full hardware access (DMA, memory, network)
4. Are rarely monitored by endpoint security tools

#### UEFI Rootkits

- **LoJax** (2018, APT28/Fancy Bear): First in-the-wild UEFI rootkit. Modified the SPI flash chip to persist a backdoor that survived OS reinstallation and hard drive replacement.
- **CosmicStrand** (2022, reported by Kaspersky): UEFI firmware rootkit found in the wild targeting ASUS and Gigabyte motherboards. Modified the firmware to inject a kernel-level implant during boot.
- **BlackLotus** (2023): First in-the-wild UEFI bootkit to bypass Secure Boot on fully patched Windows 11 systems by exploiting CVE-2022-21894.

#### BMC (Baseboard Management Controller) Compromise

BMCs provide out-of-band management access to servers. They:
- Operate independently of the host OS
- Have network access (often on a dedicated management network)
- Can read/write host memory, access the console, power cycle the server
- Run their own embedded OS (often based on Linux with known vulnerabilities)
- Frequently remain unpatched for years

**BMC attack vectors:** Default credentials, known CVEs (iLO, iDRAC, OpenBMC), firmware modification, network-based exploitation on the management VLAN.

#### Supply Chain Firmware Modification

Firmware can be modified at any point between the manufacturer and the customer: during manufacturing, warehousing, shipping, or reseller handling. Without cryptographic verification of firmware integrity, such modifications are undetectable.

### Verifica Hardware

#### TPM (Trusted Platform Module) Attestation

The TPM provides a hardware root of trust:

```
Boot Process with Measured Boot:
┌────────────┐
│  TPM 2.0   │  ← Hardware root of trust
│  PCR Banks │
└─────┬──────┘
      │ PCR[0] = hash(UEFI firmware)
      │ PCR[1] = hash(UEFI configuration)
      │ PCR[4] = hash(bootloader)
      │ PCR[5] = hash(bootloader config)
      │ PCR[7] = hash(Secure Boot policy)
      │ PCR[8-9] = hash(OS kernel + initrd)
      ▼
┌──────────────┐
│ Remote       │ ← Attestation server compares
│ Attestation  │   PCR values against known-good
│ Server       │   baseline
└──────────────┘
```

**TPM remote attestation flow:**
1. Server boots; TPM measures each boot stage into PCRs
2. Attestation agent requests a TPM quote (signed PCR values + nonce)
3. Quote is sent to the attestation server
4. Server compares PCR values against known-good baselines
5. Mismatch → alert, quarantine, or deny network access

#### Secure Boot

Secure Boot verifies that each piece of boot software is signed by a trusted authority before executing it:

```
UEFI Secure Boot Chain:
PK (Platform Key) → KEK (Key Exchange Key) → db (Authorized Signatures)
                                              → dbx (Forbidden Signatures)

Boot: UEFI firmware → Shim (signed by Microsoft) → GRUB2 (signed by distro) → Kernel (signed by distro)
```

**Limitations:**
- Secure Boot does not protect against firmware-level compromise (it runs *after* the firmware)
- The Microsoft third-party UEFI CA can be used to sign malicious bootloaders (BlackLotus exploited this)
- Secure Boot keys can be mismanaged (leaked, default PK not replaced)

#### Measured Boot

Measured boot extends Secure Boot by recording (measuring) each boot component into TPM PCRs without blocking boot. This provides an audit trail that can be verified remotely (attestation) even if Secure Boot is not enforcing.

### Sicurezza degli Approvvigionamenti

**Procurement security controls:**

| Control | Implementation |
|---------|---------------|
| Trusted supplier list | Maintain an approved vendor list with periodic review |
| Chain of custody | Tamper-evident packaging, sealed shipping containers, GPS tracking |
| Incoming inspection | Visual inspection, weight verification, serial number validation |
| Firmware verification | Hash firmware against vendor-published references on first boot |
| Component authenticity | X-ray inspection for counterfeit detection (critical systems) |
| Vendor audits | On-site manufacturing facility audits (for high-assurance) |

**Tamper-evident packaging indicators:**
- Serialized seals with vendor verification portal
- Holographic labels
- Color-changing adhesives (void if removed)
- GPS-tracked shipments with geofence alerts

### Tracciamento e Verifica Asset Hardware

Every hardware asset must be tracked from procurement through decommissioning:

1. **Receipt** — verify against purchase order, inspect packaging integrity
2. **Registration** — CMDB entry with serial numbers, firmware versions, TPM endorsement key
3. **Baseline** — record initial firmware hashes, BIOS settings, Secure Boot configuration
4. **Operational monitoring** — periodic firmware integrity checks, TPM attestation
5. **Decommissioning** — cryptographic disk erasure, physical destruction documentation, CMDB update

---

## 6. Service Provider and Third-Party Risk

### Valutazione della Sicurezza dei Vendor

#### Security Questionnaires

Standardized questionnaires provide baseline vendor assessment:

- **SIG (Standardized Information Gathering)** — Shared Assessments, comprehensive
- **CAIQ (Consensus Assessments Initiative Questionnaire)** — CSA, cloud-specific
- **VSAQ (Vendor Security Assessment Questionnaire)** — Google open-source
- **Custom questionnaires** — organization-specific, mapped to your risk framework

**Critical assessment areas:**

| Area | Key Questions |
|------|--------------|
| Data handling | Where is data stored? Encrypted at rest/transit? Retention? Deletion process? |
| Access control | MFA enforced? RBAC? Privileged access management? JIT access? |
| Incident response | Notification timeline? Breach history? IR plan tested? |
| Business continuity | RTO/RPO? DR testing frequency? Geographic redundancy? |
| Development practices | SDLC security? Vulnerability management? Pen testing? |
| Compliance | SOC 2 Type II? ISO 27001? PCI-DSS? Industry-specific certs? |
| Sub-processors | Who are their vendors? Same security requirements flowed down? |

#### SOC 2 Type II Reports

SOC 2 (Service Organization Control 2) reports are the industry standard for evaluating service provider security. Key differences:

- **Type I** — design of controls at a point in time (snapshot). Limited value.
- **Type II** — operating effectiveness of controls over a period (typically 12 months). This is what matters.

**What to look for in a SOC 2 Type II report:**
1. Trust Service Criteria covered (Security, Availability, Processing Integrity, Confidentiality, Privacy)
2. Exceptions or qualifications noted by the auditor
3. Complementary User Entity Controls (CUECs) — controls YOU must implement
4. Management assertions vs. auditor findings
5. Coverage period and reporting date freshness

#### ISO 27001 Verification

ISO 27001 certification verifies that an Information Security Management System (ISMS) is in place and audited. Verify:
- Certificate authenticity (check with the certification body)
- Scope of certification (does it cover the services you use?)
- Statement of Applicability (SoA) — which controls are included/excluded
- Surveillance audit status (annual audits required)

### Valutazione della Sicurezza SaaS

**SaaS security evaluation framework:**

| Dimension | Evaluation Criteria |
|-----------|-------------------|
| **Data handling** | Encryption at rest (AES-256 minimum), in transit (TLS 1.2+), key management (customer-managed keys available?), data residency controls, cross-tenant isolation |
| **Access controls** | SSO/SAML/OIDC integration, RBAC granularity, API key management, session management, MFA enforcement |
| **Incident response** | Contractual notification SLA (72h max per GDPR, shorter for critical), breach history disclosure, IR plan maturity |
| **Exit strategy** | Data export formats, data deletion verification, contract termination data handling, API availability for migration |
| **Availability** | SLA commitments, historical uptime, status page transparency, compensation for outages |

### Rischio MSP/MSSP

MSPs and MSSPs represent concentrated supply chain risk because they hold privileged access to multiple customer environments simultaneously. The Kaseya VSA attack demonstrated this: one MSP tool compromise → 1,500 downstream businesses hit with ransomware.

**Privileged Access Management for service providers:**

| Control | Implementation |
|---------|---------------|
| **Just-in-Time (JIT) access** | Access granted only when needed, automatically revoked after window |
| **Session recording** | All MSP sessions recorded and auditable |
| **MFA enforcement** | MSP accounts require hardware MFA tokens, not SMS |
| **Network segmentation** | MSP access limited to specific network segments |
| **Dedicated jump hosts** | MSP access only through monitored bastion hosts |
| **Separate credentials** | MSP personnel use unique, individual accounts — never shared |
| **Activity alerting** | Real-time alerts on MSP account activity outside business hours |

### Lacune nella Responsabilita' Condivisa del Cloud Provider

The shared responsibility model creates gaps where neither the cloud provider nor the customer takes ownership:

```
┌─────────────────────────────────────────────────────────┐
│                    CUSTOMER RESPONSIBILITY               │
│  Data, IAM, application code, OS patching (IaaS),       │
│  network config, encryption config, logging             │
├─────────────────────────────────────────────────────────┤
│                    GRAY ZONE                             │
│  Container runtime patching, managed service configs,   │
│  default security groups, API gateway policies,         │
│  shared tenancy risks, egress filtering                 │
├─────────────────────────────────────────────────────────┤
│                    PROVIDER RESPONSIBILITY               │
│  Physical security, hypervisor, network fabric,         │
│  managed service availability, global infrastructure    │
└─────────────────────────────────────────────────────────┘
```

**Common gaps:**
- **Managed Kubernetes** — provider manages control plane, but you own workload security, RBAC, network policies, admission controllers
- **Managed databases** — provider handles patching, but you own access controls, encryption configuration, query security
- **Serverless** — provider manages runtime, but you own function code security, IAM permissions, environment variables (secrets)
- **Object storage** — provider encrypts at rest, but public bucket misconfigurations are your problem

### Sicurezza delle Integrazioni API

```
API Integration Security Checklist:
┌──────────────────────────────────────────────┐
│ OAuth Scoping                                │
│ ☐ Request minimum required scopes            │
│ ☐ Use OAuth 2.0 with PKCE for auth code flow │
│ ☐ Token rotation and short expiry            │
│ ☐ Scope validation on resource server        │
├──────────────────────────────────────────────┤
│ Webhook Verification                         │
│ ☐ HMAC signature verification on all hooks   │
│ ☐ Timestamp validation (prevent replay)      │
│ ☐ IP allowlisting where supported            │
│ ☐ Idempotency handling for duplicate events  │
├──────────────────────────────────────────────┤
│ Rate Limiting                                │
│ ☐ Client-side retry with exponential backoff │
│ ☐ Server-side rate limits per API key        │
│ ☐ Circuit breaker for downstream failures    │
│ ☐ Monitoring for rate limit exhaustion       │
└──────────────────────────────────────────────┘
```

**Webhook HMAC verification example (Node.js):**

```javascript
const crypto = require('node:crypto');

function verifyWebhookSignature(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  hmac.update(payload, 'utf8');
  const expected = `sha256=${hmac.digest('hex')}`;

  // Timing-safe comparison to prevent timing attacks
  if (signature.length !== expected.length) return false;
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}
```

---

## 7. Vulnerability Disclosure and Coordination

### Programmi di Responsible Disclosure

A responsible disclosure program defines how external researchers report vulnerabilities to your organization. Essential components:

1. **Security.txt** (RFC 9116) — machine-readable disclosure information

```
# /.well-known/security.txt
Contact: mailto:security@example.com
Contact: https://example.com/security/report
Encryption: https://example.com/.well-known/pgp-key.asc
Preferred-Languages: en, it
Canonical: https://example.com/.well-known/security.txt
Policy: https://example.com/security/disclosure-policy
Hiring: https://example.com/careers/security
Expires: 2027-05-07T00:00:00.000Z
```

2. **Disclosure policy** specifying:
   - Scope (in-scope domains, applications, services)
   - Out-of-scope items (social engineering, DoS, physical)
   - Expected response timeline
   - Safe harbor statement (legal protection for researchers)
   - Coordinated disclosure timeline (typically 90 days)

### CVD — Coordinated Vulnerability Disclosure

The CVD process (ISO/IEC 29147:2018, ISO/IEC 30111:2019):

```
Reporter discovers vulnerability
        │
        ▼
Reporter contacts vendor (Day 0)
        │
        ▼
Vendor acknowledges (within 5 business days)
        │
        ▼
Vendor validates and triages
        │
        ▼
Vendor develops fix
        │
        ▼
Coordinated disclosure date agreed
        │
        ▼
Vendor releases patch + advisory
        │
        ▼
Reporter publishes details (post-patch)
        │
        ▼
CVE assigned and published in NVD
```

**Key timelines:**
- Initial acknowledgment: ≤ 5 business days
- Triage and validation: ≤ 10 business days
- Fix development: severity-dependent (Critical ≤ 30 days, High ≤ 60 days, Medium ≤ 90 days)
- Coordinated disclosure: typically 90 days after initial report (Google Project Zero standard)

### Programmi di Bug Bounty

| Platform | Model | Strengths |
|----------|-------|-----------|
| **HackerOne** | Public and private programs | Largest researcher community, triage services, compliance reporting |
| **Bugcrowd** | Public and private programs | Curated researchers, skills-based matching |
| **Synack** | Private, vetted researchers (Red Team) | Higher assurance, vetting process, managed testing |
| **Internal program** | Self-managed | Full control, no platform fees, requires dedicated security team |

**Bounty tiers (typical ranges):**

| Severity | Range (USD) |
|----------|------------|
| Critical (RCE, auth bypass, data breach) | $5,000 - $100,000+ |
| High (privilege escalation, significant data exposure) | $2,000 - $20,000 |
| Medium (stored XSS, IDOR with limited impact) | $500 - $5,000 |
| Low (information disclosure, reflected XSS) | $100 - $1,000 |

### VEX — Vulnerability Exploitability eXchange

VEX documents communicate whether a product is affected by a vulnerability in a component listed in its SBOM. Not every CVE in a dependency is actually exploitable in your application. VEX provides a machine-readable way to communicate this.

**VEX status values:**
- **Not affected** — the vulnerability is not exploitable in this context
- **Affected** — the vulnerability is exploitable and action is required
- **Fixed** — the vulnerability was present but has been remediated
- **Under investigation** — analysis is ongoing

**OpenVEX example:**

```json
{
  "@context": "https://openvex.dev/ns/v0.2.0",
  "@id": "https://example.com/vex/2026-05-07-001",
  "author": "security@example.com",
  "timestamp": "2026-05-07T10:00:00Z",
  "version": 1,
  "statements": [
    {
      "vulnerability": {
        "name": "CVE-2024-3094"
      },
      "products": [
        {
          "@id": "pkg:oci/myapp@sha256:abc123..."
        }
      ],
      "status": "not_affected",
      "justification": "vulnerable_code_not_in_execute_path",
      "impact_statement": "Application does not link against liblzma; xz-utils is not included in the container image."
    }
  ]
}
```

### Gestione Patch per Vulnerabilita' Supply Chain

Supply chain vulnerabilities require different patching approaches than direct vulnerabilities:

**Prioritization factors:**
1. Is the vulnerable component actually in your dependency tree? (SBOM lookup)
2. Is the vulnerable code path reachable from your application? (VEX/reachability analysis)
3. Is there an exploit available in the wild? (CISA KEV, EPSS)
4. What is the blast radius if exploited? (data exposure, lateral movement potential)

**Testing requirements before deployment:**
- Verify the patched dependency does not break API compatibility
- Run full integration test suite (not just unit tests)
- Check for behavioral changes in transitive dependencies
- Validate the fix actually resolves the vulnerability (re-scan with Trivy/Grype)

### Risposta Zero-Day per Compromissioni Supply Chain

When a supply chain zero-day is disclosed:

**Hour 0-4 (Triage):**
1. Determine if the affected component is in your environment (query SBOM/CMDB)
2. Identify all instances — production, staging, dev, CI/CD pipelines
3. Assess exploitability in your specific context
4. Activate incident response team if exploitable

**Hour 4-24 (Containment):**
1. Block or isolate affected components where possible
2. Apply virtual patching (WAF/IPS rules) if patch unavailable
3. Monitor for indicators of compromise specific to the vulnerability
4. Communicate status to stakeholders

**Day 1-7 (Remediation):**
1. Apply vendor patch when available (test first in staging)
2. If no patch available: implement compensating controls, remove dependency, or disable affected functionality
3. Perform retrospective analysis for evidence of prior exploitation
4. Update SBOM with remediated versions
5. Generate VEX statement documenting status

---

## 8. Detection and Monitoring

### Rilevamento di Compromissioni Supply Chain

Supply chain compromises are difficult to detect because malicious code arrives through trusted channels. Detection strategies must focus on behavioral anomalies rather than signatures.

**Behavioral analysis indicators:**

| Indicator | Detection Method |
|-----------|-----------------|
| Unexpected outbound network connections from build systems | Network flow monitoring, DNS analysis |
| Process execution anomalies (new processes spawned by known-good software) | EDR behavioral detection, auditd/sysdig |
| File integrity changes in vendor-supplied binaries | File integrity monitoring (AIDE, OSSEC, Wazuh) |
| Unusual DNS queries (DGA patterns, encoded data in queries) | DNS monitoring (SUNBURST used DNS for C2) |
| Modified dependency checksums between builds | Lockfile diff monitoring in CI |
| CI/CD pipeline execution anomalies (unexpected steps, modified configs) | Pipeline audit logging, config drift detection |

**File integrity monitoring configuration (AIDE):**

```ini
# /etc/aide/aide.conf
# Monitor vendor-supplied binaries
/usr/bin  p+i+n+u+g+s+b+m+c+sha256+sha512
/usr/sbin p+i+n+u+g+s+b+m+c+sha256+sha512
/usr/lib  p+i+n+u+g+s+b+m+c+sha256+sha512

# Monitor critical config files
/etc      p+i+n+u+g+s+b+m+c+sha256

# Exclude expected changes
!/var/log
!/var/cache
!/tmp
```

### Monitoraggio degli Aggiornamenti delle Dipendenze

**Automated PR review for dependency updates:**

Dependabot, Renovate, and similar tools create PRs for dependency updates. Each PR must be reviewed for:

1. **Changelog analysis** — what changed in the new version?
2. **Diff size** — unusually large diffs may indicate unexpected modifications
3. **Maintainer changes** — did the package ownership transfer recently?
4. **New dependencies** — does the update pull in new transitive dependencies?
5. **Build script changes** — any modifications to `postinstall`, `setup.py`, `build.rs`?

**Renovate configuration for security-conscious updates:**

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security"],
    "assignees": ["security-team"]
  },
  "packageRules": [
    {
      "matchUpdateTypes": ["major"],
      "automerge": false,
      "reviewers": ["team:security"],
      "labels": ["major-update", "needs-review"]
    },
    {
      "matchUpdateTypes": ["patch", "minor"],
      "matchCurrentVersion": "!/^0/",
      "automerge": true,
      "automergeType": "pr",
      "requiredStatusChecks": ["ci/test", "ci/security-scan"]
    }
  ],
  "prBodyNotes": [
    "**Security Review Required:** Check changelog for security-relevant changes, verify maintainer continuity, and review new transitive dependencies."
  ]
}
```

### Monitoraggio Runtime per Impianti Supply Chain

Once supply chain malware is deployed, runtime monitoring can detect its operational behavior:

**Unexpected network connections:**

```bash
# Monitor outbound connections from production containers
# using Falco (CNCF runtime security)

# /etc/falco/rules.d/supply-chain-detection.yaml
- rule: Unexpected Outbound Connection from Production App
  desc: Detect network connections to unexpected destinations from production workloads
  condition: >
    evt.type in (connect) and
    evt.dir = < and
    container.id != host and
    fd.sip.name != "" and
    not fd.sip.name in (allowed_destinations) and
    not fd.sport in (allowed_ports)
  output: >
    Unexpected outbound connection (container=%container.name
    image=%container.image.repository command=%proc.cmdline
    connection=%fd.name user=%user.name)
  priority: WARNING
  tags: [supply-chain, network]
```

**File modification monitoring:**

```yaml
# Falco rule for detecting unexpected file modifications
- rule: Write to Binary Directory in Container
  desc: Detect writes to /usr/bin or /usr/sbin inside containers (should be immutable)
  condition: >
    evt.type in (open, openat, openat2) and
    evt.is_open_write = true and
    container.id != host and
    (fd.name startswith /usr/bin/ or
     fd.name startswith /usr/sbin/ or
     fd.name startswith /usr/lib/)
  output: >
    File written to binary directory in container
    (user=%user.name container=%container.name
    file=%fd.name command=%proc.cmdline image=%container.image.repository)
  priority: CRITICAL
  tags: [supply-chain, file-integrity]
```

### Honeytokens nella Supply Chain

#### Canary Dependencies

Publish fake internal package names to public registries. If anyone installs them, you know a dependency confusion attack is being attempted or has succeeded.

```bash
# Publish a canary package to npm that phones home when installed
# package.json for @company/internal-auth-utils (published to npmjs.com)
{
  "name": "internal-auth-utils",
  "version": "99.0.0",
  "description": "Canary package - not for production use",
  "scripts": {
    "preinstall": "node canary.js"
  }
}
```

```javascript
// canary.js — fires an alert if this package is ever installed
const https = require('node:https');
const os = require('node:os');

const alert = JSON.stringify({
  event: 'canary_dependency_triggered',
  package: 'internal-auth-utils',
  hostname: os.hostname(),
  cwd: process.cwd(),
  timestamp: new Date().toISOString(),
  env_ci: process.env.CI || 'false',
  env_runner: process.env.GITHUB_ACTIONS || process.env.GITLAB_CI || 'unknown'
});

const req = https.request({
  hostname: 'alerts.internal.example.com',
  port: 443,
  path: '/api/canary',
  method: 'POST',
  headers: { 'Content-Type': 'application/json' }
}, () => {});

req.write(alert);
req.end();
```

#### Fake Internal Package Registry

Deploy a private registry (Verdaccio) with canary packages mimicking real internal names. Monitor for any access from external IPs or unexpected CI systems.

---

## 9. Governance and Compliance

### NIST SP 800-161 Rev. 1 — C-SCRM Guidance

NIST SP 800-161 Rev. 1 ("Cybersecurity Supply Chain Risk Management Practices for Systems and Organizations") provides the foundational federal guidance for C-SCRM. Key elements:

**Three-tiered integration:**
1. **Organization level** — enterprise-wide C-SCRM policy and governance
2. **Mission/business process level** — C-SCRM integrated into acquisition, SDLC, and vendor management
3. **Operational/system level** — technical controls on specific systems and supply chain components

**Key practices:**
- Establish a C-SCRM PMO (Program Management Office)
- Maintain a supplier risk register
- Flow down security requirements to suppliers contractually
- Conduct supplier risk assessments (risk-tiered)
- Implement provenance validation for critical components
- Plan for supply chain disruptions and compromises

### Executive Order 14028

Executive Order 14028 ("Improving the Nation's Cybersecurity," May 2021) mandated several supply chain security requirements:

| Requirement | Status |
|------------|--------|
| SBOM required for federal software | In effect — NTIA minimum elements defined |
| Critical software defined and secured | NIST definition published, OMB guidance issued |
| Zero trust architecture adoption | Ongoing — OMB M-22-09 implementation deadline passed |
| Software supply chain security standards | NIST SSDF (SP 800-218) published |
| Incident notification requirements | CISA incident reporting rules in effect |
| Enhanced logging requirements | OMB M-21-31 logging maturity model published |

**Impact on commercial organizations:** While EO 14028 directly applies to federal agencies and their suppliers, its requirements have become de facto industry standards. If you sell to the US government, SBOM generation, SSDF compliance, and supply chain attestation are contractual obligations.

### EU Cyber Resilience Act (CRA)

The EU Cyber Resilience Act (adopted 2024, enforcement phased from 2026-2027) imposes cybersecurity requirements on products with digital elements sold in the EU market:

**Key requirements:**
- **SBOM generation mandatory** for all products with digital elements
- **Vulnerability handling process** — manufacturers must have a CVD process
- **Security by design** — secure defaults, minimum data collection, encryption
- **Update obligation** — security updates for the product's expected lifetime (minimum 5 years)
- **Incident notification** — 24-hour notification to ENISA for actively exploited vulnerabilities
- **CE marking** — products must carry CE marking certifying cybersecurity compliance
- **Open-source exception** — non-commercial open-source software is exempt, but commercial open-source distributions are covered

**Penalties:** Up to 15 million EUR or 2.5% of global annual turnover.

#### Cronologia di Applicazione del CRA

La comprensione della cronologia e' essenziale per la pianificazione della conformita':

| Data | Milestone |
|------|-----------|
| **10 dicembre 2024** | Entrata in vigore del CRA (Regolamento UE 2024/2847) |
| **11 giugno 2026** | Le autorita' di notifica devono aver stabilito le procedure per la valutazione, la designazione e la notifica degli organismi di valutazione della conformita' |
| **11 settembre 2026** | Entrano in vigore gli obblighi di segnalazione — i produttori di prodotti connessi sono soggetti alla segnalazione obbligatoria di vulnerabilita' e incidenti tramite la piattaforma unica di segnalazione |
| **11 dicembre 2027** | Si applicano gli obblighi principali — conformita' piena richiesta, inclusi SBOM, gestione delle vulnerabilita', secure-by-design e marcatura CE |

**Dipendenza pratica SBOM:** Sebbene il requisito SBOM dell'Allegato I non sia tecnicamente applicabile fino a dicembre 2027, la scadenza di segnalazione di settembre 2026 crea una dipendenza pratica. Per segnalare efficacemente le vulnerabilita', i produttori devono gia' disporre di inventari dei componenti software — rendendo la generazione di SBOM una necessita' de facto molto prima della scadenza formale.

**Impatto sull'open source:** Il CRA distingue tra software open source non commerciale (esente) e distribuzioni open source commerciali (coperte). Questa distinzione ha implicazioni significative per le fondazioni open source e le aziende che distribuiscono software basato su componenti open source. Le fondazioni come la Linux Foundation e l'Apache Software Foundation hanno sollecitato chiarimenti sull'applicazione di questa distinzione.

### PCI-DSS 4.0 — Requisiti per Terze Parti

PCI-DSS 4.0 introduced stricter third-party and supply chain requirements:

- **Requirement 6.3** — Maintain an inventory of custom and third-party software components, including dependencies. This effectively requires an SBOM.
- **Requirement 6.3.2** — Maintain an inventory of bespoke and custom software, and third-party software components incorporated into bespoke and custom software, to facilitate vulnerability and patch management.
- **Requirement 12.8** — Manage service providers with which cardholder data is shared or that could affect the security of cardholder data.
- **Requirement 12.9** — Service providers must acknowledge their responsibility for cardholder data security in writing.

### ISO 27036 — Sicurezza dei Fornitori

ISO/IEC 27036 is a multi-part standard for information security in supplier relationships:

| Part | Scope |
|------|-------|
| 27036-1 | Overview and concepts |
| 27036-2 | Requirements — security controls for supplier relationships |
| 27036-3 | Guidelines for ICT supply chain security |
| 27036-4 | Guidelines for security of cloud services |

**Key controls from ISO 27036-2:**
- Supplier risk assessment before engagement
- Security requirements in contracts and SLAs
- Monitoring supplier compliance throughout the relationship
- Access control and information sharing policies for suppliers
- Incident notification and response coordination
- End-of-relationship data handling and access revocation

### Requisiti Contrattuali di Sicurezza per i Vendor

**Essential contractual clauses for vendor agreements:**

| Clause | Content |
|--------|---------|
| **Security standards** | Vendor must maintain ISO 27001 or equivalent |
| **Right to audit** | Customer may audit vendor's security controls (annually or upon cause) |
| **Incident notification** | Vendor must notify customer within 24-72 hours of security incidents |
| **Data handling** | Data classification, encryption requirements, retention, deletion |
| **Sub-processor controls** | Vendor must apply same security requirements to sub-processors |
| **SLA for patching** | Critical vulnerabilities patched within 24-48 hours |
| **SBOM provision** | Vendor must provide current SBOM for software components |
| **Penetration testing** | Annual third-party penetration tests, results shared |
| **Business continuity** | DR/BCP tested annually, RTO/RPO commitments |
| **Termination provisions** | Data return/deletion, transition period, access revocation timeline |

### Requisiti di Notifica degli Incidenti di Sicurezza del Vendor

Vendor incident notification must be contractually mandated with specific timelines:

| Severity | Notification Deadline | Information Required |
|----------|----------------------|---------------------|
| Critical (data breach, active compromise) | 24 hours | What happened, scope, data affected, containment status |
| High (significant vulnerability, potential exposure) | 48 hours | Nature of vulnerability, affected systems, remediation plan |
| Medium (security incident, no confirmed data exposure) | 72 hours | Incident description, investigation status |
| Low (minor security event) | Next scheduled report | Summary in regular security report |

---

## 10. Laboratorio

### Lab 1: Analisi del Backdoor xz-utils CVE-2024-3094

**Obiettivo:** Understand the technical mechanics of CVE-2024-3094, trace the attack timeline, and identify detection methods.

**Timeline reconstruction:**

```
2021       Jia Tan (JiaT75) begins contributing to xz-utils
2022-03    Sockpuppet accounts pressure maintainer Lasse Collin
2022-09    Jia Tan gains commit access
2023       Jia Tan becomes co-maintainer, gains release authority
2024-02-24 xz-utils 5.6.0 released with backdoor payload in test files
2024-03-09 xz-utils 5.6.1 released (payload refinement)
2024-03-28 Fedora 40, openSUSE Tumbleweed ship affected versions
2024-03-29 Andres Freund discovers backdoor via SSH latency anomaly
2024-03-29 Private disclosure to linux-distros mailing list
2024-03-29 CVE-2024-3094 assigned (CVSS 10.0)
2024-03-30 Public disclosure; Fedora, Debian, openSUSE issue advisories
```

**Technical analysis — tracing the payload:**

```bash
# Step 1: Examine the malicious test files added in 5.6.0/5.6.1
# The backdoor was hidden in:
#   tests/files/bad-3-corrupt_lzma2.xz
#   tests/files/good-large_compressed.lzma

# Step 2: The build-to-host.m4 script was modified to extract the payload
# During build, this script:
# 1. Checks if building from a release tarball (not git)
# 2. Extracts binary payload from test fixture files
# 3. Patches liblzma with the backdoor code

# Step 3: The payload mechanism
# liblzma IFUNC resolver for crc64 was modified:
# - Normal operation: resolves to standard CRC64 implementation
# - Backdoor operation: hooks RSA_public_decrypt via IFUNC
#
# The hook intercepts SSH authentication in sshd processes:
# sshd -> libsystemd -> liblzma (backdoored)
#
# Detection: sshd does NOT directly link liblzma.
# The chain is: sshd links libsystemd for sd_notify(),
# libsystemd links liblzma for compression.

# Step 4: Reproduce detection (on a safe test system)
# Check if your system was affected:
xz --version
# Affected: xz 5.6.0 or 5.6.1 (liblzma 5.6.0 or 5.6.1)

# Check for the IFUNC modification
strings /usr/lib/liblzma.so.5 | grep -c "RSA_public_decrypt"
# Non-zero result = backdoor present

# Check the build-to-host.m4 for injection code
grep -r "gl_cv_host_cpu" /usr/share/libtool/build-aux/ 2>/dev/null

# Verify package integrity against known-good hashes
sha256sum /usr/lib/liblzma.so.5
# Compare against distribution's published hashes for safe versions
```

**Detection methods that would have caught this:**
1. Binary diff analysis between builds (the test fixtures changed binary content)
2. Build reproducibility — the tarball builds differed from git builds
3. Static analysis of `build-to-host.m4` modifications
4. Runtime monitoring for unexpected IFUNC resolutions in liblzma
5. Network monitoring for unusual SSH authentication behavior
6. Performance monitoring (Freund's actual detection method)

### Lab 2: Generazione SBOM nella Pipeline CI/CD

**Obiettivo:** Integrate SBOM generation into a GitHub Actions CI/CD pipeline.

```yaml
# .github/workflows/sbom-pipeline.yml
name: SBOM Generation and Verification

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  id-token: write    # Required for cosign keyless signing
  packages: write
  security-events: write

jobs:
  build-and-sbom:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Generate SBOM (CycloneDX)
        run: |
          npx @cyclonedx/cyclonedx-npm --output-file sbom.cdx.json \
            --output-format JSON \
            --spec-version 1.5 \
            --omit dev

      - name: Generate SBOM (SPDX via Syft)
        uses: anchore/sbom-action@v0
        with:
          artifact-name: sbom-spdx.json
          output-file: sbom.spdx.json
          format: spdx-json

      - name: Scan SBOM for vulnerabilities (Grype)
        uses: anchore/scan-action@v4
        with:
          sbom: sbom.cdx.json
          fail-build: true
          severity-cutoff: high
          output-format: sarif

      - name: Upload SARIF to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif

      - name: Scan with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'sbom'
          scan-ref: 'sbom.cdx.json'
          severity: 'HIGH,CRITICAL'
          exit-code: '1'

      - name: Upload SBOMs as artifacts
        uses: actions/upload-artifact@v4
        with:
          name: sbom-artifacts
          path: |
            sbom.cdx.json
            sbom.spdx.json
          retention-days: 90

  container-sbom:
    needs: build-and-sbom
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build container image
        run: |
          docker build -t myregistry.io/app:${{ github.sha }} .

      - name: Generate container SBOM with Trivy
        run: |
          trivy image --format cyclonedx \
            --output container-sbom.cdx.json \
            myregistry.io/app:${{ github.sha }}

      - name: Scan container image
        run: |
          trivy image --exit-code 1 \
            --severity HIGH,CRITICAL \
            --ignore-unfixed \
            myregistry.io/app:${{ github.sha }}

      - name: Install cosign
        uses: sigstore/cosign-installer@v3

      - name: Sign container image (keyless)
        run: |
          cosign sign --yes \
            myregistry.io/app@$(docker inspect --format='{{index .RepoDigests 0}}' \
            myregistry.io/app:${{ github.sha }} | cut -d@ -f2)

      - name: Attach SBOM to image
        run: |
          DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' \
            myregistry.io/app:${{ github.sha }} | cut -d@ -f2)
          cosign attach sbom --sbom container-sbom.cdx.json \
            myregistry.io/app@${DIGEST}
```

### Lab 3: Configurazione della Firma Immagini con cosign

**Obiettivo:** Set up image signing with cosign in both keyless (OIDC) and key-based (air-gapped) modes.

```bash
# ===== Keyless signing (CI/CD environments with OIDC) =====

# Install cosign
go install github.com/sigstore/cosign/v2/cmd/cosign@latest
# or: brew install cosign
# or: apt install cosign (on supported distros)

# Sign an image (keyless — opens browser for OIDC auth in interactive mode,
# uses workload identity in CI)
cosign sign myregistry.io/app@sha256:abc123...

# Verify the signature
cosign verify \
  --certificate-identity "ci@example.com" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  myregistry.io/app@sha256:abc123...

# ===== Key-based signing (air-gapped environments) =====

# Generate a key pair (password-protected)
cosign generate-key-pair
# Creates cosign.key (private, encrypted) and cosign.pub (public)

# Sign with the private key
cosign sign --key cosign.key myregistry.io/app@sha256:abc123...

# Verify with the public key
cosign verify --key cosign.pub myregistry.io/app@sha256:abc123...

# ===== Attach attestations =====

# Attach vulnerability scan results as attestation
cosign attest --predicate trivy-results.json \
  --type vuln \
  myregistry.io/app@sha256:abc123...

# Verify attestation
cosign verify-attestation \
  --certificate-identity "ci@example.com" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  --type vuln \
  myregistry.io/app@sha256:abc123...

# ===== Enforce in Kubernetes (Kyverno) =====
# See Section 4 for full Kyverno and Policy Controller configurations
```

### Lab 4: Monitoraggio Dipendenze con Dependabot e Snyk

**Obiettivo:** Configure automated dependency monitoring with security alerting.

**Dependabot configuration:**

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "daily"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
      - "security"
    commit-message:
      prefix: "chore(deps):"
    ignore:
      # Ignore major version bumps for stability — review manually
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]
    groups:
      # Group minor/patch updates to reduce PR noise
      minor-and-patch:
        update-types:
          - "minor"
          - "patch"
    security-updates:
      open-pull-requests-limit: 20

  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
    reviewers:
      - "platform-team"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    reviewers:
      - "platform-team"
```

**Snyk CI integration:**

```yaml
# .github/workflows/snyk-scan.yml
name: Snyk Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 06:00 UTC

jobs:
  snyk-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Snyk to check for vulnerabilities
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: >
            --severity-threshold=high
            --fail-on=all
            --json-file-output=snyk-results.json

      - name: Run Snyk container scan
        uses: snyk/actions/docker@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          image: myregistry.io/app:${{ github.sha }}
          args: --severity-threshold=high

      - name: Run Snyk IaC scan
        uses: snyk/actions/iac@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=medium

      - name: Monitor project (continuous tracking)
        if: github.ref == 'refs/heads/main'
        run: snyk monitor
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

### Lab 5: Questionario di Valutazione del Rischio Vendor

**Obiettivo:** Create a structured vendor risk assessment questionnaire.

```markdown
# Vendor Security Risk Assessment Questionnaire
# Version: 2.0 | Date: 2026-05-07

## Section 1: Organization Security Governance

1.1  Do you maintain a current ISO 27001 certification?
     [ ] Yes — attach certificate   [ ] No — describe alternative framework

1.2  Do you have a dedicated CISO or equivalent security leadership role?
     [ ] Yes   [ ] No

1.3  Provide your most recent SOC 2 Type II report (or explain why unavailable).
     Attachment: ________________

1.4  Do you conduct annual third-party penetration tests?
     [ ] Yes — provide executive summary   [ ] No

1.5  Do you maintain a vulnerability disclosure program?
     [ ] Yes — provide URL   [ ] No

## Section 2: Data Protection

2.1  Where will our data be stored? (geographic locations)
     _____________________________________________

2.2  Encryption at rest: [ ] AES-256  [ ] Other: _______  [ ] None

2.3  Encryption in transit: [ ] TLS 1.3  [ ] TLS 1.2  [ ] Other: _______

2.4  Do you support customer-managed encryption keys (CMEK/BYOK)?
     [ ] Yes   [ ] No

2.5  Data retention period: _________ days
     Data deletion process upon contract termination: ___________________

2.6  Is our data logically or physically isolated from other tenants?
     [ ] Logical isolation   [ ] Physical isolation   [ ] Shared

## Section 3: Access Control

3.1  MFA enforced for all personnel accessing our data?
     [ ] Yes — method: __________   [ ] No

3.2  Do you implement role-based access control (RBAC)?
     [ ] Yes   [ ] No

3.3  Do you use privileged access management (PAM) with just-in-time access?
     [ ] Yes — tool: __________   [ ] No

3.4  Are admin sessions recorded and auditable?
     [ ] Yes   [ ] No

3.5  Background checks performed on employees with access to customer data?
     [ ] Yes   [ ] No

## Section 4: Incident Response

4.1  Security incident notification timeline: _________ hours

4.2  Have you experienced a data breach in the past 3 years?
     [ ] Yes — provide details   [ ] No

4.3  How frequently is your IR plan tested?
     [ ] Quarterly   [ ] Semi-annually   [ ] Annually   [ ] Never

4.4  Do you have cyber insurance?
     [ ] Yes — coverage: _________ EUR   [ ] No

## Section 5: Supply Chain (Your Vendors)

5.1  List sub-processors who may access our data:
     _____________________________________________

5.2  Do you apply the same security requirements to your sub-processors?
     [ ] Yes   [ ] No

5.3  Do you generate and maintain SBOMs for your software products?
     [ ] Yes — format: [ ] CycloneDX  [ ] SPDX   [ ] No

5.4  How quickly do you patch critical vulnerabilities in your products?
     [ ] <24h   [ ] <48h   [ ] <7d   [ ] >7d

## Section 6: Business Continuity

6.1  Recovery Time Objective (RTO): _________ hours
6.2  Recovery Point Objective (RPO): _________ hours
6.3  DR testing frequency: ________________________
6.4  Geographic redundancy: [ ] Yes — locations: __________   [ ] No

## Scoring

| Section | Weight | Score (1-5) | Weighted Score |
|---------|--------|-------------|----------------|
| Governance | 20% | | |
| Data Protection | 25% | | |
| Access Control | 20% | | |
| Incident Response | 15% | | |
| Supply Chain | 10% | | |
| Business Continuity | 10% | | |
| **Total** | **100%** | | |

Risk Rating: [ ] Low (4.0+)  [ ] Medium (3.0-3.9)  [ ] High (2.0-2.9)  [ ] Critical (<2.0)

Approved by: ________________  Date: ________________
Next review: ________________
```

### Lab 6: Honeypot Internal Package Registry

**Obiettivo:** Deploy a canary package registry to detect dependency confusion attacks against your organization.

```bash
# Step 1: Deploy Verdaccio as a canary registry
# docker-compose.yml
cat << 'COMPOSE_EOF'
services:
  verdaccio-canary:
    image: verdaccio/verdaccio:5
    container_name: canary-registry
    ports:
      - "4873:4873"
    volumes:
      - ./verdaccio-config:/verdaccio/conf
      - ./verdaccio-storage:/verdaccio/storage
    environment:
      - VERDACCIO_PORT=4873
    restart: unless-stopped

  alert-receiver:
    image: python:3.12-slim
    container_name: alert-receiver
    ports:
      - "8080:8080"
    volumes:
      - ./alert-server:/app
    command: python /app/server.py
    restart: unless-stopped
COMPOSE_EOF
```

```yaml
# verdaccio-config/config.yaml
storage: /verdaccio/storage
auth:
  htpasswd:
    file: /verdaccio/conf/htpasswd
    max_users: -1  # Disable registration
uplinks:
  npmjs:
    url: https://registry.npmjs.org/
packages:
  # Internal package names — should NEVER be requested from this registry
  # Any request triggers an alert
  '@company/auth-utils':
    access: $all
    publish: $all
  '@company/internal-api-client':
    access: $all
    publish: $all
  '@company/config-manager':
    access: $all
    publish: $all
  '**':
    access: $all
    proxy: npmjs
middlewares:
  audit:
    enabled: true
listen:
  - 0.0.0.0:4873
logs:
  type: stdout
  format: pretty
  level: info
```

```python
# alert-server/server.py
"""
Canary registry alert receiver.
Logs and alerts when canary packages are accessed.
"""

import json
import logging
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

CANARY_PACKAGES = {
    'internal-auth-utils',
    '@company/auth-utils',
    '@company/internal-api-client',
    '@company/config-manager',
}


class AlertHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {'raw': body.decode('utf-8', errors='replace')}

        alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_ip': self.client_address[0],
            'path': self.path,
            'data': data,
        }

        logger.critical(
            'CANARY TRIGGERED: %s',
            json.dumps(alert, indent=2)
        )

        # In production: send to SIEM, PagerDuty, Slack
        # requests.post(SLACK_WEBHOOK, json={...})
        # requests.post(PAGERDUTY_URL, json={...})

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Canary alert receiver running')


if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), AlertHandler)
    logger.info('Canary alert receiver listening on :8080')
    server.serve_forever()
```

```bash
# Step 2: Publish canary packages to public npm with alerting
# For each internal package name, publish a high-version canary to npmjs.com:

mkdir canary-auth-utils && cd canary-auth-utils

cat > package.json << 'PKG_EOF'
{
  "name": "internal-auth-utils",
  "version": "999.0.0",
  "description": "Security canary - do not install",
  "scripts": {
    "preinstall": "node canary.js || true"
  }
}
PKG_EOF

cat > canary.js << 'CANARY_EOF'
const https = require('node:https');
const os = require('node:os');

const payload = JSON.stringify({
  event: 'dependency_confusion_canary',
  package: 'internal-auth-utils',
  hostname: os.hostname(),
  username: os.userInfo().username,
  cwd: process.cwd(),
  timestamp: new Date().toISOString(),
  ci_env: {
    ci: process.env.CI,
    github_actions: process.env.GITHUB_ACTIONS,
    gitlab_ci: process.env.GITLAB_CI,
    jenkins: process.env.JENKINS_URL,
    runner: process.env.RUNNER_NAME
  }
});

const req = https.request({
  hostname: 'canary-alerts.example.com',
  port: 443,
  path: '/api/v1/alert',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(payload)
  },
  timeout: 3000
}, () => {});

req.on('error', () => {}); // Fail silently to avoid breaking legitimate builds
req.write(payload);
req.end();
CANARY_EOF

# Publish to npmjs.com (requires npm account)
npm publish
```

```bash
# Step 3: Monitor and alert

# Set up log monitoring for Verdaccio access logs
# Any request for canary package names is an indicator of compromise

# Example: monitor with grep + systemd journal
journalctl -u verdaccio-canary -f | grep -E "(auth-utils|internal-api|config-manager)"

# Example: Wazuh rule for canary detection
# /var/ossec/etc/rules/canary_rules.xml
cat << 'WAZUH_EOF'
<group name="canary,supply_chain">
  <rule id="100100" level="15">
    <decoded_as>json</decoded_as>
    <field name="event">dependency_confusion_canary</field>
    <description>CRITICAL: Dependency confusion canary triggered - $(package)</description>
    <group>canary,supply_chain,attack</group>
  </rule>
</group>
WAZUH_EOF
```

---

## Appendice: Riferimenti e Standard

| Resource | URL / Identifier |
|----------|-----------------|
| NIST SP 800-161 Rev. 1 | C-SCRM guidance for systems and organizations |
| NIST SP 800-218 | Secure Software Development Framework (SSDF) |
| SLSA Framework | https://slsa.dev |
| Sigstore | https://sigstore.dev |
| in-toto | https://in-toto.io |
| CycloneDX | https://cyclonedx.org |
| SPDX | https://spdx.dev |
| OpenVEX | https://openvex.dev |
| CISA KEV Catalog | https://www.cisa.gov/known-exploited-vulnerabilities-catalog |
| EO 14028 | Executive Order on Improving the Nation's Cybersecurity (2021-05-12) |
| EU Cyber Resilience Act | Regulation (EU) 2024/2847 |
| ISO/IEC 27036 | Information security for supplier relationships |
| MITRE ATT&CK T1195 | Supply Chain Compromise |
| RFC 9116 | security.txt |
| PCI-DSS 4.0 | Payment Card Industry Data Security Standard v4.0 |
