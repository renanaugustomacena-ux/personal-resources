---
corso: "Gestione Piattaforme e DevOps"
fase: "7 — Architetture Avanzate"
modulo: 21
titolo: "FinOps + Cost Governance Cloud"
versione: "FinOps Foundation Framework v3; kubecost 2.x; OpenCost 1.x; Infracost 0.10"
livello: "Avanzato"
prerequisiti: ["01-cloud-aws", "02-cloud-azure", "03-cloud-gcp", "05-kubernetes"]
obiettivi:
  - "Applicare il framework FinOps (Inform, Optimize, Operate) a un ambiente multi-cloud"
  - "Configurare tagging strategy e cost allocation per showback e chargeback"
  - "Implementare right-sizing e Savings Plans/Reserved Instances per ridurre la spesa"
  - "Deployare kubecost/OpenCost per visibilita' dei costi Kubernetes per namespace e workload"
  - "Progettare budget alert, anomaly detection e governance policy con SCP e tagging enforcement"
tag: [finops, cost-governance, rightsizing, reserved-instances, kubecost, opencost, tagging, chargeback]
---

# FinOps + Cost Governance Cloud

> **Modulo 21** · **Aggiornamento:** 2026-05-24
> **Riferimenti:** FinOps Foundation Framework v3; AWS Cost Explorer; Azure Cost Management; GCP Billing; kubecost 2.x.

> **Obiettivi di apprendimento**
>
> Al completamento di questo modulo sarai in grado di:
> 1. Applicare il framework FinOps (Inform, Optimize, Operate) a un ambiente multi-cloud.
> 2. Configurare tagging strategy e cost allocation per showback e chargeback.
> 3. Implementare right-sizing e Savings Plans/Reserved Instances per ridurre la spesa.
> 4. Deployare kubecost/OpenCost per visibilita' dei costi Kubernetes per namespace e workload.
> 5. Progettare budget alert, anomaly detection e governance policy con SCP e tagging enforcement.

---

## Sommario

1. [Idee guida](#idee-guida)
2. [Framework FinOps — Inform, Optimize, Operate](#framework-finops--inform-optimize-operate)
3. [Cost visibility — Tagging strategy](#cost-visibility--tagging-strategy)
4. [Cost allocation — Showback e Chargeback](#cost-allocation--showback-e-chargeback)
5. [Ottimizzazione costi — Right-sizing](#ottimizzazione-costi--right-sizing)
6. [Reserved Instances e Savings Plans](#reserved-instances-e-savings-plans)
7. [Spot e Preemptible instances](#spot-e-preemptible-instances)
8. [Eliminazione sprechi](#eliminazione-sprechi)
9. [Kubernetes cost management](#kubernetes-cost-management)
10. [Confronto costi multi-cloud](#confronto-costi-multi-cloud)
11. [Budgeting e forecasting](#budgeting-e-forecasting)
12. [Anomaly detection](#anomaly-detection)
13. [Governance policies](#governance-policies)
14. [Struttura del team FinOps](#struttura-del-team-finops)
15. [Vendor management e negoziazioni](#vendor-management-e-negoziazioni)
16. [Unit economics](#unit-economics)
17. [Automazione FinOps](#automazione-finops)
18. [Ottimizzazione costi storage — Tiering e lifecycle](#ottimizzazione-costi-storage--tiering-e-lifecycle)
19. [Ottimizzazione costi di rete — Egress e data transfer](#ottimizzazione-costi-di-rete--egress-e-data-transfer)
20. [Confronto tooling FinOps](#confronto-tooling-finops)
21. [KPI e metriche FinOps](#kpi-e-metriche-finops)
22. [Anomaly detection avanzata — ML e automazione](#anomaly-detection-avanzata--ml-e-automazione)
23. [Gestione costi multi-cloud avanzata](#gestione-costi-multi-cloud-avanzata)
24. [Sostenibilita' e Green Cloud](#sostenibilita-e-green-cloud)
25. [Cultura FinOps e change management](#cultura-finops-e-change-management)
26. [Esercizi](#esercizi)
27. [Troubleshooting — 20 problemi di costo](#troubleshooting--20-problemi-di-costo)
28. [FAQ — 20 domande e risposte](#faq--20-domande-e-risposte)
29. [Letture](#letture)
30. [Glossario](#glossario)

---

## Idee guida

1. **FinOps = practice cross-team che bilancia velocità e costo.** Non è un team di taglio costi, ma una cultura di responsabilità finanziaria.
2. **Tre fasi di maturità: Inform → Optimize → Operate.** Ogni organizzazione attraversa queste fasi in modo iterativo.
3. **Reserved Instances + Savings Plans = 30-60% risparmio long-term.** Ma richiedono analisi accurata del workload baseline.
4. **Tagging policy enforced > tagging suggested.** Senza tag, nessun chargeback è possibile. Il tagging è la fondazione di tutto il FinOps.
5. **Budget alert + auto-action.** Esempio: stop automatico delle istanze non-prod fuori orario lavorativo.
6. **Ogni team è responsabile del proprio costo.** Engineering ownership, non solo finance.
7. **Il costo è una metrica di efficienza, non un vincolo.** Ottimizzare per valore, non per risparmio assoluto.

---

## Framework FinOps — Inform, Optimize, Operate

### Panoramica del framework

Il FinOps Framework della FinOps Foundation definisce tre fasi iterative e sei principi fondamentali:

```
┌─────────────────────────────────────────────────────────────┐
│                     FINOPS LIFECYCLE                        │
│                                                             │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │  INFORM  │ →  │  OPTIMIZE    │ →  │     OPERATE      │   │
│  │          │    │              │    │                  │   │
│  │ Visibilità│    │ Azione       │    │ Cultura continua │   │
│  │ Allocaz.  │    │ Right-sizing │    │ Governance       │   │
│  │ Benchmark │    │ RI/SP        │    │ Automation       │   │
│  │ Showback  │    │ Waste elim.  │    │ Policy           │   │
│  └──────────┘    └──────────────┘    └──────────────────┘   │
│       ↑                                       │             │
│       └───────────────────────────────────────┘             │
│                    Ciclo continuo                            │
└─────────────────────────────────────────────────────────────┘
```

### Principi FinOps

| Principio | Descrizione |
|---|---|
| **Teams need to collaborate** | Engineering, Finance, Product, Leadership lavorano insieme. |
| **Everyone takes ownership** | Ogni team è responsabile del proprio utilizzo cloud. |
| **A centralized team drives FinOps** | Un team FinOps centralizzato fornisce strumenti, formazione e best practice. |
| **Reports should be accessible and timely** | I dati di costo devono essere disponibili in near real-time. |
| **Decisions are driven by business value** | Ottimizzare per valore generato, non per costo assoluto minimo. |
| **Take advantage of the variable cost model** | Il cloud è pay-per-use: sfruttare elasticità e commitment. |

### Fase 1: Inform — Visibilità e allocazione

**Obiettivo:** Sapere chi spende cosa, dove, perché.

**Attività chiave:**

- Implementare tagging strategy obbligatoria.
- Configurare cost allocation accounts/projects.
- Costruire dashboard di costo per team/servizio/ambiente.
- Definire showback report (visibilità senza ri-fatturazione).
- Benchmarking interno ed esterno.
- Identificare unallocated cost e ridurlo sotto il 5%.

**Metriche della fase Inform:**

| Metrica | Target |
|---|---|
| % risorse taggate | > 95% |
| % costo allocato a team | > 90% |
| Frequenza reporting | Giornaliera |
| Latenza dati | < 24h (ideale < 4h) |
| Unallocated cost | < 5% |

### Fase 2: Optimize — Azione su inefficienze

**Obiettivo:** Ridurre costi senza impattare le prestazioni.

**Attività chiave:**

- Right-sizing delle istanze (CPU, memoria, storage).
- Acquisto Reserved Instances / Savings Plans per workload steady-state.
- Utilizzo Spot/Preemptible per workload tolleranti a interruzione.
- Eliminazione risorse idle (volumi, IP, snapshot, load balancer).
- Ottimizzazione storage tier (S3 Intelligent-Tiering, Azure Cool/Archive).
- Scheduling on/off per ambienti non-prod.

**Metriche della fase Optimize:**

| Metrica | Target |
|---|---|
| Savings rate (RI/SP) | 30-60% vs on-demand |
| Waste ratio | < 10% del totale |
| Right-sizing action/mese | > 5 per team |
| Coverage RI/SP | 60-80% del baseline |

### Fase 3: Operate — Governance e cultura

**Obiettivo:** Sostenere l'ottimizzazione nel tempo con processi e automazione.

**Attività chiave:**

- Budget con alert e auto-action.
- Policy di governance (SCP, Azure Policy, Organization Policy).
- Automazione di scheduling, cleanup, right-sizing.
- Review periodiche (settimanali per team, mensili per leadership).
- Continuous improvement tramite FinOps scorecard.
- Training e onboarding FinOps per nuovi team.

**Metriche della fase Operate:**

| Metrica | Target |
|---|---|
| Budget adherence | ±10% del forecast |
| Anomaly detection time | < 4h |
| Automation coverage | > 70% delle azioni ripetitive |
| FinOps maturity score | Incremento trimestrale |

---

## Cost visibility — Tagging strategy

### Perché il tagging è fondamentale

Senza tag, i costi cloud sono una massa indistinta. Il tagging è il prerequisito per:

- Allocare costi a team, progetti, ambienti.
- Costruire dashboard significative.
- Abilitare chargeback o showback.
- Identificare risorse orfane o non autorizzate.
- Automatizzare azioni basate su contesto (shutdown, cleanup).

### Tag obbligatori (minimum set)

| Tag | Descrizione | Esempio |
|---|---|---|
| `team` | Team proprietario | `team:platform`, `team:frontend` |
| `environment` | Ambiente di deploy | `env:production`, `env:staging`, `env:dev` |
| `project` | Progetto o prodotto | `project:marketplace`, `project:api` |
| `cost-center` | Centro di costo contabile | `cc:12345` |
| `owner` | Persona o team responsabile | `owner:mario.rossi@company.io` |
| `managed-by` | Come è gestita la risorsa | `managed-by:terraform`, `managed-by:manual` |

### Tag raccomandati (extended set)

| Tag | Descrizione | Esempio |
|---|---|---|
| `service` | Microservizio specifico | `service:auth`, `service:payments` |
| `data-classification` | Livello di classificazione dati | `data:public`, `data:confidential` |
| `compliance` | Requisiti di compliance | `compliance:pci`, `compliance:gdpr` |
| `end-date` | Data di scadenza risorsa | `end-date:2026-12-31` |
| `automation` | Eligibilità a automazione | `automation:schedule-off` |
| `budget-code` | Codice budget interno | `budget:Q3-2026-INFRA` |

### Enforcement del tagging

#### AWS — Tag Policy via Organizations

```json
{
  "tags": {
    "team": {
      "tag_key": {
        "@@assign": "team"
      },
      "tag_value": {
        "@@assign": [
          "platform",
          "frontend",
          "backend",
          "data",
          "security",
          "devops"
        ]
      },
      "enforced_for": {
        "@@assign": [
          "ec2:instance",
          "ec2:volume",
          "rds:db",
          "s3:bucket",
          "lambda:function",
          "ecs:service"
        ]
      }
    },
    "environment": {
      "tag_key": {
        "@@assign": "environment"
      },
      "tag_value": {
        "@@assign": [
          "production",
          "staging",
          "development",
          "sandbox"
        ]
      }
    }
  }
}
```

#### AWS — SCP per bloccare risorse senza tag

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUntaggedEC2",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances"
      ],
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "Null": {
          "aws:RequestTag/team": "true",
          "aws:RequestTag/environment": "true"
        }
      }
    }
  ]
}
```

#### Azure — Policy per tag obbligatori

```json
{
  "if": {
    "allOf": [
      {
        "field": "type",
        "equals": "Microsoft.Resources/subscriptions/resourceGroups"
      },
      {
        "field": "tags['team']",
        "exists": "false"
      }
    ]
  },
  "then": {
    "effect": "deny"
  }
}
```

#### GCP — Organization Policy + Label

```yaml
# Terraform — enforce labels su GCP
resource "google_org_policy_policy" "require_labels" {
  name   = "organizations/${var.org_id}/policies/constraints/compute.requireLabels"
  parent = "organizations/${var.org_id}"

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}
```

#### Terraform — validazione tag nei moduli

```hcl
# variables.tf
variable "required_tags" {
  type = map(string)
  validation {
    condition = alltrue([
      for k in ["team", "environment", "project", "cost-center"] :
      contains(keys(var.required_tags), k)
    ])
    error_message = "I tag obbligatori sono: team, environment, project, cost-center."
  }
}

# main.tf
resource "aws_instance" "app" {
  ami           = var.ami_id
  instance_type = var.instance_type
  tags          = merge(var.required_tags, {
    Name = "${var.project}-${var.environment}-app"
  })
}
```

### Audit del tagging

```bash
#!/usr/bin/env bash
# Script di audit tagging AWS
set -euo pipefail

REQUIRED_TAGS=("team" "environment" "project" "cost-center")
REGION="${1:-eu-west-1}"
UNTAGGED_COUNT=0
TOTAL_COUNT=0

echo "=== Audit tagging EC2 instances (${REGION}) ==="

INSTANCES=$(aws ec2 describe-instances \
  --region "${REGION}" \
  --query 'Reservations[].Instances[].{Id:InstanceId,Tags:Tags}' \
  --output json)

for INSTANCE_ID in $(echo "${INSTANCES}" | jq -r '.[].Id'); do
  TOTAL_COUNT=$((TOTAL_COUNT + 1))
  TAGS=$(echo "${INSTANCES}" | jq -r ".[] | select(.Id==\"${INSTANCE_ID}\") | .Tags // []")

  for TAG in "${REQUIRED_TAGS[@]}"; do
    HAS_TAG=$(echo "${TAGS}" | jq -r ".[] | select(.Key==\"${TAG}\") | .Value // empty" 2>/dev/null)
    if [ -z "${HAS_TAG}" ]; then
      echo "MANCANTE: ${INSTANCE_ID} → tag '${TAG}'"
      UNTAGGED_COUNT=$((UNTAGGED_COUNT + 1))
    fi
  done
done

COMPLIANCE=$((100 - (UNTAGGED_COUNT * 100 / (TOTAL_COUNT * ${#REQUIRED_TAGS[@]}))))
echo ""
echo "Totale istanze: ${TOTAL_COUNT}"
echo "Tag mancanti: ${UNTAGGED_COUNT}"
echo "Compliance: ${COMPLIANCE}%"
```

---

## Cost allocation — Showback e Chargeback

### Differenza tra Showback e Chargeback

| Aspetto | Showback | Chargeback |
|---|---|---|
| **Definizione** | Visibilità dei costi per team senza ri-fatturazione | Costi addebitati al budget del team |
| **Complessità** | Bassa | Alta |
| **Prerequisiti** | Tagging base | Tagging completo + sistema contabile |
| **Effetto** | Consapevolezza | Accountability finanziaria |
| **Quando usare** | Fasi iniziali FinOps, piccole organizzazioni | Organizzazioni mature, grandi divisioni |

### Modello di allocazione costi

```
Costo cloud totale
├── Costo diretto allocabile (70-85%)
│   ├── Compute → team owner (tag)
│   ├── Storage → team owner (tag)
│   ├── Database → team owner (tag)
│   └── Network egress → team owner (proporzionale)
│
├── Costo condiviso allocabile (10-20%)
│   ├── Kubernetes cluster → proporzionale per namespace/pod
│   ├── Load balancer condiviso → proporzionale per traffico
│   ├── VPN/networking → split equo o per consumo
│   └── Monitoring/logging → proporzionale per volume
│
└── Costo non allocabile (< 5%)
    ├── Support plan
    ├── Organization-level services
    └── Data transfer inter-region condiviso
```

### AWS — Cost allocation con Cost Categories

```
# AWS Cost Categories — definizione
Name: team-allocation

Rules:
  - Rule: Platform Team
    Type: REGULAR
    Value: platform
    MatchingCriteria:
      - Key: "team"
        Values: ["platform"]
        MatchOptions: ["EQUALS"]

  - Rule: Frontend Team
    Type: REGULAR
    Value: frontend
    MatchingCriteria:
      - Key: "team"
        Values: ["frontend"]
        MatchOptions: ["EQUALS"]

  - Rule: Shared Infrastructure
    Type: REGULAR
    Value: shared
    MatchingCriteria:
      - Key: "team"
        Values: ["shared", ""]
        MatchOptions: ["EQUALS", "ABSENT"]

  - Rule: Split Shared Costs
    Type: INHERITED_VALUE
    Value: team
    InheritedValueDimension:
      DimensionName: TAG
      DimensionKey: team
```

### Report showback settimanale

```python
#!/usr/bin/env python3
"""Genera report showback settimanale per team."""

import boto3
import json
from datetime import datetime, timedelta, timezone

def generate_showback_report():
    ce = boto3.client('ce')
    end = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    start = (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d')

    response = ce.get_cost_and_usage(
        TimePeriod={'Start': start, 'End': end},
        Granularity='DAILY',
        Metrics=['UnblendedCost', 'UsageQuantity'],
        GroupBy=[
            {'Type': 'TAG', 'Key': 'team'},
            {'Type': 'DIMENSION', 'Key': 'SERVICE'}
        ]
    )

    report = {}
    for result in response['ResultsByTime']:
        date = result['TimePeriod']['Start']
        for group in result['Groups']:
            team = group['Keys'][0].replace('team$', '') or 'untagged'
            service = group['Keys'][1]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])

            if team not in report:
                report[team] = {'total': 0.0, 'services': {}}
            report[team]['total'] += cost
            report[team]['services'][service] = (
                report[team]['services'].get(service, 0.0) + cost
            )

    # Ordinare per costo decrescente
    sorted_teams = sorted(
        report.items(),
        key=lambda x: x[1]['total'],
        reverse=True
    )

    print(f"=== Showback Report {start} → {end} ===\n")
    for team, data in sorted_teams:
        print(f"Team: {team}")
        print(f"  Totale: ${data['total']:.2f}")
        top_services = sorted(
            data['services'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        for svc, svc_cost in top_services:
            print(f"  - {svc}: ${svc_cost:.2f}")
        print()

    return report

if __name__ == '__main__':
    generate_showback_report()
```

---

## Ottimizzazione costi — Right-sizing

### Cos'è il right-sizing

Il right-sizing consiste nell'adattare il tipo e la dimensione delle risorse cloud all'utilizzo effettivo, eliminando over-provisioning senza impattare le prestazioni.

### Processo di right-sizing

```
1. Raccolta metriche (14-30 giorni minimo)
   ├── CPU utilization (avg, p95, p99)
   ├── Memory utilization (avg, max)
   ├── Network I/O (avg, peak)
   ├── Disk I/O (IOPS, throughput)
   └── GPU utilization (se applicabile)

2. Analisi
   ├── Instance sottoutilizzate (CPU avg < 20%, mem avg < 30%)
   ├── Instance sovraccariche (CPU p99 > 90%, mem p99 > 85%)
   ├── Seasonal patterns (variazioni giornaliere, settimanali)
   └── Growth trend (proiezione 3-6 mesi)

3. Raccomandazione
   ├── Downsize (CPU/mem sottoutilizzati)
   ├── Upsize (bottleneck prestazionale)
   ├── Change family (compute-optimized vs memory-optimized)
   ├── Graviton/ARM (30% risparmio AWS, Ampere su Azure/GCP)
   └── Right-size storage (GP2→GP3, provisioned→on-demand)

4. Implementazione
   ├── Ambiente non-prod prima
   ├── Monitoring post-cambio (24-72h)
   ├── Rollback plan
   └── Documentazione del risparmio
```

### AWS — Right-sizing con CloudWatch

```bash
# Identificare EC2 sottoutilizzate (CPU < 20% avg su 14 giorni)
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0123456789abcdef0 \
  --start-time "$(date -u -d '14 days ago' +%Y-%m-%dT%H:%M:%S)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
  --period 86400 \
  --statistics Average Maximum \
  --output json | jq '.Datapoints | sort_by(.Timestamp)'

# AWS Cost Explorer right-sizing recommendations
aws ce get-rightsizing-recommendation \
  --service AmazonEC2 \
  --configuration '{"RecommendationTarget":"SAME_INSTANCE_FAMILY","BenefitsConsidered":true}' \
  --output json
```

### Right-sizing RDS

```bash
# Metriche RDS da verificare
# CPUUtilization, FreeableMemory, ReadIOPS, WriteIOPS, DatabaseConnections

aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=mydb-prod \
  --start-time "$(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
  --period 3600 \
  --statistics Average Maximum p95

# Esempio: db.r6g.2xlarge → db.r6g.xlarge se
# - CPU avg < 25% e max < 60%
# - FreeableMemory > 50% del totale
# - DatabaseConnections < 50% del max
```

### Right-sizing Kubernetes pod

```yaml
# Vertical Pod Autoscaler (VPA) — raccomandazioni automatiche
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: myapp-vpa
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  updatePolicy:
    updateMode: "Off"  # Solo raccomandazioni, no auto-update
  resourcePolicy:
    containerPolicies:
      - containerName: myapp
        minAllowed:
          cpu: "50m"
          memory: "64Mi"
        maxAllowed:
          cpu: "2"
          memory: "4Gi"
```

```bash
# Leggere raccomandazioni VPA
kubectl describe vpa myapp-vpa -n production

# Output esempio:
# Recommendation:
#   Container Recommendations:
#     Container Name: myapp
#     Lower Bound:    Cpu: 100m, Memory: 128Mi
#     Target:         Cpu: 250m, Memory: 256Mi
#     Upper Bound:    Cpu: 500m, Memory: 512Mi
#     Uncapped Target: Cpu: 250m, Memory: 256Mi
```

---

## Reserved Instances e Savings Plans

### Confronto RI vs Savings Plans

| Aspetto | Reserved Instances | Savings Plans |
|---|---|---|
| **Flessibilità** | Bassa (locked a instance type/region) | Alta (qualsiasi instance type/region) |
| **Risparmio** | Fino a 72% (All Upfront 3y) | Fino a 66% (All Upfront 3y) |
| **Scope** | Singolo account o linked | Singolo account o Organization |
| **Commitment** | Instance type specifico | $/ora di spesa compute |
| **Coverage** | EC2, RDS, ElastiCache, etc. | EC2, Fargate, Lambda |
| **Termine** | 1 anno o 3 anni | 1 anno o 3 anni |

### Strategia di commitment

```
Coverage target: 60-80% del baseline steady-state

Distribuzione raccomandata:
├── 40-50% → Savings Plans Compute (max flessibilità)
├── 20-30% → Reserved Instances (max risparmio per workload stabili)
└── 20-40% → On-demand / Spot (elasticità)

Regole d'oro:
1. Mai committare più dell'80% del baseline
2. Preferire 1y a 3y per la prima volta (riduce rischio)
3. All Upfront solo se cash flow lo permette (max risparmio)
4. Partial Upfront = compromesso ragionevole
5. No Upfront = flessibilità massima (risparmio minore)
6. Mixare RI + SP per bilanciare risparmio e flessibilità
```

### Calcolo break-even

```python
#!/usr/bin/env python3
"""Calcolo break-even per Reserved Instances vs On-Demand."""

def calculate_breakeven(
    on_demand_hourly: float,
    ri_upfront: float,
    ri_hourly: float,
    term_months: int
) -> dict:
    term_hours = term_months * 730  # ore medie per mese
    on_demand_total = on_demand_hourly * term_hours
    ri_total = ri_upfront + (ri_hourly * term_hours)
    saving_total = on_demand_total - ri_total
    saving_pct = (saving_total / on_demand_total) * 100

    if ri_hourly < on_demand_hourly:
        hourly_saving = on_demand_hourly - ri_hourly
        breakeven_hours = ri_upfront / hourly_saving if hourly_saving > 0 else 0
        breakeven_months = breakeven_hours / 730
    else:
        breakeven_months = float('inf')

    return {
        'on_demand_total': on_demand_total,
        'ri_total': ri_total,
        'saving_total': saving_total,
        'saving_pct': saving_pct,
        'breakeven_months': breakeven_months
    }


# Esempio: m6i.xlarge in eu-west-1
scenarios = {
    'No Upfront 1y': calculate_breakeven(
        on_demand_hourly=0.192,
        ri_upfront=0,
        ri_hourly=0.121,
        term_months=12
    ),
    'Partial Upfront 1y': calculate_breakeven(
        on_demand_hourly=0.192,
        ri_upfront=670,
        ri_hourly=0.057,
        term_months=12
    ),
    'All Upfront 1y': calculate_breakeven(
        on_demand_hourly=0.192,
        ri_upfront=1150,
        ri_hourly=0,
        term_months=12
    ),
    'All Upfront 3y': calculate_breakeven(
        on_demand_hourly=0.192,
        ri_upfront=2150,
        ri_hourly=0,
        term_months=36
    ),
}

for name, result in scenarios.items():
    print(f"\n{name}:")
    print(f"  On-demand totale: ${result['on_demand_total']:.0f}")
    print(f"  RI totale: ${result['ri_total']:.0f}")
    print(f"  Risparmio: ${result['saving_total']:.0f} ({result['saving_pct']:.1f}%)")
    print(f"  Break-even: {result['breakeven_months']:.1f} mesi")
```

### Monitoraggio RI/SP utilization

```bash
# AWS — utilizzo RI
aws ce get-reservation-utilization \
  --time-period Start="$(date -u -d '30 days ago' +%Y-%m-%d)",End="$(date -u +%Y-%m-%d)" \
  --granularity MONTHLY \
  --output json | jq '.UtilizationsByTime[0].Total'

# AWS — coverage RI/SP
aws ce get-savings-plans-coverage \
  --time-period Start="$(date -u -d '30 days ago' +%Y-%m-%d)",End="$(date -u +%Y-%m-%d)" \
  --granularity MONTHLY \
  --output json

# Alert se utilization < 80%
# Configurare CloudWatch alarm su RI utilization
```

---

## Spot e Preemptible instances

### Quando usare Spot instances

| Adatto ✅ | Non adatto ❌ |
|---|---|
| Batch processing | Database primario |
| CI/CD runner | Stateful workload critici |
| Dev/test environments | Singleton service |
| Data processing (Spark, EMR) | API con SLA stretto |
| Machine learning training | Real-time payment processing |
| Rendering, encoding | Primary Kubernetes control plane |
| Web application stateless (con fallback) | Workload con cold start lungo |

### Strategie per ridurre rischio di interruzione

```
1. Diversificazione instance type
   → Specificare 5-10 tipi di istanza diversi
   → Usare capacity-optimized allocation strategy
   → Mescolare famiglie diverse (m6i, m6a, m5, c6i, c6a)

2. Diversificazione Availability Zone
   → Distribuire su tutte le AZ disponibili

3. Graceful shutdown
   → Monitorare termination notice (2 minuti su AWS, 30s su GCP)
   → Salvare stato, drenare connessioni
   → Checkpoint per batch processing

4. Mixed instance policy
   → Usare ASG con mix On-Demand + Spot
   → On-Demand per base, Spot per burst
```

### AWS — Auto Scaling Group con Spot

```json
{
  "AutoScalingGroupName": "myapp-asg",
  "MixedInstancesPolicy": {
    "LaunchTemplate": {
      "LaunchTemplateSpecification": {
        "LaunchTemplateName": "myapp-lt",
        "Version": "$Latest"
      },
      "Overrides": [
        {"InstanceType": "m6i.xlarge"},
        {"InstanceType": "m6a.xlarge"},
        {"InstanceType": "m5.xlarge"},
        {"InstanceType": "c6i.xlarge"},
        {"InstanceType": "c6a.xlarge"},
        {"InstanceType": "r6i.xlarge"}
      ]
    },
    "InstancesDistribution": {
      "OnDemandBaseCapacity": 2,
      "OnDemandPercentageAboveBaseCapacity": 20,
      "SpotAllocationStrategy": "capacity-optimized",
      "SpotMaxPrice": ""
    }
  },
  "MinSize": 2,
  "MaxSize": 20,
  "DesiredCapacity": 6
}
```

### Kubernetes — Spot node pool con Karpenter

```yaml
# Karpenter NodePool con Spot
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: spot-workloads
spec:
  template:
    spec:
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values:
            - m6i.xlarge
            - m6a.xlarge
            - m5.xlarge
            - c6i.xlarge
            - c6a.xlarge
        - key: topology.kubernetes.io/zone
          operator: In
          values:
            - eu-west-1a
            - eu-west-1b
            - eu-west-1c
      nodeClassRef:
        apiVersion: karpenter.k8s.aws/v1
        kind: EC2NodeClass
        name: default
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
  limits:
    cpu: "100"
    memory: 400Gi
```

---

## Eliminazione sprechi

### Categorie di spreco cloud

```
Spreco cloud totale stimato: 25-35% della spesa (Flexera 2025)

├── Risorse idle (10-15%)
│   ├── EC2/VM non utilizzate (CPU < 5%, no traffic)
│   ├── RDS/database dev dimenticati
│   ├── Load balancer senza backend
│   └── ElastiCache/Redis senza connessioni
│
├── Over-provisioning (8-12%)
│   ├── Instance troppo grandi per il workload
│   ├── Storage sovra-provisionato (GP2 vs GP3, IOPS non usati)
│   ├── Database instance sovradimensionate
│   └── Kubernetes request >> actual usage
│
├── Risorse orfane (3-5%)
│   ├── EBS volume non attaccati
│   ├── Elastic IP non associati
│   ├── Snapshot obsoleti
│   ├── AMI/image non utilizzate
│   └── Security group non referenziati
│
├── Ambiente non-prod attivo 24/7 (3-5%)
│   ├── Dev/staging attivi fuori orario
│   ├── Demo environment permanenti
│   └── Load test environment dimenticati
│
└── Architettura inefficiente (2-5%)
    ├── Data transfer evitabile (cross-region, cross-AZ)
    ├── NAT Gateway per traffico S3/DynamoDB (usare VPC endpoint)
    ├── CloudFront/CDN non configurato (origin direct)
    └── Log retention eccessiva (CloudWatch → S3 → Glacier)
```

### Script di identificazione risorse orfane

```bash
#!/usr/bin/env bash
# Identificare risorse orfane in AWS
set -euo pipefail

REGION="${1:-eu-west-1}"
echo "=== Risorse orfane in ${REGION} ==="

echo ""
echo "--- EBS Volume non attaccati ---"
aws ec2 describe-volumes \
  --region "${REGION}" \
  --filters Name=status,Values=available \
  --query 'Volumes[].{ID:VolumeId,Size:Size,Created:CreateTime}' \
  --output table

echo ""
echo "--- Elastic IP non associati ---"
aws ec2 describe-addresses \
  --region "${REGION}" \
  --query 'Addresses[?AssociationId==null].{IP:PublicIp,AllocId:AllocationId}' \
  --output table

echo ""
echo "--- Snapshot > 90 giorni ---"
CUTOFF=$(date -u -d '90 days ago' +%Y-%m-%dT%H:%M:%S)
aws ec2 describe-snapshots \
  --region "${REGION}" \
  --owner-ids self \
  --query "Snapshots[?StartTime<'${CUTOFF}'].{ID:SnapshotId,Size:VolumeSize,Date:StartTime}" \
  --output table

echo ""
echo "--- Load Balancer senza target ---"
for ALB_ARN in $(aws elbv2 describe-load-balancers \
  --region "${REGION}" \
  --query 'LoadBalancers[].LoadBalancerArn' \
  --output text); do
  TG_COUNT=$(aws elbv2 describe-target-groups \
    --region "${REGION}" \
    --load-balancer-arn "${ALB_ARN}" \
    --query 'TargetGroups | length(@)' \
    --output text)
  if [ "${TG_COUNT}" = "0" ]; then
    ALB_NAME=$(aws elbv2 describe-load-balancers \
      --region "${REGION}" \
      --load-balancer-arns "${ALB_ARN}" \
      --query 'LoadBalancers[0].LoadBalancerName' \
      --output text)
    echo "LB senza target: ${ALB_NAME}"
  fi
done

echo ""
echo "--- RDS senza connessioni (ultimi 7 giorni) ---"
for DB_ID in $(aws rds describe-db-instances \
  --region "${REGION}" \
  --query 'DBInstances[].DBInstanceIdentifier' \
  --output text); do
  MAX_CONN=$(aws cloudwatch get-metric-statistics \
    --region "${REGION}" \
    --namespace AWS/RDS \
    --metric-name DatabaseConnections \
    --dimensions Name=DBInstanceIdentifier,Value="${DB_ID}" \
    --start-time "$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S)" \
    --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
    --period 86400 \
    --statistics Maximum \
    --query 'Datapoints[].Maximum | max(@)' \
    --output text 2>/dev/null)
  if [ "${MAX_CONN}" = "0" ] || [ "${MAX_CONN}" = "0.0" ] || [ -z "${MAX_CONN}" ]; then
    echo "RDS senza connessioni: ${DB_ID}"
  fi
done
```

### Scheduling ambienti non-prod

```python
#!/usr/bin/env python3
"""Lambda per scheduling on/off ambienti non-prod."""

import boto3
from datetime import datetime, timezone

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    action = event.get('action', 'stop')  # 'start' o 'stop'
    target_env = event.get('environment', 'development')

    filters = [
        {'Name': 'tag:environment', 'Values': [target_env]},
        {'Name': 'tag:automation', 'Values': ['schedule-off']},
    ]

    if action == 'stop':
        filters.append({'Name': 'instance-state-name', 'Values': ['running']})
        instances = ec2.describe_instances(Filters=filters)
        instance_ids = [
            i['InstanceId']
            for r in instances['Reservations']
            for i in r['Instances']
        ]
        if instance_ids:
            ec2.stop_instances(InstanceIds=instance_ids)
            print(f"Spente {len(instance_ids)} istanze {target_env}: {instance_ids}")
        else:
            print(f"Nessuna istanza {target_env} da spegnere.")

    elif action == 'start':
        filters.append({'Name': 'instance-state-name', 'Values': ['stopped']})
        instances = ec2.describe_instances(Filters=filters)
        instance_ids = [
            i['InstanceId']
            for r in instances['Reservations']
            for i in r['Instances']
        ]
        if instance_ids:
            ec2.start_instances(InstanceIds=instance_ids)
            print(f"Avviate {len(instance_ids)} istanze {target_env}: {instance_ids}")
        else:
            print(f"Nessuna istanza {target_env} da avviare.")

    return {'action': action, 'count': len(instance_ids) if instance_ids else 0}
```

```
# EventBridge schedule (cron)
# Spegnere dev alle 19:00 CET (18:00 UTC)
cron(0 18 ? * MON-FRI *)   → action: stop, environment: development

# Accendere dev alle 08:00 CET (07:00 UTC)
cron(0 7 ? * MON-FRI *)    → action: start, environment: development

# Spegnere staging venerdì sera
cron(0 18 ? * FRI *)        → action: stop, environment: staging

# Accendere staging lunedì mattina
cron(0 7 ? * MON *)         → action: start, environment: staging

# Risparmio stimato: 65-70% per dev, 25-30% per staging
```

---

## Kubernetes cost management

### kubecost

kubecost è lo strumento standard per la gestione dei costi Kubernetes. Fornisce:

- Cost allocation per namespace, deployment, label.
- Raccomandazioni di right-sizing per container.
- Idle cost detection.
- Network cost allocation.
- Savings recommendation.

```bash
# Installare kubecost
helm repo add kubecost https://kubecost.github.io/cost-analyzer/
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost \
  --create-namespace \
  --set kubecostToken="${KUBECOST_TOKEN}" \
  --set prometheus.server.retention=30d
```

### Allocazione costi Kubernetes

```
Costo cluster Kubernetes
├── Costo nodo (compute)
│   ├── Allocato a pod (request-based o usage-based)
│   ├── Idle (richieste < capacità nodo)
│   └── System overhead (kubelet, kube-proxy, DaemonSet)
│
├── Costo storage (PVC/PV)
│   └── Allocato a namespace del PVC
│
├── Costo network
│   ├── Ingress → namespace del servizio
│   ├── Egress → namespace di origine
│   └── Cross-zone → proporzionale al traffico
│
└── Costo control plane
    └── Allocato proporzionalmente o come overhead fisso
```

### Resource quota per cost control

```yaml
# ResourceQuota per namespace di team
apiVersion: v1
kind: ResourceQuota
metadata:
  name: team-frontend-quota
  namespace: frontend
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "10"
    services.loadbalancers: "2"
    count/deployments.apps: "20"
    count/statefulsets.apps: "5"
    count/jobs.batch: "50"

---
# LimitRange per default
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: frontend
spec:
  limits:
    - type: Container
      default:
        cpu: "500m"
        memory: 512Mi
      defaultRequest:
        cpu: "100m"
        memory: 128Mi
      max:
        cpu: "4"
        memory: 8Gi
      min:
        cpu: "50m"
        memory: "64Mi"
```

### OpenCost — alternativa open source

```bash
# Installare OpenCost (100% open source, CNCF sandbox)
helm repo add opencost https://opencost.github.io/opencost-helm-chart
helm install opencost opencost/opencost \
  --namespace opencost \
  --create-namespace \
  --set opencost.exporter.cloudProviderApiKey="${CLOUD_API_KEY}"

# API query — costo per namespace ultimo giorno
curl -s "http://opencost.opencost:9003/allocation/compute?window=1d&aggregate=namespace" | \
  jq '.data[0] | to_entries[] | {namespace: .key, totalCost: .value.totalCost}'
```

---

## Confronto costi multi-cloud

### Matrice comparativa servizi principali

| Servizio | AWS | Azure | GCP | Differenza tipica |
|---|---|---|---|---|
| VM general (4 vCPU, 16GB) | ~$140/mese | ~$135/mese | ~$130/mese | GCP 5-8% meno |
| Managed K8s control plane | $73/cluster | Gratuito (AKS) | $73/cluster | Azure vantaggio |
| Object storage (TB/mese) | $23 (S3 Standard) | $21 (Hot) | $20 (Standard) | Simile |
| Managed PostgreSQL (4vCPU) | ~$250/mese | ~$240/mese | ~$230/mese | Simile |
| Serverless (1M invocazioni) | ~$0.20 | ~$0.20 | ~$0.40 | GCP più caro |
| Egress (TB/mese) | $90 | $87 | $80-120 | Variabile |
| Support Enterprise | 15% della spesa o min $15k | $1000+/mese | 4% della spesa | Molto variabile |

*Prezzi indicativi eu-west-1/westeurope — verificare sempre il pricing corrente.*

### Considerazioni multi-cloud

```
Fattori oltre il prezzo unitario:
├── Sconti volume e committed use
│   (ogni cloud ha struttura diversa, negoziare case-by-case)
├── Costo di egress tra cloud
│   (può annullare risparmi da multi-cloud)
├── Costo operativo
│   (team skillset, tooling, formazione)
├── Lock-in vs portabilità
│   (servizi managed = lock-in ma meno ops)
└── Compliance e data residency
    (requisiti legali possono limitare le scelte)
```

---

## Budgeting e forecasting

### Processo di budgeting cloud

```
Budget cloud = Bottom-up + Top-down

Bottom-up:
├── Inventario workload correnti
├── Costo attuale per team/servizio
├── Nuovi progetti pianificati
├── Growth projection (storica + business plan)
└── Fattore di ottimizzazione attesa (-10-20%)

Top-down:
├── Revenue target / growth target
├── % revenue allocata a infrastruttura
├── Benchmark di settore (cloud cost / revenue)
└── COGS target per prodotto

Riconciliazione:
├── Gap analysis bottom-up vs top-down
├── Prioritizzazione ottimizzazioni
├── Piano di commitment (RI/SP)
└── Buffer per imprevisti (5-10%)
```

### AWS Budget con alert

```bash
# Creare budget con alert
aws budgets create-budget \
  --account-id "${AWS_ACCOUNT_ID}" \
  --budget '{
    "BudgetName": "monthly-total",
    "BudgetLimit": {"Amount": "50000", "Unit": "USD"},
    "BudgetType": "COST",
    "TimeUnit": "MONTHLY",
    "CostFilters": {},
    "CostTypes": {
      "IncludeTax": true,
      "IncludeSubscription": true,
      "UseBlended": false,
      "IncludeRefund": false,
      "IncludeCredit": false
    }
  }' \
  --notifications-with-subscribers '[
    {
      "Notification": {
        "NotificationType": "ACTUAL",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 80,
        "ThresholdType": "PERCENTAGE"
      },
      "Subscribers": [
        {"SubscriptionType": "EMAIL", "Address": "finops@company.io"},
        {"SubscriptionType": "SNS", "Address": "arn:aws:sns:eu-west-1:123456:budget-alerts"}
      ]
    },
    {
      "Notification": {
        "NotificationType": "FORECASTED",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 100,
        "ThresholdType": "PERCENTAGE"
      },
      "Subscribers": [
        {"SubscriptionType": "EMAIL", "Address": "finops@company.io"}
      ]
    }
  ]'
```

### Forecasting con modelli di proiezione

```python
#!/usr/bin/env python3
"""Forecasting costi cloud con media mobile e trend."""

import boto3
import json
from datetime import datetime, timedelta, timezone

def forecast_costs(months_history: int = 6, months_forecast: int = 3):
    ce = boto3.client('ce')
    end = datetime.now(timezone.utc).replace(day=1).strftime('%Y-%m-%d')
    start = (
        datetime.now(timezone.utc).replace(day=1) - timedelta(days=months_history * 31)
    ).replace(day=1).strftime('%Y-%m-%d')

    response = ce.get_cost_and_usage(
        TimePeriod={'Start': start, 'End': end},
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    costs = []
    for result in response['ResultsByTime']:
        month = result['TimePeriod']['Start']
        cost = float(result['Groups'][0]['Metrics']['UnblendedCost']['Amount'])
        if result.get('Groups') else float(
            result['Total']['UnblendedCost']['Amount']
        )
        costs.append({'month': month, 'cost': cost})

    # Calcolare trend (crescita mensile media)
    if len(costs) >= 2:
        growth_rates = []
        for i in range(1, len(costs)):
            if costs[i-1]['cost'] > 0:
                rate = (costs[i]['cost'] - costs[i-1]['cost']) / costs[i-1]['cost']
                growth_rates.append(rate)
        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
    else:
        avg_growth = 0

    # Proiezione
    last_cost = costs[-1]['cost']
    forecast = []
    for i in range(1, months_forecast + 1):
        projected = last_cost * (1 + avg_growth) ** i
        forecast.append({
            'month': f'+{i} mesi',
            'projected_cost': projected,
            'growth_rate': avg_growth
        })

    return {
        'historical': costs,
        'avg_monthly_growth': f"{avg_growth * 100:.1f}%",
        'forecast': forecast
    }
```

---

## Anomaly detection

### Strategie di detection

| Strategia | Descrizione | Latenza |
|---|---|---|
| **Threshold statico** | Alert se costo > soglia fissa | Immediato |
| **Deviazione percentuale** | Alert se costo > X% rispetto a media | Ore |
| **Z-score** | Alert se costo fuori N deviazioni standard | Ore |
| **ML-based** | Modelli che apprendono pattern normali | Ore-giorni |
| **Rate of change** | Alert se tasso di crescita anomalo | Minuti-ore |

### AWS Cost Anomaly Detection

```bash
# Creare monitor per anomalie di costo
aws ce create-anomaly-monitor \
  --anomaly-monitor '{
    "MonitorName": "service-level-monitor",
    "MonitorType": "DIMENSIONAL",
    "MonitorDimension": "SERVICE"
  }'

# Creare subscription per notifiche
aws ce create-anomaly-subscription \
  --anomaly-subscription '{
    "SubscriptionName": "cost-anomaly-alerts",
    "MonitorArnList": ["arn:aws:ce::123456:anomalymonitor/monitor-id"],
    "Subscribers": [
      {
        "Address": "finops@company.io",
        "Type": "EMAIL"
      },
      {
        "Address": "arn:aws:sns:eu-west-1:123456:cost-anomaly",
        "Type": "SNS"
      }
    ],
    "Threshold": 100,
    "Frequency": "IMMEDIATE"
  }'
```

### Script di anomaly detection custom

```python
#!/usr/bin/env python3
"""Anomaly detection su costi giornalieri con Z-score."""

import boto3
import statistics
from datetime import datetime, timedelta, timezone

def detect_anomalies(
    lookback_days: int = 30,
    z_threshold: float = 2.0,
    min_anomaly_amount: float = 50.0
):
    ce = boto3.client('ce')
    end = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    start = (datetime.now(timezone.utc) - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

    response = ce.get_cost_and_usage(
        TimePeriod={'Start': start, 'End': end},
        Granularity='DAILY',
        Metrics=['UnblendedCost'],
        GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
    )

    # Raccogliere costi per servizio
    service_costs = {}
    for result in response['ResultsByTime']:
        date = result['TimePeriod']['Start']
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            if service not in service_costs:
                service_costs[service] = []
            service_costs[service].append({'date': date, 'cost': cost})

    anomalies = []
    for service, daily_costs in service_costs.items():
        costs = [d['cost'] for d in daily_costs]
        if len(costs) < 7:  # servono almeno 7 giorni di dati
            continue

        mean = statistics.mean(costs[:-1])  # escludere ultimo giorno
        stdev = statistics.stdev(costs[:-1]) if len(costs) > 2 else 0
        latest = costs[-1]
        latest_date = daily_costs[-1]['date']

        if stdev > 0:
            z_score = (latest - mean) / stdev
        else:
            z_score = 0

        deviation = latest - mean

        if abs(z_score) > z_threshold and abs(deviation) > min_anomaly_amount:
            anomalies.append({
                'service': service,
                'date': latest_date,
                'cost': latest,
                'mean': mean,
                'z_score': z_score,
                'deviation': deviation,
                'deviation_pct': (deviation / mean * 100) if mean > 0 else 0
            })

    anomalies.sort(key=lambda x: abs(x['z_score']), reverse=True)

    for a in anomalies:
        direction = "SOPRA" if a['z_score'] > 0 else "SOTTO"
        print(f"ANOMALIA [{a['service']}] {a['date']}")
        print(f"  Costo: ${a['cost']:.2f} ({direction} media ${a['mean']:.2f})")
        print(f"  Z-score: {a['z_score']:.2f}, Deviazione: {a['deviation_pct']:.1f}%")
        print()

    return anomalies
```

---

## Governance policies

### AWS — Service Control Policies (SCP)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyExpensiveInstances",
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "ForAnyValue:StringLike": {
          "ec2:InstanceType": [
            "*.metal",
            "*.24xlarge",
            "*.16xlarge",
            "p4*",
            "p5*",
            "dl1*",
            "inf2*",
            "trn1*"
          ]
        }
      }
    },
    {
      "Sid": "DenyExpensiveRegions",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "eu-west-1",
            "eu-central-1",
            "us-east-1"
          ]
        }
      }
    },
    {
      "Sid": "RequireIMDSv2",
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotEquals": {
          "ec2:MetadataHttpTokens": "required"
        }
      }
    }
  ]
}
```

### Azure Policy per cost governance

```json
{
  "mode": "All",
  "policyRule": {
    "if": {
      "allOf": [
        {
          "field": "type",
          "equals": "Microsoft.Compute/virtualMachines"
        },
        {
          "not": {
            "field": "Microsoft.Compute/virtualMachines/sku.name",
            "in": [
              "Standard_B2s",
              "Standard_B2ms",
              "Standard_D2s_v5",
              "Standard_D4s_v5",
              "Standard_D8s_v5",
              "Standard_E2s_v5",
              "Standard_E4s_v5"
            ]
          }
        }
      ]
    },
    "then": {
      "effect": "deny"
    }
  }
}
```

### GCP — Organization Policy constraints

```yaml
# Terraform — limitare VM size su GCP
resource "google_org_policy_policy" "restrict_vm_size" {
  name   = "organizations/${var.org_id}/policies/compute.restrictMachineTypes"
  parent = "organizations/${var.org_id}"

  spec {
    rules {
      values {
        allowed_values = [
          "projects/*/zones/*/machineTypes/e2-standard-2",
          "projects/*/zones/*/machineTypes/e2-standard-4",
          "projects/*/zones/*/machineTypes/e2-standard-8",
          "projects/*/zones/*/machineTypes/n2-standard-2",
          "projects/*/zones/*/machineTypes/n2-standard-4",
          "projects/*/zones/*/machineTypes/n2-standard-8"
        ]
      }
    }
  }
}
```

### Policy di billing alert

```yaml
# Terraform — AWS budget per team
resource "aws_budgets_budget" "team_budget" {
  for_each = var.team_budgets

  name         = "budget-${each.key}"
  budget_type  = "COST"
  limit_amount = each.value.monthly_limit
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "TagKeyValue"
    values = ["user:team$${each.key}"]
  }

  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = [each.value.email]
  }

  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "FORECASTED"
    subscriber_email_addresses = [each.value.email, "finops@company.io"]
  }
}
```

---

## Struttura del team FinOps

### Modello organizzativo

```
┌─────────────────────────────────────────────────┐
│              LEADERSHIP / CFO                   │
│  Approva budget, strategy, commitment           │
└─────────────┬───────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────┐
│           FINOPS TEAM (centralized)             │
│                                                 │
│  FinOps Lead                                    │
│  ├── Analista costi cloud (1-2 per 50M spend)   │
│  ├── Automation engineer (1)                    │
│  └── FinOps practitioner per BU (embedded)      │
│                                                 │
│  Responsabilità:                                │
│  ├── Tooling e dashboard                        │
│  ├── Policy e governance                        │
│  ├── Training e enablement                      │
│  ├── Commitment management (RI/SP)              │
│  ├── Vendor relationship                        │
│  └── Reporting a leadership                     │
└─────────────┬───────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│ Team A │ │ Team B │ │ Team C │
│        │ │        │ │        │
│ Owner  │ │ Owner  │ │ Owner  │
│ del    │ │ del    │ │ del    │
│ costo  │ │ costo  │ │ costo  │
└────────┘ └────────┘ └────────┘
```

### Ruoli e responsabilità

| Ruolo | Responsabilità |
|---|---|
| **FinOps Lead** | Strategia, governance, reporting a C-level, vendor management. |
| **Cloud cost analyst** | Analisi costi, raccomandazioni, forecast, anomaly investigation. |
| **Automation engineer** | Tooling, scripting, integrazione con CI/CD, dashboard. |
| **Engineering team lead** | Right-sizing, architettura cost-aware, implementazione raccomandazioni. |
| **Product manager** | Unit economics, cost per feature decision, prioritizzazione. |
| **Finance** | Budget approvazione, chargeback processing, contract review. |

### Cadenza delle review

| Review | Frequenza | Partecipanti | Focus |
|---|---|---|---|
| Daily cost check | Giornaliera | FinOps team | Anomalie, trend |
| Team cost review | Settimanale | Team lead + FinOps | Waste, right-sizing, action items |
| FinOps board | Mensile | Leadership + FinOps | Budget vs actual, forecast, commitment |
| Optimization sprint | Trimestrale | Engineering + FinOps | Deep-dive ottimizzazioni |
| Contract review | Annuale | Finance + FinOps | Rinnovi, negoziazioni, benchmark |

---

## Vendor management e negoziazioni

### Strategia di negoziazione

```
Preparazione:
├── Analisi dello spending storico (12-24 mesi)
├── Proiezione crescita (12-36 mesi)
├── Benchmark pricing con alternative
├── Identificazione leverage (multi-cloud, commitment volume)
└── Team negotiation (FinOps + procurement + legal)

Leve negoziali:
├── Volume commitment → sconto aggiuntivo oltre RI/SP
├── Multi-year agreement → sconto su prezzo base
├── EDP (Enterprise Discount Program, AWS) → sconto fisso su tutti i servizi
├── MACC (Microsoft Azure Consumption Commitment) → crediti + sconto
├── CUD (Committed Use Discount, GCP) → sconto su spend commitment
├── Early renewal → condizioni migliori
└── Competitive pressure → quotazione da competitor
```

### Enterprise Discount Programs

| Programma | Cloud | Meccanismo |
|---|---|---|
| **EDP** | AWS | Sconto % su spesa totale in cambio di commitment annuale |
| **MACC** | Azure | Crediti + sconto su commitment di spesa |
| **CUD** | GCP | Sconto su spend commitment (resource-based o spend-based) |
| **PPA** | AWS | Private Pricing Amendment per servizi specifici |

### Checklist negoziazione

```
Pre-negoziazione:
- [ ] Spending forecast 1-3 anni con scenari (low/mid/high)
- [ ] Analisi RI/SP coverage e opportunità residue
- [ ] Benchmark prezzi con competitor
- [ ] Identificazione servizi con spending più alto
- [ ] Analisi costi di egress e data transfer

Durante negoziazione:
- [ ] Richiedere sconto EDP/MACC/CUD oltre RI/SP
- [ ] Negoziare crediti per migration/modernization
- [ ] Richiedere waiver su costi di egress
- [ ] Negoziare support discount per commitment alto
- [ ] Richiedere accesso anticipato a nuovi servizi
- [ ] Clausole di exit e portabilità dati

Post-negoziazione:
- [ ] Documentare tutti i termini concordati
- [ ] Monitorare compliance con commitment
- [ ] Tracking dei crediti e scadenze
- [ ] Review trimestrale con account team
```

---

## Unit economics

### Metriche di unit economics

| Metrica | Formula | Target tipico |
|---|---|---|
| **Cost per request** | Costo infra / Numero richieste | Decresce con scale |
| **Cost per user** | Costo infra / Utenti attivi | Stabile o decrescente |
| **Cost per transaction** | Costo infra / Transazioni | Target sotto margine |
| **Cost per GB processed** | Costo infra / GB elaborati | Decresce con volume |
| **Infrastructure cost ratio** | Costo infra / Revenue | 10-25% tipico SaaS |
| **COGS cloud** | Costo cloud / Revenue | Parte del gross margin |
| **Cost per deployment** | Costo CI/CD / Numero deploy | Stabile |

### Calcolo unit economics

```python
#!/usr/bin/env python3
"""Calcolo unit economics per servizio SaaS."""

from dataclasses import dataclass

@dataclass(frozen=True)
class UnitEconomics:
    service: str
    monthly_cost: float
    monthly_requests: int
    monthly_users: int
    monthly_revenue: float

    @property
    def cost_per_request(self) -> float:
        return self.monthly_cost / self.monthly_requests if self.monthly_requests else 0

    @property
    def cost_per_user(self) -> float:
        return self.monthly_cost / self.monthly_users if self.monthly_users else 0

    @property
    def infra_cost_ratio(self) -> float:
        return (self.monthly_cost / self.monthly_revenue * 100) if self.monthly_revenue else 0

    @property
    def gross_margin_impact(self) -> float:
        return 100 - self.infra_cost_ratio

    def report(self) -> str:
        return (
            f"Servizio: {self.service}\n"
            f"  Costo mensile: ${self.monthly_cost:,.0f}\n"
            f"  Costo per request: ${self.cost_per_request:.6f}\n"
            f"  Costo per utente: ${self.cost_per_user:.2f}\n"
            f"  Infra/Revenue ratio: {self.infra_cost_ratio:.1f}%\n"
            f"  Gross margin impact: {self.gross_margin_impact:.1f}%\n"
        )


# Esempio
services = [
    UnitEconomics("API Gateway", 8500, 150_000_000, 50_000, 200_000),
    UnitEconomics("Auth Service", 3200, 20_000_000, 50_000, 200_000),
    UnitEconomics("Data Pipeline", 12000, 5_000_000, 50_000, 200_000),
    UnitEconomics("Storage", 6800, 30_000_000, 50_000, 200_000),
]

total_cost = sum(s.monthly_cost for s in services)
revenue = services[0].monthly_revenue

print("=== Unit Economics Report ===\n")
for svc in services:
    print(svc.report())

print(f"TOTALE infra: ${total_cost:,.0f}")
print(f"Revenue: ${revenue:,.0f}")
print(f"Infra/Revenue: {total_cost / revenue * 100:.1f}%")
```

### Dashboard unit economics

```
KPI da tracciare nel tempo:
├── Cost per request (trend mensile)
├── Cost per user (trend mensile)
├── Infra cost / Revenue (trend trimestrale)
├── Cost efficiency index (requests / $)
├── Growth efficiency (delta users / delta cost)
└── Marginal cost (costo aggiuntivo per nuovo utente)

Allarmi:
├── Cost per request in crescita > 10% MoM
├── Infra/Revenue > 25%
├── Marginal cost in crescita
└── Cost efficiency index in calo
```

---

## Automazione FinOps

### Automazione raccomandata

| Automazione | Impatto | Complessità |
|---|---|---|
| Scheduling on/off non-prod | Alto (65-70% risparmio non-prod) | Bassa |
| Pulizia risorse orfane | Medio (3-5% risparmio) | Bassa |
| Right-sizing alert | Medio | Media |
| Tag compliance enforcement | Alto (prerequisito) | Media |
| RI/SP purchasing recommendation | Alto (30-60% risparmio) | Media |
| Auto-scaling tuning | Medio-alto | Alta |
| Storage tiering automatico | Medio | Bassa |
| Anomaly detection + auto-remediation | Alto | Alta |

### Infrastructure as Code per cost control

```hcl
# Terraform — modulo con cost awareness
module "application" {
  source = "./modules/application"

  # Cost-aware defaults
  instance_type = var.environment == "production" ? "m6i.xlarge" : "t3.medium"
  min_instances = var.environment == "production" ? 3 : 1
  max_instances = var.environment == "production" ? 20 : 3

  # Storage ottimizzato
  storage_type = "gp3"  # GP3 è 20% più economico di GP2 con stesse prestazioni
  storage_iops = var.environment == "production" ? 3000 : null
  storage_throughput = var.environment == "production" ? 125 : null

  # Scheduling tag per non-prod
  tags = merge(var.required_tags, {
    automation = var.environment != "production" ? "schedule-off" : "none"
    end-date   = var.environment == "sandbox" ? timeadd(timestamp(), "720h") : null
  })
}
```

---

## Ottimizzazione costi storage — Tiering e lifecycle

### Panoramica dei tier di storage

Lo storage rappresenta tipicamente il 15-25% della spesa cloud complessiva e tende a crescere in modo monotono: i dati si accumulano e raramente vengono eliminati. Una strategia di tiering ben progettata puo' ridurre i costi di storage del 40-70% senza impattare le prestazioni per i dati effettivamente acceduti.

#### Confronto tier per provider

| Tier | AWS S3 | Azure Blob | GCP Cloud Storage | Accesso tipico | Costo relativo |
|---|---|---|---|---|---|
| **Hot / Standard** | S3 Standard | Hot | Standard | Frequente (quotidiano) | 100% (base) |
| **Infrequent** | S3 Standard-IA | Cool (30d min) | Nearline (30d min) | Mensile | 45-55% |
| **Cold** | S3 Glacier Instant | Cold (90d min) | Coldline (90d min) | Trimestrale | 25-35% |
| **Archive** | S3 Glacier Flexible | Archive (180d min) | Archive (365d min) | Annuale o meno | 5-10% |
| **Deep Archive** | S3 Glacier Deep Archive | — | — | Rarissimo | 2-3% |
| **Intelligent** | S3 Intelligent-Tiering | Smart Tier | Autoclass | Automatico | Variabile + fee monitoring |

*Nota: i costi di retrieval aumentano inversamente al costo di storage. Glacier Deep Archive costa ~$1/GB per retrieval standard.*

#### Costi nascosti del tiering

```
Attenzione ai costi non evidenti:
├── Minimum storage duration
│   ├── S3 Standard-IA: 30 giorni (se elimini prima, paghi comunque 30d)
│   ├── Glacier Flexible: 90 giorni
│   └── Glacier Deep Archive: 180 giorni
│
├── Retrieval fees
│   ├── Standard-IA: $0.01/GB
│   ├── Glacier Instant: $0.03/GB
│   ├── Glacier Flexible (Standard): $0.01/GB + 3-5 ore
│   └── Glacier Deep Archive: $0.02/GB + 12 ore
│
├── Transition request fees
│   ├── $0.01 per 1000 richieste (S3 → Standard-IA)
│   ├── $0.02 per 1000 richieste (S3 → Glacier)
│   └── Milioni di piccoli file = costo di transizione > risparmio storage
│
└── Minimum object size
    └── Standard-IA: oggetti < 128KB fatturati come 128KB
```

### Lifecycle policy — AWS S3

```json
{
  "Rules": [
    {
      "ID": "log-lifecycle",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "logs/"
      },
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        },
        {
          "Days": 365,
          "StorageClass": "DEEP_ARCHIVE"
        }
      ],
      "Expiration": {
        "Days": 2555
      }
    },
    {
      "ID": "cleanup-incomplete-uploads",
      "Status": "Enabled",
      "Filter": {},
      "AbortIncompleteMultipartUpload": {
        "DaysAfterInitiation": 7
      }
    },
    {
      "ID": "cleanup-old-versions",
      "Status": "Enabled",
      "Filter": {},
      "NoncurrentVersionTransitions": [
        {
          "NoncurrentDays": 30,
          "StorageClass": "STANDARD_IA"
        },
        {
          "NoncurrentDays": 90,
          "StorageClass": "GLACIER"
        }
      ],
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 365
      }
    }
  ]
}
```

### Lifecycle policy — Azure Blob

```json
{
  "rules": [
    {
      "enabled": true,
      "name": "move-to-cool-then-archive",
      "type": "Lifecycle",
      "definition": {
        "actions": {
          "baseBlob": {
            "tierToCool": {
              "daysAfterModificationGreaterThan": 30
            },
            "tierToCold": {
              "daysAfterModificationGreaterThan": 90
            },
            "tierToArchive": {
              "daysAfterModificationGreaterThan": 180
            },
            "delete": {
              "daysAfterModificationGreaterThan": 2555
            }
          },
          "snapshot": {
            "delete": {
              "daysAfterCreationGreaterThan": 90
            }
          }
        },
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["logs/", "backups/"]
        }
      }
    }
  ]
}
```

### Terraform — lifecycle policy unificata

```hcl
# S3 lifecycle con Terraform
resource "aws_s3_bucket_lifecycle_configuration" "data_lifecycle" {
  bucket = aws_s3_bucket.data.id

  rule {
    id     = "log-tiering"
    status = "Enabled"

    filter {
      prefix = "logs/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 730
    }
  }

  rule {
    id     = "intelligent-tiering-data"
    status = "Enabled"

    filter {
      prefix = "data/"
    }

    transition {
      days          = 0
      storage_class = "INTELLIGENT_TIERING"
    }
  }

  rule {
    id     = "abort-multipart"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}
```

### S3 Intelligent-Tiering — configurazione

S3 Intelligent-Tiering e' raccomandato per dati con pattern di accesso imprevedibile. Muove automaticamente gli oggetti tra tier senza retrieval fees, con un costo di monitoring di $0.0025 per 1000 oggetti/mese.

```bash
# Abilitare Intelligent-Tiering con archive access tier
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket my-data-bucket \
  --id "full-tiering" \
  --intelligent-tiering-configuration '{
    "Id": "full-tiering",
    "Status": "Enabled",
    "Tierings": [
      {
        "AccessTier": "ARCHIVE_ACCESS",
        "Days": 90
      },
      {
        "AccessTier": "DEEP_ARCHIVE_ACCESS",
        "Days": 180
      }
    ]
  }'
```

### EBS/Managed Disk optimization

Oltre allo storage ad oggetti, i volumi block storage rappresentano una voce significativa. La migrazione GP2 → GP3 su AWS e' una delle ottimizzazioni piu' semplici e a basso rischio disponibili.

```
Ottimizzazione volumi block storage:

AWS EBS:
├── GP2 → GP3: stesso baseline (3000 IOPS, 125 MB/s), 20% piu' economico
│   └── GP2 1 TB = $100/mese → GP3 1 TB = $80/mese
├── io1 → io2: stesse prestazioni, 99.999% durabilita', stesso prezzo
│   └── io2 Block Express per > 64000 IOPS
├── Snapshot lifecycle: eliminare snapshot > 90 giorni non necessari
│   └── Snapshot incrementali: costo proporzionale ai delta
├── EBS Elastic Volumes: ridimensionare senza downtime
│   └── Ridurre volumi sovradimensionati (verifica con CloudWatch)
└── Encryption: nessun costo aggiuntivo (usare sempre)

Azure Managed Disks:
├── Standard HDD → Standard SSD per workload leggeri
├── Premium SSD v2: IOPS e throughput configurabili indipendentemente
├── Disk bursting: Standard SSD offre burst credit (no need Premium per burst)
└── Shared Disks: evitare dischi condivisi non utilizzati

GCP Persistent Disk:
├── pd-balanced: compromesso ideale per la maggior parte dei workload
├── pd-ssd: solo per IOPS > 15000 o throughput > 240 MB/s
├── Hyperdisk: IOPS e throughput provisionati indipendentemente
└── Snapshot scheduling: policy automatica con retention definita
```

```bash
# Identificare volumi EBS GP2 da migrare a GP3
aws ec2 describe-volumes \
  --region eu-west-1 \
  --filters Name=volume-type,Values=gp2 \
  --query 'Volumes[].{ID:VolumeId,Size:Size,State:State,AZ:AvailabilityZone}' \
  --output table

# Migrare un volume GP2 a GP3 (senza downtime)
aws ec2 modify-volume \
  --volume-id vol-0123456789abcdef0 \
  --volume-type gp3 \
  --iops 3000 \
  --throughput 125
```

### Stima del risparmio storage

```
Scenario: 100 TB di dati con distribuzione di accesso tipica
├── 20% hot (accesso frequente)        → 20 TB × $0.023/GB = $460/mese
├── 30% infrequent (accesso mensile)   → 30 TB × $0.0125/GB = $375/mese
├── 30% cold (accesso raro)            → 30 TB × $0.004/GB = $120/mese
└── 20% archive (compliance/backup)    → 20 TB × $0.00099/GB = $20/mese
                                         Totale: ~$975/mese

Senza tiering (tutto Standard):
100 TB × $0.023/GB = $2,300/mese

Risparmio: ~$1,325/mese (57%)
```

---

## Ottimizzazione costi di rete — Egress e data transfer

### Modello di pricing del data transfer

Il data transfer e' una delle voci di costo piu' sottovalutate e puo' rappresentare il 10-20% della fattura cloud. Il modello di base e' asimmetrico: **ingress gratuito, egress a pagamento**.

```
Costi di data transfer (modello semplificato):

Ingress (dati IN verso il cloud)
└── Gratuito su tutti i provider

Egress (dati OUT dal cloud)
├── Verso internet
│   ├── AWS: $0.09/GB (primi 10 TB), $0.085/GB (successivi 40 TB)
│   ├── Azure: $0.087/GB (primi 5 TB)
│   ├── GCP: $0.12/GB (primi 1 TB), $0.11/GB (1-10 TB)
│   └── Dal 2025 AWS offre 100 GB/mese gratuiti (era 1 GB)
│
├── Cross-region (stessa cloud)
│   ├── AWS: $0.01-0.02/GB per direzione
│   ├── Azure: $0.02/GB
│   └── GCP: $0.01/GB (stesso continente)
│
├── Cross-AZ (stessa regione)
│   ├── AWS: $0.01/GB per direzione ($0.02 round-trip)
│   ├── Azure: gratuito nella maggior parte dei casi
│   └── GCP: gratuito
│
└── Inter-cloud (cloud → cloud)
    └── $0.08-0.12/GB (somma egress + ingress del destinatario)
```

### Strategie di riduzione costi di rete

#### 1. VPC Endpoint per traffico verso servizi cloud

```bash
# VPC Gateway Endpoint per S3 (GRATUITO — elimina traffico NAT Gateway)
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-abc123 \
  --service-name com.amazonaws.eu-west-1.s3 \
  --route-table-ids rtb-def456

# VPC Gateway Endpoint per DynamoDB (GRATUITO)
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-abc123 \
  --service-name com.amazonaws.eu-west-1.dynamodb \
  --route-table-ids rtb-def456

# Interface Endpoint per ECR (evita NAT per docker pull)
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-abc123 \
  --service-name com.amazonaws.eu-west-1.ecr.dkr \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-111 subnet-222 \
  --security-group-ids sg-333
```

**Impatto tipico:** un NAT Gateway che gestisce traffico S3 puo' costare $500-2000/mese. Un VPC Gateway Endpoint e' gratuito e riduce quel costo a zero.

#### 2. CDN per content delivery

```
CloudFront / Azure CDN / Cloud CDN:
├── Cache contenuti statici ai PoP globali
├── Riduce egress dall'origin (richieste servite dal cache)
├── Costo CDN < costo egress diretto per contenuti con alto hit rate
├── CloudFront egress: $0.085/GB (vs $0.09/GB diretto da S3)
└── Con Origin Shield: ulteriore riduzione di request all'origin

Risparmio tipico: 30-50% su costi di egress per asset statici
```

#### 3. Compressione dati in transito

```
Tecniche di compressione e impatto:
├── gzip: riduzione 60-80% per testo/JSON (standard, supporto universale)
├── Brotli: riduzione 70-85% per testo (migliore ratio, piu' CPU)
├── zstd: riduzione 65-80% (ottimo per log e dati strutturati)
└── Snappy: riduzione 50-60% (basso overhead CPU, ideale per streaming)

Impatto su costi: 10 TB/mese di log JSON
├── Non compresso: 10 TB × $0.09 = $900/mese
├── gzip (70% riduzione): 3 TB × $0.09 = $270/mese
└── Risparmio: $630/mese (70%)
```

#### 4. Connettivita' privata

| Soluzione | Provider | Costo | Quando usare |
|---|---|---|---|
| **Direct Connect** | AWS | $0.02/GB + porta ($0.30-1.63/ora) | Egress > 5 TB/mese, latenza critica |
| **ExpressRoute** | Azure | $0.025/GB + circuito ($55-436/mese) | Hybrid cloud, compliance |
| **Cloud Interconnect** | GCP | $0.02/GB + porta | Workload hybrid, egress elevato |
| **PrivateLink** | AWS/Azure | $0.01/GB + endpoint ($0.01/ora) | Comunicazione tra servizi/account |

**Regola pratica:** Direct Connect diventa economico rispetto a NAT Gateway/internet quando l'egress supera 5-10 TB/mese.

#### 5. Architettura network-aware

```
Pattern per ridurre data transfer:
├── Co-locazione servizi nella stessa AZ
│   └── Riduce cross-AZ transfer ($0.02/GB round-trip su AWS)
│
├── Replica locale dei dati consumati
│   └── Cache Redis/Memcached per dati da servizi remoti
│
├── Event-driven vs polling
│   └── SNS/SQS/EventBridge invece di polling API cross-service
│
├── Data aggregation at source
│   └── Aggregare metriche prima di trasferire (riduce volume 10-100x)
│
└── Zero-egress storage alternatives
    ├── Cloudflare R2: $0 egress, S3-compatible
    ├── Backblaze B2: $0 egress con CDN partner
    └── Utili per distribuzione contenuti ad alto volume
```

#### Audit del traffico di rete

```bash
#!/usr/bin/env bash
# Analisi costi di data transfer AWS (ultimo mese)
set -euo pipefail

START=$(date -u -d '30 days ago' +%Y-%m-%d)
END=$(date -u +%Y-%m-%d)

echo "=== Analisi Data Transfer ${START} → ${END} ==="

# Costo per tipo di data transfer
aws ce get-cost-and-usage \
  --time-period Start="${START}",End="${END}" \
  --granularity MONTHLY \
  --metrics UnblendedCost UsageQuantity \
  --filter '{
    "Dimensions": {
      "Key": "USAGE_TYPE_GROUP",
      "Values": [
        "EC2: Data Transfer - Internet (Out)",
        "EC2: Data Transfer - Inter AZ",
        "EC2: Data Transfer - Region to Region",
        "S3: Data Transfer - Internet (Out)"
      ]
    }
  }' \
  --group-by Type=DIMENSION,Key=USAGE_TYPE_GROUP \
  --output json | jq '.ResultsByTime[0].Groups[] |
    {type: .Keys[0], cost: .Metrics.UnblendedCost.Amount, usage_gb: .Metrics.UsageQuantity.Amount}'
```

---

## Confronto tooling FinOps

### Panoramica dell'ecosistema

L'ecosistema di tool FinOps si e' consolidato tra il 2024 e il 2026 con diverse categorie: tool nativi del cloud provider, piattaforme enterprise, soluzioni specializzate e strumenti open source. Non esiste un singolo tool che copra tutto — la scelta dipende da dimensione, complessita' e maturita' FinOps dell'organizzazione.

### Matrice comparativa

| Tool | Tipo | Scope | Cloud supportati | Prezzo indicativo | Forza principale |
|---|---|---|---|---|---|
| **AWS Cost Explorer** | Nativo | Visibility, budgeting | AWS | Gratuito | Integrato, nessun setup |
| **Azure Cost Management** | Nativo | Visibility, budgeting | Azure (+AWS base) | Gratuito | Integrato con Azure |
| **GCP Billing** | Nativo | Visibility, export | GCP | Gratuito | Export a BigQuery |
| **Infracost** | Shift-left | Stima costi in IaC | AWS, Azure, GCP | Free tier + $50-180/dev/mese | Pre-deploy cost estimation |
| **Vantage** | Multi-cloud | Visibility, reporting | AWS, Azure, GCP, K8s | Da $500/mese | UX moderna, onboarding rapido |
| **CloudHealth** | Enterprise | Governance, reporting | AWS, Azure, GCP | Da $2000/mese (Broadcom/VMware) | Governance enterprise mature |
| **Spot.io** | Automazione | Optimization, Spot mgmt | AWS, Azure, GCP | % del risparmio | Automazione Spot instance |
| **Kubecost** | Kubernetes | K8s cost allocation | Multi-cloud K8s | Free (single cluster), Enterprise $$ | Visibilita' K8s profonda |
| **OpenCost** | Kubernetes | K8s cost monitoring | Multi-cloud K8s | Gratuito (CNCF) | Open source, no vendor lock-in |
| **CAST AI** | Automazione | K8s optimization | AWS, Azure, GCP | % del risparmio | Right-sizing automatico K8s |
| **Finout** | Multi-cloud | Visibility, MegaBill | AWS, Azure, GCP, K8s | Custom | Unified billing multi-cloud |
| **Apptio Cloudability** | Enterprise | Governance, TBM | AWS, Azure, GCP | Enterprise pricing | IT financial management |

### Scelta del tooling per dimensione

```
Per spending cloud:

$0 - $10K/mese (startup, small team):
├── Tool nativi del provider (Cost Explorer, Azure Cost Mgmt)
├── Infracost (free tier) per Terraform
├── OpenCost per Kubernetes
└── Costo tooling: $0

$10K - $100K/mese (scale-up):
├── Tool nativi + Vantage o equivalente
├── Infracost per CI/CD
├── Kubecost free per Kubernetes
└── Costo tooling: $500-2000/mese (ROI: 10-20x)

$100K - $1M/mese (mid-market):
├── Vantage o CloudHealth per governance
├── Kubecost Enterprise per K8s
├── Spot.io per automazione Spot
├── Infracost Team per shift-left
└── Costo tooling: $2000-10000/mese (ROI: 5-15x)

$1M+/mese (enterprise):
├── CloudHealth o Apptio per governance
├── Kubecost Enterprise multi-cluster
├── Spot.io per automazione avanzata
├── Infracost + policy engine
├── Tool custom per reporting C-level
└── Costo tooling: $10000-50000/mese (ROI: 3-10x)
```

### Infracost — shift-left dei costi nel CI/CD

Infracost e' uno strumento developer-first che calcola l'impatto economico delle modifiche infrastrutturali prima che raggiungano la produzione. Si integra nelle pull request di GitHub/GitLab per mostrare il delta di costo.

```yaml
# .github/workflows/infracost.yml
name: Infracost
on:
  pull_request:
    paths:
      - 'terraform/**'

jobs:
  infracost:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - name: Setup Infracost
        uses: infracost/actions/setup@v3
        with:
          api-key: ${{ secrets.INFRACOST_API_KEY }}

      - name: Generate cost diff
        run: |
          infracost diff \
            --path=terraform/ \
            --format=json \
            --out-file=/tmp/infracost.json

      - name: Post PR comment
        uses: infracost/actions/comment@v3
        with:
          path: /tmp/infracost.json
          behavior: update
```

### Integrazione tooling raccomandata

```
Stack FinOps raccomandato (organizzazione media):

Pre-deploy (shift-left):
└── Infracost → stima costi in PR, policy enforcement

Visibility (runtime):
├── Tool nativo provider → dati di base, billing
├── Vantage/CloudHealth → multi-cloud, dashboard avanzate
└── Kubecost/OpenCost → costi Kubernetes

Optimization (azione):
├── Spot.io / CAST AI → automazione Spot e right-sizing
├── Tool nativo → RI/SP recommendations
└── Script custom → scheduling, cleanup

Governance (policy):
├── SCP / Azure Policy / Org Policy → guardrail
├── Tag enforcement → tool nativo + Terraform
└── Budget alert → tool nativo + Slack/PagerDuty
```

---

## KPI e metriche FinOps

### Framework di metriche

Le metriche FinOps si articolano su tre livelli: **efficienza** (quanto bene usiamo le risorse), **copertura** (quanto del nostro spend e' gestito), e **valore** (quanto valore di business generiamo per dollaro speso). Ogni organizzazione dovrebbe tracciare metriche da ciascun livello.

### Metriche di efficienza

| KPI | Formula | Target | Frequenza |
|---|---|---|---|
| **Effective Savings Rate** | (On-demand equivalent - Actual cost) / On-demand equivalent | 25-40% | Mensile |
| **Waste Ratio** | Costo risorse idle o inutilizzate / Costo totale | < 10% | Settimanale |
| **RI/SP Utilization** | Ore RI/SP utilizzate / Ore RI/SP acquistate | > 85% | Settimanale |
| **RI/SP Coverage** | Ore coperte da RI/SP / Ore on-demand eligibili | 60-80% | Mensile |
| **Right-sizing Adoption** | Raccomandazioni implementate / Raccomandazioni totali | > 50% | Mensile |
| **Spot Adoption Rate** | Spesa Spot / Spesa compute totale | 20-40% (non-prod) | Mensile |

### Metriche di copertura

| KPI | Formula | Target | Frequenza |
|---|---|---|---|
| **Tag Compliance** | Risorse con tag completi / Risorse totali | > 95% | Giornaliera |
| **Cost Allocation Rate** | Costo allocato a team / Costo totale | > 90% | Settimanale |
| **Budget Coverage** | Team con budget definito / Team totali | 100% | Trimestrale |
| **Anomaly Detection Coverage** | Servizi monitorati per anomalie / Servizi totali | > 90% | Mensile |
| **Automation Coverage** | Azioni automatizzate / Azioni ripetitive totali | > 70% | Trimestrale |

### Metriche di valore (Unit Economics)

| KPI | Formula | Target | Frequenza |
|---|---|---|---|
| **Cost per Active User** | Costo infra / MAU | Decrescente nel tempo | Mensile |
| **Cost per Transaction** | Costo infra / Transazioni | Sotto margine target | Mensile |
| **Infra/Revenue Ratio** | Costo infra / Revenue | 10-25% (SaaS) | Mensile |
| **Marginal Cost** | Delta costo / Delta utenti | Decrescente (economie di scala) | Trimestrale |
| **Cost Avoidance** | Costi evitati grazie a FinOps | Crescente | Mensile |

### Calcolo dell'Effective Savings Rate

```python
#!/usr/bin/env python3
"""Calcolo dell'Effective Savings Rate (ESR) — metrica chiave FinOps."""

from dataclasses import dataclass

@dataclass(frozen=True)
class SavingsBreakdown:
    on_demand_equivalent: float  # Costo se tutto fosse on-demand
    ri_savings: float            # Risparmio da Reserved Instances
    sp_savings: float            # Risparmio da Savings Plans
    spot_savings: float          # Risparmio da Spot instances
    negotiated_savings: float    # Risparmio da EDP/MACC/CUD
    rightsizing_savings: float   # Risparmio da right-sizing
    waste_eliminated: float      # Risorse idle eliminate

    @property
    def total_savings(self) -> float:
        return (
            self.ri_savings
            + self.sp_savings
            + self.spot_savings
            + self.negotiated_savings
            + self.rightsizing_savings
            + self.waste_eliminated
        )

    @property
    def actual_cost(self) -> float:
        return self.on_demand_equivalent - self.total_savings

    @property
    def effective_savings_rate(self) -> float:
        if self.on_demand_equivalent == 0:
            return 0.0
        return (self.total_savings / self.on_demand_equivalent) * 100

    def report(self) -> str:
        lines = [
            "=== Effective Savings Rate Report ===",
            f"On-demand equivalent:  ${self.on_demand_equivalent:>12,.0f}",
            f"RI savings:            ${self.ri_savings:>12,.0f}",
            f"SP savings:            ${self.sp_savings:>12,.0f}",
            f"Spot savings:          ${self.spot_savings:>12,.0f}",
            f"Negotiated (EDP/MACC): ${self.negotiated_savings:>12,.0f}",
            f"Right-sizing:          ${self.rightsizing_savings:>12,.0f}",
            f"Waste eliminated:      ${self.waste_eliminated:>12,.0f}",
            f"{'─' * 48}",
            f"Total savings:         ${self.total_savings:>12,.0f}",
            f"Actual cost:           ${self.actual_cost:>12,.0f}",
            f"Effective Savings Rate: {self.effective_savings_rate:>11.1f}%",
        ]
        return "\n".join(lines)


# Esempio: organizzazione con $500K/mese di spend
breakdown = SavingsBreakdown(
    on_demand_equivalent=500_000,
    ri_savings=75_000,
    sp_savings=45_000,
    spot_savings=30_000,
    negotiated_savings=25_000,
    rightsizing_savings=15_000,
    waste_eliminated=10_000,
)
print(breakdown.report())
```

### Dashboard FinOps KPI

```
Layout dashboard KPI raccomandato:

Row 1 — Executive summary
├── Spesa totale (attuale vs budget vs forecast)
├── Effective Savings Rate (gauge con target)
├── Infra/Revenue Ratio (trend 12 mesi)
└── Cost Avoidance cumulativo YTD

Row 2 — Efficienza operativa
├── RI/SP Utilization (gauge)
├── RI/SP Coverage (gauge)
├── Waste Ratio (gauge con semaforo)
└── Tag Compliance (percentuale)

Row 3 — Trend e dettaglio
├── Costo giornaliero per servizio (stacked area)
├── Costo per team (bar chart orizzontale)
├── Top 10 servizi per costo (ranked list)
└── Anomalie recenti (timeline)

Row 4 — Unit economics
├── Cost per user (trend mensile)
├── Cost per transaction (trend)
├── Marginal cost (trend trimestrale)
└── Top raccomandazioni di risparmio (action list)
```

### Maturity scoring

| Livello | Punteggio | Criteri |
|---|---|---|
| **Crawl** | 0-25 | Visibilita' base, tagging < 50%, no budget formali |
| **Walk** | 26-50 | Tagging > 80%, showback attivo, RI/SP coverage > 40% |
| **Run** | 51-75 | Chargeback attivo, automazione, ESR > 25%, unit economics tracciati |
| **Sprint** | 76-100 | FinOps integrato in SDLC, ESR > 35%, cultura cost-aware pervasiva |

---

## Anomaly detection avanzata — ML e automazione

### Limitazioni degli approcci tradizionali

L'anomaly detection basata su soglie statiche e Z-score (trattata nella sezione precedente) funziona per pattern semplici, ma presenta limitazioni significative in ambienti cloud complessi con stagionalita', multi-tenancy e carichi variabili.

```
Limitazioni degli approcci tradizionali:
├── Soglie statiche
│   ├── Non si adattano a crescita organica
│   ├── False positive durante picchi pianificati (Black Friday, lancio prodotto)
│   └── Ritardo nella detection per anomalie lente (slow burn)
│
├── Z-score
│   ├── Assume distribuzione normale (spesso non vera per costi cloud)
│   ├── Sensibile a outlier nel training set
│   └── Non cattura pattern stagionali (giorno/notte, weekend)
│
└── Deviazione percentuale
    ├── Non funziona per servizi con costo variabile (Spot, serverless)
    └── Falsi positivi per servizi con basso baseline
```

### Tecniche avanzate di anomaly detection

#### Isolation Forest

```python
#!/usr/bin/env python3
"""Anomaly detection su costi cloud con Isolation Forest."""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta, timezone

def detect_cost_anomalies_ml(
    daily_costs: list[dict],
    contamination: float = 0.05
) -> list[dict]:
    """
    Rileva anomalie nei costi giornalieri usando Isolation Forest.

    Args:
        daily_costs: lista di dict con chiavi 'date', 'cost', 'service'.
        contamination: percentuale attesa di anomalie (0.01-0.10).

    Returns:
        lista di dict con anomalie rilevate.
    """
    # Feature engineering
    features = []
    for entry in daily_costs:
        dt = datetime.strptime(entry['date'], '%Y-%m-%d')
        features.append([
            entry['cost'],
            dt.weekday(),           # 0-6 (giorno della settimana)
            dt.day,                 # 1-31 (giorno del mese)
            1 if dt.weekday() >= 5 else 0,  # weekend flag
        ])

    X = np.array(features)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=200
    )
    predictions = model.fit_predict(X_scaled)
    scores = model.decision_function(X_scaled)

    anomalies = []
    for i, (pred, score) in enumerate(zip(predictions, scores)):
        if pred == -1:  # anomalia
            anomalies.append({
                'date': daily_costs[i]['date'],
                'cost': daily_costs[i]['cost'],
                'service': daily_costs[i].get('service', 'all'),
                'anomaly_score': float(score),
                'severity': 'HIGH' if score < -0.3 else 'MEDIUM'
            })

    return sorted(anomalies, key=lambda x: x['anomaly_score'])
```

#### Prophet per forecasting e anomaly detection

```python
#!/usr/bin/env python3
"""Anomaly detection con Prophet — rileva deviazioni dal forecast."""

from prophet import Prophet
import pandas as pd

def detect_with_prophet(
    daily_costs: list[dict],
    sensitivity: float = 0.95
) -> list[dict]:
    """
    Usa Prophet per forecast e identifica costi fuori intervallo di confidenza.
    """
    df = pd.DataFrame(daily_costs)
    df.columns = ['ds', 'y']  # Prophet richiede 'ds' e 'y'
    df['ds'] = pd.to_datetime(df['ds'])

    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        interval_width=sensitivity,
        changepoint_prior_scale=0.05
    )
    model.fit(df)

    forecast = model.predict(df)

    anomalies = []
    for i, row in forecast.iterrows():
        actual = df.iloc[i]['y']
        if actual > row['yhat_upper']:
            anomalies.append({
                'date': str(row['ds'].date()),
                'actual': actual,
                'expected': row['yhat'],
                'upper_bound': row['yhat_upper'],
                'deviation_pct': ((actual - row['yhat']) / row['yhat']) * 100,
                'direction': 'ABOVE'
            })
        elif actual < row['yhat_lower']:
            anomalies.append({
                'date': str(row['ds'].date()),
                'actual': actual,
                'expected': row['yhat'],
                'lower_bound': row['yhat_lower'],
                'deviation_pct': ((actual - row['yhat']) / row['yhat']) * 100,
                'direction': 'BELOW'
            })

    return anomalies
```

### Metriche di qualita' dell'anomaly detection

| Metrica | Formula | Target |
|---|---|---|
| **Precision** | True Positive / (True Positive + False Positive) | > 70% |
| **Recall** | True Positive / (True Positive + False Negative) | > 90% |
| **False Positive Rate** | False Positive / Total alerts | < 30% |
| **Mean Time to Detect (MTTD)** | Tempo medio tra inizio anomalia e alert | < 4 ore |
| **Mean Time to Resolve (MTTR)** | Tempo medio tra alert e risoluzione | < 24 ore |
| **Alert Fatigue Score** | Alert ignorati / Alert totali | < 20% |

### Autoencoder per anomaly detection su serie temporali

Gli autoencoder neurali sono particolarmente efficaci per rilevare anomalie in serie temporali di costo perche' apprendono una rappresentazione compressa del comportamento "normale". Quando il costo di ricostruzione supera una soglia, il dato e' classificato come anomalo.

```python
#!/usr/bin/env python3
"""Autoencoder per anomaly detection su costi cloud — concettuale."""

import numpy as np

def build_autoencoder_concept(sequence_length: int = 30):
    """
    Struttura concettuale di un autoencoder per anomaly detection.

    Input: finestra di 30 giorni di costi normalizzati
    Encoder: comprime in rappresentazione latente
    Decoder: ricostruisce la serie originale
    Anomalia: errore di ricostruzione > soglia
    """
    # Architettura tipica (pseudocodice con layer shape):
    architecture = {
        'input': (sequence_length, 1),      # 30 giorni × 1 feature
        'encoder_1': (sequence_length, 64),  # LSTM 64 unita'
        'encoder_2': (sequence_length, 32),  # LSTM 32 unita'
        'latent': (16,),                     # Rappresentazione compressa
        'decoder_1': (sequence_length, 32),  # LSTM 32 unita'
        'decoder_2': (sequence_length, 64),  # LSTM 64 unita'
        'output': (sequence_length, 1),      # Ricostruzione
    }

    # Soglia di anomalia: percentile 95-99 dell'errore su dati normali
    # reconstruction_error = MSE(input, output)
    # anomaly = reconstruction_error > threshold

    return architecture
```

I vantaggi dell'approccio autoencoder rispetto a Z-score e Isolation Forest includono la capacita' di catturare pattern temporali complessi (stagionalita' settimanale, mensile), la robustezza ai trend di crescita (il modello apprende il "normale" in modo adattivo), e la possibilita' di operare su multiple features contemporaneamente (costo, request count, data transfer).

### Anomaly detection autonoma con guardrail

```
Livelli di automazione per anomaly response:

Livello 1 — Alert (baseline)
├── Notifica via Slack/email/PagerDuty
├── Include: servizio, costo, deviazione, trend
└── Azione: investigazione manuale

Livello 2 — Alert + enrichment
├── Alert con root cause analysis automatica
├── Include: risorse coinvolte, change recenti, correlation
└── Azione: investigazione guidata con contesto

Livello 3 — Alert + raccomandazione
├── Suggerisce azione correttiva specifica
├── Include: impatto stimato, rischio, rollback plan
└── Azione: approvazione one-click da parte dell'operatore

Livello 4 — Auto-remediation con guardrail
├── Esegue azione correttiva automaticamente
├── Guardrail: solo per azioni reversibili (scaling down, scheduling)
├── Guardrail: mai in produzione senza approvazione per azioni distruttive
├── Guardrail: budget di auto-remediation (max $ impattabile)
└── Logging completo di ogni azione automatica per audit
```

---

## Gestione costi multi-cloud avanzata

### Sfide specifiche del multi-cloud

La gestione dei costi in ambiente multi-cloud introduce complessita' che vanno oltre la somma delle singole cloud. Il 75% delle aziende Forbes Global 2000 opera in multi-cloud, ma la frammentazione dei dati di billing e le differenze nei modelli di pricing rendono la governance finanziaria significativamente piu' difficile.

```
Sfide multi-cloud specifiche:
├── Nomenclatura diversa per servizi equivalenti
│   ├── AWS EC2 vs Azure VM vs GCP Compute Engine
│   ├── AWS S3 vs Azure Blob vs GCP Cloud Storage
│   └── Metriche di billing diverse (vCPU-ore vs minuti vs secondi)
│
├── Billing structure diversa
│   ├── AWS: per-second (minimo 60s), on-demand default
│   ├── Azure: per-minute, differenziazione Windows/Linux
│   └── GCP: per-second (minimo 60s), sustained use discount automatico
│
├── Sconti non comparabili
│   ├── AWS: RI + SP + EDP
│   ├── Azure: Reservations + MACC + EA
│   └── GCP: CUD + Sustained Use Discount (automatico)
│
├── Tagging inconsistente
│   ├── AWS: Tags (key:value su quasi tutto)
│   ├── Azure: Tags (key:value, case-insensitive)
│   └── GCP: Labels (key:value, solo lowercase)
│
└── Data transfer inter-cloud
    └── Costo significativo ($0.08-0.12/GB) che puo' annullare risparmi
```

### Normalizzazione dei dati di billing

```python
#!/usr/bin/env python3
"""Normalizzazione billing multi-cloud per confronto unificato."""

from dataclasses import dataclass
from enum import Enum

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"

class ServiceCategory(Enum):
    COMPUTE = "compute"
    STORAGE = "storage"
    DATABASE = "database"
    NETWORK = "network"
    SERVERLESS = "serverless"
    CONTAINERS = "containers"
    OTHER = "other"

# Mapping servizi → categoria normalizzata
SERVICE_MAP: dict[str, ServiceCategory] = {
    # AWS
    "Amazon Elastic Compute Cloud": ServiceCategory.COMPUTE,
    "Amazon Simple Storage Service": ServiceCategory.STORAGE,
    "Amazon Relational Database Service": ServiceCategory.DATABASE,
    "AWS Lambda": ServiceCategory.SERVERLESS,
    "Amazon Elastic Container Service": ServiceCategory.CONTAINERS,
    # Azure
    "Virtual Machines": ServiceCategory.COMPUTE,
    "Storage Accounts": ServiceCategory.STORAGE,
    "Azure SQL Database": ServiceCategory.DATABASE,
    "Azure Functions": ServiceCategory.SERVERLESS,
    "Azure Kubernetes Service": ServiceCategory.CONTAINERS,
    # GCP
    "Compute Engine": ServiceCategory.COMPUTE,
    "Cloud Storage": ServiceCategory.STORAGE,
    "Cloud SQL": ServiceCategory.DATABASE,
    "Cloud Functions": ServiceCategory.SERVERLESS,
    "Google Kubernetes Engine": ServiceCategory.CONTAINERS,
}

@dataclass(frozen=True)
class NormalizedCostEntry:
    provider: CloudProvider
    category: ServiceCategory
    original_service: str
    team: str
    environment: str
    cost_usd: float
    date: str

    def to_dict(self) -> dict:
        return {
            'provider': self.provider.value,
            'category': self.category.value,
            'service': self.original_service,
            'team': self.team,
            'environment': self.environment,
            'cost': self.cost_usd,
            'date': self.date,
        }
```

### Tagging unificato multi-cloud

```
Schema di tagging unificato:

Tag obbligatori (identici su tutti i provider):
├── team: <nome-team>          (owner del costo)
├── environment: <env>          (production|staging|development|sandbox)
├── project: <nome-progetto>    (progetto/prodotto)
├── cost-center: <cc-code>      (centro di costo contabile)
└── cloud-provider: <provider>  (aws|azure|gcp — utile in reporting)

Regole di normalizzazione:
├── Tutto in lowercase (GCP richiede lowercase per labels)
├── Separatore: trattino (kebab-case), non underscore
├── Valori enumerati predefiniti (no free-text per team/env)
└── Validazione pre-deploy via CI/CD (Infracost, OPA)

Enforcement per provider:
├── AWS: SCP + Tag Policy + Config Rules
├── Azure: Azure Policy (deny/audit) + Management Groups
└── GCP: Organization Policy + Label enforcement
```

### Single-pane-of-glass per multi-cloud

La visibilita' unificata richiede un layer di aggregazione che normalizzi i dati di billing e li presenti in una vista coerente. Le opzioni principali:

```
Approcci per unified visibility:

1. Tool nativo + aggregazione custom
   ├── AWS CUR export a S3 + Athena
   ├── Azure Cost Management export a Storage Account
   ├── GCP Billing export a BigQuery
   └── ETL + data warehouse (Snowflake, BigQuery) + BI tool (Grafana, Looker)
   Vantaggi: flessibilita' totale, nessun costo tool aggiuntivo
   Svantaggi: effort di sviluppo e manutenzione significativo

2. Piattaforma FinOps multi-cloud
   ├── Vantage, CloudHealth, Apptio, Finout
   ├── Connettori nativi per AWS/Azure/GCP + K8s
   └── Dashboard pre-costruite, anomaly detection, reporting
   Vantaggi: time-to-value rapido, manutenzione minima
   Svantaggi: costo della piattaforma, potenziale vendor lock-in

3. Approccio ibrido
   ├── Tool nativo per dettaglio per-provider
   ├── Piattaforma FinOps per vista aggregata e governance
   └── Script custom per automazione specifica
   Vantaggi: bilanciamento tra flessibilita' e time-to-value
```

### Arbitraggio multi-cloud: miti e realta'

```
L'idea di spostare workload tra cloud per il prezzo migliore e' spesso
controproducente. Analisi dei costi reali:

Costi visibili del multi-cloud:
├── Egress inter-cloud: $0.08-0.12/GB
├── Tooling duplicato (monitoring, logging, security)
├── Training team su piattaforme multiple
└── Complessita' IaC e deployment pipeline

Costi nascosti:
├── Cognitive load degli engineer (context switching)
├── Incident response su piattaforme diverse
├── Compliance audit su ambienti multipli
├── Tempo di negoziazione con vendor multipli
└── Perdita di sconti volume per frammentazione della spesa

Quando il multi-cloud ha senso economicamente:
├── Best-of-breed per servizi specifici (es. GCP per ML, AWS per serverless)
├── Compliance/data residency che richiede provider diversi per regione
├── Disaster recovery cross-cloud (raro, costoso)
└── Acquisizioni/fusioni con stack tecnologici diversi
```

### Strategia di commitment multi-cloud

```
Approccio raccomandato per commitment multi-cloud:

1. Analisi per provider
   ├── Baseline steady-state per provider (ultimi 6 mesi)
   ├── Growth projection per provider (12 mesi)
   └── Workload mobility (quanto e' facile spostare tra cloud?)

2. Commitment strategy per provider
   ├── Cloud primario (70%+ dello spend):
   │   ├── Aggressive commitment (70-80% del baseline)
   │   ├── Mix RI + SP + EDP/MACC/CUD
   │   └── Termine 1-3 anni basato su confidenza
   │
   ├── Cloud secondario (20-25% dello spend):
   │   ├── Moderate commitment (50-60% del baseline)
   │   ├── Preferire SP/CUD flessibili su RI rigide
   │   └── Termine 1 anno (riduce rischio di riallocazione)
   │
   └── Cloud terziario (5-10% dello spend):
       ├── Minimal commitment (30-40% del baseline)
       ├── Solo on-demand o Spot
       └── Valutare se consolidare su un altro provider

3. Review trimestrale
   └── Ribilanciamento basato su trend di spesa effettivo
```

---

## Sostenibilita' e Green Cloud

### FinOps incontra GreenOps

La sostenibilita' cloud e' diventata una dimensione formale del framework FinOps. La FinOps Foundation ha introdotto la capability "Cloud Sustainability" per riconoscere che ottimizzazione dei costi e riduzione dell'impatto ambientale sono obiettivi allineati: meno risorse sprecate = meno energia consumata = meno emissioni di CO2.

Secondo il State of FinOps Report 2025, il 36% delle organizzazioni a livello globale e il 53% in Europa riportano gia' le emissioni di carbonio associate al cloud. Il 57% prevede di avere iniziative di sostenibilita' definite entro il prossimo anno.

### Scope delle emissioni cloud

```
Emissioni cloud secondo il GHG Protocol:

Scope 1 — Emissioni dirette
└── Non applicabile per utenti cloud (rilevante per il provider)

Scope 2 — Energia acquistata
├── Datacenter on-premise: emissioni dall'elettricita' consumata
└── Cloud: il provider riporta per te (incluso nel Scope 3)

Scope 3 — Emissioni indirette (catena del valore)
├── Rappresentano > 80% delle emissioni totali per utenti cloud
├── Include: produzione hardware, energia datacenter, raffreddamento
├── I cloud provider riportano le emissioni per account/progetto
└── Ridurre Scope 3 = ottimizzare utilizzo risorse = FinOps
```

### Strumenti di carbon reporting per provider

| Provider | Tool | Dati forniti | Accesso |
|---|---|---|---|
| **AWS** | Customer Carbon Footprint Tool | Emissioni per servizio, regione | Console AWS |
| **Azure** | Emissions Impact Dashboard | Scope 1/2/3, per subscription | Azure Portal + Power BI |
| **GCP** | Carbon Footprint | Emissioni per progetto, servizio | Console GCP + BigQuery export |

### Strategie di riduzione dell'impatto ambientale

```
Azioni FinOps con impatto ambientale diretto:

1. Right-sizing e eliminazione waste
   ├── Meno compute inutilizzato = meno energia
   └── Impatto: ogni vCPU idle consuma ~10W continui

2. Scheduling ambienti non-prod
   ├── Spegnere dev/staging fuori orario = 65% meno energia
   └── Impatto diretto su emissioni Scope 3

3. Scelta della regione
   ├── Regioni con energia rinnovabile producono meno CO2
   ├── AWS: Irlanda, Oregon, Canada (alto % rinnovabile)
   ├── Azure: Svezia, Norvegia (quasi 100% rinnovabile)
   ├── GCP: Finlandia, Iowa, Oregon (bassa carbon intensity)
   └── Attenzione: latenza e compliance possono limitare la scelta

4. Architettura efficiente
   ├── Serverless > VM always-on per workload intermittente
   ├── ARM/Graviton: 60% piu' efficiente energeticamente per watt
   ├── Spot instances: riutilizzano capacita' excess (gia' alimentata)
   └── Container density: piu' workload per nodo = meno nodi

5. Storage optimization
   ├── Tiering: dati in cold storage consumano meno energia
   ├── Compressione: meno spazio = meno disco = meno energia
   └── Lifecycle: eliminare dati obsoleti

6. Carbon-aware scheduling
   ├── Eseguire batch job quando la grid elettrica e' piu' green
   ├── API disponibili: WattTime, electricityMap
   └── Shift temporale di 2-6 ore puo' ridurre CO2 del 30-50%
```

### Metriche di sostenibilita'

| Metrica | Descrizione | Fonte |
|---|---|---|
| **Carbon per dollar** | kgCO2e / $ speso | Carbon footprint tool / billing |
| **Carbon per user** | kgCO2e / MAU | Carbon tool / analytics |
| **Carbon intensity trend** | Trend kgCO2e/$ nel tempo | Calcolato |
| **Renewable energy %** | % energia da fonti rinnovabili per regione | Report del provider |
| **PUE** | Power Usage Effectiveness del datacenter | Report del provider |
| **Waste carbon** | CO2 da risorse idle/sprecate | Waste ratio × carbon totale |

### Conformita' ESG e reporting

Le normative europee CSRD (Corporate Sustainability Reporting Directive) e la tassonomia UE richiedono alle aziende sopra determinate soglie di rendicontare le emissioni Scope 3, che includono i consumi cloud. Le organizzazioni FinOps mature integrano il carbon tracking nei report standard:

```
Report di sostenibilita' cloud integrato:

Sezione 1 — Emissioni totali
├── Scope 3 totale (kgCO2e)
├── Breakdown per provider
├── Breakdown per regione
└── Trend YoY

Sezione 2 — Efficienza
├── Carbon per $ speso (trend)
├── Carbon per utente/transazione
├── % risorse in regioni rinnovabili
└── Waste carbon eliminato

Sezione 3 — Azioni
├── Regioni migrate verso fonti rinnovabili
├── Right-sizing completato
├── Scheduling implementato
└── Target prossimo trimestre

Sezione 4 — Conformita'
├── Allineamento CSRD/ESG
├── CDP disclosure
└── Certificazioni provider (ISO 14001, RE100)
```

---

## Cultura FinOps e change management

### Il problema culturale

Implementare FinOps e' per il 30% un problema tecnico e per il 70% un problema culturale. Le organizzazioni che falliscono nel FinOps tipicamente hanno strumenti eccellenti ma scarsa adozione da parte dei team. La resistenza al cambiamento e' il principale ostacolo.

```
Pattern di resistenza comuni:
├── "Non e' il mio lavoro" (engineering vs finance)
│   └── Soluzione: responsabilita' condivisa, budget ownership
│
├── "Rallenta lo sviluppo" (paura di burocrazia)
│   └── Soluzione: automazione, guardrail non bloccanti, self-service
│
├── "Non ho visibilita'" (dati inaccessibili)
│   └── Soluzione: dashboard self-service, report automatici
│
├── "Il cloud costa quello che costa" (fatalismo)
│   └── Soluzione: mostrare risparmi concreti, gamification
│
└── "Abbiamo provato, non funziona" (tentativi precedenti falliti)
    └── Soluzione: executive sponsorship, quick win visibili, approccio incrementale
```

### Modello di maturita' FinOps

```
┌─────────────────────────────────────────────────────────────┐
│                 FINOPS MATURITY MODEL                        │
│                                                             │
│  Livello 1: CRAWL                                           │
│  ├── Visibilita' base dei costi per account/subscription    │
│  ├── Tagging parziale (< 50%)                               │
│  ├── Reporting manuale (spreadsheet)                        │
│  ├── Nessun budget formale per team                         │
│  └── Ottimizzazione reattiva (dopo la fattura)              │
│                                                             │
│  Livello 2: WALK                                            │
│  ├── Tagging > 80% con enforcement parziale                │
│  ├── Showback attivo (report per team)                      │
│  ├── RI/SP coverage > 40%                                   │
│  ├── Budget per team con alert                              │
│  ├── Right-sizing raccomandazioni visibili                  │
│  └── Review mensili con leadership                          │
│                                                             │
│  Livello 3: RUN                                             │
│  ├── Chargeback attivo (costi fatturati internamente)       │
│  ├── Tag compliance > 95%                                   │
│  ├── RI/SP coverage 60-80%                                  │
│  ├── Automazione scheduling/cleanup                         │
│  ├── Unit economics tracciati                               │
│  ├── Anomaly detection automatica                           │
│  └── Review settimanali per team, mensili per leadership    │
│                                                             │
│  Livello 4: SPRINT                                          │
│  ├── FinOps integrato nel SDLC (shift-left con Infracost)  │
│  ├── ESR > 35%                                              │
│  ├── Automazione > 70% delle azioni ripetitive             │
│  ├── Cultura cost-aware pervasiva                           │
│  ├── Forecasting accurato (±5%)                             │
│  ├── Carbon tracking integrato                              │
│  └── Continuous improvement con scorecard trimestrale       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Programma di onboarding FinOps

| Settimana | Pubblico | Contenuto | Outcome |
|---|---|---|---|
| 1 | Leadership | Executive briefing: ROI del FinOps, benchmark di settore, investimento richiesto | Sponsorship e budget approvato |
| 2 | Engineering leads | Workshop: strumenti, dashboard, tagging, responsabilita' | Owner di costo per team nominati |
| 3 | Tutti i team | Training base: leggere dashboard, interpretare costi, quick win | Awareness diffusa |
| 4 | FinOps team | Deep-dive: commitment strategy, anomaly detection, automazione | Piano di ottimizzazione 90 giorni |
| 5-8 | Per team | Sessioni 1:1: analisi costi specifici, azioni personalizzate | Primi risparmi misurabili |
| 9-12 | Organizzazione | Review dei risultati, celebrazione risparmi, piano fase successiva | Momentum e cultura |

### Gamification e incentivi

La gamification e' uno strumento potente per promuovere la cultura FinOps senza creare antagonismo. L'obiettivo e' rendere l'ottimizzazione dei costi un'attivita' positiva e collaborativa.

```
Meccaniche di gamification FinOps:

Classifiche (pubbliche, aggiornate settimanalmente):
├── Efficienza: team con miglior rapporto performance/costo
├── Miglioramento: team con maggior riduzione percentuale MoM
├── Compliance: team con tag compliance piu' alta
└── Innovazione: team con migliore idea di ottimizzazione

Riconoscimenti:
├── "FinOps Champion del mese" — team con impatto piu' alto
├── "Waste Hunter" — individuo che identifica il risparmio piu' grande
├── "Tag Master" — team con compliance 100%
└── Celebrazione nei town hall / all-hands meeting

Incentivi tangibili:
├── Budget libero: % del risparmio generato reinvestito nel team
├── Innovation time: tempo per progetti personali finanziato dai risparmi
├── Team event: pranzo/cena per team che raggiunge target
└── Visibilita': presentazione dei risultati al CTO/CFO

Anti-pattern da evitare:
├── Punizioni per sforamento budget (genera paura, non cultura)
├── Classifiche anonime (riduce accountability)
├── Metriche solo su costo assoluto (penalizza team in crescita)
└── Competizione distruttiva tra team (deve essere collaborativa)
```

### Community of Practice (CoP)

```
Struttura di una FinOps Community of Practice:

Membership:
├── Core: FinOps team + engineering leads (sempre presenti)
├── Extended: rappresentante per team (rotazione trimestrale)
└── Guest: vendor, consulenti, speaker esterni (ad hoc)

Cadenza:
├── Riunione bisettimanale (30-45 minuti)
├── Demo session mensile (tool, automazione, case study)
├── Hackathon trimestrale (ottimizzazione collaborativa)
└── Annual review (risultati, strategia anno successivo)

Attivita':
├── Condivisione best practice tra team
├── Review delle nuove funzionalita' dei tool
├── Discussion su sfide specifiche
├── Sviluppo di automazione condivisa
├── Training peer-to-peer
└── Feedback su policy e governance

Canali:
├── Slack/Teams channel dedicato (#finops-community)
├── Wiki/Confluence con knowledge base
├── Repository Git con script e automazione condivisa
└── Dashboard condivisa con KPI di community
```

### Executive reporting

La comunicazione con il livello C-suite richiede un formato diverso rispetto al reporting operativo. I dirigenti necessitano di: (1) impatto finanziario in termini di business, (2) confronto con benchmark di settore, (3) trend e proiezioni, (4) decisioni necessarie.

```
Struttura report FinOps per C-level (mensile):

Pagina 1 — Executive Summary
├── Spesa cloud totale: $XXX (vs budget, vs forecast)
├── Effective Savings Rate: XX% (target: YY%)
├── Cost avoidance cumulativo YTD: $XXX
├── Infra/Revenue ratio: XX% (benchmark settore: YY%)
└── Status: ● on track / ● attenzione / ● fuori target

Pagina 2 — Trend e proiezioni
├── Grafico: spesa 12 mesi con forecast 3 mesi
├── Grafico: ESR trend 12 mesi
├── Tabella: top 5 servizi per costo e variazione
└── Proiezione fine anno vs budget

Pagina 3 — Azioni e decisioni
├── Top 3 ottimizzazioni completate (con $ risparmiato)
├── Top 3 ottimizzazioni in corso
├── Decisioni necessarie (rinnovo contratti, commitment, budget)
└── Rischi e mitigazioni

Pagina 4 — Appendice
├── Dettaglio per business unit
├── Dettaglio per cloud provider
└── Confronto con quarter precedente
```

---

## Esercizi

### Esercizio 1 — Cost dashboard (base)

**Obiettivo:** Costruire una dashboard di costo con AWS Cost Explorer + Grafana.

```bash
# 1. Abilitare Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start="$(date -u -d '30 days ago' +%Y-%m-%d)",End="$(date -u +%Y-%m-%d)" \
  --granularity DAILY \
  --metrics UnblendedCost \
  --group-by Type=TAG,Key=team \
  --output json > cost-data.json

# 2. Configurare Grafana con plugin CloudWatch
# Dashboard panels:
# - Costo totale giornaliero (line chart)
# - Costo per team (stacked bar)
# - Top 10 servizi per costo (pie chart)
# - Trend MoM (comparison panel)
```

### Esercizio 2 — RI sizing (intermedio)

**Obiettivo:** Calcolare il break-even per RI 1y vs 3y per workload steady-state.

1. Identificare 3-5 istanze EC2 con utilizzo costante > 70%.
2. Calcolare costo on-demand annuale.
3. Confrontare con RI No Upfront, Partial Upfront, All Upfront (1y e 3y).
4. Raccomandare la strategia ottimale.

### Esercizio 3 — Auto-shutdown non-prod (stretch)

**Obiettivo:** Lambda/Function App che spegne dev/stage fuori orario 9-19.

1. Creare Lambda con scheduling EventBridge.
2. Taggare istanze non-prod con `automation:schedule-off`.
3. Implementare logica start/stop.
4. Calcolare risparmio stimato.
5. Creare dashboard di monitoring dello scheduling.

### Esercizio 4 — Tag compliance audit

**Obiettivo:** Script che audita il tagging di tutte le risorse e genera report di compliance.

1. Definire tag obbligatori (team, environment, project, cost-center).
2. Scansionare tutte le risorse EC2, RDS, S3, Lambda.
3. Calcolare % di compliance per tag e per servizio.
4. Generare report con risorse non conformi.

---

## Troubleshooting — 20 problemi di costo

### Problema 1: Spike improvviso nella fattura

**Sintomo:** Costo giornaliero raddoppiato rispetto alla media.

**Diagnosi:**
```bash
# Confronto giorno anomalo vs media
aws ce get-cost-and-usage \
  --time-period Start="2026-05-20",End="2026-05-22" \
  --granularity DAILY \
  --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE \
  --output json | jq '.ResultsByTime[] | {date: .TimePeriod.Start, services: [.Groups[] | {service: .Keys[0], cost: .Metrics.UnblendedCost.Amount}] | sort_by(.cost | tonumber) | reverse | .[0:5]}'
```

**Cause comuni:** Auto-scaling senza max cap, data transfer spike, NAT Gateway con traffico anomalo, snapshot involontari.

### Problema 2: Costi di data transfer elevati

**Sintomo:** Data transfer rappresenta > 15% della fattura.

**Soluzione:** Verificare: (1) traffico cross-region evitabile, (2) NAT Gateway per traffico verso S3/DynamoDB (usare VPC endpoint), (3) CloudFront non configurato per asset statici, (4) data replication eccessiva.

### Problema 3: RI inutilizzate

**Sintomo:** RI utilization < 70%.

**Causa:** Workload migrato, ridimensionato o dismesso senza aggiornare le RI.

**Soluzione:** (1) Verificare se l'istanza riservata è ancora attiva, (2) modificare la RI a instance type diverso (se supportato), (3) vendere su RI Marketplace (AWS), (4) preventivo: review mensile RI utilization.

### Problema 4: Tag mancanti su risorse critiche

**Sintomo:** > 20% dei costi non allocabili a team.

**Soluzione:** (1) Abilitare tag enforcement via SCP/Policy, (2) script retroattivo per taggare risorse esistenti, (3) audit settimanale di compliance, (4) bloccare creazione risorse senza tag.

### Problema 5: Kubernetes cost over-allocation

**Sintomo:** I team richiedono più risorse di quelle usate (request >> usage).

**Soluzione:** Installare VPA in modalità recommend, mostrare ai team il gap request/usage, implementare LimitRange con default ragionevoli, kubecost per visibilità.

### Problema 6: Storage costs in crescita incontrollata

**Sintomo:** Costi S3/EBS/snapshot crescono ogni mese senza correlazione con il business.

**Soluzione:** (1) Lifecycle policy su S3 (Intelligent-Tiering), (2) cleanup snapshot > 90 giorni, (3) eliminare volumi EBS non attaccati, (4) compressione dati prima dello storage, (5) deduplicazione.

### Problema 7: Savings Plans sotto-utilizzati

**Sintomo:** Commitment non coperto dal workload effettivo.

**Causa:** Commitment troppo aggressivo, riduzione workload, migrazione a serverless.

**Soluzione:** Non c'è marketplace per SP. Lezione: (1) committare massimo 80% del baseline, (2) preferire Compute SP per flessibilità, (3) rivedere mensilmente.

### Problema 8: Costi NAT Gateway eccessivi

**Sintomo:** NAT Gateway costa > $1000/mese.

**Soluzione:**
```bash
# Analizzare traffico NAT Gateway con VPC Flow Logs
# Identificare destinazioni principali
# Se S3 → aggiungere Gateway VPC Endpoint (gratuito)
# Se DynamoDB → aggiungere Gateway VPC Endpoint
# Se ECR/CloudWatch → aggiungere Interface VPC Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-123 \
  --service-name com.amazonaws.eu-west-1.s3 \
  --route-table-ids rtb-456
```

### Problema 9: Dev environments costosi quanto produzione

**Sintomo:** Ambiente dev costa > 40% della produzione.

**Soluzione:** (1) Scheduling on/off (65-70% risparmio), (2) instance type più piccoli per dev, (3) Spot per dev, (4) single-AZ per dev (no HA), (5) shared database per dev.

### Problema 10: Costi di logging eccessivi (CloudWatch)

**Sintomo:** CloudWatch Logs > $2000/mese.

**Soluzione:** (1) Ridurre verbosità log (WARNING in prod, non DEBUG), (2) retention policy (7 giorni in CloudWatch, poi S3), (3) filter pattern per ridurre volume, (4) considerare alternative (Loki, Elasticsearch self-hosted).

### Problema 11: Lambda cold start + costo elevato

**Sintomo:** Lambda costa più di un EC2 equivalente per workload costante.

**Causa:** Lambda è cost-effective per workload intermittente. Per workload steady > 50% del tempo, EC2/Fargate è più economico.

**Soluzione:** Analizzare pattern di invocazione. Se > 5M invocazioni/mese con duration media > 1s, valutare Fargate.

### Problema 12: EBS GP2 più costosi del necessario

**Sintomo:** Volume GP2 con IOPS baseline inutilizzati.

**Soluzione:** Migrare a GP3: stesse prestazioni base (3000 IOPS, 125 MB/s), 20% più economico. IOPS e throughput configurabili indipendentemente.

### Problema 13: Elastic IP non utilizzati

**Sintomo:** Centinaia di EIP allocati ma non associati.

**Causa:** Istanze terminate senza rilascio dell'IP. Costo: $3.65/mese ciascuno.

**Soluzione:** Script periodico di cleanup EIP non associati.

### Problema 14: Multi-AZ non necessario per non-prod

**Sintomo:** RDS Multi-AZ in ambiente dev/staging.

**Soluzione:** Single-AZ per non-prod = 50% risparmio su RDS. Documentare che non-prod non ha SLA di disponibilità.

### Problema 15: Container image troppo grandi

**Sintomo:** Costi di storage ECR/GCR elevati, pull lenti.

**Soluzione:** (1) Multi-stage build, (2) base image minimale (distroless, alpine), (3) lifecycle policy per eliminare image non taggate > 30 giorni, (4) deduplica layer condivisi.

### Problema 16: Costi di supporto AWS eccessivi

**Sintomo:** Support plan Enterprise costa > $15.000/mese.

**Soluzione:** Valutare se Enterprise è necessario. Business Support (minore costo) è sufficiente per la maggior parte delle organizzazioni. Il costo è proporzionale allo spend.

### Problema 17: Bandwidth charges tra servizi

**Sintomo:** Data transfer tra servizi nella stessa regione genera costi.

**Causa:** Servizi in AZ diverse generano cross-AZ data transfer ($0.01/GB ciascuna direzione).

**Soluzione:** Co-locare servizi che comunicano frequentemente nella stessa AZ dove possibile, oppure accettare il costo come prezzo dell'HA.

### Problema 18: DynamoDB in provisioned mode con over-capacity

**Sintomo:** DynamoDB WCU/RCU provisionati ma utilizzati al 10%.

**Soluzione:** (1) Passare a on-demand mode per workload imprevedibili, (2) se prevedibile, auto-scaling con target utilization 70%.

### Problema 19: Budget non rispettato a metà mese

**Sintomo:** Budget mensile esaurito al 50% del mese.

**Soluzione:** (1) Investigare causa (nuovo progetto, anomalia, mancata ottimizzazione), (2) implementare budget alert al 50%, 80%, 100%, (3) auto-action (es. bloccare creazione risorse non-prod).

### Problema 20: Costi nascosti di data egress multi-cloud

**Sintomo:** Fattura di egress molto più alta del previsto in architettura multi-cloud.

**Causa:** Data transfer tra cloud provider è costoso ($0.08-0.12/GB).

**Soluzione:** (1) Minimizzare data movement tra cloud, (2) caching locale per dati remoti, (3) compressione dati in transito, (4) valutare se multi-cloud è davvero necessario per quel workload.

---

## FAQ — 20 domande e risposte

### FAQ 1: Da dove inizio con FinOps?

Fase Inform: (1) implementare tagging obbligatorio, (2) attivare cost visibility (Cost Explorer, Azure Cost Management), (3) creare dashboard per team, (4) identificare i primi quick win (risorse idle, scheduling non-prod). Non servono tool costosi per iniziare.

### FAQ 2: Quanto posso risparmiare realisticamente?

Il risparmio tipico per un'organizzazione che non ha mai fatto FinOps è del 20-35% nei primi 6 mesi. Le fonti principali: scheduling non-prod (65-70% del costo non-prod), RI/SP (30-60% su baseline), eliminazione sprechi (5-10%), right-sizing (5-15%).

### FAQ 3: FinOps team dedicato o distribuito?

Entrambi. Un team FinOps centralizzato (1-3 persone per ogni $50M di spend) fornisce tooling, governance e best practice. Ma ogni team engineering è responsabile del proprio costo. Il FinOps team abilita, non esegue.

### FAQ 4: Come misuro il successo del FinOps?

KPI chiave: (1) cost avoidance (costi evitati grazie a ottimizzazioni), (2) savings rate (% risparmiato rispetto a on-demand), (3) tag compliance (% risorse taggate), (4) budget adherence (scostamento dal budget), (5) unit economics trend (costo per request/utente).

### FAQ 5: Reserved Instances o Savings Plans?

Per massima flessibilità: Savings Plans (Compute SP). Per massimo risparmio su workload stabili e prevedibili: Reserved Instances. Strategia raccomandata: 40-50% Compute SP + 20-30% RI su workload più stabili.

### FAQ 6: Come gestisco il chargeback per risorse condivise?

Opzioni: (1) proporzionale all'utilizzo (CPU time, request count), (2) proporzionale alle risorse richieste (Kubernetes request), (3) split equo, (4) overhead fisso per team. Iniziare con showback (visibilità senza fatturazione interna), poi evolvere verso chargeback quando la cultura è matura.

### FAQ 7: Quanto tagging è "abbastanza"?

Minimum viable: team, environment, project. Target: > 95% delle risorse con tag obbligatori, < 5% di costo non allocato. Non esagerare: troppi tag creano overhead. 5-8 tag obbligatori + 3-5 opzionali è un buon equilibrio.

### FAQ 8: Come gestisco la resistenza dei team al FinOps?

(1) Rendere i costi visibili (showback), non punitivi. (2) Gamification: classifiche di efficienza tra team. (3) Celebrare i risparmi. (4) Budget ownership = empowerment. (5) Dimostrare che FinOps libera budget per innovazione.

### FAQ 9: Cloud provider singolo o multi-cloud per ottimizzare i costi?

Controintuitivamente, single-cloud è spesso più economico: sconti volume più alti, no costi di egress tra cloud, team skill concentrato, tooling unificato. Multi-cloud ha senso per compliance, disaster recovery, o best-of-breed su servizi specifici, ma il costo operativo è significativo.

### FAQ 10: Come gestisco i costi di un ambiente Kubernetes?

(1) kubecost o OpenCost per visibilità, (2) ResourceQuota per namespace, (3) LimitRange per default, (4) VPA per right-sizing, (5) cluster autoscaler / Karpenter per infrastruttura, (6) Spot per workload tolleranti, (7) monitoring costo per namespace/label/deployment.

### FAQ 11: Qual è il rapporto ideale infra cost / revenue?

Dipende dal settore. SaaS tipico: 15-25% di COGS cloud su revenue. Startup early-stage: può essere > 30%. Scale-up: target 15-20%. Enterprise: 10-15%. Il trend deve essere decrescente (economia di scala). Se cresce, investigare inefficienze.

### FAQ 12: Come gestisco i costi serverless (Lambda, Cloud Functions)?

Serverless è cost-effective per workload intermittente. Monitorare: (1) invocazioni e durata, (2) memoria allocata vs usata, (3) costo per invocazione. Ottimizzare: (1) ridurre durata (cold start, codice), (2) right-size memoria (128MB vs 1GB impatta prezzo e velocità), (3) valutare alternative per workload costante.

### FAQ 13: Come gestisco i costi di data transfer?

(1) VPC Endpoint per servizi AWS (S3, DynamoDB — gratuiti), (2) CloudFront/CDN per content delivery, (3) compressione, (4) caching ai bordi, (5) co-locazione servizi nella stessa AZ, (6) negoziare waiver egress nel contratto enterprise.

### FAQ 14: Come giustifico il budget per tool FinOps?

ROI tipico: tool FinOps costa 1-3% dello spend cloud, genera risparmi del 20-30%. Esempio: $100K di spend → tool $1-3K → risparmio $20-30K. Presentare con: (1) costo attuale, (2) risparmio identificabile, (3) payback period (tipicamente < 3 mesi).

### FAQ 15: Come gestisco Spot interruptions in produzione?

(1) Mixed instance policy (20-30% on-demand base + Spot), (2) diversificazione instance type (5-10 tipi), (3) graceful shutdown handler (salvare stato in 2 minuti), (4) HPA per riscalare rapidamente, (5) PDB (PodDisruptionBudget) per garantire disponibilità minima.

### FAQ 16: Come ottimizzo i costi di CI/CD?

(1) Spot/Preemptible per CI runner, (2) caching delle dipendenze, (3) parallelizzazione test, (4) build incrementale, (5) image layer caching, (6) self-hosted runner su hardware esistente per workload pesanti, (7) scheduling dei build batch fuori orario di punta.

### FAQ 17: Come gestisco i costi dopo un'acquisizione/fusione?

(1) Audit completo dello spending di entrambe le organizzazioni, (2) consolidamento account per sconti volume, (3) unificazione tagging strategy, (4) identificazione duplicazioni di servizio, (5) negoziazione contratto unificato con il cloud provider.

### FAQ 18: Come gestisco i costi di GPU/ML?

GPU instance sono costose (p4d.24xlarge: ~$32/ora). Ottimizzare: (1) Spot per training (checkpoint regolari), (2) right-size GPU (non usare A100 per inference leggera), (3) scheduling rigoroso, (4) SageMaker Inference per inference serverless, (5) modelli più piccoli/distilled quando possibile.

### FAQ 19: Qual è l'impatto del FinOps sulla velocità di sviluppo?

FinOps ben implementato non rallenta lo sviluppo. Automatizzare: scheduling, cleanup, tagging. Dare ai team budget e libertà di spendere entro i limiti. Il FinOps che rallenta è FinOps fatto male (troppa burocrazia, approvazioni manuali per ogni risorsa).

### FAQ 20: Come gestisco i crediti cloud e i programmi di startup?

(1) Tracciare scadenza crediti in un registro centralizzato, (2) pianificare utilizzo prima della scadenza, (3) non basare il budget futuro sulla disponibilità di crediti, (4) separare costo "reale" da costo "coperto da crediti" nel reporting, (5) pianificare il cliff (momento in cui i crediti finiscono) con 6 mesi di anticipo.

---

## Letture

- FinOps Foundation. https://www.finops.org/
- FinOps Framework. https://www.finops.org/framework/
- AWS Cost Optimization Pillar. https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/
- Azure Cost Management. https://learn.microsoft.com/en-us/azure/cost-management-billing/
- GCP Cost Management. https://cloud.google.com/billing/docs/concepts
- kubecost Documentation. https://docs.kubecost.com/
- OpenCost. https://www.opencost.io/
- Flexera State of the Cloud Report. https://www.flexera.com/blog/cloud/cloud-computing-trends/
- FinOps Certified Practitioner. https://learn.finops.org/

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione |
|---|---|---|
| [01-cloud-aws](01-cloud-aws.md) | Cloud AWS | Reserved Instances, Savings Plans, Cost Explorer e budget alert specifici AWS |
| [02-cloud-azure](02-cloud-azure.md) | Cloud Azure | Azure Cost Management, Reservations e MACC commitment per governance costi Azure |
| [03-cloud-gcp](03-cloud-gcp.md) | Cloud GCP | CUD, Billing export a BigQuery e raccomandazioni di rightsizing GCP |
| [05-kubernetes](05-kubernetes.md) | Kubernetes | kubecost, OpenCost e VPA per visibilita' e ottimizzazione costi a livello container |
| [04-infrastructure-as-code](04-infrastructure-as-code.md) | Infrastructure as Code | Infracost per stima costi pre-deploy e tagging enforcement via Terraform |
| [22-multi-tenancy-isolation](22-multi-tenancy-isolation.md) | Multi-Tenancy Isolation | Showback e chargeback per tenant richiedono cost allocation granulare per namespace |

---

## Glossario

| Termine | Definizione |
|---|---|
| **FinOps** | Cloud Financial Operations — practice cross-team per la gestione dei costi cloud. |
| **Inform** | Prima fase FinOps: visibilità e allocazione dei costi. |
| **Optimize** | Seconda fase FinOps: azioni di ottimizzazione (right-sizing, RI/SP, waste elimination). |
| **Operate** | Terza fase FinOps: governance continua, automazione, cultura. |
| **Reserved Instance (RI)** | Commitment pre-pagato 1-3 anni per sconti su compute. |
| **Savings Plans (SP)** | Commitment flessibile su spesa compute ($/ora) per sconti AWS. |
| **Showback** | Visibilità dei costi per team senza ri-fatturazione interna. |
| **Chargeback** | Addebito effettivo dei costi al budget del team consumatore. |
| **Rightsizing** | Adattare instance type e dimensione all'utilizzo reale del workload. |
| **Tagging** | Metadata associati alle risorse cloud per allocazione costi e governance. |
| **Spot instance** | Capacità compute a prezzo scontato (fino a 90%), interrompibile dal provider. |
| **Preemptible VM** | Equivalente GCP delle Spot instance AWS. |
| **kubecost** | Tool per visibilità e ottimizzazione costi in cluster Kubernetes. |
| **OpenCost** | Progetto CNCF open source per cost monitoring Kubernetes. |
| **Unit economics** | Metriche che collegano costo infrastruttura a unità di business (utente, request, transazione). |
| **Cost allocation** | Processo di attribuzione dei costi cloud a team, progetti o centri di costo. |
| **Budget alert** | Notifica automatica quando la spesa supera una soglia definita. |
| **Anomaly detection** | Identificazione automatica di pattern di spesa anomali. |
| **EDP** | Enterprise Discount Program — sconto volume su AWS. |
| **MACC** | Microsoft Azure Consumption Commitment — commitment di spesa su Azure. |
| **CUD** | Committed Use Discount — sconto su commitment GCP. |
| **SCP** | Service Control Policy — policy organizzative AWS per limitare azioni. |
| **VPA** | Vertical Pod Autoscaler — raccomandazioni di right-sizing per container Kubernetes. |
| **COGS** | Cost of Goods Sold — costo diretto di erogazione del servizio. |
| **Idle resources** | Risorse cloud attive ma non utilizzate o sottoutilizzate. |
| **Orphaned resources** | Risorse cloud disconnesse dal workload originale (volumi, IP, snapshot). |
| **Effective Savings Rate (ESR)** | Metrica principale FinOps: percentuale di risparmio rispetto al costo on-demand equivalente. |
| **Storage tiering** | Strategia di spostamento dati tra tier di storage diversi in base alla frequenza di accesso. |
| **Lifecycle policy** | Regole automatiche per transizione, archiviazione o eliminazione di oggetti storage nel tempo. |
| **Intelligent-Tiering** | Classe di storage AWS S3 che sposta automaticamente i dati tra tier senza retrieval fee. |
| **GreenOps** | Estensione del FinOps che integra metriche di sostenibilita' ambientale nella gestione cloud. |
| **Carbon intensity** | Quantita' di CO2 emessa per unita' di energia consumata (gCO2/kWh), variabile per regione. |
| **Scope 3 emissions** | Emissioni indirette nella catena del valore, incluso consumo cloud e produzione hardware. |
| **Isolation Forest** | Algoritmo ML di anomaly detection basato sull'isolamento di osservazioni anomale. |
| **Infracost** | Tool shift-left che stima l'impatto economico delle modifiche IaC nelle pull request. |
| **Vantage** | Piattaforma multi-cloud di cost visibility e reporting per team FinOps. |
| **CloudHealth** | Piattaforma enterprise (Broadcom/VMware) per governance e gestione costi multi-cloud. |
| **Spot.io** | Piattaforma di automazione per Spot instances e ottimizzazione compute cloud. |
| **CAST AI** | Piattaforma di ottimizzazione automatica dei costi Kubernetes con right-sizing e Spot. |
| **FinOps maturity model** | Modello a quattro livelli (Crawl, Walk, Run, Sprint) per valutare la maturita' FinOps. |
| **CSRD** | Corporate Sustainability Reporting Directive — normativa UE per rendicontazione sostenibilita'. |
| **Cost avoidance** | Costi evitati grazie ad azioni proattive di ottimizzazione FinOps. |
| **Community of Practice** | Gruppo cross-funzionale dedicato alla condivisione di best practice FinOps. |
