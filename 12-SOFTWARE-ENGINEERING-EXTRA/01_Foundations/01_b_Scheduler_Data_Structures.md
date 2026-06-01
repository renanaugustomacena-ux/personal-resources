---
corso: "SWE Masterclass"
fase: "1 — Foundations"
modulo: "01.1.b"
titolo: "Scheduler Data Structures Deep Dive"
versione: "Linux 6.x"
livello: "Advanced"
prerequisiti:
  - "OS process lifecycle and context switching (Module 01.1)"
  - "Red-Black tree and priority queue fundamentals"
  - "C language proficiency for reading kernel source"
obiettivi:
  - "Explain CFS virtual runtime accounting and red-black tree runqueue organisation"
  - "Contrast EEVDF eligibility and virtual-deadline picking with legacy CFS behaviour"
  - "Analyse sched_ext BPF hooks and write a minimal custom scheduling policy"
  - "Trace PELT load-tracking metrics through /proc and debugfs"
  - "Evaluate scheduling trade-offs (throughput vs latency vs energy) for real workloads"
tag: [scheduler, CFS, EEVDF, sched_ext, PELT, red-black-tree, BPF, linux-kernel, real-time, EAS]
---

# Module 1.1.b: Scheduler Data Structures Deep Dive

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Explain CFS virtual runtime accounting and red-black tree runqueue organisation
> - Contrast EEVDF eligibility and virtual-deadline picking with legacy CFS behaviour
> - Analyse sched_ext BPF hooks and write a minimal custom scheduling policy
> - Trace PELT load-tracking metrics through /proc and debugfs
> - Evaluate scheduling trade-offs (throughput vs latency vs energy) for real workloads

> **Module 01.1.b** · **Last updated:** 2026-05-22

## Guiding ideas
1. **Linux CFS uses Red-Black Tree for runqueue.** O(log n) operations.
2. **EEVDF (Earliest Eligible Virtual Deadline First) replaces CFS in 6.6+.**
3. **sched_ext (BPF schedulers): customizable scheduling policy.**
4. **PELT (Per-Entity Load Tracking) for fair averaging.**

---

## 1. Scheduling Theory Foundations

### 1.1 The Scheduling Problem

The OS must decide: which of N runnable tasks gets CPU time, on which CPU, for how long?

**Conflicting goals:**

| Goal | Metric | Tension |
|------|--------|---------|
| Throughput | Tasks completed / time | Favor long time slices (fewer switches) |
| Latency | Time from runnable to running | Favor short time slices (more switches) |
| Fairness | Equal share per priority | Must preempt long-running tasks |
| Energy | Power consumption | Favor fewer active cores |
| Affinity | Cache efficiency | Avoid migrating tasks |

### 1.2 Classical Scheduling Algorithms

| Algorithm | Type | Time Complexity | Starvation? | Interactive? |
|-----------|------|-----------------|-------------|-------------|
| FCFS (First Come First Served) | Non-preemptive | O(1) | No | Poor |
| SJF (Shortest Job First) | Non-preemptive | O(n) or O(log n) | Yes (long jobs) | N/A |
| Round Robin | Preemptive | O(1) | No | Moderate |
| Priority Queue | Preemptive | O(log n) | Yes (low prio) | Good |
| MLFQ (Multi-Level Feedback Queue) | Preemptive | O(1) | Possible | Good |
| CFS (Completely Fair Scheduler) | Preemptive | O(log n) | No | Good |
| EEVDF | Preemptive | O(log n) | No | Excellent |
| EDF (Earliest Deadline First) | Preemptive | O(log n) | No (admission) | Real-time |

### 1.3 MLFQ — Multi-Level Feedback Queue

MLFQ was the dominant scheduler design before CFS. Understanding it helps appreciate CFS's elegance.

```
MLFQ Structure:

Priority 0 (highest):  [T1] [T2]        ← Interactive tasks
                         │    │
                         ▼    ▼
Priority 1:            [T3] [T4] [T5]   ← Moderate tasks
                         │    │    │
                         ▼    ▼    ▼
Priority 2:            [T6]              ← CPU-bound tasks
                         │
                         ▼
Priority N (lowest):   [T7] [T8]         ← Background tasks

Rules:
1. New tasks start at highest priority
2. If a task uses its full time quantum → demote to lower queue
3. If a task yields before quantum expires → stay at same level
4. Periodic boost: move all tasks to highest queue (prevents starvation)
5. Each level has a different time quantum (lower = longer quantum)
```

**Problems with MLFQ:**
- Gaming: a malicious task could yield just before quantum expires to stay at high priority.
- Tuning: many parameters (number of levels, quantum per level, boost interval).
- Starvation: without periodic boost, low-priority tasks can starve.

### 1.4 The O(1) Scheduler (Linux 2.6.0 - 2.6.22)

Before CFS, Linux used an O(1) scheduler with two arrays:

```
O(1) Scheduler:

Active Array (bitmap + linked lists):
Bit 0 → [priority 0 tasks: T1, T2]
Bit 1 → [priority 1 tasks: T3]
Bit 2 → [priority 2 tasks: T4, T5, T6]
...
Bit 139→ [priority 139 tasks: T7]

Expired Array (same structure, initially empty)

Algorithm:
1. find_first_bit(active_bitmap) → highest priority with tasks
2. Dequeue first task from that list → run it
3. When task exhausts quantum → move to expired array
4. When active array is empty → swap active and expired pointers

Complexity: O(1) for pick_next_task (bitmap scan = constant time)
```

**Problem:** Heuristics for interactive tasks were fragile. The "interactivity bonus" heuristic frequently misclassified tasks, leading to desktop responsiveness issues.

---

## 2. The Red-Black Tree in CFS

### 2.1 Red-Black Tree Properties

A Red-Black Tree is a self-balancing BST with these invariants:

```
1. Every node is Red or Black
2. Root is Black
3. Every NULL leaf is Black
4. Red nodes have only Black children (no two reds in a row)
5. All paths from a node to descendant NULLs have the same Black count

Consequence: longest path ≤ 2 × shortest path
             height ≤ 2 · log₂(n+1)
```

### 2.2 Why Red-Black Trees Over AVL Trees?

| Property | AVL | Red-Black |
|----------|-----|-----------|
| Balance | Strict (height diff ≤ 1) | Relaxed (longest ≤ 2× shortest) |
| Lookup | O(1.44 · log N) | O(2 · log N) |
| Insert rotations | Up to O(log N) | At most 2 |
| Delete rotations | Up to O(log N) | At most 3 |
| Amortized rebalance | O(log N) | O(1) |

**The kernel's choice:** Schedulers mutate the tree on every wake-up, sleep, migration, and timer tick. High mutation rate → cheaper writes matter more than marginally faster reads.

### 2.3 RB-Tree Operations Illustrated

**Insertion (simplified):**

```
Insert node with vruntime=350 into:

Before:                           After:
        500(B)                          500(B)
       /     \                         /     \
    300(B)   700(B)                300(B)   700(B)
    /   \      /                  /   \      /
 200(R) 400(R) 600(R)         200(R) 400(R) 600(R)
                                      /
                                   350(R) ← new

Step 1: BST insert at correct position
Step 2: Color new node RED
Step 3: Fix violations:
  - Parent 400 is RED, uncle (sibling of parent) is...
  - Case analysis → recolor or rotate
```

**Deletion example:**

```
Delete node with vruntime=300:

Before:                          After:
        500(B)                         500(B)
       /     \                        /     \
    300(B)   700(B)  →           350(B)   700(B)
    /   \      /                 /   \      /
 200(R) 400(R) 600(R)        200(R) 400(R) 600(R)

Step 1: Find in-order successor (350)
Step 2: Replace 300 with 350
Step 3: Fix violations if any
```

### 2.4 Kernel Implementation: `lib/rbtree.c`

**Intrusive data structure:** The `rb_node` is embedded *inside* the `task_struct` (via `sched_entity`). No separate allocation needed.

```c
/* From include/linux/rbtree.h */
struct rb_node {
    unsigned long  __rb_parent_color;  /* parent pointer + color in LSB */
    struct rb_node *rb_right;
    struct rb_node *rb_left;
};

struct rb_root {
    struct rb_node *rb_node;  /* root of tree */
};

struct rb_root_cached {
    struct rb_root rb_root;
    struct rb_node *rb_leftmost;  /* ← cached for O(1) pick_next */
};
```

```c
/* How sched_entity embeds the rb_node */
struct sched_entity {
    struct load_weight    load;         /* priority weight */
    struct rb_node        run_node;     /* embedded in RB tree */
    unsigned int          on_rq;        /* on runqueue? */
    u64                   exec_start;   /* last schedule start time */
    u64                   sum_exec_runtime; /* total CPU time */
    u64                   vruntime;     /* virtual runtime (tree key) */
    u64                   prev_sum_exec_runtime;
    /* ... more fields ... */
};
```

### 2.5 The Leftmost Cache Optimization

Finding the leftmost node (smallest vruntime, next task to run) is O(log N) in a standard BST. CFS caches it:

```c
/* rb_root_cached maintains rb_leftmost */
/* In kernel/sched/fair.c: */

static struct sched_entity *pick_next_entity(struct cfs_rq *cfs_rq) {
    struct rb_node *left = rb_first_cached(&cfs_rq->tasks_timeline);
    if (!left)
        return NULL;
    return rb_entry(left, struct sched_entity, run_node);
}
/* This is O(1) — just dereference the cached pointer */
```

When inserting a new node, the tree checks if it becomes the new leftmost:

```c
/* Simplified from kernel/sched/fair.c */
static void __enqueue_entity(struct cfs_rq *cfs_rq,
                             struct sched_entity *se) {
    struct rb_node **link = &cfs_rq->tasks_timeline.rb_root.rb_node;
    struct rb_node *parent = NULL;
    bool leftmost = true;

    while (*link) {
        parent = *link;
        struct sched_entity *entry = rb_entry(parent,
                                              struct sched_entity,
                                              run_node);
        if (entity_before(se, entry)) {
            link = &parent->rb_left;
        } else {
            link = &parent->rb_right;
            leftmost = false;   /* not leftmost */
        }
    }
    rb_link_node(&se->run_node, parent, link);
    rb_insert_color_cached(&se->run_node,
                           &cfs_rq->tasks_timeline, leftmost);
}
```

---

## 3. Per-CPU Variables & Locking

### 3.1 The Per-CPU Paradigm

Scalability kills. If all CPUs fought over one global runqueue, lock contention would destroy performance on many-core systems.

```
Global runqueue (bad):                Per-CPU runqueues (good):

   ┌───────────────────┐              CPU 0: ┌──────────┐
   │  Global Lock (!)   │              │ rq0: │ T1 T2 T3 │
   │  ┌───────────────┐ │              │      └──────────┘
   │  │ T1 T2 T3 T4   │ │              │
   │  │ T5 T6 T7 T8   │ │              CPU 1: ┌──────────┐
   │  └───────────────┘ │              │ rq1: │ T4 T5    │
   └───────────────────┘              │      └──────────┘
                                      │
   All CPUs contend for               CPU 2: ┌──────────┐
   the same lock → serialized         │ rq2: │ T6 T7 T8 │
                                      │      └──────────┘
                                      
                                      Each CPU only locks its own rq
                                      → near-perfect linear scaling
```

### 3.2 Hardware Implementation (x86_64)

```
Per-CPU data access on x86_64:

1. At boot, kernel allocates N copies of per-cpu section
   (one per CPU)

2. GS segment register holds the base address of the
   current CPU's per-cpu area

3. Access pattern:
   mov rax, gs:[offset]    ; read per-cpu variable
   mov gs:[offset], rbx    ; write per-cpu variable

4. On kernel entry from userspace:
   swapgs                  ; swap user GS ↔ kernel GS
   ; Now GS points to per-cpu kernel data

5. Example: accessing the current task:
   current = gs:[current_task_offset]
   ; No lock needed — each CPU has its own copy
```

### 3.3 The Runqueue (`struct rq`)

Every CPU has its own `struct rq`:

```c
/* Simplified from kernel/sched/sched.h */
struct rq {
    raw_spinlock_t      lock;           /* rq lock */
    unsigned int        nr_running;     /* total runnable tasks */
    
    struct cfs_rq       cfs;            /* CFS runqueue */
    struct rt_rq        rt;             /* RT runqueue */
    struct dl_rq        dl;             /* Deadline runqueue */
    
    struct task_struct  *curr;          /* currently running task */
    struct task_struct  *idle;          /* idle task for this CPU */
    
    u64                 clock;          /* rq-local clock */
    u64                 clock_task;     /* clock excluding IRQ time */
    
    int                 cpu;            /* CPU index */
    int                 online;         /* CPU online? */
    
    struct sched_domain *sd;            /* scheduling domain */
    
    /* ... many more fields ... */
};
```

**Locking rules:**
- Local scheduler operations (picking next task, updating vruntime) only acquire the local `rq->lock`.
- Cross-CPU operations (migration, load balancing) acquire both source and destination `rq->lock` in a fixed order to prevent deadlocks.
- Lock ordering: always lock lower-numbered CPU first.

---

## 4. Load Balancing & Work Stealing

### 4.1 The Problem

If CPU 0 has 10 tasks and CPU 1 has 0, we waste 50% of available compute. But migrating tasks has costs:
- Acquiring remote runqueue locks
- Cache cold start on the new CPU
- NUMA penalty if crossing node boundaries

### 4.2 Hierarchical Scheduling Domains

CPUs are grouped into domains based on hardware topology:

```
Scheduling Domain Hierarchy:

Level 3: NUMA Domain
┌─────────────────────────────────────────────────┐
│                                                 │
│  Level 2: Socket Domain                         │
│  ┌───────────────────┐  ┌───────────────────┐   │
│  │                   │  │                   │   │
│  │  Level 1: Core    │  │  Level 1: Core    │   │
│  │  ┌──────┐┌──────┐ │  │  ┌──────┐┌──────┐ │   │
│  │  │ SMT  ││ SMT  │ │  │  │ SMT  ││ SMT  │ │   │
│  │  │ CPU0 ││ CPU1 │ │  │  │ CPU4 ││ CPU5 │ │   │
│  │  │ CPU2 ││ CPU3 │ │  │  │ CPU6 ││ CPU7 │ │   │
│  │  └──────┘└──────┘ │  │  └──────┘└──────┘ │   │
│  │                   │  │                   │   │
│  │  Socket 0         │  │  Socket 1         │   │
│  └───────────────────┘  └───────────────────┘   │
│                                                 │
│  NUMA Node 0             NUMA Node 1            │
└─────────────────────────────────────────────────┘

Balancing frequency per level:
  SMT siblings:     every 1 ms  (L1 cache warm, cheapest migration)
  Same socket:      every 4 ms  (L3 cache warm)
  Cross-socket:     every 16 ms (L3 cold, higher latency)
  Cross-NUMA node:  every 64 ms (memory access penalty)
```

### 4.3 Load Balancing Mechanisms

**Periodic Load Balance:**

```
scheduler_tick()  (called on every timer tick, typically 1 kHz)
    │
    ▼
trigger_load_balance()
    │
    ├── Check if balance interval expired for each domain level
    │
    ▼
load_balance()
    │
    ├── For each scheduling domain (bottom-up):
    │   1. Calculate load of each CPU group
    │   2. Identify busiest group and busiest CPU
    │   3. If imbalance > threshold:
    │      a. Lock source rq (busiest CPU)
    │      b. Lock destination rq (this CPU)
    │      c. Migrate tasks (up to sched_nr_migrate)
    │      d. Unlock both
    │
    └── Return
```

**Idle Balance (Work Stealing):**

```
schedule() finds no runnable tasks → CPU about to go idle
    │
    ▼
idle_balance()
    │
    ├── Search order (cache warmth priority):
    │   1. SMT sibling (L1 data cache warm)
    │   2. Same-core sibling (L1/L2 shared)
    │   3. Same-socket CPU (L3 shared)
    │   4. Same NUMA node
    │   5. Remote NUMA node (last resort)
    │
    ├── For each candidate source CPU:
    │   1. Try lock source rq (non-blocking)
    │   2. If locked: pick suitable task
    │      - Not cache-hot (ran recently on source)
    │      - Not pinned to source CPU
    │      - Would improve overall balance
    │   3. Migrate task to local rq
    │
    └── If no task found: enter idle
```

### 4.4 Load Metrics: PELT (Per-Entity Load Tracking)

PELT computes a decaying average of CPU utilization for each scheduling entity:

```
PELT Formula:

load_avg = Σ(contribution_i × decay_factor^(age_i))

Where:
  contribution_i = load_weight × (runtime / period)
  decay_factor = e^(-period / half_life)
  half_life = 32 ms (default)

Effect:
  A task that was busy 32 ms ago contributes 50% of its weight
  A task that was busy 64 ms ago contributes 25%
  A task that was busy 96 ms ago contributes 12.5%

┌─────────────────────────────────────────────┐
│  Utilization over time (PELT)                │
│                                              │
│  100% ┤  ████                                │
│   75% ┤  ████ ██                             │
│   50% ┤  ████ ████                           │
│   25% ┤  ████ ████ ██                        │
│    0% ┤──████─████─████─────────────────     │
│       └──┴────┴────┴────┴────┴────┴────      │
│          Task   Task  Decay  Decay  Decay    │
│          runs   runs  (idle) (idle) (idle)   │
└─────────────────────────────────────────────┘
```

**Why PELT over instantaneous load?**
- Instantaneous: task just woke up → load = 0 (wrong, it was busy before).
- PELT: remembers history → better migration decisions.
- Prevents oscillation (task migrating back and forth).

### 4.5 The "Misfit" Task Problem

On heterogeneous CPUs (ARM big.LITTLE, Intel P-core/E-core):

```
big.LITTLE System:
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  big 0   │  │  big 1   │  │ LITTLE 0 │  │ LITTLE 1 │
│ (fast)   │  │ (fast)   │  │ (slow)   │  │ (slow)   │
│ 2.5 GHz  │  │ 2.5 GHz  │  │ 1.2 GHz  │  │ 1.2 GHz  │
│          │  │ [T1,T2]  │  │ [T3]     │  │          │
└──────────┘  └──────────┘  └──────────┘  └──────────┘

Problem: T3 is a CPU-intensive task stuck on a LITTLE core.
         Load balancing sees: big1 has 2 tasks, LITTLE0 has 1.
         By load count, LITTLE0 looks underloaded!

Solution: CFS "misfit" detection:
  - Track task's capacity utilization vs CPU capacity
  - If utilization > 80% of LITTLE core capacity → misfit
  - Force migration to big core, even if load numbers look balanced
  - Capacity-aware scheduling considers CPU speed, not just task count
```

### 4.6 Energy-Aware Scheduling (EAS)

On heterogeneous systems, EAS optimizes for energy efficiency:

```
Without EAS (performance only):
  Always use biggest/fastest core available
  → Maximum performance, maximum power consumption

With EAS:
  1. Check if task fits on a small/efficient core
  2. If task utilization < small core capacity:
     → Schedule on small core (saves energy)
  3. If task needs more compute:
     → Schedule on big core (trade energy for performance)

Energy Model:
  ┌─────────────────────────────────────────────┐
  │  Power consumption vs. frequency             │
  │                                              │
  │  Power │          ╱╱╱ big core               │
  │  (W)   │        ╱╱                           │
  │        │      ╱╱                             │
  │        │    ╱╱          ╱╱╱ LITTLE core       │
  │        │  ╱╱          ╱╱                     │
  │        │╱╱          ╱╱                       │
  │        ├──────────╱╱──────────────────       │
  │        └────────────────────────────────     │
  │             Frequency (GHz)                  │
  │                                              │
  │  LITTLE at 1.2 GHz: 0.5W  (efficient)       │
  │  big at 1.2 GHz:    1.5W  (wasteful)        │
  │  big at 2.5 GHz:    5.0W  (when needed)     │
  └─────────────────────────────────────────────┘
```

---

## 5. Real-Time Scheduling Classes

### 5.1 SCHED_FIFO

- Fixed priority (1-99, higher = more important).
- Task runs until it: voluntarily yields, blocks, or is preempted by higher-priority RT task.
- No time quantum — runs forever if nothing preempts it.
- **Danger:** A SCHED_FIFO task in an infinite loop will hang the system on that CPU.

```c
/* C: SCHED_FIFO example with safety watchdog */
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>

static volatile int running = 1;

void alarm_handler(int sig) {
    (void)sig;
    running = 0;
}

int main(void) {
    struct sched_param sp;
    sp.sched_priority = 50; /* Range: 1-99 */

    if (sched_setscheduler(0, SCHED_FIFO, &sp) < 0) {
        perror("sched_setscheduler (need CAP_SYS_NICE or root)");
        return 1;
    }

    /* Safety: auto-exit after 5 seconds */
    signal(SIGALRM, alarm_handler);
    alarm(5);

    printf("Running as SCHED_FIFO prio %d for 5 seconds\n",
           sp.sched_priority);

    /* Real-time work loop */
    struct timespec deadline;
    clock_gettime(CLOCK_MONOTONIC, &deadline);

    while (running) {
        /* Do real-time work */
        volatile int sum = 0;
        for (int i = 0; i < 1000000; i++) sum += i;

        /* Yield to other same-priority tasks */
        sched_yield();
    }

    /* Restore normal scheduling */
    sp.sched_priority = 0;
    sched_setscheduler(0, SCHED_OTHER, &sp);
    printf("Back to normal scheduling\n");
    return 0;
}
```

### 5.2 SCHED_RR (Round Robin)

Like SCHED_FIFO but with a time quantum (default 100 ms):

```
SCHED_RR with priority 50, quantum = 100 ms:

Time →
T1 (prio 50): ████████████│             │████████████│
T2 (prio 50):             │████████████│             │████████████
              0          100           200          300
              ms          ms            ms           ms

Each task at the same priority gets a fair quantum.
Higher-priority RT tasks still preempt immediately.
```

### 5.3 SCHED_DEADLINE (Earliest Deadline First)

The most sophisticated Linux scheduling class. Implements CBS (Constant Bandwidth Server):

```
SCHED_DEADLINE Parameters:
  runtime:  CPU time per period (e.g., 10 ms)
  deadline: by when it must finish (e.g., 30 ms)
  period:   repetition interval (e.g., 30 ms)

Example: runtime=10ms, deadline=30ms, period=30ms
  → Task gets 10 ms of CPU every 30 ms
  → Bandwidth reservation: 10/30 = 33%

Timeline:
  ┌──────────────────────────────────────────────┐
  │ Period 1        │ Period 2        │ Period 3  │
  │ [10ms work]     │ [10ms work]     │ [10ms]    │
  │ ████░░░░░░░░░░░│████░░░░░░░░░░░│████░░░░░░ │
  │ ^deadline       │ ^deadline       │           │
  └──────────────────────────────────────────────┘
```

```c
/* C: SCHED_DEADLINE example */
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <linux/sched.h>
#include <linux/types.h>

struct sched_attr {
    __u32 size;
    __u32 sched_policy;
    __u64 sched_flags;
    __s32 sched_nice;
    __u32 sched_priority;
    __u64 sched_runtime;
    __u64 sched_deadline;
    __u64 sched_period;
};

int main(void) {
    struct sched_attr attr;
    memset(&attr, 0, sizeof(attr));
    attr.size = sizeof(attr);
    attr.sched_policy = SCHED_DEADLINE;
    attr.sched_runtime  = 10 * 1000 * 1000;   /* 10 ms */
    attr.sched_deadline = 30 * 1000 * 1000;   /* 30 ms */
    attr.sched_period   = 30 * 1000 * 1000;   /* 30 ms */

    /* sched_setattr is not in glibc, use raw syscall */
    if (syscall(SYS_sched_setattr, 0, &attr, 0) < 0) {
        perror("sched_setattr (need CAP_SYS_NICE)");
        return 1;
    }

    printf("Running as SCHED_DEADLINE: 10ms every 30ms\n");

    for (int i = 0; i < 100; i++) {
        /* Do periodic work */
        volatile int sum = 0;
        for (int j = 0; j < 100000; j++) sum += j;

        /* Yield remaining runtime; sleep until next period */
        sched_yield();
    }

    return 0;
}
```

**Admission control:** The kernel rejects `sched_setattr` if the total bandwidth of all SCHED_DEADLINE tasks would exceed a configurable limit (default 95%):

```
/proc/sys/kernel/sched_rt_runtime_us  = 950000  (95%)
/proc/sys/kernel/sched_rt_period_us   = 1000000 (1 second)

Sum of all (runtime/period) for all DL tasks must be ≤ 0.95
```

### 5.4 Priority Hierarchy

```
Scheduling class priority (highest to lowest):

SCHED_DEADLINE  (dl_sched_class)
    │  Absolute highest; tasks always run first
    │  Admission-controlled; kernel rejects overcommit
    ▼
SCHED_FIFO / SCHED_RR  (rt_sched_class)
    │  Fixed priority 1-99
    │  FIFO within same priority, RR adds time quantum
    │  WARNING: no admission control! Can starve everything
    ▼
SCHED_NORMAL / SCHED_BATCH / SCHED_IDLE  (fair_sched_class)
    │  CFS/EEVDF scheduler
    │  Nice values -20 to +19
    │  BATCH: no preemption bonus
    │  IDLE: only runs when nothing else wants CPU
    ▼
Idle task  (idle_sched_class)
    CPU-specific idle task; halts CPU when no work
```

---

## 6. EEVDF — Earliest Eligible Virtual Deadline First (Linux 6.6+)

### 6.1 Why Replace CFS?

CFS had accumulated complexity to handle edge cases:
- **Sleeper fairness hacks:** Tasks that slept needed a "bonus" to their vruntime to prevent unfairness. These heuristics were fragile.
- **Latency-nice:** A proposed feature to allow tasks to request lower latency without higher CPU share. CFS could not cleanly support this.
- **Interactive responsiveness:** CFS's vruntime model does not naturally distinguish between "wants low latency" and "wants high throughput."

### 6.2 EEVDF Core Concepts

```
CFS:                                EEVDF:
  Key: vruntime                       Key: eligible_time + virtual_deadline
  Pick: smallest vruntime             Pick: eligible task with earliest deadline
  Tree: sorted by vruntime            Tree: sorted by deadline (and eligibility)
  
  All tasks are always eligible       Tasks have a concept of "eligibility":
  (just ordered by vruntime)          A task is eligible when its lag ≥ 0
                                      (it has received ≤ its fair share)

EEVDF task parameters:
  - weight (from nice value, same as CFS)
  - request (virtual time quantum)
  - deadline = eligible_time + (request / weight)
  - lag = (ideal_service - actual_service)

Scheduling decision:
  1. Find all eligible tasks (lag ≥ 0)
  2. Among eligible, pick earliest deadline
  3. Run until request exhausted or preempted
```

### 6.3 EEVDF vs CFS Behavior

```
Scenario: Two tasks, T1 (nice 0) and T2 (nice 0)
          T1 is interactive (short bursts), T2 is CPU-bound

CFS behavior:
  Both accumulate vruntime at the same rate
  T1 sleeps → vruntime falls behind
  T1 wakes → lowest vruntime → runs immediately
  But: "how much bonus?" required fragile heuristics

EEVDF behavior:
  T1 has positive lag (received less than fair share)
  T1's deadline is early (short request)
  T1 is eligible (lag ≥ 0) and has earliest deadline
  T1 runs immediately — no heuristics needed

  T2 has zero or negative lag (received fair share)
  T2's deadline is later (longer request)
  T2 runs when T1 is not eligible

Key insight: deadline naturally separates latency-sensitive
tasks (short deadlines) from throughput tasks (long deadlines)
without any special-case heuristics.
```

### 6.4 The latency-nice Concept

EEVDF cleanly supports `latency-nice`: a way for tasks to request lower scheduling latency without changing their CPU share.

```
nice value:         controls CPU share (weight)
latency-nice value: controls request size (deadline urgency)

Example:
  Task A: nice=0, latency-nice=-20 (wants low latency)
    → short request → early deadline → preempts quickly
    → BUT: same weight → same CPU share over time

  Task B: nice=0, latency-nice=19 (throughput-oriented)
    → long request → late deadline → long time slices
    → same weight → same CPU share over time

Both get 50% CPU, but A gets it in frequent short bursts
and B gets it in infrequent long runs.
```

---

## 7. sched_ext — BPF-Programmable Scheduling

### 7.1 Architecture

```
Traditional scheduler:                sched_ext:

Scheduler logic compiled               Scheduler logic in eBPF
into kernel → reboot to change          → load/unload at runtime

kernel/sched/fair.c                     BPF program defines:
  pick_next_task_fair()                   ops.select_cpu()
  enqueue_task_fair()                     ops.enqueue()
  dequeue_task_fair()                     ops.dispatch()
  task_tick_fair()                        ops.running()
                                          ops.stopping()
Fixed policy                              ops.tick()
                                          ops.init_task()
                                          ops.exit_task()
                                        
                                        Hot-reload without reboot!
```

### 7.2 sched_ext Use Cases

| Use case | Custom policy |
|----------|---------------|
| Game server | Pin main thread to fastest core; background threads on efficient cores |
| Database | Prioritize query threads over background compaction |
| Build system | Fair share between build jobs; preempt long compilations for I/O-bound linker |
| Cloud VM | Per-tenant CPU bandwidth enforcement |
| ML training | NUMA-aware scheduling for GPU-feeding threads |

### 7.3 Example sched_ext Scheduler (Simplified)

```c
/* Simplified sched_ext BPF scheduler */
#include <scx/common.bpf.h>

/* Global FIFO dispatch queue */
struct {
    __uint(type, BPF_MAP_TYPE_QUEUE);
    __uint(max_entries, 4096);
    __type(value, s32);  /* task PID */
} dispatch_queue SEC(".maps");

/* Called when a task becomes runnable */
s32 BPF_STRUCT_OPS(simple_enqueue,
                    struct task_struct *p,
                    u64 enq_flags) {
    s32 pid = p->pid;
    bpf_map_push_elem(&dispatch_queue, &pid, 0);
    return 0;
}

/* Called when CPU needs a task to run */
void BPF_STRUCT_OPS(simple_dispatch,
                     s32 cpu, struct task_struct *prev) {
    s32 pid;
    if (bpf_map_pop_elem(&dispatch_queue, &pid) == 0) {
        scx_bpf_dispatch_from_dsq(/* ... */);
    }
}

SEC(".struct_ops")
struct sched_ext_ops simple_ops = {
    .enqueue    = (void *)simple_enqueue,
    .dispatch   = (void *)simple_dispatch,
    .name       = "simple",
};
```

---

## 8. cgroup CPU Controllers

### 8.1 CPU Bandwidth Control (cgroup v2)

```
/sys/fs/cgroup/myapp/cpu.max = "100000 100000"
                                 │        │
                                 │        └─ period (μs): 100ms
                                 └─ quota (μs): 100ms
                                 
                                 → 100% of one CPU

"50000 100000" → 50% of one CPU
"200000 100000" → 200% → 2 full CPUs
"max 100000" → unlimited (default)
```

### 8.2 CPU Weight (Proportional Share)

```
/sys/fs/cgroup/app_a/cpu.weight = 100  (default)
/sys/fs/cgroup/app_b/cpu.weight = 200

When both are CPU-bound:
  app_a gets 100/(100+200) = 33% CPU
  app_b gets 200/(100+200) = 67% CPU

When only app_a is running:
  app_a gets 100% (weight only matters under contention)
```

### 8.3 cpuset: CPU Pinning

```
/sys/fs/cgroup/latency_critical/cpuset.cpus = "0-3"
/sys/fs/cgroup/batch_jobs/cpuset.cpus = "4-15"

Latency-critical tasks can ONLY run on CPUs 0-3
Batch jobs can ONLY run on CPUs 4-15
No interference between the two groups
```

```python
# Python: inspecting cgroup CPU configuration
import os

def read_cgroup_cpu(cgroup_path):
    """Read CPU controller settings for a cgroup."""
    settings = {}
    for f in ['cpu.max', 'cpu.weight', 'cpuset.cpus',
              'cpu.stat', 'cpu.pressure']:
        path = os.path.join(cgroup_path, f)
        if os.path.exists(path):
            with open(path) as fh:
                settings[f] = fh.read().strip()
    return settings

# Example usage
cgroup = '/sys/fs/cgroup'
for name in os.listdir(cgroup):
    full_path = os.path.join(cgroup, name)
    if os.path.isdir(full_path):
        info = read_cgroup_cpu(full_path)
        if info:
            print(f"\n{name}:")
            for k, v in info.items():
                print(f"  {k}: {v}")
```

---

## 9. Priority Inversion Deep Dive

### 9.1 The Problem

```
Three tasks: T_high (priority 99), T_med (priority 50), T_low (priority 10)
T_low holds mutex M

Timeline:
  t=0:  T_low acquires M, starts working
  t=1:  T_high wakes up, tries to acquire M → BLOCKED
  t=2:  T_med wakes up, preempts T_low (higher priority)
  t=3:  T_med runs... and runs... and runs...
  t=?:  T_high is STILL blocked, waiting for T_low
        T_low cannot run because T_med (lower than T_high!)
        is consuming all CPU time

  T_high's effective priority = T_med's priority (INVERSION!)
```

### 9.2 Solutions

**Priority Inheritance (PI):**
```
When T_high blocks on mutex M held by T_low:
  T_low.priority = max(T_low.priority, T_high.priority) = 99
  
Now T_low runs at priority 99:
  T_low preempts T_med
  T_low finishes critical section, releases M
  T_low.priority restored to 10
  T_high acquires M, runs at priority 99
```

**Priority Ceiling Protocol (PCP):**
```
Each mutex has a "ceiling" = highest priority of any task that uses it
When a task acquires mutex M:
  task.priority = max(task.priority, M.ceiling)
  
Advantage: prevents deadlocks (tasks cannot block on nested mutexes
           if ceiling is set correctly)
Disadvantage: requires knowing all users of each mutex at design time
```

### 9.3 Linux Implementation

```c
/* C: Priority Inheritance mutex */
#include <pthread.h>
#include <stdio.h>

int main(void) {
    pthread_mutex_t mutex;
    pthread_mutexattr_t attr;

    pthread_mutexattr_init(&attr);
    /* Enable priority inheritance */
    pthread_mutexattr_setprotocol(&attr, PTHREAD_PRIO_INHERIT);
    pthread_mutex_init(&mutex, &attr);
    pthread_mutexattr_destroy(&attr);

    /* Now if a high-priority thread blocks on this mutex,
       the holder's priority will be boosted */
    pthread_mutex_lock(&mutex);
    printf("Holding PI mutex\n");
    pthread_mutex_unlock(&mutex);

    pthread_mutex_destroy(&mutex);
    return 0;
}
```

### 9.4 rt_mutex in the Linux Kernel

The kernel's `rt_mutex` implements priority inheritance chains:

```
Chain example:
  T1 (prio 99) → blocks on M1 → held by T2 (prio 50)
  T2 (prio 50) → blocks on M2 → held by T3 (prio 10)

PI chain propagation:
  T3.prio boosted to 99 (inherited from T1 via T2)
  T2.prio boosted to 99 (inherited from T1)

When T3 releases M2:
  T3.prio restored to 10
  T2 acquires M2, runs at 99 (still inheriting from T1)
  T2 releases M1
  T2.prio restored to 50
  T1 acquires M1, runs at 99

Maximum chain depth: configurable (default 1024)
```

---

## 10. Performance Analysis and Debugging

### 10.1 Scheduler Tracing with perf

```bash
# Record scheduling events for 10 seconds
perf sched record -- sleep 10

# Show per-task scheduling latency
perf sched latency --sort=max
#  Task              |  Runtime  |  Switches  |  Avg delay  |  Max delay
#  firefox           |  1500 ms  |     3000   |   0.5 ms    |   15 ms
#  kworker/2:0       |    50 ms  |     200    |   0.2 ms    |    3 ms

# Timeline visualization
perf sched timehist
#  Shows when each task ran on which CPU, with timestamps

# CPU utilization map
perf sched map
#  Visual ASCII map of which task ran on which CPU over time
```

### 10.2 schedstat: Per-CPU Statistics

```bash
cat /proc/schedstat
# cpu0 0 0 0 0 0 0 0 123456789 12345 67890
# Fields: version, sched_yield count, schedule() count, ...
#         time spent scheduling, run time, wait time

# Per-task scheduling stats
cat /proc/<pid>/schedstat
# run_time wait_time nr_timeslices
```

### 10.3 Tracing with ftrace

```bash
# Enable scheduler tracepoints
echo 1 > /sys/kernel/debug/tracing/events/sched/sched_switch/enable
echo 1 > /sys/kernel/debug/tracing/events/sched/sched_wakeup/enable

# Read trace
cat /sys/kernel/debug/tracing/trace_pipe | head -20
# Output format:
# <comm>-<pid> [<cpu>] <timestamp>: sched_switch: prev_comm=X prev_pid=N
#   prev_prio=P prev_state=S ==> next_comm=Y next_pid=M next_prio=Q
```

### 10.4 Common Scheduling Problems

**Problem 1: Latency spikes from load balancing**
```bash
# Check migration frequency
perf stat -e sched:sched_migrate_task -a -- sleep 10

# If too many migrations:
# 1. Increase migration cost: /proc/sys/kernel/sched_migration_cost_ns
# 2. Pin latency-sensitive tasks: taskset or cpuset cgroup
# 3. Check NUMA balancing: /proc/sys/kernel/numa_balancing
```

**Problem 2: RT task starvation of normal tasks**
```bash
# Check RT throttling
cat /proc/sys/kernel/sched_rt_runtime_us   # 950000 (95%)
cat /proc/sys/kernel/sched_rt_period_us    # 1000000

# RT tasks can only use 95% of CPU time per second
# 5% is reserved for SCHED_NORMAL (prevents complete starvation)

# If RT tasks are being throttled:
cat /proc/<pid>/sched | grep nr_throttled
```

---

## 11. Q&A

**Q1: Why did Linux switch from O(1) to CFS?**

The O(1) scheduler used heuristics to estimate whether a task was "interactive" (deserves lower latency) or "batch" (can tolerate higher latency). These heuristics broke for many real workloads — desktop users experienced UI freezes while the kernel miscategorized tasks. CFS eliminated heuristics by using a simple, provably fair metric: virtual runtime.

**Q2: Can a SCHED_DEADLINE task preempt a SCHED_FIFO task?**

Yes. The priority hierarchy is: SCHED_DEADLINE > SCHED_FIFO/RR > SCHED_NORMAL. A deadline task always preempts RT and normal tasks. However, SCHED_DEADLINE has admission control (the kernel rejects tasks that would overcommit bandwidth), while SCHED_FIFO does not.

**Q3: What happens when two SCHED_FIFO tasks of the same priority are on the same CPU?**

The first one runs until it voluntarily yields (`sched_yield`), blocks (I/O, mutex), or is preempted by a higher-priority task. The second task waits. There is no time-slicing within the same FIFO priority level. Use SCHED_RR if you want round-robin within the same priority.

**Q4: How does the scheduler handle CPU frequency scaling?**

PELT tracks both utilization (how busy the CPU is) and capacity (maximum compute power). When `schedutil` governor is active, the scheduler directly sets CPU frequency based on utilization:
- utilization > 80% of current frequency → scale up
- utilization < 50% of current frequency → scale down

This is more responsive than the old `ondemand` governor, which polled utilization periodically.

**Q5: What is `sched_yield()` and when should you use it?**

Almost never. `sched_yield()` moves the calling task to the end of the run queue. In CFS, it sets the task's vruntime to the current maximum in the tree. Problems:
- If no other task is runnable, the yielding task just runs again (wasted syscall).
- Can cause priority inversion and latency issues.
- Better alternatives: proper locking (mutex/futex), condition variables, or event-driven design.

The only valid use: cooperative multitasking in real-time contexts where tasks share the same priority and want to explicitly hand off.

**Q6: How does Linux handle CPU hotplug and scheduling?**

When a CPU goes offline (`echo 0 > /sys/devices/system/cpu/cpuN/online`):
1. All tasks on that CPU are migrated to other CPUs.
2. The CPU's runqueue is drained.
3. Timer and softirq processing is moved.
4. The CPU enters a deep idle state.

When it comes back online:
1. The CPU's runqueue is re-initialized.
2. Load balancing will naturally migrate tasks back if needed.
3. Pinned tasks (`taskset`) that were forced off may or may not return.

---

## 12. Hands-On Exercises

### Exercise 1: Red-Black Tree Implementation

Implement a Red-Black Tree in C with insert, delete, and find-minimum operations. Then:
1. Insert 1M random integers.
2. Measure insert/delete/find-min time.
3. Compare with a sorted array (binary search for lookup, shift for insert).
4. Verify the tree maintains all RB invariants after each operation.

### Exercise 2: Scheduler Simulation

Write a Python/Go simulator that models CFS:
1. Create N tasks with different nice values.
2. Implement the vruntime mechanism.
3. Use a heap or balanced BST for the run queue.
4. Simulate 1000 scheduling decisions.
5. Verify that CPU time distribution matches the weight ratios.

```go
// Go: skeleton for CFS simulator
package main

import (
    "container/heap"
    "fmt"
    "math"
)

type Task struct {
    PID      int
    Nice     int
    Weight   float64
    VRuntime float64
    TotalRun float64
}

type RunQueue []*Task

func (rq RunQueue) Len() int            { return len(rq) }
func (rq RunQueue) Less(i, j int) bool  { return rq[i].VRuntime < rq[j].VRuntime }
func (rq RunQueue) Swap(i, j int)       { rq[i], rq[j] = rq[j], rq[i] }
func (rq *RunQueue) Push(x interface{}) { *rq = append(*rq, x.(*Task)) }
func (rq *RunQueue) Pop() interface{} {
    old := *rq
    n := len(old)
    item := old[n-1]
    *rq = old[:n-1]
    return item
}

func niceToWeight(nice int) float64 {
    // Simplified: each nice level = ~1.25x ratio
    return 1024.0 * math.Pow(1.25, float64(-nice))
}

func main() {
    rq := &RunQueue{}
    heap.Init(rq)

    tasks := []*Task{
        {PID: 1, Nice: 0},
        {PID: 2, Nice: 5},
        {PID: 3, Nice: -5},
    }
    for _, t := range tasks {
        t.Weight = niceToWeight(t.Nice)
        heap.Push(rq, t)
    }

    quantum := 1.0 // ms
    for tick := 0; tick < 1000; tick++ {
        if rq.Len() == 0 {
            break
        }
        t := heap.Pop(rq).(*Task)
        delta := quantum * (1024.0 / t.Weight)
        t.VRuntime += delta
        t.TotalRun += quantum
        heap.Push(rq, t)
    }

    for _, t := range tasks {
        fmt.Printf("PID %d (nice %d, weight %.0f): total_run=%.0f ms\n",
            t.PID, t.Nice, t.Weight, t.TotalRun)
    }
}
```

### Exercise 3: Priority Inversion Demo

1. Create three pthreads at priorities 10, 50, 99.
2. Low-priority thread acquires a mutex, does work.
3. High-priority thread wakes and tries to acquire the same mutex.
4. Medium-priority thread wakes and runs CPU-intensive work.
5. Measure how long high-priority thread waits.
6. Enable `PTHREAD_PRIO_INHERIT` and re-measure.

### Exercise 4: cgroup CPU Throttling

```bash
# Create a cgroup with 50% CPU limit
mkdir /sys/fs/cgroup/test
echo "50000 100000" > /sys/fs/cgroup/test/cpu.max
echo $$ > /sys/fs/cgroup/test/cgroup.procs

# Run a CPU-intensive task
stress --cpu 1 --timeout 10 &

# In another terminal:
watch -n 1 cat /sys/fs/cgroup/test/cpu.stat
# Observe: nr_throttled, throttled_usec

# Verify CPU usage is ~50%
top -p $(pgrep stress)
```

### Exercise 5: NUMA-Aware Scheduling

```bash
# Run benchmark on local vs remote NUMA node
numactl --cpunodebind=0 --membind=0 sysbench cpu --threads=4 run
numactl --cpunodebind=0 --membind=1 sysbench cpu --threads=4 run

# The second should be slower due to remote memory access
# Compare: events per second
```

### Exercise 6: sched_ext Exploration

```bash
# Check if sched_ext is available (Linux 6.12+)
grep SCHED_EXT /boot/config-$(uname -r)

# If available, try loading a sample BPF scheduler
# (requires scx-scheds package or building from source)
# scx_simple   — FIFO scheduler
# scx_rusty    — Rust-based scheduler with load balancing
# scx_lavd     — Latency-aware scheduler

# Monitor sched_ext activity
cat /sys/kernel/sched_ext/state
cat /sys/kernel/sched_ext/enable_seq
```

---

## 13. Deep Dive: Wait Queues and Sleep/Wake Mechanisms

### 13.1 Wait Queues

When a task needs to sleep waiting for an event (I/O completion, lock availability, data arrival), it uses a **wait queue**:

```c
/* Kernel wait queue pattern */
/* In driver/subsystem code: */

DECLARE_WAIT_QUEUE_HEAD(my_wq);  /* static wait queue */
int data_ready = 0;

/* Sleeping side (waiting for event): */
wait_event_interruptible(my_wq, data_ready != 0);
/* This macro:
   1. Checks condition (data_ready != 0)
   2. If true: return immediately
   3. If false:
      a. Set task state to TASK_INTERRUPTIBLE
      b. Add task to wait queue
      c. Call schedule() → context switch
      d. When woken: re-check condition
      e. If condition true: remove from queue, continue
      f. If signal: return -ERESTARTSYS
*/

/* Waking side (event occurred): */
data_ready = 1;
wake_up_interruptible(&my_wq);
/* This:
   1. Walks the wait queue
   2. For each waiter: set state to TASK_RUNNING
   3. Waiter is now on the runqueue, will be scheduled
*/
```

### 13.2 Wait Queue Internal Structure

```
Wait Queue Head:
┌──────────────────────────┐
│ spinlock_t lock           │
│ struct list_head task_list│──┐
└──────────────────────────┘  │
                               │
Wait Queue Entry 1:            │
┌──────────────────────────┐◄──┘
│ unsigned int flags        │
│ void *private (task_struct)│
│ wait_queue_func_t func    │ (default or custom wake function)
│ struct list_head entry    │──┐
└──────────────────────────┘  │
                               │
Wait Queue Entry 2:            │
┌──────────────────────────┐◄──┘
│ unsigned int flags        │
│ void *private (task_struct)│
│ wait_queue_func_t func    │
│ struct list_head entry    │──► (back to head for circular list)
└──────────────────────────┘
```

### 13.3 Exclusive vs Non-Exclusive Waiters

```
Scenario: multiple threads waiting on the same condition

Non-exclusive (default):
  wake_up() wakes ALL waiters → thundering herd problem
  All N threads wake up, only 1 finds work, N-1 sleep again
  Cost: O(N) context switches wasted

Exclusive (WQ_FLAG_EXCLUSIVE):
  wake_up() wakes only ONE waiter
  Used by: accept() on shared listening socket
  Prevents thundering herd

Linux socket accept() optimization:
  - Listening socket has exclusive wait queue
  - When connection arrives: wake one thread only
  - epoll EPOLLEXCLUSIVE flag: same concept for event-driven
```

---

## 14. Deep Dive: Scheduler Internals — `schedule()` Function

### 14.1 The schedule() Call Path

```
schedule()  (kernel/sched/core.c)
    │
    ├── __schedule(SM_NONE)
    │       │
    │       ├── rq = this_rq()           # get current CPU's runqueue
    │       ├── prev = rq->curr          # currently running task
    │       ├── rq_lock(rq)              # acquire runqueue lock
    │       │
    │       ├── if (prev->state != TASK_RUNNING)
    │       │       deactivate_task(rq, prev)    # remove from runqueue
    │       │
    │       ├── pick_next_task(rq, prev)  # scheduler class dispatch
    │       │       │
    │       │       ├── Check dl_sched_class    (SCHED_DEADLINE)
    │       │       │   └── pick_next_task_dl()
    │       │       │
    │       │       ├── Check rt_sched_class    (SCHED_FIFO/RR)
    │       │       │   └── pick_next_task_rt()
    │       │       │
    │       │       ├── Check fair_sched_class  (SCHED_NORMAL)
    │       │       │   └── pick_next_task_fair()
    │       │       │       └── rb_first_cached()  # O(1) leftmost
    │       │       │
    │       │       └── Check idle_sched_class  (fallback)
    │       │           └── pick_next_task_idle()
    │       │
    │       ├── if (next != prev)
    │       │       context_switch(rq, prev, next)
    │       │       │
    │       │       ├── switch_mm()     # change address space
    │       │       └── switch_to()     # swap register state
    │       │
    │       └── rq_unlock(rq)
    │
    └── return
```

### 14.2 Scheduler Classes as a Linked List

Linux scheduler classes form a priority chain. `pick_next_task()` walks them in order:

```c
/* From kernel/sched/sched.h */
/* Each scheduler class points to the next lower-priority class */

const struct sched_class stop_sched_class = {  /* highest: stopper */
    .next = &dl_sched_class,
};

const struct sched_class dl_sched_class = {    /* SCHED_DEADLINE */
    .next = &rt_sched_class,
};

const struct sched_class rt_sched_class = {    /* SCHED_FIFO/RR */
    .next = &fair_sched_class,
};

const struct sched_class fair_sched_class = {  /* SCHED_NORMAL (CFS) */
    .next = &idle_sched_class,
};

const struct sched_class idle_sched_class = {  /* lowest: idle */
    .next = NULL,
};

/* Optional: ext_sched_class for sched_ext, inserted between
   fair and idle when a BPF scheduler is loaded */
```

### 14.3 The Optimization: Fast Path

Most of the time, only CFS tasks are runnable. The kernel optimizes:

```c
/* Simplified fast path in pick_next_task() */
static struct task_struct *
__pick_next_task(struct rq *rq, struct task_struct *prev) {
    const struct sched_class *class;
    struct task_struct *p;

    /* Optimization: if no DL/RT tasks, skip directly to fair */
    if (likely(!sched_class_above(rq->nr_running,
                                  &fair_sched_class))) {
        p = pick_next_task_fair(rq, prev, NULL);
        if (p)
            return p;
    }

    /* Slow path: walk all classes */
    for_each_class(class) {
        p = class->pick_next_task(rq);
        if (p)
            return p;
    }

    /* Should never reach here (idle always available) */
    BUG();
}
```

---

## 15. Deep Dive: Timer Subsystem and the Scheduler Tick

### 15.1 Timer Tick Modes

| Mode | Config | Behavior | Use case |
|------|--------|----------|----------|
| Periodic | `HZ=1000` | Timer fires every 1 ms | Simple, predictable |
| Dynamic (tickless) | `NO_HZ_IDLE` | Tick suppressed when CPU idle | Save power |
| Full tickless | `NO_HZ_FULL` | Tick suppressed even when busy (1 task) | Latency-sensitive RT |

### 15.2 What Happens on Each Tick

```
scheduler_tick()  (called from timer interrupt)
    │
    ├── rq->clock update (advance rq-local clock)
    │
    ├── curr->sched_class->task_tick()
    │   │
    │   └── task_tick_fair():
    │       ├── Update vruntime: delta_exec * (NICE_0_LOAD / weight)
    │       ├── Update PELT (load averages)
    │       ├── Check if preemption needed:
    │       │   if (vruntime - leftmost->vruntime > sched_latency)
    │       │       set TIF_NEED_RESCHED on current task
    │       └── Check slice exhaustion
    │
    ├── trigger_load_balance()
    │   └── If balance interval expired: raise SCHED_SOFTIRQ
    │
    ├── Update time accounting (user time, system time, steal time)
    │
    └── perf_event_task_tick() (update sampling counters)
```

### 15.3 TIF_NEED_RESCHED: The Preemption Flag

When the scheduler determines that another task should run:

```
1. Set TIF_NEED_RESCHED in current task's thread_info flags

2. This flag is checked at:
   a. Return from syscall (entry_SYSCALL_64 → check before sysretq)
   b. Return from interrupt (do_IRQ return path)
   c. Preemption points (cond_resched(), might_sleep())
   d. spin_unlock() with CONFIG_PREEMPT

3. When checked and set:
   a. Call schedule()
   b. Context switch to the higher-priority task
   c. Clear TIF_NEED_RESCHED
```

### 15.4 Tickless (NO_HZ) Operation

```
Tickless idle:
  When CPU has no runnable tasks:
  1. Cancel periodic timer
  2. Calculate next event (nearest software timer, RCU callback)
  3. Program one-shot timer for that event
  4. Enter deep idle (C-state)
  5. Wake only when the timer fires or an IRQ arrives

  Benefit: CPU can sleep for milliseconds or seconds
           instead of waking every 1 ms

Tickless running (NO_HZ_FULL):
  When CPU has exactly 1 runnable task:
  1. No need for preemption (nothing to preempt for)
  2. Cancel periodic timer
  3. Task runs uninterrupted
  4. Benefit: zero jitter from timer interrupts
  5. Used for: HFT, real-time control, latency benchmarks
```

---

## 16. Deep Dive: Completely Fair Group Scheduling

### 16.1 Hierarchical Scheduling with cgroups

CFS supports group scheduling: tasks are organized into groups, and fairness applies at each level of the hierarchy.

```
System (100% CPU)
├── cgroup /A  (weight 100)  → 33% CPU
│   ├── Task A1 (nice 0)     → 16.5%
│   └── Task A2 (nice 0)     → 16.5%
│
├── cgroup /B  (weight 200)  → 67% CPU
│   ├── Task B1 (nice 0)     → 22.3%
│   ├── Task B2 (nice 0)     → 22.3%
│   └── Task B3 (nice 0)     → 22.3%
│
└── cgroup /   (root)

Group scheduling ensures:
  Group A gets 33% total (100/300 of total weight)
  Group B gets 67% total (200/300 of total weight)
  
  Within Group A: tasks share equally (50/50)
  Within Group B: tasks share equally (33/33/33)

Without group scheduling:
  All 5 tasks compete equally → each gets 20%
  Group A (2 tasks) gets 40% total
  Group B (3 tasks) gets 60% total
  → Group with more tasks gets more CPU (unfair per-group)
```

### 16.2 Implementation: Nested RB-Trees

```
Per-CPU Runqueue:
┌──────────────────────────────────────────┐
│  Root CFS RQ                              │
│  ┌────────────────────────────────────┐   │
│  │  RB-Tree (group scheduling entities)│   │
│  │  Key: group vruntime                │   │
│  │                                     │   │
│  │  ┌─────────┐    ┌─────────┐        │   │
│  │  │ Group A  │    │ Group B  │        │   │
│  │  │ se_A     │    │ se_B     │        │   │
│  │  └────┬────┘    └────┬────┘        │   │
│  │       │              │              │   │
│  │  ┌────┴────┐    ┌────┴────┐        │   │
│  │  │ CFS RQ  │    │ CFS RQ  │        │   │
│  │  │ for A   │    │ for B   │        │   │
│  │  │         │    │         │        │   │
│  │  │ RB-Tree │    │ RB-Tree │        │   │
│  │  │ [A1,A2] │    │[B1,B2,B3]│       │   │
│  │  └─────────┘    └─────────┘        │   │
│  └────────────────────────────────────┘   │
└──────────────────────────────────────────┘

Scheduling decision:
1. Pick leftmost at root level → Group B (more vruntime credit)
2. Descend into Group B's CFS RQ
3. Pick leftmost → Task B2
4. Run Task B2
5. Update B2's vruntime, then propagate up to Group B's vruntime
```

---

## 17. Deep Dive: Bandwidth Control and Throttling

### 17.1 CFS Bandwidth Control

```
Parameters:
  cpu.max = "quota period"
  
  quota:  microseconds of CPU time per period
  period: the reference period (typically 100ms)

Example: cpu.max = "50000 100000"
  → 50ms of CPU every 100ms = 50% of one core

Enforcement:
  ┌──────────────────────────────────────────────┐
  │  Period 1 (0-100ms)                           │
  │  Task runs:  ████████████░░░░░░░░░░░░░░░░░  │
  │              ←── 50ms ──→←── throttled ──→   │
  │                                               │
  │  Period 2 (100-200ms)                         │
  │  Quota refilled:                              │
  │  Task runs:  ████████████░░░░░░░░░░░░░░░░░  │
  │              ←── 50ms ──→←── throttled ──→   │
  └──────────────────────────────────────────────┘
```

### 17.2 Throttling Debugging

```bash
# Check if a cgroup is being throttled
cat /sys/fs/cgroup/myapp/cpu.stat
# usage_usec 123456789
# user_usec 100000000
# system_usec 23456789
# nr_periods 1234
# nr_throttled 567
# throttled_usec 28350000

# nr_throttled / nr_periods = throttling ratio
# If > 0: task is hitting its CPU limit
# throttled_usec: total time spent throttled

# Common problem: short bursts hit the limit
# Solution: increase period (spreads quota over longer window)
# cpu.max = "50000 200000" instead of "50000 100000"
# Same 25% bandwidth but less bursty throttling
```

---

## 18. Performance Benchmarks Reference

### 18.1 Scheduling Operation Costs

| Operation | Typical cost | Notes |
|-----------|-------------|-------|
| `pick_next_task` (CFS, cached leftmost) | ~50-100 ns | O(1) |
| `enqueue_task` (CFS, RB-tree insert) | ~200-500 ns | O(log n) |
| `dequeue_task` (CFS, RB-tree delete) | ~200-500 ns | O(log n) |
| `schedule()` full path | ~1-5 μs | Includes context switch |
| Load balance check (periodic) | ~1-10 μs | Walks scheduling domains |
| Task migration (cross-CPU) | ~10-50 μs | Includes cache warm-up |
| Task migration (cross-NUMA) | ~50-200 μs | Includes remote memory |
| PELT update | ~50-100 ns | Exponential decay calculation |

### 18.2 Scheduler Tunable Summary

| Tunable | Default | Effect |
|---------|---------|--------|
| `sched_latency_ns` | 6-24 ms | Target preemption latency |
| `sched_min_granularity_ns` | 0.75-3 ms | Min runtime before preemption |
| `sched_wakeup_granularity_ns` | 1-4 ms | Wakeup preemption threshold |
| `sched_migration_cost_ns` | 500 μs | Task considered cache-hot if ran within this time |
| `sched_nr_migrate` | 32 | Max tasks moved per balance |
| `sched_rt_runtime_us` | 950,000 | RT bandwidth limit per period |
| `sched_rt_period_us` | 1,000,000 | RT bandwidth period |
| `sched_child_runs_first` | 0 | If 1, child runs before parent after fork |

---

## 19. Summary Cheat Sheet

```
┌───────────────────────────────────────────────────────────────────┐
│              SCHEDULER DATA STRUCTURES CHEAT SHEET                │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  DATA STRUCTURES                                                  │
│    CFS: Red-Black Tree, key=vruntime, O(1) pick via leftmost     │
│    EEVDF: RB-Tree, key=virtual_deadline, eligible check           │
│    RT: 100 priority queues (bitmap + linked list), O(1) pick     │
│    DL: RB-Tree, key=absolute_deadline, O(log n) pick             │
│                                                                   │
│  PER-CPU DESIGN                                                  │
│    Each CPU has its own struct rq (runqueue)                      │
│    Local operations: only local rq->lock (no cross-CPU locking)  │
│    Migration: lock both source and destination rq                 │
│                                                                   │
│  LOAD BALANCING                                                   │
│    Hierarchical domains: SMT → Core → Socket → NUMA              │
│    Periodic balance: timer-driven, per-domain intervals           │
│    Idle balance: work stealing, cache-warmth priority             │
│    PELT: decaying average for stable load signals                 │
│                                                                   │
│  REAL-TIME                                                       │
│    SCHED_DEADLINE: admission control, CBS, EDF                    │
│    SCHED_FIFO: no quantum, run until yield/block                  │
│    SCHED_RR: quantum-based round robin within priority            │
│    Priority inversion: PI mutexes (PTHREAD_PRIO_INHERIT)          │
│                                                                   │
│  CGROUP CPU CONTROL                                               │
│    cpu.max: bandwidth limit (quota/period)                        │
│    cpu.weight: proportional share (under contention)              │
│    cpuset.cpus: CPU pinning                                       │
│    Group scheduling: nested RB-trees, per-group fairness          │
│                                                                   │
│  MODERN                                                           │
│    EEVDF (6.6+): virtual deadlines, no sleeper heuristics         │
│    sched_ext (6.12+): BPF-programmable scheduling                 │
│    EAS: energy-aware scheduling for heterogeneous CPUs            │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 20. Further Reading

- **Linux kernel source:** `kernel/sched/fair.c` (CFS/EEVDF), `kernel/sched/rt.c`, `kernel/sched/deadline.c`, `kernel/sched/ext.c`
- **"Understanding the Linux Kernel"** by Bovet & Cesati — Chapter 7 (Process Scheduling)
- **"Linux Kernel Development"** by Robert Love — scheduling chapters
- **LWN articles on EEVDF:** Peter Zijlstra's EEVDF patches, 2023
- **sched_ext documentation:** `Documentation/scheduler/sched-ext.rst`
- **"Operating Systems: Three Easy Pieces"** (OSTEP) — scheduling chapters (free online)
- **CFS design document:** `Documentation/scheduler/sched-design-CFS.rst`
- **RT-Preempt wiki:** https://wiki.linuxfoundation.org/realtime/
- **man pages:** `sched(7)`, `sched_setscheduler(2)`, `sched_setattr(2)`, `cpuset(7)`, `cgroups(7)`
- **"A Complete Guide to Linux Process Scheduling"** — Nikita Ishkov, MS thesis
- **Red-Black Trees:** Cormen et al., "Introduction to Algorithms" (CLRS), Chapter 13
- **PELT description:** `Documentation/scheduler/sched-pelt.rst`
- **EAS documentation:** `Documentation/scheduler/sched-energy.rst`

- **Linux kernel source:** `kernel/sched/fair.c` (CFS/EEVDF), `kernel/sched/rt.c`, `kernel/sched/deadline.c`, `kernel/sched/ext.c`
- **"Understanding the Linux Kernel"** by Bovet & Cesati — Chapter 7 (Process Scheduling)
- **"Linux Kernel Development"** by Robert Love — scheduling chapters
- **LWN articles on EEVDF:** Peter Zijlstra's EEVDF patches, 2023
- **sched_ext documentation:** `Documentation/scheduler/sched-ext.rst`
- **"Operating Systems: Three Easy Pieces"** (OSTEP) — scheduling chapters (free online)
- **CFS design document:** `Documentation/scheduler/sched-design-CFS.rst`
- **RT-Preempt wiki:** https://wiki.linuxfoundation.org/realtime/
- **man pages:** `sched(7)`, `sched_setscheduler(2)`, `sched_setattr(2)`, `cpuset(7)`, `cgroups(7)`
- **"A Complete Guide to Linux Process Scheduling"** — Nikita Ishkov, MS thesis
- **Red-Black Trees:** Cormen et al., "Introduction to Algorithms" (CLRS), Chapter 13

---

## Exercises

### Exercise 1 — Observe CFS/EEVDF vruntime in real time

**Setup:** Open two terminals. In terminal A, launch a CPU-bound workload: `stress-ng --cpu 4 --timeout 60`. In terminal B, observe scheduler state.

**Steps:**
1. Run `cat /proc/<PID>/sched` for one of the stress-ng workers. Record the `vruntime`, `exec_start`, and `nr_switches` fields.
2. Run the same command 5 seconds later. Calculate the vruntime delta.
3. Compare two workers with different `nice` values: `renice -n 10 -p <PID1>` and `renice -n -5 -p <PID2>`.
4. Observe how vruntime diverges — the high-nice process accumulates vruntime faster.

**Expected output:** The nice-10 process should show roughly 3x the vruntime growth rate compared to the nice -5 process (weight ratio ~3:1 for a 15-nice-level gap).

### Exercise 2 — Trace scheduler decisions with ftrace

**Setup:** Requires root. Enable the `sched_switch` tracepoint.

**Steps:**
1. `echo 1 > /sys/kernel/debug/tracing/events/sched/sched_switch/enable`
2. `echo 1 > /sys/kernel/debug/tracing/tracing_on`
3. Run a mixed workload: `stress-ng --cpu 2 --io 2 --timeout 10`
4. `cat /sys/kernel/debug/tracing/trace | head -200`
5. Identify: (a) which tasks preempt which, (b) the `prev_state` codes (R, S, D), (c) whether migration across CPUs occurs.
6. Disable tracing: `echo 0 > /sys/kernel/debug/tracing/tracing_on`

**Expected output:** Trace lines showing `prev_comm`, `next_comm`, CPU IDs, and state transitions. CPU-bound tasks should show `R->R` preemptions; IO-bound tasks should show `S->R` wakeups.

### Exercise 3 — PELT load tracking via /proc

**Setup:** A system with 4+ cores.

**Steps:**
1. Start `stress-ng --cpu 1 --timeout 30` on a single core (use `taskset -c 0`).
2. Read `/proc/<PID>/sched` and note the `avg.load_avg`, `avg.runnable_avg`, and `avg.util_avg` fields.
3. After 10 seconds, read again. The PELT signals should have converged.
4. Kill the workload. Read the sched file of a different, idle process on the same core.
5. Compare: the idle process should show near-zero load/util averages; the stressed process should show values near 1024 (max scale).

**Expected output:** `util_avg` for the CPU-bound task should approach 1024; after killing it, the per-CPU `cpu.util_avg` (visible via `cat /sys/kernel/debug/sched/debug`) should decay exponentially.

### Exercise 4 — Compare scheduling policies with chrt

**Setup:** Two terminal sessions, root access.

**Steps:**
1. Write a small C program that spins for 2 seconds while calling `clock_gettime(CLOCK_MONOTONIC)` in a tight loop, printing wall time vs CPU time at the end.
2. Run under default SCHED_OTHER: `./spin`
3. Run under SCHED_FIFO priority 50: `chrt -f 50 ./spin`
4. Run under SCHED_DEADLINE: `chrt -d --sched-runtime 5000000 --sched-deadline 10000000 --sched-period 10000000 ./spin`
5. Compare: SCHED_FIFO should show wall == CPU time (no preemption). SCHED_DEADLINE should show exactly 50% utilisation (5ms runtime / 10ms period).

**Expected output:** SCHED_OTHER spin: wall ~2s, CPU ~2s but with jitter from preemption. SCHED_FIFO: wall == CPU, no jitter. SCHED_DEADLINE: wall ~4s, CPU ~2s (throttled to 50%).

### Exercise 5 — Build and load a sched_ext BPF scheduler

**Setup:** Kernel 6.12+ with `CONFIG_SCHED_CLASS_EXT=y`. Install `scx` tools from https://github.com/sched-ext/scx.

**Steps:**
1. Clone the scx repository: `git clone https://github.com/sched-ext/scx.git && cd scx`
2. Build the example schedulers: `meson setup build && cd build && meson compile`
3. Load `scx_simple` (round-robin BPF scheduler): `sudo ./scx_simple`
4. In another terminal, run `stress-ng --cpu 4 --timeout 20` and observe behaviour via `sudo bpftool prog list` and `dmesg | grep sched_ext`.
5. Unload: press Ctrl-C. The kernel falls back to the default scheduler.
6. Compare latency: run `cyclictest -p 80 -t 4 -D 10` before and after loading `scx_simple`. Note the max latency difference.

**Expected output:** `scx_simple` loads successfully, `bpftool` shows the attached BPF program, and `dmesg` confirms sched_ext activation. Latency under `scx_simple` will likely be higher than default EEVDF for real-time workloads because it lacks priority awareness.

---

## Readings and References

### Official documentation
- **CFS Scheduler** — Design document for the Completely Fair Scheduler. <https://docs.kernel.org/scheduler/sched-design-CFS.html> (retrieved: 2026-05-29)
- **EEVDF Scheduler** — Kernel documentation for the Earliest Eligible Virtual Deadline First scheduler (Linux 6.6+). <https://docs.kernel.org/scheduler/sched-eevdf.html> (retrieved: 2026-05-29)
- **sched_ext (Extensible Scheduler Class)** — BPF-programmable scheduling policies (Linux 6.12+). <https://www.kernel.org/doc/html/v6.12/scheduler/sched-ext.html> (retrieved: 2026-05-29)
- **sched_ext example schedulers** — README and usage for scx tools. <https://github.com/sched-ext/scx> (retrieved: 2026-05-29)
- **RT-Preempt wiki** — PREEMPT_RT real-time Linux patch set. <https://wiki.linuxfoundation.org/realtime/> (retrieved: 2026-05-29)

### Books
- Bovet, D. & Cesati, M., *Understanding the Linux Kernel*, 3rd ed., O'Reilly, 2005.
- Love, R., *Linux Kernel Development*, 3rd ed., Addison-Wesley, 2010.
- Arpaci-Dusseau, R. & Arpaci-Dusseau, A., *Operating Systems: Three Easy Pieces* (OSTEP), free online at <https://pages.cs.wisc.edu/~remzi/OSTEP/> (retrieved: 2026-05-29).
- Cormen, T., Leiserson, C., Rivest, R. & Stein, C., *Introduction to Algorithms* (CLRS), 4th ed., MIT Press, 2022.

### Papers and articles
- Zijlstra, P., "An EEVDF CPU Scheduler for Linux", LWN.net, 2023. <https://lwn.net/Articles/925371/>
- Linux Magazine, "A Fair Slice — EEVDF scheduler deep dive", Issue 301, 2025. <https://www.linux-magazine.com/Issues/2025/301/EEVDF>
- Ishkov, N., "A Complete Guide to Linux Process Scheduling", M.S. Thesis, University of Tampere, 2015.
- Igalia blog, "sched_ext: a BPF-extensible scheduler class (Part 1)", 2024. <https://blogs.igalia.com/changwoo/sched-ext-a-bpf-extensible-scheduler-class-part-1/>

---

## Cross-References

| Module | Relationship |
|---|---|
| [01.1 — OS Internals: Processes & Memory](01_OS_Internals_Processes_Memory.md) | Parent module covering process lifecycle, context switching, and memory fundamentals that the scheduler builds upon |
| [01.1.a — CPU / Kernel Boundary](01_a_CPU_Kernel_Boundary.md) | Syscall and interrupt paths that trigger scheduler invocations (`schedule()`, `preempt_schedule_irq()`) |
| [01.1.c — Memory Management Algorithms](01_c_Memory_Management_Algorithms.md) | NUMA-aware allocation interacts with scheduler load balancing and task placement decisions |
| [01.1.d — File Systems & Storage](01_d_File_Systems_Storage.md) | I/O-bound scheduling behaviour, `io_uring` completion-driven wakeups, and the I/O scheduler layer |
| [02 — Networking: TCP/IP Deep Dive](02_Networking_TCP_IP_Deep_Dive.md) | Network softirq processing and NAPI polling interact with scheduler preemption and CPU affinity |
| [03 — Advanced Data Structures & Algorithms](03_Advanced_Data_Structures_Algorithms.md) | Red-Black trees, augmented trees, and priority queues used as scheduler runqueue structures |

---

## Glossary

| Term | Definition |
|---|---|
| **vruntime** | Virtual runtime — a weighted measure of CPU time consumed by a task; used by CFS/EEVDF to determine fairness |
| **EEVDF** | Earliest Eligible Virtual Deadline First — the Linux scheduler (6.6+) that replaced CFS, adding deadline-based task selection |
| **CFS** | Completely Fair Scheduler — the Linux fair scheduler (2.6.23–6.5) using a red-black tree ordered by vruntime |
| **sched_ext** | Extensible scheduler class (Linux 6.12+) allowing scheduling policies to be implemented as BPF programs |
| **PELT** | Per-Entity Load Tracking — exponentially weighted moving average of task utilisation, runnable time, and load |
| **EAS** | Energy-Aware Scheduling — scheduler feature that places tasks on the most energy-efficient CPU in heterogeneous (big.LITTLE) systems |
| **Red-Black Tree** | Self-balancing binary search tree guaranteeing O(log n) insert, delete, and lookup; used for CFS/EEVDF runqueues |
| **nice value** | User-space priority hint (range -20 to +19) that maps to a scheduler weight, affecting vruntime accumulation rate |
| **SCHED_DEADLINE** | Linux scheduling policy implementing CBS (Constant Bandwidth Server) for hard real-time tasks with runtime/deadline/period parameters |
| **SCHED_FIFO** | Real-time scheduling policy where the highest-priority runnable task runs until it blocks or yields; no time-slicing |
| **runqueue (rq)** | Per-CPU data structure holding all runnable tasks for that processor, containing sub-queues for each scheduling class |
| **load balancing** | Periodic kernel mechanism that migrates tasks between per-CPU runqueues to equalise load across the system |
| **time slice (quantum)** | The maximum continuous CPU time a task receives before the scheduler considers preemption; derived from `sched_min_granularity_ns` |
| **preemption** | Involuntary suspension of a running task so the scheduler can dispatch a higher-priority or more-eligible task |
| **cgroup bandwidth** | Control-group mechanism (`cpu.max`) that throttles a group's CPU consumption to a configured quota per period |
