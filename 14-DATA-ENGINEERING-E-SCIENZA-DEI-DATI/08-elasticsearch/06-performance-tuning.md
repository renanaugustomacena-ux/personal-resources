# Performance Tuning di Elasticsearch

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Indice
1. JVM Heap Sizing and Memory Architecture
2. Indexing Throughput Optimization
3. Search Performance Optimization
4. Thread Pools and Queue Management
5. Shard Sizing Best Practices
6. Slow Log Analysis
7. Force Merge and Segment Management
8. Profiling and Diagnostics
9. OS-Level Tuning
10. Troubleshooting
11. FAQ
12. Exercises

---

## 1. JVM Heap Sizing and Memory Architecture

### 1.1 The 50% Rule and Compressed Oops

Elasticsearch runs on the JVM, and heap sizing is the single most impactful performance configuration. The fundamental rule: **allocate 50% of system RAM to the JVM heap, with a maximum of 31 GB** (not 32 GB — the compressed ordinary object pointers threshold is slightly below 32 GB on most JVMs).

Why 50% and why the cap:
- The other 50% is for the **OS page cache**, which Lucene relies on heavily. Lucene memory-maps segment files (doc values, norms, term dictionary FSTs) via `mmap`. Without sufficient page cache, these reads hit disk on every access.
- Above ~31.5 GB (varies by JVM and OS), the JVM cannot use **compressed ordinary object pointers (oops)**. Without compressed oops, every object reference expands from 4 bytes to 8 bytes, effectively wasting 30-40% of heap. A 32 GB heap without compressed oops has less usable memory than a 31 GB heap with compressed oops.

```bash
# jvm.options (Elasticsearch config directory)
-Xms31g
-Xmx31g

# IMPORTANT: -Xms and -Xmx must be equal to avoid heap resizing pauses
```

Verify compressed oops are active:

```http
GET /_nodes/jvm?filter_path=nodes.*.jvm.using_compressed_ordinary_object_pointers
```

### 1.2 Heap Sizing by Node Role

| Node Role | Heap Recommendation | Rationale |
|-----------|-------------------|-----------|
| Master-only | 4-8 GB | Cluster state management, no data |
| Data (hot) | 31 GB | Maximum for compressed oops |
| Data (warm/cold) | 16-31 GB | Less active, fewer aggregations |
| Coordinating-only | 16-31 GB | Aggregation reduction, merge operations |
| ML | 8-16 GB | ML jobs have their own memory management |
| Ingest | 8-16 GB | Pipeline processing is CPU-bound |

### 1.3 Off-Heap Memory: Lucene and the Page Cache

Elasticsearch's memory usage extends far beyond the JVM heap. Understanding off-heap memory is critical for capacity planning:

```
Total Memory Usage:
  JVM Heap (31 GB max)
    ├── Segment metadata (~10-20 KB per shard)
    ├── Field data cache (for text field sorting — avoid)
    ├── Query cache (filter results, 10% of heap by default)
    ├── Request cache (aggregation results per shard)
    ├── Indexing buffer (10% of heap by default)
    └── In-flight requests, thread stacks, etc.

  Off-Heap (the rest of system RAM)
    ├── OS page cache (Lucene segment files)
    │   ├── Term dictionary FSTs (memory-mapped)
    │   ├── Doc values (memory-mapped, columnar)
    │   ├── Norms (memory-mapped)
    │   ├── Points/BKD trees (memory-mapped)
    │   └── Stored fields (read on demand)
    ├── Direct buffers (Netty transport)
    ├── MMap regions for segment files
    └── OS overhead
```

On a 64 GB server with 31 GB heap:
- 31 GB heap for Elasticsearch JVM
- 33 GB for page cache + OS overhead
- The page cache will fill up with frequently accessed segment data, dramatically reducing disk reads

### 1.4 Garbage Collection Tuning

Elasticsearch 8.x uses G1GC by default. Key GC metrics to monitor:

```http
// GC statistics per node
GET /_nodes/stats/jvm?filter_path=nodes.*.jvm.gc.collectors

// Response shows:
// "young": { "collection_count": 1234, "collection_time_in_millis": 5000 }
// "old":   { "collection_count": 12,   "collection_time_in_millis": 3000 }
```

GC tuning parameters (modify only when diagnosing specific GC issues):

```bash
# jvm.options — G1GC tuning
-XX:+UseG1GC
-XX:G1HeapRegionSize=16m
-XX:InitiatingHeapOccupancyPercent=30
-XX:G1ReservePercent=25
-XX:MaxGCPauseMillis=200
```

GC health indicators:

| Metric | Healthy | Warning | Critical |
|--------|---------|---------|----------|
| Young GC frequency | < 20/sec | 20-50/sec | > 50/sec |
| Young GC duration | < 50ms avg | 50-200ms | > 200ms |
| Old GC frequency | < 1/hour | 1-5/hour | > 5/hour |
| Old GC duration | < 1s | 1-5s | > 5s |
| Heap after old GC | < 75% | 75-85% | > 85% |

### 1.5 Circuit Breakers

Circuit breakers prevent OutOfMemoryError by aborting operations that would exceed memory limits. Elasticsearch has multiple circuit breakers, each with a configurable limit:

```http
// View circuit breaker status
GET /_nodes/stats/breaker?human=true

// Configure circuit breakers
PUT /_cluster/settings
{
  "persistent": {
    "indices.breaker.total.limit": "70%",
    "indices.breaker.fielddata.limit": "40%",
    "indices.breaker.request.limit": "60%",
    "network.breaker.inflight_requests.limit": "100%",
    "indices.breaker.total.use_real_memory": true
  }
}
```

| Breaker | Default | Triggers When |
|---------|---------|---------------|
| `total` | 70% heap | Combined memory across all breakers exceeds limit |
| `fielddata` | 40% heap | Loading fielddata (text field aggregations) exceeds limit |
| `request` | 60% heap | A single request (aggregation, bulk response) exceeds limit |
| `inflight_requests` | 100% heap | In-flight HTTP requests exceed limit |
| `accounting` | 100% heap | Lucene segment memory overhead exceeds limit |

When a circuit breaker trips, the client receives a `CircuitBreakingException`. The solution is never to simply raise the limit — investigate what is consuming memory.

---

## 2. Indexing Throughput Optimization

### 2.1 Bulk API: The Only Way to Index

Single-document indexing creates a new translog entry, triggers a refresh timer, and incurs HTTP overhead for every document. The Bulk API amortizes this overhead across thousands of documents:

```python
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, parallel_bulk
import logging

es = Elasticsearch(
    "https://es-cluster:9200",
    basic_auth=("user", "password"),
    verify_certs=True,
    ca_certs="/path/to/ca.crt"
)

def generate_actions(records: list[dict]):
    for record in records:
        yield {
            "_index": "metrics-2026.05",
            "_source": record
        }

# Standard bulk — sequential, simpler error handling
success, errors = bulk(
    es,
    generate_actions(records),
    chunk_size=1000,
    max_chunk_bytes=15 * 1024 * 1024,  # 15 MB per batch
    request_timeout=60,
    raise_on_error=False,
    max_retries=3,
    initial_backoff=1,
    max_backoff=60
)
print(f"Indexed {success} documents, {len(errors)} failures")

# Parallel bulk — multiple threads, higher throughput
for ok, result in parallel_bulk(
    es,
    generate_actions(records),
    chunk_size=1000,
    thread_count=4,
    raise_on_error=False
):
    if not ok:
        logging.error(f"Failed to index: {result}")
```

### 2.2 Optimal Bulk Size

The optimal bulk size depends on document size, network latency, and node resources. There is no universal answer, but guidelines exist:

| Document Size | Recommended Chunk Size | Typical Batch Size |
|---------------|----------------------|-------------------|
| < 1 KB | 2000-5000 docs | 5-10 MB |
| 1-10 KB | 500-2000 docs | 5-15 MB |
| 10-100 KB | 100-500 docs | 10-20 MB |
| > 100 KB | 50-200 docs | 10-30 MB |

The target is 5-15 MB per bulk request. Beyond 30 MB, the response size can cause memory pressure and timeouts.

### 2.3 Indexing Settings for Bulk Ingestion

During initial data loading or reindexing, temporary settings dramatically improve throughput:

```http
// BEFORE bulk loading: optimize for write throughput
PUT /target-index/_settings
{
  "index": {
    "refresh_interval": "-1",
    "number_of_replicas": 0,
    "translog.durability": "async",
    "translog.sync_interval": "30s",
    "translog.flush_threshold_size": "2gb"
  }
}

// AFTER bulk loading: restore production settings
PUT /target-index/_settings
{
  "index": {
    "refresh_interval": "1s",
    "number_of_replicas": 1,
    "translog.durability": "request"
  }
}

// Force refresh to make all data searchable
POST /target-index/_refresh
```

Impact of each setting:

| Setting | Default | Bulk Value | Throughput Impact |
|---------|---------|-----------|-------------------|
| `refresh_interval` | 1s | -1 (disabled) | +30-50% |
| `number_of_replicas` | 1 | 0 | +50-100% |
| `translog.durability` | request | async | +20-30% |
| `translog.flush_threshold_size` | 512mb | 2gb | +10-15% |

Combined, these settings can improve bulk indexing throughput by 3-5x.

### 2.4 Indexing Pipeline Internals

Understanding the internal indexing pipeline helps diagnose bottlenecks:

```
Client → Coordinating Node → [Routing] → Primary Shard Node
                                          ↓
                                     [Ingest Pipeline]
                                          ↓
                                     [Analysis/Tokenization]
                                          ↓
                                     [Indexing Buffer]
                                          ↓
                                     [Translog Write]
                                          ↓
                                     [Refresh → New Segment]
                                          ↓
                                     [Replica Sync]
                                          ↓
                                     [Response to Client]
```

Bottleneck diagnosis:

```http
// Check indexing rate and latency per node
GET /_nodes/stats/indices/indexing?human=true

// Key metrics:
// "index_total": total docs indexed
// "index_time_in_millis": total time spent indexing
// "index_current": currently in-flight index operations
// "index_failed": failed index operations
// "throttle_time_in_millis": time throttled due to merge backpressure

// Check if merges are causing backpressure
GET /_nodes/stats/indices/merges?human=true

// "current": currently running merges
// "total_throttled_time_in_millis": time indexing was throttled for merges
```

### 2.5 Ingest Pipeline Optimization

Ingest pipelines run on the coordinating or ingest node before the document reaches the data node. Heavy pipelines (grok parsing, GeoIP lookups, enrich processors) can become bottlenecks:

```http
// Check ingest pipeline stats
GET /_nodes/stats/ingest?filter_path=nodes.*.ingest

// Optimize: use dedicated ingest nodes to offload parsing from data nodes
// elasticsearch.yml for ingest node:
// node.roles: [ingest]

// Reduce pipeline complexity when possible
PUT /_ingest/pipeline/optimized-log-pipeline
{
  "description": "Optimized log parsing pipeline",
  "processors": [
    {
      "dissect": {
        "field": "message",
        "pattern": "%{timestamp} %{level} [%{service}] %{msg}"
      }
    },
    {
      "date": {
        "field": "timestamp",
        "formats": ["ISO8601"],
        "target_field": "@timestamp"
      }
    },
    {
      "remove": {
        "field": ["timestamp", "message"],
        "ignore_missing": true
      }
    }
  ]
}
```

Prefer `dissect` over `grok` when the log format is fixed — dissect is 5-10x faster because it does not use regular expressions.

### 2.6 Mapping Optimization for Indexing

```http
PUT /optimized-index
{
  "mappings": {
    "dynamic": "strict",
    "properties": {
      "@timestamp": { "type": "date" },
      "message": {
        "type": "text",
        "norms": false,
        "index_options": "docs"
      },
      "level": {
        "type": "keyword",
        "doc_values": true,
        "eager_global_ordinals": false
      },
      "trace_id": {
        "type": "keyword",
        "doc_values": false
      },
      "payload": {
        "type": "object",
        "enabled": false
      }
    }
  },
  "settings": {
    "index.mapping.total_fields.limit": 200,
    "index.mapping.depth.limit": 5
  }
}
```

Mapping optimizations:

| Optimization | Saves | Trade-off |
|-------------|-------|-----------|
| `dynamic: "strict"` | Prevents mapping explosion | New fields require explicit mapping |
| `norms: false` on text fields | ~1 byte per doc per field | Disables length normalization in scoring |
| `index_options: "docs"` | Positions/offsets storage | Disables phrase queries and highlighting |
| `doc_values: false` | Columnar storage | Disables sorting, aggregations, scripting on the field |
| `enabled: false` on objects | All indexing overhead | Field is stored in `_source` but not searchable |
| `_source.excludes` | Storage space | Excluded fields cannot be retrieved, reindexed, or highlighted |

---

## 3. Search Performance Optimization

### 3.1 Filter Context vs Query Context

The most impactful search optimization is using **filter context** for non-scoring clauses. Filters are cached and skip scoring, making them significantly faster:

```http
// BAD: everything in query context (all scored, nothing cached)
POST /logs/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "message": "error" } },
        { "term": { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  }
}

// GOOD: only scoring-relevant clauses in must; non-scoring in filter
POST /logs/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "message": "error" } }
      ],
      "filter": [
        { "term": { "level": "ERROR" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  }
}
```

Why filters are faster:
1. **No scoring**: the BM25 scoring function is not evaluated.
2. **Caching**: filter results are stored in the node query cache as bitsets. Subsequent queries with the same filter reuse the cached bitset.
3. **Bitset intersection**: multiple filters are combined using efficient bitwise AND operations.

### 3.2 Node Query Cache

The node query cache stores filter results per segment. It is shared across all indices on a node:

```http
// Check query cache stats
GET /_nodes/stats/indices/query_cache?human=true

// Key metrics:
// "memory_size": current cache size
// "total_count": total queries cached
// "hit_count": cache hits
// "miss_count": cache misses
// "evictions": entries evicted due to size limit

// Hit rate = hit_count / (hit_count + miss_count) — target > 80%

// Configure cache size
PUT /_cluster/settings
{
  "persistent": {
    "indices.queries.cache.size": "15%"
  }
}

// Disable query cache for specific indices (high-churn data where caching is wasted)
PUT /ephemeral-data/_settings
{
  "index.queries.cache.enabled": false
}
```

### 3.3 Request Cache

The request cache stores the full results of search requests at the shard level. It is most effective for repeated aggregation queries on indices that do not change frequently:

```http
// Enable request cache per query
POST /metrics/_search?request_cache=true
{
  "size": 0,
  "aggs": {
    "hourly_avg": {
      "date_histogram": {
        "field": "@timestamp",
        "fixed_interval": "1h"
      },
      "aggs": {
        "avg_value": { "avg": { "field": "value" } }
      }
    }
  }
}

// Check request cache stats
GET /_nodes/stats/indices/request_cache?human=true

// The request cache is invalidated when any shard in the index refreshes.
// For time-series indices with constant writes, the request cache is less effective.
// For rolled-over (read-only) indices, it is highly effective.
```

### 3.4 Shard Request Cache vs Node Query Cache

| Feature | Node Query Cache | Request Cache |
|---------|-----------------|---------------|
| Scope | Per segment, per node | Per shard, per index |
| Caches what | Individual filter clause results (bitsets) | Full search response for a shard |
| Invalidation | Segment merge/delete | Any refresh on the shard |
| Best for | Repeated filter clauses across different queries | Identical repeated queries on stable data |
| Size default | 10% of heap | 1% of heap |

### 3.5 Doc Values vs Fielddata

Doc values are the columnar, on-disk data structure used for sorting, aggregations, and scripting. They are enabled by default on all field types except `text`:

```http
// WRONG: enabling fielddata on text fields loads entire inverted index into heap
PUT /bad-mapping/_mapping
{
  "properties": {
    "title": {
      "type": "text",
      "fielddata": true
    }
  }
}

// CORRECT: use a keyword sub-field for aggregation/sorting
PUT /good-mapping/_mapping
{
  "properties": {
    "title": {
      "type": "text",
      "fields": {
        "keyword": {
          "type": "keyword",
          "ignore_above": 256
        }
      }
    }
  }
}

// Aggregate on the keyword sub-field
POST /good-mapping/_search
{
  "size": 0,
  "aggs": {
    "top_titles": {
      "terms": {
        "field": "title.keyword",
        "size": 10
      }
    }
  }
}
```

### 3.6 Search Routing and Preference

Search routing reduces the scatter-gather overhead by targeting specific shards:

```http
// Route search to a specific shard (custom routing)
GET /orders/_search?routing=customer-abc
{
  "query": { "term": { "customer_id": "customer-abc" } }
}

// Use _preference for consistent shard assignment across retries
GET /orders/_search?preference=_local
// _local: prefer shards on the same node as the coordinating node
// _only_local: ONLY search local shards (fails if no local shards)
// _prefer_nodes:node1,node2: prefer specific nodes
// Custom string: hash-based consistent routing for session affinity

// Adaptive replica selection (default in ES 7+)
// Automatically routes to the replica with lowest latency
// No configuration needed — it is on by default
```

### 3.7 Aggregation Optimization

Aggregations are often the most expensive part of a query. Optimization strategies:

```http
// 1. Use filter aggregation to narrow the dataset before aggregating
POST /metrics/_search
{
  "size": 0,
  "aggs": {
    "recent_data": {
      "filter": {
        "range": { "@timestamp": { "gte": "now-1h" } }
      },
      "aggs": {
        "by_host": {
          "terms": { "field": "host", "size": 20 }
        }
      }
    }
  }
}

// 2. Limit cardinality: use size parameter on terms aggregation
// Do NOT set size to MAX_INT — it forces all unique values into memory
"terms": { "field": "user_id", "size": 100 }

// 3. Use composite aggregation for high-cardinality pagination
POST /logs/_search
{
  "size": 0,
  "aggs": {
    "all_services": {
      "composite": {
        "size": 1000,
        "sources": [
          { "service": { "terms": { "field": "service" } } },
          { "hour": { "date_histogram": { "field": "@timestamp", "fixed_interval": "1h" } } }
        ],
        "after": { "service": "order-api", "hour": 1716364800000 }
      }
    }
  }
}

// 4. Pre-compute with transforms for repeated expensive aggregations
PUT /_transform/daily_metrics
{
  "source": { "index": "raw-metrics-*" },
  "dest": { "index": "daily-metrics-summary" },
  "pivot": {
    "group_by": {
      "day": { "date_histogram": { "field": "@timestamp", "calendar_interval": "day" } },
      "host": { "terms": { "field": "host" } }
    },
    "aggregations": {
      "avg_cpu": { "avg": { "field": "cpu_percent" } },
      "max_memory": { "max": { "field": "memory_percent" } },
      "doc_count": { "value_count": { "field": "@timestamp" } }
    }
  },
  "frequency": "1h",
  "sync": { "time": { "field": "@timestamp", "delay": "5m" } }
}
```

### 3.8 Expensive Queries to Avoid

```http
// EXPENSIVE: wildcard at the beginning of a pattern
{ "wildcard": { "path": { "value": "*error*" } } }
// Alternative: use ngram tokenizer or reverse wildcard

// EXPENSIVE: regex on large text fields
{ "regexp": { "content": "error[0-9]{3}.*timeout" } }
// Alternative: use structured fields with keyword analysis

// EXPENSIVE: script scoring on every document
{
  "script_score": {
    "query": { "match_all": {} },
    "script": { "source": "Math.log(1 + doc['popularity'].value)" }
  }
}
// Alternative: store precomputed scores at index time

// EXPENSIVE: deeply nested aggregations
// Each level multiplies the number of buckets
// A 3-level agg with 100 buckets each = 1,000,000 leaf buckets

// Control expensive queries at the cluster level
PUT /_cluster/settings
{
  "persistent": {
    "search.allow_expensive_queries": false
  }
}
// This blocks: wildcard leading with *, regex, script queries, and joins
```

---

## 4. Thread Pools and Queue Management

### 4.1 Thread Pool Architecture

Elasticsearch uses dedicated thread pools for different operation types. Understanding and monitoring these pools is essential for diagnosing performance issues:

```http
// View thread pool stats across all nodes
GET /_cat/thread_pool?v&h=node_name,name,active,queue,rejected,completed,min,max,queue_size&s=rejected:desc

// Check specific thread pools
GET /_cat/thread_pool/write,search,search_throttled?v&h=node_name,name,active,queue,rejected
```

| Thread Pool | Purpose | Size Default | Queue Size Default |
|-------------|---------|-------------|-------------------|
| `write` | Index, update, delete, bulk operations | # of available processors | 10000 |
| `search` | Search queries (count and search phases) | `int((# of processors * 3) / 2) + 1` | 1000 |
| `search_throttled` | Search on throttled indices (frozen) | 1 | 100 |
| `get` | Get operations (by ID) | # of available processors | 1000 |
| `analyze` | Analyze API requests | 1 | 16 |
| `management` | Cluster management (cluster state, stats) | 5 | Unbounded |
| `flush` | Flush and translog operations | `max(1, # of processors / 2)` | Unbounded |
| `force_merge` | Force merge operations | `max(1, # of processors / 8)` | Unbounded |
| `snapshot` | Snapshot and restore operations | `max(1, # of processors / 2)` | Unbounded |

### 4.2 Thread Pool Rejections

Rejections occur when the queue for a thread pool is full. This means the node cannot accept new requests of that type:

```http
// Monitor rejections over time
GET /_nodes/stats/thread_pool?human=true&filter_path=nodes.*.thread_pool.write,nodes.*.thread_pool.search

// If write rejections are occurring:
// 1. Reduce bulk request rate or parallism from the client
// 2. Check if merges are causing backpressure (throttle_time > 0)
// 3. Check heap pressure (GC pauses block all threads)
// 4. Add more data nodes

// If search rejections are occurring:
// 1. Optimize query patterns (filter context, caching)
// 2. Reduce concurrent search requests
// 3. Add coordinating-only nodes for search distribution
// 4. Increase queue size as a temporary measure
```

### 4.3 Customizing Thread Pools

Thread pool settings are configured in `elasticsearch.yml` (not dynamic):

```yaml
# elasticsearch.yml — thread pool customization
thread_pool:
  write:
    size: 16
    queue_size: 20000
  search:
    size: 25
    queue_size: 2000
    min_queue_size: 1000
    max_queue_size: 3000
    auto_queue_frame_size: 2000
    target_response_time: 1s
```

The `search` thread pool uses adaptive queue sizing by default (ES 7+), adjusting its queue size based on observed response times. Override with caution.

---

## 5. Shard Sizing Best Practices

### 5.1 The Shard Sizing Formula

```
optimal_shard_count = MAX(
    CEIL(expected_data_size_gb / target_shard_size_gb),
    number_of_data_nodes
)

where target_shard_size_gb = 10-50 GB (30 GB sweet spot)
```

### 5.2 Shard Size Impact Matrix

| Shard Size | Search Latency | Indexing Throughput | Recovery Time | Merge Cost |
|------------|---------------|-------------------|---------------|------------|
| < 1 GB | Very fast per shard, but coordination overhead dominates | High per shard | Fast | Frequent small merges |
| 1-10 GB | Fast | Good | Moderate | Balanced |
| 10-50 GB | Moderate | Good | Moderate to slow | Balanced |
| 50-100 GB | Slow per shard | Good | Slow (long recovery) | Large, infrequent merges |
| > 100 GB | Very slow | Acceptable | Very slow | Very large, disruptive merges |

### 5.3 Shards Per Node Limits

```http
// Check current shard count per node
GET /_cat/allocation?v&h=node,shards,disk.used,disk.avail

// Check cluster-wide shard limit
GET /_cluster/settings?include_defaults&filter_path=defaults.cluster.max_shards_per_node

// Default is 1000 shards per node in ES 8.x
// Guideline: 20 shards per GB of JVM heap
// With 31 GB heap: max ~620 shards per node for good performance
```

### 5.4 Oversharding: Detection and Remediation

Oversharding is one of the most common production issues. Symptoms:
- High heap usage from shard metadata
- Slow cluster state updates
- Master node instability
- Poor search performance despite low query complexity

```http
// Detect oversharding
GET /_cluster/stats?filter_path=indices.shards.total,indices.count

// If total_shards / total_data_nodes > 600, you are likely oversharded

// Remediation strategies:
// 1. Shrink warm/cold indices (ILM shrink action)
// 2. Use data streams with rollover-by-size instead of daily indices
// 3. Increase target shard size in rollover conditions
// 4. Delete old indices more aggressively
// 5. Use index templates with fewer primary shards
```

### 5.5 Shard Sizing for Time-Series Data

Time-series indices with ILM should be sized by rollover conditions, not by shard count:

```http
// Rollover-based sizing (let ES manage shard count)
"rollover": {
  "max_primary_shard_size": "50gb",
  "max_age": "7d"
}

// Calculate: if ingestion is 100 GB/day with 3 primary shards:
// Each shard grows at ~33 GB/day
// At 50 GB max: rollover after ~1.5 days
// Result: ~5 backing indices per week, each with 3 shards = 15 shards/week
```

---

## 6. Slow Log Analysis

### 6.1 Configuring Slow Logs

Slow logs record queries and indexing operations that exceed configurable time thresholds:

```http
// Search slow log configuration
PUT /production-logs/_settings
{
  "index.search.slowlog.threshold.query.warn": "10s",
  "index.search.slowlog.threshold.query.info": "5s",
  "index.search.slowlog.threshold.query.debug": "2s",
  "index.search.slowlog.threshold.query.trace": "500ms",
  "index.search.slowlog.threshold.fetch.warn": "1s",
  "index.search.slowlog.threshold.fetch.info": "500ms",
  "index.search.slowlog.threshold.fetch.debug": "200ms",
  "index.search.slowlog.threshold.fetch.trace": "100ms",
  "index.search.slowlog.level": "info",
  "index.search.slowlog.source": "1000"
}

// Indexing slow log configuration
PUT /production-logs/_settings
{
  "index.indexing.slowlog.threshold.index.warn": "10s",
  "index.indexing.slowlog.threshold.index.info": "5s",
  "index.indexing.slowlog.threshold.index.debug": "2s",
  "index.indexing.slowlog.threshold.index.trace": "500ms",
  "index.indexing.slowlog.level": "info",
  "index.indexing.slowlog.source": "500"
}
```

### 6.2 Reading Slow Log Entries

Slow logs are written to `<cluster_name>_index_search_slowlog.json` and `<cluster_name>_index_indexing_slowlog.json`:

```json
{
  "type": "index_search_slowlog",
  "timestamp": "2026-05-22T14:30:15.123Z",
  "level": "WARN",
  "component": "i.s.s.query",
  "cluster.name": "production",
  "node.name": "data-hot-01",
  "message": "[production-logs][0]",
  "took": "12.5s",
  "took_millis": "12500",
  "total_hits": "45000",
  "stats": "[]",
  "search_type": "QUERY_THEN_FETCH",
  "total_shards": "15",
  "source": "{\"query\":{\"wildcard\":{\"path\":{\"value\":\"*error*\"}}}}"
}
```

Key fields for analysis:
- `took_millis`: actual execution time — the primary metric.
- `total_hits`: high hit counts suggest unselective queries.
- `total_shards`: many shards = high scatter-gather overhead.
- `source`: the actual query — look for wildcards, regex, script queries, and missing filters.

### 6.3 Slow Log Analysis Workflow

```bash
# Find the top 20 slowest queries in the last hour
cat /var/log/elasticsearch/production_index_search_slowlog.json | \
  python3 -c "
import sys, json
entries = []
for line in sys.stdin:
    try:
        entry = json.loads(line)
        entries.append(entry)
    except json.JSONDecodeError:
        pass
entries.sort(key=lambda e: int(e.get('took_millis', 0)), reverse=True)
for e in entries[:20]:
    print(f'{e.get(\"took\", \"?\")} | shards={e.get(\"total_shards\", \"?\")} | hits={e.get(\"total_hits\", \"?\")} | {e.get(\"source\", \"?\")[:100]}')
"
```

---

## 7. Force Merge and Segment Management

### 7.1 When to Force Merge

Force merge consolidates Lucene segments into fewer, larger segments. This improves search performance (fewer segments to scan) and reduces disk usage (deleted documents are physically removed).

**Rule: Never force merge indices that are still receiving writes.** Force merge is a blocking operation that competes with indexing for I/O and can cause thread pool rejections.

```http
// Force merge a read-only index to 1 segment
POST /logs-2026.04/_forcemerge?max_num_segments=1

// Only expunge deleted documents without reducing segment count
POST /active-index/_forcemerge?only_expunge_deletes=true

// Force merge with wait_for_completion=false (returns a task ID)
POST /large-index/_forcemerge?max_num_segments=1&wait_for_completion=false

// Monitor force merge progress
GET /_tasks?detailed=true&actions=*forcemerge*

// Monitor active merges across the cluster
GET /_cat/nodes?v&h=name,merges.current,merges.total,merges.current_size
```

### 7.2 Segment Count Impact on Search

```http
// Check segment count per shard
GET /_cat/segments/my-index?v&h=index,shard,segment,generation,docs.count,size,size.memory

// Rule of thumb:
// 1 segment per shard = optimal search performance (after force merge)
// 5-10 segments per shard = acceptable
// 50+ segments per shard = investigate refresh interval and merge policy
```

### 7.3 Merge Policy Tuning

The TieredMergePolicy controls background merge behavior:

```http
PUT /my-index/_settings
{
  "index": {
    "merge.policy.max_merged_segment": "5gb",
    "merge.policy.segments_per_tier": 10,
    "merge.policy.floor_segment": "2mb",
    "merge.policy.deletes_pct_allowed": 20,
    "merge.scheduler.max_thread_count": 1
  }
}
```

For spinning disks, set `max_thread_count: 1` to avoid concurrent merge I/O contention. For NVMe SSDs, the default (based on available cores) is appropriate.

---

## 8. Profiling and Diagnostics

### 8.1 Search Profiler

The Profile API reveals exactly where time is spent during query execution:

```http
POST /my-index/_search
{
  "profile": true,
  "query": {
    "bool": {
      "must": [
        { "match": { "content": "elasticsearch performance" } }
      ],
      "filter": [
        { "term": { "status": "published" } },
        { "range": { "@timestamp": { "gte": "now-7d" } } }
      ]
    }
  }
}
```

The profile output contains:

```json
{
  "profile": {
    "shards": [
      {
        "id": "[node-1][my-index][0]",
        "searches": [
          {
            "query": [
              {
                "type": "BooleanQuery",
                "description": "+content:elasticsearch +content:performance #status:published #@timestamp:[now-7d TO *]",
                "time_in_nanos": 5234000,
                "breakdown": {
                  "score": 2100000,
                  "build_scorer": 800000,
                  "advance": 1200000,
                  "match": 0,
                  "create_weight": 500000,
                  "next_doc": 600000,
                  "shallow_advance": 34000
                },
                "children": []
              }
            ],
            "collector": [
              {
                "name": "SimpleTopScoreDocCollector",
                "time_in_nanos": 1234000
              }
            ]
          }
        ],
        "aggregations": []
      }
    ]
  }
}
```

Key insights from the breakdown:
- `build_scorer` high → expensive scorer setup (complex query)
- `advance`/`next_doc` high → scanning many documents (unselective query)
- `score` high → scoring many documents (consider filters instead of queries)
- `create_weight` high → initializing internal data structures (many segments)

### 8.2 Hot Threads API

When a node is slow or unresponsive, the hot threads API shows what the JVM threads are doing:

```http
// Get hot threads from all nodes
GET /_nodes/hot_threads?threads=5&interval=500ms&type=cpu

// Get hot threads from a specific node
GET /_nodes/data-hot-01/hot_threads

// Output format (text, not JSON):
// ::: {data-hot-01}{xxxxxx}{...}{10.0.1.5}{10.0.1.5:9300}
//    60.2% CPU usage by thread 'elasticsearch[data-hot-01][search][T#3]'
//      10/10 snapshots sharing following 15 elements
//        at org.apache.lucene.search.BooleanScorer.score(BooleanScorer.java:...)
//        at org.elasticsearch.search.internal.ContextIndexSearcher.search(...)
//        ...
```

Common patterns:
- **`search` threads at 100%**: expensive queries consuming all CPU. Check slow logs.
- **`write` threads at 100%**: heavy indexing, likely with complex analyzers or pipelines.
- **`merge` threads dominating**: background merge activity competing with foreground operations.
- **`generic` threads waiting on locks**: potential contention in cluster state updates.

### 8.3 Task Management API

```http
// List all running tasks
GET /_tasks?detailed=true&actions=*search*

// List tasks grouped by node
GET /_tasks?group_by=nodes

// Cancel a long-running task
POST /_tasks/<task_id>/_cancel

// Cancel all search tasks taking longer than 30 seconds
POST /_tasks/_cancel?actions=*search*&nodes=data-hot-01
```

### 8.4 Diagnostic Dump

For offline analysis or support cases:

```http
// Cluster state dump
GET /_cluster/state?pretty > cluster_state.json

// All node stats
GET /_nodes/stats?human=true > node_stats.json

// All index stats
GET /_stats?human=true&level=shards > index_stats.json

// Cluster settings (including defaults)
GET /_cluster/settings?include_defaults&flat_settings > cluster_settings.json
```

---

## 9. OS-Level Tuning

### 9.1 Virtual Memory

Elasticsearch uses `mmap` extensively. The default `vm.max_map_count` is too low:

```bash
# Set permanently
echo "vm.max_map_count=262144" >> /etc/sysctl.conf
sysctl -p

# Verify
cat /proc/sys/vm/max_map_count
```

### 9.2 File Descriptors

Each shard requires many open file handles (one per segment file). The default 1024 is far too low:

```bash
# /etc/security/limits.conf
elasticsearch  soft  nofile  65535
elasticsearch  hard  nofile  65535

# Or for systemd:
# /etc/systemd/system/elasticsearch.service.d/override.conf
[Service]
LimitNOFILE=65535
```

```http
// Verify file descriptor settings
GET /_nodes/stats/process?filter_path=nodes.*.process.max_file_descriptors,nodes.*.process.open_file_descriptors
```

### 9.3 Swappiness

Swapping is catastrophic for Elasticsearch performance. Disable it:

```bash
# Option 1: Disable swap entirely (recommended)
sudo swapoff -a
# Remove swap entries from /etc/fstab

# Option 2: Set swappiness to minimum
echo "vm.swappiness=1" >> /etc/sysctl.conf
sysctl -p
```

```yaml
# elasticsearch.yml — memory lock (prevents swapping)
bootstrap.memory_lock: true
```

```http
// Verify memory lock is active
GET /_nodes?filter_path=nodes.*.process.mlockall
```

### 9.4 I/O Scheduler

For SSDs, use the `none` (or `noop`) I/O scheduler:

```bash
echo "none" > /sys/block/nvme0n1/queue/scheduler

# Make permanent via udev rules:
# /etc/udev/rules.d/60-scheduler.rules
ACTION=="add|change", KERNEL=="nvme*", ATTR{queue/scheduler}="none"
ACTION=="add|change", KERNEL=="sd*", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="none"
```

### 9.5 Transparent Huge Pages

Disable THP — it causes latency spikes due to background defragmentation:

```bash
echo "never" > /sys/kernel/mm/transparent_hugepage/enabled
echo "never" > /sys/kernel/mm/transparent_hugepage/defrag
```

---

## 10. Troubleshooting

### 10.1 High Indexing Latency

```http
// Step 1: Check bulk rejections
GET /_cat/thread_pool/write?v&h=node_name,active,queue,rejected

// Step 2: Check merge throttling
GET /_nodes/stats/indices/merges?human=true
// Look for "total_throttled_time_in_millis" > 0

// Step 3: Check GC pressure
GET /_nodes/stats/jvm?human=true
// Look for frequent old-gen collections

// Step 4: Check disk I/O
// Use `iostat -x 1` on the node to check %util and await

// Step 5: Check translog size
GET /my-index/_stats/translog?human=true
// Large uncommitted_operations suggest slow flushes
```

### 10.2 High Search Latency

```http
// Step 1: Profile the slow query
POST /my-index/_search
{
  "profile": true,
  "query": { ... }
}

// Step 2: Check segment count
GET /_cat/segments/my-index?v&h=index,shard,segment,docs.count,size
// >50 segments per shard → consider force merge or reduce refresh interval

// Step 3: Check cache hit rates
GET /_nodes/stats/indices/query_cache,request_cache?human=true

// Step 4: Check fielddata usage (should be near 0 if using doc_values)
GET /_nodes/stats/indices/fielddata?human=true

// Step 5: Check hot threads during slow query execution
GET /_nodes/hot_threads?threads=5&type=cpu
```

### 10.3 Memory Pressure and OOM

```http
// Immediate diagnostic
GET /_cat/nodes?v&h=name,heap.percent,heap.max,ram.percent,cpu

// Heap breakdown
GET /_nodes/stats/indices?human=true&filter_path=nodes.*.indices.segments.memory_in_bytes,nodes.*.indices.fielddata.memory_size_in_bytes,nodes.*.indices.query_cache.memory_size_in_bytes,nodes.*.indices.request_cache.memory_size_in_bytes

// If segments.memory is high:
// - Too many open shards/segments
// - Reduce shard count, force merge old indices

// If fielddata is high:
// - Text fields with fielddata enabled
// - Switch to keyword sub-fields
```

### 10.4 Cluster Going Yellow After Node Restart

This is often normal — replicas cannot be allocated on the same node as the primary. If your cluster has fewer nodes than `number_of_replicas + 1`, replicas will remain unassigned. Check with:

```http
GET /_cluster/allocation/explain
```

---

## 11. FAQ

### Q1: Should I use `_doc` or a custom type for documents?

In ES 7+, types are deprecated. Use `_doc` as the default type name. In ES 8+, types are fully removed. Just index documents without specifying a type.

### Q2: How do I benchmark Elasticsearch?

Use the official benchmarking tool `esrally` (Elastic Rally). It provides reproducible benchmarks with standardized tracks:

```bash
esrally race --track=geonames --target-hosts=es-node:9200 --pipeline=benchmark-only
```

### Q3: What is adaptive replica selection?

Adaptive replica selection (ARS) routes search requests to the replica copy with the lowest estimated response time, based on queue size, latency history, and node health. It is enabled by default in ES 7+ and replaces the older round-robin approach.

### Q4: When should I use `best_compression` codec?

The `best_compression` codec (DEFLATE) reduces stored field size by 15-25% compared to the default LZ4, at the cost of 10-20% higher indexing time and higher CPU during retrieval. Use it on warm/cold indices where writes have stopped and storage savings matter more than indexing speed.

### Q5: How do I handle high cardinality fields in aggregations?

For fields with millions of unique values (user IDs, session IDs):
1. Use `composite` aggregation with pagination instead of `terms` with large `size`.
2. Use `cardinality` aggregation (HyperLogLog approximation) instead of exact counts.
3. Pre-aggregate with transforms or rollup jobs.
4. Consider whether the aggregation is necessary — exact results for 10M+ unique values are inherently expensive.

### Q6: What is the impact of `_source` on performance?

`_source` stores the original JSON document. For large documents (>10 KB), it dominates storage size and fetch latency. Options:
- `_source.excludes`: exclude large fields from `_source`.
- `synthetic _source` (ES 8.4+): reconstruct `_source` from doc values at search time, eliminating stored field overhead.
- Disable `_source` only if you never need updates, reindex, or document retrieval.

### Q7: How many coordinating-only nodes do I need?

Coordinating nodes handle request routing, aggregation reduction, and result merging. Add dedicated coordinating nodes when:
- Search queries involve many shards (>50) and complex aggregations.
- Data nodes are CPU-bound with both indexing and searching.
- You need a stable entry point for load balancers.
A typical ratio is 1 coordinating node per 3-5 data nodes for search-heavy workloads.

### Q8: What is the impact of `refresh_interval` on search performance?

Increasing `refresh_interval` from 1s to 30s reduces the number of small segments created per time period, which means fewer segments to search and merge. On write-heavy indices where near-real-time search is not needed, `refresh_interval: 30s` can improve both indexing and search performance.

---

## 12. Exercises

### Exercise 1: Bulk Ingestion Benchmark

Index 10 million documents (each ~1 KB) into a 3-node cluster. Measure throughput (docs/sec) under four configurations:
1. Default settings (refresh=1s, replicas=1, translog=request)
2. Bulk-optimized settings (refresh=-1, replicas=0, translog=async)
3. Configuration 2 with parallel_bulk (4 threads)
4. Configuration 2 with parallel_bulk (8 threads)

Compare throughput and identify the bottleneck at each stage.

### Exercise 2: Query Optimization

Given this slow query, identify at least 3 optimization opportunities and rewrite it:

```json
{
  "query": {
    "bool": {
      "must": [
        { "wildcard": { "path": { "value": "*/api/v1/*" } } },
        { "range": { "@timestamp": { "gte": "now-24h" } } },
        { "term": { "status_code": 500 } },
        { "match_phrase": { "message": "connection timeout" } }
      ]
    }
  },
  "sort": [{ "@timestamp": "desc" }],
  "size": 100,
  "aggs": {
    "by_service": {
      "terms": { "field": "service.keyword", "size": 10000 }
    }
  }
}
```

### Exercise 3: Heap Sizing Calculation

A server has 128 GB RAM and will run a data node hosting 1500 shards (primary + replica) with an average of 30 GB per shard. The workload is 60% search, 40% indexing. Determine:
1. The optimal JVM heap size
2. The expected page cache size
3. Whether the shard count is within recommended limits
4. What changes you would recommend

### Exercise 4: Thread Pool Diagnosis

A cluster shows the following thread pool stats:

```
node    name    active  queue   rejected
node-1  write   16      9800    45230
node-1  search  24      50      0
node-2  write   16      9500    42100
node-2  search  24      100     0
```

Diagnose the problem. What are the most likely root causes? What immediate and long-term actions would you take?

### Exercise 5: Slow Log Investigation

Configure slow logs on an index with the following thresholds: warn=5s, info=2s, debug=1s. Run a series of queries (match, range, wildcard, aggregation) and analyze the slow log output. For each slow query:
1. Identify the bottleneck (query phase vs fetch phase)
2. Profile the query using the Profile API
3. Propose an optimization
4. Rerun and measure improvement

### Exercise 6: Force Merge Impact

On a test cluster, create an index with 5 million documents. Measure search latency before and after:
1. Natural state (many segments from continuous indexing)
2. After force merge to 5 segments
3. After force merge to 1 segment

Plot segment count vs. search latency. At what point does further merging stop providing meaningful improvement?

---

*Questo documento fa parte del modulo 08 "Elasticsearch" della Data Encyclopedia.*
