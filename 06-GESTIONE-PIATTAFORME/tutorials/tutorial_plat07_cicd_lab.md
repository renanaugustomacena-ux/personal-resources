# Tutorial: CI/CD — Pipeline Dichiarative e GitOps — Lab Pratico

> **Documento di riferimento:** `07-ci-cd.md`
> **Dominio:** Gestione Piattaforme — Continuous Integration & Continuous Deployment
> **Ambito:** Fondamenti CI/CD, GitHub Actions (workflow, matrix, OIDC, SHA pinning, reusable workflows), test locale con act v0.2.84, GitOps con ArgoCD 3.x (ApplicationSet, sync policies), GitLab CI concetti, pipeline sicura (supply chain, secret management), DORA metrics, strategie di deployment (blue-green, canary, rolling)
> **Durata lab:** 5-6 ore
> **Livello:** Intermedio — richiede conoscenza di base di Docker e Git
> **Prerequisiti:** Docker Engine 29.x, Git, account GitHub (gratuito), kubectl + K3s opzionale (per esercizi GitOps)
> **Ambiente:** Macchina locale con Docker, GitHub repository per test, act v0.2.84 per run locale

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI CI/CD LAB ===
echo "=== CHECK PREREQUISITI ==="

# Git configurato?
git config user.email 2>/dev/null && echo "[OK] Git configurato" || \
  echo "[WARN] Git non configurato: git config --global user.email 'tu@email.com'"

# Docker disponibile? (necessario per act)
docker --version && echo "[OK] Docker disponibile" || \
  echo "[FAIL] Docker mancante"

# GitHub CLI (opzionale ma utile)
gh --version 2>/dev/null && echo "[OK] GitHub CLI disponibile" || \
  echo "[INFO] GitHub CLI non installato (opzionale)"

echo ""
echo "=== INSTALLAZIONE act (GitHub Actions local runner) ==="

# act: esegue GitHub Actions workflow localmente — versione corrente: 0.2.84 (dicembre 2025)
if ! command -v act &> /dev/null; then
  # Linux / WSL2
  curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
  act --version && echo "[OK] act installato"
else
  echo "[OK] act già disponibile: $(act --version)"
fi

echo ""
echo "=== SETUP REPOSITORY DI LAB ==="

# Creare repository locale per gli esercizi
mkdir -p ~/cicd-lab/.github/workflows
cd ~/cicd-lab
git init
git checkout -b main 2>/dev/null || true

# App di esempio (stessa del lab Docker)
mkdir -p src
cat > src/app.py << 'PYEOF'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/')
def index():
    return jsonify({"message": "CI/CD Lab App v1.0"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
PYEOF

cat > src/requirements.txt << 'EOF'
flask==3.1.0
gunicorn==23.0.0
pytest==8.3.0
pytest-flask==1.3.0
EOF

cat > src/test_app.py << 'PYEOF'
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_health(client):
    r = client.get('/health')
    assert r.status_code == 200
    assert r.get_json()['status'] == 'ok'

def test_index(client):
    r = client.get('/')
    assert r.status_code == 200
    assert 'message' in r.get_json()
PYEOF

cat > Dockerfile << 'EOF'
FROM python:3.12-slim AS builder
WORKDIR /build
COPY src/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install --prefix=/install -r requirements.txt

FROM python:3.12-slim AS runtime
RUN groupadd -r app && useradd -r -g app -u 10001 appuser
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=appuser:app src/app.py .
USER appuser
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
EOF

echo "[OK] Repository lab pronto in ~/cicd-lab"
ls -la ~/cicd-lab/
```

### Architettura della Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CI/CD PIPELINE MODERNA                            │
│                                                                     │
│  DEVELOPER                                                          │
│  git push → GitHub / GitLab                                         │
│                  │                                                  │
│                  ▼                                                  │
│  ┌───────────────────────────────────────────────────────────┐      │
│  │                 CI (Continuous Integration)                │      │
│  │  trigger → lint → test → build → scan → SBOM             │      │
│  │  (minuti)   (fast feedback su ogni push)                  │      │
│  └────────────────────┬──────────────────────────────────────┘      │
│                       │ artefatto (immagine + provenance)           │
│                       ▼                                             │
│  ┌───────────────────────────────────────────────────────────┐      │
│  │              CD (Continuous Deployment)                   │      │
│  │  registry → staging (auto) → approvazione → production   │      │
│  │  (GitOps: ArgoCD monitora Git e sincronizza il cluster)   │      │
│  └───────────────────────────────────────────────────────────┘      │
│                                                                     │
│  GITOPS LOOP:                                                       │
│  Dev pushes manifest → Git repo → ArgoCD rileva diff               │
│  → reconcile K8s ← (ogni 3 minuti o webhook)                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — Perché CI/CD

> Prima di automatizzare, la vita di un developer assomigliava a questo: scrivi codice,
> poi manualmente esegui i test (se ci sono), poi costruisci il binario, poi accedi al
> server, poi copi il file, poi riavvii il servizio, poi preghi che non si rompa niente
> in produzione. Questo processo era lento, error-prone e scalava male. Se il team
> era di 10 persone, ognuno aveva il proprio "modo di deploiare" — caos garantito.
> CI/CD automatizza l'intera catena: ogni push al repository avvia una sequenza verificata,
> riproducibile, e documentata. Non ci sono più "ma sul mio computer funzionava".

---

### Concetto A1: CI vs CD — Differenza Pratica

> **Analogia.** Immagina una fabbrica di automobili. La CI è la linea di qualità:
> ogni pezzo viene controllato prima di andare all'assemblaggio. Se il controllo fallisce,
> il pezzo viene scartato — non va avanti. La CD è il processo di consegna: dall'assemblaggio
> finale alla concessionaria, con tutto il collaudo pre-consegna. La Continuous Deployment
> è quando la macchina viene consegnata automaticamente al cliente senza passare dalla
> concessionaria — richiede fiducia assoluta nel processo di qualità.

```
CONTINUOUS INTEGRATION (CI):
  Trigger: ogni git push / pull request
  Esegue: lint → test unitari → build → scan sicurezza
  Obiettivo: feedback veloce allo sviluppatore (< 10 minuti)
  Risultato: "il codice è integrato e funziona"

CONTINUOUS DELIVERY (CD):
  Trigger: CI superata → artefatto pronto
  Esegue: deploy su staging → test end-to-end → approvazione manuale
  Obiettivo: il codice è sempre in stato rilasciabile
  Risultato: deploy in produzione con un click

CONTINUOUS DEPLOYMENT (CD avanzato):
  Trigger: CI superata → deploy AUTOMATICO in produzione
  Esegue: tutto quanto sopra + monitoring post-deploy + rollback auto
  Prerequisito: copertura test > 85%, canary deployment, feature flags
  Usato da: Netflix, Amazon, Google (migliaia di deploy al giorno)
```

```bash
# Visualizziamo i DORA metrics — i 4 indicatori chiave di maturità CI/CD:
cat << 'DORA'
DORA METRICS (DevOps Research and Assessment):

1. DEPLOYMENT FREQUENCY: quanto spesso si deploya in produzione
   Elite: più volte al giorno
   High:  una volta al giorno / settimana
   Low:   meno di una volta al mese (dove siamo tipicamente all'inizio)

2. LEAD TIME FOR CHANGES: dal commit al deploy in produzione
   Elite: meno di 1 ora
   High:  1 giorno - 1 settimana
   Low:   più di 6 mesi

3. TIME TO RESTORE: quanto ci vuole a ripristinare dopo un'interruzione
   Elite: meno di 1 ora
   High:  meno di 1 giorno

4. CHANGE FAILURE RATE: % di deployment che causano problemi
   Elite: 0-15%
   Low:   46-60%

OBIETTIVO: migliorare progressivamente. Non serve essere "Elite" subito.
DORA'
```

---

### Concetto A2: La Pipeline come Codice (IaC per CI/CD)

> **Analogia.** Un regista di cinema non dice agli attori "improvvisate qualcosa"
> ogni volta che si gira. Ha uno script dettagliato: ogni scena, ogni inquadratura,
> ogni battuta è definita in anticipo e replicabile. La pipeline come codice è
> lo stesso concetto: i passaggi da eseguire sono in un file (`workflow.yml`, `.gitlab-ci.yml`)
> versionato in git, revisionabile, e identico in ogni esecuzione.

```
PIPELINE-AS-CODE VANTAGGI:
  ✓ Versioning: chi ha modificato la pipeline? Quando? Perché? (git blame)
  ✓ Riproducibilità: stessa pipeline su qualsiasi runner
  ✓ Review: le modifiche alla pipeline passano per code review
  ✓ Rollback: git revert per tornare a una pipeline precedente
  ✓ Documentazione: la pipeline è la documentazione del processo di deploy

STRUTTURA TIPICA:
  .github/workflows/ci.yml     ← GitHub Actions
  .gitlab-ci.yml               ← GitLab CI
  Jenkinsfile                  ← Jenkins
  .circleci/config.yml         ← CircleCI
```

---

## PART B: GITHUB ACTIONS — IL CUORE DEL LAB

### Esercizio B1: Primo Workflow — CI Base

```bash
cd ~/cicd-lab

cat > .github/workflows/ci.yml << 'EOF'
# Workflow CI di base — si attiva su ogni push e pull request
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

# BEST PRACTICE: permessi minimi per default
# (GitHub Actions runner ubuntu-24.04 da gennaio 2025)
permissions:
  contents: read     # solo lettura del codice

jobs:
  
  # ─── JOB 1: Lint e validazione ────────────────────────────────────
  lint:
    name: Lint & Validate
    runs-on: ubuntu-24.04    # ubuntu-latest = ubuntu-24.04 da gennaio 2025
    steps:
    
    - name: Checkout codice
      uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2 — SHA PINNED!
      # IMPORTANTE: mai usare @v4 o @latest — usare il SHA del commit
      # Motivo: @v4 può essere aggiornato dal maintainer → supply chain risk
    
    - name: Setup Python
      uses: actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b  # v5.3.0
      with:
        python-version: "3.12"
        cache: "pip"         # cache automatica delle dipendenze pip
    
    - name: Installa dipendenze di lint
      run: pip install flake8 black mypy
    
    - name: Lint Python (flake8)
      run: |
        flake8 src/ --max-line-length=120 --ignore=E501,W503
        echo "✓ flake8 passato"
    
    - name: Format check (black)
      run: |
        black --check src/
        echo "✓ black format check passato"
  
  # ─── JOB 2: Test unitari ──────────────────────────────────────────
  test:
    name: Unit Tests
    runs-on: ubuntu-24.04
    needs: [lint]            # eseguito DOPO lint
    
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]   # test su più versioni
        fail-fast: false     # continua anche se una versione fallisce
    
    steps:
    
    - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
    
    - name: Setup Python ${{ matrix.python-version }}
      uses: actions/setup-python@0b93645e9fea7318ecaed2b359559ac225c90a2b
      with:
        python-version: ${{ matrix.python-version }}
        cache: "pip"
    
    - name: Installa dipendenze
      working-directory: src
      run: pip install -r requirements.txt
    
    - name: Esegui test con pytest
      working-directory: src
      run: |
        pytest test_app.py -v \
          --tb=short \
          --junitxml=../test-results-${{ matrix.python-version }}.xml
    
    - name: Upload risultati test
      uses: actions/upload-artifact@65c4c4a1c2899fc98dffdb8f977bf0e6bfa73879  # v4.6.0
      if: always()           # carica i risultati anche se i test falliscono
      with:
        name: test-results-${{ matrix.python-version }}
        path: test-results-*.xml
  
  # ─── JOB 3: Build Docker ──────────────────────────────────────────
  build:
    name: Docker Build
    runs-on: ubuntu-24.04
    needs: [test]
    permissions:
      contents: read
      packages: write        # necessario per push al GitHub Container Registry
    
    steps:
    
    - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
    
    - name: Setup Docker Buildx
      uses: docker/setup-buildx-action@f7ce87b17fa9f5afa2b6b91d9e6ede5e6c3db1c3  # v3.9.0
    
    - name: Login al Container Registry
      uses: docker/login-action@9780b0c442fbb1117ed29e0efdff1e18412f7567  # v3.3.0
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}   # token automatico, nessun secret manuale
    
    - name: Metadata immagine
      id: meta
      uses: docker/metadata-action@369eb591f429131d6889c46b94e711f089e6ca96  # v5.6.1
      with:
        images: ghcr.io/${{ github.repository }}
        tags: |
          type=ref,event=branch
          type=sha,prefix={{branch}}-,format=short
          type=raw,value=latest,enable={{is_default_branch}}
    
    - name: Build e Push immagine
      uses: docker/build-push-action@0adf9959d097bfb60c9c4181c5e51bb5b02e9b72  # v6.14.0
      with:
        context: .
        push: ${{ github.event_name != 'pull_request' }}  # push solo su push, non PR
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha          # cache GitHub Actions
        cache-to: type=gha,mode=max
        platforms: linux/amd64,linux/arm64
    
    - name: Scan CVE con Trivy
      uses: aquasecurity/trivy-action@18f2510ee396bbf400402c0a4a1b5d9c68b4b0f6  # v0.29.0
      with:
        image-ref: ghcr.io/${{ github.repository }}:latest
        format: sarif
        output: trivy-results.sarif
        severity: CRITICAL,HIGH
        exit-code: "1"     # fallisce CI se trovate CVE critiche
    
    - name: Upload risultati sicurezza
      uses: github/codeql-action/upload-sarif@4f3212b61783c3c68e8309a0f18a699764274f6d  # v3.27.1
      if: always()
      with:
        sarif_file: trivy-results.sarif

EOF

# Commit del workflow
git add .
git commit -m "feat: add CI pipeline with lint, test, build stages"

echo "[OK] Workflow CI creato"
cat .github/workflows/ci.yml | grep "runs-on:"
# Verifica che usi ubuntu-24.04 (aggiornato da gennaio 2025)
```

---

### Esercizio B2: Test Locale con act

```bash
# act esegue GitHub Actions localmente — no push necessario per testare
cd ~/cicd-lab

# Configurare act per usare immagini Ubuntu 24.04
cat > ~/.actrc << 'EOF'
-P ubuntu-24.04=catthehacker/ubuntu:act-24.04
-P ubuntu-22.04=catthehacker/ubuntu:act-22.04
-P ubuntu-latest=catthehacker/ubuntu:act-24.04
EOF

echo "[OK] act configurato per Ubuntu 24.04"

# Eseguire solo il job lint
act -j lint --dry-run
# Mostra cosa verrà eseguito senza eseguirlo effettivamente

act -j lint
# Esegue il job lint localmente

# Eseguire un job specifico con variabili
act -j test \
  -e <(echo '{"push": {"ref": "refs/heads/main"}}') \
  --matrix python-version:3.12

# Listare tutti i workflow e job disponibili
act -l
# OUTPUT:
# Stage  Job ID   Job name        Workflow name  Workflow file  Events
# 0      lint     Lint & Validate  CI Pipeline   ci.yml         push,pull_request
# 1      test     Unit Tests       CI Pipeline   ci.yml         push,pull_request
# 2      build    Docker Build     CI Pipeline   ci.yml         push,pull_request

# Passare secret localmente (per test)
echo "token123" > /tmp/test-secret.txt
act -j build --secret-file /tmp/test-secret.txt
rm /tmp/test-secret.txt

# DEBUG: vedere i log dettagliati
act -j lint --verbose 2>&1 | head -50

echo "
act CHEATSHEET:
  act               → esegui su push event
  act pull_request  → esegui su pull_request event
  act -j <job>      → esegui solo un job
  act -l            → lista workflow/job
  act -n            → dry-run (solo stampa cosa farebbe)
  act --secret KEY=VALUE  → passa secret manualmente
"
```

---

### Esercizio B3: Workflow Avanzato — OIDC e Reusable Workflows

```bash
cd ~/cicd-lab

# OIDC: autenticazione su cloud provider SENZA secret long-lived
# Il runner ottiene un JWT dal provider di identità GitHub, lo scambia
# per credenziali temporanee AWS/Azure/GCP — nessun secret da gestire

cat > .github/workflows/deploy-aws.yml << 'EOF'
name: Deploy AWS (OIDC)

on:
  push:
    branches: [main]

permissions:
  contents: read
  id-token: write    # OBBLIGATORIO per OIDC — permette al workflow di richiedere il JWT

jobs:
  deploy:
    runs-on: ubuntu-24.04
    
    steps:
    - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
    
    # OIDC: nessun access key/secret key AWS nel repository!
    - name: Configure AWS credentials via OIDC
      uses: aws-actions/configure-aws-credentials@xxxxxxxxxx  # pin al SHA reale
      with:
        role-to-assume: arn:aws:iam::123456789:role/github-actions-deploy
        aws-region: eu-west-1
        # GitHub invia JWT → AWS verifica il claim 'sub' (repository + branch)
        # AWS rilascia credenziali temporanee valide 1 ora
    
    - name: Deploy su EKS (esempio)
      run: |
        aws eks update-kubeconfig --name prod-cluster --region eu-west-1
        kubectl set image deployment/app app=ghcr.io/${{ github.repository }}:${{ github.sha }}
        kubectl rollout status deployment/app --timeout=300s
EOF

# Reusable Workflow — evita duplicazione tra repository
cat > .github/workflows/reusable-build.yml << 'EOF'
# Questo workflow è riutilizzabile da altri workflow/repo
name: Reusable Build

on:
  workflow_call:        # keyword speciale per workflow riutilizzabile
    inputs:
      image-name:
        required: true
        type: string
      push:
        required: false
        type: boolean
        default: false
    secrets:
      registry-password:
        required: false
    outputs:
      image-tag:
        description: "Tag dell'immagine costruita"
        value: ${{ jobs.build.outputs.tag }}

jobs:
  build:
    runs-on: ubuntu-24.04
    outputs:
      tag: ${{ steps.meta.outputs.version }}
    steps:
    - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
    
    - name: Setup Buildx
      uses: docker/setup-buildx-action@f7ce87b17fa9f5afa2b6b91d9e6ede5e6c3db1c3
    
    - id: meta
      uses: docker/metadata-action@369eb591f429131d6889c46b94e711f089e6ca96
      with:
        images: ${{ inputs.image-name }}
        tags: |
          type=sha,format=short
    
    - uses: docker/build-push-action@0adf9959d097bfb60c9c4181c5e51bb5b02e9b72
      with:
        push: ${{ inputs.push }}
        tags: ${{ steps.meta.outputs.tags }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
EOF

# Usare il reusable workflow
cat > .github/workflows/main-ci.yml << 'EOF'
name: Main CI

on:
  push:
    branches: [main]

jobs:
  build-app:
    uses: ./.github/workflows/reusable-build.yml    # riferimento locale
    # oppure: uses: myorg/cicd-templates/.github/workflows/build.yml@main  # repo esterno
    with:
      image-name: ghcr.io/${{ github.repository }}
      push: true
    secrets:
      registry-password: ${{ secrets.GITHUB_TOKEN }}
  
  notify-slack:
    needs: build-app
    runs-on: ubuntu-24.04
    steps:
    - name: Immagine builtata
      run: echo "Tag: ${{ needs.build-app.outputs.image-tag }}"
EOF

git add .github/
git commit -m "feat: add OIDC deploy workflow and reusable build workflow"

echo "[OK] Workflow avanzati creati"
```

---

### Esercizio B4: SHA Pinning Automatico con Dependabot

```bash
# SHA pinning: mai usare @v1, @v2, @latest — sempre il SHA completo del commit
# Motivo: @v1 può essere aggiornato/compromesso dal maintainer (supply chain attack)
# Esempio reale: tj-actions/changed-files@v35 era stato compromesso (2023)

# Configurare Dependabot per aggiornare automaticamente le action
mkdir -p .github
cat > .github/dependabot.yml << 'EOF'
version: 2

updates:
  # Aggiorna le GitHub Actions automaticamente (con PR)
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"      # controlla ogni settimana
      day: "monday"
    commit-message:
      prefix: "chore(deps)"
    groups:
      actions:
        patterns:
          - "actions/*"       # raggruppa tutte le actions/* in una PR
  
  # Aggiorna le dipendenze Python
  - package-ecosystem: "pip"
    directory: "/src"
    schedule:
      interval: "weekly"
    commit-message:
      prefix: "chore(deps)"
EOF

git add .github/dependabot.yml
git commit -m "chore: add Dependabot for automatic SHA pinning updates"

# SCRIPT UTILE: trova action non pinnate con SHA
grep -r "uses:" .github/workflows/ | \
  grep -v "#" | \
  grep -E "@v[0-9]|@latest|@main" | \
  grep -v "sha|[0-9a-f]{40}"
# Mostra le action che NON sono pinnate al SHA — da correggere

echo "
SHA PINNING GUIDE:
  SBAGLIATO:  uses: actions/checkout@v4
  SBAGLIATO:  uses: actions/checkout@main  
  CORRETTO:   uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683

Per trovare il SHA di una action:
  1. Vai su GitHub → action repository → commits
  2. Copia il SHA del commit del tag che vuoi usare
  3. Aggiungi un commento con la versione: # v4.2.2

Alternativa: usa 'actionlint' per validare i workflow
  brew install actionlint   # macOS
  actionlint .github/workflows/*.yml
"
```

---

## PART C: GITOPS CON ARGOCD 3.x

### Esercizio C1: GitOps — Il Principio Fondamentale

> **Analogia.** Prima di GitOps, deploiare era come cucinare senza ricetta: ogni cuoco
> faceva a modo suo, i risultati erano imprevedibili, e se il cuoco si assentava,
> nessuno sapeva cosa c'era nella pentola. Con GitOps, il repository Git è la ricetta:
> tutto ciò che è nel cluster deve corrispondere esattamente a ciò che è nel Git.
> Se qualcuno tocca il cluster manualmente, ArgoCD se ne accorge e ripristina lo stato
> corretto dalla "ricetta". Non esiste un "ma io avevo deployato qualcosa a mano" — Git
> è l'unica fonte di verità.

```
GITOPS PRINCIPI (da OpenGitOps 1.0):

1. DICHIARATIVO: lo stato del sistema è descritto in file (non script)
   ✓  Kubernetes YAML manifests
   ✗  kubectl run ... (imperativo)

2. VERSIONATO: lo stato è in un sistema di version control (Git)
   ✓  git blame, git log, git revert — audit completo
   ✗  "non so chi ha deployato quella cosa la settimana scorsa"

3. APPROVATO AUTOMATICAMENTE: i cambiamenti passano per Git (PR/review)
   ✓  git push → PR → review → merge → deploy automatico
   ✗  SSH sul server di produzione e modifica manuale

4. PULL-BASED: l'agente nel cluster tira i cambiamenti da Git
   ✓  ArgoCD/Flux legge Git e applica al cluster
   ✗  CI/CD pusha direttamente con kubectl (push-based)

PERCHÉ PULL-BASED È MEGLIO:
  - Sicurezza: nessun accesso esterno al cluster (solo in uscita da ArgoCD)
  - Resilienza: se la CI è down, il cluster mantiene lo stato corretto
  - Audit: ogni cambiamento è in Git con autore e timestamp
```

---

### Esercizio C2: Setup ArgoCD 3.x

```bash
# Prerequisito: K3s funzionante (dal lab K8s)
# Se K3s non è installato, installarlo con:
# curl -sfL https://get.k3s.io | sh -
# export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

kubectl get nodes 2>/dev/null || {
  echo "[WARN] K3s non disponibile - installare K3s prima di procedere"
  echo "       curl -sfL https://get.k3s.io | sh -"
}

# Installare ArgoCD 3.3.x
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Attendere tutti i componenti
kubectl wait --for=condition=Available deployment \
  argocd-server argocd-repo-server argocd-application-controller \
  -n argocd --timeout=300s

# Ottenere la password admin iniziale
ARGOCD_PASS=$(kubectl get secret argocd-initial-admin-secret \
  -n argocd -o jsonpath='{.data.password}' | base64 -d)
echo "Password admin ArgoCD: $ARGOCD_PASS"

# Installare CLI argocd
curl -sSL -o /usr/local/bin/argocd \
  https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
chmod +x /usr/local/bin/argocd
argocd version --client

# Accesso via port-forward
kubectl port-forward svc/argocd-server -n argocd 8080:443 &
sleep 2

# Login via CLI
argocd login localhost:8080 \
  --username admin \
  --password "$ARGOCD_PASS" \
  --insecure

echo "[OK] ArgoCD operativo: https://localhost:8080"

# Novità ArgoCD 3.x vs 2.x:
echo "
ARGOCD 3.x NOVITÀ PRINCIPALI:
  - 3.0 (maggio 2025): annotation-based tracking default
    legacy repository config in argocd-cm rimossa
  - 3.1 (agosto 2025): OCI registry support nativo
  - 3.2 (novembre 2025): Progressive Sync ApplicationSet migliorato
  - 3.3 (dicembre 2025): PreDelete hooks, shallow clone repo grandi
"
```

---

### Esercizio C3: Application ArgoCD — GitOps Completo

```bash
# Struttura del repository GitOps (tipicamente separato dal codice)
mkdir -p ~/gitops-repo/{apps,infrastructure}
cd ~/gitops-repo
git init

# Manifesti dell'applicazione nel repo GitOps
mkdir -p apps/lab-app/{base,overlays/{staging,production}}

# Base manifest (Kustomize)
cat > apps/lab-app/base/deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lab-app
  labels:
    app: lab-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: lab-app
  template:
    metadata:
      labels:
        app: lab-app
    spec:
      containers:
      - name: app
        image: ghcr.io/miorepo/lab-app:latest  # verrà aggiornato da CI/CD
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "128Mi"
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
EOF

cat > apps/lab-app/base/service.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: lab-app
spec:
  selector:
    app: lab-app
  ports:
  - port: 80
    targetPort: 8080
EOF

cat > apps/lab-app/base/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
EOF

# Overlay per produzione: più repliche, risorse diverse
cat > apps/lab-app/overlays/production/kustomization.yaml << 'EOF'
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: production

bases:
  - ../../base

patches:
  - target:
      kind: Deployment
      name: lab-app
    patch: |
      - op: replace
        path: /spec/replicas
        value: 3
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/cpu
        value: "500m"
      - op: replace
        path: /spec/template/spec/containers/0/resources/limits/memory
        value: "256Mi"
EOF

git add .
git commit -m "feat: add lab-app GitOps manifests"

# Creare namespace per l'app
kubectl create namespace production 2>/dev/null || true

# ArgoCD Application CRD
cat > /tmp/argocd-app.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: lab-app-production
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io  # cleanup risorse quando app viene eliminata
spec:
  project: default
  
  source:
    repoURL: https://github.com/mioutente/gitops-repo.git  # sostituire con URL reale
    targetRevision: main
    path: apps/lab-app/overlays/production
  
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  
  syncPolicy:
    automated:
      prune: true        # elimina risorse rimosse dal Git
      selfHeal: true     # ripristina se qualcuno modifica manualmente il cluster
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
EOF

kubectl apply -f /tmp/argocd-app.yaml

# Monitorare la sincronizzazione
argocd app list
argocd app get lab-app-production
# OUTPUT: Status: Synced, Health: Healthy

# Simulare un drift manuale (qualcuno modifica il cluster direttamente)
kubectl scale deployment lab-app --replicas=1 -n production
# ArgoCD rileva la diff entro 3 minuti e ripristina 3 repliche (selfHeal)

# Forzare sync immediato
argocd app sync lab-app-production
```

---

### Esercizio C4: ApplicationSet — Multi-Cluster Deploy

```bash
# ApplicationSet in ArgoCD 3.2+: genera automaticamente Application CRD
# per ogni ambiente/cluster dalla stessa definizione

cat > /tmp/argocd-appset.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: lab-app-environments
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - environment: staging
        namespace: staging
        replicas: "1"
      - environment: production
        namespace: production
        replicas: "3"
  
  template:
    metadata:
      name: "lab-app-{{environment}}"
      labels:
        environment: "{{environment}}"
    spec:
      project: default
      source:
        repoURL: https://github.com/mioutente/gitops-repo.git
        targetRevision: main
        path: "apps/lab-app/overlays/{{environment}}"
      destination:
        server: https://kubernetes.default.svc
        namespace: "{{namespace}}"
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
        - CreateNamespace=true
  
  # Progressive Sync (ArgoCD 3.2+): deploya in staging prima, poi produzione
  strategy:
    type: RollingSync
    rollingSync:
      steps:
      - matchExpressions:
        - key: environment
          operator: In
          values: [staging]
      - matchExpressions:
        - key: environment
          operator: In
          values: [production]
        maxUpdate: 50%    # aggiorna max 50% dei cluster produzione alla volta
EOF

kubectl apply -f /tmp/argocd-appset.yaml
kubectl get applications -n argocd
# OUTPUT:
# NAME                   SYNC STATUS   HEALTH STATUS
# lab-app-staging        Synced        Healthy
# lab-app-production     Synced        Healthy
```

---

## PART D: STRATEGIE DI DEPLOYMENT

### Esercizio D1: Rolling Update — Zero Downtime

```bash
# Rolling Update: i pod vengono aggiornati uno alla volta
# già coperto nel lab K8s, ma vediamo come integrarlo con CI/CD

cat > /tmp/rolling-deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-rolling
  namespace: lab-app
spec:
  replicas: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # massimo 1 pod in più durante l'update (6 totali)
      maxUnavailable: 0  # zero pod non disponibili (zero downtime)
  selector:
    matchLabels:
      app: app-rolling
  template:
    metadata:
      labels:
        app: app-rolling
        version: "1.0"
    spec:
      containers:
      - name: app
        image: nginx:1.27-alpine
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 3
          failureThreshold: 3   # se fallisce 3 volte, rolling si ferma
EOF

kubectl apply -f /tmp/rolling-deployment.yaml
kubectl rollout status deployment/app-rolling -n lab-app

# Aggiornare l'immagine (simula un nuovo deploy da CI/CD)
kubectl set image deployment/app-rolling app=nginx:1.28-alpine -n lab-app
kubectl rollout status deployment/app-rolling -n lab-app
# Vedi il rolling update in azione: pod aggiornati uno alla volta

# Se qualcosa va storto
kubectl rollout undo deployment/app-rolling -n lab-app
kubectl rollout history deployment/app-rolling -n lab-app
```

---

### Esercizio D2: Blue-Green Deployment

```bash
# Blue-Green: due ambienti identici, switch del traffico
# Blue: versione corrente in produzione
# Green: nuova versione, viene preparata parallela e poi switchiamo

cat > /tmp/blue-green.yaml << 'EOF'
# Blue: versione corrente
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-blue
  namespace: lab-app
  labels:
    app: webapp
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      version: blue
  template:
    metadata:
      labels:
        app: webapp
        version: blue
    spec:
      containers:
      - name: app
        image: nginx:1.27-alpine
        ports:
        - containerPort: 80

---
# Green: nuova versione (preparata in parallelo)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-green
  namespace: lab-app
  labels:
    app: webapp
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: webapp
      version: green
  template:
    metadata:
      labels:
        app: webapp
        version: green
    spec:
      containers:
      - name: app
        image: nginx:1.28-alpine    # nuova versione
        ports:
        - containerPort: 80

---
# Service punta a blue (produzione attiva)
apiVersion: v1
kind: Service
metadata:
  name: webapp-svc
  namespace: lab-app
spec:
  selector:
    app: webapp
    version: blue     # ← cambieremo questo a "green" per switchare
  ports:
  - port: 80
    targetPort: 80
EOF

kubectl apply -f /tmp/blue-green.yaml
kubectl get pods -n lab-app -l app=webapp

# Test: il traffico va su blue
kubectl run test-bg --image=curlimages/curl:8.10 --rm -it -n lab-app -- \
  curl -s http://webapp-svc.lab-app.svc.cluster.local -I | grep Server
# OUTPUT: Server: nginx/1.27.x (blue)

# Testare green prima dello switch
kubectl port-forward deployment/app-green 18080:80 -n lab-app &
curl -s http://localhost:18080 -I | head -5
kill %1 2>/dev/null

# Switch del traffico: blue → green (istantaneo, zero downtime)
kubectl patch service webapp-svc -n lab-app \
  -p '{"spec": {"selector": {"version": "green"}}}'

# Verificare lo switch
kubectl run test-after --image=curlimages/curl:8.10 --rm -it -n lab-app -- \
  curl -s http://webapp-svc.lab-app.svc.cluster.local -I | grep Server
# OUTPUT: Server: nginx/1.28.x (green) — switch completato

# Se c'è un problema: rollback istantaneo
# kubectl patch service webapp-svc -n lab-app \
#   -p '{"spec": {"selector": {"version": "blue"}}}'
```

---

## PART E: PIPELINE SICURA — SECRET MANAGEMENT

### Esercizio E1: Secret nelle Pipeline — Best Practices

```bash
# GitHub Actions usa encrypted secrets — MAI hardcodare nel workflow

# Struttura corretta per secret nelle pipeline:
cat > /tmp/secret-management-demo.yml << 'EOF'
name: Secure Pipeline

on: [push]

jobs:
  deploy:
    runs-on: ubuntu-24.04
    
    steps:
    - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
    
    # ✓ CORRETTO: uso di GitHub Secrets
    - name: Deploy con credenziali sicure
      env:
        DB_PASSWORD: ${{ secrets.DB_PASSWORD }}          # secret criptato in GitHub
        AWS_ACCESS_KEY: ${{ secrets.AWS_ACCESS_KEY_ID }} # da evitare: prefer OIDC
      run: |
        echo "Connessione al DB..."
        # $DB_PASSWORD è mascherato nei log come "***"
    
    # ✓ MEGLIO: OIDC invece di long-lived key
    - name: Configure AWS via OIDC (no key!)
      uses: aws-actions/configure-aws-credentials@xxxxxxxxxx
      with:
        role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
        aws-region: eu-west-1
    
    # ✗ SBAGLIATO: hardcodare nel workflow
    # env:
    #   DB_PASSWORD: "mypassword123"    # ← MAI fare questo
    #   AWS_KEY: "AKIAIOSFODNN7EXAMPLE"  # ← MAI fare questo
EOF

# Verificare che il repository non abbia secret nel codice
# gitleaks: scanner di secret nel codice
if command -v gitleaks &>/dev/null; then
  gitleaks detect --source . --verbose
else
  echo "[INFO] gitleaks non installato"
  # Installare: brew install gitleaks  o  apt install gitleaks
fi

# Pattern di secret comuni da cercare manualmente
echo "
PATTERN DI SECRET DA NON COMMITTARE:
  - Chiavi AWS: AKIA...
  - Token GitHub: ghp_... o github_pat_...
  - Connection string: postgresql://user:password@...
  - Private key: -----BEGIN RSA PRIVATE KEY-----
  - API key in .env file
  
STRUMENTI DI PREVENZIONE:
  - gitleaks: scan del repo per secret
  - git-secrets: hook pre-commit
  - detect-secrets: Yelp open source
  - Dependabot secret scanning (GitHub)
"
```

---

## Conclusioni e Prossimi Passi

```
CI/CD — CONCETTI APPRESI:

FONDAMENTALI:
  ✓ CI: feedback veloce su ogni push (lint → test → build)
  ✓ CD: deploy automatico dopo CI passata
  ✓ Pipeline-as-code: il processo è versionato in Git

GITHUB ACTIONS:
  ✓ workflow YAML in .github/workflows/
  ✓ runner ubuntu-24.04 (default da gennaio 2025)
  ✓ SHA pinning obbligatorio per le action di terze parti
  ✓ permissions: {} minimo, espandere solo dove serve
  ✓ Reusable workflow: riutilizzo tra repository
  ✓ OIDC: autenticazione cloud senza long-lived secret
  ✓ act: test locale dei workflow senza push

GITOPS CON ARGOCD 3.x:
  ✓ Pull-based: ArgoCD tira i cambiamenti da Git
  ✓ selfHeal: ripristina automaticamente il drift manuale
  ✓ ApplicationSet: deploy multi-ambiente dalla stessa definizione
  ✓ Progressive Sync (3.2+): staging prima, poi produzione

STRATEGIE DEPLOY:
  ✓ Rolling Update: pod aggiornati uno alla volta, zero downtime
  ✓ Blue-Green: due ambienti, switch istantaneo del traffico
  ✓ Canary: 5% traffico sulla nuova versione → graduale

SECRET MANAGEMENT:
  ✓ GitHub Encrypted Secrets
  ✓ OIDC per cloud (AWS/Azure/GCP) — no long-lived key
  ✓ Gitleaks per scan preventivo nel codice

COMANDI ESSENZIALI:
  act -j <job>                → test locale workflow
  argocd app list             → stato applicazioni
  argocd app sync <app>       → forza sincronizzazione
  argocd app rollback <app>   → rollback alla versione precedente
  kubectl rollout undo        → rollback deployment K8s
```

**Prossimi tutorial:**
- `tutorial_plat08_monitoring_observability_lab.md` — Prometheus 3.x + Grafana 12
- `tutorial_plat20_supply_chain_slsa_lab.md` — Supply chain sicura con SLSA + cosign

```bash
# Pulizia
kubectl delete namespace lab-app 2>/dev/null || true
rm -rf ~/cicd-lab ~/gitops-repo

echo "[OK] Lab CI/CD completato"
```

---

> **Nota versioni:** Tutorial validato con GitHub Actions runner ubuntu-24.04 (standard da
> gennaio 2025), act v0.2.84 (dicembre 2025), ArgoCD 3.3.x (dicembre 2025).
> Breaking change ArgoCD 3.0: `spec.applyNestedSelectors` ora sempre `true` in ApplicationSet;
> legacy repository config in argocd-cm rimossa — migrare a Secrets prima dell'upgrade da 2.x.
