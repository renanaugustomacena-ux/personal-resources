# Architettura di Elasticsearch

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-22  
> Versione: 2.0.0  
> Stato: expanded

## Indice
1. Lucene: il Motore Sottostante
2. Struttura del Cluster
3. Indici, Shard e Replica
4. Document Routing e Near-Real-Time Search
5. Translog e Ciclo di Vita dei Dati
6. Cluster State e Metadata Management
7. Node Discovery e Fault Detection
8. Data Streams (ES 7.9+)
9. REST API: Cluster Operations
10. Troubleshooting
11. FAQ

---

## 1. Lucene: il Motore Sottostante

### 1.1 Inverted Index

Elasticsearch è costruito sopra Apache Lucene, una libreria Java di information retrieval. Il cuore di Lucene è l'**inverted index**: una struttura dati che mappa ogni termine del corpus documentale all'insieme di documenti che lo contengono, insieme a informazioni ausiliarie come la frequenza del termine nel documento (TF) e la sua posizione nel testo. Questa struttura è l'opposto dell'organizzazione tradizionale "documento → lista di parole" — in un inverted index il mapping è "termine → lista di documenti", il che permette di trovare tutti i documenti che contengono un termine in O(1) rispetto alla dimensione del corpus.

Ogni indice Lucene è composto da uno o più **segmenti**: unità immutabili di storage che contengono un sottoinsieme dei documenti. Quando si indicizza un documento, Lucene lo aggiunge a un buffer in memoria. Periodicamente, il buffer viene svuotato su disco creando un nuovo segmento immutabile. L'immutabilità dei segmenti semplifica enormemente il problema della concorrenza: più thread possono leggere un segmento simultaneamente senza lock, perché il segmento non cambia mai.

### 1.2 Anatomy of a Lucene Segment

Each segment is a self-contained mini-index that consists of several data structures stored as files on disk:

- **Term Dictionary**: a sorted list of all unique terms across all documents in the segment. Stored as a finite-state transducer (FST) for compact in-memory representation and O(1) prefix lookups.
- **Postings List**: for each term, a list of document IDs that contain it, along with term frequency, position offsets, and payloads. Encoded with variable-byte encoding and skip lists for fast intersection.
- **Stored Fields**: the original `_source` JSON document, compressed with LZ4 (default) or DEFLATE (`best_compression`). Retrieved only when the document needs to be returned.
- **Doc Values**: columnar storage for sorting, aggregations, and scripting. Stored on disk and memory-mapped. One column per field, not per document.
- **Norms**: per-document, per-field normalization factors used by the scoring algorithm (BM25). They encode field length so that shorter fields score higher for the same term.
- **Point Values (BKD Trees)**: used for numeric, date, and geo_point fields. Enables efficient range queries in multi-dimensional space.

```
# Segment file structure on disk (simplified)
/data/nodes/0/indices/<uuid>/0/index/
├── _0.cfe          # compound file entries
├── _0.cfs          # compound file (all segment files packed)
├── _0.si           # segment info (version, doc count)
├── segments_N      # commit point (lists active segments)
└── write.lock      # prevents concurrent writers
```

Understanding segment internals matters for production tuning: knowing that doc_values are columnar explains why keyword fields are fast for aggregations, while stored fields retrieval is expensive for large `_source` documents.

### 1.3 Segmenti e Merging

L'accumulo di molti segmenti piccoli degrada le prestazioni di ricerca, poiché ogni query deve essere eseguita su tutti i segmenti attivi. Per questo motivo, Lucene esegue periodicamente un processo di **merging**: segmenti piccoli vengono fusi in segmenti più grandi, riducendo il numero totale di segmenti e migliorando le prestazioni. Durante il merge, i documenti marcati come eliminati (che nei segmenti immutabili sono solo "flaggati" ma non rimossi fisicamente) vengono effettivamente rimossi, liberando spazio su disco.

In Elasticsearch, il processo di merge è gestito da un thread pool dedicato e può essere configurato per limitare l'impatto sull'I/O durante le ore di punta. La politica di merge predefinita (TieredMergePolicy) bilancia automaticamente il numero di segmenti e le loro dimensioni.

### 1.4 Merge Policies and Tuning

The `TieredMergePolicy` works by grouping segments into tiers based on size and selecting the tier with the most segments for merging. Key configuration parameters:

```http
PUT /my-index/_settings
{
  "index": {
    "merge.policy.max_merged_segment": "5gb",
    "merge.policy.segments_per_tier": 10,
    "merge.policy.floor_segment": "2mb",
    "merge.policy.deletes_pct_allowed": 33.0,
    "merge.scheduler.max_thread_count": 1
  }
}
```

- `max_merged_segment`: segments larger than this are never merged. Set lower on spinning disks (2gb) to limit I/O duration; higher on NVMe (5-10gb).
- `segments_per_tier`: how many segments are allowed per tier before a merge is triggered. Lower values mean more aggressive merging (better search performance, higher I/O cost).
- `floor_segment`: segments smaller than this are rounded up to this size when calculating merge costs, encouraging small segments to merge quickly.
- `deletes_pct_allowed`: the percentage of deleted documents allowed before a merge is forced to expunge them. In ES 8.x, this defaults to 33%.
- `max_thread_count`: on spinning disks, set to 1. On SSDs with high IOPS, the default (based on available cores) is usually fine.

### 1.5 BM25 Scoring Model

Elasticsearch uses BM25 (Best Match 25) as its default relevance scoring algorithm, replacing the older TF-IDF model since ES 5.0. BM25 is a probabilistic model that scores a document `d` for a query term `q` as:

```
score(q, d) = IDF(q) * (tf(q,d) * (k1 + 1)) / (tf(q,d) + k1 * (1 - b + b * (dl / avgdl)))
```

Where:
- `IDF(q)` = inverse document frequency: log((N - n + 0.5) / (n + 0.5) + 1)
- `tf(q,d)` = term frequency in document d
- `k1` = term frequency saturation parameter (default 1.2). Higher values increase the weight of term frequency.
- `b` = field length normalization (default 0.75). 0 disables normalization; 1 fully normalizes by field length.
- `dl` = document length (number of terms in the field)
- `avgdl` = average document length across the index

```http
// Customize BM25 parameters per field
PUT /articles
{
  "mappings": {
    "properties": {
      "content": {
        "type": "text",
        "similarity": "my_bm25"
      }
    }
  },
  "settings": {
    "index": {
      "similarity": {
        "my_bm25": {
          "type": "BM25",
          "k1": 1.5,
          "b": 0.5
        }
      }
    }
  }
}
```

---

## 2. Struttura del Cluster

### 2.1 Tipi di Nodo

Un cluster Elasticsearch è composto da nodi con ruoli distinti. Il **nodo master** è responsabile della gestione del cluster state: assegnazione degli shard ai nodi, tracciamento dei nodi online/offline, e gestione delle operazioni DDL (creazione/eliminazione indici, mapping updates). Per garantire la disponibilità, è consigliato avere almeno 3 nodi con ruolo master eligible — l'algoritmo di consenso Zen2 (basato su Raft) richiede un quorum di `(n/2)+1` nodi per eleggere il master.

Il **nodo dati** memorizza fisicamente i dati degli shard e li serve alle query. È il tipo di nodo più resource-intensive in termini di CPU, memoria (heap per la JVM), e I/O disco. I **nodi ingest** pre-processano i documenti prima dell'indicizzazione attraverso pipeline di trasformazione (simili a pipeline Logstash ma embedded nel cluster). Il **nodo coordinatore** (qualsiasi nodo può svolgere questo ruolo) riceve le richieste client, le distribuisce ai nodi dati appropriati, e aggrega le risposte parziali in un risultato finale.

```yaml
# elasticsearch.yml — configurazione nodo
node.name: "es-data-01"
node.roles: ["data", "ingest"]  # ruoli espliciti (ES 7.9+)

# Per nodo master-only in cluster di produzione:
# node.roles: ["master"]

cluster.name: "produzione-cluster"
network.host: 0.0.0.0
discovery.seed_hosts: ["es-master-01", "es-master-02", "es-master-03"]
cluster.initial_master_nodes: ["es-master-01", "es-master-02", "es-master-03"]
```

### 2.2 Node Roles Reference (ES 8.x)

Elasticsearch 8.x introduced fine-grained node roles that replace the older boolean flags. A single node can hold multiple roles:

| Role | Description | Typical Hardware |
|------|-------------|-----------------|
| `master` | Manages cluster state, index creation, shard allocation | Low CPU/RAM, fast disk for cluster state |
| `data` | Stores shards, executes searches and aggregations | High CPU, high RAM, fast storage |
| `data_content` | Stores content data (user-facing indices) | High CPU, fast SSD |
| `data_hot` | Stores recently written time-series data | NVMe SSD, high IOPS |
| `data_warm` | Stores older time-series data accessed less frequently | Standard SSD |
| `data_cold` | Stores rarely accessed time-series data | HDD or large SSD |
| `data_frozen` | Mounts searchable snapshots from remote storage | Minimal local disk |
| `ingest` | Runs ingest pipelines before indexing | Moderate CPU |
| `ml` | Runs machine learning jobs | High CPU, moderate RAM |
| `remote_cluster_client` | Acts as a client for cross-cluster search | Low resources |
| `transform` | Runs transform jobs (continuous aggregations) | Moderate CPU, moderate RAM |
| `voting_only` | Participates in master election but cannot be elected | Minimal resources |

```yaml
# Production node configuration examples

# Dedicated master node (3 minimum)
node.roles: [master]

# Hot data node with ingest
node.roles: [data_hot, ingest]

# Warm data node
node.roles: [data_warm]

# Coordinating-only node (load balancer)
node.roles: []

# ML node
node.roles: [ml, remote_cluster_client]
```

### 2.3 Zen2 e Leader Election

Elasticsearch 7.x ha introdotto **Zen2**, un algoritmo di consenso ispirato a Raft che sostituisce il precedente Zen. La caratteristica più importante è che l'elezione del master è deterministica e resistente al split-brain senza richiedere una configurazione manuale di `minimum_master_nodes`. Il cluster richiede un quorum di `(n/2)+1` nodi master-eligible per eleggere un leader, e questo quorum viene aggiornato automaticamente quando i nodi vengono aggiunti o rimossi.

### 2.4 Zen2 Internals and Failure Handling

Zen2 uses a publication-based protocol where cluster state changes follow these steps:

1. **Publish phase**: the elected master publishes a new cluster state to all master-eligible nodes.
2. **Commit phase**: once a majority (quorum) of nodes acknowledge receipt, the master sends a commit message.
3. **Apply phase**: each node applies the committed cluster state locally.

This two-phase protocol ensures that either all nodes in the quorum see the update or none do. Key timing parameters:

```yaml
# elasticsearch.yml — Zen2 timing
cluster.election.initial_timeout: 100ms      # wait before starting first election
cluster.election.back_off_time: 100ms         # backoff between election attempts
cluster.election.max_timeout: 10s             # max timeout between election attempts
cluster.election.duration: 500ms              # how long an election round lasts

cluster.fault_detection.leader_check.interval: 1s     # how often followers ping leader
cluster.fault_detection.leader_check.timeout: 10s      # timeout for leader ping
cluster.fault_detection.leader_check.retry_count: 3    # retries before considering leader dead
cluster.fault_detection.follower_check.interval: 1s    # how often leader pings followers
cluster.fault_detection.follower_check.timeout: 10s
cluster.fault_detection.follower_check.retry_count: 3
```

When a master node fails:
1. Followers detect the failure after `retry_count` missed pings.
2. A new election starts among the remaining master-eligible nodes.
3. The node with the highest cluster state version (and lowest node ID as tiebreaker) wins.
4. The new master publishes the updated cluster state removing the failed node.
5. Shard allocation begins for any unassigned shards that were on the failed node.

---

## 3. Indici, Shard e Replica

### 3.1 Shard come Unità di Distribuzione

Un **indice Elasticsearch** è una struttura logica suddivisa in **shard primari** (primary shards), ognuno dei quali è un indice Lucene completo e autonomo. La suddivisione in shard è il meccanismo di distribuzione orizzontale: shard diversi risiedono su nodi diversi, permettendo di scalare sia la capacità di storage che il throughput di ricerca aggiungendo nodi al cluster.

Il numero di shard primari viene definito al momento della creazione dell'indice e non può essere modificato successivamente (a meno di non usare la Shrink/Split API). La regola pratica è dimensionare gli shard a una dimensione target di 10-50 GB ciascuno. Un shard troppo grande rende le riparazioni post-failure lente (tutto lo shard deve essere recuperato); troppo piccolo crea overhead di metadati e degrada le query (che devono essere distribuite a molti shard).

```
# Calcolo del numero ottimale di shard
shard_count = MAX(
    CEIL(dataset_size_gb / 30),    # 30 GB per shard
    node_count                      # almeno uno shard per nodo
)
```

### 3.2 Shard Sizing Guidelines

Proper shard sizing is one of the most impactful architectural decisions. The consequences of getting it wrong compound over time:

| Factor | Too Few Shards (oversized) | Too Many Shards (undersized) |
|--------|---------------------------|------------------------------|
| Recovery time | Slow: each shard recovery transfers GBs | Fast per shard, but many shards compete for bandwidth |
| Query latency | Each shard query takes longer | Coordination overhead from scatter-gather across many shards |
| Heap overhead | Low | Each shard uses ~10-20KB of heap for metadata; 1000+ shards per node is problematic |
| Merge cost | Large segments take long to merge | Many tiny segments are merged frequently |
| Rebalancing | Moving one shard moves a lot of data | Frequent small moves, generally fine |

Production recommendations:
- Target shard size: **10-50 GB** (30 GB sweet spot for most workloads).
- Maximum shards per node: **20 shards per GB of heap**. With 32 GB heap, aim for under 640 shards per node.
- Maximum shards per index: consider the number of data nodes. An index with 30 primary shards on 3 data nodes means 10 shards per node for that index alone.
- For time-series data with ILM rollover, size the rollover trigger (`max_primary_shard_size: 50gb`) so that rolled-over indices have reasonable shard sizes.

```http
// Check current shard sizes across the cluster
GET /_cat/shards?v&h=index,shard,prirep,store,node&s=store:desc

// Check total shard count per node
GET /_cat/allocation?v&h=node,shards,disk.used,disk.avail,disk.percent
```

### 3.3 Replica Shard e ISR

Ogni shard primario ha zero o più **shard replica** (repliche esatte). I replica servono due scopi: fault tolerance (se il nodo del primario cade, una replica può essere promossa a primario) e read scalability (le query possono essere distribuite sia ai primari che alle repliche). Elasticsearch usa un meccanismo di sincronizzazione chiamato **In-Sync Replicas (ISR)**: un'operazione di scrittura è considerata riuscita solo quando è stata confermata da tutte le repliche nell'ISR set. Le repliche che rimangono indietro vengono rimosse dall'ISR e devono risincronizzarsi completamente prima di rientrare nel set.

```http
PUT /mio-indice
{
  "settings": {
    "number_of_shards":   3,
    "number_of_replicas": 1,
    "index.refresh_interval": "5s"
  },
  "mappings": {
    "properties": {
      "timestamp": { "type": "date" },
      "titolo":    { "type": "text", "analyzer": "italian" },
      "categoria": { "type": "keyword" }
    }
  }
}
```

### 3.4 Write Consistency and wait_for_active_shards

By default, an index operation returns success once the primary shard and all in-sync replicas acknowledge the write. You can control this with `wait_for_active_shards`:

```http
// Wait for all shards (primary + replicas) before returning
PUT /critical-data/_doc/1?wait_for_active_shards=all
{ "important": "data" }

// Wait for at least 2 shards (primary + 1 replica)
PUT /critical-data/_doc/2?wait_for_active_shards=2
{ "important": "data" }

// Index-level default
PUT /critical-data/_settings
{
  "index.write.wait_for_active_shards": "all"
}
```

For write-heavy workloads where some data loss is acceptable (e.g., metrics), setting `wait_for_active_shards: 1` reduces write latency by not waiting for replica acknowledgement.

---

## 4. Document Routing e Near-Real-Time Search

### 4.1 Formula di Routing

Quando si indicizza un documento, Elasticsearch determina su quale shard primario inviarlo usando la formula:

```
shard = hash(routing_key) % number_of_primary_shards
```

Dove `routing_key` è di default il `_id` del documento, ma può essere personalizzato. Questa formula garantisce una distribuzione uniforme dei documenti tra gli shard. Quando si esegue una query senza routing esplicito, la query viene distribuita a tutti gli shard (scatter phase) e i risultati vengono aggregati (gather phase). Con routing esplicito (`?routing=customer_id`), la query va solo allo shard specifico, riducendo l'overhead.

### 4.2 Custom Routing in Practice

Custom routing is essential for multi-tenant systems and parent-child relationships. When you route by `tenant_id`, all documents for a tenant land on the same shard, making single-tenant queries hit one shard instead of all:

```http
// Index with custom routing
PUT /orders/_doc/order-123?routing=tenant-abc
{
  "tenant_id": "tenant-abc",
  "amount": 99.99,
  "product": "widget"
}

// Search with routing — hits only the shard containing tenant-abc
GET /orders/_search?routing=tenant-abc
{
  "query": { "term": { "tenant_id": "tenant-abc" } }
}
```

**Routing-aware index settings** can enforce that a routing value is always provided:

```http
PUT /orders
{
  "mappings": {
    "_routing": {
      "required": true
    }
  }
}
```

The risk of custom routing is **shard skew**: if one routing key (e.g., a very large tenant) has far more documents than others, its shard becomes a hot spot. Monitor shard sizes regularly:

```http
GET /_cat/shards/orders?v&h=shard,prirep,store,docs,node&s=store:desc
```

### 4.3 Near-Real-Time Search

Elasticsearch offre una semantica **near-real-time (NRT)**: i documenti indicizzati diventano visibili alle ricerche entro circa 1 secondo (il valore di default di `refresh_interval`). Questo comportamento è possibile perché il refresh di Lucene — che crea un nuovo segment reader — è un'operazione leggera che non richiede una fsync su disco.

Il ciclo completo di un documento è:
1. **Index**: documento arriva nel buffer in memoria
2. **Refresh** (ogni 1 secondo): il buffer viene scritto in un nuovo segmento Lucene e il documento diventa cercabile. Il segmento è in memoria ma non è ancora durevole.
3. **Flush** (ogni 30 minuti o quando il translog supera 512 MB): il segmento viene scritto durevolmente su disco (fsync) e il translog viene svuotato.

### 4.4 Controlling NRT Behavior

```http
// Make a document immediately searchable (expensive — don't do per-document)
PUT /my-index/_doc/1?refresh=true
{ "content": "must be searchable immediately" }

// Wait for the next scheduled refresh (less expensive)
PUT /my-index/_doc/2?refresh=wait_for
{ "content": "will be searchable after next refresh" }

// Manually trigger a refresh on an index
POST /my-index/_refresh

// Change refresh interval (trade-off: higher = better indexing throughput, worse search freshness)
PUT /my-index/_settings
{ "index.refresh_interval": "30s" }

// Disable refresh entirely (for bulk loading)
PUT /my-index/_settings
{ "index.refresh_interval": "-1" }
```

---

## 5. Translog e Ciclo di Vita dei Dati

### 5.1 Il Translog come Write-Ahead Log

Il **translog** (transaction log) è il meccanismo di durabilità di Elasticsearch. Ogni operazione di scrittura (index, update, delete) viene scritta sul translog prima di essere confermata al client. In caso di crash prima del flush, le operazioni non ancora trasferite su disco dal refresh/flush possono essere recuperate rieseguendo il translog.

```http
# Configurazione durabilità translog
PUT /mio-indice/_settings
{
  "index": {
    "translog.durability": "request",  # fsync del translog per ogni request (sicuro, lento)
    "translog.sync_interval": "5s",    # oppure: sync ogni 5 secondi (più veloce, piccola perdita possibile)
    "translog.flush_threshold_size": "1gb"
  }
}
```

### 5.2 Translog Durability Trade-offs

The translog durability setting controls the data safety vs. performance trade-off:

| Setting | Behavior | Data Loss Risk | Performance |
|---------|----------|---------------|-------------|
| `request` (default) | fsync after every index/bulk request | None (unless disk fails) | Slower writes |
| `async` | fsync every `sync_interval` | Up to `sync_interval` seconds of data | Faster writes |

For bulk ingestion of reproducible data (e.g., reindexing from a source of truth), `async` with a 30-60s interval is safe and significantly faster. For primary data stores where the index IS the source of truth, keep `request`.

```http
// Monitor translog size and operations
GET /my-index/_stats/translog?human=true

// Response includes:
// "translog": {
//   "operations": 1234,
//   "size_in_bytes": 52428800,
//   "uncommitted_operations": 42,
//   "uncommitted_size_in_bytes": 1048576
// }
```

### 5.3 Monitoraggio dello Stato del Cluster

```http
# Stato del cluster (green/yellow/red)
GET /_cluster/health?pretty

# Statistiche degli indici
GET /_cat/indices?v&s=store.size:desc

# Dettaglio degli shard e loro allocazione
GET /_cat/shards?v&h=index,shard,prirep,state,node,store

# Nodi del cluster con risorse
GET /_cat/nodes?v&h=name,ip,heap.percent,ram.percent,cpu,disk.used_percent,node.role
```

---

## 6. Cluster State e Metadata Management

### 6.1 What Lives in the Cluster State

The cluster state is a data structure maintained by the master node and replicated to all nodes. It contains:

- **Routing table**: which shards live on which nodes, their status (STARTED, INITIALIZING, RELOCATING, UNASSIGNED).
- **Node membership**: list of all nodes, their roles, attributes, and transport addresses.
- **Index metadata**: mappings, settings, aliases, and ILM policies for every index.
- **Ingest pipelines**: all defined pipelines and their processor chains.
- **Security state**: roles, role mappings, API keys, tokens.
- **Persistent cluster settings**: settings that survive cluster restarts.

A large cluster state (thousands of indices with complex mappings) can become a bottleneck because every cluster state update must be published to all nodes.

```http
// View the full cluster state (warning: can be very large)
GET /_cluster/state?pretty

// View only specific components
GET /_cluster/state/metadata,routing_table?pretty

// View cluster state size
GET /_cluster/state?filter_path=metadata.cluster_uuid,version
```

### 6.2 Cluster State Size Management

Monitor cluster state size to prevent master instability:

```http
// Check cluster state serialization size
GET /_cluster/stats?filter_path=cluster_name,status,indices.count,indices.shards.total

// Common causes of large cluster state:
// 1. Too many indices (>10,000)
// 2. Too many fields per index (mapping explosion)
// 3. Too many shards total (>100,000 across cluster)
```

Mitigations:
- Use index templates with `dynamic: "strict"` to prevent mapping explosion.
- Set `index.mapping.total_fields.limit` (default 1000) to cap fields per index.
- Use data streams and ILM to delete old indices automatically.
- Use `index.mapping.depth.limit` (default 20) to limit nested object depth.

```http
// Set field limits
PUT /my-index/_settings
{
  "index.mapping.total_fields.limit": 500,
  "index.mapping.depth.limit": 10,
  "index.mapping.nested_fields.limit": 50,
  "index.mapping.nested_objects.limit": 10000
}
```

---

## 7. Node Discovery e Fault Detection

### 7.1 Bootstrap and Discovery

When a node starts, it must discover and join an existing cluster. The discovery process in ES 8.x:

1. Node reads `discovery.seed_hosts` from configuration.
2. Pings seed hosts on the transport port (9300).
3. Receives a list of current master-eligible nodes.
4. Joins the cluster by connecting to the elected master.

```yaml
# elasticsearch.yml — discovery configuration
discovery.seed_hosts:
  - es-master-01:9300
  - es-master-02:9300
  - es-master-03:9300

# Only needed for FIRST startup of a new cluster
cluster.initial_master_nodes:
  - es-master-01
  - es-master-02
  - es-master-03

# IMPORTANT: Remove cluster.initial_master_nodes after the cluster is formed.
# Leaving it in place can cause split-brain if nodes are wiped and restarted.
```

### 7.2 Fault Detection Mechanism

Elasticsearch runs two concurrent fault detection processes:

**Leader check**: every follower pings the leader periodically. If the leader doesn't respond after `retry_count` attempts, the follower starts a new election.

**Follower check**: the leader pings every follower. If a follower is unreachable after retries, the leader removes it from the cluster state, and its shards are reallocated.

```http
// Check which node is the current master
GET /_cat/master?v

// Inspect pending cluster state publications (sign of slow master)
GET /_cluster/pending_tasks

// Node connection stats
GET /_nodes/stats/transport?human=true
```

---

## 8. Data Streams (ES 7.9+)

### 8.1 Data Streams vs Traditional Indices

Data streams are an abstraction designed for append-only time-series data (logs, metrics, events). A data stream is backed by auto-generated, hidden indices called **backing indices**. New documents always go to the latest backing index; older backing indices are read-only and managed by ILM.

```http
// Create an index template for a data stream
PUT /_index_template/logs-template
{
  "index_patterns": ["logs-*"],
  "data_stream": {},
  "priority": 200,
  "template": {
    "settings": {
      "number_of_shards": 2,
      "number_of_replicas": 1,
      "index.lifecycle.name": "logs-ilm-policy"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "message":    { "type": "text" },
        "service":    { "type": "keyword" },
        "level":      { "type": "keyword" }
      }
    }
  }
}

// Documents are indexed directly to the data stream name
POST /logs-myapp/_doc
{
  "@timestamp": "2026-05-22T10:30:00Z",
  "message": "Request processed",
  "service": "order-api",
  "level": "INFO"
}

// The data stream auto-creates backing indices like:
// .ds-logs-myapp-2026.05.22-000001
// .ds-logs-myapp-2026.05.22-000002 (after rollover)
```

### 8.2 Data Stream Operations

```http
// List data streams
GET /_data_stream

// Get data stream details (backing indices, ILM status)
GET /_data_stream/logs-myapp

// Manual rollover (normally ILM handles this)
POST /logs-myapp/_rollover

// Delete data from a data stream by query (requires op_type)
POST /logs-myapp/_delete_by_query
{
  "query": { "range": { "@timestamp": { "lt": "2026-01-01" } } }
}

// Stats for a data stream
GET /_data_stream/logs-myapp/_stats
```

Data streams vs. traditional indices:
- Data streams enforce `@timestamp` and append-only semantics.
- Updates and deletes by `_id` are not supported (use `_delete_by_query` or `_update_by_query`).
- Data streams integrate natively with ILM rollover.
- Use data streams for time-series data. Use traditional indices for mutable data (user profiles, product catalogs).

---

## 9. REST API: Cluster Operations

### 9.1 Essential Cluster Management APIs

```http
// Reroute a shard manually (emergency use only)
POST /_cluster/reroute
{
  "commands": [
    {
      "move": {
        "index": "my-index",
        "shard": 0,
        "from_node": "node-1",
        "to_node": "node-2"
      }
    },
    {
      "allocate_stale_primary": {
        "index": "my-index",
        "shard": 1,
        "node": "node-3",
        "accept_data_loss": true
      }
    }
  ]
}

// Temporarily disable shard allocation (before rolling restart)
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.enable": "primaries"
  }
}

// Re-enable after restart
PUT /_cluster/settings
{
  "persistent": {
    "cluster.routing.allocation.enable": "all"
  }
}

// Drain a node before decommissioning
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.allocation.exclude._ip": "10.0.1.5"
  }
}
```

### 9.2 Rolling Restart Procedure

A safe rolling restart (for upgrades, config changes, or JVM tuning):

```http
// Step 1: Disable shard allocation
PUT /_cluster/settings
{ "persistent": { "cluster.routing.allocation.enable": "primaries" } }

// Step 2: Stop non-essential indexing (optional but recommended)
POST /_flush/synced

// Step 3: Restart the node (via systemd or service manager)
// $ sudo systemctl restart elasticsearch

// Step 4: Wait for the node to rejoin
GET /_cat/nodes?v

// Step 5: Re-enable allocation
PUT /_cluster/settings
{ "persistent": { "cluster.routing.allocation.enable": "all" } }

// Step 6: Wait for green
GET /_cluster/health?wait_for_status=green&timeout=5m

// Repeat steps 3-6 for each node
```

---

## 10. Troubleshooting

### 10.1 Cluster Health is RED

**Symptom**: `GET /_cluster/health` returns `status: "red"`.

**Root cause**: one or more primary shards are unassigned. No copy of those shards exists in the cluster.

```http
// Find unassigned primary shards
GET /_cat/shards?v&h=index,shard,prirep,state,unassigned.reason&s=state:desc

// Get allocation explanation for a specific shard
GET /_cluster/allocation/explain
{
  "index": "my-index",
  "shard": 0,
  "primary": true
}
```

Common causes and fixes:
- **Node failure with no replicas**: if `number_of_replicas: 0`, a node loss causes red. Fix: increase replicas. If the data is gone, allocate a stale primary (accepts data loss) or delete the index.
- **Disk watermark exceeded**: nodes refuse new shards when disk usage exceeds 85% (low watermark). Check with `GET /_cat/allocation?v`. Fix: add disk, delete old indices, or adjust watermarks.
- **Corrupted shard**: Lucene segment corruption. Fix: restore from snapshot or allocate stale primary with `accept_data_loss: true`.

### 10.2 Cluster Health is YELLOW

**Symptom**: all primaries assigned, but one or more replica shards are unassigned.

Common causes:
- **Not enough nodes**: an index with 1 replica needs at least 2 data nodes. A single-node cluster is always yellow (unless all indices have 0 replicas).
- **Allocation filtering**: replica cannot be placed on the same node as the primary (by design). If all nodes are excluded by allocation rules, replicas stay unassigned.
- **Disk watermark**: nodes above 85% disk usage reject new shard allocation.

### 10.3 Slow Search Performance

Diagnosis steps:

```http
// 1. Profile the query
POST /my-index/_search
{
  "profile": true,
  "query": { "match": { "content": "slow query example" } }
}

// 2. Check segment count (too many segments = slow searches)
GET /_cat/segments/my-index?v&h=index,shard,segment,generation,docs.count,size

// 3. Check if fielddata is consuming heap
GET /_nodes/stats/indices/fielddata?human=true

// 4. Review slow logs
// Check: /var/log/elasticsearch/<cluster_name>_index_search_slowlog.json
```

### 10.4 High JVM Heap Usage

**Symptom**: `heap_used_percent > 85%`, frequent GC pauses.

```http
// Check heap usage per node
GET /_cat/nodes?v&h=name,heap.percent,heap.max,ram.percent

// Check what is consuming heap
GET /_nodes/stats/indices?human=true&filter_path=nodes.*.indices.fielddata,nodes.*.indices.query_cache,nodes.*.indices.request_cache,nodes.*.indices.segments
```

Common causes:
- **Fielddata on text fields**: disable fielddata and use keyword sub-fields.
- **Too many shards**: each shard uses ~10-20 KB of heap. 100,000 shards = 1-2 GB just for metadata.
- **Large aggregations**: cardinality aggs on high-cardinality fields, or terms aggs with large `size`.
- **Parent-child joins**: expensive in heap. Consider denormalization.

### 10.5 Indexing Rejections (Thread Pool Queue Full)

```http
// Check thread pool rejection counts
GET /_cat/thread_pool/write?v&h=node_name,name,active,queue,rejected,completed

// If rejected > 0, the write queue is full. Options:
// 1. Reduce bulk request rate
// 2. Increase thread_pool.write.queue_size (temporary)
// 3. Add more data nodes
// 4. Check for slow merges or GC pauses causing backpressure
```

### 10.6 Snapshot Failures

```http
// Check snapshot status
GET /_snapshot/my-repo/_status

// Common issues:
// - Repository not accessible (permissions, network)
// - Concurrent snapshots (only one active snapshot per cluster)
// - Out of disk on repository target
```

### 10.7 Split Brain (Historical)

In ES 7.x+ with Zen2, true split-brain is prevented by the quorum-based election protocol. However, network partitions can still cause cluster instability. If a master-eligible node is partitioned from the quorum, it steps down and stops accepting writes. This is by design and prevents data divergence.

### 10.8 Mapping Explosion

**Symptom**: cluster state grows very large, master becomes slow, new field creation fails.

```http
// Check field count for an index
GET /my-index/_mapping?filter_path=*.mappings.properties

// Prevention:
PUT /my-index/_settings
{
  "index.mapping.total_fields.limit": 500
}

// Set dynamic mapping to strict
PUT /my-index/_mapping
{
  "dynamic": "strict"
}
```

### 10.9 Unbalanced Shard Distribution

```http
// Check shard distribution across nodes
GET /_cat/allocation?v&h=node,shards,disk.used,disk.avail,disk.percent

// Force rebalancing
PUT /_cluster/settings
{
  "transient": {
    "cluster.routing.rebalance.enable": "all",
    "cluster.routing.allocation.cluster_concurrent_rebalance": 4
  }
}
```

### 10.10 Circuit Breaker Tripped

**Symptom**: `CircuitBreakingException: [parent] Data too large`.

```http
// Check circuit breaker status
GET /_nodes/stats/breaker?human=true

// Adjust if needed (but investigate root cause first)
PUT /_cluster/settings
{
  "persistent": {
    "indices.breaker.total.limit": "70%",
    "indices.breaker.request.limit": "40%",
    "indices.breaker.fielddata.limit": "30%"
  }
}
```

### 10.11 Recovery Taking Too Long

```http
// Check recovery progress
GET /_cat/recovery?v&h=index,shard,type,stage,files_recovered,files_total,bytes_recovered,bytes_total,time

// Increase recovery speed (at the cost of indexing performance)
PUT /_cluster/settings
{
  "transient": {
    "indices.recovery.max_bytes_per_sec": "200mb",
    "cluster.routing.allocation.node_concurrent_recoveries": 4
  }
}
```

---

## 11. FAQ

### Q1: What is the maximum recommended cluster size?

There is no hard limit, but clusters with more than 200 data nodes require careful tuning of master node resources, cluster state publications, and fault detection timeouts. Elastic recommends dedicated master nodes with at least 16 GB heap for large clusters.

### Q2: Should I use one large index or many small time-based indices?

For time-series data (logs, metrics), use data streams or time-based indices with ILM. This enables efficient deletion of old data (delete entire index vs. delete_by_query), appropriate shard sizing for each time period, and hot-warm-cold tiering. For non-time-series data (product catalog, user profiles), use a single index with appropriate shard count.

### Q3: How do I upgrade Elasticsearch without downtime?

Rolling upgrades: upgrade one node at a time, starting with non-master-eligible nodes. Before each restart, disable shard allocation and perform a synced flush. After the node rejoins, re-enable allocation and wait for green before proceeding to the next node. Full-cluster restarts are required only for major version upgrades (6.x to 7.x).

### Q4: What happens when the master node dies?

The remaining master-eligible nodes hold a new election. The node with the highest cluster state version wins. Shard reallocation for the dead node's shards begins automatically after `delayed_timeout` (default 1 minute). During the election (typically <1 second), the cluster does not accept new index creation or mapping changes, but existing indices continue serving reads and writes.

### Q5: Can I change the number of primary shards after index creation?

Not directly. You can use the Split API to increase shards (target must be a multiple of the source) or the Shrink API to decrease them (target must be a divisor of the source). Both create a new index. Alternatively, use the Reindex API to move data to a new index with a different shard count.

### Q6: What is the difference between refresh and flush?

A **refresh** makes new documents searchable by opening a new Lucene segment reader. It does not guarantee durability (data is not fsynced). A **flush** commits all in-memory segments to disk (fsync) and clears the translog. Flush guarantees durability. Refresh happens every 1 second by default; flush happens every 30 minutes or when the translog exceeds its size threshold.

### Q7: How does Elasticsearch handle document updates?

Documents in Lucene are immutable. An update is internally a delete + re-index: the old document is marked as deleted (tombstoned) in its segment, and the new version is indexed into the in-memory buffer. The old document is physically removed during the next segment merge. This is why frequent updates on the same document are more expensive than appends.

### Q8: What is the `_source` field and should I disable it?

`_source` stores the original JSON document as submitted. It is required for update operations, reindex, highlighting, and returning documents in search results. Disabling it saves disk space but makes the index essentially write-only (no updates, no reindex, no full document retrieval). In most cases, keep it enabled. Use `_source` filtering or synthetic `_source` (ES 8.4+) as alternatives.

### Q9: How much RAM does Elasticsearch need?

The rule of thumb: allocate 50% of system RAM to the JVM heap (max 32 GB to stay within compressed oops range), and leave the other 50% for the OS page cache. Lucene relies heavily on memory-mapped files, so the OS page cache is as important as the JVM heap. On a 64 GB server: 32 GB heap + 32 GB page cache. Never give Elasticsearch more than 50% of RAM as heap.

### Q10: What is the impact of too many shards?

Each shard has a fixed overhead: the segment metadata, cluster state entries, and associated thread pool resources. A cluster with 200,000 shards across 50 nodes (4,000 shards/node) experiences slow cluster state updates, high heap usage just for shard metadata, and degraded query performance from the scatter-gather overhead. The Elasticsearch team recommends keeping shards per node under 1,000 and total cluster shards under 50,000 as general guidelines.

### Q11: How do I handle Elasticsearch version upgrades?

Follow the upgrade path: you can only upgrade from one major version to the next (7.x to 8.x, not 6.x to 8.x directly). Within a major version, you can upgrade from any minor to any higher minor. Always check the deprecation log before upgrading: `GET /_migration/deprecations`. Take a snapshot before any upgrade. Use the Upgrade Assistant in Kibana for guided upgrades.

### Q12: Can Elasticsearch replace a relational database?

No. Elasticsearch lacks ACID transactions, foreign key constraints, JOINs across indices (except limited nested/parent-child), and consistent read-after-write semantics. It is not a source of truth for mutable data. Use Elasticsearch as a secondary index for search and analytics, with the relational database as the primary data store. Synchronize via change data capture (Debezium/Kafka Connect) or dual writes.

---

*Questo documento fa parte del modulo 08 "Elasticsearch" della Data Encyclopedia.*
