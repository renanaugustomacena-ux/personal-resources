# Cassandra: Replication e Fault Tolerance

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
1. Replication Strategies
2. Consistency Levels
3. Strong Consistency Formula
4. Failure Detection
5. Hinted Handoff
6. Read Repair
7. Anti-Entropy Repair
8. Tombstones and Data Resurrection
9. Lightweight Transactions (LWT)
10. Transient Replication
11. Cassandra 4.x/5.x Fault Tolerance Features
12. Operational Procedures
13. Troubleshooting
14. FAQ

---

## 1. Replication Strategies

### 1.1 SimpleStrategy

```sql
-- Single datacenter, simple replication
-- Places replicas by walking the token ring, ignoring DC/rack topology.
CREATE KEYSPACE myapp
WITH REPLICATION = {
  'class': 'SimpleStrategy',
  'replication_factor': 3
};

-- How it works:
-- 1. Hash the partition key to get a token.
-- 2. Find the first node on the ring owning that token (primary replica).
-- 3. Walk clockwise on the ring to find the next N-1 nodes for replicas.
-- All replicas may land in the same rack or DC.

-- Use cases:
-- Development and testing environments.
-- Single-DC clusters with no rack awareness requirement.

-- WARNING: NEVER use SimpleStrategy in production multi-DC deployments.
-- It does not consider DC or rack placement.
```

### 1.2 NetworkTopologyStrategy (NTS)

```sql
-- Multi-datacenter, rack-aware replication.
-- Ensures replicas are distributed across racks within each DC.
CREATE KEYSPACE ecommerce
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3,
  'eu-west-1': 3,
  'ap-south-1': 2
};

-- How it works:
-- For each DC:
-- 1. Starting from the token's primary node in that DC,
--    walk clockwise to find nodes in DIFFERENT racks.
-- 2. Continue until the per-DC RF is satisfied.
-- 3. If not enough distinct racks exist, use nodes from the same rack.

-- Use cases:
-- ALL production deployments (single-DC or multi-DC).
-- NTS works correctly with a single DC too.
```

### 1.3 Choosing Replication Factor

| RF | Tolerated Failures | Quorum Size | Disk Overhead | Use Case |
|----|-------------------|-------------|---------------|----------|
| 1 | 0 | 1 | 1x | Dev/test only |
| 2 | 0 (with QUORUM) | 2 | 2x | Cost-sensitive analytics |
| 3 | 1 (with QUORUM) | 2 | 3x | Standard production |
| 5 | 2 (with QUORUM) | 3 | 5x | High-availability critical systems |

```sql
-- RF=3 is the production standard.
-- With QUORUM consistency: can tolerate 1 node failure.
-- With LOCAL_QUORUM in multi-DC: can tolerate 1 node failure per DC.

-- Increasing RF beyond 3 has diminishing returns:
-- More disk usage, more write amplification, marginal availability gain.
-- RF=5 is only justified for globally-critical, low-latency services.
```

### 1.4 Altering Replication

```sql
-- Increase RF (e.g., from 2 to 3)
ALTER KEYSPACE ecommerce
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3   -- was 2
};

-- CRITICAL: after increasing RF, new replicas have NO data.
-- You MUST run repair to stream data to the new replicas.
```

```bash
# Run repair after increasing RF
nodetool repair -full ecommerce

# Verify replication
nodetool describecluster
```

### 1.5 System Keyspace Replication

```sql
-- system_auth: authentication and authorization data
-- MUST be replicated to ALL DCs with adequate RF.
-- If system_auth is unavailable, no user can authenticate.
ALTER KEYSPACE system_auth
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3,
  'eu-west-1': 3
};

-- system_traces: query tracing data (optional but useful)
ALTER KEYSPACE system_traces
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 2,
  'eu-west-1': 2
};

-- system_distributed: repair history, CDC data
ALTER KEYSPACE system_distributed
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3,
  'eu-west-1': 3
};
```

---

## 2. Consistency Levels

### 2.1 Write Consistency Levels

| Level | Acknowledged By | Latency | Risk |
|-------|----------------|---------|------|
| `ANY` | 1 node (including hints) | Lowest | Data may be only on hint; lost if hint node dies |
| `ONE` | 1 replica | Low | Single point of failure |
| `TWO` | 2 replicas | Medium | Better than ONE |
| `THREE` | 3 replicas | Medium | Requires RF >= 3 |
| `QUORUM` | (RF/2)+1 replicas globally | Medium-High | Global quorum (cross-DC latency) |
| `LOCAL_ONE` | 1 replica in local DC | Low | No cross-DC dependency |
| `LOCAL_QUORUM` | (RF/2)+1 in local DC | Medium | Standard production choice |
| `EACH_QUORUM` | Quorum in EVERY DC | High | One slow DC blocks all writes |
| `ALL` | Every replica in every DC | Highest | One down node = failure |

```sql
-- Write with LOCAL_QUORUM (recommended for production)
CONSISTENCY LOCAL_QUORUM;
INSERT INTO orders (order_id, customer, total)
VALUES (uuid(), 'alice', 149.99);

-- Write with ONE (acceptable for metrics/logging)
CONSISTENCY ONE;
INSERT INTO page_views (page, ts, count)
VALUES ('/home', toTimestamp(now()), 1);

-- Write with ANY (fire-and-forget; almost never correct)
-- ANY means even a hint counts as acknowledgment.
-- The data may exist ONLY as a hint if all replicas are down.
CONSISTENCY ANY;
INSERT INTO low_priority_events (...) VALUES (...);
```

### 2.2 Read Consistency Levels

| Level | Reads From | Latency | Guarantee |
|-------|-----------|---------|-----------|
| `ONE` | Closest replica | Lowest | May return stale data |
| `TWO` | 2 replicas (reconcile) | Medium | Better than ONE |
| `THREE` | 3 replicas | Medium | Requires RF >= 3 |
| `QUORUM` | (RF/2)+1 globally | Medium-High | Strong with QUORUM writes |
| `LOCAL_ONE` | 1 replica in local DC | Lowest | No cross-DC hop |
| `LOCAL_QUORUM` | (RF/2)+1 in local DC | Medium | Standard production choice |
| `ALL` | Every replica | Highest | Guaranteed latest; one down = failure |
| `SERIAL` | Paxos consensus globally | Very High | For LWT reads |
| `LOCAL_SERIAL` | Paxos consensus in local DC | High | For LWT reads, local |

```sql
-- Read with LOCAL_QUORUM (recommended for most production reads)
CONSISTENCY LOCAL_QUORUM;
SELECT * FROM orders WHERE order_id = ?;

-- Read with ONE (acceptable when staleness is tolerable)
CONSISTENCY ONE;
SELECT * FROM metrics WHERE metric = 'cpu' AND bucket = '2026-05-22';
```

### 2.3 Read Repair During Reads

When reading from multiple replicas (QUORUM, ALL), Cassandra compares the responses:

```
Coordinator sends read to 2 replicas (LOCAL_QUORUM, RF=3):
  Replica 1: returns full data
  Replica 2: returns digest (hash of data)

If digests match: return data immediately.
If digests differ:
  1. Fetch full data from both replicas.
  2. Compare timestamps per column.
  3. Return the latest version to the client.
  4. Send the latest version to the stale replica (read repair).
```

---

## 3. Strong Consistency Formula

### 3.1 The Formula

```
Strong consistency is guaranteed when:
  R + W > RF

Where:
  R = number of replicas read (determined by read CL)
  W = number of replicas written (determined by write CL)
  RF = replication factor
```

### 3.2 Common Configurations

```
RF=3, LOCAL_QUORUM writes (W=2), LOCAL_QUORUM reads (R=2):
  R + W = 4 > 3  => STRONG consistency within the local DC

RF=3, LOCAL_QUORUM writes (W=2), ONE reads (R=1):
  R + W = 3 = 3  => NOT strong (edge case: may read stale)

RF=3, ONE writes (W=1), ALL reads (R=3):
  R + W = 4 > 3  => STRONG (but ALL reads fail if any node is down)

RF=3, ALL writes (W=3), ONE reads (R=1):
  R + W = 4 > 3  => STRONG (but ALL writes fail if any node is down)

RF=3, QUORUM writes (W=2), QUORUM reads (R=2):
  R + W = 4 > 3  => STRONG across ALL DCs (but high cross-DC latency)
```

### 3.3 Monotonic Reads

Even with strong consistency, Cassandra does not guarantee monotonic reads by default. A client might read from replica A (latest data), then read from replica B (stale data) on the next request.

```
Mitigation:
- Use LOCAL_QUORUM for both reads and writes (makes staleness short-lived).
- Pin reads to a specific replica using speculative_retry = NONE
  and token-aware driver routing (same coordinator each time).
- Cassandra 5.0 Accord protocol provides stronger ordering guarantees.
```

---

## 4. Failure Detection

### 4.1 Phi Accrual Failure Detector

Cassandra uses the Phi Accrual Failure Detector to determine whether a node is alive or dead. Unlike a binary (alive/dead) detector, Phi outputs a continuous suspicion level.

```yaml
# cassandra.yaml
phi_convict_threshold: 8
# Phi value above which a node is considered dead.
# Default: 8 (suitable for most networks).
# Increase for high-latency or unreliable networks:
# WAN links: 10-12
# Cloud (variable latency): 10
# Low-latency LAN: 6-8
```

### 4.2 How Phi Works

```
1. Each node sends gossip heartbeats to random peers every second.
2. The receiver tracks the inter-arrival time of heartbeats.
3. From the distribution of inter-arrival times, Phi is computed.
4. Higher Phi = higher suspicion that the node is dead.

Phi = -log10(P(heartbeat_gap > observed_gap))

If Phi > phi_convict_threshold:
  Node is marked DOWN.
  Gossip propagates the DOWN status to all nodes.
  Coordinator stops sending requests to the DOWN node.
```

### 4.3 Gossip Protocol

```bash
# Gossip is the protocol nodes use to share cluster state.
# Every second, each node gossips with 1-3 random peers.

# View gossip state:
nodetool gossipinfo

# Example output:
# /10.0.1.1
#   generation: 1716393600
#   heartbeat: 42
#   STATUS: NORMAL,-1234567890
#   LOAD: 1.5E10
#   SCHEMA: abc123-def456
#   DC: us-east-1
#   RACK: rack1
#   RELEASE_VERSION: 4.1.3

# Key gossip states:
# NORMAL   - node is healthy and serving
# LEAVING  - node is decommissioning
# JOINING  - node is bootstrapping
# MOVING   - node is moving token ranges
# REMOVING - node is being removed by another node
```

### 4.4 Failure Scenarios

```
Scenario 1: Single node failure (RF=3, LOCAL_QUORUM)
  - Writes succeed: 2 of 3 replicas acknowledge.
  - Reads succeed: 2 of 3 replicas respond.
  - Hints are stored for the down node (up to max_hint_window).
  - After recovery, hints are replayed; repair fixes any gaps.

Scenario 2: Two nodes fail (RF=3, LOCAL_QUORUM)
  - QUORUM requires 2 of 3 nodes.
  - If 2 of 3 replicas for a partition are down:
    - Writes fail with UnavailableException.
    - Reads fail with UnavailableException.
  - Downgrade to CL=ONE to continue (accepting weaker consistency).

Scenario 3: Full DC failure (multi-DC, LOCAL_QUORUM)
  - Local DC: all requests fail (no quorum).
  - Remote DC: unaffected (LOCAL_ CLs are scoped to local DC).
  - Client driver must fail over to remote DC.
  - After DC recovery: run repair, replay hints.

Scenario 4: Network partition (split-brain)
  - Both sides continue serving independently.
  - After partition heals: last-write-wins conflict resolution.
  - Repair reconciles diverged data.
```

---

## 5. Hinted Handoff

### 5.1 How Hinted Handoff Works

When a write's target replica is down, the coordinator stores a "hint" -- a copy of the mutation destined for the unavailable node.

```
Write path with hints:
1. Client sends write to coordinator.
2. Coordinator sends write to replicas.
3. Replica A: acknowledges.
4. Replica B: acknowledges.
5. Replica C: DOWN (unreachable).
6. Coordinator stores a hint for Replica C.
7. When Replica C comes back, coordinator replays the hint.
```

### 5.2 Configuration

```yaml
# cassandra.yaml
hinted_handoff_enabled: true

# Maximum time to store hints for a down node.
# After this window, hints are dropped.
max_hint_window: 10800000            # 3 hours (default), in milliseconds
# Set higher for longer expected outages (e.g., maintenance):
# max_hint_window: 86400000          # 24 hours

# Hint delivery throttle (per destination)
hinted_handoff_throttle_in_kb: 1024  # 1 MB/s per destination

# Hint storage directory
hints_directory: /data/cassandra/hints

# Hint compression
hints_compression:
  - class_name: LZ4Compressor
```

### 5.3 Monitoring Hints

```bash
# Check pending hints
nodetool tpstats | grep -i hint

# Total hints stored on this node
nodetool info | grep "Hints"

# Hints not stored (dropped because max_hint_window exceeded)
# JMX: org.apache.cassandra.metrics:type=Storage,name=TotalHintsNotStored

# View hints directory size
du -sh /data/cassandra/hints/
```

### 5.4 Limitations

```
1. Hints are NOT a replacement for repair.
   - Hints are only stored within max_hint_window (default 3 hours).
   - If a node is down longer, mutations are lost.
   - Repair must run to reconcile.

2. Hints consume disk space on the coordinator.
   - A popular partition with a down replica generates many hints.
   - If hints fill the disk, the coordinator itself can become unhealthy.

3. CL=ANY counts hints as acknowledgment.
   - Data may exist ONLY as a hint.
   - If the coordinator (hint holder) fails before replay, data is lost.
   - NEVER use CL=ANY for important data.

4. Hints are per-coordinator.
   - Different coordinators hold hints for the same down node.
   - When the node recovers, each coordinator replays its hints independently.
```

---

## 6. Read Repair

### 6.1 Synchronous Read Repair

Read repair occurs automatically during reads when digests from different replicas do not match.

```
Read with CL=QUORUM (RF=3):
1. Coordinator sends data request to Replica A (closest).
2. Coordinator sends digest request to Replica B.
3. Compare digests.
4. If MATCH: return data. No repair needed.
5. If MISMATCH:
   a. Fetch full data from both replicas.
   b. Compare cell timestamps.
   c. Merge: keep the latest timestamp for each cell.
   d. Return merged result to client.
   e. Send the correct (merged) data to the stale replica.
```

### 6.2 Background Read Repair (Deprecated)

```sql
-- In Cassandra 3.x:
-- read_repair_chance controlled background read repair probability.
-- dclocal_read_repair_chance controlled DC-local probability.

CREATE TABLE users (
    user_id uuid PRIMARY KEY,
    name text
) WITH read_repair_chance = 0.1
  AND dclocal_read_repair_chance = 0.1;

-- In Cassandra 4.0+:
-- read_repair_chance is REMOVED (always 0).
-- dclocal_read_repair_chance is REMOVED (always 0).
-- Synchronous read repair still occurs automatically during multi-replica reads.
-- Background read repair is replaced by regular anti-entropy repair.
```

### 6.3 Speculative Read Repair

```sql
-- Speculative retry can trigger additional reads, increasing
-- the chance of detecting and repairing inconsistencies.

ALTER TABLE orders WITH speculative_retry = '99percentile';
-- If the first replica is slow, a second read is sent.
-- Both responses are compared, enabling read repair.
```

---

## 7. Anti-Entropy Repair

### 7.1 How Repair Works

```
1. Coordinator node initiates repair for a token range.
2. Each replica builds a Merkle tree (hash tree) of its data for that range.
3. Merkle trees are compared between replicas.
4. Differences are identified at the leaf level.
5. The stale replica streams the missing/outdated data from the replica
   with the latest version.
6. After streaming, both replicas are consistent for that range.
```

### 7.2 Repair Types

```bash
# Full repair: compare ALL data (Merkle trees of entire dataset)
nodetool repair -full <keyspace>
# Use after: node recovery, long outage, data corruption

# Incremental repair: compare only UNREPAIRED SSTables
nodetool repair <keyspace>
# Default in 4.0+. Faster because it skips already-repaired data.
# Marks repaired SSTables after completion.

# Primary range repair: repair only ranges this node is primary for
nodetool repair -pr <keyspace>
# Reduces redundant work when running repair on every node.
# Each node repairs only its "owned" ranges.

# Sub-range repair: repair a specific token range
nodetool repair -st <start_token> -et <end_token> <keyspace>
# For parallelizing repair across nodes.

# Preview repair (4.0+): dry run
nodetool repair --preview <keyspace>
# Shows what WOULD be repaired without modifying data.
# Useful for monitoring data divergence.

# DC-local repair
nodetool repair -local <keyspace>
# Repairs only within the local DC. Faster than cross-DC repair.

# Parallel vs. sequential
nodetool repair -par <keyspace>    # parallel (repairs multiple ranges simultaneously)
nodetool repair -seq <keyspace>    # sequential (one range at a time, lower load)
```

### 7.3 Repair Scheduling

```bash
# CRITICAL RULE: repair must complete within gc_grace_seconds.
# Default gc_grace_seconds = 864000 (10 days).
# If repair does not run in time, deleted data can resurrect
# (tombstones are garbage-collected before all replicas see the delete).

# Recommended schedule:
# Run repair every 7 days (leaves 3-day safety margin before gc_grace_seconds).

# Cron example (stagger across nodes):
# Node 1: Sunday 2 AM
# Node 2: Monday 2 AM
# Node 3: Tuesday 2 AM
0 2 * * 0  /usr/bin/nodetool repair -pr ecommerce   # primary range only
```

### 7.4 Cassandra Reaper

```bash
# Reaper is the standard tool for automated repair scheduling.
# https://cassandra-reaper.io/

# Features:
# - Schedules sub-range repairs across all nodes
# - Manages parallelism (intensity parameter)
# - Retries failed segments
# - Web UI for monitoring repair progress
# - Supports incremental and full repair

# Register a cluster
curl -X POST http://reaper:8080/cluster \
  -d "seedHost=10.0.1.1"

# Schedule repair
curl -X POST http://reaper:8080/repair_schedule \
  -d "clusterName=production" \
  -d "keyspace=ecommerce" \
  -d "scheduleDaysBetween=7" \
  -d "intensity=0.5" \
  -d "incrementalRepair=true"

# intensity: 0.0 to 1.0 (fraction of repair segments run in parallel)
# 0.5 = repair at 50% parallelism (balanced load)
```

### 7.5 Repair Impact

```yaml
# cassandra.yaml
# Throttle streaming during repair to reduce impact on production traffic
stream_throughput_outbound_megabits_per_sec: 200
inter_dc_stream_throughput_outbound_megabits_per_sec: 50

# Runtime adjustment:
# nodetool setstreamthroughput 100  (reduce during peak hours)

# Compaction during repair:
# Repair triggers anti-compaction (splitting SSTables into repaired/unrepaired).
# This creates temporary disk pressure.
compaction_throughput_mb_per_sec: 64
```

---

## 8. Tombstones and Data Resurrection

### 8.1 How Tombstones Work

```
When you DELETE data in Cassandra:
1. Cassandra does NOT remove the data from disk.
2. Instead, it writes a TOMBSTONE -- a marker that says "this data is deleted."
3. The tombstone has a timestamp (when the delete occurred).
4. During reads, tombstones suppress the deleted data.
5. During compaction, tombstones are garbage-collected after gc_grace_seconds.
```

### 8.2 Types of Tombstones

```sql
-- Row tombstone (deletes entire row)
DELETE FROM users WHERE user_id = 'user_42';

-- Cell tombstone (deletes a single column value)
DELETE email FROM users WHERE user_id = 'user_42';

-- Range tombstone (deletes a range of clustering rows)
DELETE FROM messages
WHERE conversation_id = 'conv_1'
  AND message_id > minTimeuuid('2026-01-01');

-- Partition tombstone (deletes entire partition)
DELETE FROM messages WHERE conversation_id = 'conv_1';

-- TTL expiry tombstone (automatic when TTL expires)
-- INSERT ... USING TTL 3600;  -- creates a tombstone after 1 hour

-- Collection tombstone (deletes a set/list/map element)
UPDATE users SET tags = tags - {'old_tag'} WHERE user_id = 'user_42';
```

### 8.3 Data Resurrection (Zombie Data)

```
How data resurrection happens:

Timeline:
  Day 0:  INSERT row on all 3 replicas.
  Day 1:  DELETE row. Tombstone written to Replica A and B.
          Replica C is DOWN (doesn't receive the tombstone).
  Day 11: gc_grace_seconds expires (10 days).
          Compaction on Replica A and B removes the tombstone.
  Day 15: Replica C comes back online.
          It still has the original row (no tombstone).
  Day 16: Read with CL=ONE hits Replica C.
          Returns the "deleted" row.
          The row has been RESURRECTED.

Prevention:
  1. Run repair within gc_grace_seconds (every 7 days).
  2. Ensure hints are delivered for short outages.
  3. If a node is down > gc_grace_seconds, run repair BEFORE
     it rejoins the cluster to propagate tombstones.
```

### 8.4 gc_grace_seconds Configuration

```sql
-- Per-table setting
CREATE TABLE events (
    id uuid PRIMARY KEY,
    data text
) WITH gc_grace_seconds = 864000;   -- 10 days (default)

-- For tables with frequent deletes and regular repair:
ALTER TABLE events WITH gc_grace_seconds = 259200;  -- 3 days

-- For append-only tables (no deletes):
ALTER TABLE audit_log WITH gc_grace_seconds = 0;
-- WARNING: gc_grace_seconds = 0 means tombstones are removed immediately
-- during compaction. Only safe if you NEVER delete from this table.

-- For TTL-only tables with TWCS:
ALTER TABLE metrics WITH gc_grace_seconds = 0;
-- Safe with TWCS because expired SSTables are dropped as whole files.
```

---

## 9. Lightweight Transactions (LWT)

### 9.1 Compare-and-Set Operations

```sql
-- INSERT IF NOT EXISTS (check-then-insert)
INSERT INTO users (user_id, email) VALUES ('user_42', 'alice@example.com')
IF NOT EXISTS;

-- Returns [applied] = true if inserted, false if user_id already existed.

-- UPDATE IF condition (check-then-update)
UPDATE inventory SET quantity = quantity - 1
WHERE product_id = ? AND warehouse_id = 'wh-east'
IF quantity > 0;

-- Returns [applied] = true if updated, false if quantity was 0.

-- DELETE IF EXISTS
DELETE FROM reservations WHERE reservation_id = ?
IF EXISTS;
```

### 9.2 Paxos Protocol (Cassandra 3.x-4.x)

```
LWT uses the Paxos consensus protocol:

1. PREPARE phase: coordinator sends proposal to replicas.
2. PROMISE phase: replicas promise not to accept older proposals.
3. PROPOSE phase: coordinator sends the actual value.
4. COMMIT phase: replicas commit the value.

This is 4 round-trips (vs. 1 for normal writes).
LWT is 10-20x slower than regular writes.
```

### 9.3 Accord Protocol (Cassandra 5.0)

```sql
-- Accord replaces Paxos for LWT in Cassandra 5.0.
-- No change in CQL syntax; the improvement is internal.

-- Accord advantages over Paxos:
-- 1. Leaderless: no single proposer bottleneck.
-- 2. Lower latency: fewer round-trips in the common case.
-- 3. Multi-DC friendly: designed for distributed consensus across DCs.
-- 4. Supports multi-partition transactions (future).

INSERT INTO users (user_id, email) VALUES ('user_42', 'alice@example.com')
IF NOT EXISTS;
-- Same syntax, but uses Accord internally on Cassandra 5.0.
```

### 9.4 LWT Performance Impact

```yaml
# cassandra.yaml
# LWT contention timeout
cas_contention_timeout: 1000   # milliseconds (default: 1000)

# Paxos state purging (4.1+)
# Paxos leaves state in system.paxos table that needs cleanup.
paxos_state_purging: repaired  # auto-purge after repair (4.1+)
```

```bash
# Monitor LWT performance
nodetool tpstats | grep -i "cas"
# CAS_READ_STAGE and CAS_WRITE_STAGE thread pools.
# High pending = LWT contention.

# Check system.paxos table size (can grow large)
nodetool tablestats system.paxos | grep "Space used"
```

---

## 10. Transient Replication

### 10.1 Concept (Cassandra 4.0, Experimental)

Transient replication allows creating "cheap" replicas that hold data temporarily for availability but do not persist data long-term.

```sql
-- Transient replication keyspace
-- Syntax: <full_replicas>/<total_replicas>
CREATE KEYSPACE test_transient
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': '3/5'   -- 3 full replicas, 2 transient replicas
};

-- Transient replicas:
-- Hold data temporarily (until repair confirms full replicas have it).
-- Do NOT participate in read quorum.
-- Reduce the storage and repair cost of maintaining extra availability.
```

### 10.2 Limitations

```
1. EXPERIMENTAL: not recommended for production.
2. Requires careful understanding of consistency implications.
3. Transient replicas do not count toward read quorum.
4. LWT is not supported with transient replication.
5. Some nodetool operations behave differently.
```

---

## 11. Cassandra 4.x/5.x Fault Tolerance Features

### 11.1 Cassandra 4.0

- **Improved incremental repair**: repaired/unrepaired SSTable tracking is more reliable. Anti-compaction overhead is reduced.
- **Preview repair**: `nodetool repair --preview` shows divergence without repairing.
- **Zero-Copy Streaming**: 5x faster repair streaming and bootstrap.
- **Transient replication** (experimental): cheap replicas for improved availability.
- **Virtual tables**: monitor repair and streaming progress via CQL.

### 11.2 Cassandra 4.1

- **Paxos state purging**: automatic cleanup of system.paxos table after repair.
- **Guardrails**: prevent configurations that undermine fault tolerance (e.g., RF < 3).
- **Top partitions**: identify hot partitions that might cause cascade failures.

### 11.3 Cassandra 5.0

- **Accord protocol**: replaces Paxos for LWT. Lower latency, leaderless, multi-DC native.
- **Transactional Cluster Metadata (TCM)**: Raft-based consensus for cluster metadata, replacing gossip for schema and topology changes. More reliable than gossip for critical state.
- **Guardrails v2**: enhanced cluster-wide safety limits.

```sql
-- Cassandra 5.0: Accord-based LWT
-- Same syntax, better performance
INSERT INTO accounts (account_id, balance) VALUES ('acct_1', 1000.00)
IF NOT EXISTS;

-- Multi-partition transactions (future Accord feature)
-- Not yet available in 5.0, but the protocol supports it.
```

---

## 12. Operational Procedures

### 12.1 Handling a Node Failure

```bash
# Step 1: Identify the failed node
nodetool status
# Look for DN (Down/Normal) nodes

# Step 2: Determine if the node will recover
# If temporary failure (reboot, maintenance):
#   - Do nothing. Hints will be delivered when it returns.
#   - If down > max_hint_window (3h), plan a repair after recovery.

# If permanent failure (disk failure, hardware death):
#   - Replace the node:
nodetool removenode <host_id>     # remove from ring
# Start a new node with the same token range (auto_bootstrap: true)

# Step 3: After recovery, run repair
nodetool repair -full <keyspace>
```

### 12.2 Handling a DC Failure

```bash
# Step 1: Confirm surviving DCs are healthy
nodetool status

# Step 2: If using LOCAL_QUORUM, surviving DCs continue operating
# No action needed for surviving DCs.

# Step 3: After failed DC recovers:
# - Verify all nodes show UN
# - Run repair to reconcile data
nodetool repair -full <keyspace>

# Step 4: Check hint backlog (may be empty if down > max_hint_window)
nodetool tpstats | grep -i hint
```

### 12.3 Verifying Data Consistency

```bash
# Preview repair: check divergence without repairing
nodetool repair --preview ecommerce
# Shows how much data needs repair.

# Tracing a specific read:
cqlsh -e "
  TRACING ON;
  CONSISTENCY ALL;
  SELECT * FROM ecommerce.orders WHERE order_id = ?;
"
# Tracing shows if replicas returned different data.

# Compare across DCs:
# Write a value in DC-A, read in DC-B after a short delay.
# If the value matches, cross-DC replication is working.
```

### 12.4 Draining Before Maintenance

```bash
# Always drain before any planned maintenance
nodetool drain

# drain:
# 1. Stops accepting new connections.
# 2. Flushes all memtables to SSTables.
# 3. Ensures commitlog can be safely discarded.
# 4. Leaves the process running (stop separately).

# Then stop:
systemctl stop cassandra

# After maintenance:
systemctl start cassandra
# Wait for the node to rejoin (UN in nodetool status).
```

---

## 13. Troubleshooting

### 13.1 UnavailableException

**Symptom**: reads/writes fail with `UnavailableException`.

**Cause**: not enough live replicas to satisfy the consistency level.

**Fix**:
```bash
# Check which nodes are down
nodetool status

# Determine if the CL is too high for current cluster state
# RF=3, LOCAL_QUORUM: needs 2 of 3 replicas alive in the DC

# Temporary: downgrade CL
CONSISTENCY LOCAL_ONE;
SELECT * FROM ...;

# Permanent: bring the failed node(s) back online
# Or replace dead nodes and repair
```

### 13.2 WriteTimeoutException

**Symptom**: writes fail with `WriteTimeoutException`.

**Cause**: replicas did not acknowledge within `write_request_timeout_in_ms` (default 2 seconds).

**Fix**:
```yaml
# cassandra.yaml
write_request_timeout_in_ms: 2000   # increase if needed (but investigate root cause)

# Common root causes:
# 1. Disk I/O bottleneck (check iostat)
# 2. GC pauses on replica (check gc.log)
# 3. Network issue between coordinator and replica
# 4. Overloaded replica (check nodetool tpstats)
```

### 13.3 ReadTimeoutException

**Symptom**: reads fail with `ReadTimeoutException`.

**Cause**: replicas did not respond within `read_request_timeout_in_ms` (default 5 seconds).

**Fix**:
```bash
# Check for large partitions
nodetool tablestats <ks>.<table> | grep "Compacted partition maximum"

# Check tombstone count per read
nodetool tablestats <ks>.<table> | grep "tombstones"

# Reduce partition size (add bucketing)
# Reduce tombstones (fix delete patterns, run compaction)
# Increase timeout (temporary): read_request_timeout_in_ms: 10000
```

### 13.4 Zombie Data (Deleted Data Reappears)

**Symptom**: previously deleted rows reappear.

**Fix**:
```bash
# Run repair immediately
nodetool repair -full <keyspace>

# Prevent recurrence:
# 1. Run repair within gc_grace_seconds (every 7 days)
# 2. If a node was down > gc_grace_seconds:
#    Run repair BEFORE allowing it to serve reads
# 3. Consider using Reaper for automated repair scheduling
```

### 13.5 Repair Takes Too Long

**Symptom**: repair runs for days, impacting production.

**Fix**:
```bash
# Use sub-range repair for parallelism
nodetool repair -st <start> -et <end> <keyspace>

# Use Reaper with intensity=0.5 (50% parallelism)

# Increase streaming throughput during repair window
nodetool setstreamthroughput 400

# Use primary-range repair to avoid redundant work
nodetool repair -pr <keyspace>
```

### 13.6 Hinted Handoff Backlog Growing

**Symptom**: hint count keeps increasing; not being delivered.

**Fix**:
```bash
# Check if destination node is alive
nodetool status

# If node is alive but hints aren't being delivered:
# 1. Check hint delivery throttle
grep hinted_handoff_throttle /etc/cassandra/cassandra.yaml

# 2. Check disk space on hint-holding node
du -sh /data/cassandra/hints/

# 3. If max_hint_window exceeded, hints are dropped
# Run repair after the node recovers
```

### 13.7 Consistency Violations Detected

**Symptom**: same key returns different values from different nodes.

**Fix**:
```bash
# Verify with tracing
cqlsh -e "
  TRACING ON;
  CONSISTENCY ALL;
  SELECT * FROM <ks>.<table> WHERE pk = ?;
"
# Check if different replicas return different timestamps.

# Run repair to reconcile
nodetool repair -full <keyspace> <table>

# If clock skew caused wrong conflict resolution:
# Sync NTP on all nodes
ntpq -p    # check NTP sync status
```

### 13.8 Paxos (LWT) Contention

**Symptom**: `CasWriteTimeoutException` on IF-based queries.

**Fix**:
```sql
-- Reduce contention by sharding the hot partition
-- Instead of one global counter, use per-shard counters

-- Increase CAS timeout
-- cassandra.yaml: cas_contention_timeout: 5000

-- Monitor CAS thread pools
-- nodetool tpstats | grep -i cas
```

### 13.9 system.paxos Table Growing Too Large

**Symptom**: system.paxos table consumes significant disk space.

**Fix**:
```bash
# Cassandra 4.1+: enable automatic paxos state purging
# cassandra.yaml: paxos_state_purging: repaired

# Manual cleanup: run repair on the system keyspace
nodetool repair -full system

# Compact system.paxos
nodetool compact system paxos
```

### 13.10 Inconsistent RF After Keyspace Alteration

**Symptom**: data not replicated to expected number of nodes after ALTER KEYSPACE.

**Fix**:
```bash
# ALTER KEYSPACE changes the replication metadata but does NOT move data.
# You must run repair to stream data to the new replica set.

nodetool repair -full <keyspace>

# Verify replica count
nodetool describering <keyspace>
```

---

## 14. FAQ

### Q1: What is the difference between eventual consistency and strong consistency in Cassandra?

Eventual consistency means all replicas will converge to the same value *eventually* (via anti-entropy repair, read repair, hints). Strong consistency means every read returns the most recently written value, achieved when `R + W > RF`.

### Q2: Why does Cassandra use "last write wins" for conflict resolution?

Cassandra is a masterless system; any node can accept writes independently. When replicas receive conflicting writes, Cassandra resolves by keeping the cell with the highest timestamp. This is simple and deterministic but can lead to unexpected results with clock skew.

### Q3: What happens if I never run repair?

Replicas will drift apart over time. Deleted data may resurrect (tombstone garbage collection without all replicas seeing the tombstone). Counters will diverge. Read repair helps but only on the read path and only for queried data.

### Q4: Can I reduce gc_grace_seconds below 10 days?

Yes, if you run repair more frequently. The rule is: `gc_grace_seconds > repair_interval`. If you repair every 3 days, you can set gc_grace_seconds to 5 days. Never set it to 0 unless the table is purely append-only with no deletes.

### Q5: Is LOCAL_QUORUM always better than QUORUM in multi-DC?

For latency, yes. LOCAL_QUORUM does not wait for cross-DC acknowledgments. For cross-DC consistency, no -- LOCAL_QUORUM provides strong consistency only within the local DC. Use QUORUM or EACH_QUORUM if you need cross-DC strong consistency (rare and expensive).

### Q6: What is the difference between repair -full and repair (incremental)?

Full repair compares ALL data between replicas. Incremental repair compares only unrepaired SSTables (data written since the last repair). Incremental is faster but requires reliable SSTable repaired-state tracking (reliable in 4.0+).

### Q7: Can I have different consistency levels for different queries?

Yes. Consistency level is set per query, not per table or keyspace. You can use LOCAL_QUORUM for important writes and ONE for low-priority reads within the same session.

### Q8: What is the maximum number of nodes that can fail before data is lost?

With RF=3 and no repair, losing all 3 replicas of a partition results in data loss. With regular repair, the window is smaller: only losing all replicas *simultaneously* (before any are repaired) causes permanent loss.

### Q9: How does Cassandra handle clock skew?

Cassandra relies on timestamps for conflict resolution (last-write-wins). Clock skew > 1 second between nodes can cause the "wrong" write to win. Mitigation: run NTP on all nodes, use client-provided timestamps when possible.

### Q10: What is the Accord protocol in Cassandra 5.0?

Accord is a leaderless distributed transaction protocol that replaces Paxos for lightweight transactions. It provides lower latency because it does not require a single proposer/leader, and it is designed natively for multi-DC deployments. The CQL syntax for LWT does not change.

### Q11: Should I use transient replication?

Not in production. Transient replication is experimental in Cassandra 4.0 and may have subtle consistency implications. Wait for it to be marked stable in a future release.

### Q12: How does read repair interact with consistency level?

Read repair only triggers when reading from multiple replicas (CL >= TWO, QUORUM, etc.). With CL=ONE, no digest comparison occurs, so no read repair happens. If you use CL=ONE exclusively, you depend entirely on hinted handoff and anti-entropy repair for consistency.

---

*Questo documento fa parte del modulo 07 "NoSQL Cassandra" della Data Encyclopedia.*
