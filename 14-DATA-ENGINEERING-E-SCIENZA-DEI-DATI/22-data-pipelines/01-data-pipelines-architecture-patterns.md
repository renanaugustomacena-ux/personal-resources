# Data Pipeline Architecture and Design Patterns

## 1. Pipeline Architecture Patterns

### 1.1 Batch ETL (Extract-Transform-Load)

The classical batch ETL pattern extracts data from source systems at scheduled intervals, transforms it in a staging area, and loads the result into a target warehouse. This pattern dominates when latency requirements are measured in hours or days rather than seconds.

**Characteristics:**
- Bounded datasets processed as discrete units
- Scheduled execution (hourly, daily, weekly)
- Clear separation between extraction, transformation, and loading phases
- Easier to reason about correctness (snapshot semantics)
- Resource-intensive during execution windows, idle otherwise

**When to use:**
- Nightly warehouse refreshes
- Regulatory reporting with daily/weekly cadence
- Historical data backfills
- Systems where source databases cannot handle continuous reads

```python
# Batch ETL skeleton with clear phase separation
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Iterator
import pyarrow.parquet as pq
import pyarrow as pa

@dataclass(frozen=True)
class BatchWindow:
    start: datetime
    end: datetime
    partition_key: str

    @classmethod
    def for_date(cls, date: datetime) -> "BatchWindow":
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return cls(start=start, end=end, partition_key=date.strftime("%Y-%m-%d"))


def extract_orders(window: BatchWindow, conn) -> pa.Table:
    """Extract orders within the batch window. Returns Arrow table for zero-copy."""
    query = """
        SELECT order_id, customer_id, total_amount, status, created_at, updated_at
        FROM orders
        WHERE updated_at >= %(start)s AND updated_at < %(end)s
    """
    cursor = conn.cursor()
    cursor.execute(query, {"start": window.start, "end": window.end})
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    return pa.table({col: [row[i] for row in rows] for i, col in enumerate(columns)})


def transform_orders(raw: pa.Table) -> pa.Table:
    """Apply business logic: currency normalization, status mapping, dedup."""
    import pyarrow.compute as pc

    # Deduplicate by order_id keeping latest updated_at
    sorted_table = raw.sort_by([("order_id", "ascending"), ("updated_at", "descending")])
    seen = set()
    keep_indices = []
    for i in range(sorted_table.num_rows):
        oid = sorted_table.column("order_id")[i].as_py()
        if oid not in seen:
            seen.add(oid)
            keep_indices.append(i)

    deduped = sorted_table.take(keep_indices)
    return deduped


def load_orders(transformed: pa.Table, window: BatchWindow, target_path: str) -> None:
    """Write partitioned Parquet to the target landing zone."""
    output_path = f"{target_path}/orders/partition_date={window.partition_key}/data.parquet"
    pq.write_table(transformed, output_path, compression="zstd")
```

### 1.2 ELT (Extract-Load-Transform)

ELT inverts the traditional order: raw data lands in the target system first, and transformations happen inside the warehouse using its native compute engine. This pattern became dominant with the rise of columnar cloud warehouses (Snowflake, BigQuery, Redshift) that separate storage and compute.

**Key differences from ETL:**
- Transformation happens inside the warehouse, not in a separate engine
- Raw data preserved (enables re-transformation without re-extraction)
- Leverages warehouse compute elasticity
- dbt is the canonical transformation layer

**Trade-offs:**
- Requires warehouse with elastic compute (cost scales with transform complexity)
- Raw data storage costs are higher but storage is cheap
- Simpler extraction layer (no transformation logic in extractors)
- Better auditability (raw data always available for re-processing)

### 1.3 Streaming Pipelines

Streaming pipelines process events as they arrive, maintaining continuous flow from producers to consumers. The fundamental abstraction is an unbounded stream of records.

**Core concepts:**
- Event time vs. processing time
- Windowing (tumbling, sliding, session)
- Watermarks for handling late data
- Exactly-once vs. at-least-once semantics
- Backpressure handling

```python
# Flink-style streaming pipeline (using Faust as Python example)
import faust
from datetime import timedelta
from dataclasses import dataclass

app = faust.App("order-pipeline", broker="kafka://localhost:9092")

@dataclass
class OrderEvent:
    order_id: str
    customer_id: str
    amount: float
    currency: str
    timestamp: float

class OrderAggregate(faust.Record):
    customer_id: str
    total_amount: float
    order_count: int
    window_start: float

orders_topic = app.topic("raw.orders", value_type=OrderEvent)
aggregates_topic = app.topic("processed.order_aggregates", value_type=OrderAggregate)

# Tumbling window: 5-minute aggregation
@app.agent(orders_topic)
async def process_orders(stream):
    async for event in stream.tumbling(timedelta(minutes=5)):
        # Emit aggregate per window
        aggregate = OrderAggregate(
            customer_id=event.customer_id,
            total_amount=event.amount,
            order_count=1,
            window_start=event.timestamp,
        )
        await aggregates_topic.send(value=aggregate)
```

### 1.4 Lambda Architecture

Lambda architecture runs both a batch layer (for correctness) and a speed layer (for low latency) in parallel, merging results at query time. The batch layer recomputes truth from raw data periodically; the speed layer provides approximate real-time views.

**Layers:**
1. **Batch layer** — Immutable master dataset, periodic recomputation
2. **Speed layer** — Real-time incremental processing
3. **Serving layer** — Merges batch and speed views for queries

**Drawbacks:**
- Code duplication (same logic in batch and streaming)
- Operational complexity of maintaining two pipelines
- Merge logic at the serving layer is non-trivial
- Debugging discrepancies between layers

### 1.5 Kappa Architecture

Kappa architecture eliminates the batch layer entirely, using a single streaming pipeline with replayable logs (Kafka) as the source of truth. To recompute, you replay the log through a new version of the streaming job.

**Advantages over Lambda:**
- Single codebase for all processing
- Simpler operational model
- No merge logic needed
- Reprocessing by replaying from offset zero

**When to prefer Kappa:**
- Event-sourced systems
- When the log is already the source of truth
- When batch recomputation latency is unacceptable
- When the team cannot maintain two parallel codebases

### 1.6 Medallion Architecture (Bronze/Silver/Gold)

The medallion architecture (popularized by Databricks) organizes data into progressive quality layers. Each layer applies increasing levels of cleansing, conforming, and aggregation.

**Bronze (Raw):**
- Ingested data in original format
- Append-only, schema-on-read
- Full history preserved
- Minimal or no transformation (maybe add ingestion metadata)

**Silver (Conformed):**
- Cleaned, deduplicated, type-cast
- Business keys resolved
- Joins between related entities
- Schema enforced, nulls handled
- SCD applied

**Gold (Business-Ready):**
- Aggregated, domain-specific datasets
- Pre-computed metrics and KPIs
- Optimized for consumption (BI, ML, APIs)
- Often star-schema or one-big-table (OBT) patterns

```sql
-- Bronze: Raw ingestion with metadata
CREATE TABLE bronze.orders (
    _raw_data       STRING,          -- Original JSON payload
    _source         STRING,          -- Source system identifier
    _ingested_at    TIMESTAMP,       -- Ingestion timestamp
    _file_path      STRING,          -- Source file path
    _batch_id       STRING           -- Batch run identifier
);

-- Silver: Cleaned and typed
CREATE TABLE silver.orders (
    order_id        BIGINT NOT NULL,
    customer_id     BIGINT NOT NULL,
    order_date      DATE NOT NULL,
    total_amount    DECIMAL(18,2),
    currency        VARCHAR(3),
    status          VARCHAR(20),
    _silver_loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _bronze_batch_id  STRING,
    _deduplicated     BOOLEAN
);

-- Gold: Business-ready aggregation
CREATE TABLE gold.daily_revenue (
    revenue_date    DATE NOT NULL,
    region          VARCHAR(50),
    product_category VARCHAR(100),
    total_revenue   DECIMAL(18,2),
    order_count     INT,
    avg_order_value DECIMAL(18,2),
    _computed_at    TIMESTAMP
);
```

### 1.7 Data Mesh Pipelines

Data mesh decentralizes pipeline ownership to domain teams. Each domain owns its data products end-to-end, publishing well-defined interfaces for consumption.

**Principles:**
1. Domain ownership of data pipelines
2. Data as a product (SLAs, documentation, discoverability)
3. Self-serve data infrastructure platform
4. Federated computational governance

**Pipeline implications:**
- Each domain team builds and operates its own pipelines
- Cross-domain data flows through published data products (not shared databases)
- Central platform provides reusable infrastructure (orchestration, compute, catalog)
- Data contracts enforce interoperability between domains

### 1.8 Event-Driven Pipelines

Event-driven pipelines react to events (data changes, system signals, external triggers) rather than running on fixed schedules. They are inherently asynchronous and decoupled.

**Event types:**
- Domain events (OrderCreated, PaymentProcessed)
- System events (FileUploaded, SchemaChanged)
- Time events (WindowClosed, SLABreached)

**Patterns:**
- Event sourcing (full event log as source of truth)
- CQRS (separate read/write models)
- Saga pattern (distributed transactions via events)
- Event-carried state transfer

### 1.9 Micro-Batch

Micro-batch bridges pure streaming and traditional batch by processing very small batches (seconds to minutes). Spark Structured Streaming uses this approach internally.

**Characteristics:**
- Bounded mini-batches processed in rapid succession
- Simpler exactly-once semantics than true streaming
- Good latency (seconds) without full streaming complexity
- Checkpointing between micro-batches for fault tolerance

```python
# Spark Structured Streaming micro-batch
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window
from pyspark.sql.types import StructType, StringType, DoubleType, TimestampType

spark = SparkSession.builder.appName("micro-batch-orders").getOrCreate()

schema = StructType() \
    .add("order_id", StringType()) \
    .add("amount", DoubleType()) \
    .add("event_time", TimestampType())

orders_stream = (
    spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "orders")
    .option("startingOffsets", "latest")
    .load()
    .select(from_json(col("value").cast("string"), schema).alias("data"))
    .select("data.*")
)

# 1-minute micro-batch windows
windowed_revenue = (
    orders_stream
    .withWatermark("event_time", "2 minutes")
    .groupBy(window("event_time", "1 minute"))
    .sum("amount")
)

query = (
    windowed_revenue.writeStream
    .format("iceberg")
    .option("checkpointLocation", "/checkpoints/orders_revenue")
    .outputMode("append")
    .trigger(processingTime="30 seconds")  # micro-batch interval
    .start("catalog.db.minute_revenue")
)
```

### 1.10 Change Data Capture (CDC) Pipelines

CDC pipelines capture row-level changes from source databases and propagate them downstream. This avoids expensive full-table scans and provides near-real-time replication.

**CDC methods:**
- Log-based (Debezium reading MySQL binlog / PostgreSQL WAL)
- Trigger-based (database triggers writing to change table)
- Timestamp-based (polling on `updated_at` column)
- Diff-based (comparing snapshots)

Log-based CDC is preferred because it:
- Captures all changes including deletes
- Imposes zero load on source database
- Provides exact ordering of operations
- Captures the before-image for updates

---

## 2. Orchestration

### 2.1 Apache Airflow

Airflow is the industry-standard orchestrator for batch data pipelines. It models workflows as Directed Acyclic Graphs (DAGs) of tasks.

#### DAG Structure

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sensors.filesystem import FileSensor
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": ["alerts@company.com"],
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=60),
    "execution_timeout": timedelta(hours=2),
    "sla": timedelta(hours=4),
}

with DAG(
    dag_id="medallion_orders_pipeline",
    default_args=default_args,
    description="Bronze → Silver → Gold pipeline for order data",
    schedule_interval="0 6 * * *",  # Daily at 06:00 UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["orders", "medallion", "production"],
) as dag:

    # Sensor: wait for source file
    wait_for_export = FileSensor(
        task_id="wait_for_orders_export",
        filepath="/data/landing/orders/{{ ds }}/orders.parquet",
        poke_interval=300,
        timeout=7200,
        mode="reschedule",  # Free up worker slot while waiting
    )

    # Bronze ingestion
    ingest_bronze = PythonOperator(
        task_id="ingest_to_bronze",
        python_callable=ingest_orders_bronze,
        op_kwargs={"partition_date": "{{ ds }}"},
        pool="heavy_io_pool",
    )

    # Silver transformation group
    with TaskGroup("silver_transforms") as silver_group:
        deduplicate = PythonOperator(
            task_id="deduplicate_orders",
            python_callable=deduplicate_silver,
        )
        validate = PythonOperator(
            task_id="validate_schema",
            python_callable=validate_order_schema,
        )
        enrich = PythonOperator(
            task_id="enrich_customer_data",
            python_callable=enrich_with_customer,
        )
        deduplicate >> validate >> enrich

    # Gold aggregation
    with TaskGroup("gold_aggregations") as gold_group:
        daily_revenue = SQLExecuteQueryOperator(
            task_id="compute_daily_revenue",
            conn_id="warehouse",
            sql="sql/gold/daily_revenue.sql",
            parameters={"partition_date": "{{ ds }}"},
        )
        customer_metrics = SQLExecuteQueryOperator(
            task_id="compute_customer_metrics",
            conn_id="warehouse",
            sql="sql/gold/customer_metrics.sql",
            parameters={"partition_date": "{{ ds }}"},
        )
        # These can run in parallel
        [daily_revenue, customer_metrics]

    # DAG flow
    wait_for_export >> ingest_bronze >> silver_group >> gold_group
```

#### XCom for Task Communication

```python
def extract_row_count(**context):
    """Push metrics to XCom for downstream tasks."""
    count = run_extraction()
    context["ti"].xcom_push(key="row_count", value=count)
    context["ti"].xcom_push(key="extraction_ts", value=datetime.utcnow().isoformat())
    return count

def validate_extraction(**context):
    """Pull upstream metrics and validate."""
    row_count = context["ti"].xcom_pull(task_ids="extract_task", key="row_count")
    if row_count == 0:
        raise ValueError("Zero rows extracted — aborting pipeline")
    if row_count < 1000:
        # Log warning but continue
        context["ti"].xcom_push(key="quality_flag", value="LOW_VOLUME")
```

#### Pools and Priority

```python
# In Airflow UI or CLI: create pools to limit resource usage
# airflow pools set heavy_io_pool 4 "Limit concurrent IO-heavy tasks"
# airflow pools set warehouse_queries 8 "Limit concurrent warehouse slots"

heavy_transform = PythonOperator(
    task_id="heavy_spark_transform",
    python_callable=run_spark_job,
    pool="heavy_io_pool",         # Max 4 concurrent across all DAGs
    pool_slots=2,                 # This task consumes 2 of 4 slots
    priority_weight=10,           # Higher = scheduled first within pool
    weight_rule="downstream",     # Priority includes downstream dependencies
)
```

#### SLA Management

```python
def sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis):
    """Alert when SLA is breached."""
    from airflow.providers.slack.hooks.slack_webhook import SlackWebhookHook
    hook = SlackWebhookHook(slack_webhook_conn_id="slack_alerts")
    missed_tasks = ", ".join([str(t) for t in task_list])
    hook.send(text=f"SLA MISS: {dag.dag_id} — Tasks: {missed_tasks}")

with DAG(
    dag_id="critical_pipeline",
    sla_miss_callback=sla_miss_callback,
    # ...
) as dag:
    pass
```

### 2.2 Dagster

Dagster is an asset-oriented orchestrator. Instead of defining task graphs, you define data assets and Dagster infers the execution graph from asset dependencies.

```python
from dagster import (
    asset,
    AssetExecutionContext,
    MaterializeResult,
    MetadataValue,
    Definitions,
    DailyPartitionsDefinition,
    AssetIn,
    IOManager,
    io_manager,
)
import pandas as pd

daily_partitions = DailyPartitionsDefinition(start_date="2024-01-01")


@asset(
    partitions_def=daily_partitions,
    group_name="bronze",
    description="Raw orders ingested from source database",
)
def bronze_orders(context: AssetExecutionContext) -> pd.DataFrame:
    partition_date = context.partition_key
    df = extract_from_source(partition_date)
    context.log.info(f"Extracted {len(df)} rows for {partition_date}")
    return df


@asset(
    partitions_def=daily_partitions,
    group_name="silver",
    ins={"bronze_orders": AssetIn()},
    description="Deduplicated, validated orders with customer enrichment",
)
def silver_orders(context: AssetExecutionContext, bronze_orders: pd.DataFrame) -> pd.DataFrame:
    deduped = bronze_orders.drop_duplicates(subset=["order_id"], keep="last")
    validated = validate_schema(deduped)
    enriched = enrich_customer_info(validated)

    return MaterializeResult(
        metadata={
            "row_count": MetadataValue.int(len(enriched)),
            "null_rate": MetadataValue.float(enriched.isnull().mean().mean()),
        },
        value=enriched,
    )


@asset(
    partitions_def=daily_partitions,
    group_name="gold",
    ins={"silver_orders": AssetIn()},
    description="Daily revenue aggregation by region",
)
def gold_daily_revenue(context: AssetExecutionContext, silver_orders: pd.DataFrame) -> pd.DataFrame:
    return (
        silver_orders
        .groupby(["order_date", "region"])
        .agg(
            total_revenue=("amount", "sum"),
            order_count=("order_id", "count"),
            avg_order_value=("amount", "mean"),
        )
        .reset_index()
    )


# IO Manager for Iceberg
class IcebergIOManager(IOManager):
    def __init__(self, catalog_name: str, namespace: str):
        self.catalog_name = catalog_name
        self.namespace = namespace

    def handle_output(self, context, obj: pd.DataFrame):
        table_name = context.asset_key.to_user_string().replace("/", "_")
        write_to_iceberg(self.catalog_name, self.namespace, table_name, obj)

    def load_input(self, context) -> pd.DataFrame:
        table_name = context.asset_key.to_user_string().replace("/", "_")
        return read_from_iceberg(self.catalog_name, self.namespace, table_name)


@io_manager
def iceberg_io_manager():
    return IcebergIOManager(catalog_name="production", namespace="analytics")


defs = Definitions(
    assets=[bronze_orders, silver_orders, gold_daily_revenue],
    resources={"io_manager": iceberg_io_manager},
)
```

### 2.3 Prefect

Prefect emphasizes simplicity with Python-native flow definitions, minimal boilerplate, and infrastructure abstraction through work pools.

```python
from prefect import flow, task, get_run_logger
from prefect.tasks import task_input_hash
from prefect.deployments import Deployment
from prefect.infrastructure import DockerContainer
from datetime import timedelta
import pandas as pd


@task(
    retries=3,
    retry_delay_seconds=[30, 60, 120],  # Increasing backoff
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1),
    tags=["extraction", "database"],
)
def extract_orders(date: str) -> pd.DataFrame:
    logger = get_run_logger()
    logger.info(f"Extracting orders for {date}")
    return query_source_db(date)


@task(retries=2, tags=["transformation"])
def transform_orders(raw_df: pd.DataFrame) -> pd.DataFrame:
    return (
        raw_df
        .drop_duplicates(subset=["order_id"])
        .assign(amount_usd=lambda df: df["amount"] * df["exchange_rate"])
    )


@task(tags=["loading", "warehouse"])
def load_to_warehouse(df: pd.DataFrame, target_table: str) -> int:
    rows_written = write_to_snowflake(df, target_table)
    return rows_written


@flow(
    name="daily-orders-pipeline",
    description="Daily medallion pipeline for order data",
    retries=1,
    retry_delay_seconds=300,
    timeout_seconds=7200,
)
def daily_orders_pipeline(date: str):
    logger = get_run_logger()

    # Extract
    raw = extract_orders(date)
    logger.info(f"Extracted {len(raw)} rows")

    # Transform
    cleaned = transform_orders(raw)

    # Load
    rows = load_to_warehouse(cleaned, "silver.orders")
    logger.info(f"Loaded {rows} rows to warehouse")

    return {"rows_processed": rows, "date": date}
```

### 2.4 Orchestrator Comparison Matrix

| Feature | Airflow | Dagster | Prefect |
|---------|---------|---------|---------|
| Paradigm | Task-centric DAGs | Asset-centric | Flow/task Python |
| Learning curve | Moderate | Moderate | Low |
| UI | Mature, complex | Modern, asset-focused | Clean, minimal |
| Testing | Harder (DAG serialization) | First-class (asset tests) | Standard pytest |
| Backfill | Built-in (catchup) | Partition-native | Manual triggering |
| Dynamic tasks | Limited (dynamic task mapping 2.3+) | Native | Native |
| Deployment | Kubernetes, Celery, Local | Kubernetes, Docker | Work pools (K8s, Docker, Process) |
| Data lineage | Via plugins | Built-in | Via integrations |
| Secret management | Connections + Vault | Resources | Blocks + Vault |
| Community | Largest | Growing fast | Growing |
| Best for | Complex enterprise pipelines | Data platform teams | Fast iteration |

### 2.5 Scheduling Strategies

**Fixed schedule:** Cron expressions for predictable workloads. Simple, but wastes resources if data arrives at variable times.

**Event-triggered:** Pipeline starts when data arrives (file sensor, Kafka event, webhook). More efficient but requires reliable event delivery.

**Data-aware scheduling:** Dagster's `FreshnessPolicy` — schedule runs only when upstream assets are stale beyond a threshold.

**Dependency-based:** Run when all upstream dependencies complete. Airflow's `ExternalTaskSensor` or Dagster's cross-asset dependencies.

---

## 3. Data Ingestion Patterns

### 3.1 Full Load vs. Incremental

**Full load:** Extract entire table/dataset on each run. Simple but expensive. Use when:
- Source has no reliable change indicator
- Table is small enough that full extraction is cheap
- Data corrections require complete refresh
- Initial backfill

**Incremental — Timestamp-based:**
```python
def incremental_extract(conn, table: str, last_watermark: datetime) -> pa.Table:
    """Extract rows modified since the last watermark."""
    query = f"""
        SELECT * FROM {table}
        WHERE updated_at > %(watermark)s
        ORDER BY updated_at ASC
    """
    cursor = conn.cursor()
    cursor.execute(query, {"watermark": last_watermark})
    # Track new watermark as max(updated_at) from result
    rows = cursor.fetchall()
    return rows, max(r["updated_at"] for r in rows) if rows else last_watermark
```

**Incremental — CDC (log-based):** Captures INSERT/UPDATE/DELETE operations from the database transaction log. Discussed in detail in section 1.10 and section 3.4.

### 3.2 File-Based Ingestion

Landing zones in cloud object storage (S3, GCS, ADLS) are the standard pattern for file-based ingestion.

```python
import boto3
from pathlib import PurePosixPath
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class LandingZoneConfig:
    bucket: str
    prefix: str
    expected_format: str  # "parquet", "csv", "json"
    partition_scheme: str  # "dt={date}", "year={y}/month={m}/day={d}"


def list_new_files(
    config: LandingZoneConfig,
    since: datetime,
    s3_client=None,
) -> list[str]:
    """List files in landing zone newer than the given timestamp."""
    client = s3_client or boto3.client("s3")
    paginator = client.get_paginator("list_objects_v2")

    new_files = []
    for page in paginator.paginate(Bucket=config.bucket, Prefix=config.prefix):
        for obj in page.get("Contents", []):
            if obj["LastModified"].replace(tzinfo=None) > since:
                if obj["Key"].endswith(f".{config.expected_format}"):
                    new_files.append(obj["Key"])

    return sorted(new_files)


def ingest_landing_zone_files(
    config: LandingZoneConfig,
    files: list[str],
    target_table: str,
) -> int:
    """Move files from landing zone into bronze layer."""
    total_rows = 0
    for file_key in files:
        df = read_file_from_s3(config.bucket, file_key, config.expected_format)
        df_with_meta = df.assign(
            _source_file=file_key,
            _ingested_at=datetime.utcnow(),
        )
        append_to_table(target_table, df_with_meta)
        total_rows += len(df_with_meta)
        # Move to processed prefix (don't delete — archive)
        archive_file(config.bucket, file_key, "processed/")

    return total_rows
```

### 3.3 API Ingestion

API ingestion handles pagination, rate limiting, retries, and schema evolution.

```python
import httpx
import time
from dataclasses import dataclass, field
from typing import Any, Iterator, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


@dataclass
class APIIngestorConfig:
    base_url: str
    auth_header: str
    page_size: int = 100
    max_retries: int = 5
    rate_limit_requests_per_second: float = 10.0
    timeout_seconds: int = 30


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate: float):
        self.rate = rate
        self.tokens = rate
        self.last_refill = time.monotonic()

    def acquire(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
        self.last_refill = now

        if self.tokens < 1:
            sleep_time = (1 - self.tokens) / self.rate
            time.sleep(sleep_time)
            self.tokens = 0
        else:
            self.tokens -= 1


class APIIngestor:
    def __init__(self, config: APIIngestorConfig):
        self.config = config
        self.limiter = RateLimiter(config.rate_limit_requests_per_second)
        self.client = httpx.Client(
            base_url=config.base_url,
            headers={"Authorization": config.auth_header},
            timeout=config.timeout_seconds,
        )

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
    )
    def _fetch_page(self, endpoint: str, params: dict) -> dict:
        self.limiter.acquire()
        response = self.client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    def paginate(self, endpoint: str, params: Optional[dict] = None) -> Iterator[list[dict]]:
        """Yield pages of results handling cursor-based pagination."""
        params = params or {}
        params["limit"] = self.config.page_size
        cursor = None

        while True:
            if cursor:
                params["cursor"] = cursor

            data = self._fetch_page(endpoint, params)
            records = data.get("results", [])

            if records:
                yield records

            cursor = data.get("next_cursor")
            if not cursor or not records:
                break
```

### 3.4 Database Replication with Debezium

Debezium captures changes from database transaction logs and publishes them to Kafka topics.

```json
{
  "name": "postgres-orders-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "orders-primary.internal",
    "database.port": "5432",
    "database.user": "${vault:secret/debezium/pg_user}",
    "database.password": "${vault:secret/debezium/pg_password}",
    "database.dbname": "orders",
    "database.server.name": "orders-prod",
    "schema.include.list": "public",
    "table.include.list": "public.orders,public.order_items,public.customers",
    "plugin.name": "pgoutput",
    "publication.name": "debezium_orders",
    "slot.name": "debezium_orders_slot",
    "tombstones.on.delete": true,
    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "transforms": "route",
    "transforms.route.type": "org.apache.kafka.connect.transforms.RegexRouter",
    "transforms.route.regex": "orders-prod.public.(.*)",
    "transforms.route.replacement": "cdc.orders.$1",
    "snapshot.mode": "initial",
    "heartbeat.interval.ms": 10000
  }
}
```

CDC event structure (Debezium envelope):
```json
{
  "before": {"order_id": 123, "status": "pending", "amount": 99.99},
  "after": {"order_id": 123, "status": "shipped", "amount": 99.99},
  "source": {
    "version": "2.5.0",
    "connector": "postgresql",
    "ts_ms": 1704067200000,
    "db": "orders",
    "schema": "public",
    "table": "orders",
    "lsn": 33071472,
    "txId": 5891234
  },
  "op": "u",
  "ts_ms": 1704067200123
}
```

---

## 4. Transformation Patterns

### 4.1 dbt (Data Build Tool)

dbt is the standard transformation layer in modern ELT pipelines. It compiles SQL models into warehouse-native queries, manages dependencies via `ref()`, and provides testing and documentation.

#### Model Organization

```
models/
├── staging/           # 1:1 with source tables, light cleaning
│   ├── stg_orders.sql
│   ├── stg_customers.sql
│   └── _staging_models.yml
├── intermediate/      # Business logic, joins, transformations
│   ├── int_orders_enriched.sql
│   └── int_customer_lifetime.sql
├── marts/            # Business-ready, consumption-optimized
│   ├── finance/
│   │   └── fct_revenue.sql
│   ├── marketing/
│   │   └── dim_customers.sql
│   └── _marts_models.yml
└── sources.yml
```

#### Staging Model

```sql
-- models/staging/stg_orders.sql
{{
    config(
        materialized='view',
        schema='staging'
    )
}}

with source as (
    select * from {{ source('ecommerce', 'raw_orders') }}
),

renamed as (
    select
        id as order_id,
        user_id as customer_id,
        cast(order_date as date) as order_date,
        cast(amount as decimal(18, 2)) as order_amount,
        lower(trim(status)) as order_status,
        cast(created_at as timestamp) as created_at,
        cast(updated_at as timestamp) as updated_at
    from source
    where id is not null  -- Filter corrupt records
)

select * from renamed
```

#### Incremental Model

```sql
-- models/intermediate/int_orders_enriched.sql
{{
    config(
        materialized='incremental',
        unique_key='order_id',
        incremental_strategy='merge',
        on_schema_change='sync_all_columns',
        cluster_by=['order_date']
    )
}}

with orders as (
    select * from {{ ref('stg_orders') }}
    {% if is_incremental() %}
        where updated_at > (select max(updated_at) from {{ this }})
    {% endif %}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

enriched as (
    select
        o.order_id,
        o.customer_id,
        o.order_date,
        o.order_amount,
        o.order_status,
        c.customer_segment,
        c.region,
        c.lifetime_value,
        o.updated_at
    from orders o
    left join customers c on o.customer_id = c.customer_id
)

select * from enriched
```

#### Snapshot (SCD Type 2)

```sql
-- snapshots/orders_snapshot.sql
{% snapshot orders_history %}

{{
    config(
        target_schema='snapshots',
        unique_key='order_id',
        strategy='timestamp',
        updated_at='updated_at',
        invalidate_hard_deletes=True
    )
}}

select * from {{ source('ecommerce', 'raw_orders') }}

{% endsnapshot %}
```

#### Custom Macro

```sql
-- macros/deduplicate.sql
{% macro deduplicate(relation, partition_by, order_by) %}
    with ranked as (
        select
            *,
            row_number() over (
                partition by {{ partition_by }}
                order by {{ order_by }} desc
            ) as _row_rank
        from {{ relation }}
    )
    select * from ranked where _row_rank = 1
{% endmacro %}

-- Usage in a model:
-- select * from {{ deduplicate(ref('stg_events'), 'event_id', 'event_timestamp') }}
```

### 4.2 SCD (Slowly Changing Dimensions) Implementation

#### SCD Type 1 — Overwrite

```sql
-- Simply update in place; no history preserved
MERGE INTO dim_customers AS target
USING staging_customers AS source
ON target.customer_id = source.customer_id
WHEN MATCHED THEN
    UPDATE SET
        target.email = source.email,
        target.phone = source.phone,
        target.address = source.address,
        target.updated_at = CURRENT_TIMESTAMP
WHEN NOT MATCHED THEN
    INSERT (customer_id, email, phone, address, created_at, updated_at)
    VALUES (source.customer_id, source.email, source.phone, source.address,
            CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
```

#### SCD Type 2 — Full History

```sql
-- Close existing record and insert new version
-- Step 1: Expire changed records
UPDATE dim_customers
SET
    valid_to = CURRENT_TIMESTAMP,
    is_current = FALSE
WHERE customer_id IN (
    SELECT s.customer_id
    FROM staging_customers s
    JOIN dim_customers d ON s.customer_id = d.customer_id AND d.is_current = TRUE
    WHERE s.email != d.email OR s.address != d.address
);

-- Step 2: Insert new versions
INSERT INTO dim_customers (customer_id, email, phone, address, valid_from, valid_to, is_current)
SELECT
    s.customer_id,
    s.email,
    s.phone,
    s.address,
    CURRENT_TIMESTAMP,
    '9999-12-31'::timestamp,
    TRUE
FROM staging_customers s
WHERE s.customer_id IN (
    SELECT customer_id FROM dim_customers WHERE is_current = FALSE
    AND valid_to = (SELECT MAX(valid_to) FROM dim_customers dc WHERE dc.customer_id = s.customer_id)
);
```

#### SCD Type 3 — Previous Value Column

```sql
-- Store current and previous value in same row
MERGE INTO dim_customers AS target
USING staging_customers AS source
ON target.customer_id = source.customer_id
WHEN MATCHED AND target.address != source.address THEN
    UPDATE SET
        target.previous_address = target.address,
        target.address = source.address,
        target.address_changed_at = CURRENT_TIMESTAMP;
```

### 4.3 Deduplication Strategies

```sql
-- Window function deduplication (most common)
WITH ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY event_id
            ORDER BY event_timestamp DESC, _ingested_at DESC
        ) AS rn
    FROM bronze.events
)
SELECT * FROM ranked WHERE rn = 1;

-- Hash-based deduplication for detecting true duplicates
WITH hashed AS (
    SELECT
        *,
        MD5(CONCAT_WS('|',
            COALESCE(order_id::text, ''),
            COALESCE(customer_id::text, ''),
            COALESCE(amount::text, ''),
            COALESCE(order_date::text, '')
        )) AS row_hash
    FROM staging.orders
),
deduped AS (
    SELECT DISTINCT ON (row_hash) *
    FROM hashed
    ORDER BY row_hash, _ingested_at DESC
)
SELECT * FROM deduped;
```

### 4.4 Spark Transformations

```python
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import StructType, StructField, StringType, DecimalType, TimestampType


def deduplicate_by_key(df: DataFrame, key_cols: list[str], order_col: str) -> DataFrame:
    """Deduplicate keeping the latest record per key."""
    window = Window.partitionBy(*key_cols).orderBy(F.col(order_col).desc())
    return (
        df
        .withColumn("_rank", F.row_number().over(window))
        .filter(F.col("_rank") == 1)
        .drop("_rank")
    )


def apply_scd2(
    current: DataFrame,
    incoming: DataFrame,
    key_col: str,
    compare_cols: list[str],
) -> DataFrame:
    """Apply SCD Type 2 merge logic in Spark."""
    # Identify changed records
    join_cond = current[key_col] == incoming[key_col]
    change_cond = F.lit(False)
    for col in compare_cols:
        change_cond = change_cond | (current[col] != incoming[col])

    changed = (
        current.alias("c")
        .join(incoming.alias("i"), on=key_col)
        .filter(change_cond & (F.col("c.is_current") == True))
        .select("c.*")
    )

    # Expire old records
    expired = changed.withColumn("valid_to", F.current_timestamp()).withColumn("is_current", F.lit(False))

    # New versions
    new_versions = (
        incoming.alias("i")
        .join(changed.select(key_col).alias("ch"), on=key_col)
        .select("i.*")
        .withColumn("valid_from", F.current_timestamp())
        .withColumn("valid_to", F.lit("9999-12-31").cast(TimestampType()))
        .withColumn("is_current", F.lit(True))
    )

    # Unchanged records
    unchanged = current.subtract(changed)

    return unchanged.unionByName(expired).unionByName(new_versions)
```

---

## 5. Data Quality and Testing

### 5.1 Great Expectations

Great Expectations provides a framework for defining, running, and documenting data quality expectations.

```python
import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest

# Initialize context
context = gx.get_context()

# Define expectations suite
suite = context.add_expectation_suite("orders_silver_suite")

# Column-level expectations
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id")
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeUnique(column="order_id")
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="order_amount", min_value=0, max_value=1000000
    )
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeInSet(
        column="order_status",
        value_set=["pending", "processing", "shipped", "delivered", "cancelled"]
    )
)

# Table-level expectations
suite.add_expectation(
    gx.expectations.ExpectTableRowCountToBeBetween(min_value=1000, max_value=10000000)
)

# Statistical expectations
suite.add_expectation(
    gx.expectations.ExpectColumnMeanToBeBetween(
        column="order_amount", min_value=20.0, max_value=500.0
    )
)

# Freshness expectation
suite.add_expectation(
    gx.expectations.ExpectColumnMaxToBeBetween(
        column="updated_at",
        min_value={"$PARAMETER": "now() - timedelta(hours=24)"},
    )
)

# Run validation
batch_request = RuntimeBatchRequest(
    datasource_name="warehouse",
    data_connector_name="default_runtime_data_connector",
    data_asset_name="silver_orders",
    runtime_parameters={"query": "SELECT * FROM silver.orders WHERE partition_date = '2024-01-15'"},
    batch_identifiers={"default_identifier_name": "2024-01-15"},
)

checkpoint = context.add_or_update_checkpoint(
    name="orders_daily_checkpoint",
    validations=[
        {"batch_request": batch_request, "expectation_suite_name": "orders_silver_suite"}
    ],
    action_list=[
        {"name": "store_validation_result", "action": {"class_name": "StoreValidationResultAction"}},
        {"name": "update_data_docs", "action": {"class_name": "UpdateDataDocsAction"}},
        {
            "name": "slack_alert_on_failure",
            "action": {
                "class_name": "SlackNotificationAction",
                "slack_webhook": "${SLACK_WEBHOOK_URL}",
                "notify_on": "failure",
            },
        },
    ],
)

result = checkpoint.run()
if not result.success:
    raise RuntimeError(f"Data quality check failed: {result.statistics}")
```

### 5.2 dbt Tests

```yaml
# models/_marts_models.yml
version: 2

models:
  - name: fct_revenue
    description: "Daily revenue fact table"
    columns:
      - name: revenue_date
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: "'2020-01-01'"
              max_value: "current_date"
      - name: order_id
        tests:
          - not_null
          - unique
      - name: total_amount
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 1000000
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customers')
              field: customer_id

    tests:
      # Custom singular test
      - row_count_anomaly:
          threshold: 0.3  # Alert if count deviates >30% from 7-day average
```

```sql
-- tests/generic/row_count_anomaly.sql
{% test row_count_anomaly(model, threshold) %}

with current_count as (
    select count(*) as cnt from {{ model }}
),
historical_avg as (
    select avg(row_count) as avg_cnt
    from {{ ref('pipeline_metadata') }}
    where model_name = '{{ model.name }}'
      and run_date >= current_date - interval '7 days'
)
select
    current_count.cnt,
    historical_avg.avg_cnt,
    abs(current_count.cnt - historical_avg.avg_cnt) / nullif(historical_avg.avg_cnt, 0) as deviation
from current_count, historical_avg
where abs(current_count.cnt - historical_avg.avg_cnt) / nullif(historical_avg.avg_cnt, 0) > {{ threshold }}

{% endtest %}
```

### 5.3 Data Contracts

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import jsonschema


class DataType(Enum):
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    TIMESTAMP = "timestamp"
    BOOLEAN = "boolean"
    DATE = "date"


@dataclass(frozen=True)
class ColumnContract:
    name: str
    data_type: DataType
    nullable: bool = False
    unique: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[tuple] = None
    pattern: Optional[str] = None  # Regex for string validation


@dataclass(frozen=True)
class DataContract:
    name: str
    version: str
    owner: str
    description: str
    columns: tuple[ColumnContract, ...]
    sla_freshness_hours: int = 24
    sla_completeness_percent: float = 99.0
    sla_uniqueness_key: Optional[tuple[str, ...]] = None
    min_row_count: int = 0
    max_row_count: Optional[int] = None

    def validate_schema(self, df_columns: dict[str, str]) -> list[str]:
        """Validate DataFrame schema against contract."""
        violations = []
        contract_cols = {c.name for c in self.columns}
        actual_cols = set(df_columns.keys())

        missing = contract_cols - actual_cols
        if missing:
            violations.append(f"Missing required columns: {missing}")

        for col in self.columns:
            if col.name in df_columns:
                actual_type = df_columns[col.name]
                if not self._types_compatible(col.data_type, actual_type):
                    violations.append(
                        f"Column '{col.name}': expected {col.data_type.value}, got {actual_type}"
                    )

        return violations

    @staticmethod
    def _types_compatible(expected: DataType, actual: str) -> bool:
        type_map = {
            DataType.STRING: {"string", "varchar", "text", "object"},
            DataType.INTEGER: {"integer", "int", "bigint", "int64", "int32"},
            DataType.DECIMAL: {"decimal", "numeric", "float", "double", "float64"},
            DataType.TIMESTAMP: {"timestamp", "datetime", "datetime64[ns]"},
            DataType.BOOLEAN: {"boolean", "bool"},
            DataType.DATE: {"date"},
        }
        return actual.lower() in type_map.get(expected, set())


# Example contract definition
orders_contract = DataContract(
    name="silver_orders",
    version="2.1.0",
    owner="data-platform-team",
    description="Cleaned and deduplicated orders from ecommerce platform",
    columns=(
        ColumnContract("order_id", DataType.INTEGER, nullable=False, unique=True),
        ColumnContract("customer_id", DataType.INTEGER, nullable=False),
        ColumnContract("order_date", DataType.DATE, nullable=False),
        ColumnContract("total_amount", DataType.DECIMAL, nullable=False, min_value=0),
        ColumnContract("status", DataType.STRING, nullable=False,
                      allowed_values=("pending", "shipped", "delivered", "cancelled")),
        ColumnContract("updated_at", DataType.TIMESTAMP, nullable=False),
    ),
    sla_freshness_hours=6,
    sla_completeness_percent=99.5,
    sla_uniqueness_key=("order_id",),
    min_row_count=10000,
)
```

### 5.4 Data Observability

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import statistics


@dataclass
class FreshnessCheck:
    table: str
    timestamp_column: str
    max_age_hours: int
    current_max_timestamp: Optional[datetime] = None

    @property
    def is_stale(self) -> bool:
        if self.current_max_timestamp is None:
            return True
        age = datetime.utcnow() - self.current_max_timestamp
        return age > timedelta(hours=self.max_age_hours)

    @property
    def staleness_hours(self) -> float:
        if self.current_max_timestamp is None:
            return float("inf")
        return (datetime.utcnow() - self.current_max_timestamp).total_seconds() / 3600


@dataclass
class VolumeAnomaly:
    table: str
    current_count: int
    historical_counts: list[int]
    threshold_std_devs: float = 2.0

    @property
    def is_anomalous(self) -> bool:
        if len(self.historical_counts) < 7:
            return False
        mean = statistics.mean(self.historical_counts)
        std = statistics.stdev(self.historical_counts)
        if std == 0:
            return self.current_count != mean
        z_score = abs(self.current_count - mean) / std
        return z_score > self.threshold_std_devs

    @property
    def deviation_percent(self) -> float:
        mean = statistics.mean(self.historical_counts) if self.historical_counts else 0
        if mean == 0:
            return 100.0
        return abs(self.current_count - mean) / mean * 100


class DataObservabilityMonitor:
    """Monitors data freshness, volume, and schema drift."""

    def __init__(self, warehouse_conn, alert_callback):
        self.conn = warehouse_conn
        self.alert = alert_callback

    def check_freshness(self, checks: list[FreshnessCheck]) -> list[FreshnessCheck]:
        stale_tables = []
        for check in checks:
            query = f"SELECT MAX({check.timestamp_column}) FROM {check.table}"
            result = self.conn.execute(query).fetchone()
            check.current_max_timestamp = result[0]
            if check.is_stale:
                stale_tables.append(check)
                self.alert(
                    severity="HIGH",
                    message=f"Table {check.table} is stale: "
                            f"{check.staleness_hours:.1f}h (max allowed: {check.max_age_hours}h)",
                )
        return stale_tables

    def check_volume(self, table: str, partition_col: str, lookback_days: int = 14) -> VolumeAnomaly:
        # Get current partition count
        current_query = f"""
            SELECT COUNT(*) FROM {table}
            WHERE {partition_col} = CURRENT_DATE
        """
        current_count = self.conn.execute(current_query).fetchone()[0]

        # Get historical counts
        historical_query = f"""
            SELECT COUNT(*) as cnt
            FROM {table}
            WHERE {partition_col} BETWEEN CURRENT_DATE - {lookback_days} AND CURRENT_DATE - 1
            GROUP BY {partition_col}
            ORDER BY {partition_col}
        """
        historical = [row[0] for row in self.conn.execute(historical_query).fetchall()]

        anomaly = VolumeAnomaly(
            table=table,
            current_count=current_count,
            historical_counts=historical,
        )

        if anomaly.is_anomalous:
            self.alert(
                severity="MEDIUM",
                message=f"Volume anomaly in {table}: {current_count} rows "
                        f"(deviation: {anomaly.deviation_percent:.1f}%)",
            )

        return anomaly
```

---

## 6. Error Handling and Recovery

### 6.1 Dead Letter Queues

When a record fails processing, route it to a dead letter queue (DLQ) instead of failing the entire pipeline.

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import json
import traceback


@dataclass(frozen=True)
class DeadLetterRecord:
    original_payload: str
    error_message: str
    error_type: str
    stack_trace: str
    source_topic: str
    failed_at: str  # ISO 8601
    retry_count: int
    pipeline_name: str
    task_name: str

    def to_json(self) -> str:
        return json.dumps({
            "original_payload": self.original_payload,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "stack_trace": self.stack_trace,
            "source_topic": self.source_topic,
            "failed_at": self.failed_at,
            "retry_count": self.retry_count,
            "pipeline_name": self.pipeline_name,
            "task_name": self.task_name,
        })


class DeadLetterQueue:
    """Route failed records to a dead letter store for later reprocessing."""

    def __init__(self, store_path: str, max_retries: int = 3):
        self.store_path = store_path
        self.max_retries = max_retries

    def send(self, record: Any, error: Exception, context: dict) -> DeadLetterRecord:
        dlr = DeadLetterRecord(
            original_payload=json.dumps(record) if not isinstance(record, str) else record,
            error_message=str(error),
            error_type=type(error).__name__,
            stack_trace=traceback.format_exc(),
            source_topic=context.get("source_topic", "unknown"),
            failed_at=datetime.utcnow().isoformat() + "Z",
            retry_count=context.get("retry_count", 0),
            pipeline_name=context.get("pipeline_name", "unknown"),
            task_name=context.get("task_name", "unknown"),
        )
        self._persist(dlr)
        return dlr

    def _persist(self, record: DeadLetterRecord) -> None:
        """Append to dead letter store (could be file, Kafka topic, database)."""
        import pathlib
        path = pathlib.Path(self.store_path)
        path.mkdir(parents=True, exist_ok=True)
        filename = path / f"dlq_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.json"
        filename.write_text(record.to_json())


def process_with_dlq(records: list[dict], processor, dlq: DeadLetterQueue, context: dict) -> dict:
    """Process records with dead letter handling for individual failures."""
    results = {"success": 0, "failed": 0, "dead_lettered": 0}

    for record in records:
        try:
            processor(record)
            results["success"] += 1
        except (ValueError, KeyError, TypeError) as e:
            # Data quality issue — send to DLQ, don't retry
            dlq.send(record, e, context)
            results["dead_lettered"] += 1
        except Exception as e:
            # Unexpected error — might be transient
            results["failed"] += 1
            raise  # Re-raise to trigger task-level retry

    return results
```

### 6.2 Retry Strategies

```python
import random
import time
from functools import wraps
from typing import Callable, Type


def exponential_backoff_with_jitter(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_factor: float = 0.5,
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator implementing exponential backoff with jitter."""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break

                    # Exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)

                    # Add jitter (both positive and negative)
                    jitter = delay * jitter_factor * (2 * random.random() - 1)
                    actual_delay = max(0, delay + jitter)

                    time.sleep(actual_delay)

            raise last_exception

        return wrapper
    return decorator


@exponential_backoff_with_jitter(
    max_retries=5,
    base_delay=2.0,
    max_delay=120.0,
    retryable_exceptions=(ConnectionError, TimeoutError),
)
def fetch_from_api(endpoint: str) -> dict:
    """Fetch data with automatic retry on transient failures."""
    import httpx
    response = httpx.get(endpoint, timeout=30)
    response.raise_for_status()
    return response.json()
```

### 6.3 Idempotent Pipelines

Idempotency ensures that running a pipeline multiple times with the same input produces the same result without duplicating data.

```python
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256


@dataclass(frozen=True)
class PipelineRun:
    pipeline_id: str
    partition_key: str
    run_id: str
    started_at: datetime

    @property
    def idempotency_key(self) -> str:
        """Unique key for this pipeline execution."""
        return sha256(
            f"{self.pipeline_id}:{self.partition_key}:{self.run_id}".encode()
        ).hexdigest()


class IdempotentWriter:
    """Ensures writes are idempotent using write-audit-publish pattern."""

    def __init__(self, conn):
        self.conn = conn

    def write_idempotent(self, run: PipelineRun, target_table: str, data) -> bool:
        """Write data idempotently. Returns True if new data was written."""

        # Check if this exact run already completed
        check_query = """
            SELECT 1 FROM pipeline_audit.completed_runs
            WHERE idempotency_key = %(key)s AND status = 'SUCCESS'
        """
        existing = self.conn.execute(check_query, {"key": run.idempotency_key}).fetchone()
        if existing:
            return False  # Already processed, skip

        # Write-Audit-Publish pattern:
        # 1. Write to staging (overwrite if partial previous run)
        staging_table = f"staging.{target_table}_{run.idempotency_key[:8]}"
        self._write_to_staging(staging_table, data)

        # 2. Audit: record the write attempt
        self._record_audit(run, target_table, "STAGING_COMPLETE")

        # 3. Publish: atomic swap from staging to target
        self._atomic_publish(staging_table, target_table, run.partition_key)

        # 4. Mark complete
        self._record_audit(run, target_table, "SUCCESS")
        return True

    def _atomic_publish(self, staging: str, target: str, partition_key: str):
        """Atomically replace target partition with staging data."""
        self.conn.execute(f"""
            BEGIN;
            DELETE FROM {target} WHERE partition_key = '{partition_key}';
            INSERT INTO {target} SELECT * FROM {staging};
            DROP TABLE IF EXISTS {staging};
            COMMIT;
        """)
```

### 6.4 Checkpoint/Restart Pattern

```python
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class PipelineCheckpoint:
    pipeline_id: str
    last_completed_step: str
    last_processed_offset: int
    last_processed_timestamp: str
    metadata: dict
    updated_at: str = ""

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat() + "Z"


class CheckpointManager:
    """Manages pipeline checkpoints for restart-from-failure."""

    def __init__(self, checkpoint_dir: str):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, pipeline_id: str) -> Path:
        return self.checkpoint_dir / f"{pipeline_id}.checkpoint.json"

    def save(self, checkpoint: PipelineCheckpoint) -> None:
        path = self._path(checkpoint.pipeline_id)
        path.write_text(json.dumps(asdict(checkpoint), indent=2))

    def load(self, pipeline_id: str) -> Optional[PipelineCheckpoint]:
        path = self._path(pipeline_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return PipelineCheckpoint(**data)

    def clear(self, pipeline_id: str) -> None:
        path = self._path(pipeline_id)
        if path.exists():
            path.unlink()


def run_with_checkpoint(pipeline_id: str, steps: list, checkpoint_mgr: CheckpointManager):
    """Execute pipeline steps with checkpoint/restart capability."""
    checkpoint = checkpoint_mgr.load(pipeline_id)

    # Determine starting step
    start_idx = 0
    if checkpoint:
        for i, step in enumerate(steps):
            if step["name"] == checkpoint.last_completed_step:
                start_idx = i + 1
                break

    for i in range(start_idx, len(steps)):
        step = steps[i]
        try:
            result = step["func"](**step.get("kwargs", {}))

            # Save checkpoint after successful step
            checkpoint_mgr.save(PipelineCheckpoint(
                pipeline_id=pipeline_id,
                last_completed_step=step["name"],
                last_processed_offset=result.get("offset", 0),
                last_processed_timestamp=datetime.utcnow().isoformat() + "Z",
                metadata=result.get("metadata", {}),
            ))
        except Exception as e:
            raise RuntimeError(
                f"Pipeline {pipeline_id} failed at step '{step['name']}' "
                f"(step {i+1}/{len(steps)}): {e}"
            ) from e

    # Pipeline completed successfully — clear checkpoint
    checkpoint_mgr.clear(pipeline_id)
```

### 6.5 Circuit Breaker for External Dependencies

```python
import time
from enum import Enum
from dataclasses import dataclass, field
from threading import Lock
from typing import Callable, Any


class CircuitState(Enum):
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if dependency recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker for external service calls in pipelines."""

    failure_threshold: int = 5
    recovery_timeout_seconds: float = 60.0
    success_threshold: int = 3  # Successes needed in half-open to close

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _lock: Lock = field(default_factory=Lock, init=False)

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                elapsed = time.monotonic() - self._last_failure_time
                if elapsed >= self.recovery_timeout_seconds:
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
            return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        current_state = self.state

        if current_state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"Circuit is OPEN. Will retry after {self.recovery_timeout_seconds}s"
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            else:
                self._failure_count = 0

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
            elif self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN


class CircuitBreakerOpenError(Exception):
    pass


# Usage in pipeline
api_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=30.0)

def fetch_enrichment_data(customer_id: str) -> dict:
    """Fetch from external API with circuit breaker protection."""
    def _call():
        import httpx
        resp = httpx.get(f"https://api.enrichment.io/customers/{customer_id}", timeout=5)
        resp.raise_for_status()
        return resp.json()

    try:
        return api_breaker.call(_call)
    except CircuitBreakerOpenError:
        # Fallback: return cached or default data
        return {"customer_id": customer_id, "enrichment": None, "_fallback": True}
```

---

## 7. Pipeline Security

### 7.1 Secrets Management

```python
# Airflow: Use connections and variables with Vault backend
# airflow.cfg:
# [secrets]
# backend = airflow.providers.hashicorp.secrets.vault.VaultBackend
# backend_kwargs = {"connections_path": "airflow/connections", "variables_path": "airflow/variables", "url": "https://vault.internal:8200"}

from airflow.hooks.base import BaseHook
from airflow.models import Variable


def get_database_connection():
    """Retrieve connection from Airflow's secret backend (Vault-backed)."""
    conn = BaseHook.get_connection("orders_database")
    return {
        "host": conn.host,
        "port": conn.port,
        "database": conn.schema,
        "user": conn.login,
        "password": conn.password,  # Retrieved from Vault at runtime
    }


# Generic secrets manager abstraction
from abc import ABC, abstractmethod
from typing import Optional


class SecretsManager(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> str:
        ...

    @abstractmethod
    def rotate_secret(self, key: str) -> str:
        ...


class VaultSecretsManager(SecretsManager):
    def __init__(self, vault_url: str, auth_method: str = "kubernetes"):
        import hvac
        self.client = hvac.Client(url=vault_url)
        if auth_method == "kubernetes":
            # Service account auth in K8s
            with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
                jwt = f.read()
            self.client.auth.kubernetes.login(role="data-pipeline", jwt=jwt)

    def get_secret(self, key: str) -> str:
        secret = self.client.secrets.kv.v2.read_secret_version(path=key)
        return secret["data"]["data"]["value"]

    def rotate_secret(self, key: str) -> str:
        import secrets as stdlib_secrets
        new_value = stdlib_secrets.token_urlsafe(32)
        self.client.secrets.kv.v2.create_or_update_secret(
            path=key, secret={"value": new_value}
        )
        return new_value
```

### 7.2 Data Encryption and Access Control

```python
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class AccessLevel(Enum):
    FULL = "full"
    MASKED = "masked"
    DENIED = "denied"


@dataclass(frozen=True)
class ColumnPolicy:
    column_name: str
    classification: str  # "PII", "SENSITIVE", "PUBLIC"
    default_access: AccessLevel = AccessLevel.DENIED
    mask_function: Optional[str] = None  # SQL masking expression


@dataclass(frozen=True)
class RowPolicy:
    table_name: str
    filter_expression: str  # SQL WHERE clause
    applies_to_roles: tuple[str, ...]


# Column-level security policies
COLUMN_POLICIES = [
    ColumnPolicy(
        column_name="email",
        classification="PII",
        default_access=AccessLevel.MASKED,
        mask_function="CONCAT(LEFT(email, 2), '***@', SPLIT_PART(email, '@', 2))",
    ),
    ColumnPolicy(
        column_name="phone_number",
        classification="PII",
        default_access=AccessLevel.MASKED,
        mask_function="CONCAT('+XX-XXX-XXX-', RIGHT(phone_number, 4))",
    ),
    ColumnPolicy(
        column_name="ssn",
        classification="PII",
        default_access=AccessLevel.DENIED,
        mask_function=None,  # Never exposed
    ),
    ColumnPolicy(
        column_name="credit_card_number",
        classification="SENSITIVE",
        default_access=AccessLevel.MASKED,
        mask_function="CONCAT('XXXX-XXXX-XXXX-', RIGHT(credit_card_number, 4))",
    ),
]


def generate_masked_view(table: str, policies: list[ColumnPolicy], role: str) -> str:
    """Generate a SQL view with column masking applied."""
    select_clauses = []
    for policy in policies:
        if policy.default_access == AccessLevel.DENIED:
            select_clauses.append(f"NULL AS {policy.column_name}")
        elif policy.default_access == AccessLevel.MASKED and policy.mask_function:
            select_clauses.append(f"{policy.mask_function} AS {policy.column_name}")
        else:
            select_clauses.append(policy.column_name)

    columns_sql = ",\n    ".join(select_clauses)
    return f"""
CREATE OR REPLACE VIEW secured.{table}__{role} AS
SELECT
    {columns_sql}
FROM raw.{table};

GRANT SELECT ON secured.{table}__{role} TO ROLE {role};
"""
```

### 7.3 PII Handling in Transforms

```python
import hashlib
from typing import Callable


class PIIHandler:
    """Handles PII fields during transformation."""

    def __init__(self, salt: str):
        self._salt = salt

    def hash_pii(self, value: str) -> str:
        """One-way hash for pseudonymization."""
        return hashlib.sha256(f"{self._salt}:{value}".encode()).hexdigest()

    def tokenize(self, value: str, token_map: dict) -> str:
        """Reversible tokenization (requires secure token map storage)."""
        if value not in token_map:
            import secrets
            token_map[value] = secrets.token_urlsafe(16)
        return token_map[value]

    @staticmethod
    def redact(value: str, keep_chars: int = 0) -> str:
        """Irreversible redaction."""
        if keep_chars == 0:
            return "[REDACTED]"
        return value[:keep_chars] + "[REDACTED]"


# dbt macro for PII masking
PII_MASK_MACRO = """
-- macros/pii_mask.sql
{% macro pii_hash(column_name, salt_env_var='PII_HASH_SALT') %}
    SHA2(CONCAT('{{ env_var(salt_env_var) }}', ':', {{ column_name }}::VARCHAR), 256)
{% endmacro %}

{% macro pii_mask_email(column_name) %}
    CONCAT(
        LEFT({{ column_name }}, 2),
        '***@',
        SPLIT_PART({{ column_name }}, '@', 2)
    )
{% endmacro %}

-- Usage: SELECT {{ pii_hash('email') }} AS email_hash FROM {{ ref('stg_customers') }}
"""
```

### 7.4 Audit Logging

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import json


@dataclass(frozen=True)
class PipelineAuditEvent:
    event_type: str  # "DATA_ACCESS", "TRANSFORM", "EXPORT", "SCHEMA_CHANGE"
    pipeline_id: str
    task_id: str
    actor: str  # Service account or user
    timestamp: str
    source_tables: tuple[str, ...]
    target_tables: tuple[str, ...]
    row_count: Optional[int]
    columns_accessed: Optional[tuple[str, ...]]
    pii_columns_accessed: Optional[tuple[str, ...]]
    query_hash: Optional[str]
    success: bool
    error_message: Optional[str] = None

    def to_audit_record(self) -> dict:
        return {
            "event_type": self.event_type,
            "pipeline_id": self.pipeline_id,
            "task_id": self.task_id,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "source_tables": list(self.source_tables),
            "target_tables": list(self.target_tables),
            "row_count": self.row_count,
            "columns_accessed": list(self.columns_accessed) if self.columns_accessed else None,
            "pii_columns_accessed": list(self.pii_columns_accessed) if self.pii_columns_accessed else None,
            "query_hash": self.query_hash,
            "success": self.success,
            "error_message": self.error_message,
        }


class PipelineAuditor:
    """Centralized audit logging for pipeline operations."""

    def __init__(self, audit_table: str, conn):
        self.audit_table = audit_table
        self.conn = conn

    def log_event(self, event: PipelineAuditEvent) -> None:
        self.conn.execute(
            f"INSERT INTO {self.audit_table} (event_data) VALUES (%(data)s)",
            {"data": json.dumps(event.to_audit_record())},
        )

    def log_data_access(self, pipeline_id: str, task_id: str, actor: str,
                        source: str, columns: list[str], pii_cols: list[str]) -> None:
        event = PipelineAuditEvent(
            event_type="DATA_ACCESS",
            pipeline_id=pipeline_id,
            task_id=task_id,
            actor=actor,
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_tables=(source,),
            target_tables=(),
            row_count=None,
            columns_accessed=tuple(columns),
            pii_columns_accessed=tuple(pii_cols) if pii_cols else None,
            query_hash=None,
            success=True,
        )
        self.log_event(event)
```

---

## 8. Performance Optimization

### 8.1 Parallelism Strategies

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Any
import multiprocessing


@dataclass(frozen=True)
class ParallelConfig:
    max_workers: int
    chunk_size: int
    use_processes: bool = False  # True for CPU-bound, False for IO-bound


def parallel_extract(
    tables: list[str],
    extract_fn: Callable[[str], Any],
    config: ParallelConfig,
) -> dict[str, Any]:
    """Extract multiple tables in parallel."""
    executor_class = ProcessPoolExecutor if config.use_processes else ThreadPoolExecutor
    results = {}
    errors = {}

    with executor_class(max_workers=config.max_workers) as executor:
        future_to_table = {
            executor.submit(extract_fn, table): table
            for table in tables
        }

        for future in as_completed(future_to_table):
            table = future_to_table[future]
            try:
                results[table] = future.result()
            except Exception as e:
                errors[table] = str(e)

    if errors:
        raise RuntimeError(f"Extraction failed for tables: {errors}")

    return results


# Spark-level parallelism configuration
SPARK_PARALLELISM_CONFIG = {
    # Partition tuning
    "spark.sql.shuffle.partitions": "200",           # Default shuffle partitions
    "spark.sql.adaptive.enabled": "true",            # AQE for auto-tuning
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.skewJoin.enabled": "true",

    # Memory management
    "spark.memory.fraction": "0.8",
    "spark.memory.storageFraction": "0.3",

    # Compression
    "spark.sql.parquet.compression.codec": "zstd",

    # Broadcast join threshold
    "spark.sql.autoBroadcastJoinThreshold": "50MB",
}
```

### 8.2 Partitioning Strategies

```sql
-- Time-based partitioning (most common for event data)
CREATE TABLE events (
    event_id        BIGINT,
    event_type      VARCHAR(50),
    user_id         BIGINT,
    event_data      JSONB,
    event_timestamp TIMESTAMP NOT NULL
) PARTITION BY RANGE (event_timestamp);

-- Create monthly partitions
CREATE TABLE events_2024_01 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE events_2024_02 PARTITION OF events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Hash partitioning for even distribution (high-cardinality keys)
CREATE TABLE user_actions (
    action_id   BIGINT,
    user_id     BIGINT NOT NULL,
    action_type VARCHAR(50),
    created_at  TIMESTAMP
) PARTITION BY HASH (user_id);

CREATE TABLE user_actions_p0 PARTITION OF user_actions
    FOR VALUES WITH (MODULUS 8, REMAINDER 0);
CREATE TABLE user_actions_p1 PARTITION OF user_actions
    FOR VALUES WITH (MODULUS 8, REMAINDER 1);
-- ... through p7

-- Iceberg table with partition evolution
-- (schema evolution without rewriting data)
CREATE TABLE catalog.analytics.orders (
    order_id    BIGINT,
    order_date  DATE,
    region      STRING,
    amount      DECIMAL(18,2)
) USING iceberg
PARTITIONED BY (days(order_date), region);

-- Later, evolve partitioning without rewrite:
ALTER TABLE catalog.analytics.orders
    REPLACE PARTITION FIELD days(order_date) WITH months(order_date);
```

### 8.3 File Format Selection

| Format | Best For | Compression | Schema Evolution | Predicate Pushdown |
|--------|----------|-------------|------------------|--------------------|
| Parquet | Analytics, columnar queries | Excellent (Snappy, ZSTD) | Limited | Column-level |
| ORC | Hive workloads | Excellent (ZLIB, ZSTD) | Limited | Column + row group |
| Avro | Streaming, row-oriented | Moderate | Full (schema registry) | None |
| Delta Lake | ACID on object storage | Parquet-based | Full | Column + file-level |
| Apache Iceberg | Multi-engine lakehouse | Parquet/ORC-based | Full | Column + partition |

```python
# Writing optimized Parquet with proper settings
import pyarrow as pa
import pyarrow.parquet as pq

def write_optimized_parquet(
    table: pa.Table,
    output_path: str,
    partition_cols: list[str] = None,
    row_group_size: int = 128 * 1024,  # 128K rows per row group
):
    """Write Parquet with production-optimized settings."""
    pq.write_to_dataset(
        table,
        root_path=output_path,
        partition_cols=partition_cols,
        compression="zstd",
        compression_level=3,  # Balance between speed and ratio
        row_group_size=row_group_size,
        use_dictionary=True,
        write_statistics=True,  # Enable predicate pushdown
        version="2.6",
        data_page_size=1024 * 1024,  # 1MB data pages
    )
```

### 8.4 Push-Down Optimization

```python
# Push predicates down to storage layer to minimize data scanning
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F


def read_with_pushdown(
    spark: SparkSession,
    table_path: str,
    date_filter: str,
    columns: list[str],
) -> DataFrame:
    """Read with column pruning and predicate pushdown."""
    return (
        spark.read
        .format("iceberg")
        .load(table_path)
        .select(*columns)                    # Column pruning
        .filter(F.col("event_date") == date_filter)  # Partition pruning
        .filter(F.col("amount") > 0)          # Predicate pushdown to row groups
    )


# JDBC pushdown — push filter and aggregation to source database
def extract_with_pushdown(spark: SparkSession, jdbc_url: str, table: str, date: str) -> DataFrame:
    """Push filtering to the source database via JDBC."""
    pushdown_query = f"""
        (SELECT customer_id, SUM(amount) as total, COUNT(*) as cnt
         FROM {table}
         WHERE order_date = '{date}' AND status != 'cancelled'
         GROUP BY customer_id) AS subquery
    """
    return (
        spark.read
        .format("jdbc")
        .option("url", jdbc_url)
        .option("dbtable", pushdown_query)
        .option("fetchsize", "10000")
        .option("numPartitions", "8")
        .option("partitionColumn", "customer_id")
        .option("lowerBound", "1")
        .option("upperBound", "10000000")
        .load()
    )
```

---

## 9. Monitoring and Observability

### 9.1 Pipeline Metrics

```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import time


@dataclass
class PipelineMetrics:
    """Core metrics for pipeline observability."""

    pipeline_id: str
    run_id: str
    start_time: float = field(default_factory=time.monotonic)

    # Latency
    _task_durations: dict = field(default_factory=dict)

    # Throughput
    rows_read: int = 0
    rows_written: int = 0
    bytes_processed: int = 0

    # Error tracking
    errors: int = 0
    warnings: int = 0
    dead_lettered: int = 0

    # Data freshness
    source_freshness: Optional[timedelta] = None
    target_freshness: Optional[timedelta] = None

    def record_task_start(self, task_id: str) -> None:
        self._task_durations[task_id] = {"start": time.monotonic()}

    def record_task_end(self, task_id: str) -> None:
        if task_id in self._task_durations:
            self._task_durations[task_id]["end"] = time.monotonic()
            self._task_durations[task_id]["duration"] = (
                self._task_durations[task_id]["end"] - self._task_durations[task_id]["start"]
            )

    @property
    def total_duration_seconds(self) -> float:
        return time.monotonic() - self.start_time

    @property
    def throughput_rows_per_second(self) -> float:
        duration = self.total_duration_seconds
        return self.rows_written / duration if duration > 0 else 0

    @property
    def error_rate(self) -> float:
        total = self.rows_read or 1
        return self.errors / total

    def to_prometheus_metrics(self) -> list[str]:
        """Export as Prometheus-compatible metrics."""
        prefix = "pipeline"
        labels = f'pipeline_id="{self.pipeline_id}",run_id="{self.run_id}"'
        return [
            f'{prefix}_duration_seconds{{{labels}}} {self.total_duration_seconds:.2f}',
            f'{prefix}_rows_read_total{{{labels}}} {self.rows_read}',
            f'{prefix}_rows_written_total{{{labels}}} {self.rows_written}',
            f'{prefix}_errors_total{{{labels}}} {self.errors}',
            f'{prefix}_dead_lettered_total{{{labels}}} {self.dead_lettered}',
            f'{prefix}_throughput_rps{{{labels}}} {self.throughput_rows_per_second:.1f}',
            f'{prefix}_error_rate{{{labels}}} {self.error_rate:.6f}',
        ]
```

### 9.2 Lineage Tracking with OpenLineage

```python
from openlineage.client import OpenLineageClient
from openlineage.client.run import (
    RunEvent,
    RunState,
    Run,
    Job,
    InputDataset,
    OutputDataset,
    DatasetFacet,
)
from openlineage.client.facet import (
    SchemaDatasetFacet,
    SchemaDatasetFacetFields,
    DataQualityMetricsInputDatasetFacet,
    ColumnLineageDatasetFacet,
    ColumnLineageDatasetFacetFieldsAdditional,
)
import uuid
from datetime import datetime


class PipelineLineageTracker:
    """Track data lineage using OpenLineage standard."""

    def __init__(self, client: OpenLineageClient, namespace: str):
        self.client = client
        self.namespace = namespace

    def emit_start(self, job_name: str, run_id: str, inputs: list[dict], outputs: list[dict]):
        """Emit pipeline start event with input/output datasets."""
        input_datasets = [
            InputDataset(
                namespace=self.namespace,
                name=inp["name"],
                facets={
                    "schema": SchemaDatasetFacet(
                        fields=[
                            SchemaDatasetFacetFields(name=col["name"], type=col["type"])
                            for col in inp.get("columns", [])
                        ]
                    )
                },
            )
            for inp in inputs
        ]

        output_datasets = [
            OutputDataset(
                namespace=self.namespace,
                name=out["name"],
                facets={
                    "schema": SchemaDatasetFacet(
                        fields=[
                            SchemaDatasetFacetFields(name=col["name"], type=col["type"])
                            for col in out.get("columns", [])
                        ]
                    ),
                    "columnLineage": ColumnLineageDatasetFacet(
                        fields={
                            col["name"]: ColumnLineageDatasetFacetFieldsAdditional(
                                inputFields=col.get("source_fields", [])
                            )
                            for col in out.get("columns", [])
                            if "source_fields" in col
                        }
                    ),
                },
            )
            for out in outputs
        ]

        event = RunEvent(
            eventType=RunState.START,
            eventTime=datetime.utcnow().isoformat() + "Z",
            run=Run(runId=run_id),
            job=Job(namespace=self.namespace, name=job_name),
            inputs=input_datasets,
            outputs=output_datasets,
        )
        self.client.emit(event)

    def emit_complete(self, job_name: str, run_id: str, metrics: dict):
        """Emit pipeline completion with quality metrics."""
        event = RunEvent(
            eventType=RunState.COMPLETE,
            eventTime=datetime.utcnow().isoformat() + "Z",
            run=Run(runId=run_id),
            job=Job(namespace=self.namespace, name=job_name),
        )
        self.client.emit(event)
```

### 9.3 Alerting Strategy

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    FATAL = "fatal"


class AlertChannel(Enum):
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    EMAIL = "email"
    OPSGENIE = "opsgenie"


@dataclass(frozen=True)
class AlertRule:
    name: str
    condition: str  # Human-readable condition
    severity: AlertSeverity
    channels: tuple[AlertChannel, ...]
    cooldown_minutes: int = 30  # Don't re-alert within this window
    runbook_url: Optional[str] = None


# Alert routing matrix
PIPELINE_ALERT_RULES = [
    AlertRule(
        name="pipeline_failure",
        condition="Pipeline run failed after all retries exhausted",
        severity=AlertSeverity.CRITICAL,
        channels=(AlertChannel.PAGERDUTY, AlertChannel.SLACK),
        cooldown_minutes=0,
        runbook_url="https://wiki.internal/runbooks/pipeline-failure",
    ),
    AlertRule(
        name="sla_breach",
        condition="Data not available within SLA window",
        severity=AlertSeverity.CRITICAL,
        channels=(AlertChannel.PAGERDUTY, AlertChannel.SLACK),
        cooldown_minutes=60,
        runbook_url="https://wiki.internal/runbooks/sla-breach",
    ),
    AlertRule(
        name="data_freshness",
        condition="Source data older than expected threshold",
        severity=AlertSeverity.WARNING,
        channels=(AlertChannel.SLACK,),
        cooldown_minutes=120,
    ),
    AlertRule(
        name="volume_anomaly",
        condition="Row count deviates >50% from 7-day average",
        severity=AlertSeverity.WARNING,
        channels=(AlertChannel.SLACK,),
        cooldown_minutes=60,
    ),
    AlertRule(
        name="schema_drift",
        condition="Source schema changed (new/removed/type-changed columns)",
        severity=AlertSeverity.WARNING,
        channels=(AlertChannel.SLACK, AlertChannel.EMAIL),
        cooldown_minutes=0,
    ),
    AlertRule(
        name="cost_spike",
        condition="Pipeline compute cost exceeds 2x daily budget",
        severity=AlertSeverity.WARNING,
        channels=(AlertChannel.SLACK,),
        cooldown_minutes=240,
    ),
    AlertRule(
        name="dead_letter_threshold",
        condition="Dead letter queue exceeds 1% of total records",
        severity=AlertSeverity.WARNING,
        channels=(AlertChannel.SLACK,),
        cooldown_minutes=30,
    ),
]
```

### 9.4 SLA Management

```python
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Optional
from enum import Enum


class SLAStatus(Enum):
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"      # >75% of SLA window elapsed
    BREACHED = "breached"


@dataclass(frozen=True)
class PipelineSLA:
    pipeline_id: str
    description: str
    deadline_utc: time          # Daily deadline (e.g., 08:00 UTC)
    warning_threshold_minutes: int  # Alert this many minutes before deadline
    dependency_pipelines: tuple[str, ...] = ()

    def check_status(self, current_time: datetime, pipeline_completed: bool) -> SLAStatus:
        if pipeline_completed:
            return SLAStatus.ON_TRACK

        today_deadline = datetime.combine(current_time.date(), self.deadline_utc)
        time_remaining = today_deadline - current_time

        if time_remaining <= timedelta(0):
            return SLAStatus.BREACHED
        elif time_remaining <= timedelta(minutes=self.warning_threshold_minutes):
            return SLAStatus.AT_RISK
        return SLAStatus.ON_TRACK


# SLA definitions
PIPELINE_SLAS = [
    PipelineSLA(
        pipeline_id="medallion_orders",
        description="Order data available in gold layer",
        deadline_utc=time(8, 0),    # 08:00 UTC
        warning_threshold_minutes=60,
        dependency_pipelines=("cdc_orders_bronze",),
    ),
    PipelineSLA(
        pipeline_id="daily_revenue_report",
        description="Revenue dashboard data refreshed",
        deadline_utc=time(9, 0),    # 09:00 UTC
        warning_threshold_minutes=45,
        dependency_pipelines=("medallion_orders", "medallion_payments"),
    ),
]
```

### 9.5 Cost Monitoring

```sql
-- Snowflake: Track warehouse credit usage per pipeline
CREATE OR REPLACE VIEW monitoring.pipeline_costs AS
SELECT
    query_tag AS pipeline_id,
    DATE_TRUNC('day', start_time) AS run_date,
    SUM(credits_used_cloud_services + credits_used_compute) AS total_credits,
    SUM(bytes_scanned) / POWER(1024, 3) AS gb_scanned,
    COUNT(*) AS query_count,
    AVG(total_elapsed_time) / 1000 AS avg_duration_seconds
FROM snowflake.account_usage.query_history
WHERE query_tag LIKE 'pipeline_%'
  AND start_time >= DATEADD('day', -30, CURRENT_TIMESTAMP())
GROUP BY 1, 2
ORDER BY total_credits DESC;

-- Alert when daily cost exceeds budget
CREATE OR REPLACE TASK monitoring.cost_alert_check
    WAREHOUSE = monitoring_xs
    SCHEDULE = 'USING CRON 0 */4 * * * UTC'
AS
CALL check_pipeline_cost_budget();
```

---

## 10. Lab Exercises

### Lab 1: Complete Medallion Pipeline (Airflow + dbt)

Build a full bronze-silver-gold pipeline processing e-commerce order data.

```python
# dags/medallion_orders_dag.py
"""
Medallion pipeline: Raw files → Bronze → Silver → Gold
Uses Airflow for orchestration, dbt for silver/gold transforms.
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.sensors.filesystem import FileSensor
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.utils.task_group import TaskGroup
from datetime import datetime, timedelta
import json
import pyarrow.parquet as pq
import pyarrow as pa
from pathlib import Path


# --- Bronze Ingestion Functions ---

def ingest_to_bronze(partition_date: str, source_path: str, bronze_path: str, **kwargs):
    """Ingest raw files to bronze layer with metadata."""
    source = Path(source_path) / partition_date
    target = Path(bronze_path) / f"partition_date={partition_date}"
    target.mkdir(parents=True, exist_ok=True)

    files_ingested = 0
    total_rows = 0

    for file in source.glob("*.json"):
        # Read raw JSON
        with open(file) as f:
            records = json.load(f)

        # Add ingestion metadata
        enriched = []
        for record in records:
            enriched.append({
                **record,
                "_source_file": str(file.name),
                "_ingested_at": datetime.utcnow().isoformat(),
                "_batch_id": kwargs["run_id"],
            })

        # Write as Parquet to bronze
        table = pa.Table.from_pylist(enriched)
        output_file = target / f"{file.stem}.parquet"
        pq.write_table(table, str(output_file), compression="zstd")

        files_ingested += 1
        total_rows += len(enriched)

    # Push metrics via XCom
    kwargs["ti"].xcom_push(key="files_ingested", value=files_ingested)
    kwargs["ti"].xcom_push(key="rows_ingested", value=total_rows)
    return {"files": files_ingested, "rows": total_rows}


def validate_bronze(partition_date: str, bronze_path: str, **kwargs):
    """Validate bronze data before transformation."""
    target = Path(bronze_path) / f"partition_date={partition_date}"
    files = list(target.glob("*.parquet"))

    if not files:
        raise ValueError(f"No bronze files found for {partition_date}")

    total_rows = 0
    for file in files:
        table = pq.read_table(str(file))
        total_rows += table.num_rows

        # Basic schema validation
        required_cols = {"order_id", "customer_id", "amount", "status"}
        actual_cols = set(table.column_names)
        missing = required_cols - actual_cols
        if missing:
            raise ValueError(f"Missing columns in {file.name}: {missing}")

    upstream_rows = kwargs["ti"].xcom_pull(task_ids="ingest_bronze", key="rows_ingested")
    if total_rows != upstream_rows:
        raise ValueError(
            f"Row count mismatch: ingested={upstream_rows}, validated={total_rows}"
        )

    return {"validated_rows": total_rows, "files_checked": len(files)}


# --- DAG Definition ---

default_args = {
    "owner": "data-engineering",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(hours=2),
    "sla": timedelta(hours=4),
}

with DAG(
    dag_id="lab_medallion_orders",
    default_args=default_args,
    schedule_interval="0 5 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["lab", "medallion", "orders"],
    doc_md="""
    ## Medallion Orders Pipeline
    
    Ingests raw order JSON files through bronze/silver/gold layers.
    - **Bronze**: Raw Parquet with ingestion metadata
    - **Silver**: dbt models (deduplicated, validated, enriched)
    - **Gold**: dbt models (aggregated business metrics)
    """,
) as dag:

    # Wait for source data
    wait_for_data = FileSensor(
        task_id="wait_for_source_data",
        filepath="/data/landing/orders/{{ ds }}/",
        poke_interval=300,
        timeout=3600,
        mode="reschedule",
    )

    # Bronze layer
    ingest_bronze = PythonOperator(
        task_id="ingest_bronze",
        python_callable=ingest_to_bronze,
        op_kwargs={
            "partition_date": "{{ ds }}",
            "source_path": "/data/landing/orders",
            "bronze_path": "/data/lakehouse/bronze/orders",
        },
    )

    validate_bronze_task = PythonOperator(
        task_id="validate_bronze",
        python_callable=validate_bronze,
        op_kwargs={
            "partition_date": "{{ ds }}",
            "bronze_path": "/data/lakehouse/bronze/orders",
        },
    )

    # Silver layer (dbt)
    with TaskGroup("silver_dbt") as silver_group:
        dbt_silver_run = BashOperator(
            task_id="dbt_run_silver",
            bash_command=(
                "cd /opt/dbt/orders_project && "
                "dbt run --select tag:silver "
                "--vars '{partition_date: {{ ds }}}' "
                "--profiles-dir /opt/dbt/profiles"
            ),
        )
        dbt_silver_test = BashOperator(
            task_id="dbt_test_silver",
            bash_command=(
                "cd /opt/dbt/orders_project && "
                "dbt test --select tag:silver "
                "--profiles-dir /opt/dbt/profiles"
            ),
        )
        dbt_silver_run >> dbt_silver_test

    # Gold layer (dbt)
    with TaskGroup("gold_dbt") as gold_group:
        dbt_gold_run = BashOperator(
            task_id="dbt_run_gold",
            bash_command=(
                "cd /opt/dbt/orders_project && "
                "dbt run --select tag:gold "
                "--vars '{partition_date: {{ ds }}}' "
                "--profiles-dir /opt/dbt/profiles"
            ),
        )
        dbt_gold_test = BashOperator(
            task_id="dbt_test_gold",
            bash_command=(
                "cd /opt/dbt/orders_project && "
                "dbt test --select tag:gold "
                "--profiles-dir /opt/dbt/profiles"
            ),
        )
        dbt_gold_run >> dbt_gold_test

    # Data quality check
    quality_check = BashOperator(
        task_id="run_great_expectations",
        bash_command=(
            "cd /opt/great_expectations && "
            "great_expectations checkpoint run orders_daily_checkpoint "
            "--run-name {{ ds }}"
        ),
    )

    # Flow
    wait_for_data >> ingest_bronze >> validate_bronze_task >> silver_group >> gold_group >> quality_check
```

**dbt models for the lab:**

```sql
-- models/staging/stg_orders.sql
-- tag: silver
{{
    config(
        materialized='incremental',
        unique_key='order_id',
        incremental_strategy='merge',
        tags=['silver']
    )
}}

with raw_orders as (
    select
        *,
        row_number() over (
            partition by cast(_raw->>'order_id' as bigint)
            order by cast(_raw->>'updated_at' as timestamp) desc
        ) as _dedup_rank
    from {{ source('bronze', 'orders') }}
    {% if is_incremental() %}
        where _ingested_at > (select max(_ingested_at) from {{ this }})
    {% endif %}
),

deduplicated as (
    select * from raw_orders where _dedup_rank = 1
),

typed as (
    select
        cast(_raw->>'order_id' as bigint) as order_id,
        cast(_raw->>'customer_id' as bigint) as customer_id,
        cast(_raw->>'order_date' as date) as order_date,
        cast(_raw->>'amount' as decimal(18,2)) as amount,
        lower(trim(_raw->>'status')) as status,
        lower(trim(_raw->>'currency')) as currency,
        cast(_raw->>'created_at' as timestamp) as created_at,
        cast(_raw->>'updated_at' as timestamp) as updated_at,
        _ingested_at,
        _batch_id
    from deduplicated
)

select * from typed
where order_id is not null
  and amount >= 0
  and status in ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded')
```

```sql
-- models/marts/fct_daily_revenue.sql
-- tag: gold
{{
    config(
        materialized='incremental',
        unique_key=['revenue_date', 'region'],
        incremental_strategy='merge',
        tags=['gold'],
        cluster_by=['revenue_date']
    )
}}

with orders as (
    select * from {{ ref('stg_orders') }}
    where status not in ('cancelled', 'refunded')
    {% if is_incremental() %}
        and order_date > (select max(revenue_date) - interval '3 days' from {{ this }})
    {% endif %}
),

customers as (
    select * from {{ ref('dim_customers') }}
),

enriched as (
    select
        o.order_date as revenue_date,
        c.region,
        c.customer_segment,
        o.amount,
        o.order_id
    from orders o
    inner join customers c on o.customer_id = c.customer_id
),

aggregated as (
    select
        revenue_date,
        region,
        count(distinct order_id) as order_count,
        sum(amount) as total_revenue,
        avg(amount) as avg_order_value,
        count(distinct case when customer_segment = 'enterprise' then order_id end) as enterprise_orders,
        current_timestamp as _computed_at
    from enriched
    group by 1, 2
)

select * from aggregated
```

### Lab 2: CDC Pipeline (PostgreSQL → Debezium → Kafka → Iceberg)

```python
# cdc_pipeline/consumer.py
"""
CDC Consumer: Reads Debezium CDC events from Kafka and applies them to Iceberg tables.
Handles INSERT, UPDATE, DELETE operations with exactly-once semantics.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
import json
from confluent_kafka import Consumer, KafkaError, KafkaException
from pyiceberg.catalog import load_catalog
from pyiceberg.table import Table
import pyarrow as pa


class CDCOperation(Enum):
    CREATE = "c"
    UPDATE = "u"
    DELETE = "d"
    READ = "r"  # Snapshot read


@dataclass(frozen=True)
class CDCEvent:
    operation: CDCOperation
    before: Optional[dict]
    after: Optional[dict]
    source_table: str
    source_ts_ms: int
    lsn: int
    tx_id: int

    @classmethod
    def from_debezium(cls, payload: dict) -> "CDCEvent":
        return cls(
            operation=CDCOperation(payload["op"]),
            before=payload.get("before"),
            after=payload.get("after"),
            source_table=payload["source"]["table"],
            source_ts_ms=payload["source"]["ts_ms"],
            lsn=payload["source"].get("lsn", 0),
            tx_id=payload["source"].get("txId", 0),
        )


class CDCIcebergWriter:
    """Applies CDC events to Iceberg tables with upsert/delete logic."""

    def __init__(self, catalog_name: str, namespace: str):
        self.catalog = load_catalog(catalog_name)
        self.namespace = namespace
        self._buffer: dict[str, list[CDCEvent]] = {}
        self._buffer_size = 0
        self.max_buffer_size = 10000

    def buffer_event(self, event: CDCEvent) -> None:
        table_key = event.source_table
        if table_key not in self._buffer:
            self._buffer[table_key] = []
        self._buffer[table_key].append(event)
        self._buffer_size += 1

    def should_flush(self) -> bool:
        return self._buffer_size >= self.max_buffer_size

    def flush(self) -> dict[str, int]:
        """Flush buffered events to Iceberg tables."""
        results = {}
        for table_name, events in self._buffer.items():
            rows_affected = self._apply_events(table_name, events)
            results[table_name] = rows_affected

        self._buffer.clear()
        self._buffer_size = 0
        return results

    def _apply_events(self, table_name: str, events: list[CDCEvent]) -> int:
        """Apply CDC events using merge-on-read strategy."""
        iceberg_table = self.catalog.load_table(f"{self.namespace}.{table_name}")

        # Separate by operation type
        upserts = []
        deletes = []

        for event in events:
            if event.operation in (CDCOperation.CREATE, CDCOperation.UPDATE, CDCOperation.READ):
                if event.after:
                    upserts.append({
                        **event.after,
                        "_cdc_op": event.operation.value,
                        "_cdc_ts": event.source_ts_ms,
                        "_cdc_lsn": event.lsn,
                    })
            elif event.operation == CDCOperation.DELETE:
                if event.before:
                    deletes.append(event.before)

        # Apply upserts
        if upserts:
            upsert_table = pa.Table.from_pylist(upserts)
            # Overwrite matching rows (merge strategy)
            iceberg_table.overwrite(upsert_table, overwrite_filter=self._build_key_filter(upserts, table_name))

        # Apply deletes
        if deletes:
            delete_filter = self._build_delete_filter(deletes, table_name)
            iceberg_table.delete(delete_filter)

        return len(upserts) + len(deletes)

    def _build_key_filter(self, records: list[dict], table_name: str) -> str:
        """Build Iceberg filter expression for merge keys."""
        # Assumes primary key is 'id' — production code would look up schema
        ids = [str(r.get("id", r.get("order_id", ""))) for r in records]
        return f"id IN ({','.join(ids)})"

    def _build_delete_filter(self, records: list[dict], table_name: str) -> str:
        ids = [str(r.get("id", r.get("order_id", ""))) for r in records]
        return f"id IN ({','.join(ids)})"


def run_cdc_consumer(
    kafka_config: dict,
    topics: list[str],
    catalog_name: str,
    namespace: str,
):
    """Main CDC consumer loop with exactly-once commit pattern."""
    consumer = Consumer({
        **kafka_config,
        "enable.auto.commit": False,  # Manual commit for exactly-once
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe(topics)

    writer = CDCIcebergWriter(catalog_name, namespace)
    committed_offsets = {}

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                # No message — flush if buffer has content
                if writer._buffer_size > 0:
                    writer.flush()
                    consumer.commit()
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            # Parse Debezium envelope
            payload = json.loads(msg.value().decode("utf-8"))
            event = CDCEvent.from_debezium(payload)
            writer.buffer_event(event)

            # Flush when buffer is full
            if writer.should_flush():
                results = writer.flush()
                consumer.commit()  # Commit only after successful write
                for table, count in results.items():
                    print(f"Flushed {count} events to {table}")

    except KeyboardInterrupt:
        pass
    finally:
        # Final flush
        if writer._buffer_size > 0:
            writer.flush()
            consumer.commit()
        consumer.close()


# Entry point
if __name__ == "__main__":
    kafka_config = {
        "bootstrap.servers": "kafka-1:9092,kafka-2:9092,kafka-3:9092",
        "group.id": "cdc-iceberg-writer",
        "security.protocol": "SASL_SSL",
        "sasl.mechanism": "SCRAM-SHA-512",
        "sasl.username": "${CDC_KAFKA_USER}",
        "sasl.password": "${CDC_KAFKA_PASSWORD}",
    }

    run_cdc_consumer(
        kafka_config=kafka_config,
        topics=["cdc.orders.orders", "cdc.orders.order_items", "cdc.orders.customers"],
        catalog_name="production",
        namespace="cdc_raw",
    )
```

**Debezium connector deployment:**

```yaml
# docker-compose.yml (lab environment)
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: orders
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${PG_PASSWORD}
    command:
      - "postgres"
      - "-c"
      - "wal_level=logical"
      - "-c"
      - "max_replication_slots=4"
      - "-c"
      - "max_wal_senders=4"
    ports:
      - "5432:5432"

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: 'broker,controller'
      KAFKA_LISTENERS: 'PLAINTEXT://kafka:9092,CONTROLLER://kafka:9093'
      KAFKA_CONTROLLER_QUORUM_VOTERS: '1@kafka:9093'
      CLUSTER_ID: 'lab-cdc-cluster'
    ports:
      - "9092:9092"

  debezium:
    image: debezium/connect:2.5
    environment:
      BOOTSTRAP_SERVERS: kafka:9092
      GROUP_ID: debezium-connect
      CONFIG_STORAGE_TOPIC: _connect-configs
      OFFSET_STORAGE_TOPIC: _connect-offsets
      STATUS_STORAGE_TOPIC: _connect-status
    ports:
      - "8083:8083"
    depends_on:
      - kafka
      - postgres
```

### Lab 3: Data Quality Monitoring System

```python
# quality_monitor/monitor.py
"""
Data quality monitoring system with anomaly detection,
freshness tracking, and automated alerting.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Callable
from enum import Enum
import statistics
import json


class CheckStatus(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    ERROR = "error"


@dataclass(frozen=True)
class QualityCheckResult:
    check_name: str
    table: str
    status: CheckStatus
    message: str
    metric_value: Optional[float]
    threshold: Optional[float]
    executed_at: str
    duration_ms: float


@dataclass
class QualityMonitor:
    """Orchestrates data quality checks across pipeline tables."""

    checks: list = field(default_factory=list)
    results: list = field(default_factory=list)
    alert_callback: Optional[Callable] = None

    def add_freshness_check(self, table: str, column: str, max_age_hours: int):
        self.checks.append({
            "type": "freshness",
            "table": table,
            "column": column,
            "max_age_hours": max_age_hours,
        })

    def add_volume_check(self, table: str, min_rows: int, max_rows: Optional[int] = None):
        self.checks.append({
            "type": "volume",
            "table": table,
            "min_rows": min_rows,
            "max_rows": max_rows,
        })

    def add_null_rate_check(self, table: str, column: str, max_null_pct: float):
        self.checks.append({
            "type": "null_rate",
            "table": table,
            "column": column,
            "max_null_pct": max_null_pct,
        })

    def add_uniqueness_check(self, table: str, columns: list[str]):
        self.checks.append({
            "type": "uniqueness",
            "table": table,
            "columns": columns,
        })

    def add_anomaly_check(
        self,
        table: str,
        metric_query: str,
        lookback_days: int = 14,
        std_dev_threshold: float = 2.5,
    ):
        self.checks.append({
            "type": "anomaly",
            "table": table,
            "metric_query": metric_query,
            "lookback_days": lookback_days,
            "std_dev_threshold": std_dev_threshold,
        })

    def run_all(self, conn) -> list[QualityCheckResult]:
        """Execute all registered checks."""
        import time
        self.results = []

        for check in self.checks:
            start = time.monotonic()
            try:
                result = self._execute_check(check, conn)
            except Exception as e:
                result = QualityCheckResult(
                    check_name=f"{check['type']}_{check['table']}",
                    table=check["table"],
                    status=CheckStatus.ERROR,
                    message=f"Check execution error: {str(e)}",
                    metric_value=None,
                    threshold=None,
                    executed_at=datetime.utcnow().isoformat() + "Z",
                    duration_ms=(time.monotonic() - start) * 1000,
                )

            self.results.append(result)
            duration = (time.monotonic() - start) * 1000
            result = QualityCheckResult(
                check_name=result.check_name,
                table=result.table,
                status=result.status,
                message=result.message,
                metric_value=result.metric_value,
                threshold=result.threshold,
                executed_at=result.executed_at,
                duration_ms=duration,
            )

            # Alert on failures
            if result.status in (CheckStatus.FAIL, CheckStatus.ERROR) and self.alert_callback:
                self.alert_callback(result)

        return self.results

    def _execute_check(self, check: dict, conn) -> QualityCheckResult:
        check_type = check["type"]
        table = check["table"]
        now = datetime.utcnow().isoformat() + "Z"

        if check_type == "freshness":
            query = f"SELECT MAX({check['column']}) FROM {table}"
            max_ts = conn.execute(query).fetchone()[0]
            if max_ts is None:
                return QualityCheckResult(
                    check_name=f"freshness_{table}",
                    table=table,
                    status=CheckStatus.FAIL,
                    message=f"No data in {table}.{check['column']}",
                    metric_value=None,
                    threshold=float(check["max_age_hours"]),
                    executed_at=now,
                    duration_ms=0,
                )
            age_hours = (datetime.utcnow() - max_ts).total_seconds() / 3600
            status = CheckStatus.PASS if age_hours <= check["max_age_hours"] else CheckStatus.FAIL
            return QualityCheckResult(
                check_name=f"freshness_{table}",
                table=table,
                status=status,
                message=f"Data age: {age_hours:.1f}h (max: {check['max_age_hours']}h)",
                metric_value=age_hours,
                threshold=float(check["max_age_hours"]),
                executed_at=now,
                duration_ms=0,
            )

        elif check_type == "volume":
            query = f"SELECT COUNT(*) FROM {table}"
            count = conn.execute(query).fetchone()[0]
            if count < check["min_rows"]:
                status = CheckStatus.FAIL
                msg = f"Row count {count} below minimum {check['min_rows']}"
            elif check.get("max_rows") and count > check["max_rows"]:
                status = CheckStatus.WARN
                msg = f"Row count {count} exceeds maximum {check['max_rows']}"
            else:
                status = CheckStatus.PASS
                msg = f"Row count {count} within expected range"
            return QualityCheckResult(
                check_name=f"volume_{table}",
                table=table,
                status=status,
                message=msg,
                metric_value=float(count),
                threshold=float(check["min_rows"]),
                executed_at=now,
                duration_ms=0,
            )

        elif check_type == "null_rate":
            query = f"""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN {check['column']} IS NULL THEN 1 ELSE 0 END) as nulls
                FROM {table}
            """
            row = conn.execute(query).fetchone()
            total, nulls = row
            null_pct = (nulls / total * 100) if total > 0 else 0
            status = CheckStatus.PASS if null_pct <= check["max_null_pct"] else CheckStatus.FAIL
            return QualityCheckResult(
                check_name=f"null_rate_{table}_{check['column']}",
                table=table,
                status=status,
                message=f"Null rate: {null_pct:.2f}% (max: {check['max_null_pct']}%)",
                metric_value=null_pct,
                threshold=check["max_null_pct"],
                executed_at=now,
                duration_ms=0,
            )

        elif check_type == "uniqueness":
            cols = ", ".join(check["columns"])
            query = f"""
                SELECT COUNT(*) - COUNT(DISTINCT ({cols})) as duplicates
                FROM {table}
            """
            duplicates = conn.execute(query).fetchone()[0]
            status = CheckStatus.PASS if duplicates == 0 else CheckStatus.FAIL
            return QualityCheckResult(
                check_name=f"uniqueness_{table}",
                table=table,
                status=status,
                message=f"Duplicate count: {duplicates} (on columns: {cols})",
                metric_value=float(duplicates),
                threshold=0.0,
                executed_at=now,
                duration_ms=0,
            )

        raise ValueError(f"Unknown check type: {check_type}")

    def generate_report(self) -> dict:
        """Generate summary report of all check results."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        warned = sum(1 for r in self.results if r.status == CheckStatus.WARN)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        errored = sum(1 for r in self.results if r.status == CheckStatus.ERROR)

        return {
            "summary": {
                "total_checks": total,
                "passed": passed,
                "warnings": warned,
                "failures": failed,
                "errors": errored,
                "pass_rate": passed / total * 100 if total > 0 else 0,
            },
            "failures": [
                {
                    "check": r.check_name,
                    "table": r.table,
                    "message": r.message,
                    "metric": r.metric_value,
                    "threshold": r.threshold,
                }
                for r in self.results
                if r.status in (CheckStatus.FAIL, CheckStatus.ERROR)
            ],
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
```

### Lab 4: Self-Healing Pipeline with Retry and Dead Letter Handling

```python
# self_healing_pipeline/pipeline.py
"""
Self-healing pipeline that automatically:
1. Retries transient failures with exponential backoff
2. Routes poison records to dead letter queue
3. Recovers from partial failures using checkpoints
4. Applies circuit breaker to external dependencies
5. Auto-scales based on backpressure signals
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Any, Optional
from enum import Enum
import json
import time
import traceback
from pathlib import Path


class RecordStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    RETRYING = "retrying"
    DEAD_LETTERED = "dead_lettered"


@dataclass
class ProcessingRecord:
    record_id: str
    payload: dict
    status: RecordStatus = RecordStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    last_error: Optional[str] = None
    first_seen_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    last_attempted_at: Optional[str] = None


@dataclass
class PipelineStats:
    total_records: int = 0
    successful: int = 0
    retried: int = 0
    dead_lettered: int = 0
    in_progress: int = 0
    start_time: float = field(default_factory=time.monotonic)

    @property
    def error_rate(self) -> float:
        processed = self.successful + self.dead_lettered
        return self.dead_lettered / processed if processed > 0 else 0

    @property
    def throughput(self) -> float:
        elapsed = time.monotonic() - self.start_time
        return self.successful / elapsed if elapsed > 0 else 0


class SelfHealingPipeline:
    """Pipeline with built-in resilience patterns."""

    def __init__(
        self,
        pipeline_id: str,
        processor: Callable[[dict], dict],
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        dlq_path: str = "/data/dlq",
        checkpoint_path: str = "/data/checkpoints",
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 30.0,
    ):
        self.pipeline_id = pipeline_id
        self.processor = processor
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.dlq_path = Path(dlq_path) / pipeline_id
        self.checkpoint_path = Path(checkpoint_path) / pipeline_id
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout

        # State
        self.stats = PipelineStats()
        self._consecutive_failures = 0
        self._circuit_open_since: Optional[float] = None

        # Ensure directories exist
        self.dlq_path.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.mkdir(parents=True, exist_ok=True)

    def process_batch(self, records: list[dict]) -> PipelineStats:
        """Process a batch of records with self-healing behavior."""
        self.stats = PipelineStats(total_records=len(records))

        # Load checkpoint to skip already-processed records
        checkpoint = self._load_checkpoint()
        processed_ids = set(checkpoint.get("processed_ids", []))

        for record in records:
            record_id = str(record.get("id", hash(json.dumps(record, sort_keys=True))))

            # Skip already processed (idempotency)
            if record_id in processed_ids:
                self.stats.successful += 1
                continue

            # Check circuit breaker
            if self._is_circuit_open():
                # Buffer for later retry
                self._send_to_retry_queue(record, "Circuit breaker open")
                self.stats.retried += 1
                continue

            # Process with retry
            proc_record = ProcessingRecord(
                record_id=record_id,
                payload=record,
                max_attempts=self.max_retries,
            )
            result = self._process_with_retry(proc_record)

            if result.status == RecordStatus.SUCCESS:
                self.stats.successful += 1
                processed_ids.add(record_id)
                self._consecutive_failures = 0
            elif result.status == RecordStatus.DEAD_LETTERED:
                self.stats.dead_lettered += 1

            # Periodic checkpoint
            if (self.stats.successful + self.stats.dead_lettered) % 100 == 0:
                self._save_checkpoint({"processed_ids": list(processed_ids)})

        # Final checkpoint
        self._save_checkpoint({"processed_ids": list(processed_ids)})
        return self.stats

    def _process_with_retry(self, record: ProcessingRecord) -> ProcessingRecord:
        """Attempt processing with exponential backoff retries."""
        import random

        while record.attempts < record.max_attempts:
            record.attempts += 1
            record.status = RecordStatus.PROCESSING
            record.last_attempted_at = datetime.utcnow().isoformat() + "Z"

            try:
                self.processor(record.payload)
                record.status = RecordStatus.SUCCESS
                return record

            except (ValueError, KeyError, TypeError) as e:
                # Data quality issue — not retryable, send to DLQ immediately
                record.last_error = str(e)
                record.status = RecordStatus.DEAD_LETTERED
                self._send_to_dlq(record, e)
                return record

            except Exception as e:
                # Potentially transient — retry with backoff
                record.last_error = str(e)
                record.status = RecordStatus.RETRYING
                self._consecutive_failures += 1

                # Check if we should open circuit breaker
                if self._consecutive_failures >= self.circuit_breaker_threshold:
                    self._open_circuit()

                if record.attempts < record.max_attempts:
                    delay = min(
                        self.base_delay * (2 ** (record.attempts - 1)),
                        self.max_delay,
                    )
                    # Add jitter
                    delay *= (0.5 + random.random())
                    time.sleep(delay)
                    self.stats.retried += 1

        # Exhausted retries — dead letter
        record.status = RecordStatus.DEAD_LETTERED
        self._send_to_dlq(record, Exception(record.last_error or "Max retries exhausted"))
        return record

    def _send_to_dlq(self, record: ProcessingRecord, error: Exception) -> None:
        """Persist failed record to dead letter queue."""
        dlq_entry = {
            "record_id": record.record_id,
            "payload": record.payload,
            "error": str(error),
            "error_type": type(error).__name__,
            "stack_trace": traceback.format_exc(),
            "attempts": record.attempts,
            "first_seen": record.first_seen_at,
            "dead_lettered_at": datetime.utcnow().isoformat() + "Z",
            "pipeline_id": self.pipeline_id,
        }
        filename = self.dlq_path / f"{record.record_id}_{int(time.time())}.json"
        filename.write_text(json.dumps(dlq_entry, indent=2))

    def _send_to_retry_queue(self, record: dict, reason: str) -> None:
        """Buffer record for later retry when circuit is open."""
        retry_entry = {
            "payload": record,
            "reason": reason,
            "buffered_at": datetime.utcnow().isoformat() + "Z",
        }
        filename = self.dlq_path / f"retry_{int(time.time() * 1000)}.json"
        filename.write_text(json.dumps(retry_entry, indent=2))

    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self._circuit_open_since is None:
            return False
        elapsed = time.monotonic() - self._circuit_open_since
        if elapsed >= self.circuit_breaker_timeout:
            # Half-open: allow next request through
            self._circuit_open_since = None
            self._consecutive_failures = 0
            return False
        return True

    def _open_circuit(self) -> None:
        """Trip the circuit breaker."""
        self._circuit_open_since = time.monotonic()

    def _save_checkpoint(self, state: dict) -> None:
        """Save pipeline checkpoint for restart recovery."""
        checkpoint_file = self.checkpoint_path / "latest.json"
        checkpoint_file.write_text(json.dumps({
            **state,
            "pipeline_id": self.pipeline_id,
            "saved_at": datetime.utcnow().isoformat() + "Z",
            "stats": {
                "successful": self.stats.successful,
                "dead_lettered": self.stats.dead_lettered,
                "retried": self.stats.retried,
            },
        }, indent=2))

    def _load_checkpoint(self) -> dict:
        """Load previous checkpoint if exists."""
        checkpoint_file = self.checkpoint_path / "latest.json"
        if checkpoint_file.exists():
            return json.loads(checkpoint_file.read_text())
        return {}

    def replay_dlq(self) -> PipelineStats:
        """Replay dead-lettered records (manual trigger after fix deployed)."""
        dlq_files = sorted(self.dlq_path.glob("*.json"))
        retry_records = []

        for f in dlq_files:
            if f.name.startswith("retry_"):
                entry = json.loads(f.read_text())
                retry_records.append(entry["payload"])
            else:
                entry = json.loads(f.read_text())
                retry_records.append(entry["payload"])

        if not retry_records:
            return PipelineStats()

        # Process with fresh retry budget
        stats = self.process_batch(retry_records)

        # Clean up successfully reprocessed DLQ entries
        if stats.dead_lettered == 0:
            for f in dlq_files:
                f.unlink()

        return stats


# Usage example
def transform_order(record: dict) -> dict:
    """Business transformation that might fail."""
    if not record.get("order_id"):
        raise ValueError("Missing order_id")
    if record.get("amount", 0) < 0:
        raise ValueError(f"Negative amount: {record['amount']}")

    # Simulate external API call that might timeout
    enrichment = fetch_customer_data(record["customer_id"])  # Might raise ConnectionError

    return {
        **record,
        "customer_name": enrichment.get("name"),
        "customer_segment": enrichment.get("segment"),
        "processed_at": datetime.utcnow().isoformat(),
    }


# Initialize and run
pipeline = SelfHealingPipeline(
    pipeline_id="orders_enrichment_v2",
    processor=transform_order,
    max_retries=3,
    base_delay=2.0,
    max_delay=30.0,
    dlq_path="/data/dlq",
    checkpoint_path="/data/checkpoints",
    circuit_breaker_threshold=5,
    circuit_breaker_timeout=30.0,
)

# Process incoming batch
# records = fetch_new_records()
# stats = pipeline.process_batch(records)
# print(f"Processed: {stats.successful}/{stats.total_records}, DLQ: {stats.dead_lettered}")
```

---

## Summary of Key Decisions

| Decision Point | Recommendation |
|---|---|
| Batch vs. Streaming | Batch for analytics SLAs > 1h; streaming for < 1min |
| ETL vs. ELT | ELT when target warehouse has elastic compute |
| Lambda vs. Kappa | Kappa unless you cannot replay the full log |
| Orchestrator | Airflow for enterprise; Dagster for asset-oriented; Prefect for rapid dev |
| CDC method | Log-based (Debezium) for production; timestamp-based for simple cases |
| Transformation | dbt for SQL-first; Spark for complex/large-scale |
| Data quality | Great Expectations for runtime; dbt tests for transform validation |
| File format | Parquet for analytics; Avro for streaming; Iceberg/Delta for lakehouse |
| Retry strategy | Exponential backoff + jitter + circuit breaker + DLQ |
| Observability | OpenLineage for lineage; custom metrics for pipeline health |
