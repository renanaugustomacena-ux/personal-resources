# Tutorial 31 — OpenTelemetry in Python: Tracing, Metrics, Logs

> **Companion a:** `31-otel.md`
> **Scope:** OpenTelemetry SDK, auto-instrumentazione, Jaeger, Prometheus, OTLP exporter
> **Prerequisiti:** `tutorial_11_web_framework.md`, `tutorial_30_troubleshooting.md`
> **Durata stimata:** 14-18 ore
> **Stack:** Python 3.12+, opentelemetry-sdk 1.x, FastAPI, Jaeger, Prometheus

---

## Mappa concettuale

```
OpenTelemetry (OTel)
│
├── Tre pilastri
│   ├── Traces — dove va il tempo (span/trace)
│   ├── Metrics — misure aggregate (counter, gauge, histogram)
│   └── Logs — eventi con contesto (correlazione con trace)
│
├── SDK Python
│   ├── opentelemetry-sdk — core
│   ├── opentelemetry-exporter-otlp — OTLP protocol
│   ├── opentelemetry-instrumentation-fastapi
│   ├── opentelemetry-instrumentation-sqlalchemy
│   ├── opentelemetry-instrumentation-httpx
│   └── opentelemetry-instrumentation-asyncio
│
├── Componenti
│   ├── Tracer — crea span
│   ├── Meter — crea strumenti metriche
│   ├── Span — unità di lavoro tracciata
│   ├── Context — propagazione tra processi
│   └── Exporter — invia a backend (Jaeger, Tempo, OTLP)
│
└── Backend
    ├── Jaeger — tracing UI
    ├── Grafana Tempo — tracing scalabile
    ├── Prometheus — metriche
    └── OTel Collector — aggregatore/router
```

---

# Parte A — Setup OpenTelemetry

---

## A1. Installazione e configurazione base

```bash
# Dipendenze core
pip install \
  opentelemetry-sdk \
  opentelemetry-exporter-otlp \
  opentelemetry-instrumentation-fastapi \
  opentelemetry-instrumentation-sqlalchemy \
  opentelemetry-instrumentation-httpx \
  opentelemetry-instrumentation-logging
```

```python
# src/mio_progetto/telemetria.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION

def configura_telemetria(
    nome_servizio: str,
    versione: str = "0.0.0",
    otlp_endpoint: str = "http://localhost:4317",
) -> None:
    """Configura tracing e metrics con esportatore OTLP."""

    resource = Resource.create({
        SERVICE_NAME: nome_servizio,
        SERVICE_VERSION: versione,
        "deployment.environment": "production",
    })

    # ── Tracing ──────────────────────────────────────────────
    trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(tracer_provider)

    # ── Metrics ──────────────────────────────────────────────
    metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=10_000)
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

# Chiamare all'avvio dell'applicazione
# configura_telemetria("mia-api", versione="1.2.3")
```

---

## A2. Auto-instrumentazione FastAPI e httpx

```python
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

def strumenta_applicazione(app: FastAPI, engine=None) -> None:
    """Applica instrumentazione automatica."""
    # FastAPI — span per ogni request
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="salute,metrics",   # esclude health check e metriche
    )
    # httpx — span per ogni chiamata HTTP esterna
    HTTPXClientInstrumentor().instrument()

    # SQLAlchemy — span per ogni query SQL
    if engine:
        SQLAlchemyInstrumentor().instrument(engine=engine, enable_commenter=True)

# main.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    configura_telemetria("mia-api")
    strumenta_applicazione(app, engine=db_engine)
    yield

app = FastAPI(lifespan=lifespan)
```

---

# Parte B — Span manuali

---

## B1. Creare span personalizzati

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer("mio_progetto.servizio")

async def processa_ordine(ordine_id: int) -> dict:
    """Funzione con tracing manuale."""
    with tracer.start_as_current_span("processa_ordine") as span:
        # Attributi dello span
        span.set_attribute("ordine.id", ordine_id)
        span.set_attribute("servizio.nome", "ordini")

        try:
            # Sub-span per sotto-operazioni
            with tracer.start_as_current_span("valida_ordine") as span_val:
                ordine = await recupera_ordine(ordine_id)
                span_val.set_attribute("ordine.totale", ordine["totale"])

            with tracer.start_as_current_span("scala_stock") as span_stock:
                await scala_stock(ordine)
                span_stock.add_event("stock scalato", {"prodotti": len(ordine["prodotti"])})

            with tracer.start_as_current_span("notifica") as span_notif:
                await invia_notifica(ordine["email"])

            span.set_status(Status(StatusCode.OK))
            return {"stato": "completato"}

        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise

async def recupera_ordine(id: int) -> dict:
    await asyncio.sleep(0.01)
    return {"id": id, "totale": 99.99, "prodotti": [1, 2], "email": "u@e.com"}

async def scala_stock(ordine: dict) -> None:
    await asyncio.sleep(0.01)

async def invia_notifica(email: str) -> None:
    await asyncio.sleep(0.05)
```

---

## B2. Metrics: counter, gauge, histogram

```python
from opentelemetry import metrics

meter = metrics.get_meter("mio_progetto.metriche")

# Counter — monotonicamente crescente (es. richieste totali)
richieste_counter = meter.create_counter(
    "http.server.requests.total",
    unit="1",
    description="Numero totale di richieste HTTP ricevute",
)

# Gauge — valore corrente (es. connessioni attive)
connessioni_gauge = meter.create_observable_gauge(
    "db.connections.active",
    callbacks=[lambda options: [metrics.Observation(get_active_connections())]],
    unit="connections",
    description="Connessioni al database attive",
)

# Histogram — distribuzione dei valori (es. latenza)
latenza_histogram = meter.create_histogram(
    "http.server.request.duration",
    unit="ms",
    description="Distribuzione latenza richieste HTTP",
)

# Uso nei middleware
import time
from fastapi import FastAPI, Request, Response

app = FastAPI()

@app.middleware("http")
async def metriche_middleware(request: Request, call_next) -> Response:
    inizio = time.perf_counter()
    response = await call_next(request)
    durata_ms = (time.perf_counter() - inizio) * 1000

    attributi = {
        "http.method": request.method,
        "http.route": request.url.path,
        "http.status_code": str(response.status_code),
    }
    richieste_counter.add(1, attributi)
    latenza_histogram.record(durata_ms, attributi)

    return response

def get_active_connections() -> int:
    return 5   # da implementare
```

---

# Parte C — Correlazione logs e traces

---

## C1. Iniettare trace_id nei log

```python
import logging
import structlog
from opentelemetry import trace

def add_otel_context(logger, method, event_dict):
    """Processor structlog: aggiunge trace_id e span_id ai log."""
    span = trace.get_current_span()
    if span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict

# Configura structlog con il processor OTel
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        add_otel_context,   # ← aggiunge trace_id
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

log = structlog.get_logger()

# Ora ogni log ha il trace_id per correlare con Jaeger/Tempo
async def mia_funzione():
    with tracer.start_as_current_span("mia_funzione"):
        log.info("operazione iniziata", parametro="valore")
        await asyncio.sleep(0.1)
        log.info("operazione completata")
```

---

# Parte D — Docker Compose con stack OTel

---

## D1. OTel Collector + Jaeger + Prometheus

```yaml
# docker-compose.observability.yml
version: "3.9"

services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.100.0
    command: ["--config=/etc/otel/config.yaml"]
    volumes:
      - ./config/otel-collector.yaml:/etc/otel/config.yaml:ro
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8888:8888"   # metriche proprie
    depends_on:
      - jaeger
      - prometheus

  jaeger:
    image: jaegertracing/all-in-one:1.57
    ports:
      - "16686:16686"   # UI
      - "14250:14250"   # gRPC
    environment:
      - COLLECTOR_OTLP_ENABLED=true

  prometheus:
    image: prom/prometheus:v2.52.0
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:10.4.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  grafana_data:
```

```yaml
# config/otel-collector.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  prometheus:
    endpoint: "0.0.0.0:8889"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

---

# Parte E — Riepilogo

## SLI/SLO con metriche OTel

```python
# Definire SLI prima del deploy:
# - Latenza p95 < 200ms
# - Error rate < 1%
# - Throughput > 100 req/s

# Metriche che implementano i SLI:
p95_latenza = latenza_histogram  # .record(ms) per ogni request
errori_counter = meter.create_counter("http.errors.total")

# In Prometheus/Grafana:
# histogram_quantile(0.95, rate(http_server_request_duration_bucket[5m]))
# rate(http_errors_total[5m]) / rate(http_server_requests_total[5m])
```

## Checklist OTel per Python

- [ ] `configura_telemetria()` chiamato all'avvio
- [ ] FastAPI instrumentato (auto span per ogni request)
- [ ] httpx instrumentato (propagazione trace nelle chiamate esterne)
- [ ] SQLAlchemy instrumentato (span per ogni query)
- [ ] Span manuali per operazioni business critiche
- [ ] `trace_id` nei log (structlog processor)
- [ ] Counter per errori, richieste totali
- [ ] Histogram per latenza
- [ ] Gauge per risorse (connessioni, queue depth)
- [ ] Health check escluso dai trace

## Prossimi passi

- `tutorial_33_profiling.md` — profiling di produzione con py-spy
