# Module 6.1: Backend Concurrency Models

> **Module 06.1** · **Last updated:** 2026-05-22

## Guiding ideas

1. **Threads (Java) vs goroutines (Go) vs async/await (Python/JS) vs actors (Erlang).**
2. **Structured concurrency: scope-bound, no orphan task.**
3. **Backpressure mandatory for data pipeline.**
4. **Avoid shared mutable state; message passing > locks.**
5. **Work stealing balances load across processors.**
6. **Every concurrency model trades off between throughput, latency, and complexity.**

---

## Table of Contents

1. [Foundational Concepts](#1-foundational-concepts)
2. [Threads vs Processes vs Async](#2-threads-vs-processes-vs-async)
3. [Node.js: The Event Loop & Libuv](#3-nodejs-the-event-loop--libuv)
4. [Python: asyncio and the GIL](#4-python-asyncio-and-the-gil)
5. [Go: The M:N Scheduler](#5-go-the-mn-scheduler)
6. [Java: Virtual Threads (Project Loom)](#6-java-virtual-threads-project-loom)
7. [Actor Model: Erlang/Elixir and Akka](#7-actor-model-erlangelixir-and-akka)
8. [CSP: Communicating Sequential Processes](#8-csp-communicating-sequential-processes)
9. [Thread Pools and Work Stealing](#9-thread-pools-and-work-stealing)
10. [Backpressure](#10-backpressure)
11. [Structured Concurrency](#11-structured-concurrency)
12. [Synchronization Primitives](#12-synchronization-primitives)
13. [Lock-Free and Wait-Free Data Structures](#13-lock-free-and-wait-free-data-structures)
14. [Concurrency Patterns](#14-concurrency-patterns)
15. [Debugging Concurrency Issues](#15-debugging-concurrency-issues)
16. [Benchmarking and Performance](#16-benchmarking-and-performance)
17. [Choosing a Concurrency Model](#17-choosing-a-concurrency-model)
18. [Exercises](#18-exercises)
19. [References](#19-references)

---

## 1. Foundational Concepts

### 1.1 Concurrency vs Parallelism

**Concurrency:** Dealing with many things at once (structure).
**Parallelism:** Doing many things at once (execution).

Rob Pike's distinction: concurrency is about composition of independently
executing processes. Parallelism is about simultaneous execution. You can have
concurrency without parallelism (single-core CPU with context switching) and
parallelism without concurrency (SIMD instruction on a vector).

```
Concurrency (interleaved, possibly on 1 core):
  Task A: ──▓▓░░▓▓░░▓▓──
  Task B: ──░░▓▓░░▓▓░░──

Parallelism (simultaneous, requires multiple cores):
  Core 1: ──▓▓▓▓▓▓▓▓▓▓──  Task A
  Core 2: ──▓▓▓▓▓▓▓▓▓▓──  Task B
```

### 1.2 CPU-Bound vs I/O-Bound

| Type | Bottleneck | Example | Best approach |
|---|---|---|---|
| **CPU-bound** | Compute cycles | Image processing, compression, crypto | Parallelism (multiple cores) |
| **I/O-bound** | Waiting for external resource | HTTP requests, DB queries, file reads | Concurrency (async, non-blocking) |
| **Mixed** | Both | Web server processing requests with business logic | Combination |

This distinction drives every concurrency design decision. Running 10,000
goroutines for CPU-bound work on an 8-core machine gives you concurrency but
not more parallelism — you still only have 8 cores of throughput. Running
10,000 goroutines for I/O-bound work is excellent because each goroutine
spends most of its time waiting, and the scheduler can use those 8 cores
efficiently across all 10,000.

### 1.3 The C10K and C10M Problems

**C10K (1999, Dan Kegel):** How to handle 10,000 simultaneous connections
on a single server. Solved by event-driven architectures (epoll, kqueue,
IOCP) instead of thread-per-connection.

**C10M (2010+):** 10 million simultaneous connections. Requires kernel
bypass (DPDK, io_uring), zero-copy networking, and careful memory management.

### 1.4 Amdahl's Law

Speedup from parallelism is limited by the sequential portion of the program:

```
Speedup = 1 / (S + P/N)

S = fraction that is sequential (cannot be parallelized)
P = fraction that is parallelizable (P = 1 - S)
N = number of processors

Example:
  5% sequential → max speedup with infinite cores = 1/0.05 = 20x
  50% sequential → max speedup with infinite cores = 1/0.50 = 2x
```

Implication: before parallelizing, profile to find what percentage of execution
time is genuinely parallelizable. If the sequential portion is large, no amount
of cores will help.

---

## 2. Threads vs Processes vs Async

### 2.1 OS Threads (1:1 Model)

Each user-level thread maps to one OS/kernel thread.

```
User code          Kernel
┌──────┐          ┌──────┐
│Thread1│ ←──1:1──→│KThread1│
│Thread2│ ←──1:1──→│KThread2│
│Thread3│ ←──1:1──→│KThread3│
└──────┘          └──────┘
```

**Characteristics:**
- Stack size: typically 1-8 MB per thread (configurable).
- Context switch cost: ~1-10 microseconds (save/restore registers, TLB flush).
- Creation cost: ~50-100 microseconds.
- Practical limit: ~10,000 threads per process before memory pressure.
- Scheduling: preemptive (OS decides when to switch).
- Shared memory: threads in same process share heap.

**Languages:** C, C++, Java (platform threads), Rust, C#.

### 2.2 OS Processes

Each process has its own address space. No shared memory by default.

**Characteristics:**
- Isolation: crash in one process doesn't affect others.
- Memory: separate heap per process.
- Communication: IPC (pipes, sockets, shared memory segments, message queues).
- Context switch cost: higher than threads (full address space switch, TLB flush).
- Fork cost: depends on COW (copy-on-write) behavior.

**When to use:**
- Fault isolation (one worker crash shouldn't kill the server).
- CPU-bound work in languages with GIL (Python, Ruby).
- Security isolation (different privilege levels).

### 2.3 Green Threads / User-Space Threads (M:N Model)

M user-level threads multiplexed onto N OS threads, where M >> N.

```
User code                    Kernel
┌──────────────────┐        ┌──────┐
│ Green1 Green2    │        │      │
│ Green3 Green4  ──┼──M:N──→│KThread1│
│ Green5 Green6    │        │KThread2│
│ Green7 Green8    │        │      │
└──────────────────┘        └──────┘
```

**Characteristics:**
- Stack size: 2-8 KB (goroutines start at 2 KB, grow dynamically).
- Context switch cost: ~100-500 nanoseconds (user-space scheduler).
- Creation cost: ~1-3 microseconds.
- Practical limit: millions per process.
- Scheduling: cooperative or hybrid (Go uses cooperative + preemptive since 1.14).

**Languages:** Go (goroutines), Erlang (processes), Java 21+ (virtual threads).

### 2.4 Async/Await (Event-Driven)

Single thread with an event loop. I/O operations register callbacks; the
event loop dispatches results when they arrive.

```
Single Thread
┌─────────────────────────────────────┐
│  Event Loop                         │
│  ┌─ Poll for I/O completions ──┐   │
│  │  ┌─ Run ready callbacks ──┐ │   │
│  │  │  ┌─ Check timers ──┐  │ │   │
│  │  │  └─────────────────┘  │ │   │
│  │  └───────────────────────┘ │   │
│  └────────────────────────────┘   │
└─────────────────────────────────────┘
```

**Characteristics:**
- No thread creation overhead for I/O.
- No locks needed (single-threaded).
- CPU-bound work blocks the entire loop.
- "Colored function" problem: async functions can only be called from async
  contexts (except in Go, which hides this entirely).

**Languages:** JavaScript/Node.js, Python (asyncio), Rust (tokio), C# (TAP).

### 2.5 Comparison Table

| Aspect | OS Threads | Processes | Green Threads | Async/Await |
|---|---|---|---|---|
| Memory per unit | 1-8 MB | 10+ MB | 2-8 KB | ~0 (state machine) |
| Max practical units | ~10K | ~1K | ~1M+ | ~1M+ |
| Context switch | ~1-10 µs | ~10-100 µs | ~0.1-0.5 µs | ~0 (no switch) |
| Shared state | Yes (same heap) | No (IPC needed) | Yes (same heap) | Yes (same heap) |
| CPU-bound scaling | Good | Good | Good | Bad (blocks loop) |
| I/O-bound scaling | Moderate | Moderate | Excellent | Excellent |
| Debugging | Thread dumps | Process isolation | Runtime-specific | Stack traces harder |
| Preemption | OS preemptive | OS preemptive | Varies | Cooperative |

---

## 3. Node.js: The Event Loop & Libuv

JavaScript is single-threaded, but Node.js handles hundreds of thousands of
concurrent connections. The trick: asynchronous non-blocking I/O.

### 3.1 The Engine: Libuv

Libuv is a C library that provides:
- The event loop implementation.
- A thread pool (default 4 threads, configurable via `UV_THREADPOOL_SIZE`) for
  operations that don't have OS-level async support (DNS, filesystem on some
  platforms, crypto, zlib).
- Cross-platform abstraction over OS async primitives (epoll on Linux, kqueue
  on macOS/BSD, IOCP on Windows).

**How offloading works:**
```
JS Thread                    Libuv Thread Pool
    │                              │
    │  fs.readFile('data.txt')     │
    │ ─────────────────────────→   │  Thread 1: read()
    │  (returns immediately)       │
    │                              │
    │  ... executes other JS ...   │
    │                              │
    │  ←─────────────────────────  │  Read complete
    │  Callback pushed to queue    │
    │                              │
    │  Event loop picks it up      │
    │  Executes callback           │
```

**Network I/O is different:** TCP/UDP connections use OS-level non-blocking I/O
(epoll_wait) directly on the event loop thread — no thread pool needed. This is
why Node.js handles network I/O so efficiently.

### 3.2 The Event Loop Phases (Macrotasks)

```
   ┌───────────────────────────┐
┌─→│         timers            │  setTimeout, setInterval
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │     pending callbacks     │  System-level errors (TCP errors)
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │       idle, prepare       │  Internal use only
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │          poll              │  Retrieve new I/O events
│  │  (blocks here if idle)    │  Execute I/O callbacks
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │          check            │  setImmediate callbacks
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │     close callbacks       │  socket.on('close')
│  └─────────────┬─────────────┘
└─────────────────┘
```

**The Poll Phase** is the core. When the event loop reaches poll:
1. If the poll queue is non-empty, execute callbacks synchronously until the
   queue is drained or the system-dependent hard limit is reached.
2. If the poll queue is empty:
   - If `setImmediate` callbacks are scheduled, move to check phase.
   - If timers are due, wrap back to timers phase.
   - Otherwise, block and wait for new I/O events.

### 3.3 The Microtask Queue (The VIP Lane)

Microtasks are processed **between every phase** of the event loop, and after
every individual macrotask callback.

**Priority order:**
1. `process.nextTick()` — highest priority microtask. Runs immediately after
   the current operation completes, before any I/O.
2. Promise callbacks (`.then()`, `await` continuations) — after nextTick.

```javascript
setTimeout(() => console.log('1: timeout'), 0);
setImmediate(() => console.log('2: immediate'));
process.nextTick(() => console.log('3: nextTick'));
Promise.resolve().then(() => console.log('4: promise'));

// Output:
// 3: nextTick
// 4: promise
// 1: timeout  (or 2: immediate — order between these depends on poll state)
// 2: immediate (or 1: timeout)
```

**Danger:** An infinite loop of `process.nextTick()` starves the I/O loop:

```javascript
// This will never process I/O:
function recursive() {
  process.nextTick(recursive);
}
recursive();
// Event loop never advances past microtask queue
```

### 3.4 Worker Threads

Node.js is single-threaded for JS execution, but `worker_threads` provides
real OS threads for CPU-bound work:

```javascript
// main.js
import { Worker, isMainThread, parentPort } from 'worker_threads';

if (isMainThread) {
  const worker = new Worker(new URL(import.meta.url));
  worker.on('message', (result) => {
    console.log(`Fibonacci result: ${result}`);
  });
  worker.postMessage(42);
} else {
  parentPort.on('message', (n) => {
    // CPU-bound work runs on a separate OS thread
    const result = fibonacci(n);
    parentPort.postMessage(result);
  });
}

function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}
```

**When to use worker_threads:**
- CPU-bound computation (image processing, crypto, data transformation).
- Never for I/O — the event loop already handles I/O efficiently.
- Consider thread pools (`workerpool`, Piscina) for managing worker lifecycle.

### 3.5 Cluster Module

For utilizing multiple CPU cores with the same server:

```javascript
import cluster from 'cluster';
import http from 'http';
import os from 'os';

if (cluster.isPrimary) {
  const numCPUs = os.cpus().length;
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }
  cluster.on('exit', (worker) => {
    console.log(`Worker ${worker.process.pid} died, restarting`);
    cluster.fork();
  });
} else {
  http.createServer((req, res) => {
    res.writeHead(200);
    res.end('Hello from worker ' + process.pid);
  }).listen(8000);
}
```

Each worker is a separate OS process with its own event loop and memory space.
The primary process distributes incoming connections across workers.

---

## 4. Python: asyncio and the GIL

### 4.1 The GIL (Global Interpreter Lock)

CPython has a global lock that prevents multiple native threads from executing
Python bytecode simultaneously. Only one thread runs Python code at a time.

```
Thread 1:  ──▓▓▓▓░░░░▓▓▓▓░░░░──
Thread 2:  ──░░░░▓▓▓▓░░░░▓▓▓▓──
                                     (interleaved, never parallel)
```

**Implications:**
- CPU-bound multithreading in Python gives ~zero speedup (often slower due to
  lock contention).
- I/O-bound multithreading works fine — threads release the GIL during I/O waits.
- CPU-bound parallelism requires `multiprocessing` (separate processes, separate
  GILs) or C extensions that release the GIL (NumPy, OpenCV).

**Python 3.13+ (free-threaded CPython):** Experimental `--disable-gil` build
removes the GIL. Not yet production-ready but the future direction.

### 4.2 asyncio Event Loop

```python
import asyncio
import aiohttp

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def main():
    urls = [f"https://httpbin.org/get?id={i}" for i in range(100)]

    async with aiohttp.ClientSession() as session:
        # Launch all 100 requests concurrently
        tasks = [fetch_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        print(f"Fetched {len(results)} pages")

asyncio.run(main())
```

**How asyncio works internally:**
1. `async def` creates a coroutine (a state machine, not a thread).
2. `await` yields control back to the event loop.
3. The event loop monitors file descriptors (epoll/kqueue) for I/O readiness.
4. When I/O completes, the event loop resumes the coroutine.
5. Everything runs on a single thread.

### 4.3 The Colored Function Problem

```python
# Synchronous function
def get_user(user_id: int) -> User:
    return db.query(User, user_id)  # blocks the thread

# Async function — different "color"
async def get_user(user_id: int) -> User:
    return await db.query(User, user_id)  # yields to event loop

# Problem: you can't call async from sync without ceremony
# sync_function() cannot just call await async_function()
# You need asyncio.run() or loop.run_until_complete()
```

This "function coloring" forces async to propagate upward through the call
stack. Go avoids this entirely — all goroutine I/O is async under the hood,
but the API is synchronous.

### 4.4 multiprocessing for CPU-Bound Work

```python
from multiprocessing import Pool
import math

def compute_heavy(n):
    """CPU-bound work: compute sum of primes up to n."""
    return sum(1 for i in range(2, n) if all(i % j != 0 for j in range(2, int(math.sqrt(i)) + 1)))

if __name__ == '__main__':
    with Pool(processes=8) as pool:
        inputs = [100_000] * 8
        results = pool.map(compute_heavy, inputs)
        print(f"Results: {results}")
```

**Trade-offs:**
- Each process has its own Python interpreter and memory space.
- Data must be serialized (pickle) to pass between processes — expensive for
  large objects.
- Process creation is expensive (~50-100ms on Linux, worse on Windows).
- Use process pools, not fresh processes per task.

### 4.5 concurrent.futures (Unified Interface)

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import asyncio

# Thread pool for I/O-bound work
def fetch_sync(url):
    import urllib.request
    return urllib.request.urlopen(url).read()

with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(fetch_sync, f"https://example.com/{i}") for i in range(100)]
    results = [f.result() for f in futures]

# Process pool for CPU-bound work
with ProcessPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(compute_heavy, 100_000) for _ in range(8)]
    results = [f.result() for f in futures]

# Mixing async + thread pool
async def main():
    loop = asyncio.get_event_loop()
    # Run blocking function in thread pool without blocking the event loop
    result = await loop.run_in_executor(None, fetch_sync, "https://example.com")
```

### 4.6 uvloop

Drop-in replacement for asyncio's default event loop, implemented in Cython
on top of libuv. 2-4x faster than the default event loop.

```python
import uvloop
import asyncio

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
# or in Python 3.12+:
# asyncio.run(main(), loop_factory=uvloop.new_event_loop)
```

---

## 5. Go: The M:N Scheduler

Go uses an M:N threading model: M goroutines multiplexed onto N OS threads.

### 5.1 The G-M-P Model

```
         ┌─────────────────────────────────────┐
         │          Go Runtime Scheduler         │
         │                                       │
         │  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐      │
         │  │ G │ │ G │ │ G │ │ G │ │ G │ ...  │  G = Goroutine (2KB stack)
         │  └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘ └─┬─┘      │
         │    │     │     │     │     │          │
         │  ┌─┴─────┴─┐ ┌─┴─────┴─┐ ┌─┴─┐      │
         │  │    P     │ │    P     │ │ P │      │  P = Processor (logical CPU)
         │  │Local Run │ │Local Run │ │   │      │    has local run queue
         │  │  Queue   │ │  Queue   │ │   │      │
         │  └─────┬────┘ └─────┬────┘ └─┬─┘      │
         │        │            │        │          │
         │  ┌─────┴──┐  ┌─────┴──┐  ┌──┴────┐   │
         │  │   M    │  │   M    │  │   M   │   │  M = Machine (OS Thread)
         │  └────────┘  └────────┘  └───────┘   │
         └─────────────────────────────────────┘
                    │            │         │
              ┌─────┴──┐  ┌─────┴──┐ ┌────┴───┐
              │CPU Core│  │CPU Core│ │CPU Core│
              └────────┘  └────────┘ └────────┘
```

**G (Goroutine):** 2 KB initial stack (grows dynamically up to 1 GB). The unit
of concurrent execution. Lightweight enough to spawn millions.

**M (Machine):** An OS thread. Heavy (~8 MB stack). The runtime creates as many
as needed (default max: 10,000, configurable via `GOMAXPROCS` for P count, and
`runtime/debug.SetMaxThreads` for M count).

**P (Processor):** A logical processor. Each P has a local run queue of
goroutines. The number of Ps = `GOMAXPROCS` (defaults to number of CPU cores).

### 5.2 Scheduling Algorithm

1. When a goroutine is created (`go func()`), it's placed on the current P's
   local run queue.
2. The P picks goroutines from its local queue and runs them on its attached M.
3. When a goroutine blocks on I/O (syscall), the M is detached from the P, and
   a new M is assigned to the P so other goroutines can continue.
4. When a goroutine blocks on a channel or mutex (not a syscall), it is parked
   (no M wasted).

### 5.3 Work Stealing

If a P's local run queue is empty:
1. Check the global run queue (with 1/61 probability, to avoid starvation).
2. Steal half the goroutines from another P's local run queue.
3. Check the network poller (goroutines waiting on I/O that just became ready).

```
P0: [G1, G2, G3, G4]    P1: []    P2: [G5]
                              │
                     Work stealing
                              │
P0: [G1, G2]          P1: [G3, G4]   P2: [G5]
```

Result: all cores stay utilized. No goroutine starves as long as some P has work.

### 5.4 Preemption (Since Go 1.14)

Before Go 1.14, goroutines were only preempted at function call boundaries
(cooperative scheduling). A tight loop with no function calls would never yield:

```go
// Pre-1.14: this goroutine monopolizes its P forever
go func() {
    for {
        // tight loop, no function calls, no I/O
        x++
    }
}()
```

Since Go 1.14: asynchronous preemption via OS signals (SIGURG on Linux). The
runtime can interrupt a goroutine mid-execution. This prevents single-goroutine
starvation.

### 5.5 Goroutine Lifecycle and Memory

```go
func main() {
    // Spawning a goroutine: ~1-3 µs, 2 KB stack
    go worker()

    // Stack growth: when a goroutine needs more stack:
    // 1. Runtime allocates a new, larger stack (2x)
    // 2. Copies the old stack contents to the new stack
    // 3. Updates all pointers
    // 4. Frees the old stack
    // This is called "stack copying" or "segmented stacks" (Go uses copying since 1.4)
}
```

### 5.6 Channels

Channels are Go's primary synchronization mechanism (CSP model):

```go
// Unbuffered channel: sender blocks until receiver is ready
ch := make(chan int)

// Buffered channel: sender blocks only when buffer is full
ch := make(chan int, 100)

// Select: multiplex across channels
select {
case msg := <-inbound:
    process(msg)
case outbound <- result:
    // sent
case <-time.After(5 * time.Second):
    // timeout
case <-ctx.Done():
    // cancellation
}
```

### 5.7 Common Go Concurrency Patterns

```go
// Fan-out / Fan-in
func fanOutFanIn(input <-chan Job) <-chan Result {
    numWorkers := runtime.NumCPU()
    results := make([]<-chan Result, numWorkers)

    // Fan-out: distribute work across workers
    for i := 0; i < numWorkers; i++ {
        results[i] = worker(input)
    }

    // Fan-in: merge results into single channel
    return merge(results...)
}

// Pipeline
func pipeline(input <-chan int) <-chan int {
    doubled := stage(input, func(n int) int { return n * 2 })
    filtered := filter(doubled, func(n int) bool { return n > 10 })
    return filtered
}

// Context-based cancellation
func longRunningOp(ctx context.Context) error {
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()  // Cancelled or deadline exceeded
        default:
            // do work
        }
    }
}
```

---

## 6. Java: Virtual Threads (Project Loom)

### 6.1 The Problem

Traditional Java used 1 OS thread per request (thread-per-request model). Each
thread consumes ~1 MB of stack memory. At 10,000 concurrent requests, that is
10 GB of stack memory alone, plus scheduling overhead. This is the C10K problem.

Reactive frameworks (Spring WebFlux, Vert.x) solved this but at the cost of
readability — callback chains and reactive streams replace simple sequential code.

### 6.2 Virtual Threads (Since Java 21)

Virtual threads are lightweight threads managed by the JVM, not the OS. Millions
of virtual threads map to a small number of OS "carrier threads."

```java
// Traditional: OS thread per task
try (var executor = Executors.newFixedThreadPool(200)) {
    for (int i = 0; i < 100_000; i++) {
        executor.submit(() -> {
            // This blocks an OS thread during the DB call
            var user = repository.findById(userId);
            return processUser(user);
        });
    }
}

// Virtual threads: same blocking code, but lightweight
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    for (int i = 0; i < 100_000; i++) {
        executor.submit(() -> {
            // This blocks a virtual thread, NOT an OS thread
            var user = repository.findById(userId);
            return processUser(user);
        });
    }
}
```

### 6.3 How Virtual Threads Work

```
Virtual Thread 1 ─→ ┐
Virtual Thread 2 ─→ ├── Carrier Thread 1 (OS Thread)
Virtual Thread 3 ─→ ┘
                         When VT blocks on I/O:
Virtual Thread 4 ─→ ┐     1. JVM copies VT stack to heap (Continuation)
Virtual Thread 5 ─→ ├── Carrier Thread 2 (OS Thread)
Virtual Thread 6 ─→ ┘     2. Carrier thread picks up next VT
                           3. When I/O completes, VT is re-mounted
                              on any available carrier thread
```

**Mounting/Unmounting:**
1. Virtual thread calls blocking I/O (e.g., `Socket.read()`).
2. JVM detects the blocking call, saves the virtual thread's stack to heap
   as a Continuation object.
3. The carrier thread is freed to run another virtual thread.
4. When I/O completes, the virtual thread is scheduled on any available carrier.
5. The stack is restored (mounted) from the heap Continuation.

**Key insight:** You write simple, sequential, blocking-style code
(`user = repo.findById(id)`), but get async-level scalability. No reactive
streams, no callback hell, no colored functions.

### 6.4 Pinning (The Gotcha)

Virtual threads get "pinned" to their carrier thread in two cases:
1. Inside a `synchronized` block or method.
2. During a native method call (JNI).

When pinned, the carrier thread is blocked and cannot serve other virtual
threads. This defeats the purpose.

```java
// BAD: synchronized pins the virtual thread to its carrier
synchronized (lock) {
    var data = db.query(...);  // Carrier thread blocked during I/O
}

// GOOD: use ReentrantLock instead
lock.lock();
try {
    var data = db.query(...);  // Virtual thread unmounts; carrier is freed
} finally {
    lock.unlock();
}
```

**Detection:** Run with `-Djdk.tracePinnedThreads=full` to log pinning events.

### 6.5 Structured Concurrency (Preview)

```java
// Java structured concurrency (preview in Java 21+)
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Subtask<User> userTask = scope.fork(() -> fetchUser(userId));
    Subtask<Order> orderTask = scope.fork(() -> fetchOrder(orderId));

    scope.join();           // Wait for both
    scope.throwIfFailed();  // Propagate exceptions

    return new UserOrder(userTask.get(), orderTask.get());
}
// If fetchUser() fails, fetchOrder() is automatically cancelled
// No orphan tasks, no leaked threads
```

---

## 7. Actor Model: Erlang/Elixir and Akka

### 7.1 Core Principles

The actor model (Carl Hewitt, 1973) treats actors as the fundamental unit of
computation. Each actor:

1. Has private state (no shared memory).
2. Communicates exclusively via asynchronous messages.
3. Processes one message at a time (sequential within an actor).
4. Can create new actors.
5. Can send messages to other actors.
6. Can change its own state/behavior for the next message.

```
      ┌──────────┐    message    ┌──────────┐
      │  Actor A  │ ────────────→│  Actor B  │
      │           │              │           │
      │ state: {} │              │ state: {} │
      │ mailbox:  │              │ mailbox:  │
      │  [msg1]   │              │  [msg2,   │
      │           │              │   msg3]   │
      └──────────┘              └──────────┘
           │                         │
           │  message                │  message
           ▼                         ▼
      ┌──────────┐              ┌──────────┐
      │  Actor C  │              │  Actor D  │
      └──────────┘              └──────────┘
```

### 7.2 Erlang/OTP (BEAM VM)

Erlang was designed at Ericsson for telecom switches requiring 99.999% uptime.
The BEAM VM is purpose-built for massive concurrency.

**Erlang process characteristics:**
- Extremely lightweight: ~300 bytes initial memory.
- Preemptive scheduling: each process gets a fixed number of reductions
  (~2000 function calls), then yields.
- No shared memory between processes — all communication via message passing.
- Per-process garbage collection: no global GC pauses.
- Location transparent: sending a message to a process on another node uses
  the same syntax.

```erlang
%% Spawn a process
Pid = spawn(fun() ->
    loop(initial_state)
end),

%% Send a message
Pid ! {request, self(), "hello"},

%% Receive in the actor
loop(State) ->
    receive
        {request, From, Msg} ->
            NewState = handle(State, Msg),
            From ! {response, NewState},
            loop(NewState);
        stop ->
            ok
    end.
```

### 7.3 OTP Supervision Trees

OTP's supervisor model is the core of Erlang's fault tolerance:

```
           ┌─────────────┐
           │  Supervisor  │
           │ (restart     │
           │  strategy)   │
           └──┬────┬────┬─┘
              │    │    │
         ┌────┘    │    └────┐
         ▼         ▼         ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │Worker 1│ │Worker 2│ │  Sub-  │
    │        │ │        │ │Superv. │
    └────────┘ └────────┘ └──┬──┬──┘
                             │  │
                         ┌───┘  └───┐
                         ▼          ▼
                    ┌────────┐ ┌────────┐
                    │Worker 3│ │Worker 4│
                    └────────┘ └────────┘
```

**Restart strategies:**
- `one_for_one`: If a child dies, restart only that child.
- `one_for_all`: If any child dies, restart all children.
- `rest_for_one`: If a child dies, restart it and all children started after it.

**Philosophy:** "Let it crash." Instead of defensive programming with try/catch
everywhere, let processes crash when they encounter unexpected state. The
supervisor restarts them in a known-good state.

### 7.4 Elixir

Elixir runs on the BEAM VM but provides modern syntax and tooling:

```elixir
defmodule Counter do
  use GenServer

  # Client API
  def start_link(initial \\ 0) do
    GenServer.start_link(__MODULE__, initial, name: __MODULE__)
  end

  def increment, do: GenServer.cast(__MODULE__, :increment)
  def get_count, do: GenServer.call(__MODULE__, :get)

  # Server callbacks
  @impl true
  def init(count), do: {:ok, count}

  @impl true
  def handle_cast(:increment, count), do: {:noreply, count + 1}

  @impl true
  def handle_call(:get, _from, count), do: {:reply, count, count}
end
```

### 7.5 Akka (JVM)

Akka brings the actor model to the JVM (Scala/Java):

```scala
// Akka Typed (modern API)
object Counter {
  sealed trait Command
  case object Increment extends Command
  case class GetCount(replyTo: ActorRef[Int]) extends Command

  def apply(): Behavior[Command] = counter(0)

  private def counter(count: Int): Behavior[Command] =
    Behaviors.receive { (context, message) =>
      message match {
        case Increment =>
          counter(count + 1)
        case GetCount(replyTo) =>
          replyTo ! count
          Behaviors.same
      }
    }
}

// Create and use
val counterRef = context.spawn(Counter(), "myCounter")
counterRef ! Counter.Increment
```

**Akka Cluster:** Actors distributed across JVM nodes. Location transparency —
sending a message to a remote actor looks identical to a local actor. Cluster
sharding distributes actors across nodes by entity ID.

---

## 8. CSP: Communicating Sequential Processes

### 8.1 Theory (Hoare, 1978)

CSP models concurrent processes that communicate through channels. The key
difference from actors:

| Aspect | Actor Model | CSP |
|---|---|---|
| Communication | Direct (actor-to-actor messages) | Via named channels |
| Identity | Actors have identity (address) | Processes are anonymous |
| Coupling | Sender must know receiver | Both sides know the channel |
| Channels | Implicit (mailbox per actor) | Explicit, typed |
| Blocking | Async send (never blocks) | Synchronous send (blocks until received) |

### 8.2 Go Channels (CSP in Practice)

Go implements CSP with channels:

```go
// Producer-Consumer via channels
func producer(out chan<- int) {
    for i := 0; i < 100; i++ {
        out <- i  // blocks until consumer reads
    }
    close(out)
}

func consumer(in <-chan int) {
    for val := range in {
        fmt.Println(val)
    }
}

func main() {
    ch := make(chan int, 10)  // buffered channel
    go producer(ch)
    consumer(ch)
}
```

### 8.3 Clojure core.async

CSP-style channels in Clojure:

```clojure
(require '[clojure.core.async :as async :refer [<! >! go chan]])

(let [ch (chan 10)]
  ;; Producer goroutine
  (go
    (doseq [i (range 100)]
      (>! ch i))
    (async/close! ch))

  ;; Consumer goroutine
  (go
    (loop []
      (when-let [val (<! ch)]
        (println val)
        (recur)))))
```

### 8.4 Kotlin Channels and Flows

```kotlin
import kotlinx.coroutines.*
import kotlinx.coroutines.channels.*

fun CoroutineScope.produceNumbers(): ReceiveChannel<Int> = produce {
    for (i in 1..100) {
        send(i)
        delay(100)  // simulate work
    }
}

fun main() = runBlocking {
    val numbers = produceNumbers()
    for (num in numbers) {
        println(num)
    }
}
```

---

## 9. Thread Pools and Work Stealing

### 9.1 Thread Pool Fundamentals

A thread pool pre-creates a set of worker threads. Tasks are submitted to a
queue; idle workers pull tasks from the queue.

```
                    ┌──────────────────┐
  submit(task) ───→ │   Task Queue     │
                    │ [T1, T2, T3, T4] │
                    └────┬───┬───┬─────┘
                         │   │   │
                    ┌────┘   │   └────┐
                    ▼        ▼        ▼
               ┌────────┐┌────────┐┌────────┐
               │Thread 1││Thread 2││Thread 3│
               │ (busy) ││ (idle) ││ (busy) │
               └────────┘└────────┘└────────┘
```

**Sizing guidelines:**
- **CPU-bound:** `pool_size = num_cores` (or `num_cores + 1` to account for
  occasional page faults).
- **I/O-bound:** `pool_size = num_cores * (1 + wait_time / compute_time)`.
  If tasks spend 90% waiting: `8 * (1 + 9) = 80 threads`.
- **Mixed:** Separate pools for CPU-bound and I/O-bound work to prevent
  I/O-bound tasks from monopolizing threads needed for compute.

### 9.2 Java Thread Pools

```java
// Fixed pool: known concurrency level
var pool = Executors.newFixedThreadPool(Runtime.getRuntime().availableProcessors());

// Cached pool: dynamic sizing (dangerous for CPU-bound — can create too many threads)
var pool = Executors.newCachedThreadPool();

// Custom pool with bounded queue and rejection policy
var pool = new ThreadPoolExecutor(
    8,                      // core pool size
    32,                     // max pool size
    60, TimeUnit.SECONDS,   // keepalive for idle threads
    new ArrayBlockingQueue<>(1000),  // bounded queue
    new ThreadPoolExecutor.CallerRunsPolicy()  // rejection: caller executes
);

// ForkJoinPool: work-stealing pool (used for parallel streams, CompletableFuture)
var pool = new ForkJoinPool(Runtime.getRuntime().availableProcessors());
```

### 9.3 Work Stealing

In a traditional thread pool, all workers share a single queue. Contention on
the queue becomes a bottleneck.

Work stealing uses per-worker deques (double-ended queues):

```
Worker 1 deque: [T1, T2, T3] ← push/pop from this end (LIFO)
                          T3  → steal from this end (FIFO)

Worker 2 deque: []  ← empty, steals from Worker 1

Worker 3 deque: [T4, T5]
```

**LIFO for the owner, FIFO for the thief:**
- Owner pushes and pops from the "top" (LIFO) — locality-friendly, the most
  recently created task is likely still in cache.
- Thief steals from the "bottom" (FIFO) — steals the oldest, likely largest
  subtask, reducing future steals.

**Used in:** Go runtime (goroutine scheduling), Java ForkJoinPool,
Rust Rayon, Tokio (async task scheduling), .NET ThreadPool.

### 9.4 Fork/Join Pattern

```java
class SumTask extends RecursiveTask<Long> {
    private final int[] array;
    private final int lo, hi;
    private static final int THRESHOLD = 10_000;

    SumTask(int[] array, int lo, int hi) {
        this.array = array; this.lo = lo; this.hi = hi;
    }

    @Override
    protected Long compute() {
        if (hi - lo <= THRESHOLD) {
            // Base case: sequential
            long sum = 0;
            for (int i = lo; i < hi; i++) sum += array[i];
            return sum;
        }
        int mid = (lo + hi) / 2;
        SumTask left = new SumTask(array, lo, mid);
        SumTask right = new SumTask(array, mid, hi);
        left.fork();     // submit left to work-stealing pool
        long rightResult = right.compute(); // compute right in current thread
        long leftResult = left.join();      // wait for left
        return leftResult + rightResult;
    }
}
```

---

## 10. Backpressure

### 10.1 The Problem

A fast producer overwhelms a slow consumer. Without backpressure, the system
either drops data, crashes with OOM, or builds unbounded latency.

```
Producer (1000 msg/s) ──→ Queue (growing unbounded) ──→ Consumer (100 msg/s)
                              ↑
                     Queue grows at 900 msg/s
                     Eventually: OOM
```

### 10.2 Backpressure Strategies

| Strategy | Mechanism | Trade-off |
|---|---|---|
| **Blocking** | Producer blocks until consumer is ready | Lowest throughput, simplest |
| **Bounded buffer** | Fixed-size queue; producer blocks when full | Bounded memory, potential deadlock |
| **Drop** | Discard newest or oldest items | Data loss, bounded latency |
| **Sample** | Keep every Nth item | Lossy but bounded |
| **Throttle** | Rate-limit the producer | Requires feedback channel |
| **Adaptive batch** | Accumulate and process in variable-size batches | Latency variance |

### 10.3 Backpressure in Practice

**Go channels:**
```go
// Bounded channel = built-in backpressure
ch := make(chan Message, 100)

// Producer blocks when channel is full
ch <- msg  // blocks if 100 messages are buffered

// Consumer pulls at its own pace
msg := <-ch
```

**Reactive Streams (JVM):**
```java
// Subscriber requests only what it can handle
@Override
public void onSubscribe(Subscription subscription) {
    this.subscription = subscription;
    subscription.request(10);  // "I can handle 10 items"
}

@Override
public void onNext(Item item) {
    process(item);
    subscription.request(1);   // "Ready for 1 more"
}
```

**Node.js streams:**
```javascript
const { pipeline, Transform } = require('stream');

const slowTransform = new Transform({
  highWaterMark: 16,  // backpressure threshold
  transform(chunk, encoding, callback) {
    // simulate slow processing
    setTimeout(() => callback(null, chunk), 100);
  }
});

// pipeline() handles backpressure automatically
pipeline(readableSource, slowTransform, writableSink, (err) => {
  if (err) console.error('Pipeline failed:', err);
});
```

**Kafka:**
```
Consumer lag = latest offset - consumer offset
If lag grows → consumer is slower than producer
→ Add consumer instances (scale out consumer group)
→ Or: producer throttles (rate limit at API gateway)
```

---

## 11. Structured Concurrency

### 11.1 The Problem with Unstructured Concurrency

```go
// Unstructured: who owns this goroutine? When does it end? Error handling?
go func() {
    result, err := fetchData()
    if err != nil {
        // Who handles this error?
        // What if the parent already returned?
        log.Println(err)
    }
    // Where does result go?
}()
return // parent returns, goroutine is orphaned
```

Unstructured concurrency creates:
- **Orphan tasks:** Parent returns, child keeps running with no owner.
- **Lost errors:** Child fails, no one notices.
- **Resource leaks:** Goroutine/thread holds connections, never cleaned up.
- **Non-deterministic shutdown:** Kill the process and hope for the best.

### 11.2 Structured Concurrency Principle

Every concurrent task has an owner (scope). When the scope exits:
1. All child tasks are complete (or cancelled).
2. All errors are propagated.
3. No orphan tasks exist.

This mirrors structured programming (every block has defined entry/exit) but
for concurrency.

### 11.3 Implementations

**Java (StructuredTaskScope, preview):**
```java
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    var user = scope.fork(() -> fetchUser(id));
    var order = scope.fork(() -> fetchOrder(id));

    scope.join();           // Block until all subtasks complete
    scope.throwIfFailed();  // Propagate first failure

    return combine(user.get(), order.get());
}
// Scope exit guarantees: all subtasks done, resources released
```

**Kotlin (coroutineScope):**
```kotlin
suspend fun fetchUserAndOrder(id: String): UserOrder =
    coroutineScope {  // structured scope
        val user = async { fetchUser(id) }
        val order = async { fetchOrder(id) }
        // If fetchUser() throws, fetchOrder() is automatically cancelled
        UserOrder(user.await(), order.await())
    }
// coroutineScope doesn't return until all children complete
```

**Python (asyncio.TaskGroup, 3.11+):**
```python
async def fetch_all(ids: list[str]):
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(fetch_item(id)) for id in ids]
    # All tasks complete when the 'async with' block exits
    # If any task raises, all others are cancelled
    return [t.result() for t in tasks]
```

**Swift (Task groups):**
```swift
func fetchAll(ids: [String]) async throws -> [Item] {
    try await withThrowingTaskGroup(of: Item.self) { group in
        for id in ids {
            group.addTask { try await fetchItem(id) }
        }
        var results: [Item] = []
        for try await item in group {
            results.append(item)
        }
        return results
    }
    // Group scope guarantees all child tasks are complete
}
```

### 11.4 Go and Structured Concurrency

Go does not have built-in structured concurrency, but `errgroup` approximates it:

```go
import "golang.org/x/sync/errgroup"

func fetchAll(ctx context.Context, ids []string) ([]Item, error) {
    g, ctx := errgroup.WithContext(ctx)
    results := make([]Item, len(ids))

    for i, id := range ids {
        i, id := i, id
        g.Go(func() error {
            item, err := fetchItem(ctx, id)
            if err != nil {
                return err  // cancels ctx, other goroutines should respect it
            }
            results[i] = item
            return nil
        })
    }

    if err := g.Wait(); err != nil {
        return nil, err
    }
    return results, nil
}
```

---

## 12. Synchronization Primitives

### 12.1 Mutexes

```go
// Go
var mu sync.Mutex
mu.Lock()
// critical section
mu.Unlock()

// Read-Write Mutex: multiple readers OR one writer
var rwmu sync.RWMutex
rwmu.RLock()  // shared read lock
// read data
rwmu.RUnlock()

rwmu.Lock()   // exclusive write lock
// write data
rwmu.Unlock()
```

### 12.2 Condition Variables

```java
// Java
ReentrantLock lock = new ReentrantLock();
Condition notEmpty = lock.newCondition();
Condition notFull = lock.newCondition();

// Producer
lock.lock();
try {
    while (queue.isFull()) {
        notFull.await();  // release lock and wait
    }
    queue.add(item);
    notEmpty.signal();  // wake up one consumer
} finally {
    lock.unlock();
}
```

### 12.3 Semaphores

```python
import asyncio

# Limit concurrent database connections to 10
semaphore = asyncio.Semaphore(10)

async def query_db(sql):
    async with semaphore:
        # At most 10 coroutines in here simultaneously
        return await db.execute(sql)
```

### 12.4 Atomic Operations

```java
// Java
AtomicInteger counter = new AtomicInteger(0);
counter.incrementAndGet();  // atomic increment
counter.compareAndSet(expected, newValue);  // CAS

// Go
var counter atomic.Int64
counter.Add(1)
counter.CompareAndSwap(expected, newValue)

// Rust
use std::sync::atomic::{AtomicUsize, Ordering};
let counter = AtomicUsize::new(0);
counter.fetch_add(1, Ordering::SeqCst);
```

### 12.5 The sync.Once Pattern (Go)

```go
var (
    instance *Database
    once     sync.Once
)

func GetDB() *Database {
    once.Do(func() {
        instance = connectToDatabase()
    })
    return instance
}
// No matter how many goroutines call GetDB(),
// connectToDatabase() runs exactly once
```

---

## 13. Lock-Free and Wait-Free Data Structures

### 13.1 Definitions

- **Lock-free:** At least one thread makes progress in a finite number of steps
  (no deadlock, but some threads may starve temporarily).
- **Wait-free:** Every thread makes progress in a bounded number of steps
  (no starvation).
- **Obstruction-free:** A thread makes progress if it runs in isolation
  (weakest guarantee).

### 13.2 Compare-And-Swap (CAS)

The foundation of lock-free algorithms:

```
CAS(memory_location, expected_value, new_value):
    atomically:
        if *memory_location == expected_value:
            *memory_location = new_value
            return true
        else:
            return false  // someone else modified it first
```

Lock-free counter:
```go
func increment(counter *atomic.Int64) {
    for {
        old := counter.Load()
        if counter.CompareAndSwap(old, old+1) {
            return  // success
        }
        // CAS failed — another goroutine beat us. Retry.
    }
}
```

### 13.3 Lock-Free Queue (Michael-Scott Queue)

Used in Java's `ConcurrentLinkedQueue`:

```
Enqueue:
  1. Allocate new node
  2. CAS tail.next from null to new node
  3. CAS tail from old tail to new node

Dequeue:
  1. Read head.next
  2. CAS head from old head to head.next
  3. Return value from old head.next
```

Both operations are lock-free — no thread can block another indefinitely.

### 13.4 ABA Problem

CAS can be fooled if a value changes from A→B→A:
1. Thread 1 reads value A.
2. Thread 2 changes A→B→A.
3. Thread 1 does CAS(A, A, new) — succeeds, but the state has changed.

**Solution:** Use a version counter alongside the value. CAS on (value, version)
pair. Java's `AtomicStampedReference`, Go's pointer + counter packed in 128-bit.

---

## 14. Concurrency Patterns

### 14.1 Producer-Consumer

```
Producer ──→ Bounded Queue ──→ Consumer
             (backpressure)
```

### 14.2 Pipeline

```
Stage 1 ──→ Stage 2 ──→ Stage 3 ──→ Output
(decode)    (transform)  (encode)
```

Each stage is a concurrent process. Data flows through channels between stages.

### 14.3 Fan-Out / Fan-In

```
           ┌─→ Worker 1 ─→┐
Input ────→├─→ Worker 2 ─→├──→ Merged Output
           └─→ Worker 3 ─→┘
```

### 14.4 Scatter-Gather

```
Request ──→ ┌─→ Service A ─→┐
            ├─→ Service B ─→├──→ Aggregate Response
            └─→ Service C ─→┘
                         (timeout: first N or all)
```

### 14.5 Circuit Breaker (Concurrency-Aware)

```
States: Closed → Open → Half-Open → Closed
                    ↑         │
                    └─────────┘ (if test succeeds)

Closed: normal operation, count failures
Open: reject immediately (fail fast), wait timeout
Half-Open: allow one request through, if success → Closed, if fail → Open
```

### 14.6 Bulkhead

Isolate different workloads into separate thread pools so failure in one
doesn't exhaust resources for others:

```
┌─────────────────────────────────┐
│  Service                         │
│  ┌───────────┐ ┌───────────┐   │
│  │ Pool: API  │ │Pool: Batch│   │
│  │ (20 thr)   │ │ (8 thr)   │   │
│  └───────────┘ └───────────┘   │
│  API overload doesn't affect   │
│  batch processing              │
└─────────────────────────────────┘
```

### 14.7 Shard-Per-Core (Thread-Per-Core)

Instead of shared state with locks, partition state across cores. Each core owns
its partition exclusively. No synchronization needed within a partition.

**Used by:** ScyllaDB, Seastar framework, DPDK-based applications.

```
Core 0: owns partitions 0-99
Core 1: owns partitions 100-199
Core 2: owns partitions 200-299
Core 3: owns partitions 300-399

Cross-partition requests: message passing between cores
```

---

## 15. Debugging Concurrency Issues

### 15.1 Common Bugs

| Bug | Cause | Symptom |
|---|---|---|
| **Deadlock** | Circular lock acquisition | Program hangs |
| **Livelock** | Threads keep retrying, making no progress | CPU spins, no progress |
| **Race condition** | Unsynchronized shared state access | Intermittent wrong results |
| **Data race** | Two threads access same memory, at least one writes, no sync | Undefined behavior |
| **Starvation** | Thread never gets CPU time | Some tasks never complete |
| **Priority inversion** | Low-priority thread holds lock needed by high-priority | High-priority thread delayed |

### 15.2 Detection Tools

**Go:**
```bash
# Race detector (compile-time instrumentation + runtime detection)
go test -race ./...
go run -race main.go

# Deadlock detector
# go-deadlock: drop-in replacement for sync.Mutex that detects lock ordering issues
```

**Java:**
```bash
# Thread dumps (shows all thread states + lock ownership)
jstack <pid>
# or: kill -3 <pid> (sends SIGQUIT, JVM prints thread dump to stderr)

# jconsole / VisualVM: live thread monitoring
# JFR (Java Flight Recorder): low-overhead production profiling
```

**Rust:**
```bash
# The borrow checker prevents data races at compile time.
# No runtime race detector needed for safe Rust.
# For unsafe code: ThreadSanitizer (TSan)
RUSTFLAGS="-Z sanitizer=thread" cargo test
```

**Python:**
```bash
# asyncio debug mode
PYTHONASYNCIODEBUG=1 python script.py
# Shows: unawaited coroutines, slow callbacks, wrong-thread access

# threading debug
import faulthandler
faulthandler.enable()  # dump thread stacks on crash
```

### 15.3 Debugging Strategies

1. **Reproduce deterministically:** Use fixed seeds, controlled timing, reduced
   concurrency.
2. **Add structured logging with correlation IDs and timestamps.**
3. **Use thread-safe data structures** instead of manual locking where possible.
4. **Minimize critical sections** — lock only what's necessary.
5. **Always acquire locks in a consistent global order** to prevent deadlock.
6. **Prefer immutable data** — if data doesn't change, no synchronization needed.

---

## 16. Benchmarking and Performance

### 16.1 Key Metrics

| Metric | What it measures |
|---|---|
| **Throughput** | Requests/second, messages/second |
| **Latency (p50/p99/p999)** | Time from request to response |
| **Context switch rate** | Overhead of scheduler |
| **Lock contention** | Time threads spend waiting for locks |
| **Memory per connection** | Scalability indicator |
| **CPU utilization** | Are cores saturated or idle? |

### 16.2 Benchmarking Tips

- **Warm up** before measuring (JIT compilation, cache warming).
- **Measure p99, not just average.** Average hides tail latency.
- **Saturate** the system to find the inflection point where latency explodes.
- **Isolate variables:** change one parameter at a time.
- **Profile under load:** flamegraphs, perf, async-profiler.
- **Use coordinated omission correction** (Gil Tene's methodology) — naive
  benchmarks under-report latency during overload.

### 16.3 Tools

```bash
# Go: built-in benchmarking
go test -bench=. -benchmem -cpu 1,2,4,8

# Go: pprof profiling
import _ "net/http/pprof"
# then: go tool pprof http://localhost:6060/debug/pprof/goroutine

# Java: JMH (Java Microbenchmark Harness)
@Benchmark
public void testMethod() { ... }

# General: wrk (HTTP benchmark)
wrk -t12 -c400 -d30s http://localhost:8080/

# General: vegeta (HTTP load testing)
echo "GET http://localhost:8080/" | vegeta attack -rate=1000/s -duration=30s | vegeta report
```

---

## 17. Choosing a Concurrency Model

### 17.1 Decision Framework

```
Is the workload CPU-bound or I/O-bound?
├── CPU-bound → Use parallelism (multiple cores)
│   ├── Compute-heavy processing → Thread pool or process pool
│   ├── Data parallelism → Fork/Join, Rayon, parallel streams
│   └── Pipeline → Pipeline with bounded buffers
│
└── I/O-bound → Use concurrency (many waiters, few cores)
    ├── Many connections, simple handlers → Event loop (Node.js, asyncio)
    ├── Complex state per connection → Actors (Erlang, Akka)
    ├── Need simplicity + scale → Green threads (Go, Java virtual threads)
    └── Mixed I/O + some CPU → Async + worker thread pool
```

### 17.2 Language-Concurrency Fit

| Language | Best model | Why |
|---|---|---|
| **Go** | Goroutines + channels | Built-in M:N scheduler, no colored functions, CSP native |
| **Erlang/Elixir** | Actors + supervision | BEAM VM purpose-built, "let it crash," telecom-grade |
| **Java 21+** | Virtual threads | Write blocking code, get async perf, huge ecosystem |
| **Node.js** | Event loop + worker threads | Single-threaded simplicity for I/O, workers for CPU |
| **Python** | asyncio (I/O) + multiprocessing (CPU) | GIL forces this split |
| **Rust** | Tokio async (I/O) + Rayon (CPU) | Zero-cost abstractions, fearless concurrency via borrow checker |
| **C#** | Task + async/await | Mature TPL, good for mixed workloads |

### 17.3 Anti-Patterns

- **Thread-per-request with blocking I/O at scale:** Use virtual threads or async.
- **Shared mutable state with locks everywhere:** Use message passing or immutable data.
- **Unbounded concurrency:** Always limit via pools, semaphores, or bounded channels.
- **Async for CPU-bound work:** Blocks the event loop. Offload to thread/process pool.
- **Ignoring backpressure:** Producer-consumer without bounded buffers leads to OOM.
- **Over-engineering:** If your server handles 100 requests/second, you don't need
  an actor system. A simple thread pool will do.

---

## 18. Exercises

### Exercise 1: Event Loop Visualization

Write a Node.js program that demonstrates all event loop phases:
1. Schedule a `setTimeout(0)`.
2. Schedule a `setImmediate()`.
3. Schedule a `process.nextTick()`.
4. Schedule a Promise resolution.
5. Predict and then verify the execution order.
6. Add an `fs.readFile()` call and observe where its callback lands.

### Exercise 2: Go Work Stealing

1. Write a Go program that spawns 1,000,000 goroutines, each performing a
   trivial computation.
2. Measure execution time with `GOMAXPROCS=1` vs `GOMAXPROCS=8`.
3. Add `runtime.Gosched()` calls and observe scheduling behavior.
4. Use `runtime/trace` to visualize goroutine scheduling across processors.

### Exercise 3: Producer-Consumer with Backpressure

Implement a producer-consumer system in your language of choice:
1. Producer generates 10,000 items per second.
2. Consumer processes 1,000 items per second.
3. Use a bounded buffer of 100 items.
4. Measure: producer blocking time, consumer utilization, end-to-end latency.
5. Compare with an unbounded buffer: measure memory growth.

### Exercise 4: Virtual Threads vs Platform Threads

Write a Java program that:
1. Makes 10,000 concurrent HTTP requests using a fixed thread pool of 200.
2. Makes the same 10,000 requests using virtual threads.
3. Compare: throughput, memory usage, and latency distributions.
4. Introduce a `synchronized` block and observe pinning with
   `-Djdk.tracePinnedThreads=full`.

### Exercise 5: Actor System

Build a simple chat system using actors:
1. A `RoomActor` manages a list of `UserActor` references.
2. `UserActor` receives messages and prints them.
3. Users can join/leave rooms, send messages.
4. Implement supervision: if a `UserActor` crashes, restart it.
5. Use Erlang/Elixir, Akka, or a Go channel-based actor simulation.

### Exercise 6: Structured Concurrency

1. Write a function that fetches data from 3 APIs concurrently.
2. If any API fails, cancel the other in-flight requests.
3. Implement a timeout: if the group doesn't complete in 5 seconds, cancel all.
4. Compare structured (TaskGroup/errgroup/coroutineScope) vs unstructured
   (fire-and-forget goroutines/threads).

### Exercise 7: Race Condition Detection

1. Write a deliberately racy Go program (two goroutines incrementing a shared
   counter without synchronization).
2. Run with `go test -race`. Observe the report.
3. Fix with: (a) mutex, (b) atomic operations, (c) channel.
4. Benchmark all three solutions.

---

## 19. References

- Hoare, C.A.R. "Communicating Sequential Processes" (1978).
- Armstrong, Joe. "Making reliable distributed systems in the presence of
  software errors" (2003) — the Erlang thesis.
- Pike, Rob. "Concurrency is not Parallelism" (2012) — Go blog.
- Pressler, Ron. "Project Loom: Fibers and Continuations for the Java Virtual
  Machine" (JEP 444).
- Nystrom, Bob. "What Color is Your Function?" (2015).
- Elizarov, Roman. "Structured Concurrency" — Kotlin design doc.
- Sutter, Herb. "The Free Lunch Is Over" (2005) — the end of single-core
  performance scaling.
- Node.js Event Loop documentation. https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick
- Go scheduler design document. https://go.dev/src/runtime/HACKING.md
- Java Virtual Threads (JEP 444). https://openjdk.org/jeps/444
