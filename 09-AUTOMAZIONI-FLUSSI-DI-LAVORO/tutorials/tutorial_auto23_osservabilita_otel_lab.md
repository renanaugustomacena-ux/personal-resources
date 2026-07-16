# Tutorial Lab — Osservabilità con OpenTelemetry, Jaeger e Grafana Tempo

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `23-osservabilita-workflow-otel.md`
> **Livello:** intermediate → advanced
> **Tempo stimato:** 3-4 ore (lab completo)
> **Prerequisiti:** Docker Compose, Python async, HTTP/gRPC base, concetto di distributed tracing
> **Versioni di riferimento:** OTel SDK Python 1.x · OTel Collector 0.100+ · Jaeger 1.56+ · Grafana 10.x

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Configurare OpenTelemetry Collector con pipeline traces/metrics/logs
2. Instrumentare un workflow Python con span annidati e propagazione W3C trace context
3. Esportare trace a Jaeger e metriche a Prometheus/Grafana
4. Propagare il trace context attraverso HTTP (traceparent header)
5. Configurare sampling: always-on, probabilistico, tail-based
6. Correlare trace, log e metriche con correlation ID e span ID

---

## Lab Environment Setup

```bash
# Prerequisiti sistema
python3 --version          # 3.11+
docker compose version     # 2.x

# Python deps
pip install \
  opentelemetry-sdk==1.26.0 \
  opentelemetry-exporter-otlp-proto-grpc==1.26.0 \
  opentelemetry-instrumentation-httpx==0.46b0 \
  opentelemetry-instrumentation-logging==0.46b0 \
  httpx==0.27.0 \
  structlog==24.0.0

mkdir -p otel-lab/{collector,app,dashboard}
cd otel-lab
```

---

## Analogia Introduttiva

> **Osservabilità è come la scatola nera di un aereo**:
> Non sai quando il sistema andrà in panne,
> ma quando succede vuoi sapere ESATTAMENTE cosa stava facendo.
>
> I **trace** sono il percorso del volo: ogni operazione è un segmento (span),
> l'intero viaggio dall'inizio alla fine è un trace. Puoi vedere
> dove l'aereo ha rallentato, dove ha deviato, dove si è fermato.
>
> Le **metriche** sono i sensori: altitudine, velocità, carburante.
> Non ti dicono perché qualcosa è andato male, ma ti avvertono
> prima che succeda.
>
> I **log** sono il diario di bordo: eventi discreti con timestamp.
> Il problema: da soli non bastano. Con trace+log hai la causazione,
> non solo la correlazione.
>
> **OTel** è il sistema di registrazione standardizzato — una volta
> instrumenti, puoi inviare a Jaeger, Grafana Tempo, Datadog, Honeycomb
> senza cambiare il codice.

---

## Architettura del Lab

```
┌─────────────────────────────────────────────────────────────────────┐
│                        APPLICAZIONE PYTHON                           │
│                                                                       │
│  [API Handler] ──span──▶ [Processor] ──span──▶ [DB/External API]   │
│       │                       │                       │              │
│  traceparent header ───────propagato────────────────▶│              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ OTLP gRPC (:4317)
                ┌──────────────▼──────────────────┐
                │      OTEL COLLECTOR               │
                │                                   │
                │  receivers:  otlp                 │
                │  processors: batch, memory_limiter│
                │  exporters:                       │
                │    traces  → Jaeger :14250        │
                │    metrics → Prometheus :9090      │
                │    logs    → stdout               │
                └──────────────┬──────────────────-┘
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │  JAEGER  │    │PROMETHEUS│    │ GRAFANA  │
        │  :16686  │    │  :9090   │    │  :3000   │
        │ (traces) │    │(metriche)│    │(dashbrd) │
        └──────────┘    └──────────┘    └──────────┘
```

---

## PART A — Infrastruttura OTel

### A1 — Docker Compose: Stack Completo

```yaml
# file: collector/docker-compose-otel.yml
version: "3.9"

services:
  # ─── OpenTelemetry Collector ───────────────────────────────────────
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.100.0
    volumes:
      - ./otel-collector-config.yaml:/etc/otelcol-contrib/config.yaml:ro
    ports:
      - "4317:4317"    # OTLP gRPC (da app Python)
      - "4318:4318"    # OTLP HTTP (alternativa)
      - "8888:8888"    # Metriche interne del collector (Prometheus scraping)
      - "13133:13133"  # Health check
    networks: [observability]
    restart: unless-stopped

  # ─── Jaeger (UI trace) ────────────────────────────────────────────
  jaeger:
    image: jaegertracing/all-in-one:1.56
    environment:
      COLLECTOR_OTLP_ENABLED: "true"
    ports:
      - "16686:16686"  # Jaeger UI
      - "14250:14250"  # gRPC (collector → jaeger)
      - "14268:14268"  # HTTP (legacy)
    networks: [observability]
    restart: unless-stopped

  # ─── Prometheus ───────────────────────────────────────────────────
  prometheus:
    image: prom/prometheus:v2.51.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.retention.time=7d
      - --web.enable-lifecycle
    networks: [observability]
    restart: unless-stopped

  # ─── Grafana ──────────────────────────────────────────────────────
  grafana:
    image: grafana/grafana:10.4.0
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD:-admin}
      GF_USERS_ALLOW_SIGN_UP: "false"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana-provisioning:/etc/grafana/provisioning:ro
    ports:
      - "3000:3000"
    networks: [observability]
    depends_on: [prometheus, jaeger]
    restart: unless-stopped

networks:
  observability:
    driver: bridge

volumes:
  prometheus_data:
  grafana_data:
```

### A2 — Configurazione OTel Collector

```yaml
# file: collector/otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  # Limita memoria: non va mai in OOM
  memory_limiter:
    check_interval: 1s
    limit_mib: 256
    spike_limit_mib: 64

  # Raccoglie span prima di inviarli (riduce chiamate di rete)
  batch:
    timeout: 5s
    send_batch_size: 512
    send_batch_max_size: 1024

  # Aggiunge attributi comuni a tutti i span
  resource:
    attributes:
      - key: deployment.environment
        value: development
        action: insert
      - key: service.namespace
        value: automazione-lab
        action: insert

exporters:
  # Jaeger (traces)
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

  # Prometheus (metriche)
  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: otel
    send_timestamps: true
    metric_expiration: 5m

  # Debug log (development)
  debug:
    verbosity: basic

  # Logs su file (production: usare elasticsearch/loki)
  file:
    path: /tmp/otel-logs.json
    rotation:
      max_megabytes: 50

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [jaeger, debug]
    
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]
    
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [file, debug]

  # Health check
  extensions: []
  telemetry:
    logs:
      level: warn
```

### A3 — Prometheus Config

```yaml
# file: collector/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: otel-collector
    static_configs:
      - targets: ["otel-collector:8888", "otel-collector:8889"]

  - job_name: automazione-app
    static_configs:
      - targets: ["host.docker.internal:9091"]  # App Python
```

---

## PART B — Instrumentazione Python

### B1 — Setup Tracer e Meter Globali

```python
#!/usr/bin/env python3
# file: app/otel_setup.py
"""
Setup centralizzato per OpenTelemetry SDK.
Da importare UNA SOLA VOLTA all'avvio dell'applicazione.
"""
from __future__ import annotations

import os
import logging
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace.sampling import (
    TraceIdRatioBased,
    ParentBased,
    ALWAYS_ON,
)
from opentelemetry.instrumentation.logging import LoggingInstrumentor

logger = logging.getLogger(__name__)


def _crea_resource(nome_servizio: str, versione: str = "1.0.0") -> Resource:
    """
    Resource descrive il processo che genera telemetria.
    Attributi importanti: service.name, service.version, deployment.environment.
    """
    return Resource.create({
        SERVICE_NAME: nome_servizio,
        SERVICE_VERSION: versione,
        "deployment.environment": os.environ.get("DEPLOY_ENV", "development"),
        "service.instance.id": os.environ.get("HOSTNAME", "local"),
    })


def _crea_sampler(tasso: float = 1.0):
    """
    Configura il sampler per il tracing.
    
    tasso=1.0: tutte le richieste (sviluppo/test)
    tasso=0.1: 10% delle richieste (produzione alta frequenza)
    
    ParentBased: rispetta la decisione del padre se il trace arriva dall'esterno.
    Questo è CRITICO in microservizi: se il gateway campiona al 10%,
    tutti i servizi downstream devono campionare lo stesso trace.
    """
    if tasso >= 1.0:
        return ALWAYS_ON
    return ParentBased(root=TraceIdRatioBased(tasso))


def configura_otel(
    nome_servizio: str,
    versione: str = "1.0.0",
    otlp_endpoint: str = "http://localhost:4317",
    sampling_rate: float = 1.0,
) -> tuple:
    """
    Configura TracerProvider e MeterProvider.
    Ritorna (tracer, meter) per uso nell'applicazione.
    """
    resource = _crea_resource(nome_servizio, versione)
    
    # ─── Trace ────────────────────────────────────────────────────────
    span_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    span_processor = BatchSpanProcessor(
        span_exporter,
        max_queue_size=2048,
        max_export_batch_size=512,
        export_timeout_millis=30_000,
    )
    
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=_crea_sampler(sampling_rate),
    )
    tracer_provider.add_span_processor(span_processor)
    trace.set_tracer_provider(tracer_provider)
    
    # ─── Metrics ──────────────────────────────────────────────────────
    metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=60_000,  # ogni 60s
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
    )
    metrics.set_meter_provider(meter_provider)
    
    # ─── Logging con trace correlation ────────────────────────────────
    # Inietta trace_id e span_id nei log automaticamente
    LoggingInstrumentor().instrument(set_logging_format=True)
    
    tracer = trace.get_tracer(nome_servizio)
    meter = metrics.get_meter(nome_servizio)
    
    logger.info("OTel configurato: service=%s endpoint=%s", nome_servizio, otlp_endpoint)
    
    return tracer, meter
```

### B2 — Worker Workflow con Span Annidati

```python
#!/usr/bin/env python3
# file: app/workflow_worker.py
"""
Worker che processa ordini con tracing completo.
Ogni operazione è uno span — visibile in Jaeger come timeline.
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from opentelemetry import trace, metrics, propagate, baggage
from opentelemetry.trace import StatusCode, SpanKind
from opentelemetry.semconv.trace import SpanAttributes

from app.otel_setup import configura_otel

logger = logging.getLogger(__name__)

# ─── Inizializzazione (una sola volta all'avvio) ──────────────────────────────

TRACER, METER = configura_otel(
    nome_servizio="ordini-worker",
    versione="2.1.0",
    otlp_endpoint="http://localhost:4317",
)

# ─── Metriche applicazione ────────────────────────────────────────────────────

ordini_processati = METER.create_counter(
    name="ordini.processati.totale",
    description="Numero totale di ordini processati",
    unit="1",
)

ordini_falliti = METER.create_counter(
    name="ordini.falliti.totale",
    description="Numero totale di ordini falliti",
    unit="1",
)

latenza_processing = METER.create_histogram(
    name="ordini.latenza_ms",
    description="Latenza elaborazione ordine",
    unit="ms",
)

dimensione_ordine = METER.create_histogram(
    name="ordini.importo_eur",
    description="Distribuzione importo ordini",
    unit="EUR",
)


# ─── Funzioni worker ─────────────────────────────────────────────────────────

async def valida_ordine(ordine: dict) -> bool:
    """
    Validazione ordine — span figlio di process_ordine.
    
    span.set_attribute() aggiunge metadati searchable in Jaeger:
    → Puoi filtrare per "ordine.valuta=EUR" o "ordine.importo>100"
    """
    with TRACER.start_as_current_span(
        "valida_ordine",
        attributes={
            "ordine.id": ordine["id"],
            "ordine.valuta": ordine.get("valuta", "EUR"),
            "ordine.articoli": len(ordine.get("articoli", [])),
        }
    ) as span:
        try:
            if not ordine.get("id"):
                raise ValueError("ordine.id obbligatorio")
            if ordine.get("importo", 0) <= 0:
                raise ValueError(f"importo non valido: {ordine.get('importo')}")
            
            span.set_attribute("validazione.esito", "ok")
            span.set_status(StatusCode.OK)
            return True
        
        except ValueError as e:
            span.record_exception(e)
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("validazione.esito", "failed")
            span.set_attribute("validazione.errore", str(e))
            return False


async def chiama_gateway_pagamenti(ordine: dict) -> dict:
    """
    Chiamata HTTP al gateway — span con propagazione W3C traceparent.
    Il gateway (se instrumentato) riceverà il trace context e creerà span figli.
    """
    with TRACER.start_as_current_span(
        "gateway_pagamenti.charge",
        kind=SpanKind.CLIENT,  # CLIENT = span che chiama un servizio esterno
        attributes={
            SpanAttributes.HTTP_METHOD: "POST",
            SpanAttributes.HTTP_URL: "http://gateway.example.com/charge",
            SpanAttributes.NET_PEER_NAME: "gateway.example.com",
            "payment.importo": ordine["importo"],
            "payment.valuta": ordine.get("valuta", "EUR"),
        }
    ) as span:
        # Inietta trace context negli header HTTP
        # Il gateway riceve 'traceparent' e 'tracestate' header
        headers = {}
        propagate.inject(headers)  # Aggiunge traceparent, tracestate
        
        span.set_attribute("traceparent.inviato", headers.get("traceparent", "none"))
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    "http://gateway.example.com/charge",
                    json={
                        "amount": ordine["importo"],
                        "currency": ordine.get("valuta", "EUR"),
                        "reference": ordine["id"],
                    },
                    headers=headers,  # Propaga trace context!
                )
                span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, response.status_code)
                
                if response.status_code == 200:
                    data = response.json()
                    span.set_attribute("payment.transaction_id", data.get("transaction_id", ""))
                    span.set_status(StatusCode.OK)
                    return data
                else:
                    span.set_status(StatusCode.ERROR, f"HTTP {response.status_code}")
                    raise RuntimeError(f"Gateway error: {response.status_code}")
            
            except httpx.ConnectError as e:
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, "Gateway non raggiungibile")
                # Simula successo per il lab
                return {"transaction_id": f"MOCK-TXN-{ordine['id']}", "status": "approved"}


async def aggiorna_inventario(ordine: dict) -> None:
    """Aggiorna inventario — span figlio con eventi interni."""
    with TRACER.start_as_current_span(
        "inventario.aggiorna",
        attributes={"ordine.id": ordine["id"]},
    ) as span:
        # Span event: punti significativi dentro lo span
        span.add_event("inventario.lock_acquisito", {"tabella": "prodotti"})
        await asyncio.sleep(0.005)  # Simula query DB
        
        span.add_event("inventario.stock_decrementato", {
            "articoli": len(ordine.get("articoli", [])),
        })
        
        span.set_status(StatusCode.OK)


async def invia_notifica(ordine: dict, transaction_id: str) -> None:
    """Invia notifica — span con attributo esito notifica."""
    with TRACER.start_as_current_span(
        "notifica.invia",
        kind=SpanKind.PRODUCER,  # PRODUCER = pubblica su queue/topic
        attributes={
            "messaging.system": "redis",
            "messaging.destination": "notifiche",
            "ordine.id": ordine["id"],
        }
    ) as span:
        await asyncio.sleep(0.002)  # Simula pub su queue
        span.set_attribute("notifica.canale", "email")
        span.set_status(StatusCode.OK)


async def processa_ordine(ordine: dict) -> dict:
    """
    Root span per l'elaborazione di un ordine.
    Tutti gli altri span sono figli di questo.
    
    Struttura span tree in Jaeger:
    
    processa_ordine (root)
    ├── valida_ordine
    ├── gateway_pagamenti.charge
    ├── inventario.aggiorna
    └── notifica.invia
    """
    start_ms = time.monotonic() * 1000
    
    with TRACER.start_as_current_span(
        "processa_ordine",
        kind=SpanKind.INTERNAL,
        attributes={
            "ordine.id": ordine["id"],
            "ordine.importo": ordine.get("importo", 0),
            "ordine.cliente_id": ordine.get("cliente_id", ""),
            # Non loggare dati PII! Solo ID opachi
        }
    ) as root_span:
        logger.info("Processing ordine %s", ordine["id"])
        
        try:
            # Step 1: Valida
            if not await valida_ordine(ordine):
                root_span.set_status(StatusCode.ERROR, "Validazione fallita")
                ordini_falliti.add(1, {"motivo": "validazione"})
                return {"status": "error", "ordine_id": ordine["id"]}
            
            # Step 2: Pagamento (parallelo con inventario non è sicuro — step sequenziale)
            payment_result = await chiama_gateway_pagamenti(ordine)
            
            # Step 3: Inventario e notifica in parallelo
            await asyncio.gather(
                aggiorna_inventario(ordine),
                invia_notifica(ordine, payment_result.get("transaction_id", "")),
            )
            
            # Metriche
            latenza_ms = time.monotonic() * 1000 - start_ms
            ordini_processati.add(1, {"valuta": ordine.get("valuta", "EUR")})
            latenza_processing.record(latenza_ms, {"servizio": "ordini-worker"})
            dimensione_ordine.record(ordine.get("importo", 0))
            
            root_span.set_attribute("processing.durata_ms", int(latenza_ms))
            root_span.set_attribute("processing.transaction_id",
                                    payment_result.get("transaction_id", ""))
            root_span.set_status(StatusCode.OK)
            
            return {
                "status": "ok",
                "ordine_id": ordine["id"],
                "transaction_id": payment_result.get("transaction_id"),
            }
        
        except Exception as e:
            root_span.record_exception(e)
            root_span.set_status(StatusCode.ERROR, str(e))
            ordini_falliti.add(1, {"motivo": type(e).__name__})
            raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(otelTraceID)s:%(otelSpanID)s] %(name)s %(message)s"
    )
    
    ordine_test = {
        "id": "ORD-2026-001",
        "cliente_id": "CLT-0042",  # Solo ID, non il nome!
        "importo": 149.90,
        "valuta": "EUR",
        "articoli": [{"sku": "PROD-A", "qty": 2}],
    }
    
    result = asyncio.run(processa_ordine(ordine_test))
    print(f"\nRisultato: {json.dumps(result, indent=2)}")
    print("\nApri Jaeger: http://localhost:16686")
    print("Cerca servizio: ordini-worker")
```

### B3 — Propagazione W3C Trace Context (HTTP)

```python
#!/usr/bin/env python3
# file: app/trace_context_http.py
"""
Dimostrazione propagazione W3C trace context tra servizi HTTP.

W3C traceparent header formato:
  traceparent: {versione}-{trace-id}-{parent-span-id}-{flags}
  Es: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

  - versione:       "00" (sempre)
  - trace-id:       32 hex = 16 bytes (unico per tutta la catena)
  - parent-span-id: 16 hex = 8 bytes (lo span che ha generato la richiesta)
  - flags:          "01" = sampled, "00" = not sampled
"""
from __future__ import annotations

import asyncio
import json
from opentelemetry import trace, propagate
from opentelemetry.trace import SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
import httpx

from app.otel_setup import configura_otel

TRACER, _ = configura_otel("trace-propagation-demo")


async def servizio_A_crea_ordine(ordine: dict) -> dict:
    """
    Servizio A: genera un nuovo trace e chiama il Servizio B.
    Questo è il punto di ingresso — crea il root span.
    """
    with TRACER.start_as_current_span(
        "servizio_A.crea_ordine",
        kind=SpanKind.SERVER,  # SERVER = sono io che ricevo la richiesta
    ) as span_a:
        trace_id = span_a.get_span_context().trace_id
        span_id = span_a.get_span_context().span_id
        print(f"\n[Servizio A] trace_id: {trace_id:032x}")
        print(f"[Servizio A] span_id:  {span_id:016x}")
        
        # Inietta il trace context negli header per Servizio B
        headers = {}
        propagate.inject(headers)
        print(f"[Servizio A] traceparent inviato: {headers.get('traceparent')}")
        
        # Chiama Servizio B (simulato)
        result = await servizio_B_elabora_pagamento(ordine, headers)
        return result


async def servizio_B_elabora_pagamento(ordine: dict, headers_ricevuti: dict) -> dict:
    """
    Servizio B: estrae il trace context dagli header e crea span figlio.
    Il trace_id è LO STESSO del Servizio A — è lo stesso trace distribuito.
    """
    # Estrai il contesto dagli header HTTP
    contesto = propagate.extract(headers_ricevuti)
    
    with TRACER.start_as_current_span(
        "servizio_B.elabora_pagamento",
        kind=SpanKind.SERVER,
        context=contesto,  # CRITICO: collega questo span al parent del Servizio A
    ) as span_b:
        trace_id = span_b.get_span_context().trace_id
        span_id = span_b.get_span_context().span_id
        print(f"\n[Servizio B] trace_id: {trace_id:032x}  ← STESSO trace!")
        print(f"[Servizio B] span_id:  {span_id:016x}  ← span diverso")
        
        await asyncio.sleep(0.01)  # Simula elaborazione
        return {"status": "pagato", "ordine_id": ordine["id"]}


def demo_header_manuale():
    """Mostra il formato del traceparent header."""
    print("\n=== FORMATO W3C TRACEPARENT ===")
    print("traceparent: 00-{trace_id}-{parent_span_id}-{flags}")
    print()
    
    # Costruisci manualmente un traceparent
    import secrets
    trace_id = secrets.token_hex(16)   # 32 hex chars
    span_id = secrets.token_hex(8)     # 16 hex chars
    flags = "01"                        # sampled
    traceparent = f"00-{trace_id}-{span_id}-{flags}"
    
    print(f"  trace_id:  {trace_id}  (16 bytes, 128-bit)")
    print(f"  span_id:   {span_id}   (8 bytes, 64-bit)")
    print(f"  flags:     {flags}              (01=sampled, 00=not sampled)")
    print(f"\n  traceparent: {traceparent}")
    print()
    print("Questo header viaggia in OGNI richiesta HTTP tra microservizi.")
    print("Senza di esso, i trace sono spezzati e non correlabili in Jaeger.")


if __name__ == "__main__":
    demo_header_manuale()
    result = asyncio.run(servizio_A_crea_ordine({"id": "ORD-DEMO-001"}))
    print(f"\nRisultato finale: {json.dumps(result, indent=2)}")
    print("\nIn Jaeger: search by trace_id per vedere entrambi gli span")
```

---

## PART C — Sampling Strategies

### C1 — Quando Campionare

```python
#!/usr/bin/env python3
# file: app/sampling_demo.py
"""
Strategie di sampling per OpenTelemetry.

ALWAYS_ON (1.0):  tutti gli span — dev e staging
RATIO (0.1):      10% — produzione alta frequenza
ParentBased:      rispetta la decisione del caller — microservizi
Head sampling:    decisione all'inizio del trace
Tail sampling:    decisione DOPO aver visto tutto il trace (OTel Collector)
"""
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_ON,
    ALWAYS_OFF,
    TraceIdRatioBased,
    ParentBased,
    Decision,
    SamplingResult,
)
from opentelemetry.trace import SpanContext, TraceFlags


def guida_sampling():
    print("""
=== GUIDA SCELTA SAMPLING ===

ALWAYS_ON (sampling_rate=1.0)
  ✓ Dev/staging: vuoi vedere TUTTI i trace
  ✓ Produzione bassa frequenza (<100 req/s)
  ✗ Produzione alta frequenza: costo storage enorme

PROBABILISTICO (TraceIdRatioBased(0.1))
  ✓ Produzione alta frequenza (>1000 req/s)
  ✓ Riduce costo 10-100x mantenendo campione statistico
  ✗ Potrebbe perdere trace di errori rari

ParentBased(root=TraceIdRatioBased(0.1))
  ✓ Microservizi: rispetta la decisione del gateway
  ✓ Un trace è campionato interamente o per niente
  ✗ Non aiuta se il caller non propaga trace context

TAIL-BASED (OTel Collector tail_sampling processor)
  ✓ Campiona il 100% degli errori, 1% del successo
  ✓ Migliore visibilità su problemi reali
  ✓ Decisione DOPO aver visto l'intero trace (latenza, errori)
  ✗ Richiede il collector in modalità tail_sampling
  ✗ Più complesso da configurare

REGOLA PRATICA:
  dev/staging   → ALWAYS_ON
  prod <100rps  → ALWAYS_ON o 100%
  prod 100-1000 → ParentBased(0.1)
  prod >1000    → tail_sampling nel collector
""")


# ─── Tail Sampling nel Collector ──────────────────────────────────────────────

TAIL_SAMPLING_CONFIG = """
# Aggiungere a otel-collector-config.yaml (processors section)
# Richiede: otel/opentelemetry-collector-contrib (non -core)

processors:
  tail_sampling:
    decision_wait: 10s     # Attende 10s per ricevere tutti gli span del trace
    num_traces: 50000       # Trace in memoria simultaneamente
    expected_new_traces_per_sec: 100
    policies:
      # Campiona TUTTI i trace con errori
      - name: errors-policy
        type: status_code
        status_code: {status_codes: [ERROR]}
      
      # Campiona trace lenti (>2s)
      - name: slow-traces
        type: latency
        latency: {threshold_ms: 2000}
      
      # 5% di tutti gli altri (successi veloci)
      - name: probabilistic-policy
        type: probabilistic
        probabilistic: {sampling_percentage: 5}
      
      # Regola composita: AND tra conditions
      - name: critical-service-errors
        type: and
        and:
          and_sub_policy:
            - name: service-filter
              type: string_attribute
              string_attribute: {key: service.name, values: [ordini-worker]}
            - name: error-filter
              type: status_code
              status_code: {status_codes: [ERROR]}
"""

if __name__ == "__main__":
    guida_sampling()
    print("Tail sampling config per il collector:")
    print(TAIL_SAMPLING_CONFIG)
```

---

## PART D — Correlazione Log-Trace-Metric

### D1 — Structlog con Trace Context

```python
#!/usr/bin/env python3
# file: app/logging_correlato.py
"""
Correlazione log con trace context.
Ogni log ha trace_id e span_id → correlabile in Grafana/Elasticsearch.
"""
from __future__ import annotations

import logging
import asyncio
from opentelemetry import trace
import structlog

# ─── Structlog con trace context injection ────────────────────────────────────

def inject_trace_context(logger, method, event_dict):
    """Processor structlog: aggiunge trace_id e span_id al log."""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        ctx = current_span.get_span_context()
        event_dict["trace_id"] = f"{ctx.trace_id:032x}"
        event_dict["span_id"] = f"{ctx.span_id:016x}"
        event_dict["trace_sampled"] = bool(ctx.trace_flags & trace.TraceFlags.SAMPLED)
    return event_dict


def configura_structlog():
    """Configura structlog con trace context e JSON output."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            inject_trace_context,  # Custom: aggiunge trace_id/span_id
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),  # Output JSON
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
    return structlog.get_logger()


async def demo_correlazione():
    """
    Dimostra correlazione log-trace.
    Ogni log emesso dentro uno span ha trace_id e span_id.
    → In Grafana: click sul trace_id nel log → apri Jaeger automaticamente.
    """
    from app.otel_setup import configura_otel
    TRACER, _ = configura_otel("logging-demo")
    log = configura_structlog()
    
    with TRACER.start_as_current_span("demo.operazione") as span:
        log.info("Inizio operazione", ordine_id="ORD-001")
        
        with TRACER.start_as_current_span("demo.sub_step") as sub_span:
            log.info("Esecuzione sub-step", parametro="valore")
            await asyncio.sleep(0.001)
            log.info("Sub-step completato")
        
        log.info("Operazione completata", durata_ms=42)
    
    print("\n↑ I log JSON sopra contengono trace_id e span_id")
    print("In Grafana/Loki: filtra per trace_id e poi apri Jaeger per vedere il trace")


# ─── Dashboard Grafana — query di esempio ─────────────────────────────────────

GRAFANA_QUERIES = {
    "latenza_p95": """
        histogram_quantile(0.95, 
          rate(otel_ordini_latenza_ms_bucket[5m])
        )
    """,
    
    "error_rate": """
        rate(otel_ordini_falliti_totale_total[5m])
        /
        rate(otel_ordini_processati_totale_total[5m])
        * 100
    """,
    
    "throughput": """
        rate(otel_ordini_processati_totale_total[1m]) * 60
    """,
    
    "importo_medio": """
        rate(otel_ordini_importo_eur_sum[5m])
        /
        rate(otel_ordini_importo_eur_count[5m])
    """,
}


if __name__ == "__main__":
    asyncio.run(demo_correlazione())
    print("\n=== QUERY GRAFANA UTILI ===")
    for nome, query in GRAFANA_QUERIES.items():
        print(f"\n{nome}:{query}")
```

---

## Esercizi

### Esercizio 1 — Avvia lo Stack e Visualizza un Trace (30 min)

```bash
cd collector
docker compose -f docker-compose-otel.yml up -d

# Verifica health
curl http://localhost:13133/    # OTel Collector health
curl http://localhost:16686/    # Jaeger UI
curl http://localhost:9090/     # Prometheus

# Esegui il worker
python app/workflow_worker.py

# In Jaeger (http://localhost:16686):
# Service: ordini-worker
# Operation: processa_ordine
# → Dovresti vedere la timeline con span annidati
```

### Esercizio 2 — Aggiungi uno Span Custom (20 min)

Aggiungi un nuovo span `"cache.lookup"` dentro `processa_ordine` che:
- Controlla in-memory se l'ordine è già stato visto
- Imposta attributo `cache.hit: true/false`
- Registra `cache.latenza_ms`

### Esercizio 3 — Configura Tail Sampling (30 min)

Modifica `otel-collector-config.yaml` aggiungendo `tail_sampling` come processor.
Verifica in Jaeger che:
- Gli ordini con errore compaiono sempre (100% campionamento)
- Gli ordini ok compaiono solo nel 5% dei casi

---

## Script di Verifica Prerequisiti

```python
#!/usr/bin/env python3
# file: verifica_prerequisiti.py
"""Verifica che l'ambiente per il lab OTel sia pronto."""
import subprocess
import sys

def check(nome, cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        ok = result.returncode == 0
        print(f"  {'[OK]' if ok else '[FAIL]'} {nome}")
        return ok
    except Exception as e:
        print(f"  [FAIL] {nome}: {e}")
        return False

def check_import(modulo):
    try:
        __import__(modulo)
        print(f"  [OK] Python: {modulo}")
        return True
    except ImportError:
        print(f"  [FAIL] Python: {modulo} — pip install {modulo}")
        return False

print("Verifica prerequisiti OTel Lab...")
results = [
    check("Python 3.11+", ["python3", "-c", "import sys; assert sys.version_info >= (3,11)"]),
    check("Docker", ["docker", "info"]),
    check_import("opentelemetry.sdk.trace"),
    check_import("opentelemetry.exporter.otlp.proto.grpc.trace_exporter"),
    check_import("httpx"),
    check_import("structlog"),
]
print(f"\n{'Tutti prerequisiti OK!' if all(results) else 'Alcune dipendenze mancanti — vedi [FAIL] sopra'}")
sys.exit(0 if all(results) else 1)
```

---

## Riferimenti

- OpenTelemetry Python Docs: https://opentelemetry.io/docs/instrumentation/python/
- W3C TraceContext: https://www.w3.org/TR/trace-context/
- Jaeger Docs: https://www.jaegertracing.io/docs/
- OTel Collector Contrib: https://github.com/open-telemetry/opentelemetry-collector-contrib
- Modulo sorgente: `23-osservabilita-workflow-otel.md`
