# Phase 3: Advanced Database Engineering — Syllabus

> **Last updated:** 2026-05-29

This phase dives into how data is stored, protected, and distributed.

## Module 3.1: Relational Internals (The Single Node)

**Goal:** Understand what happens when you type `COMMIT`.

| File | Focus |
|---|---|
| [01_Relational_Internals.md](01_Relational_Internals.md) | B+Tree, WAL, MVCC, query planning, autovacuum, connection pooling |

*   **Storage Structures:** B+ Trees (high fan-out, cache-friendly), Heap Files.
*   **Transaction Management (ACID):** WAL and Checkpoints. Isolation levels. MVCC.
*   **Concurrency Control:** 2PL, Snapshot Isolation, SSI (Serializable Snapshot Isolation).

## Module 3.2: Distributed Consensus & Replication

**Goal:** Agree on "Truth" across unreliable networks.

| File | Focus |
|---|---|
| [02_Distributed_Consensus.md](02_Distributed_Consensus.md) | Raft, Paxos, CRDTs, gossip, replication topologies, FLP impossibility |

*   **Consensus Algorithms:** Raft (leader election, log replication), Paxos.
*   **Replication Patterns:** Leader-Follower, Multi-Leader, Leaderless (Dynamo-style quorum).
*   **Conflict Resolution:** LWW, Vector Clocks, HLC, CRDTs.

## Module 3.3: Storage Engines & NoSQL

**Goal:** Optimize for specific access patterns (Write-heavy vs Scan-heavy).

| File | Focus |
|---|---|
| [03_Storage_Engines_NoSQL.md](03_Storage_Engines_NoSQL.md) | LSM-trees, B-tree vs LSM trade-offs, Redis, Cassandra, MongoDB, graph DBs, NewSQL |

*   **LSM Trees:** MemTable, WAL, SSTables. Leveled vs Tiered compaction. Write amplification.
*   **Columnar Storage:** RLE, Delta Encoding, vectorized execution (SIMD).
*   **NoSQL Models:** Document (MongoDB), Wide-Column (Cassandra), Graph (Neo4j), Key-Value (Redis).

## Module 3.4: Data Engineering — OLTP vs OLAP, Warehouses, Lakes

**Goal:** Design end-to-end data pipelines from operational to analytical workloads.

| File | Focus |
|---|---|
| [04_Data_Engineering_OLAP_OLTP.md](04_Data_Engineering_OLAP_OLTP.md) | Star schema, column stores, dbt, Iceberg/Delta Lake, medallion architecture |

*   **OLTP vs OLAP:** Row-store vs column-store, workload isolation.
*   **Data Warehousing:** Kimball star schema, Inmon 3NF, materialized views.
*   **Modern Data Stack:** ELT, dbt, open table formats (Iceberg, Delta Lake), lakehouse architecture.
