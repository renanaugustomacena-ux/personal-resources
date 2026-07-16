# Tutorial: Sicurezza delle Piattaforme — Defense in Depth, Scanning e Runtime Security

> **Documento di riferimento:** `13-sicurezza-piattaforme.md`
> **Dominio:** Gestione Piattaforme — Sicurezza e Compliance
> **Ambito:** Defense in depth, Zero Trust, Trivy container scanning, gitleaks secrets detection, Falco runtime security, RBAC audit Kubernetes, seccomp profiles, OPA/Kyverno policy enforcement
> **Durata lab:** 6-8 ore
> **Livello:** Avanzato — richiede Kubernetes (K3s o kind), Docker, Python 3.10+
> **Prerequisiti:** K3s o kind cluster locale, Docker Engine 29.x, helm 3.x, kubectl configurato
> **Ambiente:** Tutto locale: Falco via Helm su K3s, Trivy CLI, gitleaks, Kyverno policy admission controller

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI SECURITY LAB ===
echo "=== PREREQUISITI ==="

kubectl version --client --short 2>/dev/null && echo "[OK] kubectl" || echo "[FAIL] kubectl richiesto"
helm version --short 2>/dev/null && echo "[OK] helm" || echo "[FAIL] helm richiesto"
docker --version && echo "[OK] Docker" || echo "[FAIL] Docker richiesto"

# Verificare cluster attivo
kubectl get nodes 2>/dev/null && echo "[OK] Cluster Kubernetes attivo" || \
  echo "[FAIL] Nessun cluster — avviare K3s: curl -sfL https://get.k3s.io | sh -"

# Tool di sicurezza
for tool in trivy gitleaks; do
  command -v $tool &>/dev/null && echo "[OK] $tool" || echo "[INFO] $tool non installato — istruz. sotto"
done

echo ""
echo "=== INSTALLAZIONE TOOL ==="

# Trivy (vulnerability scanner per container e IaC)
if ! command -v trivy &>/dev/null; then
  curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin v0.57.0
  echo "[OK] Trivy installato"
fi

# gitleaks (secrets scanner per git repo)
if ! command -v gitleaks &>/dev/null; then
  GITLEAKS_VERSION="8.21.2"
  curl -sSfL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
    | tar -xz -C /tmp gitleaks && mv /tmp/gitleaks /usr/local/bin/gitleaks
  echo "[OK] gitleaks installato"
fi

trivy --version 2>/dev/null | head -1
gitleaks version 2>/dev/null

mkdir -p ~/security-lab/{falco,kyverno,trivy,gitleaks,workloads}
cd ~/security-lab

echo "[OK] Directory lab pronta: ~/security-lab"
```

### Architettura Defense in Depth del Lab

```
┌──────────────────────────────────────────────────────────────────────────┐
│              DEFENSE IN DEPTH — LAB SICUREZZA                            │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 1: SUPPLY CHAIN                                            │   │
│  │  gitleaks ── secret scan su git commits                          │   │
│  │  Trivy ──── vulnerabilità immagini container + IaC              │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 2: ADMISSION CONTROL                                       │   │
│  │  Kyverno ── policy: no-latest-tag, require-requests, read-only- │   │
│  │             rootfs, no-privileged, require-resource-limits       │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 3: RUNTIME SECURITY                                        │   │
│  │  Falco ──── detection syscall anomale (shell in container,       │   │
│  │             read /etc/shadow, network scan, privilege escalation) │   │
│  │  seccomp ── filtro syscall a livello kernel (allowlist)          │   │
│  └───────────────────────────────────────────────────────────────────┘   │
│  ┌───────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 4: ACCESSO                                                 │   │
│  │  RBAC audit ── chi ha accesso a cosa nel cluster Kubernetes      │   │
│  └───────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — Sicurezza delle Piattaforme

> La sicurezza non è un prodotto che si acquista e si installa.
> È una pratica continua, un processo, un mindset.
> Un sistema può avere il firewall più aggiornato del mondo,
> ma se un developer fa commit di una password nel repository Git
> e quell'API key finisce su GitHub per 30 secondi,
> l'attaccante ha già estratto le credenziali e le ha archiviate.
> La sicurezza moderna richiede difesa a ogni layer, dal codice sorgente
> fino al runtime dei container in produzione.

---

### Concetto A1: Defense in Depth

```
DEFENSE IN DEPTH — STRATI DI PROTEZIONE:

L'idea è semplice: ogni strato assume che il precedente possa fallire.

STRATO 1 — SUPPLY CHAIN (prima che il codice entri in produzione):
  ├── Secret scanning: nessuna credenziale nel codice sorgente
  ├── Dependency audit: nessuna dipendenza con CVE critiche
  ├── Image scanning: immagini container senza vulnerabilità HIGH/CRITICAL
  └── IaC scanning: nessuna misconfiguration Terraform/Kubernetes/Helm

STRATO 2 — ADMISSION CONTROL (al momento del deploy):
  ├── Policy: immagini devono provenire da registry approvati
  ├── Policy: nessun container privilegiato senza eccezione esplicita
  ├── Policy: tutti i container hanno resource limits
  └── Policy: rootFileSystem read-only (il container non può scrivere su disco)

STRATO 3 — RUNTIME (durante l'esecuzione):
  ├── Falco: detection comportamenti anomali (syscall monitoring)
  ├── seccomp: blocco syscall pericolose a livello kernel
  ├── AppArmor/SELinux: Mandatory Access Control
  └── Network Policy: solo traffico esplicitamente permesso

STRATO 4 — RISPOSTA AGLI INCIDENTI:
  ├── Audit log: tutto loggato e immutabile
  ├── Alert: notifiche immediate su eventi critici
  ├── Quarantine: isolamento automatico del pod compromesso
  └── Forensics: preservare evidenze senza perdere dati

SE UN STRATO FALLISCE → il successivo contiene il danno.
```

---

### Concetto A2: Zero Trust — Never Trust, Always Verify

```
ZERO TRUST: IL MODELLO MODERNO DI SICUREZZA

Modello tradizionale (perimetro):
  INTERNET ──→ [FIREWALL] ──→ INTERNO (tutto trusted)
  Problema: se un attaccante supera il firewall, ha accesso a tutto.
  Problema: minacce interne (malicious insider, compromissione host).

Modello Zero Trust:
  - Ogni richiesta viene autenticata e autorizzata, indipendentemente dalla rete
  - Nessuna fiducia implicita basata sulla posizione di rete
  - Least privilege: accesso minimo necessario per svolgere il compito
  - Assume breach: progetta come se l'attaccante fosse già dentro

IMPLEMENTAZIONE PRATICA:
  1. Identità: ogni servizio ha un'identità verificata (mTLS, SPIFFE/SPIRE)
  2. Autorizzazione: ogni chiamata verifica se l'identità è autorizzata
  3. Rete: NetworkPolicy Kubernetes blocca tutto per default
  4. Dati: cifrati at rest e in transit
  5. Osservabilità: tutto loggato, alert su anomalie

IN KUBERNETES:
  ✓ PodSecurity Standards (Restricted): massima sicurezza
  ✓ NetworkPolicy: default-deny-all + allow esplicito
  ✓ RBAC: least privilege per ogni ServiceAccount
  ✓ Istio mTLS: autenticazione mutua tra servizi
  ✓ OPA/Kyverno: policy enforcement all'admission
```

---

## PART B: SUPPLY CHAIN SECURITY — TRIVY E GITLEAKS

### Esercizio B1: Scanning Container con Trivy

```bash
cd ~/security-lab

# === TRIVY: VULNERABILITY SCANNER UNIVERSALE ===
# Trivy scansiona: immagini Docker, filesystem, repository Git,
# file IaC (Terraform, Helm, Kubernetes YAML), SBOMs

echo "=== TRIVY CONTAINER SCAN ==="

# Scansione immagine: find vulnerabilità HIGH e CRITICAL
# nginx:1.24 è intenzionalmente vecchia per mostrare CVE
trivy image \
  --severity HIGH,CRITICAL \
  --format table \
  nginx:1.24-alpine

echo ""
echo "=== TRIVY CON OUTPUT JSON (per CI/CD) ==="
trivy image \
  --severity CRITICAL \
  --format json \
  --output trivy/nginx-report.json \
  nginx:1.24-alpine 2>/dev/null

# Estrarre sommario
python3 << 'PYEOF'
import json, sys

try:
    with open("trivy/nginx-report.json") as f:
        report = json.load(f)
    
    critical_cves = []
    for result in report.get("Results", []):
        for vuln in result.get("Vulnerabilities", []):
            if vuln.get("Severity") == "CRITICAL":
                critical_cves.append({
                    "id": vuln["VulnerabilityID"],
                    "package": vuln["PkgName"],
                    "fixed_in": vuln.get("FixedVersion", "non fixata")
                })
    
    print(f"CVE CRITICAL trovate: {len(critical_cves)}")
    for cve in critical_cves[:5]:
        print(f"  {cve['id']}: {cve['package']} → fix: {cve['fixed_in']}")
    if len(critical_cves) > 5:
        print(f"  ... e altre {len(critical_cves) - 5}")
except FileNotFoundError:
    print("[INFO] Nessun report trovato (trivy potrebbe non aver trovato CVE CRITICAL)")
PYEOF

echo ""
echo "=== TRIVY KUBERNETES CLUSTER SCAN ==="
# Scansione cluster Kubernetes attivo (analizza tutti i workload)
trivy k8s --report=summary cluster 2>/dev/null || \
  echo "[INFO] Nessun cluster attivo — simulazione scan"

echo ""
echo "=== TRIVY SCAN DOCKERFILE/IaC ==="
# Creare un Dockerfile con problemi intenzionali per dimostrazione
cat > trivy/Dockerfile.bad << 'EOF'
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y curl wget
ENV AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
ENV DATABASE_PASSWORD=supersecret123
USER root
COPY . /app
RUN chmod 777 /app
CMD ["/bin/bash"]
EOF

trivy config trivy/ --severity HIGH,CRITICAL 2>/dev/null || \
  trivy fs --security-checks config trivy/ 2>/dev/null
```

---

### Esercizio B2: Secret Scanning con gitleaks

```bash
cd ~/security-lab

echo "=== GITLEAKS: SECRET DETECTION ==="

# Creare un repo di test con segreti intenzionali
mkdir -p gitleaks/test-repo
cd gitleaks/test-repo

git init -q
git config user.email "test@lab.local"
git config user.name "Lab Test"

# File con segreti simulati (NON reali — solo per dimostrazione)
cat > config.py << 'EOF'
# ATTENZIONE: Questo è un file di DEMO per mostrare come gitleaks funziona
# MAI inserire credenziali reali nel codice!

# Simulazione di segreti (pattern riconosciuto da gitleaks)
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"          # AWS Access Key (simulata)
GITHUB_TOKEN = "ghp_FakeTokenForDemoOnly123456789"  # GitHub token (simulato)
DB_PASSWORD = "postgres://user:p@ssw0rd@host/db"   # Connection string con password

# Questo invece NON è un segreto (valore ovviamente placeholder)
API_KEY = "your-api-key-here"
EOF

cat > application.yaml << 'EOF'
database:
  host: prod-db.internal
  port: 5432
  password: "hunter2"    # gitleaks rileva "password:" seguita da valore non-placeholder
  
stripe:
  secret_key: "sk_test_FakeStripeKeyForDemoOnly"
EOF

git add -A && git commit -m "Aggiunge configurazione (con segreti accidentali)"

# Creare un secondo commit "pulito"
cat > clean.py << 'EOF'
import os
# Buona pratica: leggere segreti da variabili d'ambiente
DB_URL = os.environ.get("DATABASE_URL")
API_KEY = os.environ.get("API_KEY")

if not DB_URL:
    raise RuntimeError("DATABASE_URL non configurata")
EOF

git add clean.py && git commit -m "Aggiunge accesso sicuro ai segreti tramite env vars"

cd ~/security-lab

echo "=== SCAN REPO GIT CON GITLEAKS ==="
gitleaks detect \
  --source gitleaks/test-repo \
  --verbose \
  --report-format json \
  --report-path gitleaks/findings.json \
  2>&1 | head -40

echo ""
echo "=== SOMMARIO FINDINGS ==="
python3 << 'PYEOF'
import json

try:
    with open("gitleaks/findings.json") as f:
        findings = json.load(f)
    
    if not findings:
        print("[OK] Nessun segreto trovato")
    else:
        print(f"[WARN] Trovati {len(findings)} segreti potenziali:")
        for f in findings:
            print(f"  → {f.get('RuleID', '?')}: {f.get('Description', '')} in {f.get('File', '?')}:{f.get('StartLine', '?')}")
            secret = f.get('Secret', '')
            if secret:
                masked = secret[:4] + "***" + secret[-2:] if len(secret) > 6 else "***"
                print(f"    Secret: {masked}")
except (FileNotFoundError, json.JSONDecodeError):
    print("[INFO] Nessun report trovato")
PYEOF

echo ""
echo "=== .GITLEAKS.TOML — CONFIGURAZIONE CUSTOM ==="
cat > ~/security-lab/.gitleaks.toml << 'EOF'
# Configurazione gitleaks per il progetto
title = "security-lab gitleaks config"

[extend]
useDefault = true   # include tutte le regole default

# Escludere percorsi non rilevanti
[allowlist]
description = "File di test e documentazione"
paths = [
  '''gitleaks/test-repo''',    # esclude il repo di test (demo intenzionale)
  '''.*_test\.py$''',          # file di test
  '''.*/testdata/.*'''         # fixture di test
]

# Regola custom per API keys proprietarie
[[rules]]
id = "custom-internal-api-key"
description = "Chiave API interna aziendale"
regex = '''INTERNAL_[A-Z0-9]{32}'''
severity = "critical"
EOF

echo "[OK] .gitleaks.toml configurato"

echo ""
echo "=== INTEGRAZIONE PRE-COMMIT HOOK ==="
cat << 'HOOK'
# Aggiungere al file .git/hooks/pre-commit:
#!/bin/bash
gitleaks protect --staged --config .gitleaks.toml
if [ $? -ne 0 ]; then
    echo "STOP: gitleaks ha trovato segreti nel commit!"
    echo "Rimuovere i segreti prima di procedere."
    exit 1
fi
HOOK
```

---

## PART C: KYVERNO — POLICY ADMISSION CONTROL

### Esercizio C1: Installazione e Policy di Base

```bash
cd ~/security-lab

echo "=== KYVERNO — POLICY ADMISSION CONTROLLER ==="

# Installare Kyverno via Helm
helm repo add kyverno https://kyverno.github.io/kyverno/ --force-update
helm repo update

helm upgrade --install kyverno kyverno/kyverno \
  --namespace kyverno \
  --create-namespace \
  --set replicaCount=1 \
  --wait \
  --timeout 120s

kubectl -n kyverno get pods

echo "[OK] Kyverno installato"

# === POLICY 1: Vietare tag 'latest' ===
cat > kyverno/policy-no-latest-tag.yaml << 'EOF'
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-latest-tag
  annotations:
    policies.kyverno.io/title: "Vietare tag :latest"
    policies.kyverno.io/description: >-
      Il tag :latest non è riproducibile — due deploy dello stesso manifest
      possono usare immagini diverse. Ogni immagine deve avere un tag specifico.
spec:
  validationFailureAction: Enforce   # blocca il deploy
  background: true                   # controlla anche risorse esistenti
  rules:
    - name: require-image-tag
      match:
        any:
          - resources:
              kinds: [Pod]
              namespaces: ["default", "production"]
      validate:
        message: "Tag :latest vietato. Usare un tag specifico (es. nginx:1.27.0)"
        pattern:
          spec:
            containers:
              - image: "!*:latest"
EOF

kubectl apply -f kyverno/policy-no-latest-tag.yaml

# === POLICY 2: Resource limits obbligatori ===
cat > kyverno/policy-require-limits.yaml << 'EOF'
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
  annotations:
    policies.kyverno.io/title: "Richiedere resource limits"
    policies.kyverno.io/description: >-
      Senza limits, un container può consumare tutta la CPU/RAM del nodo.
      Tutti i container devono dichiarare requests e limits.
spec:
  validationFailureAction: Enforce
  rules:
    - name: require-cpu-memory-limits
      match:
        any:
          - resources:
              kinds: [Pod]
              namespaces: ["default", "production"]
      validate:
        message: "Tutti i container devono avere resource limits (memory e cpu)"
        pattern:
          spec:
            containers:
              - resources:
                  limits:
                    memory: "?*"
                    cpu: "?*"
                  requests:
                    memory: "?*"
                    cpu: "?*"
EOF

kubectl apply -f kyverno/policy-require-limits.yaml

# === POLICY 3: Rootless FS ===
cat > kyverno/policy-readonly-rootfs.yaml << 'EOF'
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-readonly-rootfs
  annotations:
    policies.kyverno.io/title: "Richiedere root filesystem read-only"
    policies.kyverno.io/description: >-
      Un container con filesystem read-only non può essere usato per
      installare malware persistente su disco. I dati mutabili devono
      usare volume emptyDir o PVC espliciti.
spec:
  validationFailureAction: Warn   # warn invece di enforce durante transizione
  rules:
    - name: require-readonly-rootfs
      match:
        any:
          - resources:
              kinds: [Pod]
              namespaces: ["production"]
      validate:
        message: "Il filesystem root deve essere read-only: securityContext.readOnlyRootFilesystem: true"
        pattern:
          spec:
            containers:
              - securityContext:
                  readOnlyRootFilesystem: true
EOF

kubectl apply -f kyverno/policy-readonly-rootfs.yaml

echo "[OK] Policy Kyverno applicate:"
kubectl get clusterpolicy
```

---

### Esercizio C2: Testare le Policy

```bash
echo "=== TEST POLICY KYVERNO ==="

# Test 1: Pod con tag :latest → deve essere BLOCCATO
echo "Test 1: Pod con :latest (deve fallire)..."
kubectl run test-latest --image=nginx:latest --dry-run=server 2>&1 && \
  echo "[FAIL] Policy non ha bloccato :latest" || \
  echo "[OK] Policy ha bloccato :latest correttamente"

# Test 2: Pod senza resource limits → deve essere BLOCCATO
echo ""
echo "Test 2: Pod senza limits (deve fallire)..."
kubectl run test-no-limits --image=nginx:1.27 --dry-run=server 2>&1 && \
  echo "[FAIL] Policy non ha bloccato l'assenza di limits" || \
  echo "[OK] Policy ha bloccato l'assenza di limits"

# Test 3: Pod conforme → deve passare
echo ""
echo "Test 3: Pod conforme (deve passare)..."
cat << 'EOF' | kubectl apply --dry-run=server -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-compliant
  namespace: default
spec:
  containers:
    - name: nginx
      image: nginx:1.27.0
      resources:
        requests:
          cpu: "100m"
          memory: "128Mi"
        limits:
          cpu: "200m"
          memory: "256Mi"
      securityContext:
        readOnlyRootFilesystem: false  # namespace default ha solo Warn
        allowPrivilegeEscalation: false
        runAsNonRoot: true
        runAsUser: 1000
EOF
echo "[OK] Pod conforme accettato"

echo ""
echo "=== KYVERNO POLICY REPORT ==="
kubectl get policyreport -A 2>/dev/null | head -20
```

---

## PART D: FALCO — RUNTIME SECURITY

### Esercizio D1: Installare e Configurare Falco

```bash
cd ~/security-lab

echo "=== FALCO — RUNTIME SECURITY ==="

# Falco monitora syscall a livello kernel
# Installa via Helm con driver eBPF (non richiede kernel headers)
helm repo add falcosecurity https://falcosecurity.github.io/charts --force-update
helm repo update

helm upgrade --install falco falcosecurity/falco \
  --namespace falco \
  --create-namespace \
  --set driver.kind=modern_ebpf \   # eBPF moderno (kernel 5.8+)
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true \
  --set collectors.kubernetes.enabled=true \
  --wait \
  --timeout 120s

kubectl -n falco get pods

echo "[OK] Falco installato"

# === REGOLE FALCO CUSTOM ===
cat > falco/custom-rules.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: falco-custom-rules
  namespace: falco
data:
  custom-rules.yaml: |
    # Regola 1: Shell aperta in container in produzione
    - rule: Terminal shell in production container
      desc: Aperta una shell interattiva in un container in namespace production
      condition: >
        spawned_process
        and container
        and k8s.ns.name = "production"
        and shell_procs
        and proc.tty != 0
      output: >
        Shell interattiva in container produzione
        (user=%user.name container=%container.name image=%container.image.repository
        ns=%k8s.ns.name pod=%k8s.pod.name cmd=%proc.cmdline)
      priority: CRITICAL
      tags: [container, shell, production]
    
    # Regola 2: Lettura file di credenziali
    - rule: Read sensitive file untrusted
      desc: Container legge file sensibili (/etc/shadow, /etc/passwd, .ssh)
      condition: >
        open_read
        and container
        and sensitive_files
        and not proc.name in (trusted_processes)
      output: >
        File sensibile letto da container
        (file=%fd.name process=%proc.name container=%container.name)
      priority: WARNING
      tags: [container, filesystem, credentials]
    
    # Regola 3: Scrittura in /etc all'interno del container
    - rule: Write in /etc
      desc: Un processo nel container tenta di scrivere in /etc
      condition: >
        open_write
        and container
        and fd.directory = /etc
      output: >
        Scrittura in /etc rilevata
        (file=%fd.name container=%container.name image=%container.image.repository)
      priority: ERROR
      tags: [container, filesystem]
    
    # Lista macro helper
    - macro: shell_procs
      condition: proc.name in (bash, sh, zsh, ksh, fish, dash)
    
    - macro: sensitive_files
      condition: >
        fd.name startswith /etc/shadow
        or fd.name startswith /etc/sudoers
        or fd.name startswith /root/.ssh
        or fd.name startswith /etc/pam.d
    
    - macro: trusted_processes
      condition: proc.name in (sshd, systemd, login)
EOF

kubectl apply -f falco/custom-rules.yaml

# Riavviare Falco per caricare le regole custom
kubectl -n falco rollout restart daemonset/falco
kubectl -n falco rollout status daemonset/falco --timeout=60s

echo "[OK] Regole Falco custom applicate"
```

---

### Esercizio D2: Testare il Detection di Falco

```bash
echo "=== TEST FALCO DETECTION ==="

# Creare un pod di test per triggerare le regole Falco
kubectl run falco-test --image=nginx:1.27 --restart=Never

echo "Pod test avviato. Attendo ready..."
kubectl wait --for=condition=Ready pod/falco-test --timeout=60s

echo ""
echo "--- Azione 1: Aprire una shell nel container (deve triggerare alert) ---"
kubectl exec falco-test -- /bin/sh -c "ls /etc" 2>/dev/null
echo "[INFO] Shell eseguita nel container"

echo ""
echo "--- Azione 2: Leggere /etc/passwd (file sensibile) ---"
kubectl exec falco-test -- cat /etc/passwd 2>/dev/null | head -3
echo "[INFO] /etc/passwd letto"

echo ""
echo "--- Vedere gli alert Falco (ultimi 30 eventi) ---"
kubectl -n falco logs -l app.kubernetes.io/name=falco --tail=30 2>/dev/null | \
  grep -E "(CRITICAL|WARNING|ERROR)" | tail -10 || \
  echo "[INFO] Nessun alert visibile nei log (potrebbero essere in falcosidekick-ui)"

echo ""
echo "[INFO] Falco Sidekick UI: kubectl -n falco port-forward svc/falco-falcosidekick-ui 2802:2802"

# Pulizia pod test
kubectl delete pod falco-test --grace-period=0
```

---

## PART E: RBAC AUDIT

### Esercizio E1: Audit dei Permessi Kubernetes

```bash
cd ~/security-lab

echo "=== KUBERNETES RBAC AUDIT ==="

# kubectl-who-can: strumento per verificare chi può fare cosa
# Alternativa: usare audit-log di Kubernetes + analisi manuale

# Creare un ServiceAccount con troppi permessi (esempio negativo)
cat > kyverno/rbac-demo.yaml << 'EOF'
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: over-privileged-sa
  namespace: default

---
# PERICOLOSO: accesso a tutto (cluster-admin è anti-pattern)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: over-privileged-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin    # SOLO ADMINS DEVONO AVERE QUESTO
subjects:
  - kind: ServiceAccount
    name: over-privileged-sa
    namespace: default

---
# Corretto: ServiceAccount con permessi minimi necessari
apiVersion: v1
kind: ServiceAccount
metadata:
  name: order-processor-sa
  namespace: default

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: order-processor-role
  namespace: default
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list"]
    resourceNames: ["order-config"]  # solo la ConfigMap specifica
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list"]           # sola lettura, solo pod stesso namespace

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: order-processor-binding
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: order-processor-role
subjects:
  - kind: ServiceAccount
    name: order-processor-sa
    namespace: default
EOF

kubectl apply -f kyverno/rbac-demo.yaml

echo ""
echo "=== AUDIT: CHI PUÒ FARE COSA ==="

# Verificare se la SA over-privileged può listare secrets (dovrebbe potere - è admin)
kubectl auth can-i list secrets \
  --as=system:serviceaccount:default:over-privileged-sa 2>/dev/null && \
  echo "[WARN] over-privileged-sa può listare secrets (troppi permessi!)" || \
  echo "[INFO] over-privileged-sa NON può listare secrets"

# Verificare se la SA order-processor può listare secrets (NON deve potere)
kubectl auth can-i list secrets \
  --as=system:serviceaccount:default:order-processor-sa 2>/dev/null && \
  echo "[FAIL] order-processor-sa può listare secrets (bug nella policy!)" || \
  echo "[OK] order-processor-sa NON può listare secrets (least privilege rispettato)"

# Verificare se order-processor può leggere la configmap specifica
kubectl auth can-i get configmaps/order-config \
  --as=system:serviceaccount:default:order-processor-sa 2>/dev/null && \
  echo "[OK] order-processor-sa può leggere order-config (permesso corretto)" || \
  echo "[INFO] order-processor-sa non può leggere order-config (creare la ConfigMap)"

echo ""
echo "=== REPORT RBAC: CLUSTER ROLE BINDINGS PERICOLOSI ==="
# Trovare tutti i ClusterRoleBinding che danno cluster-admin
echo "ClusterRoleBinding con cluster-admin:"
kubectl get clusterrolebindings -o json 2>/dev/null | \
  python3 << 'PYEOF'
import json, sys

data = json.load(sys.stdin)
for item in data.get("items", []):
    role = item.get("roleRef", {})
    if role.get("name") == "cluster-admin":
        name = item.get("metadata", {}).get("name", "?")
        subjects = item.get("subjects", [])
        for s in subjects:
            kind = s.get("kind", "?")
            subj_name = s.get("name", "?")
            ns = s.get("namespace", "cluster-level")
            print(f"  [WARN] {name}: {kind}/{subj_name} ({ns})")
PYEOF

echo ""
echo "=== SCRIPT AUDIT RBAC AUTOMATICO ==="
cat > scripts/rbac-audit.sh << 'EOF'
#!/bin/bash
# RBAC Audit: trova permessi eccessivi

echo "=== RBAC AUDIT REPORT ==="
echo "Data: $(date)"
echo ""

echo "--- 1. ServiceAccount con ClusterRole admin ---"
kubectl get clusterrolebindings -o json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for b in data['items']:
    if b['roleRef']['name'] in ['cluster-admin', 'admin']:
        for s in b.get('subjects', []):
            if s['kind'] == 'ServiceAccount':
                print(f\"  {b['metadata']['name']}: {s.get('namespace','?')}/{s['name']}\")
"

echo ""
echo "--- 2. Wildcard permissions (* verbs o * resources) ---"
kubectl get clusterroles -o json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data['items']:
    name = r['metadata']['name']
    if name.startswith('system:'):
        continue
    for rule in r.get('rules', []):
        if '*' in rule.get('verbs', []) or '*' in rule.get('resources', []):
            print(f'  {name}: verbs={rule.get(\"verbs\", [])} resources={rule.get(\"resources\", [])}')
"

echo ""
echo "--- 3. ServiceAccount senza RoleBinding (orfani) ---"
for sa in $(kubectl get sa -A -o jsonpath='{.items[*].metadata.name}'); do
    ns=$(kubectl get sa -A -o jsonpath="{.items[?(@.metadata.name==\"$sa\")].metadata.namespace}")
    echo "  Found SA: $ns/$sa"
done 2>/dev/null | head -10

echo ""
echo "=== FINE AUDIT RBAC ==="
EOF

chmod +x scripts/rbac-audit.sh
bash scripts/rbac-audit.sh
```

---

## PART F: SECCOMP — FILTRO SYSCALL

### Esercizio F1: Profili Seccomp

```bash
cd ~/security-lab

echo "=== SECCOMP — FILTRO SYSCALL A LIVELLO KERNEL ==="

# Seccomp (Secure Computing Mode) permette di specificare
# quale sottoinsieme di syscall Linux un processo può usare.
# Un container nginx normale non ha bisogno di ptrace, mount,
# o di creare socket raw — se li usa, è sospetto.

# Creare un profilo seccomp custom per nginx
mkdir -p /var/lib/kubelet/seccomp/profiles 2>/dev/null || \
  mkdir -p ~/.kube/seccomp/profiles

cat > ~/.kube/seccomp/profiles/nginx-restricted.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_X32"],
  "syscalls": [
    {
      "names": [
        "accept", "accept4", "access", "arch_prctl",
        "bind", "brk", "capget", "capset",
        "chdir", "chmod", "chown", "clock_gettime",
        "clone", "close", "connect", "dup", "dup2",
        "epoll_create", "epoll_create1", "epoll_ctl", "epoll_wait",
        "execve", "exit", "exit_group",
        "fchdir", "fcntl", "fork", "fstat", "fstatfs",
        "futex", "getdents64", "getegid", "geteuid",
        "getgid", "getpeername", "getpgrp", "getpid",
        "getppid", "getrlimit", "getrusage", "getsockname",
        "getsockopt", "gettid", "getuid",
        "inotify_add_watch", "inotify_init", "inotify_init1",
        "ioctl", "kill",
        "listen", "lseek", "lstat",
        "mmap", "mprotect", "mremap", "munmap",
        "nanosleep", "newfstatat", "open", "openat",
        "pipe", "pipe2", "poll", "prctl",
        "pread64", "pwrite64",
        "read", "readlink", "readv",
        "recv", "recvfrom", "recvmsg",
        "rename", "rt_sigaction", "rt_sigprocmask", "rt_sigreturn",
        "select", "send", "sendfile", "sendmsg", "sendto",
        "set_robust_list", "setgid", "setgroups", "setuid",
        "setsockopt", "shutdown", "sigaltstack",
        "socket", "socketpair", "stat", "statfs",
        "symlink", "tgkill", "truncate",
        "umask", "uname", "unlink",
        "vfork", "wait4", "waitid", "write", "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
EOF

echo "[OK] Profilo seccomp creato"

# Applicare il profilo seccomp a un pod
cat > workloads/pod-seccomp.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: nginx-seccomp
  namespace: default
spec:
  securityContext:
    # Profilo seccomp a livello pod
    seccompProfile:
      type: RuntimeDefault   # usa il profilo default del runtime (containerd)
      # Per profilo custom (richiede file sul nodo):
      # type: Localhost
      # localhostProfile: profiles/nginx-restricted.json
  
  containers:
    - name: nginx
      image: nginx:1.27.0
      ports:
        - containerPort: 80
      
      securityContext:
        # Seccomp a livello container (override del profilo pod)
        seccompProfile:
          type: RuntimeDefault
        
        # Altri security context
        allowPrivilegeEscalation: false    # non può diventare root
        readOnlyRootFilesystem: true       # filesystem immutabile
        runAsNonRoot: true                 # deve girare come non-root
        runAsUser: 101                     # nginx user
        capabilities:
          drop: ["ALL"]                    # rimuove TUTTE le capabilities Linux
          add: ["NET_BIND_SERVICE"]        # solo quella necessaria per porta 80
      
      resources:
        requests:
          cpu: "100m"
          memory: "64Mi"
        limits:
          cpu: "200m"
          memory: "128Mi"
      
      volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: var-cache
          mountPath: /var/cache/nginx
        - name: var-run
          mountPath: /var/run
  
  volumes:
    - name: tmp
      emptyDir: {}
    - name: var-cache
      emptyDir: {}
    - name: var-run
      emptyDir: {}
EOF

kubectl apply -f workloads/pod-seccomp.yaml
kubectl wait --for=condition=Ready pod/nginx-seccomp --timeout=60s && \
  echo "[OK] Pod con seccomp e read-only FS avviato" || \
  echo "[INFO] Pod potrebbe richiedere aggiustamenti"

echo ""
echo "=== VERIFICA SECURITY CONTEXT ==="
kubectl get pod nginx-seccomp -o jsonpath='{.spec.containers[0].securityContext}' | \
  python3 -m json.tool

kubectl delete pod nginx-seccomp --grace-period=0 2>/dev/null
```

---

## PART G: INCIDENT RESPONSE

### Esercizio G1: Playbook di Risposta agli Incidenti

```bash
cd ~/security-lab

cat > scripts/incident-response.sh << 'SCRIPT'
#!/bin/bash
# PLAYBOOK: Risposta a container compromesso
# Trigger: Falco alert CRITICAL nel namespace production
# Autore: Security Operations

NAMESPACE="${1:-production}"
POD_NAME="${2:-}"

if [ -z "$POD_NAME" ]; then
    echo "Uso: $0 <namespace> <pod-name>"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
FORENSICS_DIR="./forensics/${TIMESTAMP}-${POD_NAME}"
mkdir -p "$FORENSICS_DIR"

echo "=== INCIDENT RESPONSE PLAYBOOK ==="
echo "Timestamp: $TIMESTAMP"
echo "Pod: ${NAMESPACE}/${POD_NAME}"
echo "Report: $FORENSICS_DIR"
echo ""

# FASE 1: RACCOGLIERE EVIDENZE (prima di toccare il pod)
echo "--- FASE 1: RACCOLTA EVIDENZE ---"

# 1a. Metadata del pod
kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o yaml > "$FORENSICS_DIR/pod-manifest.yaml"
echo "[OK] Manifest pod salvato"

# 1b. Log del pod (current + previous se crashato)
kubectl logs "$POD_NAME" -n "$NAMESPACE" > "$FORENSICS_DIR/pod-logs-current.txt" 2>&1
kubectl logs "$POD_NAME" -n "$NAMESPACE" --previous > "$FORENSICS_DIR/pod-logs-previous.txt" 2>&1
echo "[OK] Log pod salvati"

# 1c. Processi in esecuzione
kubectl exec "$POD_NAME" -n "$NAMESPACE" -- ps aux > "$FORENSICS_DIR/processes.txt" 2>&1 || \
    echo "[WARN] ps non disponibile nel container"

# 1d. Connessioni di rete
kubectl exec "$POD_NAME" -n "$NAMESPACE" -- ss -tulnp > "$FORENSICS_DIR/network.txt" 2>&1 || \
    kubectl exec "$POD_NAME" -n "$NAMESPACE" -- netstat -tulnp > "$FORENSICS_DIR/network.txt" 2>&1 || \
    echo "[WARN] Strumenti di rete non disponibili"

# 1e. Variabili d'ambiente (attenzione: potrebbero contenere segreti!)
kubectl exec "$POD_NAME" -n "$NAMESPACE" -- env > "$FORENSICS_DIR/env-vars.txt" 2>&1
echo "[WARN] env-vars.txt può contenere segreti — proteggere il file!"

# 1f. Falco alert correlati
kubectl -n falco logs -l app.kubernetes.io/name=falco --since=1h 2>/dev/null | \
    grep "$POD_NAME" > "$FORENSICS_DIR/falco-alerts.txt" 2>&1 || \
    echo "[INFO] Log Falco non disponibili"

echo ""
echo "--- FASE 2: CONTENIMENTO ---"

# 2a. Annotare il pod con timestamp incidente (per audit trail)
kubectl annotate pod "$POD_NAME" -n "$NAMESPACE" \
    "security.io/incident-detected=${TIMESTAMP}" \
    "security.io/incident-status=investigating" \
    --overwrite 2>/dev/null
echo "[OK] Pod annotato con incidente"

# 2b. Isolare il pod: applicare NetworkPolicy deny-all
cat << EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: quarantine-${POD_NAME}
  namespace: ${NAMESPACE}
  annotations:
    security.io/reason: "Quarantena automatica incidente ${TIMESTAMP}"
spec:
  podSelector:
    matchLabels:
      app: $(kubectl get pod "$POD_NAME" -n "$NAMESPACE" \
        -o jsonpath='{.metadata.labels.app}' 2>/dev/null || echo "$POD_NAME")
  policyTypes: [Ingress, Egress]
  # nessuna regola = nessun traffico consentito
EOF
echo "[OK] Pod isolato con NetworkPolicy quarantena"

# 2c. Avvisare il team
echo ""
echo "[ACTION REQUIRED] Notificare il team di sicurezza!"
echo "  - Email: security@azienda.com"
echo "  - Slack: #security-incidents"
echo "  - Dettagli: ${FORENSICS_DIR}/"

echo ""
echo "--- FASE 3: ERADICAZIONE ---"
echo "[MANUAL] Analizzare le evidenze in $FORENSICS_DIR"
echo "[MANUAL] Determinare il vettore di attacco"
echo "[MANUAL] Aggiornare le policy per prevenire la ripetizione"

echo ""
echo "--- FASE 4: RECOVERY ---"
echo "[MANUAL] Fare rollback a una versione nota pulita"
echo "[MANUAL] Eseguire Trivy scan sull'immagine nuova"
echo "[MANUAL] Rimuovere NetworkPolicy quarantena dopo verifica"
echo "         kubectl delete networkpolicy quarantine-${POD_NAME} -n ${NAMESPACE}"

echo ""
echo "=== INCIDENTE DOCUMENTATO: $FORENSICS_DIR ==="
ls -la "$FORENSICS_DIR"
SCRIPT

chmod +x scripts/incident-response.sh
echo "[OK] Playbook incident response creato: scripts/incident-response.sh"
echo "Uso: bash scripts/incident-response.sh <namespace> <pod-name>"
```

---

## PART H: CHECKLIST FINALE

```bash
echo "=== SECURITY CHECKLIST — AUDIT COMPLETO ==="

cat << 'CHECKLIST'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECURITY POSTURE CHECKLIST — Kubernetes/Container Platform
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUPPLY CHAIN:
[ ] Trivy scan in CI/CD (blocca su HIGH/CRITICAL)
[ ] gitleaks pre-commit hook abilitato
[ ] Immagini base aggiornate mensilmente
[ ] Dipendenze con versioni pinnate (no "latest" in requirements)
[ ] SBOM generato per ogni release (syft)
[ ] Registry privato con vulnerability scanning automatico

ADMISSION CONTROL (Kyverno/OPA):
[ ] Vietato tag :latest
[ ] Resource limits obbligatori
[ ] Container non privilegiati per default
[ ] read-only root filesystem
[ ] Registry allowlist (solo registry approvati)
[ ] No hostPath mounts in produzione
[ ] seccompProfile: RuntimeDefault come minimo

RUNTIME:
[ ] Falco installato e configurato
[ ] Regole custom per casi d'uso specifici
[ ] Alert inviati a SIEM/Slack
[ ] seccomp profile: RuntimeDefault o Localhost custom
[ ] AppArmor/SELinux abilitato dove supportato
[ ] runAsNonRoot: true ovunque

RETE:
[ ] NetworkPolicy default-deny in ogni namespace produzione
[ ] Istio mTLS STRICT (se usato service mesh)
[ ] Nessuna porta esposta non necessaria
[ ] Egress filtrato (solo destinazioni note)

ACCESSO:
[ ] RBAC audit eseguito (nessun ServiceAccount con cluster-admin)
[ ] Nessun wildcard (*) in ClusterRole production
[ ] ServiceAccount dedicata per ogni deployment
[ ] Audit log Kubernetes abilitato
[ ] kubectl exec vietato in produzione (RBAC)

RISPOSTA INCIDENTI:
[ ] Playbook documentato e testato (tabletop exercise)
[ ] Contatti di sicurezza aggiornati
[ ] Processo di forensics definito
[ ] RTO/RPO definiti
[ ] Post-mortem template disponibile
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHECKLIST
```

---

## Conclusioni e Prossimi Passi

```
SICUREZZA PIATTAFORME — RIEPILOGO:

DEFENSE IN DEPTH:
  ✓ Ogni strato assume che il precedente possa fallire
  ✓ Supply chain → Admission → Runtime → Risposta
  ✓ Automazione: scanner in CI/CD, policy enforcement, alert automatici

SUPPLY CHAIN:
  ✓ Trivy: scan vulnerabilità immagini, IaC, filesystem
  ✓ gitleaks: nessun segreto nel codice sorgente
  ✓ Regola: blocco su CRITICAL in CI/CD, warning su HIGH

KYVERNO POLICY:
  ✓ disallow-latest-tag: riproducibilità garantita
  ✓ require-resource-limits: no runaway containers
  ✓ require-readonly-rootfs: resistenza a malware persistente
  ✓ Enforce = blocca, Warn = avvisa (transizione graduale)

FALCO RUNTIME:
  ✓ Monitora syscall a livello kernel via eBPF
  ✓ Alert su: shell in container, lettura file sensibili, privilege escalation
  ✓ Regole custom per casi aziendali specifici
  ✓ Output → SIEM, Slack, webhook

RBAC AUDIT:
  ✓ Principio least privilege
  ✓ Nessun ServiceAccount con cluster-admin
  ✓ Nessun wildcard nelle ClusterRole di produzione
  ✓ Script di audit automatico

SECCOMP:
  ✓ RuntimeDefault come minimo per ogni workload
  ✓ Profili custom per servizi ad alto rischio
  ✓ drop: ALL + add solo capabilities necessarie

INCIDENT RESPONSE:
  ✓ Raccogliere evidenze PRIMA di toccare il pod
  ✓ Isolare con NetworkPolicy (quarantena)
  ✓ Annotare per audit trail
  ✓ Playbook scritto e testato

CITAZIONE CHIAVE:
  "Security is not a product, it's a process."
  "Un sistema non è sicuro finché non è dimostrato; è vulnerabile finché non è controllato."
```

**Prossimi tutorial:**
- `tutorial_plat14_compliance_lab.md` — OPA, checkov, audit log immutabile
- `tutorial_plat15_secrets_management_lab.md` — Vault, External Secrets Operator

```bash
# Pulizia lab
kubectl delete -f kyverno/ --ignore-not-found=true
kubectl delete -f workloads/ --ignore-not-found=true
helm uninstall kyverno -n kyverno 2>/dev/null || true
helm uninstall falco -n falco 2>/dev/null || true
rm -rf ~/security-lab

echo "[OK] Lab Sicurezza Piattaforme completato"
```

---

> **Nota versioni:** Tutorial validato con Trivy v0.57.0 (ottobre 2024), gitleaks v8.21.x (2024),
> Kyverno 1.12.x (Helm chart kyverno/kyverno 3.2.x), Falco 0.38.x (Helm chart 4.x),
> Kubernetes 1.29-1.32, Seccomp/seccompProfile API stabile da Kubernetes 1.22.
> CIS Kubernetes Benchmark v1.9.0 (2024) raccomanda: seccomp RuntimeDefault,
> read-only root filesystem, non-root user, no privilege escalation.
> NIST CSF 2.0 (febbraio 2024): aggiunge funzione "Govern" alle 5 originali (ID, PR, DE, RS, RC).
