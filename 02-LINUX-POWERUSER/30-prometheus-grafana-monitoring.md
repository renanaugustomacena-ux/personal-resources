---
title: "Prometheus e Grafana: Stack di Monitoring"
modulo: 30
categoria: "Linux Power User"
data_creazione: 2026-04-27
data_aggiornamento: 2026-05-23
difficolta: avanzato
tags:
  - monitoring
  - prometheus
  - grafana
  - alerting
  - observability
  - tsdb
  - promql
  - thanos
  - kubernetes
prerequisiti:
  - "Fondamenti di Linux (moduli 01-10)"
  - "Networking TCP/IP (modulo 20)"
  - "Systemd e gestione servizi (modulo 12)"
  - "Docker e container (modulo 25)"
  - "YAML syntax"
tempo_stimato: "40-50 ore"
fonti_primarie:
  - "https://prometheus.io/docs/ (consultato: 2026-05-23)"
  - "https://grafana.com/docs/grafana/latest/ (consultato: 2026-05-23)"
  - "https://openmetrics.io/ (consultato: 2026-05-23)"
  - "https://thanos.io/tip/thanos/design.md/ (consultato: 2026-05-23)"
  - "https://www.cncf.io/projects/ (consultato: 2026-05-23)"
---

# Prometheus e Grafana: Stack di Monitoring — Guida Approfondita

> **Modulo 30** · **Aggiornamento:** 2026-04-27

## Idee guida
1. **Prometheus pull + service discovery (consul, k8s).**
2. **Grafana 11+: variables, alerting unified.**
3. **Tempo (traces) + Loki (logs) + Mimir (long-term metrics) full stack.**
4. **Recording rules + alerting rules separati.**


## Indice

- [Panoramica](#panoramica)
- [Architettura Prometheus](#architettura-prometheus)
  - [TSDB Internals: WAL, Blocchi, Compaction](#tsdb-internals-wal-blocchi-compaction)
  - [Ciclo di Vita dello Scrape](#ciclo-di-vita-dello-scrape)
  - [Service Discovery Avanzata](#service-discovery-avanzata)
  - [Relabeling: relabel_configs vs metric_relabel_configs](#relabeling-relabel_configs-vs-metric_relabel_configs)
- [Installazione e Configurazione Prometheus](#installazione-e-configurazione-prometheus)
- [PromQL: Linguaggio di Query](#promql-linguaggio-di-query)
  - [Instant Vector vs Range Vector](#instant-vector-vs-range-vector)
  - [rate vs irate vs increase](#rate-vs-irate-vs-increase)
  - [histogram_quantile in Profondità](#histogram_quantile-in-profondità)
  - [Operatori di Aggregazione: by e without](#operatori-di-aggregazione-by-e-without)
  - [Subquery](#subquery)
  - [Anti-Pattern PromQL](#anti-pattern-promql)
- [Recording Rules](#recording-rules)
  - [Convenzioni di Naming per Recording Rules](#convenzioni-di-naming-per-recording-rules)
  - [Recording Rules e Performance](#recording-rules-e-performance)
- [Alerting Rules e Alertmanager](#alerting-rules-e-alertmanager)
  - [Architettura Alertmanager](#architettura-alertmanager-deep-dive)
  - [Routing Tree in Dettaglio](#routing-tree-in-dettaglio)
  - [Grouping, Inhibition, Silencing Avanzati](#grouping-inhibition-silencing-avanzati)
  - [Integrazione Webhook](#integrazione-webhook)
  - [Prevenzione Alert Fatigue](#prevenzione-alert-fatigue)
  - [Alert SLO Multi-Window Multi-Burn-Rate](#alert-slo-multi-window-multi-burn-rate)
- [Exporter: node_exporter e blackbox_exporter](#exporter-node_exporter-e-blackbox_exporter)
- [Ecosistema Exporter Avanzato](#ecosistema-exporter-avanzato)
  - [node_exporter: Metriche Chiave](#node_exporter-metriche-chiave)
  - [mysqld_exporter](#mysqld_exporter)
  - [postgres_exporter](#postgres_exporter)
  - [Exporter Personalizzati (Go e Python)](#exporter-personalizzati-go-e-python)
  - [Pushgateway: Casi d'Uso e Anti-Pattern](#pushgateway-casi-duso-e-anti-pattern)
- [Grafana: Installazione e Configurazione](#grafana-installazione-e-configurazione)
- [Grafana: Dashboard Avanzate](#grafana-dashboard-avanzate)
  - [Principi di Design delle Dashboard](#principi-di-design-delle-dashboard)
  - [Tipi di Panel](#tipi-di-panel)
  - [Dashboard-as-Code](#dashboard-as-code)
  - [Provisioning Automatizzato](#provisioning-automatizzato)
- [Grafana: Alerting Unificato](#grafana-alerting-unificato)
  - [Architettura dell'Alerting Unificato](#architettura-dellalerting-unificato)
  - [Contact Points](#contact-points)
  - [Notification Policies](#notification-policies)
  - [Alert Rules in Grafana](#alert-rules-in-grafana)
  - [Relazione con Alertmanager](#relazione-con-alertmanager)
- [Setup Completo End-to-End](#setup-completo-end-to-end)
- [Federation e Scaling](#federation-e-scaling)
  - [Federation Gerarchica](#federation-gerarchica)
  - [Thanos: Architettura Completa](#thanos-architettura-completa)
  - [Cortex e Mimir](#cortex-e-mimir)
  - [remote_write e remote_read](#remote_write-e-remote_read)
  - [Storage a Lungo Termine (S3/GCS)](#storage-a-lungo-termine-s3gcs)
- [Metodologia RED e USE](#metodologia-red-e-use)
- [Prometheus Operator su Kubernetes](#prometheus-operator-su-kubernetes)
- [Exemplars e Correlazione Metriche-Trace](#exemplars-e-correlazione-metriche-trace)
  - [Cosa Sono gli Exemplars](#cosa-sono-gli-exemplars)
  - [Configurazione Prometheus per Exemplars](#configurazione-prometheus-per-exemplars)
  - [Instrumentazione Client con Exemplars](#instrumentazione-client-con-exemplars)
  - [Visualizzazione Exemplars in Grafana](#visualizzazione-exemplars-in-grafana)
- [Sicurezza](#sicurezza)
- [Gestione Operativa](#gestione-operativa)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Esercizi Pratici](#esercizi-pratici)
- [Autovalutazione](#autovalutazione)
- [Letture Consigliate e Cross-Link](#letture-consigliate-e-cross-link)
- [Riferimenti](#riferimenti)
- [Glossario](#glossario)

---

## Panoramica

Il monitoring è il sistema nervoso di un'infrastruttura IT. Senza monitoring, l'amministratore è cieco: scopre i problemi solo quando gli utenti li segnalano, non ha dati storici per l'analisi delle cause e non può fare capacity planning. Prometheus e Grafana formano lo stack di monitoring open source più diffuso e potente, adottato come standard de facto dall'ecosistema cloud-native e dalla Cloud Native Computing Foundation (CNCF).

Prometheus è un sistema di monitoring e alerting basato su metriche numeriche time-series, con un modello pull (è Prometheus che raccoglie le metriche, non i target che le inviano). È progettato per affidabilità: ogni istanza è autonoma, senza dipendenze esterne. Se il database muore, Prometheus perde i dati storici ma continua a raccogliere e a fare alerting. Grafana è la piattaforma di visualizzazione che trasforma le metriche grezze in dashboard interattive e comprensibili.

Questo documento guida passo passo nella configurazione di uno stack di monitoring completo: dall'installazione di Prometheus e dei suoi exporter (node_exporter per metriche OS, blackbox_exporter per probe di rete), alla configurazione di Alertmanager con routing e receivers, fino alla creazione di dashboard Grafana con variabili, annotations e alerting integrato.

---

## Architettura Prometheus

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │ node_exporter│   │ node_exporter│   │ app /metrics │    │
│  │ :9100        │   │ :9100        │   │ :8080        │    │
│  │ (server1)    │   │ (server2)    │   │ (app server) │    │
│  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘    │
│         │                  │                   │             │
│         │    HTTP GET /metrics (scrape)         │             │
│         │                  │                   │             │
│  ┌──────▼──────────────────▼───────────────────▼──────────┐ │
│  │                    Prometheus                           │ │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────────────┐ │ │
│  │  │ Scraper    │  │ TSDB       │  │ Rule Engine      │ │ │
│  │  │ (pull)     │  │ (storage)  │  │ (recording +     │ │ │
│  │  │            │  │            │  │  alerting rules)  │ │ │
│  │  └────────────┘  └────────────┘  └────────┬─────────┘ │ │
│  └──────────────────────────────────────────┬────────────┘ │
│                                              │              │
│  ┌───────────────────────────────────────────▼────────────┐ │
│  │                   Alertmanager                          │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │ │
│  │  │ Routing  │  │ Grouping │  │ Receivers            │ │ │
│  │  │          │  │ Silencing│  │ (email, Slack, PD)   │ │ │
│  │  └──────────┘  └──────────┘  └──────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                      Grafana                            │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │ │
│  │  │ Dashboard│  │ Variables│  │ Alerting             │ │ │
│  │  │          │  │ Templating│ │                      │ │ │
│  │  └──────────┘  └──────────┘  └──────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Concetti Fondamentali

**Metric**: Un valore numerico con un nome e un set di label (coppie chiave-valore):
```
node_cpu_seconds_total{cpu="0", mode="idle"} 123456.78
│                      │                      │
│                      └── Label             └── Valore
└── Nome della metrica
```

**Tipi di Metrica:**
| Tipo | Descrizione | Esempio |
|------|-------------|---------|
| Counter | Monotonicamente crescente | `http_requests_total` |
| Gauge | Valore variabile (su e giù) | `node_memory_MemFree_bytes` |
| Histogram | Distribuzione (bucket) | `http_request_duration_seconds` |
| Summary | Distribuzione (quantili pre-calcolati) | `go_gc_duration_seconds` |

**Scrape**: Il processo con cui Prometheus raccoglie metriche da un target HTTP endpoint (`/metrics`).

### TSDB Internals: WAL, Blocchi, Compaction

Il TSDB (Time Series Database) di Prometheus è il motore di storage locale. Comprenderne l'architettura è fondamentale per il dimensionamento, il tuning e la risoluzione dei problemi.

> Riferimento: https://prometheus.io/docs/prometheus/latest/storage/ (consultato: 2026-05-23)

#### Write-Ahead Log (WAL)

Tutti i campioni in ingresso vengono prima scritti nel WAL prima di essere processati in memoria. Il WAL garantisce la durabilità dei dati in caso di crash: al riavvio, Prometheus rilegge il WAL e ricostruisce lo stato in memoria.

```
Flusso di scrittura:
  scrape → WAL (disco, append-only) → head block (memoria) → blocco persistente (disco)
```

Caratteristiche del WAL:
- Directory: `<storage.tsdb.path>/wal/`
- Formato: segmenti sequenziali di 128 MB ciascuno
- Retention: i segmenti WAL vengono rimossi dopo che i dati sono stati persistiti in un blocco
- Checkpoint: periodicamente Prometheus crea checkpoint WAL per ridurre il tempo di replay al riavvio

```bash
# Struttura tipica della directory TSDB
ls -la /var/lib/prometheus/
# wal/              ← Write-Ahead Log
# chunks_head/      ← Chunk in memoria mappati su disco
# 01HQRS.../        ← Blocchi persistenti (ULID come nome)
# 01HQRT.../
# lock              ← File di lock (una sola istanza per directory)
```

#### Blocchi e Compaction

I dati in memoria (head block) vengono periodicamente "tagliati" (cut) e scritti su disco come blocchi immutabili. Ogni blocco copre un intervallo temporale tipico di 2 ore.

```
Struttura di un blocco:
  01HQRS.../
  ├── meta.json       ← Metadati: range temporale, statistiche, livello compaction
  ├── index           ← Indice invertito: label → serie → chunk
  ├── chunks/
  │   ├── 000001      ← Chunk di dati compressi (XOR encoding per float64)
  │   └── 000002
  └── tombstones       ← Marker di cancellazione (delete API)
```

La **compaction** è il processo background che fonde blocchi più piccoli in blocchi più grandi:
- Riduce il numero di blocchi su disco
- Migliora le performance delle query (meno file da scansionare)
- Rimuove dati cancellati (tombstones) e serie duplicate
- I livelli di compaction seguono una progressione: 2h → 6h → 18h → 54h...

```
Timeline compaction:
  [2h][2h][2h] → compaction → [6h]
  [6h][6h][6h] → compaction → [18h]
```

#### Retention

La retention controlla quanto a lungo Prometheus mantiene i dati:

| Flag | Descrizione | Default |
|------|-------------|---------|
| `--storage.tsdb.retention.time` | Durata massima dei dati | 15d |
| `--storage.tsdb.retention.size` | Dimensione massima dello storage | 0 (illimitato) |

Quando entrambi sono impostati, il criterio più restrittivo vince. La cancellazione avviene per blocchi interi, quindi la retention effettiva può essere leggermente superiore al valore configurato.

```bash
# Metriche TSDB utili per il monitoraggio
prometheus_tsdb_head_series          # Serie attive nel head block
prometheus_tsdb_head_chunks          # Chunk nel head block
prometheus_tsdb_blocks_loaded        # Blocchi caricati
prometheus_tsdb_compactions_total    # Compaction eseguite
prometheus_tsdb_wal_corruptions_total # Corruzione WAL (deve essere 0)
prometheus_tsdb_storage_blocks_bytes # Spazio occupato dai blocchi
```

### Ciclo di Vita dello Scrape

Ogni ciclo di scrape segue un percorso preciso. Comprendere questo percorso è essenziale per il debugging di problemi di raccolta metriche.

```
1. Service Discovery       → Scopre i target (da static_configs, consul_sd, k8s_sd...)
2. relabel_configs          → Trasforma/filtra i target PRIMA dello scrape
3. HTTP GET /metrics        → Richiesta HTTP al target
4. Parsing                  → Prometheus parsa il formato exposition (text/OpenMetrics)
5. metric_relabel_configs   → Trasforma/filtra le metriche DOPO il parsing
6. Append to TSDB           → I campioni vengono scritti nel WAL e nel head block
7. Generazione metriche     → Prometheus genera up{}, scrape_duration_seconds, ecc.
   di scrape
```

Metriche generate automaticamente per ogni scrape:

| Metrica | Significato |
|---------|-------------|
| `up` | 1 se lo scrape ha avuto successo, 0 altrimenti |
| `scrape_duration_seconds` | Durata dello scrape in secondi |
| `scrape_samples_scraped` | Numero di campioni raccolti |
| `scrape_samples_post_metric_relabeling` | Campioni dopo metric_relabel_configs |
| `scrape_series_added` | Nuove serie create in questo scrape |

### Service Discovery Avanzata

La service discovery automatica è uno dei punti di forza di Prometheus. Invece di elencare manualmente ogni target, Prometheus può scoprirli dinamicamente.

> Riferimento: https://prometheus.io/docs/prometheus/latest/configuration/configuration/#scrape_config (consultato: 2026-05-23)

#### file_sd_configs

Il meccanismo più semplice e flessibile. Prometheus legge i target da file JSON o YAML e li ricarica automaticamente quando i file cambiano.

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'file-sd-example'
    file_sd_configs:
      - files:
          - '/etc/prometheus/file_sd/*.json'
        refresh_interval: 30s
```

```json
// /etc/prometheus/file_sd/webservers.json
[
  {
    "targets": ["web01:9100", "web02:9100", "web03:9100"],
    "labels": {
      "env": "production",
      "team": "platform"
    }
  },
  {
    "targets": ["staging-web01:9100"],
    "labels": {
      "env": "staging",
      "team": "platform"
    }
  }
]
```

Caso d'uso tipico: integrazione con tool di provisioning (Ansible, Terraform, Puppet) che generano i file di target automaticamente.

#### consul_sd_configs

Integrazione nativa con HashiCorp Consul per la service discovery.

```yaml
scrape_configs:
  - job_name: 'consul-services'
    consul_sd_configs:
      - server: 'consul.example.com:8500'
        services: []  # vuoto = tutti i servizi
        tags:
          - 'monitoring'
        # Opzionale: autenticazione
        token: '${CONSUL_TOKEN}'
    relabel_configs:
      # Usa il nome del servizio Consul come job
      - source_labels: [__meta_consul_service]
        target_label: job
      # Aggiungi il datacenter come label
      - source_labels: [__meta_consul_dc]
        target_label: datacenter
      # Filtra solo servizi con tag "metrics"
      - source_labels: [__meta_consul_tags]
        regex: '.*,metrics,.*'
        action: keep
```

#### kubernetes_sd_configs

La service discovery Kubernetes è la più complessa e la più potente. Supporta diversi ruoli di scoperta.

```yaml
scrape_configs:
  # Scoperta basata su Pod
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      # Scrape solo pod con annotation prometheus.io/scrape=true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        regex: 'true'
        action: keep
      # Usa la porta dall'annotation prometheus.io/port
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
        regex: '(\d+)'
        target_label: __address__
        replacement: '${1}'
        action: replace
      # Path delle metriche dall'annotation
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        target_label: __metrics_path__
        regex: '(.+)'
      # Namespace come label
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      # Nome del pod come label
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod

  # Scoperta basata su Endpoints (per Service)
  - job_name: 'kubernetes-services'
    kubernetes_sd_configs:
      - role: endpoints
    relabel_configs:
      - source_labels:
          [__meta_kubernetes_service_annotation_prometheus_io_scrape]
        regex: 'true'
        action: keep
      - source_labels: [__meta_kubernetes_service_name]
        target_label: service
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace

  # Scoperta dei nodi del cluster
  - job_name: 'kubernetes-nodes'
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
```

Ruoli disponibili per `kubernetes_sd_configs`:

| Ruolo | Scopre | Caso d'uso |
|-------|--------|------------|
| `node` | Nodi del cluster | kubelet, node_exporter |
| `pod` | Pod | Applicazioni con endpoint /metrics |
| `service` | Servizi | Blackbox probing |
| `endpoints` | Endpoint di servizi | Servizi con annotation |
| `endpointslice` | EndpointSlice | Cluster grandi (>1000 endpoint) |
| `ingress` | Ingress | Probing URL esterne |

#### ec2_sd_configs

Service discovery per istanze AWS EC2.

```yaml
scrape_configs:
  - job_name: 'ec2-instances'
    ec2_sd_configs:
      - region: eu-west-1
        port: 9100
        filters:
          - name: tag:Environment
            values: [production, staging]
          - name: instance-state-name
            values: [running]
    relabel_configs:
      - source_labels: [__meta_ec2_tag_Name]
        target_label: instance_name
      - source_labels: [__meta_ec2_tag_Environment]
        target_label: environment
      - source_labels: [__meta_ec2_instance_type]
        target_label: instance_type
      - source_labels: [__meta_ec2_availability_zone]
        target_label: az
```

### Relabeling: relabel_configs vs metric_relabel_configs

Il relabeling è il meccanismo più potente e allo stesso tempo più confuso di Prometheus. È fondamentale capire la differenza tra le due fasi di relabeling.

```
                    relabel_configs              metric_relabel_configs
                    (PRIMA dello scrape)          (DOPO lo scrape)

Target discovery    ──► relabel_configs ──► scrape ──► metric_relabel_configs ──► TSDB
                        │                              │
                        ├─ Modifica __address__         ├─ Drop metriche inutili
                        ├─ Aggiungi label al target     ├─ Rinomina metriche
                        ├─ Filtra target (keep/drop)    ├─ Filtra label
                        └─ Imposta __metrics_path__     └─ Modifica valori label
```

#### Azioni di Relabeling

| Azione | Effetto | Fase tipica |
|--------|---------|-------------|
| `keep` | Mantieni solo target/metriche che matchano | entrambe |
| `drop` | Scarta target/metriche che matchano | entrambe |
| `replace` | Sostituisci valore di una label | entrambe |
| `labelmap` | Copia label che matchano un pattern | relabel_configs |
| `labeldrop` | Rimuovi label che matchano un pattern | metric_relabel_configs |
| `labelkeep` | Mantieni solo label che matchano | metric_relabel_configs |
| `hashmod` | Calcola hash per sharding | relabel_configs |

#### Esempi Pratici di Relabeling

```yaml
# ESEMPIO 1: Drop metriche ad alta cardinalità che non servono
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'go_.*'
    action: drop

# ESEMPIO 2: Rinomina una metrica
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'old_metric_name'
    target_label: __name__
    replacement: 'new_metric_name'

# ESEMPIO 3: Estrai informazioni da una label composta
# Da: label "endpoint" = "https://api.example.com:443/v2/health"
# A:  label "scheme" = "https", "host" = "api.example.com"
relabel_configs:
  - source_labels: [__address__]
    regex: '(.+):(\d+)'
    target_label: __address__
    replacement: '${1}:${2}'

# ESEMPIO 4: Hashmod per sharding orizzontale di Prometheus
# Distribuisce i target su N istanze Prometheus
relabel_configs:
  - source_labels: [__address__]
    modulus: 3            # 3 istanze Prometheus
    target_label: __tmp_hash
    action: hashmod
  - source_labels: [__tmp_hash]
    regex: '0'            # Questa istanza processa solo hash=0
    action: keep
```

---

## Installazione e Configurazione Prometheus

### Installazione

```bash
# Crea utente di sistema
sudo useradd --no-create-home --shell /bin/false prometheus

# Download (verificare ultima versione su github.com/prometheus/prometheus/releases)
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.51.0/prometheus-2.51.0.linux-amd64.tar.gz
tar xzf prometheus-2.51.0.linux-amd64.tar.gz

# Installa binari
sudo cp prometheus-2.51.0.linux-amd64/prometheus /usr/local/bin/
sudo cp prometheus-2.51.0.linux-amd64/promtool /usr/local/bin/
sudo chown prometheus:prometheus /usr/local/bin/{prometheus,promtool}

# Crea directory
sudo mkdir -p /etc/prometheus /var/lib/prometheus
sudo cp -r prometheus-2.51.0.linux-amd64/consoles /etc/prometheus/
sudo cp -r prometheus-2.51.0.linux-amd64/console_libraries /etc/prometheus/
sudo chown -R prometheus:prometheus /etc/prometheus /var/lib/prometheus
```

### Configurazione

```yaml
# /etc/prometheus/prometheus.yml

global:
  scrape_interval: 15s          # Frequenza di scrape default
  evaluation_interval: 15s       # Frequenza di valutazione regole
  scrape_timeout: 10s

  # Label aggiunte a tutte le metriche e alert
  external_labels:
    environment: 'production'
    datacenter: 'eu-west-1'

# Regole di recording e alerting
rule_files:
  - "rules/*.yml"

# Configurazione Alertmanager
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'localhost:9093'

# Configurazione degli scrape target
scrape_configs:
  # Prometheus monitora sé stesso
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node exporter su tutti i server
  - job_name: 'node'
    scrape_interval: 10s
    static_configs:
      - targets:
          - 'web01:9100'
          - 'web02:9100'
          - 'db01:9100'
          - 'db02:9100'
        labels:
          group: 'production'
      - targets:
          - 'staging01:9100'
        labels:
          group: 'staging'

  # Blackbox exporter — probe HTTP
  - job_name: 'blackbox-http'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - 'https://example.com'
          - 'https://api.example.com/health'
          - 'https://app.example.com'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: 'localhost:9115'  # Blackbox exporter address

  # Applicazione con metriche native
  - job_name: 'myapp'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['app01:8080', 'app02:8080']

  # Service discovery per Docker
  - job_name: 'docker'
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
    relabel_configs:
      - source_labels: [__meta_docker_container_label_prometheus_scrape]
        regex: 'true'
        action: keep
      - source_labels: [__meta_docker_container_name]
        target_label: container_name
```

### Systemd Service

```ini
# /etc/systemd/system/prometheus.service
[Unit]
Description=Prometheus Monitoring System
Documentation=https://prometheus.io/docs/
After=network-online.target
Wants=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/var/lib/prometheus/ \
    --storage.tsdb.retention.time=30d \
    --storage.tsdb.retention.size=50GB \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries \
    --web.enable-lifecycle \
    --web.enable-admin-api

ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now prometheus

# Verifica
curl http://localhost:9090/-/healthy
# Prometheus Server is Healthy.

# Valida configurazione
promtool check config /etc/prometheus/prometheus.yml
```

---

## PromQL: Linguaggio di Query

PromQL è il linguaggio di query di Prometheus. È potente ma ha una curva di apprendimento.

### Selettori

```promql
# Selettore semplice — tutte le time series con questo nome
node_cpu_seconds_total

# Con label filter
node_cpu_seconds_total{mode="idle"}
node_cpu_seconds_total{mode!="idle"}              # non uguale
node_cpu_seconds_total{mode=~"user|system"}       # regex match
node_cpu_seconds_total{mode!~"idle|iowait"}       # regex non match
node_cpu_seconds_total{instance="web01:9100", mode="idle"}
```

### Range Vector e Funzioni

```promql
# Range vector — ultimi 5 minuti di dati
node_cpu_seconds_total{mode="idle"}[5m]

# Rate — tasso di crescita per secondo di un counter
rate(node_cpu_seconds_total{mode="idle"}[5m])

# irate — rate istantaneo (ultimi 2 datapoint)
irate(node_cpu_seconds_total{mode="idle"}[5m])

# increase — incremento assoluto in un periodo
increase(http_requests_total[1h])  # richieste nell'ultima ora

# Aggregazioni
sum(rate(node_cpu_seconds_total{mode!="idle"}[5m])) by (instance)
avg(node_memory_MemAvailable_bytes) by (instance)
max(node_filesystem_avail_bytes) by (instance, mountpoint)
count(up == 1)
topk(5, rate(http_requests_total[5m]))
```

### Query Utili

```promql
# CPU usage per istanza (%)
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Memoria utilizzata (%)
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# Spazio disco utilizzato (%)
(1 - node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes) * 100

# Request rate per secondo
sum(rate(http_requests_total[5m])) by (method, status)

# Latenza p99 da histogram
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Latenza p50 (mediana)
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# Error rate (%)
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m])) * 100

# Predizione: disco pieno in X ore
predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[1h], 24*3600) < 0
# True se il disco sarà pieno entro 24 ore al tasso attuale

# Network traffic
rate(node_network_receive_bytes_total{device!="lo"}[5m]) * 8  # bit/s
rate(node_network_transmit_bytes_total{device!="lo"}[5m]) * 8
```

### Instant Vector vs Range Vector

Comprendere la differenza tra instant vector e range vector è fondamentale per scrivere query PromQL corrette.

> Riferimento: https://prometheus.io/docs/prometheus/latest/querying/basics/#expression-language-data-types (consultato: 2026-05-23)

Un **instant vector** è un set di time series con un singolo campione per ogni serie, tutti allo stesso timestamp. Un **range vector** è un set di time series con una sequenza di campioni per ogni serie, coprendo un intervallo temporale.

```promql
# Instant vector: un valore per serie al timestamp corrente
node_cpu_seconds_total{mode="idle"}
# Risultato: {cpu="0",mode="idle",instance="web01:9100"} 54321.5

# Range vector: multipli valori per serie nell'intervallo [5m]
node_cpu_seconds_total{mode="idle"}[5m]
# Risultato: {cpu="0",mode="idle",instance="web01:9100"}
#   54300.0 @1716422100
#   54305.0 @1716422115
#   54310.0 @1716422130
#   ...
```

Regole chiave:
- I range vector **non possono** essere graficati direttamente — servono come input a funzioni come `rate()`, `increase()`, `avg_over_time()`
- Le funzioni di aggregazione (`sum`, `avg`, `max`, `min`) operano su instant vector
- Le funzioni `*_over_time` convertono range vector in instant vector

```promql
# Funzioni _over_time: convertono range vector → instant vector
avg_over_time(node_cpu_seconds_total{mode="idle"}[1h])    # media nell'ultima ora
max_over_time(node_memory_MemFree_bytes[24h])             # massimo nelle 24 ore
min_over_time(node_filesystem_avail_bytes[7d])             # minimo nella settimana
quantile_over_time(0.95, http_request_duration_seconds[1h]) # 95mo percentile
count_over_time(up[1h])                                    # numero campioni nell'ora
```

### rate vs irate vs increase

Queste tre funzioni operano su counter (valori monotonicamente crescenti) e sono spesso confuse tra loro.

| Funzione | Calcolo | Uso consigliato |
|----------|---------|-----------------|
| `rate()` | Media del tasso di crescita per secondo nell'intero range | Dashboard, alerting, recording rules |
| `irate()` | Tasso istantaneo basato sugli ultimi 2 campioni del range | Grafici ad alta risoluzione temporanea |
| `increase()` | Incremento totale nel range (= `rate() * secondi_nel_range`) | "Quante richieste nell'ultima ora?" |

```promql
# rate: media ponderata su tutto il range — smussata, stabile
# Ideale per alert e recording rules
rate(http_requests_total[5m])

# irate: guarda solo gli ultimi 2 punti — picchi visibili ma rumorosa
# Ideale solo per grafici real-time, MAI per alerting
irate(http_requests_total[5m])

# increase: quante richieste totali nel periodo
# Equivalente a rate() * secondi, ma con gestione counter reset
increase(http_requests_total[1h])  # ≈ rate(http_requests_total[1h]) * 3600
```

**Attenzione ai counter reset**: tutte e tre le funzioni gestiscono automaticamente i counter reset (quando un processo si riavvia e il counter riparte da 0). Prometheus rileva il reset e compensa nel calcolo.

**Errore comune**: usare `irate()` in alerting rules. Poiché `irate()` è sensibile solo agli ultimi 2 campioni, un singolo scrape anomalo può far scattare l'alert. Usare sempre `rate()` per gli alert.

### histogram_quantile in Profondità

`histogram_quantile()` calcola il quantile approssimato da un histogram. È la funzione più potente e allo stesso tempo più incompresa di PromQL.

> Riferimento: https://prometheus.io/docs/practices/histograms/ (consultato: 2026-05-23)

```promql
# Struttura di un histogram con bucket
# http_request_duration_seconds_bucket{le="0.005"} 24054
# http_request_duration_seconds_bucket{le="0.01"}  33444
# http_request_duration_seconds_bucket{le="0.025"} 100392
# http_request_duration_seconds_bucket{le="0.05"}  129389
# http_request_duration_seconds_bucket{le="0.1"}   133988
# http_request_duration_seconds_bucket{le="+Inf"}  144320
# http_request_duration_seconds_sum                 53423.4
# http_request_duration_seconds_count               144320
```

Come funziona internamente:
1. `histogram_quantile()` riceve i bucket cumulativi
2. Identifica il bucket che contiene il quantile desiderato
3. Interpola linearmente all'interno di quel bucket
4. La label `le` (less-than-or-equal) **deve** essere preservata nell'aggregazione

```promql
# CORRETTO: mantieni le nell'aggregazione
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le))

# CORRETTO: per istanza, mantieni sia instance che le
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le, instance))

# SBAGLIATO: le manca nell'aggregazione — errore
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (instance))
# Restituisce NaN perché non ha i bucket
```

Scelta dei bucket: i bucket di default (`{.005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10}`) sono adatti per la latenza HTTP. Per altre distribuzioni, personalizzare i bucket:

```go
// Go client: bucket personalizzati
prometheus.NewHistogramVec(prometheus.HistogramOpts{
    Name:    "batch_processing_duration_seconds",
    Help:    "Tempo di elaborazione batch",
    Buckets: []float64{1, 5, 10, 30, 60, 120, 300, 600},
}, []string{"job_type"})
```

### Operatori di Aggregazione: by e without

Gli operatori `by` e `without` controllano quali label mantenere o escludere nell'aggregazione.

```promql
# by: mantieni SOLO le label specificate, aggrega il resto
sum(rate(http_requests_total[5m])) by (method, status)
# Risultato: {method="GET", status="200"} 150
#            {method="POST", status="201"} 30

# without: aggrega rimuovendo SOLO le label specificate, mantieni il resto
sum(rate(http_requests_total[5m])) without (instance, pod)
# Risultato: mantiene method, status, job, namespace, ...
#            rimuove instance e pod

# Regola pratica:
#   - by   → quando vuoi poche label nel risultato
#   - without → quando vuoi rimuovere poche label specifiche
```

Operatori di aggregazione completi:

| Operatore | Descrizione |
|-----------|-------------|
| `sum` | Somma dei valori |
| `min` | Valore minimo |
| `max` | Valore massimo |
| `avg` | Media |
| `stddev` | Deviazione standard |
| `stdvar` | Varianza |
| `count` | Conteggio delle serie |
| `count_values` | Conteggio per valore distinto |
| `group` | Raggruppa serie (valore = 1) |
| `topk` | Top K serie per valore |
| `bottomk` | Bottom K serie per valore |
| `quantile` | Quantile tra le serie |

### Subquery

Le subquery permettono di applicare funzioni su range vector calcolati da instant vector. Utili quando si vuole un range di un'espressione complessa.

> Riferimento: https://prometheus.io/docs/prometheus/latest/querying/basics/#subquery (consultato: 2026-05-23)

```promql
# Sintassi: <instant_query>[<range>:<resolution>]

# Massimo del rate di CPU negli ultimi 30 minuti, calcolato ogni minuto
max_over_time(
  rate(node_cpu_seconds_total{mode="idle"}[5m])[30m:1m]
)

# Media del rate di errori nell'ultima ora, campionata ogni 5 minuti
avg_over_time(
  sum(rate(http_requests_total{status=~"5.."}[5m]))[1h:5m]
)

# Deviazione standard della latenza p99 nelle ultime 24 ore
stddev_over_time(
  histogram_quantile(0.99,
    sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
  )[24h:5m]
)
```

Se la risoluzione (`:1m`, `:5m`) viene omessa, Prometheus usa l'`evaluation_interval` globale.

### Anti-Pattern PromQL

Errori comuni da evitare per query corrette e performanti.

#### 1. rate() su Gauge

```promql
# SBAGLIATO: rate su gauge non ha senso semantico
rate(node_memory_MemFree_bytes[5m])
# Un gauge può scendere, rate potrebbe dare valori negativi insensati

# CORRETTO: per la variazione di un gauge, usare deriv() o delta()
deriv(node_memory_MemFree_bytes[5m])   # derivata (tasso di cambiamento)
delta(node_memory_MemFree_bytes[1h])    # differenza assoluta
```

#### 2. Range troppo corto per rate()

```promql
# SBAGLIATO: range < 2 * scrape_interval → dati insufficienti
rate(http_requests_total[15s])  # con scrape_interval 15s

# CORRETTO: range >= 4 * scrape_interval per tollerare uno scrape mancato
rate(http_requests_total[1m])   # con scrape_interval 15s
# Regola empirica: range = 4 × scrape_interval
```

#### 3. Aggregazione senza contesto

```promql
# PERICOLOSO: sum globale senza by/without
sum(rate(http_requests_total[5m]))
# Aggrega tutto — perde visibilità su quale servizio genera traffico

# MEGLIO: aggregare con contesto
sum(rate(http_requests_total[5m])) by (job, method)
```

#### 4. Label matching implicito in operazioni binarie

```promql
# SBAGLIATO: le label non matchano → risultato vuoto
node_memory_MemFree_bytes / node_memory_MemTotal_bytes
# Funziona solo se TUTTE le label sono identiche tra le due serie

# CORRETTO: usa on() o ignoring() per controllare il matching
node_memory_MemFree_bytes / ignoring(job) node_memory_MemTotal_bytes
# oppure
node_memory_MemFree_bytes / on(instance) node_memory_MemTotal_bytes
```

#### 5. Usare count per verificare assenza di serie

```promql
# SBAGLIATO: count su serie inesistente restituisce "empty", non 0
count(nonexistent_metric) == 0  # non funziona

# CORRETTO: usare absent()
absent(up{job="myapp"})  # restituisce 1 se la serie non esiste
```

---

## Recording Rules

Le recording rules pre-calcolano query PromQL complesse e le salvano come nuove time series. Utili per dashboard che usano la stessa query costosa ripetutamente.

```yaml
# /etc/prometheus/rules/recording.yml

groups:
  - name: node_recording_rules
    interval: 15s
    rules:
      # CPU usage pre-calcolato
      - record: instance:node_cpu_utilisation:rate5m
        expr: |
          100 - (avg by (instance)
            (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

      # Memoria utilizzata pre-calcolata
      - record: instance:node_memory_utilisation:ratio
        expr: |
          1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes

      # Disco utilizzato pre-calcolato
      - record: instance:node_filesystem_utilisation:ratio
        expr: |
          1 - node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} /
              node_filesystem_size_bytes{fstype!~"tmpfs|overlay"}

  - name: http_recording_rules
    interval: 15s
    rules:
      # Request rate totale
      - record: job:http_requests:rate5m
        expr: sum(rate(http_requests_total[5m])) by (job)

      # Error rate
      - record: job:http_requests:error_rate5m
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) by (job) /
          sum(rate(http_requests_total[5m])) by (job)

      # Latenza p99
      - record: job:http_request_duration:p99
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (job, le))
```

```bash
# Valida le regole
promtool check rules /etc/prometheus/rules/recording.yml

# Reload Prometheus (con --web.enable-lifecycle)
curl -X POST http://localhost:9090/-/reload
```

### Convenzioni di Naming per Recording Rules

> Riferimento: https://prometheus.io/docs/practices/rules/ (consultato: 2026-05-23)

La convenzione ufficiale Prometheus per i nomi delle recording rules segue il formato:

```
level:metric:operations
```

| Componente | Significato | Esempi |
|------------|-------------|--------|
| `level` | Le label di aggregazione | `instance`, `job`, `cluster` |
| `metric` | Il nome della metrica originale | `node_cpu`, `http_requests` |
| `operations` | Le operazioni applicate (in ordine) | `rate5m`, `ratio`, `total` |

```yaml
# Esempi corretti:
- record: instance:node_cpu_utilisation:rate5m
  # level=instance, metric=node_cpu_utilisation, op=rate5m

- record: job:http_requests_total:rate5m
  # level=job, metric=http_requests_total, op=rate5m

- record: cluster:namespace:http_requests:error_rate5m
  # level=cluster:namespace, metric=http_requests, op=error_rate5m

# Nomi da EVITARE:
# cpu_usage_average     ← non segue la convenzione
# my_custom_rule_1      ← nome opaco, non descrive il contenuto
# ALERT_high_cpu        ← confonde recording rules con alerting rules
```

### Recording Rules e Performance

Le recording rules devono essere usate con criterio. Non ogni query merita una recording rule.

**Quando creare una recording rule:**
- La query è usata in 3+ dashboard o alert
- La query richiede > 1 secondo di esecuzione
- La query aggrega centinaia di serie
- La query usa `histogram_quantile` su histogram ad alta cardinalità
- La query è usata in cascata (una recording rule ne alimenta un'altra)

**Quando NON creare una recording rule:**
- La query è semplice e veloce (selettore diretto con poche serie)
- La query è usata in un singolo pannello di una singola dashboard
- La cardinalità risultante è alta (molte combinazioni di label)

```yaml
# Pattern a cascata: recording rules che alimentano altre recording rules
groups:
  - name: http_slo_recording
    rules:
      # Livello 1: rate per instance
      - record: instance:http_requests_total:rate5m
        expr: sum(rate(http_requests_total[5m])) by (instance, job)

      # Livello 2: aggregazione per job (usa il livello 1)
      - record: job:http_requests_total:rate5m
        expr: sum(instance:http_requests_total:rate5m) by (job)

      # Livello 3: error budget (usa il livello 2)
      - record: job:http_requests:availability5m
        expr: |
          1 - (
            sum(rate(http_requests_total{status=~"5.."}[5m])) by (job) /
            job:http_requests_total:rate5m
          )
```

---

## Alerting Rules e Alertmanager

### Alerting Rules

```yaml
# /etc/prometheus/rules/alerts.yml

groups:
  - name: node_alerts
    rules:
      # CPU alta per più di 5 minuti
      - alert: HighCPUUsage
        expr: instance:node_cpu_utilisation:rate5m > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU alta su {{ $labels.instance }}"
          description: "CPU al {{ $value | printf \"%.1f\" }}% su {{ $labels.instance }} da 5 minuti."

      # CPU critica
      - alert: CriticalCPUUsage
        expr: instance:node_cpu_utilisation:rate5m > 95
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "CPU critica su {{ $labels.instance }}"
          description: "CPU al {{ $value | printf \"%.1f\" }}% da 2 minuti."

      # Memoria quasi esaurita
      - alert: HighMemoryUsage
        expr: instance:node_memory_utilisation:ratio > 0.90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memoria alta su {{ $labels.instance }}"
          description: "Memoria utilizzata al {{ $value | humanizePercentage }} su {{ $labels.instance }}."

      # Disco quasi pieno
      - alert: DiskSpaceLow
        expr: instance:node_filesystem_utilisation:ratio > 0.85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Disco quasi pieno su {{ $labels.instance }}:{{ $labels.mountpoint }}"
          description: "Disco utilizzato al {{ $value | humanizePercentage }}."

      # Disco pieno predetto in 24h
      - alert: DiskWillFillIn24h
        expr: predict_linear(node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"}[6h], 24*3600) < 0
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Disco si riempirà entro 24 ore su {{ $labels.instance }}"

      # Target down
      - alert: TargetDown
        expr: up == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Target {{ $labels.instance }} non raggiungibile"
          description: "Il target {{ $labels.job }}/{{ $labels.instance }} non risponde."

  - name: http_alerts
    rules:
      # Error rate alto
      - alert: HighErrorRate
        expr: job:http_requests:error_rate5m > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate alto per {{ $labels.job }}"
          description: "Error rate al {{ $value | humanizePercentage }} (soglia: 5%)."

      # Latenza alta
      - alert: HighLatency
        expr: job:http_request_duration:p99 > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Latenza p99 alta per {{ $labels.job }}"
          description: "Latenza p99 a {{ $value | printf \"%.2f\" }}s."
```

### Alertmanager

```bash
# Installazione
cd /tmp
wget https://github.com/prometheus/alertmanager/releases/download/v0.27.0/alertmanager-0.27.0.linux-amd64.tar.gz
tar xzf alertmanager-0.27.0.linux-amd64.tar.gz
sudo cp alertmanager-0.27.0.linux-amd64/alertmanager /usr/local/bin/
sudo cp alertmanager-0.27.0.linux-amd64/amtool /usr/local/bin/
sudo mkdir -p /etc/alertmanager /var/lib/alertmanager
```

```yaml
# /etc/alertmanager/alertmanager.yml

global:
  resolve_timeout: 5m
  smtp_from: 'alerts@example.com'
  smtp_smarthost: 'smtp.example.com:587'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'smtp_password'
  smtp_require_tls: true

# Inibizione: sopprime alert meno gravi se esiste un alert più grave
inhibit_rules:
  - source_matchers:
      - severity="critical"
    target_matchers:
      - severity="warning"
    equal: ['instance']  # stesso target

# Routing: dirige gli alert ai receiver corretti
route:
  receiver: 'default-email'
  group_by: ['alertname', 'instance']
  group_wait: 30s         # attesa prima di inviare il primo alert del gruppo
  group_interval: 5m      # intervallo tra notifiche dello stesso gruppo
  repeat_interval: 4h     # ripeti alert non risolto

  routes:
    # Critical → Slack + email + PagerDuty
    - matchers:
        - severity="critical"
      receiver: 'critical-multi'
      continue: false

    # Warning → solo email
    - matchers:
        - severity="warning"
      receiver: 'warning-email'
      group_wait: 1m
      repeat_interval: 12h

# Receiver definitions
receivers:
  - name: 'default-email'
    email_configs:
      - to: 'ops@example.com'

  - name: 'warning-email'
    email_configs:
      - to: 'ops@example.com'
        send_resolved: true

  - name: 'critical-multi'
    email_configs:
      - to: 'ops-urgent@example.com'
        send_resolved: true
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/xxx/yyy/zzz'
        channel: '#alerts-critical'
        title: '{{ .GroupLabels.alertname }}'
        text: >-
          {{ range .Alerts }}
          *{{ .Labels.instance }}*: {{ .Annotations.description }}
          {{ end }}
        send_resolved: true
    pagerduty_configs:
      - service_key: 'pagerduty_integration_key'
        severity: '{{ if eq .GroupLabels.severity "critical" }}critical{{ else }}warning{{ end }}'
```

```ini
# /etc/systemd/system/alertmanager.service
[Unit]
Description=Alertmanager
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/alertmanager \
    --config.file=/etc/alertmanager/alertmanager.yml \
    --storage.path=/var/lib/alertmanager/
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Validazione
amtool check-config /etc/alertmanager/alertmanager.yml

# Gestione silenziamenti
amtool silence add alertname="HighCPUUsage" instance="web01:9100" \
    --duration=2h --comment="Manutenzione pianificata"

# Lista alert attivi
amtool alert
```

### Architettura Alertmanager Deep Dive

> Riferimento: https://prometheus.io/docs/alerting/latest/alertmanager/ (consultato: 2026-05-23)

Alertmanager non è un semplice relay di notifiche. È un sistema sofisticato con pipeline di elaborazione degli alert.

```
Pipeline Alertmanager:

  Alert da Prometheus
       │
       ▼
  ┌─────────────┐
  │ Dispatcher  │ ← Riceve alert via API POST /api/v2/alerts
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Router      │ ← Matcha alert contro l'albero di routing
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Inhibitor   │ ← Sopprime alert inibiti da alert di severity superiore
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Silencer    │ ← Sopprime alert matchati da silence attivi
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Grouper     │ ← Raggruppa alert con stesse label (group_by)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Notifier    │ ← Invia a uno o più receiver (email, Slack, webhook...)
  └─────────────┘
```

**High Availability**: Alertmanager supporta clustering nativo. Più istanze comunicano via gossip protocol (porta 9094) e deduplicano le notifiche.

```bash
# Cluster di 3 Alertmanager
alertmanager --config.file=alertmanager.yml \
    --cluster.listen-address=0.0.0.0:9094 \
    --cluster.peer=am2:9094 \
    --cluster.peer=am3:9094
```

### Routing Tree in Dettaglio

L'albero di routing di Alertmanager è valutato top-down. Ogni alert viene matchato dalla prima route che corrisponde, a meno che `continue: true` non sia specificato.

```yaml
# Albero di routing avanzato
route:
  receiver: 'catch-all'
  group_by: ['alertname', 'cluster']
  routes:
    # Infrastruttura → team platform
    - matchers:
        - team="platform"
      receiver: 'platform-slack'
      routes:
        # Infrastruttura critica → anche PagerDuty
        - matchers:
            - severity="critical"
          receiver: 'platform-pagerduty'

    # Applicazione → team dev
    - matchers:
        - team="application"
      receiver: 'dev-slack'
      group_by: ['alertname', 'service']
      routes:
        - matchers:
            - severity="critical"
          receiver: 'dev-pagerduty'

    # Database → DBA
    - matchers:
        - component=~"postgres|mysql|redis"
      receiver: 'dba-email'
      group_wait: 10s
      routes:
        - matchers:
            - severity="critical"
          receiver: 'dba-pagerduty'

    # Security → team security (sempre, con continue per notificare anche il team owner)
    - matchers:
        - category="security"
      receiver: 'security-team'
      continue: true  # ← continua a valutare le route successive
```

### Grouping, Inhibition, Silencing Avanzati

#### Grouping Avanzato

Il grouping controlla come gli alert vengono raggruppati prima della notifica. Alert con le stesse label specificate in `group_by` vengono raggruppati in una singola notifica.

```yaml
# Scenario: 100 pod dello stesso servizio vanno in errore
# Senza grouping → 100 notifiche separate
# Con grouping → 1 notifica con 100 alert

route:
  group_by: ['alertname', 'service', 'namespace']
  group_wait: 30s       # Attendi 30s per raccogliere alert correlati
  group_interval: 5m    # Nuove notifiche per lo stesso gruppo ogni 5 min
  repeat_interval: 4h   # Ripeti alert irrisolti ogni 4 ore
```

`group_by: ['...']` — un singolo valore `'...'` (tre punti letterali) significa "raggruppa tutti gli alert in un singolo gruppo" — utile per ambienti con pochissimi alert.

#### Inhibition Avanzata

```yaml
inhibit_rules:
  # Se il cluster è down, non notificare alert dei singoli nodi
  - source_matchers:
      - alertname="ClusterDown"
    target_matchers:
      - alertname=~"Node.*"
    equal: ['cluster']

  # Se il database è down, non notificare alert applicativi
  - source_matchers:
      - alertname="DatabaseDown"
      - severity="critical"
    target_matchers:
      - component="application"
      - severity=~"warning|info"
    equal: ['environment']

  # Inibizione gerarchica di severity
  - source_matchers:
      - severity="critical"
    target_matchers:
      - severity="warning"
    equal: ['alertname', 'instance']
```

#### Silencing Programmatico

```bash
# Crea un silence con scadenza
amtool silence add \
    alertname="HighCPUUsage" \
    instance=~"web0[1-3]:9100" \
    --duration=4h \
    --author="renan" \
    --comment="Manutenzione pianificata server web 2026-05-23"

# Elenca silence attivi
amtool silence query

# Rimuovi un silence specifico
amtool silence expire <silence-id>

# Silence via API (utile nei pipeline CI/CD)
curl -X POST http://localhost:9093/api/v2/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {"name": "alertname", "value": "HighCPUUsage", "isRegex": false},
      {"name": "instance", "value": "web01:9100", "isRegex": false}
    ],
    "startsAt": "2026-05-23T22:00:00Z",
    "endsAt": "2026-05-24T02:00:00Z",
    "createdBy": "deploy-pipeline",
    "comment": "Deploy window"
  }'
```

### Integrazione Webhook

L'integrazione webhook è la più flessibile — permette di connettere Alertmanager a qualsiasi sistema.

```yaml
# alertmanager.yml — receiver webhook
receivers:
  - name: 'custom-webhook'
    webhook_configs:
      - url: 'https://hooks.internal.example.com/alertmanager'
        send_resolved: true
        max_alerts: 0  # 0 = illimitato
        http_config:
          bearer_token_file: '/etc/alertmanager/webhook-token'
          tls_config:
            ca_file: '/etc/ssl/certs/internal-ca.pem'
```

Payload JSON inviato dal webhook:

```json
{
  "version": "4",
  "groupKey": "{}:{alertname=\"HighCPUUsage\"}",
  "truncatedAlerts": 0,
  "status": "firing",
  "receiver": "custom-webhook",
  "groupLabels": {"alertname": "HighCPUUsage"},
  "commonLabels": {"alertname": "HighCPUUsage", "severity": "warning"},
  "commonAnnotations": {"summary": "CPU alta"},
  "externalURL": "http://alertmanager:9093",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "HighCPUUsage",
        "instance": "web01:9100",
        "severity": "warning"
      },
      "annotations": {
        "summary": "CPU alta su web01:9100",
        "description": "CPU al 92.3% su web01:9100 da 5 minuti."
      },
      "startsAt": "2026-05-23T10:30:00.000Z",
      "endsAt": "0001-01-01T00:00:00Z",
      "generatorURL": "http://prometheus:9090/graph?g0.expr=..."
    }
  ]
}
```

### Prevenzione Alert Fatigue

L'alert fatigue è il problema numero uno dei sistemi di monitoring. Troppi alert portano gli operatori a ignorarli.

**Sintomi dell'alert fatigue:**
- Notifiche disabilitate o mutate dal team
- Alert in stato "firing" per settimane senza azione
- Tempo medio di risposta che si allunga progressivamente
- Incidenti persi perché sepolti tra alert rumorosi

**Strategie di prevenzione:**

1. **Ogni alert deve essere azionabile**: Se un alert non richiede azione umana immediata, non deve esistere come alert. Trasformarlo in una dashboard o in un report periodico.

2. **Classificazione rigorosa delle severity:**
   - `critical` → sveglia qualcuno alle 3 di notte (page)
   - `warning` → deve essere investigato durante l'orario lavorativo (ticket)
   - `info` → solo dashboard, nessuna notifica

3. **Regola del "paging someone"**: Se non pagheresti qualcuno per rispondere a questo alert, non è critical.

4. **Aggregazione temporale**: Usare `for` per evitare alert su spike transitori.

5. **Inibizione appropriata**: Non notificare alert figli se il padre è già firing.

6. **Review periodica**: Ogni trimestre, rivedere tutti gli alert:
   - Alert che non hanno mai fired → eliminarli o abbassare la soglia
   - Alert che firino costantemente → risolvere la causa root o alzare la soglia
   - Alert ignorati dal team → eliminarli

### Alert SLO Multi-Window Multi-Burn-Rate

> Riferimento: Google SRE Workbook, Chapter 5 — Alerting on SLOs (consultato: 2026-05-23)

Gli alert basati su SLO (Service Level Objectives) sono il gold standard per l'alerting moderno. Invece di soglie arbitrarie, si basa l'alert sul consumo dell'error budget.

**Concetti:**
- **SLO**: "Il 99.9% delle richieste deve avere successo" → error budget = 0.1%
- **Burn rate**: Velocità con cui si sta consumando l'error budget. Burn rate = 1 → si consuma l'intero budget in 30 giorni. Burn rate = 10 → in 3 giorni.
- **Multi-window**: Si usano finestre temporali multiple per bilanciare velocità di detection e sensibilità.

```yaml
# Recording rules per SLO
groups:
  - name: slo_recording_rules
    rules:
      # Error ratio su diverse finestre temporali
      - record: job:slo_errors_per_request:ratio_rate5m
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) by (job)
          /
          sum(rate(http_requests_total[5m])) by (job)

      - record: job:slo_errors_per_request:ratio_rate30m
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[30m])) by (job)
          /
          sum(rate(http_requests_total[30m])) by (job)

      - record: job:slo_errors_per_request:ratio_rate1h
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[1h])) by (job)
          /
          sum(rate(http_requests_total[1h])) by (job)

      - record: job:slo_errors_per_request:ratio_rate6h
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[6h])) by (job)
          /
          sum(rate(http_requests_total[6h])) by (job)

# Alerting rules multi-window multi-burn-rate (SLO 99.9%)
  - name: slo_alerts
    rules:
      # Burn rate 14.4x — finestra 5m/1h
      # Detection: < 2 minuti | Budget consumato se persiste: 100% in 2 giorni
      - alert: SLOErrorBudgetBurnCritical
        expr: |
          (
            job:slo_errors_per_request:ratio_rate5m{job="myapp"} > (14.4 * 0.001)
            and
            job:slo_errors_per_request:ratio_rate1h{job="myapp"} > (14.4 * 0.001)
          )
        for: 2m
        labels:
          severity: critical
          slo: "availability-99.9"
        annotations:
          summary: "SLO error budget si sta esaurendo velocemente per {{ $labels.job }}"
          description: "Burn rate 14.4x — l'error budget verrà consumato in ~2 giorni."

      # Burn rate 6x — finestra 30m/6h
      # Detection: < 15 minuti | Budget consumato: 100% in 5 giorni
      - alert: SLOErrorBudgetBurnHigh
        expr: |
          (
            job:slo_errors_per_request:ratio_rate30m{job="myapp"} > (6 * 0.001)
            and
            job:slo_errors_per_request:ratio_rate6h{job="myapp"} > (6 * 0.001)
          )
        for: 15m
        labels:
          severity: warning
          slo: "availability-99.9"
        annotations:
          summary: "SLO error budget in erosione per {{ $labels.job }}"
          description: "Burn rate 6x — l'error budget verrà consumato in ~5 giorni."
```

---

## Exporter: node_exporter e blackbox_exporter

### node_exporter

```bash
# Installazione
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xzf node_exporter-1.7.0.linux-amd64.tar.gz
sudo cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
```

```ini
# /etc/systemd/system/node_exporter.service
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter \
    --collector.systemd \
    --collector.processes \
    --collector.tcpstat \
    --no-collector.infiniband \
    --no-collector.nfs \
    --no-collector.nfsd \
    --web.listen-address=:9100
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo useradd --no-create-home --shell /bin/false node_exporter
sudo systemctl enable --now node_exporter

# Verifica
curl http://localhost:9100/metrics | head -20
```

### blackbox_exporter

```bash
# Installazione
wget https://github.com/prometheus/blackbox_exporter/releases/download/v0.25.0/blackbox_exporter-0.25.0.linux-amd64.tar.gz
tar xzf blackbox_exporter-0.25.0.linux-amd64.tar.gz
sudo cp blackbox_exporter-0.25.0.linux-amd64/blackbox_exporter /usr/local/bin/
sudo mkdir /etc/blackbox_exporter
```

```yaml
# /etc/blackbox_exporter/config.yml
modules:
  http_2xx:
    prober: http
    timeout: 10s
    http:
      method: GET
      valid_http_versions: ["HTTP/1.1", "HTTP/2.0"]
      valid_status_codes: [200]
      follow_redirects: true
      preferred_ip_protocol: ip4
      tls_config:
        insecure_skip_verify: false

  http_post_2xx:
    prober: http
    http:
      method: POST
      headers:
        Content-Type: application/json

  tcp_connect:
    prober: tcp
    timeout: 5s

  icmp_ping:
    prober: icmp
    timeout: 5s
    icmp:
      preferred_ip_protocol: ip4

  dns_resolve:
    prober: dns
    dns:
      query_name: "example.com"
      query_type: "A"
      transport_protocol: "udp"
```

```bash
sudo systemctl enable --now blackbox_exporter

# Test manuale
curl "http://localhost:9115/probe?target=https://example.com&module=http_2xx"
```

---

## Ecosistema Exporter Avanzato

> Riferimento: https://prometheus.io/docs/instrumenting/exporters/ (consultato: 2026-05-23)

### node_exporter: Metriche Chiave

Le metriche di node_exporter sono centinaia. Queste sono le più importanti per il monitoraggio operativo.

| Metrica | Tipo | Descrizione |
|---------|------|-------------|
| `node_cpu_seconds_total` | Counter | Tempo CPU per modalità (idle, user, system, iowait...) |
| `node_memory_MemTotal_bytes` | Gauge | Memoria RAM totale |
| `node_memory_MemAvailable_bytes` | Gauge | Memoria disponibile (incluso cache reclaimable) |
| `node_memory_Buffers_bytes` | Gauge | Memoria per buffer I/O |
| `node_memory_Cached_bytes` | Gauge | Memoria cache pagine |
| `node_filesystem_size_bytes` | Gauge | Dimensione totale filesystem |
| `node_filesystem_avail_bytes` | Gauge | Spazio disponibile filesystem |
| `node_disk_read_bytes_total` | Counter | Byte letti dal disco |
| `node_disk_written_bytes_total` | Counter | Byte scritti sul disco |
| `node_disk_io_time_seconds_total` | Counter | Tempo speso in I/O |
| `node_network_receive_bytes_total` | Counter | Byte ricevuti dall'interfaccia di rete |
| `node_network_transmit_bytes_total` | Counter | Byte trasmessi dall'interfaccia di rete |
| `node_load1` | Gauge | Load average 1 minuto |
| `node_load5` | Gauge | Load average 5 minuti |
| `node_load15` | Gauge | Load average 15 minuti |
| `node_boot_time_seconds` | Gauge | Timestamp di boot del sistema |
| `node_context_switches_total` | Counter | Context switch del kernel |
| `node_filefd_allocated` | Gauge | File descriptor allocati |
| `node_filefd_maximum` | Gauge | File descriptor massimi |
| `node_entropy_available_bits` | Gauge | Entropia disponibile (importante per crittografia) |

Collector opzionali utili:

```bash
# Abilitare collector aggiuntivi:
--collector.systemd         # stato servizi systemd
--collector.processes       # conteggio processi per stato
--collector.tcpstat         # statistiche connessioni TCP
--collector.textfile        # metriche personalizzate da file
--collector.ethtool         # statistiche schede di rete
```

#### Textfile Collector

Il textfile collector permette di esporre metriche personalizzate tramite file nella directory configurata.

```bash
# Avvia node_exporter con textfile collector
node_exporter --collector.textfile.directory=/var/lib/node_exporter/textfile_collector

# Script cron che genera metriche personalizzate
cat > /var/lib/node_exporter/textfile_collector/backup_status.prom << 'METRICS'
# HELP backup_last_success_timestamp_seconds Timestamp dell'ultimo backup riuscito
# TYPE backup_last_success_timestamp_seconds gauge
backup_last_success_timestamp_seconds{job="db-backup"} 1716422400
# HELP backup_size_bytes Dimensione dell'ultimo backup
# TYPE backup_size_bytes gauge
backup_size_bytes{job="db-backup"} 5368709120
METRICS
```

### mysqld_exporter

```bash
# Installazione
wget https://github.com/prometheus/mysqld_exporter/releases/download/v0.15.1/mysqld_exporter-0.15.1.linux-amd64.tar.gz
tar xzf mysqld_exporter-0.15.1.linux-amd64.tar.gz
sudo cp mysqld_exporter-0.15.1.linux-amd64/mysqld_exporter /usr/local/bin/
```

```sql
-- Crea utente MySQL dedicato al monitoring
CREATE USER 'exporter'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'localhost';
FLUSH PRIVILEGES;
```

```bash
# Configurazione credenziali (file protetto)
cat > /etc/.mysqld_exporter.cnf << 'EOF'
[client]
user=exporter
password=strong_password_here
EOF
chmod 600 /etc/.mysqld_exporter.cnf

# Avvio
mysqld_exporter --config.my-cnf=/etc/.mysqld_exporter.cnf \
    --web.listen-address=:9104 \
    --collect.info_schema.processlist \
    --collect.info_schema.innodb_tablespaces \
    --collect.slave_status
```

Metriche chiave mysqld_exporter:

| Metrica | Significato |
|---------|-------------|
| `mysql_global_status_threads_connected` | Connessioni attive |
| `mysql_global_status_slow_queries` | Query lente (counter) |
| `mysql_global_status_queries` | Query totali (counter) |
| `mysql_global_status_innodb_buffer_pool_reads` | Letture dal disco (miss cache) |
| `mysql_global_status_innodb_buffer_pool_read_requests` | Richieste al buffer pool |
| `mysql_slave_status_seconds_behind_master` | Ritardo replicazione |

### postgres_exporter

```bash
# Installazione
wget https://github.com/prometheus-community/postgres_exporter/releases/download/v0.15.0/postgres_exporter-0.15.0.linux-amd64.tar.gz
tar xzf postgres_exporter-0.15.0.linux-amd64.tar.gz
sudo cp postgres_exporter-0.15.0.linux-amd64/postgres_exporter /usr/local/bin/
```

```sql
-- Crea ruolo PostgreSQL per il monitoring
CREATE ROLE exporter LOGIN PASSWORD 'strong_password_here';
GRANT pg_monitor TO exporter;
```

```bash
# Avvio con variabile d'ambiente
export DATA_SOURCE_NAME="postgresql://exporter:strong_password_here@localhost:5432/postgres?sslmode=disable"
postgres_exporter --web.listen-address=:9187
```

Query personalizzate (per metriche specifiche del proprio schema):

```yaml
# /etc/postgres_exporter/queries.yml
pg_replication:
  query: |
    SELECT CASE WHEN NOT pg_is_in_recovery()
      THEN 0
      ELSE GREATEST(0, EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())))
    END AS lag
  metrics:
    - lag:
        usage: "GAUGE"
        description: "Replication lag in seconds"

pg_database_size:
  query: |
    SELECT pg_database.datname,
           pg_database_size(pg_database.datname) as bytes
    FROM pg_database
    WHERE datistemplate = false
  metrics:
    - datname:
        usage: "LABEL"
        description: "Database name"
    - bytes:
        usage: "GAUGE"
        description: "Database size in bytes"
```

```bash
postgres_exporter --extend.query-path=/etc/postgres_exporter/queries.yml
```

### Exporter Personalizzati (Go e Python)

Quando nessun exporter esistente copre le metriche necessarie, si può creare un exporter personalizzato.

#### Exporter in Python

```python
# custom_exporter.py
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import time
import random

# Definizione metriche
QUEUE_SIZE = Gauge(
    'app_queue_size',
    'Numero di messaggi in coda',
    ['queue_name']
)

PROCESSED_TOTAL = Counter(
    'app_messages_processed_total',
    'Messaggi processati totali',
    ['queue_name', 'status']
)

PROCESSING_TIME = Histogram(
    'app_processing_duration_seconds',
    'Tempo di elaborazione messaggio',
    ['queue_name'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
)

def collect_metrics():
    """Raccoglie metriche dalla propria applicazione."""
    while True:
        # Qui si inserisce la logica di raccolta reale
        # Esempio: query al database, lettura coda, API call
        QUEUE_SIZE.labels(queue_name='orders').set(random.randint(0, 100))
        QUEUE_SIZE.labels(queue_name='notifications').set(random.randint(0, 50))

        PROCESSED_TOTAL.labels(queue_name='orders', status='success').inc()

        with PROCESSING_TIME.labels(queue_name='orders').time():
            time.sleep(random.uniform(0.01, 0.1))  # simula elaborazione

        time.sleep(15)  # intervallo di aggiornamento

if __name__ == '__main__':
    start_http_server(9200)  # endpoint /metrics sulla porta 9200
    collect_metrics()
```

#### Exporter in Go

```go
// main.go
package main

import (
    "log"
    "net/http"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
    activeConnections = prometheus.NewGauge(prometheus.GaugeOpts{
        Name: "app_active_connections",
        Help: "Numero di connessioni attive",
    })

    requestDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "app_request_duration_seconds",
            Help:    "Durata delle richieste in secondi",
            Buckets: prometheus.DefBuckets,
        },
        []string{"method", "endpoint"},
    )
)

func init() {
    prometheus.MustRegister(activeConnections)
    prometheus.MustRegister(requestDuration)
}

func main() {
    http.Handle("/metrics", promhttp.Handler())
    log.Fatal(http.ListenAndServe(":9201", nil))
}
```

### Pushgateway: Casi d'Uso e Anti-Pattern

> Riferimento: https://prometheus.io/docs/practices/pushing/ (consultato: 2026-05-23)

Il Pushgateway è un intermediario che accetta metriche pushate da job batch/effimeri e le espone per lo scrape di Prometheus.

```bash
# Installazione
wget https://github.com/prometheus/pushgateway/releases/download/v1.7.0/pushgateway-1.7.0.linux-amd64.tar.gz
tar xzf pushgateway-1.7.0.linux-amd64.tar.gz
sudo cp pushgateway-1.7.0.linux-amd64/pushgateway /usr/local/bin/

# Avvio
pushgateway --web.listen-address=:9091

# Push di metriche da un job batch
echo 'batch_job_duration_seconds 42.5' | curl --data-binary @- \
    http://localhost:9091/metrics/job/nightly_backup/instance/db01

# Push con metriche multiple
cat <<EOF | curl --data-binary @- \
    http://localhost:9091/metrics/job/data_import/instance/etl01
# TYPE import_rows_total counter
import_rows_total 150000
# TYPE import_duration_seconds gauge
import_duration_seconds 3600
# TYPE import_errors_total counter
import_errors_total 5
EOF

# Elimina metriche di un job specifico
curl -X DELETE http://localhost:9091/metrics/job/nightly_backup/instance/db01
```

**Casi d'uso legittimi:**
- Job batch che partono, eseguono e terminano (cron job, ETL, backup)
- Job con vita breve (secondi) che non possono essere scrapati
- Ambienti dove il target non è raggiungibile (NAT, firewall unidirezionale)

**Anti-pattern (NON usare Pushgateway per):**
- Servizi long-running → usare scrape diretto
- Trasformare il modello push-based in pull-based → snatura l'architettura Prometheus
- Aggregazione metriche da multiple istanze → usare federation o Thanos
- Monitoraggio di servizi con up/down tracking → il Pushgateway non ha il concetto di "target down", le metriche persistono anche se il servizio è morto

---

## Grafana: Installazione e Configurazione

```bash
# Installazione (Debian/Ubuntu)
sudo apt install -y apt-transport-https software-properties-common
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install grafana

# Avvia
sudo systemctl enable --now grafana-server

# Accesso: http://localhost:3000
# Default: admin / admin (cambiarla immediatamente!)
```

### Configurazione

```ini
# /etc/grafana/grafana.ini — parametri chiave

[server]
http_addr = 0.0.0.0
http_port = 3000
root_url = https://grafana.example.com

[security]
admin_user = admin
admin_password = secure_password_here
disable_gravatar = true
cookie_secure = true
cookie_samesite = strict

[auth]
disable_login_form = false

[users]
allow_sign_up = false
auto_assign_org_role = Viewer

[log]
mode = file
level = warn

[alerting]
enabled = true
```

### Data Source Prometheus

```bash
# Via API (automatizzabile)
curl -X POST http://admin:password@localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://localhost:9090",
    "access": "proxy",
    "isDefault": true
  }'
```

---

## Grafana: Dashboard Avanzate

### Variabili di Template

Le variabili rendono le dashboard interattive e riutilizzabili:

```
# Nella configurazione della dashboard → Variables

# Variabile: instance (da Prometheus)
Name: instance
Type: Query
Data source: Prometheus
Query: label_values(up{job="node"}, instance)
Regex: /(.*)/
Multi-value: true
Include All option: true

# Variabile: job
Name: job
Type: Query
Query: label_values(up, job)

# Uso nelle query del pannello:
# rate(node_cpu_seconds_total{instance=~"$instance"}[5m])
```

### Panel JSON per Dashboard Node

```json
{
  "title": "CPU Usage",
  "type": "timeseries",
  "datasource": "Prometheus",
  "targets": [
    {
      "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\", instance=~\"$instance\"}[5m])) * 100)",
      "legendFormat": "{{ instance }}"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "unit": "percent",
      "min": 0,
      "max": 100,
      "thresholds": {
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 70},
          {"color": "red", "value": 90}
        ]
      }
    }
  }
}
```

### Annotations

Le annotations marcano eventi sulle dashboard (deploy, incident, manutenzione):

```bash
# Crea annotation via API
curl -X POST http://admin:password@localhost:3000/api/annotations \
  -H "Content-Type: application/json" \
  -d '{
    "dashboardUID": "abc123",
    "time": 1712000000000,
    "tags": ["deploy", "v2.1.0"],
    "text": "Deploy v2.1.0 in produzione"
  }'

# Da usare nel CI/CD pipeline dopo ogni deploy
```

### Dashboard Raccomandate

Dashboard community pronte all'uso (importabili per ID):

| ID | Nome | Uso |
|-----|------|-----|
| 1860 | Node Exporter Full | Metriche OS dettagliate |
| 3662 | Prometheus Stats | Monitoring di Prometheus stesso |
| 9628 | PostgreSQL Database | Metriche PostgreSQL |
| 12708 | Docker Container | Metriche container |
| 13659 | Blackbox Exporter | Probe HTTP/TCP/ICMP |

```
Grafana UI → + → Import → inserisci ID → Load
```

### Principi di Design delle Dashboard

> Riferimento: https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/best-practices/ (consultato: 2026-05-23)

Una dashboard efficace comunica lo stato del sistema in pochi secondi. Dashboard mal progettate sono peggio di nessuna dashboard.

**Principi fondamentali:**

1. **Una dashboard, un contesto**: Ogni dashboard deve rispondere a una domanda specifica. "Come sta il cluster?" e "Come sta il servizio X?" sono dashboard separate.

2. **Gerarchia visiva**: I pannelli più importanti in alto e a sinistra. Il lettore scansiona come un testo: da sinistra a destra, dall'alto in basso.

3. **Layout consigliato per dashboard di servizio:**
   ```
   ┌──────────────────────────────────────────────────────────────┐
   │ ROW 1: Stat panels (KPI: uptime, error rate, latenza p99)   │
   ├──────────────────────────────────────────────────────────────┤
   │ ROW 2: Time series principali (rate, latenza, errori)        │
   ├──────────────────────────────────────────────────────────────┤
   │ ROW 3: Risorse (CPU, memoria, disco, rete)                   │
   ├──────────────────────────────────────────────────────────────┤
   │ ROW 4: Dettagli (tabelle, log, breakdown per endpoint)       │
   └──────────────────────────────────────────────────────────────┘
   ```

4. **Colori con significato**: Verde = normale, giallo = attenzione, rosso = critico. Non usare colori casuali.

5. **Time range predefinito**: Impostare un range di default sensato (ultima ora per real-time, ultime 24h per overview).

6. **Annotations per correlazione**: Sovrapporre eventi (deploy, incident, change) ai grafici delle metriche.

### Tipi di Panel

| Tipo | Caso d'uso | Query tipica |
|------|-----------|--------------|
| **Time series** | Andamento metriche nel tempo | `rate(http_requests_total[5m])` |
| **Stat** | Valore singolo KPI | `sum(rate(http_requests_total[5m]))` |
| **Gauge** | Valore con threshold (0-100%) | `instance:node_cpu_utilisation:rate5m` |
| **Bar gauge** | Confronto tra istanze | `node_filesystem_avail_bytes` per mountpoint |
| **Table** | Dati tabulari, top-N | `topk(10, rate(http_requests_total[5m]))` |
| **Heatmap** | Distribuzione nel tempo (histogram) | `sum(increase(http_request_duration_seconds_bucket[5m])) by (le)` |
| **Logs** | Log correlati (con Loki) | LogQL query |
| **State timeline** | Stato on/off nel tempo | `up{job="node"}` |
| **Geomap** | Distribuzione geografica | Metriche con label lat/lon |
| **Alert list** | Alert attivi | Nessuna query (automatico) |

### Dashboard-as-Code

Versionare le dashboard come codice è fondamentale per la riproducibilità e il disaster recovery.

#### JSON Model

Ogni dashboard Grafana è un documento JSON. Si può esportare, versionare e importare programmaticamente.

```bash
# Esportare una dashboard
curl -s http://admin:password@localhost:3000/api/dashboards/uid/abc123 | \
    jq '.dashboard' > dashboards/node-overview.json

# Importare una dashboard
curl -X POST http://admin:password@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d '{
    "dashboard": '"$(cat dashboards/node-overview.json)"',
    "overwrite": true,
    "folderId": 0
  }'
```

#### Grafonnet (Jsonnet)

Grafonnet è una libreria Jsonnet per generare dashboard Grafana programmaticamente.

```jsonnet
// dashboard.jsonnet
local grafana = import 'grafonnet/grafana.libsonnet';
local dashboard = grafana.dashboard;
local prometheus = grafana.prometheus;
local graphPanel = grafana.graphPanel;
local template = grafana.template;

dashboard.new(
  'Node Overview',
  tags=['node', 'infrastructure'],
  time_from='now-1h',
)
.addTemplate(
  template.new(
    'instance',
    'Prometheus',
    'label_values(up{job="node"}, instance)',
    multi=true,
    includeAll=true,
  )
)
.addPanel(
  graphPanel.new(
    'CPU Usage',
    datasource='Prometheus',
    format='percent',
    min=0,
    max=100,
  ).addTarget(
    prometheus.target(
      '100 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle", instance=~"$instance"}[5m])) * 100',
      legendFormat='{{ instance }}',
    )
  ),
  gridPos={x: 0, y: 0, w: 24, h: 8},
)
```

```bash
# Genera JSON dalla definizione Jsonnet
jsonnet -J vendor dashboard.jsonnet > dashboard.json
```

#### Terraform Provider

```hcl
# Grafana Terraform provider per dashboard infrastructure-as-code
resource "grafana_dashboard" "node_overview" {
  config_json = file("dashboards/node-overview.json")
  folder      = grafana_folder.infrastructure.id
  overwrite   = true
}

resource "grafana_folder" "infrastructure" {
  title = "Infrastructure"
}

resource "grafana_data_source" "prometheus" {
  type = "prometheus"
  name = "Prometheus"
  url  = "http://prometheus:9090"

  json_data_encoded = jsonencode({
    httpMethod = "POST"
    timeInterval = "15s"
  })
}
```

### Provisioning Automatizzato

> Riferimento: https://grafana.com/docs/grafana/latest/administration/provisioning/ (consultato: 2026-05-23)

Il provisioning permette di configurare Grafana all'avvio senza intervento manuale, ideale per deployment automatizzati.

```yaml
# /etc/grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
    jsonData:
      httpMethod: POST
      timeInterval: '15s'

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
      tracesToLogs:
        datasourceUid: loki
```

```yaml
# /etc/grafana/provisioning/dashboards/default.yml
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: 'Provisioned'
    type: file
    disableDeletion: true
    updateIntervalSeconds: 30
    allowUiUpdates: false
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

```yaml
# /etc/grafana/provisioning/alerting/alerts.yml
apiVersion: 1
groups:
  - orgId: 1
    name: Infrastructure
    folder: Alerts
    interval: 1m
    rules:
      - uid: node-cpu-high
        title: High CPU Usage
        condition: C
        data:
          - refId: A
            datasourceUid: prometheus
            model:
              expr: instance:node_cpu_utilisation:rate5m > 85
        for: 5m
        labels:
          severity: warning
```

---

## Grafana: Alerting Unificato

> Riferimento: https://grafana.com/docs/grafana/latest/alerting/ (consultato: 2026-05-24)

A partire da Grafana 9+, il sistema di alerting è stato completamente riprogettato con l'**Unified Alerting**, che sostituisce il vecchio modello legacy basato su alert incorporati nei panel delle dashboard. Questo nuovo approccio centralizza la gestione degli alert, separandoli dalla visualizzazione e allineandosi all'architettura di Alertmanager.

### Architettura dell'Alerting Unificato

L'Unified Alerting introduce una separazione netta tra tre componenti fondamentali:

1. **Alert Rules**: definizioni dichiarative delle condizioni di alerting, indipendenti dalle dashboard. Ogni regola specifica una o più query (PromQL, LogQL, SQL, ecc.), una condizione di valutazione e una durata `for` prima del firing.

2. **Contact Points**: i canali di destinazione delle notifiche — email, Slack, PagerDuty, Telegram, webhook, Microsoft Teams, OpsGenie, e molti altri. Ogni contact point può avere template personalizzati per formattare il messaggio di notifica.

3. **Notification Policies**: l'albero di routing che determina quale contact point riceve quale alert, basato su label matching. Funziona in modo analogo al routing tree di Alertmanager, con supporto per grouping, timing (group_wait, group_interval, repeat_interval) e muting.

Grafana include un **Alertmanager interno** integrato, ma può anche connettersi a un Alertmanager esterno (ad esempio quello deployato con Prometheus Operator). La scelta dipende dall'architettura: per setup semplici l'Alertmanager interno è sufficiente; per ambienti Kubernetes con più istanze Prometheus, un Alertmanager esterno condiviso è preferibile.

### Contact Points

La configurazione dei contact point avviene tramite UI o provisioning YAML:

```yaml
# provisioning/contactpoints.yaml
apiVersion: 1
contactPoints:
  - orgId: 1
    name: team-platform-slack
    receivers:
      - uid: slack-platform
        type: slack
        settings:
          recipient: "#platform-alerts"
          token: $SLACK_BOT_TOKEN
          title: |
            {{ .Status | toUpper }}: {{ .CommonLabels.alertname }}
          text: |
            {{ range .Alerts }}
            *Severity*: {{ .Labels.severity }}
            *Instance*: {{ .Labels.instance }}
            *Summary*: {{ .Annotations.summary }}
            {{ end }}
      - uid: pagerduty-critical
        type: pagerduty
        settings:
          integrationKey: $PAGERDUTY_KEY
          severity: '{{ if eq .CommonLabels.severity "critical" }}critical{{ else }}warning{{ end }}'
```

Ogni contact point può contenere più receiver, consentendo la notifica simultanea su più canali. I template supportano le stesse funzioni Go template disponibili in Alertmanager nativo.

### Notification Policies

Le notification policies formano un albero gerarchico. La **policy di default** (root) cattura tutti gli alert non matchati da policy più specifiche:

```yaml
# provisioning/notification-policies.yaml
apiVersion: 1
policies:
  - orgId: 1
    receiver: team-platform-slack
    group_by:
      - alertname
      - cluster
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
    routes:
      - receiver: pagerduty-critical
        matchers:
          - severity = critical
        continue: false
        group_wait: 10s
        repeat_interval: 1h
      - receiver: team-platform-slack
        matchers:
          - severity = warning
        group_wait: 1m
        repeat_interval: 8h
      - receiver: dev-team-email
        matchers:
          - team = backend
          - severity =~ "warning|info"
        continue: true
```

Il campo `continue: true` permette a un alert di essere processato anche dalle policy successive, utile per inviare la stessa notifica a più destinatari. Il campo `matchers` supporta operatori di uguaglianza (`=`, `!=`) e regex (`=~`, `!~`).

### Alert Rules in Grafana

Le alert rules nell'Unified Alerting sono **indipendenti dalle dashboard**. Si definiscono nel contesto di un folder e un evaluation group:

```yaml
# provisioning/alert-rules.yaml
apiVersion: 1
groups:
  - orgId: 1
    name: SLO Monitoring
    folder: Platform Alerts
    interval: 30s
    rules:
      - uid: slo-availability-breach
        title: "SLO Availability sotto target"
        condition: threshold_check
        data:
          - refId: error_ratio
            datasourceUid: prometheus-main
            model:
              expr: |
                1 - (
                  sum(rate(http_requests_total{status!~"5.."}[30m]))
                  /
                  sum(rate(http_requests_total[30m]))
                )
          - refId: threshold_check
            datasourceUid: __expr__
            model:
              type: threshold
              conditions:
                - evaluator:
                    type: gt
                    params: [0.001]
        for: 10m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Availability SLO breach: error ratio {{ $values.error_ratio }} > 0.1%"
          runbook_url: "https://runbooks.internal/slo-availability"
```

Le regole supportano **multi-dimensional alerting**: una singola regola può generare alert separati per ogni combinazione di label risultante dalla query, permettendo di monitorare centinaia di servizi con una sola definizione.

### Relazione con Alertmanager

Grafana Unified Alerting e Prometheus Alertmanager sono complementari:

| Aspetto | Alertmanager Prometheus | Grafana Unified Alerting |
|---------|------------------------|--------------------------|
| Input | Solo alert da Prometheus | Query multi-datasource (Prometheus, Loki, SQL, ecc.) |
| Configurazione | YAML file su disco | UI + provisioning YAML |
| Routing | routing tree YAML | notification policies (simile) |
| HA | Cluster gossip nativo | Dipende dal database Grafana |
| Template | Go templates | Go templates (compatibili) |
| Silencing | Tramite UI/API AM | Tramite UI Grafana (mute timings) |

In ambienti ibridi, Grafana può inoltrare gli alert al proprio Alertmanager interno oppure a un Alertmanager esterno. Per Kubernetes, è comune usare Prometheus Alertmanager per gli alert infrastrutturali e Grafana Unified Alerting per alert basati su datasource eterogenei (Loki + Prometheus + database SQL).

---

## Setup Completo End-to-End

### Docker Compose per lo Stack Completo

```yaml
# docker-compose.monitoring.yml

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
    ports:
      - "9093:9093"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
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
    restart: unless-stopped

  blackbox-exporter:
    image: prom/blackbox-exporter:latest
    container_name: blackbox-exporter
    volumes:
      - ./blackbox/config.yml:/etc/blackbox_exporter/config.yml:ro
    ports:
      - "9115:9115"
    restart: unless-stopped

volumes:
  prometheus_data:
  alertmanager_data:
  grafana_data:
```

---

## Federation e Scaling

Quando un singolo Prometheus non basta — troppi target, troppi dati, requisiti di retention a lungo termine — è necessario scalare.

### Federation Gerarchica

> Riferimento: https://prometheus.io/docs/prometheus/latest/federation/ (consultato: 2026-05-23)

La federation permette a un Prometheus di scraping dati aggregati da altri Prometheus. Architettura tipica: Prometheus "foglia" per datacenter/cluster, Prometheus "globale" che federa le recording rules aggregate.

```yaml
# prometheus-global.yml — Prometheus federatore
scrape_configs:
  - job_name: 'federate-dc1'
    scrape_interval: 30s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        # Scrape solo recording rules aggregate, non metriche raw
        - '{__name__=~"job:.*"}'
        - '{__name__=~"instance:.*"}'
        - '{__name__=~"cluster:.*"}'
    static_configs:
      - targets:
          - 'prometheus-dc1:9090'
        labels:
          datacenter: 'dc1'

  - job_name: 'federate-dc2'
    scrape_interval: 30s
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{__name__=~"job:.*"}'
        - '{__name__=~"instance:.*"}'
    static_configs:
      - targets:
          - 'prometheus-dc2:9090'
        labels:
          datacenter: 'dc2'
```

**Regola critica**: Non federare metriche raw ad alta cardinalità. Federare solo recording rules pre-aggregate. Altrimenti il Prometheus globale diventa un collo di bottiglia.

```
Architettura federation:

  ┌─────────────────┐     ┌─────────────────┐
  │ Prom DC1        │     │ Prom DC2        │
  │ (1000 target)   │     │ (800 target)    │
  │ scrape raw data │     │ scrape raw data │
  │ recording rules │     │ recording rules │
  └────────┬────────┘     └────────┬────────┘
           │                       │
           │  /federate (solo      │
           │  recording rules)     │
           ▼                       ▼
  ┌─────────────────────────────────────────┐
  │         Prometheus Globale              │
  │  - Vista cross-datacenter               │
  │  - Dashboard globali                    │
  │  - Alert cross-cluster                  │
  └─────────────────────────────────────────┘
```

### Thanos: Architettura Completa

> Riferimento: https://thanos.io/tip/thanos/design.md/ (consultato: 2026-05-23)

Thanos estende Prometheus con storage a lungo termine, global query e alta disponibilità. Progetto CNCF graduated.

```
Architettura Thanos:

  ┌──────────────────┐    ┌──────────────────┐
  │ Prometheus + HA  │    │ Prometheus + HA  │
  │ ┌──────────────┐ │    │ ┌──────────────┐ │
  │ │ Thanos       │ │    │ │ Thanos       │ │
  │ │ Sidecar      │─┤    │ │ Sidecar      │─┤
  │ └──────────────┘ │    │ └──────────────┘ │
  └────────┬─────────┘    └────────┬─────────┘
           │                       │
           │  gRPC StoreAPI        │
           ▼                       ▼
  ┌─────────────────────────────────────────┐
  │              Thanos Query               │
  │  (deduplicazione, merge di risultati)   │
  └────────────────┬────────────────────────┘
                   │
           ┌───────┴───────┐
           │               │
           ▼               ▼
  ┌─────────────┐  ┌──────────────┐
  │ Thanos      │  │ Object Store │
  │ Store GW    │  │ (S3/GCS/     │
  │ (legge da   │  │  Azure Blob) │
  │ object      │  │              │
  │ store)      │  │ ← upload     │
  └─────────────┘  │   blocchi    │
                   └──────────────┘
                          ▲
                          │
                   ┌──────┴──────┐
                   │   Thanos    │
                   │  Compactor  │
                   │ (compatta + │
                   │  downsample │
                   │  i blocchi) │
                   └─────────────┘
```

Componenti Thanos:

| Componente | Funzione |
|------------|----------|
| **Sidecar** | Affiancato a Prometheus, carica blocchi su object store e serve dati recenti via StoreAPI |
| **Store Gateway** | Serve dati storici dall'object store via StoreAPI |
| **Query** | Frontend di query: merge dati da sidecar + store + ruler. Deduplicazione HA integrata |
| **Compactor** | Compatta e downsampla blocchi nell'object store. **Singleton** — mai più di uno |
| **Ruler** | Valuta recording rules e alerting rules su dati globali (opzionale) |
| **Receive** | Alternativa al sidecar: riceve dati via remote_write (architettura push) |

```yaml
# docker-compose.thanos.yml (estratto)
services:
  thanos-sidecar:
    image: quay.io/thanos/thanos:latest
    command:
      - sidecar
      - --tsdb.path=/prometheus
      - --prometheus.url=http://prometheus:9090
      - --objstore.config-file=/etc/thanos/objstore.yml
      - --grpc-address=0.0.0.0:10901
    volumes:
      - prometheus_data:/prometheus:ro
      - ./thanos/objstore.yml:/etc/thanos/objstore.yml:ro

  thanos-query:
    image: quay.io/thanos/thanos:latest
    command:
      - query
      - --store=thanos-sidecar:10901
      - --store=thanos-store:10901
      - --query.auto-downsampling
      - --query.replica-label=replica
    ports:
      - "19090:9090"

  thanos-store:
    image: quay.io/thanos/thanos:latest
    command:
      - store
      - --objstore.config-file=/etc/thanos/objstore.yml
      - --data-dir=/var/thanos/store
    volumes:
      - ./thanos/objstore.yml:/etc/thanos/objstore.yml:ro
```

```yaml
# /etc/thanos/objstore.yml — configurazione object store (S3)
type: S3
config:
  bucket: "thanos-metrics"
  endpoint: "s3.eu-west-1.amazonaws.com"
  access_key: "${AWS_ACCESS_KEY_ID}"
  secret_key: "${AWS_SECRET_ACCESS_KEY}"
  region: "eu-west-1"
```

### Cortex e Mimir

**Grafana Mimir** (successore di Cortex) è la soluzione Grafana Labs per Prometheus multi-tenant a lungo termine. A differenza di Thanos che estende Prometheus esistenti, Mimir è un backend di storage indipendente.

| Caratteristica | Thanos | Mimir |
|---------------|--------|-------|
| Modello | Estende Prometheus esistenti | Backend di storage separato |
| Ingest | Sidecar + StoreAPI oppure Receive | remote_write |
| Multi-tenancy | Limitato | Nativo |
| Complessità operativa | Moderata (più componenti) | Alta (richiede key-value store) |
| Query globali | Via Thanos Query | Via query frontend distribuito |
| Licensing | Apache 2.0 | AGPLv3 |

### remote_write e remote_read

`remote_write` e `remote_read` sono le interfacce standard per integrare Prometheus con storage esterni.

```yaml
# prometheus.yml — remote_write verso Mimir/Thanos Receive/Cortex
remote_write:
  - url: "http://mimir:9009/api/v1/push"
    queue_config:
      capacity: 10000
      max_shards: 30
      min_shards: 1
      max_samples_per_send: 5000
      batch_send_deadline: 5s
    write_relabel_configs:
      # Non inviare metriche go_* al remote storage
      - source_labels: [__name__]
        regex: 'go_.*'
        action: drop

# remote_read — query trasparente verso storage esterno
remote_read:
  - url: "http://thanos-query:9090/api/v1/read"
    read_recent: false  # non leggere dati recenti (li ha già localmente)
```

### Storage a Lungo Termine (S3/GCS)

Calcolo del dimensionamento dello storage:

```
Formula approssimativa:
  bytes/campione ≈ 1.5-2 byte (compresso)
  campioni/giorno = serie_attive × (86400 / scrape_interval)

Esempio:
  10.000 serie attive × scrape ogni 15s
  = 10.000 × 5760 campioni/giorno
  = 57.600.000 campioni/giorno
  × 2 byte/campione = ~115 MB/giorno = ~3.4 GB/mese

Per 1 anno di retention: ≈ 42 GB (compresso)
Con downsampling (5m, 1h): riduzione 10-20x sui dati storici
```

---

## Metodologia RED e USE

Due framework complementari per definire quali metriche monitorare.

### RED Method (per servizi)

> Tom Wilkie, Weaveworks — "The RED Method: How to instrument your services"

**R**ate — **E**rrors — **D**uration

| Segnale | Metrica | Query PromQL |
|---------|---------|--------------|
| **Rate** | Richieste per secondo | `sum(rate(http_requests_total[5m])) by (service)` |
| **Errors** | Tasso di errori | `sum(rate(http_requests_total{status=~"5.."}[5m])) by (service) / sum(rate(http_requests_total[5m])) by (service)` |
| **Duration** | Distribuzione della latenza | `histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))` |

RED risponde a: "Il mio servizio funziona correttamente dal punto di vista dell'utente?"

### USE Method (per risorse)

> Brendan Gregg — "The USE Method"

**U**tilization — **S**aturation — **E**rrors

| Risorsa | Utilization | Saturation | Errors |
|---------|-------------|------------|--------|
| **CPU** | `rate(node_cpu_seconds_total{mode!="idle"}[5m])` | `node_load1 / count(node_cpu_seconds_total{mode="idle"})` | — |
| **Memoria** | `1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes` | `rate(node_vmstat_pswpin[5m]) + rate(node_vmstat_pswpout[5m])` (swap) | `node_edac_correctable_errors_total` |
| **Disco** | `rate(node_disk_io_time_seconds_total[5m])` | `node_disk_io_time_weighted_seconds_total` | `node_disk_io_now` (stuck I/O) |
| **Rete** | `rate(node_network_receive_bytes_total[5m]) / node_network_speed_bytes` | `rate(node_network_transmit_drop_total[5m])` (drop) | `rate(node_network_receive_errs_total[5m])` |

USE risponde a: "La mia infrastruttura ha risorse sufficienti?"

**Approccio combinato**: Usare RED per i servizi applicativi e USE per le risorse infrastrutturali. Le due metodologie sono complementari.

```yaml
# Recording rules per RED method
groups:
  - name: red_method
    rules:
      - record: service:http_requests:rate5m
        expr: sum(rate(http_requests_total[5m])) by (service)

      - record: service:http_errors:ratio_rate5m
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) by (service)
          /
          sum(rate(http_requests_total[5m])) by (service)

      - record: service:http_duration:p99_rate5m
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le, service))

# Recording rules per USE method
  - name: use_method
    rules:
      - record: instance:node_cpu:utilisation_rate5m
        expr: |
          1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m]))

      - record: instance:node_cpu:saturation
        expr: |
          node_load1 /
          count by (instance) (node_cpu_seconds_total{mode="idle"})

      - record: instance:node_memory:utilisation
        expr: |
          1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes

      - record: instance:node_memory:saturation_rate5m
        expr: |
          rate(node_vmstat_pswpin[5m]) + rate(node_vmstat_pswpout[5m])
```

---

## Prometheus Operator su Kubernetes

> Riferimento: https://prometheus-operator.dev/docs/getting-started/introduction/ (consultato: 2026-05-23)

Il Prometheus Operator semplifica il deployment e la configurazione di Prometheus su Kubernetes tramite Custom Resource Definitions (CRD).

### Installazione via Helm

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --create-namespace \
    --set prometheus.prometheusSpec.retention=30d \
    --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=100Gi
```

### CRD Principali

#### ServiceMonitor

Definisce come Prometheus deve scoprire e scrapare servizi Kubernetes.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: myapp-monitor
  namespace: monitoring
  labels:
    release: kube-prometheus-stack  # deve matchare il selector del Prometheus
spec:
  namespaceSelector:
    matchNames:
      - production
  selector:
    matchLabels:
      app: myapp
  endpoints:
    - port: http-metrics
      interval: 15s
      path: /metrics
      scheme: http
      relabelings:
        - sourceLabels: [__meta_kubernetes_pod_label_version]
          targetLabel: app_version
      metricRelabelings:
        - sourceLabels: [__name__]
          regex: 'go_.*'
          action: drop
```

#### PodMonitor

Come ServiceMonitor, ma per pod senza Service associato.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: batch-jobs-monitor
  namespace: monitoring
spec:
  namespaceSelector:
    matchNames:
      - batch
  selector:
    matchLabels:
      monitoring: enabled
  podMetricsEndpoints:
    - port: metrics
      interval: 30s
```

#### PrometheusRule

Definisce recording rules e alerting rules come risorsa Kubernetes.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: myapp-rules
  namespace: monitoring
  labels:
    release: kube-prometheus-stack
spec:
  groups:
    - name: myapp.rules
      rules:
        - record: namespace:http_requests:rate5m
          expr: |
            sum(rate(http_requests_total[5m])) by (namespace, service)

        - alert: MyAppHighErrorRate
          expr: |
            sum(rate(http_requests_total{status=~"5..", service="myapp"}[5m]))
            /
            sum(rate(http_requests_total{service="myapp"}[5m]))
            > 0.05
          for: 5m
          labels:
            severity: critical
            team: backend
          annotations:
            summary: "Error rate alto per myapp nel namespace {{ $labels.namespace }}"
```

---

## Exemplars e Correlazione Metriche-Trace

> Riferimento: https://prometheus.io/docs/prometheus/latest/feature_flags/#exemplars-storage (consultato: 2026-05-24)

Gli **exemplars** rappresentano il ponte tra metriche e tracce distribuite, risolvendo uno dei problemi fondamentali dell'observability: passare da un aggregato numerico (es. "la latency p99 è 2.3s") al singolo request che ha generato quel valore anomalo. Un exemplar è un campione aggiuntivo allegato a un data point di un histogram o counter, contenente un **trace_id** che punta alla traccia distribuita corrispondente.

### Cosa Sono gli Exemplars

Nel formato **OpenMetrics** (evoluzione di Prometheus exposition format), un exemplar appare come annotazione inline:

```text
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.5",method="GET"} 12000 # {trace_id="abc123def456"} 0.48 1716556800.000
http_request_duration_seconds_bucket{le="1.0",method="GET"} 14500 # {trace_id="789xyz012abc"} 0.92 1716556801.000
http_request_duration_seconds_bucket{le="+Inf",method="GET"} 15000 # {trace_id="deadbeef4242"} 3.71 1716556802.000
```

Ogni riga `# {trace_id="..."} valore timestamp` è un exemplar: il valore osservato (`0.48`, `0.92`, `3.71`) e il trace_id che permette di navigare direttamente alla traccia in Tempo, Jaeger o Zipkin. Prometheus conserva gli exemplars in un buffer circolare separato dalla TSDB, con retention configurabile (default: 5 minuti di campioni).

### Configurazione Prometheus per Exemplars

Per abilitare gli exemplars in Prometheus è necessario attivare la feature flag:

```bash
# Avvio Prometheus con exemplars abilitati
prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --enable-feature=exemplar-storage \
  --storage.exemplars.max-exemplars=100000
```

Il parametro `--storage.exemplars.max-exemplars` definisce il numero massimo di exemplars in memoria. Prometheus espone anche le metriche `prometheus_tsdb_exemplar_exemplars_in_storage` e `prometheus_tsdb_exemplar_exemplars_appended_total` per monitorare l'utilizzo.

Lo scrape dei target deve avvenire con il content type OpenMetrics per ricevere exemplars:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'instrumented-app'
    scrape_interval: 15s
    # Prometheus negozia automaticamente OpenMetrics se il target lo supporta
    metrics_path: /metrics
    static_configs:
      - targets: ['app:8080']
```

Il target deve esporre metriche in formato OpenMetrics (`application/openmetrics-text`) anziché il classico Prometheus text format, affinché gli exemplars siano trasmessi.

### Instrumentazione Client con Exemplars

Le librerie client Prometheus supportano l'aggiunta di exemplars. Ecco un esempio in Go con il middleware HTTP:

```go
package main

import (
    "net/http"
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promhttp"
    "go.opentelemetry.io/otel/trace"
)

var httpDuration = prometheus.NewHistogramVec(
    prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Help:    "Duration of HTTP requests",
        Buckets: prometheus.DefBuckets,
    },
    []string{"method", "path", "status"},
)

func instrumentedHandler(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        timer := prometheus.NewTimer(prometheus.ObserverFunc(func(v float64) {
            spanCtx := trace.SpanContextFromContext(r.Context())
            if spanCtx.HasTraceID() {
                httpDuration.WithLabelValues(r.Method, r.URL.Path, "200").
                    (Observe).(prometheus.ExemplarObserver).
                    ObserveWithExemplar(v, prometheus.Labels{
                        "trace_id": spanCtx.TraceID().String(),
                    })
            }
        }))
        next.ServeHTTP(w, r)
        timer.ObserveDuration()
    })
}
```

In Python con `prometheus_client`:

```python
from prometheus_client import Histogram, CONTENT_TYPE_LATEST
from opentelemetry import trace

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'Duration of HTTP requests',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

def observe_request(method, endpoint, duration):
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(
            duration,
            exemplar={'trace_id': format(ctx.trace_id, '032x')}
        )
```

### Visualizzazione Exemplars in Grafana

In Grafana, la visualizzazione degli exemplars richiede:

1. **Datasource Prometheus** configurato con "Exemplars" abilitato e il campo `trace_id` mappato al datasource di tracing (Tempo, Jaeger).

2. **Internal link** configurato nel datasource Prometheus:

```yaml
# provisioning/datasources.yaml
datasources:
  - name: Prometheus
    type: prometheus
    url: http://prometheus:9090
    jsonData:
      exemplarTraceIdDestinations:
        - name: trace_id
          datasourceUid: tempo
          urlDisplayLabel: "Vedi Traccia"
```

3. Nella query del panel, attivare il toggle **"Exemplars"**. I punti exemplar appaiono come rombi sovrapposti al grafico del histogram. Cliccando su un exemplar, Grafana apre direttamente la traccia nel datasource Tempo/Jaeger configurato.

Il flusso completo è: **metrica anomala → exemplar → trace_id → traccia distribuita → span specifico**, eliminando il gap tra "so che c'è un problema" e "vedo esattamente quale request l'ha causato". Questo workflow è particolarmente potente combinato con Loki: dalla traccia si risale ai log correlati tramite il campo `trace_id`, chiudendo il ciclo delle tre colonne dell'observability (metriche, tracce, log).

---

## Sicurezza

### TLS per Scraping

> Riferimento: https://prometheus.io/docs/prometheus/latest/configuration/configuration/#tls_config (consultato: 2026-05-23)

```yaml
# prometheus.yml — scrape con TLS e autenticazione
scrape_configs:
  - job_name: 'secure-app'
    scheme: https
    tls_config:
      ca_file: /etc/prometheus/certs/ca.pem
      cert_file: /etc/prometheus/certs/prometheus.pem
      key_file: /etc/prometheus/certs/prometheus-key.pem
      # insecure_skip_verify: false  # default, MAI impostare a true in produzione
    basic_auth:
      username: 'prometheus'
      password_file: /etc/prometheus/secrets/scrape-password
    static_configs:
      - targets: ['secure-app:8443']
```

### Autenticazione Prometheus

Prometheus supporta autenticazione per il proprio endpoint web a partire dalla versione 2.24+.

```yaml
# /etc/prometheus/web.yml
basic_auth_users:
  # Generare con: htpasswd -nBC 12 admin
  admin: '$2y$12$...'    # bcrypt hash della password

tls_server_config:
  cert_file: /etc/prometheus/certs/server.pem
  key_file: /etc/prometheus/certs/server-key.pem
  client_auth_type: RequireAndVerifyClientCert
  client_ca_file: /etc/prometheus/certs/ca.pem
```

```bash
prometheus --web.config.file=/etc/prometheus/web.yml \
    --config.file=/etc/prometheus/prometheus.yml
```

### RBAC in Grafana

```ini
# /etc/grafana/grafana.ini — sezione autenticazione avanzata

[auth.ldap]
enabled = true
config_file = /etc/grafana/ldap.toml

[auth.generic_oauth]
enabled = true
name = SSO
client_id = grafana-client-id
client_secret = ${GF_AUTH_GENERIC_OAUTH_CLIENT_SECRET}
scopes = openid profile email
auth_url = https://idp.example.com/authorize
token_url = https://idp.example.com/token
api_url = https://idp.example.com/userinfo
role_attribute_path = contains(groups[*], 'admin') && 'Admin' || contains(groups[*], 'editor') && 'Editor' || 'Viewer'
```

Ruoli Grafana e permessi:

| Ruolo | Permessi |
|-------|----------|
| **Viewer** | Visualizza dashboard e query. Non può modificare nulla |
| **Editor** | Crea/modifica dashboard e alert. Non gestisce utenti o data source |
| **Admin** | Pieno controllo: utenti, data source, plugin, organizzazione |

### Audit Logging

```ini
# /etc/grafana/grafana.ini — audit log (Grafana Enterprise o OSS 9+)
[log]
mode = file console
level = info
filters = apiserver:debug

# Log delle azioni utente
[log.file]
log_rotate = true
max_lines = 1000000
max_size_shift = 28
daily_rotate = true
max_days = 90
```

---

## Gestione Operativa

### Gestione della Cardinalità

La cardinalità è il numero di combinazioni uniche di nome metrica + set di label. È il fattore principale che determina l'uso di memoria e le performance di Prometheus.

```promql
# Conta le serie attive totali
prometheus_tsdb_head_series

# Top 10 metriche per numero di serie
topk(10, count by (__name__) ({__name__!=""}))

# Serie create da uno specifico job
count({job="myapp"})

# Serie per metrica per un job
count by (__name__) ({job="myapp"})
```

**Regole per contenere la cardinalità:**

1. **Mai usare valori ad alta cardinalità come label**: user_id, request_id, IP address, URL path completo, query SQL
2. **Limit del bucket**: Non più di 10-15 bucket per histogram
3. **Label statiche**: Le label devono avere un set finito e piccolo di valori
4. **Drop metriche inutili**: Usare `metric_relabel_configs` per eliminare metriche non utilizzate

```yaml
# Esempio: drop metriche Go runtime non necessarie
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'go_(gc|memstats|threads|info)_.*'
    action: drop
```

### Convenzioni di Naming delle Metriche

> Riferimento: https://prometheus.io/docs/practices/naming/ (consultato: 2026-05-23)

| Regola | Esempio corretto | Esempio errato |
|--------|-----------------|----------------|
| snake_case | `http_requests_total` | `httpRequestsTotal` |
| Suffisso `_total` per counter | `errors_total` | `errors` |
| Suffisso `_seconds` per durate | `request_duration_seconds` | `request_duration_ms` |
| Suffisso `_bytes` per dimensioni | `file_size_bytes` | `file_size_kb` |
| Suffisso `_info` per metriche informative (gauge=1) | `build_info` | `build_version` |
| Prefisso per namespace | `myapp_queue_size` | `queue_size` |
| Unità base (secondi, byte, non milli-) | `_seconds`, `_bytes` | `_milliseconds`, `_kilobytes` |

### Label Hygiene

```yaml
# Label da usare sempre:
# job         → nome del servizio/applicazione
# instance    → host:porta del target
# environment → production/staging/development
# team        → team responsabile

# Label da NON usare MAI come label di metrica:
# user_id, session_id         → cardinalità infinita
# timestamp                   → è già nel campione
# ip_address                  → troppi valori unici
# full_url_path               → usare pattern: /api/v1/users/{id}
# query_text                  → infiniti valori
```

### Dimensionamento dello Storage

```bash
# Formula per dimensionamento
# Spazio = serie_attive × campioni_per_secondo × byte_per_campione × retention_secondi
#
# Valori tipici:
#   byte_per_campione ≈ 1.5-2 (compresso)
#   campioni_per_secondo = serie / scrape_interval

# Esempio pratico:
#   50.000 serie attive
#   scrape_interval = 15s
#   retention = 30 giorni
#
#   Campioni/giorno = 50.000 × (86400/15) = 288.000.000
#   Spazio/giorno = 288M × 2 byte ≈ 576 MB/giorno
#   Spazio 30 giorni ≈ 17 GB
#   + WAL e overhead ≈ 20-25 GB totali

# Metriche per monitorare lo storage
prometheus_tsdb_storage_blocks_bytes          # spazio blocchi
prometheus_tsdb_head_chunks_storage_size_bytes # spazio head
prometheus_tsdb_wal_storage_size_bytes         # spazio WAL
```

---

## Best Practices

1. **Usa recording rules per query complesse**: Le query usate ripetutamente nelle dashboard e negli alert devono essere pre-calcolate come recording rules per ridurre il carico su Prometheus.

2. **Imposta retention basata sulla capacità disco**: `--storage.tsdb.retention.time=30d` e `--storage.tsdb.retention.size=50GB` — usa entrambi per evitare di riempire il disco.

3. **Etichetta con external_labels**: Ogni istanza Prometheus deve avere label univoche (environment, datacenter) per poter federare o aggregare dati da più istanze.

4. **Usa `for` negli alert**: La clausola `for` previene alert per picchi transitori. Un `for: 5m` significa che la condizione deve essere vera per 5 minuti consecutivi.

5. **Implementa inhibition in Alertmanager**: Se un server è completamente down (critical), non ha senso ricevere anche alert per CPU alta (warning) sullo stesso server.

6. **Dashboard con variabili**: Le dashboard devono usare variabili template per essere riutilizzabili. Una dashboard hard-coded per un singolo server non scala.

7. **Monitora il monitoring**: Prometheus deve monitorare sé stesso. Configura alert per `prometheus_tsdb_*` metrics e per lo spazio disco.

8. **Backup delle dashboard Grafana**: Esporta le dashboard come JSON e versionale in git. Oppure usa il provisioning via file.

9. **Scrape interval coerente**: Non usare intervalli troppo corti (< 10s) senza necessità. Ogni scrape genera dati e consuma risorse. 15-30 secondi è adeguato per la maggior parte dei casi.

10. **Usa histogram per la latenza, non summary**: Gli histogram sono aggregabili tra istanze, i summary no. `histogram_quantile` è calcolato lato query, permettendo flessibilità.

---

## Troubleshooting

### Problema: Prometheus non scrape un target

**Sintomi**: Il target appare come DOWN nella pagina Targets (`http://localhost:9090/targets`).

**Causa**: Target non raggiungibile, firewall, porta sbagliata, o path /metrics errato.

**Soluzione**:
```bash
# Verifica raggiungibilità dal server Prometheus
curl -v http://target_host:9100/metrics

# Verifica firewall
ss -tlnp | grep 9100   # sul target

# Controlla l'errore in Prometheus UI → Status → Targets
# "connection refused" → servizio non in ascolto
# "context deadline exceeded" → timeout, probabile firewall
```

### Problema: Alert non inviato

**Sintomi**: L'alert è in stato FIRING in Prometheus ma Alertmanager non invia notifiche.

**Causa**: Prometheus non riesce a raggiungere Alertmanager, o il routing in Alertmanager non matcha.

**Soluzione**:
```bash
# Verifica connessione Prometheus → Alertmanager
curl http://localhost:9093/-/healthy

# Verifica alert in Alertmanager UI
curl http://localhost:9093/api/v2/alerts

# Verifica routing
amtool config routes show --config.file=/etc/alertmanager/alertmanager.yml

# Testa il routing per un alert specifico
amtool config routes test --config.file=/etc/alertmanager/alertmanager.yml \
    alertname=HighCPUUsage severity=critical
```

### Problema: Dashboard Grafana mostra "No data"

**Sintomi**: I pannelli Grafana mostrano "No data" nonostante Prometheus abbia i dati.

**Causa**: Data source non configurato, query errata, range temporale sbagliato, o variabile non selezionata.

**Soluzione**:
```
1. Verifica data source: Settings → Data Sources → Prometheus → Test
2. Esegui la stessa query in Prometheus UI (http://localhost:9090/graph)
3. Controlla il range temporale nella dashboard
4. Controlla che le variabili abbiano valori selezionati
5. Usa "Query Inspector" nel pannello per vedere la query esatta inviata
```

### Problema: Alta cardinalità — Prometheus consuma troppa memoria

**Sintomi**: Prometheus usa molta RAM, query lente, OOM kill periodici.

**Causa**: Metriche con label ad alta cardinalità (user_id, request_id, URL path completo).

**Soluzione**:
```promql
# Identifica le metriche con più serie
topk(20, count by (__name__) ({__name__!=""}))

# Identifica le label con più valori unici per una metrica
count by (label_name) (http_requests_total)
```

```yaml
# Elimina metriche ad alta cardinalità
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'problematic_metric_.*'
    action: drop
```

### Problema: Query PromQL lente

**Sintomi**: Le query impiegano secondi o vanno in timeout.

**Causa**: Query su troppe serie, range troppo lungo, aggregazioni senza filtri.

**Soluzione**:
```promql
# PRIMA: query lenta su tutte le serie
sum(rate(http_requests_total[5m]))

# DOPO: filtrare prima di aggregare
sum(rate(http_requests_total{job="myapp"}[5m])) by (status)

# Usare recording rules per query ripetute
# Ridurre il range per query esplorative
# Evitare subquery con range lunghi su metriche ad alta cardinalità
```

### Problema: Scrape mancati intermittenti

**Sintomi**: `scrape_duration_seconds` varia molto, `up` fluttua tra 0 e 1.

**Causa**: Target lento a rispondere, rete instabile, timeout troppo stretto.

**Soluzione**:
```yaml
# Aumenta il timeout per target lenti
scrape_configs:
  - job_name: 'slow-app'
    scrape_interval: 30s
    scrape_timeout: 25s  # deve essere < scrape_interval
    static_configs:
      - targets: ['slow-app:8080']
```

```promql
# Monitorare la durata degli scrape
scrape_duration_seconds{job="slow-app"}

# Contare gli scrape falliti
sum(rate(prometheus_target_scrapes_exceeded_sample_limit_total[5m]))
```

### Problema: OOM Kill di Prometheus

**Sintomi**: Prometheus viene killato dal kernel (OOM), riavvio automatico, perdita dati.

**Causa**: Troppe serie attive, query costose simultanee, WAL troppo grande al riavvio.

**Soluzione**:
```bash
# Limita la memoria con cgroups/systemd
# /etc/systemd/system/prometheus.service.d/limits.conf
[Service]
MemoryMax=8G
MemoryHigh=6G

# Monitorare il consumo
process_resident_memory_bytes{job="prometheus"}
prometheus_tsdb_head_series
prometheus_tsdb_head_chunks
```

Strategie preventive:
- Ridurre la cardinalità (drop metriche inutili)
- Aumentare il scrape_interval dove possibile
- Usare `--storage.tsdb.max-block-duration` per controllare la dimensione dei blocchi
- Implementare sharding orizzontale (hashmod) se necessario

### Problema: Corruzione del WAL

**Sintomi**: Prometheus non parte, errori nel log tipo "error replaying WAL".

**Causa**: Crash improvviso (power loss, kill -9), disco pieno durante la scrittura.

**Soluzione**:
```bash
# Verifica il WAL con promtool
promtool tsdb analyze /var/lib/prometheus/

# Se il WAL è corrotto, tentare il repair
promtool tsdb clean /var/lib/prometheus/

# Ultima risorsa: rimuovere il WAL (si perdono i dati non ancora persistiti)
# ATTENZIONE: operazione distruttiva — procedere solo dopo backup
rm -rf /var/lib/prometheus/wal/
systemctl restart prometheus
```

### Problema: Grafana dashboard lente

**Sintomi**: Dashboard impiegano secondi a caricare, pannelli in timeout.

**Causa**: Troppe query per dashboard, query non ottimizzate, variabili con troppi valori.

**Soluzione**:
```
1. Controllare il Query Inspector: Grafana → pannello → Inspect → Query
   - Tempo di esecuzione di ogni query
   - Numero di serie restituite

2. Ottimizzare:
   - Usare recording rules per query ripetute
   - Ridurre il numero di pannelli per dashboard (max 20-25)
   - Usare $__rate_interval invece di range fisso
   - Limitare le variabili con regex
   - Impostare Min interval nei pannelli

3. Impostazioni Grafana:
   [database]
   cache_mode = shared   # condividi cache tra pannelli
   
   [dataproxy]
   timeout = 60           # timeout query in secondi
   keep_alive_seconds = 30
```

### Problema: Discrepanza tra metriche Prometheus e realtà

**Sintomi**: I valori mostrati da Prometheus non corrispondono a quelli reali (es. top mostra CPU 80% ma Prometheus mostra 40%).

**Causa**: Scrape interval troppo lungo, aliasing temporale, lookback delta.

**Soluzione**:
```
1. Verificare che lo scrape_interval sia adeguato al fenomeno monitorato
2. Confrontare il timestamp del campione con il momento dell'osservazione
3. Usare rate() con range >= 4x scrape_interval
4. Per metriche di sistema: verificare che node_exporter stia usando i collector corretti
```

### Problema: Clock skew tra Prometheus e target

**Sintomi**: Metriche con timestamp nel futuro, grafici con "buchi", alert intermittenti senza causa.

**Causa**: Orologio di sistema non sincronizzato tra Prometheus e i target.

**Soluzione**:
```bash
# Verificare la sincronizzazione NTP su tutti i nodi
timedatectl status
chronyc tracking   # oppure ntpq -p

# Monitorare il clock skew
node_timex_offset_seconds   # da node_exporter
```

### Problema: Prometheus non rileva nuovi target da service discovery

**Sintomi**: Nuovi servizi deployati non appaiono nella pagina Target di Prometheus.

**Causa**: Label/annotation mancanti, permessi insufficienti per la SD, filtri relabel troppo restrittivi.

**Soluzione**:
```bash
# Kubernetes: verificare annotation sul pod/service
kubectl get pod myapp-xxx -o yaml | grep -A5 annotations

# Verificare i log di Prometheus per errori di SD
journalctl -u prometheus | grep -i "discovery"

# Verificare i target scoperti (prima del relabeling)
# Prometheus UI → Status → Service Discovery
```

### Problema: Rate restituisce "No data" su counter appena creato

**Sintomi**: `rate(new_counter[5m])` restituisce empty nonostante il counter esista.

**Causa**: `rate()` necessita di almeno 2 campioni nell'intervallo per calcolare il tasso. Un counter appena creato ha un solo campione.

**Soluzione**: Attendere almeno 2 scrape interval. Se lo scrape_interval è 15s e il range è 5m, servono al minimo 2 campioni (30s). In pratica con 5m di range il problema si risolve autonomamente dopo il secondo scrape.

### Problema: Alertmanager invia duplicati

**Sintomi**: Stessa notifica ricevuta più volte per lo stesso alert.

**Causa**: Più istanze Prometheus inviano lo stesso alert senza deduplicazione, o configurazione cluster Alertmanager errata.

**Soluzione**:
```yaml
# Assicurarsi che external_labels sia unico per ogni Prometheus
global:
  external_labels:
    cluster: 'cluster-1'
    replica: 'prometheus-1'   # diverso per ogni replica

# In Alertmanager cluster, verificare la comunicazione gossip
alertmanager --cluster.listen-address=0.0.0.0:9094 \
    --cluster.peer=am2:9094
```

### Problema: remote_write backlog crescente

**Sintomi**: `prometheus_remote_storage_samples_pending` cresce, metriche in ritardo nello storage remoto.

**Causa**: Backend remoto lento, rete congestionata, configurazione della coda inadeguata.

**Soluzione**:
```yaml
# Tune della coda remote_write
remote_write:
  - url: "http://mimir:9009/api/v1/push"
    queue_config:
      capacity: 50000        # buffer più grande
      max_shards: 50          # più worker paralleli
      max_samples_per_send: 10000
      batch_send_deadline: 10s
      min_backoff: 1s
      max_backoff: 5m
```

```promql
# Monitorare il backlog
prometheus_remote_storage_samples_pending
prometheus_remote_storage_samples_failed_total
prometheus_remote_storage_bytes_total
```

### Problema: Prometheus config reload fallisce silenziosamente

**Sintomi**: Modifiche a `prometheus.yml` non prese in carico dopo `kill -SIGHUP` o `POST /-/reload`, nessun errore visibile nel log.

**Causa**: Errore di sintassi YAML nel file di configurazione. Prometheus valida il nuovo config e, se invalido, mantiene quello precedente senza crashare — ma il log a livello `info` potrebbe non essere monitorato.

**Soluzione**:
```bash
# SEMPRE validare PRIMA di ricaricare
promtool check config /etc/prometheus/prometheus.yml

# Verificare l'ultimo reload riuscito
curl -s http://localhost:9090/api/v1/status/config | jq '.status'

# Monitorare la metrica di reload
# 0 = ultimo reload fallito, 1 = riuscito
prometheus_config_last_reload_successful

# Timestamp dell'ultimo reload riuscito
prometheus_config_last_reload_success_timestamp_seconds
```

**Best Practice**: Aggiungere un alert permanente:
```yaml
- alert: PrometheusConfigReloadFailed
  expr: prometheus_config_last_reload_successful == 0
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Prometheus config reload fallito"
    description: "Verificare la sintassi di prometheus.yml con promtool check config"
```

> **Fonte**: prometheus.io/docs/prometheus/latest/configuration/configuration/#configuration — retrieved 2026-05-23

### Problema: Alertmanager template rendering errors

**Sintomi**: Le notifiche arrivano con contenuto vuoto, parziale o con stringhe come `<no value>`, oppure non arrivano affatto per errori di rendering del template.

**Causa**: Errori nel template Go (`.tmpl`) usato dai receiver: riferimento a campi inesistenti, pipe syntax errata, accesso a `.Labels` con chiave sbagliata.

**Soluzione**:
```bash
# Validare i template prima del deploy
amtool check-config /etc/alertmanager/alertmanager.yml

# Test di rendering con dati fittizi
amtool template render --template.glob='/etc/alertmanager/templates/*.tmpl' \
  --template.text='{{ template "email.subject" . }}'
```

```go
// Template difensivo — usare `index` con fallback
{{ define "custom.title" }}
  [{{ .Status | toUpper }}] {{ index .Labels "alertname" | default "Unknown" }}
{{ end }}

// Iterare sugli alert nel gruppo
{{ define "custom.body" }}
  {{ range .Alerts }}
    - {{ .Labels.alertname }}: {{ .Annotations.summary }}
      Inizio: {{ .StartsAt.Format "2006-01-02 15:04:05 MST" }}
  {{ end }}
{{ end }}
```

**Diagnosi**: Controllare i log di Alertmanager con `--log.level=debug` per vedere gli errori di template rendering.

> **Fonte**: prometheus.io/docs/alerting/latest/notification_template_reference/ — retrieved 2026-05-23

### Problema: blackbox_exporter DNS resolution failures

**Sintomi**: Probe HTTP/TCP falliscono con `probe_success=0`, ma il servizio target è raggiungibile manualmente. `probe_dns_lookup_time_seconds` è 0 o assente.

**Causa**: Il container o host dove gira blackbox_exporter non riesce a risolvere il DNS del target. Comune in ambienti Docker (DNS interno) o quando `/etc/resolv.conf` punta a un resolver non raggiungibile.

**Soluzione**:
```yaml
# blackbox.yml — specificare un DNS resolver esplicito
modules:
  http_2xx_custom_dns:
    prober: http
    timeout: 10s
    http:
      preferred_ip_protocol: ip4
      ip_protocol_fallback: false
    dns:
      transport_protocol: udp
      preferred_ip_protocol: ip4
      query_name: "target.example.com"

# In Docker Compose, assicurarsi che il container abbia accesso DNS
services:
  blackbox:
    image: prom/blackbox-exporter:latest
    dns:
      - 8.8.8.8
      - 1.1.1.1
    # oppure usare la rete host
    # network_mode: host
```

```promql
# Query diagnostiche
probe_dns_lookup_time_seconds{job="blackbox"}  # tempo DNS
probe_success{job="blackbox"} == 0             # probe fallite
probe_http_status_code{job="blackbox"}          # codice HTTP (0 = no connection)
```

**Verifica rapida**: `docker exec blackbox nslookup target.example.com` per confermare la risoluzione DNS dall'interno del container.

> **Fonte**: github.com/prometheus/blackbox_exporter — retrieved 2026-05-23

### Problema: Federation che tira metriche raw causando esplosione di performance

**Sintomi**: Il Prometheus federante ha memoria e CPU elevati, scrape lenti (>30s), timeout frequenti su `/federate`.

**Causa**: L'endpoint `/federate` viene chiamato senza `match[]` sufficientemente selettivi, causando il pull di centinaia di migliaia di serie dal Prometheus federato.

**Soluzione**:
```yaml
# SBAGLIATO — tira TUTTO (performance bomb)
scrape_configs:
  - job_name: 'federate-bad'
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{__name__=~".+"}'   # MAI fare questo
    static_configs:
      - targets: ['prometheus-remote:9090']

# CORRETTO — selezionare solo le metriche aggregate necessarie
scrape_configs:
  - job_name: 'federate-good'
    honor_labels: true
    metrics_path: '/federate'
    scrape_interval: 60s       # intervallo più lungo per federation
    scrape_timeout: 30s
    params:
      'match[]':
        - '{__name__=~"job:.*"}'              # solo recording rules aggregate
        - '{__name__="up"}'                     # health check
        - '{__name__=~".*:.*_total"}'           # metriche pre-aggregate
    static_configs:
      - targets: ['prometheus-remote:9090']
```

**Regola d'oro della federation**: Federare solo recording rules pre-aggregate, mai metriche raw. Se servono tutte le metriche raw, usare `remote_write` verso uno storage centralizzato (Thanos, Mimir).

```promql
# Monitorare la dimensione della risposta federate
scrape_series_added{job="federate-good"}
scrape_samples_scraped{job="federate-good"}
scrape_duration_seconds{job="federate-good"}
```

> **Fonte**: prometheus.io/docs/prometheus/latest/federation/ — retrieved 2026-05-23

### Problema: Grafana plugin incompatibilità dopo upgrade

**Sintomi**: Dopo un aggiornamento di Grafana, alcune dashboard mostrano errori "Panel plugin not found", pannelli vuoti, o la UI non carica.

**Causa**: Plugin di terze parti non compatibili con la nuova major version di Grafana. Le API dei plugin cambiano tra major release (es. da Angular a React panel SDK).

**Soluzione**:
```bash
# 1. Verificare i plugin installati e la compatibilità
grafana cli plugins ls

# 2. Aggiornare tutti i plugin
grafana cli plugins update-all

# 3. Se un plugin non ha una versione compatibile, rimuoverlo
grafana cli plugins remove <plugin-id>

# 4. Cercare alternative compatibili
grafana cli plugins list-remote --page 1

# 5. Controllare i log per errori specifici
journalctl -u grafana-server | grep -i "plugin"
```

**Strategia di upgrade sicura**:
```bash
# Pre-upgrade checklist
# 1. Backup del database Grafana
cp /var/lib/grafana/grafana.db /backup/grafana-$(date +%F).db

# 2. Backup delle dashboard come JSON
for uid in $(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:3000/api/search | jq -r '.[].uid'); do
  curl -s -H "Authorization: Bearer $TOKEN" \
    "http://localhost:3000/api/dashboards/uid/$uid" \
    > "/backup/dashboards/${uid}.json"
done

# 3. Testare in ambiente staging con la stessa versione target
# 4. Verificare la matrice di compatibilità dei plugin su grafana.com
# 5. Solo dopo, procedere con l'upgrade in produzione
```

> **Fonte**: grafana.com/docs/grafana/latest/setup-grafana/upgrade-grafana/ — retrieved 2026-05-23

### Problema: Time series stale dopo rimozione di un target

**Sintomi**: Serie temporali di target rimossi continuano a comparire nelle query per ~5 minuti, poi scompaiono. In alcuni casi, alert basati su `absent()` non scattano immediatamente.

**Causa**: Prometheus utilizza un meccanismo di **staleness** (introdotto in v2.0): quando un target viene rimosso o una serie non viene più esposta, Prometheus inserisce un **stale marker** (NaN speciale) alla prossima valutazione dello scrape. Le serie rimangono "attive" per il lookback delta (default 5 minuti).

**Soluzione**:
```promql
# Le query istantanee rispettano il lookback delta (5m default)
# Per verificare se una serie è davvero stale:
timestamp(up{job="removed-job"})
# Se il timestamp è vecchio > 5m, la serie è stale

# absent() rispetta lo staleness — scatta dopo il lookback delta
# Per reazione più rapida, usare un for più breve:
- alert: TargetDown
  expr: up{job="critical-service"} == 0
  for: 1m    # più reattivo di absent()
```

```yaml
# Controllare il lookback delta (NON modificare in produzione senza motivo)
# Flag di avvio:
# --query.lookback-delta=5m   (default, raramente da cambiare)

# Per cleanup immediato di serie orfane (API admin, richiede --web.enable-admin-api):
# POST http://localhost:9090/api/v1/admin/tsdb/clean_tombstones
# DELETE http://localhost:9090/api/v1/series?match[]=up{job="removed-job"}
```

**Attenzione**: L'API `delete series` rimuove i dati dallo storage ma non influenza il meccanismo di staleness. Il lookback delta è il comportamento corretto — evita falsi positivi durante scrape temporaneamente falliti. Non ridurlo sotto i 5 minuti senza comprendere le conseguenze sugli alert.

> **Fonte**: prometheus.io/docs/prometheus/latest/querying/basics/#staleness — retrieved 2026-05-23

---

## Esercizi Pratici

### Esercizio 1: Setup Base

**Obiettivo**: Installare Prometheus, node_exporter e Grafana su una macchina locale.

**Passi**:
1. Installare Prometheus e node_exporter seguendo le istruzioni di questo capitolo
2. Configurare Prometheus per scrapare node_exporter
3. Verificare che le metriche appaiano in Prometheus UI
4. Installare Grafana e configurare il data source Prometheus
5. Importare la dashboard Node Exporter Full (ID 1860)

**Verifica**: La dashboard mostra CPU, memoria, disco e rete della macchina locale.

### Esercizio 2: PromQL Hands-On

**Obiettivo**: Padroneggiare le query PromQL fondamentali.

**Passi**:
1. Calcolare l'uso CPU per ciascun core separatamente
2. Calcolare la memoria usata in percentuale
3. Calcolare il rate di I/O disco in MB/s
4. Creare una query che predica quando il disco sarà pieno
5. Usare `histogram_quantile` per calcolare p50, p90, p99 (richiede un'app con histogram)

**Verifica**: Le query restituiscono risultati coerenti con `top`, `free -m`, `iostat`.

### Esercizio 3: Alerting Pipeline Completo

**Obiettivo**: Configurare un pipeline di alerting end-to-end.

**Passi**:
1. Configurare Alertmanager con almeno un receiver email (o webhook per test)
2. Creare alerting rules per: CPU > 80%, memoria > 90%, disco > 85%
3. Creare inhibition rules (critical inibisce warning)
4. Testare con stress tool: `stress --cpu 4 --timeout 10m`
5. Verificare che l'alert arrivi alla destinazione configurata
6. Creare un silence e verificare che l'alert venga soppresso

**Verifica**: L'alert viene generato, ruotato, notificato e poi soppresso dal silence.

### Esercizio 4: Dashboard Personalizzata

**Obiettivo**: Creare una dashboard Grafana da zero con variabili e multi-pannello.

**Passi**:
1. Creare una variabile `instance` che popola dai target Prometheus
2. Creare pannelli: time series (CPU), gauge (memoria), stat (uptime), tabella (filesystem)
3. Aggiungere threshold di colore su ogni pannello
4. Aggiungere una annotation query per visualizzare i riavvii del target
5. Esportare la dashboard come JSON e reimportarla

**Verifica**: La dashboard è funzionale con il selettore di variabili, tutti i pannelli mostrano dati corretti.

### Esercizio 5: Docker Compose Stack

**Obiettivo**: Deployare lo stack completo di monitoring con Docker Compose.

**Passi**:
1. Utilizzare il `docker-compose.monitoring.yml` di questo capitolo
2. Aggiungere un'applicazione di test che espone metriche `/metrics`
3. Configurare Grafana provisioning per data source e dashboard
4. Configurare Alertmanager con un webhook receiver
5. Eseguire `docker compose up -d` e verificare tutti i componenti

**Verifica**: Tutti i container sono running, Prometheus scrape tutti i target, Grafana mostra le dashboard provisionate.

### Esercizio 6: Blackbox Probing

**Obiettivo**: Configurare blackbox_exporter per verificare la disponibilità di endpoint HTTP.

**Passi**:
1. Configurare blackbox_exporter con moduli HTTP, TCP e ICMP
2. Aggiungere target di probe in Prometheus con relabel_configs appropriati
3. Creare alert per endpoint non raggiungibili o con latenza alta
4. Creare una dashboard che mostri uptime, latenza e status code per ogni target

**Verifica**: I probe restituiscono metriche corrette, gli alert scattano quando un endpoint è irraggiungibile.

### Esercizio 7: Recording Rules e Ottimizzazione

**Obiettivo**: Ottimizzare le performance delle query con recording rules.

**Passi**:
1. Identificare 3 query lente nelle dashboard (usare Query Inspector di Grafana)
2. Creare recording rules per ciascuna
3. Aggiornare le dashboard per usare le recording rules
4. Confrontare i tempi di esecuzione prima e dopo
5. Validare le regole con `promtool check rules`

**Verifica**: Le query nelle dashboard sono più veloci dopo l'introduzione delle recording rules.

### Esercizio 8: SLO-Based Alerting

**Obiettivo**: Implementare alert basati su SLO con il metodo multi-window multi-burn-rate.

**Passi**:
1. Definire un SLO (es. 99.9% availability)
2. Creare recording rules per error ratio su finestre 5m, 30m, 1h, 6h
3. Creare alert con burn rate 14.4x (critical) e 6x (warning)
4. Simulare errori e verificare che gli alert scattino al tasso corretto
5. Creare una dashboard SLO con error budget rimanente

**Verifica**: Gli alert scattano proporzionalmente al burn rate, non a soglie fisse arbitrarie.

---

## Autovalutazione

### Domande di Comprensione

1. Quale è la differenza fondamentale tra il modello pull di Prometheus e il modello push di sistemi come Graphite/StatsD?

2. Un counter Prometheus mostra il valore 50000. Cosa significa questo valore da solo? Perché si usa `rate()` sui counter?

3. Spiegare la differenza tra `rate()` e `irate()`. In quale contesto ciascuna è preferibile?

4. Un histogram Prometheus ha i seguenti bucket: le=0.1, le=0.5, le=1.0, le=+Inf. Come funziona `histogram_quantile(0.95, ...)` internamente? Quali sono i limiti di precisione?

5. Che differenza c'è tra `relabel_configs` e `metric_relabel_configs`? Quando si usa ciascuna?

6. Come funziona il WAL di Prometheus? Cosa succede se Prometheus crasha prima che i dati siano persistiti in un blocco?

7. Perché la cardinalità è il nemico numero uno delle performance di Prometheus? Fornire un esempio di label ad alta cardinalità e come risolverlo.

8. In un cluster Alertmanager, come vengono evitate le notifiche duplicate? Che ruolo gioca il gossip protocol?

9. Qual è la differenza tra Thanos e Mimir? Quando scegliere l'uno o l'altro?

10. Spiegare il concetto di "burn rate" nell'alerting SLO. Perché un burn rate di 14.4x corrisponde a un consumo del budget in ~2 giorni per un SLO mensile?

11. Perché non si deve usare il Pushgateway per servizi long-running?

12. Cos'è il `for` nelle alerting rules e perché è fondamentale per prevenire false notifiche?

13. Descrivere il metodo RED e il metodo USE. Per quali tipi di risorse/servizi è indicato ciascuno?

14. Come si implementa lo sharding orizzontale di Prometheus con `hashmod`?

15. Un dashboard Grafana è lento. Elencare almeno 5 possibili cause e le relative soluzioni.

### Risposte Sintetiche

1. **Pull vs Push**: Prometheus interroga attivamente i target (pull). Il vantaggio è che Prometheus controlla il ritmo, può rilevare target down (metrica `up`), e non necessita di agent sui target che conoscano l'indirizzo del server di monitoring.

2. **Counter**: Il valore assoluto 50000 è il conteggio cumulativo dall'avvio del processo. Da solo non dice nulla di utile. `rate()` calcola l'incremento per secondo, trasformandolo in "quante richieste al secondo" — l'informazione operativa reale.

3. **rate vs irate**: `rate()` media su tutto il range (stabile, adatto per alert). `irate()` usa solo gli ultimi 2 punti (reattiva, adatta per grafici real-time). Mai usare `irate()` negli alert.

4. **histogram_quantile**: Identifica il bucket che contiene il 95-esimo percentile tramite interpolazione lineare. La precisione dipende dalla granularità dei bucket — con pochi bucket, il quantile calcolato può essere significativamente diverso dal reale.

5. **relabel vs metric_relabel**: `relabel_configs` opera sui target PRIMA dello scrape (filtra/modifica target). `metric_relabel_configs` opera sulle metriche DOPO lo scrape (filtra/modifica metriche raccolte).

6. **WAL**: Scritte append-only su disco prima dell'elaborazione in memoria. Al crash, il WAL viene riletto (replay) per ricostruire lo stato. I dati nel WAL non ancora persistiti in blocco vengono recuperati.

7. **Cardinalità**: Ogni combinazione unica di label crea una serie separata in memoria. Una label `user_id` con 1M utenti crea 1M serie. Soluzione: rimuovere la label o aggregare lato applicazione.

8. **Alertmanager HA**: Le istanze comunicano via gossip protocol (mesh), condividendo lo stato degli alert e dei silence. Solo un'istanza invia effettivamente la notifica per ogni gruppo di alert.

9. **Thanos vs Mimir**: Thanos estende Prometheus esistenti (sidecar), mantiene l'architettura pull. Mimir è un backend separato con ingest via remote_write, nativo multi-tenant. Thanos per chi ha già Prometheus; Mimir per chi vuole un backend centralizzato multi-tenant.

10. **Burn rate**: SLO mensile 99.9% = 0.1% error budget = ~43 minuti/mese di downtime. Burn rate 1 = consumo lineare (tutto il budget in 30 giorni). Burn rate 14.4 = 30/14.4 ≈ 2.08 giorni per esaurire il budget.

---

## Letture Consigliate e Cross-Link

### Moduli Correlati nella Libreria

- **Modulo 12 — Systemd e Gestione Servizi**: Per la configurazione dei service unit di Prometheus, Alertmanager e node_exporter
- **Modulo 20 — Networking TCP/IP**: Per la comprensione delle probe di rete con blackbox_exporter
- **Modulo 25 — Docker e Container**: Per il deployment dello stack con Docker Compose
- **Modulo 28 — Kubernetes (se presente)**: Per Prometheus Operator, ServiceMonitor e PodMonitor
- **Modulo 15 — Sicurezza**: Per TLS, autenticazione e RBAC

### Testi di Riferimento

- **"Prometheus: Up & Running"** — Brian Brazil (O'Reilly, 2a edizione). Il riferimento definitivo per Prometheus, scritto dal co-founder del progetto
- **"Site Reliability Engineering"** — Google (O'Reilly). Capitoli su monitoring, alerting e SLO
- **"The Site Reliability Workbook"** — Google (O'Reilly). Capitolo 5: Alerting on SLOs — la base teorica per multi-window multi-burn-rate
- **"Observability Engineering"** — Charity Majors et al. (O'Reilly). Monitoring vs observability, tre pilastri (metriche, log, trace)

### Risorse Online

- CNCF Prometheus Project: https://www.cncf.io/projects/prometheus/ (consultato: 2026-05-23)
- OpenMetrics Specification: https://openmetrics.io/ (consultato: 2026-05-23)
- Grafana Play (demo interattiva): https://play.grafana.org/ (consultato: 2026-05-23)
- Awesome Prometheus Alerts (regole community): https://awesome-prometheus-alerts.grep.to/ (consultato: 2026-05-23)
- PromLens (visual PromQL builder): https://promlens.com/ (consultato: 2026-05-23)
- Thanos Design Document: https://thanos.io/tip/thanos/design.md/ (consultato: 2026-05-23)

---

## Riferimenti

- **Prometheus Documentation**: https://prometheus.io/docs/
- **PromQL Guide**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Alertmanager Documentation**: https://prometheus.io/docs/alerting/latest/alertmanager/
- **Grafana Documentation**: https://grafana.com/docs/grafana/latest/
- **Awesome Prometheus Alerts**: https://awesome-prometheus-alerts.grep.to/ — collection di alerting rules
- **Grafana Dashboard Library**: https://grafana.com/grafana/dashboards/
- **Prometheus: Up & Running (O'Reilly)**: https://www.oreilly.com/library/view/prometheus-up/9781492034131/
- **node_exporter**: https://github.com/prometheus/node_exporter
- **blackbox_exporter**: https://github.com/prometheus/blackbox_exporter

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **Burn Rate** | Velocità con cui si consuma l'error budget di un SLO. Burn rate 1 = consumo lineare del budget nell'intero periodo SLO |
| **Cardinalità** | Numero di combinazioni uniche di nome metrica + set di label. Determina l'uso di memoria di Prometheus |
| **Compaction** | Processo background che fonde blocchi TSDB più piccoli in blocchi più grandi, migliorando performance e pulizia |
| **Counter** | Tipo di metrica Prometheus monotonicamente crescente. Si resetta solo al riavvio del processo. Usare `rate()` per ottenere il tasso di crescita |
| **CRD** | Custom Resource Definition. In Kubernetes, estensione dell'API per definire risorse custom come ServiceMonitor e PrometheusRule |
| **Error Budget** | Quantità di errori ammissibili in un periodo, derivata dallo SLO. Es. SLO 99.9% = 0.1% error budget |
| **Exporter** | Componente che espone metriche in formato Prometheus da un sistema che non le espone nativamente |
| **Federation** | Meccanismo per cui un Prometheus scrape dati aggregati da altri Prometheus |
| **Gauge** | Tipo di metrica Prometheus con valore variabile (può salire e scendere). Rappresenta lo stato corrente |
| **Gossip Protocol** | Protocollo di comunicazione peer-to-peer usato da Alertmanager in cluster per la deduplicazione |
| **Grafonnet** | Libreria Jsonnet per generare dashboard Grafana programmaticamente (dashboard-as-code) |
| **Head Block** | Il blocco TSDB attivo in memoria dove vengono scritti i campioni recenti prima della persistenza su disco |
| **Histogram** | Tipo di metrica che traccia la distribuzione di valori in bucket cumulativi. Permette il calcolo dei quantili con `histogram_quantile()` |
| **Inhibition** | Meccanismo di Alertmanager che sopprime alert di severity inferiore quando un alert di severity superiore è attivo per la stessa risorsa |
| **Instant Vector** | Set di time series con un singolo campione per serie, tutti allo stesso timestamp |
| **Label** | Coppia chiave-valore associata a una metrica. Identifica univocamente una time series |
| **Mimir** | Backend di storage long-term per metriche Prometheus, sviluppato da Grafana Labs. Successore di Cortex |
| **OpenMetrics** | Standard CNCF per il formato di exposition delle metriche, evoluzione del formato text di Prometheus |
| **PodMonitor** | CRD del Prometheus Operator per definire target di scrape basati su pod Kubernetes |
| **PromQL** | Prometheus Query Language. Linguaggio funzionale per query su time series |
| **Provisioning** | Configurazione automatica di Grafana (datasource, dashboard, alert) all'avvio senza intervento manuale |
| **Pushgateway** | Intermediario che riceve metriche push da job batch e le espone per lo scrape di Prometheus |
| **Range Vector** | Set di time series con una sequenza di campioni per serie, coprendo un intervallo temporale |
| **Recording Rule** | Query PromQL pre-calcolata il cui risultato viene salvato come nuova time series per migliorare le performance |
| **RED Method** | Framework di monitoring per servizi: Rate, Errors, Duration |
| **Relabeling** | Meccanismo per trasformare, filtrare o modificare label durante lo scrape |
| **Remote Write** | Interfaccia Prometheus per inviare campioni a backend di storage esterni in tempo reale |
| **Scrape** | Processo con cui Prometheus raccoglie metriche da un target via HTTP GET /metrics |
| **Service Discovery** | Meccanismo automatico per scoprire target da monitorare (Consul, Kubernetes, file, EC2...) |
| **ServiceMonitor** | CRD del Prometheus Operator per definire target di scrape basati su servizi Kubernetes |
| **Silence** | Regola temporanea in Alertmanager che sopprime le notifiche per alert che matchano determinati criteri |
| **SLO** | Service Level Objective. Obiettivo misurabile di affidabilità (es. 99.9% availability) |
| **Summary** | Tipo di metrica che calcola quantili lato client. Non aggregabile tra istanze, preferire histogram |
| **Thanos** | Progetto CNCF che estende Prometheus con global query, HA, e storage a lungo termine su object store |
| **TSDB** | Time Series Database. Il motore di storage locale di Prometheus |
| **USE Method** | Framework di monitoring per risorse: Utilization, Saturation, Errors |
| **WAL** | Write-Ahead Log. Registro append-only su disco per garantire la durabilità dei dati in caso di crash |
