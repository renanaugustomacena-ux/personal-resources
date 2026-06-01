# Cassandra: Multi-Datacenter

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
1. Multi-DC Architecture
2. NetworkTopologyStrategy
3. Cross-DC Replication
4. Consistency Across DC
5. Snitch Configuration
6. Cross-DC Write Path
7. Cross-DC Read Path
8. Adding a New Datacenter
9. Removing a Datacenter
10. Multi-DC Repair Strategies
11. Latency and WAN Optimization
12. Multi-DC Security
13. Monitoring Multi-DC Clusters
14. Cassandra 4.x/5.x Multi-DC Features
15. Troubleshooting
16. FAQ

---

## 1. Multi-DC Architecture

Cassandra's multi-datacenter architecture provides geographic redundancy, disaster recovery, and workload isolation. Every node in every datacenter is a peer; there is no primary/secondary hierarchy. Each datacenter can serve reads and writes independently while data replicates asynchronously across WAN links.

### 1.1 Architecture Principles

- **Symmetric topology**: every DC holds a full copy of the data (at the configured RF). No DC is "primary."
- **Rack-aware placement**: replicas are distributed across racks within a DC to survive rack-level failures.
- **Local coordinators**: a client connects to a coordinator in its local DC; cross-DC hops happen only for replication, not for coordination.
- **Gossip protocol**: nodes in all DCs share cluster metadata via the gossip protocol, converging within seconds.

### 1.2 Seed Nodes

```yaml
# cassandra.yaml - seed list must include at least one node from each DC
# Seeds bootstrap the gossip ring; they are NOT special at runtime
seed_provider:
  - class_name: org.apache.cassandra.locator.SimpleSeedProvider
    parameters:
      - seeds: "10.0.1.1,10.0.1.2,10.0.2.1,10.0.2.2,10.0.3.1"
```

**Seed best practices:**
- Two or three seeds per DC (never every node).
- Seeds should be stable, long-lived nodes.
- If a seed goes down, remaining seeds keep gossip alive; replace promptly.
- Never make all nodes seeds -- it slows gossip convergence.

### 1.3 Datacenter and Rack Assignment

```yaml
# cassandra-rackdc.properties  (used by GossipingPropertyFileSnitch)
dc=us-east-1
rack=rack1

# These properties define the node's logical DC and rack.
# Changing them on a live node requires a full data move.
```

```bash
# Verify DC/rack assignment across the cluster
nodetool status

# Example output:
# Datacenter: us-east-1
# ====================
# Status=Up/Down  State=Normal/Leaving/Joining/Moving
# UN  10.0.1.1  256.0 KiB  256  45.2%  abc12345  rack1
# UN  10.0.1.2  256.0 KiB  256  54.8%  def67890  rack2
# Datacenter: eu-west-1
# ====================
# UN  10.0.2.1  256.0 KiB  256  50.1%  ghi11111  rack1
# UN  10.0.2.2  256.0 KiB  256  49.9%  ghi22222  rack2
```

---

## 2. NetworkTopologyStrategy

### 2.1 Why NetworkTopologyStrategy

`SimpleStrategy` ignores datacenter and rack topology. It places replicas by walking the token ring regardless of physical location, which means all replicas may land in the same rack or DC. **Never use SimpleStrategy in production multi-DC deployments.**

`NetworkTopologyStrategy` (NTS) is datacenter-aware and rack-aware:
1. For each DC, it walks the token ring to find the first node in a *different rack* from the previous replica.
2. It repeats until the per-DC replication factor is satisfied.
3. This guarantees replicas are spread across racks within each DC.

### 2.2 Keyspace Creation

```sql
-- Production multi-DC keyspace
CREATE KEYSPACE ecommerce
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3,
  'eu-west-1': 3,
  'ap-south-1': 2
};

-- The DC names MUST match the dc= value in cassandra-rackdc.properties.
-- Case-sensitive. A mismatch silently creates replicas in a "phantom" DC.
```

### 2.3 Altering Replication

```sql
-- Increase RF in an existing DC
ALTER KEYSPACE ecommerce
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3,
  'eu-west-1': 3,
  'ap-south-1': 3   -- was 2, now 3
};

-- After altering RF upward, run repair to stream data to new replicas:
-- nodetool repair -full ecommerce
```

### 2.4 System Keyspaces

```sql
-- system_auth, system_traces, and system_distributed should also use NTS
ALTER KEYSPACE system_auth
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3,
  'eu-west-1': 3,
  'ap-south-1': 3
};

-- CRITICAL: if system_auth uses SimpleStrategy with RF=1 and that single
-- replica node goes down, all authentication fails cluster-wide.
```

---

## 3. Cross-DC Replication

### 3.1 How Replication Works Across DCs

When a write arrives at a coordinator node:

1. The coordinator determines all replica nodes (local + remote DCs) from the token ring and NTS settings.
2. It sends the mutation to **all** replica nodes across all DCs.
3. For remote DCs, the coordinator picks one node per remote DC as a **forwarding coordinator**. That node forwards the write to the other replicas in its DC.
4. This reduces cross-WAN messages from N to 1 per remote DC.

```
Client --> Coordinator (us-east-1)
              |
              |--> Replica 1 (us-east-1, local)
              |--> Replica 2 (us-east-1, local)
              |--> Replica 3 (us-east-1, local)
              |
              |--> Forwarding Coordinator (eu-west-1) --> Replicas in eu-west-1
              |--> Forwarding Coordinator (ap-south-1) --> Replicas in ap-south-1
```

### 3.2 Asynchronous Cross-DC Writes

When using `LOCAL_QUORUM`, the coordinator acknowledges the write as soon as a quorum in the **local DC** responds. Remote DC writes happen asynchronously. This means:

- Local write latency is unaffected by WAN latency.
- Remote DCs are **eventually consistent** with the local DC.
- If the remote DC is temporarily unreachable, hinted handoff queues the mutations.

### 3.3 Hinted Handoff Across DCs

```yaml
# cassandra.yaml
hinted_handoff_enabled: true
max_hint_window: 10800000          # 3 hours (default)
hinted_handoff_throttle_in_kb: 1024  # throttle per-destination hint delivery

# If a remote DC is down for longer than max_hint_window,
# hints are dropped and you MUST run a full repair after the DC recovers.
```

### 3.4 Verifying Cross-DC Replication

```bash
# Write to us-east-1
cqlsh 10.0.1.1 -e "
  CONSISTENCY LOCAL_ONE;
  INSERT INTO ecommerce.orders (order_id, customer, total)
  VALUES (uuid(), 'alice', 99.99);
"

# Read from eu-west-1 to verify replication
cqlsh 10.0.2.1 -e "
  CONSISTENCY LOCAL_ONE;
  SELECT * FROM ecommerce.orders LIMIT 5;
"

# Check pending hints (indicates cross-DC backlog)
nodetool tpstats | grep HintedHandoff
```

---

## 4. Consistency Across DC

### 4.1 Consistency Levels for Multi-DC

| Level | Scope | Acknowledged By | Typical Use |
|-------|-------|-----------------|-------------|
| `ONE` | Global | 1 replica (any DC) | Low-latency reads, acceptable staleness |
| `LOCAL_ONE` | Local DC | 1 replica in coordinator's DC | Lowest latency, single-DC guarantee |
| `LOCAL_QUORUM` | Local DC | Quorum in coordinator's DC | Standard production reads/writes |
| `QUORUM` | Global | Global quorum across all DCs | Rarely used multi-DC (high latency) |
| `EACH_QUORUM` | All DCs | Quorum in **every** DC | Strong cross-DC consistency (writes only) |
| `ALL` | Global | Every replica in every DC | Almost never used (one node down = failure) |
| `LOCAL_SERIAL` | Local DC | Paxos quorum in local DC | Lightweight transactions, local |
| `SERIAL` | Global | Paxos quorum across all DCs | Lightweight transactions, global |

### 4.2 Strong Consistency Formula

```
R + W > RF  (per DC, when using LOCAL_ levels)

Example with RF=3 per DC:
  LOCAL_QUORUM writes (W=2) + LOCAL_QUORUM reads (R=2) => 2+2=4 > 3  ✓ strong
  LOCAL_ONE writes (W=1) + LOCAL_QUORUM reads (R=2) => 1+2=3 = 3  ✗ NOT strong
```

### 4.3 Common Multi-DC Consistency Patterns

```sql
-- Pattern 1: LOCAL_QUORUM everywhere (recommended)
-- Strong consistency within each DC, eventual across DCs.
CONSISTENCY LOCAL_QUORUM;
INSERT INTO orders (order_id, total) VALUES (uuid(), 149.99);
SELECT * FROM orders WHERE order_id = ?;

-- Pattern 2: LOCAL_QUORUM writes, LOCAL_ONE reads
-- Acceptable when slight staleness on reads is tolerable.
-- Write:
CONSISTENCY LOCAL_QUORUM;
INSERT INTO page_views (page, ts, views) VALUES ('home', now(), 1);
-- Read:
CONSISTENCY LOCAL_ONE;
SELECT * FROM page_views WHERE page = 'home' LIMIT 100;

-- Pattern 3: EACH_QUORUM writes (rare, high-value data)
-- Ensures data is durably written in ALL DCs before acknowledging.
CONSISTENCY EACH_QUORUM;
INSERT INTO financial_transactions (tx_id, amount) VALUES (uuid(), 10000.00);
-- WARNING: one unreachable DC blocks all writes at this level.
```

### 4.4 Lightweight Transactions Across DCs

```sql
-- LOCAL_SERIAL: Paxos consensus in the local DC only
CONSISTENCY LOCAL_SERIAL;
INSERT INTO users (user_id, email)
VALUES ('user123', 'alice@example.com')
IF NOT EXISTS;

-- SERIAL: Paxos consensus across ALL DCs (very high latency)
CONSISTENCY SERIAL;
UPDATE accounts SET balance = 500
WHERE account_id = 'acct1'
IF balance >= 500;

-- In multi-DC, prefer LOCAL_SERIAL unless global uniqueness is required.
```

---

## 5. Snitch Configuration

The **snitch** tells Cassandra which DC and rack each node belongs to. The snitch directly affects replica placement and request routing.

### 5.1 Snitch Types

| Snitch | Description | Use Case |
|--------|-------------|----------|
| `SimpleSnitch` | Single DC, no rack awareness | Dev/test only |
| `PropertyFileSnitch` | Reads `cassandra-topology.properties` | Legacy; requires file on every node |
| `GossipingPropertyFileSnitch` | Reads local `cassandra-rackdc.properties`, shares via gossip | **Recommended for all production** |
| `Ec2Snitch` | AWS single-region, maps AZ to rack | AWS single-region |
| `Ec2MultiRegionSnitch` | AWS multi-region, maps region to DC | AWS multi-region |
| `GoogleCloudSnitch` | GCP, maps zone to rack, region to DC | GCP deployments |
| `AzureSnitch` (4.1+) | Azure, maps availability zone to rack | Azure deployments |
| `RackInferringSnitch` | Infers from IP address octets | Rare; fragile |

### 5.2 GossipingPropertyFileSnitch (Recommended)

```yaml
# cassandra.yaml
endpoint_snitch: GossipingPropertyFileSnitch

# cassandra-rackdc.properties (one per node)
dc=us-east-1
rack=rack1
# prefer_local=true  # (optional) prefer local DC for reads
```

### 5.3 Cloud-Provider Snitches

```yaml
# AWS multi-region
endpoint_snitch: Ec2MultiRegionSnitch
# DC name = AWS region (e.g., us-east-1)
# Rack = availability zone (e.g., us-east-1a)
# Uses public IPs for cross-region, private for intra-region

# GCP
endpoint_snitch: GoogleCloudSnitch
# DC = GCP region (e.g., us-central1)
# Rack = zone (e.g., us-central1-a)
```

### 5.4 Switching Snitches

Changing the snitch on an existing cluster is risky. Procedure:

1. Set the new snitch in `cassandra.yaml` on all nodes.
2. Update `cassandra-rackdc.properties` on all nodes with correct DC/rack.
3. Perform a rolling restart (one node at a time, wait for `UN` status).
4. Run `nodetool repair -full` on every node to ensure data placement matches the new topology.
5. Verify with `nodetool status` that DC/rack assignments are correct.

---

## 6. Cross-DC Write Path

### 6.1 Detailed Write Flow

```
1. Client sends write to coordinator in DC-A.
2. Coordinator computes replica list from token + NTS.
3. For local DC (DC-A):
   - Sends mutation directly to all local replicas.
   - Waits for LOCAL_QUORUM acknowledgments.
4. For each remote DC (DC-B, DC-C):
   - Selects one node as the remote "forwarding coordinator."
   - Sends mutation over WAN to that forwarding coordinator.
   - Forwarding coordinator fans out to all replicas in its DC.
   - Remote acknowledgments flow back but are NOT waited for
     (when using LOCAL_QUORUM).
5. Coordinator acknowledges write to client after local quorum.
```

### 6.2 Write Latency Characteristics

| Phase | Typical Latency |
|-------|----------------|
| Local memtable write | < 1 ms |
| Commitlog fsync | 1-5 ms (periodic sync) |
| Local quorum acknowledgment | 2-10 ms |
| Cross-DC WAN hop (same continent) | 10-40 ms |
| Cross-DC WAN hop (intercontinental) | 60-200 ms |

### 6.3 Commit Log Configuration for Multi-DC

```yaml
# cassandra.yaml
# periodic mode: batch syncs every commitlog_sync_period_in_ms
commitlog_sync: periodic
commitlog_sync_period_in_ms: 10000    # 10 seconds

# batch mode: every write syncs commitlog (slower but more durable)
# commitlog_sync: batch
# commitlog_sync_batch_window_in_ms: 2

# For multi-DC, periodic is typically fine because
# remote replicas provide additional durability.
```

---

## 7. Cross-DC Read Path

### 7.1 Coordinator-Local Reads

With `LOCAL_QUORUM`, the coordinator contacts only replicas in its own DC:

```
Client --> Coordinator (eu-west-1)
              |
              |--> Replica 1 (eu-west-1) -- full data
              |--> Replica 2 (eu-west-1) -- digest
              |
              Compare digests. If match, return data.
              If mismatch, fetch full data from both, reconcile (latest timestamp wins).
```

### 7.2 Speculative Retry

```yaml
# cassandra.yaml
# If a local replica is slow, send a speculative read to another replica
# to reduce tail latency.

# Table-level setting:
# CREATE TABLE ... WITH speculative_retry = '99percentile';
# Options: NONE, ALWAYS, Xpercentile, Xms
```

```sql
-- Set speculative retry per table
CREATE TABLE ecommerce.products (
    product_id uuid PRIMARY KEY,
    name text,
    price decimal
) WITH speculative_retry = '95percentile';

-- For multi-DC latency-sensitive reads:
ALTER TABLE ecommerce.products
WITH speculative_retry = '50ms';
```

### 7.3 Dynamic Snitch

The **dynamic snitch** wraps the configured snitch and tracks replica response times. It routes reads to the fastest-responding replica, avoiding slow nodes.

```yaml
# cassandra.yaml
dynamic_snitch: true                          # enabled by default
dynamic_snitch_update_interval_in_ms: 100     # scoring interval
dynamic_snitch_reset_interval_in_ms: 600000   # reset scores every 10 min
dynamic_snitch_badness_threshold: 1.0         # switch when 100% slower
```

---

## 8. Adding a New Datacenter

### 8.1 Step-by-Step Procedure

```bash
# Step 1: Update schema to include the new DC
# Run from any existing node
cqlsh -e "
  ALTER KEYSPACE ecommerce
  WITH REPLICATION = {
    'class': 'NetworkTopologyStrategy',
    'us-east-1': 3,
    'eu-west-1': 3,
    'ap-south-1': 3   -- NEW DC
  };
"

# Repeat for system_auth, system_traces, system_distributed
cqlsh -e "
  ALTER KEYSPACE system_auth
  WITH REPLICATION = {
    'class': 'NetworkTopologyStrategy',
    'us-east-1': 3,
    'eu-west-1': 3,
    'ap-south-1': 3
  };
"

# Step 2: Configure new nodes
# cassandra.yaml on each new node:
#   cluster_name: same as existing cluster
#   seeds: include seeds from ALL DCs
#   endpoint_snitch: GossipingPropertyFileSnitch
# cassandra-rackdc.properties:
#   dc=ap-south-1
#   rack=rack1

# Step 3: Start new nodes one at a time
# They will join the ring and begin streaming data
cassandra

# Step 4: Monitor bootstrap progress
nodetool netstats          # streaming progress
nodetool status            # all nodes should show UN

# Step 5: Run repair on new DC
nodetool repair -full -dc ap-south-1 ecommerce

# Step 6: Route client traffic to new DC
# Update application connection config to include new DC endpoints
```

### 8.2 Streaming During Bootstrap

```bash
# Monitor streaming bandwidth
nodetool netstats

# Throttle streaming to avoid saturating WAN
# cassandra.yaml:
# stream_throughput_outbound_megabits_per_sec: 200
# inter_dc_stream_throughput_outbound_megabits_per_sec: 50

# Check compaction queue (streaming triggers compaction)
nodetool compactionstats
```

### 8.3 Automating with nodetool

```bash
# After all nodes are UP in the new DC, rebuild from a source DC
nodetool rebuild -- us-east-1
# This streams all data from us-east-1 to the local node.
# Run on EACH node in the new DC.

# For large datasets, rebuild is faster than waiting for repair
# because it reads entire SSTables rather than computing diffs.
```

---

## 9. Removing a Datacenter

### 9.1 Safe Removal Procedure

```bash
# Step 1: Redirect ALL client traffic away from the DC being removed.
# Update application load balancer / connection policies.

# Step 2: Change keyspace replication to exclude the DC
cqlsh -e "
  ALTER KEYSPACE ecommerce
  WITH REPLICATION = {
    'class': 'NetworkTopologyStrategy',
    'us-east-1': 3,
    'eu-west-1': 3
    -- ap-south-1 removed
  };
"
# Repeat for system_auth, system_traces, system_distributed.

# Step 3: Run repair on remaining DCs to ensure no data loss
nodetool repair -full ecommerce

# Step 4: Decommission each node in the removed DC (one at a time)
nodetool decommission
# Wait for completion before decommissioning the next node.

# Step 5: Verify the DC is gone
nodetool status
# Only us-east-1 and eu-west-1 should appear.
```

### 9.2 Common Mistakes

- Removing the DC from replication **before** redirecting traffic causes `UnavailableException` for clients still pointing there.
- Forgetting to update `system_auth` replication causes authentication failures if the removed DC held the only auth replicas.
- Shutting down nodes without `decommission` leaves token ranges unowned and data behind.

---

## 10. Multi-DC Repair Strategies

### 10.1 Why Repair Matters in Multi-DC

Without regular repair, replicas across DCs drift apart due to:
- Dropped hints (remote DC down > `max_hint_window`).
- Network partitions causing missed mutations.
- Clock skew leading to incorrect conflict resolution.

### 10.2 Repair Types

```bash
# Full repair: compare all data, stream differences
nodetool repair -full ecommerce

# Incremental repair (4.0+): only repair unrepaired SSTables
nodetool repair ecommerce

# Preview repair (4.0+): shows what WOULD be repaired without modifying data
nodetool repair --preview ecommerce

# Sub-range repair: repair a specific token range
nodetool repair -st <start_token> -et <end_token> ecommerce

# DC-local repair: repair only within the local DC
nodetool repair -local ecommerce

# Cross-DC repair: repair between specific DCs
nodetool repair -dc us-east-1 -dc eu-west-1 ecommerce
```

### 10.3 Repair Scheduling

```bash
# Best practice: run repair within gc_grace_seconds (default 10 days)
# If repair does not complete within gc_grace_seconds, deleted data
# can resurrect ("zombie data").

# Recommended schedule:
# - Run repair every 7 days (leaves 3-day buffer before gc_grace_seconds)
# - Stagger repairs: don't repair all keyspaces on all nodes simultaneously
# - Use sub-range repair for large clusters to parallelize

# Example cron job (run on each node, staggered):
# 0 2 * * 0  nodetool repair -full -pr ecommerce  # Sunday 2 AM, primary range only
```

### 10.4 Cassandra 4.x Repair Improvements

```bash
# Transient replication (4.0+, experimental)
# Allows "cheap" replicas that only store data temporarily for availability
# but do not participate in read quorum. Reduces repair overhead.

# Preview repair
nodetool repair --preview ecommerce
# Output: "Previewed X ranges, Y bytes need repair"
# Useful for monitoring data divergence without triggering actual repair.

# Incremental repair improvements in 4.0:
# - Repaired/unrepaired SSTable separation is more reliable
# - Anti-compaction overhead reduced
```

---

## 11. Latency and WAN Optimization

### 11.1 Inter-DC Streaming Throttle

```yaml
# cassandra.yaml
# Limit outbound streaming bandwidth to avoid saturating WAN
stream_throughput_outbound_megabits_per_sec: 200           # intra-DC
inter_dc_stream_throughput_outbound_megabits_per_sec: 50   # cross-DC (lower)
```

### 11.2 Compression for Inter-Node Communication

```yaml
# cassandra.yaml
# Compress inter-node traffic (reduces WAN bandwidth usage significantly)
internode_compression: dc     # Options: all, dc, none
# "dc" = compress only cross-DC traffic (recommended)
# "all" = compress intra-DC too (CPU cost, minimal benefit on LAN)
# "none" = no compression
```

### 11.3 Connection Pooling

```yaml
# cassandra.yaml (4.0+)
# Native protocol connection settings
native_transport_max_threads: 128
native_transport_max_frame_size_in_mb: 256

# Internode messaging (4.0 reworked messaging)
# Cassandra 4.0 uses a single connection per node pair with multiplexing
# instead of the old per-thread connection model.
internode_application_send_queue_capacity_in_bytes: 4194304    # 4 MB
internode_application_receive_queue_capacity_in_bytes: 4194304
```

### 11.4 Client-Side Multi-DC Configuration

```java
// Java driver (DataStax 4.x driver)
// Configure DC-aware load balancing
CqlSession session = CqlSession.builder()
    .addContactPoint(new InetSocketAddress("10.0.1.1", 9042))
    .withLocalDatacenter("us-east-1")
    .withConfigLoader(DriverConfigLoader.programmaticBuilder()
        .withString(DefaultDriverOption.LOAD_BALANCING_POLICY_CLASS,
            "DcInferringLoadBalancingPolicy")
        .withBoolean(DefaultDriverOption.LOAD_BALANCING_DC_FAILOVER_ALLOW_FOR_LOCAL_CL,
            true)  // fail over to remote DC for local CLs
        .withInt(DefaultDriverOption.LOAD_BALANCING_DC_FAILOVER_MAX_NODES_PER_REMOTE_DC,
            2)     // max 2 nodes per remote DC for failover
        .build())
    .build();
```

```python
# Python driver - DC-aware policy
from cassandra.cluster import Cluster
from cassandra.policies import DCAwareRoundRobinPolicy

cluster = Cluster(
    contact_points=['10.0.1.1', '10.0.2.1'],
    load_balancing_policy=DCAwareRoundRobinPolicy(
        local_dc='us-east-1',
        used_hosts_per_remote_dc=2
    )
)
session = cluster.connect('ecommerce')
```

---

## 12. Multi-DC Security

### 12.1 Internode Encryption

```yaml
# cassandra.yaml
# MANDATORY for multi-DC: encrypt all inter-node traffic over WAN
server_encryption_options:
  internode_encryption: dc       # Options: none, all, dc, rack
  # "dc" = encrypt only cross-DC traffic (saves CPU on LAN)
  # "all" = encrypt everything (recommended if you don't trust LAN)
  enable_legacy_ssl_storage_port: false
  keystore: /etc/cassandra/conf/.keystore
  keystore_password: ${KEYSTORE_PASSWORD}
  truststore: /etc/cassandra/conf/.truststore
  truststore_password: ${TRUSTSTORE_PASSWORD}
  protocol: TLSv1.3
  cipher_suites:
    - TLS_AES_256_GCM_SHA384
    - TLS_AES_128_GCM_SHA256
  require_client_auth: true       # mutual TLS between nodes
  require_endpoint_verification: true  # verify hostname in cert
```

### 12.2 Firewall Rules

```bash
# Required ports between DCs (minimum):
# 7000   - internode communication (or 7001 for TLS)
# 7199   - JMX (restrict to monitoring only, do NOT expose over WAN)
# 9042   - native transport (client connections; usually not cross-DC)
# 9142   - native transport SSL

# iptables example: allow internode from specific DC CIDRs
iptables -A INPUT -p tcp --dport 7001 -s 10.0.2.0/24 -j ACCEPT  # eu-west-1
iptables -A INPUT -p tcp --dport 7001 -s 10.0.3.0/24 -j ACCEPT  # ap-south-1
iptables -A INPUT -p tcp --dport 7001 -j DROP
```

### 12.3 Separate Auth Keyspace Replication

```sql
-- ALWAYS replicate system_auth to ALL DCs with adequate RF
-- Otherwise, if the DC holding auth replicas goes down,
-- no user can authenticate anywhere.
ALTER KEYSPACE system_auth
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3,
  'eu-west-1': 3,
  'ap-south-1': 3
};

-- Run repair after altering:
-- nodetool repair -full system_auth
```

---

## 13. Monitoring Multi-DC Clusters

### 13.1 Key Metrics

```bash
# Cross-DC replication lag (approximation via hint backlog)
nodetool tpstats | grep -i hint

# Streaming activity
nodetool netstats

# Per-DC latency histograms
nodetool proxyhistograms

# Dropped messages (indicates overload or network issues)
nodetool tpstats | grep -i dropped

# Pending tasks per thread pool
nodetool tpstats
```

### 13.2 Prometheus / Grafana Metrics

```yaml
# Key JMX metrics to export for multi-DC monitoring:
#
# org.apache.cassandra.metrics:type=ClientRequest,scope=Write,name=Latency
# org.apache.cassandra.metrics:type=ClientRequest,scope=Read,name=Latency
# org.apache.cassandra.metrics:type=HintedHandOffManager,name=Hints_not_stored-*
# org.apache.cassandra.metrics:type=Storage,name=Hints
# org.apache.cassandra.metrics:type=DroppedMessage,scope=*
# org.apache.cassandra.metrics:type=Streaming,name=*

# Use the JMX exporter agent or Cassandra's built-in metrics reporter
# to push metrics to Prometheus.
```

### 13.3 Cross-DC Health Checks

```bash
# Verify all DCs are reachable
nodetool describecluster
# Lists each DC's schema versions. If schemas diverge,
# cross-DC communication is broken.

# Check schema agreement
nodetool describecluster | grep "Schema versions"
# All nodes should report the same schema hash.
# Disagreement often indicates a down node or network partition.

# Check gossip state for remote nodes
nodetool gossipinfo | grep -A 5 "10.0.2"
# STATUS should be NORMAL, not REMOVING, LEAVING, etc.
```

---

## 14. Cassandra 4.x/5.x Multi-DC Features

### 14.1 Cassandra 4.0 Improvements

- **Transient replication** (experimental): allows creating "cheap" replicas that hold data temporarily for availability but do not count toward read quorum. Reduces cross-DC storage and repair overhead.
- **Virtual tables** (`system_views` keyspace): monitor per-node state without JMX -- useful for remote DC monitoring.
- **Audit logging**: centralized audit trail for cross-DC compliance.
- **Improved streaming** (Zero-Copy Streaming): SSTable streaming is 5x faster, significantly speeding up cross-DC bootstrap and rebuild.
- **Internode messaging overhaul**: single connection per peer with multiplexing replaces the old thread-per-connection model. Reduces connection count between DCs.

### 14.2 Cassandra 5.0 Multi-DC Enhancements

- **Accord protocol**: distributed transaction protocol replacing Paxos for lightweight transactions. Designed for multi-DC with lower latency than Paxos.
- **Unified Compaction Strategy (UCS)**: automatically adapts compaction behavior, simplifying multi-DC operational tuning.
- **Storage Attached Indexes (SAI)**: distributed secondary indexes that work correctly across DCs without the problems of legacy secondary indexes.
- **Guardrails framework**: set cluster-wide limits (partition size, tombstones, etc.) that are enforced across all DCs.
- **Java 17 requirement**: all nodes across all DCs must run Java 17+.

```sql
-- Cassandra 5.0: SAI indexes work correctly in multi-DC
CREATE INDEX ON ecommerce.products (category) USING 'sai';

-- Query with SAI (works across DCs without ALLOW FILTERING)
SELECT * FROM ecommerce.products WHERE category = 'electronics';
```

---

## 15. Troubleshooting

### 15.1 UnavailableException on Cross-DC Writes

**Symptom**: writes fail with `UnavailableException` when using `EACH_QUORUM`.

**Cause**: one DC does not have enough live replicas to satisfy its quorum.

**Fix**:
```bash
# Check which nodes are down
nodetool status

# If a DC is fully unreachable, switch to LOCAL_QUORUM
# EACH_QUORUM requires quorum in EVERY DC

# If nodes are down, bring them back or reduce RF in that DC
```

### 15.2 Schema Disagreement

**Symptom**: `nodetool describecluster` shows multiple schema versions.

**Cause**: schema change did not propagate to all DCs (network issue, down node).

**Fix**:
```bash
# Check which nodes have the old schema
nodetool describecluster

# Restart the disagreeing node
nodetool drain && systemctl restart cassandra

# If persistent, force schema sync
nodetool resetlocalschema   # on the disagreeing node
```

### 15.3 High Cross-DC Latency

**Symptom**: read/write latency spikes when cross-DC communication is involved.

**Fix**:
```bash
# Ensure internode_compression is set to "dc"
grep internode_compression /etc/cassandra/cassandra.yaml

# Verify inter_dc_stream_throughput is not saturating WAN
nodetool netstats

# Check for large partitions causing high streaming volume
nodetool tablestats ecommerce.orders | grep "Compacted partition maximum"
```

### 15.4 Zombie Data (Tombstone Resurrection)

**Symptom**: deleted rows reappear after repair.

**Cause**: repair did not run within `gc_grace_seconds`, tombstones were garbage-collected in one DC but the original data still exists in another.

**Fix**:
```bash
# Run repair immediately across all DCs
nodetool repair -full ecommerce

# Prevent recurrence: ensure repair runs within gc_grace_seconds
# Default gc_grace_seconds = 864000 (10 days)
# Run repair every 7 days
```

### 15.5 Hinted Handoff Backlog Growing

**Symptom**: `nodetool tpstats` shows increasing hint count; remote DC lagging.

**Fix**:
```bash
# Check hint backlog
nodetool tpstats | grep -i hint

# Increase hint delivery throttle
# cassandra.yaml: hinted_handoff_throttle_in_kb: 2048

# If hints exceed max_hint_window, they are dropped.
# You must run repair after the remote DC recovers.
```

### 15.6 Bootstrap Stuck at 0%

**Symptom**: new node in a new DC joins the ring but streaming never starts.

**Fix**:
```bash
# Verify the node can reach seeds in other DCs
nodetool netstats

# Check firewall rules (port 7000/7001 must be open cross-DC)
# Check seed list includes seeds from existing DCs
grep seeds /etc/cassandra/cassandra.yaml

# Use rebuild instead of relying on automatic bootstrap
nodetool rebuild -- us-east-1
```

### 15.7 Authentication Failures After DC Loss

**Symptom**: users cannot log in after a DC goes down.

**Cause**: `system_auth` keyspace used `SimpleStrategy` with RF=1, and the single replica was in the lost DC.

**Fix**:
```sql
-- From a surviving node:
ALTER KEYSPACE system_auth
WITH REPLICATION = {
  'class': 'NetworkTopologyStrategy',
  'us-east-1': 3,
  'eu-west-1': 3
};
-- Then repair: nodetool repair -full system_auth
```

### 15.8 Gossip Partition Between DCs

**Symptom**: nodes in DC-A see nodes in DC-B as DOWN, but DC-B nodes are actually healthy.

**Fix**:
```bash
# Check gossip state
nodetool gossipinfo

# Verify network connectivity (port 7000/7001)
nc -zv 10.0.2.1 7001

# Check phi_convict_threshold (may need to increase for high-latency WANs)
# Default: 8. For cross-continent links, try 10-12.
grep phi_convict_threshold /etc/cassandra/cassandra.yaml
```

### 15.9 DC Failover Not Working

**Symptom**: clients do not fail over to a remote DC when the local DC goes down.

**Fix**: the Cassandra server does not do client failover; it is a **client driver** responsibility.

```java
// Java driver: enable DC failover for local consistency levels
CqlSession session = CqlSession.builder()
    .withConfigLoader(DriverConfigLoader.programmaticBuilder()
        .withBoolean(DefaultDriverOption.LOAD_BALANCING_DC_FAILOVER_ALLOW_FOR_LOCAL_CL, true)
        .withInt(DefaultDriverOption.LOAD_BALANCING_DC_FAILOVER_MAX_NODES_PER_REMOTE_DC, 2)
        .build())
    .build();
```

### 15.10 Inconsistent Data Across DCs After Network Partition

**Symptom**: same key returns different values in different DCs.

**Fix**:
```bash
# Run full cross-DC repair
nodetool repair -full -dc us-east-1 -dc eu-west-1 ecommerce

# Use tracing to verify conflict resolution (last-write-wins by timestamp)
cqlsh -e "TRACING ON; SELECT * FROM ecommerce.orders WHERE order_id = ?;"

# If clock skew caused wrong "winner", consider NTP synchronization
# All Cassandra nodes MUST run NTP. Clock skew > 1 second is dangerous.
```

---

## 16. FAQ

### Q1: Can I use SimpleStrategy for a multi-DC cluster?

No. `SimpleStrategy` is completely unaware of DCs and racks. All replicas may land in a single DC, defeating the purpose of multi-DC. Always use `NetworkTopologyStrategy` in production.

### Q2: How many seeds should I have per DC?

Two or three per DC. Seeds are only used for gossip bootstrapping. Having too many seeds (every node) actually slows gossip convergence because seeds have special gossip behavior.

### Q3: What happens if all seeds are down?

Existing nodes continue to operate because gossip state is already shared. However, new nodes cannot bootstrap without at least one reachable seed. Bring at least one seed back up before adding new nodes.

### Q4: Can different DCs have different replication factors?

Yes. `NetworkTopologyStrategy` allows setting RF independently per DC. A common pattern is RF=3 in primary DCs and RF=2 in analytics or DR DCs.

### Q5: How does Cassandra handle a full DC outage?

Writes continue in surviving DCs (using `LOCAL_QUORUM`). Mutations for the downed DC are queued as hints (up to `max_hint_window`, default 3 hours). After recovery, run `nodetool repair` to fix any data that exceeded the hint window.

### Q6: Should I use QUORUM or LOCAL_QUORUM in multi-DC?

Use `LOCAL_QUORUM` for almost everything. `QUORUM` counts replicas across all DCs, meaning cross-WAN latency impacts every request. `LOCAL_QUORUM` provides strong consistency within a single DC with no WAN dependency.

### Q7: Can I run different Cassandra versions in different DCs?

Yes, temporarily during rolling upgrades. Cassandra supports mixed-version clusters within one minor version (e.g., 4.0 and 4.1). Cross-major-version (3.x and 4.x) is not supported for extended periods.

### Q8: How do I monitor cross-DC replication lag?

There is no built-in "replication lag" metric. Proxies include: hint backlog size, `nodetool repair --preview` output, and application-level consistency checks (write to DC-A, read from DC-B, compare).

### Q9: Is it possible to have a read-only DC?

Not natively. All DCs accept reads and writes. However, you can configure clients to only send reads (not writes) to a specific DC, and you can use `LOCAL_QUORUM` writes only in the "primary" DC. The "read-only" DC still receives replicated writes.

### Q10: How do I handle clock skew between DCs?

Cassandra uses timestamps for conflict resolution (last-write-wins). Clock skew between DCs can cause the "wrong" write to win. Mitigation:
- Run NTP on every node, synced to the same stratum.
- Use client-provided timestamps when possible (driver controls the timestamp).
- Monitor clock drift: `ntpq -p` on each node.
- Maximum acceptable skew: ideally < 10 ms; > 1 second is dangerous.

### Q11: What is the Accord protocol in Cassandra 5.0?

Accord is a leaderless distributed transaction protocol that replaces Paxos for lightweight transactions. It provides lower latency in multi-DC because it does not require a single leader, unlike Paxos which must coordinate through a proposer.

### Q12: Can I add a DC without downtime?

Yes. Adding a DC is an online operation. You alter the keyspace, start nodes in the new DC, and they stream data from existing DCs. No downtime is required. However, the streaming may temporarily increase load on the source DCs.

---

*Questo documento fa parte del modulo 07 "NoSQL Cassandra" della Data Encyclopedia.*
