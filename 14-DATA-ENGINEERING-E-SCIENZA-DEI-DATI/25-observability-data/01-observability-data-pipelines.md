# Observability for Data Systems and Pipelines

## Table of Contents

1. [Observability Fundamentals](#1-observability-fundamentals)
2. [Metrics for Data Infrastructure](#2-metrics-for-data-infrastructure)
3. [Logging for Data Systems](#3-logging-for-data-systems)
4. [Distributed Tracing for Data Pipelines](#4-distributed-tracing-for-data-pipelines)
5. [Data Observability Platforms](#5-data-observability-platforms)
6. [Alerting Strategy](#6-alerting-strategy)
7. [Dashboards and Visualization](#7-dashboards-and-visualization)
8. [Cost Observability](#8-cost-observability)
9. [Incident Management for Data](#9-incident-management-for-data)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Observability Fundamentals

### Three Pillars Applied to Data Systems

Traditional software observability rests on three pillars: **metrics**, **logs**, and **traces**. When applied to data systems, each pillar acquires domain-specific semantics that extend well beyond application-level concerns.

**Metrics** in data systems measure pipeline throughput, record counts, transformation latency, data freshness, and infrastructure utilization. Unlike request-response systems where latency percentiles dominate, data metrics track batch completion times, streaming lag, and warehouse slot utilization.

**Logs** capture the narrative of data movement — which records were filtered, why a transformation failed, what schema change was detected. Structured logging with correlation IDs enables following a single record (or batch) across ingestion, transformation, and serving layers.

**Traces** provide end-to-end visibility across distributed pipeline stages. A trace might span from a Kafka producer in a microservice through a Flink transformation, into a data warehouse load, and finally to a dashboard refresh. This cross-system span is fundamentally different from tracing a single HTTP request through service meshes.

### Observability vs Monitoring

Monitoring answers predetermined questions: "Is the pipeline running?" "Did the DAG complete?" Observability enables asking arbitrary questions of a system without deploying new instrumentation. The distinction matters critically for data teams because data failures are often novel — a schema drift in an upstream API, a subtle distribution shift in a feature column, a timezone edge case that surfaces only on DST transitions.

A monitored data pipeline tells you it failed. An observable data pipeline tells you *why* it failed, which records were affected, which downstream consumers are impacted, and whether this pattern matches previous incidents.

### Data-Specific Observability Signals

Beyond the three pillars, data systems require domain-specific signals that have no analog in application monitoring:

**Freshness** — How stale is the data? The time delta between the most recent record's event timestamp and the current wall clock. Critical for real-time dashboards and ML feature stores.

**Volume** — Is the expected amount of data arriving? Volume anomalies (both drops and spikes) indicate upstream issues, schema changes, or ingestion failures. Track row counts, byte sizes, and partition counts.

**Schema** — Has the structure of the data changed? Schema drift detection catches added/removed columns, type changes, and nullable-to-required transitions before they break downstream consumers.

**Distribution** — Are the statistical properties of the data stable? Column-level distribution monitoring catches data quality issues invisible to schema or volume checks: a sudden shift in the mean of a price column, unexpected NULL rates, or a category value that stops appearing.

**Lineage** — Can you trace data from source to consumption? Lineage observability tracks dependencies, enabling impact analysis when issues are detected. If a source table is late, lineage tells you which reports, models, and dashboards are affected.

### SLIs, SLOs, and SLAs for Data

**Service Level Indicators (SLIs)** for data systems:

| SLI | Definition | Measurement |
|-----|-----------|-------------|
| Freshness | Time since last successful load | `now() - max(event_timestamp)` |
| Completeness | Percentage of expected records present | `actual_count / expected_count * 100` |
| Accuracy | Percentage of records passing quality rules | `valid_records / total_records * 100` |
| Availability | Percentage of time data is queryable | `uptime / total_time * 100` |
| Latency | End-to-end pipeline processing time | `load_complete_ts - event_ts` |

**Service Level Objectives (SLOs)** set targets:

```yaml
# data-slos.yaml
slos:
  - name: orders_freshness
    sli: freshness
    target: 99.5%
    threshold: 15m
    description: "Orders data is no more than 15 minutes stale 99.5% of the time"

  - name: user_events_completeness
    sli: completeness
    target: 99.9%
    threshold: 0.1%  # max 0.1% record loss
    description: "User events pipeline loses fewer than 0.1% of records"

  - name: ml_features_latency
    sli: latency
    target: 99%
    threshold: 5m
    description: "ML feature computations complete within 5 minutes of event time"
```

**Service Level Agreements (SLAs)** are contractual — the business impact when SLOs are breached. For data teams, SLAs typically manifest as: "If the executive dashboard is stale by more than 1 hour, the data team is paged with P1 severity."

---

## 2. Metrics for Data Infrastructure

### Database Metrics

#### Connection Pool Metrics

```python
# Prometheus metrics for connection pool monitoring
from prometheus_client import Gauge, Histogram, Counter

db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections',
    ['database', 'pool_name']
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Number of idle connections in pool',
    ['database', 'pool_name']
)

db_connections_waiting = Gauge(
    'db_connections_waiting',
    'Number of threads waiting for a connection',
    ['database', 'pool_name']
)

db_connection_acquire_duration = Histogram(
    'db_connection_acquire_seconds',
    'Time to acquire a connection from pool',
    ['database', 'pool_name'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)
```

#### Query Latency

Track query latency by operation type, table, and query pattern:

```python
query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query execution time',
    ['database', 'operation', 'table', 'query_hash'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

query_rows_returned = Histogram(
    'db_query_rows_returned',
    'Number of rows returned by queries',
    ['database', 'operation', 'table'],
    buckets=[1, 10, 100, 1000, 10000, 100000, 1000000]
)
```

#### Cache Hit Ratio

```python
cache_hits = Counter(
    'db_cache_hits_total',
    'Database buffer cache hits',
    ['database', 'cache_type']
)

cache_misses = Counter(
    'db_cache_misses_total',
    'Database buffer cache misses',
    ['database', 'cache_type']
)

# PostgreSQL-specific: query pg_stat_bgwriter
# cache_hit_ratio = shared_blks_hit / (shared_blks_hit + shared_blks_read)
```

#### Replication Lag

```python
replication_lag_seconds = Gauge(
    'db_replication_lag_seconds',
    'Replication lag between primary and replica',
    ['database', 'replica_name']
)

replication_lag_bytes = Gauge(
    'db_replication_lag_bytes',
    'Replication lag in bytes (WAL position difference)',
    ['database', 'replica_name']
)
```

#### Lock Contention and Deadlocks

```python
lock_wait_count = Counter(
    'db_lock_waits_total',
    'Number of times queries waited for locks',
    ['database', 'lock_type']
)

deadlock_count = Counter(
    'db_deadlocks_total',
    'Number of deadlocks detected',
    ['database']
)

lock_wait_duration = Histogram(
    'db_lock_wait_seconds',
    'Time spent waiting for locks',
    ['database', 'lock_type'],
    buckets=[0.01, 0.1, 1.0, 5.0, 30.0, 60.0, 300.0]
)
```

### Pipeline Metrics

#### Task Duration and Success Rate

```python
pipeline_task_duration = Histogram(
    'pipeline_task_duration_seconds',
    'Duration of pipeline task execution',
    ['dag_id', 'task_id', 'execution_date'],
    buckets=[10, 30, 60, 120, 300, 600, 1800, 3600, 7200]
)

pipeline_task_status = Counter(
    'pipeline_task_completions_total',
    'Pipeline task completions by status',
    ['dag_id', 'task_id', 'status']  # status: success, failed, skipped, upstream_failed
)

pipeline_dag_duration = Histogram(
    'pipeline_dag_duration_seconds',
    'Total DAG execution time',
    ['dag_id'],
    buckets=[60, 300, 600, 1800, 3600, 7200, 14400, 28800]
)
```

#### Data Volume Processed

```python
pipeline_records_processed = Counter(
    'pipeline_records_processed_total',
    'Number of records processed by pipeline stage',
    ['pipeline', 'stage', 'source']
)

pipeline_bytes_processed = Counter(
    'pipeline_bytes_processed_total',
    'Bytes processed by pipeline stage',
    ['pipeline', 'stage', 'source']
)

pipeline_records_filtered = Counter(
    'pipeline_records_filtered_total',
    'Records filtered/rejected at each stage',
    ['pipeline', 'stage', 'filter_reason']
)
```

#### Streaming Lag

```python
kafka_consumer_lag = Gauge(
    'kafka_consumer_lag_records',
    'Number of records behind latest offset',
    ['consumer_group', 'topic', 'partition']
)

kafka_consumer_lag_seconds = Gauge(
    'kafka_consumer_lag_seconds',
    'Estimated time lag based on consumption rate',
    ['consumer_group', 'topic']
)

streaming_watermark_lag = Gauge(
    'streaming_watermark_lag_seconds',
    'Difference between event time watermark and processing time',
    ['pipeline', 'stage']
)
```

### Infrastructure Metrics for Data Nodes

```yaml
# Prometheus scrape config for data infrastructure
scrape_configs:
  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-primary:9187', 'postgres-replica1:9187']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance

  - job_name: 'kafka-exporter'
    static_configs:
      - targets: ['kafka-exporter:9308']

  - job_name: 'airflow-statsd'
    static_configs:
      - targets: ['statsd-exporter:9102']

  - job_name: 'spark-metrics'
    metrics_path: /metrics/prometheus
    static_configs:
      - targets: ['spark-master:4040']

  - job_name: 'node-exporter'
    static_configs:
      - targets:
          - 'data-node-01:9100'
          - 'data-node-02:9100'
          - 'data-node-03:9100'
```

Key infrastructure metrics for data nodes:

| Resource | Metric | Alert Threshold | Rationale |
|----------|--------|----------------|-----------|
| CPU | `node_cpu_seconds_total` | >85% sustained 5m | Spark/Flink jobs CPU-bound |
| Memory | `node_memory_MemAvailable_bytes` | <15% free | OOM kills corrupt pipelines |
| Disk I/O | `node_disk_io_time_seconds_total` | >90% utilization | Disk-bound queries stall |
| Disk Space | `node_filesystem_avail_bytes` | <20% free | Full disks halt writes |
| Network | `node_network_transmit_bytes_total` | >80% bandwidth | Shuffle/replication bottleneck |

---

## 3. Logging for Data Systems

### Structured Logging in Pipelines

Data pipelines demand structured logging because unstructured text becomes unqueryable at scale. Every log entry should be a machine-parseable JSON document with consistent fields:

```python
import structlog
import uuid
from datetime import datetime, timezone


def configure_pipeline_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(20),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


def get_pipeline_logger(pipeline_name: str, run_id: str = None):
    """Create a logger bound with pipeline context."""
    if run_id is None:
        run_id = str(uuid.uuid4())

    return structlog.get_logger().bind(
        pipeline=pipeline_name,
        run_id=run_id,
        timestamp_utc=datetime.now(timezone.utc).isoformat()
    )


# Usage in pipeline code
logger = get_pipeline_logger("user_events_etl", run_id="run-2026-05-07-001")

logger.info(
    "stage_started",
    stage="transform",
    source_table="raw_events",
    target_table="dim_users",
    expected_records=150000
)

logger.info(
    "stage_completed",
    stage="transform",
    records_in=150000,
    records_out=148523,
    records_filtered=1477,
    duration_seconds=45.2,
    filter_reasons={"null_user_id": 1200, "duplicate": 277}
)

logger.warning(
    "schema_drift_detected",
    stage="ingestion",
    table="raw_events",
    new_columns=["user_preferences_v2"],
    removed_columns=[],
    type_changes={"event_value": "string -> float"}
)
```

### Correlation IDs Across Pipeline Stages

A single pipeline run spans multiple systems. Correlation IDs tie all log entries together:

```python
import contextvars
from functools import wraps

# Context variable for correlation
pipeline_context = contextvars.ContextVar('pipeline_context', default={})


def with_correlation(func):
    """Decorator to propagate correlation context through pipeline stages."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        ctx = pipeline_context.get()
        structlog.contextvars.bind_contextvars(
            correlation_id=ctx.get('correlation_id'),
            dag_run_id=ctx.get('dag_run_id'),
            execution_date=ctx.get('execution_date'),
            upstream_task=ctx.get('upstream_task')
        )
        try:
            return func(*args, **kwargs)
        finally:
            structlog.contextvars.unbind_contextvars(
                'correlation_id', 'dag_run_id',
                'execution_date', 'upstream_task'
            )
    return wrapper


def propagate_to_spark(spark_session, correlation_id: str):
    """Set correlation ID in Spark job for cross-system tracing."""
    spark_session.sparkContext.setLocalProperty(
        "spark.pipeline.correlation_id", correlation_id
    )
```

### Database Logging Best Practices

```yaml
# PostgreSQL logging configuration (postgresql.conf)
log_destination: 'jsonlog'
logging_collector: on
log_directory: '/var/log/postgresql'
log_filename: 'postgresql-%Y-%m-%d.log'
log_rotation_age: 1d
log_rotation_size: 100MB

# Query logging
log_min_duration_statement: 1000  # Log queries slower than 1s
log_statement: 'ddl'              # Log all DDL statements
log_lock_waits: on                # Log lock waits
log_temp_files: 0                 # Log all temp file usage
log_checkpoints: on
log_connections: on
log_disconnections: on

# Auto-explain for slow queries
shared_preload_libraries: 'auto_explain'
auto_explain.log_min_duration: '3s'
auto_explain.log_analyze: on
auto_explain.log_buffers: on
auto_explain.log_format: 'json'
```

### Log Levels for Data Operations

| Level | Data Context | Example |
|-------|-------------|---------|
| DEBUG | Record-level transforms, query plans | "Applied type cast: event_value string→float for record batch 4521" |
| INFO | Stage transitions, batch completions, metrics | "Transform stage completed: 150K records in 45.2s" |
| WARNING | Schema drift, volume anomalies, retries | "Volume 30% below 7-day average for source_api_events" |
| ERROR | Stage failures, data loss, timeout | "Load failed: COPY command timeout after 300s on target_table" |
| CRITICAL | Pipeline halt, data corruption, SLA breach | "SLA BREACH: orders_freshness exceeded 1h threshold" |

### PII Redaction in Logs

Data pipeline logs frequently contain record samples, error payloads, and query results that may include PII:

```python
import re
from typing import Any

PII_PATTERNS = {
    'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'credit_card': re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
    'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
}

PII_FIELDS = {'email', 'phone', 'ssn', 'address', 'name', 'first_name',
              'last_name', 'date_of_birth', 'credit_card', 'password'}


def redact_pii(data: Any, depth: int = 0) -> Any:
    """Recursively redact PII from log payloads."""
    if depth > 10:
        return "[REDACTED: max depth]"

    if isinstance(data, dict):
        return {
            k: "[REDACTED]" if k.lower() in PII_FIELDS else redact_pii(v, depth + 1)
            for k, v in data.items()
        }
    elif isinstance(data, list):
        return [redact_pii(item, depth + 1) for item in data[:5]]  # Sample only
    elif isinstance(data, str):
        result = data
        for pattern_name, pattern in PII_PATTERNS.items():
            result = pattern.sub(f"[REDACTED:{pattern_name}]", result)
        return result
    return data


# Integration with structlog
def pii_redaction_processor(logger, method_name, event_dict):
    """Structlog processor that redacts PII before serialization."""
    for key in list(event_dict.keys()):
        if key in ('record_sample', 'error_payload', 'query_result', 'row_data'):
            event_dict[key] = redact_pii(event_dict[key])
    return event_dict
```

### Log Aggregation

#### Loki Configuration for Data Pipeline Logs

```yaml
# loki-config.yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2026-01-01
      store: boltdb-shipper
      object_store: s3
      schema: v12
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/index
    cache_location: /loki/index_cache
    shared_store: s3
  aws:
    s3: s3://data-pipeline-logs/loki
    region: eu-west-1

limits_config:
  retention_period: 30d
  max_entries_limit_per_query: 5000
  max_query_length: 72h

# Promtail config for pipeline containers
# promtail-config.yaml
scrape_configs:
  - job_name: airflow
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: service
    pipeline_stages:
      - json:
          expressions:
            level: level
            pipeline: pipeline
            run_id: run_id
            stage: stage
      - labels:
          level:
          pipeline:
          stage:
      - timestamp:
          source: timestamp
          format: RFC3339
```

---

## 4. Distributed Tracing for Data Pipelines

### OpenTelemetry for Data Workloads

OpenTelemetry (OTel) provides vendor-neutral instrumentation for data pipelines. The key insight is that a data pipeline "request" is a batch or stream of records flowing through stages, not an HTTP request:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.trace.propagation import set_span_in_context
import opentelemetry.context as otel_context

# Initialize tracer for data pipeline
resource = Resource.create({
    ResourceAttributes.SERVICE_NAME: "data-pipeline-etl",
    ResourceAttributes.SERVICE_VERSION: "2.3.1",
    "pipeline.team": "data-engineering",
    "pipeline.environment": "production",
})

provider = TracerProvider(resource=resource)
exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
provider.add_span_processor(BatchSpanExporter(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("data_pipeline", "2.3.1")


class PipelineTracer:
    """Tracing wrapper for data pipeline stages."""

    def __init__(self, pipeline_name: str, run_id: str):
        self.pipeline_name = pipeline_name
        self.run_id = run_id
        self.root_span = None
        self.root_context = None

    def start_pipeline_trace(self):
        """Create the root span for an entire pipeline run."""
        self.root_span = tracer.start_span(
            name=f"pipeline.{self.pipeline_name}",
            attributes={
                "pipeline.name": self.pipeline_name,
                "pipeline.run_id": self.run_id,
                "pipeline.start_time": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.root_context = set_span_in_context(self.root_span)
        return self.root_context

    def trace_stage(self, stage_name: str):
        """Context manager for tracing a pipeline stage."""
        return tracer.start_as_current_span(
            name=f"stage.{stage_name}",
            context=self.root_context,
            attributes={
                "stage.name": stage_name,
                "pipeline.name": self.pipeline_name,
                "pipeline.run_id": self.run_id,
            }
        )

    def end_pipeline_trace(self, status: str = "success"):
        """End the root pipeline span."""
        if self.root_span:
            self.root_span.set_attribute("pipeline.status", status)
            self.root_span.end()


# Usage
pipeline_tracer = PipelineTracer("user_events_etl", "run-2026-05-07-001")
ctx = pipeline_tracer.start_pipeline_trace()

with pipeline_tracer.trace_stage("extract") as span:
    span.set_attribute("extract.source", "kafka://events-topic")
    span.set_attribute("extract.records_read", 250000)
    span.set_attribute("extract.duration_ms", 3200)
    # ... extraction logic ...

with pipeline_tracer.trace_stage("transform") as span:
    span.set_attribute("transform.records_in", 250000)
    span.set_attribute("transform.records_out", 248500)
    span.set_attribute("transform.records_filtered", 1500)
    # ... transformation logic ...

with pipeline_tracer.trace_stage("load") as span:
    span.set_attribute("load.target", "warehouse.dim_users")
    span.set_attribute("load.records_loaded", 248500)
    span.set_attribute("load.method", "COPY")
    # ... load logic ...

pipeline_tracer.end_pipeline_trace("success")
```

### Trace Context Propagation in Kafka

Kafka messages carry trace context in headers, enabling end-to-end tracing from producer through consumer pipelines:

```python
from opentelemetry.propagators.textmap import CarrierT
from opentelemetry.context.context import Context
from opentelemetry import propagate
from confluent_kafka import Producer, Consumer


class KafkaHeaderCarrier:
    """Carrier that reads/writes trace context from/to Kafka headers."""

    def __init__(self, headers: list = None):
        self._headers = dict(headers) if headers else {}

    def get(self, key: str) -> str:
        value = self._headers.get(key)
        if isinstance(value, bytes):
            return value.decode('utf-8')
        return value

    def set(self, key: str, value: str):
        self._headers[key] = value.encode('utf-8')

    def keys(self) -> list:
        return list(self._headers.keys())

    def to_kafka_headers(self) -> list:
        return [(k, v if isinstance(v, bytes) else v.encode('utf-8'))
                for k, v in self._headers.items()]


def produce_with_trace(producer: Producer, topic: str, value: bytes, key: bytes = None):
    """Produce a Kafka message with trace context injected into headers."""
    carrier = KafkaHeaderCarrier()
    propagate.inject(carrier)

    producer.produce(
        topic=topic,
        value=value,
        key=key,
        headers=carrier.to_kafka_headers()
    )


def consume_with_trace(message) -> Context:
    """Extract trace context from consumed Kafka message headers."""
    headers = message.headers() or []
    carrier = KafkaHeaderCarrier(headers)
    ctx = propagate.extract(carrier)
    return ctx
```

### Tracing in Airflow DAGs

```python
from airflow.decorators import dag, task
from opentelemetry import trace

tracer = trace.get_tracer("airflow_dag")


@dag(schedule="@hourly", catchup=False)
def user_events_pipeline():

    @task
    def extract_from_kafka():
        with tracer.start_as_current_span("airflow.extract_from_kafka") as span:
            span.set_attribute("airflow.dag_id", "user_events_pipeline")
            span.set_attribute("airflow.task_id", "extract_from_kafka")
            # Extract logic
            records = consume_kafka_batch("user-events", batch_size=100000)
            span.set_attribute("extract.record_count", len(records))
            return records

    @task
    def transform_events(raw_records):
        with tracer.start_as_current_span("airflow.transform_events") as span:
            span.set_attribute("transform.input_records", len(raw_records))
            # Transform logic
            transformed = apply_transformations(raw_records)
            span.set_attribute("transform.output_records", len(transformed))
            return transformed

    @task
    def load_to_warehouse(transformed_records):
        with tracer.start_as_current_span("airflow.load_to_warehouse") as span:
            span.set_attribute("load.target_table", "analytics.user_events")
            span.set_attribute("load.record_count", len(transformed_records))
            # Load logic
            load_result = bulk_insert(transformed_records, "analytics.user_events")
            span.set_attribute("load.status", load_result.status)

    raw = extract_from_kafka()
    transformed = transform_events(raw)
    load_to_warehouse(transformed)


user_events_pipeline()
```

### OpenTelemetry Collector Configuration

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

  # Kafka metrics receiver
  kafkametrics:
    brokers:
      - kafka-broker-1:9092
      - kafka-broker-2:9092
    protocol_version: 2.8.0
    scrapers:
      - brokers
      - topics
      - consumers
    collection_interval: 30s

  # PostgreSQL receiver
  postgresql:
    endpoint: postgres-primary:5432
    transport: tcp
    username: ${POSTGRES_MONITOR_USER}
    password: ${POSTGRES_MONITOR_PASSWORD}
    databases:
      - analytics
      - warehouse
    collection_interval: 30s

processors:
  batch:
    timeout: 5s
    send_batch_size: 1024

  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128

  attributes:
    actions:
      - key: environment
        value: production
        action: upsert
      - key: team
        value: data-engineering
        action: upsert

  # Filter out noisy health-check spans
  filter:
    spans:
      exclude:
        match_type: strict
        span_names:
          - "health_check"
          - "readiness_probe"

exporters:
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: true

  prometheus:
    endpoint: 0.0.0.0:8889
    namespace: data_pipeline

  loki:
    endpoint: http://loki:3100/loki/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, filter, attributes]
      exporters: [otlp/tempo]
    metrics:
      receivers: [otlp, kafkametrics, postgresql]
      processors: [memory_limiter, batch, attributes]
      exporters: [prometheus]
```

### Trace-Based Debugging of Slow Pipelines

When a pipeline SLO is breached, traces reveal the bottleneck without guesswork:

1. **Query Tempo/Jaeger** for pipeline traces exceeding duration threshold
2. **Identify the slow span** — which stage consumed the most wall-clock time?
3. **Examine span attributes** — record counts, query plans, resource usage
4. **Follow span links** — cross-service dependencies (e.g., a slow Kafka consumer causing downstream starvation)
5. **Compare with baseline** — find a normal-duration trace for the same pipeline, diff span durations

```python
# Programmatic trace analysis for SLO breach investigation
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from datetime import timedelta


def analyze_slow_pipeline_traces(tempo_client, pipeline_name: str, threshold_seconds: float):
    """Find and analyze traces that exceeded duration SLO."""
    query = f'{{resource.pipeline.name="{pipeline_name}"}} | duration > {threshold_seconds}s'
    slow_traces = tempo_client.search(query, limit=50)

    bottleneck_analysis = {}
    for t in slow_traces:
        for span in t.spans:
            stage = span.attributes.get("stage.name", "unknown")
            duration = span.duration_ms
            if stage not in bottleneck_analysis:
                bottleneck_analysis[stage] = []
            bottleneck_analysis[stage].append(duration)

    # Report: which stage is the most frequent bottleneck?
    for stage, durations in sorted(
        bottleneck_analysis.items(), key=lambda x: max(x[1]), reverse=True
    ):
        avg_ms = sum(durations) / len(durations)
        max_ms = max(durations)
        print(f"Stage: {stage} | Avg: {avg_ms:.0f}ms | Max: {max_ms:.0f}ms | Count: {len(durations)}")
```

---

## 5. Data Observability Platforms

### Platform Comparison Matrix

| Platform | Type | Approach | Strengths | Weaknesses |
|----------|------|----------|-----------|------------|
| **Monte Carlo** | Commercial | Automated ML-based anomaly detection | Zero-config monitoring, deep warehouse integration, incident management | Expensive, vendor lock-in to supported warehouses |
| **Elementary** | Open Source | dbt-native data observability | Tight dbt integration, free, column-level monitoring | Requires dbt, limited to dbt-accessible data |
| **Bigeye** | Commercial | Rule + ML hybrid monitoring | Flexible rules, auto-thresholds, good UI | Cost scales with monitored tables |
| **Metaplane** | Commercial | Automated anomaly detection | Easy setup, Slack-native alerts, good for small teams | Less customizable than alternatives |
| **Datafold** | Commercial | Data diff and regression testing | CI/CD integration, PR-level data diffs | Focused on deployment, less runtime monitoring |
| **Great Expectations** | Open Source | Declarative data validation | Highly customizable, no vendor lock-in, large community | Not real-time, requires explicit rule definition |
| **OpenLineage + Marquez** | Open Source | Lineage-first observability | Standard lineage protocol, vendor-neutral | Requires integration effort, no built-in anomaly detection |

### Open-Source Stack: OpenLineage + Custom Metrics

```python
# OpenLineage integration for custom pipeline observability
from openlineage.client import OpenLineageClient
from openlineage.client.run import RunEvent, RunState, Run, Job
from openlineage.client.facet import (
    DataQualityMetricsInputDatasetFacet,
    ColumnMetric,
    OutputStatisticsOutputDatasetFacet,
)
from openlineage.client.uuid import generate_new_uuid
from datetime import datetime, timezone

client = OpenLineageClient(url="http://marquez:5000")

NAMESPACE = "data_engineering"


def emit_pipeline_lineage(
    job_name: str,
    run_id: str,
    state: RunState,
    inputs: list,
    outputs: list,
    quality_metrics: dict = None
):
    """Emit lineage event with data quality facets."""
    run = Run(runId=run_id)
    job = Job(namespace=NAMESPACE, name=job_name)

    input_datasets = []
    for inp in inputs:
        facets = {}
        if quality_metrics and inp['name'] in quality_metrics:
            metrics = quality_metrics[inp['name']]
            facets['dataQualityMetrics'] = DataQualityMetricsInputDatasetFacet(
                rowCount=metrics.get('row_count'),
                bytes=metrics.get('bytes'),
                columnMetrics={
                    col: ColumnMetric(
                        nullCount=m.get('null_count'),
                        distinctCount=m.get('distinct_count'),
                        min=m.get('min'),
                        max=m.get('max'),
                    )
                    for col, m in metrics.get('columns', {}).items()
                }
            )
        input_datasets.append({
            'namespace': NAMESPACE,
            'name': inp['name'],
            'facets': facets,
        })

    event = RunEvent(
        eventType=state,
        eventTime=datetime.now(timezone.utc).isoformat(),
        run=run,
        job=job,
        inputs=input_datasets,
        outputs=outputs,
    )
    client.emit(event)
```

### Build vs Buy Decision Framework

**Build (Open Source) when:**
- Budget is constrained but engineering capacity exists
- Data stack is heterogeneous (not purely dbt + one warehouse)
- You need deep customization of detection logic
- Regulatory constraints prevent sending metadata to third parties
- Team has observability engineering expertise

**Buy (Commercial Platform) when:**
- Time-to-value matters more than cost
- Team is small and cannot maintain observability infrastructure
- ML-based anomaly detection provides more value than rule-based
- Vendor supports your specific warehouse and orchestrator natively
- Executive reporting and incident management are immediate needs

**Hybrid approach (common in practice):**
- Use Great Expectations or Elementary for known-rule validation (schema, constraints)
- Deploy OpenTelemetry + Prometheus + Grafana for infrastructure metrics
- Consider a commercial platform for automated anomaly detection on top
- Use OpenLineage for lineage regardless of monitoring choice

---

## 6. Alerting Strategy

### Alert Fatigue Prevention

Alert fatigue is the primary failure mode of data observability. A team that ignores alerts is worse off than one with no alerts. Principles:

1. **Every alert must be actionable.** If there's nothing to do, it's a log entry, not an alert.
2. **Every alert must have an owner.** Unowned alerts decay into noise.
3. **Alert on symptoms, not causes.** Alert on "data freshness SLO breached," not "Kafka consumer rebalancing."
4. **Use severity levels honestly.** If everything is P1, nothing is.
5. **Review alert volume monthly.** Alerts that fire >5x/week without action should be tuned or removed.

### Severity Levels for Data Issues

```yaml
# alert-severity-policy.yaml
severity_levels:
  P1_critical:
    description: "Business-critical data unavailable or corrupted"
    examples:
      - "Revenue reporting data stale >2 hours"
      - "Production ML model serving stale features"
      - "Customer-facing dashboards showing incorrect data"
    response_time: 15 minutes
    escalation: immediate page to on-call
    notification: PagerDuty + Slack #data-incidents + stakeholder email

  P2_high:
    description: "Data quality degraded, SLO breached but not customer-facing"
    examples:
      - "Pipeline failed, retry budget exhausted"
      - "Data freshness SLO breached for internal analytics"
      - "Schema change detected in upstream source"
    response_time: 1 hour
    escalation: page after 30 min if unacknowledged
    notification: PagerDuty + Slack #data-alerts

  P3_medium:
    description: "Anomaly detected, may require investigation"
    examples:
      - "Volume 40% below daily average"
      - "New NULL pattern in non-nullable column"
      - "Pipeline duration 2x normal"
    response_time: 4 hours (business hours)
    escalation: Slack mention after 4 hours
    notification: Slack #data-alerts

  P4_low:
    description: "Informational, track for patterns"
    examples:
      - "Pipeline duration trending upward over 7 days"
      - "Disk usage approaching threshold"
      - "New column detected in source"
    response_time: Next business day
    escalation: none
    notification: Slack #data-info (daily digest)
```

### Alerting Rules in Prometheus

```yaml
# data-pipeline-alerts.yaml
groups:
  - name: data_freshness
    rules:
      - alert: DataFreshnessSLOBreach
        expr: |
          (time() - data_last_successful_load_timestamp{}) > on(pipeline)
          group_left data_freshness_slo_threshold_seconds{}
        for: 5m
        labels:
          severity: critical
          team: data-engineering
        annotations:
          summary: "Data freshness SLO breached for {{ $labels.pipeline }}"
          description: |
            Pipeline {{ $labels.pipeline }} data is {{ $value | humanizeDuration }}
            stale. SLO threshold is {{ $labels.threshold }}.
          runbook_url: "https://runbooks.internal/data/freshness-breach"
          dashboard: "https://grafana.internal/d/pipeline-health"

      - alert: DataVolumeAnomaly
        expr: |
          abs(
            pipeline_records_processed_total - pipeline_records_expected_total
          ) / pipeline_records_expected_total > 0.3
        for: 10m
        labels:
          severity: high
          team: data-engineering
        annotations:
          summary: "Volume anomaly detected for {{ $labels.pipeline }}"
          description: |
            Pipeline {{ $labels.pipeline }} processed {{ $value | humanize }}%
            different from expected volume.

  - name: pipeline_health
    rules:
      - alert: PipelineConsecutiveFailures
        expr: pipeline_consecutive_failures > 3
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "Pipeline {{ $labels.dag_id }} failed {{ $value }} consecutive times"
          runbook_url: "https://runbooks.internal/data/pipeline-failure"

      - alert: PipelineDurationAnomaly
        expr: |
          pipeline_dag_duration_seconds{quantile="0.95"}
          > 2 * avg_over_time(pipeline_dag_duration_seconds{quantile="0.95"}[7d])
        for: 5m
        labels:
          severity: medium
        annotations:
          summary: "Pipeline {{ $labels.dag_id }} running 2x slower than 7-day average"

  - name: kafka_consumer
    rules:
      - alert: KafkaConsumerLagCritical
        expr: kafka_consumer_lag_records > 1000000
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Kafka consumer lag > 1M records for {{ $labels.consumer_group }}"

      - alert: KafkaConsumerLagGrowing
        expr: |
          rate(kafka_consumer_lag_records[10m]) > 0
          and kafka_consumer_lag_records > 100000
        for: 15m
        labels:
          severity: high
        annotations:
          summary: "Kafka consumer lag growing for {{ $labels.consumer_group }}"
```

### Runbook-Linked Alerts

Every alert must link to a runbook that describes:

```markdown
# Runbook: Data Freshness SLO Breach

## Alert: DataFreshnessSLOBreach

### Diagnosis Steps

1. Check pipeline status in Airflow UI:
   `https://airflow.internal/dags/{dag_id}/grid`

2. Check for upstream source availability:
   ```sql
   SELECT MAX(ingested_at) FROM raw_layer.{source_table};
   ```

3. Check Kafka consumer lag (if streaming):
   ```bash
   kafka-consumer-groups --bootstrap-server kafka:9092 \
     --group {consumer_group} --describe
   ```

4. Check infrastructure (disk, memory, connections):
   Dashboard: https://grafana.internal/d/data-infra

### Resolution Steps

- If pipeline task failed: Check task logs, fix, trigger manual rerun
- If source is delayed: Contact source team, update stakeholders
- If infrastructure issue: Scale resources or failover
- If Kafka lag: Check consumer health, consider adding partitions/consumers

### Escalation

- If not resolved within 30 minutes: Page secondary on-call
- If customer-facing: Notify #data-incidents, update status page
```

### Business-Impact-Based Prioritization

Not all data is equal. Prioritize alerts by downstream business impact:

```python
# Alert priority matrix based on downstream consumers
PIPELINE_BUSINESS_IMPACT = {
    "revenue_reporting": {
        "severity_multiplier": 2.0,
        "stakeholders": ["finance_team", "cfo_office"],
        "sla_minutes": 60,
        "revenue_impact": True,
    },
    "ml_feature_store": {
        "severity_multiplier": 1.8,
        "stakeholders": ["ml_team", "product"],
        "sla_minutes": 30,
        "customer_facing": True,
    },
    "internal_analytics": {
        "severity_multiplier": 1.0,
        "stakeholders": ["analytics_team"],
        "sla_minutes": 240,
        "revenue_impact": False,
    },
    "experimental_pipeline": {
        "severity_multiplier": 0.5,
        "stakeholders": ["data_science"],
        "sla_minutes": 1440,  # 24 hours
        "revenue_impact": False,
    },
}
```

---

## 7. Dashboards and Visualization

### Grafana Dashboard Architecture

Organize dashboards in a hierarchy:

```
Data Platform Dashboards/
├── Executive Overview        (business stakeholders)
├── Pipeline Health           (data engineering daily)
├── Data Quality              (data engineering + analytics)
├── Infrastructure            (platform/SRE team)
├── Cost Management           (engineering leadership)
├── SLA Compliance            (data engineering + business)
└── Per-Pipeline Detail/      (deep-dive troubleshooting)
    ├── user_events_etl
    ├── revenue_reporting
    └── ml_feature_pipeline
```

### Pipeline Health Dashboard

```json
{
  "dashboard": {
    "title": "Data Pipeline Health",
    "uid": "pipeline-health-v2",
    "tags": ["data-engineering", "pipelines"],
    "timezone": "utc",
    "refresh": "1m",
    "panels": [
      {
        "title": "Pipeline SLO Compliance (24h)",
        "type": "stat",
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "avg(data_pipeline_slo_compliance{window=\"24h\"}) * 100",
            "legendFormat": "SLO Compliance %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "orange", "value": 95},
                {"color": "green", "value": 99}
              ]
            },
            "unit": "percent"
          }
        }
      },
      {
        "title": "Active Pipeline Failures",
        "type": "stat",
        "gridPos": {"h": 4, "w": 3, "x": 6, "y": 0},
        "targets": [
          {
            "expr": "count(pipeline_task_status{status=\"failed\"} unless on(dag_id, task_id) pipeline_task_status{status=\"success\"})"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"color": "green", "value": 0},
                {"color": "orange", "value": 1},
                {"color": "red", "value": 3}
              ]
            }
          }
        }
      },
      {
        "title": "Data Freshness by Pipeline",
        "type": "table",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
        "targets": [
          {
            "expr": "time() - data_last_successful_load_timestamp",
            "format": "table",
            "instant": true
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "renameByName": {
                "Value": "Staleness",
                "pipeline": "Pipeline"
              }
            }
          }
        ]
      },
      {
        "title": "Pipeline Duration Trend (7d)",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
        "targets": [
          {
            "expr": "pipeline_dag_duration_seconds{quantile=\"0.95\"}",
            "legendFormat": "{{ dag_id }} (p95)"
          }
        ]
      },
      {
        "title": "Records Processed (24h)",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 12},
        "targets": [
          {
            "expr": "sum by (pipeline) (increase(pipeline_records_processed_total[1h]))",
            "legendFormat": "{{ pipeline }}"
          }
        ]
      },
      {
        "title": "Kafka Consumer Lag",
        "type": "timeseries",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 12},
        "targets": [
          {
            "expr": "sum by (consumer_group) (kafka_consumer_lag_records)",
            "legendFormat": "{{ consumer_group }}"
          }
        ]
      }
    ]
  }
}
```

### Executive Dashboard vs Engineering Dashboard

**Executive Dashboard** shows:
- SLA compliance percentage (green/red)
- Number of active data incidents
- Data freshness status for key business reports
- Cost trends (month-over-month)
- Data quality score (composite metric)

**Engineering Dashboard** shows:
- Individual pipeline task durations
- Error rates by task and error type
- Infrastructure utilization per data node
- Kafka lag per consumer group per partition
- Query latency percentiles for the warehouse
- Replication lag for database replicas

The key difference: executives need binary "healthy/unhealthy" signals with trend context. Engineers need granular metrics for root cause analysis.

### Real-Time vs Historical Views

```yaml
# Grafana dashboard time range strategy
real_time_panels:
  refresh: 10s-1m
  time_range: "now-1h to now"
  use_cases:
    - Streaming pipeline lag
    - Active incident monitoring
    - Live infrastructure metrics

historical_panels:
  refresh: 5m-1h
  time_range: "now-7d to now" or "now-30d to now"
  use_cases:
    - Pipeline duration trends
    - Volume patterns (daily/weekly cycles)
    - SLO compliance over reporting period
    - Cost trends
    - Capacity planning
```

---

## 8. Cost Observability

### Data Processing Cost Tracking

#### BigQuery Cost Attribution

```python
from google.cloud import bigquery
from prometheus_client import Gauge, Counter

bq_query_cost = Counter(
    'bigquery_query_cost_usd_total',
    'Total cost of BigQuery queries',
    ['project', 'dataset', 'user', 'pipeline', 'query_type']
)

bq_bytes_billed = Counter(
    'bigquery_bytes_billed_total',
    'Total bytes billed by BigQuery',
    ['project', 'dataset', 'pipeline']
)

bq_slot_ms_consumed = Counter(
    'bigquery_slot_ms_total',
    'Total slot-milliseconds consumed',
    ['project', 'reservation', 'pipeline']
)


def track_bigquery_costs(client: bigquery.Client, project_id: str):
    """Query INFORMATION_SCHEMA for recent job costs."""
    query = f"""
    SELECT
        user_email,
        COALESCE(labels.value, 'unattributed') as pipeline,
        statement_type as query_type,
        SUM(total_bytes_billed) as bytes_billed,
        SUM(total_slot_ms) as slot_ms,
        SUM(total_bytes_billed) / POW(1024, 4) * 6.25 as estimated_cost_usd
    FROM `{project_id}.region-us.INFORMATION_SCHEMA.JOBS`
    LEFT JOIN UNNEST(labels) labels ON labels.key = 'pipeline_name'
    WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        AND state = 'DONE'
    GROUP BY user_email, pipeline, query_type
    """
    results = client.query(query).result()
    for row in results:
        bq_query_cost.labels(
            project=project_id,
            dataset='all',
            user=row.user_email,
            pipeline=row.pipeline,
            query_type=row.query_type
        ).inc(row.estimated_cost_usd)

        bq_bytes_billed.labels(
            project=project_id,
            dataset='all',
            pipeline=row.pipeline
        ).inc(row.bytes_billed)
```

#### Snowflake Cost Tracking

```sql
-- Snowflake: credit consumption by pipeline/warehouse
CREATE OR REPLACE VIEW observability.cost_attribution AS
SELECT
    warehouse_name,
    query_tag AS pipeline_name,
    DATE_TRUNC('hour', start_time) AS hour,
    COUNT(*) AS query_count,
    SUM(credits_used_cloud_services) AS cloud_credits,
    SUM(credits_used_compute) AS compute_credits,
    SUM(credits_used_compute + credits_used_cloud_services) AS total_credits,
    SUM(credits_used_compute + credits_used_cloud_services) * 3.00 AS estimated_cost_usd
FROM snowflake.account_usage.query_history
WHERE start_time > DATEADD('hour', -24, CURRENT_TIMESTAMP())
GROUP BY warehouse_name, query_tag, DATE_TRUNC('hour', start_time);
```

#### Spark Cost Estimation

```python
from prometheus_client import Gauge, Histogram

spark_job_cost = Histogram(
    'spark_job_estimated_cost_usd',
    'Estimated cost of Spark job execution',
    ['application', 'pipeline', 'cluster_type'],
    buckets=[0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 50.0, 100.0]
)


def estimate_spark_cost(
    executor_hours: float,
    driver_hours: float,
    instance_type: str,
    pricing: dict
) -> float:
    """Estimate Spark job cost based on resource consumption."""
    executor_cost = executor_hours * pricing[instance_type]['per_hour']
    driver_cost = driver_hours * pricing['driver']['per_hour']
    storage_cost = 0  # Add if using spot with EBS
    return executor_cost + driver_cost + storage_cost
```

### Cost Attribution to Pipelines and Teams

```yaml
# cost-attribution-config.yaml
attribution_rules:
  # Tag-based attribution (primary)
  - source: resource_tags
    tag_key: "pipeline_name"
    fallback: "unattributed"

  # Query-based attribution for warehouses
  - source: query_metadata
    fields: ["query_tag", "user_email", "warehouse_name"]
    mapping:
      warehouse_name:
        "ETL_WH_LARGE": {team: "data-engineering", category: "etl"}
        "ANALYTICS_WH": {team: "analytics", category: "adhoc"}
        "ML_WH": {team: "ml-engineering", category: "training"}

  # Storage attribution
  - source: storage_metadata
    fields: ["database", "schema", "table"]
    mapping_table: "observability.storage_ownership"

cost_centers:
  data-engineering:
    budget_monthly_usd: 15000
    alert_threshold_percent: 80
    escalation: "data-eng-lead"

  analytics:
    budget_monthly_usd: 8000
    alert_threshold_percent: 90
    escalation: "analytics-lead"

  ml-engineering:
    budget_monthly_usd: 25000
    alert_threshold_percent: 75
    escalation: "ml-lead"
```

### Unit Economics for Data

Track cost efficiency with unit metrics:

```python
# Unit economics metrics
cost_per_gb_processed = Gauge(
    'data_cost_per_gb_processed',
    'Cost per gigabyte of data processed',
    ['pipeline', 'stage']
)

cost_per_record = Gauge(
    'data_cost_per_million_records',
    'Cost per million records processed',
    ['pipeline']
)

cost_per_query = Histogram(
    'data_cost_per_query_usd',
    'Cost per warehouse query',
    ['warehouse', 'query_type', 'team'],
    buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 50.0]
)

# Calculate unit economics
def compute_unit_economics(
    total_cost: float,
    gb_processed: float,
    records_processed: int,
    queries_executed: int
) -> dict:
    return {
        "cost_per_gb": total_cost / max(gb_processed, 0.001),
        "cost_per_million_records": (total_cost / max(records_processed, 1)) * 1_000_000,
        "cost_per_query": total_cost / max(queries_executed, 1),
    }
```

### Budget Alerts

```yaml
# Prometheus alert rules for cost
groups:
  - name: cost_alerts
    rules:
      - alert: DailyBudgetExceeded
        expr: |
          sum by (team) (
            increase(bigquery_query_cost_usd_total[24h])
          ) > on(team) group_left cost_budget_daily_usd
        labels:
          severity: high
        annotations:
          summary: "Team {{ $labels.team }} exceeded daily budget"
          description: |
            Spent ${{ $value | printf \"%.2f\" }} against daily budget of
            ${{ with query (printf `cost_budget_daily_usd{team=\"%s\"}` $labels.team) }}{{ . | first | value }}{{ end }}

      - alert: CostSpike
        expr: |
          sum by (pipeline) (rate(bigquery_query_cost_usd_total[1h])) * 24
          > 3 * avg_over_time(
            sum by (pipeline) (rate(bigquery_query_cost_usd_total[1h]))[7d:1h]
          ) * 24
        for: 30m
        labels:
          severity: medium
        annotations:
          summary: "Cost spike detected for pipeline {{ $labels.pipeline }}"
          description: "Current daily cost rate 3x above 7-day average"

      - alert: MonthlyBudgetProjection
        expr: |
          predict_linear(
            sum by (team) (bigquery_query_cost_usd_total)[7d:1h],
            30*24*3600
          ) > on(team) group_left cost_budget_monthly_usd * 1.1
        labels:
          severity: medium
        annotations:
          summary: "Team {{ $labels.team }} projected to exceed monthly budget by 10%+"
```

---

## 9. Incident Management for Data

### Data Incidents vs Software Incidents

Data incidents differ from software incidents in critical ways:

| Dimension | Software Incident | Data Incident |
|-----------|------------------|---------------|
| Detection | Immediate (errors, crashes) | Delayed (stale data may go unnoticed) |
| Blast radius | Users currently making requests | All consumers of affected data |
| Rollback | Deploy previous version | May require data backfill/correction |
| Impact duration | Until fix deployed | Until data corrected across all consumers |
| Root cause | Code change, infra failure | Upstream changes, schema drift, volume anomalies |
| Resolution | Fix and deploy | Fix, backfill, validate, notify consumers |

### Severity Classification for Data Incidents

```yaml
# data-incident-severity.yaml
P1_critical:
  definition: "Customer-facing data incorrect or unavailable"
  indicators:
    - Revenue/billing data affected
    - Production ML models serving incorrect predictions
    - Regulatory reporting data corrupted
    - Customer-visible dashboards showing wrong numbers
  response:
    acknowledgement: 15 min
    status_update_frequency: 30 min
    resolution_target: 4 hours
    stakeholder_notification: immediate
    war_room: yes

P2_high:
  definition: "Internal business decisions blocked or data SLO breached"
  indicators:
    - Executive dashboards stale >2 hours
    - Internal analytics unavailable for >4 hours
    - Pipeline SLO breached affecting multiple consumers
    - Data quality below threshold for key tables
  response:
    acknowledgement: 30 min
    status_update_frequency: 1 hour
    resolution_target: 8 hours
    stakeholder_notification: within 1 hour
    war_room: case-by-case

P3_medium:
  definition: "Data degradation with workarounds available"
  indicators:
    - Single pipeline failure with manual workaround
    - Non-critical table freshness breach
    - Performance degradation (queries 3x+ slower)
    - Schema drift detected but not yet impacting consumers
  response:
    acknowledgement: 2 hours
    status_update_frequency: 4 hours
    resolution_target: 24 hours
    stakeholder_notification: if requested

P4_low:
  definition: "Minor issue, no business impact"
  indicators:
    - Development/staging environment issues
    - Cosmetic data issues (formatting, display)
    - Single record-level discrepancies
    - Monitoring false positives
  response:
    acknowledgement: next business day
    resolution_target: 1 week
```

### Incident Response Process

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class IncidentSeverity(Enum):
    P1 = "critical"
    P2 = "high"
    P3 = "medium"
    P4 = "low"


class IncidentStatus(Enum):
    DETECTED = "detected"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    POSTMORTEM = "postmortem"


@dataclass
class DataIncident:
    id: str
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    detected_at: datetime
    detected_by: str  # alert name or human
    affected_pipelines: list = field(default_factory=list)
    affected_tables: list = field(default_factory=list)
    downstream_impact: list = field(default_factory=list)
    incident_commander: Optional[str] = None
    timeline: list = field(default_factory=list)
    root_cause: Optional[str] = None
    resolution: Optional[str] = None
    data_impact: Optional[dict] = None  # records affected, time range, etc.

    def acknowledge(self, commander: str):
        self.status = IncidentStatus.ACKNOWLEDGED
        self.incident_commander = commander
        self.timeline.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "acknowledged",
            "actor": commander,
        })

    def assess_blast_radius(self, lineage_client):
        """Use lineage to determine all downstream consumers."""
        all_downstream = set()
        for table in self.affected_tables:
            downstream = lineage_client.get_downstream_consumers(table)
            all_downstream.update(downstream)
        self.downstream_impact = list(all_downstream)
        return self.downstream_impact

    def record_data_impact(self, records_affected: int, time_range_start: str,
                           time_range_end: str, tables_affected: list):
        self.data_impact = {
            "records_affected": records_affected,
            "time_range": {"start": time_range_start, "end": time_range_end},
            "tables_corrupted": tables_affected,
            "backfill_required": records_affected > 0,
        }
```

### Communication Templates

#### Stakeholder Notification (P1/P2)

```markdown
## Data Incident Notification

**Incident:** [INC-2026-0507-001] Revenue Data Freshness Breach
**Severity:** P1 - Critical
**Status:** Investigating
**Started:** 2026-05-07T14:23:00Z
**Incident Commander:** [Name]

### Impact
- Revenue dashboard showing data as of 12:00 UTC (>2 hours stale)
- Downstream consumers affected: finance_daily_report, cfo_dashboard, billing_reconciliation

### Current Actions
- Investigating root cause (upstream API timeout suspected)
- Finance team notified — manual process available as workaround

### Next Update
- Expected within 30 minutes or when status changes

### Status Page
- https://status.internal/data-platform
```

#### Resolution Notification

```markdown
## Data Incident Resolved

**Incident:** [INC-2026-0507-001] Revenue Data Freshness Breach
**Duration:** 2 hours 15 minutes (14:23 - 16:38 UTC)
**Root Cause:** Upstream payment API rate-limited our extraction, causing timeout cascade

### Resolution
- Implemented exponential backoff on payment API extraction
- Backfill completed for 14:00-16:30 UTC window
- All downstream tables refreshed and verified

### Data Impact
- 45,000 revenue records delayed (not lost)
- All data now correct and current
- No financial reporting impact (report deadline is 18:00 UTC)

### Follow-up
- Postmortem scheduled: 2026-05-09 10:00 UTC
- Ticket for permanent fix: DATA-4521
```

### Blameless Postmortem Template

```yaml
# postmortem-template.yaml
incident_id: "INC-2026-0507-001"
title: "Revenue Data Freshness Breach Due to Upstream API Rate Limiting"
date: "2026-05-07"
severity: P1
duration: "2h 15m"
authors: ["incident_commander_name"]
reviewers: ["team_lead", "affected_stakeholder"]

summary: |
  The revenue data pipeline breached its freshness SLO (15 minutes)
  for 2 hours and 15 minutes due to the upstream payment API
  enforcing a new rate limit that our extraction job was not
  configured to handle gracefully.

impact:
  data_affected:
    tables: ["warehouse.revenue_transactions"]
    records: 45000
    time_range: "2026-05-07 14:00 - 16:30 UTC"
  consumers_affected:
    - "finance_daily_report (delayed 2h)"
    - "cfo_dashboard (showed stale data)"
    - "billing_reconciliation (delayed, no data loss)"
  business_impact: "None — all reports corrected before deadline"

timeline:
  - time: "14:23 UTC"
    event: "Alert fired: DataFreshnessSLOBreach for revenue_pipeline"
  - time: "14:28 UTC"
    event: "On-call acknowledged, began investigation"
  - time: "14:35 UTC"
    event: "Identified extraction task failing with HTTP 429"
  - time: "14:45 UTC"
    event: "Confirmed: upstream payment API deployed new rate limit (100 req/min → 30 req/min)"
  - time: "15:10 UTC"
    event: "Deployed hotfix: reduced batch size and added exponential backoff"
  - time: "15:30 UTC"
    event: "Pipeline running successfully, backfill initiated"
  - time: "16:38 UTC"
    event: "Backfill complete, all downstream tables refreshed, incident resolved"

root_cause: |
  The upstream payment API team deployed a rate limit reduction
  (100 → 30 requests/minute) without advance notice. Our extraction
  job made 80 requests/minute during peak, triggering 429 responses.
  The extraction task had no retry logic for rate limiting, treating
  429 as a terminal failure.

contributing_factors:
  - "No communication channel with upstream API team for breaking changes"
  - "Extraction task lacked rate-limit-aware retry logic"
  - "No circuit breaker between extraction and the upstream API"
  - "Alert fired on freshness breach (lagging indicator) rather than extraction failure (leading indicator)"

action_items:
  - action: "Implement exponential backoff with jitter for upstream API calls"
    owner: "data_engineer_a"
    priority: P1
    deadline: "2026-05-09"
    ticket: "DATA-4521"

  - action: "Add alert on extraction task HTTP error rates (leading indicator)"
    owner: "data_engineer_b"
    priority: P2
    deadline: "2026-05-12"
    ticket: "DATA-4522"

  - action: "Establish communication channel with payment API team for change notifications"
    owner: "data_eng_lead"
    priority: P2
    deadline: "2026-05-14"
    ticket: "DATA-4523"

  - action: "Implement circuit breaker pattern for all upstream API extractions"
    owner: "data_engineer_a"
    priority: P3
    deadline: "2026-05-21"
    ticket: "DATA-4524"

lessons_learned:
  - "Upstream API changes are a top source of pipeline failures — invest in change detection"
  - "Leading indicators (task failure) alert faster than lagging indicators (freshness breach)"
  - "Rate-limit handling should be standard in all extraction code, not an afterthought"
```

---

## 10. Lab Exercises

### Lab 1: Deploy OpenTelemetry Collector for Kafka + Airflow + PostgreSQL

**Objective:** Set up end-to-end observability for a data stack using OpenTelemetry Collector, Prometheus, Grafana, and Tempo.

#### Docker Compose Setup

```yaml
# docker-compose-observability-lab.yaml
version: '3.8'

services:
  # --- Data Infrastructure ---
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: analytics
      POSTGRES_USER: pipeline_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - ./postgres-init:/docker-entrypoint-initdb.d
      - postgres-data:/var/lib/postgresql/data
    command: >
      postgres
        -c shared_preload_libraries='pg_stat_statements'
        -c pg_stat_statements.track=all
        -c log_destination='jsonlog'
        -c logging_collector=on
        -c log_min_duration_statement=500

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_CONTROLLER_QUORUM_VOTERS: '1@kafka:29093'
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:29093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      CLUSTER_ID: 'q1Sh-9_ISia_zwGINzRvyQ'
      KAFKA_JMX_PORT: 9101
      KAFKA_JMX_HOSTNAME: kafka
    ports:
      - "9092:9092"
      - "9101:9101"

  airflow:
    image: apache/airflow:2.9.0
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://pipeline_user:${POSTGRES_PASSWORD}@postgres/analytics
      AIRFLOW__METRICS__STATSD_ON: 'true'
      AIRFLOW__METRICS__STATSD_HOST: statsd-exporter
      AIRFLOW__METRICS__STATSD_PORT: 9125
      OTEL_EXPORTER_OTLP_ENDPOINT: http://otel-collector:4317
      OTEL_SERVICE_NAME: airflow
    ports:
      - "8080:8080"
    volumes:
      - ./dags:/opt/airflow/dags
    depends_on:
      - postgres
      - kafka

  # --- Observability Stack ---
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.96.0
    command: ["--config=/etc/otel/config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel/config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8889:8889"   # Prometheus exporter
    depends_on:
      - tempo
      - prometheus

  prometheus:
    image: prom/prometheus:v2.51.0
    volumes:
      - ./prometheus.yaml:/etc/prometheus/prometheus.yml
      - ./alert-rules:/etc/prometheus/rules
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'

  grafana:
    image: grafana/grafana:10.4.0
    volumes:
      - ./grafana-provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    depends_on:
      - prometheus
      - tempo
      - loki

  tempo:
    image: grafana/tempo:2.4.0
    command: ["-config.file=/etc/tempo/config.yaml"]
    volumes:
      - ./tempo-config.yaml:/etc/tempo/config.yaml
      - tempo-data:/tmp/tempo
    ports:
      - "3200:3200"   # Tempo HTTP
      - "4317"        # OTLP gRPC (internal)

  loki:
    image: grafana/loki:2.9.0
    volumes:
      - ./loki-config.yaml:/etc/loki/config.yaml
      - loki-data:/loki
    ports:
      - "3100:3100"

  # --- Exporters ---
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:v0.15.0
    environment:
      DATA_SOURCE_NAME: "postgresql://pipeline_user:${POSTGRES_PASSWORD}@postgres:5432/analytics?sslmode=disable"
    ports:
      - "9187:9187"
    depends_on:
      - postgres

  kafka-exporter:
    image: danielqsj/kafka-exporter:v1.7.0
    command: ["--kafka.server=kafka:9092"]
    ports:
      - "9308:9308"
    depends_on:
      - kafka

  statsd-exporter:
    image: prom/statsd-exporter:v0.26.0
    volumes:
      - ./statsd-mapping.yaml:/etc/statsd/mapping.yaml
    command: ["--statsd.mapping-config=/etc/statsd/mapping.yaml"]
    ports:
      - "9125:9125/udp"
      - "9102:9102"

volumes:
  postgres-data:
  prometheus-data:
  grafana-data:
  tempo-data:
  loki-data:
```

#### Prometheus Configuration

```yaml
# prometheus.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/rules/*.yaml

scrape_configs:
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8889']

  - job_name: 'postgres-exporter'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'kafka-exporter'
    static_configs:
      - targets: ['kafka-exporter:9308']

  - job_name: 'statsd-exporter'
    static_configs:
      - targets: ['statsd-exporter:9102']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
```

#### Tempo Configuration

```yaml
# tempo-config.yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"

ingester:
  trace_idle_period: 10s
  max_block_bytes: 1073741824  # 1GB
  max_block_duration: 5m

compactor:
  compaction:
    block_retention: 72h

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/blocks
    wal:
      path: /tmp/tempo/wal

metrics_generator:
  registry:
    external_labels:
      source: tempo
  storage:
    path: /tmp/tempo/generator/wal
    remote_write:
      - url: http://prometheus:9090/api/v1/write
        send_exemplars: true
```

#### Verification Steps

```bash
#!/bin/bash
# verify-observability-stack.sh

echo "=== Verifying Observability Stack ==="

echo "[1/6] Checking Prometheus targets..."
curl -s http://localhost:9090/api/v1/targets | python3 -c "
import json, sys
data = json.load(sys.stdin)
active = [t for t in data['data']['activeTargets']]
for t in active:
    status = '✓' if t['health'] == 'up' else '✗'
    print(f\"  {status} {t['labels'].get('job', 'unknown')}: {t['health']}\")
"

echo "[2/6] Checking Grafana datasources..."
curl -s -u admin:${GRAFANA_PASSWORD} http://localhost:3000/api/datasources | python3 -c "
import json, sys
for ds in json.load(sys.stdin):
    print(f\"  - {ds['name']} ({ds['type']})\")
"

echo "[3/6] Checking OTel Collector health..."
curl -s http://localhost:13133/

echo "[4/6] Checking Tempo..."
curl -s http://localhost:3200/ready

echo "[5/6] Checking Loki..."
curl -s http://localhost:3100/ready

echo "[6/6] Checking Kafka metrics..."
curl -s http://localhost:9308/metrics | grep kafka_consumergroup_lag | head -5

echo "=== Stack verification complete ==="
```

---

### Lab 2: Build Grafana Dashboards for Pipeline Observability

**Objective:** Create a comprehensive Grafana dashboard that covers pipeline health, data quality, and infrastructure.

#### Grafana Provisioning

```yaml
# grafana-provisioning/datasources/datasources.yaml
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
      tracesToMetrics:
        datasourceUid: prometheus
        tags:
          - key: pipeline.name
            value: pipeline

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      derivedFields:
        - name: TraceID
          matcherRegex: '"trace_id":"([a-f0-9]+)"'
          url: '$${__value.raw}'
          datasourceUid: tempo
```

#### Dashboard JSON (Pipeline Health)

```json
{
  "annotations": {"list": []},
  "editable": true,
  "title": "Lab: Pipeline Observability",
  "uid": "lab-pipeline-obs",
  "panels": [
    {
      "title": "Pipeline Run Status (Last 24h)",
      "type": "piechart",
      "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
      "targets": [{
        "expr": "sum by (status) (increase(pipeline_task_completions_total[24h]))",
        "legendFormat": "{{status}}"
      }],
      "fieldConfig": {
        "overrides": [
          {"matcher": {"id": "byName", "options": "success"}, "properties": [{"id": "color", "value": {"fixedColor": "green", "mode": "fixed"}}]},
          {"matcher": {"id": "byName", "options": "failed"}, "properties": [{"id": "color", "value": {"fixedColor": "red", "mode": "fixed"}}]}
        ]
      }
    },
    {
      "title": "Data Freshness (minutes stale)",
      "type": "gauge",
      "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
      "targets": [{
        "expr": "(time() - data_last_successful_load_timestamp) / 60",
        "legendFormat": "{{pipeline}}"
      }],
      "fieldConfig": {
        "defaults": {
          "unit": "min",
          "thresholds": {
            "steps": [
              {"color": "green", "value": 0},
              {"color": "yellow", "value": 15},
              {"color": "red", "value": 60}
            ]
          }
        }
      }
    },
    {
      "title": "Records Processed Per Hour",
      "type": "timeseries",
      "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
      "targets": [{
        "expr": "sum by (pipeline) (rate(pipeline_records_processed_total[5m])) * 3600",
        "legendFormat": "{{pipeline}}"
      }]
    },
    {
      "title": "Kafka Consumer Lag (records)",
      "type": "timeseries",
      "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
      "targets": [{
        "expr": "sum by (consumer_group, topic) (kafka_consumer_lag_records)",
        "legendFormat": "{{consumer_group}} / {{topic}}"
      }],
      "fieldConfig": {
        "defaults": {
          "custom": {
            "thresholdsStyle": {"mode": "line+area"}
          },
          "thresholds": {
            "steps": [
              {"color": "transparent", "value": 0},
              {"color": "red", "value": 1000000}
            ]
          }
        }
      }
    },
    {
      "title": "PostgreSQL Query Latency (p95)",
      "type": "timeseries",
      "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
      "targets": [{
        "expr": "histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))",
        "legendFormat": "p95 query latency"
      }]
    },
    {
      "title": "Pipeline Logs (Errors)",
      "type": "logs",
      "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
      "datasource": "Loki",
      "targets": [{
        "expr": "{job=\"airflow\"} |= \"ERROR\" | json"
      }]
    }
  ]
}
```

---

### Lab 3: Implement Data Freshness and Volume Monitoring with Alerting

**Objective:** Build a Python service that monitors data freshness and volume, exposes Prometheus metrics, and triggers alerts.

```python
#!/usr/bin/env python3
"""
data_freshness_monitor.py

Monitors data freshness and volume for configured tables,
exposes Prometheus metrics, and integrates with alerting.
"""

import time
import os
from datetime import datetime, timezone
from typing import Optional

import psycopg2
from prometheus_client import start_http_server, Gauge, Counter, Histogram, Info

# --- Metrics ---
data_freshness_seconds = Gauge(
    'data_freshness_seconds',
    'Seconds since the most recent record in the table',
    ['database', 'schema', 'table', 'pipeline']
)

data_volume_records = Gauge(
    'data_volume_records_current',
    'Current record count in monitored table/partition',
    ['database', 'schema', 'table', 'partition']
)

data_volume_expected = Gauge(
    'data_volume_records_expected',
    'Expected record count based on historical average',
    ['database', 'schema', 'table']
)

data_freshness_slo_threshold = Gauge(
    'data_freshness_slo_threshold_seconds',
    'Configured freshness SLO threshold in seconds',
    ['pipeline']
)

monitor_check_duration = Histogram(
    'data_monitor_check_duration_seconds',
    'Time taken to perform a monitoring check',
    ['check_type'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

monitor_errors = Counter(
    'data_monitor_errors_total',
    'Errors encountered during monitoring checks',
    ['check_type', 'error_type']
)

# --- Configuration ---
MONITORED_TABLES = [
    {
        "database": "analytics",
        "schema": "public",
        "table": "user_events",
        "timestamp_column": "event_timestamp",
        "pipeline": "user_events_etl",
        "freshness_slo_seconds": 900,  # 15 minutes
        "volume_lookback_days": 7,
    },
    {
        "database": "analytics",
        "schema": "public",
        "table": "revenue_transactions",
        "timestamp_column": "transaction_time",
        "pipeline": "revenue_pipeline",
        "freshness_slo_seconds": 3600,  # 1 hour
        "volume_lookback_days": 7,
    },
    {
        "database": "analytics",
        "schema": "public",
        "table": "ml_features",
        "timestamp_column": "computed_at",
        "pipeline": "ml_feature_pipeline",
        "freshness_slo_seconds": 300,  # 5 minutes
        "volume_lookback_days": 7,
    },
]


def get_db_connection(database: str):
    """Create database connection from environment."""
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        database=database,
        user=os.environ.get("POSTGRES_USER", "pipeline_user"),
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=10,
    )


def check_freshness(config: dict) -> Optional[float]:
    """Check data freshness for a table. Returns staleness in seconds."""
    query = f"""
    SELECT EXTRACT(EPOCH FROM (NOW() - MAX({config['timestamp_column']})))
    FROM {config['schema']}.{config['table']}
    """
    try:
        with monitor_check_duration.labels(check_type="freshness").time():
            conn = get_db_connection(config['database'])
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchone()
            conn.close()

        if result and result[0] is not None:
            staleness = float(result[0])
            data_freshness_seconds.labels(
                database=config['database'],
                schema=config['schema'],
                table=config['table'],
                pipeline=config['pipeline']
            ).set(staleness)

            data_freshness_slo_threshold.labels(
                pipeline=config['pipeline']
            ).set(config['freshness_slo_seconds'])

            return staleness
    except Exception as e:
        monitor_errors.labels(
            check_type="freshness",
            error_type=type(e).__name__
        ).inc()
        raise
    return None


def check_volume(config: dict) -> Optional[int]:
    """Check current volume and compare with historical average."""
    current_query = f"""
    SELECT COUNT(*)
    FROM {config['schema']}.{config['table']}
    WHERE {config['timestamp_column']} >= NOW() - INTERVAL '1 hour'
    """

    historical_query = f"""
    SELECT AVG(hourly_count) FROM (
        SELECT DATE_TRUNC('hour', {config['timestamp_column']}) as hour,
               COUNT(*) as hourly_count
        FROM {config['schema']}.{config['table']}
        WHERE {config['timestamp_column']} >= NOW() - INTERVAL '{config["volume_lookback_days"]} days'
          AND {config['timestamp_column']} < NOW() - INTERVAL '1 hour'
        GROUP BY DATE_TRUNC('hour', {config['timestamp_column']})
    ) hourly_stats
    """
    try:
        with monitor_check_duration.labels(check_type="volume").time():
            conn = get_db_connection(config['database'])
            with conn.cursor() as cur:
                cur.execute(current_query)
                current_count = cur.fetchone()[0]

                cur.execute(historical_query)
                expected_avg = cur.fetchone()[0] or 0
            conn.close()

        data_volume_records.labels(
            database=config['database'],
            schema=config['schema'],
            table=config['table'],
            partition="last_hour"
        ).set(current_count)

        data_volume_expected.labels(
            database=config['database'],
            schema=config['schema'],
            table=config['table']
        ).set(expected_avg)

        return current_count
    except Exception as e:
        monitor_errors.labels(
            check_type="volume",
            error_type=type(e).__name__
        ).inc()
        raise
    return None


def run_monitoring_loop(interval_seconds: int = 60):
    """Main monitoring loop."""
    print(f"Starting data freshness/volume monitor (interval={interval_seconds}s)")
    print(f"Monitoring {len(MONITORED_TABLES)} tables")

    while True:
        for config in MONITORED_TABLES:
            table_name = f"{config['schema']}.{config['table']}"
            try:
                staleness = check_freshness(config)
                volume = check_volume(config)
                if staleness is not None:
                    status = "OK" if staleness < config['freshness_slo_seconds'] else "BREACH"
                    print(
                        f"[{datetime.now(timezone.utc).isoformat()}] "
                        f"{table_name}: freshness={staleness:.0f}s "
                        f"(SLO={config['freshness_slo_seconds']}s) [{status}] "
                        f"volume_last_hour={volume}"
                    )
            except Exception as e:
                print(f"[ERROR] Failed to check {table_name}: {e}")

        time.sleep(interval_seconds)


if __name__ == "__main__":
    # Start Prometheus metrics endpoint
    metrics_port = int(os.environ.get("METRICS_PORT", "8000"))
    start_http_server(metrics_port)
    print(f"Prometheus metrics exposed on port {metrics_port}")

    run_monitoring_loop(
        interval_seconds=int(os.environ.get("CHECK_INTERVAL", "60"))
    )
```

#### Alert Rules for Lab 3

```yaml
# alert-rules/data-freshness-volume.yaml
groups:
  - name: data_freshness_volume
    rules:
      - alert: DataFreshnessBreach
        expr: data_freshness_seconds > on(pipeline) data_freshness_slo_threshold_seconds
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Freshness SLO breached for {{ $labels.table }}"
          description: |
            Table {{ $labels.schema }}.{{ $labels.table }} is {{ $value | humanizeDuration }}
            stale. Pipeline: {{ $labels.pipeline }}
          runbook_url: "https://runbooks.internal/data/freshness-breach"

      - alert: DataVolumeDrop
        expr: |
          (data_volume_records_current / data_volume_records_expected) < 0.5
          and data_volume_records_expected > 100
        for: 15m
        labels:
          severity: high
        annotations:
          summary: "Volume 50%+ below expected for {{ $labels.table }}"
          description: |
            Table {{ $labels.schema }}.{{ $labels.table }} received
            {{ $value | humanizePercentage }} of expected volume in the last hour.

      - alert: DataVolumeZero
        expr: data_volume_records_current == 0 and data_volume_records_expected > 0
        for: 30m
        labels:
          severity: critical
        annotations:
          summary: "Zero records received for {{ $labels.table }} in last hour"

      - alert: MonitorHealthCheck
        expr: up{job="data-freshness-monitor"} == 0
        for: 5m
        labels:
          severity: high
        annotations:
          summary: "Data freshness monitor is down"
```

---

### Lab 4: Create a Data Incident Response Workflow

**Objective:** Build an incident response automation that detects, classifies, and orchestrates response to data incidents.

```python
#!/usr/bin/env python3
"""
data_incident_workflow.py

Automated data incident detection, classification, and response orchestration.
Integrates with Prometheus alerts, Slack, and PagerDuty.
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError


class Severity(Enum):
    P1 = "critical"
    P2 = "high"
    P3 = "medium"
    P4 = "low"


class Status(Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"


@dataclass
class DataIncident:
    id: str
    title: str
    severity: Severity
    status: Status
    detected_at: str
    alert_name: str
    affected_pipeline: str
    affected_tables: list = field(default_factory=list)
    downstream_consumers: list = field(default_factory=list)
    timeline: list = field(default_factory=list)
    assigned_to: Optional[str] = None
    resolved_at: Optional[str] = None
    root_cause: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d['severity'] = self.severity.value
        d['status'] = self.status.value
        return d


# --- Incident Classification ---
SEVERITY_RULES = {
    # Alert name patterns → severity mapping
    "DataFreshnessBreach": {
        "default": Severity.P2,
        "pipeline_overrides": {
            "revenue_pipeline": Severity.P1,
            "ml_feature_pipeline": Severity.P1,
            "internal_analytics": Severity.P3,
        }
    },
    "DataVolumeZero": {
        "default": Severity.P1,
    },
    "DataVolumeDrop": {
        "default": Severity.P2,
    },
    "PipelineConsecutiveFailures": {
        "default": Severity.P2,
        "pipeline_overrides": {
            "revenue_pipeline": Severity.P1,
        }
    },
    "KafkaConsumerLagCritical": {
        "default": Severity.P1,
    },
}

# --- Downstream Impact Mapping ---
LINEAGE_MAP = {
    "user_events": ["user_analytics_dashboard", "ml_feature_store", "marketing_report"],
    "revenue_transactions": ["finance_daily_report", "cfo_dashboard", "billing_reconciliation"],
    "ml_features": ["recommendation_model", "fraud_detection_model", "search_ranking"],
}

# --- On-Call Schedule (simplified) ---
ON_CALL_ROTATION = {
    "data-engineering": "oncall-data-eng@company.com",
}


def classify_incident(alert_name: str, labels: dict) -> Severity:
    """Determine incident severity from alert name and labels."""
    rules = SEVERITY_RULES.get(alert_name, {"default": Severity.P3})
    pipeline = labels.get("pipeline", "")

    if "pipeline_overrides" in rules and pipeline in rules["pipeline_overrides"]:
        return rules["pipeline_overrides"][pipeline]
    return rules["default"]


def generate_incident_id(alert_name: str, labels: dict) -> str:
    """Generate deterministic incident ID for deduplication."""
    key = f"{alert_name}:{labels.get('pipeline', '')}:{labels.get('table', '')}"
    short_hash = hashlib.sha256(key.encode()).hexdigest()[:8]
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"INC-{date_str}-{short_hash}"


def get_downstream_impact(tables: list) -> list:
    """Look up downstream consumers from lineage map."""
    consumers = set()
    for table in tables:
        table_name = table.split(".")[-1]  # strip schema
        if table_name in LINEAGE_MAP:
            consumers.update(LINEAGE_MAP[table_name])
    return sorted(consumers)


def send_slack_notification(incident: DataIncident):
    """Send incident notification to Slack."""
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("[WARN] SLACK_WEBHOOK_URL not set, skipping notification")
        return

    severity_emoji = {
        Severity.P1: ":rotating_light:",
        Severity.P2: ":warning:",
        Severity.P3: ":information_source:",
        Severity.P4: ":memo:",
    }

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{severity_emoji[incident.severity]} Data Incident: {incident.title}"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Severity:* {incident.severity.value.upper()}"},
                {"type": "mrkdwn", "text": f"*Status:* {incident.status.value}"},
                {"type": "mrkdwn", "text": f"*Pipeline:* {incident.affected_pipeline}"},
                {"type": "mrkdwn", "text": f"*Detected:* {incident.detected_at}"},
            ]
        },
    ]

    if incident.downstream_consumers:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Downstream Impact:*\n" +
                        "\n".join(f"• {c}" for c in incident.downstream_consumers)
            }
        })

    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Acknowledge"},
                "action_id": f"ack_{incident.id}",
                "style": "primary"
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "View Runbook"},
                "url": f"https://runbooks.internal/data/{incident.alert_name.lower()}"
            }
        ]
    })

    payload = json.dumps({"blocks": blocks}).encode('utf-8')
    req = Request(webhook_url, data=payload, headers={"Content-Type": "application/json"})
    try:
        urlopen(req, timeout=10)
        print(f"[INFO] Slack notification sent for {incident.id}")
    except URLError as e:
        print(f"[ERROR] Failed to send Slack notification: {e}")


def trigger_pagerduty(incident: DataIncident):
    """Create PagerDuty incident for P1/P2 severity."""
    if incident.severity not in (Severity.P1, Severity.P2):
        return

    routing_key = os.environ.get("PAGERDUTY_ROUTING_KEY")
    if not routing_key:
        print("[WARN] PAGERDUTY_ROUTING_KEY not set, skipping page")
        return

    pd_severity = "critical" if incident.severity == Severity.P1 else "error"

    payload = {
        "routing_key": routing_key,
        "event_action": "trigger",
        "dedup_key": incident.id,
        "payload": {
            "summary": f"[{incident.severity.value.upper()}] {incident.title}",
            "severity": pd_severity,
            "source": "data-incident-workflow",
            "component": incident.affected_pipeline,
            "custom_details": {
                "incident_id": incident.id,
                "affected_tables": incident.affected_tables,
                "downstream_impact": incident.downstream_consumers,
                "detected_at": incident.detected_at,
            }
        },
        "links": [
            {
                "href": f"https://grafana.internal/d/pipeline-health?var-pipeline={incident.affected_pipeline}",
                "text": "Grafana Dashboard"
            },
            {
                "href": f"https://runbooks.internal/data/{incident.alert_name.lower()}",
                "text": "Runbook"
            }
        ]
    }

    data = json.dumps(payload).encode('utf-8')
    req = Request(
        "https://events.pagerduty.com/v2/enqueue",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        urlopen(req, timeout=10)
        print(f"[INFO] PagerDuty incident created for {incident.id}")
    except URLError as e:
        print(f"[ERROR] Failed to create PagerDuty incident: {e}")


def handle_prometheus_alert(alert_payload: dict) -> DataIncident:
    """
    Process incoming Prometheus alert webhook and orchestrate response.

    Expected payload format (Alertmanager webhook):
    {
        "alerts": [{
            "status": "firing",
            "labels": {"alertname": "...", "pipeline": "...", "table": "..."},
            "annotations": {"summary": "...", "description": "..."},
            "startsAt": "2026-05-07T14:23:00Z"
        }]
    }
    """
    for alert in alert_payload.get("alerts", []):
        if alert["status"] != "firing":
            continue

        labels = alert.get("labels", {})
        annotations = alert.get("annotations", {})
        alert_name = labels.get("alertname", "UnknownAlert")

        # Classify
        severity = classify_incident(alert_name, labels)

        # Build incident
        tables = [f"{labels.get('schema', 'public')}.{labels.get('table', 'unknown')}"]
        downstream = get_downstream_impact(tables)

        incident = DataIncident(
            id=generate_incident_id(alert_name, labels),
            title=annotations.get("summary", f"{alert_name} triggered"),
            severity=severity,
            status=Status.OPEN,
            detected_at=alert.get("startsAt", datetime.now(timezone.utc).isoformat()),
            alert_name=alert_name,
            affected_pipeline=labels.get("pipeline", "unknown"),
            affected_tables=tables,
            downstream_consumers=downstream,
            timeline=[{
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": "incident_created",
                "details": f"Auto-created from alert {alert_name}",
            }]
        )

        # Orchestrate response
        print(f"\n{'='*60}")
        print(f"INCIDENT CREATED: {incident.id}")
        print(f"  Severity: {incident.severity.value.upper()}")
        print(f"  Pipeline: {incident.affected_pipeline}")
        print(f"  Tables: {incident.affected_tables}")
        print(f"  Downstream: {incident.downstream_consumers}")
        print(f"{'='*60}\n")

        # Notify
        send_slack_notification(incident)
        trigger_pagerduty(incident)

        return incident

    return None


# --- Flask webhook receiver (minimal) ---
def create_webhook_app():
    """Create a minimal webhook receiver for Alertmanager."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    class AlertHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                payload = json.loads(body)
                incident = handle_prometheus_alert(payload)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                if incident:
                    self.wfile.write(json.dumps(incident.to_dict()).encode())
                else:
                    self.wfile.write(b'{"status": "no_action"}')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())

        def log_message(self, format, *args):
            print(f"[WEBHOOK] {args[0]}")

    return HTTPServer(("0.0.0.0", 9095), AlertHandler)


if __name__ == "__main__":
    print("Starting Data Incident Workflow Webhook (port 9095)")
    server = create_webhook_app()
    server.serve_forever()
```

#### Alertmanager Configuration for the Workflow

```yaml
# alertmanager-config.yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'pipeline']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'data-incident-workflow'

  routes:
    - match:
        severity: critical
      receiver: 'data-incident-workflow'
      group_wait: 10s
      repeat_interval: 1h

    - match:
        severity: high
      receiver: 'data-incident-workflow'
      repeat_interval: 2h

    - match:
        severity: medium
      receiver: 'data-incident-slack-only'
      repeat_interval: 8h

receivers:
  - name: 'data-incident-workflow'
    webhook_configs:
      - url: 'http://incident-workflow:9095/alert'
        send_resolved: true

  - name: 'data-incident-slack-only'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK_URL}'
        channel: '#data-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

#### Testing the Incident Workflow

```bash
#!/bin/bash
# test-incident-workflow.sh
# Simulate a Prometheus alert to test the incident response workflow

curl -X POST http://localhost:9095/alert \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "DataFreshnessBreach",
          "pipeline": "revenue_pipeline",
          "schema": "public",
          "table": "revenue_transactions",
          "severity": "critical"
        },
        "annotations": {
          "summary": "Freshness SLO breached for revenue_transactions",
          "description": "Table public.revenue_transactions is 2h15m stale. SLO threshold is 1h.",
          "runbook_url": "https://runbooks.internal/data/freshness-breach"
        },
        "startsAt": "2026-05-07T14:23:00Z",
        "endsAt": "0001-01-01T00:00:00Z"
      }
    ]
  }'

echo ""
echo "Expected: P1 incident created, Slack + PagerDuty notifications sent"
echo "Check Slack channel #data-incidents and PagerDuty for notifications"
```

---

## Summary

Data observability is not a bolt-on concern — it is a first-class requirement for any production data system. The key takeaways:

1. **Instrument proactively.** Retrofit observability is always harder and less complete than built-in instrumentation.

2. **Data-specific signals matter.** Freshness, volume, schema, and distribution monitoring catch failures invisible to traditional application metrics.

3. **Traces bridge the gap.** Distributed tracing across Kafka, Airflow, Spark, and warehouses provides the "why" that metrics and logs alone cannot.

4. **Alert on business impact.** Not all pipelines are equal. Severity should reflect downstream consumer criticality, not just technical failure state.

5. **Cost is a metric.** Without cost observability, data platforms grow unconstrained. Track unit economics (cost per GB, cost per query) and attribute to teams.

6. **Incidents need process.** Data incidents are fundamentally different from software incidents — they require lineage-aware blast radius assessment, backfill workflows, and stakeholder communication tailored to data consumers.

7. **Dashboards serve audiences.** Executives need binary health signals with trends. Engineers need granular metrics for root cause analysis. Build both.

The labs in this document provide a concrete foundation: a full observability stack (OTel Collector, Prometheus, Grafana, Tempo, Loki), automated monitoring with alerting, and incident response automation. Extend these patterns to your specific data infrastructure, and continuously refine thresholds based on operational experience.
