# Monitoring e Logging di Elasticsearch

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Indice
1. Cluster Health and the Health API
2. _cat APIs for Rapid Diagnostics
3. Node Stats and Index Stats
4. JVM and GC Monitoring
5. Thread Pool Monitoring
6. Circuit Breaker Monitoring
7. Slow Logs: Configuration and Analysis
8. Stack Monitoring with Metricbeat
9. Kibana Dashboards for Elasticsearch
10. Alerting: Watcher and Kibana Rules
11. Diagnostic Dump and Support
12. Key Metrics Reference
13. Troubleshooting
14. FAQ
15. Exercises

---

## 1. Cluster Health and the Health API

### 1.1 Cluster Health Endpoint

The cluster health API is the first diagnostic tool to check. It provides a single status indicator and summary counts:

```http
// Basic cluster health
GET /_cluster/health

// Response:
{
  "cluster_name": "production",
  "status": "green",
  "timed_out": false,
  "number_of_nodes": 12,
  "number_of_data_nodes": 8,
  "active_primary_shards": 450,
  "active_shards": 900,
  "relocating_shards": 0,
  "initializing_shards": 0,
  "unassigned_shards": 0,
  "delayed_unassigned_shards": 0,
  "number_of_pending_tasks": 0,
  "number_of_in_flight_fetch": 0,
  "task_max_waiting_in_queue_millis": 0,
  "active_shards_percent_as_number": 100.0
}
```

### 1.2 Status Meanings

| Status | Meaning | Action Required |
|--------|---------|-----------------|
| `green` | All primary and replica shards are assigned | None |
| `yellow` | All primaries assigned, some replicas unassigned | Investigate: may need more nodes or disk space |
| `red` | Some primary shards are unassigned | Immediate: data is unavailable for those indices |

### 1.3 Health API Variants

```http
// Wait for a specific status (blocks until condition met or timeout)
GET /_cluster/health?wait_for_status=green&timeout=60s

// Per-index health
GET /_cluster/health/logs-*?level=indices

// Per-shard health (most detailed)
GET /_cluster/health/logs-2026.05?level=shards

// Health of a specific index
GET /_cluster/health/critical-data
```

### 1.4 Health Indicators API (ES 8.7+)

The health indicators API provides detailed, structured diagnostics beyond the simple green/yellow/red status:

```http
GET /_health_report

// Response includes indicators like:
// "master_is_stable": { "status": "green", "symptom": "The cluster has a stable master node" }
// "shards_availability": { "status": "yellow", "symptom": "2 replica shards are not assigned" }
// "disk": { "status": "green", "symptom": "All nodes have sufficient disk space" }
// "ilm": { "status": "green" }
// "slm": { "status": "yellow", "symptom": "No snapshots have been taken recently" }

// Check a specific indicator
GET /_health_report/shards_availability
GET /_health_report/disk
GET /_health_report/master_is_stable
```

Each indicator provides:
- `status`: green/yellow/red
- `symptom`: human-readable description of the issue
- `diagnosis`: root cause analysis with specific affected resources
- `impacts`: what functionality is degraded
- `actions`: recommended remediation steps

---

## 2. _cat APIs for Rapid Diagnostics

### 2.1 Essential _cat Commands

The `_cat` APIs return data in compact text format, designed for terminal use:

```http
// Cluster health (one-line summary)
GET /_cat/health?v
// epoch    timestamp  cluster     status node.total node.data shards pri relo init unassign
// 1716379200 14:00:00 production  green    12        8        900   450   0    0      0

// List all indices sorted by size
GET /_cat/indices?v&s=store.size:desc&h=index,health,status,pri,rep,docs.count,store.size,pri.store.size
// index              health status pri rep docs.count store.size pri.store.size
// logs-2026.05.22    green  open     3   1   45000000   25.5gb       12.7gb
// metrics-2026.05.22 green  open     2   1   12000000    8.3gb        4.1gb

// Node resources
GET /_cat/nodes?v&h=name,ip,heap.percent,heap.max,ram.percent,cpu,load_1m,load_5m,disk.used_percent,node.role,master
// name         ip        heap.percent heap.max ram.percent cpu load_1m load_5m disk.used_percent node.role master
// data-hot-01  10.0.1.10          65    31gb          89  42   3.2     2.8              68        dhi       -
// es-master-01 10.0.1.20          22     8gb          45   5   0.5     0.3              12        m         *

// Shard allocation per node
GET /_cat/allocation?v&h=node,shards,disk.indices,disk.used,disk.avail,disk.total,disk.percent
// node         shards disk.indices disk.used disk.avail disk.total disk.percent
// data-hot-01     125       300gb     350gb     150gb      500gb           70
// data-hot-02     120       290gb     340gb     160gb      500gb           68

// Unassigned shards with reasons
GET /_cat/shards?v&h=index,shard,prirep,state,unassigned.reason,unassigned.at,unassigned.for&s=state:desc
// Useful when cluster is yellow or red

// Aliases
GET /_cat/aliases?v&h=alias,index,filter,routing.index,routing.search

// Running tasks
GET /_cat/tasks?v&detailed&actions=*merge*,*forcemerge*,*snapshot*,*reindex*

// Pending cluster tasks (master queue)
GET /_cat/pending_tasks?v

// Recovery progress
GET /_cat/recovery?v&h=index,shard,type,stage,files_recovered,files_total,bytes_recovered,bytes_total,time&active_only=true

// Thread pool status
GET /_cat/thread_pool?v&h=node_name,name,active,queue,rejected,completed&s=rejected:desc

// Segments per index
GET /_cat/segments/logs-*?v&h=index,shard,segment,generation,docs.count,docs.deleted,size,size.memory
```

### 2.2 _cat API Tips

```http
// Use help to see all available columns
GET /_cat/nodes?help

// Output as JSON instead of text
GET /_cat/nodes?format=json&pretty

// Sort by multiple columns
GET /_cat/indices?v&s=docs.count:desc,store.size:desc

// Filter with specific patterns
GET /_cat/indices/logs-2026.05*?v
```

---

## 3. Node Stats and Index Stats

### 3.1 Node Stats Deep Dive

The `_nodes/stats` API provides detailed per-node metrics:

```http
// All stats for all nodes
GET /_nodes/stats?human=true

// Specific stat categories
GET /_nodes/stats/jvm,os,fs,thread_pool,indices?human=true

// Stats for a specific node
GET /_nodes/data-hot-01/stats/jvm,indices?human=true

// Transport stats (inter-node communication)
GET /_nodes/stats/transport?human=true

// HTTP stats (client connections)
GET /_nodes/stats/http?human=true

// Process stats (file descriptors, CPU)
GET /_nodes/stats/process?human=true
```

### 3.2 Key Node Stats Paths

```http
// JVM heap and GC
GET /_nodes/stats/jvm?filter_path=nodes.*.jvm.mem,nodes.*.jvm.gc

// Response structure:
// nodes.<id>.jvm.mem.heap_used_in_bytes
// nodes.<id>.jvm.mem.heap_used_percent
// nodes.<id>.jvm.mem.heap_max_in_bytes
// nodes.<id>.jvm.mem.non_heap_used_in_bytes
// nodes.<id>.jvm.gc.collectors.young.collection_count
// nodes.<id>.jvm.gc.collectors.young.collection_time_in_millis
// nodes.<id>.jvm.gc.collectors.old.collection_count
// nodes.<id>.jvm.gc.collectors.old.collection_time_in_millis

// Indexing and search rates
GET /_nodes/stats/indices?filter_path=nodes.*.indices.indexing,nodes.*.indices.search

// nodes.<id>.indices.indexing.index_total            — total docs indexed
// nodes.<id>.indices.indexing.index_time_in_millis   — total indexing time
// nodes.<id>.indices.indexing.index_current          — in-flight indexing ops
// nodes.<id>.indices.indexing.throttle_time_in_millis — time throttled by merges
// nodes.<id>.indices.search.query_total              — total search queries
// nodes.<id>.indices.search.query_time_in_millis     — total search time
// nodes.<id>.indices.search.query_current            — in-flight searches
// nodes.<id>.indices.search.fetch_total              — total fetch phases
// nodes.<id>.indices.search.fetch_time_in_millis     — total fetch time

// OS stats (CPU, memory, load)
GET /_nodes/stats/os?filter_path=nodes.*.os.cpu,nodes.*.os.mem
```

### 3.3 Index-Level Stats

```http
// Stats for a specific index
GET /logs-2026.05/_stats?human=true

// Per-shard level stats
GET /logs-2026.05/_stats?human=true&level=shards

// Specific stat categories for an index
GET /logs-2026.05/_stats/indexing,search,store,merge,refresh,flush?human=true

// Key index stats:
// _all.primaries.indexing.index_total          — docs indexed on primaries
// _all.primaries.search.query_total            — search queries on primaries
// _all.primaries.store.size_in_bytes           — primary shard size
// _all.total.store.size_in_bytes               — total size (primaries + replicas)
// _all.primaries.merges.current                — active merges
// _all.primaries.refresh.total_time_in_millis  — time spent refreshing
```

### 3.4 Cluster-Level Stats

```http
// Cluster-wide aggregate stats
GET /_cluster/stats?human=true

// Key cluster stats:
// indices.count              — total number of indices
// indices.shards.total       — total shard count
// indices.docs.count         — total document count
// indices.store.size         — total storage
// nodes.count.total          — total nodes
// nodes.count.data           — data nodes
// nodes.count.master         — master-eligible nodes
// nodes.jvm.max_uptime       — longest node uptime
// nodes.fs.total_in_bytes    — total filesystem capacity
// nodes.fs.available_in_bytes — available filesystem space
```

---

## 4. JVM and GC Monitoring

### 4.1 Heap Usage Monitoring

```http
// Real-time heap usage per node
GET /_cat/nodes?v&h=name,heap.percent,heap.current,heap.max,ram.percent,cpu

// Detailed JVM memory pools
GET /_nodes/stats/jvm?filter_path=nodes.*.jvm.mem

// Response includes:
// "heap_used_in_bytes": 21474836480,
// "heap_used_percent": 67,
// "heap_committed_in_bytes": 33285996544,
// "heap_max_in_bytes": 33285996544,
// "non_heap_used_in_bytes": 285212672,
// "pools": {
//   "young": { "used_in_bytes": 536870912, "max_in_bytes": 0, "peak_used_in_bytes": ... },
//   "old":   { "used_in_bytes": 20937965568, "max_in_bytes": ... },
//   "survivor": { "used_in_bytes": 67108864, "max_in_bytes": ... }
// }
```

### 4.2 GC Metrics Interpretation

```http
// GC statistics
GET /_nodes/stats/jvm?filter_path=nodes.*.jvm.gc

// Response:
// "gc": {
//   "collectors": {
//     "young": {
//       "collection_count": 15234,
//       "collection_time_in_millis": 125000
//     },
//     "old": {
//       "collection_count": 12,
//       "collection_time_in_millis": 8500
//     }
//   }
// }
```

GC health assessment:

| Metric | Calculation | Healthy | Warning | Critical |
|--------|------------|---------|---------|----------|
| Young GC rate | Δ collection_count / Δ time | < 20/sec | 20-50/sec | > 50/sec |
| Young GC avg duration | Δ collection_time / Δ collection_count | < 50ms | 50-200ms | > 200ms |
| Old GC rate | Δ collection_count / Δ time | < 1/min | 1-10/min | > 10/min |
| Old GC avg duration | Δ collection_time / Δ collection_count | < 500ms | 0.5-5s | > 5s |
| Heap after GC | heap_used after old GC | < 70% | 70-85% | > 85% |
| GC overhead | GC time / wall time | < 5% | 5-10% | > 10% |

### 4.3 GC Log Analysis

GC logs are written to the Elasticsearch log directory. For G1GC (ES 8.x default):

```bash
# jvm.options — enable GC logging (already default in ES 8.x)
-Xlog:gc*,gc+age=trace,safepoint:file=/var/log/elasticsearch/gc.log:utctime,pid,tags:filecount=32,filesize=64m
```

Key GC log patterns to watch:

```
# Normal young GC (fast, frequent)
[gc] GC(1234) Pause Young (Normal) 20G->15G(31G) 25.5ms

# Full GC (concerning if frequent)
[gc] GC(1235) Pause Full (G1 Compaction Pause) 28G->18G(31G) 3500ms

# To-space exhaustion (critical — heap is nearly full)
[gc] GC(1236) To-space exhausted
```

### 4.4 Monitoring Script for GC Health

```bash
#!/bin/bash
# gc_health_check.sh — check GC metrics for all nodes
ES_URL="http://localhost:9200"

curl -s "$ES_URL/_nodes/stats/jvm?human=true" | \
python3 -c "
import sys, json

data = json.load(sys.stdin)
for node_id, node in data['nodes'].items():
    name = node['name']
    jvm = node['jvm']
    heap_pct = jvm['mem']['heap_used_percent']
    young_gc = jvm['gc']['collectors']['young']
    old_gc = jvm['gc']['collectors']['old']

    status = 'OK'
    if heap_pct > 85:
        status = 'CRITICAL'
    elif heap_pct > 75:
        status = 'WARNING'

    print(f'{status:10} {name:20} heap={heap_pct}% '
          f'young_gc_count={young_gc[\"collection_count\"]} '
          f'young_gc_time={young_gc[\"collection_time_in_millis\"]}ms '
          f'old_gc_count={old_gc[\"collection_count\"]} '
          f'old_gc_time={old_gc[\"collection_time_in_millis\"]}ms')
"
```

---

## 5. Thread Pool Monitoring

### 5.1 Thread Pool Overview

```http
// Comprehensive thread pool view
GET /_cat/thread_pool?v&h=node_name,name,active,queue,rejected,completed,min,max,queue_size&s=rejected:desc

// Focus on critical pools
GET /_cat/thread_pool/write,search,get,management?v&h=node_name,name,active,queue,rejected,completed
```

### 5.2 Thread Pool Health Indicators

| Pool | Healthy Queue | Warning Queue | Critical |
|------|--------------|---------------|----------|
| `write` | 0-100 | 100-5000 | > 5000 or any rejections |
| `search` | 0-50 | 50-500 | > 500 or any rejections |
| `get` | 0-10 | 10-100 | > 100 or any rejections |
| `management` | 0-5 | 5-20 | > 20 |

### 5.3 Rejection Analysis

```http
// Detailed thread pool stats via node stats API
GET /_nodes/stats/thread_pool?human=true

// Focus on rejection counts
GET /_nodes/stats/thread_pool?filter_path=nodes.*.thread_pool.*.rejected

// Common rejection causes and solutions:
//
// write rejections:
//   Cause: indexing rate exceeds node capacity
//   Solutions:
//   1. Reduce bulk request parallelism
//   2. Check for merge throttling (slow I/O)
//   3. Check GC pressure (heap too small)
//   4. Add more data nodes
//
// search rejections:
//   Cause: search request rate exceeds capacity
//   Solutions:
//   1. Optimize queries (use filters, reduce shard count)
//   2. Add coordinating-only nodes
//   3. Add more data nodes or replicas
//   4. Implement request queuing in the application
```

### 5.4 Thread Pool Trends Over Time

To track thread pool metrics over time, use Metricbeat or a periodic collection script:

```bash
#!/bin/bash
# Collect thread pool metrics every 10 seconds
while true; do
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  curl -s "http://localhost:9200/_cat/thread_pool/write,search?format=json" | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
for entry in data:
    print(f'$TIMESTAMP {entry[\"node_name\"]:20} {entry[\"name\"]:10} '
          f'active={entry[\"active\"]:3} queue={entry[\"queue\"]:5} '
          f'rejected={entry[\"rejected\"]:8} completed={entry[\"completed\"]}')
"
  sleep 10
done >> /var/log/es-thread-pool-metrics.log
```

---

## 6. Circuit Breaker Monitoring

### 6.1 Circuit Breaker Status

```http
// View all circuit breaker statuses
GET /_nodes/stats/breaker?human=true

// Response for each node:
// "breakers": {
//   "request": {
//     "limit_size_in_bytes": 19327352832,
//     "limit_size": "18gb",
//     "estimated_size_in_bytes": 1073741824,
//     "estimated_size": "1gb",
//     "overhead": 1.0,
//     "tripped": 0
//   },
//   "fielddata": {
//     "limit_size": "12.4gb",
//     "estimated_size": "0b",
//     "tripped": 0
//   },
//   "in_flight_requests": {
//     "limit_size": "31gb",
//     "estimated_size": "2mb",
//     "tripped": 0
//   },
//   "parent": {
//     "limit_size": "21.7gb",
//     "estimated_size": "12gb",
//     "tripped": 2
//   }
// }
```

### 6.2 Circuit Breaker Trip Analysis

When a circuit breaker trips, the client receives an error:

```json
{
  "error": {
    "type": "circuit_breaking_exception",
    "reason": "[parent] Data too large, data for [<request>] would be [22/31gb], which is larger than the limit of [21.7gb/31gb]",
    "bytes_wanted": 23622320128,
    "bytes_limit": 21474836480,
    "durability": "PERMANENT"
  },
  "status": 429
}
```

Root cause analysis by breaker:

| Breaker | Common Cause | Investigation |
|---------|-------------|---------------|
| `parent` | Combined memory pressure from multiple sources | Check all sub-breakers, identify the largest consumer |
| `fielddata` | Text fields with `fielddata: true` | Check `GET /_nodes/stats/indices/fielddata?fields=*` |
| `request` | Large aggregation result set | Reduce `size` in terms agg, use composite agg for pagination |
| `in_flight_requests` | Too many concurrent large requests | Add coordinating nodes, implement backpressure |

```http
// Identify the top memory consumers
GET /_nodes/stats/indices?filter_path=nodes.*.indices.segments.memory_in_bytes,nodes.*.indices.fielddata.memory_size_in_bytes,nodes.*.indices.query_cache.memory_size_in_bytes,nodes.*.indices.request_cache.memory_size_in_bytes

// Check fielddata usage per field
GET /_nodes/stats/indices/fielddata?fields=*&human=true
```

---

## 7. Slow Logs: Configuration and Analysis

### 7.1 Search Slow Log

The search slow log records queries that exceed configurable thresholds. It distinguishes between the query phase (scoring and matching) and the fetch phase (retrieving documents):

```http
// Configure search slow log per index
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
```

### 7.2 Indexing Slow Log

```http
// Configure indexing slow log
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

### 7.3 Slow Log Entry Format

Search slow log entries (JSON format in ES 7+):

```json
{
  "type": "index_search_slowlog",
  "timestamp": "2026-05-22T14:30:15.123Z",
  "level": "WARN",
  "component": "i.s.s.query",
  "cluster.name": "production",
  "node.name": "data-hot-01",
  "message": "[logs-2026.05][2]",
  "took": "12.5s",
  "took_millis": "12500",
  "total_hits": "450000",
  "types": "[]",
  "stats": "[]",
  "search_type": "QUERY_THEN_FETCH",
  "total_shards": "15",
  "source": "{\"query\":{\"bool\":{\"must\":[{\"wildcard\":{\"path\":{\"value\":\"*error*\"}}}]}},\"size\":100}"
}
```

### 7.4 Slow Log Analysis Queries

If slow logs are shipped to Elasticsearch via Filebeat:

```http
// Top 10 slowest queries in the last 24 hours
POST /slowlog-*/_search
{
  "size": 10,
  "query": {
    "bool": {
      "filter": [
        { "term": { "component": "i.s.s.query" } },
        { "range": { "timestamp": { "gte": "now-24h" } } }
      ]
    }
  },
  "sort": [{ "took_millis": "desc" }],
  "_source": ["took", "total_hits", "total_shards", "source", "node.name"]
}

// Most frequent slow query patterns
POST /slowlog-*/_search
{
  "size": 0,
  "query": {
    "bool": {
      "filter": [
        { "range": { "timestamp": { "gte": "now-7d" } } }
      ]
    }
  },
  "aggs": {
    "by_level": {
      "terms": { "field": "level", "size": 5 }
    },
    "avg_duration": {
      "avg": { "field": "took_millis" }
    },
    "p99_duration": {
      "percentiles": { "field": "took_millis", "percents": [50, 95, 99] }
    }
  }
}
```

### 7.5 Global Slow Log (Cluster-Level)

Set slow log thresholds across all indices using index templates:

```http
PUT /_index_template/slowlog-defaults
{
  "index_patterns": ["*"],
  "priority": 1,
  "template": {
    "settings": {
      "index.search.slowlog.threshold.query.warn": "10s",
      "index.search.slowlog.threshold.query.info": "5s",
      "index.search.slowlog.threshold.fetch.warn": "1s",
      "index.indexing.slowlog.threshold.index.warn": "10s"
    }
  }
}
```

---

## 8. Stack Monitoring with Metricbeat

### 8.1 Metricbeat Configuration for Elasticsearch

```yaml
# metricbeat.yml — Elasticsearch monitoring module
metricbeat.modules:
  - module: elasticsearch
    metricsets:
      - node
      - node_stats
      - index
      - index_recovery
      - index_summary
      - cluster_stats
      - shard
      - pending_tasks
      - ccr            # cross-cluster replication stats
      - enrich         # enrich processor stats
      - ml_job         # machine learning job stats
    period: 10s
    hosts: ["https://es-node-01:9200", "https://es-node-02:9200"]
    username: "monitoring_user"
    password: "${MONITORING_PASSWORD}"
    ssl.certificate_authorities: ["/etc/metricbeat/certs/ca.crt"]
    xpack.enabled: true

output.elasticsearch:
  hosts: ["https://monitoring-cluster:9200"]
  username: "beats_system"
  password: "${BEATS_PASSWORD}"
  ssl.certificate_authorities: ["/etc/metricbeat/certs/monitoring-ca.crt"]
```

### 8.2 Self-Monitoring vs Dedicated Monitoring Cluster

**Self-monitoring** (sending metrics back to the same cluster):
- Simple setup, no additional infrastructure.
- Risk: monitoring data adds load to the cluster being monitored. During a crisis (the exact moment you need monitoring), the monitoring data itself may be unavailable.
- Acceptable for development and small production clusters.

**Dedicated monitoring cluster** (recommended for production):
- Monitoring data is isolated from production data.
- Monitoring remains available even when the production cluster is degraded.
- Requires a separate small cluster (3 nodes minimum).

```yaml
# metricbeat.yml — output to dedicated monitoring cluster
output.elasticsearch:
  hosts: ["https://monitoring-es-01:9200", "https://monitoring-es-02:9200"]
  username: "beats_system"
  password: "${BEATS_PASSWORD}"
  index: ".monitoring-es-8-%{+yyyy.MM.dd}"
```

### 8.3 System-Level Monitoring

```yaml
# metricbeat.yml — system module for OS metrics
metricbeat.modules:
  - module: system
    metricsets:
      - cpu
      - memory
      - network
      - diskio
      - filesystem
      - process
    period: 10s
    processes: ["elasticsearch"]

  - module: linux
    metricsets:
      - pageinfo
      - memory
    period: 30s
```

### 8.4 Monitoring with Elastic Agent (ES 8.x)

In ES 8.x, Elastic Agent with Fleet is the recommended replacement for standalone Metricbeat:

```yaml
# Fleet integration for Elasticsearch monitoring
# Configure via Kibana > Fleet > Integrations > Elasticsearch
#
# The integration automatically:
# 1. Collects all Elasticsearch metrics
# 2. Ships to the monitoring cluster
# 3. Powers Stack Monitoring dashboards in Kibana
# 4. Sets up default alerting rules
```

---

## 9. Kibana Dashboards for Elasticsearch

### 9.1 Stack Monitoring Overview

Kibana's Stack Monitoring (under Management > Stack Monitoring) provides pre-built dashboards for:

- **Cluster overview**: health, node count, shard status, indexing/search rates
- **Node detail**: heap usage, GC metrics, CPU, disk I/O, thread pools per node
- **Index detail**: shard distribution, document count, indexing rate, search rate
- **Logstash monitoring**: pipeline throughput, events in/out, failures
- **Beats monitoring**: events published, output errors

### 9.2 Key Dashboard Panels to Create

If building custom Kibana dashboards, include these panels:

```
Cluster Health Dashboard:
┌─────────────────────────────────────────────────────────────────┐
│ Cluster Status: [GREEN]  Nodes: [12]  Shards: [900]           │
├──────────────────────┬──────────────────────────────────────────┤
│ JVM Heap by Node     │ Search Latency (p50, p95, p99)          │
│ [Line chart, 1h]     │ [Line chart, 1h]                        │
├──────────────────────┼──────────────────────────────────────────┤
│ Indexing Rate        │ Thread Pool Rejections                   │
│ [Area chart, 1h]     │ [Bar chart, cumulative]                  │
├──────────────────────┼──────────────────────────────────────────┤
│ Disk Usage by Node   │ GC Pause Duration                        │
│ [Bar chart]          │ [Line chart, 1h]                          │
├──────────────────────┼──────────────────────────────────────────┤
│ Unassigned Shards    │ Circuit Breaker Trips                    │
│ [Metric, last value] │ [Metric, rate]                            │
└──────────────────────┴──────────────────────────────────────────┘
```

### 9.3 Custom Dashboard with Saved Searches

```http
// Create a Kibana saved search for slow queries
POST /api/saved_objects/search
{
  "attributes": {
    "title": "ES Slow Queries (>5s)",
    "description": "Search slow log entries above 5 seconds",
    "kibanaSavedObjectMeta": {
      "searchSourceJSON": "{\"query\":{\"bool\":{\"filter\":[{\"term\":{\"type\":\"index_search_slowlog\"}},{\"range\":{\"took_millis\":{\"gte\":5000}}}]}},\"index\":\"slowlog-*\"}"
    }
  }
}
```

---

## 10. Alerting: Watcher and Kibana Rules

### 10.1 Watcher (Elasticsearch Built-In)

```http
// Alert: cluster health is not green
PUT /_watcher/watch/cluster_health_alert
{
  "trigger": {
    "schedule": { "interval": "1m" }
  },
  "input": {
    "http": {
      "request": {
        "host": "localhost",
        "port": 9200,
        "path": "/_cluster/health",
        "scheme": "https",
        "auth": {
          "basic": {
            "username": "watcher_user",
            "password": "{{watcher_password}}"
          }
        }
      }
    }
  },
  "condition": {
    "compare": {
      "ctx.payload.status": { "not_eq": "green" }
    }
  },
  "throttle_period": "15m",
  "actions": {
    "email_ops": {
      "email": {
        "profile": "standard",
        "to": ["ops@example.com"],
        "subject": "ES Cluster {{ctx.payload.status}} - {{ctx.payload.cluster_name}}",
        "body": {
          "text": "Cluster status: {{ctx.payload.status}}\nNodes: {{ctx.payload.number_of_nodes}}\nUnassigned shards: {{ctx.payload.unassigned_shards}}\nTimestamp: {{ctx.execution_time}}"
        }
      }
    },
    "webhook_pagerduty": {
      "webhook": {
        "scheme": "https",
        "host": "events.pagerduty.com",
        "port": 443,
        "method": "post",
        "path": "/v2/enqueue",
        "headers": {
          "Content-Type": "application/json"
        },
        "body": "{\"routing_key\":\"YOUR_PD_KEY\",\"event_action\":\"trigger\",\"payload\":{\"summary\":\"ES cluster {{ctx.payload.status}}\",\"severity\":\"critical\",\"source\":\"elasticsearch-watcher\"}}"
      }
    }
  }
}

// Alert: high heap usage
PUT /_watcher/watch/heap_usage_alert
{
  "trigger": {
    "schedule": { "interval": "5m" }
  },
  "input": {
    "http": {
      "request": {
        "host": "localhost",
        "port": 9200,
        "path": "/_nodes/stats/jvm",
        "scheme": "https",
        "auth": {
          "basic": {
            "username": "watcher_user",
            "password": "{{watcher_password}}"
          }
        }
      }
    }
  },
  "condition": {
    "script": {
      "source": "return ctx.payload.nodes.values().stream().anyMatch(n -> n.jvm.mem.heap_used_percent > 85)"
    }
  },
  "throttle_period": "30m",
  "actions": {
    "notify": {
      "email": {
        "to": ["ops@example.com"],
        "subject": "ES High Heap Usage Alert",
        "body": {
          "text": "One or more nodes have heap usage above 85%. Check immediately."
        }
      }
    }
  }
}

// Alert: thread pool rejections
PUT /_watcher/watch/rejection_alert
{
  "trigger": {
    "schedule": { "interval": "5m" }
  },
  "input": {
    "http": {
      "request": {
        "host": "localhost",
        "port": 9200,
        "path": "/_cat/thread_pool/write,search?format=json",
        "scheme": "https",
        "auth": {
          "basic": {
            "username": "watcher_user",
            "password": "{{watcher_password}}"
          }
        }
      }
    }
  },
  "condition": {
    "script": {
      "source": "return ctx.payload._value.stream().anyMatch(tp -> Integer.parseInt(tp.rejected) > 0)"
    }
  },
  "throttle_period": "15m",
  "actions": {
    "notify": {
      "email": {
        "to": ["ops@example.com"],
        "subject": "ES Thread Pool Rejections Detected",
        "body": {
          "text": "Thread pool rejections detected. Check write and search queues."
        }
      }
    }
  }
}
```

### 10.2 Managing Watcher

```http
// List all watches
GET /_watcher/_stats

// Get a specific watch
GET /_watcher/watch/cluster_health_alert

// Execute a watch immediately (for testing)
POST /_watcher/watch/cluster_health_alert/_execute

// Deactivate a watch
PUT /_watcher/watch/cluster_health_alert/_deactivate

// Activate a watch
PUT /_watcher/watch/cluster_health_alert/_activate

// Delete a watch
DELETE /_watcher/watch/cluster_health_alert

// Check watch execution history
GET /.watcher-history-*/_search
{
  "query": {
    "bool": {
      "filter": [
        { "term": { "watch_id": "cluster_health_alert" } },
        { "range": { "trigger_event.triggered_time": { "gte": "now-24h" } } }
      ]
    }
  },
  "sort": [{ "trigger_event.triggered_time": "desc" }],
  "size": 10
}
```

### 10.3 Kibana Rules (ES 8.x)

Kibana Rules provide a UI-driven alerting system that is simpler than Watcher for most use cases:

```
Kibana > Management > Rules and Connectors > Create Rule

Recommended rules for Elasticsearch monitoring:

1. Cluster Health
   - Type: Elasticsearch query
   - Index: .monitoring-es-*
   - Condition: cluster_state.status != green
   - Action: Email + Slack

2. High Heap Usage
   - Type: Elasticsearch query
   - Index: .monitoring-es-*
   - Condition: node_stats.jvm.mem.heap_used_percent > 85
   - Action: PagerDuty (critical)

3. Disk Space Low
   - Type: Elasticsearch query
   - Condition: node_stats.fs.total.available_in_bytes < threshold
   - Action: Slack + OpsGenie

4. Indexing Failures
   - Type: Elasticsearch query
   - Condition: delta(node_stats.indices.indexing.index_failed) > 0
   - Action: Email

5. Snapshot Failure
   - Type: Elasticsearch query
   - Condition: snapshot.state == "FAILED"
   - Action: PagerDuty
```

---

## 11. Diagnostic Dump and Support

### 11.1 Collecting a Diagnostic Bundle

When opening a support case or performing offline analysis, collect all diagnostic data:

```bash
#!/bin/bash
# diagnostic_dump.sh — collect ES diagnostic data
ES_URL="https://localhost:9200"
AUTH="-u elastic:password"
OUT_DIR="/tmp/es-diagnostics-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT_DIR"

# Cluster state
curl -s $AUTH "$ES_URL/_cluster/state?pretty" > "$OUT_DIR/cluster_state.json"

# Cluster health
curl -s $AUTH "$ES_URL/_cluster/health?pretty" > "$OUT_DIR/cluster_health.json"

# Cluster settings (including defaults)
curl -s $AUTH "$ES_URL/_cluster/settings?include_defaults&flat_settings&pretty" > "$OUT_DIR/cluster_settings.json"

# Node stats
curl -s $AUTH "$ES_URL/_nodes/stats?human=true&pretty" > "$OUT_DIR/node_stats.json"

# Node info
curl -s $AUTH "$ES_URL/_nodes?pretty" > "$OUT_DIR/node_info.json"

# Index stats
curl -s $AUTH "$ES_URL/_stats?human=true&pretty" > "$OUT_DIR/index_stats.json"

# Pending tasks
curl -s $AUTH "$ES_URL/_cluster/pending_tasks?pretty" > "$OUT_DIR/pending_tasks.json"

# Hot threads (3 snapshots, 500ms apart)
curl -s $AUTH "$ES_URL/_nodes/hot_threads?threads=5&interval=500ms" > "$OUT_DIR/hot_threads.txt"

# Task list
curl -s $AUTH "$ES_URL/_tasks?detailed=true&pretty" > "$OUT_DIR/tasks.json"

# Allocation explain (if yellow/red)
curl -s $AUTH "$ES_URL/_cluster/allocation/explain?pretty" > "$OUT_DIR/allocation_explain.json" 2>/dev/null

# Cat outputs
for api in health nodes indices shards allocation thread_pool; do
  curl -s $AUTH "$ES_URL/_cat/$api?v" > "$OUT_DIR/cat_$api.txt"
done

# Create archive
tar czf "$OUT_DIR.tar.gz" -C /tmp "$(basename $OUT_DIR)"
echo "Diagnostic dump: $OUT_DIR.tar.gz"
```

### 11.2 Elastic Support Diagnostic Tool

Elastic provides an official diagnostic tool:

```bash
# Download the diagnostic tool
# https://github.com/elastic/support-diagnostics

java -jar diagnostics-*.jar \
  --host https://es-node:9200 \
  --user elastic \
  --type remote \
  -o /tmp/es-diag
```

---

## 12. Key Metrics Reference

### 12.1 Comprehensive Metrics Table

| Category | Metric | API Path | Alert Threshold |
|----------|--------|----------|-----------------|
| **Cluster** | Status | `_cluster/health → status` | != green for > 5 min |
| | Unassigned shards | `_cluster/health → unassigned_shards` | > 0 for > 5 min |
| | Pending tasks | `_cluster/pending_tasks` | > 10 |
| | Active shards % | `_cluster/health → active_shards_percent` | < 100% |
| **JVM** | Heap used % | `_nodes/stats/jvm → mem.heap_used_percent` | > 85% |
| | Old GC count | `_nodes/stats/jvm → gc.collectors.old.collection_count` | Δ > 5/min |
| | Old GC time | `_nodes/stats/jvm → gc.collectors.old.collection_time_in_millis` | Δ > 5s/min |
| | Young GC time | `_nodes/stats/jvm → gc.collectors.young.collection_time_in_millis` | Avg > 200ms |
| **Indexing** | Index rate | `_nodes/stats → indices.indexing.index_total` | Δ drop > 50% |
| | Index latency | `_nodes/stats → indices.indexing.index_time_in_millis / index_total` | > 50ms avg |
| | Throttle time | `_nodes/stats → indices.indexing.throttle_time_in_millis` | > 0 |
| | Index failures | `_nodes/stats → indices.indexing.index_failed` | Δ > 0 |
| **Search** | Query rate | `_nodes/stats → indices.search.query_total` | Monitor trend |
| | Query latency | `_nodes/stats → indices.search.query_time_in_millis / query_total` | > 500ms avg |
| | Fetch latency | `_nodes/stats → indices.search.fetch_time_in_millis / fetch_total` | > 100ms avg |
| **Thread Pools** | Write rejections | `_cat/thread_pool/write → rejected` | Δ > 0 |
| | Search rejections | `_cat/thread_pool/search → rejected` | Δ > 0 |
| | Write queue | `_cat/thread_pool/write → queue` | > 5000 |
| | Search queue | `_cat/thread_pool/search → queue` | > 500 |
| **Disk** | Disk used % | `_cat/allocation → disk.percent` | > 80% |
| | Available space | `_nodes/stats/fs → total.available_in_bytes` | < 15% free |
| **Merges** | Active merges | `_nodes/stats → indices.merges.current` | > 10 |
| | Merge throttle | `_nodes/stats → indices.merges.total_throttled_time_in_millis` | > 0 |
| **Circuit Breakers** | Parent tripped | `_nodes/stats/breaker → parent.tripped` | Δ > 0 |
| | Fielddata tripped | `_nodes/stats/breaker → fielddata.tripped` | Δ > 0 |
| **OS** | CPU % | `_nodes/stats/os → cpu.percent` | > 90% |
| | Load average | `_nodes/stats/os → cpu.load_average.5m` | > 2 * cores |
| | Open file descriptors | `_nodes/stats/process → open_file_descriptors` | > 80% of max |

### 12.2 Derived Metrics

```
Indexing latency (ms/doc) = Δ index_time_in_millis / Δ index_total
Search latency (ms/query) = Δ query_time_in_millis / Δ query_total
Fetch latency (ms/fetch)  = Δ fetch_time_in_millis / Δ fetch_total
GC overhead (%)           = Δ gc_time_in_millis / (Δ wall_time * 1000) * 100
Cache hit rate (%)        = hit_count / (hit_count + miss_count) * 100
Merge ratio               = merge_total_size / store_size
```

---

## 13. Troubleshooting

### 13.1 Monitoring Data Not Appearing in Kibana

Check:
1. Metricbeat is running and connected: `metricbeat test output`
2. Monitoring indices exist: `GET /_cat/indices/.monitoring-es-*?v`
3. `xpack.enabled: true` is set in the Metricbeat module config
4. The monitoring user has the `monitoring_user` role
5. Time range in Kibana includes the monitoring data period

### 13.2 Stack Monitoring Shows Stale Data

```http
// Check the most recent monitoring document timestamp
GET /.monitoring-es-*/_search
{
  "size": 1,
  "sort": [{ "timestamp": "desc" }],
  "_source": ["timestamp", "type"]
}
```

If the timestamp is old, Metricbeat may be failing silently. Check Metricbeat logs.

### 13.3 Watcher Not Firing

```http
// Check watcher status
GET /_watcher/stats

// Check if the watch is active
GET /_watcher/watch/my_watch

// Manual execution for debugging
POST /_watcher/watch/my_watch/_execute
{
  "record_execution": true
}

// Check execution history
GET /.watcher-history-*/_search
{
  "query": { "term": { "watch_id": "my_watch" } },
  "sort": [{ "trigger_event.triggered_time": "desc" }],
  "size": 5
}
```

### 13.4 High Monitoring Overhead

If monitoring itself is consuming too many resources:
1. Increase the collection period from 10s to 30s or 60s.
2. Reduce the number of metricsets collected.
3. Use a dedicated monitoring cluster to isolate load.
4. Set shorter retention on monitoring indices.

---

## 14. FAQ

### Q1: Should I monitor Elasticsearch with Prometheus instead of Metricbeat?

Both work. Use the `elasticsearch_exporter` for Prometheus if your organization is standardized on Prometheus/Grafana. Use Metricbeat/Stack Monitoring if you want native Kibana integration. The metrics are equivalent — the choice is a tooling decision.

### Q2: How long should I retain monitoring data?

7-14 days is sufficient for operational troubleshooting. Beyond that, monitoring data rarely provides actionable insights. Use ILM on monitoring indices to auto-delete old data.

### Q3: What is the overhead of enabling slow logs?

Slow logs add negligible overhead. The log entry is only written when a query exceeds the threshold, and the I/O cost of writing a log line is trivial compared to the query itself. Always enable slow logs at the `warn` level in production.

### Q4: Can I alert on individual query performance?

Not directly via Watcher. Watcher can query the slow log index for patterns (e.g., "more than 10 queries above 10s in the last 5 minutes"). For real-time per-query alerting, use APM (Application Performance Monitoring) with the Elasticsearch APM agent.

### Q5: How do I identify which query is causing high heap usage?

1. Check hot threads: `GET /_nodes/hot_threads`.
2. Check the task list for long-running search tasks: `GET /_tasks?actions=*search*&detailed=true`.
3. Check slow logs for recent expensive queries.
4. Check fielddata usage: `GET /_nodes/stats/indices/fielddata?fields=*`.

### Q6: What is the difference between `_cluster/health` and `_health_report`?

`_cluster/health` provides a simple green/yellow/red status based on shard assignment. `_health_report` (ES 8.7+) provides structured diagnostics with root cause analysis, impact assessment, and recommended actions for multiple aspects of cluster health (master stability, disk usage, ILM, SLM).

---

## 15. Exercises

### Exercise 1: Monitoring Setup

Set up a complete monitoring stack:
1. Deploy a 3-node production cluster and a 1-node monitoring cluster.
2. Configure Metricbeat to collect Elasticsearch and system metrics.
3. Ship metrics to the monitoring cluster.
4. Verify data appears in Kibana Stack Monitoring.
5. Set retention on monitoring indices to 7 days via ILM.

### Exercise 2: Alert Configuration

Create Watcher alerts for the following scenarios:
1. Cluster status is not green for more than 5 minutes.
2. Any node's heap usage exceeds 85%.
3. Disk usage on any node exceeds 80%.
4. Write thread pool rejections increase by more than 100 in 5 minutes.
5. No snapshot has been taken in the last 24 hours.

Test each alert by simulating the condition and verifying the notification fires.

### Exercise 3: Slow Log Analysis

1. Configure slow logs on a test index with low thresholds (info=100ms, warn=500ms).
2. Run 20 different queries of varying complexity (match, range, wildcard, aggregation, nested).
3. Analyze the slow log output to identify the top 5 slowest queries.
4. For each slow query, use the Profile API to identify the bottleneck.
5. Optimize each query and verify the improvement in slow log times.

### Exercise 4: Diagnostic Dump Interpretation

Given a diagnostic dump from a distressed cluster, analyze:
1. `cat_health.txt`: What is the cluster status? How many unassigned shards?
2. `node_stats.json`: Which node has the highest heap usage? Is GC healthy?
3. `cat_thread_pool.txt`: Are there any rejections? Which pool?
4. `hot_threads.txt`: What are the threads doing?
5. `allocation_explain.json`: Why are shards unassigned?

Document your findings and recommend remediation steps.

### Exercise 5: Custom Kibana Dashboard

Build a Kibana dashboard with the following panels:
1. Cluster health status (metric visualization)
2. JVM heap usage per node (line chart, last 6 hours)
3. Indexing rate vs. search rate (dual-axis chart)
4. Thread pool rejections (cumulative bar chart)
5. Disk usage per node (horizontal bar chart)
6. Top 10 slowest queries (data table from slow log index)

Export the dashboard as a saved object for team sharing.

---

*Questo documento fa parte del modulo 08 "Elasticsearch" della Data Encyclopedia.*
