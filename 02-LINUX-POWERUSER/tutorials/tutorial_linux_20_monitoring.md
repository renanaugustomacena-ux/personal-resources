# Tutorial Linux 20 — Monitoring: Prometheus, node_exporter, Grafana, Alertmanager

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** stack Prometheus/Grafana completo, alert, esporta metriche, blackbox exporter
> **Prerequisiti:** `tutorial_linux_04_systemd.md`, `tutorial_linux_14_containerizzazione.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Stack Monitoring
│
├── Prometheus
│   ├── Scraping (pull model)
│   ├── PromQL — query language
│   ├── Recording rules
│   └── Alerting rules
│
├── Exporters
│   ├── node_exporter — sistema Linux
│   ├── postgres_exporter — PostgreSQL
│   ├── nginx_exporter — NGINX
│   ├── blackbox_exporter — HTTP/TCP/ping
│   └── custom — via textfile collector
│
├── Alertmanager
│   ├── Routing alert
│   ├── Deduplication / Silences
│   └── Receiver: Slack, PagerDuty, email
│
└── Grafana
    ├── Dashboard
    ├── Data sources
    └── Alert rules UI
```

---

# Parte A — Setup con Docker Compose

---

## A1. Stack completo

```yaml
# monitoring/docker-compose.yml
name: monitoring

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'     # reload senza restart
      - '--web.enable-admin-api'
    ports:
      - "9090:9090"
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    restart: unless-stopped
    volumes:
      - ./alertmanager:/etc/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
    ports:
      - "9093:9093"
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
      GF_USERS_ALLOW_SIGN_UP: false
      GF_SERVER_DOMAIN: grafana.esempio.it
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    pid: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    networks:
      - monitoring

  blackbox-exporter:
    image: prom/blackbox-exporter:latest
    container_name: blackbox-exporter
    restart: unless-stopped
    volumes:
      - ./blackbox:/etc/blackbox_exporter
    ports:
      - "9115:9115"
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
```

---

## A2. Configurazione Prometheus

```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    datacenter: 'dc1'
    environment: 'production'

# Alertmanager
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

# Regole alert
rule_files:
  - /etc/prometheus/rules/*.yml

# Scrape targets
scrape_configs:
  # Prometheus stesso
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node exporter (sistema)
  - job_name: 'node'
    static_configs:
      - targets:
          - 'node-exporter:9100'        # questo server
          - 'server2.interno.it:9100'   # altri server
          - 'server3.interno.it:9100'
    labels:
      team: infrastructure

  # PostgreSQL
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Nginx
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  # Blackbox — HTTP check
  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://esempio.it
          - https://api.esempio.it/health
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

---

# Parte B — Alert rules

---

## B1. Regole di alerting

```yaml
# monitoring/prometheus/rules/system.yml
groups:
  - name: sistema
    rules:
      # CPU
      - alert: CPUAlta
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU alta su {{ $labels.instance }}"
          description: "CPU al {{ $value | humanize }}% per più di 5 minuti"

      # Memoria
      - alert: MemoriaEsaurita
        expr: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100 < 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Memoria quasi esaurita su {{ $labels.instance }}"
          description: "Solo {{ $value | humanize }}% memoria disponibile"

      # Disco
      - alert: DiscipleSpazioEsaurito
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 15
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Spazio disco basso su {{ $labels.instance }}"
          description: "Disco / al {{ $value | humanize }}% disponibile"

      # Disco critico
      - alert: DiscoSpazioEsauritoCritico
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 5
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "CRITICO: Disco quasi pieno su {{ $labels.instance }}"

      # Load average
      - alert: LoadAltissimo
        expr: node_load15 / on(instance) group_left() count(node_cpu_seconds_total{mode="idle"}) by(instance) > 1.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Load average alto su {{ $labels.instance }}"

      # Host down
      - alert: HostDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Host {{ $labels.instance }} non raggiungibile"

  - name: servizi-web
    rules:
      # HTTP endpoint down
      - alert: EndpointHTTPDown
        expr: probe_success{job="blackbox-http"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Endpoint {{ $labels.instance }} non risponde"

      # SSL in scadenza
      - alert: SSLInScadenza
        expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Certificato SSL {{ $labels.instance }} scade tra {{ $value | humanizeDuration }}"
```

---

## B2. Alertmanager

```yaml
# monitoring/alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m
  smtp_from: alerts@esempio.it
  smtp_smarthost: smtp.gmail.com:587
  smtp_auth_username: alerts@esempio.it
  smtp_auth_password: "APP-PASSWORD"
  slack_api_url: "https://hooks.slack.com/services/XXX/YYY/ZZZ"

route:
  group_by: ['alertname', 'instance']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: slack-general

  routes:
    # Alert critici → PagerDuty + Slack
    - match:
        severity: critical
      receiver: pagerduty-critical
      continue: true

    # Alert su database → team DBA
    - match_re:
        alertname: "^(Postgres|Database).*"
      receiver: slack-dba

receivers:
  - name: slack-general
    slack_configs:
      - channel: '#alerts-infra'
        send_resolved: true
        title: '{{ .GroupLabels.alertname }}'
        text: >-
          {{ range .Alerts }}
            *Istanza:* {{ .Labels.instance }}
            *Descrizione:* {{ .Annotations.description }}
          {{ end }}
        color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'

  - name: email-admin
    email_configs:
      - to: admin@esempio.it
        require_tls: true

  - name: slack-dba
    slack_configs:
      - channel: '#alerts-database'

inhibit_rules:
  # Se un host è down, non invia alert per servizi su quell'host
  - source_match:
      alertname: 'HostDown'
    target_match_re:
      alertname: '^(CPUAlta|Disco.*|Memoria.*)$'
    equal: ['instance']
```

---

# Parte C — PromQL essenziale

---

## C1. Query fondamentali

```promql
# CPU utilizzata
100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# RAM disponibile in GB
node_memory_MemAvailable_bytes / 1024^3

# Disco usato %
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100

# Throughput rete in Mbps
irate(node_network_receive_bytes_total{device="eth0"}[5m]) * 8 / 1024^2

# Load average normalizzato per CPU
node_load5 / on(instance) count(node_cpu_seconds_total{mode="idle"}) by(instance)

# Top 5 processi per CPU
topk(5, process_cpu_seconds_total)

# Percentuale richieste HTTP con errore
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# Latenza p99
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

---

# Parte D — Grafana Dashboard

---

## D1. Provisioning automatico

```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: "15s"
```

```yaml
# grafana/provisioning/dashboards/dashboard.yml
apiVersion: 1

providers:
  - name: Default
    folder: ''
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
```

```bash
# Dashboard community popolari:
# Node Exporter Full: dashboard ID 1860 (importa da grafana.com)
# PostgreSQL: 9628
# Nginx: 9614
# Docker: 893

# Import dashboard
# Grafana UI → Dashboards → Import → inserisci ID
```

---

# Parte E — Riepilogo

## Setup rapido

```bash
# 1. Clone repository
mkdir monitoring && cd monitoring

# 2. Crea struttura
mkdir -p prometheus/rules alertmanager grafana/provisioning/{datasources,dashboards} blackbox

# 3. Copia configurazioni (sopra)

# 4. Avvia stack
docker compose up -d

# 5. Verifica
# Prometheus: http://localhost:9090/targets
# Alertmanager: http://localhost:9093
# Grafana: http://localhost:3000 (admin/admin)

# 6. Import dashboard Node Exporter Full (ID 1860)
```

## Metriche fondamentali da monitorare

| Metrica | Soglia warning | Soglia critica |
|---|---|---|
| CPU (5min avg) | > 80% | > 95% |
| RAM disponibile | < 20% | < 10% |
| Disco disponibile | < 20% | < 10% |
| Load avg / CPU | > 1.0 | > 2.0 |
| HTTP 5xx rate | > 1% | > 5% |
| Latenza p99 | > 1s | > 5s |
| Certificato SSL | 30 giorni | 7 giorni |

## Prossimi passi

- `tutorial_linux_30_prometheus_grafana.md` — configurazione avanzata PromQL
- `tutorial_linux_21_automazione.md` — cron, Ansible, automazione manutenzione
