# Stream Processing — Real-Time Data Processing Architectures

## Table of Contents

1. [Stream Processing Fundamentals](#1-stream-processing-fundamentals)
2. [Apache Flink](#2-apache-flink)
3. [Apache Kafka Streams](#3-apache-kafka-streams)
4. [Apache Spark Structured Streaming](#4-apache-spark-structured-streaming)
5. [Cloud Streaming Services](#5-cloud-streaming-services)
6. [Windowing and Time](#6-windowing-and-time)
7. [State Management and Fault Tolerance](#7-state-management-and-fault-tolerance)
8. [Patterns and Anti-Patterns](#8-patterns-and-anti-patterns)
9. [Monitoring and Operations](#9-monitoring-and-operations)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Stream Processing Fundamentals

### 1.1 Batch vs Stream vs Micro-Batch

The data processing landscape divides into three paradigms, each with distinct trade-offs between latency, throughput, and complexity.

**Batch Processing** operates on bounded datasets. A job reads an entire dataset, processes it, and produces output. MapReduce and traditional Spark batch jobs exemplify this model. Latency ranges from minutes to hours; throughput is maximized because the system processes data in large chunks with full knowledge of the complete dataset.

**Stream Processing** operates on unbounded datasets — data that arrives continuously without a defined end. True stream processors (Flink, Kafka Streams) handle events one at a time or in small groups as they arrive. Latency drops to milliseconds or seconds. The system must handle incomplete data, out-of-order arrivals, and the concept that "all data" never fully materializes.

**Micro-Batch Processing** is a hybrid approach where Spark Structured Streaming (in its default mode) slices the continuous stream into small batches (typically 100ms-several seconds). Each micro-batch is processed as a small bounded dataset. This provides near-real-time latency (seconds) while reusing batch execution engines.

| Characteristic | Batch | Micro-Batch | True Stream |
|---|---|---|---|
| Latency | Minutes–hours | Seconds | Milliseconds |
| Throughput | Very high | High | High (with back-pressure) |
| Completeness | Full dataset | Near-complete window | Per-event |
| Complexity | Low | Medium | High |
| Fault tolerance | Re-run job | Checkpoint per batch | Continuous checkpointing |

### 1.2 Time Semantics

Stream processing introduces three notions of time that do not exist in batch:

**Event Time** — the time when the event actually occurred at its source. Embedded in the event payload (e.g., a transaction timestamp). This is the most meaningful time for business logic but requires watermark-based tracking because events arrive out of order.

**Processing Time** — the wall-clock time at the machine processing the event. Simplest to implement (just read the clock) but non-deterministic: replaying the same data produces different results depending on processing speed and delays.

**Ingestion Time** — the time when the event enters the streaming system (e.g., when Kafka assigns an offset timestamp). A middle ground: more stable than processing time, more accessible than event time, but still does not reflect when the event actually happened.

```
Source → [Event Time: 10:00:00] → Network delay → [Ingestion Time: 10:00:03] → Queue → [Processing Time: 10:00:07]
```

Choosing the wrong time domain produces incorrect windowed aggregations. A click event at 09:59:59 that arrives at 10:00:05 lands in different windows depending on which time you use.

### 1.3 Watermarks

Watermarks solve the problem of knowing "when is it safe to close a window?" in event-time processing. A watermark is a monotonically increasing timestamp that declares: "No events with timestamps earlier than this will arrive."

**Heuristic watermarks** use observed data patterns (e.g., maximum event time minus an estimated delay). They can be wrong — late data may arrive after the watermark passes.

**Perfect watermarks** are possible only when the source guarantees ordering (rare in distributed systems).

Watermark generation strategies:

```
// Bounded-out-of-orderness: allow up to 5 seconds of lateness
Watermark = max(observed event times) - 5 seconds

// Per-partition tracking: watermark is min across all source partitions
Watermark = min(watermark_partition_0, watermark_partition_1, ..., watermark_partition_n)

// Idle source handling: advance watermark if a source is idle for threshold
if (time_since_last_event > idle_threshold) mark_source_as_idle()
```

When a watermark advances past a window's end time, the window fires. Late events (those arriving after the watermark has passed) can either be dropped, redirected to side outputs, or allowed to trigger window re-computation within an "allowed lateness" interval.

### 1.4 Delivery Semantics

**At-most-once** — events may be lost but never reprocessed. Fastest but unreliable. Achieved by not acknowledging messages and not replaying on failure. Suitable only for metrics where occasional loss is acceptable (e.g., page view counts where 99.9% accuracy suffices).

**At-least-once** — every event is processed at least once, but duplicates are possible. Achieved through acknowledgment and replay on failure without deduplication. Simpler to implement but downstream must be idempotent or tolerate duplicates.

**Exactly-once** — every event affects the output exactly once, even across failures. The hardest guarantee to achieve. Strategies:

1. **Idempotent writes** — make downstream operations naturally idempotent (upserts, conditional writes). The system may process an event multiple times, but the effect is as if it processed once.

2. **Transactional writes** — atomically commit processing progress and output together (Kafka transactions, Flink's two-phase commit sink).

3. **Deduplication** — track processed event IDs and skip duplicates. Requires maintaining a deduplication index.

### 1.5 Event Sourcing

Event sourcing stores the state of an application as a sequence of immutable events rather than mutable current state. Every state change is captured as an event appended to a log.

```
// Traditional CRUD: UPDATE accounts SET balance = 950 WHERE id = 'A'
// Event sourcing:
Event { type: "MoneyWithdrawn", accountId: "A", amount: 50, timestamp: "2024-01-15T10:30:00Z" }
```

Benefits:
- Complete audit trail by construction
- Ability to reconstruct any historical state by replaying events up to a point
- Natural fit for stream processing — the event log IS the stream
- Enables temporal queries ("what was the balance at 3pm yesterday?")

Challenges:
- Event schema evolution (what happens when the event structure changes?)
- Snapshot management (replaying millions of events from scratch is slow)
- Eventual consistency (projections/read models lag behind the event log)

### 1.6 CQRS (Command Query Responsibility Segregation)

CQRS separates the write model (commands that change state) from the read model (queries that retrieve state). Combined with event sourcing:

```
Command → Validate → Produce Event → Event Store (write side)
                                         ↓
                              Stream Processor → Materialized View (read side)
                                         ↓
                              Query Service → Responds to reads
```

The write side handles business validation and produces events. Stream processors consume events and build optimized read-side projections (denormalized views, search indices, aggregation caches). Different read models can coexist — one optimized for dashboards, another for search, another for reporting.

This decoupling allows independent scaling: the write side handles spikes in writes while read replicas scale horizontally for query load.

---

## 2. Apache Flink

### 2.1 Architecture

Flink's distributed runtime consists of:

**JobManager** — the master process responsible for:
- Receiving and scheduling jobs
- Coordinating checkpoints
- Managing failure recovery
- Distributing work across TaskManagers

In high-availability mode, multiple JobManagers run with ZooKeeper or Kubernetes-based leader election.

**TaskManager** — worker processes that:
- Execute the actual data processing tasks (subtasks)
- Manage network buffers for data exchange
- Report heartbeats and metrics to JobManager

Each TaskManager offers a fixed number of **task slots** — units of resource isolation (memory segments). A slot can run one or more operator chains (pipelined operators fused together).

**Dispatcher** — receives job submissions, spawns JobManagers per job (in per-job or application mode), serves the web UI.

**ResourceManager** — negotiates resources with cluster managers (YARN, Kubernetes, standalone).

```
┌─────────────────────────────────────────────────┐
│                   Client                         │
│  (submit JobGraph via REST/CLI)                  │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│              Dispatcher + REST API               │
└──────────────────────┬──────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────┐
│              JobManager (per job)                │
│  - Scheduler (slots → tasks)                    │
│  - Checkpoint Coordinator                       │
│  - Failure Recovery                             │
└──────────┬───────────────────────┬──────────────┘
           ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  TaskManager 1   │    │  TaskManager 2   │
│  ┌────┐ ┌────┐  │    │  ┌────┐ ┌────┐  │
│  │Slot│ │Slot│  │    │  │Slot│ │Slot│  │
│  └────┘ └────┘  │    │  └────┘ └────┘  │
└──────────────────┘    └──────────────────┘
```

### 2.2 DataStream API

The DataStream API is Flink's core API for processing unbounded streams.

**Java example — streaming word count with event-time windowing:**

```java
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.api.java.tuple.Tuple2;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.assigners.TumblingEventTimeWindows;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.util.Collector;

import java.time.Duration;

public class StreamingWordCount {
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(60000); // checkpoint every 60s

        DataStream<String> source = env.fromSource(
            KafkaSource.<String>builder()
                .setBootstrapServers("kafka:9092")
                .setTopics("text-input")
                .setGroupId("word-count-group")
                .setValueOnlyDeserializer(new SimpleStringSchema())
                .build(),
            WatermarkStrategy.<String>forBoundedOutOfOrderness(Duration.ofSeconds(5))
                .withTimestampAssigner((event, timestamp) -> extractTimestamp(event)),
            "kafka-source"
        );

        DataStream<Tuple2<String, Integer>> wordCounts = source
            .flatMap(new Tokenizer())
            .keyBy(value -> value.f0)
            .window(TumblingEventTimeWindows.of(Time.minutes(1)))
            .sum(1);

        wordCounts.sinkTo(buildKafkaSink());

        env.execute("Streaming Word Count");
    }

    public static class Tokenizer implements FlatMapFunction<String, Tuple2<String, Integer>> {
        @Override
        public void flatMap(String value, Collector<Tuple2<String, Integer>> out) {
            for (String word : value.toLowerCase().split("\\W+")) {
                if (word.length() > 0) {
                    out.collect(new Tuple2<>(word, 1));
                }
            }
        }
    }
}
```

**Python (PyFlink) equivalent:**

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaSource, KafkaOffsetsInitializer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.watermark_strategy import WatermarkStrategy
from pyflink.datastream.window import TumblingEventTimeWindows
from pyflink.common.time import Time
import json

env = StreamExecutionEnvironment.get_execution_environment()
env.enable_checkpointing(60000)

kafka_source = KafkaSource.builder() \
    .set_bootstrap_servers("kafka:9092") \
    .set_topics("text-input") \
    .set_group_id("word-count-group") \
    .set_value_only_deserializer(SimpleStringSchema()) \
    .build()

watermark_strategy = WatermarkStrategy \
    .for_bounded_out_of_orderness(Duration.of_seconds(5))

ds = env.from_source(kafka_source, watermark_strategy, "kafka-source")

word_counts = ds \
    .flat_map(lambda line: [(word, 1) for word in line.lower().split()]) \
    .key_by(lambda x: x[0]) \
    .window(TumblingEventTimeWindows.of(Time.minutes(1))) \
    .reduce(lambda a, b: (a[0], a[1] + b[1]))

word_counts.print()
env.execute("PyFlink Word Count")
```

### 2.3 Table API and SQL

Flink's Table API provides a relational abstraction over streams, enabling SQL queries on unbounded data.

```java
import org.apache.flink.table.api.*;
import org.apache.flink.table.api.bridge.java.StreamTableEnvironment;

StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
StreamTableEnvironment tableEnv = StreamTableEnvironment.create(env);

// DDL to define a Kafka-backed table
tableEnv.executeSql("""
    CREATE TABLE transactions (
        transaction_id STRING,
        user_id STRING,
        amount DECIMAL(10, 2),
        currency STRING,
        event_time TIMESTAMP(3),
        WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'transactions',
        'properties.bootstrap.servers' = 'kafka:9092',
        'format' = 'json',
        'scan.startup.mode' = 'latest-offset'
    )
""");

// Windowed aggregation via SQL
Table result = tableEnv.sqlQuery("""
    SELECT
        user_id,
        TUMBLE_START(event_time, INTERVAL '1' HOUR) AS window_start,
        COUNT(*) AS tx_count,
        SUM(amount) AS total_amount
    FROM transactions
    GROUP BY
        user_id,
        TUMBLE(event_time, INTERVAL '1' HOUR)
    HAVING SUM(amount) > 10000
""");

tableEnv.toChangelogStream(result).print();
env.execute("SQL Windowed Aggregation");
```

### 2.4 State Management

Flink provides two categories of state:

**Keyed State** — partitioned by key, accessible only within keyed operations. Types:
- `ValueState<T>` — single value per key
- `ListState<T>` — list of values per key
- `MapState<K, V>` — map per key
- `ReducingState<T>` — single value reduced from all added elements
- `AggregatingState<IN, OUT>` — pre-aggregated state

**Operator State** — not partitioned by key, associated with a parallel operator instance. Used for source connectors (e.g., Kafka partition offsets).

**State Backends:**

| Backend | Storage | Performance | Size Limit | Use Case |
|---|---|---|---|---|
| HashMapStateBackend | JVM heap | Very fast (ns) | Limited by heap | Small state, low latency |
| EmbeddedRocksDBStateBackend | Local disk (RocksDB) | Fast (μs) | Terabytes | Large state, production |

```java
// Configure RocksDB state backend
env.setStateBackend(new EmbeddedRocksDBStateBackend(true)); // true = incremental checkpoints
env.getCheckpointConfig().setCheckpointStorage("s3://checkpoints/flink/job-1");

// Using keyed state in a ProcessFunction
public class FraudDetector extends KeyedProcessFunction<String, Transaction, Alert> {
    private ValueState<Double> runningTotal;
    private ValueState<Long> lastTransactionTime;

    @Override
    public void open(Configuration parameters) {
        ValueStateDescriptor<Double> totalDesc =
            new ValueStateDescriptor<>("running-total", Double.class);
        // Configure state TTL — expire state after 24h of inactivity
        StateTtlConfig ttlConfig = StateTtlConfig.newBuilder(Time.hours(24))
            .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
            .setStateVisibility(StateTtlConfig.StateVisibility.NeverReturnExpired)
            .cleanupFullSnapshot()
            .build();
        totalDesc.enableTimeToLive(ttlConfig);
        runningTotal = getRuntimeContext().getState(totalDesc);
        lastTransactionTime = getRuntimeContext().getState(
            new ValueStateDescriptor<>("last-tx-time", Long.class));
    }

    @Override
    public void processElement(Transaction tx, Context ctx, Collector<Alert> out) throws Exception {
        Double total = runningTotal.value();
        if (total == null) total = 0.0;

        total += tx.getAmount();
        runningTotal.update(total);

        // Register a timer to check velocity
        ctx.timerService().registerEventTimeTimer(tx.getTimestamp() + 60_000);

        if (total > 10_000 && timeSinceLastTx(tx) < 60_000) {
            out.collect(new Alert(tx.getUserId(), "High velocity spending", total));
        }
        lastTransactionTime.update(tx.getTimestamp());
    }

    @Override
    public void onTimer(long timestamp, OnTimerContext ctx, Collector<Alert> out) {
        // Timer-triggered logic for time-based patterns
    }
}
```

### 2.5 Checkpointing and the Chandy-Lamport Algorithm

Flink achieves fault tolerance through **distributed snapshots** based on the Chandy-Lamport algorithm:

1. The JobManager's Checkpoint Coordinator injects **barrier markers** into the source streams at regular intervals.
2. When an operator receives a barrier on one input channel, it performs **barrier alignment** — it buffers records from that channel until barriers arrive on all input channels.
3. Once all barriers are received, the operator snapshots its state and forwards the barrier downstream.
4. When all operators have reported successful snapshots, the checkpoint is complete.

**Aligned checkpoints** provide exactly-once but may increase latency during barrier alignment (back-pressure propagation).

**Unaligned checkpoints** (Flink 1.11+) do not wait for barrier alignment. Instead, they snapshot in-flight records as part of the checkpoint. This eliminates alignment-induced back-pressure at the cost of larger checkpoint sizes.

```java
// Checkpoint configuration
CheckpointConfig config = env.getCheckpointConfig();
config.setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
config.setCheckpointInterval(30_000); // 30 seconds
config.setMinPauseBetweenCheckpoints(10_000); // minimum 10s between checkpoint starts
config.setCheckpointTimeout(120_000); // abort if not complete within 2 minutes
config.setMaxConcurrentCheckpoints(1);
config.setTolerableCheckpointFailureNumber(3);

// Enable unaligned checkpoints for back-pressure-heavy jobs
config.enableUnalignedCheckpoints();
config.setAlignedCheckpointTimeout(Duration.ofSeconds(10)); // fall back to unaligned after 10s

// Externalized checkpoints — retain on cancellation for recovery
config.setExternalizedCheckpointCleanup(
    CheckpointConfig.ExternalizedCheckpointCleanup.RETAIN_ON_CANCELLATION);
```

**Savepoints** are manually triggered, portable snapshots. Unlike checkpoints (which use incremental formats optimized for speed), savepoints capture the full state in a format-independent way. Use savepoints for:
- Job version upgrades
- Cluster migration
- A/B testing with state forking
- Scaling changes (changing parallelism)

```bash
# Trigger a savepoint
flink savepoint <job-id> s3://savepoints/sp-001

# Resume from savepoint with new code
flink run -s s3://savepoints/sp-001 new-job.jar
```

### 2.6 Complex Event Processing (CEP)

Flink's CEP library detects complex patterns across event streams:

```java
import org.apache.flink.cep.CEP;
import org.apache.flink.cep.PatternStream;
import org.apache.flink.cep.pattern.Pattern;
import org.apache.flink.cep.pattern.conditions.SimpleCondition;

// Pattern: three failed login attempts within 5 minutes from same IP
Pattern<LoginEvent, ?> bruteForcePattern = Pattern.<LoginEvent>begin("first-failure")
    .where(new SimpleCondition<LoginEvent>() {
        @Override
        public boolean filter(LoginEvent event) {
            return !event.isSuccess();
        }
    })
    .next("second-failure")
    .where(new SimpleCondition<LoginEvent>() {
        @Override
        public boolean filter(LoginEvent event) {
            return !event.isSuccess();
        }
    })
    .next("third-failure")
    .where(new SimpleCondition<LoginEvent>() {
        @Override
        public boolean filter(LoginEvent event) {
            return !event.isSuccess();
        }
    })
    .within(Time.minutes(5));

// Apply pattern to keyed stream (keyed by IP)
PatternStream<LoginEvent> patternStream = CEP.pattern(
    loginEvents.keyBy(LoginEvent::getIpAddress),
    bruteForcePattern
);

DataStream<SecurityAlert> alerts = patternStream.select(
    (Map<String, List<LoginEvent>> matchedEvents) -> {
        LoginEvent first = matchedEvents.get("first-failure").get(0);
        return new SecurityAlert(
            first.getIpAddress(),
            "Brute force detected: 3 failed attempts in 5 minutes",
            Severity.HIGH
        );
    }
);
```

---

## 3. Apache Kafka Streams

### 3.1 Architecture and Topology

Kafka Streams is a client library (not a cluster) that processes data stored in Kafka topics. It runs as a standard JVM application — no separate infrastructure.

**Topology** — a DAG of stream processors (nodes) connected by streams (edges):
- **Source processors** — consume from Kafka topics
- **Stream processors** — transform data (map, filter, aggregate, join)
- **Sink processors** — produce to Kafka topics

```java
import org.apache.kafka.streams.*;
import org.apache.kafka.streams.kstream.*;

StreamsBuilder builder = new StreamsBuilder();

// Define topology
KStream<String, String> source = builder.stream("input-topic");

KTable<String, Long> wordCounts = source
    .flatMapValues(value -> Arrays.asList(value.toLowerCase().split("\\W+")))
    .groupBy((key, word) -> word)
    .count(Materialized.as("word-counts-store"));

wordCounts.toStream().to("output-topic", Produced.with(Serdes.String(), Serdes.Long()));

// Build and start
Topology topology = builder.build();
KafkaStreams streams = new KafkaStreams(topology, buildProperties());
streams.start();
```

### 3.2 KStream vs KTable

**KStream** — an unbounded stream of records. Each record is an independent event (insert semantics). All records are processed regardless of key.

**KTable** — a changelog stream representing the latest value per key (upsert semantics). Only the latest value for each key is retained. Equivalent to a materialized view of a compacted topic.

**GlobalKTable** — like KTable but replicated in full on every instance. Useful for small lookup datasets (e.g., currency rates, product catalogs).

```java
// KStream: every click event is processed
KStream<String, ClickEvent> clicks = builder.stream("clicks");

// KTable: only latest profile per user is retained
KTable<String, UserProfile> profiles = builder.table("user-profiles");

// GlobalKTable: full product catalog available everywhere
GlobalKTable<String, Product> products = builder.globalTable("products");
```

### 3.3 Joins

Kafka Streams supports multiple join types with different semantics:

**Stream-Stream Join** — correlates events from two streams within a time window. Both sides are unbounded, so a time window bounds the join.

```java
KStream<String, Order> orders = builder.stream("orders");
KStream<String, Payment> payments = builder.stream("payments");

// Join orders with payments that arrive within 30 minutes
KStream<String, EnrichedOrder> enriched = orders.join(
    payments,
    (order, payment) -> new EnrichedOrder(order, payment),
    JoinWindows.ofTimeDifferenceAndGrace(Duration.ofMinutes(30), Duration.ofMinutes(5)),
    StreamJoined.with(Serdes.String(), orderSerde, paymentSerde)
);
```

**Stream-Table Join** — enriches a stream with lookup data from a table. Only the stream side drives the join; when a stream record arrives, it looks up the current table value.

```java
KStream<String, Transaction> transactions = builder.stream("transactions");
KTable<String, Customer> customers = builder.table("customers");

KStream<String, EnrichedTransaction> enriched = transactions.join(
    customers,
    (transaction, customer) -> new EnrichedTransaction(transaction, customer)
);
```

**Table-Table Join** — both sides are tables. The result is also a table that updates whenever either side changes. Useful for materialized joins of two slowly-changing datasets.

```java
KTable<String, Address> addresses = builder.table("addresses");
KTable<String, CustomerInfo> customerInfo = builder.table("customer-info");

KTable<String, FullCustomer> fullCustomers = customerInfo.join(
    addresses,
    (info, address) -> new FullCustomer(info, address)
);
```

### 3.4 Windowed Aggregations

```java
KStream<String, Transaction> transactions = builder.stream("transactions");

// Tumbling window: non-overlapping 1-hour windows
KTable<Windowed<String>, Double> hourlyTotals = transactions
    .groupByKey()
    .windowedBy(TimeWindows.ofSizeAndGrace(Duration.ofHours(1), Duration.ofMinutes(10)))
    .aggregate(
        () -> 0.0,
        (key, tx, total) -> total + tx.getAmount(),
        Materialized.<String, Double, WindowStore<Bytes, byte[]>>as("hourly-totals")
            .withValueSerde(Serdes.Double())
    );

// Session window: gap-based windows (sessions end after 30min inactivity)
KTable<Windowed<String>, Long> sessions = transactions
    .groupByKey()
    .windowedBy(SessionWindows.ofInactivityGapAndGrace(
        Duration.ofMinutes(30), Duration.ofMinutes(5)))
    .count(Materialized.as("session-counts"));
```

### 3.5 Punctuators

Punctuators schedule periodic actions within a processor, independent of incoming records:

```java
public class PeriodicFlushProcessor implements Processor<String, Transaction, String, Alert> {
    private ProcessorContext<String, Alert> context;
    private KeyValueStore<String, AggregatedData> store;

    @Override
    public void init(ProcessorContext<String, Alert> context) {
        this.context = context;
        this.store = context.getStateStore("aggregation-store");

        // Schedule wall-clock punctuation every 30 seconds
        context.schedule(Duration.ofSeconds(30), PunctuationType.WALL_CLOCK_TIME, this::flush);
    }

    private void flush(long timestamp) {
        try (KeyValueIterator<String, AggregatedData> iter = store.all()) {
            while (iter.hasNext()) {
                KeyValue<String, AggregatedData> entry = iter.next();
                if (entry.value.exceedsThreshold()) {
                    context.forward(new Record<>(entry.key,
                        new Alert(entry.key, entry.value), timestamp));
                }
                store.delete(entry.key); // reset after flush
            }
        }
    }

    @Override
    public void process(Record<String, Transaction> record) {
        AggregatedData current = store.get(record.key());
        if (current == null) current = new AggregatedData();
        current.add(record.value());
        store.put(record.key(), current);
    }
}
```

### 3.6 State Stores and Interactive Queries

Kafka Streams materializes state in local RocksDB stores. These stores are queryable from outside the stream processing topology via **Interactive Queries**:

```java
// Query local state store
ReadOnlyKeyValueStore<String, Long> store =
    streams.store(StoreQueryParameters.fromNameAndType(
        "word-counts-store", QueryableStoreTypes.keyValueStore()));

Long count = store.get("kafka"); // query count for key "kafka"

// For distributed queries, determine which instance hosts a key:
KeyQueryMetadata metadata = streams.queryMetadataForKey(
    "word-counts-store", "kafka", Serdes.String().serializer());

if (metadata.activeHost().equals(thisHost)) {
    // Query locally
    return store.get("kafka");
} else {
    // Forward to remote instance via REST
    return httpClient.get(metadata.activeHost() + "/api/count/kafka");
}
```

### 3.7 Exactly-Once Semantics

Kafka Streams achieves exactly-once via Kafka transactions:

```java
Properties props = new Properties();
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2);
// EXACTLY_ONCE_V2 (Kafka 2.5+) uses a single transaction coordinator per thread
// reducing overhead compared to the original EXACTLY_ONCE (per-task transactions)
```

This ensures: reading from input topics, processing, state updates, and writing to output topics are all atomic. If a failure occurs, the transaction is aborted and processing resumes from the last committed offset.

### 3.8 Testing with TopologyTestDriver

```java
import org.apache.kafka.streams.TopologyTestDriver;
import org.apache.kafka.streams.TestInputTopic;
import org.apache.kafka.streams.TestOutputTopic;

@Test
void testWordCount() {
    Topology topology = buildTopology(); // your topology
    Properties props = buildTestProperties();

    try (TopologyTestDriver driver = new TopologyTestDriver(topology, props)) {
        TestInputTopic<String, String> input = driver.createInputTopic(
            "input-topic", new StringSerializer(), new StringSerializer());
        TestOutputTopic<String, Long> output = driver.createOutputTopic(
            "output-topic", new StringDeserializer(), new LongDeserializer());

        input.pipeInput("key1", "hello world");
        input.pipeInput("key2", "hello kafka");

        Map<String, Long> results = output.readKeyValuesToMap();
        assertEquals(2L, results.get("hello"));
        assertEquals(1L, results.get("world"));
        assertEquals(1L, results.get("kafka"));
    }
}
```

---

## 4. Apache Spark Structured Streaming

### 4.1 Micro-Batch vs Continuous Processing

Spark Structured Streaming unifies batch and streaming under the DataFrame/Dataset API. Internally it uses two execution modes:

**Micro-Batch (default)** — processes data in small batches triggered at intervals. Each batch produces a consistent output. Latency: 100ms minimum (Spark 3.x) to seconds. This mode supports all operators and sinks.

**Continuous Processing (experimental since Spark 2.3)** — processes records individually without batching, achieving ~1ms latency. Limited operator support (only map-like operations, no aggregations or joins).

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

spark = SparkSession.builder \
    .appName("StructuredStreamingExample") \
    .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoints") \
    .getOrCreate()

# Read from Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "transactions") \
    .option("startingOffsets", "latest") \
    .load()

# Parse JSON payload
schema = StructType([
    StructField("user_id", StringType()),
    StructField("amount", DoubleType()),
    StructField("currency", StringType()),
    StructField("event_time", TimestampType())
])

transactions = df.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")
```

### 4.2 Watermarks in Structured Streaming

```python
# Define watermark: accept data up to 10 minutes late
windowed_counts = transactions \
    .withWatermark("event_time", "10 minutes") \
    .groupBy(
        window("event_time", "5 minutes"),  # 5-minute tumbling windows
        "user_id"
    ) \
    .agg(
        count("*").alias("tx_count"),
        sum("amount").alias("total_amount"),
        avg("amount").alias("avg_amount")
    )
```

Spark uses the watermark to determine when to discard state for old windows. Data arriving more than 10 minutes late (in this example) is dropped.

### 4.3 Output Modes

| Mode | Behavior | Use Case |
|---|---|---|
| Append | Only new rows that will not change again | Non-aggregation queries, windowed aggregations after watermark |
| Update | Only rows that changed since last trigger | Dashboards, mutable sinks |
| Complete | Entire result table every trigger | Small result sets, debugging |

```python
# Append mode — suitable for windowed aggregations with watermarks
query = windowed_counts.writeStream \
    .outputMode("append") \
    .format("parquet") \
    .option("path", "s3a://data-lake/hourly-aggregates/") \
    .option("checkpointLocation", "s3a://checkpoints/hourly-agg/") \
    .trigger(processingTime="1 minute") \
    .start()

# Update mode — suitable for non-windowed aggregations
query = running_totals.writeStream \
    .outputMode("update") \
    .format("console") \
    .start()
```

### 4.4 Triggers

```python
# Process every 30 seconds (default micro-batch)
.trigger(processingTime="30 seconds")

# Process once (useful for periodic batch-like runs)
.trigger(once=True)

# Available-now trigger — process all available data then stop (Spark 3.3+)
.trigger(availableNow=True)

# Continuous processing (experimental) — ~1ms latency
.trigger(continuous="1 second")
```

### 4.5 foreachBatch Pattern

`foreachBatch` provides a bridge between streaming and batch APIs, enabling arbitrary batch operations per micro-batch:

```python
def write_to_multiple_sinks(batch_df, batch_id):
    """Process each micro-batch with full DataFrame API access."""
    # Deduplicate within the batch
    deduped = batch_df.dropDuplicates(["transaction_id"])

    # Write to Delta Lake
    deduped.write \
        .format("delta") \
        .mode("append") \
        .save("s3a://data-lake/transactions/")

    # Write aggregates to PostgreSQL
    aggregates = deduped.groupBy("user_id") \
        .agg(sum("amount").alias("batch_total"))

    aggregates.write \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://db:5432/analytics") \
        .option("dbtable", "user_batch_totals") \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()

query = transactions.writeStream \
    .foreachBatch(write_to_multiple_sinks) \
    .option("checkpointLocation", "s3a://checkpoints/multi-sink/") \
    .trigger(processingTime="1 minute") \
    .start()
```

### 4.6 Stateful Processing

**mapGroupsWithState** — custom stateful processing returning one result per group per trigger:

```scala
import org.apache.spark.sql.streaming.{GroupState, GroupStateTimeout}

case class UserSession(userId: String, events: List[Event], startTime: Long, lastActivity: Long)
case class SessionOutput(userId: String, duration: Long, eventCount: Int)

def updateSession(
    userId: String,
    events: Iterator[Event],
    state: GroupState[UserSession]
): SessionOutput = {

  // Check for timeout (session expired)
  if (state.hasTimedOut) {
    val session = state.get
    state.remove()
    return SessionOutput(userId, session.lastActivity - session.startTime, session.events.size)
  }

  // Update or create session
  val currentSession = if (state.exists) state.get
    else UserSession(userId, List.empty, System.currentTimeMillis(), 0L)

  val newEvents = events.toList
  val updated = currentSession.copy(
    events = currentSession.events ++ newEvents,
    lastActivity = System.currentTimeMillis()
  )

  state.update(updated)
  state.setTimeoutDuration("30 minutes") // session timeout

  SessionOutput(userId, updated.lastActivity - updated.startTime, updated.events.size)
}

val sessionized = events
  .groupByKey(_.userId)
  .mapGroupsWithState(GroupStateTimeout.ProcessingTimeTimeout)(updateSession)
```

**flatMapGroupsWithState** — same as above but can emit zero or more outputs per group per trigger.

### 4.7 Stream-Stream and Stream-Static Joins

```python
# Stream-stream join with event-time constraints
impressions = spark.readStream.format("kafka").option("subscribe", "impressions").load()
clicks = spark.readStream.format("kafka").option("subscribe", "clicks").load()

# Join impressions with clicks within 1 hour
joined = impressions.join(
    clicks,
    expr("""
        impressions.ad_id = clicks.ad_id AND
        clicks.click_time >= impressions.impression_time AND
        clicks.click_time <= impressions.impression_time + interval 1 hour
    """),
    "leftOuter"  # left outer join to track unclicked impressions
).withWatermark("impression_time", "2 hours")

# Stream-static join (enrich stream with static DataFrame)
dim_products = spark.read.format("delta").load("s3a://warehouse/dim_products/")
enriched = transactions.join(dim_products, "product_id", "left")
```

---

## 5. Cloud Streaming Services

### 5.1 AWS Kinesis

**Kinesis Data Streams** — managed real-time data streaming service.
- Unit of throughput: **shard** (1 MB/s write, 2 MB/s read per shard)
- Retention: 24 hours default, up to 365 days
- Consumer types: shared (2 MB/s per shard shared across consumers) vs enhanced fan-out (2 MB/s per shard per consumer, ~70ms latency)

```python
import boto3
import json
from datetime import datetime

kinesis = boto3.client('kinesis', region_name='us-east-1')

# Produce records
def put_record(stream_name: str, data: dict, partition_key: str):
    kinesis.put_record(
        StreamName=stream_name,
        Data=json.dumps(data).encode('utf-8'),
        PartitionKey=partition_key
    )

# Enhanced fan-out consumer using KCL 2.x
# Consumer registers with Kinesis and receives push-based delivery
# with dedicated throughput per consumer-shard pair
```

**Kinesis Data Firehose** — fully managed delivery to S3, Redshift, OpenSearch, or HTTP endpoints. Zero administration, auto-scaling, built-in transformation via Lambda.

**Kinesis Data Analytics** — runs Apache Flink applications on managed infrastructure. Supports both SQL and Flink DataStream API.

### 5.2 GCP Dataflow (Apache Beam Runner)

Google Cloud Dataflow is a fully managed Apache Beam runner. It executes Beam pipelines with:
- Autoscaling based on backlog
- Built-in monitoring and diagnostics
- Streaming and batch unified model

```python
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, GoogleCloudOptions
from apache_beam.transforms.window import FixedWindows, SlidingWindows
from apache_beam.transforms.trigger import AfterWatermark, AfterCount, AccumulationMode

options = PipelineOptions([
    '--runner=DataflowRunner',
    '--project=my-project',
    '--region=us-central1',
    '--temp_location=gs://my-bucket/temp',
    '--streaming'
])

with beam.Pipeline(options=options) as pipeline:
    events = (
        pipeline
        | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(
            topic='projects/my-project/topics/events',
            timestamp_attribute='event_timestamp')
        | 'ParseJSON' >> beam.Map(json.loads)
    )

    # Windowed aggregation with early and late firings
    windowed = (
        events
        | 'AddTimestamps' >> beam.Map(
            lambda x: beam.window.TimestampedValue(x, x['event_time']))
        | 'Window' >> beam.WindowInto(
            FixedWindows(300),  # 5-minute windows
            trigger=AfterWatermark(
                early=AfterCount(100),  # fire early every 100 elements
                late=AfterCount(1)       # fire for every late element
            ),
            accumulation_mode=AccumulationMode.ACCUMULATING,
            allowed_lateness=600  # accept data up to 10 minutes late
        )
        | 'GroupByUser' >> beam.GroupBy(lambda x: x['user_id'])
        | 'Aggregate' >> beam.CombinePerKey(sum_amounts)
    )

    # Write to BigQuery
    windowed | 'WriteToBQ' >> beam.io.WriteToBigQuery(
        'my-project:analytics.user_hourly_totals',
        write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
        create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
    )
```

### 5.3 Azure Stream Analytics

Azure's managed SQL-based stream processor:
- SQL dialect over streams
- Native integration with Event Hubs, IoT Hub, Blob Storage
- Reference data joins (slowly changing dimensions)
- Built-in ML scoring

```sql
-- Azure Stream Analytics SQL
SELECT
    System.Timestamp() AS WindowEnd,
    IoTHub.ConnectionDeviceId AS DeviceId,
    AVG(temperature) AS AvgTemp,
    MAX(temperature) AS MaxTemp,
    COUNT(*) AS ReadingCount
INTO [output-eventhub]
FROM [input-iothub] TIMESTAMP BY EventEnqueuedUtcTime
GROUP BY
    IoTHub.ConnectionDeviceId,
    TumblingWindow(minute, 5)
HAVING AVG(temperature) > 80
```

**Event Hubs + Azure Functions** — serverless event processing:
- Event Hubs provides Kafka-compatible ingestion (millions of events/second)
- Azure Functions trigger on Event Hub events for lightweight processing
- Consumption-based pricing for sporadic workloads

### 5.4 Comparison Matrix

| Feature | Kinesis | Dataflow | Stream Analytics | Event Hubs + Functions |
|---|---|---|---|---|
| **Throughput** | 1 MB/s per shard | Auto-scales | 1-192 SU | Millions events/s |
| **Latency** | 70ms (EFO) | Seconds | Seconds | Milliseconds |
| **Pricing Model** | Per shard-hour | Per vCPU-hour | Per streaming unit | Per event + execution |
| **Max Retention** | 365 days | N/A (PubSub: 31d) | N/A | 90 days |
| **Language** | Any (KCL/SDK) | Java/Python/Go (Beam) | SQL | Any (Functions runtime) |
| **Managed** | Partial (scale shards) | Fully | Fully | Fully |
| **Exactly-once** | With KCL+DynamoDB | Built-in | At-least-once | At-least-once |
| **Self-hosted alt** | Kafka | Flink/Spark | Flink SQL | Kafka + serverless |
| **Best for** | AWS ecosystem, simple streaming | Complex pipelines, Beam portability | SQL analysts, Azure IoT | Event-driven microservices |

---

## 6. Windowing and Time

### 6.1 Tumbling Windows

Non-overlapping, fixed-size windows. Every event belongs to exactly one window.

```
Timeline: |----W1----|----W2----|----W3----|
Events:    * * *      * *        * * * *

Window size = 5 minutes
W1: [00:00, 00:05)
W2: [00:05, 00:10)
W3: [00:10, 00:15)
```

**Flink:**
```java
stream.keyBy(Event::getUserId)
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .aggregate(new CountAggregate());
```

**Kafka Streams:**
```java
stream.groupByKey()
    .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(5)))
    .count();
```

### 6.2 Sliding (Hopping) Windows

Fixed-size windows that overlap. Defined by size and slide interval. An event may belong to multiple windows.

```
Window size = 10 min, slide = 5 min
Timeline: |-----W1 (00:00-00:10)-----|
               |-----W2 (00:05-00:15)-----|
                    |-----W3 (00:10-00:20)-----|

An event at 00:07 belongs to BOTH W1 and W2.
```

```java
// Flink: 10-minute windows, sliding every 2 minutes
stream.keyBy(Event::getUserId)
    .window(SlidingEventTimeWindows.of(Time.minutes(10), Time.minutes(2)))
    .aggregate(new AverageAggregate());

// Kafka Streams: 10-minute windows, advancing every 5 minutes
stream.groupByKey()
    .windowedBy(SlidingWindows.ofTimeDifferenceAndGrace(
        Duration.ofMinutes(10), Duration.ofMinutes(2)))
    .count();
```

### 6.3 Session Windows

Dynamic windows based on activity gaps. A session starts with an event and ends after a period of inactivity (the gap). No fixed size — sessions vary per key.

```
Gap = 5 min
User A: event@00:00, event@00:03, event@00:04, [gap], event@00:15, event@00:17
         └──── Session 1 (00:00-00:04) ────┘          └── Session 2 (00:15-00:17) ──┘

User B: event@00:01, event@00:10
         └──── Session 1 (00:01-00:01) ──┘  └── Session 2 (00:10-00:10) ──┘
```

```java
// Flink session windows
stream.keyBy(Event::getUserId)
    .window(EventTimeSessionWindows.withGap(Time.minutes(5)))
    .process(new SessionAnalyzer());

// Dynamic session gap based on event type
stream.keyBy(Event::getUserId)
    .window(EventTimeSessionWindows.withDynamicGap(
        (event) -> event.isHighPriority() ? 60_000 : 300_000))
    .aggregate(new SessionAggregate());
```

### 6.4 Global Windows with Triggers

Global windows assign all elements to a single window per key. Without a trigger, they never fire. Triggers control when the global window emits results.

```java
// Fire every 100 elements OR every 30 seconds, whichever comes first
stream.keyBy(Event::getKey)
    .window(GlobalWindows.create())
    .trigger(PurgingTrigger.of(
        CountTrigger.of(100)
            .or(ProcessingTimeTrigger.create(Time.seconds(30)))
    ))
    .aggregate(new BatchAggregate());
```

### 6.5 Allowed Lateness and Side Outputs

```java
// Flink: handle late data with side outputs
final OutputTag<Event> lateDataTag = new OutputTag<Event>("late-data") {};

SingleOutputStreamOperator<Result> mainResults = stream
    .keyBy(Event::getUserId)
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .allowedLateness(Time.minutes(10))
    .sideOutputLateData(lateDataTag)
    .aggregate(new CountAggregate());

// Main results — includes late data that arrived within allowed lateness
mainResults.addSink(mainSink);

// Side output — data that arrived AFTER allowed lateness expired
DataStream<Event> lateData = mainResults.getSideOutput(lateDataTag);
lateData.addSink(lateDataSink); // log or store for separate processing
```

### 6.6 Custom Window Assigners

```java
// Custom window assigner: business-hour windows (9am-5pm, then overnight)
public class BusinessHourWindowAssigner extends WindowAssigner<Object, TimeWindow> {
    @Override
    public Collection<TimeWindow> assignWindows(Object element, long timestamp,
            WindowAssignerContext context) {
        LocalDateTime dt = Instant.ofEpochMilli(timestamp)
            .atZone(ZoneId.of("America/New_York")).toLocalDateTime();

        LocalDate date = dt.toLocalDate();
        long dayStart = date.atTime(9, 0).atZone(ZoneId.of("America/New_York"))
            .toInstant().toEpochMilli();
        long dayEnd = date.atTime(17, 0).atZone(ZoneId.of("America/New_York"))
            .toInstant().toEpochMilli();

        if (timestamp >= dayStart && timestamp < dayEnd) {
            return Collections.singleton(new TimeWindow(dayStart, dayEnd));
        } else {
            // overnight window: 5pm to next 9am
            long overnightStart = dayEnd;
            long overnightEnd = date.plusDays(1).atTime(9, 0)
                .atZone(ZoneId.of("America/New_York")).toInstant().toEpochMilli();
            return Collections.singleton(new TimeWindow(overnightStart, overnightEnd));
        }
    }

    @Override
    public Trigger<Object, TimeWindow> getDefaultTrigger(StreamExecutionEnvironment env) {
        return EventTimeTrigger.create();
    }
}
```

### 6.7 Event Time Skew Handling

When processing multi-source streams, different sources may progress at different rates. Strategies:

1. **Per-partition watermarks** — track watermark per source partition, emit minimum.
2. **Idle source detection** — if a partition produces no events, mark it idle so it does not hold back the global watermark.
3. **Watermark alignment** — limit how far ahead fast sources can advance relative to slow ones.

```java
// Flink: watermark alignment to prevent fast sources from advancing too far
WatermarkStrategy.<Event>forBoundedOutOfOrderness(Duration.ofSeconds(5))
    .withTimestampAssigner((event, ts) -> event.getTimestamp())
    .withIdleness(Duration.ofMinutes(1))        // mark idle after 1 min no data
    .withWatermarkAlignment("alignment-group",   // alignment group name
        Duration.ofSeconds(20),                  // max drift between sources
        Duration.ofSeconds(3));                  // update interval
```

---

## 7. State Management and Fault Tolerance

### 7.1 Local vs Remote State

**Local state** (Flink's default, Kafka Streams' default) — state stored on the processing node itself (heap or embedded RocksDB). Advantages: sub-millisecond access latency, no network round-trips. Disadvantages: recovery requires state restoration from checkpoints.

**Remote state** — state stored in external systems (Redis, DynamoDB, Cassandra). Advantages: state survives node failures without restoration. Disadvantages: every state access incurs network latency (1-10ms), which dominates processing time at high throughput.

Rule of thumb: use local state with checkpointing for primary stream processing state. Use remote state for cross-job shared state or when state must be accessible by non-streaming services.

### 7.2 State Size Management

Large state (hundreds of GB to TB) requires careful management:

1. **State TTL** — automatically expire stale state entries.
2. **Compaction** — RocksDB's background compaction reclaims space from deleted keys.
3. **Incremental checkpoints** — only checkpoint state changes since last checkpoint (RocksDB backend supports this natively by uploading new SST files).
4. **State partitioning** — distribute state across more parallel instances (increase parallelism).

```java
// Flink State TTL configuration
StateTtlConfig ttlConfig = StateTtlConfig.newBuilder(Time.days(7))
    .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
    .setStateVisibility(StateTtlConfig.StateVisibility.NeverReturnExpired)
    .cleanupInRocksdbCompactFilter(1000)  // check every 1000 entries during compaction
    .build();

ValueStateDescriptor<SessionData> descriptor =
    new ValueStateDescriptor<>("session-state", SessionData.class);
descriptor.enableTimeToLive(ttlConfig);
```

### 7.3 Incremental Checkpointing

Standard checkpointing snapshots the entire state every interval — unacceptable for TB-scale state. Incremental checkpointing (RocksDB only) captures only the delta:

- RocksDB produces immutable SST files via compaction
- Each checkpoint uploads only new SST files since the previous checkpoint
- Recovery assembles the latest checkpoint from the base plus incremental files

```java
// Enable incremental checkpointing
env.setStateBackend(new EmbeddedRocksDBStateBackend(true)); // true = incremental

// Fine-tune RocksDB for large state
RocksDBOptionsFactory rocksDbOptions = new DefaultConfigurableOptionsFactory()
    .setMaxWriteBufferNumber(4)
    .setWriteBufferSize("128mb")
    .setMaxBytesForLevelBase("512mb");
```

### 7.4 Aligned vs Unaligned Checkpoints

**Aligned (default):**
- Operator waits for barriers from all input channels before checkpointing
- Provides exactly-once without including in-flight data in the snapshot
- Under back-pressure, barrier alignment can stall processing (barriers stuck behind buffered data)

**Unaligned (Flink 1.11+):**
- Operator checkpoints immediately upon receiving the first barrier
- In-flight data (buffers) from channels where barrier has not arrived are included in the snapshot
- Eliminates checkpoint delays under back-pressure
- Trade-off: larger checkpoint size (includes buffered network data)

```java
// Adaptive: start aligned, switch to unaligned if alignment takes too long
env.getCheckpointConfig().enableUnalignedCheckpoints();
env.getCheckpointConfig().setAlignedCheckpointTimeout(Duration.ofSeconds(30));
```

### 7.5 RocksDB Tuning

For production workloads with large state:

```java
// Custom RocksDB options
public class ProductionRocksDBOptions implements ConfigurableRocksDBOptionsFactory {
    @Override
    public DBOptions createDBOptions(DBOptions currentOptions, Collection<AutoCloseable> handles) {
        return currentOptions
            .setMaxBackgroundJobs(4)           // parallel compaction/flush threads
            .setMaxOpenFiles(-1)               // keep all files open (memory for handles)
            .setStatsDumpPeriodSec(60);        // metrics every 60s
    }

    @Override
    public ColumnFamilyOptions createColumnOptions(
            ColumnFamilyOptions currentOptions, Collection<AutoCloseable> handles) {
        // Block-based table with bloom filter for point lookups
        BlockBasedTableConfig tableConfig = new BlockBasedTableConfig()
            .setBlockSize(32 * 1024)          // 32KB blocks
            .setBlockCacheSize(256 * 1024 * 1024)  // 256MB block cache
            .setFilterPolicy(new BloomFilter(10, false))
            .setCacheIndexAndFilterBlocks(true);

        return currentOptions
            .setTableFormatConfig(tableConfig)
            .setWriteBufferSize(128 * 1024 * 1024)   // 128MB write buffer
            .setMaxWriteBufferNumber(4)
            .setMinWriteBufferNumberToMerge(2)
            .setCompactionStyle(CompactionStyle.LEVEL)
            .setLevelCompactionDynamicLevelBytes(true)
            .setTargetFileSizeBase(64 * 1024 * 1024); // 64MB SST files
    }
}
```

### 7.6 State Migration

When changing state schemas (adding fields, changing types), Flink supports state migration through:

1. **POJO and Avro state** — Flink automatically migrates compatible schema changes (new nullable fields, removed fields).
2. **TypeSerializerSnapshot** — custom serializers implement migration logic.
3. **State processor API** — read, modify, and write savepoint state offline.

```java
// State Processor API: offline state modification
ExecutionEnvironment batchEnv = ExecutionEnvironment.getExecutionEnvironment();
ExistingSavepoint savepoint = Savepoint.load(batchEnv, "s3://savepoints/sp-001",
    new EmbeddedRocksDBStateBackend());

// Read keyed state from a specific operator
DataSet<KeyedState> states = savepoint.readKeyedState(
    "fraud-detector-uid",
    new ReaderFunction()
);

// Transform state (e.g., migrate schema)
DataSet<KeyedState> migratedStates = states.map(new StateMigrator());

// Write back to a new savepoint
Savepoint.create(new EmbeddedRocksDBStateBackend(), 128)
    .withOperator("fraud-detector-uid", new WriterFunction(), migratedStates)
    .write("s3://savepoints/sp-002");

batchEnv.execute("State Migration");
```

### 7.7 Exactly-Once with External Systems

Achieving exactly-once guarantees across the streaming engine AND external sinks requires one of:

**Two-Phase Commit (2PC):**
1. Pre-commit: write to external system in a pending transaction
2. On checkpoint success: commit the transaction
3. On failure: abort the pending transaction

Flink's `TwoPhaseCommitSinkFunction` implements this protocol. The Kafka sink uses it to atomically commit output records only when a checkpoint completes.

```java
// Flink Kafka sink with exactly-once (uses Kafka transactions + 2PC)
KafkaSink<String> sink = KafkaSink.<String>builder()
    .setBootstrapServers("kafka:9092")
    .setRecordSerializer(KafkaRecordSerializationSchema.builder()
        .setTopic("output-topic")
        .setValueSerializationSchema(new SimpleStringSchema())
        .build())
    .setDeliveryGuarantee(DeliveryGuarantee.EXACTLY_ONCE)
    .setTransactionalIdPrefix("flink-job-tx")
    .setProperty(ProducerConfig.TRANSACTION_TIMEOUT_CONFIG, "900000") // > checkpoint interval
    .build();
```

**Idempotent Writes:**
- Write operations are naturally idempotent (e.g., upserts keyed by a deterministic ID)
- No transaction coordination needed
- The system may process duplicates, but the output converges to the same state

```java
// Idempotent write to Elasticsearch: document ID derived deterministically
stream.sinkTo(
    new Elasticsearch7SinkBuilder<Event>()
        .setHosts(new HttpHost("es-host", 9200, "http"))
        .setEmitter((event, context, indexer) -> {
            // Deterministic document ID = exactly-once via idempotency
            String docId = event.getKey() + "_" + event.getWindowEnd();
            indexer.add(new IndexRequest("events")
                .id(docId)
                .source(event.toJson(), XContentType.JSON));
        })
        .build()
);
```

---

## 8. Patterns and Anti-Patterns

### 8.1 Enrichment Patterns

**Async I/O** — for enriching stream events with external lookups without blocking:

```java
// Flink Async I/O: non-blocking external lookups
public class AsyncDatabaseLookup extends RichAsyncFunction<Transaction, EnrichedTransaction> {
    private transient AsyncHttpClient httpClient;

    @Override
    public void open(Configuration parameters) {
        httpClient = Dsl.asyncHttpClient();
    }

    @Override
    public void asyncInvoke(Transaction tx, ResultFuture<EnrichedTransaction> resultFuture) {
        CompletableFuture<Response> future = httpClient
            .prepareGet("http://user-service/api/users/" + tx.getUserId())
            .execute()
            .toCompletableFuture();

        future.thenAccept(response -> {
            UserProfile profile = parseResponse(response);
            resultFuture.complete(
                Collections.singleton(new EnrichedTransaction(tx, profile)));
        }).exceptionally(throwable -> {
            // Handle failure: use default or retry
            resultFuture.complete(
                Collections.singleton(new EnrichedTransaction(tx, UserProfile.UNKNOWN)));
            return null;
        });
    }

    @Override
    public void timeout(Transaction tx, ResultFuture<EnrichedTransaction> resultFuture) {
        resultFuture.complete(
            Collections.singleton(new EnrichedTransaction(tx, UserProfile.TIMEOUT)));
    }
}

// Apply with ordering guarantees and capacity limits
DataStream<EnrichedTransaction> enriched = AsyncDataStream.orderedWait(
    transactions,
    new AsyncDatabaseLookup(),
    30, TimeUnit.SECONDS,  // timeout per request
    100                     // max concurrent requests
);
```

**Broadcast State Pattern** — for enriching streams with slowly-changing rules or configuration:

```java
// Broadcast rules to all parallel instances
MapStateDescriptor<String, FraudRule> ruleStateDescriptor =
    new MapStateDescriptor<>("rules", String.class, FraudRule.class);

BroadcastStream<FraudRule> ruleBroadcast = rulesStream.broadcast(ruleStateDescriptor);

DataStream<Alert> alerts = transactions
    .connect(ruleBroadcast)
    .process(new BroadcastProcessFunction<Transaction, FraudRule, Alert>() {
        @Override
        public void processElement(Transaction tx, ReadOnlyContext ctx,
                Collector<Alert> out) throws Exception {
            // Read broadcast state (rules)
            ReadOnlyBroadcastState<String, FraudRule> rules =
                ctx.getBroadcastState(ruleStateDescriptor);

            for (Map.Entry<String, FraudRule> entry : rules.immutableEntries()) {
                if (entry.getValue().matches(tx)) {
                    out.collect(new Alert(tx, entry.getValue()));
                }
            }
        }

        @Override
        public void processBroadcastElement(FraudRule rule, Context ctx,
                Collector<Alert> out) throws Exception {
            // Update broadcast state
            ctx.getBroadcastState(ruleStateDescriptor).put(rule.getId(), rule);
        }
    });
```

### 8.2 Deduplication

```java
// Flink: deduplication with state TTL
public class DeduplicateFunction extends KeyedProcessFunction<String, Event, Event> {
    private ValueState<Boolean> seen;

    @Override
    public void open(Configuration parameters) {
        ValueStateDescriptor<Boolean> desc = new ValueStateDescriptor<>("seen", Boolean.class);
        StateTtlConfig ttl = StateTtlConfig.newBuilder(Time.hours(1))
            .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
            .build();
        desc.enableTimeToLive(ttl);
        seen = getRuntimeContext().getState(desc);
    }

    @Override
    public void processElement(Event event, Context ctx, Collector<Event> out) throws Exception {
        if (seen.value() == null) {
            seen.update(true);
            out.collect(event);
        }
        // Duplicate — drop silently
    }
}

// Apply: key by the deduplication key (e.g., event ID)
stream.keyBy(Event::getEventId)
    .process(new DeduplicateFunction());
```

### 8.3 Sessionization

Building user sessions from raw events:

```java
// Flink session window with custom processing
public class SessionBuilder extends ProcessWindowFunction<ClickEvent, UserSession,
        String, TimeWindow> {

    @Override
    public void process(String userId, Context context, Iterable<ClickEvent> events,
            Collector<UserSession> out) {
        List<ClickEvent> sorted = StreamSupport.stream(events.spliterator(), false)
            .sorted(Comparator.comparingLong(ClickEvent::getTimestamp))
            .collect(Collectors.toList());

        UserSession session = new UserSession();
        session.setUserId(userId);
        session.setSessionStart(context.window().getStart());
        session.setSessionEnd(context.window().getEnd());
        session.setDuration(context.window().getEnd() - context.window().getStart());
        session.setEventCount(sorted.size());
        session.setPages(sorted.stream().map(ClickEvent::getPage).collect(Collectors.toList()));

        // Classify session
        if (sorted.stream().anyMatch(e -> e.getPage().contains("/checkout"))) {
            session.setConversion(true);
        }

        out.collect(session);
    }
}

stream.keyBy(ClickEvent::getUserId)
    .window(EventTimeSessionWindows.withGap(Time.minutes(30)))
    .allowedLateness(Time.minutes(5))
    .process(new SessionBuilder());
```

### 8.4 Backpressure Handling

Backpressure occurs when downstream operators cannot keep up with upstream producers. Strategies:

1. **Buffering** — let the system buffer (Flink's network buffers, Kafka's consumer lag). Limited by memory.
2. **Dropping** — discard events when overwhelmed (acceptable for some metrics).
3. **Throttling** — slow down the source (Flink does this automatically via credit-based flow control).
4. **Scaling** — add parallelism to bottleneck operators.
5. **Shedding** — selectively drop low-priority events while preserving high-priority ones.

```java
// Load shedding: drop low-priority events under pressure
public class LoadSheddingFunction extends ProcessFunction<Event, Event> {
    private transient Gauge<Double> throughputGauge;

    @Override
    public void processElement(Event event, Context ctx, Collector<Event> out) {
        // Simple load shedding based on priority
        if (isUnderPressure() && event.getPriority() == Priority.LOW) {
            // Drop low priority events; increment dropped counter
            getRuntimeContext().getMetricGroup().counter("dropped-events").inc();
            return;
        }
        out.collect(event);
    }

    private boolean isUnderPressure() {
        // Check buffer utilization or custom metric
        return getRuntimeContext().getMetricGroup()
            .gauge("bufferUsage", () -> currentBufferUsage) > 0.8;
    }
}
```

### 8.5 Anti-Patterns

**Hot Keys** — a single key receiving disproportionate traffic. Solutions:
- Pre-aggregate before keying (local pre-combining)
- Salt the key and post-aggregate (split the hot key into N sub-keys, aggregate per sub-key, then combine)
- Use rebalance() before the hot operator

**Unbounded State** — state that grows without bound. Solutions:
- Always configure State TTL
- Use windowed aggregations instead of global state
- Monitor state size metrics

**Synchronous External Calls** — blocking the processing thread on HTTP/DB calls. Solutions:
- Use Async I/O (Flink)
- Use broadcast state for enrichment data
- Pre-load lookup data into local state stores

**Processing Time for Business Logic** — using processing time leads to non-reproducible results. Solution: always use event time for business-critical windows and aggregations.

**Fat Events** — carrying entire state in every event instead of using state management. Solution: store state in the operator and emit only deltas or results.

---

## 9. Monitoring and Operations

### 9.1 Key Metrics

| Metric | What It Means | Alert Threshold |
|---|---|---|
| **Throughput** (records/sec) | Processing rate | Depends on SLA; alert if < expected rate |
| **Latency** (ms) | Time from event creation to output | p99 > SLA threshold |
| **Consumer Lag** | Events waiting to be processed | Growing lag = falling behind |
| **Backpressure** | % time operator is blocked waiting | > 50% sustained |
| **Checkpoint Duration** | Time to complete a checkpoint | > checkpoint interval = overlap |
| **Checkpoint Size** | Bytes stored per checkpoint | Growing = possible state leak |
| **State Size** | Total managed state | Growing unboundedly = missing TTL |
| **Restart Count** | Job restarts due to failures | > 0 within an hour |
| **GC Pause Time** | JVM garbage collection | > 500ms = affects latency |

### 9.2 Flink Web UI

The Flink web UI provides:
- Job DAG visualization with per-operator metrics
- Backpressure indicators (idle/OK/low/high) per subtask
- Checkpoint history (size, duration, alignment)
- Exception history and root cause
- TaskManager resource utilization
- Watermark tracking per operator

### 9.3 Prometheus + Grafana Dashboards

```yaml
# Flink Prometheus reporter configuration (flink-conf.yaml)
metrics.reporters: prom
metrics.reporter.prom.factory.class: org.apache.flink.metrics.prometheus.PrometheusReporterFactory
metrics.reporter.prom.port: 9249
```

Key Prometheus queries for Grafana:

```promql
# Throughput
rate(flink_taskmanager_job_task_numRecordsInPerSecond[5m])

# Checkpoint duration
flink_jobmanager_job_lastCheckpointDuration / 1000  # convert to seconds

# Backpressure (fraction of time busy)
flink_taskmanager_job_task_busyTimeMsPerSecond / 1000

# Consumer lag (Kafka source)
flink_taskmanager_job_task_operator_KafkaSourceReader_KafkaConsumer_records_lag_max

# State size per operator
flink_taskmanager_job_task_operator_state_size

# Restart rate
increase(flink_jobmanager_job_numRestarts[1h])
```

**Sample Grafana dashboard layout:**
- Row 1: Throughput (in/out records per second), End-to-end Latency histogram
- Row 2: Checkpoint duration, Checkpoint size, Checkpoint alignment duration
- Row 3: Backpressure per operator, Buffer usage
- Row 4: State size growth, GC pause time, TaskManager memory
- Row 5: Kafka consumer lag, Watermark delay

### 9.4 Capacity Planning

**Throughput-based:**
```
Required parallelism = Peak throughput (records/s) / Per-instance throughput (records/s)
```

Measure per-instance throughput via load testing with representative data.

**State-based:**
```
Required memory = State size per key × Number of active keys × Overhead factor (1.5-2x for RocksDB)
Required disk = State size × Checkpoint multiplier (2-3x for concurrent checkpoints + compaction)
```

**Network-based:**
```
Inter-TaskManager bandwidth = Records/s × Avg record size × Shuffle factor
```

### 9.5 Scaling Strategies

**Reactive scaling** — scale based on real-time metrics:
- Flink Reactive Mode (Flink 1.13+): automatically adjusts parallelism when TaskManagers are added/removed
- Kubernetes HPA based on consumer lag or CPU

```yaml
# Kubernetes HPA for Flink TaskManagers based on consumer lag
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: flink-taskmanager-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: flink-taskmanager
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: External
      external:
        metric:
          name: kafka_consumer_lag
          selector:
            matchLabels:
              consumer_group: "flink-job"
        target:
          type: AverageValue
          averageValue: "10000"  # scale when lag exceeds 10k per replica
```

**Scheduled scaling** — pre-scale for known traffic patterns (e.g., scale up before business hours).

### 9.6 Troubleshooting Common Issues

**Back-Pressure:**
1. Identify the bottleneck operator via Web UI (first operator showing high backpressure from downstream)
2. Check if it is CPU-bound (slow UDF), I/O-bound (slow sink), or memory-bound (GC)
3. Solutions: increase parallelism, optimize UDF, batch sink writes, add async I/O

**Checkpoint Timeouts:**
1. Check if backpressure is blocking barrier propagation → enable unaligned checkpoints
2. Check state size → incremental checkpoints, state TTL
3. Check I/O throughput to checkpoint storage → faster storage, compression

**State Size Growth:**
1. Monitor `state_size` metric over time
2. Audit state descriptors — ensure all have TTL configured
3. Check for hot keys concentrating state on single operators
4. Consider if window allowed lateness is too generous

**Out-of-Memory:**
1. Check if state exceeds heap → switch to RocksDB backend
2. Check managed memory configuration → allocate more to RocksDB
3. Check for memory leaks in UDFs (cached objects, unclosed resources)
4. Check network buffer configuration

**Data Skew:**
1. Monitor per-subtask metrics — one subtask processing significantly more than others
2. Pre-aggregate before keyBy to reduce per-key volume
3. Salt hot keys: `keyBy(e -> e.getKey() + "_" + (e.hashCode() % 10))`
4. Use rebalance() for stateless operations before the skewed keyBy

---

## 10. Lab Exercises

### Lab 1: Real-Time Fraud Detection System (Flink + Kafka)

**Objective:** Build a streaming fraud detection pipeline that identifies suspicious transaction patterns in real time.

**Architecture:**
```
Kafka (transactions) → Flink → Kafka (alerts) → Alert Service
                         ↓
                    Kafka (enriched) → Data Lake
```

**Implementation:**

```java
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.api.common.state.*;
import org.apache.flink.streaming.api.functions.KeyedProcessFunction;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.util.Collector;

public class FraudDetectionJob {
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        env.enableCheckpointing(30_000);
        env.setStateBackend(new EmbeddedRocksDBStateBackend(true));
        env.getCheckpointConfig().setCheckpointStorage("s3://checkpoints/fraud-detection/");

        // Source: transactions from Kafka
        DataStream<Transaction> transactions = env.fromSource(
            buildKafkaSource("transactions"),
            WatermarkStrategy.<Transaction>forBoundedOutOfOrderness(Duration.ofSeconds(10))
                .withTimestampAssigner((tx, ts) -> tx.getTimestamp()),
            "transaction-source"
        );

        // Rule 1: Velocity check — more than 5 transactions in 1 minute
        DataStream<Alert> velocityAlerts = transactions
            .keyBy(Transaction::getCardNumber)
            .process(new VelocityFraudDetector());

        // Rule 2: Amount anomaly — single transaction > 3x average for this card
        DataStream<Alert> amountAlerts = transactions
            .keyBy(Transaction::getCardNumber)
            .process(new AmountAnomalyDetector());

        // Rule 3: Geographic impossibility — transactions from distant locations
        //         within impossible travel time
        DataStream<Alert> geoAlerts = transactions
            .keyBy(Transaction::getCardNumber)
            .process(new GeoImpossibilityDetector());

        // Merge all alerts
        DataStream<Alert> allAlerts = velocityAlerts
            .union(amountAlerts)
            .union(geoAlerts);

        // Deduplicate alerts (same card, same rule, within 5 minutes)
        DataStream<Alert> dedupedAlerts = allAlerts
            .keyBy(alert -> alert.getCardNumber() + "_" + alert.getRuleId())
            .process(new AlertDeduplicator());

        // Sink alerts to Kafka
        dedupedAlerts.sinkTo(buildKafkaSink("fraud-alerts"));

        env.execute("Fraud Detection Pipeline");
    }
}

// Velocity fraud detector: >5 transactions in 60 seconds
public class VelocityFraudDetector
        extends KeyedProcessFunction<String, Transaction, Alert> {

    private ListState<Long> transactionTimestamps;

    @Override
    public void open(Configuration parameters) {
        ListStateDescriptor<Long> desc = new ListStateDescriptor<>(
            "tx-timestamps", Long.class);
        StateTtlConfig ttl = StateTtlConfig.newBuilder(Time.minutes(5))
            .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
            .build();
        desc.enableTimeToLive(ttl);
        transactionTimestamps = getRuntimeContext().getListState(desc);
    }

    @Override
    public void processElement(Transaction tx, Context ctx, Collector<Alert> out)
            throws Exception {
        long now = tx.getTimestamp();
        long windowStart = now - 60_000; // 1-minute lookback

        // Add current timestamp
        transactionTimestamps.add(now);

        // Count transactions within the window
        int count = 0;
        List<Long> retained = new ArrayList<>();
        for (Long ts : transactionTimestamps.get()) {
            if (ts >= windowStart) {
                count++;
                retained.add(ts);
            }
        }

        // Update state (remove expired timestamps)
        transactionTimestamps.update(retained);

        if (count > 5) {
            out.collect(new Alert(
                tx.getCardNumber(),
                "VELOCITY",
                String.format("Card %s: %d transactions in last 60s (threshold: 5)",
                    tx.getCardNumber(), count),
                Severity.HIGH,
                tx.getTimestamp()
            ));
        }
    }
}

// Amount anomaly detector: transaction > 3x rolling average
public class AmountAnomalyDetector
        extends KeyedProcessFunction<String, Transaction, Alert> {

    private ValueState<Double> runningSum;
    private ValueState<Long> transactionCount;

    @Override
    public void open(Configuration parameters) {
        runningSum = getRuntimeContext().getState(
            new ValueStateDescriptor<>("running-sum", Double.class));
        transactionCount = getRuntimeContext().getState(
            new ValueStateDescriptor<>("tx-count", Long.class));
    }

    @Override
    public void processElement(Transaction tx, Context ctx, Collector<Alert> out)
            throws Exception {
        Double sum = runningSum.value();
        Long count = transactionCount.value();

        if (sum == null) { sum = 0.0; count = 0L; }

        double avg = count > 0 ? sum / count : tx.getAmount();

        // Check if current transaction is anomalous (after enough history)
        if (count >= 10 && tx.getAmount() > avg * 3.0) {
            out.collect(new Alert(
                tx.getCardNumber(),
                "AMOUNT_ANOMALY",
                String.format("Card %s: amount %.2f > 3x avg (%.2f)",
                    tx.getCardNumber(), tx.getAmount(), avg),
                Severity.MEDIUM,
                tx.getTimestamp()
            ));
        }

        // Update running statistics
        runningSum.update(sum + tx.getAmount());
        transactionCount.update(count + 1);
    }
}

// Geographic impossibility: speed > 900 km/h between consecutive transactions
public class GeoImpossibilityDetector
        extends KeyedProcessFunction<String, Transaction, Alert> {

    private ValueState<Transaction> lastTransaction;

    @Override
    public void open(Configuration parameters) {
        ValueStateDescriptor<Transaction> desc =
            new ValueStateDescriptor<>("last-tx", Transaction.class);
        StateTtlConfig ttl = StateTtlConfig.newBuilder(Time.hours(24))
            .setUpdateType(StateTtlConfig.UpdateType.OnCreateAndWrite)
            .build();
        desc.enableTimeToLive(ttl);
        lastTransaction = getRuntimeContext().getState(desc);
    }

    @Override
    public void processElement(Transaction tx, Context ctx, Collector<Alert> out)
            throws Exception {
        Transaction lastTx = lastTransaction.value();

        if (lastTx != null && tx.hasLocation() && lastTx.hasLocation()) {
            double distanceKm = haversineDistance(
                lastTx.getLatitude(), lastTx.getLongitude(),
                tx.getLatitude(), tx.getLongitude());

            double timeDiffHours = (tx.getTimestamp() - lastTx.getTimestamp()) / 3_600_000.0;

            if (timeDiffHours > 0) {
                double speedKmH = distanceKm / timeDiffHours;

                if (speedKmH > 900) { // faster than commercial flight
                    out.collect(new Alert(
                        tx.getCardNumber(),
                        "GEO_IMPOSSIBILITY",
                        String.format("Card %s: %.0f km in %.1f hours (%.0f km/h)",
                            tx.getCardNumber(), distanceKm, timeDiffHours, speedKmH),
                        Severity.CRITICAL,
                        tx.getTimestamp()
                    ));
                }
            }
        }

        lastTransaction.update(tx);
    }

    private double haversineDistance(double lat1, double lon1, double lat2, double lon2) {
        double R = 6371; // Earth radius in km
        double dLat = Math.toRadians(lat2 - lat1);
        double dLon = Math.toRadians(lon2 - lon1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }
}
```

### Lab 2: Sessionization with Late Data Handling

**Objective:** Build a user session aggregation pipeline that correctly handles late-arriving events.

```python
# PySpark Structured Streaming: sessionization with watermarks
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

spark = SparkSession.builder.appName("SessionizationLab").getOrCreate()

# Schema for clickstream events
click_schema = StructType([
    StructField("user_id", StringType()),
    StructField("page", StringType()),
    StructField("action", StringType()),
    StructField("event_time", TimestampType()),
    StructField("session_hint", StringType())  # optional session boundary marker
])

# Read clickstream from Kafka
clicks = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "clickstream") \
    .load() \
    .select(from_json(col("value").cast("string"), click_schema).alias("data")) \
    .select("data.*")

# Approach 1: Session windows using native Spark session_window (Spark 3.2+)
sessions = clicks \
    .withWatermark("event_time", "15 minutes") \
    .groupBy(
        session_window("event_time", "30 minutes"),  # 30-min gap = new session
        "user_id"
    ) \
    .agg(
        count("*").alias("event_count"),
        first("page").alias("landing_page"),
        last("page").alias("exit_page"),
        collect_list("page").alias("page_path"),
        min("event_time").alias("session_start"),
        max("event_time").alias("session_end"),
        (unix_timestamp(max("event_time")) - unix_timestamp(min("event_time"))).alias("duration_seconds"),
        sum(when(col("action") == "purchase", 1).otherwise(0)).alias("purchases")
    )

# Write sessions — append mode emits only after watermark passes the session end
query = sessions.writeStream \
    .outputMode("append") \
    .format("delta") \
    .option("path", "s3a://data-lake/user_sessions/") \
    .option("checkpointLocation", "s3a://checkpoints/sessions/") \
    .trigger(processingTime="1 minute") \
    .start()
```

**Flink version with explicit late data handling:**

```java
// Flink: sessionization with side outputs for late data
OutputTag<ClickEvent> lateClicks = new OutputTag<ClickEvent>("late-clicks") {};

SingleOutputStreamOperator<UserSession> sessions = clicks
    .keyBy(ClickEvent::getUserId)
    .window(EventTimeSessionWindows.withGap(Time.minutes(30)))
    .allowedLateness(Time.minutes(15))
    .sideOutputLateData(lateClicks)
    .process(new SessionWindowFunction());

// Main output: complete sessions
sessions.sinkTo(sessionSink);

// Late data: update existing sessions or create corrections
DataStream<ClickEvent> lateStream = sessions.getSideOutput(lateClicks);
lateStream.keyBy(ClickEvent::getUserId)
    .process(new LateDataCorrector()) // look up existing session and amend
    .sinkTo(correctionSink);
```

### Lab 3: Streaming ETL with Exactly-Once Guarantees

**Objective:** Build a CDC-based streaming ETL pipeline that maintains exactly-once semantics from source to sink.

```java
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.connector.kafka.source.KafkaSource;
import org.apache.flink.connector.kafka.sink.KafkaSink;
import com.ververica.cdc.connectors.mysql.source.MySqlSource;
import com.ververica.cdc.debezium.JsonDebeziumDeserializationSchema;

public class StreamingETLJob {
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // Exactly-once checkpointing
        env.enableCheckpointing(60_000);
        env.getCheckpointConfig().setCheckpointingMode(CheckpointingMode.EXACTLY_ONCE);
        env.getCheckpointConfig().setMinPauseBetweenCheckpoints(30_000);
        env.setStateBackend(new EmbeddedRocksDBStateBackend(true));
        env.getCheckpointConfig().setCheckpointStorage("s3://checkpoints/etl/");

        // Source: MySQL CDC (Debezium-based, exactly-once via binlog position tracking)
        MySqlSource<String> mySqlSource = MySqlSource.<String>builder()
            .hostname("mysql-host")
            .port(3306)
            .databaseList("ecommerce")
            .tableList("ecommerce.orders", "ecommerce.order_items", "ecommerce.products")
            .username("cdc_user")
            .password(System.getenv("MYSQL_CDC_PASSWORD"))
            .deserializer(new JsonDebeziumDeserializationSchema())
            .build();

        DataStream<String> cdcStream = env.fromSource(
            mySqlSource,
            WatermarkStrategy.noWatermarks(),
            "mysql-cdc-source"
        );

        // Parse CDC events and route by table
        DataStream<CDCEvent> parsedEvents = cdcStream
            .map(new CDCEventParser())
            .name("parse-cdc-events");

        // Split by table
        OutputTag<CDCEvent> orderItemsTag = new OutputTag<CDCEvent>("order-items") {};
        OutputTag<CDCEvent> productsTag = new OutputTag<CDCEvent>("products") {};

        SingleOutputStreamOperator<CDCEvent> orders = parsedEvents
            .process(new ProcessFunction<CDCEvent, CDCEvent>() {
                @Override
                public void processElement(CDCEvent event, Context ctx,
                        Collector<CDCEvent> out) {
                    switch (event.getTable()) {
                        case "orders": out.collect(event); break;
                        case "order_items": ctx.output(orderItemsTag, event); break;
                        case "products": ctx.output(productsTag, event); break;
                    }
                }
            });

        DataStream<CDCEvent> orderItems = orders.getSideOutput(orderItemsTag);
        DataStream<CDCEvent> products = orders.getSideOutput(productsTag);

        // Enrich orders with product data via broadcast state
        MapStateDescriptor<String, Product> productState =
            new MapStateDescriptor<>("products", String.class, Product.class);

        BroadcastStream<CDCEvent> productBroadcast = products.broadcast(productState);

        DataStream<EnrichedOrder> enriched = orderItems
            .connect(productBroadcast)
            .process(new OrderEnrichmentFunction(productState));

        // Sink with exactly-once to Kafka (transactional producer)
        KafkaSink<EnrichedOrder> kafkaSink = KafkaSink.<EnrichedOrder>builder()
            .setBootstrapServers("kafka:9092")
            .setRecordSerializer(KafkaRecordSerializationSchema.builder()
                .setTopic("enriched-orders")
                .setValueSerializationSchema(new EnrichedOrderSerializer())
                .build())
            .setDeliveryGuarantee(DeliveryGuarantee.EXACTLY_ONCE)
            .setTransactionalIdPrefix("etl-job-tx")
            .setProperty(ProducerConfig.TRANSACTION_TIMEOUT_CONFIG, "600000")
            .build();

        enriched.sinkTo(kafkaSink);

        // Also sink to Iceberg (exactly-once via Flink-Iceberg connector)
        // Iceberg commits align with Flink checkpoints
        FlinkSink.forRow(enriched.map(EnrichedOrder::toRow, rowTypeInfo), tableSchema)
            .table(icebergTable)
            .tableLoader(TableLoader.fromHadoopTable("s3://warehouse/enriched_orders"))
            .distributionMode(DistributionMode.HASH)
            .writeParallelism(4)
            .build();

        env.execute("Streaming ETL with Exactly-Once");
    }
}
```

### Lab 4: Performance Benchmark — Flink vs Spark Structured Streaming

**Objective:** Benchmark both engines on identical workloads measuring throughput, latency, and resource consumption.

**Test Harness:**

```python
#!/usr/bin/env python3
"""
Benchmark harness for stream processing engines.
Generates load, measures end-to-end latency, throughput, and resource usage.
"""

import json
import time
import uuid
import statistics
from dataclasses import dataclass, field
from typing import List
from confluent_kafka import Producer, Consumer, TopicPartition
from concurrent.futures import ThreadPoolExecutor
import threading

@dataclass
class BenchmarkConfig:
    input_topic: str = "benchmark-input"
    output_topic: str = "benchmark-output"
    kafka_bootstrap: str = "kafka:9092"
    num_events: int = 1_000_000
    producer_threads: int = 4
    event_size_bytes: int = 512
    warmup_events: int = 50_000

@dataclass
class BenchmarkResult:
    engine: str
    throughput_events_per_sec: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    total_time_seconds: float
    events_processed: int
    cpu_utilization_percent: float = 0.0
    memory_peak_mb: float = 0.0
    checkpoint_avg_ms: float = 0.0

class StreamBenchmark:
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.latencies: List[float] = []
        self.produce_timestamps: dict = {}  # event_id -> produce_time_ns

    def produce_events(self):
        """Generate benchmark events with embedded timestamps."""
        producer = Producer({'bootstrap.servers': self.config.kafka_bootstrap,
                           'linger.ms': 5, 'batch.size': 65536})

        events_per_thread = self.config.num_events // self.config.producer_threads

        def produce_batch(thread_id: int):
            for i in range(events_per_thread):
                event_id = f"{thread_id}_{i}_{uuid.uuid4().hex[:8]}"
                event = {
                    "event_id": event_id,
                    "user_id": f"user_{i % 10000}",
                    "amount": round(50 + (i % 500) * 0.5, 2),
                    "timestamp": int(time.time() * 1000),
                    "produce_time_ns": time.time_ns(),
                    "padding": "x" * (self.config.event_size_bytes - 200)
                }
                producer.produce(
                    self.config.input_topic,
                    key=event["user_id"].encode(),
                    value=json.dumps(event).encode()
                )
                if i % 10000 == 0:
                    producer.flush()
            producer.flush()

        with ThreadPoolExecutor(max_workers=self.config.producer_threads) as executor:
            futures = [executor.submit(produce_batch, tid)
                      for tid in range(self.config.producer_threads)]
            for f in futures:
                f.result()

    def consume_and_measure(self, timeout_seconds: int = 300) -> BenchmarkResult:
        """Consume output events and calculate latency statistics."""
        consumer = Consumer({
            'bootstrap.servers': self.config.kafka_bootstrap,
            'group.id': f'benchmark-consumer-{uuid.uuid4().hex[:8]}',
            'auto.offset.reset': 'latest',
            'enable.auto.commit': True
        })
        consumer.subscribe([self.config.output_topic])

        latencies = []
        start_time = time.time()
        events_consumed = 0
        warmup_complete = False

        while time.time() - start_time < timeout_seconds:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                continue

            event = json.loads(msg.value().decode())
            events_consumed += 1

            # Skip warmup period
            if not warmup_complete:
                if events_consumed >= self.config.warmup_events:
                    warmup_complete = True
                    latencies.clear()
                    start_time = time.time()
                    events_consumed = 0
                continue

            # Measure end-to-end latency
            if "produce_time_ns" in event:
                latency_ms = (time.time_ns() - event["produce_time_ns"]) / 1_000_000
                latencies.append(latency_ms)

            if events_consumed >= self.config.num_events - self.config.warmup_events:
                break

        consumer.close()
        total_time = time.time() - start_time

        if not latencies:
            raise RuntimeError("No latency measurements collected")

        latencies.sort()
        return BenchmarkResult(
            engine="",  # filled by caller
            throughput_events_per_sec=events_consumed / total_time,
            p50_latency_ms=latencies[int(len(latencies) * 0.50)],
            p95_latency_ms=latencies[int(len(latencies) * 0.95)],
            p99_latency_ms=latencies[int(len(latencies) * 0.99)],
            max_latency_ms=latencies[-1],
            total_time_seconds=total_time,
            events_processed=events_consumed
        )

    def run_benchmark(self, engine_name: str) -> BenchmarkResult:
        """Full benchmark cycle: produce → wait for processing → consume."""
        print(f"[{engine_name}] Producing {self.config.num_events} events...")
        self.produce_events()

        print(f"[{engine_name}] Consuming output and measuring latency...")
        result = self.consume_and_measure()
        result.engine = engine_name

        print(f"\n{'='*60}")
        print(f"RESULTS: {engine_name}")
        print(f"{'='*60}")
        print(f"  Throughput:    {result.throughput_events_per_sec:,.0f} events/sec")
        print(f"  p50 Latency:   {result.p50_latency_ms:.1f} ms")
        print(f"  p95 Latency:   {result.p95_latency_ms:.1f} ms")
        print(f"  p99 Latency:   {result.p99_latency_ms:.1f} ms")
        print(f"  Max Latency:   {result.max_latency_ms:.1f} ms")
        print(f"  Total Time:    {result.total_time_seconds:.1f} s")
        print(f"{'='*60}\n")

        return result


def compare_engines():
    """Run benchmarks for both engines and produce comparison."""
    config = BenchmarkConfig(num_events=2_000_000)
    benchmark = StreamBenchmark(config)

    # Assumes both Flink and Spark jobs are already running
    # processing from 'benchmark-input' to 'benchmark-output'

    # Run Flink benchmark
    config.output_topic = "flink-benchmark-output"
    flink_result = benchmark.run_benchmark("Apache Flink")

    # Run Spark benchmark
    config.output_topic = "spark-benchmark-output"
    spark_result = benchmark.run_benchmark("Spark Structured Streaming")

    # Comparison table
    print("\n" + "=" * 80)
    print(f"{'METRIC':<30} {'FLINK':<25} {'SPARK SS':<25}")
    print("=" * 80)
    metrics = [
        ("Throughput (events/s)", f"{flink_result.throughput_events_per_sec:,.0f}",
         f"{spark_result.throughput_events_per_sec:,.0f}"),
        ("p50 Latency (ms)", f"{flink_result.p50_latency_ms:.1f}",
         f"{spark_result.p50_latency_ms:.1f}"),
        ("p95 Latency (ms)", f"{flink_result.p95_latency_ms:.1f}",
         f"{spark_result.p95_latency_ms:.1f}"),
        ("p99 Latency (ms)", f"{flink_result.p99_latency_ms:.1f}",
         f"{spark_result.p99_latency_ms:.1f}"),
    ]
    for name, flink_val, spark_val in metrics:
        print(f"  {name:<28} {flink_val:<25} {spark_val:<25}")
    print("=" * 80)


if __name__ == "__main__":
    compare_engines()
```

**Expected results summary (based on published benchmarks and production experience):**

| Metric | Flink | Spark Structured Streaming |
|---|---|---|
| Throughput (simple agg) | 1-5M events/s per node | 500K-2M events/s per node |
| p50 Latency | 5-50ms | 100ms-2s (micro-batch interval) |
| p99 Latency | 50-200ms | 1-5s |
| State access | Sub-ms (local RocksDB) | Per-batch (checkpoint overhead) |
| Checkpoint overhead | Low (async, incremental) | Per-batch (write-ahead log) |
| Recovery time | Seconds (from last checkpoint) | Seconds-minutes |
| Best for | Low-latency, complex state, CEP | SQL-heavy, batch+stream unification |

**Key takeaways:**
- Flink wins on latency and stateful processing efficiency
- Spark wins on ecosystem integration (same code for batch and stream) and SQL-heavy workloads
- Flink's true streaming model handles event-time processing more naturally
- Spark's micro-batch provides simpler exactly-once semantics at the cost of latency floor
- For latency-critical applications (fraud detection, real-time bidding): choose Flink
- For analytics-heavy streaming with existing Spark infrastructure: choose Structured Streaming

---

## Summary

Stream processing systems enable organizations to react to data in real time — detecting fraud in milliseconds, computing live dashboards, and maintaining eventually-consistent materialized views. The choice between Flink, Kafka Streams, Spark Structured Streaming, and cloud-managed services depends on:

1. **Latency requirements** — sub-second demands Flink or Kafka Streams; seconds-level is fine for Spark SS
2. **State complexity** — complex stateful logic favors Flink's rich state primitives
3. **Operational model** — Kafka Streams as a library requires no cluster; Flink and Spark need orchestration
4. **Existing infrastructure** — organizations deep in Kafka benefit from Kafka Streams; those with Spark benefit from Structured Streaming
5. **Team expertise** — SQL-savvy teams can leverage Flink SQL or Spark SQL; Kafka Streams requires JVM expertise
6. **Cloud strategy** — fully managed options (Kinesis, Dataflow, Stream Analytics) reduce operational burden at the cost of vendor lock-in

Regardless of engine choice, the fundamentals remain constant: understand time semantics, design for fault tolerance, manage state deliberately, and monitor relentlessly.
