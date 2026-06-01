# Apache Kafka — Distributed Event Streaming Platform

## Table of Contents

1. [Kafka Architecture](#1-kafka-architecture)
2. [Producers](#2-producers)
3. [Consumers](#3-consumers)
4. [Kafka Streams](#4-kafka-streams)
5. [Kafka Connect](#5-kafka-connect)
6. [Schema Management](#6-schema-management)
7. [Performance Tuning](#7-performance-tuning)
8. [Security](#8-security)
9. [Operations](#9-operations)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Kafka Architecture

### 1.1 Broker Fundamentals

A Kafka broker is a single server process that receives messages from producers, assigns offsets within partitions, persists messages to disk, and serves consumer fetch requests. A Kafka cluster consists of multiple brokers coordinating to provide fault tolerance and horizontal scalability.

Each broker is identified by a unique integer `broker.id`. Brokers are stateless with respect to consumers—offset tracking is handled by a special internal topic (`__consumer_offsets`). The broker's primary responsibilities:

- Accept produce requests and write records to partition log segments
- Serve fetch requests from consumers and follower replicas
- Participate in cluster metadata propagation
- Handle partition leadership and replication

**Key broker configurations:**

```properties
broker.id=1
listeners=PLAINTEXT://0.0.0.0:9092
log.dirs=/var/kafka-logs
num.partitions=6
default.replication.factor=3
min.insync.replicas=2
log.retention.hours=168
log.segment.bytes=1073741824
```

### 1.2 ZooKeeper vs KRaft (KIP-500)

#### ZooKeeper Mode (Legacy)

Historically, Kafka relied on Apache ZooKeeper for:

- Controller election
- Broker registration and liveness
- Topic/partition metadata storage
- ACL storage
- Dynamic configuration management

ZooKeeper introduces operational complexity: a separate 3- or 5-node ensemble must be deployed, monitored, and secured independently. The dual-system architecture creates split-brain risks during network partitions and adds latency to metadata operations.

#### KRaft Mode (KIP-500)

KRaft (Kafka Raft) eliminates ZooKeeper by embedding a Raft-based consensus protocol directly into Kafka brokers. Introduced in KIP-500 and production-ready since Kafka 3.3, KRaft collapses the control plane into the Kafka process itself.

**KRaft architecture:**

- A subset of brokers are designated as **controllers** (typically 3 or 5)
- Controllers form a Raft quorum managing the metadata log (`__cluster_metadata`)
- One controller is the **active controller**; others are hot standbys
- Regular brokers are **data brokers** that fetch metadata from the controller quorum

```properties
# KRaft controller configuration
process.roles=controller
node.id=1
controller.quorum.voters=1@controller1:9093,2@controller2:9093,3@controller3:9093
controller.listener.names=CONTROLLER
listeners=CONTROLLER://0.0.0.0:9093
```

```properties
# KRaft broker configuration
process.roles=broker
node.id=101
controller.quorum.voters=1@controller1:9093,2@controller2:9093,3@controller3:9093
listeners=PLAINTEXT://0.0.0.0:9092
```

**Combined mode** (process.roles=broker,controller) is suitable for development but production clusters should separate roles for isolation.

**KRaft advantages over ZooKeeper:**

| Aspect | ZooKeeper | KRaft |
|--------|-----------|-------|
| Deployment | Separate ensemble | Integrated controllers |
| Metadata propagation | Async push from ZK watches | Metadata log replication |
| Controller failover | ~30s typical | ~5s typical |
| Partition limit | ~200K practical ceiling | Millions (tested) |
| Operational complexity | High (two systems) | Lower (single system) |

### 1.3 Topics, Partitions, and Segments

**Topics** are logical categories for messages. Each topic is divided into one or more **partitions**, which are the fundamental unit of parallelism and ordering.

**Partitions** are append-only, immutable, ordered sequences of records. Each record within a partition gets a monotonically increasing offset. Ordering guarantees exist only within a single partition—there is no global ordering across partitions of a topic.

**Segments** are the on-disk representation of partition data. A partition consists of multiple segment files:

```
/var/kafka-logs/orders-0/
├── 00000000000000000000.log      # Active segment
├── 00000000000000000000.index    # Offset index
├── 00000000000000000000.timeindex # Timestamp index
├── 00000000000000524288.log      # Rolled segment
├── 00000000000000524288.index
├── 00000000000000524288.timeindex
└── leader-epoch-checkpoint
```

Segment rolling occurs when:
- `log.segment.bytes` is reached (default 1 GB)
- `log.roll.ms` / `log.roll.hours` elapses
- The index file is full (`log.index.size.max.bytes`)

### 1.4 Replication

Kafka replicates each partition across multiple brokers for fault tolerance. The replication unit is the partition.

**Key concepts:**

- **Replication factor**: Number of copies of each partition (set per topic)
- **Leader replica**: Handles all produce and consume requests for a partition
- **Follower replicas**: Passively replicate from the leader
- **ISR (In-Sync Replicas)**: The set of replicas that are caught up to the leader within `replica.lag.time.max.ms` (default 30s)

**Leader election:**

When a leader fails, the controller selects a new leader from the ISR. If `unclean.leader.election.enable=true` (default false since 2.0), an out-of-sync replica can become leader, risking data loss.

**min.insync.replicas:**

This broker/topic-level config defines the minimum ISR size required for a produce request with `acks=all` to succeed. With `replication.factor=3` and `min.insync.replicas=2`, the system tolerates one broker failure without blocking writes.

```
Replication Factor = 3
min.insync.replicas = 2
acks = all

Broker 1 (Leader) ← Producer writes here
Broker 2 (ISR)    ← Replicates from leader
Broker 3 (ISR)    ← Replicates from leader

If Broker 3 fails → ISR = {1, 2} → writes still succeed (ISR size >= min.insync.replicas)
If Broker 2 also fails → ISR = {1} → writes REJECTED (ISR size < min.insync.replicas)
```

### 1.5 Log Compaction

Log compaction is an alternative retention policy (`cleanup.policy=compact`) that retains at least the last known value for each message key within a partition. Instead of deleting old segments by time or size, the log cleaner thread identifies duplicate keys and removes older records, keeping only the most recent value per key.

**Use cases:**
- Changelog streams (database state replication)
- KTable backing topics in Kafka Streams
- Configuration distribution

**Tombstones:** A record with a null value signals deletion. The compactor retains tombstones for `delete.retention.ms` (default 24h) before removing them.

**Compaction guarantees:**
- Consumers starting from offset 0 will see at least the final state
- Records in the "dirty" (uncompacted) portion are never removed
- The active segment is never compacted

### 1.6 Consumer Groups

Consumer groups enable parallel consumption. Each partition is assigned to exactly one consumer within a group. Multiple groups can independently consume the same topic.

**Group coordinator:** One broker acts as the coordinator for each consumer group (determined by hashing the group.id). The coordinator manages:
- Group membership (join/leave/heartbeat)
- Partition assignment
- Offset commits

### 1.7 Partition Assignment Strategies

When consumers join or leave a group, partition reassignment occurs via the configured assignor:

| Strategy | Behavior |
|----------|----------|
| Range | Assigns partitions per topic in ranges to consumers (can create imbalance with many topics) |
| RoundRobin | Distributes all partitions across consumers in round-robin |
| Sticky | Like RoundRobin but minimizes partition movement during rebalances |
| CooperativeSticky | Sticky assignment with incremental (cooperative) rebalancing |

### 1.8 Controller Architecture

The controller is the broker responsible for managing partition state transitions (leader election, ISR updates) and propagating metadata to other brokers.

**In ZooKeeper mode:** One broker wins the controller election via ZooKeeper ephemeral nodes. It watches ZK for broker failures and topic changes, then issues `LeaderAndIsr` and `UpdateMetadata` requests to affected brokers.

**In KRaft mode:** The active controller maintains the authoritative metadata log. All state changes are committed as records to this log. Other controllers replicate the log via Raft consensus. Brokers fetch metadata updates from the controller quorum.

---

## 2. Producers

### 2.1 Partitioning Strategies

The producer determines which partition receives each record:

**Default partitioner (Kafka 2.4+):**
- If a key is present: `murmur2(key) % numPartitions` (deterministic, same key → same partition)
- If key is null: Sticky partitioning — batches records to the same partition until `batch.size` or `linger.ms` triggers a send, then selects a new partition

**Custom partitioner:**

```java
public class GeoPartitioner implements Partitioner {
    @Override
    public int partition(String topic, Object key, byte[] keyBytes,
                         Object value, byte[] valueBytes, Cluster cluster) {
        List<PartitionInfo> partitions = cluster.partitionsForTopic(topic);
        int numPartitions = partitions.size();
        
        if (key == null) {
            return ThreadLocalRandom.current().nextInt(numPartitions);
        }
        
        String region = extractRegion((String) key);
        return switch (region) {
            case "EU" -> Math.abs(key.hashCode()) % (numPartitions / 3);
            case "US" -> (numPartitions / 3) + Math.abs(key.hashCode()) % (numPartitions / 3);
            default -> (2 * numPartitions / 3) + Math.abs(key.hashCode()) % (numPartitions / 3);
        };
    }
}
```

**Python (confluent-kafka):**

```python
from confluent_kafka import Producer

def geo_partitioner(key, all_partitions, available_partitions):
    """Custom partitioner routing by geographic region prefix."""
    if key is None:
        return random.choice(available_partitions)
    
    region = key.decode("utf-8").split("-")[0]
    partition_count = len(all_partitions)
    
    region_offsets = {"EU": 0, "US": partition_count // 3, "APAC": 2 * partition_count // 3}
    base = region_offsets.get(region, 0)
    bucket_size = partition_count // 3
    
    return base + (hash(key) % bucket_size)

producer = Producer({
    "bootstrap.servers": "kafka1:9092,kafka2:9092,kafka3:9092",
    "partitioner": geo_partitioner,  # Note: confluent-kafka doesn't directly support this
})
```

Note: confluent-kafka's Python client uses the built-in librdkafka partitioner. For true custom partitioning in Python, explicitly set the partition in the `produce()` call:

```python
from confluent_kafka import Producer
import hashlib

producer = Producer({"bootstrap.servers": "kafka1:9092,kafka2:9092,kafka3:9092"})

def compute_partition(key: bytes, num_partitions: int) -> int:
    h = int(hashlib.md5(key).hexdigest(), 16)
    return h % num_partitions

topic = "orders"
key = b"user-12345"
partition = compute_partition(key, num_partitions=12)

producer.produce(topic, key=key, value=b'{"order_id": 999}', partition=partition)
producer.flush()
```

### 2.2 Acknowledgment Configuration (acks)

| acks | Behavior | Durability | Latency |
|------|----------|------------|---------|
| 0 | Fire and forget — no broker acknowledgment | Data loss possible on any failure | Lowest |
| 1 | Leader acknowledges write to its local log | Data loss if leader fails before replication | Medium |
| all (-1) | All ISR replicas acknowledge | No data loss if `min.insync.replicas` > 1 | Highest |

```java
Properties props = new Properties();
props.put(ProducerConfig.ACKS_CONFIG, "all");
props.put(ProducerConfig.RETRIES_CONFIG, Integer.MAX_VALUE);
props.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 5);
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
```

### 2.3 Idempotent Producers

Idempotent producers guarantee exactly-once delivery per partition within a single producer session. The broker deduplicates records using a producer ID (PID) and sequence number.

**Enabling:**
```properties
enable.idempotence=true
acks=all                              # Required
max.in.flight.requests.per.connection=5   # Max allowed with idempotence
retries=2147483647                    # Recommended
```

Under the hood, the broker maintains a map of `(PID, partition) → last 5 sequence numbers`. Duplicate sends (from retries) are silently discarded.

### 2.4 Transactional Producers (Exactly-Once Semantics)

Transactions enable atomic writes across multiple partitions and topics. Combined with `read_committed` consumers, this provides end-to-end exactly-once semantics (EOS).

```java
Properties props = new Properties();
props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka1:9092");
props.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "order-processor-1");
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
props.put(ProducerConfig.ACKS_CONFIG, "all");

KafkaProducer<String, String> producer = new KafkaProducer<>(props);
producer.initTransactions();

try {
    producer.beginTransaction();
    
    producer.send(new ProducerRecord<>("orders", orderId, orderJson));
    producer.send(new ProducerRecord<>("inventory-updates", sku, inventoryJson));
    producer.send(new ProducerRecord<>("notifications", userId, notificationJson));
    
    // Commit offsets within the transaction (consume-transform-produce)
    producer.sendOffsetsToTransaction(offsetsToCommit, consumerGroupMetadata);
    
    producer.commitTransaction();
} catch (ProducerFencedException | OutOfOrderSequenceException e) {
    producer.close();
} catch (KafkaException e) {
    producer.abortTransaction();
}
```

**Transaction coordinator:** A broker designated by hashing the `transactional.id` manages the transaction state machine. Transaction state is stored in `__transaction_state`.

### 2.5 Batching

Producers accumulate records into batches per partition before sending:

```properties
# Batch size in bytes — larger batches improve throughput at the cost of latency
batch.size=65536

# Time to wait for additional records before sending an incomplete batch
linger.ms=20

# Maximum memory for all buffered unsent records
buffer.memory=67108864
```

**Tuning trade-off:**
- High `linger.ms` + large `batch.size` → higher throughput, higher latency
- Low `linger.ms` + small `batch.size` → lower latency, lower throughput

### 2.6 Compression

Producers can compress record batches before transmission. Compression is per-batch and is stored as-is by the broker (broker decompresses only for validation or offset assignment in older formats).

| Codec | CPU | Compression Ratio | Best For |
|-------|-----|-------------------|----------|
| none | 0 | 1:1 | Low-latency, small messages |
| snappy | Low | ~2:1 | General purpose, low CPU overhead |
| lz4 | Low | ~2.5:1 | High throughput, good balance |
| zstd | Medium | ~3.5:1 | Best ratio, acceptable CPU for batch workloads |
| gzip | High | ~3:1 | Legacy, avoid for new deployments |

```properties
compression.type=zstd
```

**Python:**

```python
producer = Producer({
    "bootstrap.servers": "kafka1:9092",
    "compression.type": "zstd",
    "compression.level": 3,  # zstd levels 1-22
    "batch.size": 65536,
    "linger.ms": 20,
})
```

### 2.7 Interceptors

Interceptors allow injecting cross-cutting logic (metrics, tracing, header injection) without modifying application code.

```java
public class TracingProducerInterceptor implements ProducerInterceptor<String, String> {
    
    @Override
    public ProducerRecord<String, String> onSend(ProducerRecord<String, String> record) {
        record.headers().add("trace-id", TraceContext.current().traceId().getBytes());
        record.headers().add("timestamp", Long.toString(System.currentTimeMillis()).getBytes());
        return record;
    }
    
    @Override
    public void onAcknowledgement(RecordMetadata metadata, Exception exception) {
        if (exception != null) {
            Metrics.counter("kafka.producer.errors").increment();
        } else {
            Metrics.counter("kafka.producer.success").increment();
            Metrics.histogram("kafka.producer.latency")
                .record(System.currentTimeMillis() - metadata.timestamp());
        }
    }
    
    @Override
    public void close() {}
    
    @Override
    public void configure(Map<String, ?> configs) {}
}
```

Configuration:
```properties
interceptor.classes=com.example.TracingProducerInterceptor
```

---

## 3. Consumers

### 3.1 Consumer Group Protocol

The consumer group protocol coordinates partition assignment among group members:

1. **FindCoordinator**: Consumer discovers which broker is the group coordinator
2. **JoinGroup**: Consumer sends a join request with its subscription and supported assignors
3. **SyncGroup**: The designated leader computes the assignment and sends it via the coordinator to all members
4. **Heartbeat**: Consumers periodically send heartbeats; missed heartbeats trigger rebalance
5. **LeaveGroup**: Graceful shutdown notifies the coordinator

```java
Properties props = new Properties();
props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka1:9092");
props.put(ConsumerConfig.GROUP_ID_CONFIG, "order-processor");
props.put(ConsumerConfig.GROUP_INSTANCE_ID_CONFIG, "order-processor-pod-3"); // Static membership
props.put(ConsumerConfig.SESSION_TIMEOUT_MS_CONFIG, 45000);
props.put(ConsumerConfig.HEARTBEAT_INTERVAL_MS_CONFIG, 15000);
props.put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, 300000);
props.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
```

### 3.2 Rebalancing Strategies

#### Eager Rebalancing (Stop-the-World)

All consumers revoke all partitions, then receive new assignments. During rebalance, no consumption occurs (brief processing gap).

#### Cooperative (Incremental) Rebalancing

Only partitions that need to move are revoked. Consumers continue processing unaffected partitions during rebalance.

```java
props.put(ConsumerConfig.PARTITION_ASSIGNMENT_STRATEGY_CONFIG,
    "org.apache.kafka.clients.consumer.CooperativeStickyAssignor");
```

#### Static Group Membership

Assigning `group.instance.id` prevents rebalances during transient disconnections. The consumer retains its assignment for `session.timeout.ms` even if it disconnects.

```python
from confluent_kafka import Consumer

consumer = Consumer({
    "bootstrap.servers": "kafka1:9092",
    "group.id": "order-processor",
    "group.instance.id": "pod-3",  # Static membership
    "partition.assignment.strategy": "cooperative-sticky",
    "session.timeout.ms": 45000,
    "auto.offset.reset": "earliest",
})

consumer.subscribe(["orders", "payments"])
```

### 3.3 Offset Management

#### Auto Commit

```properties
enable.auto.commit=true
auto.commit.interval.ms=5000
```

Risk: Records processed between the last auto-commit and a crash are reprocessed (at-least-once semantics at best).

#### Manual Commit (Synchronous)

```java
while (running) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    
    for (ConsumerRecord<String, String> record : records) {
        processRecord(record);
    }
    
    // Commit after successful processing
    consumer.commitSync();
}
```

#### Manual Commit (Asynchronous with Callback)

```java
consumer.commitAsync((offsets, exception) -> {
    if (exception != null) {
        log.error("Commit failed for offsets: {}", offsets, exception);
    }
});
```

#### Fine-Grained Offset Control

```java
Map<TopicPartition, OffsetAndMetadata> currentOffsets = new HashMap<>();

for (ConsumerRecord<String, String> record : records) {
    processRecord(record);
    currentOffsets.put(
        new TopicPartition(record.topic(), record.partition()),
        new OffsetAndMetadata(record.offset() + 1, "processed")
    );
    
    if (recordCount % 1000 == 0) {
        consumer.commitAsync(currentOffsets, null);
    }
}
```

**Python manual commit:**

```python
from confluent_kafka import Consumer, TopicPartition

consumer = Consumer({
    "bootstrap.servers": "kafka1:9092",
    "group.id": "etl-pipeline",
    "enable.auto.commit": False,
    "auto.offset.reset": "earliest",
})

consumer.subscribe(["raw-events"])

try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            handle_error(msg.error())
            continue
        
        process_message(msg)
        
        # Commit specific offset
        consumer.commit(offsets=[
            TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1)
        ], asynchronous=False)
finally:
    consumer.close()
```

### 3.4 Exactly-Once Consumption (read_committed)

When consuming from transactional producers, setting `isolation.level=read_committed` ensures consumers only see committed transaction records:

```properties
isolation.level=read_committed
```

Non-committed (in-progress or aborted) transaction records are filtered. The consumer sees a consistent view—all records from a transaction or none.

### 3.5 Consumer Lag Monitoring

Consumer lag = latest partition offset - consumer committed offset. High lag indicates consumers cannot keep pace with producers.

**Monitoring approaches:**

```bash
# CLI tool
kafka-consumer-groups.sh --bootstrap-server kafka1:9092 \
    --group order-processor --describe
```

**Programmatic lag calculation:**

```java
Map<TopicPartition, Long> endOffsets = consumer.endOffsets(consumer.assignment());
Map<TopicPartition, OffsetAndMetadata> committed = consumer.committed(consumer.assignment());

for (TopicPartition tp : consumer.assignment()) {
    long lag = endOffsets.get(tp) - committed.get(tp).offset();
    metrics.gauge("consumer.lag", lag, "partition", String.valueOf(tp.partition()));
}
```

**Burrow:** LinkedIn's open-source consumer lag evaluation tool that assesses lag trend (OK, WARNING, ERROR) rather than absolute values.

### 3.6 Poll Loop Patterns

#### Basic Poll Loop

```java
try {
    consumer.subscribe(List.of("events"));
    
    while (!shutdown.get()) {
        ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
        
        if (records.isEmpty()) continue;
        
        for (ConsumerRecord<String, String> record : records) {
            processRecord(record);
        }
        
        consumer.commitSync();
    }
} finally {
    consumer.close();
}
```

#### Pause/Resume for Backpressure

```java
while (!shutdown.get()) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    
    for (TopicPartition partition : records.partitions()) {
        List<ConsumerRecord<String, String>> partitionRecords = records.records(partition);
        
        if (processingQueue.size() > MAX_QUEUE_SIZE) {
            consumer.pause(Set.of(partition));
            scheduleResume(partition, Duration.ofSeconds(5));
        } else {
            partitionRecords.forEach(processingQueue::add);
        }
    }
}
```

---

## 4. Kafka Streams

### 4.1 Stream/Table Duality

Kafka Streams builds on the fundamental insight that streams and tables are two sides of the same coin:

- A **stream** is a changelog: an unbounded sequence of facts (inserts)
- A **table** is a materialized view: the latest value per key (upserts)
- Any stream can be folded into a table (by replaying and keeping latest per key)
- Any table can be unfolded into a stream (by capturing each change as an event)

### 4.2 KStream, KTable, GlobalKTable

| Abstraction | Semantics | Partitioning | Use Case |
|-------------|-----------|--------------|----------|
| KStream | Insert (append-only) | Co-partitioned | Event streams, clicks, logs |
| KTable | Upsert (latest per key) | Co-partitioned | Materialized state, user profiles |
| GlobalKTable | Upsert (full copy on every instance) | Broadcast | Small reference data, config |

```java
StreamsBuilder builder = new StreamsBuilder();

// Stream of order events
KStream<String, Order> orders = builder.stream("orders",
    Consumed.with(Serdes.String(), orderSerde));

// Table of customer profiles (compacted topic)
KTable<String, Customer> customers = builder.table("customers",
    Consumed.with(Serdes.String(), customerSerde));

// Global table of product catalog (small, needs full copy)
GlobalKTable<String, Product> products = builder.globalTable("products",
    Consumed.with(Serdes.String(), productSerde));
```

### 4.3 Stateful Operations

#### Aggregation

```java
KTable<String, Long> orderCountsByCustomer = orders
    .groupByKey()
    .count(Materialized.as("order-counts-store"));

KTable<String, OrderStats> orderStats = orders
    .groupByKey()
    .aggregate(
        OrderStats::new,
        (customerId, order, stats) -> stats.add(order),
        Materialized.<String, OrderStats, KeyValueStore<Bytes, byte[]>>as("order-stats-store")
            .withKeySerde(Serdes.String())
            .withValueSerde(orderStatsSerde)
    );
```

#### Joins

```java
// Stream-Table join (enrichment)
KStream<String, EnrichedOrder> enrichedOrders = orders.join(
    customers,
    (order, customer) -> new EnrichedOrder(order, customer)
);

// Stream-GlobalKTable join (lookup, no co-partitioning required)
KStream<String, FullOrder> fullOrders = enrichedOrders.join(
    products,
    (key, enrichedOrder) -> enrichedOrder.getProductId(),  // Key extractor
    (enrichedOrder, product) -> new FullOrder(enrichedOrder, product)
);

// Stream-Stream join (windowed)
KStream<String, CombinedEvent> combined = clicks.join(
    impressions,
    (click, impression) -> new CombinedEvent(click, impression),
    JoinWindows.ofTimeDifferenceWithNoGrace(Duration.ofMinutes(5)),
    StreamJoined.with(Serdes.String(), clickSerde, impressionSerde)
);
```

### 4.4 Windowing

| Window Type | Behavior | Use Case |
|-------------|----------|----------|
| Tumbling | Fixed-size, non-overlapping | Hourly aggregation |
| Hopping | Fixed-size, overlapping by advance interval | Rolling averages |
| Sliding | Fixed-size, triggered per event | Precise event correlation |
| Session | Dynamic size based on activity gaps | User session analysis |

```java
// Tumbling window: 1-hour buckets
KTable<Windowed<String>, Long> hourlyClicks = clicks
    .groupByKey()
    .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofHours(1)))
    .count(Materialized.as("hourly-clicks"));

// Hopping window: 5-min windows advancing every 1 min
KTable<Windowed<String>, Double> rollingAvg = metrics
    .groupByKey()
    .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofMinutes(5))
        .advanceBy(Duration.ofMinutes(1)))
    .aggregate(/* ... */);

// Session window: 30-min inactivity gap
KTable<Windowed<String>, SessionData> sessions = events
    .groupByKey()
    .windowedBy(SessionWindows.ofInactivityGapWithNoGrace(Duration.ofMinutes(30)))
    .aggregate(/* ... */);
```

### 4.5 State Stores (RocksDB)

Kafka Streams persists local state in RocksDB by default. Each stateful operation creates a state store backed by:
- A local RocksDB instance for fast lookups
- A changelog topic for fault tolerance (replayed on recovery)

```java
// Custom state store
StoreBuilder<KeyValueStore<String, UserProfile>> storeBuilder =
    Stores.keyValueStoreBuilder(
        Stores.persistentKeyValueStore("user-profiles"),
        Serdes.String(),
        userProfileSerde
    ).withCachingEnabled()
     .withLoggingEnabled(Map.of(
         "cleanup.policy", "compact",
         "retention.ms", "-1"
     ));

builder.addStateStore(storeBuilder);
```

### 4.6 Interactive Queries

State stores can be queried directly via the Interactive Queries API, turning Kafka Streams into a queryable materialized view:

```java
ReadOnlyKeyValueStore<String, OrderStats> store =
    streams.store(StoreQueryParameters.fromNameAndType(
        "order-stats-store", QueryableStoreTypes.keyValueStore()));

OrderStats stats = store.get("customer-123");

// Range queries
KeyValueIterator<String, OrderStats> range = store.range("customer-100", "customer-200");
```

For distributed deployments, use `streams.metadataForKey()` to locate which instance holds a given key, then route queries accordingly.

### 4.7 Exactly-Once Stream Processing

```java
Properties props = new Properties();
props.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2);
props.put(StreamsConfig.APPLICATION_ID_CONFIG, "order-processor");
props.put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka1:9092");
props.put(StreamsConfig.NUM_STREAM_THREADS_CONFIG, 4);
```

`EXACTLY_ONCE_V2` (Kafka 3.0+) uses a single transaction per task rather than per-partition, significantly reducing overhead compared to the deprecated `EXACTLY_ONCE` (v1).

### 4.8 Topology Optimization

```java
Properties props = new Properties();
props.put(StreamsConfig.TOPOLOGY_OPTIMIZATION_CONFIG, StreamsConfig.OPTIMIZE);
```

Optimizations include:
- Merging repartition topics when multiple operations share the same key
- Reusing source topics as changelog topics
- Eliminating redundant serialization/deserialization steps

---

## 5. Kafka Connect

### 5.1 Architecture

Kafka Connect is a framework for streaming data between Kafka and external systems using reusable connectors.

**Distributed mode:**
- Multiple workers form a Connect cluster
- Connectors and tasks are distributed across workers
- Automatic rebalancing on worker failure
- Configuration stored in internal Kafka topics

```properties
# connect-distributed.properties
bootstrap.servers=kafka1:9092,kafka2:9092,kafka3:9092
group.id=connect-cluster

key.converter=org.apache.kafka.connect.json.JsonConverter
value.converter=io.confluent.connect.avro.AvroConverter
value.converter.schema.registry.url=http://schema-registry:8081

config.storage.topic=connect-configs
offset.storage.topic=connect-offsets
status.storage.topic=connect-status

config.storage.replication.factor=3
offset.storage.replication.factor=3
status.storage.replication.factor=3
```

### 5.2 Source and Sink Connectors

**Source connectors** pull data from external systems into Kafka topics:

```json
{
    "name": "postgres-source",
    "config": {
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "database.hostname": "postgres",
        "database.port": "5432",
        "database.user": "${secrets:postgres/username}",
        "database.password": "${secrets:postgres/password}",
        "database.dbname": "orders_db",
        "database.server.name": "orders",
        "table.include.list": "public.orders,public.customers",
        "plugin.name": "pgoutput",
        "slot.name": "debezium_orders",
        "publication.name": "dbz_publication",
        "topic.prefix": "cdc",
        "snapshot.mode": "initial",
        "transforms": "route",
        "transforms.route.type": "org.apache.kafka.connect.transforms.RegexRouter",
        "transforms.route.regex": "([^.]+)\\.([^.]+)\\.([^.]+)",
        "transforms.route.replacement": "$3"
    }
}
```

**Sink connectors** push data from Kafka topics to external systems:

```json
{
    "name": "elasticsearch-sink",
    "config": {
        "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
        "topics": "orders,customers",
        "connection.url": "http://elasticsearch:9200",
        "type.name": "_doc",
        "key.ignore": "false",
        "schema.ignore": "false",
        "behavior.on.malformed.documents": "warn",
        "behavior.on.null.values": "delete",
        "write.method": "upsert",
        "batch.size": 2000,
        "max.buffered.records": 20000,
        "flush.timeout.ms": 120000
    }
}
```

### 5.3 Single Message Transforms (SMT)

SMTs modify records in-flight without a full stream processing pipeline:

```json
{
    "transforms": "extractTimestamp,maskFields,addMetadata",
    "transforms.extractTimestamp.type": "org.apache.kafka.connect.transforms.InsertField$Value",
    "transforms.extractTimestamp.timestamp.field": "ingested_at",
    
    "transforms.maskFields.type": "org.apache.kafka.connect.transforms.MaskField$Value",
    "transforms.maskFields.fields": "ssn,credit_card",
    "transforms.maskFields.replacement": "***REDACTED***",
    
    "transforms.addMetadata.type": "org.apache.kafka.connect.transforms.InsertField$Value",
    "transforms.addMetadata.static.field": "pipeline",
    "transforms.addMetadata.static.value": "cdc-v2"
}
```

Common SMTs:
- `ExtractField` — extract a field from struct or map
- `ReplaceField` — include/exclude/rename fields
- `TimestampConverter` — convert between timestamp formats
- `RegexRouter` — rename destination topics
- `Flatten` — flatten nested structures
- `Cast` — cast field types

### 5.4 Dead Letter Queues

For sink connectors, DLQs capture records that fail processing:

```json
{
    "errors.tolerance": "all",
    "errors.deadletterqueue.topic.name": "dlq-elasticsearch-sink",
    "errors.deadletterqueue.topic.replication.factor": 3,
    "errors.deadletterqueue.context.headers.enable": true,
    "errors.log.enable": true,
    "errors.log.include.messages": true
}
```

Headers on DLQ records include error class, message, stack trace, topic, partition, and offset of the failed record.

### 5.5 Connector Lifecycle Management

```bash
# List connectors
curl -s http://connect:8083/connectors | jq .

# Get connector status
curl -s http://connect:8083/connectors/postgres-source/status | jq .

# Pause connector
curl -X PUT http://connect:8083/connectors/postgres-source/pause

# Resume connector
curl -X PUT http://connect:8083/connectors/postgres-source/resume

# Restart failed task
curl -X POST http://connect:8083/connectors/postgres-source/tasks/0/restart

# Update configuration
curl -X PUT http://connect:8083/connectors/postgres-source/config \
    -H "Content-Type: application/json" \
    -d @updated-config.json

# Delete connector
curl -X DELETE http://connect:8083/connectors/postgres-source
```

### 5.6 Popular Connectors

| Connector | Type | Description |
|-----------|------|-------------|
| Debezium PostgreSQL | Source | CDC from PostgreSQL via logical replication |
| Debezium MySQL | Source | CDC from MySQL via binlog |
| JDBC Source | Source | Poll-based ingestion from any JDBC database |
| JDBC Sink | Sink | Write to RDBMS via JDBC |
| S3 Sink | Sink | Write to S3 in Avro/Parquet/JSON |
| Elasticsearch Sink | Sink | Index documents in Elasticsearch/OpenSearch |
| BigQuery Sink | Sink | Load into Google BigQuery |
| HTTP Source/Sink | Both | REST API integration |
| FileStream | Both | File-based (dev/testing only) |

### 5.7 Custom Connector Development

```java
public class CustomApiSourceConnector extends SourceConnector {
    private Map<String, String> config;
    
    @Override
    public void start(Map<String, String> props) {
        this.config = props;
    }
    
    @Override
    public Class<? extends Task> taskClass() {
        return CustomApiSourceTask.class;
    }
    
    @Override
    public List<Map<String, String>> taskConfigs(int maxTasks) {
        // Distribute work across tasks
        List<Map<String, String>> taskConfigs = new ArrayList<>();
        List<String> endpoints = parseEndpoints(config.get("api.endpoints"));
        
        for (int i = 0; i < Math.min(maxTasks, endpoints.size()); i++) {
            Map<String, String> taskConfig = new HashMap<>(config);
            taskConfig.put("task.endpoint", endpoints.get(i));
            taskConfigs.add(taskConfig);
        }
        return taskConfigs;
    }
    
    @Override
    public ConfigDef config() {
        return new ConfigDef()
            .define("api.url", ConfigDef.Type.STRING, ConfigDef.Importance.HIGH, "API base URL")
            .define("api.endpoints", ConfigDef.Type.LIST, ConfigDef.Importance.HIGH, "Endpoints to poll")
            .define("poll.interval.ms", ConfigDef.Type.LONG, 60000L, ConfigDef.Importance.MEDIUM, "Poll interval");
    }
}

public class CustomApiSourceTask extends SourceTask {
    private String endpoint;
    private long pollInterval;
    
    @Override
    public void start(Map<String, String> props) {
        this.endpoint = props.get("task.endpoint");
        this.pollInterval = Long.parseLong(props.get("poll.interval.ms"));
    }
    
    @Override
    public List<SourceRecord> poll() throws InterruptedException {
        Thread.sleep(pollInterval);
        
        List<ApiRecord> apiRecords = fetchFromApi(endpoint);
        Map<String, Object> sourcePartition = Map.of("endpoint", endpoint);
        
        return apiRecords.stream()
            .map(r -> new SourceRecord(
                sourcePartition,
                Map.of("position", r.getId()),
                "api-events",
                Schema.STRING_SCHEMA, r.getKey(),
                Schema.STRING_SCHEMA, r.getValue()
            ))
            .collect(Collectors.toList());
    }
}
```

---

## 6. Schema Management

### 6.1 Schema Registry

The Schema Registry (Confluent or Apicurio) provides a centralized service for managing schemas and ensuring compatibility between producers and consumers.

**Architecture:**
- REST API for schema registration and retrieval
- Kafka topic (`_schemas`) as the durable backend
- Local caching for performance
- High availability via leader election among multiple instances

```
Producer → Serialize (lookup/register schema) → Schema Registry
                                                       ↓
                                              Store in _schemas topic
                                                       ↓
Consumer → Deserialize (fetch schema by ID) ← Schema Registry
```

### 6.2 Serialization Formats

#### Avro

```json
{
    "type": "record",
    "name": "Order",
    "namespace": "com.example.events",
    "fields": [
        {"name": "order_id", "type": "string"},
        {"name": "customer_id", "type": "string"},
        {"name": "amount", "type": {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}},
        {"name": "currency", "type": {"type": "enum", "name": "Currency", "symbols": ["USD", "EUR", "GBP"]}},
        {"name": "items", "type": {"type": "array", "items": {
            "type": "record",
            "name": "OrderItem",
            "fields": [
                {"name": "sku", "type": "string"},
                {"name": "quantity", "type": "int"},
                {"name": "unit_price", "type": {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}}
            ]
        }}},
        {"name": "created_at", "type": {"type": "long", "logicalType": "timestamp-millis"}},
        {"name": "metadata", "type": ["null", {"type": "map", "values": "string"}], "default": null}
    ]
}
```

#### Protobuf

```protobuf
syntax = "proto3";

package com.example.events;

import "google/protobuf/timestamp.proto";

message Order {
    string order_id = 1;
    string customer_id = 2;
    
    message Money {
        int64 units = 1;
        int32 nanos = 2;
        string currency = 3;
    }
    
    Money amount = 3;
    
    message OrderItem {
        string sku = 1;
        int32 quantity = 2;
        Money unit_price = 3;
    }
    
    repeated OrderItem items = 4;
    google.protobuf.Timestamp created_at = 5;
    map<string, string> metadata = 6;
}
```

#### JSON Schema

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Order",
    "type": "object",
    "required": ["order_id", "customer_id", "amount", "items"],
    "properties": {
        "order_id": {"type": "string", "format": "uuid"},
        "customer_id": {"type": "string"},
        "amount": {"type": "number", "minimum": 0},
        "currency": {"type": "string", "enum": ["USD", "EUR", "GBP"]},
        "items": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["sku", "quantity"],
                "properties": {
                    "sku": {"type": "string"},
                    "quantity": {"type": "integer", "minimum": 1},
                    "unit_price": {"type": "number", "minimum": 0}
                }
            }
        },
        "created_at": {"type": "string", "format": "date-time"}
    }
}
```

### 6.3 Compatibility Modes

| Mode | Rule | Can Add | Can Remove | Use Case |
|------|------|---------|------------|----------|
| BACKWARD | New schema can read old data | Optional fields | Yes (with defaults) | Default — consumers upgrade first |
| FORWARD | Old schema can read new data | Yes | Optional fields | Producers upgrade first |
| FULL | Both BACKWARD and FORWARD | Optional fields only | Optional fields only | Maximum safety |
| NONE | No compatibility check | Anything | Anything | Development only |

**Transitive variants** (BACKWARD_TRANSITIVE, FORWARD_TRANSITIVE, FULL_TRANSITIVE) check against all previous versions, not just the latest.

### 6.4 Schema Evolution Strategies

**Safe evolution rules (BACKWARD compatible):**
- Add fields with default values
- Remove fields that had defaults
- Widen numeric types (int → long)

**Breaking changes (require NONE mode or new topic):**
- Renaming fields
- Changing field types incompatibly
- Removing required fields without defaults
- Changing enum symbols

```bash
# Set compatibility for a subject
curl -X PUT http://schema-registry:8081/config/orders-value \
    -H "Content-Type: application/vnd.schemaregistry.v1+json" \
    -d '{"compatibility": "BACKWARD"}'

# Test compatibility before registering
curl -X POST http://schema-registry:8081/compatibility/subjects/orders-value/versions/latest \
    -H "Content-Type: application/vnd.schemaregistry.v1+json" \
    -d '{"schema": "{...}"}'
```

### 6.5 Broker-Level Schema Validation (Confluent Server)

Confluent Server can enforce schema validation at the broker:

```bash
kafka-configs.sh --bootstrap-server kafka1:9092 \
    --entity-type topics --entity-name orders \
    --alter --add-config \
    'confluent.value.schema.validation=true,confluent.key.schema.validation=true'
```

Records that fail validation are rejected with a `INVALID_RECORD` error.

### 6.6 Subject Naming Strategies

| Strategy | Subject Name | Use Case |
|----------|-------------|----------|
| TopicNameStrategy | `<topic>-key` / `<topic>-value` | Default — one schema per topic |
| RecordNameStrategy | `<fully.qualified.record.name>` | Multiple event types per topic |
| TopicRecordNameStrategy | `<topic>-<record.name>` | Multiple types, topic-scoped |

**Python with Schema Registry:**

```python
from confluent_kafka import SerializingProducer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer

schema_registry_conf = {"url": "http://schema-registry:8081"}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

avro_serializer = AvroSerializer(
    schema_registry_client,
    schema_str=order_schema_str,
    to_dict=lambda order, ctx: order.to_dict(),
    conf={"auto.register.schemas": True, "subject.name.strategy": topic_record_subject_name_strategy}
)

producer_conf = {
    "bootstrap.servers": "kafka1:9092",
    "key.serializer": StringSerializer("utf_8"),
    "value.serializer": avro_serializer,
}

producer = SerializingProducer(producer_conf)
producer.produce(topic="orders", key=order.order_id, value=order)
producer.flush()
```

---

## 7. Performance Tuning

### 7.1 Broker Tuning

#### Thread Configuration

```properties
# Network threads handling socket I/O
num.network.threads=8

# I/O threads handling disk reads/writes
num.io.threads=16

# Background threads for log cleaning, expiration
background.threads=10

# Request handler queue size
queued.max.requests=500
```

Rule of thumb: `num.network.threads` = number of CPU cores (for network-heavy workloads); `num.io.threads` = 2× the number of disks.

#### Log Configuration

```properties
# Segment size — smaller segments mean more frequent rolling but faster cleanup
log.segment.bytes=1073741824

# Index interval — how frequently offset indexes are written
log.index.interval.bytes=4096

# Flush behavior (usually leave to OS page cache)
log.flush.interval.messages=10000
log.flush.interval.ms=1000

# Retention
log.retention.hours=168
log.retention.bytes=-1
log.cleanup.policy=delete

# Compaction tuning
log.cleaner.threads=4
log.cleaner.dedupe.buffer.size=134217728
log.cleaner.io.buffer.size=524288
```

#### Replication

```properties
# Replica fetch configuration
replica.fetch.max.bytes=1048576
replica.fetch.wait.max.ms=500
replica.fetch.min.bytes=1

# How long before a slow replica is removed from ISR
replica.lag.time.max.ms=30000

# Leader imbalance check
leader.imbalance.check.interval.seconds=300
leader.imbalance.per.broker.percentage=10
```

### 7.2 Producer Optimization

```properties
# Batching
batch.size=131072          # 128 KB batches
linger.ms=50               # Wait up to 50ms to fill batch
buffer.memory=134217728    # 128 MB buffer

# Compression
compression.type=lz4

# Network
max.in.flight.requests.per.connection=5
send.buffer.bytes=131072
request.timeout.ms=30000
delivery.timeout.ms=120000

# Idempotence (prevents duplicates on retry)
enable.idempotence=true
acks=all
retries=2147483647
max.in.flight.requests.per.connection=5
```

**High-throughput producer profile:**

```python
producer = Producer({
    "bootstrap.servers": "kafka1:9092,kafka2:9092,kafka3:9092",
    "compression.type": "lz4",
    "batch.size": 131072,
    "linger.ms": 50,
    "buffer.memory": 134217728,
    "acks": "all",
    "enable.idempotence": True,
    "max.in.flight.requests.per.connection": 5,
    "queue.buffering.max.messages": 1000000,
    "queue.buffering.max.kbytes": 2097152,  # 2 GB
})
```

### 7.3 Consumer Throughput

```properties
# Fetch tuning
fetch.min.bytes=1048576            # Wait for 1 MB before returning
fetch.max.wait.ms=500              # But no longer than 500ms
max.partition.fetch.bytes=1048576  # 1 MB per partition per fetch
max.poll.records=1000              # Records per poll()

# Session management
session.timeout.ms=45000
heartbeat.interval.ms=15000
max.poll.interval.ms=300000

# Threading
# Use multiple consumers in a group (one per thread/pod)
# Or use manual partition assignment with multi-threaded processing
```

**Multi-threaded consumption pattern:**

```java
int numThreads = Runtime.getRuntime().availableProcessors();
ExecutorService executor = Executors.newFixedThreadPool(numThreads);

while (!shutdown.get()) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    
    List<Future<?>> futures = new ArrayList<>();
    for (TopicPartition partition : records.partitions()) {
        List<ConsumerRecord<String, String>> partitionRecords = records.records(partition);
        futures.add(executor.submit(() -> processPartitionBatch(partitionRecords)));
    }
    
    // Wait for all partition batches to complete
    for (Future<?> future : futures) {
        future.get(30, TimeUnit.SECONDS);
    }
    
    consumer.commitSync();
}
```

### 7.4 OS-Level Tuning

#### Page Cache

Kafka relies heavily on the OS page cache. Allocate at least 30-50% of RAM to page cache (do not over-allocate heap):

```bash
# JVM heap should NOT exceed 6-8 GB for brokers
export KAFKA_HEAP_OPTS="-Xms6g -Xmx6g"

# Check page cache usage
free -h
cat /proc/meminfo | grep -i cache
```

#### Network Buffers

```bash
# /etc/sysctl.conf
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.core.rmem_default=16777216
net.core.wmem_default=16777216
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
net.core.netdev_max_backlog=50000
net.ipv4.tcp_max_syn_backlog=8192
net.core.somaxconn=32768
```

#### Filesystem

```bash
# Use XFS for Kafka log directories (better than ext4 for large sequential I/O)
mkfs.xfs -f /dev/nvme0n1
mount -o noatime,nodiratime /dev/nvme0n1 /var/kafka-logs

# Disable swap (or set swappiness very low)
echo 1 > /proc/sys/vm/swappiness

# Increase file descriptors
# /etc/security/limits.conf
kafka    soft    nofile    1000000
kafka    hard    nofile    1000000
```

### 7.5 Benchmarking

```bash
# Producer benchmark
kafka-producer-perf-test.sh \
    --topic perf-test \
    --num-records 10000000 \
    --record-size 1024 \
    --throughput -1 \
    --producer-props \
        bootstrap.servers=kafka1:9092 \
        acks=all \
        compression.type=lz4 \
        batch.size=131072 \
        linger.ms=50

# Consumer benchmark
kafka-consumer-perf-test.sh \
    --bootstrap-server kafka1:9092 \
    --topic perf-test \
    --messages 10000000 \
    --threads 4 \
    --fetch-size 1048576

# End-to-end latency
kafka-e2e-latency.sh kafka1:9092 latency-test 10000 all 1
```

### 7.6 Partition Count Optimization

**Too few partitions:**
- Limited consumer parallelism
- Higher latency under load (single partition bottleneck)

**Too many partitions:**
- More file handles and memory on brokers
- Longer leader election time during broker failure
- Higher end-to-end latency (more batching delays)
- Larger metadata overhead on controller

**Guidelines:**
- Start with `max(throughput_requirement / throughput_per_partition, max_consumers)`
- Typical throughput per partition: 10-100 MB/s depending on hardware
- Target: 10-50 partitions per broker for most workloads
- Never exceed a few thousand partitions per broker (KRaft handles this better than ZK)

---

## 8. Security

### 8.1 SASL Authentication

Kafka supports multiple SASL mechanisms:

| Mechanism | Use Case | Notes |
|-----------|----------|-------|
| PLAIN | Development, simple deployments | Credentials in plain text (use with TLS) |
| SCRAM-SHA-256/512 | Production without Kerberos | Stored in ZK/KRaft, supports dynamic creation |
| GSSAPI (Kerberos) | Enterprise environments | Requires KDC infrastructure |
| OAUTHBEARER | Cloud-native, token-based | Integrates with IdP (Keycloak, Okta, etc.) |

**SCRAM configuration (broker):**

```properties
# server.properties
listeners=SASL_SSL://0.0.0.0:9093
security.inter.broker.protocol=SASL_SSL
sasl.mechanism.inter.broker.protocol=SCRAM-SHA-512
sasl.enabled.mechanisms=SCRAM-SHA-512

# JAAS configuration
listener.name.sasl_ssl.scram-sha-512.sasl.jaas.config=\
    org.apache.kafka.common.security.scram.ScramLoginModule required \
    username="admin" \
    password="${KAFKA_ADMIN_PASSWORD}";
```

**Create SCRAM credentials:**

```bash
kafka-configs.sh --bootstrap-server kafka1:9093 \
    --command-config admin.properties \
    --alter --add-config 'SCRAM-SHA-512=[password=s3cure-passw0rd]' \
    --entity-type users --entity-name app-producer
```

**OAUTHBEARER configuration:**

```properties
sasl.enabled.mechanisms=OAUTHBEARER
sasl.oauthbearer.token.endpoint.url=https://keycloak.example.com/realms/kafka/protocol/openid-connect/token
listener.name.sasl_ssl.oauthbearer.sasl.jaas.config=\
    org.apache.kafka.common.security.oauthbearer.OAuthBearerLoginModule required \
    clientId="kafka-broker" \
    clientSecret="${OAUTH_CLIENT_SECRET}" \
    scope="kafka";
sasl.oauthbearer.expected.audience=kafka
```

### 8.2 TLS Encryption

#### Inter-Broker TLS

```properties
# Broker-to-broker communication
security.inter.broker.protocol=SSL
ssl.keystore.location=/etc/kafka/ssl/kafka-broker1.keystore.jks
ssl.keystore.password=${KEYSTORE_PASSWORD}
ssl.key.password=${KEY_PASSWORD}
ssl.truststore.location=/etc/kafka/ssl/kafka.truststore.jks
ssl.truststore.password=${TRUSTSTORE_PASSWORD}
ssl.client.auth=required
ssl.endpoint.identification.algorithm=https
```

#### Client-Broker TLS

```properties
# Client configuration
security.protocol=SSL
ssl.truststore.location=/etc/kafka/ssl/client.truststore.jks
ssl.truststore.password=${TRUSTSTORE_PASSWORD}
ssl.keystore.location=/etc/kafka/ssl/client.keystore.jks
ssl.keystore.password=${KEYSTORE_PASSWORD}
ssl.key.password=${KEY_PASSWORD}
ssl.endpoint.identification.algorithm=https
```

**Python TLS client:**

```python
from confluent_kafka import Producer

producer = Producer({
    "bootstrap.servers": "kafka1:9093",
    "security.protocol": "SSL",
    "ssl.ca.location": "/etc/kafka/ssl/ca-cert.pem",
    "ssl.certificate.location": "/etc/kafka/ssl/client-cert.pem",
    "ssl.key.location": "/etc/kafka/ssl/client-key.pem",
    "ssl.key.password": os.environ["SSL_KEY_PASSWORD"],
    "ssl.endpoint.identification.algorithm": "https",
})
```

### 8.3 ACLs (Access Control Lists)

```bash
# Grant producer access to a topic
kafka-acls.sh --bootstrap-server kafka1:9093 \
    --command-config admin.properties \
    --add --allow-principal User:app-producer \
    --operation Write --operation Describe \
    --topic orders

# Grant consumer group access
kafka-acls.sh --bootstrap-server kafka1:9093 \
    --command-config admin.properties \
    --add --allow-principal User:app-consumer \
    --operation Read --operation Describe \
    --topic orders \
    --group order-processors

# Deny access from specific host
kafka-acls.sh --bootstrap-server kafka1:9093 \
    --command-config admin.properties \
    --add --deny-principal User:suspect-app \
    --deny-host 10.0.0.50 \
    --operation All \
    --topic '*'

# List all ACLs
kafka-acls.sh --bootstrap-server kafka1:9093 \
    --command-config admin.properties --list

# Prefixed ACLs (apply to all topics matching prefix)
kafka-acls.sh --bootstrap-server kafka1:9093 \
    --command-config admin.properties \
    --add --allow-principal User:analytics-team \
    --operation Read --operation Describe \
    --topic analytics- --resource-pattern-type prefixed
```

### 8.4 RBAC (Confluent Platform)

Confluent Platform provides RBAC with predefined roles:

| Role | Scope | Permissions |
|------|-------|-------------|
| SystemAdmin | Cluster | Full cluster management |
| ClusterAdmin | Cluster | Broker config, create topics |
| Operator | Cluster | Read-only cluster operations |
| ResourceOwner | Topic/Group/Subject | Full control over specific resources |
| DeveloperRead | Topic/Group | Consume, describe |
| DeveloperWrite | Topic | Produce, describe |
| DeveloperManage | Topic/Group/Subject | Create, delete, alter |

```bash
# Assign role
confluent iam rbac role-binding create \
    --principal User:analytics-team \
    --role DeveloperRead \
    --environment production \
    --kafka-cluster-id lkc-abc123 \
    --resource Topic:analytics-
```

### 8.5 Audit Logging

```properties
# Confluent audit logging
confluent.security.event.logger.enable=true
confluent.security.event.logger.exporter.class=io.confluent.security.auth.provider.audit.KafkaAuditLogExporter
confluent.security.event.logger.authentication.enable=true
confluent.security.event.logger.authorization.enable=true
confluent.security.event.logger.destination.topic=confluent-audit-log-events
```

### 8.6 Data at Rest Encryption

Kafka does not natively encrypt data at rest. Options:

1. **Filesystem encryption**: LUKS, dm-crypt, AWS EBS encryption
2. **Application-level encryption**: Encrypt record values before producing
3. **Confluent Server**: Provides BYOK (Bring Your Own Key) encryption

**Application-level encryption pattern:**

```java
public class EncryptingSerializer implements Serializer<String> {
    private Cipher cipher;
    
    @Override
    public void configure(Map<String, ?> configs, boolean isKey) {
        SecretKey key = loadEncryptionKey(configs.get("encryption.key.id"));
        cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, key);
    }
    
    @Override
    public byte[] serialize(String topic, String data) {
        byte[] iv = cipher.getIV();
        byte[] ciphertext = cipher.doFinal(data.getBytes(StandardCharsets.UTF_8));
        
        ByteBuffer buffer = ByteBuffer.allocate(4 + iv.length + ciphertext.length);
        buffer.putInt(iv.length);
        buffer.put(iv);
        buffer.put(ciphertext);
        return buffer.array();
    }
}
```

### 8.7 Network Security (Listeners)

```properties
# Multiple listeners for different networks
listeners=INTERNAL://0.0.0.0:9092,EXTERNAL://0.0.0.0:9093,REPLICATION://0.0.0.0:9094

# Advertised listeners (what clients see)
advertised.listeners=INTERNAL://broker1.internal:9092,EXTERNAL://kafka.example.com:9093,REPLICATION://broker1.internal:9094

# Map listener names to security protocols
listener.security.protocol.map=INTERNAL:SASL_SSL,EXTERNAL:SASL_SSL,REPLICATION:SSL

# Inter-broker uses dedicated replication listener
inter.broker.listener.name=REPLICATION

# Per-listener authentication
listener.name.internal.sasl.enabled.mechanisms=SCRAM-SHA-512
listener.name.external.sasl.enabled.mechanisms=OAUTHBEARER
```

### 8.8 Common Attack Vectors

| Attack | Description | Mitigation |
|--------|-------------|------------|
| Unauthorized access | Direct broker access without auth | Enable SASL + ACLs |
| Man-in-the-middle | Intercept unencrypted traffic | TLS with endpoint verification |
| Topic enumeration | Discovering internal topics | Restrict Describe permissions |
| Consumer group hijack | Joining another app's consumer group | ACLs on consumer groups |
| Partition flooding | Overwhelming a partition with data | Quotas (`producer_byte_rate`) |
| Schema poisoning | Registering incompatible schemas | Schema Registry ACLs + compatibility rules |
| Credential leakage | Secrets in config files | External secret managers, short-lived tokens |

**Broker quotas for rate limiting:**

```bash
# Limit producer to 10 MB/s
kafka-configs.sh --bootstrap-server kafka1:9093 \
    --alter --add-config 'producer_byte_rate=10485760' \
    --entity-type users --entity-name app-producer

# Limit consumer to 50 MB/s
kafka-configs.sh --bootstrap-server kafka1:9093 \
    --alter --add-config 'consumer_byte_rate=52428800' \
    --entity-type users --entity-name app-consumer
```

---

## 9. Operations

### 9.1 Multi-Cluster Architectures

#### MirrorMaker 2 (MM2)

MM2 is built on Kafka Connect and provides active-active or active-passive replication:

```properties
# mm2.properties
clusters=us-east, eu-west
us-east.bootstrap.servers=kafka-us1:9092,kafka-us2:9092
eu-west.bootstrap.servers=kafka-eu1:9092,kafka-eu2:9092

# Replication flows
us-east->eu-west.enabled=true
us-east->eu-west.topics=orders.*,customers.*
us-east->eu-west.groups=.*

eu-west->us-east.enabled=true
eu-west->us-east.topics=events.*

# Configuration
replication.factor=3
sync.topic.configs.enabled=true
sync.topic.acls.enabled=true
emit.heartbeats.enabled=true
emit.checkpoints.enabled=true
refresh.topics.interval.seconds=30

# Rename strategy
replication.policy.class=org.apache.kafka.connect.mirror.DefaultReplicationPolicy
replication.policy.separator=.
```

**Topic naming in MM2:**
- Source topic `orders` in `us-east` appears as `us-east.orders` in `eu-west`
- Consumers can failover by seeking to checkpointed offsets

#### Cluster Linking (Confluent)

Cluster Linking provides byte-for-byte replication without MM2 overhead:

```bash
# Create cluster link
kafka-cluster-links.sh --bootstrap-server kafka-dest:9092 \
    --create --link us-east-link \
    --config-file link.properties

# Create mirror topic
kafka-mirrors.sh --bootstrap-server kafka-dest:9092 \
    --create --mirror-topic orders \
    --link us-east-link
```

### 9.2 Monitoring

#### Critical JMX Metrics

| Category | Metric | Threshold |
|----------|--------|-----------|
| Throughput | `kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec` | Baseline dependent |
| Latency | `kafka.network:type=RequestMetrics,name=TotalTimeMs,request=Produce` | < 100ms p99 |
| Replication | `kafka.server:type=ReplicaManager,name=UnderReplicatedPartitions` | 0 |
| Controller | `kafka.controller:type=KafkaController,name=ActiveControllerCount` | Exactly 1 |
| ISR | `kafka.server:type=ReplicaManager,name=IsrShrinksPerSec` | Near 0 |
| Requests | `kafka.network:type=RequestChannel,name=RequestQueueSize` | < queued.max.requests |
| Log | `kafka.log:type=LogFlushStats,name=LogFlushRateAndTimeMs` | < 100ms p99 |
| GC | JVM GC pause time | < 200ms |

#### Prometheus + Grafana Setup

```yaml
# docker-compose monitoring stack
services:
  jmx-exporter:
    image: bitnami/jmx-exporter:latest
    volumes:
      - ./jmx-exporter-config.yaml:/etc/jmx-exporter/config.yaml
    ports:
      - "5556:5556"
    command:
      - "5556"
      - "/etc/jmx-exporter/config.yaml"

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: "${GRAFANA_PASSWORD}"
```

**JMX exporter configuration:**

```yaml
# jmx-exporter-config.yaml
hostPort: kafka1:9999
lowercaseOutputName: true
lowercaseOutputLabelNames: true
rules:
  - pattern: kafka.server<type=(.+), name=(.+), clientId=(.+), topic=(.+), partition=(.+)><>Value
    name: kafka_server_$1_$2
    labels:
      clientId: "$3"
      topic: "$4"
      partition: "$5"
  - pattern: kafka.server<type=(.+), name=(.+)><>Value
    name: kafka_server_$1_$2
  - pattern: kafka.controller<type=(.+), name=(.+)><>Value
    name: kafka_controller_$1_$2
```

**Key Grafana dashboard panels:**
- Under-replicated partitions over time
- Produce/fetch request rate and latency percentiles
- Consumer group lag by topic
- Broker network throughput
- Disk usage and I/O wait
- JVM heap and GC pause duration

### 9.3 Partition Reassignment

```bash
# Generate reassignment plan
kafka-reassign-partitions.sh --bootstrap-server kafka1:9092 \
    --topics-to-move-json-file topics.json \
    --broker-list "1,2,3,4" \
    --generate

# Execute reassignment
kafka-reassign-partitions.sh --bootstrap-server kafka1:9092 \
    --reassignment-json-file plan.json \
    --execute

# Throttle reassignment to 100 MB/s to avoid impact
kafka-reassign-partitions.sh --bootstrap-server kafka1:9092 \
    --reassignment-json-file plan.json \
    --execute \
    --throttle 104857600

# Verify completion
kafka-reassign-partitions.sh --bootstrap-server kafka1:9092 \
    --reassignment-json-file plan.json \
    --verify
```

### 9.4 Rolling Upgrades

1. Update broker binary on one node
2. Start broker with `inter.broker.protocol.version` set to the OLD version
3. Verify the broker rejoins the cluster and replicas are in-sync
4. Repeat for all brokers
5. Once all brokers run the new version, update `inter.broker.protocol.version` to the NEW version (rolling restart)
6. Update `log.message.format.version` if changing message format (rolling restart)

```properties
# During upgrade (keep old protocol)
inter.broker.protocol.version=3.5
log.message.format.version=3.5

# After all brokers upgraded (enable new features)
inter.broker.protocol.version=3.6
log.message.format.version=3.6
```

### 9.5 Disaster Recovery

**RPO/RTO targets by strategy:**

| Strategy | RPO | RTO | Cost |
|----------|-----|-----|------|
| Active-Passive (MM2) | Seconds to minutes | Minutes | 2× infrastructure |
| Active-Active (MM2 bidirectional) | Seconds | Seconds (client failover) | 2× + conflict resolution |
| Cluster Linking | Sub-second | Seconds (promote mirror) | 2× storage, low CPU overhead |
| Stretched cluster (rack-aware) | 0 (synchronous) | Automatic | High network cost |

**Backup strategy:**
- Tiered storage to S3/GCS for long-term retention
- Periodic topic snapshots via Kafka Connect S3 Sink
- Schema Registry backup via REST API export

### 9.6 Retention Policies

```properties
# Time-based retention
log.retention.hours=168         # 7 days
log.retention.minutes=-1        # Disabled (hours takes precedence)

# Size-based retention
log.retention.bytes=107374182400  # 100 GB per partition

# Both apply — whichever is reached first triggers deletion

# Compaction (for changelog topics)
log.cleanup.policy=compact
log.cleaner.min.compaction.lag.ms=3600000   # 1 hour before eligible
log.cleaner.max.compaction.lag.ms=86400000  # Force compaction within 24h

# Combined (compact + delete)
log.cleanup.policy=compact,delete
log.retention.hours=720    # Keep 30 days, then delete even compacted
```

### 9.7 Tiered Storage

Tiered storage (KIP-405, GA in Kafka 3.6+) offloads cold log segments to remote storage (S3, GCS, Azure Blob):

```properties
# Broker configuration
remote.log.storage.system.enable=true
remote.log.storage.manager.class.name=org.apache.kafka.server.log.remote.storage.RemoteLogManagerConfig
remote.log.storage.manager.impl.class=io.confluent.kafka.tieredstorage.s3.S3RemoteStorageManager

# S3 backend
remote.log.storage.s3.bucket=kafka-tiered-storage
remote.log.storage.s3.region=us-east-1

# Topic-level tiered storage
kafka-configs.sh --bootstrap-server kafka1:9092 \
    --alter --entity-type topics --entity-name events \
    --add-config 'remote.storage.enable=true,local.retention.ms=86400000,retention.ms=31536000000'
```

This allows 365-day retention with only 24 hours on local disk, dramatically reducing broker storage costs.

---

## 10. Lab Exercises

### Lab 1: Deploy a 3-Broker KRaft Cluster

**Objective:** Set up a production-like Kafka cluster without ZooKeeper.

**docker-compose.yml:**

```yaml
version: "3.8"

services:
  controller1:
    image: apache/kafka:3.7.0
    container_name: controller1
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: controller
      KAFKA_LISTENERS: CONTROLLER://0.0.0.0:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@controller1:9093,2@controller2:9093,3@controller3:9093
      KAFKA_LOG_DIRS: /var/lib/kafka/data
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"
    volumes:
      - controller1-data:/var/lib/kafka/data
    networks:
      - kafka-net

  controller2:
    image: apache/kafka:3.7.0
    container_name: controller2
    environment:
      KAFKA_NODE_ID: 2
      KAFKA_PROCESS_ROLES: controller
      KAFKA_LISTENERS: CONTROLLER://0.0.0.0:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@controller1:9093,2@controller2:9093,3@controller3:9093
      KAFKA_LOG_DIRS: /var/lib/kafka/data
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"
    volumes:
      - controller2-data:/var/lib/kafka/data
    networks:
      - kafka-net

  controller3:
    image: apache/kafka:3.7.0
    container_name: controller3
    environment:
      KAFKA_NODE_ID: 3
      KAFKA_PROCESS_ROLES: controller
      KAFKA_LISTENERS: CONTROLLER://0.0.0.0:9093
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@controller1:9093,2@controller2:9093,3@controller3:9093
      KAFKA_LOG_DIRS: /var/lib/kafka/data
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"
    volumes:
      - controller3-data:/var/lib/kafka/data
    networks:
      - kafka-net

  broker1:
    image: apache/kafka:3.7.0
    container_name: broker1
    depends_on:
      - controller1
      - controller2
      - controller3
    ports:
      - "19092:9092"
    environment:
      KAFKA_NODE_ID: 101
      KAFKA_PROCESS_ROLES: broker
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://broker1:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@controller1:9093,2@controller2:9093,3@controller3:9093
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_LOG_DIRS: /var/lib/kafka/data
      KAFKA_NUM_PARTITIONS: 6
      KAFKA_DEFAULT_REPLICATION_FACTOR: 3
      KAFKA_MIN_INSYNC_REPLICAS: 2
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"
    volumes:
      - broker1-data:/var/lib/kafka/data
    networks:
      - kafka-net

  broker2:
    image: apache/kafka:3.7.0
    container_name: broker2
    depends_on:
      - controller1
      - controller2
      - controller3
    ports:
      - "29092:9092"
    environment:
      KAFKA_NODE_ID: 102
      KAFKA_PROCESS_ROLES: broker
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://broker2:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@controller1:9093,2@controller2:9093,3@controller3:9093
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_LOG_DIRS: /var/lib/kafka/data
      KAFKA_NUM_PARTITIONS: 6
      KAFKA_DEFAULT_REPLICATION_FACTOR: 3
      KAFKA_MIN_INSYNC_REPLICAS: 2
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"
    volumes:
      - broker2-data:/var/lib/kafka/data
    networks:
      - kafka-net

  broker3:
    image: apache/kafka:3.7.0
    container_name: broker3
    depends_on:
      - controller1
      - controller2
      - controller3
    ports:
      - "39092:9092"
    environment:
      KAFKA_NODE_ID: 103
      KAFKA_PROCESS_ROLES: broker
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://broker3:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@controller1:9093,2@controller2:9093,3@controller3:9093
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_LOG_DIRS: /var/lib/kafka/data
      KAFKA_NUM_PARTITIONS: 6
      KAFKA_DEFAULT_REPLICATION_FACTOR: 3
      KAFKA_MIN_INSYNC_REPLICAS: 2
      CLUSTER_ID: "MkU3OEVBNTcwNTJENDM2Qk"
    volumes:
      - broker3-data:/var/lib/kafka/data
    networks:
      - kafka-net

volumes:
  controller1-data:
  controller2-data:
  controller3-data:
  broker1-data:
  broker2-data:
  broker3-data:

networks:
  kafka-net:
    driver: bridge
```

**Verification steps:**

```bash
# Start the cluster
docker compose up -d

# Verify all brokers registered
docker exec broker1 kafka-metadata.sh --snapshot /var/lib/kafka/data/__cluster_metadata-0/00000000000000000000.log --cluster-id MkU3OEVBNTcwNTJENDM2Qk

# Create a test topic
docker exec broker1 kafka-topics.sh --bootstrap-server broker1:9092 \
    --create --topic test-replication \
    --partitions 6 --replication-factor 3

# Describe topic
docker exec broker1 kafka-topics.sh --bootstrap-server broker1:9092 \
    --describe --topic test-replication

# Produce messages
docker exec broker1 bash -c 'seq 1 1000 | kafka-console-producer.sh --bootstrap-server broker1:9092 --topic test-replication'

# Consume messages
docker exec broker1 kafka-console-consumer.sh --bootstrap-server broker1:9092 \
    --topic test-replication --from-beginning --max-messages 10

# Test fault tolerance: stop a broker
docker stop broker2

# Verify topic still works (under-replicated but functional)
docker exec broker1 kafka-topics.sh --bootstrap-server broker1:9092 \
    --describe --topic test-replication --under-replicated-partitions
```

---

### Lab 2: CDC Pipeline (PostgreSQL → Debezium → Kafka → Elasticsearch)

**Objective:** Build a real-time change data capture pipeline.

**Additional services for docker-compose.yml:**

```yaml
  postgres:
    image: postgres:16
    container_name: postgres
    environment:
      POSTGRES_USER: cdc_user
      POSTGRES_PASSWORD: "${POSTGRES_PASSWORD}"
      POSTGRES_DB: orders_db
    ports:
      - "5432:5432"
    volumes:
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
      - postgres-data:/var/lib/postgresql/data
    command:
      - "postgres"
      - "-c"
      - "wal_level=logical"
      - "-c"
      - "max_wal_senders=4"
      - "-c"
      - "max_replication_slots=4"
    networks:
      - kafka-net

  schema-registry:
    image: confluentinc/cp-schema-registry:7.6.0
    container_name: schema-registry
    depends_on:
      - broker1
    ports:
      - "8081:8081"
    environment:
      SCHEMA_REGISTRY_HOST_NAME: schema-registry
      SCHEMA_REGISTRY_KAFKASTORE_BOOTSTRAP_SERVERS: broker1:9092,broker2:9092,broker3:9092
      SCHEMA_REGISTRY_LISTENERS: http://0.0.0.0:8081
    networks:
      - kafka-net

  connect:
    image: confluentinc/cp-kafka-connect:7.6.0
    container_name: connect
    depends_on:
      - broker1
      - schema-registry
    ports:
      - "8083:8083"
    environment:
      CONNECT_BOOTSTRAP_SERVERS: broker1:9092,broker2:9092,broker3:9092
      CONNECT_REST_PORT: 8083
      CONNECT_GROUP_ID: connect-cluster
      CONNECT_CONFIG_STORAGE_TOPIC: _connect-configs
      CONNECT_OFFSET_STORAGE_TOPIC: _connect-offsets
      CONNECT_STATUS_STORAGE_TOPIC: _connect-status
      CONNECT_KEY_CONVERTER: io.confluent.connect.avro.AvroConverter
      CONNECT_VALUE_CONVERTER: io.confluent.connect.avro.AvroConverter
      CONNECT_KEY_CONVERTER_SCHEMA_REGISTRY_URL: http://schema-registry:8081
      CONNECT_VALUE_CONVERTER_SCHEMA_REGISTRY_URL: http://schema-registry:8081
      CONNECT_CONFIG_STORAGE_REPLICATION_FACTOR: 3
      CONNECT_OFFSET_STORAGE_REPLICATION_FACTOR: 3
      CONNECT_STATUS_STORAGE_REPLICATION_FACTOR: 3
      CONNECT_PLUGIN_PATH: /usr/share/java,/usr/share/confluent-hub-components
    command:
      - bash
      - -c
      - |
        confluent-hub install --no-prompt debezium/debezium-connector-postgresql:2.5.0
        confluent-hub install --no-prompt confluentinc/kafka-connect-elasticsearch:14.0.0
        /etc/confluent/docker/run
    networks:
      - kafka-net

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    container_name: elasticsearch
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
      ES_JAVA_OPTS: "-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - es-data:/usr/share/elasticsearch/data
    networks:
      - kafka-net
```

**init.sql:**

```sql
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    product_sku VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    tier VARCHAR(20) DEFAULT 'STANDARD',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create publication for Debezium
CREATE PUBLICATION dbz_publication FOR TABLE orders, customers;
```

**Deploy Debezium source connector:**

```bash
curl -X POST http://localhost:8083/connectors -H "Content-Type: application/json" -d '{
    "name": "postgres-cdc-source",
    "config": {
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "database.hostname": "postgres",
        "database.port": "5432",
        "database.user": "cdc_user",
        "database.password": "'"${POSTGRES_PASSWORD}"'",
        "database.dbname": "orders_db",
        "topic.prefix": "cdc",
        "table.include.list": "public.orders,public.customers",
        "plugin.name": "pgoutput",
        "slot.name": "debezium_slot",
        "publication.name": "dbz_publication",
        "snapshot.mode": "initial",
        "key.converter": "io.confluent.connect.avro.AvroConverter",
        "key.converter.schema.registry.url": "http://schema-registry:8081",
        "value.converter": "io.confluent.connect.avro.AvroConverter",
        "value.converter.schema.registry.url": "http://schema-registry:8081",
        "transforms": "unwrap",
        "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
        "transforms.unwrap.drop.tombstones": "false",
        "transforms.unwrap.delete.handling.mode": "rewrite"
    }
}'
```

**Deploy Elasticsearch sink connector:**

```bash
curl -X POST http://localhost:8083/connectors -H "Content-Type: application/json" -d '{
    "name": "elasticsearch-sink",
    "config": {
        "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
        "topics": "cdc.public.orders,cdc.public.customers",
        "connection.url": "http://elasticsearch:9200",
        "type.name": "_doc",
        "key.ignore": "false",
        "schema.ignore": "false",
        "behavior.on.null.values": "delete",
        "write.method": "upsert",
        "batch.size": 500,
        "flush.timeout.ms": 10000,
        "key.converter": "io.confluent.connect.avro.AvroConverter",
        "key.converter.schema.registry.url": "http://schema-registry:8081",
        "value.converter": "io.confluent.connect.avro.AvroConverter",
        "value.converter.schema.registry.url": "http://schema-registry:8081",
        "transforms": "extractKey,topicRoute",
        "transforms.extractKey.type": "org.apache.kafka.connect.transforms.ExtractField$Key",
        "transforms.extractKey.field": "order_id",
        "transforms.topicRoute.type": "org.apache.kafka.connect.transforms.RegexRouter",
        "transforms.topicRoute.regex": "cdc\\.public\\.(.*)",
        "transforms.topicRoute.replacement": "$1",
        "errors.tolerance": "all",
        "errors.deadletterqueue.topic.name": "dlq-es-sink",
        "errors.deadletterqueue.topic.replication.factor": 3,
        "errors.deadletterqueue.context.headers.enable": true
    }
}'
```

**Verification:**

```bash
# Insert test data
docker exec postgres psql -U cdc_user -d orders_db -c "
INSERT INTO customers (customer_id, name, email, tier) VALUES
    ('cust-001', 'Alice Smith', 'alice@example.com', 'PREMIUM'),
    ('cust-002', 'Bob Jones', 'bob@example.com', 'STANDARD');

INSERT INTO orders (customer_id, product_sku, quantity, total_amount, status) VALUES
    ('cust-001', 'SKU-A100', 2, 59.98, 'PENDING'),
    ('cust-002', 'SKU-B200', 1, 29.99, 'CONFIRMED');
"

# Wait a few seconds for CDC propagation, then query Elasticsearch
curl -s http://localhost:9200/orders/_search?pretty | jq '.hits.hits[]._source'

# Update a record and verify real-time sync
docker exec postgres psql -U cdc_user -d orders_db -c "
UPDATE orders SET status = 'SHIPPED', updated_at = NOW() WHERE order_id = 1;
"

# Verify update in Elasticsearch
curl -s http://localhost:9200/orders/_doc/1?pretty
```

---

### Lab 3: Exactly-Once Stream Processing

**Objective:** Implement a Kafka Streams application with exactly-once semantics.

**Kotlin implementation:**

```kotlin
// build.gradle.kts
// dependencies {
//     implementation("org.apache.kafka:kafka-streams:3.7.0")
//     implementation("org.apache.kafka:kafka-clients:3.7.0")
// }

import org.apache.kafka.streams.StreamsBuilder
import org.apache.kafka.streams.StreamsConfig
import org.apache.kafka.streams.KafkaStreams
import org.apache.kafka.streams.kstream.*
import org.apache.kafka.common.serialization.Serdes
import java.time.Duration
import java.util.Properties

data class OrderEvent(
    val orderId: String,
    val customerId: String,
    val amount: Double,
    val currency: String,
    val timestamp: Long
)

data class CustomerStats(
    val customerId: String,
    val totalOrders: Long = 0,
    val totalAmount: Double = 0.0,
    val avgOrderValue: Double = 0.0,
    val lastOrderTimestamp: Long = 0
) {
    fun addOrder(amount: Double, timestamp: Long): CustomerStats {
        val newTotal = totalOrders + 1
        val newAmount = totalAmount + amount
        return CustomerStats(
            customerId = customerId,
            totalOrders = newTotal,
            totalAmount = newAmount,
            avgOrderValue = newAmount / newTotal,
            lastOrderTimestamp = maxOf(lastOrderTimestamp, timestamp)
        )
    }
}

fun main() {
    val props = Properties().apply {
        put(StreamsConfig.APPLICATION_ID_CONFIG, "order-stats-processor")
        put(StreamsConfig.BOOTSTRAP_SERVERS_CONFIG, "broker1:9092,broker2:9092,broker3:9092")
        put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2)
        put(StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG, Serdes.StringSerde::class.java)
        put(StreamsConfig.DEFAULT_VALUE_SERDE_CLASS_CONFIG, Serdes.StringSerde::class.java)
        put(StreamsConfig.NUM_STREAM_THREADS_CONFIG, 4)
        put(StreamsConfig.STATE_DIR_CONFIG, "/var/lib/kafka-streams")
        put(StreamsConfig.COMMIT_INTERVAL_MS_CONFIG, 100)
        put(StreamsConfig.CACHE_MAX_BYTES_BUFFERING_CONFIG, 10 * 1024 * 1024)
    }

    val builder = StreamsBuilder()

    // Input stream of order events
    val orders: KStream<String, String> = builder.stream("orders")

    // Parse and re-key by customer_id
    val ordersByCustomer: KStream<String, OrderEvent> = orders
        .mapValues { value -> parseOrderEvent(value) }
        .selectKey { _, order -> order.customerId }

    // Aggregate to customer stats (exactly-once guaranteed)
    val customerStats: KTable<String, CustomerStats> = ordersByCustomer
        .groupByKey(Grouped.with(Serdes.String(), orderEventSerde()))
        .aggregate(
            { CustomerStats(customerId = "") },
            { customerId, order, stats ->
                stats.copy(customerId = customerId).addOrder(order.amount, order.timestamp)
            },
            Materialized.`as`<String, CustomerStats, KeyValueStore<Bytes, ByteArray>>("customer-stats-store")
                .withKeySerde(Serdes.String())
                .withValueSerde(customerStatsSerde())
        )

    // Windowed aggregation: hourly revenue per currency
    val hourlyRevenue: KTable<Windowed<String>, Double> = ordersByCustomer
        .map { _, order -> KeyValue(order.currency, order.amount) }
        .groupByKey(Grouped.with(Serdes.String(), Serdes.Double()))
        .windowedBy(TimeWindows.ofSizeWithNoGrace(Duration.ofHours(1)))
        .reduce(Double::plus, Materialized.`as`("hourly-revenue-store"))

    // Output enriched stats to a sink topic
    customerStats.toStream()
        .mapValues { stats -> serializeCustomerStats(stats) }
        .to("customer-stats", Produced.with(Serdes.String(), Serdes.String()))

    // Build and start
    val topology = builder.build(props)
    println(topology.describe())

    val streams = KafkaStreams(topology, props)

    // Graceful shutdown
    Runtime.getRuntime().addShutdownHook(Thread {
        streams.close(Duration.ofSeconds(30))
    })

    streams.start()
}
```

**Python exactly-once consumer-producer pattern:**

```python
from confluent_kafka import Consumer, Producer, TopicPartition, KafkaError
import json

consumer = Consumer({
    "bootstrap.servers": "broker1:9092,broker2:9092,broker3:9092",
    "group.id": "eos-processor",
    "enable.auto.commit": False,
    "isolation.level": "read_committed",
    "auto.offset.reset": "earliest",
})

producer = Producer({
    "bootstrap.servers": "broker1:9092,broker2:9092,broker3:9092",
    "transactional.id": "eos-processor-txn-1",
    "enable.idempotence": True,
    "acks": "all",
})

producer.init_transactions()
consumer.subscribe(["raw-orders"])

try:
    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            raise Exception(f"Consumer error: {msg.error()}")

        # Process the message
        order = json.loads(msg.value().decode("utf-8"))
        enriched_order = enrich_order(order)
        stats_update = compute_stats(order)

        # Atomic transaction: produce outputs + commit input offset
        producer.begin_transaction()
        try:
            producer.produce(
                "enriched-orders",
                key=order["customer_id"].encode("utf-8"),
                value=json.dumps(enriched_order).encode("utf-8"),
            )
            producer.produce(
                "order-stats",
                key=order["customer_id"].encode("utf-8"),
                value=json.dumps(stats_update).encode("utf-8"),
            )

            # Commit consumer offset within the transaction
            producer.send_offsets_to_transaction(
                [TopicPartition(msg.topic(), msg.partition(), msg.offset() + 1)],
                consumer.consumer_group_metadata(),
            )

            producer.commit_transaction()
        except Exception:
            producer.abort_transaction()
            raise

finally:
    consumer.close()
```

---

### Lab 4: Full Security Configuration (mTLS + SCRAM + ACLs)

**Objective:** Configure a secured Kafka cluster with mutual TLS, SCRAM authentication, and fine-grained ACLs.

**Step 1: Generate certificates**

```bash
#!/bin/bash
set -euo pipefail

VALIDITY=365
CA_PASSWORD="${CA_PASSWORD:?Set CA_PASSWORD env var}"
KEYSTORE_PASSWORD="${KEYSTORE_PASSWORD:?Set KEYSTORE_PASSWORD env var}"

mkdir -p certs

# Generate CA
openssl req -new -x509 -keyout certs/ca-key.pem -out certs/ca-cert.pem \
    -days $VALIDITY -passout pass:"$CA_PASSWORD" \
    -subj "/CN=KafkaCA/O=Lab/C=US"

# Function to generate broker/client keystores
generate_keystore() {
    local NAME=$1
    local CN=$2
    local SAN=$3

    # Generate keystore with key pair
    keytool -genkeypair -alias $NAME -keyalg RSA -keysize 2048 \
        -keystore certs/$NAME.keystore.jks \
        -storepass "$KEYSTORE_PASSWORD" -keypass "$KEYSTORE_PASSWORD" \
        -dname "CN=$CN,O=Lab,C=US" \
        -ext SAN=$SAN -validity $VALIDITY

    # Generate CSR
    keytool -certreq -alias $NAME \
        -keystore certs/$NAME.keystore.jks \
        -storepass "$KEYSTORE_PASSWORD" \
        -file certs/$NAME.csr \
        -ext SAN=$SAN

    # Sign with CA
    openssl x509 -req -CA certs/ca-cert.pem -CAkey certs/ca-key.pem \
        -in certs/$NAME.csr -out certs/$NAME-signed.pem \
        -days $VALIDITY -CAcreateserial -passin pass:"$CA_PASSWORD" \
        -extfile <(printf "subjectAltName=$SAN")

    # Import CA and signed cert into keystore
    keytool -importcert -alias ca-root -file certs/ca-cert.pem \
        -keystore certs/$NAME.keystore.jks \
        -storepass "$KEYSTORE_PASSWORD" -noprompt
    keytool -importcert -alias $NAME -file certs/$NAME-signed.pem \
        -keystore certs/$NAME.keystore.jks \
        -storepass "$KEYSTORE_PASSWORD" -noprompt
}

# Generate truststore (shared)
keytool -importcert -alias ca-root -file certs/ca-cert.pem \
    -keystore certs/kafka.truststore.jks \
    -storepass "$KEYSTORE_PASSWORD" -noprompt

# Generate broker keystores
generate_keystore "broker1" "broker1" "DNS:broker1,DNS:localhost,IP:127.0.0.1"
generate_keystore "broker2" "broker2" "DNS:broker2,DNS:localhost,IP:127.0.0.1"
generate_keystore "broker3" "broker3" "DNS:broker3,DNS:localhost,IP:127.0.0.1"

# Generate client keystores
generate_keystore "producer-app" "producer-app" "DNS:producer-app"
generate_keystore "consumer-app" "consumer-app" "DNS:consumer-app"
generate_keystore "admin" "admin" "DNS:admin"
```

**Step 2: Broker security configuration**

```properties
# server.properties for broker1 (adapt node.id and keystore for others)

# Listeners
listeners=SASL_SSL://0.0.0.0:9093,REPLICATION://0.0.0.0:9094
advertised.listeners=SASL_SSL://broker1:9093,REPLICATION://broker1:9094
listener.security.protocol.map=SASL_SSL:SASL_SSL,REPLICATION:SSL
inter.broker.listener.name=REPLICATION

# TLS
ssl.keystore.location=/etc/kafka/ssl/broker1.keystore.jks
ssl.keystore.password=${KEYSTORE_PASSWORD}
ssl.key.password=${KEYSTORE_PASSWORD}
ssl.truststore.location=/etc/kafka/ssl/kafka.truststore.jks
ssl.truststore.password=${KEYSTORE_PASSWORD}
ssl.client.auth=required
ssl.endpoint.identification.algorithm=https

# SASL (client-facing listener)
listener.name.sasl_ssl.sasl.enabled.mechanisms=SCRAM-SHA-512
sasl.mechanism.inter.broker.protocol=NONE

# ACL authorizer
authorizer.class.name=org.apache.kafka.metadata.authorizer.StandardAuthorizer
allow.everyone.if.no.acl.found=false
super.users=User:admin;User:broker1;User:broker2;User:broker3
```

**Step 3: Create SCRAM users**

```bash
# Create admin user
kafka-configs.sh --bootstrap-server broker1:9093 \
    --command-config /etc/kafka/admin.properties \
    --alter --add-config 'SCRAM-SHA-512=[password='"${ADMIN_PASSWORD}"']' \
    --entity-type users --entity-name admin

# Create application users
kafka-configs.sh --bootstrap-server broker1:9093 \
    --command-config /etc/kafka/admin.properties \
    --alter --add-config 'SCRAM-SHA-512=[password='"${PRODUCER_PASSWORD}"']' \
    --entity-type users --entity-name order-producer

kafka-configs.sh --bootstrap-server broker1:9093 \
    --command-config /etc/kafka/admin.properties \
    --alter --add-config 'SCRAM-SHA-512=[password='"${CONSUMER_PASSWORD}"']' \
    --entity-type users --entity-name order-consumer
```

**Step 4: Configure ACLs**

```bash
# Producer: write to orders topic
kafka-acls.sh --bootstrap-server broker1:9093 \
    --command-config /etc/kafka/admin.properties \
    --add --allow-principal User:order-producer \
    --operation Write --operation Describe --operation Create \
    --topic orders

# Producer: write to transactional ID
kafka-acls.sh --bootstrap-server broker1:9093 \
    --command-config /etc/kafka/admin.properties \
    --add --allow-principal User:order-producer \
    --operation Write --operation Describe \
    --transactional-id order-producer-txn

# Consumer: read from orders topic
kafka-acls.sh --bootstrap-server broker1:9093 \
    --command-config /etc/kafka/admin.properties \
    --add --allow-principal User:order-consumer \
    --operation Read --operation Describe \
    --topic orders

# Consumer: manage consumer group
kafka-acls.sh --bootstrap-server broker1:9093 \
    --command-config /etc/kafka/admin.properties \
    --add --allow-principal User:order-consumer \
    --operation Read --operation Describe \
    --group order-processing-group

# Verify ACLs
kafka-acls.sh --bootstrap-server broker1:9093 \
    --command-config /etc/kafka/admin.properties --list
```

**Step 5: Client configuration**

```properties
# producer.properties
bootstrap.servers=broker1:9093
security.protocol=SASL_SSL
sasl.mechanism=SCRAM-SHA-512
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required \
    username="order-producer" \
    password="${PRODUCER_PASSWORD}";
ssl.truststore.location=/etc/kafka/ssl/kafka.truststore.jks
ssl.truststore.password=${KEYSTORE_PASSWORD}
ssl.keystore.location=/etc/kafka/ssl/producer-app.keystore.jks
ssl.keystore.password=${KEYSTORE_PASSWORD}
ssl.key.password=${KEYSTORE_PASSWORD}
ssl.endpoint.identification.algorithm=https
```

**Python secured client:**

```python
from confluent_kafka import Producer
import os

producer = Producer({
    "bootstrap.servers": "broker1:9093",
    "security.protocol": "SASL_SSL",
    "sasl.mechanism": "SCRAM-SHA-512",
    "sasl.username": "order-producer",
    "sasl.password": os.environ["PRODUCER_PASSWORD"],
    "ssl.ca.location": "/etc/kafka/ssl/ca-cert.pem",
    "ssl.certificate.location": "/etc/kafka/ssl/producer-app-signed.pem",
    "ssl.key.location": "/etc/kafka/ssl/producer-app-key.pem",
    "ssl.key.password": os.environ["KEYSTORE_PASSWORD"],
    "ssl.endpoint.identification.algorithm": "https",
    "enable.idempotence": True,
    "acks": "all",
})

producer.produce("orders", key=b"order-1", value=b'{"item": "widget", "qty": 5}')
producer.flush()
```

---

### Lab 5: Performance Benchmark and Tuning

**Objective:** Establish baseline performance, identify bottlenecks, and apply optimizations.

**Step 1: Baseline benchmark**

```bash
# Create benchmark topic
kafka-topics.sh --bootstrap-server broker1:9092 \
    --create --topic perf-baseline \
    --partitions 12 --replication-factor 3 \
    --config min.insync.replicas=2

# Producer baseline (1 KB messages, max throughput)
kafka-producer-perf-test.sh \
    --topic perf-baseline \
    --num-records 5000000 \
    --record-size 1024 \
    --throughput -1 \
    --producer-props \
        bootstrap.servers=broker1:9092,broker2:9092,broker3:9092 \
        acks=all \
        batch.size=16384 \
        linger.ms=0

# Consumer baseline
kafka-consumer-perf-test.sh \
    --bootstrap-server broker1:9092,broker2:9092,broker3:9092 \
    --topic perf-baseline \
    --messages 5000000 \
    --threads 1
```

**Step 2: Optimized producer benchmark**

```bash
# Optimized producer (larger batches, compression, linger)
kafka-producer-perf-test.sh \
    --topic perf-baseline \
    --num-records 5000000 \
    --record-size 1024 \
    --throughput -1 \
    --producer-props \
        bootstrap.servers=broker1:9092,broker2:9092,broker3:9092 \
        acks=all \
        batch.size=131072 \
        linger.ms=50 \
        compression.type=lz4 \
        buffer.memory=134217728 \
        max.in.flight.requests.per.connection=5 \
        enable.idempotence=true
```

**Step 3: Measure the impact**

```bash
# Compare results
echo "=== Baseline vs Optimized Producer ==="
echo "Expected improvement: 2-5x throughput, slightly higher avg latency"
echo "Expected: lower p99 latency due to fewer small requests"

# End-to-end latency test
kafka-e2e-latency.sh broker1:9092 perf-latency 10000 all 1024
```

**Step 4: OS tuning verification**

```bash
# Check current limits
ulimit -n           # File descriptors
cat /proc/sys/vm/swappiness
cat /proc/sys/net/core/rmem_max
cat /proc/sys/net/core/wmem_max
df -T /var/kafka-logs  # Filesystem type

# Verify page cache utilization
vmstat 1 5   # Check buffer/cache columns
iostat -x 1 5  # Check await and %util for kafka disks
```

**Step 5: Partition count experiment**

```bash
# Test with different partition counts
for PARTITIONS in 3 6 12 24 48; do
    kafka-topics.sh --bootstrap-server broker1:9092 \
        --create --topic "perf-p${PARTITIONS}" \
        --partitions $PARTITIONS --replication-factor 3

    echo "=== $PARTITIONS partitions ==="
    kafka-producer-perf-test.sh \
        --topic "perf-p${PARTITIONS}" \
        --num-records 2000000 \
        --record-size 1024 \
        --throughput -1 \
        --producer-props \
            bootstrap.servers=broker1:9092,broker2:9092,broker3:9092 \
            acks=all \
            compression.type=lz4 \
            batch.size=131072 \
            linger.ms=50
done
```

**Step 6: Monitoring during benchmark**

```bash
# Watch under-replicated partitions (should stay 0)
watch -n 2 "kafka-topics.sh --bootstrap-server broker1:9092 \
    --describe --under-replicated-partitions"

# JMX query for request latency (requires JMX exporter or JConsole)
# Key metrics to observe:
# - kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec
# - kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec
# - kafka.network:type=RequestMetrics,name=TotalTimeMs,request=Produce (p99)
# - kafka.network:type=RequestMetrics,name=TotalTimeMs,request=FetchConsumer (p99)
# - kafka.server:type=KafkaRequestHandlerPool,name=RequestHandlerAvgIdlePercent (should be > 0.3)
```

**Expected results summary:**

| Configuration | Throughput (MB/s) | Avg Latency | p99 Latency |
|---------------|-------------------|-------------|-------------|
| Baseline (no batching, no compression) | ~50-100 | ~5ms | ~50ms |
| Optimized (lz4, batch 128KB, linger 50ms) | ~200-500 | ~60ms | ~100ms |
| Max throughput (12+ partitions, multi-producer) | ~500-1000 | ~80ms | ~150ms |

Actual numbers depend heavily on hardware (NVMe vs HDD, network bandwidth, CPU cores).

---

## Summary

This guide covered Apache Kafka from architectural fundamentals through production operations:

- **Architecture**: The shift from ZooKeeper to KRaft simplifies deployment and increases metadata scalability. Understanding partitions, replication, ISR mechanics, and log compaction is foundational to all Kafka operations.

- **Producers and Consumers**: Idempotent and transactional producers combined with `read_committed` consumers provide exactly-once semantics. Proper batching, compression, and offset management are critical to both correctness and performance.

- **Kafka Streams**: Stream/table duality, windowed aggregations, and state stores (backed by RocksDB with changelog topics) enable stateful stream processing with exactly-once guarantees and interactive queries.

- **Kafka Connect**: The connector ecosystem (particularly Debezium for CDC) enables integration with external systems without custom code. SMTs, dead letter queues, and distributed mode provide production resilience.

- **Schema Management**: Schema Registry with compatibility modes prevents breaking changes in a decoupled producer/consumer environment. Avro provides the best backward/forward compatibility story.

- **Performance**: Kafka's performance depends on OS-level tuning (page cache, network buffers, XFS), proper partition counts, and matching producer/consumer configurations to workload characteristics.

- **Security**: Defense in depth via SASL authentication, mutual TLS, fine-grained ACLs, and audit logging. Never deploy Kafka without authentication and encryption in production.

- **Operations**: Multi-cluster replication (MM2 or Cluster Linking), comprehensive monitoring via JMX/Prometheus, rolling upgrades, and tiered storage for cost-effective long-term retention.
