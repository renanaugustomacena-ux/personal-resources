# Cassandra Architecture

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
1. Cassandra Overview
2. Data Model Fundamentals
3. CQL Essentials
4. Cluster Architecture
5. Write Path
6. Read Path
7. Replication and Consistency
8. Compaction
9. Gossip Protocol and Failure Detection
10. Cassandra Configuration
11. Cassandra 4.x/5.x Architecture Changes
12. Troubleshooting
13. FAQ

---

## 1. Cassandra Overview

### 1.1 What is Cassandra

Apache Cassandra is a distributed, wide-column NoSQL database designed for massive-scale workloads requiring high availability, linear scalability, and tunable consistency. Originally developed at Facebook for inbox search, open-sourced in 2008, and became a top-level Apache project in 2010.

### 1.2 Core Design Principles

- **Peer-to-peer architecture**: no master node, no single point of failure. Every node is identical.
- **Linear scalability**: doubling nodes approximately doubles throughput. No re-sharding needed.
- **Tunable consistency**: choose per-query from eventual to strong consistency.
- **Write-optimized**: writes go to an append-only commitlog and an in-memory memtable. No random disk I/O for writes.
- **Multi-datacenter replication**: built-in support for active-active replication across geographies.
- **Fault tolerant**: data is replicated to multiple nodes. The system continues operating during node, rack, or datacenter failures.

### 1.3 Where Cassandra Fits

| Strength | Weakness |
|----------|----------|
| Massive write throughput (100K+ ops/sec per node) | No JOINs; requires denormalized data models |
| Linear horizontal scaling | Limited ad-hoc query support |
| Multi-DC active-active | No multi-row ACID transactions (LWT only for single partition) |
| High availability (99.999% uptime achievable) | Read latency higher than memory-first stores (Redis) |
| Time-series, IoT, messaging workloads | Not ideal for small datasets (< 10 GB) |
| Tunable consistency per query | Counter and aggregate support is limited |

### 1.4 Cassandra vs. Other Databases

| Feature | Cassandra | MongoDB | DynamoDB | PostgreSQL |
|---------|-----------|---------|----------|------------|
| Data model | Wide-column | Document | Key-value / Document | Relational |
| Scalability | Linear (peer-to-peer) | Sharded (mongos) | Managed auto-scale | Vertical (read replicas) |
| Consistency | Tunable | Configurable | Eventually / Strong | Strong (ACID) |
| Write perf | Excellent | Good | Excellent | Good |
| Read perf | Good (partition key) | Good (index) | Excellent (key) | Excellent (index) |
| JOINs | None | Lookup/pipeline | None | Full SQL |
| Multi-DC | Native | Manual / Atlas | Global Tables | Logical replication |
| Operations | Self-managed or managed | Self-managed or Atlas | Fully managed | Self-managed or managed |

---

## 2. Data Model Fundamentals

### 2.1 Keyspace

A keyspace is the top-level namespace, analogous to a database in RDBMS. It defines replication strategy and replication factor.

```sql
-- Create keyspace with SimpleStrategy (dev/test only)
CREATE KEYSPACE myapp
WITH REPLICATION = {'class': 'SimpleStrategy', 'replication_factor': 3};

-- Create keyspace with NetworkTopologyStrategy (production)
CREATE KEYSPACE ecommerce
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3,
  'eu-west-1': 3
};

-- Alter keyspace (change replication)
ALTER KEYSPACE ecommerce
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3,
  'eu-west-1': 3,
  'ap-south-1': 2
};

-- List keyspaces
DESCRIBE KEYSPACES;

-- Use a keyspace
USE ecommerce;

-- Drop keyspace (DESTRUCTIVE)
DROP KEYSPACE myapp;
```

### 2.2 Table

Tables define the schema for data storage. The primary key determines data distribution and ordering.

```sql
CREATE TABLE users (
    user_id uuid,
    username text,
    email text,
    created_at timestamp,
    profile map<text, text>,
    tags set<text>,
    PRIMARY KEY (user_id)
);

-- Composite primary key
CREATE TABLE messages (
    conversation_id text,      -- partition key
    message_id timeuuid,       -- clustering column
    sender text,
    body text,
    PRIMARY KEY (conversation_id, message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);
```

### 2.3 Primary Key Anatomy

```sql
PRIMARY KEY (partition_key, clustering_col1, clustering_col2)

-- partition_key: determines which node stores the data (via consistent hashing).
-- clustering columns: determine the sort order of rows WITHIN a partition.

-- Composite partition key (double parentheses):
PRIMARY KEY ((tenant_id, year), month, day)
-- (tenant_id, year) is the partition key.
-- month and day are clustering columns.

-- Rules:
-- 1. Partition key is REQUIRED in every query's WHERE clause.
-- 2. Clustering columns can be queried with equality or range (in order).
-- 3. You cannot skip clustering columns in a WHERE clause.
```

### 2.4 Data Types

```sql
-- Primitive types
text        -- UTF-8 string
int         -- 32-bit signed integer
bigint      -- 64-bit signed integer
float       -- 32-bit IEEE 754
double      -- 64-bit IEEE 754
decimal     -- arbitrary precision decimal
boolean     -- true/false
uuid        -- Type 4 UUID
timeuuid    -- Type 1 UUID (time-based, sortable)
timestamp   -- milliseconds since epoch
date        -- date without time
time        -- time without date
blob        -- arbitrary bytes
inet        -- IPv4 or IPv6 address
varint      -- arbitrary precision integer
duration    -- time duration (nanosecond precision)

-- Collection types
set<text>                -- unordered unique elements
list<text>               -- ordered elements (by insertion)
map<text, text>          -- key-value pairs

-- Frozen collections (stored as a single blob, immutable)
frozen<map<text, text>>  -- entire map must be replaced on update

-- Tuples
tuple<text, int, double>

-- User-defined types
CREATE TYPE address (
    street text,
    city text,
    zip text,
    country text
);

-- Counter type (special: increment/decrement only)
counter
```

### 2.5 Static Columns

```sql
-- Static columns share a single value per PARTITION (not per row).
CREATE TABLE department_employees (
    department_id text,
    employee_id uuid,
    employee_name text,
    department_name text STATIC,   -- one value per department_id
    department_head text STATIC,   -- one value per department_id
    PRIMARY KEY (department_id, employee_id)
);

-- Updating a static column affects ALL rows in the partition.
UPDATE department_employees SET department_head = 'Alice'
WHERE department_id = 'eng';
-- All employees in 'eng' department now see department_head = 'Alice'.
```

---

## 3. CQL Essentials

### 3.1 Basic Operations

```sql
-- Insert
INSERT INTO users (user_id, username, email, created_at)
VALUES (uuid(), 'john', 'john@example.com', toTimestamp(now()));

-- Insert with TTL (auto-expire after 1 hour)
INSERT INTO sessions (session_id, user_id, token)
VALUES (uuid(), user_uuid, 'abc123')
USING TTL 3600;

-- Select (partition key required)
SELECT * FROM users WHERE user_id = 550e8400-e29b-41d4-a716-446655440000;

-- Select with clustering column range
SELECT * FROM messages
WHERE conversation_id = 'conv_42'
  AND message_id >= minTimeuuid('2026-05-22T00:00:00Z')
LIMIT 50;

-- Update
UPDATE users SET email = 'new@example.com'
WHERE user_id = 550e8400-e29b-41d4-a716-446655440000;

-- Delete
DELETE FROM users WHERE user_id = 550e8400-e29b-41d4-a716-446655440000;

-- Lightweight transaction (compare-and-set)
INSERT INTO users (user_id, email) VALUES (uuid(), 'alice@example.com')
IF NOT EXISTS;
```

### 3.2 Batch Operations

```sql
-- LOGGED BATCH: atomic across partitions (uses batch log coordinator)
BEGIN BATCH
  INSERT INTO orders (order_id, customer, total) VALUES (uuid(), 'alice', 99.99);
  INSERT INTO orders_by_customer (customer, order_id, total) VALUES ('alice', uuid(), 99.99);
APPLY BATCH;

-- UNLOGGED BATCH: no atomicity guarantee; use for same-partition inserts
BEGIN UNLOGGED BATCH
  INSERT INTO metrics (metric, bucket, ts, value) VALUES ('cpu', '2026-05-22', now(), 72.5);
  INSERT INTO metrics (metric, bucket, ts, value) VALUES ('cpu', '2026-05-22', now(), 73.1);
APPLY BATCH;

-- WARNING: LOGGED BATCH is NOT a performance optimization.
-- It adds coordination overhead. Use it only for atomicity
-- across denormalized tables, not for bulk loading.
```

### 3.3 cqlsh Basics

```bash
# Connect to a Cassandra node
cqlsh 10.0.1.1

# Connect with authentication
cqlsh -u admin -p 'password' 10.0.1.1

# Connect with TLS
cqlsh --ssl 10.0.1.1 9142

# Execute a CQL file
cqlsh -f /path/to/schema.cql

# Set consistency level in cqlsh
CONSISTENCY LOCAL_QUORUM;

# Enable tracing
TRACING ON;
SELECT * FROM users WHERE user_id = ?;
TRACING OFF;

# Copy data (export/import)
COPY users TO '/tmp/users.csv';
COPY users FROM '/tmp/users.csv';
```

---

## 4. Cluster Architecture

### 4.1 Peer-to-Peer Topology

Cassandra uses a peer-to-peer (masterless) architecture. Every node is functionally identical:

```
Client --> Any Node (Coordinator)
              |
              |--> Replica 1
              |--> Replica 2
              |--> Replica 3

No master, no standby, no election.
Any node can serve any request.
The coordinator routes to the appropriate replicas.
```

### 4.2 Nodes, Racks, and Datacenters

```yaml
# Logical hierarchy:
# Cluster
#   └── Datacenter (DC)
#         └── Rack
#               └── Node

# cassandra.yaml: cluster identity
cluster_name: 'production'

# cassandra-rackdc.properties: DC and rack assignment
dc=us-east-1
rack=rack1

# Cassandra distributes replicas across racks within a DC
# to survive rack-level failures (power, network switch).
```

### 4.3 Coordinator Node

```
The coordinator is the node that receives the client request.
It is NOT a special role; any node can be coordinator.

Coordinator responsibilities:
1. Receive the client's CQL query.
2. Determine which nodes hold the relevant partition(s)
   based on the partition key's token and the replication strategy.
3. Send the request to the appropriate replica nodes.
4. Collect responses according to the consistency level.
5. Reconcile data (if multiple responses differ).
6. Return the result to the client.
7. Optionally trigger read repair if replicas disagree.
```

### 4.4 Seed Nodes

```yaml
# cassandra.yaml
seed_provider:
  - class_name: org.apache.cassandra.locator.SimpleSeedProvider
    parameters:
      - seeds: "10.0.1.1,10.0.1.2,10.0.2.1"

# Seeds are used for gossip bootstrapping:
# - New nodes contact seeds to learn the ring topology.
# - Seeds are NOT special at runtime (same as any other node).
# - 2-3 seeds per DC is recommended.
# - Never make ALL nodes seeds (slows gossip convergence).
# - A seed going down does not affect running nodes.
```

### 4.5 nodetool Status

```bash
nodetool status

# Example output:
# Datacenter: us-east-1
# =======================
# Status=Up/Down  |/ State=Normal/Leaving/Joining/Moving
# --  Address     Load       Tokens  Owns    Host ID                               Rack
# UN  10.0.1.1    15.2 GiB   256     33.3%   a1b2c3d4-e5f6-7890-abcd-ef1234567890  rack1
# UN  10.0.1.2    14.8 GiB   256     33.4%   f1e2d3c4-b5a6-7890-dcba-098765432101  rack2
# UN  10.0.1.3    15.0 GiB   256     33.3%   11223344-5566-7788-99aa-bbccddeeff00  rack3

# Key columns:
# UN = Up/Normal (healthy)
# DN = Down/Normal (unreachable)
# UJ = Up/Joining (bootstrapping)
# UL = Up/Leaving (decommissioning)
# Load = data stored on the node
# Tokens = number of vnodes
# Owns = percentage of data this node is responsible for
```

---

## 5. Write Path

### 5.1 Write Path Detailed

```
Client write arrives at the coordinator:

1. COORDINATOR:
   - Parses CQL and determines the partition key.
   - Hashes partition key → token.
   - Finds replica nodes from the token ring + replication strategy.
   - Sends the mutation to all replica nodes.
   - Waits for CL acknowledgments (e.g., LOCAL_QUORUM = 2 of 3).

2. REPLICA NODE (each independently):
   a. Write to COMMITLOG (append-only, sequential I/O)
      - Ensures durability: if the node crashes, commitlog replays on restart.
      - fsync behavior: periodic (every 10s) or batch (every write).
   b. Write to MEMTABLE (in-memory sorted structure)
      - Fast: pure memory write.
      - Organized by partition key, then clustering columns.
   c. Acknowledge to coordinator.

3. COORDINATOR:
   - Receives enough ACKs to satisfy CL.
   - Returns success to client.
   - For unreachable replicas: stores a HINT (if hinted_handoff_enabled).

4. BACKGROUND (later):
   a. MEMTABLE FLUSH: when memtable reaches threshold, flush to SSTable on disk.
   b. COMPACTION: periodically merge SSTables, remove tombstones, reclaim space.
```

### 5.2 Write Path Diagram

```
Client
  |
  v
Coordinator Node
  |
  ├──> Replica 1: Commitlog → Memtable → ACK
  ├──> Replica 2: Commitlog → Memtable → ACK
  └──> Replica 3: Commitlog → Memtable → (down → HINT stored)
  |
  v
ACK to Client (after CL=LOCAL_QUORUM satisfied)

Later:
  Memtable ──flush──> SSTable (immutable on disk)
  SSTables ──compact──> Merged SSTable (fewer files, tombstones removed)
```

### 5.3 Commitlog

```yaml
# cassandra.yaml
commitlog_sync: periodic
commitlog_sync_period_in_ms: 10000     # fsync every 10 seconds
commitlog_total_space_in_mb: 8192      # total commitlog space
commitlog_segment_size_in_mb: 32       # individual segment size

# commitlog_sync: batch
# Syncs commitlog after EVERY write. Safest but slowest.
# Use only when data loss of even 10 seconds is unacceptable.

# Commitlog compression (recommended):
commitlog_compression:
  - class_name: LZ4Compressor

# CRITICAL: put commitlog on a SEPARATE disk from data.
# Commitlog is sequential write; data is random read/write.
# Sharing a disk creates I/O contention.
commitlog_directory: /ssd1/cassandra/commitlog
```

### 5.4 Memtable

```yaml
# cassandra.yaml
memtable_heap_space_in_mb: 2048       # on-heap memtable space
memtable_offheap_space_in_mb: 2048    # off-heap memtable space

# Each table has its own memtable.
# When the total memtable space threshold is reached,
# the largest memtable is flushed to an SSTable.

# Memtable is a concurrent sorted data structure (skiplist or tree).
# Writes are O(log N) within the memtable.
```

### 5.5 SSTables (Sorted String Tables)

```
SSTables are immutable files written during memtable flush.

SSTable components:
  data.db             -- actual row data, sorted by token then clustering key
  Index.db            -- partition key to byte offset mapping
  Summary.db          -- sparse in-memory index of Index.db
  Filter.db           -- bloom filter (probabilistic key membership test)
  CompressionInfo.db  -- compression offsets for random access
  Statistics.db       -- min/max values, tombstone count, metadata
  TOC.txt             -- table of contents of all components

Properties:
  - Immutable: never modified after creation.
  - Sorted: rows within a partition are ordered by clustering columns.
  - Versioned: each cell has a timestamp for conflict resolution.
  - Compacted: periodically merged to reduce file count and purge tombstones.
```

---

## 6. Read Path

### 6.1 Read Path Detailed

```
Client read arrives at the coordinator:

1. COORDINATOR:
   - Determines which replicas hold the requested partition.
   - Based on CL, decides how many replicas to contact:
     * ONE: send data request to closest replica.
     * QUORUM: send data request to 1 replica, digest requests to (CL-1) replicas.
   - If digests match: return data to client.
   - If digests mismatch: fetch full data from all, reconcile, return latest.

2. REPLICA NODE:
   a. Check MEMTABLE (current in-memory data).
   b. Check ROW CACHE (if enabled; whole partition cache).
   c. For each SSTABLE on disk:
      1. BLOOM FILTER: "Is this partition key possibly in this SSTable?"
         - If NO: skip this SSTable (fast rejection).
         - If MAYBE: continue to next step.
      2. PARTITION KEY CACHE: check if byte offset is cached.
         - If HIT: jump directly to data.
         - If MISS: check Partition Summary → Partition Index → data.
      3. Read compressed chunk from disk (or OS page cache).
   d. MERGE results from memtable + all relevant SSTables.
      - Latest timestamp wins for each cell.
      - Tombstones suppress deleted data.
   e. Return merged result to coordinator.

3. COORDINATOR:
   - Reconcile responses from multiple replicas.
   - Return result to client.
   - If replicas disagreed: trigger READ REPAIR (send correct data to stale replica).
```

### 6.2 Read Path Diagram

```
Client
  |
  v
Coordinator Node
  |
  ├──> Replica 1 (data request):
  |      Memtable
  |      Row Cache (if enabled)
  |      SSTable 1: Bloom Filter → Key Cache → Index → Data
  |      SSTable 2: Bloom Filter → Key Cache → Index → Data
  |      SSTable N: Bloom Filter → (rejected by bloom filter)
  |      MERGE all results → return data
  |
  ├──> Replica 2 (digest request):
  |      Same process, but returns only a hash (digest)
  |
  v
Compare data hash vs. digest
  - Match: return data to client
  - Mismatch: full data fetch from both, reconcile, read repair
```

### 6.3 Bloom Filter

```sql
-- Bloom filter is per-SSTable and loaded into off-heap memory at startup.
-- It answers: "Is this partition key DEFINITELY NOT in this SSTable?"
-- False positives possible (says "maybe" when key is absent).
-- False negatives impossible (never says "no" when key IS present).

-- Tune false positive rate per table:
CREATE TABLE orders (
    order_id uuid PRIMARY KEY,
    data text
) WITH bloom_filter_fp_chance = 0.01;   -- 1% false positive rate (default)
-- Lower = fewer wasted disk reads, more memory.
-- Higher = more wasted disk reads, less memory.
```

---

## 7. Replication and Consistency

### 7.1 Replication Factor

```sql
-- RF=3 means each partition is stored on 3 different nodes.
-- The replication strategy determines WHICH 3 nodes.

CREATE KEYSPACE critical_data
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3   -- 3 replicas in us-east-1
};

-- With RF=3 and LOCAL_QUORUM:
-- Writes need 2 of 3 replicas to acknowledge.
-- Reads need 2 of 3 replicas to respond.
-- Can tolerate 1 node failure without data loss or unavailability.
```

### 7.2 Consistency Level Summary

```sql
-- Write consistency levels:
CONSISTENCY ONE;            -- 1 replica ACK (fastest, weakest)
CONSISTENCY LOCAL_QUORUM;   -- quorum in local DC (standard production)
CONSISTENCY QUORUM;         -- global quorum (cross-DC latency)
CONSISTENCY ALL;            -- every replica (slowest, strongest)

-- Read consistency levels:
CONSISTENCY ONE;            -- read from closest replica (may be stale)
CONSISTENCY LOCAL_QUORUM;   -- read from quorum in local DC
CONSISTENCY ALL;            -- read from every replica

-- Strong consistency: R + W > RF
-- LOCAL_QUORUM reads + LOCAL_QUORUM writes with RF=3:
-- R=2 + W=2 = 4 > 3  =>  strong consistency within the local DC.
```

### 7.3 Conflict Resolution

```
Cassandra uses LAST-WRITE-WINS (LWW) conflict resolution:

1. Each cell (column value) has a microsecond timestamp.
2. When replicas have different values for the same cell,
   the cell with the HIGHEST timestamp wins.
3. Ties are broken by value comparison (rare).

Implications:
- Clock skew between nodes can cause the "wrong" value to win.
- NTP synchronization is CRITICAL on all Cassandra nodes.
- Client-provided timestamps are supported (driver-level control).
- Tombstones (deletes) also have timestamps and participate in LWW.
```

---

## 8. Compaction

### 8.1 Why Compaction Exists

Cassandra's write path creates immutable SSTables. Over time, the number of SSTables grows, degrading read performance (each read must check multiple files). Compaction merges SSTables to:

1. Reduce the number of SSTables (faster reads).
2. Remove tombstones (reclaim disk space from deleted data).
3. Merge duplicate rows (keep only the latest version).
4. Remove expired TTL data.

### 8.2 Compaction Strategies

```sql
-- SizeTieredCompactionStrategy (STCS) -- default
-- Groups SSTables of similar size and merges them.
-- Best for: write-heavy workloads.
-- Weakness: needs ~50% free disk for compaction; read latency varies.
CREATE TABLE write_heavy (
    id int PRIMARY KEY,
    data text
) WITH COMPACTION = {
    'class': 'SizeTieredCompactionStrategy',
    'min_threshold': 4,
    'max_threshold': 32
};

-- LeveledCompactionStrategy (LCS)
-- Organizes SSTables into levels; each level is 10x the previous.
-- Best for: read-heavy workloads (consistent read latency).
-- Weakness: high write amplification (each write rewritten 5-10x).
CREATE TABLE read_heavy (
    id int PRIMARY KEY,
    data text
) WITH COMPACTION = {'class': 'LeveledCompactionStrategy'};

-- TimeWindowCompactionStrategy (TWCS)
-- Groups SSTables by time window. Expired windows are dropped as files.
-- Best for: time-series data with TTL.
-- Weakness: out-of-order writes reduce efficiency.
CREATE TABLE time_series (
    id timeuuid,
    data text,
    PRIMARY KEY (id)
) WITH COMPACTION = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 1
};

-- UnifiedCompactionStrategy (UCS) -- Cassandra 5.0
-- Auto-adapts behavior based on workload.
-- Replaces manual strategy selection.
CREATE TABLE adaptive (
    id int PRIMARY KEY,
    data text
) WITH COMPACTION = {'class': 'UnifiedCompactionStrategy'};
```

### 8.3 Compaction Monitoring

```bash
# View active compactions
nodetool compactionstats

# View compaction history
nodetool compactionhistory

# Force compaction (use sparingly)
nodetool compact <keyspace> <table>

# Throttle compaction I/O
nodetool setcompactionthroughput 64   # MB/s
```

---

## 9. Gossip Protocol and Failure Detection

### 9.1 Gossip Protocol

Gossip is the protocol by which Cassandra nodes share cluster state (node status, schema versions, load, token ownership).

```
Every second, each node:
1. Picks 1-3 random peers.
2. Sends its gossip state (what it knows about all nodes).
3. Receives the peer's gossip state.
4. Merges: keeps the entry with the highest heartbeat version.

Gossip converges quickly:
- With N nodes, information propagates in O(log N) rounds.
- A 100-node cluster converges in ~7 seconds.
```

### 9.2 Gossip State

```bash
# View raw gossip state for all known nodes
nodetool gossipinfo

# Example:
# /10.0.1.1
#   generation: 1716393600
#   heartbeat: 1234
#   STATUS: NORMAL,-9223372036854775808
#   LOAD: 15200000000
#   SCHEMA: abc12345-def67890
#   DC: us-east-1
#   RACK: rack1
#   RELEASE_VERSION: 4.1.3
#   NET_VERSION: 12
#   HOST_ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
#   TOKENS: <list of tokens>
```

### 9.3 Failure Detection

```yaml
# cassandra.yaml
# Phi Accrual Failure Detector: continuous suspicion scoring.
phi_convict_threshold: 8
# Higher = more tolerant of delayed heartbeats (fewer false positives).
# Lower = faster failure detection (more false positives).
# Increase for high-latency networks (WAN, cloud): 10-12.
# Decrease for low-latency networks: 6-8.
```

---

## 10. Cassandra Configuration

### 10.1 cassandra.yaml Core Settings

```yaml
# cassandra.yaml -- key configuration parameters

# Cluster identity
cluster_name: 'production'

# Networking
listen_address: 10.0.1.1         # internode communication
rpc_address: 10.0.1.1            # client connections
native_transport_port: 9042       # CQL port
storage_port: 7000               # internode port

# Seeds
seed_provider:
  - class_name: org.apache.cassandra.locator.SimpleSeedProvider
    parameters:
      - seeds: "10.0.1.1,10.0.1.2,10.0.2.1"

# Topology
endpoint_snitch: GossipingPropertyFileSnitch

# Virtual nodes
num_tokens: 16                    # Cassandra 4.0+ recommended
allocate_tokens_for_local_replication_factor: 3

# Directories (separate disks recommended)
data_file_directories:
  - /data/cassandra/data
commitlog_directory: /ssd1/cassandra/commitlog
saved_caches_directory: /data/cassandra/saved_caches
hints_directory: /data/cassandra/hints

# Memory
memtable_heap_space_in_mb: 2048
memtable_offheap_space_in_mb: 2048
key_cache_size_in_mb: 256
file_cache_size_in_mb: 512

# Commitlog
commitlog_sync: periodic
commitlog_sync_period_in_ms: 10000
commitlog_total_space_in_mb: 8192
commitlog_compression:
  - class_name: LZ4Compressor

# Compaction
compaction_throughput_mb_per_sec: 64
concurrent_compactors: 2

# Concurrency
concurrent_reads: 32
concurrent_writes: 32
concurrent_counter_writes: 32

# Timeouts
read_request_timeout_in_ms: 5000
write_request_timeout_in_ms: 2000
counter_write_request_timeout_in_ms: 5000
cas_contention_timeout: 1000
request_timeout_in_ms: 10000

# Network
internode_compression: dc
stream_throughput_outbound_megabits_per_sec: 200
inter_dc_stream_throughput_outbound_megabits_per_sec: 50

# Hinted handoff
hinted_handoff_enabled: true
max_hint_window: 10800000

# Tombstones
tombstone_warn_threshold: 1000
tombstone_failure_threshold: 100000

# Authentication (enable for production)
authenticator: PasswordAuthenticator
authorizer: CassandraAuthorizer

# Encryption
# server_encryption_options: ...
# client_encryption_options: ...
```

### 10.2 JVM Configuration

```bash
# jvm11-server.options (Cassandra 4.x)
# jvm17-server.options (Cassandra 5.x)

# Heap (8-16 GB for most workloads)
-Xms16G
-Xmx16G

# G1GC (default in 4.0+)
-XX:+UseG1GC
-XX:MaxGCPauseMillis=500
-XX:G1HeapRegionSize=16m
-XX:InitiatingHeapOccupancyPercent=45
-XX:ParallelGCThreads=16
-XX:ConcGCThreads=4

# GC logging
-Xlog:gc*:file=/var/log/cassandra/gc.log:time,level,tags:filecount=10,filesize=100m

# OOM handling
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/var/log/cassandra/
-XX:+ExitOnOutOfMemoryError
```

### 10.3 cassandra-rackdc.properties

```yaml
# Used by GossipingPropertyFileSnitch
dc=us-east-1
rack=rack1
# prefer_local=true   # prefer local DC for reads (optional)
```

---

## 11. Cassandra 4.x/5.x Architecture Changes

### 11.1 Cassandra 4.0

- **Internode messaging v4**: single multiplexed connection per peer (replaces thread-per-connection model). Reduces connection count and memory overhead.
- **Zero-Copy Streaming**: transfers SSTables directly without deserialization, 5x faster bootstrap and repair.
- **Virtual tables** (`system_views` keyspace): CQL-accessible node state without JMX.
- **Audit logging**: built-in query auditing.
- **Full Query Logging (FQL)**: capture every query for replay and analysis.
- **Transient replication** (experimental): "cheap" replicas that do not persist data permanently.
- **Improved incremental repair**: better repaired/unrepaired SSTable tracking.
- **Java 11 minimum requirement**.

### 11.2 Cassandra 4.1

- **Guardrails framework**: configurable cluster-wide limits (partition size, column count, query scope).
- **Top partitions**: `nodetool toppartitions` for real-time hot partition detection.
- **Pluggable memtable**: custom memtable implementations for specialized workloads.
- **Paxos state purging**: automatic cleanup of system.paxos table after repair.
- **Password validator**: enforce password complexity requirements.

### 11.3 Cassandra 5.0

- **Accord protocol**: leaderless distributed transaction protocol replacing Paxos for LWT. Lower latency, multi-DC native.
- **Unified Compaction Strategy (UCS)**: auto-adapting compaction.
- **Storage Attached Indexes (SAI)**: efficient distributed secondary indexes replacing legacy SASI and secondary indexes.
- **Trie-indexed SSTables**: faster partition lookups with 30-60% memory reduction.
- **Transactional Cluster Metadata (TCM)**: Raft-based consensus for cluster metadata (schema, topology) replacing gossip for these operations.
- **Vector search** (preview): ANN search via SAI for embedding workloads.
- **Java 17 minimum requirement**.
- **PEM-based TLS**: use PEM files directly instead of Java keystores.

```sql
-- Cassandra 5.0 SAI example
CREATE INDEX ON products (category) USING 'sai';
CREATE INDEX ON products (price) USING 'sai';

SELECT * FROM products
WHERE category = 'electronics' AND price < 100.00;
-- No ALLOW FILTERING needed.
```

```bash
-- Cassandra 5.0 virtual tables
SELECT * FROM system_views.sstable_tasks;
SELECT * FROM system_views.clients;
SELECT * FROM system_views.settings;
```

---

## 12. Troubleshooting

### 12.1 Node Fails to Join Cluster

**Symptom**: new node starts but does not appear in `nodetool status`.

**Fix**:
```bash
# Check cluster_name matches existing cluster
grep cluster_name /etc/cassandra/cassandra.yaml

# Check seeds include at least one reachable seed node
grep seeds /etc/cassandra/cassandra.yaml

# Check listen_address is correctly set to this node's IP
grep listen_address /etc/cassandra/cassandra.yaml

# Check network connectivity to seeds
nc -zv 10.0.1.1 7000

# Check system.log for errors
tail -100 /var/log/cassandra/system.log
```

### 12.2 Cassandra Fails to Start

**Symptom**: process exits immediately.

**Fix**:
```bash
# Check system.log
tail -100 /var/log/cassandra/system.log

# Common causes:
# 1. Wrong Java version (5.0 requires Java 17+)
java -version

# 2. Port conflict (another process on 9042, 7000)
lsof -i :9042
lsof -i :7000

# 3. Corrupted commitlog
# Move commitlog and restart (loses unflushed data):
mv /data/cassandra/commitlog/* /tmp/commitlog_backup/

# 4. Permission issues
ls -la /data/cassandra/
chown -R cassandra:cassandra /data/cassandra/

# 5. Insufficient memory
grep -E "^-Xm[sx]" /etc/cassandra/jvm*-server.options
```

### 12.3 High Write Latency

**Symptom**: p99 write latency > 50ms.

**Fix**:
```bash
# Check commitlog and data on same disk (must be separate)
grep commitlog_directory /etc/cassandra/cassandra.yaml
grep data_file_directories /etc/cassandra/cassandra.yaml

# Check compaction backlog (competing for disk I/O)
nodetool compactionstats

# Check GC pauses
grep "GC pause" /var/log/cassandra/gc.log | tail -10

# Check disk I/O utilization
iostat -x 1 5
```

### 12.4 High Read Latency

**Symptom**: p99 read latency > 100ms.

**Fix**:
```bash
# Check SSTable count (too many = slow reads)
nodetool tablestats <ks>.<table> | grep "SSTable count"

# Check large partitions
nodetool tablestats <ks>.<table> | grep "Compacted partition maximum"

# Check tombstone count per read
nodetool tablestats <ks>.<table> | grep "tombstones"

# Check bloom filter effectiveness
nodetool tablestats <ks>.<table> | grep "Bloom filter false"

# Check key cache hit rate
nodetool info | grep "Key Cache"
```

### 12.5 Schema Disagreement

**Symptom**: DDL operations fail; nodes show different schema versions.

**Fix**:
```bash
nodetool describecluster

# If one node has a different schema:
# 1. Try restarting it
nodetool drain && systemctl restart cassandra

# 2. If restart does not help:
nodetool resetlocalschema
# Forces the node to re-fetch schema from peers.
```

### 12.6 Node Shows DN (Down) in Status

**Symptom**: `nodetool status` shows a node as DN.

**Fix**:
```bash
# Check if the node process is running
ssh 10.0.1.3 "ps aux | grep CassandraDaemon"

# Check if the node can be reached on internode port
nc -zv 10.0.1.3 7000

# Check phi_convict_threshold (may be too aggressive for WAN)
grep phi_convict_threshold /etc/cassandra/cassandra.yaml
# Increase for high-latency networks: 10-12

# If the node is truly down, restart it:
ssh 10.0.1.3 "systemctl start cassandra"
```

### 12.7 Out of Memory (OOM)

**Symptom**: `OutOfMemoryError` in system.log.

**Fix**:
```bash
# Check which operation triggered OOM
grep "OutOfMemoryError" /var/log/cassandra/system.log

# Common causes:
# 1. Large partition read -- redesign partition key
nodetool tablestats <ks>.<table> | grep "Compacted partition maximum"

# 2. Heap too small -- increase (max 16 GB with G1GC)
grep -E "^-Xm[sx]" /etc/cassandra/jvm*-server.options

# 3. Too many tables -- each memtable consumes heap
# Reduce table count or increase heap

# 4. Tombstone accumulation -- scanned during reads, held in heap
nodetool tablestats <ks>.<table> | grep "tombstones"
```

### 12.8 Data Not Appearing After Write

**Symptom**: write succeeds but subsequent read returns nothing.

**Fix**:
```sql
-- Check consistency levels
-- If write CL=ONE and read CL=ONE, you might hit a different replica.
-- Use LOCAL_QUORUM for both for strong consistency.

-- Check if tombstone is masking the data
-- A previous DELETE may have a newer timestamp than the INSERT.
-- Verify with tracing:
TRACING ON;
SELECT * FROM <ks>.<table> WHERE pk = ?;
-- Look for "Tombstone" in the trace output.
```

### 12.9 Gossip Not Converging

**Symptom**: nodes disagree about cluster state for > 30 seconds.

**Fix**:
```bash
# Check gossip state
nodetool gossipinfo

# Verify network connectivity between all nodes (port 7000/7001)
# Firewall rules may block gossip traffic.

# Restart the problematic node to reset gossip state
nodetool drain && systemctl restart cassandra
```

### 12.10 SSTable Corruption

**Symptom**: `CorruptSSTableException` in logs.

**Fix**:
```bash
# Scrub the affected table to rebuild SSTables
nodetool scrub <keyspace> <table>

# If scrub fails:
# 1. Remove the corrupted SSTable file
# 2. Run repair to re-fetch data from replicas
nodetool repair -full <keyspace> <table>

# To detect corruption proactively:
nodetool verify <keyspace> <table>   # Cassandra 4.0+
```

---

## 13. FAQ

### Q1: Is Cassandra a column-oriented database?

No. Despite being called a "wide-column store," Cassandra stores data row-by-row (partition-by-partition). The "wide-column" name refers to the ability to have a dynamic number of columns per row, not columnar storage like Apache Parquet.

### Q2: Why does Cassandra not support JOINs?

JOINs require comparing data across different tables, potentially on different nodes. In a distributed system, this creates cross-network traffic that kills performance at scale. Cassandra instead requires denormalization: design one table per query pattern.

### Q3: Can Cassandra replace my relational database?

For specific workloads (high write throughput, time series, IoT, messaging), yes. For general-purpose OLTP with complex queries, transactions, and JOINs, no. Many architectures use Cassandra alongside a relational database.

### Q4: What is the maximum data size per node?

Practical limit: 1-3 TB per node on SSDs. Beyond 3 TB, compaction and repair become slow. For larger datasets, add more nodes rather than bigger disks.

### Q5: How does Cassandra handle deletes?

Cassandra writes a tombstone marker instead of removing data. The tombstone is replicated and compacted. After `gc_grace_seconds` (default 10 days), compaction removes the tombstone and the original data. If repair does not run within gc_grace_seconds, deleted data can reappear (resurrection).

### Q6: What Java version does Cassandra require?

Cassandra 4.0-4.1: Java 11. Cassandra 5.0: Java 17. Always use the exact major version specified; newer Java versions may not be tested.

### Q7: Can I run Cassandra on Kubernetes?

Yes, but it adds significant operational complexity. Cassandra relies on persistent local storage, stable network identities, and careful orchestration of rolling restarts. Use a Cassandra-specific Kubernetes operator (K8ssandra, Cass-operator) rather than generic StatefulSets.

### Q8: How many nodes do I need?

Minimum: 3 nodes with RF=3 (no fault tolerance below this). For production: plan for N+1 or N+2 nodes so that losing one node does not breach capacity limits. Scale horizontally based on throughput and storage requirements.

### Q9: What is the difference between Cassandra and ScyllaDB?

ScyllaDB is a Cassandra-compatible database rewritten in C++ (instead of Java). It claims lower latency and higher throughput due to avoiding JVM garbage collection. ScyllaDB is wire-compatible with Cassandra (uses the same CQL protocol and drivers).

### Q10: Is Cassandra ACID-compliant?

Not in the traditional sense. Cassandra provides atomicity at the partition level (single-partition writes are atomic). It supports lightweight transactions (LWT) for compare-and-set operations on a single partition. It does NOT support multi-partition ACID transactions. Cassandra 5.0's Accord protocol improves LWT performance but remains single-partition.

### Q11: What is the gossip protocol and why does Cassandra use it?

Gossip is a peer-to-peer protocol where each node periodically shares its knowledge of cluster state with random peers. Cassandra uses it because it is decentralized (no leader needed), eventually consistent (converges in O(log N) rounds), and resilient to node failures. In Cassandra 5.0, gossip is partially replaced by Raft-based TCM for schema and topology changes.

### Q12: Should I use UUIDs or TimeUUIDs for primary keys?

Use UUID (v4, random) when order does not matter (e.g., user IDs, product IDs). Use TimeUUID (v1, time-based) when you need time-ordered data (e.g., message IDs, event IDs). TimeUUIDs can be used as clustering columns for chronological ordering.

---

*Questo documento fa parte del modulo 07 "NoSQL Cassandra" della Data Encyclopedia.*
