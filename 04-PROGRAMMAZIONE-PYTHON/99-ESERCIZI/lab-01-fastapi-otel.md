# Lab 01 — FastAPI con OpenTelemetry, Structured Logging e Observability End-to-End

> **Tempo stimato:** 4-5 ore
> **Livello:** intermedio-avanzato
> **Data:** 2026-05-23
> **Moduli correlati:**
> [07 — Error Handling e Logging](../07-error-handling-e-logging.md) ·
> [11 — Web Framework](../11-web-framework.md) ·
> [13 — REST API](../13-rest-api.md) ·
> [29 — Pydantic e Validazione](../29-pydantic-e-validazione.md) ·
> [31 — Osservabilita OTel + Prometheus](../31-osservabilita-otel-prometheus.md)

---

## Scenario

Lavori nel team piattaforma di un'azienda fintech. Il team prodotto ha sviluppato un
microservizio per la gestione di un catalogo prodotti interni, ma il servizio e stato
rilasciato senza alcuna osservabilita: nessun tracing distribuito, nessuna metrica custom,
log non strutturati mescolati a `print()`. Quando un endpoint rallenta in produzione,
nessuno riesce a capire dove si accumula la latenza.

Il tuo compito e riscrivere il servizio da zero con FastAPI, integrando fin dal primo
commit: tracing distribuito via OpenTelemetry, metriche Prometheus, logging strutturato
con correlazione automatica al trace corrente. Il deliverable include un
`docker-compose.yml` che avvia Jaeger e Prometheus insieme all'applicazione, cosi che
qualsiasi sviluppatore del team possa fare `docker compose up` e avere l'intero stack
di osservabilita funzionante in locale.

---

## Obiettivi di apprendimento

1. Configurare un progetto FastAPI con `uv` e dipendenze OTel.
2. Definire modelli Pydantic v2 con `@field_validator` e `ConfigDict`.
3. Implementare endpoint CRUD con codici di stato HTTP corretti.
4. Configurare `TracerProvider` con esportatore OTLP verso Jaeger.
5. Abilitare l'auto-instrumentation FastAPI per tracing automatico.
6. Creare span custom per isolare logiche di business nel trace.
7. Configurare `MeterProvider` con istogramma di latenza e contatore custom.
8. Integrare `structlog` con output JSON e processori per contesto.
9. Propagare un Correlation ID (`X-Request-ID`) tramite `contextvars` e middleware ASGI.
10. Correlare log e trace inserendo `trace_id` e `span_id` in ogni riga di log.
11. Comporre lo stack infrastrutturale con `docker-compose` (Jaeger + Prometheus + app).
12. Verificare trace in Jaeger e metriche in Prometheus.

---

## Prerequisiti

- Python >= 3.12 installato.
- `uv` installato (`pip install uv` oppure installer ufficiale).
- Docker e Docker Compose v2 installati.
- Familiarita con HTTP, JSON, terminale.
- Aver completato (o almeno letto) i moduli 11, 13, 29.

---

## Step 1 — Inizializzazione progetto con `uv`

Creiamo la struttura del progetto e installiamo tutte le dipendenze in un unico
passaggio. `uv` gestisce il virtual environment implicitamente.

```bash
mkdir fastapi-otel-lab && cd fastapi-otel-lab
uv init --name fastapi-otel-lab --python 3.12

# Dipendenze applicative
uv add fastapi "uvicorn[standard]" pydantic structlog

# OpenTelemetry SDK + esportatore OTLP (gRPC)
uv add opentelemetry-sdk \
       opentelemetry-exporter-otlp-proto-grpc \
       opentelemetry-instrumentation-fastapi

# Metriche Prometheus
uv add prometheus-client

# Utility
uv add uuid7
```

Struttura attesa dopo l'init:

```
fastapi-otel-lab/
├── pyproject.toml
├── src/
│   └── fastapi_otel_lab/
│       └── __init__.py
└── uv.lock
```

Crea i moduli:

```bash
mkdir -p src/fastapi_otel_lab
touch src/fastapi_otel_lab/{main,models,telemetry,logging_config,middleware}.py
```

**Verifica:**

```bash
uv run python -c "import fastapi; import opentelemetry; print('OK')"
```

---

## Step 2 — Modelli Pydantic v2

Definiamo i modelli di dominio con validazione custom. Usiamo `ConfigDict` (v2)
e `@field_validator` al posto dei vecchi decoratori v1.

```python
# src/fastapi_otel_lab/models.py
"""Modelli Pydantic v2 per il catalogo prodotti."""

from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Category(StrEnum):
    """Categorie di prodotto ammesse."""

    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOD = "food"
    SOFTWARE = "software"


class ProductCreate(BaseModel):
    """Payload per la creazione di un prodotto."""

    model_config = ConfigDict(str_strip_whitespace=True, strict=True)

    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2000)
    price: Decimal = Field(gt=0, decimal_places=2)
    category: Category
    sku: str = Field(min_length=4, max_length=30, pattern=r"^[A-Z0-9\-]+$")

    @field_validator("name")
    @classmethod
    def name_not_placeholder(cls, v: str) -> str:
        forbidden = {"test", "todo", "xxx", "placeholder"}
        if v.lower() in forbidden:
            msg = f"Il nome '{v}' non e ammesso come nome prodotto."
            raise ValueError(msg)
        return v

    @field_validator("price")
    @classmethod
    def price_reasonable(cls, v: Decimal) -> Decimal:
        if v > Decimal("999999.99"):
            msg = "Prezzo superiore al massimo consentito (999999.99)."
            raise ValueError(msg)
        return v


class ProductRead(BaseModel):
    """Rappresentazione pubblica di un prodotto."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    price: Decimal
    category: Category
    sku: str


class ProductUpdate(BaseModel):
    """Payload per aggiornamento parziale (PATCH)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    category: Category | None = None
```

**Verifica:**

```bash
uv run python -c "
from fastapi_otel_lab.models import ProductCreate, Category
from decimal import Decimal
p = ProductCreate(
    name='Widget Pro', price=Decimal('29.99'),
    category=Category.ELECTRONICS, sku='WGT-001'
)
print(p.model_dump_json(indent=2))
"
```

---

## Step 3 — Configurazione OpenTelemetry (TracerProvider + MeterProvider)

Questo modulo centralizza tutta la configurazione di telemetria. Teniamolo separato
da `main.py` per testabilita e riuso.

```python
# src/fastapi_otel_lab/telemetry.py
"""Configurazione centralizzata OpenTelemetry: tracing + metrics."""

import os

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from prometheus_client import Histogram, Counter


# --- Risorse condivise -------------------------------------------------------

_resource = Resource.create({
    SERVICE_NAME: "fastapi-otel-lab",
    SERVICE_VERSION: "0.1.0",
    "deployment.environment": os.getenv("DEPLOY_ENV", "development"),
})


# --- Tracing ------------------------------------------------------------------

def init_tracing() -> trace.Tracer:
    """Configura TracerProvider con OTLP gRPC exporter verso Jaeger."""
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    processor = BatchSpanProcessor(exporter)

    provider = TracerProvider(resource=_resource)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    return trace.get_tracer("fastapi-otel-lab")


# --- Metrics ------------------------------------------------------------------

def init_metrics() -> metrics.Meter:
    """Configura MeterProvider con OTLP gRPC exporter."""
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=5000)

    provider = MeterProvider(resource=_resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)

    return metrics.get_meter("fastapi-otel-lab")


# --- Prometheus metrics (scrape-based) ----------------------------------------

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Latenza delle richieste HTTP in secondi",
    labelnames=["method", "endpoint", "status_code"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

PRODUCTS_CREATED = Counter(
    "products_created_total",
    "Numero totale di prodotti creati",
    labelnames=["category"],
)
```

**Verifica:**

```bash
uv run python -c "
from fastapi_otel_lab.telemetry import init_tracing, init_metrics
tracer = init_tracing()
meter = init_metrics()
print(f'Tracer: {tracer}')
print(f'Meter: {meter}')
print('Telemetry init OK')
"
```

---

## Step 4 — Structured Logging con structlog

Configuriamo `structlog` con output JSON in produzione e output colorato in
sviluppo. I processori aggiungono automaticamente timestamp, livello, e — cruciale —
`trace_id` e `span_id` dal contesto OTel corrente.

```python
# src/fastapi_otel_lab/logging_config.py
"""Configurazione structlog con correlazione OTel."""

import logging
import os
import sys

import structlog
from opentelemetry import trace


def _add_otel_context(
    _logger: object,
    _method: str,
    event_dict: dict,
) -> dict:
    """Processore custom: inietta trace_id e span_id dal contesto OTel."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


def setup_logging() -> None:
    """Inizializza structlog con processori per JSON + correlazione OTel."""
    is_prod = os.getenv("DEPLOY_ENV", "development") == "production"

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        _add_otel_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if is_prod:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
```

**Verifica:**

```bash
DEPLOY_ENV=production uv run python -c "
from fastapi_otel_lab.logging_config import setup_logging
from fastapi_otel_lab.telemetry import init_tracing
init_tracing()
setup_logging()
import structlog
log = structlog.get_logger()
log.info('test_event', product_id='abc-123')
"
```

Output atteso: riga JSON con `event`, `product_id`, `timestamp`, `level`. Senza
span attivo, `trace_id`/`span_id` non compaiono — li vedrai nelle richieste HTTP.

---

## Step 5 — Middleware: Correlation ID e metriche di latenza

Il middleware fa tre cose:
1. Legge (o genera) un `X-Request-ID` dall'header della richiesta.
2. Lo propaga tramite `contextvars` cosi che `structlog` lo includa in ogni log.
3. Misura la latenza della richiesta e la registra nell'istogramma Prometheus.

```python
# src/fastapi_otel_lab/middleware.py
"""ASGI middleware per correlation ID e metriche di latenza."""

import time
import uuid
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from fastapi_otel_lab.telemetry import REQUEST_LATENCY

# Context var accessibile da qualsiasi punto dello stack async
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")

logger = structlog.get_logger()


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Inietta X-Request-ID nel contesto e misura la latenza."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint,
    ) -> Response:
        # 1. Correlation ID
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        correlation_id_ctx.set(request_id)

        # Bind nel contesto structlog per tutti i log di questa richiesta
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=request_id,
            http_method=request.method,
            http_path=request.url.path,
        )

        # 2. Misura latenza
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        # 3. Registra nell'istogramma Prometheus
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
        ).observe(duration)

        # Propaga l'ID nella risposta
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_s=round(duration, 4),
        )

        return response
```

---

## Step 6 — Applicazione FastAPI: endpoint CRUD

Store in-memory (lo scopo del lab e l'osservabilita, non la persistenza). I trace
custom avvolgono la logica di business per isolarla nel waterfall di Jaeger.

```python
# src/fastapi_otel_lab/main.py
"""FastAPI application con OTel tracing, metriche e structured logging."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from decimal import Decimal
from typing import Any

import structlog
import uuid7
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from fastapi_otel_lab.logging_config import setup_logging
from fastapi_otel_lab.middleware import CorrelationIDMiddleware
from fastapi_otel_lab.models import (
    Category,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)
from fastapi_otel_lab.telemetry import (
    init_metrics,
    init_tracing,
    PRODUCTS_CREATED,
)

logger = structlog.get_logger()

# In-memory store — dict e immutabile a livello di singolo record:
# ogni update restituisce un nuovo dict, non modifica l'originale.
_products: dict[str, dict[str, Any]] = {}


# --- Lifespan -----------------------------------------------------------------

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Inizializza telemetria e logging all'avvio."""
    tracer = init_tracing()
    _meter = init_metrics()
    setup_logging()
    logger.info("app_started", service="fastapi-otel-lab")
    yield
    # Shutdown: flush dei processori
    provider = trace.get_tracer_provider()
    if hasattr(provider, "shutdown"):
        provider.shutdown()
    logger.info("app_stopped")


# --- App factory --------------------------------------------------------------

app = FastAPI(
    title="Catalogo Prodotti — OTel Lab",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CorrelationIDMiddleware)

# Auto-instrumentation FastAPI: crea span per ogni richiesta HTTP automaticamente
FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer("fastapi-otel-lab")


# --- Helpers ------------------------------------------------------------------

def _format_product(product_id: str, data: dict[str, Any]) -> ProductRead:
    """Converte il record interno in ProductRead."""
    return ProductRead(id=product_id, **data)


def _find_product_or_404(product_id: str) -> dict[str, Any]:
    """Cerca un prodotto; solleva 404 se non trovato."""
    product = _products.get(product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prodotto '{product_id}' non trovato.",
        )
    return product


# --- Endpoints ----------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    """Healthcheck per orchestratori e load balancer."""
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
async def metrics_scrape() -> Response:
    """Endpoint di scrape Prometheus (formato OpenMetrics)."""
    from starlette.responses import Response as RawResponse
    return RawResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.post(
    "/products",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(payload: ProductCreate) -> ProductRead:
    """Crea un nuovo prodotto nel catalogo."""
    # Span custom: isola la logica di business nel trace
    with tracer.start_as_current_span("create_product.business_logic") as span:
        product_id = str(uuid7.create())
        data = payload.model_dump()
        # Conversione Decimal -> str per serializzazione
        data["price"] = data["price"]

        # Attributi sullo span per debugging in Jaeger
        span.set_attribute("product.id", product_id)
        span.set_attribute("product.sku", data["sku"])
        span.set_attribute("product.category", data["category"])

        # Simula una validazione di business (es. check duplicato SKU)
        with tracer.start_as_current_span("check_duplicate_sku"):
            for existing in _products.values():
                if existing["sku"] == data["sku"]:
                    logger.warning("duplicate_sku", sku=data["sku"])
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"SKU '{data['sku']}' gia esistente.",
                    )

        _products[product_id] = data

        # Metrica custom
        PRODUCTS_CREATED.labels(category=data["category"]).inc()

        logger.info("product_created", product_id=product_id, sku=data["sku"])

    return _format_product(product_id, data)


@app.get("/products", response_model=list[ProductRead])
async def list_products(
    category: Category | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
) -> list[ProductRead]:
    """Lista prodotti con filtri opzionali."""
    with tracer.start_as_current_span("list_products.filter") as span:
        results: list[ProductRead] = []

        for pid, data in _products.items():
            if category is not None and data["category"] != category:
                continue
            price = data["price"]
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue
            results.append(_format_product(pid, data))

        span.set_attribute("result.count", len(results))
        logger.info("products_listed", count=len(results))

    return results


@app.get("/products/{product_id}", response_model=ProductRead)
async def get_product(product_id: str) -> ProductRead:
    """Restituisce un singolo prodotto per ID."""
    data = _find_product_or_404(product_id)
    return _format_product(product_id, data)


@app.patch("/products/{product_id}", response_model=ProductRead)
async def update_product(product_id: str, payload: ProductUpdate) -> ProductRead:
    """Aggiornamento parziale di un prodotto (PATCH)."""
    existing = _find_product_or_404(product_id)

    with tracer.start_as_current_span("update_product.apply_changes") as span:
        # Pattern immutabile: crea un nuovo dict con le modifiche
        updates = payload.model_dump(exclude_unset=True)
        updated = {**existing, **updates}
        _products[product_id] = updated

        span.set_attribute("product.id", product_id)
        span.set_attribute("fields_updated", list(updates.keys()))
        logger.info(
            "product_updated",
            product_id=product_id,
            fields=list(updates.keys()),
        )

    return _format_product(product_id, updated)


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str) -> None:
    """Elimina un prodotto dal catalogo."""
    _find_product_or_404(product_id)
    del _products[product_id]
    logger.info("product_deleted", product_id=product_id)


# --- Error handler globale con match/case ------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Any, exc: HTTPException) -> JSONResponse:
    """Handler centralizzato con log strutturato per livello di severita."""
    match exc.status_code:
        case code if 400 <= code < 500:
            logger.warning("client_error", status=code, detail=exc.detail)
        case code if code >= 500:
            logger.error("server_error", status=code, detail=exc.detail)
        case _:
            logger.info("http_exception", status=exc.status_code, detail=exc.detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
```

**Verifica:**

```bash
uv run uvicorn fastapi_otel_lab.main:app --reload --port 8000
```

In un altro terminale:

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
curl -s -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" -H "X-Request-ID: lab-test-001" \
  -d '{"name":"Widget Pro","price":"29.99","category":"electronics","sku":"WGT-001"}' \
  | python3 -m json.tool
curl -s http://localhost:8000/products | python3 -m json.tool
```

Nei log del server: righe JSON con `correlation_id: "lab-test-001"`, `trace_id`, `span_id`.

---

## Step 7 — Docker Compose: Jaeger + Prometheus + App

### 7a — Dockerfile dell'applicazione

```dockerfile
# Dockerfile
FROM python:3.12-slim AS base

WORKDIR /app

# Installa uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copia file di progetto
COPY pyproject.toml uv.lock ./
COPY src/ src/

# Installa dipendenze
RUN uv sync --frozen --no-dev

# Esponi porta
EXPOSE 8000

CMD ["uv", "run", "uvicorn", "fastapi_otel_lab.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
```

### 7b — Configurazione Prometheus

```yaml
# prometheus.yml
global:
  scrape_interval: 5s
  evaluation_interval: 5s

scrape_configs:
  - job_name: "fastapi-otel-lab"
    metrics_path: /metrics
    static_configs:
      - targets: ["app:8000"]
        labels:
          environment: "development"
```

### 7c — Docker Compose

```yaml
# docker-compose.yml
services:

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://jaeger:4317"
      DEPLOY_ENV: "production"
    depends_on:
      jaeger:
        condition: service_started
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 3s
      retries: 3

  jaeger:
    image: jaegertracing/jaeger:2
    ports:
      - "16686:16686"   # UI
      - "4317:4317"     # OTLP gRPC
      - "4318:4318"     # OTLP HTTP
    environment:
      COLLECTOR_OTLP_ENABLED: "true"

  prometheus:
    image: prom/prometheus:v3.4.0
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    depends_on:
      - app
```

**Verifica:**

```bash
docker compose up --build -d

# Attendi che i container siano healthy
docker compose ps

# Test rapido
curl -s http://localhost:8000/health
```

---

## Step 8 — Verifica tracing in Jaeger

Genera traffico per popolare i trace:

```bash
# Crea prodotti + provoca un 409 e un 404
for i in 1 2 3; do
  curl -s -X POST http://localhost:8000/products \
    -H "Content-Type: application/json" \
    -H "X-Request-ID: test-$i" \
    -d "{\"name\":\"Prodotto $i\",\"price\":\"$((i*10+5)).99\",\"category\":\"electronics\",\"sku\":\"SKU-00$i\"}" > /dev/null
done
curl -s -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Dup","price":"9.99","category":"food","sku":"SKU-001"}'
curl -s http://localhost:8000/products/non-esiste
```

Apri **http://localhost:16686**, seleziona il servizio `fastapi-otel-lab`, clicca
**Find Traces**. In un trace POST `/products` dovresti vedere:

- Span root: `POST /products` (auto-instrumentation).
- Span figlio: `create_product.business_logic`.
- Span nipote: `check_duplicate_sku`.
- Attributi: `product.id`, `product.sku`, `product.category`.

---

## Step 9 — Verifica metriche in Prometheus

Apri **http://localhost:9090** e prova queste query PromQL:

| Query | Descrizione |
|-------|-------------|
| `rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])` | Latenza media |
| `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` | P95 latenza |
| `products_created_total` | Contatore prodotti per categoria |
| `sum(rate(http_request_duration_seconds_count{status_code=~"4.."}[5m]))` | Tasso errori client |

Verifica che i valori siano coerenti con il traffico generato nello step 8.

---

## Step 10 — Verifica correlazione trace-log

```bash
docker compose logs app --tail 20
```

Ogni riga JSON deve contenere almeno: `timestamp`, `level`, `event`,
`correlation_id`, `trace_id` (32 hex), `span_id` (16 hex).

**Test di correlazione:** copia il `trace_id` da una riga `product_created` nei
log, incollalo nella barra di ricerca di Jaeger. Il trace deve corrispondere
esattamente alla richiesta che ha generato quel log. Questo e il flusso che un
ingegnere on-call segue durante un incident: log di errore -> `trace_id` ->
waterfall in Jaeger.

---

## Step 11 — Pulizia e teardown

```bash
docker compose down -v
```

---

## Deliverable checklist

- [ ] Progetto inizializzato con `uv`, `pyproject.toml` con tutte le dipendenze.
- [ ] Modelli Pydantic v2 con `@field_validator` custom e `ConfigDict`.
- [ ] 5 endpoint REST: `POST`, `GET` (lista + singolo), `PATCH`, `DELETE`.
- [ ] Codici HTTP corretti: 201, 200, 204, 404, 409.
- [ ] `TracerProvider` configurato con OTLP exporter verso Jaeger.
- [ ] Auto-instrumentation FastAPI attiva.
- [ ] Almeno 2 span custom (`create_product.business_logic`, `check_duplicate_sku`).
- [ ] `REQUEST_LATENCY` histogram con label `method`, `endpoint`, `status_code`.
- [ ] `PRODUCTS_CREATED` counter con label `category`.
- [ ] `structlog` con output JSON e processore `_add_otel_context`.
- [ ] Middleware `CorrelationIDMiddleware` con `X-Request-ID` via `contextvars`.
- [ ] `docker-compose.yml` con `app`, `jaeger`, `prometheus` — funzionante con `docker compose up`.
- [ ] Trace visibili in Jaeger con span annidati e attributi custom.
- [ ] Metriche visibili in Prometheus con query PromQL funzionanti.
- [ ] Log JSON con `trace_id`, `span_id`, `correlation_id` presenti.
- [ ] Correlazione verificata: `trace_id` da un log porta al trace corretto in Jaeger.

---

## Criteri di valutazione

| Criterio | Peso | Sufficiente | Eccellente |
|----------|------|-------------|------------|
| Setup progetto e dipendenze | 5% | `uv init` + dipendenze corrette | `pyproject.toml` con metadati completi, versioni pinned |
| Modelli Pydantic v2 | 10% | Modelli base funzionanti | Validatori custom, `ConfigDict`, `StrEnum` |
| Endpoint CRUD | 15% | CRUD funzionante | Status code corretti, gestione errori, response model |
| TracerProvider + OTLP | 15% | Tracing funzionante | Resource attributes, batch processor configurato |
| Auto-instrumentation | 5% | `FastAPIInstrumentor` attivo | Trace visibili in Jaeger con span HTTP |
| Span custom | 10% | Almeno 1 span custom | Span annidati con attributi di business |
| Metriche Prometheus | 10% | Histogram presente | Histogram + counter, label corrette, query PromQL |
| structlog + JSON | 10% | Log strutturati | Processori custom, correlazione OTel |
| Correlation ID middleware | 10% | Header propagato | `contextvars`, bind structlog, risposta con ID |
| Docker Compose | 10% | Stack avviabile | Healthcheck, volumi, dipendenze tra servizi |

---

## Suggerimenti

1. **Non saltare la verifica.** Ogni step ha un comando di verifica — eseguilo
   prima di passare al successivo.

2. **Jaeger v2 accetta OTLP nativamente** su `4317` (gRPC) e `4318` (HTTP).
   Non serve un collector separato.

3. **`contextvars` e async.** Ogni task mantiene il proprio contesto. Con
   `run_in_executor`, copia il contesto con `copy_context().run()`.

4. **OTLP vs Prometheus scrape.** Qui usiamo `prometheus_client` con scrape
   (`/metrics`) — pattern piu comune in produzione. OTLP push e un'alternativa;
   i due approcci coesistono.

5. **`insecure=True`** solo per sviluppo locale. In produzione, TLS obbligatorio.

6. **Ordine nel lifespan:** tracing -> metriche -> logging (il logging dipende
   dal tracer per la correlazione).

7. **Estensioni possibili:** `LoggerProvider` OTel, endpoint `/ready`, Grafana
   con dashboard pre-configurata, store SQLite + SQLAlchemy con auto-instrumentation.

---

> **Moduli di riferimento per approfondire:**
>
> - [Modulo 07 — Error Handling e Logging](../07-error-handling-e-logging.md): `structlog`, `contextvars`, exception chaining.
> - [Modulo 11 — Web Framework](../11-web-framework.md): FastAPI lifespan, middleware, dependency injection.
> - [Modulo 13 — REST API](../13-rest-api.md): status code, OpenAPI schema, Pydantic integration.
> - [Modulo 29 — Pydantic e Validazione](../29-pydantic-e-validazione.md): `field_validator`, `ConfigDict`, `model_dump`.
> - [Modulo 31 — Osservabilita OTel + Prometheus](../31-osservabilita-otel-prometheus.md): TracerProvider, MeterProvider, auto-instrumentation.
