# Cassandra: Partitioning e Partitioner

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
1. Partition Concept
2. Partition Key Design
3. Partitioners
4. Token Ring and Token Calculation
5. Virtual Nodes (vnodes)
6. Rebalancing
7. Partition Size Management
8. Composite Partition Keys
9. Hot Partitions
10. Partitioning Internals
11. Cassandra 4.x/5.x Partitioning Features
12. Troubleshooting
13. FAQ

---

## 1. Partition Concept

### 1.1 What is a Partition

A partition is the fundamental unit of data distribution in Cassandra. All rows sharing the same partition key are stored together on the same node (and its replicas). The partition key determines:

- **Which node** stores the data (via consistent hashing).
- **Data locality**: all rows in a partition are physically co-located on disk.
- **Query efficiency**: reading within a partition is fast (sequential disk read); reading across partitions requires scatter-gather.

```sql
-- Single-column partition key
CREATE TABLE users (
    user_id uuid,             -- this IS the partition key
    name text,
    email text,
    PRIMARY KEY (user_id)
);
-- Each user_id maps to exactly one partition.
-- All data for a user is on one node.

-- Composite partition key (multi-column)
CREATE TABLE metrics (
    metric_name text,
    bucket text,
    ts timestamp,
    value double,
    PRIMARY KEY ((metric_name, bucket), ts)
    --          ^^^^^^^^^^^^^^^^^^^^^^  partition key (in double parens)
    --                                  ^^  clustering column
);
-- Partition = all rows with same (metric_name, bucket) pair.
-- ts is a clustering column: orders rows WITHIN the partition.
```

### 1.2 Partition vs. Row vs. Cell

```
Hierarchy:
  Keyspace
    └── Table
          └── Partition (defined by partition key)
                └── Row (defined by partition key + clustering columns)
                      └── Cell (column name + value + timestamp)

Example: CREATE TABLE messages (
    conversation_id text,     -- partition key
    message_id timeuuid,      -- clustering column
    body text,                -- regular column
    PRIMARY KEY (conversation_id, message_id)
);

Partition:  conversation_id = 'conv_42'
Row 1:      conversation_id = 'conv_42', message_id = uuid1, body = 'hello'
Row 2:      conversation_id = 'conv_42', message_id = uuid2, body = 'world'
Cell:       body of Row 1 = 'hello' (with timestamp 1716393600000)
```

### 1.3 Data Distribution via Consistent Hashing

```
1. The partition key is hashed using the configured partitioner
   (Murmur3 by default) to produce a TOKEN.
2. The token ring is divided among nodes, each owning a range of tokens.
3. The node owning the token range containing this token stores the partition.
4. Additional replicas are placed according to the replication strategy.

Token Ring (conceptual):

    Node A (tokens: -2^63 to -1000)
         \
          \---- Node B (tokens: -999 to 5000)
          |
          |---- Node C (tokens: 5001 to 2^63-1)
         /
    Node A

A partition key "user_42" → Murmur3 hash → token = 3456
→ falls in Node B's range → stored on Node B (+ replicas).
```

---

## 2. Partition Key Design

### 2.1 Design Principles

```
Rule 1: Every query MUST include the full partition key.
  Cassandra cannot efficiently query across partitions.
  Design your partition key around your query patterns.

Rule 2: Partition size should be 10-100 MB (max ~100K rows).
  Too small: excessive overhead (bloom filters, index entries per partition).
  Too large: slow reads, GC pressure, compaction issues, OOM risk.

Rule 3: Distribute data evenly across nodes.
  Avoid partition keys with high cardinality skew.
  Example: using "country" as partition key puts most data on the
  node owning the "US" or "CN" partition.

Rule 4: Avoid unbounded growth.
  A partition key like (user_id) with time-series data grows forever.
  Add a time bucket (user_id, day) to cap partition size.
```

### 2.2 Good Partition Key Examples

```sql
-- Time-series with daily bucketing
CREATE TABLE sensor_readings (
    sensor_id text,
    day text,             -- daily bucket prevents unbounded growth
    ts timestamp,
    value double,
    PRIMARY KEY ((sensor_id, day), ts)
);
-- Each partition: one sensor's data for one day.
-- ~86,400 rows per day at 1 reading/sec.
-- Well-bounded, even distribution.

-- User activity with monthly bucketing
CREATE TABLE user_activity (
    user_id uuid,
    month text,           -- '2026-05'
    activity_time timeuuid,
    description text,
    PRIMARY KEY ((user_id, month), activity_time)
);

-- E-commerce orders (single high-cardinality key)
CREATE TABLE orders (
    order_id uuid PRIMARY KEY,
    customer text,
    total decimal
);
-- UUIDs distribute evenly via hash.
-- Each partition = 1 row = very small (fine for lookup-by-ID pattern).
```

### 2.3 Bad Partition Key Examples

```sql
-- BAD: low-cardinality partition key
CREATE TABLE events (
    event_type text,         -- only 5-10 distinct values
    ts timestamp,
    data text,
    PRIMARY KEY (event_type, ts)
);
-- Result: 5-10 giant partitions. Extreme hot spots.

-- BAD: unbounded partition
CREATE TABLE logs (
    service_name text,       -- one partition per service
    ts timestamp,
    message text,
    PRIMARY KEY (service_name, ts)
);
-- Result: partitions grow forever. After months, each partition is GBs.

-- BAD: skewed distribution
CREATE TABLE orders_by_country (
    country text,            -- US has 100x more orders than Liechtenstein
    order_id uuid,
    PRIMARY KEY (country, order_id)
);
-- Result: massive "US" partition, tiny others. Uneven node load.
```

---

## 3. Partitioners

### 3.1 Murmur3Partitioner (Default)

```yaml
# cassandra.yaml
partitioner: org.apache.cassandra.dht.Murmur3Partitioner

# Token range: -2^63 to 2^63-1  (Long.MIN_VALUE to Long.MAX_VALUE)
# Hash function: Murmur3 (non-cryptographic, very fast, good distribution)
# Output: 64-bit signed integer

# Characteristics:
# - Uniform distribution across the token ring.
# - Deterministic: same key always maps to same token.
# - Non-reversible: cannot derive the key from the token.
# - Default since Cassandra 1.2+. ALWAYS use this.
```

### 3.2 RandomPartitioner (Legacy)

```yaml
# cassandra.yaml
partitioner: org.apache.cassandra.dht.RandomPartitioner

# Token range: 0 to 2^127-1
# Hash function: MD5 (128-bit, cryptographic -- slower than Murmur3)
# Output: BigInteger

# Legacy partitioner. No reason to use on new clusters.
# Existing clusters using RandomPartitioner cannot switch to Murmur3
# without a full data migration (export + reimport).
```

### 3.3 ByteOrderedPartitioner (Avoid)

```yaml
# cassandra.yaml
partitioner: org.apache.cassandra.dht.ByteOrderedPartitioner

# Token range: lexicographic byte order of the partition key
# NO hashing: the raw key bytes determine token order.

# This preserves key ordering, enabling range scans across partitions.
# BUT it causes severe problems:
# 1. Hot spots: sequential keys (timestamps, auto-increment IDs)
#    map to sequential tokens, concentrating load on one node.
# 2. Manual balancing: no automatic even distribution.
# 3. Operational nightmare: adding/removing nodes requires manual rebalancing.

# NEVER use ByteOrderedPartitioner.
# If you need ordered scans, use clustering columns within a partition.
```

### 3.4 Partitioner Comparison

| Partitioner | Hash | Range | Distribution | Use |
|------------|------|-------|-------------|-----|
| Murmur3Partitioner | Murmur3 (64-bit) | -2^63 to 2^63-1 | Uniform | Default; always use |
| RandomPartitioner | MD5 (128-bit) | 0 to 2^127-1 | Uniform | Legacy only |
| ByteOrderedPartitioner | None (raw bytes) | Byte order | Skewed | Never use |

---

## 4. Token Ring and Token Calculation

### 4.1 The Token Ring

```
The token ring is a circular number line from -2^63 to 2^63-1
(for Murmur3Partitioner). Each node owns one or more ranges
on this ring.

Without vnodes (single token per node, 3 nodes):
  Node A: token 0         → owns range (-2^63, 0]
  Node B: token 3074...   → owns range (0, 3074...]
  Node C: token 6148...   → owns range (3074..., 2^63-1]

With vnodes (256 tokens per node, 3 nodes):
  Each node owns 256 randomly distributed ranges.
  Ranges interleave across nodes for better distribution.
```

### 4.2 Determining Token for a Key

```sql
-- CQL function to find the token for a partition key
SELECT token(user_id), user_id, name FROM users;

-- Example output:
-- token(user_id)           | user_id                              | name
-- -7509452495886106294     | 550e8400-e29b-41d4-a716-446655440000 | alice
--  3456789012345678901     | 660e8400-e29b-41d4-a716-446655440001 | bob
-- This tells you which part of the ring (which node) owns each row.
```

```python
# Python: compute Murmur3 token for a key
# The actual Murmur3 implementation must match Cassandra's variant.
# Use the cassandra-driver's built-in token computation:

from cassandra.cluster import Cluster
from cassandra.metadata import Murmur3Token

cluster = Cluster(['10.0.1.1'])
metadata = cluster.metadata

# After connecting, the driver knows token-to-node mappings:
for token_range in metadata.token_map.ring:
    print(f"Token: {token_range.value}, Node: {metadata.token_map.get_replicas('myapp', token_range)}")
```

### 4.3 Token-to-Node Mapping

```bash
# View the full token ring
nodetool ring

# Example output:
# Address     Rack   Status  State   Load       Owns   Token
# 10.0.1.1    rack1  Up      Normal  15.2 GiB   33.3%  -9223372036854775808
# 10.0.1.2    rack2  Up      Normal  14.8 GiB   33.4%  -3074457345618258602
# 10.0.1.3    rack3  Up      Normal  15.0 GiB   33.3%  3074457345618258602

# Each row shows one token owned by a node.
# With vnodes (num_tokens=256), each node has 256 rows in this output.

# View token ranges owned by a node
nodetool describering ecommerce
# Shows which ranges map to which nodes, including replicas.
```

---

## 5. Virtual Nodes (vnodes)

### 5.1 What are vnodes

Without vnodes, each node owns a single contiguous range on the token ring. This causes problems:

- **Uneven distribution**: new nodes get one large range; splitting is manual.
- **Slow rebalancing**: adding/removing a node affects only its neighbors.
- **Long bootstrap**: one node must stream all data from one range.

With vnodes, each node owns many small, randomly distributed ranges:

```yaml
# cassandra.yaml
# Number of virtual nodes per physical node
num_tokens: 256   # default in Cassandra 3.x
num_tokens: 16    # recommended in Cassandra 4.x+ (with token allocation)

# Cassandra 4.0+ includes an improved token allocation algorithm
# that achieves better balance with fewer vnodes (16 vs. 256).
allocate_tokens_for_local_replication_factor: 3
```

### 5.2 vnodes vs. Single Token

| Feature | vnodes (num_tokens > 1) | Single Token (num_tokens = 1) |
|---------|------------------------|-------------------------------|
| Token assignment | Automatic (random) | Manual (calculate initial_token) |
| Data distribution | Even (many small ranges) | Depends on manual calculation |
| Bootstrap speed | Faster (parallel streaming from multiple nodes) | Slower (stream from 1-2 neighbors) |
| Rebalancing | Automatic on add/remove | Manual token recalculation |
| Token ring complexity | Many entries per node | One entry per node |
| Operational overhead | Lower | Higher |

### 5.3 num_tokens Values

```yaml
# Cassandra 3.x: num_tokens = 256 (default)
# Good distribution but noisy token ring (256 entries per node).

# Cassandra 4.0+: num_tokens = 16 (recommended)
# New token allocation algorithm achieves equivalent distribution
# with fewer tokens, reducing memory overhead and ring complexity.

# Cassandra 4.0+ optimal setup:
num_tokens: 16
allocate_tokens_for_local_replication_factor: 3
# The allocator considers existing token assignments
# and places new tokens to minimize imbalance.
```

### 5.4 Disabling vnodes (Single Token)

```yaml
# For manual token management (advanced, usually unnecessary):
num_tokens: 1
initial_token: <calculated_token>

# Calculate tokens for N nodes evenly:
# token_i = (i * 2^63 * 2 / N) - 2^63
# For 3 nodes:
# Node 0: initial_token = -9223372036854775808
# Node 1: initial_token = -3074457345618258603
# Node 2: initial_token = 3074457345618258602
```

---

## 6. Rebalancing

### 6.1 Automatic Rebalancing with vnodes

```bash
# With vnodes, adding or removing a node automatically rebalances
# the token ring. No manual intervention needed.

# Adding a node:
# 1. Start new node with same cluster_name and seeds.
# 2. It auto-bootstraps: receives ranges from multiple existing nodes.
# 3. After bootstrap, run cleanup on existing nodes.

# Adding a node:
cassandra    # start the new node
nodetool status    # monitor join progress (UJ -> UN)

# After bootstrap completes:
# Run cleanup on EXISTING nodes to remove data now owned by the new node
nodetool cleanup ecommerce   # on each existing node
```

### 6.2 Manual Token Movement (Single Token Mode)

```bash
# Move a node to a new token position
nodetool move <new_token>

# This streams data in/out of the node to match the new token assignment.
# Only works with num_tokens = 1.
# Rarely needed with vnodes.
```

### 6.3 Monitoring Rebalancing

```bash
# Check bootstrap/streaming progress
nodetool netstats

# Example output:
# Mode: NORMAL
# Receiving:
#   /10.0.1.1 1234567 bytes   53% complete
#   /10.0.1.3 987654 bytes    78% complete
# Nothing sending

# Check load balance after rebalancing
nodetool status
# All nodes should have roughly equal "Load" values.
# Minor differences are normal; > 20% skew warrants investigation.

# Check token ownership percentage
nodetool status
# "Owns" column should be ~equal for all nodes.
# With RF=3 and 3 nodes, each shows ~100% (each owns all data).
# With RF=3 and 6 nodes, each shows ~50%.
```

### 6.4 Cleanup After Topology Change

```bash
# After adding/removing nodes, run cleanup to remove orphaned data.
nodetool cleanup ecommerce

# cleanup scans all SSTables and removes data that no longer belongs
# to this node according to the new token ring.

# WARNING: cleanup creates new SSTables (rewritten without orphaned data).
# Ensure sufficient disk space (similar to compaction overhead).

# Run cleanup on all EXISTING nodes (not the new node).
# The new node already has only its own data from bootstrap.
```

---

## 7. Partition Size Management

### 7.1 Target Partition Size

```
Recommended: 10-100 MB per partition, max ~100K-200K rows.

Why these limits?
- Reads: a single partition is read into memory. Large partitions
  cause heap pressure and GC pauses.
- Compaction: large partitions slow down compaction because the
  entire partition must be held in memory during merge.
- Repair: Merkle tree resolution is per-partition. Giant partitions
  create large tree nodes that are expensive to compare.
- Streaming: bootstrap and repair stream data per-partition.
  Large partitions create large streaming messages.
```

### 7.2 Checking Partition Size

```bash
# Per-table partition size statistics
nodetool tablestats ecommerce.orders

# Key fields:
# Compacted partition minimum bytes: smallest partition on this node
# Compacted partition mean bytes: average partition size
# Compacted partition maximum bytes: LARGEST partition on this node
# Number of partitions (estimate): total partition count

# If "maximum bytes" > 100 MB, you likely have a hot/unbounded partition.

# Per-table histogram (more detail):
nodetool tablehistograms ecommerce.orders

# Shows distribution of partition sizes and row counts.
```

### 7.3 Identifying Large Partitions

```bash
# Cassandra 4.1+: top partitions
nodetool toppartitions ecommerce orders 5000
# Shows the most accessed partitions over 5000 ms.
# Useful for identifying both hot (frequently accessed) and
# large (slow to read) partitions.

# SSTable tools: scan SSTables for large partitions
sstableutil -e /data/cassandra/data/ecommerce/orders-*/
# Lists all SSTable files.

# Cassandra 4.0+ Guardrails:
# cassandra.yaml:
# guardrails:
#   partition_size_warn_threshold: 100MiB
#   partition_size_fail_threshold: 500MiB
# Logs a warning or rejects writes when a partition exceeds thresholds.
```

### 7.4 Fixing Large Partitions

```sql
-- Problem: unbounded partition
CREATE TABLE messages_v1 (
    conversation_id text,
    message_id timeuuid,
    body text,
    PRIMARY KEY (conversation_id, message_id)
);
-- A conversation with 10 million messages = multi-GB partition.

-- Fix: add time bucketing to the partition key
CREATE TABLE messages_v2 (
    conversation_id text,
    message_month text,    -- '2026-05'
    message_id timeuuid,
    body text,
    PRIMARY KEY ((conversation_id, message_month), message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);
-- Each partition: one conversation's messages for one month.
-- Much smaller, bounded partitions.

-- Fix: add synthetic bucketing for high-frequency data
CREATE TABLE events_v2 (
    event_type text,
    bucket int,            -- 0-99 (application hashes event_id % 100)
    ts timestamp,
    data text,
    PRIMARY KEY ((event_type, bucket), ts)
);
-- Distributes "event_type" across 100 sub-partitions.
```

### 7.5 Data Migration for Partition Redesign

```bash
# Option 1: COPY command (for small tables)
cqlsh -e "COPY ecommerce.messages_v1 TO '/tmp/messages.csv';"
# Transform CSV to add the new bucket column
cqlsh -e "COPY ecommerce.messages_v2 FROM '/tmp/messages_v2.csv';"

# Option 2: sstableloader (for large tables, no downtime)
# Export data, transform, create new SSTables, load with:
sstableloader -d 10.0.1.1 /path/to/new_sstables/ecommerce/messages_v2/

# Option 3: Application-level dual-write migration
# 1. Create the new table (messages_v2).
# 2. Update application to write to BOTH old and new tables.
# 3. Backfill old data from v1 to v2 using a batch job.
# 4. After backfill, switch reads to v2.
# 5. Stop writes to v1, drop v1 after verification.
```

---

## 8. Composite Partition Keys

### 8.1 Syntax

```sql
-- Single-column partition key
PRIMARY KEY (user_id)
-- user_id alone determines the partition.

-- Composite partition key (double parentheses)
PRIMARY KEY ((metric_name, bucket), ts)
-- (metric_name, bucket) together determine the partition.
-- ts is a clustering column within the partition.

-- Three-column composite partition key
PRIMARY KEY ((tenant_id, region, day), event_id)
-- All three columns are needed in the WHERE clause to query efficiently.
```

### 8.2 When to Use Composite Keys

```sql
-- Use case 1: Time bucketing (prevent unbounded partitions)
PRIMARY KEY ((sensor_id, day), ts)
-- Bounds partition to one day of data.

-- Use case 2: Multi-tenant isolation
PRIMARY KEY ((tenant_id, table_name), row_id)
-- Data for each tenant-table combo is co-located.

-- Use case 3: Geographic bucketing
PRIMARY KEY ((country, region), city, store_id)
-- Queries: all stores in a specific country+region.

-- Use case 4: Even distribution of hot keys
PRIMARY KEY ((user_id, shard), activity_time)
-- Shard = user_id.hashCode() % N (application-managed)
-- Distributes a hot user across N partitions.
```

### 8.3 Query Requirements

```sql
-- With composite partition key: ALL partition key columns are required in WHERE.

-- CORRECT: both partition key columns provided
SELECT * FROM metrics
WHERE metric_name = 'cpu' AND bucket = '2026-05-22';

-- CORRECT: partition key + clustering column range
SELECT * FROM metrics
WHERE metric_name = 'cpu' AND bucket = '2026-05-22'
  AND ts >= '2026-05-22T14:00:00Z'
  AND ts <= '2026-05-22T15:00:00Z';

-- WRONG: missing one partition key column
SELECT * FROM metrics WHERE metric_name = 'cpu';
-- Error: Cannot execute this query as it might involve data filtering
-- You MUST provide all partition key columns.

-- WRONG: only clustering column (no partition key)
SELECT * FROM metrics WHERE ts = '2026-05-22T14:30:00Z';
-- Error: partition key columns are required.
```

---

## 9. Hot Partitions

### 9.1 What Causes Hot Partitions

```
A hot partition receives disproportionate read/write traffic compared
to other partitions. Causes:

1. Natural skew: a viral social media post, a global "default" user,
   a "catch-all" event type.
2. Counter/aggregate patterns: a single global counter partition.
3. Current-time-bucket: if all writes go to "today's" partition,
   the node owning that partition is hot.
4. Low-cardinality partition key: only a few distinct values.
```

### 9.2 Detecting Hot Partitions

```bash
# Cassandra 4.1+: top partitions
nodetool toppartitions ecommerce orders 5000
# Shows partitions with the most reads/writes in the sample window.

# Check load balance
nodetool status
# If one node has significantly higher Load, it may own hot partitions.

# Check per-node latency
nodetool proxyhistograms
# If one node has much higher read/write latency, it's likely overloaded.

# JMX metric:
# org.apache.cassandra.metrics:type=Table,keyspace=<ks>,scope=<table>,name=CoordinatorReadLatency
# Compare across nodes.
```

### 9.3 Fixing Hot Partitions

```sql
-- Strategy 1: Add a synthetic shard to the partition key
-- Before (hot):
PRIMARY KEY (popular_user_id, ts)

-- After (distributed across N shards):
PRIMARY KEY ((popular_user_id, shard), ts)
-- Application sets shard = hash(event_id) % 16
-- Reads must query all 16 shards and merge client-side.

-- Strategy 2: Add time bucketing
-- Before (hot: all writes go to one partition per user):
PRIMARY KEY (user_id, ts)

-- After (bounded: one partition per user per day):
PRIMARY KEY ((user_id, day), ts)

-- Strategy 3: Use a random partition key for write-only tables
-- For logging/metrics where individual rows are not queried:
PRIMARY KEY (random_uuid)
-- Perfect distribution, but no range queries possible.
```

---

## 10. Partitioning Internals

### 10.1 SSTable On-Disk Layout

```
Each SSTable contains:
1. Data file (.db):     actual cell data, grouped by partition.
2. Partition index (.Index): maps partition keys to byte offsets in the data file.
3. Summary (.Summary):  sparse sample of partition index entries (in memory).
4. Bloom filter (.Filter): probabilistic structure to test partition key membership.
5. Compression info (.CompressionInfo): compression metadata per chunk.
6. Statistics (.Statistics): min/max token, tombstone count, etc.
7. TOC (.TOC):          table of contents listing all SSTable components.

Read path for a partition:
  Bloom filter → Summary → Partition index → Data file
  Each step narrows the byte offset until the exact partition data is found.
```

### 10.2 Partition Index Trie (Cassandra 5.0)

```
Cassandra 5.0 replaces the traditional partition index with a trie-based index:
- Trie (prefix tree) structure reduces memory footprint by 30-60%.
- Faster partition lookups (O(key_length) instead of binary search).
- Lower off-heap memory usage for large datasets.
- Transparent: no CQL or configuration change needed.

The trie index is enabled by default on Cassandra 5.0+.
```

### 10.3 Bloom Filter Internals

```
A bloom filter is a probabilistic data structure that answers:
"Is this partition key DEFINITELY NOT in this SSTable?"

- False positives are possible (says "maybe yes" when key is absent).
- False negatives are impossible (never says "no" when key IS present).

Tunable via bloom_filter_fp_chance:
- 0.01 (1%): default for STCS. Uses more memory per SSTable.
- 0.1 (10%): default for LCS. Uses less memory.
- 0.001 (0.1%): use for read-heavy tables where I/O is critical.

Each SSTable's bloom filter is loaded off-heap at startup.
Total bloom filter memory = sum across all SSTables.

# Check bloom filter effectiveness:
nodetool tablestats <ks>.<table>
# "Bloom filter false positives" should be << total reads.
# "Bloom filter false ratio" should be << bloom_filter_fp_chance.
```

### 10.4 Partition Summary

```
The partition summary is a sparse in-memory index of the partition index.
It contains every Nth entry of the partition index, where N is:

# cassandra.yaml
min_index_interval: 128      # sample every 128th entry (default)
max_index_interval: 2048     # adaptive: up to every 2048th entry

# Lower min_index_interval = more memory, faster lookups.
# Higher min_index_interval = less memory, more disk reads.

# For read-heavy workloads: min_index_interval: 64
# For write-heavy workloads: min_index_interval: 256
```

---

## 11. Cassandra 4.x/5.x Partitioning Features

### 11.1 Cassandra 4.0

- **Improved token allocation**: `allocate_tokens_for_local_replication_factor` enables better token distribution with fewer vnodes (16 instead of 256).
- **Zero-Copy Streaming**: 5x faster bootstrap when a new node joins and receives partitions from existing nodes.
- **Virtual tables**: query partition and token metadata via CQL.

```sql
-- Query token ranges via system_views (Cassandra 4.0+)
-- SELECT * FROM system.peers;  -- all known peers with tokens
-- SELECT * FROM system.local;  -- this node's tokens
```

### 11.2 Cassandra 4.1

- **Guardrails for partition size**: configurable warn/fail thresholds on partition size.
- **Top partitions**: `nodetool toppartitions` for real-time hot partition detection.

```yaml
# cassandra.yaml (4.1+)
guardrails:
  partition_size_warn_threshold: 100MiB
  partition_size_fail_threshold: 500MiB
  # Logs warning or rejects writes that would make a partition exceed threshold.

  partition_count_warn_threshold: 100
  partition_count_fail_threshold: 500
  # Warns/fails if a single query touches too many partitions.
```

### 11.3 Cassandra 5.0

- **Trie-based partition index**: 30-60% memory reduction for partition indexes, faster lookups.
- **Storage Attached Indexes (SAI)**: secondary indexes that avoid full partition scans. Enable queries on non-partition-key columns without ALLOW FILTERING.
- **Unified Compaction Strategy**: adapts compaction per partition access pattern.

```sql
-- SAI enables efficient queries without partition key (Cassandra 5.0+)
CREATE INDEX ON users (email) USING 'sai';
SELECT * FROM users WHERE email = 'alice@example.com';
-- No ALLOW FILTERING needed. SAI handles cross-partition lookup efficiently.

-- SAI with numeric range
CREATE INDEX ON products (price) USING 'sai';
SELECT * FROM products WHERE price >= 10.00 AND price <= 50.00;
```

---

## 12. Troubleshooting

### 12.1 Uneven Data Distribution

**Symptom**: `nodetool status` shows some nodes with 2-3x more data than others.

**Fix**:
```bash
# Check token ownership
nodetool status
# "Owns" should be roughly equal.

# If using num_tokens=256, switching to 16 with allocate_tokens:
# Only possible on a fresh cluster or after full data migration.

# If single-token mode: recalculate tokens for even distribution
# and use nodetool move.

# If partition key has natural skew: redesign partition key
# (add bucketing, sharding).
```

### 12.2 Large Partition Warnings in Logs

**Symptom**: `WARN  [CompactionExecutor] Compacting large partition <ks>.<table>:<key> (X bytes)`

**Fix**:
```bash
# Identify the partition key from the warning
# Check current partition size
nodetool tablestats <ks>.<table> | grep "Compacted partition maximum"

# Redesign table with time bucketing or synthetic sharding
# Migrate data (see Section 7.5)
```

### 12.3 Hot Partition Causing Node Overload

**Symptom**: one node has much higher CPU/latency than others.

**Fix**:
```bash
# Identify the hot partition
nodetool toppartitions <ks> <table> 5000   # 4.1+

# Apply sharding to the partition key (Section 9.3)
# Or use application-level caching to reduce reads to the hot partition.
```

### 12.4 Cannot Query Without Full Partition Key

**Symptom**: `InvalidQueryException: Cannot execute this query as it might involve data filtering`

**Fix**:
```sql
-- You MUST provide all partition key columns.
-- If your query pattern does not include the partition key,
-- you need a different table designed for that query.

-- Option 1: Create a query-specific table
CREATE TABLE users_by_email (
    email text PRIMARY KEY,
    user_id uuid
);

-- Option 2: Use SAI (Cassandra 5.0+)
CREATE INDEX ON users (email) USING 'sai';
SELECT * FROM users WHERE email = 'alice@example.com';

-- Option 3 (NEVER in production): ALLOW FILTERING
-- SELECT * FROM users WHERE email = 'alice@example.com' ALLOW FILTERING;
-- This scans ALL partitions. Performance disaster at scale.
```

### 12.5 OOM During Partition Read

**Symptom**: `OutOfMemoryError` when reading a specific partition.

**Fix**:
```bash
# The partition is too large to fit in memory.
# Check partition size:
nodetool tablestats <ks>.<table> | grep "Compacted partition maximum"

# Temporary: use LIMIT to read only part of the partition
# Permanent: redesign with bucketing (Section 7.4)
```

### 12.6 Token Range Scan Timeout

**Symptom**: `ReadTimeoutException` on range queries without specific partition key.

**Fix**:
```bash
# Range scans query ALL partitions on ALL nodes. Very expensive.
# Add pagination:
# LIMIT 100
# Use driver-level paging (default page size: 5000)

# Or redesign the query to include a partition key.
```

### 12.7 Cleanup Takes Too Long After Adding Node

**Symptom**: `nodetool cleanup` runs for hours.

**Fix**:
```bash
# Cleanup rewrites all SSTables, removing data not owned by the node.
# For large datasets, this is expected.

# Throttle to reduce impact:
nodetool setcompactionthroughput 64

# Run cleanup on one keyspace at a time:
nodetool cleanup ecommerce
# Then:
nodetool cleanup user_data
```

### 12.8 Wrong Partitioner Selected

**Symptom**: after misconfiguration, data distribution is skewed or Cassandra fails to start.

**Fix**:
```bash
# The partitioner is set at cluster creation and CANNOT be changed.
# If you set the wrong partitioner on a running cluster:
# Data is corrupted / unreadable with the wrong partitioner.

# Only fix: create a new cluster with the correct partitioner
# and migrate data using sstableloader or COPY.

# ALWAYS use Murmur3Partitioner.
```

### 12.9 nodetool ring Shows Unexpected Token Distribution

**Symptom**: tokens are clustered together instead of evenly distributed.

**Fix**:
```yaml
# Ensure allocate_tokens is configured (4.0+):
num_tokens: 16
allocate_tokens_for_local_replication_factor: 3

# This only affects NEW nodes joining the ring.
# Existing nodes keep their tokens.
# For a full rebalance, you must rebuild the cluster.
```

### 12.10 Partition Key Change Requires Data Migration

**Symptom**: need to change partition key design on a production table.

**Fix**:
```bash
# Cannot ALTER a table's primary key.
# Must create a new table with the new key design and migrate data.

# Recommended approach: dual-write migration (Section 7.5, Option 3)
# 1. Create new table
# 2. Application writes to both old and new
# 3. Backfill old data
# 4. Switch reads to new table
# 5. Drop old table
```

---

## 13. FAQ

### Q1: Can I change the partition key of an existing table?

No. The partition key is part of the PRIMARY KEY, which is immutable after table creation. You must create a new table with the desired key and migrate data.

### Q2: What is the maximum partition size?

There is no hard technical limit, but Cassandra starts to degrade above 100 MB per partition. Guardrails (4.1+) can set warn/fail thresholds. The practical maximum depends on available heap -- reading a multi-GB partition causes OOM.

### Q3: Can I use ALLOW FILTERING to query without the partition key?

Technically yes, but NEVER in production. It triggers a full cluster scan, reading every partition on every node. Use a query-specific table or SAI index instead.

### Q4: How do vnodes affect performance?

vnodes improve data distribution and operational simplicity (no manual token management). The performance impact is minimal. In Cassandra 4.0+, 16 vnodes with `allocate_tokens` provide optimal balance.

### Q5: Can I switch partitioners on an existing cluster?

No. The partitioner determines how existing data is distributed. Switching would make all existing data unreadable. Create a new cluster with the desired partitioner and migrate.

### Q6: What is the TOKEN() function in CQL?

`TOKEN(partition_key)` returns the Murmur3 hash of the partition key. It is useful for range scans across the token ring (e.g., for data export) but not for normal queries.

```sql
SELECT * FROM users WHERE TOKEN(user_id) > -9223372036854775808
  AND TOKEN(user_id) <= -3074457345618258603;
```

### Q7: How do I estimate partition size before inserting data?

Estimate: `partition_size = num_rows * (sum_of_column_sizes + 23_bytes_overhead_per_cell)`. For a table with 10 columns averaging 50 bytes each, a partition with 100K rows is approximately 100K * 523 bytes = ~52 MB.

### Q8: Should I prefer many small partitions or fewer large ones?

Many small partitions (within reason). Each partition adds a small overhead (bloom filter entry, partition index entry), but this is negligible compared to the problems of large partitions (OOM, slow compaction, repair bottlenecks).

### Q9: What is the Trie-based partition index in Cassandra 5.0?

A data structure that replaces the traditional B-tree-like partition index. Tries (prefix trees) exploit common prefixes in partition keys for 30-60% memory savings. Lookups are O(key_length) instead of O(log N). Enabled by default in Cassandra 5.0.

### Q10: How does SAI differ from the old secondary index?

Legacy secondary indexes create a local index per node, which becomes a scatter-gather on every query. SAI (Storage Attached Index) stores index data alongside SSTables and supports efficient range queries, multi-column predicates, and numeric/text filtering without ALLOW FILTERING.

### Q11: What does `allocate_tokens_for_local_replication_factor` do?

It tells Cassandra's token allocation algorithm to optimize token placement considering the replication factor. With RF=3, it ensures that adding a new node distributes tokens so that replicas are evenly spread across nodes. Only works with `num_tokens > 1`.

### Q12: How do I handle partition key design for multi-tenant systems?

Include `tenant_id` as the first component of the partition key. This ensures tenant data is co-located and isolates tenants from each other. Add time bucketing or other components to prevent unbounded partitions.

```sql
PRIMARY KEY ((tenant_id, entity_type, month), entity_id)
```

---

*Questo documento fa parte del modulo 07 "NoSQL Cassandra" della Data Encyclopedia.*
