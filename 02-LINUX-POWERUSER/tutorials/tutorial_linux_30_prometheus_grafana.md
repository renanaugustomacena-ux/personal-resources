# Tutorial Linux 30 — Prometheus, Grafana e Monitoring Avanzato

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** PromQL avanzato, recording rules, Grafana alerting, Loki aggregazione, tracing
> **Prerequisiti:** `tutorial_linux_20_monitoring.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Monitoring Stack
│
├── Metriche
│   ├── Prometheus (scrape + tsdb)
│   ├── PromQL (query language)
│   └── Recording rules (pre-aggregazione)
│
├── Visualizzazione
│   ├── Grafana (dashboard)
│   ├── Alerting (Grafana Unified)
│   └── Annotazioni e correlazioni
│
├── Log
│   ├── Loki (log aggregazione)
│   ├── Promtail / Alloy (agent)
│   └── LogQL (query language)
│
└── Tracing
    ├── Tempo (storage trace)
    ├── Jaeger (raccolta trace)
    └── OpenTelemetry (standard)
```

---

# Parte A — PromQL Avanzato

---

## A1. Tipi di metriche e operatori

```
# Tipi di metriche Prometheus:
# Counter — solo incrementa (es. richieste totali, errori)
# Gauge   — può salire e scendere (es. uso memoria, connessioni attive)
# Histogram — distribuzione in bucket (es. latenza HTTP)
# Summary — percentili precalcolati

# Selettore di base
http_requests_total                          # tutti i valori
http_requests_total{job="api"}               # filtro per label
http_requests_total{status!="200"}           # negazione
http_requests_total{path=~"/api/.*"}         # regex match
http_requests_total{path!~"/health.*"}       # regex negazione

# Range vector
http_requests_total[5m]    # ultimi 5 minuti di campioni
http_requests_total[1h]    # ultima ora

# Funzioni su counter (rate/irate/increase)
rate(http_requests_total[5m])              # rate medio per secondo (ultimi 5m)
irate(http_requests_total[1m])            # rate istantaneo (ultimi 2 punti)
increase(http_requests_total[1h])         # incremento totale nell'ultima ora

# Aggregazioni
sum(rate(http_requests_total[5m]))                     # somma su tutti i label
sum by (job)(rate(http_requests_total[5m]))            # somma per job
sum without (instance)(rate(http_requests_total[5m])) # somma escludendo instance
avg, min, max, count, topk, bottomk

# Operazioni su gauge
100 - (avg by (instance)(
    rate(node_cpu_seconds_total{mode="idle"}[5m])
) * 100)
# CPU usage % per instance
```

---

## A2. Recording rules

```yaml
# /etc/prometheus/rules/recording_rules.yml
groups:
  - name: node_aggregations
    interval: 1m    # calcola ogni minuto
    rules:
      # CPU usage pre-aggregato (evita PromQL pesante su dashboard)
      - record: instance:node_cpu_usage:rate5m
        expr: |
          100 - (
            avg by (instance) (
              rate(node_cpu_seconds_total{mode="idle"}[5m])
            ) * 100
          )

      # Memory usage %
      - record: instance:node_memory_usage:ratio
        expr: |
          1 - (
            node_memory_MemAvailable_bytes /
            node_memory_MemTotal_bytes
          )

      # Disk write rate
      - record: instance:node_disk_write:rate5m
        expr: sum by (instance) (
          rate(node_disk_written_bytes_total[5m])
        )

  - name: http_service_aggregations
    interval: 30s
    rules:
      # Error rate per servizio
      - record: job:http_error_rate:rate5m
        expr: |
          sum by (job) (
            rate(http_requests_total{status=~"5.."}[5m])
          ) /
          sum by (job) (
            rate(http_requests_total[5m])
          )

      # Latenza p99 per servizio
      - record: job:http_request_duration_p99:5m
        expr: |
          histogram_quantile(0.99,
            sum by (job, le) (
              rate(http_request_duration_seconds_bucket[5m])
            )
          )
```

---

# Parte B — Alert Rules Avanzate

---

## B1. Alert con routing intelligente

```yaml
# /etc/prometheus/rules/alerts.yml
groups:
  - name: infrastructure
    rules:
      # CPU alta per 5 minuti
      - alert: CPUAltaSostenuta
        expr: instance:node_cpu_usage:rate5m > 85
        for: 5m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "CPU alta su {{ $labels.instance }}"
          description: "CPU al {{ $value | printf \"%.1f\" }}% da più di 5 minuti"
          runbook: "https://wiki/runbooks/cpu-alta"

      # Disco quasi pieno
      - alert: DiscoQuasiPieno
        expr: |
          (
            node_filesystem_avail_bytes{fstype!~"tmpfs|fuse.lxcfs|squashfs"}
            / node_filesystem_size_bytes
          ) < 0.10
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Disco sotto 10% su {{ $labels.instance }}"
          description: "{{ $labels.mountpoint }}: {{ $value | humanizePercentage }} disponibile"

      # Memory pressure
      - alert: MemoriaPressione
        expr: instance:node_memory_usage:ratio > 0.90
        for: 5m
        labels:
          severity: warning

  - name: application
    rules:
      # Error rate > 1%
      - alert: ErrorRateAlta
        expr: job:http_error_rate:rate5m > 0.01
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Error rate > 1% per {{ $labels.job }}"
          description: "Error rate: {{ $value | humanizePercentage }}"

      # Latenza p99 > 2 secondi
      - alert: LatenzaP99Alta
        expr: job:http_request_duration_p99:5m > 2
        for: 5m
        labels:
          severity: critical

      # Servizio down
      - alert: ServizioDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
          pager: "true"
        annotations:
          summary: "{{ $labels.job }} down su {{ $labels.instance }}"
```

---

## B2. Alertmanager routing

```yaml
# /etc/alertmanager/alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/XXX/YYY/ZZZ'

route:
  group_by: ['alertname', 'job']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: slack-ops

  routes:
    # Critical con pager → PagerDuty
    - match:
        severity: critical
        pager: "true"
      receiver: pagerduty
      group_wait: 10s
      repeat_interval: 1h

    # Team database
    - match_re:
        alertname: ".*Postgres.*|.*DB.*"
      receiver: slack-dba

    # Silenzia alert noti durante manutenzione
    # (configurare via amtool o UI)

receivers:
  - name: slack-ops
    slack_configs:
      - channel: '#ops-alerts'
        send_resolved: true
        title: '{{ if eq .Status "firing" }}🔥{{ else }}✅{{ end }} {{ .GroupLabels.alertname }}'
        text: |
          *Severity:* {{ (index .Alerts 0).Labels.severity }}
          {{ range .Alerts }}
          • {{ .Annotations.summary }}
          {{ end }}

  - name: pagerduty
    pagerduty_configs:
      - routing_key: 'CHIAVE_PAGERDUTY'
        severity: '{{ .CommonLabels.severity }}'

  - name: slack-dba
    slack_configs:
      - channel: '#dba-alerts'
        send_resolved: true

inhibit_rules:
  # Se un host è down, non inviare alert per i servizi su quell'host
  - source_match:
      alertname: ServizioDown
    target_match_re:
      alertname: ".*Alta.*|.*Pieno.*"
    equal: ['instance']
```

---

# Parte C — Loki e Log Aggregazione

---

## C1. Stack completo con Alloy

```yaml
# docker-compose.monitoring.yml
services:
  loki:
    image: grafana/loki:3.0.0
    command: -config.file=/etc/loki/config.yml
    volumes:
      - ./loki-config.yml:/etc/loki/config.yml
      - loki-data:/loki
    ports:
      - "3100:3100"

  alloy:
    image: grafana/alloy:latest
    volumes:
      - ./alloy-config.river:/etc/alloy/config.river
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    privileged: true

  tempo:
    image: grafana/tempo:latest
    command: -config.file=/etc/tempo/config.yml
    volumes:
      - ./tempo-config.yml:/etc/tempo/config.yml
      - tempo-data:/tmp/tempo

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin_sicuro
    volumes:
      - ./grafana-provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
```

```river
// alloy-config.river
// Raccolta log da file
local.file_match "varlog" {
  path_targets = [{"__path__" = "/var/log/**/*.log"}]
}

loki.source.file "varlog" {
  targets    = local.file_match.varlog.targets
  forward_to = [loki.write.default.receiver]
}

// Raccolta log Docker
discovery.docker "containers" {
  host = "unix:///var/run/docker.sock"
}

loki.source.docker "docker" {
  host       = "unix:///var/run/docker.sock"
  targets    = discovery.docker.containers.targets
  forward_to = [loki.write.default.receiver]
  labels     = {component = "docker"}
}

loki.write "default" {
  endpoint {
    url = "http://loki:3100/loki/api/v1/push"
  }
}
```

---

## C2. LogQL — query Loki

```
# LogQL syntax (simile a PromQL + filtro log)

# Selettore stream (label)
{job="nginx", env="production"}

# Filtro log
{job="nginx"} |= "error"          # contiene "error"
{job="nginx"} != "health"         # non contiene "health"
{job="nginx"} |~ "status=5\\d\\d" # regex match

# Parser (estrae campi da log)
{job="nginx"} | json                         # parsing JSON
{job="nginx"} | json | status >= 500         # filtra dopo parsing
{job="nginx"} | pattern `<ip> - <user> [<ts>] "<method> <path> <proto>" <status> <size>`
{job="nginx"} | logfmt                       # key=value format
{job="nginx"} | regexp `status=(?P<status>\d+)`

# Metriche da log
rate({job="nginx"} |= "error" [5m])               # error rate
count_over_time({job="nginx"} |= "500" [1h])      # count 500 in un'ora

# Top path con più errori
topk(10,
  sum by (path) (
    rate({job="nginx"} | json | status >= 500 [5m])
  )
)
```

---

# Parte D — Grafana Provisioning

---

## D1. Dashboard e datasource as code

```yaml
# grafana-provisioning/datasources/all.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: "15s"
      exemplarTraceIdDestinations:
        - name: traceID
          datasourceUid: tempo

  - name: Loki
    type: loki
    url: http://loki:3100
    jsonData:
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: "traceID=(\\w+)"
          name: TraceID
          url: "${__value.raw}"

  - name: Tempo
    uid: tempo
    type: tempo
    url: http://tempo:3200
    jsonData:
      tracesToMetrics:
        datasourceUid: prometheus
```

```yaml
# grafana-provisioning/alerting/rules.yml
apiVersion: 1
groups:
  - orgId: 1
    name: infrastruttura
    folder: Alerts
    interval: 1m
    rules:
      - uid: cpu-alta
        title: CPU Alta
        condition: C
        data:
          - refId: A
            relativeTimeRange:
              from: 300
              to: 0
            datasourceUid: prometheus
            model:
              expr: "instance:node_cpu_usage:rate5m > 85"
              legendFormat: "{{instance}}"
          - refId: C
            datasourceUid: __expr__
            model:
              conditions:
                - evaluator:
                    params: [0]
                    type: gt
                  query:
                    params: [A]
              type: threshold
        noDataState: NoData
        execErrState: Alerting
        for: 5m
        labels:
          severity: warning
```

---

# Parte E — Riepilogo

## Cheatsheet PromQL

```
# CPU
100 - (avg by (instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memoria
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# Disco
(1 - (node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes)) * 100

# HTTP error rate
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# HTTP p99 latency
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Servizi down
up == 0

# Top 5 endpoint per richieste/s
topk(5, sum by (path) (rate(http_requests_total[5m])))
```

## Tabella componenti stack

| Componente | Ruolo | Porta |
|---|---|---|
| Prometheus | Scrape + storage metriche | 9090 |
| Alertmanager | Routing alert | 9093 |
| node_exporter | Metriche OS | 9100 |
| Loki | Storage log | 3100 |
| Alloy | Agent raccolta | — |
| Tempo | Storage trace | 3200 |
| Grafana | Visualizzazione | 3000 |

## Prossimi passi

- `tutorial_linux_31_ansible.md` — automazione infrastruttura
- `tutorial_linux_20_monitoring.md` — stack base Prometheus
