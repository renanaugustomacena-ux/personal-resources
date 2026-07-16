# Tutorial: FinOps — Cost Governance, Kubecost e Right-Sizing

> **Documento di riferimento:** `21-finops-cost-governance.md`
> **Dominio:** Gestione Piattaforme — Architetture Avanzate
> **Ambito:** Framework FinOps (Inform/Optimize/Operate), tagging strategy cloud, showback e chargeback, right-sizing con VPA, Kubecost su K3s, budget alert, anomaly detection, unit economics
> **Durata lab:** 5-6 ore
> **Livello:** Avanzato — richiede K3s cluster, helm, accesso AWS/GCP/Azure opzionale
> **Prerequisiti:** K3s cluster locale (o cloud), helm 3.x, kubectl, Python 3.10+
> **Ambiente:** Kubecost Community Edition su K3s, script Python per cost analysis, LocalStack opzionale

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI FINOPS LAB ===
echo "=== PREREQUISITI ==="

kubectl version --client --short 2>/dev/null && echo "[OK] kubectl" || echo "[FAIL] kubectl richiesto"
helm version --short 2>/dev/null && echo "[OK] helm" || echo "[FAIL] helm richiesto"
python3 --version && echo "[OK] Python" || echo "[FAIL] Python richiesto"

mkdir -p ~/finops-lab/{kubecost,reports,scripts,tagging}
cd ~/finops-lab

echo "[OK] Directory lab: ~/finops-lab"
```

### Framework FinOps — Le Tre Fasi

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    FINOPS LIFECYCLE                                       │
│                                                                          │
│   INFORM ──────────────────────────────────────────────────────────┐    │
│   "Quanto stiamo spendendo? Su cosa?"                              │    │
│   ├── Tagging: ogni risorsa ha owner, team, environment, project   │    │
│   ├── Showback: report costi per team/servizio (informativo)       │    │
│   └── Chargeback: addebito reale dei costi ai team responsabili    │    │
│                                                                    │    │
│   OPTIMIZE ─────────────────────────────────────────────────────┐ │    │
│   "Come spendiamo meno per lo stesso risultato?"                │ │    │
│   ├── Right-sizing: VM/container troppo grandi per il workload  │ │    │
│   ├── Reserved Instances / Savings Plans: sconto 30-70%         │ │    │
│   ├── Spot/Preemptible: sconto 80-90% per workload tolleranti   │ │    │
│   └── Eliminare sprechi: risorse non usate, dev env overnight   │ │    │
│                                                                 │ │    │
│   OPERATE ──────────────────────────────────────────────────┐  │ │    │
│   "Come manteniamo la disciplina nel tempo?"                │  │ │    │
│   ├── Budget alert: notifica quando si supera il budget     │  │ │    │
│   ├── Anomaly detection: spike inaspettati di spesa         │  │ │    │
│   ├── Policy enforcement: tagging obbligatorio, max size    │  │ │    │
│   └── Governance: SCP, OPA per prevenire over-provisioning  │  │ │    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — FinOps come Pratica

> I team cloud spesso scoprono l'entità dei costi DOPO che la fattura è arrivata.
> FinOps cambia il processo: i costi diventano visibili in tempo reale,
> i team sono responsabili della propria spesa,
> e ci sono processi per ottimizzare prima che sia troppo tardi.
> Il principio fondamentale: "Il cloud è OPEX, non CAPEX —
> ogni risorsa costa per ogni secondo di vita."

---

### Concetto A1: Tagging Strategy — La Base di Tutto

```
TAGGING STRATEGY — PERCHÉ È FONDAMENTALE:

Senza tag, non sai rispondere a:
  - "Quanto spende il team backend vs frontend?"
  - "Quanto costano le risorse di production vs staging?"
  - "Quale progetto usa il 40% del cluster?"

CON UNA BUONA TAGGING STRATEGY:
  - Showback: "team-A ha generato €5k di costi questo mese"
  - Chargeback: addebitare realmente i costi ai P&L dei team
  - Anomaly: "resources senza tag = rogue spending"

TAG MINIMI OBBLIGATORI (applicabili a tutti i cloud):

  Struttura raccomandata FinOps Foundation:
  
  environment:     production | staging | development | testing
  team:            platform | backend | frontend | data | ml
  project:         order-service | payment-gateway | user-api
  cost-center:     CC-1234 (codice contabile aziendale)
  owner:           alice.rossi@company.com (chi è responsabile)
  created-by:      terraform | manual | helm
  terraform:       true/false (gestita da IaC)
  
  Tag opzionali per compliance:
  data-classification:  pii | internal | public
  gdpr:                 true/false (tratta dati personali?)
  backup:               required | not-required

ENFORCEMENT TAG OBBLIGATORI:
  AWS: Service Control Policy (SCP) + Config Rules
  Azure: Azure Policy + Tag Inheritance
  GCP: Organization Policy Constraints

KUBERNETES:
  label: "team/name: backend"
  label: "cost-center: CC-1234"
  annotation: "owner: alice.rossi@company.com"
  → Kubecost usa questi label per cost allocation per namespace/workload
```

---

## PART B: KUBECOST SU KUBERNETES

### Esercizio B1: Installare Kubecost Community

```bash
cd ~/finops-lab

echo "=== KUBECOST — COST MONITORING K8S ==="

# Kubecost: visibilità costi Kubernetes per namespace, pod, workload, label
helm repo add kubecost https://kubecost.github.io/cost-analyzer/ --force-update
helm repo update

helm upgrade --install kubecost kubecost/cost-analyzer \
  --namespace kubecost \
  --create-namespace \
  --set kubecostToken="" \          # Community Edition: token vuoto
  --set global.prometheus.enabled=true \
  --set global.grafana.enabled=false \   # usa Grafana esistente se disponibile
  --set kubecostFrontend.image.pullPolicy=IfNotPresent \
  --wait \
  --timeout 300s

kubectl -n kubecost get pods

echo "[OK] Kubecost Community Edition installato"
echo "[INFO] UI: kubectl -n kubecost port-forward svc/kubecost-cost-analyzer 9090:9090"
echo "       Poi aprire: http://localhost:9090"

echo ""
echo "=== WORKLOAD CON LABEL PER COST ALLOCATION ==="

# Creare namespace con label team (Kubecost usa i namespace label)
kubectl create namespace team-backend --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace team-backend team=backend cost-center=CC-1001 environment=production

kubectl create namespace team-frontend --dry-run=client -o yaml | kubectl apply -f -
kubectl label namespace team-frontend team=frontend cost-center=CC-1002 environment=production

# Deployment con label per cost tracking
cat > kubecost/deployment-backend.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: team-backend
  labels:
    team: backend
    project: order-service
    cost-center: "CC-1001"
    environment: production
spec:
  replicas: 2
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
        team: backend
        project: order-service
        cost-center: "CC-1001"
    spec:
      containers:
        - name: app
          image: nginx:1.27.0
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "200m"
              memory: "256Mi"
EOF

kubectl apply -f kubecost/deployment-backend.yaml
echo "[OK] Deployment con label cost-tracking creato"

echo ""
echo "--- API Kubecost per query costi ---"
# Kubecost espone API REST per query programmatiche
sleep 30   # Attendere dati iniziali

curl -s "http://localhost:9090/model/allocation?window=24h&aggregate=namespace" 2>/dev/null | \
  python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    allocations = data.get('data', [{}])[0] if data.get('data') else {}
    print('Costi per namespace (ultimi 24h):')
    for ns, info in allocations.items():
        if ns != '__idle__':
            cost = info.get('totalCost', 0)
            cpu = info.get('cpuCost', 0)
            mem = info.get('ramCost', 0)
            print(f'  {ns}: \${cost:.4f} total (cpu=\${cpu:.4f}, mem=\${mem:.4f})')
except Exception as e:
    print(f'[INFO] Kubecost in avvio — dati disponibili dopo ~15 minuti: {e}')
" || echo "[INFO] Port-forward non attivo — avviare: kubectl port-forward -n kubecost svc/kubecost-cost-analyzer 9090:9090 &"
```

---

## PART C: RIGHT-SIZING

### Esercizio C1: Vertical Pod Autoscaler per Right-Sizing

```bash
cd ~/finops-lab

echo "=== RIGHT-SIZING CON VPA ==="

# VPA osserva il consumo REALE e suggerisce limits appropriati
helm repo add fairwinds-stable https://charts.fairwinds.com/stable --force-update
helm repo update

helm upgrade --install vpa fairwinds-stable/vpa \
  --namespace vpa \
  --create-namespace \
  --wait \
  --timeout 120s

kubectl -n vpa get pods

echo "[OK] VPA installato"

# VPA Object: osserva un Deployment e suggerisce risorse
cat > kubecost/vpa-order-service.yaml << 'EOF'
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: order-service-vpa
  namespace: team-backend
  annotations:
    description: >
      VPA per order-service.
      UpdateMode: "Off" = solo suggerisce, non modifica automaticamente.
      In produzione iniziare con "Off", poi passare a "Auto" dopo revisione.
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-service
  
  updatePolicy:
    updateMode: "Off"    # Non modificare automaticamente (solo suggerimenti)
  
  resourcePolicy:
    containerPolicies:
      - containerName: "app"
        minAllowed:          # Non scendere sotto questi valori
          cpu: "50m"
          memory: "64Mi"
        maxAllowed:          # Non superare questi valori
          cpu: "2000m"
          memory: "4Gi"
        controlledResources: ["cpu", "memory"]
EOF

kubectl apply -f kubecost/vpa-order-service.yaml
echo "[OK] VPA configurato per order-service"

echo ""
echo "--- Generare traffico per far raccogliere dati al VPA ---"
# Fare alcune richieste per generare metriche
for i in $(seq 1 20); do
  kubectl exec -n team-backend deploy/order-service -- sh -c "ls /etc > /dev/null 2>&1" 2>/dev/null || true
done

sleep 30

echo ""
echo "--- Raccomandazioni VPA ---"
kubectl get vpa order-service-vpa -n team-backend -o json 2>/dev/null | python3 -c "
import json, sys
try:
    vpa = json.load(sys.stdin)
    recommendation = vpa.get('status', {}).get('recommendation', {})
    containers = recommendation.get('containerRecommendations', [])
    
    if not containers:
        print('[INFO] VPA raccoglie dati per ~15 minuti prima di fare raccomandazioni')
    else:
        for c in containers:
            print(f'Container: {c[\"containerName\"]}')
            lower = c.get('lowerBound', {})
            target = c.get('target', {})
            upper = c.get('upperBound', {})
            print(f'  Corrente requests: cpu=100m memory=128Mi')
            print(f'  VPA suggerisce:')
            print(f'    Lower bound: cpu={lower.get(\"cpu\",\"?\")} memory={lower.get(\"memory\",\"?\")}')
            print(f'    Target:      cpu={target.get(\"cpu\",\"?\")} memory={target.get(\"memory\",\"?\")}')
            print(f'    Upper bound: cpu={upper.get(\"cpu\",\"?\")} memory={upper.get(\"memory\",\"?\")}')
except Exception as e:
    print(f'[INFO] VPA in raccolta dati: {e}')
" 2>/dev/null
```

---

## PART D: SCRIPT DI ANALISI COSTI

### Esercizio D1: Cost Analysis e Report

```bash
cat > scripts/cost-analysis.py << 'PYTHON'
"""
FinOps Cost Analyzer — analizza risorse K8s e calcola costo stimato.
Usa i request/limit configurati e i prezzi cloud stimati.
"""
import json
import subprocess
from dataclasses import dataclass, field
from typing import Optional

# Prezzi stimati (€/core-month e €/GB-month) per cloud europei
CLOUD_PRICES = {
    "aws-eu-west-1": {
        "cpu_per_core_hour": 0.0426,     # c5.xlarge equivalente
        "memory_per_gb_hour": 0.0053,    # c5.xlarge equivalente
    },
    "gcp-europe-west4": {
        "cpu_per_core_hour": 0.0380,
        "memory_per_gb_hour": 0.0051,
    },
    "azure-westeurope": {
        "cpu_per_core_hour": 0.0448,
        "memory_per_gb_hour": 0.0056,
    }
}

HOURS_PER_MONTH = 730


@dataclass
class WorkloadCost:
    namespace: str
    name: str
    kind: str
    replicas: int
    cpu_request_cores: float
    memory_request_gb: float
    cpu_limit_cores: float
    memory_limit_gb: float
    team: str = "unknown"
    cost_center: str = "unknown"
    
    def monthly_cost(self, provider: str = "aws-eu-west-1") -> dict:
        prices = CLOUD_PRICES.get(provider, CLOUD_PRICES["aws-eu-west-1"])
        cpu_cost = self.replicas * self.cpu_request_cores * prices["cpu_per_core_hour"] * HOURS_PER_MONTH
        mem_cost = self.replicas * self.memory_request_gb * prices["memory_per_gb_hour"] * HOURS_PER_MONTH
        return {
            "total": cpu_cost + mem_cost,
            "cpu": cpu_cost,
            "memory": mem_cost,
        }


def parse_cpu(cpu_str: str) -> float:
    """Converte CPU string K8s in core (es. '100m' → 0.1)."""
    if not cpu_str:
        return 0.0
    if cpu_str.endswith("m"):
        return float(cpu_str[:-1]) / 1000
    return float(cpu_str)


def parse_memory(mem_str: str) -> float:
    """Converte memoria string K8s in GB (es. '256Mi' → 0.256)."""
    if not mem_str:
        return 0.0
    if mem_str.endswith("Mi"):
        return float(mem_str[:-2]) / 1024
    if mem_str.endswith("Gi"):
        return float(mem_str[:-2])
    if mem_str.endswith("Ki"):
        return float(mem_str[:-2]) / 1024 / 1024
    return float(mem_str) / 1024 / 1024 / 1024


def get_all_deployments() -> list[WorkloadCost]:
    """Legge tutti i Deployment dal cluster via kubectl."""
    try:
        result = subprocess.run(
            ["kubectl", "get", "deployments", "-A", "-o", "json"],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return []
    
    workloads = []
    for item in data.get("items", []):
        metadata = item.get("metadata", {})
        labels = metadata.get("labels", {})
        spec = item.get("spec", {})
        
        replicas = spec.get("replicas", 1)
        containers = spec.get("template", {}).get("spec", {}).get("containers", [])
        
        total_cpu_req = 0.0
        total_mem_req = 0.0
        total_cpu_lim = 0.0
        total_mem_lim = 0.0
        
        for c in containers:
            res = c.get("resources", {})
            req = res.get("requests", {})
            lim = res.get("limits", {})
            
            total_cpu_req += parse_cpu(req.get("cpu", "0"))
            total_mem_req += parse_memory(req.get("memory", "0"))
            total_cpu_lim += parse_cpu(lim.get("cpu", "0"))
            total_mem_lim += parse_memory(lim.get("memory", "0"))
        
        workloads.append(WorkloadCost(
            namespace=metadata.get("namespace", "?"),
            name=metadata.get("name", "?"),
            kind="Deployment",
            replicas=replicas,
            cpu_request_cores=total_cpu_req,
            memory_request_gb=total_mem_req,
            cpu_limit_cores=total_cpu_lim,
            memory_limit_gb=total_mem_lim,
            team=labels.get("team", labels.get("app.kubernetes.io/part-of", "unknown")),
            cost_center=labels.get("cost-center", "untagged"),
        ))
    
    return workloads


def generate_finops_report(provider: str = "aws-eu-west-1"):
    """Genera report FinOps completo."""
    workloads = get_all_deployments()
    
    if not workloads:
        print("[INFO] Nessun Deployment trovato o kubectl non disponibile")
        print("       Generando report con dati simulati...")
        
        # Dati simulati per demo
        workloads = [
            WorkloadCost("team-backend", "order-service", "Deployment", 2, 0.1, 0.125, 0.2, 0.25, "backend", "CC-1001"),
            WorkloadCost("team-backend", "payment-service", "Deployment", 3, 0.2, 0.256, 0.5, 0.512, "backend", "CC-1001"),
            WorkloadCost("team-frontend", "web-app", "Deployment", 2, 0.1, 0.128, 0.2, 0.256, "frontend", "CC-1002"),
            WorkloadCost("monitoring", "prometheus", "Deployment", 1, 0.5, 2.0, 1.0, 4.0, "platform", "CC-9999"),
            WorkloadCost("default", "orphan-deployment", "Deployment", 1, 0.2, 0.256, 0.5, 0.512, "unknown", "untagged"),
        ]
    
    print("=" * 70)
    print("FINOPS REPORT — KUBERNETES COST ANALYSIS")
    print(f"Provider: {provider}")
    print("=" * 70)
    
    # Per namespace
    by_ns: dict[str, float] = {}
    by_team: dict[str, float] = {}
    by_cc: dict[str, float] = {}
    total = 0.0
    untagged_cost = 0.0
    
    print(f"\n{'Namespace':<20} {'Workload':<25} {'Replicas':>8} {'CPU req':>10} {'Mem req':>10} {'€/mese':>10}")
    print("-" * 85)
    
    for w in sorted(workloads, key=lambda x: (x.namespace, x.name)):
        cost = w.monthly_cost(provider)["total"]
        total += cost
        by_ns[w.namespace] = by_ns.get(w.namespace, 0) + cost
        by_team[w.team] = by_team.get(w.team, 0) + cost
        by_cc[w.cost_center] = by_cc.get(w.cost_center, 0) + cost
        
        if w.cost_center == "untagged" or w.team == "unknown":
            untagged_cost += cost
        
        print(f"{w.namespace:<20} {w.name:<25} {w.replicas:>8} "
              f"{w.cpu_request_cores:>9.2f}c {w.memory_request_gb:>8.2f}G €{cost:>8.2f}")
    
    print("-" * 85)
    print(f"{'TOTALE':>55} €{total:>8.2f}/mese")
    
    print(f"\n--- Costi per Team ---")
    for team, cost in sorted(by_team.items(), key=lambda x: -x[1]):
        pct = cost / total * 100 if total > 0 else 0
        bar = "█" * int(pct / 5)
        print(f"  {team:<20} €{cost:>8.2f}/mese ({pct:.1f}%) {bar}")
    
    print(f"\n--- Costi per Cost Center ---")
    for cc, cost in sorted(by_cc.items(), key=lambda x: -x[1]):
        pct = cost / total * 100 if total > 0 else 0
        print(f"  {cc:<20} €{cost:>8.2f}/mese ({pct:.1f}%)")
    
    if untagged_cost > 0:
        print(f"\n⚠️  ATTENZIONE: €{untagged_cost:.2f}/mese senza tag appropriati")
        print("   Applicare tag 'team' e 'cost-center' a tutti i workload!")
    
    # Right-sizing opportunities
    print(f"\n--- Opportunità Right-Sizing ---")
    over_provisioned = [w for w in workloads
                        if w.cpu_limit_cores > w.cpu_request_cores * 3
                        or w.memory_limit_gb > w.memory_request_gb * 3]
    
    if over_provisioned:
        print("  Workload potenzialmente over-provisioned (limits > 3× requests):")
        for w in over_provisioned:
            current = w.monthly_cost(provider)["total"]
            optimized_cost = current * 0.5   # stima risparmio 50%
            print(f"  → {w.namespace}/{w.name}: €{current:.2f}/mese → ~€{optimized_cost:.2f} ottimizzato")
    else:
        print("  Nessuna over-provisioning evidente rilevata.")
    
    print(f"\n{'='*70}")
    print(f"Risparmio potenziale stimato: €{untagged_cost * 0.2:.2f}/mese (ottimizzazione 20%)")
    print(f"Azione prioritaria: {'Applicare tag a risorse non taggate' if untagged_cost > 0 else 'Right-sizing workload over-provisioned'}")


if __name__ == "__main__":
    generate_finops_report("aws-eu-west-1")
PYTHON

python3 scripts/cost-analysis.py

echo "[OK] Report FinOps generato"
```

---

## PART E: BUDGET ALERT E ANOMALY DETECTION

### Esercizio E1: Alert e Policy

```bash
cd ~/finops-lab

cat << 'FINOPS_GUIDE'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUDGET ALERT — CONFIGURAZIONE PER CLOUD PROVIDER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AWS BUDGET ALERT (Terraform):
  resource "aws_budgets_budget" "monthly_alert" {
    name         = "monthly-total-budget"
    budget_type  = "COST"
    limit_amount = "10000"    # €10,000/mese
    limit_unit   = "USD"
    time_unit    = "MONTHLY"
    
    notification {
      comparison_operator = "GREATER_THAN"
      threshold           = 80    # alert a 80% del budget
      threshold_type      = "PERCENTAGE"
      notification_type   = "ACTUAL"
      subscriber_email_addresses = ["team-finops@company.com"]
    }
    
    # Alert anche su forecast (se il trend attuale porta a supergare il budget)
    notification {
      comparison_operator = "GREATER_THAN"
      threshold           = 100
      threshold_type      = "PERCENTAGE"
      notification_type   = "FORECASTED"
      subscriber_email_addresses = ["cto@company.com"]
    }
  }

AZURE COST ALERT (Bicep):
  resource budgetAlert 'Microsoft.Consumption/budgets@2021-10-01' = {
    name: 'monthly-alert'
    properties: {
      category: 'Cost'
      amount: 10000
      timeGrain: 'Monthly'
      timePeriod: {
        startDate: '2026-01-01T00:00:00Z'
      }
      notifications: {
        at80pct: {
          enabled: true
          operator: 'GreaterThanOrEqualTo'
          threshold: 80
          contactEmails: ['finops@company.com']
        }
      }
    }
  }

GCP BUDGET ALERT (gcloud):
  gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="Monthly Production Budget" \
    --budget-amount=10000EUR \
    --threshold-rule=percent=50,basis=CURRENT_SPEND \
    --threshold-rule=percent=80,basis=CURRENT_SPEND \
    --threshold-rule=percent=100,basis=CURRENT_SPEND

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANOMALY DETECTION — MODELLI E APPROCCI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

METODO 1: Z-SCORE (statistico semplice):
  Calcola media e deviazione standard degli ultimi 30 giorni.
  Alert se spesa giornaliera > media + 2σ (sigma)
  
  Python:
  import numpy as np
  daily_costs = [120.5, 118.2, 121.0, 119.8, ...]  # ultimi 30gg
  mean = np.mean(daily_costs)
  std = np.std(daily_costs)
  threshold = mean + 2 * std
  if today_cost > threshold:
      alert(f"Anomalia costi: {today_cost:.2f} > {threshold:.2f}")

METODO 2: MOVING AVERAGE:
  Confronta con media degli ultimi 7 giorni × 1.3 (tolleranza 30%)
  Alert se supera il 130% della media mobile

METODO 3: MACHINE LEARNING (AWS Cost Anomaly Detection):
  AWS ha un servizio nativo che usa ML per rilevare anomalie
  Zero configurazione richiesta (pay-per-anomaly)
  Rileva: spike improvvisi, trend graduali, variazioni per servizio

AUTOMATION FINOPS:
  CronJob giornaliero: scrape Kubecost API → report Slack
  Weekly: VPA recommendation → PR automatica con right-sizing
  Monthly: compare spesa vs budget → report CFO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINOPS_GUIDE
```

---

## Conclusioni e Prossimi Passi

```
FINOPS — RIEPILOGO:

FRAMEWORK (Inform → Optimize → Operate):
  ✓ Inform: tagging → showback → chargeback
  ✓ Optimize: right-sizing, Reserved/Spot, cleanup sprechi
  ✓ Operate: budget alert, anomaly detection, governance

TAGGING STRATEGY:
  ✓ Obbligatori: environment, team, project, cost-center, owner
  ✓ Enforcement: SCP (AWS), Azure Policy, OPA (K8s)
  ✓ Regola: "Se non è tuo, non lo sai" → tag obbligatorio prima del deploy

KUBECOST:
  ✓ Community Edition: gratuita per 1 cluster
  ✓ Costi per namespace, deployment, label, team
  ✓ API REST: integrazione con dashboard custom
  ✓ Alternativa: OpenCost (CNCF, 100% open source)

VPA (Vertical Pod Autoscaler):
  ✓ UpdateMode: Off (solo suggerimenti) → Auto (modifica automaticamente)
  ✓ Osserva consumo REALE per 1-7 giorni poi suggerisce
  ✓ Integrazione Kubecost: identifica workload over-provisioned
  ✓ Non compatibile con HPA (orizzontale): scegliere uno dei due

RIGHT-SIZING REGOLE:
  ✓ CPU request: 40-60% dell'utilizzo medio
  ✓ Memory request: 80-90% del picco (non media — OOM è peggio)
  ✓ CPU limit: 3-5× il request (burstable)
  ✓ Memory limit: 1.2-1.5× il request (no OOM accidentale)

SAVINGS POTENZIALI TIPICI:
  Right-sizing: 20-35% di risparmio
  Reserved Instances: 30-60% su carichi stabili
  Spot/Preemptible: 70-90% su job batch, CI/CD
  Cleanup sprechi: 10-20% di risorse inutilizzate

UNIT ECONOMICS:
  Costo per transazione = Costo totale infra / N transazioni mensili
  Costo per utente attivo = Costo totale / MAU (Monthly Active Users)
  Questi KPI permettono di valutare la sostenibilità del modello
  e guidano le decisioni di architettura

CULTURA FINOPS:
  "FinOps funziona quando ogni sviluppatore si sente
   responsabile del costo della propria feature,
   non solo delle sue funzionalità."
```

```bash
# Pulizia
helm uninstall kubecost -n kubecost 2>/dev/null
helm uninstall vpa -n vpa 2>/dev/null
kubectl delete namespace team-backend team-frontend 2>/dev/null
rm -rf ~/finops-lab
echo "[OK] Lab FinOps completato"
```

---

> **Nota versioni:** Kubecost 2.x (Helm chart 2.x, 2024), OpenCost 1.13.x (CNCF sandbox 2023).
> VPA 1.1.x (Helm chart fairwinds-stable/vpa 9.x).
> FinOps Foundation Framework v3 (2024): aggiunge "maturity model" con livelli Crawl/Walk/Run.
> AWS Cost Anomaly Detection: disponibile senza configurazione aggiuntiva (pay-per-alert).
> GCP Carbon Footprint Report: integrato in Cloud Billing (sostenibilità Green Cloud).
> EU Sustainability Reporting (CSRD): dal 2024 obbligatoria per grandi aziende EU — include cloud carbon footprint.
