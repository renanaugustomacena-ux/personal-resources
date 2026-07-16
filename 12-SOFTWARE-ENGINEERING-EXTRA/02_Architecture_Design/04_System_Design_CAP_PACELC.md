# Module 2.4: System Design — Scalability, CAP, PACELC

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
