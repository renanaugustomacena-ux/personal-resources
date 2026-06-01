# Data Lake Architecture, Implementation, and Security

---

## 1. Data Lake Concepts

### 1.1 Data Lake vs Data Warehouse vs Data Lakehouse

A **data lake** is a centralized repository that stores structured, semi-structured, and unstructured data at any scale in its native format. Unlike a data warehouse, it defers schema enforcement to query time (schema-on-read), enabling flexibility at the cost of governance complexity.

A **data warehouse** enforces schema-on-write: data is transformed, cleaned, and loaded into a predefined relational schema before it becomes queryable. Warehouses excel at BI workloads with predictable query patterns but struggle with unstructured data, machine learning pipelines, and exploratory analytics.

A **data lakehouse** combines the raw storage economics and flexibility of a lake with the transactional guarantees, schema enforcement, and performance optimizations of a warehouse. Table formats like Apache Iceberg, Delta Lake, and Apache Hudi sit on top of object storage and provide ACID transactions, time travel, and schema evolution — effectively turning a lake into a lakehouse.

| Characteristic | Data Lake | Data Warehouse | Data Lakehouse |
|---|---|---|---|
| Storage format | Open files (Parquet, ORC, JSON, Avro) | Proprietary columnar | Open files + table format metadata |
| Schema enforcement | On read | On write | On write (optional on read) |
| ACID transactions | No (native) | Yes | Yes (via table format) |
| Cost | Low (object storage) | High (compute-storage coupled) | Low (object storage) |
| Data types | Any | Structured only | Any |
| Governance | Manual | Built-in | Table-format + catalog |
| Query performance | Variable | Optimized | Optimized (with statistics/indexes) |

### 1.2 Data Lake Zones

A well-architected data lake uses logical zones to separate data by processing stage:

**Landing Zone (Transient):** Raw data arrives here from source systems. Files are in their original format (CSV, JSON, Avro, binary). Retention is short — data moves to the raw zone after validation. This zone acts as a buffer and allows replay if downstream processing fails.

**Raw Zone (Bronze):** Immutable copy of source data stored in an optimized format (typically Parquet or ORC). Schema is preserved exactly as received. This zone serves as the system of record — nothing is deleted, nothing is transformed. Append-only semantics.

**Curated Zone (Silver):** Data is cleaned, deduplicated, conformed to standard schemas, and joined across sources. Business entities emerge here. PII may be masked or tokenized. Partition strategies are applied for query efficiency.

**Consumption Zone (Gold):** Business-ready datasets optimized for specific use cases: BI dashboards, ML feature stores, API serving layers. Aggregations, materialized views, and denormalized tables live here. SLAs are defined at this tier.

**Sandbox Zone (optional):** Isolated environment for data scientists and analysts to experiment without affecting production zones. Time-limited, auto-purged, with restricted egress.

### 1.3 Schema-on-Read vs Schema-on-Write

**Schema-on-write** requires defining the target schema before data lands. ETL pipelines transform source data to match the schema. Advantages: query performance, data quality guarantees. Disadvantages: inflexible, expensive to evolve, rejects data that does not conform.

**Schema-on-read** stores data as-is and interprets structure at query time. Advantages: ingest everything, evolve interpretation without re-processing, support multiple interpretations of the same data. Disadvantages: garbage in/garbage out, inconsistent query results across consumers, no enforcement of data contracts.

Modern lakehouses blur this line. Table formats enforce schema on write (INSERT/MERGE operations validate types) while still allowing schema evolution (adding columns, widening types) and supporting partition evolution without rewriting data.

### 1.4 The Data Swamp Anti-Pattern

A data lake degrades into a **data swamp** when:

- No metadata or catalog — nobody knows what data exists or what it means.
- No ownership — data is dumped without a responsible team.
- No quality checks — corrupt, duplicate, and stale data accumulates.
- No access controls — everyone can read/write everything.
- No lineage — impossible to trace where data came from or how it was transformed.
- No retention policy — storage grows indefinitely with no cleanup.

Prevention requires: automated cataloging, data contracts between producers and consumers, quality gates at zone transitions, ownership tags enforced by policy, and active lifecycle management.

### 1.5 Data Lake Maturity Model

| Level | Name | Characteristics |
|---|---|---|
| 0 | File dump | Unstructured folder of files, no catalog, no governance |
| 1 | Organized lake | Zoned structure, basic catalog, manual quality checks |
| 2 | Governed lake | Automated cataloging, data contracts, access controls, lineage |
| 3 | Lakehouse | ACID transactions, table formats, schema evolution, time travel |
| 4 | Mesh-ready | Domain-oriented ownership, self-serve infrastructure, federated governance |

### 1.6 Use Cases

- **Machine learning pipelines:** Raw data → feature engineering → training datasets, all in one storage layer.
- **Log analytics:** Petabytes of semi-structured logs (JSON, syslog) queryable without upfront schema.
- **IoT telemetry:** High-volume time-series from devices, stored cheaply, queried for anomaly detection.
- **Regulatory compliance:** Immutable audit trails with long retention, queryable for investigations.
- **Data science exploration:** Analysts access raw data directly without waiting for warehouse modeling.

---

## 2. Object Storage Foundations

### 2.1 Amazon S3 Architecture

S3 is the de facto standard for data lake storage. Key architectural properties:

**Buckets:** Globally unique namespace containers within a region. Flat namespace (prefixes simulate folders). Bucket-level policies control access.

**Objects:** Immutable blobs up to 5 TB. Each object has a key (path), data, metadata (system + user-defined), and a version ID (if versioning enabled). Objects are replicated across at least 3 AZs within a region.

**Consistency model:** Since December 2020, S3 provides strong read-after-write consistency for PUTs and DELETEs. List operations are also strongly consistent. This eliminated the eventual consistency issues that previously plagued data lake workloads.

**Request model:** S3 partitions data by key prefix. High-throughput workloads benefit from randomized prefixes (or date-partitioned prefixes with sufficient cardinality). S3 can handle 5,500 GET and 3,500 PUT requests per second per partitioned prefix.

**Multipart upload:** Objects larger than 100 MB should use multipart upload (required above 5 GB). Parts are uploaded in parallel, improving throughput. Incomplete multipart uploads consume storage — lifecycle rules should abort them after a threshold.

### 2.2 Google Cloud Storage (GCS)

GCS provides a similar object storage model with some architectural differences:

- **Uniform bucket-level access:** Disables object-level ACLs in favor of IAM-only access control (simpler, more secure).
- **Dual-region and multi-region:** Built-in geo-redundancy options beyond single-region.
- **Autoclass:** Automatically transitions objects between storage classes based on access patterns.
- **Hierarchical namespace (preview):** Enables rename/move operations without copying, critical for Hadoop-style workloads.
- **Strong consistency:** All operations (read, list, metadata) are strongly consistent.

### 2.3 Azure Data Lake Storage Gen2

ADLS Gen2 is Azure Blob Storage with a hierarchical namespace (HNS) layered on top:

- **Hierarchical namespace:** True directory semantics — rename is O(1) metadata operation, not O(n) copy+delete. Critical for Spark workloads that rename output directories.
- **POSIX-like ACLs:** File and directory-level permissions with inheritance, compatible with Hadoop access patterns.
- **Integration:** Native connector for Azure Synapse, Databricks, HDInsight. ABFS driver (abfss://) replaces the legacy WASB driver.
- **Storage tiers:** Hot, Cool, Cold, Archive — set per-blob or via lifecycle management.

### 2.4 MinIO (On-Premises)

MinIO is an S3-compatible object store for on-premises and private cloud deployments:

- **S3 API compatible:** Drop-in replacement for S3 in most tooling (Spark, Trino, Iceberg all work unchanged).
- **Erasure coding:** Data protection without RAID, using Reed-Solomon erasure coding across drives.
- **Multi-site replication:** Active-active replication across geographically distributed clusters.
- **Performance:** Designed for high-throughput workloads on NVMe. Can saturate 100 Gbps network links.
- **Deployment:** Single binary, Kubernetes operator, or bare-metal distributed mode.
- **Use case:** Air-gapped environments, data sovereignty requirements, cost optimization at scale.

### 2.5 Storage Classes and Tiers

| Provider | Hot | Warm | Cold | Archive |
|---|---|---|---|---|
| AWS S3 | Standard | IA / One-Zone IA | Glacier Instant | Glacier Deep Archive |
| GCS | Standard | Nearline | Coldline | Archive |
| Azure | Hot | Cool | Cold | Archive |

Selection criteria: access frequency, retrieval latency tolerance, minimum storage duration charges, per-GB storage cost vs per-GB retrieval cost.

### 2.6 Lifecycle Policies

Lifecycle policies automate tier transitions and cleanup:

```json
{
  "Rules": [
    {
      "ID": "TransitionRawToIA",
      "Filter": {"Prefix": "raw/"},
      "Status": "Enabled",
      "Transitions": [
        {"Days": 90, "StorageClass": "STANDARD_IA"},
        {"Days": 365, "StorageClass": "GLACIER_INSTANT_RETRIEVAL"}
      ]
    },
    {
      "ID": "AbortIncompleteMultipart",
      "Filter": {},
      "Status": "Enabled",
      "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}
    },
    {
      "ID": "DeleteOldVersions",
      "Filter": {},
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {"NoncurrentDays": 90}
    }
  ]
}
```

### 2.7 Versioning and Cross-Region Replication

**Versioning** preserves every version of every object. Essential for:
- Accidental deletion recovery.
- Audit compliance (immutable history).
- Table format snapshot integrity (never lose a manifest file).

**Cross-region replication (CRR):** Asynchronous replication of objects to a bucket in another region. Use cases: disaster recovery, latency reduction for multi-region reads, compliance with data residency requirements (replicate to a specific jurisdiction).

Considerations: replication lag (typically seconds to minutes), cost (data transfer + storage), delete marker replication (configurable), and filter rules (replicate only specific prefixes).

---

## 3. Table Formats

### 3.1 Apache Iceberg

Iceberg is an open table format designed for large analytic datasets on object storage.

**Architecture layers:**

1. **Catalog:** Entry point that maps table names to current metadata locations. Implementations: Hive Metastore, AWS Glue, Nessie (git-like branching), REST catalog, JDBC catalog.

2. **Metadata file:** JSON document containing table schema, partition spec, sort order, current snapshot ID, and snapshot history.

3. **Snapshot:** A complete point-in-time view of the table. Each snapshot references a manifest list.

4. **Manifest list:** An Avro file listing all manifest files in a snapshot, with partition range summaries for pruning.

5. **Manifest file:** An Avro file listing data files, with per-file statistics (min/max values, null counts, row counts) enabling file-level pruning.

6. **Data files:** The actual Parquet/ORC/Avro files containing rows.

**Key capabilities:**

- **Time travel:** Query any historical snapshot by ID or timestamp. Rollback to previous versions.
- **Schema evolution:** Add, rename, drop, reorder columns without rewriting data. Type promotion (int → long).
- **Partition evolution:** Change partitioning strategy (e.g., daily → hourly) without rewriting existing data. New data uses the new scheme; queries spanning both are handled transparently.
- **Hidden partitioning:** Partition transforms (year, month, day, hour, bucket, truncate) applied at write time. Queries filter on source columns; the engine maps to partitions automatically.
- **Compaction:** Rewrite small files into larger ones (target ~256 MB-1 GB). Handles the small file problem from streaming ingestion.
- **Row-level deletes:** Position delete files and equality delete files enable efficient single-row deletions without rewriting entire data files.
- **Branching and tagging:** (via Nessie catalog) Git-like branching for experimentation, testing, and CI/CD of data pipelines.

**Compaction strategies:**

```sql
-- Iceberg compaction via Spark
CALL catalog.system.rewrite_data_files(
  table => 'db.events',
  strategy => 'binpack',
  options => map('target-file-size-bytes', '536870912')  -- 512 MB
);

-- Sort-order compaction for better query pruning
CALL catalog.system.rewrite_data_files(
  table => 'db.events',
  strategy => 'sort',
  sort_order => 'event_time ASC NULLS LAST, user_id ASC'
);
```

### 3.2 Delta Lake

Delta Lake is an open-source storage layer from Databricks providing ACID transactions on data lakes.

**Transaction log (_delta_log/):** JSON files recording every action (add file, remove file, metadata change, protocol change). Every 10 commits, a checkpoint Parquet file is written for fast state reconstruction.

**ACID guarantees:**
- **Atomicity:** Multi-file writes succeed or fail as a unit.
- **Consistency:** Schema enforcement rejects writes that violate the table schema.
- **Isolation:** Optimistic concurrency with conflict detection on file-level operations.
- **Durability:** Committed transactions are persisted to object storage.

**Change Data Feed (CDF):** Tracks row-level changes (insert, update_preimage, update_postimage, delete) enabling downstream CDC consumers to process only changes since last checkpoint.

**Liquid clustering:** Replaces static Hive-style partitioning with dynamic data layout optimization. Data is incrementally clustered by specified columns during writes and OPTIMIZE operations. No need to choose partition granularity upfront.

```sql
-- Enable liquid clustering
CREATE TABLE events (
  event_id BIGINT,
  event_time TIMESTAMP,
  user_id STRING,
  event_type STRING
) USING DELTA
CLUSTER BY (event_time, user_id);

-- Optimize (trigger clustering)
OPTIMIZE events;
```

**Deletion vectors:** Instead of rewriting data files on DELETE/UPDATE, a deletion vector (bitmap) marks which rows are logically deleted. Reduces write amplification significantly.

**UniForm:** Automatic generation of Iceberg-compatible metadata alongside Delta metadata, enabling Iceberg readers to query Delta tables without conversion.

### 3.3 Apache Hudi

Hudi (Hadoop Upserts Deletes and Incrementals) is optimized for record-level mutations and streaming ingestion.

**Table types:**

- **Copy-on-Write (CoW):** Updates rewrite entire data files. Higher write cost, zero read overhead. Best for read-heavy workloads with infrequent updates.
- **Merge-on-Read (MoR):** Updates written to row-level log files (Avro). Reads merge base files + logs at query time. Lower write cost, read-time merge overhead. Compaction merges logs into base files periodically.

**Timeline:** Ordered log of all actions (commits, deltacommits, compaction, clean, rollback). Each action has three states: REQUESTED, INFLIGHT, COMPLETED. The timeline enables incremental queries — consumers can request "all changes since timestamp X."

**Compaction:** For MoR tables, compaction merges delta logs into base Parquet files. Strategies: bound I/O (limit files per compaction), bound growth (compact when log files exceed threshold), time-based (compact every N minutes).

**Indexing:** Hudi maintains indexes (bloom filter, HBase, bucket, record-level) for efficient upsert operations — finding which file group contains a given record key without scanning all files.

### 3.4 Comparison Matrix

| Feature | Iceberg | Delta Lake | Hudi |
|---|---|---|---|
| ACID transactions | Yes | Yes | Yes |
| Time travel | Snapshot-based | Version-based | Timeline-based |
| Schema evolution | Full (add, drop, rename, reorder, type widen) | Add, rename, type widen | Add, delete (limited) |
| Partition evolution | Yes (transparent) | No (liquid clustering as alternative) | No |
| Row-level operations | Position/equality deletes | Deletion vectors | Native upsert (CoW/MoR) |
| Streaming support | Good (Flink/Spark) | Good (Spark Structured Streaming) | Excellent (designed for it) |
| File format | Parquet, ORC, Avro | Parquet only | Parquet (base) + Avro (logs) |
| Catalog | Pluggable (REST, Hive, Glue, Nessie) | Unity Catalog, Hive | Hive Metastore |
| Engine support | Spark, Flink, Trino, Dremio, Athena, BigQuery | Spark, Flink (emerging), Trino, Databricks | Spark, Flink, Presto, Trino |
| Community | Apache, vendor-neutral | Databricks-driven (Apache-licensed) | Apache, Uber-originated |

---

## 4. Query Engines

### 4.1 Trino (formerly Presto SQL)

Trino is a distributed SQL query engine designed for interactive analytics across federated data sources.

**Architecture:**
- **Coordinator:** Parses SQL, plans queries, schedules execution across workers.
- **Workers:** Execute query fragments in parallel, process data in memory (pipeline model, not MapReduce).
- **Connectors:** Pluggable data source adapters (Hive/Iceberg/Delta for lakes, PostgreSQL, MySQL, Elasticsearch, Kafka, MongoDB, etc.).

**Federated queries:** A single SQL statement can join data across multiple connectors:

```sql
SELECT c.name, o.total, l.event_count
FROM postgres.public.customers c
JOIN iceberg.warehouse.orders o ON c.id = o.customer_id
JOIN elasticsearch.logs.events l ON c.id = l.user_id
WHERE o.order_date > DATE '2025-01-01';
```

**Performance features:**
- Cost-based optimizer with table/column statistics.
- Dynamic filtering (push predicate from build side of join to probe side).
- Fault-tolerant execution (retry failed tasks, exchange spooling to disk).
- Connector-level pushdown (predicate, projection, aggregation, limit, topN).

**Iceberg integration:** Full support for Iceberg tables including time travel, hidden partitioning, schema evolution, and file pruning via manifest statistics.

### 4.2 Apache Spark SQL

Spark SQL is the SQL interface to Apache Spark, operating on DataFrames and Datasets.

**Strengths for data lakes:**
- Native support for Iceberg, Delta, and Hudi as table formats.
- Batch and streaming (Structured Streaming) in a unified API.
- UDF support (Python, Scala, Java) for custom transformations.
- Adaptive Query Execution (AQE): runtime optimization (coalesce shuffle partitions, switch join strategy, skew handling).
- Columnar execution with Tungsten memory management.

**Spark + Iceberg example:**

```python
spark.sql("""
    CREATE TABLE catalog.db.events (
        event_id BIGINT,
        event_time TIMESTAMP,
        payload STRING
    )
    USING iceberg
    PARTITIONED BY (days(event_time))
    TBLPROPERTIES (
        'write.target-file-size-bytes' = '536870912',
        'write.metadata.compression-codec' = 'gzip'
    )
""")

# Time travel query
df = spark.read.option("as-of-timestamp", "2025-01-15 00:00:00").table("catalog.db.events")
```

### 4.3 DuckDB

DuckDB is an in-process OLAP database optimized for analytical queries on a single machine.

**Data lake relevance:**
- Reads Parquet, Iceberg, Delta Lake, and CSV directly from S3/GCS/Azure.
- Zero-copy integration with Pandas and Arrow.
- Vectorized execution engine with excellent single-node performance.
- No server, no cluster — runs embedded in Python, R, Node.js, Java, CLI.

**Use cases:** Local development against lake data, data exploration, CI/CD testing of SQL transformations, edge analytics.

```sql
-- DuckDB reading Iceberg from S3
INSTALL iceberg;
LOAD iceberg;

SELECT * FROM iceberg_scan('s3://bucket/warehouse/db/events')
WHERE event_time >= '2025-01-01';
```

### 4.4 Serverless Engines: Athena and BigQuery

**Amazon Athena:** Serverless Trino-based engine querying data directly in S3. Pay per query (per TB scanned). Supports Iceberg, Delta, Hudi. Integrates with AWS Glue Catalog. No infrastructure to manage.

**BigQuery:** Google's serverless warehouse with native support for external tables on GCS. BigLake extends this with fine-grained access control over external data. Supports Iceberg tables (BigLake Metastore). Slot-based pricing or on-demand (per TB scanned).

### 4.5 Dremio

Dremio is a lakehouse platform built around Apache Arrow and Iceberg:

- **Reflections:** Materialized acceleration structures (aggregation reflections, raw reflections) automatically routed by the optimizer. Queries hit reflections without user awareness.
- **Apache Arrow Flight:** High-performance data transfer protocol replacing JDBC/ODBC for analytics.
- **Nessie integration:** Git-like catalog for branching, tagging, and merging table metadata.

### 4.6 Query Federation Patterns

**Hub-and-spoke:** A single engine (Trino) connects to all data sources. Simple, but the engine must handle all optimizations.

**Materialized integration:** Federated queries populate a curated zone; downstream consumers query only the lake. Better performance, higher latency.

**Polyglot persistence with virtual layer:** A semantic layer (dbt metrics, Dremio virtual datasets) abstracts physical storage. Consumers query logical entities; the layer routes to the optimal engine.

---

## 5. Data Ingestion into Lakes

### 5.1 Batch Ingestion

**Spark batch ingestion:**

```python
# Read from JDBC source, write to Iceberg
df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:postgresql://host:5432/db") \
    .option("dbtable", "orders") \
    .option("fetchsize", "10000") \
    .load()

df.writeTo("catalog.bronze.orders") \
    .option("write-format", "parquet") \
    .option("target-file-size-bytes", "536870912") \
    .append()
```

**Apache Airflow orchestration:**

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(schedule="@daily", start_date=datetime(2025, 1, 1), catchup=True)
def ingest_orders():
    @task
    def extract(ds=None):
        # Extract partition for execution date
        ...

    @task
    def load_to_lake(data, ds=None):
        # Write to bronze zone partitioned by date
        ...

    data = extract()
    load_to_lake(data)
```

**AWS Glue:** Serverless Spark with crawlers for automatic schema discovery. Glue ETL jobs read from RDS, DynamoDB, or S3, transform, and write to Iceberg tables registered in the Glue Catalog.

### 5.2 Streaming Ingestion

**Kafka to Iceberg (via Flink):**

```java
// Flink SQL: Kafka source → Iceberg sink
CREATE TABLE kafka_events (
    event_id BIGINT,
    event_time TIMESTAMP(3),
    payload STRING,
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'events',
    'properties.bootstrap.servers' = 'broker:9092',
    'format' = 'json'
);

CREATE TABLE iceberg_events (
    event_id BIGINT,
    event_time TIMESTAMP(3),
    payload STRING
) WITH (
    'connector' = 'iceberg',
    'catalog-name' = 'lakehouse',
    'catalog-type' = 'rest',
    'uri' = 'http://iceberg-rest:8181'
);

INSERT INTO iceberg_events SELECT * FROM kafka_events;
```

**Spark Structured Streaming to Delta:**

```python
spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "broker:9092") \
    .option("subscribe", "events") \
    .load() \
    .selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*") \
    .writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "s3://bucket/checkpoints/events") \
    .option("path", "s3://bucket/bronze/events") \
    .trigger(processingTime="1 minute") \
    .start()
```

### 5.3 CDC to Data Lake

**Debezium → Kafka → Iceberg pipeline:**

1. Debezium captures row-level changes from PostgreSQL/MySQL WAL.
2. Changes flow to Kafka topics (one per table) in Debezium envelope format.
3. Flink or Spark consumes the CDC stream and applies upserts to Iceberg/Hudi tables.

```sql
-- Flink: Apply CDC upserts to Iceberg
CREATE TABLE cdc_orders (
    order_id BIGINT,
    status STRING,
    amount DECIMAL(10,2),
    updated_at TIMESTAMP(3),
    PRIMARY KEY (order_id) NOT ENFORCED
) WITH (
    'connector' = 'kafka',
    'topic' = 'dbserver.public.orders',
    'format' = 'debezium-json'
);

-- UPSERT into Iceberg (merge-on-read)
INSERT INTO iceberg_orders
SELECT order_id, status, amount, updated_at FROM cdc_orders;
```

### 5.4 File-Based Ingestion

**S3 event-driven ingestion:**

1. Source system drops files into `s3://landing/source-name/YYYY/MM/DD/`.
2. S3 Event Notification triggers a Lambda or SQS message.
3. A processing job (Step Functions + Glue, or Airflow) validates the file, applies schema, and writes to the bronze zone.
4. Original file is moved to an archive prefix or deleted per retention policy.

**Landing zone patterns:**
- Idempotent processing: use file name as deduplication key.
- Quarantine: files that fail validation move to a dead-letter prefix with error metadata.
- Manifest files: a source system writes a `_MANIFEST` file listing all files in a delivery batch. Processing waits for the manifest before starting.

### 5.5 Schema Enforcement at Ingestion

**Schema registry integration:** Apache Avro schemas registered in Confluent Schema Registry or AWS Glue Schema Registry enforce structure at the Kafka producer level. Consumers can trust schema compatibility guarantees (backward, forward, full).

**Table format enforcement:** Iceberg and Delta reject writes that violate the table schema (wrong types, missing required columns). This acts as a gate between landing and bronze zones.

**Data contracts:** Formalized agreements between producers and consumers specifying:
- Schema (fields, types, nullability).
- Freshness SLA (data arrives within N minutes).
- Quality expectations (completeness, uniqueness, valid ranges).
- Evolution rules (additive changes allowed, breaking changes require versioning).

---

## 6. Data Organization

### 6.1 Partitioning Strategies

**Date-based partitioning:** Most common for event data. Partition by year/month/day or year/month/day/hour depending on data volume and query patterns.

```
s3://bucket/bronze/events/
├── year=2025/month=01/day=15/hour=00/
├── year=2025/month=01/day=15/hour=01/
└── ...
```

**Hash-based partitioning:** Distributes data evenly across N buckets based on a hash of a key column. Useful when no natural time dimension exists or when avoiding hot partitions.

```sql
-- Iceberg bucket partitioning
CREATE TABLE users (
    user_id BIGINT,
    name STRING,
    email STRING
)
USING iceberg
PARTITIONED BY (bucket(16, user_id));
```

**Hybrid partitioning:** Combine temporal and hash-based strategies. Partition by date for time-range pruning, bucket by entity ID within each date partition for join efficiency.

**Z-ordering / space-filling curves:** (Delta Lake OPTIMIZE ZORDER, Iceberg sort-order) Colocates related data across multiple dimensions within files. Enables pruning on multiple columns simultaneously without explicit multi-column partitioning.

### 6.2 File Sizing Optimization

**The small file problem:** Streaming ingestion creates many small files (KB to low MB). Thousands of small files degrade query performance because:
- Each file requires metadata lookup (list operations).
- Columnar formats have fixed overhead per file (footer, statistics).
- Task scheduling overhead exceeds data processing time.

**Target file sizes:**
- Parquet: 256 MB to 1 GB per file.
- ORC: 256 MB per stripe, multiple stripes per file.
- Iceberg default target: 512 MB.

**Compaction strategies:**
- **Scheduled compaction:** Periodic jobs (hourly/daily) rewrite small files into larger ones.
- **Inline compaction:** Hudi MoR compaction triggered after N delta commits.
- **Bin-pack:** Combine small files without sorting. Fast, preserves existing order.
- **Sort compaction:** Rewrite and sort by specified columns. Improves query pruning but more expensive.

### 6.3 Folder Structure Conventions

```
s3://data-lake-{env}/
├── landing/                    # Transient incoming data
│   └── {source}/{date}/
├── bronze/                     # Raw, immutable, optimized format
│   └── {domain}/{table}/       # Iceberg/Delta managed
├── silver/                     # Cleaned, conformed, joined
│   └── {domain}/{entity}/
├── gold/                       # Business-ready, aggregated
│   └── {use-case}/{dataset}/
├── sandbox/                    # Experimentation
│   └── {user}/{experiment}/
└── _metadata/                  # Catalogs, schemas, configs
    ├── schemas/
    └── quality-rules/
```

### 6.4 Metadata Catalogs

**Hive Metastore:** Legacy standard. Stores table metadata (schema, partitions, location) in a relational database (MySQL/PostgreSQL). Widely supported but limited to Hive-style partitioning.

**AWS Glue Data Catalog:** Managed Hive-compatible metastore. Integrates with Athena, Spark, Redshift Spectrum. Supports Iceberg table registration. Crawlers auto-discover schemas.

**Nessie:** Git-like catalog for Iceberg tables. Enables branching (create a branch, experiment, merge or discard), tagging (mark production snapshots), and multi-table transactions. Used with Dremio and Spark.

**Unity Catalog (Databricks):** Unified governance layer across Delta, Iceberg (via UniForm), ML models, and notebooks. Fine-grained access control, lineage, and auditing.

### 6.5 Naming Conventions

- Environments: `prod`, `staging`, `dev` as bucket suffix or top-level prefix.
- Domains: Business domain names (not technical team names): `finance`, `marketing`, `logistics`.
- Tables: Snake_case, plural nouns: `customer_orders`, `page_views`, `device_telemetry`.
- Partitions: `key=value` format (Hive-style) or Iceberg hidden partitions.
- Timestamps: ISO 8601 in UTC: `2025-05-07T14:30:00Z`.

---

## 7. Security Architecture

### 7.1 IAM Policies for Data Lakes

**Principle of least privilege:** Every identity (user, service, role) gets only the permissions required for its specific function. No wildcards on resource ARNs in production.

**Service roles pattern:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SparkJobReadBronze",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::datalake-prod-bronze",
        "arn:aws:s3:::datalake-prod-bronze/*"
      ],
      "Condition": {
        "StringLike": {
          "s3:prefix": ["events/*", "users/*"]
        }
      }
    },
    {
      "Sid": "SparkJobWriteSilver",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::datalake-prod-silver/processed_events/*"
    }
  ]
}
```

**Role chaining for cross-account access:** Data producers in account A assume a role in the lake account B to write data. The role trust policy restricts which external principals can assume it.

**Permission boundaries:** Cap the maximum permissions a role can ever receive, regardless of attached policies. Prevents privilege escalation through policy attachment.

**Condition keys for defense in depth:**
- `aws:SourceVpc` / `aws:SourceVpce`: Restrict access to specific VPCs/endpoints.
- `s3:x-amz-server-side-encryption`: Require encryption on all PUTs.
- `aws:PrincipalOrgID`: Limit access to identities within the AWS Organization.

### 7.2 Encryption

**Server-Side Encryption (SSE):**

| Type | Key Management | Use Case |
|---|---|---|
| SSE-S3 | AWS manages keys entirely | Default, simplest |
| SSE-KMS | Customer-managed KMS key | Audit key usage, rotation control, cross-account sharing |
| SSE-C | Customer provides key per request | Maximum control, key never stored by AWS |

**Client-Side Encryption:** Data encrypted before upload. AWS never sees plaintext. Required for:
- Zero-trust environments where the cloud provider is not trusted.
- Regulatory requirements mandating end-to-end encryption.
- Multi-cloud scenarios where keys must be portable.

**Encryption in transit:** TLS 1.2+ enforced via bucket policy condition:

```json
{
  "Condition": {
    "Bool": {"aws:SecureTransport": "false"}
  },
  "Effect": "Deny",
  "Action": "s3:*",
  "Resource": "arn:aws:s3:::datalake-prod-*/*"
}
```

**KMS key policy for data lake:**

```json
{
  "Statement": [
    {
      "Sid": "AllowLakeAdminFullControl",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::111111111111:role/LakeAdmin"},
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "AllowSparkDecrypt",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::111111111111:role/SparkJobRole"},
      "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
      "Resource": "*"
    }
  ]
}
```

### 7.3 Network Security

**VPC Endpoints (Gateway):** S3 gateway endpoint keeps traffic within the AWS network. No internet traversal, no NAT gateway costs. Route table entries direct S3-bound traffic through the endpoint.

**VPC Endpoints (Interface):** For services like KMS, Glue, STS. Creates ENIs within the VPC with private IP addresses.

**Endpoint policies:** Restrict which buckets and actions are accessible through the endpoint:

```json
{
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::datalake-prod-*",
        "arn:aws:s3:::datalake-prod-*/*"
      ]
    }
  ]
}
```

**Private Link (Azure/GCS):** Similar concept — traffic stays on the provider backbone, never traversing the public internet.

**Network segmentation:** Processing clusters (Spark, Trino) run in private subnets with no internet access. Dependencies pulled from internal mirrors. Egress explicitly controlled via security groups and NACLs.

### 7.4 Access Control Models

**Bucket policies:** Resource-based policies attached to S3 buckets. Control who (principal) can do what (action) on which objects (resource) under which conditions.

**AWS Lake Formation:** Fine-grained access control layer on top of the Glue Catalog:
- Column-level security: restrict access to specific columns.
- Row-level security: filter rows based on conditions.
- Cell-level security: mask specific cell values.
- Tag-based access control (LF-TBAC): assign tags to databases/tables/columns, grant permissions based on tags.
- Data filters: combine column and row filters into reusable permission objects.

```
# Lake Formation grant example
Database: silver
Table: customer_orders
Columns: [order_id, product, amount]  # Excludes PII columns
Row filter: region = 'EU'             # Analyst only sees EU data
Grantee: arn:aws:iam::111111111111:role/EUAnalystRole
```

**Apache Ranger:** Open-source fine-grained authorization for Hadoop ecosystem. Policies defined per service (HDFS, Hive, Spark, Kafka). Integrates with Trino via plugin. Centralized audit logging.

**Column masking and row filtering:** Dynamically applied at query time. The physical data remains unmasked; access control injects transformations:
- Hash masking: `SHA256(email)` for analytics that need uniqueness without PII.
- Nulling: sensitive columns return NULL for unauthorized users.
- Date truncation: birthdate becomes birth year only.
- Regex redaction: partial credit card number `****-****-****-1234`.

---

## 8. Data Lake Security Threats

### 8.1 Bucket Misconfigurations

The most common and impactful vulnerability. Public bucket exposure has caused hundreds of major data breaches.

**Attack vectors:**
- Bucket policy with `"Principal": "*"` and no conditions.
- ACL grants to `AllUsers` or `AuthenticatedUsers` groups.
- Static website hosting enabled on a data bucket.
- Block Public Access settings disabled at account or bucket level.

**Detection:**
- AWS Config rule: `s3-bucket-public-read-prohibited`, `s3-bucket-public-write-prohibited`.
- AWS Access Analyzer: identifies resources shared with external principals.
- Continuous scanning with tools like Prowler, ScoutSuite, or CloudSploit.

**Prevention:**
- Enable S3 Block Public Access at the account level (all four settings).
- SCPs (Service Control Policies) that deny `s3:PutBucketPolicy` with public principal.
- Automated remediation via EventBridge + Lambda: if a bucket becomes public, immediately revert the policy.

### 8.2 Credential Theft and IAM Role Compromise

**IMDS exploitation (Instance Metadata Service):** EC2 instances with IAM roles expose temporary credentials via the metadata service (169.254.169.254). SSRF vulnerabilities in applications running on these instances can harvest these credentials.

- **Mitigation:** Enforce IMDSv2 (require session tokens for metadata access). Restrict metadata endpoint via iptables or security groups. Use container credential providers instead of instance roles where possible.

**Leaked credentials:**
- Access keys committed to git repositories.
- Credentials in CI/CD logs, error messages, or stack traces.
- Credentials in environment variables of containerized workloads accessible via process listing.

**Assume role abuse:** An attacker compromises a low-privilege identity that has `sts:AssumeRole` permission on a high-privilege lake role. Chained role assumptions can escalate from developer access to lake admin.

**Mitigation:**
- External ID and MFA conditions on role trust policies.
- CloudTrail monitoring for unusual AssumeRole patterns.
- Short session durations (1 hour maximum for sensitive roles).
- Credential rotation automation.

### 8.3 Data Exfiltration

**Bulk download:** An attacker with read access copies large volumes of data to external storage. Without egress controls, this is difficult to detect.

**Detection mechanisms:**
- CloudTrail data events: monitor `GetObject` volume by principal.
- VPC Flow Logs: detect unusual outbound data volume.
- S3 access logs: analyze download patterns (time, volume, IP).
- Macie: identify sensitive data being accessed abnormally.

**DNS tunneling:** Encoding data in DNS queries to exfiltrate past network controls. Data lake environments with DNS resolution to the internet are vulnerable.

**S3 presigned URL abuse:** A legitimate internal user generates presigned URLs and shares them externally. The URL grants time-limited access without authentication.

**Prevention:**
- Deny `s3:GetObject` except from known VPC endpoints.
- Bucket policies restricting access to specific VPCs/IPs.
- DLP monitoring on egress paths.
- Presigned URL generation restricted to specific roles with short expiry.
- AWS S3 Object Lock for critical data (prevents deletion/modification but not reading).

### 8.4 Insider Threats

**Scenarios:**
- Data engineer with broad lake access exports customer data.
- Analyst queries PII columns unnecessarily and saves results locally.
- Admin modifies lake policies to grant themselves broader access.

**Controls:**
- Separation of duties: the team managing IAM policies should not be the team using the data.
- Just-in-time access: temporary elevated permissions via tools like AWS SSO Permission Sets with time limits.
- Mandatory query logging: all Athena/Trino/Spark queries logged with full SQL text.
- Anomaly detection: ML-based analysis of query patterns to detect unusual access (e.g., first time an analyst queries the PII schema).
- Data loss prevention at the endpoint: MDM policies preventing bulk downloads to unmanaged devices.

### 8.5 Supply Chain: Malicious Data Ingestion

**Threat:** An attacker compromises a data source or the ingestion pipeline to inject malicious data:
- Crafted Parquet files exploiting deserialization vulnerabilities in query engines.
- SQL injection via data values that propagate to downstream SQL generation.
- CSV injection (formula injection) in files consumed by spreadsheet tools.
- Oversized files designed to cause OOM in processing jobs (resource exhaustion).

**Mitigations:**
- Input validation at the landing zone (schema validation, file size limits, format verification).
- Sandboxed processing: ingestion jobs run with minimal privileges and resource limits.
- Content scanning: antivirus/anti-malware on uploaded files.
- Integrity verification: checksums provided by source systems, validated before processing.
- Immutable bronze zone: raw data cannot be modified after ingestion, enabling forensic analysis.

### 8.6 Privilege Escalation in Lake Platforms

**Lake Formation privilege escalation:**
- A user with `DESCRIBE` permission on a database discovers table names and schemas, then social-engineers broader access.
- A service role with `ALTER` permission on tables can change the table location to point at a different S3 path, potentially accessing unauthorized data.
- The `DATA_LOCATION_ACCESS` permission allows registering new S3 paths. An attacker could register a path containing prepared malicious data.

**Glue Catalog manipulation:**
- Modifying a table's `SerDe` (serialization/deserialization) library to execute arbitrary code during query processing.
- Changing partition locations to point at attacker-controlled S3 buckets.

**Mitigations:**
- Restrict `ALTER TABLE`, `CREATE TABLE`, and catalog modification permissions to CI/CD pipelines only.
- Monitor Glue Catalog changes via CloudTrail.
- Validate table locations against an allowlist of blessed S3 prefixes.
- Use Lake Formation's governed tables which restrict location changes.

---

## 9. Governance and Compliance

### 9.1 Data Classification in Lakes

Establish a classification taxonomy applied to all data assets:

| Level | Label | Examples | Controls |
|---|---|---|---|
| 1 | Public | Marketing content, public APIs | No restrictions |
| 2 | Internal | Business metrics, internal reports | Authentication required |
| 3 | Confidential | Customer data, financial records | Role-based access, encryption |
| 4 | Restricted | PII, PHI, payment data, secrets | Column masking, audit logging, DLP |

Classification should be:
- **Automated:** Use discovery tools to scan and tag data assets.
- **Inherited:** A derived table inherits the highest classification of its source tables.
- **Enforced:** Access controls are derived from classification level (LF-TBAC maps tags to permissions).
- **Auditable:** Classification decisions are logged with justification.

### 9.2 PII Discovery

**Amazon Macie:** ML-powered service that scans S3 objects for PII (names, addresses, SSNs, credit cards, health data). Produces findings with severity, location (bucket/key/offset), and suggested remediation.

**Google Cloud DLP API:** Inspects, classifies, and de-identifies sensitive data. Supports structured and unstructured data. InfoTypes detect patterns (email, phone, custom regex). Integrated with BigQuery and GCS.

**Custom PII scanning pipeline:**

```python
# Pseudocode: PII scanner for incoming Parquet files
def scan_for_pii(parquet_path: str) -> list[Finding]:
    df = read_parquet(parquet_path)
    findings = []

    for column in df.columns:
        sample = df[column].dropna().sample(min(1000, len(df)))

        # Regex patterns
        if matches_email_pattern(sample):
            findings.append(Finding(column, "EMAIL", "HIGH"))
        if matches_ssn_pattern(sample):
            findings.append(Finding(column, "SSN", "CRITICAL"))
        if matches_phone_pattern(sample):
            findings.append(Finding(column, "PHONE", "MEDIUM"))

        # ML-based NER for names, addresses
        entities = run_ner_model(sample)
        if entity_density_above_threshold(entities, "PERSON"):
            findings.append(Finding(column, "PERSON_NAME", "HIGH"))

    return findings
```

### 9.3 Access Audit Trails

**AWS CloudTrail:** Records all API calls (management events) and optionally data events (S3 GetObject, PutObject). Data events at scale generate massive volumes — use selective logging (specific buckets/prefixes) or sampling.

**CloudTrail Lake:** SQL-queryable storage for CloudTrail events. Enables investigation queries like:

```sql
SELECT
    userIdentity.arn,
    COUNT(*) as access_count,
    SUM(additionalEventData.bytesTransferred) as bytes_total
FROM cloudtrail_events
WHERE eventName = 'GetObject'
    AND resources[0].arn LIKE '%datalake-prod-silver/customer%'
    AND eventTime > '2025-04-01'
GROUP BY userIdentity.arn
ORDER BY bytes_total DESC;
```

**Google Cloud Audit Logs:** Admin activity logs (always on), data access logs (configurable per service). Exported to BigQuery for analysis.

**Azure Monitor:** Activity logs + diagnostic settings on storage accounts. Log Analytics workspace for querying.

**Centralized SIEM integration:** Forward audit logs to Splunk, Elastic, or a cloud SIEM (AWS Security Lake, Chronicle) for correlation with other security signals.

### 9.4 Retention Policies

**Zone-based retention:**
| Zone | Default Retention | Justification |
|---|---|---|
| Landing | 7 days | Transient, replayable from source |
| Bronze | 7 years | Regulatory (financial), audit trail |
| Silver | 3 years | Business analysis period |
| Gold | 1 year | Current operational data |
| Sandbox | 30 days | Experimentation only |

**Implementation:**
- S3 lifecycle rules for automated deletion after retention period.
- S3 Object Lock (Governance or Compliance mode) for immutable retention of regulated data.
- Iceberg snapshot expiration: `CALL catalog.system.expire_snapshots('db.table', TIMESTAMP '2025-01-01 00:00:00', 100)`.
- Delta Lake vacuum: `VACUUM table RETAIN 168 HOURS` (removes unreferenced files older than 7 days).

### 9.5 Legal Hold

When litigation is anticipated or active, a legal hold preserves all potentially relevant data regardless of normal retention policies.

**Implementation:**
- S3 Object Lock Legal Hold: prevents deletion/modification of specific objects until explicitly released.
- Suspend lifecycle rules on affected prefixes.
- Tag affected objects with legal hold metadata (case ID, hold date, custodian).
- Disable compaction and vacuum on affected tables to preserve all historical versions.

### 9.6 Data Subject Requests (GDPR Article 17 — Right to Erasure)

Finding and deleting specific records in a data lake is architecturally challenging because:
- Data is spread across multiple zones, tables, and file formats.
- Immutable bronze zone conflicts with deletion requirements.
- Columnar formats (Parquet) are not designed for single-record deletion.

**Approach:**

1. **Discovery:** Maintain a record locator index mapping subject IDs to all lake locations (zone, table, partition, file). Updated on ingestion.

2. **Deletion in table-format tables:** Use Iceberg/Delta/Hudi DELETE statements. Table formats handle this via rewriting affected files or adding deletion markers.

3. **Deletion in raw/bronze zone:** Options:
   - Rewrite affected Parquet files excluding the subject's records.
   - Crypto-shredding: encrypt PII with a per-subject key; "delete" by destroying the key.
   - Maintain a deletion registry; queries filter out deleted subjects at read time.

4. **Verification:** After deletion, scan affected locations to confirm no residual PII. Produce an audit certificate.

5. **Downstream propagation:** Trigger re-processing of derived tables that consumed the deleted data.

### 9.7 Cross-Border Data Residency

**Requirements:** GDPR (EU), LGPD (Brazil), PIPL (China), and others mandate data remain within specific jurisdictions.

**Implementation patterns:**
- **Regional buckets:** Separate S3 buckets per region, data routed based on subject's jurisdiction.
- **Replication controls:** CRR with bucket filters — only non-restricted data replicates cross-border.
- **Processing locality:** Compute clusters deployed in the same region as the data they process. No cross-region reads.
- **Metadata separation:** Even catalog metadata may be subject to residency requirements. Deploy regional Glue Catalogs or Hive Metastores.
- **Transfer mechanisms:** For legitimate cross-border needs, implement approved transfer mechanisms (SCCs, BCRs, adequacy decisions) and document them per data asset.

---

## 10. Lab Exercises

### Lab 1: Build a Complete Lakehouse (MinIO + Iceberg + Spark + Trino)

**Objective:** Deploy a fully functional lakehouse on local infrastructure, ingest data through all zones, and query with multiple engines.

**Architecture:**

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Data Source │────▶│  Spark Jobs  │────▶│    MinIO     │
│  (CSV/JSON)  │     │  (Ingestion) │     │  (S3-compat) │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                    ┌──────────────┐              │
                    │   Trino      │◀─────────────┤
                    │  (Query)     │              │
                    └──────────────┘     ┌────────┴──────┐
                                         │ Iceberg REST  │
                                         │   Catalog     │
                                         └───────────────┘
```

**Step 1: Docker Compose environment**

```yaml
version: '3.8'
services:
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: supersecret123
    volumes:
      - minio_data:/data

  iceberg-rest:
    image: tabulario/iceberg-rest:latest
    ports:
      - "8181:8181"
    environment:
      CATALOG_WAREHOUSE: s3://warehouse/
      CATALOG_IO__IMPL: org.apache.iceberg.aws.s3.S3FileIO
      CATALOG_S3_ENDPOINT: http://minio:9000
      AWS_ACCESS_KEY_ID: admin
      AWS_SECRET_ACCESS_KEY: supersecret123
      AWS_REGION: us-east-1

  spark:
    image: bitnami/spark:3.5
    ports:
      - "8080:8080"
      - "4040:4040"
    environment:
      SPARK_MODE: master
    volumes:
      - ./spark-jobs:/opt/spark-jobs

  trino:
    image: trinodb/trino:latest
    ports:
      - "8082:8080"
    volumes:
      - ./trino-config/catalog:/etc/trino/catalog

volumes:
  minio_data:
```

**Step 2: Trino catalog configuration**

```properties
# trino-config/catalog/iceberg.properties
connector.name=iceberg
iceberg.catalog.type=rest
iceberg.rest-catalog.uri=http://iceberg-rest:8181
iceberg.rest-catalog.warehouse=s3://warehouse/
hive.s3.endpoint=http://minio:9000
hive.s3.aws-access-key=admin
hive.s3.aws-secret-key=supersecret123
hive.s3.path-style-access=true
```

**Step 3: Create lakehouse zones with Spark**

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("LakehouseSetup") \
    .config("spark.sql.catalog.lakehouse", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.lakehouse.type", "rest") \
    .config("spark.sql.catalog.lakehouse.uri", "http://iceberg-rest:8181") \
    .config("spark.sql.catalog.lakehouse.io-impl", "org.apache.iceberg.aws.s3.S3FileIO") \
    .config("spark.sql.catalog.lakehouse.s3.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "admin") \
    .config("spark.hadoop.fs.s3a.secret.key", "supersecret123") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .getOrCreate()

# Create namespaces (zones)
spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.bronze")
spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.silver")
spark.sql("CREATE NAMESPACE IF NOT EXISTS lakehouse.gold")

# Create bronze table
spark.sql("""
    CREATE TABLE IF NOT EXISTS lakehouse.bronze.events (
        event_id BIGINT,
        event_time TIMESTAMP,
        user_id STRING,
        event_type STRING,
        payload STRING
    )
    USING iceberg
    PARTITIONED BY (days(event_time))
    TBLPROPERTIES (
        'write.target-file-size-bytes' = '134217728',
        'write.metadata.compression-codec' = 'gzip'
    )
""")

# Ingest sample data
from pyspark.sql.functions import current_timestamp, lit, expr
import random

events = spark.range(100000).selectExpr(
    "id as event_id",
    "current_timestamp() - make_interval(0, 0, 0, cast(rand() * 30 as int), 0, 0, 0) as event_time",
    "concat('user_', cast(cast(rand() * 1000 as int) as string)) as user_id",
    "array('click', 'view', 'purchase', 'signup')[cast(rand() * 4 as int)] as event_type",
    "'{\"page\": \"home\", \"duration\": ' || cast(cast(rand() * 300 as int) as string) || '}' as payload"
)

events.writeTo("lakehouse.bronze.events").append()

# Silver: cleaned and enriched
spark.sql("""
    CREATE TABLE IF NOT EXISTS lakehouse.silver.events_cleaned AS
    SELECT
        event_id,
        event_time,
        user_id,
        event_type,
        from_json(payload, 'page STRING, duration INT') as parsed_payload,
        current_timestamp() as processed_at
    FROM lakehouse.bronze.events
    WHERE event_type IS NOT NULL
""")

# Gold: aggregated for dashboards
spark.sql("""
    CREATE TABLE IF NOT EXISTS lakehouse.gold.daily_event_summary AS
    SELECT
        date_trunc('day', event_time) as event_date,
        event_type,
        count(*) as event_count,
        count(distinct user_id) as unique_users
    FROM lakehouse.silver.events_cleaned
    GROUP BY 1, 2
""")
```

**Step 4: Query with Trino**

```sql
-- Time travel: query 1 hour ago
SELECT * FROM lakehouse.bronze.events
FOR TIMESTAMP AS OF TIMESTAMP '2025-05-07 12:00:00';

-- Snapshot history
SELECT * FROM lakehouse.bronze."events$snapshots";

-- Cross-zone join
SELECT g.event_date, g.event_count, s.parsed_payload.page
FROM lakehouse.gold.daily_event_summary g
JOIN lakehouse.silver.events_cleaned s
    ON date_trunc('day', s.event_time) = g.event_date
WHERE g.event_type = 'purchase'
LIMIT 100;
```

**Step 5: Compaction exercise**

```python
# Simulate small file problem (100 micro-batches)
for i in range(100):
    small_batch = spark.range(100).selectExpr(
        f"{i * 100} + id as event_id",
        "current_timestamp() as event_time",
        "'user_999' as user_id",
        "'micro_event' as event_type",
        "'{}' as payload"
    )
    small_batch.writeTo("lakehouse.bronze.events").append()

# Check file count before compaction
spark.sql("SELECT * FROM lakehouse.bronze.\"events$files\"").count()

# Run compaction
spark.sql("""
    CALL lakehouse.system.rewrite_data_files(
        table => 'bronze.events',
        strategy => 'binpack',
        options => map('target-file-size-bytes', '134217728', 'min-file-size-bytes', '67108864')
    )
""")

# Check file count after compaction
spark.sql("SELECT * FROM lakehouse.bronze.\"events$files\"").count()
```

---

### Lab 2: Fine-Grained Access Control with AWS Lake Formation

**Objective:** Implement column-level security, row filtering, and cell-level masking on an Iceberg table using Lake Formation.

**Prerequisites:** AWS account with Lake Formation configured, Glue Catalog with Iceberg tables, IAM roles for different user personas.

**Step 1: Register data lake locations**

```bash
# Register S3 locations with Lake Formation
aws lakeformation register-resource \
    --resource-arn "arn:aws:s3:::datalake-prod-silver" \
    --use-service-linked-role

aws lakeformation register-resource \
    --resource-arn "arn:aws:s3:::datalake-prod-gold" \
    --use-service-linked-role
```

**Step 2: Create data filters**

```bash
# Column-level + row-level filter for EU analysts
aws lakeformation create-data-cells-filter \
    --table-data '{
        "TableCatalogId": "111111111111",
        "DatabaseName": "silver",
        "TableName": "customers",
        "Name": "eu_analysts_filter",
        "RowFilter": {
            "FilterExpression": "region = '\''EU'\''"
        },
        "ColumnNames": ["customer_id", "name", "region", "total_orders"],
        "ColumnWildcard": null
    }'

# Masking filter: hash email, hide full SSN
aws lakeformation create-data-cells-filter \
    --table-data '{
        "TableCatalogId": "111111111111",
        "DatabaseName": "silver",
        "TableName": "customers",
        "Name": "masked_pii_filter",
        "RowFilter": {"AllRowsWildcard": {}},
        "ColumnNames": ["customer_id", "name", "region", "masked_email", "total_orders"],
        "ColumnWildcard": null
    }'
```

**Step 3: Grant permissions with filters**

```bash
# Grant EU analyst role access with filter
aws lakeformation grant-permissions \
    --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::111111111111:role/EUAnalystRole"}' \
    --resource '{
        "DataCellsFilter": {
            "TableCatalogId": "111111111111",
            "DatabaseName": "silver",
            "TableName": "customers",
            "Name": "eu_analysts_filter"
        }
    }' \
    --permissions '["SELECT"]'

# Grant data science role access with masked PII
aws lakeformation grant-permissions \
    --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::111111111111:role/DataScienceRole"}' \
    --resource '{
        "DataCellsFilter": {
            "TableCatalogId": "111111111111",
            "DatabaseName": "silver",
            "TableName": "customers",
            "Name": "masked_pii_filter"
        }
    }' \
    --permissions '["SELECT"]'
```

**Step 4: Tag-based access control (LF-TBAC)**

```bash
# Create LF-Tags
aws lakeformation create-lf-tag \
    --tag-key "classification" \
    --tag-values '["public", "internal", "confidential", "restricted"]'

aws lakeformation create-lf-tag \
    --tag-key "domain" \
    --tag-values '["finance", "marketing", "engineering", "hr"]'

# Assign tags to resources
aws lakeformation add-lf-tags-to-resource \
    --resource '{"Table": {"DatabaseName": "silver", "Name": "customers"}}' \
    --lf-tags '[{"TagKey": "classification", "TagValues": ["confidential"]}, {"TagKey": "domain", "TagValues": ["marketing"]}]'

# Grant permissions via tags
aws lakeformation grant-permissions \
    --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::111111111111:role/MarketingAnalystRole"}' \
    --resource '{
        "LFTagPolicy": {
            "ResourceType": "TABLE",
            "Expression": [
                {"TagKey": "classification", "TagValues": ["internal", "public"]},
                {"TagKey": "domain", "TagValues": ["marketing"]}
            ]
        }
    }' \
    --permissions '["SELECT", "DESCRIBE"]'
```

**Step 5: Verification and audit**

```sql
-- As EU Analyst (via Athena, assuming EUAnalystRole)
-- Should only see EU customers, no email/SSN columns
SELECT * FROM silver.customers LIMIT 10;

-- As Data Science (via Athena, assuming DataScienceRole)
-- Should see all regions but with masked email
SELECT * FROM silver.customers LIMIT 10;

-- Verify in CloudTrail: filter for Lake Formation events
-- Look for GetDataAccess, GrantPermissions, BatchGetPartition events
```

---

### Lab 3: Data Lake Security Assessment Methodology (Pentest Perspective)

**Objective:** Develop a systematic methodology for assessing data lake security posture from an offensive security perspective.

**Phase 1: Reconnaissance**

```bash
# Enumerate S3 buckets via DNS/certificate transparency
# (Authorized scope only — document authorization before proceeding)

# Enumerate buckets from AWS account access
aws s3 ls 2>/dev/null

# Check for public buckets
aws s3api get-bucket-policy-status --bucket $BUCKET
aws s3api get-bucket-acl --bucket $BUCKET
aws s3api get-public-access-block --bucket $BUCKET

# Enumerate Glue catalog
aws glue get-databases
aws glue get-tables --database-name silver
aws glue get-table --database-name silver --name customers

# Check Lake Formation permissions
aws lakeformation list-permissions \
    --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::111111111111:role/CurrentRole"}'

# Enumerate IAM roles with S3/Glue access
aws iam list-roles --query "Roles[?contains(to_string(AssumeRolePolicyDocument), 's3')]"
```

**Phase 2: Access Testing**

```bash
# Test bucket access from different principals
# For each role discoverable in the account:

# Can we list objects?
aws s3 ls s3://$BUCKET/ --recursive --summarize

# Can we read sensitive prefixes?
aws s3 cp s3://$BUCKET/silver/customers/part-00000.parquet /tmp/test.parquet

# Can we write to landing zone?
echo "test" | aws s3 cp - s3://$BUCKET/landing/test.txt

# Test cross-account access
aws sts assume-role --role-arn arn:aws:iam::222222222222:role/CrossAccountLakeRole \
    --role-session-name pentest

# Test VPC endpoint bypass
# From an instance outside the data VPC, attempt S3 access
# Should be denied if bucket policy restricts to VPC endpoint
```

**Phase 3: Privilege Escalation Testing**

```bash
# Check for overly permissive Lake Formation grants
aws lakeformation list-permissions \
    --resource-type TABLE \
    --query "PrincipalResourcePermissions[?contains(Permissions, 'ALL')]"

# Check for roles that can modify Glue catalog
aws iam simulate-principal-policy \
    --policy-source-arn arn:aws:iam::111111111111:role/$ROLE \
    --action-names glue:UpdateTable glue:CreateTable glue:DeleteTable

# Test SerDe injection (if we can modify table properties)
# WARNING: Only in authorized test environments
aws glue update-table --database-name test_db --table-input '{
    "Name": "test_table",
    "StorageDescriptor": {
        "SerdeInfo": {
            "SerializationLibrary": "org.apache.hadoop.hive.serde2.OpenCSVSerde"
        },
        "Location": "s3://attacker-controlled-bucket/data/"
    }
}'

# Check for PassRole permissions that enable escalation
aws iam simulate-principal-policy \
    --policy-source-arn arn:aws:iam::111111111111:role/$ROLE \
    --action-names iam:PassRole \
    --resource-arns arn:aws:iam::111111111111:role/GlueServiceRole
```

**Phase 4: Data Exposure Assessment**

```python
# Automated PII exposure check across accessible tables
import boto3
import pyarrow.parquet as pq
import re

glue = boto3.client('glue')
s3 = boto3.client('s3')

PII_PATTERNS = {
    'email': re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
    'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
}

def assess_table_exposure(database: str, table: str) -> dict:
    """Check a single table for PII exposure."""
    table_info = glue.get_table(DatabaseName=database, Name=table)
    location = table_info['Table']['StorageDescriptor']['Location']

    # Sample first partition/file
    bucket, prefix = parse_s3_url(location)
    objects = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)

    if not objects.get('Contents'):
        return {'table': f'{database}.{table}', 'status': 'empty'}

    key = objects['Contents'][0]['Key']
    s3.download_file(bucket, key, '/tmp/sample.parquet')

    pf = pq.read_table('/tmp/sample.parquet')
    findings = []

    for col in pf.column_names:
        sample_values = pf.column(col).to_pylist()[:100]
        for pattern_name, pattern in PII_PATTERNS.items():
            matches = sum(1 for v in sample_values
                        if v and isinstance(v, str) and pattern.search(v))
            if matches > 5:  # Threshold
                findings.append({
                    'column': col,
                    'pii_type': pattern_name,
                    'match_rate': matches / len(sample_values)
                })

    return {
        'table': f'{database}.{table}',
        'location': location,
        'findings': findings,
        'severity': 'CRITICAL' if any(f['pii_type'] in ('ssn', 'credit_card')
                                      for f in findings) else 'HIGH' if findings else 'LOW'
    }
```

**Phase 5: Report Template**

```markdown
# Data Lake Security Assessment Report

## Executive Summary
- Overall risk rating: [CRITICAL/HIGH/MEDIUM/LOW]
- Total findings: N
- Critical findings requiring immediate action: N

## Scope
- AWS Account: 111111111111
- Region: us-east-1
- Buckets assessed: [list]
- Date range: [UTC timestamps]
- Authorization reference: [ticket/document]

## Findings

### Finding 1: [Title]
- **Severity:** CRITICAL
- **CVSS:** 9.1 (AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:L/A:N)
- **CWE:** CWE-284 (Improper Access Control)
- **Description:** [What was found]
- **Evidence:** [Screenshots, API responses, timestamps]
- **Impact:** [What an attacker could achieve]
- **Remediation:**
  ```json
  // Bucket policy fix
  { ... }
  ```
- **Verification:** [How to confirm the fix works]
```

---

### Lab 4: Automated PII Scanning for Incoming Data

**Objective:** Build a production-grade pipeline that scans all incoming data for PII, quarantines violations, and produces actionable alerts.

**Architecture:**

```
┌──────────┐    ┌──────────┐    ┌─────────────┐    ┌──────────────┐
│  Landing │───▶│  S3 Event│───▶│  PII Scanner│───▶│   Decision   │
│   Zone   │    │  (SQS)   │    │  (Lambda/ECS)│    │              │
└──────────┘    └──────────┘    └─────────────┘    └──────┬───────┘
                                                          │
                                    ┌─────────────────────┼─────────────────────┐
                                    │                     │                     │
                              ┌─────▼─────┐       ┌──────▼──────┐      ┌──────▼──────┐
                              │   CLEAN   │       │ QUARANTINE  │      │   ALERT    │
                              │  (Bronze) │       │ (Restricted)│      │  (SNS/PD)  │
                              └───────────┘       └─────────────┘      └────────────┘
```

**Step 1: Infrastructure (Terraform)**

```hcl
resource "aws_sqs_queue" "pii_scan_queue" {
  name                       = "pii-scan-queue"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.pii_scan_dlq.arn
    maxReceiveCount     = 3
  })
}

resource "aws_s3_bucket_notification" "landing_notification" {
  bucket = aws_s3_bucket.landing.id

  queue {
    queue_arn     = aws_sqs_queue.pii_scan_queue.arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "landing/"
    filter_suffix = ".parquet"
  }
}

resource "aws_lambda_function" "pii_scanner" {
  function_name = "pii-scanner"
  runtime       = "python3.12"
  handler       = "scanner.handler"
  timeout       = 300
  memory_size   = 1024

  environment {
    variables = {
      QUARANTINE_BUCKET = aws_s3_bucket.quarantine.id
      BRONZE_BUCKET     = aws_s3_bucket.bronze.id
      ALERT_TOPIC_ARN   = aws_sns_topic.pii_alerts.arn
      SCAN_CONFIG_TABLE = aws_dynamodb_table.scan_config.name
    }
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.scanner_sg.id]
  }
}
```

**Step 2: Scanner implementation**

```python
"""PII Scanner Lambda — scans incoming Parquet files for sensitive data."""

import json
import os
import re
import hashlib
from datetime import datetime, timezone
from typing import Any

import boto3
import pyarrow.parquet as pq

s3 = boto3.client("s3")
sns = boto3.client("sns")
dynamodb = boto3.resource("dynamodb")

QUARANTINE_BUCKET = os.environ["QUARANTINE_BUCKET"]
BRONZE_BUCKET = os.environ["BRONZE_BUCKET"]
ALERT_TOPIC_ARN = os.environ["ALERT_TOPIC_ARN"]

# Pattern definitions
PII_DETECTORS = {
    "email": {
        "pattern": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "severity": "HIGH",
        "threshold": 0.1,  # 10% of sampled values match
    },
    "ssn": {
        "pattern": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "severity": "CRITICAL",
        "threshold": 0.05,
    },
    "credit_card": {
        "pattern": re.compile(r"\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        "severity": "CRITICAL",
        "threshold": 0.05,
    },
    "phone_us": {
        "pattern": re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
        "severity": "MEDIUM",
        "threshold": 0.15,
    },
    "ip_address": {
        "pattern": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "severity": "LOW",
        "threshold": 0.2,
    },
}

SAMPLE_SIZE = 1000


def handler(event: dict, context: Any) -> dict:
    """Process SQS messages containing S3 event notifications."""
    results = []

    for record in event["Records"]:
        body = json.loads(record["body"])
        for s3_record in body.get("Records", []):
            bucket = s3_record["s3"]["bucket"]["name"]
            key = s3_record["s3"]["object"]["key"]

            result = scan_file(bucket, key)
            results.append(result)

            if result["action"] == "quarantine":
                quarantine_file(bucket, key, result)
                send_alert(result)
            else:
                promote_to_bronze(bucket, key)

    return {"processed": len(results), "results": results}


def scan_file(bucket: str, key: str) -> dict:
    """Scan a single Parquet file for PII patterns."""
    local_path = f"/tmp/{hashlib.md5(key.encode()).hexdigest()}.parquet"
    s3.download_file(bucket, key, local_path)

    table = pq.read_table(local_path)
    total_rows = table.num_rows
    findings = []

    for col_name in table.column_names:
        column = table.column(col_name)

        # Only scan string columns
        if not str(column.type).startswith("string"):
            continue

        # Sample for efficiency
        values = column.to_pylist()[:SAMPLE_SIZE]
        non_null_values = [v for v in values if v is not None]

        if not non_null_values:
            continue

        for detector_name, config in PII_DETECTORS.items():
            matches = sum(
                1 for v in non_null_values if config["pattern"].search(str(v))
            )
            match_rate = matches / len(non_null_values)

            if match_rate >= config["threshold"]:
                findings.append({
                    "column": col_name,
                    "pii_type": detector_name,
                    "severity": config["severity"],
                    "match_rate": round(match_rate, 3),
                    "sample_size": len(non_null_values),
                    "estimated_affected_rows": int(match_rate * total_rows),
                })

    # Determine action
    max_severity = "NONE"
    for f in findings:
        if f["severity"] == "CRITICAL":
            max_severity = "CRITICAL"
            break
        elif f["severity"] == "HIGH" and max_severity != "CRITICAL":
            max_severity = "HIGH"

    action = "quarantine" if max_severity in ("CRITICAL", "HIGH") else "promote"

    return {
        "source": f"s3://{bucket}/{key}",
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "total_rows": total_rows,
        "findings": findings,
        "max_severity": max_severity,
        "action": action,
    }


def quarantine_file(bucket: str, key: str, scan_result: dict) -> None:
    """Move file to quarantine bucket with scan metadata."""
    quarantine_key = f"quarantine/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{key.split('/')[-1]}"

    # Copy to quarantine
    s3.copy_object(
        Bucket=QUARANTINE_BUCKET,
        Key=quarantine_key,
        CopySource={"Bucket": bucket, "Key": key},
        Metadata={
            "scan-result": json.dumps(scan_result),
            "original-location": f"s3://{bucket}/{key}",
            "quarantine-reason": f"PII detected: {scan_result['max_severity']}",
        },
        MetadataDirective="REPLACE",
    )

    # Delete from landing
    s3.delete_object(Bucket=bucket, Key=key)


def promote_to_bronze(bucket: str, key: str) -> None:
    """Move clean file to bronze zone."""
    bronze_key = key.replace("landing/", "bronze/", 1)

    s3.copy_object(
        Bucket=BRONZE_BUCKET,
        Key=bronze_key,
        CopySource={"Bucket": bucket, "Key": key},
    )

    s3.delete_object(Bucket=bucket, Key=key)


def send_alert(scan_result: dict) -> None:
    """Send alert for quarantined files."""
    message = {
        "source": scan_result["source"],
        "severity": scan_result["max_severity"],
        "findings": scan_result["findings"],
        "action": "File quarantined. Manual review required.",
        "timestamp": scan_result["scan_time"],
    }

    sns.publish(
        TopicArn=ALERT_TOPIC_ARN,
        Subject=f"[{scan_result['max_severity']}] PII Detected in Data Lake Ingestion",
        Message=json.dumps(message, indent=2),
    )
```

**Step 3: Testing the scanner**

```python
"""Test suite for PII scanner."""

import pyarrow as pa
import pyarrow.parquet as pq
import tempfile
import os

def create_test_file_with_pii() -> str:
    """Create a Parquet file containing various PII for testing."""
    data = {
        "user_id": list(range(100)),
        "name": [f"User {i}" for i in range(100)],
        "email": [f"user{i}@example.com" for i in range(100)],
        "ssn": [f"{100+i}-{10+i%90}-{1000+i}" for i in range(100)],
        "safe_field": [f"value_{i}" for i in range(100)],
        "ip_address": [f"192.168.1.{i%256}" for i in range(100)],
    }

    table = pa.table(data)
    path = tempfile.mktemp(suffix=".parquet")
    pq.write_table(table, path)
    return path


def create_clean_test_file() -> str:
    """Create a Parquet file with no PII."""
    data = {
        "metric_id": list(range(100)),
        "value": [i * 1.5 for i in range(100)],
        "category": [f"cat_{i % 5}" for i in range(100)],
        "timestamp": ["2025-05-07T00:00:00Z"] * 100,
    }

    table = pa.table(data)
    path = tempfile.mktemp(suffix=".parquet")
    pq.write_table(table, path)
    return path


# Integration test assertions:
# 1. File with PII → quarantined, alert sent
# 2. Clean file → promoted to bronze
# 3. Malformed file → dead-letter queue
# 4. Large file (>100MB) → processed within timeout
# 5. Column with partial PII (below threshold) → not flagged
```

**Step 4: Monitoring dashboard (CloudWatch)**

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["PII-Scanner", "FilesProcessed", {"stat": "Sum"}],
          ["PII-Scanner", "FilesQuarantined", {"stat": "Sum"}],
          ["PII-Scanner", "FilesPromoted", {"stat": "Sum"}]
        ],
        "period": 300,
        "title": "PII Scanner Throughput"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["PII-Scanner", "ScanDuration", {"stat": "p99"}],
          ["PII-Scanner", "ScanDuration", {"stat": "Average"}]
        ],
        "period": 300,
        "title": "Scan Latency"
      }
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["PII-Scanner", "FindingsBySeverity", "Severity", "CRITICAL"],
          ["PII-Scanner", "FindingsBySeverity", "Severity", "HIGH"],
          ["PII-Scanner", "FindingsBySeverity", "Severity", "MEDIUM"]
        ],
        "period": 3600,
        "title": "Findings by Severity (Hourly)"
      }
    }
  ]
}
```

**Step 5: Operational runbook**

```
RUNBOOK: PII Scanner Alert Response

TRIGGER: SNS alert with severity CRITICAL or HIGH

STEPS:
1. Identify the quarantined file:
   - Check alert payload for source location and quarantine path
   - Verify file exists in quarantine bucket

2. Assess the finding:
   - Download scan metadata from quarantine object tags
   - Determine if PII is real (not false positive)
   - Identify the data source/producer

3. If TRUE POSITIVE:
   - Notify data producer of contract violation
   - Determine if PII was already propagated downstream
   - If yes: trigger retroactive scan of affected tables
   - Document in incident tracker (severity, scope, response time)
   - File must be remediated (PII removed/masked) before re-ingestion

4. If FALSE POSITIVE:
   - Add pattern exception to scan configuration (DynamoDB)
   - Re-process file (move back to landing zone)
   - Update detection patterns to reduce false positive rate

5. Close:
   - Update scan metrics
   - If pattern change needed: submit PR to scanner config
   - Weekly review of quarantine backlog
```

---

## References

- Apache Iceberg specification: https://iceberg.apache.org/spec/
- Delta Lake protocol: https://github.com/delta-io/delta/blob/master/PROTOCOL.md
- Apache Hudi documentation: https://hudi.apache.org/docs/overview
- AWS Lake Formation developer guide
- Trino documentation: https://trino.io/docs/current/
- CIS Benchmark for Amazon S3
- OWASP Cloud Security: Data Lake Controls
- NIST SP 800-188: De-Identifying Government Datasets
