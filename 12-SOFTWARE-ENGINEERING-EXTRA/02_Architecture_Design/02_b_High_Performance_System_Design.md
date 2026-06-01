---
corso: "SWE Masterclass"
fase: "2 — Architecture & Design"
modulo: "2.2b"
titolo: "High-Performance System Design"
versione: "2026-05-29"
livello: "Advanced"
prerequisiti:
  - "Working knowledge of CPU architecture (caches, pipelines, memory hierarchy)"
  - "Proficiency in at least one systems language (C, C++, Java, Rust, or Go)"
obiettivi:
  - "Diagnose false sharing and cache-line contention using profiling tools"
  - "Implement a lock-free queue using compare-and-swap (CAS) operations"
  - "Apply the LMAX Disruptor single-writer principle to a high-throughput pipeline"
  - "Profile and benchmark a hot-path workload with perf, async-profiler, or equivalent"
  - "Quantify the theoretical speedup limit of a parallel workload using Amdahl's Law and the Universal Scalability Law"
tag: [performance, mechanical-sympathy, lock-free, disruptor, NUMA, cache, profiling, benchmarking]
---

# Module 2.2b: High-Performance System Design

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Diagnose false sharing and cache-line contention using profiling tools
> - Implement a lock-free queue using compare-and-swap (CAS) operations
> - Apply the LMAX Disruptor single-writer principle to a high-throughput pipeline
> - Profile and benchmark a hot-path workload with perf, async-profiler, or equivalent
> - Quantify the theoretical speedup limit of a parallel workload using Amdahl's Law and the Universal Scalability Law

> **Module 02.2.b** · **Last updated:** 2026-05-22

## Guiding ideas
1. **Mechanical sympathy: code tuned to hardware.** Cache lines, branch prediction.
2. **Lock-free / wait-free for high-throughput hot paths.**
3. **Disruptor pattern (LMAX): single-writer principle.**
4. **NUMA awareness for multi-socket servers.**
5. **Measure first, optimize second. Profilers do not lie.**

---

## Table of Contents

1. Mechanical Sympathy
2. CPU Cache Hierarchy & Cache Lines
3. False Sharing
4. Branch Prediction & Speculative Execution
5. NUMA — Non-Uniform Memory Access
6. Lock-Free & Wait-Free Data Structures
7. The LMAX Disruptor
8. Connection Pooling
9. Async I/O & Event Loops
10. Zero-Copy Techniques
11. Cache Hierarchies — L1/L2/L3 to Redis
12. Hot Path Optimization
13. Memory Allocation & Pooling
14. Profiling & Benchmarking
15. Common Pitfalls & Troubleshooting
16. Q&A — Frequently Asked Questions
17. Hands-On Exercises
18. References

---

## 1. Mechanical Sympathy

Martin Thompson coined the term for software engineering: write code that works *with* the hardware, not against it. Understanding CPU caches, memory hierarchies, branch prediction, and I/O models lets you write code that is orders of magnitude faster — without changing algorithms.

### 1.1 The Memory Hierarchy

```
┌─────────────────┐  ~1 cycle     ~1 ns
│   CPU Register  │
├─────────────────┤
│   L1 Cache      │  ~4 cycles    ~1-2 ns       32-64 KB per core
├─────────────────┤
│   L2 Cache      │  ~12 cycles   ~3-5 ns       256 KB - 1 MB per core
├─────────────────┤
│   L3 Cache      │  ~40 cycles   ~10-20 ns     8-64 MB shared
├─────────────────┤
│   Main Memory   │  ~200 cycles  ~50-100 ns    16-512 GB
├─────────────────┤
│   NVMe SSD      │  ~10K cycles  ~10-25 μs     TB scale
├─────────────────┤
│   Network (LAN) │  ~500K cycles ~100-500 μs
├─────────────────┤
│   Spinning Disk │  ~10M cycles  ~5-10 ms
├─────────────────┤
│   Network (WAN) │  ~100M cycles ~50-150 ms
└─────────────────┘
```

**Key insight:** The gap between L1 cache and main memory is ~100x. The gap between main memory and disk is ~100,000x. Data locality dominates performance.

### 1.2 Latency Numbers Every Engineer Should Know

| Operation | Latency | Relative to 1s human time |
|---|---|---|
| L1 cache reference | 1 ns | 1 second |
| L2 cache reference | 4 ns | 4 seconds |
| L3 cache reference | 15 ns | 15 seconds |
| Main memory reference | 100 ns | 1.7 minutes |
| SSD random read | 16 μs | 4.4 hours |
| HDD seek | 4 ms | 46 days |
| SF → NYC round trip | 40 ms | 1.3 years |
| SF → London round trip | 80 ms | 2.5 years |

---

## 2. CPU Cache Hierarchy & Cache Lines

### 2.1 Cache Line Basics

CPUs do not load individual bytes from memory. They load **cache lines** — typically 64 bytes on x86/ARM.

```
Memory address: 0x1000

CPU loads cache line: [0x1000 ... 0x103F]  (64 bytes)

If you access byte 0x1000, bytes 0x1001-0x103F
are "free" — already in cache.
```

### 2.2 Sequential vs Random Access

```
Sequential access (array scan):
  ┌──┬──┬──┬──┬──┬──┬──┬──┐
  │a0│a1│a2│a3│a4│a5│a6│a7│  ← one cache line
  └──┴──┴──┴──┴──┴──┴──┴──┘
  Access a0 → cache miss, loads line
  Access a1..a7 → cache hits (7 free accesses)
  Hit rate: 87.5%

Random access (linked list traversal):
  Node at 0x1000 → next at 0x8400 → next at 0x3200
  Each node is on a different cache line.
  Every access is a cache miss.
  Hit rate: ~0%
```

**Practical rule:** Arrays > linked lists for cache performance. Even when the algorithm favors a linked list, an array-based alternative (e.g., array-backed queue) often wins due to cache locality.

### 2.3 Data-Oriented Design

Arrange data for how it is *accessed*, not how it is *conceptually structured*.

**Array of Structs (AoS) — poor cache use when accessing one field:**

```c
// AoS: each particle is one struct
struct Particle {
    float x, y, z;      // position (12 bytes)
    float vx, vy, vz;   // velocity (12 bytes)
    float mass;          // 4 bytes
    int type;            // 4 bytes
};                       // Total: 32 bytes per particle

Particle particles[1000];

// Update positions: touches x, y, z, vx, vy, vz per particle
// But also loads mass, type into cache (wasted)
for (int i = 0; i < 1000; i++) {
    particles[i].x += particles[i].vx * dt;
    particles[i].y += particles[i].vy * dt;
    particles[i].z += particles[i].vz * dt;
}
```

**Struct of Arrays (SoA) — optimal cache use when accessing one field:**

```c
// SoA: separate arrays per field
struct Particles {
    float x[1000], y[1000], z[1000];
    float vx[1000], vy[1000], vz[1000];
    float mass[1000];
    int type[1000];
};

Particles p;

// Update positions: sequential access through x[], vx[], etc.
// Each array is contiguous → maximum cache utilization
for (int i = 0; i < 1000; i++) {
    p.x[i] += p.vx[i] * dt;
    p.y[i] += p.vy[i] * dt;
    p.z[i] += p.vz[i] * dt;
}
```

SoA enables SIMD (Single Instruction, Multiple Data) vectorization by the compiler, further multiplying throughput.

### 2.4 Cache Prefetching

Modern CPUs detect sequential access patterns and prefetch the next cache lines automatically (hardware prefetcher). You can also issue explicit prefetch hints:

```c
// GCC/Clang intrinsic
for (int i = 0; i < N; i++) {
    __builtin_prefetch(&data[i + 16], 0, 3);  // prefetch 16 elements ahead
    process(data[i]);
}
```

- `0` = read, `1` = write.
- `3` = highest temporal locality (keep in all cache levels).

Use sparingly. Incorrect prefetching pollutes the cache.

---

## 3. False Sharing

### 3.1 The Problem

False sharing occurs when two threads write to *different* variables that happen to reside on the *same cache line*. The CPU's cache coherence protocol (MESI/MOESI) forces the cache line to ping-pong between cores, destroying performance.

```
Core 0 writes var_a at address 0x1000
Core 1 writes var_b at address 0x1004

Both on the same cache line [0x1000 - 0x103F].

Core 0 writes → invalidates Core 1's copy
Core 1 writes → invalidates Core 0's copy
Repeat → "cache line ping-pong"

Result: Appears as if there is lock contention,
        but there is no lock. Pure hardware overhead.
```

### 3.2 Detection

**Symptom:** Multi-threaded code runs *slower* with more cores. Per-thread counters show high L2/L3 cache miss rates.

**Tools:**
- `perf c2c` (Linux): detects cache-line contention.
- Intel VTune: false sharing analysis.
- `perf stat -e cache-misses,cache-references`: overall cache miss rate.

### 3.3 Fix: Cache Line Padding

Ensure each thread's hot data lives on its own cache line.

```java
// WRONG: counters[0] and counters[1] are adjacent → false sharing
long[] counters = new long[NUM_THREADS];  // each long is 8 bytes

// Thread i increments counters[i]
// But counters[0] and counters[1] share a cache line (64 bytes fits 8 longs)
```

```java
// FIX: pad to cache line boundary
@jdk.internal.vm.annotation.Contended  // JDK annotation
class PaddedCounter {
    volatile long value;
}

// Or manually:
class PaddedCounter {
    long p1, p2, p3, p4, p5, p6, p7;  // 56 bytes padding
    volatile long value;                // 8 bytes
    long p8, p9, p10, p11, p12, p13, p14;  // 56 bytes padding
}
```

```c
// C: align to cache line
struct __attribute__((aligned(64))) PerThreadCounter {
    long value;
    char padding[64 - sizeof(long)];
};

struct PerThreadCounter counters[NUM_THREADS];
```

```go
// Go: padding struct
type Counter struct {
    value int64
    _     [56]byte  // pad to 64 bytes
}

var counters [8]Counter
```

### 3.4 Benchmark Impact

Typical false sharing penalty on a 4-core machine:

| Scenario | Throughput |
|---|---|
| No sharing (padded) | 800M ops/sec |
| False sharing (adjacent longs) | 50M ops/sec |
| True sharing (same variable, atomic) | 30M ops/sec |

False sharing is **16x** slower than padded. Worse than actual contention.

---

## 4. Branch Prediction & Speculative Execution

### 4.1 The Branch Predictor

Modern CPUs pipeline instructions 15-20 stages deep. A branch (if/else, loop condition) creates a fork — the CPU must decide which path to execute *before* the condition is evaluated.

The **branch predictor** guesses which path to take. If correct, zero penalty. If wrong, the pipeline is flushed — typically a 15-20 cycle penalty.

### 4.2 Predictable vs Unpredictable Branches

```c
// PREDICTABLE: sorted array, branch is TRUE then FALSE (one transition)
int sum = 0;
sort(data, N);
for (int i = 0; i < N; i++) {
    if (data[i] >= 128)  // predictable: FALSE...FALSE...TRUE...TRUE
        sum += data[i];
}

// UNPREDICTABLE: random array, branch flips randomly
int sum = 0;
// data is unsorted random
for (int i = 0; i < N; i++) {
    if (data[i] >= 128)  // unpredictable: TRUE, FALSE, TRUE, TRUE, FALSE...
        sum += data[i];
}
```

The sorted version can be **5-6x faster** due to branch prediction.

### 4.3 Branch-Free Programming

Replace unpredictable branches with arithmetic:

```c
// With branch (unpredictable)
if (data[i] >= 128)
    sum += data[i];

// Branch-free equivalent
int mask = -(data[i] >= 128);  // 0 or -1 (all bits set)
sum += data[i] & mask;

// Or use CMOV (compiler often does this with -O2)
sum += (data[i] >= 128) ? data[i] : 0;
```

### 4.4 Practical Guidance

1. **Hot loops with data-dependent branches:** consider sorting the data first, or using branch-free techniques.
2. **Switch statements with many cases:** use lookup tables instead.
3. **Polymorphic dispatch (virtual calls):** the CPU also predicts indirect branches. Monomorphic call sites are faster (one concrete type) than megamorphic (many types).
4. **Sorted data is friendly:** binary search, merge operations, and filtered scans all benefit from sorted input.

---

## 5. NUMA — Non-Uniform Memory Access

### 5.1 The Architecture

In multi-socket servers, each CPU socket has its own memory controller and local DRAM. Accessing memory attached to the *local* socket is fast; accessing memory on a *remote* socket is 1.5-3x slower (must traverse the inter-socket interconnect — QPI, UPI, or Infinity Fabric).

```
┌─────────────────────────────────────────────────────┐
│                   Server                            │
│                                                     │
│  ┌──────────────┐         ┌──────────────┐          │
│  │   Socket 0   │◀──UPI──▶│   Socket 1   │          │
│  │  Cores 0-15  │         │  Cores 16-31 │          │
│  └──────┬───────┘         └──────┬───────┘          │
│         │                        │                  │
│  ┌──────▼───────┐         ┌──────▼───────┐          │
│  │   DRAM 0     │         │   DRAM 1     │          │
│  │  (128 GB)    │         │  (128 GB)    │          │
│  │  LOCAL to    │         │  LOCAL to    │          │
│  │  Socket 0    │         │  Socket 1    │          │
│  └──────────────┘         └──────────────┘          │
│                                                     │
│  Core 0 accessing DRAM 0: ~90 ns  (local)           │
│  Core 0 accessing DRAM 1: ~150 ns (remote, +67%)    │
└─────────────────────────────────────────────────────┘
```

### 5.2 NUMA-Aware Programming

**Rule:** Pin threads to the NUMA node whose memory they access.

```bash
# Linux: run process on NUMA node 0 only
numactl --cpunodebind=0 --membind=0 ./my_app

# Check NUMA topology
numactl --hardware
# node 0 cpus: 0 1 2 3 4 5 6 7
# node 1 cpus: 8 9 10 11 12 13 14 15

# Check NUMA stats
numastat -p <pid>
# Look for "other_node" — high values mean remote accesses
```

**JVM:**

```bash
# Pin JVM to NUMA node 0
numactl --cpunodebind=0 --membind=0 java -jar app.jar

# JVM NUMA-aware GC
java -XX:+UseNUMA -jar app.jar
```

**Database servers:** PostgreSQL, MySQL, and Redis benefit significantly from NUMA pinning. A common anti-pattern is "NUMA interleaving" which spreads memory across all nodes — this gives uniform-but-slower access. For databases, pinning is usually better.

### 5.3 NUMA and Containerization

In Kubernetes, use `topology.kubernetes.io/zone` labels and `topologySpreadConstraints` to place pods near their data. For NUMA-sensitive workloads (databases, caches), use the Kubernetes Topology Manager:

```yaml
# kubelet config
topologyManagerPolicy: single-numa-node
```

This ensures that CPU and memory are allocated from the same NUMA node.

---

## 6. Lock-Free & Wait-Free Data Structures

### 6.1 Lock-Based vs Lock-Free vs Wait-Free

| Property | Lock-Based | Lock-Free | Wait-Free |
|---|---|---|---|
| Mutual exclusion | Mutex/spinlock | No locks | No locks |
| Progress guarantee | None (deadlock possible) | System-wide progress (at least one thread makes progress) | Per-thread progress (every thread completes in bounded steps) |
| Performance under contention | Degrades rapidly | Degrades gracefully | Constant |
| Complexity | Simple | High | Very high |

### 6.2 Compare-And-Swap (CAS)

The fundamental primitive for lock-free programming.

```
CAS(memory_location, expected_value, new_value):
    if *memory_location == expected_value:
        *memory_location = new_value
        return true
    else:
        return false
```

This is a single atomic CPU instruction (CMPXCHG on x86, LDXR/STXR on ARM).

### 6.3 Lock-Free Counter

```java
import java.util.concurrent.atomic.AtomicLong;

class LockFreeCounter {
    private final AtomicLong value = new AtomicLong(0);

    public void increment() {
        long current;
        do {
            current = value.get();
        } while (!value.compareAndSet(current, current + 1));
        // Retry loop: if another thread changed the value between
        // get() and compareAndSet(), we retry.
    }

    // Simpler: AtomicLong.incrementAndGet() does this internally.
    public void incrementSimple() {
        value.incrementAndGet();
    }
}
```

### 6.4 Lock-Free Queue (Michael-Scott Queue)

The classic lock-free concurrent queue. Used by `java.util.concurrent.ConcurrentLinkedQueue`.

```
Invariant: head and tail are always valid pointers.

Enqueue:
  1. Create new node
  2. CAS tail.next from null to new node
  3. CAS tail from old tail to new node

Dequeue:
  1. Read head
  2. Read head.next
  3. If head.next is null → queue is empty
  4. CAS head from old head to head.next
  5. Return old head.next.value
```

```java
class LockFreeQueue<T> {
    private final AtomicReference<Node<T>> head;
    private final AtomicReference<Node<T>> tail;

    static class Node<T> {
        final T value;
        final AtomicReference<Node<T>> next = new AtomicReference<>(null);

        Node(T value) { this.value = value; }
    }

    public LockFreeQueue() {
        Node<T> sentinel = new Node<>(null);
        head = new AtomicReference<>(sentinel);
        tail = new AtomicReference<>(sentinel);
    }

    public void enqueue(T value) {
        Node<T> newNode = new Node<>(value);
        while (true) {
            Node<T> curTail = tail.get();
            Node<T> next = curTail.next.get();
            if (curTail == tail.get()) {
                if (next == null) {
                    if (curTail.next.compareAndSet(null, newNode)) {
                        tail.compareAndSet(curTail, newNode);
                        return;
                    }
                } else {
                    tail.compareAndSet(curTail, next);  // help advance tail
                }
            }
        }
    }

    public T dequeue() {
        while (true) {
            Node<T> curHead = head.get();
            Node<T> curTail = tail.get();
            Node<T> next = curHead.next.get();
            if (curHead == head.get()) {
                if (curHead == curTail) {
                    if (next == null) return null;  // empty
                    tail.compareAndSet(curTail, next);
                } else {
                    T value = next.value;
                    if (head.compareAndSet(curHead, next)) {
                        return value;
                    }
                }
            }
        }
    }
}
```

### 6.5 The ABA Problem

```
Thread 1 reads A from location X
Thread 1 is preempted
Thread 2 changes X from A → B → A
Thread 1 resumes, CAS(X, A, C) succeeds — but the value was changed!
```

**Solutions:**
- **Tagged pointers:** pair the value with a version counter. CAS on both.
- **Hazard pointers:** mark nodes as "in use" to prevent premature reclamation.
- **Epoch-based reclamation:** defer memory freeing until all threads pass a quiescent state.

Java's `AtomicStampedReference` solves ABA:

```java
AtomicStampedReference<Node> head = new AtomicStampedReference<>(sentinel, 0);

int[] stampHolder = new int[1];
Node current = head.get(stampHolder);
int stamp = stampHolder[0];

// CAS checks both reference AND stamp
head.compareAndSet(current, newNode, stamp, stamp + 1);
```

---

## 7. The LMAX Disruptor

### 7.1 Background

LMAX Exchange processes 6 million orders per second on a single thread. The key insight: lock-free, single-writer, pre-allocated ring buffer.

### 7.2 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Ring Buffer (pre-allocated)                │
│                                                              │
│   ┌────┬────┬────┬────┬────┬────┬────┬────┐                  │
│   │ S0 │ S1 │ S2 │ S3 │ S4 │ S5 │ S6 │ S7 │  ← Slots       │
│   └────┴────┴────┴────┴────┴────┴────┴────┘                  │
│     ▲                        ▲                               │
│     │                        │                               │
│   Consumer                Producer                           │
│   Sequence               Sequence                            │
│   (4)                    (7)                                  │
│                                                              │
│   Available slots = Producer - Consumer                      │
│   Consumer can read slots [Consumer+1 .. Producer]           │
└──────────────────────────────────────────────────────────────┘
```

### 7.3 Key Design Principles

1. **Pre-allocation:** All slots are allocated at startup. No GC pressure during operation.
2. **Single writer:** Only one thread writes to the ring buffer. No CAS needed for writes.
3. **Mechanical sympathy:** Slots are contiguous in memory → cache-line friendly.
4. **Sequence barriers:** Consumers track their position with atomic longs. No locks.
5. **Padding:** Sequence counters are padded to avoid false sharing.

### 7.4 Performance Comparison

| Structure | Throughput (ops/sec) | Latency (p99) |
|---|---|---|
| `ArrayBlockingQueue` (Java) | ~5M | ~1 μs |
| `ConcurrentLinkedQueue` (Java) | ~15M | ~500 ns |
| LMAX Disruptor | ~100M+ | ~100 ns |

The Disruptor is 20x faster than `ArrayBlockingQueue` because:
- No locks (single writer, sequence barriers).
- No allocation (pre-allocated ring buffer).
- Cache-line padding on sequences.
- Sequential memory access pattern.

### 7.5 When to Use

- Ultra-low-latency messaging (financial trading, real-time analytics).
- Single-machine, high-throughput event processing.
- Replacement for traditional producer-consumer queues when lock contention is the bottleneck.

---

## 8. Connection Pooling

### 8.1 The Cost of Opening Connections

```
TCP connection setup:
  Client → SYN → Server         ~0.5 ms (LAN)
  Server → SYN-ACK → Client     ~0.5 ms
  Client → ACK → Server         ~0.5 ms
  Total: ~1.5 ms

TLS handshake (on top of TCP):
  ClientHello → ServerHello → Certificate → KeyExchange
  Total: ~5-15 ms (1-RTT for TLS 1.3, 2-RTT for TLS 1.2)

Database connection:
  TCP + TLS + authentication + session setup
  Total: ~10-50 ms
```

If every request opens and closes a connection, you pay this cost per request. At 10,000 requests/second, that is 100-500 seconds of pure connection overhead.

### 8.2 Pool Architecture

```
┌──────────────────────────────────────────────┐
│                Connection Pool                │
│                                              │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐        │
│  │Conn 1│ │Conn 2│ │Conn 3│ │Conn 4│  Idle  │
│  │ IDLE │ │ BUSY │ │ IDLE │ │ BUSY │        │
│  └──────┘ └──────┘ └──────┘ └──────┘        │
│                                              │
│  Config:                                     │
│    min_size: 5        (keep 5 warm)           │
│    max_size: 20       (never exceed 20)       │
│    idle_timeout: 300s (close idle after 5m)   │
│    max_lifetime: 1800s (replace after 30m)    │
│    acquire_timeout: 5s (wait max 5s)          │
│    validation: "SELECT 1" every 30s           │
└──────────────────────────────────────────────┘
```

### 8.3 Sizing Formula

Little's Law: `L = λ * W`
- L = number of connections needed
- λ = request rate (requests/second)
- W = average time a connection is held (seconds)

```
Example:
  λ = 1000 req/sec
  W = 0.010 sec (10ms average query time)
  L = 1000 * 0.010 = 10 connections

Add 20% headroom: pool_size = 12
```

**Common mistake:** setting pool size too high. PostgreSQL recommendation: `pool_size = (2 * cores) + disk_spindles`. For SSDs, `2 * cores` is often sufficient. More connections = more context switching, more memory per connection, worse performance.

### 8.4 Connection Pool Implementation

```python
import threading
import time
from collections import deque
from typing import Optional


class ConnectionPool:
    def __init__(self, factory, min_size=5, max_size=20,
                 idle_timeout=300, acquire_timeout=5):
        self._factory = factory
        self._min_size = min_size
        self._max_size = max_size
        self._idle_timeout = idle_timeout
        self._acquire_timeout = acquire_timeout

        self._idle: deque = deque()
        self._active: int = 0
        self._lock = threading.Lock()
        self._available = threading.Condition(self._lock)

        # Pre-warm pool
        for _ in range(min_size):
            conn = self._factory.create()
            self._idle.append((conn, time.monotonic()))
            self._active += 1

    def acquire(self):
        deadline = time.monotonic() + self._acquire_timeout
        with self._lock:
            while True:
                # Try to get an idle connection
                while self._idle:
                    conn, idle_since = self._idle.popleft()
                    if time.monotonic() - idle_since > self._idle_timeout:
                        self._factory.destroy(conn)
                        self._active -= 1
                        continue
                    if self._factory.validate(conn):
                        return conn
                    self._factory.destroy(conn)
                    self._active -= 1

                # Create new if under max
                if self._active < self._max_size:
                    self._active += 1
                    conn = self._factory.create()
                    return conn

                # Wait for a connection to be released
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Could not acquire connection")
                self._available.wait(timeout=remaining)

    def release(self, conn):
        with self._lock:
            self._idle.append((conn, time.monotonic()))
            self._available.notify()
```

### 8.5 Connection Pool Monitoring

| Metric | Alert Threshold |
|---|---|
| Pool utilization (active/max) | > 80% sustained |
| Acquire wait time | > 1s p99 |
| Validation failures | > 5% |
| Connection creation rate | Spiky (indicates pool exhaustion + recreation) |
| Idle connection count | 0 sustained (pool too small) |

---

## 9. Async I/O & Event Loops

### 9.1 The Problem with Blocking I/O

```
Thread-per-request model:

Thread 1: [──── accept ──── read DB (50ms idle) ──── respond ────]
Thread 2: [──── accept ──── read DB (50ms idle) ──── respond ────]
...
Thread 1000: [──── accept ──── read DB (50ms idle) ──── respond ────]

1000 threads, each idle 95% of the time.
Memory: ~1 MB per thread stack = 1 GB just for stacks.
Context switching overhead: significant at 1000+ threads.
```

### 9.2 Event Loop Architecture

```
Single thread:

┌─────────────────────────────────────────────────────────┐
│                    Event Loop                           │
│                                                         │
│   ┌──────────┐                                          │
│   │  epoll / │     ┌───────────────────────────────┐    │
│   │  kqueue  │────▶│  Ready events                  │    │
│   │  io_uring│     │  fd=5: data ready (read)       │    │
│   └──────────┘     │  fd=8: write complete           │    │
│                    │  fd=12: new connection           │    │
│                    └───────────────────────────────┘    │
│                         │                               │
│                         ▼                               │
│               ┌──────────────────┐                      │
│               │ Dispatch to      │                      │
│               │ callbacks/        │                      │
│               │ coroutines        │                      │
│               └──────────────────┘                      │
│                                                         │
│   One thread handles 10,000+ connections                │
│   CPU never idles waiting for I/O                       │
└─────────────────────────────────────────────────────────┘
```

### 9.3 Linux I/O Models

| Model | Mechanism | Blocking? | Copies | Throughput |
|---|---|---|---|---|
| **Blocking** | `read()` | Yes | Kernel → User | Low (thread-bound) |
| **Non-blocking** | `read()` + `poll()` | No | Kernel → User | Medium |
| **epoll** | Event notification | No | Kernel → User | High |
| **io_uring** | Submission/completion queues | No | Kernel → User (or zero-copy) | Highest |

### 9.4 io_uring (Linux 5.1+)

The newest and fastest I/O interface on Linux. Uses shared ring buffers between userspace and kernel — no system calls for submission/completion.

```
Userspace                          Kernel
┌──────────────────┐     ┌──────────────────┐
│ Submission Queue │────▶│ Process I/O      │
│ (SQ) - ring buf  │     │ operations       │
└──────────────────┘     └────────┬─────────┘
                                  │
┌──────────────────┐              │
│ Completion Queue │◀─────────────┘
│ (CQ) - ring buf  │
└──────────────────┘

No system calls needed for batched I/O.
Kernel and userspace share memory-mapped ring buffers.
```

### 9.5 Async Patterns by Language

| Language | Async Model | Key Type |
|---|---|---|
| Python | asyncio event loop | `async def`, `await` |
| JavaScript/Node | libuv event loop | `Promise`, `async/await` |
| Java | Virtual threads (Project Loom, JDK 21+) | `Thread.ofVirtual()` |
| Go | Goroutines (M:N scheduler) | `go func()` |
| Rust | tokio / async-std | `async fn`, `.await` |
| C# | Task-based async (TPL) | `async Task`, `await` |

---

## 10. Zero-Copy Techniques

### 10.1 The Problem: Traditional File Transfer

```
Traditional read + write (4 copies, 4 context switches):

1. read(file_fd, buffer, size)
   Kernel reads from disk → Kernel buffer (DMA)     ← copy 1
   Kernel buffer → User buffer                      ← copy 2
   (context switch: kernel → user)

2. write(socket_fd, buffer, size)
   User buffer → Kernel socket buffer               ← copy 3
   (context switch: user → kernel)
   Kernel socket buffer → NIC (DMA)                 ← copy 4
```

Four copies. Two are unnecessary (user buffer is just a relay).

### 10.2 sendfile() — Zero-Copy File Transfer

```c
// Linux sendfile: 2 copies, 2 context switches
sendfile(socket_fd, file_fd, offset, count);

// Data path:
// Disk → Kernel buffer (DMA)          ← copy 1
// Kernel buffer → NIC (DMA)           ← copy 2
// User space is never involved.
```

With `sendfile()`, the data never enters userspace. Used by web servers (Nginx, Apache) and Kafka for log segment serving.

### 10.3 mmap — Memory-Mapped Files

```c
void *addr = mmap(NULL, file_size, PROT_READ, MAP_PRIVATE, fd, 0);
// File is now accessible as a memory region.
// No explicit read() calls needed.
// Pages are loaded on demand (page faults → kernel loads from disk).

write(socket_fd, addr, file_size);
// Still copies from kernel to socket buffer, but avoids read() overhead.
```

Used by: databases (LMDB, SQLite), message brokers (Kafka log files), search engines (Lucene).

### 10.4 splice() — Pipe-Based Zero-Copy

Linux-specific. Moves data between file descriptors via a pipe without user-space copies.

```c
int pipefd[2];
pipe(pipefd);

// Move data from file to pipe (no copy)
splice(file_fd, &offset, pipefd[1], NULL, count, SPLICE_F_MOVE);

// Move data from pipe to socket (no copy)
splice(pipefd[0], NULL, socket_fd, NULL, count, SPLICE_F_MOVE);
```

### 10.5 When to Use Zero-Copy

| Technique | Use Case | Limitation |
|---|---|---|
| `sendfile` | Serving static files over network | File → socket only |
| `mmap` | Database storage, read-heavy file access | TLB pressure on large files |
| `splice` | Proxying between file descriptors | Linux only, pipe-based |
| `io_uring` | General high-performance I/O | Linux 5.1+, complex API |

---

## 11. Cache Hierarchies — L1/L2/L3 to Redis

### 11.1 Multi-Level Application Cache

```
┌─────────────────────────────────────────────────────────────┐
│                 Application Cache Hierarchy                  │
│                                                              │
│  ┌──────────────────┐   Hit: < 1 μs                         │
│  │  L1: In-Process   │   (Caffeine, Guava, lru_cache)       │
│  │  (per instance)   │                                       │
│  └────────┬─────────┘                                       │
│           │ Miss                                            │
│  ┌────────▼─────────┐   Hit: 0.1-1 ms                      │
│  │  L2: Distributed  │   (Redis, Memcached)                  │
│  │  (shared cluster) │                                       │
│  └────────┬─────────┘                                       │
│           │ Miss                                            │
│  ┌────────▼─────────┐   Hit: 1-100 ms                      │
│  │  L3: Database     │   (PostgreSQL, MySQL)                 │
│  │  (source of truth)│                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

### 11.2 L1: In-Process Cache

```python
from functools import lru_cache

@lru_cache(maxsize=1024)
def get_product(product_id: str):
    return db.query("SELECT * FROM products WHERE id = %s", product_id)
```

**Pros:** Fastest possible (no network), no serialization.
**Cons:** Per-instance (N instances = N caches, potential inconsistency), limited by process memory, lost on restart.

**Better: W-TinyLFU (Caffeine in Java):**

```java
Cache<String, Product> cache = Caffeine.newBuilder()
    .maximumSize(10_000)
    .expireAfterWrite(Duration.ofMinutes(5))
    .recordStats()  // hit rate, eviction count
    .build();

Product product = cache.get(productId, id -> db.findById(id));
```

### 11.3 L2: Distributed Cache (Redis)

```python
import redis
import json

r = redis.Redis(host='redis-cluster', port=6379)

def get_product(product_id: str) -> dict:
    # L1: check in-process cache (not shown)
    
    # L2: check Redis
    cached = r.get(f"product:{product_id}")
    if cached:
        return json.loads(cached)
    
    # L3: database
    product = db.query("SELECT * FROM products WHERE id = %s", product_id)
    
    # Populate L2
    r.setex(f"product:{product_id}", 300, json.dumps(product))  # TTL 5 min
    
    return product
```

### 11.4 Cache Invalidation Strategies

| Strategy | How | Trade-off |
|---|---|---|
| **TTL (Time-To-Live)** | Cache expires after N seconds | Simple, bounded staleness, but stale reads within TTL |
| **Event-Based** | Publish event on write, subscribers invalidate | Near-real-time, but requires event infrastructure |
| **Write-Through** | Update cache on every write | Always fresh, but higher write latency |
| **Cache-Aside + Invalidation** | Delete cache key on write; next read repopulates | Simple, but brief window of inconsistency |

### 11.5 The Thundering Herd Problem

When a popular cache key expires, hundreds of concurrent requests all miss the cache and all hit the database simultaneously.

**Solution 1: Request Coalescing (singleflight in Go):**

```go
import "golang.org/x/sync/singleflight"

var group singleflight.Group

func GetProduct(id string) (*Product, error) {
    result, err, _ := group.Do(id, func() (interface{}, error) {
        // Only ONE goroutine executes this
        // Others with the same key wait for the result
        return db.FindProduct(id)
    })
    return result.(*Product), err
}
```

**Solution 2: Probabilistic Early Expiration (X-Fetch):**

```python
import random, time

def get_with_early_expiration(key, ttl=300, beta=1.0):
    """
    With probability increasing as TTL approaches,
    one request recomputes the value while others
    serve the existing (soon-to-expire) cached value.
    """
    cached = cache.get(key)
    if cached:
        value, expiry, delta = cached
        # delta = time to recompute
        if time.time() - delta * beta * math.log(random.random()) < expiry:
            return value
        # else: this request will recompute

    # Recompute
    start = time.time()
    value = expensive_computation(key)
    delta = time.time() - start
    cache.set(key, (value, time.time() + ttl, delta))
    return value
```

### 11.6 Modern Eviction: W-TinyLFU

Already introduced in the original stub. Detailed architecture:

```
┌────────────────────────────────────────────────────────────┐
│                    W-TinyLFU Cache                         │
│                                                            │
│  ┌────────────────┐                                        │
│  │  Window Cache   │  1% of total capacity                 │
│  │  (LRU)          │  New items enter here first           │
│  └───────┬────────┘                                        │
│          │ Evicted from window                             │
│          ▼                                                 │
│  ┌────────────────┐                                        │
│  │  Admission      │  Count-Min Sketch (frequency estimate)│
│  │  Filter         │  + Bloom Filter (doorkeeper)          │
│  │                 │                                        │
│  │  Compare freq(candidate) vs freq(victim)                │
│  │  If candidate is hotter → admit                         │
│  │  Else → reject candidate, keep victim                   │
│  └───────┬────────┘                                        │
│          │ Admitted                                         │
│          ▼                                                 │
│  ┌────────────────┐                                        │
│  │  Main Cache     │  99% of total capacity                │
│  │  (Segmented LRU)│  Probation → Protected segments       │
│  └────────────────┘                                        │
└────────────────────────────────────────────────────────────┘
```

---

## 12. Hot Path Optimization

### 12.1 Identify the Hot Path

The hot path is the code executed for every request. Optimizing cold paths (error handling, startup, admin endpoints) is wasted effort.

```
Request flow:
  Parse HTTP request     ← hot path
  Authenticate           ← hot path
  Validate input         ← hot path
  Business logic         ← hot path
  Serialize response     ← hot path
  Write access log       ← hot path (consider async)

  Generate PDF report    ← cold path (rare)
  Send welcome email     ← cold path (once per user)
  Database migration     ← cold path (once per deploy)
```

### 12.2 Hot Path Rules

1. **No allocation on hot path.** Pre-allocate buffers, pool objects.
2. **No I/O on hot path** unless the I/O *is* the purpose. Defer logging, metrics aggregation.
3. **No locks on hot path.** Use lock-free structures or partition data by thread.
4. **No virtual dispatch on hot path** (if possible). Inline or monomorphize.
5. **Minimize branches.** Use lookup tables, branch-free arithmetic.
6. **Batch operations.** Process N items per system call, not 1.

### 12.3 Example: Optimizing a JSON Parser

```python
# SLOW: naive per-character parsing
def parse_json_slow(data: bytes) -> dict:
    text = data.decode("utf-8")          # copy + decode
    return json.loads(text)              # re-parse from string

# FAST: use orjson (C extension, zero-copy where possible)
import orjson

def parse_json_fast(data: bytes) -> dict:
    return orjson.loads(data)            # direct from bytes, SIMD-optimized
```

`orjson` is 3-10x faster than `json.loads` because:
- Parses bytes directly (no UTF-8 decode step).
- Uses SIMD instructions for string scanning.
- Minimal allocation.

---

## 13. Memory Allocation & Pooling

### 13.1 The Cost of malloc

General-purpose allocators (`malloc`, `new`, Go's GC) are designed for correctness and flexibility, not for hot-path speed.

| Allocator | Typical Latency |
|---|---|
| `malloc` (glibc) | 50-200 ns |
| `jemalloc` | 30-100 ns |
| `tcmalloc` | 20-80 ns |
| Arena/bump allocator | 1-5 ns |
| Object pool (reuse) | 0 ns (no allocation) |

### 13.2 Object Pooling

```python
class ByteBufferPool:
    """Pool of pre-allocated byte buffers to avoid repeated allocation."""
    def __init__(self, buffer_size: int, pool_size: int):
        self._size = buffer_size
        self._pool = [bytearray(buffer_size) for _ in range(pool_size)]

    def acquire(self) -> bytearray:
        if self._pool:
            return self._pool.pop()
        return bytearray(self._size)  # fallback: allocate new

    def release(self, buf: bytearray) -> None:
        if len(self._pool) < 100:  # cap pool size
            self._pool.append(buf)
```

### 13.3 Arena Allocation

Allocate from a contiguous block. Free everything at once (per-request arena).

```c
typedef struct {
    char *base;
    size_t offset;
    size_t capacity;
} Arena;

void *arena_alloc(Arena *a, size_t size) {
    size = (size + 7) & ~7;  // align to 8 bytes
    if (a->offset + size > a->capacity) return NULL;
    void *ptr = a->base + a->offset;
    a->offset += size;
    return ptr;
}

void arena_reset(Arena *a) {
    a->offset = 0;  // "free" everything at once
}
```

Used by: Go's per-goroutine stack, game engines, request-scoped allocation in web servers.

---

## 14. Profiling & Benchmarking

### 14.1 Golden Rules

1. **Measure before optimizing.** Intuition about bottlenecks is wrong ~80% of the time.
2. **Profile in production-like conditions.** Benchmarks on a laptop with 8 items do not reflect production with 8 million.
3. **Benchmark one thing at a time.** Change one variable, measure, repeat.
4. **Warm up.** JIT compilation, cache warming, and connection pool filling change performance characteristics.

### 14.2 CPU Profiling Tools

| Tool | Language | Type |
|---|---|---|
| `perf` | Any (Linux) | Sampling, hardware counters |
| `async-profiler` | Java | CPU + allocation, low overhead |
| `py-spy` | Python | Sampling, no code changes |
| `pprof` | Go | CPU, memory, goroutine |
| `VTune` | Any | Deep CPU analysis (Intel) |
| `Instruments` | Any (macOS) | Time Profiler, Allocations |

### 14.3 Reading a Flame Graph

```
                    ┌──────────────────────────┐
                    │      main()              │ 100%
                    ├────────────┬─────────────┤
                    │ handleReq()│  startup()   │
                    │    85%     │    15%       │
                    ├─────┬──────┤              │
                    │parse│query │              │
                    │ 20% │ 65%  │              │
                    │     ├──────┤              │
                    │     │ IO   │              │
                    │     │ 60%  │              │
                    │     └──────┘              │
                    └──────────────────────────┘

Reading: query() takes 65% of handleReq() time.
         IO within query() is the bottleneck (60%).
         Optimize the IO path, not parse.
```

### 14.4 Micro-Benchmark Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Dead code elimination | Compiler optimizes away your benchmark | Consume the result (blackhole) |
| Constant folding | Compiler computes result at compile time | Use runtime-variable inputs |
| No warmup | First iterations skewed by JIT/cache cold | Run warmup iterations, discard |
| Too few iterations | High variance, unreliable results | Run for at least 1 second or 10K iterations |
| Measuring the wrong thing | Benchmark includes setup/teardown | Isolate the hot path |

---

## 14b. Hardware Performance Counters

### 14b.1 What Hardware Counters Measure

Modern CPUs expose hundreds of performance counters. The most useful for software optimization:

| Counter | What It Measures | Optimization Indicator |
|---|---|---|
| `cache-misses` | L1/L2/L3 cache misses | Data locality problems |
| `cache-references` | Total cache accesses | Baseline for miss ratio |
| `branch-misses` | Mispredicted branches | Branch-heavy code on random data |
| `instructions` | Instructions executed | Workload volume |
| `cycles` | CPU cycles consumed | Efficiency (IPC = instructions/cycles) |
| `page-faults` | Memory page faults | Memory mapping, swap |
| `context-switches` | Thread context switches | Lock contention, over-threading |
| `cpu-migrations` | Core migrations | NUMA issues, affinity problems |

### 14b.2 Using perf stat

```bash
# Basic CPU counters
perf stat -e cycles,instructions,cache-misses,cache-references,branch-misses \
    ./my_application

# Output:
#   1,234,567,890  cycles
#     987,654,321  instructions  # IPC = 0.80 (below 1.0 → likely memory bound)
#      12,345,678  cache-misses  # 5.2% of cache-references → investigate
#     237,654,321  cache-references
#       1,234,567  branch-misses # 3.1% → acceptable

# NUMA monitoring
perf stat -e node-loads,node-load-misses ./my_application
# node-load-misses > 10% → NUMA locality problem
```

### 14b.3 IPC (Instructions Per Cycle) Guide

| IPC | Interpretation |
|---|---|
| > 2.0 | CPU-bound, compute-heavy (good) |
| 1.0 - 2.0 | Typical application code |
| 0.5 - 1.0 | Memory-bound or stalled on branches |
| < 0.5 | Severely memory-bound (cache thrashing) |

### 14b.4 Systematic Performance Investigation

```
Step 1: Is it CPU-bound or I/O-bound?
  → perf stat: high CPU utilization + high IPC = CPU-bound
  → low CPU utilization + high wall time = I/O-bound

Step 2: If CPU-bound, what is the bottleneck?
  → High cache-miss rate = data locality problem
  → High branch-miss rate = unpredictable branches
  → High context-switches = lock contention
  → Low IPC = pipeline stalls (memory or branch)

Step 3: If I/O-bound, what I/O?
  → Disk: use iostat, iotop
  → Network: use ss, netstat, tcpdump
  → Lock contention: use perf lock, mutrace

Step 4: Optimize the top bottleneck
  → Cache: reorganize data layout (SoA, prefetch)
  → Branch: sort data, use branch-free code
  → Lock: reduce critical section, use lock-free
  → I/O: use async I/O, batching, connection pooling
```

---

## 14c. Batching and Vectorization

### 14c.1 Batching I/O Operations

Instead of issuing one system call per item, batch them:

```python
# SLOW: one insert per row
for row in rows:
    db.execute("INSERT INTO events (id, data) VALUES (%s, %s)", row)
# 10,000 rows → 10,000 system calls + network round trips

# FAST: batch insert
db.executemany(
    "INSERT INTO events (id, data) VALUES (%s, %s)",
    rows,
)
# 10,000 rows → 1 system call + 1 network round trip

# FASTEST: COPY (PostgreSQL)
with db.cursor() as cur:
    cur.copy_from(csv_buffer, "events", columns=("id", "data"))
```

**Kafka:** batch produces. Instead of producing one message at a time, use `batch.size` and `linger.ms` to accumulate messages:

```python
producer = KafkaProducer(
    batch_size=16384,      # 16 KB batch
    linger_ms=5,           # wait 5ms to accumulate
    compression_type="lz4", # compress the batch
)
```

### 14c.2 SIMD Vectorization

SIMD (Single Instruction, Multiple Data) processes multiple data elements with one instruction.

```
Scalar:  process 1 float per cycle
SIMD:    process 4/8/16 floats per cycle (SSE/AVX/AVX-512)

Example (sum of array):
Scalar: 1 add per cycle → N cycles
AVX2:   8 adds per cycle → N/8 cycles (8x speedup)
AVX-512: 16 adds per cycle → N/16 cycles (16x speedup)
```

Compilers auto-vectorize simple loops. To help the compiler:

```c
// Enable auto-vectorization
// Compile with: -O2 -march=native -ftree-vectorize

// This loop will be auto-vectorized:
void add_arrays(float *a, float *b, float *c, int n) {
    for (int i = 0; i < n; i++) {
        c[i] = a[i] + b[i];  // simple, no dependencies
    }
}

// This loop will NOT be auto-vectorized (loop-carried dependency):
void running_sum(float *a, int n) {
    for (int i = 1; i < n; i++) {
        a[i] += a[i-1];  // depends on previous iteration
    }
}
```

Check if vectorization happened: `gcc -O2 -march=native -ftree-vectorize -fopt-info-vec-optimized`.

### 14c.3 Batching Rules of Thumb

| Operation | Optimal Batch Size | Why |
|---|---|---|
| Database inserts | 100-1000 rows | Amortize network RTT + transaction overhead |
| Kafka produces | 16-64 KB | Amortize network + compression |
| HTTP/2 requests | Multiplexed (built-in) | Single connection, interleaved streams |
| File writes | 4-64 KB | Match filesystem block size |
| Redis pipelines | 50-200 commands | Amortize network RTT |

---

## 15. Common Pitfalls & Troubleshooting

### Pitfall 1: Premature Optimization

**Symptom:** Team spends weeks optimizing a function that accounts for 0.1% of total execution time.
**Fix:** Profile first. Optimize the top 3 bottlenecks. Amdahl's Law: optimizing a 1% component by 100x speeds up the system by < 1%.

### Pitfall 2: Cache Pollution

**Symptom:** Batch job scans 10 million rows. After the batch, all hot data is evicted from cache. Online query latency spikes.
**Fix:** Use a separate cache namespace for batch. Or use W-TinyLFU (admission filter rejects cold data).

### Pitfall 3: Connection Pool Exhaustion

**Symptom:** All connections are busy. New requests timeout waiting for a connection.
**Fix:** Check for leaked connections (connections not returned to pool). Add `maxLifetime` to force recycling. Monitor pool utilization.

### Pitfall 4: GC Pauses on Hot Path

**Symptom:** p99 latency spikes every few seconds. Flame graph shows time in `GC.collect()`.
**Fix:** Reduce allocation on hot path (object pooling, pre-allocation). Tune GC (G1GC region size, ZGC for low-latency Java). Use arenas for request-scoped allocation.

### Pitfall 5: Lock Convoy

**Symptom:** Throughput drops when adding more threads. All threads spend time waiting for one lock.
**Fix:** Partition data by thread (no shared state). Use lock-free structures. Use reader-writer locks if reads dominate.

---

## 16. Q&A — Frequently Asked Questions

**Q1: When is lock-free programming worth the complexity?**
A: Only on proven hot paths where lock contention is measured (not assumed). For most code, a well-protected mutex is simpler and fast enough. Lock-free is for infrastructure components (queues, allocators, counters) at extreme scale.

**Q2: Should I always use zero-copy?**
A: No. Zero-copy helps when transferring large files or high-throughput streaming. For small payloads (< 4 KB), the overhead of setting up `sendfile()` or `splice()` can exceed the copy cost.

**Q3: How do I choose between epoll, kqueue, and io_uring?**
A: Use the platform's best option. Linux: `io_uring` (if kernel 5.1+), else `epoll`. macOS/BSD: `kqueue`. In practice, use a framework (tokio, asyncio, libuv) that abstracts the choice.

**Q4: How do I size a connection pool for microservices?**
A: Start with `2 * cores` per database. Load test. If acquire wait time exceeds 500ms at p99, increase cautiously. More connections is not always better — it can worsen database performance due to context switching and lock contention.

**Q5: When should I use SoA vs AoS?**
A: SoA when you process one or a few fields across many elements (e.g., physics simulation, columnar analytics). AoS when you access all fields of one element at a time (e.g., loading a user profile).

**Q6: Is Redis fast enough as an L2 cache, or should I use Memcached?**
A: Both are fast (sub-millisecond). Redis is richer (data structures, persistence, pub/sub). Memcached is simpler and slightly faster for pure key-value get/set. For most applications, Redis is the default choice. Memcached if you need multi-threaded scaling with simpler ops.

---

## 17. Hands-On Exercises

### Exercise 1: False Sharing Benchmark (Beginner)

Write a multi-threaded counter benchmark.

**Requirements:**
- Version A: Array of `long`, one per thread (false sharing).
- Version B: Array of padded structs (64-byte aligned), one per thread.
- Each thread increments its counter 100 million times.
- Measure total time for both versions with 1, 2, 4, 8 threads.

**Expected result:** Version B is 5-20x faster with multiple threads.

### Exercise 2: Connection Pool (Intermediate)

Build a connection pool from scratch.

**Requirements:**
- Implement acquire/release with a bounded pool.
- Support `min_size`, `max_size`, `idle_timeout`, `acquire_timeout`.
- Validate connections on acquire (stale connection detection).
- Thread-safe.
- Write a load test: 100 concurrent goroutines/threads, each acquiring and releasing 1000 times.

### Exercise 3: Lock-Free Stack (Intermediate)

Implement a Treiber stack (lock-free stack using CAS).

**Requirements:**
- `push(item)` and `pop()` using CAS.
- Handle ABA problem (use tagged pointer or AtomicStampedReference).
- Benchmark against `synchronized` stack with 8 threads.

### Exercise 4: Zero-Copy File Server (Advanced)

Build a static file server that uses `sendfile()`.

**Requirements:**
- Accept HTTP GET requests.
- Serve files using `sendfile()` (or `os.sendfile` in Python, `FileChannel.transferTo` in Java).
- Compare throughput against a naive read-write implementation for a 100 MB file.
- Measure using `wrk` or `ab`.

### Exercise 5: Cache Hierarchy with Thundering Herd Protection (Advanced)

Build a two-level cache (L1 in-process + L2 Redis) with thundering herd protection.

**Requirements:**
- L1: LRU cache with 1000 entries.
- L2: Redis with 5-minute TTL.
- On L2 miss, use request coalescing (singleflight) to prevent multiple threads from hitting the database simultaneously.
- Benchmark: 100 concurrent requests for the same cold key. Database should receive exactly 1 query.

### Exercise 6: NUMA-Aware Benchmark (Advanced)

On a multi-socket server (or a NUMA-simulated VM):

**Requirements:**
- Write a memory-intensive benchmark (large array scan).
- Run with `numactl --membind=0 --cpunodebind=0` (local access).
- Run with `numactl --membind=1 --cpunodebind=0` (remote access).
- Measure throughput difference.

**Expected result:** Local access is 1.5-2x faster than remote.

### Exercise 7: Branch Prediction Lab (Beginner)

**Requirements:**
- Create an array of 100,000 random integers (0-255).
- Sum all values >= 128 using an if-branch.
- Measure time for: (a) unsorted array, (b) sorted array.
- Implement a branch-free version and measure.

**Expected result:** Sorted version is 3-5x faster due to branch prediction. Branch-free matches sorted performance.

---

## 18. Tail Latency & Percentile Optimization

### 18.1 Why p99 Matters More Than Average

```
Average latency: 5 ms (looks fine)
p50: 3 ms
p95: 8 ms
p99: 150 ms    ← 1 in 100 requests waits 30x longer
p99.9: 2,000 ms ← 1 in 1000 requests waits 400x longer

At 1000 req/s:
  10 requests/sec experience > 150ms latency
  1 request/sec experiences > 2s latency
```

In a microservices system with fan-out, tail latency compounds:

```
Service A fans out to 10 backends in parallel.
P(at least one backend hits p99) = 1 - (0.99)^10 = 9.6%

Nearly 10% of requests hit the tail.
At 100 backends: 1 - (0.99)^100 = 63% of requests hit the tail.
```

### 18.2 Hedged Requests

Send the same request to multiple backends. Use the first response that comes back.

```python
async def hedged_request(backends, request, delay_ms=10):
    """
    Send request to first backend immediately.
    If no response within delay_ms, send to second backend.
    Return whichever responds first.
    """
    tasks = []
    for i, backend in enumerate(backends):
        if i > 0:
            await asyncio.sleep(delay_ms / 1000)  # stagger
        task = asyncio.create_task(backend.send(request))
        tasks.append(task)

        # Check if any completed during the delay
        done, _ = await asyncio.wait(tasks, timeout=0)
        if done:
            for t in tasks:
                if t not in done:
                    t.cancel()
            return done.pop().result()

    # Wait for any to complete
    done, pending = await asyncio.wait(
        tasks, return_when=asyncio.FIRST_COMPLETED
    )
    for t in pending:
        t.cancel()
    return done.pop().result()
```

**Trade-off:** Uses extra backend capacity (~5% overhead if delay is tuned well), but dramatically reduces p99.

### 18.3 Tied Requests (Google)

Like hedged requests, but both replicas are aware. The first to start processing notifies the other to cancel.

### 18.4 Tail Tolerant Strategies

| Strategy | How | When |
|---|---|---|
| **Hedged requests** | Send duplicate, use first response | Read-only, idempotent operations |
| **Tied requests** | Like hedged, but with cancellation | Same, with resource conservation |
| **Canary requests** | Test one backend before fan-out | New deployments |
| **Good-enough results** | Return partial results + timeout indicator | Search, recommendations |
| **Adaptive timeouts** | p95 of recent latency as timeout | All remote calls |

---

## 19. Kernel Bypass & DPDK

### 19.1 The Cost of the Kernel

The Linux kernel networking stack adds:
- System calls (`sendto`, `recvfrom`): ~100 ns overhead per call.
- Buffer copies (user → kernel → NIC).
- Interrupt handling for each packet.
- Socket buffer management.

For 10 Gbps / 40 Gbps networking, the kernel becomes the bottleneck.

### 19.2 DPDK (Data Plane Development Kit)

DPDK bypasses the kernel entirely. The NIC is mapped into userspace. Packets are read/written directly.

```
Traditional:
  NIC → Kernel (interrupt) → Socket → User process
  Latency: ~10 μs per packet

DPDK:
  NIC → User process (poll mode, busy-wait)
  Latency: ~1 μs per packet
```

**Use cases:** High-frequency trading, telecom packet processing, DDoS mitigation (Cloudflare).
**Drawback:** Dedicates CPU cores to polling (no idle), requires driver support, bypasses kernel security/firewall.

### 19.3 XDP (eXpress Data Path)

A lighter-weight alternative. BPF programs run in the kernel *before* the networking stack processes the packet. Faster than the full stack, but still in kernel space.

```
NIC → XDP (BPF program) → DROP / PASS / REDIRECT
                            │
                            ▼ (PASS only)
                       Normal kernel stack
```

**Use case:** DDoS filtering, load balancing at line rate.

---

## 20. Consistent Hashing for Cache Distribution

### 20.1 Problem

Distributing 1 TB of cached data across 4 Redis nodes. Simple modulo hashing: `node = hash(key) % 4`.

Adding a 5th node changes the assignment for ~80% of keys → massive cache miss storm.

### 20.2 Consistent Hashing Solution

Map nodes and keys onto a hash ring. Each key is assigned to the next node clockwise.

```
        Node A (90°)
           ●
          / \
         /   \
Key X → ●     ● Node B (180°)
       /       \
      /         \
     ● Node D    ● Node C
   (315°)      (270°)

Key X (hash = 120°) → assigned to Node B (next clockwise = 180°)

Add Node E at 150°:
  Only keys between 90° and 150° move from B to E.
  All other keys stay put.
```

### 20.3 Virtual Nodes

Without virtual nodes, node positions are random → uneven load.

```
With 100 virtual nodes per physical node:
  Node A → A1, A2, ... A100 (100 points on ring)
  Node B → B1, B2, ... B100

  Statistical distribution approaches uniform.
  Adding/removing a node moves ~K/N keys (K = total keys, N = nodes).
```

### 20.4 Jump Consistent Hash

Google's alternative. No ring, O(1) per lookup, perfectly balanced:

```c
int32_t JumpConsistentHash(uint64_t key, int32_t num_buckets) {
    int64_t b = -1, j = 0;
    while (j < num_buckets) {
        b = j;
        key = key * 2862933555777941757ULL + 1;
        j = (int64_t)((b + 1) * ((double)(1LL << 31) /
            ((double)((key >> 33) + 1))));
    }
    return b;
}
```

**Pros:** No memory overhead, perfectly balanced, O(ln n) time.
**Cons:** Does not support weighted nodes or named nodes (only numbered buckets).

---

## 21. Write Amplification & Log-Structured Storage

### 21.1 B-Tree Write Amplification

B-trees (PostgreSQL, MySQL InnoDB) update pages in place. A single row update may require:
1. Read the page from disk (if not cached).
2. Modify the page.
3. Write the entire page (typically 4-16 KB) for one small change.
4. Update the WAL (another write).

Write amplification = (bytes written to disk) / (bytes of actual data change). B-trees typically have 10-30x amplification.

### 21.2 LSM-Tree (Log-Structured Merge-Tree)

Used by: RocksDB, LevelDB, Cassandra, HBase, CockroachDB.

```
                    Memory
┌──────────────────────────────────────────┐
│  MemTable (Red-Black Tree / Skip List)   │
│  Write here (sorted, in-memory)          │
└────────────────────┬─────────────────────┘
                     │ Flush when full
                     ▼
                    Disk
┌──────────────────────────────────────────┐
│  Level 0: SSTable files (sorted runs)    │
│  ┌─────┐ ┌─────┐ ┌─────┐                │
│  │ SST │ │ SST │ │ SST │  (may overlap)  │
│  └─────┘ └─────┘ └─────┘                │
├──────────────────────────────────────────┤
│  Level 1: Merged SSTables (no overlap)   │
│  ┌─────────────────────────┐             │
│  │     Merged SSTable      │             │
│  └─────────────────────────┘             │
├──────────────────────────────────────────┤
│  Level 2: Larger merged SSTables         │
│  ...                                     │
└──────────────────────────────────────────┘
```

**Writes:** Append to MemTable (fast, sequential).
**Reads:** Check MemTable → L0 → L1 → ... (use Bloom filters per SSTable to skip).
**Compaction:** Merge levels in background → write amplification, but writes are sequential (disk-friendly).

### 21.3 B-Tree vs LSM-Tree Trade-offs

| Dimension | B-Tree | LSM-Tree |
|---|---|---|
| Write throughput | Moderate (random I/O) | High (sequential I/O) |
| Read latency | Low (single page lookup) | Higher (check multiple levels) |
| Write amplification | 10-30x | 10-30x (different source: compaction) |
| Space amplification | Low | Higher (duplicate keys across levels) |
| Best for | Read-heavy, OLTP | Write-heavy, time-series, logging |

---

## 22. Performance Checklist

Before marking a system "performance-ready":

- [ ] Hot path identified via profiling (not guessing)
- [ ] Cache hierarchy designed (L1 in-process, L2 distributed, L3 DB)
- [ ] Connection pools sized with Little's Law
- [ ] Timeouts set on all external calls
- [ ] No false sharing on per-thread data
- [ ] No allocation on hot path (object pools or pre-allocation)
- [ ] Async I/O for I/O-bound workloads
- [ ] NUMA awareness verified on multi-socket hardware
- [ ] p99 latency measured and acceptable
- [ ] Thundering herd protection on popular cache keys
- [ ] Load test results under expected and 2x peak traffic

---

## 23. Glossary

| Term | Definition |
|---|---|
| **ABA problem** | A CAS hazard where a value changes A→B→A, making the CAS succeed incorrectly. |
| **Branch prediction** | CPU hardware that guesses the outcome of conditional branches to keep the pipeline full. |
| **Cache line** | The unit of data transfer between CPU cache and memory, typically 64 bytes. |
| **CAS** | Compare-And-Swap: atomic operation that updates a value only if it matches the expected value. |
| **Connection pool** | A cache of reusable connections to avoid the overhead of creating new ones. |
| **DPDK** | Data Plane Development Kit: library for kernel-bypass packet processing. |
| **Epoll** | Linux kernel event notification mechanism for scalable I/O multiplexing. |
| **False sharing** | Cache coherence overhead when threads write to different variables on the same cache line. |
| **Flame graph** | Visualization of profiling data showing call stack depth and CPU time per function. |
| **io_uring** | Linux async I/O interface using shared ring buffers between user and kernel space. |
| **Lock-free** | Concurrent programming technique guaranteeing system-wide progress without locks. |
| **LSM-tree** | Log-Structured Merge-Tree: write-optimized storage using sequential writes and background compaction. |
| **Mechanical sympathy** | Writing software that works with hardware architecture, not against it. |
| **NUMA** | Non-Uniform Memory Access: architecture where memory access time depends on memory location relative to CPU. |
| **Object pool** | Pre-allocated collection of reusable objects to avoid allocation overhead. |
| **Sendfile** | System call for zero-copy file-to-socket transfer, bypassing userspace. |
| **SoA** | Struct of Arrays: data layout optimized for accessing one field across many elements. |
| **Tail latency** | The latency experienced by the slowest requests (p99, p99.9). |
| **W-TinyLFU** | Window Tiny Least Frequently Used: cache admission policy with high hit rates and scan resistance. |
| **XDP** | eXpress Data Path: BPF-based early packet processing in the Linux kernel. |
| **Zero-copy** | Data transfer technique that avoids unnecessary copying between kernel and userspace buffers. |

---

## 24. References

1. Thompson, M. "Mechanical Sympathy" blog. https://mechanical-sympathy.blogspot.com/
2. Drepper, U. "What Every Programmer Should Know About Memory" (2007). Red Hat.
3. Herlihy, M. & Shavit, N. *The Art of Multiprocessor Programming* (Morgan Kaufmann, 2012).
4. Michael, M. & Scott, M. "Simple, Fast, and Practical Non-Blocking and Blocking Concurrent Queue Algorithms" (1996). PODC.
5. LMAX Exchange. "Disruptor: High-Performance Alternative to Bounded Queues" (2011). https://lmax-exchange.github.io/disruptor/
6. Axboe, J. "io_uring" documentation. Linux kernel.
7. Einziger, G. et al. "TinyLFU: A Highly Efficient Cache Admission Policy" (2017). ACM Transactions on Storage.
8. Dean, J. & Barroso, L.A. "The Tail at Scale" (2013). Communications of the ACM.
9. Gregg, B. *Systems Performance* (Prentice Hall, 2nd edition, 2020).
10. Kerrisk, M. *The Linux Programming Interface* (No Starch Press, 2010). — sendfile, mmap, epoll.
11. Love, R. *Linux Kernel Development* (Addison-Wesley, 3rd edition, 2010). — NUMA, scheduling.
12. O'Neil, P. et al. "The Log-Structured Merge-Tree (LSM-Tree)" (1996). Acta Informatica.
13. Lamport, L. "Multiple Byte Word Lock/Unlock" (1977). — Early CAS-based synchronization.
14. Karger, D. et al. "Consistent Hashing and Random Trees" (1997). STOC.
15. Lamping, J. et al. "A Fast, Minimal Memory, Consistent Hash Algorithm" (2014). Google.

---

## 25. GC Tuning for Low-Latency Systems

### 25.1 GC Pause Impact

Garbage collection pauses directly affect tail latency. A 50ms GC pause makes p99 = 50ms regardless of your code's speed.

### 25.2 JVM GC Options for Low Latency

| GC | Max Pause | Throughput | Best For |
|---|---|---|---|
| **G1** | 10-200ms (tunable) | High | General purpose, default since JDK 9 |
| **ZGC** | < 1ms | Moderate | Low-latency applications |
| **Shenandoah** | < 10ms | Moderate | Low-latency, OpenJDK |
| **Epsilon** | 0ms (no GC) | Maximum | Short-lived processes, benchmarking |

```bash
# ZGC (recommended for low-latency JVM apps)
java -XX:+UseZGC -XX:+ZGenerational -Xmx4g -jar app.jar

# G1 with target pause
java -XX:+UseG1GC -XX:MaxGCPauseMillis=20 -Xmx4g -jar app.jar
```

### 25.3 Allocation Pressure Reduction

The best GC tuning is reducing allocation:

```java
// BAD: allocates a new String per call
public String formatPrice(double price) {
    return String.format("$%.2f", price);  // new String each time
}

// BETTER: pre-allocated formatter, reuse StringBuilder
private static final ThreadLocal<StringBuilder> SB =
    ThreadLocal.withInitial(() -> new StringBuilder(32));

public String formatPrice(double price) {
    StringBuilder sb = SB.get();
    sb.setLength(0);
    sb.append('$');
    // append formatted number without allocation
    appendDecimal(sb, price, 2);
    return sb.toString();  // still allocates, but fewer intermediaries
}
```

### 25.4 Go GC Tuning

```bash
# Set target GC percentage (default 100 = GC when heap doubles)
GOGC=200 ./my_app  # less frequent GC, more memory usage

# Memory limit (Go 1.19+)
GOMEMLIMIT=2GiB ./my_app  # GC becomes more aggressive near limit

# Ballast trick (pre-Go 1.19): allocate a large unused slice
// to increase the "live heap" baseline, delaying GC
var ballast = make([]byte, 1<<30)  // 1 GB
```

### 25.5 Python: Avoiding GC Overhead

CPython uses reference counting + cyclic GC. For latency-sensitive code:

```python
import gc

# Disable cyclic GC in hot sections (ref counting still works)
gc.disable()
process_hot_path()
gc.enable()
gc.collect()  # collect cycles after hot section
```

Or better: avoid creating reference cycles entirely (no circular references between objects).

---

## 26. Network Performance Optimization

### 26.1 TCP Tuning

```bash
# Increase socket buffer sizes
sysctl -w net.core.rmem_max=16777216       # 16 MB receive buffer
sysctl -w net.core.wmem_max=16777216       # 16 MB send buffer
sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"  # min default max
sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"

# Enable TCP Fast Open (saves 1 RTT on repeat connections)
sysctl -w net.ipv4.tcp_fastopen=3          # 1=client, 2=server, 3=both

# Increase connection backlog
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# Enable BBR congestion control (Google)
sysctl -w net.core.default_qdisc=fq
sysctl -w net.ipv4.tcp_congestion_control=bbr
```

### 26.2 HTTP/2 and HTTP/3

| Feature | HTTP/1.1 | HTTP/2 | HTTP/3 (QUIC) |
|---|---|---|---|
| Multiplexing | No (HOL blocking) | Yes (streams) | Yes (no HOL blocking) |
| Header compression | No | HPACK | QPACK |
| Transport | TCP | TCP | UDP + QUIC |
| Connection setup | 1 RTT (TCP) + 2 RTT (TLS) | Same as 1.1 | 0-1 RTT |
| Connection migration | No | No | Yes (connection ID) |

For inter-service communication: gRPC over HTTP/2 or HTTP/3 gives multiplexing, binary framing, and header compression.

### 26.3 Connection Reuse

```
Without keep-alive:
  Request 1: TCP handshake (1.5ms) + TLS (5ms) + request (2ms) = 8.5ms
  Request 2: TCP handshake (1.5ms) + TLS (5ms) + request (2ms) = 8.5ms
  10 requests = 85ms

With keep-alive (persistent connection):
  Request 1: TCP handshake (1.5ms) + TLS (5ms) + request (2ms) = 8.5ms
  Request 2: request (2ms)  ← reuses connection
  10 requests = 8.5 + 9 * 2 = 26.5ms (3.2x faster)
```

Always enable HTTP keep-alive for inter-service calls. Set `MaxIdleConnsPerHost` appropriately.

---

## 27. Compression Trade-offs

### 27.1 Algorithm Selection

| Algorithm | Compression Ratio | Speed (compress) | Speed (decompress) | Best For |
|---|---|---|---|---|
| **LZ4** | Low-medium | Very fast (> 500 MB/s) | Very fast (> 1 GB/s) | Real-time, inter-service |
| **Snappy** | Low-medium | Very fast | Very fast | Database pages, RPC |
| **Zstd** | High | Fast (> 200 MB/s) | Very fast (> 800 MB/s) | Storage, archival, HTTP |
| **gzip** | Medium | Moderate | Moderate | HTTP responses, legacy |
| **Brotli** | Very high | Slow | Fast | Static web assets |

**Rule:** For hot-path network traffic, use LZ4 or Snappy. For storage at rest, use Zstd. For static web assets, pre-compress with Brotli.

### 27.2 When NOT to Compress

- Already-compressed data (images, video, encrypted data).
- Payloads < 1 KB (compression overhead exceeds savings).
- Ultra-low-latency paths where even microseconds matter (raw binary protocol).

---

## 28. Amdahl's Law & Performance Limits

### 28.1 The Formula

```
Speedup = 1 / ((1 - P) + P/N)

P = fraction of work that is parallelizable
N = number of processors/cores

Example:
  90% parallelizable (P=0.9), 16 cores:
  Speedup = 1 / (0.1 + 0.9/16) = 1 / 0.15625 = 6.4x
  Not 16x! The 10% serial portion limits the speedup.

  Even with infinite cores:
  Speedup_max = 1 / (1 - P) = 1 / 0.1 = 10x
```

### 28.2 Implication

Optimizing the parallel part has diminishing returns. To get 2x speedup, you need P > 50%. To get 10x, you need P > 90%. **Identify and shrink the serial bottleneck first.**

### 28.3 Universal Scalability Law (USL)

Gunther's extension of Amdahl's Law that adds a *coherence penalty* (the cost of coordinating parallel work):

```
Throughput(N) = N / (1 + σ(N-1) + κN(N-1))

σ = contention parameter (serialization)
κ = coherence parameter (crosstalk/coordination)

When κ > 0, throughput eventually DECREASES with more cores.
This models lock contention, cache coherence, and network overhead.
```

The USL explains why adding more servers sometimes makes the system slower.

---

## Exercises

### Exercise 1: Detect and Fix False Sharing (Intermediate)

Write a multi-threaded counter benchmark that deliberately triggers false sharing, then fix it.

**Requirements:**
- Create a struct/class with two `long` counters that share a cache line (adjacent fields, no padding).
- Spawn two threads, each incrementing its own counter in a tight loop (100 million iterations).
- Measure elapsed time with and without false sharing.
- Fix by adding padding (e.g., `@Contended` in Java, `alignas(64)` in C++, or manual byte padding).
- Report the speedup ratio and verify using `perf stat` (or equivalent) that L1 cache miss rates drop after the fix.

### Exercise 2: Lock-Free Stack with CAS (Advanced)

Implement a Treiber stack (lock-free LIFO) using atomic compare-and-swap.

**Requirements:**
- Define a `Node<T>` with a value and a next pointer.
- Implement `push(T)` and `pop() -> Option<T>` using CAS on the head pointer.
- Handle the ABA problem (use a version counter or hazard pointers).
- Write a stress test: 8 threads, 4 producers and 4 consumers, 1 million operations each.
- Verify linearizability: all pushed items are popped exactly once, no duplicates, no losses.
- Benchmark against a `Mutex`-protected stack and report throughput (ops/sec) and p99 latency.

### Exercise 3: Disruptor-Style Pipeline (Advanced)

Build a single-producer, multi-consumer event processing pipeline using the ring buffer pattern.

**Requirements:**
- Implement a power-of-2 ring buffer with a sequence counter (no locks).
- Single producer writes events; three consumer stages read in dependency order (decode → process → persist).
- Each consumer tracks its own sequence; the producer must not overwrite slots still being read.
- Measure throughput (events/sec) and latency (ns per event) for 10 million events.
- Compare with a `BlockingQueue`-based pipeline and report the throughput ratio.

### Exercise 4: Profiling a Hot Path (Intermediate)

Given a provided (or self-written) JSON parsing workload, profile it and optimize for 2x throughput.

**Requirements:**
- Run the workload under a CPU profiler (`perf record` + `perf report`, async-profiler flame graph, or `pprof`).
- Identify the top 3 hottest functions and the percentage of CPU time each consumes.
- Apply at least two optimizations (e.g., reduce allocations, improve data locality, avoid virtual dispatch, use SIMD-friendly layout).
- Re-profile after each optimization and record the incremental improvement.
- Produce a before/after flame graph and a written summary of findings.

### Exercise 5: Amdahl's Law and USL Modeling (Intermediate)

Model the scalability of a web request pipeline that is 80% parallelizable.

**Requirements:**
- Calculate theoretical speedup for 1, 2, 4, 8, 16, 32, 64, and 128 cores using Amdahl's Law.
- Extend the model with the Universal Scalability Law: assume contention σ = 0.03 and coherence κ = 0.001.
- Plot both curves (Amdahl vs USL) on the same chart.
- Identify the point of diminishing returns and the point where USL throughput starts decreasing.
- Propose two architectural changes that would increase the parallelizable fraction P from 0.8 to 0.95.

---

## Readings and References

### Official Documentation (retrieved: 2026-05-29)

- LMAX Disruptor — Technical paper: https://lmax-exchange.github.io/disruptor/disruptor.html
- LMAX Disruptor — GitHub: https://lmax-exchange.github.io/disruptor/
- Mechanical Sympathy Blog (Martin Thompson) — https://mechanical-sympathy.blogspot.com/
- Single Writer Principle — https://mechanical-sympathy.blogspot.com/2011/09/single-writer-principle.html
- Lock-Based vs Lock-Free Concurrent Algorithms — https://mechanical-sympathy.blogspot.com/2013/08/lock-based-vs-lock-free-concurrent.html
- Linux `perf` wiki — https://perf.wiki.kernel.org/index.php/Main_Page
- async-profiler — https://github.com/async-profiler/async-profiler

### Books

- Gregg, B. *Systems Performance: Enterprise and the Cloud*, 2nd edition (Addison-Wesley, 2020). Comprehensive OS and hardware profiling methodology.
- Kleppmann, M. *Designing Data-Intensive Applications* (O'Reilly, 2017). Chapter 7 (transactions), Chapter 8 (distributed consistency).
- Herlihy, M., Shavit, N. *The Art of Multiprocessor Programming*, revised 1st edition (Morgan Kaufmann, 2012). Lock-free algorithms and concurrent data structures.
- Drepper, U. "What Every Programmer Should Know About Memory." Red Hat Inc. (2007). https://people.freebsd.org/~lstewart/articles/cpumemory.pdf
- Hennessy, J.L., Patterson, D.A. *Computer Architecture: A Quantitative Approach*, 6th edition (Morgan Kaufmann, 2017). Cache hierarchy, pipelining, NUMA.

### Papers and Articles

- Thompson, M. "Mechanical Sympathy" (SE Radio Episode 201, 2014). https://se-radio.net/2014/02/episode-201-martin-thompson-on-mechanical-sympathy/
- Gunther, N.J. "A General Theory of Computational Scalability Based on Rational Functions." *arXiv:0808.1431* (2008).
- Fowler, M. "The LMAX Architecture" (2011). https://martinfowler.com/articles/lmax.html

---

## Cross-References

| Topic | Module | File |
|---|---|---|
| Distributed system patterns (saga, outbox, tracing) | 2.2 | `02_Distributed_System_Patterns.md` |
| API design and inter-service latency budgets | 2.2c | `02_c_API_Design_Evolution.md` |
| Code-level architecture (hexagonal, clean) | 2.1 | `01_Code_Level_Architecture.md` |
| SOLID principles and separation of concerns | 2.3 | `03_Design_Principles_SOLID_etc.md` |
| CAP / PACELC and consistency-latency trade-offs | 2.4 | `04_System_Design_CAP_PACELC.md` |
| Database indexing, query optimization, and storage engines | — | `03_Database_Engineering/` |

---

## Glossary

| Term | Definition |
|---|---|
| **Mechanical Sympathy** | Writing software that works in harmony with the underlying hardware — CPU caches, memory buses, branch predictors — to maximize performance. |
| **False Sharing** | A performance pathology where threads on different cores modify independent variables that reside on the same cache line, causing excessive cache-coherence traffic. |
| **Cache Line** | The smallest unit of data transfer between main memory and CPU cache, typically 64 bytes on modern x86 processors. |
| **CAS (Compare-and-Swap)** | An atomic CPU instruction that updates a memory location only if its current value matches an expected value; the foundation of most lock-free algorithms. |
| **Lock-Free** | A progress guarantee meaning that at least one thread makes forward progress in a finite number of steps, even if other threads stall. |
| **Wait-Free** | A stronger progress guarantee than lock-free: every thread completes its operation in a bounded number of steps. |
| **Ring Buffer** | A fixed-size circular array where producers and consumers advance sequence counters instead of allocating or deallocating memory. |
| **Disruptor** | A high-performance inter-thread messaging library created by LMAX Exchange that uses a ring buffer, sequence barriers, and the single-writer principle to achieve sub-microsecond latency. |
| **NUMA** | Non-Uniform Memory Access — an architecture where memory access latency depends on which CPU socket the memory is attached to. |
| **Zero-Copy** | A technique that moves data between kernel and user space (or between network and disk) without copying it through intermediate buffers (e.g., `sendfile`, `mmap`). |
| **Amdahl's Law** | A formula that models the theoretical speedup of a workload as a function of the parallelizable fraction and the number of processors. |
| **USL (Universal Scalability Law)** | Neil Gunther's extension of Amdahl's Law that adds a coherence penalty to model throughput degradation under coordination overhead. |
| **Hot Path** | The code path executed most frequently in a system — the primary target for performance optimization. |
| **Backpressure** | A flow-control mechanism where a consumer signals the producer to reduce its emission rate when the consumer cannot keep up. |

---

*End of Module 2.2b*
