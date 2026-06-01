# Cassandra: Operations e Monitoring

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
1. Node Operations
2. Cluster Lifecycle Management
3. Monitoring Infrastructure
4. JMX Metrics Deep Dive
5. Prometheus and Grafana Integration
6. Backup and Restore
7. Repair Operations
8. Compaction Management
9. Log Analysis
10. Alerting Strategy
11. Capacity Planning
12. Cassandra 4.x/5.x Operations Features
13. Troubleshooting
14. FAQ

---

## 1. Node Operations

### 1.1 Starting and Stopping Cassandra

```bash
# Start Cassandra in the foreground (useful for debugging)
cassandra -f

# Start Cassandra as a daemon (production)
cassandra

# Start with specific JVM options
JVM_OPTS="-Xms8G -Xmx8G" cassandra

# Graceful shutdown: flush memtables to SSTables, then stop
nodetool drain
systemctl stop cassandra

# Hard kill (last resort; may lose unflushed data)
pkill -9 -f CassandraDaemon
```

### 1.2 Essential nodetool Commands

```bash
# Cluster-level status
nodetool status                    # DC/rack, load, tokens, state per node
nodetool describecluster           # cluster name, schema versions, snitch
nodetool ring                      # token ownership per node

# Node-level info
nodetool info                      # uptime, heap, data load, gossip state
nodetool version                   # Cassandra version
nodetool gossipinfo                # raw gossip state of all known nodes

# Data operations
nodetool flush <keyspace>          # flush memtables to SSTables
nodetool compact <keyspace> <table>  # force compaction
nodetool cleanup <keyspace>        # remove data no longer owned by this node
nodetool scrub <keyspace> <table>  # rebuild SSTables from data files

# Repair
nodetool repair -full <keyspace>   # full anti-entropy repair
nodetool repair -pr <keyspace>     # repair only primary range

# Token management
nodetool move <new_token>          # reassign token (single-token nodes)
nodetool removenode <host_id>      # remove a dead node from the cluster
nodetool assassinate <endpoint>    # force remove unresponsive node

# Streaming
nodetool netstats                  # active streams (bootstrap, repair)
nodetool rebuild -- <source_dc>    # stream all data from a source DC

# Thread pools and latency
nodetool tpstats                   # thread pool stats, dropped messages
nodetool proxyhistograms           # read/write/range latency histograms
nodetool tablehistograms <ks> <t>  # per-table latency, partition size

# Snapshot
nodetool snapshot -t <tag> <ks>    # create named snapshot
nodetool listsnapshots             # list all snapshots
nodetool clearsnapshot -t <tag>    # delete snapshot
```

### 1.3 Node States

| State | Symbol | Meaning |
|-------|--------|---------|
| Up/Normal | `UN` | Healthy, serving requests |
| Up/Leaving | `UL` | Decommissioning, streaming data out |
| Up/Joining | `UJ` | Bootstrapping, streaming data in |
| Up/Moving | `UM` | Moving token ranges |
| Down/Normal | `DN` | Not responding but still a ring member |

```bash
# Example nodetool status output:
# Datacenter: us-east-1
# =======================
# Status=Up/Down  |/ State=Normal/Leaving/Joining/Moving
# --  Address     Load       Tokens  Owns   Host ID                               Rack
# UN  10.0.1.1    15.2 GiB   256     33.3%  a1b2c3d4-...  rack1
# UN  10.0.1.2    14.8 GiB   256     33.4%  e5f6g7h8-...  rack2
# DN  10.0.1.3    15.0 GiB   256     33.3%  i9j0k1l2-...  rack3
```

---

## 2. Cluster Lifecycle Management

### 2.1 Adding a Node

```bash
# 1. Install Cassandra on the new server (same version as existing cluster)
# 2. Configure cassandra.yaml:
#    cluster_name: same as existing cluster
#    seeds: include 2-3 existing seeds (do NOT include the new node as seed)
#    listen_address: new node's IP
#    rpc_address: new node's IP
#    auto_bootstrap: true  (default)

# 3. Start the node
cassandra

# 4. Monitor bootstrap progress
nodetool netstats                  # streaming progress
nodetool status                    # should show UJ, then UN

# 5. After bootstrap completes, run cleanup on EXISTING nodes
# This removes data that now belongs to the new node
nodetool cleanup <keyspace>        # run on each existing node
```

### 2.2 Decommissioning a Node

```bash
# Gracefully removes a node and streams its data to remaining nodes
nodetool decommission

# Monitor progress
nodetool netstats

# After completion, the node leaves the ring and stops.
# DO NOT just shut down a node -- that leaves its token range unowned.
```

### 2.3 Removing a Dead Node

```bash
# If a node is permanently dead and cannot be decommissioned:
nodetool removenode <host_id>

# Get host_id from: nodetool status (look for DN nodes)
# removenode streams the dead node's data to remaining replicas.

# If removenode hangs or the node is truly gone:
nodetool assassinate <ip_address>
# WARNING: assassinate does NOT stream data. Use only as last resort.
# Run repair after assassinate to ensure data integrity.
```

### 2.4 Rolling Restart

```bash
# Restart nodes one at a time for configuration changes
# Order: one node at a time, wait for UN status before proceeding

# On each node:
nodetool drain                     # flush all memtables
systemctl restart cassandra        # restart the process

# Wait for the node to rejoin
nodetool status                    # verify UN state

# Proceed to next node only after the restarted node is UN
# and all pending compactions are manageable.
```

### 2.5 Upgrading Cassandra

```bash
# 1. Read the upgrade guide for your version transition
# 2. Take snapshots on ALL nodes
nodetool snapshot -t pre_upgrade

# 3. Upgrade one DC at a time (in multi-DC setups)
# 4. Within a DC, upgrade one node at a time:
nodetool drain
systemctl stop cassandra
# Install new Cassandra version
systemctl start cassandra

# 5. After all nodes upgraded, run:
nodetool upgradesstables           # rewrite SSTables to new format

# 6. Verify:
nodetool version                   # confirm new version
nodetool describecluster           # confirm schema agreement
```

---

## 3. Monitoring Infrastructure

### 3.1 Monitoring Stack Overview

```
Cassandra Nodes --[JMX]--> JMX Exporter --[/metrics]--> Prometheus --> Grafana
                                                                         |
                                                                    Alertmanager
                                                                         |
                                                                   PagerDuty/Slack
```

### 3.2 JMX Configuration

```yaml
# cassandra-env.sh
# Enable JMX on a specific port (default 7199)
JMX_PORT=7199

# For remote JMX access (monitoring servers):
# WARNING: never expose JMX over untrusted networks without auth + TLS
LOCAL_JMX=no
# Set JMX auth in jmxremote.password and jmxremote.access

# cassandra.yaml (Cassandra 4.0+)
# JMX can also be configured via yaml:
# jmx_port: 7199
```

### 3.3 Virtual Tables (Cassandra 4.0+)

```sql
-- system_views keyspace: query node state via CQL instead of JMX
-- Available in Cassandra 4.0+

-- Active SSTable tasks (compaction, streaming)
SELECT * FROM system_views.sstable_tasks;

-- Connected clients
SELECT * FROM system_views.clients;

-- Thread pool stats
SELECT * FROM system_views.thread_pools;

-- Internode messaging
SELECT * FROM system_views.internode_inbound;
SELECT * FROM system_views.internode_outbound;

-- Settings
SELECT * FROM system_views.settings;
-- Lists all cassandra.yaml settings and their current values.
-- Extremely useful for verifying configuration on remote nodes.
```

---

## 4. JMX Metrics Deep Dive

### 4.1 Critical Metrics Categories

```
org.apache.cassandra.metrics:
├── type=ClientRequest          # read/write latency, timeouts
├── type=ColumnFamily           # per-table stats (legacy name)
├── type=Table                  # per-table stats (4.0+ name)
├── type=Keyspace               # per-keyspace aggregates
├── type=ThreadPools            # internal thread pool utilization
├── type=Storage                # load, hints, exceptions
├── type=Compaction             # pending tasks, bytes compacted
├── type=CommitLog              # commitlog size, pending tasks
├── type=DroppedMessage         # messages dropped due to overload
├── type=Cache                  # key cache, row cache, counter cache
├── type=CQL                    # prepared statements, regular statements
└── type=Streaming              # active streams, throughput
```

### 4.2 Read/Write Latency Metrics

```bash
# Key metrics to monitor (JMX paths):
# ClientRequest.Read.Latency        -- read latency histogram
# ClientRequest.Write.Latency       -- write latency histogram
# ClientRequest.Read.Timeouts       -- read timeout count
# ClientRequest.Write.Timeouts      -- write timeout count
# ClientRequest.Read.Unavailables   -- reads rejected due to CL
# ClientRequest.Write.Unavailables  -- writes rejected due to CL

# nodetool shortcut:
nodetool proxyhistograms

# Example output:
# proxy histograms
# Percentile      Read Latency     Write Latency    Range Latency
#                     (micros)         (micros)          (micros)
# 50%                  354.00           279.00          3379.00
# 75%                  519.00           421.00          5765.00
# 95%                 1708.00          1708.00         15109.00
# 99%                 4947.00          4947.00         74975.00
# Min                   42.00            42.00          1708.00
# Max                51472.00         51472.00        124031.00
```

### 4.3 Thread Pool Metrics

```bash
nodetool tpstats

# CRITICAL columns:
# Active   -- threads currently processing
# Pending  -- tasks queued waiting for a thread
# Blocked  -- tasks rejected (pool exhausted)
# Dropped  -- messages dropped (timeout before processing)

# Key thread pools:
# ReadStage           -- local read requests
# MutationStage       -- local write requests
# CounterMutationStage -- counter writes
# ViewMutationStage   -- materialized view writes
# CompactionExecutor  -- compaction tasks
# MemtableFlushWriter -- flushing memtables to disk
# GossipStage         -- gossip protocol messages
# AntiEntropyStage    -- repair-related tasks
# Native-Transport-Requests  -- CQL client requests

# Alert if:
# - Dropped messages > 0 on any pool
# - Pending > 0 sustained on ReadStage or MutationStage
# - Blocked > 0 on any pool
```

### 4.4 Table-Level Metrics

```bash
nodetool tablestats <keyspace>.<table>

# Key fields:
# SSTable count               -- number of SSTables on this node
# Space used (live)            -- actual data size
# Space used (total)           -- including tombstones and old versions
# Number of partitions (estimate)
# Memtable cell count          -- cells in the active memtable
# Memtable data size           -- bytes in the active memtable
# Memtable switch count        -- number of memtable flushes
# Local read count / latency   -- reads served by this node
# Local write count / latency  -- writes served by this node
# Pending flushes              -- memtables waiting to flush
# Bloom filter false positives -- indicates suboptimal bloom filter
# Compacted partition minimum/mean/maximum bytes  -- partition sizing
# Tombstone scanned per read   -- high values indicate tombstone problem

# Per-table latency histograms:
nodetool tablehistograms <keyspace>.<table>
```

---

## 5. Prometheus and Grafana Integration

### 5.1 JMX Exporter Setup

```yaml
# Download: https://github.com/prometheus/jmx_exporter
# Add to cassandra-env.sh:
JVM_OPTS="$JVM_OPTS -javaagent:/opt/jmx_exporter/jmx_prometheus_javaagent.jar=9500:/opt/jmx_exporter/cassandra.yml"

# /opt/jmx_exporter/cassandra.yml (metric filtering config):
---
lowercaseOutputName: true
lowercaseOutputLabelNames: true
rules:
  # Client request metrics
  - pattern: org.apache.cassandra.metrics<type=ClientRequest, scope=(\w+), name=(\w+)><>(Count|OneMinuteRate|Mean|95thPercentile|99thPercentile)
    name: cassandra_client_request_$2
    labels:
      scope: "$1"
    type: GAUGE

  # Table metrics
  - pattern: org.apache.cassandra.metrics<type=Table, keyspace=(\w+), scope=(\w+), name=(\w+)><>(Count|Value|Mean|95thPercentile)
    name: cassandra_table_$3
    labels:
      keyspace: "$1"
      table: "$2"
    type: GAUGE

  # Thread pool metrics
  - pattern: org.apache.cassandra.metrics<type=ThreadPools, path=(\w+), scope=(\w+), name=(\w+)><>Value
    name: cassandra_threadpool_$3
    labels:
      pool_type: "$1"
      pool_name: "$2"
    type: GAUGE

  # Compaction metrics
  - pattern: org.apache.cassandra.metrics<type=Compaction, name=(\w+)><>(Count|Value)
    name: cassandra_compaction_$1
    type: GAUGE

  # Dropped messages
  - pattern: org.apache.cassandra.metrics<type=DroppedMessage, scope=(\w+), name=(\w+)><>(Count|OneMinuteRate)
    name: cassandra_dropped_message_$2
    labels:
      message_type: "$1"
    type: GAUGE

  # Storage metrics
  - pattern: org.apache.cassandra.metrics<type=Storage, name=(\w+)><>(Count|Value)
    name: cassandra_storage_$1
    type: GAUGE

  # Cache metrics
  - pattern: org.apache.cassandra.metrics<type=Cache, scope=(\w+), name=(\w+)><>(Count|Value|OneMinuteRate)
    name: cassandra_cache_$2
    labels:
      cache: "$1"
    type: GAUGE
```

### 5.2 Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'cassandra'
    scrape_interval: 15s
    static_configs:
      - targets:
          - '10.0.1.1:9500'
          - '10.0.1.2:9500'
          - '10.0.1.3:9500'
        labels:
          dc: 'us-east-1'
      - targets:
          - '10.0.2.1:9500'
          - '10.0.2.2:9500'
        labels:
          dc: 'eu-west-1'
```

### 5.3 Key Grafana Dashboard Panels

```
Recommended Grafana dashboard panels:

1. Cluster Overview
   - Nodes up/down per DC
   - Total cluster load (GB)
   - Read/write request rate (ops/sec)

2. Latency
   - p50/p95/p99 read latency per node
   - p50/p95/p99 write latency per node
   - Range scan latency

3. Throughput
   - Read requests/sec per node
   - Write requests/sec per node
   - Cross-DC replication throughput

4. Errors
   - Dropped messages per message type
   - Timeouts (read/write)
   - Unavailable errors

5. Storage
   - Disk usage per node
   - SSTable count per table
   - Pending compactions

6. JVM
   - Heap usage
   - GC pause time and frequency
   - Off-heap memory usage

7. Thread Pools
   - Active/Pending/Blocked per pool
   - Mutation stage depth
   - Read stage depth

8. Compaction
   - Compaction bytes throughput
   - Pending compaction tasks
   - SSTable count trend
```

### 5.4 Useful PromQL Queries

```promql
# Average read latency per node (p99)
cassandra_client_request_latency{scope="Read",quantile="0.99"}

# Write request rate
rate(cassandra_client_request_latency_count{scope="Write"}[5m])

# Dropped messages rate
rate(cassandra_dropped_message_count[5m]) > 0

# Pending compactions
cassandra_compaction_pendingtasks

# Heap usage percentage
jvm_memory_bytes_used{area="heap"} / jvm_memory_bytes_max{area="heap"} * 100

# SSTable count per table (watch for growth)
cassandra_table_livesstablecount

# Tombstone ratio per read
cassandra_table_tombstonescannedhistogram{quantile="0.99"}
```

---

## 6. Backup and Restore

### 6.1 Snapshot-Based Backup

```bash
# Create a snapshot (hard-links SSTables; near-instant, no I/O)
nodetool snapshot -t daily_backup_20260522 ecommerce

# Snapshot location:
# <data_dir>/<keyspace>/<table>/snapshots/<tag>/

# List all snapshots
nodetool listsnapshots

# Example output:
# Snapshot name   Keyspace   Table        True size  Size on disk
# daily_backup... ecommerce  orders       15.2 GiB   15.2 GiB
# daily_backup... ecommerce  products     3.4 GiB    3.4 GiB

# Copy snapshots to remote storage
rsync -avz /data/cassandra/data/ecommerce/orders-*/snapshots/daily_backup_20260522/ \
  backup-server:/backups/cassandra/ecommerce/orders/20260522/

# Or use aws s3 sync for cloud storage:
aws s3 sync /data/cassandra/data/ecommerce/orders-*/snapshots/daily_backup_20260522/ \
  s3://cassandra-backups/ecommerce/orders/20260522/

# Clean up snapshots (they consume disk space as SSTables are compacted)
nodetool clearsnapshot -t daily_backup_20260522
```

### 6.2 Incremental Backup

```yaml
# cassandra.yaml
incremental_backups: true
# When enabled, every flushed SSTable is hard-linked to:
# <data_dir>/<keyspace>/<table>/backups/

# CAUTION: incremental backups accumulate hard-links forever.
# You MUST regularly copy and delete the backups/ directory
# or disk space will eventually be exhausted.
```

```bash
# Process incremental backups:
# 1. Copy new SSTables from backups/ directory
cp /data/cassandra/data/ecommerce/orders-*/backups/* /backup-staging/

# 2. Clear the backups directory
rm /data/cassandra/data/ecommerce/orders-*/backups/*

# 3. Combine with a periodic snapshot for a complete backup
```

### 6.3 Restore from Snapshot

```bash
# Restore procedure (per node):

# 1. Stop Cassandra
systemctl stop cassandra

# 2. Clear existing data for the table
rm -rf /data/cassandra/data/ecommerce/orders-*/*.db

# 3. Copy snapshot SSTables to the table directory
cp /backups/cassandra/ecommerce/orders/20260522/* \
   /data/cassandra/data/ecommerce/orders-<table_uuid>/

# 4. Start Cassandra
systemctl start cassandra

# 5. Run repair to ensure consistency with other nodes
nodetool repair -full ecommerce orders

# Alternative: use sstableloader (does not require stopping Cassandra)
sstableloader -d 10.0.1.1 /backups/cassandra/ecommerce/orders/20260522/
# This streams the SSTables to all replicas. No downtime.
```

### 6.4 Point-in-Time Recovery

```bash
# Cassandra does not natively support PITR.
# To achieve PITR:
# 1. Take regular snapshots (e.g., hourly)
# 2. Enable commitlog archiving:

# cassandra.yaml
commitlog_archiving:
  archive_command: '/usr/local/bin/archive_commitlog.sh %path %name'
  restore_command: '/usr/local/bin/restore_commitlog.sh %from %to'
  restore_directories: /data/cassandra/commitlog_restore/

# 3. To restore to a point in time:
#    a. Restore the most recent snapshot before the target time
#    b. Replay archived commitlogs up to the target timestamp
#    c. Start Cassandra

# NOTE: this is complex and error-prone. For critical workloads,
# consider Medusa (https://github.com/thelastpickle/cassandra-medusa)
# which automates backup/restore including PITR.
```

### 6.5 Backup Tools

```bash
# Medusa (The Last Pickle) -- production-grade backup tool
# Supports S3, GCS, Azure Blob, local storage
# Install:
pip install cassandra-medusa

# Backup:
medusa backup --backup-name=daily_20260522

# Restore:
medusa restore --backup-name=daily_20260522

# List backups:
medusa list-backups

# Verify backup integrity:
medusa verify --backup-name=daily_20260522
```

---

## 7. Repair Operations

### 7.1 Why Repair is Critical

Repair is the anti-entropy mechanism that ensures all replicas hold the same data. Without regular repair:
- Deleted data can resurrect (tombstone expiry + gc_grace_seconds).
- Read repair only fixes data on the read path (not all data).
- Hinted handoff covers only short outages (max_hint_window, default 3h).

### 7.2 Repair Types and Commands

```bash
# Full repair: compare all data via Merkle trees, stream differences
nodetool repair -full <keyspace>

# Incremental repair (default in 4.0+): only repair unrepaired SSTables
nodetool repair <keyspace>

# Primary range repair: repair only ranges this node is primary for
# Reduces redundant work when running repair on all nodes
nodetool repair -pr <keyspace>

# Sub-range repair: repair a specific token range
nodetool repair -st <start> -et <end> <keyspace>

# DC-local repair: repair only within the local DC
nodetool repair -local <keyspace>

# Preview repair (4.0+): dry run showing what would be repaired
nodetool repair --preview <keyspace>

# Repair a specific table
nodetool repair <keyspace> <table>

# Parallel repair (repairs multiple token ranges simultaneously)
nodetool repair -par <keyspace>

# Sequential repair (one range at a time; lower load)
nodetool repair -seq <keyspace>
```

### 7.3 Repair Scheduling Best Practices

```bash
# Rule: complete repair cycle within gc_grace_seconds
# Default gc_grace_seconds = 864000 (10 days)
# Run repair every 7 days (3-day safety margin)

# Use Cassandra Reaper for automated repair scheduling:
# https://cassandra-reaper.io/
# Reaper schedules sub-range repairs across all nodes,
# manages parallelism, and handles failures.

# Example Reaper API call:
curl -X POST http://reaper:8080/repair_schedule \
  -d "clusterName=production" \
  -d "keyspace=ecommerce" \
  -d "tables=orders,products" \
  -d "scheduleDaysBetween=7" \
  -d "intensity=0.5"
```

### 7.4 Repair Impact and Throttling

```yaml
# cassandra.yaml
# Limit repair's impact on production traffic

# Throttle validation compaction during repair
compaction_throughput_mb_per_sec: 64

# Throttle streaming during repair
stream_throughput_outbound_megabits_per_sec: 200
inter_dc_stream_throughput_outbound_megabits_per_sec: 50
```

---

## 8. Compaction Management

### 8.1 Monitoring Compaction

```bash
# View active compactions
nodetool compactionstats

# Example output:
# pending tasks: 42
# id        compaction type  keyspace   table    completed  total     unit   progress
# abc123    COMPACTION       ecommerce  orders   1.5 GiB    3.2 GiB  bytes  46.88%

# View compaction history
nodetool compactionhistory

# SSTable count per table (indicates compaction lag)
nodetool tablestats ecommerce.orders | grep "SSTable count"
```

### 8.2 Compaction Throttling

```yaml
# cassandra.yaml
# Limit compaction throughput to preserve I/O for reads/writes
compaction_throughput_mb_per_sec: 64    # default 64 MB/s

# Runtime adjustment (no restart):
nodetool setcompactionthroughput 32     # reduce during peak hours
nodetool setcompactionthroughput 128    # increase during maintenance window
```

### 8.3 Forcing Compaction

```bash
# Force major compaction on a table
nodetool compact ecommerce orders

# WARNING: major compaction creates a single large SSTable.
# This is NOT recommended for STCS (creates a huge file that
# won't compact with future smaller files).
# It IS fine for purging tombstones or one-time cleanup.

# Force compaction on all tables in a keyspace
nodetool compact ecommerce
```

### 8.4 Unified Compaction Strategy (Cassandra 5.0)

```sql
-- UCS automatically adapts behavior based on workload patterns
-- Replaces manual selection of STCS/LCS/TWCS
CREATE TABLE events (
    id uuid PRIMARY KEY,
    data text
) WITH compaction = {
    'class': 'UnifiedCompactionStrategy',
    'scaling_parameters': 'T4'   -- tuning parameter
};

-- scaling_parameters controls the trade-off:
-- T2-T4: more write-optimized (like STCS)
-- L4-L10: more read-optimized (like LCS)
-- N: number-based, for time-window behavior (like TWCS)
```

---

## 9. Log Analysis

### 9.1 Log Files

```bash
# Main log files:
# /var/log/cassandra/system.log    -- main application log
# /var/log/cassandra/debug.log     -- debug-level output
# /var/log/cassandra/gc.log        -- GC activity (JVM)

# Tail system log in real time
tail -f /var/log/cassandra/system.log

# Search for errors
grep -i "error\|exception\|warn" /var/log/cassandra/system.log | tail -50

# Search for slow queries (if slow query logging is enabled)
grep "Slow query" /var/log/cassandra/debug.log
```

### 9.2 Enabling Slow Query Logging

```yaml
# cassandra.yaml (4.0+)
slow_query_log_timeout_in_ms: 500    # log queries slower than 500ms

# Logs appear in debug.log:
# WARN  [Native-Transport-Requests-1] SlowQueryLogger.java:...
# Slow query: SELECT * FROM ecommerce.orders WHERE ...
# time: 1523ms
```

### 9.3 Audit Logging (Cassandra 4.0+)

```yaml
# cassandra.yaml
audit_logging_options:
  enabled: true
  logger:
    - class_name: BinAuditLogger     # binary format (efficient)
    # - class_name: FileAuditLogger  # text format (human-readable)
  included_keyspaces: ecommerce,user_data
  excluded_keyspaces: system,system_schema,system_auth
  included_categories: QUERY,DML,DDL,AUTH
  # QUERY: SELECT statements
  # DML: INSERT, UPDATE, DELETE
  # DDL: CREATE, ALTER, DROP
  # DCL: GRANT, REVOKE
  # AUTH: LOGIN attempts
  # PREPARE: PREPARE statements
  # ERROR: failed queries

# View binary audit logs:
auditlogviewer /var/log/cassandra/audit/
```

### 9.4 GC Log Analysis

```bash
# JVM GC settings (cassandra-env.sh or jvm11-server.options)
# Cassandra 4.x uses G1GC by default

# Key GC log patterns to watch:
# "GC pause" > 500ms indicates memory pressure
# "to-space exhausted" indicates heap too small
# "Full GC" should never happen in production

# Parse GC logs:
grep "GC pause" /var/log/cassandra/gc.log | awk '{print $1, $NF}'

# Use GCViewer or GCEasy for visual analysis
```

---

## 10. Alerting Strategy

### 10.1 Critical Alerts (Page Immediately)

```yaml
# Alert rules (Prometheus Alertmanager format):

groups:
  - name: cassandra_critical
    rules:
      - alert: CassandraNodeDown
        expr: up{job="cassandra"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Cassandra node {{ $labels.instance }} is down"

      - alert: CassandraDroppedMessages
        expr: rate(cassandra_dropped_message_count[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Dropped messages on {{ $labels.instance }}"

      - alert: CassandraHeapCritical
        expr: jvm_memory_bytes_used{area="heap"} / jvm_memory_bytes_max{area="heap"} > 0.90
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Heap usage > 90% on {{ $labels.instance }}"

      - alert: CassandraWriteUnavailable
        expr: rate(cassandra_client_request_unavailables_count{scope="Write"}[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Write unavailables on {{ $labels.instance }}"
```

### 10.2 Warning Alerts (Investigate During Business Hours)

```yaml
      - alert: CassandraPendingCompactions
        expr: cassandra_compaction_pendingtasks > 100
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Compaction backlog on {{ $labels.instance }}"

      - alert: CassandraHighReadLatency
        expr: cassandra_client_request_latency{scope="Read",quantile="0.99"} > 100000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "p99 read latency > 100ms on {{ $labels.instance }}"

      - alert: CassandraDiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/data"} / node_filesystem_size_bytes{mountpoint="/data"}) < 0.20
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Disk space < 20% on {{ $labels.instance }}"

      - alert: CassandraHintBacklog
        expr: cassandra_storage_totalhints > 10000
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Hint backlog > 10K on {{ $labels.instance }}"
```

---

## 11. Capacity Planning

### 11.1 Sizing Formula

```
Data per node = (Total raw data * RF) / Number of nodes

Disk requirement per node = Data per node * Compaction overhead factor
  - STCS: 2x (needs 50% free for compaction)
  - LCS: 1.1x (10% overhead)
  - TWCS: 1.5x

Memory: 32-64 GB RAM typical
  - JVM heap: 8-16 GB (never more than 16 GB with CMS; 31 GB with G1GC)
  - OS page cache: remaining RAM (the more the better for reads)

CPU: 8-16 cores per node
  - Write-heavy: more cores for compaction threads
  - Read-heavy: more cores for concurrent reads

Network: 1 Gbps minimum, 10 Gbps recommended
  - Cross-DC: dedicated WAN link or VPN
```

### 11.2 When to Add Nodes

```bash
# Add nodes when ANY of these thresholds are breached:

# 1. Disk utilization > 50% (STCS) or > 70% (LCS/TWCS)
#    Check: df -h /data/cassandra

# 2. CPU utilization sustained > 60%
#    Check: top, mpstat

# 3. p99 read latency increasing over weeks
#    Check: nodetool proxyhistograms

# 4. Pending compactions consistently > 0
#    Check: nodetool compactionstats

# 5. GC pauses > 500ms regularly
#    Check: gc.log
```

### 11.3 Hardware Recommendations

```
Production hardware per node:

CPU:      16-32 cores (modern x86_64)
RAM:      64-128 GB
          - JVM heap: 16 GB (G1GC) or 8 GB (ZGC)
          - Rest for OS page cache
Disk:     NVMe SSDs strongly recommended
          - Separate drive for commitlog (critical for write latency)
          - One or more drives for data
          - RAID-0 or JBOD for data drives (Cassandra handles redundancy)
Network:  10 Gbps NIC
OS:       Linux (Ubuntu 22.04 LTS, RHEL 8/9, Debian 12)

AVOID:
- Spinning disks (HDD) for data in production
- Network-attached storage (NAS/SAN) -- high latency kills performance
- EBS gp2 on AWS (use gp3 or io2 for consistent IOPS)
- Shared hosts / noisy neighbors
```

---

## 12. Cassandra 4.x/5.x Operations Features

### 12.1 Cassandra 4.0

- **Virtual tables**: CQL-accessible node state (`system_views`).
- **Audit logging**: built-in query auditing without external tools.
- **Full query logging (fql)**: capture every query for replay/analysis.
- **Improved incremental repair**: better repaired/unrepaired SSTable tracking.
- **Zero-copy streaming**: 5x faster node bootstrap and repair streaming.
- **Internode messaging v4**: single multiplexed connection per peer.
- **Diagnostic events**: subscribe to events via JMX for custom monitoring.
- **Preview repair**: `nodetool repair --preview` for dry-run repairs.

### 12.2 Cassandra 4.1

- **Guardrails framework**: configurable limits on partition size, column count, query scope.
- **Pluggable memtable implementations**: use custom memtable backends.
- **Paxos state purging**: automatic cleanup of Paxos state for LWT.
- **Top partitions**: `nodetool toppartitions` for identifying hot partitions.

```bash
# Top partitions (4.1+)
nodetool toppartitions ecommerce orders 1000
# Shows the most active partitions over the last 1000 ms
# Useful for identifying hot partitions in real time
```

### 12.3 Cassandra 5.0

- **Unified Compaction Strategy (UCS)**: auto-adapting compaction.
- **Storage Attached Indexes (SAI)**: efficient distributed secondary indexes.
- **Accord protocol**: replaces Paxos for LWT with lower latency.
- **Trie-indexed SSTables**: faster lookups, smaller index memory footprint.
- **Java 17 requirement**: all nodes must run Java 17+.
- **Vector search (preview)**: ANN search via SAI.
- **Transactional Cluster Metadata (TCM)**: replaces gossip-based schema dissemination with Raft-based consensus for cluster metadata changes.

```bash
# Check Java version (must be 17+ for Cassandra 5.0)
java -version

# Verify UCS is active
nodetool tablestats ecommerce.orders | grep "compaction"
```

---

## 13. Troubleshooting

### 13.1 Node Fails to Start

**Symptom**: Cassandra process exits immediately after starting.

**Fix**:
```bash
# Check system.log for the error
tail -100 /var/log/cassandra/system.log

# Common causes:
# 1. Port already in use (another Cassandra instance)
lsof -i :9042
lsof -i :7000

# 2. Wrong Java version (5.0 requires Java 17+)
java -version

# 3. Corrupted commitlog
# Move commitlog files and restart:
mv /data/cassandra/commitlog/* /tmp/commitlog_backup/
# WARNING: this may lose unflushed writes

# 4. Insufficient memory
# Check jvm.options or jvm11-server.options for heap settings
grep -E "^-Xm[sx]" /etc/cassandra/jvm11-server.options

# 5. Data directory permissions
ls -la /data/cassandra/
chown -R cassandra:cassandra /data/cassandra/
```

### 13.2 High GC Pauses

**Symptom**: GC pauses > 500 ms; clients see timeouts.

**Fix**:
```bash
# Analyze GC log
grep "GC pause" /var/log/cassandra/gc.log | tail -20

# If using CMS collector, switch to G1GC (default in 4.0+):
# jvm11-server.options:
# -XX:+UseG1GC
# -XX:G1HeapRegionSize=16m
# -XX:MaxGCPauseMillis=500

# Reduce heap if > 16 GB (diminishing returns with G1GC)
# -Xms16G -Xmx16G

# Check for large partitions (cause heap pressure during reads)
nodetool tablestats ecommerce.orders | grep "Compacted partition maximum"

# Check tombstone accumulation (scanned during reads, held in heap)
nodetool tablestats ecommerce.orders | grep "tombstones"
```

### 13.3 Dropped Messages

**Symptom**: `nodetool tpstats` shows dropped messages.

**Fix**:
```bash
nodetool tpstats | grep -v "0$" | grep -v "^$"

# Dropped MUTATION: writes are overloading the node
# Solutions:
# - Reduce write throughput
# - Add more nodes
# - Check compaction backlog (compaction competing for disk I/O)

# Dropped READ: reads are timing out
# Solutions:
# - Check for large partitions or tombstone-heavy tables
# - Increase read_request_timeout (cassandra.yaml)
# - Add more nodes or increase RF
```

### 13.4 SSTable Count Growing Unbounded

**Symptom**: SSTable count per table keeps increasing despite compaction running.

**Fix**:
```bash
# Check if compaction is keeping up
nodetool compactionstats

# If pending tasks are high, increase compaction throughput:
nodetool setcompactionthroughput 128

# If using STCS, large SSTables may not compact because
# min_threshold (default 4) similar-sized SSTables are needed.
# Solution: run major compaction (one-time):
nodetool compact ecommerce orders

# If using LCS, check if disk I/O is a bottleneck.
# LCS has higher write amplification and needs fast disks.
```

### 13.5 Commitlog Full

**Symptom**: writes fail with "commitlog space limit reached."

**Fix**:
```bash
# Check commitlog disk usage
du -sh /data/cassandra/commitlog/

# Flush all memtables (allows commitlog segments to be recycled)
nodetool flush

# Increase commitlog space:
# cassandra.yaml: commitlog_total_space_in_mb: 4096

# Ensure commitlog is on a separate disk from data
# to prevent compaction I/O from competing with commitlog writes.
```

### 13.6 Schema Disagreement

**Symptom**: DDL operations fail; `nodetool describecluster` shows multiple schema versions.

**Fix**:
```bash
nodetool describecluster

# Identify which node(s) have the old schema
# Try restarting the disagreeing node:
nodetool drain && systemctl restart cassandra

# If restart does not help:
nodetool resetlocalschema    # forces re-sync from peers
```

### 13.7 Repair Running Too Long

**Symptom**: repair takes days, impacts production performance.

**Fix**:
```bash
# Use sub-range repair to parallelize:
# Split the token range into N segments and run in parallel (on different nodes)

# Better: use Reaper for automated, throttled repair scheduling
# Set intensity to 0.5 (50% of repair segments run in parallel)

# Increase streaming throughput during repair window:
nodetool setstreamthroughput 400   # MB/s
```

### 13.8 Client Connection Refused

**Symptom**: clients cannot connect to port 9042.

**Fix**:
```bash
# Check if Cassandra is listening
ss -tlnp | grep 9042

# Check rpc_address in cassandra.yaml
# rpc_address: 0.0.0.0  (listen on all interfaces)
# or rpc_address: <specific_ip>

# Check native_transport_port
grep native_transport_port /etc/cassandra/cassandra.yaml

# Check if max client connections is exhausted
nodetool tpstats | grep "Native-Transport"

# Cassandra 4.0+ virtual tables:
# SELECT * FROM system_views.clients;
```

### 13.9 Data Directory Full

**Symptom**: writes fail; compaction stops; node goes into error state.

**Fix**:
```bash
# Check disk usage
df -h /data/cassandra

# Clear old snapshots (they hold hard-links that prevent space reclamation)
nodetool clearsnapshot -t <old_tag>

# Clear all snapshots:
nodetool clearsnapshot --all

# Run cleanup (removes data that belongs to other nodes after scaling)
nodetool cleanup

# If critically full, temporarily increase compaction throughput
# to compact and reclaim tombstoned space faster
nodetool setcompactionthroughput 256
```

### 13.10 Zombie Nodes in Gossip

**Symptom**: `nodetool status` shows nodes that no longer exist.

**Fix**:
```bash
# If the node was properly decommissioned, gossip should clear it.
# If not:

# Wait 72 hours (3x gossip quarantine); often resolves itself.

# If persistent, assassinate the phantom node:
nodetool assassinate <ip_of_zombie>

# Run repair afterward to ensure data integrity:
nodetool repair -full <keyspace>
```

---

## 14. FAQ

### Q1: How often should I run nodetool repair?

Run repair at least once within `gc_grace_seconds` (default 10 days). Recommended: every 7 days. This prevents tombstone-based data resurrection.

### Q2: Can I run nodetool commands remotely?

Yes. Use `-h <host>` and `-p <jmx_port>`:
```bash
nodetool -h 10.0.1.2 -p 7199 status
```
Requires JMX access. In Cassandra 4.0+, prefer virtual tables via CQL for remote monitoring.

### Q3: What is the difference between nodetool drain and nodetool stopdaemon?

`drain` flushes all memtables and stops accepting connections but leaves the process running. `stopdaemon` stops the process. For graceful shutdown: `drain` first, then stop the service.

### Q4: How do I find the largest partitions?

```bash
nodetool tablestats <ks>.<table> | grep "Compacted partition maximum"
# Cassandra 4.1+:
nodetool toppartitions <ks> <table> 5000
```

### Q5: How much disk space does compaction need?

- **STCS**: 50% free space (worst case: temporary 2x data size during major compaction).
- **LCS**: 10% free space (compacts small SSTables incrementally).
- **TWCS**: 50% free space (similar to STCS per time window).
- **UCS**: varies by tuning; plan for 30-50% free.

### Q6: Should I use incremental or full repair?

In Cassandra 4.0+, incremental repair is reliable and recommended for regular use. Full repair is needed after major incidents (node loss, extended outage). Use `--preview` to check divergence before committing.

### Q7: How do I safely change cassandra.yaml settings?

Most settings require a restart. Use rolling restart: change one node, restart, wait for UN, proceed. Some settings can be changed at runtime:
```bash
nodetool setcompactionthroughput 128
nodetool setstreamthroughput 400
nodetool setcachecapacity <key_cache_mb> <row_cache_mb> <counter_cache_mb>
```

### Q8: What JVM garbage collector should I use?

- **Cassandra 3.x**: CMS (default), heap <= 8 GB.
- **Cassandra 4.x**: G1GC (default), heap 8-16 GB.
- **Cassandra 5.0**: G1GC or ZGC (experimental). ZGC offers sub-millisecond pauses but higher CPU overhead.

### Q9: How do I monitor Cassandra without JMX?

Cassandra 4.0+ provides virtual tables in the `system_views` keyspace, queryable via CQL. This is the preferred method for remote monitoring and automation, as it does not require JMX port exposure.

### Q10: How do I automate backup and restore?

Use Medusa (cassandra-medusa) for automated backups to S3, GCS, or Azure Blob. It handles snapshots, schema backup, and restore orchestration. For enterprise, DataStax OpsCenter provides backup scheduling.

### Q11: What is the Cassandra Reaper tool?

Reaper (cassandra-reaper.io) is an automated repair scheduler. It splits repairs into sub-range segments, manages parallelism, retries failures, and provides a web UI. Essential for clusters with > 10 nodes.

### Q12: How do I handle a split-brain scenario?

Cassandra is designed to avoid split-brain via its quorum-based consistency model. If partitions occur, writes succeed in each partition independently and are reconciled (last-write-wins) when the partition heals. Run repair after a network partition heals.

---

*Questo documento fa parte del modulo 07 "NoSQL Cassandra" della Data Encyclopedia.*
