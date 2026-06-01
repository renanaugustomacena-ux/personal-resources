# Monitoring Linux — Guida Completa

> **Modulo 20** · **Aggiornamento:** 2026-05-24

## Idee guida
1. **Prometheus + node_exporter standard de facto.**
2. **OTel Collector vendor-neutral pipeline.**
3. **Alert: Alertmanager + multi-burn-rate.**
4. **Dashboard Grafana: USE + RED methodologie.**


## Indice

- [Panoramica](#panoramica)
- [Filosofia del Monitoring](#filosofia-del-monitoring)
- [Prometheus: Architettura e Deep Dive](#prometheus-architettura-e-deep-dive)
- [PromQL: Linguaggio di Query](#promql-linguaggio-di-query)
- [Recording Rules e Alerting Rules](#recording-rules-e-alerting-rules)
- [Federation e Remote Storage](#federation-e-remote-storage)
- [Grafana: Deep Dive](#grafana-deep-dive)
- [Node Exporter e Metriche](#node-exporter-e-metriche)
- [Alertmanager: Notifiche e Routing](#alertmanager-notifiche-e-routing)
- [Zabbix: Architettura e Configurazione](#zabbix-architettura-e-configurazione)
- [Nagios/Icinga2: Panoramica e Configurazione](#nagiosicinga2-panoramica-e-configurazione)
- [Uptime Monitoring e Blackbox Exporter](#uptime-monitoring-e-blackbox-exporter)
- [Log Monitoring: Loki, ELK, Alert su Log](#log-monitoring-loki-elk-alert-su-log)
- [APM e Distributed Tracing](#apm-e-distributed-tracing)
- [Infrastructure Monitoring: SNMP, IPMI, iDRAC/iLO](#infrastructure-monitoring-snmp-ipmi-idracilo)
- [Container Monitoring](#container-monitoring)
- [Observability basata su eBPF](#observability-basata-su-ebpf)
- [Capacity Planning e Forecasting](#capacity-planning-e-forecasting)
- [On-Call e Incident Management](#on-call-e-incident-management)
- [Dashboard Best Practices](#dashboard-best-practices)
- [Monitoraggio Custom con Script](#monitoraggio-custom-con-script)
- [Guida Implementazione: Stack Completo da Zero](#guida-implementazione-stack-completo-da-zero)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)

---

## Panoramica

Il monitoring è essenziale per mantenere l'infrastruttura sana e prevenire i problemi prima che diventino incidenti. Lo stack moderno è basato su Prometheus (raccolta metriche) + Grafana (visualizzazione) + Alertmanager (notifiche). Nagios/Icinga sono le soluzioni tradizionali, ancora diffuse. Un buon sistema di monitoring copre: disponibilità (il servizio è up?), performance (quanto è veloce?), capacità (quanto spazio/risorse rimangono?), errori (cosa sta fallendo?).

### I Tre Pilastri dell'Osservabilità

Un sistema moderno di osservabilità si basa su tre pilastri complementari:

| Pilastro | Cosa cattura | Strumenti tipici |
|----------|-------------|------------------|
| **Metriche** | Valori numerici aggregati nel tempo (CPU, latenza, error rate) | Prometheus, Zabbix, InfluxDB |
| **Log** | Eventi discreti con contesto testuale | Loki, Elasticsearch, Fluentd |
| **Trace** | Percorso di una richiesta attraverso servizi distribuiti | Jaeger, Tempo, Zipkin |

Le metriche dicono *che qualcosa è andato storto*, i log dicono *cosa è andato storto*, le trace dicono *dove è andato storto* nel flusso distribuito.

### Monitoring vs Osservabilità

Il **monitoring** tradizionale risponde a domande conosciute in anticipo: "Il server è up?", "Il disco è pieno?". L'**osservabilità** permette di rispondere a domande che non sapevamo di dover porre: "Perché le richieste dal datacenter EU verso il servizio di pagamento hanno latenza 10x superiore solo il martedì mattina?".

Il monitoring è un sottoinsieme dell'osservabilità. Un sistema osservabile permette di diagnosticare problemi sconosciuti senza dover deployare nuova strumentazione.

---

## Filosofia del Monitoring

### Metodo USE (Utilization, Saturation, Errors)

Ideato da Brendan Gregg, il metodo USE fornisce un framework sistematico per analizzare le prestazioni di ogni risorsa hardware:

| Dimensione | Definizione | Esempio |
|-----------|------------|---------|
| **Utilization** | Percentuale di tempo in cui la risorsa è occupata | CPU al 75% |
| **Saturation** | Coda di lavoro in attesa (work queued) | Load average 8 su 4 core |
| **Errors** | Conteggio di eventi di errore | ECC memory errors, NIC drops |

Applicazione pratica per risorsa:

| Risorsa | Utilization | Saturation | Errors |
|---------|------------|------------|--------|
| CPU | `node_cpu_seconds_total` (% non-idle) | Load average, run queue | Machine check exceptions |
| Memoria | `MemUsed / MemTotal` | Swap usage, OOM kills | ECC errors (edac) |
| Disco | `%util` da iostat | `avgqu-sz` (queue depth) | Read/write errors in dmesg |
| Rete | Bytes tx/rx vs bandwidth | Dropped packets, overruns | CRC errors, carrier errors |
| File system | `df -h` (% usato) | Inode usage | Mount errors, read-only FS |

```promql
# USE per CPU
# Utilization
100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Saturation
node_load15 / count without(cpu)(node_cpu_seconds_total{mode="idle"})

# Errors — controllo via dmesg/log, non metriche standard
```

### Metodo RED (Rate, Errors, Duration)

Il metodo RED, proposto da Tom Wilkie, è orientato ai **servizi** anziché alle risorse hardware:

| Dimensione | Definizione | Query tipica |
|-----------|------------|-------------|
| **Rate** | Richieste per secondo | `rate(http_requests_total[5m])` |
| **Errors** | Richieste fallite per secondo | `rate(http_requests_total{status=~"5.."}[5m])` |
| **Duration** | Distribuzione della latenza | `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))` |

USE per le risorse, RED per i servizi — insieme coprono l'intera infrastruttura.

### Golden Signals (Google SRE)

Il libro "Site Reliability Engineering" di Google definisce quattro segnali d'oro per ogni servizio:

1. **Latenza** — tempo per servire una richiesta. Distinguere tra richieste riuscite e fallite (una richiesta che fallisce velocemente distorce la media).
2. **Traffico** — domanda sul sistema. HTTP requests/s, transazioni/s, sessioni attive.
3. **Errori** — tasso di richieste fallite. Include errori espliciti (HTTP 500), impliciti (HTTP 200 con contenuto errato), policy-based (risposte sopra un SLO di latenza).
4. **Saturazione** — quanto è "pieno" il servizio. Enfatizzare le risorse più vincolate (CPU, memoria, I/O, connessioni DB).

### SLI, SLO, SLA e Error Budget

| Termine | Definizione | Esempio |
|---------|-----------|---------|
| **SLI** (Service Level Indicator) | Metrica quantitativa di un aspetto del servizio | "99.2% delle richieste sotto 200ms" |
| **SLO** (Service Level Objective) | Target interno per un SLI | "Il 99.9% delle richieste deve avere latenza < 300ms" |
| **SLA** (Service Level Agreement) | Contratto con conseguenze legali/economiche | "Uptime 99.95% o crediti al cliente" |
| **Error Budget** | Margine ammesso di errore (100% - SLO) | SLO 99.9% → error budget 0.1% = ~43 minuti/mese |

L'error budget è il concetto chiave: finché il budget non è esaurito, il team può rilasciare feature e accettare rischio. Quando il budget è consumato, si blocca il deploy e si concentra sull'affidabilità.

```promql
# SLI: percentuale di richieste con latenza < 300ms
sum(rate(http_request_duration_seconds_bucket{le="0.3"}[30d]))
/
sum(rate(http_request_duration_seconds_count[30d]))

# Error budget rimanente (target 99.9%)
1 - (
  (1 - (sum(rate(http_request_duration_seconds_bucket{le="0.3"}[30d]))
        / sum(rate(http_request_duration_seconds_count[30d]))))
  / (1 - 0.999)
)
```

### Multi-Window Multi-Burn-Rate Alert

Il modello classico "soglia statica" genera troppi falsi positivi. L'approccio multi-burn-rate usa finestre temporali multiple:

| Finestra | Burn rate | Significato |
|---------|-----------|------------|
| 1h | 14.4x | Emergenza: budget esaurito in ~1 giorno |
| 6h | 6x | Urgente: budget esaurito in ~3 giorni |
| 3d | 1x | Lento degrado: budget in pericolo |

```yaml
# Alert multi-burn-rate per SLO 99.9%
groups:
  - name: slo_burn_rate
    rules:
      - alert: ErrorBudgetBurnHigh
        expr: |
          (
            job:slo_errors_per_request:ratio_rate1h{job="api"} > (14.4 * 0.001)
            and
            job:slo_errors_per_request:ratio_rate5m{job="api"} > (14.4 * 0.001)
          )
        for: 2m
        labels:
          severity: critical
          window: 1h
        annotations:
          summary: "Error budget in esaurimento rapido (burn rate 14.4x)"

      - alert: ErrorBudgetBurnMedium
        expr: |
          (
            job:slo_errors_per_request:ratio_rate6h{job="api"} > (6 * 0.001)
            and
            job:slo_errors_per_request:ratio_rate30m{job="api"} > (6 * 0.001)
          )
        for: 15m
        labels:
          severity: warning
          window: 6h
        annotations:
          summary: "Error budget in calo (burn rate 6x)"
```

---

## Prometheus: Architettura e Deep Dive

Prometheus è un sistema di monitoring basato su metriche time-series, con modello pull (scraping degli endpoint).

### Architettura

```
                    ┌──────────────────────────────┐
                    │      Prometheus Server        │
                    │  ┌──────────┐ ┌────────────┐ │
 Targets ──scrape──▶│  │ Retrieval│ │  TSDB      │ │
 (exporters,        │  │ (pull)   │ │ (storage)  │ │
  /metrics)         │  └──────────┘ └────────────┘ │
                    │  ┌──────────┐ ┌────────────┐ │
                    │  │ Rule     │ │ HTTP API   │─┼──▶ Grafana, API clients
                    │  │ Engine   │ │ (PromQL)   │ │
                    │  └──────────┘ └────────────┘ │
                    │       │                       │
                    │       ▼                       │
                    │  ┌──────────┐                 │
                    │  │ Alert    │─────────────────┼──▶ Alertmanager
                    │  │ Manager  │                 │        │
                    │  └──────────┘                 │        ▼
                    └──────────────────────────────┘    Email/Slack/PD
                    
Pushgateway ◀── batch jobs (push metriche)

Service Discovery ── Consul, Kubernetes, EC2, DNS, file_sd
```

Componenti chiave:

- **Retrieval**: modulo che effettua scrape periodico sugli endpoint `/metrics`.
- **TSDB**: database time-series locale, altamente compresso, con retention configurabile.
- **Rule Engine**: valuta recording rules (pre-calcolo) e alerting rules.
- **HTTP API**: espone PromQL e endpoint di gestione.
- **Pushgateway**: per job batch che non possono esporre endpoint (short-lived jobs).
- **Service Discovery**: auto-discovery di target da Kubernetes, Consul, file, DNS, EC2, ecc.

### Installazione

```bash
# Installazione (da binario)
wget https://github.com/prometheus/prometheus/releases/download/v2.48.0/prometheus-2.48.0.linux-amd64.tar.gz
tar xzf prometheus-*.tar.gz
sudo mv prometheus-2.48.0.linux-amd64 /opt/prometheus
sudo useradd -rs /bin/false prometheus
sudo chown -R prometheus:prometheus /opt/prometheus
```

### Configurazione

```yaml
# /opt/prometheus/prometheus.yml
global:
  scrape_interval: 15s               # Ogni 15 secondi
  evaluation_interval: 15s           # Valutazione regole
  scrape_timeout: 10s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node'
    static_configs:
      - targets:
        - 'server1:9100'
        - 'server2:9100'
        - 'server3:9100'

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
```

### Service systemd

```ini
# /etc/systemd/system/prometheus.service
[Unit]
Description=Prometheus
After=network.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/opt/prometheus/prometheus \
  --config.file=/opt/prometheus/prometheus.yml \
  --storage.tsdb.path=/opt/prometheus/data \
  --storage.tsdb.retention.time=30d \
  --web.listen-address=:9090
Restart=always

[Install]
WantedBy=multi-user.target
```

### Service Discovery

Oltre a `static_configs`, Prometheus supporta discovery dinamico:

```yaml
# File-based service discovery
scrape_configs:
  - job_name: 'file_sd'
    file_sd_configs:
      - files:
          - '/opt/prometheus/targets/*.json'
        refresh_interval: 30s
```

```json
# /opt/prometheus/targets/webservers.json
[
  {
    "targets": ["web1:9100", "web2:9100", "web3:9100"],
    "labels": {
      "env": "production",
      "role": "webserver",
      "datacenter": "eu-west"
    }
  }
]
```

```yaml
# Kubernetes service discovery
scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port, __address__]
        action: replace
        regex: (\d+);([^:]+)(?::\d+)?
        replacement: $2:$1
        target_label: __address__
```

```yaml
# Consul service discovery
scrape_configs:
  - job_name: 'consul'
    consul_sd_configs:
      - server: 'consul.example.com:8500'
        services: []
    relabel_configs:
      - source_labels: [__meta_consul_tags]
        regex: .*,prometheus,.*
        action: keep
      - source_labels: [__meta_consul_service]
        target_label: job
```

### TSDB e Storage

Il TSDB di Prometheus è progettato per alta ingestione con basso footprint:

```
data/
├── chunks_head/           # Dati in memoria (ultime 2h)
├── wal/                   # Write-Ahead Log (persistenza crash)
├── 01HXXXXXX/             # Blocco compattato
│   ├── chunks/            # Dati compressi
│   ├── index              # Indice invertito per label
│   ├── meta.json          # Metadata del blocco
│   └── tombstones         # Dati cancellati
└── 01HYYYYYY/
    └── ...
```

Parametri di storage critici:

```bash
# Retention per tempo (default 15d)
--storage.tsdb.retention.time=90d

# Retention per dimensione (alternativa)
--storage.tsdb.retention.size=50GB

# Dimensione minima blocco (per compaction)
--storage.tsdb.min-block-duration=2h

# Dimensione massima blocco
--storage.tsdb.max-block-duration=36h

# WAL compression (raccomandato)
--storage.tsdb.wal-compression

# Calcolo spazio necessario:
# bytes_per_sample * ingestion_rate * retention_seconds
# Tipicamente ~1.5-2 bytes/sample dopo compressione
# 100k series, 15s scrape, 30 giorni ≈ 50-80 GB
```

### Relabeling

Il relabeling è uno strumento potente per manipolare label prima o dopo lo scrape:

```yaml
scrape_configs:
  - job_name: 'nodes'
    static_configs:
      - targets: ['server1:9100', 'server2:9100']
    relabel_configs:
      # Estrarre hostname dal target
      - source_labels: [__address__]
        regex: '([^:]+):.*'
        target_label: hostname
        replacement: '$1'

      # Aggiungere label environment basato su hostname
      - source_labels: [hostname]
        regex: 'prod-.*'
        target_label: env
        replacement: 'production'

      - source_labels: [hostname]
        regex: 'stag-.*'
        target_label: env
        replacement: 'staging'

      # Rimuovere target di staging in produzione
      # - source_labels: [env]
      #   regex: 'staging'
      #   action: drop

    # metric_relabel_configs agisce DOPO lo scrape
    metric_relabel_configs:
      # Eliminare metriche costose non necessarie
      - source_labels: [__name__]
        regex: 'go_.*'
        action: drop
      
      # Rinominare una metrica
      - source_labels: [__name__]
        regex: 'old_metric_name'
        target_label: __name__
        replacement: 'new_metric_name'
```

---

## PromQL: Linguaggio di Query

PromQL è il linguaggio di query di Prometheus. Supporta quattro tipi di dati:

| Tipo | Descrizione | Esempio |
|------|------------|---------|
| **Instant vector** | Set di time series, ognuna con un singolo sample al timestamp corrente | `node_cpu_seconds_total` |
| **Range vector** | Set di time series con range di sample nel tempo | `node_cpu_seconds_total[5m]` |
| **Scalar** | Singolo valore numerico floating point | `3.14` |
| **String** | Valore stringa (raramente usato) | `"hello"` |

### Selettori e Modificatori

```promql
# Selettore esatto
node_cpu_seconds_total{mode="idle", instance="server1:9100"}

# Regex match
node_cpu_seconds_total{mode=~"idle|iowait"}

# Negazione
node_cpu_seconds_total{mode!="idle"}

# Regex negativa
node_cpu_seconds_total{mode!~"idle|iowait"}

# Offset modifier — query nel passato
node_memory_MemAvailable_bytes offset 1h

# @ modifier — query a timestamp specifico
node_memory_MemAvailable_bytes @ 1609459200
```

### Funzioni di Aggregazione

```promql
# Somma per label
sum by (instance) (rate(http_requests_total[5m]))

# Media escludendo label
avg without (cpu) (rate(node_cpu_seconds_total{mode="idle"}[5m]))

# Top 5 per CPU usage
topk(5, 100 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Bottom 3 per memoria disponibile
bottomk(3, node_memory_MemAvailable_bytes)

# Conteggio di serie con valore > soglia
count(node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.15)

# Quantile
quantile(0.95, rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]))

# Standard deviation
stddev by (job) (rate(http_requests_total[5m]))

# Group — elenco di label senza valore
group by (instance) (up)
```

### Funzioni su Range Vector

```promql
# rate — incremento per secondo (per counter)
rate(http_requests_total[5m])

# irate — rate istantaneo (ultimi 2 sample)
irate(http_requests_total[5m])

# increase — incremento totale nel range
increase(http_requests_total[1h])

# delta — differenza tra primo e ultimo sample (per gauge)
delta(node_memory_MemAvailable_bytes[1h])

# deriv — derivata (pendenza) per gauge
deriv(node_memory_MemAvailable_bytes[1h])

# predict_linear — previsione lineare
# "Quando il disco sarà pieno?"
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 24*3600)

# changes — numero di cambiamenti di valore
changes(node_boot_time_seconds[1d])

# resets — numero di reset del counter
resets(http_requests_total[1h])

# avg_over_time, min_over_time, max_over_time
avg_over_time(node_load1[1h])
max_over_time(node_cpu_seconds_total{mode="idle"}[1h])
```

### Operatori Binari

```promql
# Aritmetici: + - * / % ^
node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes

# Confronto: == != > < >= <=
# Filtra serie dove CPU > 80%
(100 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80

# bool modifier — restituisce 0 o 1 anziché filtrare
up == bool 0

# Vector matching
# one-to-one (label corrispondenti)
node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes

# on() — match solo su label specifiche
rate(http_requests_total{status="500"}[5m])
  / on(method, handler)
rate(http_requests_total[5m])

# ignoring() — ignora label nel match
rate(errors_total[5m]) / ignoring(error_type) rate(requests_total[5m])

# group_left / group_right — many-to-one match
rate(http_requests_total[5m])
  * on(instance) group_left(datacenter)
  machine_info
```

### Query di Uso Comune

```promql
# CPU utilizzazione
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memoria usata (%)
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Disco usato (%)
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100

# Rete: traffico in ingresso (byte/s)
rate(node_network_receive_bytes_total{device="eth0"}[5m])

# Uptime
time() - node_boot_time_seconds

# HTTP request rate
rate(http_requests_total[5m])

# HTTP error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Latency (histogram)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Histogram e Summary

```promql
# Histogram: distribuzione in bucket
# Metrica esposta dall'applicazione:
# http_request_duration_seconds_bucket{le="0.01"} 24054
# http_request_duration_seconds_bucket{le="0.05"} 33444
# http_request_duration_seconds_bucket{le="0.1"}  41234
# http_request_duration_seconds_bucket{le="0.5"}  45678
# http_request_duration_seconds_bucket{le="+Inf"} 45890
# http_request_duration_seconds_count             45890
# http_request_duration_seconds_sum               2345.67

# Percentile 99
histogram_quantile(0.99, sum by(le)(rate(http_request_duration_seconds_bucket[5m])))

# Apdex score (soglia 0.3s, tolerable 1.2s)
(
  sum(rate(http_request_duration_seconds_bucket{le="0.3"}[5m]))
  +
  sum(rate(http_request_duration_seconds_bucket{le="1.2"}[5m]))
)
/ 2
/ sum(rate(http_request_duration_seconds_count[5m]))

# Latenza media
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

---

## Recording Rules e Alerting Rules

### Recording Rules

Le recording rules pre-calcolano query costose e le salvano come nuove time series. Essenziali per dashboard performanti e query ricorrenti:

```yaml
# /opt/prometheus/rules/recording.yml
groups:
  - name: node_recording
    interval: 15s
    rules:
      # CPU usage per instance
      - record: instance:node_cpu_utilization:ratio
        expr: |
          1 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m]))

      # Memoria usata in percentuale
      - record: instance:node_memory_utilization:ratio
        expr: |
          1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

      # Disco usato in percentuale per mountpoint
      - record: instance:node_filesystem_utilization:ratio
        expr: |
          1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)

      # Network throughput
      - record: instance:node_network_receive_bytes:rate5m
        expr: rate(node_network_receive_bytes_total[5m])

      - record: instance:node_network_transmit_bytes:rate5m
        expr: rate(node_network_transmit_bytes_total[5m])

  - name: http_recording
    interval: 15s
    rules:
      # Request rate per servizio
      - record: job:http_requests:rate5m
        expr: sum by(job)(rate(http_requests_total[5m]))

      # Error ratio per servizio
      - record: job:http_errors:ratio_rate5m
        expr: |
          sum by(job)(rate(http_requests_total{status=~"5.."}[5m]))
          /
          sum by(job)(rate(http_requests_total[5m]))

      # Latenza p99
      - record: job:http_request_duration_seconds:p99_rate5m
        expr: |
          histogram_quantile(0.99, sum by(job, le)(rate(http_request_duration_seconds_bucket[5m])))

      # SLI per multi-burn-rate
      - record: job:slo_errors_per_request:ratio_rate5m
        expr: |
          sum by(job)(rate(http_requests_total{status=~"5.."}[5m]))
          / sum by(job)(rate(http_requests_total[5m]))

      - record: job:slo_errors_per_request:ratio_rate1h
        expr: |
          sum by(job)(rate(http_requests_total{status=~"5.."}[1h]))
          / sum by(job)(rate(http_requests_total[1h]))

      - record: job:slo_errors_per_request:ratio_rate6h
        expr: |
          sum by(job)(rate(http_requests_total{status=~"5.."}[6h]))
          / sum by(job)(rate(http_requests_total[6h]))
```

Convenzione di naming per recording rules: `level:metric_name:operations`. Esempio: `instance:node_cpu_utilization:ratio`.

### Alerting Rules Avanzate

```yaml
# /opt/prometheus/rules/alerts.yml
groups:
  - name: node_alerts
    rules:
      - alert: HighCPU
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU alta su {{ $labels.instance }}"
          description: "CPU sopra l'80% da 5 minuti (attuale: {{ $value }}%)"

      - alert: DiskSpaceLow
        expr: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 > 85
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Disco quasi pieno su {{ $labels.instance }}"
          description: "Disco / al {{ $value }}%"

      - alert: MemoryHigh
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memoria alta su {{ $labels.instance }}"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "{{ $labels.instance }} non raggiungibile"

  - name: node_alerts_extended
    rules:
      - alert: DiskWillFillIn24h
        expr: |
          predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 24*3600) < 0
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Disco {{ $labels.mountpoint }} su {{ $labels.instance }} pieno entro 24h"
          description: "Estrapolazione lineare delle ultime 6h prevede esaurimento"

      - alert: HighIOWait
        expr: |
          avg by(instance)(rate(node_cpu_seconds_total{mode="iowait"}[5m])) * 100 > 20
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "I/O wait elevato su {{ $labels.instance }}: {{ $value }}%"

      - alert: TooManyOpenFiles
        expr: |
          node_filefd_allocated / node_filefd_maximum * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "File descriptor al {{ $value }}% del limite su {{ $labels.instance }}"

      - alert: NetworkErrors
        expr: |
          rate(node_network_receive_errs_total[5m]) > 0
          or
          rate(node_network_transmit_errs_total[5m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Errori di rete su {{ $labels.instance }} ({{ $labels.device }})"

      - alert: SwapUsageHigh
        expr: |
          (node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes)
          / node_memory_SwapTotal_bytes * 100 > 50
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Swap al {{ $value }}% su {{ $labels.instance }}"

      - alert: ClockSkew
        expr: |
          abs(node_timex_offset_seconds) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Clock drift rilevato su {{ $labels.instance }}: {{ $value }}s"

      - alert: SystemdServiceFailed
        expr: |
          node_systemd_unit_state{state="failed"} == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Servizio {{ $labels.name }} in stato failed su {{ $labels.instance }}"

      - alert: OOMKillDetected
        expr: |
          increase(node_vmstat_oom_kill[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "OOM kill rilevato su {{ $labels.instance }}"

      - alert: ConntrackTableFull
        expr: |
          node_nf_conntrack_entries / node_nf_conntrack_entries_limit * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Conntrack table all'{{ $value }}% su {{ $labels.instance }}"

  - name: http_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          job:http_errors:ratio_rate5m > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate >5% per {{ $labels.job }}: {{ $value | humanizePercentage }}"

      - alert: HighLatencyP99
        expr: |
          job:http_request_duration_seconds:p99_rate5m > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Latenza p99 >2s per {{ $labels.job }}: {{ $value }}s"

      - alert: NoTraffic
        expr: |
          job:http_requests:rate5m == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Nessun traffico su {{ $labels.job }} da 5 minuti"
```

### Verificare le Regole

```bash
# Validare sintassi delle regole
/opt/prometheus/promtool check rules /opt/prometheus/rules/*.yml

# Test delle regole con dati di esempio
/opt/prometheus/promtool test rules test_rules.yml

# Reload configurazione senza riavvio
curl -X POST http://localhost:9090/-/reload

# oppure con signal
kill -HUP $(pidof prometheus)
```

---

## Federation e Remote Storage

### Federation

La federation permette a un Prometheus "globale" di raccogliere metriche selezionate da istanze locali:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Prometheus   │     │ Prometheus   │     │ Prometheus   │
│ Datacenter A │     │ Datacenter B │     │ Datacenter C │
│ (locale)     │     │ (locale)     │     │ (locale)     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                     │
       └──────────┬─────────┴──────────┬──────────┘
                  │                    │
           ┌──────▼────────────────────▼──────┐
           │       Prometheus Globale          │
           │  (scrape /federate dalle locali)  │
           └──────────────────────────────────┘
```

```yaml
# Configurazione Prometheus globale
scrape_configs:
  - job_name: 'federate'
    scrape_interval: 30s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        # Raccogliere solo recording rules (pre-aggregate)
        - '{__name__=~"job:.*"}'
        # E metriche critiche
        - '{__name__=~"up|node_load1"}'
    static_configs:
      - targets:
          - 'prometheus-dc-a:9090'
          - 'prometheus-dc-b:9090'
          - 'prometheus-dc-c:9090'
```

### Remote Write / Remote Read

Per retention a lungo termine, Prometheus supporta remote write verso storage esterni:

```yaml
# prometheus.yml — remote write verso Thanos/Cortex/Mimir/VictoriaMetrics
remote_write:
  - url: "http://mimir:9009/api/v1/push"
    queue_config:
      max_samples_per_send: 5000
      batch_send_deadline: 5s
      max_shards: 10
    # Filtrare cosa inviare
    write_relabel_configs:
      - source_labels: [__name__]
        regex: 'go_.*'
        action: drop

remote_read:
  - url: "http://mimir:9009/prometheus/api/v1/read"
    read_recent: false    # Leggere dati vecchi dal remote storage
```

### Thanos (architettura sidecar)

```
┌──────────────────────────┐
│   Prometheus + Sidecar   │ ──upload──▶ Object Storage (S3, GCS, MinIO)
└──────────────────────────┘                    │
                                                ▼
                                    ┌──────────────────┐
                                    │   Thanos Store    │
                                    │   Gateway         │
                                    └────────┬─────────┘
                                             │
┌──────────────────┐              ┌──────────▼─────────┐
│  Thanos Query    │◀─────────────│   Thanos Querier    │
│  Frontend        │              │  (dedup + merge)     │
│  (caching)       │              └────────────────────┘
└──────────────────┘
```

Thanos permette: query globali multi-cluster, deduplicazione, downsampling automatico (5m, 1h), retention illimitata su object storage.

### VictoriaMetrics come Alternativa a Prometheus

VictoriaMetrics è un TSDB ad alte prestazioni progettato come drop-in replacement per Prometheus. Offre compressione dati fino al 70% superiore, consumo RAM 3-4x inferiore e velocità di ingestione significativamente più elevata, mantenendo piena compatibilità con il protocollo `remote_write` di Prometheus e con PromQL.

#### Architettura Single-Node vs Cluster

**Single-node** — ideale per ambienti fino a ~30 milioni di metriche attive:

```bash
# Installazione e avvio single-node
wget https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/v1.108.1/victoria-metrics-linux-amd64-v1.108.1.tar.gz
tar xzf victoria-metrics-linux-amd64-v1.108.1.tar.gz

# Avvio con retention 90 giorni e storage su SSD
./victoria-metrics-prod \
  -storageDataPath=/var/lib/victoria-metrics \
  -retentionPeriod=90d \
  -httpListenAddr=:8428 \
  -search.maxUniqueTimeseries=500000
```

**Cluster mode** — scala orizzontalmente con tre componenti:

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  vminsert     │────▶│    vmstorage      │◀────│    vmselect      │
│  (ingestione) │     │ (persistenza TSDB)│     │  (query engine)  │
│  :8480        │     │  :8482            │     │  :8481           │
└──────────────┘     └──────────────────┘     └──────────────────┘
       ▲                    ▲ ▲                        │
       │              repliche N                       │
  remote_write         sharding                   PromQL / MetricsQL
  da Prometheus        automatico                  query unificate
```

- **vminsert** — riceve dati via remote_write, distribuisce agli shard vmstorage
- **vmstorage** — storage replicato, compressione aggressiva, merge-tree engine
- **vmselect** — esegue query su tutti i nodi vmstorage, deduplicazione trasparente

#### MetricsQL: Superset di PromQL

VictoriaMetrics estende PromQL con MetricsQL, che aggiunge funzionalità mancanti:

```promql
# range_median — mediana nativa (non disponibile in PromQL standard)
range_median(node_cpu_seconds_total{mode="idle"}[1h])

# keep_last_value — riempie gap nei dati (utile per metriche sparse)
keep_last_value(up{job="api-server"})

# label_graphite_group — estrae segmenti da metriche Graphite-style
label_graphite_group(graphite_metric_name, 2, 3)

# Supporto WITH templates per query complesse
WITH (
  cpuUsage = 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
)
cpuUsage > 80
```

#### Integrazione con Prometheus Esistente

Configurare Prometheus per inviare metriche a VictoriaMetrics richiede due righe:

```yaml
# prometheus.yml — aggiungere nella sezione remote_write
remote_write:
  - url: http://victoria-metrics:8428/api/v1/write
    queue_config:
      max_samples_per_send: 10000
      capacity: 20000
      max_shards: 30
```

VictoriaMetrics espone l'endpoint `/api/v1/query` compatibile con Prometheus, quindi Grafana può usarlo come data source Prometheus senza modifiche. Per sfruttare MetricsQL, selezionare il data source dedicato VictoriaMetrics.

#### Vantaggi Operativi Misurabili

| Aspetto | Prometheus | VictoriaMetrics |
|---------|-----------|-----------------|
| Compressione disco | ~1.3 bytes/sample | ~0.4 bytes/sample |
| RAM per 1M time series attive | ~6 GB | ~1.5 GB |
| Velocità ingestione | ~240k samples/s | ~800k samples/s |
| Downsampling nativo | No (richiede Thanos) | Sì (`-downsampling.period`) |
| Query cache | No | Sì (rollup result cache) |
| Supporto multi-tenancy | No | Sì (via `vm-account-id` header) |

VictoriaMetrics supporta anche l'importazione diretta di dati in formati Prometheus exposition, InfluxDB line protocol, Graphite plaintext, DataDog e OpenTelemetry, rendendolo un aggregatore universale per ambienti eterogenei.

#### vmagent e vmalert: Componenti Satellite

**vmagent** è un collector leggero che sostituisce Prometheus per lo scraping, consumando 5-10x meno RAM:

```bash
# vmagent scrape e forward (sostituisce Prometheus come scraper)
./vmagent-prod \
  -promscrape.config=/etc/vmagent/scrape.yml \
  -remoteWrite.url=http://victoria-metrics:8428/api/v1/write \
  -remoteWrite.tmpDataPath=/var/lib/vmagent-buffer \
  -remoteWrite.maxDiskUsagePerURL=1GB \
  -promscrape.streamParse=true
```

**vmalert** valuta alerting rules e recording rules compatibili con Prometheus, inviando notifiche ad Alertmanager:

```bash
# vmalert con regole Prometheus-compatibili
./vmalert-prod \
  -rule=/etc/vmalert/rules/*.yml \
  -datasource.url=http://victoria-metrics:8428 \
  -notifier.url=http://alertmanager:9093 \
  -remoteWrite.url=http://victoria-metrics:8428 \
  -evaluationInterval=15s \
  -external.url=http://grafana:3000
```

Per un deployment completo VictoriaMetrics single-node, la catena operativa minima è: **vmagent** (scraping) → **VictoriaMetrics** (storage + query) → **vmalert** (rules + alerting) → **Alertmanager** (notifiche), con Grafana come frontend di visualizzazione. Questo stack sostituisce completamente Prometheus mantenendo la compatibilità con tutte le dashboard e le regole esistenti, richiedendo al contempo una frazione delle risorse hardware.

```yaml
# Esempio recording rule per vmalert (formato identico a Prometheus)
groups:
  - name: node_aggregations
    interval: 30s
    rules:
      - record: instance:node_cpu_utilisation:rate5m
        expr: |
          1 - avg without(cpu) (rate(node_cpu_seconds_total{mode="idle"}[5m]))
      - record: instance:node_memory_utilisation:ratio
        expr: |
          1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
```

---

## Grafana: Deep Dive

```bash
# Installazione
sudo apt install -y apt-transport-https software-properties-common
wget -q -O - https://packages.grafana.com/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/grafana.gpg
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://packages.grafana.com/oss/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update && sudo apt install grafana
sudo systemctl enable --now grafana-server

# Accesso: http://server:3000 (default: admin/admin)
```

### Configurare Data Source

1. Settings → Data Sources → Add data source → Prometheus
2. URL: `http://localhost:9090`
3. Save & Test

### Dashboard Importanti

Dashboard pre-costruite da Grafana.com:
- **Node Exporter Full** (ID: 1860) — Metriche sistema complete
- **Docker and system monitoring** (ID: 893)
- **NGINX** (ID: 9614)
- **PostgreSQL** (ID: 9628)

Importare: Dashboards → Import → inserire ID.

### Tipi di Panel

| Panel | Caso d'uso | Quando usarlo |
|-------|-----------|---------------|
| **Time series** | Metriche nel tempo | CPU, traffico, latenza — il tipo predefinito |
| **Gauge** | Valore percentuale attuale | Disco usato, memoria, SLO compliance |
| **Stat** | Singolo valore con trend | Uptime, request count, error rate |
| **Table** | Dati tabulari | Lista di target, top-N |
| **Heatmap** | Distribuzione nel tempo | Distribuzione latenza (histogram_quantile) |
| **Bar chart** | Confronto tra categorie | Errori per endpoint, traffico per datacenter |
| **Logs** | Visualizzazione log | Integrazione con Loki |
| **Node graph** | Relazioni tra entità | Topologia di rete, dipendenze servizi |
| **Alert list** | Alert attivi | Dashboard overview |
| **Status history** | Stato nel tempo | Uptime storico per servizio |

### Variabili (Template Variables)

Le variabili rendono le dashboard riutilizzabili e interattive:

```
# Variabile "instance" — query tipo
Label values:
  Query: label_values(up{job="node"}, instance)
  Multi-value: enabled
  Include All option: enabled

# Variabile "job"
  Query: label_values(up, job)

# Variabile "mountpoint"
  Query: label_values(node_filesystem_size_bytes{instance="$instance"}, mountpoint)

# Variabile intervallo (custom)
  Type: Interval
  Values: 1m, 5m, 15m, 1h

# Variabile da datasource
  Type: Data source
  Type filter: Prometheus
```

Uso nelle query:

```promql
# Usare la variabile $instance nei panel
100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle", instance=~"$instance"}[5m])) * 100)

# Multi-value (regex match)
node_memory_MemAvailable_bytes{instance=~"$instance"}

# Variabile intervallo
rate(http_requests_total{job="$job"}[$__rate_interval])
```

### Alert in Grafana

```yaml
# Alert rule example (in Grafana UI o provisioning)
# Disco > 85%
# Condition: WHEN avg() OF query(A, 5m, now) IS ABOVE 85
# Query A: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100

# Canali notifica: Email, Slack, PagerDuty, Telegram, Webhook
```

### Grafana Alerting (Unified Alerting)

Dal Grafana 9+, il sistema di alerting è unificato:

```yaml
# Alert rule via provisioning
# /etc/grafana/provisioning/alerting/alerts.yml
apiVersion: 1
groups:
  - orgId: 1
    name: Infrastructure
    folder: Alerts
    interval: 1m
    rules:
      - uid: disk-space-alert
        title: Disk Space Low
        condition: C
        data:
          - refId: A
            relativeTimeRange:
              from: 600
              to: 0
            datasourceUid: prometheus
            model:
              expr: (1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100
          - refId: B
            relativeTimeRange:
              from: 600
              to: 0
            datasourceUid: __expr__
            model:
              type: reduce
              expression: A
              reducer: last
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              expression: B
              conditions:
                - evaluator:
                    type: gt
                    params: [85]
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Disco quasi pieno"

# Contact point
contactPoints:
  - orgId: 1
    name: slack-ops
    receivers:
      - uid: slack-receiver
        type: slack
        settings:
          url: "https://hooks.slack.com/services/xxx"
          recipient: "#infra-alerts"
          title: '{{ template "slack.default.title" . }}'

# Notification policy
policies:
  - orgId: 1
    receiver: slack-ops
    group_by: ['alertname', 'instance']
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
    routes:
      - receiver: pagerduty-critical
        matchers:
          - severity = critical
        continue: false
```

### Dashboard as Code (Provisioning)

```yaml
# /etc/grafana/provisioning/datasources/datasources.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    editable: false
    jsonData:
      tracesToLogsV2:
        datasourceUid: loki
      nodeGraph:
        enabled: true
```

```yaml
# /etc/grafana/provisioning/dashboards/dashboards.yml
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: 'Provisioned'
    type: file
    disableDeletion: true
    updateIntervalSeconds: 30
    options:
      path: /etc/grafana/dashboards
      foldersFromFilesStructure: true
```

Dashboard JSON salvate in `/etc/grafana/dashboards/` vengono caricate automaticamente. Gestire le dashboard in Git per version control.

### Grafonnet (Dashboard as Code con Jsonnet)

```jsonnet
// dashboard.jsonnet
local grafana = import 'grafonnet/grafana.libsonnet';
local dashboard = grafana.dashboard;
local row = grafana.row;
local prometheus = grafana.prometheus;
local graphPanel = grafana.graphPanel;

dashboard.new(
  'Node Overview',
  schemaVersion=27,
  tags=['infrastructure', 'node'],
  refresh='30s',
)
.addTemplate(
  grafana.template.datasource('datasource', 'prometheus', 'Prometheus')
)
.addTemplate(
  grafana.template.query('instance', 'label_values(up{job="node"}, instance)', datasource='$datasource', multi=true, includeAll=true)
)
.addPanel(
  graphPanel.new(
    'CPU Usage',
    datasource='$datasource',
    format='percent',
    min=0,
    max=100,
  )
  .addTarget(
    prometheus.target(
      '100 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle",instance=~"$instance"}[5m])) * 100',
      legendFormat='{{instance}}'
    )
  ),
  gridPos={x: 0, y: 0, w: 12, h: 8}
)
```

---

## Node Exporter e Metriche

Node Exporter espone le metriche del sistema Linux per Prometheus.

```bash
# Installazione
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xzf node_exporter-*.tar.gz
sudo cp node_exporter-*/node_exporter /usr/local/bin/
sudo useradd -rs /bin/false node_exporter
```

```ini
# /etc/systemd/system/node_exporter.service
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter \
  --collector.systemd \
  --collector.processes
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now node_exporter
# Metriche disponibili su http://server:9100/metrics

# Exporter per servizi specifici:
# nginx-prometheus-exporter    (porta 9113)
# postgres_exporter            (porta 9187)
# mysqld_exporter              (porta 9104)
# redis_exporter               (porta 9121)
# blackbox_exporter            (probe HTTP/TCP/ICMP)
```

### Metriche CPU Spiegate

```promql
# node_cpu_seconds_total — counter cumulativo di secondi CPU per modalità
# Mode: user, system, idle, iowait, irq, softirq, steal, nice, guest

# CPU utilization totale (escludendo idle)
100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# CPU per modalità (user vs system vs iowait)
avg by(instance, mode)(rate(node_cpu_seconds_total{mode=~"user|system|iowait"}[5m])) * 100

# Context switch rate
rate(node_context_switches_total[5m])

# CPU steal (virtualizzazione — il hypervisor ruba cicli CPU)
avg by(instance)(rate(node_cpu_seconds_total{mode="steal"}[5m])) * 100

# Interrupt rate
rate(node_intr_total[5m])
```

### Metriche Memoria Spiegate

```promql
# Memoria totale
node_memory_MemTotal_bytes

# Memoria disponibile (il kernel la stima includendo cache reclaimable)
node_memory_MemAvailable_bytes

# Memoria usata effettivamente
node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes

# Buffer e cache (possono essere liberate)
node_memory_Buffers_bytes + node_memory_Cached_bytes

# Swap usato
node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes

# Swap in/out (attività swap — segnale di memory pressure)
rate(node_vmstat_pswpin[5m])
rate(node_vmstat_pswpout[5m])

# Page faults
rate(node_vmstat_pgmajfault[5m])    # Major faults (disco)
rate(node_vmstat_pgfault[5m])       # Minor + major faults

# OOM kill counter
node_vmstat_oom_kill
```

### Metriche Disco / I/O

```promql
# Spazio disco
node_filesystem_size_bytes{mountpoint="/"}
node_filesystem_avail_bytes{mountpoint="/"}
node_filesystem_free_bytes{mountpoint="/"}

# Nota: avail < free perché avail esclude spazio riservato a root

# Inode utilizzati (%)
(1 - node_filesystem_files_free{mountpoint="/"} / node_filesystem_files{mountpoint="/"}) * 100

# I/O throughput (byte/s)
rate(node_disk_read_bytes_total{device="sda"}[5m])
rate(node_disk_written_bytes_total{device="sda"}[5m])

# IOPS
rate(node_disk_reads_completed_total{device="sda"}[5m])
rate(node_disk_writes_completed_total{device="sda"}[5m])

# I/O latenza media per operazione
rate(node_disk_read_time_seconds_total{device="sda"}[5m])
/ rate(node_disk_reads_completed_total{device="sda"}[5m])

# Disk utilization (% tempo occupato)
rate(node_disk_io_time_seconds_total{device="sda"}[5m]) * 100

# I/O queue depth
rate(node_disk_io_time_weighted_seconds_total{device="sda"}[5m])
```

### Metriche Rete

```promql
# Throughput (byte/s)
rate(node_network_receive_bytes_total{device="eth0"}[5m])
rate(node_network_transmit_bytes_total{device="eth0"}[5m])

# Pacchetti/s
rate(node_network_receive_packets_total{device="eth0"}[5m])
rate(node_network_transmit_packets_total{device="eth0"}[5m])

# Errori
rate(node_network_receive_errs_total{device="eth0"}[5m])
rate(node_network_transmit_errs_total{device="eth0"}[5m])

# Dropped packets
rate(node_network_receive_drop_total{device="eth0"}[5m])
rate(node_network_transmit_drop_total{device="eth0"}[5m])

# Conntrack
node_nf_conntrack_entries
node_nf_conntrack_entries_limit

# Socket statistics
node_sockstat_TCP_alloc
node_sockstat_TCP_tw          # TIME_WAIT connections
node_sockstat_sockets_used
```

### Metriche Filesystem e Systemd

```promql
# Filesystem read-only check
node_filesystem_readonly{mountpoint="/"}

# Systemd service state
node_systemd_unit_state{name="nginx.service", state="active"}

# Servizi in stato failed
count(node_systemd_unit_state{state="failed"} == 1)

# File descriptor
node_filefd_allocated
node_filefd_maximum

# Processi
node_procs_running
node_procs_blocked
```

### Textfile Collector (Metriche Custom)

Il textfile collector permette di esporre metriche custom scrivendo file `.prom`:

```bash
# Abilitare il textfile collector
ExecStart=/usr/local/bin/node_exporter \
  --collector.systemd \
  --collector.processes \
  --collector.textfile.directory=/var/lib/node_exporter/textfile_collector

# Creare directory
sudo mkdir -p /var/lib/node_exporter/textfile_collector
sudo chown node_exporter:node_exporter /var/lib/node_exporter/textfile_collector
```

```bash
#!/bin/bash
# /usr/local/bin/collect-custom-metrics.sh
# Eseguire via cron ogni minuto

TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"

# Numero di connessioni PostgreSQL attive
PG_CONNS=$(sudo -u postgres psql -t -c "SELECT count(*) FROM pg_stat_activity WHERE state='active'" 2>/dev/null || echo 0)
cat > "${TEXTFILE_DIR}/postgres.prom" <<PROM
# HELP custom_postgres_active_connections Numero di connessioni PostgreSQL attive
# TYPE custom_postgres_active_connections gauge
custom_postgres_active_connections ${PG_CONNS}
PROM

# Dimensione coda email
MAIL_QUEUE=$(find /var/spool/postfix/deferred -type f 2>/dev/null | wc -l)
cat > "${TEXTFILE_DIR}/mailqueue.prom" <<PROM
# HELP custom_mail_queue_size Messaggi in coda deferred
# TYPE custom_mail_queue_size gauge
custom_mail_queue_size ${MAIL_QUEUE}
PROM

# Ultimo backup riuscito (timestamp epoch)
LAST_BACKUP=$(stat -c %Y /var/backups/latest.tar.gz 2>/dev/null || echo 0)
cat > "${TEXTFILE_DIR}/backup.prom" <<PROM
# HELP custom_last_backup_timestamp_seconds Epoch del ultimo backup
# TYPE custom_last_backup_timestamp_seconds gauge
custom_last_backup_timestamp_seconds ${LAST_BACKUP}
PROM

# Certificato SSL — giorni alla scadenza
CERT_EXPIRY=$(echo | openssl s_client -connect localhost:443 -servername localhost 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
if [ -n "$CERT_EXPIRY" ]; then
  EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s)
  NOW_EPOCH=$(date +%s)
  DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))
  cat > "${TEXTFILE_DIR}/cert.prom" <<PROM
# HELP custom_ssl_cert_days_remaining Giorni alla scadenza del certificato
# TYPE custom_ssl_cert_days_remaining gauge
custom_ssl_cert_days_remaining ${DAYS_LEFT}
PROM
fi
```

```
# crontab -e (utente node_exporter o root)
* * * * * /usr/local/bin/collect-custom-metrics.sh
```

### Elenco Exporter Comuni

| Exporter | Porta | Target |
|----------|-------|--------|
| node_exporter | 9100 | Metriche OS Linux |
| windows_exporter | 9182 | Metriche OS Windows |
| postgres_exporter | 9187 | PostgreSQL |
| mysqld_exporter | 9104 | MySQL/MariaDB |
| redis_exporter | 9121 | Redis |
| mongodb_exporter | 9216 | MongoDB |
| nginx-prometheus-exporter | 9113 | NGINX |
| apache_exporter | 9117 | Apache HTTPD |
| blackbox_exporter | 9115 | Probe HTTP/TCP/ICMP/DNS |
| snmp_exporter | 9116 | Dispositivi SNMP |
| haproxy_exporter | 9101 | HAProxy |
| elasticsearch_exporter | 9114 | Elasticsearch |
| rabbitmq_exporter | 9419 | RabbitMQ |
| kafka_exporter | 9308 | Apache Kafka |
| process-exporter | 9256 | Processi individuali |
| ipmi_exporter | 9290 | Hardware via IPMI |

---

## Alertmanager: Notifiche e Routing

### Architettura

Alertmanager riceve alert da Prometheus, li deduplica, li raggruppa, li silenzia e li instrada ai receiver appropriati:

```
Prometheus ──alert──▶ Alertmanager
                      ├── Deduplication (stessa fingerprint)
                      ├── Grouping (raggruppa per label)
                      ├── Inhibition (sopprime alert correlati)
                      ├── Silencing (muting temporaneo)
                      └── Routing (instrada a receiver)
                           ├── Email
                           ├── Slack
                           ├── PagerDuty
                           ├── OpsGenie
                           ├── Telegram
                           └── Webhook
```

### Configurazione Completa

```yaml
# /opt/alertmanager/alertmanager.yml
global:
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'password'
  resolve_timeout: 5m

# Template personalizzati per notifiche
templates:
  - '/opt/alertmanager/templates/*.tmpl'

route:
  receiver: 'email-team'
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  group_by: ['alertname', 'cluster', 'service']
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      group_wait: 10s
      repeat_interval: 1h
      continue: false

    - match:
        severity: warning
      receiver: 'slack-warnings'
      group_wait: 1m
      repeat_interval: 4h

    - match_re:
        alertname: '^(Disk|Filesystem).*'
      receiver: 'email-storage-team'
      group_by: ['alertname', 'instance', 'mountpoint']

    - match:
        team: database
      receiver: 'slack-dba'
      routes:
        - match:
            severity: critical
          receiver: 'pagerduty-dba'

receivers:
  - name: 'email-team'
    email_configs:
      - to: 'team@example.com'
        send_resolved: true
        headers:
          Subject: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'

  - name: 'slack-warnings'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/xxx'
        channel: '#alerts'
        send_resolved: true
        title: '{{ .Status | toUpper }}: {{ .GroupLabels.alertname }}'
        text: >-
          {{ range .Alerts }}
          *Alert:* {{ .Annotations.summary }}
          *Istanza:* {{ .Labels.instance }}
          *Severity:* {{ .Labels.severity }}
          *Descrizione:* {{ .Annotations.description }}
          {{ end }}
        color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: 'xxx'
        severity: '{{ .CommonLabels.severity }}'
        description: '{{ .CommonAnnotations.summary }}'
        details:
          firing: '{{ .Alerts.Firing | len }}'
          resolved: '{{ .Alerts.Resolved | len }}'
          instances: '{{ range .Alerts }}{{ .Labels.instance }} {{ end }}'

  - name: 'email-storage-team'
    email_configs:
      - to: 'storage-team@example.com'
        send_resolved: true

  - name: 'slack-dba'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/yyy'
        channel: '#dba-alerts'
        send_resolved: true

  - name: 'pagerduty-dba'
    pagerduty_configs:
      - service_key: 'zzz'

  - name: 'telegram-ops'
    webhook_configs:
      - url: 'http://alertmanager-telegram-bot:9087/alert'
        send_resolved: true
```

### Inhibition Rules

L'inibizione sopprime alert quando un altro alert correlato è già attivo. Esempio: se l'intero nodo è down, non serve ricevere anche gli alert per singoli servizi su quel nodo.

```yaml
inhibit_rules:
  # Se il nodo è down, sopprimere tutti gli alert su quel nodo
  - source_matchers:
      - alertname = ServiceDown
    target_matchers:
      - severity =~ "warning|info"
    equal: ['instance']

  # Se un alert critical è attivo, sopprimere warning dello stesso tipo
  - source_matchers:
      - severity = critical
    target_matchers:
      - severity = warning
    equal: ['alertname', 'instance']

  # Se il cluster è down, sopprimere alert dei singoli nodi
  - source_matchers:
      - alertname = ClusterDown
    target_matchers:
      - alertname =~ ".*"
    equal: ['cluster']
```

### Silencing (Muting Temporaneo)

```bash
# Creare un silence via amtool
amtool silence add \
  --alertmanager.url=http://localhost:9093 \
  --author="admin" \
  --comment="Manutenzione programmata server1" \
  --duration=2h \
  instance="server1:9100"

# Silence per regex
amtool silence add \
  --alertmanager.url=http://localhost:9093 \
  --author="admin" \
  --comment="Deploy in corso" \
  --duration=30m \
  alertname=~"High.*" job="api"

# Elenco silence attivi
amtool silence query --alertmanager.url=http://localhost:9093

# Rimuovere un silence
amtool silence expire --alertmanager.url=http://localhost:9093 <silence-id>

# Verificare configurazione
amtool check-config /opt/alertmanager/alertmanager.yml

# Test routing — dove andrebbe un alert?
amtool config routes test --config.file=/opt/alertmanager/alertmanager.yml \
  severity=critical alertname=HighCPU
```

### Alertmanager in HA

```bash
# Alertmanager supporta clustering nativo (gossip protocol)
# Nodo 1
alertmanager --config.file=alertmanager.yml \
  --cluster.listen-address=0.0.0.0:9094 \
  --cluster.peer=alertmanager2:9094

# Nodo 2
alertmanager --config.file=alertmanager.yml \
  --cluster.listen-address=0.0.0.0:9094 \
  --cluster.peer=alertmanager1:9094

# In Prometheus, configurare entrambi
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager1:9093', 'alertmanager2:9093']
```

### Routing Avanzato e Finestre di Manutenzione

Alertmanager supporta strategie di routing sofisticate tramite `time_intervals`, `mute_time_intervals` e il parametro `continue` per cascading di receiver multipli.

#### Time Intervals e Orari di Business

```yaml
# alertmanager.yml — routing basato su fasce orarie
time_intervals:
  - name: business_hours
    time_intervals:
      - weekdays: ['monday:friday']
        times:
          - start_time: '09:00'
            end_time: '18:00'
        location: 'Europe/Rome'

  - name: weekend
    time_intervals:
      - weekdays: ['saturday', 'sunday']
        location: 'Europe/Rome'

  - name: maintenance_window
    time_intervals:
      - weekdays: ['wednesday']
        times:
          - start_time: '02:00'
            end_time: '06:00'
        location: 'Europe/Rome'

route:
  receiver: 'default-slack'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    # Alert critici: sempre notifica, anche di notte
    - matchers:
        - severity="critical"
      receiver: 'pagerduty-critical'
      continue: true  # continua per inviare anche a Slack

    # Durante orario lavorativo: Slack + email
    - matchers:
        - severity=~"warning|info"
      active_time_intervals:
        - business_hours
      receiver: 'slack-team'

    # Fuori orario: solo critical (warning silenziati)
    - matchers:
        - severity="warning"
      mute_time_intervals:
        - weekend
      receiver: 'slack-low-priority'

    # Manutenzione: silenziare alert infrastruttura
    - matchers:
        - team="infrastructure"
      mute_time_intervals:
        - maintenance_window
      receiver: 'slack-infra'
```

#### Nuova Sintassi Matchers (v0.22+)

La sintassi legacy `match` e `match_re` è deprecata. Usare la nuova sintassi `matchers`:

```yaml
# LEGACY (deprecato)
match:
  severity: critical
match_re:
  service: "api|web|worker"

# NUOVA SINTASSI (obbligatoria da v0.27+)
matchers:
  - severity="critical"
  - service=~"api|web|worker"
  - alertname!="Watchdog"          # negazione esatta
  - namespace!~"kube-system|test"  # negazione regex

# Operatori disponibili:
#   =   match esatto
#   !=  negazione esatta
#   =~  match regex
#   !~  negazione regex
```

#### Pattern `continue: true` per Multi-Receiver

Il parametro `continue: true` permette a un alert di attraversare più route, inviando notifiche a receiver multipli:

```yaml
routes:
  # 1. Invia a PagerDuty per on-call
  - matchers:
      - severity="critical"
    receiver: 'pagerduty'
    continue: true    # non fermarti, continua matching

  # 2. Invia anche a Slack per visibilità team
  - matchers:
      - severity="critical"
    receiver: 'slack-critical'
    continue: true

  # 3. Registra in webhook per audit trail
  - matchers:
      - severity="critical"
    receiver: 'audit-webhook'
```

#### Test e Validazione del Routing

```bash
# Validare la configurazione prima di applicare
amtool check-config alertmanager.yml

# Testare dove un alert verrebbe instradato
amtool config routes test \
  --config.file=alertmanager.yml \
  severity=critical service=api-gateway team=platform

# Output:
# Routing tree:
# └── default-receiver: 'default-slack'
#     ├── receiver: 'pagerduty-critical' (continue: true)
#     ├── receiver: 'slack-critical' (continue: true)
#     └── receiver: 'audit-webhook'

# Visualizzare l'albero di routing completo
amtool config routes show --config.file=alertmanager.yml

# Creare un silence programmatico per manutenzione
amtool silence add \
  --alertmanager.url=http://localhost:9093 \
  --author="ops-team" \
  --comment="Manutenzione DB pianificata" \
  --duration=4h \
  'job=~"mysql|postgres"' 'severity=~"warning|info"'
```

#### Inhibition Rules Avanzate

Le regole di inibizione sopprimono alert ridondanti quando un alert più grave è già attivo:

```yaml
inhibit_rules:
  # Se un nodo è down, sopprimere tutti gli alert dei servizi su quel nodo
  - source_matchers:
      - alertname="NodeDown"
    target_matchers:
      - severity=~"warning|info"
    equal: ['instance']

  # Se il cluster è degradato, sopprimere alert singoli pod
  - source_matchers:
      - alertname="ClusterDegraded"
      - severity="critical"
    target_matchers:
      - alertname=~"PodCrashLooping|PodNotReady"
    equal: ['cluster']

  # Se la rete è irraggiungibile, sopprimere alert di latenza
  - source_matchers:
      - alertname="NetworkUnreachable"
    target_matchers:
      - alertname=~"HighLatency|SlowResponse"
    equal: ['datacenter']
```

---

## Zabbix: Architettura e Configurazione

Zabbix è una piattaforma di monitoring enterprise open-source con architettura agent-based e agentless.

### Architettura

```
┌──────────────────────────────┐
│       Zabbix Server          │
│  ┌──────────┐ ┌───────────┐ │
│  │ Poller   │ │ Database  │ │     PostgreSQL / MySQL / TimescaleDB
│  │ (data    │ │ (storage) │ │
│  │ collect) │ └───────────┘ │
│  └──────────┘ ┌───────────┐ │
│  ┌──────────┐ │ Alerter   │ │
│  │ Trapper  │ │ (notif)   │ │
│  │ (receive)│ └───────────┘ │
│  └──────────┘               │
│  ┌──────────┐               │
│  │ Pre-     │               │
│  │ processor│               │
│  └──────────┘               │
└──────────────────────────────┘
       ▲              ▲
       │              │
  Zabbix Agent    Zabbix Proxy
  (su ogni host)  (datacenter remoto)
       │              │
  ┌────▼────┐    ┌────▼────────────┐
  │ Host 1  │    │ Remote site     │
  │ Host 2  │    │  ├── Host 10    │
  │ Host 3  │    │  ├── Host 11    │
  └─────────┘    │  └── Host 12    │
                 └─────────────────┘

Frontend Web (PHP o Nginx+Go)
```

### Installazione (Debian/Ubuntu)

```bash
# Repository ufficiale
wget https://repo.zabbix.com/zabbix/7.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_7.0-1+ubuntu24.04_all.deb
sudo dpkg -i zabbix-release_7.0-1+ubuntu24.04_all.deb
sudo apt update

# Server, frontend, agent
sudo apt install zabbix-server-pgsql zabbix-frontend-php zabbix-apache-conf \
  zabbix-sql-scripts zabbix-agent2

# Database
sudo -u postgres createuser zabbix
sudo -u postgres createdb -O zabbix zabbix
zcat /usr/share/zabbix-sql-scripts/postgresql/server.sql.gz | sudo -u zabbix psql zabbix

# Configurazione server
# /etc/zabbix/zabbix_server.conf
# DBHost=localhost
# DBName=zabbix
# DBUser=zabbix
# DBPassword=<password>

sudo systemctl enable --now zabbix-server zabbix-agent2 apache2
# Frontend: http://server/zabbix (default: Admin/zabbix)
```

### Template

I template definiscono cosa monitorare. Zabbix include template predefiniti per centinaia di sistemi:

```
Template: "Linux by Zabbix agent active"
├── Items (metriche raccolte)
│   ├── system.cpu.util[,idle]
│   ├── vm.memory.size[available]
│   ├── vfs.fs.size[/,pfree]
│   ├── net.if.in[eth0]
│   ├── system.uptime
│   └── ...
├── Triggers (condizioni di alert)
│   ├── CPU > 80% per 5m → WARNING
│   ├── Disco < 15% → HIGH
│   ├── Servizio down → DISASTER
│   └── ...
├── Graphs (grafici predefiniti)
│   ├── CPU usage
│   ├── Memory usage
│   └── Network traffic
├── Discovery rules (LLD)
│   ├── Filesystem discovery
│   ├── Network interface discovery
│   └── ...
└── Web scenarios
    └── HTTP availability check
```

### Trigger Expressions

```
# Sintassi Zabbix 7.x
# CPU utilization > 80% per 5 minuti
avg(/Linux by Zabbix agent/system.cpu.util[,idle],5m) < 20

# Disco libero < 10%
last(/Linux by Zabbix agent/vfs.fs.size[/,pfree]) < 10

# Servizio non in esecuzione
last(/Linux by Zabbix agent/proc.num[nginx]) = 0

# Più di 100 connessioni sulla porta 3306
last(/Linux by Zabbix agent/net.tcp.count[,,3306,established]) > 100

# Differenza rispetto al valore di 1 ora fa (anomaly detection)
abs(last(/host/metric) - avg(/host/metric,1h)) > 2 * stddev(/host/metric,1h)

# Trigger con dipendenza (hysteresis)
# Trigger: disco pieno
avg(/host/vfs.fs.size[/,pfree],5m) < 10
# Recovery: disco > 15%
avg(/host/vfs.fs.size[/,pfree],5m) > 15
```

### Low-Level Discovery (LLD)

LLD scopre automaticamente risorse (filesystem, interfacce di rete, database, ecc.):

```json
// Esempio di output discovery per filesystem
{
  "data": [
    {"{#FSNAME}": "/", "{#FSTYPE}": "ext4"},
    {"{#FSNAME}": "/home", "{#FSTYPE}": "ext4"},
    {"{#FSNAME}": "/var", "{#FSTYPE}": "ext4"}
  ]
}
```

```bash
# LLD custom script — scoperta database PostgreSQL
#!/bin/bash
# /usr/local/bin/discover_pg_databases.sh
DBS=$(sudo -u postgres psql -t -c "SELECT datname FROM pg_database WHERE NOT datistemplate AND datname != 'postgres'")
echo '{"data":['
FIRST=true
for DB in $DBS; do
  if [ "$FIRST" = true ]; then FIRST=false; else echo ','; fi
  echo "  {\"{#DBNAME}\": \"$DB\"}"
done
echo ']}'
```

Item prototype basato su LLD:

```
Item key: custom.pg.dbsize[{#DBNAME}]
→ crea automaticamente:
  custom.pg.dbsize[mydb]
  custom.pg.dbsize[appdb]
  custom.pg.dbsize[analytics]
```

### Proxy Zabbix

Per siti remoti o grandi infrastrutture, il proxy raccoglie dati localmente e li inoltra al server centrale:

```ini
# /etc/zabbix/zabbix_proxy.conf
ProxyMode=0          # 0=attivo (push verso server), 1=passivo (server fa pull)
Server=zabbix-server.example.com
Hostname=proxy-datacenter-eu
DBName=/var/lib/zabbix/proxy.db   # SQLite per proxy leggero
DataSenderFrequency=5
ConfigFrequency=300
```

### Mass Deployment con Autoregistration

```
# In Zabbix Server → Configuration → Actions → Autoregistration
# Condition: Host metadata contains "linux-production"
# Operations:
#   1. Add host
#   2. Link template "Linux by Zabbix agent active"
#   3. Add to host group "Production/Linux"
```

```ini
# /etc/zabbix/zabbix_agent2.conf (su ogni host)
Server=zabbix-server.example.com
ServerActive=zabbix-server.example.com
Hostname=web-server-42
HostMetadata=linux-production webserver
# L'agent si registra automaticamente al primo avvio
```

---

## Nagios/Icinga2: Panoramica e Configurazione

Nagios e Icinga sono sistemi di monitoring tradizionali, basati su check attivi (il server esegue check periodici sugli host).

```bash
# Icinga2 (fork moderno di Nagios)
sudo apt install icinga2 monitoring-plugins icingaweb2

# Concetti chiave:
# Host: un server/dispositivo monitorato
# Service: un servizio su un host (HTTP, SSH, disco, CPU)
# Check: il test eseguito (plugin)
# Notification: alert quando un check fallisce

# Plugin standard (monitoring-plugins)
/usr/lib/nagios/plugins/check_http -H example.com
/usr/lib/nagios/plugins/check_disk -w 80% -c 90%
/usr/lib/nagios/plugins/check_load -w 5,4,3 -c 10,8,6
/usr/lib/nagios/plugins/check_ssh -H server
/usr/lib/nagios/plugins/check_tcp -H server -p 3306

# Differenze con Prometheus:
# Nagios/Icinga: check attivi, stato (OK/WARNING/CRITICAL), host-centric
# Prometheus: metriche pull, time-series, query-centric, più flessibile
```

### Architettura Icinga2

```
┌─────────────────────────────┐
│        Icinga2 Master       │
│  ┌───────────┐              │
│  │ Check     │              │
│  │ Scheduler │              │     ┌───────────┐
│  └───────────┘              │────▶│ IcingaDB  │──▶ Redis + PostgreSQL
│  ┌───────────┐              │     └───────────┘
│  │ Plugin    │              │          │
│  │ Executor  │              │          ▼
│  └───────────┘              │     ┌───────────┐
│  ┌───────────┐              │     │ Icinga    │
│  │ Notifier  │              │     │ Web 2     │
│  └───────────┘              │     └───────────┘
└──────────┬──────────────────┘
           │ (API / cluster)
    ┌──────▼───────┐
    │ Icinga2      │
    │ Satellite    │     (per datacenter remoti)
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │ Icinga2      │
    │ Agent        │     (su ogni host monitorato)
    └──────────────┘
```

### Configurazione Host e Servizio (Icinga2)

```
// /etc/icinga2/zones.d/master/hosts.conf
object Host "web-server-01" {
  import "generic-host"
  address = "192.168.1.10"
  vars.os = "Linux"
  vars.role = "webserver"
  vars.notification["mail"] = {
    groups = ["ops-team"]
  }
}

object Host "db-server-01" {
  import "generic-host"
  address = "192.168.1.20"
  vars.os = "Linux"
  vars.role = "database"
  vars.notification["mail"] = {
    groups = ["dba-team"]
  }
}
```

```
// /etc/icinga2/zones.d/master/services.conf
apply Service "http" {
  import "generic-service"
  check_command = "http"
  vars.http_uri = "/"
  vars.http_ssl = true
  vars.http_expect = "200"
  assign where host.vars.role == "webserver"
}

apply Service "disk" {
  import "generic-service"
  check_command = "disk"
  vars.disk_wfree = "20%"
  vars.disk_cfree = "10%"
  assign where host.vars.os == "Linux"
}

apply Service "load" {
  import "generic-service"
  check_command = "load"
  vars.load_wload1 = 5
  vars.load_wload5 = 4
  vars.load_wload15 = 3
  vars.load_cload1 = 10
  vars.load_cload5 = 8
  vars.load_cload15 = 6
  assign where host.vars.os == "Linux"
}

apply Service "ssh" {
  import "generic-service"
  check_command = "ssh"
  assign where host.vars.os == "Linux"
}

apply Service "postgres" {
  import "generic-service"
  check_command = "pgsql"
  vars.pgsql_hostname = host.address
  assign where host.vars.role == "database"
}
```

### Check Command Custom

```
// /etc/icinga2/zones.d/master/commands.conf
object CheckCommand "check_cert_expiry" {
  command = [ PluginDir + "/check_ssl_cert" ]
  arguments = {
    "-H" = "$cert_host$"
    "-p" = "$cert_port$"
    "-w" = "$cert_warn_days$"
    "-c" = "$cert_crit_days$"
  }
  vars.cert_port = 443
  vars.cert_warn_days = 30
  vars.cert_crit_days = 7
}

apply Service "ssl-certificate" {
  import "generic-service"
  check_command = "check_cert_expiry"
  vars.cert_host = host.address
  check_interval = 6h
  assign where host.vars.role == "webserver"
}
```

### Notification (Icinga2)

```
// Notifica via email
apply Notification "mail-ops" to Service {
  import "mail-service-notification"
  users = ["admin"]
  user_groups = ["ops-team"]
  states = [ Warning, Critical ]
  types = [ Problem, Recovery ]
  period = "24x7"
  assign where service.vars.notification.mail
}

// Escalation — se non risolto in 30 minuti, notifica il manager
apply Notification "escalation-manager" to Service {
  import "mail-service-notification"
  users = ["manager"]
  times = {
    begin = 30m
    end = 2h
  }
  states = [ Critical ]
  types = [ Problem ]
  assign where service.vars.notification.mail
}
```

---

## Uptime Monitoring e Blackbox Exporter

### Blackbox Exporter

Il Blackbox Exporter esegue probe attivi (HTTP, TCP, ICMP, DNS, gRPC) per verificare la raggiungibilità e la salute degli endpoint:

```yaml
# /opt/blackbox_exporter/blackbox.yml
modules:
  http_2xx:
    prober: http
    timeout: 10s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: [200]
      method: GET
      follow_redirects: true
      fail_if_ssl: false
      fail_if_not_ssl: false
      tls_config:
        insecure_skip_verify: false

  http_post_2xx:
    prober: http
    http:
      method: POST
      headers:
        Content-Type: application/json
      body: '{"health": "check"}'

  http_ssl_expiry:
    prober: http
    http:
      valid_status_codes: [200, 301, 302, 403]
      fail_if_not_ssl: true
    timeout: 15s

  tcp_connect:
    prober: tcp
    timeout: 5s

  icmp_ping:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: "ip4"

  dns_resolution:
    prober: dns
    timeout: 5s
    dns:
      query_name: "example.com"
      query_type: "A"
      valid_rcode: ["NOERROR"]
      validate_answer_rrs:
        fail_if_not_matches_regexp:
          - ".*"

  grpc_health:
    prober: grpc
    timeout: 5s
    grpc:
      tls: false
      service: "health"
```

```yaml
# prometheus.yml — configurazione scrape per blackbox
scrape_configs:
  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://example.com
          - https://api.example.com/health
          - https://app.example.com
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115

  - job_name: 'blackbox-icmp'
    metrics_path: /probe
    params:
      module: [icmp_ping]
    static_configs:
      - targets:
          - 192.168.1.1      # Router
          - 10.0.0.1          # Gateway
          - 8.8.8.8           # DNS esterno
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115

  - job_name: 'blackbox-ssl-expiry'
    metrics_path: /probe
    params:
      module: [http_ssl_expiry]
    static_configs:
      - targets:
          - https://example.com
          - https://secure.example.com
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

### Alert per Uptime e Certificati

```yaml
groups:
  - name: blackbox_alerts
    rules:
      - alert: EndpointDown
        expr: probe_success == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Endpoint {{ $labels.instance }} non raggiungibile"

      - alert: SSLCertExpiringSoon
        expr: (probe_ssl_earliest_cert_expiry - time()) / 86400 < 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Certificato SSL di {{ $labels.instance }} scade tra {{ $value | humanize }} giorni"

      - alert: SSLCertExpiringCritical
        expr: (probe_ssl_earliest_cert_expiry - time()) / 86400 < 7
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "Certificato SSL di {{ $labels.instance }} scade tra {{ $value | humanize }} giorni"

      - alert: HighProbeLatency
        expr: probe_duration_seconds > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Latenza alta verso {{ $labels.instance }}: {{ $value }}s"

      - alert: HTTPStatusCodeError
        expr: probe_http_status_code != 200
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.instance }} risponde con status {{ $value }}"
```

### Synthetic Monitoring

Il synthetic monitoring simula il percorso dell'utente con script automatizzati:

```bash
# Script synthetic monitoring con curl
#!/bin/bash
# /usr/local/bin/synthetic-check.sh
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
TARGET="https://app.example.com"

# Login flow
START=$(date +%s%N)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$TARGET/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"user":"healthcheck","pass":"xxx"}')
END=$(date +%s%N)
DURATION=$(echo "scale=3; ($END - $START) / 1000000000" | bc)

cat > "$TEXTFILE_DIR/synthetic.prom" <<PROM
# HELP synthetic_login_duration_seconds Durata del login flow
# TYPE synthetic_login_duration_seconds gauge
synthetic_login_duration_seconds{target="app"} $DURATION
# HELP synthetic_login_success Login riuscito (1) o fallito (0)
# TYPE synthetic_login_success gauge
synthetic_login_success{target="app"} $([ "$HTTP_CODE" = "200" ] && echo 1 || echo 0)
PROM
```

---

## Log Monitoring: Loki, ELK, Alert su Log

### Grafana Loki

Loki è il sistema di log aggregation progettato per integrarsi con Grafana. A differenza di Elasticsearch, Loki indicizza solo le label, non il contenuto dei log.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Promtail   │    │   Promtail   │    │   Promtail   │
│   (agent)    │    │   (agent)    │    │   (agent)    │
│   Host A     │    │   Host B     │    │   Host C     │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────┬───────┴───────────┬───────┘
                   │                   │
            ┌──────▼───────────────────▼──────┐
            │              Loki               │
            │  ┌──────────┐  ┌─────────────┐  │
            │  │Distributor│  │ Ingester    │  │
            │  └──────────┘  └─────────────┘  │
            │  ┌──────────┐  ┌─────────────┐  │
            │  │ Querier  │  │ Compactor   │  │
            │  └──────────┘  └─────────────┘  │
            └──────────────────────────────────┘
                         │
                    ┌────▼────┐
                    │ Grafana │  (Explore → Logs)
                    └─────────┘
```

### Installazione Loki + Promtail

```yaml
# /etc/loki/loki-config.yml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /var/lib/loki
  storage:
    filesystem:
      chunks_directory: /var/lib/loki/chunks
      rules_directory: /var/lib/loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

limits_config:
  retention_period: 30d
  max_query_series: 5000

compactor:
  working_directory: /var/lib/loki/compactor
  compaction_interval: 10m
  retention_enabled: true
```

```yaml
# /etc/promtail/promtail-config.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /var/lib/promtail/positions.yml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Log di sistema (syslog)
  - job_name: system
    static_configs:
      - targets: ['localhost']
        labels:
          job: syslog
          host: ${HOSTNAME}
          __path__: /var/log/syslog

  # Auth log
  - job_name: auth
    static_configs:
      - targets: ['localhost']
        labels:
          job: auth
          host: ${HOSTNAME}
          __path__: /var/log/auth.log

  # NGINX access log
  - job_name: nginx
    static_configs:
      - targets: ['localhost']
        labels:
          job: nginx
          type: access
          __path__: /var/log/nginx/access.log
    pipeline_stages:
      - regex:
          expression: '^(?P<remote_addr>[\w\.]+) - (?P<remote_user>\S+) \[(?P<time_local>[^\]]+)\] "(?P<method>\w+) (?P<request_uri>\S+) (?P<protocol>\S+)" (?P<status>\d+) (?P<body_bytes_sent>\d+)'
      - labels:
          method:
          status:
      - metrics:
          nginx_request_duration:
            type: Histogram
            description: "request duration"
            source: request_time
            config:
              buckets: [0.01, 0.05, 0.1, 0.5, 1, 5]

  # Journal (systemd)
  - job_name: journal
    journal:
      json: false
      max_age: 12h
      labels:
        job: systemd-journal
    relabel_configs:
      - source_labels: ['__journal__systemd_unit']
        target_label: unit
      - source_labels: ['__journal_priority_keyword']
        target_label: level
```

### LogQL (Query Language di Loki)

```logql
# Filtrare per label
{job="nginx", status="500"}

# Filtrare per contenuto
{job="syslog"} |= "error"

# Regex nel contenuto
{job="auth"} |~ "Failed password.*ssh"

# Negazione
{job="nginx"} != "healthcheck"

# Pipeline di parsing
{job="nginx"} | json | status >= 500

# Regex named groups + metriche
{job="nginx"} | regexp `(?P<ip>\S+) .* "(?P<method>\w+) (?P<path>\S+).*" (?P<status>\d+)`
  | status = "500"

# Aggregazioni (metriche derivate dai log)
# Rate di errori per minuto
rate({job="nginx"} |= "500" [1m])

# Conteggio per label
sum by (status)(count_over_time({job="nginx"} | json [5m]))

# Top 10 IP per richieste
topk(10, sum by (ip)(count_over_time({job="nginx"} | regexp `(?P<ip>\S+)` [1h])))
```

### Loki 3.x: Structured Metadata e Bloom Filters

Loki 3.x introduce cambiamenti architetturali significativi che migliorano le prestazioni delle query di ordini di grandezza rispetto a Loki 2.x.

#### Structured Metadata

Le structured metadata permettono di allegare coppie chiave-valore ai log senza includerle nel label set (evitando l'esplosione di cardinalità):

```bash
# Invio log con structured metadata via API push
curl -X POST http://loki:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d '{
    "streams": [{
      "stream": {"job": "api-server", "env": "production"},
      "values": [
        ["1716500000000000000", "GET /api/users 200 45ms", {
          "trace_id": "abc123def456",
          "user_id": "u-789",
          "request_id": "req-001",
          "response_time_ms": "45"
        }]
      ]
    }]
  }'
```

Le structured metadata sono queryabili in LogQL senza impatto sulla cardinalità:

```logql
# Filtrare per trace_id nelle structured metadata
{job="api-server"} | trace_id="abc123def456"

# Combinare label filter con metadata filter
{job="api-server", env="production"} | response_time_ms > 500 | user_id=~"u-.*"
```

#### Bloom Filters e V3 Block Schema

Loki 3.x utilizza bloom filters per accelerare le query full-text. Il sistema pre-calcola filtri probabilistici per ogni chunk, permettendo di escludere rapidamente chunk che sicuramente non contengono il termine cercato:

```yaml
# loki-config.yaml — abilitare bloom filters
schema_config:
  configs:
    - from: "2024-01-01"
      store: tsdb                  # TSDB come default (sostituisce boltdb-shipper)
      object_store: s3
      schema: v13
      index:
        prefix: loki_index_
        period: 24h

bloom_gateway:
  enabled: true
  ring:
    kvstore:
      store: memberlist

bloom_build:
  enabled: true
  builder:
    planner:
      min_table_offset: 1        # ritardo minimo in periodi di tabella
```

L'architettura bloom in Loki 3.x introduce due nuovi componenti:

- **Bloom Planner** — decide quali TSDB index necessitano di bloom filters, pianifica i task di build
- **Bloom Builder** — costruisce effettivamente i bloom blocks, sostituendo il vecchio Compactor per questa funzione
- **Bloom Gateway** — serve le query filtrando i chunk tramite i bloom filters pre-calcolati

Il risultato è una riduzione drastica dei chunk scansionati: query che prima richiedevano la scansione di migliaia di chunk ora toccano solo quelli rilevanti, con tempi di risposta ridotti del 90%+ su dataset di grandi dimensioni.

#### Supporto Nativo OpenTelemetry

Loki 3.x supporta l'ingestione nativa di log OTel senza conversione:

```yaml
# OTel Collector → Loki 3.x (configurazione exporter)
exporters:
  otlphttp/loki:
    endpoint: http://loki:3100/otlp
    tls:
      insecure: true

# Loki mappa automaticamente:
# - Resource attributes → stream labels (service.name, k8s.namespace.name)
# - Log attributes → structured metadata
# - Body → log line
```

Questo elimina la necessità di Promtail o Grafana Agent per pipeline OTel, unificando il formato di ingestione. Le resource attributes di OpenTelemetry vengono mappate automaticamente a stream labels, mentre i log attributes diventano structured metadata queryabili.

### Alert basati su Log

```yaml
# /etc/loki/rules/alerts.yml
groups:
  - name: log_alerts
    rules:
      - alert: HighErrorRateInLogs
        expr: |
          sum(rate({job="nginx"} |= "500" [5m])) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Alto tasso di errori 500 nei log nginx"

      - alert: SSHBruteForce
        expr: |
          sum(rate({job="auth"} |= "Failed password" [5m])) > 5
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Possibile brute force SSH rilevato"

      - alert: OOMInLogs
        expr: |
          count_over_time({job="systemd-journal"} |= "Out of memory" [5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "OOM killer attivato"
```

### ELK Stack (Panoramica)

Lo stack ELK (Elasticsearch + Logstash + Kibana) è l'alternativa enterprise per log management:

```
┌────────────────┐
│ Filebeat       │ ──▶ Logstash ──▶ Elasticsearch ──▶ Kibana
│ (log shipper)  │     (parsing)    (storage+search)  (visualize)
└────────────────┘

Alternativa leggera:
Filebeat ──────────────────▶ Elasticsearch ──▶ Kibana
(senza Logstash, parsing in Elasticsearch ingest pipelines)
```

Quando usare cosa:

| Criterio | Loki + Grafana | ELK/OpenSearch |
|----------|---------------|----------------|
| Full-text search | Limitato (grep-like) | Eccellente (inverted index) |
| Costo storage | Basso (solo label indicizzate) | Alto (tutto indicizzato) |
| Integrazione Prometheus | Nativa | Richiede adattamento |
| Complessità operativa | Bassa | Alta |
| Caso d'uso ideale | Correlazione metriche+log in Grafana | Analytics su log, compliance, audit |
| Scalabilità | Buona (object storage) | Eccellente ma costosa |

---

## APM e Distributed Tracing

### Concetti Fondamentali

Il distributed tracing segue una richiesta attraverso tutti i servizi che attraversa in un'architettura a microservizi:

```
Utente → API Gateway → Auth Service → User DB
                     → Product Service → Product DB
                     → Cache (Redis)
                     → Payment Service → External API (Stripe)
                     
Ogni "hop" è uno SPAN. L'insieme degli span è una TRACE.
```

| Termine | Definizione |
|---------|-----------|
| **Trace** | Percorso completo di una richiesta attraverso il sistema |
| **Span** | Singola operazione all'interno di una trace |
| **Trace ID** | Identificatore univoco propagato attraverso tutti i servizi |
| **Span ID** | Identificatore del singolo span |
| **Parent Span** | Lo span che ha generato lo span corrente |
| **Baggage** | Metadati propagati attraverso il contesto |

### Grafana Tempo

Tempo è il backend di tracing di Grafana, progettato per integrarsi con Loki e Prometheus:

```yaml
# /etc/tempo/tempo-config.yml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"
        http:
          endpoint: "0.0.0.0:4318"
    jaeger:
      protocols:
        thrift_http:
          endpoint: "0.0.0.0:14268"
        grpc:
          endpoint: "0.0.0.0:14250"

storage:
  trace:
    backend: local
    local:
      path: /var/lib/tempo/traces
    wal:
      path: /var/lib/tempo/wal

metrics_generator:
  registry:
    external_labels:
      source: tempo
  storage:
    path: /var/lib/tempo/generator
    remote_write:
      - url: http://prometheus:9090/api/v1/write
```

### Jaeger

```yaml
# docker-compose per Jaeger all-in-one (sviluppo)
services:
  jaeger:
    image: jaegertracing/all-in-one:1.54
    ports:
      - "16686:16686"    # UI
      - "14268:14268"    # Collector HTTP
      - "4317:4317"      # OTLP gRPC
      - "4318:4318"      # OTLP HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true
      - SPAN_STORAGE_TYPE=elasticsearch
      - ES_SERVER_URLS=http://elasticsearch:9200
```

### OpenTelemetry Collector

L'OTel Collector è il componente vendor-neutral per raccogliere, processare e esportare telemetria:

```yaml
# /etc/otel-collector/config.yml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"
      http:
        endpoint: "0.0.0.0:4318"
  prometheus:
    config:
      scrape_configs:
        - job_name: 'otel-collector'
          scrape_interval: 10s
          static_configs:
            - targets: ['localhost:8888']

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
  attributes:
    actions:
      - key: environment
        value: production
        action: upsert

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
  otlp/tempo:
    endpoint: "tempo:4317"
    tls:
      insecure: true
  loki:
    endpoint: "http://loki:3100/loki/api/v1/push"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, attributes]
      exporters: [otlp/tempo]
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [loki]
```

### Architettura Pipeline dell'OTel Collector

L'OpenTelemetry Collector elabora dati telemetrici attraverso pipeline componibili. Ogni pipeline è una sequenza: **Receivers → Processors → Exporters**, con i **Connectors** che collegano pipeline diverse.

```
┌─────────────────────────────────────────────────────────────────┐
│                    OTel Collector Pipeline                       │
│                                                                 │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │ Receivers │──▶│  Processors  │──▶│  Exporters   │            │
│  │           │   │              │   │              │            │
│  │ • otlp    │   │ • batch      │   │ • otlp       │            │
│  │ • prom    │   │ • filter     │   │ • prometheus  │            │
│  │ • filelog  │   │ • transform  │   │ • loki       │            │
│  │ • hostmet │   │ • tail_samp  │   │ • debug      │            │
│  └──────────┘   │ • resource   │   └──────────────┘            │
│                  └──────┬───────┘                                │
│                         │                                       │
│                  ┌──────▼───────┐                                │
│                  │  Connectors  │ (pipeline-to-pipeline)         │
│                  │ • spanmetrics│                                │
│                  │ • count      │                                │
│                  └──────────────┘                                │
└─────────────────────────────────────────────────────────────────┘
```

#### Processors Essenziali

```yaml
processors:
  # Filter: elimina telemetria indesiderata prima dell'export
  filter/drop-health:
    error_mode: ignore
    traces:
      span:
        - 'attributes["http.route"] == "/healthz"'
        - 'attributes["http.route"] == "/readyz"'
    metrics:
      metric:
        - 'name == "go_goroutines"'    # drop metriche interne Go

  # Transform: modifica attributi in-flight
  transform/enrich:
    error_mode: ignore
    trace_statements:
      - context: span
        statements:
          - set(attributes["deployment.environment"], "production")
          - truncate_all(attributes, 256)    # tronca valori lunghi

    metric_statements:
      - context: datapoint
        statements:
          - set(attributes["cluster"], "eu-west-1")

  # Tail Sampling: campionamento intelligente (solo su Collector gateway)
  tail_sampling:
    decision_wait: 10s
    num_traces: 100000
    expected_new_traces_per_sec: 1000
    policies:
      - name: errors-always
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow-traces
        type: latency
        latency: {threshold_ms: 1000}
      - name: probabilistic-rest
        type: probabilistic
        probabilistic: {sampling_percentage: 10}

  # Resource: aggiunge attributi a tutte le risorse
  resource/add-env:
    attributes:
      - key: deployment.environment
        value: production
        action: upsert
      - key: service.version
        from_attribute: app.version
        action: insert
```

#### Deployment: Agent vs Gateway

Due pattern di deployment complementari:

- **Agent mode** — un Collector per nodo/host, raccoglie telemetria locale, pre-processa e inoltra al gateway. Leggero, ~50 MB RAM
- **Gateway mode** — Collector centralizzato che riceve da tutti gli agent, esegue tail sampling, arricchimento e routing verso i backend. Scala orizzontalmente dietro un load balancer

```yaml
# Connectors: collegare pipeline diverse
connectors:
  # Genera metriche RED automatiche dagli span
  spanmetrics:
    histogram:
      explicit:
        buckets: [5ms, 10ms, 25ms, 50ms, 100ms, 500ms, 1s, 5s]
    dimensions:
      - name: http.method
      - name: http.status_code
    namespace: span.metrics

service:
  pipelines:
    traces/in:
      receivers: [otlp]
      processors: [memory_limiter, filter/drop-health, batch]
      exporters: [spanmetrics]   # connector come exporter

    metrics/spanmetrics:
      receivers: [spanmetrics]    # connector come receiver
      processors: [batch]
      exporters: [prometheus]
```

### Grafana Alloy: Sostituto di Grafana Agent

Grafana Alloy è il successore di Grafana Agent (EOL 1 novembre 2025) e costituisce una distribuzione OTel Collector con oltre 120 componenti pre-integrati. Alloy utilizza una sintassi di configurazione dichiarativa proprietaria (file `.alloy`) basata su componenti collegabili tramite riferimenti diretti.

#### Architettura a Componenti

```alloy
// /etc/alloy/config.alloy — Esempio completo di raccolta metriche + log

// Componente: scrape metriche Prometheus-compatibili
prometheus.scrape "node_metrics" {
  targets = [{
    __address__ = "localhost:9100",
    job         = "node-exporter",
  }]
  forward_to = [prometheus.remote_write.victoriametrics.receiver]
  scrape_interval = "15s"
}

// Componente: remote_write verso VictoriaMetrics o Prometheus
prometheus.remote_write "victoriametrics" {
  endpoint {
    url = "http://victoria-metrics:8428/api/v1/write"
    queue_config {
      max_samples_per_send = 5000
      batch_send_deadline  = "5s"
    }
  }
}

// Componente: raccolta log (sostituto di Promtail)
local.file_match "syslogs" {
  path_targets = [{
    __path__ = "/var/log/syslog",
    job      = "syslog",
    host     = constants.hostname,
  }]
}

loki.source.file "syslog_reader" {
  targets    = local.file_match.syslogs.targets
  forward_to = [loki.write.loki_endpoint.receiver]
}

loki.write "loki_endpoint" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
    tenant_id = "default"
  }
}

// Componente: ricezione trace OTel
otelcol.receiver.otlp "traces_in" {
  grpc {
    endpoint = "0.0.0.0:4317"
  }
  http {
    endpoint = "0.0.0.0:4318"
  }
  output {
    traces = [otelcol.exporter.otlp.tempo.input]
  }
}

otelcol.exporter.otlp "tempo" {
  client {
    endpoint = "tempo:4317"
    tls {
      insecure = true
    }
  }
}
```

#### Migrazione da Promtail / Grafana Agent

```bash
# Convertire configurazione Grafana Agent Flow a Alloy (stesso formato)
# I file .river di Agent Flow sono compatibili con Alloy

# Convertire configurazione Promtail YAML a formato Alloy
alloy convert --source-format=promtail \
  --output=/etc/alloy/from-promtail.alloy \
  /etc/promtail/config.yml

# Convertire configurazione OTel Collector YAML a formato Alloy
alloy convert --source-format=otelcol \
  --output=/etc/alloy/from-otel.alloy \
  /etc/otelcol/config.yaml

# Validare la configurazione
alloy fmt /etc/alloy/config.alloy
alloy run /etc/alloy/config.alloy --stability.level=generally-available
```

#### Vantaggi Rispetto a Promtail e Grafana Agent Standalone

| Caratteristica | Promtail | Grafana Agent | Grafana Alloy |
|---------------|----------|---------------|---------------|
| Metriche | No | Sì | Sì |
| Log | Sì | Sì | Sì |
| Trace | No | Sì | Sì |
| Profili continui | No | No | Sì (Pyroscope) |
| Configurazione | YAML | River / YAML | .alloy (componenti) |
| Componenti OTel | No | Parziale | 120+ componenti |
| Debug UI | No | Limitata | http://localhost:12345 |
| Conversione config | — | — | Da Promtail, Agent, OTel |
| Stato progetto | Mantenuto | EOL Nov 2025 | Attivo, raccomandato |

Alloy espone un'interfaccia web di debug su `localhost:12345` che visualizza il grafo dei componenti, lo stato di ciascun componente e il flusso dei dati in tempo reale, rendendo il troubleshooting significativamente più semplice rispetto ai tool precedenti.

### Correlazione Metriche-Log-Trace in Grafana

In Grafana, configurare le data source per la correlazione:

```
1. Prometheus → Grafana: Exemplars configurati → link a Tempo
2. Loki → Grafana: Derived fields → estrarre trace_id e link a Tempo
3. Tempo → Grafana: Trace to logs → link a Loki per lo span selezionato

Flusso investigativo:
Dashboard (metriche anomale)
  → Drill down su metrica specifica (Prometheus)
    → Exemplar: click su trace_id
      → Tempo: visualizzazione trace
        → Click su span: "View logs" → Loki
```

---

## Infrastructure Monitoring: SNMP, IPMI, iDRAC/iLO

### SNMP (Simple Network Management Protocol)

SNMP è il protocollo standard per il monitoring di dispositivi di rete (switch, router, firewall, AP):

```yaml
# /opt/snmp_exporter/snmp.yml (generato da snmp_exporter generator)
# Configurazione per switch Cisco
modules:
  if_mib:
    walk:
      - 1.3.6.1.2.1.2       # interfaces
      - 1.3.6.1.2.1.31.1.1  # ifXTable
    metrics:
      - name: ifHCInOctets
        oid: 1.3.6.1.2.1.31.1.1.1.6
        type: counter
        help: Bytes in ingresso sull'interfaccia
        indexes:
          - labelname: ifIndex
            type: Integer
        lookups:
          - labels: [ifIndex]
            labelname: ifDescr
            oid: 1.3.6.1.2.1.2.2.1.2
            type: DisplayString

      - name: ifHCOutOctets
        oid: 1.3.6.1.2.1.31.1.1.1.10
        type: counter
        help: Bytes in uscita sull'interfaccia

      - name: ifOperStatus
        oid: 1.3.6.1.2.1.2.2.1.8
        type: gauge
        help: Stato operativo (1=up, 2=down, 3=testing)

    auth:
      community: public      # SNMPv2c
      # Per SNMPv3:
      # security_level: authPriv
      # username: monitor
      # password: xxx
      # auth_protocol: SHA
      # priv_protocol: AES
      # priv_password: xxx
```

```yaml
# prometheus.yml — scrape SNMP
scrape_configs:
  - job_name: 'snmp-switches'
    metrics_path: /snmp
    params:
      module: [if_mib]
    static_configs:
      - targets:
          - 192.168.1.1    # Core switch
          - 192.168.1.2    # Distribution switch
          - 192.168.1.3    # Access switch
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: snmp-exporter:9116
```

### IPMI (Intelligent Platform Management Interface)

IPMI permette il monitoring hardware out-of-band (temperatura, ventole, alimentazione, stato dischi):

```yaml
# ipmi_exporter configurazione
# /opt/ipmi_exporter/ipmi_config.yml
modules:
  default:
    user: "ADMIN"
    pass: "password"
    privilege: "admin"
    driver: "LAN_2_0"
    collectors:
      - bmc
      - ipmi
      - dcmi
      - chassis
      - sel          # System Event Log
    exclude_sensor_ids:
      - 0
```

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ipmi'
    metrics_path: /ipmi
    params:
      module: [default]
    static_configs:
      - targets:
          - 10.0.0.101    # iDRAC/iLO/BMC address
          - 10.0.0.102
          - 10.0.0.103
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: ipmi-exporter:9290
```

### Alert Hardware

```yaml
groups:
  - name: hardware_alerts
    rules:
      - alert: HighCPUTemperature
        expr: ipmi_temperature_celsius{name=~".*CPU.*"} > 85
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Temperatura CPU alta su {{ $labels.instance }}: {{ $value }}°C"

      - alert: FanFailure
        expr: ipmi_fan_speed_rpm{} < 100
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Ventola guasta su {{ $labels.instance }}: {{ $labels.name }}"

      - alert: PowerSupplyFault
        expr: ipmi_power_supply_state != 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Alimentatore in fault su {{ $labels.instance }}"

      - alert: DiskPredictiveFailure
        expr: ipmi_sensor_value{name=~".*Disk.*Predictive.*"} != 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Disco in predictive failure su {{ $labels.instance }}"

      - alert: SELCriticalEvent
        expr: increase(ipmi_sel_entries_count[1h]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Aumento eventi SEL su {{ $labels.instance }}"
```

### iDRAC / iLO Monitoring via Redfish

Per hardware Dell (iDRAC) e HPE (iLO), l'API Redfish è l'alternativa moderna a IPMI:

```bash
# Query Redfish per stato sistema
curl -s -k -u admin:password \
  https://idrac.example.com/redfish/v1/Systems/System.Embedded.1 \
  | jq '{Status: .Status, PowerState: .PowerState, MemoryGiB: .MemorySummary.TotalSystemMemoryGiB}'

# Script per textfile collector con Redfish
#!/bin/bash
HOSTS="idrac1:10.0.0.101 idrac2:10.0.0.102"
TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"

for ENTRY in $HOSTS; do
  NAME="${ENTRY%%:*}"
  IP="${ENTRY##*:}"
  
  HEALTH=$(curl -s -k -u admin:password \
    "https://${IP}/redfish/v1/Systems/System.Embedded.1" \
    | jq -r '.Status.Health')
  
  HEALTH_NUM=0
  [ "$HEALTH" = "OK" ] && HEALTH_NUM=1

  echo "hardware_health{host=\"${NAME}\",ip=\"${IP}\"} ${HEALTH_NUM}" \
    >> "${TEXTFILE_DIR}/hardware.prom.tmp"
done

mv "${TEXTFILE_DIR}/hardware.prom.tmp" "${TEXTFILE_DIR}/hardware.prom"
```

---

## Container Monitoring

### cAdvisor

cAdvisor (Container Advisor) espone metriche per singolo container:

```yaml
# docker-compose.yml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.49.1
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "8080:8080"
    privileged: true
    devices:
      - /dev/kmsg
```

```promql
# CPU usage per container
rate(container_cpu_usage_seconds_total{name!=""}[5m])

# Memoria per container
container_memory_usage_bytes{name!=""}

# Memoria RSS (senza cache)
container_memory_rss{name!=""}

# Network I/O per container
rate(container_network_receive_bytes_total{name!=""}[5m])
rate(container_network_transmit_bytes_total{name!=""}[5m])

# Disco I/O per container
rate(container_fs_reads_bytes_total{name!=""}[5m])
rate(container_fs_writes_bytes_total{name!=""}[5m])

# Container restart count
increase(container_restart_count{name!=""}[1h])
```

### kube-state-metrics (Kubernetes)

kube-state-metrics espone metriche sullo stato degli oggetti Kubernetes (non metriche di performance):

```promql
# Pod non pronti
kube_pod_status_ready{condition="false"}

# Pod in stato CrashLoopBackOff
kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"}

# Deployment con repliche desiderate != available
kube_deployment_spec_replicas - kube_deployment_status_replicas_available > 0

# PVC non bound
kube_persistentvolumeclaim_status_phase{phase!="Bound"}

# Node not ready
kube_node_status_condition{condition="Ready", status="false"}

# Resource requests vs limits vs usage
# CPU requests ratio
sum(kube_pod_container_resource_requests{resource="cpu"}) by (node)
/ sum(kube_node_status_allocatable{resource="cpu"}) by (node)

# Memoria utilizzata vs allocata
sum(container_memory_usage_bytes{namespace!=""}) by (namespace)
/ sum(kube_resourcequota{type="hard", resource="limits.memory"}) by (namespace)

# Job failures
kube_job_status_failed{} > 0

# HPA al limite
kube_horizontalpodautoscaler_status_current_replicas
== kube_horizontalpodautoscaler_spec_max_replicas
```

### Prometheus Operator (Kubernetes)

```yaml
# ServiceMonitor — discovery automatico in Kubernetes
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-monitor
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: api-server
  endpoints:
    - port: metrics
      interval: 15s
      path: /metrics

---
# PrometheusRule — regole di alert
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: api-alerts
  labels:
    release: prometheus
spec:
  groups:
    - name: api
      rules:
        - alert: APIPodCrashLooping
          expr: |
            rate(kube_pod_container_status_restarts_total{namespace="production", pod=~"api-.*"}[15m]) > 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Pod {{ $labels.pod }} in crash loop"

---
# PodMonitor — per pod senza Service
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: batch-jobs
spec:
  selector:
    matchLabels:
      type: batch-worker
  podMetricsEndpoints:
    - port: metrics
      interval: 30s
```

### Alert per Container

```yaml
groups:
  - name: container_alerts
    rules:
      - alert: ContainerHighCPU
        expr: |
          sum by(name)(rate(container_cpu_usage_seconds_total{name!=""}[5m])) > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} usa >80% CPU"

      - alert: ContainerHighMemory
        expr: |
          container_memory_usage_bytes{name!=""} / container_spec_memory_limit_bytes{name!=""} > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} al 90% del limite memoria"

      - alert: ContainerOOMKilled
        expr: |
          increase(container_oom_events_total{name!=""}[5m]) > 0
        labels:
          severity: critical
        annotations:
          summary: "Container {{ $labels.name }} terminato per OOM"

      - alert: ContainerRestarting
        expr: |
          increase(container_restart_count{name!=""}[1h]) > 3
        labels:
          severity: warning
        annotations:
          summary: "Container {{ $labels.name }} riavviato {{ $value }} volte nell'ultima ora"
```

---

## Observability basata su eBPF

eBPF (extended Berkeley Packet Filter) permette di inserire programmi nel kernel Linux senza modificare il codice sorgente o caricare moduli kernel. Per l'observability, questo significa raccogliere metriche di rete, latenza applicativa e profiling con overhead minimo e **senza instrumentazione del codice applicativo**.

### Panoramica degli Strumenti eBPF

| Strumento | Maintainer | Focus | Overhead | Deployment |
|-----------|-----------|-------|----------|------------|
| **Beyla** | Grafana Labs | HTTP/gRPC auto-instrumentation | <1% CPU | Sidecar o DaemonSet |
| **Pixie** | CNCF (New Relic) | Full K8s observability | <5% CPU | DaemonSet (solo K8s) |
| **Coroot** | Coroot Inc. | Service maps + root cause | <2% CPU | DaemonSet o standalone |
| **Cilium Hubble** | Isovalent/Cisco | Network observability L3-L7 | <3% CPU | CNI plugin (solo K8s) |
| **bpftrace** | Kernel community | Ad-hoc tracing e debugging | Variabile | CLI one-shot |
| **Kepler** | CNCF | Energy consumption metrics | <1% CPU | DaemonSet |

### Grafana Beyla: Auto-Instrumentation HTTP/gRPC

Beyla (donato a OpenTelemetry come progetto OBI nel 2025) rileva automaticamente chiamate HTTP e gRPC intercettando le syscall del kernel, senza modifiche al codice applicativo. Produce metriche RED (Rate, Errors, Duration) e span distribuiti.

```yaml
# /etc/beyla/config.yaml — configurazione standalone
open_port: 8080          # monitora il processo in ascolto su porta 8080
# Oppure: executable_name: "my-api"  — match per nome processo

otel_metrics_export:
  endpoint: http://otel-collector:4318/v1/metrics
  protocol: http/protobuf
  interval: 15s

otel_traces_export:
  endpoint: http://otel-collector:4318/v1/traces
  protocol: http/protobuf
  sampler:
    name: parentbased_traceidratio
    arg: "0.1"    # campiona 10% delle trace

# Metriche prodotte automaticamente:
# http.server.request.duration   — istogramma latenza
# http.server.request.body.size  — dimensione request
# http.server.active_requests    — richieste concorrenti
# rpc.server.duration            — latenza gRPC
```

```bash
# Esecuzione come processo standalone
sudo beyla --config /etc/beyla/config.yaml

# Oppure come container sidecar (Docker)
docker run --rm \
  --privileged \
  --pid=host \
  --network=host \
  -e BEYLA_OPEN_PORT=8080 \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4318 \
  grafana/beyla:latest
```

### Pixie: Observability Kubernetes Nativa

Pixie opera esclusivamente in cluster Kubernetes e cattura automaticamente richieste HTTP, query SQL, messaggi gRPC e DNS senza instrumentazione. I dati rimangono nel cluster (nessun invio a SaaS esterno):

```bash
# Installazione via CLI
px deploy --cluster_name=prod-eu-west

# Query live con PxL (Pixie Query Language)
px live http_requests_per_service    # richieste HTTP per servizio
px live mysql_queries                # query MySQL intercettate via eBPF
px live network_flow_graph           # grafo flussi di rete L4-L7

# Script PxL custom: latenza p99 per endpoint
px script run -f - <<'EOF'
import px
df = px.DataFrame('http_events', start_time='-5m')
df = df.groupby(['service', 'req_path']).agg(
  p99_latency=('latency', px.p99),
  count=('latency', px.count),
  error_rate=('resp_status', lambda x: px.mean(x >= 400))
)
px.display(df.head(20))
EOF
```

### Coroot: Service Map e Root Cause Analysis

Coroot combina metriche eBPF con analisi automatica delle dipendenze, generando service map e identificando colli di bottiglia senza configurazione:

```bash
# Installazione su host Linux (non richiede Kubernetes)
curl -sfL https://raw.githubusercontent.com/coroot/coroot/main/deploy/docker-compose.yaml \
  -o docker-compose.yaml

docker compose up -d

# Coroot agent raccoglie automaticamente:
# - Connessioni TCP (latenza, retransmit, stato)
# - Richieste HTTP/gRPC (metodo, status, durata)
# - Query DNS (risoluzioni, errori, latenza)
# - I/O disco (IOPS, latenza, throughput)
# - Overhead CPU per processo
```

Coroot si distingue per la capacità di produrre insight azionabili: invece di presentare solo grafici, identifica automaticamente anomalie e suggerisce la causa radice (es. "latenza aumentata del 300% correlata con CPU throttling sul nodo X").

### Confronto Casi d'Uso

- **Solo metriche RED senza K8s**: Beyla (il più leggero, funziona su qualsiasi host Linux)
- **Full observability K8s**: Pixie (dati nel cluster, nessun SaaS)
- **Troubleshooting con root cause**: Coroot (service map + analisi automatica)
- **Network observability L3-L7**: Cilium Hubble (richiede Cilium come CNI)
- **Debugging ad-hoc kernel/userspace**: bpftrace (scripts one-liner)

### bpftrace: Debugging Ad-Hoc dal Kernel

bpftrace è lo strumento di riferimento per investigazioni one-shot su latenza, syscall e comportamento kernel:

```bash
# Istogramma latenza di lettura disco (distribuzione I/O)
sudo bpftrace -e '
tracepoint:block:block_rq_complete {
  @latency_us = hist(args->sector ? (nsecs - @start[args->dev, args->sector]) / 1000 : 0);
}
tracepoint:block:block_rq_issue {
  @start[args->dev, args->sector] = nsecs;
}'

# Top 10 processi per syscall al secondo
sudo bpftrace -e '
tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }
interval:s:5 { print(@, 10); clear(@); }'

# Tracciare connessioni TCP con latenza handshake
sudo bpftrace -e '
kretprobe:tcp_v4_connect {
  printf("%-16s %-6d -> connect() = %d\n", comm, pid, retval);
}'

# Monitorare file aperti per processo (utile per leak di file descriptor)
sudo bpftrace -e '
tracepoint:syscalls:sys_enter_openat {
  printf("%-16s %-6d %s\n", comm, pid, str(args->filename));
}'
```

### Kepler: Metriche Energetiche via eBPF

Kepler (Kubernetes-based Efficient Power Level Exporter) utilizza eBPF e modelli di potenza hardware per esporre metriche di consumo energetico per processo e container, in formato Prometheus:

```promql
# Consumo energetico per namespace Kubernetes
sum by (container_namespace) (
  rate(kepler_container_joules_total[5m])
) * 3600  # conversione in Watt-ora

# Top 5 container per consumo CPU energy
topk(5, sum by (container_name) (
  rate(kepler_container_core_joules_total[5m])
))
```

Kepler è particolarmente rilevante per reporting ESG e ottimizzazione dei costi cloud, dove il consumo energetico dei workload può guidare decisioni di scheduling e right-sizing.

---

## Capacity Planning e Forecasting

### Trend Analysis con Prometheus

```promql
# Previsione lineare: quando il disco sarà pieno?
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[7d], 30*24*3600)
# Restituisce il valore previsto tra 30 giorni basandosi sul trend degli ultimi 7

# Previsione esaurimento: ore rimaste
(node_filesystem_avail_bytes{mountpoint="/"})
/
(
  (node_filesystem_avail_bytes{mountpoint="/"} offset 7d - node_filesystem_avail_bytes{mountpoint="/"})
  / (7 * 24 * 3600)
)
/ 3600  # Converti in ore

# Crescita giornaliera media
(node_filesystem_size_bytes{mountpoint="/"} - node_filesystem_avail_bytes{mountpoint="/"})
-
(node_filesystem_size_bytes{mountpoint="/"} offset 7d - node_filesystem_avail_bytes{mountpoint="/"} offset 7d)
/ 7

# Trend CPU: crescita media settimana su settimana
avg_over_time(instance:node_cpu_utilization:ratio[7d])
-
avg_over_time(instance:node_cpu_utilization:ratio[7d] offset 7d)

# Proiezione connessioni DB — esaurimento pool
predict_linear(
  sum(pg_stat_activity_count{state="active"})[7d:1h],
  30*24*3600
)
```

### Dashboard di Capacity Planning

```promql
# Metriche chiave per capacity planning dashboard:

# 1. Resource utilization (attuale)
instance:node_cpu_utilization:ratio
instance:node_memory_utilization:ratio
instance:node_filesystem_utilization:ratio

# 2. Growth rate (giorno su giorno)
deriv(instance:node_filesystem_utilization:ratio[24h]) * 86400

# 3. Headroom (quanto margine abbiamo)
1 - instance:node_cpu_utilization:ratio    # CPU headroom
node_memory_MemAvailable_bytes             # Memory headroom
node_filesystem_avail_bytes                # Disk headroom

# 4. Prediction (quando raggiungeremo la soglia)
# Giorni al 90% di disco
(0.9 - instance:node_filesystem_utilization:ratio)
/ clamp_min(deriv(instance:node_filesystem_utilization:ratio[7d]) * 86400, 0.0001)

# 5. Peak vs average (per sizing)
max_over_time(instance:node_cpu_utilization:ratio[7d])
/ avg_over_time(instance:node_cpu_utilization:ratio[7d])
```

### Alerting per Capacity

```yaml
groups:
  - name: capacity_alerts
    rules:
      - alert: DiskWillFill30Days
        expr: |
          predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[7d], 30*24*3600) < 0
        for: 6h
        labels:
          severity: warning
          team: capacity
        annotations:
          summary: "Disco {{ $labels.mountpoint }} su {{ $labels.instance }} pieno entro 30 giorni"

      - alert: MemoryGrowthAnomaly
        expr: |
          deriv(node_memory_MemAvailable_bytes[6h]) < -1e8
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Memoria in calo rapido su {{ $labels.instance }}: possibile memory leak"

      - alert: CPUSteadilyIncreasing
        expr: |
          avg_over_time(instance:node_cpu_utilization:ratio[7d])
          - avg_over_time(instance:node_cpu_utilization:ratio[7d] offset 7d) > 0.15
        for: 1d
        labels:
          severity: info
          team: capacity
        annotations:
          summary: "CPU utilization in crescita del 15%+ su {{ $labels.instance }} (settimana su settimana)"
```

---

## On-Call e Incident Management

### Struttura On-Call

```
Incident → Alert fired
         → On-call engineer riceve notifica (PagerDuty / OpsGenie)
         → Acknowledge (entro 5 min)
         → Triage (severity assessment)
         → Investigate (usa dashboard, log, trace)
         → Mitigate (fix temporaneo)
         → Resolve (fix permanente)
         → Postmortem (blameless)
```

### Integrazione PagerDuty

```yaml
# alertmanager.yml — integrazione PagerDuty completa
receivers:
  - name: 'pagerduty-infra'
    pagerduty_configs:
      - routing_key: 'R0XXXXXXXXXXXXXXXXXXXXXXXXX'
        severity: '{{ if eq .CommonLabels.severity "critical" }}critical{{ else if eq .CommonLabels.severity "warning" }}warning{{ else }}info{{ end }}'
        description: '{{ .CommonAnnotations.summary }}'
        client: 'Prometheus Alertmanager'
        client_url: 'http://alertmanager.example.com'
        details:
          firing: '{{ .Alerts.Firing | len }} alert(s) attivi'
          instances: '{{ range .Alerts }}{{ .Labels.instance }} {{ end }}'
          runbook: '{{ .CommonAnnotations.runbook_url }}'
        links:
          - href: '{{ .CommonAnnotations.dashboard_url }}'
            text: 'Dashboard Grafana'
          - href: '{{ .CommonAnnotations.runbook_url }}'
            text: 'Runbook'
```

### Escalation Policy

```
Livello 1 (0 min):    On-call engineer (SMS + push notification)
Livello 2 (15 min):   Secondo on-call + team lead (SMS + telefono)
Livello 3 (30 min):   Engineering manager + incident commander (telefono)
Livello 4 (60 min):   VP Engineering + CTO (telefono)
```

### Runbook Template

Ogni alert critico deve avere un runbook associato. Struttura minima:

```markdown
## Alert: DiskSpaceLow

### Descrizione
Il disco su un server ha superato l'85% di utilizzo.

### Impatto
Se il disco si riempie al 100%:
- Database: crash per impossibilità di scrivere WAL
- Applicazione: impossibilità di scrivere log, file temporanei
- Sistema: impossibilità di creare processi (no /tmp space)

### Diagnosi
1. Verificare quale filesystem è pieno:
   df -h
2. Trovare file/directory più grandi:
   du -sh /* | sort -rh | head -20
   du -sh /var/* | sort -rh | head -20
3. Controllare log cresciuti fuori controllo:
   find /var/log -type f -size +100M -exec ls -lh {} \;

### Mitigazione immediata
1. Pulire log vecchi:
   journalctl --vacuum-time=3d
   find /var/log -name "*.gz" -mtime +7 -delete
2. Pulire cache package manager:
   apt clean
3. Rimuovere kernel vecchi:
   apt autoremove --purge
4. Se Docker: docker system prune -a --volumes

### Fix permanente
1. Valutare aumento disco (se cloud: resize volume)
2. Configurare log rotation adeguata
3. Implementare policy di retention
4. Considerare mount separato per /var/log

### Dashboard
http://grafana.example.com/d/disk-overview

### Escalation
Se il disco è al 95%+ e non si riesce a liberare spazio → escalare a Livello 2.
```

### Postmortem (Blameless)

```
## Postmortem: [Titolo incidente]
Data: 2026-05-22
Durata: 45 minuti (14:30 - 15:15 UTC)
Severity: SEV-1
Incident Commander: [nome]

### Summary
[1-2 frasi su cosa è successo]

### Timeline (UTC)
14:30 — Alert DiskSpaceLow fired su db-primary-01
14:32 — On-call acknowledge
14:35 — Investigazione: /var/lib/postgresql al 96%
14:40 — Causa identificata: query di export non terminata genera file temp
14:45 — Mitigazione: kill query, rimozione file temp
15:00 — Disco sotto 60%
15:15 — Monitoring confermato stabile, incidente chiuso

### Root Cause
Query di data export schedulata senza LIMIT ha generato un file temporaneo
da 180 GB saturando il disco.

### Impact
- 45 minuti di degradazione performance DB
- 5 minuti di errori 500 su API (write failure)
- ~200 utenti impattati

### Lessons Learned
- Cosa ha funzionato: alert ha notificato rapidamente, runbook era aggiornato
- Cosa non ha funzionato: query non aveva timeout, disco senza alert a 70%
- Dove abbiamo avuto fortuna: il DB non è crashato

### Action Items
- [ ] Aggiungere timeout a tutte le query export (owner: [nome], deadline: 2026-05-29)
- [ ] Alert a 70% disco per DB server (owner: [nome], deadline: 2026-05-24)
- [ ] Spostare file temp su volume dedicato (owner: [nome], deadline: 2026-06-05)
```

---

## Dashboard Best Practices

### Layout e Gerarchia

```
Dashboard Overview (per management):
┌─────────────────────────────────────────────────┐
│  SLO Status: ✅ API 99.95%  ✅ Web 99.98%      │
│  Error Budget: API 72% remaining                 │
├──────────────────────┬──────────────────────────┤
│  Active Alerts: 2    │  Incident Status: Clear   │
├──────────────────────┴──────────────────────────┤
│  [Request Rate]  [Error Rate]  [Latency p99]    │
│  [Availability]  [Saturation]  [Active Users]   │
└─────────────────────────────────────────────────┘

Dashboard Dettaglio (per operations):
┌─────────────────────────────────────────────────┐
│ Variabili: [Instance ▼] [Job ▼] [Interval ▼]   │
├─────────────────────────────────────────────────┤
│ Row: Sistema                                     │
│  [CPU %]  [Memory %]  [Disk %]  [Network]       │
├─────────────────────────────────────────────────┤
│ Row: Applicazione                                │
│  [Request Rate] [Error Rate] [Latency] [Queue]  │
├─────────────────────────────────────────────────┤
│ Row: Database                                    │
│  [Connections] [Queries/s] [Slow Queries] [Size]│
├─────────────────────────────────────────────────┤
│ Row: Logs (integrazione Loki)                    │
│  [Error log stream]                              │
└─────────────────────────────────────────────────┘
```

### Regole per Dashboard Efficaci

1. **Gerarchia visiva**: i pannelli più importanti in alto e più grandi. Metriche secondarie sotto, più piccole.
2. **Colori con significato**: rosso = critico, giallo = warning, verde = ok. Non usare colori random.
3. **Soglie visibili**: ogni pannello con gauge/stat deve avere soglie (thresholds) che corrispondono agli alert.
4. **Variabili template**: ogni dashboard deve usare variabili per instance, job, namespace. Mai hardcodare valori.
5. **Time range sensato**: default 6h o 24h per overview. 1h per troubleshooting.
6. **Link tra dashboard**: drill-down da overview → dettaglio → servizio specifico.
7. **Annotazioni**: deploy, incident, maintenance window visibili come annotazioni sul grafico.

### Dashboard SLO-Driven

```promql
# Pannello: SLO Compliance (Stat panel, verde/rosso)
# Mostra percentuale di compliance nell'ultimo mese
sum(rate(http_request_duration_seconds_bucket{le="0.3", job="api"}[30d]))
/ sum(rate(http_request_duration_seconds_count{job="api"}[30d]))

# Pannello: Error Budget Remaining (Gauge panel)
# 100% = budget intatto, 0% = budget esaurito
(
  1 - (
    1 - sum(rate(http_request_duration_seconds_bucket{le="0.3"}[30d]))
        / sum(rate(http_request_duration_seconds_count[30d]))
  ) / (1 - 0.999)
) * 100

# Pannello: Error Budget Burn Rate (Time series)
# Mostra velocità di consumo del budget nel tempo
(
  1 - sum(rate(http_request_duration_seconds_bucket{le="0.3"}[1h]))
      / sum(rate(http_request_duration_seconds_count[1h]))
) / (1 - 0.999)

# Pannello: Time Until Budget Exhaustion (Stat)
# Ore rimanenti al tasso attuale
# (budget_rimanente / burn_rate_attuale)
```

### Annotazioni per Deploy e Incidenti

```bash
# Aggiungere annotazione Grafana via API al momento del deploy
curl -X POST http://grafana:3000/api/annotations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <api-key>" \
  -d '{
    "dashboardUID": "node-overview",
    "time": '"$(date +%s%N | cut -b1-13)"',
    "tags": ["deploy", "production"],
    "text": "Deploy v2.3.1 - API service"
  }'

# In CI/CD pipeline (esempio GitLab CI)
# deploy:
#   script:
#     - kubectl apply -f k8s/
#     - |
#       curl -s -X POST "$GRAFANA_URL/api/annotations" \
#         -H "Content-Type: application/json" \
#         -H "Authorization: Bearer $GRAFANA_API_KEY" \
#         -d "{\"time\":$(date +%s)000, \"tags\":[\"deploy\"], \"text\":\"$CI_COMMIT_SHORT_SHA\"}"
```

---

## Monitoraggio Custom con Script

```bash
#!/bin/bash
# /usr/local/bin/check-services.sh
# Monitoraggio custom con notifica

SERVICES="nginx postgresql redis"
ALERT_EMAIL="admin@example.com"

for SERVICE in $SERVICES; do
    if ! systemctl is-active --quiet "$SERVICE"; then
        echo "ALERT: $SERVICE is down on $(hostname)" | \
          mail -s "Service Alert: $SERVICE DOWN" "$ALERT_EMAIL"
        logger -p daemon.crit "MONITOR: $SERVICE is down"
    fi
done

# Per Prometheus: text file collector
# Scrivere metriche in formato Prometheus in un file
# che node_exporter legge con --collector.textfile.directory

TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
mkdir -p "$TEXTFILE_DIR"

# Esempio: conteggio connessioni attive
CONNS=$(ss -tuln | wc -l)
echo "custom_active_connections $CONNS" > "$TEXTFILE_DIR/connections.prom"

# Esempio: dimensione database
DB_SIZE=$(sudo -u postgres psql -t -c "SELECT pg_database_size('mydb')")
echo "custom_database_size_bytes{db=\"mydb\"} $DB_SIZE" > "$TEXTFILE_DIR/dbsize.prom"
```

### Script Avanzati per Monitoring Custom

```bash
#!/bin/bash
# /usr/local/bin/advanced-monitoring.sh
# Metriche custom avanzate per Prometheus textfile collector

TEXTFILE_DIR="/var/lib/node_exporter/textfile_collector"
TMPFILE=$(mktemp)

# 1. Stato dei backup
BACKUP_DIR="/var/backups"
for BACKUP in "$BACKUP_DIR"/*.tar.gz; do
  [ -f "$BACKUP" ] || continue
  NAME=$(basename "$BACKUP" .tar.gz)
  AGE_HOURS=$(( ($(date +%s) - $(stat -c %Y "$BACKUP")) / 3600 ))
  SIZE=$(stat -c %s "$BACKUP")
  cat >> "$TMPFILE" <<PROM
custom_backup_age_hours{name="${NAME}"} ${AGE_HOURS}
custom_backup_size_bytes{name="${NAME}"} ${SIZE}
PROM
done

# 2. Coda di lavoro applicativa
if command -v redis-cli &>/dev/null; then
  QUEUE_LEN=$(redis-cli llen job_queue 2>/dev/null || echo 0)
  cat >> "$TMPFILE" <<PROM
# HELP custom_job_queue_length Lunghezza coda lavori Redis
# TYPE custom_job_queue_length gauge
custom_job_queue_length ${QUEUE_LEN}
PROM
fi

# 3. Latenza DNS
DNS_START=$(date +%s%N)
dig +short example.com @8.8.8.8 > /dev/null 2>&1
DNS_END=$(date +%s%N)
DNS_MS=$(( (DNS_END - DNS_START) / 1000000 ))
cat >> "$TMPFILE" <<PROM
# HELP custom_dns_resolution_ms Tempo risoluzione DNS in millisecondi
# TYPE custom_dns_resolution_ms gauge
custom_dns_resolution_ms{server="8.8.8.8"} ${DNS_MS}
PROM

# 4. Conteggio processi zombie
ZOMBIES=$(ps aux | awk '$8 ~ /^Z/' | wc -l)
cat >> "$TMPFILE" <<PROM
# HELP custom_zombie_processes Numero di processi zombie
# TYPE custom_zombie_processes gauge
custom_zombie_processes ${ZOMBIES}
PROM

# Atomico: scrivi su temp e rinomina
mv "$TMPFILE" "$TEXTFILE_DIR/advanced.prom"
```

---

## Guida Implementazione: Stack Completo da Zero

### Prerequisiti

```bash
# Sistema: Debian 12 / Ubuntu 24.04
# Risorse minime:
#   Monitoring server: 4 CPU, 8 GB RAM, 100 GB SSD
#   Per 50 target con retention 90d: 8 CPU, 16 GB RAM, 500 GB SSD

# Preparazione
sudo apt update && sudo apt upgrade -y
sudo apt install -y wget curl jq gnupg2 apt-transport-https
```

### Passo 1: Prometheus

```bash
# Utente dedicato
sudo useradd -rs /bin/false prometheus

# Download e installazione
PROM_VERSION="2.48.0"
wget "https://github.com/prometheus/prometheus/releases/download/v${PROM_VERSION}/prometheus-${PROM_VERSION}.linux-amd64.tar.gz"
tar xzf "prometheus-${PROM_VERSION}.linux-amd64.tar.gz"
sudo mv "prometheus-${PROM_VERSION}.linux-amd64" /opt/prometheus
sudo chown -R prometheus:prometheus /opt/prometheus
sudo mkdir -p /opt/prometheus/rules /opt/prometheus/targets

# Configurazione iniziale
sudo tee /opt/prometheus/prometheus.yml > /dev/null <<'YAML'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node'
    file_sd_configs:
      - files: ['targets/nodes.json']
        refresh_interval: 30s

  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    file_sd_configs:
      - files: ['targets/http_targets.json']
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9115
YAML

# Systemd service
sudo tee /etc/systemd/system/prometheus.service > /dev/null <<'INI'
[Unit]
Description=Prometheus Monitoring
After=network.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/opt/prometheus/prometheus \
  --config.file=/opt/prometheus/prometheus.yml \
  --storage.tsdb.path=/opt/prometheus/data \
  --storage.tsdb.retention.time=90d \
  --storage.tsdb.wal-compression \
  --web.listen-address=:9090 \
  --web.enable-lifecycle \
  --web.enable-admin-api
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
INI

sudo systemctl daemon-reload
sudo systemctl enable --now prometheus
```

### Passo 2: Node Exporter (su ogni host)

```bash
sudo useradd -rs /bin/false node_exporter
NE_VERSION="1.7.0"
wget "https://github.com/prometheus/node_exporter/releases/download/v${NE_VERSION}/node_exporter-${NE_VERSION}.linux-amd64.tar.gz"
tar xzf "node_exporter-${NE_VERSION}.linux-amd64.tar.gz"
sudo cp "node_exporter-${NE_VERSION}.linux-amd64/node_exporter" /usr/local/bin/
sudo mkdir -p /var/lib/node_exporter/textfile_collector
sudo chown node_exporter:node_exporter /var/lib/node_exporter/textfile_collector

sudo tee /etc/systemd/system/node_exporter.service > /dev/null <<'INI'
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter \
  --collector.systemd \
  --collector.processes \
  --collector.textfile.directory=/var/lib/node_exporter/textfile_collector \
  --web.listen-address=:9100
Restart=always

[Install]
WantedBy=multi-user.target
INI

sudo systemctl daemon-reload
sudo systemctl enable --now node_exporter
```

### Passo 3: Alertmanager

```bash
sudo useradd -rs /bin/false alertmanager
AM_VERSION="0.27.0"
wget "https://github.com/prometheus/alertmanager/releases/download/v${AM_VERSION}/alertmanager-${AM_VERSION}.linux-amd64.tar.gz"
tar xzf "alertmanager-${AM_VERSION}.linux-amd64.tar.gz"
sudo mv "alertmanager-${AM_VERSION}.linux-amd64" /opt/alertmanager
sudo chown -R alertmanager:alertmanager /opt/alertmanager

# Configurazione minima (espandere in base ai canali)
sudo tee /opt/alertmanager/alertmanager.yml > /dev/null <<'YAML'
global:
  resolve_timeout: 5m

route:
  receiver: 'default'
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  group_by: ['alertname', 'instance']

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:9095/alert'
        send_resolved: true
YAML

sudo tee /etc/systemd/system/alertmanager.service > /dev/null <<'INI'
[Unit]
Description=Alertmanager
After=network.target

[Service]
User=alertmanager
Group=alertmanager
Type=simple
ExecStart=/opt/alertmanager/alertmanager \
  --config.file=/opt/alertmanager/alertmanager.yml \
  --storage.path=/opt/alertmanager/data \
  --web.listen-address=:9093
Restart=always

[Install]
WantedBy=multi-user.target
INI

sudo systemctl daemon-reload
sudo systemctl enable --now alertmanager
```

### Passo 4: Blackbox Exporter

```bash
BB_VERSION="0.25.0"
wget "https://github.com/prometheus/blackbox_exporter/releases/download/v${BB_VERSION}/blackbox_exporter-${BB_VERSION}.linux-amd64.tar.gz"
tar xzf "blackbox_exporter-${BB_VERSION}.linux-amd64.tar.gz"
sudo mv "blackbox_exporter-${BB_VERSION}.linux-amd64" /opt/blackbox_exporter

# Configurazione (usare esempio dalla sezione Blackbox Exporter)
# Systemd service simile ai precedenti, porta 9115
sudo systemctl enable --now blackbox_exporter
```

### Passo 5: Grafana

```bash
wget -q -O - https://packages.grafana.com/gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/grafana.gpg
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://packages.grafana.com/oss/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update && sudo apt install -y grafana

# Provisioning datasource
sudo mkdir -p /etc/grafana/provisioning/datasources
sudo tee /etc/grafana/provisioning/datasources/prometheus.yml > /dev/null <<'YAML'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
YAML

sudo systemctl enable --now grafana-server
# Accesso: http://server:3000 — cambiare immediatamente la password admin
```

### Passo 6: Loki + Promtail

```bash
# Loki
LOKI_VERSION="3.0.0"
wget "https://github.com/grafana/loki/releases/download/v${LOKI_VERSION}/loki-linux-amd64.zip"
unzip loki-linux-amd64.zip
sudo mv loki-linux-amd64 /usr/local/bin/loki
# Configurazione: vedere sezione Log Monitoring

# Promtail (su ogni host)
wget "https://github.com/grafana/loki/releases/download/v${LOKI_VERSION}/promtail-linux-amd64.zip"
unzip promtail-linux-amd64.zip
sudo mv promtail-linux-amd64 /usr/local/bin/promtail
# Configurazione: vedere sezione Log Monitoring
```

### Passo 7: Verifica

```bash
# Verificare che tutti i servizi siano attivi
for SVC in prometheus node_exporter alertmanager grafana-server; do
  echo -n "$SVC: "
  systemctl is-active $SVC
done

# Verificare endpoint
curl -s http://localhost:9090/-/healthy && echo "Prometheus OK"
curl -s http://localhost:9093/-/healthy && echo "Alertmanager OK"
curl -s http://localhost:9100/metrics | head -5 && echo "Node Exporter OK"
curl -s http://localhost:3000/api/health | jq . && echo "Grafana OK"

# Verificare target in Prometheus
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Importare dashboard Node Exporter Full
curl -s -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d '{"dashboard": {"id": null}, "overwrite": true, "inputs": [{"name": "DS_PROMETHEUS", "type": "datasource", "pluginId": "prometheus", "value": "Prometheus"}], "folderId": 0, "pluginId": "grafana-piechart-panel", "gnetId": 1860}'
```

### Checklist Post-Installazione

```
[ ] Prometheus scrape tutti i target (http://prometheus:9090/targets)
[ ] Grafana connessa a Prometheus (Save & Test OK)
[ ] Dashboard Node Exporter Full importata e funzionante
[ ] Recording rules caricate (http://prometheus:9090/rules)
[ ] Alert rules caricate e nessun errore
[ ] Alertmanager connesso (http://prometheus:9090/config — alerting section)
[ ] Notifiche testate (amtool alert add test severity=critical)
[ ] Blackbox Exporter funzionante per endpoint critici
[ ] Firewall: porte 9090, 9093, 9100, 3000, 9115 aperte solo da rete interna
[ ] TLS configurato per Grafana (reverse proxy o diretto)
[ ] Password admin Grafana cambiata
[ ] Backup configurazione Prometheus/Grafana automatizzato
[ ] Monitoring del monitoring (uptime check esterno su Grafana/Prometheus)
```

---

## Best Practices

1. **Monitorare tutto ciò che è critico**: ogni servizio in produzione deve avere: check di disponibilità (up/down), metriche di performance (latenza, throughput), metriche di capacità (disco, memoria, connessioni)
2. **Alert azionabili**: ogni alert deve richiedere un'azione. Se l'alert viene ignorato regolarmente: o la soglia è sbagliata, o l'alert non serve. Eliminare il rumore
3. **Severity chiare**: Critical = azione immediata (servizio down, disco pieno). Warning = azione entro ore (disco al 80%, CPU alta). Info = da monitorare
4. **Retention**: mantenere le metriche per almeno 30 giorni (ideale: 90-365 giorni). I trend storici sono essenziali per capacity planning
5. **Dashboard per ruolo**: una dashboard per l'overview (management), una per i dettagli (operations), una per ogni servizio critico
6. **Monitorare il monitoring**: se Prometheus o Grafana cadono, nessun alert arriverà. Monitoraggio esterno (es. uptime check da un servizio terzo)
7. **Naming convention consistente**: usare nomi metriche coerenti con le convenzioni Prometheus (`_total` per counter, `_bytes` per dimensioni, `_seconds` per durate)
8. **Label cardinality**: mai usare label ad alta cardinalità (user_id, request_id, IP). Ogni combinazione unica di label crea una nuova time series. 10 label con 100 valori = 100^10 serie potenziali
9. **Scrape interval ragionevole**: 15s è il default. Non scendere sotto 5s senza motivo. Alert non devono dipendere da campionamento < 10s
10. **Recording rules per query costose**: se una query appare in più dashboard o alert, creare una recording rule
11. **Test delle regole di alert**: usare `promtool test rules` per verificare che gli alert si attivino correttamente con dati simulati
12. **Documentare ogni alert**: ogni alert deve avere un runbook linkato nelle annotations
13. **Separare metriche di business da metriche infrastrutturali**: dashboard diverse, audience diversa, SLO diversi
14. **Backup della configurazione**: Prometheus config, Grafana dashboard (JSON), Alertmanager config in version control (Git)
15. **Aggiornamenti regolari**: exporter e Prometheus hanno release frequenti con fix di sicurezza e nuove metriche

---

## Troubleshooting

**"Prometheus non scrape i target"** → `http://prometheus:9090/targets` per lo stato. Target "down": il target è raggiungibile? La porta dell'exporter è aperta? Il firewall blocca? `curl http://target:9100/metrics` per test manuale.

**"Grafana: no data"** → Data source configurata correttamente? Test con "Save & Test". La query PromQL è corretta? Verificare il time range nel dashboard. Il target ha dati nel periodo selezionato?

**"Alert non arrivano"** → Alertmanager attivo? Route e receiver configurati correttamente? `http://alertmanager:9093/#/alerts` per lo stato. Verificare le credenziali SMTP/Slack. Testare con `amtool alert add test severity=critical`.

**"Metriche mancanti"** → L'exporter è in esecuzione? `curl http://target:PORT/metrics` per verificare. Il collector specifico è abilitato? (Node exporter: `--collector.systemd`). La metrica è stata rinominata in una nuova versione dell'exporter?

**"Prometheus usa troppa memoria"** → Controllare la cardinality: `prometheus_tsdb_head_series` per numero di serie attive. Troppe label ad alta cardinalità? Usare `metric_relabel_configs` per eliminare metriche non necessarie. Controllare `topk(10, count by (__name__)({__name__=~".+"}))` per trovare metriche con troppe serie.

**"Prometheus storage cresce troppo velocemente"** → Calcolare ingestion rate: `rate(prometheus_tsdb_head_samples_appended_total[5m])`. Ridurre serie con relabel/drop. Aumentare scrape interval per target meno critici. Verificare che la retention sia configurata (`--storage.tsdb.retention.time`).

**"PromQL restituisce risultati inattesi"** → Verificare il tipo di metrica (counter vs gauge). `rate()` solo su counter, `deriv()` su gauge. Attenzione a `rate()` con range troppo corto (minimo 4x scrape_interval). Verificare il label matching con `on()` / `ignoring()`.

**"Grafana dashboard lente"** → Query troppo pesanti? Usare recording rules. Range troppo lungo (30d) con scrape interval 15s = troppi datapoint. Usare `$__rate_interval` anziché intervalli fissi. Ridurre il numero di serie con aggregazione (`sum by`).

**"Alertmanager: duplicate notifications"** → Controllare `group_by`: raggruppamento troppo specifico genera gruppi separati. Verificare `repeat_interval`: troppo basso causa ripetizioni. Se HA cluster, verificare che il gossip funzioni (`amtool cluster show`).

**"Node Exporter non espone metriche systemd"** → Il flag `--collector.systemd` è presente? L'utente node_exporter ha permesso di leggere lo stato systemd? Su sistemi con molti servizi, aggiungere `--collector.systemd.unit-include="nginx|postgresql|redis"` per limitare.

**"Blackbox Exporter: probe failed"** → Verificare il modulo configurato. `curl http://blackbox:9115/probe?target=https://example.com&module=http_2xx` per test diretto. Problemi DNS? TLS certificate issues? Timeout troppo basso?

**"Loki: query lente o timeout"** → Ridurre il range della query. Usare label filter prima di line filter: `{job="nginx"} |= "error"` anziché `{} |= "error"`. Limitare con `| limit 1000`. Verificare che i chunk siano compattati.

**"Loki: promtail non invia log"** → Verificare che promtail possa leggere i file (`sudo -u promtail cat /var/log/syslog`). Controllare il file positions (`/var/lib/promtail/positions.yml`). Verificare connettività verso Loki (`curl http://loki:3100/ready`).

**"cAdvisor metriche mancanti per container"** → Verificare i volumi montati (soprattutto `/sys`, `/var/lib/docker`). Il flag `--privileged` è necessario. Alcuni container non espongono metriche se il cgroup driver è diverso (cgroupfs vs systemd).

**"Zabbix agent non si connette al server"** → Verificare `Server=` e `ServerActive=` in `/etc/zabbix/zabbix_agent2.conf`. Firewall aperto sulla porta 10050 (passivo) e 10051 (attivo). Hostname nel config deve corrispondere a quello configurato nel frontend.

**"SNMP Exporter: no data"** → Community string corretta? Il dispositivo risponde a `snmpwalk -v2c -c public <device> 1.3.6.1.2.1.1`? Le OID nel modulo sono supportate dal dispositivo?

**"Prometheus federation: stale data"** → Verificare `honor_labels: true`. Lo scrape interval della federation è adeguato? I match[] nel federate endpoint sono corretti? `curl 'http://remote-prometheus:9090/federate?match[]={__name__=~"job:.*"}'` per test.

**"Grafana provisioning non carica dashboard"** → Verificare i permessi del file e della directory. Il path nel provider YAML è corretto? I file JSON sono validi? Controllare i log di Grafana: `journalctl -u grafana-server -f`. Il datasource UID nel JSON deve corrispondere a quello provisionato.

**"Recording rules non funzionano"** → Verificare con `promtool check rules /path/to/rules.yml`. Le regole appaiono in `http://prometheus:9090/rules`? L'evaluation_interval è configurato? Controllare i log di Prometheus per errori di valutazione.

**"Metriche di scrape lente (scrape_duration_seconds alto)"** → L'exporter è sovraccarico? Troppi collector abilitati? Target con troppi servizi/filesystem/interfacce produce pagine `/metrics` molto grandi. Disabilitare collector non necessari. Aumentare `scrape_timeout`.

**"Prometheus crash: out of memory"** → TSDB head troppo grande. Controllare `prometheus_tsdb_head_series`. Limitare la cardinality. Impostare `--storage.tsdb.retention.size` per limitare lo spazio. Aumentare la RAM del server. Considerare `remote_write` + retention locale breve.

---

## FAQ — Domande Frequenti

**D: Prometheus o Zabbix? Quale scegliere?**
R: Prometheus per ambienti cloud-native, container, Kubernetes, microservizi. Zabbix per infrastrutture tradizionali, datacenter fisici, ambienti enterprise con necessità di auto-discovery avanzato e configurazione via GUI. Possono coesistere: Zabbix per l'hardware e la rete legacy, Prometheus per applicazioni e container.

**D: Quanto spazio disco serve per Prometheus?**
R: Formula approssimativa: `bytes_per_sample (1.5-2) * scrape_interval_seconds * num_series * retention_seconds`. Esempio: 10.000 serie, scrape 15s, retention 90 giorni ≈ 10.000 * (86400/15) * 90 * 2 = ~10 GB. Con 100.000 serie: ~100 GB. Usare `prometheus_tsdb_head_series` e `prometheus_tsdb_compactions_total` per monitorare la crescita effettiva.

**D: Come evitare l'alert fatigue?**
R: 1) Ogni alert deve avere un runbook con azione chiara. 2) Usare severity appropriate: non tutto è critical. 3) Implementare multi-burn-rate per SLO anziché soglie statiche. 4) Usare inhibition per sopprimere alert ridondanti. 5) Rivedere periodicamente gli alert: se un alert non ha generato azione in 3 mesi, rimuoverlo o ricalibarlo.

**D: Devo monitorare anche gli ambienti di staging/dev?**
R: Si, ma con soglie diverse e senza invio notifiche al team on-call. Usare label `env=staging` e routing separato in Alertmanager. Il monitoring in staging aiuta a: validare nuove metriche prima della produzione, testare alert rule, verificare che le applicazioni espongano metriche correttamente.

**D: Come gestire metriche ad alta cardinalità?**
R: La cardinalità è il nemico numero uno di Prometheus. Regole: mai usare user_id, session_id, request_id, UUID come label. Usare histogram anziché label per valori con molte combinazioni. Monitorare `prometheus_tsdb_head_series` e `scrape_series_added`. Usare `metric_relabel_configs` con `action: drop` per eliminare serie non necessarie.

**D: Prometheus pull vs push: quando usare il Pushgateway?**
R: Il Pushgateway è per job batch short-lived che terminano prima dello scrape successivo (cron job, CI/CD, batch import). Mai usarlo come proxy generico per il push. Non usarlo per servizi long-running. Ogni job deve sovrascrivere le proprie metriche, non accumulare. Considerare `honor_labels: true` nello scrape del Pushgateway.

**D: Come migrare da Nagios/Icinga a Prometheus?**
R: Approccio graduale: 1) Installare Prometheus + node_exporter in parallelo a Nagios. 2) Ricreare gli alert più importanti come alerting rules. 3) Costruire dashboard Grafana equivalenti. 4) Redirigere le notifiche da Alertmanager. 5) Spegnere i check Nagios uno alla volta, verificando la copertura. 6) Per check custom Nagios, valutare blackbox_exporter o script con textfile collector. La migrazione tipica richiede 2-4 mesi per un'infrastruttura di 100 server.

**D: Loki o Elasticsearch per i log?**
R: Loki se: usi già Grafana, vuoi correlazione nativa metriche-log, hai budget limitato (storage molto più economico), le query sono prevalentemente "grep-like". Elasticsearch se: hai bisogno di full-text search avanzato, analytics complesse sui log, compliance/audit con query arbitrarie, volume log molto alto con necessità di ricerche sub-secondo.

**D: Come monitorare servizi che non espongono metriche Prometheus?**
R: Tre approcci: 1) Blackbox exporter per check HTTP/TCP/ICMP (il servizio è raggiungibile?). 2) Textfile collector con script custom che raccoglie metriche e le scrive in formato Prometheus. 3) Cercare un exporter dedicato nel registro ufficiale (https://prometheus.io/docs/instrumenting/exporters/).

**D: Quanti target può gestire un singolo Prometheus?**
R: Un singolo Prometheus su hardware moderno (8 core, 32 GB RAM, SSD) gestisce 500.000-1.000.000 di serie attive, che corrisponde a circa 500-1.000 target con node_exporter. Oltre questo, usare federation o sharding (es. un Prometheus per datacenter o per team, con un Prometheus globale che federa le metriche aggregate).

**D: Come testare le regole di alert senza aspettare che il problema si verifichi?**
R: Usare `promtool test rules` con test file che simulano scenari. Usare anche `amtool` per verificare il routing. In alternativa, creare un target "test" che espone metriche artificiali per validare l'intera pipeline (metrica → alert → Alertmanager → notifica).

**D: Il mio team è piccolo, serve davvero un sistema di monitoring complesso?**
R: Anche per team piccoli, il minimo indispensabile è: Prometheus + node_exporter + Grafana + Alertmanager con notifiche email/Slack. Si installa in 1-2 ore, costa zero in licenze. L'alternativa (accorgersi dei problemi quando gli utenti chiamano) costa molto di più in termini di reputazione e downtime.

**D: Come gestire il monitoring in ambiente multi-cloud?**
R: Usare Prometheus con remote_write verso uno storage centralizzato (Thanos, Mimir, VictoriaMetrics). Ogni cloud/regione ha il proprio Prometheus locale che scrape i target e invia le metriche aggregate. Il querier centrale permette query globali con deduplicazione. Usare label `cloud=aws`, `region=eu-west-1` per filtrare.

**D: Devo monitorare anche i certificati SSL?**
R: Assolutamente. Un certificato scaduto causa disservizio immediato e perdita di fiducia degli utenti. Usare blackbox_exporter con il modulo `http_ssl_expiry` e alert a 30 giorni (warning) e 7 giorni (critical). Verificare anche i certificati interni (mTLS, certificati client, CA intermedie).

**D: Come gestire la rotazione dei segreti nell'Alertmanager?**
R: Non inserire mai segreti direttamente in `alertmanager.yml`. Usare variabili d'ambiente con `$ENV_VAR` nelle configurazioni. Oppure un secret manager (Vault, AWS Secrets Manager). Per SMTP e Slack webhook, ruotare i token regolarmente e testare le notifiche dopo ogni rotazione.

**D: Quali metriche devo monitorare per primo quando aggiungo un nuovo servizio?**
R: I golden signals: 1) Rate (richieste/secondo). 2) Error rate (% errori). 3) Duration (latenza p50, p95, p99). 4) Saturation (connessioni, thread pool, queue depth). Poi aggiungere USE per le risorse del server (CPU, memoria, disco, rete). Infine, metriche di business specifiche del servizio (ordini/minuto, utenti attivi, job in coda).

---

> **Prossimo modulo** · [21-troubleshooting-avanzato.md](./21-troubleshooting-avanzato.md)
