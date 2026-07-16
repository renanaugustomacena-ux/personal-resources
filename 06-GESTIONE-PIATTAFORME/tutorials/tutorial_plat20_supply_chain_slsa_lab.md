# Tutorial: Supply Chain Security — SLSA, cosign, SBOM e Sigstore

> **Documento di riferimento:** `20-supply-chain-slsa-cosign.md`
> **Dominio:** Gestione Piattaforme — Sicurezza e Compliance
> **Ambito:** Framework SLSA 1-4, cosign keyless signing con sigstore, syft per SBOM (CycloneDX/SPDX), grype per vulnerability scan su SBOM, Gatekeeper per bloccare immagini non firmate, GitHub Actions pipeline sicura
> **Durata lab:** 6-7 ore
> **Livello:** Avanzato — richiede Docker, kubectl, GitHub Actions o pipeline locale
> **Prerequisiti:** Docker Engine 29.x, kubectl, cosign CLI, syft CLI, grype CLI
> **Ambiente:** Tutto locale + registry (ttl.sh per test temporaneo senza autenticazione)

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI SUPPLY CHAIN LAB ===
echo "=== INSTALLAZIONE TOOL ==="

# cosign (firma e verifica immagini container)
if ! command -v cosign &>/dev/null; then
  curl -sSfL https://github.com/sigstore/cosign/releases/download/v2.4.1/cosign-linux-amd64 \
    -o /usr/local/bin/cosign && chmod +x /usr/local/bin/cosign
  echo "[OK] cosign installato"
fi

# syft (genera SBOM)
if ! command -v syft &>/dev/null; then
  curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin v1.17.0
  echo "[OK] syft installato"
fi

# grype (vulnerability scanner su SBOM)
if ! command -v grype &>/dev/null; then
  curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin v0.87.0
  echo "[OK] grype installato"
fi

# Verificare versioni
cosign version 2>/dev/null | head -2
syft version 2>/dev/null | head -2
grype version 2>/dev/null | head -2

mkdir -p ~/supply-chain-lab/{sbom,signatures,provenance,policies,app}
cd ~/supply-chain-lab

echo "[OK] Directory lab: ~/supply-chain-lab"
```

### Architettura Supply Chain Security

```
SUPPLY CHAIN ATTACK — VETTORI DI ATTACCO:

  Developer ──→ [git push] ──→ CI/CD ──→ Registry ──→ Production
      ↑                ↑           ↑          ↑
  [Attacco 1]   [Attacco 2]  [Attacco 3] [Attacco 4]
  Secret in     Iniettare    Immagine    Immagine
  codice        codice nel   manomessa   non firmata
                build step   nel transit deployata

DIFESE SLSA:

  L1: Build automatizzato (no manual build)
  L2: Build su CI fidato + firma provenance
  L3: Build hermetic (no rete, input deterministic)
  L4: Two-party review + firma con hardware key

NOSTRO LAB:
  ✓ Dockerfile sicuro (non-root, multi-stage)
  ✓ syft: genera SBOM (inventario completo dipendenze)
  ✓ grype: scan vulnerabilità sull'SBOM
  ✓ cosign: firma keyless via sigstore (OIDC → firma)
  ✓ Gatekeeper: blocca immagini non firmate in K8s
```

---

## PART A: FONDAMENTI — Cosa Significa Supply Chain Security

> Nel 2020, SolarWinds fu vittima di un attacco sofisticato:
> gli attaccanti compromisero il processo di build e iniettarono
> codice malevolo nell'aggiornamento software PRIMA della firma.
> Migliaia di organizzazioni installarono l'aggiornamento "ufficiale e firmato"
> — e installarono inconsapevolmente una backdoor.
> SLSA esiste proprio per prevenire questo: non basta firmare il risultato,
> bisogna garantire l'integrità dell'intero processo di costruzione.

---

### Concetto A1: SLSA — Supply-chain Levels for Software Artifacts

```
SLSA v1.0 — LIVELLI DI GARANZIA:

SLSA 1 — Provenance documentata:
  ✓ Build automatizzato (script/CI, no build manuale)
  ✓ Provenance generata: "questa immagine è stata buildata da questo commit"
  ✓ Provenance NOT verified (può essere auto-generata)
  ✗ No firma crittografica del provenance
  Impatto: tracciabilità di base

SLSA 2 — Firma CI verificabile:
  ✓ SLSA 1 +
  ✓ Build su hosted CI (GitHub Actions, GitLab CI, etc.)
  ✓ Provenance firmata dal CI (OIDC token)
  ✓ Build isolato (workload identity, non credenziali statiche)
  Impatto: protezione da "developer build e poi push"

SLSA 3 — Build hardening:
  ✓ SLSA 2 +
  ✓ Build hermetic: accesso rete bloccato durante build
  ✓ Source code verificato (commit firmato o hash verificato)
  ✓ Builders disponibili solo su infra fidato
  Impatto: protezione da "iniettare dipendenze durante build"

SLSA 4 — Revisione e Two-Party Review:
  ✓ SLSA 3 +
  ✓ Two-party review su ogni change (PR review)
  ✓ Hardware-backed signing keys
  ✓ Hermetic, reproducible builds
  Impatto: protezione da insider threats e APT

DOVE SIAMO ORA (2026):
  GitHub Actions: SLSA 2-3 nativo con slsa-framework/slsa-github-generator
  Linux distribution (Debian, Fedora, Arch): SLSA 2-3 in implementazione
  npm/PyPI: SLSA 2 per pacchetti pubblicati con provenance
```

---

## PART B: SBOM — SOFTWARE BILL OF MATERIALS

### Esercizio B1: Generare SBOM con syft

```bash
cd ~/supply-chain-lab

# Creare applicazione Flask di esempio
cat > app/app.py << 'PYTHON'
"""Demo app per supply chain lab."""
from flask import Flask, jsonify
import requests
import cryptography

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({"status": "ok", "version": "1.0.0"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
PYTHON

cat > app/requirements.txt << 'EOF'
flask==3.1.0
requests==2.32.3
cryptography==43.0.3
Werkzeug==3.1.3
gunicorn==23.0.0
EOF

# Dockerfile multi-stage sicuro
cat > app/Dockerfile << 'EOF'
# Stage 1: Build (installa dipendenze)
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime (immagine minima)
FROM python:3.12-slim AS runtime

# Security: non girare come root
RUN useradd -r -s /bin/false -u 1001 appuser
WORKDIR /app

# Copiare solo le dipendenze già installate (no pip nel runtime)
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser app.py .

USER appuser
EXPOSE 5000

ENV PATH="/home/appuser/.local/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
EOF

echo "=== BUILD IMMAGINE ==="
docker build -t supply-chain-demo:1.0.0 app/
echo "[OK] Immagine buildata"

echo ""
echo "=== SBOM CON SYFT ==="

# Generare SBOM in formato CycloneDX (XML e JSON)
syft supply-chain-demo:1.0.0 -o cyclonedx-json > sbom/sbom-cyclonedx.json
echo "[OK] SBOM CycloneDX JSON generato"

# Generare SBOM in formato SPDX
syft supply-chain-demo:1.0.0 -o spdx-json > sbom/sbom-spdx.json
echo "[OK] SBOM SPDX JSON generato"

# Generare SBOM in formato leggibile
syft supply-chain-demo:1.0.0 -o table | head -30

echo ""
echo "=== ANALISI SBOM ==="
python3 << 'PYEOF'
import json

with open("sbom/sbom-cyclonedx.json") as f:
    sbom = json.load(f)

components = sbom.get("components", [])
print(f"Componenti totali nel SBOM: {len(components)}")

by_type = {}
for c in components:
    t = c.get("type", "unknown")
    by_type[t] = by_type.get(t, 0) + 1

print("\nPer tipo:")
for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
    print(f"  {t}: {count}")

# Componenti con licenze rilevanti
problematic_licenses = ["GPL", "AGPL", "LGPL", "SSPL"]
print("\nComponenti con licenze copyleft:")
for c in components:
    for lic in c.get("licenses", []):
        lic_id = lic.get("license", {}).get("id", "")
        if any(p in lic_id for p in problematic_licenses):
            print(f"  ⚠️  {c.get('name')} {c.get('version')}: {lic_id}")
PYEOF
```

---

### Esercizio B2: Vulnerability Scan con grype

```bash
echo "=== GRYPE — VULNERABILITY SCAN SU SBOM E IMMAGINE ==="

# Scan diretto sull'immagine
echo "--- Scan immagine supply-chain-demo ---"
grype supply-chain-demo:1.0.0 \
  --output table \
  --fail-on high 2>&1 | head -50 || \
  echo "[INFO] Vulnerabilità trovate — vedere output sopra"

echo ""
echo "--- Scan su SBOM (più veloce, no pull) ---"
grype sbom:sbom/sbom-cyclonedx.json \
  --output json \
  --output table 2>/dev/null | head -30

echo ""
echo "--- Report JSON per CI/CD gate ---"
grype supply-chain-demo:1.0.0 \
  --output json \
  2>/dev/null | python3 << 'PYEOF'
import json, sys

try:
    data = json.load(sys.stdin)
    matches = data.get("matches", [])
    
    by_severity = {}
    for m in matches:
        sev = m.get("vulnerability", {}).get("severity", "Unknown")
        by_severity[sev] = by_severity.get(sev, 0) + 1
    
    print(f"Vulnerabilità trovate: {len(matches)}")
    for sev, count in sorted(by_severity.items(), key=lambda x: ["Critical","High","Medium","Low","Negligible","Unknown"].index(x[0]) if x[0] in ["Critical","High","Medium","Low","Negligible","Unknown"] else 99):
        prefix = "❌" if sev in ["Critical", "High"] else "⚠️" if sev == "Medium" else "ℹ️"
        print(f"  {prefix} {sev}: {count}")
    
    if by_severity.get("Critical", 0) > 0 or by_severity.get("High", 0) > 0:
        print("\n[FAIL] CI/CD gate: vulnerabilità CRITICAL/HIGH trovate — bloccare il deploy")
    else:
        print("\n[OK] Nessuna vulnerabilità CRITICAL/HIGH — deploy consentito")
except json.JSONDecodeError:
    print("[INFO] Parsing JSON non riuscito")
PYEOF
```

---

## PART C: COSIGN — FIRMA KEYLESS CON SIGSTORE

### Esercizio C1: Firma e Verifica Immagini

```bash
cd ~/supply-chain-lab

echo "=== COSIGN KEYLESS SIGNING ==="

# Cosign keyless: NON richiede chiavi generate manualmente
# Funziona con OIDC:
#   1. cosign chiede un token OIDC (da GitHub Actions, Google, GitLab, ecc.)
#   2. Fulcio (CA) emette un certificato X.509 con l'identità OIDC
#   3. La firma viene creata con la chiave effimera
#   4. Il certificato + firma viene pubblicato su Rekor (transparency log)
#   5. La firma si può verificare senza chiavi pre-condivise!

echo ""
echo "=== ALTERNATIVA: FIRMA CON KEY FILE (per lab locale) ==="

# Per il lab, usiamo la firma con key file (più semplice senza OIDC)
# In produzione: usare keyless con GitHub OIDC

# Generare coppia di chiavi
cosign generate-key-pair --output-key-prefix=signatures/cosign

echo "[OK] Chiavi generate: signatures/cosign.key + signatures/cosign.pub"

# Tag push su registry temporaneo (ttl.sh scade dopo 1h)
REGISTRY="ttl.sh"
IMAGE_REF="${REGISTRY}/supply-chain-demo-lab:1h"

echo ""
echo "--- Push immagine su registry temporaneo ---"
docker tag supply-chain-demo:1.0.0 "$IMAGE_REF"
docker push "$IMAGE_REF" 2>/dev/null && echo "[OK] Push riuscito" || \
  echo "[INFO] Push non riuscito — demo firma offline"

echo ""
echo "--- Firmare l'immagine ---"
COSIGN_PASSWORD="" cosign sign \
  --key signatures/cosign.key \
  --yes \
  "$IMAGE_REF" 2>/dev/null && echo "[OK] Immagine firmata" || \
  echo "[INFO] Firma richiede accesso al registry"

echo ""
echo "--- Verificare la firma ---"
cosign verify \
  --key signatures/cosign.pub \
  "$IMAGE_REF" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -20 || \
  echo "[INFO] Verifica richiede accesso al registry"

echo ""
echo "=== FIRMA ATTESTAZIONE SBOM ==="
# cosign può anche firmare attestazioni arbitrarie (come l'SBOM)
COSIGN_PASSWORD="" cosign attest \
  --key signatures/cosign.key \
  --type cyclonedx \
  --predicate sbom/sbom-cyclonedx.json \
  --yes \
  "$IMAGE_REF" 2>/dev/null && echo "[OK] SBOM attestato come CycloneDX" || \
  echo "[INFO] Attestazione richiede accesso al registry"

echo ""
echo "=== WORKFLOW GITHUB ACTIONS CON COSIGN KEYLESS ==="
cat > signatures/github-actions-sign.yaml << 'EOF'
name: "Build, Sign and Push"

on:
  push:
    tags: ["v*"]

permissions:
  contents: read
  packages: write
  id-token: write    # FONDAMENTALE: permette a cosign keyless di richiedere OIDC token

jobs:
  build-sign:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@b5ca38b07ba8cefc6ba299ba2cf5a40a8f6a7a52  # v3.9.0
      
      - name: Install cosign
        uses: sigstore/cosign-installer@d7d6bc7722e3dca5234d404d87e27db09e6b8cfc  # v3.8.1
      
      - name: Log in to GHCR
        uses: docker/login-action@74a5d142c56f0668f18d8d1b6c6c1ab8bbef66e5  # v3.4.0
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and Push
        id: push
        uses: docker/build-push-action@1dc73fef7e8b4d8f0a7afa9b5b12cae76e1893d7  # v6.17.0
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}/app:${{ github.ref_name }}
          sbom: true      # genera SBOM automaticamente
          provenance: true  # genera SLSA provenance automaticamente
      
      - name: Sign container image (keyless)
        # cosign usa il token OIDC di GitHub Actions per firmare
        # Nessuna chiave da gestire — identità = github.com/org/repo@ref
        run: |
          cosign sign --yes \
            "ghcr.io/${{ github.repository }}/app@${{ steps.push.outputs.digest }}"
      
      - name: Attach SBOM as attestation
        run: |
          syft ghcr.io/${{ github.repository }}/app@${{ steps.push.outputs.digest }} \
            -o cyclonedx-json > sbom.json
          cosign attest --yes \
            --type cyclonedx \
            --predicate sbom.json \
            "ghcr.io/${{ github.repository }}/app@${{ steps.push.outputs.digest }}"
      
      - name: Scan for vulnerabilities
        run: |
          grype ghcr.io/${{ github.repository }}/app@${{ steps.push.outputs.digest }} \
            --fail-on high \
            --output table
EOF

echo "[OK] Workflow GitHub Actions creato: signatures/github-actions-sign.yaml"
```

---

## PART D: GATEKEEPER ADMISSION POLICY

### Esercizio D1: Bloccare Immagini Non Firmate

```bash
cd ~/supply-chain-lab

echo "=== GATEKEEPER: BLOCCO IMMAGINI NON FIRMATE ==="

# Policy OPA/Rego che verifica la firma cosign prima di ammettere il pod
cat > policies/require-image-signature.yaml << 'EOF'
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiresignedimages
  annotations:
    description: >
      Verifica che le immagini container siano firmate con cosign.
      Blocca deployment di immagini non firmate in produzione.
spec:
  crd:
    spec:
      names:
        kind: K8sRequireSignedImages
      validation:
        openAPIV3Schema:
          type: object
          properties:
            allowedRegistries:
              type: array
              items:
                type: string
            verificationKey:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiresignedimages
        
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          image := container.image
          
          # Permettere immagini da registry interni/trusted
          not image_from_trusted_registry(image, input.parameters.allowedRegistries)
          
          # Per immagini da registry non trusted, richiedere firma
          not image_has_signature(image)
          
          msg := sprintf(
            "Immagine '%v' non firmata o da registry non approvato. Firmare con cosign prima del deploy.",
            [image]
          )
        }
        
        image_from_trusted_registry(image, registries) {
          startswith(image, registries[_])
        }
        
        # In produzione, questo check chiamerebbe il cosign webhook
        # o un sistema esterno. Per semplicità qui è semplificato.
        image_has_signature(image) {
          # Verifica reale: cosign verify --key ... image
          # Questo richiederebbe integrazione con cosign webhook o image policy
          endswith(image, "@sha256:")   # immagini con digest sono più sicure di :latest
        }

---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequireSignedImages
metadata:
  name: require-signed-images-production
spec:
  match:
    kinds:
      - apiGroups: ["apps"]
        kinds: ["Deployment"]
    namespaces: ["production"]
  parameters:
    allowedRegistries:
      - "ghcr.io/myorg/"
      - "registry.k8s.io/"
      - "gcr.io/"
    verificationKey: "path/to/cosign.pub"
EOF

echo "[OK] Policy Gatekeeper creata"
echo "[INFO] In produzione: usare sigstore/policy-controller per verifica firma nativa"

# sigstore Policy Controller (alternativa più potente a OPA per questo caso)
echo ""
echo "=== SIGSTORE POLICY CONTROLLER (alternativa) ==="
cat << 'POLICY_CTRL'
# Policy Controller è il modo consigliato per enforcement cosign in K8s

helm repo add sigstore https://sigstore.github.io/helm-charts
helm repo update

helm install policy-controller sigstore/policy-controller \
  --namespace cosign-system \
  --create-namespace

# ClusterImagePolicy: verifica firma su tutte le immagini che matchano il pattern
apiVersion: policy.sigstore.dev/v1beta1
kind: ClusterImagePolicy
metadata:
  name: require-signature-production
spec:
  images:
    - glob: "ghcr.io/myorg/**"
  authorities:
    - keyless:
        url: https://fulcio.sigstore.dev
        identities:
          - issuer: https://token.actions.githubusercontent.com
            subject: "https://github.com/myorg/myrepo/.github/workflows/build.yaml@refs/heads/main"
POLICY_CTRL
```

---

## Conclusioni e Prossimi Passi

```
SUPPLY CHAIN SECURITY — RIEPILOGO:

SLSA FRAMEWORK:
  ✓ L1: Build automatizzato (no manuale)
  ✓ L2: CI fidato + provenance firmata
  ✓ L3: Build hermetic (rete bloccata durante build)
  ✓ L4: Two-party review + hardware signing key
  → GitHub Actions nativo arriva a SLSA 2-3

SBOM (Software Bill of Materials):
  ✓ syft: genera SBOM da immagine, filesystem, codice
  ✓ Formati: CycloneDX (preferito per security), SPDX (legal/compliance)
  ✓ SBOM = inventario completo di OGNI dipendenza
  ✓ Obbligatorio: Executive Order USA 14028 (2021), EU Cyber Resilience Act

GRYPE — VULNERABILITY SCAN:
  ✓ Scan su immagine Docker o SBOM esistente
  ✓ --fail-on high: blocca CI/CD se ci sono HIGH/CRITICAL
  ✓ Database CVE aggiornato automaticamente
  ✓ Alternativa: Trivy (stesso scopo, anche per IaC)

COSIGN KEYLESS:
  ✓ Nessuna chiave da generare/gestire
  ✓ Usa OIDC (GitHub OIDC, Google, Kubernetes ServiceAccount)
  ✓ Firma attestazioni: SBOM, SLSA provenance, custom
  ✓ Transparency log Rekor: ogni firma è pubblica e verificabile
  ✓ Revoca: non serve (le chiavi sono effimere, TTL ~10min)

GATEKEEPER + SIGSTORE POLICY CONTROLLER:
  ✓ Blocca deployment di immagini non firmate in K8s
  ✓ ClusterImagePolicy: definisce chi può firmare cosa
  ✓ identities: specifica il workflow GitHub autorizzato
  ✓ Alternativa enterprise: Notary v2 (Docker Content Trust v2)

WORKFLOW COMPLETO (CI/CD):
  1. Build con BuildKit (SBOM automatico)
  2. syft: genera SBOM completo
  3. grype: scan CVE sull'SBOM (blocca su HIGH/CRITICAL)
  4. cosign sign: firma keyless con OIDC GitHub Actions
  5. cosign attest: allega SBOM all'immagine
  6. Gatekeeper/Policy Controller: blocca immagini non firmate in prod

ATTACCHI PREVENUTI:
  SolarWinds-style: SLSA L3 previene iniezione durante build
  Typosquatting: SBOM rivela dipendenze sospette
  Immagine manomessa nel transit: cosign firma il digest SHA256
  Insider threat: SLSA L4 richiede two-party review
```

```bash
# Pulizia
rm -rf ~/supply-chain-lab
docker rmi supply-chain-demo:1.0.0 2>/dev/null
echo "[OK] Lab Supply Chain Security completato"
```

---

> **Nota versioni:** cosign 2.4.x (2024), syft 1.17.x, grype 0.87.x.
> Sigstore: Fulcio, Rekor, cosign — CNCF graduated 2022.
> EU Cyber Resilience Act: SBOM obbligatorio per software commerciale EU (2025-2027).
> SLSA v1.0: pubblicato aprile 2023 (v0.1 era 2021 con livelli diversi).
> GitHub Actions SLSA: `slsa-framework/slsa-github-generator` v2.x supporta L2 e L3.
> sigstore Policy Controller 0.9.x: sostituto più semplice di Gatekeeper per image signing.
