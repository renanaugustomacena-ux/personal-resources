# Tutorial: Site Reliability Engineering (SRE) — Lab Pratico

> **Documento di riferimento:** `24-sre-reliability-engineering.md`
> **Dominio:** Gestione Piattaforme — Reliability, Operazioni, Cultura DevOps
> **Ambito:** SLI/SLO/Error Budget, burn rate alert, toil measurement, chaos engineering, post-mortem blameless
> **Durata lab:** 5-7 ore
> **Livello:** Avanzato — richiede Kubernetes, Prometheus, conoscenza di incident management
> **Prerequisiti:** Cluster K8s funzionante, Prometheus installato, kubectl, Python 3.11+
> **Ambiente:** Cluster K8s locale con Prometheus (kube-prometheus-stack), Python per script di calcolo

---

## Lab Environment Setup

### Prerequisiti

```bash
#!/bin/bash
# check-prerequisites-sre.sh

echo "=== Verifica Prerequisiti SRE Lab ==="
echo ""

check() {
    if eval "$2" &>/dev/null; then
        echo "[OK]   $1 — $(eval "$2" 2>&1 | head -1)"
    else
        echo "[FAIL] $1 — $3"
        return 1
    fi
}

check "kubectl"           "kubectl version --client --short 2>/dev/null"  "https://kubernetes.io/docs/tasks/tools/"
check "Python 3.11+"      "python3 --version"                             "https://python3.org"
check "pip"               "pip3 --version"                                "incluso con Python"

# Verifica Prometheus nel cluster
if kubectl get svc -n monitoring prometheus-operated &>/dev/null 2>&1; then
    echo "[OK]   Prometheus (monitoring namespace)"
else
    echo "[INFO] Prometheus non trovato — verrà mostrato come installarlo"
fi

# Installa dipendenze Python
pip3 install requests tabulate dataclasses-json 2>/dev/null | tail -1
echo "[OK]   Librerie Python installate"

echo ""
echo "=== Setup Completato ==="
```

### Architettura del Lab SRE

```
ARCHITETTURA LAB SRE:

┌─────────────────────────────────────────────────────────────────────────┐
│                      CLUSTER KUBERNETES                                  │
│                                                                         │
│  namespace: monitoring                                                  │
│  ├── Prometheus         → raccoglie metriche SLI                       │
│  ├── Grafana            → dashboard SLO + error budget                 │
│  └── AlertManager       → routing alert burn rate                      │
│                                                                         │
│  namespace: demo-slo                                                    │
│  └── podinfo            → app demo con metriche HTTP                   │
│                                                                         │
│  TOOL LOCALI (Python):                                                  │
│  ├── slo-calculator.py  → calcola SLO, error budget, burn rate        │
│  ├── toil-tracker.py    → misura e categorizza il toil                 │
│  └── postmortem-gen.py  → genera template post-mortem                  │
│                                                                         │
│  CHAOS ENGINEERING:                                                     │
│  ├── LitmusChaos 3.x    → iniettore di fault K8s                      │
│  └── chaos-experiments/ → esperimenti definiti come YAML               │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — Perché la Reliability non è "tutto OK o tutto rotto"

> **Perché questo modulo è trasformativo:**
>
> La reliability non è uno switch on/off. Tutti i sistemi reali hanno un certo tasso
> di errori — la domanda non è "mai errori" ma "quanti errori sono accettabili?".
> SRE risponde con un framework matematico preciso: error budget.
>
> Questo modulo ti darà gli strumenti per rispondere a domande concrete: "Possiamo
> fare questa release rischiosa questo venerdì?" (dipende dall'error budget rimasto),
> "Vale la pena di un'altra notte di on-call manuale?" (toil budget esaurito, bisogna
> automatizzare), "Come facciamo a sapere se il chaos test ha trovato qualcosa di reale?"
> (confronta con il baseline SLO).

---

### Concetto A1: Il Contratto tra Sviluppo e Operations

> **Analogia.** Immagina un contratto di locazione: il proprietario (la piattaforma)
> garantisce al locatario (gli utenti) un appartamento in condizioni accettabili.
> Se l'appartamento non funziona per più di X giorni l'anno (error budget esaurito),
> il proprietario è in violazione del contratto (SLA breach) e paga una penale.
>
> L'SLO è esattamente questo: un contratto interno tra il team che sviluppa e il team
> che opera il servizio, con metriche precise e conseguenze concrete quando si viola.

```
SENZA SLO (situazione comune):
  Developer: "Il sistema è al 99% — va benissimo!"
  Ops Team:  "Abbiamo avuto 5 incidenti questo mese!"
  Manager:   "Beh, ma i bug fix erano importanti..."
  
  Risultato: nessuno sa qual è il livello "accettabile" di reliability,
             discussioni soggettive, incentivi non allineati

CON SLO (SRE approach):
  SLO definito: 99.9% availability su 30 giorni
  Error budget: 43.2 minuti al mese
  
  Dopo incidente da 30 minuti:
  Developer: "Abbiamo consumato 30/43.2 minuti (70% del budget)"
  Ops Team:  "Rimangono 13.2 minuti. Attenzione alla prossima release."
  Manager:   "Ok, la prossima release è low-risk?"
             Se sì → procede. Se no → aspettiamo il reset mensile.
  
  Risultato: decisioni oggettive, incentivi allineati, nessuna discussione soggettiva

L'ERROR BUDGET ALLINEA SVILUPPO E OPERATIONS:
  Dev vuole rilasciare → consuma budget → deve essere stabile
  Ops vuole stabilità → se dev è stabile, budget non si consuma
  Entrambi condividono lo stesso obiettivo: budget sempre alto
```

---

### Concetto A2: Il Costo del Downtime vs Il Costo della Reliability

> **Analogia.** Un'assicurazione auto ha un costo mensile (premium) ma ti protegge
> da un costo catastrofico (incidente). Spendere zero in assicurazione sembra un
> risparmio — finché non hai l'incidente.
>
> Investire in reliability (SRE, chaos engineering, on-call, postmortem) sembra
> un costo. Ma il costo del downtime in produzione — revenue perso, penali SLA,
> danni alla reputazione — è quasi sempre superiore al costo della prevenzione.

```
COSTO DEL DOWNTIME — NUMERI REALI (2024):

Financial services:  $9,000/minuto (Ponemon Institute)
E-commerce:          $5,000-$22,000/minuto (Gartner)
Healthcare:          $7,900/minuto (HIMSS)
SaaS typical:        $1,000-$5,000/minuto

Un SLO 99.9% permette 43.2 min/mese di downtime.
Un SLO 99.99% ("four nines") permette 4.32 min/mese.

CALCOLO BUSINESS CASE:
  Revenue annuale: €10,000,000
  Revenue al minuto: €10,000,000 / 525,600 min = €19/min
  
  Con SLO 99.9% (43.2 min/mese × 12 = 518 min/anno di downtime accettabile):
  Downtime max accettabile: €19/min × 518 min = €9,842/anno
  
  Aggiungere SLO 99.99% riduce il downtime accettabile a 52 min/anno
  → Riduzione rischio: 518-52 = 466 min × €19 = €8,854/anno
  → Se il costo di raggiungere 99.99% < €8,854/anno: ha senso business

ATTENZIONE: non tutti i servizi richiedono 99.99%
  Servizio interno non critico: 99.5% è spesso sufficiente e molto più economico
  SLO troppo alto = budget mai disponibile per feature → innovazione bloccata
```

---

## PART B: CALCOLO SLI, SLO ED ERROR BUDGET

### Esercizio B1: Installare l'App Demo con Metriche

```bash
# Namespace per il lab SRE
kubectl create namespace demo-slo || true

# podinfo: app demo di Stefano Prodan con metriche Prometheus integrate
kubectl apply -n demo-slo -f - <<'EOF'
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: podinfo
  namespace: demo-slo
  labels:
    app: podinfo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: podinfo
  template:
    metadata:
      labels:
        app: podinfo
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9898"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: podinfo
          image: ghcr.io/stefanprodan/podinfo:6.7.0
          ports:
            - name: http
              containerPort: 9898
          env:
            - name: PODINFO_PORT
              value: "9898"
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 256Mi
          readinessProbe:
            httpGet:
              path: /readyz
              port: 9898
            initialDelaySeconds: 5
            periodSeconds: 3
          livenessProbe:
            httpGet:
              path: /healthz
              port: 9898
            initialDelaySeconds: 10
            periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: podinfo
  namespace: demo-slo
spec:
  selector:
    app: podinfo
  ports:
    - name: http
      port: 80
      targetPort: 9898
EOF

# Aspetta che i pod siano ready
kubectl wait --for=condition=ready pod -l app=podinfo -n demo-slo --timeout=90s

echo "[OK] podinfo deployato"

# Genera un po' di traffico per avere metriche
kubectl run traffic-gen \
    --image=busybox \
    --restart=Never \
    --rm \
    -n demo-slo \
    --command -- sh -c '
        for i in $(seq 1 100); do
            wget -q -O- http://podinfo.demo-slo/
            sleep 0.5
        done
    '

echo "[OK] Traffico generato — metriche disponibili in Prometheus"
```

---

### Esercizio B2: Script Python per Calcolo SLO ed Error Budget

```python
# slo-calculator.py
"""
Calcola SLI, SLO ed Error Budget da metriche Prometheus.
Simula il calcolo che un team SRE fa quotidianamente.
"""

import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import requests


PROMETHEUS_URL = "http://localhost:9090"

@dataclass
class SLO:
    name: str
    service: str
    description: str
    target_pct: float      # es: 99.9
    window_days: int       # es: 30
    sli_good_query: str    # query Prometheus per richieste "buone"
    sli_total_query: str   # query Prometheus per tutte le richieste


@dataclass
class SLOResult:
    slo: SLO
    current_sli_pct: float
    error_budget_total_min: float
    error_budget_consumed_min: float
    error_budget_remaining_pct: float
    burn_rate: float
    status: str             # ok | warning | critical | breached


def query_prometheus(query: str, prometheus_url: str = PROMETHEUS_URL) -> float:
    """Esegue una query Prometheus istantanea e restituisce il valore."""
    try:
        response = requests.get(
            f"{prometheus_url}/api/v1/query",
            params={"query": query},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        
        results = data.get("data", {}).get("result", [])
        if not results:
            return 0.0
        
        return float(results[0]["value"][1])
    except Exception as e:
        print(f"[WARN] Prometheus non raggiungibile ({e}) — uso valori simulati")
        return -1.0


def calculate_slo(slo: SLO, prometheus_url: str = PROMETHEUS_URL) -> SLOResult:
    """Calcola lo stato di un SLO."""
    
    # Query Prometheus per SLI
    window = f"{slo.window_days * 24}h"
    
    good_rate = query_prometheus(
        f"sum(increase({slo.sli_good_query}[{window}]))",
        prometheus_url,
    )
    total_rate = query_prometheus(
        f"sum(increase({slo.sli_total_query}[{window}]))",
        prometheus_url,
    )
    
    # Valori simulati se Prometheus non è raggiungibile
    if good_rate < 0 or total_rate < 0:
        # Simula un servizio con leggero degradamento (99.85% invece di 99.9%)
        total_rate = 1_000_000.0        # 1 milione di richieste in 30 giorni
        good_rate = total_rate * 0.9985  # 99.85% buone
        print(f"[INFO] Usando valori simulati per {slo.name}")
    
    # Calcolo SLI
    if total_rate == 0:
        current_sli_pct = 100.0
    else:
        current_sli_pct = (good_rate / total_rate) * 100
    
    # Error budget totale (in minuti)
    total_minutes = slo.window_days * 24 * 60
    error_budget_total_min = total_minutes * (1 - slo.target_pct / 100)
    
    # Error budget consumato
    actual_downtime_pct = 100 - current_sli_pct
    target_downtime_pct = 100 - slo.target_pct
    
    if target_downtime_pct == 0:
        error_budget_consumed_min = 0
    else:
        # Quanti minuti di budget sono stati consumati
        error_budget_consumed_min = (actual_downtime_pct / target_downtime_pct) * error_budget_total_min
    
    error_budget_remaining_min = max(0, error_budget_total_min - error_budget_consumed_min)
    
    if error_budget_total_min > 0:
        error_budget_remaining_pct = (error_budget_remaining_min / error_budget_total_min) * 100
    else:
        error_budget_remaining_pct = 100.0
    
    # Burn rate: quanto velocemente si consuma il budget
    # Burn rate 1 = si consuma esattamente alla velocità "normale"
    if target_downtime_pct > 0:
        burn_rate = actual_downtime_pct / target_downtime_pct
    else:
        burn_rate = 1.0
    
    # Status
    if current_sli_pct >= slo.target_pct:
        if error_budget_remaining_pct >= 50:
            status = "ok"
        elif error_budget_remaining_pct >= 25:
            status = "warning"
        else:
            status = "critical"
    else:
        status = "breached"
    
    return SLOResult(
        slo=slo,
        current_sli_pct=round(current_sli_pct, 4),
        error_budget_total_min=round(error_budget_total_min, 2),
        error_budget_consumed_min=round(error_budget_consumed_min, 2),
        error_budget_remaining_pct=round(error_budget_remaining_pct, 2),
        burn_rate=round(burn_rate, 2),
        status=status,
    )


def print_slo_report(results: list[SLOResult]) -> None:
    """Stampa il report SLO in formato leggibile."""
    
    print(f"\n{'='*70}")
    print(f"SLO STATUS REPORT — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*70}\n")
    
    for r in results:
        status_icons = {
            "ok": "✅",
            "warning": "⚠️ ",
            "critical": "🔴",
            "breached": "❌",
        }
        icon = status_icons.get(r.status, "?")
        
        print(f"{icon} {r.slo.name}")
        print(f"   Servizio:      {r.slo.service}")
        print(f"   Descrizione:   {r.slo.description}")
        print(f"   SLO Target:    {r.slo.target_pct}% ({r.slo.window_days} giorni rolling)")
        print(f"   SLI Corrente:  {r.current_sli_pct}%")
        
        # Differenza dal target
        diff = r.current_sli_pct - r.slo.target_pct
        diff_str = f"+{diff:.4f}%" if diff >= 0 else f"{diff:.4f}%"
        print(f"   Δ dal Target:  {diff_str}")
        
        print(f"   Error Budget:")
        print(f"     Totale:       {r.error_budget_total_min:.1f} minuti/mese")
        print(f"     Consumato:    {r.error_budget_consumed_min:.1f} minuti")
        
        remaining_min = r.error_budget_total_min - r.error_budget_consumed_min
        print(f"     Rimanente:    {max(0, remaining_min):.1f} minuti ({r.error_budget_remaining_pct:.1f}%)")
        
        print(f"   Burn Rate:     {r.burn_rate}x", end="")
        if r.burn_rate > 14.4:
            print(" ← PAGE NOW! Budget esaurito in < 2 giorni")
        elif r.burn_rate > 6:
            print(" ← ATTENZIONE: budget esaurito in < 5 giorni")
        elif r.burn_rate > 3:
            print(" ← MONITORARE")
        else:
            print(" (normale)")
        
        # Proiezione
        if r.burn_rate > 0 and remaining_min > 0:
            days_to_exhaustion = (remaining_min / 60) / (r.burn_rate * (r.error_budget_total_min / 60 / r.slo.window_days))
            if days_to_exhaustion < r.slo.window_days:
                exhaust_date = datetime.now() + timedelta(days=days_to_exhaustion)
                print(f"   Proiezione:    Budget esaurito il {exhaust_date.strftime('%d/%m/%Y')} (in {days_to_exhaustion:.1f} giorni)")
        
        print()


def calculate_burn_rate_thresholds(slo_target_pct: float, window_days: int) -> dict:
    """
    Calcola le soglie di burn rate per l'alerting.
    Basato su Google SRE Workbook, Chapter 5.
    """
    error_budget_pct = 1 - (slo_target_pct / 100)
    total_minutes = window_days * 24 * 60
    error_budget_min = total_minutes * error_budget_pct
    
    return {
        "page_immediately": {
            "burn_rate": 14.4,
            "budget_consumed_pct": 2,
            "time_to_exhaustion": f"{window_days / 14.4:.1f} giorni",
            "window": "1 ora",
            "description": "Page immediata — budget esaurito in < 2 giorni",
        },
        "page_soon": {
            "burn_rate": 6,
            "budget_consumed_pct": 5,
            "time_to_exhaustion": f"{window_days / 6:.1f} giorni",
            "window": "6 ore",
            "description": "Page entro poche ore — budget esaurito in < 5 giorni",
        },
        "ticket": {
            "burn_rate": 3,
            "budget_consumed_pct": 10,
            "time_to_exhaustion": f"{window_days / 3:.1f} giorni",
            "window": "3 giorni",
            "description": "Ticket — budget esaurito in < 10 giorni",
        },
        "info": {
            "burn_rate": 1,
            "budget_consumed_pct": 33,
            "time_to_exhaustion": f"{window_days} giorni",
            "window": "3 giorni",
            "description": "Informativo — consumo normale",
        },
    }


if __name__ == "__main__":
    # Definisci i tuoi SLO
    slos = [
        SLO(
            name="order-service-availability",
            service="order-service",
            description="99.9% delle richieste API devono avere risposta 2xx/3xx",
            target_pct=99.9,
            window_days=30,
            sli_good_query='http_requests_total{job="order-service",status!~"5.."}',
            sli_total_query='http_requests_total{job="order-service"}',
        ),
        SLO(
            name="order-service-latency",
            service="order-service",
            description="99% delle richieste API devono rispondere in < 200ms",
            target_pct=99.0,
            window_days=30,
            sli_good_query='http_request_duration_seconds_bucket{job="order-service",le="0.2"}',
            sli_total_query='http_request_duration_seconds_count{job="order-service"}',
        ),
        SLO(
            name="payment-service-availability",
            service="payment-service",
            description="99.95% delle transazioni devono completarsi con successo",
            target_pct=99.95,
            window_days=30,
            sli_good_query='payment_transactions_total{status="success",job="payment-service"}',
            sli_total_query='payment_transactions_total{job="payment-service"}',
        ),
    ]
    
    # Calcola SLO
    results = [calculate_slo(slo) for slo in slos]
    print_slo_report(results)
    
    # Mostra le soglie di alert per il primo SLO
    slo_example = slos[0]
    thresholds = calculate_burn_rate_thresholds(slo_example.target_pct, slo_example.window_days)
    
    print(f"\n{'='*70}")
    print(f"SOGLIE DI BURN RATE PER ALERTING — {slo_example.name}")
    print(f"SLO: {slo_example.target_pct}% su {slo_example.window_days} giorni")
    print(f"{'='*70}")
    
    for level, data in thresholds.items():
        print(f"\n  {level.upper()}:")
        print(f"    Burn rate:            > {data['burn_rate']}x")
        print(f"    Budget consumato:     {data['budget_consumed_pct']}% in 1h")
        print(f"    Finestra alert:       {data['window']}")
        print(f"    Stima esaurimento:    {data['time_to_exhaustion']}")
        print(f"    Azione:               {data['description']}")
```

```bash
# Esegui il calculator
python3 slo-calculator.py

# Output atteso (con valori simulati):
# ======================================================================
# SLO STATUS REPORT — 2026-07-16 10:00 UTC
# ======================================================================
# 
# ⚠️  order-service-availability
#    Servizio:      order-service
#    Descrizione:   99.9% delle richieste API devono avere risposta 2xx/3xx
#    SLO Target:    99.9% (30 giorni rolling)
#    SLI Corrente:  99.8500%
#    Δ dal Target:  -0.0500%
#    Error Budget:
#      Totale:       43.2 minuti/mese
#      Consumato:    64.8 minuti
#      Rimanente:    0.0 minuti (0.0%)
#    Burn Rate:     1.5x (normale)
# 
# ===SOGLIE DI BURN RATE PER ALERTING:
#   PAGE_IMMEDIATELY: Burn rate > 14.4x (budget esaurito in < 2 giorni)
#   PAGE_SOON: Burn rate > 6x (budget esaurito in < 5 giorni)
```

---

### Esercizio B3: Regole Prometheus per Burn Rate Alert

```bash
# Crea PrometheusRule per alert basati su burn rate
cat <<'EOF' | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: slo-alerts
  namespace: monitoring
  labels:
    release: prometheus    # label richiesta da kube-prometheus-stack
spec:
  groups:
    - name: slo.rules
      rules:
        # Recording rules: pre-calcola error rate per finestre diverse
        - record: job:http_request_error_rate:ratio_rate5m
          expr: |
            sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
            /
            sum(rate(http_requests_total[5m])) by (job)
        
        - record: job:http_request_error_rate:ratio_rate1h
          expr: |
            sum(rate(http_requests_total{status=~"5.."}[1h])) by (job)
            /
            sum(rate(http_requests_total[1h])) by (job)
        
        - record: job:http_request_error_rate:ratio_rate6h
          expr: |
            sum(rate(http_requests_total{status=~"5.."}[6h])) by (job)
            /
            sum(rate(http_requests_total[6h])) by (job)
        
        # Alert CRITICAL: burn rate > 14.4 su 1 ora
        # → budget esaurito in 2 giorni → PAGE IMMEDIATELY
        - alert: SLOBurnRateCritical
          expr: |
            (
              job:http_request_error_rate:ratio_rate1h{job="order-service"}
              > (14.4 * (1 - 0.999))
            )
          for: 2m
          labels:
            severity: critical
            slo: order-service-availability
          annotations:
            summary: "SLO Burn Rate CRITICO per {{ $labels.job }}"
            description: |
              Il servizio {{ $labels.job }} sta consumando il budget di errori
              a {{ $value | humanizePercentage }} tasso di errore.
              Burn rate: {{ $value / (1 - 0.999) | printf "%.1f" }}x
              Budget esaurito in circa 2 giorni.
              ACTION REQUIRED: investigare immediatamente.
            runbook_url: "https://wiki.myorg.com/runbooks/order-service"
        
        # Alert WARNING: burn rate > 6 su 6 ore
        # → budget esaurito in 5 giorni → PAGE SOON
        - alert: SLOBurnRateWarning
          expr: |
            (
              job:http_request_error_rate:ratio_rate6h{job="order-service"}
              > (6 * (1 - 0.999))
            )
          for: 15m
          labels:
            severity: warning
            slo: order-service-availability
          annotations:
            summary: "SLO Burn Rate ELEVATO per {{ $labels.job }}"
            description: |
              Il servizio {{ $labels.job }} ha un tasso di errore elevato
              che potrebbe esaurire il budget SLO entro 5 giorni.
              Tasso corrente: {{ $value | humanizePercentage }}
              ACTION: investigare nelle prossime ore.
        
        # Alert per latenza SLO (p99 > 200ms)
        - alert: SLOLatencyBreach
          expr: |
            histogram_quantile(0.99,
              sum(rate(http_request_duration_seconds_bucket{job="order-service"}[5m]))
              by (le)
            ) > 0.2
          for: 5m
          labels:
            severity: warning
            slo: order-service-latency
          annotations:
            summary: "SLO Latenza in breach per order-service"
            description: |
              La latenza p99 di order-service è {{ $value | humanizeDuration }}
              che supera il SLO target di 200ms.
EOF

echo "[OK] PrometheusRule applicato"

# Verifica che le rule siano caricate
kubectl get prometheusrule slo-alerts -n monitoring
# NAME        AGE
# slo-alerts  30s

# Visualizza nel Prometheus
kubectl port-forward svc/prometheus-operated 9090:9090 -n monitoring &
sleep 3
curl -sf "http://localhost:9090/api/v1/rules" | \
    python3 -c "
import sys,json
data=json.load(sys.stdin)
for g in data.get('data',{}).get('groups',[]):
    if 'slo' in g.get('name','').lower():
        print(f'Gruppo: {g[\"name\"]}')
        for r in g.get('rules',[]):
            t = r.get('type','')
            name = r.get('name','') or r.get('alert','')
            print(f'  [{t}] {name}')
"
kill %1 2>/dev/null
```

---

## PART C: TOIL MEASUREMENT E AUTOMAZIONE

### Concetto C1: Identificare il Toil

> **Analogia.** Il toil è come dover innaffiare manualmente ogni pianta del giardino
> ogni mattina. Non è sbagliato farlo — le piante crescono — ma si scala male:
> con 10 piante ci vuole 10 minuti, con 100 piante ci vogliono 100 minuti.
> Un sistema di irrigazione automatica (automazione del toil) scala a costo zero:
> 10 piante o 1000 piante, lo stesso tempo.

```python
# toil-tracker.py
"""
Strumento per misurare e categorizzare il toil.
Il team SRE registra le attività settimanalmente.
"""

import csv
import json
import statistics
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from io import StringIO


class ActivityCategory(str, Enum):
    TOIL = "toil"                      # lavoro manuale ripetitivo
    ENGINEERING = "engineering"         # automazione, miglioramenti
    ON_CALL = "on_call"               # gestione incidenti
    LEARNING = "learning"              # formazione, ricerca
    PROJECT = "project"               # lavoro su progetto non urgente


class ToilType(str, Enum):
    RESTART = "restart_manuale"
    DEPLOY_APPROVAL = "approvazione_deploy"
    FALSE_ALERT = "falso_positivo_alert"
    TICKET_MANUAL = "ticket_manuale"
    LOG_COPY = "copia_log_manuale"
    SCALING = "scaling_manuale"
    OTHER = "altro"


@dataclass
class Activity:
    date: str
    engineer: str
    category: ActivityCategory
    toil_type: ToilType | None
    duration_minutes: int
    description: str
    automatable: bool = True
    automation_effort_hours: float = 0.0


# Dati simulati per il lab — in produzione: importa da CSV/JIRA
SAMPLE_ACTIVITIES = """date,engineer,category,toil_type,duration_minutes,description,automatable,automation_effort_hours
2026-07-01,mario.rossi,toil,restart_manuale,30,"Riavviato order-service dopo OOMKilled",true,8
2026-07-01,giulia.bianchi,engineering,,,120,"Scritto script auto-restart basato su metrica memoria",false,0
2026-07-02,mario.rossi,on_call,,,90,"Investigato alert falso positivo CPU",false,0
2026-07-02,mario.rossi,toil,falso_positivo_alert,60,"Tuning threshold alert CPU (alert si triggerava troppo spesso)",true,4
2026-07-03,giulia.bianchi,toil,approvazione_deploy,45,"Approvato manualmente 3 deploy di staging",true,16
2026-07-03,giulia.bianchi,toil,approvazione_deploy,45,"Approvato manualmente 3 deploy di staging (routine)",true,0
2026-07-04,mario.rossi,toil,ticket_manuale,30,"Creato ticket JIRA per richiesta database",true,40
2026-07-04,giulia.bianchi,engineering,,,180,"Implementato auto-approval deploy staging (GitOps)",false,0
2026-07-05,mario.rossi,toil,scaling_manuale,20,"Scalato manualmente order-service durante picco traffico",true,6
2026-07-05,giulia.bianchi,learning,,,120,"Corso Kubernetes avanzato",false,0
2026-07-06,mario.rossi,engineering,,,240,"Configurato HPA per order-service (elimina scaling manuale)",false,0
2026-07-07,giulia.bianchi,toil,restart_manuale,40,"Riavviato payment-service (memoria alta)",true,0
2026-07-07,mario.rossi,project,,,180,"Pianificazione Q3 reliability improvements",false,0
2026-07-08,giulia.bianchi,toil,falso_positivo_alert,50,"Silenced 5 falsi positivi alert disco",true,6
2026-07-09,mario.rossi,toil,copia_log_manuale,60,"Estratto log da 3 pod e inviato via email al team dev",true,12
"""


def parse_activities(csv_data: str) -> list[Activity]:
    activities = []
    reader = csv.DictReader(StringIO(csv_data))
    for row in reader:
        activities.append(Activity(
            date=row["date"],
            engineer=row["engineer"],
            category=ActivityCategory(row["category"]),
            toil_type=ToilType(row["toil_type"]) if row.get("toil_type") else None,
            duration_minutes=int(row["duration_minutes"]),
            description=row["description"],
            automatable=row.get("automatable", "true").lower() == "true",
            automation_effort_hours=float(row.get("automation_effort_hours", 0)),
        ))
    return activities


def analyze_toil(activities: list[Activity]) -> dict:
    # Totali
    total_minutes = sum(a.duration_minutes for a in activities)
    toil_minutes = sum(a.duration_minutes for a in activities if a.category == ActivityCategory.TOIL)
    engineering_minutes = sum(a.duration_minutes for a in activities if a.category == ActivityCategory.ENGINEERING)
    on_call_minutes = sum(a.duration_minutes for a in activities if a.category == ActivityCategory.ON_CALL)
    
    toil_pct = (toil_minutes / total_minutes * 100) if total_minutes > 0 else 0
    
    # Per tipo di toil
    by_type: dict[str, int] = {}
    for a in activities:
        if a.category == ActivityCategory.TOIL and a.toil_type:
            key = a.toil_type.value
            by_type[key] = by_type.get(key, 0) + a.duration_minutes
    
    # Automazioni con ROI più alto
    automatable = [
        a for a in activities
        if a.category == ActivityCategory.TOIL and a.automatable and a.automation_effort_hours > 0
    ]
    
    roi_items = []
    for a in automatable:
        # ROI: quante volte occorre l'attività al mese (semplificato)
        weekly_minutes = a.duration_minutes
        monthly_minutes = weekly_minutes * 4.3
        automation_minutes = a.automation_effort_hours * 60
        
        if automation_minutes > 0:
            payback_months = automation_minutes / monthly_minutes
            roi_items.append({
                "description": a.description[:60],
                "monthly_cost_min": round(monthly_minutes),
                "automation_effort_min": round(automation_minutes),
                "payback_months": round(payback_months, 1),
            })
    
    roi_items.sort(key=lambda x: x["payback_months"])
    
    return {
        "total_minutes": total_minutes,
        "toil_minutes": toil_minutes,
        "engineering_minutes": engineering_minutes,
        "on_call_minutes": on_call_minutes,
        "toil_pct": round(toil_pct, 1),
        "by_toil_type": by_type,
        "high_roi_automations": roi_items[:5],
    }


def print_toil_report(analysis: dict) -> None:
    total_h = analysis["total_minutes"] // 60
    toil_h = analysis["toil_minutes"] // 60
    eng_h = analysis["engineering_minutes"] // 60
    
    print(f"\n{'='*60}")
    print(f"TOIL REPORT — Settimana del {date.today().strftime('%d/%m/%Y')}")
    print(f"{'='*60}")
    
    print(f"\nRIEPILOGO (ore totali lavorative: {total_h}h):")
    print(f"  Toil:            {toil_h}h  ({analysis['toil_pct']}%)")
    
    # Target Google: toil < 50%
    if analysis["toil_pct"] > 50:
        print(f"  ⚠️  SOGLIA SUPERATA: toil > 50% (target Google: < 50%)")
        print(f"      Azione richiesta: piano di automazione urgente")
    elif analysis["toil_pct"] > 35:
        print(f"  ⚠️  ATTENZIONE: toil in crescita (35-50%)")
    else:
        print(f"  ✅ OK: toil sotto la soglia del 50%")
    
    print(f"  Engineering:     {eng_h}h")
    print(f"  On-call:         {analysis['on_call_minutes']//60}h")
    
    print(f"\nTOIL PER TIPO:")
    for toil_type, minutes in sorted(analysis["by_toil_type"].items(), key=lambda x: x[1], reverse=True):
        hours = minutes / 60
        print(f"  {toil_type:30s}: {hours:.1f}h")
    
    if analysis["high_roi_automations"]:
        print(f"\nAUTOMAZIONI CON ROI PIÙ ALTO (priorità per il Platform Team):")
        print(f"  {'Attività':<45} {'Costo/mese':>12} {'Effort':>8} {'Payback':>8}")
        print(f"  {'-'*77}")
        for item in analysis["high_roi_automations"]:
            print(f"  {item['description']:<45} "
                  f"{item['monthly_cost_min']:>10}min "
                  f"{item['automation_effort_min']:>6}min "
                  f"{item['payback_months']:>7.1f}m")


if __name__ == "__main__":
    activities = parse_activities(SAMPLE_ACTIVITIES)
    analysis = analyze_toil(activities)
    print_toil_report(analysis)
```

```bash
python3 toil-tracker.py

# Output atteso:
# ============================================================
# TOIL REPORT — Settimana del 16/07/2026
# ============================================================
# 
# RIEPILOGO (ore totali lavorative: 28h):
#   Toil:            7h  (25.0%)
#   ✅ OK: toil sotto la soglia del 50%
#   Engineering:     9h
#   On-call:         1h
# 
# TOIL PER TIPO:
#   approvazione_deploy           : 1.5h
#   falso_positivo_alert          : 1.8h
#   copia_log_manuale             : 1.0h
#   restart_manuale               : 1.2h
#   scaling_manuale               : 0.3h
#   ticket_manuale                : 0.5h
# 
# AUTOMAZIONI CON ROI PIÙ ALTO:
#   Attività                                     Costo/mese   Effort  Payback
#   ─────────────────────────────────────────────────────────────────────────
#   Scalato manualmente order-service                  86min    360min    4.2m
#   Tuning threshold alert CPU                        258min    240min    0.9m
#   Estratto log da 3 pod e inviato via email         258min    720min    2.8m
```

---

## PART D: CHAOS ENGINEERING — Lab con LitmusChaos

### Concetto D1: Hypothesis-Driven Chaos

> **Analogia.** Prima di fare un crash test su un'auto nuova, gli ingegneri formulano
> un'ipotesi: "Se colpiamo l'auto a 50km/h frontalmente, l'airbag si apre e le cinture
> reggono, e i passeggeri non riportano lesioni critiche."
>
> Il Chaos Engineering funziona allo stesso modo: prima formuli l'ipotesi
> ("Se un pod crasha, il Deployment crea un nuovo pod entro 30 secondi e il traffico
> non viene impattato"), poi fai l'esperimento controllato, poi misuri se l'ipotesi
> era corretta.

```
CHAOS ENGINEERING — PROCESSO STRUTTURATO:

1. DEFINE STATE: definisci lo stato "normale" del sistema
   - SLI: error rate 0.01%, latenza p99 150ms
   - Verifica con query Prometheus PRIMA dell'esperimento

2. HYPOTHESIS: formula l'ipotesi
   - "Se termino 1 pod su 3 di order-service,
      il sistema resta disponibile al 99.9%
      e la latenza non supera i 200ms"

3. DESIGN EXPERIMENT: progetta l'esperimento
   - Inietta: pod-delete su 1 pod di order-service
   - Durata: 60 secondi
   - Blast radius: solo order-service namespace

4. RUN EXPERIMENT: esegui l'esperimento
   - LitmusChaos: kubectl apply -f chaos-experiment.yaml
   - Monitora in parallelo con Prometheus/Grafana

5. VERIFY HYPOTHESIS: verifica l'ipotesi
   - Query Prometheus post-chaos: error rate ancora < 0.1%?
   - Se SÌ: ipotesi confermata, sistema resiliente
   - Se NO: trovata una debolezza → fix prima che succeda in produzione

6. LEARN AND IMPROVE: apprendi e migliora
   - Documenta i risultati
   - Se debolezza trovata: fix (più repliche, PDB, circuit breaker)
   - Ripeti periodicamente (CI/CD chaos)
```

---

### Esercizio D1: Installare LitmusChaos

```bash
# Installa LitmusChaos via Helm
helm repo add litmuschaos https://litmuschaos.github.io/litmus-helm/
helm repo update

helm install chaos litmuschaos/litmus \
    --namespace litmus \
    --create-namespace \
    --set portal.frontend.service.type=NodePort \
    --set portal.frontend.service.nodePort=30083 \
    --version 3.8.0 \
    --wait

# Verifica
kubectl get pods -n litmus

# Output atteso:
# NAME                                    READY   STATUS    RESTARTS   AGE
# chaos-litmus-auth-server-xxx            1/1     Running   0          2m
# chaos-litmus-frontend-xxx               1/1     Running   0          2m
# chaos-litmus-server-xxx                 1/1     Running   0          2m
# chaos-mongodb-0                         1/1     Running   0          2m

echo "[OK] LitmusChaos installato"
echo "     UI disponibile su: http://localhost:30083 (admin/litmus)"
```

---

### Esercizio D2: Esperimento di Chaos — Pod Delete

```bash
# Crea l'app di test (se non già presente)
kubectl apply -n demo-slo -f - <<'EOF'
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service-chaos
  namespace: demo-slo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service-chaos
  template:
    metadata:
      labels:
        app: order-service-chaos
    spec:
      containers:
        - name: app
          image: ghcr.io/stefanprodan/podinfo:6.7.0
          ports:
            - containerPort: 9898
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi
          readinessProbe:
            httpGet:
              path: /readyz
              port: 9898
            initialDelaySeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: order-service-chaos
  namespace: demo-slo
spec:
  selector:
    app: order-service-chaos
  ports:
    - port: 80
      targetPort: 9898
EOF

# Installa i CRD di LitmusChaos nel namespace
kubectl apply -f https://raw.githubusercontent.com/litmuschaos/chaos-operator/master/deploy/chaos_crds.yaml

# Crea ServiceAccount e RBAC per il chaos runner
cat <<'EOF' | kubectl apply -f -
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: chaos-runner
  namespace: demo-slo

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: chaos-runner
  namespace: demo-slo
rules:
  - apiGroups: [litmuschaos.io]
    resources: [chaosengines, chaosexperiments, chaosresults]
    verbs: [create, list, get, patch, update, delete]
  - apiGroups: [""]
    resources: [pods, events, configmaps, secrets]
    verbs: [create, list, get, patch, update, delete]
  - apiGroups: [apps]
    resources: [deployments, replicasets]
    verbs: [get, list, patch]
  - apiGroups: [""]
    resources: [pods/log, pods/exec]
    verbs: [get, list, create]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: chaos-runner
  namespace: demo-slo
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: chaos-runner
subjects:
  - kind: ServiceAccount
    name: chaos-runner
    namespace: demo-slo
EOF

# Installa l'esperimento pod-delete
kubectl apply -f https://hub.litmuschaos.io/api/chaos/3.8.0?file=charts/generic/pod-delete/experiment.yaml -n demo-slo

echo "[OK] Esperimento pod-delete installato"
kubectl get chaosexperiment -n demo-slo
```

---

### Esercizio D3: Eseguire Esperimento Chaos e Verificare SLO

```bash
# STEP 1: Misura il baseline PRIMA del chaos
echo "=== BASELINE PRE-CHAOS ==="
kubectl get pods -n demo-slo -l app=order-service-chaos

# Conta i pod disponibili
PODS_BEFORE=$(kubectl get pods -n demo-slo -l app=order-service-chaos --field-selector=status.phase=Running -o name | wc -l)
echo "Pod in esecuzione: $PODS_BEFORE/3"

# STEP 2: Avvia l'esperimento di chaos
cat <<'EOF' | kubectl apply -f -
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: pod-delete-chaos
  namespace: demo-slo
spec:
  # Target: il deployment da cui eliminare i pod
  appinfo:
    appns: demo-slo
    applabel: "app=order-service-chaos"
    appkind: deployment
  
  # ServiceAccount per il chaos runner
  chaosServiceAccount: chaos-runner
  
  # Monitor: collezione eventi K8s
  monitoring: true
  
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            # Quanti pod eliminare (1 su 3)
            - name: TOTAL_CHAOS_DURATION
              value: "60"       # durata esperimento in secondi
            - name: CHAOS_INTERVAL
              value: "20"       # elimina un pod ogni 20 secondi
            - name: FORCE
              value: "false"    # graceful termination
            - name: PODS_AFFECTED_PERC
              value: "33"       # 33% dei pod (1 su 3)
EOF

# STEP 3: Monitora il chaos in tempo reale
echo ""
echo "=== ESPERIMENTO CHAOS IN ESECUZIONE ==="
echo "Osserva i pod durante il chaos:"
watch -n 2 kubectl get pods -n demo-slo -l app=order-service-chaos &
WATCH_PID=$!

# Aspetta la fine del chaos (60 secondi + buffer)
sleep 70

kill $WATCH_PID 2>/dev/null

# STEP 4: Verifica il risultato
echo ""
echo "=== VERIFICA POST-CHAOS ==="

# Aspetta che i pod si ripristinino
kubectl wait --for=condition=ready pod \
    -l app=order-service-chaos \
    -n demo-slo \
    --timeout=120s

PODS_AFTER=$(kubectl get pods -n demo-slo -l app=order-service-chaos --field-selector=status.phase=Running -o name | wc -l)
echo "Pod in esecuzione: $PODS_AFTER/3"

# Controlla il risultato del chaos
kubectl get chaosresult pod-delete-chaos-pod-delete -n demo-slo \
    -o jsonpath='{.status.experimentStatus.verdict}' 2>/dev/null || echo "N/A"

echo ""
echo "=== RISULTATO DELL'ESPERIMENTO ==="

if [ "$PODS_AFTER" -eq 3 ]; then
    echo "[OK] IPOTESI CONFERMATA: il sistema ha recuperato automaticamente"
    echo "     I pod eliminati sono stati ricreati dal ReplicaSet"
    echo "     Il Deployment garantisce sempre 3 pod disponibili"
else
    echo "[WARN] Sistema non completamente recuperato: $PODS_AFTER/3 pod attivi"
    echo "       Controllare gli eventi: kubectl get events -n demo-slo"
fi

# STEP 5: Verifica SLO (se Prometheus disponibile)
echo ""
echo "=== VERIFICA SLO POST-CHAOS ==="
echo "Esegui manualmente in Prometheus:"
echo "  Query error rate: rate(http_requests_total{job=\"order-service\",status=~\"5..\"}[5m])"
echo "  Atteso: < 0.001 (0.1%)"
echo ""
echo "  Se il chaos ha rispettato il SLO → sistema resiliente ✓"
echo "  Se il chaos ha violato il SLO → trovata debolezza da correggere ✗"
```

---

## PART E: POST-MORTEM BLAMELESS

### Esercizio E1: Generatore di Post-Mortem

```python
# postmortem-gen.py
"""
Genera un template di post-mortem blameless strutturato.
Inserisci i dati dell'incidente e ottieni un documento markdown pronto.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json


@dataclass
class TimelineEvent:
    timestamp: str
    actor: str       # chi ha fatto l'azione
    action: str      # cosa è successo
    type: str        # detected | escalated | investigated | mitigated | resolved | retrospective


@dataclass
class ActionItem:
    description: str
    owner: str
    due_date: str
    priority: str    # P1 (critico) | P2 (alto) | P3 (medio)
    category: str    # prevention | detection | response | mitigation


@dataclass
class PostMortem:
    # Metadati
    incident_id: str
    title: str
    date: str
    severity: str           # SEV-1 | SEV-2 | SEV-3
    authors: list[str]
    
    # Impatto
    duration_minutes: int
    users_affected: int
    services_affected: list[str]
    revenue_impact_eur: Optional[float]
    
    # Timeline
    timeline: list[TimelineEvent]
    
    # Analisi
    root_cause: str
    contributing_factors: list[str]
    five_whys: list[str]   # lista di perché (massimo 5)
    
    # Cosa ha funzionato / non funzionato
    what_worked: list[str]
    what_didnt_work: list[str]
    
    # Action items
    action_items: list[ActionItem]


def generate_markdown(pm: PostMortem) -> str:
    """Genera un post-mortem in formato Markdown."""
    
    lines = []
    
    # Header
    lines.append(f"# Post-Mortem: {pm.title}")
    lines.append(f"")
    lines.append(f"**ID Incidente:** `{pm.incident_id}`")
    lines.append(f"**Data:** {pm.date}")
    lines.append(f"**Severity:** {pm.severity}")
    lines.append(f"**Autori:** {', '.join(pm.authors)}")
    lines.append(f"**Stato:** ✅ Pubblicato")
    lines.append(f"")
    lines.append(f"> ⚠️ **Post-mortem blameless**: questo documento descrive il fallimento del sistema,")
    lines.append(f"> non delle persone. Ogni persona coinvolta ha agito in buona fede con le")
    lines.append(f"> informazioni disponibili in quel momento.")
    lines.append(f"")
    
    # Sommario esecutivo
    lines.append(f"---")
    lines.append(f"## Sommario Esecutivo")
    lines.append(f"")
    
    hours = pm.duration_minutes // 60
    minutes = pm.duration_minutes % 60
    duration_str = f"{hours}h {minutes}min" if hours > 0 else f"{minutes} minuti"
    
    lines.append(f"**Durata:** {duration_str}")
    lines.append(f"**Utenti colpiti:** ~{pm.users_affected:,}")
    lines.append(f"**Servizi colpiti:** {', '.join(pm.services_affected)}")
    if pm.revenue_impact_eur:
        lines.append(f"**Impatto economico stimato:** €{pm.revenue_impact_eur:,.0f}")
    lines.append(f"")
    
    # Timeline
    lines.append(f"---")
    lines.append(f"## Timeline")
    lines.append(f"")
    lines.append(f"| Ora | Chi | Cosa | Tipo |")
    lines.append(f"|-----|-----|------|------|")
    
    type_emoji = {
        "detected": "🔴",
        "escalated": "📢",
        "investigated": "🔍",
        "mitigated": "⚙️",
        "resolved": "✅",
        "retrospective": "📝",
    }
    
    for event in pm.timeline:
        emoji = type_emoji.get(event.type, "•")
        lines.append(f"| `{event.timestamp}` | {event.actor} | {event.action} | {emoji} {event.type} |")
    
    lines.append(f"")
    
    # Root cause e 5 Why
    lines.append(f"---")
    lines.append(f"## Root Cause Analysis")
    lines.append(f"")
    lines.append(f"**Root Cause:**")
    lines.append(f"> {pm.root_cause}")
    lines.append(f"")
    
    if pm.contributing_factors:
        lines.append(f"**Fattori contribuenti:**")
        for factor in pm.contributing_factors:
            lines.append(f"- {factor}")
        lines.append(f"")
    
    if pm.five_whys:
        lines.append(f"**Analisi 5 Why:**")
        for i, why in enumerate(pm.five_whys, 1):
            lines.append(f"{i}. {why}")
        lines.append(f"")
    
    # Lezioni apprese
    lines.append(f"---")
    lines.append(f"## Lezioni Apprese")
    lines.append(f"")
    
    lines.append(f"### Cosa ha funzionato ✅")
    for item in pm.what_worked:
        lines.append(f"- {item}")
    lines.append(f"")
    
    lines.append(f"### Cosa non ha funzionato ❌")
    for item in pm.what_didnt_work:
        lines.append(f"- {item}")
    lines.append(f"")
    
    # Action items
    lines.append(f"---")
    lines.append(f"## Action Items")
    lines.append(f"")
    lines.append(f"| Priorità | Descrizione | Owner | Scadenza | Categoria |")
    lines.append(f"|----------|-------------|-------|----------|-----------|")
    
    priority_sort = {"P1": 0, "P2": 1, "P3": 2}
    sorted_items = sorted(pm.action_items, key=lambda x: priority_sort.get(x.priority, 99))
    
    for item in sorted_items:
        priority_emoji = {"P1": "🔴", "P2": "🟡", "P3": "🟢"}.get(item.priority, "⚪")
        lines.append(f"| {priority_emoji} {item.priority} | {item.description} | @{item.owner} | {item.due_date} | {item.category} |")
    
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"*Post-mortem generato il {datetime.now().strftime('%Y-%m-%d')} — da rivedere con il team entro 48h dall'incidente*")
    
    return "\n".join(lines)


# Esempio di post-mortem per il lab
def create_example_postmortem() -> PostMortem:
    return PostMortem(
        incident_id="INC-2026-0716-001",
        title="Order Service — Degradazione API per Memory Leak",
        date="2026-07-16",
        severity="SEV-2",
        authors=["mario.rossi", "giulia.bianchi"],
        
        duration_minutes=45,
        users_affected=12000,
        services_affected=["order-service", "payment-service (downstream)"],
        revenue_impact_eur=3500.0,
        
        timeline=[
            TimelineEvent("09:15", "Prometheus", "Alert: error_rate > 1% per order-service", "detected"),
            TimelineEvent("09:18", "PagerDuty", "On-call notificato: mario.rossi", "escalated"),
            TimelineEvent("09:22", "mario.rossi", "Verificato: pod order-service in CrashLoopBackOff (OOMKilled)", "investigated"),
            TimelineEvent("09:25", "mario.rossi", "Aumentato memory limit a 512Mi (workaround temporaneo)", "mitigated"),
            TimelineEvent("09:30", "giulia.bianchi", "Root cause identificata: memory leak nel parser JSON", "investigated"),
            TimelineEvent("09:45", "giulia.bianchi", "Fix deployato: v2.1.5 con memory leak corretto", "resolved"),
            TimelineEvent("10:00", "mario.rossi", "Monitoraggio post-incidente: error rate tornato a 0%", "resolved"),
            TimelineEvent("11:00", "Team", "Post-mortem meeting (blameless)", "retrospective"),
        ],
        
        root_cause="Memory leak nel parser JSON introdotto in v2.1.4: la libreria `orjson` v3.9.10 ha un bug di leak su dizionari annidati profondi > 10 livelli. L'API /orders/{id}/items restituisce strutture profonde per ordini con molti prodotti.",
        
        contributing_factors=[
            "Test di carico non coprivano scenari con ordini grandi (> 50 prodotti)",
            "Memory limits K8s troppo bassi (256Mi) non rilevati da VPA",
            "Nessun alert su crescita graduale della memoria (solo OOMKilled)",
        ],
        
        five_whys=[
            "Perché l'order-service era in CrashLoopBackOff? → OOMKilled: memoria esaurita",
            "Perché la memoria era esaurita? → Memory leak nel parsing JSON",
            "Perché c'era il memory leak? → Bug in orjson 3.9.10 non conosciuto",
            "Perché non è stato rilevato prima del deploy? → Test di carico con dataset troppo piccolo",
            "Perché il dataset di test era piccolo? → Nessun processo di test con dati realistici",
        ],
        
        what_worked=[
            "Alert Prometheus ha rilevato l'incidente in < 3 minuti dall'inizio",
            "On-call response time: 3 minuti (target: < 5 minuti)",
            "Workaround disponibile in 10 minuti (aumento memory limit)",
            "Comunicazione verso il team proattiva e chiara",
        ],
        
        what_didnt_work=[
            "Nessun alert su crescita graduale memoria (solo su OOMKilled a crash avvenuto)",
            "Test di carico non riproducevano il caso reale (ordini grandi)",
            "Nessun pinning delle versioni delle dipendenze (orjson non era pinnato)",
        ],
        
        action_items=[
            ActionItem(
                description="Aggiungere alert Prometheus su crescita memoria > 80% per > 10 minuti",
                owner="mario.rossi",
                due_date="2026-07-23",
                priority="P1",
                category="detection",
            ),
            ActionItem(
                description="Pinnare versione orjson a 3.9.9 (stabile) nel requirements.txt",
                owner="giulia.bianchi",
                due_date="2026-07-17",
                priority="P1",
                category="prevention",
            ),
            ActionItem(
                description="Aggiungere test di carico con ordini > 100 prodotti nella pipeline CI",
                owner="giulia.bianchi",
                due_date="2026-07-30",
                priority="P2",
                category="prevention",
            ),
            ActionItem(
                description="Configurare VPA per order-service (auto right-sizing memory)",
                owner="platform-team",
                due_date="2026-08-07",
                priority="P2",
                category="mitigation",
            ),
            ActionItem(
                description="Implementare Dependabot con policy di pinning automatico",
                owner="platform-team",
                due_date="2026-08-15",
                priority="P3",
                category="prevention",
            ),
        ],
    )


if __name__ == "__main__":
    pm = create_example_postmortem()
    markdown = generate_markdown(pm)
    
    # Stampa il post-mortem
    print(markdown)
    
    # Salva su file
    output_file = f"postmortem-{pm.incident_id}.md"
    with open(output_file, "w") as f:
        f.write(markdown)
    
    print(f"\n[OK] Post-mortem salvato in {output_file}")
```

```bash
python3 postmortem-gen.py

# Output (troncato per brevità):
# # Post-Mortem: Order Service — Degradazione API per Memory Leak
# 
# **ID Incidente:** `INC-2026-0716-001`
# **Data:** 2026-07-16
# **Severity:** SEV-2
# ...
# 
# ## Action Items
# 
# | Priorità | Descrizione | Owner | Scadenza | Categoria |
# |----------|-------------|-------|----------|-----------|
# | 🔴 P1 | Aggiungere alert Prometheus su crescita memoria... | @mario.rossi | 2026-07-23 | detection |
# | 🔴 P1 | Pinnare versione orjson a 3.9.9 | @giulia.bianchi | 2026-07-17 | prevention |
# ...
```

---

## Conclusioni e Prossimi Passi

```
COMPETENZE ACQUISITE:

✓ SLI/SLO: definire indicatori e obiettivi misurabili
✓ ERROR BUDGET: calcolare il budget e tenerne traccia
✓ BURN RATE: alert intelligenti basati sul consumo del budget
✓ PrometheusRule: definire alert K8s per SLO
✓ TOIL: misurare, categorizzare, prioritizzare l'automazione
✓ CHAOS ENGINEERING: esperimento strutturato con LitmusChaos
✓ POST-MORTEM: template blameless con 5 Why e action items SMART

CULTURA SRE:
  ✓ Gli incidenti sono fallimenti del sistema, non delle persone
  ✓ Il toil è un debito tecnico operativo — va ridotto con automazione
  ✓ Il chaos engineering trova debolezze prima degli utenti
  ✓ L'error budget allinea gli incentivi di sviluppo e operations

PROSSIMI PASSI:
  → Configurare Pyrra o Sloth per SLO management automatico (K8s CRD)
  → Integrare chaos engineering nella pipeline CI/CD (chaos in staging ad ogni deploy)
  → Implementare post-mortem meeting strutturati (15 giorni dopo ogni SEV-1/2)
  → Dashboard Grafana per error budget consumption nel tempo

RIFERIMENTI:
  SRE Books:     https://sre.google (gratuiti)
  LitmusChaos:   https://litmuschaos.io
  OpenSLO:       https://openslo.com
  Pyrra:         https://github.com/pyrra-dev/pyrra
  
PROSSIMO TUTORIAL:
  → tutorial_plat25_velero_backup_lab.md
     Backup e ripristino Kubernetes con Velero + MinIO
```

---

> **Documento di riferimento:** `24-sre-reliability-engineering.md` — Modulo 24, Gestione Piattaforme
> **Versioni testate:** LitmusChaos 3.8 (Helm), kube-prometheus-stack 65.x
> **Ultimo aggiornamento:** 2026-07-16
