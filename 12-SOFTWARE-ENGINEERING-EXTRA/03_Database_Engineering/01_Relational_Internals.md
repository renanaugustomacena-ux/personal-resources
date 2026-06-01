---
corso: "SWE Masterclass"
fase: "3 — Database Engineering"
modulo: "01"
titolo: "Relational Database Internals"
versione: "PostgreSQL 17"
livello: "Advanced"
prerequisiti:
  - "Solid SQL fluency (DDL, DML, joins, subqueries, window functions)"
  - "Operating-system fundamentals: virtual memory, page cache, file I/O, processes vs. threads"
  - "Basic understanding of B-trees and hash tables as data structures"
  - "Familiarity with ACID transaction properties"
obiettivi:
  - "Trace a SQL query through all five kernel stages (parser, analyzer, rewriter, planner, executor) and identify the bottleneck stage for a given slow query"
  - "Read and interpret EXPLAIN (ANALYZE, BUFFERS) output to diagnose plan regressions, cardinality misestimates, and buffer-pool misses"
  - "Describe the PostgreSQL MVCC visibility rules, predict which row version a concurrent transaction will see, and measure HOT-update effectiveness"
  - "Configure WAL, checkpoints, and autovacuum parameters for a high-throughput OLTP workload and justify each setting"
  - "Design an indexing strategy (B+tree, partial, covering, expression, BRIN) for a given schema and query pattern, and verify it with pg_stat_user_indexes"
tag: [postgresql, relational, internals, mvcc, wal, b-tree, query-planner, vacuum, indexing, connection-pooling]
---

# Module 3.1: Relational Database Internals

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Trace a SQL query through all five kernel stages (parser, analyzer, rewriter, planner, executor) and identify the bottleneck stage for a given slow query
> - Read and interpret EXPLAIN (ANALYZE, BUFFERS) output to diagnose plan regressions, cardinality misestimates, and buffer-pool misses
> - Describe the PostgreSQL MVCC visibility rules, predict which row version a concurrent transaction will see, and measure HOT-update effectiveness
> - Configure WAL, checkpoints, and autovacuum parameters for a high-throughput OLTP workload and justify each setting
> - Design an indexing strategy (B+tree, partial, covering, expression, BRIN) for a given schema and query pattern, and verify it with pg_stat_user_indexes

> **Module 03.1** · **Last updated:** 2026-05-22

## Guiding ideas
1. **B+ tree index: O(log n) lookup; sequential scan friendly.**
2. **MVCC (multi-version concurrency control): readers don't block writers.**
3. **WAL (Write-Ahead Log): durability + crash recovery.**
4. **Query planner: cost-based (CBO) > rule-based (RBO).**
5. **Statistics ANALYZE for accurate plans.**

---

## 1. Anatomy of a Query: From SQL Text to Result Set

A SQL query traverses five major stages inside the RDBMS kernel before a single row
is returned. Understanding these stages is fundamental to debugging performance
issues and reasoning about behavior.

```
┌─────────────────────────────────────────────────────────────┐
│                      Client SQL Text                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   1. Parser    │  Lexer + Grammar → AST
                    └───────┬────────┘
                            │
                            ▼
                    ┌────────────────┐
                    │  2. Analyzer   │  Name resolution, type checking
                    └───────┬────────┘
                            │
                            ▼
                    ┌────────────────┐
                    │  3. Rewriter   │  View expansion, rule system
                    └───────┬────────┘
                            │
                            ▼
                    ┌────────────────┐
                    │  4. Planner /  │  Generate plans, estimate cost,
                    │   Optimizer    │  pick cheapest
                    └───────┬────────┘
                            │
                            ▼
                    ┌────────────────┐
                    │  5. Executor   │  Volcano / vectorized execution
                    └───────┬────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │   Result Rows    │
                  └──────────────────┘
```

### 1.1 Parser

The parser converts raw SQL text into an Abstract Syntax Tree (AST).

**Lexer (tokenizer):** Splits the input string into tokens — keywords (`SELECT`,
`FROM`, `WHERE`), identifiers, literals, operators, punctuation.

**Grammar:** A formal grammar (usually yacc/bison-based in PostgreSQL, ANTLR-based
in newer systems) validates syntax and produces the raw parse tree.

```sql
-- Input:
SELECT e.name, d.title
FROM employees e
JOIN departments d ON e.dept_id = d.id
WHERE e.salary > 80000;

-- Parser output (conceptual AST):
SelectStmt
├── targetList: [ColumnRef(e.name), ColumnRef(d.title)]
├── fromClause:
│   └── JoinExpr
│       ├── larg: RangeVar(employees, alias=e)
│       ├── rarg: RangeVar(departments, alias=d)
│       └── quals: OpExpr(=, e.dept_id, d.id)
└── whereClause: OpExpr(>, e.salary, Const(80000))
```

At this stage, the parser knows nothing about whether `employees` or `departments`
exist or whether `salary` is an integer. It only validates syntax.

**Common parser errors:**

| Error message | Root cause |
|---|---|
| `syntax error at or near "FROM"` | Missing column list or typo in SELECT |
| `unterminated quoted string` | Unbalanced single quotes |
| `column "foo" does not exist` | Passes parser but fails in analyzer |

### 1.2 Analyzer (Semantic Analysis)

The analyzer transforms the raw parse tree into a **query tree** by resolving names
and types against the system catalog (`pg_class`, `pg_attribute`, `pg_type`,
`pg_operator`).

**Steps performed:**

1. **Relation lookup:** Does `employees` exist? Is the user allowed to read it?
2. **Column resolution:** Does `e.name` exist in `employees`? What is its type?
3. **Type coercion:** `e.salary > 80000` — salary is `numeric`, 80000 is `int4`.
   Insert an implicit cast node.
4. **Function resolution:** `upper(e.name)` — find `upper(text) → text` in
   `pg_proc`.
5. **Subquery scoping:** Correlate outer references in subqueries.

### 1.3 Rewriter

PostgreSQL's rule system transforms the query tree before planning:

- **View expansion:** `SELECT * FROM active_users` → the view's defining query is
  inlined.
- **Rules:** `CREATE RULE` rewrites (e.g., redirect INSERTs to a partitioned child).
- **Security barrier views:** Mark subquery as security-barrier to prevent predicate
  pushdown that could leak rows.

In MySQL/InnoDB, this stage is simpler — views are merged or materialized but there
is no general rule system.

### 1.4 Planner / Optimizer

The core of query performance. The planner enumerates possible execution strategies,
estimates their cost, and picks the cheapest.

#### 1.4.1 Cost-Based Optimization (CBO)

The dominant approach in modern RDBMS. The planner:

1. **Enumerates join orders.** For N tables, there are N! orderings (pruned by
   dynamic programming or genetic algorithm for large N).
2. **Considers access methods** per table: sequential scan, index scan, index-only
   scan, bitmap scan.
3. **Considers join algorithms:** nested loop, hash join, merge join.
4. **Estimates cardinality** (row count) at each node using table statistics.
5. **Computes total cost** = startup cost + run cost, expressed in arbitrary
   cost units calibrated to sequential page reads.

**Cost model parameters (PostgreSQL GUCs):**

```
seq_page_cost     = 1.0      -- cost of a sequential page read
random_page_cost  = 4.0      -- cost of a random page read (SSD: lower to 1.1-1.5)
cpu_tuple_cost    = 0.01     -- cost of processing one row
cpu_index_tuple_cost = 0.005 -- cost of processing one index entry
cpu_operator_cost = 0.0025   -- cost of applying an operator
effective_cache_size = 4GB   -- planner's estimate of OS + shared buffer cache
```

**Key insight:** If `random_page_cost` is too high relative to your actual hardware
(e.g., NVMe SSD), the planner avoids indexes even when they would help. On SSD,
set `random_page_cost` to 1.1.

#### 1.4.2 Rule-Based Optimization (RBO)

Oracle's legacy optimizer (pre-10g) and some embedded databases use RBO:

- Fixed hierarchy of access paths: indexed access always preferred over full scan.
- No statistics, no cardinality estimates.
- Deterministic but brittle — adding an index can change plans unpredictably.
- **No modern RDBMS should use RBO for production workloads.**

#### 1.4.3 Cardinality Estimation

The single most impactful factor in plan quality. Bad estimates → bad plans.

**Statistics collected by ANALYZE:**

| Statistic | What it captures |
|---|---|
| `n_distinct` | Estimated number of distinct values in column |
| `null_frac` | Fraction of NULL values |
| `most_common_vals` | Array of most frequent values |
| `most_common_freqs` | Frequencies of the above |
| `histogram_bounds` | Equal-frequency histogram boundaries |
| `correlation` | Physical vs. logical ordering (1.0 = perfectly correlated) |

**Selectivity estimation examples:**

```sql
-- Equality: selectivity = 1 / n_distinct
WHERE status = 'active'
-- If n_distinct = 5, selectivity ≈ 0.2 (20% of rows)

-- Range: selectivity from histogram
WHERE price BETWEEN 100 AND 500
-- Planner finds histogram buckets covering [100, 500], sums their fractions

-- AND: selectivity = sel(A) * sel(B)  (independence assumption)
WHERE status = 'active' AND price > 100
-- Problem: if status and price are correlated, this underestimates
```

**Extended statistics (PostgreSQL 10+):**

```sql
CREATE STATISTICS city_state_stats (dependencies, ndistinct, mcv)
ON city, state FROM addresses;
ANALYZE addresses;
```

This tells the planner that `city` and `state` are correlated, preventing
cardinality underestimation on predicates like `WHERE city = 'SF' AND state = 'CA'`.

#### 1.4.4 Join Ordering and Algorithms

**Dynamic programming** is used for up to ~12 tables (configurable via
`geqo_threshold` in PostgreSQL). Beyond that, the **Genetic Query Optimizer (GEQO)**
uses a genetic algorithm to search the plan space heuristically.

**Join algorithms:**

```
┌──────────────────────────────────────────────────────────────────────┐
│ Algorithm     │ Best when                │ Cost           │ Memory  │
├───────────────┼──────────────────────────┼────────────────┼─────────┤
│ Nested Loop   │ Small outer, indexed     │ O(N * M) or    │ O(1)    │
│               │ inner                    │ O(N * log M)   │         │
├───────────────┼──────────────────────────┼────────────────┼─────────┤
│ Hash Join     │ Large inner fits in      │ O(N + M)       │ O(M)    │
│               │ work_mem                 │ build + probe  │         │
├───────────────┼──────────────────────────┼────────────────┼─────────┤
│ Merge Join    │ Both inputs pre-sorted   │ O(N log N +    │ O(1)    │
│               │ (index-backed)           │  M log M)      │         │
└──────────────────────────────────────────────────────────────────────┘
```

**Hash join internals:**

```
Phase 1 — Build:
  for each row in inner_table:
      bucket = hash(join_key) % num_buckets
      hash_table[bucket].append(row)

Phase 2 — Probe:
  for each row in outer_table:
      bucket = hash(join_key) % num_buckets
      for candidate in hash_table[bucket]:
          if candidate.join_key == row.join_key:
              emit(row, candidate)
```

If the hash table exceeds `work_mem`, PostgreSQL spills to disk using **batch
partitioning** (Grace hash join variant).

#### 1.4.5 Reading EXPLAIN Output

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT e.name, d.title
FROM employees e
JOIN departments d ON e.dept_id = d.id
WHERE e.salary > 80000;
```

```
Hash Join  (cost=3.25..24.50 rows=100 width=64) (actual time=0.05..0.12 rows=87 loops=1)
  Hash Cond: (e.dept_id = d.id)
  Buffers: shared hit=12
  ->  Seq Scan on employees e  (cost=0.00..20.00 rows=100 width=40) (actual time=0.01..0.05 rows=87 loops=1)
        Filter: (salary > 80000)
        Rows Removed by Filter: 913
        Buffers: shared hit=10
  ->  Hash  (cost=2.00..2.00 rows=25 width=24) (actual time=0.02..0.02 rows=25 loops=1)
        Buckets: 1024  Batches: 1  Memory Usage: 10kB
        ->  Seq Scan on departments d  (cost=0.00..2.00 rows=25 width=24) (actual time=0.00..0.01 rows=25 loops=1)
              Buffers: shared hit=2
Planning Time: 0.15 ms
Execution Time: 0.18 ms
```

**Key fields:**

- `cost=start..total` — estimated cost in arbitrary units
- `rows` — estimated (in cost) vs. actual (in ANALYZE) row count
- `Buffers: shared hit=12` — 12 pages found in buffer pool, no disk reads
- `Rows Removed by Filter: 913` — indicates filter selectivity was ~10%
- Mismatch between estimated and actual rows signals stale statistics

### 1.5 Executor

The executor runs the plan tree using the **Volcano (iterator) model** in most
traditional RDBMS:

```
interface PlanNode:
    open()    -- initialize
    next()    -- return one row (or NULL if done)
    close()   -- cleanup
```

Each node pulls rows from its children on demand (pull-based, lazy evaluation).
This enables pipelining — a `LIMIT 10` stops pulling after 10 rows, even if the
underlying scan has millions.

**Vectorized execution** (used by ClickHouse, DuckDB, PostgreSQL JIT):

Instead of one row at a time, process batches (vectors) of ~1000 rows. This
amortizes function-call overhead and enables SIMD instructions.

```
Traditional (row-at-a-time):       Vectorized (batch):
  for each row:                      for each batch of 1024 rows:
    apply_filter(row)                  apply_filter_simd(batch)
    project(row)                       project_simd(batch)
    emit(row)                          emit(batch)
```

**JIT compilation (PostgreSQL 11+):**

For CPU-intensive queries, PostgreSQL can JIT-compile expression evaluation and
tuple deforming using LLVM. Controlled by:

```
jit = on
jit_above_cost = 100000       -- enable JIT only for expensive queries
jit_inline_above_cost = 500000
jit_optimize_above_cost = 500000
```

---

## 2. Page Layout and Tuple Structure

### 2.1 The 8 KB Page

PostgreSQL uses a fixed 8 KB page (configurable at compile time but almost never
changed). Every table, index, and TOAST relation is stored as an array of pages.

```
┌────────────────────────────────────────────────────────────────┐
│                        Page (8192 bytes)                       │
├────────────────────────────────────────────────────────────────┤
│  Page Header (24 bytes)                                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ pd_lsn    (8) │ pd_checksum (2) │ pd_flags (2)          │  │
│  │ pd_lower  (2) │ pd_upper   (2)  │ pd_special (2)        │  │
│  │ pd_pagesize_version (2) │ pd_prune_xid (4)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Item Pointers (Line Pointers) — array growing downward        │
│  ┌──────┬──────┬──────┬──────┬─────┐                          │
│  │ lp_1 │ lp_2 │ lp_3 │ lp_4 │ ... │  (4 bytes each)        │
│  └──────┴──────┴──────┴──────┴─────┘                          │
│         pd_lower ↓                                             │
│  ┌─────────────────────────────────────┐                       │
│  │         Free Space                  │                       │
│  └─────────────────────────────────────┘                       │
│         pd_upper ↑                                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Tuple 4 │ Tuple 3 │ Tuple 2 │ Tuple 1                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  Special Space (index-specific metadata)                       │
└────────────────────────────────────────────────────────────────┘
```

**Key details:**

- `pd_lsn`: LSN of last WAL record that modified this page. Used by recovery.
- `pd_checksum`: Optional data checksums (enabled via `initdb --data-checksums`).
  Detects silent corruption from disk/firmware bugs.
- Line pointers grow forward from the header; tuples grow backward from the end.
  They meet in the middle.
- `pd_lower` points to the end of line pointers; `pd_upper` points to the start
  of the first tuple.
- Tuples are never moved within a page (stable TID = page + offset). Line pointers
  can be redirected (HOT updates).

### 2.2 Heap Tuple Header

Every heap tuple (row) in PostgreSQL carries a 23-byte header:

```
HeapTupleHeaderData:
  t_xmin       (4 bytes)  — XID of inserting transaction
  t_xmax       (4 bytes)  — XID of deleting/locking transaction (0 if live)
  t_cid        (4 bytes)  — command ID within the transaction
  t_ctid       (6 bytes)  — current TID (self, or pointer to newer version)
  t_infomask   (2 bytes)  — status flags (committed, aborted, has nulls, etc.)
  t_infomask2  (2 bytes)  — number of attributes + more flags
  t_hoff       (1 byte)   — offset to user data (header + null bitmap size)
```

**The overhead:** For a table with 3 smallint columns (6 bytes of data), each row
consumes 23 (header) + 1 (alignment) + 6 (data) = 30 bytes minimum, plus 4 bytes
for the line pointer = 34 bytes total. This is why narrow tables with billions of
rows have significant overhead.

### 2.3 TOAST (The Oversized Attribute Storage Technique)

When a tuple exceeds ~2 KB (1/4 of page size), PostgreSQL TOASTs large attributes:

1. **Compress** the attribute (pglz or lz4 since PG 14).
2. If still too large, **slice** into chunks stored in a separate TOAST table.
3. Main tuple stores a TOAST pointer (18 bytes) instead of the full value.

**TOAST strategies per column:**

| Strategy | Behavior |
|---|---|
| `PLAIN` | No TOAST (fixed-length types like `int4`) |
| `EXTENDED` | Compress first, then out-of-line if still large (default for `text`) |
| `EXTERNAL` | Out-of-line without compression (good for pre-compressed data) |
| `MAIN` | Compress, but try to keep in-line (only out-of-line as last resort) |

```sql
ALTER TABLE documents ALTER COLUMN body SET STORAGE EXTERNAL;
```

### 2.4 Fillfactor

Controls how much of each page is left free for future HOT updates:

```sql
CREATE TABLE orders (...) WITH (fillfactor = 90);
-- 10% of each page reserved for updates
```

- Default: 100 (pack pages full).
- For tables with frequent UPDATEs on non-indexed columns, set 70-90.
- Lower fillfactor → more pages → larger table → slower seq scans, but enables
  HOT updates (see section 7.3).

---

## 3. Storage & Indexing: The B+ Tree

### 3.1 Why B+ Tree is the Standard

B+ trees dominate RDBMS indexing because they optimize for the fundamental I/O
pattern of databases: block-oriented storage.

**Structure:**

```
                        ┌─────────────────────┐
                        │    Root Node        │
                        │  [30 | 60]          │
                        └──┬──────┬──────┬────┘
                           │      │      │
              ┌────────────┘      │      └────────────┐
              ▼                   ▼                    ▼
     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
     │ Internal Node  │  │ Internal Node  │  │ Internal Node  │
     │ [10 | 20]      │  │ [40 | 50]      │  │ [70 | 80]      │
     └─┬───┬───┬──────┘  └─┬───┬───┬──────┘  └─┬───┬───┬──────┘
       │   │   │            │   │   │            │   │   │
       ▼   ▼   ▼            ▼   ▼   ▼            ▼   ▼   ▼
     ┌───┬───┬───┐        ┌───┬───┬───┐        ┌───┬───┬───┐
     │ 5 │12 │25 │◄──────►│35 │42 │55 │◄──────►│65 │75 │90 │
     │ 8 │15 │28 │        │38 │48 │58 │        │68 │78 │95 │
     └───┴───┴───┘        └───┴───┴───┘        └───┴───┴───┘
      Leaf Nodes (doubly-linked list)
```

- **Internal nodes:** Keys + child pointers. High fan-out (typically 200-500
  keys per node on an 8 KB page).
- **Leaf nodes:** Keys + row pointers (TIDs). Linked as a doubly-linked list.
- **Height:** With fan-out 300, a 3-level tree indexes 300^3 = 27 million rows.
  A 4-level tree indexes 8 billion rows. Height rarely exceeds 4.

**Performance:**

| Operation | Cost |
|---|---|
| Point lookup | O(log_B N) — typically 3-4 page reads |
| Range scan | O(log_B N) to find start, then O(K) sequential reads |
| Insert | O(log_B N) + possible page split |
| Delete | O(log_B N) + possible merge (lazy in practice) |

### 3.2 Index-Only Scans (Covering Indexes)

If the index contains all columns needed by the query, the executor can skip the
heap entirely:

```sql
CREATE INDEX idx_emp_salary ON employees (dept_id, salary);

-- This can be an index-only scan:
SELECT dept_id, salary FROM employees WHERE dept_id = 5;

-- This CANNOT (name is not in the index):
SELECT dept_id, name FROM employees WHERE dept_id = 5;
```

**Visibility map requirement:** PostgreSQL must check the visibility map to confirm
all tuples on each page are visible to all transactions. If a page is "not all-visible"
(recent updates), it falls back to a regular index scan with heap fetches.

**INCLUDE columns (PostgreSQL 11+):**

```sql
CREATE INDEX idx_emp_covering ON employees (dept_id)
INCLUDE (name, salary);
```

The INCLUDE columns are stored in leaf pages but not in internal nodes, so they
do not increase tree height. This enables index-only scans for queries that need
`name` and `salary` without bloating the search key.

### 3.3 Partial Indexes

Index only a subset of rows:

```sql
CREATE INDEX idx_active_orders ON orders (created_at)
WHERE status = 'active';

-- Only ~5% of orders are active → index is 20x smaller
-- Scans of completed orders do not touch this index
```

### 3.4 Expression Indexes

Index the result of an expression:

```sql
CREATE INDEX idx_lower_email ON users (lower(email));

-- Now this query uses the index:
SELECT * FROM users WHERE lower(email) = 'user@example.com';
```

### 3.5 Multi-Column Index Ordering

The leftmost prefix rule:

```sql
CREATE INDEX idx_a_b_c ON t (a, b, c);

-- Uses index: WHERE a = 1
-- Uses index: WHERE a = 1 AND b = 2
-- Uses index: WHERE a = 1 AND b = 2 AND c = 3
-- CANNOT use index efficiently: WHERE b = 2 (skips leading column)
-- CANNOT use index efficiently: WHERE c = 3
```

---

## 4. Hash Indexes

### 4.1 Structure

Hash indexes map keys to buckets via a hash function:

```
hash(key) % num_buckets → bucket_number → overflow chain of TIDs
```

**PostgreSQL hash index layout:**

```
┌─────────────────────────────────────────────┐
│              Meta Page                       │
│  num_buckets, high_mask, low_mask, etc.      │
├─────────────────────────────────────────────┤
│  Bucket 0: [hash_val, TID] → overflow page  │
│  Bucket 1: [hash_val, TID] → overflow page  │
│  Bucket 2: [hash_val, TID]                   │
│  ...                                         │
│  Bucket N: [hash_val, TID] → overflow page  │
└─────────────────────────────────────────────┘
```

### 4.2 When to Use

| Property | B+ Tree | Hash Index |
|---|---|---|
| Equality lookups | O(log N) | O(1) amortized |
| Range scans | Yes (linked leaves) | No |
| ORDER BY | Yes | No |
| Multi-column prefix | Yes | No |
| WAL-logged (PG 10+) | Yes | Yes |
| Size | Larger | Smaller for equality-only |

**Use hash indexes when:**
- Queries are exclusively equality (`=`)
- Column has high cardinality (UUIDs, hashes)
- You need to save space vs. a B+ tree on the same column

**Avoid hash indexes when:**
- Any range query, sorting, or `BETWEEN` is needed
- You might add range queries later (index rebuild required)

### 4.3 Other Index Types

**GiST (Generalized Search Tree):**
- R-tree for spatial data (`geometry`, PostGIS)
- Full-text search (`tsvector`)
- Range types (`int4range`)

**GIN (Generalized Inverted Index):**
- Full-text search (fast lookup, slow updates)
- JSONB containment (`@>`)
- Array containment

**BRIN (Block Range Index):**
- Stores min/max per block range (128 pages default)
- Tiny index size for naturally ordered data (timestamps, auto-increment IDs)
- `SELECT * FROM logs WHERE ts > '2026-01-01'` scans only relevant block ranges

```sql
CREATE INDEX idx_logs_ts ON logs USING brin (created_at)
WITH (pages_per_range = 64);
```

**SP-GiST (Space-Partitioned GiST):**
- Quadtree, k-d tree, radix tree
- Phone number prefix matching, IP range lookups

---

## 5. Buffer Pool (Shared Buffers)

### 5.1 Purpose

The buffer pool is a fixed-size cache of 8 KB pages in shared memory. Its job is
to minimize disk I/O by keeping frequently accessed pages in RAM.

```
                        ┌──────────────────┐
                        │   SQL Query      │
                        └────────┬─────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Buffer Pool         │
                     │   (shared_buffers)     │
                     │                       │
                     │  ┌────┬────┬────┐     │
                     │  │pg 1│pg 5│pg 9│ ... │
                     │  └────┴────┴────┘     │
                     │     Cache Hit?        │
                     └───┬─────────┬─────────┘
                    Yes  │         │  No (Cache Miss)
                         │         │
                         ▼         ▼
                    Return      ┌──────────┐
                    Page        │  OS Page  │
                                │  Cache    │
                                └────┬─────┘
                                     │
                                     ▼
                                ┌──────────┐
                                │   Disk   │
                                └──────────┘
```

### 5.2 Clock-Sweep Eviction (PostgreSQL)

PostgreSQL uses a **clock-sweep** algorithm (variant of CLOCK, which approximates
LRU):

1. Each buffer has a `usage_count` (0 to 5, capped at `BM_MAX_USAGE_COUNT`).
2. When a page is accessed, its `usage_count` increments (up to the cap).
3. When a free buffer is needed, the clock hand sweeps:
   - If `usage_count > 0`, decrement and move on.
   - If `usage_count == 0`, evict this buffer.
4. If the evicted page is dirty, write it to disk first (or let bgwriter do it).

**Why not pure LRU?** LRU is expensive (maintaining a doubly-linked list with
locks in a concurrent system). Clock-sweep provides similar behavior with much
lower contention.

### 5.3 Ring Buffers (Bulk Scan Protection)

A sequential scan of a 100 GB table would flush the entire buffer pool (a "cache
pollution" problem). PostgreSQL mitigates this with **ring buffers:**

- Sequential scans on large tables use a small ring buffer (256 KB = 32 pages).
- Bulk writes (COPY, CREATE TABLE AS) use a 16 MB ring buffer.
- VACUUM uses a 256 KB ring buffer.

This ensures bulk operations do not evict hot pages from the shared buffer pool.

### 5.4 Sizing shared_buffers

**Rule of thumb:** Set `shared_buffers` to 25% of total RAM. The OS page cache
handles the rest.

```
# postgresql.conf
shared_buffers = 8GB         # 25% of 32 GB RAM
effective_cache_size = 24GB  # 75% of RAM (shared_buffers + OS cache estimate)
```

**Monitoring buffer pool hit rate:**

```sql
SELECT
    sum(heap_blks_hit) AS hits,
    sum(heap_blks_read) AS misses,
    round(100.0 * sum(heap_blks_hit) /
          nullif(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2) AS hit_pct
FROM pg_statio_user_tables;
```

Target: > 99% hit rate for OLTP workloads. If below 95%, increase `shared_buffers`
or investigate working set size.

### 5.5 Double Buffering Problem

Data passes through two caches: the database buffer pool and the OS page cache.
This wastes memory. Solutions:

- **Direct I/O:** Bypass OS cache entirely (used by Oracle, MySQL with
  `innodb_flush_method = O_DIRECT`). PostgreSQL does not support direct I/O by
  default (discussions ongoing for PG 18+).
- **Huge pages:** Reduce TLB misses for the large shared_buffers allocation.

```
# postgresql.conf
huge_pages = on

# OS (Linux):
# sysctl vm.nr_hugepages = 4096  (for 8GB at 2MB per page)
```

---

## 6. Write-Ahead Log (WAL)

### 6.1 The Golden Rule

> A log record describing a change must be written to stable storage **before**
> the changed data page is written to stable storage.

This rule guarantees that after a crash, the database can reconstruct any committed
transaction by replaying the WAL, and undo any uncommitted transaction.

### 6.2 WAL Record Structure

```
┌────────────────────────────────────────────────────────┐
│                    WAL Record                          │
├────────────────────────────────────────────────────────┤
│  xl_tot_len    (4)  — total record length              │
│  xl_xid        (4)  — transaction ID                   │
│  xl_prev       (8)  — LSN of previous record           │
│  xl_info       (1)  — resource manager info flags      │
│  xl_rmid       (1)  — resource manager ID              │
│  xl_crc        (4)  — CRC32C checksum                  │
│  ─── header ───────────────────────────────────────    │
│  Block reference(s): relation, fork, block number      │
│  Payload: the actual change data (FPI or delta)        │
└────────────────────────────────────────────────────────┘
```

### 6.3 Full Page Images (FPI)

After a checkpoint, the first modification to any page writes a **full page image**
(the entire 8 KB page) into WAL. Subsequent modifications to the same page (before
the next checkpoint) write only deltas.

**Why?** If a crash occurs during a partial page write (torn page), the FPI
provides a known-good base. This is PostgreSQL's defense against torn pages
without needing double-write buffers (which InnoDB uses).

**Trade-off:** FPIs increase WAL volume significantly right after checkpoints.
`full_page_writes = on` is **mandatory** for data safety.

### 6.4 WAL Segment Files

WAL is stored as a sequence of 16 MB segment files (configurable with
`--wal-segsize` during `initdb`):

```
pg_wal/
├── 000000010000000000000001
├── 000000010000000000000002
├── 000000010000000000000003
└── ...
```

**Timeline + segment naming:** `TTTTTTTTSSSSSSSSSSSSSSSS`
- T = timeline ID (incremented after point-in-time recovery)
- S = segment number

### 6.5 fsync and WAL Flush

**Commit processing:**

```
1. Transaction writes WAL records to WAL buffers (in shared memory)
2. COMMIT record is written to WAL buffer
3. WAL buffers are flushed to disk (fsync)     ← durability guarantee
4. Transaction acknowledged to client
5. Dirty data pages are written later (bgwriter / checkpointer)
```

**fsync methods (wal_sync_method):**

| Method | Behavior | Platform |
|---|---|---|
| `fdatasync` | Flushes file data (not metadata) | Linux (default) |
| `fsync` | Flushes file data + metadata | POSIX |
| `open_datasync` | O_DSYNC on open | Some Unix |
| `open_sync` | O_SYNC on open | Some Unix |

### 6.6 Synchronous Commit Levels

```
synchronous_commit = off     -- WAL not flushed on commit (risk: last ~600ms)
synchronous_commit = local   -- flush local WAL only
synchronous_commit = on      -- flush local WAL (default)
synchronous_commit = remote_write  -- standby has received (OS buffer)
synchronous_commit = remote_apply  -- standby has applied
```

Setting `synchronous_commit = off` risks losing the last ~200-600ms of
transactions on crash, but dramatically improves throughput for workloads
that can tolerate this (e.g., logging, metrics).

### 6.7 ARIES Recovery Algorithm

**ARIES (Algorithm for Recovery and Isolation Exploiting Semantics)** is the
gold-standard crash recovery protocol. PostgreSQL's recovery follows ARIES
principles.

**Three phases:**

```
                WAL Timeline
    ┌──────────────────────────────────────────────┐
    │  ... │ Checkpoint │ ... │ ... │ CRASH        │
    └──────┴─────┬──────┴─────┴─────┴──────────────┘
                 │
                 ▼
    Phase 1: ANALYSIS
    ├── Scan WAL from checkpoint forward
    ├── Build Dirty Page Table (DPT): which pages need redo
    ├── Build Active Transaction Table (ATT): in-flight at crash
    └── Determine starting point for redo (oldest dirty page LSN)

    Phase 2: REDO (repeat history)
    ├── Replay ALL WAL records from redo start point
    ├── Including records of transactions that will be rolled back
    ├── Skip if page LSN >= record LSN (already applied)
    └── Result: database state = exact state at crash moment

    Phase 3: UNDO
    ├── For each loser transaction (in ATT, not committed)
    ├── Scan WAL backward, undo each operation
    ├── Write Compensation Log Records (CLRs) for each undo
    └── CLRs ensure undo is itself crash-safe
```

**Why redo losers?** If transaction T1 modified page P, and transaction T2 (committed)
later modified the same page P, skipping T1's redo would leave P in an inconsistent
state. Redo restores exact crash-point state, then undo cleans up losers.

---

## 7. MVCC (Multi-Version Concurrency Control)

### 7.1 Fundamental Principle

> Readers never block writers. Writers never block readers.

Each transaction sees a **snapshot** of the database as of the transaction's start
time. Modifications create new versions of rows rather than overwriting existing
ones.

### 7.2 PostgreSQL MVCC Implementation

**Version chain via xmin/xmax:**

```
Transaction T100 inserts a row:
  ┌────────────────────────────────────────┐
  │ xmin=100 │ xmax=0 │ data: Alice, 50k  │   ← visible to T100+
  └────────────────────────────────────────┘

Transaction T200 updates salary to 60k:
  ┌────────────────────────────────────────┐
  │ xmin=100 │ xmax=200 │ data: Alice, 50k │  ← dead (marked by T200)
  └────────────────────────────────────────┘
  ┌────────────────────────────────────────┐
  │ xmin=200 │ xmax=0   │ data: Alice, 60k │  ← new version
  └────────────────────────────────────────┘

Transaction T150 (started before T200) still sees:
  xmin=100 is committed and < 150  ✓
  xmax=200 is not committed yet from T150's perspective  ✓
  → T150 sees the old row (Alice, 50k)
```

**Visibility rules (simplified):**

A transaction T sees row R if:
1. `R.xmin` is committed **AND** `R.xmin` started before T's snapshot
2. `R.xmax` is either 0 (not deleted), or uncommitted from T's perspective, or
   started after T's snapshot

**Transaction snapshots:**

PostgreSQL stores the snapshot as:
- `xmin`: Oldest active transaction ID at snapshot time
- `xmax`: First unassigned transaction ID at snapshot time
- `xip_list`: List of all in-progress transaction IDs at snapshot time

```sql
-- View current snapshot:
SELECT txid_current_snapshot();
-- Result: 100:105:100,102,104
-- Meaning: xmin=100, xmax=105, active=[100,102,104]
-- TxIDs < 100 are all committed (or aborted)
-- TxIDs 100, 102, 104 are in-progress
-- TxIDs 101, 103 committed (not in active list)
```

### 7.3 HOT Updates (Heap-Only Tuples)

When an UPDATE does not change any indexed column and the new tuple fits on the
same page, PostgreSQL performs a HOT update:

1. New tuple is written on the same page.
2. Old tuple's `t_ctid` points to new tuple.
3. **No index update needed** — the index still points to the old tuple, which
   redirects to the new one.

**Benefits:** Dramatic reduction in index maintenance and WAL volume for
update-heavy workloads. Requires `fillfactor < 100` to leave room.

```sql
-- Check HOT update ratio:
SELECT
    relname,
    n_tup_hot_upd,
    n_tup_upd,
    round(100.0 * n_tup_hot_upd / nullif(n_tup_upd, 0), 1) AS hot_pct
FROM pg_stat_user_tables
WHERE n_tup_upd > 0
ORDER BY n_tup_upd DESC;
```

### 7.4 InnoDB MVCC (Undo Logs)

MySQL/InnoDB uses a different MVCC approach:

```
Clustered Index (B+ tree):
  ┌──────────────────────────────────────┐
  │  Current Row: Alice, 60k             │
  │  DB_TRX_ID = 200                     │
  │  DB_ROLL_PTR → Undo Log              │
  └──────────────────────────────────────┘
                    │
                    ▼
  ┌──────────────────────────────────────┐
  │  Undo Log Entry: Alice, 50k          │
  │  TRX_ID = 100                         │
  │  ROLL_PTR → older undo entry          │
  └──────────────────────────────────────┘
```

- Only the latest version lives in the B+ tree.
- Previous versions are reconstructed from the undo log.
- **Purge thread** removes undo entries when no transaction needs them.

**Trade-off vs. PostgreSQL:**

| Aspect | PostgreSQL (in-place versions) | InnoDB (undo log) |
|---|---|---|
| Update cost | Write new tuple on heap | Write new tuple + undo entry |
| Read (old version) | Direct heap access | Reconstruct from undo chain |
| Space overhead | Dead tuples accumulate | Undo log grows |
| Cleanup mechanism | VACUUM | Purge thread |
| Long-running tx impact | Blocks VACUUM, bloat | Long undo chains, slow reads |

---

## 8. Lock Manager

### 8.1 Lock Hierarchy

PostgreSQL uses a multi-level lock hierarchy:

```
┌─────────────────────────────────────────────────────────────┐
│  Lock Level          │ Example                              │
├──────────────────────┼──────────────────────────────────────┤
│  Table-level locks   │ ACCESS SHARE, ROW EXCLUSIVE, etc.    │
│  Row-level locks     │ FOR UPDATE, FOR SHARE                │
│  Page-level locks    │ Short-lived, during B-tree operations │
│  Advisory locks      │ Application-defined                   │
└──────────────────────┴──────────────────────────────────────┘
```

### 8.2 Table-Level Lock Modes

```
┌──────────────────────────┬─────────────────────────────────────┐
│ Lock Mode                │ Acquired by                         │
├──────────────────────────┼─────────────────────────────────────┤
│ ACCESS SHARE             │ SELECT                              │
│ ROW SHARE                │ SELECT FOR UPDATE/SHARE             │
│ ROW EXCLUSIVE            │ INSERT, UPDATE, DELETE              │
│ SHARE UPDATE EXCLUSIVE   │ VACUUM, ANALYZE, CREATE INDEX       │
│                          │ CONCURRENTLY                        │
│ SHARE                    │ CREATE INDEX (non-concurrent)       │
│ SHARE ROW EXCLUSIVE      │ CREATE TRIGGER, some ALTER TABLE    │
│ EXCLUSIVE                │ REFRESH MATERIALIZED VIEW           │
│                          │ CONCURRENTLY                        │
│ ACCESS EXCLUSIVE         │ DROP TABLE, ALTER TABLE, VACUUM FULL│
└──────────────────────────┴─────────────────────────────────────┘
```

**Conflict matrix (simplified):** ACCESS SHARE conflicts only with ACCESS EXCLUSIVE.
This is why `SELECT` never blocks on `INSERT/UPDATE/DELETE` and vice versa — they
acquire non-conflicting lock modes.

### 8.3 Row-Level Locks

Row-level locks in PostgreSQL are implemented via tuple header flags (xmax field),
not a separate lock table. This means they scale to millions of locked rows without
memory issues.

```sql
-- Exclusive row lock (blocks other FOR UPDATE):
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;

-- Shared row lock (blocks FOR UPDATE but allows FOR SHARE):
SELECT * FROM accounts WHERE id = 1 FOR SHARE;

-- Skip locked rows (non-blocking queue pattern):
SELECT * FROM tasks WHERE status = 'pending'
LIMIT 1 FOR UPDATE SKIP LOCKED;
```

### 8.4 Deadlock Detection

PostgreSQL runs a deadlock detector (`deadlock_timeout` = 1 second default) that
builds a wait-for graph:

```
Transaction T1 holds lock on Row A, waits for Row B
Transaction T2 holds lock on Row B, waits for Row A
→ Cycle detected → T2 (the latest to enter the wait) is aborted

ERROR:  deadlock detected
DETAIL: Process 12345 waits for ShareLock on transaction 67890;
        blocked by process 67891.
        Process 67891 waits for ShareLock on transaction 12345;
        blocked by process 12345.
```

**Prevention strategies:**

1. Always lock resources in a consistent order (e.g., by primary key ascending).
2. Keep transactions short.
3. Use `SELECT ... FOR UPDATE NOWAIT` to fail fast instead of waiting.
4. Use advisory locks for application-level coordination.

### 8.5 Advisory Locks

Application-defined locks using arbitrary integer keys:

```sql
-- Session-level advisory lock (released at session end):
SELECT pg_advisory_lock(12345);

-- Transaction-level advisory lock (released at commit/rollback):
SELECT pg_advisory_xact_lock(12345);

-- Non-blocking attempt:
SELECT pg_try_advisory_lock(12345);  -- returns true/false
```

Use cases: distributed cron (only one worker runs a job), rate limiting,
preventing duplicate processing.

---

## 9. Vacuum and Autovacuum

### 9.1 Why Vacuum Exists

PostgreSQL's MVCC leaves dead tuples (old row versions) in the heap. Without
cleanup, tables grow indefinitely ("table bloat"). VACUUM reclaims this space.

```
Before VACUUM:
  Page: [Live] [Dead] [Live] [Dead] [Dead] [Live]
  Dead tuples waste 50% of page space

After VACUUM:
  Page: [Live] [Live] [Live] [Free] [Free] [Free]
  Space reclaimed for reuse (but not returned to OS)
```

### 9.2 VACUUM Operations

**Regular VACUUM:**
1. Scan the visibility map to find pages with dead tuples.
2. Remove dead tuples, update the free space map.
3. Update the visibility map (mark all-visible pages).
4. Freeze old transaction IDs (preventing wraparound).
5. Update `pg_class.reltuples` and `pg_class.relpages`.

**Does NOT:**
- Return space to the OS (file size unchanged)
- Block reads or writes (runs concurrently)
- Reorder data on disk

**VACUUM FULL:**
- Rewrites the entire table, compacting it.
- **Acquires ACCESS EXCLUSIVE lock** — blocks everything.
- Returns space to the OS.
- Use only as a last resort for severely bloated tables.

### 9.3 Transaction ID Wraparound

PostgreSQL uses 32-bit transaction IDs (about 4 billion). The system uses modular
arithmetic to determine "before" and "after":

```
  XID space (circular):

  0 ──── 2^31 (2 billion) ──── 2^32 (4 billion)
  │         ▲                        │
  │    "in the past"                 │
  │         │                        │
  └─────────┴────────────────────────┘
        "in the future"
```

If a transaction ID is more than 2 billion XIDs in the past without being "frozen"
(marked as definitively committed), the database will **shut down** to prevent data
corruption:

```
WARNING: database "mydb" must be vacuumed within 10000000 transactions
HINT: To avoid a database shutdown, execute a database-wide VACUUM
```

**VACUUM's freezing duty:**

- When a tuple's xmin is old enough (`vacuum_freeze_min_age` = 50 million by
  default), VACUUM replaces it with `FrozenTransactionId`.
- Frozen tuples are visible to all future transactions regardless of XID.
- `autovacuum_freeze_max_age` (default: 200 million) triggers an **anti-wraparound
  autovacuum** even on tables with no dead tuples.

### 9.4 Autovacuum Configuration

Autovacuum is PostgreSQL's background daemon that triggers VACUUM automatically.

```
# postgresql.conf — critical parameters:

autovacuum = on                       # never turn this off in production
autovacuum_max_workers = 3            # increase for many tables
autovacuum_naptime = 60s              # check interval

# Trigger thresholds:
autovacuum_vacuum_threshold = 50      # min dead tuples before vacuum
autovacuum_vacuum_scale_factor = 0.2  # fraction of table size
# Trigger: dead_tuples > threshold + scale_factor * reltuples
# For a 1M row table: 50 + 0.2 * 1,000,000 = 200,050 dead tuples

autovacuum_analyze_threshold = 50
autovacuum_analyze_scale_factor = 0.1

# Throttling:
autovacuum_vacuum_cost_delay = 2ms    # pause between I/O bursts
autovacuum_vacuum_cost_limit = 200    # I/O budget per cycle
```

**Per-table overrides for high-churn tables:**

```sql
ALTER TABLE events SET (
    autovacuum_vacuum_scale_factor = 0.01,   -- trigger earlier
    autovacuum_vacuum_cost_delay = 0,        -- no throttling
    autovacuum_vacuum_cost_limit = 10000     -- aggressive I/O budget
);
```

### 9.5 Monitoring Vacuum

```sql
-- Dead tuples and last vacuum time:
SELECT
    schemaname, relname,
    n_dead_tup,
    n_live_tup,
    round(100.0 * n_dead_tup / nullif(n_live_tup + n_dead_tup, 0), 1) AS dead_pct,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 20;

-- Transaction ID age (wraparound risk):
SELECT
    datname,
    age(datfrozenxid) AS xid_age,
    2^31 - age(datfrozenxid) AS remaining
FROM pg_database
ORDER BY xid_age DESC;
```

---

## 10. Connection Pooling

### 10.1 The Problem: Process-Per-Connection

PostgreSQL forks a new OS process for each client connection. Each process
consumes:
- ~5-10 MB of RAM (private memory)
- One slot in `max_connections`
- Kernel resources (file descriptors, process table entries)

At 500+ connections, you see:
- Memory pressure (5 GB+ for connections alone)
- Context switching overhead
- Lock contention on shared data structures
- Diminishing returns — throughput peaks around 2-4x CPU cores

### 10.2 PgBouncer

PgBouncer is the standard connection pooler for PostgreSQL. It sits between the
application and PostgreSQL, multiplexing many client connections onto fewer
database connections.

```
┌──────────┐      ┌──────────┐      ┌──────────────────┐
│  App 1   │──────│          │      │                  │
│  (200    │      │          │      │  PostgreSQL      │
│  conns)  │      │ PgBouncer│──────│  (50 actual      │
├──────────┤      │          │      │   connections)   │
│  App 2   │──────│  (pool   │      │                  │
│  (300    │      │   size:  │      │  max_connections  │
│  conns)  │      │   50)    │      │  = 100           │
└──────────┘      └──────────┘      └──────────────────┘
```

**Pool modes:**

| Mode | Behavior | Compatible features |
|---|---|---|
| `session` | Client holds pool connection for entire session | All PG features |
| `transaction` | Connection returned to pool after each transaction | Most features (no session-level state) |
| `statement` | Connection returned after each statement | Very limited (no transactions, no prepared statements) |

**Transaction mode restrictions:**

Cannot use with transaction pooling:
- `SET` commands (session variables) — use `SET LOCAL` instead
- Named prepared statements — use protocol-level prepared statements
- `LISTEN/NOTIFY`
- Advisory locks (session-level)
- Temporary tables — use `ON COMMIT DROP`

**PgBouncer configuration (pgbouncer.ini):**

```ini
[databases]
mydb = host=127.0.0.1 port=5432 dbname=mydb

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3

# Timeouts
server_idle_timeout = 600
client_idle_timeout = 0
query_timeout = 0
client_login_timeout = 60

# Logging
log_connections = 1
log_disconnections = 1
stats_period = 60
```

**Monitoring PgBouncer:**

```sql
-- Connect to PgBouncer admin console:
-- psql -p 6432 -U pgbouncer pgbouncer

SHOW POOLS;
-- database | user | cl_active | cl_waiting | sv_active | sv_idle | sv_used

SHOW STATS;
-- total_xact_count | total_query_count | avg_xact_time | avg_query_time

SHOW CLIENTS;
SHOW SERVERS;
```

### 10.3 Pgpool-II vs PgBouncer

| Feature | PgBouncer | Pgpool-II |
|---|---|---|
| Connection pooling | Yes (lightweight) | Yes |
| Load balancing | No | Yes (read replicas) |
| Replication | No | Yes (native) |
| Query caching | No | Yes |
| Failover | No | Yes (watchdog) |
| Memory footprint | ~2 KB/connection | ~30 KB/connection |
| Complexity | Simple | Complex |

**Recommendation:** Use PgBouncer for pure connection pooling (most cases).
Use Pgpool-II only if you need its load balancing and failover features and
cannot implement those at the application layer.

### 10.4 Application-Level Pooling

Many application frameworks include built-in connection pools:

```python
# Python — psycopg pool (psycopg 3)
from psycopg_pool import ConnectionPool

pool = ConnectionPool(
    conninfo="host=localhost dbname=mydb",
    min_size=5,
    max_size=20,
    max_idle=300,       # close idle connections after 5 min
    max_lifetime=3600,  # recycle connections after 1 hour
)

with pool.connection() as conn:
    conn.execute("SELECT ...")
```

```java
// Java — HikariCP
HikariConfig config = new HikariConfig();
config.setJdbcUrl("jdbc:postgresql://localhost:5432/mydb");
config.setMaximumPoolSize(20);
config.setMinimumIdle(5);
config.setIdleTimeout(300000);
config.setMaxLifetime(1800000);
config.setConnectionTimeout(30000);

HikariDataSource ds = new HikariDataSource(config);
```

**Best practice:** Use application-level pooling AND PgBouncer. The app pool
manages per-instance connection reuse; PgBouncer aggregates across all application
instances.

---

## 11. Transaction Isolation Deep Dive

### 11.1 The Anomalies

| Anomaly | Description | Example |
|---|---|---|
| Dirty Read | Reading uncommitted data | T1 writes, T2 reads, T1 aborts |
| Non-Repeatable Read | Same row, different values | T1 reads, T2 updates + commits, T1 re-reads |
| Phantom Read | Same query, different row set | T1 scans, T2 inserts + commits, T1 re-scans |
| Write Skew | Two txns read overlapping data, write disjoint data, violating a constraint | T1 reads all doctors on-call, T2 reads same, both remove themselves |
| Serialization Anomaly | Result differs from any serial ordering | Counter incremented by two concurrent txns |

### 11.2 Isolation Levels in Practice

| Level | PostgreSQL implementation | MySQL/InnoDB |
|---|---|---|
| Read Uncommitted | Same as Read Committed (PG never does dirty reads) | True dirty reads possible |
| Read Committed | New snapshot per statement | New snapshot per statement |
| Repeatable Read | Snapshot at first statement in txn; detects write conflicts | Snapshot at first statement; gap locks for phantom prevention |
| Serializable | SSI (Serializable Snapshot Isolation) | S2PL + gap locks (traditional locking) |

### 11.3 Serializable Snapshot Isolation (SSI)

PostgreSQL's Serializable level uses SSI (based on Cahill et al. 2008), which
detects serialization anomalies without blocking:

1. Every transaction takes a snapshot (like Repeatable Read).
2. The system tracks **read-write dependencies** between concurrent transactions.
3. If a **dangerous structure** (rw-antidependency cycle) is detected, one
   transaction is aborted with a serialization failure.
4. Application must retry the aborted transaction.

```sql
-- Example: Write Skew with doctor on-call constraint
-- min 1 doctor must be on-call

BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT count(*) FROM doctors WHERE on_call = true;  -- returns 2
-- Both T1 and T2 see count=2, both set themselves off-call
UPDATE doctors SET on_call = false WHERE id = 1;
COMMIT;
-- SSI detects the rw-antidependency cycle and aborts one transaction:
-- ERROR: could not serialize access due to read/write dependencies
```

**SSI vs. 2PL trade-offs:**

| Aspect | SSI (PostgreSQL) | 2PL (MySQL Serializable) |
|---|---|---|
| Blocking | None (optimistic) | Readers block writers |
| Deadlocks | No deadlocks (aborts instead) | Possible deadlocks |
| False aborts | Yes (conservative detection) | No (precise locking) |
| Performance | Better for read-heavy | Better for write-heavy with few conflicts |
| Retry logic required | Yes | No (waits instead) |

---

## 12. Checkpoints and Background Processes

### 12.1 Checkpoints

A checkpoint forces all dirty pages to disk and writes a checkpoint record to WAL:

```
                    Checkpoint
                        │
    WAL: ───────────────┼──────────────────── →
                        │
    At checkpoint:
    1. Write all dirty pages from buffer pool to disk
    2. Write checkpoint record to WAL
    3. Update pg_control with checkpoint location
    4. Recycle old WAL segment files
```

**Checkpoint configuration:**

```
checkpoint_timeout = 5min          # max time between checkpoints
max_wal_size = 1GB                 # WAL size before forcing checkpoint
checkpoint_completion_target = 0.9 # spread writes over 90% of interval
checkpoint_warning = 30s           # warn if checkpoints are too frequent
```

If checkpoints are too frequent (high WAL volume), increase `max_wal_size`.
If they are too infrequent, crash recovery takes longer.

### 12.2 Background Writer (bgwriter)

Proactively writes dirty pages to disk so that the checkpointer has less work
and backend processes do not stall waiting for clean buffers:

```
bgwriter_delay = 200ms            # sleep between rounds
bgwriter_lru_maxpages = 100       # max pages written per round
bgwriter_lru_multiplier = 2.0     # recent activity multiplier
```

### 12.3 WAL Writer

Flushes WAL buffers to disk. Important when `synchronous_commit = off` —
the WAL writer ensures WAL is flushed periodically (every `wal_writer_delay`
= 200ms) even without explicit commits.

### 12.4 Autovacuum Launcher

Manages autovacuum worker processes (see section 9.4).

### 12.5 Stats Collector

Collects table/index usage statistics (access counts, row counts, block reads/hits).
These feed `pg_stat_*` views. In PostgreSQL 15+, replaced by shared memory
statistics.

---

## 13. Partitioning

### 13.1 Why Partition

- **Partition pruning:** Queries touching one time range skip all other partitions.
- **Maintenance isolation:** VACUUM, reindex, or drop individual partitions.
- **Parallel scans:** Each partition can be scanned by a separate worker.
- **Data lifecycle:** Drop old partitions instead of DELETE (instant, no dead tuples).

### 13.2 Partition Types

```sql
-- Range partitioning (most common: time-series):
CREATE TABLE events (
    id        bigint GENERATED ALWAYS AS IDENTITY,
    created   timestamptz NOT NULL,
    payload   jsonb
) PARTITION BY RANGE (created);

CREATE TABLE events_2026_01 PARTITION OF events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE events_2026_02 PARTITION OF events
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- List partitioning:
CREATE TABLE orders (
    id     bigint,
    region text NOT NULL,
    total  numeric
) PARTITION BY LIST (region);

CREATE TABLE orders_eu PARTITION OF orders
    FOR VALUES IN ('eu-west', 'eu-east', 'eu-central');
CREATE TABLE orders_us PARTITION OF orders
    FOR VALUES IN ('us-east', 'us-west');

-- Hash partitioning:
CREATE TABLE sessions (
    id   uuid PRIMARY KEY,
    data jsonb
) PARTITION BY HASH (id);

CREATE TABLE sessions_0 PARTITION OF sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE sessions_1 PARTITION OF sessions
    FOR VALUES WITH (MODULUS 4, REMAINDER 1);
-- ... etc.
```

### 13.3 Partition Pruning

```sql
EXPLAIN SELECT * FROM events WHERE created = '2026-03-15';

-- Output shows only events_2026_03 is scanned:
Append
  ->  Seq Scan on events_2026_03
        Filter: (created = '2026-03-15')
-- All other partitions are pruned at plan time
```

**Runtime pruning** (PostgreSQL 11+): For parameterized queries (`WHERE created = $1`),
pruning happens at execution time when the parameter value is known.

---

## 14. Replication (Single-Primary)

### 14.1 Streaming Replication

PostgreSQL ships WAL segments to standby servers in near-real-time:

```
┌──────────┐    WAL stream    ┌──────────┐
│  Primary  │ ──────────────► │  Standby  │
│           │                 │ (read-only│
│           │                 │  queries) │
└──────────┘                  └──────────┘
```

**Setup (standby):**

```
# postgresql.conf on standby:
primary_conninfo = 'host=primary port=5432 user=replication'
hot_standby = on
```

### 14.2 Replication Lag Monitoring

```sql
-- On primary:
SELECT
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    pg_wal_lsn_diff(sent_lsn, replay_lsn) AS replay_lag_bytes
FROM pg_stat_replication;

-- On standby:
SELECT
    now() - pg_last_xact_replay_timestamp() AS replay_lag;
```

### 14.3 Logical Replication

Unlike streaming replication (physical, byte-level), logical replication decodes
WAL into logical changes:

```sql
-- On publisher:
CREATE PUBLICATION my_pub FOR TABLE orders, customers;

-- On subscriber:
CREATE SUBSCRIPTION my_sub
    CONNECTION 'host=primary port=5432 dbname=mydb'
    PUBLICATION my_pub;
```

Use cases:
- Cross-version upgrades (PG 14 → PG 16)
- Selective table replication
- Multi-primary setups (with conflict resolution)
- Change data capture to external systems

---

## 15. Performance Tuning Checklist

### 15.1 Configuration

```
# Memory
shared_buffers = 25% of RAM (e.g., 8GB for 32GB)
effective_cache_size = 75% of RAM
work_mem = 64MB (increase for sort/hash-heavy queries)
maintenance_work_mem = 1GB (for VACUUM, CREATE INDEX)

# WAL
wal_level = replica
max_wal_size = 4GB
checkpoint_completion_target = 0.9

# Planner
random_page_cost = 1.1 (SSD)
effective_io_concurrency = 200 (SSD)
default_statistics_target = 200 (for complex queries)

# Parallelism
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
parallel_tuple_cost = 0.01
parallel_setup_cost = 1000
```

### 15.2 Query-Level

1. Run `EXPLAIN (ANALYZE, BUFFERS)` to identify actual bottlenecks.
2. Look for sequential scans on large tables — add indexes.
3. Look for estimated vs. actual row mismatches — run `ANALYZE` or create
   extended statistics.
4. Look for hash/sort spilling to disk — increase `work_mem`.
5. Look for nested loop joins on large tables — check if hash/merge join is
   disabled or if statistics are wrong.
6. Use `pg_stat_statements` to find the top queries by total time.

```sql
-- Top 10 queries by total time:
SELECT
    query,
    calls,
    round(total_exec_time::numeric, 1) AS total_ms,
    round(mean_exec_time::numeric, 1) AS mean_ms,
    rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

### 15.3 Index Diagnostics

```sql
-- Unused indexes (candidates for removal):
SELECT
    schemaname, relname, indexrelname,
    idx_scan, idx_tup_read, idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND schemaname NOT IN ('pg_catalog')
ORDER BY pg_relation_size(indexrelid) DESC;

-- Missing indexes (sequential scans on large tables):
SELECT
    schemaname, relname,
    seq_scan, seq_tup_read,
    idx_scan, idx_tup_fetch,
    pg_size_pretty(pg_table_size(relid)) AS size
FROM pg_stat_user_tables
WHERE seq_scan > 100
AND pg_table_size(relid) > 10 * 1024 * 1024  -- >10 MB
ORDER BY seq_tup_read DESC;
```

### 15.4 Bloat Detection

```sql
-- Estimated table bloat using pgstattuple:
CREATE EXTENSION IF NOT EXISTS pgstattuple;

SELECT
    table_len,
    tuple_count,
    dead_tuple_count,
    dead_tuple_len,
    round(100.0 * dead_tuple_len / nullif(table_len, 0), 1) AS dead_pct,
    free_space,
    round(100.0 * free_space / nullif(table_len, 0), 1) AS free_pct
FROM pgstattuple('my_table');
```

---

## 16. Common Pitfalls

### 16.1 Long-Running Transactions

A transaction open for hours prevents VACUUM from cleaning dead tuples created
after the transaction's snapshot. This causes unbounded table bloat.

**Detection:**

```sql
SELECT pid, now() - xact_start AS duration, query
FROM pg_stat_activity
WHERE state = 'idle in transaction'
AND now() - xact_start > interval '5 minutes';
```

**Prevention:**

```
idle_in_transaction_session_timeout = 300000  # 5 minutes, then kill
statement_timeout = 60000                      # 60 seconds per statement
```

### 16.2 Missing ANALYZE After Bulk Load

After loading millions of rows, the planner has stale statistics and may choose
catastrophically bad plans. Always:

```sql
COPY large_table FROM '/data/export.csv' WITH (FORMAT csv);
ANALYZE large_table;
```

### 16.3 Over-Indexing

Each index:
- Slows down INSERT/UPDATE/DELETE (index maintenance)
- Increases WAL volume
- Consumes disk space
- Requires VACUUM maintenance

A table with 15 indexes may spend more time maintaining indexes than serving reads.
Audit with the unused index query above.

### 16.4 SELECT * in Application Code

- Fetches all columns including large TOAST values
- Prevents index-only scans
- Breaks when columns are added/removed
- Wastes network bandwidth

Always specify the columns you need.

### 16.5 Implicit Casts Breaking Index Usage

```sql
-- Column is integer, parameter is text:
SELECT * FROM orders WHERE id = '42';
-- PostgreSQL casts '42' to integer → index used

-- Column is varchar, parameter is integer:
SELECT * FROM users WHERE phone = 5551234;
-- PostgreSQL casts phone column to integer → SEQUENTIAL SCAN
-- Fix: WHERE phone = '5551234'
```

---

## 17. Monitoring Essentials

### 17.1 Key Views

| View | Purpose |
|---|---|
| `pg_stat_activity` | Current connections and queries |
| `pg_stat_user_tables` | Table-level access statistics |
| `pg_stat_user_indexes` | Index usage statistics |
| `pg_statio_user_tables` | Table I/O statistics (buffer hits vs. disk reads) |
| `pg_stat_statements` | Query-level aggregated statistics |
| `pg_stat_replication` | Replication lag and status |
| `pg_stat_bgwriter` | Background writer and checkpoint stats |
| `pg_locks` | Current lock state |
| `pg_stat_wal` | WAL generation statistics (PG 14+) |

### 17.2 Alerting Thresholds

| Metric | Warning | Critical |
|---|---|---|
| Buffer cache hit ratio | < 98% | < 95% |
| Dead tuple ratio | > 10% | > 20% |
| Replication lag | > 1 second | > 10 seconds |
| Transaction ID age | > 150M | > 180M |
| Active connections | > 80% of max | > 95% of max |
| Long-running queries | > 5 minutes | > 30 minutes |
| Lock waits | > 10 seconds | > 60 seconds |

---

## References

- **PostgreSQL Documentation** — postgresql.org/docs/current/
- **ARIES** — Mohan et al., "ARIES: A Transaction Recovery Method Supporting
  Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging,"
  ACM TODS 17(1), 1992.
- **Serializable Snapshot Isolation** — Cahill et al., "Serializable Isolation
  for Snapshot Databases," ACM TODS 34(4), 2009.
- **The Internals of PostgreSQL** — Suzuki, interdb.jp
- **Use The Index, Luke** — use-the-index-luke.com
- **PgBouncer Documentation** — pgbouncer.org

---

## Exercises

### Exercise 1: EXPLAIN ANALYZE Deep Dive

Create a table with at least 1 million rows and several indexes. Write five queries
of increasing complexity (point lookup, range scan, two-table join, three-table join
with aggregation, correlated subquery). For each query:

1. Run `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)`.
2. Record estimated vs. actual row counts at every node.
3. Identify any node where the estimate is off by more than 10x.
4. Run `ANALYZE` on the relevant tables and re-run. Document the plan change.
5. Experiment with `SET random_page_cost = 1.1` (SSD setting) and note whether
   any access method switches from sequential scan to index scan.

### Exercise 2: B+Tree Inspection with pageinspect

Install the `pageinspect` extension and examine a B+tree index:

```sql
CREATE EXTENSION IF NOT EXISTS pageinspect;

-- Inspect the metapage:
SELECT * FROM bt_metap('idx_employees_dept_id');

-- Inspect page 1 (root or internal):
SELECT * FROM bt_page_items('idx_employees_dept_id', 1);

-- Inspect a leaf page:
SELECT * FROM bt_page_items('idx_employees_dept_id', 3);
```

Questions to answer:
1. What is the tree height? How does it relate to the number of indexed rows?
2. How many items fit on a single leaf page? Calculate the effective fan-out.
3. Insert 100,000 rows and re-inspect. Did the height change? Did page splits occur?

### Exercise 3: MVCC Visibility Observation

Open three concurrent `psql` sessions. In session A, begin a REPEATABLE READ
transaction and read a row. In session B, update that row and commit. In session C,
read the row.

1. Verify that session A still sees the old value (snapshot isolation).
2. Query `pg_stat_user_tables` to confirm a dead tuple was created.
3. Run `SELECT xmin, xmax, ctid FROM your_table WHERE id = ?` in all three sessions
   and explain the differences.
4. Run VACUUM on the table and verify the dead tuple count drops, but only after
   session A's transaction ends.

### Exercise 4: Autovacuum Tuning Lab

Create a high-churn table and configure per-table autovacuum overrides:

1. Insert 500,000 rows, then DELETE 400,000. Check `n_dead_tup` in
   `pg_stat_user_tables`.
2. Wait for autovacuum to run (or trigger manually with `VACUUM VERBOSE`).
3. Set `autovacuum_vacuum_scale_factor = 0.01` on the table and repeat.
4. Monitor `pg_stat_progress_vacuum` during a VACUUM run.
5. Compare bloat before and after using `pgstattuple`.

### Exercise 5: Connection Pooling Benchmark

Set up PgBouncer in transaction mode in front of PostgreSQL. Using `pgbench`:

1. Run `pgbench -c 200 -j 4 -T 60` directly against PostgreSQL.
2. Run the same benchmark through PgBouncer with `default_pool_size = 25`.
3. Compare TPS, latency percentiles, and PostgreSQL's `pg_stat_activity` connection
   count between the two runs.
4. Test with `pool_mode = session` and compare overhead.
5. Document which PgBouncer settings (`reserve_pool_size`, `server_idle_timeout`)
   had the most impact on throughput stability.

---

## Readings and References

**Official Documentation (retrieved: 2026-05-29):**

- PostgreSQL 17 — Using EXPLAIN: https://www.postgresql.org/docs/17/using-explain.html
- PostgreSQL 17 — B-Tree Indexes: https://www.postgresql.org/docs/17/btree.html
- PostgreSQL 17 — Concurrency Control (MVCC): https://www.postgresql.org/docs/17/mvcc.html
- PostgreSQL 17 — WAL Configuration: https://www.postgresql.org/docs/17/wal-configuration.html
- PostgreSQL 17 — WAL Internals: https://www.postgresql.org/docs/17/wal-internals.html
- PostgreSQL 17 — ANALYZE: https://www.postgresql.org/docs/17/sql-analyze.html
- PostgreSQL 17 — Routine Vacuuming: https://www.postgresql.org/docs/17/routine-vacuuming.html
- PostgreSQL 17 — Database Page Layout: https://www.postgresql.org/docs/17/storage-page-layout.html

**Books:**

- Kleppmann, Martin. *Designing Data-Intensive Applications*. O'Reilly, 2017.
  Chapters 3 (Storage and Retrieval) and 7 (Transactions).
- Suzuki, Hironobu. *The Internals of PostgreSQL*. Self-published, 2015--2024.
  Available at https://www.interdb.jp/pg/

**Papers:**

- Mohan, C. et al. "ARIES: A Transaction Recovery Method Supporting Fine-Granularity
  Locking and Partial Rollbacks Using Write-Ahead Logging." *ACM Transactions on
  Database Systems* 17(1), March 1992. https://dl.acm.org/doi/10.1145/128765.128770
- Cahill, Michael J. et al. "Serializable Isolation for Snapshot Databases."
  *ACM Transactions on Database Systems* 34(4), December 2009.
- Lehman, P.L. and Yao, S.B. "Efficient Locking for Concurrent Operations on
  B-Trees." *ACM Transactions on Database Systems* 6(4), December 1981.

**Online Resources (retrieved: 2026-05-29):**

- Use The Index, Luke (B-tree visualization and SQL tuning): https://use-the-index-luke.com/
- PgBouncer Documentation: https://www.pgbouncer.org/
- pganalyze — Basics of Postgres Query Planning: https://pganalyze.com/docs/explain/basics-of-postgres-query-planning

---

## Cross-References

| Module | File | Relationship |
|---|---|---|
| 3.2 — Distributed Consensus & Replication | `03_Database_Engineering/02_Distributed_Consensus.md` | WAL shipping drives streaming replication; consensus algorithms coordinate replicas |
| 3.3 — Storage Engines & NoSQL | `03_Database_Engineering/03_Storage_Engines_NoSQL.md` | Contrasts B+tree heap storage with LSM-tree and document stores |
| 3.4 — Data Engineering OLAP/OLTP | `03_Database_Engineering/04_Data_Engineering_OLAP_OLTP.md` | OLTP tuning (this module) vs. columnar OLAP trade-offs |
| 1.4 — Compilers & Interpreters | `01_Foundations/04_Compilers_Interpreters.md` | SQL parser/analyzer stage mirrors compiler front-end (lexer, AST, semantic analysis) |
| 2.1 — Code-Level Architecture | `02_Architecture_Design/01_Code_Level_Architecture.md` | Connection pooling and query patterns inform application-level data-access design |
| 4.1 — Application Security | `04_Security_Cryptography/01_Application_Security.md` | SQL injection prevention, parameterized queries, row-level security |

---

## Glossary

| Term | Definition |
|---|---|
| **AST (Abstract Syntax Tree)** | Tree representation of SQL syntax produced by the parser; input to semantic analysis. |
| **B+Tree** | Balanced tree index structure where internal nodes store keys and child pointers, leaf nodes store keys and row pointers (TIDs), and leaves are linked for efficient range scans. |
| **Buffer Pool** | Fixed-size shared-memory cache of 8 KB pages (`shared_buffers`) that minimizes disk I/O by keeping hot pages in RAM. |
| **Cardinality Estimation** | The planner's prediction of how many rows a query node will produce; drives join-order and access-method decisions. |
| **CBO (Cost-Based Optimizer)** | Query planner strategy that enumerates plans, estimates their cost using statistics, and picks the cheapest. |
| **Fillfactor** | Per-table storage parameter (0--100) controlling how full each heap page is packed; values below 100 reserve space for HOT updates. |
| **HOT Update (Heap-Only Tuple)** | An UPDATE that places the new tuple on the same heap page and requires no index-entry changes, enabled when no indexed column changes and free space exists on the page. |
| **LSN (Log Sequence Number)** | Monotonically increasing 64-bit pointer into the WAL stream; used to track which WAL records have been applied to a page. |
| **MVCC (Multi-Version Concurrency Control)** | Concurrency scheme where each transaction sees a consistent snapshot; readers never block writers because old row versions are retained until vacuumed. |
| **TOAST (The Oversized Attribute Storage Technique)** | PostgreSQL mechanism that compresses and/or out-of-lines large column values exceeding approximately 2 KB. |
| **Visibility Map** | Per-table bitmap tracking which heap pages contain only tuples visible to all transactions; enables index-only scans and guides VACUUM. |
| **WAL (Write-Ahead Log)** | Append-only log of all data modifications; guarantees durability by requiring the log record to be flushed to disk before the corresponding data page. |
| **XID (Transaction ID)** | 32-bit identifier assigned to each write transaction in PostgreSQL; subject to wraparound requiring periodic VACUUM freezing. |
| **Autovacuum** | Background daemon that automatically triggers VACUUM and ANALYZE based on configurable dead-tuple thresholds and table activity. |
| **SSI (Serializable Snapshot Isolation)** | PostgreSQL's implementation of the Serializable isolation level; detects rw-antidependency cycles among concurrent transactions and aborts one to prevent anomalies. |
