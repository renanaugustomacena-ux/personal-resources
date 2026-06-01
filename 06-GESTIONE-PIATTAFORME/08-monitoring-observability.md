---
corso: "Gestione Piattaforme e DevOps"
fase: "4 — Osservabilità e Networking"
modulo: 8
titolo: "Monitoring e Observability"
versione: "OpenTelemetry 1.x / Prometheus 2.54 / Grafana 11"
livello: "Avanzato"
prerequisiti: ["05-kubernetes", "06-docker-avanzato", "07-ci-cd"]
obiettivi:
  - "Implementare i tre pilastri dell'osservabilità: metriche, log e trace distribuiti"
  - "Configurare OpenTelemetry Collector come hub centralizzato con OTLP"
  - "Costruire dashboard Grafana efficaci con metodologie RED e USE"
  - "Progettare alerting multi-livello con Prometheus, Alertmanager e runbook automatici"
  - "Definire policy di retention e sampling per gestire costi e volumi di dati"
tag: [monitoring, observability, opentelemetry, prometheus, grafana, jaeger, alerting, red-use]
---

# Monitoring e Observability — Documentazione Completa

> **Modulo 08** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Implementare i tre pilastri dell'osservabilità: metriche, log e trace distribuiti
> 2. Configurare OpenTelemetry Collector come hub centralizzato con OTLP
> 3. Costruire dashboard Grafana efficaci con metodologie RED e USE
> 4. Progettare alerting multi-livello con Prometheus, Alertmanager e runbook automatici
> 5. Definire policy di retention e sampling per gestire costi e volumi di dati
>
> **Prerequisiti:** [Kubernetes](05-kubernetes.md) · [Docker Avanzato](06-docker-avanzato.md) · [CI/CD](07-ci-cd.md)
> **Tempo stimato:** 8-10 ore · **Livello:** Avanzato

## Idee guida

1. **OTel Collector centralizza ingestion.** Vendor-swap senza re-instrumentation.
2. **OTLP HTTP/gRPC standard transport.** Drop in replacement Jaeger native + Prometheus pull.
3. **Exemplars: link metric → trace.** Prometheus 2.30+ supporta.
4. **RED + USE methodologie.** Rate/Errors/Duration per service; Utilization/Saturation/Errors per resource.


## Indice

1. [Panoramica e Principi Fondamentali](#1-panoramica-e-principi-fondamentali)
2. [Prometheus](#2-prometheus)
3. [Grafana](#3-grafana)
4. [ELK Stack (Elasticsearch, Logstash, Kibana)](#4-elk-stack-elasticsearch-logstash-kibana)
5. [Loki](#5-loki)
6. [Distributed Tracing — Jaeger e OpenTelemetry](#6-distributed-tracing--jaeger-e-opentelemetry)
7. [APM (Application Performance Monitoring)](#7-apm-application-performance-monitoring)
8. [Alerting Strategies](#8-alerting-strategies)
9. [Monitoring Infrastructure](#9-monitoring-infrastructure)
10. [Observability in Kubernetes](#10-observability-in-kubernetes)
11. [Best Practices](#11-best-practices)
12. [Deep-Dive sui Tre Pilastri](#12-deep-dive-sui-tre-pilastri)
13. [OpenTelemetry Collector — Architettura Avanzata](#13-opentelemetry-collector--architettura-avanzata)
14. [Prometheus Avanzato — Federation e Long-Term Storage](#14-prometheus-avanzato--federation-e-long-term-storage)
15. [Ecosistema Grafana — LGTM Stack](#15-ecosistema-grafana--lgtm-stack)
16. [Implementazione SLI/SLO/SLA](#16-implementazione-slislosla)
17. [Distributed Tracing — Pattern Avanzati](#17-distributed-tracing--pattern-avanzati)
18. [Confronto Soluzioni di Log Aggregation](#18-confronto-soluzioni-di-log-aggregation)
19. [AIOps e Anomaly Detection](#19-aiops-e-anomaly-detection)
20. [Observability as Code — Approccio Completo](#20-observability-as-code--approccio-completo)

---

## 1. Panoramica e Principi Fondamentali

### I Tre Pilastri dell'Observability

L'observability si fonda su tre pilastri complementari che, combinati, forniscono una visione completa del comportamento di un sistema:

**Metrics** — Valori numerici aggregati nel tempo. Rappresentano contatori, gauge e istogrammi che descrivono lo stato quantitativo del sistema. Sono efficienti in termini di storage e permettono query rapide su lunghi periodi temporali. Esempio: `http_requests_total`, `cpu_usage_percent`, `request_duration_seconds`.

**Logs** — Record testuali o strutturati di eventi discreti. Ogni log entry rappresenta un evento specifico con timestamp, severity e contesto. Sono fondamentali per il debugging dettagliato ma costosi in termini di storage e indicizzazione. Esempio: un log strutturato JSON con `{"timestamp": "2026-04-11T10:30:00Z", "level": "ERROR", "service": "payment-api", "message": "timeout connecting to database", "trace_id": "abc123"}`.

**Traces** — Rappresentazioni del percorso di una richiesta attraverso sistemi distribuiti. Ogni trace si compone di span interconnessi che descrivono le operazioni individuali, i tempi di esecuzione e le dipendenze tra servizi. Sono indispensabili per diagnosticare latenza e errori in architetture a microservizi.

### Differenza tra Monitoring e Observability

Il **monitoring** e un approccio reattivo: si definiscono in anticipo le condizioni da controllare e si generano alert quando le soglie vengono superate. E basato sulla domanda "il sistema funziona?".

L'**observability** e un approccio proattivo e investigativo: permette di porre domande arbitrarie sul comportamento del sistema senza dover predefinire cosa cercare. E basata sulla domanda "perche il sistema si comporta cosi?".

In termini pratici, il monitoring dice "il CPU e al 95%", l'observability permette di capire "quale richiesta specifica, da quale utente, attraverso quali microservizi ha causato il picco di CPU".

### SLI, SLO, SLA

**SLI (Service Level Indicator)** — Metrica quantitativa che misura un aspetto del livello di servizio. Deve essere espressa come rapporto o percentuale. Esempi:

- Disponibilita: `richieste_successo / richieste_totali * 100`
- Latenza: `richieste_sotto_300ms / richieste_totali * 100`
- Throughput: `richieste_processate_per_secondo`

**SLO (Service Level Objective)** — Obiettivo target per un SLI, definito internamente dal team. Esempio: "il 99.9% delle richieste API deve avere latenza inferiore a 300ms misurata su una finestra di 30 giorni".

**SLA (Service Level Agreement)** — Contratto formale con il cliente che definisce le conseguenze del mancato raggiungimento degli obiettivi. Include penalita finanziarie o crediti. Gli SLA sono sempre meno stringenti degli SLO interni per garantire un margine di sicurezza.

Calcolo pratico di un SLO di disponibilita al 99.9% su 30 giorni:

```
Minuti totali in 30 giorni: 30 * 24 * 60 = 43.200 minuti
Downtime ammesso: 43.200 * 0.001 = 43,2 minuti (~43 minuti)
```

### Error Budget

L'error budget e il complemento dell'SLO: rappresenta la quantita ammessa di errori o indisponibilita prima di violare l'obiettivo. Con un SLO del 99.9%, l'error budget e lo 0.1%.

L'error budget serve come meccanismo decisionale:

- Se l'error budget e consumato, si bloccano i deploy e si priorizza l'affidabilita
- Se l'error budget e abbondante, si possono accettare rischi maggiori per rilasciare nuove funzionalita
- Il burn rate indica la velocita con cui l'error budget viene consumato

```
Error Budget Remaining = 1 - (errori_osservati / errori_ammessi)
Burn Rate = (errori_nel_periodo / error_budget_totale) * (durata_finestra / durata_periodo)
```

Un burn rate di 1.0 significa che l'error budget verra esaurito esattamente alla fine della finestra. Un burn rate di 10.0 significa che verra esaurito in 1/10 del tempo previsto.

### Golden Signals

Le quattro golden signals definite da Google nel Site Reliability Engineering book:

**Latenza** — Tempo necessario per servire una richiesta. Fondamentale distinguere tra latenza delle richieste riuscite e latenza delle richieste fallite (un errore HTTP 500 restituito in 10ms non e "veloce").

**Traffico** — Quantita di domanda posta sul sistema. Per un servizio web: richieste HTTP al secondo. Per un sistema di streaming: sessioni concorrenti o throughput in byte/secondo. Per un database: transazioni o query al secondo.

**Errori** — Tasso di richieste che falliscono. Include errori espliciti (HTTP 5xx), errori impliciti (HTTP 200 con contenuto errato) e errori di policy (risposte piu lente dell'SLO).

**Saturazione** — Quanto il servizio e "pieno". Misura le risorse piu vincolate (CPU, memoria, I/O, connessioni al database). I sistemi si degradano prima di raggiungere il 100% di utilizzo.

### Metodologia USE

La metodologia USE (Utilization, Saturation, Errors) di Brendan Gregg si applica a ogni risorsa hardware:

- **Utilization** — Percentuale di tempo in cui la risorsa e occupata (o capacita usata rispetto alla totale)
- **Saturation** — Lavoro in eccesso che la risorsa non riesce a servire (lunghezza della coda)
- **Errors** — Numero di eventi di errore sulla risorsa

Esempio per CPU: utilization = 85%, saturation = 12 processi in runqueue, errors = 0 machine check exceptions.

### Metodologia RED

La metodologia RED si applica ai servizi (non alle risorse):

- **Rate** — Richieste al secondo servite
- **Errors** — Richieste al secondo che falliscono
- **Duration** — Distribuzioni di latenza delle richieste

USE e per l'infrastruttura, RED e per i servizi applicativi. Utilizzarle entrambe fornisce copertura completa.

---

## 2. Prometheus

### Architettura

Prometheus utilizza un modello **pull-based**: il server Prometheus interroga periodicamente gli endpoint `/metrics` esposti dai target (scrape). Questo approccio offre vantaggi significativi rispetto al push-based:

- Il server controlla la frequenza di raccolta
- E possibile verificare immediatamente se un target e raggiungibile
- Non serve configurare i target con l'indirizzo del server
- Semplifica il funzionamento dietro firewall e NAT (con Pushgateway per casi eccezionali)

Componenti principali:

- **Prometheus Server** — Raccoglie e memorizza time series, valuta regole e genera alert
- **Client Libraries** — Librerie per instrumentare il codice applicativo (Go, Java, Python, etc.)
- **Pushgateway** — Accetta metriche push per job batch di breve durata
- **Exporters** — Processi che espongono metriche di sistemi terzi nel formato Prometheus
- **Alertmanager** — Gestisce deduplicazione, raggruppamento, silenziamento e routing degli alert

### Data Model

Ogni time series e identificata univocamente dal nome della metrica e da un insieme di coppie chiave-valore dette **labels**:

```
http_requests_total{method="GET", handler="/api/users", status="200"} 1234 1681234567000
```

Formato: `<metric_name>{<label1>=<value1>, ...} <value> [<timestamp>]`

Tipi di metriche:

- **Counter** — Valore monotonicamente crescente (richieste totali, errori totali). Si usa `rate()` per ottenere il tasso di crescita.
- **Gauge** — Valore che puo salire e scendere (temperatura, memoria usata, connessioni attive).
- **Histogram** — Campiona osservazioni in bucket configurabili. Genera `_bucket`, `_sum`, `_count`. Permette il calcolo di quantili lato server.
- **Summary** — Simile all'histogram ma calcola quantili lato client. Non aggregabile tra istanze.

### Configurazione — prometheus.yml

```yaml
global:
  scrape_interval: 15s          # Frequenza di scraping globale
  evaluation_interval: 15s      # Frequenza di valutazione delle regole
  scrape_timeout: 10s           # Timeout per ogni scrape
  external_labels:
    cluster: "production-eu"
    environment: "prod"

# Regole di recording e alerting
rule_files:
  - "rules/recording_rules.yml"
  - "rules/alerting_rules.yml"

# Configurazione Alertmanager
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - "alertmanager-01:9093"
            - "alertmanager-02:9093"

# Configurazione degli scrape job
scrape_configs:
  # Monitoraggio di Prometheus stesso
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # Applicazioni con static config
  - job_name: "api-servers"
    metrics_path: "/metrics"
    scheme: "https"
    tls_config:
      ca_file: "/etc/prometheus/ca.pem"
    basic_auth:
      username: "prometheus"
      password_file: "/etc/prometheus/password"
    static_configs:
      - targets:
          - "api-01.example.com:8443"
          - "api-02.example.com:8443"
        labels:
          team: "backend"
          tier: "api"

  # Service discovery Kubernetes
  - job_name: "kubernetes-pods"
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: ["production", "staging"]
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: "true"
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port, __address__]
        action: replace
        regex: (\d+);([^:]+):(\d+)
        replacement: $2:$1
        target_label: __address__
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: pod

  # Service discovery Consul
  - job_name: "consul-services"
    consul_sd_configs:
      - server: "consul.example.com:8500"
        services: []
    relabel_configs:
      - source_labels: [__meta_consul_tags]
        regex: .*,prometheus,.*
        action: keep
      - source_labels: [__meta_consul_service]
        target_label: service

# Remote write per long-term storage
remote_write:
  - url: "https://thanos-receive.example.com/api/v1/receive"
    queue_config:
      max_samples_per_send: 5000
      batch_send_deadline: 5s
      max_shards: 30
    write_relabel_configs:
      - source_labels: [__name__]
        regex: "go_.*"
        action: drop

remote_read:
  - url: "https://thanos-query.example.com/api/v1/read"
    read_recent: true
```

### PromQL — Query Language

Selettori e operazioni fondamentali:

```promql
# Selettore semplice — tutte le time series con questo nome
http_requests_total

# Selettore con label matching
http_requests_total{method="GET", status=~"2.."}

# Selettore con regex negativo
http_requests_total{handler!~"/health|/ready"}

# Rate — tasso al secondo su 5 minuti (fondamentale per counter)
rate(http_requests_total[5m])

# Increase — incremento assoluto su un periodo
increase(http_requests_total[1h])

# Tasso di errore percentuale
sum(rate(http_requests_total{status=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))
* 100

# Latenza p99 da histogram
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
)

# Latenza p99 per servizio
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service)
)

# Top 5 endpoint per richieste al secondo
topk(5,
  sum(rate(http_requests_total[5m])) by (handler)
)

# Memoria usata percentuale
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes)
/ node_memory_MemTotal_bytes * 100

# CPU usage percentuale (escludendo idle)
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Disk I/O utilization
rate(node_disk_io_time_seconds_total[5m]) * 100

# Predizione spazio disco esaurito in 4 ore
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[1h], 4 * 3600) < 0

# Aggregazione con without — somma rimuovendo label specifiche
sum without (instance, pod) (rate(http_requests_total[5m]))

# Subquery — rate del rate (accelerazione)
deriv(rate(http_requests_total[5m])[30m:1m])

# Utilizzo delle label_replace
label_replace(up{job="api"}, "short_instance", "$1", "instance", "(.*):.*")
```

### Recording Rules

Le recording rules precalcolano query costose e le salvano come nuove time series:

```yaml
# rules/recording_rules.yml
groups:
  - name: http_recording_rules
    interval: 30s
    rules:
      - record: job:http_requests_total:rate5m
        expr: sum(rate(http_requests_total[5m])) by (job)

      - record: job:http_request_errors:rate5m
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)

      - record: job:http_request_error_rate:ratio
        expr: |
          job:http_request_errors:rate5m
          / job:http_requests_total:rate5m

      - record: job:http_request_duration_seconds:p99
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le)
          )

      - record: job:http_request_duration_seconds:p50
        expr: |
          histogram_quantile(0.50,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le)
          )

  - name: node_recording_rules
    rules:
      - record: instance:node_cpu_utilization:ratio
        expr: |
          1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))

      - record: instance:node_memory_utilization:ratio
        expr: |
          1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
```

### Alerting Rules

```yaml
# rules/alerting_rules.yml
groups:
  - name: slo_alerts
    rules:
      # Burn rate alert multifinestra — strategia raccomandata da Google
      - alert: HighErrorBudgetBurn
        expr: |
          (
            job:http_request_error_rate:ratio > (14.4 * 0.001)
            and
            job:http_request_error_rate:ratio > (14.4 * 0.001)
          )
        for: 2m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Alto consumo error budget per {{ $labels.job }}"
          description: |
            Il servizio {{ $labels.job }} sta consumando l'error budget
            a un tasso 14.4x superiore al normale.
            Valore attuale: {{ $value | humanizePercentage }}
          runbook_url: "https://runbooks.example.com/high-error-budget-burn"

      - alert: HighLatencyP99
        expr: job:http_request_duration_seconds:p99 > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Latenza p99 elevata per {{ $labels.job }}"
          description: "Latenza p99 di {{ $value }}s supera la soglia di 1s"

  - name: infrastructure_alerts
    rules:
      - alert: HighCPUUsage
        expr: instance:node_cpu_utilization:ratio > 0.90
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU al {{ $value | humanizePercentage }} su {{ $labels.instance }}"

      - alert: DiskSpaceRunningOut
        expr: predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 24*3600) < 0
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Disco esaurito entro 24h su {{ $labels.instance }}"

      - alert: TargetDown
        expr: up == 0
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Target {{ $labels.instance }} non raggiungibile"
```

### Comandi CLI

```bash
# Avviare Prometheus
prometheus --config.file=/etc/prometheus/prometheus.yml \
           --storage.tsdb.path=/var/lib/prometheus \
           --storage.tsdb.retention.time=30d \
           --storage.tsdb.retention.size=50GB \
           --web.enable-lifecycle \
           --web.enable-admin-api

# Validare la configurazione
promtool check config /etc/prometheus/prometheus.yml

# Validare le regole
promtool check rules /etc/prometheus/rules/*.yml

# Query da CLI
promtool query instant http://localhost:9090 'up{job="api"}'
promtool query range http://localhost:9090 \
  --start="2026-04-10T00:00:00Z" \
  --end="2026-04-11T00:00:00Z" \
  --step=60s \
  'rate(http_requests_total[5m])'

# Ricaricare la configurazione senza restart
curl -X POST http://localhost:9090/-/reload

# Snapshot dei dati
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot

# Compattazione
curl -X POST http://localhost:9090/api/v1/admin/tsdb/clean_tombstones
```

---

## 3. Grafana

### Installazione e Configurazione

```bash
# Installazione su Debian/Ubuntu
sudo apt-get install -y apt-transport-https software-properties-common
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | \
  gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | \
  sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt-get update
sudo apt-get install grafana

# Avvio e abilitazione del servizio
sudo systemctl daemon-reload
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Installazione con Docker
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -v grafana-storage:/var/lib/grafana \
  -e "GF_SECURITY_ADMIN_USER=admin" \
  -e "GF_SECURITY_ADMIN_PASSWORD=securepassword" \
  -e "GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-piechart-panel" \
  grafana/grafana-oss:latest
```

Configurazione principale in `/etc/grafana/grafana.ini`:

```ini
[server]
protocol = https
http_port = 3000
domain = grafana.example.com
root_url = https://grafana.example.com/
cert_file = /etc/grafana/ssl/grafana.crt
cert_key = /etc/grafana/ssl/grafana.key

[database]
type = postgres
host = postgres.example.com:5432
name = grafana
user = grafana
password = ${GF_DATABASE_PASSWORD}
ssl_mode = require

[security]
admin_user = admin
admin_password = ${GF_SECURITY_ADMIN_PASSWORD}
cookie_secure = true
cookie_samesite = strict
content_security_policy = true

[auth.ldap]
enabled = true
config_file = /etc/grafana/ldap.toml

[smtp]
enabled = true
host = smtp.example.com:587
user = grafana@example.com
password = ${GF_SMTP_PASSWORD}
from_address = grafana@example.com
from_name = Grafana Alerts

[alerting]
enabled = true
execute_alerts = true
```

### Data Sources — Provisioning as Code

```yaml
# /etc/grafana/provisioning/datasources/datasources.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: "15s"
      httpMethod: POST
      exemplarTraceIdDestinations:
        - name: traceID
          datasourceUid: tempo
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: '"trace_id":"(\w+)"'
          name: TraceID
          url: "$${__value.raw}"

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    uid: tempo
    jsonData:
      tracesToLogs:
        datasourceUid: loki
        tags: ["service.name"]
      tracesToMetrics:
        datasourceUid: prometheus
      serviceMap:
        datasourceUid: prometheus

  - name: Elasticsearch
    type: elasticsearch
    access: proxy
    url: https://elasticsearch:9200
    database: "logs-*"
    jsonData:
      esVersion: "8.0.0"
      timeField: "@timestamp"
      logMessageField: message
      logLevelField: level
    secureJsonData:
      basicAuthPassword: "${ES_PASSWORD}"
    basicAuth: true
    basicAuthUser: grafana_reader
```

### Dashboard Design — JSON Model

```json
{
  "dashboard": {
    "id": null,
    "uid": "api-overview",
    "title": "API Service Overview",
    "tags": ["api", "production"],
    "timezone": "browser",
    "refresh": "30s",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "templating": {
      "list": [
        {
          "name": "namespace",
          "type": "query",
          "datasource": "Prometheus",
          "query": "label_values(http_requests_total, namespace)",
          "refresh": 2,
          "sort": 1,
          "multi": true,
          "includeAll": true
        },
        {
          "name": "service",
          "type": "query",
          "datasource": "Prometheus",
          "query": "label_values(http_requests_total{namespace=~\"$namespace\"}, service)",
          "refresh": 2,
          "sort": 1
        }
      ]
    },
    "panels": [
      {
        "type": "stat",
        "title": "Request Rate",
        "gridPos": { "h": 4, "w": 6, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{namespace=~\"$namespace\", service=~\"$service\"}[5m]))",
            "legendFormat": "req/s"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps",
            "thresholds": {
              "steps": [
                { "color": "green", "value": null },
                { "color": "yellow", "value": 1000 },
                { "color": "red", "value": 5000 }
              ]
            }
          }
        }
      },
      {
        "type": "timeseries",
        "title": "Request Rate by Status",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 4 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{namespace=~\"$namespace\", service=~\"$service\"}[5m])) by (status)",
            "legendFormat": "HTTP {{status}}"
          }
        ],
        "fieldConfig": {
          "overrides": [
            {
              "matcher": { "id": "byRegexp", "options": "HTTP 5.." },
              "properties": [
                { "id": "color", "value": { "fixedColor": "red", "mode": "fixed" } }
              ]
            }
          ]
        }
      },
      {
        "type": "heatmap",
        "title": "Request Duration Distribution",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 4 },
        "targets": [
          {
            "expr": "sum(increase(http_request_duration_seconds_bucket{namespace=~\"$namespace\", service=~\"$service\"}[5m])) by (le)",
            "format": "heatmap",
            "legendFormat": "{{le}}"
          }
        ]
      }
    ]
  }
}
```

### Provisioning Dashboard

```yaml
# /etc/grafana/provisioning/dashboards/dashboards.yml
apiVersion: 1

providers:
  - name: "default"
    orgId: 1
    folder: "Production"
    type: file
    disableDeletion: true
    updateIntervalSeconds: 60
    allowUiUpdates: false
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

### Grafana CLI e Gestione

```bash
# Gestione plugin
grafana cli plugins install grafana-piechart-panel
grafana cli plugins list-remote
grafana cli plugins update-all

# Reset password admin
grafana cli admin reset-admin-password newpassword

# Backup e restore tramite API
curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
  http://localhost:3000/api/dashboards/uid/api-overview | jq . > dashboard_backup.json

# Importare dashboard
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -d @dashboard_backup.json \
  http://localhost:3000/api/dashboards/db

# Creare API key
curl -X POST http://admin:password@localhost:3000/api/auth/keys \
  -H "Content-Type: application/json" \
  -d '{"name":"automation","role":"Editor","secondsToLive":86400}'

# Elencare data sources
curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
  http://localhost:3000/api/datasources | jq '.[] | {name, type, url}'
```

### Best Practices per Dashboard Design

- Organizzare le dashboard in una gerarchia: Overview -> Service -> Detail
- Usare variabili template per rendere le dashboard riutilizzabili
- Posizionare le metriche piu critiche (golden signals) nella parte superiore
- Utilizzare soglie di colore coerenti in tutta l'organizzazione (verde=ok, giallo=warning, rosso=critical)
- Includere link tra dashboard correlate per facilitare il drill-down
- Limitare il numero di pannelli per dashboard (massimo 15-20) per mantenere le prestazioni
- Utilizzare le annotations per marcare i deploy e gli incidenti sulla timeline

---

## 4. ELK Stack (Elasticsearch, Logstash, Kibana)

### Architettura

L'ELK Stack e composto da tre componenti principali che formano una pipeline di log processing:

1. **Elasticsearch** — Motore di ricerca e analisi distribuito basato su Apache Lucene. Memorizza e indicizza i dati, fornendo ricerca full-text e aggregazioni in tempo quasi reale.
2. **Logstash** — Pipeline di data processing che ingesta dati da molteplici sorgenti, li trasforma e li invia a una o piu destinazioni.
3. **Kibana** — Interfaccia web per visualizzazione e esplorazione dei dati in Elasticsearch.

Componenti aggiuntivi (Elastic Beats):
- **Filebeat** — Agent leggero per la raccolta e l'invio di log file
- **Metricbeat** — Agent per la raccolta di metriche di sistema e servizi
- **Packetbeat** — Analizzatore di traffico di rete
- **Heartbeat** — Monitor di disponibilita (uptime)

### Elasticsearch

#### Configurazione Cluster

```yaml
# /etc/elasticsearch/elasticsearch.yml
cluster.name: production-logs
node.name: es-node-01
node.roles: [master, data_hot, ingest]

path.data: /var/lib/elasticsearch
path.logs: /var/log/elasticsearch

network.host: 0.0.0.0
http.port: 9200
transport.port: 9300

discovery.seed_hosts:
  - es-node-01:9300
  - es-node-02:9300
  - es-node-03:9300
cluster.initial_master_nodes:
  - es-node-01
  - es-node-02
  - es-node-03

# Sicurezza
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.transport.ssl.keystore.path: /etc/elasticsearch/certs/elastic-certificates.p12
xpack.security.http.ssl.enabled: true
xpack.security.http.ssl.keystore.path: /etc/elasticsearch/certs/http.p12

# Allocazione memoria
indices.memory.index_buffer_size: 20%
thread_pool.write.queue_size: 1000
```

#### Gestione Indici e Mapping

```bash
# Creare un index template
curl -X PUT "https://localhost:9200/_index_template/logs-template" \
  -H "Content-Type: application/json" \
  -u elastic:password \
  -d '{
  "index_patterns": ["logs-*"],
  "priority": 100,
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.lifecycle.name": "logs-policy",
      "index.lifecycle.rollover_alias": "logs-write",
      "index.codec": "best_compression",
      "index.refresh_interval": "5s"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "message": { "type": "text", "analyzer": "standard" },
        "level": { "type": "keyword" },
        "service": { "type": "keyword" },
        "host": { "type": "keyword" },
        "trace_id": { "type": "keyword" },
        "span_id": { "type": "keyword" },
        "duration_ms": { "type": "long" },
        "request": {
          "properties": {
            "method": { "type": "keyword" },
            "path": { "type": "keyword" },
            "status_code": { "type": "integer" },
            "body_bytes": { "type": "long" }
          }
        },
        "geo": { "type": "geo_point" }
      }
    }
  }
}'
```

#### Index Lifecycle Management (ILM)

```bash
# Creare una ILM policy
curl -X PUT "https://localhost:9200/_ilm/policy/logs-policy" \
  -H "Content-Type: application/json" \
  -u elastic:password \
  -d '{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_primary_shard_size": "50gb",
            "max_age": "1d"
          },
          "set_priority": { "priority": 100 }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": { "number_of_shards": 1 },
          "forcemerge": { "max_num_segments": 1 },
          "set_priority": { "priority": 50 },
          "allocate": {
            "require": { "data": "warm" }
          }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "set_priority": { "priority": 0 },
          "allocate": {
            "require": { "data": "cold" }
          }
        }
      },
      "delete": {
        "min_age": "90d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}'
```

#### Query DSL

```bash
# Ricerca full-text con filtri
curl -X POST "https://localhost:9200/logs-*/_search" \
  -H "Content-Type: application/json" \
  -u elastic:password \
  -d '{
  "query": {
    "bool": {
      "must": [
        { "match": { "message": "connection timeout" } }
      ],
      "filter": [
        { "term": { "level": "ERROR" } },
        { "term": { "service": "payment-api" } },
        { "range": {
          "@timestamp": {
            "gte": "now-1h",
            "lte": "now"
          }
        }}
      ],
      "must_not": [
        { "term": { "host": "canary-01" } }
      ]
    }
  },
  "sort": [{ "@timestamp": "desc" }],
  "size": 50,
  "_source": ["@timestamp", "level", "service", "message", "trace_id"]
}'

# Aggregazione per contare errori per servizio
curl -X POST "https://localhost:9200/logs-*/_search" \
  -H "Content-Type: application/json" \
  -u elastic:password \
  -d '{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "term": { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "aggs": {
    "errors_by_service": {
      "terms": {
        "field": "service",
        "size": 20,
        "order": { "_count": "desc" }
      },
      "aggs": {
        "error_trend": {
          "date_histogram": {
            "field": "@timestamp",
            "fixed_interval": "1h"
          }
        },
        "top_errors": {
          "terms": {
            "field": "message.keyword",
            "size": 5
          }
        }
      }
    }
  }
}'

# Monitorare la salute del cluster
curl -X GET "https://localhost:9200/_cluster/health?pretty" -u elastic:password
curl -X GET "https://localhost:9200/_cat/indices?v&s=store.size:desc" -u elastic:password
curl -X GET "https://localhost:9200/_cat/shards?v&h=index,shard,prirep,state,docs,store,node" -u elastic:password
curl -X GET "https://localhost:9200/_cat/nodes?v&h=name,role,heap.percent,cpu,load_1m,disk.used_percent" -u elastic:password
```

### Logstash

#### Pipeline Configuration

```ruby
# /etc/logstash/conf.d/main.conf

input {
  beats {
    port => 5044
    ssl_enabled => true
    ssl_certificate => "/etc/logstash/ssl/logstash.crt"
    ssl_key => "/etc/logstash/ssl/logstash.key"
  }

  kafka {
    bootstrap_servers => "kafka-01:9092,kafka-02:9092,kafka-03:9092"
    topics => ["application-logs", "access-logs"]
    group_id => "logstash-consumers"
    codec => "json"
    consumer_threads => 3
    decorate_events => "extended"
  }
}

filter {
  # Parsing log strutturati JSON
  if [message] =~ /^\{/ {
    json {
      source => "message"
      target => "parsed"
    }
    mutate {
      rename => {
        "[parsed][level]" => "level"
        "[parsed][service]" => "service"
        "[parsed][trace_id]" => "trace_id"
        "[parsed][msg]" => "log_message"
      }
    }
  }

  # Parsing log Apache/Nginx con grok
  if [fileset][name] == "access" {
    grok {
      match => {
        "message" => '%{IPORHOST:client_ip} - %{DATA:user} \[%{HTTPDATE:timestamp}\] "%{WORD:method} %{URIPATHPARAM:request_uri} HTTP/%{NUMBER:http_version}" %{NUMBER:status_code:int} %{NUMBER:body_bytes:int} "%{DATA:referrer}" "%{DATA:user_agent}" %{NUMBER:request_time:float}'
      }
    }
    date {
      match => ["timestamp", "dd/MMM/yyyy:HH:mm:ss Z"]
      target => "@timestamp"
    }
    geoip {
      source => "client_ip"
      target => "geo"
    }
    useragent {
      source => "user_agent"
      target => "ua"
    }
  }

  # Parsing Java stack trace multilinea
  if [service] == "java-app" {
    multiline {
      pattern => "^%{TIMESTAMP_ISO8601}"
      negate => true
      what => "previous"
    }
    grok {
      match => {
        "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level}\s+\[%{DATA:thread}\] %{JAVACLASS:class} - %{GREEDYDATA:log_message}"
      }
    }
  }

  # Arricchimento e normalizzazione
  mutate {
    lowercase => ["level"]
    strip => ["log_message"]
    remove_field => ["agent", "ecs", "input", "tags"]
  }

  # Filtraggio — eliminare log di health check
  if [request_uri] =~ /^\/(health|ready|live)$/ {
    drop {}
  }

  # Calcolo fingerprint per deduplicazione
  fingerprint {
    source => ["service", "level", "log_message"]
    target => "[@metadata][fingerprint]"
    method => "SHA256"
  }
}

output {
  # Output primario verso Elasticsearch
  elasticsearch {
    hosts => ["https://es-node-01:9200", "https://es-node-02:9200"]
    index => "logs-%{[service]}-%{+YYYY.MM.dd}"
    user => "logstash_writer"
    password => "${ES_PASSWORD}"
    ssl_enabled => true
    ssl_certificate_authorities => ["/etc/logstash/ssl/ca.crt"]
    document_id => "%{[@metadata][fingerprint]}"
    action => "index"
  }

  # Output condizionale — errori critici verso canale Slack
  if [level] == "error" or [level] == "fatal" {
    http {
      url => "https://hooks.slack.com/services/T00/B00/xxx"
      http_method => "post"
      format => "json"
      mapping => {
        "text" => "[ALERT] %{service}: %{log_message}"
      }
    }
  }

  # Debug output (solo in sviluppo)
  # stdout { codec => rubydebug }
}
```

### Filebeat

```yaml
# /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: filestream
    id: app-logs
    paths:
      - /var/log/app/*.log
    parsers:
      - ndjson:
          keys_under_root: true
          overwrite_keys: true
          add_error_key: true
    fields:
      environment: production
    fields_under_root: true
    processors:
      - add_host_metadata: ~
      - add_cloud_metadata: ~

  - type: filestream
    id: nginx-access
    paths:
      - /var/log/nginx/access.log
    fileset:
      name: access

  - type: container
    paths:
      - /var/lib/docker/containers/*/*.log
    processors:
      - add_docker_metadata:
          host: "unix:///var/run/docker.sock"

output.logstash:
  hosts: ["logstash-01:5044", "logstash-02:5044"]
  ssl.certificate_authorities: ["/etc/filebeat/ca.crt"]
  loadbalance: true

# Monitoraggio Filebeat stesso
monitoring:
  enabled: true
  elasticsearch:
    hosts: ["https://es-monitor:9200"]
    username: beats_monitor
    password: "${BEATS_MONITOR_PASSWORD}"
```

### Kibana

Kibana si configura in `/etc/kibana/kibana.yml`:

```yaml
server.port: 5601
server.host: "0.0.0.0"
server.name: "kibana-prod"
server.publicBaseUrl: "https://kibana.example.com"

elasticsearch.hosts: ["https://es-node-01:9200", "https://es-node-02:9200"]
elasticsearch.username: "kibana_system"
elasticsearch.password: "${KIBANA_SYSTEM_PASSWORD}"
elasticsearch.ssl.certificateAuthorities: ["/etc/kibana/certs/ca.crt"]

xpack.security.encryptionKey: "something_random_at_least_32_characters"
xpack.encryptedSavedObjects.encryptionKey: "another_random_at_least_32_chars"
xpack.reporting.encryptionKey: "yet_another_random_32_chars_key"

logging:
  appenders:
    file:
      type: file
      fileName: /var/log/kibana/kibana.log
      layout:
        type: json
  root:
    level: info
    appenders: [file]
```

Le funzionalita principali di Kibana comprendono:

- **Discover** — Esplorazione interattiva dei log con filtri, query KQL e visualizzazione dei documenti
- **Visualize / Lens** — Creazione di grafici (linee, barre, pie, heatmap) basati su aggregazioni Elasticsearch
- **Dashboard** — Composizione di visualizzazioni in viste aggregate
- **Alerting** — Regole di alert basate su query Elasticsearch con notifiche verso email, Slack, PagerDuty
- **Index Management** — Gestione di indici, ILM policies, index templates

---

## 5. Loki

### Architettura

Loki e un sistema di aggregazione log sviluppato da Grafana Labs, progettato per essere efficiente in termini di costi. La sua filosofia fondamentale e: **indicizza solo le label, non il contenuto dei log**. Questo lo rende significativamente meno costoso in termini di storage e risorse rispetto a Elasticsearch, sacrificando la velocita di ricerca full-text.

Componenti architetturali:

- **Distributor** — Riceve i log in ingresso, li valida e li distribuisce agli Ingester
- **Ingester** — Costruisce chunk compressi in memoria e li scrive nello storage
- **Querier** — Esegue le query LogQL leggendo da Ingester (dati recenti) e storage (dati storici)
- **Query Frontend** — Ottimizza le query con splitting, caching e parallelizzazione
- **Compactor** — Ottimizza gli indici e gestisce la retention

Modalita di deployment:

- **Single Binary** — Tutti i componenti in un singolo processo (sviluppo, test)
- **Simple Scalable** — Read path e write path separati (produzione media)
- **Microservices** — Ogni componente scalato indipendentemente (alta scala)

### Differenze con ELK

| Aspetto | Loki | Elasticsearch |
|---------|------|---------------|
| Indicizzazione | Solo label (metadata) | Full-text su tutto il contenuto |
| Storage | Molto efficiente (object storage) | Costoso (indici invertiti) |
| Ricerca | Filtra per label, poi grep | Ricerca full-text nativa |
| Costo | 10-100x inferiore | Elevato per grandi volumi |
| Complessita operativa | Bassa | Alta (cluster management) |
| Query language | LogQL | Query DSL / KQL |
| Integrazione | Nativa con Grafana | Kibana dedicato |

### Configurazione

```yaml
# /etc/loki/loki-config.yml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096
  log_level: info

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: "2024-01-01"
      store: tsdb
      object_store: s3
      schema: v13
      index:
        prefix: index_
        period: 24h

storage_config:
  tsdb_shipper:
    active_index_directory: /loki/tsdb-index
    cache_location: /loki/tsdb-cache
  aws:
    s3: s3://us-east-1/loki-logs-bucket
    bucketnames: loki-logs-bucket
    region: us-east-1
    access_key_id: ${AWS_ACCESS_KEY_ID}
    secret_access_key: ${AWS_SECRET_ACCESS_KEY}

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h    # 7 giorni
  max_cache_freshness_per_query: 10m
  ingestion_rate_mb: 16
  ingestion_burst_size_mb: 32
  per_stream_rate_limit: 5MB
  max_entries_limit_per_query: 10000
  max_query_parallelism: 32
  retention_period: 744h              # 31 giorni

compactor:
  working_directory: /loki/compactor
  compaction_interval: 10m
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150

query_range:
  align_queries_with_step: true
  cache_results: true
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 256

ruler:
  storage:
    type: local
    local:
      directory: /loki/rules
  rule_path: /loki/rules-temp
  alertmanager_url: http://alertmanager:9093
  ring:
    kvstore:
      store: inmemory
  enable_api: true
```

### Promtail Agent

```yaml
# /etc/promtail/promtail-config.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /var/lib/promtail/positions.yml

clients:
  - url: http://loki:3100/loki/api/v1/push
    batchwait: 1s
    batchsize: 1048576    # 1MB
    timeout: 10s
    tenant_id: "default"

scrape_configs:
  # Log di sistema
  - job_name: syslog
    static_configs:
      - targets: [localhost]
        labels:
          job: syslog
          host: ${HOSTNAME}
          __path__: /var/log/syslog

  # Log applicativi con parsing pipeline
  - job_name: app-logs
    static_configs:
      - targets: [localhost]
        labels:
          job: application
          environment: production
          __path__: /var/log/app/*.log
    pipeline_stages:
      - json:
          expressions:
            level: level
            service: service
            trace_id: trace_id
            message: msg
            duration: duration_ms
      - labels:
          level:
          service:
      - timestamp:
          source: timestamp
          format: "2006-01-02T15:04:05.000Z"
      - output:
          source: message

  # Log container Docker
  - job_name: docker
    docker_sd_configs:
      - host: "unix:///var/run/docker.sock"
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'logstream'
    pipeline_stages:
      - docker: {}
      - json:
          expressions:
            level: level
      - labels:
          level:

  # Log Kubernetes tramite journal
  - job_name: journal
    journal:
      labels:
        job: systemd-journal
      path: /var/log/journal
      max_age: 12h
    relabel_configs:
      - source_labels: ['__journal__systemd_unit']
        target_label: 'unit'
```

### LogQL — Query Language

```logql
# Selettore di stream basilare
{job="application", level="error"}

# Filtro per contenuto (grep-like)
{service="payment-api"} |= "timeout"

# Filtro con regex
{service="payment-api"} |~ "connection.*(refused|timeout)"

# Filtro negativo
{service="payment-api"} != "healthcheck"

# Parsing JSON e filtraggio su campi estratti
{job="application"} | json | duration_ms > 1000

# Parsing con pattern
{job="nginx"} | pattern "<ip> - - [<_>] \"<method> <path> <_>\" <status> <bytes>"
  | status >= 500

# Formatting dell'output
{service="auth-api"} | json | line_format "{{.level}} | {{.message}} | trace={{.trace_id}}"

# Metric queries — contare log per secondo
count_over_time({service="payment-api", level="error"}[5m])

# Rate di errori
rate({service="payment-api", level="error"}[5m])

# Quantile della durata estratta dai log
quantile_over_time(0.99, {service="api"} | json | unwrap duration_ms [5m]) by (service)

# Top 5 servizi per volume di errori
topk(5, sum(rate({level="error"}[5m])) by (service))

# Rapporto errori su totale per servizio
sum(rate({level="error"}[5m])) by (service)
/
sum(rate({job="application"}[5m])) by (service)

# Bytes totali per servizio (analisi costi)
sum(bytes_over_time({job="application"}[24h])) by (service)

# Confronto tra periodi temporali
sum(count_over_time({level="error"}[1h]))
/
sum(count_over_time({level="error"}[1h] offset 24h))
```

---

## 6. Distributed Tracing — Jaeger e OpenTelemetry

### Concetti Fondamentali

Il distributed tracing permette di seguire il percorso di una singola richiesta attraverso tutti i servizi di un sistema distribuito. E fondamentale per diagnosticare problemi di latenza, identificare colli di bottiglia e comprendere le dipendenze tra servizi.

**Trace** — Rappresentazione completa del percorso di una richiesta end-to-end. Ogni trace ha un identificativo unico (trace ID) condiviso da tutti i servizi coinvolti.

**Span** — Unita di lavoro all'interno di un trace. Ogni span rappresenta una singola operazione (una chiamata HTTP, una query al database, un'elaborazione) con:

- Span ID univoco
- Riferimento al parent span (tranne lo span root)
- Timestamp di inizio e durata
- Nome dell'operazione
- Tag/attributi (chiave-valore)
- Log/eventi interni allo span
- Status (OK, ERROR)

**Context Propagation** — Meccanismo di trasmissione del trace context (trace ID, span ID, baggage) tra servizi. Avviene tramite header HTTP (es. `traceparent`, `tracestate` nel formato W3C Trace Context) o header di messaging.

**Baggage** — Coppie chiave-valore che viaggiano con il trace context attraverso tutti i servizi. Utili per propagare informazioni come tenant ID, user ID o feature flags.

### Jaeger — Architettura

Jaeger, sviluppato originariamente da Uber, e un sistema di tracing distribuito open source conforme allo standard OpenTelemetry:

- **Agent** — Daemon locale che riceve span via UDP e li invia al Collector. In deployment moderni con OpenTelemetry Collector, l'agent Jaeger e spesso sostituito.
- **Collector** — Riceve span, li valida, li indicizza e li scrive nello storage.
- **Query** — Servizio che espone un'API e una UI per cercare e visualizzare i trace.
- **Storage** — Backend di persistenza. Supporta Elasticsearch, Cassandra, Kafka, Badger (embedded), e storage compatibile con OpenSearch.

```bash
# Deploy Jaeger all-in-one (sviluppo)
docker run -d --name jaeger \
  -p 6831:6831/udp \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 4317:4317 \
  -p 4318:4318 \
  -e COLLECTOR_OTLP_ENABLED=true \
  -e SPAN_STORAGE_TYPE=elasticsearch \
  -e ES_SERVER_URLS=https://elasticsearch:9200 \
  -e ES_USERNAME=jaeger \
  -e ES_PASSWORD=jaeger_password \
  jaegertracing/all-in-one:latest

# Deploy Jaeger produzione con Elasticsearch
docker run -d --name jaeger-collector \
  -p 14250:14250 \
  -p 4317:4317 \
  -e SPAN_STORAGE_TYPE=elasticsearch \
  -e ES_SERVER_URLS=https://es-01:9200,https://es-02:9200 \
  -e ES_INDEX_PREFIX=jaeger \
  -e ES_NUM_SHARDS=3 \
  -e ES_NUM_REPLICAS=1 \
  jaegertracing/jaeger-collector:latest
```

### OpenTelemetry

OpenTelemetry (OTel) e lo standard de facto per l'instrumentazione: fornisce API, SDK e strumenti per generare, raccogliere e esportare telemetry data (traces, metrics, logs).

Componenti:

- **API** — Interfacce per l'instrumentazione del codice. Indipendenti dall'implementazione.
- **SDK** — Implementazione dell'API con configurazione di sampling, processing e export.
- **Collector** — Agente/gateway che riceve, processa e esporta telemetry data. Supporta il protocollo OTLP (OpenTelemetry Protocol) via gRPC e HTTP.
- **Instrumentazione Automatica** — Agent che iniettano instrumentazione senza modifiche al codice sorgente.

#### OpenTelemetry Collector — Configurazione

```yaml
# /etc/otelcol/config.yml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
        max_recv_msg_size_mib: 16
      http:
        endpoint: 0.0.0.0:4318

  prometheus:
    config:
      scrape_configs:
        - job_name: "otel-collector"
          scrape_interval: 15s
          static_configs:
            - targets: ["localhost:8888"]

  jaeger:
    protocols:
      thrift_compact:
        endpoint: 0.0.0.0:6831
      grpc:
        endpoint: 0.0.0.0:14250

processors:
  batch:
    timeout: 5s
    send_batch_size: 8192
    send_batch_max_size: 16384

  memory_limiter:
    check_interval: 1s
    limit_mib: 2048
    spike_limit_mib: 512

  resource:
    attributes:
      - key: environment
        value: production
        action: upsert
      - key: cluster
        value: eu-west-1
        action: upsert

  attributes:
    actions:
      - key: db.password
        action: delete
      - key: http.request.header.authorization
        action: delete

  tail_sampling:
    decision_wait: 10s
    num_traces: 100000
    policies:
      - name: errors
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow-traces
        type: latency
        latency: { threshold_ms: 2000 }
      - name: probabilistic
        type: probabilistic
        probabilistic: { sampling_percentage: 10 }

exporters:
  otlp/jaeger:
    endpoint: jaeger-collector:4317
    tls:
      insecure: false
      ca_file: /etc/otelcol/certs/ca.crt

  prometheus:
    endpoint: 0.0.0.0:8889
    namespace: otel
    resource_to_telemetry_conversion:
      enabled: true

  loki:
    endpoint: http://loki:3100/loki/api/v1/push
    labels:
      attributes:
        service.name: "service"
        level: "level"

  debug:
    verbosity: detailed

extensions:
  health_check:
    endpoint: 0.0.0.0:13133
  zpages:
    endpoint: 0.0.0.0:55679

service:
  extensions: [health_check, zpages]
  pipelines:
    traces:
      receivers: [otlp, jaeger]
      processors: [memory_limiter, resource, attributes, tail_sampling, batch]
      exporters: [otlp/jaeger]
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, resource, batch]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, resource, attributes, batch]
      exporters: [loki]
  telemetry:
    logs:
      level: info
    metrics:
      address: 0.0.0.0:8888
```

#### Instrumentazione Manuale — Python

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Configurazione del provider
resource = Resource.create({
    "service.name": "payment-service",
    "service.version": "1.2.0",
    "deployment.environment": "production"
})

provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(endpoint="otel-collector:4317", insecure=False)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("payment-service")

# Utilizzo nel codice applicativo
@tracer.start_as_current_span("process_payment")
def process_payment(order_id: str, amount: float):
    span = trace.get_current_span()
    span.set_attribute("order.id", order_id)
    span.set_attribute("payment.amount", amount)

    with tracer.start_as_current_span("validate_card") as child_span:
        child_span.set_attribute("card.type", "visa")
        # logica di validazione

    with tracer.start_as_current_span("charge_payment") as child_span:
        try:
            # logica di addebito
            child_span.set_attribute("payment.status", "success")
        except Exception as e:
            child_span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            child_span.record_exception(e)
            raise
```

### Sampling Strategies

- **Head-based sampling** — Decisione presa all'inizio del trace (es. campionare il 10% delle richieste). Semplice ma rischia di perdere trace importanti (errori rari).
- **Tail-based sampling** — Decisione presa alla fine del trace quando tutte le informazioni sono disponibili. Permette di campionare il 100% degli errori e dei trace lenti, riducendo il volume complessivo. Richiede piu risorse (buffer dei trace in attesa di decisione).
- **Rate limiting** — Limita il numero di trace al secondo indipendentemente dal volume.
- **Adaptive sampling** — Regola dinamicamente il tasso di campionamento in base al volume e alla tipologia delle richieste.

### Correlazione Traces-Metrics-Logs

La correlazione tra i tre pilastri e il vero valore dell'observability. Si realizza tramite:

1. Inserire `trace_id` e `span_id` nei log applicativi
2. Utilizzare exemplar in Prometheus per collegare metriche a trace specifici
3. Configurare Grafana con data source linkati (Prometheus -> Tempo/Jaeger, Loki -> Tempo/Jaeger)

Questo permette il flusso investigativo: alert su metrica -> dashboard -> log correlati -> trace specifico -> span problematico.

---

## 7. APM (Application Performance Monitoring)

### Concetti

L'APM si focalizza sulle prestazioni dal punto di vista dell'applicazione, integrando metriche di infrastruttura con dati applicativi dettagliati. I componenti chiave sono:

**Transaction Tracing** — Ogni richiesta dell'utente viene tracciata attraverso tutti i tier applicativi (frontend, backend, database). Ogni transazione registra tempi di risposta, breakdown per componente e errori.

**Service Maps** — Visualizzazione automatica delle dipendenze tra servizi, con indicazione del tasso di richieste, latenza e tasso di errore per ogni connessione.

**Error Tracking** — Raggruppamento automatico di eccezioni e errori per tipo, con conteggio delle occorrenze, impatto sugli utenti e primo/ultimo verificarsi.

**Code-Level Profiling** — Identificazione delle funzioni e metodi che consumano piu tempo o risorse all'interno di una transazione.

### Apdex Score

L'Apdex (Application Performance Index) e uno standard aperto che misura la soddisfazione dell'utente sulla base della latenza:

```
Apdex = (Satisfied + Tolerated/2) / Total_Requests

Dove:
- Satisfied: risposta < T (soglia target, es. 500ms)
- Tolerated: T <= risposta < 4T (tra 500ms e 2s)
- Frustrated: risposta >= 4T (oltre 2s)
```

Interpretazione:
- 0.94-1.00: Eccellente
- 0.85-0.93: Buono
- 0.70-0.84: Discreto
- 0.50-0.69: Scarso
- < 0.50: Inaccettabile

### Strumenti APM — Panoramica Comparativa

**Elastic APM** — Soluzione open source integrata nell'Elastic Stack. Agent disponibili per Java, .NET, Node.js, Python, Go, Ruby, PHP. I dati APM vengono memorizzati in Elasticsearch e visualizzati in Kibana.

Configurazione agent Elastic APM per Node.js:

```javascript
// Deve essere la prima istruzione nel file principale
const apm = require('elastic-apm-node').start({
  serviceName: 'payment-service',
  secretToken: process.env.APM_SECRET_TOKEN,
  serverUrl: 'https://apm-server.example.com:8200',
  environment: 'production',
  captureBody: 'errors',
  transactionSampleRate: 0.5,
  captureHeaders: true,
  errorOnAbortedRequests: true,
  abortedRequestTimeout: 25
});
```

Configurazione APM Server:

```yaml
# /etc/apm-server/apm-server.yml
apm-server:
  host: "0.0.0.0:8200"
  auth:
    secret_token: "${APM_SECRET_TOKEN}"
  ssl:
    enabled: true
    certificate: "/etc/apm-server/certs/apm.crt"
    key: "/etc/apm-server/certs/apm.key"
  rum:
    enabled: true
    allow_origins: ["https://app.example.com"]

output.elasticsearch:
  hosts: ["https://es-01:9200"]
  username: "apm_writer"
  password: "${ES_PASSWORD}"
  indices:
    - index: "apm-%{[observer.version]}-transaction-%{+yyyy.MM.dd}"
    - index: "apm-%{[observer.version]}-span-%{+yyyy.MM.dd}"
    - index: "apm-%{[observer.version]}-error-%{+yyyy.MM.dd}"
```

**Datadog APM** — Piattaforma SaaS completa. Agent locale (dd-agent) raccoglie metriche, trace e log. Punti di forza: correlazione automatica tra metriche infrastruttura e trace applicativi, Continuous Profiler, Error Tracking avanzato.

**New Relic** — Piattaforma SaaS con modello pricing basato su dati ingeriti. Offre APM, infrastructure monitoring, log management, synthetic monitoring e browser monitoring in un'unica piattaforma.

**Dynatrace** — Piattaforma con forte enfasi sull'automazione (AI-powered root cause analysis tramite Davis AI). OneAgent si installa automaticamente e scopre la topologia applicativa senza configurazione manuale.

### Scelta dello Strumento APM

Criteri di valutazione:

- **Linguaggi supportati** — Verificare la copertura per lo stack tecnologico in uso
- **Overhead dell'agent** — Impatto sulle prestazioni dell'applicazione (target: < 3% CPU, < 50MB RAM)
- **Costo** — Modelli diversi: per host, per GB ingeriti, per utente
- **Integrazione** — Compatibilita con il resto dello stack di observability
- **Retention** — Durata di conservazione dei dati e politiche di campionamento
- **Self-hosted vs SaaS** — Requisiti di compliance e sovranita dei dati

---

## 8. Alerting Strategies

### Principi di Design degli Alert

Un alert efficace deve soddisfare questi criteri:

- **Azionabile** — Ogni alert deve richiedere un'azione umana immediata. Se non richiede azione, non e un alert (e un log o una notifica informativa).
- **Basato su sintomi, non su cause** — Allertare su "il tasso di errore supera lo SLO" piuttosto che su "il CPU e al 90%". Gli utenti subiscono i sintomi, non le cause.
- **Contestualizzato** — Deve includere informazioni sufficienti per iniziare la diagnosi: servizio, ambiente, valore attuale, soglia, link al runbook, link alla dashboard.
- **Non ridondante** — Evitare alert multipli per lo stesso incidente. Utilizzare raggruppamento e inibizione.

### Severity e Routing

```
CRITICAL (P1) — Impatto sugli utenti in corso. SLA a rischio.
  -> Notifica immediata: PagerDuty, telefono, SMS
  -> Risposta attesa: entro 5 minuti
  -> Esempio: error rate > 5% per 2 minuti, servizio completamente non disponibile

HIGH (P2) — Degrado significativo o rischio imminente di impatto.
  -> Notifica: PagerDuty durante orario lavorativo, Slack channel urgente
  -> Risposta attesa: entro 30 minuti
  -> Esempio: latenza p99 > 2s per 10 minuti, disk space < 10%

MEDIUM (P3) — Problema che richiede attenzione ma non impatto immediato.
  -> Notifica: Slack channel, email
  -> Risposta attesa: entro 4 ore (orario lavorativo)
  -> Esempio: error rate leggermente elevato, certificate in scadenza tra 14 giorni

LOW (P4) — Informativo, da investigare quando possibile.
  -> Notifica: ticket automatico, dashboard
  -> Risposta attesa: entro 1-2 giorni lavorativi
  -> Esempio: nuovo warning in log, drift di configurazione
```

### Alertmanager — Configurazione

```yaml
# /etc/alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m
  smtp_smarthost: "smtp.example.com:587"
  smtp_from: "alertmanager@example.com"
  smtp_auth_username: "alertmanager@example.com"
  smtp_auth_password: "${SMTP_PASSWORD}"
  smtp_require_tls: true
  pagerduty_url: "https://events.pagerduty.com/v2/enqueue"
  slack_api_url: "https://hooks.slack.com/services/T00/B00/xxx"

templates:
  - "/etc/alertmanager/templates/*.tmpl"

# Routing tree
route:
  receiver: "default-slack"
  group_by: ["alertname", "cluster", "service"]
  group_wait: 30s         # Tempo di attesa per raggruppare alert correlati
  group_interval: 5m      # Intervallo tra notifiche per lo stesso gruppo
  repeat_interval: 4h     # Intervallo prima di ripetere una notifica non risolta

  routes:
    # Alert critici -> PagerDuty
    - receiver: "pagerduty-critical"
      matchers:
        - severity = critical
      group_wait: 10s
      repeat_interval: 1h
      continue: true       # Continua a valutare le route successive

    # Alert critici -> anche Slack urgente
    - receiver: "slack-critical"
      matchers:
        - severity = critical

    # Alert per team specifico
    - receiver: "slack-backend"
      matchers:
        - team = backend
        - severity =~ "warning|critical"

    # Alert infrastruttura
    - receiver: "slack-infra"
      matchers:
        - team = infrastructure

    # Alert di business -> email ai product owner
    - receiver: "email-product"
      matchers:
        - type = business
      group_by: ["alertname"]
      repeat_interval: 24h

# Inibizione — sopprimere alert ridondanti
inhibit_rules:
  # Se un servizio e down (critical), sopprimere i warning correlati
  - source_matchers:
      - severity = critical
    target_matchers:
      - severity = warning
    equal: ["alertname", "cluster", "service"]

  # Se il cluster e irraggiungibile, sopprimere tutti gli alert dei nodi
  - source_matchers:
      - alertname = ClusterUnreachable
    target_matchers:
      - severity =~ "warning|critical"
    equal: ["cluster"]

# Silenziamento temporaneo via API:
# amtool silence add alertname="DiskSpaceLow" instance="worker-03" --comment="Disco in sostituzione" --duration="4h"

receivers:
  - name: "default-slack"
    slack_configs:
      - channel: "#alerts-general"
        title: '{{ template "slack.title" . }}'
        text: '{{ template "slack.text" . }}'
        send_resolved: true

  - name: "slack-critical"
    slack_configs:
      - channel: "#alerts-critical"
        title: '[CRITICAL] {{ .GroupLabels.alertname }}'
        text: |
          *Servizio:* {{ .CommonLabels.service }}
          *Cluster:* {{ .CommonLabels.cluster }}
          *Descrizione:* {{ range .Alerts }}{{ .Annotations.description }}{{ end }}
          *Runbook:* {{ (index .Alerts 0).Annotations.runbook_url }}
          *Dashboard:* {{ (index .Alerts 0).Annotations.dashboard_url }}
        send_resolved: true
        color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'

  - name: "pagerduty-critical"
    pagerduty_configs:
      - routing_key: "${PAGERDUTY_ROUTING_KEY}"
        severity: critical
        description: '{{ .GroupLabels.alertname }}: {{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ template "pagerduty.instances" .Alerts.Firing }}'
          num_firing: '{{ .Alerts.Firing | len }}'

  - name: "slack-backend"
    slack_configs:
      - channel: "#team-backend-alerts"
        send_resolved: true

  - name: "slack-infra"
    slack_configs:
      - channel: "#team-infra-alerts"
        send_resolved: true

  - name: "email-product"
    email_configs:
      - to: "product-team@example.com"
        send_resolved: true
```

### Amtool — CLI per Alertmanager

```bash
# Verificare la configurazione
amtool check-config /etc/alertmanager/alertmanager.yml

# Visualizzare alert attivi
amtool alert query --alertmanager.url=http://localhost:9093

# Creare un silence
amtool silence add alertname="HighCPU" instance="worker-05" \
  --alertmanager.url=http://localhost:9093 \
  --comment="Manutenzione programmata" \
  --author="ops-team" \
  --duration="2h"

# Elencare i silence attivi
amtool silence query --alertmanager.url=http://localhost:9093

# Rimuovere un silence
amtool silence expire <silence-id> --alertmanager.url=http://localhost:9093
```

### Prevenzione dell'Alert Fatigue

L'alert fatigue si verifica quando il volume di notifiche e cosi alto che gli operatori iniziano a ignorarle. Strategie di prevenzione:

1. **Revisione periodica** — Ogni alert che non ha richiesto azione negli ultimi 30 giorni va eliminato o convertito in dashboard
2. **Soglie dinamiche** — Utilizzare deviazioni dalla baseline piuttosto che soglie statiche quando possibile
3. **Raggruppamento aggressivo** — Configurare `group_by` in modo che incidenti correlati generino una singola notifica
4. **Inibizione** — Sopprimere alert subordinati quando la causa radice e gia notificata
5. **Finestre di manutenzione** — Silenziare proattivamente durante i deploy pianificati
6. **Metriche sugli alert** — Tracciare il rapporto signal-to-noise: `alert_utili / alert_totali`. Obiettivo: > 80%

---

## 9. Monitoring Infrastructure

### Node Exporter

Node Exporter espone metriche hardware e OS dei sistemi Linux per Prometheus:

```bash
# Installazione
wget https://github.com/prometheus/node_exporter/releases/download/v1.8.0/node_exporter-1.8.0.linux-amd64.tar.gz
tar xzf node_exporter-1.8.0.linux-amd64.tar.gz
sudo cp node_exporter-1.8.0.linux-amd64/node_exporter /usr/local/bin/

# Systemd service
sudo tee /etc/systemd/system/node_exporter.service <<EOF
[Unit]
Description=Prometheus Node Exporter
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter \
  --collector.filesystem.mount-points-exclude="^/(sys|proc|dev|host|etc)($$|/)" \
  --collector.netclass.ignored-devices="^(veth.*|cali.*|docker.*)$$" \
  --collector.systemd \
  --collector.processes \
  --web.listen-address=":9100" \
  --web.telemetry-path="/metrics"

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now node_exporter
```

Metriche fondamentali esposte da Node Exporter:

```promql
# CPU — utilizzo per modo
rate(node_cpu_seconds_total{mode!="idle"}[5m])

# Memoria — percentuale utilizzata
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes

# Disco — spazio disponibile
node_filesystem_avail_bytes{mountpoint="/"}

# Disco — I/O throughput
rate(node_disk_read_bytes_total[5m])
rate(node_disk_written_bytes_total[5m])

# Network — traffico
rate(node_network_receive_bytes_total{device="eth0"}[5m])
rate(node_network_transmit_bytes_total{device="eth0"}[5m])

# Load average
node_load1
node_load5
node_load15

# File descriptor in uso
node_filefd_allocated / node_filefd_maximum
```

### cAdvisor

cAdvisor (Container Advisor) fornisce metriche per i container in esecuzione:

```bash
# Deploy con Docker
docker run -d \
  --name cadvisor \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --volume=/dev/disk/:/dev/disk:ro \
  --publish=8080:8080 \
  --privileged \
  --device=/dev/kmsg \
  gcr.io/cadvisor/cadvisor:latest
```

Query PromQL per metriche container:

```promql
# CPU usage per container
rate(container_cpu_usage_seconds_total{name!=""}[5m])

# Memory usage per container
container_memory_working_set_bytes{name!=""}

# Network I/O per container
rate(container_network_receive_bytes_total{name!=""}[5m])
rate(container_network_transmit_bytes_total{name!=""}[5m])

# Filesystem usage
container_fs_usage_bytes{name!=""}

# Container restart count
increase(container_restart_count{name!=""}[1h])
```

### Blackbox Exporter

Il Blackbox Exporter permette il probing di endpoint tramite HTTP, HTTPS, DNS, TCP e ICMP:

```yaml
# /etc/blackbox_exporter/blackbox.yml
modules:
  http_2xx:
    prober: http
    timeout: 10s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: [200, 201, 204]
      method: GET
      follow_redirects: true
      fail_if_ssl: false
      fail_if_not_ssl: true
      tls_config:
        insecure_skip_verify: false

  http_post_json:
    prober: http
    timeout: 10s
    http:
      method: POST
      headers:
        Content-Type: application/json
      body: '{"test": true}'
      valid_status_codes: [200]

  tcp_connect:
    prober: tcp
    timeout: 5s

  dns_resolution:
    prober: dns
    timeout: 5s
    dns:
      query_name: "example.com"
      query_type: "A"
      valid_rcodes:
        - NOERROR

  icmp_ping:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: "ip4"
```

Configurazione Prometheus per il Blackbox Exporter:

```yaml
# In prometheus.yml
scrape_configs:
  - job_name: "blackbox-http"
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://api.example.com/health
          - https://www.example.com
          - https://admin.example.com/login
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115

  - job_name: "blackbox-tcp"
    metrics_path: /probe
    params:
      module: [tcp_connect]
    static_configs:
      - targets:
          - postgres.example.com:5432
          - redis.example.com:6379
          - rabbitmq.example.com:5672
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

Alert basati su Blackbox Exporter:

```promql
# Endpoint non raggiungibile
probe_success{job="blackbox-http"} == 0

# Certificato SSL in scadenza entro 14 giorni
probe_ssl_earliest_cert_expiry - time() < 86400 * 14

# Latenza HTTP superiore a 2 secondi
probe_http_duration_seconds{phase="transfer"} > 2

# DNS resolution failure
probe_dns_lookup_time_seconds > 1
```

### Synthetic Monitoring

Il synthetic monitoring simula le interazioni degli utenti per verificare la disponibilita e le prestazioni in modo proattivo, indipendentemente dal traffico reale. Si complementa con il Real User Monitoring (RUM) che misura l'esperienza degli utenti reali.

Strumenti comuni:

- **Grafana Synthetic Monitoring** — Plugin Grafana Cloud che esegue check HTTP, DNS, TCP e multi-step da location globali
- **Prometheus Blackbox Exporter** — Probing di base (HTTP, TCP, DNS, ICMP)
- **Checkly** — Piattaforma SaaS per API monitoring e browser checks con Playwright
- **Uptime Robot / BetterUptime** — Servizi di uptime monitoring con status page integrate

---

## 10. Observability in Kubernetes

### Prometheus Operator e kube-prometheus-stack

Il Prometheus Operator semplifica il deploy e la gestione di Prometheus in Kubernetes utilizzando Custom Resource Definitions (CRD):

- **Prometheus** — Definisce un'istanza Prometheus
- **ServiceMonitor** — Definisce quali Service monitorare e come
- **PodMonitor** — Definisce quali Pod monitorare direttamente
- **PrometheusRule** — Definisce recording e alerting rules
- **Alertmanager** — Definisce un'istanza Alertmanager

```bash
# Installazione kube-prometheus-stack con Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=100Gi \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.storageClassName=gp3 \
  --set grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}" \
  --set grafana.persistence.enabled=true \
  --set grafana.persistence.size=10Gi \
  --set alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.resources.requests.storage=10Gi \
  -f custom-values.yml
```

Custom values per kube-prometheus-stack:

```yaml
# custom-values.yml
prometheus:
  prometheusSpec:
    podMonitorSelectorNilUsesHelmValues: false
    serviceMonitorSelectorNilUsesHelmValues: false
    ruleSelectorNilUsesHelmValues: false
    externalLabels:
      cluster: production-eu
    resources:
      requests:
        memory: 2Gi
        cpu: 500m
      limits:
        memory: 4Gi
        cpu: 2000m
    additionalScrapeConfigs:
      - job_name: "custom-app"
        kubernetes_sd_configs:
          - role: pod
        relabel_configs:
          - source_labels: [__meta_kubernetes_pod_annotation_custom_scrape]
            action: keep
            regex: "true"

grafana:
  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
        - name: custom
          orgId: 1
          folder: "Custom"
          type: file
          disableDeletion: false
          editable: true
          options:
            path: /var/lib/grafana/dashboards/custom
  additionalDataSources:
    - name: Loki
      type: loki
      url: http://loki-gateway.monitoring.svc:3100
      access: proxy
    - name: Tempo
      type: tempo
      url: http://tempo.monitoring.svc:3200
      access: proxy

alertmanager:
  config:
    route:
      receiver: "slack-default"
      group_by: ["alertname", "namespace"]
      routes:
        - receiver: "pagerduty"
          matchers:
            - severity = critical
    receivers:
      - name: "slack-default"
        slack_configs:
          - api_url: "${SLACK_WEBHOOK}"
            channel: "#k8s-alerts"
      - name: "pagerduty"
        pagerduty_configs:
          - routing_key: "${PD_KEY}"
```

### ServiceMonitor e PodMonitor

```yaml
# ServiceMonitor per monitorare un'applicazione
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: payment-service
  namespace: monitoring
  labels:
    release: kube-prometheus
spec:
  namespaceSelector:
    matchNames:
      - production
  selector:
    matchLabels:
      app: payment-service
  endpoints:
    - port: metrics
      interval: 15s
      path: /metrics
      scrapeTimeout: 10s
      metricRelabelings:
        - sourceLabels: [__name__]
          regex: "go_(gc|memstats)_.*"
          action: drop

---
# PrometheusRule per l'applicazione
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: payment-service-rules
  namespace: monitoring
  labels:
    release: kube-prometheus
spec:
  groups:
    - name: payment-service
      rules:
        - alert: PaymentServiceHighErrorRate
          expr: |
            sum(rate(http_requests_total{job="payment-service", status=~"5.."}[5m]))
            / sum(rate(http_requests_total{job="payment-service"}[5m])) > 0.05
          for: 3m
          labels:
            severity: critical
            service: payment
          annotations:
            summary: "Tasso di errore elevato per payment-service"
            description: "Error rate: {{ $value | humanizePercentage }}"
```

### Metriche Kubernetes Essenziali

```promql
# kube-state-metrics — stato dei pod
kube_pod_status_phase{phase="Running"}
kube_pod_container_status_restarts_total
kube_pod_container_status_waiting_reason

# Risorse richieste vs limiti vs utilizzo effettivo
# Questo e fondamentale per il capacity planning
sum(kube_pod_container_resource_requests{resource="cpu"}) by (namespace)
sum(kube_pod_container_resource_limits{resource="cpu"}) by (namespace)
sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (namespace)

# Overcommit ratio (risorse richieste / capacita nodo)
sum(kube_pod_container_resource_requests{resource="memory"})
/ sum(kube_node_status_allocatable{resource="memory"})

# Pod non schedulabili
kube_pod_status_phase{phase="Pending"} > 0

# Deployment rollout bloccato
kube_deployment_status_observed_generation != kube_deployment_metadata_generation

# HPA — stato dell'autoscaling
kube_horizontalpodautoscaler_status_current_replicas
  / kube_horizontalpodautoscaler_spec_max_replicas

# PVC — stato dei volumi persistenti
kube_persistentvolumeclaim_status_phase{phase!="Bound"}

# Node conditions
kube_node_status_condition{condition="Ready", status="true"} == 0
kube_node_status_condition{condition="MemoryPressure", status="true"} == 1
kube_node_status_condition{condition="DiskPressure", status="true"} == 1
```

### Logging Architecture in Kubernetes — DaemonSet Pattern

Il pattern standard per la raccolta log in Kubernetes utilizza un DaemonSet che esegue un agent di log su ogni nodo:

```yaml
# Promtail DaemonSet per Loki
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: promtail
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: promtail
  template:
    metadata:
      labels:
        app: promtail
    spec:
      serviceAccountName: promtail
      tolerations:
        - effect: NoSchedule
          operator: Exists
      containers:
        - name: promtail
          image: grafana/promtail:latest
          args:
            - -config.file=/etc/promtail/promtail.yml
          env:
            - name: HOSTNAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
          volumeMounts:
            - name: config
              mountPath: /etc/promtail
            - name: varlog
              mountPath: /var/log
              readOnly: true
            - name: containers
              mountPath: /var/lib/docker/containers
              readOnly: true
            - name: positions
              mountPath: /var/lib/promtail
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 256Mi
      volumes:
        - name: config
          configMap:
            name: promtail-config
        - name: varlog
          hostPath:
            path: /var/log
        - name: containers
          hostPath:
            path: /var/lib/docker/containers
        - name: positions
          hostPath:
            path: /var/lib/promtail
```

### Grafana Tempo per Traces in Kubernetes

```yaml
# Deploy Tempo con Helm
# helm install tempo grafana/tempo --namespace monitoring -f tempo-values.yml

# tempo-values.yml
tempo:
  storage:
    trace:
      backend: s3
      s3:
        bucket: tempo-traces
        endpoint: s3.eu-west-1.amazonaws.com
        region: eu-west-1
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318
    jaeger:
      protocols:
        thrift_compact:
          endpoint: 0.0.0.0:6831
  overrides:
    defaults:
      metrics_generator:
        processors:
          - service-graphs
          - span-metrics
  metricsGenerator:
    enabled: true
    remoteWriteUrl: http://prometheus:9090/api/v1/write
```

---

## 11. Best Practices

### Monitoring as Code

Tutta la configurazione dell'observability deve essere gestita come codice, versionata in Git e applicata tramite pipeline CI/CD:

```
monitoring-repo/
  prometheus/
    prometheus.yml
    rules/
      recording_rules.yml
      alerting_rules.yml
  alertmanager/
    alertmanager.yml
    templates/
      slack.tmpl
  grafana/
    provisioning/
      datasources/
        datasources.yml
      dashboards/
        dashboards.yml
    dashboards/
      api-overview.json
      infrastructure.json
  loki/
    loki-config.yml
    promtail-config.yml
  otel-collector/
    config.yml
  kubernetes/
    servicemonitors/
    prometheusrules/
  terraform/
    datadog_monitors.tf
    pagerduty_services.tf
```

Principi:

- Ogni modifica alla configurazione di monitoring passa per code review
- Le alerting rules vengono testate con `promtool test rules` in CI
- Le dashboard Grafana sono esportate come JSON e versionato
- I SLO sono definiti come codice e monitorati automaticamente

### Dashboard Standards

Standard organizzativi per le dashboard:

1. **Gerarchia a tre livelli**:
   - **L1 — Executive Overview**: SLO, disponibilita, metriche business (una schermata, nessun dettaglio tecnico)
   - **L2 — Service Overview**: Golden signals per servizio, error budget, deployment markers
   - **L3 — Debug Detail**: Metriche dettagliate per componente, query lente, heap usage, thread count

2. **Naming convention**: `[Team] - [Servizio] - [Livello]` (es. "Backend - Payment API - L2 Overview")

3. **Regole di design**:
   - Massimo 15 pannelli per dashboard
   - Utilizzare variabili template per cluster, namespace, service
   - Time range default di 1 ora per dashboard operative, 24 ore per trend
   - Annotations per deploy e incidenti
   - Link tra dashboard correlate per facilitare il drill-down

### Alert Hygiene

Processo di manutenzione degli alert:

```
Revisione mensile:
1. Elencare tutti gli alert che sono scattati nel mese
2. Classificarli: azionabile / non azionabile / falso positivo
3. Per ogni alert non azionabile o falso positivo:
   - Se la soglia e sbagliata: correggerla
   - Se la metrica e irrilevante: eliminare l'alert
   - Se e ridondante: consolidare con un alert esistente
4. Verificare che ogni alert critico abbia un runbook aggiornato
5. Verificare che i canali di routing siano corretti
6. Tracciare il rapporto signal-to-noise e puntare a migliorarlo ogni mese
```

Metriche sugli alert da tracciare:

- **MTTA** (Mean Time to Acknowledge) — Tempo medio di presa in carico
- **MTTR** (Mean Time to Resolve) — Tempo medio di risoluzione
- **Alert volume** — Numero di alert per settimana, per team
- **Signal-to-noise ratio** — Percentuale di alert che hanno richiesto azione reale
- **Alert fatigue index** — Tempo medio prima dell'acknowledge (aumenta con il fatigue)

### Capacity Planning Basato su Metriche

Utilizzare le metriche storiche per prevedere le necessita future:

```promql
# Previsione dell'utilizzo CPU tra 30 giorni
predict_linear(
  avg_over_time(instance:node_cpu_utilization:ratio[7d])[30d:1d],
  30 * 24 * 3600
)

# Previsione dello spazio disco
predict_linear(
  node_filesystem_avail_bytes{mountpoint="/"}[30d],
  90 * 24 * 3600
) < 0

# Trend di crescita delle richieste
deriv(
  sum(increase(http_requests_total[1d]))[30d:1d]
)

# Rapporto risorse utilizzate vs allocate (efficienza)
sum(rate(container_cpu_usage_seconds_total[5m])) by (namespace)
/
sum(kube_pod_container_resource_requests{resource="cpu"}) by (namespace)
```

### Costo dell'Observability

L'observability ha costi significativi che devono essere gestiti attivamente:

**Metriche** — Ogni time series in Prometheus consuma circa 1-2 byte per campione. Con scrape interval di 15 secondi, una metrica genera ~5.760 campioni al giorno (~8-12 KB/giorno). Con 100.000 time series attive, il costo di storage e circa 1 GB/giorno prima della compressione.

Strategie di riduzione costi:

- Utilizzare recording rules per pre-aggregare metriche ad alta cardinalita
- Applicare `metric_relabel_configs` per eliminare metriche non necessarie (es. metriche Go runtime, metriche interne)
- Ridurre la cardinalita delle label (evitare label con valori ad alta cardinalita come user ID, request ID)
- Implementare retention differenziata: dati raw per 15 giorni, dati aggregati per 1 anno

**Log** — Il costo principale. Un'applicazione tipica genera 1-10 GB di log al giorno. Con Elasticsearch, ogni GB richiede circa 1.5-2 GB di storage con repliche.

Strategie:

- Log a livello strutturato (JSON) per ridurre la necessita di parsing costoso
- Campionamento dei log di debug e info in produzione
- Retention aggressiva: 7 giorni per debug, 30 per info/warn, 90 per error
- Utilizzare Loki al posto di Elasticsearch per ridurre i costi di indicizzazione del 90%

**Traces** — Il sampling e obbligatorio. Campionare il 100% dei trace in produzione e insostenibile. Con tail-based sampling al 10% + 100% degli errori, il volume e gestibile.

### Retention Policies

```yaml
# Policy di retention raccomandate
metriche:
  raw_data: 15 giorni (Prometheus locale)
  downsampled_5m: 6 mesi (Thanos/Cortex)
  downsampled_1h: 2 anni (Thanos/Cortex)

log:
  debug: 3 giorni
  info: 7 giorni
  warn: 30 giorni
  error: 90 giorni
  audit: 1 anno (requisiti compliance)

trace:
  raw_traces: 7 giorni
  aggregated_metrics: 30 giorni
  service_dependency_maps: 90 giorni

dashboard:
  definizioni: versionate in Git (indefinito)
  snapshot: 90 giorni
  annotations: 1 anno
```

---

## 12. Deep-Dive sui Tre Pilastri

### Metriche — Approfondimento

Le metriche rappresentano il pilastro piu efficiente dell'osservabilita in termini di rapporto informazione/costo. Una comprensione approfondita dei tipi di metriche e delle loro implicazioni architetturali e fondamentale per progettare sistemi di monitoraggio scalabili.

#### Cardinalita e Serie Temporali

La cardinalita e il prodotto cartesiano di tutti i valori unici di tutte le label associate a una metrica. Una metrica con 5 label, ciascuna con 10 valori possibili, genera potenzialmente 10^5 = 100.000 serie temporali. Questo fenomeno, noto come **cardinality explosion**, e la causa principale di problemi di performance e costo in Prometheus.

Regole pratiche per il controllo della cardinalita:

- Mai usare come label valori ad alta cardinalita: user ID, request ID, IP address, session ID, email
- Ogni nuova label moltiplica il numero di serie: aggiungere label solo quando necessario per il filtering o il raggruppamento nelle query
- Monitorare la cardinalita attivamente con `prometheus_tsdb_head_series` e impostare alert quando supera soglie predefinite
- Utilizzare `metric_relabel_configs` per eliminare label non necessarie prima dello storage

```promql
# Identificare le metriche con piu serie temporali
topk(10, count by (__name__) ({__name__!=""}))

# Serie temporali per job
count({job=~".+"}) by (job)

# Crescita delle serie negli ultimi 7 giorni
delta(prometheus_tsdb_head_series[7d])

# Metriche che contribuiscono maggiormente alla cardinalita
topk(20, count by (__name__, job) ({__name__!=""}))
```

#### Native Histograms (Prometheus 3.x)

A partire da Prometheus 3.x, i native histograms rappresentano un'evoluzione significativa rispetto agli histograms classici. Utilizzano bucket con confini esponenziali che si adattano automaticamente alla distribuzione dei dati, eliminando la necessita di configurare manualmente i bucket boundaries.

Vantaggi rispetto agli histogram classici:

- **Riduzione della cardinalita**: un singolo native histogram sostituisce decine di serie `_bucket`, riducendo la cardinalita di 10-50x per metrica
- **Precisione adattiva**: i bucket si adattano dinamicamente alla distribuzione, evitando la perdita di precisione dovuta a bucket mal configurati
- **Merge efficiente**: i native histograms possono essere aggregati tra istanze senza perdita di informazione, risolvendo il problema dell'aggregazione cross-instance dei quantili
- **Storage ridotto**: fino al 70% di riduzione dello spazio occupato rispetto agli histogram classici con bucket equivalenti

```promql
# Query su native histogram — calcolo quantile
histogram_quantile(0.95, sum(rate(http_request_duration_seconds[5m])))

# Confronto tra percentili con native histogram
histogram_quantile(0.50, http_request_duration_seconds)
histogram_quantile(0.90, http_request_duration_seconds)
histogram_quantile(0.99, http_request_duration_seconds)
```

#### Metriche di Business vs Metriche Tecniche

Un errore comune e concentrarsi esclusivamente sulle metriche tecniche (CPU, memoria, latenza) trascurando le metriche di business che collegano il comportamento del sistema agli obiettivi aziendali:

| Metrica Tecnica | Metrica di Business Corrispondente |
|-----------------|-----------------------------------|
| `http_requests_total` | `orders_placed_total` |
| `error_rate_5xx` | `payment_failures_total` |
| `request_duration_p99` | `checkout_completion_time_seconds` |
| `db_connections_active` | `concurrent_users` |
| `queue_depth` | `order_processing_backlog` |

Le metriche di business devono essere instrumentate direttamente nel codice applicativo e trattate con la stessa priorita delle metriche infrastrutturali.

### Log — Approfondimento

#### Structured Logging

Il logging strutturato (JSON) e il prerequisito per un'aggregazione efficiente. Ogni log entry dovrebbe contenere un insieme minimo di campi standardizzati:

```json
{
  "timestamp": "2026-05-24T14:30:00.123Z",
  "level": "ERROR",
  "service": "payment-api",
  "version": "2.4.1",
  "environment": "production",
  "host": "payment-api-7d8f9-abc12",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "message": "Payment processing failed",
  "error": {
    "type": "TimeoutException",
    "message": "Connection to payment gateway timed out after 5000ms",
    "stack": "com.example.payment.PaymentProcessor.charge(PaymentProcessor.java:142)..."
  },
  "context": {
    "order_id": "ORD-2026-789456",
    "amount": 149.99,
    "currency": "EUR",
    "retry_count": 2,
    "gateway": "stripe"
  }
}
```

Principi fondamentali del structured logging:

1. **Schema consistente** — Tutti i servizi devono aderire allo stesso schema di base. Campi come `timestamp`, `level`, `service`, `trace_id` devono essere presenti in ogni log entry.
2. **Livelli semantici** — `DEBUG` per sviluppo locale, `INFO` per eventi operativi normali, `WARN` per situazioni anomale ma gestite, `ERROR` per errori che richiedono attenzione, `FATAL` per errori irrecuperabili.
3. **Contesto ricco** — Includere sempre il contesto necessario per la diagnosi senza dover cercare altrove. L'obiettivo e che un singolo log entry contenga tutte le informazioni necessarie per comprendere l'evento.
4. **No PII nei log** — Mai loggare dati personali (email, numeri di carta, password). Utilizzare tokenizzazione o hashing se necessario per la correlazione.

#### Log Levels — Strategia di Produzione

In produzione, il livello di log predefinito dovrebbe essere `INFO`. Il livello `DEBUG` genera volumi insostenibili (tipicamente 10-50x il volume di `INFO`) e deve essere abilitato solo temporaneamente per la diagnosi di problemi specifici, idealmente solo su istanze specifiche.

Pattern di dynamic log level:

```
# Abilitare DEBUG per un singolo servizio via endpoint admin
POST /admin/log-level
{
  "level": "DEBUG",
  "duration_seconds": 300,
  "component": "payment.processor"
}
```

Questo approccio consente la diagnosi dettagliata senza impattare l'intero sistema e senza richiedere un redeploy.

### Trace — Approfondimento

#### Anatomia di uno Span

Ogni span contiene una struttura ricca di informazioni che va oltre il semplice tempo di inizio e fine:

```
Span {
  trace_id:    "4bf92f3577b34da6a3ce929d0e0e4736"
  span_id:     "00f067aa0ba902b7"
  parent_id:   "7a8c5f2e1d3b4a6c"
  name:        "POST /api/v1/payments"
  kind:        SERVER
  start_time:  2026-05-24T14:30:00.000Z
  end_time:    2026-05-24T14:30:00.342Z
  status:      ERROR
  attributes: {
    "http.method":       "POST"
    "http.url":          "https://api.example.com/api/v1/payments"
    "http.status_code":  500
    "service.name":      "payment-api"
    "service.version":   "2.4.1"
    "db.system":         "postgresql"
    "db.statement":      "INSERT INTO payments..."
  }
  events: [
    {
      name: "exception"
      time: 2026-05-24T14:30:00.340Z
      attributes: {
        "exception.type":    "TimeoutException"
        "exception.message": "Connection timed out"
      }
    }
  ]
  links: [
    { trace_id: "...", span_id: "...", attributes: {} }
  ]
}
```

I **links** collegano span a trace diversi, utili per operazioni asincrone (es. un messaggio in coda che genera un nuovo trace per l'elaborazione). Gli **events** registrano momenti significativi durante la vita dello span senza creare span figli separati.

#### Semantic Conventions di OpenTelemetry

Le semantic conventions definiscono nomi e tipi standardizzati per gli attributi degli span. L'adozione di queste convenzioni e fondamentale per l'interoperabilita tra strumenti e per la creazione di dashboard e alert riutilizzabili:

| Categoria | Attributi Chiave |
|-----------|-----------------|
| HTTP | `http.method`, `http.status_code`, `http.url`, `http.request.body.size` |
| Database | `db.system`, `db.statement`, `db.operation`, `db.name` |
| Messaging | `messaging.system`, `messaging.operation`, `messaging.destination.name` |
| RPC | `rpc.system`, `rpc.method`, `rpc.service` |
| Cloud | `cloud.provider`, `cloud.region`, `cloud.availability_zone` |
| Container | `container.id`, `container.name`, `container.image.name` |

---

## 13. OpenTelemetry Collector — Architettura Avanzata

### Pipeline Model

L'OpenTelemetry Collector implementa un modello a pipeline dove i dati fluiscono attraverso tre stadi: ricezione, elaborazione ed esportazione. Ogni pipeline e tipizzata per uno dei tre segnali (traces, metrics, logs) e puo avere configurazioni indipendenti.

```
                  ┌─────────────┐
                  │  Receivers   │
                  │  (OTLP,      │
                  │  Prometheus, │
                  │  Jaeger,     │
                  │  Kafka...)   │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │ Processors   │
                  │ (batch,      │
                  │  filter,     │
                  │  transform,  │
                  │  sampling...) │
                  └──────┬──────┘
                         │
                  ┌──────▼──────┐
                  │  Exporters   │
                  │ (OTLP,       │
                  │  Prometheus, │
                  │  Loki,       │
                  │  Jaeger...)  │
                  └─────────────┘
```

Le pipeline sono definite nella sezione `service.pipelines` della configurazione. Un singolo Collector puo gestire pipeline multiple per segnali diversi, e lo stesso receiver o exporter puo essere condiviso tra pipeline.

### Receiver — Catalogo Avanzato

I receiver sono il punto di ingresso dei dati nel Collector. Si dividono in due categorie:

**Push-based** — Ascoltano su un endpoint e ricevono dati inviati dalle applicazioni:

- `otlp`: receiver OTLP via gRPC (porta 4317) e HTTP (porta 4318), il receiver primario per le applicazioni instrumentate con OpenTelemetry SDK
- `jaeger`: supporta i protocolli legacy Jaeger (Thrift Compact su UDP 6831, gRPC su 14250)
- `zipkin`: riceve span nel formato Zipkin
- `kafka`: consuma messaggi da topic Kafka contenenti dati di telemetria
- `syslog`: riceve messaggi syslog via TCP/UDP (RFC 5424, RFC 3164)
- `filelog`: legge e parsa log da file locali con supporto multilinea e operatori di parsing

**Pull-based** — Interrogano attivamente i target per raccogliere dati:

- `prometheus`: implementa un Prometheus scraper completo con supporto per service discovery
- `hostmetrics`: raccoglie metriche del sistema operativo (CPU, memoria, disco, rete) senza bisogno di node_exporter
- `kubeletstats`: interroga l'API kubelet per metriche dei container Kubernetes

```yaml
receivers:
  filelog:
    include:
      - /var/log/app/*.log
    operators:
      - type: json_parser
        timestamp:
          parse_from: attributes.timestamp
          layout: "%Y-%m-%dT%H:%M:%S.%LZ"
        severity:
          parse_from: attributes.level
          mapping:
            error: ["ERROR", "FATAL"]
            warn: ["WARN", "WARNING"]
            info: ["INFO"]
            debug: ["DEBUG"]
      - type: move
        from: attributes.message
        to: body

  hostmetrics:
    collection_interval: 30s
    scrapers:
      cpu:
        metrics:
          system.cpu.utilization:
            enabled: true
      memory:
        metrics:
          system.memory.utilization:
            enabled: true
      disk: {}
      network: {}
      filesystem: {}
      load: {}
      processes: {}
```

### Processor — Catalogo Avanzato

I processor trasformano, filtrano e arricchiscono i dati tra receiver ed exporter. L'ordine dei processor nella pipeline e significativo.

**Processor critici per la produzione:**

```yaml
processors:
  # Memory Limiter — DEVE essere il primo processor
  # Previene crash per out-of-memory
  memory_limiter:
    check_interval: 1s
    limit_mib: 4096
    spike_limit_mib: 1024

  # Filter — elimina dati non necessari
  filter:
    error_mode: ignore
    traces:
      span:
        - 'attributes["http.route"] == "/health"'
        - 'attributes["http.route"] == "/ready"'
    metrics:
      metric:
        - 'name == "go_gc_duration_seconds"'
        - 'name == "go_memstats_alloc_bytes"'
    logs:
      log_record:
        - 'severity_number < 9'  # elimina DEBUG

  # Transform — modifica attributi con OTTL
  transform:
    trace_statements:
      - context: span
        statements:
          - truncate_all(attributes, 256)
          - set(attributes["deployment.environment"], "production")
    log_statements:
      - context: log
        statements:
          - merge_maps(attributes, ExtractPatterns(body, "user_id=(?P<user_id>[a-f0-9]+)"), "insert")

  # Probabilistic Sampler — campionamento head-based
  probabilistic_sampler:
    sampling_percentage: 15
    hash_seed: 22

  # Group by Trace — necessario per tail sampling
  groupbytrace:
    wait_duration: 10s
    num_traces: 200000

  # K8s Attributes — arricchisce con metadati Kubernetes
  k8sattributes:
    auth_type: "serviceAccount"
    extract:
      metadata:
        - k8s.pod.name
        - k8s.namespace.name
        - k8s.deployment.name
        - k8s.node.name
      labels:
        - tag_name: app
          key: app.kubernetes.io/name
```

### Deployment Pattern — Agent vs Gateway

Due pattern architetturali principali per il deployment del Collector:

**Agent Pattern** — Un Collector per nodo/host, eseguito come DaemonSet in Kubernetes o come sidecar. Riceve dati dalle applicazioni locali, esegue pre-processing leggero (batch, resource enrichment) e inoltra a un Collector centralizzato.

**Gateway Pattern** — Un pool di Collector centralizzati che ricevono dati da tutti gli agent. Eseguono processing pesante (tail sampling, aggregazione) ed esportano verso i backend finali.

```
App → Agent Collector (locale) → Gateway Collector (centralizzato) → Backend
```

Il pattern combinato agent + gateway e raccomandato per ambienti di produzione perche:

- L'agent riduce la latenza di invio e gestisce buffering locale in caso di interruzioni
- Il gateway centralizza la logica di processing complessa (tail sampling richiede visione globale dei trace)
- Scaling indipendente: gli agent scalano con l'infrastruttura, i gateway con il volume di dati

### Grafana Alloy

Grafana Alloy (introdotto nel 2025) e una pipeline di telemetria unificata che sostituisce Promtail, Grafana Agent e OpenTelemetry Collector in un singolo binario. Supporta la raccolta di metriche (Prometheus), log (Loki), trace (Tempo) e profili (Pyroscope) con un linguaggio di configurazione dichiarativo basato su River (ora rinominato Alloy configuration language).

```alloy
// Configurazione Alloy — esempio completo
otelcol.receiver.otlp "default" {
  grpc { endpoint = "0.0.0.0:4317" }
  http { endpoint = "0.0.0.0:4318" }
  output {
    metrics = [otelcol.processor.batch.default.input]
    logs    = [otelcol.processor.batch.default.input]
    traces  = [otelcol.processor.batch.default.input]
  }
}

otelcol.processor.batch "default" {
  timeout = "5s"
  send_batch_size = 8192
  output {
    metrics = [otelcol.exporter.prometheus.default.input]
    logs    = [otelcol.exporter.loki.default.input]
    traces  = [otelcol.exporter.otlp.tempo.input]
  }
}

prometheus.scrape "app_metrics" {
  targets    = discovery.kubernetes.pods.targets
  forward_to = [prometheus.remote_write.mimir.receiver]
}

prometheus.remote_write "mimir" {
  endpoint {
    url = "http://mimir:9009/api/v1/push"
  }
}
```

---

## 14. Prometheus Avanzato — Federation e Long-Term Storage

### Federation

La federation di Prometheus permette a un server Prometheus di effettuare scrape da altri server Prometheus, creando una gerarchia che consente di scalare il monitoring oltre i limiti di una singola istanza.

#### Hierarchical Federation

Un Prometheus di livello superiore (federation server) raccoglie metriche aggregate da Prometheus di livello inferiore (data center, cluster). Ogni livello effettua pre-aggregazione tramite recording rules, riducendo il volume di dati che fluisce verso l'alto.

```yaml
# prometheus-federation.yml — Prometheus di livello superiore
scrape_configs:
  - job_name: "federation-dc-eu"
    honor_labels: true
    metrics_path: "/federate"
    params:
      "match[]":
        # Solo metriche pre-aggregate (prefisso job: o cluster:)
        - '{__name__=~"job:.+"}'
        - '{__name__=~"cluster:.+"}'
        - '{__name__=~"namespace:.+"}'
    static_configs:
      - targets:
          - "prometheus-dc-eu.example.com:9090"
        labels:
          datacenter: "eu-west-1"

  - job_name: "federation-dc-us"
    honor_labels: true
    metrics_path: "/federate"
    params:
      "match[]":
        - '{__name__=~"job:.+"}'
        - '{__name__=~"cluster:.+"}'
    static_configs:
      - targets:
          - "prometheus-dc-us.example.com:9090"
        labels:
          datacenter: "us-east-1"
```

#### Cross-Service Federation

Pattern alternativo dove ogni team ha il proprio Prometheus per le metriche del proprio dominio, e un Prometheus centrale raccoglie solo le metriche SLI/SLO necessarie per la visione globale. Questo garantisce l'autonomia dei team mantenendo una vista unificata sulla salute del sistema.

### Thanos — Architettura

Thanos estende Prometheus per fornire storage a lungo termine, alta disponibilita e query globali multi-cluster. Si compone di diversi componenti distribuiti:

**Thanos Sidecar** — Container che affianca ogni istanza Prometheus. Carica i blocchi TSDB su object storage (S3, GCS, Azure Blob) e serve le query per i dati recenti ancora in Prometheus.

**Thanos Store Gateway** — Serve i dati storici dall'object storage, implementando caching e sharding per query efficienti su grandi volumi.

**Thanos Compactor** — Esegue downsampling e compaction dei blocchi storici. Produce riduzioni a 5 minuti e 1 ora per query su periodi lunghi. Gestisce anche la retention con eliminazione automatica dei blocchi scaduti.

**Thanos Query (Querier)** — Punto di ingresso per le query PromQL. Fan-out verso tutti i Sidecar e gli Store Gateway, con deduplicazione automatica delle serie replicate.

**Thanos Ruler** — Valuta recording rules e alerting rules su dati distribuiti, scrivendo i risultati nell'object storage.

```yaml
# docker-compose — Thanos essenziale
services:
  prometheus-01:
    image: prom/prometheus:v2.54.0
    volumes:
      - ./prometheus-01.yml:/etc/prometheus/prometheus.yml
      - prometheus-01-data:/prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.path=/prometheus
      - --storage.tsdb.min-block-duration=2h
      - --storage.tsdb.max-block-duration=2h  # Necessario per Thanos

  thanos-sidecar-01:
    image: thanosio/thanos:v0.36.1
    command:
      - sidecar
      - --tsdb.path=/prometheus
      - --prometheus.url=http://prometheus-01:9090
      - --objstore.config-file=/etc/thanos/bucket.yml
      - --grpc-address=0.0.0.0:10901
    volumes:
      - prometheus-01-data:/prometheus:ro
      - ./bucket.yml:/etc/thanos/bucket.yml

  thanos-query:
    image: thanosio/thanos:v0.36.1
    command:
      - query
      - --http-address=0.0.0.0:9090
      - --store=thanos-sidecar-01:10901
      - --store=thanos-sidecar-02:10901
      - --store=thanos-store:10901
      - --query.replica-label=replica

  thanos-store:
    image: thanosio/thanos:v0.36.1
    command:
      - store
      - --data-dir=/var/thanos/store
      - --objstore.config-file=/etc/thanos/bucket.yml
      - --grpc-address=0.0.0.0:10901
      - --index-cache-size=2GB
      - --chunk-pool-size=4GB

  thanos-compactor:
    image: thanosio/thanos:v0.36.1
    command:
      - compact
      - --data-dir=/var/thanos/compact
      - --objstore.config-file=/etc/thanos/bucket.yml
      - --retention.resolution-raw=15d
      - --retention.resolution-5m=90d
      - --retention.resolution-1h=365d
      - --compact.concurrency=4
      - --downsample.concurrency=4
      - --wait
```

### Grafana Mimir

Mimir e l'alternativa a Thanos sviluppata da Grafana Labs, progettata per scalabilita orizzontale nativa e multi-tenancy. Utilizza un'architettura ad anello (ring-based) per distribuire il carico tra le istanze.

Differenze chiave rispetto a Thanos:

| Aspetto | Thanos | Mimir |
|---------|--------|-------|
| Architettura | Sidecar + componenti distribuiti | Microservizi con ring-based sharding |
| Multi-tenancy | Limitata (via external labels) | Nativa (header X-Scope-OrgID) |
| Ingestion | Via Prometheus remote_write + sidecar | Solo remote_write (pull eliminato) |
| Compaction | Componente dedicato | Integrata nel compactor con sharding |
| Query | Fan-out ai sidecar/store | Query su store unificato |
| Scalabilita | Verticale per componente | Orizzontale nativa per ogni componente |
| Complessita operativa | Media (molti componenti) | Media-alta (ring management) |

Configurazione Mimir essenziale:

```yaml
# mimir-config.yml
multitenancy_enabled: true

blocks_storage:
  backend: s3
  s3:
    bucket_name: mimir-blocks
    endpoint: s3.eu-west-1.amazonaws.com
    region: eu-west-1
  tsdb:
    dir: /data/tsdb
    block_ranges_period: [2h]
    retention_period: 24h

compactor:
  data_dir: /data/compactor
  sharding_ring:
    kvstore:
      store: memberlist
  deletion_delay: 2h

distributor:
  ring:
    kvstore:
      store: memberlist
  instance_limits:
    max_ingestion_rate: 100000

ingester:
  ring:
    kvstore:
      store: memberlist
    replication_factor: 3

limits:
  max_global_series_per_user: 5000000
  max_global_series_per_metric: 100000
  ingestion_rate: 50000
  ingestion_burst_size: 500000
  compactor_blocks_retention_period: 365d

ruler:
  alertmanager_url: http://alertmanager:9093
  enable_api: true
  rule_path: /data/rules

ruler_storage:
  backend: s3
  s3:
    bucket_name: mimir-rules
```

### PromQL Avanzato — Pattern per la Produzione

```promql
# Subquery — rate aggregato su finestre mobili
max_over_time(
  sum(rate(http_requests_total[5m]))[1h:5m]
)

# Offset — confronto con il giorno precedente
sum(rate(http_requests_total[5m]))
/ sum(rate(http_requests_total[5m] offset 1d))

# Absent — rilevare la scomparsa di una metrica
absent(up{job="payment-service"})

# Changes — contare il numero di cambi di valore di un gauge
changes(kube_deployment_spec_replicas[1h])

# Resets — contare i reset di un counter (riavvii del processo)
resets(process_start_time_seconds[1d])

# Clamp — limitare i valori in un range
clamp_min(
  1 - (sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))),
  0
)

# Label join — combinare metriche con label diverse
label_join(
  kube_pod_info,
  "pod_label", ",",
  "label_app", "label_version"
)

# Group — ridurre le label mantenendo solo quelle specificate
group without (instance, pod) (up{job="api"})
```

---

## 15. Ecosistema Grafana — LGTM Stack

### Panoramica LGTM

Lo stack LGTM (Loki, Grafana, Tempo, Mimir) rappresenta l'approccio open source di Grafana Labs all'osservabilita completa. Ogni componente gestisce uno dei pilastri della telemetria, con Grafana come layer di visualizzazione unificato.

| Componente | Segnale | Funzione |
|-----------|---------|----------|
| **Mimir** | Metriche | Long-term storage per Prometheus con scalabilita orizzontale |
| **Loki** | Log | Aggregazione log cost-effective con indicizzazione solo sulle label |
| **Tempo** | Trace | Storage di trace distribuiti senza indicizzazione, lookup per trace ID |
| **Grafana** | Visualizzazione | Dashboard unificate con correlazione cross-signal |
| **Alloy** | Collection | Pipeline di raccolta unificata per tutti i segnali |
| **Pyroscope** | Profiling | Continuous profiling per analisi delle performance a livello di codice |

Il vantaggio principale dello stack LGTM e l'integrazione nativa: da una dashboard Grafana e possibile navigare da una metrica (Mimir) ai log correlati (Loki) al trace specifico (Tempo) fino al profilo di performance (Pyroscope), il tutto con un singolo click.

### Grafana Tempo — Approfondimento

Tempo adotta un approccio radicalmente diverso rispetto a Jaeger con Elasticsearch: non indicizza i dati dei trace. I trace vengono scritti come blob in object storage e recuperati tramite lookup diretto per trace ID. Questa architettura riduce drasticamente i costi (fino al 90% rispetto a soluzioni indicizzate) sacrificando la possibilita di cercare trace senza conoscere l'ID.

Per ovviare a questa limitazione, Tempo introduce due meccanismi:

1. **Metrics Generator** — Genera automaticamente metriche RED (rate, errors, duration) e service graph metrics dai trace, scrivendo i risultati in Prometheus/Mimir. Questo permette di trovare trace problematici partendo dalle metriche.

2. **TraceQL** — Linguaggio di query per cercare trace in base agli attributi degli span:

```traceql
# Cercare trace con errori HTTP nel servizio payment
{ resource.service.name = "payment-api" && span.http.status_code >= 500 }

# Trace con latenza superiore a 2 secondi
{ span.http.method = "POST" && duration > 2s }

# Trace che attraversano sia il servizio auth che il servizio payment
{ resource.service.name = "auth-api" } >> { resource.service.name = "payment-api" }

# Trace con query database lente
{ span.db.system = "postgresql" && duration > 500ms }

# Pipeline di query — contare trace per status code
{ resource.service.name = "api-gateway" } | count() by (span.http.status_code)

# Cercare trace con un attributo specifico
{ span.order.amount > 1000 && span.http.status_code = 200 }
```

### Grafana OnCall e IRM

**Grafana OnCall** e una soluzione open source per la gestione delle rotazioni on-call e l'escalation degli incidenti. Si integra nativamente con Alertmanager e Grafana Alerting per fornire:

- **Rotazioni on-call** — Schedules settimanali/giornaliere con supporto per override, swap e vacanze
- **Escalation chains** — Politiche di escalation multi-livello: se il primo on-call non risponde entro N minuti, escala al secondo, poi al team lead, poi al manager
- **Multi-channel notification** — SMS, telefono, Slack, Telegram, email, webhook
- **ChatOps** — Integrazione bidirezionale con Slack: acknowledge, resolve e note direttamente dalla chat

**Grafana IRM (Incident Response Management)** — Evoluzione di OnCall che aggiunge la gestione strutturata degli incidenti:

- Dichiarazione formale dell'incidente con severity e impatto
- Timeline automatica degli eventi con correlazione ai dati di osservabilita
- Assegnazione ruoli (Incident Commander, Communications Lead, Technical Lead)
- Post-incident review con template strutturati
- Integrazione con sistemi di ticketing (Jira, ServiceNow)

Configurazione OnCall con Alertmanager:

```yaml
# alertmanager.yml — integrazione Grafana OnCall
receivers:
  - name: "grafana-oncall"
    webhook_configs:
      - url: "https://oncall.example.com/integrations/v1/alertmanager/abc123/"
        send_resolved: true
        max_alerts: 100

route:
  receiver: "grafana-oncall"
  routes:
    - receiver: "grafana-oncall"
      matchers:
        - severity =~ "critical|high"
      group_wait: 15s
      repeat_interval: 1h
```

### Pyroscope — Continuous Profiling

Pyroscope (acquisito da Grafana Labs) aggiunge il quarto segnale dell'osservabilita: il profiling continuo. A differenza del profiling on-demand tradizionale, il continuous profiling raccoglie dati costantemente in produzione con overhead minimo (<2% CPU).

Casi d'uso:

- Identificare funzioni che consumano piu CPU o memoria in produzione
- Confrontare profili tra versioni diverse di un servizio (prima/dopo un deploy)
- Correlare picchi di CPU/memoria con trace specifici (Tempo -> Pyroscope)
- Analisi dei costi cloud: capire quale codice contribuisce maggiormente al consumo di risorse

---

## 16. Implementazione SLI/SLO/SLA

### Framework di Implementazione

L'implementazione efficace degli SLO richiede un processo strutturato che collega gli obiettivi di affidabilita agli indicatori tecnici:

**Passo 1 — Definire i Critical User Journeys (CUJ)**

Identificare i percorsi utente piu importanti per il business. Per un e-commerce:

1. Ricerca prodotti e navigazione catalogo
2. Aggiunta al carrello
3. Processo di checkout e pagamento
4. Visualizzazione stato ordine

**Passo 2 — Selezionare gli SLI per ogni CUJ**

Per ogni journey, scegliere gli SLI che riflettono l'esperienza dell'utente:

| CUJ | SLI Disponibilita | SLI Latenza |
|-----|-------------------|-------------|
| Ricerca prodotti | % richieste con status < 500 | % richieste con latenza < 200ms |
| Checkout | % transazioni completate senza errore | % checkout completati in < 3s |
| Stato ordine | % richieste API con status 200 | % risposte in < 500ms |

**Passo 3 — Definire gli SLO**

Impostare target realistici basati sui dati storici. Non partire da 99.99% se il sistema attuale e al 99.5%. Approccio incrementale:

```
SLO iniziale (basato su storico):
  - Disponibilita: 99.5% su 30 giorni (downtime ammesso: 3h 36m)
  - Latenza p99: < 1s per il 99% delle richieste su 30 giorni

SLO target (a 6 mesi):
  - Disponibilita: 99.9% su 30 giorni (downtime ammesso: 43m)
  - Latenza p99: < 500ms per il 99.5% delle richieste su 30 giorni
```

### Error Budget e Burn Rate

L'error budget quantifica quanto margine di errore resta prima di violare l'SLO. Il burn rate indica la velocita di consumo dell'error budget.

#### Alert Multi-Finestra (Strategia Google)

Google SRE raccomanda un approccio multi-finestra per gli alert basati su burn rate. L'idea e combinare una finestra breve (sensibilita rapida) con una finestra lunga (riduzione falsi positivi):

```yaml
# Recording rules per SLO
groups:
  - name: slo_recording_rules
    rules:
      # Error rate su diverse finestre temporali
      - record: slo:http_error_rate:ratio_rate5m
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          / sum(rate(http_requests_total[5m]))

      - record: slo:http_error_rate:ratio_rate30m
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[30m]))
          / sum(rate(http_requests_total[30m]))

      - record: slo:http_error_rate:ratio_rate1h
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[1h]))
          / sum(rate(http_requests_total[1h]))

      - record: slo:http_error_rate:ratio_rate6h
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[6h]))
          / sum(rate(http_requests_total[6h]))

      # Error budget remaining (SLO 99.9%)
      - record: slo:error_budget:remaining
        expr: |
          1 - (
            sum(increase(http_requests_total{status=~"5.."}[30d]))
            / sum(increase(http_requests_total[30d]))
          ) / 0.001

  - name: slo_alerts
    rules:
      # Alert burn rate 14.4x su 1h/5m — ticket P1 in 2 ore
      - alert: SLOHighBurnRate_Fast
        expr: |
          slo:http_error_rate:ratio_rate5m > (14.4 * 0.001)
          and
          slo:http_error_rate:ratio_rate1h > (14.4 * 0.001)
        for: 2m
        labels:
          severity: critical
          slo: "availability"
        annotations:
          summary: "Burn rate 14.4x — error budget esaurito in 2 ore"
          error_budget_remaining: '{{ printf "%.1f" (query "slo:error_budget:remaining") }}%'

      # Alert burn rate 6x su 6h/30m — ticket P1 in 5 ore
      - alert: SLOHighBurnRate_Medium
        expr: |
          slo:http_error_rate:ratio_rate30m > (6 * 0.001)
          and
          slo:http_error_rate:ratio_rate6h > (6 * 0.001)
        for: 5m
        labels:
          severity: warning
          slo: "availability"
        annotations:
          summary: "Burn rate 6x — error budget esaurito in 5 ore"

      # Alert burn rate 1x su 3d/6h — ticket P2, indagare durante orario lavorativo
      - alert: SLOSlowBurnRate
        expr: |
          slo:http_error_rate:ratio_rate6h > (1 * 0.001)
          and
          slo:http_error_rate:ratio_rate3d > (1 * 0.001)
        for: 30m
        labels:
          severity: info
          slo: "availability"
        annotations:
          summary: "Burn rate 1x — error budget in consumo costante"
```

### SLO as Code — Strumenti

**Sloth** — Generatore di recording rules e alerting rules Prometheus a partire da definizioni SLO dichiarative:

```yaml
# sloth-slo.yml
version: "prometheus/v1"
service: "payment-api"
labels:
  team: "payments"
  tier: "critical"

slos:
  - name: "requests-availability"
    objective: 99.9
    description: "Percentuale di richieste HTTP che non restituiscono errore 5xx"
    sli:
      events:
        error_query: sum(rate(http_requests_total{job="payment-api",status=~"5.."}[{{.window}}]))
        total_query: sum(rate(http_requests_total{job="payment-api"}[{{.window}}]))
    alerting:
      name: PaymentAPIAvailability
      labels:
        team: payments
      annotations:
        runbook: "https://runbooks.example.com/payment-api/availability"
      page_alert:
        labels:
          severity: critical
      ticket_alert:
        labels:
          severity: warning

  - name: "requests-latency"
    objective: 99.5
    description: "Percentuale di richieste HTTP con latenza sotto 300ms"
    sli:
      events:
        error_query: |
          sum(rate(http_requests_total{job="payment-api"}[{{.window}}]))
          - sum(rate(http_request_duration_seconds_bucket{job="payment-api",le="0.3"}[{{.window}}]))
        total_query: sum(rate(http_requests_total{job="payment-api"}[{{.window}}]))
    alerting:
      name: PaymentAPILatency
      page_alert:
        labels:
          severity: critical
```

Sloth genera automaticamente tutte le recording rules, le alerting rules con multi-window burn rate, e i pannelli Grafana per la dashboard SLO.

**Pyrra** — Alternativa Kubernetes-native che opera come controller e genera PrometheusRule CRD:

```yaml
apiVersion: pyrra.dev/v1alpha1
kind: ServiceLevelObjective
metadata:
  name: payment-api-availability
  namespace: monitoring
spec:
  target: "99.9"
  window: 30d
  indicator:
    ratio:
      errors:
        metric: http_requests_total{job="payment-api",status=~"5.."}
      total:
        metric: http_requests_total{job="payment-api"}
```

### Error Budget Policy

L'error budget policy definisce le azioni da intraprendere in base al livello di consumo dell'error budget:

```
Error Budget Policy — Payment API (SLO 99.9%)

Budget > 75% rimanente:
  - Operazioni normali
  - Deploy con procedura standard
  - Feature development prioritario

Budget 50-75% rimanente:
  - Review delle cause di consumo
  - Aumentare la copertura dei test prima dei deploy
  - Canary deployment obbligatorio

Budget 25-50% rimanente:
  - Blocco dei deploy non critici
  - Team dedica 50% del tempo alla reliability
  - Review architetturale delle aree problematiche

Budget < 25% rimanente:
  - Freeze completo dei deploy
  - Tutto il team dedicato alla reliability
  - Incident review per ogni evento che consuma budget
  - Escalation al management se necessario

Budget esaurito:
  - Nessun deploy fino al recupero
  - Post-mortem obbligatorio
  - Piano di rimedio con timeline
```

---

## 17. Distributed Tracing — Pattern Avanzati

### Tracing di Operazioni Asincrone

Il tracing di operazioni asincrone (code di messaggi, eventi, job batch) richiede pattern diversi rispetto alle chiamate HTTP sincrone.

#### Pattern: Linked Traces per Code di Messaggi

Quando un messaggio viene pubblicato in una coda (Kafka, RabbitMQ, SQS), il trace del produttore termina con la pubblicazione. Il consumatore crea un nuovo trace con un link al trace originale:

```python
# Produttore — crea uno span e propaga il context nel messaggio
with tracer.start_as_current_span("publish_order_event") as span:
    span.set_attribute("messaging.system", "kafka")
    span.set_attribute("messaging.destination.name", "orders")

    # Il context viene serializzato negli header del messaggio
    headers = {}
    inject(headers)  # W3C TraceContext propagation
    kafka_producer.send("orders", value=order_data, headers=headers)

# Consumatore — estrae il context e crea un link
def process_message(message):
    # Estrae il context dal messaggio
    parent_ctx = extract(message.headers)
    link = trace.Link(parent_ctx)

    with tracer.start_as_current_span(
        "process_order_event",
        links=[link],
        kind=SpanKind.CONSUMER
    ) as span:
        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.operation", "process")
        # elaborazione del messaggio
```

#### Pattern: Saga Tracing

Nelle architetture basate su saga (sequenza di transazioni distribuite con compensazioni), il tracing deve catturare sia il percorso di successo che le compensazioni:

```
Trace di una Saga — Ordine E-commerce

[Root Span: CreateOrder]
  ├── [Span: ReserveInventory] ─── OK (200ms)
  ├── [Span: ProcessPayment] ───── OK (450ms)
  ├── [Span: CreateShipment] ───── ERROR (timeout)
  │   └── [Event: ShipmentServiceUnavailable]
  ├── [Span: CompensatePayment] ── OK (refund, 300ms)
  │   └── [Link: -> original ProcessPayment span]
  └── [Span: CompensateInventory] ─ OK (release, 150ms)
      └── [Link: -> original ReserveInventory span]

Status: ERROR
Duration: 1.3s
```

Ogni span di compensazione e collegato tramite link allo span dell'operazione originale che sta compensando, permettendo la ricostruzione completa del flusso.

### TraceQL — Query Avanzate

TraceQL (Grafana Tempo) permette query strutturali sui trace che non sono possibili con i linguaggi di query tradizionali:

```traceql
# Trace dove il servizio A chiama il servizio B
# e la chiamata al servizio B e lenta
{ resource.service.name = "api-gateway" }
  >> { resource.service.name = "payment-api" && duration > 1s }

# Trace con gap temporali (indicano attese su code o lock)
{ duration > 5s && span.childCount = 0 }

# Trace con fan-out elevato (un servizio chiama molti downstream)
{ span.childCount > 10 }

# Trace che toccano il database e hanno errori
{ span.db.system = "postgresql" } && { status = error }

# Confronto di latenza tra servizi per lo stesso trace
select(
  { resource.service.name = "auth-api" } | avg(duration),
  { resource.service.name = "payment-api" } | avg(duration)
)
```

### Service Dependency Maps

I service dependency maps vengono generati automaticamente dai dati di tracing e forniscono una vista topologica in tempo reale dell'architettura. Configurazione in Grafana con Tempo:

```yaml
# In grafana datasources
- name: Tempo
  type: tempo
  jsonData:
    serviceMap:
      datasourceUid: prometheus  # Le metriche RED generate da Tempo
    nodeGraph:
      enabled: true
    tracesToMetrics:
      datasourceUid: prometheus
      tags:
        - key: service.name
          value: service
    tracesToLogs:
      datasourceUid: loki
      tags:
        - key: service.name
          value: service_name
      filterByTraceID: true
      filterBySpanID: true
```

La mappa mostra per ogni connessione tra servizi: rate di richieste, tasso di errore e latenza p95. I nodi rossi indicano servizi con error rate elevato, i nodi gialli indicano latenza anomala.

---

## 18. Confronto Soluzioni di Log Aggregation

### Matrice di Confronto Dettagliata

| Criterio | ELK Stack | Grafana Loki | Datadog Logs |
|----------|-----------|-------------|--------------|
| **Modello** | Self-hosted / Elastic Cloud | Self-hosted / Grafana Cloud | SaaS |
| **Indicizzazione** | Full-text (inverted index) | Solo label (no content index) | Full-text + proprietaria |
| **Query Language** | Query DSL / KQL | LogQL | Filtri + Datadog query |
| **Ricerca** | Full-text istantanea | Filtra label, poi grep sequenziale | Full-text istantanea |
| **Costo storage** | Alto (1.5-2x dati raw con repliche) | Basso (10-100x meno di ELK) | Variabile (per GB ingeriti) |
| **Costo operativo** | Alto (JVM tuning, shard mgmt) | Basso-medio | Zero (managed) |
| **Scalabilita** | Orizzontale (complessa) | Orizzontale (semplice) | Trasparente |
| **Integrazione metriche** | Via Kibana + Metricbeat | Nativa con Grafana + Prometheus | Nativa (piattaforma unica) |
| **Integrazione trace** | Via Elastic APM | Nativa con Tempo | Nativa (Datadog APM) |
| **Retention** | ILM con hot/warm/cold tiers | Compactor con retention per tenant | Configurabile per piano |
| **Multi-tenancy** | Limitata (indici separati) | Nativa (header X-Scope-OrgID) | Nativa (Organizations) |
| **Alerting** | Elastic Alerting / Watcher | Loki ruler + Alertmanager | Monitors nativi |

### Guida alla Scelta

**Scegliere ELK quando:**

- Serve ricerca full-text performante su grandi volumi (es. analisi di log non strutturati legacy)
- L'organizzazione ha gia competenze Elasticsearch consolidate
- Servono funzionalita avanzate di analisi (ML anomaly detection, geo-analysis)
- Il budget per infrastruttura e sufficiente (ELK richiede hardware significativo)

**Scegliere Loki quando:**

- Il costo e un driver primario (Loki costa 10-100x meno di ELK per lo stesso volume)
- I log sono strutturati (JSON) e filtrabili per label
- Si usa gia Grafana come piattaforma di visualizzazione
- Si preferisce un approccio "grep distribuito" rispetto alla ricerca full-text
- Il team ha competenze Prometheus/PromQL (LogQL e simile)

**Scegliere Datadog quando:**

- Si preferisce una soluzione completamente gestita senza overhead operativo
- Serve correlazione immediata tra log, metriche, trace e profili in un'unica piattaforma
- Il budget permette i costi SaaS (tipicamente piu alto per grandi volumi)
- Il team e piccolo e non puo dedicare risorse alla gestione dell'infrastruttura di observability

### Migrazione da ELK a Loki

Pattern di migrazione graduale per ridurre i costi mantenendo le funzionalita:

1. **Fase 1** — Deploy Loki in parallelo. Inviare i nuovi log a entrambi i sistemi con doppio shipping (Filebeat -> ELK, Promtail -> Loki)
2. **Fase 2** — Ricreare le dashboard e gli alert principali in Grafana/Loki. Validare che i risultati siano equivalenti
3. **Fase 3** — Spostare il traffico di lettura su Loki per i casi d'uso che non richiedono full-text search
4. **Fase 4** — Mantenere ELK solo per i log che richiedono ricerca full-text (audit log, compliance) e migrare tutto il resto su Loki
5. **Fase 5** — Ridimensionare il cluster ELK in base al volume residuo

Risparmio tipico: 60-80% sulla spesa infrastrutturale per log aggregation.

---

## 19. AIOps e Anomaly Detection

### Introduzione all'AIOps

AIOps (Artificial Intelligence for IT Operations) applica tecniche di machine learning ai dati di osservabilita per automatizzare il rilevamento di anomalie, la correlazione di eventi e, in scenari avanzati, la remediation automatica.

Secondo il Grafana Observability Survey 2025, il 71% delle organizzazioni che utilizzano soluzioni di osservabilita adotta funzionalita basate su AI, con un aumento del 26% rispetto al 2024.

### Anomaly Detection — Approcci

#### Anomaly Detection Statistica

Approcci basati su modelli statistici classici, adatti per metriche con pattern regolari:

- **Z-score / Deviazioni standard** — Segnala anomalia quando il valore devia di N deviazioni standard dalla media mobile. Semplice ma inefficace per metriche con stagionalita o trend.

- **Seasonal Decomposition** — Scompone la serie temporale in trend, stagionalita e residuo. Anomalie nel residuo indicano comportamento anomalo. Efficace per metriche con pattern giornalieri/settimanali (es. traffico web).

- **Exponential Smoothing (Holt-Winters)** — Modello predittivo che gestisce trend e stagionalita. Genera bande di previsione e segnala anomalia quando il valore osservato esce dalla banda.

```promql
# Anomaly detection semplice con PromQL
# Deviazione dalla media su 7 giorni
(
  http_requests_total
  - avg_over_time(http_requests_total[7d])
)
/ stddev_over_time(http_requests_total[7d])
> 3  # Piu di 3 deviazioni standard
```

#### Anomaly Detection con Machine Learning

Piattaforme come Elastic ML, Datadog e Dynatrace implementano modelli ML piu sofisticati:

- **Unsupervised learning** — Clustering di metriche per identificare pattern normali e deviazioni. Non richiede dati etichettati ma puo generare falsi positivi.
- **Supervised learning** — Modelli addestrati su incidenti storici per prevedere futuri problemi. Richiede un dataset di incidenti etichettati di buona qualita.
- **Deep learning (LSTM, Transformer)** — Reti neurali per la previsione di serie temporali complesse con dipendenze a lungo termine. Efficaci per metriche con pattern non lineari.

### Root Cause Analysis Automatizzata

La Root Cause Analysis (RCA) automatizzata correla anomalie su metriche, log e trace per identificare la causa radice di un incidente:

```
Flusso RCA automatizzato:

1. Alert: Error rate > 5% sul servizio checkout
2. Correlazione metriche: latenza database aumentata 3x nello stesso intervallo
3. Correlazione log: 500 occorrenze di "connection pool exhausted" nel servizio checkout
4. Correlazione trace: 85% dei trace lenti hanno uno span DB con durata > 2s
5. Identificazione causa: query non ottimizzata su tabella products senza indice
6. Suggerimento: "CREATE INDEX idx_products_category ON products(category_id)"
```

Strumenti che implementano RCA automatizzata:

- **Dynatrace Davis AI** — Analisi topologica automatica con scoring di probabilita per ogni causa radice potenziale
- **Datadog Watchdog** — Rilevamento automatico di anomalie con correlazione cross-signal
- **Elastic AI Assistant** — Analisi di log e metriche con suggerimenti di remediation basati su LLM
- **New Relic AI** — Correlazione automatica tra deployment, alert e anomalie

### Auto-Remediation

L'auto-remediation esegue azioni correttive automatiche in risposta a condizioni predefinite. Deve essere implementata con cautela e solo per scenari ben compresi:

Scenari sicuri per auto-remediation:

| Condizione | Azione Automatica | Safeguard |
|-----------|-------------------|-----------|
| Pod in CrashLoopBackOff | Restart con backoff esponenziale | Max 5 restart, poi escalation |
| Disco > 95% pieno | Pulizia log/temp vecchi | Mai eliminare dati applicativi |
| Error rate > SLO con deploy recente | Rollback automatico al deploy precedente | Solo se il deploy ha < 30 minuti |
| Certificato in scadenza < 7 giorni | Rinnovo automatico (cert-manager) | Notifica del rinnovo |
| Connessioni DB esaurite | Scale-up connection pool | Max +50%, poi alert manuale |

Principi di sicurezza per l'auto-remediation:

1. **Circuit breaker** — Ogni azione automatica ha un limite di esecuzioni per evitare loop
2. **Audit trail** — Ogni azione automatica viene loggata con timestamp, causa e risultato
3. **Dry-run first** — Nuove regole di auto-remediation partono in modalita dry-run per almeno 2 settimane
4. **Human-in-the-loop** — Per azioni distruttive (scale-down, eliminazione risorse), richiedere approvazione umana anche in scenari automatizzati
5. **Blast radius** — Limitare l'impatto di ogni azione automatica a un singolo componente o servizio

### Costo dell'Observability e Ottimizzazione

L'osservabilita ha costi che crescono con il volume di dati e il numero di servizi monitorati. Un'analisi regolare dei costi e fondamentale:

#### Struttura dei Costi

```
Costi tipici per un'organizzazione con 50 microservizi:

Metriche (Prometheus/Mimir):
  - 500.000 serie temporali attive
  - ~5 GB/giorno di dati raw
  - Storage: $50-100/mese (object storage con compressione)

Log (Loki):
  - 50 GB/giorno di log ingeriti
  - Storage: $100-300/mese (object storage)
  - Se ELK: $1000-3000/mese (cluster Elasticsearch)

Traces (Tempo):
  - 10 milioni di span/giorno (con 10% sampling)
  - Storage: $30-80/mese (object storage)

Infrastruttura:
  - Collector, Prometheus, Grafana, backend storage
  - $500-2000/mese (compute + storage)

Totale self-hosted LGTM: $700-2500/mese
Totale SaaS equivalente (Datadog/New Relic): $5000-20.000/mese
```

#### Strategie di Ottimizzazione dei Costi

1. **Eliminare metriche inutili** — Audit periodico delle metriche: eliminare quelle mai usate in dashboard o alert
2. **Ridurre la cardinalita** — Ogni label aggiuntiva moltiplica le serie temporali
3. **Campionamento intelligente** — Tail-based sampling per trace: 100% errori, 100% lenti, 5-10% normali
4. **Log level management** — `DEBUG` mai in produzione, `INFO` solo per eventi significativi
5. **Retention differenziata** — Dati raw per giorni, aggregati per mesi, riassunti per anni
6. **Filter at source** — Eliminare dati non necessari il piu vicino possibile alla sorgente (nel Collector, non nel backend)

---

## 20. Observability as Code — Approccio Completo

### Principi

L'Observability as Code (OaC) estende il concetto di Infrastructure as Code alla configurazione completa dello stack di osservabilita. Ogni aspetto — dashboard, alert, SLO, data source, rotazioni on-call — e definito come codice, versionato in Git e applicato tramite pipeline CI/CD.

Vantaggi:

- **Riproducibilita** — Lo stack di osservabilita puo essere ricreato identicamente in qualsiasi ambiente
- **Review** — Ogni modifica agli alert o alle dashboard passa per code review, riducendo errori
- **Audit** — La storia completa delle modifiche e tracciabile nel version control
- **Testing** — Le regole di alerting possono essere testate prima del deploy
- **Disaster recovery** — In caso di perdita dell'infrastruttura di monitoring, il ripristino e automatizzato

### Terraform per Monitoring

Terraform provider per le principali piattaforme di osservabilita:

```hcl
# Grafana dashboard via Terraform
resource "grafana_dashboard" "api_overview" {
  config_json = file("${path.module}/dashboards/api-overview.json")
  folder      = grafana_folder.production.id
  overwrite   = true
}

resource "grafana_folder" "production" {
  title = "Production Services"
}

# Data source Prometheus
resource "grafana_data_source" "prometheus" {
  type = "prometheus"
  name = "Prometheus"
  url  = "http://prometheus:9090"

  json_data_encoded = jsonencode({
    httpMethod        = "POST"
    exemplarTraceIdDestinations = [{
      name          = "traceID"
      datasourceUid = grafana_data_source.tempo.uid
    }]
  })
}

# Alert rule
resource "grafana_rule_group" "slo_alerts" {
  name             = "SLO Alerts"
  folder_uid       = grafana_folder.production.uid
  interval_seconds = 60

  rule {
    name      = "High Error Rate"
    condition = "C"

    data {
      ref_id         = "A"
      datasource_uid = grafana_data_source.prometheus.uid

      relative_time_range {
        from = 300
        to   = 0
      }

      model = jsonencode({
        expr = "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m]))"
      })
    }
  }
}

# PagerDuty service
resource "pagerduty_service" "payment_api" {
  name              = "Payment API"
  escalation_policy = pagerduty_escalation_policy.platform.id
  alert_creation    = "create_alerts_and_incidents"

  incident_urgency_rule {
    type    = "constant"
    urgency = "high"
  }
}

resource "pagerduty_service_integration" "prometheus" {
  name    = "Prometheus Alertmanager"
  service = pagerduty_service.payment_api.id
  vendor  = data.pagerduty_vendor.prometheus.id
}
```

### Jsonnet per Dashboard Grafana

Jsonnet e un linguaggio di templating che genera JSON, ideale per dashboard Grafana complesse e riutilizzabili:

```jsonnet
// libs/panels.libsonnet
{
  timeseries(title, expr, legend=''):: {
    type: 'timeseries',
    title: title,
    targets: [{
      expr: expr,
      legendFormat: legend,
    }],
    fieldConfig: {
      defaults: {
        custom: {
          drawStyle: 'line',
          lineWidth: 2,
          fillOpacity: 10,
        },
      },
    },
  },

  stat(title, expr, unit=''):: {
    type: 'stat',
    title: title,
    targets: [{ expr: expr }],
    fieldConfig: {
      defaults: { unit: unit },
    },
  },

  redDashboard(service):: {
    local rateExpr = 'sum(rate(http_requests_total{service="%s"}[5m]))' % service,
    local errorExpr = 'sum(rate(http_requests_total{service="%s",status=~"5.."}[5m])) / %s * 100' % [service, rateExpr],
    local durationExpr = 'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{service="%s"}[5m])) by (le))' % service,

    dashboard: {
      title: '%s — RED Dashboard' % service,
      uid: '%s-red' % std.strReplace(service, '-', ''),
      panels: [
        $.stat('Request Rate', rateExpr, 'reqps') + { gridPos: { h: 4, w: 8, x: 0, y: 0 } },
        $.stat('Error Rate', errorExpr, 'percent') + { gridPos: { h: 4, w: 8, x: 8, y: 0 } },
        $.stat('P99 Latency', durationExpr, 's') + { gridPos: { h: 4, w: 8, x: 16, y: 0 } },
        $.timeseries('Request Rate', rateExpr, '{{handler}}') + { gridPos: { h: 8, w: 24, x: 0, y: 4 } },
      ],
    },
  },
}
```

### CI Testing delle Regole di Alerting

Le regole di alerting devono essere testate in CI per verificare correttezza sintattica e comportamento atteso:

```yaml
# .github/workflows/monitoring-ci.yml
name: Monitoring CI

on:
  pull_request:
    paths:
      - "monitoring/**"

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate Prometheus config
        run: promtool check config monitoring/prometheus/prometheus.yml

      - name: Validate recording rules
        run: promtool check rules monitoring/prometheus/rules/*.yml

      - name: Test alerting rules
        run: promtool test rules monitoring/prometheus/tests/*.yml

      - name: Validate Alertmanager config
        run: amtool check-config monitoring/alertmanager/alertmanager.yml

      - name: Lint Jsonnet dashboards
        run: |
          jsonnetfmt --test monitoring/grafana/jsonnet/*.jsonnet
          jsonnet monitoring/grafana/jsonnet/main.jsonnet > /dev/null

      - name: Validate Grafana dashboards
        run: |
          for f in monitoring/grafana/dashboards/*.json; do
            jq empty "$f" || exit 1
          done
```

File di test per le alerting rules:

```yaml
# monitoring/prometheus/tests/slo_test.yml
rule_files:
  - ../rules/recording_rules.yml
  - ../rules/alerting_rules.yml

evaluation_interval: 1m

tests:
  - interval: 1m
    input_series:
      - series: 'http_requests_total{job="api",status="200"}'
        values: "0+100x60"    # 100 req/min per 60 minuti
      - series: 'http_requests_total{job="api",status="500"}'
        values: "0+1x60"      # 1 errore/min per 60 minuti (1% error rate)

    alert_rule_test:
      # Con 1% error rate e SLO 99.9%, burn rate = 10x
      - eval_time: 10m
        alertname: SLOHighBurnRate_Fast
        exp_alerts:
          - exp_labels:
              severity: critical
              slo: availability
              job: api

  - interval: 1m
    input_series:
      - series: 'http_requests_total{job="api",status="200"}'
        values: "0+1000x60"
      - series: 'http_requests_total{job="api",status="500"}'
        values: "0+0x60"       # Zero errori

    alert_rule_test:
      # Con 0% error rate, nessun alert
      - eval_time: 10m
        alertname: SLOHighBurnRate_Fast
        exp_alerts: []
```

### Crossplane per Monitoring Multi-Cloud

Per ambienti multi-cloud, Crossplane permette di definire risorse di monitoring come Kubernetes CRD:

```yaml
apiVersion: monitoring.crossplane.io/v1alpha1
kind: MonitoringStack
metadata:
  name: production-monitoring
spec:
  forProvider:
    region: eu-west-1
    prometheus:
      retention: 30d
      storage: 100Gi
      replicas: 2
    alertmanager:
      replicas: 3
      config:
        route:
          receiver: default
    grafana:
      version: "11.x"
      dashboards:
        - source: git
          repo: "https://github.com/org/monitoring-dashboards.git"
          path: "dashboards/"
```

---

## Esercizi

1. **Stack Prometheus + Grafana con OTel Collector** — Deployare su Docker Compose: OpenTelemetry Collector, Prometheus e Grafana. Instrumentare un'applicazione web (Go, Python o Node.js) con il SDK OpenTelemetry per esportare metriche via OTLP. Creare una dashboard Grafana che visualizzi le metriche RED (Rate, Errors, Duration) per ogni endpoint.

2. **Alerting multi-livello con Alertmanager** — Configurare Alertmanager con routing per severity (critical → PagerDuty/webhook, warning → Slack, info → email). Definire almeno 5 alert rule in Prometheus: error rate, latenza P99, CPU saturation, disk space, pod restart. Testare ogni regola simulando la condizione e verificando la notifica.

3. **Distributed tracing con Jaeger** — Instrumentare due microservizi che comunicano via HTTP/gRPC con OpenTelemetry SDK. Configurare il collector per esportare trace a Jaeger. Implementare context propagation (W3C Trace Context). Analizzare un trace end-to-end e identificare il servizio con la latenza maggiore.

4. **Log aggregation con Loki** — Configurare Grafana Loki per raccogliere log da container Docker tramite Promtail. Implementare label strutturate (service, environment, level). Creare dashboard Grafana che correlino log ed errori con le metriche Prometheus. Configurare policy di retention differenziate per livello di log.

5. **Exemplar: collegare metriche e trace** — Abilitare gli exemplar in Prometheus 2.30+ e collegare una metrica di latenza al trace ID corrispondente in Jaeger. In Grafana, configurare la data source Prometheus con exemplar abilitati e verificare la navigazione click-through da metrica a trace.

---

## Letture e Riferimenti

### Documentazione ufficiale

- OpenTelemetry Documentation: <https://opentelemetry.io/docs/> (consultato: 2026-05-24)
- Prometheus Documentation: <https://prometheus.io/docs/> (consultato: 2026-05-24)
- Grafana Documentation: <https://grafana.com/docs/grafana/latest/> (consultato: 2026-05-24)
- Jaeger Documentation: <https://www.jaegertracing.io/docs/> (consultato: 2026-05-24)
- Grafana Loki Documentation: <https://grafana.com/docs/loki/latest/> (consultato: 2026-05-24)
- Alertmanager Configuration: <https://prometheus.io/docs/alerting/latest/configuration/> (consultato: 2026-05-24)
- USE Method — Brendan Gregg: <https://www.brendangregg.com/usemethod.html> (consultato: 2026-05-24)
- RED Method — Tom Wilkie: <https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/> (consultato: 2026-05-24)

### Libri

- Majors, C.; Fong-Jones, L.; Miranda, G. — *Observability Engineering*, O'Reilly, 2022
- Sridharan, C. — *Distributed Systems Observability*, O'Reilly, 2018
- Gregg, B. — *Systems Performance* (2a ed.), Addison-Wesley, 2020

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione con questo modulo |
|--------|--------|-----------------------------|
| [05-kubernetes](05-kubernetes.md) | Kubernetes | Metriche cluster, kube-state-metrics, cAdvisor |
| [07-ci-cd](07-ci-cd.md) | CI/CD — Piattaforme e Pipeline | Monitoring post-deployment e DORA metrics |
| [09-service-mesh](09-service-mesh.md) | Service Mesh | Metriche Envoy/Istio integrate nel stack di osservabilità |
| [11-database-management](11-database-management.md) | Database Management | Monitoring query performance e connessioni DB |
| [12-message-queues](12-message-queues.md) | Message Queues | Metriche consumer lag, throughput e dead letter |
| [18-troubleshooting-e-guide-pratiche](18-troubleshooting-e-guide-pratiche.md) | Troubleshooting | Utilizzo dati di osservabilità per diagnosi incidenti |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **Osservabilità** | Capacità di comprendere lo stato interno di un sistema a partire dai suoi output esterni: metriche, log e trace |
| **OpenTelemetry (OTel)** | Framework open source vendor-neutral per la raccolta e l'esportazione di dati di telemetria (metriche, log, trace) |
| **OTLP** | OpenTelemetry Protocol — protocollo standard per il trasporto di dati di telemetria via HTTP o gRPC |
| **Prometheus** | Sistema di monitoraggio e alerting open source basato su modello pull, con database time-series integrato |
| **Grafana** | Piattaforma di visualizzazione e dashboarding che supporta molteplici data source per metriche, log e trace |
| **Jaeger** | Sistema di tracing distribuito open source per il monitoraggio e la diagnosi di transazioni in architetture a microservizi |
| **Metrica RED** | Metodologia per monitorare servizi: Rate (richieste/s), Errors (tasso errori), Duration (latenza) |
| **Metrica USE** | Metodologia per monitorare risorse: Utilization (utilizzo), Saturation (saturazione), Errors (errori) |
| **Exemplar** | Campione che collega un punto metrico a un trace ID specifico, consentendo la navigazione diretta da metrica a trace |
| **Tail-based sampling** | Strategia di campionamento che decide se conservare un trace dopo averlo completato, basandosi su criteri come errori o latenza |
| **Alertmanager** | Componente di Prometheus che gestisce routing, deduplicazione, raggruppamento e silenziamento degli alert |
| **SLI/SLO/SLA** | Service Level Indicator (metrica), Service Level Objective (target), Service Level Agreement (contratto) — gerarchia di garanzie di servizio |
| **Retention policy** | Politica che definisce per quanto tempo conservare dati di telemetria, bilanciando costi di storage e necessità operative |
| **Context propagation** | Meccanismo per trasmettere il contesto del trace (trace ID, span ID) attraverso i confini di servizio via header HTTP o metadata gRPC |
| **Cardinality** | Numero di combinazioni uniche di label in una serie temporale; alta cardinalità causa esplosione delle serie e problemi di performance |

Ogni politica di retention deve essere bilanciata tra costo dello storage e necessita di analisi storiche. I requisiti di compliance (GDPR, PCI-DSS, SOX) possono imporre retention minime o massime specifiche per determinati tipi di dati.
