---
corso: "Programmazione Python"
fase: "6 — DevOps e Distribuzione"
modulo: "31"
titolo: "Osservabilità — OpenTelemetry e Prometheus"
versione: "OTel SDK 1.x / prometheus_client 0.21+"
livello: "Avanzato"
prerequisiti:
  - "07 — Error Handling e Logging"
  - "11 — Web Framework"
  - "26 — Docker"
obiettivi:
  - "Implementare tracing distribuito con OpenTelemetry SDK"
  - "Esporre metriche Prometheus da applicazioni Python"
  - "Correlare trace, log e metriche per observability completa"
  - "Configurare exporter per Jaeger, Grafana e collector OTel"
  - "Instrumentare automaticamente framework web (FastAPI, Django, Flask)"
  - "Definire SLI/SLO e alert basati su metriche"
tag: [observability, OpenTelemetry, Prometheus, tracing, metriche, Grafana, Jaeger, SLI-SLO]
---

# Osservabilita Python — OpenTelemetry e Prometheus — Guida Completa

> **Modulo 31** · **Aggiornamento:** 2026-05-24 · **Versione:** OTel SDK 1.x / prometheus_client 0.21+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Error Handling e Logging](07-error-handling-e-logging.md), [Web Framework](11-web-framework.md), [Docker](26-docker-per-python.md)
>
> Al termine di questo modulo saprai:
> 1. Implementare tracing distribuito con OpenTelemetry SDK
> 2. Esporre metriche Prometheus da applicazioni Python
> 3. Correlare trace, log e metriche per observability completa
> 4. Configurare exporter per Jaeger, Grafana e collector OTel
> 5. Instrumentare automaticamente framework web (FastAPI, Django, Flask)
> 6. Definire SLI/SLO e alert basati su metriche
>
> **Tempo stimato:** 6-8 ore · **Livello:** Avanzato

## Idee guida

1. **I tre pilastri dell'osservabilita: traces, metrics, logs — correlati tramite trace_id.**
2. **OTel SDK Python: TracerProvider, MeterProvider, LoggerProvider unificati in un unico framework.**
3. **Auto-instrumentation per FastAPI, Django, Flask, SQLAlchemy, requests, redis — zero-code coverage.**
4. **prometheus_client per custom metrics + scrape endpoint; PromQL + Grafana per dashboarding e alerting.**


## Indice

1. [Panoramica](#panoramica)
2. [OpenTelemetry SDK Setup](#opentelemetry-sdk-setup)
3. [Traces](#traces)
4. [Metrics con OpenTelemetry](#metrics-con-opentelemetry)
5. [Logs con OpenTelemetry](#logs-con-opentelemetry)
6. [Auto-Instrumentation](#auto-instrumentation)
7. [Prometheus Client Library](#prometheus-client-library)
8. [Distributed Tracing](#distributed-tracing)
9. [Custom Metrics Design](#custom-metrics-design)
10. [Structured Logging](#structured-logging)
11. [APM Integration](#apm-integration)
12. [Error Tracking e Sentry](#error-tracking-e-sentry)
13. [Profiling in Produzione](#profiling-in-produzione)
14. [Health Check e Readiness Probe](#health-check-e-readiness-probe)
15. [Docker e Kubernetes Observability](#docker-e-kubernetes-observability)
16. [Grafana Dashboard e PromQL](#grafana-dashboard-e-promql)
17. [Alerting](#alerting)
18. [Guida Implementativa — Stack Completo](#guida-implementativa--stack-completo)
19. [Troubleshooting](#troubleshooting)
20. [FAQ](#faq)
21. [Best Practices](#best-practices)
22. [Correlazione Trace-Metric-Log e Grafana Stack](#correlazione-trace-metric-log-e-grafana-stack)
23. [Impatto sulle Performance dell'Instrumentazione](#impatto-sulle-performance-dellinstrumentazione)
24. [Testing del Codice di Osservabilita](#testing-del-codice-di-osservabilita)
25. [Esercizi](#esercizi)
26. [Letture](#letture)
27. [Glossario](#glossario)

---

## Panoramica

L'osservabilita e la capacita di comprendere lo stato interno di un sistema a partire dai segnali che esso emette verso l'esterno. Non si tratta semplicemente di monitoraggio: il monitoraggio risponde a domande note in anticipo ("il CPU e sopra l'80%?"), mentre l'osservabilita consente di porre domande nuove a sistemi che non si conoscono completamente — ed e esattamente cio che serve quando si investigano incidenti in architetture distribuite.

### I tre pilastri

Il modello classico identifica tre categorie di segnali di telemetria:

**Traces** — Rappresentano il percorso di una singola richiesta attraverso il sistema. Ogni trace e composto da uno o piu span, ognuno dei quali descrive un'unita di lavoro: una chiamata HTTP, una query al database, un'operazione su una coda. I trace sono lo strumento primario per diagnosticare latenza e colli di bottiglia in architetture a microservizi.

**Metrics** — Sono valori numerici aggregati nel tempo. Un counter che conta le richieste HTTP, un histogram che traccia la distribuzione della latenza, un gauge che misura le connessioni attive al database. Le metriche sono economiche da raccogliere, efficienti da archiviare e la base per dashboarding e alerting.

**Logs** — Sono eventi discreti con timestamp e contesto. Ogni riga di log racconta qualcosa che e accaduto in un momento specifico. I log strutturati (JSON) con `trace_id` e `span_id` iniettati automaticamente diventano correlabili con traces e metrics, creando un sistema di osservabilita unificato.

### Perche OpenTelemetry

OpenTelemetry (OTel) e il progetto CNCF che unifica la generazione di telemetria. Prima di OTel, ogni vendor (Datadog, New Relic, Jaeger, Zipkin) richiedeva la propria libreria di instrumentazione. Il risultato era vendor lock-in e duplicazione di codice.

OTel risolve il problema separando due preoccupazioni:

1. **Generazione dei segnali** — L'SDK OTel genera traces, metrics e logs con un'API unica e standardizzata.
2. **Esportazione dei segnali** — Gli exporter inviano i dati a qualsiasi backend: Jaeger, Zipkin, Prometheus, Datadog, Grafana Tempo, Elastic APM, o qualsiasi sistema che supporti il protocollo OTLP.

Questa separazione significa che si instrumenta il codice una sola volta, e si sceglie il backend in fase di deployment — non in fase di sviluppo.

### Perche Prometheus

Prometheus e il sistema di monitoraggio e alerting open-source dominante nell'ecosistema cloud-native. Il suo modello pull-based (Prometheus scrapa periodicamente gli endpoint `/metrics` delle applicazioni) e semplice, affidabile e non richiede un agent esterno. PromQL, il suo linguaggio di query, e potente e flessibile. Insieme a Grafana, forma lo stack di dashboarding piu diffuso al mondo.

La libreria `prometheus_client` per Python espone metriche nel formato nativo Prometheus, complementando perfettamente l'ecosistema OTel.

### Architettura di riferimento

```
┌──────────────┐      OTLP       ┌──────────────────┐
│  Python App  │ ───────────────→ │  OTel Collector  │
│  (OTel SDK)  │                  │                  │
│              │  /metrics (pull) │                  │
│  prometheus_ │ ←────────────── │                  │
│  client      │    Prometheus    │                  │
└──────────────┘                  └──────┬───────────┘
                                         │
                        ┌────────────────┼────────────────┐
                        ▼                ▼                ▼
                 ┌──────────┐    ┌──────────┐    ┌──────────┐
                 │  Jaeger  │    │  Tempo   │    │   Loki   │
                 │ (traces) │    │ (traces) │    │  (logs)  │
                 └──────────┘    └──────────┘    └──────────┘
```

L'OTel Collector funge da hub centrale: riceve telemetria via OTLP, la processa (batching, sampling, arricchimento) e la inoltra ai backend appropriati. Non e strettamente necessario — le applicazioni possono esportare direttamente ai backend — ma in produzione e quasi sempre presente perche disaccoppia l'applicazione dalla configurazione del backend.

---

## OpenTelemetry SDK Setup

La configurazione dell'SDK OTel per Python richiede tre provider — uno per ogni pilastro della telemetria — piu una Resource che identifica il servizio.

### Installazione

```bash
# Core SDK
pip install opentelemetry-api opentelemetry-sdk

# Exporter OTLP (traces + metrics + logs)
pip install opentelemetry-exporter-otlp-proto-grpc
# oppure HTTP:
pip install opentelemetry-exporter-otlp-proto-http

# Exporter specifici
pip install opentelemetry-exporter-jaeger
pip install opentelemetry-exporter-prometheus

# Auto-instrumentation
pip install opentelemetry-distro opentelemetry-instrumentation
opentelemetry-bootstrap -a install   # installa tutte le instrumentazioni rilevate
```

### Resource

La `Resource` descrive l'entita che produce la telemetria. Ogni span, metric e log emesso dall'applicazione portera con se questi attributi. La Resource segue le Semantic Conventions di OTel, un vocabolario standardizzato che garantisce coerenza tra servizi scritti in linguaggi diversi.

```python
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: "ordini-api",
    ResourceAttributes.SERVICE_VERSION: "2.4.1",
    ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "production",
    ResourceAttributes.SERVICE_NAMESPACE: "ecommerce",
    ResourceAttributes.SERVICE_INSTANCE_ID: "ordini-api-pod-7b4f9",
    "team.name": "platform-backend",
})
```

L'attributo `service.name` e obbligatorio. Senza di esso, tutti i segnali verranno raggruppati sotto un nome generico, rendendo impossibile il filtraggio per servizio nei backend di osservabilita.

### TracerProvider

Il `TracerProvider` e il punto di ingresso per la generazione di traces. Configura come gli span vengono processati e dove vengono inviati.

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)

provider = TracerProvider(resource=resource)

# Exporter OTLP verso il Collector
otlp_exporter = OTLPSpanExporter(
    endpoint="http://otel-collector:4317",
    insecure=True,  # solo in dev; in prod usare TLS
)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Console exporter per debug locale
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

trace.set_tracer_provider(provider)
```

Il `BatchSpanProcessor` accumula gli span in un buffer e li invia in batch periodicamente. E l'opzione consigliata per la produzione. Il `SimpleSpanProcessor` invia ogni span immediatamente — utile solo per debugging perche impatta la latenza dell'applicazione.

Parametri di tuning del `BatchSpanProcessor`:

| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `max_queue_size` | 2048 | Span in coda prima del drop |
| `schedule_delay_millis` | 5000 | Intervallo di invio in ms |
| `max_export_batch_size` | 512 | Span per batch |
| `export_timeout_millis` | 30000 | Timeout per singolo export |

### MeterProvider

Il `MeterProvider` gestisce la raccolta e l'esportazione delle metriche.

```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader,
    ConsoleMetricExporter,
)
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter,
)

otlp_metric_exporter = OTLPMetricExporter(
    endpoint="http://otel-collector:4317",
    insecure=True,
)

metric_reader = PeriodicExportingMetricReader(
    otlp_metric_exporter,
    export_interval_millis=15000,  # ogni 15 secondi
)

meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[metric_reader],
)
metrics.set_meter_provider(meter_provider)
```

Il `PeriodicExportingMetricReader` raccoglie le metriche a intervalli regolari e le invia all'exporter configurato. Per Prometheus si usa invece il `PrometheusMetricReader`, che espone un endpoint HTTP scrapabile.

### LoggerProvider

Il `LoggerProvider` e il terzo pilastro. OTel non rimpiazza `logging` di Python — piuttosto, fornisce un bridge che cattura i log emessi dalla libreria standard e li arricchisce con il contesto di tracing.

```python
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import (
    BatchLogRecordProcessor,
    ConsoleLogExporter,
)
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)

logger_provider = LoggerProvider(resource=resource)

otlp_log_exporter = OTLPLogExporter(
    endpoint="http://otel-collector:4317",
    insecure=True,
)
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(otlp_log_exporter)
)

set_logger_provider(logger_provider)
```

### Configurazione tramite variabili d'ambiente

L'SDK OTel supporta la configurazione completa tramite variabili d'ambiente, che e il metodo raccomandato per la produzione perche disaccoppia la configurazione dal codice.

```bash
export OTEL_SERVICE_NAME="ordini-api"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
export OTEL_TRACES_SAMPLER="parentbased_traceidratio"
export OTEL_TRACES_SAMPLER_ARG="0.1"
export OTEL_METRICS_EXPORTER="otlp"
export OTEL_LOGS_EXPORTER="otlp"
export OTEL_RESOURCE_ATTRIBUTES="deployment.environment=production,team.name=platform"
export OTEL_PYTHON_LOG_CORRELATION="true"
```

Con queste variabili impostate, l'auto-instrumentation configura tutto automaticamente:

```bash
opentelemetry-instrument python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### Shutdown corretto

E fondamentale chiamare `shutdown()` sui provider prima che il processo termini, altrimenti i dati nel buffer vengono persi.

```python
import atexit

def shutdown_telemetry():
    provider.shutdown()
    meter_provider.shutdown()
    logger_provider.shutdown()

atexit.register(shutdown_telemetry)
```

In un'applicazione FastAPI si puo usare il lifecycle event:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    provider.shutdown()
    meter_provider.shutdown()
    logger_provider.shutdown()

app = FastAPI(lifespan=lifespan)
```

### Architettura Interna dell'SDK

Comprendere la pipeline interna dell'SDK aiuta a personalizzare ogni fase del percorso dei dati di telemetria.

#### Pipeline di elaborazione degli span

Il flusso interno di un span segue questo percorso:

```
TracerProvider
  └─ Tracer.start_span()
       └─ Sampler → SamplingResult (RECORD_AND_SAMPLE / RECORD_ONLY / DROP)
            └─ SpanProcessor.on_start(span, parent_context)
                 └─ [span attivo — l'applicazione lo popola con attributi, eventi, link]
                      └─ span.end()
                           └─ SpanProcessor.on_end(ReadableSpan)
                                └─ SpanExporter.export([ReadableSpan])
```

Il **Sampler** decide se il dato vale la pena di essere registrato prima che lo span venga creato. Lo **SpanProcessor** e il punto di aggancio per logica custom — `on_start` permette di arricchire lo span appena creato, `on_end` lo riceve come oggetto immutabile. L'**Exporter** serializza e trasmette gli span completati verso il backend.

#### Implementare un SpanProcessor custom

Un processor che aggiunge automaticamente informazioni sul deployment:

```python
from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan
from opentelemetry.context import Context
import os

class DeploymentEnrichmentProcessor(SpanProcessor):
    """Arricchisce ogni span con metadati del deployment."""

    def __init__(self):
        self._version = os.getenv("APP_VERSION", "unknown")
        self._ring = os.getenv("DEPLOY_RING", "stable")
        self._region = os.getenv("AWS_REGION", "unknown")

    def on_start(self, span, parent_context: Context | None = None) -> None:
        span.set_attribute("deploy.version", self._version)
        span.set_attribute("deploy.ring", self._ring)
        span.set_attribute("deploy.region", self._region)

    def on_end(self, span: ReadableSpan) -> None:
        pass  # ReadableSpan e immutabile — arricchimento solo in on_start

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
```

Per usarlo, aggiungerlo al `TracerProvider`:

```python
provider.add_span_processor(DeploymentEnrichmentProcessor())
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
```

L'ordine conta: i processor vengono eseguiti in sequenza. Mettere l'arricchimento prima dell'export garantisce che gli attributi siano presenti quando lo span viene serializzato.

#### Implementare un Exporter custom

Uno scheletro per un exporter che invia span a un sistema proprietario:

```python
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from typing import Sequence

class CustomBackendExporter(SpanExporter):
    """Esporta span verso un backend interno."""

    def __init__(self, endpoint: str, api_key: str):
        self._endpoint = endpoint
        self._api_key = api_key
        self._session = None  # inizializza lazy

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        try:
            payload = [self._serialize(s) for s in spans]
            # invio HTTP/gRPC al backend
            response = self._send(payload)
            if response.ok:
                return SpanExportResult.SUCCESS
            return SpanExportResult.FAILURE
        except Exception:
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        if self._session:
            self._session.close()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True

    def _serialize(self, span: ReadableSpan) -> dict:
        return {
            "trace_id": format(span.context.trace_id, "032x"),
            "span_id": format(span.context.span_id, "016x"),
            "name": span.name,
            "start_ns": span.start_time,
            "end_ns": span.end_time,
            "attributes": dict(span.attributes or {}),
            "status": span.status.status_code.name,
        }
```

#### API dei Propagator

I propagator iniettano ed estraggono il contesto di tracing dai carrier (tipicamente header HTTP). L'interfaccia `TextMapPropagator` definisce due metodi:

- **`inject(carrier, context, setter)`** — serializza `trace_id`, `span_id` e `trace_flags` nel carrier
- **`extract(carrier, context, getter)`** — deserializza il contesto dal carrier e restituisce un nuovo `Context`

Implementazione di un propagator custom (es. per un sistema legacy con header proprietari):

```python
from opentelemetry.context.propagation import TextMapPropagator
from opentelemetry import trace
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags

class LegacyPropagator(TextMapPropagator):
    """Propagator per sistemi legacy con header X-Legacy-Trace."""
    HEADER = "x-legacy-trace"

    def inject(self, carrier, context=None, setter=None):
        span = trace.get_current_span(context)
        ctx = span.get_span_context()
        if ctx.is_valid:
            value = f"{format(ctx.trace_id, '032x')}:{format(ctx.span_id, '016x')}"
            if setter:
                setter.set(carrier, self.HEADER, value)
            else:
                carrier[self.HEADER] = value

    def extract(self, carrier, context=None, getter=None):
        if getter:
            values = getter.get(carrier, self.HEADER)
            value = values[0] if values else None
        else:
            value = carrier.get(self.HEADER)
        if not value:
            return context
        parts = value.split(":")
        if len(parts) != 2:
            return context
        trace_id = int(parts[0], 16)
        span_id = int(parts[1], 16)
        span_ctx = SpanContext(
            trace_id=trace_id,
            span_id=span_id,
            is_remote=True,
            trace_flags=TraceFlags(0x01),
        )
        return trace.set_span_in_context(NonRecordingSpan(span_ctx), context)

    @property
    def fields(self) -> set[str]:
        return {self.HEADER}
```

Per comporre propagator multipli (es. W3C + legacy):

```python
from opentelemetry.propagators import set_global_textmap
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.textmap import TraceContextTextMapPropagator

set_global_textmap(CompositePropagator([
    TraceContextTextMapPropagator(),
    LegacyPropagator(),
]))
```

Questo permette la migrazione graduale: il sistema accetta entrambi i formati e inietta entrambi, consentendo ai servizi legacy di partecipare al tracing distribuito durante la transizione.

---

## Traces

I traces sono il segnale piu potente per comprendere il flusso di una richiesta attraverso un sistema distribuito. Ogni trace e un grafo aciclico diretto (DAG) di span, dove ogni span rappresenta un'operazione con un inizio, una durata e una fine.

### Anatomia di uno span

Uno span contiene:

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `trace_id` | 128-bit | Identifica l'intera trace |
| `span_id` | 64-bit | Identifica questo specifico span |
| `parent_span_id` | 64-bit | Span padre (null per root span) |
| `name` | string | Nome dell'operazione |
| `kind` | enum | `SERVER`, `CLIENT`, `PRODUCER`, `CONSUMER`, `INTERNAL` |
| `start_time` | timestamp | Inizio dell'operazione |
| `end_time` | timestamp | Fine dell'operazione |
| `status` | enum | `UNSET`, `OK`, `ERROR` |
| `attributes` | dict | Coppie chiave-valore di contesto |
| `events` | list | Eventi puntuali durante lo span |
| `links` | list | Riferimenti ad altri span/trace |

### Creazione manuale di span

```python
from opentelemetry import trace

tracer = trace.get_tracer("ordini.service", "2.4.1")

def processa_ordine(ordine_id: str) -> dict:
    with tracer.start_as_current_span(
        "processa_ordine",
        kind=trace.SpanKind.INTERNAL,
        attributes={
            "ordine.id": ordine_id,
            "ordine.tipo": "standard",
        },
    ) as span:
        # Validazione
        with tracer.start_as_current_span("valida_ordine") as val_span:
            risultato = valida(ordine_id)
            val_span.set_attribute("validazione.esito", risultato.esito)

        # Pagamento
        with tracer.start_as_current_span(
            "processa_pagamento",
            kind=trace.SpanKind.CLIENT,
        ) as pay_span:
            try:
                pagamento = chiama_servizio_pagamento(ordine_id)
                pay_span.set_attribute("pagamento.id", pagamento.id)
                pay_span.set_attribute("pagamento.importo", pagamento.importo)
            except PagamentoError as e:
                pay_span.set_status(
                    trace.StatusCode.ERROR,
                    description=str(e),
                )
                pay_span.record_exception(e)
                raise

        # Evento nel contesto dello span padre
        span.add_event(
            "ordine_completato",
            attributes={"ordine.id": ordine_id},
        )
        span.set_status(trace.StatusCode.OK)
        return {"status": "completato"}
```

### Attributi — Semantic Conventions

OTel definisce Semantic Conventions per attributi standard. Usare nomi standardizzati garantisce che i backend di osservabilita possano interpretare correttamente i dati senza configurazione personalizzata.

```python
from opentelemetry.semconv.trace import SpanAttributes

with tracer.start_as_current_span("http_request") as span:
    span.set_attribute(SpanAttributes.HTTP_METHOD, "POST")
    span.set_attribute(SpanAttributes.HTTP_URL, "https://api.pagamenti.it/v1/charge")
    span.set_attribute(SpanAttributes.HTTP_STATUS_CODE, 200)
    span.set_attribute(SpanAttributes.HTTP_REQUEST_CONTENT_LENGTH, 1234)
    span.set_attribute(SpanAttributes.NET_PEER_NAME, "api.pagamenti.it")
    span.set_attribute(SpanAttributes.NET_PEER_PORT, 443)
```

Per il database:

```python
span.set_attribute(SpanAttributes.DB_SYSTEM, "postgresql")
span.set_attribute(SpanAttributes.DB_NAME, "ordini_db")
span.set_attribute(SpanAttributes.DB_OPERATION, "SELECT")
span.set_attribute(SpanAttributes.DB_STATEMENT, "SELECT * FROM ordini WHERE id = $1")
```

**Attenzione alla sicurezza**: non inserire mai valori sensibili (password, token, PII) negli attributi degli span. I dati di tracing vengono archiviati in backend accessibili al team di operations. Usare sanitizzazione o omissione.

### Events

Gli eventi sono timestamp puntuali all'interno di uno span. A differenza degli attributi (che descrivono proprieta dello span), gli eventi descrivono qualcosa che e successo durante lo span.

```python
span.add_event(
    "cache_miss",
    attributes={
        "cache.key": "prodotto:12345",
        "cache.backend": "redis",
    },
)

span.add_event(
    "retry_attempt",
    attributes={
        "retry.count": 2,
        "retry.delay_ms": 500,
        "retry.reason": "connection_timeout",
    },
)
```

L'evento piu importante e `record_exception`, che cattura automaticamente tipo, messaggio e stacktrace dell'eccezione:

```python
try:
    risultato = operazione_rischiosa()
except Exception as e:
    span.record_exception(e)
    span.set_status(trace.StatusCode.ERROR, str(e))
    raise
```

### Links

I link collegano uno span ad altri span in traces diverse. Sono utili quando esiste una relazione causale ma non parent-child — ad esempio, un consumer che processa un batch di messaggi puo linkare agli span dei producer originali.

```python
from opentelemetry.trace import Link

# Contesto del messaggio in arrivo dalla coda
link_context = trace.get_current_span().get_span_context()

with tracer.start_as_current_span(
    "processa_batch",
    links=[
        Link(link_context, attributes={"messaggio.id": "msg-001"}),
        Link(altro_context, attributes={"messaggio.id": "msg-002"}),
    ],
) as span:
    processa_messaggi(batch)
```

### SpanKind

Lo `SpanKind` indica il ruolo dello span nella comunicazione:

| Kind | Quando usarlo |
|------|---------------|
| `SERVER` | Il servizio riceve una richiesta da un client |
| `CLIENT` | Il servizio invia una richiesta a un servizio esterno |
| `PRODUCER` | Il servizio invia un messaggio a una coda/topic |
| `CONSUMER` | Il servizio riceve un messaggio da una coda/topic |
| `INTERNAL` | Operazione interna al servizio |

### Strategie di sampling

In produzione con alto traffico, raccogliere il 100% delle traces e proibitivo in termini di costi di storage e banda di rete. Il sampling decide quali traces conservare.

**AlwaysOnSampler** — Cattura tutto. Utile solo in sviluppo.

```python
from opentelemetry.sdk.trace.sampling import ALWAYS_ON

provider = TracerProvider(resource=resource, sampler=ALWAYS_ON)
```

**TraceIdRatioBasedSampler** — Campiona una percentuale fissa delle traces basata sull'hash del `trace_id`.

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Campiona il 10% delle traces
sampler = TraceIdRatioBased(0.1)
provider = TracerProvider(resource=resource, sampler=sampler)
```

**ParentBasedSampler** — Rispetta la decisione di sampling del servizio chiamante. Se il parent span e stato campionato, anche i figli lo saranno. Questo e cruciale per garantire traces complete nei sistemi distribuiti.

```python
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

sampler = ParentBased(root=TraceIdRatioBased(0.1))
provider = TracerProvider(resource=resource, sampler=sampler)
```

**Tail-Based Sampling** — Decide se mantenere una trace dopo che tutti gli span sono stati raccolti. Permette di campionare il 100% delle traces con errori e solo una percentuale delle traces riuscite. Questo tipo di sampling non avviene nell'SDK ma nell'OTel Collector.

```yaml
# otel-collector-config.yaml
processors:
  tail_sampling:
    decision_wait: 10s
    policies:
      - name: errori-sempre
        type: status_code
        status_code:
          status_codes: [ERROR]
      - name: latenza-alta
        type: latency
        latency:
          threshold_ms: 2000
      - name: percentuale-base
        type: probabilistic
        probabilistic:
          sampling_percentage: 5
```

### Exporter

| Exporter | Protocollo | Uso tipico |
|----------|------------|------------|
| `OTLPSpanExporter` (gRPC) | OTLP/gRPC | Standard; OTel Collector |
| `OTLPSpanExporter` (HTTP) | OTLP/HTTP | Firewall-friendly |
| `JaegerExporter` | Thrift/gRPC | Direct-to-Jaeger (deprecato, usare OTLP) |
| `ZipkinExporter` | HTTP/JSON | Direct-to-Zipkin |
| `ConsoleSpanExporter` | stdout | Debug locale |

```python
# Esempio: export diretto a Jaeger via OTLP
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)

jaeger_exporter = OTLPSpanExporter(
    endpoint="http://jaeger:4317",
    insecure=True,
)
```

---

## Metrics con OpenTelemetry

Le metriche OTel seguono un modello a strumenti (instruments): si crea uno strumento, lo si utilizza per registrare misurazioni, e il MeterProvider si occupa di aggregarle e esportarle.

### Tipi di strumento

| Strumento | Tipo | Esempio |
|-----------|------|---------|
| `Counter` | Monotono crescente | Richieste totali, errori |
| `UpDownCounter` | Crescente o decrescente | Connessioni attive, jobs in coda |
| `Histogram` | Distribuzione di valori | Latenza, dimensione payload |
| `Gauge` | Valore puntuale | Temperatura, utilizzo memoria |
| `ObservableCounter` | Counter asincrono | Bytes totali letti dal disco |
| `ObservableGauge` | Gauge asincrono | Utilizzo CPU |
| `ObservableUpDownCounter` | UpDownCounter asincrono | Thread attivi |

### Counter

```python
meter = metrics.get_meter("ordini.service", "2.4.1")

richieste_counter = meter.create_counter(
    name="http.server.request.count",
    description="Numero totale di richieste HTTP ricevute",
    unit="1",
)

def handle_request(method: str, status_code: int, endpoint: str):
    richieste_counter.add(
        1,
        attributes={
            "http.method": method,
            "http.status_code": status_code,
            "http.route": endpoint,
        },
    )
```

### Histogram

L'histogram e lo strumento piu importante per le metriche di latenza. Registra la distribuzione dei valori, non solo la media.

```python
latenza_histogram = meter.create_histogram(
    name="http.server.request.duration",
    description="Durata delle richieste HTTP in secondi",
    unit="s",
)

import time

def handle_request():
    start = time.perf_counter()
    try:
        risultato = processa()
        return risultato
    finally:
        durata = time.perf_counter() - start
        latenza_histogram.record(
            durata,
            attributes={
                "http.method": "GET",
                "http.route": "/api/ordini",
                "http.status_code": 200,
            },
        )
```

### Gauge

```python
# Gauge sincrono (OTel >= 1.22)
coda_gauge = meter.create_gauge(
    name="queue.depth",
    description="Numero di messaggi in coda",
    unit="1",
)

def aggiorna_coda(profondita: int):
    coda_gauge.set(profondita, attributes={"queue.name": "ordini"})
```

Per misurazioni asincrone (il valore viene letto al momento dell'export):

```python
import psutil

def leggi_cpu(options):
    yield metrics.Observation(
        psutil.cpu_percent(),
        attributes={"cpu.core": "all"},
    )

meter.create_observable_gauge(
    name="system.cpu.utilization",
    description="Utilizzo CPU percentuale",
    unit="percent",
    callbacks=[leggi_cpu],
)
```

### UpDownCounter

```python
connessioni = meter.create_up_down_counter(
    name="db.connections.active",
    description="Connessioni al database attive",
    unit="1",
)

def on_connect(db_name: str):
    connessioni.add(1, attributes={"db.name": db_name})

def on_disconnect(db_name: str):
    connessioni.add(-1, attributes={"db.name": db_name})
```

### Views

Le Views consentono di personalizzare l'aggregazione delle metriche lato SDK — ad esempio, per cambiare i bucket di un histogram o per eliminare attributi ad alta cardinalita prima dell'export.

```python
from opentelemetry.sdk.metrics.view import View

# Bucket personalizzati per la latenza HTTP
vista_latenza = View(
    instrument_name="http.server.request.duration",
    aggregation=ExplicitBucketHistogramAggregation(
        boundaries=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    ),
)

# Eliminare un attributo ad alta cardinalita
vista_senza_user_id = View(
    instrument_name="http.server.request.count",
    attribute_keys=["http.method", "http.route", "http.status_code"],
    # user.id viene escluso per evitare esplosione di cardinalita
)

meter_provider = MeterProvider(
    resource=resource,
    metric_readers=[metric_reader],
    views=[vista_latenza, vista_senza_user_id],
)
```

### Exemplars

Gli exemplars collegano un data point di una metrica a un trace specifico. Quando vedi un picco di latenza nel grafico Grafana, l'exemplar ti porta direttamente alla trace che ha generato quel data point.

Gli exemplars sono supportati dall'SDK OTel e vengono automaticamente collegati quando un trace context e presente al momento della registrazione della metrica.

```python
# Il collegamento avviene automaticamente se c'e un trace context attivo
# quando si chiama .record() o .add() su uno strumento

with tracer.start_as_current_span("handle_request"):
    # Questo histogram data point avra un exemplar con
    # trace_id e span_id dello span corrente
    latenza_histogram.record(0.345, attributes={"http.route": "/api/ordini"})
```

In Grafana, gli exemplars appaiono come punti cliccabili sovrapposti ai grafici metrici. Cliccando, si naviga direttamente alla trace corrispondente in Tempo o Jaeger.

---

## Logs con OpenTelemetry

Il modello OTel per i log non rimpiazza `logging` di Python. Invece, fornisce un bridge che intercetta i log emessi dalla libreria standard e li arricchisce con il contesto di tracing (`trace_id`, `span_id`), li converte nel formato OTel LogRecord e li esporta via OTLP.

### Logging Bridge

```python
import logging
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Configura il LoggerProvider
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(OTLPLogExporter(endpoint="http://otel-collector:4317"))
)
set_logger_provider(logger_provider)

# Attiva il bridge con logging stdlib
LoggingInstrumentor().instrument(set_logging_format=True)

# Ora ogni log emesso con logging stdlib avra trace_id e span_id
logger = logging.getLogger(__name__)

with tracer.start_as_current_span("processa_ordine"):
    logger.info("Elaborazione ordine %s", ordine_id)
    # Il log conterra automaticamente:
    # trace_id=abc123...
    # span_id=def456...
    # trace_flags=01
```

### Formato log con trace context

Con `LoggingInstrumentor(set_logging_format=True)`, il formato log diventa:

```
%(asctime)s %(levelname)s [%(name)s] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] - %(message)s
```

Questo consente la correlazione diretta tra log e trace: in Grafana, da un log si puo navigare direttamente alla trace corrispondente e viceversa.

### Integrazione con logging strutturato

Per log JSON strutturati con OTel context:

```python
import logging
import json

class OTelJsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        # OTel aggiunge questi attributi al record
        if hasattr(record, "otelTraceID"):
            log_data["trace_id"] = record.otelTraceID
            log_data["span_id"] = record.otelSpanID
            log_data["trace_flags"] = record.otelTraceFlagsf

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

handler = logging.StreamHandler()
handler.setFormatter(OTelJsonFormatter())
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)
```

### Log severity mapping

| Python Level | OTel Severity |
|-------------|---------------|
| `DEBUG` | `DEBUG` (5) |
| `INFO` | `INFO` (9) |
| `WARNING` | `WARN` (13) |
| `ERROR` | `ERROR` (17) |
| `CRITICAL` | `FATAL` (21) |

---

## Auto-Instrumentation

L'auto-instrumentation di OTel e il modo piu rapido per ottenere osservabilita senza modificare il codice applicativo. Funziona attraverso monkey-patching delle librerie supportate a runtime.

### Installazione e avvio

```bash
# Installa le instrumentazioni per le librerie rilevate nel progetto
pip install opentelemetry-distro
opentelemetry-bootstrap -a install

# Avvia con auto-instrumentation
opentelemetry-instrument \
    --service_name ordini-api \
    --exporter_otlp_endpoint http://otel-collector:4317 \
    --exporter_otlp_protocol grpc \
    python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### FastAPI

```python
# Programmatico (alternativa a opentelemetry-instrument)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()

FastAPIInstrumentor.instrument_app(
    app,
    excluded_urls="/health,/ready,/metrics",
    server_request_hook=aggiungi_attributi_custom,
)

def aggiungi_attributi_custom(span, scope):
    if scope.get("type") == "http":
        span.set_attribute("tenant.id", scope.get("headers", {}).get("x-tenant-id", "unknown"))
```

L'instrumentazione FastAPI genera automaticamente span `SERVER` per ogni richiesta con attributi come `http.method`, `http.route`, `http.status_code`, `http.url`, `net.host.name`.

### Django

```python
# settings.py
INSTALLED_APPS = [
    "opentelemetry.instrumentation.django",
    # ... altre app
]

# Oppure programmatico
from opentelemetry.instrumentation.django import DjangoInstrumentor

DjangoInstrumentor().instrument(
    is_sql_commentor_enabled=True,  # aggiunge trace context ai commenti SQL
)
```

Con `is_sql_commentor_enabled=True`, ogni query SQL emessa da Django ORM conterra un commento con il trace context:

```sql
SELECT * FROM ordini WHERE id = 42
/*traceparent='00-abc123-def456-01'*/
```

Questo permette di correlare le query lente identificate nel database monitor direttamente alla trace OTel.

### Flask

```python
from opentelemetry.instrumentation.flask import FlaskInstrumentor

app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
```

### SQLAlchemy

```python
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

engine = create_engine("postgresql://user:pass@localhost/ordini_db")
SQLAlchemyInstrumentor().instrument(engine=engine)

# Ogni query generera uno span con attributi:
# db.system = "postgresql"
# db.name = "ordini_db"
# db.statement = "SELECT ..."
# db.operation = "SELECT"
```

### requests / httpx / aiohttp

```python
# requests
from opentelemetry.instrumentation.requests import RequestsInstrumentor
RequestsInstrumentor().instrument()

# httpx
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
HTTPXClientInstrumentor().instrument()

# aiohttp client
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
AioHttpClientInstrumentor().instrument()
```

Ogni chiamata HTTP in uscita generera uno span `CLIENT` e propaghera automaticamente il trace context nell'header `traceparent`.

### Redis

```python
from opentelemetry.instrumentation.redis import RedisInstrumentor
RedisInstrumentor().instrument()

# Span generati per ogni comando:
# db.system = "redis"
# db.statement = "GET user:12345"
# net.peer.name = "redis-host"
# net.peer.port = 6379
```

### Celery

```python
from opentelemetry.instrumentation.celery import CeleryInstrumentor
CeleryInstrumentor().instrument()

# Il trace context viene propagato dal producer al worker
# attraverso gli header del messaggio Celery
```

### Tabella riassuntiva instrumentazioni

| Libreria | Pacchetto | Tipo span |
|----------|-----------|-----------|
| FastAPI | `opentelemetry-instrumentation-fastapi` | SERVER |
| Django | `opentelemetry-instrumentation-django` | SERVER |
| Flask | `opentelemetry-instrumentation-flask` | SERVER |
| SQLAlchemy | `opentelemetry-instrumentation-sqlalchemy` | CLIENT |
| requests | `opentelemetry-instrumentation-requests` | CLIENT |
| httpx | `opentelemetry-instrumentation-httpx` | CLIENT |
| aiohttp | `opentelemetry-instrumentation-aiohttp-client` | CLIENT |
| Redis | `opentelemetry-instrumentation-redis` | CLIENT |
| Celery | `opentelemetry-instrumentation-celery` | PRODUCER/CONSUMER |
| psycopg2 | `opentelemetry-instrumentation-psycopg2` | CLIENT |
| grpc | `opentelemetry-instrumentation-grpc` | CLIENT/SERVER |
| boto3 | `opentelemetry-instrumentation-botocore` | CLIENT |
| Kafka | `opentelemetry-instrumentation-confluent-kafka` | PRODUCER/CONSUMER |

### Pattern di Instrumentazione Custom Avanzati

Oltre all'auto-instrumentation, scenari complessi richiedono instrumentazione manuale strutturata. Ecco i pattern piu efficaci.

#### Decoratore per span automatici

Un decoratore riutilizzabile che crea span con attributi contestuali:

```python
import functools
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def traced(
    span_name: str | None = None,
    attributes: dict[str, str] | None = None,
    record_exception: bool = True,
    set_status_on_exception: bool = True,
):
    """Decoratore che wrappa la funzione in uno span OTel."""
    def decorator(func):
        _name = span_name or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(
                _name,
                attributes=attributes or {},
                record_exception=record_exception,
                set_status_on_exception=set_status_on_exception,
            ) as span:
                span.set_attribute("code.function", func.__qualname__)
                return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.start_as_current_span(
                _name,
                attributes=attributes or {},
                record_exception=record_exception,
                set_status_on_exception=set_status_on_exception,
            ) as span:
                span.set_attribute("code.function", func.__qualname__)
                return await func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Uso
@traced("ordini.calcola_totale", attributes={"business.domain": "checkout"})
def calcola_totale(items: list[dict]) -> Decimal:
    ...
```

#### Context propagation in task asincroni

Quando si lanciano task su Celery, thread pool o asyncio, il contesto OTel deve essere propagato esplicitamente:

```python
from opentelemetry import context, trace, baggage

def submit_background_task(pool, func, *args):
    """Propaga il contesto OTel in un thread pool."""
    ctx = context.get_current()
    carrier: dict[str, str] = {}
    # Serializza contesto in carrier
    from opentelemetry.propagators import inject
    inject(carrier)

    def wrapper():
        from opentelemetry.propagators import extract
        token = context.attach(extract(carrier))
        try:
            return func(*args)
        finally:
            context.detach(token)

    return pool.submit(wrapper)
```

Per Celery, usare i signals `before_task_publish` e `task_prerun`:

```python
from celery.signals import before_task_publish, task_prerun
from opentelemetry.propagators import inject, extract

@before_task_publish.connect
def propagate_context_to_celery(headers: dict, **kwargs):
    inject(headers)

@task_prerun.connect
def restore_context_in_worker(task, **kwargs):
    ctx = extract(task.request.headers or {})
    context.attach(ctx)
```

#### Middleware custom per arricchimento span

Un middleware ASGI che aggiunge attributi business-relevant allo span corrente:

```python
class BusinessContextMiddleware:
    """Arricchisce gli span con contesto di business."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            span = trace.get_current_span()
            # Estrai tenant da header
            headers = dict(scope.get("headers", []))
            tenant = headers.get(b"x-tenant-id", b"").decode()
            if tenant:
                span.set_attribute("tenant.id", tenant)
                baggage.set_baggage("tenant.id", tenant)
            # Estrai request-id per correlazione
            request_id = headers.get(b"x-request-id", b"").decode()
            if request_id:
                span.set_attribute("request.id", request_id)
        await self.app(scope, receive, send)
```

#### Wrapping di codice terze parti

Quando una libreria non ha instrumentazione OTel nativa, si puo wrappare:

```python
class InstrumentedCacheClient:
    """Wrapper OTel attorno a un client cache generico."""

    def __init__(self, client, tracer=None):
        self._client = client
        self._tracer = tracer or trace.get_tracer(__name__)

    def get(self, key: str):
        with self._tracer.start_as_current_span(
            "cache.get",
            attributes={"cache.key": key, "cache.system": "memcached"},
        ) as span:
            result = self._client.get(key)
            span.set_attribute("cache.hit", result is not None)
            return result

    def set(self, key: str, value, ttl: int = 300):
        with self._tracer.start_as_current_span(
            "cache.set",
            attributes={"cache.key": key, "cache.ttl": ttl},
        ):
            return self._client.set(key, value, ttl)
```

Questi pattern mantengono il codice di business pulito, concentrando la logica di observability in layer dedicati.

---

## Prometheus Client Library

Mentre OTel fornisce un framework unificato per tutta la telemetria, la libreria `prometheus_client` per Python e lo strumento nativo per esporre metriche nel formato Prometheus. In molti ambienti di produzione le due librerie coesistono: OTel per traces e logs, `prometheus_client` per metriche con scraping diretto.

### Installazione

```bash
pip install prometheus-client
```

### Tipi di metrica

**Counter** — Valore monotono crescente. Si puo solo incrementare (o resettare a zero al riavvio). Usare per: richieste totali, errori totali, byte processati.

```python
from prometheus_client import Counter

RICHIESTE_TOTALI = Counter(
    "http_requests_total",
    "Numero totale di richieste HTTP",
    labelnames=["method", "endpoint", "status_code"],
)

def handle_request(method, endpoint, status):
    RICHIESTE_TOTALI.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status),
    ).inc()
```

**Gauge** — Valore che puo salire e scendere. Usare per: connessioni attive, temperatura, utilizzo memoria, dimensione coda.

```python
from prometheus_client import Gauge

CONNESSIONI_ATTIVE = Gauge(
    "db_connections_active",
    "Connessioni al database attive",
    labelnames=["db_name"],
)

CONNESSIONI_ATTIVE.labels(db_name="ordini").inc()   # +1
CONNESSIONI_ATTIVE.labels(db_name="ordini").dec()   # -1
CONNESSIONI_ATTIVE.labels(db_name="ordini").set(42) # valore assoluto

# Context manager per tracciare operazioni in-flight
RICHIESTE_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Richieste HTTP attualmente in elaborazione",
)

@RICHIESTE_IN_PROGRESS.track_inprogress()
def handle_request():
    # il gauge si incrementa all'ingresso e si decrementa all'uscita
    processa()
```

**Histogram** — Traccia la distribuzione dei valori osservati in bucket predefiniti. Ogni histogram genera automaticamente tre time series: `_bucket`, `_count`, `_sum`.

```python
from prometheus_client import Histogram

LATENZA = Histogram(
    "http_request_duration_seconds",
    "Durata delle richieste HTTP in secondi",
    labelnames=["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Registra un valore
LATENZA.labels(method="GET", endpoint="/api/ordini").observe(0.127)

# Timer decorator
@LATENZA.labels(method="GET", endpoint="/api/ordini").time()
def get_ordini():
    return db.query(Ordine).all()

# Context manager
with LATENZA.labels(method="POST", endpoint="/api/ordini").time():
    crea_ordine(dati)
```

I bucket di default sono: `[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, +Inf]`. Per la maggior parte delle API web, bucket piu granulari sotto i 500ms sono consigliati.

**Summary** — Simile all'histogram ma calcola quantili lato client. Da usare con cautela: i quantili calcolati lato client non sono aggregabili tra istanze.

```python
from prometheus_client import Summary

LATENZA_SUMMARY = Summary(
    "http_request_duration_summary_seconds",
    "Durata richieste HTTP (summary)",
    labelnames=["endpoint"],
)

LATENZA_SUMMARY.labels(endpoint="/api/ordini").observe(0.127)
```

**Regola pratica**: preferire Histogram a Summary quasi sempre. Gli histogram sono aggregabili con `histogram_quantile()` in PromQL, i summary no.

### Labels

Le label sono coppie chiave-valore che aggiungono dimensionalita alle metriche. Ogni combinazione unica di label crea una time series distinta.

```python
# Buon uso delle label: bassa cardinalita
ERRORI = Counter(
    "app_errors_total",
    "Errori applicativi totali",
    labelnames=["error_type", "severity"],
)

ERRORI.labels(error_type="validation", severity="warning").inc()
ERRORI.labels(error_type="database", severity="critical").inc()
```

**Trappola della cardinalita**: ogni combinazione unica di valori di label crea una time series separata in Prometheus. Se si usa `user_id` come label e si hanno 1 milione di utenti, si creano 1 milione di time series — e Prometheus collassa.

```python
# MAI fare questo
RICHIESTE = Counter("requests_total", "Richieste", labelnames=["user_id"])
# Con 1M utenti = 1M time series = OOM Prometheus

# Usare invece aggregazioni:
RICHIESTE = Counter("requests_total", "Richieste", labelnames=["user_tier"])
# "free", "premium", "enterprise" = 3 time series
```

### Exposition — esporre le metriche

```python
from prometheus_client import start_http_server, generate_latest, CONTENT_TYPE_LATEST
import threading

# Opzione 1: server HTTP dedicato su porta separata
start_http_server(port=9090)
# Prometheus scrapa http://app:9090/metrics

# Opzione 2: integrazione con FastAPI
from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/metrics")
def metrics_endpoint():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
```

Per Django:

```python
# urls.py
from django.urls import path
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from django.http import HttpResponse

def prometheus_metrics(request):
    return HttpResponse(
        generate_latest(),
        content_type=CONTENT_TYPE_LATEST,
    )

urlpatterns = [
    path("metrics/", prometheus_metrics),
]
```

### Multiprocess mode

In ambienti con piu worker (gunicorn con `--workers 4`), ogni worker ha il proprio registry Prometheus. Senza configurazione aggiuntiva, ogni scrape vede solo le metriche di un worker. Il multiprocess mode unifica le metriche.

```python
import os
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/tmp/prometheus_multiproc"

from prometheus_client import (
    CollectorRegistry,
    multiprocess,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

def metrics_endpoint():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST,
    )
```

Nella configurazione gunicorn:

```python
# gunicorn.conf.py
import os
from prometheus_client import multiprocess

def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)

bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
```

---

## Distributed Tracing

Il distributed tracing e il meccanismo che permette di seguire una singola richiesta utente attraverso decine di servizi. Funziona grazie alla propagazione del contesto: ogni servizio riceve il trace context dal chiamante, lo usa per creare span figli, e lo propaga alle chiamate in uscita.

### Context Propagation

Il W3C Trace Context e lo standard de facto. Definisce due header HTTP:

- `traceparent`: `00-{trace_id}-{parent_span_id}-{trace_flags}`
- `tracestate`: coppie chiave-valore vendor-specific

```
traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
tracestate: dd=s:1;o:rum,congo=t61rcWkgMzE
```

L'SDK OTel Python configura automaticamente il W3C TraceContext propagator. Per scenari multi-vendor:

```python
from opentelemetry import propagate
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.b3 import B3MultiFormat

# Supporta sia W3C che B3 (Zipkin)
propagate.set_global_textmap(
    CompositePropagator([
        TraceContextTextMapPropagator(),
        B3MultiFormat(),
    ])
)
```

### Propagazione manuale

In scenari dove l'auto-instrumentation non copre (code personalizzate, protocolli binari, message broker custom):

```python
from opentelemetry import context, propagate

# Iniettare il context in un carrier (dict, header HTTP, messaggio)
headers = {}
propagate.inject(headers)
# headers contiene ora {"traceparent": "00-...", "tracestate": "..."}

# Estrarre il context da un carrier ricevuto
ctx = propagate.extract(carrier=headers)
with tracer.start_as_current_span("operazione", context=ctx) as span:
    processa()
```

### Baggage

Il baggage e un meccanismo per propagare coppie chiave-valore attraverso i confini di servizio. A differenza degli attributi degli span, il baggage non viene registrato automaticamente negli span — viene solo propagato. E utile per passare informazioni di contesto come `tenant_id`, `request_priority`, `feature_flags`.

```python
from opentelemetry import baggage, context

# Impostare baggage
ctx = baggage.set_baggage("tenant.id", "acme-corp")
ctx = baggage.set_baggage("request.priority", "high", context=ctx)

# Il baggage viene propagato automaticamente nelle chiamate HTTP in uscita
# I servizi downstream possono leggerlo:
tenant_id = baggage.get_baggage("tenant.id")
```

**Attenzione alla sicurezza**: il baggage attraversa i confini di trust. Non inserire mai dati sensibili nel baggage. Ogni servizio nella catena puo leggere e modificare il baggage.

### Cross-Service Tracing — esempio completo

Consideriamo tre servizi: `gateway-api`, `ordini-service`, `pagamenti-service`.

```python
# --- gateway-api ---
@app.post("/api/v1/ordini")
async def crea_ordine(ordine: OrdineRequest):
    with tracer.start_as_current_span(
        "crea_ordine",
        kind=trace.SpanKind.SERVER,
    ) as span:
        span.set_attribute("ordine.importo", ordine.importo)

        # La chiamata HTTP al servizio ordini propaga automaticamente
        # il traceparent header grazie all'auto-instrumentation di httpx
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://ordini-service:8001/ordini",
                json=ordine.dict(),
            )
        return resp.json()


# --- ordini-service ---
@app.post("/ordini")
async def processa_ordine(ordine: OrdineRequest):
    # Lo span SERVER viene creato automaticamente dall'auto-instrumentation
    # con il trace_id ricevuto dal gateway
    with tracer.start_as_current_span("valida_e_salva") as span:
        salva_su_db(ordine)

        # Chiamata al servizio pagamenti — il trace context continua
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://pagamenti-service:8002/pagamenti",
                json={"ordine_id": ordine.id, "importo": ordine.importo},
            )
        return {"status": "creato", "pagamento": resp.json()}


# --- pagamenti-service ---
@app.post("/pagamenti")
async def processa_pagamento(pagamento: PagamentoRequest):
    with tracer.start_as_current_span("addebita_carta") as span:
        risultato = gateway_pagamento.charge(pagamento)
        span.set_attribute("pagamento.esito", risultato.status)
        return {"status": risultato.status}
```

La trace risultante in Jaeger/Tempo mostrera un albero come:

```
gateway-api: POST /api/v1/ordini (350ms)
  ├── ordini-service: POST /ordini (300ms)
  │   ├── valida_e_salva (50ms)
  │   │   └── postgresql: INSERT INTO ordini (15ms)
  │   └── pagamenti-service: POST /pagamenti (200ms)
  │       └── addebita_carta (180ms)
  │           └── https: POST api.stripe.com/v1/charges (170ms)
```

---

## Custom Metrics Design

Progettare metriche custom efficaci richiede disciplina. Metriche sbagliate generano dashboard inutili e alert falsi. Metriche ben progettate rendono il sistema comprensibile a colpo d'occhio.

### Naming conventions

Prometheus ha convenzioni precise per i nomi delle metriche:

1. **Prefisso con il nome del componente**: `ordini_`, `pagamenti_`, `gateway_`
2. **Unita nel suffisso**: `_seconds`, `_bytes`, `_total`, `_ratio`
3. **Counter con suffisso `_total`**: `http_requests_total`
4. **Histogram/Summary senza `_total`**: `http_request_duration_seconds`
5. **Snake_case**: `ordini_processati_total`, non `ordiniProcessatiTotal`

```python
# Corretto
ordini_processati_total = Counter(
    "ordini_processati_total",
    "Ordini processati con successo",
    labelnames=["tipo", "canale"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "Durata delle richieste HTTP",
    labelnames=["method", "endpoint", "status"],
)

db_connections_active = Gauge(
    "db_connections_active",
    "Connessioni al database attive",
    labelnames=["pool_name"],
)

# Errato
Requests = Counter("Requests", "requests")  # no PascalCase, no unita, no label
```

### Gestione della cardinalita

La cardinalita e il numero di combinazioni uniche di valori di label. E il fattore piu critico per le performance di Prometheus.

| Label | Valori possibili | Cardinalita |
|-------|-----------------|-------------|
| `method` | GET, POST, PUT, DELETE | 4 |
| `status_code` | 200, 201, 400, 404, 500 | ~10 |
| `endpoint` | /api/ordini, /api/utenti, ... | ~50 |
| **Totale** | | 4 * 10 * 50 = **2.000** |

2.000 time series sono gestibili. Ma se aggiungiamo `user_id` con 100.000 utenti: 4 * 10 * 50 * 100.000 = **200.000.000** time series — completamente insostenibile.

Regole per la cardinalita:
- **Max ~10 valori distinti per label** come obiettivo
- Mai usare ID univoci (user_id, request_id, order_id) come label
- Raggruppare in bucket: `user_tier` invece di `user_id`, `latency_bucket` invece del valore esatto
- Monitorare con `prometheus_tsdb_head_series` la crescita delle time series

### Metriche SLI/SLO

Le metriche SLI (Service Level Indicator) sono la base quantitativa per gli SLO (Service Level Objective).

**SLI Disponibilita**: percentuale di richieste riuscite.

```python
RICHIESTE = Counter(
    "http_requests_total",
    "Richieste HTTP totali",
    labelnames=["method", "status_class"],  # "2xx", "4xx", "5xx"
)

# PromQL per SLI disponibilita (finestra 30 giorni):
# sum(rate(http_requests_total{status_class!="5xx"}[30d]))
# /
# sum(rate(http_requests_total[30d]))
```

**SLI Latenza**: percentuale di richieste entro la soglia target.

```python
LATENZA = Histogram(
    "http_request_duration_seconds",
    "Durata richieste HTTP",
    labelnames=["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# PromQL per SLI latenza (% richieste sotto 250ms):
# sum(rate(http_request_duration_seconds_bucket{le="0.25"}[5m]))
# /
# sum(rate(http_request_duration_seconds_count[5m]))
```

**SLI Throughput**: richieste al secondo.

```python
# PromQL:
# sum(rate(http_requests_total[5m]))
```

**Error budget**: la quantita di errore tollerabile prima di violare lo SLO.

```python
# Se lo SLO e 99.9% disponibilita su 30 giorni:
# Error budget = 30 giorni * 24 ore * 60 min * (1 - 0.999) = 43.2 minuti di downtime
# Error budget consumato:
# 1 - (
#   sum(rate(http_requests_total{status_class!="5xx"}[30d]))
#   /
#   sum(rate(http_requests_total[30d]))
# ) / (1 - 0.999)
```

### RED Method

Il pattern RED e uno schema consolidato per le metriche di servizi:

- **R**ate — Richieste al secondo
- **E**rrors — Richieste fallite al secondo
- **D**uration — Distribuzione della latenza

```python
# Rate
richieste_totali = Counter(
    "ordini_service_requests_total",
    "Richieste totali al servizio ordini",
    labelnames=["method", "endpoint"],
)

# Errors
errori_totali = Counter(
    "ordini_service_errors_total",
    "Errori totali nel servizio ordini",
    labelnames=["method", "endpoint", "error_type"],
)

# Duration
durata = Histogram(
    "ordini_service_request_duration_seconds",
    "Durata delle richieste al servizio ordini",
    labelnames=["method", "endpoint"],
)
```

### USE Method

Il pattern USE e per le risorse infrastrutturali:

- **U**tilization — Percentuale di utilizzo
- **S**aturation — Lavoro in coda
- **E**rrors — Errori della risorsa

```python
# Utilization
pool_utilizzo = Gauge(
    "db_pool_utilization_ratio",
    "Percentuale di connessioni DB in uso",
    labelnames=["pool_name"],
)

# Saturation
pool_attesa = Gauge(
    "db_pool_pending_requests",
    "Richieste in attesa di una connessione DB",
    labelnames=["pool_name"],
)

# Errors
pool_errori = Counter(
    "db_pool_errors_total",
    "Errori nel pool di connessioni DB",
    labelnames=["pool_name", "error_type"],
)
```

---

## Structured Logging

I log non strutturati (testo libero) sono facili da scrivere ma impossibili da interrogare programmaticamente. I log strutturati (JSON) con campi tipizzati sono la base per log aggregation, alerting e correlazione con traces.

### structlog

`structlog` e la libreria Python piu matura per il logging strutturato. Produce log JSON con contesto automatico e si integra nativamente con `logging` stdlib.

```bash
pip install structlog
```

Configurazione production-ready:

```python
import structlog
import logging

structlog.configure(
    processors=[
        # Aggiunge timestamp ISO 8601
        structlog.processors.TimeStamper(fmt="iso"),
        # Aggiunge il livello di log
        structlog.processors.add_log_level,
        # Aggiunge caller info (modulo, funzione, linea)
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ],
        ),
        # Formatta le eccezioni
        structlog.processors.format_exc_info,
        # Aggiunge stack info se presente
        structlog.processors.StackInfoRenderer(),
        # Output JSON
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()

log.info(
    "ordine_creato",
    ordine_id="ord-12345",
    importo=99.99,
    canale="web",
    utente_tier="premium",
)
# Output:
# {"event": "ordine_creato", "ordine_id": "ord-12345", "importo": 99.99,
#  "canale": "web", "utente_tier": "premium", "timestamp": "2026-05-22T10:30:00Z",
#  "level": "info", "module": "ordini", "func_name": "crea_ordine", "lineno": 42}
```

### structlog con OTel

Per iniettare automaticamente `trace_id` e `span_id` nei log structlog:

```python
from opentelemetry import trace

def add_otel_context(logger, method_name, event_dict):
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
        event_dict["trace_flags"] = ctx.trace_flags
    return event_dict

structlog.configure(
    processors=[
        add_otel_context,  # prima degli altri processor
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    # ...
)
```

### python-json-logger

Alternativa piu leggera a structlog, basata su un formatter per `logging` stdlib:

```python
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    rename_fields={"asctime": "timestamp", "levelname": "level"},
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info("Ordine creato", extra={"ordine_id": "ord-12345", "importo": 99.99})
```

### Integrazione con ELK Stack

L'ELK stack (Elasticsearch, Logstash, Kibana) e uno dei sistemi di log aggregation piu diffusi. I log JSON possono essere inviati direttamente a Elasticsearch o tramite Logstash.

```python
# Filebeat legge i log JSON da stdout/file e li invia a Elasticsearch
# docker-compose.yml
# filebeat:
#   volumes:
#     - /var/log/app:/var/log/app:ro
#   command: >
#     filebeat -e
#     -E output.elasticsearch.hosts=["elasticsearch:9200"]
#     -E filebeat.inputs=[{type: container, paths: ["/var/log/app/*.json"]}]
```

Configurazione Logstash per log Python JSON:

```ruby
# logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  json {
    source => "message"
  }
  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "python-app-%{+YYYY.MM.dd}"
  }
}
```

### Integrazione con Grafana Loki

Loki e l'alternativa "like Prometheus, but for logs" di Grafana Labs. Non indicizza il contenuto dei log — solo le label. Questo lo rende ordini di grandezza piu economico di Elasticsearch per volumi elevati.

```python
# python-logging-loki
import logging
import logging_loki

handler = logging_loki.LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"application": "ordini-api", "environment": "production"},
    version="1",
)

logger = logging.getLogger("ordini")
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info(
    "Ordine processato",
    extra={"tags": {"ordine_tipo": "standard"}},
)
```

In LogQL (il linguaggio di query di Loki):

```logql
{application="ordini-api"} |= "ordine_creato" | json | importo > 100
```

---

## APM Integration

I servizi APM (Application Performance Monitoring) aggiungono un livello di analisi sopra la telemetria grezza: transaction tracking, error grouping, dependency maps, anomaly detection. OTel semplifica l'integrazione perche separa la generazione dall'invio dei dati.

### Datadog

Datadog supporta l'ingest diretto di telemetria OTel via OTLP. Non e necessaria la libreria `ddtrace` se si usa OTel.

```yaml
# otel-collector-config.yaml
exporters:
  datadog:
    api:
      key: "${DD_API_KEY}"
      site: "datadoghq.eu"  # o datadoghq.com

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [datadog]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [datadog]
```

Alternativa con `ddtrace` nativo (senza OTel):

```bash
pip install ddtrace
DD_SERVICE=ordini-api DD_ENV=production DD_VERSION=2.4.1 \
    ddtrace-run python -m uvicorn app:app
```

### New Relic

New Relic accetta OTLP nativamente:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://otlp.eu01.nr-data.net"
export OTEL_EXPORTER_OTLP_HEADERS="api-key=${NEW_RELIC_LICENSE_KEY}"
```

### Elastic APM

Elastic APM supporta sia l'agent nativo `elastic-apm` sia l'ingest OTLP.

```bash
pip install elastic-apm

# settings.py (Django)
ELASTIC_APM = {
    "SERVICE_NAME": "ordini-api",
    "SECRET_TOKEN": "${ELASTIC_APM_SECRET_TOKEN}",
    "SERVER_URL": "http://apm-server:8200",
    "ENVIRONMENT": "production",
    "CAPTURE_BODY": "errors",  # mai 'all' in prod — dati sensibili
}

INSTALLED_APPS = [
    "elasticapm.contrib.django",
    # ...
]
```

Con OTLP tramite OTel Collector:

```yaml
exporters:
  otlp/elastic:
    endpoint: "apm-server:8200"
    tls:
      insecure: false
      ca_file: "/etc/ssl/certs/apm-ca.pem"
    headers:
      Authorization: "Bearer ${ELASTIC_APM_SECRET_TOKEN}"
```

### Confronto APM

| Caratteristica | Datadog | New Relic | Elastic APM | Sentry |
|---------------|---------|-----------|-------------|--------|
| OTLP nativo | Si | Si | Si | No (SDK) |
| Traces | Si | Si | Si | Si |
| Metrics | Si | Si | Si | Limitato |
| Logs | Si | Si | Si | No |
| Profiling | Si | No | Si | Si |
| Error tracking | Si | Si | Si | Eccellente |
| Pricing | Per host + ingest | Per ingest | Self-hosted / Cloud | Per evento |
| Open source | No | No | Si (stack) | Si (SDK) |

---

## Error Tracking e Sentry

Sentry e lo standard de facto per l'error tracking in Python. Cattura eccezioni con stacktrace completo, contesto di runtime, breadcrumb (cronologia di eventi precedenti l'errore) e informazioni sull'utente. Si integra con OTel per correlare errori a traces.

### Setup

```bash
pip install sentry-sdk
```

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn="${SENTRY_DSN}",
    environment="production",
    release="ordini-api@2.4.1",
    traces_sample_rate=0.1,  # 10% delle transazioni
    profiles_sample_rate=0.1,  # 10% delle transazioni profilate

    # Integrazione OTel
    instrumenter="otel",

    # Sicurezza: non inviare dati sensibili
    send_default_pii=False,
    before_send=filtra_dati_sensibili,

    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
        RedisIntegration(),
        CeleryIntegration(),
    ],
)

def filtra_dati_sensibili(event, hint):
    """Rimuove dati sensibili prima dell'invio a Sentry."""
    if "request" in event:
        headers = event["request"].get("headers", {})
        for chiave_sensibile in ["authorization", "cookie", "x-api-key"]:
            headers.pop(chiave_sensibile, None)
    return event
```

### Contesto personalizzato

```python
from sentry_sdk import set_user, set_tag, set_context

# Informazioni utente (senza PII se send_default_pii=False)
set_user({"id": "usr-12345", "segment": "premium"})

# Tag: indicizzati, cercabili, bassa cardinalita
set_tag("tenant", "acme-corp")
set_tag("feature_flag", "nuovo_checkout")

# Contesto: dati strutturati non indicizzati
set_context("ordine", {
    "id": "ord-67890",
    "importo": 299.99,
    "items_count": 3,
})
```

### Breadcrumbs

I breadcrumb sono una cronologia di eventi che precedono l'errore. Sentry li cattura automaticamente per HTTP, SQL, log e console.

```python
import sentry_sdk

sentry_sdk.add_breadcrumb(
    category="ordine",
    message="Validazione ordine completata",
    level="info",
    data={"ordine_id": "ord-12345", "items": 3},
)

sentry_sdk.add_breadcrumb(
    category="pagamento",
    message="Tentativo di addebito",
    level="info",
    data={"gateway": "stripe", "importo": 299.99},
)

# Quando l'eccezione viene catturata, Sentry include tutti i breadcrumb
# nel contesto dell'errore, permettendo di ricostruire la sequenza di eventi
```

### Release tracking

```bash
# CI/CD pipeline
sentry-cli releases new "ordini-api@2.4.1"
sentry-cli releases set-commits "ordini-api@2.4.1" --auto
sentry-cli releases deploys "ordini-api@2.4.1" new -e production
sentry-cli releases finalize "ordini-api@2.4.1"
```

In Sentry, ogni errore viene associato alla release che lo ha introdotto, permettendo di identificare quali commit hanno causato la regressione.

---

## Profiling in Produzione

Il profiling in produzione rivela i colli di bottiglia che non emergono in sviluppo: query lente sotto carico, GC pressure, contention su lock, I/O blocking inatteso.

### py-spy

`py-spy` e un sampling profiler per Python che non richiede modifiche al codice e ha overhead trascurabile (~2%). Funziona attaccandosi a un processo Python in esecuzione.

```bash
pip install py-spy

# Profila un processo in esecuzione
py-spy record -o profile.svg --pid 12345

# Profila all'avvio
py-spy record -o profile.svg -- python -m uvicorn app:app

# Top-like in tempo reale
py-spy top --pid 12345

# Genera flame graph con durata specifica
py-spy record -o profile.svg --pid 12345 --duration 60 --rate 100
```

Il flame graph risultante mostra visivamente dove il programma spende il tempo. Le funzioni piu larghe sono quelle che occupano piu CPU. I flame graph sono leggibili dal basso verso l'alto: la base mostra la funzione di entry point, e ogni livello superiore mostra le funzioni chiamate.

### Pyroscope — Continuous Profiling

Pyroscope (ora parte di Grafana) fornisce profiling continuo: raccoglie profili a intervalli regolari e li archivia per analisi storica. Permette di rispondere a domande come "cosa faceva il servizio alle 3 di notte quando la latenza e salita?".

```bash
pip install pyroscope-io
```

```python
import pyroscope

pyroscope.configure(
    application_name="ordini-api",
    server_address="http://pyroscope:4040",
    tags={
        "environment": "production",
        "version": "2.4.1",
        "region": "eu-west-1",
    },
    sample_rate=100,  # campioni al secondo
)

# Il profiling e attivo automaticamente.
# Per profilare sezioni specifiche:
with pyroscope.tag_wrapper({"endpoint": "/api/ordini", "method": "POST"}):
    processa_ordine(ordine)
```

### Sentry Profiling

Sentry offre profiling integrato con le transazioni (traces):

```python
sentry_sdk.init(
    dsn="${SENTRY_DSN}",
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,  # profila il 10% delle transazioni tracciate
)

# Ogni transazione campionata includera un profilo
# visibile direttamente nell'interfaccia Sentry
```

### memory_profiler e memray

Per problemi di memoria (leak, allocazioni eccessive):

```bash
pip install memray

# Profila l'uso di memoria
memray run -o output.bin python app.py

# Genera report
memray flamegraph output.bin -o flamegraph.html
memray table output.bin
memray tree output.bin
```

---

## Health Check e Readiness Probe

In ambienti containerizzati (Kubernetes, ECS), le probe di salute determinano se un'istanza puo ricevere traffico. Una probe mal configurata puo causare cascate di riavvii o traffico verso istanze non pronte.

### Tre tipi di probe

| Probe | Scopo | Fallimento |
|-------|-------|------------|
| **Liveness** | Il processo e vivo? | Kubernetes riavvia il container |
| **Readiness** | Il servizio puo gestire traffico? | Rimosso dal service discovery |
| **Startup** | L'applicazione ha completato l'inizializzazione? | Kubernetes attende prima di attivare liveness/readiness |

### Implementazione FastAPI

```python
from fastapi import FastAPI, Response, status
import asyncio
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

# Stato globale delle dipendenze
_db_engine = None
_redis_client = None


@app.get("/health/live")
async def liveness():
    """Verifica che il processo sia vivo.
    Non verifica le dipendenze — solo che il processo risponda.
    """
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness(response: Response):
    """Verifica che il servizio possa gestire traffico.
    Controlla tutte le dipendenze critiche.
    """
    checks = {}

    # Database
    try:
        async with AsyncSession(_db_engine) as session:
            await asyncio.wait_for(
                session.execute("SELECT 1"),
                timeout=2.0,
            )
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis
    try:
        await asyncio.wait_for(
            _redis_client.ping(),
            timeout=1.0,
        )
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    # Valutazione complessiva
    all_ok = all(v == "ok" for v in checks.values())
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if all_ok else "not_ready",
        "checks": checks,
    }


@app.get("/health/startup")
async def startup_check():
    """Verifica che l'inizializzazione sia completa.
    Controlla migrazioni DB, cache warming, ecc.
    """
    return {"status": "started"}
```

### Configurazione Kubernetes

```yaml
# deployment.yaml
spec:
  containers:
    - name: ordini-api
      livenessProbe:
        httpGet:
          path: /health/live
          port: 8000
        initialDelaySeconds: 10
        periodSeconds: 15
        timeoutSeconds: 3
        failureThreshold: 3

      readinessProbe:
        httpGet:
          path: /health/ready
          port: 8000
        initialDelaySeconds: 5
        periodSeconds: 10
        timeoutSeconds: 5
        failureThreshold: 3

      startupProbe:
        httpGet:
          path: /health/startup
          port: 8000
        initialDelaySeconds: 0
        periodSeconds: 5
        timeoutSeconds: 3
        failureThreshold: 30  # max 150 secondi per startup
```

### Antipattern da evitare

**Non verificare dipendenze esterne nella liveness probe.** Se il database e giu, il servizio non va riavviato — va rimosso dal pool di traffico (readiness). Se la liveness verifica il database e il database e giu, Kubernetes riavvia tutti i pod contemporaneamente, causando una tempesta di riavvii.

**Non usare timeout troppo aggressivi.** Un timeout di 1 secondo su un health check che verifica il database puo causare flapping durante i picchi di carico — il database risponde in 1.1 secondi e Kubernetes rimuove il pod.

**Non esporre informazioni sensibili.** L'endpoint `/health/ready` non deve rivelare stringhe di connessione, versioni di database o dettagli interni che possano aiutare un attaccante.

---

## Docker e Kubernetes Observability

L'osservabilita in ambienti containerizzati richiede configurazioni specifiche per la raccolta dei segnali di telemetria, la Service Discovery e la gestione delle risorse.

### Dockerfile con OTel

```dockerfile
FROM python:3.12-slim AS base

WORKDIR /app

# Dipendenze
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Auto-instrumentation OTel
RUN opentelemetry-bootstrap -a install

COPY . .

# Health check Docker nativo
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')"

EXPOSE 8000 9090

# Avvio con auto-instrumentation
CMD ["opentelemetry-instrument", \
     "python", "-m", "uvicorn", "app:app", \
     "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose con stack osservabilita completo

```yaml
# docker-compose.observability.yaml
version: "3.9"

services:
  app:
    build: .
    ports:
      - "8000:8000"
      - "9090:9090"  # Prometheus metrics
    environment:
      - OTEL_SERVICE_NAME=ordini-api
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - OTEL_EXPORTER_OTLP_PROTOCOL=grpc
      - OTEL_PYTHON_LOG_CORRELATION=true
      - OTEL_TRACES_SAMPLER=parentbased_traceidratio
      - OTEL_TRACES_SAMPLER_ARG=0.1
    depends_on:
      - otel-collector
      - postgres

  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.100.0
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8888:8888"   # Metriche del collector
    volumes:
      - ./otel-collector-config.yaml:/etc/otelcol-contrib/config.yaml

  prometheus:
    image: prom/prometheus:v2.53.0
    ports:
      - "9091:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana:11.1.0
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning

  tempo:
    image: grafana/tempo:2.5.0
    ports:
      - "3200:3200"   # API
      - "4317"        # OTLP gRPC (interno)
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
      - tempo-data:/var/tempo
    command: ["-config.file=/etc/tempo.yaml"]

  loki:
    image: grafana/loki:3.1.0
    ports:
      - "3100:3100"
    volumes:
      - loki-data:/loki

  jaeger:
    image: jaegertracing/all-in-one:1.58
    ports:
      - "16686:16686"  # UI
      - "14268:14268"  # Collector HTTP

volumes:
  prometheus-data:
  grafana-data:
  tempo-data:
  loki-data:
```

### OTel Collector configuration

```yaml
# otel-collector-config.yaml
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
    send_batch_size: 1024

  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128

  resource:
    attributes:
      - key: deployment.environment
        value: production
        action: upsert

exporters:
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true

  prometheusremotewrite:
    endpoint: http://prometheus:9090/api/v1/write

  loki:
    endpoint: http://loki:3100/loki/api/v1/push

  debug:
    verbosity: detailed

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/tempo]
    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [loki]
```

### OTel Collector — Configurazione Avanzata

Il Collector supporta componenti avanzati oltre ai classici receivers/processors/exporters. I **connectors** sono componenti che agiscono sia come exporter di una pipeline sia come receiver di un'altra, consentendo di derivare segnali da segnali.

#### Connettore `spanmetrics`

Genera metriche RED (Rate, Errors, Duration) automaticamente dalle traces ricevute:

```yaml
connectors:
  spanmetrics:
    histogram:
      explicit:
        buckets: [5ms, 10ms, 25ms, 50ms, 100ms, 250ms, 500ms, 1s, 2.5s, 5s, 10s]
    dimensions:
      - name: http.method
      - name: http.status_code
      - name: service.version
    exemplars:
      enabled: true
    metrics_flush_interval: 15s

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/tempo, spanmetrics]
    metrics/spanmetrics:
      receivers: [spanmetrics]
      processors: [batch]
      exporters: [prometheusremotewrite]
```

Le metriche generate includono `traces_spanmetrics_calls_total`, `traces_spanmetrics_latency_bucket` e `traces_spanmetrics_latency_sum` — pronte per query PromQL e dashboard Grafana senza instrumentazione manuale aggiuntiva.

#### Connettore `count`

Conta span/datapoint/log per dimensione, utile per monitorare volumi di telemetria:

```yaml
connectors:
  count:
    spans:
      span.count.by.service:
        description: "Numero di span per servizio"
        conditions:
          - status.code == STATUS_CODE_ERROR
        attributes:
          - key: service.name
    logs:
      log.count.by.severity:
        description: "Conteggio log per severita"
        attributes:
          - key: severity
```

#### Processor `attributes`

Manipola attributi su qualsiasi segnale — inserimento, aggiornamento, cancellazione, hashing:

```yaml
processors:
  attributes/sanitize:
    actions:
      - key: user.email
        action: hash      # hash per privacy GDPR
      - key: db.statement
        action: delete     # rimuovi query SQL potenzialmente sensibili
      - key: deployment.ring
        value: "canary"
        action: upsert     # aggiungi/aggiorna
      - key: http.url
        pattern: "token=([^&]*)"
        replace: "token=REDACTED"
        action: update     # sanitizza token dalle URL
```

#### Processor `transform`

Usa OTTL (OpenTelemetry Transformation Language) per trasformazioni piu complesse:

```yaml
processors:
  transform/traces:
    trace_statements:
      - context: span
        statements:
          - set(attributes["team"], "platform") where attributes["service.name"] == "ordini-api"
          - truncate_all(attributes, 256)
          - limit(attributes, 64)
```

#### Processor `filter`

Filtra segnali in base a condizioni, utile per ridurre il volume:

```yaml
processors:
  filter/drop_health:
    traces:
      span:
        - 'attributes["http.target"] == "/health/live"'
        - 'attributes["http.target"] == "/health/ready"'
        - 'attributes["http.target"] == "/metrics"'
    logs:
      log_record:
        - 'severity_number < SEVERITY_NUMBER_WARN'  # drop DEBUG e INFO
```

#### Routing multi-tenant

Il `routing` processor instrada segnali verso exporter diversi in base ad attributi, utile in architetture multi-tenant:

```yaml
processors:
  routing/by_tenant:
    from_attribute: tenant.id
    table:
      - value: "tenant-a"
        exporters: [otlp/tenant_a]
      - value: "tenant-b"
        exporters: [otlp/tenant_b]
    default_exporters: [otlp/shared]
```

Combinando connectors, processors avanzati e routing, il Collector diventa un vero motore di elaborazione della telemetria — non un semplice proxy.

### Kubernetes — deployment con OTel sidecar

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ordini-api
  labels:
    app: ordini-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ordini-api
  template:
    metadata:
      labels:
        app: ordini-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: ordini-api
          image: registry.example.com/ordini-api:2.4.1
          ports:
            - containerPort: 8000
              name: http
            - containerPort: 9090
              name: metrics
          env:
            - name: OTEL_SERVICE_NAME
              value: "ordini-api"
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "http://otel-collector.observability.svc:4317"
            - name: OTEL_RESOURCE_ATTRIBUTES
              value: "k8s.namespace.name=$(K8S_NAMESPACE),k8s.pod.name=$(K8S_POD_NAME)"
            - name: K8S_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
            - name: K8S_POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /health/live
              port: http
            initialDelaySeconds: 10
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /health/ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
```

### Prometheus ServiceMonitor (Prometheus Operator)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ordini-api
  namespace: observability
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: ordini-api
  endpoints:
    - port: metrics
      interval: 15s
      path: /metrics
  namespaceSelector:
    matchNames:
      - production
```

---

## Grafana Dashboard e PromQL

Grafana e il frontend di visualizzazione per Prometheus. La costruzione di dashboard efficaci richiede padronanza di PromQL e comprensione delle metriche esposte dall'applicazione.

### PromQL fondamentale

**Rate** — la funzione piu importante. Calcola il tasso di incremento per secondo di un counter su una finestra temporale.

```promql
# Richieste al secondo negli ultimi 5 minuti
rate(http_requests_total[5m])

# Richieste al secondo per endpoint
sum by (endpoint) (rate(http_requests_total[5m]))

# Tasso di errore (5xx)
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))
```

**Histogram quantiles** — calcola percentili dalla distribuzione dell'histogram.

```promql
# P99 latenza
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))

# P99 per endpoint
histogram_quantile(0.99,
  sum by (le, endpoint) (rate(http_request_duration_seconds_bucket[5m]))
)

# P50 (mediana)
histogram_quantile(0.5, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))

# Latenza media
sum(rate(http_request_duration_seconds_sum[5m]))
/
sum(rate(http_request_duration_seconds_count[5m]))
```

**Aggregazioni**

```promql
# Somma per label
sum by (method) (rate(http_requests_total[5m]))

# Top 5 endpoint per richieste
topk(5, sum by (endpoint) (rate(http_requests_total[5m])))

# Valore minimo/massimo
min(db_connections_active)
max(db_connections_active)
```

**Operazioni su gauge**

```promql
# Connessioni DB attive per pool
db_connections_active{pool_name="default"}

# Percentuale utilizzo pool (attive / max)
db_connections_active / db_connections_max * 100

# Media connessioni nell'ultima ora
avg_over_time(db_connections_active[1h])
```

### Dashboard template per servizio Python

**Pannello 1 — Request Rate (RED: Rate)**

```promql
# Richieste al secondo, suddivise per status
sum by (status_code) (rate(http_requests_total{service="ordini-api"}[5m]))
```

**Pannello 2 — Error Rate (RED: Errors)**

```promql
# Percentuale errori 5xx
100 * sum(rate(http_requests_total{service="ordini-api", status_code=~"5.."}[5m]))
/
sum(rate(http_requests_total{service="ordini-api"}[5m]))
```

**Pannello 3 — Latency (RED: Duration)**

```promql
# P50, P90, P99 latenza
histogram_quantile(0.50, sum by (le) (rate(http_request_duration_seconds_bucket{service="ordini-api"}[5m])))
histogram_quantile(0.90, sum by (le) (rate(http_request_duration_seconds_bucket{service="ordini-api"}[5m])))
histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{service="ordini-api"}[5m])))
```

**Pannello 4 — Connessioni database**

```promql
db_connections_active{service="ordini-api"}
db_pool_pending_requests{service="ordini-api"}
```

**Pannello 5 — Throughput per endpoint**

```promql
topk(10, sum by (endpoint) (rate(http_requests_total{service="ordini-api"}[5m])))
```

**Pannello 6 — Process metrics**

```promql
# Memoria RSS del processo Python
process_resident_memory_bytes{service="ordini-api"}

# CPU usage
rate(process_cpu_seconds_total{service="ordini-api"}[5m])

# File descriptor aperti
process_open_fds{service="ordini-api"}
```

**Pannello 7 — SLO Burn Rate**

```promql
# Error budget burn rate (finestra 1h vs target 99.9%)
(
  1 - (
    sum(rate(http_requests_total{service="ordini-api", status_code!~"5.."}[1h]))
    /
    sum(rate(http_requests_total{service="ordini-api"}[1h]))
  )
) / (1 - 0.999)
```

### Grafana provisioning automatico

```yaml
# grafana/provisioning/datasources/datasources.yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    jsonData:
      tracesToLogs:
        datasourceUid: loki
        tags: ["service.name"]
      nodeGraph:
        enabled: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: "$${__value.raw}"
```

Questa configurazione abilita la navigazione tra i tre pilastri: da un log in Loki si naviga alla trace in Tempo, da una metrica in Prometheus si naviga all'exemplar in Tempo.

---

## Alerting

Le metriche senza alert sono solo decorazione. L'alerting trasforma l'osservabilita da passiva (guardo i dashboard) ad attiva (vengo notificato quando qualcosa non va).

### Alert rules in Prometheus

```yaml
# alerts.yaml
groups:
  - name: ordini-api
    rules:
      # Tasso di errore superiore al 5% per 5 minuti
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{service="ordini-api", status_code=~"5.."}[5m]))
          /
          sum(rate(http_requests_total{service="ordini-api"}[5m]))
          > 0.05
        for: 5m
        labels:
          severity: critical
          team: platform-backend
        annotations:
          summary: "Alto tasso di errore su ordini-api"
          description: "Il tasso di errore 5xx e al {{ $value | humanizePercentage }} (soglia 5%)"
          runbook_url: "https://wiki.internal/runbooks/ordini-api-high-error-rate"

      # P99 latenza superiore a 2 secondi
      - alert: HighLatencyP99
        expr: |
          histogram_quantile(0.99,
            sum by (le) (rate(http_request_duration_seconds_bucket{service="ordini-api"}[5m]))
          ) > 2.0
        for: 10m
        labels:
          severity: warning
          team: platform-backend
        annotations:
          summary: "Latenza P99 elevata su ordini-api"
          description: "P99 latenza a {{ $value | humanizeDuration }} (soglia 2s)"

      # Error budget burn rate troppo alto (multiwindow)
      - alert: ErrorBudgetBurning
        expr: |
          (
            (1 - (
              sum(rate(http_requests_total{service="ordini-api", status_code!~"5.."}[1h]))
              /
              sum(rate(http_requests_total{service="ordini-api"}[1h]))
            )) / (1 - 0.999)
          ) > 14.4
          and
          (
            (1 - (
              sum(rate(http_requests_total{service="ordini-api", status_code!~"5.."}[5m]))
              /
              sum(rate(http_requests_total{service="ordini-api"}[5m]))
            )) / (1 - 0.999)
          ) > 14.4
        for: 2m
        labels:
          severity: critical
          team: platform-backend
        annotations:
          summary: "Error budget in rapido consumo"
          description: "Il burn rate dell'error budget supera 14.4x la velocita normale"

      # Connessioni database vicine al limite
      - alert: DBConnectionPoolNearLimit
        expr: |
          db_connections_active / db_connections_max > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Pool connessioni DB quasi esaurito"
          description: "{{ $value | humanizePercentage }} del pool utilizzato"

      # Servizio non risponde al health check
      - alert: ServiceDown
        expr: up{job="ordini-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "ordini-api non raggiungibile"
          description: "Prometheus non riesce a scrapare l'endpoint metrics"

      # Memoria alta
      - alert: HighMemoryUsage
        expr: |
          process_resident_memory_bytes{service="ordini-api"}
          / on() group_left
          container_spec_memory_limit_bytes{container="ordini-api"}
          > 0.9
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Uso memoria elevato"
          description: "Il processo usa il {{ $value | humanizePercentage }} della memoria disponibile"
```

### Alertmanager — routing e notifiche

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  receiver: default
  group_by: ["alertname", "service"]
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    - receiver: pagerduty-critical
      match:
        severity: critical
      continue: true  # notifica anche il canale Slack

    - receiver: slack-warnings
      match:
        severity: warning

receivers:
  - name: default
    slack_configs:
      - api_url: "${SLACK_WEBHOOK_URL}"
        channel: "#alerts-platform"
        title: "{{ .GroupLabels.alertname }}"
        text: "{{ range .Alerts }}{{ .Annotations.description }}\n{{ end }}"

  - name: pagerduty-critical
    pagerduty_configs:
      - service_key: "${PAGERDUTY_SERVICE_KEY}"
        severity: critical

  - name: slack-warnings
    slack_configs:
      - api_url: "${SLACK_WEBHOOK_URL}"
        channel: "#alerts-platform-warn"
```

### Best practices per l'alerting

1. **Alert su sintomi, non cause.** "Il tasso di errore e alto" e un buon alert. "Il CPU e alto" non lo e — potrebbe essere normale durante un picco di traffico.

2. **Ogni alert deve avere un runbook.** L'`annotations.runbook_url` deve puntare a una pagina che spiega cosa verificare e come intervenire.

3. **Evitare alert fatigue.** Troppi alert non critici vengono ignorati. Usare le severity con disciplina: `critical` = qualcuno deve svegliarsi di notte, `warning` = da verificare nel prossimo orario lavorativo.

4. **Multiwindow alerting per SLO.** Il burn rate su finestra singola genera falsi positivi. Usare due finestre (1h + 5m) per ridurre il rumore.

---

## Guida Implementativa — Stack Completo

Questa sezione descrive la costruzione di un'infrastruttura di osservabilita completa per un servizio Python FastAPI, partendo da zero.

### Step 1: struttura del progetto

```
ordini-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── telemetry.py        # setup OTel centralizzato
│   ├── metrics.py           # metriche Prometheus custom
│   ├── health.py            # endpoint salute
│   ├── middleware.py         # middleware custom
│   ├── routers/
│   │   ├── ordini.py
│   │   └── utenti.py
│   └── services/
│       ├── ordini_service.py
│       └── pagamenti_client.py
├── docker-compose.yaml
├── Dockerfile
├── otel-collector-config.yaml
├── prometheus.yml
├── alerts.yaml
└── requirements.txt
```

### Step 2: telemetry.py — configurazione centralizzata

```python
"""Configurazione centralizzata della telemetria OTel."""
from opentelemetry import trace, metrics
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
import os


def create_resource() -> Resource:
    return Resource.create({
        ResourceAttributes.SERVICE_NAME: os.getenv("OTEL_SERVICE_NAME", "ordini-api"),
        ResourceAttributes.SERVICE_VERSION: os.getenv("APP_VERSION", "0.0.0"),
        ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.getenv("ENVIRONMENT", "development"),
    })


def setup_telemetry(app=None, db_engine=None):
    """Inizializza tutti e tre i pilastri OTel."""
    resource = create_resource()
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    sample_rate = float(os.getenv("OTEL_TRACES_SAMPLER_ARG", "1.0"))

    # --- Traces ---
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=ParentBased(root=TraceIdRatioBased(sample_rate)),
    )
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
    )
    trace.set_tracer_provider(tracer_provider)

    # --- Metrics ---
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=endpoint, insecure=True),
        export_interval_millis=15000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # --- Logs ---
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(OTLPLogExporter(endpoint=endpoint, insecure=True))
    )
    set_logger_provider(logger_provider)

    # --- Auto-instrumentation ---
    LoggingInstrumentor().instrument(set_logging_format=True)
    HTTPXClientInstrumentor().instrument()
    RedisInstrumentor().instrument()

    if db_engine:
        SQLAlchemyInstrumentor().instrument(engine=db_engine)

    if app:
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="/health/live,/health/ready,/metrics",
        )

    return tracer_provider, meter_provider, logger_provider
```

### Step 3: metrics.py — metriche Prometheus custom

```python
"""Metriche custom Prometheus per il servizio ordini."""
from prometheus_client import Counter, Histogram, Gauge, Info

# --- Business metrics ---
ORDINI_CREATI = Counter(
    "ordini_creati_total",
    "Ordini creati",
    labelnames=["canale", "tipo"],
)

ORDINI_IMPORTO = Histogram(
    "ordini_importo_euro",
    "Distribuzione importo ordini in euro",
    labelnames=["tipo"],
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000],
)

ORDINI_IN_ELABORAZIONE = Gauge(
    "ordini_in_elaborazione",
    "Ordini attualmente in fase di elaborazione",
)

# --- Infrastructure metrics ---
HTTP_RICHIESTE = Counter(
    "http_requests_total",
    "Richieste HTTP totali",
    labelnames=["method", "endpoint", "status_code"],
)

HTTP_LATENZA = Histogram(
    "http_request_duration_seconds",
    "Durata richieste HTTP",
    labelnames=["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

DB_QUERY_DURATA = Histogram(
    "db_query_duration_seconds",
    "Durata query database",
    labelnames=["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# --- Info metric ---
APP_INFO = Info(
    "ordini_api",
    "Informazioni sul servizio",
)
APP_INFO.info({
    "version": "2.4.1",
    "python_version": "3.12",
    "framework": "fastapi",
})
```

### Step 4: main.py — assemblaggio

```python
"""Entry point dell'applicazione."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import time
import structlog

from app.telemetry import setup_telemetry
from app.metrics import HTTP_RICHIESTE, HTTP_LATENZA
from app.health import router as health_router
from app.routers.ordini import router as ordini_router

log = structlog.get_logger()

_providers = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _providers
    _providers = setup_telemetry(app=app)
    log.info("telemetria_inizializzata")
    yield
    # Shutdown
    for p in _providers:
        p.shutdown()
    log.info("telemetria_chiusa")


app = FastAPI(title="Ordini API", lifespan=lifespan)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(ordini_router, prefix="/api/v1/ordini", tags=["ordini"])


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    durata = time.perf_counter() - start

    endpoint = request.url.path
    method = request.method
    status = str(response.status_code)

    HTTP_RICHIESTE.labels(method=method, endpoint=endpoint, status_code=status).inc()
    HTTP_LATENZA.labels(method=method, endpoint=endpoint).observe(durata)

    return response


@app.get("/metrics")
def prometheus_metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
```

### Step 5: prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alerts.yaml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ["alertmanager:9093"]

scrape_configs:
  - job_name: "ordini-api"
    static_configs:
      - targets: ["app:9090"]
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: "otel-collector"
    static_configs:
      - targets: ["otel-collector:8888"]
```

### Step 6: verifica dello stack

```bash
# Avvia tutto
docker compose -f docker-compose.yaml -f docker-compose.observability.yaml up -d

# Verifica che le metriche siano esposte
curl -s http://localhost:9090/metrics | head -20

# Verifica che Prometheus scrapi correttamente
curl -s http://localhost:9091/api/v1/targets | python -m json.tool

# Verifica che Grafana sia raggiungibile
curl -s http://localhost:3000/api/health

# Genera traffico di test
for i in $(seq 1 100); do
    curl -s http://localhost:8000/api/v1/ordini > /dev/null
done

# Verifica i traces in Jaeger
# Apri http://localhost:16686 nel browser
```

---

## Troubleshooting

### Problema 1: nessun trace visibile nel backend

**Sintomi**: l'applicazione gira, nessun errore nei log, ma Jaeger/Tempo non mostra traces.

**Cause possibili**:
- L'endpoint OTLP e errato o non raggiungibile.
- Il sampler e configurato a 0%.
- Il `BatchSpanProcessor` non ha fatto flush prima dello shutdown.
- Il firewall blocca la porta 4317 (gRPC) o 4318 (HTTP).

**Diagnosi**:
```python
# Aggiungi ConsoleSpanExporter per verificare che gli span vengano generati
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
```

```bash
# Verifica la raggiungibilita dell'endpoint
grpcurl -plaintext otel-collector:4317 list
# oppure
curl -v http://otel-collector:4318/v1/traces
```

### Problema 2: metriche Prometheus tutte a zero

**Sintomi**: le metriche appaiono nell'endpoint `/metrics` ma i valori sono sempre 0.

**Cause possibili**:
- Le metriche vengono dichiarate ma mai aggiornate (`.inc()` / `.observe()` mai chiamati).
- Le label usate nella query PromQL non corrispondono a quelle nelle metriche.
- Il middleware che registra le metriche non e montato correttamente.

**Diagnosi**:
```bash
# Verifica l'output grezzo dell'endpoint
curl -s http://localhost:9090/metrics | grep http_requests_total
# Se le metriche appaiono con valori > 0, il problema e in PromQL
```

### Problema 3: trace context non propagato tra servizi

**Sintomi**: ogni servizio mostra traces indipendenti; non esiste un'unica trace che attraversa i servizi.

**Cause possibili**:
- L'auto-instrumentation della libreria HTTP client non e installata.
- Il servizio downstream non estrae il trace context dagli header.
- Un reverse proxy (nginx, envoy) rimuove l'header `traceparent`.

**Diagnosi**:
```python
# Verifica che gli header vengano propagati
import httpx
from opentelemetry import propagate

headers = {}
propagate.inject(headers)
print(headers)
# Deve stampare: {'traceparent': '00-...', 'tracestate': ''}
```

### Problema 4: esplosione di cardinalita in Prometheus

**Sintomi**: Prometheus usa troppa memoria, le query sono lente, le metriche vengono droppate.

**Diagnosi**:
```promql
# Numero totale di time series
prometheus_tsdb_head_series

# Serie create per metrica (identifica la metrica problematica)
topk(10, count by (__name__) ({__name__=~".+"}))
```

**Soluzione**: rimuovere le label ad alta cardinalita (user_id, request_id) e usare Views OTel o relabeling Prometheus.

### Problema 5: log duplicati con OTel LoggingBridge

**Sintomi**: ogni messaggio di log appare due volte — una volta sullo stdout, una volta nel backend OTel.

**Causa**: il `LoggingInstrumentor` non rimuove gli handler esistenti; aggiunge un handler OTel che esporta via OTLP, ma l'handler originale (console) resta attivo.

**Soluzione**: non e un problema se lo stdout va a Loki tramite il container runtime. Se si vuole solo l'output OTLP, rimuovere l'handler console dal root logger.

### Problema 6: BatchSpanProcessor perde span durante shutdown

**Sintomi**: gli ultimi span di una richiesta non appaiono nel backend.

**Causa**: il processo termina prima che il `BatchSpanProcessor` abbia fatto flush del buffer.

**Soluzione**: chiamare `provider.force_flush()` nel lifecycle hook o in `atexit`.

```python
import atexit
atexit.register(lambda: provider.force_flush(timeout_millis=5000))
```

### Problema 7: metriche Prometheus con multiprocess worker

**Sintomi**: in produzione con gunicorn + 4 worker, le metriche cambiano ad ogni scrape (il load balancer interno di gunicorn ruota i worker).

**Soluzione**: usare `PROMETHEUS_MULTIPROC_DIR` e `MultiProcessCollector` come descritto nella sezione [Multiprocess mode](#multiprocess-mode).

### Problema 8: overhead di tracing in produzione

**Sintomi**: la latenza dell'applicazione aumenta dopo l'attivazione del tracing.

**Cause possibili**:
- `SimpleSpanProcessor` usato in produzione (sincrono).
- Troppi attributi per span.
- Sampling rate al 100% con alto traffico.

**Soluzione**: usare `BatchSpanProcessor`, ridurre il sampling rate, limitare gli attributi allo stretto necessario.

### Problema 9: `db.statement` contiene query con parametri sensibili

**Sintomi**: le traces nel backend contengono query SQL con valori di password o dati personali.

**Soluzione**: configurare l'instrumentazione SQLAlchemy per sanitizzare le query.

```python
SQLAlchemyInstrumentor().instrument(
    engine=engine,
    enable_commenter=True,
)
# I valori dei parametri vengono sostituiti con '?' di default
```

### Problema 10: Sentry e OTel generano traces duplicate

**Sintomi**: ogni richiesta produce due traces — una da Sentry e una da OTel.

**Causa**: sia Sentry sia OTel hanno il proprio TracerProvider attivo.

**Soluzione**: usare `instrumenter="otel"` nella configurazione Sentry, che delega il tracing a OTel.

```python
sentry_sdk.init(dsn="...", instrumenter="otel")
```

### Problema 11: Grafana non mostra gli exemplars

**Sintomi**: i grafici Prometheus non hanno i punti cliccabili degli exemplars.

**Cause possibili**:
- Prometheus non e configurato per accettare exemplars (`--enable-feature=exemplar-storage`).
- L'exporter non invia gli exemplars.
- Il pannello Grafana non ha l'opzione "Exemplars" abilitata.

**Soluzione**: abilitare exemplars in Prometheus e nel pannello Grafana.

### Problema 12: `opentelemetry-instrument` non instrumenta la libreria X

**Sintomi**: la libreria e nel `requirements.txt` ma non genera span.

**Causa**: il pacchetto di instrumentazione non e installato.

**Diagnosi**:
```bash
opentelemetry-bootstrap --action=requirements
# Elenca le instrumentazioni rilevate e installate
```

### Problema 13: metriche OTel e prometheus_client in conflitto

**Sintomi**: errori di registrazione duplicata quando si usano entrambe le librerie.

**Causa**: il `PrometheusMetricReader` di OTel e `prometheus_client` usano lo stesso registry globale.

**Soluzione**: usare registry separati o scegliere una sola libreria per le metriche.

```python
from prometheus_client import CollectorRegistry
custom_registry = CollectorRegistry()
# Passare custom_registry alle metriche prometheus_client
```

### Problema 14: PromQL `rate()` restituisce `NaN`

**Sintomi**: i grafici PromQL mostrano "No Data" o NaN.

**Cause possibili**:
- La finestra temporale e troppo piccola (deve essere almeno 2x lo scrape interval).
- La metrica non e un counter (rate funziona solo su counter/histogram).
- La metrica non ha campioni nella finestra selezionata.

**Soluzione**: usare `rate(...[5m])` con scrape interval di 15s. Verificare con `http_requests_total` (senza rate) che i dati esistano.

### Problema 15: OTel Collector out-of-memory

**Sintomi**: il container OTel Collector viene killato per OOM.

**Causa**: il `memory_limiter` processor non e configurato, oppure il batch size e troppo grande.

**Soluzione**: aggiungere il `memory_limiter` processor come primo nella pipeline.

```yaml
processors:
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128
```

### Problema 16: liveness probe causa restart loop

**Sintomi**: i pod Kubernetes si riavviano continuamente.

**Causa**: la liveness probe verifica dipendenze esterne (database, cache) che sono temporaneamente lente.

**Soluzione**: la liveness probe deve verificare SOLO che il processo risponda. Le dipendenze vanno nella readiness probe.

---

## FAQ

### 1. Qual e la differenza tra monitoring e osservabilita?

Il monitoring risponde a domande predefinite: "il CPU e sopra l'80%?", "il disco e pieno?". L'osservabilita consente di porre domande nuove senza dover aggiungere nuova instrumentazione: "perche il 3% delle richieste verso il servizio X impiega piu di 5 secondi solo il martedi mattina?". Il monitoring e un sottoinsieme dell'osservabilita.

### 2. Devo usare OTel o la libreria nativa del mio APM vendor?

Usare OTel quando possibile. Vantaggi: nessun vendor lock-in, un'unica instrumentazione per qualsiasi backend, standard CNCF con ampio supporto. Eccezione: se il vendor offre funzionalita specifiche non coperte da OTel (es. Sentry error grouping), usare la libreria nativa per quel segnale specifico e OTel per il resto.

### 3. Quanto costa il tracing in termini di performance?

Con `BatchSpanProcessor` e sampling al 10%, l'overhead e tipicamente sotto l'1% della latenza e trascurabile in termini di CPU. Il costo principale e la banda di rete e lo storage nel backend. Con sampling al 100% e alto traffico (>10k RPS), l'overhead puo arrivare al 3-5%.

### 4. Quante metriche dovrebbe esporre un servizio?

Non esiste un numero magico. Un servizio ben instrumentato espone tipicamente 20-50 metriche (senza contare le combinazioni di label). La regola e: ogni metrica deve poter rispondere a una domanda operativa specifica. Se non sai quale domanda risponde, probabilmente non serve.

### 5. Counter o Gauge per le richieste in-flight?

**Gauge.** Un counter e monotono crescente e misura il totale cumulativo. Le richieste in-flight salgono e scendono, quindi serve un gauge. Usare `RICHIESTE_IN_PROGRESS.inc()` all'ingresso e `.dec()` all'uscita, oppure il decorator `@gauge.track_inprogress()`.

### 6. Histogram o Summary per la latenza?

**Histogram** nella quasi totalita dei casi. Gli histogram sono aggregabili in PromQL con `histogram_quantile()`, i summary no. I summary calcolano i quantili lato client, il che significa che non puoi combinare i quantili di piu istanze — un'operazione fondamentale in ambienti con autoscaling.

### 7. Come gestisco il tracing con code Celery/RQ?

L'instrumentazione Celery di OTel propaga automaticamente il trace context attraverso gli header del messaggio. Il worker riceve il contesto e crea span figli nella stessa trace. Per RQ, la propagazione va implementata manualmente iniettando/estraendo il context negli argomenti del job.

### 8. Posso usare OTel Metrics e prometheus_client insieme?

Si, con cautela. Sono approcci complementari: OTel Metrics usa il modello push (OTLP verso il Collector), `prometheus_client` usa il modello pull (Prometheus scrapa l'endpoint). Possono coesistere senza conflitti se usano registry separati. Il `PrometheusMetricReader` di OTel puo anche esporre le metriche OTel nel formato Prometheus.

### 9. Come dimensiono il buffer del BatchSpanProcessor?

Il default (`max_queue_size=2048`, `max_export_batch_size=512`) e adeguato per la maggior parte dei servizi. Per servizi ad alto throughput (>5k RPS), aumentare `max_queue_size` a 8192 e `schedule_delay_millis` a 2000. Monitorare la metrica `otel.bsp.buffer.utilization` per verificare.

### 10. Come evito che i dati sensibili finiscano nelle traces?

Tre approcci complementari: (1) Non inserire mai PII/token negli attributi degli span nel codice applicativo. (2) Usare un processor OTel Collector che sanitizza gli attributi prima dell'export. (3) Configurare le instrumentazioni per non catturare i body HTTP (`OTEL_INSTRUMENTATION_HTTP_CAPTURE_HEADERS_SERVER_REQUEST=none`).

### 11. Serve un OTel Collector o posso esportare direttamente al backend?

In produzione, sempre il Collector. Vantaggi: batching e retry centralizzati, aggiunta/rimozione di backend senza toccare l'applicazione, processing (sampling, arricchimento, filtraggio) in un punto unico, riduzione del numero di connessioni aperte dall'applicazione. L'export diretto e accettabile solo in sviluppo o per POC.

### 12. Come configuro gli alert per evitare falsi positivi?

Usare `for: 5m` (o piu) per evitare alert su spike transitori. Usare multiwindow alerting per gli SLO (combinare una finestra lunga e una corta). Impostare `group_wait` e `group_interval` in Alertmanager per raggruppare notifiche correlate. Ogni alert deve avere un runbook e una severity corretta.

### 13. Come migro da un APM proprietario a OTel?

Approccio incrementale: (1) Aggiungere l'SDK OTel in parallelo all'agent proprietario. (2) Configurare l'OTel Collector per inviare i dati sia al vecchio sia al nuovo backend. (3) Validare la parita dei dati. (4) Rimuovere l'agent proprietario. (5) Riconfigurare il Collector per inviare solo al nuovo backend. Il dual-write tramite Collector rende la migrazione reversibile.

### 14. Come instrumento un servizio gRPC in Python?

```bash
pip install opentelemetry-instrumentation-grpc
```

```python
from opentelemetry.instrumentation.grpc import (
    GrpcInstrumentorClient,
    GrpcInstrumentorServer,
)
GrpcInstrumentorServer().instrument()  # server-side
GrpcInstrumentorClient().instrument()  # client-side
```

L'instrumentazione crea span SERVER/CLIENT e propaga il trace context nei metadata gRPC.

### 15. Qual e la differenza tra `force_flush()` e `shutdown()`?

`force_flush()` invia immediatamente tutti i dati nel buffer ma mantiene il provider attivo — utile per garantire che i dati vengano inviati prima di un'operazione critica. `shutdown()` chiama `force_flush()` internamente e poi disattiva il provider — nessun dato puo essere registrato dopo lo shutdown. Usare `shutdown()` alla terminazione del processo, `force_flush()` per flush intermedi.

### 16. Come correlo log, trace e metrica per lo stesso evento?

Il `trace_id` e il collante. (1) I log strutturati contengono `trace_id` e `span_id` (tramite `LoggingInstrumentor`). (2) Le metriche con exemplars contengono il `trace_id` del data point. (3) In Grafana, configurare i link tra datasource: Loki → Tempo (via `trace_id` nei log), Prometheus → Tempo (via exemplars). Questo crea un circolo completo di navigazione.

---

## Best Practices

### Architettura

1. **Separare generazione ed esportazione.** Instrumentare il codice con l'API OTel (stabile), non con un exporter specifico. L'exporter si configura a deploy time, non a code time.

2. **Un Collector per cluster, non per pod.** In Kubernetes, il pattern consigliato e un DaemonSet di Collector (uno per nodo) o un Deployment centralizzato. Evitare il sidecar per servizio, a meno che non servano configurazioni specifiche.

3. **Metriche RED per ogni servizio.** Rate, Errors, Duration sono il minimo necessario per ogni servizio. Partire da qui e aggiungere metriche business-specific.

4. **Log strutturati JSON con trace_id.** Mai log non strutturati in produzione. Il `trace_id` nei log e fondamentale per la correlazione.

### Performance

5. **Sempre `BatchSpanProcessor` in produzione.** `SimpleSpanProcessor` e sincrono e blocca il thread applicativo ad ogni span.

6. **Sampling proporzionato al traffico.** 100% per <100 RPS, 10-50% per 100-1000 RPS, 1-10% per >1000 RPS. Tail-based sampling nel Collector per mantenere il 100% degli errori.

7. **Cardinalita sotto controllo.** Max ~10 valori distinti per label. Monitorare `prometheus_tsdb_head_series` e impostare alert quando supera una soglia.

8. **Export interval ragionevole.** 15-30 secondi per le metriche, 5 secondi per i traces. Intervalli troppo brevi sovraccaricano il Collector e il backend.

### Sicurezza

9. **Mai PII nelle traces.** Username, email, indirizzo IP, carte di credito non devono mai apparire negli attributi degli span.

10. **Sanitizzare i `db.statement`.** Le query SQL nei traces non devono contenere valori di parametri sensibili.

11. **TLS tra applicazione e Collector in produzione.** Il traffico OTLP contiene dati operativi potenzialmente sensibili.

12. **RBAC per l'accesso ai dashboard.** Non tutti devono poter vedere tutte le metriche. I dati di osservabilita possono rivelare pattern di business.

### Operativita

13. **Ogni alert ha un runbook.** Un alert senza istruzioni operative e rumore.

14. **Dashboard per ruolo.** Un dashboard "overview" per il management, dashboard dettagliati per gli SRE, dashboard di debug per gli sviluppatori.

15. **Testare l'osservabilita.** Verificare che i traces vengano generati, che le metriche vengano esposte, che gli alert si attivino. L'osservabilita e infrastruttura critica — se non funziona quando serve, non serve.

16. **Retention differenziata.** Traces: 7-14 giorni (costosi). Metriche: 90 giorni full resolution, 1 anno downsampled. Log: 30 giorni hot, 1 anno cold storage.

---

## Correlazione Trace-Metric-Log e Grafana Stack

La correlazione tra i tre pilastri dell'osservabilita e cio che trasforma tre flussi di dati separati in un sistema di indagine unificato. Senza correlazione, un picco di latenza in un grafico Prometheus richiede una ricerca manuale nei log e una caccia alla trace corrispondente. Con correlazione attiva, un singolo click porta dal data point anomalo alla trace che lo ha generato e ai log emessi durante quella specifica esecuzione.

### Exemplars — collegamento end-to-end

Gli exemplars sono il ponte tra metriche e traces. Un exemplar e un riferimento a un `trace_id` e `span_id` attaccato a un data point specifico di un histogram o counter. Quando l'SDK OTel registra una misurazione (`.record()` o `.add()`) e un trace context e attivo, l'exemplar viene creato automaticamente.

Perche gli exemplars funzionino end-to-end, ogni componente dello stack deve essere configurato:

**Prometheus**: deve accettare e archiviare gli exemplars. Questa funzionalita richiede un feature flag esplicito:

```bash
# Avvio Prometheus con supporto exemplars
prometheus --config.file=prometheus.yml \
    --enable-feature=exemplar-storage \
    --storage.tsdb.retention.time=15d
```

Senza `--enable-feature=exemplar-storage`, Prometheus scarta silenziosamente gli exemplars ricevuti. Nessun errore nei log, nessun warning — i dati vengono semplicemente ignorati.

**OTel Collector**: il `prometheusremotewrite` exporter invia gli exemplars automaticamente quando sono presenti nei data point. Non e necessaria configurazione aggiuntiva. Se si usa il ricevitore Prometheus nel Collector, assicurarsi che il target esponga exemplars nel formato OpenMetrics:

```yaml
# otel-collector-config.yaml — ricevitore con supporto exemplars
receivers:
  prometheus:
    config:
      scrape_configs:
        - job_name: "ordini-api"
          scrape_interval: 15s
          static_configs:
            - targets: ["app:9090"]
          # Necessario per ricevere exemplars
          enable_open_metrics: true
```

**Grafana**: nel pannello Time Series, abilitare la visualizzazione degli exemplars:

1. Aprire il pannello e selezionare la tab "Query"
2. Attivare il toggle "Exemplars" sotto la query Prometheus
3. Configurare il data source di Tempo come destinazione dei link
4. Nella configurazione del data source Prometheus, sotto "Exemplars", mappare `traceID` al campo `trace_id`

Una volta configurato, i punti degli exemplars appaiono sovrapposti al grafico. Ogni punto e cliccabile e porta direttamente alla trace in Tempo o Jaeger, permettendo di passare da "la latenza e alta" a "ecco esattamente la richiesta lenta con tutto il suo albero di span" in un solo click.

### Grafana Tempo — TraceQL e Service Graph

Grafana Tempo e il backend di tracing progettato per integrarsi nativamente con Prometheus, Loki e Grafana. A differenza di Jaeger, Tempo non richiede un database esterno — archivia le traces direttamente su object storage (S3, GCS, Azure Blob) con costi significativamente inferiori.

**TraceQL** e il linguaggio di query di Tempo, analogo a PromQL per Prometheus e LogQL per Loki. Permette di cercare traces per attributi, durata e struttura:

```traceql
# Trova tutte le traces con span di errore nel servizio ordini
{ resource.service.name = "ordini-api" && status = error }

# Traces con latenza superiore a 2 secondi su un endpoint specifico
{ span.http.route = "/api/v1/ordini" && duration > 2s }

# Traces dove uno span contiene un attributo specifico
{ span.ordine.importo > 500 }

# Struttura: trova traces dove un SERVER span contiene un CLIENT span con errore
{ kind = server } >> { kind = client && status = error }

# Combinazione: servizio specifico, endpoint, con errore database
{ resource.service.name = "ordini-api" } >> { span.db.system = "postgresql" && status = error }
```

**Service Graph** e una funzionalita di Tempo che genera automaticamente una mappa delle dipendenze tra servizi basandosi sulle traces raccolte. Non richiede configurazione nel codice — il Collector genera le metriche del service graph dalle traces:

```yaml
# Nel Collector: abilitare il metrics-generator
processors:
  servicegraph:
    metrics_exporter: prometheusremotewrite
    latency_histogram_buckets: [100ms, 250ms, 500ms, 1s, 2s, 5s]
    dimensions:
      - http.method
      - http.route
    store:
      ttl: 2s
      max_items: 1000
```

Le metriche generate (`traces_service_graph_request_total`, `traces_service_graph_request_failed_total`, `traces_service_graph_request_server_seconds`) alimentano la visualizzazione Service Graph in Grafana, mostrando rate, errori e latenza per ogni arco tra servizi.

### Loki — Derived Fields e navigazione ai traces

Grafana Loki completa il triangolo dell'osservabilita. La correlazione log-trace avviene attraverso i "Derived Fields": regole che estraggono il `trace_id` dal contenuto dei log e creano link cliccabili verso Tempo.

Configurazione nel data source Loki in Grafana:

```yaml
# grafana/provisioning/datasources/loki.yaml
apiVersion: 1
datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      derivedFields:
        - datasourceUid: tempo-uid
          matcherRegex: "\"trace_id\":\\s*\"(\\w+)\""
          name: TraceID
          url: "$${__value.raw}"
          urlDisplayLabel: "Vedi Trace"
        - datasourceUid: tempo-uid
          matcherRegex: "trace_id=(\\w+)"
          name: TraceID_flat
          url: "$${__value.raw}"
          urlDisplayLabel: "Vedi Trace"
```

La regex nel `matcherRegex` deve corrispondere al formato in cui il `trace_id` appare nei log. Due pattern comuni sono il formato JSON (`"trace_id": "abc123"`) e il formato key=value (`trace_id=abc123`). Configurare entrambi garantisce compatibilita con diversi formati di log.

**Da Tempo verso Loki** (trace-to-logs): nella configurazione del data source Tempo in Grafana, la sezione `tracesToLogs` specifica come costruire la query Loki quando si naviga da una trace ai log:

```yaml
# grafana/provisioning/datasources/tempo.yaml
datasources:
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    jsonData:
      tracesToLogsV2:
        datasourceUid: loki-uid
        spanStartTimeShift: "-1m"
        spanEndTimeShift: "1m"
        filterByTraceID: true
        filterBySpanID: false
        tags:
          - key: "service.name"
            value: "service_name"
      tracesToMetrics:
        datasourceUid: prometheus-uid
        spanStartTimeShift: "-5m"
        spanEndTimeShift: "5m"
        tags:
          - key: "service.name"
            value: "service"
        queries:
          - name: "Request Rate"
            query: "sum(rate(http_requests_total{service=\"$${__tags.service}\"}[5m]))"
          - name: "Error Rate"
            query: "sum(rate(http_requests_total{service=\"$${__tags.service}\",status_code=~\"5..\"}[5m]))"
      nodeGraph:
        enabled: true
      serviceMap:
        datasourceUid: prometheus-uid
```

### Il circolo completo della correlazione

Con la configurazione completa, il flusso di indagine di un incidente diventa:

1. **Alert Prometheus** → Il burn rate supera la soglia: "errore budget in esaurimento".
2. **Dashboard Grafana** → Identifico quale endpoint ha il tasso di errore anomalo.
3. **Exemplar** → Clicco sul data point anomalo nel grafico histogram; Grafana apre la trace in Tempo.
4. **Trace Tempo** → L'albero di span rivela che il servizio `pagamenti-service` risponde con timeout.
5. **Trace-to-Logs** → Dal span del servizio `pagamenti-service`, clicco "Logs"; Grafana esegue una query Loki filtrata per `trace_id`.
6. **Log Loki** → I log rivelano `"connection refused: payment-gateway:443"` — il gateway di pagamento esterno e irraggiungibile.

L'intera indagine richiede 60 secondi e zero ricerca manuale. Senza correlazione, lo stesso incidente richiederebbe 15-30 minuti di grep distribuito tra log di servizi diversi.

### Grafana Unified Alerting

A partire da Grafana 11+, il sistema di alerting unificato sostituisce il vecchio alerting di Grafana e si integra nativamente con Alertmanager. Le alert rules possono essere definite direttamente in Grafana usando qualsiasi data source configurato — Prometheus, Loki, Tempo — senza necessita di file YAML separati.

Vantaggi dell'unified alerting rispetto alle sole alert rules Prometheus:

- **Multi-data-source alerts**: una singola regola puo combinare condizioni da Prometheus (metriche) e Loki (log patterns). Esempio: "alert se il tasso di errore supera il 5% E nei log compaiono errori di connessione al database".
- **Template di notifica centralizzati**: i template per le notifiche (Slack, PagerDuty, email) sono gestiti in Grafana, non in Alertmanager.
- **Gestione RBAC**: le alert rules ereditano il sistema di permessi di Grafana, con visibilita per team e folder.

```yaml
# Esempio di alert rule Grafana unified (provisioning)
apiVersion: 1
groups:
  - orgId: 1
    name: ordini-api-alerts
    folder: Platform
    interval: 1m
    rules:
      - uid: high-error-rate-ordini
        title: "Alto tasso di errore ordini-api"
        condition: C
        data:
          - refId: A
            datasourceUid: prometheus
            model:
              expr: |
                sum(rate(http_requests_total{service="ordini-api",status_code=~"5.."}[5m]))
                / sum(rate(http_requests_total{service="ordini-api"}[5m]))
          - refId: B
            datasourceUid: loki
            model:
              expr: |
                count_over_time({service_name="ordini-api"} |= "database connection refused" [5m])
          - refId: C
            datasourceUid: __expr__
            model:
              type: threshold
              conditions:
                - evaluator:
                    type: gt
                    params: [0.05]
                  operator:
                    type: and
        for: 5m
        labels:
          severity: critical
          team: platform-backend
        annotations:
          summary: "Alto tasso di errore con possibile failure database"
```

---

## Impatto sulle Performance dell'Instrumentazione

L'instrumentazione non e gratuita. Ogni span creato, ogni metrica registrata, ogni log arricchito richiede CPU, memoria e banda di rete. In produzione, l'overhead deve essere misurabile, prevedibile e accettabile per il caso d'uso specifico.

### Benchmark di overhead per componente

I dati seguenti derivano da misurazioni su un servizio FastAPI con traffico sintetico su hardware di riferimento (4 vCPU, 8GB RAM):

| Configurazione | Latenza overhead | CPU overhead | Memoria aggiuntiva |
|---------------|------------------|--------------|---------------------|
| Nessuna instrumentazione (baseline) | 0% | 0% | 0 MB |
| Auto-instrumentation + BatchSpanProcessor (10% sampling) | +0.5-1% | +2-3% | +15-25 MB |
| Auto-instrumentation + BatchSpanProcessor (100% sampling) | +2-4% | +5-8% | +30-50 MB |
| Auto-instrumentation + SimpleSpanProcessor (100%) | +15-30% | +10-15% | +20-35 MB |
| Metriche Prometheus (20 metriche custom) | +0.1-0.3% | <1% | +5-10 MB |
| Full stack (traces + metrics + logs, 10% sampling) | +1-3% | +5-10% | +40-70 MB |

I numeri variano significativamente in base al throughput, alla complessita degli span (numero di attributi, eventi), e alla velocita del backend di export. Il punto chiave: con `BatchSpanProcessor` e sampling ragionevole (10%), l'overhead e quasi sempre sotto il 3% di latenza.

### SimpleSpanProcessor vs BatchSpanProcessor — impatto reale

Il `SimpleSpanProcessor` esporta ogni span in modo sincrono nel thread della richiesta. Questo significa che ogni span aggiunge la latenza della chiamata di rete all'exporter alla latenza della richiesta dell'utente. Con un Collector su rete locale (latenza ~1ms), uno span aggiunge ~1ms. Con 10 span per richiesta, si aggiungono ~10ms. Su un servizio con P50 di 20ms, questo e un overhead del 50%.

Il `BatchSpanProcessor` accumula gli span in un buffer thread-safe e li esporta in batch su un thread in background. L'unico overhead nel thread della richiesta e l'inserimento nel buffer — operazione nell'ordine dei microsecondi. L'export avviene in modo completamente asincrono.

```python
# MAI in produzione
provider.add_span_processor(SimpleSpanProcessor(exporter))
# Overhead: latenza_rete * num_span per richiesta

# SEMPRE in produzione
provider.add_span_processor(BatchSpanProcessor(
    exporter,
    max_queue_size=4096,       # span bufferizzati prima del drop
    schedule_delay_millis=3000, # intervallo di export
    max_export_batch_size=512,  # span per batch
))
# Overhead: microsecondi per enqueue
```

### Strategie di ottimizzazione

**Sampling intelligente**: il modo piu efficace per ridurre l'overhead. Con tail-based sampling nel Collector, si mantiene il 100% delle traces con errori o alta latenza e si campiona il 5-10% delle traces normali. Questo riduce il volume di dati di 10-20x preservando la visibilita sugli eventi anomali.

**Limitare gli attributi**: ogni attributo aggiunto a uno span consuma memoria nel buffer e banda in fase di export. Limitare gli attributi allo stretto necessario. L'SDK supporta limiti configurabili:

```python
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider(
    resource=resource,
    sampler=sampler,
    span_limits=trace.SpanLimits(
        max_attributes=32,          # default 128
        max_events=16,              # default 128
        max_links=16,               # default 128
        max_attribute_length=256,   # tronca valori lunghi
    ),
)
```

**Instrumentazione selettiva**: non tutte le librerie necessitano di auto-instrumentation. Se il servizio non usa Redis, non installare `opentelemetry-instrumentation-redis`. Se le query SQL sono gia tracciate tramite l'ORM, un'instrumentazione aggiuntiva su psycopg2 genera span duplicati.

```bash
# Invece di installare tutto:
# opentelemetry-bootstrap -a install  # installa TUTTO

# Installare solo cio che serve:
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-instrumentation-sqlalchemy
pip install opentelemetry-instrumentation-httpx
```

**Views per ridurre la cardinalita delle metriche**: usare le Views OTel per eliminare attributi ad alta cardinalita prima dell'export, riducendo il volume di dati senza toccare il codice applicativo:

```python
from opentelemetry.sdk.metrics.view import View, DropAggregation

# Eliminare una metrica completamente
vista_drop = View(
    instrument_name="http.server.active_requests",
    aggregation=DropAggregation(),
)

# Ridurre gli attributi esportati
vista_ridotta = View(
    instrument_name="http.server.request.duration",
    attribute_keys=["http.method", "http.route"],
    # Esclude http.url (alta cardinalita per query string)
)
```

### Checklist di tuning per la produzione

- [ ] `BatchSpanProcessor` con `schedule_delay_millis` >= 2000
- [ ] Sampling rate adeguato al traffico (10% per >1000 RPS)
- [ ] `SpanLimits` configurati per prevenire span sovradimensionati
- [ ] Views per eliminare metriche e attributi non necessari
- [ ] `memory_limiter` processor nel Collector come primo nella catena
- [ ] Monitoraggio dell'overhead con metriche del processo (`process_cpu_seconds_total`, `process_resident_memory_bytes`)
- [ ] Load test con instrumentazione attiva per misurare l'impatto prima del deploy

---

## Testing del Codice di Osservabilita

L'instrumentazione e infrastruttura critica: se non funziona quando serve, l'osservabilita e inutile. Testare il codice di osservabilita garantisce che gli span vengano creati con i nomi e gli attributi corretti, che le metriche registrino i valori attesi e che la correlazione tra segnali funzioni.

### InMemorySpanExporter — test unitari sugli span

L'SDK OTel Python fornisce un exporter in-memory che cattura gli span in una lista, accessibile nei test per verifiche. Questo approccio non richiede un Collector o un backend — tutto avviene in processo.

```python
import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory import InMemorySpanExporter


@pytest.fixture
def otel_spans():
    """Fixture che configura OTel con exporter in-memory per i test."""
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    yield exporter
    exporter.clear()
    provider.shutdown()


def test_processa_ordine_crea_span_corretto(otel_spans):
    """Verifica che processa_ordine crei uno span con gli attributi attesi."""
    from app.services.ordini_service import processa_ordine

    processa_ordine(ordine_id="ord-123", importo=99.99)

    spans = otel_spans.get_finished_spans()
    assert len(spans) >= 1

    span_principale = next(
        s for s in spans if s.name == "processa_ordine"
    )
    assert span_principale.status.status_code == trace.StatusCode.OK
    assert span_principale.attributes["ordine.id"] == "ord-123"
    assert span_principale.attributes["ordine.importo"] == 99.99


def test_errore_pagamento_imposta_status_error(otel_spans):
    """Verifica che un errore nel pagamento imposti lo span in stato ERROR."""
    from app.services.ordini_service import processa_ordine

    with pytest.raises(PagamentoError):
        processa_ordine(ordine_id="ord-456", importo=-1)

    spans = otel_spans.get_finished_spans()
    span_pagamento = next(
        s for s in spans if s.name == "processa_pagamento"
    )
    assert span_pagamento.status.status_code == trace.StatusCode.ERROR

    # Verifica che l'eccezione sia stata registrata come evento
    eventi_eccezione = [
        e for e in span_pagamento.events if e.name == "exception"
    ]
    assert len(eventi_eccezione) == 1
    assert "PagamentoError" in eventi_eccezione[0].attributes["exception.type"]
```

### Verifica della gerarchia parent-child

In un sistema distribuito, la struttura degli span e fondamentale. Uno span orfano o con parent errato significa una trace spezzata.

```python
def test_span_gerarchia_corretta(otel_spans):
    """Verifica che gli span figli siano correttamente collegati al parent."""
    from app.services.ordini_service import processa_ordine_completo

    processa_ordine_completo(ordine_id="ord-789")

    spans = otel_spans.get_finished_spans()
    span_names = {s.name: s for s in spans}

    root = span_names["processa_ordine_completo"]
    valida = span_names["valida_ordine"]
    pagamento = span_names["processa_pagamento"]

    # Verifica che valida e pagamento siano figli di root
    assert valida.parent.span_id == root.context.span_id
    assert pagamento.parent.span_id == root.context.span_id

    # Verifica che tutti condividano lo stesso trace_id
    assert valida.context.trace_id == root.context.trace_id
    assert pagamento.context.trace_id == root.context.trace_id
```

### InMemoryMetricReader — test unitari sulle metriche

Per le metriche OTel, l'`InMemoryMetricReader` cattura i data point senza bisogno di un exporter esterno:

```python
import pytest
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader


@pytest.fixture
def otel_metrics():
    """Fixture che configura le metriche OTel con reader in-memory."""
    reader = InMemoryMetricReader()
    provider = MeterProvider(metric_readers=[reader])
    metrics.set_meter_provider(provider)
    yield reader
    provider.shutdown()


def test_counter_richieste_incrementato(otel_metrics):
    """Verifica che il counter venga incrementato correttamente."""
    from app.metrics_otel import registra_richiesta

    registra_richiesta(method="GET", endpoint="/api/ordini", status=200)
    registra_richiesta(method="GET", endpoint="/api/ordini", status=200)
    registra_richiesta(method="POST", endpoint="/api/ordini", status=201)

    data = otel_metrics.get_metrics_data()
    metric_richieste = None
    for resource_metric in data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name == "http.server.request.count":
                    metric_richieste = metric

    assert metric_richieste is not None
    data_points = list(metric_richieste.data.data_points)
    # Verifica che esistano data point per le combinazioni di attributi
    valori_totali = sum(dp.value for dp in data_points)
    assert valori_totali == 3
```

### Test delle metriche prometheus_client

Per le metriche `prometheus_client`, i test usano registry isolati per evitare interferenze tra test:

```python
import pytest
from prometheus_client import CollectorRegistry, Counter, Histogram


@pytest.fixture
def prom_registry():
    """Registry isolato per ogni test."""
    return CollectorRegistry()


def test_ordini_counter(prom_registry):
    counter = Counter(
        "ordini_creati_total",
        "Ordini creati",
        labelnames=["canale"],
        registry=prom_registry,
    )

    counter.labels(canale="web").inc()
    counter.labels(canale="web").inc()
    counter.labels(canale="api").inc()

    assert counter.labels(canale="web")._value.get() == 2.0
    assert counter.labels(canale="api")._value.get() == 1.0


def test_latenza_histogram(prom_registry):
    hist = Histogram(
        "http_request_duration_seconds",
        "Durata richieste",
        buckets=[0.1, 0.5, 1.0],
        registry=prom_registry,
    )

    hist.observe(0.05)
    hist.observe(0.3)
    hist.observe(0.8)

    # Verifica count e sum
    assert hist._count.get() == 3
    assert abs(hist._sum.get() - 1.15) < 0.001
```

### Test di integrazione con il Collector

Per verificare che la telemetria fluisca correttamente dall'applicazione al backend, si possono usare test di integrazione con un Collector in Docker:

```python
import pytest
import httpx
import time
from testcontainers.compose import DockerCompose


@pytest.fixture(scope="session")
def observability_stack():
    """Avvia lo stack di osservabilita con docker-compose."""
    compose = DockerCompose(
        filepath=".",
        compose_file_name="docker-compose.test.yaml",
    )
    compose.start()
    compose.wait_for("http://localhost:4318/v1/traces")
    yield compose
    compose.stop()


def test_traces_raggiungono_il_backend(observability_stack):
    """Verifica che le traces emesse dall'applicazione raggiungano Tempo."""
    # Genera traffico
    with httpx.Client(base_url="http://localhost:8000") as client:
        resp = client.get("/api/v1/ordini")
        assert resp.status_code == 200

    # Attendi il flush del BatchSpanProcessor
    time.sleep(6)

    # Verifica in Tempo
    with httpx.Client(base_url="http://localhost:3200") as client:
        resp = client.get(
            "/api/search",
            params={"q": 'resource.service.name="ordini-api"', "limit": 1},
        )
        traces = resp.json().get("traces", [])
        assert len(traces) >= 1
```

### Pattern per test robusti

1. **Pulire lo stato tra i test**: chiamare `exporter.clear()` nel teardown della fixture per evitare che span di un test inquinino il successivo.

2. **Usare `SimpleSpanProcessor` nei test**: il `BatchSpanProcessor` esporta in modo asincrono su un thread separato, rendendo i test non deterministici. Il `SimpleSpanProcessor` esporta sincrono — nel test, gli span sono immediatamente disponibili dopo la chiamata.

3. **Non testare l'auto-instrumentation**: i test di auto-instrumentation verificano il funzionamento dell'SDK OTel, non del codice applicativo. Testare solo la propria instrumentazione custom — span creati manualmente, attributi business, metriche custom.

4. **Verificare l'assenza di span sensibili**: aggiungere test negativi che verificano che gli attributi degli span non contengano PII, token o password:

```python
def test_nessun_dato_sensibile_negli_span(otel_spans):
    """Verifica che gli span non contengano dati sensibili."""
    from app.services.ordini_service import processa_ordine

    processa_ordine(ordine_id="ord-123", importo=99.99)

    spans = otel_spans.get_finished_spans()
    campi_sensibili = {"password", "token", "secret", "authorization", "cookie"}

    for span in spans:
        for chiave in span.attributes:
            assert chiave.lower() not in campi_sensibili, (
                f"Attributo sensibile '{chiave}' trovato nello span '{span.name}'"
            )
```

---

## Esercizi

### Esercizio 1 — Full OTel FastAPI (Lab fondamentale)

Creare un servizio FastAPI "catalogo-prodotti" con:
- TracerProvider + MeterProvider + LoggerProvider configurati in `telemetry.py`
- Auto-instrumentation per FastAPI, SQLAlchemy (SQLite), httpx
- 3 endpoint: `GET /prodotti`, `GET /prodotti/{id}`, `POST /prodotti`
- Metriche custom: `prodotti_creati_total`, `catalogo_ricerche_total`, `catalogo_dimensione` (gauge)
- Log strutturati con structlog + trace_id automatico
- Export a OTel Collector → Tempo (traces) + Prometheus (metrics) + Loki (logs)
- docker-compose con tutti i servizi
- Verificare la correlazione tra log, trace e metrica in Grafana

### Esercizio 2 — Tail-Based Sampling

Configurare l'OTel Collector con tail-based sampling:
- 100% delle traces con errori
- 100% delle traces con latenza > 2 secondi
- 5% delle traces riuscite sotto i 2 secondi
- Generare traffico misto (successi, errori, lento) e verificare in Jaeger che le policies funzionino

### Esercizio 3 — Dashboard SLO

Costruire un dashboard Grafana per un servizio con SLO 99.9% disponibilita e P99 latenza < 500ms:
- Pannello SLI disponibilita (finestra rolling 30d)
- Pannello SLI latenza P99
- Pannello error budget rimanente
- Pannello burn rate (multiwindow)
- Alert con regole PromQL per burn rate > 14.4x

### Esercizio 4 — Distributed Tracing multi-servizio

Creare tre servizi FastAPI: `gateway`, `ordini`, `pagamenti`. Il gateway chiama ordini, che chiama pagamenti. Verificare che una singola trace attraversi tutti e tre i servizi con span parent-child corretti. Aggiungere baggage con `tenant_id` e verificare la propagazione.

### Esercizio 5 — Prometheus multiprocess con Gunicorn

Configurare un servizio Flask con gunicorn (4 worker) e `prometheus_client` in multiprocess mode. Verificare che le metriche siano aggregate correttamente indipendentemente da quale worker risponde allo scrape.

### Esercizio 6 — Error tracking con Sentry + OTel

Integrare Sentry in un servizio FastAPI con `instrumenter="otel"`. Implementare:
- Breadcrumb custom per le operazioni business-critical
- Contesto utente (senza PII)
- `before_send` hook che filtra header sensibili
- Release tracking con `sentry-cli`
- Verificare che le traces Sentry siano le stesse di OTel (stesso trace_id)

### Esercizio 7 — Alerting completo

Implementare le seguenti regole di alert per un servizio in Prometheus:
- `HighErrorRate` (>5% per 5 min, critical)
- `HighLatencyP99` (>2s per 10 min, warning)
- `ErrorBudgetBurning` (multiwindow, critical)
- `DBConnectionPoolExhausted` (>90%, critical)
- `ServiceDown` (probe fallita per 1 min, critical)
- Configurare Alertmanager per inviare critical a PagerDuty e warning a Slack

### Esercizio 8 — Profiling continuo con Pyroscope

Integrare Pyroscope in un servizio FastAPI e:
- Identificare un endpoint deliberatamente lento (con `time.sleep` o O(n^2) loop)
- Usare il flame graph per individuare il bottleneck
- Ottimizzare e confrontare i profili prima/dopo

### Esercizio 9 — Custom Metric Design

Progettare lo schema di metriche per un servizio di pagamenti seguendo i pattern RED e USE:
- Definire almeno 10 metriche con naming corretto, label, e bucket appropriati
- Calcolare la cardinalita totale attesa
- Scrivere le query PromQL per: error rate, P99 latenza, throughput, pool saturation

### Esercizio 10 — Migrazione da APM proprietario a OTel

Simulare la migrazione da `ddtrace` a OTel per un servizio Django:
- Configurare il dual-write tramite OTel Collector (export a Datadog e Tempo contemporaneamente)
- Validare la parita dei dati tra i due backend
- Rimuovere `ddtrace` e verificare che il servizio funzioni solo con OTel

---

## Letture

- OpenTelemetry Python Documentation. https://opentelemetry.io/docs/languages/python/
- OpenTelemetry Semantic Conventions. https://opentelemetry.io/docs/concepts/semantic-conventions/
- Prometheus Client Python. https://prometheus.github.io/client_python/
- PromQL Cheat Sheet. https://promlabs.com/promql-cheat-sheet/
- Grafana Documentation. https://grafana.com/docs/grafana/latest/
- Grafana Tempo Documentation. https://grafana.com/docs/tempo/latest/
- Grafana Loki Documentation. https://grafana.com/docs/loki/latest/
- Sentry Python SDK. https://docs.sentry.io/platforms/python/
- structlog Documentation. https://www.structlog.org/en/stable/
- py-spy Documentation. https://github.com/benfred/py-spy
- Pyroscope Documentation. https://grafana.com/docs/pyroscope/latest/
- Google SRE Book — Monitoring Distributed Systems. https://sre.google/sre-book/monitoring-distributed-systems/
- The Art of SLOs. https://sre.google/resources/practices-and-processes/art-of-slos/
- Cindy Sridharan — Distributed Systems Observability. https://www.oreilly.com/library/view/distributed-systems-observability/9781492033431/

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **APM** | Application Performance Monitoring — piattaforme che forniscono visibilita sulle prestazioni delle applicazioni (Datadog, New Relic, Elastic APM). |
| **Auto-instrumentation** | Instrumentazione automatica tramite monkey-patching delle librerie a runtime, senza modifiche al codice applicativo. |
| **Baggage** | Meccanismo W3C per propagare coppie chiave-valore attraverso i confini di servizio nel contesto di un trace. |
| **BatchSpanProcessor** | Processor OTel che accumula span in un buffer e li invia in batch periodici all'exporter — scelta standard per produzione. |
| **Burn rate** | Velocita alla quale viene consumato l'error budget di uno SLO. Un burn rate di 1 significa consumo alla velocita attesa. |
| **Cardinalita** | Numero di combinazioni uniche di valori di label per una metrica. Alta cardinalita = tante time series = alto costo. |
| **Context propagation** | Meccanismo che trasporta il trace context (trace_id, span_id) attraverso i confini di processo e servizio. |
| **Counter** | Tipo di metrica Prometheus che puo solo incrementare. Usato per totali cumulativi (richieste, errori, byte). |
| **Error budget** | Quantita di errore tollerabile prima di violare uno SLO. Se lo SLO e 99.9%, l'error budget e 0.1%. |
| **Exemplar** | Collegamento da un data point di una metrica a un trace specifico, per navigare dal grafico alla trace. |
| **Gauge** | Tipo di metrica Prometheus il cui valore puo salire e scendere. Usato per valori puntuali (connessioni, temperatura). |
| **Histogram** | Tipo di metrica che traccia la distribuzione dei valori osservati in bucket predefiniti. Genera `_bucket`, `_count`, `_sum`. |
| **Liveness probe** | Endpoint K8s per verificare che il processo sia vivo. Se fallisce, il container viene riavviato. |
| **LoggerProvider** | Provider OTel per la gestione dei log. Cattura log da `logging` stdlib e li esporta via OTLP. |
| **MeterProvider** | Provider OTel per la gestione delle metriche. Configura come le metriche vengono aggregate ed esportate. |
| **OTLP** | OpenTelemetry Protocol — protocollo standard per l'invio di telemetria (traces, metrics, logs) ai backend. Supporta gRPC e HTTP. |
| **OTel Collector** | Componente intermedio che riceve, processa e esporta telemetria. Disaccoppia l'applicazione dalla configurazione del backend. |
| **OTel SDK** | OpenTelemetry SDK — implementazione dell'API OTel per un linguaggio specifico. Genera e gestisce la telemetria. |
| **PromQL** | Prometheus Query Language — linguaggio funzionale per interrogare le metriche Prometheus. |
| **Readiness probe** | Endpoint K8s per verificare che il servizio possa gestire traffico. Se fallisce, il pod viene rimosso dal load balancer. |
| **RED method** | Pattern di metriche per servizi: Rate, Errors, Duration. |
| **Resource** | Oggetto OTel che descrive l'entita che produce telemetria (nome servizio, versione, ambiente). |
| **Sampling** | Processo di selezione di un sottoinsieme di traces da raccogliere. Riduce costi di storage e banda. |
| **Semantic Conventions** | Vocabolario standardizzato OTel per nomi di attributi, metriche e span. Garantisce coerenza tra servizi e linguaggi. |
| **SLI** | Service Level Indicator — metrica quantitativa che misura un aspetto del servizio (disponibilita, latenza, throughput). |
| **SLO** | Service Level Objective — target per un SLI (es. "99.9% disponibilita su 30 giorni"). |
| **Span** | Unita di lavoro in un trace. Contiene nome, durata, attributi, eventi. Puo avere span figli. |
| **structlog** | Libreria Python per logging strutturato che produce log JSON con contesto automatico. |
| **Summary** | Tipo di metrica Prometheus che calcola quantili lato client. Non aggregabile — preferire Histogram. |
| **Tail-based sampling** | Decisione di sampling presa dopo la raccolta di tutti gli span di una trace. Implementato nell'OTel Collector. |
| **Trace** | Rappresentazione del percorso di una richiesta attraverso il sistema. Composto da uno o piu span collegati. |
| **TracerProvider** | Provider OTel per la gestione dei traces. Configura sampler, processor ed exporter. |
| **USE method** | Pattern di metriche per risorse: Utilization, Saturation, Errors. |
| **View** | Meccanismo OTel SDK per personalizzare l'aggregazione delle metriche (bucket, attributi da escludere). |
| **W3C Trace Context** | Standard W3C per la propagazione del trace context via header HTTP (`traceparent`, `tracestate`). |
| **`prometheus_client`** | Libreria Python nativa per esporre metriche nel formato Prometheus (pull model). |
