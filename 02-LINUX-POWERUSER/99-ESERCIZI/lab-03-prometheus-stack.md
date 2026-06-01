# Lab 03 — Stack Prometheus + Grafana + Loki Completo

> **Modulo di riferimento:** [30-prometheus-grafana-monitoring.md](../30-prometheus-grafana-monitoring.md), [20-monitoring.md](../20-monitoring.md)
> **Tempo stimato:** 3-4 ore
> **Livello:** proficient
> **Prerequisiti:** VM Debian 12 con 4 GB RAM, completamento moduli 04, 14, 20
> **Ultimo aggiornamento:** 2026-05-23

---

## Obiettivo

Costruire uno stack di observability completo: Prometheus per metriche, Grafana per visualizzazione, Alertmanager per notifiche, Loki per log aggregation. Configurare dashboard, alert rules, e recording rules operative.

---

## Ambiente

- VM Debian 12 (4 vCPU, 4 GB RAM, 40 GB disco)
- Accesso root
- Connessione internet per scaricare binari

---

## Parte 1 — Prometheus (45 min)

### 1.1 Installazione

```bash
# Creare utente dedicato
useradd --no-create-home --shell /usr/sbin/nologin prometheus

# Scaricare e installare
PROM_VER="2.53.0"
cd /tmp
wget "https://github.com/prometheus/prometheus/releases/download/v${PROM_VER}/prometheus-${PROM_VER}.linux-amd64.tar.gz"
tar xzf "prometheus-${PROM_VER}.linux-amd64.tar.gz"
cp "prometheus-${PROM_VER}.linux-amd64"/{prometheus,promtool} /usr/local/bin/
cp -r "prometheus-${PROM_VER}.linux-amd64"/{consoles,console_libraries} /etc/prometheus/

# Directory
mkdir -p /etc/prometheus/rules /var/lib/prometheus
chown -R prometheus:prometheus /etc/prometheus /var/lib/prometheus
```

### 1.2 Configurazione

```bash
cat > /etc/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  scrape_timeout: 10s

rule_files:
  - "rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "node"
    static_configs:
      - targets: ["localhost:9100"]

  - job_name: "blackbox"
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - http://localhost:9090/-/healthy
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9115
EOF

chown prometheus:prometheus /etc/prometheus/prometheus.yml
```

### 1.3 Recording rules

```bash
cat > /etc/prometheus/rules/recording.yml << 'EOF'
groups:
  - name: node_recording
    interval: 15s
    rules:
      - record: instance:node_cpu_utilisation:ratio
        expr: 1 - avg without(cpu) (rate(node_cpu_seconds_total{mode="idle"}[5m]))

      - record: instance:node_memory_utilisation:ratio
        expr: 1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)

      - record: instance:node_disk_utilisation:ratio
        expr: 1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})

      - record: instance:node_network_receive_bytes:rate5m
        expr: rate(node_network_receive_bytes_total{device!~"lo|veth.*|br.*"}[5m])

      - record: instance:node_network_transmit_bytes:rate5m
        expr: rate(node_network_transmit_bytes_total{device!~"lo|veth.*|br.*"}[5m])
EOF

chown prometheus:prometheus /etc/prometheus/rules/recording.yml
```

### 1.4 Alert rules

```bash
cat > /etc/prometheus/rules/alerts.yml << 'EOF'
groups:
  - name: node_alerts
    rules:
      - alert: HighCPU
        expr: instance:node_cpu_utilisation:ratio > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU alta su {{ $labels.instance }}"
          description: "CPU al {{ $value | humanizePercentage }} da 5+ minuti."

      - alert: HighMemory
        expr: instance:node_memory_utilisation:ratio > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memoria alta su {{ $labels.instance }}"
          description: "Memoria al {{ $value | humanizePercentage }}."

      - alert: DiskAlmostFull
        expr: instance:node_disk_utilisation:ratio > 0.8
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Disco quasi pieno su {{ $labels.instance }}"
          description: "Disco root al {{ $value | humanizePercentage }}."

      - alert: InstanceDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Istanza {{ $labels.instance }} down"
          description: "{{ $labels.job }} su {{ $labels.instance }} non raggiungibile da 2 minuti."

      - alert: HighLoadAverage
        expr: node_load15 / count without(cpu) (node_cpu_seconds_total{mode="idle"}) > 2
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Load average alto su {{ $labels.instance }}"

  - name: prometheus_alerts
    rules:
      - alert: PrometheusConfigReloadFailed
        expr: prometheus_config_last_reload_successful == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Prometheus config reload fallito"

      - alert: PrometheusTSDBCompactionsFailed
        expr: increase(prometheus_tsdb_compactions_failed_total[1h]) > 0
        labels:
          severity: warning
        annotations:
          summary: "Compaction TSDB fallita"
EOF

chown prometheus:prometheus /etc/prometheus/rules/alerts.yml
```

### 1.5 Systemd unit

```bash
cat > /etc/systemd/system/prometheus.service << 'EOF'
[Unit]
Description=Prometheus Monitoring
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
Restart=on-failure
RestartSec=5s
ExecStart=/usr/local/bin/prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/var/lib/prometheus \
    --storage.tsdb.retention.time=30d \
    --storage.tsdb.retention.size=10GB \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries \
    --web.enable-lifecycle \
    --web.enable-admin-api
ExecReload=/bin/kill -HUP $MAINPID

ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/lib/prometheus
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now prometheus

# Validare config
promtool check config /etc/prometheus/prometheus.yml
promtool check rules /etc/prometheus/rules/*.yml
```

---

## Parte 2 — Exporters (30 min)

### 2.1 Node Exporter

```bash
NODE_VER="1.8.1"
cd /tmp
wget "https://github.com/prometheus/node_exporter/releases/download/v${NODE_VER}/node_exporter-${NODE_VER}.linux-amd64.tar.gz"
tar xzf "node_exporter-${NODE_VER}.linux-amd64.tar.gz"
cp "node_exporter-${NODE_VER}.linux-amd64/node_exporter" /usr/local/bin/

useradd --no-create-home --shell /usr/sbin/nologin node_exporter

cat > /etc/systemd/system/node-exporter.service << 'EOF'
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
Restart=on-failure
ExecStart=/usr/local/bin/node_exporter \
    --collector.systemd \
    --collector.processes \
    --no-collector.infiniband \
    --no-collector.nfs \
    --no-collector.nfsd

ProtectSystem=strict
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now node-exporter

# Verificare
curl -s http://localhost:9100/metrics | head -5
```

### 2.2 Blackbox Exporter

```bash
BB_VER="0.25.0"
cd /tmp
wget "https://github.com/prometheus/blackbox_exporter/releases/download/v${BB_VER}/blackbox_exporter-${BB_VER}.linux-amd64.tar.gz"
tar xzf "blackbox_exporter-${BB_VER}.linux-amd64.tar.gz"
cp "blackbox_exporter-${BB_VER}.linux-amd64/blackbox_exporter" /usr/local/bin/

useradd --no-create-home --shell /usr/sbin/nologin blackbox

mkdir -p /etc/blackbox_exporter
cat > /etc/blackbox_exporter/config.yml << 'EOF'
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: []
      method: GET
      follow_redirects: true
      preferred_ip_protocol: ip4

  icmp:
    prober: icmp
    timeout: 5s

  tcp_connect:
    prober: tcp
    timeout: 5s
EOF

cat > /etc/systemd/system/blackbox-exporter.service << 'EOF'
[Unit]
Description=Blackbox Exporter
After=network.target

[Service]
User=blackbox
Group=blackbox
Type=simple
Restart=on-failure
ExecStart=/usr/local/bin/blackbox_exporter \
    --config.file=/etc/blackbox_exporter/config.yml

ProtectSystem=strict
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now blackbox-exporter
```

---

## Parte 3 — Alertmanager (30 min)

### 3.1 Installazione e configurazione

```bash
AM_VER="0.27.0"
cd /tmp
wget "https://github.com/prometheus/alertmanager/releases/download/v${AM_VER}/alertmanager-${AM_VER}.linux-amd64.tar.gz"
tar xzf "alertmanager-${AM_VER}.linux-amd64.tar.gz"
cp "alertmanager-${AM_VER}.linux-amd64"/{alertmanager,amtool} /usr/local/bin/

useradd --no-create-home --shell /usr/sbin/nologin alertmanager
mkdir -p /etc/alertmanager /var/lib/alertmanager
chown alertmanager:alertmanager /var/lib/alertmanager

cat > /etc/alertmanager/alertmanager.yml << 'EOF'
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'instance']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-webhook'
      continue: true
    - match:
        severity: warning
      receiver: 'default'

inhibit_rules:
  - source_match:
      alertname: InstanceDown
    target_match_re:
      alertname: '.*'
    equal: ['instance']

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:5001/webhook'
        send_resolved: true

  - name: 'critical-webhook'
    webhook_configs:
      - url: 'http://localhost:5001/webhook-critical'
        send_resolved: true
EOF

chown -R alertmanager:alertmanager /etc/alertmanager

cat > /etc/systemd/system/alertmanager.service << 'EOF'
[Unit]
Description=Alertmanager
After=network.target

[Service]
User=alertmanager
Group=alertmanager
Type=simple
Restart=on-failure
ExecStart=/usr/local/bin/alertmanager \
    --config.file=/etc/alertmanager/alertmanager.yml \
    --storage.path=/var/lib/alertmanager \
    --web.listen-address=:9093

ProtectSystem=strict
ReadWritePaths=/var/lib/alertmanager
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now alertmanager
```

---

## Parte 4 — Grafana (45 min)

### 4.1 Installazione

```bash
apt install -y apt-transport-https software-properties-common

wget -qO- https://apt.grafana.com/gpg.key | gpg --dearmor > /usr/share/keyrings/grafana.gpg
echo "deb [signed-by=/usr/share/keyrings/grafana.gpg] https://apt.grafana.com stable main" \
    > /etc/apt/sources.list.d/grafana.list

apt update
apt install -y grafana

systemctl enable --now grafana-server
```

### 4.2 Provisioning datasource

```bash
cat > /etc/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://localhost:3100
    editable: false
EOF
```

### 4.3 Dashboard provisioning

```bash
mkdir -p /var/lib/grafana/dashboards

cat > /etc/grafana/provisioning/dashboards/default.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: 'Provisioned'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
EOF
```

### 4.4 Dashboard host overview (USE method)

```bash
cat > /var/lib/grafana/dashboards/host-overview.json << 'DASHBOARD_EOF'
{
  "dashboard": {
    "title": "Host Overview (USE Method)",
    "uid": "host-overview",
    "timezone": "browser",
    "refresh": "30s",
    "time": { "from": "now-1h", "to": "now" },
    "panels": [
      {
        "title": "CPU Utilization",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 8, "x": 0, "y": 0 },
        "targets": [{
          "expr": "instance:node_cpu_utilisation:ratio",
          "legendFormat": "{{instance}}"
        }],
        "fieldConfig": {
          "defaults": { "unit": "percentunit", "max": 1, "min": 0 }
        }
      },
      {
        "title": "Memory Utilization",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 8, "x": 8, "y": 0 },
        "targets": [{
          "expr": "instance:node_memory_utilisation:ratio",
          "legendFormat": "{{instance}}"
        }],
        "fieldConfig": {
          "defaults": { "unit": "percentunit", "max": 1, "min": 0 }
        }
      },
      {
        "title": "Disk Utilization (/)",
        "type": "gauge",
        "gridPos": { "h": 8, "w": 8, "x": 16, "y": 0 },
        "targets": [{
          "expr": "instance:node_disk_utilisation:ratio",
          "legendFormat": "{{instance}}"
        }],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit", "max": 1, "min": 0,
            "thresholds": {
              "steps": [
                { "color": "green", "value": null },
                { "color": "yellow", "value": 0.7 },
                { "color": "red", "value": 0.85 }
              ]
            }
          }
        }
      },
      {
        "title": "Network I/O",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
        "targets": [
          {
            "expr": "instance:node_network_receive_bytes:rate5m",
            "legendFormat": "recv {{device}}"
          },
          {
            "expr": "-instance:node_network_transmit_bytes:rate5m",
            "legendFormat": "send {{device}}"
          }
        ],
        "fieldConfig": { "defaults": { "unit": "Bps" } }
      },
      {
        "title": "Load Average",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 8 },
        "targets": [
          { "expr": "node_load1", "legendFormat": "1m" },
          { "expr": "node_load5", "legendFormat": "5m" },
          { "expr": "node_load15", "legendFormat": "15m" }
        ]
      }
    ]
  },
  "overwrite": true
}
DASHBOARD_EOF

chown -R grafana:grafana /var/lib/grafana/dashboards/
systemctl restart grafana-server
```

---

## Parte 5 — Loki + Promtail (30 min)

### 5.1 Loki

```bash
LOKI_VER="3.1.0"
cd /tmp
wget "https://github.com/grafana/loki/releases/download/v${LOKI_VER}/loki-linux-amd64.zip"
unzip loki-linux-amd64.zip
cp loki-linux-amd64 /usr/local/bin/loki
chmod +x /usr/local/bin/loki

useradd --no-create-home --shell /usr/sbin/nologin loki
mkdir -p /etc/loki /var/lib/loki
chown loki:loki /var/lib/loki

cat > /etc/loki/config.yml << 'EOF'
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
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  max_query_series: 5000

compactor:
  working_directory: /var/lib/loki/compactor
  compaction_interval: 10m
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150
EOF

cat > /etc/systemd/system/loki.service << 'EOF'
[Unit]
Description=Loki Log Aggregation
After=network.target

[Service]
User=loki
Group=loki
Type=simple
Restart=on-failure
ExecStart=/usr/local/bin/loki -config.file=/etc/loki/config.yml

ProtectSystem=strict
ReadWritePaths=/var/lib/loki
NoNewPrivileges=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now loki
```

### 5.2 Promtail

```bash
wget "https://github.com/grafana/loki/releases/download/v${LOKI_VER}/promtail-linux-amd64.zip"
unzip promtail-linux-amd64.zip
cp promtail-linux-amd64 /usr/local/bin/promtail
chmod +x /usr/local/bin/promtail

mkdir -p /etc/promtail

cat > /etc/promtail/config.yml << 'EOF'
server:
  http_listen_port: 9080

positions:
  filename: /var/lib/promtail/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: journal
    journal:
      max_age: 12h
      labels:
        job: systemd-journal
    relabel_configs:
      - source_labels: ['__journal__systemd_unit']
        target_label: 'unit'
      - source_labels: ['__journal__hostname']
        target_label: 'hostname'
      - source_labels: ['__journal_priority_keyword']
        target_label: 'level'

  - job_name: syslog
    static_configs:
      - targets:
          - localhost
        labels:
          job: syslog
          __path__: /var/log/syslog

  - job_name: auth
    static_configs:
      - targets:
          - localhost
        labels:
          job: authlog
          __path__: /var/log/auth.log
EOF

mkdir -p /var/lib/promtail

cat > /etc/systemd/system/promtail.service << 'EOF'
[Unit]
Description=Promtail Log Collector
After=network.target loki.service

[Service]
Type=simple
Restart=on-failure
ExecStart=/usr/local/bin/promtail -config.file=/etc/promtail/config.yml

ProtectSystem=strict
ReadWritePaths=/var/lib/promtail
ReadOnlyPaths=/var/log
NoNewPrivileges=yes
SupplementaryGroups=adm systemd-journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now promtail
```

---

## Parte 6 — Verifica (30 min)

### 6.1 Checklist servizi

```bash
for svc in prometheus node-exporter blackbox-exporter alertmanager grafana-server loki promtail; do
    printf "%-25s %s\n" "$svc" "$(systemctl is-active $svc)"
done
```

### 6.2 Verificare metriche

```bash
# Prometheus targets
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool | grep -E '"health"|"job"'

# Numero metriche
curl -s http://localhost:9090/api/v1/label/__name__/values | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']))"

# Recording rules attive
curl -s http://localhost:9090/api/v1/rules | python3 -m json.tool | grep -c "recording"

# Alert rules
curl -s http://localhost:9090/api/v1/rules | python3 -m json.tool | grep -c "alerting"
```

### 6.3 Verificare Loki

```bash
# Query test
curl -s "http://localhost:3100/loki/api/v1/query_range" \
    --data-urlencode 'query={job="systemd-journal"}' \
    --data-urlencode 'limit=5' | python3 -m json.tool | head -20
```

### 6.4 Test alert

```bash
# Simulare disco pieno (creare file grande)
dd if=/dev/zero of=/tmp/diskfill bs=1M count=100

# Verificare alert in Prometheus
curl -s http://localhost:9090/api/v1/alerts | python3 -m json.tool

# Cleanup
rm /tmp/diskfill
```

---

## Criteri di Completamento

- [ ] Tutti i servizi attivi e healthy
- [ ] Prometheus: ≥ 3 target UP
- [ ] Recording rules: 5 regole attive
- [ ] Alert rules: ≥ 6 regole configurate
- [ ] Alertmanager: routing e inhibition configurati
- [ ] Grafana: dashboard host overview accessibile su :3000
- [ ] Loki: log da journal visibili in Grafana
- [ ] Promtail: posizioni tracciate, log in arrivo

---

## Riferimenti

- Prometheus Documentation — https://prometheus.io/docs/ (consultato: 2026-05-23)
- Grafana Documentation — https://grafana.com/docs/ (consultato: 2026-05-23)
- Loki Documentation — https://grafana.com/docs/loki/latest/ (consultato: 2026-05-23)
- [30-prometheus-grafana-monitoring.md](../30-prometheus-grafana-monitoring.md)
- [20-monitoring.md](../20-monitoring.md)
