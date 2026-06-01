# Apache Spark --- Distributed Computing for Big Data

## Table of Contents

1. [Spark Architecture](#1-spark-architecture)
2. [Spark Core and RDDs](#2-spark-core-and-rdds)
3. [Spark SQL and DataFrames](#3-spark-sql-and-dataframes)
4. [Spark Streaming and Structured Streaming](#4-spark-streaming-and-structured-streaming)
5. [PySpark and Performance](#5-pyspark-and-performance)
6. [Performance Tuning](#6-performance-tuning)
7. [Spark on Kubernetes](#7-spark-on-kubernetes)
8. [Security](#8-security)
9. [Data Engineering Patterns](#9-data-engineering-patterns)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Spark Architecture

### 1.1 Driver/Executor Model

Apache Spark operates on a master-worker architecture consisting of two primary process types: the **Driver** and the **Executors**.

**Driver Process.** The driver is the controller of a Spark application. It runs the `main()` function, creates the `SparkSession` (or `SparkContext` in legacy code), converts user code into a DAG of stages and tasks, negotiates resources with the cluster manager, and schedules tasks on executors. The driver maintains the complete metadata about the application --- lineage graphs, partition locations, accumulator values, and broadcast variable references. If the driver dies, the entire application fails.

**Executor Processes.** Executors are JVM processes launched on worker nodes. Each executor provides CPU cores and memory for running tasks. An executor's lifecycle is tied to the application --- it starts when the application registers with the cluster manager and terminates when the application finishes (or when the executor is preempted under dynamic allocation). Executors have two responsibilities: (1) execute tasks assigned by the driver and return results, and (2) provide in-memory storage for cached RDDs and DataFrames via the `BlockManager`.

The communication flow:

```
User Code → Driver (DAG Scheduler → Task Scheduler) → Cluster Manager → Executors
                     ↑ task results / heartbeats ↑
```

Each executor runs multiple **tasks** concurrently. A task is the smallest unit of work, operating on a single partition of data. The maximum concurrency per executor equals its allocated core count (`spark.executor.cores`).

### 1.2 SparkContext and SparkSession

`SparkContext` was the original entry point (Spark 1.x). It established the connection to the cluster manager and provided the API for creating RDDs, accumulators, and broadcast variables. Since Spark 2.0, `SparkSession` is the unified entry point, wrapping `SparkContext`, `SQLContext`, and `HiveContext` into a single object.

```python
# PySpark
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("etl-pipeline") \
    .config("spark.sql.shuffle.partitions", "200") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .enableHiveSupport() \
    .getOrCreate()

sc = spark.sparkContext  # Access the underlying SparkContext when needed
```

```scala
// Scala
import org.apache.spark.sql.SparkSession

val spark = SparkSession.builder()
  .appName("etl-pipeline")
  .config("spark.sql.shuffle.partitions", "200")
  .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
  .enableHiveSupport()
  .getOrCreate()

val sc = spark.sparkContext
```

`SparkSession` provides the `read`, `sql`, `table`, `createDataFrame`, and `catalog` APIs. Multiple sessions can coexist in the same JVM with isolated SQL configurations via `spark.newSession()`, which is useful for multi-tenant notebook environments.

### 1.3 Cluster Managers

Spark is agnostic about resource scheduling. Four cluster manager integrations exist:

**Standalone Mode.** Spark's built-in cluster manager. A Master process coordinates resource allocation, and Worker processes launch executors. Simple to deploy, supports basic fault tolerance with ZooKeeper-based standby masters, but lacks multi-tenancy features. Appropriate for dedicated Spark clusters or development environments.

**YARN (Yet Another Resource Negotiator).** The Hadoop ecosystem's resource manager. Spark submits to YARN's ResourceManager, which allocates containers on NodeManagers. Two deploy modes: `client` (driver runs on the submitting machine) and `cluster` (driver runs inside a YARN ApplicationMaster container). YARN provides queue-based scheduling (CapacityScheduler, FairScheduler), resource isolation via Linux cgroups, and integration with Hadoop security (Kerberos). The standard choice for on-premises Hadoop deployments.

**Mesos.** Apache Mesos offered fine-grained and coarse-grained scheduling modes. Spark on Mesos is deprecated as of Spark 3.2 and removed in later versions. Mentioned here for historical context only.

**Kubernetes.** The modern deployment target. Spark's native Kubernetes integration (GA since Spark 3.1) submits the driver as a Kubernetes pod, which then requests executor pods from the Kubernetes API server. Provides container-level isolation, auto-scaling via pod lifecycle, integration with cloud-native tooling, and cost optimization through spot/preemptible instances. Detailed in Section 7.

### 1.4 DAG Scheduler

When a Spark action (e.g., `count()`, `collect()`, `save()`) triggers computation, the driver's **DAG Scheduler** converts the logical execution plan into a **physical execution plan** consisting of stages and tasks.

The process:

1. **Job creation.** Each action creates a job.
2. **Stage division.** The DAG Scheduler inspects the RDD lineage graph and divides it into stages at **shuffle boundaries**. A narrow dependency (map, filter, union) stays within the same stage. A wide dependency (groupByKey, reduceByKey, join) forces a new stage because data must be redistributed.
3. **Stage ordering.** Stages form a DAG. Parent stages must complete before child stages begin.
4. **Task creation.** Each stage is divided into tasks, one per partition. A `ShuffleMapStage` produces shuffle output. A `ResultStage` computes the final action.

```
Job 0
├── Stage 0 (ShuffleMapStage): read → filter → map (narrow deps)
│   ├── Task 0 (partition 0)
│   ├── Task 1 (partition 1)
│   └── Task N (partition N)
└── Stage 1 (ResultStage): reduceByKey → count (depends on Stage 0 shuffle output)
    ├── Task 0
    └── Task M
```

### 1.5 Task Scheduling

The **Task Scheduler** receives task sets from the DAG Scheduler and assigns them to executors. It respects **data locality** preferences in priority order:

1. `PROCESS_LOCAL` --- data is in the same executor's memory (cached RDD)
2. `NODE_LOCAL` --- data is on the same node (HDFS block, local disk)
3. `RACK_LOCAL` --- data is on a node in the same rack
4. `ANY` --- no locality preference

The scheduler waits briefly for a preferred locality level before falling back. The wait durations are controlled by `spark.locality.wait` (default 3s) and its per-level variants (`spark.locality.wait.process`, etc.).

**Speculative execution** (`spark.speculation=true`) detects slow tasks (stragglers) and launches duplicate copies on other executors. The first to complete wins. Useful for heterogeneous hardware environments but harmful when tasks have side effects.

### 1.6 Memory Management

Spark uses a **Unified Memory Management** model (default since Spark 1.6, replacing the legacy static model). Each executor's JVM heap is divided into regions:

```
Executor JVM Heap
├── Reserved Memory (300 MB fixed)
├── User Memory: (1 - spark.memory.fraction) × (heap - 300MB)
│   └── User data structures, metadata, internal objects
└── Unified Memory: spark.memory.fraction (default 0.6) × (heap - 300MB)
    ├── Storage Memory (cached RDDs, broadcast variables)
    └── Execution Memory (shuffles, joins, sorts, aggregations)
```

The key insight of unified memory is that **storage and execution can borrow from each other**. If execution memory is under pressure and storage memory has free space, execution can evict cached blocks. Storage can similarly expand into unused execution memory. However, execution memory eviction takes priority --- execution can always force-evict storage, but storage cannot force-evict active execution buffers (since interrupting a running computation would be destructive).

**Off-Heap Memory.** Enabled via `spark.memory.offHeap.enabled=true` and `spark.memory.offHeap.size`. Off-heap memory is allocated outside the JVM heap using `sun.misc.Unsafe`. Benefits: no GC overhead, deterministic allocation, reduced JVM heap pressure. Used by Tungsten for sort and hash operations. The unified model applies to off-heap as well.

**Memory per executor formula:**

```
Total = spark.executor.memory (heap) + spark.executor.memoryOverhead (off-heap + native)
memoryOverhead default = max(384MB, 0.10 × spark.executor.memory)
```

For Kubernetes, add `spark.executor.pyspark.memory` for Python workers and `spark.kubernetes.memoryOverheadFactor` (default 0.10, or 0.40 for non-JVM languages).

### 1.7 Shuffle Architecture

Shuffles are the most expensive operation in Spark. A shuffle redistributes data across partitions, requiring serialization, disk I/O, network transfer, and deserialization.

**Shuffle Write.** Each map task serializes its output into `ShuffleMapOutputs` partitioned by the target reduce partition. The data is written to local disk (in the executor's `spark.local.dir`). The sort-based shuffle manager (default since Spark 1.2) produces a single sorted output file per map task plus an index file.

**Shuffle Read.** Reduce tasks fetch their partition's data from all map tasks via the `BlockTransferService`. The `ExternalShuffleService` (a long-lived process on each node) allows shuffle data to survive executor restarts and enables dynamic allocation.

**Shuffle optimizations:**
- **Tungsten sort** eliminates deserialization during sort when possible (operating directly on serialized binary data).
- **Compression:** `spark.shuffle.compress=true` (default) with configurable codec (`lz4`, `snappy`, `zstd`). `zstd` provides the best compression ratio at reasonable CPU cost.
- **spark.shuffle.file.buffer** (default 32KB) and **spark.reducer.maxSizeInFlight** (default 48MB) control I/O buffering.
- **Push-based shuffle** (Spark 3.2+) proactively pushes shuffle blocks to remote shuffle services, reducing the "fetch all" bottleneck.

### 1.8 Data Serialization

Serialization is critical because Spark serializes data for shuffles, caching, and network transfers.

**Java Serialization.** Default. Uses `java.io.Serializable`. Flexible but slow and produces large serialized objects. Suitable only for development.

**Kryo Serialization.** Enabled via `spark.serializer=org.apache.spark.serializer.KryoSerializer`. 2--10x faster than Java serialization, produces smaller output. Requires class registration for best performance:

```scala
val conf = new SparkConf()
  .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
  .set("spark.kryo.registrationRequired", "true")
  .registerKryoClasses(Array(
    classOf[MyRecord],
    classOf[Array[MyRecord]]
  ))
```

```python
spark = SparkSession.builder \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .config("spark.kryo.registrationRequired", "true") \
    .getOrCreate()
```

With `registrationRequired=true`, Kryo throws an exception for unregistered classes, catching serialization issues early. Always use Kryo in production.

---

## 2. Spark Core and RDDs

### 2.1 Resilient Distributed Datasets

An **RDD (Resilient Distributed Dataset)** is the foundational abstraction of Spark. It represents an immutable, partitioned collection of records that can be processed in parallel. "Resilient" refers to the ability to recompute lost partitions through lineage.

RDDs are created by:
- Parallelizing an existing collection: `sc.parallelize([1, 2, 3], numSlices=4)`
- Reading from external storage: `sc.textFile("hdfs:///data/logs/*.gz")`
- Transforming an existing RDD: `rdd.map(lambda x: x * 2)`

Each RDD tracks five properties:
1. A list of partitions
2. A function for computing each partition
3. A list of dependencies on parent RDDs
4. (Optional) a `Partitioner` for key-value RDDs
5. (Optional) preferred locations for computing each partition (data locality hints)

### 2.2 Transformations vs Actions

**Transformations** produce new RDDs from existing ones. They are **lazy** --- they don't trigger computation, only build the lineage graph. Examples: `map`, `flatMap`, `filter`, `mapPartitions`, `union`, `distinct`, `groupByKey`, `reduceByKey`, `join`, `cogroup`, `repartition`.

**Actions** trigger actual computation and return results to the driver or write to external storage. Examples: `count`, `collect`, `take`, `first`, `reduce`, `aggregate`, `foreach`, `saveAsTextFile`, `saveAsSequenceFile`.

```python
# PySpark example: transformations + action
rdd = sc.textFile("hdfs:///logs/access.log")          # Transformation (lazy)
errors = rdd.filter(lambda line: "ERROR" in line)       # Transformation (lazy)
error_count = errors.count()                            # Action (triggers execution)
```

```scala
// Scala equivalent
val rdd = sc.textFile("hdfs:///logs/access.log")
val errors = rdd.filter(_.contains("ERROR"))
val errorCount = errors.count()
```

**Why laziness matters:** Spark can optimize the entire chain before executing. For example, if you read a file, filter, then count, Spark won't materialize the full dataset --- it applies the filter during the read. This enables pipelining: multiple narrow transformations fuse into a single pass over the data.

### 2.3 Lineage Graph

Every RDD records its parent RDDs and the transformation applied. This chain is the **lineage graph** (or DAG of RDDs). If a partition is lost (executor crash, node failure), Spark recomputes only the lost partition by replaying the lineage from the nearest available ancestor. No data replication is needed --- the computation itself is the redundancy.

```
textFile("logs.csv") → filter(ERROR) → map(parse) → reduceByKey(+)
     RDD_0                RDD_1          RDD_2          RDD_3
```

If partition 3 of `RDD_2` is lost, Spark recomputes it by reading partition 3 of `RDD_0`, applying the filter, then the map. This is cheaper than replicating every intermediate result.

**Dependency types:**
- **Narrow dependencies:** Each parent partition maps to at most one child partition (map, filter, union). Allows pipelining within a single stage.
- **Wide dependencies (shuffle):** Each parent partition contributes to multiple child partitions (groupByKey, join). Requires a shuffle and breaks the pipeline into separate stages.

### 2.4 Partitioning Strategies

**Default partitioning:** When reading from HDFS, the number of partitions equals the number of HDFS blocks. When parallelizing a collection, the number equals `spark.default.parallelism` (typically the total number of executor cores).

**HashPartitioner.** Used by default for key-value operations like `reduceByKey`. Assigns keys to partitions via `key.hashCode() % numPartitions`. Provides uniform distribution for well-distributed keys.

**RangePartitioner.** Samples the data to determine range boundaries, then assigns keys to partitions based on ranges. Used by `sortByKey`. Ensures partitions have roughly equal sizes and are ordered.

**Custom Partitioner (Scala):**

```scala
class DomainPartitioner(numParts: Int) extends Partitioner {
  override def numPartitions: Int = numParts
  override def getPartition(key: Any): Int = {
    val domain = key.asInstanceOf[String].split("@")(1)
    (domain.hashCode & Integer.MAX_VALUE) % numPartitions
  }
}

val emailRdd = sc.parallelize(List(("user@gmail.com", 1), ("admin@yahoo.com", 2)))
val partitioned = emailRdd.partitionBy(new DomainPartitioner(10))
```

### 2.5 Persistence and Caching Levels

By default, RDDs are recomputed every time an action is called. `persist()` / `cache()` stores an RDD's partitions for reuse.

| Storage Level | Meaning |
|---|---|
| `MEMORY_ONLY` | Deserialized Java objects in JVM heap. Default for `cache()`. Fastest but uses the most memory. |
| `MEMORY_AND_DISK` | Spills to disk when memory is insufficient. |
| `MEMORY_ONLY_SER` | Serialized objects in JVM heap. More compact (2--5x less memory) but requires deserialization on read. |
| `MEMORY_AND_DISK_SER` | Serialized in memory, spill to disk. Best for large datasets. |
| `DISK_ONLY` | Stored only on disk. Slowest. |
| `OFF_HEAP` | Stored in off-heap memory (Tungsten). No GC overhead. |
| `*_2` variants | Replicated on 2 nodes. Provides redundancy at the cost of double storage. |

**Guidelines:**
- Use `MEMORY_AND_DISK_SER` for production workloads (compact, fault-tolerant).
- Use `MEMORY_ONLY` only when the dataset fits comfortably in memory and is accessed frequently.
- Always `unpersist()` when a cached RDD is no longer needed.
- DataFrames default to `MEMORY_AND_DISK` with Tungsten's columnar encoding, which is already highly compact.

### 2.6 Accumulators and Broadcast Variables

**Accumulators** are write-only shared variables. Executors add to them; only the driver reads the final value. Used for counters and sums.

```python
error_count = sc.accumulator(0)

def count_errors(line):
    if "ERROR" in line:
        error_count.add(1)
    return line

rdd.map(count_errors).count()
print(f"Errors: {error_count.value}")
```

Caveat: accumulators in transformations may be incremented more than once if a task is retried. Use accumulators only inside actions (`foreach`) for exact counts, or accept approximate counts in transformations.

**Broadcast Variables** are read-only shared variables replicated once per executor (not per task). Used to distribute large lookup tables, ML models, or configuration maps efficiently.

```python
lookup = {"US": "United States", "DE": "Germany", "JP": "Japan"}
broadcast_lookup = sc.broadcast(lookup)

rdd.map(lambda code: broadcast_lookup.value.get(code, "Unknown")).collect()
```

```scala
val lookup = Map("US" -> "United States", "DE" -> "Germany", "JP" -> "Japan")
val broadcastLookup = sc.broadcast(lookup)

rdd.map(code => broadcastLookup.value.getOrElse(code, "Unknown")).collect()
```

Without broadcast, the lookup map would be serialized and shipped with every task. With broadcast, it ships once per executor and is shared across all tasks on that executor.

### 2.7 Fault Tolerance Through Lineage Replay

Spark's fault tolerance model is fundamentally different from systems like Hadoop MapReduce that rely on checkpointing intermediate data to HDFS. Instead, Spark relies on the deterministic lineage graph. If an executor fails:

1. The driver detects the failure via missed heartbeats.
2. The DAG Scheduler identifies which stages had tasks running on the failed executor.
3. For `ShuffleMapStage` outputs that were stored on the failed executor, the stage is resubmitted (shuffle files are lost).
4. For `ResultStage` tasks, only the lost tasks are retried.
5. Cached RDD partitions on the failed executor are recomputed from lineage.

For very long lineage chains, **checkpointing** truncates the lineage by materializing the RDD to reliable storage (HDFS, S3):

```python
sc.setCheckpointDir("hdfs:///checkpoints")
rdd.checkpoint()  # Must be called before any action
rdd.count()       # Triggers checkpointing
# Subsequent actions read from checkpoint, not recompute from lineage
```

---

## 3. Spark SQL and DataFrames

### 3.1 DataFrame and Dataset API

A **DataFrame** is a distributed collection of rows organized into named columns --- conceptually equivalent to a table in a relational database or a pandas DataFrame. Under the hood, a DataFrame is a `Dataset[Row]`. The **Dataset** API (Scala/Java only) adds compile-time type safety via case classes.

```python
# PySpark DataFrame creation
df = spark.read.format("parquet").load("s3a://datalake/events/")
df.printSchema()

# Transformations
result = (df
    .filter(df.event_type == "purchase")
    .groupBy("user_id")
    .agg(
        F.count("*").alias("purchase_count"),
        F.sum("amount").alias("total_spent")
    )
    .filter(F.col("total_spent") > 1000)
    .orderBy(F.desc("total_spent")))
```

```scala
// Scala Dataset with case class
case class Event(userId: String, eventType: String, amount: Double, ts: Long)

val ds: Dataset[Event] = spark.read.parquet("s3a://datalake/events/").as[Event]

val result = ds
  .filter(_.eventType == "purchase")
  .groupByKey(_.userId)
  .agg(
    typed.count[Event](_.eventType).name("purchase_count"),
    typed.sumLong[Event](_.amount.toLong).name("total_spent")
  )
```

**Why DataFrames over RDDs:** The DataFrame API enables Spark's Catalyst optimizer and Tungsten execution engine. RDD operations are opaque to the optimizer --- `rdd.map(f)` tells Spark nothing about what `f` does. DataFrame operations are declarative expressions that Catalyst can analyze, reorder, and optimize.

### 3.2 Catalyst Optimizer

Catalyst is Spark SQL's query optimizer. It converts a logical plan into an optimized physical plan through a series of rule-based and cost-based transformations.

**Pipeline:**

```
SQL Query / DataFrame API
        ↓
Unresolved Logical Plan (column names unresolved)
        ↓ Analysis (resolve references against Catalog)
Resolved Logical Plan
        ↓ Logical Optimization (rule-based)
Optimized Logical Plan
        ↓ Physical Planning (cost-based selection)
Physical Plan(s)
        ↓ Cost Model selects best plan
Selected Physical Plan
        ↓ Code Generation (Tungsten)
RDDs of Internal Row
```

**Key logical optimizations:**
- **Predicate pushdown:** Pushes filters as close to the data source as possible. A `WHERE year = 2024` on a Parquet file becomes a Parquet row group filter, skipping irrelevant blocks entirely.
- **Column pruning:** Only reads columns that are actually referenced in the query. On columnar formats like Parquet, this avoids reading entire row groups of unused columns.
- **Constant folding:** Evaluates constant expressions at compile time.
- **Filter pushthrough:** Pushes filters through joins and aggregations when safe.
- **Join reordering:** Reorders joins to minimize intermediate result sizes (cost-based).

### 3.3 Tungsten Execution Engine

Tungsten is Spark's physical execution backend, focused on CPU and memory efficiency:

1. **Whole-stage code generation:** Instead of interpreting the plan node by node (with virtual function calls per row), Tungsten compiles the entire stage into a single Java function using Janino. This eliminates iterator overhead and enables CPU pipelining.
2. **Binary memory management:** Operates on raw binary data using `sun.misc.Unsafe`, avoiding Java object overhead and GC pressure.
3. **Cache-aware computation:** Sorts and hashes data in binary format that fits CPU cache lines.
4. **Columnar in-memory format:** Cached DataFrames use Tungsten's columnar encoding, which is 10x more compact than deserialized Java objects.

### 3.4 Join Strategies

Spark SQL supports multiple join strategies, selected by the optimizer based on table sizes and statistics:

**Broadcast Hash Join (BHJ).** The smaller side is broadcast to all executors. Each executor builds a hash table from the broadcast data and probes it with the larger side. No shuffle required. Optimal when one side fits in memory.

```python
# Force broadcast
from pyspark.sql.functions import broadcast
result = large_df.join(broadcast(small_df), "join_key")
```

Threshold: `spark.sql.autoBroadcastJoinThreshold` (default 10MB). Set to `-1` to disable auto-broadcast.

**Sort-Merge Join (SMJ).** Both sides are shuffled by the join key, sorted within each partition, and merged. The default for equi-joins between two large tables. Handles arbitrarily large data but requires a full shuffle of both sides.

**Shuffle Hash Join (SHJ).** Both sides are shuffled by the join key. The smaller side is built into a hash table per partition. Faster than SMJ when one side is moderately smaller but too large for broadcast. Enabled via `spark.sql.join.preferSortMergeJoin=false`.

**Broadcast Nested Loop Join (BNLJ).** Used for non-equi joins (theta joins) when one side is small enough to broadcast. Performs a nested loop, so `O(n * m)` complexity.

**Cartesian Product.** Last resort for cross joins. Produces `n * m` rows.

### 3.5 Window Functions

Window functions compute aggregates over a sliding window of rows without collapsing the result set.

```python
from pyspark.sql import Window
import pyspark.sql.functions as F

window_spec = Window.partitionBy("department").orderBy("salary")

df_with_rank = df.select(
    "*",
    F.row_number().over(window_spec).alias("row_num"),
    F.rank().over(window_spec).alias("rank"),
    F.dense_rank().over(window_spec).alias("dense_rank"),
    F.lag("salary", 1).over(window_spec).alias("prev_salary"),
    F.lead("salary", 1).over(window_spec).alias("next_salary"),
    F.sum("salary").over(
        Window.partitionBy("department")
              .orderBy("salary")
              .rowsBetween(Window.unboundedPreceding, Window.currentRow)
    ).alias("running_total")
)
```

```scala
import org.apache.spark.sql.expressions.Window
import org.apache.spark.sql.functions._

val windowSpec = Window.partitionBy("department").orderBy("salary")

val dfWithRank = df.select(
  col("*"),
  row_number().over(windowSpec).alias("row_num"),
  rank().over(windowSpec).alias("rank"),
  lag("salary", 1).over(windowSpec).alias("prev_salary"),
  sum("salary").over(
    Window.partitionBy("department")
      .orderBy("salary")
      .rowsBetween(Window.unboundedPreceding, Window.currentRow)
  ).alias("running_total")
)
```

### 3.6 User-Defined Functions (UDFs)

**Deterministic UDFs** produce the same output for the same input. Spark can optimize them (e.g., push them through filters). **Non-deterministic UDFs** (e.g., involving random numbers or external lookups) cannot be optimized this way; mark them with `asNondeterministic()`.

```python
# Python UDF (slow --- serializes data to Python worker)
@F.udf(returnType=StringType())
def normalize_email(email):
    return email.strip().lower() if email else None

# Pandas UDF (fast --- vectorized via Arrow)
@F.pandas_udf(StringType())
def normalize_email_vectorized(emails: pd.Series) -> pd.Series:
    return emails.str.strip().str.lower()
```

**Performance hierarchy for PySpark:**
1. Built-in Spark SQL functions (fastest --- runs in JVM)
2. Spark SQL expressions via `expr()` (same as above)
3. Pandas UDFs / Vectorized UDFs (Arrow-based, near-JVM speed)
4. Python UDFs (slowest --- per-row serialization to Python)

Always prefer built-in functions. Resort to Pandas UDFs only when no built-in equivalent exists. Avoid plain Python UDFs in production.

---

## 4. Spark Streaming and Structured Streaming

### 4.1 Micro-Batch vs Continuous Processing

**Spark Structured Streaming** treats a stream as an unbounded table. New data arrives as new rows appended to the table. Queries are expressed using the same DataFrame API as batch, and Spark incrementally processes them.

**Micro-batch mode** (default): Spark checks for new data at a configurable trigger interval, processes it as a small batch, and writes results. Provides exactly-once guarantees and reuses the full batch Catalyst/Tungsten pipeline. Typical latency: 100ms to seconds.

```python
query = (spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "broker:9092")
    .option("subscribe", "events")
    .load()
    .selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
    .writeStream
    .format("parquet")
    .option("path", "s3a://datalake/events_stream/")
    .option("checkpointLocation", "s3a://datalake/_checkpoints/events/")
    .trigger(processingTime="30 seconds")
    .start())
```

**Continuous processing** (experimental since Spark 2.3): Launches long-running tasks that continuously process records. Provides at-least-once guarantees with ~1ms latency. Limited operator support (no aggregations, no joins). Rarely used in production; Flink is typically preferred for sub-second latency requirements.

```python
query = (stream_df.writeStream
    .format("console")
    .trigger(continuous="1 second")  # Continuous processing
    .start())
```

### 4.2 Event-Time Processing and Watermarks

Real-world events arrive out of order. **Event time** is the timestamp embedded in the data (when the event occurred), as opposed to **processing time** (when Spark sees the event).

**Watermarks** define how long Spark waits for late data. A watermark of "10 minutes" means Spark discards data older than `max(event_time_seen) - 10 minutes`.

```python
from pyspark.sql.functions import window, col

windowed = (stream_df
    .withWatermark("event_time", "10 minutes")
    .groupBy(
        window("event_time", "5 minutes"),  # 5-minute tumbling window
        "user_id"
    )
    .agg(F.count("*").alias("event_count")))
```

Without a watermark, Spark must maintain state for every window indefinitely, leading to unbounded memory growth.

### 4.3 Window Types

**Tumbling windows:** Fixed-size, non-overlapping intervals. Every event belongs to exactly one window.

```python
window("event_time", "1 hour")  # [00:00, 01:00), [01:00, 02:00), ...
```

**Sliding windows:** Fixed-size, overlapping intervals. An event may belong to multiple windows.

```python
window("event_time", "1 hour", "15 minutes")  # 1h window, slides every 15m
```

**Session windows:** (Spark 3.2+) Dynamic windows that close after a gap of inactivity. Group events that occur close together.

```python
from pyspark.sql.functions import session_window

session_df = (stream_df
    .withWatermark("event_time", "10 minutes")
    .groupBy(
        session_window("event_time", "30 minutes"),
        "user_id"
    )
    .agg(F.count("*").alias("events_in_session")))
```

### 4.4 State Management

Stateful operations (aggregations, joins, deduplication) require Spark to maintain intermediate state across micro-batches. Spark stores this state in an internal state store backed by RocksDB (default since Spark 3.2 for large state) or an in-memory HashMap.

**mapGroupsWithState** provides low-level control over stateful processing:

```scala
import org.apache.spark.sql.streaming.{GroupState, GroupStateTimeout}

case class UserEvent(userId: String, action: String, ts: Long)
case class UserSession(userId: String, startTs: Long, endTs: Long, count: Int)

def updateSession(
    userId: String,
    events: Iterator[UserEvent],
    state: GroupState[UserSession]
): UserSession = {

  val eventList = events.toList
  val currentSession = state.getOption.getOrElse(
    UserSession(userId, eventList.head.ts, eventList.head.ts, 0)
  )

  val updatedSession = currentSession.copy(
    endTs = eventList.map(_.ts).max,
    count = currentSession.count + eventList.size
  )

  state.update(updatedSession)
  state.setTimeoutDuration("30 minutes")
  updatedSession
}

val sessionDf = eventDs
  .groupByKey(_.userId)
  .mapGroupsWithState(GroupStateTimeout.ProcessingTimeTimeout)(updateSession)
```

**flatMapGroupsWithState** allows emitting zero or more output rows per group update, useful for session windows with custom logic.

### 4.5 Exactly-Once Semantics

Structured Streaming achieves exactly-once end-to-end by combining:

1. **Replayable sources:** Kafka, Kinesis, and file sources support offset tracking. On failure, Spark replays from the last committed offset.
2. **Idempotent sinks:** Sinks that support idempotent writes (Delta Lake, databases with upsert) ensure reprocessing doesn't duplicate output.
3. **Checkpoint metadata:** The checkpoint directory stores offset ranges and state snapshots. On restart, Spark recovers from the last consistent checkpoint.

### 4.6 Kafka Integration

```python
# Read from Kafka
kafka_df = (spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "broker1:9092,broker2:9092")
    .option("subscribe", "orders,payments")
    .option("startingOffsets", "earliest")
    .option("maxOffsetsPerTrigger", 100000)
    .option("kafka.security.protocol", "SASL_SSL")
    .option("kafka.sasl.mechanism", "PLAIN")
    .option("kafka.sasl.jaas.config",
            "org.apache.kafka.common.security.plain.PlainLoginModule required "
            "username='$ConnectionString' password='...';"
    )
    .load())

# Parse value (JSON)
parsed = kafka_df.select(
    F.from_json(
        F.col("value").cast("string"),
        schema
    ).alias("data")
).select("data.*")

# Write to Kafka
(result_df.selectExpr("CAST(user_id AS STRING) AS key", "to_json(struct(*)) AS value")
    .writeStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "broker1:9092")
    .option("topic", "enriched_orders")
    .option("checkpointLocation", "/checkpoints/enriched_orders")
    .start())
```

---

## 5. PySpark and Performance

### 5.1 Python Worker Overhead

PySpark's architecture involves inter-process communication between the JVM (where Spark runs) and Python worker processes. For each task that executes Python code (UDFs, RDD operations), data is serialized from the JVM, sent over a socket to a Python process, deserialized, processed, serialized back, and sent to the JVM. This round-trip is the primary source of PySpark overhead.

The overhead is negligible for DataFrame operations that use built-in functions, because those operations execute entirely in the JVM. It only manifests when Python code is invoked per-row or per-batch.

### 5.2 Arrow Optimization and Pandas UDFs

Apache Arrow provides zero-copy columnar data transfer between the JVM and Python. Instead of serializing row by row with pickle, Arrow batches entire columns in a binary format that both Java and Python can read without conversion.

**Enable Arrow for toPandas() / createDataFrame():**

```python
spark.conf.set("spark.sql.execution.arrow.pyspark.enabled", "true")
spark.conf.set("spark.sql.execution.arrow.pyspark.fallback.enabled", "true")
```

**Pandas UDFs (Vectorized UDFs):**

```python
import pandas as pd
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import DoubleType

# Scalar Pandas UDF --- operates on pd.Series, returns pd.Series
@pandas_udf(DoubleType())
def haversine_distance(lat1: pd.Series, lon1: pd.Series,
                       lat2: pd.Series, lon2: pd.Series) -> pd.Series:
    R = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat / 2)**2 +
         np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2)**2)
    return 2 * R * np.arcsin(np.sqrt(a))

# Grouped Map Pandas UDF --- receives a pd.DataFrame per group, returns pd.DataFrame
@pandas_udf(schema, PandasUDFType.GROUPED_MAP)
def normalize_per_group(pdf: pd.DataFrame) -> pd.DataFrame:
    pdf["amount_normalized"] = (pdf["amount"] - pdf["amount"].mean()) / pdf["amount"].std()
    return pdf

df.groupBy("category").apply(normalize_per_group)
```

**Pandas UDF types:**
- **Scalar:** `pd.Series → pd.Series`. Map-like operation per batch.
- **Scalar Iterator:** `Iterator[pd.Series] → Iterator[pd.Series]`. Allows initialization (load a model once).
- **Grouped Map:** `pd.DataFrame → pd.DataFrame`. Full control per group.
- **Grouped Aggregate:** `pd.Series → scalar`. Custom aggregation per group.

### 5.3 PySpark Best Practices

1. **Use DataFrame API, not RDDs.** DataFrame operations run in the JVM. RDD `map`/`filter` with Python lambdas invoke Python workers.
2. **Prefer built-in functions.** `F.col("x") + 1` runs in the JVM. `udf(lambda x: x + 1)` spawns Python workers.
3. **Use Pandas UDFs when custom logic is unavoidable.** 3--100x faster than row-at-a-time Python UDFs.
4. **Avoid `.collect()` on large DataFrames.** It pulls all data to the driver (single machine). Use `.take(n)` or `.show()` for debugging.
5. **Avoid Python-side iteration.** `for row in df.collect()` is a code smell. Express logic as DataFrame transformations.
6. **Leverage `spark.sql()` for complex expressions.** SQL is often more readable and equally optimized by Catalyst.

### 5.4 Avoiding Python UDF Anti-Patterns

```python
# ANTI-PATTERN: Python UDF for something built-in
@F.udf(StringType())
def upper_case(s):
    return s.upper() if s else None

# CORRECT: Use built-in
df.withColumn("name_upper", F.upper(F.col("name")))

# ANTI-PATTERN: Row-by-row Python logic
@F.udf(DoubleType())
def compute_tax(amount, rate):
    return amount * rate

# CORRECT: Built-in expression
df.withColumn("tax", F.col("amount") * F.col("rate"))

# ANTI-PATTERN: Python UDF that queries a database per row
# CORRECT: Broadcast join with a lookup DataFrame
lookup_df = spark.read.jdbc(url, "tax_rates", properties=props)
df.join(broadcast(lookup_df), "state_code")
```

### 5.5 Spark Connect

Spark Connect (Spark 3.4+) decouples the client from the Spark cluster via a gRPC-based thin client protocol. Benefits:

- Remote connectivity: connect from any machine to a running Spark cluster.
- Language independence: the protocol is language-neutral.
- Stability: client upgrades don't require cluster restarts.
- Security: reduced attack surface (no direct JVM access).

```python
# Connect to a remote Spark cluster via Spark Connect
spark = SparkSession.builder \
    .remote("sc://spark-server:15002") \
    .getOrCreate()

# Use the same DataFrame API
df = spark.read.parquet("s3a://datalake/events/")
df.filter(F.col("event_type") == "purchase").count()
```

### 5.6 Delta Lake Integration

Delta Lake adds ACID transactions, schema enforcement, and time travel to Spark's data lake workflows.

```python
# Write Delta table
df.write.format("delta").mode("overwrite").save("s3a://datalake/events_delta/")

# Read Delta table
delta_df = spark.read.format("delta").load("s3a://datalake/events_delta/")

# Time travel
df_v0 = spark.read.format("delta").option("versionAsOf", 0).load("s3a://datalake/events_delta/")
df_yesterday = (spark.read.format("delta")
    .option("timestampAsOf", "2024-01-15")
    .load("s3a://datalake/events_delta/"))

# Upsert (MERGE)
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "s3a://datalake/events_delta/")
target.alias("t").merge(
    updates_df.alias("u"),
    "t.event_id = u.event_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

# Optimize (compaction + Z-ordering)
target.optimize().executeZOrderBy("user_id", "event_time")

# Vacuum (delete old versions)
target.vacuum(168)  # Retain 168 hours (7 days)
```

---

## 6. Performance Tuning

### 6.1 Executor Sizing

The canonical formula for executor sizing on YARN or Kubernetes:

```
Total cluster cores: C
Total cluster memory: M
Cores per executor: 5 (sweet spot --- more causes GC pressure and HDFS contention)
Number of executors: (C / 5) - 1 (reserve 1 core per node for OS/YARN)
Memory per executor: (M / executors) - overhead

Example: 10 nodes × 16 cores × 64 GB
Cores per executor: 5
Executors per node: 3 (15 of 16 cores; 1 for OS)
Total executors: 29 (30 - 1 for YARN ApplicationMaster)
Memory per executor: ~19 GB (64 / 3 nodes, minus overhead)
spark.executor.memoryOverhead: ~2 GB (10% of 19 GB, rounded up)
```

**Why 5 cores?** Beyond 5, the JVM's GC pauses increase due to larger heaps, and HDFS client throughput degrades because each executor opens too many connections.

### 6.2 Partition Tuning

**spark.sql.shuffle.partitions** (default 200): Controls the number of partitions after a shuffle (groupBy, join, distinct). This is the single most impactful tuning parameter for most workloads.

**Rule of thumb:** Target 128 MB per partition. If your shuffle processes 100 GB, set `spark.sql.shuffle.partitions = 800` (100 GB / 128 MB).

**repartition(n):** Performs a full shuffle to produce exactly `n` partitions. Distributes data evenly. Use when increasing partition count or rebalancing skewed data.

**coalesce(n):** Reduces partitions without a full shuffle by merging adjacent partitions. Use only when reducing partition count (e.g., after a heavy filter that leaves many empty partitions).

```python
# After heavy filtering, reduce partition count without shuffle
filtered = large_df.filter(F.col("status") == "active")  # 10000 → 50 partitions of data
result = filtered.coalesce(50)  # Merge without shuffle

# Before writing, repartition for optimal file sizes
result.repartition(100).write.parquet("output/")

# Repartition by column for co-located writes
result.repartition("date", "region").write.partitionBy("date", "region").parquet("output/")
```

### 6.3 Skew Handling

Data skew occurs when some partitions have dramatically more data than others. A single "hot key" can cause one task to run for hours while others finish in seconds.

**Symptoms:** One or a few tasks take 10--100x longer than the median. Spark UI shows uneven task durations.

**Solution 1: Salting.**

```python
import pyspark.sql.functions as F
from pyspark.sql.types import IntegerType

SALT_BUCKETS = 100

# Add salt to the skewed side
skewed_df = skewed_df.withColumn("salt", (F.rand() * SALT_BUCKETS).cast(IntegerType()))
skewed_df = skewed_df.withColumn("salted_key", F.concat(F.col("join_key"), F.lit("_"), F.col("salt")))

# Explode the non-skewed side to match all salts
from pyspark.sql.functions import explode, array, lit
salt_array = array([lit(i) for i in range(SALT_BUCKETS)])
other_df = other_df.withColumn("salt", explode(salt_array))
other_df = other_df.withColumn("salted_key", F.concat(F.col("join_key"), F.lit("_"), F.col("salt")))

# Join on salted key
result = skewed_df.join(other_df, "salted_key")

# Drop salt columns
result = result.drop("salt", "salted_key")
```

**Solution 2: Adaptive Query Execution (AQE).**

AQE (enabled by default since Spark 3.2) dynamically adjusts query plans based on runtime statistics:

```python
spark.conf.set("spark.sql.adaptive.enabled", "true")                     # Default true
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")            # Default true
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5") # Skew threshold
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256m")
```

AQE's skew join optimization detects skewed partitions at runtime and splits them into smaller sub-partitions, replicating the corresponding partition from the other side of the join.

### 6.4 Spill Management

When a task's execution memory is exhausted, Spark **spills** data to disk. Spilling involves serializing in-memory data, writing it to local disk, and later reading it back. This is orders of magnitude slower than in-memory processing.

**Detect spills:** Spark UI → Stages → Task Metrics → "Shuffle Spill (Memory)" and "Shuffle Spill (Disk)". If spill is significant:

1. Increase `spark.executor.memory`.
2. Increase `spark.memory.fraction` (if user memory usage is low).
3. Reduce `spark.sql.shuffle.partitions` per task data volume.
4. Use Kryo serialization to reduce serialized data size.

### 6.5 Broadcast Join Threshold

```python
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "50m")  # Increase from 10MB default
```

A broadcast join avoids the shuffle of one side entirely. If your dimension tables are under 200 MB, consider increasing this threshold. Beyond ~500 MB, broadcast overhead (serialization, network transfer, memory on each executor) may outweigh the shuffle savings.

### 6.6 Adaptive Query Execution (AQE) Deep Dive

AQE's three core optimizations:

1. **Coalescing post-shuffle partitions:** After a shuffle, AQE merges small partitions into larger ones to reduce task overhead. Controlled by `spark.sql.adaptive.advisoryPartitionSizeInBytes` (default 64MB).

2. **Converting sort-merge joins to broadcast joins:** If one side of a join turns out to be small at runtime (after filters), AQE switches to a broadcast join. Controlled by `spark.sql.adaptive.autoBroadcastJoinThreshold`.

3. **Skew join optimization:** Splits skewed partitions as described above.

```python
# Key AQE configurations
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.minPartitionSize", "1m")
spark.conf.set("spark.sql.adaptive.advisoryPartitionSizeInBytes", "128m")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
```

### 6.7 Dynamic Resource Allocation

Dynamic allocation adjusts executor count based on workload. Idle executors are released; new executors are requested when pending tasks exist.

```python
spark.conf.set("spark.dynamicAllocation.enabled", "true")
spark.conf.set("spark.dynamicAllocation.minExecutors", "2")
spark.conf.set("spark.dynamicAllocation.maxExecutors", "100")
spark.conf.set("spark.dynamicAllocation.executorIdleTimeout", "120s")
spark.conf.set("spark.dynamicAllocation.schedulerBacklogTimeout", "5s")
spark.conf.set("spark.shuffle.service.enabled", "true")  # Required for YARN
```

On Kubernetes, dynamic allocation uses executor pod lifecycle instead of the external shuffle service (though the shuffle service is recommended for long-running Spark applications).

---

## 7. Spark on Kubernetes

### 7.1 spark-submit on Kubernetes

Spark's native Kubernetes integration uses the Kubernetes API to schedule driver and executor pods.

```bash
spark-submit \
  --master k8s://https://k8s-apiserver:6443 \
  --deploy-mode cluster \
  --name etl-pipeline \
  --class com.example.ETLPipeline \
  --conf spark.kubernetes.container.image=registry.example.com/spark:3.5.1 \
  --conf spark.kubernetes.namespace=spark-workloads \
  --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark-sa \
  --conf spark.executor.instances=10 \
  --conf spark.executor.memory=8g \
  --conf spark.executor.cores=4 \
  --conf spark.driver.memory=4g \
  --conf spark.driver.cores=2 \
  --conf spark.kubernetes.executor.request.cores=4 \
  --conf spark.kubernetes.executor.limit.cores=4 \
  --conf spark.kubernetes.driver.request.cores=2 \
  --conf spark.kubernetes.driver.limit.cores=2 \
  local:///opt/spark/jars/etl-pipeline.jar
```

The `local://` URI refers to a path inside the container image. The driver pod is created first, which then requests executor pods via the Kubernetes API.

### 7.2 Spark Operator

The **Spark Kubernetes Operator** (maintained by the Kubeflow community) provides a Kubernetes-native way to manage Spark applications using Custom Resource Definitions (CRDs).

```yaml
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: etl-pipeline
  namespace: spark-workloads
spec:
  type: Python
  pythonVersion: "3"
  mode: cluster
  image: registry.example.com/spark:3.5.1-python
  mainApplicationFile: local:///opt/spark/app/etl_pipeline.py
  sparkVersion: "3.5.1"
  restartPolicy:
    type: OnFailure
    onFailureRetries: 3
    onFailureRetryInterval: 30
  driver:
    cores: 2
    memory: "4g"
    serviceAccount: spark-sa
    labels:
      app: etl-pipeline
      role: driver
  executor:
    cores: 4
    instances: 10
    memory: "8g"
    labels:
      app: etl-pipeline
      role: executor
  sparkConf:
    spark.sql.shuffle.partitions: "400"
    spark.sql.adaptive.enabled: "true"
    spark.serializer: "org.apache.spark.serializer.KryoSerializer"
  monitoring:
    exposeDriverMetrics: true
    exposeExecutorMetrics: true
    prometheus:
      jmxExporterJar: /prometheus/jmx_prometheus_javaagent.jar
```

Benefits over raw `spark-submit`: declarative configuration, automatic retry, scheduled applications via `ScheduledSparkApplication`, integration with Kubernetes RBAC, and Prometheus metrics export.

### 7.3 Pod Templates

Pod templates allow fine-grained control over the Kubernetes pod spec for drivers and executors:

```yaml
# executor-pod-template.yaml
apiVersion: v1
kind: Pod
spec:
  nodeSelector:
    node-pool: spark-compute
    kubernetes.io/arch: amd64
  tolerations:
    - key: "spark-workload"
      operator: "Equal"
      value: "true"
      effect: "NoSchedule"
  containers:
    - name: spark-executor
      resources:
        requests:
          ephemeral-storage: "20Gi"
        limits:
          ephemeral-storage: "40Gi"
      volumeMounts:
        - name: spark-local
          mountPath: /data/spark-local
  volumes:
    - name: spark-local
      emptyDir:
        sizeLimit: "40Gi"
  initContainers:
    - name: volume-permissions
      image: busybox:1.36
      command: ["sh", "-c", "chmod 777 /data/spark-local"]
      volumeMounts:
        - name: spark-local
          mountPath: /data/spark-local
```

Reference it via `spark.kubernetes.executor.podTemplateFile`.

### 7.4 Volume Mounts and Cloud Storage

**Local volumes for shuffle/spill:**

```
--conf spark.kubernetes.executor.volumes.emptyDir.spark-local.mount.path=/data/spark-local
--conf spark.kubernetes.executor.volumes.emptyDir.spark-local.options.sizeLimit=50Gi
--conf spark.local.dir=/data/spark-local
```

**S3 (AWS):**

```
--conf spark.hadoop.fs.s3a.endpoint=s3.us-east-1.amazonaws.com
--conf spark.hadoop.fs.s3a.aws.credentials.provider=com.amazonaws.auth.WebIdentityTokenCredentialsProvider
--conf spark.hadoop.fs.s3a.fast.upload=true
--conf spark.hadoop.fs.s3a.fast.upload.buffer=bytebuffer
--conf spark.hadoop.fs.s3a.multipart.size=512m
```

**GCS (GCP):**

```
--conf spark.hadoop.fs.gs.impl=com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem
--conf spark.hadoop.google.cloud.auth.service.account.enable=true
--conf spark.hadoop.google.cloud.auth.service.account.json.keyfile=/secrets/gcs-key.json
```

**ADLS (Azure):**

```
--conf spark.hadoop.fs.azure.account.auth.type.STORAGE_ACCOUNT.dfs.core.windows.net=OAuth
--conf spark.hadoop.fs.azure.account.oauth.provider.type.STORAGE_ACCOUNT.dfs.core.windows.net=org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider
--conf spark.hadoop.fs.azure.account.oauth2.client.id.STORAGE_ACCOUNT.dfs.core.windows.net=CLIENT_ID
--conf spark.hadoop.fs.azure.account.oauth2.client.secret.STORAGE_ACCOUNT.dfs.core.windows.net=CLIENT_SECRET
--conf spark.hadoop.fs.azure.account.oauth2.client.endpoint.STORAGE_ACCOUNT.dfs.core.windows.net=https://login.microsoftonline.com/TENANT_ID/oauth2/token
```

### 7.5 Cost Optimization

**Spot instances / preemptible VMs:** Use for executor pods. The driver should run on on-demand nodes (its loss kills the application).

```yaml
# Executor pod template targeting spot node pool
spec:
  nodeSelector:
    cloud.google.com/gke-spot: "true"  # GKE spot
    # OR: eks.amazonaws.com/capacityType: SPOT  # EKS spot
  tolerations:
    - key: "cloud.google.com/gke-spot"
      operator: "Equal"
      value: "true"
      effect: "NoSchedule"
```

**Node pools:** Separate node pools for different workload profiles --- memory-optimized for caching-heavy jobs, compute-optimized for CPU-bound transformations, spot pools for batch ETL.

**Auto-scaling:** Configure Kubernetes Cluster Autoscaler to scale node pools based on pending pod requests. Dynamic allocation in Spark adjusts executor count, triggering the autoscaler.

### 7.6 Monitoring

**Spark UI:** The driver exposes the Spark UI on port 4040. Expose it via a Kubernetes Service or `kubectl port-forward`. The Spark UI shows jobs, stages, tasks, storage, executors, SQL plans, and streaming statistics.

**Prometheus metrics:**

```
--conf spark.metrics.conf.*.sink.prometheusServlet.class=org.apache.spark.metrics.sink.PrometheusServlet
--conf spark.metrics.conf.*.sink.prometheusServlet.path=/metrics
--conf spark.ui.prometheus.enabled=true
```

Key metrics to monitor:
- `spark_executor_cpuTime` --- CPU utilization
- `spark_executor_memoryUsed` --- memory pressure
- `spark_shuffle_read_bytes` / `spark_shuffle_write_bytes` --- shuffle volume
- `spark_streaming_latency` --- structured streaming processing delay
- `spark_task_duration` --- task duration distribution (detect skew)

**Spark History Server:** For post-mortem analysis of completed applications. Reads event logs from a configured location (S3, GCS, HDFS).

```bash
# Deploy as a Kubernetes Deployment
spark.history.fs.logDirectory=s3a://spark-logs/event-logs/
spark.history.ui.port=18080
```

---

## 8. Security

### 8.1 Kerberos Authentication

On Hadoop clusters, Kerberos is the standard authentication mechanism. Spark integrates with Kerberos via Hadoop's security framework.

```bash
spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --principal spark-user@EXAMPLE.COM \
  --keytab /etc/security/keytabs/spark-user.keytab \
  --conf spark.yarn.keytab=/etc/security/keytabs/spark-user.keytab \
  --conf spark.yarn.principal=spark-user@EXAMPLE.COM \
  application.jar
```

For long-running streaming applications, configure token renewal:

```
spark.hadoop.yarn.resourcemanager.principal=rm/_HOST@EXAMPLE.COM
spark.yarn.access.hadoopFileSystems=hdfs://namenode:8020,s3a://secure-bucket
```

### 8.2 Network Encryption

**RPC encryption (between driver and executors):**

```
spark.authenticate=true
spark.authenticate.secret=<shared secret>  # Use environment variable injection
spark.network.crypto.enabled=true
spark.network.crypto.keyLength=256
spark.network.crypto.keyFactoryAlgorithm=PBKDF2WithHmacSHA256
```

**Shuffle encryption:**

```
spark.io.encryption.enabled=true
spark.io.encryption.keySizeBits=256
spark.io.encryption.keygen.algorithm=HmacSHA256
```

**TLS for Spark UI and REST API:**

```
spark.ssl.enabled=true
spark.ssl.keyStore=/certs/keystore.jks
spark.ssl.keyStorePassword=${KEYSTORE_PASSWORD}
spark.ssl.keyPassword=${KEY_PASSWORD}
spark.ssl.trustStore=/certs/truststore.jks
spark.ssl.trustStorePassword=${TRUSTSTORE_PASSWORD}
spark.ssl.protocol=TLSv1.3
```

### 8.3 ACLs and Authorization

**Spark UI ACLs:**

```
spark.acls.enable=true
spark.admin.acls=admin_user,ops_team
spark.ui.view.acls=*                     # Who can view the UI
spark.modify.acls=admin_user             # Who can kill jobs
spark.ui.view.acls.groups=data-eng       # Group-based ACLs
```

**Spark History Server security:**

```
spark.history.ui.acls.enable=true
spark.history.ui.admin.acls=admin_user
spark.history.ui.admin.acls.groups=platform-team
```

### 8.4 Secret Management

Never embed secrets in Spark configurations or application code.

**Kubernetes secrets:**

```yaml
# Mount secrets as environment variables in pod template
spec:
  containers:
    - name: spark-executor
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: spark-secrets
              key: db-password
        - name: AWS_ACCESS_KEY_ID
          valueFrom:
            secretKeyRef:
              name: aws-credentials
              key: access-key-id
```

**HashiCorp Vault integration:**

```python
import hvac

client = hvac.Client(url="https://vault.example.com:8200")
client.auth.kubernetes.login(role="spark-etl", jwt=open("/var/run/secrets/kubernetes.io/serviceaccount/token").read())
secrets = client.secrets.kv.v2.read_secret_version(path="spark/db-credentials")
db_password = secrets["data"]["data"]["password"]
```

### 8.5 Data Encryption

**At rest:** Use server-side encryption on the storage layer (S3 SSE-KMS, GCS CMEK, ADLS encryption). For local shuffle/spill data, use `spark.io.encryption.enabled=true`.

**In transit:** Enable `spark.network.crypto.enabled=true` for RPC and `spark.io.encryption.enabled=true` for shuffle data. Use TLS for external connections (databases, Kafka).

**In processing:** Sensitive columns should be encrypted/tokenized at the application level before processing. Use Spark's built-in functions for hashing:

```python
from pyspark.sql.functions import sha2, col

df = df.withColumn("email_hash", sha2(col("email"), 256))
df = df.drop("email")  # Remove PII after hashing
```

### 8.6 Multi-Tenant Security

**RBAC with Apache Ranger:**

Apache Ranger provides centralized security policy management for Hadoop ecosystem components, including Spark SQL.

- Define policies per database, table, column, and row.
- Integrate with LDAP/AD for user and group management.
- Audit all access through Ranger's audit framework.

```xml
<!-- ranger-spark-security.xml -->
<property>
  <name>ranger.plugin.spark.service.name</name>
  <value>spark_prod</value>
</property>
<property>
  <name>ranger.plugin.spark.policy.rest.url</name>
  <value>https://ranger-admin:6182</value>
</property>
```

**SQL Views for Row/Column Security:**

```sql
-- Column masking: hide sensitive data from unauthorized users
CREATE VIEW public_customers AS
SELECT
    customer_id,
    CASE WHEN is_member_of_role('pii_readers')
         THEN email
         ELSE sha2(email, 256)
    END AS email,
    CASE WHEN is_member_of_role('pii_readers')
         THEN phone
         ELSE 'REDACTED'
    END AS phone,
    city,
    state
FROM raw_customers;

-- Row-level security: restrict by region
CREATE VIEW regional_orders AS
SELECT * FROM orders
WHERE region = current_user_region();
```

---

## 9. Data Engineering Patterns

### 9.1 Medallion Architecture (Bronze/Silver/Gold)

The medallion architecture (popularized by Databricks) organizes data into three quality tiers:

**Bronze (Raw).** Ingested data in its original format. No transformations except adding metadata (ingestion timestamp, source, batch ID). Schema-on-read. Retained for auditability and reprocessing.

**Silver (Cleaned).** Data after validation, deduplication, type casting, and null handling. Schema-enforced. Joins with reference data. This layer serves as the "single source of truth."

**Gold (Business).** Aggregated, denormalized datasets optimized for specific use cases (dashboards, ML feature stores, reporting). Pre-computed metrics, star schema dimensions.

```python
# Bronze: ingest raw JSON
bronze_df = (spark.read
    .format("json")
    .option("mode", "PERMISSIVE")
    .option("columnNameOfCorruptRecord", "_corrupt_record")
    .schema(raw_schema)
    .load("s3a://raw-zone/events/2024/01/15/"))

bronze_df = bronze_df.withColumn("_ingested_at", F.current_timestamp())
bronze_df = bronze_df.withColumn("_source_file", F.input_file_name())

bronze_df.write.format("delta").mode("append").save("s3a://bronze/events/")

# Silver: clean and deduplicate
silver_df = (spark.read.format("delta").load("s3a://bronze/events/")
    .filter(F.col("_corrupt_record").isNull())
    .drop("_corrupt_record")
    .withColumn("event_time", F.to_timestamp("event_time_str", "yyyy-MM-dd'T'HH:mm:ss.SSSZ"))
    .withColumn("amount", F.col("amount").cast("decimal(18,2)"))
    .filter(F.col("event_id").isNotNull())
    .dropDuplicates(["event_id"]))

silver_df.write.format("delta").mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save("s3a://silver/events/")

# Gold: business aggregation
gold_df = (spark.read.format("delta").load("s3a://silver/events/")
    .filter(F.col("event_type") == "purchase")
    .groupBy(
        F.date_trunc("day", F.col("event_time")).alias("date"),
        F.col("product_category")
    )
    .agg(
        F.count("*").alias("order_count"),
        F.sum("amount").alias("revenue"),
        F.avg("amount").alias("avg_order_value"),
        F.countDistinct("user_id").alias("unique_customers")
    ))

gold_df.write.format("delta").mode("overwrite").save("s3a://gold/daily_revenue/")
```

### 9.2 Change Data Capture (CDC) Processing

CDC captures row-level changes (INSERT, UPDATE, DELETE) from source databases and applies them to the data lake.

```python
# CDC records from Debezium (Kafka Connect)
# Schema: {"op": "c|u|d|r", "before": {...}, "after": {...}, "ts_ms": ..., "source": {...}}

cdc_df = (spark.read.format("delta").load("s3a://bronze/cdc/customers/")
    .filter(F.col("_ingested_at") > last_processed_timestamp))

# Apply CDC to target Delta table
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "s3a://silver/customers/")

# Deduplicate CDC events (keep latest per key)
deduped = (cdc_df
    .withColumn("rn", F.row_number().over(
        Window.partitionBy("after.customer_id").orderBy(F.desc("ts_ms"))
    ))
    .filter(F.col("rn") == 1)
    .drop("rn"))

# Separate deletes from upserts
deletes = deduped.filter(F.col("op") == "d").select("before.customer_id")
upserts = deduped.filter(F.col("op").isin("c", "u", "r")).select("after.*")

# Apply upserts
target.alias("t").merge(
    upserts.alias("u"),
    "t.customer_id = u.customer_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

# Apply deletes (soft delete or hard delete)
target.alias("t").merge(
    deletes.alias("d"),
    "t.customer_id = d.customer_id"
).whenMatchedUpdate(set={"is_deleted": F.lit(True), "deleted_at": F.current_timestamp()}) \
 .execute()
```

### 9.3 SCD Type 2 Implementation

Slowly Changing Dimension Type 2 maintains full history by creating new rows for changes.

```python
from delta.tables import DeltaTable
from pyspark.sql import functions as F

target = DeltaTable.forPath(spark, "s3a://silver/dim_customer/")
incoming = spark.read.format("delta").load("s3a://bronze/customers_snapshot/")

# Join incoming with current active records
current_active = target.toDF().filter(F.col("is_current") == True)

# Identify changes
changes = (incoming.alias("new")
    .join(current_active.alias("old"), "customer_id", "left")
    .filter(
        F.col("old.customer_id").isNull() |  # New record
        (F.col("new.name") != F.col("old.name")) |  # Changed fields
        (F.col("new.address") != F.col("old.address")) |
        (F.col("new.email") != F.col("old.email"))
    )
    .select("new.*"))

# Close existing records (set end date and is_current=False)
target.alias("t").merge(
    changes.alias("c"),
    "t.customer_id = c.customer_id AND t.is_current = true"
).whenMatchedUpdate(set={
    "end_date": F.current_date(),
    "is_current": F.lit(False)
}).execute()

# Insert new versions
new_records = (changes
    .withColumn("start_date", F.current_date())
    .withColumn("end_date", F.lit("9999-12-31").cast("date"))
    .withColumn("is_current", F.lit(True))
    .withColumn("surrogate_key", F.monotonically_increasing_id()))

new_records.write.format("delta").mode("append").save("s3a://silver/dim_customer/")
```

### 9.4 Data Quality Checks

```python
from pyspark.sql import functions as F

def run_quality_checks(df, table_name):
    checks = []

    # Completeness: no nulls in required columns
    for col_name in ["event_id", "user_id", "event_time"]:
        null_count = df.filter(F.col(col_name).isNull()).count()
        checks.append({
            "table": table_name,
            "check": f"null_check_{col_name}",
            "passed": null_count == 0,
            "details": f"{null_count} nulls found"
        })

    # Uniqueness: no duplicate primary keys
    total = df.count()
    distinct = df.select("event_id").distinct().count()
    checks.append({
        "table": table_name,
        "check": "pk_uniqueness",
        "passed": total == distinct,
        "details": f"{total - distinct} duplicates"
    })

    # Freshness: data is not stale
    max_time = df.agg(F.max("event_time")).collect()[0][0]
    from datetime import datetime, timedelta
    is_fresh = max_time > datetime.now() - timedelta(hours=2)
    checks.append({
        "table": table_name,
        "check": "freshness",
        "passed": is_fresh,
        "details": f"latest record: {max_time}"
    })

    # Range: amounts are non-negative
    negative_count = df.filter(F.col("amount") < 0).count()
    checks.append({
        "table": table_name,
        "check": "amount_range",
        "passed": negative_count == 0,
        "details": f"{negative_count} negative amounts"
    })

    quality_df = spark.createDataFrame(checks)
    quality_df.write.format("delta").mode("append").save("s3a://metadata/quality_checks/")

    failures = [c for c in checks if not c["passed"]]
    if failures:
        raise ValueError(f"Quality checks failed: {failures}")

    return True
```

### 9.5 Incremental Processing

```python
# Track processed watermark in Delta table metadata
from delta.tables import DeltaTable

# Read last processed watermark
watermark_df = spark.read.format("delta").load("s3a://metadata/watermarks/")
last_watermark = (watermark_df
    .filter(F.col("pipeline") == "events_etl")
    .agg(F.max("watermark_value"))
    .collect()[0][0])

# Read only new data
new_data = (spark.read.format("delta").load("s3a://bronze/events/")
    .filter(F.col("_ingested_at") > last_watermark))

if new_data.count() == 0:
    print("No new data to process")
else:
    # Process and write
    processed = transform(new_data)
    processed.write.format("delta").mode("append").save("s3a://silver/events/")

    # Update watermark
    new_watermark = new_data.agg(F.max("_ingested_at")).collect()[0][0]
    spark.createDataFrame([{
        "pipeline": "events_etl",
        "watermark_value": new_watermark,
        "processed_at": datetime.now().isoformat()
    }]).write.format("delta").mode("append").save("s3a://metadata/watermarks/")
```

### 9.6 Table Format Integration

**Delta Lake:** ACID transactions, time travel, MERGE (upserts), Z-ordering, optimize/vacuum. Best integration with Databricks and Spark. Community and proprietary editions.

**Apache Iceberg:** Open table format with vendor-neutral governance (Apache Foundation). Hidden partitioning (partition evolution without rewriting data), schema evolution, branching/tagging. Strong multi-engine support (Spark, Flink, Trino, Presto).

```python
# Iceberg example
spark.sql("CREATE TABLE catalog.db.events ("
          "  event_id STRING, user_id STRING, event_time TIMESTAMP, amount DECIMAL(18,2)"
          ") USING iceberg "
          "PARTITIONED BY (days(event_time))")

df.writeTo("catalog.db.events").append()

# Snapshot expiration
spark.sql("CALL catalog.system.expire_snapshots('db.events', TIMESTAMP '2024-01-01')")
```

**Apache Hudi:** Copy-on-write and merge-on-read table types. Optimized for CDC and incremental processing. Compaction for merge-on-read tables. Record-level indexing for fast upserts.

```python
# Hudi example
hudi_options = {
    "hoodie.table.name": "events",
    "hoodie.datasource.write.recordkey.field": "event_id",
    "hoodie.datasource.write.partitionpath.field": "event_date",
    "hoodie.datasource.write.precombine.field": "event_time",
    "hoodie.datasource.write.operation": "upsert",
    "hoodie.upsert.shuffle.parallelism": "200"
}

df.write.format("hudi").options(**hudi_options).mode("append").save("s3a://datalake/hudi/events/")
```

---

## 10. Lab Exercises

### Lab 1: Complete ETL Pipeline (JSON to Bronze to Silver to Gold with Delta Lake)

**Objective:** Build a production-grade ETL pipeline that ingests raw JSON event data, cleans it, and produces business aggregations using the medallion architecture.

**Setup:**

```python
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    TimestampType, IntegerType
)
from delta.tables import DeltaTable

spark = SparkSession.builder \
    .appName("lab1-etl-pipeline") \
    .config("spark.jars.packages", "io.delta:delta-spark_2.12:3.1.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .getOrCreate()
```

**Step 1: Generate sample data.**

```python
import json
import random
from datetime import datetime, timedelta

def generate_events(n=100000):
    events = []
    categories = ["electronics", "clothing", "food", "books", "sports"]
    event_types = ["view", "add_to_cart", "purchase", "return"]
    base_time = datetime(2024, 1, 1)

    for i in range(n):
        event = {
            "event_id": f"evt-{i:08d}",
            "user_id": f"user-{random.randint(1, 10000):05d}",
            "event_type": random.choice(event_types),
            "product_id": f"prod-{random.randint(1, 500):04d}",
            "category": random.choice(categories),
            "amount": round(random.uniform(5.0, 500.0), 2) if random.random() > 0.1 else None,
            "event_time": (base_time + timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "metadata": {"browser": random.choice(["chrome", "firefox", "safari"]),
                         "platform": random.choice(["web", "mobile", "tablet"])}
        }
        # Introduce some bad records
        if random.random() < 0.01:
            event["event_time"] = "INVALID_DATE"
        if random.random() < 0.005:
            event["event_id"] = events[-1]["event_id"] if events else event["event_id"]  # Duplicate

        events.append(json.dumps(event))

    return events

# Write to file (in practice, this comes from Kafka or S3)
events = generate_events()
rdd = spark.sparkContext.parallelize(events)
raw_df = spark.read.json(rdd)
raw_df.write.mode("overwrite").json("/tmp/lab1/raw/events/")
```

**Step 2: Bronze layer.**

```python
raw_schema = StructType([
    StructField("event_id", StringType()),
    StructField("user_id", StringType()),
    StructField("event_type", StringType()),
    StructField("product_id", StringType()),
    StructField("category", StringType()),
    StructField("amount", DoubleType()),
    StructField("event_time", StringType()),
    StructField("metadata", StructType([
        StructField("browser", StringType()),
        StructField("platform", StringType())
    ]))
])

bronze_df = (spark.read
    .format("json")
    .option("mode", "PERMISSIVE")
    .option("columnNameOfCorruptRecord", "_corrupt_record")
    .schema(raw_schema.add("_corrupt_record", StringType()))
    .load("/tmp/lab1/raw/events/"))

bronze_df = (bronze_df
    .withColumn("_ingested_at", F.current_timestamp())
    .withColumn("_source_file", F.input_file_name())
    .withColumn("_batch_id", F.lit("batch-001")))

bronze_df.write.format("delta").mode("overwrite").save("/tmp/lab1/bronze/events/")

corrupt_count = bronze_df.filter(F.col("_corrupt_record").isNotNull()).count()
total_count = bronze_df.count()
print(f"Bronze: {total_count} records, {corrupt_count} corrupt")
```

**Step 3: Silver layer.**

```python
bronze = spark.read.format("delta").load("/tmp/lab1/bronze/events/")

silver_df = (bronze
    .filter(F.col("_corrupt_record").isNull())
    .drop("_corrupt_record")
    # Parse and validate event_time
    .withColumn("event_time_parsed",
        F.to_timestamp("event_time", "yyyy-MM-dd'T'HH:mm:ss.SSSZ"))
    .filter(F.col("event_time_parsed").isNotNull())  # Drop unparseable dates
    .drop("event_time")
    .withColumnRenamed("event_time_parsed", "event_time")
    # Type casting
    .withColumn("amount", F.col("amount").cast("decimal(18,2)"))
    # Null handling
    .withColumn("amount", F.coalesce(F.col("amount"), F.lit(0).cast("decimal(18,2)")))
    # Validate required fields
    .filter(F.col("event_id").isNotNull())
    .filter(F.col("user_id").isNotNull())
    # Deduplicate
    .dropDuplicates(["event_id"])
    # Flatten metadata
    .withColumn("browser", F.col("metadata.browser"))
    .withColumn("platform", F.col("metadata.platform"))
    .drop("metadata")
    # Add derived columns
    .withColumn("event_date", F.to_date("event_time"))
    .withColumn("event_hour", F.hour("event_time")))

silver_df.write.format("delta") \
    .mode("overwrite") \
    .partitionBy("event_date") \
    .save("/tmp/lab1/silver/events/")

print(f"Silver: {silver_df.count()} records (dropped {total_count - silver_df.count()})")
```

**Step 4: Gold layer.**

```python
silver = spark.read.format("delta").load("/tmp/lab1/silver/events/")

# Daily revenue by category
daily_revenue = (silver
    .filter(F.col("event_type") == "purchase")
    .groupBy("event_date", "category")
    .agg(
        F.count("*").alias("order_count"),
        F.sum("amount").alias("revenue"),
        F.avg("amount").alias("avg_order_value"),
        F.countDistinct("user_id").alias("unique_customers"),
        F.countDistinct("product_id").alias("unique_products")
    )
    .orderBy("event_date", "category"))

daily_revenue.write.format("delta").mode("overwrite").save("/tmp/lab1/gold/daily_revenue/")

# User activity summary
user_summary = (silver
    .groupBy("user_id")
    .agg(
        F.count("*").alias("total_events"),
        F.sum(F.when(F.col("event_type") == "purchase", F.col("amount")).otherwise(0))
         .alias("total_spent"),
        F.count(F.when(F.col("event_type") == "purchase", 1)).alias("purchase_count"),
        F.min("event_time").alias("first_event"),
        F.max("event_time").alias("last_event"),
        F.countDistinct("event_date").alias("active_days")
    )
    .withColumn("avg_purchase_value",
        F.when(F.col("purchase_count") > 0,
               F.col("total_spent") / F.col("purchase_count"))
         .otherwise(0)))

user_summary.write.format("delta").mode("overwrite").save("/tmp/lab1/gold/user_summary/")

daily_revenue.show(10)
user_summary.orderBy(F.desc("total_spent")).show(10)
```

---

### Lab 2: Real-Time Streaming Pipeline (Kafka to Spark Structured Streaming to PostgreSQL)

**Objective:** Build a streaming pipeline that consumes events from Kafka, aggregates them in real-time windows, and sinks results to PostgreSQL.

```python
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType

spark = SparkSession.builder \
    .appName("lab2-streaming-pipeline") \
    .config("spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,"
            "org.postgresql:postgresql:42.7.1") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()

# Define schema for Kafka messages
event_schema = StructType([
    StructField("event_id", StringType()),
    StructField("user_id", StringType()),
    StructField("event_type", StringType()),
    StructField("amount", DoubleType()),
    StructField("category", StringType()),
    StructField("event_time", LongType())  # epoch millis
])

# Read from Kafka
kafka_stream = (spark.readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "localhost:9092")
    .option("subscribe", "events")
    .option("startingOffsets", "latest")
    .option("maxOffsetsPerTrigger", 10000)
    .load())

# Parse JSON values
parsed = (kafka_stream
    .select(
        F.from_json(F.col("value").cast("string"), event_schema).alias("data"),
        F.col("timestamp").alias("kafka_time")
    )
    .select("data.*", "kafka_time")
    .withColumn("event_time",
        F.to_timestamp(F.col("event_time") / 1000))
    .filter(F.col("event_id").isNotNull()))

# Windowed aggregation with watermark
windowed_agg = (parsed
    .withWatermark("event_time", "5 minutes")
    .groupBy(
        F.window("event_time", "1 minute"),
        "category"
    )
    .agg(
        F.count("*").alias("event_count"),
        F.sum(F.when(F.col("event_type") == "purchase", F.col("amount"))
              .otherwise(0)).alias("revenue"),
        F.countDistinct("user_id").alias("unique_users")
    )
    .select(
        F.col("window.start").alias("window_start"),
        F.col("window.end").alias("window_end"),
        "category",
        "event_count",
        "revenue",
        "unique_users"
    ))

# Write to PostgreSQL via foreachBatch
def write_to_postgres(batch_df, batch_id):
    if batch_df.count() == 0:
        return

    (batch_df.write
        .format("jdbc")
        .option("url", "jdbc:postgresql://localhost:5432/analytics")
        .option("dbtable", "realtime_metrics")
        .option("user", "spark_writer")
        .option("password", "${DB_PASSWORD}")  # Use env var in production
        .option("driver", "org.postgresql.Driver")
        .mode("append")
        .save())

    print(f"Batch {batch_id}: wrote {batch_df.count()} rows")

# Start streaming query
query = (windowed_agg.writeStream
    .foreachBatch(write_to_postgres)
    .outputMode("update")
    .option("checkpointLocation", "/tmp/lab2/checkpoints/realtime_metrics/")
    .trigger(processingTime="30 seconds")
    .start())

# Monitor in a separate thread or just wait
# query.awaitTermination()
```

**PostgreSQL table setup:**

```sql
CREATE TABLE realtime_metrics (
    window_start    TIMESTAMP NOT NULL,
    window_end      TIMESTAMP NOT NULL,
    category        VARCHAR(50) NOT NULL,
    event_count     BIGINT,
    revenue         DECIMAL(18, 2),
    unique_users    BIGINT,
    PRIMARY KEY (window_start, window_end, category)
);

-- For upsert behavior, use ON CONFLICT in foreachBatch:
-- INSERT INTO realtime_metrics (...) VALUES (...)
-- ON CONFLICT (window_start, window_end, category)
-- DO UPDATE SET event_count = EXCLUDED.event_count, ...;
```

---

### Lab 3: Performance Tuning a Skewed Join (Before/After Benchmarks)

**Objective:** Demonstrate the impact of data skew on join performance and apply salting + AQE to fix it.

```python
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import IntegerType
import time

spark = SparkSession.builder \
    .appName("lab3-skew-tuning") \
    .config("spark.sql.adaptive.enabled", "false")  # Disable AQE to see raw skew first \
    .config("spark.sql.shuffle.partitions", "200") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .getOrCreate()

# Generate skewed data: 90% of records have join_key = "hot_key"
num_records = 10_000_000
skewed_data = (spark.range(num_records)
    .withColumn("join_key",
        F.when(F.rand() < 0.9, F.lit("hot_key"))
         .otherwise(F.concat(F.lit("key_"), (F.rand() * 1000).cast(IntegerType()).cast("string")))
    )
    .withColumn("value_a", F.rand() * 100))

# Dimension table (small, no skew)
dim_data = (spark.range(1001)
    .withColumn("join_key",
        F.when(F.col("id") == 0, F.lit("hot_key"))
         .otherwise(F.concat(F.lit("key_"), F.col("id").cast("string")))
    )
    .withColumn("value_b", F.rand() * 50)
    .drop("id"))

# Cache inputs to isolate join performance
skewed_data.cache().count()
dim_data.cache().count()

# ---- BEFORE: Naive join with skew ----
start = time.time()
naive_result = skewed_data.join(dim_data, "join_key")
naive_count = naive_result.count()
naive_time = time.time() - start
print(f"Naive join: {naive_count} rows in {naive_time:.1f}s")

# ---- FIX 1: Salting ----
SALT_BUCKETS = 50

salted_skewed = (skewed_data
    .withColumn("salt", (F.rand() * SALT_BUCKETS).cast(IntegerType()))
    .withColumn("salted_key", F.concat("join_key", F.lit("_"), "salt")))

from pyspark.sql.functions import explode, array, lit
salt_array = array([lit(i) for i in range(SALT_BUCKETS)])
salted_dim = (dim_data
    .withColumn("salt", explode(salt_array))
    .withColumn("salted_key", F.concat("join_key", F.lit("_"), "salt")))

start = time.time()
salted_result = salted_skewed.join(salted_dim, "salted_key").drop("salt", "salted_key")
salted_count = salted_result.count()
salted_time = time.time() - start
print(f"Salted join: {salted_count} rows in {salted_time:.1f}s")

# ---- FIX 2: AQE skew join ----
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionFactor", "5")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "64m")

start = time.time()
aqe_result = skewed_data.join(dim_data, "join_key")
aqe_count = aqe_result.count()
aqe_time = time.time() - start
print(f"AQE join: {aqe_count} rows in {aqe_time:.1f}s")

# ---- FIX 3: Broadcast join (if dim fits in memory) ----
from pyspark.sql.functions import broadcast

start = time.time()
broadcast_result = skewed_data.join(broadcast(dim_data), "join_key")
broadcast_count = broadcast_result.count()
broadcast_time = time.time() - start
print(f"Broadcast join: {broadcast_count} rows in {broadcast_time:.1f}s")

print("\n--- Benchmark Summary ---")
print(f"{'Method':<20} {'Time (s)':<12} {'Rows':<15}")
print(f"{'Naive (skewed)':<20} {naive_time:<12.1f} {naive_count:<15}")
print(f"{'Salting':<20} {salted_time:<12.1f} {salted_count:<15}")
print(f"{'AQE':<20} {aqe_time:<12.1f} {aqe_count:<15}")
print(f"{'Broadcast':<20} {broadcast_time:<12.1f} {broadcast_count:<15}")
```

**Expected results:** The naive join shows one task running much longer than others. Salting distributes the hot key across 50 partitions. AQE automatically splits the skewed partition. Broadcast eliminates the shuffle entirely (fastest when the dimension table fits in memory).

---

### Lab 4: Securing a Spark Cluster on Kubernetes

**Objective:** Deploy a Spark application on Kubernetes with network encryption, RBAC, and secret management.

**Step 1: Kubernetes namespace and RBAC.**

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: spark-secure
  labels:
    team: data-engineering

---
# service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: spark-sa
  namespace: spark-secure

---
# role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: spark-role
  namespace: spark-secure
rules:
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps", "persistentvolumeclaims"]
    verbs: ["create", "get", "list", "watch", "delete", "patch"]
  - apiGroups: [""]
    resources: ["pods/log"]
    verbs: ["get", "list"]

---
# rolebinding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: spark-rolebinding
  namespace: spark-secure
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: spark-role
subjects:
  - kind: ServiceAccount
    name: spark-sa
    namespace: spark-secure
```

**Step 2: Secret management.**

```yaml
# secrets.yaml (use sealed-secrets or external-secrets-operator in production)
apiVersion: v1
kind: Secret
metadata:
  name: spark-credentials
  namespace: spark-secure
type: Opaque
stringData:
  db-password: "${DB_PASSWORD}"
  s3-access-key: "${AWS_ACCESS_KEY_ID}"
  s3-secret-key: "${AWS_SECRET_ACCESS_KEY}"

---
# TLS certificates for Spark internal communication
apiVersion: v1
kind: Secret
metadata:
  name: spark-tls
  namespace: spark-secure
type: kubernetes.io/tls
data:
  tls.crt: "${BASE64_CERT}"
  tls.key: "${BASE64_KEY}"
  ca.crt: "${BASE64_CA}"
```

**Step 3: Network policy.**

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: spark-network-policy
  namespace: spark-secure
spec:
  podSelector:
    matchLabels:
      app: spark
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Allow driver <-> executor communication
    - from:
        - podSelector:
            matchLabels:
              app: spark
      ports:
        - protocol: TCP
          port: 7078   # Driver RPC
        - protocol: TCP
          port: 7079   # Block manager
  egress:
    # Allow S3/cloud storage access
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
      ports:
        - protocol: TCP
          port: 443
    # Allow Kubernetes API
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 443
    # Allow DNS
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
```

**Step 4: Secure spark-submit.**

```bash
spark-submit \
  --master k8s://https://k8s-apiserver:6443 \
  --deploy-mode cluster \
  --name secure-etl \
  --conf spark.kubernetes.namespace=spark-secure \
  --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark-sa \
  --conf spark.kubernetes.container.image=registry.example.com/spark:3.5.1-secure \
  --conf spark.kubernetes.driver.label.app=spark \
  --conf spark.kubernetes.executor.label.app=spark \
  # Network encryption
  --conf spark.authenticate=true \
  --conf spark.network.crypto.enabled=true \
  --conf spark.network.crypto.keyLength=256 \
  --conf spark.io.encryption.enabled=true \
  # TLS
  --conf spark.ssl.enabled=true \
  --conf spark.ssl.keyStore=/certs/keystore.jks \
  --conf spark.ssl.trustStore=/certs/truststore.jks \
  # Mount secrets
  --conf spark.kubernetes.driver.secretKeyRef.DB_PASSWORD=spark-credentials:db-password \
  --conf spark.kubernetes.executor.secretKeyRef.DB_PASSWORD=spark-credentials:db-password \
  --conf spark.kubernetes.driver.volumes.secret.spark-tls.secretName=spark-tls \
  --conf spark.kubernetes.driver.volumes.secret.spark-tls.mount.path=/certs \
  --conf spark.kubernetes.executor.volumes.secret.spark-tls.secretName=spark-tls \
  --conf spark.kubernetes.executor.volumes.secret.spark-tls.mount.path=/certs \
  # UI access control
  --conf spark.acls.enable=true \
  --conf spark.admin.acls=admin \
  --conf spark.ui.view.acls=data-eng-team \
  # Resource limits (prevent resource abuse)
  --conf spark.executor.memory=4g \
  --conf spark.executor.cores=2 \
  --conf spark.kubernetes.executor.limit.cores=2 \
  --conf spark.kubernetes.executor.request.cores=2 \
  --conf spark.dynamicAllocation.enabled=true \
  --conf spark.dynamicAllocation.maxExecutors=20 \
  local:///opt/spark/app/secure_etl.py
```

**Step 5: Verify security.**

```bash
# Check that pods are running in the correct namespace
kubectl get pods -n spark-secure -l app=spark

# Verify network policy is enforced
kubectl describe networkpolicy spark-network-policy -n spark-secure

# Check that secrets are mounted (not exposed in env)
kubectl exec -n spark-secure spark-driver-pod -- ls /certs/

# Verify TLS is active in Spark UI
kubectl port-forward -n spark-secure svc/spark-driver-svc 4040:4040
# Access https://localhost:4040 (should require TLS)

# Check audit logs for unauthorized access attempts
kubectl logs -n spark-secure -l app=spark | grep -i "auth\|denied\|forbidden"
```

**Security checklist for the lab:**

- [x] RBAC: service account with minimum required permissions
- [x] Secrets: mounted via Kubernetes Secrets, not passed as CLI args
- [x] Network: encrypted RPC and shuffle data
- [x] TLS: enabled for Spark UI and internal communication
- [x] Network policy: ingress/egress limited to required traffic
- [x] ACLs: Spark UI access restricted to authorized users
- [x] Resource limits: prevent executor resource abuse
- [x] Dynamic allocation capped: prevent cluster monopolization

---

## Quick Reference: Key Configuration Parameters

| Parameter | Default | Recommended | Purpose |
|---|---|---|---|
| `spark.executor.memory` | 1g | 4--20g | Executor heap memory |
| `spark.executor.cores` | 1 | 4--5 | Cores per executor |
| `spark.executor.memoryOverhead` | max(384MB, 10%) | 10--15% | Off-heap memory |
| `spark.sql.shuffle.partitions` | 200 | data_size / 128MB | Post-shuffle partitions |
| `spark.sql.adaptive.enabled` | true (3.2+) | true | Adaptive Query Execution |
| `spark.serializer` | JavaSerializer | KryoSerializer | Serialization framework |
| `spark.sql.autoBroadcastJoinThreshold` | 10MB | 50--200MB | Auto broadcast threshold |
| `spark.memory.fraction` | 0.6 | 0.6--0.75 | Unified memory fraction |
| `spark.memory.storageFraction` | 0.5 | 0.5 | Initial storage share |
| `spark.sql.files.maxPartitionBytes` | 128MB | 128MB | Max bytes per file partition |
| `spark.sql.parquet.filterPushdown` | true | true | Parquet predicate pushdown |
| `spark.network.crypto.enabled` | false | true (prod) | RPC encryption |
| `spark.io.encryption.enabled` | false | true (prod) | Shuffle encryption |
| `spark.dynamicAllocation.enabled` | false | true | Auto-scale executors |

---

## Version History

| Version | Key Features |
|---|---|
| 1.0 (2014) | RDD API, standalone scheduler |
| 1.6 (2016) | Dataset API, unified memory management |
| 2.0 (2016) | SparkSession, Structured Streaming, Catalyst overhaul |
| 2.3 (2018) | Continuous processing (experimental), Kubernetes (experimental) |
| 2.4 (2019) | Barrier execution mode, Pandas UDF improvements |
| 3.0 (2020) | Adaptive Query Execution, dynamic partition pruning, Kubernetes GA-track |
| 3.1 (2021) | Kubernetes GA, ANSI SQL mode, RocksDB state store |
| 3.2 (2022) | AQE enabled by default, session windows, push-based shuffle |
| 3.3 (2022) | Performance improvements, error message overhaul |
| 3.4 (2023) | Spark Connect (client-server decoupling), Python packaging improvements |
| 3.5 (2023) | Arrow-optimized Python UDFs, IDENTIFIER clause, distributed ML improvements |
| 4.0 (2024) | ANSI mode default, Spark Connect server improvements, Variant data type |
