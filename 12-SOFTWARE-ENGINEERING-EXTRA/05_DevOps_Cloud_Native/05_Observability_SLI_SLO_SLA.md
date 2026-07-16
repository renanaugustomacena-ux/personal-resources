# Module 5.5: Observability — Metrics, Logs, Traces, SLI/SLO/SLA

> **Module 05.5** · **Last updated:** 2026-04-27

## Guiding ideas
1. **OTel SDK end-to-end: tracer + meter + logger correlated.**
2. **Sampling: head-based for cost, tail-based for quality.**
3. **Vendor-neutral exporters: avoid lock-in.**
4. **SLI = measurement, SLO = internal target, SLA = contract.**
5. **Multi-burn-rate alerts > threshold static.**


**Date:** 2026-04-22
**Status:** Completed

## 1. The Pillars

Three classical pillars + an emerging fourth:
1.  **Metrics** — numeric time series, low cardinality, cheap to store, fast to query.
2.  **Logs** — discrete events, high cardinality, expensive at scale.
3.  **Traces** — causally-linked spans across services.
4.  **Profiles** (continuous profiling) — CPU/heap flamegraphs over time (Pyroscope, Parca).

Pillars are **complementary**: metrics tell you *something is wrong*, traces tell you *where*, logs and profiles tell you *why*.

## 2. Metrics: Prometheus Model

### 2.1 Pull Model
*   Targets expose `/metrics` (text/openmetrics format).
*   Prometheus scrapes on a schedule (`scrape_interval: 15s`).
*   Service discovery via K8s API, Consul, EC2, file_sd.
*   **Pro:** target liveness is a free signal (`up == 0`).
*   **Con:** ephemeral jobs need a Pushgateway.

### 2.2 Metric Types
| Type | Semantics | Example |
| :--- | :--- | :--- |
| **Counter** | Monotonic; reset on restart | `http_requests_total` |
| **Gauge** | Up/down value | `memory_bytes` |
| **Histogram** | Bucketed counts + sum + count | `http_request_duration_seconds_bucket` |
| **Summary** | Pre-computed quantiles per instance | client-side p50/p99 |

Histogram is preferred for latency: server aggregates buckets, $\phi$-quantiles computed at query time with `histogram_quantile()`.

### 2.3 Recording Rules & Federation
*   **Recording rules** pre-aggregate frequent queries (`job:http_requests:rate5m`).
*   **Federation:** hierarchical scrape between Prometheus instances (datacenter → global).
*   **`remote_write`** to long-term stores: **Mimir**, **Thanos**, **VictoriaMetrics**, **Cortex** — solve retention, HA, multi-tenant.

### 2.4 Cardinality Bombs
*   Series count = product of label values.
*   `user_id`, `request_id`, `email` as labels = death.
*   Rule: labels must have **bounded, low cardinality**. Put unique IDs in **traces/logs**, not metric labels.

## 3. Logs

### 3.1 Structured Logging
*   JSON, one event per line. Fields: `ts`, `level`, `msg`, `service`, `trace_id`, `span_id`, plus context.
*   Avoid string interpolation that hides fields.
*   **Levels:** TRACE / DEBUG / INFO / WARN / ERROR / FATAL. Keep INFO meaningful in prod.

### 3.2 Correlation
*   Inject **`trace_id`** into every log line emitted while a request is in scope.
*   Generate per-request **correlation ID** at the edge if no trace yet (`X-Request-Id`).

### 3.3 Storage Trade-offs
| Stack | Index | Cost profile | Query |
| :--- | :--- | :--- | :--- |
| **ELK / OpenSearch** | Full-text inverted index | Expensive ingest + storage | Rich (Lucene) |
| **Loki** | Index labels only, content compressed | Cheap | LogQL; slower full-text |
| **ClickHouse / SigNoz** | Columnar | Cheap, fast aggregates | SQL |

### 3.4 Sampling
*   Tail-sample noisy INFO logs (keep 10%, keep 100% of ERROR).
*   Always emit fully on error path.

## 4. Traces

### 4.1 OpenTelemetry
The vendor-neutral standard. Replaces OpenTracing + OpenCensus.

*   **SDK:** instrumentation in app code (auto-instrumentation for many frameworks).
*   **Collector:** sidecar/daemon receiving OTLP, processing (batching, redaction, sampling), exporting to backends.
*   **Wire:** **OTLP** over gRPC/HTTP.

### 4.2 Span Anatomy
*   `trace_id` (128-bit), `span_id` (64-bit), `parent_span_id`, name, kind (client/server/producer/consumer/internal), `start`, `end`, status, attributes, events, links.
*   **W3C Trace Context** propagation header: `traceparent: 00-<trace-id>-<parent-span-id>-<flags>`.

### 4.3 Sampling
*   **Head sampling:** decision at root span (cheap, may miss errors).
*   **Tail sampling:** collector buffers full trace then decides (keeps all errors/slow). Costlier but signal-rich.

### 4.4 Backends
**Jaeger**, **Tempo** (Grafana, object-store backed), **Zipkin**, **SigNoz**, **Honeycomb**, **Lightstep**.

## 5. Correlation Across Pillars

*   **Exemplars:** attach a `trace_id` to a histogram bucket sample → from a latency spike click straight into a representative trace.
*   **Logs ↔ traces:** structured `trace_id`/`span_id` fields → Grafana/Loki "view trace" link.
*   **Metrics ↔ logs:** Loki derived fields, label parity (`service`, `env`, `cluster`).

Goal: any alert leads to the relevant trace and logs in **<3 clicks**.

## 6. SLI / SLO / SLA

### 6.1 Definitions (Google SRE)
*   **SLI — Service Level Indicator:** a measured ratio of "good" to "valid" events.
    $$\text{SLI} = \frac{\text{good events}}{\text{valid events}}$$
*   **SLO — Service Level Objective:** internal target (e.g., 99.9% of requests in 30 days).
*   **SLA — Service Level Agreement:** external contract; missing → financial penalty/credits.

Rule: SLA loose ≪ SLO ≪ achievable performance. SLO is the line your team optimizes against; SLA is what legal signs.

### 6.2 SLI Patterns
*   **Request-based:** ratio of OK/total over a window.
*   **Window-based:** fraction of N-second windows that met threshold.
*   Common SLIs: availability, latency (p99 < X ms), correctness, freshness, throughput, durability.

### 6.3 Availability Math
| SLO | Allowed downtime / 30 days |
| :--- | :--- |
| 99.0% | 7h 12m |
| 99.5% | 3h 36m |
| 99.9% | **43m 12s** |
| 99.95% | 21m 36s |
| 99.99% | 4m 19s |
| 99.999% | 26s |

Each extra "nine" ≈ 10× engineering cost. Pick deliberately.

### 6.4 Error Budget
$$\text{Budget} = (1 - \text{SLO}) \times \text{Window}$$

When budget burns slowly → ship features. When it burns fast → freeze releases, prioritize reliability.

### 6.5 Burn-Rate Alerts
Multi-window, multi-burn-rate (Google SRE workbook):
*   **Fast burn:** consuming the 30d budget in 1h → alert if 14.4× burn over 1h **and** 5m.
*   **Slow burn:** consuming the budget in <3 days → alert if 6× burn over 6h **and** 30m.
*   Two windows reduce false positives (short window must confirm long).

## 7. Diagnostic Methods

### 7.1 Golden Signals (Google)
1.  **Latency** (success vs error latency separately).
2.  **Traffic** (RPS, QPS).
3.  **Errors** (rate of failed requests).
4.  **Saturation** (how full the resource is).

### 7.2 USE (Brendan Gregg, resources)
For every resource: **U**tilization, **S**aturation, **E**rrors. Best for OS/hardware (CPU, disk, NIC).

### 7.3 RED (Tom Wilkie, services)
For every service: **R**ate, **E**rrors, **D**uration. Best for request-driven microservices.

USE + RED together cover infra and application layers; map both onto the four golden signals.
