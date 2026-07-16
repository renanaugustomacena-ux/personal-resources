# Tutorial: Monitoring e Observability — Prometheus, Grafana, Loki, OpenTelemetry — Lab Pratico

> **Documento di riferimento:** `08-monitoring-observability.md`
> **Dominio:** Gestione Piattaforme — Observability & Monitoring
> **Ambito:** I tre pilastri observability (metriche, log, trace), Prometheus 3.x (nuova UI, Remote Write 2.0, Native Histograms), PromQL (query language), Alertmanager con routing intelligente, Grafana 12 (React, no Angular), dashboard RED/USE, Loki + Promtail per log aggregation, OpenTelemetry Collector 0.155.x, distributed tracing con Jaeger, SLI/SLO/Error Budget
> **Durata lab:** 6-7 ore
> **Livello:** Intermedio-Avanzato — richiede conoscenza base di Docker Compose e Linux
> **Prerequisiti:** Docker Engine 29.x con Docker Compose, 8GB RAM raccomandati, porta 3000/9090/3100/16686 libere
> **Ambiente:** Stack LGTM completo via Docker Compose (Loki + Grafana + Tempo + Prometheus) + Jaeger + OTel Collector

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI OBSERVABILITY LAB ===
echo "=== CHECK PREREQUISITI ==="

# Docker e Compose disponibili?
docker --version && echo "[OK] Docker disponibile" || echo "[FAIL] Installare Docker"
docker compose version && echo "[OK] Docker Compose disponibile" || \
  echo "[FAIL] Installare Docker Compose"

# RAM disponibile (stack pesante: 4-6GB immagini + dati)
free_mb=$(free -m 2>/dev/null | awk 'NR==2{print $2}')
[ -n "$free_mb" ] && {
  [ "$free_mb" -gt 6000 ] && echo "[OK] RAM: ${free_mb}MB" || \
    echo "[WARN] RAM: ${free_mb}MB — raccomandati 8GB per il lab completo"
}

# Porte necessarie libere
for port in 3000 9090 9093 3100 16686 4317 4318; do
  ss -tlnp 2>/dev/null | grep -q ":${port} " && \
    echo "[WARN] Porta ${port} occupata" || echo "[OK] Porta ${port} libera"
done

echo ""
echo "=== SETUP DIRECTORY DI LAB ==="
mkdir -p ~/observability-lab/{prometheus,grafana,loki,otel,alertmanager,app}
cd ~/observability-lab

echo "[OK] Directory lab creata: ~/observability-lab"
```

### Architettura del Lab

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       OBSERVABILITY STACK                                │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                      INGESTIONE DATI                            │     │
│  │                                                                 │     │
│  │  app-demo → OTLP (gRPC :4317) → OTel Collector                │     │
│  │  node-exporter → HTTP :9100 ← Prometheus (scrape pull)        │     │
│  │  app-demo → stdout → Promtail → Loki                           │     │
│  └─────────────────┬───────────────────────────────────────────────┘     │
│                    │                                                      │
│  ┌─────────────────▼───────────────────────────────────────────────┐     │
│  │                      STORAGE                                    │     │
│  │                                                                 │     │
│  │  Prometheus 3.x :9090  │  Loki :3100   │  Jaeger :16686       │     │
│  │  (metriche TSDB)        │  (log store)   │  (trace store)       │     │
│  └─────────────────┬───────────────────────────────────────────────┘     │
│                    │                                                      │
│  ┌─────────────────▼───────────────────────────────────────────────┐     │
│  │                    VISUALIZZAZIONE                               │     │
│  │                                                                 │     │
│  │  Grafana 12.x :3000                                            │     │
│  │  ├── Data source: Prometheus (metriche)                         │     │
│  │  ├── Data source: Loki (log)                                    │     │
│  │  ├── Data source: Jaeger (trace)                                │     │
│  │  └── Alert: Alertmanager → Slack/Email/PagerDuty               │     │
│  └─────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
```

### Docker Compose — Stack Completo

```bash
cd ~/observability-lab

cat > compose.yaml << 'EOF'
name: "observability-lab"

networks:
  obs-net:
    driver: bridge

volumes:
  prometheus-data:
  grafana-data:
  loki-data:

services:
  
  # ──────────────────────────────────────────────────────────
  # APP DI DEMO (genera metriche, log, trace)
  # ──────────────────────────────────────────────────────────
  app-demo:
    image: prom/prometheus:v3.1.0   # temp: usiamo prometheus come demo app
    # In realtà useremo un'app Python con strumentazione OTel
    # Sostituta durante esercizi con l'app vera
    restart: unless-stopped
    networks: [obs-net]

  # ──────────────────────────────────────────────────────────
  # METRICHE: Prometheus 3.x
  # ──────────────────────────────────────────────────────────
  prometheus:
    image: prom/prometheus:v3.1.0
    container_name: prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--storage.tsdb.retention.time=15d"
      - "--storage.tsdb.retention.size=5GB"
      - "--web.enable-lifecycle"          # permette reload config via HTTP
      - "--web.enable-admin-api"
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - prometheus-data:/prometheus
    networks: [obs-net]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ──────────────────────────────────────────────────────────
  # ALERT MANAGEMENT: Alertmanager
  # ──────────────────────────────────────────────────────────
  alertmanager:
    image: prom/alertmanager:v0.27.0
    container_name: alertmanager
    command:
      - "--config.file=/etc/alertmanager/alertmanager.yml"
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    networks: [obs-net]
    restart: unless-stopped

  # ──────────────────────────────────────────────────────────
  # METRICHE SISTEMA: Node Exporter
  # ──────────────────────────────────────────────────────────
  node-exporter:
    image: prom/node-exporter:v1.8.2
    container_name: node-exporter
    pid: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - "--path.procfs=/host/proc"
      - "--path.sysfs=/host/sys"
      - "--path.rootfs=/rootfs"
      - "--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)"
    ports:
      - "9100:9100"
    networks: [obs-net]
    restart: unless-stopped

  # ──────────────────────────────────────────────────────────
  # LOG AGGREGATION: Loki
  # ──────────────────────────────────────────────────────────
  loki:
    image: grafana/loki:3.3.0
    container_name: loki
    ports:
      - "3100:3100"
    volumes:
      - ./loki/loki-config.yaml:/etc/loki/local-config.yaml:ro
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks: [obs-net]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3100/ready"]
      interval: 30s
      timeout: 10s
      retries: 5

  # ──────────────────────────────────────────────────────────
  # LOG COLLECTION: Promtail (agent Loki)
  # ──────────────────────────────────────────────────────────
  promtail:
    image: grafana/promtail:3.3.0
    container_name: promtail
    volumes:
      - ./loki/promtail-config.yaml:/etc/promtail/config.yaml:ro
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yaml
    networks: [obs-net]
    restart: unless-stopped

  # ──────────────────────────────────────────────────────────
  # TRACE STORAGE: Jaeger (all-in-one per lab)
  # ──────────────────────────────────────────────────────────
  jaeger:
    image: jaegertracing/all-in-one:1.63
    container_name: jaeger
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
    ports:
      - "16686:16686"    # UI
      - "14268:14268"    # HTTP thrift
      - "14250:14250"    # gRPC
    networks: [obs-net]
    restart: unless-stopped

  # ──────────────────────────────────────────────────────────
  # TELEMETRIA HUB: OpenTelemetry Collector (Contrib)
  # ──────────────────────────────────────────────────────────
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.115.0
    container_name: otel-collector
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel/otel-collector-config.yaml:/etc/otel-collector-config.yaml:ro
    ports:
      - "4317:4317"     # OTLP gRPC receiver
      - "4318:4318"     # OTLP HTTP receiver
      - "8888:8888"     # metriche self-monitoring del collector
      - "8889:8889"     # Prometheus exporter per metriche traces
    networks: [obs-net]
    restart: unless-stopped

  # ──────────────────────────────────────────────────────────
  # VISUALIZZAZIONE: Grafana 12.x
  # ──────────────────────────────────────────────────────────
  grafana:
    image: grafana/grafana:12.0.0
    container_name: grafana
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: grafana-lab-2026
      GF_USERS_ALLOW_SIGN_UP: "false"
      # Grafana 12: Angular rimosso completamente
      # Tutti i plugin devono essere React-based
      GF_PLUGINS_ENABLE_ALPHA: "false"
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    networks: [obs-net]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

EOF

echo "[OK] compose.yaml creato"
```

### Configurazione dei Componenti

```bash
cd ~/observability-lab

# ── Prometheus 3.x ────────────────────────────────────────────────────
mkdir -p prometheus/rules

cat > prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s       # scrape ogni 15 secondi
  evaluation_interval: 15s   # valuta le regole di alert ogni 15s
  scrape_timeout: 10s

# Alertmanager
alerting:
  alertmanagers:
  - static_configs:
    - targets: ["alertmanager:9093"]

# Regole di alert
rule_files:
  - "/etc/prometheus/rules/*.yml"

scrape_configs:
  # Prometheus auto-monitoring
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]
  
  # Metriche sistema (CPU, RAM, disco, rete)
  - job_name: "node-exporter"
    static_configs:
      - targets: ["node-exporter:9100"]
    relabel_configs:
      - target_label: instance
        replacement: "lab-machine"   # etichetta personalizzata

  # OpenTelemetry Collector self-monitoring
  - job_name: "otel-collector"
    static_configs:
      - targets: ["otel-collector:8888"]
  
  # Metriche trace (derivate da OTel Collector)
  - job_name: "otel-traces-metrics"
    static_configs:
      - targets: ["otel-collector:8889"]
EOF

# Regole di alert
cat > prometheus/rules/node-alerts.yml << 'EOF'
groups:
- name: node-resources
  interval: 1m        # valuta ogni minuto (sovrascrive global)
  rules:
  
  # CPU alta per più di 5 minuti
  - alert: HighCPUUsage
    expr: |
      100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
    for: 5m
    labels:
      severity: warning
      team: ops
    annotations:
      summary: "CPU alta su {{ $labels.instance }}"
      description: "CPU al {{ printf \"%.1f\" $value }}% da oltre 5 minuti."
      runbook_url: "https://wiki.azienda.it/runbook/high-cpu"
  
  # Memoria quasi esaurita
  - alert: HighMemoryUsage
    expr: |
      (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
    for: 3m
    labels:
      severity: warning
    annotations:
      summary: "Memoria alta su {{ $labels.instance }}"
      description: "Memoria usata: {{ printf \"%.1f\" $value }}%"
  
  # Disco quasi pieno (alert critico)
  - alert: DiskAlmostFull
    expr: |
      (node_filesystem_size_bytes{fstype!="tmpfs"} - node_filesystem_free_bytes) /
      node_filesystem_size_bytes{fstype!="tmpfs"} * 100 > 85
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Disco quasi pieno su {{ $labels.instance }}:{{ $labels.mountpoint }}"
      description: "Spazio usato: {{ printf \"%.1f\" $value }}%"
  
  # Nessuno scrape ricevuto (istanza down)
  - alert: InstanceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Istanza {{ $labels.instance }} non raggiungibile"
      description: "Lo scrape di {{ $labels.job }}/{{ $labels.instance }} fallisce da 1 minuto."
EOF

# ── Alertmanager ──────────────────────────────────────────────────────
mkdir -p alertmanager

cat > alertmanager/alertmanager.yml << 'EOF'
global:
  resolve_timeout: 5m
  # smtp_smarthost: 'smtp.gmail.com:587'
  # smtp_from: 'alerts@azienda.com'
  # smtp_auth_username: 'alerts@azienda.com'
  # smtp_auth_password_file: '/run/secrets/smtp_password'

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s         # attende 30s prima di inviare il primo alert del gruppo
  group_interval: 5m      # attende 5m prima di mandare nuovi alert dello stesso gruppo
  repeat_interval: 4h     # rimanda l'alert ogni 4h se non risolto
  receiver: "slack-ops"   # receiver default
  
  routes:
  # Alert critici → notifica immediata (no grouping)
  - match:
      severity: critical
    receiver: "pagerduty-critical"
    group_wait: 0s
    repeat_interval: 1h
  
  # Alert del team sicurezza
  - match:
      team: security
    receiver: "slack-security"

receivers:
- name: "slack-ops"
  slack_configs:
  - api_url: "https://hooks.slack.com/services/XXX/YYY/ZZZ"   # sostituire
    channel: "#ops-alerts"
    title: '{{ .CommonLabels.alertname }}'
    text: |
      {{ range .Alerts }}
      *Alert:* {{ .Labels.alertname }}
      *Severity:* {{ .Labels.severity }}
      *Summary:* {{ .Annotations.summary }}
      *Description:* {{ .Annotations.description }}
      {{ end }}

- name: "pagerduty-critical"
  pagerduty_configs:
  - routing_key: "PAGERDUTY_INTEGRATION_KEY"   # sostituire
    description: '{{ .CommonLabels.alertname }}: {{ .CommonAnnotations.summary }}'

- name: "slack-security"
  slack_configs:
  - api_url: "https://hooks.slack.com/services/XXX/YYY/ZZZ"
    channel: "#security-alerts"

inhibit_rules:
# Silenzia warning se c'è già un critical per la stessa istanza
- source_match:
    severity: critical
  target_match:
    severity: warning
  equal: ['instance', 'alertname']
EOF

# ── Loki ──────────────────────────────────────────────────────────────
mkdir -p loki

cat > loki/loki-config.yaml << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

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

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 100

schema_config:
  configs:
    - from: 2024-01-01
      store: tsdb
      object_store: filesystem
      schema: v13
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://alertmanager:9093

analytics:
  reporting_enabled: false
EOF

cat > loki/promtail-config.yaml << 'EOF'
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Log dei container Docker
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: container
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: service
      - source_labels: ['__meta_docker_container_image']
        target_label: image
    pipeline_stages:
      - json:
          expressions:
            level: level
            message: msg
      - labels:
          level:
      - output:
          source: message

  # Log di sistema
  - job_name: system
    static_configs:
      - targets: ["localhost"]
        labels:
          job: system
          __path__: /var/log/*.log
EOF

# ── OTel Collector ────────────────────────────────────────────────────
mkdir -p otel

cat > otel/otel-collector-config.yaml << 'EOF'
# OpenTelemetry Collector 0.115.x (Contrib)
# Versione corrente luglio 2026: v0.155.x
# La configurazione usa gli stessi componenti delle versioni recenti

receivers:
  # Riceve metriche/trace/log da applicazioni via OTLP
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  
  # Self-monitoring del collector
  prometheus:
    config:
      scrape_configs:
        - job_name: "otel-collector"
          static_configs:
            - targets: ["0.0.0.0:8888"]

processors:
  # Aggiunge attributi a tutte le telemetrie
  resource:
    attributes:
      - key: deployment.environment
        value: "lab"
        action: upsert
      - key: service.version
        from_attribute: "SERVICE_VERSION"
        action: insert
  
  # Comprime i batch per efficienza
  batch:
    timeout: 1s
    send_batch_size: 1024
  
  # Filtra metriche per ridurre il volume
  filter/exclude-noisy:
    metrics:
      exclude:
        match_type: regexp
        metric_names:
          - ".*_bucket$"    # escludi histogram bucket per ora (riduce volume)
  
  # Memory limiter: evita OOM del collector
  memory_limiter:
    check_interval: 1s
    limit_percentage: 75
    spike_limit_percentage: 15

exporters:
  # Trace → Jaeger
  otlp/jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  
  # Metriche → Prometheus (pull-based)
  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: "otel"
  
  # Log → Loki
  loki:
    endpoint: http://loki:3100/loki/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [otlp/jaeger]
    
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, resource, filter/exclude-noisy, batch]
      exporters: [prometheus]
    
    logs:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [loki]

  telemetry:
    metrics:
      address: 0.0.0.0:8888   # self-monitoring del collector stesso
    logs:
      level: info
EOF

# ── Grafana — Provisioning automatico ─────────────────────────────────
mkdir -p grafana/provisioning/{datasources,dashboards}

cat > grafana/provisioning/datasources/datasources.yaml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: "15s"
      httpMethod: POST
      exemplarTraceIdDestinations:
        - name: trace_id
          datasourceUid: jaeger-uid   # collega metriche → trace

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    uid: loki-uid
    editable: false
    jsonData:
      derivedFields:
        - name: trace_id
          matcherRegex: '"trace_id":"(\w+)"'
          url: "$${__value.raw}"
          datasourceUid: jaeger-uid   # collega log → trace

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686
    uid: jaeger-uid
    editable: false
EOF

cat > grafana/provisioning/dashboards/dashboards.yaml << 'EOF'
apiVersion: 1

providers:
  - name: "default"
    orgId: 1
    folder: "Lab"
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

echo "[OK] Configurazione stack completata"
```

---

## PART A: FONDAMENTI — I Tre Pilastri dell'Observability

> Prima del monitoring moderno, un sysadmin si accorgeva di un problema quando il telefono
> squillava: "il sito è down!". Poi arrivò il monitoring basico: "CPU al 95%, manda un alert".
> Meglio, ma ancora limitato — sai che qualcosa non va, ma non sai cosa né perché.
> L'observability moderna risponde a tre domande distinte: QUANTO (metriche), COSA (log),
> DOVE (trace). Solo con tutti e tre puoi rispondere a "cosa è successo alle 3:17 di notte
> che ha causato il 5% di errori per 90 secondi?"

---

### Concetto A1: Il Triangolo Metriche-Log-Trace

> **Analogia.** Immagina un medico di pronto soccorso. Per capire lo stato di un paziente
> usa tre strumenti diversi: il monitor (metriche: frequenza cardiaca, pressione, saturazione),
> la cartella clinica (log: "alle 14:32 ha avuto dolore toracico, alle 15:01 ha vomitato"),
> e la TAC (trace: "il problema originale è in questo vaso sanguigno, si è propagato qui e poi lì").
> Ogni strumento risponde a domande diverse. Senza tutti e tre, la diagnosi è incompleta.

```
TRE PILASTRI — QUANDO USARLI:

METRICHE (Prometheus, InfluxDB):
  Domanda: "QUANTO?" — numeri aggregati nel tempo
  Esempio: CPU 87%, 1523 req/s, latenza p99=340ms
  PRO: compatte, veloci, permette alert su soglie
  QUANDO: capire lo STATO GENERALE del sistema
  LIMITE: non dicono PERCHÉ un numero è cambiato

LOG (Loki, Elasticsearch):
  Domanda: "COSA?" — eventi discreti con contesto
  Esempio: [15:34:21] ERROR: Connection pool exhausted after 5000ms
  PRO: contesto completo dell'evento
  QUANDO: diagnosticare COSA è andato storto
  LIMITE: volume enorme (GB/giorno), costosi da indicizzare

TRACE (Jaeger, Zipkin):
  Domanda: "DOVE?" — percorso di una richiesta
  Esempio: richiesta A → nginx(5ms) → app(45ms) → redis(2ms) → DB(340ms)
  PRO: trovano DOVE si accumula la latenza in sistemi distribuiti
  QUANDO: diagnosticare latenza e dipendenze tra microservizi
  LIMITE: richiedono strumentazione del codice

COMBINAZIONE REALE:
  1. Dashboard metriche: "il p99 è salito a 800ms alle 15:34"
  2. Log correlati per timestamp: "Connection pool exhausted"
  3. Trace di una richiesta lenta: "il DB risponde in 700ms"
  → Diagnosi: il pool di connessioni DB è esaurito, aumentare pool_size
```

```bash
# Avviare lo stack e verificare che tutti i servizi siano pronti
cd ~/observability-lab
docker compose up -d

# Attendere la salute di tutti i servizi
echo "Attendo avvio stack (60-90 secondi)..."
sleep 30

# Verifica health check
for service in prometheus grafana loki; do
  HEALTH=$(docker compose ps $service --format json | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Health','?'))")
  echo "[INFO] $service: $HEALTH"
done

# Verifica accessi
curl -s http://localhost:9090/-/healthy | head -1 && \
  echo "[OK] Prometheus operativo"
curl -s http://localhost:3100/ready | head -1 && \
  echo "[OK] Loki operativo"
curl -s http://localhost:3000/api/health | python3 -m json.tool | grep '"database"' && \
  echo "[OK] Grafana operativo"
```

---

## PART B: PROMETHEUS 3.x — METRICHE E PROMQL

### Esercizio B1: Esplorare la Nuova UI di Prometheus 3.x

```bash
# Aprire Prometheus: http://localhost:9090
# Prometheus 3.0 (novembre 2024) ha una UI completamente nuova:
# - Tree-view stile PromLens
# - Metrics Explorer con ricerca
# - Tab "Explain" per PromQL queries
# - Remote Write 2.0 (60% meno messaggi, 90% meno allocazioni memoria)

echo "Apri: http://localhost:9090"
echo "Novità Prometheus 3.x:"
echo "  - Nuova UI (React, non più Angular/jQuery)"
echo "  - Native Histograms stabili"
echo "  - Remote Write 2.0"
echo "  - Agent mode stabile (usa --agent flag)"

# Versione di Prometheus attiva
curl -s http://localhost:9090/api/v1/status/buildinfo | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print('Prometheus:', d['data']['version'])"
```

---

### Esercizio B2: PromQL — Dalla Base all'Avanzato

```bash
# PromQL: Prometheus Query Language — esempi pratici

# Le query si eseguono sulla UI: http://localhost:9090

cat << 'PROMQL'
═══════════════════════════════════════════════════════════════
PROMQL — GUIDA PRATICA
═══════════════════════════════════════════════════════════════

── TIPI DI METRICHE ──────────────────────────────────────────

1. Counter (sempre crescente — contatore di eventi):
   prometheus_http_requests_total
   → conta le richieste totali. Non decresce mai.
   → usa rate() per vedere quanto cresce al secondo

2. Gauge (può salire e scendere — valore istantaneo):
   node_memory_MemAvailable_bytes
   → memoria disponibile in questo momento
   → usa direttamente, nessuna trasformazione necessaria

3. Histogram (distribuzione di valori — latenza, size):
   prometheus_http_request_duration_seconds_bucket
   → conta le richieste per bucket di latenza
   → usa histogram_quantile() per calcolare p50/p95/p99

── QUERY BASE ────────────────────────────────────────────────

# CPU utilizzo per core (in percentuale)
100 - (rate(node_cpu_seconds_total{mode="idle"}[5m]) * 100)

# Memoria usata in GB
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024^3

# Spazio disco usato in percentuale
(node_filesystem_size_bytes - node_filesystem_free_bytes) /
node_filesystem_size_bytes * 100

# Uptime del nodo in giorni
node_time_seconds - node_boot_time_seconds

── QUERY INTERMEDIATE ────────────────────────────────────────

# Rate delle richieste HTTP (richieste/secondo negli ultimi 5 minuti)
rate(prometheus_http_requests_total[5m])

# Solo le richieste con errore (status 4xx o 5xx)
rate(prometheus_http_requests_total{code=~"4..|5.."}[5m])

# Percentuale di errori
sum(rate(prometheus_http_requests_total{code=~"5.."}[5m])) /
sum(rate(prometheus_http_requests_total[5m])) * 100

# Latenza P99 (99° percentile)
histogram_quantile(0.99,
  sum by (le) (rate(prometheus_http_request_duration_seconds_bucket[5m]))
)

── QUERY AVANZATE ────────────────────────────────────────────

# Top 5 processi per consumo CPU
topk(5, rate(node_cpu_seconds_total{mode!="idle"}[5m]))

# Previsione: a questo ritmo, in quante ore il disco sarà pieno?
predict_linear(node_filesystem_free_bytes[6h], 24*3600) < 0

# Tasso di crescita del disco (bytes/secondo)
deriv(node_filesystem_size_bytes[5m])

# Anomalia: CPU più di 2 deviazioni standard dalla media
(rate(node_cpu_seconds_total{mode!="idle"}[5m]) -
 avg_over_time(rate(node_cpu_seconds_total{mode!="idle"}[5m])[1h:5m])) /
stddev_over_time(rate(node_cpu_seconds_total{mode!="idle"}[5m])[1h:5m]) > 2

═══════════════════════════════════════════════════════════════
PROMQL

# Eseguire le query via API (per automazione)
# CPU utilizzo medio
curl -s "http://localhost:9090/api/v1/query?query=100+-+(avg(rate(node_cpu_seconds_total%7Bmode%3D%22idle%22%7D%5B5m%5D))*100)" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print('CPU:', d['data']['result'])"

# Memoria disponibile in bytes
curl -s "http://localhost:9090/api/v1/query?query=node_memory_MemAvailable_bytes" | \
  python3 -c "
import json,sys
d=json.load(sys.stdin)
for r in d['data']['result']:
  mb = int(r['value'][1]) / 1024 / 1024
  print(f'Memoria disponibile: {mb:.0f} MB')
"
```

---

### Esercizio B3: Regole di Alert e Alertmanager

```bash
# Testare le regole di alert configurate
curl -s http://localhost:9090/api/v1/rules | \
  python3 -m json.tool | grep -A3 '"name"'

# Verificare lo stato degli alert
curl -s http://localhost:9090/api/v1/alerts | python3 -m json.tool

# Alertmanager UI: http://localhost:9093
# Mostra gli alert attivi, silenziati, e la configurazione del routing

# Creare un alert di test (forziamo la condizione)
# Nota: in un lab reale genereremmo carico CPU, qui vediamo la sintassi

# Aggiungere regola di alert per servizio down (sempre vera in lab se
# non tutti i servizi sono in su)
cat >> prometheus/rules/node-alerts.yml << 'RULE'

  # Alert di test — da rimuovere dopo il lab
  - alert: LabTestAlert
    expr: |
      count(up{job="node-exporter"} == 0) > 0
    for: 1m
    labels:
      severity: warning
      test: "true"
    annotations:
      summary: "Test alert dal lab"
      description: "Alert di test generato durante il laboratorio."
RULE

# Reload configurazione Prometheus (senza restart)
curl -X POST http://localhost:9090/-/reload
echo "[OK] Configurazione Prometheus ricaricata"
```

---

## PART C: GRAFANA 12 — DASHBOARD E VISUALIZZAZIONE

### Esercizio C1: Prima Dashboard in Grafana 12

```bash
echo "Apri Grafana: http://localhost:3000"
echo "Credenziali: admin / grafana-lab-2026"
echo ""
echo "NOVITÀ GRAFANA 12 (maggio 2025):"
echo "  - Angular completamente rimosso (era già disabilitato in v11)"
echo "  - Tutti i plugin devono essere React-based"
echo "  - Nuove API reattive (le legacy API di v11.4 sono rimosse)"
echo "  - OpsGenie contact point rimosso (usare webhook)"
echo "  - Scenes library per panel URL migliorate"

# La configurazione via provisioning è già stata applicata
# I data source Prometheus, Loki, Jaeger sono già configurati

# Dashboard preconfigurata via API Grafana
GRAFANA_URL="http://localhost:3000"
GRAFANA_AUTH="admin:grafana-lab-2026"

# Importare dashboard da Grafana.com (ID 1860 = Node Exporter Full)
curl -s -X POST \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_AUTH" \
  -d '{
    "dashboard": null,
    "inputs": [{"name": "DS_PROMETHEUS", "type": "datasource", "pluginId": "prometheus", "value": "Prometheus"}],
    "folderId": 0,
    "overwrite": true,
    "path": "dashboard/1860"
  }' \
  "$GRAFANA_URL/api/dashboards/import" || echo "[INFO] Import manuale disponibile in UI"

# Dashboard RED/USE personalizzata via API
cat > /tmp/dashboard-red-use.json << 'DASH'
{
  "dashboard": {
    "title": "RED/USE Lab Dashboard",
    "uid": "lab-red-use",
    "tags": ["lab", "red", "use"],
    "panels": [
      {
        "title": "CPU Utilizzo %",
        "type": "gauge",
        "gridPos": {"h": 8, "w": 8, "x": 0, "y": 0},
        "targets": [{
          "expr": "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
          "legendFormat": "CPU %"
        }],
        "options": {
          "reduceOptions": {"calcs": ["lastNotNull"]},
          "thresholds": {
            "steps": [
              {"color": "green", "value": null},
              {"color": "yellow", "value": 70},
              {"color": "red", "value": 85}
            ]
          }
        }
      },
      {
        "title": "Memoria Utilizzata %",
        "type": "gauge",
        "gridPos": {"h": 8, "w": 8, "x": 8, "y": 0},
        "targets": [{
          "expr": "(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100",
          "legendFormat": "Memoria %"
        }]
      },
      {
        "title": "Request Rate (req/s)",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
        "targets": [{
          "expr": "rate(prometheus_http_requests_total[5m])",
          "legendFormat": "{{handler}} {{code}}"
        }]
      }
    ],
    "time": {"from": "now-1h", "to": "now"},
    "refresh": "30s"
  },
  "overwrite": true,
  "folderId": 0
}
DASH

curl -s -X POST \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_AUTH" \
  -d @/tmp/dashboard-red-use.json \
  "$GRAFANA_URL/api/dashboards/db" | python3 -m json.tool
```

---

### Esercizio C2: Alert in Grafana (Grafana Alerting)

```bash
# Grafana 12 usa Grafana Alerting (non più Grafana Legacy Alerting)
# Permette di creare alert direttamente dai panel delle dashboard

# Creare un contact point Slack via API
curl -s -X POST \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_AUTH" \
  -d '{
    "uid": "lab-slack",
    "name": "Slack Lab",
    "type": "slack",
    "settings": {
      "url": "https://hooks.slack.com/services/XXX/YYY/ZZZ",
      "channel": "#alerts",
      "text": "{{ len .Alerts }} alert(s): {{ .Alerts | len }} totale"
    },
    "disableResolveMessage": false
  }' \
  "$GRAFANA_URL/api/alerting/contact-points" | python3 -m json.tool

# Creare una regola di alert
curl -s -X POST \
  -H "Content-Type: application/json" \
  -u "$GRAFANA_AUTH" \
  -d '{
    "name": "CPU Alert Group",
    "interval": "1m",
    "rules": [{
      "grafana_alert": {
        "title": "CPU Alta",
        "condition": "C",
        "data": [
          {
            "refId": "A",
            "datasourceUid": "__expr__",
            "model": {
              "type": "classic_conditions",
              "conditions": [{
                "evaluator": {"type": "gt", "params": [80]},
                "operator": {"type": "and"},
                "query": {"params": ["A"]},
                "reducer": {"type": "avg"},
                "type": "query"
              }]
            }
          }
        ],
        "noDataState": "NoData",
        "execErrState": "Error"
      },
      "for": "5m",
      "labels": {"severity": "warning"},
      "annotations": {
        "summary": "CPU alta",
        "description": "CPU sopra 80% per 5 minuti"
      }
    }]
  }' \
  "$GRAFANA_URL/api/ruler/grafana/api/v1/rules/lab-alerts"

echo "[OK] Alert creato in Grafana"
```

---

## PART D: LOKI — AGGREGAZIONE LOG

### Esercizio D1: LogQL — Il Linguaggio di Query di Loki

```bash
# Loki usa LogQL — simile a PromQL ma per log
# Regola base: Loki NON indicizza il contenuto dei log (solo label)
# → molto più economico di Elasticsearch
# → molto meno flessibile per ricerche full-text complesse

cat << 'LOGQL'
═══════════════════════════════════════════════════════════════
LOGQL — GUIDA PRATICA
═══════════════════════════════════════════════════════════════

── QUERY BASE (Log Stream Selectors) ────────────────────────

# Tutti i log di Prometheus
{container="prometheus"}

# Log del container grafana con level ERROR
{container="grafana"} |= "level=error"

# Log che contengono "error" (case insensitive)
{service="lab-app"} |~ "(?i)error"

# Log JSON parsati — estrae il campo level
{container="otel-collector"} | json | level = "error"

── METRIC QUERIES (su log) ──────────────────────────────────

# Rate degli errori (linee con "error" al secondo)
rate({container="prometheus"} |= "error" [5m])

# Conta per livello di log
sum by (level) (
  count_over_time(
    {container="grafana"} | json | __error__="" [5m]
  )
)

# Top 5 endpoint con errori
topk(5,
  sum by (path) (
    rate({service="app"} | json | status_code =~ "5.." [5m])
  )
)

── PIPELINE STAGES ──────────────────────────────────────────

# Parsare log JSON e filtrare per campo
{container="app"} | json | duration > 1000ms | line_format "Slow: {{.path}} {{.duration}}"

# Estrarre metriche dai log con pattern
{container="nginx"} | pattern '<ip> - <user> [<ts>] "<method> <path> HTTP/<ver>" <status> <bytes>'
| status = "500"
| line_format "500 error: {{.method}} {{.path}}"

═══════════════════════════════════════════════════════════════
LOGQL

# Accedere a Loki via API
# Ultimi 100 log di Prometheus
START=$(date -d '1 hour ago' +%s 2>/dev/null || date -v-1H +%s)000000000
END=$(date +%s)000000000

curl -s -G \
  --data-urlencode 'query={container="prometheus"}' \
  --data-urlencode "start=$START" \
  --data-urlencode "end=$END" \
  --data-urlencode "limit=10" \
  "http://localhost:3100/loki/api/v1/query_range" | \
  python3 -c "
import json, sys
d = json.load(sys.stdin)
results = d.get('data', {}).get('result', [])
for stream in results[:3]:
  print('Labels:', stream['stream'])
  for ts, line in stream['values'][:3]:
    print(' ->', line[:100])
"

# In Grafana: http://localhost:3000 → Explore → Selezionare Loki come data source
echo "[OK] Loki operativo — accedere via Grafana → Explore → Loki"
```

---

## PART E: OPENTELEMETRY COLLECTOR — HUB DI TELEMETRIA

### Esercizio E1: App con Strumentazione OTel

```bash
mkdir -p ~/observability-lab/app

# App Python con strumentazione OpenTelemetry
cat > ~/observability-lab/app/app.py << 'PYEOF'
"""App di demo con full OpenTelemetry instrumentation"""
import time, random, os
from flask import Flask, jsonify
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.instrumentation.flask import FlaskInstrumentor
import logging, json

# ── Setup Logging strutturato (va a Loki via Promtail) ─────────────
logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s","service":"demo-app"}'
)
logger = logging.getLogger(__name__)

# ── Setup Tracing (va a Jaeger via OTel Collector) ─────────────────
OTEL_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=OTEL_ENDPOINT))
)
tracer = trace.get_tracer(__name__)

# ── Setup Metrics (va a Prometheus via OTel Collector) ──────────────
reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=OTEL_ENDPOINT), export_interval_millis=10000
)
metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))
meter = metrics.get_meter(__name__)

# Metriche custom
request_counter = meter.create_counter(
    "app_requests_total", description="Totale richieste"
)
request_duration = meter.create_histogram(
    "app_request_duration_ms", description="Durata richieste in ms"
)

# ── Flask App ───────────────────────────────────────────────────────
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)  # strumentazione automatica

@app.route('/health')
def health():
    return jsonify({"status": "ok", "service": "demo-app"})

@app.route('/process')
def process():
    start = time.time()
    with tracer.start_as_current_span("process-request") as span:
        # Simulare latenza variabile (50-500ms)
        latency = random.uniform(0.05, 0.5)
        time.sleep(latency)
        
        # Simulare errore sporadico (10% dei casi)
        if random.random() < 0.1:
            span.set_status(trace.StatusCode.ERROR, "Simulated error")
            span.set_attribute("error.type", "SimulatedError")
            logger.error("Errore simulato nella richiesta", extra={"path": "/process"})
            request_counter.add(1, {"status": "error", "endpoint": "/process"})
            return jsonify({"error": "Internal error"}), 500
        
        span.set_attribute("latency_ms", latency * 1000)
        duration_ms = (time.time() - start) * 1000
        request_duration.record(duration_ms, {"endpoint": "/process"})
        request_counter.add(1, {"status": "ok", "endpoint": "/process"})
        logger.info(f"Richiesta completata in {duration_ms:.1f}ms")
        return jsonify({"message": "OK", "duration_ms": round(duration_ms, 1)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
PYEOF

cat > ~/observability-lab/app/requirements.txt << 'EOF'
flask==3.1.0
opentelemetry-api==1.31.0
opentelemetry-sdk==1.31.0
opentelemetry-exporter-otlp-proto-grpc==1.31.0
opentelemetry-instrumentation-flask==0.52b0
EOF

cat > ~/observability-lab/app/Dockerfile << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
USER 10001
EXPOSE 8080
CMD ["python", "app.py"]
EOF

# Costruire e aggiungere al compose
docker build -t demo-otel-app:latest ~/observability-lab/app/

# Avviare la demo app con il collector
docker run -d \
  --name demo-otel-app \
  --network observability-lab_obs-net \
  -e OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317 \
  -e OTEL_SERVICE_NAME=demo-app \
  -p 18080:8080 \
  demo-otel-app:latest

# Generare traffico per il lab
echo "Generando traffico verso l'app..."
for i in $(seq 1 50); do
  curl -s http://localhost:18080/process > /dev/null
  sleep 0.2
done

echo "[OK] Traffico generato — vedere trace in http://localhost:16686 (Jaeger)"
echo "     Metriche in Grafana: http://localhost:3000 → data source Prometheus"
echo "     Log in Grafana: http://localhost:3000 → Explore → Loki"
```

---

## PART F: SLI/SLO/ERROR BUDGET

### Esercizio F1: Definire SLO e Calcolare Error Budget

> **Analogia.** Un SLO è come un contratto di qualità che un ristorante firma con sé stesso:
> "Ci impegniamo a servire ogni piatto in meno di 30 minuti nel 99% dei casi". Non è una
> promessa al cliente (quella è la SLA), è un obiettivo interno. L'error budget è il margine
> di tolleranza: se il SLO è 99%, ho l'1% di "budget" per fallire — se lo uso troppo velocemente,
> devo fermare i deploy e concentrarmi sull'affidabilità.

```bash
cat << 'SLO_GUIDE'
═══════════════════════════════════════════════════════════════
SLI/SLO/ERROR BUDGET — CONCETTI PRATICI
═══════════════════════════════════════════════════════════════

SLI (Service Level Indicator) = la metrica che misuriamo
  Esempi:
  - Availability: (richieste riuscite / richieste totali) * 100
  - Latency: percentuale di richieste sotto 300ms
  - Throughput: richieste/secondo > 1000
  - Error rate: errori 5xx / richieste totali

SLO (Service Level Objective) = il target del SLI
  Esempi:
  - Availability SLO: 99.9% (i.e., max 8.7 ore/anno di downtime)
  - Latency SLO: 95% delle richieste in meno di 300ms
  - Error rate SLO: meno di 0.1% errori 5xx

ERROR BUDGET = quanto possiamo "sbagliare" e restare nel SLO
  Se SLO = 99.9% (30 giorni):
  - Budget totale = 0.1% × 30 giorni × 24h × 60m = 43.2 minuti/mese
  - Se il sistema è stato down 20 minuti questo mese:
    Budget rimanente = 43.2 - 20 = 23.2 minuti
  - Se il budget è esaurito → STOP dei deploy non critici
    (qualsiasi deploy rischia di usare il budget rimanente)

CALCOLO IN PROMQL:
  # Availability delle ultime 24 ore
  sum(rate(prometheus_http_requests_total{code!~"5.."}[24h])) /
  sum(rate(prometheus_http_requests_total[24h])) * 100

  # Error budget consumato (in %)
  1 - (
    sum(rate(prometheus_http_requests_total{code!~"5.."}[30d])) /
    sum(rate(prometheus_http_requests_total[30d]))
  ) / 0.001  # 0.001 = 0.1% error rate budget per un SLO 99.9%
═══════════════════════════════════════════════════════════════
SLO_GUIDE

# Dashboard SLO in Grafana (via API)
cat > /tmp/slo-dashboard.json << 'DASH'
{
  "dashboard": {
    "title": "SLO Dashboard",
    "uid": "slo-lab",
    "panels": [
      {
        "title": "Availability 24h (%)",
        "type": "stat",
        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 0},
        "targets": [{
          "expr": "sum(rate(prometheus_http_requests_total{code!~\"5..\"}[24h])) / sum(rate(prometheus_http_requests_total[24h])) * 100",
          "legendFormat": "Availability"
        }],
        "options": {
          "thresholds": {
            "steps": [
              {"color": "red", "value": null},
              {"color": "yellow", "value": 99},
              {"color": "green", "value": 99.9}
            ]
          }
        }
      }
    ]
  },
  "overwrite": true,
  "folderId": 0
}
DASH

curl -s -X POST \
  -H "Content-Type: application/json" \
  -u "admin:grafana-lab-2026" \
  -d @/tmp/slo-dashboard.json \
  "http://localhost:3000/api/dashboards/db"

echo "[OK] Dashboard SLO creata: http://localhost:3000/d/slo-lab"
```

---

## Conclusioni e Prossimi Passi

```
OBSERVABILITY — RIEPILOGO:

I TRE PILASTRI:
  ✓ Metriche (Prometheus 3.x): aggregazioni numeriche, alert su soglie
  ✓ Log (Loki 3.3): log aggregation con LogQL, integrazione Grafana
  ✓ Trace (Jaeger + OTel): percorso richiesta attraverso microservizi

PROMETHEUS 3.x (novembre 2024):
  ✓ Nuova UI completa (React-based)
  ✓ Remote Write 2.0: 60% meno traffico, 90% meno allocazioni
  ✓ Native Histograms stabili (h_classic → h_native)
  ✓ Agent mode stabile (flag --agent)
  ✓ PromQL: range selectors ora left-open (breaking change)

GRAFANA 12 (maggio 2025):
  ✓ Angular rimosso completamente
  ✓ React-only plugin ecosystem
  ✓ Scenes library per panel URL
  ✓ Grafana Alerting (non più legacy alerting)

LOGQL (Loki):
  ✓ {label="value"} — stream selector
  ✓ | json — parse JSON log
  ✓ rate({...}[5m]) — rate di log al secondo
  ✓ Più economico di Elasticsearch (nessun full-text index)

OPENTELEMETRY COLLECTOR (0.155.x):
  ✓ Core vs Contrib: usare Contrib per la maggior parte dei casi
  ✓ Pipeline: receivers → processors → exporters
  ✓ OTLP via gRPC :4317 e HTTP :4318
  ✓ Vendor-agnostico: switch backend senza riscrivere il codice

SLI/SLO/ERROR BUDGET:
  ✓ SLI: cosa misuriamo (availability, latency, error rate)
  ✓ SLO: il target (99.9% availability)
  ✓ Error budget: margine di tolleranza (43.2 min/mese per 99.9%)

COMANDI ESSENZIALI:
  docker compose up/down/logs
  curl http://localhost:9090/api/v1/query?query=...
  curl http://localhost:3100/loki/api/v1/query_range?query=...
```

**Prossimi tutorial:**
- `tutorial_plat09_service_mesh_lab.md` — Istio mTLS e traffic management
- `tutorial_plat13_sicurezza_piattaforme_lab.md` — Falco runtime security
- `tutorial_plat24_sre_lab.md` — SRE: error budget policy, chaos engineering

```bash
# Pulizia lab
cd ~/observability-lab
docker stop demo-otel-app 2>/dev/null && docker rm demo-otel-app 2>/dev/null
docker compose down -v
rm -rf ~/observability-lab

echo "[OK] Lab Monitoring e Observability completato"
```

---

> **Nota versioni:** Tutorial validato con Prometheus 3.1.0, Grafana 12.0.0, Loki 3.3.0,
> OTel Collector 0.115.0 (configurazione compatibile con 0.155.x, luglio 2026).
> Breaking change Prometheus 3.0: le Content-Type non valide durante lo scrape non hanno
> più fallback al formato testuale — lo scrape fallisce; aggiornare gli exporter legacy.
> Breaking change Grafana 12: Angular rimosso — verificare compatibilità plugin prima dell'upgrade.
