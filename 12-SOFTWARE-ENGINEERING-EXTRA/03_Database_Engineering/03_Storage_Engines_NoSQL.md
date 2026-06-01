---
corso: "SWE Masterclass"
fase: "3 — Database Engineering"
modulo: "03.3"
titolo: "Storage Engines & NoSQL"
versione: "RocksDB 9.x, Redis 8.x, MongoDB 8.x (WiredTiger), Cassandra 5.x, Neo4j 2026, CockroachDB 24.x, DuckDB 1.5"
livello: "Advanced"
prerequisiti:
  - "Module 3.1 — Relational Database Internals (B-tree pages, buffer pool, WAL)"
  - "Module 3.2 — Distributed Consensus & Replication (quorum writes, Raft/Paxos)"
  - "Operating systems fundamentals (file I/O, memory-mapped files, page cache)"
  - "Familiarity with at least one RDBMS (PostgreSQL or MySQL)"
obiettivi:
  - "Explain LSM-tree write path and quantify write amplification under leveled vs size-tiered compaction"
  - "Compare B-tree, LSM-tree, and columnar storage trade-offs for OLTP, OLAP, and time-series workloads"
  - "Design a data model for document, wide-column, graph, and key-value stores given application access patterns"
  - "Tune RocksDB configuration parameters (MemTable size, compaction strategy, Bloom filter bits) for a given workload profile"
  - "Evaluate NewSQL architectures (CockroachDB, TiDB, Spanner) against traditional sharded RDBMS deployments"
tag: [storage-engines, lsm-tree, b-tree, nosql, rocksdb, mongodb, cassandra, redis, neo4j, columnar, parquet, newsql, cockroachdb, duckdb]
---

# Module 3.3: Storage Engines & NoSQL

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Trace the full write and read paths of an LSM-tree engine, identifying where WAL, MemTable, Bloom filters, and compaction interact
> - Quantify write amplification, read amplification, and space amplification for leveled, size-tiered, and universal compaction strategies
> - Select the appropriate NoSQL data model (document, wide-column, graph, key-value, time-series) based on query patterns, consistency requirements, and scale targets
> - Configure and benchmark RocksDB and WiredTiger for real workloads, interpreting `db_bench` and `mongoperf` output
> - Articulate how NewSQL systems (CockroachDB, TiDB, Spanner) layer SQL semantics over distributed KV storage without sacrificing horizontal scalability

> **Module 03.3** · **Last updated:** 2026-05-22

## Guiding ideas
1. **B-tree (read-optimized) vs LSM (write-optimized).**
2. **Document DB (Mongo) vs Wide-column (Cassandra) vs KV (DynamoDB) vs Graph (Neo4j).**
3. **RocksDB embedded LSM engine (used by many DBs).**
4. **NewSQL (CockroachDB, TiDB, Spanner): SQL + horizontal scale.**

---

## 1. The Write-Optimized Engine: LSM Trees

### 1.1 Fundamental Problem

Traditional B-trees perform random I/O on writes: updating a value means seeking
to the correct page, reading it, modifying it, and writing it back. On HDDs this
is ~10ms per write. On SSDs it is faster but still creates write amplification due
to the erase-before-write nature of flash.

**LSM trees** (Log-Structured Merge-Trees, O'Neil et al., 1996) convert random
writes into sequential writes, which are 10-100x faster on any storage medium.

### 1.2 Architecture

```
┌────────────────────────────────────────────────────────┐
│                      LSM-Tree Architecture              │
│                                                         │
│  ┌──────────────┐                                       │
│  │   Write       │  1. Write → WAL (sequential append)  │
│  │   Request     │  2. Write → MemTable (in-memory)     │
│  └──────┬───────┘                                       │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │    WAL       │    │  MemTable    │  (SkipList or     │
│  │  (Disk,      │    │  (Memory)    │   Red-Black Tree) │
│  │   sequential)│    │  ~64MB       │                   │
│  └──────────────┘    └──────┬───────┘                   │
│                             │  Flush when full           │
│                             ▼                            │
│  ┌──────────────────────────────────────────────┐       │
│  │  Level 0 (L0): Immutable SSTables            │       │
│  │  [SST-1] [SST-2] [SST-3]                    │       │
│  │  May have overlapping key ranges             │       │
│  └──────────────────────────┬───────────────────┘       │
│                             │  Compaction                │
│                             ▼                            │
│  ┌──────────────────────────────────────────────┐       │
│  │  Level 1 (L1): Non-overlapping SSTables      │       │
│  │  [SST-a: keys 0-99] [SST-b: 100-199] [...]  │       │
│  └──────────────────────────┬───────────────────┘       │
│                             │  Compaction                │
│                             ▼                            │
│  ┌──────────────────────────────────────────────┐       │
│  │  Level 2 (L2): Non-overlapping, 10x larger   │       │
│  │  [SST] [SST] [SST] [SST] [SST] [SST] [...]  │       │
│  └──────────────────────────────────────────────┘       │
│                             │                            │
│                             ▼                            │
│  ... Level N (each level ~10x larger)                   │
└────────────────────────────────────────────────────────┘
```

### 1.3 SSTable (Sorted String Table)

Each SSTable is an immutable file containing sorted key-value pairs:

```
┌────────────────────────────────────────────────────────┐
│                    SSTable File                         │
├────────────────────────────────────────────────────────┤
│  Data Block 1   (4-32 KB, sorted KV pairs)             │
│  Data Block 2                                          │
│  Data Block 3                                          │
│  ...                                                   │
│  Data Block N                                          │
├────────────────────────────────────────────────────────┤
│  Meta Block: Bloom Filter                              │
│  Meta Block: Statistics (count, min/max key, etc.)     │
├────────────────────────────────────────────────────────┤
│  Index Block   (maps key prefixes → data block offsets)│
├────────────────────────────────────────────────────────┤
│  Footer        (offsets to index and meta blocks)      │
└────────────────────────────────────────────────────────┘
```

**Properties:**
- Immutable: never modified after creation. Updates create new SSTables.
- Sorted: enables efficient merging (merge sort) and binary search.
- Block-compressed: snappy, lz4, or zstd per data block.

### 1.4 Compaction Strategies

Compaction merges SSTables to remove deleted/overwritten entries and maintain
read performance.

#### Leveled Compaction (RocksDB default)

```
Level 0:  [SST] [SST] [SST]  ← overlapping, from MemTable flushes
          ↓ compact
Level 1:  [A-F] [G-M] [N-Z]  ← non-overlapping, max ~256 MB total
          ↓ compact (pick 1 L1 file + overlapping L2 files)
Level 2:  [A-C] [D-F] [G-I] ... [X-Z]  ← max ~2.5 GB total
          ↓
Level 3:  max ~25 GB
Level 4:  max ~250 GB
...
```

| Metric | Leveled |
|---|---|
| Write amplification | ~10-30x (each entry rewritten per-level) |
| Read amplification | ~1-2 SSTables per level (non-overlapping) |
| Space amplification | ~1.1x (dead entries cleaned promptly) |
| Best for | Read-heavy and space-sensitive workloads |

#### Size-Tiered Compaction (Cassandra default)

```
Tier 1:  [64MB] [64MB] [64MB] [64MB]
         ↓ merge when 4 files of similar size
Tier 2:  [256MB] [256MB] [256MB] [256MB]
         ↓ merge
Tier 3:  [1GB] [1GB] [1GB] [1GB]
         ↓
Tier 4:  [4GB] ...
```

| Metric | Size-Tiered |
|---|---|
| Write amplification | ~4-8x (merged less frequently) |
| Read amplification | ~N/tier (key might be in any file of a tier) |
| Space amplification | ~2x (old data kept until merged) |
| Best for | Write-heavy workloads, time-series |

#### FIFO Compaction

Files are deleted (not merged) when they exceed a configured TTL or total size.
Used for time-series data where old data is simply discarded.

#### Universal Compaction (RocksDB)

A hybrid between leveled and size-tiered. Compacts files based on space
amplification ratio, targeting a balance between write amp and space amp.

### 1.5 Bloom Filters

**Problem:** A point lookup must potentially check every level (L0 through LN)
until the key is found. Without optimization, this is slow.

**Solution:** Each SSTable contains a Bloom filter in its metadata block.

```
Bloom Filter (m bits, k hash functions):

Insert "key_X":
  h1("key_X") % m → set bit 42
  h2("key_X") % m → set bit 157
  h3("key_X") % m → set bit 891

Lookup "key_Y":
  h1("key_Y") % m → bit 42 set? YES
  h2("key_Y") % m → bit 157 set? NO → DEFINITELY NOT IN THIS SST

  Result: skip this SSTable entirely (saved one disk read)

False positive rate: ~1% with 10 bits/key
                     ~0.1% with 14 bits/key
```

**RocksDB optimization:** Full Bloom filter for the whole SSTable, plus
prefix Bloom filters for range queries (`Iterator::Seek(prefix)`).

### 1.6 Read Path

```
Point Lookup for key K:

1. Check MemTable (in-memory, O(log n))
   ├── Found → return
   └── Not found ↓

2. Check Immutable MemTable (if one is being flushed)
   ├── Found → return
   └── Not found ↓

3. Check L0 SSTables (newest first, may need to check all)
   For each L0 SSTable:
     ├── Check Bloom filter → "definitely not here" → skip
     ├── Check Bloom filter → "maybe here"
     │   └── Binary search index block → read data block → check
     ├── Found → return
     └── Not found → next SSTable

4. Check L1..LN (at most one SSTable per level due to non-overlap)
   For each level:
     ├── Binary search file boundaries to find candidate SSTable
     ├── Check Bloom filter → skip or proceed
     ├── Found → return
     └── Not found → next level

5. Key does not exist → return "not found"
```

### 1.7 Write Amplification

Write amplification = total bytes written to storage / bytes written by application.

```
Example with leveled compaction (size ratio = 10):

Application writes 1 byte:
  Written to WAL:        1 byte
  Written to MemTable:   (memory, not counted)
  Flushed to L0:         1 byte
  Compacted L0→L1:       1 byte (but sorted with L1 data)
  Compacted L1→L2:       1 byte
  Compacted L2→L3:       1 byte
  ...

Total: ~10-30 bytes written per application byte
```

This is the fundamental cost of LSM trees: trading write amplification for
sequential I/O and read performance.

### 1.8 RocksDB Configuration Tuning

```cpp
// Key RocksDB options:
options.write_buffer_size = 64 << 20;           // 64 MB MemTable
options.max_write_buffer_number = 3;            // allow 3 MemTables
options.level0_file_num_compaction_trigger = 4; // compact when 4 L0 files
options.max_bytes_for_level_base = 256 << 20;   // 256 MB for L1
options.max_bytes_for_level_multiplier = 10;    // L2 = 2.5 GB, L3 = 25 GB
options.target_file_size_base = 64 << 20;       // 64 MB per SSTable
options.compression = kLZ4Compression;          // fast compression
options.bottommost_compression = kZSTD;         // best ratio for cold data
options.bloom_bits_per_key = 10;                // ~1% false positive rate
```

---

## 2. The Read-Optimized Engine: B-Trees

### 2.1 B-Tree Structure (InnoDB)

InnoDB (MySQL's default storage engine) uses a B+ tree as its primary storage
structure with a **clustered index** — the table data is stored directly in the
leaf nodes of the primary key index.

```
InnoDB Clustered Index:

              ┌──────────────────────┐
              │   Root Page          │
              │   [PK: 50, 100]      │
              └──┬──────────┬───┬────┘
                 │          │   │
    ┌────────────┘    ┌─────┘   └─────────┐
    ▼                 ▼                    ▼
┌────────────┐  ┌────────────┐  ┌────────────────┐
│ PK < 50    │  │ 50 ≤ PK    │  │ PK ≥ 100       │
│ Leaf: rows │  │  < 100     │  │ Leaf: rows      │
│ [1,Alice]  │  │ Leaf: rows │  │ [100,Eve,...]   │
│ [2,Bob,..]│  │ [50,Carol] │  │ [150,Frank,..] │
│ [3,Carol] │  │ [75,Dave]  │  │                  │
└────────────┘  └────────────┘  └────────────────┘
      ↕ linked         ↕ linked         ↕ linked
```

**Secondary indexes** in InnoDB store the primary key value (not a row pointer)
in their leaf nodes. A secondary index lookup requires two B-tree traversals:
1. Search secondary index → get primary key
2. Search clustered index → get row data

This is called a **double lookup** or **bookmark lookup**.

### 2.2 InnoDB Page Structure

InnoDB uses 16 KB pages (vs. PostgreSQL's 8 KB):

```
┌──────────────────────────────────────────────────┐
│  FIL Header (38 bytes)                            │
│  ├── space_id, page_number, prev/next page        │
│  └── checksum, LSN                                │
├──────────────────────────────────────────────────┤
│  Page Header (56 bytes)                           │
│  ├── number of records, heap_top                  │
│  └── page direction (left/right), level            │
├──────────────────────────────────────────────────┤
│  Infimum Record (smallest possible record)        │
│  Supremum Record (largest possible record)        │
├──────────────────────────────────────────────────┤
│  User Records (sorted by key within page)         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │ Record 1│→│ Record 2│→│ Record 3│→ Supremum  │
│  └─────────┘ └─────────┘ └─────────┘            │
├──────────────────────────────────────────────────┤
│  Free Space                                       │
├──────────────────────────────────────────────────┤
│  Page Directory (sparse index of records)         │
├──────────────────────────────────────────────────┤
│  FIL Trailer (8 bytes: checksum + LSN)            │
└──────────────────────────────────────────────────┘
```

### 2.3 InnoDB Buffer Pool

Equivalent to PostgreSQL's shared_buffers but with different eviction:

- Uses a **modified LRU** with a midpoint insertion strategy.
- New pages are inserted at the 3/8 point (not the head) of the LRU list.
- Pages must survive a configurable time window before being promoted to the
  "young" (hot) sublist.
- This prevents full table scans from evicting frequently accessed pages.

```
# my.cnf
innodb_buffer_pool_size = 24G       # 70-80% of RAM for dedicated DB server
innodb_buffer_pool_instances = 8    # reduce contention on large pools
```

### 2.4 InnoDB Double Write Buffer

InnoDB's defense against torn pages (partial writes):

```
Write path:
1. Modified page in buffer pool
2. Write page to double-write buffer (sequential, 2 MB region on disk)
3. fsync the double-write buffer
4. Write page to its actual location in the tablespace
5. If crash during step 4 → recover from double-write buffer
```

PostgreSQL uses Full Page Images in WAL instead (different trade-off: more WAL
volume, simpler recovery).

### 2.5 WiredTiger (MongoDB)

MongoDB's storage engine since 3.2. Supports both B-tree and LSM-tree, but
defaults to B-tree.

**Key features:**
- **Document-level concurrency control** (not collection-level)
- **Prefix compression** for keys in B-tree pages
- **Block compression** (snappy by default, zlib or zstd optional)
- **Multi-version concurrency:** Reads see a consistent snapshot
- **Hazard pointers** for lock-free read access to pages

```
// MongoDB storage engine configuration:
storage:
  engine: wiredTiger
  wiredTiger:
    engineConfig:
      cacheSizeGB: 8
    collectionConfig:
      blockCompressor: zstd
    indexConfig:
      prefixCompression: true
```

### 2.6 B-Tree vs. LSM-Tree Comparison

| Dimension | B-Tree | LSM-Tree |
|---|---|---|
| Write pattern | Random I/O (in-place update) | Sequential I/O (append + compact) |
| Read pattern | Single tree traversal | Multi-level search |
| Write amplification | ~2-5x | ~10-30x (leveled) / ~4-8x (tiered) |
| Read amplification | 1 (one tree) | 1-N (multiple levels) |
| Space amplification | ~1.5-2x (page fill factor) | ~1.1x (leveled) / ~2x (tiered) |
| Point reads | Excellent (O(log N)) | Good (Bloom filter helps) |
| Range scans | Excellent (linked leaves) | Good (merge across levels) |
| Write throughput | Lower (random I/O) | Higher (sequential I/O) |
| Predictable latency | Yes | Compaction spikes |
| Space reclamation | Immediate (in-place) | Deferred (compaction) |

**When to choose B-tree:** Read-heavy OLTP, need predictable latency, moderate
write throughput sufficient.

**When to choose LSM:** Write-heavy workloads, time-series, high-throughput
ingestion, can tolerate compaction latency spikes.

---

## 3. Column Stores

### 3.1 Why Columns?

Analytical queries typically access a small subset of columns across many rows:

```sql
SELECT region, SUM(revenue)
FROM sales
WHERE year = 2025
GROUP BY region;

Row-store: reads ALL columns for every row (customer_name, address,
           phone, ... even though the query only needs region + revenue)
           → 95% wasted I/O

Column-store: reads only the region and revenue columns
              → minimal I/O, high cache efficiency
```

### 3.2 Column Store Layout

```
Row-store on disk:
  Page 1: [1, Alice, NY, 100] [2, Bob, CA, 200] [3, Carol, NY, 150]
  Page 2: [4, Dave, TX, 300] [5, Eve, CA, 250] ...

Column-store on disk:
  Column "id":      [1, 2, 3, 4, 5, ...]
  Column "name":    [Alice, Bob, Carol, Dave, Eve, ...]
  Column "region":  [NY, CA, NY, TX, CA, ...]
  Column "revenue": [100, 200, 150, 300, 250, ...]

  Each column file is sorted by the same row order
  Row N in each column file corresponds to the same logical row
```

### 3.3 Compression Techniques

Column data is highly compressible because adjacent values are the same type and
often similar:

#### Run-Length Encoding (RLE)

```
Input:  [NY, NY, NY, CA, CA, TX, TX, TX, TX]
Output: [(NY, 3), (CA, 2), (TX, 4)]

Best for: Low-cardinality columns sorted by this column
Compression ratio: potentially 100x+ for sorted data
```

#### Dictionary Encoding

```
Dictionary: {NY → 0, CA → 1, TX → 2}

Input:  [NY, CA, NY, TX, CA, NY, TX, TX]
Output: [0, 1, 0, 2, 1, 0, 2, 2]

Now each value is 2 bits instead of variable-length string
Can apply further encoding (bit-packing, RLE) on the integer codes
```

#### Delta Encoding

```
Input (timestamps):  [1000, 1005, 1012, 1015, 1020]
Deltas:              [1000, +5, +7, +3, +5]

Delta-of-delta:      [1000, 5, +2, -4, +2]

Small integers → fewer bits → better compression
Used by: time-series databases, Gorilla encoding (Facebook)
```

#### Bit-Packing

```
Values range [0, 15] → 4 bits per value
Pack 8 values into 4 bytes (32 bits)
Instead of 8 × 4 bytes = 32 bytes (int32 per value)

Compression: 8x for this example
```

### 3.4 Parquet File Format

Apache Parquet is the dominant open columnar file format for data lakes:

```
┌────────────────────────────────────────────────────┐
│                  Parquet File                       │
├────────────────────────────────────────────────────┤
│  Magic Number: "PAR1"                              │
├────────────────────────────────────────────────────┤
│  Row Group 1 (~128 MB of uncompressed data)        │
│  ├── Column Chunk: id                              │
│  │   ├── Page 1 (data page, ~1 MB compressed)     │
│  │   ├── Page 2                                    │
│  │   └── ...                                       │
│  ├── Column Chunk: name                            │
│  │   ├── Page 1                                    │
│  │   └── ...                                       │
│  ├── Column Chunk: region                          │
│  └── Column Chunk: revenue                         │
├────────────────────────────────────────────────────┤
│  Row Group 2                                       │
│  ├── Column Chunk: id                              │
│  ├── ...                                           │
├────────────────────────────────────────────────────┤
│  Footer                                            │
│  ├── File Metadata                                 │
│  │   ├── Schema (column names, types, encoding)    │
│  │   ├── Row group metadata                        │
│  │   │   ├── Column chunk offsets                  │
│  │   │   ├── Column statistics (min, max, null_count) │
│  │   │   └── Encodings used                        │
│  │   └── Key-value metadata (custom properties)    │
│  ├── Footer length (4 bytes)                       │
│  └── Magic Number: "PAR1"                          │
└────────────────────────────────────────────────────┘
```

**Reading strategy:**
1. Read footer (last few bytes) → get schema + row group metadata.
2. Use column statistics (min/max per row group) to skip irrelevant row groups.
3. Read only the column chunks needed by the query.
4. Decompress and decode at the page level.

### 3.5 ORC (Optimized Row Columnar)

Competing format from the Hive ecosystem:

| Feature | Parquet | ORC |
|---|---|---|
| Origin | Twitter/Cloudera | Facebook/Hortonworks |
| Nested data | Dremel encoding (repetition/definition levels) | Flattened structs |
| Compression | Snappy, Gzip, LZ4, Zstd | Zlib, Snappy, LZ4, Zstd |
| Statistics | Column chunk level | Stripe + row index level |
| Predicate pushdown | Via min/max statistics | Via min/max + Bloom filters |
| Ecosystem | Spark, Presto, DuckDB, BigQuery | Hive, Presto, Spark |

Both are excellent. Parquet has wider ecosystem adoption; ORC has slightly better
compression in some workloads due to its lightweight indexing.

### 3.6 Vectorized Execution

```
Traditional execution (Volcano model, row-at-a-time):

  for each row in column_chunk:
      if row.region == 'NY':           ← branch per row
          sum += row.revenue           ← function call per row

Vectorized execution (batch-at-a-time):

  region_batch = read_batch(region_column, 1024)  ← 1024 values
  mask = SIMD_compare_eq(region_batch, 'NY')      ← single SIMD instruction
  revenue_batch = read_batch(revenue_column, 1024)
  sum += SIMD_masked_sum(revenue_batch, mask)      ← single SIMD instruction

  Speedup: 10-50x due to:
  - Eliminated per-row function call overhead
  - Branch-free SIMD comparisons
  - Cache-friendly sequential access
  - CPU pipeline stays full (no branch mispredictions)
```

**Systems using vectorized execution:**

| System | Implementation |
|---|---|
| ClickHouse | Custom vectorized engine from the start |
| DuckDB | Vectorized push-based execution |
| Velox (Meta) | Vectorized library used by Presto/Spark |
| DataFusion (Apache Arrow) | Vectorized + JIT via Arrow |
| PostgreSQL | Column-oriented storage via columnar extensions |

---

## 4. Document Model (MongoDB)

### 4.1 Data Model

Documents are schema-flexible JSON-like objects (BSON in MongoDB):

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "name": "Alice",
  "email": "alice@example.com",
  "addresses": [
    {
      "type": "home",
      "street": "123 Main St",
      "city": "Portland",
      "state": "OR"
    },
    {
      "type": "work",
      "street": "456 Office Ave",
      "city": "Portland",
      "state": "OR"
    }
  ],
  "orders": [
    {"product": "Widget", "qty": 5, "price": 9.99},
    {"product": "Gadget", "qty": 1, "price": 49.99}
  ]
}
```

**Advantages over relational:**
- Related data co-located in one document → single read for the full entity
- No JOINs needed for entity retrieval
- Schema evolution without ALTER TABLE (add fields freely)
- Natural mapping to application objects (less ORM friction)

**Disadvantages:**
- Many-to-many relationships require denormalization or manual references
- Updating deeply nested fields is complex
- No cross-document transactions (until MongoDB 4.0 added multi-document ACID)
- Document size limit (16 MB in MongoDB)

### 4.2 Indexing in MongoDB

```javascript
// Single field index:
db.users.createIndex({ email: 1 })  // 1 = ascending

// Compound index:
db.users.createIndex({ status: 1, created_at: -1 })

// Multikey index (arrays):
db.users.createIndex({ "tags": 1 })
// Automatically creates one index entry per array element

// Text index:
db.articles.createIndex({ title: "text", body: "text" })

// Geospatial index:
db.places.createIndex({ location: "2dsphere" })

// Wildcard index (schema-flexible):
db.products.createIndex({ "attributes.$**": 1 })
// Indexes all fields under "attributes" regardless of their names

// Partial index:
db.orders.createIndex(
  { status: 1 },
  { partialFilterExpression: { status: "active" } }
)
```

### 4.3 Aggregation Pipeline

MongoDB's equivalent to SQL GROUP BY, JOINs, and subqueries:

```javascript
db.orders.aggregate([
  // Stage 1: Filter
  { $match: { status: "completed", date: { $gte: ISODate("2026-01-01") } } },

  // Stage 2: Lookup (LEFT JOIN equivalent)
  { $lookup: {
      from: "customers",
      localField: "customer_id",
      foreignField: "_id",
      as: "customer"
  }},

  // Stage 3: Unwind (flatten array)
  { $unwind: "$customer" },

  // Stage 4: Group (aggregate)
  { $group: {
      _id: "$customer.region",
      total_revenue: { $sum: "$total" },
      order_count: { $count: {} },
      avg_order: { $avg: "$total" }
  }},

  // Stage 5: Sort
  { $sort: { total_revenue: -1 } },

  // Stage 6: Limit
  { $limit: 10 }
])
```

### 4.4 Sharding

MongoDB distributes data across shards using a shard key:

```
┌────────────────────────────────────────────────────┐
│                    mongos (router)                   │
│  Routes queries to correct shard based on shard key │
└──────────┬───────────────┬───────────────┬──────────┘
           │               │               │
    ┌──────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
    │  Shard 1    │ │  Shard 2    │ │  Shard 3    │
    │  user_id    │ │  user_id    │ │  user_id    │
    │  [0-333]    │ │  [334-666]  │ │  [667-999]  │
    │  (replica   │ │  (replica   │ │  (replica   │
    │   set)      │ │   set)      │ │   set)      │
    └─────────────┘ └─────────────┘ └─────────────┘
```

**Shard key strategies:**

| Strategy | Pros | Cons |
|---|---|---|
| Hashed shard key | Even distribution | No range queries on shard key |
| Range shard key | Range queries stay on one shard | Hotspotting on sequential keys |
| Zone sharding | Data locality (EU data in EU shard) | Uneven distribution possible |

---

## 5. Wide-Column Model (Cassandra, HBase)

### 5.1 Data Model

Wide-column stores organize data as rows of column families, where each row can
have different columns:

```
Cassandra data model:

Keyspace: "ecommerce"
  Table: "user_activity"
    Partition Key: user_id
    Clustering Key: timestamp (DESC)

    ┌────────────────────────────────────────────────────┐
    │ Partition: user_id = "alice"                        │
    │                                                     │
    │  timestamp (cluster)  │ event_type │ page   │ dur  │
    │  2026-05-22 14:30:00 │ click      │ /home  │ 5s   │
    │  2026-05-22 14:25:00 │ view       │ /cart  │ 30s  │
    │  2026-05-22 14:20:00 │ click      │ /prod  │ 2s   │
    └────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────┐
    │ Partition: user_id = "bob"                          │
    │                                                     │
    │  timestamp (cluster)  │ event_type │ page   │ meta │
    │  2026-05-22 15:00:00 │ purchase   │ /pay   │ {...}│
    └────────────────────────────────────────────────────┘
```

### 5.2 Cassandra Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Cassandra Ring                         │
│                                                          │
│              Node A (token: 0-25)                        │
│             /                    \                       │
│    Node F                        Node B                  │
│   (75-100)                      (25-50)                 │
│     |                              |                     │
│    Node E                        Node C                  │
│   (63-75)                       (50-63)                 │
│             \                    /                       │
│              Node D (...)                                │
│                                                          │
│  Each node owns a token range                            │
│  Data is replicated to RF=3 next nodes                   │
└─────────────────────────────────────────────────────────┘
```

**Write path:**

```
Client write:
  1. Any node can receive write (coordinator)
  2. Coordinator computes partition hash → identifies replica nodes
  3. Sends write to all RF replicas
  4. Waits for CL (Consistency Level) acknowledgments:
     - ONE:    1 replica ACK    (fastest, least durable)
     - QUORUM: RF/2 + 1 ACKs   (balanced)
     - ALL:    all RF ACKs      (slowest, most durable)
  5. Returns success to client

On each replica:
  1. Write to commit log (WAL equivalent)
  2. Write to MemTable
  3. MemTable flushes to SSTable when full
  4. Compaction merges SSTables (size-tiered by default)
```

### 5.3 Cassandra Data Modeling Rules

Cassandra data modeling is **query-driven**, not entity-driven:

```
Rule 1: Know your queries before designing tables.
Rule 2: One table per query pattern.
Rule 3: Denormalize aggressively (no JOINs exist).
Rule 4: Partition key determines data distribution.
Rule 5: Clustering key determines sort order within partition.
Rule 6: Keep partitions under 100 MB (recommended).
```

```sql
-- Query: "Get all orders for user X in the last 30 days"
CREATE TABLE orders_by_user (
    user_id     uuid,
    order_date  timestamp,
    order_id    uuid,
    total       decimal,
    status      text,
    PRIMARY KEY (user_id, order_date, order_id)
) WITH CLUSTERING ORDER BY (order_date DESC, order_id ASC);

-- Query: "Get all orders with status 'pending'"
-- Needs a SEPARATE table (Cassandra cannot efficiently filter by status
-- on the orders_by_user table)
CREATE TABLE orders_by_status (
    status      text,
    order_date  timestamp,
    order_id    uuid,
    user_id     uuid,
    total       decimal,
    PRIMARY KEY (status, order_date, order_id)
) WITH CLUSTERING ORDER BY (order_date DESC);
```

### 5.4 HBase

Apache HBase is the wide-column store in the Hadoop ecosystem:

| Feature | Cassandra | HBase |
|---|---|---|
| Architecture | Peer-to-peer (no master) | Master-slave (RegionServer) |
| Consistency | Tunable (ONE to ALL) | Strong (single RegionServer per region) |
| Storage | LSM on local disk | LSM on HDFS |
| Availability | AP (highly available) | CP (RegionServer failure = unavailability) |
| Query language | CQL (SQL-like) | Java API, Thrift, REST |
| Use cases | High-write, global distribution | Hadoop integration, HBase-on-HDFS |

---

## 6. Graph Storage

### 6.1 Property Graph Model

```
Nodes and relationships with properties:

  ┌───────────────┐     WORKS_AT (since: 2020)     ┌──────────────┐
  │ Person        │ ─────────────────────────────► │ Company      │
  │ name: Alice   │                                 │ name: Acme   │
  │ age: 30       │                                 │ industry: SW │
  └───────┬───────┘                                 └──────────────┘
          │
          │ FRIENDS_WITH (since: 2018)
          │
          ▼
  ┌───────────────┐
  │ Person        │
  │ name: Bob     │
  │ age: 28       │
  └───────────────┘
```

### 6.2 Neo4j (Index-Free Adjacency)

Neo4j stores relationships as physical pointers between nodes:

```
Node Record (fixed 15 bytes):
  ┌────────────────────────────────────────────┐
  │ in_use │ first_rel_id │ first_prop_id │ labels │
  └────────────────────────────────────────────┘

Relationship Record (fixed 34 bytes):
  ┌─────────────────────────────────────────────────────────┐
  │ start_node │ end_node │ type │ start_prev │ start_next │
  │ end_prev │ end_next │ first_prop_id                     │
  └─────────────────────────────────────────────────────────┘
```

**Index-free adjacency:** Traversing from node A to its neighbors is O(1) per
relationship — just follow the pointer. No index lookup needed. This makes
multi-hop traversals dramatically faster than JOINs in a relational database.

```
Relational (3-hop social query):
  SELECT DISTINCT f3.name
  FROM friendships f1
  JOIN friendships f2 ON f1.friend_id = f2.user_id
  JOIN friendships f3 ON f2.friend_id = f3.user_id
  WHERE f1.user_id = 1;
  -- Cost: 3 index lookups × cardinality per level
  -- 1000 friends → 1000 × 1000 × 1000 = 1 billion row lookups

Graph (Neo4j):
  MATCH (p:Person {name: "Alice"})-[:FRIENDS*3]-(friend)
  RETURN DISTINCT friend.name
  -- Cost: follow pointers, no index needed
  -- 1000 friends → 1000 + 1000 + 1000 pointer traversals
```

### 6.3 Cypher Query Language

```cypher
// Find shortest path between two people:
MATCH path = shortestPath(
  (a:Person {name: "Alice"})-[:FRIENDS*..6]-(b:Person {name: "Eve"})
)
RETURN path

// Recommendation: people who like what my friends like:
MATCH (me:Person {name: "Alice"})-[:FRIENDS]->(friend)-[:LIKES]->(item)
WHERE NOT (me)-[:LIKES]->(item)
RETURN item.name, count(friend) AS num_friends_who_like
ORDER BY num_friends_who_like DESC
LIMIT 10

// Fraud detection: cyclic money transfers:
MATCH (a)-[:TRANSFER]->(b)-[:TRANSFER]->(c)-[:TRANSFER]->(a)
WHERE a.amount > 10000
RETURN a, b, c
```

### 6.4 Graph Storage Alternatives

| System | Storage | Query Language | Best for |
|---|---|---|---|
| Neo4j | Native graph (index-free adjacency) | Cypher | OLTP graph queries |
| Amazon Neptune | Native graph | Gremlin, SPARQL, openCypher | Managed graph DB |
| JanusGraph | Pluggable (Cassandra, HBase, etc.) | Gremlin | Distributed graphs |
| ArangoDB | Multi-model (doc + graph + KV) | AQL | Polyglot applications |
| DGraph | Native, distributed | GraphQL+/- DQL | Distributed graph |
| PostgreSQL + AGE | Relational with graph extension | openCypher | Adding graph to existing PG |

---

## 7. Time-Series Storage

### 7.1 Characteristics of Time-Series Data

```
Typical time-series record:
  (timestamp, metric_name, tags, value)
  (2026-05-22T14:30:00Z, "cpu.usage", {host: "web-1", dc: "us-east"}, 78.5)

Properties:
  - Append-mostly (rarely update historical data)
  - Natural ordering by time
  - High write throughput (millions of points/second)
  - Queries are range-based (last hour, last day, last month)
  - Old data can be downsampled or expired
  - High compression potential (delta encoding on timestamps, values)
```

### 7.2 Storage Strategies

#### Gorilla Compression (Facebook, 2015)

Used by Prometheus (TSDB), VictoriaMetrics, and others:

```
Timestamp compression (delta-of-delta):
  t0 = 1716393000
  t1 = 1716393060  → δ = 60
  t2 = 1716393120  → δ = 60  → δδ = 0  → encode as 1 bit (0)
  t3 = 1716393180  → δ = 60  → δδ = 0  → encode as 1 bit (0)
  t4 = 1716393300  → δ = 120 → δδ = 60 → encode with value bits

Value compression (XOR encoding):
  v0 = 78.5  (IEEE 754: 0x4053A00000000000)
  v1 = 78.7  (XOR with v0 = sparse bits)
  → Encode: leading zeros, meaningful bits, trailing zeros
  → Consecutive similar values compress to ~1-2 bits each

Result: 12x compression vs. raw storage
```

#### LSM-Based (InfluxDB, TimescaleDB)

```
InfluxDB (TSI - Time Structured Merge):
  Shard per time range (e.g., 1 week)
  Within shard: TSM files (columnar, compressed)
  
  ┌──────────────────┐
  │ Shard: May 15-21  │  ← actively writing
  │ Shard: May 8-14   │  ← read-only, compacting
  │ Shard: May 1-7    │  ← cold, may be downsampled
  │ ...               │
  └──────────────────┘
  
  Old shards can be moved to cheaper storage or deleted entirely
```

### 7.3 Time-Series Databases Comparison

| System | Storage Engine | Query Language | Clustering | Best for |
|---|---|---|---|---|
| Prometheus | Custom TSDB (Gorilla) | PromQL | Federation | Kubernetes metrics |
| InfluxDB | TSM (custom LSM) | InfluxQL / Flux | Enterprise only | IoT, infrastructure |
| TimescaleDB | PostgreSQL extension | SQL | Multi-node | SQL-native, complex queries |
| VictoriaMetrics | Gorilla + LSM hybrid | MetricsQL (PromQL superset) | Built-in | High-cardinality Prometheus |
| ClickHouse | MergeTree (LSM variant) | SQL | Built-in | Analytics on time-series |
| QuestDB | Column-store, memory-mapped | SQL | Single node | Low-latency ingestion |

---

## 8. Key-Value Stores

### 8.1 Pure Key-Value

The simplest NoSQL model: `get(key) → value`, `put(key, value)`, `delete(key)`.

```
┌────────────────────────────────────────────────────────┐
│  Key-Value Store                                        │
│                                                         │
│  Key              │ Value                               │
│  ─────────────────┼───────────────────────────────────  │
│  "user:1001"      │ {"name":"Alice","email":"a@b.com"} │
│  "session:abc123" │ {"user_id":1001,"expires":16...}   │
│  "cache:product:5"│ <serialized Product object>        │
└────────────────────────────────────────────────────────┘
```

### 8.2 Redis

In-memory key-value store with rich data structures:

```
Data structures:
  String:    SET key "value"          GET key
  Hash:      HSET user:1 name Alice   HGETALL user:1
  List:      LPUSH queue job1         RPOP queue
  Set:       SADD tags:post1 go rust  SMEMBERS tags:post1
  Sorted Set: ZADD leaderboard 100 alice  ZRANGE leaderboard 0 9 WITHSCORES
  Stream:    XADD events * key val    XRANGE events - +
  HyperLogLog: PFADD visitors user1  PFCOUNT visitors
  Bitmap:    SETBIT active:2026-05-22 1001 1  BITCOUNT active:2026-05-22
```

**Persistence options:**

| Mode | Mechanism | Trade-off |
|---|---|---|
| RDB | Point-in-time snapshots (fork + serialize) | Fast recovery, data loss between snapshots |
| AOF | Append-only file (log every write) | Durability, slower recovery |
| RDB + AOF | Both | Best durability + fast recovery |
| None | In-memory only | Cache use case, no persistence |

**Redis Cluster:**

```
Hash slots: 16384 slots distributed across nodes
Key → CRC16(key) % 16384 → slot → node

Node A: slots 0-5460
Node B: slots 5461-10922
Node C: slots 10923-16383

Each node has replicas for failover
Gossip-based cluster bus for health and slot assignment
```

### 8.3 DynamoDB

AWS managed key-value + document store:

```
Table: Orders
  Partition Key: user_id (hash)
  Sort Key: order_date (range)

  ┌──────────┬──────────────┬─────────┬────────┐
  │ user_id  │ order_date   │ total   │ status │
  │ (PK)     │ (SK)         │         │        │
  ├──────────┼──────────────┼─────────┼────────┤
  │ alice    │ 2026-05-01   │ 99.99   │ done   │
  │ alice    │ 2026-05-15   │ 49.99   │ active │
  │ bob      │ 2026-05-10   │ 149.99  │ done   │
  └──────────┴──────────────┴─────────┴────────┘
```

**Capacity modes:**

| Mode | Pricing | Best for |
|---|---|---|
| Provisioned | Fixed RCU/WCU per table | Predictable workloads |
| On-Demand | Per-request pricing | Spiky/unpredictable workloads |

**Global Secondary Index (GSI):** Project data into a new table with a different
partition key. Eventually consistent. Creates a separate partition structure.

**Local Secondary Index (LSI):** Same partition key, different sort key. Strongly
consistent. Must be created at table creation time.

---

## 9. NewSQL: SQL + Horizontal Scale

### 9.1 The Problem

Traditional RDBMS (PostgreSQL, MySQL): strong consistency, rich SQL, but single-node
or limited read replicas. Cannot horizontally scale writes.

NoSQL (Cassandra, DynamoDB): horizontal scale, but limited query capabilities, no
multi-row ACID transactions, denormalized data models.

**NewSQL** systems aim for both: distributed SQL with ACID transactions and horizontal
write scaling.

### 9.2 Google Spanner

The original globally-distributed NewSQL database:

```
┌────────────────────────────────────────────────────────┐
│                   Google Spanner                        │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Zone A      │  │  Zone B      │  │  Zone C      │  │
│  │  (us-east)   │  │  (eu-west)   │  │  (asia-east) │  │
│  │              │  │              │  │              │    │
│  │  SpanServer  │  │  SpanServer  │  │  SpanServer  │  │
│  │  SpanServer  │  │  SpanServer  │  │  SpanServer  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                         │
│  TrueTime: GPS + atomic clocks → bounded uncertainty    │
│  Consensus: Paxos per split (partition)                  │
│  Transactions: 2PC across Paxos groups                   │
└────────────────────────────────────────────────────────┘
```

**TrueTime API:**

```
TT.now() → [earliest, latest]

Uncertainty interval: typically ε ≈ 7ms
Commit rule: wait out the uncertainty before declaring commit
  → External consistency: if T1 commits before T2 starts (wall clock),
    T1's timestamp < T2's timestamp (guaranteed)
```

### 9.3 CockroachDB

Open-source Spanner-inspired system:

- **Storage:** RocksDB (per-range) → Pebble (custom Go LSM, replaced RocksDB)
- **Consensus:** Raft per range (default 512 MB ranges)
- **Transactions:** Serializable by default, distributed MVCC
- **SQL:** PostgreSQL wire protocol compatible
- **Clock:** HLC (no GPS/atomic clocks → larger clock offset tolerance)

```sql
-- CockroachDB SQL (PostgreSQL compatible):
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    total DECIMAL(10,2) NOT NULL,
    region STRING NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    INDEX idx_customer (customer_id),
    INDEX idx_region_date (region, created_at DESC)
);

-- Geo-partitioning:
ALTER TABLE orders PARTITION BY LIST (region) (
    PARTITION us VALUES IN ('us-east', 'us-west'),
    PARTITION eu VALUES IN ('eu-west', 'eu-central')
);

ALTER PARTITION us OF TABLE orders
    CONFIGURE ZONE USING constraints = '[+region=us]';
ALTER PARTITION eu OF TABLE orders
    CONFIGURE ZONE USING constraints = '[+region=eu]';
```

### 9.4 TiDB

PingCAP's NewSQL database, MySQL compatible:

```
┌────────────────────────────────────────────────────────┐
│                      TiDB Architecture                  │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  TiDB     │  │  TiDB     │  │  TiDB     │  (SQL)    │
│  │  Server   │  │  Server   │  │  Server   │           │
│  └────┬──────┘  └────┬──────┘  └────┬──────┘           │
│       │              │              │                    │
│  ┌────▼──────────────▼──────────────▼──────┐           │
│  │              PD (Placement Driver)       │           │
│  │     Timestamp Oracle + Scheduling        │           │
│  └──────────────────┬──────────────────────┘           │
│                     │                                    │
│  ┌──────────┐  ┌────▼─────┐  ┌──────────┐             │
│  │  TiKV     │  │  TiKV     │  │  TiKV     │  (Storage)│
│  │ (RocksDB  │  │ (RocksDB  │  │ (RocksDB  │           │
│  │  + Raft)  │  │  + Raft)  │  │  + Raft)  │           │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                         │
│  TiFlash: columnar replicas for OLAP (HTAP)            │
└────────────────────────────────────────────────────────┘
```

### 9.5 NewSQL Comparison

| Feature | Spanner | CockroachDB | TiDB | YugabyteDB |
|---|---|---|---|---|
| Wire protocol | gRPC | PostgreSQL | MySQL | PostgreSQL |
| Storage | Colossus + LSM | Pebble (LSM) | TiKV (RocksDB) | DocDB (RocksDB) |
| Consensus | Paxos | Raft | Raft | Raft |
| Clock | TrueTime (GPS) | HLC | TSO (centralized) | HLC |
| Default isolation | External consistency | Serializable | Snapshot | Snapshot |
| HTAP | Yes (built-in) | Limited | TiFlash | Limited |
| Deployment | GCP only | Any cloud/on-prem | Any cloud/on-prem | Any cloud/on-prem |

---

## 10. Choosing the Right Storage Engine

### 10.1 Decision Framework

```
Start Here:
│
├── Need ACID transactions?
│   ├── Single-node sufficient?
│   │   ├── Yes → PostgreSQL / MySQL
│   │   └── No → CockroachDB / TiDB / Spanner
│   └── No → continue
│
├── Access pattern?
│   ├── Key-value lookups → Redis (in-memory) / DynamoDB (persistent)
│   ├── Document retrieval → MongoDB
│   ├── Wide-column (time-series, IoT) → Cassandra / ScyllaDB
│   ├── Graph traversals → Neo4j
│   ├── Full-text search → Elasticsearch / OpenSearch
│   ├── Time-series metrics → Prometheus / InfluxDB / TimescaleDB
│   └── Analytics / OLAP → ClickHouse / DuckDB / Snowflake
│
├── Write-heavy or read-heavy?
│   ├── Write-heavy → LSM-based (RocksDB, Cassandra)
│   └── Read-heavy → B-tree based (PostgreSQL, MySQL)
│
├── Consistency requirement?
│   ├── Strong (linearizable) → etcd / ZooKeeper / Spanner
│   ├── Strong (serializable) → PostgreSQL / CockroachDB
│   └── Eventual → Cassandra / DynamoDB / Redis
│
└── Scale requirement?
    ├── Single-node (TB scale) → PostgreSQL / MySQL
    ├── Multi-node (10s of TB) → CockroachDB / TiDB
    └── Global (PB scale) → Spanner / DynamoDB / Cassandra
```

### 10.2 Anti-Patterns

| Anti-pattern | Problem | Better choice |
|---|---|---|
| MongoDB for financial transactions | Weak multi-doc ACID until recently | PostgreSQL, CockroachDB |
| Cassandra for small datasets with complex queries | Overhead without benefit | PostgreSQL |
| Redis as primary database | Data loss risk, memory cost | Redis for cache, PostgreSQL for primary |
| Elasticsearch as source of truth | Eventual consistency, complex writes | ES for search, RDBMS as source |
| PostgreSQL for 100M+ writes/sec | Single-node write bottleneck | Cassandra, ScyllaDB, DynamoDB |
| Graph DB for tabular data | Overhead without traversal benefit | RDBMS |
| Using one DB for everything | Impedance mismatch | Polyglot persistence |

### 10.3 Polyglot Persistence

Modern systems often use multiple storage engines for different access patterns:

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
└───┬──────────┬──────────┬──────────┬──────────┬─────────┘
    │          │          │          │          │
    ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Postgres│ │ Redis  │ │Elastic │ │ S3 +   │ │ Neo4j  │
│        │ │        │ │ search │ │Parquet │ │        │
│OLTP    │ │Cache + │ │Full-   │ │Data    │ │Graph   │
│Source  │ │Session │ │text    │ │Lake    │ │queries │
│of truth│ │        │ │search  │ │        │ │        │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
    │          ▲          ▲          ▲          ▲
    └──────────┴──────────┴──────────┴──────────┘
      CDC / ETL / Event streaming keeps derived stores in sync
```

**Challenges:**
- Data consistency across stores (eventually consistent by nature)
- Operational complexity (monitoring, backup, upgrades for each system)
- Schema drift between stores
- Transaction boundaries span multiple systems (saga pattern needed)

---

## 11. Embedded Storage Engines

### 11.1 RocksDB

Facebook's fork of Google's LevelDB. The most widely used embedded LSM engine:

**Used as the storage layer for:**
- MySQL (MyRocks storage engine)
- CockroachDB (until Pebble migration)
- TiKV (TiDB's storage)
- YugabyteDB (DocDB)
- Kafka (KRaft metadata)

**Key APIs:**

```cpp
#include "rocksdb/db.h"

rocksdb::DB* db;
rocksdb::Options options;
options.create_if_missing = true;
options.compression = rocksdb::kLZ4Compression;

rocksdb::Status s = rocksdb::DB::Open(options, "/data/mydb", &db);

// Point operations:
s = db->Put(rocksdb::WriteOptions(), "key1", "value1");
std::string value;
s = db->Get(rocksdb::ReadOptions(), "key1", &value);
s = db->Delete(rocksdb::WriteOptions(), "key1");

// Atomic batch:
rocksdb::WriteBatch batch;
batch.Put("key1", "val1");
batch.Put("key2", "val2");
batch.Delete("key3");
s = db->Write(rocksdb::WriteOptions(), &batch);

// Iterator (range scan):
auto it = db->NewIterator(rocksdb::ReadOptions());
for (it->Seek("prefix:"); it->Valid() && it->key().starts_with("prefix:"); it->Next()) {
    process(it->key(), it->value());
}
delete it;

// Snapshot (consistent read view):
const rocksdb::Snapshot* snap = db->GetSnapshot();
rocksdb::ReadOptions ro;
ro.snapshot = snap;
s = db->Get(ro, "key1", &value);  // reads as of snapshot time
db->ReleaseSnapshot(snap);
```

### 11.2 SQLite

The most deployed database engine in the world (embedded in every smartphone,
browser, and many applications):

- **Single-file database** — the entire database is one file.
- **ACID transactions** — uses WAL or rollback journal.
- **Zero-configuration** — no server, no setup.
- **Size limit:** 281 TB theoretical, practical limit ~1 TB.
- **Concurrency:** Single writer, multiple readers (WAL mode).

```python
import sqlite3

conn = sqlite3.connect("app.db")
conn.execute("PRAGMA journal_mode=WAL")         # best concurrency
conn.execute("PRAGMA synchronous=NORMAL")        # balanced durability
conn.execute("PRAGMA cache_size=-64000")          # 64 MB page cache
conn.execute("PRAGMA foreign_keys=ON")            # enforce FKs

conn.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY,
        ts TEXT NOT NULL DEFAULT (datetime('now')),
        data TEXT NOT NULL
    )
""")

conn.execute("INSERT INTO events (data) VALUES (?)", ['{"type":"click"}'])
conn.commit()
```

### 11.3 DuckDB

Embedded OLAP database (the "SQLite for analytics"):

- **Columnar storage** with vectorized execution.
- **In-process** — no server, links into your application.
- **Reads Parquet, CSV, JSON** directly without import.

```python
import duckdb

# Query Parquet files on S3 directly:
result = duckdb.sql("""
    SELECT region, SUM(revenue) AS total
    FROM read_parquet('s3://bucket/sales/*.parquet')
    WHERE year = 2025
    GROUP BY region
    ORDER BY total DESC
""")

# Query pandas DataFrame:
import pandas as pd
df = pd.read_csv("data.csv")
duckdb.sql("SELECT * FROM df WHERE amount > 100")
```

---

## 12. Storage Engine Internals: Write Amplification Analysis

### 12.1 Quantifying Write Amplification

```
                    B-Tree              LSM (Leveled)
                    ──────              ─────────────
WAL write           1x                  1x
In-place update     1x (read page,     0 (no in-place)
                     modify, write)
Flush to L0         0                   1x
L0 → L1 compact    0                   ~1x
L1 → L2 compact    0                   ~1x (10x size ratio)
L2 → L3 compact    0                   ~1x
...                                     ~1x per level
Page split          occasional          0

Total (amortized):  ~2-5x               ~10-30x (leveled)
                                        ~4-8x (size-tiered)
```

### 12.2 Space Amplification

```
B-Tree:
  Average page fill: ~67% (after splits)
  Space amplification: ~1.5x
  With fillfactor=70: ~1.43x (intentional for updates)

LSM (Leveled):
  Temporary overlap during compaction: ~1.1x
  Dead entries between compactions: small

LSM (Size-Tiered):
  Copies of same data in multiple tiers: ~2x
  Worst case during compaction: ~3x temporarily
```

### 12.3 Read Amplification

```
B-Tree:
  Point read: 1 tree traversal (2-4 page reads)
  Read amplification: 1

LSM:
  Point read (worst case): check each level
    L0: up to 4 SSTables × Bloom filter check
    L1: 1 SSTable (binary search on boundaries)
    L2: 1 SSTable
    L3: 1 SSTable
    ...
  With Bloom filters (1% FPR): ~1.04 reads on average
  Read amplification: ~1 (with Bloom) to ~N (without Bloom)
```

---

## References

- **The Log-Structured Merge-Tree** — O'Neil et al., 1996.
- **Bigtable: A Distributed Storage System for Structured Data** — Chang et al., 2006.
- **Dynamo: Amazon's Highly Available Key-value Store** — DeCandia et al., 2007.
- **RocksDB documentation** — rocksdb.org
- **Apache Parquet specification** — parquet.apache.org
- **Designing Data-Intensive Applications** — Kleppmann, 2017. Chapters 3, 7.
- **Gorilla: A Fast, Scalable, In-Memory Time Series Database** — Pelkonen et al., 2015.
- **Spanner: Google's Globally-Distributed Database** — Corbett et al., 2012.
- **CockroachDB Architecture** — cockroachlabs.com/docs
- **WiredTiger Documentation** — source.wiredtiger.com
- **Neo4j Internals** — neo4j.com/docs/operations-manual

---

## Exercises

### Exercise 1: LSM-Tree vs B-Tree Benchmark

Set up a local RocksDB instance (via `db_bench`) and a MySQL/InnoDB instance on
the same hardware. Run the following workloads and record throughput (ops/sec),
p99 latency, and disk bytes written:

1. **Sequential write flood:** 10M key-value pairs (100-byte keys, 1 KB values).
2. **Random write flood:** 10M random key-value pairs.
3. **Mixed read-write:** 50% random reads, 50% random writes, 5M operations.
4. **Point lookups after load:** 1M random point queries on the 10M-key dataset.

Compare write amplification by dividing total disk bytes written (from OS-level
`iostat` or RocksDB's `compaction_stats`) by the application-level bytes written.
Explain why RocksDB outperforms InnoDB on sequential/random writes but may show
higher write amplification. Discuss how changing `write_buffer_size`,
`max_bytes_for_level_multiplier`, and compaction strategy (leveled vs universal)
affects the results.

### Exercise 2: Redis Data Structures for Real-Time Analytics

Design and implement a real-time leaderboard system using Redis sorted sets that
supports the following operations in O(log N):

1. `addScore(userId, score)` — add or update a player's score.
2. `getTopK(k)` — retrieve the top-K players with scores.
3. `getRank(userId)` — retrieve a player's rank.
4. `getAroundMe(userId, range)` — retrieve players ranked near a given user.

Extend the system with:
- A sliding-window leaderboard (last 24 hours) using Redis streams + sorted sets.
- HyperLogLog for approximate unique player counts per game session.
- A Bloom filter to check if a user has already claimed a daily reward.

Benchmark the system with 1M simulated players and document throughput per
operation type.

### Exercise 3: Write Amplification Analysis

Given a leveled-compaction LSM engine with the following configuration:
- MemTable size: 64 MB
- L1 target size: 256 MB
- Level multiplier: 10
- Total data: 100 GB

Calculate:
1. The number of levels required.
2. The theoretical worst-case write amplification per byte written.
3. How switching to size-tiered compaction changes write amplification and space
   amplification (show the math).
4. The expected Bloom filter memory usage at 10 bits/key with 500M keys.
5. The impact of increasing `bloom_bits_per_key` from 10 to 14 on false-positive
   rate and total memory.

### Exercise 4: NoSQL Data Modeling Comparison

A social media application needs to store:
- User profiles (name, bio, followers list, following list)
- Posts (text, media URLs, timestamp, likes count, comments)
- Activity feed (chronological list of posts from followed users)
- Direct messages (sender, recipient, message, timestamp, read status)

Design the data model for **three** different NoSQL paradigms:
1. **Document store (MongoDB):** Define collections, document schemas, indexes,
   and the aggregation pipeline for generating a user's activity feed.
2. **Wide-column store (Cassandra):** Define the keyspace, tables with partition
   keys and clustering columns, and explain your denormalization strategy.
3. **Graph database (Neo4j):** Define node labels, relationship types, and write
   Cypher queries for mutual-friend suggestions and shortest-path between users.

For each model, analyze: consistency guarantees, read/write latency for the feed
query at 100M users, storage efficiency, and operational complexity.

### Exercise 5: NewSQL Evaluation

Deploy a 3-node CockroachDB cluster (Docker or local) and a 3-node PostgreSQL
cluster with Citus or manual sharding. Run the following experiments:

1. Create a `users` table and an `orders` table with a foreign key.
2. Insert 5M rows across both tables.
3. Run OLTP benchmark queries (point reads, range scans, JOINs) and record
   latency at p50, p95, p99.
4. Simulate a node failure (kill one node) and measure:
   - Time to detect failure.
   - Query availability during failure.
   - Data loss (if any).
   - Recovery time after node restart.
5. Add a fourth node and measure automatic rebalancing time and throughput impact.

Document how CockroachDB's Raft-based replication and range-split mechanism
compare to manual sharding in PostgreSQL.

---

## Readings and References

### Official Documentation (retrieved: 2026-05-29)

- **RocksDB Wiki** — Architecture guide, tuning, compaction:
  https://github.com/facebook/rocksdb/wiki
- **RocksDB Official Site** — Getting started, FAQ:
  https://rocksdb.org/
- **Apache Cassandra Storage Engine** — Memtables, SSTables, compaction:
  https://cassandra.apache.org/doc/latest/cassandra/architecture/storage-engine.html
- **MongoDB WiredTiger Storage Engine** — Concurrency, checkpointing, compression:
  https://www.mongodb.com/docs/manual/core/wiredtiger/
- **Redis Data Types** — Strings, sorted sets, streams, HyperLogLog, vector sets:
  https://redis.io/docs/latest/develop/data-types/
- **Neo4j Documentation** — Graph concepts, Cypher, operations:
  https://neo4j.com/docs/
- **ClickHouse Documentation** — Column-oriented OLAP engine:
  https://clickhouse.com/docs/intro
- **DuckDB Documentation** — In-process OLAP, vectorized execution:
  https://duckdb.org/docs/current/
- **Apache Parquet Specification** — Columnar file format:
  https://parquet.apache.org/documentation/latest/
- **CockroachDB Architecture** — Ranges, Raft, distributed SQL:
  https://www.cockroachlabs.com/docs/stable/architecture/overview

### Books

- Kleppmann, M. (2017). *Designing Data-Intensive Applications*. O'Reilly.
  Chapters 3 (Storage and Retrieval), 7 (Transactions). ISBN 978-1-4493-7332-0.
- Petrov, A. (2019). *Database Internals: A Deep Dive into How Distributed Data
  Systems Work*. O'Reilly. Parts I (Storage Engines) and II (Distributed Systems).
  ISBN 978-1-4920-4034-7.

### Papers

- O'Neil, P., Cheng, E., Gawlick, D., O'Neil, E. (1996). "The Log-Structured
  Merge-Tree (LSM-Tree)." *Acta Informatica*, 33(4), 351-385.
  https://www.cs.umb.edu/~poneil/lsmtree.pdf
- Chang, F. et al. (2006). "Bigtable: A Distributed Storage System for Structured
  Data." *OSDI '06*.
- DeCandia, G. et al. (2007). "Dynamo: Amazon's Highly Available Key-value Store."
  *SOSP '07*.
- Pelkonen, T. et al. (2015). "Gorilla: A Fast, Scalable, In-Memory Time Series
  Database." *VLDB '15*.
- Corbett, J. et al. (2012). "Spanner: Google's Globally-Distributed Database."
  *OSDI '12*.
- Stonebraker, M. and Cetintemel, U. (2005). "One Size Fits All: An Idea Whose
  Time Has Come and Gone." *ICDE '05*.

---

## Cross-References

| Topic | Module | File |
|---|---|---|
| B-tree page layout, buffer pool, MVCC | 3.1 — Relational Internals | `01_Relational_Internals.md` |
| Raft consensus, quorum writes, replication topologies | 3.2 — Distributed Consensus | `02_Distributed_Consensus.md` |
| OLTP vs OLAP workloads, column stores in warehouses, Parquet/ORC in data lakes | 3.4 — Data Engineering OLAP/OLTP | `04_Data_Engineering_OLAP_OLTP.md` |
| CAP theorem, PACELC, distributed system trade-offs | 2 — Architecture & Design | `02_Architecture_Design/04_System_Design_CAP_PACELC.md` |
| Container orchestration, running stateful databases on Kubernetes | 5 — DevOps & Cloud Native | `05_DevOps_Cloud_Native/02_Kubernetes_Architecture.md` |
| Vector databases (Milvus, Pinecone, pgvector) for ML embeddings | 7 — AI/ML Integration | `07_AI_ML_Integration/02_LLM_Integration_RAG_VectorDB.md` |

---

## Glossary

| Term | Definition |
|---|---|
| **LSM-Tree** | Log-Structured Merge-Tree: a write-optimized data structure that buffers writes in memory (MemTable) and flushes sorted runs (SSTables) to disk, merging them via compaction. |
| **SSTable** | Sorted String Table: an immutable, sorted file of key-value pairs with an index block and optional Bloom filter metadata. |
| **Compaction** | Background process that merges overlapping SSTables to remove tombstones and obsolete versions, reclaiming space and improving read performance. |
| **Write Amplification** | Ratio of total bytes written to storage vs. bytes written by the application; a key cost metric for LSM engines (typical 10-30x for leveled compaction). |
| **Bloom Filter** | Probabilistic data structure that answers set-membership queries with no false negatives; used in LSM-tree read paths to skip SSTables that definitely do not contain the target key. |
| **MemTable** | In-memory sorted data structure (typically a skip list or red-black tree) that buffers writes before flushing to disk as an SSTable. |
| **WAL** | Write-Ahead Log: a sequential, append-only log on disk ensuring durability; every write is logged to WAL before being applied to the MemTable. |
| **Clustered Index** | A B-tree index where the leaf nodes store the actual row data, ordered by the primary key (e.g., InnoDB's primary index). |
| **Document Model** | A schema-flexible data model storing records as self-describing documents (JSON/BSON), enabling nested structures without predefined schemas. |
| **Wide-Column Store** | A distributed NoSQL model organizing data by row key, column family, and column qualifier, optimized for sparse datasets with many columns per row. |
| **Vectorized Execution** | Query execution strategy that processes data in batches (vectors) of ~1024 values rather than row-at-a-time, enabling SIMD instructions and reducing per-row overhead. |
| **NewSQL** | A category of databases that provide the horizontal scalability of NoSQL with full ACID transactions and SQL interface (e.g., CockroachDB, TiDB, Spanner). |
| **Tombstone** | A deletion marker in LSM-tree storage that suppresses older versions of a key until compaction physically removes the data. |
| **Read Amplification** | The number of disk reads required to satisfy a single logical read; minimized in B-trees (one traversal) and mitigated in LSM-trees via Bloom filters. |
| **Space Amplification** | Ratio of actual disk usage to the logical data size; caused by obsolete entries awaiting compaction (LSM) or partially filled pages (B-tree). |
