# Tutorial: SLO, SLI e Error Budget — Hands-On Lab

> **Documento di riferimento:** `22-slo-sli-quantificazione.md`
> **Dominio:** Operations Advanced
> **Ambito:** SLI, SLO, SLA, error budget, multi-burn-rate alerting, Prometheus recording rules
> **Durata lab:** 8-10 ore (suddivise in sessioni da 2-3 ore)
> **Livello:** Da intermedio (Parte A-B) ad avanzato (Parte C)
> **Prerequisiti:** `tutorial_ops07_ch1a_monitoring_setup_lab.md` (Prometheus/Grafana), `tutorial_ops10_ch1a_kpi_reporting_lab.md` (KPI)
> **Ambiente:** Solo lab isolato — mai su sistemi di produzione

---

## Lab Environment Setup

### Requisiti Hardware

| Componente | Minimo | Raccomandato |
|---|---|---|
| RAM host | 6 GB | 12 GB |
| CPU host | 4 core | 6 core |
| Storage | 20 GB liberi | 40 GB liberi |

### VM necessarie

```
Lab SLO/SLI
===========
VM1  Ubuntu 22.04 — Prometheus + Alertmanager + Grafana
     IP: 192.168.56.10
     RAM: 3 GB, 2 vCPU

VM2  Ubuntu 22.04 — Applicazione web simulata (Node Exporter + Python http server)
     IP: 192.168.56.11
     RAM: 2 GB, 2 vCPU

HOST  Windows/Linux — Browser, VS Code, terminali
```

### Struttura directory lab

```bash
# Su VM1
mkdir -p ~/slo_lab/{rules,dashboards,policies,scripts}
cd ~/slo_lab
```

### Installazione Alertmanager (se non già presente)

```bash
# Su VM1
wget https://github.com/prometheus/alertmanager/releases/download/v0.27.0/alertmanager-0.27.0.linux-amd64.tar.gz
tar -xzf alertmanager-0.27.0.linux-amd64.tar.gz
sudo cp alertmanager-0.27.0.linux-amd64/alertmanager /usr/local/bin/
sudo cp alertmanager-0.27.0.linux-amd64/amtool /usr/local/bin/

# Crea servizio systemd
sudo tee /etc/systemd/system/alertmanager.service <<'EOF'
[Unit]
Description=Prometheus Alertmanager
After=network.target

[Service]
User=prometheus
ExecStart=/usr/local/bin/alertmanager \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/var/lib/alertmanager
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo mkdir -p /etc/alertmanager /var/lib/alertmanager
sudo systemctl daemon-reload && sudo systemctl enable alertmanager
```

### Simulatore di traffico HTTP per il lab

```python
# scripts/traffic_simulator.py
# Genera traffico HTTP simulato con error rate controllabile

import http.server
import threading
import time
import random
import requests

ERROR_RATE = 0.005  # 0.5% errori (entro SLO 99.9%)
PORT = 8080

class SimulatedHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if random.random() < ERROR_RATE:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'Internal Server Error')
        else:
            latency_ms = random.gauss(80, 30)  # media 80ms
            time.sleep(max(0, latency_ms / 1000))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')

    def log_message(self, format, *args):
        pass  # silenzio nel lab

if __name__ == '__main__':
    server = http.server.HTTPServer(('0.0.0.0', PORT), SimulatedHandler)
    print(f"Simulatore avviato su :{PORT} (error_rate={ERROR_RATE*100:.1f}%)")
    server.serve_forever()
```

```bash
# Avvia simulatore su VM2
python3 scripts/traffic_simulator.py &

# Genera traffico continuo (su VM1, 100 req/s)
while true; do
    for i in $(seq 1 10); do
        curl -s http://192.168.56.11:8080/ > /dev/null &
    done
    sleep 0.1
done &
```

---

## PART A: FONDAMENTI — Capire il Perché e il Cosa

### Concetto A1: SLI, SLO, SLA — Tre Cose Diverse

**Analogia.** Sei un ristorante stellato. Il **SLI** è il tempo reale che i clienti aspettano per il primo piatto (lo misuri con un cronometro). Il **SLO** è l'obiettivo che ti sei dato: "il 99% dei tavoli non aspetta più di 20 minuti" (standard interno). Il **SLA** è quello che hai promesso al wedding planner nel contratto: "garantisco che il 98% aspetterà meno di 25 minuti, altrimenti sconto del 15%". Tre cose diverse, gerarchicamente legate.

**La distinzione precisa:**

```
SLI = COSA MISURO
      "9.987% delle richieste rispondono in < 300ms questa settimana"
         ↓
SLO = QUANTO BENE DEVO ESSERE (obiettivo interno)
      "La latenza sotto 300ms deve essere ≥ 99.9% su finestra rolling 30 giorni"
         ↓
SLA = COSA HO PROMESSO AL CLIENTE (contratto legale)
      "Garantiamo ≥ 99.5% di richieste sotto 500ms. Violazione → credito 25%"
```

**Regola d'oro:**

```
SLA target < SLO target < 100%

Esempio:
  SLA = 99.5%  (promesso al cliente)
  SLO = 99.9%  (obiettivo interno — buffer 0.4%)
  
Il buffer (0.4%) ti dà il tempo di reagire prima che scattino le penalità.
```

**Confronto tabellare:**

| Aspetto | SLI | SLO | SLA |
|---|---|---|---|
| Natura | Misurazione | Obiettivo interno | Contratto legale |
| Se violato | Segnale diagnostico | Attiva error budget policy | Attiva penalità/crediti |
| Chi lo definisce | SRE/Ops | SRE + Product | Sales + Legal + SRE |
| Chi lo monitora | Team interno | Team interno | Anche il cliente |
| Modifica | Facile | Media | Rinegoziazione |

---

### Concetto A2: Le Categorie di SLI

**Analogia.** Per misurare la qualità di un servizio postale, puoi misurare: se il pacco arriva (disponibilità), quando arriva (latenza), se arriva intatto (correttezza), se la tracciatura è aggiornata (freshness). Ogni servizio IT ha categorie di SLI analoghe.

**Le 6 categorie di SLI:**

| Categoria | Formula | Esempio | Quando usarlo |
|---|---|---|---|
| **Disponibilità** | richieste_buone / totali | Risponde a richieste valide | Quasi sempre — base di ogni SLO |
| **Latenza** | richieste_veloci / totali | Risponde entro 300ms | App interattive, API |
| **Error Rate** | errori / totali | < 0.1% 5xx | Spesso complemento a disponibilità |
| **Throughput** | operazioni/secondo | ≥ 100 tps | Batch, pipeline, stream |
| **Freshness** | dati_aggiornati / totali | Aggiornato entro 60s | Dashboard, cache, repliche |
| **Durabilità** | oggetti_leggibili / scritti | 0 oggetti persi | Storage, backup, database |

**Dove misurare — impatta cosa stai misurando:**

```
Utente → CDN → Load Balancer → App Server → Database
  ↑         ↑         ↑             ↑           ↑
(ideale)  (buono)  (accept.)    (server)   (backend)

Misurare al server → non vedi latenza rete cliente
Misurare al LB → non vedi errori interni all'app
Misurare al client → rumoroso, ma più vicino alla realtà
```

**Regola pratica:** misura il più vicino possibile all'utente. Se non puoi, usa synthetic monitoring (probe ogni 60s da location esterne).

---

### Concetto A3: Le "Nines" — Quanto Costa Ogni Nine

**Analogia.** Mettere i paracaduti di sicurezza su un aereo (99%) costa poco. Aggiungere il terzo sistema di sicurezza (99.9%) costa molto di più. Il quarto (99.99%) richiede ridondanza totale e ingegneri dedicati. Ogni "nove" di affidabilità ha un costo esponenzialmente crescente.

**Tabella "nines" — costo e downtime:**

| Target | Downtime/mese | Downtime/anno | Costo relativo | Infrastruttura tipica |
|---|---|---|---|---|
| 99% (2 nines) | 7.2 ore | 3.65 giorni | 1x | Singola VM, no HA |
| 99.9% (3 nines) | 43.8 min | 8.76 ore | ~10x | Multi-AZ, LB, auto-scaling |
| 99.99% (4 nines) | 4.38 min | 52.6 min | ~100x | Multi-region, chaos engineering |
| 99.999% (5 nines) | 26.3 sec | 5.26 min | ~1000x | Active-active multi-DC |

**Perché NON puntare al 100%?**
1. Matematicamente impossibile (teorema CAP, FLP impossibility)
2. Economicamente irrazionale: ogni nine in più → costi 10x
3. Operativamente controproducente: se punti al 100%, ogni deploy è un rischio e la velocità di rilascio crolla

---

### Concetto A4: Error Budget — L'Inaffidabilità Come Risorsa

**Analogia.** Hai un budget mensile per le spese straordinarie: €500. Se spendi €400 nelle prime due settimane, devi rallentare. Se arrivi a €0, stop totale. L'error budget funziona esattamente così: è la quota di "malfunzionamento tollerato" che puoi consumare prima di dover fermare i deploy.

**Calcolo error budget:**

```
Error Budget = 1 - SLO target

SLO = 99.9%
Error Budget = 0.1% per mese (30 giorni)
             = 0.001 × 30 × 24 × 60 = 43.2 minuti di downtime/mese
             = 0.001 × 30 × 86400 = 2.592 secondi/mese
             = 0.001 × volume_richieste (se 1M req/giorno → 30.000 errori/mese)
```

**Burn rate — velocità di consumo:**

```
Burn rate = tasso_errore_attuale / tasso_errore_SLO_consentito

SLO 99.9% su 30gg → 0.1% / 720 ore = 0.000139% errori/ora consentiti

Se il tasso attuale è 0.002% errori/ora:
Burn rate = 0.002% / 0.000139% = 14.4x
```

**Significato del burn rate:**

| Burn rate | Tempo per esaurire budget | Azione |
|---|---|---|
| 0.5x | 60 giorni | Servizio più affidabile del SLO — ok |
| 1x | 30 giorni | Consumo normale |
| 6x | 5 giorni | Azione urgente in giornata |
| 14.4x | ~50 ore | Page immediato, servizio in difficoltà |
| 36x | 20 ore | Outage significativo in corso |
| 720x | 1 ora | Servizio completamente down |

---

### Concetto A5: Multi-Burn-Rate Alerting — La Soluzione Google SRE

**Il problema degli alert tradizionali:**

```
"Alert se error rate > 1%"
→ Uno spike di 30 secondi all'2% scatena un page per niente

"Alert se error rate > 0.1% nell'ora scorsa"
→ Se il servizio è completamente down, aspetti 1 ora?
```

**La soluzione: alert multi-finestra, multi-burn-rate.**

Alert scatta SOLO quando DUE finestre concordano:
- **Finestra corta**: verifica che il problema sia ATTUALE
- **Finestra lunga**: verifica che sia SIGNIFICATIVO (non uno spike breve)

**Le 4 regole standard Google SRE (SLO 99.9% su 30gg):**

| Severity | Burn rate | Finestra corta | Finestra lunga | Consumo budget |
|---|---|---|---|---|
| 🔴 CRITICAL (page) | 14.4x | 5 min | 1 ora | 2% in 1h |
| 🔴 CRITICAL (page) | 6x | 30 min | 6 ore | 5% in 6h |
| 🟡 WARNING (ticket) | 3x | 2 ore | 1 giorno | 10% in 24h |
| 🟡 WARNING (ticket) | 1x | 6 ore | 3 giorni | 10% in 72h |

**Come si derivano i burn rate:**

```
burn_rate = (budget_consumato% / 100) × finestra_SLO_ore / finestra_alert_ore

14.4x: consume 2% budget in 1h → 0.02 × 720 / 1 = 14.4
6x:    consume 5% budget in 6h → 0.05 × 720 / 6 = 6.0
3x:    consume 10% in 1g        → 0.10 × 720 / 24 = 3.0
1x:    consume 10% in 3g        → 0.10 × 720 / 72 = 1.0
```

---

## PART B: OPERAZIONI — Costruire e Configurare

### Esercizio B1: Calcolo SLI e SLO — Python

**Obiettivo.** Calcolare SLI, error budget e burn rate a partire da dati di log simulati.

```python
# scripts/b1_slo_calculator.py

from dataclasses import dataclass

@dataclass
class SLOConfig:
    name: str
    sli_type: str           # availability / latency / error_rate
    window_days: int = 30
    target_pct: float = 99.9

    @property
    def error_budget_pct(self) -> float:
        return 100 - self.target_pct

    @property
    def error_budget_minutes(self) -> float:
        return (self.error_budget_pct / 100) * self.window_days * 24 * 60

    @property
    def error_budget_ratio(self) -> float:
        return 1 - self.target_pct / 100

    def burn_rate(self, actual_error_rate: float) -> float:
        """Burn rate dato il tasso errore attuale (0-1)."""
        return actual_error_rate / self.error_budget_ratio

    def budget_consumed_pct(self, actual_error_rate: float, hours_elapsed: float) -> float:
        """Quanto budget è stato consumato (0-100%)."""
        return (actual_error_rate / self.error_budget_ratio) * (hours_elapsed / (self.window_days * 24)) * 100

    def print_status(self, actual_error_rate: float, hours_elapsed: float = 720):
        current_sli = (1 - actual_error_rate) * 100
        br = self.burn_rate(actual_error_rate)
        consumed = self.budget_consumed_pct(actual_error_rate, hours_elapsed)
        remaining = 100 - consumed

        status_icon = "✅" if remaining > 50 else ("🟡" if remaining > 10 else "🔴")

        print(f"\n=== SLO: {self.name} ===")
        print(f"  Target:          {self.target_pct:.3f}%")
        print(f"  SLI attuale:     {current_sli:.4f}%")
        print(f"  Error rate:      {actual_error_rate*100:.4f}%")
        print(f"  Error budget:    {self.error_budget_pct:.3f}% = {self.error_budget_minutes:.1f} min/mese")
        print(f"  Burn rate:       {br:.1f}x", end="")
        if br > 14.4:
            print("  ← PAGE (14.4x+)")
        elif br > 6:
            print("  ← PAGE (6x+)")
        elif br > 3:
            print("  ← Ticket (3x+)")
        elif br > 1:
            print("  ← Ticket (1x+)")
        else:
            print("  ← OK")
        print(f"  Budget rimasto:  {remaining:.1f}%  {status_icon}")

# SLO comuni
slo_availability = SLOConfig("API Availability", "availability", target_pct=99.9)
slo_latency      = SLOConfig("API Latency p99 < 300ms", "latency", target_pct=99.9)

# Scenario 1: servizio in buona salute
print("Scenario 1: Servizio in buona salute (0.05% errori)")
slo_availability.print_status(actual_error_rate=0.0005, hours_elapsed=360)  # 15 giorni
slo_latency.print_status(actual_error_rate=0.0008, hours_elapsed=360)

# Scenario 2: degradazione moderata
print("\n\nScenario 2: Degradazione moderata (0.5% errori)")
slo_availability.print_status(actual_error_rate=0.005, hours_elapsed=200)

# Scenario 3: outage grave
print("\n\nScenario 3: Outage grave (15% errori)")
slo_availability.print_status(actual_error_rate=0.15, hours_elapsed=2)
```

**Output atteso (scenario 3):**

```
Scenario 3: Outage grave (15% errori)

=== SLO: API Availability ===
  Target:          99.900%
  SLI attuale:     85.0000%
  Error rate:      15.0000%
  Error budget:    0.100% = 43.2 min/mese
  Burn rate:       150.0x  ← PAGE (14.4x+)
  Budget rimasto:  -5.6%  🔴
```

---

### Esercizio B2: SLO Compositi — Catena di Dipendenze

**Obiettivo.** Calcolare l'SLO effettivo di un sistema con dipendenze multiple.

```python
# scripts/b2_composite_slo.py

def composite_slo(*slo_pcts: float) -> float:
    """SLO composito: prodotto degli SLO individuali."""
    result = 1.0
    for s in slo_pcts:
        result *= s / 100
    return result * 100

def print_dependency_chain(services: list[dict]):
    """Analizza una catena di servizi e calcola l'SLO composito."""
    slo_values = [s['slo'] for s in services]
    composite = composite_slo(*slo_values)

    print("=== Catena di dipendenze SLO ===")
    for s in services:
        print(f"  {s['name']:<30} SLO: {s['slo']:.3f}%")
    print(f"  {'─'*45}")
    print(f"  {'SLO COMPOSITO':<30} SLO: {composite:.4f}%")
    print(f"  {'Error budget composito':<30}      {100 - composite:.4f}%")

    # Downtime composito su 30 giorni
    downtime_min = (1 - composite / 100) * 30 * 24 * 60
    print(f"  {'Downtime budget/mese':<30}      {downtime_min:.1f} minuti")

    print(f"\nInsegnamento: ogni dipendenza ABBASSA l'SLO raggiungibile.")
    print(f"Con {len(services)} servizi a 99.9%, il composito è {composite:.4f}% — non 99.9%!")

# Scenario 1: microservizi tipici
print_dependency_chain([
    {"name": "API Gateway",          "slo": 99.9},
    {"name": "Auth Service",         "slo": 99.9},
    {"name": "Business Logic API",   "slo": 99.9},
    {"name": "Database",             "slo": 99.95},
    {"name": "Cache (Redis)",        "slo": 99.99},
])

# Scenario 2: architettura semplice
print("\n")
print_dependency_chain([
    {"name": "Web Server",           "slo": 99.9},
    {"name": "Database",             "slo": 99.95},
])
```

---

### Esercizio B3: Prometheus Recording Rules — SLI Base

**Obiettivo.** Configurare le recording rules Prometheus per calcolare SLI su finestre multiple.

```yaml
# rules/slo-recording-rules.yaml
groups:
  - name: slo_sli_recording
    interval: 30s
    rules:
      # === Tasso di errore su finestre multiple ===
      - record: slo:http_error_rate:rate5m
        expr: |
          sum(rate(http_requests_total{job="lab-app", code=~"5.."}[5m]))
          /
          sum(rate(http_requests_total{job="lab-app"}[5m]))

      - record: slo:http_error_rate:rate30m
        expr: |
          sum(rate(http_requests_total{job="lab-app", code=~"5.."}[30m]))
          /
          sum(rate(http_requests_total{job="lab-app"}[30m]))

      - record: slo:http_error_rate:rate1h
        expr: |
          sum(rate(http_requests_total{job="lab-app", code=~"5.."}[1h]))
          /
          sum(rate(http_requests_total{job="lab-app"}[1h]))

      - record: slo:http_error_rate:rate6h
        expr: |
          sum(rate(http_requests_total{job="lab-app", code=~"5.."}[6h]))
          /
          sum(rate(http_requests_total{job="lab-app"}[6h]))

      - record: slo:http_error_rate:rate2h
        expr: |
          sum(rate(http_requests_total{job="lab-app", code=~"5.."}[2h]))
          /
          sum(rate(http_requests_total{job="lab-app"}[2h]))

      - record: slo:http_error_rate:rate1d
        expr: |
          sum(rate(http_requests_total{job="lab-app", code=~"5.."}[1d]))
          /
          sum(rate(http_requests_total{job="lab-app"}[1d]))

      - record: slo:http_error_rate:rate3d
        expr: |
          sum(rate(http_requests_total{job="lab-app", code=~"5.."}[3d]))
          /
          sum(rate(http_requests_total{job="lab-app"}[3d]))

      # === SLI latenza (proporzione richieste sotto 300ms) ===
      - record: slo:http_latency_good:rate5m
        expr: |
          sum(rate(http_request_duration_seconds_bucket{
            job="lab-app", le="0.3"
          }[5m]))
          /
          sum(rate(http_request_duration_seconds_count{job="lab-app"}[5m]))

      - record: slo:http_latency_good:rate1h
        expr: |
          sum(rate(http_request_duration_seconds_bucket{
            job="lab-app", le="0.3"
          }[1h]))
          /
          sum(rate(http_request_duration_seconds_count{job="lab-app"}[1h]))

      - record: slo:http_latency_good:rate6h
        expr: |
          sum(rate(http_request_duration_seconds_bucket{
            job="lab-app", le="0.3"
          }[6h]))
          /
          sum(rate(http_request_duration_seconds_count{job="lab-app"}[6h]))

      # === Error budget rimanente (SLO 99.9%) ===
      - record: slo:error_budget_remaining:ratio
        expr: |
          1 - (
            sum(rate(http_requests_total{job="lab-app", code=~"5.."}[30d]))
            /
            sum(rate(http_requests_total{job="lab-app"}[30d]))
          )
          /
          (1 - 0.999)
        labels:
          slo: "lab-app-availability-99.9"
```

```bash
# Installa le regole
sudo mkdir -p /etc/prometheus/rules
sudo cp rules/slo-recording-rules.yaml /etc/prometheus/rules/

# Aggiungi al prometheus.yml
sudo tee -a /etc/prometheus/prometheus.yml <<'EOF'
rule_files:
  - /etc/prometheus/rules/*.yaml
EOF

# Valida
promtool check rules /etc/prometheus/rules/slo-recording-rules.yaml
# Atteso: SUCCESS

# Ricarica
sudo systemctl reload prometheus
```

---

### Esercizio B4: Alert Rules Multi-Burn-Rate

**Obiettivo.** Configurare le 4 regole di alerting multi-burn-rate Google SRE.

```yaml
# rules/slo-alert-rules.yaml
groups:
  - name: slo_availability_multiburn
    rules:
      # ─── CRITICAL PAGE: 14.4x burn rate (5m + 1h) ───
      # Consuma 2% del budget in 1 ora → outage rapido, page immediato
      - alert: SLOBurnRateCritical
        expr: |
          slo:http_error_rate:rate5m > (14.4 * 0.001)
          and
          slo:http_error_rate:rate1h > (14.4 * 0.001)
        for: 2m
        labels:
          severity: critical
          slo: lab-app-availability
          burn_rate: "14.4x"
        annotations:
          summary: "SLO availability CRITICO: burn rate 14.4x"
          description: >-
            lab-app sta consumando l'error budget a 14.4x.
            Budget esaurito in ~50 ore.
            Error rate (5m): {{ $value | humanizePercentage }}.
            Azione: page on-call, aprire bridge call.

      # ─── CRITICAL PAGE: 6x burn rate (30m + 6h) ───
      # Consuma 5% budget in 6 ore → degradazione significativa
      - alert: SLOBurnRateHigh
        expr: |
          slo:http_error_rate:rate30m > (6 * 0.001)
          and
          slo:http_error_rate:rate6h > (6 * 0.001)
        for: 5m
        labels:
          severity: critical
          slo: lab-app-availability
          burn_rate: "6x"
        annotations:
          summary: "SLO availability ALTO: burn rate 6x"
          description: >-
            lab-app sta consumando l'error budget a 6x.
            Budget esaurito in ~5 giorni a questo ritmo.
            Azione: page on-call, indagine approfondita.

      # ─── WARNING TICKET: 3x burn rate (2h + 1d) ───
      # Consuma 10% budget in 1 giorno → problema lento ma reale
      - alert: SLOBurnRateMedium
        expr: |
          slo:http_error_rate:rate2h > (3 * 0.001)
          and
          slo:http_error_rate:rate1d > (3 * 0.001)
        for: 15m
        labels:
          severity: warning
          slo: lab-app-availability
          burn_rate: "3x"
        annotations:
          summary: "SLO availability MODERATO: burn rate 3x"
          description: >-
            lab-app sta consumando l'error budget a 3x.
            Budget esaurito in ~10 giorni.
            Azione: aprire ticket, investigare entro 4 ore.

      # ─── WARNING TICKET: 1x burn rate (6h + 3d) ───
      # Consumo uniforme → budget non durerà il mese
      - alert: SLOBurnRateSlow
        expr: |
          slo:http_error_rate:rate6h > (1 * 0.001)
          and
          slo:http_error_rate:rate3d > (1 * 0.001)
        for: 30m
        labels:
          severity: warning
          slo: lab-app-availability
          burn_rate: "1x"
        annotations:
          summary: "SLO availability SOSTENUTO: burn rate 1x"
          description: >-
            lab-app sta consumando error budget a 1x sostenuto.
            Il budget si esaurirà prima della fine della finestra SLO.
            Azione: ticket a bassa urgenza, analisi trend.

  - name: slo_error_budget
    rules:
      # Budget sotto 25% → livello orange della policy
      - alert: SLOErrorBudgetLow
        expr: slo:error_budget_remaining:ratio < 0.25
        for: 5m
        labels:
          severity: warning
          slo: lab-app-availability
        annotations:
          summary: "Error budget sotto 25%"
          description: >-
            Rimane {{ $value | humanizePercentage }} dell'error budget.
            Attivare error budget policy livello ORANGE:
            feature freeze, ogni deploy richiede approvazione SRE.

      # Budget esaurito → SLO violato
      - alert: SLOErrorBudgetExhausted
        expr: slo:error_budget_remaining:ratio < 0
        for: 1m
        labels:
          severity: critical
          slo: lab-app-availability
        annotations:
          summary: "ERROR BUDGET ESAURITO — SLO VIOLATO"
          description: >-
            L'error budget è esaurito. SLO 99.9% violato.
            AZIONE OBBLIGATORIA: deploy freeze totale,
            post-mortem entro 48 ore, review architetturale.
```

```bash
# Installa e valida
sudo cp rules/slo-alert-rules.yaml /etc/prometheus/rules/
promtool check rules /etc/prometheus/rules/slo-alert-rules.yaml
sudo systemctl reload prometheus

# Verifica che le regole siano caricate
curl -s http://localhost:9090/api/v1/rules | python3 -m json.tool | grep '"name"'
```

---

### Esercizio B5: Error Budget Policy

**Obiettivo.** Creare una error budget policy formale con soglie e azioni.

```yaml
# policies/error-budget-policy.yaml
service: lab-app
slo_target: 99.9%
window: 30d_rolling
owner: team-ops-lab

thresholds:
  - level: green
    budget_remaining: ">50%"
    actions:
      - "Operazioni normali"
      - "Deploy consentiti senza restrizioni"
      - "Chaos testing consentito (ambiente staging)"

  - level: yellow
    budget_remaining: "25%-50%"
    actions:
      - "Review obbligatoria pre-deploy (checklist CI)"
      - "No chaos testing in produzione"
      - "Post-mortem per ogni incidente che consuma >5% budget"

  - level: orange
    budget_remaining: "10%-25%"
    actions:
      - "Feature freeze: solo bug fix e reliability work"
      - "Ogni deploy richiede approvazione SRE + Tech Lead"
      - "Rollback automatico se error rate > 0.5% post-deploy"
      - "Standup giornaliero sulla reliability"
      - "Comunicazione proattiva al cliente se SLA a rischio"

  - level: red
    budget_remaining: "<10%"
    actions:
      - "Deploy freeze totale (solo hotfix critici)"
      - "Tutto il team su reliability work"
      - "Escalation a IT Manager"
      - "Incident review per ogni errore in produzione"

  - level: exhausted
    budget_remaining: "0% (SLO violato)"
    actions:
      - "Deploy freeze fino al ripristino del budget"
      - "Post-mortem obbligatorio entro 48 ore"
      - "Action items completati prima di riprendere feature work"
      - "Review architetturale se SLO violato 2 mesi consecutivi"
      - "Se SLA violato: processo di incident report per il cliente"

escalation_path:
  - "Ops Team Lead"
  - "IT Manager"
  - "CTO (solo se SLA violato)"

review_cadence: "Settimanale durante ops standup, mensile review completa"
```

```python
# scripts/b5_budget_policy_checker.py
# Controlla lo stato del budget e determina il livello di policy

import yaml

def check_policy_level(budget_remaining_pct: float, policy_file: str = 'policies/error-budget-policy.yaml') -> dict:
    """Determina il livello di policy basato sul budget rimanente."""
    with open(policy_file, 'r') as f:
        policy = yaml.safe_load(f)
    
    levels = {
        'green':     (50, float('inf')),
        'yellow':    (25, 50),
        'orange':    (10, 25),
        'red':       (0, 10),
        'exhausted': (float('-inf'), 0),
    }
    
    for threshold in policy['thresholds']:
        level = threshold['level']
        lo, hi = levels[level]
        if lo < budget_remaining_pct <= hi or (level == 'exhausted' and budget_remaining_pct <= 0):
            return {
                'level':   level,
                'actions': threshold['actions'],
                'budget':  budget_remaining_pct,
            }
    
    return {'level': 'unknown', 'actions': [], 'budget': budget_remaining_pct}

# Test scenari
for budget in [75, 35, 18, 5, -2]:
    status = check_policy_level(budget)
    icons  = {'green': '🟢', 'yellow': '🟡', 'orange': '🟠', 'red': '🔴', 'exhausted': '⛔'}
    icon   = icons.get(status['level'], '❓')
    print(f"\n{icon} Budget {budget:.0f}% → Livello: {status['level'].upper()}")
    for action in status['actions'][:2]:  # prime 2 azioni
        print(f"   • {action}")
```

---

### Esercizio B6: SLA Design — Dal SLO al Contratto

**Obiettivo.** Progettare un documento SLA a partire dagli SLO interni.

```python
# scripts/b6_sla_designer.py

def design_sla(
    slo_target_pct: float,
    margin_pct: float = 0.4,
    quota_monthly_eur: float = 10000,
) -> dict:
    """Progetta struttura SLA dato un SLO interno."""
    
    sla_target = slo_target_pct - margin_pct
    sla_target = round(sla_target, 2)
    
    # Calcola soglie penalità
    penalty_tiers = [
        {'from': sla_target - 0.5, 'to': sla_target, 'credit_pct': 10},
        {'from': sla_target - 4,   'to': sla_target - 0.5, 'credit_pct': 25},
        {'from': 0,                'to': sla_target - 4,   'credit_pct': 50},
    ]
    
    # Calcola costo per minuto eccedente (modello alternativo)
    budget_minutes = (1 - sla_target / 100) * 30 * 24 * 60
    cost_per_excess_min = quota_monthly_eur / budget_minutes if budget_minutes > 0 else 0
    
    print(f"=== SLA Design ===")
    print(f"  SLO interno:      {slo_target_pct:.3f}%")
    print(f"  Margine buffer:   {margin_pct:.2f}%")
    print(f"  SLA promesso:     {sla_target:.2f}%")
    print(f"\n  Downtime budget SLA:  {budget_minutes:.1f} min/mese ({budget_minutes/60:.1f} ore)")
    print(f"  Downtime budget SLO:  {(1-slo_target_pct/100)*30*24*60:.1f} min/mese")
    print(f"\n=== Struttura Penalità ===")
    print(f"  Quota mensile:     €{quota_monthly_eur:,.0f}")
    print(f"  Cap penalità:      €{quota_monthly_eur*0.50:,.0f} (50% quota)")
    print(f"\n  {'Disponibilità':>25}  {'Credito':<10}  {'Importo massimo'}")
    for t in penalty_tiers:
        credit = t['credit_pct']
        amount = quota_monthly_eur * credit / 100
        print(f"  {t['to']:.2f}% - {t['from']:.2f}%            {credit}%          €{amount:,.0f}")
    
    print(f"\n  Costo per minuto eccedente: €{cost_per_excess_min:.2f}/min")
    
    return {'sla': sla_target, 'budget_min': budget_minutes, 'tiers': penalty_tiers}

# Design SLA per API gateway 99.9% SLO
design_sla(slo_target_pct=99.9, margin_pct=0.4, quota_monthly_eur=10000)
```

---

### Esercizio B7: Dashboard Grafana SLO

**Obiettivo.** Creare una dashboard Grafana per visualizzare SLO, burn rate e budget.

```python
# scripts/b7_slo_grafana_dashboard.py
import requests
import json

GRAFANA_URL  = 'http://192.168.56.10:3000'
GRAFANA_USER = 'admin'
GRAFANA_PASS = 'admin'

SLO_TARGET = 0.999  # 99.9%
ERROR_BUDGET = 1 - SLO_TARGET

dashboard = {
    "title": "SLO / SLI / Error Budget",
    "uid":   "slo-dashboard-01",
    "panels": [
        {
            "title":   "SLI Availability (30d)",
            "type":    "stat",
            "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
            "targets": [{
                "expr": f"(1 - (sum(rate(http_requests_total{{job='lab-app', code=~'5..'}}[30d])) / sum(rate(http_requests_total{{job='lab-app'}}[30d])))) * 100",
                "legendFormat": "SLI %"
            }],
            "fieldConfig": {
                "defaults": {
                    "unit": "percent",
                    "thresholds": {"steps": [
                        {"color": "red",    "value": 0},
                        {"color": "yellow", "value": 99.5},
                        {"color": "green",  "value": SLO_TARGET * 100},
                    ]},
                }
            },
        },
        {
            "title":   "Error Budget Rimanente",
            "type":    "gauge",
            "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
            "targets": [{
                "expr": "slo:error_budget_remaining:ratio * 100",
                "legendFormat": "Budget %"
            }],
            "fieldConfig": {
                "defaults": {
                    "unit": "percent",
                    "min": 0, "max": 100,
                    "thresholds": {"steps": [
                        {"color": "red",    "value": 0},
                        {"color": "orange", "value": 10},
                        {"color": "yellow", "value": 25},
                        {"color": "green",  "value": 50},
                    ]},
                }
            },
        },
        {
            "title":   "Burn Rate (5m window)",
            "type":    "timeseries",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
            "targets": [
                {"expr": f"slo:http_error_rate:rate5m / {ERROR_BUDGET}", "legendFormat": "Burn rate (5m)"},
                {"expr": "14.4", "legendFormat": "PAGE threshold (14.4x)"},
                {"expr": "6",    "legendFormat": "PAGE threshold (6x)"},
                {"expr": "3",    "legendFormat": "Ticket threshold (3x)"},
            ],
        },
    ],
    "schemaVersion": 38,
    "version": 1,
    "refresh": "30s",
    "time": {"from": "now-3h", "to": "now"},
}

try:
    resp = requests.post(
        f"{GRAFANA_URL}/api/dashboards/db",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        json={"dashboard": dashboard, "overwrite": True, "folderId": 0},
        timeout=10,
    )
    resp.raise_for_status()
    url = resp.json().get('url', '')
    print(f"✅ Dashboard SLO creata: {GRAFANA_URL}{url}")
except Exception as e:
    print(f"⚠️  Errore Grafana: {e}")
    print("Struttura dashboard verificata — salva il JSON e importa manualmente")
```

---

## PART C: SISTEMATIZZARE — Dall'Esecuzione alla Governance

### Progetto C1: SLO Review Meeting — Template e Processo

```markdown
<!-- reports/SLO_review_template.md -->
# SLO Review — [MESE ANNO]

## Error Budget Summary

| SLO | Target | SLI mese | Budget Consumato | Status |
|---|---|---|---|---|
| API Availability | 99.9% | __._____% | ___% | 🟢/🟡/🟠/🔴 |
| API Latency p99 | 99.9% | __._____% | ___% | 🟢/🟡/🟠/🔴 |

## Incidenti del mese

| Data | Durata | Impatto | Budget Consumato | RCA completata? |
|---|---|---|---|---|
| | | | | |

## Trend

Budget consumato ultimi 3 mesi: [M-2]: ___% | [M-1]: ___% | [M]: ___%
Trend: 📈 Peggioramento / 📉 Miglioramento / ➡️ Stabile

## Decisioni

- [ ] Proseguire feature development (budget > 50%)
- [ ] Freeze feature non critiche (budget < 25%)
- [ ] Revisione architettura (SLO violato 2 mesi)
- [ ] Aggiornamento target SLO (storico diverge > 20%)

## Action items

| # | Azione | Owner | Deadline | Status |
|---|---|---|---|---|
| | | | | |
```

---

### Progetto C2: Script Mensile di SLO Review

```python
# scripts/c2_monthly_slo_review.py
# Script per raccogliere dati SLO e generare report mensile automatico

import requests
from datetime import datetime, date

PROMETHEUS_URL = 'http://192.168.56.10:9090'
SLO_TARGET     = 99.9

def query(expr: str) -> float | None:
    try:
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/query",
                           params={"query": expr}, timeout=10)
        resp.raise_for_status()
        results = resp.json()['data']['result']
        return float(results[0]['value'][1]) if results else None
    except Exception:
        return None

# SLI 30 giorni
sli_30d = query("""
    (1 - (
        sum(rate(http_requests_total{job="lab-app", code=~"5.."}[30d]))
        /
        sum(rate(http_requests_total{job="lab-app"}[30d]))
    )) * 100
""")

# Error budget rimanente
budget_remaining = query("slo:error_budget_remaining:ratio * 100")

# Burn rate corrente (5m)
burn_rate = query(f"slo:http_error_rate:rate5m / (1 - {SLO_TARGET/100})")

sli_val     = sli_30d if sli_30d is not None else 0
budget_val  = budget_remaining if budget_remaining is not None else 0
br_val      = burn_rate if burn_rate is not None else 0

consumed    = 100 - budget_val
slo_status  = "✅ SLO RISPETTATO" if sli_val >= SLO_TARGET else "❌ SLO VIOLATO"
budget_icon = "🟢" if budget_val > 50 else ("🟡" if budget_val > 25 else ("🟠" if budget_val > 10 else "🔴"))

report = f"""# SLO Monthly Review — {date.today().strftime('%B %Y')}
Generato: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Risultati

| Metrica | Valore |
|---|---|
| SLO Target | {SLO_TARGET:.3f}% |
| SLI 30 giorni | {sli_val:.4f}% |
| Stato SLO | {slo_status} |
| Error Budget Rimanente | {budget_val:.1f}% {budget_icon} |
| Budget Consumato | {consumed:.1f}% |
| Burn Rate attuale | {br_val:.2f}x |

## Policy Level

{budget_icon} {'GREEN — operazioni normali' if budget_val > 50
    else 'YELLOW — review pre-deploy' if budget_val > 25
    else 'ORANGE — feature freeze' if budget_val > 10
    else 'RED — deploy freeze' if budget_val > 0
    else 'EXHAUSTED — SLO VIOLATO'}

---
*Prossima revisione: prima settimana del mese successivo*
"""

report_file = f"reports/slo_review_{date.today().strftime('%Y-%m')}.md"
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(report)
print(report)
print(f"\n📄 Report: {report_file}")
```

---

## Checklist di Validazione Lab

- [ ] **A1**: Distinzione SLI/SLO/SLA formulata con esempio concreto e regola "SLA < SLO < 100%"
- [ ] **A2**: 6 categorie SLI elencate, punto di misura corretto scelto per il lab
- [ ] **A3**: Tabella "nines" compresa, motivazione per non puntare al 100% articolata
- [ ] **A4**: Calcolo error budget corretto per SLO 99.9% (43.2 min/mese)
- [ ] **A5**: 4 regole multi-burn-rate derivate matematicamente, comprensione del "doppio-finestra"
- [ ] **B1**: Script Python calcola correttamente burn rate e stato budget per 3 scenari
- [ ] **B2**: SLO composito 5 servizi calcolato (risultato ~99.65%)
- [ ] **B3**: Recording rules installate e validate con promtool
- [ ] **B4**: Alert rules 4 livelli (14.4x, 6x, 3x, 1x) installate e validate
- [ ] **B5**: Error budget policy con 5 livelli (green → exhausted) creata
- [ ] **B6**: SLA a 99.5% progettato da SLO 99.9% con struttura penalità
- [ ] **B7**: Dashboard Grafana SLO con stat + gauge + burn rate timeseries
- [ ] **C1**: Template SLO review mensile strutturato e pronto all'uso
- [ ] **C2**: Script review mensile genera report con dati Prometheus reali (o mock se non disponibili)

---

## Appendice A: Formula Quick Reference

```
SLI  = eventi_buoni / eventi_totali × 100%
SLO  = SLI ≥ target% per finestra rolling
SLA  = SLO_target - margine (tipicamente 0.2-0.5%)

Error Budget = (1 - SLO) × window
Burn Rate    = error_rate_attuale / error_budget_ratio
Policy Level: >50% green | 25-50% yellow | 10-25% orange | <10% red | 0% exhausted

Multi-burn-rate (SLO 99.9%, finestra 30gg):
  14.4x = 2% in 1h    → PAGE (5m + 1h)
  6x    = 5% in 6h    → PAGE (30m + 6h)
  3x    = 10% in 1g   → Ticket (2h + 1d)
  1x    = 10% in 3g   → Ticket (6h + 3d)
```

---

## Appendice B: Matrice SLI per Tipo di Servizio

| Tipo servizio | SLI primari | SLI secondari |
|---|---|---|
| API REST/gRPC | Availability, Latency (p99) | Error rate, Throughput |
| Web frontend | Availability, Latency (LCP) | Error rate JS |
| Database | Availability, Latency (query p99) | Durability, Replication lag |
| Message queue | Availability, Freshness (lag) | Throughput, Error rate |
| Pipeline batch | Freshness, Correctness | Throughput, Durability |
| Storage | Availability, Durability | Latency, Throughput |
| Autenticazione | Availability, Latency | Error rate |

---

## Appendice C: Mappatura ITIL 4

| Pratica ITIL 4 | Collegamento a SLO/SLI |
|---|---|
| Service Level Management | SLA verso cliente, SLO interni, reporting mensile |
| Monitoring and Event Management | SLI = base per tutti gli alert |
| Incident Management | Outage impatta direttamente error budget |
| Problem Management | SLO degradati cronici → problem records |
| Continual Improvement | Review mensile SLO = loop di miglioramento |

---

## Riferimenti

1. Beyer, B. et al. — *Site Reliability Engineering* (Google, 2016) — Cap. 3, 4, 5
2. Murphy, N. et al. — *The Site Reliability Workbook* (Google, 2018) — Multi-burn-rate alerting
3. Sloss, B. et al. — *Implementing Service Level Objectives* (O'Reilly, 2020)
4. Prometheus — Recording rules documentation, Alertmanager configuration
5. Grafana Labs — SLO/Error budget panel documentation
6. ITIL 4 — *Service Level Management Practice Guide* (Axelos, 2020)
