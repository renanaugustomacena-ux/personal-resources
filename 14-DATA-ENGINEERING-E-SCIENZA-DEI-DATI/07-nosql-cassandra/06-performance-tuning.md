# Cassandra: Performance Tuning

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
1. Memory Tuning
2. JVM and Garbage Collection
3. Disk I/O Optimization
4. Compaction Tuning
5. Caching
6. Query Optimization
7. Write Path Tuning
8. Read Path Tuning
9. Network Tuning
10. OS-Level Tuning
11. Benchmarking
12. Cassandra 4.x/5.x Performance Features
13. Troubleshooting
14. FAQ

---

## 1. Memory Tuning

### 1.1 Memory Architecture Overview

Cassandra uses memory in three main areas:
1. **JVM Heap**: memtables, key cache, row cache, internal data structures.
2. **JVM Off-Heap**: bloom filters, compression metadata, partition summary.
3. **OS Page Cache**: cached SSTables for read performance (managed by Linux kernel).

The optimal memory split depends on workload, but a general guideline for a 64 GB machine:
- JVM Heap: 16 GB (never exceed 31 GB with G1GC)
- Off-Heap: 4-8 GB (automatic)
- OS Page Cache: remaining ~40 GB

### 1.2 Memtable Configuration

```yaml
# cassandra.yaml
# Memtables buffer writes before flushing to SSTables.
# Larger memtables = fewer flushes = better write throughput,
# but more heap pressure and longer flush times.

# On-heap memtable space (shared across ALL tables on the node)
memtable_heap_space_in_mb: 2048

# Off-heap memtable space (reduces GC pressure)
memtable_offheap_space_in_mb: 2048

# Flush threshold: memtable is flushed when either threshold is reached
memtable_cleanup_threshold: 0.11
# This means: flush when memtable usage exceeds (1 - 0.11) = 89% of total

# Memtable allocation type
memtable_allocation_type: heap_buffers
# Options:
# heap_buffers      -- allocate on JVM heap (simple, but GC pressure)
# offheap_buffers   -- allocate off-heap (reduces GC, slight CPU overhead)
# offheap_objects   -- off-heap with object-level management (experimental)
```

### 1.3 Key Cache

```yaml
# cassandra.yaml
# Key cache maps partition keys to SSTable byte offsets.
# A cache hit avoids reading the partition index from disk.
# VERY effective; always enable.

key_cache_size_in_mb: 256
# Auto-size: leave empty to use 5% of heap (capped at 100 MB)

key_cache_save_period: 14400   # persist to disk every 4 hours (seconds)

# Verify key cache effectiveness:
# nodetool info | grep "Key Cache"
# Target: hit rate > 85%
```

### 1.4 Row Cache

```yaml
# cassandra.yaml
# Row cache stores entire partitions in memory.
# EXPENSIVE: uses a lot of heap; invalidated on ANY write to the partition.
# Only beneficial for small, frequently-read, rarely-written tables.

row_cache_size_in_mb: 0       # disabled by default (recommended)

# Enable per-table instead of globally:
# CREATE TABLE ... WITH caching = {'keys': 'ALL', 'rows_per_partition': '100'};

# When to use row cache:
# - Small lookup tables (< 1000 rows)
# - Read-heavy, write-rare (e.g., configuration, feature flags)
# - Partitions are small (< 10 KB)

# When NOT to use row cache:
# - Write-heavy tables (invalidation overhead exceeds benefit)
# - Large partitions (wastes heap)
# - Tables with frequent updates
```

### 1.5 Counter Cache

```yaml
# cassandra.yaml
counter_cache_size_in_mb: 50
# Caches counter cell values to speed up counter reads.
# Only relevant for tables using counter columns.
# If you don't use counters, leave at 0.
```

### 1.6 Chunk Cache (Off-Heap)

```yaml
# cassandra.yaml (Cassandra 4.0+)
# Replaces the old buffer pool. Caches compressed SSTable chunks.
# Allocated off-heap, does not affect GC.

file_cache_size_in_mb: 512
# Auto-size: if not set, uses min(1/4 of heap, 512 MB)
# For read-heavy workloads on SSDs, increase to 1024-2048 MB.
```

---

## 2. JVM and Garbage Collection

### 2.1 Heap Sizing

```bash
# jvm11-server.options (Cassandra 4.x)
# or jvm17-server.options (Cassandra 5.x)

# Heap should be 1/4 to 1/2 of total RAM, max 31 GB (compressed oops)
# For most workloads: 8-16 GB is optimal

# GOOD: 16 GB heap on a 64 GB machine
-Xms16G
-Xmx16G

# WRONG: 48 GB heap on a 64 GB machine
# Leaves no RAM for OS page cache -- read performance suffers.

# Young gen sizing (G1GC auto-manages this, but can be tuned):
# -Xmn is NOT recommended with G1GC; let G1 manage regions.
```

### 2.2 G1GC Tuning (Cassandra 4.x Default)

```bash
# jvm11-server.options
-XX:+UseG1GC

# Target max GC pause
-XX:MaxGCPauseMillis=500

# G1 heap region size (should be large enough for big memtables)
-XX:G1HeapRegionSize=16m

# Initiating heap occupancy (trigger mixed GC earlier to avoid full GC)
-XX:InitiatingHeapOccupancyPercent=45

# Parallel GC threads (match core count)
-XX:ParallelGCThreads=16

# Concurrent GC threads (1/4 of ParallelGCThreads)
-XX:ConcGCThreads=4

# Survivor ratio
-XX:SurvivorRatio=8

# Max tenuring threshold (how many young GC cycles before promotion)
-XX:MaxTenuringThreshold=1

# NEVER use CMS with heap > 8 GB -- long STW pauses.
# CMS is deprecated in Java 14+ anyway.
```

### 2.3 ZGC (Cassandra 5.0, Experimental)

```bash
# jvm17-server.options
# ZGC provides sub-millisecond GC pauses regardless of heap size.
# Experimental in Cassandra 5.0; higher CPU overhead than G1GC.

-XX:+UseZGC
-XX:+ZGenerational    # generational ZGC (Java 21+)

# No need for MaxGCPauseMillis -- ZGC pauses are always < 1ms.
# Trade-off: ~5-10% higher CPU usage compared to G1GC.
```

### 2.4 JVM Diagnostic Options

```bash
# Enable GC logging
-Xlog:gc*,gc+age=trace,gc+heap=debug:file=/var/log/cassandra/gc.log:time,level,tags:filecount=10,filesize=100m

# Enable heap dump on OOM
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/cassandra/

# Disable explicit GC calls (prevents System.gc() from causing STW)
-XX:+DisableExplicitGC

# Enable compressed oops (automatic if heap <= 31 GB)
-XX:+UseCompressedOops

# Thread stack size
-Xss512k
```

### 2.5 Monitoring GC Performance

```bash
# Key indicators of GC health:
# 1. GC pause time (should be < 500ms for G1GC)
grep "GC pause" /var/log/cassandra/gc.log | awk '{print $NF}' | sort -n | tail -10

# 2. GC throughput (time NOT spent in GC; target > 95%)
# Use GCViewer or GCEasy.io for analysis

# 3. Heap after GC (if steadily increasing, likely a memory leak)
grep "Heap after GC" /var/log/cassandra/gc.log

# 4. Full GC events (should be 0 in production)
grep "Full GC" /var/log/cassandra/gc.log

# nodetool for JVM memory info:
nodetool info | grep -E "Heap|Off"
# Heap Memory (MB) : 4096.00 / 16384.00
# Off Heap Memory (MB) : 1234.56
```

---

## 3. Disk I/O Optimization

### 3.1 Storage Layout

```yaml
# cassandra.yaml
# CRITICAL: separate commitlog from data on different physical disks.
# Commitlog is sequential write; data is random read/write.
# Mixing them on one disk creates I/O contention.

commitlog_directory: /ssd1/cassandra/commitlog    # dedicated fast SSD
data_file_directories:
  - /ssd2/cassandra/data                          # one or more SSDs

# For JBOD (Just a Bunch of Disks) with multiple data drives:
data_file_directories:
  - /ssd2/cassandra/data
  - /ssd3/cassandra/data
  - /ssd4/cassandra/data
# Cassandra distributes SSTables across drives round-robin.
# JBOD is preferred over RAID for Cassandra (Cassandra handles redundancy via replication).

# Saved caches directory (low I/O; can share with data)
saved_caches_directory: /ssd2/cassandra/saved_caches

# Hints directory
hints_directory: /ssd2/cassandra/hints
```

### 3.2 Commitlog Configuration

```yaml
# cassandra.yaml
# Commitlog ensures write durability. Every mutation is written to
# commitlog before the memtable.

commitlog_sync: periodic
# periodic: batch fsync every commitlog_sync_period_in_ms
# batch: fsync every write (slowest but safest)

commitlog_sync_period_in_ms: 10000   # 10 seconds (default)
# Lower = more durable (less data loss on crash) but more I/O.
# Higher = better write throughput but potential data loss window.

commitlog_total_space_in_mb: 8192    # total commitlog space
# When full, the oldest commitlog segment is recycled after its
# corresponding memtable is flushed.

commitlog_segment_size_in_mb: 32     # individual segment size

# Commitlog compression (reduces disk I/O at the cost of CPU):
commitlog_compression:
  - class_name: LZ4Compressor
  # Options: LZ4Compressor (fast), SnappyCompressor, ZstdCompressor (best ratio)
```

### 3.3 SSTable Compression

```sql
-- Compression is per-table and enabled by default.
-- Reduces disk usage and I/O at the cost of CPU.

-- LZ4 (default): fastest compression/decompression
CREATE TABLE fast_reads (
    id uuid PRIMARY KEY,
    data text
) WITH compression = {
    'class': 'LZ4Compressor',
    'chunk_length_in_kb': 16     -- larger chunks = better ratio, slower random reads
};

-- Zstd (Cassandra 4.0+): best compression ratio
CREATE TABLE cold_storage (
    id uuid PRIMARY KEY,
    data text
) WITH compression = {
    'class': 'ZstdCompressor',
    'compression_level': 3       -- 1 (fast) to 19 (max compression)
};

-- Snappy: balanced (legacy default)
CREATE TABLE balanced (
    id uuid PRIMARY KEY,
    data text
) WITH compression = {
    'class': 'SnappyCompressor'
};

-- Disable compression (rare; only for already-compressed data like images)
CREATE TABLE uncompressed (
    id uuid PRIMARY KEY,
    data blob
) WITH compression = {'enabled': false};

-- Check compression ratio:
-- nodetool tablestats <ks>.<table> | grep "Compression ratio"
-- Target: < 0.5 (50% of original size)
```

### 3.4 Disk Access Mode

```yaml
# cassandra.yaml
disk_access_mode: auto
# auto:   Cassandra chooses (usually mmap for reads)
# mmap:   memory-mapped I/O (best for SSDs with large page cache)
# standard: standard I/O (use if mmap causes issues)
# mmap_index_only: mmap only the index files

# For Cassandra 4.0+:
# disk_access_mode is simplified; mmap is used for SSTable reads.
# The file_cache (chunk cache) replaces explicit mmap configuration.
```

---

## 4. Compaction Tuning

### 4.1 SizeTieredCompactionStrategy (STCS)

```sql
-- Default strategy. Good for write-heavy workloads.
-- Compacts SSTables of similar size together.

CREATE TABLE write_heavy (
    id uuid PRIMARY KEY,
    data text
) WITH COMPACTION = {
    'class': 'SizeTieredCompactionStrategy',
    'min_threshold': 4,       -- min SSTables of similar size to trigger (default: 4)
    'max_threshold': 32,      -- max SSTables to compact at once (default: 32)
    'min_sstable_size': 50,   -- ignore SSTables smaller than this (MB)
    'bucket_low': 0.5,        -- lower bound for "similar size" (50% of average)
    'bucket_high': 1.5        -- upper bound for "similar size" (150% of average)
};

-- Pros:
--   Low write amplification (writes are cheap).
--   Good for burst-write workloads.
-- Cons:
--   Requires ~50% free disk space for compaction.
--   Read latency varies (many SSTables to check).
--   Tombstone purging is less predictable.
```

### 4.2 LeveledCompactionStrategy (LCS)

```sql
-- Best for read-heavy workloads. Guarantees bounded SSTable count.
-- Organizes SSTables into levels; each level is 10x the size of the previous.

CREATE TABLE read_heavy (
    id uuid PRIMARY KEY,
    data text
) WITH COMPACTION = {
    'class': 'LeveledCompactionStrategy',
    'sstable_size_in_mb': 160,     -- target SSTable size per level (default: 160)
    'fanout_size': 10              -- size multiplier between levels (default: 10)
};

-- Pros:
--   Consistent read latency (bounded SSTables per partition).
--   Only ~10% free disk overhead.
--   Efficient tombstone purging.
-- Cons:
--   HIGH write amplification (each write may be rewritten 5-10x across levels).
--   Not suitable for write-heavy workloads (compaction I/O overwhelms writes).
```

### 4.3 TimeWindowCompactionStrategy (TWCS)

```sql
-- Best for time-series data with TTL.
-- Groups SSTables by time window. Expired windows are dropped as files.

CREATE TABLE time_series (
    metric text,
    bucket text,
    ts timestamp,
    value double,
    PRIMARY KEY ((metric, bucket), ts)
) WITH COMPACTION = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'HOURS',   -- MINUTES, HOURS, DAYS
    'compaction_window_size': 1,         -- 1 hour windows
    'timestamp_resolution': 'MICROSECONDS',
    'expired_sstable_check_frequency_seconds': 600  -- check every 10 min
}
AND default_time_to_live = 604800;  -- 7 days

-- Rule of thumb: compaction_window = TTL / 20 to TTL / 30
-- Example: TTL = 7 days -> window = 6-8 hours

-- Pros:
--   Extremely efficient TTL expiry (drop whole SSTables, no compaction I/O).
--   Low write amplification within each window.
-- Cons:
--   Out-of-order writes (late data) create SSTables in old windows,
--   preventing efficient compaction.
--   Not suitable for tables without TTL.
```

### 4.4 UnifiedCompactionStrategy (Cassandra 5.0)

```sql
-- UCS automatically adapts its behavior based on workload.
-- Replaces the need to manually choose STCS/LCS/TWCS.

CREATE TABLE adaptive (
    id uuid PRIMARY KEY,
    data text
) WITH COMPACTION = {
    'class': 'UnifiedCompactionStrategy',
    'scaling_parameters': 'T4'   -- default auto-scaling
};

-- scaling_parameters values:
-- T2: tiered (STCS-like, very write-friendly)
-- T4: tiered (default, balanced)
-- L4: leveled (LCS-like, read-friendly)
-- L10: leveled (aggressive read optimization)
-- N: number-based (TWCS-like for time-series)

-- UCS can also be configured to change strategy per level:
-- 'scaling_parameters': 'T4, L10'
-- Level 0-1: tiered (write-friendly for incoming data)
-- Level 2+: leveled (read-friendly for settled data)
```

### 4.5 Compaction Throttling

```yaml
# cassandra.yaml
compaction_throughput_mb_per_sec: 64   # max MB/s for compaction I/O

# Runtime adjustment (no restart needed):
# nodetool setcompactionthroughput <MB/s>

# Concurrent compaction threads:
concurrent_compactors: 2
# Default: min(number of disks, number of cores).
# Increase for JBOD setups with many disks.
# Decrease if compaction starves reads/writes of I/O.
```

### 4.6 Monitoring Compaction

```bash
# Active compactions
nodetool compactionstats
# pending tasks: number waiting
# Each row shows: type, keyspace, table, progress

# Compaction history
nodetool compactionhistory

# SSTable count (high count = compaction not keeping up)
nodetool tablestats <ks>.<table> | grep "SSTable count"
# LCS: should be few SSTables per level
# STCS: grows until threshold triggers compaction

# Per-table compaction settings
nodetool tablestats <ks>.<table> | grep -i compaction
```

---

## 5. Caching

### 5.1 Table-Level Cache Configuration

```sql
-- Full caching (keys + rows): small, read-heavy lookup tables
CREATE TABLE config (
    key text PRIMARY KEY,
    value text
) WITH caching = {'keys': 'ALL', 'rows_per_partition': 'ALL'};

-- Key-only caching (default, recommended for most tables)
CREATE TABLE orders (
    order_id uuid PRIMARY KEY,
    total decimal
) WITH caching = {'keys': 'ALL', 'rows_per_partition': 'NONE'};

-- Partial row caching: cache first N rows per partition
CREATE TABLE recent_events (
    user_id text,
    event_time timestamp,
    data text,
    PRIMARY KEY (user_id, event_time)
) WITH caching = {'keys': 'ALL', 'rows_per_partition': '50'}
  AND CLUSTERING ORDER BY (event_time DESC);
-- Caches the 50 most recent events per user.
```

### 5.2 Cache Monitoring

```bash
# Overall cache stats
nodetool info | grep -E "Cache"

# Example:
# Key Cache     : entries 150234, size 45.2 MiB, capacity 256 MiB, 95234 hits, 4012 requests, 0.958 recent hit rate, 14400 save period in seconds
# Row Cache     : entries 0, size 0 bytes, capacity 0 bytes, 0 hits, 0 requests, NaN recent hit rate, 0 save period in seconds
# Counter Cache : entries 0, size 0 bytes, capacity 50 MiB, 0 hits, 0 requests, NaN recent hit rate, 7200 save period in seconds

# Target hit rates:
# Key Cache: > 85%
# Row Cache: > 95% (if enabled; otherwise it's not worth the heap cost)

# Resize caches at runtime:
nodetool setcachecapacity <key_cache_mb> <row_cache_mb> <counter_cache_mb>
nodetool setcachecapacity 512 0 50
```

### 5.3 Bloom Filters

```sql
-- Bloom filters reduce unnecessary disk reads.
-- Each SSTable has a bloom filter that answers:
-- "Is this partition key DEFINITELY NOT in this SSTable?"

-- Adjust false positive rate per table:
CREATE TABLE high_read (
    id uuid PRIMARY KEY,
    data text
) WITH bloom_filter_fp_chance = 0.01;
-- Lower = fewer false positives = more memory used
-- Default: 0.01 (1%) for SizeTiered; 0.1 (10%) for Leveled

-- Monitor bloom filter effectiveness:
-- nodetool tablestats <ks>.<table> | grep "Bloom"
-- "Bloom filter false positives" should be << "Bloom filter space used"
```

---

## 6. Query Optimization

### 6.1 Partition Key Access (Fastest)

```sql
-- ALWAYS include the full partition key in the WHERE clause.
-- This is the only truly efficient query pattern in Cassandra.

SELECT * FROM orders WHERE order_id = 550e8400-e29b-41d4-a716-446655440000;

-- Composite partition key: both parts required
SELECT * FROM metrics
WHERE metric_name = 'cpu_usage' AND bucket = '2026-05-22';
```

### 6.2 Clustering Column Queries

```sql
-- Clustering columns enable range queries WITHIN a partition.

-- Exact match on clustering column
SELECT * FROM metrics
WHERE metric_name = 'cpu' AND bucket = '2026-05-22'
  AND ts = '2026-05-22T14:30:00Z';

-- Range query on clustering column (efficient: scans within one partition)
SELECT * FROM metrics
WHERE metric_name = 'cpu' AND bucket = '2026-05-22'
  AND ts >= '2026-05-22T14:00:00Z'
  AND ts <= '2026-05-22T15:00:00Z';

-- LIMIT for efficiency
SELECT * FROM metrics
WHERE metric_name = 'cpu' AND bucket = '2026-05-22'
ORDER BY ts DESC
LIMIT 100;
```

### 6.3 Avoid ALLOW FILTERING

```sql
-- ALLOW FILTERING causes a full cluster scan. NEVER use in production.

-- BAD: full scan
SELECT * FROM users WHERE age > 25 ALLOW FILTERING;

-- GOOD: create a query-specific table
CREATE TABLE users_by_age (
    age int,
    user_id uuid,
    name text,
    PRIMARY KEY (age, user_id)
);
SELECT * FROM users_by_age WHERE age = 25;

-- GOOD (Cassandra 5.0+): use SAI index
CREATE INDEX ON users (age) USING 'sai';
SELECT * FROM users WHERE age > 25;
-- SAI handles range queries efficiently without full scan.
```

### 6.4 Prepared Statements

```python
# Python driver: ALWAYS use prepared statements for repeated queries.
# Benefits:
# 1. Query is parsed and validated ONCE on the server.
# 2. Only the bound values are sent on subsequent executions.
# 3. Token-aware routing is automatic.

from cassandra.cluster import Cluster

cluster = Cluster(['10.0.1.1'])
session = cluster.connect('ecommerce')

# Prepare once at startup
get_order = session.prepare("SELECT * FROM orders WHERE order_id = ?")

# Execute many times with different values
order = session.execute(get_order, [order_id])
```

### 6.5 Paging

```sql
-- Always use paging for large result sets.
-- Default page size: 5000 rows.

-- cqlsh:
PAGING ON;
SELECT * FROM large_table WHERE partition_key = 'value';

-- Driver-level paging (Python):
-- from cassandra.query import SimpleStatement
-- stmt = SimpleStatement("SELECT * FROM ...", fetch_size=1000)
-- results = session.execute(stmt)
-- for row in results:  # automatically fetches next page
--     process(row)
```

### 6.6 Token-Aware Queries

```python
# The driver sends queries directly to the node owning the partition.
# This avoids an extra network hop through a coordinator.

from cassandra.cluster import Cluster
from cassandra.policies import TokenAwarePolicy, DCAwareRoundRobinPolicy

cluster = Cluster(
    contact_points=['10.0.1.1'],
    load_balancing_policy=TokenAwarePolicy(
        DCAwareRoundRobinPolicy(local_dc='us-east-1')
    )
)
# With prepared statements, the driver knows the partition key
# and routes directly to the owning node.
```

---

## 7. Write Path Tuning

### 7.1 Write Path Overview

```
Client write request
  --> Coordinator node
    --> Commitlog (sequential write, fsync based on commitlog_sync)
    --> Memtable (in-memory sorted structure)
    --> Acknowledge to client (write is "durable")
    ...later...
    --> Memtable flush to SSTable on disk (when memtable is full)
    --> Compaction (merge SSTables periodically)
```

### 7.2 Tuning Write Throughput

```yaml
# cassandra.yaml

# Increase concurrent writers
concurrent_writes: 32
# Default: 8 * number of disks.
# Increase for SSDs which handle high parallelism.

# Increase memtable space (delays flushes, batches more writes)
memtable_heap_space_in_mb: 4096

# Use periodic commitlog sync (higher throughput, small durability window)
commitlog_sync: periodic
commitlog_sync_period_in_ms: 10000

# Increase commitlog space (prevents blocking writes during flush)
commitlog_total_space_in_mb: 8192

# Batch writes at the driver level (unlogged batches for throughput)
# UNLOGGED BATCH does not use the batch log coordinator.
# Use for bulk-inserting into the SAME partition.
```

### 7.3 Write Consistency vs. Performance

```sql
-- ONE: fastest writes (single replica ACK)
CONSISTENCY ONE;
INSERT INTO metrics (metric, ts, value) VALUES ('cpu', now(), 72.5);

-- LOCAL_QUORUM: balanced (quorum in local DC)
CONSISTENCY LOCAL_QUORUM;
INSERT INTO orders (order_id, total) VALUES (uuid(), 99.99);

-- ALL: slowest (every replica must ACK)
-- NEVER use for write-heavy workloads.
```

---

## 8. Read Path Tuning

### 8.1 Read Path Overview

```
Client read request
  --> Coordinator node
    --> Determine replica(s) based on CL
    --> Send read to replica(s)
      --> Check row cache (if enabled)
      --> Check bloom filter (per SSTable: "is key possibly here?")
      --> Check partition key cache (byte offset of partition in SSTable)
      --> Check partition summary (sparse index of partition positions)
      --> Check partition index (exact byte offset)
      --> Read data from SSTable (compressed chunk from disk or page cache)
      --> Merge data from memtable + all SSTables
    --> Coordinator reconciles responses (if multiple replicas)
    --> Return to client
```

### 8.2 Reducing Read Latency

```yaml
# cassandra.yaml

# Increase concurrent readers
concurrent_reads: 32
# Default: 16 * number of disks.
# Increase for SSDs.

# Speculative retry (send a second read if first is slow)
# Configured per-table:
# CREATE TABLE ... WITH speculative_retry = '99percentile';
# Options: NONE, ALWAYS, Xpercentile, Xms

# Increase key cache (avoid partition index reads)
key_cache_size_in_mb: 512

# Increase file cache (off-heap SSTable cache)
file_cache_size_in_mb: 2048
```

### 8.3 Read Consistency vs. Performance

```sql
-- ONE: fastest reads (single replica, may be stale)
CONSISTENCY ONE;
SELECT * FROM metrics WHERE metric = 'cpu' AND bucket = '2026-05-22';

-- LOCAL_QUORUM: balanced (quorum in local DC, strong consistency)
CONSISTENCY LOCAL_QUORUM;
SELECT * FROM orders WHERE order_id = ?;

-- ALL: slowest (every replica must respond)
-- Only use for critical reads where absolute consistency is required.
```

### 8.4 Tombstone Management

```yaml
# cassandra.yaml
# Tombstones are markers for deleted data. They must be scanned during reads.
# Too many tombstones degrade read performance significantly.

# gc_grace_seconds: how long tombstones are kept before compaction removes them.
# Default: 864000 (10 days)
# Must be greater than max_hint_window (3 hours) + repair interval.

# Per-table override:
# ALTER TABLE events WITH gc_grace_seconds = 259200;  -- 3 days (aggressive)

# Tombstone warnings in cassandra.yaml:
tombstone_warn_threshold: 1000    # warn if a read scans > 1000 tombstones
tombstone_failure_threshold: 100000  # fail the read above this count
```

---

## 9. Network Tuning

### 9.1 Internode Communication

```yaml
# cassandra.yaml

# Internode compression
internode_compression: dc
# dc: compress only cross-DC (recommended; saves WAN bandwidth, no CPU overhead on LAN)
# all: compress everything (use if network is the bottleneck even on LAN)
# none: no compression

# Streaming throughput (bootstrap, repair, rebuild)
stream_throughput_outbound_megabits_per_sec: 200
inter_dc_stream_throughput_outbound_megabits_per_sec: 50

# Internode send/receive buffer (4.0+ multiplexed connections)
internode_application_send_queue_capacity_in_bytes: 4194304    # 4 MB
internode_application_receive_queue_capacity_in_bytes: 4194304
```

### 9.2 Native Transport (Client Connections)

```yaml
# cassandra.yaml
native_transport_max_threads: 128    # max threads for client requests
# Increase for high client connection counts

native_transport_max_frame_size_in_mb: 256  # max CQL frame size
# Increase if sending large blobs

native_transport_max_concurrent_connections: -1  # unlimited (default)
# Set a limit if you need to protect the node from connection floods

# Backpressure (4.0+):
native_transport_allow_older_protocols: true  # backward compatibility
```

### 9.3 Client Driver Tuning

```python
# Python driver connection pool settings
from cassandra.cluster import Cluster
from cassandra.policies import (
    TokenAwarePolicy,
    DCAwareRoundRobinPolicy,
    ConstantReconnectionPolicy
)

cluster = Cluster(
    contact_points=['10.0.1.1', '10.0.1.2', '10.0.1.3'],
    load_balancing_policy=TokenAwarePolicy(
        DCAwareRoundRobinPolicy(local_dc='us-east-1')
    ),
    protocol_version=5,          # native protocol v5 (Cassandra 4.0+)
    reconnection_policy=ConstantReconnectionPolicy(delay=5.0),
    # Connection pool: 1 connection per host by default
    # Each connection handles up to 32768 concurrent requests (protocol v5)
)
```

---

## 10. OS-Level Tuning

### 10.1 Linux Kernel Settings

```bash
# /etc/sysctl.conf

# Virtual memory: minimize swapping
vm.swappiness = 1                    # almost never swap
vm.dirty_background_ratio = 5        # start flushing dirty pages at 5%
vm.dirty_ratio = 80                  # hard limit for dirty pages
vm.min_free_kbytes = 1048576         # keep 1 GB free for kernel (adjust to RAM)

# Network tuning
net.core.somaxconn = 65535           # max connection backlog
net.core.rmem_max = 16777216         # max receive buffer 16 MB
net.core.wmem_max = 16777216         # max send buffer 16 MB
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_max_syn_backlog = 65535

# Apply: sysctl -p
```

### 10.2 File Descriptor and Process Limits

```bash
# /etc/security/limits.conf
cassandra  soft  nofile  1048576
cassandra  hard  nofile  1048576
cassandra  soft  nproc   32768
cassandra  hard  nproc   32768
cassandra  soft  memlock unlimited
cassandra  hard  memlock unlimited
cassandra  soft  as      unlimited
cassandra  hard  as      unlimited

# Verify after Cassandra starts:
cat /proc/$(pgrep -f CassandraDaemon)/limits | grep "Max open files"
```

### 10.3 I/O Scheduler

```bash
# For SSDs: use 'none' (noop) or 'mq-deadline'
echo none > /sys/block/nvme0n1/queue/scheduler

# For HDDs (not recommended for production): use 'mq-deadline'
echo mq-deadline > /sys/block/sda/queue/scheduler

# Read-ahead: reduce for SSDs (random I/O is cheap)
blockdev --setra 8 /dev/nvme0n1    # 4 KB read-ahead for SSD
# Default (128 = 64 KB) is too high for SSD random reads.
```

### 10.4 NUMA Configuration

```bash
# For multi-socket servers, pin Cassandra to one NUMA node
# to avoid cross-socket memory access latency.

numactl --interleave=all cassandra
# Or in systemd service:
# [Service]
# ExecStart=/usr/bin/numactl --interleave=all /usr/sbin/cassandra
```

---

## 11. Benchmarking

### 11.1 cassandra-stress

```bash
# Built-in benchmarking tool

# Write test: insert 1 million rows
cassandra-stress write n=1000000 -rate threads=64 \
  -node 10.0.1.1 -mode native cql3

# Read test: read 1 million rows
cassandra-stress read n=1000000 -rate threads=64 \
  -node 10.0.1.1 -mode native cql3

# Mixed workload: 50% reads, 50% writes
cassandra-stress mixed ratio\(write=1,read=1\) n=1000000 \
  -rate threads=64 -node 10.0.1.1

# Custom schema stress test:
cassandra-stress user profile=my_schema.yaml n=1000000 \
  ops\(insert=1,read=1\) -rate threads=64

# Output metrics:
# Op rate (ops/sec)
# Partition rate (partitions/sec)
# Latency mean/median/95th/99th/max
```

### 11.2 Custom Stress Profile

```yaml
# my_schema.yaml
keyspace: benchmark
table: sensor_data

columnspec:
  - name: sensor_id
    size: fixed(16)
    population: uniform(1..100000)
  - name: ts
    cluster: uniform(1..1000)
  - name: value
    size: fixed(8)

insert:
  partitions: fixed(1)
  batchtype: UNLOGGED
  select: fixed(1)/1000

queries:
  read:
    cql: SELECT * FROM sensor_data WHERE sensor_id = ? LIMIT 100
    fields: samerow
```

### 11.3 Interpreting Results

```bash
# Key metrics from cassandra-stress output:

# Op rate: operations per second (higher = better)
# Partition rate: partitions accessed per second
# Row rate: rows read/written per second
# Latency mean: average latency (not useful for production targets)
# Latency 95th: 95% of requests below this (useful target)
# Latency 99th: 99% of requests below this (SLA target)
# Latency max: worst case (can be GC pauses or compaction spikes)

# Production targets (per-node):
# Writes: p99 < 10ms
# Reads:  p99 < 20ms (for partition key lookups)
# Throughput: 10-50K ops/sec per node (depends on data model and hardware)
```

---

## 12. Cassandra 4.x/5.x Performance Features

### 12.1 Cassandra 4.0

- **Zero-Copy Streaming**: 5x faster bootstrap and repair via direct SSTable transfer.
- **Internode messaging v4**: single multiplexed connection per peer reduces connection overhead.
- **Improved incremental repair**: better SSTable tracking, less anti-compaction overhead.
- **Virtual tables**: monitor system state via CQL without JMX overhead.
- **Full query logging**: capture and replay for performance analysis.

### 12.2 Cassandra 4.1

- **Guardrails**: prevent performance-killing queries (large IN clauses, ALLOW FILTERING).
- **Top partitions**: `nodetool toppartitions` identifies hot partitions in real time.
- **Pluggable memtable**: custom memtable implementations for specialized workloads.

### 12.3 Cassandra 5.0

- **Unified Compaction Strategy**: auto-adapts compaction to workload patterns.
- **Trie-indexed SSTables**: faster partition lookups with smaller memory footprint.
- **Storage Attached Indexes (SAI)**: efficient secondary indexes without ALLOW FILTERING.
- **Accord protocol**: faster lightweight transactions (replaces Paxos).
- **ZGC support** (experimental): sub-millisecond GC pauses.
- **Vector search**: ANN queries via SAI for ML/recommendation workloads.

```bash
# Check if trie indexes are enabled (5.0)
nodetool tablestats <ks>.<table> | grep "index"

# Check SAI index stats
nodetool tablestats <ks>.<table> | grep -i "sai"

# Monitor UCS behavior
nodetool compactionstats
```

---

## 13. Troubleshooting

### 13.1 High p99 Read Latency

**Symptom**: p99 read latency > 50ms despite SSDs.

**Diagnosis**:
```bash
# Check GC pauses
grep "GC pause" /var/log/cassandra/gc.log | awk '{print $NF}' | sort -n | tail -5

# Check SSTable count (too many = slow reads)
nodetool tablestats <ks>.<table> | grep "SSTable count"

# Check tombstones per read
nodetool tablestats <ks>.<table> | grep "tombstones"

# Check bloom filter false positives
nodetool tablestats <ks>.<table> | grep "Bloom filter false positives"

# Check large partitions
nodetool tablestats <ks>.<table> | grep "Compacted partition maximum"
```

**Fixes**:
- High SSTable count: increase compaction throughput or switch to LCS.
- High tombstones: reduce gc_grace_seconds, fix DELETE-heavy patterns.
- Bloom filter FP: lower bloom_filter_fp_chance (e.g., 0.001).
- Large partitions: redesign partition key with bucketing.

### 13.2 Write Latency Spikes

**Symptom**: periodic spikes in write latency (every few minutes).

**Cause**: usually memtable flushes or compaction competing for disk I/O.

**Fix**:
```yaml
# Separate commitlog and data disks
commitlog_directory: /ssd1/commitlog
data_file_directories:
  - /ssd2/data

# Reduce compaction impact during writes
compaction_throughput_mb_per_sec: 32   # lower during peak
# nodetool setcompactionthroughput 32

# Increase memtable space to flush less frequently
memtable_heap_space_in_mb: 4096
```

### 13.3 Compaction Not Keeping Up

**Symptom**: pending compaction tasks growing over time.

**Fix**:
```bash
# Check compaction stats
nodetool compactionstats

# Increase throughput
nodetool setcompactionthroughput 128

# Increase concurrent compactors (if JBOD)
# cassandra.yaml: concurrent_compactors: 4

# Consider switching compaction strategy:
# STCS -> LCS for read-heavy tables
# STCS -> TWCS for time-series with TTL
# Any -> UCS on Cassandra 5.0
```

### 13.4 OOM During Large Partition Read

**Symptom**: `OutOfMemoryError` when reading a specific partition.

**Fix**:
```bash
# Identify the large partition
nodetool tablestats <ks>.<table> | grep "Compacted partition maximum"

# If partition is > 100 MB, redesign with bucketing

# Temporary mitigation: limit rows returned
# SELECT * FROM table WHERE pk = ? LIMIT 1000;

# Increase heap (temporary, not a real fix)
# -Xmx24G (up from 16G)
```

### 13.5 Node Takes Hours to Bootstrap

**Symptom**: new node joins ring but bootstrap streaming takes > 12 hours.

**Fix**:
```yaml
# Increase streaming throughput
stream_throughput_outbound_megabits_per_sec: 400
# For cross-DC:
inter_dc_stream_throughput_outbound_megabits_per_sec: 100

# Consider using nodetool rebuild instead of auto-bootstrap
# (reads full SSTables, faster than Merkle-tree-based streaming)
```

### 13.6 Key Cache Hit Rate Below 50%

**Symptom**: key cache hit rate is low; every read goes to disk.

**Fix**:
```bash
# Increase key cache size
nodetool setcachecapacity 1024 0 50

# Check if the table has too many SSTables (each has its own key cache entries)
nodetool tablestats <ks>.<table> | grep "SSTable count"

# A high SSTable count fragments the key cache. Compact to reduce SSTables.
nodetool compact <ks> <table>
```

### 13.7 High CPU From Compaction

**Symptom**: CPU utilization is 90%+, mostly from compaction threads.

**Fix**:
```bash
# Throttle compaction
nodetool setcompactionthroughput 32

# Reduce concurrent compactors
# cassandra.yaml: concurrent_compactors: 1

# If using LCS with high write throughput, consider switching to STCS or UCS
```

### 13.8 Slow Queries in Debug Log

**Symptom**: `Slow query` messages in debug.log for specific tables.

**Fix**:
```bash
# Analyze the slow query
grep "Slow query" /var/log/cassandra/debug.log | tail -20

# Common causes:
# 1. ALLOW FILTERING -- redesign query
# 2. Large partition -- add bucketing
# 3. Range scan without LIMIT -- add LIMIT
# 4. Secondary index on high-cardinality column -- use SAI or query table
```

### 13.9 Frequent Memtable Flushes

**Symptom**: memtable flushes every few seconds; high disk write volume.

**Fix**:
```yaml
# Increase memtable space
memtable_heap_space_in_mb: 4096

# Reduce number of tables (each table has its own memtable)
# Consolidate if possible

# Use offheap memtables to reduce GC pressure
memtable_allocation_type: offheap_buffers
```

### 13.10 Speculative Retry Causing Double Reads

**Symptom**: read throughput doubles because speculative retries fire too aggressively.

**Fix**:
```sql
-- Increase speculative retry threshold
ALTER TABLE orders WITH speculative_retry = '99percentile';
-- Or disable:
ALTER TABLE orders WITH speculative_retry = 'NONE';

-- Monitor speculative retry rate:
-- nodetool tablestats <ks>.<table> | grep "speculative"
```

---

## 14. FAQ

### Q1: How much RAM should I allocate to the JVM heap?

8-16 GB for most workloads. Never exceed 31 GB (compressed oops threshold). The remaining RAM should be left for the OS page cache, which speeds up SSTable reads. On a 64 GB machine: 16 GB heap, ~48 GB for page cache.

### Q2: SSD or HDD?

SSDs are strongly recommended for production. Cassandra's read path involves random I/O (bloom filter, index, data lookups), which is orders of magnitude faster on SSDs. Use NVMe for best performance. HDDs are only acceptable for cold archival data with very low read rates.

### Q3: Why is my read latency high even though CPU and disk are fine?

Common causes: (1) Too many SSTables per partition (compaction lag). (2) Large partitions causing heap pressure. (3) Tombstone accumulation. (4) Bloom filter false positives. (5) OS page cache thrashing (insufficient free RAM). Check each with `nodetool tablestats`.

### Q4: Should I use RAID for Cassandra data disks?

No. Use JBOD (Just a Bunch of Disks) or individual disks. Cassandra handles data redundancy via replication. RAID adds unnecessary overhead, and RAID-5/6 write penalty is particularly harmful.

### Q5: How do I reduce write amplification?

- Use STCS (lowest write amplification) or UCS with tiered parameters.
- Increase memtable size to write larger SSTables per flush.
- Use UNLOGGED BATCH for multi-row inserts to the same partition.
- Avoid LCS for write-heavy tables (5-10x write amplification).

### Q6: What is the impact of enabling compression?

Compression reduces disk I/O (fewer bytes to read/write) at the cost of CPU. With LZ4 (default), the CPU overhead is negligible on modern hardware. Compression typically improves both read and write performance because disk I/O is usually the bottleneck.

### Q7: How many tables is too many?

Each table has its own memtable, bloom filter, and SSTable files. More than 200 tables per node is considered excessive. Each table consumes ~1-2 MB of heap per flush cycle. Consolidate tables where possible.

### Q8: How do I tune for time-series workloads?

Use TWCS with TTL. Set `compaction_window = TTL / 20`. Bucket partition keys by time (hourly/daily). Keep partitions under 100 MB. Disable row cache. Use periodic commitlog sync.

### Q9: When should I run major compaction?

Rarely. Major compaction (nodetool compact) creates a single huge SSTable, which: (a) cannot be compacted further in STCS, (b) uses 2x disk space temporarily, (c) blocks other compaction. Use only for one-time tombstone purging. UCS/LCS handle this automatically.

### Q10: How do I profile a slow query?

Enable tracing:
```sql
TRACING ON;
SELECT * FROM orders WHERE order_id = ?;
TRACING OFF;
```
The trace shows time spent in each phase: bloom filter, key cache, partition index, data read, merge. Also use `nodetool tablehistograms` for per-table latency distributions.

### Q11: What is the UnifiedCompactionStrategy and when should I use it?

UCS (Cassandra 5.0) automatically adapts its behavior based on workload. It replaces the need to manually choose STCS/LCS/TWCS. Use it for new tables on Cassandra 5.0. For existing tables, migrate during a maintenance window after testing.

### Q12: How does speculative retry work?

When enabled, if a read to the primary replica takes longer than the configured threshold (e.g., 99th percentile of historical latency), Cassandra sends a second read to another replica. The first response wins. This reduces tail latency but increases read amplification. Tune per-table based on latency sensitivity.

---

*Questo documento fa parte del modulo 07 "NoSQL Cassandra" della Data Encyclopedia.*
