# Redis: Streaming e Pub/Sub

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Skip list
- [x] Bozza iniziale
- [x] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Pub/Sub Basics
2. Pub/Sub Patterns and Advanced Usage
3. Sharded Pub/Sub (Redis 7+)
4. Redis Streams Fundamentals
5. Stream Commands Deep Dive
6. Consumer Groups
7. Stream Trimming and Retention
8. Architecture Patterns
9. Monitoring and Observability
10. Performance Tuning
11. Operational Procedures
12. Real-World Patterns
13. Troubleshooting
14. FAQ

---

## 1. Pub/Sub Basics

### 1.1 How Pub/Sub Works

Redis Pub/Sub implements a fire-and-forget messaging model. Publishers send messages to channels without knowing which subscribers will receive them. Subscribers express interest in one or more channels and receive messages in real time. Messages are never persisted -- if a subscriber is disconnected at the time a message is published, that message is lost.

The Pub/Sub subsystem operates outside the keyspace. Channel names are not Redis keys, they do not consume keyspace memory, and they are not affected by `FLUSHDB` or `FLUSHALL`.

```bash
# Subscribe to a single channel
SUBSCRIBE channel_name

# Subscribe to multiple channels
SUBSCRIBE news sports weather

# Pattern subscribe (glob-style)
PSUBSCRIBE news.*
PSUBSCRIBE user:*:notifications

# Publish a message
PUBLISH channel_name "message payload"

# Unsubscribe
UNSUBSCRIBE channel_name
PUNSUBSCRIBE news.*
```

### 1.2 Message Flow Internals

When a client issues `SUBSCRIBE`, Redis adds that connection to a dictionary keyed by channel name. On `PUBLISH`, Redis looks up all connections in that dictionary and writes the message to each client output buffer. The cost of `PUBLISH` is O(N+M) where N is the number of subscribed clients and M is the number of pattern subscriptions.

```bash
# Check how many subscribers a channel has
PUBSUB NUMSUB channel_name

# List all active channels (with at least one subscriber)
PUBSUB CHANNELS

# List channels matching a pattern
PUBSUB CHANNELS news.*

# Count pattern subscriptions across all clients
PUBSUB NUMPAT
```

### 1.3 Python Pub/Sub Example

```python
import redis
import threading

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# --- Subscriber (runs in a thread or separate process) ---
def subscriber():
    pubsub = r.pubsub()
    pubsub.subscribe('notifications')
    pubsub.psubscribe('user:*:events')

    for message in pubsub.listen():
        if message['type'] in ('message', 'pmessage'):
            print(f"Channel: {message['channel']}, Data: {message['data']}")

thread = threading.Thread(target=subscriber, daemon=True)
thread.start()

# --- Publisher ---
r.publish('notifications', 'Server maintenance at 03:00 UTC')
r.publish('user:42:events', 'New login from 192.168.1.5')
```

### 1.4 Pub/Sub Limitations

| Limitation | Detail |
|---|---|
| No persistence | Messages not stored; offline subscribers miss them |
| No acknowledgment | No confirmation that a subscriber received the message |
| No replay | Cannot re-read old messages |
| At-most-once delivery | A message is delivered zero or one times per subscriber |
| Client buffer pressure | Slow subscribers accumulate backlog in output buffer |
| No consumer groups | Cannot load-balance across multiple consumers of the same channel |

These limitations make Pub/Sub suitable for real-time notifications, live dashboards, and invalidation signals, but not for reliable message queuing. For reliable delivery, use Redis Streams (section 4+).

---

## 2. Pub/Sub Patterns and Advanced Usage

### 2.1 Pattern Subscriptions

Pattern subscriptions use glob-style matching. Each incoming message is tested against all registered patterns, making pattern count a performance factor.

```bash
# Subscribe to all channels starting with "sensor:"
PSUBSCRIBE sensor:*

# Subscribe to channels matching two-level hierarchy
PSUBSCRIBE app:*.error

# A message published to "sensor:temperature:room1" matches "sensor:*"
PUBLISH sensor:temperature:room1 '{"celsius": 22.5}'
```

A single message can trigger both a direct channel subscription and a pattern subscription on the same client. If a client has `SUBSCRIBE sensor:temp` and `PSUBSCRIBE sensor:*`, publishing to `sensor:temp` delivers the message twice.

### 2.2 Cache Invalidation Pattern

A common Pub/Sub use case is broadcasting cache invalidation across application nodes:

```python
# Invalidation publisher (runs after DB write)
def invalidate_cache(entity_type, entity_id):
    channel = f"invalidate:{entity_type}"
    r.publish(channel, str(entity_id))

# Invalidation subscriber (runs in each app instance)
def cache_invalidation_listener(local_cache):
    pubsub = r.pubsub()
    pubsub.psubscribe('invalidate:*')

    for message in pubsub.listen():
        if message['type'] == 'pmessage':
            entity_type = message['channel'].split(':')[1]
            entity_id = message['data']
            local_cache.pop(f"{entity_type}:{entity_id}", None)
```

### 2.3 Configuration for Pub/Sub Clients

```bash
# redis.conf -- control output buffer limits for pub/sub clients
# Syntax: client-output-buffer-limit <class> <hard> <soft> <seconds>
# Disconnect if buffer exceeds 32MB, or stays above 8MB for 60 seconds
client-output-buffer-limit pubsub 32mb 8mb 60

# For slave/replica output buffers
client-output-buffer-limit replica 256mb 64mb 60
```

---

## 3. Sharded Pub/Sub (Redis 7+)

### 3.1 The Problem with Classic Pub/Sub in Cluster Mode

In Redis Cluster with classic Pub/Sub, every `PUBLISH` command broadcasts the message to every node in the cluster, regardless of which nodes have subscribers. This creates O(N) inter-node traffic where N is the cluster size, wasting bandwidth on nodes with zero subscribers for that channel.

### 3.2 How Sharded Pub/Sub Works

Redis 7.0 introduced sharded Pub/Sub. Channels are mapped to hash slots (the same 16384-slot ring used for keys), so messages are only forwarded to the node that owns the slot for that channel. Subscribers connect to the correct node automatically when using cluster-aware clients.

```bash
# Sharded subscribe (channel mapped to a hash slot)
SSUBSCRIBE orders.region.eu

# Sharded publish (routed to the slot-owning node only)
SPUBLISH orders.region.eu '{"order_id": 9001}'

# Sharded unsubscribe
SUNSUBSCRIBE orders.region.eu

# Check sharded channel subscribers
PUBSUB SHARDCHANNELS
PUBSUB SHARDNUMSUB orders.region.eu
```

### 3.3 When to Use Sharded vs. Classic Pub/Sub

| Criteria | Classic Pub/Sub | Sharded Pub/Sub |
|---|---|---|
| Cluster mode | Broadcasts to all nodes | Routes to slot-owning node |
| Pattern subscriptions | Supported | Not supported |
| Scalability | Degrades with cluster size | Scales linearly |
| Use case | Global notifications | Per-entity events |

### 3.4 Configuration for Sharded Pub/Sub

No special configuration is required. Sharded Pub/Sub is available automatically in Redis 7.0+ cluster mode. Clients must use `SSUBSCRIBE`/`SPUBLISH` commands explicitly; the classic `SUBSCRIBE`/`PUBLISH` still works the old way.

```python
# Python example with redis-py 5.x cluster client
from redis.cluster import RedisCluster

rc = RedisCluster(host='redis-node-1', port=6379)

# Sharded publish
rc.spublish('user:1001:events', 'profile_updated')

# Sharded subscribe (in subscriber process)
pubsub = rc.pubsub()
pubsub.ssubscribe('user:1001:events')
for msg in pubsub.listen():
    print(msg)
```

---

## 4. Redis Streams Fundamentals

### 4.1 What Are Redis Streams

Redis Streams are an append-only log data structure introduced in Redis 5.0 and significantly enhanced in Redis 7.x. They combine the best of Pub/Sub (real-time push) and Lists (persistence) with unique features:

- **Persistent**: messages survive restarts (unlike Pub/Sub)
- **Consumer groups**: load-balance processing across multiple consumers
- **Acknowledgment**: track which messages have been successfully processed
- **Replay**: read historical messages from any point
- **ID-based ordering**: each entry has a time-based unique ID

A stream entry is a set of field-value pairs, similar to a Hash. Each entry is identified by an auto-generated ID in the format `<millisecondsTime>-<sequenceNumber>`.

### 4.2 Stream Entry IDs

```bash
# Auto-generated ID (recommended)
XADD mystream * sensor_id 1234 temperature 22.5
# Returns something like: "1684934400000-0"

# Explicit ID (use with caution)
XADD mystream 1684934400000-0 sensor_id 1234 temperature 22.5

# Partial auto-ID: specify milliseconds, auto-increment sequence
XADD mystream 1684934400000-* sensor_id 1234 temperature 22.5
```

The ID encodes the entry's creation timestamp, enabling efficient time-range queries without secondary indexes.

---

## 5. Stream Commands Deep Dive

### 5.1 Writing to Streams

```bash
# Basic add
XADD mystream * field1 value1 field2 value2

# Add with max length cap (approximate trimming for performance)
XADD mystream MAXLEN ~ 1000 * field1 value1

# Add with minimum ID trim (Redis 6.2+)
XADD mystream MINID ~ 1684900000000-0 * field1 value1

# Add with NOMKSTREAM -- do not create stream if it does not exist
XADD mystream NOMKSTREAM * field1 value1
```

### 5.2 Reading from Streams

```bash
# Read all entries
XRANGE mystream - +

# Read with count limit
XRANGE mystream - + COUNT 10

# Reverse range (newest first)
XREVRANGE mystream + - COUNT 10

# Read entries after a specific ID
XRANGE mystream 1684934400000-0 +

# Time-range query (entries from the last hour)
XRANGE mystream 1684930800000 +

# XREAD: blocking read (like BLPOP for streams)
XREAD COUNT 10 BLOCK 5000 STREAMS mystream 0

# XREAD from latest (only new entries)
XREAD COUNT 10 BLOCK 0 STREAMS mystream $

# Read from multiple streams simultaneously
XREAD COUNT 5 BLOCK 2000 STREAMS stream1 stream2 0 0
```

### 5.3 Stream Metadata

```bash
# Stream length
XLEN mystream

# Stream information
XINFO STREAM mystream

# Full stream info including first/last entry
XINFO STREAM mystream FULL

# List consumer groups
XINFO GROUPS mystream

# List consumers in a group
XINFO CONSUMERS mystream mygroup

# Delete specific entries
XDEL mystream 1684934400000-0

# Check if stream exists
EXISTS mystream
TYPE mystream
```

---

## 6. Consumer Groups

### 6.1 Consumer Group Architecture

Consumer groups enable multiple consumers to cooperatively process a stream. Each message is delivered to exactly one consumer within the group (competing consumers pattern). Multiple groups on the same stream each receive all messages independently.

```
Stream: mystream
  ├── Group: analytics  (each msg → one of: consumer-a1, consumer-a2)
  └── Group: archiver   (each msg → one of: consumer-b1, consumer-b2, consumer-b3)
```

### 6.2 Group Lifecycle

```bash
# Create group starting from the beginning of the stream
XGROUP CREATE mystream analytics 0

# Create group starting from current latest (only new messages)
XGROUP CREATE mystream archiver $

# Create group and auto-create the stream if it does not exist
XGROUP CREATE mystream newgroup 0 MKSTREAM

# Delete a group
XGROUP DESTROY mystream analytics

# Set group's last-delivered ID (replay from a specific point)
XGROUP SETID mystream analytics 0

# Delete a specific consumer from a group
XGROUP DELCONSUMER mystream analytics consumer-a1
```

### 6.3 Reading and Acknowledging

```bash
# Read pending messages for this consumer (unacknowledged)
XREADGROUP GROUP analytics consumer-a1 COUNT 10 STREAMS mystream 0

# Read only NEW messages (not yet delivered to any consumer in this group)
XREADGROUP GROUP analytics consumer-a1 COUNT 10 STREAMS mystream >

# Blocking read for new messages
XREADGROUP GROUP analytics consumer-a1 COUNT 10 BLOCK 5000 STREAMS mystream >

# Acknowledge successful processing
XACK mystream analytics 1684934400000-0 1684934400001-0

# Check pending entries list (PEL)
XPENDING mystream analytics
XPENDING mystream analytics - + 10
XPENDING mystream analytics - + 10 consumer-a1
```

### 6.4 Claiming Stale Messages

When a consumer crashes, its pending messages remain unacknowledged. Other consumers can claim them:

```bash
# Claim messages idle for more than 30 seconds
XCLAIM mystream analytics consumer-a2 30000 1684934400000-0

# Auto-claim (Redis 6.2+): automatically find and claim idle messages
XAUTOCLAIM mystream analytics consumer-a2 30000 0-0 COUNT 10
```

### 6.5 Consumer Group Python Example

```python
import redis
import time

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

STREAM = 'events'
GROUP = 'processors'
CONSUMER = 'worker-1'

# Create group (idempotent)
try:
    r.xgroup_create(STREAM, GROUP, id='0', mkstream=True)
except redis.exceptions.ResponseError as e:
    if 'BUSYGROUP' not in str(e):
        raise

# Processing loop
while True:
    # Read new messages
    entries = r.xreadgroup(GROUP, CONSUMER, {STREAM: '>'}, count=10, block=5000)

    if not entries:
        # No new messages; check for stale pending messages to reclaim
        stale = r.xautoclaim(STREAM, GROUP, CONSUMER, min_idle_time=30000, start_id='0-0', count=5)
        if stale and stale[1]:
            entries = [(STREAM, stale[1])]
        else:
            continue

    for stream_name, messages in entries:
        for msg_id, fields in messages:
            try:
                process_event(fields)
                r.xack(STREAM, GROUP, msg_id)
            except Exception as e:
                print(f"Failed to process {msg_id}: {e}")
                # Message stays in PEL for retry or claim
```

---

## 7. Stream Trimming and Retention

### 7.1 Trimming Strategies

Streams grow indefinitely unless trimmed. Redis provides two trimming strategies:

```bash
# MAXLEN: keep at most N entries
XTRIM mystream MAXLEN 10000

# MAXLEN approximate (faster, may keep slightly more)
XTRIM mystream MAXLEN ~ 10000

# MINID: remove entries with IDs lower than the specified ID
XTRIM mystream MINID 1684900000000-0

# MINID approximate
XTRIM mystream MINID ~ 1684900000000-0

# Inline trimming during XADD
XADD mystream MAXLEN ~ 10000 * key value
```

### 7.2 Why Approximate Trimming

Exact trimming (`MAXLEN 10000`) may need to delete many radix-tree nodes. Approximate trimming (`MAXLEN ~ 10000`) only trims whole macro-nodes, making it nearly free in terms of CPU. The stream may temporarily hold slightly more entries than the specified limit.

### 7.3 Retention Automation

```bash
# Cron-based trim (run every hour)
# Keep entries from the last 24 hours
0 * * * * redis-cli XTRIM mystream MINID ~ $(date -d '24 hours ago' +%s)000-0

# Or use MAXLEN to cap at 100k entries
0 * * * * redis-cli XTRIM mystream MAXLEN ~ 100000
```

---

## 8. Architecture Patterns

### 8.1 Event Sourcing with Streams

```
Producers → XADD events * type order_created ...
                ↓
Consumer Group "projections"  →  Build read models (SQL tables)
Consumer Group "notifications" → Send emails/push notifications
Consumer Group "analytics"     → Update real-time dashboards
```

Each group processes the full event log independently, enabling decoupled microservices.

### 8.2 CQRS with Redis Streams

```
Write Side:
  API → Validate → XADD command_stream * ...
                        ↓
  Event Processor (consumer group):
    Read command → Execute business logic → XADD event_stream * ...

Read Side:
  Projector (consumer group on event_stream):
    Read event → Update read model (Redis Hash / SQL)
  Query API reads from read model directly
```

### 8.3 Fan-Out Pattern

Use multiple consumer groups on the same stream to fan-out processing:

```bash
# One stream, multiple independent processing pipelines
XGROUP CREATE user_actions search_indexer $
XGROUP CREATE user_actions fraud_detector $
XGROUP CREATE user_actions analytics_pipeline $
XGROUP CREATE user_actions audit_logger $
```

### 8.4 Dead Letter Queue

```python
MAX_RETRIES = 5

def process_with_dlq(r, stream, group, consumer):
    # Check pending messages with high delivery count
    pending = r.xpending_range(stream, group, min='-', max='+', count=100)

    for entry in pending:
        if entry['times_delivered'] > MAX_RETRIES:
            # Move to dead letter stream
            msg = r.xrange(stream, min=entry['message_id'], max=entry['message_id'])
            if msg:
                r.xadd(f"{stream}:dlq", fields=msg[0][1])
            r.xack(stream, group, entry['message_id'])
            r.xdel(stream, entry['message_id'])
```

### 8.5 Pub/Sub vs. Streams Decision Matrix

| Requirement | Use Pub/Sub | Use Streams |
|---|---|---|
| Fire-and-forget notifications | Yes | Overkill |
| Reliable message delivery | No | Yes |
| Consumer load balancing | No | Yes (consumer groups) |
| Message replay / history | No | Yes |
| Pattern-based subscriptions | Yes | No |
| Cluster-efficient routing | Yes (sharded, 7.0+) | Yes (key-based routing) |
| Low latency broadcast | Yes | Acceptable |
| Complex acknowledgment logic | No | Yes |

---

## 9. Monitoring and Observability

### 9.1 Pub/Sub Monitoring

```bash
# Real-time monitoring of all Pub/Sub activity (debug only, high overhead)
MONITOR

# Count active subscriptions
PUBSUB NUMSUB channel1 channel2

# Count pattern subscriptions
PUBSUB NUMPAT

# List all active channels
PUBSUB CHANNELS *

# Client list filtered by pub/sub subscribers
CLIENT LIST TYPE pubsub
```

### 9.2 Stream Monitoring

```bash
# Stream length (check for unbounded growth)
XLEN mystream

# Full stream info: radix tree stats, first/last entry, recorded first entry
XINFO STREAM mystream FULL

# Consumer group lag (pending entries per group)
XINFO GROUPS mystream

# Per-consumer stats: pending count, idle time
XINFO CONSUMERS mystream mygroup

# Memory usage of a stream
MEMORY USAGE mystream

# Key metrics to alert on
# 1. XLEN growing beyond expected capacity
# 2. PEL size (pending entries) growing -- consumers falling behind
# 3. Consumer idle time exceeding threshold -- consumer may be dead
# 4. entries-read vs entries-added delta per group (lag)
```

### 9.3 INFO Command Sections

```bash
# Overall server stats
INFO stats
# Look for: total_connections_received, pubsub_channels, pubsub_patterns

# Memory stats
INFO memory
# Look for: used_memory, used_memory_dataset (includes stream overhead)

# Client stats
INFO clients
# Look for: connected_clients, blocked_clients (XREAD BLOCK consumers)
```

### 9.4 Prometheus/Grafana Integration

Key metrics to export:

```
redis_stream_length{stream="mystream"}                     # XLEN
redis_stream_groups{stream="mystream"}                     # number of consumer groups
redis_stream_pending_entries{stream="mystream",group="g1"} # PEL size
redis_stream_consumer_idle_ms{stream="mystream",group="g1",consumer="c1"}
redis_pubsub_channels                                      # total active channels
redis_pubsub_patterns                                      # total pattern subscriptions
redis_connected_clients
redis_blocked_clients
```

---

## 10. Performance Tuning

### 10.1 Pub/Sub Performance

```bash
# Increase output buffer for pub/sub clients to handle spikes
client-output-buffer-limit pubsub 64mb 16mb 120

# If subscribers are slow, consider:
# 1. Dedicated Redis instance for Pub/Sub
# 2. Reduce message size (send IDs, not payloads)
# 3. Use sharded Pub/Sub in cluster mode to reduce broadcast overhead
```

### 10.2 Stream Performance

```bash
# Stream entries are stored in radix trees with listpack nodes
# Each listpack node holds ~100 entries by default

# Control listpack size (bytes) -- larger = more memory efficient, smaller = faster access
stream-node-max-bytes 4096

# Control max entries per listpack node
stream-node-max-entries 100

# For high-throughput streams, increase these values:
stream-node-max-bytes 16384
stream-node-max-entries 500
```

### 10.3 XADD Performance Considerations

- `XADD` with `MAXLEN` exact is O(N) for trimmed entries. Use `MAXLEN ~` for O(1) amortized.
- Batch writes with pipelines when producing many entries:

```python
pipe = r.pipeline()
for event in events:
    pipe.xadd('mystream', event, maxlen=100000, approximate=True)
pipe.execute()
```

### 10.4 XREADGROUP Tuning

```bash
# COUNT: fetch more entries per call to reduce round trips
XREADGROUP GROUP g1 c1 COUNT 100 BLOCK 5000 STREAMS mystream >

# BLOCK timeout: balance between latency and CPU usage
# 0 = infinite block (lowest CPU, highest latency for shutdown signals)
# 1000-5000ms = good balance for most workloads
# NOACK: skip PEL tracking for fire-and-forget consumers (faster)
XREADGROUP GROUP g1 c1 COUNT 100 NOACK STREAMS mystream >
```

### 10.5 Memory Optimization for Streams

```bash
# Check memory usage
MEMORY USAGE mystream SAMPLES 0

# Compact streams by trimming processed entries
XTRIM mystream MAXLEN ~ 50000

# Use field name compression: short field names save memory across millions of entries
# BAD:  XADD s * temperature_celsius 22 humidity_percent 45
# GOOD: XADD s * tc 22 hp 45
```

---

## 11. Operational Procedures

### 11.1 Setting Up a Stream Processing Pipeline

```bash
# Step 1: Create the stream (auto-created on first XADD, but explicit is better)
XADD events 0-1 init true
XDEL events 0-1

# Step 2: Create consumer groups
XGROUP CREATE events processors 0 MKSTREAM
XGROUP CREATE events archivers $ MKSTREAM

# Step 3: Verify setup
XINFO STREAM events
XINFO GROUPS events

# Step 4: Start consumer processes (application side)
# Step 5: Publish first test event
XADD events * type test message "pipeline validation"
```

### 11.2 Consumer Failure Recovery

```bash
# 1. Identify dead consumers
XINFO CONSUMERS mystream mygroup
# Look for consumers with high idle time

# 2. Claim their pending messages
XAUTOCLAIM mystream mygroup healthy-consumer 60000 0-0 COUNT 100

# 3. Remove the dead consumer
XGROUP DELCONSUMER mystream mygroup dead-consumer

# 4. Verify PEL is clean
XPENDING mystream mygroup
```

### 11.3 Stream Migration Between Instances

```bash
# Export stream entries from source
redis-cli -h source XRANGE mystream - + > stream_dump.txt

# Replay into target (scripted)
while IFS= read -r line; do
    # Parse and XADD to target
    redis-cli -h target XADD mystream_migrated '*' $line
done < stream_dump.txt

# For large streams, use redis-cli --pipe or DUMP/RESTORE
redis-cli -h source DUMP mystream | redis-cli -h target RESTORE mystream 0 -
```

### 11.4 Graceful Consumer Shutdown

```python
import signal

shutdown_flag = False

def handle_signal(signum, frame):
    global shutdown_flag
    shutdown_flag = True

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT, handle_signal)

while not shutdown_flag:
    entries = r.xreadgroup(GROUP, CONSUMER, {STREAM: '>'}, count=10, block=2000)
    if entries:
        for stream_name, messages in entries:
            for msg_id, fields in messages:
                process_event(fields)
                r.xack(STREAM, GROUP, msg_id)

# On shutdown: pending messages will be reclaimed by other consumers via XAUTOCLAIM
print("Consumer shutting down gracefully")
```

---

## 12. Real-World Patterns

### 12.1 Chat System with Streams

```python
def send_message(room_id, user_id, text):
    r.xadd(f'chat:{room_id}', {
        'user': user_id,
        'text': text,
        'ts': int(time.time() * 1000)
    }, maxlen=10000, approximate=True)

def get_history(room_id, count=50):
    return r.xrevrange(f'chat:{room_id}', '+', '-', count=count)

def listen_new_messages(room_id, last_id='$'):
    while True:
        result = r.xread({f'chat:{room_id}': last_id}, count=10, block=5000)
        if result:
            for stream, messages in result:
                for msg_id, fields in messages:
                    yield msg_id, fields
                    last_id = msg_id
```

### 12.2 IoT Sensor Data Pipeline

```python
# Producer (edge device)
def report_sensor_reading(sensor_id, readings):
    r.xadd('sensors:raw', {
        'sid': sensor_id,
        'temp': readings['temperature'],
        'hum': readings['humidity'],
        'ts': int(time.time() * 1000)
    }, maxlen=1000000, approximate=True)

# Consumer: real-time alerting
def alert_consumer():
    while True:
        entries = r.xreadgroup('alerting', 'alert-worker-1',
                               {'sensors:raw': '>'}, count=50, block=3000)
        if entries:
            for _, messages in entries:
                for msg_id, fields in messages:
                    temp = float(fields['temp'])
                    if temp > 80.0:
                        send_alert(fields['sid'], temp)
                    r.xack('sensors:raw', 'alerting', msg_id)
```

### 12.3 Order Processing Pipeline

```python
# Step 1: Order placed
r.xadd('orders', {'order_id': '9001', 'status': 'created', 'total': '59.99'})

# Step 2: Payment processor (consumer group)
# Reads from 'orders', validates payment, writes to 'orders:paid'
r.xadd('orders:paid', {'order_id': '9001', 'payment_id': 'pay_abc'})

# Step 3: Fulfillment (consumer group on 'orders:paid')
# Reads paid orders, triggers shipping, writes to 'orders:shipped'
r.xadd('orders:shipped', {'order_id': '9001', 'tracking': 'TRACK123'})
```

### 12.4 Activity Feed with Pub/Sub + Stream Hybrid

```python
# Write activity to stream (durable) AND publish notification (real-time)
def record_activity(user_id, action, target):
    entry_id = r.xadd(f'activity:{user_id}', {
        'action': action,
        'target': target,
        'ts': int(time.time())
    }, maxlen=1000, approximate=True)

    # Real-time push to online followers
    r.publish(f'feed:{user_id}', f'{action}:{target}:{entry_id}')

# Online user listens via Pub/Sub for instant updates
# Offline user catches up by reading the stream on next login
```

---

## 13. Troubleshooting

### 13.1 Subscribers Not Receiving Messages

**Symptoms**: `PUBLISH` returns 0 or subscribers see no data.

**Diagnosis**:
```bash
PUBSUB NUMSUB channel_name
CLIENT LIST TYPE pubsub
```

**Common causes**:
- Subscriber connected to wrong Redis node (cluster mode)
- Channel name typo or encoding mismatch
- Subscriber disconnected and reconnected but did not re-subscribe
- Client library auto-reconnect does not restore subscriptions

### 13.2 Stream Consumer Group Lag Growing

**Symptoms**: `XPENDING` shows increasing entries, `XINFO GROUPS` shows growing lag.

**Diagnosis**:
```bash
XPENDING mystream mygroup - + 10
XINFO CONSUMERS mystream mygroup
```

**Resolution**: Scale consumers horizontally, increase `COUNT` per `XREADGROUP`, or trim unneeded old entries.

### 13.3 High Memory Usage from Streams

**Symptoms**: `INFO memory` shows unexpected growth.

**Diagnosis**:
```bash
MEMORY USAGE mystream SAMPLES 0
XLEN mystream
XINFO STREAM mystream
```

**Resolution**: Enable trimming with `MAXLEN ~` or `MINID ~` on `XADD`. Shorten field names. Reduce entry payload size.

### 13.4 XREADGROUP Returns Empty Despite Pending Messages

**Symptoms**: Consumer reads with `>` and gets nothing, but `XPENDING` shows entries.

**Cause**: The `>` special ID means "only new, never-delivered messages." Pending messages were already delivered to this or another consumer.

**Fix**: Read with `0` instead of `>` to retrieve pending messages for this consumer, or use `XAUTOCLAIM`.

### 13.5 Consumer Stuck in BLOCK State

**Symptoms**: Consumer process appears hung.

**Diagnosis**:
```bash
CLIENT LIST
# Look for cmd=xreadgroup with age > expected
```

**Resolution**: Use a finite `BLOCK` timeout (e.g., 5000ms) instead of 0 (infinite). Implement shutdown signal handling.

### 13.6 Pub/Sub Client Disconnected by Output Buffer

**Symptoms**: Client log shows "Client closed connection" or "Output buffer limit exceeded."

**Diagnosis**:
```bash
INFO clients
# Check client_recent_max_output_buffer
```

**Resolution**: Increase `client-output-buffer-limit pubsub`, make subscribers process faster, or reduce message rate.

### 13.7 XADD Failing with NOPERM

**Symptoms**: `XADD` returns permission error.

**Cause**: ACL restricts the user from write commands on the key pattern.

**Fix**:
```bash
ACL SETUSER myuser on >password ~streams:* +xadd +xreadgroup +xack
```

### 13.8 Stream Entry IDs Not Sequential

**Symptoms**: IDs have gaps or unexpected timestamps.

**Cause**: Entries were deleted with `XDEL`, or the system clock shifted. Redis guarantees monotonically increasing IDs but not contiguity.

**Resolution**: Never rely on ID contiguity. Use `XRANGE` with time-based IDs for queries.

### 13.9 Consumer Group Not Created (NOGROUP Error)

**Symptoms**: `XREADGROUP` returns `NOGROUP No such key or consumer group`.

**Cause**: The stream or group does not exist, or was dropped by `FLUSHDB`.

**Fix**:
```bash
XGROUP CREATE mystream mygroup 0 MKSTREAM
```

### 13.10 Messages Delivered Multiple Times

**Symptoms**: The same message is processed more than once.

**Cause**: Consumer processed the message but crashed before `XACK`. On restart or claim, the message is redelivered.

**Resolution**: Make consumers idempotent. Use the message ID as a deduplication key. Check `times_delivered` in `XPENDING` output.

### 13.11 Sharded Pub/Sub Messages Not Arriving (Redis 7+)

**Symptoms**: `SPUBLISH` returns 0 in cluster mode.

**Cause**: Subscriber connected to a different node than the one owning the channel's hash slot.

**Fix**: Use a cluster-aware client that handles redirections automatically. Verify with `CLUSTER KEYSLOT channel_name`.

---

## 14. FAQ

### Q1: Can I use Pub/Sub for reliable message delivery?

No. Pub/Sub is fire-and-forget. If a subscriber is disconnected, messages are lost. Use Redis Streams with consumer groups for at-least-once delivery.

### Q2: What is the maximum number of subscribers per channel?

There is no hard limit. The practical limit is determined by available memory for client output buffers and the CPU cost of iterating subscribers on each `PUBLISH`.

### Q3: Do Streams consume more memory than Lists for the same data?

Yes, slightly more per entry due to radix-tree metadata and entry IDs. However, Streams offer consumer groups, acknowledgment, and time-based queries that Lists do not.

### Q4: Can I use XREAD without consumer groups?

Yes. `XREAD` works standalone for simple tail-following. Consumer groups add load balancing and acknowledgment on top.

### Q5: What happens if all consumers in a group crash?

Pending messages stay in the PEL indefinitely. When consumers restart, they can read their pending messages (using ID `0` instead of `>`) or new consumers can `XCLAIM`/`XAUTOCLAIM` them.

### Q6: How do I replay a stream from the beginning?

```bash
XREADGROUP GROUP mygroup myconsumer COUNT 100 STREAMS mystream 0
```
Or reset the group's last-delivered ID: `XGROUP SETID mystream mygroup 0`.

### Q7: Does XTRIM delete entries immediately?

With exact mode (`MAXLEN 1000`), yes. With approximate mode (`MAXLEN ~ 1000`), Redis trims at the radix-tree macro-node boundary, so slightly more entries may remain temporarily.

### Q8: Can I have multiple consumer groups on the same stream?

Yes. Each group independently tracks its own position and PEL. This is the primary mechanism for fan-out processing.

### Q9: Is there a way to get the total lag of a consumer group?

Redis 7.0 added the `entries-read` field to `XINFO GROUPS`. Lag is calculated as `stream_entries_added - entries_read - pending_count`.

### Q10: How do I migrate from Pub/Sub to Streams?

1. Replace `PUBLISH` with `XADD` (stream name = channel name)
2. Replace `SUBSCRIBE` with `XREADGROUP` in a loop
3. Add `XACK` after successful processing
4. Set up trimming to manage retention
5. Test idempotency in consumers

### Q11: What is the performance difference between PUBLISH and XADD?

`PUBLISH` is slightly faster because it does no persistence and no ID generation. `XADD` persists to the AOF/RDB and generates a unique ID. For most workloads, the difference is negligible (both handle 100k+ ops/sec).

### Q12: Can sharded Pub/Sub use pattern subscriptions?

No. `SPSUBSCRIBE` does not exist. Sharded Pub/Sub only supports exact channel names via `SSUBSCRIBE`. If you need pattern subscriptions in cluster mode, use classic `PSUBSCRIBE` (with the broadcast cost trade-off).

---

*Questo documento fa parte del modulo 06 "NoSQL Redis" della Data Encyclopedia.*
