# Tutorial: Compliance e Normative — Compliance-as-Code, OPA e Audit Log

> **Documento di riferimento:** `14-compliance.md`
> **Dominio:** Gestione Piattaforme — Sicurezza e Compliance
> **Ambito:** GDPR/NIS2/DORA overview tecnico, compliance-as-code con OPA Gatekeeper e Kyverno, checkov per IaC, audit log immutabile Kubernetes, data classification automatica, report di compliance automatizzati
> **Durata lab:** 5-6 ore
> **Livello:** Avanzato — richiede Kubernetes locale, Python 3.10+, Terraform/OpenTofu
> **Prerequisiti:** K3s o kind cluster locale, helm 3.x, kubectl, OpenTofu/Terraform, checkov
> **Ambiente:** Tutto locale — OPA Gatekeeper su K3s, checkov CLI, script Python per audit report

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI COMPLIANCE LAB ===
echo "=== PREREQUISITI ==="

kubectl version --client --short 2>/dev/null && echo "[OK] kubectl" || echo "[FAIL] kubectl richiesto"
helm version --short 2>/dev/null && echo "[OK] helm" || echo "[FAIL] helm richiesto"
python3 --version && echo "[OK] Python" || echo "[FAIL] Python 3.10+ richiesto"

# Installare checkov (IaC scanner)
pip3 install checkov 2>/dev/null && echo "[OK] checkov" || \
  echo "[INFO] Installare: pip3 install checkov"

# Tool opzionale: conftest (test OPA policy su file YAML)
command -v conftest &>/dev/null && echo "[OK] conftest" || \
  echo "[INFO] conftest opzionale — https://www.conftest.dev"

mkdir -p ~/compliance-lab/{opa,kyverno,checkov,iac,audit,reports}
cd ~/compliance-lab

echo "[OK] Directory lab: ~/compliance-lab"
```

### Architettura Compliance-as-Code

```
┌──────────────────────────────────────────────────────────────────────────┐
│              COMPLIANCE-AS-CODE — AUTOMAZIONE NORMATIVA                  │
│                                                                          │
│  NORMATIVA ──→ POLICY (OPA/Rego) ──→ ENFORCEMENT (Gatekeeper/Kyverno)  │
│                     ↓                        ↓                          │
│  GDPR art.25      "no-PII-in-logs"        Admission webhook K8s         │
│  NIS2 art.21      "encrypted-storage"     CI/CD gate (checkov)          │
│  DORA art.11      "rto-labels-required"   Report periodico              │
│                                                                          │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────┐   │
│  │   IaC SCAN      │   │   K8s POLICY    │   │   AUDIT LOG         │   │
│  │   checkov       │   │   OPA/Kyverno   │   │   Immutabile        │   │
│  │   tfsec/trivy   │   │   Gatekeeper    │   │   API Server audit  │   │
│  └─────────────────┘   └─────────────────┘   └─────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — Normativa EU e Compliance Tecnica

> La compliance non è un documento firmato e archiviato in un cassetto.
> È il risultato quotidiano di mille piccole scelte tecniche:
> "questo log deve mascherare l'email?",
> "questo bucket S3 deve essere cifrato?",
> "questo endpoint restituisce dati personali senza autenticazione?".
> La compliance-as-code trasforma queste domande in policy automatizzate
> che vengono valutate ad ogni deploy, impedendo la deriva dalla norma.

---

### Concetto A1: Il Trio Normativo Europeo 2024-2025

```
GDPR (2016/679) — PROTEZIONE DATI PERSONALI:
  Ambito: tutti coloro che trattano dati di cittadini EU
  Penalty: max 20M€ o 4% del fatturato globale annuo
  
  Requisiti tecnici chiave:
  ├── Privacy by Design (art.25): protezione dati nella progettazione
  ├── Data Minimization: raccogliere solo i dati necessari
  ├── Pseudonymization/Encryption: dati protetti at rest e in transit
  ├── Data Subject Rights: accesso, cancellazione, portabilità in 30 gg
  ├── Breach Notification: notifica all'autorità entro 72 ore
  └── Data Retention: cancellazione quando non più necessari

NIS2 (2022/2555) — SICUREZZA DELLE RETI:
  Ambito: operatori di servizi essenziali + fornitori digitali importanti
  Penalty: max 10M€ o 2% del fatturato per entità essenziali
  Vigenza: ottobre 2024 (recepita in Italy con D.Lgs. 138/2024)
  
  Requisiti tecnici chiave:
  ├── Risk management framework documentato
  ├── Incident response: notifica entro 24h (early warning) + 72h (report)
  ├── Business continuity e disaster recovery testati
  ├── Supply chain security: audit dei fornitori
  ├── Vulnerability disclosure policy
  └── Crittografia end-to-end

DORA (2022/2554) — RESILIENZA DIGITALE SETTORE FINANZIARIO:
  Ambito: istituzioni finanziarie EU (banche, assicurazioni, exchange crypto)
  Vigenza: 17 gennaio 2025
  
  Requisiti tecnici chiave:
  ├── RTO (Recovery Time Objective) documentato per ogni sistema critico
  ├── ICT risk management framework con 4 livelli
  ├── Penetration testing TLPT ogni 3 anni (threat-led)
  ├── Incident classification: Major ICT Incident → notifica 4h
  ├── Third-party risk management: contratti con TPSP conformi
  └── Register of ICT assets: inventario completo

IMPLEMENTAZIONE TECNICA COMUNE:
  ✓ Audit log immutabile per tutte le azioni
  ✓ Data classification: GDPR/DORA distinguono dati ordinari vs speciali
  ✓ Encryption: AES-256 at rest, TLS 1.2+ in transit
  ✓ IAM: principio least privilege + MFA
  ✓ Backup testato: RPO/RTO documentati e verificati
```

---

## PART B: OPA GATEKEEPER — POLICY ENFORCEMENT

### Esercizio B1: Installazione OPA Gatekeeper

```bash
cd ~/compliance-lab

echo "=== OPA GATEKEEPER — POLICY ENFORCEMENT K8S ==="

# OPA Gatekeeper: admission controller che valuta policy Rego
# a ogni CREATE/UPDATE di risorse Kubernetes
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.17.1/deploy/gatekeeper.yaml

echo "Attendo Gatekeeper ready..."
kubectl -n gatekeeper-system rollout status deployment/gatekeeper-controller-manager --timeout=120s

kubectl -n gatekeeper-system get pods

# === CONSTRAINT TEMPLATE: Vietare namespace "default" in produzione ===
cat > opa/constraint-template-required-labels.yaml << 'EOF'
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
  annotations:
    description: >
      Richiede che le risorse abbiano certi label.
      Necessario per: DORA (RTO label), GDPR (data-classification label),
      FinOps (cost-center label), Incident Response (team-owner label).
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items:
                type: object
                properties:
                  key:
                    type: string
                  allowedRegex:
                    type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequiredlabels
        
        violation[{"msg": msg, "details": {"missing_labels": missing}}] {
          provided := {label | input.review.object.metadata.labels[label]}
          required := {label | label := input.parameters.labels[_].key}
          missing := required - provided
          count(missing) > 0
          msg := sprintf("Risorse devono avere i label: %v (mancanti: %v)", [required, missing])
        }
        
        violation[{"msg": msg}] {
          value := input.review.object.metadata.labels[input.parameters.labels[i].key]
          expected := input.parameters.labels[i].allowedRegex
          not re_match(expected, value)
          msg := sprintf("Label '%v' deve corrispondere a regex '%v', valore trovato: '%v'",
            [input.parameters.labels[i].key, expected, value])
        }
EOF

kubectl apply -f opa/constraint-template-required-labels.yaml

# === CONSTRAINT: Richiede label GDPR data-classification ===
cat > opa/constraint-gdpr-labels.yaml << 'EOF'
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: gdpr-data-classification
  annotations:
    description: >
      GDPR Art.25 Privacy by Design: ogni workload deve dichiarare
      la classificazione dei dati trattati. Questo permette di applicare
      controlli differenziati per dati personali vs pubblici.
spec:
  match:
    kinds:
      - apiGroups: ["apps"]
        kinds: ["Deployment"]
    namespaces: ["production", "staging"]
  parameters:
    labels:
      - key: "gdpr.compliance/data-classification"
        allowedRegex: "^(public|internal|confidential|pii|special-category)$"
      - key: "gdpr.compliance/data-retention-days"
        allowedRegex: "^[0-9]+$"
      - key: "team/owner"
        allowedRegex: "^[a-z0-9-]+$"
EOF

kubectl apply -f opa/constraint-gdpr-labels.yaml

# === CONSTRAINT: Richiede label RTO per DORA ===
cat > opa/constraint-dora-labels.yaml << 'EOF'
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: dora-rto-label
  annotations:
    description: >
      DORA Art.11: ogni sistema critico deve documentare RTO/RPO.
      Il label 'dora/rto-minutes' permette la generazione automatica
      del registro ICT assets richiesto dalla normativa.
spec:
  match:
    kinds:
      - apiGroups: ["apps"]
        kinds: ["Deployment"]
    namespaces: ["financial-services"]
  parameters:
    labels:
      - key: "dora/criticality"
        allowedRegex: "^(critical|important|standard)$"
      - key: "dora/rto-minutes"
        allowedRegex: "^(15|30|60|120|240|480)$"
EOF

kubectl apply -f opa/constraint-dora-labels.yaml

echo ""
echo "[OK] Policy OPA Gatekeeper applicate:"
kubectl get constrainttemplate
kubectl get K8sRequiredLabels 2>/dev/null
```

---

### Esercizio B2: Test Policy OPA

```bash
echo "=== TEST POLICY OPA ==="

# Test 1: Deployment SENZA label GDPR → deve fallire in staging/production
echo "Test 1: Deployment senza label GDPR in staging (deve fallire)..."
cat << 'EOF' | kubectl apply -f - 2>&1 | grep -E "(Error|admission|violation|created)"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-no-gdpr-label
  namespace: staging
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test
  template:
    metadata:
      labels:
        app: test
    spec:
      containers:
        - name: nginx
          image: nginx:1.27.0
          resources:
            limits:
              cpu: "100m"
              memory: "64Mi"
            requests:
              cpu: "50m"
              memory: "32Mi"
EOF

# Test 2: Deployment CONFORME con tutti i label
echo ""
echo "Test 2: Deployment conforme con label GDPR (deve passare)..."
cat << 'EOF' | kubectl apply -f - 2>&1 | grep -E "(Error|admission|violation|created|configured)"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-gdpr-compliant
  namespace: default
  labels:
    gdpr.compliance/data-classification: "pii"
    gdpr.compliance/data-retention-days: "365"
    team/owner: "platform-team"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-compliant
  template:
    metadata:
      labels:
        app: test-compliant
        gdpr.compliance/data-classification: "pii"
        gdpr.compliance/data-retention-days: "365"
        team/owner: "platform-team"
    spec:
      containers:
        - name: nginx
          image: nginx:1.27.0
          resources:
            limits:
              cpu: "100m"
              memory: "64Mi"
            requests:
              cpu: "50m"
              memory: "32Mi"
EOF

# Vedere violations esistenti
echo ""
echo "=== GATEKEEPER CONSTRAINT VIOLATIONS ==="
kubectl get K8sRequiredLabels -o json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for item in data.get('items', []):
    name = item['metadata']['name']
    violations = item.get('status', {}).get('violations', [])
    if violations:
        print(f'Constraint {name}: {len(violations)} violazioni')
        for v in violations[:3]:
            print(f'  - {v.get(\"resource\")}: {v.get(\"message\", \"\")[:80]}')
" || echo "[INFO] Nessuna violation o namespace mancante"

# Pulizia test
kubectl delete deployment test-gdpr-compliant 2>/dev/null
```

---

## PART C: CHECKOV — IaC SCANNING

### Esercizio C1: Scan Terraform con checkov

```bash
cd ~/compliance-lab

# Creare configurazione Terraform con vulnerabilità intenzionali
mkdir -p checkov/terraform-bad

cat > checkov/terraform-bad/main.tf << 'EOF'
# ESEMPIO NEGATIVO: violazioni compliance intenzionali per dimostrazione

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

# VIOLAZIONE: bucket S3 pubblico (GDPR art.32 — no protezione adeguata)
resource "aws_s3_bucket" "data" {
  bucket = "company-data-bucket"
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket = aws_s3_bucket.data.id
  # VIOLAZIONE: non blocca accesso pubblico!
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# VIOLAZIONE: nessuna cifratura (GDPR art.32, NIS2 art.21)
# mancano: aws_s3_bucket_server_side_encryption_configuration

# VIOLAZIONE: nessun versioning (DORA: business continuity)
# mancano: aws_s3_bucket_versioning

# VIOLAZIONE: log accessi non abilitati
# mancano: aws_s3_bucket_logging

# VIOLAZIONE: security group troppo permissivo (porta 22 da 0.0.0.0/0)
resource "aws_security_group" "web" {
  name = "web-sg"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # SSH aperto a internet!
  }
}

# VIOLAZIONE: RDS senza encryption at rest
resource "aws_db_instance" "main" {
  engine         = "postgres"
  engine_version = "17.1"
  instance_class = "db.t3.micro"
  storage_encrypted = false    # VIOLAZIONE: GDPR richiede cifratura
  deletion_protection = false  # VIOLAZIONE: DORA resilienza
  backup_retention_period = 0  # VIOLAZIONE: DORA richiede backup
}
EOF

# Creare versione CORRETTA (conforme)
mkdir -p checkov/terraform-good

cat > checkov/terraform-good/main.tf << 'EOF'
# ESEMPIO CORRETTO: configurazione conforme GDPR/NIS2/DORA

terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "company-data-bucket-private"
  
  tags = {
    "gdpr.compliance/data-classification" = "pii"
    "gdpr.compliance/data-retention-days" = "365"
    "dora/criticality"                    = "important"
  }
}

resource "aws_s3_bucket_public_access_block" "data" {
  bucket                  = aws_s3_bucket.data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"  # usa KMS invece di AES256
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_security_group" "web" {
  name = "web-sg"
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # solo HTTPS, no SSH
  }
  # SSH solo da bastion host (CIDR privato)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }
}

resource "aws_db_instance" "main" {
  engine                  = "postgres"
  engine_version          = "17.1"
  instance_class          = "db.t3.micro"
  storage_encrypted       = true    # cifratura at rest
  deletion_protection     = true    # no eliminazione accidentale
  backup_retention_period = 30      # 30 giorni backup (DORA)
  multi_az                = true    # HA cross-AZ
}
EOF

echo "=== CHECKOV SCAN: configurazione NON conforme ==="
checkov -d checkov/terraform-bad \
  --framework terraform \
  --output cli \
  --quiet 2>/dev/null | head -60

echo ""
echo "=== CHECKOV SCAN: configurazione CONFORME ==="
checkov -d checkov/terraform-good \
  --framework terraform \
  --output cli \
  --quiet 2>/dev/null | head -30

echo ""
echo "=== CHECKOV REPORT JSON (per CI/CD gate) ==="
checkov -d checkov/terraform-bad \
  --framework terraform \
  --output json \
  --quiet 2>/dev/null | python3 << 'PYEOF'
import json, sys

try:
    data = json.load(sys.stdin)
    results = data.get("results", {})
    failed = results.get("failed_checks", [])
    passed = results.get("passed_checks", [])
    
    print(f"Passed: {len(passed)}")
    print(f"Failed: {len(failed)}")
    
    # Raggruppare per severità (checkov mappa check a normative)
    critical = [c for c in failed if c.get("check_result", {}).get("result") == "failed"]
    print(f"\nCheck falliti (top 5):")
    for check in critical[:5]:
        print(f"  [{check.get('check_id', '?')}] {check.get('check', '?')[:60]}")
except Exception as e:
    print(f"[INFO] Parsing: {e}")
PYEOF
```

---

## PART D: AUDIT LOG IMMUTABILE

### Esercizio D1: Kubernetes Audit Log

```bash
cd ~/compliance-lab

echo "=== KUBERNETES AUDIT LOG ==="

# Il Kubernetes API Server può loggare ogni azione (chi ha fatto cosa, quando)
# Questo è FONDAMENTALE per GDPR (art.5 accountability), NIS2, DORA

# Configurazione audit policy per K3s
# NOTA: in produzione il file va su ogni control-plane node

cat > audit/audit-policy.yaml << 'EOF'
apiVersion: audit.k8s.io/v1
kind: Policy

# Non loggare richieste banali che creano rumore
omitStages:
  - "RequestReceived"

rules:
  # Regola 1: Log completo per secrets (GDPR — accesso dati sensibili)
  - level: RequestResponse
    verbs: ["get", "list", "create", "update", "delete", "patch"]
    resources:
      - group: ""
        resources: ["secrets"]
    omitManagedFields: false

  # Regola 2: Log per RBAC changes (audit degli accessi)
  - level: RequestResponse
    verbs: ["create", "update", "delete", "patch"]
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["roles", "clusterroles", "rolebindings", "clusterrolebindings"]

  # Regola 3: Log per accesso ai dati (exec, port-forward = azione manuale sospetta)
  - level: Metadata
    verbs: ["create"]
    resources:
      - group: ""
        resources: ["pods/exec", "pods/portforward", "pods/attach"]

  # Regola 4: Log per tutti i workload changes
  - level: Metadata
    verbs: ["create", "update", "delete", "patch"]
    resources:
      - group: "apps"
        resources: ["deployments", "daemonsets", "statefulsets"]

  # Regola 5: Non loggare watch ricorrenti (rumore dal controller manager)
  - level: None
    users: ["system:kube-controller-manager", "system:kube-scheduler"]
    verbs: ["get", "list", "watch"]

  # Default: log metadata per tutto il resto
  - level: Metadata
EOF

echo "[OK] Audit policy Kubernetes creata"

# Script per analizzare audit log
cat > audit/analyze-audit-log.py << 'PYTHON'
"""
Analizzatore audit log Kubernetes per compliance report.
Input: file JSONL con eventi audit Kubernetes
"""
import json
import sys
from collections import defaultdict
from datetime import datetime

def analyze_audit_log(log_file: str):
    """Analizza un audit log Kubernetes e produce report compliance."""
    events = []
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
    except FileNotFoundError:
        print(f"[WARN] File non trovato: {log_file}")
        print("       In K3s: /var/log/kubernetes/audit.log")
        print("       In kubeadm: /var/log/kube-apiserver-audit.log")
        return {}
    
    report = {
        "total_events": len(events),
        "secret_access": [],
        "rbac_changes": [],
        "exec_events": [],
        "users": defaultdict(int),
        "verbs": defaultdict(int),
    }
    
    for event in events:
        user = event.get("user", {}).get("username", "unknown")
        verb = event.get("verb", "")
        resource = event.get("objectRef", {}).get("resource", "")
        namespace = event.get("objectRef", {}).get("namespace", "cluster")
        name = event.get("objectRef", {}).get("name", "")
        timestamp = event.get("requestReceivedTimestamp", "")
        
        report["users"][user] += 1
        report["verbs"][verb] += 1
        
        # Accesso a secrets
        if resource == "secrets":
            report["secret_access"].append({
                "user": user, "verb": verb,
                "name": name, "namespace": namespace,
                "timestamp": timestamp
            })
        
        # Cambi RBAC
        if "rbac.authorization.k8s.io" in event.get("objectRef", {}).get("apiGroup", ""):
            report["rbac_changes"].append({
                "user": user, "verb": verb,
                "resource": resource, "name": name,
                "timestamp": timestamp
            })
        
        # exec/portforward (azione manuale)
        if resource in ["pods/exec", "pods/portforward", "pods/attach"]:
            report["exec_events"].append({
                "user": user, "verb": verb,
                "name": name, "namespace": namespace,
                "timestamp": timestamp
            })
    
    return report


def print_report(report: dict):
    """Stampa report leggibile per audit compliance."""
    if not report:
        return
    
    print("=" * 60)
    print("KUBERNETES AUDIT COMPLIANCE REPORT")
    print(f"Generato: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)
    
    print(f"\nEventi totali analizzati: {report['total_events']}")
    
    print(f"\n--- ACCESSO SECRETS ({len(report['secret_access'])} eventi) ---")
    for ev in report["secret_access"][:10]:
        print(f"  [{ev['timestamp'][:19]}] {ev['user']} → {ev['verb']} secret/{ev['name']} ({ev['namespace']})")
    
    print(f"\n--- CAMBI RBAC ({len(report['rbac_changes'])} eventi) ---")
    for ev in report["rbac_changes"][:5]:
        print(f"  [{ev['timestamp'][:19]}] {ev['user']} → {ev['verb']} {ev['resource']}/{ev['name']}")
    
    print(f"\n--- EXEC IN CONTAINER ({len(report['exec_events'])} eventi) ---")
    if report["exec_events"]:
        for ev in report["exec_events"][:5]:
            print(f"  [WARN] [{ev['timestamp'][:19]}] {ev['user']} → exec in {ev['name']} ({ev['namespace']})")
    else:
        print("  [OK] Nessun exec nel periodo analizzato")
    
    print(f"\n--- TOP UTENTI ---")
    for user, count in sorted(report["users"].items(), key=lambda x: -x[1])[:5]:
        print(f"  {user}: {count} azioni")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    log_file = sys.argv[1] if len(sys.argv) > 1 else "/var/log/kubernetes/audit.log"
    report = analyze_audit_log(log_file)
    if report:
        print_report(report)
PYTHON

echo "[OK] Script analisi audit log creato: audit/analyze-audit-log.py"
echo "Uso: python3 audit/analyze-audit-log.py /var/log/kubernetes/audit.log"
```

---

## PART E: REPORT COMPLIANCE AUTOMATICO

### Esercizio E1: Generare Report GDPR/NIS2

```bash
cd ~/compliance-lab

cat > reports/generate-compliance-report.py << 'PYTHON'
"""
Generatore report compliance automatico.
Aggrega evidenze da: Kubernetes, Trivy, gitleaks, checkov.
Produce: report PDF-ready (Markdown) per audit SOC2/ISO27001/GDPR.
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path


def run_kubectl_check(cmd: list[str]) -> dict:
    """Esegue kubectl e ritorna il risultato."""
    try:
        result = subprocess.run(
            ["kubectl"] + cmd,
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout.strip() else {}
        return {}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return {}


def check_rbac_compliance() -> dict:
    """Verifica compliance RBAC: no cluster-admin per SA, no wildcard."""
    crbs = run_kubectl_check(["get", "clusterrolebindings", "-o", "json"])
    
    issues = []
    for binding in crbs.get("items", []):
        role = binding.get("roleRef", {}).get("name", "")
        if role == "cluster-admin":
            for subj in binding.get("subjects", []):
                if subj.get("kind") == "ServiceAccount":
                    issues.append(f"SA {subj.get('namespace','?')}/{subj.get('name')} ha cluster-admin")
    
    return {
        "status": "FAIL" if issues else "PASS",
        "control": "Least Privilege RBAC",
        "regulation": "NIS2 art.21, ISO27001 A.9",
        "issues": issues
    }


def check_network_policy_compliance() -> dict:
    """Verifica che ogni namespace abbia NetworkPolicy default-deny."""
    namespaces_data = run_kubectl_check(["get", "namespaces", "-o", "json"])
    netpols_data = run_kubectl_check(["get", "networkpolicies", "-A", "-o", "json"])
    
    namespaces = [
        ns["metadata"]["name"] for ns in namespaces_data.get("items", [])
        if ns["metadata"]["name"] not in ("kube-system", "kube-public", "kube-node-lease")
    ]
    
    netpols = netpols_data.get("items", [])
    covered = {np["metadata"]["namespace"] for np in netpols}
    
    uncovered = [ns for ns in namespaces if ns not in covered]
    
    return {
        "status": "FAIL" if uncovered else "PASS",
        "control": "Network Segmentation",
        "regulation": "GDPR art.32, NIS2 art.21",
        "issues": [f"Namespace senza NetworkPolicy: {ns}" for ns in uncovered]
    }


def check_encryption_compliance() -> dict:
    """Verifica che i secret Kubernetes siano cifrati (EncryptionConfig)."""
    # Semplificato: verifica solo che i secret non siano in base64 plain
    # In produzione: verificare EncryptionConfiguration sull'API server
    return {
        "status": "WARN",
        "control": "Encryption at Rest",
        "regulation": "GDPR art.32, DORA art.9",
        "issues": [
            "Verificare EncryptionConfiguration su API server",
            "K3s default: secret NON cifrati su etcd"
        ]
    }


def generate_report(output_path: str = "compliance-report.md"):
    """Genera il report compliance completo."""
    checks = [
        check_rbac_compliance(),
        check_network_policy_compliance(),
        check_encryption_compliance(),
    ]
    
    now = datetime.utcnow()
    passed = sum(1 for c in checks if c["status"] == "PASS")
    failed = sum(1 for c in checks if c["status"] == "FAIL")
    warned = sum(1 for c in checks if c["status"] == "WARN")
    
    lines = [
        f"# Compliance Report — {now.strftime('%Y-%m-%d')}",
        f"",
        f"**Generato:** {now.isoformat()}Z",
        f"**Periodo:** {now.strftime('%Y-%m-01')} → {now.strftime('%Y-%m-%d')}",
        f"**Cluster:** {subprocess.run(['kubectl', 'config', 'current-context'], capture_output=True, text=True).stdout.strip()}",
        f"",
        f"## Executive Summary",
        f"",
        f"| Status | Count |",
        f"|--------|-------|",
        f"| ✅ PASS | {passed} |",
        f"| ❌ FAIL | {failed} |",
        f"| ⚠️ WARN | {warned} |",
        f"",
        f"## Dettaglio Controlli",
        f"",
    ]
    
    for check in checks:
        icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(check["status"], "?")
        lines.extend([
            f"### {icon} {check['control']}",
            f"",
            f"- **Normativa:** {check['regulation']}",
            f"- **Status:** {check['status']}",
            f"",
        ])
        if check["issues"]:
            lines.append("**Problemi riscontrati:**")
            for issue in check["issues"]:
                lines.append(f"- {issue}")
        else:
            lines.append("**Nessun problema riscontrato.**")
        lines.append("")
    
    lines.extend([
        "## Prossima Revisione",
        "",
        f"- Data: {now.replace(month=now.month % 12 + 1).strftime('%Y-%m-01')}",
        "- Aggiunti: scan Trivy + gitleaks + checkov da pipeline CI/CD",
        "",
        "---",
        f"*Report generato automaticamente — rivedere con il team security*",
    ])
    
    content = "\n".join(lines)
    
    Path(output_path).write_text(content, encoding="utf-8")
    print(f"[OK] Report salvato: {output_path}")
    print(content[:500])
    return content


if __name__ == "__main__":
    generate_report("reports/compliance-report.md")
PYTHON

python3 reports/generate-compliance-report.py

echo ""
echo "[OK] Report compliance generato: reports/compliance-report.md"
```

---

## Conclusioni e Prossimi Passi

```
COMPLIANCE-AS-CODE — RIEPILOGO:

NORMATIVA EU 2024-2025:
  ✓ GDPR: privacy by design, encryption, breach notification 72h
  ✓ NIS2 (ott.2024): risk management, incident report 24h/72h
  ✓ DORA (gen.2025): RTO documentato, TLPT ogni 3 anni, ICT register

OPA GATEKEEPER:
  ✓ ConstraintTemplate: definisce la struttura della policy (Rego)
  ✓ Constraint: applica la policy a scope/namespace specifici
  ✓ Enforcement modes: deny (blocca) vs warn (avvisa)
  ✓ Policy GDPR: label data-classification obbligatorio
  ✓ Policy DORA: label RTO obbligatorio per servizi finanziari

CHECKOV:
  ✓ Scan Terraform, Kubernetes YAML, Helm, CloudFormation, Bicep
  ✓ 1000+ check built-in mappati a CIS, NIST, GDPR, SOC2
  ✓ --framework terraform --severity CRITICAL → gate in CI/CD
  ✓ Output JSON → parsing automatico per dashboard compliance

AUDIT LOG KUBERNETES:
  ✓ Audit policy: livelli None/Metadata/Request/RequestResponse
  ✓ Log accesso secrets, cambi RBAC, exec nei container
  ✓ Immutabilità: log scritti su storage append-only + WORM
  ✓ Retention: almeno 1 anno per GDPR, 5 anni per DORA

REPORT AUTOMATICO:
  ✓ Aggregare: kubectl + Trivy + gitleaks + checkov
  ✓ Formato: Markdown → PDF per auditor esterno
  ✓ Frequenza: mensile per SOC2, trimestrale per ISO27001
  ✓ Evidence collection: screenshot, log, hash verificabili

MAXIM FONDAMENTALE:
  "La compliance non è un evento annuale, è una pratica quotidiana.
   I controlli automatizzati rendono la non-compliance immediatamente visibile."
```

```bash
# Pulizia lab
kubectl delete -f opa/ --ignore-not-found=true 2>/dev/null
kubectl delete deployment test-gdpr-compliant 2>/dev/null
kubectl delete -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.17.1/deploy/gatekeeper.yaml 2>/dev/null
rm -rf ~/compliance-lab

echo "[OK] Lab Compliance completato"
```

---

> **Nota versioni:** OPA Gatekeeper v3.17.x (ottobre 2024), Kyverno 1.12.x, checkov 3.2.x.
> GDPR 2016/679 vigente. NIS2 2022/2555: deadline recepimento ottobre 2024 — Italy: D.Lgs. 138/2024
> entrato in vigore 16 ottobre 2024. DORA 2022/2554: applicazione dal 17 gennaio 2025.
> EU AI Act 2024/1689: pubblicato giugno 2024, phased enforcement 2025-2027.
> SOC2 Trust Services Criteria 2017 (aggiornamento 2022 in vigore).
> ISO 27001:2022 — versione con 93 controlli (vs 114 della versione 2013).
