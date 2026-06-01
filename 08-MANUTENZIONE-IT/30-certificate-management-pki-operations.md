# Certificate Management, PKI Operations, and TLS Infrastructure

> **Modulo 30** · **Tempo:** 180 min · **Aggiornamento:** 2026-05-07

## Idee guida

1. **Certificates are the identity layer of the internet.** A misconfigured or expired cert is an outage — a compromised CA is a catastrophe.
2. **Automation eliminates human error.** Manual renewal is the single biggest cause of certificate-related outages.
3. **Defense in depth applies to PKI.** Offline root, constrained intermediates, short-lived certs, CT monitoring, OCSP stapling — every layer matters.
4. **Crypto agility is not optional.** Post-quantum migration is coming; your PKI architecture must accommodate algorithm transitions without rebuilding from scratch.

---

## Indice

1. [Fondamenti PKI](#1-fondamenti-pki)
2. [Implementazione CA Interna](#2-implementazione-ca-interna)
3. [TLS Configuration e Hardening](#3-tls-configuration-e-hardening)
4. [Certificate Automation](#4-certificate-automation)
5. [Attacchi ai Certificati — Red Team](#5-attacchi-ai-certificati--red-team)
6. [mTLS e Service Mesh](#6-mtls-e-service-mesh)
7. [Code Signing e Document Signing](#7-code-signing-e-document-signing)
8. [Gestione Operativa](#8-gestione-operativa)
9. [Compliance e Audit](#9-compliance-e-audit)
10. [Laboratorio Pratico](#10-laboratorio-pratico)

---

## 1. Fondamenti PKI

### 1.1 Asymmetric Cryptography Recap

Public Key Infrastructure rests on asymmetric (public-key) cryptography. The fundamental property: a key pair where one key encrypts and only the other decrypts, or one key signs and only the other verifies — and deriving one from the other is computationally infeasible.

**RSA (Rivest-Shamir-Adleman)**

- Based on the difficulty of factoring the product of two large primes.
- Key sizes: 2048-bit minimum (NIST deprecated 1024 in 2013), 3072-bit recommended for longevity past 2030, 4096-bit for root CAs.
- Operations: encryption (OAEP padding), signature (PSS padding preferred over PKCS#1 v1.5).
- Performance: slower than elliptic curve operations at equivalent security levels. A 3072-bit RSA key provides ~128-bit security; a 256-bit ECDSA key achieves the same.

```bash
# Generate RSA 4096-bit key
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out ca-key.pem

# Extract public key
openssl pkey -in ca-key.pem -pubout -out ca-pub.pem

# Inspect key parameters
openssl pkey -in ca-key.pem -text -noout
```

**ECDSA (Elliptic Curve Digital Signature Algorithm)**

- Based on the Elliptic Curve Discrete Logarithm Problem (ECDLP).
- Common curves: P-256 (secp256r1/prime256v1) — 128-bit security, P-384 (secp384r1) — 192-bit security.
- Advantages: smaller keys, faster signing, lower bandwidth.
- Disadvantage: nonce reuse is catastrophic (leaks private key). Deterministic ECDSA (RFC 6979) mitigates this.

```bash
# Generate ECDSA P-384 key
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:secp384r1 -out ec-key.pem

# Generate ECDSA P-256 key (most common for TLS)
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:prime256v1 -out ec256-key.pem
```

**EdDSA (Edwards-curve Digital Signature Algorithm)**

- Ed25519 (Curve25519): 128-bit security, 32-byte keys, deterministic signatures.
- Ed448 (Goldilocks): 224-bit security.
- Advantages: constant-time implementation (side-channel resistant), fast verification, no nonce vulnerability.
- TLS support: TLS 1.3 natively supports Ed25519/Ed448. Browser support is mature since ~2020.

```bash
# Generate Ed25519 key
openssl genpkey -algorithm ED25519 -out ed25519-key.pem

# Generate Ed448 key
openssl genpkey -algorithm ED448 -out ed448-key.pem
```

**Algorithm Comparison Matrix**

| Algorithm | Key Size | Security Level | Sign Speed | Verify Speed | TLS 1.3 |
|-----------|----------|---------------|------------|--------------|---------|
| RSA-2048 | 2048 bit | ~112 bit | Slow | Fast | Yes |
| RSA-3072 | 3072 bit | ~128 bit | Slower | Fast | Yes |
| RSA-4096 | 4096 bit | ~140 bit | Slowest | Fast | Yes |
| ECDSA P-256 | 256 bit | ~128 bit | Fast | Fast | Yes |
| ECDSA P-384 | 384 bit | ~192 bit | Fast | Fast | Yes |
| Ed25519 | 256 bit | ~128 bit | Very fast | Very fast | Yes |
| Ed448 | 448 bit | ~224 bit | Fast | Fast | Yes |

### 1.2 X.509v3 Certificate Structure

An X.509v3 certificate is an ASN.1 DER-encoded data structure (typically distributed as PEM — Base64 with header/footer). The structure defined in RFC 5280:

```
Certificate ::= SEQUENCE {
    tbsCertificate      TBSCertificate,        -- "to be signed" content
    signatureAlgorithm  AlgorithmIdentifier,   -- algorithm used by issuer
    signatureValue      BIT STRING             -- actual signature bytes
}

TBSCertificate ::= SEQUENCE {
    version         [0]  EXPLICIT INTEGER DEFAULT v1,  -- v3 = 2
    serialNumber         INTEGER,                       -- unique per CA
    signature            AlgorithmIdentifier,
    issuer               Name,                          -- CA's DN
    validity             Validity,                      -- notBefore/notAfter
    subject              Name,                          -- entity's DN
    subjectPublicKeyInfo SubjectPublicKeyInfo,
    extensions      [3]  EXPLICIT Extensions OPTIONAL   -- v3 only
}
```

**Critical Fields:**

- **Serial Number**: Must be unique per issuing CA. CA/Browser Forum requires at least 64 bits of entropy. Collision = revocation confusion.
- **Issuer**: Distinguished Name (DN) of the signing CA. Format: `C=IT, O=Acme Corp, CN=Acme Issuing CA G2`.
- **Subject**: DN of the entity. For TLS server certs, the CN is deprecated in favor of SAN.
- **Validity**: `notBefore` and `notAfter` in UTC. Max lifetime for public TLS certs: 398 days (since September 2020, CA/Browser Forum Ballot SC31). Apple announced 47-day maximum effective from 2028.
- **Subject Public Key Info**: The public key and algorithm OID.

**Key Extensions (v3):**

| Extension | Critical | Purpose |
|-----------|----------|---------|
| Basic Constraints | YES | `CA:TRUE` / `CA:FALSE`, pathLen |
| Key Usage | YES | digitalSignature, keyEncipherment, keyCertSign, cRLSign |
| Extended Key Usage | NO* | serverAuth, clientAuth, codeSigning, emailProtection |
| Subject Alternative Name | NO | DNS names, IPs, emails, URIs — the REAL identity |
| Authority Key Identifier | NO | Links to issuer's public key (SKI of issuer) |
| Subject Key Identifier | NO | Hash of this cert's public key |
| CRL Distribution Points | NO | URL(s) to fetch CRL |
| Authority Info Access | NO | OCSP responder URL, CA issuers URL |
| Certificate Policies | NO | OIDs indicating validation level (DV/OV/EV) |
| Name Constraints | YES | Restricts what names a sub-CA can issue for |
| CT Precertificate SCTs | NO | Signed Certificate Timestamps from CT logs |

```bash
# Inspect certificate structure in detail
openssl x509 -in cert.pem -text -noout

# Extract specific fields
openssl x509 -in cert.pem -subject -issuer -dates -serial -noout

# View extensions only
openssl x509 -in cert.pem -text -noout | grep -A2 "X509v3"

# Check SAN entries
openssl x509 -in cert.pem -noout -ext subjectAltName
```

### 1.3 Certificate Chain of Trust

Trust is transitive and hierarchical. A relying party (browser, OS, application) maintains a **trust store** containing root CA certificates. Any certificate signed by a trusted root — or by an intermediate CA whose chain terminates at a trusted root — is trusted.

**Chain Validation Algorithm (RFC 5280 Section 6):**

1. Build candidate chain from end-entity cert up to a trust anchor.
2. For each certificate in the chain:
   - Verify signature using issuer's public key.
   - Check validity period (notBefore <= now <= notAfter).
   - Check revocation status (CRL or OCSP).
   - Verify name constraints (if present).
   - Verify policy constraints.
   - Verify Basic Constraints (CA:TRUE for intermediates, pathLen respected).
   - Verify Key Usage includes keyCertSign for CA certs.
3. Confirm the chain terminates at a trust anchor in the trust store.

**Common Chain Issues:**

- **Incomplete chain**: Server sends end-entity cert without intermediate(s). Client cannot build chain → TLS failure.
- **Cross-certification**: A root CA signs another CA's certificate, creating alternative trust paths. Used during CA migrations.
- **Bridge CAs**: Federal Bridge CA (US government) connects disparate PKI hierarchies.

```bash
# Verify chain
openssl verify -CAfile root-ca.pem -untrusted intermediate.pem end-entity.pem

# Download and display chain from server
openssl s_client -connect example.com:443 -showcerts </dev/null 2>/dev/null | \
  awk '/BEGIN CERT/,/END CERT/{print}' > fullchain.pem

# Check chain order
openssl crl2pkcs7 -nocrl -certfile fullchain.pem | \
  openssl pkcs7 -print_certs -noout
```

### 1.4 CA Hierarchy — Root / Intermediate / Issuing

**Three-tier hierarchy (recommended):**

```
Root CA (offline, HSM-protected, 20-30 year validity)
├── Policy CA / Intermediate CA (online or nearline, 10-15 year validity)
│   ├── Issuing CA - TLS Servers (online, 5-7 year validity)
│   ├── Issuing CA - TLS Clients/mTLS (online, 5-7 year validity)
│   ├── Issuing CA - Code Signing (nearline, 5-7 year validity)
│   └── Issuing CA - S/MIME (online, 5-7 year validity)
└── Policy CA - IoT/Devices
    └── Issuing CA - Device Certificates
```

**Root CA:**
- MUST be offline. Air-gapped machine or HSM-only access.
- Used only to sign intermediate CA certificates and CRLs.
- Key ceremony required for any operation (documented, witnessed, recorded).
- Validity: 20-30 years. RSA 4096-bit or ECDSA P-384 minimum.

**Intermediate/Policy CA:**
- Can enforce Name Constraints (restrict issuance to specific domains).
- Validity shorter than root but longer than issuing CAs.
- May be online if properly hardened, or nearline (powered on only for signing operations).

**Issuing CA:**
- Handles day-to-day certificate issuance.
- Fully online, integrated with automation (ACME, SCEP, EST, CMP).
- Shorter key validity, more frequent rotation.
- Constrained by intermediate's Name Constraints and pathLen.

### 1.5 Certificate Lifecycle

```
┌─────────┐     ┌──────────┐     ┌─────────┐     ┌─────────┐     ┌───────────┐
│ Request │ ──▶ │ Issuance │ ──▶ │  Active │ ──▶ │ Renewal │ ──▶ │Revocation │
│  (CSR)  │     │(Signing) │     │  (Use)  │     │(Re-key) │     │  (CRL/    │
└─────────┘     └──────────┘     └─────────┘     └─────────┘     │   OCSP)   │
                                                                   └───────────┘
```

**Certificate Signing Request (CSR):**

```bash
# Generate key + CSR in one command
openssl req -new -newkey ec:<(openssl ecparam -name prime256v1) \
  -keyout server.key -out server.csr -nodes \
  -subj "/C=IT/ST=Lombardia/L=Milano/O=Acme SpA/CN=api.acme.it"

# CSR with SAN (config file method - preferred)
cat > san.cnf <<'EOF'
[req]
distinguished_name = req_dn
req_extensions = v3_req
prompt = no

[req_dn]
C = IT
ST = Lombardia
L = Milano
O = Acme SpA
CN = api.acme.it

[v3_req]
subjectAltName = @alt_names
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth

[alt_names]
DNS.1 = api.acme.it
DNS.2 = *.api.acme.it
DNS.3 = api-internal.acme.it
IP.1 = 10.0.1.50
EOF

openssl req -new -key server.key -out server.csr -config san.cnf

# Verify CSR content
openssl req -in server.csr -text -noout -verify
```

**Issuance**: CA validates request (DV/OV/EV validation), signs the TBS portion with its private key, outputs the certificate.

**Renewal vs Re-key**: Renewal uses the same key pair (acceptable if key is not compromised); re-key generates a new key pair (preferred, limits exposure window).

**Revocation**: Declare a certificate invalid before its expiration. Triggers: key compromise, CA compromise, affiliation change, superseded, cessation of operation.

### 1.6 Revocation Mechanisms

**CRL (Certificate Revocation List):**
- Signed list of revoked serial numbers, published periodically by the CA.
- Cons: grows indefinitely, bandwidth-heavy, update latency (hours to days).
- Distribution: HTTP URL in CRL Distribution Points extension.

```bash
# Download and inspect CRL
curl -s http://crl.ca.example.com/issuing-ca.crl -o ca.crl
openssl crl -in ca.crl -inform DER -text -noout

# Check if a serial is in the CRL
openssl crl -in ca.crl -inform DER -text -noout | grep -i "serial"
```

**OCSP (Online Certificate Status Protocol):**
- Real-time query: "Is serial X revoked?" → response: good/revoked/unknown.
- Defined in RFC 6960.
- Cons: privacy concern (CA sees who visits which sites), availability dependency, latency.

```bash
# Query OCSP responder
openssl ocsp -issuer intermediate.pem -cert server.pem \
  -url http://ocsp.ca.example.com -resp_text

# Verify OCSP response
openssl ocsp -issuer intermediate.pem -cert server.pem \
  -url http://ocsp.ca.example.com -CAfile root.pem -verify_other intermediate.pem
```

**OCSP Stapling:**
- Server pre-fetches its own OCSP response and "staples" it to the TLS handshake (Certificate Status extension).
- Eliminates privacy concerns, reduces latency, removes CA availability dependency from client path.
- OCSP Must-Staple extension (OID 1.3.6.1.5.5.7.1.24): tells clients to REQUIRE a stapled response — hard-fail if missing.

```nginx
# nginx OCSP stapling configuration
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/ssl/chain.pem;
resolver 8.8.8.8 1.1.1.1 valid=300s;
resolver_timeout 5s;
```

### 1.7 Certificate Transparency (CT)

Certificate Transparency (RFC 6962, 9162) is a framework of publicly auditable, append-only logs that record all issued certificates. Purpose: detect rogue or mis-issued certificates.

**Components:**
- **CT Logs**: Append-only Merkle hash trees operated by various organizations (Google, Cloudflare, DigiCert, Sectigo, Let's Encrypt).
- **Monitors**: Services that watch CT logs for certificates matching specific domains.
- **Auditors**: Verify that logs are consistent and append-only (no retroactive removal).

**SCT (Signed Certificate Timestamp):**
- Proof that a certificate has been submitted to a CT log.
- Delivery methods: embedded in certificate (precertificate flow), TLS extension, OCSP stapling.
- Chrome requires SCTs from at least 2-3 independent logs (depending on cert lifetime).

**Operational Use:**
- Monitor CT logs for unauthorized issuance of your domains.
- Detect shadow IT (unexpected subdomains getting certificates).
- Forensic investigation: find all certificates ever issued for a domain.

```bash
# Query crt.sh (Sectigo CT aggregator)
curl -s "https://crt.sh/?q=%.example.com&output=json" | \
  python3 -m json.tool | head -50

# Using certspotter API
curl -s "https://api.certspotter.com/v1/issuances?domain=example.com&include_subdomains=true&expand=dns_names"
```

---

## 2. Implementazione CA Interna

### 2.1 Microsoft AD CS (Active Directory Certificate Services)

AD CS is the enterprise PKI solution deeply integrated with Active Directory. It provides certificate lifecycle management within Windows ecosystems.

**Architecture & Role Services:**

| Role Service | Function |
|--------------|----------|
| Certification Authority | Core CA engine — issues/revokes certificates |
| CA Web Enrollment | IIS-based web interface for manual requests |
| Online Responder (OCSP) | OCSP responses for AD CS-issued certificates |
| Network Device Enrollment Service (NDES) | SCEP protocol for network devices (routers, switches) |
| Certificate Enrollment Policy Web Service | Policy information for non-domain-joined clients |
| Certificate Enrollment Web Service | HTTPS enrollment for non-domain-joined clients |

**Deployment Best Practices:**
- Root CA: Standalone, offline (not domain-joined), Windows Server Core.
- Issuing CA: Enterprise (domain-joined), online, integrated with AD.
- Separate CA for different certificate purposes (TLS, client auth, code signing).

```powershell
# Install AD CS role (Issuing CA)
Install-WindowsFeature -Name AD-Certificate -IncludeManagementTools

# Configure Enterprise Subordinate CA
Install-AdcsCertificationAuthority `
  -CAType EnterpriseSubordinateCA `
  -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" `
  -KeyLength 4096 `
  -HashAlgorithmName SHA256 `
  -CACommonName "Acme Issuing CA G2" `
  -CADistinguishedNameSuffix "O=Acme SpA,C=IT" `
  -DatabaseDirectory "D:\CertDB" `
  -LogDirectory "D:\CertLog" `
  -ValidityPeriod Years `
  -ValidityPeriodUnits 5

# Configure CRL and AIA distribution points
$crlDP = "http://pki.acme.it/crls/<CaName><CRLNameSuffix><DeltaCRLAllowed>.crl"
$aiaDP = "http://pki.acme.it/aia/<ServerDNSName>_<CaName><CertificateName>.crt"

# Set CRL publication interval
certutil -setreg CA\CRLPeriodUnits 7
certutil -setreg CA\CRLPeriod "Days"
certutil -setreg CA\CRLDeltaPeriodUnits 1
certutil -setreg CA\CRLDeltaPeriod "Days"

# Restart CA service
Restart-Service certsvc
```

**Certificate Templates:**

Templates define what a certificate can contain and who can enroll. Key settings:
- Cryptography tab: algorithm, key size, key usage.
- Subject Name: supply in request vs build from AD.
- Issuance Requirements: CA manager approval, authorized signatures.
- Security: which AD groups can Read, Enroll, Autoenroll.

```powershell
# Duplicate and customize a template (via ADSI or PKI module)
# List all templates
Get-CATemplate | Select-Object Name, Oid

# Publish template to issuing CA
Add-CATemplate -Name "WebServerSAN" -Force

# Configure auto-enrollment via Group Policy
# Computer Configuration > Policies > Windows Settings > Security Settings >
# Public Key Policies > Certificate Services Client - Auto-Enrollment
# Set to Enabled, check "Update certificates that use certificate templates"
```

**Key Archival and Recovery:**
- Enable key archival for encryption certificates (NOT signing certificates).
- Requires Key Recovery Agent (KRA) certificate.
- m-of-n recovery: require multiple KRA holders to recover a key.

```powershell
# Configure key archival on CA
certutil -setreg CA\KRAFlags +KRAF_ENABLEARCHIVEALL

# Recover archived key
certutil -getkey <SerialNumber> outputblob.pfx
certutil -recoverkey outputblob.pfx recovered.pfx
```

### 2.2 EJBCA (Enterprise Java Beans Certificate Authority)

EJBCA is an open-source, enterprise-grade CA platform written in Java. Supports X.509, CVC, SSH certificates.

**Key Features:**
- Full CA lifecycle management (root, sub-CA, cross-certification).
- Protocols: CMP (RFC 4210), SCEP, ACME, EST, REST API.
- HA deployment with database clustering.
- HSM integration (PKCS#11): Thales Luna, Utimaco, AWS CloudHSM, SoftHSM.
- OCSP responder (internal or external VA).
- CT log integration.

**Docker Deployment:**

```bash
# Deploy EJBCA Community with Docker
docker run -d --name ejbca \
  -p 8080:8080 -p 8443:8443 \
  -e DATABASE_JDBC_URL="jdbc:mariadb://db:3306/ejbca" \
  -e DATABASE_USER=ejbca \
  -e DATABASE_PASSWORD="${DB_PASS}" \
  -e TLS_SETUP_ENABLED=true \
  keyfactor/ejbca-ce:latest

# Initial superadmin enrollment via CLI
docker exec -it ejbca /opt/keyfactor/bin/ejbca.sh ra addendentity \
  --username superadmin \
  --dn "CN=SuperAdmin,O=Acme" \
  --caname ManagementCA \
  --type 1 \
  --token P12 \
  --password "${ADMIN_PASS}"
```

**Certificate Profiles vs End Entity Profiles:**
- Certificate Profile: defines X.509 content (extensions, validity, key usage).
- End Entity Profile: defines enrollment workflow (what fields are visible, mandatory, who can request).

### 2.3 HashiCorp Vault PKI Secrets Engine

Vault's PKI engine provides a fully API-driven CA with automatic certificate generation and short-lived certificate support. Ideal for microservices and dynamic infrastructure.

**Complete Setup:**

```bash
# Enable PKI secrets engine for root CA
vault secrets enable -path=pki pki

# Set max TTL (root CA validity)
vault secrets tune -max-lease-ttl=87600h pki  # 10 years

# Generate root CA
vault write pki/root/generate/internal \
  common_name="Acme Root CA" \
  issuer_name="acme-root-2026" \
  key_type="ec" \
  key_bits=384 \
  ttl=87600h \
  organization="Acme SpA" \
  country="IT" \
  province="Lombardia" \
  locality="Milano"

# Configure CRL and OCSP URLs
vault write pki/config/urls \
  issuing_certificates="https://vault.acme.it:8200/v1/pki/ca" \
  crl_distribution_points="https://vault.acme.it:8200/v1/pki/crl" \
  ocsp_servers="https://vault.acme.it:8200/v1/pki/ocsp"

# Enable intermediate CA
vault secrets enable -path=pki_int pki

vault secrets tune -max-lease-ttl=43800h pki_int  # 5 years

# Generate intermediate CSR
vault write -format=json pki_int/intermediate/generate/internal \
  common_name="Acme Issuing CA G2" \
  issuer_name="acme-issuing-g2" \
  key_type="ec" \
  key_bits=256 | jq -r '.data.csr' > pki_int.csr

# Sign intermediate with root
vault write -format=json pki/root/sign-intermediate \
  csr=@pki_int.csr \
  format=pem_bundle \
  ttl=43800h | jq -r '.data.certificate' > signed_intermediate.pem

# Import signed intermediate
vault write pki_int/intermediate/set-signed \
  certificate=@signed_intermediate.pem
```

**Role Configuration:**

```bash
# Create role for web servers
vault write pki_int/roles/web-servers \
  allowed_domains="acme.it,acme.internal" \
  allow_subdomains=true \
  allow_bare_domains=false \
  allow_wildcard_certificates=true \
  max_ttl=2160h \
  ttl=720h \
  key_type="ec" \
  key_bits=256 \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ServerAuth" \
  require_cn=false \
  organization="Acme SpA" \
  country="IT" \
  no_store=true

# Create role for mTLS client certificates
vault write pki_int/roles/mtls-clients \
  allowed_domains="acme.internal" \
  allow_subdomains=true \
  max_ttl=24h \
  ttl=1h \
  key_type="ec" \
  key_bits=256 \
  key_usage="DigitalSignature" \
  ext_key_usage="ClientAuth" \
  no_store=true

# Issue a certificate
vault write -format=json pki_int/issue/web-servers \
  common_name="api.acme.it" \
  alt_names="api-v2.acme.it,api.acme.internal" \
  ip_sans="10.0.1.50" \
  ttl=720h
```

**Auto-Rotation with Vault Agent:**

```hcl
# vault-agent-config.hcl
auto_auth {
  method "kubernetes" {
    mount_path = "auth/kubernetes"
    config = {
      role = "web-app"
    }
  }
  sink "file" {
    config = {
      path = "/tmp/vault-token"
    }
  }
}

template {
  source      = "/etc/vault-agent/tls.tpl"
  destination = "/etc/ssl/app/cert.pem"
  perms       = "0644"
  command     = "systemctl reload nginx"
}

template {
  source      = "/etc/vault-agent/key.tpl"
  destination = "/etc/ssl/app/key.pem"
  perms       = "0600"
  command     = "systemctl reload nginx"
}
```

```gotemplate
{{/* /etc/vault-agent/tls.tpl */}}
{{ with secret "pki_int/issue/web-servers" "common_name=api.acme.it" "ttl=720h" }}
{{ .Data.certificate }}
{{ .Data.issuing_ca }}
{{ end }}
```

### 2.4 step-ca — Lightweight CA for DevOps

Smallstep's `step-ca` is a zero-config, API-driven CA purpose-built for DevOps and cloud-native environments. Supports ACME, OAuth/OIDC provisioners, SSH certificates, and short-lived TLS certificates.

```bash
# Initialize CA
step ca init --name="Acme DevOps CA" \
  --provisioner="admin@acme.it" \
  --dns="ca.acme.internal" \
  --address=":8443" \
  --deployment-type standalone

# Start CA
step-ca $(step path)/config/ca.json

# Add ACME provisioner
step ca provisioner add acme --type ACME

# Add OIDC provisioner (for human auth via IdP)
step ca provisioner add google --type OIDC \
  --client-id="xxxx.apps.googleusercontent.com" \
  --client-secret="xxxx" \
  --configuration-endpoint="https://accounts.google.com/.well-known/openid-configuration" \
  --domain="acme.it"

# Request certificate with ACME
step ca certificate api.acme.internal cert.pem key.pem \
  --provisioner acme \
  --san api.acme.internal \
  --san 10.0.1.50

# Automated renewal daemon
step ca renew --daemon cert.pem key.pem \
  --exec "systemctl reload nginx"
```

### 2.5 cfssl — CloudFlare PKI Toolkit

`cfssl` is CloudFlare's PKI/TLS toolkit. Lightweight, JSON-configured, excellent for CI/CD pipeline integration.

```bash
# Initialize root CA
cat > ca-csr.json <<'EOF'
{
  "CN": "Acme Root CA",
  "key": { "algo": "ecdsa", "size": 384 },
  "ca": { "expiry": "87600h" },
  "names": [
    { "C": "IT", "ST": "Lombardia", "L": "Milano", "O": "Acme SpA" }
  ]
}
EOF

cfssl gencert -initca ca-csr.json | cfssljson -bare ca

# Signing profile configuration
cat > cfssl-config.json <<'EOF'
{
  "signing": {
    "default": { "expiry": "8760h" },
    "profiles": {
      "server": {
        "usages": ["signing", "key encipherment", "server auth"],
        "expiry": "2160h"
      },
      "client": {
        "usages": ["signing", "key encipherment", "client auth"],
        "expiry": "720h"
      },
      "peer": {
        "usages": ["signing", "key encipherment", "server auth", "client auth"],
        "expiry": "2160h"
      }
    }
  }
}
EOF

# Issue server certificate
cat > server-csr.json <<'EOF'
{
  "CN": "api.acme.it",
  "hosts": ["api.acme.it", "api.acme.internal", "10.0.1.50"],
  "key": { "algo": "ecdsa", "size": 256 },
  "names": [{ "C": "IT", "O": "Acme SpA" }]
}
EOF

cfssl gencert -ca=ca.pem -ca-key=ca-key.pem \
  -config=cfssl-config.json -profile=server \
  server-csr.json | cfssljson -bare server
```

---

## 3. TLS Configuration e Hardening

### 3.1 TLS 1.2 vs TLS 1.3

**TLS 1.3 (RFC 8446) Key Differences:**

| Aspect | TLS 1.2 | TLS 1.3 |
|--------|---------|---------|
| Handshake RTT | 2-RTT | 1-RTT (0-RTT resumption) |
| Key Exchange | RSA, DHE, ECDHE | ECDHE/DHE only (PFS mandatory) |
| Cipher Suites | ~300 (many insecure) | 5 AEAD-only suites |
| Static RSA | Supported | Removed |
| Compression | Optional | Removed (CRIME mitigation) |
| Renegotiation | Supported | Removed |
| Session Tickets | Yes | Pre-Shared Keys (PSK) |
| 0-RTT | No | Yes (with replay risk) |
| Encrypted Handshake | Only after Finished | After ServerHello |
| Certificate encrypted | No | Yes |
| Change Cipher Spec | Yes | Removed (compatibility mode only) |

**TLS 1.3 Cipher Suites (all AEAD + PFS):**

```
TLS_AES_256_GCM_SHA384        (0x13,0x02)
TLS_AES_128_GCM_SHA256        (0x13,0x01)
TLS_CHACHA20_POLY1305_SHA256  (0x13,0x03)
TLS_AES_128_CCM_SHA256        (0x13,0x04)
TLS_AES_128_CCM_8_SHA256      (0x13,0x05) -- constrained devices
```

**0-RTT Considerations:**
- Enables sending application data in the first flight (zero round-trip time).
- Replay risk: 0-RTT data can be replayed by a network attacker.
- Only safe for idempotent requests (GET, not POST/PUT/DELETE).
- Mitigations: server-side replay detection, single-use tickets, limited time window.

### 3.2 Cipher Suite Selection

**Recommended TLS 1.2 Suites (in priority order):**

```
TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256
TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256
```

**Requirements:**
- **PFS mandatory**: Only ECDHE or DHE key exchange. No static RSA.
- **AEAD only**: GCM or ChaCha20-Poly1305. No CBC (padding oracle attacks).
- **No SHA-1**: SHA-256 minimum for PRF/MAC.
- **No RC4, DES, 3DES, EXPORT ciphers**: Obviously.

**nginx Configuration:**

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.acme.it;

    # Certificates
    ssl_certificate     /etc/ssl/acme/fullchain.pem;
    ssl_certificate_key /etc/ssl/acme/privkey.pem;

    # Protocol versions
    ssl_protocols TLSv1.2 TLSv1.3;

    # TLS 1.2 ciphers (TLS 1.3 ciphers are not configurable in nginx — always secure)
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';
    ssl_prefer_server_ciphers on;

    # ECDH curve
    ssl_ecdh_curve X25519:secp384r1:secp256r1;

    # Session configuration
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;  # Disable for PFS

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/ssl/acme/chain.pem;
    resolver 1.1.1.1 8.8.8.8 valid=300s;

    # DH parameters (TLS 1.2 DHE fallback)
    ssl_dhparam /etc/ssl/dhparam-4096.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
}
```

**Apache Configuration:**

```apache
<VirtualHost *:443>
    ServerName api.acme.it

    SSLEngine on
    SSLCertificateFile      /etc/ssl/acme/fullchain.pem
    SSLCertificateKeyFile   /etc/ssl/acme/privkey.pem

    SSLProtocol             all -SSLv3 -TLSv1 -TLSv1.1
    SSLCipherSuite          ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305
    SSLHonorCipherOrder     on
    SSLSessionTickets       off
    SSLCompression          off

    SSLUseStapling          on
    SSLStaplingResponderTimeout 5
    SSLStaplingReturnResponderErrors off

    Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
</VirtualHost>

SSLStaplingCache shmcb:/var/run/ocsp(128000)
SSLOpenSSLConfCmd ECDHParameters X25519:secp384r1:secp256r1
```

### 3.3 HSTS Deployment

**HTTP Strict Transport Security (RFC 6797):**

Forces browsers to use HTTPS exclusively for a domain. Prevents SSL stripping attacks.

**Deployment Stages:**

```
Stage 1: Start with short max-age, no includeSubDomains
  Strict-Transport-Security: max-age=300

Stage 2: Increase max-age, confirm no HTTP-only resources break
  Strict-Transport-Security: max-age=86400

Stage 3: Add includeSubDomains (all subdomains MUST support HTTPS)
  Strict-Transport-Security: max-age=86400; includeSubDomains

Stage 4: Production max-age (2 years), add preload
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload

Stage 5: Submit to HSTS preload list (hstspreload.org)
```

**HSTS Preload List:**
- Hardcoded in browsers (Chrome, Firefox, Safari, Edge).
- Domain MUST serve valid HTTPS on root domain and all subdomains.
- Once in the list, removal takes months. Do not preload prematurely.
- Submission requirements: valid cert, redirect HTTP→HTTPS, serve HSTS header on HTTPS with `max-age>=31536000`, `includeSubDomains`, `preload`.

**Warning**: Adding `includeSubDomains` when any subdomain lacks HTTPS will break that subdomain for all visitors until the max-age expires from their browser cache. Audit ALL subdomains first.

### 3.4 Certificate Pinning

**HPKP (HTTP Public Key Pinning) — Deprecated:**
- RFC 7469 — allowed servers to pin their certificate's public key hash.
- Deprecated by Chrome in 2018 due to: risk of bricking sites (pin misconfiguration = permanent DoS), weaponization (RansomPKP), operational complexity.
- **Do NOT implement HPKP for web browsers.**

**Mobile App Pinning (Still Relevant):**
- Android: Network Security Config (`<pin-set>` in XML).
- iOS: `Info.plist` App Transport Security or frameworks like TrustKit.
- Purpose: prevent MITM by enterprise proxies or compromised system CAs.

```xml
<!-- Android Network Security Config -->
<network-security-config>
    <domain-config>
        <domain includeSubdomains="true">api.acme.it</domain>
        <pin-set expiration="2027-01-01">
            <!-- Pin the intermediate CA's SPKI hash -->
            <pin digest="SHA-256">YLh1dUR9y6Kja30RrAn7JKnbQG/uEtLMkBgFF2Fuihg=</pin>
            <!-- Backup pin (different CA path) -->
            <pin digest="SHA-256">sRHdihwgkaib1P1gxX8HFszlD+7/gTlPmSOvJNy6bUQ=</pin>
        </pin-set>
    </domain-config>
</network-security-config>
```

**Generating Pin Hashes:**

```bash
# From certificate file (pin the SPKI — Subject Public Key Info)
openssl x509 -in intermediate.pem -pubkey -noout | \
  openssl pkey -pubin -outform DER | \
  openssl dgst -sha256 -binary | base64

# From live server
openssl s_client -connect api.acme.it:443 -servername api.acme.it 2>/dev/null | \
  openssl x509 -pubkey -noout | \
  openssl pkey -pubin -outform DER | \
  openssl dgst -sha256 -binary | base64
```

### 3.5 DANE/TLSA Records

DNS-Based Authentication of Named Entities (RFC 6698). Pins certificates via DNS TLSA records, secured by DNSSEC.

```
_443._tcp.api.acme.it. IN TLSA 3 1 1 <SHA-256 hash of SPKI>
```

**TLSA Fields:**
- Certificate Usage: 0=PKIX-TA, 1=PKIX-EE, 2=DANE-TA, 3=DANE-EE
- Selector: 0=full cert, 1=SubjectPublicKeyInfo
- Matching Type: 0=exact, 1=SHA-256, 2=SHA-512

**Usage 3 (DANE-EE) + Selector 1 (SPKI) + Matching 1 (SHA-256)** is the most common for web servers — pins the end-entity's public key hash.

```bash
# Generate TLSA record content
openssl x509 -in cert.pem -noout -pubkey | \
  openssl pkey -pubin -outform DER | \
  sha256sum | awk '{print $1}'

# Using tlsa CLI
tlsa --create --selector 1 --mtype 1 --certificate cert.pem api.acme.it

# Verify TLSA record
dig +short TLSA _443._tcp.api.acme.it
```

**Limitation**: Requires DNSSEC on the domain. Without DNSSEC, TLSA records are unauthenticated and provide no security guarantee.

### 3.6 SSL/TLS Testing

**testssl.sh:**

```bash
# Comprehensive test
testssl.sh --full https://api.acme.it

# Specific checks
testssl.sh --protocols --ciphers --headers --vulnerabilities https://api.acme.it

# JSON output for automation
testssl.sh --jsonfile results.json --severity HIGH https://api.acme.it

# Test specific vulnerabilities
testssl.sh --heartbleed --ccs-injection --ticketbleed --robot \
  --crime --breach --poodle --freak --logjam --drown https://api.acme.it
```

**sslyze:**

```bash
# Full scan
sslyze api.acme.it

# Specific commands
sslyze --tlsv1_2 --tlsv1_3 --certinfo --http_headers api.acme.it

# JSON output
sslyze --json_out=results.json api.acme.it

# Check certificate transparency
sslyze --certinfo api.acme.it | grep "Certificate Transparency"
```

**sslscan:**

```bash
# Standard scan
sslscan api.acme.it:443

# Show supported ciphers only
sslscan --show-ciphers api.acme.it

# Check specific protocol
sslscan --tls12 api.acme.it
```

**Qualys SSL Labs API:**

```bash
# Initiate scan (async)
curl -s "https://api.ssllabs.com/api/v3/analyze?host=api.acme.it&startNew=on"

# Poll for results
curl -s "https://api.ssllabs.com/api/v3/analyze?host=api.acme.it" | \
  python3 -c "import sys,json; d=json.load(sys.stdin); \
  print(f'Grade: {d[\"endpoints\"][0][\"grade\"]}')" 2>/dev/null
```

---

## 4. Certificate Automation

### 4.1 ACME Protocol (RFC 8555)

Automatic Certificate Management Environment — the protocol behind Let's Encrypt. Enables fully automated DV certificate issuance.

**Flow:**
1. Client creates account with ACME server.
2. Client submits order for identifiers (domains).
3. Server returns authorization challenges.
4. Client completes challenge(s) to prove domain control.
5. Client submits CSR via finalize URL.
6. Server issues certificate.

**Challenge Types:**

| Type | Mechanism | Use Case |
|------|-----------|----------|
| HTTP-01 | Place file at `/.well-known/acme-challenge/<token>` | Standard web servers |
| DNS-01 | Create TXT record `_acme-challenge.<domain>` | Wildcards, non-web services, firewalled hosts |
| TLS-ALPN-01 | TLS handshake with special ALPN extension and self-signed cert | Reverse proxies, no HTTP/DNS control |

**ACME Providers:**

| Provider | Rate Limits | Wildcard | Cost |
|----------|-------------|----------|------|
| Let's Encrypt | 50 certs/week/domain, 300 new orders/3h | Yes (DNS-01) | Free |
| ZeroSSL | 3 free certs, unlimited paid | Yes | Free/Paid |
| BuyPass Go | 20 certs/week/domain | Yes | Free |
| Google Trust Services | Via Google Cloud | Yes | Free |
| ssl.com | Varies | Yes | Paid |

### 4.2 Certbot

```bash
# Install
apt install certbot python3-certbot-nginx  # Debian/Ubuntu
dnf install certbot python3-certbot-nginx  # RHEL/Fedora

# Obtain certificate — nginx plugin (modifies nginx config)
certbot --nginx -d api.acme.it -d www.acme.it \
  --email security@acme.it --agree-tos --no-eff-email

# Obtain certificate — standalone (certbot runs its own server on :80)
certbot certonly --standalone -d api.acme.it \
  --preferred-challenges http

# Obtain certificate — webroot (existing server handles HTTP)
certbot certonly --webroot -w /var/www/html -d api.acme.it

# Wildcard via DNS challenge (manual)
certbot certonly --manual --preferred-challenges dns \
  -d "*.acme.it" -d acme.it

# Wildcard via DNS challenge (automated with DNS plugin)
certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d "*.acme.it" -d acme.it

# Renewal hooks
certbot renew --deploy-hook "systemctl reload nginx" \
  --pre-hook "echo 'starting renewal'" \
  --post-hook "echo 'renewal complete'"

# Test renewal (dry run)
certbot renew --dry-run

# Renewal cron/systemd timer (usually auto-installed)
# /etc/cron.d/certbot:
# 0 */12 * * * root certbot renew --quiet --deploy-hook "systemctl reload nginx"
```

**Certbot DNS Plugin — Cloudflare Example:**

```ini
# /etc/letsencrypt/cloudflare.ini (mode 0600)
dns_cloudflare_api_token = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

### 4.3 cert-manager in Kubernetes

cert-manager is the de facto standard for certificate lifecycle management in Kubernetes. It manages issuance and renewal of TLS certificates from various sources.

**Installation:**

```bash
# Helm installation
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set crds.enabled=true \
  --set prometheus.enabled=true
```

**ClusterIssuer — Let's Encrypt:**

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    email: security@acme.it
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
    - http01:
        ingress:
          ingressClassName: nginx
    - dns01:
        cloudDNS:
          project: acme-gcp-project
          serviceAccountSecretRef:
            name: clouddns-sa
            key: key.json
      selector:
        dnsZones:
        - "acme.it"
```

**ClusterIssuer — Vault PKI:**

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: vault-issuer
spec:
  vault:
    path: pki_int/sign/web-servers
    server: https://vault.acme.internal:8200
    caBundle: <base64-encoded-vault-ca>
    auth:
      kubernetes:
        role: cert-manager
        mountPath: /v1/auth/kubernetes
        serviceAccountRef:
          name: cert-manager
```

**Certificate Resource:**

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: api-acme-it
  namespace: production
spec:
  secretName: api-acme-it-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  commonName: api.acme.it
  dnsNames:
  - api.acme.it
  - api-v2.acme.it
  duration: 2160h      # 90 days
  renewBefore: 720h    # Renew 30 days before expiry
  privateKey:
    algorithm: ECDSA
    size: 256
    rotationPolicy: Always
  usages:
  - server auth
  - digital signature
  - key encipherment
```

**Ingress Annotation (automatic):**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.acme.it
    secretName: api-acme-it-tls
  rules:
  - host: api.acme.it
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080
```

**ACME Solver Types:**

| Solver | When to Use |
|--------|-------------|
| HTTP-01 (ingress) | Standard web workloads with public ingress |
| HTTP-01 (gateway) | Gateway API environments |
| DNS-01 (various providers) | Wildcards, non-HTTP services, private clusters |
| TLS-ALPN-01 | Environments where only port 443 is available |

### 4.4 Venafi as Certificate Management Platform

Venafi TLS Protect (formerly Trust Protection Platform) provides enterprise-grade certificate visibility and policy enforcement across the entire organization.

**Key Capabilities:**
- Discovery: scan networks, CT logs, cloud providers to find ALL certificates.
- Policy: enforce key length, algorithm, validity, CA, SAN patterns.
- Automation: integrate with F5, Citrix, IIS, Apache, nginx, Kubernetes.
- Visibility: single dashboard for all certificates across all environments.
- Compliance: enforce CA/Browser Forum requirements, internal policies.

**Integration Points:**
- cert-manager (Venafi Issuer for Kubernetes)
- HashiCorp Vault (Venafi PKI backend)
- Terraform provider
- Ansible modules
- CI/CD webhooks

### 4.5 Monitoring Certificate Expiry

**Prometheus Exporter — x509-certificate-exporter:**

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: x509-certificate-exporter
spec:
  template:
    spec:
      containers:
      - name: exporter
        image: enix/x509-certificate-exporter:3.14.0
        args:
        - --watch-kube-secrets
        - --secret-type=kubernetes.io/tls
        - --listen-address=:9793
        ports:
        - containerPort: 9793
```

**Prometheus Alert Rules:**

```yaml
groups:
- name: certificate-expiry
  rules:
  - alert: CertificateExpiringSoon
    expr: x509_cert_not_after - time() < 30 * 24 * 3600
    for: 1h
    labels:
      severity: warning
    annotations:
      summary: "Certificate {{ $labels.subject_CN }} expires in < 30 days"

  - alert: CertificateExpiryCritical
    expr: x509_cert_not_after - time() < 7 * 24 * 3600
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Certificate {{ $labels.subject_CN }} expires in < 7 days"

  - alert: CertificateExpired
    expr: x509_cert_not_after - time() < 0
    for: 0m
    labels:
      severity: critical
    annotations:
      summary: "Certificate {{ $labels.subject_CN }} HAS EXPIRED"
```

**Nagios/Icinga Check:**

```bash
#!/bin/bash
# check_ssl_cert.sh
HOST=$1
PORT=${2:-443}
WARN_DAYS=${3:-30}
CRIT_DAYS=${4:-7}

EXPIRY=$(echo | openssl s_client -servername "$HOST" -connect "$HOST:$PORT" 2>/dev/null | \
  openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)

if [ -z "$EXPIRY" ]; then
  echo "UNKNOWN - Cannot connect to $HOST:$PORT"
  exit 3
fi

EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt 0 ]; then
  echo "CRITICAL - Certificate EXPIRED $((DAYS_LEFT * -1)) days ago"
  exit 2
elif [ $DAYS_LEFT -lt $CRIT_DAYS ]; then
  echo "CRITICAL - Certificate expires in $DAYS_LEFT days"
  exit 2
elif [ $DAYS_LEFT -lt $WARN_DAYS ]; then
  echo "WARNING - Certificate expires in $DAYS_LEFT days"
  exit 1
else
  echo "OK - Certificate expires in $DAYS_LEFT days"
  exit 0
fi
```

---

## 5. Attacchi ai Certificati — Red Team

### 5.1 Certificate Forgery with Compromised CA Key

If an attacker obtains a CA private key, they can forge certificates for ANY domain within that CA's trust scope. Historical incidents: DigiNotar (2011), Comodo reseller (2011), CNNIC/MCS Holdings (2015).

**Attack Scenario:**

```bash
# Attacker has stolen intermediate-ca-key.pem
# Forge certificate for target.com

openssl req -new -newkey ec:<(openssl ecparam -name prime256v1) \
  -keyout forged-key.pem -out forged.csr -nodes \
  -subj "/CN=login.target.com"

openssl x509 -req -in forged.csr \
  -CA stolen-intermediate.pem -CAkey stolen-intermediate-key.pem \
  -CAcreateserial -out forged-cert.pem \
  -days 365 -sha256 \
  -extfile <(printf "subjectAltName=DNS:login.target.com,DNS:*.target.com")
```

**Detection:**
- CT log monitoring will reveal unauthorized issuance.
- CAA records (DNS) limit which CAs can issue for your domain (but attacker has already bypassed the CA).
- DANE/TLSA records will cause validation failure if the forged cert does not match the pinned hash.

**Mitigation:**
- Multi-party control over CA key material (m-of-n HSM access).
- Offline root CA.
- Name Constraints on intermediate CAs.
- CT monitoring with immediate alerting.
- Short-lived certificates (limit window of exposure).

### 5.2 Rogue CA Installation Attacks

Installing a rogue root CA in a target's trust store enables transparent MITM of all TLS traffic.

**Attack Vectors:**
- Corporate proxy "SSL inspection" with employee-device enrollment.
- Malware adding root CA (Superfish/Lenovo 2015, eDellRoot 2015).
- Government-mandated root CAs (Kazakhstan 2019 — browsers blocked it).
- Social engineering: "Install this certificate to access the network."
- MDM profile abuse on mobile devices.

**Detection:**
- Audit trust store changes (Windows: `certutil -store root`, macOS: `security dump-keychain`, Linux: check `/etc/ssl/certs/`).
- Certificate Transparency: certificates signed by rogue CAs will NOT appear in public CT logs (absence is the signal).
- Endpoint detection: compare presented cert chain against expected CT log presence.

```powershell
# Windows — List all root CAs
Get-ChildItem Cert:\LocalMachine\Root | Select-Object Subject, NotAfter, Thumbprint

# Detect non-standard root CAs (compare against known good list)
$knownRoots = Get-Content .\approved-root-thumbprints.txt
Get-ChildItem Cert:\LocalMachine\Root | Where-Object {
    $_.Thumbprint -notin $knownRoots
} | ForEach-Object {
    Write-Warning "UNKNOWN ROOT CA: $($_.Subject) [$($_.Thumbprint)]"
}
```

### 5.3 SSL Stripping

SSL stripping (Moxie Marlinspike, 2009) downgrades HTTPS connections to HTTP by intercepting the initial HTTP→HTTPS redirect.

**sslstrip Attack Flow:**
1. Attacker performs ARP spoofing (or sits at network chokepoint).
2. Victim requests `http://bank.com`.
3. Attacker intercepts, connects to `https://bank.com` on victim's behalf.
4. Attacker serves content to victim over plain HTTP.
5. Victim sees no lock icon but many users do not notice.

```bash
# Classic sslstrip attack (educational/authorized testing only)
echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -t nat -A PREROUTING -p tcp --destination-port 80 -j REDIRECT --to-port 10000
sslstrip -l 10000 --write sslstrip.log
# Combine with arpspoof or bettercap for MITM position
```

**HSTS Bypass Attempts:**
- If victim has previously visited the site with HSTS, browser refuses HTTP. Attack fails.
- **sslstrip2/sslstrip+**: Uses DNS spoofing to redirect to a lookalike subdomain NOT in HSTS cache (e.g., `wwww.bank.com` → no HSTS entry for that specific name).
- **HSTS Preload** defeats this because the entire domain (with subdomains) is hardcoded in the browser.

**Defense Stack:**
1. HSTS with `includeSubDomains` and `preload`.
2. Preload list submission.
3. HTTP→HTTPS redirect with 301 (cacheable).
4. CAA DNS records.
5. Consider HTTPS-Only mode (Firefox) / HTTPS-First mode (Chrome).

### 5.4 Certificate Impersonation and Homograph Attacks

- IDN homograph: register `аcme.it` (Cyrillic "а") to impersonate `acme.it` (Latin "a"). Modern browsers display punycode for mixed-script domains.
- Lookalike domains: `acme-login.it`, `acme.it.evil.com`.
- Attack: obtain legitimate DV cert for lookalike domain (trivial — DV only validates domain control).

**Defense:**
- Monitor CT logs for similar-looking domains.
- Defensive domain registration.
- DMARC/SPF/DKIM for email impersonation prevention.
- User awareness training.

### 5.5 MITM with Self-Signed Certificates

On internal networks or IoT devices that do not validate certificate chains properly, an attacker can present a self-signed certificate and intercept traffic.

```bash
# Generate self-signed cert mimicking target
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout mitm-key.pem -out mitm-cert.pem -days 1 \
  -subj "/CN=internal-api.acme.it"

# Use with mitmproxy
mitmproxy --mode transparent --set ssl_insecure=true \
  --set certs=*=mitm-cert.pem
```

**Why it works:** Many internal tools, scripts, IoT devices, and misconfigured applications disable certificate verification (`verify=False`, `curl -k`, `NODE_TLS_REJECT_UNAUTHORIZED=0`).

**Detection:**
- Network IDS: detect TLS connections where the certificate does not chain to a known CA.
- Endpoint agents: alert on applications disabling cert verification.

### 5.6 BGP Hijacking + Certificate Issuance

Advanced attack: hijack BGP routes to redirect traffic for a target domain, then complete ACME HTTP-01 or TLS-ALPN-01 challenge to obtain a legitimate certificate.

**Attack Chain:**
1. Announce more-specific BGP prefix containing target's IP.
2. Traffic for target domain flows to attacker.
3. ACME server's validation request also routes to attacker.
4. Attacker completes challenge, obtains valid certificate.
5. Withdraw BGP announcement.
6. Use certificate for MITM at a later time.

**Real-World Incidents:** Amazon Route 53 (2018), MyEtherWallet (2018).

**Defenses:**
- RPKI (Resource Public Key Infrastructure) for BGP route origin validation.
- Multi-perspective validation (Let's Encrypt added this in 2020 — validates from multiple network vantage points).
- CAA records (prevent issuance by CAs you do not use).
- CT monitoring (detect unauthorized issuance quickly).
- DNS-01 challenges are immune to BGP hijacking (DNS resolution can still be attacked separately).

### 5.7 Compromising ACME DNS Challenges

DNS-01 challenges require creating a TXT record. If an attacker can modify DNS records for a target domain, they can complete the challenge and obtain certificates.

**Attack Vectors:**
- Compromised DNS provider credentials (leaked API keys).
- DNS zone transfer exploitation.
- Registrar account takeover.
- Dangling DNS records (subdomain takeover: CNAME pointing to decommissioned cloud resource).

**Subdomain Takeover for Cert Issuance:**

```bash
# 1. Find dangling CNAME
dig CNAME old-app.acme.it
# old-app.acme.it. CNAME something.herokuapp.com. (but app was deleted)

# 2. Claim the herokuapp subdomain
# 3. Serve ACME HTTP-01 challenge on that subdomain
# 4. Obtain valid cert for old-app.acme.it
```

**Defense:**
- Audit DNS records regularly. Remove dangling CNAMEs.
- Use CAA records to restrict which CAs can issue.
- Limit DNS API credentials (scope to specific zones, use short-lived tokens).
- Enable multi-factor on registrar accounts.
- Monitor CT logs for unexpected subdomain certificates.

---

## 6. mTLS e Service Mesh

### 6.1 Mutual TLS Architecture

Standard TLS is unidirectional: the client authenticates the server. Mutual TLS (mTLS) adds the reverse: the server also authenticates the client via a client certificate.

**Handshake Addition (TLS 1.2/1.3):**
1. Server sends `CertificateRequest` message during handshake.
2. Client responds with its certificate and `CertificateVerify` (signature proving possession of private key).
3. Server validates client certificate against its trust store and optionally checks CRL/OCSP.

**Use Cases:**
- Service-to-service authentication (zero-trust networks).
- API authentication (stronger than API keys/OAuth).
- IoT device authentication.
- VPN/network access control (802.1X-TLS).
- Financial services (PSD2 eIDAS certificates).

### 6.2 Client Certificate Authentication

**nginx mTLS Configuration:**

```nginx
server {
    listen 443 ssl;
    server_name api.acme.it;

    ssl_certificate     /etc/ssl/server-cert.pem;
    ssl_certificate_key /etc/ssl/server-key.pem;

    # Client certificate verification
    ssl_client_certificate /etc/ssl/client-ca.pem;  # CA(s) that sign client certs
    ssl_verify_client on;          # Require client cert (use "optional" for mixed)
    ssl_verify_depth 2;            # Chain depth for client certs

    # Optional: CRL for client cert revocation
    ssl_crl /etc/ssl/client-crl.pem;

    # Pass client cert info to backend
    location / {
        proxy_pass http://backend;
        proxy_set_header X-Client-DN $ssl_client_s_dn;
        proxy_set_header X-Client-Serial $ssl_client_serial;
        proxy_set_header X-Client-Verify $ssl_client_verify;
        proxy_set_header X-Client-Fingerprint $ssl_client_fingerprint;
    }
}
```

**Apache mTLS:**

```apache
<VirtualHost *:443>
    SSLEngine on
    SSLCertificateFile    /etc/ssl/server-cert.pem
    SSLCertificateKeyFile /etc/ssl/server-key.pem

    SSLCACertificateFile  /etc/ssl/client-ca.pem
    SSLVerifyClient require
    SSLVerifyDepth 2

    # Optional: restrict to specific client CN
    <Location /admin>
        SSLRequire %{SSL_CLIENT_S_DN_CN} eq "admin-service"
    </Location>
</VirtualHost>
```

### 6.3 SPIFFE/SPIRE for Workload Identity

SPIFFE (Secure Production Identity Framework for Everyone) provides a standard for workload identity — cryptographic identity for services without relying on network location or secrets.

**Core Concepts:**
- **SPIFFE ID**: URI-format identity: `spiffe://trust-domain/path` (e.g., `spiffe://acme.it/production/api-service`).
- **SVID (SPIFFE Verifiable Identity Document)**: X.509 certificate or JWT token containing the SPIFFE ID in the SAN URI field.
- **Trust Domain**: Administrative boundary. Analogous to a CA trust realm.
- **Workload Attestation**: Proving workload identity based on platform-specific selectors (Kubernetes pod metadata, AWS instance identity, docker labels).

**SPIRE (SPIFFE Runtime Environment):**

```bash
# Deploy SPIRE server
helm install spire-server spiffe/spire-server \
  --set trustDomain=acme.it

# Register workload entry
spire-server entry create \
  -spiffeID spiffe://acme.it/production/api-service \
  -parentID spiffe://acme.it/spire-agent/node1 \
  -selector k8s:ns:production \
  -selector k8s:sa:api-service \
  -ttl 3600

# Workload fetches SVID via Workload API
# No secrets in config — identity derived from platform attestation
```

### 6.4 Istio mTLS

Istio service mesh provides transparent mTLS between services via Envoy sidecar proxies.

**PeerAuthentication — Mesh-wide Strict mTLS:**

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system  # Mesh-wide
spec:
  mtls:
    mode: STRICT  # All traffic must be mTLS
```

**Permissive vs Strict:**
- **PERMISSIVE**: Accept both plaintext and mTLS. Use during migration.
- **STRICT**: Reject plaintext. Required for zero-trust.
- **DISABLE**: No mTLS (not recommended).

**Per-Namespace Override:**

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: legacy-namespace
  namespace: legacy-apps
spec:
  mtls:
    mode: PERMISSIVE  # Allow legacy apps to connect without mTLS
```

**DestinationRule — Client-side mTLS Settings:**

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: api-service
  namespace: production
spec:
  host: api-service.production.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL  # Use Istio's built-in certs
```

### 6.5 Envoy TLS Configuration

```yaml
# Envoy listener with mTLS
static_resources:
  listeners:
  - name: mtls_listener
    address:
      socket_address:
        address: 0.0.0.0
        port_value: 8443
    filter_chains:
    - transport_socket:
        name: envoy.transport_sockets.tls
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.DownstreamTlsContext
          require_client_certificate: true
          common_tls_context:
            tls_certificates:
            - certificate_chain:
                filename: /certs/server-cert.pem
              private_key:
                filename: /certs/server-key.pem
            validation_context:
              trusted_ca:
                filename: /certs/client-ca.pem
            tls_params:
              tls_minimum_protocol_version: TLSv1_3
```

### 6.6 gRPC mTLS

```go
// Go gRPC server with mTLS
cert, _ := tls.LoadX509KeyPair("server-cert.pem", "server-key.pem")
caCert, _ := os.ReadFile("client-ca.pem")
caPool := x509.NewCertPool()
caPool.AppendCertsFromPEM(caCert)

tlsConfig := &tls.Config{
    Certificates: []tls.Certificate{cert},
    ClientCAs:    caPool,
    ClientAuth:   tls.RequireAndVerifyClientCert,
    MinVersion:   tls.VersionTLS13,
}

server := grpc.NewServer(grpc.Creds(credentials.NewTLS(tlsConfig)))
```

```go
// Go gRPC client with mTLS
cert, _ := tls.LoadX509KeyPair("client-cert.pem", "client-key.pem")
caCert, _ := os.ReadFile("server-ca.pem")
caPool := x509.NewCertPool()
caPool.AppendCertsFromPEM(caCert)

tlsConfig := &tls.Config{
    Certificates: []tls.Certificate{cert},
    RootCAs:      caPool,
    MinVersion:   tls.VersionTLS13,
}

conn, _ := grpc.Dial("api.acme.it:8443",
    grpc.WithTransportCredentials(credentials.NewTLS(tlsConfig)))
```

### 6.7 Certificate Rotation in Service Mesh — Zero Downtime

**Istio Certificate Rotation:**
- Citadel (Istio CA) issues short-lived certificates to sidecars (default: 24h).
- Envoy sidecars use SDS (Secret Discovery Service) for hot-reloading.
- No pod restart needed during rotation.
- Grace period: new cert issued before old one expires (default: 50% of lifetime).

**Manual Rotation Strategy (non-mesh):**

```bash
# 1. Deploy new certificate alongside old one (dual-cert phase)
# 2. Update server config to use new certificate
# 3. Reload server (not restart) — existing connections continue with old cert
# 4. New connections use new certificate
# 5. After all old connections drain, remove old cert

# nginx zero-downtime reload
nginx -t && systemctl reload nginx
# reload sends SIGHUP — graceful transition, no dropped connections
```

---

## 7. Code Signing e Document Signing

### 7.1 Code Signing Certificates

**Types by Validation Level:**

| Type | Validation | Trust Indicators | Use Case |
|------|-----------|-----------------|----------|
| Standard (OV) | Organization identity verified | Publisher name in signature | Internal tools |
| EV (Extended Validation) | Rigorous org verification + HSM | Immediate SmartScreen reputation, hardware key required | Public software distribution |
| Individual (IV) | Personal identity | Individual name | Independent developers |

**Platform-Specific Signing:**

| Platform | Format | Signing Tool |
|----------|--------|-------------|
| Windows | Authenticode (PE, MSI, MSIX, PS1, DLL) | signtool.exe, SignTool |
| macOS | Code Signature (Mach-O, DMG, PKG) | codesign, productsign |
| Linux | GPG detached signature, RPM signing | gpg, rpmsign |
| Java | JAR signing | jarsigner |
| Android | APK Signature Scheme v2/v3 | apksigner |
| Container images | OCI signatures | cosign, notation |

### 7.2 Authenticode, GPG, and Sigstore/Cosign

**Authenticode (Windows):**

```powershell
# Sign executable with timestamp
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 `
  /f code-signing.pfx /p "$env:PFX_PASSWORD" app.exe

# Verify signature
signtool verify /pa /v app.exe

# Sign PowerShell script
Set-AuthenticodeSignature -FilePath script.ps1 `
  -Certificate (Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert) `
  -TimestampServer "http://timestamp.digicert.com" `
  -HashAlgorithm SHA256
```

**Sigstore/Cosign (Keyless Signing for Containers):**

```bash
# Sign container image (keyless — uses OIDC identity)
cosign sign --yes ghcr.io/acme/api-service:v1.2.3

# Sign with key pair
cosign generate-key-pair
cosign sign --key cosign.key ghcr.io/acme/api-service:v1.2.3

# Verify signature
cosign verify --certificate-identity=security@acme.it \
  --certificate-oidc-issuer=https://accounts.google.com \
  ghcr.io/acme/api-service:v1.2.3

# Attach SBOM and sign it
cosign attest --predicate sbom.json --type spdxjson \
  ghcr.io/acme/api-service:v1.2.3

# Verify attestation
cosign verify-attestation --type spdxjson \
  --certificate-identity=security@acme.it \
  --certificate-oidc-issuer=https://accounts.google.com \
  ghcr.io/acme/api-service:v1.2.3
```

### 7.3 Software Supply Chain — SLSA Framework

SLSA (Supply-chain Levels for Software Artifacts) defines levels of supply chain security:

| Level | Requirements |
|-------|-------------|
| SLSA 1 | Build process documented, provenance generated |
| SLSA 2 | Signed provenance, build service (not developer laptop) |
| SLSA 3 | Hardened build platform, non-falsifiable provenance |
| SLSA 4 | Two-person review, hermetic/reproducible builds |

**Integration with Certificate Management:**
- Build provenance signed with short-lived certificates (Sigstore Fulcio).
- Certificate embedded in Rekor transparency log.
- Verification traces back to identity (OIDC) not long-lived key.

### 7.4 Timestamping Authority (TSA)

Timestamps prove code was signed BEFORE the signing certificate expired or was revoked. Without timestamps, all signatures become invalid when the cert expires.

**RFC 3161 Timestamp Protocol:**

```bash
# Create timestamp request
openssl ts -query -data file.dat -no_nonce -sha256 -out ts-request.tsq

# Submit to TSA
curl -H "Content-Type: application/timestamp-query" \
  --data-binary @ts-request.tsq \
  http://timestamp.digicert.com -o ts-response.tsr

# Verify timestamp
openssl ts -verify -in ts-response.tsr -data file.dat \
  -CAfile tsa-ca.pem
```

### 7.5 Document Signing

**PDF Signing (PAdES — PDF Advanced Electronic Signatures):**
- Long-term validation (LTV): embeds all certificates, OCSP responses, and CRLs in the PDF.
- Conformance levels: PAdES-B, PAdES-T (timestamp), PAdES-LT (long-term), PAdES-LTA (long-term archival).

**XML Signing (XAdES — XML Advanced Electronic Signatures):**
- Enveloped, enveloping, or detached signatures.
- Levels: XAdES-B, XAdES-T, XAdES-LT, XAdES-LTA.

**S/MIME Email Encryption/Signing:**

```bash
# Sign email
openssl smime -sign -in message.txt -out signed.p7m \
  -signer user-cert.pem -inkey user-key.pem -text

# Encrypt email
openssl smime -encrypt -in message.txt -out encrypted.p7m \
  -des3 recipient-cert.pem

# Verify S/MIME signature
openssl smime -verify -in signed.p7m -CAfile ca-chain.pem
```

---

## 8. Gestione Operativa

### 8.1 Certificate Inventory and Discovery

**Discovery Methods:**

1. **Network scanning**: Scan IP ranges/ports for TLS services.
2. **CT log monitoring**: Watch public CT logs for your domains.
3. **Configuration management**: Parse configs from nginx, Apache, load balancers.
4. **Cloud provider APIs**: AWS ACM, GCP CAS, Azure Key Vault.
5. **Agent-based**: Deploy agents that report local certificate stores.

**Network Discovery with nmap:**

```bash
# Scan for TLS services and extract certificate info
nmap -p 443,8443,9443 --script ssl-cert -oX certs.xml 10.0.0.0/24

# Extract cert details from scan results
nmap -p 443 --script ssl-cert --script-args=ssl-cert.maxdepth=3 \
  -oN cert-inventory.txt target-list.txt
```

**CT Log Monitoring Script:**

```bash
#!/bin/bash
# Monitor CT logs for unauthorized certificates
DOMAIN="acme.it"
KNOWN_ISSUERS="Let's Encrypt|DigiCert|Sectigo"
ALERT_EMAIL="security@acme.it"

certs=$(curl -s "https://crt.sh/?q=%25.${DOMAIN}&output=json" | \
  python3 -c "
import sys, json
from datetime import datetime, timedelta
certs = json.load(sys.stdin)
cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
for c in certs:
    if c['not_before'] > cutoff:
        print(f\"{c['common_name']}|{c['issuer_name']}|{c['serial_number']}\")
")

while IFS='|' read -r cn issuer serial; do
  if ! echo "$issuer" | grep -qiE "$KNOWN_ISSUERS"; then
    echo "ALERT: Unexpected issuer for ${cn}: ${issuer} (serial: ${serial})" | \
      mail -s "CT Alert: Unauthorized Certificate" "$ALERT_EMAIL"
  fi
done <<< "$certs"
```

### 8.2 Expiry Alerting and Dashboards

**Grafana Dashboard Queries (with Prometheus x509 exporter):**

```promql
# Certificates expiring within 30 days
x509_cert_not_after - time() < 30 * 24 * 3600

# Time until expiry (for gauge display)
(x509_cert_not_after - time()) / 86400

# Count of certificates by issuer
count by (issuer_CN) (x509_cert_not_after)

# Certificates already expired
x509_cert_not_after < time()
```

### 8.3 Key Ceremony Procedures

A key ceremony is the formal, audited process of generating, backing up, or rotating CA key material. Required for root and intermediate CA keys.

**Ceremony Requirements:**

1. **Participants**: minimum 3 roles — Ceremony Administrator, Crypto Officer(s), Witness(es).
2. **Location**: Secure room with access controls, no network connectivity.
3. **HSM**: FIPS 140-2 Level 3+ (or Level 4 for root CAs). Common: Thales Luna, Utimaco CryptoServer, AWS CloudHSM (for cloud-hosted intermediates).
4. **M-of-N Key Splitting**: Root key activation requires M of N smart cards/PINs (e.g., 3-of-5). No single person can activate the key.
5. **Video Recording**: End-to-end recording of the ceremony. Stored securely.
6. **Script**: Pre-written, reviewed script of exact commands/steps. No deviation.
7. **Hash Verification**: At each step, hash outputs and compare against expected values.
8. **Documentation**: Signed ceremony report with all participants' signatures.

**Example Ceremony Script (abbreviated):**

```bash
# === ROOT CA KEY GENERATION CEREMONY ===
# Date: 2026-05-07
# Location: Secure Room B, Building 3
# HSM: Thales Luna Network HSM 7 (serial: 1234567)
# Participants: [names redacted]

# Step 1: Verify HSM firmware and configuration
lunacm -c haInfo

# Step 2: Login with multi-party authentication (M-of-N)
# Crypto Officers insert smart cards (3 of 5 required)
lunacm -c login -s 1  # Each CO enters their PIN

# Step 3: Generate key pair on HSM
# Record key handle for audit trail
cmu generatekeypair \
  -keyType=EC -curvetype=P-384 \
  -labelPublic="ACME-ROOT-CA-2026-PUB" \
  -labelPrivate="ACME-ROOT-CA-2026-PRIV" \
  -extractable=false

# Step 4: Generate self-signed root certificate
# (Using HSM-backed key — key never leaves HSM)

# Step 5: Export public key and certificate (NOT private key)
# Step 6: Verify certificate
# Step 7: Distribute root CA certificate to trust stores
# Step 8: Logout and verify HSM audit log
# Step 9: Secure smart cards in separate safes
```

### 8.4 Disaster Recovery for CA

**Recovery Scenarios:**

| Scenario | Impact | Recovery |
|----------|--------|----------|
| Issuing CA failure | No new certs issued | Restore from backup, re-enroll |
| Issuing CA key compromise | All issued certs suspect | Revoke intermediate, re-issue from backup CA |
| Intermediate CA key compromise | Entire sub-tree compromised | Revoke intermediate, issue new from root, re-issue all end-entity |
| Root CA key compromise | Entire PKI compromised | Full PKI rebuild, new root, all clients update trust stores |
| HSM failure | Key material inaccessible | Restore from HSM backup partition or cloned HSM |

**Backup Strategy:**

- Root CA: HSM backup (cloned to secondary HSM in separate location). Offline encrypted backup of HSM partition.
- Intermediate CA: Encrypted key backup + CA database backup. Test restore quarterly.
- Issuing CA: Automated daily backups. Can be rebuilt from intermediate if total loss.
- Configuration: Infrastructure-as-Code (Terraform, Ansible) for CA configuration. Version-controlled.

```powershell
# AD CS backup
Backup-CARoleService -Path "D:\CABackup" -Password (ConvertTo-SecureString "..." -AsPlainText -Force)

# Restore AD CS
Restore-CARoleService -Path "D:\CABackup" -Password (ConvertTo-SecureString "..." -AsPlainText -Force)
```

### 8.5 Certificate Revocation Procedures

**Emergency Revocation (Key Compromise):**

1. Immediately revoke the certificate with reason `keyCompromise`.
2. Publish updated CRL.
3. If OCSP responder is cached, force refresh or reduce OCSP response validity.
4. Notify affected parties.
5. Issue replacement certificate with new key pair.
6. Investigate compromise vector.
7. Document in incident report.

**Routine Revocation (Employee Departure, Service Decommission):**

1. Verify authorization for revocation request.
2. Revoke with appropriate reason code (cessationOfOperation, superseded, affiliationChanged).
3. Standard CRL publication cycle is acceptable.
4. Remove certificate and key from systems.
5. Update inventory.

```bash
# Revoke certificate (OpenSSL CA)
openssl ca -config ca.cnf -revoke compromised-cert.pem -crl_reason keyCompromise

# Generate updated CRL
openssl ca -config ca.cnf -gencrl -out ca-crl.pem

# Vault PKI revocation
vault write pki_int/revoke serial_number="39:dd:2e:..."

# Vault tidy (clean up revoked certs)
vault write pki_int/tidy tidy_cert_store=true tidy_revoked_certs=true
```

### 8.6 Crypto Agility and Post-Quantum Readiness

**The Quantum Threat:**
- Shor's algorithm breaks RSA, ECDSA, EdDSA (all current public-key crypto).
- Grover's algorithm halves symmetric key strength (AES-256 → 128-bit effective).
- Timeline: NIST estimates cryptographically relevant quantum computers by 2030-2035.
- "Harvest now, decrypt later": adversaries may be collecting encrypted traffic TODAY for future decryption.

**NIST Post-Quantum Standards (FIPS 203, 204, 205 — finalized 2024):**

| Standard | Algorithm | Type | Use |
|----------|-----------|------|-----|
| FIPS 203 | ML-KEM (CRYSTALS-Kyber) | KEM (key encapsulation) | Key exchange in TLS |
| FIPS 204 | ML-DSA (CRYSTALS-Dilithium) | Signature | Certificate signing, code signing |
| FIPS 205 | SLH-DSA (SPHINCS+) | Signature (hash-based, stateless) | Long-lived signatures (backup) |

**Hybrid Approach (Recommended for Transition):**
- Combine classical + PQ algorithms. If either is broken, the other provides security.
- TLS: hybrid key exchange (X25519 + ML-KEM-768). Chrome/Cloudflare already deploying.
- Certificates: dual-signed or composite certificates (draft-ounsworth-pq-composite-sigs).

**Preparation Steps:**

1. **Inventory**: Catalog all cryptographic algorithms in use (certificates, VPNs, key exchange, signatures).
2. **Risk Assessment**: Identify systems with long data lifetimes ("harvest now, decrypt later" risk).
3. **Testing**: Deploy PQ hybrid in non-production environments.
4. **Vendor Readiness**: Verify HSMs, CAs, and TLS libraries support PQ algorithms.
5. **Migration Plan**: Phased rollout starting with highest-risk data paths.

---

## 9. Compliance e Audit

### 9.1 CA/Browser Forum Baseline Requirements

The CA/Browser Forum sets policy for publicly trusted CAs. Key requirements (v2.0+):

- **Certificate Lifetime**: Maximum 398 days (Apple: moving to 47 days by 2028).
- **Key Size**: RSA >= 2048 bit, ECDSA >= P-256.
- **Serial Number**: At least 64 bits of entropy.
- **Subject**: CN deprecated for TLS; SAN is authoritative.
- **Validation**: DV/OV/EV with specified methods. Multi-perspective validation required.
- **CT Logging**: All certificates must be logged to at least 2 CT logs.
- **OCSP**: CA must operate OCSP responder. Response validity <= 10 days.
- **CRL**: Must publish. Update within 24h of revocation for compromise.
- **CAA**: CAs must check CAA records before issuance.
- **Key Protection**: CA keys on FIPS 140-2 Level 3+ HSM.
- **Audit**: Annual WebTrust or ETSI audit.

### 9.2 WebTrust/ETSI Audits

**WebTrust for CAs:**
- Based on AICPA Trust Services Criteria.
- Covers: CA business practices, CA environmental controls, CA key lifecycle management, certificate lifecycle management, subordinate CA management.
- Audit by licensed WebTrust practitioner (CPA firm).
- Annual engagement, seal displayed on CA website.

**ETSI EN 319 411 (European):**
- Qualified Trust Service Providers (QTSP) under eIDAS regulation.
- EN 319 411-1: non-qualified certificates.
- EN 319 411-2: qualified certificates (legal equivalence to handwritten signature in EU).
- Conformity assessment by accredited body.

### 9.3 PCI-DSS Certificate Requirements

PCI-DSS v4.0 requirements relevant to certificates:

- **Requirement 2.2.7**: Only necessary services, protocols, daemons — TLS 1.2+ only, no SSL/early TLS.
- **Requirement 4.2.1**: Strong cryptography for transmission of cardholder data. TLS 1.2+ with PFS.
- **Requirement 4.2.1.1**: Maintain inventory of trusted keys and certificates.
- **Requirement 4.2.2**: PAN secured with strong cryptography whenever sent via end-user messaging technologies.
- **Requirement 8.3.2**: Strong authentication for all admin access — mTLS satisfies this where applicable.

### 9.4 NIST SP 800-57 Key Management

NIST Special Publication 800-57 (Recommendation for Key Management) defines:

**Key States:**
- Pre-activation → Active → Deactivated → Compromised → Destroyed

**Key Usage Periods (Cryptoperiods):**

| Key Type | Originator Usage | Recipient Usage |
|----------|-----------------|-----------------|
| Symmetric (encryption) | <= 2 years | Past data: indefinite |
| Asymmetric (signing) | 1-3 years | Verification: indefinite |
| Asymmetric (key transport) | <= 2 years | Decryption: indefinite |
| CA signing key | Depends on hierarchy level | Certificate chain validity |

**Algorithm Transition Guidance (SP 800-131A rev2):**

| Algorithm | Status | Disallowed After |
|-----------|--------|-----------------|
| RSA < 2048 | Disallowed | Already |
| SHA-1 (signing) | Disallowed | Already |
| 3DES (2-key) | Disallowed | Already |
| 3DES (3-key) | Deprecated | 2023 |
| RSA 2048 | Acceptable | ~2030 |
| RSA 3072+ | Acceptable | Until PQ transition |
| ECDSA P-256+ | Acceptable | Until PQ transition |

### 9.5 Key Length Requirements by Standard

| Standard/Framework | RSA Min | ECDSA Min | Hash Min | TLS Min |
|-------------------|---------|-----------|----------|---------|
| CA/B Forum (public TLS) | 2048 | P-256 | SHA-256 | 1.2 |
| PCI-DSS v4.0 | 2048 | P-256 | SHA-256 | 1.2 |
| NIST SP 800-57 (>=2030) | 3072 | P-256 | SHA-256 | 1.2 |
| BSI (Germany) | 3000 | P-256 | SHA-256 | 1.2 |
| ANSSI (France) | 3072 | P-256 | SHA-256 | 1.3 pref |
| SOX (via PCI) | 2048 | P-256 | SHA-256 | 1.2 |
| HIPAA (via NIST) | 2048 | P-256 | SHA-256 | 1.2 |

### 9.6 Certificate Logging and Audit Trails

**What to Log:**
- All certificate issuance events (who requested, what was issued, timestamp).
- All revocation events (who requested, reason, timestamp).
- CA key usage events (HSM audit log).
- CRL/OCSP publication events.
- Administrative actions on CA (template changes, permission changes).
- Failed enrollment attempts.
- Certificate lifecycle state changes.

**AD CS Audit Configuration:**

```powershell
# Enable CA auditing (all events)
certutil -setreg CA\AuditFilter 127

# Events logged to Windows Security Event Log:
# Event ID 4886: Certificate Services received a certificate request
# Event ID 4887: Certificate Services approved a certificate request
# Event ID 4888: Certificate Services denied a certificate request
# Event ID 4889: Certificate Services set the status of a certificate request to pending
# Event ID 4890: Certificate Manager settings for Certificate Services changed
# Event ID 4891: A configuration entry changed in Certificate Services
# Event ID 4892: A property of Certificate Services changed
# Event ID 4893: Certificate Services archived a key
# Event ID 4894: Certificate Services imported and archived a key
# Event ID 4895: Certificate Services published the CA certificate
# Event ID 4896: One or more rows have been deleted from the certificate database
# Event ID 4897: Role separation enabled
```

**Vault PKI Audit:**

```bash
# Enable audit logging
vault audit enable file file_path=/var/log/vault/audit.log

# All PKI operations are logged:
# - Secret reads (certificate issuance)
# - Secret writes (role configuration)
# - Auth events (who authenticated)
# Includes: timestamp, client IP, path, operation, auth metadata
```

---

## 10. Laboratorio Pratico

### 10.1 Build Complete PKI Lab

**Architecture:**

```
┌──────────────────────────────────────────────────────────────────┐
│                    PKI LAB ARCHITECTURE                            │
│                                                                    │
│  ┌─────────────┐                                                  │
│  │  Root CA     │  (Offline — air-gapped VM, used only for        │
│  │  EC P-384    │   signing intermediate CA certs)                 │
│  └──────┬──────┘                                                  │
│         │ Signs                                                    │
│  ┌──────┴──────┐                                                  │
│  │Intermediate │  (Near-line — powered on for signing sessions)   │
│  │  CA EC P-384│                                                  │
│  └──────┬──────┘                                                  │
│         │ Signs                                                    │
│  ┌──────┴──────┐                                                  │
│  │ Issuing CA  │  (Online — Vault PKI or step-ca)                 │
│  │  EC P-256   │                                                  │
│  └──────┬──────┘                                                  │
│         │ Issues                                                   │
│  ┌──────┴────────────────────┐                                    │
│  │ End-Entity Certificates   │                                    │
│  │ - TLS Server certs        │                                    │
│  │ - mTLS Client certs       │                                    │
│  │ - Code signing certs      │                                    │
│  └───────────────────────────┘                                    │
└──────────────────────────────────────────────────────────────────┘
```

**Step 1: Root CA (OpenSSL — Offline Machine)**

```bash
# Create directory structure
mkdir -p ~/pki-lab/{root-ca,intermediate-ca,issuing-ca}/{certs,crl,newcerts,private,csr}
chmod 700 ~/pki-lab/root-ca/private ~/pki-lab/intermediate-ca/private

# Initialize serial and index
echo 1000 > ~/pki-lab/root-ca/serial
touch ~/pki-lab/root-ca/index.txt
echo 1000 > ~/pki-lab/root-ca/crlnumber

# Root CA OpenSSL config
cat > ~/pki-lab/root-ca/openssl.cnf <<'EOF'
[ca]
default_ca = CA_default

[CA_default]
dir               = /root/pki-lab/root-ca
certs             = $dir/certs
crl_dir           = $dir/crl
new_certs_dir     = $dir/newcerts
database          = $dir/index.txt
serial            = $dir/serial
RANDFILE          = $dir/private/.rand
private_key       = $dir/private/root-ca.key.pem
certificate       = $dir/certs/root-ca.cert.pem
crlnumber         = $dir/crlnumber
crl               = $dir/crl/root-ca.crl.pem
crl_extensions    = crl_ext
default_crl_days  = 180
default_md        = sha384
name_opt          = ca_default
cert_opt          = ca_default
default_days      = 3650
preserve          = no
policy            = policy_strict

[policy_strict]
countryName             = match
stateOrProvinceName     = match
organizationName        = match
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional

[req]
default_bits        = 384
distinguished_name  = req_distinguished_name
string_mask         = utf8only
default_md          = sha384
x509_extensions     = v3_ca

[req_distinguished_name]
countryName                     = Country Name (2 letter code)
stateOrProvinceName             = State or Province Name
localityName                    = Locality Name
organizationName                = Organization Name
commonName                      = Common Name

[v3_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign

[v3_intermediate_ca]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true, pathlen:1
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
nameConstraints = critical, @name_constraints

[name_constraints]
permitted;DNS.0 = acme.it
permitted;DNS.1 = acme.internal
permitted;IP.0 = 10.0.0.0/255.0.0.0
permitted;IP.1 = 172.16.0.0/255.240.0.0
permitted;IP.2 = 192.168.0.0/255.255.0.0

[crl_ext]
authorityKeyIdentifier = keyid:always
EOF

# Generate Root CA key (EC P-384)
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:secp384r1 \
  -aes256 -out ~/pki-lab/root-ca/private/root-ca.key.pem
chmod 400 ~/pki-lab/root-ca/private/root-ca.key.pem

# Generate Root CA self-signed certificate (20 years)
openssl req -config ~/pki-lab/root-ca/openssl.cnf \
  -key ~/pki-lab/root-ca/private/root-ca.key.pem \
  -new -x509 -days 7300 -sha384 \
  -extensions v3_ca \
  -out ~/pki-lab/root-ca/certs/root-ca.cert.pem \
  -subj "/C=IT/ST=Lombardia/L=Milano/O=Acme SpA/CN=Acme Root CA 2026"

# Verify root certificate
openssl x509 -in ~/pki-lab/root-ca/certs/root-ca.cert.pem -text -noout
```

**Step 2: Intermediate CA**

```bash
# Initialize intermediate
echo 2000 > ~/pki-lab/intermediate-ca/serial
touch ~/pki-lab/intermediate-ca/index.txt
echo 2000 > ~/pki-lab/intermediate-ca/crlnumber

# Generate intermediate key
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:secp384r1 \
  -aes256 -out ~/pki-lab/intermediate-ca/private/intermediate-ca.key.pem
chmod 400 ~/pki-lab/intermediate-ca/private/intermediate-ca.key.pem

# Generate CSR
openssl req -config ~/pki-lab/root-ca/openssl.cnf \
  -key ~/pki-lab/intermediate-ca/private/intermediate-ca.key.pem \
  -new -sha384 \
  -out ~/pki-lab/intermediate-ca/csr/intermediate-ca.csr.pem \
  -subj "/C=IT/ST=Lombardia/L=Milano/O=Acme SpA/CN=Acme Intermediate CA G2"

# Sign intermediate with root (10 years, with Name Constraints)
openssl ca -config ~/pki-lab/root-ca/openssl.cnf \
  -extensions v3_intermediate_ca \
  -days 3650 -notext -md sha384 \
  -in ~/pki-lab/intermediate-ca/csr/intermediate-ca.csr.pem \
  -out ~/pki-lab/intermediate-ca/certs/intermediate-ca.cert.pem

# Create chain file
cat ~/pki-lab/intermediate-ca/certs/intermediate-ca.cert.pem \
    ~/pki-lab/root-ca/certs/root-ca.cert.pem > \
    ~/pki-lab/intermediate-ca/certs/ca-chain.cert.pem

# Verify chain
openssl verify -CAfile ~/pki-lab/root-ca/certs/root-ca.cert.pem \
  ~/pki-lab/intermediate-ca/certs/intermediate-ca.cert.pem
```

**Step 3: Issuing CA (Vault PKI)**

```bash
# Start Vault in dev mode for lab (production: use proper storage backend)
vault server -dev -dev-root-token-id="lab-token" &

export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='lab-token'

# Enable PKI for issuing CA
vault secrets enable -path=pki_issuing pki
vault secrets tune -max-lease-ttl=26280h pki_issuing  # 3 years

# Generate issuing CA key and CSR
vault write -format=json pki_issuing/intermediate/generate/internal \
  common_name="Acme Issuing CA - TLS Services" \
  key_type="ec" \
  key_bits=256 | jq -r '.data.csr' > ~/pki-lab/issuing-ca/csr/issuing-ca.csr

# Sign with intermediate CA (using OpenSSL)
# (In production, sign with the intermediate CA's key via its own tool)
openssl ca -config ~/pki-lab/intermediate-ca/openssl.cnf \
  -extensions v3_issuing_ca \
  -days 1825 -notext -md sha256 \
  -in ~/pki-lab/issuing-ca/csr/issuing-ca.csr \
  -out ~/pki-lab/issuing-ca/certs/issuing-ca.cert.pem

# Create full chain (issuing + intermediate + root)
cat ~/pki-lab/issuing-ca/certs/issuing-ca.cert.pem \
    ~/pki-lab/intermediate-ca/certs/intermediate-ca.cert.pem \
    ~/pki-lab/root-ca/certs/root-ca.cert.pem > \
    ~/pki-lab/issuing-ca/certs/fullchain.pem

# Import signed certificate into Vault
vault write pki_issuing/intermediate/set-signed \
  certificate=@~/pki-lab/issuing-ca/certs/fullchain.pem

# Configure issuing CA roles
vault write pki_issuing/roles/tls-server \
  allowed_domains="acme.it,acme.internal" \
  allow_subdomains=true \
  max_ttl=2160h \
  ttl=720h \
  key_type=ec \
  key_bits=256 \
  require_cn=false \
  organization="Acme SpA" \
  country="IT"

vault write pki_issuing/roles/mtls-client \
  allowed_domains="acme.internal" \
  allow_subdomains=true \
  max_ttl=24h \
  ttl=1h \
  key_type=ec \
  key_bits=256 \
  ext_key_usage=ClientAuth \
  no_store=true

# Test: Issue a certificate
vault write -format=json pki_issuing/issue/tls-server \
  common_name="lab-api.acme.internal" \
  alt_names="lab-api-v2.acme.internal" \
  ttl=720h | jq .
```

### 10.2 Configure Auto-Enrollment

**AD CS Auto-Enrollment via Group Policy:**

```powershell
# Step 1: Create certificate template for workstations
# (Duplicate "Computer" template in certtmpl.msc)

# Step 2: Configure template permissions
# Grant "Domain Computers" group: Read + Enroll + Autoenroll

# Step 3: Publish template to CA
Add-CATemplate -Name "AutoEnroll-Workstation"

# Step 4: Configure GPO
# Computer Configuration > Policies > Windows Settings >
# Security Settings > Public Key Policies >
# Certificate Services Client - Auto-Enrollment
# - Configuration Model: Enabled
# - [x] Renew expired certificates, update pending certificates, and remove revoked certificates
# - [x] Update certificates that use certificate templates

# Step 5: Force policy update on test machine
gpupdate /force

# Step 6: Verify enrollment
certutil -pulse
Get-ChildItem Cert:\LocalMachine\My | Format-List Subject, NotAfter, Issuer
```

**cert-manager Auto-Enrollment (Kubernetes):**

```yaml
# Automatic certificate for every Ingress with annotation
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: internal-ca
spec:
  vault:
    path: pki_issuing/sign/tls-server
    server: https://vault.acme.internal:8200
    auth:
      kubernetes:
        role: cert-manager
        mountPath: /v1/auth/kubernetes
        serviceAccountRef:
          name: cert-manager
---
# Default issuer for namespace (via annotation or policy)
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: wildcard-internal
  namespace: production
spec:
  secretName: wildcard-internal-tls
  issuerRef:
    name: internal-ca
    kind: ClusterIssuer
  dnsNames:
  - "*.production.acme.internal"
  duration: 720h
  renewBefore: 240h
  privateKey:
    algorithm: ECDSA
    size: 256
    rotationPolicy: Always
```

### 10.3 Deploy mTLS Between Services

**Scenario**: Service A (api-gateway) calls Service B (order-service) over mTLS.

```bash
# Issue server cert for order-service
vault write -format=json pki_issuing/issue/tls-server \
  common_name="order-service.production.acme.internal" \
  ttl=720h > /tmp/order-service-cert.json

jq -r '.data.certificate' /tmp/order-service-cert.json > /etc/ssl/order-service/cert.pem
jq -r '.data.private_key' /tmp/order-service-cert.json > /etc/ssl/order-service/key.pem
jq -r '.data.ca_chain[]' /tmp/order-service-cert.json > /etc/ssl/order-service/ca-chain.pem

# Issue client cert for api-gateway
vault write -format=json pki_issuing/issue/mtls-client \
  common_name="api-gateway.production.acme.internal" \
  ttl=1h > /tmp/api-gateway-client-cert.json

jq -r '.data.certificate' /tmp/api-gateway-client-cert.json > /etc/ssl/api-gateway/client-cert.pem
jq -r '.data.private_key' /tmp/api-gateway-client-cert.json > /etc/ssl/api-gateway/client-key.pem
```

**order-service nginx config (server-side mTLS):**

```nginx
server {
    listen 8443 ssl;
    server_name order-service.production.acme.internal;

    ssl_certificate     /etc/ssl/order-service/cert.pem;
    ssl_certificate_key /etc/ssl/order-service/key.pem;
    ssl_protocols       TLSv1.3;

    # Require client certificate
    ssl_client_certificate /etc/ssl/order-service/ca-chain.pem;
    ssl_verify_client on;
    ssl_verify_depth 3;

    location / {
        # Only allow api-gateway's identity
        if ($ssl_client_s_dn !~ "CN=api-gateway") {
            return 403;
        }
        proxy_pass http://127.0.0.1:8080;
    }
}
```

**api-gateway calling order-service (client-side mTLS):**

```bash
# Test with curl
curl --cert /etc/ssl/api-gateway/client-cert.pem \
     --key /etc/ssl/api-gateway/client-key.pem \
     --cacert /etc/ssl/order-service/ca-chain.pem \
     https://order-service.production.acme.internal:8443/api/orders
```

### 10.4 Test Certificate Attacks with mitmproxy/Burp

**mitmproxy — Intercept and Inspect TLS Traffic:**

```bash
# Start mitmproxy with custom CA (lab environment)
mitmproxy --mode transparent --set ssl_insecure=true

# For specific upstream with custom cert
mitmproxy --mode reverse:https://order-service:8443 \
  --set ssl_insecure=true \
  --set client_certs=/path/to/client-cert.pem

# Export mitmproxy CA cert for import into test client trust store
cat ~/.mitmproxy/mitmproxy-ca-cert.pem
```

**Burp Suite — TLS Interception:**

```
1. Import Burp CA cert into browser/client trust store
2. Configure proxy: 127.0.0.1:8080
3. In Burp: Proxy > Options > TLS Pass Through (add exceptions for non-target hosts)
4. For mTLS targets: Project Options > TLS > Client TLS Certificates
   - Add destination host
   - Import client cert + key (PKCS#12)
5. Monitor: Proxy > HTTP History for decrypted traffic
```

**Testing Certificate Validation Weaknesses:**

```bash
# Test 1: Self-signed cert (should be rejected by properly configured clients)
openssl req -x509 -newkey ec:<(openssl ecparam -name prime256v1) -nodes \
  -keyout selfsigned.key -out selfsigned.crt -days 1 \
  -subj "/CN=order-service.production.acme.internal"

# Test 2: Expired certificate
openssl req -x509 -newkey ec:<(openssl ecparam -name prime256v1) -nodes \
  -keyout expired.key -out expired.crt -days 0 \
  -subj "/CN=order-service.production.acme.internal"

# Test 3: Wrong hostname (valid cert, wrong SAN)
# Use cert issued for different-service.acme.internal against order-service

# Test 4: Revoked certificate
# Issue cert, revoke it, attempt connection with revoked cert

# Test 5: Client that does not verify (should be flagged as vulnerability)
curl -k https://order-service:8443/api/orders  # -k skips verification
# If this works in production code: CRITICAL finding
```

### 10.5 Implement CT Monitoring

```bash
#!/bin/bash
# ct-monitor.sh — Continuous CT Log Monitoring
# Run as cron job every hour or as systemd timer

set -euo pipefail

DOMAINS=("acme.it" "acme.internal")
APPROVED_ISSUERS=("Let's Encrypt" "Acme Issuing CA" "DigiCert")
STATE_DIR="/var/lib/ct-monitor"
ALERT_WEBHOOK="https://hooks.slack.com/services/XXX/YYY/ZZZ"

mkdir -p "$STATE_DIR"

for domain in "${DOMAINS[@]}"; do
  state_file="${STATE_DIR}/${domain}.last_id"
  last_id=$(cat "$state_file" 2>/dev/null || echo "0")

  # Query crt.sh for new certificates
  new_certs=$(curl -sf "https://crt.sh/?q=%25.${domain}&output=json" | \
    python3 -c "
import sys, json
certs = json.load(sys.stdin)
last_id = int(sys.argv[1])
for c in sorted(certs, key=lambda x: x['id']):
    if c['id'] > last_id:
        print(f\"{c['id']}|{c['common_name']}|{c['issuer_name']}|{c['not_before']}\")
" "$last_id" 2>/dev/null || true)

  while IFS='|' read -r cert_id cn issuer not_before; do
    [ -z "$cert_id" ] && continue

    # Check if issuer is approved
    approved=false
    for approved_issuer in "${APPROVED_ISSUERS[@]}"; do
      if echo "$issuer" | grep -qi "$approved_issuer"; then
        approved=true
        break
      fi
    done

    if [ "$approved" = false ]; then
      # ALERT: Unauthorized certificate detected
      payload=$(cat <<ALERTEOF
{
  "text": ":rotating_light: *UNAUTHORIZED CERTIFICATE DETECTED*",
  "attachments": [{
    "color": "danger",
    "fields": [
      {"title": "Domain", "value": "${cn}", "short": true},
      {"title": "Issuer", "value": "${issuer}", "short": true},
      {"title": "Not Before", "value": "${not_before}", "short": true},
      {"title": "crt.sh ID", "value": "${cert_id}", "short": true}
    ]
  }]
}
ALERTEOF
      )
      curl -sf -X POST -H "Content-Type: application/json" \
        -d "$payload" "$ALERT_WEBHOOK"
    fi

    # Update state
    echo "$cert_id" > "$state_file"
  done <<< "$new_certs"
done
```

### 10.6 Automate with Vault PKI — Full Pipeline

**Terraform Configuration for Vault PKI:**

```hcl
# terraform/vault-pki/main.tf

terraform {
  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = "~> 4.0"
    }
  }
}

provider "vault" {
  address = "https://vault.acme.internal:8200"
}

# Root CA
resource "vault_mount" "pki_root" {
  path                  = "pki"
  type                  = "pki"
  max_lease_ttl_seconds = 315360000  # 10 years
  description           = "Root CA"
}

resource "vault_pki_secret_backend_root_cert" "root" {
  backend              = vault_mount.pki_root.path
  type                 = "internal"
  common_name          = "Acme Root CA 2026"
  ttl                  = "315360000"
  key_type             = "ec"
  key_bits             = 384
  organization         = "Acme SpA"
  country              = "IT"
  province             = "Lombardia"
  locality             = "Milano"
  exclude_cn_from_sans = true
  issuer_name          = "acme-root-2026"
}

resource "vault_pki_secret_backend_config_urls" "root_urls" {
  backend                 = vault_mount.pki_root.path
  issuing_certificates    = ["https://vault.acme.internal:8200/v1/pki/ca"]
  crl_distribution_points = ["https://vault.acme.internal:8200/v1/pki/crl"]
  ocsp_servers            = ["https://vault.acme.internal:8200/v1/pki/ocsp"]
}

# Intermediate CA
resource "vault_mount" "pki_int" {
  path                  = "pki_int"
  type                  = "pki"
  max_lease_ttl_seconds = 157680000  # 5 years
  description           = "Intermediate CA"
}

resource "vault_pki_secret_backend_intermediate_cert_request" "int_csr" {
  backend     = vault_mount.pki_int.path
  type        = "internal"
  common_name = "Acme Issuing CA G2"
  key_type    = "ec"
  key_bits    = 256
}

resource "vault_pki_secret_backend_root_sign_intermediate" "int_signed" {
  backend              = vault_mount.pki_root.path
  csr                  = vault_pki_secret_backend_intermediate_cert_request.int_csr.csr
  common_name          = "Acme Issuing CA G2"
  ttl                  = "157680000"
  exclude_cn_from_sans = true
  organization         = "Acme SpA"
  country              = "IT"
}

resource "vault_pki_secret_backend_intermediate_set_signed" "int_cert" {
  backend     = vault_mount.pki_int.path
  certificate = vault_pki_secret_backend_root_sign_intermediate.int_signed.certificate
}

# Roles
resource "vault_pki_secret_backend_role" "tls_server" {
  backend          = vault_mount.pki_int.path
  name             = "tls-server"
  allowed_domains  = ["acme.it", "acme.internal"]
  allow_subdomains = true
  max_ttl          = "7776000"   # 90 days
  ttl              = "2592000"   # 30 days
  key_type         = "ec"
  key_bits         = 256
  key_usage        = ["DigitalSignature", "KeyEncipherment"]
  ext_key_usage    = ["ServerAuth"]
  organization     = ["Acme SpA"]
  country          = ["IT"]
  no_store         = true
}

resource "vault_pki_secret_backend_role" "mtls_client" {
  backend          = vault_mount.pki_int.path
  name             = "mtls-client"
  allowed_domains  = ["acme.internal"]
  allow_subdomains = true
  max_ttl          = "86400"    # 24h
  ttl              = "3600"     # 1h
  key_type         = "ec"
  key_bits         = 256
  key_usage        = ["DigitalSignature"]
  ext_key_usage    = ["ClientAuth"]
  no_store         = true
}

# Policy for cert-manager
resource "vault_policy" "cert_manager" {
  name = "cert-manager"
  policy = <<-EOT
    path "pki_int/sign/tls-server" {
      capabilities = ["create", "update"]
    }
    path "pki_int/sign/mtls-client" {
      capabilities = ["create", "update"]
    }
    path "pki_int/issue/tls-server" {
      capabilities = ["create"]
    }
    path "pki_int/issue/mtls-client" {
      capabilities = ["create"]
    }
  EOT
}
```

**CI/CD Pipeline — Certificate Issuance and Deployment:**

```yaml
# .github/workflows/deploy-with-cert.yml
name: Deploy with Certificate Rotation

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * 1'  # Weekly cert rotation

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # For Vault JWT auth
      contents: read

    steps:
    - uses: actions/checkout@v4

    - name: Authenticate to Vault
      uses: hashicorp/vault-action@v3
      with:
        url: https://vault.acme.internal:8200
        method: jwt
        role: ci-deployer
        jwtGithubAudience: vault.acme.internal
        secrets: |
          pki_int/issue/tls-server common_name="api.acme.it" alt_names="api-v2.acme.it" ttl="720h" | CERT ;
          pki_int/issue/tls-server common_name="api.acme.it" alt_names="api-v2.acme.it" ttl="720h" | KEY ;
          pki_int/issue/tls-server common_name="api.acme.it" alt_names="api-v2.acme.it" ttl="720h" | CA_CHAIN

    - name: Deploy certificate to target
      run: |
        echo "$CERT" | base64 -d > cert.pem
        echo "$KEY" | base64 -d > key.pem
        echo "$CA_CHAIN" | base64 -d > chain.pem
        # Deploy via ansible/kubectl/etc
        kubectl create secret tls api-tls \
          --cert=cert.pem --key=key.pem \
          --namespace=production --dry-run=client -o yaml | \
          kubectl apply -f -

    - name: Verify deployment
      run: |
        sleep 10
        openssl s_client -connect api.acme.it:443 -servername api.acme.it \
          </dev/null 2>/dev/null | openssl x509 -noout -dates -subject
```

---

## Appendice A — Quick Reference Commands

### OpenSSL One-Liners

```bash
# Check certificate expiry of remote server
echo | openssl s_client -servername HOST -connect HOST:443 2>/dev/null | \
  openssl x509 -noout -dates

# Check certificate SANs
openssl x509 -in cert.pem -noout -ext subjectAltName

# Convert PEM to PKCS#12
openssl pkcs12 -export -in cert.pem -inkey key.pem -certfile chain.pem -out bundle.p12

# Convert PKCS#12 to PEM
openssl pkcs12 -in bundle.p12 -out all.pem -nodes

# Check if key matches certificate
diff <(openssl x509 -in cert.pem -noout -modulus | openssl md5) \
     <(openssl pkey -in key.pem -noout -modulus 2>/dev/null | openssl md5 || \
       openssl rsa -in key.pem -noout -modulus | openssl md5)

# Generate DH parameters
openssl dhparam -out dhparam.pem 4096

# Check TLS connection with specific protocol/cipher
openssl s_client -connect HOST:443 -tls1_3 -ciphersuites TLS_AES_256_GCM_SHA384

# View certificate chain from server
openssl s_client -connect HOST:443 -showcerts </dev/null 2>/dev/null

# Check OCSP stapling from server
openssl s_client -connect HOST:443 -status </dev/null 2>/dev/null | grep -A5 "OCSP"

# Generate random serial (for CSR/cert)
openssl rand -hex 16

# Verify certificate against CA bundle
openssl verify -CAfile ca-bundle.pem -untrusted intermediate.pem end-entity.pem
```

### Vault PKI Quick Reference

```bash
# List all roles
vault list pki_int/roles

# Read role configuration
vault read pki_int/roles/tls-server

# Issue certificate
vault write pki_int/issue/tls-server common_name="app.acme.it" ttl=720h

# List certificates (if store enabled)
vault list pki_int/certs

# Revoke by serial
vault write pki_int/revoke serial_number="xx:yy:zz:..."

# Tidy certificate store
vault write pki_int/tidy tidy_cert_store=true tidy_revoked_certs=true safety_buffer=72h

# Rotate intermediate CA
vault write pki_int/intermediate/generate/internal common_name="New Issuing CA" ...
# (then sign with root and set-signed)

# Read CA certificate
vault read -field=certificate pki_int/cert/ca

# Read CRL
vault read -field=crl pki_int/crl/rotate
```

---

## Appendice B — Troubleshooting Matrix

| Symptom | Likely Cause | Diagnostic | Fix |
|---------|-------------|-----------|-----|
| `certificate has expired` | Renewal automation failed | `openssl x509 -enddate -noout -in cert.pem` | Renew immediately, fix automation |
| `unable to get local issuer certificate` | Incomplete chain served | `openssl s_client -showcerts` | Configure server to send full chain |
| `certificate verify failed` | CA not in trust store | Check trust store contents | Add CA to trust store |
| `SSL: CERTIFICATE_VERIFY_FAILED` (Python) | Missing CA bundle or self-signed | `python3 -c "import ssl; print(ssl.get_default_verify_paths())"` | Set `SSL_CERT_FILE` or install CA |
| `OCSP response not valid` | Stale stapled response | Check OCSP responder URL, resolver config | Verify resolver accessible, force OCSP refresh |
| `handshake failure` | Protocol/cipher mismatch | `testssl.sh --protocols --ciphers HOST` | Align client/server TLS configuration |
| `no suitable key share` | TLS 1.3 curve mismatch | Check `ssl_ecdh_curve` | Add required curves to configuration |
| `client certificate required` | Missing or wrong client cert | Check client cert DN against server ACL | Provide correct client certificate |
| `certificate name mismatch` | SAN does not include hostname | `openssl x509 -noout -ext subjectAltName -in cert.pem` | Re-issue with correct SAN |
| HSTS blocks HTTP | Premature preload or includeSubDomains | Check browser HSTS cache | Wait for max-age expiry or clear browser cache |
| CT SCT missing | Certificate not logged | `sslyze --certinfo HOST` | Re-issue via CA that logs to CT |

---

## Appendice C — Security Checklist

### Pre-Production TLS Deployment

- [ ] Certificate algorithm: ECDSA P-256+ or RSA 3072+
- [ ] TLS 1.2 minimum (TLS 1.3 preferred)
- [ ] Only AEAD ciphers enabled (GCM, ChaCha20-Poly1305)
- [ ] PFS enforced (ECDHE only, no static RSA key exchange)
- [ ] HSTS enabled with appropriate max-age
- [ ] OCSP stapling enabled and verified working
- [ ] Full chain served (intermediate + end-entity)
- [ ] Session tickets disabled (for PFS) or rotated frequently
- [ ] No RC4, DES, 3DES, EXPORT, NULL ciphers
- [ ] SSL Labs grade A or A+
- [ ] Certificate validity < 398 days
- [ ] SAN includes all required names (no reliance on CN)
- [ ] CAA DNS record published restricting allowed CAs
- [ ] Automated renewal configured and tested
- [ ] Expiry monitoring/alerting in place
- [ ] CT log monitoring for domain
- [ ] Private key protected (600 permissions, not in version control)
- [ ] DH parameters >= 2048 bit (if DHE is enabled)

### Internal PKI Deployment

- [ ] Root CA offline and HSM-protected
- [ ] Intermediate CA with Name Constraints
- [ ] Key ceremony documented and witnessed
- [ ] CRL publication automated and tested
- [ ] OCSP responder available (if needed)
- [ ] Certificate templates/roles follow least privilege
- [ ] Auto-enrollment tested
- [ ] Revocation procedures documented and rehearsed
- [ ] Disaster recovery plan tested
- [ ] Audit logging enabled on all CA components
- [ ] Post-quantum migration plan documented
- [ ] Certificate inventory current and complete

---

## Riferimenti

- RFC 5280 — Internet X.509 PKI Certificate and CRL Profile
- RFC 6960 — Online Certificate Status Protocol (OCSP)
- RFC 6962 — Certificate Transparency
- RFC 8446 — The Transport Layer Security (TLS) Protocol Version 1.3
- RFC 8555 — Automatic Certificate Management Environment (ACME)
- RFC 6797 — HTTP Strict Transport Security (HSTS)
- RFC 6698 — DNS-Based Authentication of Named Entities (DANE)
- RFC 7469 — Public Key Pinning Extension for HTTP (deprecated)
- NIST SP 800-57 — Recommendation for Key Management
- NIST SP 800-131A — Transitioning the Use of Cryptographic Algorithms
- FIPS 203/204/205 — Post-Quantum Cryptography Standards (2024)
- CA/Browser Forum Baseline Requirements v2.0
- SPIFFE specification — spiffe.io
- HashiCorp Vault PKI documentation — developer.hashicorp.com
- cert-manager documentation — cert-manager.io
- Smallstep step-ca documentation — smallstep.com/docs
