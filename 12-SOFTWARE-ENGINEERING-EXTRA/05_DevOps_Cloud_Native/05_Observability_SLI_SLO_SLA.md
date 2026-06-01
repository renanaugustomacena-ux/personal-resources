---
corso: "SWE Masterclass"
fase: "5 — DevOps & Cloud Native"
modulo: "5.5"
titolo: "Observability — Metrics, Logs, Traces, SLI/SLO/SLA"
versione: "OpenTelemetry 1.x / Prometheus 3.x / Grafana Mimir 3.0 / Loki 3.x / Tempo 2.9"
livello: "Advanced"
prerequisiti:
  - "HTTP, gRPC, and REST API fundamentals"
  - "Distributed systems basics (microservices, message queues)"
  - "Kubernetes architecture (Module 5.2)"
  - "Site Reliability Engineering concepts (Module 5.3)"
  - "Basic statistics (percentiles, rates, histograms)"
obiettivi:
  - "Instrument a multi-service application with OpenTelemetry SDK to emit correlated metrics, logs, and traces"
  - "Deploy a Prometheus + Grafana Mimir stack with recording rules, remote_write, and multi-tenant long-term retention"
  - "Define SLIs for availability and latency, set SLOs with error budgets, and configure multi-burn-rate alerts"
  - "Implement tail-based sampling in the OTel Collector that retains 100% of error/slow traces while sampling normal traffic"
  - "Correlate across all three pillars so any alert leads to the relevant trace and logs within three clicks"
tag: [observability, opentelemetry, prometheus, grafana, mimir, loki, tempo, sli, slo, sla, error-budget, distributed-tracing, metrics, logs]
---

# Module 5.5: Observability — Metrics, Logs, Traces, SLI/SLO/SLA

> **Learning Objectives**
> After completing this module you will be able to:
> 1. Instrument a multi-service application with OpenTelemetry SDK to emit correlated metrics, logs, and traces.
> 2. Deploy a Prometheus + Grafana Mimir stack with recording rules, remote_write, and multi-tenant long-term retention.
> 3. Define SLIs for availability and latency, set SLOs with error budgets, and configure multi-burn-rate alerts.
> 4. Implement tail-based sampling in the OTel Collector that retains 100% of error/slow traces while sampling normal traffic.
> 5. Correlate across all three pillars so any alert leads to the relevant trace and logs within three clicks.

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

## Exercises

1. **Prometheus + Grafana Dashboard for Golden Signals**
   Deploy Prometheus (via Helm on Kubernetes or Docker Compose) scraping a sample HTTP service that exposes `/metrics`. Create a Grafana dashboard with four panels covering the Golden Signals: (a) request rate (`rate(http_requests_total[5m])`), (b) error rate (`rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])`), (c) latency p50/p95/p99 using `histogram_quantile()`, (d) saturation (CPU/memory utilization from `node_exporter`). Add a recording rule for `job:http_requests:rate5m` and verify it reduces query latency on the dashboard.

2. **Distributed Tracing with OpenTelemetry Collector and Tail-Based Sampling**
   Instrument two microservices (e.g., an API gateway and an order service) with the OpenTelemetry SDK (auto-instrumentation). Deploy an OTel Collector in gateway mode with a `tail_sampling` processor configured to: (a) always keep traces with any span status `ERROR`, (b) always keep traces with total duration > 2 seconds, (c) probabilistically sample 10% of remaining traces. Export to Grafana Tempo (or Jaeger). Verify in the UI that all error traces appear while normal traffic is sampled. Measure the storage reduction compared to 100% sampling.

3. **SLO Definition and Multi-Burn-Rate Alerting**
   For a production-like API, define two SLIs: availability (ratio of non-5xx responses) and latency (fraction of requests completing in < 300 ms). Set a 30-day SLO of 99.9% for each. Calculate the error budget (43 minutes of downtime / 0.1% error allowance). Implement multi-burn-rate alerts in Prometheus: (a) fast burn — 14.4x rate over 1h confirmed by 5m window, (b) slow burn — 6x rate over 6h confirmed by 30m window. Wire alerts to Alertmanager with Slack/PagerDuty receiver. Simulate a latency spike and verify the fast-burn alert fires within minutes.

4. **Cross-Pillar Correlation: Metrics → Traces → Logs**
   Configure exemplars on a Prometheus histogram so that each bucket sample carries a `trace_id`. In Grafana, click a latency spike data point and follow the exemplar link to the representative trace in Tempo. From the trace, use the `trace_id` / `span_id` fields injected into structured logs to jump to the corresponding log lines in Loki. Document the end-to-end click path and verify it completes in fewer than three navigations.

5. **Log Pipeline with Loki: Structured Ingestion, Retention, and Cost Control**
   Deploy Grafana Loki with a structured metadata pipeline: (a) configure Promtail/Alloy to parse JSON logs and extract `service`, `level`, `trace_id` as index labels, (b) set up a retention policy that keeps ERROR logs for 90 days and INFO logs for 14 days, (c) implement tail-sampling at the agent level to drop 90% of DEBUG logs before they reach Loki. Write LogQL queries that filter by `trace_id` and by error patterns. Compare ingest volume and query speed before and after the sampling rule.

## Readings and References

### Books

*   Beyer, B.; Jones, C.; Petoff, J.; Murphy, N. R. — *Site Reliability Engineering: How Google Runs Production Systems* (O'Reilly, 2016). Chapters 4–6 on SLIs, SLOs, error budgets. — [sre.google/sre-book](https://sre.google/sre-book/table-of-contents/) (retrieved: 2026-05-29)
*   Beyer, B. et al. — *The Site Reliability Workbook* (O'Reilly, 2018). Practical SLO implementation, alerting on SLOs. — [sre.google/workbook](https://sre.google/workbook/table-of-contents/) (retrieved: 2026-05-29)
*   Majors, C.; Fong-Jones, L.; Miranda, G. — *Observability Engineering* (O'Reilly, 2022). Covers instrumentation, tracing, and observability culture.
*   Sridharan, C. — *Distributed Systems Observability* (O'Reilly, 2018). Concise treatment of the three pillars and their correlation.

### Official Documentation

*   OpenTelemetry — *Observability Primer*. — [opentelemetry.io/docs/concepts/observability-primer](https://opentelemetry.io/docs/concepts/observability-primer/) (retrieved: 2026-05-29)
*   OpenTelemetry — *Collector Documentation*. — [opentelemetry.io/docs/collector](https://opentelemetry.io/docs/collector/) (retrieved: 2026-05-29)
*   Grafana Labs — *Grafana Mimir 3.0 Release (Nov 2025)*. — [grafana.com](https://grafana.com/about/press/2025/11/05/grafana-labs-launches-mimir-3.0-expanding-open-observability-at-scale-at-kubecon--cloudnativecon-north-america-2025/) (retrieved: 2026-05-29)
*   Grafana Labs — *Mimir Documentation*. — [grafana.com/docs/mimir/latest](https://grafana.com/docs/mimir/latest/) (retrieved: 2026-05-29)

### Articles and Guides

*   Better Stack — *Essential OpenTelemetry Best Practices for Robust Observability*. — [betterstack.com](https://betterstack.com/community/guides/observability/opentelemetry-best-practices/) (retrieved: 2026-05-29)
*   OneUptime — *How to Implement SLO Monitoring with OpenTelemetry Metrics*. — [oneuptime.com](https://oneuptime.com/blog/post/2026-02-06-slo-monitoring-opentelemetry-metrics/view) (retrieved: 2026-05-29)
*   Uptrace — *Defining SLA/SLO-Driven Monitoring Requirements in 2025*. — [uptrace.dev](https://uptrace.dev/blog/sla-slo-monitoring-requirements) (retrieved: 2026-05-29)
*   sanj.dev — *Scaling Prometheus in 2026: Thanos vs Mimir vs VictoriaMetrics*. — [sanj.dev](https://sanj.dev/post/prometheus-scaling-thanos-mimir-victoriametrics/) (retrieved: 2026-05-29)

## Cross-References

| Topic | Module | Link |
| :--- | :--- | :--- |
| Container internals (cgroups, namespaces, OCI) | 5.1 | [01_Container_Internals.md](01_Container_Internals.md) |
| Kubernetes architecture and workloads | 5.2 | [02_Kubernetes_Architecture.md](02_Kubernetes_Architecture.md) |
| Site Reliability Engineering (error budgets, toil, incident response) | 5.3 | [03_Site_Reliability_Engineering.md](03_Site_Reliability_Engineering.md) |
| Infrastructure as Code — Terraform, Pulumi, Ansible | 5.4 | [04_Infrastructure_as_Code.md](04_Infrastructure_as_Code.md) |
| Cloud architecture — AWS, Azure, GCP, landing zones, FinOps | 5.6 | [06_Cloud_Architecture_AWS_Azure_GCP.md](06_Cloud_Architecture_AWS_Azure_GCP.md) |
| Security, cryptography, and zero-trust models | — | [../../04_Security_Cryptography/](../../04_Security_Cryptography/) |

## Glossary

| Term | Definition |
| :--- | :--- |
| **Metric** | Numeric time series with labels; low cardinality, cheap to store, fast to query. Foundation for alerting. |
| **Log** | Discrete event record with timestamp, level, message, and structured fields. High cardinality, expensive at scale. |
| **Trace** | Causally-linked set of spans representing a request's journey across services; identified by a 128-bit `trace_id`. |
| **Span** | A single unit of work within a trace, carrying start/end time, status, attributes, and parent linkage. |
| **OpenTelemetry (OTel)** | Vendor-neutral CNCF project providing SDKs, Collector, and wire protocol (OTLP) for metrics, logs, and traces. |
| **SLI (Service Level Indicator)** | A measured ratio of good events to valid events, expressing a concrete aspect of service quality. |
| **SLO (Service Level Objective)** | An internal reliability target expressed as an SLI threshold over a rolling window (e.g., 99.9% over 30 days). |
| **SLA (Service Level Agreement)** | A contractual commitment to a minimum SLO; violation triggers financial penalties or credits. |
| **Error budget** | The tolerable amount of unreliability within an SLO window: `(1 - SLO) x window`. Spent budget freezes feature releases. |
| **Burn rate** | The rate at which error budget is consumed relative to the steady-state expectation; used for multi-window alerting. |
| **Exemplar** | A `trace_id` attached to a metric sample (histogram bucket), enabling one-click navigation from a metric spike to a representative trace. |
| **Tail-based sampling** | Sampling decision made after the full trace is collected, allowing retention of all error/slow traces regardless of head decision. |
| **Cardinality** | The number of unique time series produced by a metric; high cardinality (e.g., per-user labels) degrades storage and query performance. |
| **Recording rule** | A Prometheus rule that pre-aggregates a frequently-evaluated PromQL expression into a new time series, reducing dashboard query cost. |
| **Golden Signals** | Google SRE's four key indicators: latency, traffic, errors, and saturation — the minimum dashboard for any service. |
