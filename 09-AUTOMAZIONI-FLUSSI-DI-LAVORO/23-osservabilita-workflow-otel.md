---
corso: "Automazioni e Flussi di Lavoro"
fase: "5 — Pattern Avanzati"
modulo: 23
titolo: "Osservabilita dei Workflow con OpenTelemetry"
versione: "OpenTelemetry 1.x (GA), OTLP HTTP/gRPC, OTel Collector 0.95+"
livello: "proficient"
prerequisiti: ["Modulo 04 — Integrazione API", "Modulo 12 — Temporal/Prefect", "Modulo 16 — Event-Driven Architecture", "Distributed tracing, metrics, logs"]
obiettivi:
  - "Instrumentare workflow con OTel SDK per generare trace, metriche e log strutturati"
  - "Configurare OTLP export verso backend (Jaeger, Grafana Tempo, Elasticsearch) tramite OTel Collector"
  - "Correlare traces, logs e metrics per diagnosticare failure end-to-end nei workflow distribuiti"
  - "Definire SLI/SLO per workflow di automazione e configurare alerting su violazioni"
  - "Implementare context propagation tra servizi e piattaforme eterogenee (n8n, Temporal, code-based)"
tag: [opentelemetry, otel, observability, tracing, metrics, logs, otlp, sli-slo, grafana]
---

# Osservabilita dei Workflow con OpenTelemetry

> **Obiettivi di apprendimento**
> 1. Instrumentare workflow con OTel SDK per generare trace, metriche e log strutturati
> 2. Configurare OTLP export verso backend (Jaeger, Grafana Tempo, Elasticsearch) tramite OTel Collector
> 3. Correlare traces, logs e metrics per diagnosticare failure end-to-end nei workflow distribuiti
> 4. Definire SLI/SLO per workflow di automazione e configurare alerting su violazioni
> 5. Implementare context propagation tra servizi e piattaforme eterogenee (n8n, Temporal, code-based)

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 4-5 · Modulo 23 (nuovo)
> **Prerequisiti:** Moduli 04, 12, 16; concetti distributed tracing, metrics, logs.
> **Obiettivi:** instrumentare workflow con OTel SDK; OTLP export; correlazione traces ↔ logs ↔ metrics.
> **Tempo:** lettura 60 min · lab 240 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-24
> **Versioni:** OpenTelemetry 1.x (GA), OTLP HTTP/gRPC, OTel Collector 0.95+.

---

## Indice

1. [Idee guida](#idee-guida)
2. [Architettura dell'osservabilita per workflow](#architettura-dellosservabilita-per-workflow)
3. [I tre pilastri: traces, metrics, logs](#i-tre-pilastri-traces-metrics-logs)
4. [OpenTelemetry SDK — setup completo](#opentelemetry-sdk--setup-completo)
5. [Distributed tracing attraverso catene di automazione](#distributed-tracing-attraverso-catene-di-automazione)
6. [Propagazione del contesto via webhook e code](#propagazione-del-contesto-via-webhook-e-code)
7. [Integrazione Temporal](#integrazione-temporal)
8. [Integrazione Prefect](#integrazione-prefect)
9. [Integrazione Apache Airflow](#integrazione-apache-airflow)
10. [Metriche custom per la salute dei workflow](#metriche-custom-per-la-salute-dei-workflow)
11. [OTel Collector — configurazione avanzata](#otel-collector--configurazione-avanzata)
12. [Correlazione log attraverso gli step del workflow](#correlazione-log-attraverso-gli-step-del-workflow)
13. [Dashboard Grafana per workflow monitoring](#dashboard-grafana-per-workflow-monitoring)
14. [Alerting su SLO dei workflow](#alerting-su-slo-dei-workflow)
15. [Error tracking e root cause analysis](#error-tracking-e-root-cause-analysis)
16. [Ottimizzazione delle prestazioni usando le trace](#ottimizzazione-delle-prestazioni-usando-le-trace)
17. [Cost observability per workflow](#cost-observability-per-workflow)
18. [Observability-driven development per automazioni](#observability-driven-development-per-automazioni)
19. [Sampling strategies avanzate](#sampling-strategies-avanzate)
20. [Esercizi](#esercizi)
21. [Troubleshooting — 18 problemi comuni](#troubleshooting--18-problemi-comuni)
22. [FAQ — 18 domande e risposte](#faq--18-domande-e-risposte)
23. [Auto-valutazione](#auto-valutazione)
24. [Letture primarie consigliate](#letture-primarie-consigliate)
25. [Collegamenti incrociati](#collegamenti-incrociati)
26. [Glossario locale](#glossario-locale)

---

## Idee guida

1. **Three pillars: traces, metrics, logs. Tutti correlati via trace_id.**
2. **OTel = vendor-neutral.** Backend swappable: Jaeger, Tempo, Datadog, Splunk, Honeycomb.
3. **Sampling head-based per costo, tail-based per qualita.** Tail vede l'errore prima di decidere.
4. **W3C Trace Context propagato attraverso webhook + queue.** Fondamentale per correlazione.
5. **Semantic conventions.** Standard naming permette dashboard cross-vendor.
6. **Ogni workflow step e uno span.** La trace descrive l'intera esecuzione end-to-end.
7. **Metriche custom = SLI misurabili.** Senza metriche, gli SLO sono opinioni.
8. **Cost observability come pilastro aggiuntivo.** Sapere quanto costa ogni workflow permette ottimizzazione.
9. **Observability-driven development.** Prima instrumenti, poi scrivi la logica; non il contrario.
10. **Alert su SLO, non su sintomi.** Un CPU alto non e un problema; un workflow fuori SLO si.

---

## Architettura dell'osservabilita per workflow

### Il problema: workflow distribuiti opachi

Un workflow di automazione tipico attraversa multipli servizi, code, API esterne e database. Senza osservabilita strutturata:

- Non sai dove un workflow si e bloccato.
- Non sai perche un workflow impiega 3x il tempo previsto.
- Non sai quanto costa ogni esecuzione.
- Non sai se un fallimento e isolato o sistemico.
- Non puoi dimostrare il rispetto degli SLO.

### Architettura di riferimento

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Workflow Engine                               │
│  (Temporal / Prefect / Airflow / n8n / custom)                      │
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Step A   │→│  Step B   │→│  Step C   │→│  Step D   │           │
│  │  span_a   │  │  span_b   │  │  span_c   │  │  span_d   │       │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘           │
│        │              │              │              │                 │
│        └──────────────┴──────────────┴──────────────┘                │
│                              │                                       │
│                    ┌─────────▼─────────┐                            │
│                    │    OTel SDK         │                            │
│                    │  traces + metrics   │                            │
│                    │  + structured logs  │                            │
│                    └─────────┬─────────┘                            │
└──────────────────────────────┼──────────────────────────────────────┘
                               │ OTLP (gRPC/HTTP)
                    ┌──────────▼──────────┐
                    │   OTel Collector     │
                    │  ┌────────────────┐  │
                    │  │  processors:    │  │
                    │  │  - batch        │  │
                    │  │  - tail_sampling│  │
                    │  │  - attributes   │  │
                    │  │  - filter       │  │
                    │  └────────────────┘  │
                    └──────┬───┬───┬──────┘
                           │   │   │
              ┌────────────┘   │   └────────────┐
              ▼                ▼                  ▼
     ┌────────────┐   ┌────────────┐   ┌────────────────┐
     │   Tempo /   │   │ Prometheus │   │     Loki /     │
     │   Jaeger    │   │  / Mimir   │   │  Elasticsearch │
     │  (traces)   │   │ (metrics)  │   │    (logs)      │
     └──────┬─────┘   └─────┬─────┘   └───────┬────────┘
            │                │                  │
            └────────────────┼──────────────────┘
                             │
                    ┌────────▼────────┐
                    │     Grafana      │
                    │  traces↔metrics  │
                    │   ↔logs unified  │
                    └─────────────────┘
```

### Principi architetturali

**Separazione dei concern.** L'applicazione genera telemetria via SDK; il Collector la processa e la instrada. L'applicazione non deve conoscere il backend di destinazione.

**Protocollo unico: OTLP.** Tutti e tre i segnali (traces, metrics, logs) viaggiano sullo stesso protocollo. Questo semplifica la configurazione di rete (un solo endpoint, una sola porta).

**Collector come gateway.** Il Collector funge da proxy: accetta telemetria, la arricchisce (aggiungendo attributi come `environment`, `service.version`), la campiona, la esporta verso N backend. Cambiare backend = cambiare configurazione del Collector, non il codice applicativo.

**Correlazione nativa.** Ogni log emesso durante l'esecuzione di uno span porta automaticamente il `trace_id` e lo `span_id`. Grafana (o qualsiasi frontend) puo navigare da una trace a tutti i log correlati e viceversa.

### Flusso dati end-to-end

```
Workflow step genera span
       │
       ├── span.set_attribute("workflow.name", "etl_daily")
       ├── span.set_attribute("workflow.run_id", "abc-123")
       ├── span.add_event("record_processed", count=500)
       │
       ▼
SDK raccoglie span + metrics + logs
       │
       ▼ OTLP export (batch, async, retry built-in)
       │
OTel Collector riceve
       │
       ├── processor/batch: raggruppa per efficienza
       ├── processor/attributes: aggiunge env, region
       ├── processor/tail_sampling: mantiene 100% errori, 10% successi
       │
       ▼
Backend storage (Tempo, Prometheus, Loki)
       │
       ▼
Grafana query + dashboard + alerting
```

### Componenti necessari — checklist

| Componente | Ruolo | Obbligatorio |
|---|---|---|
| OTel SDK (Python/Go/Java/...) | Generazione telemetria | Si |
| OTel Collector | Processing + routing | Si (produzione) |
| Backend traces (Tempo/Jaeger) | Storage trace | Si |
| Backend metrics (Prometheus/Mimir) | Storage metriche | Si |
| Backend logs (Loki/ES) | Storage log strutturati | Si |
| Grafana | Visualizzazione unificata | Si |
| Alertmanager | Notifiche SLO violation | Si (produzione) |

---

## I tre pilastri: traces, metrics, logs

### Traces

Una trace rappresenta l'esecuzione end-to-end di un workflow. E composta da span, ciascuno rappresentante un'operazione (uno step del workflow, una chiamata API, una query database).

```
trace_id: abc123
├── span: workflow_execution (root)
│   ├── span: fetch_data          (120ms)
│   ├── span: transform_records   (450ms)
│   │   ├── span: validate        (30ms)
│   │   └── span: enrich          (420ms)
│   │       └── span: api_call    (380ms)  ← bottleneck
│   ├── span: load_to_warehouse   (200ms)
│   └── span: send_notification   (50ms)
```

Ogni span contiene:

| Campo | Tipo | Esempio |
|---|---|---|
| `trace_id` | string (32 hex) | `abc123def456...` |
| `span_id` | string (16 hex) | `1a2b3c4d...` |
| `parent_span_id` | string | `00000000...` (root) |
| `name` | string | `transform_records` |
| `kind` | enum | `INTERNAL`, `CLIENT`, `SERVER` |
| `start_time` | timestamp | `2026-05-22T10:15:30.123Z` |
| `end_time` | timestamp | `2026-05-22T10:15:30.573Z` |
| `status` | enum | `OK`, `ERROR`, `UNSET` |
| `attributes` | key-value | `workflow.name=etl_daily` |
| `events` | list | `[{name: "exception", ...}]` |

### Metrics

Le metriche sono misure numeriche aggregate nel tempo. OTel definisce tre tipi principali:

| Tipo | Uso | Esempio workflow |
|---|---|---|
| **Counter** | Conta eventi monotoni | `workflow.executions.total` |
| **Histogram** | Distribuzione valori | `workflow.duration.seconds` |
| **Gauge** | Valore puntuale | `workflow.queue.depth` |

Le metriche sono complementari alle trace: le trace mostrano cosa e successo in una specifica esecuzione, le metriche mostrano il trend aggregato.

### Logs

I log strutturati arricchiti con `trace_id` e `span_id` sono il collante tra i tre pilastri. Un log emesso durante l'esecuzione di uno span eredita automaticamente il contesto di tracing.

```json
{
  "timestamp": "2026-05-22T10:15:30.450Z",
  "severity": "ERROR",
  "body": "API esterna ha restituito 503",
  "trace_id": "abc123def456",
  "span_id": "1a2b3c4d",
  "attributes": {
    "workflow.name": "etl_daily",
    "workflow.run_id": "run-789",
    "step.name": "enrich",
    "http.status_code": 503,
    "http.url": "https://api.partner.com/v2/enrich"
  }
}
```

### Correlazione tra pilastri

```
                    ┌─────────────────────┐
                    │      Grafana         │
                    │                      │
        ┌──────────┤  Dashboard workflow   │──────────┐
        │          └──────────────────────┘          │
        │                    │                        │
        ▼                    ▼                        ▼
   ┌─────────┐        ┌──────────┐            ┌───────────┐
   │ Metrics  │  ───── │  Traces   │ ────────  │   Logs     │
   │         │ trace_id│          │ trace_id   │           │
   │ counter  │ exemplar│ span tree │ span_id   │ structured │
   │histogram │        │ waterfall │           │ JSON lines │
   └─────────┘        └──────────┘            └───────────┘
```

La navigazione e bidirezionale:

1. **Metrica anomala** → clicca sull'exemplar → apri la trace corrispondente → vedi gli span → clicca sullo span → vedi i log.
2. **Log di errore** → estrai `trace_id` → apri la trace → vedi il contesto completo.
3. **Trace lenta** → leggi gli attributi → pivot sulle metriche dell'endpoint lento.

---

## OpenTelemetry SDK — setup completo

### Installazione dipendenze Python

```bash
pip install \
  opentelemetry-api==1.27.0 \
  opentelemetry-sdk==1.27.0 \
  opentelemetry-exporter-otlp-proto-http==1.27.0 \
  opentelemetry-exporter-otlp-proto-grpc==1.27.0 \
  opentelemetry-instrumentation-requests==0.48b0 \
  opentelemetry-instrumentation-logging==0.48b0
```

### Setup traces (dal contenuto originale, espanso)

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

# Definisci la risorsa (identita del servizio)
resource = Resource.create({
    SERVICE_NAME: "workflow-engine",
    SERVICE_VERSION: "2.1.0",
    "deployment.environment": "production",
    "service.namespace": "automazioni",
})

# Configura il TracerProvider
provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(
        OTLPSpanExporter(endpoint="https://otel-collector:4318/v1/traces"),
        max_queue_size=2048,
        max_export_batch_size=512,
        schedule_delay_millis=5000,
    )
)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# Utilizzo: ogni step del workflow e uno span
with tracer.start_as_current_span("process_webhook") as span:
    span.set_attribute("webhook.source", "stripe")
    span.set_attribute("webhook.event_id", event_id)
    # ... processing
```

### Setup metrics

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter

metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint="https://otel-collector:4318/v1/metrics"),
    export_interval_millis=30000,  # 30 secondi
)

meter_provider = MeterProvider(
    resource=resource,  # stessa risorsa dei traces
    metric_readers=[metric_reader],
)
metrics.set_meter_provider(meter_provider)

meter = metrics.get_meter(__name__)

# Definisci strumenti
workflow_executions = meter.create_counter(
    name="workflow.executions.total",
    description="Numero totale di esecuzioni workflow",
    unit="1",
)
workflow_duration = meter.create_histogram(
    name="workflow.duration.seconds",
    description="Durata esecuzione workflow",
    unit="s",
)
workflow_queue_depth = meter.create_up_down_counter(
    name="workflow.queue.depth",
    description="Profondita corrente della coda workflow",
    unit="1",
)
```

### Setup structured logging con trace context

```python
import logging
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Inietta trace_id e span_id in ogni log record
LoggingInstrumentor().instrument(set_logging_format=True)

# Configura formato JSON strutturato
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "severity": record.levelname,
            "body": record.getMessage(),
            "logger": record.name,
            "trace_id": getattr(record, "otelTraceID", ""),
            "span_id": getattr(record, "otelSpanID", ""),
            "trace_flags": getattr(record, "otelTraceFlagsSampled", ""),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.INFO)
```

### Combinazione completa: workflow instrumentato

```python
import time
import logging

from opentelemetry import trace, metrics
from opentelemetry.trace import StatusCode

logger = logging.getLogger("workflow.etl")
tracer = trace.get_tracer("workflow.etl")
meter = metrics.get_meter("workflow.etl")

# Metriche
exec_counter = meter.create_counter("workflow.executions.total")
duration_hist = meter.create_histogram("workflow.duration.seconds")
error_counter = meter.create_counter("workflow.errors.total")
records_processed = meter.create_counter("workflow.records.processed")

def run_etl_workflow(config: dict) -> None:
    """Esegue il workflow ETL con observability completa."""
    start = time.monotonic()
    attributes = {
        "workflow.name": "etl_daily",
        "workflow.config.source": config["source"],
        "workflow.config.destination": config["destination"],
    }

    with tracer.start_as_current_span("etl_daily", attributes=attributes) as root:
        root.set_attribute("workflow.run_id", config["run_id"])
        try:
            # Step 1: fetch
            with tracer.start_as_current_span("fetch_data") as fetch_span:
                data = fetch_from_source(config["source"])
                fetch_span.set_attribute("fetch.record_count", len(data))
                logger.info("Dati recuperati", extra={"record_count": len(data)})

            # Step 2: transform
            with tracer.start_as_current_span("transform") as transform_span:
                transformed = transform_records(data)
                transform_span.set_attribute("transform.output_count", len(transformed))
                records_processed.add(len(transformed), {"workflow.name": "etl_daily"})

            # Step 3: load
            with tracer.start_as_current_span("load_to_warehouse") as load_span:
                rows = load_data(transformed, config["destination"])
                load_span.set_attribute("load.rows_inserted", rows)

            # Step 4: notify
            with tracer.start_as_current_span("send_notification"):
                notify_completion(config["notify_channel"])

            exec_counter.add(1, {"workflow.name": "etl_daily", "status": "success"})
            root.set_status(StatusCode.OK)

        except Exception as e:
            root.set_status(StatusCode.ERROR, str(e))
            root.record_exception(e)
            error_counter.add(1, {"workflow.name": "etl_daily", "error.type": type(e).__name__})
            exec_counter.add(1, {"workflow.name": "etl_daily", "status": "error"})
            logger.error("Workflow fallito", exc_info=True)
            raise
        finally:
            duration = time.monotonic() - start
            duration_hist.record(duration, {"workflow.name": "etl_daily"})
```

---

## Distributed tracing attraverso catene di automazione

### Il problema delle catene

Un'automazione complessa raramente e un singolo processo. Una catena tipica:

```
Webhook Stripe  →  n8n workflow  →  Python microservice  →  Database
                                         │
                                         ▼
                                    API esterna  →  Notification service
```

Senza tracing distribuito, ogni componente ha i propri log isolati. Un fallimento nella API esterna appare come timeout nel microservice, errore generico in n8n, e silenzio nel webhook. La root cause e invisibile.

### W3C Trace Context: lo standard

Il W3C Trace Context definisce due header HTTP:

```
traceparent: 00-<trace_id>-<parent_span_id>-<trace_flags>
tracestate:  vendor1=value1,vendor2=value2
```

Esempio concreto:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate:  congo=t61rcWkgMzE
```

- `00` = versione
- `4bf92f3577b34da6a3ce929d0e0e4736` = trace_id (32 hex)
- `00f067aa0ba902b7` = parent_span_id (16 hex)
- `01` = sampled (01=si, 00=no)

### Propagazione in pratica

#### Producer: inietta il contesto

```python
from opentelemetry import trace
from opentelemetry.propagate import inject
import requests

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("send_webhook") as span:
    headers = {}
    inject(headers)  # aggiunge traceparent + tracestate

    span.set_attribute("http.method", "POST")
    span.set_attribute("http.url", "https://service-b.internal/webhook")

    response = requests.post(
        "https://service-b.internal/webhook",
        json=payload,
        headers=headers,
    )
    span.set_attribute("http.status_code", response.status_code)
```

#### Consumer: estrai il contesto e crea child span

```python
from opentelemetry import trace
from opentelemetry.propagate import extract
from flask import Flask, request

app = Flask(__name__)
tracer = trace.get_tracer(__name__)

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    # Estrai contesto W3C dal header
    ctx = extract(request.headers)

    # Crea child span collegato alla trace del producer
    with tracer.start_as_current_span(
        "handle_webhook",
        context=ctx,
        kind=trace.SpanKind.SERVER,
    ) as span:
        event = request.get_json()
        span.set_attribute("webhook.event_type", event["type"])
        span.set_attribute("webhook.source", "stripe")

        process_event(event)
        return {"status": "ok"}, 200
```

### Propagazione attraverso code di messaggi

Le code (RabbitMQ, Kafka, SQS) non supportano nativamente header HTTP. La propagazione richiede l'inserimento del contesto negli attributi del messaggio.

#### Producer — Kafka

```python
from opentelemetry.propagate import inject

def produce_message(topic: str, payload: dict) -> None:
    with tracer.start_as_current_span("kafka_produce", kind=trace.SpanKind.PRODUCER) as span:
        headers = {}
        inject(headers)

        # Kafka headers come lista di tuple (key, value_bytes)
        kafka_headers = [
            (k, v.encode("utf-8")) for k, v in headers.items()
        ]

        span.set_attribute("messaging.system", "kafka")
        span.set_attribute("messaging.destination", topic)
        span.set_attribute("messaging.operation", "publish")

        producer.send(topic, value=payload, headers=kafka_headers)
```

#### Consumer — Kafka

```python
from opentelemetry.propagate import extract

def consume_messages(topic: str) -> None:
    for message in consumer:
        # Ricostruisci header dict da Kafka headers
        carrier = {
            k: v.decode("utf-8")
            for k, v in (message.headers or [])
        }
        ctx = extract(carrier)

        with tracer.start_as_current_span(
            "kafka_consume",
            context=ctx,
            kind=trace.SpanKind.CONSUMER,
        ) as span:
            span.set_attribute("messaging.system", "kafka")
            span.set_attribute("messaging.destination", topic)
            span.set_attribute("messaging.message_id", message.key)

            process_message(message.value)
```

### Propagazione cross-platform

Scenario: n8n trigger → Python microservice → Temporal workflow → callback n8n.

```
n8n (Step 1)
  │ POST /api/process
  │ traceparent: 00-AAAA-1111-01
  ▼
Python FastAPI
  │ estrae ctx, crea child span
  │ avvia Temporal workflow con traceparent nel header
  ▼
Temporal Worker
  │ interceptor estrae ctx
  │ ogni activity = child span
  ▼
Temporal → callback n8n
  │ inietta traceparent nel POST
  ▼
n8n (Step finale)
  │ trace completa: n8n → Python → Temporal → n8n
```

Tutto appare come una singola trace in Jaeger/Tempo, navigabile dal trigger iniziale fino al callback finale.

---

## Propagazione del contesto via webhook e code

### Protocolli di propagazione supportati

| Propagatore | Header | Quando usare |
|---|---|---|
| W3C TraceContext | `traceparent`, `tracestate` | Default raccomandato |
| B3 (Zipkin) | `X-B3-TraceId`, `X-B3-SpanId`, ... | Legacy Zipkin |
| B3 single | `b3` | Formato compatto |
| Jaeger | `uber-trace-id` | Legacy Jaeger |
| AWS X-Ray | `X-Amzn-Trace-Id` | Ambiente AWS |

### Configurazione multi-propagatore

```python
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.trace.propagation import TraceContextTextMapPropagator

# Supporta sia W3C che B3 (per backward compatibility)
set_global_textmap(
    CompositePropagator([
        TraceContextTextMapPropagator(),
        B3MultiFormat(),
    ])
)
```

### Propagazione attraverso SQS

AWS SQS non supporta header custom sugli attributi di sistema. Il contesto va nei `MessageAttributes`:

```python
from opentelemetry.propagate import inject, extract

def send_to_sqs(queue_url: str, body: dict) -> None:
    with tracer.start_as_current_span("sqs_send", kind=trace.SpanKind.PRODUCER) as span:
        carrier = {}
        inject(carrier)

        message_attributes = {
            k: {"DataType": "String", "StringValue": v}
            for k, v in carrier.items()
        }

        span.set_attribute("messaging.system", "aws_sqs")
        span.set_attribute("messaging.destination", queue_url)

        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(body),
            MessageAttributes=message_attributes,
        )

def receive_from_sqs(queue_url: str) -> None:
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MessageAttributeNames=["traceparent", "tracestate"],
    )
    for message in response.get("Messages", []):
        carrier = {
            k: v["StringValue"]
            for k, v in message.get("MessageAttributes", {}).items()
        }
        ctx = extract(carrier)

        with tracer.start_as_current_span(
            "sqs_receive",
            context=ctx,
            kind=trace.SpanKind.CONSUMER,
        ) as span:
            process_message(json.loads(message["Body"]))
            sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message["ReceiptHandle"],
            )
```

---

## Integrazione Temporal

### Temporal e OTel: architettura

Temporal ha supporto nativo per OpenTelemetry tramite interceptor. Ogni workflow execution, activity execution, e signal diventa uno span nella trace.

```
trace_id: xyz789
├── span: TemporalWorkflow::OrderProcessing (root)
│   ├── span: Activity::ValidateOrder       (50ms)
│   ├── span: Activity::ChargePayment       (800ms)
│   │   └── span: HTTP::POST /v1/charges    (750ms)
│   ├── span: Activity::FulfillOrder         (200ms)
│   └── span: Activity::SendConfirmation     (30ms)
```

### Setup Python Temporal con OTel interceptor

```python
from temporalio.client import Client
from temporalio.worker import Worker
from temporalio.contrib.opentelemetry import TracingInterceptor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

# Setup OTel
resource = Resource.create({SERVICE_NAME: "temporal-worker-orders"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="otel-collector:4317"))
)
trace.set_tracer_provider(provider)

async def main():
    # Client con tracing interceptor
    client = await Client.connect(
        "temporal-server:7233",
        interceptors=[TracingInterceptor()],
    )

    # Worker con tracing interceptor
    worker = Worker(
        client,
        task_queue="order-processing",
        workflows=[OrderWorkflow],
        activities=[validate_order, charge_payment, fulfill_order, send_confirmation],
        interceptors=[TracingInterceptor()],
    )
    await worker.run()
```

### Workflow Temporal instrumentato

```python
from temporalio import workflow, activity
from datetime import timedelta
import logging

logger = logging.getLogger("temporal.orders")

@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, order: dict) -> dict:
        # Ogni activity diventa automaticamente un child span
        validation = await workflow.execute_activity(
            validate_order,
            order,
            start_to_close_timeout=timedelta(seconds=30),
        )

        payment = await workflow.execute_activity(
            charge_payment,
            {"order_id": order["id"], "amount": order["total"]},
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=workflow.RetryPolicy(
                maximum_attempts=3,
                initial_interval=timedelta(seconds=2),
            ),
        )

        fulfillment = await workflow.execute_activity(
            fulfill_order,
            order["id"],
            start_to_close_timeout=timedelta(seconds=120),
        )

        await workflow.execute_activity(
            send_confirmation,
            {"order_id": order["id"], "email": order["email"]},
            start_to_close_timeout=timedelta(seconds=15),
        )

        return {"status": "completed", "payment_id": payment["id"]}


@activity.defn
async def validate_order(order: dict) -> dict:
    """Validazione ordine — trace automatica via interceptor."""
    # L'interceptor crea span: Activity::validate_order
    # con attributi temporal.activity.*, temporal.workflow.*
    logger.info("Validazione ordine %s", order["id"])
    if not order.get("items"):
        raise ValueError("Ordine senza prodotti")
    return {"valid": True, "item_count": len(order["items"])}


@activity.defn
async def charge_payment(payment_info: dict) -> dict:
    """Pagamento — span include retry se fallisce."""
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("payment_gateway_call") as span:
        span.set_attribute("payment.amount", payment_info["amount"])
        span.set_attribute("payment.order_id", payment_info["order_id"])
        result = await call_payment_gateway(payment_info)
        span.set_attribute("payment.transaction_id", result["id"])
        return result
```

### Metriche custom Temporal

```python
from opentelemetry import metrics

meter = metrics.get_meter("temporal.workflows")

workflow_started = meter.create_counter(
    "temporal.workflow.started",
    description="Workflow avviati per tipo",
)
workflow_completed = meter.create_counter(
    "temporal.workflow.completed",
    description="Workflow completati per tipo e stato",
)
activity_duration = meter.create_histogram(
    "temporal.activity.duration_seconds",
    description="Durata activity per tipo",
)
activity_retries = meter.create_counter(
    "temporal.activity.retries",
    description="Numero di retry per activity",
)
```

---

## Integrazione Prefect

### Prefect 2.x/3.x e OpenTelemetry

Prefect non ha un interceptor OTel nativo come Temporal. L'instrumentazione avviene tramite decoratori custom e gli hook `on_completion` / `on_failure` / `on_cancellation`.

### Setup base

```python
import time
import functools
from prefect import flow, task, get_run_logger
from opentelemetry import trace, metrics

tracer = trace.get_tracer("prefect.workflows")
meter = metrics.get_meter("prefect.workflows")

flow_duration = meter.create_histogram("prefect.flow.duration_seconds")
flow_counter = meter.create_counter("prefect.flow.executions.total")
task_counter = meter.create_counter("prefect.task.executions.total")
task_duration = meter.create_histogram("prefect.task.duration_seconds")


def traced_task(name: str = None):
    """Decoratore che wrappa un Prefect task con un OTel span."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            span_name = name or func.__name__
            with tracer.start_as_current_span(span_name) as span:
                span.set_attribute("prefect.task.name", func.__name__)
                start = time.monotonic()
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.StatusCode.OK)
                    task_counter.add(1, {"task": func.__name__, "status": "success"})
                    return result
                except Exception as e:
                    span.set_status(trace.StatusCode.ERROR, str(e))
                    span.record_exception(e)
                    task_counter.add(1, {"task": func.__name__, "status": "error"})
                    raise
                finally:
                    duration = time.monotonic() - start
                    task_duration.record(duration, {"task": func.__name__})
        return wrapper
    return decorator
```

### Flow Prefect con observability

```python
@task(retries=3, retry_delay_seconds=10)
@traced_task("fetch_orders")
def fetch_orders(date: str) -> list:
    logger = get_run_logger()
    logger.info("Recupero ordini per %s", date)
    # ... query database
    return orders


@task
@traced_task("process_order")
def process_order(order: dict) -> dict:
    logger = get_run_logger()
    logger.info("Elaborazione ordine %s", order["id"])
    # ... business logic
    return {"processed": True, "id": order["id"]}


@task
@traced_task("generate_report")
def generate_report(results: list) -> str:
    # ... genera report
    return report_path


def on_flow_completion(flow, flow_run, state):
    """Hook Prefect: emetti metriche a completamento."""
    flow_counter.add(1, {
        "flow": flow.name,
        "status": "completed",
    })


def on_flow_failure(flow, flow_run, state):
    """Hook Prefect: emetti metriche su fallimento."""
    flow_counter.add(1, {
        "flow": flow.name,
        "status": "failed",
    })
    # Crea span di errore per visibilita nella trace
    with tracer.start_as_current_span("flow_failure") as span:
        span.set_status(trace.StatusCode.ERROR, str(state.message))
        span.set_attribute("prefect.flow.name", flow.name)
        span.set_attribute("prefect.flow_run.id", str(flow_run.id))


@flow(
    name="daily_order_processing",
    on_completion=[on_flow_completion],
    on_failure=[on_flow_failure],
)
def daily_order_processing(date: str):
    with tracer.start_as_current_span("daily_order_processing") as root:
        root.set_attribute("workflow.name", "daily_order_processing")
        root.set_attribute("workflow.param.date", date)

        orders = fetch_orders(date)
        root.set_attribute("workflow.order_count", len(orders))

        results = [process_order(order) for order in orders]
        report = generate_report(results)

        root.set_attribute("workflow.report_path", report)
        return report
```

---

## Integrazione Apache Airflow

### Airflow OpenTelemetry Provider

Apache Airflow supporta OTel tramite il provider `apache-airflow-providers-opentelemetry`.

```bash
pip install apache-airflow-providers-opentelemetry==1.2.0
```

### Configurazione airflow.cfg

```ini
[metrics]
otel_on = True
otel_host = otel-collector
otel_port = 4318
otel_prefix = airflow
otel_ssl_active = False

[traces]
otel_on = True
otel_host = otel-collector
otel_port = 4318
otel_task_log_event = True
```

In alternativa, via variabili d'ambiente:

```bash
export AIRFLOW__METRICS__OTEL_ON=True
export AIRFLOW__METRICS__OTEL_HOST=otel-collector
export AIRFLOW__METRICS__OTEL_PORT=4318
export AIRFLOW__TRACES__OTEL_ON=True
export AIRFLOW__TRACES__OTEL_HOST=otel-collector
export AIRFLOW__TRACES__OTEL_PORT=4318
```

### DAG Airflow con OTel spans custom

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.opentelemetry.hooks.otel import OtelHook
from datetime import datetime, timedelta
from opentelemetry import trace

tracer = trace.get_tracer("airflow.dags.etl")

default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


def extract_data(**context):
    """Task con span OTel custom aggiuntivo."""
    with tracer.start_as_current_span("custom_extract") as span:
        span.set_attribute("airflow.dag_id", context["dag"].dag_id)
        span.set_attribute("airflow.task_id", context["task"].task_id)
        span.set_attribute("airflow.run_id", context["run_id"])
        span.set_attribute("airflow.execution_date", str(context["execution_date"]))

        # ... estrazione dati
        records = fetch_records()
        span.set_attribute("extract.record_count", len(records))
        context["ti"].xcom_push(key="record_count", value=len(records))
        return records


def transform_data(**context):
    with tracer.start_as_current_span("custom_transform") as span:
        ti = context["ti"]
        record_count = ti.xcom_pull(task_ids="extract", key="record_count")
        span.set_attribute("transform.input_count", record_count)
        # ... trasformazione


def load_data_to_warehouse(**context):
    with tracer.start_as_current_span("custom_load") as span:
        # ... caricamento nel warehouse
        span.set_attribute("load.destination", "bigquery")
        span.set_attribute("load.table", "analytics.orders")


with DAG(
    dag_id="etl_daily_orders",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["etl", "otel-instrumented"],
) as dag:

    extract = PythonOperator(
        task_id="extract",
        python_callable=extract_data,
    )

    transform = PythonOperator(
        task_id="transform",
        python_callable=transform_data,
    )

    load = PythonOperator(
        task_id="load",
        python_callable=load_data_to_warehouse,
    )

    extract >> transform >> load
```

### Metriche Airflow esposte via OTel

Con `otel_on = True`, Airflow esporta automaticamente:

| Metrica | Tipo | Descrizione |
|---|---|---|
| `airflow.dag.processing.total_parse_time` | Gauge | Tempo di parsing DAG |
| `airflow.dag_run.duration` | Histogram | Durata run DAG |
| `airflow.dag_run.{state}` | Counter | Run per stato (success/failed) |
| `airflow.task_instance.duration` | Histogram | Durata task instance |
| `airflow.task_instance.{state}` | Counter | Task per stato |
| `airflow.executor.open_slots` | Gauge | Slot executor disponibili |
| `airflow.executor.queued_tasks` | Gauge | Task in coda |
| `airflow.executor.running_tasks` | Gauge | Task in esecuzione |
| `airflow.pool.open_slots` | Gauge | Slot pool disponibili |
| `airflow.pool.used_slots` | Gauge | Slot pool usati |
| `airflow.scheduler.heartbeat` | Counter | Heartbeat dello scheduler |

---

## Metriche custom per la salute dei workflow

### Metriche fondamentali

Ogni sistema di workflow dovrebbe esporre queste metriche:

| Metrica | Tipo OTel | Semantic Convention | Perche |
|---|---|---|---|
| `workflow.executions.total` | Counter | custom | Volume e trend |
| `workflow.duration.seconds` | Histogram | custom | SLO latenza |
| `workflow.errors.total` | Counter | custom | Error budget |
| `workflow.queue.depth` | UpDownCounter | custom | Backpressure |
| `workflow.retry.count` | Counter | custom | Instabilita |
| `workflow.records.processed` | Counter | custom | Throughput |
| `workflow.step.duration.seconds` | Histogram | custom | Bottleneck per step |
| `workflow.inflight` | UpDownCounter | custom | Concorrenza |

### Implementazione completa

```python
from opentelemetry import metrics
from opentelemetry.metrics import Observation
import psutil
import threading

meter = metrics.get_meter("workflow.health", version="1.0.0")

# --- Counter ---
executions_total = meter.create_counter(
    name="workflow.executions.total",
    description="Esecuzioni totali per workflow e stato",
    unit="1",
)

errors_total = meter.create_counter(
    name="workflow.errors.total",
    description="Errori totali per workflow e tipo errore",
    unit="1",
)

retries_total = meter.create_counter(
    name="workflow.retry.count",
    description="Retry totali per workflow e step",
    unit="1",
)

records_processed = meter.create_counter(
    name="workflow.records.processed",
    description="Record elaborati per workflow",
    unit="1",
)

# --- Histogram ---
workflow_duration = meter.create_histogram(
    name="workflow.duration.seconds",
    description="Distribuzione durata workflow",
    unit="s",
)

step_duration = meter.create_histogram(
    name="workflow.step.duration.seconds",
    description="Distribuzione durata per step",
    unit="s",
)

# --- UpDownCounter (gauge behavior) ---
queue_depth = meter.create_up_down_counter(
    name="workflow.queue.depth",
    description="Profondita coda workflow pendenti",
    unit="1",
)

inflight_workflows = meter.create_up_down_counter(
    name="workflow.inflight",
    description="Workflow attualmente in esecuzione",
    unit="1",
)

# --- Observable Gauge (callback-based) ---
def get_worker_memory(_options):
    """Callback per memoria worker."""
    mem = psutil.Process().memory_info()
    return [Observation(mem.rss / 1024 / 1024, {"unit": "MB"})]

worker_memory = meter.create_observable_gauge(
    name="workflow.worker.memory_mb",
    description="Memoria RSS del worker in MB",
    callbacks=[get_worker_memory],
)


# --- Utilizzo ---
class WorkflowRunner:
    def execute(self, workflow_name: str, payload: dict) -> dict:
        attrs = {"workflow.name": workflow_name}
        inflight_workflows.add(1, attrs)
        start = time.monotonic()

        try:
            result = self._run_steps(workflow_name, payload)
            executions_total.add(1, {**attrs, "status": "success"})
            return result
        except Exception as e:
            executions_total.add(1, {**attrs, "status": "error"})
            errors_total.add(1, {**attrs, "error.type": type(e).__name__})
            raise
        finally:
            duration = time.monotonic() - start
            workflow_duration.record(duration, attrs)
            inflight_workflows.add(-1, attrs)

    def _run_steps(self, workflow_name: str, payload: dict) -> dict:
        for step_name, step_fn in self.steps[workflow_name]:
            step_start = time.monotonic()
            step_attrs = {"workflow.name": workflow_name, "step.name": step_name}

            try:
                payload = step_fn(payload)
            except RetryableError:
                retries_total.add(1, step_attrs)
                raise
            finally:
                step_duration.record(
                    time.monotonic() - step_start, step_attrs
                )

        return payload
```

### Metriche di success rate e error budget

```python
# PromQL per calcolare SLI da queste metriche OTel:

# Success rate (ultimi 5 minuti)
# sum(rate(workflow_executions_total{status="success"}[5m]))
# /
# sum(rate(workflow_executions_total[5m]))

# Error budget remaining (SLO 99.5%, finestra 30 giorni)
# 1 - (
#   sum(increase(workflow_executions_total{status="error"}[30d]))
#   /
#   sum(increase(workflow_executions_total[30d]))
# ) / (1 - 0.995)
```

---

## OTel Collector — configurazione avanzata

### Configurazione completa per workflow

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: "0.0.0.0:4317"
      http:
        endpoint: "0.0.0.0:4318"

  # Scrape metriche Prometheus da Temporal/Airflow
  prometheus:
    config:
      scrape_configs:
        - job_name: "temporal-server"
          scrape_interval: 15s
          static_configs:
            - targets: ["temporal-server:8000"]
        - job_name: "airflow-statsd"
          scrape_interval: 15s
          static_configs:
            - targets: ["airflow-statsd-exporter:9102"]

processors:
  # Batch per efficienza
  batch:
    send_batch_size: 1024
    send_batch_max_size: 2048
    timeout: 5s

  # Arricchisci con attributi globali
  attributes/env:
    actions:
      - key: deployment.environment
        value: production
        action: upsert
      - key: service.region
        value: eu-west-1
        action: upsert

  # Filtra span di health check (rumorosi)
  filter/healthcheck:
    error_mode: ignore
    traces:
      span:
        - 'attributes["http.route"] == "/healthz"'
        - 'attributes["http.route"] == "/readyz"'

  # Resource detection automatica
  resourcedetection:
    detectors: [env, system, docker]
    timeout: 5s

  # Memory limiter (protezione OOM)
  memory_limiter:
    check_interval: 5s
    limit_mib: 512
    spike_limit_mib: 128

  # Tail sampling (decisione dopo aver visto la trace completa)
  tail_sampling:
    decision_wait: 10s
    num_traces: 50000
    expected_new_traces_per_sec: 100
    policies:
      # Tutti gli errori
      - name: errors-always
        type: status_code
        status_code:
          status_codes: [ERROR]
      # Latenza alta (> 5s)
      - name: slow-traces
        type: latency
        latency:
          threshold_ms: 5000
      # 10% dei successi per baseline
      - name: success-sample
        type: probabilistic
        probabilistic:
          sampling_percentage: 10
      # Sempre per workflow critici
      - name: critical-workflows
        type: string_attribute
        string_attribute:
          key: workflow.priority
          values: [critical, high]

exporters:
  # Traces -> Tempo
  otlp/tempo:
    endpoint: "tempo:4317"
    tls:
      insecure: true

  # Metrics -> Prometheus remote write
  prometheusremotewrite:
    endpoint: "http://mimir:9009/api/v1/push"
    resource_to_telemetry_conversion:
      enabled: true

  # Logs -> Loki
  loki:
    endpoint: "http://loki:3100/loki/api/v1/push"
    default_labels_enabled:
      exporter: false
      job: true

  # Debug (solo dev)
  debug:
    verbosity: detailed

extensions:
  health_check:
    endpoint: "0.0.0.0:13133"
  zpages:
    endpoint: "0.0.0.0:55679"

service:
  extensions: [health_check, zpages]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, filter/healthcheck, attributes/env, tail_sampling, batch]
      exporters: [otlp/tempo]
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, attributes/env, batch]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, attributes/env, batch]
      exporters: [loki]
```

### Docker Compose per lo stack completo

```yaml
# docker-compose.otel-stack.yaml
version: "3.9"

services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.95.0
    command: ["--config=/etc/otelcol/config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otelcol/config.yaml:ro
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "13133:13133" # Health check
      - "55679:55679" # zPages
    deploy:
      resources:
        limits:
          memory: 768M

  tempo:
    image: grafana/tempo:2.4.0
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml:ro
      - tempo-data:/var/tempo
    ports:
      - "3200:3200"

  prometheus:
    image: prom/prometheus:v2.51.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

  loki:
    image: grafana/loki:2.9.5
    volumes:
      - loki-data:/loki
    ports:
      - "3100:3100"

  grafana:
    image: grafana/grafana:10.4.0
    environment:
      GF_AUTH_ANONYMOUS_ENABLED: "true"
      GF_AUTH_ANONYMOUS_ORG_ROLE: "Admin"
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"

volumes:
  tempo-data:
  prometheus-data:
  loki-data:
  grafana-data:
```

---

## Correlazione log attraverso gli step del workflow

### Il problema

Senza correlazione, i log di un workflow distribuito sono N flussi indipendenti. Un errore nello step 4 ha un log nel servizio D, ma il contesto (quale workflow, quale trigger, quali dati) e nel servizio A.

### Structured logging con trace context injection

```python
import logging
import json
from opentelemetry import trace

class TraceContextFilter(logging.Filter):
    """Inietta trace_id e span_id in ogni log record."""

    def filter(self, record):
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            record.trace_id = format(ctx.trace_id, "032x")
            record.span_id = format(ctx.span_id, "016x")
            record.trace_flags = ctx.trace_flags
        else:
            record.trace_id = ""
            record.span_id = ""
            record.trace_flags = 0
        return True


class StructuredJsonFormatter(logging.Formatter):
    """Formato JSON con campi OTel standard."""

    def format(self, record):
        entry = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": getattr(record, "trace_id", ""),
            "span_id": getattr(record, "span_id", ""),
            "service.name": "workflow-engine",
        }

        # Aggiungi extra fields
        for key in ["workflow_name", "step_name", "record_count",
                     "error_type", "retry_attempt"]:
            if hasattr(record, key):
                entry[key] = getattr(record, key)

        if record.exc_info:
            entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "stacktrace": self.formatException(record.exc_info),
            }

        return json.dumps(entry, default=str)


def setup_logging():
    """Configura logging con trace context per tutto il processo."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    handler.addFilter(TraceContextFilter())

    root.addHandler(handler)
```

### Esempio di log correlati in Loki/Grafana

Query LogQL per trovare tutti i log di una trace:

```logql
{service_name="workflow-engine"} | json | trace_id="4bf92f3577b34da6a3ce929d0e0e4736"
```

Risultato: tutti i log emessi durante quella specifica esecuzione, ordinati cronologicamente, attraverso tutti gli step e servizi.

### Pattern: workflow context propagato nei log

```python
import contextvars

# Context var per metadata workflow
workflow_context = contextvars.ContextVar("workflow_context", default={})


class WorkflowContextFilter(logging.Filter):
    """Aggiunge contesto workflow a tutti i log."""

    def filter(self, record):
        ctx = workflow_context.get()
        for key, value in ctx.items():
            setattr(record, key, value)
        return True


def run_workflow(name: str, run_id: str, payload: dict):
    """Imposta contesto workflow per tutti i log durante l'esecuzione."""
    token = workflow_context.set({
        "workflow_name": name,
        "workflow_run_id": run_id,
        "workflow_trigger": payload.get("trigger", "manual"),
    })

    try:
        with tracer.start_as_current_span(name) as span:
            span.set_attribute("workflow.name", name)
            span.set_attribute("workflow.run_id", run_id)
            # ... esecuzione
    finally:
        workflow_context.reset(token)
```

---

## Dashboard Grafana per workflow monitoring

### Dashboard JSON — Overview workflow

```json
{
  "dashboard": {
    "title": "Workflow Observability",
    "uid": "workflow-obs-main",
    "tags": ["workflow", "otel", "sre"],
    "timezone": "browser",
    "refresh": "30s",
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "templating": {
      "list": [
        {
          "name": "workflow_name",
          "type": "query",
          "datasource": "Prometheus",
          "query": "label_values(workflow_executions_total, workflow_name)",
          "multi": true,
          "includeAll": true
        },
        {
          "name": "environment",
          "type": "query",
          "datasource": "Prometheus",
          "query": "label_values(workflow_executions_total, deployment_environment)",
          "multi": false
        }
      ]
    },
    "panels": [
      {
        "title": "Esecuzioni per minuto",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "sum(rate(workflow_executions_total{workflow_name=~\"$workflow_name\"}[5m])) by (workflow_name, status)",
            "legendFormat": "{{workflow_name}} — {{status}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "drawStyle": "line",
              "fillOpacity": 15,
              "pointSize": 5,
              "stacking": { "mode": "none" }
            },
            "color": {
              "mode": "palette-classic"
            }
          },
          "overrides": [
            {
              "matcher": { "id": "byRegexp", "options": ".*error.*" },
              "properties": [
                { "id": "color", "value": { "fixedColor": "red", "mode": "fixed" } }
              ]
            }
          ]
        }
      },
      {
        "title": "Success Rate (SLI)",
        "type": "stat",
        "gridPos": { "h": 4, "w": 6, "x": 12, "y": 0 },
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "sum(rate(workflow_executions_total{status=\"success\", workflow_name=~\"$workflow_name\"}[1h])) / sum(rate(workflow_executions_total{workflow_name=~\"$workflow_name\"}[1h])) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "value": 0, "color": "red" },
                { "value": 95, "color": "yellow" },
                { "value": 99, "color": "green" }
              ]
            }
          }
        }
      },
      {
        "title": "P95 Durata Workflow",
        "type": "stat",
        "gridPos": { "h": 4, "w": 6, "x": 18, "y": 0 },
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(workflow_duration_seconds_bucket{workflow_name=~\"$workflow_name\"}[5m])) by (le, workflow_name))"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "value": 0, "color": "green" },
                { "value": 30, "color": "yellow" },
                { "value": 120, "color": "red" }
              ]
            }
          }
        }
      },
      {
        "title": "Durata per step (heatmap)",
        "type": "heatmap",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 4 },
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "sum(rate(workflow_step_duration_seconds_bucket{workflow_name=~\"$workflow_name\"}[5m])) by (le, step_name)",
            "format": "heatmap"
          }
        ],
        "options": {
          "color": { "scheme": "Oranges" },
          "yAxis": { "unit": "s" }
        }
      },
      {
        "title": "Coda workflow pendenti",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "workflow_queue_depth{workflow_name=~\"$workflow_name\"}",
            "legendFormat": "{{workflow_name}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "custom": {
              "fillOpacity": 30,
              "gradientMode": "scheme"
            },
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "value": 0, "color": "green" },
                { "value": 100, "color": "yellow" },
                { "value": 500, "color": "red" }
              ]
            }
          }
        }
      },
      {
        "title": "Retry rate per step",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 12 },
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "sum(rate(workflow_retry_count_total{workflow_name=~\"$workflow_name\"}[5m])) by (step_name)",
            "legendFormat": "{{step_name}}"
          }
        ]
      },
      {
        "title": "Error budget consumato (30d)",
        "type": "gauge",
        "gridPos": { "h": 8, "w": 6, "x": 0, "y": 16 },
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "(sum(increase(workflow_executions_total{status=\"error\", workflow_name=~\"$workflow_name\"}[30d])) / sum(increase(workflow_executions_total{workflow_name=~\"$workflow_name\"}[30d]))) / (1 - 0.995) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "value": 0, "color": "green" },
                { "value": 50, "color": "yellow" },
                { "value": 80, "color": "orange" },
                { "value": 100, "color": "red" }
              ]
            }
          }
        }
      },
      {
        "title": "Trace recenti con errore",
        "type": "table",
        "gridPos": { "h": 8, "w": 18, "x": 6, "y": 16 },
        "datasource": "Tempo",
        "targets": [
          {
            "queryType": "traceql",
            "query": "{ resource.service.name = \"workflow-engine\" && status = error } | select(span.workflow.name, span.workflow.run_id, duration)"
          }
        ]
      }
    ]
  }
}
```

### Dashboard pannello: trace explorer link

Per navigare da una metrica alla trace, configura il data link nel pannello Grafana:

```json
{
  "fieldConfig": {
    "defaults": {
      "links": [
        {
          "title": "Vedi trace in Tempo",
          "url": "/explore?orgId=1&left={\"datasource\":\"Tempo\",\"queries\":[{\"queryType\":\"traceql\",\"query\":\"{resource.service.name=\\\"workflow-engine\\\" && span.workflow.name=\\\"${__data.fields.workflow_name}\\\"}\"}]}",
          "targetBlank": true
        }
      ]
    }
  }
}
```

---

## Alerting su SLO dei workflow

### Definizione SLO

| SLO | SLI (cosa misuri) | Target | Finestra |
|---|---|---|---|
| Disponibilita workflow | Success rate | 99.5% | 30 giorni |
| Latenza ETL giornaliero | P95 durata | < 300s | 30 giorni |
| Latenza order processing | P99 durata | < 60s | 30 giorni |
| Coda backlog | Queue depth | < 500 | Continuo |
| Freshness dati | Tempo dall'ultimo successo | < 2h | Continuo |

### Regole Prometheus per SLO

```yaml
# prometheus-rules/workflow-slo.yml
groups:
  - name: workflow_slo_recording
    interval: 30s
    rules:
      # Success rate (SLI)
      - record: workflow:success_rate:5m
        expr: |
          sum(rate(workflow_executions_total{status="success"}[5m])) by (workflow_name)
          /
          sum(rate(workflow_executions_total[5m])) by (workflow_name)

      # Error budget remaining (30d rolling)
      - record: workflow:error_budget_remaining:30d
        expr: |
          1 - (
            sum(increase(workflow_executions_total{status="error"}[30d])) by (workflow_name)
            /
            sum(increase(workflow_executions_total[30d])) by (workflow_name)
          ) / (1 - 0.995)

      # P95 duration
      - record: workflow:duration_p95:5m
        expr: |
          histogram_quantile(0.95,
            sum(rate(workflow_duration_seconds_bucket[5m])) by (le, workflow_name)
          )

  - name: workflow_slo_alerts
    rules:
      # Error budget quasi esaurito
      - alert: WorkflowErrorBudgetLow
        expr: workflow:error_budget_remaining:30d < 0.2
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "Error budget workflow {{ $labels.workflow_name }} sotto il 20%"
          description: |
            Il workflow {{ $labels.workflow_name }} ha consumato oltre l'80% del suo
            error budget (SLO 99.5%, finestra 30 giorni).
            Budget rimanente: {{ printf "%.1f" $value | mul 100 }}%.
          runbook_url: "https://wiki.internal/runbooks/workflow-error-budget"

      # Error budget esaurito
      - alert: WorkflowErrorBudgetExhausted
        expr: workflow:error_budget_remaining:30d <= 0
        for: 1m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Error budget ESAURITO per {{ $labels.workflow_name }}"
          description: |
            SLO violato. Il workflow {{ $labels.workflow_name }} ha superato
            lo 0.5% di errori nella finestra di 30 giorni.

      # Workflow bloccato (nessuna esecuzione da troppo tempo)
      - alert: WorkflowStale
        expr: |
          time() - max(workflow_last_success_timestamp) by (workflow_name) > 7200
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Workflow {{ $labels.workflow_name }} senza successo da >2h"

      # Latenza P95 fuori SLO
      - alert: WorkflowLatencyHigh
        expr: workflow:duration_p95:5m > 300
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Latenza P95 {{ $labels.workflow_name }} sopra 300s"
          description: |
            P95 attuale: {{ printf "%.0f" $value }}s.
            SLO target: 300s.

      # Coda in crescita
      - alert: WorkflowQueueBacklog
        expr: workflow_queue_depth > 500
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Coda workflow {{ $labels.workflow_name }} sopra 500 messaggi"

      # Spike di retry (instabilita)
      - alert: WorkflowRetrySpike
        expr: |
          sum(rate(workflow_retry_count_total[5m])) by (workflow_name) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Retry rate elevato per {{ $labels.workflow_name }}"
          description: "Oltre 1 retry/sec per 10 minuti. Possibile dipendenza instabile."
```

### Alertmanager routing

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ["alertname", "workflow_name"]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: "default"
  routes:
    - match:
        severity: critical
      receiver: "pagerduty-oncall"
      repeat_interval: 15m
    - match:
        severity: warning
        team: platform
      receiver: "slack-platform"
      repeat_interval: 2h

receivers:
  - name: "default"
    slack_configs:
      - channel: "#alerts-workflow"
        send_resolved: true
        title: '{{ .GroupLabels.alertname }} — {{ .GroupLabels.workflow_name }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: "pagerduty-oncall"
    pagerduty_configs:
      - service_key_file: /etc/alertmanager/secrets/pagerduty_key

  - name: "slack-platform"
    slack_configs:
      - channel: "#platform-alerts"
        send_resolved: true
```

---

## Error tracking e root cause analysis

### Struttura dell'errore in OTel

Quando uno span registra un errore, OTel cattura:

```python
try:
    result = call_external_api(payload)
except requests.exceptions.Timeout as e:
    span.set_status(StatusCode.ERROR, "API timeout dopo 30s")
    span.record_exception(e, attributes={
        "exception.escaped": True,
        "api.endpoint": "https://api.partner.com/v2/process",
        "api.timeout_seconds": 30,
        "workflow.run_id": run_id,
        "retry.attempt": attempt,
    })
```

L'evento `exception` nello span contiene:

| Attributo | Valore |
|---|---|
| `exception.type` | `requests.exceptions.Timeout` |
| `exception.message` | `Connection timed out after 30s` |
| `exception.stacktrace` | Traceback completo |

### Pattern: error fingerprinting

Per raggruppare errori simili, calcola un fingerprint:

```python
import hashlib

def error_fingerprint(exc: Exception, span_name: str) -> str:
    """Genera fingerprint per raggruppare errori identici."""
    components = [
        type(exc).__name__,
        span_name,
        # Primo frame dello stacktrace (dove e stato lanciato)
        str(exc.__traceback__.tb_lineno) if exc.__traceback__ else "unknown",
    ]
    raw = "|".join(components)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# Uso
with tracer.start_as_current_span("process_payment") as span:
    try:
        charge(order)
    except Exception as e:
        fp = error_fingerprint(e, "process_payment")
        span.set_attribute("error.fingerprint", fp)
        span.record_exception(e)
        span.set_status(StatusCode.ERROR)
```

### Root cause analysis con trace waterfall

Processo sistematico:

```
1. Alert: WorkflowErrorBudgetLow per "etl_daily"
   │
2. Dashboard Grafana: error rate spike iniziato alle 14:32 UTC
   │
3. Query TraceQL per errori recenti:
   │  { resource.service.name = "workflow-engine"
   │    && span.workflow.name = "etl_daily"
   │    && status = error }
   │
4. Apri trace: root span "etl_daily" → ERROR
   │
5. Naviga waterfall:
   │  ├── fetch_data (OK, 120ms)
   │  ├── transform (OK, 200ms)
   │  └── load_to_warehouse (ERROR, 30012ms) ← timeout
   │      └── db_insert_batch (ERROR, 30000ms)
   │          attributi:
   │            db.system = postgresql
   │            db.statement = "INSERT INTO analytics.orders ..."
   │            db.connection_pool.active = 50
   │            db.connection_pool.max = 50  ← pool esaurito!
   │
6. Root cause: connection pool PostgreSQL saturo
   │
7. Correlazione log (LogQL con trace_id):
   │  14:32:01 WARN "Connection pool wait timeout exceeded"
   │  14:31:45 WARN "Slow query detected: 28s"
   │  14:30:00 INFO "Concurrent workflow instances: 12"
   │
8. Causa radice: troppe istanze concorrenti hanno esaurito il pool.
   Azione: limitare concorrenza workflow + aumentare pool max.
```

### Query TraceQL utili per RCA

```
# Tutti gli errori di un workflow specifico
{ span.workflow.name = "etl_daily" && status = error }

# Span lenti (> 10s) in un servizio
{ resource.service.name = "workflow-engine" && duration > 10s }

# Errori per tipo di eccezione
{ span.exception.type = "ConnectionError" }

# Span con retry elevato
{ span.retry.attempt > 2 }

# Workflow falliti con attributo specifico
{ span.workflow.name = "order_processing"
  && span.order.total > 10000
  && status = error }
```

---

## Ottimizzazione delle prestazioni usando le trace

### Identificare bottleneck

Le trace mostrano la struttura temporale di ogni esecuzione. Il bottleneck e lo span che domina la durata totale.

```
trace_id: xyz789 — durata totale: 12.5s
├── fetch_data:     0.5s  (4%)
├── transform:      1.2s  (10%)
│   ├── validate:   0.3s
│   └── enrich:     0.9s
├── load:           10.5s (84%) ← BOTTLENECK
│   ├── batch_1:    3.2s
│   ├── batch_2:    3.5s
│   └── batch_3:    3.8s
└── notify:         0.3s  (2%)
```

### Pattern: parallelizzazione guidata dalle trace

Prima della trace, il workflow era sequenziale. Dopo l'analisi:

```python
# PRIMA: sequenziale (12.5s totali)
data = fetch_data()
transformed = transform(data)
load(transformed)  # 10.5s — 3 batch sequenziali
notify()

# DOPO: batch paralleli (6.3s totali, -50%)
import asyncio

data = fetch_data()
transformed = transform(data)

batches = split_into_batches(transformed, batch_size=1000)
with tracer.start_as_current_span("load_parallel") as span:
    span.set_attribute("load.batch_count", len(batches))
    await asyncio.gather(*[
        load_batch(batch, i) for i, batch in enumerate(batches)
    ])

notify()
```

### Pattern: cache informed by traces

```python
# Trace mostra: api_call_enrich ripetuta con stessi parametri
# 420ms per chiamata, 500 chiamate → 210s di API calls

from functools import lru_cache

@lru_cache(maxsize=10000)
def enrich_record_cached(record_key: str) -> dict:
    with tracer.start_as_current_span("enrich_cached") as span:
        span.set_attribute("cache.hit", False)  # sarà True per hit
        return call_enrichment_api(record_key)

# Con span wrapper per distinguere hit/miss:
def enrich_with_tracing(record_key: str) -> dict:
    with tracer.start_as_current_span("enrich") as span:
        if record_key in _cache:
            span.set_attribute("cache.hit", True)
            span.set_attribute("cache.key", record_key)
            return _cache[record_key]
        else:
            span.set_attribute("cache.hit", False)
            result = call_enrichment_api(record_key)
            _cache[record_key] = result
            return result
```

### Metriche per P99 optimization

```python
# Query PromQL: trova il percentile dove vive il problema
#
# P50: 2.1s   ← accettabile
# P90: 5.3s   ← borderline
# P95: 12.8s  ← problema
# P99: 45.2s  ← outlier grave

# histogram_quantile(0.50, sum(rate(workflow_duration_seconds_bucket[1h])) by (le))
# histogram_quantile(0.90, sum(rate(workflow_duration_seconds_bucket[1h])) by (le))
# histogram_quantile(0.95, sum(rate(workflow_duration_seconds_bucket[1h])) by (le))
# histogram_quantile(0.99, sum(rate(workflow_duration_seconds_bucket[1h])) by (le))
```

La differenza tra P90 e P99 indica la distribuzione degli outlier. Una differenza ampia suggerisce un problema intermittente (e.g., cold start, GC pause, contesa risorse).

---

## Cost observability per workflow

### Perche tracciare i costi

Ogni workflow consuma risorse: compute, API calls, storage, network. Senza visibilita sui costi:

- Non sai quale workflow e il piu costoso.
- Non puoi ottimizzare dove serve.
- Non puoi allocare costi ai team/prodotti.
- Non puoi preventivare la crescita.

### Metriche di costo

```python
meter = metrics.get_meter("workflow.cost")

# Costo API esterne
api_cost = meter.create_counter(
    name="workflow.cost.api_calls.usd",
    description="Costo stimato chiamate API esterne in USD",
    unit="USD",
)

# Costo compute (basato su durata * costo/ora)
compute_cost = meter.create_counter(
    name="workflow.cost.compute.usd",
    description="Costo stimato compute in USD",
    unit="USD",
)

# Costo storage
storage_cost = meter.create_counter(
    name="workflow.cost.storage.usd",
    description="Costo stimato storage in USD",
    unit="USD",
)

# Costo totale per workflow
total_cost = meter.create_counter(
    name="workflow.cost.total.usd",
    description="Costo totale stimato per workflow",
    unit="USD",
)


# Pricing config (da env/config, non hardcoded)
PRICING = {
    "compute_per_second_usd": 0.00003,  # ~$0.108/ora
    "api_enrichment_per_call_usd": 0.002,
    "api_payment_per_call_usd": 0.025,
    "storage_per_gb_usd": 0.023,
}


def track_cost(workflow_name: str, step_name: str,
               duration_s: float, api_calls: dict, data_gb: float):
    """Registra costi per un'esecuzione workflow."""
    attrs = {"workflow.name": workflow_name}

    # Compute
    compute = duration_s * PRICING["compute_per_second_usd"]
    compute_cost.add(compute, {**attrs, "step": step_name})

    # API
    for api_name, count in api_calls.items():
        price_key = f"api_{api_name}_per_call_usd"
        if price_key in PRICING:
            cost = count * PRICING[price_key]
            api_cost.add(cost, {**attrs, "api": api_name})

    # Storage
    if data_gb > 0:
        storage = data_gb * PRICING["storage_per_gb_usd"]
        storage_cost.add(storage, {**attrs, "step": step_name})

    # Totale (approssimativo)
    total = compute + sum(
        count * PRICING.get(f"api_{api}_per_call_usd", 0)
        for api, count in api_calls.items()
    ) + (data_gb * PRICING["storage_per_gb_usd"])
    total_cost.add(total, attrs)
```

### Dashboard costi Grafana (PromQL)

```
# Costo giornaliero per workflow
sum(increase(workflow_cost_total_usd[24h])) by (workflow_name)

# Top 5 workflow piu costosi (ultima settimana)
topk(5, sum(increase(workflow_cost_total_usd[7d])) by (workflow_name))

# Breakdown costi per tipo (compute vs API vs storage)
sum(increase(workflow_cost_compute_usd[24h])) by (workflow_name)
sum(increase(workflow_cost_api_calls_usd[24h])) by (workflow_name, api)
sum(increase(workflow_cost_storage_usd[24h])) by (workflow_name)

# Costo per esecuzione (media)
sum(increase(workflow_cost_total_usd[24h])) by (workflow_name)
/
sum(increase(workflow_executions_total[24h])) by (workflow_name)
```

---

## Observability-driven development per automazioni

### Il principio

Observability-driven development (ODD) inverte l'approccio tradizionale: invece di scrivere codice e poi aggiungere osservabilita, parti dall'osservabilita e poi scrivi il codice.

### Workflow ODD

```
1. Definisci SLO (cosa significa "funziona")
   │
2. Definisci SLI (come misuri "funziona")
   │
3. Scrivi le metriche e gli span PRIMA del codice
   │  - meter.create_counter(...)
   │  - tracer.start_as_current_span(...)
   │
4. Crea la dashboard Grafana con pannelli vuoti
   │
5. Configura gli alert (regole Prometheus)
   │
6. ORA scrivi la logica del workflow
   │  - ogni step gia instrumentato
   │  - la dashboard si popola durante lo sviluppo
   │
7. Testa guardando la dashboard, non solo i log
   │
8. Itera: la trace mostra dove ottimizzare
```

### Vantaggi rispetto all'approccio tradizionale

| Aspetto | Tradizionale | ODD |
|---|---|---|
| Quando aggiungi osservabilita | Dopo (spesso mai) | Prima |
| Cosa instrumenti | Quello che ti ricordi | Tutto lo skeleton |
| SLO | Definiti dopo l'incidente | Definiti prima del deploy |
| Dashboard | Create in emergenza | Pronte dal giorno 1 |
| Alert | Reattivi | Proattivi |
| Debug incidenti | Aggiungi log, rideploya | Gia visibile |

### Template per nuovo workflow

```python
"""
Template ODD per nuovo workflow.
1. Copia questo file.
2. Definisci SLO nel docstring.
3. Rinomina metriche e span.
4. Implementa la logica nei metodi TODO.
"""

from opentelemetry import trace, metrics
from opentelemetry.trace import StatusCode
import time
import logging

# SLO:
# - Success rate: >= 99.5% (30 giorni)
# - P95 durata: < 120s
# - Freshness: ultimo successo < 2h fa

logger = logging.getLogger("workflow.NOME_WORKFLOW")
tracer = trace.get_tracer("workflow.NOME_WORKFLOW")
meter = metrics.get_meter("workflow.NOME_WORKFLOW")

# Metriche (definite PRIMA della logica)
_executions = meter.create_counter("workflow.NOME.executions.total")
_duration = meter.create_histogram("workflow.NOME.duration.seconds")
_errors = meter.create_counter("workflow.NOME.errors.total")
_records = meter.create_counter("workflow.NOME.records.processed")
_last_success = meter.create_up_down_counter("workflow.NOME.last_success_ts")


def run(config: dict) -> dict:
    start = time.monotonic()
    attrs = {"workflow.name": "NOME_WORKFLOW"}

    with tracer.start_as_current_span("NOME_WORKFLOW", attributes=attrs) as root:
        try:
            # Step 1
            with tracer.start_as_current_span("step_1_fetch"):
                data = _step_1_fetch(config)

            # Step 2
            with tracer.start_as_current_span("step_2_process"):
                result = _step_2_process(data)

            # Step 3
            with tracer.start_as_current_span("step_3_store"):
                _step_3_store(result)

            _executions.add(1, {**attrs, "status": "success"})
            root.set_status(StatusCode.OK)
            return {"status": "ok"}

        except Exception as e:
            _executions.add(1, {**attrs, "status": "error"})
            _errors.add(1, {**attrs, "error.type": type(e).__name__})
            root.set_status(StatusCode.ERROR, str(e))
            root.record_exception(e)
            raise
        finally:
            _duration.record(time.monotonic() - start, attrs)


def _step_1_fetch(config: dict) -> list:
    # TODO: implementa
    raise NotImplementedError

def _step_2_process(data: list) -> list:
    # TODO: implementa
    raise NotImplementedError

def _step_3_store(result: list) -> None:
    # TODO: implementa
    raise NotImplementedError
```

---

## Sampling strategies avanzate

### Head-based vs tail-based

| Aspetto | Head-based | Tail-based |
|---|---|---|
| Decisione | All'inizio della trace | Alla fine della trace |
| Dove | SDK (applicazione) | Collector |
| Pro | Semplice, basso overhead | Cattura errori e outlier |
| Contro | Perde errori e outlier | Richiede buffer, piu RAM |
| Quando | Alta cardinalita, costo prioritario | SLO-critical, debug |

### Configurazione tail sampling nel Collector

```yaml
processors:
  tail_sampling:
    decision_wait: 10s          # attendi 10s per span tardivi
    num_traces: 100000          # buffer massimo trace in memoria
    expected_new_traces_per_sec: 500

    policies:
      # Policy 1: TUTTI gli errori (sempre)
      - name: errors-policy
        type: status_code
        status_code:
          status_codes: [ERROR]

      # Policy 2: trace lente (> 5s)
      - name: latency-policy
        type: latency
        latency:
          threshold_ms: 5000

      # Policy 3: workflow critici (sempre)
      - name: critical-workflows
        type: string_attribute
        string_attribute:
          key: workflow.priority
          values: [critical, high]

      # Policy 4: 10% di tutto il resto (baseline)
      - name: baseline-sample
        type: probabilistic
        probabilistic:
          sampling_percentage: 10

      # Policy 5: composite per combinare criteri
      - name: composite-policy
        type: composite
        composite:
          max_total_spans_per_second: 2000
          policy_order: [errors-policy, latency-policy, critical-workflows, baseline-sample]
          rate_allocation:
            - policy: errors-policy
              percent: 40
            - policy: latency-policy
              percent: 20
            - policy: critical-workflows
              percent: 30
            - policy: baseline-sample
              percent: 10
```

### Head sampling nell'SDK (per ridurre il volume prima del Collector)

```python
from opentelemetry.sdk.trace.sampling import (
    ParentBasedTraceIdRatio,
    ALWAYS_ON,
    ALWAYS_OFF,
)

# 50% head sampling (riduce volume in ingresso al Collector)
sampler = ParentBasedTraceIdRatio(0.5)

# Per workflow critici: forza sampling
class WorkflowAwareSampler:
    """Sampler che forza il campionamento per workflow critici."""

    def __init__(self, default_ratio: float = 0.1):
        self.default = ParentBasedTraceIdRatio(default_ratio)
        self.always_on = ALWAYS_ON

    def should_sample(self, context, trace_id, name, kind, attributes, links):
        priority = (attributes or {}).get("workflow.priority", "normal")
        if priority in ("critical", "high"):
            return self.always_on.should_sample(
                context, trace_id, name, kind, attributes, links
            )
        return self.default.should_sample(
            context, trace_id, name, kind, attributes, links
        )


provider = TracerProvider(
    resource=resource,
    sampler=WorkflowAwareSampler(default_ratio=0.1),
)
```

---

## Esercizi

1. **Lab — instrumentazione script Python.** Workflow di 4 step, ognuno e uno span; export a Jaeger locale; visualizza trace.

2. **Lab — propagation cross-service.** 2 servizi connessi via webhook; verifica che il trace si estenda attraverso boundary.

3. **Stretch — sampling tail-based.** Setup OTel Collector con tail sampling che cattura tutti gli errori + 10% successi.

4. **Lab — metriche custom.** Crea 4 metriche (counter executions, histogram duration, counter errors, gauge queue depth). Visualizzale in Grafana con 3 pannelli distinti.

5. **Lab — correlazione log ↔ trace.** Configura structured logging JSON con `trace_id` injection. Emetti log durante 3 step di un workflow. In Loki/Grafana, parti da un log di errore e naviga alla trace completa.

6. **Lab — dashboard Grafana.** Importa il JSON della dashboard fornito in questo modulo. Aggiungi un pannello custom per il tuo workflow. Configura un data link che da una metrica apra la trace corrispondente in Tempo.

7. **Lab — SLO alerting.** Configura le recording rules e le alert rules Prometheus fornite. Simula un fallimento workflow (raise Exception). Verifica che l'alert `WorkflowErrorBudgetLow` si attivi in Alertmanager. Verifica la notifica in Slack (o il channel configurato).

8. **Progetto — cost observability.** Instrumenta un workflow con metriche di costo (compute, API, storage). Crea un pannello Grafana che mostri il costo giornaliero per workflow e il costo medio per esecuzione.

---

## Troubleshooting — 18 problemi comuni

### 1. Le trace non appaiono in Jaeger/Tempo

**Sintomo:** workflow eseguito con successo, ma nessuna trace visibile nel backend.

**Cause probabili:**
- SDK non esporta: `BatchSpanProcessor` non ha fatto flush (applicazione terminata prima del flush).
- Endpoint errato: il Collector non e raggiungibile dall'applicazione.
- Sampling: head sampling impostato a 0% o percentuale molto bassa.
- Firewall: porta 4317 (gRPC) o 4318 (HTTP) bloccata.

**Soluzione:**
```python
# Forza flush prima dell'uscita
trace.get_tracer_provider().force_flush(timeout_millis=10000)

# Verifica connettivita
curl -v http://otel-collector:4318/v1/traces

# Verifica sampling
# Se usi ParentBasedTraceIdRatio(0.0), nessuna trace verra campionata
```

### 2. Le metriche non arrivano a Prometheus

**Sintomo:** `workflow_executions_total` non appare in Prometheus.

**Cause probabili:**
- `PeriodicExportingMetricReader` non ancora scattato (default 60s).
- Collector non configurato con pipeline `metrics`.
- Prometheus remote write endpoint errato.
- Metriche con cardinalita troppo alta filtrate dal Collector.

**Soluzione:** verifica la pipeline `metrics` nel Collector config, controlla i log del Collector per errori di export.

### 3. `trace_id` vuoto nei log

**Sintomo:** i log JSON hanno `trace_id: ""`.

**Causa:** il log viene emesso fuori dal contesto di uno span attivo.

**Soluzione:** assicurati che il `logging.info()` avvenga dentro un blocco `with tracer.start_as_current_span(...)`.

### 4. Trace spezzata tra servizi

**Sintomo:** due trace separate invece di una trace unica cross-service.

**Cause:**
- Il producer non inietta `traceparent` negli header HTTP.
- Il consumer non estrae il contesto con `extract()`.
- Proxy/gateway intermedio rimuove header custom.

**Soluzione:** verifica che `inject(headers)` sia chiamato lato producer e `extract(request.headers)` lato consumer. Controlla che il proxy preservi gli header `traceparent` e `tracestate`.

### 5. OTel Collector OOM (Out of Memory)

**Sintomo:** il Collector si riavvia continuamente.

**Causa:** tail sampling con `num_traces` troppo alto o traffico superiore al previsto.

**Soluzione:**
```yaml
processors:
  memory_limiter:
    check_interval: 5s
    limit_mib: 512
    spike_limit_mib: 128
  tail_sampling:
    num_traces: 20000  # ridurre
```

### 6. Metriche con cardinalita esplosiva

**Sintomo:** Prometheus rallenta, storage cresce rapidamente.

**Causa:** attributi ad alta cardinalita come `user_id`, `order_id`, `request_id` usati come label.

**Soluzione:** usa attributi ad alta cardinalita solo su span (traces), non su metriche. Per le metriche usa label a bassa cardinalita (`workflow_name`, `status`, `step_name`, `error_type`).

### 7. Latenza aggiunta dall'instrumentazione

**Sintomo:** workflow piu lento del 5%+ dopo l'instrumentazione.

**Cause:**
- `SimpleSpanProcessor` (sincrono) invece di `BatchSpanProcessor`.
- `batch_size` troppo piccolo.
- Export sincrono invece di asincrono.

**Soluzione:** usa sempre `BatchSpanProcessor` in produzione. `SimpleSpanProcessor` e solo per debug locale.

### 8. Span duplicati

**Sintomo:** lo stesso span appare due volte nella trace.

**Cause:**
- SDK configurato due volte (doppio `add_span_processor`).
- Instrumentazione automatica + manuale sullo stesso codice.

**Soluzione:** verifica che `TracerProvider` sia configurato una sola volta. Se usi auto-instrumentation, non creare span manuali per le stesse operazioni.

### 9. Dashboard Grafana vuota dopo import

**Sintomo:** pannelli importati mostrano "No data".

**Cause:**
- Datasource name nel JSON non corrisponde al nome configurato in Grafana.
- Le metriche usano `_` come separatore ma OTel usa `.` (dipende dal backend).
- Variabile template non selezionata.

**Soluzione:** verifica il nome del datasource. Prometheus converte `.` in `_` nei nomi metriche OTel. Quindi `workflow.executions.total` diventa `workflow_executions_total`.

### 10. Alert non si attiva nonostante errori

**Sintomo:** workflow fallisce ma nessun alert.

**Cause:**
- Recording rule non calcolata (errore di sintassi PromQL).
- `for: 5m` non ancora scaduto (l'alert deve essere in firing per 5 minuti).
- Alertmanager non raggiungibile da Prometheus.
- Label mismatch nel routing Alertmanager.

**Soluzione:** verifica lo stato delle regole in Prometheus UI (Alerts tab). Controlla che non ci siano errori nelle recording rules (Rules tab).

### 11. Trace context perso attraverso async task queue

**Sintomo:** i task Celery/RQ non ereditano il `trace_id` del chiamante.

**Causa:** il context OTel e thread-local. Quando il task viene eseguito in un worker separato, il contesto non e disponibile.

**Soluzione:** serializza `traceparent` nel payload del task e riestrailo nel worker.

```python
# Producer
from opentelemetry.propagate import inject
carrier = {}
inject(carrier)
celery_task.delay(payload=data, trace_context=carrier)

# Consumer (worker)
from opentelemetry.propagate import extract
ctx = extract(task.trace_context)
with tracer.start_as_current_span("celery_task", context=ctx):
    process(task.payload)
```

### 12. Temporal interceptor non genera span

**Sintomo:** il workflow Temporal funziona ma non appare nessuna trace.

**Causa:** `TracingInterceptor` non aggiunto sia al client sia al worker.

**Soluzione:** assicurati di passare `interceptors=[TracingInterceptor()]` sia in `Client.connect()` sia in `Worker(...)`.

### 13. Airflow metriche OTel non esportate

**Sintomo:** `otel_on = True` ma nessuna metrica in Prometheus.

**Cause:**
- Provider `apache-airflow-providers-opentelemetry` non installato.
- Collector non raggiungibile dal container Airflow (networking Docker).

**Soluzione:** verifica installazione provider, controlla connettivita di rete dal container Airflow al Collector.

### 14. Grafana non mostra trace da Tempo

**Sintomo:** Tempo datasource configurato ma le query TraceQL restituiscono errore.

**Cause:**
- Versione Tempo non supporta TraceQL (richiede Tempo >= 2.0).
- Grafana datasource punta alla porta sbagliata (Tempo API: 3200, non 3100).

**Soluzione:** verifica versione Tempo e URL del datasource.

### 15. Cost metrics non precise

**Sintomo:** il costo calcolato non corrisponde alla bolletta cloud.

**Cause:**
- Pricing constants hardcoded non aggiornate.
- Non si conteggiano costi di rete, egress, idle compute.

**Soluzione:** le metriche di costo sono stime. Per precisione, correla le metriche OTel con i dati di billing del cloud provider (AWS Cost Explorer, GCP Billing Export). Le metriche OTel servono per il trend e il confronto relativo tra workflow.

### 16. Log duplicati in Loki

**Sintomo:** ogni log appare due volte in Loki.

**Causa:** il log viene inviato sia tramite il pipeline OTel (SDK → Collector → Loki) sia tramite il driver di logging Docker (stdout → Promtail → Loki).

**Soluzione:** scegli un solo percorso. Raccomandato: invia log tramite OTel SDK/Collector e disabilita Promtail per quel servizio.

### 17. Span con durata negativa o zero

**Sintomo:** alcuni span hanno `duration = 0ms` o valori negativi.

**Cause:**
- Clock skew tra servizi diversi (NTP non sincronizzato).
- Span creato e chiuso nello stesso nanosecondo (operazione troppo veloce).

**Soluzione:** per clock skew, configura NTP su tutti i nodi. Per span troppo veloci, non e un problema reale: le operazioni sub-microsecondo sono correttamente registrate come 0.

### 18. Collector non processa tail sampling correttamente

**Sintomo:** trace con errori non vengono campionate nonostante la policy `errors-always`.

**Causa:** span di errore arriva dopo il `decision_wait` (10s default). Il Collector ha gia preso la decisione di scartare la trace.

**Soluzione:** aumenta `decision_wait` o assicurati che tutti gli span della trace arrivino entro la finestra. Per workflow lunghi (>10s), considera `decision_wait: 30s` (al costo di piu RAM).

---

## FAQ — 18 domande e risposte

### 1. Posso usare OTel senza il Collector?

Si, l'SDK puo esportare direttamente al backend (Jaeger, Tempo). Ma in produzione il Collector e fortemente raccomandato perche: (a) disaccoppia l'app dal backend, (b) permette batch/retry/sampling centralizzato, (c) puoi cambiare backend senza toccare il codice.

### 2. OTel ha overhead significativo sulle prestazioni?

Con `BatchSpanProcessor` e sampling ragionevole, l'overhead e tipicamente <1% di CPU e <2% di memoria. `SimpleSpanProcessor` (sincrono) puo avere overhead significativo e va usato solo in sviluppo.

### 3. Qual e la differenza tra OTel e Prometheus?

Prometheus e un sistema di monitoring (scrape metrics, storage, alerting). OTel e uno standard per generare e trasportare telemetria (traces, metrics, logs). OTel puo esportare metriche verso Prometheus. Sono complementari, non alternativi.

### 4. Devo instrumentare ogni singola funzione?

No. Instrumenta: (a) ogni step del workflow (span), (b) le chiamate a servizi esterni (HTTP, DB, queue), (c) le operazioni business-critical. Non instrumentare utility functions triviali o loop interni. Troppi span = rumore + overhead.

### 5. Come gestisco il costo dello storage delle trace?

Combinando: (a) tail sampling per tenere solo trace utili (errori + outlier + baseline), (b) retention differenziata (errori 30 giorni, successi 7 giorni), (c) compressione (Tempo supporta S3/GCS con compressione). Un tail sampling aggressivo (10% successi, 100% errori) riduce lo storage dell'80-90%.

### 6. Posso usare OTel con n8n?

n8n non ha supporto OTel nativo. Opzioni: (a) instrumenta i webhook endpoint che n8n chiama, (b) usa un proxy HTTP che inietta `traceparent`, (c) per workflow n8n → Python, instrumenta il lato Python. La trace coprira la parte da Python in poi.

### 7. W3C Trace Context funziona con tutti i cloud?

AWS, GCP, Azure supportano tutti W3C Trace Context. AWS X-Ray ha il proprio formato ma supporta anche W3C. Il multi-propagator (W3C + vendor-specific) garantisce compatibilita.

### 8. Quante metriche custom dovrei creare?

Inizia con le 5 fondamentali: executions counter, duration histogram, error counter, queue depth, retry count. Aggiungi metriche business-specific solo quando hai un use case concreto per ciascuna. Ogni metrica ha un costo di cardinalita.

### 9. Come faccio debug se il Collector non funziona?

(a) Abilita l'exporter `debug` nel Collector per vedere la telemetria in stdout. (b) Usa zPages (`localhost:55679/debug/tracez`) per ispezionare le trace in transito. (c) Controlla l'endpoint health: `curl localhost:13133`. (d) Leggi i log del Collector.

### 10. Temporal ha gia le proprie metriche. Serve anche OTel?

Si. Le metriche native di Temporal coprono il runtime Temporal (workflow started, task queue depth, schedule to start latency). Le metriche OTel custom coprono la business logic (ordini processati, costo per esecuzione, SLI custom). Usale entrambe.

### 11. Posso usare Datadog/Splunk/Honeycomb come backend OTel?

Si. Tutti supportano OTLP come protocollo di ingestion. Cambia solo l'exporter nel Collector:

```yaml
exporters:
  datadog:
    api:
      key: ${DD_API_KEY}
      site: datadoghq.eu
```

Questa e la forza di OTel: vendor-neutral. Migrare backend = cambiare config Collector.

### 12. Come instrumentare workflow che durano ore?

Per workflow lunghi (batch ETL, ML training), usa heartbeat span: emetti eventi periodici sullo span root per indicare progresso. Imposta `decision_wait` nel tail sampling abbastanza alto da coprire la durata massima, oppure usa head sampling per questi workflow.

### 13. Qual e la differenza tra `record_exception` e `set_status(ERROR)`?

`record_exception(e)` aggiunge un evento allo span con stacktrace. `set_status(StatusCode.ERROR, msg)` marca lo span come fallito. Usa entrambi: `record_exception` per il dettaglio, `set_status` per la visibilita nella trace (colorazione rossa in Jaeger/Tempo).

### 14. Come faccio correlazione trace ↔ metriche in Grafana?

Usa gli exemplar. Configura l'histogram OTel per emettere exemplar (contengono `trace_id`). In Grafana, il pannello metrica mostra punti cliccabili che aprono la trace corrispondente in Tempo.

```python
# L'histogram OTel emette exemplar automaticamente
# se il trace context e attivo al momento del record
workflow_duration.record(elapsed, {"workflow.name": name})
# ^^ l'exemplar con trace_id viene aggiunto se c'e uno span attivo
```

### 15. Come proteggo i dati sensibili nelle trace?

(a) Non mettere PII negli attributi degli span (`user.email`, `credit_card`). (b) Usa il processor `attributes` nel Collector per rimuovere o mascherare attributi sensibili prima dell'export. (c) Implementa un `SpanProcessor` custom che sanitizza prima dell'export.

```yaml
processors:
  attributes/sanitize:
    actions:
      - key: user.email
        action: delete
      - key: db.statement
        action: hash
```

### 16. OTel Logs SDK e pronto per la produzione?

Al 2026, l'OTel Logs SDK per Python e in stato stabile (GA dal 2024). Per linguaggi con ecosistema di logging maturo (Python logging, Java SLF4J), l'approccio raccomandato e il bridge: usa il tuo framework di logging abituale con il `LoggingInstrumentor` che inietta `trace_id`/`span_id`. Non e necessario sostituire il framework di logging.

### 17. Come stimo la capacity del Collector?

Regola empirica: 1 vCPU + 2GB RAM gestisce circa 10.000 span/secondo. Per tail sampling, moltiplica la RAM per il `decision_wait` in secondi e il throughput atteso. Esempio: 500 trace/sec × 10s wait × 20 span/trace × 1KB/span = 100MB di buffer. Aggiungi margine 2x.

### 18. E possibile fare A/B testing di workflow usando le trace?

Si. Aggiungi un attributo `workflow.variant` (A/B) allo span root. In Grafana, filtra per variante e confronta: durata, success rate, costo. Questo e un pattern potente per validare ottimizzazioni workflow prima del rollout completo.

```python
with tracer.start_as_current_span("order_workflow") as span:
    variant = "B" if feature_flag("new_enrichment") else "A"
    span.set_attribute("workflow.variant", variant)
    # ... esecuzione con logica A o B
```

---

## Auto-valutazione

1. Three pillars: cosa sono?
2. trace_id: come si propaga via HTTP?
3. Head vs tail sampling: trade-off.
4. OTLP: HTTP vs gRPC?
5. Semantic conventions: a cosa servono?
6. Spiega il ruolo del Collector nell'architettura.
7. Quali metriche definiresti per un workflow ETL giornaliero?
8. Come correli un log di errore alla trace che lo ha generato?
9. Cosa succede se il `decision_wait` del tail sampling e troppo corto?
10. Come definiresti un SLO per un workflow di order processing?
11. Qual e la differenza tra `record_exception` e `set_status(ERROR)`?
12. Come propaghi il trace context attraverso Kafka?
13. Perche non dovresti usare `user_id` come label su una metrica?
14. Come implementeresti cost observability per un workflow con API esterne?
15. Che vantaggio da l'observability-driven development?

---

## Letture primarie consigliate

- OpenTelemetry Specification. https://opentelemetry.io/docs/specs/otel/
- W3C Trace Context. https://www.w3.org/TR/trace-context/
- Cindy Sridharan — *Distributed Systems Observability* (O'Reilly).
- Charity Majors, Liz Fong-Jones, George Miranda — *Observability Engineering* (O'Reilly, 2022).
- OpenTelemetry Python SDK docs. https://opentelemetry.io/docs/languages/python/
- OpenTelemetry Collector docs. https://opentelemetry.io/docs/collector/
- Grafana Tempo docs. https://grafana.com/docs/tempo/
- Temporal Observability docs. https://docs.temporal.io/develop/python/observability
- Google SRE Book — cap. su SLO e error budget. https://sre.google/sre-book/
- Alex Hidalgo — *Implementing Service Level Objectives* (O'Reilly, 2020).

---

## Collegamenti incrociati

- Modulo 12 — `12-python-automazione-avanzata.md`: OTel SDK Python.
- Modulo 16 — `16-event-driven-architecture-pratica.md`: tracing in messaging.
- Modulo 17 — `17-retry-idempotency-pattern.md`: retry metrics e correlazione con trace.
- Modulo 19 — `19-cost-monitoring-piattaforme.md`: cost observability complementare.
- Modulo 22 — `22-dlq-parking-lot-pattern.md`: DLQ monitoring e alerting via metriche OTel.
- Modulo 24 — `24-audit-logging-compliance.md`: structured logging e trace_id nei log di audit.

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **OpenTelemetry (OTel)** | Standard vendor-neutral per observability. |
| **Trace** | Albero di span che descrive una request end-to-end. |
| **Span** | Operazione singola con timing. |
| **Metric** | Misura numerica nel tempo (counter, gauge, histogram). |
| **Log** | Messaggio testuale strutturato. |
| **`trace_id`** | UUID che identifica una trace. |
| **W3C Trace Context** | Standard propagation. |
| **OTLP** | OpenTelemetry Protocol; transport. |
| **Sampling head-based** | Decisione campionamento prima dell'esecuzione. |
| **Sampling tail-based** | Decisione dopo aver visto la trace completa. |
| **Semantic conventions** | Standard per naming attributi. |
| **Collector** | Componente OTel che riceve, processa e esporta telemetria. |
| **Exemplar** | Sample trace_id attaccato a un punto metrica per correlazione. |
| **SLO** | Service Level Objective — target di affidabilita. |
| **SLI** | Service Level Indicator — metrica che misura l'SLO. |
| **Error budget** | Quantita di errori tollerata prima di violare l'SLO. |
| **TraceQL** | Linguaggio di query per trace (Grafana Tempo). |
| **Recording rule** | Regola Prometheus che pre-calcola espressioni PromQL. |
| **Instrumentation** | Processo di aggiunta di telemetria al codice. |
| **Resource** | Identita del servizio (nome, versione, ambiente) in OTel. |
| **BatchSpanProcessor** | Processore asincrono che raggruppa span prima dell'export. |
| **Observable gauge** | Metrica letta tramite callback periodica (non push). |
| **Propagator** | Componente che inietta/estrae contesto di tracing nei carrier (HTTP header, message attributes). |
| **Tail sampling processor** | Processore del Collector che decide il campionamento dopo aver visto la trace completa. |
| **LogQL** | Linguaggio di query per log in Grafana Loki. |
| **PromQL** | Linguaggio di query per metriche in Prometheus. |
