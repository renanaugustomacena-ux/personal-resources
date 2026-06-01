# Big Data Architecture — Patterns, Technologies, and Security

---

## 1. Architecture Patterns

Big data architecture patterns define how organizations ingest, store, process, and serve data at scale. The choice of pattern determines latency guarantees, operational complexity, cost profiles, and the range of analytical workloads the system can support. No single pattern dominates; mature organizations often combine elements from multiple paradigms.

### 1.1 Lambda Architecture

The Lambda architecture, formalized by Nathan Marz, splits data processing into three layers:

**Batch Layer** — Stores the immutable, append-only master dataset and precomputes batch views. Technologies: HDFS, S3, Apache Spark batch jobs, Hive. The batch layer provides correctness by reprocessing the entire dataset on every cycle.

**Speed Layer (Real-Time)** — Processes only recent data that the batch layer has not yet incorporated. Technologies: Apache Storm, Spark Structured Streaming, Apache Flink. The speed layer sacrifices perfect accuracy for low latency.

**Serving Layer** — Merges batch views with real-time views to answer queries. Technologies: Druid, Apache Cassandra, ElasticSearch, HBase.

Lambda's strength lies in fault tolerance: if the speed layer produces an incorrect result, the next batch cycle self-corrects. Its weakness is operational duplication — every piece of logic must be implemented twice (batch and streaming) and kept in sync.

```
                    ┌───────────────────────┐
  Raw Data ──────►  │     Batch Layer       │──► Batch Views ──┐
       │            └───────────────────────┘                  │
       │                                                       ▼
       │            ┌───────────────────────┐          ┌─────────────┐
       └──────────► │     Speed Layer       │──────►   │  Serving    │──► Queries
                    └───────────────────────┘          │   Layer     │
                                                       └─────────────┘
```

### 1.2 Kappa Architecture

Jay Kreps proposed Kappa as a simplification: treat everything as a stream. The master dataset lives in a replayable log (e.g., Apache Kafka with infinite retention). When logic changes, you replay the log through the new streaming job and swap out the serving layer atomically.

**Advantages:** Single codebase, simpler operational model, natural fit for event-sourced systems.

**Disadvantages:** Replay at petabyte scale is expensive; some analytical workloads (complex joins, ML training) remain awkward in pure streaming.

**When to choose Kappa:** When the primary access pattern is event-driven, when late-arriving data is uncommon, and when the team prefers operational simplicity over theoretical completeness.

### 1.3 Medallion / Lakehouse Architecture

Popularized by Databricks, the medallion architecture organizes a data lake into progressive quality tiers:

| Layer | Purpose | Format | Retention |
|-------|---------|--------|-----------|
| Bronze | Raw ingestion, append-only | JSON, CSV, Avro | Long (years) |
| Silver | Cleansed, deduplicated, conformed | Parquet/Delta/Iceberg | Medium |
| Gold | Business-level aggregates, curated | Parquet/Delta/Iceberg | Domain-driven |

The lakehouse combines the flexibility of a data lake (schema-on-read, cheap storage) with warehouse-grade features (ACID transactions, schema enforcement, time travel) via table formats like Delta Lake, Apache Iceberg, or Apache Hudi.

### 1.4 Data Mesh

Zhamak Dehghani's data mesh decentralizes data ownership:

1. **Domain-oriented ownership** — Each business domain owns its data products, including pipelines, storage, and quality guarantees.
2. **Data as a product** — Domains publish discoverable, trustworthy, self-describing datasets with SLAs.
3. **Self-serve data platform** — A centralized platform team provides infrastructure primitives (compute, storage, catalog, governance) consumed via self-service.
4. **Federated computational governance** — Global policies (security, interoperability) enforced automatically, not via a central team gatekeeping every query.

Data mesh suits large organizations with many autonomous teams but demands organizational maturity. Without strong contracts and automated governance, it devolves into siloed chaos.

### 1.5 Data Fabric

Gartner's data fabric concept emphasizes metadata-driven automation. A knowledge graph of metadata (schemas, lineage, usage patterns, quality metrics) powers automated recommendations: what data to integrate, which pipelines to optimize, where quality has degraded.

Key technologies: Apache Atlas, Collibra, Informatica, Alation. The fabric sits above physical storage and provides a unified semantic layer regardless of where data lives.

### 1.6 Event-Driven Architecture

In event-driven architectures, state changes propagate as immutable events through a broker (Kafka, Pulsar, Kinesis, EventBridge). Consumers react asynchronously.

**Patterns within EDA:**

- **Event notification** — Thin event; consumer fetches details.
- **Event-carried state transfer** — Fat event; consumer has everything it needs without callback.
- **Event sourcing** — The log IS the system of record; current state is a derived view.
- **CQRS** — Command side writes events; query side materializes optimized read models.

### 1.7 Polyglot Persistence

No single database satisfies all access patterns. Polyglot persistence selects the storage engine per workload:

| Workload | Storage |
|----------|---------|
| Transactional CRUD | PostgreSQL, MySQL |
| Time-series telemetry | TimescaleDB, InfluxDB, ClickHouse |
| Graph relationships | Neo4j, Amazon Neptune |
| Full-text search | Elasticsearch, OpenSearch |
| Key-value cache | Redis, Memcached |
| Wide-column analytics | Cassandra, ScyllaDB |
| Document flexibility | MongoDB, CouchDB |

The trade-off: operational complexity multiplied by the number of engines, plus cross-store consistency challenges.

### 1.8 HTAP (Hybrid Transactional/Analytical Processing)

HTAP systems serve both OLTP and OLAP workloads from a single engine, eliminating ETL latency between operational and analytical databases.

Implementations: TiDB (row + columnar replicas), SingleStore (rowstore + columnstore), AlloyDB (PostgreSQL + columnar engine), CockroachDB with column families.

HTAP avoids the "ETL tax" but introduces resource contention. Isolation mechanisms (read replicas, resource groups, separate storage engines for each workload) mitigate interference.

### 1.9 Choosing the Right Pattern

| Criterion | Best Fit |
|-----------|----------|
| Sub-second latency + correctness | Lambda |
| Operational simplicity + streaming-first | Kappa |
| Analytical lake with ACID | Lakehouse / Medallion |
| Many autonomous teams | Data Mesh |
| Heterogeneous sources, metadata-heavy | Data Fabric |
| Microservices, async communication | Event-Driven |
| Mixed workloads, single stack | HTAP |

In practice, hybrid approaches dominate: a lakehouse medallion structure with event-driven ingestion, polyglot serving layers, and data mesh organizational principles.

---

## 2. Hadoop Ecosystem

The Hadoop ecosystem defined the first generation of open-source big data. While its dominance has waned, understanding its architecture remains essential — many organizations still operate Hadoop clusters, and its successors (Spark, object stores, cloud-managed services) inherited Hadoop's design vocabulary.

### 2.1 HDFS Architecture

HDFS (Hadoop Distributed File System) stores large files across commodity hardware with built-in fault tolerance.

**NameNode** — Single master that manages the filesystem namespace (directory tree, file-to-block mapping, block locations). Stores metadata in memory for fast lookups. The NameNode is a single point of failure mitigated by HA configurations (Active/Standby NameNodes backed by a shared edit log in JournalNodes or ZooKeeper).

**DataNode** — Worker nodes storing actual data blocks. Each file is split into fixed-size blocks (default 128 MB). DataNodes send heartbeats and block reports to the NameNode.

**Replication** — Default replication factor of 3. HDFS places replicas using a rack-awareness policy:

1. First replica: local node (or a random node in the writer's rack).
2. Second replica: a node in a different rack.
3. Third replica: a different node in the second rack.

This balances network bandwidth (intra-rack is cheaper) with fault tolerance (survives a full rack failure).

**Write Path:**
1. Client requests NameNode for block allocation.
2. NameNode returns a pipeline of DataNodes.
3. Client streams data to the first DataNode, which forwards to the second, which forwards to the third (pipeline replication).
4. Acknowledgments propagate back through the pipeline.

**Read Path:**
1. Client asks NameNode for block locations.
2. NameNode returns sorted list (by network distance).
3. Client reads from the closest DataNode.

### 2.2 MapReduce Concepts

MapReduce is a programming model for distributed computation:

**Map Phase** — Input splits are processed in parallel. Each mapper emits key-value pairs.

**Shuffle and Sort** — The framework partitions mapper output by key, sorts within each partition, and transfers data to reducers.

**Reduce Phase** — Reducers aggregate all values for each key, producing final output.

MapReduce enforces a rigid two-phase structure. Complex workflows require chaining multiple MapReduce jobs, leading to verbose code and excessive I/O (each stage writes to HDFS). This rigidity drove adoption of Spark's DAG-based execution model.

### 2.3 YARN Resource Management

YARN (Yet Another Resource Negotiator) decoupled resource management from MapReduce, enabling Hadoop clusters to run multiple frameworks (Spark, Tez, Flink) concurrently.

**Components:**
- **ResourceManager** — Cluster-wide resource arbitrator. Manages a scheduler and an ApplicationManager.
- **NodeManager** — Per-node agent managing containers (CPU, memory allocations).
- **ApplicationMaster** — Per-application coordinator that negotiates resources from the ResourceManager and works with NodeManagers to execute tasks.
- **Container** — A resource allocation (CPU cores, memory) on a specific node.

**Schedulers:** Fair Scheduler (equal shares), Capacity Scheduler (hierarchical queues with guaranteed minimums), FIFO (legacy).

### 2.4 Apache Hive

Hive provides SQL-like access (HiveQL) over data stored in HDFS or object storage.

**Metastore** — Central metadata repository storing table schemas, partition information, and storage descriptors. Backed by a relational database (MySQL, PostgreSQL). The metastore decouples schema from storage, enabling schema-on-read.

**Partitioning** — Organizes data into subdirectories by column values (e.g., `/events/year=2025/month=05/day=07/`). Queries filtering on partition columns skip irrelevant directories entirely (partition pruning).

**Bucketing** — Within a partition, data is hashed into fixed-number buckets. Enables efficient sampling and optimized joins (bucket map join) when both tables share the same bucketing scheme.

**Execution Engines:** Originally MapReduce; now commonly Tez (DAG-based, fewer materializations) or Spark.

**LLAP (Live Long and Process)** — Persistent daemon providing in-memory caching and vectorized execution for interactive Hive queries.

### 2.5 Apache HBase

HBase is a distributed, sorted, column-family NoSQL store modeled after Google's Bigtable.

**Data Model:**
- **Table** → collection of rows.
- **Row** → identified by a row key (byte array, sorted lexicographically).
- **Column Family** → physical grouping of columns; each family stored in separate HFiles.
- **Column Qualifier** → identifies a specific column within a family.
- **Cell** → (row, column family, qualifier, timestamp) → value.

**Architecture:**
- **HMaster** — Assigns regions to RegionServers, handles schema changes, load balancing.
- **RegionServer** — Serves reads/writes for assigned regions. Each region is a contiguous range of row keys.
- **ZooKeeper** — Coordinates master election, region assignments, and client discovery.

**Write Path:**
1. Write goes to WAL (Write-Ahead Log) for durability.
2. Then to MemStore (in-memory sorted buffer).
3. When MemStore fills, it flushes to an HFile on HDFS.

**Compaction:** Minor compaction merges small HFiles. Major compaction merges all HFiles for a column family, removing deleted/expired cells. Major compaction is I/O-intensive.

**Row Key Design** is critical: monotonically increasing keys cause hotspotting (all writes hit one region). Solutions: salting, hashing, reversing timestamp.

### 2.6 Ecosystem Evolution and Decline

The Hadoop ecosystem peaked circa 2014-2018. Factors driving its decline:

- **Cloud object storage** (S3, GCS, ADLS) replaced HDFS for durable storage at lower cost with zero operational burden.
- **Spark** replaced MapReduce for processing, making YARN the only remaining Hadoop piece many used.
- **Kubernetes** replaced YARN for resource management in cloud-native environments.
- **Managed services** (EMR, Dataproc, HDInsight) abstracted cluster management, removing the Hadoop operational "brand."
- **Separation of storage and compute** — Hadoop's colocation of storage and compute (data locality) became less relevant as network bandwidth improved and object storage performance increased.

Hadoop's legacy: it proved distributed computing on commodity hardware was viable, established HDFS as the reference architecture for distributed storage, and spawned an ecosystem (Hive, HBase, Kafka, Spark) that outlived Hadoop itself.

---

## 3. Modern Data Lake

The modern data lake decouples storage from compute, uses object storage as the persistence tier, and employs open table formats to provide warehouse-grade capabilities (ACID, schema enforcement, time travel) without a monolithic warehouse engine.

### 3.1 Object Storage Foundations

**Amazon S3** — The de facto standard. Provides 11 nines of durability, tiered storage classes (Standard, Intelligent-Tiering, Glacier), strong read-after-write consistency (since December 2020), and S3 Select/Glacier Select for server-side filtering.

**Google Cloud Storage (GCS)** — Comparable durability and performance. Strong consistency by default. Hierarchical namespace via folders (metadata-only).

**Azure Data Lake Storage Gen2 (ADLS)** — Built on Azure Blob Storage with a hierarchical namespace (true directories), fine-grained POSIX-like ACLs, and optimized driver for Hadoop-compatible workloads (abfs:// protocol).

**Key characteristics shared across providers:**
- Flat namespace (object key → bytes) with optional hierarchical namespace overlays.
- Effectively unlimited capacity.
- Cost: $0.02-0.03/GB/month for hot tier; orders of magnitude cheaper than block storage.
- No random writes; objects are immutable once written.
- Optimized for large sequential reads (analytics workloads).

### 3.2 Open Table Formats

Table formats add ACID transactions, schema enforcement, and time travel to object storage.

#### Apache Iceberg

Developed at Netflix, donated to Apache. Architecture:

- **Catalog** (Hive Metastore, Nessie, REST, Glue) points to the current metadata file.
- **Metadata file** (JSON) references the current snapshot.
- **Snapshot** references a manifest list.
- **Manifest list** references manifests.
- **Manifest** references data files with per-file statistics (min/max per column, row count, null count).

Iceberg's manifest-level statistics enable aggressive file pruning without scanning data. Partition evolution allows changing partitioning strategy without rewriting data. Hidden partitioning derives partition values from source columns (e.g., `day(timestamp)`) without requiring users to manage partition columns manually.

#### Delta Lake

Developed by Databricks. Uses a transaction log (`_delta_log/`) containing JSON commit files and periodic checkpoint Parquet files. Supports ACID transactions, schema enforcement and evolution, time travel via versioned snapshots, Z-ordering for multi-dimensional clustering, and liquid clustering (adaptive, maintenance-free clustering).

Delta Lake's tight integration with Spark and Databricks gives it strong vendor-supported tooling. Delta UniForm enables reading Delta tables as Iceberg or Hudi tables by maintaining metadata in all three formats.

#### Apache Hudi

Developed at Uber for incremental processing. Two table types:

- **Copy-on-Write (CoW)** — Updates rewrite entire Parquet files. Read-optimized.
- **Merge-on-Read (MoR)** — Updates written to row-level log files; merged at read time or during compaction. Write-optimized.

Hudi's incremental query capability returns only records changed since a given commit, enabling efficient CDC (Change Data Capture) pipelines.

### 3.3 Metadata Management

| System | Description |
|--------|-------------|
| Hive Metastore | Legacy standard; stores table/partition metadata in RDBMS. Limited scalability. |
| Nessie | Git-like catalog for Iceberg. Branching, tagging, merging of table states. Enables experimentation without affecting production. |
| Unity Catalog | Databricks' unified governance layer. Manages Delta, Iceberg, external tables, ML models, and functions. Fine-grained access control. |
| AWS Glue Data Catalog | Managed Hive-compatible metastore. Tight integration with Athena, EMR, Redshift Spectrum. |
| Polaris Catalog | Snowflake's open-source REST catalog for Iceberg. Vendor-neutral interoperability. |

### 3.4 Schema Evolution

Table formats support schema evolution without rewriting data:

- **Add columns** — New columns return NULL for historical files.
- **Rename columns** — Iceberg uses unique column IDs; renaming is metadata-only.
- **Widen types** — e.g., INT → BIGINT.
- **Reorder columns** — Metadata-only in Iceberg (column IDs decouple logical and physical order).
- **Drop columns** — Metadata-only; physical data remains until compaction.

### 3.5 Time Travel

All three formats (Iceberg, Delta, Hudi) support querying data as of a previous point in time:

```sql
-- Iceberg
SELECT * FROM catalog.db.events FOR SYSTEM_TIME AS OF '2025-05-01 00:00:00';

-- Delta Lake
SELECT * FROM events VERSION AS OF 42;
SELECT * FROM events TIMESTAMP AS OF '2025-05-01';
```

Time travel enables: debugging data issues, reproducing ML training data, auditing historical state, and rolling back bad writes.

### 3.6 Partition Evolution

Iceberg's partition evolution allows changing the partitioning strategy on a table without rewriting existing data:

```sql
ALTER TABLE events SET PARTITION SPEC (day(event_time), bucket(16, user_id));
```

Old data files retain their original partitioning metadata; new writes use the new scheme. Queries spanning both automatically apply the correct pruning logic per manifest.

### 3.7 Compaction

Over time, small files accumulate (from streaming ingestion or frequent updates). Compaction merges small files into larger ones, improving read performance.

- **Iceberg** — `CALL catalog.system.rewrite_data_files(table => 'db.events')` with configurable target file size and strategies (bin-pack, sort, z-order).
- **Delta** — `OPTIMIZE` command with Z-ORDER BY for multi-dimensional clustering.
- **Hudi** — Automatic compaction for MoR tables; scheduled via Hudi's compaction service.

---

## 4. Cloud Data Platforms

### 4.1 AWS Data Stack

| Service | Role |
|---------|------|
| S3 | Object storage, data lake foundation |
| AWS Glue | Managed ETL (Spark-based), Data Catalog, crawlers |
| Athena | Serverless SQL over S3 (Presto/Trino engine) |
| EMR | Managed Hadoop/Spark/Hive/Flink clusters |
| Redshift | Columnar MPP data warehouse |
| Redshift Spectrum | Query S3 data from Redshift without loading |
| Kinesis | Real-time streaming (Data Streams, Firehose, Analytics) |
| Lake Formation | Data lake governance (fine-grained access, encryption) |
| MSK | Managed Apache Kafka |

**Architecture pattern:**
```
Sources → Kinesis/MSK → Glue ETL → S3 (Bronze/Silver/Gold) → Athena/Redshift → BI
                                                    ↕
                                             Glue Data Catalog
```

### 4.2 GCP Data Stack

| Service | Role |
|---------|------|
| GCS | Object storage |
| Dataflow | Managed Apache Beam (batch + stream) |
| BigQuery | Serverless columnar warehouse, supports nested/repeated fields |
| Dataproc | Managed Hadoop/Spark clusters |
| Pub/Sub | Managed message broker |
| Dataplex | Data governance and management |
| Looker | BI and semantic layer |
| Composer | Managed Apache Airflow |

BigQuery's architecture separates storage (Capacitor columnar format on Colossus) from compute (Dremel execution engine). This enables serverless scaling and pay-per-query pricing.

BigQuery's native features: partitioning (ingestion-time, column-based), clustering (up to 4 columns), materialized views, BI Engine (in-memory acceleration), BigLake (unified governance across GCS/S3/ADLS).

### 4.3 Azure Data Stack

| Service | Role |
|---------|------|
| ADLS Gen2 | Object storage with hierarchical namespace |
| Data Factory | Managed ETL/ELT orchestration (90+ connectors) |
| Synapse Analytics | Unified analytics (serverless SQL, Spark pools, dedicated SQL pools) |
| Databricks on Azure | Lakehouse platform (deeply integrated) |
| Event Hubs | Managed event streaming (Kafka-compatible) |
| Purview | Data governance, lineage, classification |
| Fabric | Unified analytics platform (OneLake, lakehouse, warehouse, notebooks) |

Microsoft Fabric represents Azure's bet on a unified lakehouse: one copy of data in OneLake (built on ADLS), accessible via multiple engines (SQL, Spark, Power BI, Data Activator).

### 4.4 Snowflake

Multi-cloud data platform built on separation of storage and compute.

**Architecture layers:**
1. **Cloud Services** — Metadata, query parsing, optimization, access control, transaction management.
2. **Virtual Warehouses** — Independent compute clusters that can scale up/down/out. Multiple warehouses share the same data without contention.
3. **Storage** — Data stored in proprietary micro-partitions (columnar, compressed, encrypted) on the provider's object storage.

**Key features:** Zero-copy cloning, time travel (up to 90 days on Enterprise), data sharing (no data movement), Snowpark (Python/Java/Scala on Snowflake), Cortex (AI/ML functions), dynamic tables (declarative ELT).

### 4.5 Databricks

Founded by Spark's creators, Databricks commercialized the lakehouse concept.

**Key components:**
- **Delta Lake** — ACID table format (open source).
- **Unity Catalog** — Centralized governance across workspaces.
- **Photon** — C++ vectorized query engine for Delta tables.
- **Databricks SQL** — Serverless SQL warehouses.
- **MLflow** — ML lifecycle management (experiment tracking, model registry).
- **Delta Live Tables** — Declarative ETL with automatic lineage and quality expectations.
- **Mosaic AI** — LLM training, serving, and compound AI systems.

### 4.6 Platform Comparison Matrix

| Dimension | AWS | GCP | Azure | Snowflake | Databricks |
|-----------|-----|-----|-------|-----------|------------|
| Storage | S3 | GCS | ADLS | Internal micro-partitions | Delta on object storage |
| Serverless SQL | Athena | BigQuery | Synapse Serverless | Native | Databricks SQL |
| Streaming | Kinesis/MSK | Dataflow/Pub/Sub | Event Hubs | Snowpipe Streaming | Structured Streaming |
| Governance | Lake Formation | Dataplex | Purview/Fabric | Native RBAC | Unity Catalog |
| ML | SageMaker | Vertex AI | Azure ML | Snowpark ML | MLflow/Mosaic |
| Multi-cloud | No | No | No | Yes | Yes |
| Open formats | Iceberg/Hudi/Delta | BigLake open formats | Delta/Iceberg | Iceberg (Apache Polaris) | Delta (UniForm) |

---

## 5. Distributed Computing Fundamentals

### 5.1 CAP Theorem

Eric Brewer's CAP theorem states that a distributed system can simultaneously guarantee at most two of:

- **Consistency (C)** — Every read receives the most recent write.
- **Availability (A)** — Every request receives a non-error response.
- **Partition Tolerance (P)** — The system continues operating despite network partitions.

Since network partitions are inevitable in distributed systems, the real choice is between CP (consistency over availability during partitions) and AP (availability over consistency during partitions).

**CP systems:** ZooKeeper, etcd, HBase, Spanner (technically CP + high availability via TrueTime).
**AP systems:** Cassandra (tunable consistency), DynamoDB (eventual consistency mode), CouchDB.

### 5.2 Consistency Models

**Strong consistency (linearizability)** — Operations appear instantaneous and totally ordered. Every read sees the latest write. Expensive (requires coordination).

**Sequential consistency** — Operations from each client appear in order, but interleaving between clients is flexible.

**Causal consistency** — If operation A causally precedes B (A happened-before B), all nodes see A before B. Concurrent operations may appear in any order.

**Eventual consistency** — Given enough time without new writes, all replicas converge to the same state. No ordering guarantees during convergence.

**Read-your-writes consistency** — A client always sees its own writes, even if other clients see stale data.

**Monotonic reads** — Once a client reads a value, subsequent reads never return older values.

### 5.3 Distributed Consensus

Consensus algorithms ensure agreement among distributed nodes despite failures.

**Raft** (Diego Ongaro, 2013) — Designed for understandability. Uses leader election, log replication, and safety properties:
1. A leader is elected via randomized timeouts.
2. The leader receives all client writes and appends to its log.
3. The leader replicates log entries to followers.
4. Once a majority acknowledges, the entry is committed.
5. If the leader fails, a new election occurs.

Used by: etcd, CockroachDB, TiKV, Consul.

**Paxos** (Leslie Lamport, 1989) — Theoretical foundation for consensus. More general but harder to implement correctly. Variants: Multi-Paxos (for log replication), Flexible Paxos (relaxed quorum requirements), EPaxos (leaderless).

**Practical differences:** Raft constrains the design space (only the leader proposes), making it easier to implement and reason about. Paxos allows more flexible configurations but is notoriously difficult to implement correctly.

### 5.4 Partitioning Strategies

**Hash partitioning** — `partition = hash(key) mod N`. Distributes data uniformly but makes range queries impossible.

**Range partitioning** — Keys are split into contiguous ranges. Enables range scans but risks hotspots (e.g., time-series data with recent timestamps).

**Consistent hashing** — Maps both keys and nodes onto a hash ring. When a node is added/removed, only keys near the affected position are remapped. Used by DynamoDB, Cassandra, Riak. Virtual nodes (vnodes) improve distribution uniformity.

**Directory-based partitioning** — A lookup service maps keys to partitions. Maximum flexibility but the directory is a potential bottleneck and single point of failure.

### 5.5 Replication Strategies

**Single-leader (master-slave)** — One node accepts writes; replicas serve reads. Simple but the leader is a bottleneck and single point of failure (mitigated by automatic failover).

**Multi-leader** — Multiple nodes accept writes (e.g., geographically distributed leaders). Requires conflict resolution (last-writer-wins, application-specific merge).

**Leaderless (Dynamo-style)** — Client writes to multiple replicas simultaneously. Reads from multiple replicas and reconciles via version vectors. Quorum reads/writes: `W + R > N` ensures overlap.

### 5.6 Vector Clocks

Vector clocks track causal ordering in distributed systems. Each node maintains a vector of logical timestamps (one per node). When node `i` sends a message, it increments its own counter. The receiver merges vectors by taking the element-wise maximum.

Two events are concurrent if neither vector dominates the other — requiring application-level conflict resolution.

**Limitation:** Vector clocks grow linearly with the number of nodes. Dotted version vectors and interval tree clocks address this.

### 5.7 CRDTs (Conflict-Free Replicated Data Types)

CRDTs are data structures that can be replicated across nodes and updated independently, with mathematically guaranteed convergence.

**Types:**
- **G-Counter** — Grow-only counter (per-node counters summed).
- **PN-Counter** — Increment/decrement counter (two G-Counters).
- **G-Set** — Grow-only set (only additions).
- **OR-Set** — Observed-Remove set (supports additions and removals).
- **LWW-Register** — Last-Writer-Wins register (timestamp resolves conflicts).
- **RGA** — Replicated Growable Array (ordered sequences, collaborative editing).

CRDTs are used in: Redis Enterprise (active-active geo-replication), Riak, Automerge, Yjs (collaborative editing), Apple's CloudKit.

---

## 6. Performance at Scale

### 6.1 Data Partitioning

Effective partitioning is the single most impactful performance optimization for big data systems. The goal: minimize data scanned per query by eliminating irrelevant partitions early.

**Temporal partitioning** — Most analytical queries filter by time. Partition by `date` or `hour` to enable partition pruning.

**Multi-dimensional partitioning** — For queries filtering on multiple columns (e.g., region + date), consider composite partition keys or clustering within partitions.

**Dynamic partitioning** — Iceberg's hidden partitioning derives partitions automatically. Delta's liquid clustering adapts to evolving query patterns.

**Partition sizing guidelines:**
- Target 128 MB – 1 GB per partition file.
- Too few partitions → large scans, memory pressure.
- Too many partitions → metadata overhead, small file problem.

### 6.2 File Format Optimization

#### Columnar Formats

**Apache Parquet:**
- Columnar storage with row groups (default 128 MB).
- Each row group contains column chunks.
- Each column chunk contains pages (default 1 MB).
- Encoding: dictionary encoding (for low-cardinality columns), delta encoding (for sorted data), RLE (for repeated values), bit-packing.
- Statistics: min/max values per row group and page, null counts, distinct counts (optional).
- Compression: Snappy (fast, moderate ratio), Zstd (better ratio, slightly slower), LZ4 (fastest decompression).

**Apache ORC (Optimized Row Columnar):**
- Stripe-based (default 64 MB stripes).
- Built-in lightweight indexes: stripe-level statistics, row-group-level bloom filters.
- Predicate pushdown into the format itself (ORC reader skips irrelevant stripes/row groups).
- ACID support in Hive (ORC supports row-level updates via delta files).
- Typically achieves better compression than Parquet for Hive workloads.

**Apache Avro:**
- Row-based, schema-embedded format.
- Fast serialization/deserialization.
- Best for: write-heavy workloads, Kafka messages, schema evolution scenarios.
- Not suitable for analytical scans (no column pruning).

#### Predicate Pushdown

Predicate pushdown evaluates filters at the storage layer:

1. **File-level pruning** — Skip entire files based on manifest/metadata statistics.
2. **Row-group/stripe-level pruning** — Skip row groups whose min/max statistics prove no rows match the predicate.
3. **Page-level pruning** — Parquet v2 page-level statistics enable skipping individual pages.
4. **Bloom filter pruning** — Probabilistic test for membership; definitively excludes non-matching row groups.

#### Projection Pushdown

Read only requested columns. In columnar formats, unrequested columns are never deserialized, saving I/O and CPU. A query reading 3 of 200 columns scans ~1.5% of the data volume.

### 6.3 Caching Layers

**Alluxio** — Distributed caching layer between compute and storage. Caches frequently accessed object storage data on compute nodes' local SSDs. Transparent to the application (presents a filesystem interface). Used by Facebook (Presto + Alluxio), Uber, Alibaba.

**Memcached / Redis** — Application-level caching for materialized aggregations, query results, or frequently accessed dimension tables.

**Arrow Flight / Arrow in-memory** — Columnar in-memory format for zero-copy reads across processes. Used by DataFusion, DuckDB, and various query engines for inter-process data exchange.

### 6.4 Cost-Based Optimization (CBO)

Modern query engines (Spark, Trino, Presto, Hive) use cost-based optimizers that estimate query plan costs based on table/column statistics:

- **Row count estimation** — Uses histogram statistics per column.
- **Join ordering** — Chooses the cheapest join order (smallest intermediate results first).
- **Join strategy selection** — Broadcast join (small table replicated), shuffle hash join, sort-merge join.
- **Aggregate pushdown** — Pushes partial aggregation before shuffles.

Statistics collection:
```sql
-- Spark
ANALYZE TABLE events COMPUTE STATISTICS FOR ALL COLUMNS;

-- Hive
ANALYZE TABLE events COMPUTE STATISTICS;
ANALYZE TABLE events COMPUTE STATISTICS FOR COLUMNS user_id, event_type;
```

### 6.5 Adaptive Query Execution (AQE)

Spark 3.0+ AQE optimizes query plans at runtime based on actual shuffle statistics:

- **Coalescing shuffle partitions** — Merges small partitions post-shuffle to reduce task overhead.
- **Converting sort-merge join to broadcast join** — If one side of a join is discovered to be small at runtime.
- **Optimizing skewed joins** — Splits skewed partitions into sub-partitions and replicates the smaller side.

AQE eliminates the need for manual tuning of `spark.sql.shuffle.partitions` in many cases.

### 6.6 Data Skew Handling

Skew occurs when one partition holds disproportionately more data than others, creating stragglers that dominate job runtime.

**Detection:** Monitor task duration variance. A task taking 10x the median indicates skew.

**Mitigation strategies:**
- **Salting** — Add a random prefix to skewed keys, process in parallel, then aggregate.
- **AQE skew join optimization** — Automatic in Spark 3.0+.
- **Broadcast join** — If the skewed side is the larger table and the other side fits in memory.
- **Two-pass aggregation** — Partial aggregate with salted keys, then final aggregate without salt.
- **Isolation** — Process skewed keys separately with a dedicated job.

---

## 7. Big Data Security

### 7.1 HDFS Encryption Zones

HDFS Transparent Data Encryption (TDE) encrypts data at rest without application changes:

- **Encryption Zone** — A directory in HDFS where all files are automatically encrypted.
- **Key Management Server (KMS)** — Manages encryption keys. Supports key rotation without re-encryption (envelope encryption: DEK encrypted by zone key, zone key encrypted by master key).
- **Encryption** — AES-CTR-256 for data, AES-128 for key encryption.
- **Transparent** — Clients see plaintext; encryption/decryption happens in the HDFS client library.

Configuration:
```bash
# Create encryption key
hadoop key create zone_key -size 256

# Create encryption zone
hdfs crypto -createZone -keyName zone_key -path /data/sensitive
```

### 7.2 Apache Ranger Authorization

Ranger provides centralized authorization and audit for the Hadoop ecosystem.

**Capabilities:**
- Fine-grained access control (database, table, column, row-level filtering).
- Tag-based policies (classify data with Atlas tags, apply policies to tags).
- Attribute-based access control (ABAC) via conditions.
- Dynamic column masking (hash, partial mask, null) based on user/group.
- Audit logging to Solr or HDFS.

**Supported services:** HDFS, Hive, HBase, Kafka, YARN, Spark, Trino, NiFi, Ozone.

**Policy model:**
```
Resource → Allow/Deny → Users/Groups/Roles → Conditions → Permissions
```

Row-level filtering example:
```
Table: orders
Filter: region = '{USER.department}'
Effect: Users see only their department's orders
```

### 7.3 Kerberos Authentication for Hadoop

Kerberos provides strong authentication (mutual authentication, no plaintext passwords on the wire) for Hadoop services.

**Components:**
- **KDC (Key Distribution Center)** — Issues tickets. Contains AS (Authentication Server) and TGS (Ticket Granting Server).
- **Principals** — Identities (users: `user@REALM`, services: `hdfs/hostname@REALM`).
- **Keytab** — File containing principal's key for non-interactive authentication.

**Authentication flow:**
1. Client authenticates to AS, receives TGT (Ticket Granting Ticket).
2. Client presents TGT to TGS, requests service ticket for specific service.
3. Client presents service ticket to the service. Service validates and grants access.

**Hadoop-specific considerations:**
- Every service (NameNode, DataNode, ResourceManager, Hive, HBase) has its own principal and keytab.
- Delegation tokens reduce KDC load for long-running jobs (MapReduce tasks use delegation tokens instead of hitting KDC per task).
- Token renewal and cancellation must be managed for job lifecycle.

### 7.4 Data Lake Security

#### S3 Security Layers

1. **IAM Policies** — Identity-based policies attached to users/roles. Principle of least privilege.
2. **Bucket Policies** — Resource-based policies on the bucket. Control cross-account access, enforce encryption.
3. **Access Points** — Named endpoints with dedicated access policies. Simplify multi-tenant access.
4. **VPC Endpoints (Gateway)** — Route S3 traffic through the VPC without internet exposure.
5. **S3 Block Public Access** — Account-level or bucket-level guard against accidental public exposure.
6. **Object Lock** — WORM (Write Once Read Many) for regulatory compliance.
7. **S3 Access Grants** — Map identities from corporate directories to S3 prefixes.

#### IAM Role Patterns for Data Access

```
┌─────────────────────────────────────────────────────────┐
│  Instance Profile / Pod Identity / Workload Identity    │
│       (no long-lived credentials)                       │
└───────────────────────┬─────────────────────────────────┘
                        │ AssumeRole
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Data Access Role (scoped to specific prefixes)         │
│  - s3:GetObject on s3://lake/gold/domain-a/*            │
│  - s3:PutObject on s3://lake/silver/domain-a/*          │
│  - Deny s3:DeleteObject (immutable lake)                │
└─────────────────────────────────────────────────────────┘
```

### 7.5 Encryption

**At rest:**
- **SSE-S3** — Server-side encryption with S3-managed keys. Zero configuration.
- **SSE-KMS** — Server-side encryption with AWS KMS keys. Audit trail of key usage, separate key management.
- **SSE-C** — Server-side encryption with customer-provided keys. Customer manages keys entirely.
- **CSE (Client-Side Encryption)** — Data encrypted before upload. Maximum security; cloud provider never sees plaintext.

**In transit:**
- TLS 1.2+ for all API calls (enforce via bucket policy: `aws:SecureTransport`).
- HDFS wire encryption (data transfer and RPC encryption via Hadoop's SASL framework).
- Kafka TLS for inter-broker and client-broker communication.

**Database-level:**
- HBase cell-level encryption (encrypt specific column families).
- Transparent Data Encryption in cloud warehouses (Snowflake: always-on, customer-managed keys available; BigQuery: default encryption + CMEK; Redshift: cluster-level KMS encryption).

### 7.6 Column-Level Access Control

Fine-grained access prevents users from seeing sensitive columns while allowing access to the rest of the table.

**Ranger dynamic column masking:**
```
Policy: Mask column "ssn" for group "analysts"
Mask type: Partial (show last 4 digits)
Result: SELECT ssn FROM customers → "***-**-1234"
```

**Unity Catalog column masks:**
```sql
ALTER TABLE customers ALTER COLUMN ssn SET MASK mask_ssn USING COLUMNS (current_user());

CREATE FUNCTION mask_ssn(ssn STRING, invoker STRING)
RETURNS STRING
RETURN CASE WHEN is_member('pii_readers') THEN ssn ELSE 'REDACTED' END;
```

**BigQuery column-level security:**
```sql
-- Create policy tag taxonomy in Data Catalog
-- Apply policy tags to columns
-- Grant Fine-Grained Reader role on specific policy tags
```

---

## 8. Data Governance at Scale

### 8.1 Metadata Management

Effective metadata management at petabyte scale requires automated discovery and classification — manual cataloging does not scale.

**Metadata categories:**
- **Technical metadata** — Schemas, data types, file formats, storage locations, partitioning schemes.
- **Operational metadata** — Pipeline run history, freshness timestamps, row counts, failure rates.
- **Business metadata** — Descriptions, owners, domain tags, data contracts, SLAs.
- **Social metadata** — Usage patterns, popular queries, frequent joiners, user ratings.

### 8.2 Data Catalogs

#### Apache Atlas

Open-source metadata and governance framework for Hadoop/Spark ecosystems.

**Core features:**
- Type system (define custom entity types: Table, Column, Pipeline, ML Model).
- Classification tags (PII, Sensitive, Public) with propagation rules.
- Lineage tracking (automatically captures Hive/Spark lineage via hooks).
- Search and discovery (full-text search, faceted browsing, DSL queries).
- Integration: Ranger uses Atlas classifications for tag-based policies.

#### DataHub (LinkedIn)

Modern metadata platform designed for scale and extensibility.

**Architecture:**
- **Metadata Service (GMS)** — Central API for metadata CRUD.
- **Metadata Audit Event (MAE)** stream — Kafka-based change events for real-time propagation.
- **Frontend** — React-based UI for discovery, lineage, governance.
- **Ingestion framework** — 100+ connectors (Snowflake, BigQuery, dbt, Airflow, Kafka, etc.).

**Differentiators vs Atlas:** Better UI, broader connector ecosystem, Kafka-native architecture, GraphQL API, active open-source community.

#### Other Catalogs

- **Amundsen** (Lyft) — Discovery-focused; frontend for search and lineage.
- **OpenMetadata** — Unified metadata standard with built-in quality, lineage, and governance.
- **Alation** — Commercial; strong in data stewardship and collaboration.
- **Collibra** — Commercial; focused on business glossary and policy management.

### 8.3 Lineage Tracking (OpenLineage)

OpenLineage is an open standard for metadata and lineage collection across data pipelines.

**Core concepts:**
- **Job** — A unit of work (Spark job, Airflow task, dbt model).
- **Dataset** — A data source or sink (table, file, topic).
- **Run** — An instance of a job execution.
- **Facets** — Extensible metadata (schema facet, data quality facet, source code facet).

**Events:**
```json
{
  "eventType": "COMPLETE",
  "job": {"namespace": "analytics", "name": "daily_aggregation"},
  "inputs": [{"namespace": "warehouse", "name": "events_silver"}],
  "outputs": [{"namespace": "warehouse", "name": "daily_metrics_gold"}],
  "run": {"runId": "abc-123"},
  "producer": "spark"
}
```

**Integrations:** Airflow (natively since 2.7), Spark (OpenLineage Spark listener), dbt (built-in), Flink, Dagster.

**Consumers:** Marquez (reference implementation), DataHub, Atlan, OpenMetadata.

### 8.4 Quality Gates

Automated quality checks integrated into pipelines prevent bad data from propagating:

**Tools:**
- **Great Expectations** — Python library for data validation with expressive assertions.
- **Soda** — Data quality checks defined in YAML.
- **dbt tests** — Schema tests (not null, unique, accepted values, relationships) and custom SQL tests.
- **Delta Live Tables Expectations** — Declarative quality constraints in DLT pipelines.

**Quality dimensions:**
- Completeness (null rates, missing records).
- Uniqueness (duplicate detection).
- Validity (format, range, domain constraints).
- Freshness (data is not stale beyond SLA).
- Consistency (cross-source agreement).
- Accuracy (matches ground truth where verifiable).

**Implementation pattern:**
```
Ingestion → Bronze (raw) → Quality Gate → Silver (validated) → Quality Gate → Gold (curated)
                              ↓ fail                              ↓ fail
                         Quarantine                          Alert + Block
```

### 8.5 PII Detection at Scale

Automated PII detection for petabyte-scale lakes:

**Approaches:**
1. **Pattern-based** — Regex for SSN, credit card numbers, phone numbers, emails. Fast but narrow.
2. **NER-based** — Named Entity Recognition models detect names, addresses, organizations. Better recall but compute-intensive.
3. **Statistical profiling** — Column statistics (cardinality, value distribution) flag likely PII columns.
4. **Sampling + classification** — Sample N rows per column, run classifiers, propagate labels.

**Tools:**
- AWS Macie — Automated PII discovery in S3.
- Google Cloud DLP — InfoType detectors for 150+ sensitive data types.
- Microsoft Purview — Classification and sensitivity labels.
- Open-source: Presidio (Microsoft), piicatcher, DataHub's classification.

### 8.6 Compliance Automation

**GDPR / Right to Deletion:**
- Maintain PII inventory (which tables, columns, partitions contain user data).
- Implement deletion pipelines that rewrite affected Parquet files excluding the deleted user's records.
- Iceberg/Delta positional deletes make this more efficient than full file rewrites.
- Track deletion certification (prove deletion occurred).

**CCPA / Data Subject Access Requests (DSAR):**
- Index user data locations for fast retrieval.
- Generate comprehensive data exports per user.
- Automate response within regulatory timelines (30 days CCPA, 30 days GDPR).

**HIPAA:**
- Encryption at rest and in transit (mandatory).
- Audit logging of all PHI access.
- Minimum necessary access (column-level controls for PHI fields).
- BAA (Business Associate Agreement) with cloud provider.

### 8.7 Data Retention at Petabyte Scale

**Policy definition:**
```yaml
retention_policies:
  - dataset: events_bronze
    retention: 7_years
    reason: regulatory_compliance
    action: archive_to_glacier_after_1_year

  - dataset: session_logs
    retention: 90_days
    reason: operational
    action: delete_after_expiry

  - dataset: ml_training_snapshots
    retention: 2_years
    reason: model_reproducibility
    action: move_to_infrequent_access_after_6_months
```

**Implementation:**
- Tag datasets with retention metadata in the catalog.
- Scheduled jobs evaluate retention policies and execute lifecycle transitions.
- Iceberg/Delta time travel expiration: `CALL system.expire_snapshots('db.table', TIMESTAMP '2025-01-01')`.
- S3 Lifecycle rules for automated tier transitions and expiration.
- Audit trail of all deletions for compliance evidence.

---

## 9. Cost Optimization

### 9.1 Storage Tiering

| Tier | Use Case | AWS S3 Class | Monthly Cost (per GB) |
|------|----------|--------------|----------------------|
| Hot | Active queries, dashboards | Standard | $0.023 |
| Warm | Occasional analysis | Infrequent Access | $0.0125 |
| Cold | Compliance, rare access | Glacier Instant Retrieval | $0.004 |
| Archive | Legal hold, never queried | Glacier Deep Archive | $0.00099 |

**Automation:**
- S3 Intelligent-Tiering monitors access patterns and moves objects automatically (no retrieval fees).
- S3 Lifecycle rules based on object age or tags.
- Custom policies based on query frequency from catalog metadata.

**GCS equivalents:** Standard → Nearline ($0.01/GB) → Coldline ($0.004/GB) → Archive ($0.0012/GB).

**Azure equivalents:** Hot → Cool → Cold → Archive.

### 9.2 Compute Auto-Scaling

**Cluster auto-scaling:**
- EMR managed scaling: adjusts core/task nodes based on YARN metrics.
- Dataproc autoscaling: policies define min/max nodes and scale-up/down cooldown.
- Databricks autoscaling: min/max workers with dynamic allocation.

**Serverless compute:**
- Athena: pay per TB scanned (no idle costs).
- BigQuery: pay per TB processed (on-demand) or flat-rate slots (capacity reservations).
- Databricks SQL Serverless: compute spins up/down per query.
- Snowflake: warehouses auto-suspend after configurable idle timeout.

**Spark dynamic allocation:**
```
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.minExecutors=2
spark.dynamicAllocation.maxExecutors=100
spark.dynamicAllocation.executorIdleTimeout=60s
```

### 9.3 Spot/Preemptible Instances

| Provider | Service | Discount | Interruption Notice |
|----------|---------|----------|---------------------|
| AWS | Spot Instances | 60-90% | 2 minutes |
| GCP | Preemptible VMs | 60-91% | 30 seconds |
| GCP | Spot VMs | 60-91% | 30 seconds (no 24h limit) |
| Azure | Spot VMs | Up to 90% | 30 seconds |

**Best practices for spot in data workloads:**
- Use spot for Spark executors/task nodes; keep the driver on on-demand.
- Enable graceful decommissioning (Spark's `spark.decommission.enabled=true`).
- Diversify across instance types and availability zones.
- Use checkpointing for long-running streaming jobs.
- EMR instance fleets: mix on-demand (core) + spot (task) with multiple instance types.

### 9.4 Query Optimization for Cost

#### BigQuery Cost Optimization

```sql
-- Use column projection (avoid SELECT *)
SELECT user_id, event_type FROM events WHERE date = '2025-05-07';

-- Use partitioned tables
CREATE TABLE events
PARTITION BY DATE(event_time)
CLUSTER BY user_id, event_type;

-- Materialize expensive joins
CREATE MATERIALIZED VIEW daily_summary AS
SELECT date, COUNT(*) as events FROM events GROUP BY date;

-- Use BI Engine for dashboards (in-memory, flat monthly cost)

-- Monitor with INFORMATION_SCHEMA
SELECT
  user_email,
  SUM(total_bytes_processed) / POW(1024, 4) AS tb_scanned,
  SUM(total_bytes_processed) / POW(1024, 4) * 6.25 AS estimated_cost_usd
FROM `region-us`.INFORMATION_SCHEMA.JOBS
WHERE creation_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY user_email
ORDER BY tb_scanned DESC;
```

#### Snowflake Credit Optimization

- Right-size warehouses (X-Small for simple queries, larger for complex).
- Use auto-suspend (minimum 60 seconds; set to 300 for bursty workloads).
- Use multi-cluster warehouses for concurrency instead of larger single warehouses.
- Materialized views for repeated aggregations.
- Search optimization service for point lookups on large tables.
- Monitor with `SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY` and `WAREHOUSE_METERING_HISTORY`.

### 9.5 Data Lifecycle Automation

```python
# Example: Automated lifecycle policy enforcement
lifecycle_rules = {
    "bronze": {
        "compact_after_hours": 6,
        "move_to_ia_after_days": 30,
        "archive_after_days": 365,
        "delete_after_days": 2555  # 7 years
    },
    "silver": {
        "compact_after_hours": 12,
        "move_to_ia_after_days": 90,
        "expire_snapshots_after_days": 7
    },
    "gold": {
        "compact_after_hours": 24,
        "move_to_ia_after_days": 180,
        "retain_indefinitely": True
    }
}
```

**Iceberg snapshot expiration:**
```sql
-- Remove snapshots older than 7 days
CALL catalog.system.expire_snapshots('db.events', TIMESTAMP '2025-04-30 00:00:00');

-- Remove orphan files (files not referenced by any snapshot)
CALL catalog.system.remove_orphan_files('db.events');
```

### 9.6 FinOps Practices for Data Teams

**Tagging strategy:**
```
team: data-platform
environment: production
cost-center: analytics
pipeline: daily-etl
data-tier: gold
```

**Cost allocation:**
- Tag all resources (S3 buckets, compute clusters, warehouses) with team/pipeline ownership.
- Use AWS Cost Explorer, GCP Billing, or Azure Cost Management to break down costs.
- Implement chargeback or showback models.

**Governance controls:**
- Set per-team/per-user query cost limits.
- Alert when daily spend exceeds threshold.
- Require approval for queries exceeding N TB scanned.
- Automated reports: weekly cost per team, per pipeline, per dataset.

**Optimization cadence:**
- Weekly: Review top expensive queries, identify optimization opportunities.
- Monthly: Storage tiering review, unused resource cleanup.
- Quarterly: Architecture review — are we using the right services?

---

## 10. Lab Exercises

### Lab 10.1: Build a Lakehouse Architecture (MinIO + Iceberg + Spark + Trino)

**Objective:** Deploy a local lakehouse stack demonstrating ACID transactions, schema evolution, time travel, and multi-engine access.

**Prerequisites:** Docker, Docker Compose, 16 GB RAM minimum.

**Architecture:**
```
┌───────────┐     ┌───────────────┐     ┌─────────────┐
│  Spark    │────►│   MinIO       │◄────│   Trino     │
│ (writer)  │     │ (S3-compat)   │     │ (SQL query) │
└───────────┘     └───────────────┘     └─────────────┘
       │                   │                    │
       └───────────┬───────┘                    │
                   ▼                            │
           ┌──────────────┐                    │
           │  Nessie      │◄───────────────────┘
           │  (catalog)   │
           └──────────────┘
```

**Step 1: Docker Compose setup**

```yaml
version: "3.9"
services:
  minio:
    image: quay.io/minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin123
    volumes:
      - minio_data:/data

  nessie:
    image: ghcr.io/projectnessie/nessie:latest
    ports:
      - "19120:19120"

  spark:
    image: bitnami/spark:3.5
    ports:
      - "4040:4040"
      - "8080:8080"
    environment:
      - SPARK_MODE=master
    volumes:
      - ./spark-defaults.conf:/opt/bitnami/spark/conf/spark-defaults.conf
      - ./jars:/opt/bitnami/spark/jars/custom

  trino:
    image: trinodb/trino:latest
    ports:
      - "8081:8080"
    volumes:
      - ./trino-catalog:/etc/trino/catalog

volumes:
  minio_data:
```

**Step 2: Spark configuration (spark-defaults.conf)**

```properties
spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions
spark.sql.catalog.nessie=org.apache.iceberg.spark.SparkCatalog
spark.sql.catalog.nessie.type=nessie
spark.sql.catalog.nessie.uri=http://nessie:19120/api/v2
spark.sql.catalog.nessie.ref=main
spark.sql.catalog.nessie.warehouse=s3://lakehouse/warehouse
spark.sql.catalog.nessie.io-impl=org.apache.iceberg.aws.s3.S3FileIO
spark.sql.catalog.nessie.s3.endpoint=http://minio:9000
spark.sql.catalog.nessie.s3.access-key-id=minioadmin
spark.sql.catalog.nessie.s3.secret-access-key=minioadmin123
spark.sql.catalog.nessie.s3.path-style-access=true
```

**Step 3: Create tables and write data (PySpark)**

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("LakehouseLab") \
    .getOrCreate()

# Create namespace
spark.sql("CREATE NAMESPACE IF NOT EXISTS nessie.analytics")

# Create table with partitioning
spark.sql("""
    CREATE TABLE IF NOT EXISTS nessie.analytics.events (
        event_id STRING,
        user_id STRING,
        event_type STRING,
        event_time TIMESTAMP,
        properties MAP<STRING, STRING>
    )
    USING iceberg
    PARTITIONED BY (day(event_time), bucket(16, user_id))
""")

# Insert data
from pyspark.sql.functions import current_timestamp, lit, map_from_arrays, array
from datetime import datetime, timedelta
import random

events = []
for i in range(100000):
    events.append((
        f"evt-{i:06d}",
        f"user-{random.randint(1, 10000):05d}",
        random.choice(["page_view", "click", "purchase", "signup"]),
        datetime(2025, 5, 1) + timedelta(hours=random.randint(0, 168)),
        {"source": random.choice(["web", "mobile", "api"])}
    ))

df = spark.createDataFrame(events, ["event_id", "user_id", "event_type", "event_time", "properties"])
df.writeTo("nessie.analytics.events").append()

# Verify
spark.sql("SELECT event_type, COUNT(*) FROM nessie.analytics.events GROUP BY 1").show()
```

**Step 4: Schema evolution**

```python
# Add a new column (metadata-only operation)
spark.sql("ALTER TABLE nessie.analytics.events ADD COLUMN session_id STRING")

# Verify old data has NULL for new column
spark.sql("SELECT event_id, session_id FROM nessie.analytics.events LIMIT 5").show()
```

**Step 5: Time travel**

```python
# List snapshots
spark.sql("SELECT * FROM nessie.analytics.events.snapshots").show(truncate=False)

# Query historical state
spark.sql("""
    SELECT COUNT(*) 
    FROM nessie.analytics.events 
    FOR SYSTEM_VERSION AS OF 1
""").show()
```

**Step 6: Query from Trino**

Trino catalog configuration (`trino-catalog/iceberg.properties`):
```properties
connector.name=iceberg
iceberg.catalog.type=nessie
iceberg.nessie-catalog.uri=http://nessie:19120/api/v2
iceberg.nessie-catalog.ref=main
iceberg.nessie-catalog.default-warehouse=s3://lakehouse/warehouse
fs.native-s3.enabled=true
s3.endpoint=http://minio:9000
s3.aws-access-key=minioadmin
s3.aws-secret-key=minioadmin123
s3.path-style-access=true
```

```sql
-- From Trino CLI
SELECT event_type, COUNT(*) as cnt
FROM iceberg.analytics.events
WHERE event_time >= TIMESTAMP '2025-05-05 00:00:00'
GROUP BY event_type
ORDER BY cnt DESC;
```

**Verification checklist:**
- [ ] Data written via Spark is queryable from Trino
- [ ] Schema evolution does not require data rewrite
- [ ] Time travel returns historical snapshots
- [ ] Partition pruning reduces scan size (verify via query plan)

---

### Lab 10.2: Implement Data Lake Security with Apache Ranger

**Objective:** Configure fine-grained access control including row-level filtering and column masking.

**Prerequisites:** Docker, Ranger 2.4+, Trino or Hive.

**Step 1: Deploy Ranger**

```yaml
# docker-compose-ranger.yaml
services:
  ranger-admin:
    image: apache/ranger:latest
    ports:
      - "6080:6080"
    environment:
      - DB_HOST=ranger-db
      - DB_NAME=ranger
      - DB_USER=ranger
      - DB_PASSWORD=ranger123
    depends_on:
      - ranger-db

  ranger-db:
    image: postgres:15
    environment:
      POSTGRES_DB: ranger
      POSTGRES_USER: ranger
      POSTGRES_PASSWORD: ranger123

  solr:
    image: solr:9
    ports:
      - "8983:8983"
    command: solr-precreate ranger_audits
```

**Step 2: Create service definition for Trino/Hive**

```bash
# Register Hive service in Ranger
curl -u admin:rangerR0cks! -X POST \
  http://localhost:6080/service/public/v2/api/service \
  -H "Content-Type: application/json" \
  -d '{
    "name": "lakehouse_hive",
    "type": "hive",
    "configs": {
      "username": "hive",
      "password": "hive",
      "jdbc.driverClassName": "org.apache.hive.jdbc.HiveDriver",
      "jdbc.url": "jdbc:hive2://hive-server:10000"
    }
  }'
```

**Step 3: Define access policies**

```bash
# Create policy: analysts can read gold tables but not PII columns
curl -u admin:rangerR0cks! -X POST \
  http://localhost:6080/service/public/v2/api/policy \
  -H "Content-Type: application/json" \
  -d '{
    "service": "lakehouse_hive",
    "name": "gold_analysts_access",
    "resources": {
      "database": {"values": ["gold"]},
      "table": {"values": ["*"]},
      "column": {"values": ["*"], "excludes": ["ssn", "email", "phone"]}
    },
    "policyItems": [{
      "users": [],
      "groups": ["analysts"],
      "accesses": [{"type": "select", "isAllowed": true}]
    }]
  }'
```

**Step 4: Configure column masking**

```bash
# Mask SSN column for analysts group
curl -u admin:rangerR0cks! -X POST \
  http://localhost:6080/service/public/v2/api/policy \
  -H "Content-Type: application/json" \
  -d '{
    "service": "lakehouse_hive",
    "name": "mask_ssn_analysts",
    "policyType": 1,
    "resources": {
      "database": {"values": ["gold"]},
      "table": {"values": ["customers"]},
      "column": {"values": ["ssn"]}
    },
    "dataMaskPolicyItems": [{
      "groups": ["analysts"],
      "accesses": [{"type": "select", "isAllowed": true}],
      "dataMaskInfo": {"dataMaskType": "MASK_SHOW_LAST_4"}
    }]
  }'
```

**Step 5: Configure row-level filtering**

```bash
# Analysts can only see their region's data
curl -u admin:rangerR0cks! -X POST \
  http://localhost:6080/service/public/v2/api/policy \
  -H "Content-Type: application/json" \
  -d '{
    "service": "lakehouse_hive",
    "name": "row_filter_by_region",
    "policyType": 2,
    "resources": {
      "database": {"values": ["gold"]},
      "table": {"values": ["orders"]}
    },
    "rowFilterPolicyItems": [{
      "groups": ["analysts"],
      "accesses": [{"type": "select", "isAllowed": true}],
      "rowFilterInfo": {
        "filterExpr": "region = current_user_region()"
      }
    }]
  }'
```

**Step 6: Verify audit logs**

```bash
# Query Solr for audit events
curl "http://localhost:8983/solr/ranger_audits/select?q=*:*&rows=10&sort=evtTime+desc&wt=json" | jq '.response.docs[] | {user: .reqUser, resource: .resType, action: .action, result: .result}'
```

**Verification checklist:**
- [ ] Analysts cannot access excluded columns directly
- [ ] Column masking returns partial data (last 4 digits of SSN)
- [ ] Row-level filter restricts visible rows
- [ ] All access attempts are logged in Solr audit
- [ ] Denied access returns authorization error, not empty results

---

### Lab 10.3: Create a Cost Monitoring Dashboard for Cloud Data Services

**Objective:** Build an automated cost monitoring system that tracks spending across data services and alerts on anomalies.

**Prerequisites:** AWS account with billing access (or equivalent GCP/Azure), Python 3.11+, Grafana.

**Step 1: Cost data collection (AWS)**

```python
"""
cost_collector.py — Collects AWS data service costs via Cost Explorer API.
"""
import boto3
from datetime import datetime, timedelta
from typing import Any

def get_data_service_costs(days_back: int = 30) -> list[dict[str, Any]]:
    """Fetch daily costs for data services from AWS Cost Explorer."""
    client = boto3.client("ce", region_name="us-east-1")

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days_back)

    data_services = [
        "Amazon Simple Storage Service",
        "Amazon Athena",
        "Amazon EMR",
        "Amazon Redshift",
        "AWS Glue",
        "Amazon Kinesis",
        "Amazon Managed Streaming for Apache Kafka",
    ]

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date.isoformat(),
            "End": end_date.isoformat(),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost", "UsageQuantity"],
        Filter={
            "Dimensions": {
                "Key": "SERVICE",
                "Values": data_services,
            }
        },
        GroupBy=[
            {"Type": "DIMENSION", "Key": "SERVICE"},
            {"Type": "TAG", "Key": "team"},
        ],
    )

    results = []
    for period in response["ResultsByTime"]:
        date = period["TimePeriod"]["Start"]
        for group in period["Groups"]:
            service = group["Keys"][0]
            team = group["Keys"][1] if len(group["Keys"]) > 1 else "untagged"
            cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
            results.append({
                "date": date,
                "service": service,
                "team": team,
                "cost_usd": cost,
            })

    return results


def detect_anomalies(
    costs: list[dict[str, Any]], threshold_multiplier: float = 2.0
) -> list[dict[str, Any]]:
    """Flag days where cost exceeds threshold_multiplier * rolling 7-day average."""
    from collections import defaultdict
    import statistics

    # Group by service+team
    grouped: dict[str, list[float]] = defaultdict(list)
    for record in sorted(costs, key=lambda r: r["date"]):
        key = f"{record['service']}|{record['team']}"
        grouped[key].append(record["cost_usd"])

    anomalies = []
    for key, daily_costs in grouped.items():
        for i in range(7, len(daily_costs)):
            window = daily_costs[i - 7 : i]
            avg = statistics.mean(window)
            if avg > 0 and daily_costs[i] > avg * threshold_multiplier:
                service, team = key.split("|")
                anomalies.append({
                    "service": service,
                    "team": team,
                    "date": costs[i]["date"],
                    "cost": daily_costs[i],
                    "rolling_avg": avg,
                    "multiplier": daily_costs[i] / avg,
                })

    return anomalies
```

**Step 2: Store metrics in PostgreSQL (for Grafana)**

```sql
CREATE TABLE data_costs (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    service VARCHAR(100) NOT NULL,
    team VARCHAR(50) NOT NULL,
    cost_usd NUMERIC(10,4) NOT NULL,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_data_costs_date ON data_costs(date);
CREATE INDEX idx_data_costs_service ON data_costs(service, date);
CREATE INDEX idx_data_costs_team ON data_costs(team, date);

CREATE TABLE cost_anomalies (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    service VARCHAR(100) NOT NULL,
    team VARCHAR(50) NOT NULL,
    cost_usd NUMERIC(10,4) NOT NULL,
    rolling_avg NUMERIC(10,4) NOT NULL,
    multiplier NUMERIC(6,2) NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Step 3: Grafana dashboard queries**

```sql
-- Panel 1: Daily cost by service (time series)
SELECT
    date AS time,
    service,
    SUM(cost_usd) AS cost
FROM data_costs
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY date, service
ORDER BY date;

-- Panel 2: Cost by team (bar chart)
SELECT
    team,
    SUM(cost_usd) AS total_cost
FROM data_costs
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY team
ORDER BY total_cost DESC;

-- Panel 3: Anomalies table
SELECT
    date,
    service,
    team,
    cost_usd,
    rolling_avg,
    multiplier,
    CASE WHEN acknowledged THEN 'Yes' ELSE 'No' END AS acked
FROM cost_anomalies
WHERE detected_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY multiplier DESC;

-- Panel 4: Month-over-month trend
SELECT
    DATE_TRUNC('month', date) AS month,
    SUM(cost_usd) AS total_cost,
    LAG(SUM(cost_usd)) OVER (ORDER BY DATE_TRUNC('month', date)) AS prev_month,
    ROUND(
        (SUM(cost_usd) - LAG(SUM(cost_usd)) OVER (ORDER BY DATE_TRUNC('month', date)))
        / NULLIF(LAG(SUM(cost_usd)) OVER (ORDER BY DATE_TRUNC('month', date)), 0) * 100,
        1
    ) AS pct_change
FROM data_costs
GROUP BY DATE_TRUNC('month', date)
ORDER BY month;
```

**Step 4: Alert configuration**

```yaml
# Grafana alert rule (provisioned via YAML)
apiVersion: 1
groups:
  - orgId: 1
    name: data_cost_alerts
    folder: Data Platform
    interval: 1h
    rules:
      - uid: cost-anomaly-alert
        title: "Data Service Cost Anomaly"
        condition: C
        data:
          - refId: A
            datasourceUid: postgres
            model:
              rawSql: |
                SELECT COUNT(*) as anomaly_count
                FROM cost_anomalies
                WHERE detected_at >= NOW() - INTERVAL '1 hour'
                AND acknowledged = false
                AND multiplier > 3.0
          - refId: C
            type: threshold
            conditions:
              - evaluator: {type: gt, params: [0]}
                operator: {type: and}
                query: {params: [A]}
        annotations:
          summary: "Cost anomaly detected: {{ $values.A }} unacknowledged anomalies with >3x spike"
        labels:
          severity: warning
```

**Verification checklist:**
- [ ] Cost data collected daily via scheduled job (cron or Airflow)
- [ ] Anomaly detection flags spikes > 2x rolling average
- [ ] Grafana dashboard displays: time series, team breakdown, anomalies, trends
- [ ] Alerts fire within 1 hour of anomaly detection
- [ ] All data services are tagged with team ownership

---

### Lab 10.4: Benchmark Parquet vs ORC for Analytical Workloads

**Objective:** Empirically compare Parquet and ORC across dimensions: write speed, read speed, file size, predicate pushdown effectiveness, and compression ratios.

**Prerequisites:** Spark 3.5+, dataset with 100M+ rows (TPC-DS or synthetic).

**Step 1: Generate test data**

```python
"""
benchmark_data_gen.py — Generate synthetic analytical data for format benchmarking.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    rand, randn, floor, concat, lit, from_unixtime,
    unix_timestamp, expr
)

spark = SparkSession.builder \
    .appName("FormatBenchmark") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

NUM_ROWS = 200_000_000  # 200M rows

df = spark.range(0, NUM_ROWS) \
    .withColumn("user_id", (rand() * 1_000_000).cast("long")) \
    .withColumn("event_type", expr(
        "CASE WHEN rand() < 0.4 THEN 'page_view' "
        "WHEN rand() < 0.7 THEN 'click' "
        "WHEN rand() < 0.9 THEN 'add_to_cart' "
        "ELSE 'purchase' END"
    )) \
    .withColumn("amount", (randn() * 50 + 100).cast("decimal(10,2)")) \
    .withColumn("event_time", from_unixtime(
        unix_timestamp(lit("2025-01-01")) + (rand() * 86400 * 120).cast("long")
    ).cast("timestamp")) \
    .withColumn("region", expr(
        "CASE WHEN rand() < 0.3 THEN 'US' "
        "WHEN rand() < 0.5 THEN 'EU' "
        "WHEN rand() < 0.7 THEN 'APAC' "
        "WHEN rand() < 0.85 THEN 'LATAM' "
        "ELSE 'MEA' END"
    )) \
    .withColumn("session_id", concat(lit("sess-"), (rand() * 50_000_000).cast("long").cast("string"))) \
    .withColumn("payload", expr("repeat(hex(cast(rand()*1000 as int)), 10)"))

# Cache to avoid recomputation during writes
df.cache()
df.count()  # Force materialization

print(f"Generated {NUM_ROWS:,} rows")
```

**Step 2: Write in both formats with various configurations**

```python
import time

configs = {
    "parquet_snappy": {"format": "parquet", "compression": "snappy"},
    "parquet_zstd": {"format": "parquet", "compression": "zstd"},
    "parquet_uncompressed": {"format": "parquet", "compression": "none"},
    "orc_snappy": {"format": "orc", "compression": "snappy"},
    "orc_zstd": {"format": "orc", "compression": "zstd"},
    "orc_zlib": {"format": "orc", "compression": "zlib"},
    "orc_uncompressed": {"format": "orc", "compression": "none"},
}

write_results = {}
base_path = "s3://benchmark/format-test"

for name, cfg in configs.items():
    path = f"{base_path}/{name}"
    start = time.time()

    df.write \
        .format(cfg["format"]) \
        .option("compression", cfg["compression"]) \
        .partitionBy("region") \
        .mode("overwrite") \
        .save(path)

    elapsed = time.time() - start
    write_results[name] = elapsed
    print(f"{name}: {elapsed:.1f}s")
```

**Step 3: Measure file sizes**

```python
from subprocess import check_output

size_results = {}
for name in configs:
    path = f"{base_path}/{name}"
    # Using hadoop fs -du -s or boto3 for S3
    total_bytes = spark._jvm.org.apache.hadoop.fs.FileSystem \
        .get(spark._jsc.hadoopConfiguration()) \
        .getContentSummary(spark._jvm.org.apache.hadoop.fs.Path(path)) \
        .getLength()
    size_gb = total_bytes / (1024**3)
    size_results[name] = size_gb
    print(f"{name}: {size_gb:.2f} GB")
```

**Step 4: Read benchmarks**

```python
read_benchmarks = {}

queries = {
    "full_scan": "SELECT COUNT(*), SUM(amount) FROM data",
    "filtered_scan": "SELECT COUNT(*), AVG(amount) FROM data WHERE region = 'US' AND event_type = 'purchase'",
    "aggregation": "SELECT region, event_type, COUNT(*), SUM(amount), AVG(amount) FROM data GROUP BY region, event_type",
    "projection": "SELECT user_id, amount FROM data WHERE amount > 200",
    "point_lookup": "SELECT * FROM data WHERE user_id = 42 AND event_type = 'purchase'",
}

for name, cfg in configs.items():
    path = f"{base_path}/{name}"
    read_df = spark.read.format(cfg["format"]).load(path)
    read_df.createOrReplaceTempView("data")

    read_benchmarks[name] = {}
    for query_name, sql in queries.items():
        # Warm up
        spark.sql(sql).collect()

        # Timed run (average of 3)
        times = []
        for _ in range(3):
            start = time.time()
            spark.sql(sql).collect()
            times.append(time.time() - start)

        avg_time = sum(times) / len(times)
        read_benchmarks[name][query_name] = avg_time
        print(f"{name} | {query_name}: {avg_time:.2f}s")
```

**Step 5: Analyze predicate pushdown effectiveness**

```python
for name, cfg in configs.items():
    path = f"{base_path}/{name}"
    read_df = spark.read.format(cfg["format"]).load(path)
    read_df.createOrReplaceTempView("data")

    # Get physical plan showing pushed filters
    explain = spark.sql(
        "SELECT * FROM data WHERE region = 'US' AND amount > 150"
    )._jdf.queryExecution().executedPlan().toString()

    print(f"\n{'='*60}")
    print(f"Format: {name}")
    print(f"Pushed filters visible in plan: {'PushedFilters' in explain}")
    print(explain[:500])
```

**Step 6: Summary report generation**

```python
import pandas as pd

# Compile results
summary = pd.DataFrame({
    "format": list(configs.keys()),
    "write_time_s": [write_results[k] for k in configs],
    "size_gb": [size_results[k] for k in configs],
    "full_scan_s": [read_benchmarks[k]["full_scan"] for k in configs],
    "filtered_scan_s": [read_benchmarks[k]["filtered_scan"] for k in configs],
    "aggregation_s": [read_benchmarks[k]["aggregation"] for k in configs],
})

summary["compression_ratio"] = summary["size_gb"].max() / summary["size_gb"]
summary = summary.sort_values("filtered_scan_s")

print("\n" + "=" * 80)
print("BENCHMARK SUMMARY")
print("=" * 80)
print(summary.to_string(index=False))
print("\nExpected findings:")
print("- Parquet + Zstd: best compression ratio for most workloads")
print("- ORC + Zlib: competitive compression, better for Hive-native workloads")
print("- Predicate pushdown: both formats benefit, ORC's built-in indexes may edge out on point lookups")
print("- Projection pushdown: nearly identical (both are columnar)")
print("- Write speed: Snappy fastest (less CPU), Zstd/Zlib slower but smaller files")
```

**Expected results (directional):**

| Metric | Parquet + Zstd | ORC + Zlib | Notes |
|--------|---------------|------------|-------|
| Compression | Excellent | Excellent | Within 5-10% of each other |
| Full scan | Fast | Fast | Parquet slightly faster in Spark |
| Predicate pushdown | Good | Better | ORC bloom filters help point lookups |
| Write speed | Moderate | Moderate | Snappy variants are faster |
| Ecosystem support | Broader | Hive-focused | Parquet dominates outside Hive |
| Nested types | Better | Good | Parquet's Dremel encoding handles deep nesting |

**Verification checklist:**
- [ ] Generated 200M+ rows across multiple data types
- [ ] Both formats written with 3+ compression codecs
- [ ] Read benchmarks run 3+ times and averaged
- [ ] Physical plans show predicate pushdown for both formats
- [ ] Size comparison accounts for compression codec differences
- [ ] Results documented with reproducible methodology

---

## References

- Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly.
- Marz, N. & Warren, J. (2015). *Big Data: Principles and best practices of scalable real-time data systems*. Manning.
- Dehghani, Z. (2022). *Data Mesh: Delivering Data-Driven Value at Scale*. O'Reilly.
- Apache Iceberg Documentation — https://iceberg.apache.org/docs/latest/
- Delta Lake Documentation — https://docs.delta.io/latest/
- Apache Ranger Documentation — https://ranger.apache.org/
- AWS Well-Architected Framework: Analytics Lens — https://docs.aws.amazon.com/wellarchitected/latest/analytics-lens/
- OpenLineage Specification — https://openlineage.io/docs/spec/
- Raft Consensus Algorithm — https://raft.github.io/
- CAP Theorem (Brewer, 2000; Gilbert & Lynch, 2002)
