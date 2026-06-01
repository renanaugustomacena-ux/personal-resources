# Redis: Performance e Ottimizzazione

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
1. Memory Optimization
2. Key Design
3. Pipeline Usage
4. Cluster Optimization
5. I/O Threading (Redis 7+)
6. Latency Analysis and Reduction
7. Connection Management
8. Data Structure Selection for Performance
9. Configuration Tuning Reference
10. Monitoring and Profiling
11. Operational Procedures
12. Real-World Patterns
13. Troubleshooting
14. FAQ

---

## 1. Memory Optimization

### 1.1 Eviction Policies

Redis can operate as a bounded-memory cache by setting `maxmemory` and choosing an eviction policy. When memory usage reaches the limit, Redis evicts keys according to the selected policy before accepting new writes.

```bash
# Set maximum memory
maxmemory 2gb

# Eviction policy options:
maxmemory-policy allkeys-lru

# Full list of policies:
# noeviction        - Return error on write when memory full (default)
# allkeys-lru       - Evict least recently used across all keys
# allkeys-lfu       - Evict least frequently used across all keys (Redis 4+)
# allkeys-random    - Evict random keys
# volatile-lru      - Evict LRU among keys with TTL set
# volatile-lfu      - Evict LFU among keys with TTL set
# volatile-random   - Evict random keys with TTL set
# volatile-ttl      - Evict keys with shortest remaining TTL
```

### 1.2 LRU vs LFU

Redis does not implement exact LRU/LFU. It samples a configurable number of keys and evicts the best candidate from the sample.

```bash
# Number of keys to sample for eviction (default 5, higher = more accurate but slower)
maxmemory-samples 10

# LFU tuning (Redis 4+)
# lfu-log-factor: higher = slower frequency counter growth
# lfu-decay-time: minutes before frequency counter decays
lfu-log-factor 10
lfu-decay-time 1
```

**When to use LFU over LRU**: LFU is better when access patterns have a power-law distribution (few keys accessed very frequently). LRU is better when recency matters more than frequency.

### 1.3 Memory Analysis

```bash
# Overall memory stats
INFO memory
# Key fields:
# used_memory         - total bytes allocated by Redis allocator
# used_memory_rss     - resident set size (OS-reported)
# mem_fragmentation_ratio - RSS / used_memory (>1.5 = high fragmentation)
# used_memory_dataset - memory used by data (excluding overhead)

# Memory usage of a single key
MEMORY USAGE mykey
MEMORY USAGE mykey SAMPLES 0   # exact calculation (slower for large values)

# Memory doctor (Redis 7+)
MEMORY DOCTOR

# Key distribution analysis
redis-cli --bigkeys
redis-cli --memkeys

# Find the top-N largest keys (Redis 7+)
redis-cli --bigkeys --no-auth-warning
```

### 1.4 Memory Fragmentation

```bash
# Check fragmentation ratio
INFO memory
# mem_fragmentation_ratio > 1.5 means high fragmentation

# Active defragmentation (Redis 4+)
activedefrag yes

# Tuning defrag behavior
active-defrag-enabled yes
active-defrag-ignore-bytes 100mb       # Minimum fragmentation waste to trigger
active-defrag-threshold-lower 10       # Minimum percentage to start
active-defrag-threshold-upper 100      # Maximum percentage for full effort
active-defrag-cycle-min 1              # Minimal CPU % for defrag
active-defrag-cycle-max 25             # Maximum CPU % for defrag
active-defrag-max-scan-fields 1000     # Max fields scanned per step in hash/set/zset
```

### 1.5 Hash Ziplist Optimization

Small Hashes, Sets, and Sorted Sets use compact encodings (ziplist/listpack in Redis 7+) that are significantly more memory-efficient than their full data structure counterparts.

```bash
# Redis 7+ uses listpack instead of ziplist
# Thresholds for listpack encoding:
hash-max-listpack-entries 128       # Max entries before converting to hashtable
hash-max-listpack-value 64          # Max value size (bytes) for listpack

zset-max-listpack-entries 128
zset-max-listpack-value 64

set-max-listpack-entries 128

list-max-listpack-size -2           # -2 = 8KB per node (recommended)
```

A Hash with 100 fields and short values uses ~10x less memory than 100 separate String keys. This is one of the most impactful optimizations.

---

## 2. Key Design

### 2.1 Key Naming Conventions

```bash
# Convention: object-type:id:field
# Examples:
user:1234:profile
session:abc123
cache:page:home:v2
queue:emails:pending

# Use colons as separators (community convention)
# Keep key names descriptive but not excessively long
```

### 2.2 Key Length Impact

Every key is stored as a string object. In a dataset with millions of keys, shorter names save megabytes.

```bash
# Measure the difference
SET user:1234567890:profile:name "John"
MEMORY USAGE user:1234567890:profile:name
# ~90 bytes

SET u:1234567890:p:n "John"
MEMORY USAGE u:1234567890:p:n
# ~72 bytes

# At 10 million keys, the ~18 byte difference = ~171 MB saved
```

However, readability matters. Use abbreviations only when the dataset is large enough to justify it.

### 2.3 Hash Packing (Small Object Optimization)

Instead of many individual keys, group related small fields into a single Hash:

```bash
# BAD: 5 keys per user, 1M users = 5M keys
SET user:123:name "John"
SET user:123:email "john@test.com"
SET user:123:age "30"
SET user:123:city "NYC"
SET user:123:role "admin"

# GOOD: 1 hash per user, 1M users = 1M keys
HSET user:123 name "John" email "john@test.com" age "30" city "NYC" role "admin"
HGETALL user:123
```

### 2.4 Key Expiration Strategy

```bash
# Set TTL at creation time (atomic)
SET session:abc "data" EX 3600          # seconds
SET session:abc "data" PX 3600000       # milliseconds
SET session:abc "data" EXAT 1700000000  # Unix timestamp (seconds)
SET session:abc "data" PXAT 1700000000000  # Unix timestamp (milliseconds)

# Set TTL on existing key
EXPIRE key 3600
PEXPIRE key 3600000
EXPIREAT key 1700000000

# Check remaining TTL
TTL key       # seconds (-1 = no expiry, -2 = key does not exist)
PTTL key      # milliseconds

# Remove expiration
PERSIST key

# Redis 7.x: conditional expiration
EXPIRE key 3600 NX   # Set only if key has no expiry
EXPIRE key 3600 XX   # Set only if key already has an expiry
EXPIRE key 3600 GT   # Set only if new TTL > current TTL
EXPIRE key 3600 LT   # Set only if new TTL < current TTL
```

---

## 3. Pipeline Usage

### 3.1 How Pipelines Work

Without pipelining, each Redis command requires a full network round trip (send command, wait for response). Pipelining batches multiple commands into a single write, then reads all responses at once. This reduces the round-trip-time (RTT) overhead from O(N * RTT) to O(RTT).

```python
import redis

r = redis.Redis(host='localhost', port=6379)

# WITHOUT pipeline: 1000 round trips
for i in range(1000):
    r.set(f'key:{i}', f'value:{i}')
# Total time: ~1000 * RTT (e.g., 1000 * 0.5ms = 500ms)

# WITH pipeline: 1 round trip
pipe = r.pipeline(transaction=False)
for i in range(1000):
    pipe.set(f'key:{i}', f'value:{i}')
results = pipe.execute()
# Total time: ~1 * RTT + server processing (e.g., 5ms)
```

### 3.2 Pipeline vs Transaction

```python
# Pipeline without transaction (no atomicity, max throughput)
pipe = r.pipeline(transaction=False)
pipe.set('a', 1)
pipe.set('b', 2)
pipe.execute()  # Commands may interleave with other clients

# Pipeline with MULTI/EXEC (atomic transaction)
pipe = r.pipeline(transaction=True)  # default
pipe.set('a', 1)
pipe.set('b', 2)
pipe.execute()  # Wrapped in MULTI/EXEC, atomic execution
```

### 3.3 Pipeline Batch Sizing

Sending millions of commands in a single pipeline can consume excessive server memory (the entire response is buffered). Batch in chunks:

```python
BATCH_SIZE = 10000

pipe = r.pipeline(transaction=False)
for i in range(1_000_000):
    pipe.set(f'key:{i}', f'value:{i}')
    if (i + 1) % BATCH_SIZE == 0:
        pipe.execute()
        pipe = r.pipeline(transaction=False)

# Flush remaining
pipe.execute()
```

### 3.4 Pipeline in Cluster Mode

In Redis Cluster, pipelining still works but commands are grouped by slot and sent to the appropriate node. Cluster-aware clients (redis-py-cluster, ioredis) handle this transparently. Commands targeting the same slot are batched together.

```python
from redis.cluster import RedisCluster

rc = RedisCluster(host='redis-node-1', port=6379)
pipe = rc.pipeline()
pipe.set('key1', 'a')  # Routed to slot for 'key1'
pipe.set('key2', 'b')  # Routed to slot for 'key2'
pipe.execute()          # Internally batched per node
```

Use hash tags to force keys to the same slot for pipeline efficiency:

```bash
# {user:123} is the hash tag -- all these keys land on the same slot
SET {user:123}:name "John"
SET {user:123}:email "john@test.com"
SET {user:123}:age "30"
```

---

## 4. Cluster Optimization

### 4.1 Read from Replicas

```bash
# READONLY mode on replica connections (cluster mode)
READONLY

# In application code (redis-py)
from redis.cluster import RedisCluster

rc = RedisCluster(
    host='redis-node-1',
    port=6379,
    read_from_replicas=True  # Distribute reads across replicas
)
```

### 4.2 Hash Tag Design for Multi-Key Operations

Multi-key commands (MGET, MSET, SUNION, pipeline batches) require all keys to reside on the same slot in cluster mode. Use hash tags:

```bash
# All keys share the same hash tag {order:5001}
MSET {order:5001}:items "..." {order:5001}:total "59.99" {order:5001}:status "pending"
MGET {order:5001}:items {order:5001}:total {order:5001}:status

# Verify slot assignment
CLUSTER KEYSLOT {order:5001}:items
CLUSTER KEYSLOT {order:5001}:total
# Both return the same slot number
```

### 4.3 Avoid Hot Slots

If one hash tag is accessed disproportionately, the node owning that slot becomes a bottleneck. Distribute load by varying hash tags:

```bash
# BAD: all rate limits on one slot
SET {ratelimit}:user:1 ...
SET {ratelimit}:user:2 ...

# BETTER: distribute across slots
SET ratelimit:user:1 ...
SET ratelimit:user:2 ...
# Each key hashes independently
```

---

## 5. I/O Threading (Redis 7+)

### 5.1 How I/O Threading Works

Redis is fundamentally single-threaded for command execution (this guarantees atomicity). However, Redis 6.0+ introduced I/O threads that handle network read/write operations in parallel. The main thread still executes commands sequentially, but socket I/O is offloaded.

### 5.2 Configuration

```bash
# Number of I/O threads (default 1 = disabled)
# Recommended: set to number of CPU cores / 2, minimum 2, maximum 8
io-threads 4

# Enable threaded reads (disabled by default, writes are always threaded)
io-threads-do-reads yes
```

### 5.3 When I/O Threading Helps

- High connection count (thousands of clients)
- Large payloads (values > 1KB)
- Network-bound workloads (high bandwidth, low command complexity)

I/O threading does NOT help when:
- The bottleneck is CPU (complex Lua scripts, SORT, large aggregations)
- Connection count is low (< 100 clients)
- Payloads are tiny (< 100 bytes)

### 5.4 Benchmarking I/O Threads

```bash
# Baseline without I/O threads
redis-benchmark -h 127.0.0.1 -p 6379 -c 300 -n 1000000 -t SET,GET -d 1024

# Enable threads (via CONFIG SET, no restart needed for testing)
CONFIG SET io-threads 4
CONFIG SET io-threads-do-reads yes

# Re-run benchmark
redis-benchmark -h 127.0.0.1 -p 6379 -c 300 -n 1000000 -t SET,GET -d 1024

# Compare throughput (ops/sec) and latency (p50, p99)
```

---

## 6. Latency Analysis and Reduction

### 6.1 Measuring Latency

```bash
# Built-in latency test (measures RTT from client to server)
redis-cli --latency
redis-cli --latency-history -i 5  # sample every 5 seconds
redis-cli --latency-dist           # ASCII latency distribution

# Intrinsic latency (measures jitter from the OS/hardware)
redis-cli --intrinsic-latency 10   # test for 10 seconds
```

### 6.2 SLOWLOG

The slowlog captures commands exceeding a time threshold. It is the primary tool for finding expensive operations.

```bash
# Configuration
slowlog-log-slower-than 10000  # microseconds (10ms default)
slowlog-max-len 128            # max entries to keep

# View slow commands
SLOWLOG GET 10       # last 10 entries
SLOWLOG LEN          # number of entries
SLOWLOG RESET        # clear the log

# Runtime reconfiguration
CONFIG SET slowlog-log-slower-than 5000   # lower to 5ms
CONFIG SET slowlog-max-len 256
```

### 6.3 LATENCY Subsystem

```bash
# Enable latency monitoring
CONFIG SET latency-monitor-threshold 5  # milliseconds

# View latency events
LATENCY LATEST
LATENCY HISTORY command
LATENCY HISTORY fast-command

# Human-readable report
LATENCY DOCTOR

# Reset
LATENCY RESET
```

### 6.4 Common Latency Sources

| Source | Impact | Mitigation |
|---|---|---|
| KEYS * | O(N) scan of entire keyspace | Use SCAN with cursor |
| SORT on large sets | O(N+M*log(M)) | Limit result size, add BY/GET |
| SMEMBERS on large sets | O(N) | Use SSCAN |
| HGETALL on large hashes | O(N) | Use HSCAN or HMGET specific fields |
| SAVE (synchronous) | Blocks entirely | Use BGSAVE |
| AOF rewrite | fork() latency | Schedule during low traffic |
| Swap (OS) | Catastrophic | Disable swap or set vm.overcommit |
| Transparent Huge Pages | Fork latency spike | Disable THP |

### 6.5 Dangerous Commands to Avoid in Production

```bash
# NEVER use in production (O(N) on entire keyspace)
KEYS *
KEYS user:*

# Use SCAN instead (cursor-based, non-blocking)
SCAN 0 MATCH user:* COUNT 100

# Similarly, avoid:
# SMEMBERS on large sets → use SSCAN
# HGETALL on large hashes → use HSCAN
# LRANGE 0 -1 on large lists → paginate with LRANGE start end
```

---

## 7. Connection Management

### 7.1 Connection Pooling

Every Redis connection consumes ~10KB of memory on the server side. Thousands of idle connections waste resources.

```bash
# Server-side limits
maxclients 10000           # default
timeout 300                # close idle connections after 300 seconds (0 = disabled)
tcp-keepalive 300          # TCP keepalive interval

# Check connected clients
INFO clients
CLIENT LIST
CLIENT LIST TYPE normal
```

### 7.2 Client-Side Connection Pooling

```python
# Python -- always use connection pools in production
pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    decode_responses=True,
    socket_timeout=5,
    socket_connect_timeout=2,
    retry_on_timeout=True,
    health_check_interval=30
)
r = redis.Redis(connection_pool=pool)
```

```java
// Java (Jedis) -- pool configuration
JedisPoolConfig config = new JedisPoolConfig();
config.setMaxTotal(50);
config.setMaxIdle(20);
config.setMinIdle(5);
config.setTestOnBorrow(true);
config.setTestWhileIdle(true);

JedisPool pool = new JedisPool(config, "localhost", 6379, 2000);
```

### 7.3 Multiplexing (Shared Connection)

Some clients (Lettuce for Java, ioredis for Node.js) use a single multiplexed connection. This is more efficient for low-to-medium concurrency:

```javascript
// ioredis: single connection, multiplexed
const redis = new Redis({
  host: 'localhost',
  port: 6379,
  lazyConnect: true,
  maxRetriesPerRequest: 3,
  retryStrategy(times) {
    return Math.min(times * 50, 2000);
  }
});
```

---

## 8. Data Structure Selection for Performance

### 8.1 Performance Characteristics

| Operation | String | Hash | List | Set | Sorted Set |
|---|---|---|---|---|---|
| Single field read | O(1) | O(1) | O(N) | O(1) | O(log N) |
| Single field write | O(1) | O(1) | O(1) push | O(1) | O(log N) |
| Range query | N/A | N/A | O(S+N) | N/A | O(log N + M) |
| Membership test | N/A | O(1) | O(N) | O(1) | O(log N) |
| Memory (small) | Baseline | ~10x less per field* | Compact | Compact | Compact |

*When Hash uses listpack encoding (< 128 entries with small values).

### 8.2 Choosing the Right Structure

```
Need fast lookup by field?         → Hash
Need ordered data with scores?     → Sorted Set
Need FIFO/LIFO queue?              → List (LPUSH/RPOP) or Stream
Need unique membership?            → Set
Need approximate unique count?     → HyperLogLog
Need bit-level operations?         → Bitmap (String with SETBIT/GETBIT)
Need time-series with consumers?   → Stream
Need simple key-value?             → String
Need JSON document operations?     → RedisJSON module or Hash
```

---

## 9. Configuration Tuning Reference

### 9.1 Memory

```bash
maxmemory 4gb
maxmemory-policy allkeys-lfu
maxmemory-samples 10

# Listpack thresholds (Redis 7+)
hash-max-listpack-entries 128
hash-max-listpack-value 64
zset-max-listpack-entries 128
zset-max-listpack-value 64
set-max-listpack-entries 128
list-max-listpack-size -2

# Active defrag
activedefrag yes
active-defrag-ignore-bytes 100mb
active-defrag-threshold-lower 10
active-defrag-cycle-min 1
active-defrag-cycle-max 25
```

### 9.2 Network

```bash
# I/O threads
io-threads 4
io-threads-do-reads yes

# TCP backlog
tcp-backlog 511

# TCP keepalive
tcp-keepalive 300

# Client output buffer limits
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
```

### 9.3 Persistence (Performance Impact)

```bash
# RDB: less frequent saves = less fork overhead
save 3600 1
save 300 100
save 60 10000

# AOF: everysec is the best balance
appendfsync everysec

# No-appendfsync-on-rewrite: prevent AOF fsync during BGSAVE/BGREWRITEAOF
no-appendfsync-on-rewrite yes

# Lazy freeing (background deletion for large keys)
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
lazyfree-lazy-user-del yes
lazyfree-lazy-user-flush yes
```

### 9.4 Kernel / OS Tuning

```bash
# Disable Transparent Huge Pages (causes fork latency spikes)
echo never > /sys/kernel/mm/transparent_hugepage/enabled

# Set overcommit memory (required for BGSAVE fork)
sysctl vm.overcommit_memory=1

# Increase max open files
ulimit -n 65535

# Increase TCP backlog
sysctl net.core.somaxconn=65535
sysctl net.ipv4.tcp_max_syn_backlog=65535

# Disable swap (or set swappiness very low)
sysctl vm.swappiness=1
```

---

## 10. Monitoring and Profiling

### 10.1 Key Metrics to Monitor

```bash
# Commands processed per second
INFO stats
# instantaneous_ops_per_sec

# Memory
INFO memory
# used_memory, used_memory_rss, mem_fragmentation_ratio

# Connected clients
INFO clients
# connected_clients, blocked_clients

# Keyspace
INFO keyspace
# db0:keys=1000,expires=500,avg_ttl=3600000

# Replication lag
INFO replication
# master_repl_offset, slave_repl_offset (diff = lag)
```

### 10.2 redis-cli Profiling Tools

```bash
# Continuous latency monitoring
redis-cli --latency-history -i 1

# Big key detection (samples keyspace)
redis-cli --bigkeys

# Memory key analysis
redis-cli --memkeys

# Hot key detection (requires maxmemory-policy with LFU)
redis-cli --hotkeys

# Command statistics
INFO commandstats
# cmdstat_get:calls=1000,usec=5000,usec_per_call=5.00
```

### 10.3 Real-Time Monitoring

```bash
# MONITOR: streams every command processed (DEBUG ONLY, high overhead)
MONITOR

# CLIENT LIST: see all connected clients and their state
CLIENT LIST

# CLIENT INFO: current client's info
CLIENT INFO
```

---

## 11. Operational Procedures

### 11.1 Performance Baseline

Before any optimization, establish a baseline:

```bash
# 1. Record current metrics
redis-cli INFO stats > baseline_stats.txt
redis-cli INFO memory >> baseline_stats.txt

# 2. Run redis-benchmark for throughput baseline
redis-benchmark -h 127.0.0.1 -p 6379 -c 50 -n 100000 -q

# 3. Capture latency profile
redis-cli --latency-history -i 1 -c 100

# 4. Record slow log
SLOWLOG GET 128

# 5. Document configuration
CONFIG GET *
```

### 11.2 Rolling Configuration Changes

```bash
# Most settings can be changed at runtime without restart
CONFIG SET maxmemory 4gb
CONFIG SET maxmemory-policy allkeys-lfu

# Verify the change
CONFIG GET maxmemory
CONFIG GET maxmemory-policy

# Persist runtime changes to config file
CONFIG REWRITE
```

### 11.3 Memory Pressure Response

```bash
# Step 1: Check current state
INFO memory
DBSIZE

# Step 2: Find large keys
redis-cli --bigkeys

# Step 3: Enable lazy-free if not already
CONFIG SET lazyfree-lazy-eviction yes

# Step 4: Set eviction policy if not set
CONFIG SET maxmemory-policy allkeys-lfu

# Step 5: Trim streams, expire stale keys
SCAN 0 MATCH temp:* COUNT 1000
# Delete found stale keys
```

---

## 12. Real-World Patterns

### 12.1 Batch Warming

Pre-populate cache before traffic spikes:

```python
def warm_cache(user_ids):
    pipe = r.pipeline(transaction=False)
    for uid in user_ids:
        user = db.get_user(uid)
        pipe.setex(f'user:{uid}', 3600, json.dumps(user))
    pipe.execute()
```

### 12.2 Coalesced Reads

Prevent thundering herd on cache miss:

```python
import threading

_locks = {}
_lock_guard = threading.Lock()

def get_with_coalescing(key, loader, ttl=3600):
    value = r.get(key)
    if value is not None:
        return json.loads(value)

    # Acquire per-key lock to prevent duplicate DB queries
    with _lock_guard:
        if key not in _locks:
            _locks[key] = threading.Lock()
        lock = _locks[key]

    with lock:
        # Double-check after acquiring lock
        value = r.get(key)
        if value is not None:
            return json.loads(value)

        result = loader()
        r.setex(key, ttl, json.dumps(result))
        return result
```

### 12.3 Probabilistic Early Expiration (PER)

Proactively refresh cache entries before they expire to avoid thundering herd:

```python
import math
import random

def get_with_per(key, loader, ttl=3600, beta=1.0):
    """Probabilistic Early Recomputation (XFetch algorithm)."""
    value = r.get(key)
    remaining_ttl = r.ttl(key)

    if value is not None and remaining_ttl > 0:
        # Probability of early recomputation increases as TTL approaches 0
        delta = ttl - remaining_ttl  # time since last refresh
        threshold = delta * beta * math.log(random.random())
        if remaining_ttl + threshold > 0:
            return json.loads(value)

    # Cache miss or early recomputation triggered
    result = loader()
    r.setex(key, ttl, json.dumps(result))
    return result
```

### 12.4 Async Pipeline Pattern (Node.js)

```javascript
const Redis = require('ioredis');
const redis = new Redis();

async function batchLookup(keys) {
  const pipeline = redis.pipeline();
  keys.forEach(key => pipeline.get(key));
  const results = await pipeline.exec();
  return results.map(([err, val]) => {
    if (err) throw err;
    return val ? JSON.parse(val) : null;
  });
}
```

---

## 13. Troubleshooting

### 13.1 High Latency Spikes

**Symptoms**: p99 latency jumps from < 1ms to > 50ms intermittently.

**Diagnosis**:
```bash
LATENCY LATEST
LATENCY HISTORY fork
```

**Common causes**: BGSAVE/BGREWRITEAOF fork on large datasets, THP enabled, OS swapping.

**Resolution**: Disable THP, schedule persistence during low traffic, ensure `vm.overcommit_memory=1`.

### 13.2 Memory Usage Higher Than Expected

**Symptoms**: `used_memory_rss` is much higher than `used_memory`.

**Diagnosis**:
```bash
INFO memory
# Check mem_fragmentation_ratio
```

**Resolution**: Enable active defragmentation. If ratio > 2.0, consider restarting Redis to reclaim fragmented memory.

### 13.3 Connection Refused Under Load

**Symptoms**: Clients get `ECONNREFUSED` or `Cannot assign requested address`.

**Diagnosis**: Check `maxclients`, OS file descriptor limit, TCP backlog.

```bash
CONFIG GET maxclients
# Check OS limits
ulimit -n
cat /proc/sys/net/core/somaxconn
```

**Resolution**: Increase `maxclients`, `ulimit -n`, `net.core.somaxconn`. Use connection pooling.

### 13.4 KEYS Command Causing Downtime

**Symptoms**: Redis becomes unresponsive during `KEYS *` execution.

**Resolution**: Never use `KEYS` in production. Use `SCAN` instead. Rename or disable `KEYS`:
```bash
rename-command KEYS ""
```

### 13.5 OOM Killer Terminating Redis

**Symptoms**: Redis process disappears, `dmesg` shows OOM kill.

**Diagnosis**:
```bash
dmesg | grep -i "out of memory"
dmesg | grep -i redis
```

**Resolution**: Set `maxmemory` below available RAM, set `vm.overcommit_memory=1`, disable swap or set `vm.swappiness=1`.

### 13.6 Slow BGSAVE on Large Datasets

**Symptoms**: `BGSAVE` takes minutes, causes latency spikes during `fork()`.

**Diagnosis**:
```bash
INFO persistence
# rdb_last_bgsave_time_sec, rdb_last_bgsave_status
LATENCY HISTORY fork
```

**Resolution**: Ensure sufficient free RAM for copy-on-write (fork needs ~2x memory in worst case). Disable THP. Consider using AOF only for smaller datasets.

### 13.7 Pipeline Not Improving Performance

**Symptoms**: Pipeline throughput is similar to non-pipeline.

**Cause**: Network is not the bottleneck (localhost), or commands are CPU-heavy (Lua scripts, SORT).

**Resolution**: Pipeline benefits are largest over network (not loopback). For CPU-bound commands, optimize the commands themselves.

### 13.8 Eviction Happening on Unexpected Keys

**Symptoms**: Keys without TTL are being evicted.

**Cause**: `allkeys-lru` or `allkeys-lfu` policy evicts any key, not just those with TTL.

**Resolution**: Use `volatile-lru` or `volatile-lfu` if only TTL keys should be evicted. Set TTL on cache keys.

### 13.9 Cluster Resharding Performance Impact

**Symptoms**: Latency increases during slot migration.

**Resolution**: Migrate during low-traffic windows. Use `redis-cli --cluster reshard` with small slot batches.

### 13.10 High CPU Usage with Low QPS

**Symptoms**: CPU at 80%+ despite low command rate.

**Diagnosis**:
```bash
INFO commandstats
SLOWLOG GET 50
```

**Common causes**: Expensive commands (SORT, ZUNIONSTORE on large sets), Lua scripts, large key serialization for persistence.

**Resolution**: Identify expensive commands via `SLOWLOG` and `commandstats`. Optimize or eliminate them.

### 13.11 Client-Side Timeout Errors

**Symptoms**: Application logs show Redis timeout exceptions despite server being responsive.

**Cause**: Client-side pool exhaustion, network congestion, or slow consumer blocking the connection.

**Resolution**: Increase pool size, set appropriate `socket_timeout`, enable `retry_on_timeout`, check network path.

---

## 14. FAQ

### Q1: Should I disable persistence for pure-cache use cases?

Yes, if data loss is acceptable. Set `save ""` and `appendonly no`. This eliminates fork overhead and disk I/O, giving the lowest latency.

### Q2: How many I/O threads should I configure?

Start with `io-threads 4`. Benchmark with your workload. More threads help with many connections and large payloads. Never exceed the number of CPU cores. Redis documentation recommends no more than 8.

### Q3: Is MULTI/EXEC slower than pipelining without transactions?

Slightly. `MULTI/EXEC` adds two extra commands (MULTI and EXEC) and prevents command interleaving. For non-atomic batches, use `pipeline(transaction=False)` for maximum throughput.

### Q4: What is the maximum number of keys Redis can hold?

2^32 keys (over 4 billion). The practical limit is available memory. Each key has ~70 bytes of overhead (dictEntry + SDS string + redisObject).

### Q5: Should I compress values before storing in Redis?

Yes, for values > 1KB. Compression (gzip, lz4, zstd) reduces memory usage and network transfer at the cost of CPU on client side. Redis itself does not decompress -- the application must handle it.

### Q6: How do I identify hot keys?

```bash
# Requires LFU eviction policy
redis-cli --hotkeys

# Or use OBJECT FREQ (requires LFU policy)
OBJECT FREQ mykey
```

### Q7: Can Redis use multiple CPU cores for command execution?

No. Command execution is single-threaded. I/O threads (Redis 6+) only parallelize network I/O. For multi-core utilization, run multiple Redis instances or use Redis Cluster.

### Q8: What is the overhead of enabling AOF?

With `appendfsync everysec`, the overhead is minimal (one fsync per second). With `appendfsync always`, every write triggers an fsync, reducing throughput by 10-50x. Never use `always` in high-throughput workloads.

### Q9: How do I benchmark my specific workload?

```bash
# Custom benchmark with redis-benchmark
redis-benchmark -h host -p 6379 -c 100 -n 1000000 -d 256 \
  -t SET,GET,LPUSH,LPOP,ZADD --csv

# For complex operations, write a custom script:
redis-benchmark -h host -p 6379 -c 100 -n 100000 \
  eval "redis.call('SET',KEYS[1],ARGV[1])" 1 __rand_int__ __rand_int__
```

### Q10: When should I use allkeys-lfu instead of allkeys-lru?

Use LFU when your access pattern has a clear "hot" working set that is accessed much more frequently than the tail. LFU keeps frequently-accessed keys even if they were not accessed recently. LRU is better for recency-driven workloads.

### Q11: Does maxmemory include replication buffer and AOF buffer?

No. `maxmemory` only accounts for the data keyspace. Replication buffers, AOF buffers, client output buffers, and Lua script memory are additional. Plan for 20-30% overhead on top of `maxmemory`.

### Q12: How do I handle thundering herd on cache expiration?

Use one of: (1) probabilistic early recomputation (section 12.3), (2) coalesced reads with per-key locking (section 12.2), or (3) staggered TTLs (add random jitter to TTL: `base_ttl + random(0, base_ttl * 0.1)`).

---

*Questo documento fa parte del modulo 06 "NoSQL Redis" della Data Encyclopedia.*
