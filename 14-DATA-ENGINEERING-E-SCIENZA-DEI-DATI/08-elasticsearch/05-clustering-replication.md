# Clustering e Replicazione in Elasticsearch

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Indice
1. Shard Allocation and Balancing
2. Allocation Awareness and Forced Awareness
3. Index Lifecycle Management (ILM)
4. Hot-Warm-Cold-Frozen Architecture
5. Shrink, Split, and Clone API
6. Cross-Cluster Replication (CCR)
7. Cross-Cluster Search (CCS)
8. Split-Brain Prevention
9. Rolling Restarts and Upgrade Procedures
10. Troubleshooting
11. FAQ
12. Exercises

---

## 1. Shard Allocation and Balancing

### 1.1 The Allocation Algorithm

Elasticsearch's shard allocator determines which node should host each shard. The algorithm runs on the elected master node and evaluates a set of **allocator deciders** — each decider can allow, deny, or throttle the allocation of a shard to a particular node. All deciders must agree before a shard is placed on a node.

The built-in deciders include:

| Decider | Purpose |
|---------|---------|
| `SameShardAllocator` | Prevents placing a primary and its replica on the same node |
| `DiskThresholdDecider` | Prevents allocation when disk usage exceeds watermarks |
| `FilterAllocationDecider` | Enforces include/exclude/require allocation filters |
| `AwarenessAllocationDecider` | Distributes replicas across awareness zones |
| `ShardsLimitAllocationDecider` | Limits shards per node per index |
| `ThrottlingAllocationDecider` | Limits concurrent recoveries to prevent network saturation |
| `RebalanceOnlyWhenActiveAllocationDecider` | Blocks rebalancing until all primaries are started |
| `MaxRetryAllocationDecider` | Gives up on a shard after N failed allocation attempts |
| `ReplicaAfterPrimaryActiveAllocationDecider` | Allocates replicas only after the primary is started |
| `ClusterRebalanceAllocationDecider` | Controls when rebalancing is allowed based on cluster state |

The allocator also evaluates a **weight function** that balances two competing objectives: keeping an equal number of shards per node (shard balance factor) and keeping an equal number of shards for each index per node (index balance factor). These are configurable:

```http
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.balance.shard": 0.45,
    "cluster.routing.allocation.balance.index": 0.55,
    "cluster.routing.allocation.balance.threshold": 1.0
  }
}
```

- `balance.shard`: weight given to equalizing total shard count across nodes (default 0.45).
- `balance.index`: weight given to equalizing per-index shard count across nodes (default 0.55).
- `balance.threshold`: minimum improvement required before a shard move is considered (default 1.0). Higher values reduce the frequency of rebalancing moves.

### 1.2 Allocation Filtering

Allocation filters control which nodes can host shards for a given index. Three levels of filtering exist:

- `require`: the node must have ALL specified attributes.
- `include`: the node must have AT LEAST ONE of the specified attributes.
- `exclude`: the node must NOT have ANY of the specified attributes.

Filters operate on built-in node attributes (`_name`, `_ip`, `_host`, `_id`, `_tier_preference`) or custom attributes defined in `elasticsearch.yml`:

```yaml
# elasticsearch.yml — custom node attributes
node.attr.zone: eu-south-1a
node.attr.rack: rack-3
node.attr.box_type: hot
node.attr.region: europe
```

```http
// Index-level allocation filtering
PUT /orders-2026.05/_settings
{
  "index": {
    "routing.allocation.require.box_type": "hot",
    "routing.allocation.exclude._name": "decommissioned-node",
    "routing.allocation.total_shards_per_node": 2
  }
}

// Cluster-level filtering (affects all indices)
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.exclude._ip": "10.0.1.5,10.0.1.6"
  }
}

// Drain a node before decommissioning (move all shards away)
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.allocation.exclude._name": "node-to-remove"
  }
}
```

### 1.3 Shard Allocation Throttling

During recovery (node restart, replica allocation, rebalancing), Elasticsearch limits concurrent shard movements to prevent network and disk saturation:

```http
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.node_concurrent_incoming_recoveries": 2,
    "cluster.routing.allocation.node_concurrent_outgoing_recoveries": 2,
    "cluster.routing.allocation.node_concurrent_recoveries": 2,
    "cluster.routing.allocation.cluster_concurrent_rebalance": 2,
    "indices.recovery.max_bytes_per_sec": "100mb"
  }
}
```

In a high-bandwidth environment (10 Gbps+ network, NVMe storage), increasing these values dramatically speeds up recovery:

```http
// Aggressive recovery settings for fast hardware
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.allocation.node_concurrent_incoming_recoveries": 8,
    "cluster.routing.allocation.node_concurrent_outgoing_recoveries": 8,
    "cluster.routing.allocation.cluster_concurrent_rebalance": 8,
    "indices.recovery.max_bytes_per_sec": "500mb"
  }
}
```

Use transient settings for temporary speed-ups (they revert on cluster restart) and persistent settings for permanent configuration.

### 1.4 Delayed Allocation After Node Loss

When a node leaves the cluster, Elasticsearch waits before reallocating its shards. This delay prevents unnecessary data movement when a node is restarted quickly (e.g., rolling restart, brief outage):

```http
// Per-index delayed allocation
PUT /my-index/_settings
{
  "index": {
    "unassigned.node_left.delayed_timeout": "5m"
  }
}

// Cluster-wide default
PUT /_cluster/settings
{
  "persistent": {
    "index.unassigned.node_left.delayed_timeout": "5m"
  }
}

// Check which shards are waiting with delayed allocation
GET /_cat/shards?v&h=index,shard,prirep,state,unassigned.reason,unassigned.at,unassigned.for&s=state
```

In production, 5 minutes is a reasonable default. For planned maintenance windows, increase to 30-60 minutes. For environments where nodes may not return (cloud spot instances), set to 0 or 1 minute.

### 1.5 Manual Shard Routing with the Reroute API

The `_cluster/reroute` API allows manual intervention in shard placement. Use sparingly — it overrides the allocator's decisions:

```http
POST /_cluster/reroute
{
  "commands": [
    {
      "move": {
        "index": "logs-2026.05",
        "shard": 2,
        "from_node": "data-hot-03",
        "to_node": "data-hot-05"
      }
    }
  ]
}

// Cancel an ongoing shard recovery
POST /_cluster/reroute
{
  "commands": [
    {
      "cancel": {
        "index": "logs-2026.05",
        "shard": 2,
        "node": "data-hot-05",
        "allow_primary": false
      }
    }
  ]
}

// Allocate an unassigned replica to a specific node
POST /_cluster/reroute
{
  "commands": [
    {
      "allocate_replica": {
        "index": "logs-2026.05",
        "shard": 0,
        "node": "data-warm-02"
      }
    }
  ]
}

// DANGEROUS: Allocate a stale primary (accepts potential data loss)
POST /_cluster/reroute
{
  "commands": [
    {
      "allocate_stale_primary": {
        "index": "critical-data",
        "shard": 1,
        "node": "data-hot-01",
        "accept_data_loss": true
      }
    }
  ]
}
```

### 1.6 Allocation Explain API

When shards remain unassigned, the allocation explain API reveals why:

```http
// Explain why a specific shard is unassigned
GET /_cluster/allocation/explain
{
  "index": "orders",
  "shard": 0,
  "primary": false
}

// Explain any unassigned shard (picks the first one)
GET /_cluster/allocation/explain

// Common explanation patterns:
// "decider": "same_shard" — replica cannot go on same node as primary
// "decider": "disk_threshold" — all nodes exceed disk watermark
// "decider": "filter" — allocation filters exclude all eligible nodes
// "decider": "awareness" — not enough zones for replica distribution
```

The response includes a detailed breakdown of every decider's decision, making it the primary diagnostic tool for allocation problems.

---

## 2. Allocation Awareness and Forced Awareness

### 2.1 Basic Allocation Awareness

Allocation awareness distributes replica shards across different failure domains (availability zones, racks, data centers). Without it, a primary and its replica might land in the same zone — losing that zone means losing both copies.

```yaml
# elasticsearch.yml — each node declares its zone
node.attr.zone: eu-south-1a
```

```http
// Cluster-level awareness configuration
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.awareness.attributes": "zone"
  }
}
```

With this setting, Elasticsearch distributes replicas so that each copy of a shard lives in a different zone. For an index with 1 primary + 1 replica across zones A and B, the primary goes to zone A and the replica to zone B (or vice versa).

### 2.2 Forced Awareness

Basic awareness has a subtle problem: if zone B goes offline, Elasticsearch might allocate zone B's replicas to zone A — overloading it. Forced awareness prevents this by refusing to allocate shards when it would violate the awareness constraint:

```http
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.awareness.attributes": "zone",
    "cluster.routing.allocation.awareness.force.zone.values": "eu-south-1a,eu-south-1b,eu-south-1c"
  }
}
```

With forced awareness:
- Replicas are NEVER placed in the same zone as the primary.
- If a zone is lost, its replicas remain UNASSIGNED rather than being allocated to surviving zones. The cluster goes yellow, not green, but surviving zones are not overloaded.
- When the zone recovers, replicas are allocated automatically.

### 2.3 Multi-Attribute Awareness

You can distribute across multiple dimensions simultaneously:

```yaml
# elasticsearch.yml
node.attr.zone: eu-south-1a
node.attr.rack: rack-2
```

```http
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.awareness.attributes": "zone,rack"
  }
}
```

With `zone,rack`, Elasticsearch first distributes across zones, then across racks within each zone. This provides two layers of fault tolerance.

### 2.4 Tier-Based Allocation (ES 7.10+)

Elasticsearch 7.10 introduced `_tier_preference`, a built-in allocation attribute for data tiers. Instead of custom `box_type` attributes, indices can declare which tier they prefer:

```http
PUT /logs-2026.05/_settings
{
  "index": {
    "routing.allocation.include._tier_preference": "data_hot,data_warm"
  }
}
```

The `_tier_preference` is an ordered list: the index prefers `data_hot`, but falls back to `data_warm` if no hot nodes are available. ILM uses this automatically when moving indices between phases.

### 2.5 Real-World Zone Architecture

A typical three-zone deployment on AWS:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Elasticsearch Cluster                       │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐│
│  │   eu-south-1a    │  │   eu-south-1b    │  │  eu-south-1c   ││
│  │                  │  │                  │  │                ││
│  │  master-01       │  │  master-02       │  │  master-03     ││
│  │  data-hot-01     │  │  data-hot-02     │  │  data-hot-03   ││
│  │  data-warm-01    │  │  data-warm-02    │  │  data-warm-03  ││
│  │  coord-01        │  │  coord-02        │  │  coord-03      ││
│  └──────────────────┘  └──────────────────┘  └────────────────┘│
│                                                                 │
│  Index: logs-2026.05 (3 primaries, 1 replica each)             │
│  P0 → 1a, R0 → 1b   |  P1 → 1b, R1 → 1c  |  P2 → 1c, R2 → 1a│
└─────────────────────────────────────────────────────────────────┘
```

With forced awareness on zone, losing any single AZ leaves the cluster with all primaries available (promoted from replicas if needed) and the lost replicas unassigned (yellow state). No data loss, service continues.

---

## 3. Index Lifecycle Management (ILM)

### 3.1 ILM Phases

ILM manages the lifecycle of an index through five phases, each with specific actions:

| Phase | Typical Storage | Purpose | Common Actions |
|-------|----------------|---------|----------------|
| Hot | NVMe SSD | Active writes and frequent searches | rollover, set_priority, readonly |
| Warm | Standard SSD | No writes, moderate search frequency | shrink, forcemerge, allocate, set_priority |
| Cold | HDD or large SSD | Rare searches, long retention | allocate, set_priority, searchable_snapshot |
| Frozen | Object storage (S3/GCS) | Compliance/archival, very rare search | searchable_snapshot (shared_cache) |
| Delete | - | Data no longer needed | delete |

### 3.2 Complete ILM Policy

```http
PUT /_ilm/policy/production-logs
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_primary_shard_size": "50gb",
            "max_age": "7d",
            "max_docs": 500000000
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "7d",
        "actions": {
          "shrink": {
            "number_of_shards": 1
          },
          "forcemerge": {
            "max_num_segments": 1
          },
          "allocate": {
            "number_of_replicas": 1,
            "require": {
              "data": "warm"
            }
          },
          "set_priority": {
            "priority": 50
          }
        }
      },
      "cold": {
        "min_age": "30d",
        "actions": {
          "allocate": {
            "require": {
              "data": "cold"
            }
          },
          "set_priority": {
            "priority": 0
          },
          "readonly": {}
        }
      },
      "frozen": {
        "min_age": "90d",
        "actions": {
          "searchable_snapshot": {
            "snapshot_repository": "s3-archive",
            "force_merge_index": true
          }
        }
      },
      "delete": {
        "min_age": "365d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

### 3.3 ILM with Index Templates and Data Streams

```http
// Create component template for mappings
PUT /_component_template/logs-mappings
{
  "template": {
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "message": { "type": "text" },
        "level": { "type": "keyword" },
        "service": { "type": "keyword" },
        "host": { "type": "keyword" },
        "trace_id": { "type": "keyword" }
      }
    }
  }
}

// Create component template for settings
PUT /_component_template/logs-settings
{
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.lifecycle.name": "production-logs",
      "index.codec": "best_compression",
      "index.refresh_interval": "5s"
    }
  }
}

// Create index template that uses data streams
PUT /_index_template/logs
{
  "index_patterns": ["logs-*"],
  "data_stream": {},
  "composed_of": ["logs-mappings", "logs-settings"],
  "priority": 200,
  "_meta": {
    "description": "Template for application log data streams"
  }
}

// Indexing creates the data stream automatically
POST /logs-app-orders/_doc
{
  "@timestamp": "2026-05-22T14:30:00Z",
  "message": "Order created",
  "level": "INFO",
  "service": "order-api",
  "host": "pod-abc123"
}
```

### 3.4 ILM Rollover Mechanics

Rollover creates a new backing index when trigger conditions are met. The conditions are evaluated at every ILM poll interval (default 10 minutes):

```http
// Check ILM poll interval
GET /_cluster/settings?include_defaults&filter_path=defaults.indices.lifecycle.poll_interval

// Change poll interval (affects how quickly ILM responds to triggers)
PUT /_cluster/settings
{
  "persistent": {
    "indices.lifecycle.poll_interval": "5m"
  }
}
```

Rollover conditions are OR-ed: the rollover happens when ANY condition is met:

```http
"rollover": {
  "max_primary_shard_size": "50gb",   // any primary shard exceeds 50 GB
  "max_age": "7d",                     // index is older than 7 days
  "max_docs": 500000000,               // index has more than 500M documents
  "min_age": "1d",                     // minimum age before rollover (ES 8.4+)
  "min_primary_shard_size": "1gb",     // minimum size before rollover (ES 8.4+)
  "min_docs": 1                        // minimum docs before rollover (ES 8.4+)
}
```

### 3.5 Monitoring ILM Status

```http
// Check ILM status for all managed indices
GET /*/_ilm/explain?only_managed=true&filter_path=indices.*.index,indices.*.managed,indices.*.phase,indices.*.action,indices.*.step

// Check ILM errors
GET /*/_ilm/explain?only_errors=true

// Common ILM errors and resolutions:
// "step": "ERROR", "step_info.reason": "index.lifecycle.rollover_alias does not point to index"
//   → Alias was manually changed. Fix the alias or retry the step.

// Retry a failed ILM step
POST /logs-2026.05.20-000003/_ilm/retry

// Manually move an index to a specific ILM phase
POST /_ilm/move/logs-2026.05.20-000003
{
  "current_step": {
    "phase": "hot",
    "action": "rollover",
    "name": "check-rollover-ready"
  },
  "next_step": {
    "phase": "warm",
    "action": "shrink",
    "name": "shrink"
  }
}
```

### 3.6 ILM Best Practices

1. **Size-based rollover over time-based**: `max_primary_shard_size: 50gb` produces more uniform shard sizes than `max_age: 1d` (which varies with ingestion rate).

2. **Do not mix rollover conditions carelessly**: combining `max_age: 1d` with `max_primary_shard_size: 50gb` can create many tiny indices on days with low ingestion. Add `min_primary_shard_size` or `min_docs` guards.

3. **Forcemerge after writes stop**: The warm phase should include `forcemerge: { max_num_segments: 1 }` to consolidate segments. Never forcemerge indices that are still receiving writes.

4. **Set priority per phase**: Higher-priority indices recover first during cluster restarts. Hot=100, warm=50, cold=0 is a common scheme.

5. **Monitor ILM execution**: Check `GET /*/_ilm/explain?only_errors=true` regularly. ILM failures can silently block index transitions.

---

## 4. Hot-Warm-Cold-Frozen Architecture

### 4.1 Node Configuration per Tier

```yaml
# Hot node: maximum write throughput
# Hardware: NVMe SSD, high CPU, 64 GB RAM
node.roles: [data_hot, ingest]
node.attr.box_type: hot

# Warm node: read-heavy, no writes
# Hardware: Standard SSD, moderate CPU, 64 GB RAM
node.roles: [data_warm]
node.attr.box_type: warm

# Cold node: rare reads
# Hardware: HDD or large SSD, lower CPU, 32 GB RAM
node.roles: [data_cold]
node.attr.box_type: cold

# Frozen node: searchable snapshots from object storage
# Hardware: Minimal local SSD (cache), low CPU, 32 GB RAM
node.roles: [data_frozen]
node.attr.box_type: frozen
```

### 4.2 Tier-Aware Index Templates

The recommended approach in ES 8.x is to use `_tier_preference` instead of custom `box_type` attributes:

```http
PUT /_index_template/metrics-template
{
  "index_patterns": ["metrics-*"],
  "data_stream": {},
  "template": {
    "settings": {
      "index.lifecycle.name": "metrics-ilm",
      "index.routing.allocation.include._tier_preference": "data_hot"
    }
  }
}
```

ILM automatically adjusts `_tier_preference` as the index moves through phases. No manual allocation filter changes needed.

### 4.3 Searchable Snapshots (Frozen Tier)

Searchable snapshots allow searching data stored in object storage (S3, GCS, Azure Blob) without fully restoring it. Two modes exist:

| Mode | `storage` Parameter | Local Cache | Latency | Cost |
|------|---------------------|-------------|---------|------|
| Full copy | `full_copy` | Full index on local disk | Same as cold tier | Moderate |
| Shared cache | `shared_cache` | Partial, LRU cache on local SSD | Higher (remote reads) | Lowest |

```http
// Register a snapshot repository
PUT /_snapshot/s3-archive
{
  "type": "s3",
  "settings": {
    "bucket": "es-snapshots-prod",
    "region": "eu-south-1",
    "base_path": "elasticsearch",
    "max_restore_bytes_per_sec": "200mb",
    "max_snapshot_bytes_per_sec": "200mb"
  }
}

// Take a snapshot
PUT /_snapshot/s3-archive/snap-2026-05-22?wait_for_completion=false
{
  "indices": "logs-2026.02*,logs-2026.03*",
  "include_global_state": false
}

// Mount as a searchable snapshot (shared_cache = true frozen tier)
POST /_snapshot/s3-archive/snap-2026-05-22/_mount?storage=shared_cache
{
  "index": "logs-2026.02.01-000001",
  "renamed_index": "restored-logs-2026.02.01"
}

// Configure the shared cache on frozen nodes
// elasticsearch.yml
xpack.searchable.snapshot.shared_cache.size: 90%
xpack.searchable.snapshot.shared_cache.size.max_headroom: 100gb
```

### 4.4 Data Tier Capacity Planning

A capacity planning model for a 4-tier architecture:

```
Given:
  - Ingestion rate: 500 GB/day raw
  - Retention: 365 days
  - Hot retention: 7 days
  - Warm retention: 23 days (total 30 days hot+warm)
  - Cold retention: 60 days (total 90 days)
  - Frozen retention: 275 days (total 365 days)
  - Compression in warm/cold: 30% savings (forcemerge + codec)
  - Compression in frozen: object storage, no local disk needed

Hot tier:
  7 days * 500 GB = 3,500 GB raw + 1 replica = 7,000 GB
  Nodes: 4 x 2 TB NVMe (1.4 TB usable at 70% watermark)

Warm tier:
  23 days * 500 GB * 0.7 (compression) = 8,050 GB + 1 replica = 16,100 GB
  Nodes: 6 x 4 TB SSD

Cold tier:
  60 days * 500 GB * 0.7 = 21,000 GB + 0 replicas = 21,000 GB
  Nodes: 4 x 8 TB HDD

Frozen tier:
  275 days * 500 GB in S3 = 137,500 GB (S3 Standard or IA)
  Frozen nodes: 2 x 500 GB local SSD cache
```

### 4.5 Index Sorting for Better Compression

Sorting documents within an index improves compression in warm/cold phases by grouping similar values together:

```http
PUT /logs-template
{
  "settings": {
    "index.sort.field": ["service", "@timestamp"],
    "index.sort.order": ["asc", "desc"]
  },
  "mappings": {
    "properties": {
      "service": { "type": "keyword" },
      "@timestamp": { "type": "date" }
    }
  }
}
```

Index sorting has trade-offs:
- **Benefit**: Better compression, faster conjunctive queries with early termination.
- **Cost**: Slower indexing (documents must be sorted during flush), higher merge cost.
- **Recommendation**: Use on warm/cold indices where writes have stopped. Do not use on hot indices with high write throughput.

---

## 5. Shrink, Split, and Clone API

### 5.1 Shrink API: Reducing Shard Count

Shrink creates a new index with fewer primary shards. The target shard count must be a factor of the source shard count (e.g., 12 can shrink to 6, 4, 3, 2, or 1).

Prerequisites:
1. The index must be read-only.
2. All primary shards must be relocated to a single node.
3. The target node must have enough disk space for the entire index.

```http
// Step 1: Block writes and relocate to a single node
PUT /logs-2026.04-000001/_settings
{
  "settings": {
    "index.blocks.write": true,
    "index.routing.allocation.require._name": "data-warm-01"
  }
}

// Step 2: Wait for relocation to complete
GET /_cat/shards/logs-2026.04-000001?v&h=index,shard,prirep,state,node

// Step 3: Shrink from 6 shards to 1
POST /logs-2026.04-000001/_shrink/logs-2026.04-shrunk
{
  "settings": {
    "index.number_of_shards": 1,
    "index.number_of_replicas": 1,
    "index.blocks.write": null,
    "index.routing.allocation.require._name": null,
    "index.codec": "best_compression"
  },
  "aliases": {
    "logs-2026.04": {}
  }
}

// Step 4: Verify the shrunk index
GET /_cat/indices/logs-2026.04*?v&h=index,health,pri,rep,docs.count,store.size
```

### 5.2 Split API: Increasing Shard Count

Split creates a new index with more primary shards. The target shard count must be a multiple of the source (e.g., 2 can split to 4, 6, 8, etc.).

```http
// Step 1: Set index to read-only and ensure number_of_routing_shards allows the split
PUT /products/_settings
{
  "index.blocks.write": true
}

// Step 2: Split from 2 shards to 6
POST /products/_split/products-split
{
  "settings": {
    "index.number_of_shards": 6,
    "index.blocks.write": null
  }
}
```

The split operation works by using hash-based routing to redistribute documents. It is faster than reindex because it does not re-parse or re-analyze documents.

### 5.3 Clone API: Exact Copy

Clone creates an identical copy of an index (same shard count, same data):

```http
PUT /source-index/_settings
{ "index.blocks.write": true }

POST /source-index/_clone/cloned-index
{
  "settings": {
    "index.blocks.write": null,
    "index.number_of_replicas": 0
  }
}
```

Clone is useful for testing schema changes, creating staging copies, or snapshot-before-mutation workflows.

### 5.4 Comparison Table

| Operation | Input Shards | Output Shards | Constraint | Use Case |
|-----------|-------------|---------------|------------|----------|
| Shrink | N | Factor of N | All primaries on one node | ILM warm phase, consolidation |
| Split | N | Multiple of N | Read-only source | Scaling out a growing index |
| Clone | N | N (identical) | Read-only source | Testing, staging copies |
| Reindex | N | Any M | None | Schema change, cross-cluster migration |

---

## 6. Cross-Cluster Replication (CCR)

### 6.1 Architecture and Use Cases

CCR replicates indices from a **leader cluster** to one or more **follower clusters**. Replication is asynchronous and operation-based: the follower reads the leader's translog and replays operations locally.

Primary use cases:
- **Disaster recovery**: a follower in a second region provides a hot standby.
- **Geo-proximity**: replicate data close to users for lower-latency search.
- **Centralized reporting**: multiple edge clusters replicate to a central analytics cluster.
- **Data separation**: replicate production data to a staging/dev cluster without impacting production.

### 6.2 Setting Up CCR

```http
// On the FOLLOWER cluster: register the leader cluster
PUT /_cluster/settings
{
  "persistent": {
    "cluster.remote.leader-dc": {
      "seeds": ["leader-node-1:9300", "leader-node-2:9300"],
      "transport.compress": true,
      "skip_unavailable": false
    }
  }
}

// Verify connectivity
GET /_remote/info

// Create a follower index
PUT /orders-follower/_ccr/follow
{
  "remote_cluster": "leader-dc",
  "leader_index": "orders",
  "settings": {
    "index.number_of_replicas": 0
  },
  "max_read_request_operation_count": 5120,
  "max_outstanding_read_requests": 12,
  "max_read_request_size": "32mb",
  "max_write_request_operation_count": 5120,
  "max_write_buffer_count": 512,
  "max_write_buffer_size": "512mb",
  "max_retry_delay": "500ms",
  "read_poll_timeout": "1m"
}
```

### 6.3 Auto-Follow Patterns

Auto-follow automatically creates follower indices for new indices on the leader that match a pattern:

```http
PUT /_ccr/auto_follow/logs-pattern
{
  "remote_cluster": "leader-dc",
  "leader_index_patterns": ["logs-*"],
  "leader_index_exclusion_patterns": ["logs-debug-*"],
  "follow_index_pattern": "{{leader_index}}-replica",
  "settings": {
    "index.number_of_replicas": 1
  },
  "max_read_request_operation_count": 5120
}

// List auto-follow patterns
GET /_ccr/auto_follow

// Check auto-follow stats
GET /_ccr/stats
```

### 6.4 CCR Monitoring and Operations

```http
// Check replication status of a follower index
GET /orders-follower/_ccr/stats

// Key metrics in the response:
// "leader_global_checkpoint": 12345    — leader's latest checkpoint
// "follower_global_checkpoint": 12340  — follower's latest checkpoint
// "operations_written": 12340         — operations replicated
// "total_read_time_millis": 5000      — time spent reading from leader
// Lag = leader_global_checkpoint - follower_global_checkpoint

// Pause replication (for maintenance)
POST /orders-follower/_ccr/pause_follow

// Resume replication
POST /orders-follower/_ccr/resume_follow
{
  "max_read_request_operation_count": 5120
}

// Unfollow (convert follower to a regular index)
POST /orders-follower/_ccr/unfollow
// Prerequisites: must pause first, then close the index
```

### 6.5 CCR Failover Procedure

When the leader cluster fails, promote the follower:

```http
// Step 1: Pause replication (if not already paused due to leader failure)
POST /orders-follower/_ccr/pause_follow

// Step 2: Close the follower index
POST /orders-follower/_close

// Step 3: Unfollow — converts to a regular read-write index
POST /orders-follower/_ccr/unfollow

// Step 4: Open the index
POST /orders-follower/_open

// Step 5: Point applications to the follower cluster
// Step 6: After the leader recovers, reverse the replication direction
```

### 6.6 Bi-Directional Replication

True bi-directional replication (active-active) is not supported by CCR. Each index can have only one writer. The common workaround for multi-region writes:

1. Use index-per-region on each cluster (e.g., `orders-eu`, `orders-us`).
2. Replicate each region's index to the other cluster via CCR.
3. Search across both local and replicated indices using aliases or CCS.

---

## 7. Cross-Cluster Search (CCS)

### 7.1 CCS Architecture

Cross-cluster search lets a single query span multiple clusters. Unlike CCR, CCS does not replicate data — it sends the query to remote clusters at search time.

```http
// Register remote clusters
PUT /_cluster/settings
{
  "persistent": {
    "cluster.remote.cluster-us": {
      "seeds": ["us-node-1:9300", "us-node-2:9300"],
      "skip_unavailable": true
    },
    "cluster.remote.cluster-eu": {
      "seeds": ["eu-node-1:9300"],
      "skip_unavailable": true
    }
  }
}

// Search across local and remote clusters
GET /local-logs-*,cluster-us:logs-*,cluster-eu:logs-*/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "message": "error" } }
      ],
      "filter": [
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "size": 20,
  "sort": [{ "@timestamp": "desc" }]
}
```

### 7.2 CCS Minimization

CCS minimization (ES 7.12+) reduces the number of round trips between clusters by pushing filters and sorting to the remote side:

```http
PUT /_cluster/settings
{
  "persistent": {
    "cluster.remote.cluster-us.transport.compress": true,
    "search.allow_expensive_queries": true
  }
}

// CCS minimization is enabled by default in ES 8.x
// You can control it per-request:
GET /cluster-us:logs-*/_search?ccs_minimize_roundtrips=true
{
  "query": { "match_all": {} },
  "size": 10
}
```

### 7.3 CCS vs CCR: When to Use Which

| Aspect | CCS | CCR |
|--------|-----|-----|
| Data location | Data stays in source clusters | Data replicated to follower |
| Search latency | Higher (cross-network query) | Lower (local data) |
| Bandwidth | Per-query network cost | Per-write replication cost |
| Availability | Degrades if remote cluster is down | Independent of leader availability |
| Data freshness | Real-time | Replication lag (seconds to minutes) |
| Use case | Ad-hoc cross-cluster analytics | DR, geo-proximity reads |

---

## 8. Split-Brain Prevention

### 8.1 What Is Split-Brain

Split-brain occurs when a network partition divides a cluster into two subclusters, each electing its own master and accepting writes independently. When the partition heals, the two halves have divergent data that cannot be automatically merged. This is the most dangerous failure mode for a distributed system.

### 8.2 Zen2 Quorum-Based Prevention

Elasticsearch 7.x+ uses the Zen2 consensus protocol (based on Raft), which inherently prevents split-brain through quorum voting:

- A master election requires a **strict majority** of master-eligible nodes to vote.
- With 3 master-eligible nodes, the quorum is 2. A partition that isolates 1 node leaves the majority (2) intact — they elect a master. The isolated node cannot form a quorum alone and steps down.
- With 5 master-eligible nodes, the quorum is 3. Any partition must produce one group of 3+ and one of 2- — only the larger group can elect a master.

```
3 master-eligible nodes:
  Quorum = 2

  Partition: [A, B] | [C]
  → [A, B] has quorum, elects master
  → [C] alone, no quorum, steps down
  → No split-brain

5 master-eligible nodes:
  Quorum = 3

  Partition: [A, B, C] | [D, E]
  → [A, B, C] has quorum, elects master
  → [D, E] no quorum, step down
  → No split-brain
```

### 8.3 Why You Need an Odd Number of Master-Eligible Nodes

An even number provides no advantage over the next lower odd number:

- 2 nodes: quorum = 2. Losing one node means no quorum — cluster cannot elect a master. No better than 1 node for fault tolerance.
- 3 nodes: quorum = 2. Losing one node leaves quorum intact. **Tolerates 1 failure.**
- 4 nodes: quorum = 3. Losing one node leaves 3 — quorum intact. Losing two leaves 2 — no quorum. Still **tolerates only 1 failure**, same as 3 nodes, but with an extra node's cost.
- 5 nodes: quorum = 3. **Tolerates 2 failures.**

### 8.4 The `cluster.initial_master_nodes` Danger

`cluster.initial_master_nodes` bootstraps the cluster by telling nodes who the initial master-eligible members are. After the cluster forms, this setting is no longer used — but if left in `elasticsearch.yml` and a node is wiped and restarted, it may bootstrap a **new** single-node cluster, leading to a split-brain scenario.

```yaml
# REMOVE this setting after the cluster is bootstrapped:
# cluster.initial_master_nodes: ["master-01", "master-02", "master-03"]
#
# It should ONLY be present during the very first startup of a new cluster.
# After the cluster has formed, remove it from all elasticsearch.yml files.
```

### 8.5 Voting Configuration Exclusions

When decommissioning a master-eligible node, use voting exclusions to safely shrink the voting quorum:

```http
// Exclude a node from voting (before stopping it)
POST /_cluster/voting_config_exclusions?node_names=master-03

// After the node is stopped and removed, clear exclusions
DELETE /_cluster/voting_config_exclusions

// Check current voting configuration
GET /_cluster/state?filter_path=metadata.cluster_coordination
```

### 8.6 Network Partition Behavior

When a network partition occurs with Zen2:

1. **Minority side**: the master (if on this side) detects it lost quorum and steps down. Nodes on this side refuse writes and return 503 errors.
2. **Majority side**: if the master is on the minority side, the majority holds a new election. Normal operations resume within seconds.
3. **Partition heals**: the minority-side nodes rejoin the cluster. Their data is reconciled — any writes accepted during the partition (should be none on the minority side) are replayed from the primary shards.

---

## 9. Rolling Restarts and Upgrade Procedures

### 9.1 Rolling Restart Procedure

A rolling restart upgrades or reconfigures cluster nodes one at a time without downtime:

```http
// ========== FOR EACH NODE ==========

// Step 1: Disable shard allocation
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.enable": "primaries"
  }
}

// Step 2: Stop indexing if possible (for cleanest restart)
// This is optional for search-only periods

// Step 3: Perform a synced flush (ES < 8.0) or regular flush (ES 8.0+)
POST /_flush

// Step 4: Stop the node
// $ sudo systemctl stop elasticsearch

// Step 5: Make changes (config update, OS patch, JVM upgrade)
// ...

// Step 6: Start the node
// $ sudo systemctl start elasticsearch

// Step 7: Wait for the node to rejoin the cluster
GET /_cat/nodes?v&h=name,ip,node.role,master

// Step 8: Re-enable allocation
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.enable": "all"
  }
}

// Step 9: Wait for cluster to go green
GET /_cluster/health?wait_for_status=green&timeout=10m

// Step 10: Proceed to the next node
// ===================================
```

### 9.2 Node Restart Order

1. **Master-eligible nodes last**: start with data-only and coordinating nodes. Restart master-eligible nodes one at a time after all data nodes are updated.
2. **Non-voting nodes first**: if using voting-only nodes, restart those after data nodes but before full master nodes.
3. **Frozen/cold before hot**: lower-tier nodes serve less traffic and can tolerate brief unavailability.

### 9.3 Major Version Upgrades

Major version upgrades (7.x to 8.x) require additional preparation:

```http
// Step 1: Check deprecation log for breaking changes
GET /_migration/deprecations

// Step 2: Use the Kibana Upgrade Assistant
// Available at: Kibana > Management > Stack > Upgrade Assistant

// Step 3: Take a full cluster snapshot BEFORE upgrading
PUT /_snapshot/backup/pre-upgrade-snapshot?wait_for_completion=true
{
  "indices": "*",
  "include_global_state": true
}

// Step 4: Upgrade path check
// ES only supports rolling upgrade from one major to the next:
// 6.x → 7.x → 8.x (cannot skip 7.x)
// Within a major version: any minor → any higher minor
```

### 9.4 Rolling Upgrade from 7.17 to 8.x

```bash
# 1. Upgrade to the latest 7.17.x first (7.17 is the bridge version)
# 2. Resolve all deprecation warnings
# 3. Check the Upgrade Assistant

# 4. For each node (data nodes first, then master-eligible):
sudo systemctl stop elasticsearch

# 5. Install the new version
sudo dpkg -i elasticsearch-8.x.y-amd64.deb    # Debian/Ubuntu
# or
sudo rpm -Uvh elasticsearch-8.x.y-x86_64.rpm  # RHEL/CentOS

# 6. Review config changes (security is now enabled by default in 8.x)
# 7. Start the node
sudo systemctl start elasticsearch

# 8. Wait for the node to join and cluster to stabilize before next node
```

---

## 10. Troubleshooting

### 10.1 Shards Stuck in UNASSIGNED State

**Symptom**: `GET /_cat/shards` shows shards in UNASSIGNED state for extended periods.

```http
// Find unassigned shards
GET /_cat/shards?v&h=index,shard,prirep,state,unassigned.reason&s=state:desc

// Get detailed allocation explanation
GET /_cluster/allocation/explain
{
  "index": "problematic-index",
  "shard": 0,
  "primary": true
}
```

Common causes:

| Unassigned Reason | Meaning | Fix |
|-------------------|---------|-----|
| `INDEX_CREATED` | Index just created, shards being allocated | Wait; if persistent, check allocation filters |
| `CLUSTER_RECOVERED` | Cluster restarted, recovering shards | Wait for recovery to complete |
| `NODE_LEFT` | Node hosting the shard left the cluster | Wait for delayed allocation or add nodes |
| `ALLOCATION_FAILED` | Allocation attempted but failed | Check logs, may be corrupted shard |
| `REROUTE_CANCELLED` | Manual reroute was cancelled | Retry reroute or let allocator handle it |
| `REINITIALIZED` | Shard was reinitializing and failed | Check disk space and node health |

### 10.2 ILM Stuck in a Phase

```http
// Check ILM status
GET /stuck-index/_ilm/explain

// Common stuck states:
// "action": "shrink", "step": "ERROR"
//   → Shrink target already exists. Delete the target index and retry.

// "action": "rollover", "step": "check-rollover-ready"
//   → Rollover conditions not met. Check index stats.

// Retry the failed step
POST /stuck-index/_ilm/retry

// Force-move to the next phase (use with caution)
POST /_ilm/move/stuck-index
{
  "current_step": { "phase": "warm", "action": "shrink", "name": "ERROR" },
  "next_step": { "phase": "warm", "action": "forcemerge", "name": "forcemerge" }
}
```

### 10.3 CCR Follower Index Falling Behind

```http
// Check replication lag
GET /follower-index/_ccr/stats

// Look for:
// "operations_read" vs "operations_written" — gap indicates write backlog
// "time_since_last_read_millis" — high value indicates leader connectivity issues
// "fatal_exception" — replication has failed and needs manual intervention

// If follower is too far behind, it may need to be recreated:
POST /follower-index/_ccr/pause_follow
POST /follower-index/_close
POST /follower-index/_ccr/unfollow
DELETE /follower-index

// Re-create from scratch
PUT /follower-index/_ccr/follow
{
  "remote_cluster": "leader-dc",
  "leader_index": "orders"
}
```

### 10.4 Searchable Snapshot Mount Failures

```http
// Check mount status
GET /_cat/indices/.ds-restored*?v

// Common issues:
// - Snapshot repository not accessible: check S3/GCS credentials and network
// - Snapshot does not exist: verify with GET /_snapshot/repo-name/_all
// - License expired: searchable snapshots require Enterprise license
```

### 10.5 Cross-Cluster Search Timeout

```http
// Check remote cluster connectivity
GET /_remote/info

// Response includes:
// "connected": true/false
// "num_nodes_connected": N
// "initial_connect_timeout": "30s"

// If disconnected:
// 1. Check network connectivity between clusters (port 9300)
// 2. Check TLS certificates (must be signed by a trusted CA on both sides)
// 3. Check cluster name matches the configured remote name
// 4. Verify seed node addresses are correct and resolvable
```

### 10.6 Disk Watermarks Blocking Allocation

```http
// Check current watermark settings
GET /_cluster/settings?include_defaults&filter_path=defaults.cluster.routing.allocation.disk

// Default watermarks:
// low: 85% — new shards will not be allocated to nodes above this
// high: 90% — shards will be relocated away from nodes above this
// flood_stage: 95% — indices on this node become read-only

// Check node disk usage
GET /_cat/allocation?v&h=node,shards,disk.used,disk.avail,disk.percent

// Temporarily raise watermarks (emergency only)
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.allocation.disk.watermark.low": "90%",
    "cluster.routing.allocation.disk.watermark.high": "95%",
    "cluster.routing.allocation.disk.watermark.flood_stage": "97%"
  }
}

// Remove read-only blocks set by flood stage
PUT /*/_settings
{
  "index.blocks.read_only_allow_delete": null
}
```

---

## 11. FAQ

### Q1: How many replicas should I configure?

For most production workloads, 1 replica provides sufficient fault tolerance (survives loss of 1 node or 1 zone). Use 2 replicas for critical data that must survive simultaneous loss of 2 nodes. Use 0 replicas for transient or reproducible data (logs that can be re-ingested from Kafka). More replicas increase storage cost linearly and write latency (each write must wait for all in-sync replicas), but improve read throughput (searches distribute across more copies).

### Q2: What is the difference between `persistent` and `transient` cluster settings?

`persistent` settings survive cluster restarts — they are stored in the cluster state. `transient` settings are cleared on cluster restart. Use `persistent` for permanent configuration. Use `transient` for temporary overrides during maintenance (e.g., disabling allocation during a rolling restart, temporarily raising recovery speed).

### Q3: Can I change ILM policy on existing indices?

Yes. Changing the ILM policy affects existing indices that reference it. However, if an index has already completed a phase, it will not re-execute that phase under the new policy. It picks up the new policy at its current phase and moves forward. To apply a completely new lifecycle to an existing index, assign the new policy name in the index settings.

### Q4: How does CCR handle schema changes on the leader?

CCR replicates mapping changes automatically. When a new field is added to the leader index, the follower receives the mapping update. However, backward-incompatible mapping changes (changing a field type) are not supported — the follower will enter an error state. Always add fields; never change or remove them.

### Q5: What is the maximum number of shards per node?

The `cluster.max_shards_per_node` setting (default 1000 in ES 8.x) limits the total number of shards (primary + replica) that any single node can host. This is a safety limit to prevent cluster instability. If you hit this limit, the solution is not to raise it — it is to consolidate indices, reduce replicas, or add nodes.

### Q6: How do I migrate from time-based indices to data streams?

Data streams require an `@timestamp` field and append-only semantics. To migrate:
1. Create an index template with `"data_stream": {}` matching your index pattern.
2. Reindex existing indices into the data stream.
3. Update applications to index directly to the data stream name.
4. Delete old indices after verification.

### Q7: What happens if the ILM poll interval is too long?

The default poll interval is 10 minutes. With very high ingestion rates and aggressive rollover conditions, the index may exceed the target size significantly before ILM checks. Reduce the poll interval to 1-5 minutes for time-sensitive workloads. Note that very short intervals increase master node load.

### Q8: Can I use CCR across different Elasticsearch versions?

CCR requires the follower cluster to be at the same or higher minor version as the leader (within the same major version). Cross-major-version CCR is not supported. Upgrade the follower first, then the leader.

### Q9: How does tier-based allocation interact with ILM?

ILM automatically sets `_tier_preference` when moving indices between phases. When an index enters the warm phase, ILM sets `_tier_preference: data_warm,data_hot` (prefer warm, fall back to hot). The allocator then moves shards to warm nodes. You do not need to configure `box_type` allocation filters when using `_tier_preference`.

### Q10: What is shard over-allocation and how do I detect it?

Shard over-allocation occurs when the total number of shards across all indices exceeds the cluster's ability to manage them efficiently. Symptoms: slow cluster state updates, master node instability, high heap usage. Detect it with:

```http
GET /_cat/allocation?v&h=node,shards
GET /_cluster/stats?filter_path=indices.shards.total
```

If total shards exceed 20 * heap_gb across the cluster, consolidation is needed.

---

## 12. Exercises

### Exercise 1: Zone-Aware Deployment

Design a shard allocation strategy for a 3-zone deployment with the following requirements:
- 6 data nodes (2 per zone)
- 3 master-eligible nodes (1 per zone)
- Index with 3 primary shards and 1 replica each
- No data loss if an entire zone is lost

Write the `elasticsearch.yml` snippet for each node type and the cluster settings for forced awareness. Verify your design by listing every possible zone failure scenario and confirming that all primaries remain available.

### Exercise 2: ILM Policy Design

A logging pipeline ingests 200 GB/day. Requirements:
- Hot phase: fast search, up to 7 days or 50 GB per shard
- Warm phase: starts after 7 days, reduce to 1 shard, forcemerge to 1 segment
- Cold phase: starts after 30 days, move to cold tier, 0 replicas
- Delete after 90 days

Write the complete ILM policy, index template (with data stream), and calculate the storage requirements for each tier.

### Exercise 3: CCR Failover Drill

Set up a two-cluster CCR environment (leader and follower). Simulate a leader failure by stopping the leader cluster. Execute the failover procedure:
1. Pause replication
2. Unfollow the follower index
3. Write new documents to the promoted follower
4. After "recovering" the leader, set up reverse replication

Document each step with the exact API calls and expected responses.

### Exercise 4: Troubleshooting Unassigned Shards

Given the following cluster state:
- 5 data nodes across 2 zones
- Index with 3 primaries, 2 replicas each (9 total shards)
- Forced awareness on zone
- Zone A has 3 nodes, zone B has 2 nodes
- All 3 primaries and 3 replicas are assigned; 3 replicas are unassigned

Explain why the 3 replicas are unassigned. What allocation explain output would you expect? Propose two different solutions.

### Exercise 5: Capacity Planning

You are designing a hot-warm-cold architecture for a metrics pipeline:
- Ingestion: 500 GB/day of raw data
- Retention: 2 years
- Hot: 3 days
- Warm: 27 days
- Cold: 335 days (until deletion)
- Compression in warm: 40% reduction after forcemerge + best_compression
- Cold tier uses searchable snapshots (shared_cache) with 20% of data cached locally

Calculate:
1. Total storage needed per tier (including replicas: hot=1 replica, warm=1 replica, cold=0 replicas)
2. Number of nodes per tier (assuming 2 TB usable per hot/warm node, 10 TB per cold node)
3. Object storage size for cold tier
4. Estimated monthly cost on AWS (use current S3 and EC2 pricing)

### Exercise 6: Rolling Restart Automation

Write a bash script that performs a rolling restart across N nodes, using the Elasticsearch REST API to:
1. Disable allocation
2. Flush
3. Check node count before stopping
4. Wait for the node to rejoin after restart
5. Re-enable allocation
6. Wait for green status
7. Move to the next node

Include error handling for cases where the cluster does not go green within a timeout.

---

*Questo documento fa parte del modulo 08 "Elasticsearch" della Data Encyclopedia.*
