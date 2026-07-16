# Module 1.3: Advanced Data Structures & Algorithms

> **Module 01.3** · **Last updated:** 2026-04-27

## Guiding ideas
1. **Skip list, B+ tree, LSM tree: production-relevant.**
2. **Bloom filter: probabilistic; false positives but no false negatives.**
3. **HyperLogLog: cardinality estimation in low memory.**
4. **Consistent hashing: distributed cache key distribution.**


**Date:** 2026-04-22
**Status:** Completed

## 1. B-Trees & B+Trees

The dominant on-disk index structure: PostgreSQL (`btree`), MySQL InnoDB clustered index, SQLite, NTFS, ext4 HTree, MongoDB WiredTiger.

### 1.1 B-Tree Properties (order *m*)
*   Every node has between `ceil(m/2) - 1` and `m - 1` keys.
*   Internal nodes have between `ceil(m/2)` and `m` children.
*   All leaves at the same depth (perfectly balanced).
*   **Height:** `h <= log_ceil(m/2) ((n+1)/2)`. For `m=200`, `n=10^9` → `h ≈ 4`.

### 1.2 B+Tree (the variant DBs actually use)
*   **Internal nodes** store *only routing keys* (no payload).
*   **Leaf nodes** store all key/value pairs and form a **doubly-linked list** → range scans are sequential I/O.
*   **Fanout maximized:** with 8KB page, 16-byte keys, 8-byte child pointers → fanout ≈ 340. Three levels index ~40M rows; four levels ~13B.

### 1.3 Splits & Merges
*   **Insert:** if leaf full → split at median, push median up. Cascades up; root split → tree grows by 1.
*   **Delete:** if node underflows (`< ceil(m/2) - 1` keys) → borrow from sibling, else merge with sibling and pull separator down.
*   *Worst case I/O:* `O(log_m n)` per operation.

## 2. Bloom Filters

Probabilistic membership: *no false negatives, tunable false positives*. Used in Cassandra SSTable read-path, BigTable, HBase, Redis (`BF.ADD`), Chrome safe-browsing, RocksDB.

### 2.1 Math
*   Bit array of size `m`, `k` independent hash functions, `n` inserted elements.
*   **False positive rate:** `p ≈ (1 - e^(-kn/m))^k`.
*   **Optimal k:** `k* = (m/n) ln 2 ≈ 0.693 (m/n)`.
*   **Optimal m:** `m = - n ln(p) / (ln 2)^2 ≈ -1.44 n log2(p)`.
*   *Example:* `n = 10^6`, `p = 1%` → `m ≈ 9.6 Mbit ≈ 1.2 MB`, `k ≈ 7`.

### 2.2 Variants
*   **Counting Bloom:** cells are 4-bit counters → supports deletion at 4× space.
*   **Cuckoo Filter:** supports deletion, often lower space at low `p`.

## 3. HyperLogLog (HLL)

Cardinality estimation in *constant memory*. Used by Redis (`PFADD`/`PFCOUNT`), Presto/Trino, BigQuery `APPROX_COUNT_DISTINCT`.

*   Hash element → use first `b` bits to pick bucket (`m = 2^b` buckets), remaining bits → count leading zeros `ρ`.
*   Per-bucket store `max(ρ)`. Estimate: `E = α_m · m^2 / Σ 2^(-M[j])` with bias correction.
*   **Standard error:** `ε ≈ 1.04 / √m`. Redis uses `m = 16384` → `ε ≈ 0.81%`, fixed 12 KB regardless of cardinality (up to ~2^64).

## 4. Skip Lists

Probabilistic alternative to balanced BSTs. Used in Redis **sorted sets** (`ZADD`/`ZRANGE`), LevelDB MemTable, Java `ConcurrentSkipListMap`.

*   Node promoted to level `L+1` with probability `p` (typically `p = 1/2` or `1/4`).
*   Expected levels: `log_(1/p) n`. Expected search/insert/delete: **O(log n)**.
*   *Why Redis chose it over RB-tree:* simpler concurrent implementation, easier range queries, lock-free variants exist.

## 5. LSM-Trees (Log-Structured Merge)

Optimized for write-heavy workloads. Used in RocksDB, LevelDB, Cassandra, HBase, ScyllaDB, InfluxDB.

### 5.1 Structure
*   **MemTable:** in-memory sorted (skip list / RB-tree). Writes go here + WAL.
*   **Flush:** when MemTable full → write immutable **SSTable** (Sorted String Table) to disk at L0.
*   **Levels L1..Ln:** each level ~10× larger than previous. Files within a level have non-overlapping key ranges (except L0).

### 5.2 Compaction Strategies
*   **Leveled (RocksDB default):** merge L_i into L_(i+1), maintaining size ratio `T` (typ. 10). *Read amp:* `O(L)`. *Write amp:* `~T·L`. *Space amp:* low.
*   **Tiered / Size-Tiered (Cassandra default):** merge files of similar size. *Write amp:* low. *Space amp:* up to 2×. *Read amp:* high.
*   **Universal:** hybrid; bounds total file count.

### 5.3 Read Path Optimization
*   Bloom filter per SSTable to skip files lacking the key.
*   Block cache, index/filter cache.

## 6. Trie / Radix Tree

*   **Trie:** each edge labeled with one symbol. Lookup `O(k)` in key length, independent of `n`.
*   **Radix Tree (PATRICIA):** compress chains of single-child nodes into one edge labeled with a string. Memory-efficient.
*   **Adaptive Radix Tree (ART):** node sizes 4/16/48/256 → cache-friendly, used in HyPer, DuckDB.
*   *Use cases:* IP routing tables (longest-prefix match), autocomplete, Linux kernel `idr`/`xarray`.

## 7. Graph Algorithms

| Algorithm | Problem | Complexity |
|---|---|---|
| **Dijkstra** | Single-source shortest path, non-negative weights | `O((V+E) log V)` w/ binary heap; `O(E + V log V)` w/ Fibonacci heap |
| **A*** | SSSP with admissible heuristic `h` | Same as Dijkstra; explores fewer nodes if `h` tight |
| **Bellman-Ford** | SSSP with negative edges; detects negative cycles | `O(V·E)` |
| **Floyd-Warshall** | All-pairs shortest path | `O(V^3)`, `O(V^2)` space |
| **Kruskal** | MST via edge sort + Union-Find | `O(E log E)` |
| **Prim** | MST via priority queue | `O((V+E) log V)` |
| **Tarjan SCC** | Strongly connected components | `O(V+E)` single DFS pass, uses lowlink |
| **Kosaraju SCC** | Same | `O(V+E)`, two DFS passes (G then G^T) |
| **Topological sort** | DAG ordering | `O(V+E)` (Kahn's BFS or DFS post-order reverse) |

*A* admissibility:* `h(n) <= h*(n)`. *Consistency (monotone):* `h(n) <= c(n,n') + h(n')` → never re-expand.

## 8. Union-Find (Disjoint Set Union)

Backbone of Kruskal, Tarjan offline LCA, network connectivity, percolation.

*   **Find(x):** with **path compression** → flatten tree on traversal.
*   **Union(a,b):** with **union by rank/size** → attach smaller under larger.
*   Combined amortized cost per op: **O(α(n))** where α is the inverse Ackermann function. For all practical `n`, `α(n) <= 4` → effectively *O(1)*.

```text
function Find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]   // path halving
        x = parent[x]
    return x
```
