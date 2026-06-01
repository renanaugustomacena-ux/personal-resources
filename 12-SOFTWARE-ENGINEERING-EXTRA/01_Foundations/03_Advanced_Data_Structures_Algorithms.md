---
corso: "SWE Masterclass"
fase: "1 — Foundations"
modulo: "03"
titolo: "Advanced Data Structures & Algorithms"
versione: "CLRS 4th ed. (2022) · Redis 7.x · RocksDB 9.x"
livello: "Advanced"
prerequisiti:
  - "Basic data structures (arrays, linked lists, hash tables, binary trees)"
  - "Algorithm complexity analysis (Big-O, amortized analysis)"
  - "Familiarity with disk I/O models and memory hierarchy"
obiettivi:
  - "Analyze and implement B+Tree insertion/deletion with split and merge operations"
  - "Design and tune Bloom filters for target false-positive rates in real systems"
  - "Explain LSM-tree compaction strategies and their read/write/space amplification trade-offs"
  - "Apply probabilistic data structures (HyperLogLog, skip lists) to solve cardinality and ordered-set problems"
  - "Select appropriate graph algorithms (Dijkstra, A*, Tarjan SCC) for production routing and dependency analysis"
tag: [data-structures, algorithms, B+tree, bloom-filter, LSM-tree, HyperLogLog, skip-list, graph-algorithms, union-find, trie]
---

# Module 1.3: Advanced Data Structures & Algorithms

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Analyze and implement B+Tree insertion/deletion with split and merge operations
> - Design and tune Bloom filters for target false-positive rates in real systems
> - Explain LSM-tree compaction strategies and their read/write/space amplification trade-offs
> - Apply probabilistic data structures (HyperLogLog, skip lists) to solve cardinality and ordered-set problems
> - Select appropriate graph algorithms (Dijkstra, A*, Tarjan SCC) for production routing and dependency analysis

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

---

## Exercises

### Exercise 1 — Bloom Filter Sizing and Benchmarking
Design a Bloom filter for a dictionary of 1 million English words with a target false-positive rate of 0.1%. Calculate the optimal `m` and `k`. Implement it in your language of choice, insert the dictionary, then query 100,000 random non-dictionary strings. Measure the empirical FP rate and compare it against the theoretical prediction.

### Exercise 2 — B+Tree Range Scan Simulator
Implement a B+Tree (order 64) that stores integer keys with string payloads. Support `insert`, `delete`, `point_lookup`, and `range_scan(lo, hi)`. Insert 10 million random keys, then benchmark range scans of width 100, 1000, and 10000. Report I/O cost (node accesses) vs. key count. Verify the leaf-level linked-list traversal property.

### Exercise 3 — LSM Compaction Comparison
Build a simplified LSM simulator with MemTable (skip list), L0 flush, and two compaction strategies: leveled and size-tiered. Insert 5 million keys with Zipfian distribution, then measure write amplification (bytes written to disk / bytes of user data) and read amplification (SSTables checked per point query). Plot both metrics as a function of insert count.

### Exercise 4 — HyperLogLog vs. Exact Count
Implement HyperLogLog with `m = 1024` buckets. Stream 10 million unique 64-bit hashes and compare the HLL estimate against the exact count at intervals of 10k, 100k, 1M, and 10M. Report relative error at each checkpoint. Then merge two independent HLL sketches and verify the union cardinality estimate.

### Exercise 5 — Graph Algorithm Showdown
Given a weighted directed graph with 50,000 nodes and 200,000 edges (randomly generated, some negative weights on a subset of edges): (a) Run Dijkstra with a binary heap on the non-negative subgraph and report shortest-path distances from a source. (b) Run Bellman-Ford on the full graph and detect any negative cycles. (c) Run Tarjan's SCC algorithm on the unweighted projection and report the number and sizes of strongly connected components. Compare wall-clock times.

---

## Readings and References

### Official documentation
- **Redis Data Types — Probabilistic** — Bloom filter (`BF.ADD`), HyperLogLog (`PFADD`/`PFCOUNT`), and sorted set (skip list) documentation. <https://redis.io/docs/latest/develop/data-types/probabilistic/> (retrieved: 2026-05-29)
- **RocksDB Wiki — Compaction** — Leveled, universal, and FIFO compaction strategy details. <https://github.com/facebook/rocksdb/wiki/Compaction> (retrieved: 2026-05-29)
- **PostgreSQL B-Tree Index** — Implementation notes on the B-tree access method used by PostgreSQL. <https://www.postgresql.org/docs/current/btree.html> (retrieved: 2026-05-29)

### Books
- Cormen, T.H., Leiserson, C.E., Rivest, R.L., Stein, C., *Introduction to Algorithms*, 4th ed., MIT Press, 2022. ISBN 978-0-262-04630-5.
- Sedgewick, R., Wayne, K., *Algorithms*, 4th ed., Addison-Wesley, 2011. ISBN 978-0-321-57351-3.
- Skiena, S.S., *The Algorithm Design Manual*, 3rd ed., Springer, 2020. ISBN 978-3-030-54255-9.

### Papers and articles
- Bloom, B.H., "Space/Time Trade-offs in Hash Coding with Allowable Errors", *Communications of the ACM*, 13(7), pp. 422–426, 1970. <https://dl.acm.org/doi/10.1145/362686.362692>
- Pugh, W., "Skip Lists: A Probabilistic Alternative to Balanced Trees", *Communications of the ACM*, 33(6), pp. 668–676, 1990. <https://dl.acm.org/doi/10.1145/78973.78977>
- O'Neil, P. et al., "The Log-Structured Merge-Tree (LSM-Tree)", *Acta Informatica*, 33(4), pp. 351–385, 1996. <https://www.cs.umb.edu/~poneil/lsmtree.pdf>
- Flajolet, P. et al., "HyperLogLog: The Analysis of a Near-Optimal Cardinality Estimation Algorithm", *AofA '07*, 2007. <https://hal.science/hal-00406166v1>
- Heule, S., Nunkesser, M., Hall, A., "HyperLogLog in Practice: Algorithmic Engineering of a State of the Art Cardinality Estimation Algorithm", *EDBT 2013*. <https://research.google.com/pubs/archive/40671.pdf>
- Dayan, N., Idreos, S., "Optimal Bloom Filters and Adaptive Merging for LSM-Trees", *ACM TODS*, 43(4), 2018. <https://cs-people.bu.edu/mathan/publications/tods18-dayan.pdf>

---

## Cross-References

| Module | Relationship |
|---|---|
| `01_b_Scheduler_Data_Structures.md` | Red-black trees, priority queues — alternative balanced-tree structures compared with skip lists and B-trees |
| `01_c_Memory_Management_Algorithms.md` | Buddy allocator, slab allocator — memory-management algorithms that rely on tree and bitmap data structures |
| `01_d_File_Systems_Storage.md` | B+Tree as the dominant on-disk index in ext4 HTree and NTFS; LSM-tree in modern storage engines |
| `04_Compilers_Interpreters.md` | SSA graph construction, dominator trees — graph algorithms (DFS, topological sort) applied in compiler IRs |
| `02_Architecture_Design/` | System design trade-offs involving consistent hashing, Bloom filters in distributed caches, HLL in analytics pipelines |
| `03_Database_Engineering/` | B+Tree indexing, LSM-tree storage engines (RocksDB, LevelDB), Bloom filters in query-path optimization |

---

## Glossary

| Term | Definition |
|---|---|
| **B+Tree** | A self-balancing tree where internal nodes store only routing keys and all data resides in leaf nodes linked sequentially |
| **Bloom filter** | A space-efficient probabilistic data structure that tests set membership with no false negatives but tunable false positives |
| **Counting Bloom filter** | A Bloom filter variant using counters instead of bits, enabling element deletion at the cost of extra space |
| **Cuckoo filter** | A probabilistic filter supporting deletion and often achieving lower space usage than Bloom filters at low FP rates |
| **HyperLogLog** | A cardinality estimation algorithm using constant memory (typically 12 KB) to approximate distinct-element counts |
| **Skip list** | A probabilistic data structure providing O(log n) search, insertion, and deletion via layered linked lists |
| **LSM-tree** | Log-Structured Merge-tree; a write-optimized data structure that batches writes in memory and flushes sorted runs to disk |
| **SSTable** | Sorted String Table; an immutable on-disk file of sorted key-value pairs, the building block of LSM-tree levels |
| **Write amplification** | The ratio of total bytes written to storage versus bytes of actual user data, a key LSM-tree tuning metric |
| **Compaction** | The background process of merging and sorting SSTables across LSM-tree levels to reclaim space and bound read cost |
| **Consistent hashing** | A hashing scheme where adding/removing nodes only remaps O(K/n) keys, used in distributed caches and databases |
| **Union-Find** | A disjoint-set data structure supporting near-constant-time union and find operations via path compression and rank |
| **Radix tree** | A compressed trie where single-child chains collapse into one edge, reducing memory overhead |
| **Adaptive Radix Tree (ART)** | A radix tree variant with node sizes 4/16/48/256 for cache efficiency, used in analytical databases |
| **Inverse Ackermann function (α)** | An extremely slowly growing function that bounds the amortized cost of Union-Find operations; effectively constant for all practical inputs |
