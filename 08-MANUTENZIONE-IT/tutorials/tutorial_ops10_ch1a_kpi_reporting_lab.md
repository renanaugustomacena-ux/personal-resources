# Tutorial: KPI, Reporting e Capacity Planning — Guidare l'IT con i Dati

> **Documento di riferimento:** `10-pianificazione-reportistica.md`
> **Dominio:** Pianificazione e Reportistica (Dominio 10)
> **Ambito:** KPI operativi, report mensile IT, capacity planning, budget IT e roadmap tecnologica
> **Durata lab:** 8-10 ore (suddivise in 3 sessioni)
> **Livello:** Da principiante (Parte A) ad avanzato (Parte C)
> **Prerequisiti:** `tutorial_ops07_ch1a_monitoring_setup_lab.md`, `tutorial_ops07_ch1b_incident_management_lab.md`, `tutorial_ops09_ch1b_change_release_management_lab.md`
> **Ambiente:** Solo lab isolato — Grafana e Prometheus già attivi dal tutorial ops07

---

## Analogia Iniziale: Il Cruscotto della Fabbrica

Immagina una fabbrica che produce automobili. Il direttore di produzione deve sapere ogni giorno: quante auto sono state prodotte, quante fermate di linea ci sono state, quanto tempo ci ha messo ciascun reparto, e quanto costa produrre un'auto questo mese rispetto al budget.

Senza queste informazioni, gestisce "a occhio": non sa se il reparto verniciatura è più lento del solito, non sa se il consumo di materiali è oltre il previsto, non sa se la linea raggiungerà gli obiettivi mensili.

Il **KPI reporting** IT è quel cruscotto: rende visibile l'invisibile. La disponibilità dei server, il tempo di risoluzione degli incidenti, l'utilizzo della capacità — dati che esistono nei log ma che senza report non comunicano nulla a chi deve prendere decisioni.

---

## Lab Environment Setup

### Requisiti

| Componente | Minimo | Raccomandato |
|---|---|---|
| VM Ubuntu 22.04 (SRV-LINUX-01) | 2 vCPU / 4 GB RAM / 40 GB | 4 vCPU / 8 GB RAM / 80 GB |
| VM Windows Server 2022 (DC-LAB-01) | 2 vCPU / 4 GB RAM | 4 vCPU / 8 GB RAM |

### Topologia

```
┌─────────────────────────────────────────────────────────────┐
│                  Rete Lab: 192.168.56.0/24                  │
│                                                             │
│  ┌──────────────┐    ┌──────────────────────────────────┐   │
│  │  DC-LAB-01   │    │         SRV-LINUX-01             │   │
│  │192.168.56.10 │    │       192.168.56.20              │   │
│  │              │    │                                  │   │
│  │  AD/DNS      │    │ Prometheus :9090                 │   │
│  │  WinEvents   │    │ Grafana    :3000                 │   │
│  │              │    │ Node Exp.  :9100                 │   │
│  └──────────────┘    │ GLPI       :8080                 │   │
│                      └──────────────────────────────────┘   │
│                                                             │
│  Dashboard Lab: http://192.168.56.20:3000  (admin/admin)   │
│  GLPI Lab:      http://192.168.56.20:8080  (glpi/glpi)     │
└─────────────────────────────────────────────────────────────┘
```

### Verificare i Prerequisiti

```bash
# Su SRV-LINUX-01 — verificare che Prometheus e Grafana siano attivi
curl -sf http://localhost:9090/-/ready && echo "Prometheus: OK" || echo "Prometheus: NON ATTIVO"
curl -sf http://localhost:3000/api/health && echo "Grafana: OK" || echo "Grafana: NON ATTIVO"

# Se non attivi, avviarli:
sudo systemctl start prometheus
sudo systemctl start grafana-server

# Struttura directory per il lab
mkdir -p /opt/reporting/{data,reports,scripts,templates,budget}
```

---

## PART A: FONDAMENTI — Misurare quello che Conta

### Concetto A1: KPI vs Vanity Metric — La Differenza Fondamentale

**Analogia**: "Uptime 99.9%" è un KPI se attiva un'azione quando scende al 99.7%. È una vanity metric se lo pubblichi nel report e nessuno fa nulla.

La distinzione tra KPI e vanity metric:

| | KPI (Key Performance Indicator) | Vanity Metric |
|---|---|---|
| **Definizione** | Misura actionable collegata a un target | Numero che sembra buono ma non genera azione |
| **Esempio** | MTTR P1: 45 min (target < 60 min) ✅ | "Abbiamo chiuso 320 ticket questo mese" |
| **Risposta a deviazione** | Attiva un processo di miglioramento | Nessuna risposta definita |
| **Trend** | Comparato con periodi precedenti e target | Presentato in isolamento |
| **Owner** | Ha un responsabile specifico | Prodotto dall'ufficio IT, non appartiene a nessuno |

**Perché mi interessa?**
Le organizzazioni IT spesso producono report con decine di numeri. Il management li scorre e chiede "tutto bene?". La risposta è "sì" — anche quando tre incidenti critici sono stati risolti in 3 ore invece di 1. I KPI trasformano i numeri in conversazioni: "Il MTTR P1 è stato 3 ore questo mese, target è 1 ora. Ecco il piano di miglioramento."

### Concetto A2: La Struttura del Report Mensile IT

Un buon report mensile IT ha questa struttura su una singola pagina (executive summary):

```
REPORT MENSILE IT — [MESE/ANNO]
════════════════════════════════

Stato complessivo: [VERDE / GIALLO / ROSSO]

Punti salienti:
  ✅ Uptime 99.95% — sopra target (99.9%)
  ✅ MTTR P1: 45 min — entro target (< 60 min)
  ⚠️  Patch compliance: 93% — sotto target (95%)
  ❌ Backup success rate: 98.5% — sotto target (99%)

Metriche chiave:          Questo mese  Target  Trend
  Incidenti P1/P2:        6            —       ↓ (miglioramento)
  Change success rate:    94.7%        ≥95%    ↔
  SLA compliance:         98.6%        100%    ↔
  Vulnerabilità critiche: 0            0       ✅

Prossimo mese:
  - Remediation 12 workstation non patchate
  - Investigate causa fallimenti backup
  - Change firmware switch (pianificato sabato 15)
```

**Regola d'oro**: il management ha 60 secondi per leggere il tuo report. Se non vede immediatamente il semaforo e le azioni necessarie, il report è troppo lungo.

### Concetto A3: Capacity Planning — Pianificare Prima che Sia Troppo Tardi

**Analogia**: non aspetti che il serbatoio dell'auto sia a zero per fare benzina. Allo stesso modo, non aspetti che il disco sia pieno per comprare storage aggiuntivo (il lead time per hardware server è 4-12 settimane).

La metodologia in 5 fasi:

```
FASE 1: Raccolta dati storici (min 3 mesi, ideale 12)
  → Esportare metriche da Prometheus, Zabbix, ecc.
  → Calcolare media, percentile P95, valori di picco
  → Identificare pattern stagionali

FASE 2: Identificare il trend di crescita
  → Crescita lineare: +X unità/mese costante
  → Crescita esponenziale: raddoppio in N mesi
  → Crescita a gradini: eventi che causano salti

FASE 3: Proiettare le necessità future
  → Formula: Capacità futura = Attuale + (Crescita/mese × Mesi)
  → Includere piani di crescita business (nuovi utenti, nuove sedi)

FASE 4: Pianificare l'approvvigionamento
  → On-premise: ordini con 8-12 settimane di anticipo
  → Cloud: configurare auto-scaling, reserved instances

FASE 5: Revisione trimestrale
  → Confrontare previsioni con dati reali
  → Aggiustare il modello
```

**Soglie di intervento tipiche**:

| Risorsa | Soglia Attenzione | Soglia Critica | Lead time intervento |
|---|---|---|---|
| CPU (media) | > 70% | > 85% | 4-8 settimane (acquisto) |
| RAM (media) | > 75% | > 90% | 4-8 settimane (acquisto) |
| Storage | > 75% | > 85% | 4-8 settimane (acquisto) |
| Banda di rete | > 60% | > 80% | 2-12 settimane (upgrade ISP) |
| Licenze M365 | > 80% | > 95% | 1-5 giorni (acquisto online) |

### Concetto A4: Budget IT — CAPEX vs OPEX vs TCO

**Tre modi di vedere i costi IT**:

```
CAPEX (Capital Expenditure)
→ Investimenti in beni durevoli
→ Ammortamento pluriennale
→ Esempi: acquisto server, switch, storage
→ Pro: paghi una volta; Contro: esborso iniziale elevato

OPEX (Operational Expenditure)
→ Spese operative ricorrenti
→ Deduzione nell'anno corrente
→ Esempi: licenze SaaS, cloud, contratti di manutenzione
→ Pro: pagamenti distribuiti, flessibilità; Contro: costo continuo

TCO (Total Cost of Ownership)
→ Costo TOTALE nel ciclo di vita di un asset
→ CAPEX + OPEX + energia + personale + fine vita
→ Un server da EUR 14.000 può costare EUR 65.000 in 5 anni (TCO)
→ Usare il TCO per confrontare on-premise vs cloud: spesso cloud conviene
```

**Formula TCO base per 5 anni**:
```
TCO = Acquisto hardware
    + Licenze OS/software (5 anni)
    + Energia (kWh/anno × EUR/kWh × PUE × 5)
    + Spazio rack (€/anno × 5)
    + Amministrazione (h/settimana × 52 × 5 × costo/h)
    + Garanzia estesa
    + Migrazione / smaltimento
```

---

## PART B: OPERAZIONI — Costruire il Sistema di Reporting del Lab

### Esercizio B1: KPI Dashboard in Grafana

**Obiettivo.** Creare una dashboard Grafana con i KPI operativi principali del lab, usando dati reali da Prometheus e Node Exporter.

**Step 1 — Configurare Prometheus per raccogliere metriche aggiuntive**

```yaml
# Aggiungere a /etc/prometheus/prometheus.yml

global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'lab-nodes'
    static_configs:
      - targets:
          - '192.168.56.10:9100'   # DC-LAB-01
          - '192.168.56.20:9100'   # SRV-LINUX-01
          - '192.168.56.30:9100'   # WKS-LAB-01 (se node exporter installato)
        labels:
          environment: 'lab'

  - job_name: 'glpi'
    static_configs:
      - targets: ['192.168.56.20:8080']
    metrics_path: '/glpi/apirest.php/metrics'
```

```bash
# Riavviare Prometheus per applicare la configurazione
sudo systemctl reload prometheus

# Verificare che i target siano attivi
curl -s http://localhost:9090/api/v1/targets | \
    python3 -c "import sys,json; [print(t['labels']['instance'], t['health']) for t in json.load(sys.stdin)['data']['activeTargets']]"
```

**Step 2 — Creare la dashboard via Grafana API**

```python
#!/usr/bin/env python3
"""
create_kpi_dashboard.py — Crea la dashboard KPI mensile in Grafana via API.
"""

import requests
import json

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "admin"


def create_dashboard(dashboard_json: dict) -> str:
    resp = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=(GRAFANA_USER, GRAFANA_PASSWORD),
        json={"dashboard": dashboard_json, "overwrite": True, "folderId": 0},
        timeout=15
    )
    resp.raise_for_status()
    result = resp.json()
    return f"{GRAFANA_URL}{result.get('url', '')}"


def build_kpi_dashboard() -> dict:
    return {
        "title": "IT Operations — KPI Dashboard",
        "uid": "it-ops-kpi",
        "tags": ["kpi", "monthly", "it-ops"],
        "refresh": "5m",
        "panels": [
            {
                "id": 1,
                "title": "System Availability",
                "type": "stat",
                "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
                "targets": [{
                    "expr": "avg(up{job='lab-nodes'}) * 100",
                    "legendFormat": "Availability %"
                }],
                "options": {
                    "colorMode": "background",
                    "thresholds": {
                        "steps": [
                            {"value": None, "color": "red"},
                            {"value": 99.0, "color": "yellow"},
                            {"value": 99.9, "color": "green"}
                        ]
                    }
                },
                "fieldConfig": {
                    "defaults": {
                        "unit": "percent",
                        "decimals": 2
                    }
                }
            },
            {
                "id": 2,
                "title": "CPU Utilization — Average",
                "type": "gauge",
                "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
                "targets": [{
                    "expr": "avg(100 - (avg by(instance)(rate(node_cpu_seconds_total{mode='idle',job='lab-nodes'}[5m])) * 100))",
                    "legendFormat": "CPU %"
                }],
                "options": {
                    "thresholds": {
                        "steps": [
                            {"value": None, "color": "green"},
                            {"value": 70, "color": "yellow"},
                            {"value": 85, "color": "red"}
                        ]
                    }
                },
                "fieldConfig": {"defaults": {"unit": "percent", "max": 100}}
            },
            {
                "id": 3,
                "title": "Memory Utilization — Average",
                "type": "gauge",
                "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
                "targets": [{
                    "expr": "avg((1 - node_memory_MemAvailable_bytes{job='lab-nodes'} / node_memory_MemTotal_bytes{job='lab-nodes'}) * 100)",
                    "legendFormat": "RAM %"
                }],
                "fieldConfig": {"defaults": {"unit": "percent", "max": 100}}
            },
            {
                "id": 4,
                "title": "Disk Usage — Root Filesystem",
                "type": "gauge",
                "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0},
                "targets": [{
                    "expr": "avg((1 - node_filesystem_avail_bytes{job='lab-nodes',mountpoint='/'} / node_filesystem_size_bytes{job='lab-nodes',mountpoint='/'}) * 100)",
                    "legendFormat": "Disk %"
                }],
                "fieldConfig": {
                    "defaults": {"unit": "percent", "max": 100},
                    "overrides": [{
                        "matcher": {"id": "byName", "options": "Disk %"},
                        "properties": [{
                            "id": "thresholds",
                            "value": {
                                "steps": [
                                    {"value": None, "color": "green"},
                                    {"value": 75, "color": "yellow"},
                                    {"value": 85, "color": "red"}
                                ]
                            }
                        }]
                    }]
                }
            },
            {
                "id": 5,
                "title": "CPU Utilization — Trend (24h)",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
                "targets": [
                    {
                        "expr": "100 - (avg by(instance)(rate(node_cpu_seconds_total{mode='idle',job='lab-nodes'}[5m])) * 100)",
                        "legendFormat": "{{instance}}"
                    }
                ],
                "fieldConfig": {
                    "defaults": {"unit": "percent", "min": 0, "max": 100}
                }
            },
            {
                "id": 6,
                "title": "Storage Capacity Forecast (90 giorni)",
                "type": "timeseries",
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
                "targets": [
                    {
                        "expr": "node_filesystem_size_bytes{job='lab-nodes',mountpoint='/'} - node_filesystem_avail_bytes{job='lab-nodes',mountpoint='/'}",
                        "legendFormat": "Usato — {{instance}}"
                    },
                    {
                        "expr": "predict_linear(node_filesystem_avail_bytes{job='lab-nodes',mountpoint='/'}[7d], 86400*90)",
                        "legendFormat": "Previsione libero (90gg) — {{instance}}"
                    }
                ],
                "fieldConfig": {"defaults": {"unit": "bytes"}}
            },
            {
                "id": 7,
                "title": "Node Uptime",
                "type": "table",
                "gridPos": {"h": 4, "w": 24, "x": 0, "y": 12},
                "targets": [{
                    "expr": "node_time_seconds{job='lab-nodes'} - node_boot_time_seconds{job='lab-nodes'}",
                    "legendFormat": "{{instance}}",
                    "instant": True
                }],
                "fieldConfig": {
                    "defaults": {"unit": "s", "displayName": "Uptime"}
                }
            }
        ]
    }


def main() -> None:
    dashboard_url = create_dashboard(build_kpi_dashboard())
    print(f"Dashboard creata: {dashboard_url}")
    print(f"Accedere a: {GRAFANA_URL}{dashboard_url}")


if __name__ == "__main__":
    main()
```

**Step 3 — Eseguire e verificare**

```bash
# Installare dipendenze Python
pip3 install requests

# Creare la dashboard
python3 /opt/reporting/scripts/create_kpi_dashboard.py

# Aprire nel browser
echo "Dashboard: http://192.168.56.20:3000/d/it-ops-kpi"
```

**Output atteso:**
```
Dashboard creata: /d/it-ops-kpi/it-operations-kpi-dashboard
Accedere a: http://localhost:3000/d/it-ops-kpi/it-operations-kpi-dashboard
```

---

### Esercizio B2: Script di Raccolta KPI da Prometheus e GLPI

**Obiettivo.** Creare uno script Python che raccoglie tutti i KPI mensili da Prometheus e GLPI e li esporta in un formato strutturato.

```python
#!/usr/bin/env python3
"""
collect_monthly_kpis.py — Raccoglie KPI mensili da Prometheus e GLPI.
Output: JSON strutturato per generazione report.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Any

PROMETHEUS_URL = "http://localhost:9090"
GLPI_URL = "http://192.168.56.20:8080/glpi"
USER_TOKEN = "YOUR_TOKEN"
APP_TOKEN = "YOUR_APP_TOKEN"

# Definizione KPI con target
KPI_TARGETS = {
    "availability": {"target": 99.9, "direction": "higher_is_better"},
    "mttr_p1_minutes": {"target": 60.0, "direction": "lower_is_better"},
    "patch_compliance_pct": {"target": 95.0, "direction": "higher_is_better"},
    "backup_success_rate": {"target": 99.0, "direction": "higher_is_better"},
    "change_success_rate": {"target": 95.0, "direction": "higher_is_better"},
    "open_critical_vulns": {"target": 0, "direction": "lower_is_better"},
}


def query_prometheus(query: str, start: str, end: str, step: str = "1h") -> list[Any]:
    """Esegue una query PromQL su Prometheus."""
    resp = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query_range",
        params={"query": query, "start": start, "end": end, "step": step},
        timeout=30
    )
    if resp.status_code == 200:
        return resp.json().get("data", {}).get("result", [])
    return []


def query_prometheus_instant(query: str) -> float | None:
    """Esegue una query istantanea su Prometheus."""
    resp = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query",
        params={"query": query},
        timeout=15
    )
    if resp.status_code == 200:
        result = resp.json().get("data", {}).get("result", [])
        if result:
            return float(result[0]["value"][1])
    return None


def get_glpi_session_token() -> str | None:
    resp = requests.get(
        f"{GLPI_URL}/apirest.php/initSession",
        headers={"Authorization": f"user_token {USER_TOKEN}", "App-Token": APP_TOKEN},
        timeout=10
    )
    if resp.status_code == 200:
        return resp.json().get("session_token")
    return None


def get_glpi_ticket_stats(session_token: str) -> dict[str, Any]:
    """Recupera statistiche sui ticket GLPI dell'ultimo mese."""
    headers = {
        "App-Token": APP_TOKEN,
        "Session-Token": session_token,
        "Content-Type": "application/json"
    }
    resp = requests.get(
        f"{GLPI_URL}/apirest.php/Ticket",
        headers=headers,
        params={"range": "0-999"},
        timeout=15
    )
    tickets = resp.json() if isinstance(resp.json(), list) else []

    # Calcolare statistiche base
    total = len(tickets)
    by_priority = {}
    for t in tickets:
        prio = t.get("priority", 3)
        by_priority[prio] = by_priority.get(prio, 0) + 1

    return {
        "total": total,
        "by_priority": by_priority,
        "p1": by_priority.get(6, 0),  # Priority 6 = Very High in GLPI
        "p2": by_priority.get(5, 0),  # Priority 5 = High
    }


def calculate_kpi_status(value: float, kpi_name: str) -> str:
    """Determina lo stato di un KPI (ok/warning/critical)."""
    target_info = KPI_TARGETS.get(kpi_name)
    if not target_info:
        return "unknown"
    target = target_info["target"]
    direction = target_info["direction"]
    if direction == "higher_is_better":
        if value >= target:
            return "ok"
        if value >= target * 0.97:
            return "warning"
        return "critical"
    else:  # lower_is_better
        if value <= target:
            return "ok"
        if value <= target * 1.5:
            return "warning"
        return "critical"


def collect_all_kpis(month_start: datetime, month_end: datetime) -> dict[str, Any]:
    """Raccoglie tutti i KPI per il mese specificato."""
    start_ts = month_start.isoformat() + "Z"
    end_ts = month_end.isoformat() + "Z"

    kpis = {}

    # 1. Availability (da Prometheus)
    availability_data = query_prometheus(
        "avg(up{job='lab-nodes'}) * 100",
        start=start_ts, end=end_ts, step="1h"
    )
    if availability_data:
        values = [float(v[1]) for v in availability_data[0].get("values", [])]
        avg_avail = sum(values) / len(values) if values else 0.0
        kpis["availability"] = {
            "value": round(avg_avail, 3),
            "status": calculate_kpi_status(avg_avail, "availability"),
            "target": KPI_TARGETS["availability"]["target"],
            "unit": "%"
        }

    # 2. CPU utilization attuale
    cpu_now = query_prometheus_instant(
        "avg(100 - (avg by(instance)(rate(node_cpu_seconds_total{mode='idle',job='lab-nodes'}[5m])) * 100))"
    )
    if cpu_now is not None:
        kpis["cpu_utilization_current"] = {
            "value": round(cpu_now, 1),
            "status": "ok" if cpu_now < 70 else ("warning" if cpu_now < 85 else "critical"),
            "target": 70.0,
            "unit": "%"
        }

    # 3. Memory utilization
    mem_now = query_prometheus_instant(
        "avg((1 - node_memory_MemAvailable_bytes{job='lab-nodes'} / node_memory_MemTotal_bytes{job='lab-nodes'}) * 100)"
    )
    if mem_now is not None:
        kpis["memory_utilization_current"] = {
            "value": round(mem_now, 1),
            "status": "ok" if mem_now < 75 else ("warning" if mem_now < 90 else "critical"),
            "target": 75.0,
            "unit": "%"
        }

    # 4. Disk utilization
    disk_now = query_prometheus_instant(
        "avg((1 - node_filesystem_avail_bytes{job='lab-nodes',mountpoint='/'} / node_filesystem_size_bytes{job='lab-nodes',mountpoint='/'}) * 100)"
    )
    if disk_now is not None:
        kpis["disk_utilization_current"] = {
            "value": round(disk_now, 1),
            "status": "ok" if disk_now < 75 else ("warning" if disk_now < 85 else "critical"),
            "target": 75.0,
            "unit": "%"
        }

    # 5. Storage forecast (giorni a saturazione)
    forecast_avail = query_prometheus_instant(
        "predict_linear(node_filesystem_avail_bytes{job='lab-nodes',mountpoint='/'}[7d], 86400*90)"
    )
    if forecast_avail is not None:
        disk_size = query_prometheus_instant(
            "avg(node_filesystem_size_bytes{job='lab-nodes',mountpoint='/'})"
        )
        if disk_size:
            pct_at_90d = (1 - forecast_avail / disk_size) * 100
            kpis["disk_forecast_90d_pct"] = {
                "value": round(pct_at_90d, 1),
                "status": "ok" if pct_at_90d < 75 else ("warning" if pct_at_90d < 85 else "critical"),
                "description": f"Utilizzo disco previsto a 90 giorni: {pct_at_90d:.1f}%",
                "unit": "%"
            }

    # 6. Statistiche GLPI (ticket)
    session_token = get_glpi_session_token()
    if session_token:
        try:
            ticket_stats = get_glpi_ticket_stats(session_token)
            kpis["tickets_total"] = {"value": ticket_stats["total"], "unit": "count"}
            kpis["tickets_p1"] = {"value": ticket_stats["p1"], "unit": "count"}
            kpis["tickets_p2"] = {"value": ticket_stats["p2"], "unit": "count"}
        finally:
            requests.get(
                f"{GLPI_URL}/apirest.php/killSession",
                headers={"App-Token": APP_TOKEN, "Session-Token": session_token},
                timeout=5
            )

    return kpis


def print_kpi_report(kpis: dict[str, Any], month_str: str) -> None:
    status_icons = {"ok": "✅", "warning": "⚠️ ", "critical": "❌", "unknown": "❓"}

    print(f"\n{'='*60}")
    print(f"  REPORT KPI — {month_str}")
    print(f"{'='*60}\n")

    for kpi_name, data in kpis.items():
        value = data.get("value", "N/A")
        status = data.get("status", "unknown")
        target = data.get("target")
        unit = data.get("unit", "")
        icon = status_icons.get(status, "❓")
        target_str = f"(target: {target}{unit})" if target else ""
        print(f"  {icon} {kpi_name:<35} {value}{unit}  {target_str}")

    print(f"\n{'='*60}\n")


def main() -> None:
    now = datetime.utcnow()
    # Mese corrente
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_end = now

    kpis = collect_all_kpis(month_start, month_end)

    month_str = now.strftime("%B %Y")
    print_kpi_report(kpis, month_str)

    # Salvare in JSON
    output_path = f"/opt/reporting/data/kpis_{now.strftime('%Y-%m')}.json"
    with open(output_path, "w") as f:
        json.dump({"month": now.strftime("%Y-%m"), "kpis": kpis}, f, indent=2)
    print(f"KPI salvati in: {output_path}")


if __name__ == "__main__":
    main()
```

---

### Esercizio B3: Capacity Planning — Previsione Storage

**Obiettivo.** Analizzare il trend di utilizzo dello storage nel lab e calcolare quanti mesi rimangono prima di raggiungere la soglia critica (85%).

**Step 1 — Raccogliere dati storici da Prometheus**

```python
#!/usr/bin/env python3
"""
capacity_forecast.py — Analizza il trend di utilizzo risorse e prevede la saturazione.
"""

import requests
from datetime import datetime, timedelta

PROMETHEUS_URL = "http://localhost:9090"


def query_range(query: str, hours_back: int = 720) -> list:
    """Query PromQL sulle ultime N ore."""
    end = datetime.utcnow()
    start = end - timedelta(hours=hours_back)
    resp = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query_range",
        params={
            "query": query,
            "start": start.isoformat() + "Z",
            "end": end.isoformat() + "Z",
            "step": "3600"  # Un punto per ora
        },
        timeout=30
    )
    if resp.status_code == 200:
        return resp.json().get("data", {}).get("result", [])
    return []


def linear_regression(x_vals: list[float], y_vals: list[float]) -> tuple[float, float]:
    """Regressione lineare semplice. Restituisce (slope, intercept)."""
    n = len(x_vals)
    if n < 2:
        return 0.0, y_vals[0] if y_vals else 0.0
    sum_x = sum(x_vals)
    sum_y = sum(y_vals)
    sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))
    sum_x2 = sum(x ** 2 for x in x_vals)
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def forecast_resource(metric_name: str, query: str, threshold_pct: float, hours_back: int = 720) -> None:
    """Analizza il trend di utilizzo di una risorsa e prevede quando raggiungerà la soglia."""
    print(f"\n=== CAPACITY FORECAST: {metric_name} ===")

    results = query_range(query, hours_back)
    if not results:
        print("  Dati non disponibili da Prometheus")
        return

    for result in results:
        instance = result.get("metric", {}).get("instance", "unknown")
        values = result.get("values", [])
        if not values:
            continue

        # Estrarre serie temporale
        timestamps = [float(v[0]) for v in values]
        utilizations = [float(v[1]) for v in values]

        # Rimuovere valori NaN
        valid_pairs = [(t, u) for t, u in zip(timestamps, utilizations) if u == u]
        if not valid_pairs:
            continue
        ts, us = zip(*valid_pairs)

        # Normalizzare i timestamp (ore dall'inizio)
        t0 = ts[0]
        ts_hours = [(t - t0) / 3600 for t in ts]

        # Regressione lineare
        slope, intercept = linear_regression(list(ts_hours), list(us))

        # Utilizzo attuale
        current = us[-1]

        # Previsione a 30, 60, 90 giorni
        print(f"\n  Instance: {instance}")
        print(f"  Utilizzo attuale: {current:.1f}%")
        print(f"  Trend: {slope:.4f}%/ora = {slope*24:.2f}%/giorno = {slope*24*30:.1f}%/mese")
        print()

        for days in [30, 60, 90]:
            future_hours = len(ts_hours) + days * 24
            predicted = slope * future_hours + intercept
            status = "✅" if predicted < threshold_pct * 0.9 else ("⚠️ " if predicted < threshold_pct else "❌")
            print(f"  {status} Previsione a {days} giorni: {predicted:.1f}% (soglia: {threshold_pct}%)")

        # Calcolare quando raggiungerà la soglia
        if slope > 0:
            hours_to_threshold = (threshold_pct - current) / slope
            if hours_to_threshold > 0:
                days_to_threshold = hours_to_threshold / 24
                date_threshold = datetime.utcnow() + timedelta(hours=hours_to_threshold)
                print(f"\n  ⏰ Stima raggiungimento soglia {threshold_pct}%: {days_to_threshold:.0f} giorni ({date_threshold.strftime('%d/%m/%Y')})")
            else:
                print(f"\n  ❌ SOGLIA GIÀ SUPERATA: azione immediata necessaria!")
        else:
            print(f"\n  ✅ Trend stabile o in diminuzione — nessun problema a breve termine")


def main() -> None:
    print("CAPACITY PLANNING REPORT")
    print(f"Generato: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    forecast_resource(
        metric_name="Disk Usage — Root Filesystem",
        query="(1 - node_filesystem_avail_bytes{job='lab-nodes',mountpoint='/'} / node_filesystem_size_bytes{job='lab-nodes',mountpoint='/'}) * 100",
        threshold_pct=85.0,
        hours_back=720  # 30 giorni
    )

    forecast_resource(
        metric_name="RAM Utilization",
        query="(1 - node_memory_MemAvailable_bytes{job='lab-nodes'} / node_memory_MemTotal_bytes{job='lab-nodes'}) * 100",
        threshold_pct=90.0
    )

    forecast_resource(
        metric_name="CPU Utilization (P95)",
        query="avg by(instance)(rate(node_cpu_seconds_total{mode!='idle',job='lab-nodes'}[5m])) * 100",
        threshold_pct=85.0
    )


if __name__ == "__main__":
    main()
```

**Output atteso:**
```
CAPACITY PLANNING REPORT
Generato: 15/07/2026 14:30

=== CAPACITY FORECAST: Disk Usage — Root Filesystem ===

  Instance: 192.168.56.20:9100
  Utilizzo attuale: 42.3%
  Trend: 0.0008%/ora = 0.02%/giorno = 0.6%/mese

  ✅ Previsione a 30 giorni:  42.9%
  ✅ Previsione a 60 giorni:  43.5%
  ✅ Previsione a 90 giorni:  44.1%

  ⏰ Stima raggiungimento soglia 85%: 2167 giorni (14/10/2031)
```

---

### Esercizio B4: Report Mensile IT — Generazione Automatica

**Obiettivo.** Creare uno script che genera il report mensile IT in formato HTML, combinando dati da Prometheus e GLPI.

```python
#!/usr/bin/env python3
"""
generate_monthly_report.py — Genera il report mensile IT in HTML.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

REPORT_DIR = Path("/opt/reporting/reports")
DATA_DIR = Path("/opt/reporting/data")


def load_kpis(month: str) -> dict:
    """Carica i KPI dal file JSON generato da collect_monthly_kpis.py."""
    kpi_file = DATA_DIR / f"kpis_{month}.json"
    if kpi_file.exists():
        return json.loads(kpi_file.read_text())
    return {}


def status_badge(status: str) -> str:
    colors = {"ok": "#28a745", "warning": "#ffc107", "critical": "#dc3545", "unknown": "#6c757d"}
    icons = {"ok": "✅", "warning": "⚠️", "critical": "❌", "unknown": "❓"}
    color = colors.get(status, "#6c757d")
    icon = icons.get(status, "❓")
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:12px;font-size:0.85em">{icon} {status.upper()}</span>'


def overall_status(kpis: dict) -> tuple[str, str]:
    """Determina lo stato complessivo del mese."""
    statuses = [v.get("status", "unknown") for v in kpis.get("kpis", {}).values() if "status" in v]
    if "critical" in statuses:
        return "ROSSO", "#dc3545"
    if "warning" in statuses:
        return "GIALLO", "#ffc107"
    return "VERDE", "#28a745"


def generate_html_report(month: str, kpis_data: dict) -> str:
    now = datetime.now()
    kpis = kpis_data.get("kpis", {})
    overall, color = overall_status(kpis_data)

    kpi_rows = ""
    for name, data in kpis.items():
        value = data.get("value", "N/A")
        unit = data.get("unit", "")
        status = data.get("status", "unknown")
        target = data.get("target", "—")
        kpi_rows += f"""
        <tr>
            <td>{name}</td>
            <td>{value}{unit}</td>
            <td>{target}{unit}</td>
            <td>{status_badge(status)}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>Report IT Mensile — {month}</title>
<style>
body {{font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f7fa;}}
.header {{background: #1a3a5c; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;}}
.status-badge {{background: {color}; color: white; padding: 8px 20px; border-radius: 20px; font-size: 1.2em; font-weight: bold;}}
.card {{background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}}
h2 {{color: #1a3a5c; border-bottom: 2px solid #e9ecef; padding-bottom: 10px;}}
table {{width: 100%; border-collapse: collapse;}}
th {{background: #1a3a5c; color: white; padding: 10px; text-align: left;}}
td {{padding: 8px 10px; border-bottom: 1px solid #e9ecef;}}
tr:hover td {{background: #f8f9fa;}}
.footer {{text-align: center; color: #6c757d; font-size: 0.85em; margin-top: 20px;}}
</style>
</head>
<body>

<div class="header">
    <h1 style="margin:0">Report IT Mensile — {month}</h1>
    <p style="margin:5px 0">Generato: {now.strftime('%d/%m/%Y %H:%M')} | Distribuzione: CTO, IT Manager, CISO</p>
    <span class="status-badge">Stato complessivo: {overall}</span>
</div>

<div class="card">
    <h2>KPI Operativi</h2>
    <table>
        <tr>
            <th>Indicatore</th>
            <th>Valore</th>
            <th>Target</th>
            <th>Stato</th>
        </tr>
        {kpi_rows if kpi_rows else '<tr><td colspan="4">Nessun dato disponibile</td></tr>'}
    </table>
</div>

<div class="card">
    <h2>Attività Prossimo Mese</h2>
    <ul>
        <li>Revisione KPI e azioni correttive per indicatori in WARNING/CRITICAL</li>
        <li>Patch Tuesday Microsoft — pianificare finestra di manutenzione</li>
        <li>Verifica capacity forecast storage</li>
        <li>Access review account privilegiati (se trimestrale)</li>
    </ul>
</div>

<div class="footer">
    <p>Report generato automaticamente da IT Operations Lab | {now.strftime('%Y')}</p>
    <p>Dashboard live: <a href="http://192.168.56.20:3000/d/it-ops-kpi">Grafana KPI Dashboard</a></p>
</div>

</body>
</html>"""


def main() -> None:
    now = datetime.now()
    month = now.strftime("%Y-%m")
    month_display = now.strftime("%B %Y")

    # Caricare KPI
    kpis_data = load_kpis(month)

    # Generare HTML
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = REPORT_DIR / f"report_it_{month}.html"
    html = generate_html_report(month_display, kpis_data)
    output_file.write_text(html, encoding="utf-8")

    print(f"Report generato: {output_file}")
    print(f"Aprire con: firefox {output_file}")

    # Sommario a terminale
    if kpis_data.get("kpis"):
        print("\n=== SOMMARIO KPI ===")
        for name, data in kpis_data["kpis"].items():
            status = data.get("status", "?")
            value = data.get("value", "N/A")
            unit = data.get("unit", "")
            icons = {"ok": "✅", "warning": "⚠️ ", "critical": "❌"}
            icon = icons.get(status, "❓")
            print(f"  {icon} {name}: {value}{unit}")


if __name__ == "__main__":
    main()
```

---

### Esercizio B5: TCO Calculation per il Lab

**Obiettivo.** Calcolare il TCO a 5 anni per SRV-LINUX-01 e confrontarlo con un'alternativa cloud.

```python
#!/usr/bin/env python3
"""
tco_calculator.py — Calcola il Total Cost of Ownership per un server lab
e lo confronta con un'alternativa cloud.
"""

from dataclasses import dataclass, field


@dataclass
class ServerTCO:
    name: str
    hardware_cost: float = 0.0
    os_licenses: float = 0.0
    software_licenses: float = 0.0
    warranty_5yr: float = 0.0
    power_watts: float = 500.0
    electricity_price_kwh: float = 0.25
    pue: float = 1.5
    rack_space_per_year: float = 500.0
    admin_hours_per_week: float = 2.0
    admin_hourly_rate: float = 50.0
    network_per_year: float = 200.0
    monitoring_per_year: float = 300.0
    backup_per_year: float = 600.0
    migration_cost: float = 2000.0
    disposal_cost: float = 150.0
    years: int = 5

    @property
    def electricity_per_year(self) -> float:
        return self.power_watts / 1000 * 8760 * self.electricity_price_kwh * self.pue

    @property
    def admin_cost_per_year(self) -> float:
        return self.admin_hours_per_week * 52 * self.admin_hourly_rate

    @property
    def total_capex(self) -> float:
        return self.hardware_cost + self.warranty_5yr

    @property
    def total_opex_annual(self) -> float:
        return (
            self.os_licenses / self.years +
            self.software_licenses / self.years +
            self.electricity_per_year +
            self.rack_space_per_year +
            self.admin_cost_per_year +
            self.network_per_year +
            self.monitoring_per_year +
            self.backup_per_year
        )

    @property
    def total_tco(self) -> float:
        return (
            self.total_capex +
            self.total_opex_annual * self.years +
            self.migration_cost +
            self.disposal_cost
        )

    def print_breakdown(self) -> None:
        print(f"\n{'='*60}")
        print(f"  TCO {self.years} ANNI — {self.name}")
        print(f"{'='*60}")
        print(f"\n  CAPEX:")
        print(f"    Hardware:              EUR {self.hardware_cost:>8,.0f}")
        print(f"    Garanzia estesa:       EUR {self.warranty_5yr:>8,.0f}")
        print(f"    Subtotale CAPEX:       EUR {self.total_capex:>8,.0f}")
        print(f"\n  OPEX (per anno × {self.years}):")
        print(f"    Licenze OS/SW:         EUR {(self.os_licenses+self.software_licenses)/self.years:>8,.0f}/anno")
        print(f"    Energia ({self.power_watts}W, PUE {self.pue}): EUR {self.electricity_per_year:>8,.0f}/anno")
        print(f"    Spazio rack:           EUR {self.rack_space_per_year:>8,.0f}/anno")
        print(f"    Amministrazione:       EUR {self.admin_cost_per_year:>8,.0f}/anno")
        print(f"    Rete:                  EUR {self.network_per_year:>8,.0f}/anno")
        print(f"    Monitoring:            EUR {self.monitoring_per_year:>8,.0f}/anno")
        print(f"    Backup:                EUR {self.backup_per_year:>8,.0f}/anno")
        print(f"    Subtotale OPEX/anno:   EUR {self.total_opex_annual:>8,.0f}/anno")
        print(f"\n  Fine vita:")
        print(f"    Migrazione:            EUR {self.migration_cost:>8,.0f}")
        print(f"    Smaltimento RAEE:      EUR {self.disposal_cost:>8,.0f}")
        print(f"\n{'─'*60}")
        print(f"  TCO TOTALE {self.years} ANNI:    EUR {self.total_tco:>8,.0f}")
        print(f"  TCO ANNUALE:             EUR {self.total_tco/self.years:>8,.0f}/anno")
        print(f"  TCO MENSILE:             EUR {self.total_tco/self.years/12:>8,.0f}/mese")
        print(f"{'='*60}")


@dataclass
class CloudTCO:
    name: str
    monthly_vm_cost: float = 0.0       # Reserved Instance 3 anni
    admin_hours_per_week: float = 1.0  # Meno admin in cloud
    admin_hourly_rate: float = 50.0
    backup_per_year: float = 2400.0 / 5
    networking_per_year: float = 1800.0 / 5  # egress costs
    years: int = 5

    @property
    def vm_cost_total(self) -> float:
        return self.monthly_vm_cost * 12 * self.years

    @property
    def admin_cost_total(self) -> float:
        return self.admin_hours_per_week * 52 * self.admin_hourly_rate * self.years

    @property
    def total_tco(self) -> float:
        return (
            self.vm_cost_total +
            self.admin_cost_total +
            self.backup_per_year * self.years +
            self.networking_per_year * self.years
        )

    def print_breakdown(self) -> None:
        print(f"\n{'='*60}")
        print(f"  TCO {self.years} ANNI — {self.name}")
        print(f"{'='*60}")
        print(f"\n  Costo VM (RI 3y):      EUR {self.monthly_vm_cost:>8,.0f}/mese × {self.years*12}m = EUR {self.vm_cost_total:>8,.0f}")
        print(f"  Amministrazione:       EUR {self.admin_cost_total:>8,.0f}")
        print(f"  Backup:                EUR {self.backup_per_year*self.years:>8,.0f}")
        print(f"  Networking (egress):   EUR {self.networking_per_year*self.years:>8,.0f}")
        print(f"\n{'─'*60}")
        print(f"  TCO TOTALE {self.years} ANNI:    EUR {self.total_tco:>8,.0f}")
        print(f"  TCO ANNUALE:             EUR {self.total_tco/self.years:>8,.0f}/anno")
        print(f"  TCO MENSILE:             EUR {self.total_tco/self.years/12:>8,.0f}/mese")
        print(f"{'='*60}")


def main() -> None:
    # TCO On-Premise — SRV-LINUX-01 (simulazione lab)
    onprem = ServerTCO(
        name="On-Premise Server (Ubuntu 22.04)",
        hardware_cost=8_000.0,    # Server di classe entry-level
        os_licenses=0.0,          # Ubuntu gratuito
        software_licenses=2_000.0,
        warranty_5yr=2_000.0,
        power_watts=200.0,        # Server lab piccolo
        electricity_price_kwh=0.25,
        pue=1.5,
        rack_space_per_year=300.0,
        admin_hours_per_week=1.0,
        admin_hourly_rate=50.0,
        network_per_year=100.0,
        monitoring_per_year=200.0,
        backup_per_year=400.0,
        migration_cost=500.0,
        disposal_cost=100.0,
        years=5
    )
    onprem.print_breakdown()

    # TCO Cloud — equivalente Azure VM (Standard_B2s)
    cloud = CloudTCO(
        name="Cloud VM (Azure Standard_B2s, RI 3y)",
        monthly_vm_cost=35.0,     # Standard_B2s Reserved 3 anni ~$35/mese
        admin_hours_per_week=0.5,
        admin_hourly_rate=50.0,
        backup_per_year=480.0,
        networking_per_year=360.0,
        years=5
    )
    cloud.print_breakdown()

    # Confronto
    savings = onprem.total_tco - cloud.total_tco
    savings_pct = savings / onprem.total_tco * 100

    print(f"\n{'='*60}")
    print(f"  CONFRONTO")
    print(f"{'='*60}")
    print(f"  On-Premise TCO:  EUR {onprem.total_tco:>8,.0f}")
    print(f"  Cloud TCO:       EUR {cloud.total_tco:>8,.0f}")
    if savings > 0:
        print(f"  Risparmio cloud: EUR {savings:>8,.0f} ({savings_pct:.1f}%)")
    else:
        print(f"  Costo extra cloud: EUR {-savings:>8,.0f} ({-savings_pct:.1f}% più caro)")
    print(f"\n  RACCOMANDAZIONE:")
    if savings > 5000:
        print(f"  ✅ Cloud conveniente — valutare migrazione")
    elif savings > 0:
        print(f"  ⚠️  Cloud marginalmente conveniente — valutare altri fattori (latenza, compliance)")
    else:
        print(f"  🏠 On-premise conveniente per questo workload")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
```

---

## PART C: SISTEMATIZZARE — Automazione e Governance del Reporting

### Progetto C1: Pipeline di Reporting Automatizzata (Cron)

**Obiettivo.** Configurare una pipeline che esegue automaticamente la raccolta KPI e la generazione del report ogni primo del mese.

```bash
cat > /opt/reporting/scripts/monthly_pipeline.sh << 'SCRIPT'
#!/bin/bash
# monthly_pipeline.sh — Pipeline completa di reporting mensile
# Eseguire il primo giorno lavorativo di ogni mese

MONTH=$(date +"%Y-%m")
LOG_FILE="/var/log/reporting/monthly-${MONTH}.log"
REPORT_EMAIL="it-manager@lab.local"

mkdir -p "$(dirname $LOG_FILE)"
exec >> "$LOG_FILE" 2>&1

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"; }

log "=== AVVIO PIPELINE REPORT MENSILE ${MONTH} ==="

# 1. Raccogliere KPI
log "FASE 1: Raccolta KPI da Prometheus e GLPI"
python3 /opt/reporting/scripts/collect_monthly_kpis.py
if [ $? -ne 0 ]; then
    log "[ERRORE] Raccolta KPI fallita"
    exit 1
fi
log "KPI raccolta: OK"

# 2. Analisi capacity
log "FASE 2: Analisi capacity forecast"
python3 /opt/reporting/scripts/capacity_forecast.py > /opt/reporting/data/capacity-${MONTH}.txt
log "Capacity forecast: OK"

# 3. Generare report HTML
log "FASE 3: Generazione report HTML"
python3 /opt/reporting/scripts/generate_monthly_report.py
if [ $? -ne 0 ]; then
    log "[ERRORE] Generazione report fallita"
    exit 1
fi
log "Report generato: OK"

# 4. Verificare file output
REPORT_FILE="/opt/reporting/reports/report_it_${MONTH}.html"
if [ -f "$REPORT_FILE" ]; then
    SIZE=$(du -h "$REPORT_FILE" | awk '{print $1}')
    log "Report salvato: $REPORT_FILE ($SIZE)"
else
    log "[ERRORE] File report non trovato"
    exit 1
fi

# 5. Notifica (simulazione — in produzione inviare email)
log "FASE 4: Notifica agli stakeholder"
echo "Il report IT mensile ${MONTH} è disponibile: $REPORT_FILE" | \
    mail -s "Report IT Mensile — ${MONTH}" "$REPORT_EMAIL" 2>/dev/null || \
    log "[INFO] Email non inviata (configurare mail in produzione)"

log "=== PIPELINE COMPLETATA ==="
SCRIPT

chmod +x /opt/reporting/scripts/monthly_pipeline.sh

# Configurare cron per esecuzione automatica
# (primo giorno lavorativo alle 07:00 — approssimazione: primo del mese)
(crontab -l 2>/dev/null; echo "0 7 1 * * /opt/reporting/scripts/monthly_pipeline.sh") | crontab -
echo "Cron configurato: ogni primo del mese alle 07:00"
crontab -l
```

### Progetto C2: Alert Automatici su KPI — Regole Prometheus

**Obiettivo.** Configurare regole di alerting Prometheus che avvisano quando un KPI supera la soglia critica.

```yaml
# /etc/prometheus/rules/kpi_alerts.yml
groups:
  - name: kpi_alerts
    interval: 5m
    rules:

      # Disponibilità sotto 99.9%
      - alert: LowAvailability
        expr: avg(up{job="lab-nodes"}) * 100 < 99.9
        for: 5m
        labels:
          severity: warning
          category: availability
        annotations:
          summary: "Disponibilità sotto il target"
          description: "Disponibilità attuale: {{ $value | printf \"%.2f\" }}% (target: 99.9%)"

      # CPU sopra 70% (warning) e 85% (critical)
      - alert: HighCPUWarning
        expr: avg(100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle",job="lab-nodes"}[5m])) * 100)) > 70
        for: 15m
        labels:
          severity: warning
          category: capacity
        annotations:
          summary: "CPU sopra soglia warning"
          description: "CPU media: {{ $value | printf \"%.1f\" }}% — soglia warning 70%"

      - alert: HighCPUCritical
        expr: avg(100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle",job="lab-nodes"}[5m])) * 100)) > 85
        for: 5m
        labels:
          severity: critical
          category: capacity
        annotations:
          summary: "CPU sopra soglia critica"
          description: "CPU media: {{ $value | printf \"%.1f\" }}% — soglia critica 85%"

      # Disco sopra 75% (warning) e 85% (critical)
      - alert: HighDiskWarning
        expr: avg((1 - node_filesystem_avail_bytes{job="lab-nodes",mountpoint="/"} / node_filesystem_size_bytes{job="lab-nodes",mountpoint="/"}) * 100) > 75
        for: 30m
        labels:
          severity: warning
          category: capacity
        annotations:
          summary: "Utilizzo disco sopra soglia warning"
          description: "Disco medio: {{ $value | printf \"%.1f\" }}% — soglia 75%"

      - alert: DiskForecastCritical
        expr: predict_linear(node_filesystem_avail_bytes{job="lab-nodes",mountpoint="/"}[7d], 86400*30) < 0
        for: 1h
        labels:
          severity: critical
          category: capacity
        annotations:
          summary: "Disco si esaurirà entro 30 giorni"
          description: "La previsione lineare indica saturazione entro 30 giorni su {{ $labels.instance }}"

      # RAM sopra 90%
      - alert: HighMemoryCritical
        expr: avg((1 - node_memory_MemAvailable_bytes{job="lab-nodes"} / node_memory_MemTotal_bytes{job="lab-nodes"}) * 100) > 90
        for: 10m
        labels:
          severity: critical
          category: capacity
        annotations:
          summary: "RAM sopra soglia critica"
          description: "RAM media: {{ $value | printf \"%.1f\" }}% — soglia 90%"
```

```bash
# Applicare le regole
sudo cp /etc/prometheus/rules/kpi_alerts.yml /etc/prometheus/rules/
sudo systemctl reload prometheus

# Verificare che le regole siano caricate
curl -s http://localhost:9090/api/v1/rules | python3 -c "
import sys, json
data = json.load(sys.stdin)
for group in data['data']['groups']:
    for rule in group['rules']:
        print(f\"{rule['name']}: {rule.get('state', 'ok')}\")
"
```

### Progetto C3: Roadmap Tecnologica Lab 3 Anni

**Obiettivo.** Creare la roadmap tecnologica del lab per i prossimi 3 anni, in formato markdown strutturato con il metodo GAP Analysis + Effort/Impact matrix.

```bash
cat > /opt/reporting/templates/roadmap_tecnologica.md << 'EOF'
# Roadmap Tecnologica IT — Lab 2026-2028

**Preparato da**: Lab Admin
**Data**: 2026-07-15
**Revisione**: Annuale (prossima: 2027-07-15)

---

## Stato Attuale (As-Is)

| Area | Stato Attuale | Punteggio Maturità (1-5) |
|---|---|---|
| Monitoring | Prometheus + Grafana base | 3 |
| Backup | Restic automatizzato | 3 |
| Automazione | Script bash manuali | 2 |
| Sicurezza | Firewall base, fail2ban | 2 |
| ITSM/CMDB | GLPI operativo | 3 |
| Documentazione | Wiki.js + Gitea | 3 |
| Cloud | Nessuna integrazione | 1 |

## Stato Target (To-Be) — 2028

| Area | Stato Target | Punteggio Maturità Target |
|---|---|---|
| Monitoring | Full observability (metriche + log + trace) | 5 |
| Backup | 3-2-1 con cloud, RTO < 4h testato | 5 |
| Automazione | Ansible + Terraform, IaC completo | 4 |
| Sicurezza | Zero Trust, EDR, SIEM | 4 |
| ITSM/CMDB | GLPI full ITIL 4, self-service portal | 4 |
| Documentazione | Versionata, auto-aggiornata, searchable | 4 |
| Cloud | Ibrido (30% cloud, Azure integrato) | 4 |

## GAP Analysis

| Area | Gap | Priorità |
|---|---|---|
| Monitoring | Manca log centralizzato (Loki) e tracing | MEDIO |
| Backup | Manca destinazione cloud, RTO non testato | ALTO |
| Automazione | Configuration Management non implementato | ALTO |
| Sicurezza | EDR e SIEM assenti | ALTO |
| Cloud | Nessuna integrazione | MEDIO |

## Matrice Effort vs Impact

```
                IMPATTO
          Basso      Alto
        ┌──────────┬──────────┐
Basso   │          │ QUICK    │ ← Ansible base, log Loki,
EFFORT  │          │ WINS     │   backup cloud script
        ├──────────┼──────────┤
Alto    │  EVITARE │ PROGETTO │ ← Zero Trust, SIEM,
EFFORT  │          │STRATEGICO│   cloud migration
        └──────────┴──────────┘
```

## ANNO 1 (2026): Stabilizzazione

### Q3 2026
- [ ] Implementare Loki per log centralizzato
- [ ] Configurare backup verso cloud (restic + Backblaze B2)
- [ ] Deploy Ansible per configuration management base
- [ ] Test DR completo: RTO misurato e documentato

### Q4 2026
- [ ] EDR base (Wazuh open source)
- [ ] Automatizzare onboarding/offboarding utenti (PowerShell + Ansible)
- [ ] Self-service portal per richieste comuni (GLPI catalogo servizi)

**KPI target fine anno:**
- Disponibilità: ≥ 99.9%
- RTO testato: < 4h
- Patch compliance: ≥ 95%

## ANNO 2 (2027): Automazione e Cloud Ibrido

### Q1-Q2 2027
- [ ] Valutazione workload per cloud migration
- [ ] Connettività Azure (VPN site-to-site lab → Azure)
- [ ] Azure AD Connect (identità ibrida)
- [ ] Migrazione backup secondario su Azure Blob

### Q3-Q4 2027
- [ ] SIEM base (Wazuh + Elastic)
- [ ] Terraform per IaC (infrastruttura cloud)
- [ ] Auto-scaling per workload variabili
- [ ] Knowledge base self-service (Wiki + AI search)

## ANNO 3 (2028): Maturità Operativa

### Q1-Q2 2028
- [ ] Zero Trust access per accessi remoti
- [ ] Osservabilità completa (metriche + log + trace)
- [ ] Capacity planning automatizzato (ML-based)

### Q3-Q4 2028
- [ ] Revisione completa roadmap
- [ ] Certificazione ISO 27001 (se applicabile)
- [ ] Nuova roadmap 2029-2031

---

*Revisione annuale obbligatoria: ogni luglio*
*Owner: Lab Admin | Approvazione: IT Manager*
EOF

echo "Roadmap tecnologica creata: /opt/reporting/templates/roadmap_tecnologica.md"
```

---

## Checklist di Validazione Lab

**Parte A — Fondamenti:**
- [ ] A1: Distinguere KPI da vanity metric su 5 esempi proposti
- [ ] A2: Riconoscere la struttura del report mensile (stato complessivo, sezioni, azioni)
- [ ] A3: Calcolare manualmente i mesi a saturazione dato: capacità 100 GB, usato 70 GB, crescita 1.3 GB/mese
- [ ] A4: Calcolare il TCO annuale di un server da EUR 10.000 con energia 300W, 0.25 EUR/kWh, PUE 1.4, 2h admin/settimana

**Parte B — Esercizi:**
- [ ] B1: Dashboard Grafana "IT Operations — KPI" visibile a http://192.168.56.20:3000
- [ ] B1: Tutti i panel mostrano dati reali (non "No data")
- [ ] B2: Script `collect_monthly_kpis.py` eseguito con output JSON
- [ ] B2: File `/opt/reporting/data/kpis_YYYY-MM.json` creato
- [ ] B3: Script `capacity_forecast.py` mostra previsione storage con data stima saturazione
- [ ] B4: Report HTML generato in `/opt/reporting/reports/`
- [ ] B4: Report apribile in browser con stato complessivo visibile
- [ ] B5: TCO calculator mostra breakdown completo per server lab
- [ ] B5: Confronto on-premise vs cloud con raccomandazione

**Parte C — Sistematizzazione:**
- [ ] C1: `monthly_pipeline.sh` eseguito manualmente senza errori
- [ ] C1: Cron configurato (verificare con `crontab -l`)
- [ ] C2: File `kpi_alerts.yml` creato e caricato in Prometheus
- [ ] C2: Alert visibili in Prometheus UI → Alerts
- [ ] C3: Roadmap tecnologica 3 anni salvata e strutturata

---

## Appendice A: Tabella KPI Completa con Target

| KPI | Formula | Target | Frequenza | Owner |
|---|---|---|---|---|
| **Availability** | (Totale - Downtime) / Totale × 100 | ≥ 99.9% | Mensile | Ops Manager |
| **MTTR P1** | Somma tempi risoluzione / N incidenti P1 | < 60 min | Mensile | Incident Manager |
| **MTTR P2** | Somma tempi risoluzione / N incidenti P2 | < 4h | Mensile | Incident Manager |
| **MTTA P1** | Somma tempi acknowledgement / N incidenti P1 | < 5 min | Mensile | On-call team |
| **Patch Compliance** | Host patchati SLA / Host totali × 100 | ≥ 95% | Mensile | Security team |
| **Backup Success Rate** | Backup riusciti / Backup totali × 100 | ≥ 99% | Settimanale | Backup admin |
| **Change Success Rate** | Change riusciti / Change totali × 100 | ≥ 95% | Mensile | Change Manager |
| **Emergency Change Ratio** | Emergency change / Change totali × 100 | ≤ 5% | Mensile | Change Manager |
| **Vulnerabilità Critiche** | N vulnerabilità CVSS ≥ 9.0 aperte | 0 | Settimanale | Security team |
| **SLA Compliance** | Servizi entro SLA / Servizi totali × 100 | 100% | Mensile | Service Manager |
| **CSAT** | Media punteggi soddisfazione su ticket chiusi | ≥ 4.0/5.0 | Mensile | Service Desk |
| **CPU Utilization** | Media utilizzo CPU (P95) | < 70% | Continuativo | Infra team |
| **Storage Utilization** | Spazio usato / Totale × 100 | < 75% | Continuativo | Infra team |
| **License Utilization** | Licenze in uso / Licenze acquistate × 100 | 80-95% | Mensile | IT Manager |

---

## Appendice B: Template Report Mensile (1 Pagina)

```
REPORT MENSILE IT — [MESE ANNO]
══════════════════════════════
Stato complessivo:    [VERDE / GIALLO / ROSSO]
Preparato da:         [Nome]
Data:                 [GG/MM/AAAA]

PUNTI SALIENTI:
  ✅ [Risultato positivo 1]
  ✅ [Risultato positivo 2]
  ⚠️  [Criticità con azione in corso]

METRICHE CHIAVE:
  Uptime:                [XX.XX]%    target 99.9%    [status]
  Incidenti P1+P2:       [N]         trend [↑↓↔]
  Change success rate:   [XX.X]%     target 95%      [status]
  Patch compliance:      [XX.X]%     target 95%      [status]
  Backup success:        [XX.X]%     target 99%      [status]
  Vulnerabilità critiche: [N]        target 0        [status]

CAPACITY (trend):
  CPU:     [XX]% (trend [+X%/mese]) → [OK/ATTENZIONE/CRITICO]
  RAM:     [XX]% (trend [+X%/mese]) → [OK/ATTENZIONE/CRITICO]
  Storage: [XX]% (stimata sat. in [N] mesi)

AZIONI PROSSIMO MESE:
  [ ] [Azione 1 — owner — scadenza]
  [ ] [Azione 2 — owner — scadenza]
══════════════════════════════
```

---

## Appendice C: Integrazione ITIL 4

| Pratica ITIL 4 | Relazione con KPI Reporting |
|---|---|
| **Continual Improvement** | I KPI identificano le aree di miglioramento; il ciclo PDCA (Plan-Do-Check-Act) usa i KPI per misurare il progresso |
| **Monitoring and Event Management** | Le regole Prometheus alert sono la fonte primaria dei dati di disponibilità e capacity |
| **Service Level Management** | I KPI di availability, MTTR e MTTA sono direttamente collegati agli SLA definiti |
| **Capacity and Performance Management** | Il capacity forecast è il cuore della pratica; alimenta le decisioni di investimento |
| **Financial Management for IT** | Il TCO e il budget tracking collegano le decisioni tecniche ai costi reali |
| **Change Enablement** | Il Change Success Rate e l'Emergency Change Ratio misurano la maturità del processo di change |

---

## Riferimenti

- `10-pianificazione-reportistica.md` — Documento sorgente completo
- `tutorial_ops07_ch1a_monitoring_setup_lab.md` — Setup Prometheus e Grafana (prerequisito)
- `tutorial_ops09_ch1b_change_release_management_lab.md` — KPI change management
- ITIL 4 Foundation: Capacity and Performance Management Practice
- Prometheus Documentation: alerting rules, PromQL
- Grafana Documentation: dashboard JSON model
