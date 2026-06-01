# Redis Clustering e High Availability

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
1. Replication
2. Sentinel
3. Cluster Mode
4. Data Partitioning
5. Failover
6. Cluster Administration
7. Monitoring and Observability
8. Network Topology and Architecture
9. Performance Tuning for Clusters
10. Security in Clustered Deployments
11. Migration Strategies
12. Anti-Patterns
13. Troubleshooting
14. FAQ

---

## 1. Replication

### 1.1 Replication Architecture

Redis uses asynchronous replication by default with a single-leader model. One master accepts writes while replicas maintain copies of the data. Replication is non-blocking on the master side: while a replica performs initial synchronization, the master continues serving queries.

The replication process works in two phases:
1. **Full synchronization (FULLRESYNC)**: The master creates an RDB snapshot, buffers new write commands, sends the snapshot to the replica, then sends the buffered commands.
2. **Partial resynchronization**: After initial sync, the master streams write commands to the replica via the replication backlog. If the connection drops briefly, the replica can request only the missed portion (PSYNC).

```
+----------+       async replication       +----------+
|  Master  | ───────────────────────────►  | Replica1 |
|  R/W     |                               | R only   |
+----------+                               +----------+
      │                                    +----------+
      └────────────────────────────────►   | Replica2 |
                                           | R only   |
                                           +----------+
```

### 1.2 Master-Replica Setup

```bash
# Method 1: Command line flag
redis-server --replicaof 10.0.1.10 6379

# Method 2: redis.conf
replicaof 10.0.1.10 6379

# Method 3: Runtime (hot configuration)
redis-cli REPLICAOF 10.0.1.10 6379

# Promote replica to master (break replication)
redis-cli REPLICAOF NO ONE

# Check replication status
redis-cli INFO replication
redis-cli ROLE
```

### 1.3 Replication Configuration Deep Dive

```bash
# redis.conf — master side

# Replication backlog size: determines how much data the master
# retains for partial resync after a replica disconnects.
# Larger values tolerate longer disconnects at the cost of memory.
repl-backlog-size 64mb

# Time in seconds before the backlog is freed when no replicas are connected.
# 0 = never free it.
repl-backlog-ttl 3600

# Minimum number of replicas that must be connected and have a lag
# of less than min-replicas-max-lag seconds for the master to accept writes.
# This provides a weak form of synchronous replication guarantee.
min-replicas-to-write 1
min-replicas-max-lag 10

# Disk-based vs diskless replication
# disk: master forks, writes RDB to disk, then sends file
# diskless: master forks, streams RDB directly to replica socket (Redis 7+ default)
repl-diskless-sync yes

# How long to wait for multiple replicas to connect before starting
# a diskless sync (so all replicas can receive the same stream)
repl-diskless-sync-delay 5

# Diskless loading on replica side (Redis 7+)
# disabled: save to disk first, then load (safer)
# on-empty-db: load directly into memory only if DB is empty
# swapdb: load into side DB, then swap atomically
repl-diskless-load on-empty-db
```

```bash
# redis.conf — replica side

# Allow replica to serve stale data while syncing
# yes = serve possibly outdated data during sync
# no = return error LOADING for all commands during sync
replica-serve-stale-data yes

# Make replica read-only (strongly recommended in production)
replica-read-only yes

# Replicas can replicate from other replicas (chained replication)
# Reduces master load when you have many replicas
# Master -> Replica1 -> Replica2 -> Replica3
```

### 1.4 Wait for Synchronous Replication

```bash
# WAIT: block until N replicas acknowledge the write
# Returns the number of replicas that acknowledged within timeout

# Wait for at least 2 replicas to acknowledge, timeout 500ms
redis-cli WAIT 2 500

# Wait for at least 1 replica, no timeout (blocking)
redis-cli WAIT 1 0
```

The WAIT command provides a way to achieve synchronous replication guarantees for critical writes. It does not guarantee the write is on disk at the replica — only that it was received.

### 1.5 Replication and Persistence Interaction

The interplay between replication and persistence is critical for durability:

| Scenario | Master Persistence | Replica Persistence | Durability |
|----------|-------------------|---------------------|------------|
| Cache only | Off | Off | None (acceptable for pure cache) |
| Standard HA | RDB+AOF | RDB | Good |
| Maximum durability | RDB+AOF | RDB+AOF | High |
| Dangerous | Off | RDB+AOF | **Data loss on master restart** |

**Critical warning**: If the master has persistence disabled and restarts, it comes up with an empty dataset and replicates that empty dataset to all replicas, destroying their data. Always enable persistence on the master or ensure the master never auto-restarts.

---

## 2. Sentinel

### 2.1 Sentinel Architecture

Redis Sentinel provides high availability through automatic failover. It is a distributed system of Sentinel processes that:
1. **Monitor** master and replica instances for health
2. **Notify** administrators or other systems via API about state changes
3. **Automatic failover** promotes a replica to master when the master fails
4. **Configuration provider** clients connect to Sentinel to discover the current master

```
+----------+     +----------+     +----------+
| Sentinel |     | Sentinel |     | Sentinel |
|  26379   |     |  26379   |     |  26379   |
+----+-----+     +----+-----+     +----+-----+
     │                │                │
     │    monitoring   │                │
     ▼                ▼                ▼
+----------+     +----------+     +----------+
|  Master  |     | Replica1 |     | Replica2 |
|  6379    |     |  6379    |     |  6379    |
+----------+     +----------+     +----------+
```

Deploy at least 3 Sentinel instances across different availability zones or physical machines. The quorum (minimum Sentinels agreeing on a failure) is typically set to `ceil(N/2)`. For 3 Sentinels, quorum = 2.

### 2.2 Sentinel Configuration

```bash
# /etc/redis/sentinel.conf

# Sentinel port
port 26379

# Sentinel announce IP (for NAT/Docker environments)
sentinel announce-ip 10.0.1.50
sentinel announce-port 26379

# Monitor the master named "mymaster" at 10.0.1.10:6379
# Quorum = 2 (need 2 Sentinels to agree on failure)
sentinel monitor mymaster 10.0.1.10 6379 2

# Time in ms before a master is considered subjectively down (SDOWN)
sentinel down-after-milliseconds mymaster 5000

# How many replicas can be reconfigured simultaneously during failover
sentinel parallel-syncs mymaster 1

# Maximum time in ms for the entire failover process
sentinel failover-timeout mymaster 60000

# Authentication for monitored instances
sentinel auth-pass mymaster your_master_password

# Authentication for Sentinel itself (Redis 6.2+)
requirepass sentinel_password

# ACL for Sentinel (Redis 7+)
sentinel auth-user mymaster sentinel_user

# Notification script — called on any state change
sentinel notification-script mymaster /opt/redis/notify.sh

# Client reconfiguration script — called when master address changes
sentinel client-reconfig-script mymaster /opt/redis/reconfig.sh

# Deny potentially dangerous scripts in production
sentinel deny-scripts-reconfig yes

# Resolve hostnames (Redis 6.2+)
sentinel resolve-hostnames yes
SENTINEL_RESOLVE_HOSTNAMES yes
```

### 2.3 Starting Sentinel

```bash
# Method 1: dedicated binary
redis-sentinel /etc/redis/sentinel.conf

# Method 2: redis-server with --sentinel flag
redis-server /etc/redis/sentinel.conf --sentinel

# Method 3: systemd
systemctl start redis-sentinel
```

### 2.4 Sentinel Commands

```bash
# Connect to Sentinel
redis-cli -p 26379

# Get the current master address
SENTINEL get-master-addr-by-name mymaster

# List all monitored masters
SENTINEL masters

# List replicas for a master
SENTINEL replicas mymaster

# List other Sentinel instances
SENTINEL sentinels mymaster

# Check if quorum is reachable
SENTINEL ckquorum mymaster

# Force a failover (manual trigger)
SENTINEL failover mymaster

# Reset a master (clear state, re-discover replicas)
SENTINEL reset mymaster

# Dynamically change configuration
SENTINEL SET mymaster down-after-milliseconds 10000
SENTINEL SET mymaster failover-timeout 120000

# Simulate a failure for testing
SENTINEL simulate-failure crash-after-election
SENTINEL simulate-failure crash-after-promotion
```

### 2.5 Client Integration

```python
# Python — redis-py with Sentinel support
from redis.sentinel import Sentinel

sentinel = Sentinel(
    [('sentinel1', 26379), ('sentinel2', 26379), ('sentinel3', 26379)],
    socket_timeout=0.5,
    password='sentinel_password'
)

# Get master connection (auto-discovers current master)
master = sentinel.master_for(
    'mymaster',
    socket_timeout=0.5,
    password='master_password'
)

# Get replica connection (load-balanced across healthy replicas)
replica = sentinel.slave_for(
    'mymaster',
    socket_timeout=0.5,
    password='master_password'
)

# Use like normal Redis clients
master.set('key', 'value')
value = replica.get('key')
```

```javascript
// Node.js — ioredis with Sentinel
const Redis = require('ioredis');

const redis = new Redis({
  sentinels: [
    { host: 'sentinel1', port: 26379 },
    { host: 'sentinel2', port: 26379 },
    { host: 'sentinel3', port: 26379 },
  ],
  name: 'mymaster',
  sentinelPassword: 'sentinel_password',
  password: 'master_password',
  role: 'master',  // or 'slave' for read replicas
});
```

### 2.6 Sentinel Failover Sequence

The failover process follows a strict protocol:

1. **SDOWN (Subjective Down)**: A single Sentinel considers the master down after `down-after-milliseconds` of failed PING responses.
2. **ODOWN (Objective Down)**: The Sentinel asks other Sentinels — if at least `quorum` Sentinels agree, the master is objectively down.
3. **Leader Election**: Sentinels elect a leader using the Raft algorithm to coordinate failover.
4. **Replica Selection**: The leader picks the best replica based on:
   - Priority (`replica-priority` — lower is preferred, 0 means never promote)
   - Replication offset (most data replicated)
   - Run ID (lexicographic tiebreaker)
5. **Promotion**: The selected replica is sent `REPLICAOF NO ONE`.
6. **Reconfiguration**: Other replicas are told to replicate from the new master.
7. **Client notification**: Sentinel publishes the new master address via Pub/Sub.

---

## 3. Cluster Mode

### 3.1 Cluster Architecture

Redis Cluster provides automatic data sharding across multiple master nodes. Each master owns a subset of the 16384 hash slots and can have one or more replicas for HA.

```
                        Hash Slots: 0-16383

+------------------+   +------------------+   +------------------+
| Master 1 (M1)   |   | Master 2 (M2)   |   | Master 3 (M3)   |
| Slots: 0-5460   |   | Slots: 5461-10922|  | Slots: 10923-16383|
| Port: 7001      |   | Port: 7002      |   | Port: 7003      |
+--------+---------+   +--------+---------+   +--------+---------+
         │                      │                      │
    +----+----+            +----+----+            +----+----+
    |Replica1a|            |Replica2a|            |Replica3a|
    |Port:7004|            |Port:7005|            |Port:7006|
    +---------+            +---------+            +---------+
```

Key cluster properties:
- Data automatically partitioned across nodes
- Majority of masters must be reachable for cluster to stay available
- Cluster uses a gossip protocol on the cluster bus (port + 10000)
- Every node knows every other node and the slot mapping

### 3.2 Creating a Cluster

```bash
# Create a 3-master + 3-replica cluster
redis-cli --cluster create \
  10.0.1.1:7001 10.0.1.2:7002 10.0.1.3:7003 \
  10.0.1.4:7004 10.0.1.5:7005 10.0.1.6:7006 \
  --cluster-replicas 1

# Verify cluster state
redis-cli -c -h 10.0.1.1 -p 7001 CLUSTER INFO
redis-cli -c -h 10.0.1.1 -p 7001 CLUSTER NODES

# Connect in cluster mode (-c flag enables auto-redirect)
redis-cli -c -h 10.0.1.1 -p 7001
```

### 3.3 Cluster Configuration

```bash
# redis.conf for each cluster node

# Enable cluster mode
cluster-enabled yes

# Cluster config file (auto-generated, do not edit manually)
cluster-config-file nodes-7001.conf

# Node timeout in milliseconds — how long before a node is considered failing
cluster-node-timeout 15000

# Cluster bus port (default: port + 10000)
cluster-port 17001

# Require full slot coverage for the cluster to accept queries
# yes = cluster goes down if any slot is uncovered
# no = cluster serves queries for covered slots even if some slots are down
cluster-require-full-coverage yes

# Allow reads from replicas (experimental in some versions)
cluster-allow-reads-when-down no

# Enable pubsub across cluster nodes (Redis 7+)
cluster-allow-pubsubshard-when-down yes

# Cluster link TLS
# tls-cluster yes

# Announce IP for NAT/Docker environments
cluster-announce-ip 10.0.1.1
cluster-announce-port 7001
cluster-announce-bus-port 17001
```

### 3.4 Cluster Commands Reference

```bash
# Node information
CLUSTER MYID                  # Current node's ID
CLUSTER NODES                 # All nodes, slots, roles, state
CLUSTER INFO                  # Cluster state summary
CLUSTER SLOTS                 # Slot ranges and node assignments

# Slot management
CLUSTER KEYSLOT mykey          # Which slot a key maps to
CLUSTER COUNTKEYSINSLOT 5000   # Keys in slot 5000
CLUSTER GETKEYSINSLOT 5000 10  # Get 10 keys from slot 5000

# Node management
CLUSTER MEET 10.0.1.4 7004    # Introduce a new node to the cluster
CLUSTER FORGET <node-id>      # Remove a node from the cluster
CLUSTER REPLICATE <node-id>   # Make current node a replica of node-id

# Slot assignment
CLUSTER ADDSLOTS 0 1 2 3      # Assign slots to current node
CLUSTER DELSLOTS 0 1 2        # Remove slot assignments
CLUSTER SETSLOT 5000 MIGRATING <destination-id>  # Begin migration
CLUSTER SETSLOT 5000 IMPORTING <source-id>       # Accept migration
CLUSTER SETSLOT 5000 STABLE                      # Cancel migration
CLUSTER SETSLOT 5000 NODE <node-id>              # Finalize migration

# Failover
CLUSTER FAILOVER              # Manual failover (replica takes over)
CLUSTER FAILOVER FORCE        # Force failover even if master unreachable
CLUSTER FAILOVER TAKEOVER     # Force without master agreement

# Reset
CLUSTER RESET SOFT            # Reset node, keep data
CLUSTER RESET HARD            # Reset node, flush data
```

---

## 4. Data Partitioning

### 4.1 Hash Slot Algorithm

Redis Cluster uses CRC16 hashing modulo 16384 to determine the slot for each key:

```
SLOT = CRC16(key) mod 16384
```

```bash
# Check slot for any key
CLUSTER KEYSLOT user:1000      # Returns e.g. 12539
CLUSTER KEYSLOT user:2000      # Returns e.g. 3359
CLUSTER KEYSLOT session:abc    # Returns e.g. 7654
```

### 4.2 Hash Tags

Hash tags force related keys to the same slot by hashing only the substring between `{` and `}`:

```bash
# These keys all hash on "user:1000" — same slot
SET {user:1000}:profile "data"
SET {user:1000}:session "data"
SET {user:1000}:cart "data"

# Multi-key commands work only when keys are in the same slot
MGET {user:1000}:profile {user:1000}:session

# Verify
CLUSTER KEYSLOT {user:1000}:profile   # same as
CLUSTER KEYSLOT {user:1000}:session   # same slot
```

Hash tags enable multi-key operations and Lua scripts that touch multiple keys — these only work within a single slot.

### 4.3 Slot Migration (Resharding)

```bash
# Using redis-cli (recommended for production)
redis-cli --cluster reshard 10.0.1.1:7001

# Automated resharding
redis-cli --cluster reshard 10.0.1.1:7001 \
  --cluster-from <source-node-id> \
  --cluster-to <destination-node-id> \
  --cluster-slots 1000 \
  --cluster-yes

# Rebalance slots evenly across all masters
redis-cli --cluster rebalance 10.0.1.1:7001

# Check cluster for configuration errors
redis-cli --cluster check 10.0.1.1:7001

# Fix cluster issues automatically
redis-cli --cluster fix 10.0.1.1:7001
```

### 4.4 MOVED and ASK Redirections

When a client sends a command to a node that does not own the target slot, the node returns a redirection:

```
# MOVED — permanent redirect (slot belongs to another node)
> GET user:1000
(error) MOVED 12539 10.0.1.2:7002

# ASK — temporary redirect (slot is being migrated)
> GET user:1000
(error) ASK 12539 10.0.1.3:7003
# Client must send ASKING before the actual command to the new node
```

Smart clients (like ioredis, redis-py-cluster) handle redirections automatically and cache the slot map.

---

## 5. Failover

### 5.1 Automatic Failover in Cluster

When a master is unreachable:
1. Other masters mark it as `PFAIL` (possible failure) after `cluster-node-timeout`.
2. When a majority of masters agree, the node is marked `FAIL`.
3. One of the failing master's replicas initiates an election.
4. The replica with the most data (highest replication offset) wins the election.
5. The winning replica promotes itself and claims the slots.
6. Other nodes update their configuration.

```bash
# Check cluster health
CLUSTER INFO

# Example healthy output
cluster_state:ok
cluster_slots_assigned:16384
cluster_slots_ok:16384
cluster_slots_pfail:0
cluster_slots_fail:0
cluster_known_nodes:6
cluster_size:3

# Example degraded output
cluster_state:fail
cluster_slots_fail:5461
```

### 5.2 Manual Failover

```bash
# Graceful failover — run on the REPLICA you want to promote
# The replica negotiates with the master for a safe handover
redis-cli -h replica-ip -p 7004 CLUSTER FAILOVER

# Forced failover — when master is down and cannot negotiate
redis-cli -h replica-ip -p 7004 CLUSTER FAILOVER FORCE

# Takeover — when quorum cannot be reached (use with extreme caution)
redis-cli -h replica-ip -p 7004 CLUSTER FAILOVER TAKEOVER
```

### 5.3 Replica Migration

Redis Cluster supports automatic replica migration: if a master has multiple replicas and another master has zero replicas, one replica is automatically migrated to protect the under-replicated master.

```bash
# Configure the minimum number of replicas a master needs
# before its replicas can migrate to orphaned masters
cluster-migration-barrier 1
```

---

## 6. Cluster Administration

### 6.1 Adding Nodes

```bash
# Add a new master node to the cluster
redis-cli --cluster add-node 10.0.1.7:7007 10.0.1.1:7001

# The new node starts with zero slots — reshard to assign slots
redis-cli --cluster reshard 10.0.1.1:7001

# Add a new replica node
redis-cli --cluster add-node 10.0.1.8:7008 10.0.1.1:7001 \
  --cluster-slave --cluster-master-id <master-node-id>
```

### 6.2 Removing Nodes

```bash
# First, reshard all slots away from the node being removed
redis-cli --cluster reshard 10.0.1.1:7001 \
  --cluster-from <removing-node-id> \
  --cluster-to <another-master-id> \
  --cluster-slots 5461 \
  --cluster-yes

# Then remove the empty node
redis-cli --cluster del-node 10.0.1.1:7001 <removing-node-id>
```

### 6.3 Scaling Operations

```bash
# Scale out: add nodes + reshard
# 1. Add new master
redis-cli --cluster add-node new-host:7009 10.0.1.1:7001

# 2. Add replica for the new master
redis-cli --cluster add-node new-host:7010 10.0.1.1:7001 \
  --cluster-slave --cluster-master-id <new-master-id>

# 3. Rebalance slots
redis-cli --cluster rebalance 10.0.1.1:7001 --cluster-use-empty-masters

# Scale down: drain + remove
# 1. Move all slots from the node
# 2. Wait for replication to catch up
# 3. Remove replica first, then master
```

### 6.4 Rolling Upgrades

```bash
# Upgrade cluster nodes one at a time with zero downtime
# Order: upgrade replicas first, then masters (using failover)

# Step 1: Upgrade a replica
systemctl stop redis@7004
# install new version
systemctl start redis@7004
# Verify it rejoins the cluster
redis-cli -h 10.0.1.4 -p 7004 CLUSTER NODES

# Step 2: For masters, first failover, then upgrade
redis-cli -h 10.0.1.4 -p 7004 CLUSTER FAILOVER  # promote replica
# Now 7001 is a replica — safe to upgrade
systemctl stop redis@7001
# install new version
systemctl start redis@7001

# Step 3: Optionally fail back
redis-cli -h 10.0.1.1 -p 7001 CLUSTER FAILOVER
```

---

## 7. Monitoring and Observability

### 7.1 Key Metrics to Monitor

```bash
# Cluster-level metrics
CLUSTER INFO
# cluster_state: ok|fail
# cluster_slots_assigned: should be 16384
# cluster_slots_ok: should be 16384
# cluster_slots_pfail: should be 0
# cluster_slots_fail: should be 0
# cluster_known_nodes: total nodes
# cluster_size: number of masters
# cluster_current_epoch: configuration epoch
# cluster_stats_messages_sent: gossip messages sent
# cluster_stats_messages_received: gossip messages received

# Per-node metrics
INFO server          # version, uptime, mode
INFO clients         # connected clients, blocked clients
INFO memory          # used_memory, used_memory_rss, fragmentation_ratio
INFO stats           # keyspace hits/misses, expired/evicted keys
INFO replication     # role, connected_slaves, repl_backlog_size
INFO cpu             # used_cpu_sys, used_cpu_user
INFO keyspace        # keys per DB, expires, avg_ttl
INFO latencystats    # per-command latency histograms (Redis 7+)

# Slow log
SLOWLOG GET 25       # last 25 slow queries
SLOWLOG LEN          # number of entries in slow log
SLOWLOG RESET        # clear slow log
CONFIG SET slowlog-log-slower-than 10000  # threshold in microseconds
CONFIG SET slowlog-max-len 128            # max entries retained
```

### 7.2 Latency Monitoring

```bash
# Built-in latency monitor
CONFIG SET latency-monitor-threshold 100  # log events over 100ms

# View latency events
LATENCY LATEST              # latest samples per event type
LATENCY HISTORY event_name  # full history for an event
LATENCY RESET               # clear history
LATENCY GRAPH event_name    # ASCII graph of latency

# Measure intrinsic latency (network + system)
redis-cli --intrinsic-latency 10  # 10 second sample
redis-cli --latency                # continuous ping
redis-cli --latency-history        # periodic latency measurement
redis-cli --latency-dist           # latency distribution
```

### 7.3 Prometheus + Grafana Setup

```yaml
# docker-compose.yml snippet for redis_exporter
redis-exporter:
  image: oliver006/redis_exporter:latest
  environment:
    REDIS_ADDR: "redis://10.0.1.1:7001,redis://10.0.1.2:7002,redis://10.0.1.3:7003"
    REDIS_PASSWORD: "your_password"
  ports:
    - "9121:9121"
```

Key Prometheus alerts:

```yaml
# prometheus/alerts.yml
groups:
  - name: redis-cluster
    rules:
      - alert: RedisClusterDown
        expr: redis_cluster_state == 0
        for: 30s
        labels:
          severity: critical

      - alert: RedisClusterSlotsFailing
        expr: redis_cluster_slots_fail > 0
        for: 1m
        labels:
          severity: critical

      - alert: RedisReplicationBroken
        expr: redis_connected_slaves < 1
        for: 5m
        labels:
          severity: warning

      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning

      - alert: RedisHighLatency
        expr: redis_commands_duration_seconds_total / redis_commands_processed_total > 0.01
        for: 5m
        labels:
          severity: warning
```

---

## 8. Network Topology and Architecture

### 8.1 Production Deployment Topologies

**Three-AZ deployment** (recommended minimum):
```
AZ-a                    AZ-b                    AZ-c
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│ Master1      │       │ Master2      │       │ Master3      │
│ Replica2a    │       │ Replica3a    │       │ Replica1a    │
│ Sentinel1    │       │ Sentinel2    │       │ Sentinel3    │
└──────────────┘       └──────────────┘       └──────────────┘
```

Each master's replica is in a different AZ from the master — survives a full AZ failure.

**Cluster bus port requirements**:
```bash
# Every cluster node needs TWO ports open:
# Data port (e.g., 7001) — client connections
# Bus port (data port + 10000, e.g., 17001) — node-to-node gossip

# Firewall rules example (iptables)
iptables -A INPUT -p tcp --dport 7001 -s 10.0.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 17001 -s 10.0.0.0/16 -j ACCEPT
```

### 8.2 Docker and Kubernetes Considerations

```bash
# Docker: use host networking or announce the external IP
cluster-announce-ip 10.0.1.1
cluster-announce-port 7001
cluster-announce-bus-port 17001

# Kubernetes: use a StatefulSet with stable network identities
# Each pod needs a predictable hostname and IP
# Use anti-affinity rules to spread across nodes/zones
```

```yaml
# Kubernetes anti-affinity example
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: redis-cluster
        topologyKey: kubernetes.io/hostname
```

---

## 9. Performance Tuning for Clusters

### 9.1 Client-Side Optimization

```python
# Use cluster-aware clients that cache the slot map
from redis.cluster import RedisCluster

rc = RedisCluster(
    host='10.0.1.1',
    port=7001,
    password='password',
    # Read from replicas to offload masters
    read_from_replicas=True,
    # Retry on MOVED/ASK redirections
    retry_on_timeout=True,
    # Connection pool per node
    max_connections_per_node=50,
)
```

### 9.2 Pipeline in Cluster Mode

Pipelining in cluster mode requires slot-aware batching: commands must be grouped by the node that owns their slot.

```python
# redis-py-cluster handles this automatically
pipe = rc.pipeline()
for i in range(1000):
    pipe.set(f"key:{i}", f"value:{i}")
results = pipe.execute()
# Internally groups commands by node and sends parallel pipelines
```

### 9.3 Cross-Slot Operations

```bash
# Multi-key commands require all keys in the same slot
# Use hash tags to co-locate related keys

# Works: same hash tag
MGET {user:1}:name {user:1}:email

# Fails: different slots
MGET user:1:name user:2:name
# (error) CROSSSLOT Keys in request don't hash to the same slot
```

---

## 10. Security in Clustered Deployments

### 10.1 Authentication

```bash
# Set password for cluster nodes (must be same on all nodes)
requirepass your_cluster_password
masterauth your_cluster_password

# ACL for cluster (Redis 7+)
# Define users in aclfile, replicate across all nodes
aclfile /etc/redis/users.acl

# Cluster bus authentication (Redis 7+)
cluster-preferred-endpoint-type ip
```

### 10.2 TLS for Cluster

```bash
# Enable TLS on cluster data port
tls-port 7001
port 0

# Enable TLS on cluster bus
tls-cluster yes

# Certificate configuration
tls-cert-file /etc/redis/tls/redis.crt
tls-key-file /etc/redis/tls/redis.key
tls-ca-cert-file /etc/redis/tls/ca.crt
tls-auth-clients optional

# Client connection with TLS
redis-cli -c --tls --cert client.crt --key client.key --cacert ca.crt \
  -h 10.0.1.1 -p 7001
```

---

## 11. Migration Strategies

### 11.1 Standalone to Cluster

```bash
# Step 1: Set up the cluster with empty nodes
# Step 2: Use redis-cli --cluster import to migrate data

redis-cli --cluster import 10.0.1.1:7001 \
  --cluster-from 10.0.0.1:6379 \
  --cluster-copy \
  --cluster-replace

# --cluster-copy: do not delete keys from source
# --cluster-replace: overwrite existing keys in target
```

### 11.2 Sentinel to Cluster

Migration from Sentinel to Cluster requires application changes (cluster-aware client, hash tags for multi-key operations). Plan a phased approach:
1. Audit all multi-key operations and add hash tags
2. Set up the cluster alongside the Sentinel deployment
3. Dual-write during transition
4. Switch reads to cluster
5. Switch writes to cluster
6. Decommission Sentinel

---

## 12. Anti-Patterns

1. **No replicas**: Running a cluster without replicas for masters. Any master failure takes slots offline.
2. **All nodes in one AZ**: A single AZ failure takes down the entire cluster.
3. **Ignoring cluster-node-timeout**: Setting it too low causes flapping; too high delays failover.
4. **Hardcoding node addresses in clients**: Use service discovery or Sentinel for Sentinel setups, cluster-aware clients for Cluster mode.
5. **Using KEYS command in production**: Use SCAN instead — KEYS blocks the node.
6. **Cross-slot Lua scripts**: Writing Lua that touches keys in different slots — fails at runtime.
7. **Skipping cluster-require-full-coverage**: Setting to `no` without understanding that uncovered slots return errors.
8. **Same-machine master and its replica**: If the machine dies, both are lost.
9. **Massive key migrations during peak**: Resharding generates load — schedule during off-peak.
10. **Not testing failover**: Never running `CLUSTER FAILOVER` in staging to validate the process works.

---

## 13. Troubleshooting

### 13.1 Cluster State is FAIL

```bash
# Diagnosis
CLUSTER INFO     # check cluster_state, cluster_slots_fail
CLUSTER NODES    # look for nodes marked "fail" or "noaddr"

# Fix: if a master is permanently lost and has a replica
# The replica should auto-promote. If not:
redis-cli -h replica-ip -p 7004 CLUSTER FAILOVER FORCE

# Fix: if a master is lost with no replica
# Add a new node and assign the orphaned slots manually
redis-cli --cluster add-node new-host:7009 10.0.1.1:7001
redis-cli --cluster fix 10.0.1.1:7001
```

### 13.2 CROSSSLOT Errors

```bash
# Cause: multi-key command with keys in different slots
# Fix: use hash tags
SET {order:123}:items "..."
SET {order:123}:total "..."
# Now MGET {order:123}:items {order:123}:total works
```

### 13.3 Slot Coverage Incomplete

```bash
# Check which slots are uncovered
redis-cli --cluster check 10.0.1.1:7001

# Auto-fix
redis-cli --cluster fix 10.0.1.1:7001
```

### 13.4 Split-Brain

```bash
# Happens when network partition isolates nodes
# Diagnosis: different nodes report different masters for the same slots

# Prevention:
# - Use cluster-node-timeout appropriately
# - Deploy across odd number of AZs
# - Use min-replicas-to-write on standalone setups
```

### 13.5 Replication Lag

```bash
# Check replica lag
INFO replication
# master_repl_offset: 123456789
# slave0:ip=10.0.1.4,port=7004,...,lag=0

# If lag is growing:
# 1. Check network between master and replica
# 2. Check if replica is overloaded (slow disk, CPU)
# 3. Increase repl-backlog-size if replicas disconnect and need full resync
```

### 13.6 Node Keeps Failing to Join Cluster

```bash
# Check cluster-config-file for stale state
cat /var/lib/redis/nodes-7001.conf

# Reset the node
redis-cli -h problem-node -p 7001 CLUSTER RESET HARD

# Re-meet the cluster
redis-cli -h 10.0.1.1 -p 7001 CLUSTER MEET problem-node 7001
```

### 13.7 High Memory Fragmentation

```bash
INFO memory
# mem_fragmentation_ratio: should be close to 1.0
# > 1.5: significant fragmentation

# Fix: enable active defragmentation (Redis 4+)
CONFIG SET activedefrag yes
CONFIG SET active-defrag-enabled yes
CONFIG SET active-defrag-threshold-lower 10
CONFIG SET active-defrag-threshold-upper 100
```

### 13.8 Gossip Bandwidth Too High

```bash
# Large clusters (100+ nodes) generate significant gossip traffic
# Each node pings cluster-node-timeout/10 random nodes per second

# Reduce by increasing cluster-node-timeout (trade-off: slower failure detection)
CONFIG SET cluster-node-timeout 30000
```

### 13.9 Sentinel Not Detecting Failure

```bash
# Check Sentinel connectivity
redis-cli -p 26379 SENTINEL ckquorum mymaster

# Check if down-after-milliseconds is too high
SENTINEL SET mymaster down-after-milliseconds 5000

# Verify Sentinel can reach the master
redis-cli -p 26379 SENTINEL masters
# Check the "is_master_down" and "last_ping_reply" fields
```

### 13.10 Client Receives Stale Data After Failover

```bash
# Cause: client cached the old master address
# Fix: use Sentinel-aware or cluster-aware clients that auto-discover

# For Sentinel: client subscribes to +switch-master channel
# For Cluster: client refreshes slot map on MOVED errors

# Verify the client library handles reconnection correctly
```

### 13.11 Full Resync Loop

```bash
# Replica repeatedly performs full sync instead of partial
# Cause: repl-backlog-size too small for the write rate

# Check
INFO replication
# If master_repl_offset - slave_repl_offset > repl-backlog-size → full resync

# Fix
CONFIG SET repl-backlog-size 256mb
```

### 13.12 Cluster Fails After Master Restart with Empty Dataset

```bash
# Cause: master had persistence disabled, restarted with empty data,
# replicas synced empty data

# Prevention: ALWAYS enable persistence on masters
# Or: do not auto-restart masters, handle manually

# Recovery: restore from replica or backup
# 1. Stop the empty master
# 2. Manually promote a replica
# 3. Restore data from backup if no replica exists
```

---

## 14. FAQ

**Q1: What is the minimum number of nodes for Redis Cluster?**
A: Redis Cluster requires at least 3 master nodes. For production HA, you want 3 masters + 3 replicas = 6 nodes total.

**Q2: Can I mix Sentinel and Cluster?**
A: No. Sentinel manages standalone Redis with replication. Cluster handles its own failover internally. Choose one or the other.

**Q3: What happens when a master fails and it has no replicas?**
A: The slots owned by that master become unavailable. If `cluster-require-full-coverage` is yes (default), the entire cluster stops accepting writes. If no, only queries for those slots fail.

**Q4: How do I handle multi-key operations in Cluster?**
A: Use hash tags: `{user:1}:profile`, `{user:1}:settings`. Both hash on `user:1` and land in the same slot.

**Q5: Does Redis Cluster support SELECT (multiple databases)?**
A: No. Redis Cluster only supports database 0. The SELECT command is disabled.

**Q6: How does Redis Cluster handle client connections during resharding?**
A: Clients may receive ASK redirections during migration. Smart clients handle this transparently. There is no downtime — keys are accessible throughout the migration.

**Q7: What is the maximum number of nodes in a Redis Cluster?**
A: The recommended maximum is around 1000 nodes. Beyond that, gossip protocol overhead becomes significant and cluster convergence slows.

**Q8: How do I back up a Redis Cluster?**
A: Run BGSAVE on each master node individually. Restore requires setting up a new cluster and importing data from each node's RDB.

**Q9: Can replicas serve reads in Cluster mode?**
A: Yes, by using the `READONLY` command on the replica connection. Some client libraries support `read_from_replicas` configuration.

**Q10: What is the difference between CLUSTER FAILOVER and CLUSTER FAILOVER FORCE?**
A: Normal failover coordinates with the master for a safe handover (no data loss). FORCE skips the coordination — used when the master is unreachable. TAKEOVER additionally skips the election (use only as last resort).

**Q11: How do I estimate the right repl-backlog-size?**
A: Multiply your write throughput (bytes/second) by the maximum expected disconnect duration. If you write 10MB/s and disconnects can last 60s, set backlog to at least 600MB.

**Q12: Does Redis Cluster support cross-datacenter replication?**
A: Not natively. For cross-DC, use active-passive setups with standalone replication or third-party tools like Redis Enterprise's Active-Active geo-replication.

---

*Questo documento fa parte del modulo 06 "NoSQL Redis" della Data Encyclopedia.*
