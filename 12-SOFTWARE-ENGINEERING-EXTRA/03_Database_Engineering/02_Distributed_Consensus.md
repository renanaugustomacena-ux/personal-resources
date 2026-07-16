# Module 3.2: Distributed Consensus & Replication

> **Module 03.2** · **Last updated:** 2026-05-22

## Guiding ideas
1. **Paxos hard to understand; Raft designed for clarity.**
2. **Raft phases: leader election + log replication + safety.**
3. **etcd-io/raft: production reference impl.**
4. **Election edge cases: split vote, partition, byzantine considerations.**
5. **Multi-Paxos / EPaxos for scale.**

---

## 1. Why Consensus?

Distributed systems face a fundamental problem: multiple nodes must agree on a
single value (or sequence of values) even when some nodes crash, messages are lost,
or the network partitions. Consensus algorithms solve this.

**Use cases:**
- Electing a leader for a replicated state machine
- Committing a distributed transaction
- Agreeing on configuration changes (cluster membership)
- Ordering log entries identically across replicas

### 1.1 The FLP Impossibility Result

Fischer, Lynch, and Paterson (1985) proved that in a purely asynchronous system
with even one possible crash failure, **no deterministic consensus algorithm can
guarantee termination** in all executions.

**Practical impact:** Every real consensus algorithm uses one of these escapes:
- **Randomization:** Probabilistic progress (e.g., Ben-Or algorithm)
- **Failure detectors:** Timeouts to suspect crashed nodes (Raft, Paxos in practice)
- **Partial synchrony:** Assume the network is eventually timely (Dwork, Lynch, Stockmeyer 1988)

All production systems (etcd, ZooKeeper, CockroachDB) rely on timeouts — they are
partially synchronous systems. During asynchronous periods (network partition), they
may lose liveness (cannot make progress) but never violate safety (never return
incorrect results).

### 1.2 The CAP Theorem

Brewer (2000), proved by Gilbert and Lynch (2002):

```
    Consistency ─── Availability
         \            /
          \          /
           \        /
       Partition Tolerance
```

A distributed system can guarantee at most two of:
- **Consistency:** Every read returns the most recent write
- **Availability:** Every request receives a response
- **Partition Tolerance:** The system continues operating despite network partitions

Since network partitions are unavoidable in distributed systems, the real choice
is between **CP** (consistent during partition, may reject requests) and **AP**
(available during partition, may return stale data).

| System | Choice | Behavior during partition |
|---|---|---|
| etcd, ZooKeeper, Spanner | CP | Minority partition rejects writes |
| Cassandra, DynamoDB | AP | All partitions accept writes; reconcile later |
| CockroachDB | CP | Ranges with no majority quorum become unavailable |

---

## 2. Paxos (The Foundation)

Leslie Lamport, 1989 (published 1998). The first proven-correct consensus
algorithm for asynchronous crash-failure systems with partial synchrony.

### 2.1 Roles

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│  Proposer  │     │  Acceptor  │     │  Learner   │
│            │     │            │     │            │
│ Suggests   │     │ Votes on   │     │ Learns the │
│ values     │     │ proposals  │     │ chosen     │
│            │     │            │     │ value      │
└────────────┘     └────────────┘     └────────────┘
```

In practice, a single node often plays all three roles. A quorum is a majority of
acceptors: for 2f+1 acceptors, a quorum is f+1.

### 2.2 Single-Decree Paxos (Synod Protocol)

Agrees on a single value. Two phases:

```
Phase 1: PREPARE
══════════════════════════════════════════════════

Proposer                         Acceptors (A1, A2, A3)
   │                                │    │    │
   │── Prepare(n=5) ───────────────►│    │    │
   │── Prepare(n=5) ────────────────────►│    │
   │── Prepare(n=5) ─────────────────────────►│
   │                                │    │    │
   │◄── Promise(n=5, prev=nil) ─────│    │    │
   │◄── Promise(n=5, prev=nil) ──────────│    │
   │◄── Promise(n=5, prev=nil) ───────────────│
   │                                │    │    │
   │   Got majority → proceed to Phase 2     │

Phase 2: ACCEPT
══════════════════════════════════════════════════

   │── Accept(n=5, v="X") ────────►│    │    │
   │── Accept(n=5, v="X") ─────────────►│    │
   │── Accept(n=5, v="X") ──────────────────►│
   │                                │    │    │
   │◄── Accepted(n=5) ─────────────│    │    │
   │◄── Accepted(n=5) ──────────────────│    │
   │◄── Accepted(n=5) ───────────────────────│
   │                                │    │    │
   │   Got majority → value "X" is CHOSEN    │
```

**Prepare(n):** "I want to propose with ID n. Will you promise to ignore any
future proposal with ID < n? If you already accepted something, tell me."

**Promise(n, prev_accepted):** "I promise to ignore proposals with ID < n. Here
is the last value I accepted (if any)."

**Accept(n, v):** "Accept value v with proposal ID n."
- If an acceptor promised n and hasn't promised a higher number, it accepts.
- If any acceptor reported a previously accepted value in Phase 1, the proposer
  MUST use that value (the highest-numbered previously accepted value).

**Accepted(n):** Acknowledgment that the acceptor has accepted.

### 2.3 Safety Proof Intuition

Why does Paxos never choose two different values?

1. A value is chosen only when a majority of acceptors accept it.
2. Any two majorities overlap in at least one acceptor.
3. The overlapping acceptor has already accepted value V.
4. Any future proposer's Phase 1 will hear about V from this acceptor.
5. The future proposer is then forced to propose V (not a different value).

### 2.4 Liveness Issues

Paxos can enter a **livelock** (dueling proposers):

```
Proposer A: Prepare(1) → succeeds
Proposer B: Prepare(2) → succeeds (A's Accept(1) now rejected by acceptors)
Proposer A: Prepare(3) → succeeds (B's Accept(2) now rejected)
... infinite loop, no value ever chosen
```

**Solution:** Elect a distinguished proposer (leader) who is the only one allowed
to propose. This is Multi-Paxos.

### 2.5 Multi-Paxos

Optimization for agreeing on a sequence of values (a replicated log):

1. Run Phase 1 **once** when a leader is elected.
2. For each subsequent log entry, run only Phase 2 (Accept).
3. Leader maintains lease; other nodes do not propose.
4. If the leader fails, a new Phase 1 elects a new leader.

**Performance:** In steady state, agreeing on a value requires one round trip
(leader → acceptors → leader) instead of two.

```
Steady-state Multi-Paxos:

Client ──► Leader ──► Acceptors
                  ◄── Accepted
           Leader ──► Client (response)

           1 RTT per entry
```

### 2.6 EPaxos (Egalitarian Paxos)

Moraru, Andersen, Kaminsky (2013). Removes the single-leader bottleneck:

- **No designated leader.** Any node can propose.
- Uses **dependency tracking** to order commands that conflict (access the same key).
- Non-conflicting commands are committed with 1 RTT in the fast path.
- Conflicting commands require an additional coordination round.

**Trade-offs:**
- Better throughput than Multi-Paxos when commands are non-conflicting.
- Significantly more complex implementation.
- Used in research and some internal systems; less common in production.

---

## 3. Raft (The Standard)

Ongaro and Ousterhout (2014). Designed explicitly for understandability. Equivalent
safety guarantees to Multi-Paxos but decomposed into independent subproblems.

### 3.1 Core Concepts

```
┌──────────────────────────────────────────────────────────────┐
│                        Raft Cluster                          │
│                                                              │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐             │
│  │  Node 1 │      │  Node 2 │      │  Node 3 │             │
│  │ LEADER  │◄────►│FOLLOWER │◄────►│FOLLOWER │             │
│  │         │      │         │      │         │             │
│  │ Term: 5 │      │ Term: 5 │      │ Term: 5 │             │
│  │ Log:    │      │ Log:    │      │ Log:    │             │
│  │ [1,2,3] │      │ [1,2,3] │      │ [1,2]  │             │
│  └─────────┘      └─────────┘      └─────────┘             │
│                                                              │
│  ┌─────────┐      ┌─────────┐                               │
│  │  Node 4 │      │  Node 5 │                               │
│  │FOLLOWER │      │FOLLOWER │                               │
│  │ Term: 5 │      │ Term: 5 │                               │
│  │ [1,2,3] │      │ [1,2,3] │                               │
│  └─────────┘      └─────────┘                               │
└──────────────────────────────────────────────────────────────┘
```

**States:** Every node is in one of three states:
- **Leader:** Handles all client requests, replicates log entries
- **Follower:** Passively responds to RPCs from leader and candidates
- **Candidate:** Attempting to become leader

**Term:** A logical clock that increases monotonically. Each term has at most one
leader. If a node receives a message with a higher term, it updates its term and
becomes a follower.

### 3.2 Leader Election

```
Election Timeline:
═══════════════════════════════════════════════════════

   Term 4              Term 5              Term 6
   ┌─────────────┐     ┌──────────────┐    ┌──────
   │ Leader: N1  │     │ Leader: N3   │    │ ...
   │             │     │              │    │
   └─────────────┘     └──────────────┘    └──────
                 │     │
         N1 crashes    N3 elected
                       (election timeout)
```

**Election procedure:**

1. Follower's **election timer** expires (randomized 150-300ms).
2. Follower becomes **Candidate**, increments term, votes for itself.
3. Candidate sends `RequestVote` RPCs to all other nodes:
   ```
   RequestVote:
     term:          candidate's current term
     candidateId:   candidate's ID
     lastLogIndex:  index of candidate's last log entry
     lastLogTerm:   term of candidate's last log entry
   ```
4. Other nodes grant vote if:
   - They haven't voted for anyone else in this term.
   - Candidate's log is **at least as up-to-date** as their own.
5. Candidate wins if it receives votes from a majority.
6. Winner sends `AppendEntries` heartbeats to establish authority.

**"At least as up-to-date" log comparison:**

```python
def is_up_to_date(candidate_last_term, candidate_last_index,
                  my_last_term, my_last_index):
    if candidate_last_term != my_last_term:
        return candidate_last_term > my_last_term
    return candidate_last_index >= my_last_index
```

This ensures that a node missing committed entries can **never** become leader.

### 3.3 Split Vote

If two candidates start elections simultaneously with the same term:

```
N1 (Candidate, Term 6): votes from N1, N3      → 2 votes (need 3)
N2 (Candidate, Term 6): votes from N2, N4      → 2 votes (need 3)
N5: hasn't voted yet, grants to whichever request arrives first

If N5's vote goes to N1 → N1 wins
If both requests arrive simultaneously → N5 picks one
If N5 is partitioned → neither wins → timeout → new election with Term 7
```

**Randomized timeouts** prevent repeated split votes. Each node picks a random
election timeout, so one will almost always time out first.

### 3.4 Log Replication

```
Client Request Flow:
════════════════════════════════════════════════════════════

Client ──► Leader
             │
             ├── 1. Append entry to local log (uncommitted)
             │
             ├── 2. Send AppendEntries to all followers
             │      │
             │      ├──► Follower 1: appends, replies success
             │      ├──► Follower 2: appends, replies success
             │      ├──► Follower 3: (slow, no reply yet)
             │      └──► Follower 4: appends, replies success
             │
             ├── 3. Majority replied (3 of 4 followers + leader = 4/5)
             │      → Mark entry as COMMITTED
             │
             ├── 4. Apply entry to state machine
             │
             └── 5. Reply to client

             6. Next AppendEntries informs followers of new commit index
                → Followers apply committed entries to their state machines
```

**AppendEntries RPC:**

```
AppendEntries:
  term:              leader's current term
  leaderId:          leader's ID
  prevLogIndex:      index of log entry immediately preceding new ones
  prevLogTerm:       term of entry at prevLogIndex
  entries[]:         log entries to append (empty for heartbeat)
  leaderCommit:      leader's commitIndex
```

**Log Matching Property:**

If two entries in different logs have the same index and term, then:
1. They store the same command.
2. All preceding entries are identical.

This is enforced by the `prevLogIndex` / `prevLogTerm` consistency check. If a
follower's log does not match at `prevLogIndex`, it rejects the AppendEntries.
The leader then decrements `nextIndex` for that follower and retries.

### 3.5 Safety Guarantees

```
┌────────────────────────────────────────────────────────────────┐
│  Raft Safety Properties                                        │
├────────────────────────────────────────────────────────────────┤
│  Election Safety:    At most one leader per term                │
│  Leader Append-Only: Leader never overwrites/deletes entries    │
│  Log Matching:       Same index+term → identical prefix         │
│  Leader Completeness:If entry committed in term T, present in   │
│                      all leaders of terms > T                   │
│  State Machine Safety: If server applies entry at index i,      │
│                        no other server applies different entry   │
│                        at index i                               │
└────────────────────────────────────────────────────────────────┘
```

**Leader Completeness** is the most critical property. It is guaranteed by the
election restriction: a candidate must have all committed entries to win an
election (because it needs votes from a majority, and any majority overlaps with
the majority that committed the entry).

### 3.6 Log Compaction (Snapshotting)

The log grows indefinitely without compaction. Raft uses snapshots:

```
Log without compaction:
  [1] [2] [3] [4] [5] [6] [7] [8] [9] [10] [11] [12] ...
                                                    ↑ applied

Log after snapshot at index 8:
  Snapshot(state at index 8, term 3)  [9] [10] [11] [12] ...
  ├── Contains full state machine state
  └── last_included_index=8, last_included_term=3
```

**InstallSnapshot RPC:** If a follower is so far behind that the leader no longer
has the necessary log entries (they were compacted), the leader sends the entire
snapshot. The follower discards its log and applies the snapshot.

### 3.7 Cluster Membership Changes

Adding or removing nodes from the cluster safely:

**Problem:** Switching from a 3-node to a 5-node cluster creates a moment where
both the old (2-of-3) and new (3-of-5) quorums could independently elect leaders.

**Raft's solution: Joint Consensus (two-phase approach):**

1. Leader proposes `C_old,new` configuration (joint consensus).
   - Decisions require majorities from **both** old and new configurations.
2. Once `C_old,new` is committed, leader proposes `C_new`.
3. Once `C_new` is committed, old nodes not in `C_new` can be shut down.

**Single-server change (simpler alternative, used by etcd):**

Add or remove one node at a time. Because |old| and |new| differ by at most 1,
any majority of old and any majority of new always overlap. This eliminates the
need for joint consensus.

### 3.8 Production Implementations

| Implementation | Language | Used by |
|---|---|---|
| etcd/raft | Go | Kubernetes, etcd, CockroachDB, TiKV |
| hashicorp/raft | Go | Consul, Nomad, Vault |
| openraft | Rust | Databend, various |
| Apache Ratis | Java | Apache Ozone |
| dragonboat | Go | Various |

**etcd/raft design philosophy:**
- Minimal: only implements the core algorithm.
- No network layer: caller provides transport.
- No storage layer: caller provides WAL + snapshot storage.
- Deterministic: all randomness is externalized.
- This makes it highly testable and embeddable.

---

## 4. Viewstamped Replication (VR)

Oki and Liskov (1988), revisited by Liskov and Cowling (2012). Historically
predates Paxos in publication but was less widely studied.

### 4.1 Core Mechanism

VR is a replicated state machine protocol with strong similarities to Raft:

```
┌─────────────────────────────────────────────────────────┐
│  Viewstamped Replication Concepts                        │
│                                                          │
│  View Number      ≈  Raft's Term                         │
│  Primary           ≈  Raft's Leader                      │
│  Backup            ≈  Raft's Follower                    │
│  View Change       ≈  Raft's Leader Election             │
│  Op Number         ≈  Raft's Log Index                   │
│  Commit Number     ≈  Raft's Commit Index                │
└─────────────────────────────────────────────────────────┘
```

**Normal operation (view v, primary p):**

1. Client sends `REQUEST(op, client-id, request-number)` to primary.
2. Primary assigns op-number, adds to log.
3. Primary sends `PREPARE(v, op, op-number, commit-number)` to all backups.
4. Backups append to log, reply `PREPAREOK(v, op-number, replica-id)`.
5. Primary waits for f `PREPAREOK` messages (f+1 total including itself).
6. Primary commits, increments commit-number, replies to client.

**View change protocol:**

When a backup suspects the primary has failed:
1. It sends `STARTVIEWCHANGE(v+1, replica-id)` to all replicas.
2. When f+1 replicas agree, one sends `DOVIEWCHANGE` to the new primary
   (determined by `view_number mod num_replicas`).
3. New primary collects `DOVIEWCHANGE` messages from f+1 replicas, picks the
   most up-to-date log, installs it, and starts the new view.

### 4.2 VR vs. Raft

| Feature | VR | Raft |
|---|---|---|
| Leader election | View change protocol | RequestVote |
| Log divergence | New primary's log is canonical | Leader never overwrites its log |
| Membership changes | Epoch mechanism | Joint consensus / single-server |
| Adoption | Academic (few production uses) | Widespread production use |

---

## 5. ZAB (ZooKeeper Atomic Broadcast)

The consensus protocol powering Apache ZooKeeper. Designed for ordered broadcast
rather than single-value consensus.

### 5.1 Architecture

```
┌────────────────────────────────────────────────────────┐
│                ZooKeeper Cluster                        │
│                                                         │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐       │
│  │  Leader   │     │ Follower │     │ Follower │       │
│  │          │◄───►│          │◄───►│          │       │
│  │ Epoch: 3 │     │ Epoch: 3 │     │ Epoch: 3 │       │
│  └──────────┘     └──────────┘     └──────────┘       │
│        │                                                │
│        │ Total order broadcast                          │
│        │ (all writes go through leader)                 │
│        ▼                                                │
│  Write ordering: zxid = (epoch, counter)                │
│  epoch 3, counter 1 < epoch 3, counter 2 < epoch 4, 0  │
└────────────────────────────────────────────────────────┘
```

### 5.2 The zxid

Every transaction is assigned a **zxid** (ZooKeeper transaction ID):
- **Epoch** (high 32 bits): Incremented each time a new leader is elected.
- **Counter** (low 32 bits): Incremented for each transaction within an epoch.

This ensures **total ordering** across leader changes: all transactions from
epoch 3 precede all transactions from epoch 4.

### 5.3 ZAB Phases

```
Phase 0: ELECTION
  └── Elect a prospective leader (using fast leader election: FLE)
      └── Node with highest (lastZxid, serverId) wins

Phase 1: DISCOVERY
  └── Prospective leader contacts followers
  └── Learns the highest epoch seen by any follower
  └── Establishes new epoch = max(epochs) + 1

Phase 2: SYNCHRONIZATION
  └── Leader sends its transaction history to followers
  └── Followers truncate divergent entries
  └── Followers apply missing committed entries
  └── Once a quorum is synchronized → leader is established

Phase 3: BROADCAST (steady state)
  └── Leader assigns zxid to each write
  └── Sends PROPOSAL to all followers
  └── Followers write to disk, send ACK
  └── Leader waits for quorum ACKs → COMMIT
  └── Followers apply COMMIT
```

### 5.4 ZAB vs. Raft

| Feature | ZAB | Raft |
|---|---|---|
| Designed for | Atomic broadcast (ordered delivery) | Replicated state machine |
| Transaction ordering | zxid (epoch + counter) | Term + log index |
| Recovery | SNAP + DIFF + TRUNC | AppendEntries catch-up + InstallSnapshot |
| Leader election | Fast Leader Election (FLE) | RequestVote |
| Read semantics | Leader or follower (with sync) | Leader reads (or read index) |
| Production use | ZooKeeper | etcd, Consul, CockroachDB, TiKV |

---

## 6. CRDTs (Conflict-Free Replicated Data Types)

### 6.1 Motivation

Consensus algorithms require a majority quorum and cannot make progress during
partitions. For some data types, we can achieve **eventual consistency** without
coordination — every replica can accept writes independently and converge to the
same state automatically.

### 6.2 Types of CRDTs

**State-based CRDTs (CvRDTs — Convergent):**
- Replicas periodically exchange full state.
- Merge function must be commutative, associative, and idempotent (a join semilattice).
- High bandwidth (sending full state), but simple.

**Operation-based CRDTs (CmRDTs — Commutative):**
- Replicas broadcast operations.
- Operations must be commutative (order doesn't matter).
- Requires reliable causal broadcast (every op delivered exactly once).
- Low bandwidth, but delivery requirements are complex.

### 6.3 Common CRDT Data Structures

#### G-Counter (Grow-Only Counter)

```
Each node maintains its own counter:

  Node A: {A: 5, B: 0, C: 0}    total = 5
  Node B: {A: 0, B: 3, C: 0}    total = 3
  Node C: {A: 0, B: 0, C: 7}    total = 7

Increment: node increments only its own entry
Merge: element-wise max

After merge at Node A:
  {A: 5, B: 3, C: 7}  total = 15

Properties:
  - Only supports increment (no decrement)
  - Merge is idempotent: merge(x, x) = x
```

#### PN-Counter (Positive-Negative Counter)

Two G-Counters: one for increments, one for decrements.

```
Value = sum(P) - sum(N)

P: {A: 10, B: 5}   →  15
N: {A: 3,  B: 1}   →   4
Value = 15 - 4 = 11
```

#### LWW-Register (Last-Writer-Wins Register)

```
Each write carries a timestamp:
  Node A writes "Alice" at t=100
  Node B writes "Bob" at t=105

Merge: value with highest timestamp wins → "Bob"

Problem: requires synchronized clocks (or Lamport timestamps)
Problem: concurrent writes lose data (one is silently discarded)
```

#### OR-Set (Observed-Remove Set)

```
Each element has a unique tag per add operation:

  Add "x" at Node A:   {(x, tag_a1)}
  Add "x" at Node B:   {(x, tag_b1)}
  Remove "x" at Node A: removes tag_a1 only

After merge:
  {(x, tag_b1)}  → "x" is still in the set

"Add wins over concurrent remove" semantics
```

#### LWW-Element-Set

Used by Redis (CRDT) and Riak:

```
Each element has an add-timestamp and a remove-timestamp.
Element is in the set if add-ts > remove-ts.

Add "x" at t=10:    adds[(x, 10)]
Remove "x" at t=15: removes[(x, 15)]
Re-add "x" at t=20: adds[(x, 20)]

State: "x" is present (20 > 15)
```

### 6.4 CRDTs in Practice

| System | CRDTs used |
|---|---|
| Riak | Counters, sets, maps, registers, flags |
| Redis Enterprise (CRDB) | Counters, sets, strings, lists (active-active) |
| Automerge | JSON-like CRDT for collaborative editing |
| Yjs | Text CRDT for collaborative editors |
| Apple (Notes, Reminders) | Custom CRDTs for sync across devices |

### 6.5 Limitations

- Not all data structures have natural CRDT representations.
- Metadata overhead can be large (OR-Set stores tombstones of all removes).
- Garbage collection of metadata requires consensus (ironic).
- Semantic conflicts (two users edit the same paragraph) are resolved
  syntactically, not semantically — the result may be nonsensical.

---

## 7. Gossip Protocols

### 7.1 Concept

Gossip (epidemic) protocols spread information through a cluster the way rumors
spread in a population: each node periodically picks a random peer and exchanges
state.

```
Gossip Round:

t=0:  Node A has info X
      A randomly picks B → sends X to B

t=1:  Nodes A, B have X
      A picks D → sends X to D
      B picks C → sends X to C

t=2:  All nodes have X
      Convergence in O(log N) rounds
```

### 7.2 Gossip Variants

**Anti-Entropy (state reconciliation):**
- Nodes periodically exchange full or partial state digests.
- Compare digests, exchange missing/outdated entries.
- Guaranteed convergence but higher bandwidth.

**Rumor Mongering (dissemination):**
- New information is "hot" — nodes eagerly spread it.
- After enough rounds, the rumor "cools" and spreading stops.
- Lower bandwidth but small probability of missing a node.

### 7.3 Applications

- **Cassandra:** Gossip for cluster membership, failure detection, schema changes.
  Uses a `generation` counter + heartbeat counter. Each node gossips every second.
- **Consul:** Serf-based gossip for service discovery and health checking.
- **Redis Cluster:** Gossip bus for node health and slot assignment.
- **Amazon S3:** Anti-entropy for replica synchronization.

### 7.4 Failure Detection via Gossip

Each node maintains a heartbeat counter. If a peer's heartbeat has not increased
within a threshold, it is suspected. The **phi accrual failure detector** (used by
Cassandra and Akka) computes a suspicion level:

```
φ = -log₁₀(P(heartbeat_late > actual_delay))

φ < 1:    probably alive
φ ≥ 8:    very likely dead (P ≈ 10⁻⁸)
φ ≥ 12:   almost certainly dead

Threshold is configurable (Cassandra default: φ = 8)
```

This adapts to actual network conditions — a node on a slow link gets a longer
leash before being declared dead.

---

## 8. Membership Protocols: SWIM

### 8.1 The Problem

In a cluster of N nodes, direct heartbeating (every node pings every other node)
generates O(N²) messages per interval. This does not scale beyond a few hundred
nodes.

### 8.2 SWIM (Scalable Weakly-consistent Infection-style Membership)

Das, Gupta, Muthukrishnan (2002). O(N) message load per interval.

**Protocol:**

```
Every T seconds, Node A:

1. PING a random node B
   ├── B replies ACK → B is alive ✓
   │
   └── B does not reply within timeout
       │
       ├── 2. PING-REQ: Ask k random nodes to ping B on A's behalf
       │      ├── Any of them gets ACK → B is alive ✓
       │      └── None get ACK → B is SUSPECTED
       │
       └── 3. After suspicion timeout → B is declared DEAD
              └── Disseminate "B is dead" via gossip (piggyback)
```

**Properties:**

| Property | Value |
|---|---|
| Message complexity | O(N) per protocol period |
| Detection time | O(log N) protocol periods |
| False positive rate | Tunable via k (number of indirect probes) |
| Dissemination | Piggyback on protocol messages (O(N log N)) |

### 8.3 SWIM Extensions (Lifeguard)

Hashicorp's Serf/Memberlist implements SWIM with Lifeguard enhancements:

- **Suspicion with refutation:** A suspected node can broadcast an "alive"
  message to cancel the suspicion.
- **Dynamic suspicion timeout:** Scales with cluster size.
- **Composite protocol periods:** Combine direct probe, indirect probe, and
  dissemination into one round.

### 8.4 Comparison

| Protocol | Messages/interval | Detection time | Use case |
|---|---|---|---|
| All-to-all heartbeat | O(N²) | O(1) | Small clusters (<20) |
| SWIM | O(N) | O(log N) | Medium clusters |
| SWIM + Lifeguard | O(N) | O(log N), adaptive | Large clusters (1000+) |
| Gossip-based | O(N) | O(log N) | Information dissemination |

---

## 9. Causal Consistency

### 9.1 Definition

Causal consistency ensures that operations that are **causally related** are seen
in the same order by all nodes. Concurrent (causally unrelated) operations may be
seen in different orders by different nodes.

```
Causal relationship:

  Thread 1: write(x, 1)  ──────────────►  read(x) = 1
                          happens-before

  If T2 reads x=1 and then writes y=2:
    write(x,1) → read(x)=1 → write(y,2)
    These are causally related: any node that sees y=2 must also see x=1

  Concurrent (no causal relation):
    T1: write(x, 1)
    T3: write(z, 3)    (T3 never read x, never communicated with T1)
    Different nodes may see x=1 before z=3 or z=3 before x=1
```

### 9.2 Mechanisms for Tracking Causality

#### Vector Clocks

Each node maintains a vector of counters, one per node:

```
Nodes: A, B, C

Node A writes x=1:   VC_A = [1, 0, 0]
Node B reads x=1:    VC_B = [1, 1, 0]  (merged A's clock, incremented own)
Node B writes y=2:   VC_B = [1, 2, 0]
Node C writes z=3:   VC_C = [0, 0, 1]

Comparison:
  [1, 2, 0] > [1, 0, 0]  → causally after  (y=2 happened after x=1)
  [1, 2, 0] || [0, 0, 1] → concurrent      (y=2 and z=3 are independent)
```

**Problem:** Vector size grows with the number of nodes. For systems with
thousands of clients, this is impractical.

#### Lamport Timestamps

Single integer counter. Every message carries the sender's timestamp. Receiver
updates: `local = max(local, received) + 1`.

- Guarantees: if A → B (happens before), then timestamp(A) < timestamp(B).
- Does NOT guarantee the converse: timestamp(A) < timestamp(B) does not mean A → B.
- Useful for total ordering (break ties with node ID) but does not capture concurrency.

#### Hybrid Logical Clocks (HLC)

Kulkarni et al. (2014). Combine physical time with logical time:

```
HLC = (physical_time, logical_counter, node_id)

- physical_time: max of local wall clock and received HLC physical time
- logical_counter: incremented when physical_time does not advance
- Bounded drift: HLC is always within ε of physical time

Used by: CockroachDB, MongoDB (causal sessions)
```

HLC provides causal ordering with constant-size metadata (no vector growth)
and close-to-real-time timestamps useful for TTL, GC, and human readability.

### 9.3 Causal Consistency in Practice

| System | Mechanism | Notes |
|---|---|---|
| MongoDB | Causal sessions + HLC | Client tracks operation time; reads wait for causal deps |
| CockroachDB | HLC + transaction ordering | Serializable by default; HLC used for clock skew management |
| Riak | Vector clocks (now dotted version vectors) | Client resolves siblings |
| DynamoDB | Not causally consistent | Eventual consistency; strong consistency on read |

### 9.4 Session Guarantees

Weaker than full causal consistency but practically useful:

| Guarantee | Meaning |
|---|---|
| Read Your Writes | After a write, subsequent reads see that write |
| Monotonic Reads | If you read v2, you never subsequently read v1 |
| Monotonic Writes | Writes from a session are applied in session order |
| Writes Follow Reads | A write that follows a read is ordered after the read's causal deps |

---

## 10. Replication Models

### 10.1 Synchronous vs. Asynchronous

```
Synchronous Replication:
═══════════════════════════════

Client ──► Primary ──► Replica 1 (waits for ACK)
                   ──► Replica 2 (waits for ACK)
                   ◄── ACKs received
           Primary ──► Client: "committed"

  Latency = max(replica_latency)
  Data loss on primary crash: ZERO
  Problem: one slow replica blocks everything

Asynchronous Replication:
═══════════════════════════════

Client ──► Primary ──► Client: "committed"  (immediately)
                   ──► Replica 1 (background)
                   ──► Replica 2 (background)

  Latency = primary write time only
  Data loss on primary crash: recent uncommitted writes
  Used by: PostgreSQL async streaming replication
```

### 10.2 Semi-Synchronous

**MySQL semi-sync replication:**
- Primary waits for **at least one** replica to acknowledge the write.
- If the acknowledging replica also crashes, data may be lost.
- Trade-off between full sync (all replicas) and async (none).

**PostgreSQL synchronous replication:**

```
# postgresql.conf on primary:
synchronous_standby_names = 'FIRST 1 (standby1, standby2)'

# "FIRST 1": wait for ACK from the first standby that responds
# "ANY 2": wait for ACK from any 2 of the listed standbys
```

### 10.3 Leaderless Replication

No designated leader. Any node can accept writes.

```
Client Write:
  Send write to N=3 replicas
  Wait for W=2 ACKs (write quorum)
  Success when W achieved

Client Read:
  Send read to N=3 replicas
  Wait for R=2 responses (read quorum)
  Return value with highest version/timestamp

Consistency guarantee when R + W > N:
  Read and write quorums overlap by at least one node
  That node has the latest write
```

**Sloppy quorum (DynamoDB):**

During a partition, writes may go to nodes that are not the usual replicas for
that key (hinted handoff nodes). This maintains availability but temporarily
violates the R + W > N guarantee.

**Read repair:**

When a read returns stale data from one node:

```
Client reads from A, B, C:
  A: version 5 (current)
  B: version 5 (current)
  C: version 3 (stale)

Client uses version 5 as the result.
Background: client sends version 5 to C → C updates.
```

**Anti-entropy:**

Background process (Merkle tree comparison) detects and repairs inconsistencies:

```
                    Root Hash
                   /         \
             Hash(L)       Hash(R)
            /      \      /      \
        H(LL)  H(LR)  H(RL)  H(RR)
        /  \   /  \    /  \   /  \
      d1  d2 d3  d4  d5  d6 d7  d8

Node A and Node B compare root hashes.
If different → descend tree to find divergent leaves.
Exchange only the divergent data ranges.
```

---

## 11. Linearizability and Sequential Consistency

### 11.1 Linearizability

The strongest single-object consistency model. Every operation appears to take
effect at a single atomic point between its invocation and response.

```
Real time: ───────────────────────────────────────────►

Client A: ──[write x=1]──          (completes at t=5)
Client B:        ──[read x]── → must return 1 (started after A's write completed)
Client C:   ──[read x]────── → may return 0 or 1 (overlaps with A's write)
```

**Where linearizability is required:**
- Leader election (if two nodes both think they are leader, data corruption)
- Distributed locks (if a lock is not linearizable, mutual exclusion fails)
- Unique constraints (if uniqueness check is not linearizable, duplicates)

### 11.2 Sequential Consistency

Weaker than linearizability. All operations appear in some sequential order
consistent with each client's program order, but this order need not respect
real-time ordering.

```
Linearizable:    real-time order respected
Sequential:      some total order exists consistent with program order
Causal:          only causally related ops are ordered
Eventual:        all replicas converge "eventually"

Stronger ──────────────────────────────────── Weaker
Linearizable > Sequential > Causal > Eventual
```

---

## 12. Distributed Transactions

### 12.1 Two-Phase Commit (2PC)

The classic protocol for atomic cross-node transactions:

```
Phase 1: PREPARE
══════════════════════════════════════════

Coordinator              Participants
    │                    P1    P2    P3
    │── Prepare ────────►│     │     │
    │── Prepare ─────────────►│     │
    │── Prepare ──────────────────►│
    │                    │     │     │
    │◄── Vote YES ───────│     │     │
    │◄── Vote YES ────────────│     │
    │◄── Vote YES ─────────────────│
    │                    │     │     │
    │   All YES → proceed to Phase 2    │

Phase 2: COMMIT
══════════════════════════════════════════

    │── Commit ─────────►│     │     │
    │── Commit ──────────────►│     │
    │── Commit ───────────────────►│
    │                    │     │     │
    │◄── ACK ────────────│     │     │
    │◄── ACK ─────────────────│     │
    │◄── ACK ──────────────────────│
```

**Blocking problem:** If the coordinator crashes after sending Prepare but before
sending Commit/Abort, participants are stuck holding locks indefinitely (they voted
YES and cannot unilaterally abort or commit).

### 12.2 Three-Phase Commit (3PC)

Adds a **Pre-Commit** phase between Prepare and Commit. Allows participants to
recover without blocking if the coordinator crashes. However, 3PC does not handle
network partitions correctly and is rarely used in practice.

### 12.3 Saga Pattern

For long-running distributed transactions where holding locks is impractical:

```
Forward execution:
  T1 (book hotel) → T2 (book flight) → T3 (charge card)

If T3 fails, execute compensating transactions:
  C2 (cancel flight) → C1 (cancel hotel)

Saga guarantees:
  Either all Ti complete, or
  Executed Ti are compensated by Ci in reverse order
```

**Orchestration vs. Choreography:**

| Approach | How | Trade-off |
|---|---|---|
| Orchestration | Central coordinator drives steps | Easier to understand; single point of failure |
| Choreography | Each service emits events, next service reacts | Decoupled; harder to debug/trace |

---

## 13. Consistency Models Summary

```
┌────────────────────────────────────────────────────────────────┐
│                    Consistency Spectrum                         │
│                                                                │
│  Strongest ◄──────────────────────────────────► Weakest        │
│                                                                │
│  Strict          All ops in real-time order     Impossible in  │
│  Consistency     (requires instantaneous         distributed   │
│                   communication)                 systems       │
│                                                                │
│  Linearizable    Single atomic point in          etcd, Spanner │
│                  real time per op                                │
│                                                                │
│  Sequential      Total order consistent          ZooKeeper     │
│                  with program order                             │
│                                                                │
│  Causal          Causally related ops            MongoDB        │
│                  ordered; concurrent unordered   (sessions)     │
│                                                                │
│  PRAM /          Per-client order preserved      Some caches   │
│  FIFO                                                          │
│                                                                │
│  Eventual        All replicas converge           Cassandra,    │
│                  "eventually"                    DynamoDB       │
│                                                                │
│  Weak            No ordering guarantees          DNS caches    │
└────────────────────────────────────────────────────────────────┘
```

---

## 14. Production Considerations

### 14.1 Network Partitions in Practice

Partitions happen more often than most engineers expect (Bailis and Kingsbury,
"The Network Is Reliable" survey). Common causes:

- Switch/router failures
- Asymmetric network issues (A can reach B, B cannot reach A)
- GC pauses long enough to trigger failure detection
- NIC firmware bugs
- Misconfigured firewalls after maintenance

### 14.2 Clock Skew

Consensus algorithms that rely on time (leader leases, HLC) must account for
clock skew:

- NTP accuracy: typically 1-10ms within a data center.
- Google TrueTime (Spanner): GPS + atomic clocks, uncertainty bounded to ~7ms.
- CockroachDB: assumes max clock offset of 500ms (configurable), aborts
  transactions if observed offset exceeds limit.

### 14.3 Byzantine Fault Tolerance

All algorithms discussed above assume crash-stop failures (a node either works
correctly or stops). Byzantine failures (a node sends arbitrary, possibly malicious
messages) require different algorithms:

| Algorithm | Fault model | Tolerance | Use case |
|---|---|---|---|
| Paxos/Raft | Crash-stop | f < N/2 | Databases, coordination services |
| PBFT | Byzantine | f < N/3 | Permissioned blockchains |
| HotStuff | Byzantine | f < N/3 | Diem/Libra (now Aptos) |
| Tendermint | Byzantine | f < N/3 | Cosmos ecosystem |

Byzantine tolerance requires 3f+1 nodes to tolerate f faults (vs. 2f+1 for
crash-stop). The message complexity is also higher (O(N²) for PBFT vs. O(N) for
Raft).

### 14.4 Observability

Monitor these metrics in a consensus cluster:

| Metric | Healthy | Warning |
|---|---|---|
| Leader changes per hour | < 1 | > 5 |
| Proposal latency (p99) | < 50ms | > 200ms |
| Raft log behind (follower) | < 100 entries | > 1000 entries |
| Snapshot frequency | Per configured schedule | Unexpected snapshots |
| WAL disk fsync latency | < 5ms | > 20ms |
| Network RTT between nodes | < 2ms (same DC) | > 10ms |

---

## References

- **Paxos Made Simple** — Lamport, 2001. The clearest Paxos explanation.
- **In Search of an Understandable Consensus Algorithm (Raft)** — Ongaro and
  Ousterhout, 2014. ATC Best Paper.
- **Viewstamped Replication Revisited** — Liskov and Cowling, 2012.
- **ZooKeeper: Wait-free coordination for Internet-scale systems** — Hunt et al., 2010.
- **A comprehensive study of CRDTs** — Shapiro et al., INRIA TR 7506, 2011.
- **SWIM: Scalable Weakly-consistent Infection-style Process Group Membership** —
  Das et al., 2002.
- **Designing Data-Intensive Applications** — Kleppmann, 2017. Chapters 5, 8, 9.
- **FLP Impossibility** — Fischer, Lynch, Paterson, 1985.
- **Logical Physical Clocks and Consistent Snapshots (HLC)** — Kulkarni et al., 2014.
