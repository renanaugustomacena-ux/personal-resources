---
corso: "SWE Masterclass"
fase: "2 — Architecture & Design"
modulo: "2.4"
titolo: "System Design — Scalability, CAP, PACELC"
versione: "2026-05 (post-NewSQL era)"
livello: "Advanced"
prerequisiti:
  - "Understanding of client-server and request-response models"
  - "Familiarity with TCP/IP networking, DNS, and HTTP"
  - "Experience with at least one relational and one NoSQL database"
  - "Basic knowledge of replication and sharding concepts"
  - "Completion of Module 2.2 (Distributed System Patterns) recommended"
obiettivi:
  - "Classify a distributed system as CP, AP, or PA/EL vs PC/EC using the PACELC framework and justify the classification"
  - "Design a caching strategy combining write patterns (write-through, write-back, cache-aside) with eviction policies for a given workload"
  - "Select and justify a sharding strategy (range, hash, directory, geo) for a concrete data model and access pattern"
  - "Configure quorum parameters (N, W, R) to achieve the desired consistency-availability trade-off for a multi-region deployment"
  - "Compare consistency models (linearizability through eventual) and map each to real database products and their configuration knobs"
tag: [cap-theorem, pacelc, consistency, availability, partition-tolerance, sharding, replication, quorum, caching, load-balancing, distributed-systems, scalability]
---

# Module 2.4: System Design — Scalability, CAP, PACELC

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Apply the CAP theorem and PACELC framework to evaluate distributed database trade-offs for a given workload
> - Design a multi-tier caching architecture with appropriate write patterns, TTL policies, and eviction strategies
> - Select a sharding strategy and consistent hashing configuration that minimizes hot-shard risk for a given key distribution
> - Configure replication topology (single-leader, multi-leader, leaderless) and quorum settings to meet SLA targets for consistency and latency
> - Map real-world database products to their position on the consistency spectrum and tune per-request consistency levels

> **Module 02.4** · **Last updated:** 2026-04-27

## Guiding ideas
1. **Brewer's CAP (2000): in partition, choose Consistency or Availability.**
2. **PACELC (2010 extension): Else (no partition) Latency vs Consistency.**
3. **ACID vs BASE: trade-off in NoSQL.**
4. **Decision matrix: tipo workload → CP, AP, CA selection.**
5. **Lynch's proof: CAP is theorem not folklore.**


**Date:** 2026-04-22
**Status:** Completed

## 1. Vertical vs Horizontal Scaling

*   **Vertical (scale-up):** bigger box — more cores, RAM, NVMe. Bounded by single-node ceilings; no fault tolerance from replication; simpler consistency.
*   **Horizontal (scale-out):** more boxes behind a coordinator. Near-linear capacity gains for stateless workloads, sub-linear for stateful ones (coordination overhead). Fault-tolerant by design.
*   **Heuristic:** scale up until the price/performance knee, then scale out. Most production systems are *both* (large nodes, multiple replicas).

## 2. Load Balancing

### 2.1 L4 vs L7
*   **L4 (transport):** routes by `(src_ip, src_port, dst_ip, dst_port, proto)`. Fast, protocol-agnostic. Examples: AWS NLB, IPVS, HAProxy `mode tcp`.
*   **L7 (application):** parses HTTP/2/gRPC; routes by host, path, header, cookie. Enables canary, A/B, mTLS termination. Examples: Envoy, NGINX, ALB, Traefik.

### 2.2 Algorithms
*   **Round-robin** — uniform but ignores load.
*   **Least-connections** — routes to backend with fewest active conns; better under heterogeneous request cost.
*   **Weighted round-robin / WLC** — capacity-aware.
*   **Power of two choices (P2C):** pick 2 random backends, send to less loaded. O(1), near-optimal tail latency. Used by Finagle, Envoy.
*   **Consistent hashing** — minimizes reshuffling on backend membership change (see §6).
*   **Sticky sessions:** route same client → same backend via cookie or hash. Required for in-memory session state, but violates stateless ideal and complicates failover.

## 3. Caching Strategies

### 3.1 Write Patterns
*   **Write-through:** write hits cache and DB synchronously. Strong cache consistency, higher write latency.
*   **Write-back (write-behind):** write hits cache; DB updated asynchronously. Lowest write latency, *risk of data loss on cache crash before flush*.
*   **Write-around:** write goes to DB only; cache populated on next read. Avoids cache pollution by cold writes.
*   **Cache-aside (lazy loading):** app code checks cache, reads DB on miss, populates cache. Simple, dominant in practice (Redis + app).

### 3.2 TTL & Eviction
*   **TTL** bounds staleness regardless of access pattern.
*   **LRU** — evict least recently used. Hash + doubly-linked list, O(1).
*   **LFU** — least frequently used; better for stable hot sets, expensive to track.
*   **ARC (Adaptive Replacement Cache):** balances recency and frequency via two LRU lists with adaptive sizing. Used by ZFS L2ARC, PostgreSQL clock-sweep is a related approximation.
*   **W-TinyLFU (Caffeine):** admission filter (Count-Min sketch) + segmented LRU. Best hit ratio in current literature.

## 4. Sharding

Horizontal partitioning of data across nodes.

| Strategy | How | Pros | Cons |
|---|---|---|---|
| **Range** | `id < 1000 → S1`, `1000-2000 → S2` | Range scans local | Hot shard on monotonic keys |
| **Hash** | `shard = hash(key) mod N` | Uniform load | No range scans; resharding costly (use consistent hashing instead) |
| **Directory** | Lookup table maps key → shard | Flexible, easy rebalance | Lookup is a SPOF / extra hop |
| **Geo** | By region | Locality, regulatory | Skew if usage is regional |

**Hot-shard problem:** one key (or key prefix) absorbs disproportionate traffic. Mitigations: salt keys, split shard, route hot keys to a dedicated tier, replicate read-only.

## 5. Consistent Hashing

Designed for dynamic membership without mass re-keying.

*   Map both keys and nodes onto a circular hash space `[0, 2^k)`.
*   Key owned by the next node clockwise.
*   Adding/removing node `N` only reassigns keys between `N` and its predecessor → expected `K/N` keys move.
*   **Virtual nodes (vnodes):** each physical node owns hundreds of evenly-distributed positions → smooths load, allows weighted nodes.
*   *Used by:* Amazon Dynamo (origin), Cassandra, ScyllaDB, Riak, Memcached client (`ketama`), Envoy `ring_hash`, Akamai DSR.

## 6. Replication

### 6.1 Topologies
*   **Single-leader (master-slave):** writes to leader, async/sync replication to followers. Simple, dominant model (PostgreSQL streaming repl, MySQL binlog, MongoDB replica set).
*   **Multi-leader (master-master):** writes accepted at multiple sites; conflicts resolved via LWW, vector clocks, or CRDTs. Use cases: multi-region, offline-tolerant clients.
*   **Leaderless:** any node accepts any write; client coordinates via quorums (Dynamo, Cassandra).

### 6.2 Quorum (N, W, R)
*   `N` = replicas, `W` = nodes that must ack a write, `R` = nodes read.
*   **Strong consistency requires `W + R > N`** (read and write quorums overlap).
*   Common choices: `N=3, W=2, R=2` (balanced); `W=N, R=1` (read-heavy); `W=1, R=N` (write-heavy, rare).
*   Sloppy quorum + hinted handoff trade strict overlap for availability under partition.

## 7. CAP Theorem

Brewer 2000, proven by Gilbert & Lynch 2002. *In the presence of a network **P**artition, a distributed system must choose between **C**onsistency (linearizability) and **A**vailability.*

*   **CP:** refuse requests that cannot be linearized. Examples: HBase, Zookeeper, etcd, Spanner (under partition).
*   **AP:** keep serving, accept divergent state, reconcile later. Examples: Cassandra, DynamoDB (default), Riak, CouchDB.
*   *"CA"* is a misnomer — every real system spans a network and therefore experiences partitions; the choice is forced when one occurs.

## 8. PACELC

Abadi 2010 extension that captures the *normal-operation* trade-off CAP ignores.

*   **If P**artition: choose **A**vailability or **C**onsistency.
*   **Else (no partition):** choose **L**atency or **C**onsistency.

| System | Classification |
|---|---|
| Cassandra (default) | **PA/EL** |
| DynamoDB (default) | **PA/EL** |
| MongoDB (default) | **PA/EC** |
| HBase | **PC/EC** |
| Spanner | **PC/EC** (TrueTime keeps L low) |
| BigTable | **PC/EC** |
| etcd, Zookeeper | **PC/EC** |

PACELC explains why two AP systems (Cassandra vs MongoDB) feel different in steady state.

## 9. Consistency Models (strongest → weakest)

*   **Linearizability:** every operation appears to take effect atomically at some instant between invocation and response, consistent with real-time order. Single-copy semantics.
*   **Sequential consistency:** all clients see the same total order; that order need not match real time.
*   **Causal consistency:** operations causally related are seen in the same order by all observers; concurrent ops may diverge. Implementable with vector clocks.
*   **Read-your-writes / monotonic reads / monotonic writes:** session guarantees, weaker than causal.
*   **Eventual consistency:** absent new updates, replicas converge. No bound on staleness window without anti-entropy (read-repair, Merkle trees, hinted handoff).

### 9.1 Practical Implications
*   **Linearizability** requires consensus (Paxos/Raft) or external time (Spanner TrueTime). Cost: latency + reduced availability under partition.
*   **Causal consistency** is the strongest model **achievable with availability under partition** (Mahajan et al., 2011).
*   Most production systems offer **tunable consistency per request** (Cassandra `ONE`/`QUORUM`/`ALL`, DynamoDB strongly-consistent reads). Pick per use case, not globally.

---

## Exercises

### Exercise 1: PACELC Classification (Beginner)

You are evaluating three databases for a new project: PostgreSQL (single-node), CockroachDB (multi-region), and Redis Cluster.

1. Classify each under the PACELC framework. Justify each classification.
2. For each, describe what happens during a 30-second network partition between two data centers.
3. Identify which database you would choose for: (a) a financial ledger, (b) a session cache, (c) a social media feed. Justify each choice using PACELC.

**Acceptance criteria:** Each classification references the specific consistency and availability behavior of the product, not just generic CP/AP labels.

### Exercise 2: Caching Strategy Design (Intermediate)

Design a multi-tier caching architecture for an e-commerce product catalog with:
- 10 million products, 500 reads/second, 5 writes/second
- 99th percentile read latency target: < 50ms
- Staleness tolerance: 30 seconds for product details, 0 seconds for inventory count

1. Select write pattern (write-through, write-back, cache-aside) for each data type and justify.
2. Choose an eviction policy (LRU, LFU, W-TinyLFU) and set TTL values.
3. Design the cache invalidation strategy when a product is updated.
4. Calculate the cache hit ratio needed to meet the latency SLA, assuming a cache hit takes 2ms and a DB read takes 200ms.

**Acceptance criteria:** The design includes a diagram, TTL/eviction configuration, and the hit-ratio calculation.

### Exercise 3: Sharding and Consistent Hashing (Intermediate)

You have a messaging system with 100 million users. Messages are keyed by `(sender_id, receiver_id, timestamp)`.

1. Evaluate range sharding by `sender_id` — identify the hot-shard risk for celebrity accounts.
2. Implement a consistent hash ring with 150 virtual nodes per physical node. Simulate adding and removing a node; measure the percentage of keys that migrate.
3. Design a composite sharding key that balances write distribution while preserving query locality for "get all messages between user A and user B."
4. Propose a mitigation for the celebrity hot-shard problem (salting, dedicated tier, or read replicas).

**Acceptance criteria:** The simulation shows < 1/N key migration on node addition with virtual nodes. The composite key supports the primary query without scatter-gather.

### Exercise 4: Quorum Configuration Under Failure (Advanced)

You operate a 5-node leaderless cluster (N=5) across 3 availability zones (AZ-A: 2 nodes, AZ-B: 2 nodes, AZ-C: 1 node).

1. Determine the W and R values needed for strong consistency.
2. Simulate AZ-C going offline (1 node lost). Can you still achieve strong consistency? What are the new effective quorum sizes?
3. Simulate AZ-B going offline (2 nodes lost). What consistency level is achievable? What is the impact on write availability?
4. Design a sloppy quorum + hinted handoff strategy for the AZ-B failure scenario. What is the staleness window?
5. Recommend a configuration that survives any single-AZ failure while maintaining strong consistency.

**Acceptance criteria:** Each scenario includes the math (W + R > N check), the availability impact, and the consistency guarantee.

### Exercise 5: End-to-End System Design — Multi-Region Chat (Advanced)

Design a multi-region chat application serving users in US-East, EU-West, and AP-Southeast:

1. Choose a replication topology (single-leader, multi-leader, leaderless) and justify using PACELC.
2. Design the message ordering strategy: causal consistency with vector clocks, or eventual with LWW.
3. Define the conflict resolution policy for simultaneous edits to the same message from two regions.
4. Select a database product and map its configuration knobs to your consistency requirements.
5. Calculate the expected replication lag between regions (assume 80ms cross-Atlantic RTT, 180ms US-to-AP RTT).

**Deliverable:** An architecture diagram with region placement, replication topology, consistency model, and conflict resolution strategy. Include a PACELC classification table for your design.

---

## Readings and References

### Books

1. Kleppmann, M. *Designing Data-Intensive Applications*. O'Reilly, 2017. ISBN 978-1449373320. — Chapters 5-9 cover replication, partitioning, consistency, and consensus.
2. Tanenbaum, A.S., Van Steen, M. *Distributed Systems*. 4th ed., 2023. ISBN 978-9081540636.
3. Burns, B. *Designing Distributed Systems*. O'Reilly, 2018. ISBN 978-1491983645.
4. Petrov, A. *Database Internals: A Deep Dive into How Distributed Data Systems Work*. O'Reilly, 2019. ISBN 978-1492040347.

### Papers

5. Brewer, E. "Towards Robust Distributed Systems." Keynote, ACM PODC, 2000.
6. Gilbert, S., Lynch, N. "Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services." *ACM SIGACT News*, 33(2), 2002, pp. 51-59.
7. Abadi, D. "Consistency Tradeoffs in Modern Distributed Database System Design: CAP is Only Part of the Story." *IEEE Computer*, 45(2), 2012, pp. 37-42.
8. DeCandia, G. et al. "Dynamo: Amazon's Highly Available Key-value Store." *SOSP*, 2007.
9. Corbett, J. et al. "Spanner: Google's Globally-Distributed Database." *OSDI*, 2012.
10. Mahajan, P., Alvisi, L., Dahlin, M. "Consistency, Availability, and Convergence." Technical Report TR-11-22, UT Austin, 2011.
11. Lamport, L. "The Part-Time Parliament." *ACM TOCS*, 16(2), 1998, pp. 133-169. — Paxos.
12. Ongaro, D., Ousterhout, J. "In Search of an Understandable Consensus Algorithm." *USENIX ATC*, 2014. — Raft.

### Articles and Online Resources

13. Whittaker, M. "An Illustrated Proof of the CAP Theorem." Retrieved: 2026-05-29. https://mwhittaker.github.io/blog/an_illustrated_proof_of_the_cap_theorem/
14. Wikipedia. "CAP theorem." Retrieved: 2026-05-29. https://en.wikipedia.org/wiki/CAP_theorem
15. Abadi, D. "Consistency Tradeoffs in Modern Distributed Database System Design." *IEEE Xplore*. Retrieved: 2026-05-29. https://ieeexplore.ieee.org/document/6127847/
16. Java Code Geeks. "Beyond CAP: Why the PACELC Model Is a Better Framework for Database Decisions in 2026." Retrieved: 2026-05-29. https://www.javacodegeeks.com/2026/04/beyond-cap-why-the-pacelc-model-is-a-better-framework-for-database-decisions-in-2026.html
17. DesignGurus. "CAP Theorem vs PACELC: Understanding Distributed System Trade-offs." Retrieved: 2026-05-29. https://www.designgurus.io/blog/system-design-interview-basics-cap-vs-pacelc
18. Gilbert, S., Lynch, N. "Perspectives on the CAP Theorem." Retrieved: 2026-05-29. https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf

---

## Cross-References

| Module | Relationship to This Module |
|---|---|
| [01_Code_Level_Architecture.md](./01_Code_Level_Architecture.md) | CQRS and Event Sourcing patterns whose persistence layer is governed by CAP/PACELC trade-offs |
| [02_Distributed_System_Patterns.md](./02_Distributed_System_Patterns.md) | Saga, consensus protocols, and service discovery that implement the consistency and availability guarantees discussed here |
| [02_b_High_Performance_System_Design.md](./02_b_High_Performance_System_Design.md) | Caching tiers, connection pooling, and backpressure patterns that optimize latency within the PACELC "Else Latency" dimension |
| [03_Design_Principles_SOLID_etc.md](./03_Design_Principles_SOLID_etc.md) | KISS and YAGNI principles that prevent over-engineering consistency guarantees beyond what the workload requires |
| [../03_Database_Engineering/](../03_Database_Engineering/) | Schema design, indexing, replication configuration, and transaction isolation levels for the databases classified in the PACELC table |
| [../05_DevOps_Cloud_Native/](../05_DevOps_Cloud_Native/) | Infrastructure provisioning, multi-region deployment, and observability that operationalize the scalability and replication strategies |

---

## Glossary

| Term | Definition |
|---|---|
| **Anti-Entropy** | Background processes (read-repair, Merkle tree comparison, hinted handoff) that detect and resolve replica divergence. |
| **Availability (CAP)** | Every non-failing node returns a response for every request it receives, with no bound on staleness. |
| **Cache-Aside (Lazy Loading)** | A caching pattern where the application checks the cache on read, falls back to the database on miss, and populates the cache with the result. |
| **Causal Consistency** | A consistency model where operations with a causal relationship are seen in the same order by all observers; concurrent operations may be seen in different orders. |
| **Consistent Hashing** | A hash-based partitioning scheme where both keys and nodes are mapped onto a circular space, minimizing key redistribution when nodes join or leave. |
| **Eventual Consistency** | A consistency model where, absent new updates, all replicas will eventually converge to the same state. No bound on the convergence window without anti-entropy. |
| **Hinted Handoff** | A technique where a write destined for an unavailable node is temporarily stored on another node, which forwards it when the target recovers. |
| **Linearizability** | The strongest consistency model: every operation appears to take effect atomically at some instant between its invocation and response, consistent with real-time order. |
| **PACELC** | An extension of CAP (Abadi, 2012) stating: if Partition → choose Availability or Consistency; Else → choose Latency or Consistency. |
| **Partition Tolerance (CAP)** | The system continues to operate despite arbitrary message loss or delay between network segments. |
| **Quorum** | A voting mechanism where a write must be acknowledged by W replicas and a read must contact R replicas. Strong consistency requires W + R > N. |
| **Sloppy Quorum** | A quorum where the W or R nodes may include nodes outside the key's designated replica set, trading strict consistency for higher availability. |
| **Vector Clock** | A data structure that tracks causal ordering of events across distributed nodes, represented as a vector of logical timestamps — one per node. |
| **Virtual Node (vnode)** | A technique in consistent hashing where each physical node is assigned multiple positions on the hash ring to improve load distribution. |
| **Write-Back (Write-Behind)** | A caching pattern where writes hit the cache first and are asynchronously flushed to the database, risking data loss on cache failure before flush. |
