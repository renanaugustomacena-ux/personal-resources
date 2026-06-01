---
corso: "SWE Masterclass"
fase: "1 — Foundations"
modulo: "01.1"
titolo: "Operating Systems Internals — Process & Memory Management"
versione: "Linux 6.x"
livello: "Advanced"
prerequisiti:
  - "C programming and pointer arithmetic"
  - "Basic understanding of computer architecture (registers, caches, RAM)"
  - "Familiarity with Linux command line and shell usage"
obiettivi:
  - "Explain the lifecycle of a Linux process from fork() through exit(), including task_struct internals"
  - "Trace virtual-to-physical address translation through multi-level page tables and the TLB"
  - "Compare CFS, EEVDF, and real-time scheduling policies and predict their behaviour under contention"
  - "Evaluate trade-offs among kernel memory allocators (slab, buddy, SLUB) and userspace allocators (glibc ptmalloc, jemalloc, tcmalloc)"
  - "Use cgroups v2, namespaces, and capabilities to isolate and constrain processes"
tag: [os-internals, processes, memory-management, scheduling, linux-kernel, virtual-memory, cgroups, namespaces]
---

# Module 1.1: Operating Systems Internals — Process & Memory Management

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Explain the lifecycle of a Linux process from fork() through exit(), including task_struct internals
> - Trace virtual-to-physical address translation through multi-level page tables and the TLB
> - Compare CFS, EEVDF, and real-time scheduling policies and predict their behaviour under contention
> - Evaluate trade-offs among kernel memory allocators (slab, buddy, SLUB) and userspace allocators (glibc ptmalloc, jemalloc, tcmalloc)
> - Use cgroups v2, namespaces, and capabilities to isolate and constrain processes

> **Course:** SWE Masterclass · Phase 1 · Module 01.1 · **Last updated:** 2026-05-22

## Guiding ideas
1. **Process vs thread vs lightweight thread (goroutine, async task).** Different abstractions, different costs.
2. **Virtual memory + page tables: foundation for isolation.**
3. **Scheduling: CFS (Linux), MLFQ, CFS replacement (sched_ext) 2024+.**
4. **Memory allocators: slab/buddy/jemalloc/tcmalloc trade-offs.**

---

## 1. Process Fundamentals

### 1.1 What Is a Process?

A process is the OS abstraction for a running program. It bundles:
- An address space (virtual memory mappings)
- One or more threads of execution
- Open file descriptors
- Signal handlers and disposition
- Credentials (UID, GID, capabilities)
- Resource limits (rlimits)
- Scheduling state

The kernel represents each process with a **task_struct** (Linux), which is approximately 6-8 KB on a 64-bit kernel. Every thread is also a `task_struct`; Linux makes no internal distinction between processes and threads at the scheduler level.

### 1.2 Process Lifecycle

```
                      fork()
  CREATED ──────────────────────► READY
     │                              │
     │                              │ schedule()
     │                              ▼
     │                           RUNNING ◄──────── preempt / wake
     │                            │   │
     │               exit()       │   │  wait for I/O / sleep
     │                ▼           │   ▼
     │             ZOMBIE      BLOCKED / SLEEPING
     │               │              │
     │    wait()     │              │  I/O complete / signal
     │       ▼       │              │
     └───► DEAD ◄────┘              └────► READY
```

**State details (Linux `task_struct->__state`):**

| State | Macro | Meaning |
|-------|-------|---------|
| Running | `TASK_RUNNING` | On CPU or in run queue |
| Interruptible sleep | `TASK_INTERRUPTIBLE` | Waiting; wakes on signal |
| Uninterruptible sleep | `TASK_UNINTERRUPTIBLE` | Waiting; ignores signals (D state) |
| Stopped | `__TASK_STOPPED` | SIGSTOP / ptrace |
| Zombie | `EXIT_ZOMBIE` | Exited, waiting for parent `wait()` |
| Dead | `EXIT_DEAD` | Final cleanup |

### 1.3 Process Creation: `fork()` and `clone()`

**Traditional `fork()`:**
1. Kernel allocates new `task_struct`.
2. Copies the parent's page table entries but marks all pages **Copy-on-Write (CoW)**.
3. Copies file descriptor table (references only; underlying `struct file` is shared).
4. Child gets PID, parent gets child's PID as return value; child gets 0.

**Cost of fork:**
- On modern Linux with CoW, `fork()` costs roughly 50-200 microseconds for a typical process. The actual data pages are not copied until one side writes to them.
- `vfork()` is cheaper (shares address space until `exec`) but dangerous — the parent is suspended.

**`clone()` — the real system call:**
```
clone(flags, stack, ptid, ctid, regs)
```
`fork()` and `pthread_create()` both call `clone()` with different flags:

| Flag | Effect |
|------|--------|
| `CLONE_VM` | Share address space (threads) |
| `CLONE_FS` | Share filesystem info (cwd, root) |
| `CLONE_FILES` | Share file descriptor table |
| `CLONE_SIGHAND` | Share signal handlers |
| `CLONE_THREAD` | Same thread group (same PID to user) |
| `CLONE_NEWNS` | New mount namespace (containers) |
| `CLONE_NEWPID` | New PID namespace (containers) |
| `CLONE_NEWNET` | New network namespace (containers) |

**Threads vs processes is just a question of which flags you pass to `clone()`.**

### 1.4 The `exec()` Family

After `fork()`, the child typically calls `execve()` to replace its image:
1. Kernel parses the ELF binary header.
2. Maps `.text`, `.data`, `.bss` segments into the address space.
3. Sets up the stack with `argc`, `argv`, `envp`.
4. Sets the instruction pointer to the ELF entry point (usually `_start` in libc).
5. Old mappings are destroyed.

```c
/* C: classic fork-exec pattern */
#include <unistd.h>
#include <sys/wait.h>
#include <stdio.h>

int main(void) {
    pid_t pid = fork();
    if (pid < 0) {
        perror("fork");
        return 1;
    }
    if (pid == 0) {
        /* Child: replace with /bin/ls */
        char *args[] = {"ls", "-la", NULL};
        execve("/bin/ls", args, NULL);
        /* Only reached on error */
        perror("execve");
        _exit(127);
    }
    /* Parent: wait for child */
    int status;
    waitpid(pid, &status, 0);
    if (WIFEXITED(status))
        printf("Child exited with %d\n", WEXITSTATUS(status));
    return 0;
}
```

### 1.5 Zombie and Orphan Processes

**Zombie:** The child has exited but the parent has not called `wait()`. The `task_struct` remains so the kernel can deliver the exit status. Zombies consume a PID slot and a small amount of kernel memory (~400 bytes) but no user-space resources.

**Orphan:** The parent exits before the child. The child is re-parented to `init` (PID 1) or a subreaper (`prctl(PR_SET_CHILD_SUBREAPER)`). The subreaper then reaps zombies.

**Troubleshooting zombie accumulation:**
```bash
# Find zombies
ps aux | awk '$8 == "Z"'

# Find the parent that is not reaping
ps -eo pid,ppid,stat,comm | grep ' Z'
# The PPID column tells you which process is leaking zombies

# strace the parent to see if it calls wait()
strace -p <PPID> -e trace=wait4
```

---

## 2. Threads and Lightweight Processes

### 2.1 POSIX Threads (pthreads)

Linux implements pthreads as kernel threads via `clone(CLONE_VM | CLONE_FILES | CLONE_FS | CLONE_SIGHAND | CLONE_THREAD, ...)`. Each thread:
- Has its own stack (default 8 MB, configurable via `pthread_attr_setstacksize`)
- Has its own `task_struct` (kernel-scheduled)
- Shares heap, globals, file descriptors with other threads in the group

```
┌──────────────────────────────────────────────────────┐
│                  Process Address Space                │
│                                                      │
│  ┌──────┐  ┌──────┐  ┌──────┐     Shared:           │
│  │Stack │  │Stack │  │Stack │     - .text (code)     │
│  │  T0  │  │  T1  │  │  T2  │     - .data / .bss    │
│  │      │  │      │  │      │     - heap             │
│  │  │   │  │  │   │  │  │   │     - mmap region      │
│  │  ▼   │  │  ▼   │  │  ▼   │     - file descriptors │
│  └──────┘  └──────┘  └──────┘                        │
│                                                      │
│  ┌────────────────────────────────┐                  │
│  │          Heap (shared)         │                  │
│  └────────────────────────────────┘                  │
│  ┌────────────────────────────────┐                  │
│  │     .data / .bss (shared)      │                  │
│  └────────────────────────────────┘                  │
│  ┌────────────────────────────────┐                  │
│  │       .text (shared, r-x)      │                  │
│  └────────────────────────────────┘                  │
└──────────────────────────────────────────────────────┘
```

### 2.2 Thread vs Process Cost Comparison

| Operation | Process (`fork`) | Thread (`pthread_create`) |
|-----------|------------------|---------------------------|
| Address space | New (CoW) | Shared |
| Page table | Duplicated | Shared |
| File descriptors | Copied (refs) | Shared |
| Creation time | ~50-200 μs | ~10-30 μs |
| Context switch | ~3-5 μs (TLB flush) | ~1-2 μs (no TLB flush) |
| Isolation | Full | None (one thread crash kills all) |
| Communication | IPC needed | Shared memory (direct) |

### 2.3 Goroutines and Green Threads

Go, Erlang, and async runtimes (Tokio in Rust, asyncio in Python) use **M:N scheduling**: M user-level tasks multiplexed onto N kernel threads.

**Go runtime specifics:**
- Goroutine stack starts at 2-8 KB (grows dynamically via stack copying).
- Go scheduler (GMP model): Goroutines (G) run on machine threads (M) attached to processors (P).
- Context switch between goroutines is ~100-200 ns (vs ~1-5 μs for kernel threads).
- No kernel involvement for goroutine switches — purely userspace.

```
GMP Model:
                                       ┌─────┐
                                   ┌──►│  G  │ (goroutine)
         ┌──────┐   ┌──────┐      │   └─────┘
Kernel   │  M0  │──►│  P0  │──────┤
Thread   └──────┘   └──────┘      │   ┌─────┐
                    (processor)   └──►│  G  │
                                      └─────┘
         ┌──────┐   ┌──────┐
Kernel   │  M1  │──►│  P1  │──────►┌─────┐
Thread   └──────┘   └──────┘       │  G  │
                                   └─────┘

         Global Run Queue: [G, G, G, ...]
         Local Run Queues: P0:[G,G], P1:[G]
         
Work stealing: if P1's queue is empty, steal from P0.
```

```go
// Go: spawning goroutines
package main

import (
    "fmt"
    "runtime"
    "sync"
)

func main() {
    fmt.Println("CPUs:", runtime.NumCPU())
    fmt.Println("GOMAXPROCS:", runtime.GOMAXPROCS(0))

    var wg sync.WaitGroup
    for i := 0; i < 100000; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            // Each goroutine uses ~2-8 KB stack
            _ = id * id
        }(i)
    }
    wg.Wait()
    fmt.Println("All goroutines done")
}
```

---

## 3. Process Scheduling: The Linux CFS (Completely Fair Scheduler)

### 3.1 Core Concept: Ideal Multi-Tasking

CFS aims to model an "ideal, precise multi-tasking CPU". On such hardware, if 2 processes run, each gets exactly 50% power instantly. On real hardware, we must time-slice.

### 3.2 The vruntime Mechanism

Instead of fixed time slices, CFS tracks how long a task *has run*.

**Virtual Runtime (`vruntime`):**
- `vruntime += delta_exec * (NICE_0_LOAD / task_load_weight)`
- Lower priority tasks (high `nice`) gain `vruntime` faster → pushed to the back sooner.
- Higher priority tasks (low `nice`) gain `vruntime` slower → run longer before catching up.

**Nice value to weight mapping (kernel/sched/core.c):**

| nice | weight | ratio to nice 0 |
|------|--------|-----------------|
| -20 | 88761 | 27.5x |
| -10 | 9548 | 2.96x |
| 0 | 1024 | 1.0x |
| 10 | 110 | 0.107x |
| 19 | 15 | 0.0146x |

Each nice level represents roughly a 10% change in CPU share (1.25x ratio between adjacent levels).

### 3.3 Data Structure: Red-Black Tree

The run-queue is not a queue; it is a **time-ordered Red-Black Tree**.

```
                    ┌───────────┐
                    │ vruntime  │
                    │   500     │ (root, black)
                    └─────┬─────┘
                     ╱         ╲
            ┌───────────┐  ┌───────────┐
            │ vruntime  │  │ vruntime  │
            │   300     │  │   700     │ (black)
            └─────┬─────┘  └─────┬─────┘
             ╱         ╲        ╱
    ┌───────────┐ ┌───────────┐ ┌───────────┐
    │ vruntime  │ │ vruntime  │ │ vruntime  │
    │   200     │ │   400     │ │   600     │ (red)
    └───────────┘ └───────────┘ └───────────┘
    
    ▲ leftmost (next to run)          rightmost ►
    
    pick_next_task() → O(1) via cached leftmost pointer
    enqueue/dequeue → O(log n) for tree rebalancing
```

**Key:** `vruntime`.
**Leftmost Node:** The task with the lowest `vruntime` — always the next task to run.
**Complexity:** Insert/Delete/Search is **O(log N)**.

### 3.4 Granularity & Latency Tunables

| Sysctl | Default | Meaning |
|--------|---------|---------|
| `sched_latency_ns` | 6-24 ms | Period in which all runnable tasks get a turn |
| `sched_min_granularity_ns` | 0.75-3 ms | Minimum run time before preemption |
| `sched_wakeup_granularity_ns` | 1-4 ms | Threshold for preempting on wakeup |
| `sched_nr_migrate` | 32 | Max tasks to move per load-balance pass |

When the number of runnable tasks exceeds `sched_latency / min_granularity`, the scheduler uses `nr_running * min_granularity` as the effective period.

### 3.5 EEVDF — CFS Replacement (Linux 6.6+)

The **Earliest Eligible Virtual Deadline First (EEVDF)** scheduler replaced CFS:
- Each task has a virtual deadline: `deadline = eligible_time + (request / weight)`.
- The scheduler picks the eligible task with the earliest deadline.
- Eliminates the "sleeper bonus" hacks in CFS that caused latency jitter.
- Still uses a red-black tree, but keyed on deadline instead of vruntime.

### 3.6 Real-Time Scheduling Classes

Linux supports three scheduling policies beyond `SCHED_NORMAL`:

| Policy | Class | Behavior |
|--------|-------|----------|
| `SCHED_FIFO` | RT | Run until voluntary yield or higher-prio RT preempts |
| `SCHED_RR` | RT | Like FIFO but with time quantum (default 100 ms) |
| `SCHED_DEADLINE` | DL | Earliest Deadline First with admission control |

**Priority hierarchy:** `SCHED_DEADLINE` > `SCHED_FIFO/RR` > `SCHED_NORMAL`

```c
/* C: setting real-time priority */
#include <sched.h>
#include <stdio.h>

int main(void) {
    struct sched_param sp = { .sched_priority = 50 };

    /* Set calling thread to SCHED_FIFO priority 50 (1-99) */
    if (sched_setscheduler(0, SCHED_FIFO, &sp) < 0) {
        perror("sched_setscheduler");
        return 1;
    }
    printf("Now running as SCHED_FIFO priority %d\n", sp.sched_priority);

    /* CPU-intensive work here */
    return 0;
}
```

### 3.7 sched_ext — BPF-Programmable Scheduling (Linux 6.12+)

`sched_ext` allows loading custom scheduling policies as eBPF programs at runtime:
- Define `ops.select_cpu()`, `ops.enqueue()`, `ops.dispatch()` callbacks in BPF.
- Hot-reload scheduling policy without rebooting.
- Used by Meta for custom scheduling in production data centers.
- Enables workload-specific policies (e.g., game server with latency-sensitive main thread).

---

## 4. Context Switching Internals

When the scheduler picks a new task, a **context switch** occurs. This is pure overhead.

### 4.1 The Full Sequence

```
Timer IRQ / Syscall return
         │
         ▼
┌─────────────────────────────────────────────┐
│  1. Enter kernel mode (if not already)      │
│     - Save user registers to kernel stack   │
│     - Set CPL = 0                           │
├─────────────────────────────────────────────┤
│  2. schedule() → pick_next_task()           │
│     - Walk scheduling classes in priority   │
│     - DL → RT → CFS → IDLE                 │
├─────────────────────────────────────────────┤
│  3. context_switch()                        │
│     a. switch_mm_irqs_off()                 │
│        - Load new CR3 (page table root)     │
│        - TLB flush (unless PCID used)       │
│     b. switch_to()                          │
│        - Save callee-saved regs (RBX, RBP,  │
│          R12-R15, RSP) to old task stack     │
│        - Load callee-saved regs from new    │
│          task stack                          │
│        - Switch kernel stack pointer         │
├─────────────────────────────────────────────┤
│  4. Restore FPU / SSE / AVX state           │
│     - Lazy FPU: only restore if task uses   │
│       FPU (handled via #NM exception)       │
│     - Eager FPU (modern default): always    │
│       save/restore via XSAVE/XRSTOR        │
├─────────────────────────────────────────────┤
│  5. Return to userspace                     │
│     - IRET or SYSRET                        │
│     - Restore user registers from stack     │
│     - CPL = 3                               │
└─────────────────────────────────────────────┘
```

### 4.2 Context Switch Costs

| Component | Typical cost | Notes |
|-----------|-------------|-------|
| Register save/restore | ~100-300 ns | Minimal |
| CR3 reload (TLB flush) | ~1-3 μs | Dominates inter-process switch |
| PCID (Process Context ID) | avoids TLB flush | Tags TLB entries with 12-bit ASID |
| FPU/AVX-512 state | ~200-500 ns | AVX-512 state is 2 KB |
| Cache pollution | variable | Cold cache lines after switch |
| Kernel page table isolation (KPTI) | +0.5-2 μs | Meltdown mitigation; two CR3 loads |

**Measuring context switch cost:**

```c
/* C: measure context switch via pipe ping-pong */
#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include <sys/wait.h>

#define ITERATIONS 100000

int main(void) {
    int p1[2], p2[2];
    pipe(p1);
    pipe(p2);
    char buf;

    pid_t pid = fork();
    if (pid == 0) {
        /* Child: read from p1, write to p2 */
        for (int i = 0; i < ITERATIONS; i++) {
            read(p1[0], &buf, 1);
            write(p2[1], &buf, 1);
        }
        _exit(0);
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < ITERATIONS; i++) {
        write(p1[1], "x", 1);
        read(p2[0], &buf, 1);
    }

    clock_gettime(CLOCK_MONOTONIC, &end);
    waitpid(pid, NULL, 0);

    double elapsed = (end.tv_sec - start.tv_sec) * 1e9 +
                     (end.tv_nsec - start.tv_nsec);
    printf("Per round-trip: %.0f ns\n", elapsed / ITERATIONS);
    printf("Per context switch: ~%.0f ns (approx)\n",
           elapsed / ITERATIONS / 2);
    return 0;
}
```

### 4.3 PCID (Process Context Identifiers)

Without PCID, every CR3 write flushes the entire TLB. With PCID:
- Each address space gets a 12-bit tag (up to 4096 concurrent contexts).
- TLB entries are tagged with the PCID; entries from other contexts are not flushed.
- When PCID space runs out, the kernel falls back to full TLB flush.
- INVPCID instruction allows selective flushing.

This is critical for mitigating the KPTI (Kernel Page Table Isolation) overhead added for Meltdown.

---

## 5. Virtual Memory & Paging (x86_64)

Processes see a flat, continuous virtual memory space. The CPU (MMU) translates this to fragmented physical RAM.

### 5.1 Virtual Address Space Layout (Linux x86_64)

```
0xFFFFFFFF FFFFFFFF ┌───────────────────────────┐
                    │   Kernel Space (upper)     │ 128 TB
                    │   - Direct mapping          │
                    │   - vmalloc area             │
                    │   - kernel text/data         │
0xFFFF8000 00000000 ├───────────────────────────┤
                    │   ████████████████████████  │ Non-canonical
                    │   ████ Hole (unused) ████  │ (SIGSEGV on access)
                    │   ████████████████████████  │
0x00007FFF FFFFFFFF ├───────────────────────────┤
                    │   Stack (grows down)        │
                    │        ↓ ↓ ↓               │
                    │                             │
                    │   mmap region               │
                    │   (shared libs, anon maps)  │
                    │                             │
                    │        ↑ ↑ ↑               │
                    │   Heap (grows up, brk)      │
                    │                             │
                    │   BSS  (uninitialized data) │
                    │   Data (initialized data)   │
                    │   Text (code, read-execute) │
0x00000000 00400000 │   ELF load address          │
                    │   [guard page / NULL trap]   │
0x00000000 00000000 └───────────────────────────┘
```

### 5.2 4-Level Paging Walk (Standard x86_64)

A virtual address is 48 bits effective (canonical form). The MMU walks four tables:

```
  63     48 47   39 38   30 29   21 20   12 11    0
 ┌────────┬───────┬───────┬───────┬───────┬────────┐
 │ sign   │ PML4  │ PDPT  │  PD   │  PT   │ Offset │
 │ extend │ index │ index │ index │ index │        │
 └────────┴───┬───┴───┬───┴───┬───┴───┬───┴────────┘
              │       │       │       │
              ▼       ▼       ▼       ▼
           ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
   CR3 ──►│PML4 │→│PDPT │→│ PD  │→│ PT  │→ Physical Frame
           │Entry│ │Entry│ │Entry│ │Entry│    + Offset
           └─────┘ └─────┘ └─────┘ └─────┘
```

1. **PML4 (Page Map Level 4):** Bits 47-39 index into this table. Points to PDPT.
2. **PDPT (Page Directory Pointer Table):** Bits 38-30. Points to Page Directory.
3. **PD (Page Directory):** Bits 29-21. Points to Page Table.
4. **PT (Page Table):** Bits 20-12. Points to Physical Page Frame (4 KB).
5. **Offset:** Bits 11-0. Exact byte in the 4 KB page.

**5-Level Paging (LA57, optional):** Adds PML5 for 57-bit virtual addresses (128 PB), needed for machines with > 64 TB physical RAM.

### 5.3 Page Table Entry Flags

Each PTE is 8 bytes (64 bits) with these key flags:

| Bit | Name | Meaning |
|-----|------|---------|
| 0 | Present (P) | Page is in physical memory |
| 1 | Read/Write (R/W) | 0 = read-only, 1 = writable |
| 2 | User/Supervisor (U/S) | 0 = kernel-only, 1 = user-accessible |
| 3 | Write-Through (PWT) | Page-level cache policy |
| 4 | Cache Disable (PCD) | Disable caching for this page |
| 5 | Accessed (A) | Set by MMU on read |
| 6 | Dirty (D) | Set by MMU on write |
| 7 | Page Size (PS) | 1 = huge page (2 MB in PD, 1 GB in PDPT) |
| 63 | Execute Disable (NX) | No-execute bit; DEP/W^X enforcement |

### 5.4 TLB (Translation Lookaside Buffer)

The TLB caches recent virtual-to-physical translations to avoid the full 4-level walk.

**TLB structure (typical modern CPU):**

| TLB Level | Entries | Associativity | Latency |
|-----------|---------|---------------|---------|
| L1 iTLB (4K) | 64-128 | 4-8 way | 1 cycle |
| L1 dTLB (4K) | 64-128 | 4-8 way | 1 cycle |
| L2 sTLB (4K) | 1024-2048 | 8-12 way | 7-10 cycles |
| L1 dTLB (2M) | 32-64 | 4 way | 1 cycle |

**TLB Miss cost:** 4 memory reads (one per page table level) ≈ 30-100 ns if page tables are cached in data cache; up to 400+ ns if they miss all caches.

**TLB Shootdown:** When one CPU invalidates a page table entry, all other CPUs that might have cached it must be notified via IPI (Inter-Processor Interrupt). This is expensive on many-core systems.

### 5.5 Huge Pages

Regular 4 KB pages mean a 1 GB dataset requires 262,144 TLB entries. With 2 MB huge pages, you need only 512.

| Page Size | TLB Entries for 1 GB | Page Table Levels |
|-----------|---------------------|-------------------|
| 4 KB | 262,144 | 4 |
| 2 MB | 512 | 3 (skip PT level) |
| 1 GB | 1 | 2 (skip PD + PT) |

**Transparent Huge Pages (THP):**
- Kernel automatically promotes 4 KB pages to 2 MB when possible.
- **Risk:** THP compaction can cause unpredictable latency spikes (up to 100+ ms).
- **Databases (Redis, PostgreSQL) often disable THP** via:
  ```bash
  echo never > /sys/kernel/mm/transparent_hugepage/enabled
  ```

**Explicit Huge Pages (hugetlbfs):**
- Reserved at boot: `hugepages=512` in kernel cmdline.
- Applications map them explicitly via `mmap(MAP_HUGETLB)`.
- Deterministic: no compaction stalls.

---

## 6. Inter-Process Communication (IPC)

### 6.1 IPC Mechanisms Comparison

| Mechanism | Latency | Throughput | Use Case |
|-----------|---------|------------|----------|
| Pipe | ~2-5 μs | ~2-4 GB/s | Parent-child, shell pipelines |
| Unix Domain Socket | ~2-5 μs | ~4-8 GB/s | Local client-server |
| Shared Memory | ~50-200 ns | Limited by RAM bandwidth | High-perf data sharing |
| Message Queue (POSIX) | ~3-10 μs | Moderate | Decoupled producers/consumers |
| Signal | ~1-3 μs | N/A (notification only) | Asynchronous notification |
| eventfd | ~1-2 μs | N/A (counter only) | Event notification |
| io_uring | ~0.5-1 μs | Very high | Modern async I/O |

### 6.2 Pipes

```
  Process A                 Process B
  ┌──────┐                 ┌──────┐
  │write()│──► Kernel ──►│read() │
  └──────┘    Buffer     └──────┘
              (64 KB      
               default)   
```

- Unidirectional (use two for bidirectional).
- Blocking by default; writable via `fcntl(O_NONBLOCK)`.
- Buffer size: 64 KB default (`/proc/sys/fs/pipe-max-size`), up to 1 MB via `fcntl(F_SETPIPE_SZ)`.

### 6.3 Shared Memory

The fastest IPC — no kernel involvement after setup.

```c
/* C: POSIX shared memory between processes */
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    const char *name = "/my_shm";
    const size_t SIZE = 4096;

    /* Create shared memory object */
    int fd = shm_open(name, O_CREAT | O_RDWR, 0666);
    ftruncate(fd, SIZE);

    /* Map into address space */
    char *ptr = mmap(NULL, SIZE, PROT_READ | PROT_WRITE,
                     MAP_SHARED, fd, 0);

    /* Write a message */
    snprintf(ptr, SIZE, "Hello from PID %d", getpid());
    printf("Written: %s\n", ptr);

    /* Another process can shm_open the same name and read */
    munmap(ptr, SIZE);
    close(fd);
    /* shm_unlink(name); to remove */
    return 0;
}
```

**Synchronization required:** Shared memory has no built-in synchronization. Use:
- POSIX semaphores (`sem_open`, `sem_wait`, `sem_post`)
- `pthread_mutex` with `PTHREAD_PROCESS_SHARED` attribute
- Futexes (Fast Userspace muTEXes) — the kernel primitive underlying both

### 6.4 Futex — The Foundation

Most synchronization primitives in Linux (pthread_mutex, Go sync.Mutex, Java locks) ultimately use futexes.

```
Fast path (no contention): pure userspace atomic CAS — no syscall
Slow path (contention): futex(FUTEX_WAIT) → kernel sleeps thread
                         futex(FUTEX_WAKE) → kernel wakes thread
```

The kernel maintains a hash table of wait queues keyed by the futex address. This avoids kernel involvement in the common uncontended case.

---

## 7. Memory Allocators

### 7.1 Kernel-Space: Buddy System and Slab

Covered in detail in [01_c_Memory_Management_Algorithms.md](01_c_Memory_Management_Algorithms.md).

### 7.2 User-Space: `malloc` Implementations

The kernel provides pages via `mmap` or `brk`. User-space allocators subdivide them.

#### glibc `malloc` (ptmalloc2)

**Architecture:**
```
┌──────────────────────────────────────────────────────┐
│                   ptmalloc2                           │
│                                                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐              │
│  │ Arena 0  │  │ Arena 1  │  │ Arena N  │  (per-thread)│
│  │ (main)   │  │          │  │          │              │
│  │ ┌──────┐ │  │ ┌──────┐ │  │ ┌──────┐ │              │
│  │ │Fast  │ │  │ │Fast  │ │  │ │Fast  │ │              │
│  │ │Bins  │ │  │ │Bins  │ │  │ │Bins  │ │              │
│  │ ├──────┤ │  │ ├──────┤ │  │ ├──────┤ │              │
│  │ │Small │ │  │ │Small │ │  │ │Small │ │              │
│  │ │Bins  │ │  │ │Bins  │ │  │ │Bins  │ │              │
│  │ ├──────┤ │  │ ├──────┤ │  │ ├──────┤ │              │
│  │ │Large │ │  │ │Large │ │  │ │Large │ │              │
│  │ │Bins  │ │  │ │Bins  │ │  │ │Bins  │ │              │
│  │ ├──────┤ │  │ ├──────┤ │  │ ├──────┤ │              │
│  │ │Unsort│ │  │ │Unsort│ │  │ │Unsort│ │              │
│  │ └──────┘ │  │ └──────┘ │  │ └──────┘ │              │
│  └─────────┘  └─────────┘  └─────────┘              │
│                                                      │
│  Syscalls: brk() for main arena, mmap() for others   │
└──────────────────────────────────────────────────────┘
```

- **Bins:** Free chunks kept in linked lists by size (Fastbins, Smallbins, Largebins, Unsorted).
- **Arenas:** One per core/thread typically to reduce lock contention.
- **Cons:** Can suffer from fragmentation; "best-fit" logic can be slow.

#### jemalloc (Meta, Firefox, Rust default)

- **Small Objects:** Grouped into Runs. A run contains objects of the same Size Class.
- **Bitmap:** Uses bitmaps to track used/free slots.
- **Thread Caches:** Aggressive per-thread caching avoids locks for common ops.
- **Win:** Highly predictable memory footprint; excellent fragmentation resistance.

#### tcmalloc (Google)

- **Thread-Local Cache:** Satisfies most allocations instantly (0 locks).
- **Central Free List:** When thread cache is empty, fetch a batch.
- **Page Heap:** Manages large memory spans.
- **Win:** Speed; used in most Google C++ services.

#### mimalloc (Microsoft Research)

- **Free-list sharding:** Each page has its own free list.
- **Segment-based:** Memory organized in 4 MB segments of fixed-size pages.
- **Win:** Best-in-class on allocation-heavy benchmarks; excellent on small allocations.

### 7.3 Allocator Performance Comparison

| Allocator | Small alloc/free | Large alloc/free | Fragmentation | Thread scaling |
|-----------|-----------------|-----------------|---------------|----------------|
| ptmalloc2 | Moderate | Moderate | Higher | Good (arenas) |
| jemalloc | Fast | Fast | Low | Excellent |
| tcmalloc | Very fast | Fast | Moderate | Excellent |
| mimalloc | Very fast | Fast | Low | Excellent |

**Switching allocators at runtime (LD_PRELOAD):**
```bash
# Use jemalloc for any existing binary
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2 ./my_app

# Use tcmalloc
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libtcmalloc.so.4 ./my_app
```

---

## 8. Memory-Mapped Files and `mmap`

### 8.1 How mmap Works

```c
void *addr = mmap(NULL, length, PROT_READ | PROT_WRITE,
                  MAP_SHARED, fd, offset);
```

1. Kernel creates a VMA (Virtual Memory Area) in the process address space.
2. No physical pages are allocated yet (lazy allocation).
3. On first access → page fault → kernel reads the page from disk into the page cache → maps it.
4. Subsequent accesses by any process hit the page cache (shared).

### 8.2 Private vs Shared Mappings

| Flag | Write behavior | Use case |
|------|---------------|----------|
| `MAP_SHARED` | Writes visible to other processes and flushed to file | IPC, shared files |
| `MAP_PRIVATE` | Copy-on-Write; writes are process-local | Loading .so libraries, fork() |
| `MAP_ANONYMOUS` | No file backing; zeroed pages | Heap expansion, large allocations |

### 8.3 mmap vs read/write

| Aspect | `mmap` | `read`/`write` |
|--------|--------|-----------------|
| System calls | 1 (setup) + page faults | 1 per operation |
| Data copies | 0 (direct page cache access) | 1 (kernel→user copy) |
| Random access | Excellent (pointer arithmetic) | Poor (seek + read) |
| Sequential large files | Can be slower (TLB pressure, page faults) | Faster with readahead |
| Portability | POSIX | Universal |

---

## 9. Signals and Exception Handling

### 9.1 Signal Delivery Mechanism

```
                    Signal sent (kill(), hardware fault, etc.)
                              │
                              ▼
                    ┌─────────────────┐
                    │  Kernel sets     │
                    │  pending bit in  │
                    │  task_struct     │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │  On return to userspace:     │
              │  do_signal() checks pending  │
              └──────────────┬──────────────┘
                             │
                ┌────────────┴────────────┐
                │                          │
         Default action              Custom handler
         (terminate, stop,           (sigaction)
          ignore, core dump)              │
                                          ▼
                                   ┌──────────────┐
                                   │ Kernel sets   │
                                   │ up signal     │
                                   │ frame on user │
                                   │ stack, then   │
                                   │ returns to    │
                                   │ handler addr  │
                                   └──────┬───────┘
                                          │
                                          ▼
                                   Handler runs in
                                   userspace
                                          │
                                          ▼
                                   sigreturn() syscall
                                   restores original
                                   execution context
```

### 9.2 Signal Safety

Only **async-signal-safe** functions may be called from signal handlers. Key safe functions:
`write()`, `_exit()`, `signal()`, `sigaction()`, `fork()`, `execve()`.

**Not safe:** `printf()`, `malloc()`, `free()`, any function that takes a lock.

```c
/* C: safe signal handler */
#include <signal.h>
#include <unistd.h>

static volatile sig_atomic_t got_signal = 0;

static void handler(int sig) {
    (void)sig;
    got_signal = 1;     /* Only set a flag */
    /* write() is async-signal-safe */
    const char msg[] = "Signal received\n";
    write(STDERR_FILENO, msg, sizeof(msg) - 1);
}

int main(void) {
    struct sigaction sa = {
        .sa_handler = handler,
        .sa_flags = SA_RESTART,     /* restart interrupted syscalls */
    };
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);

    while (!got_signal) {
        pause();    /* sleep until signal */
    }
    return 0;
}
```

---

## 10. Namespaces and cgroups — Process Isolation

### 10.1 Linux Namespaces (Container Foundation)

| Namespace | Flag | Isolates |
|-----------|------|----------|
| Mount | `CLONE_NEWNS` | Filesystem mount points |
| PID | `CLONE_NEWPID` | Process IDs |
| Network | `CLONE_NEWNET` | Network stack (interfaces, routing) |
| User | `CLONE_NEWUSER` | UID/GID mapping |
| UTS | `CLONE_NEWUTS` | Hostname |
| IPC | `CLONE_NEWIPC` | SysV IPC, POSIX message queues |
| Cgroup | `CLONE_NEWCGROUP` | cgroup root |
| Time | `CLONE_NEWTIME` | CLOCK_MONOTONIC, CLOCK_BOOTTIME |

```python
# Python: inspecting process namespaces
import os

pid = os.getpid()
ns_dir = f"/proc/{pid}/ns"
for ns in os.listdir(ns_dir):
    target = os.readlink(f"{ns_dir}/{ns}")
    print(f"{ns:>12}: {target}")
```

### 10.2 cgroups v2

cgroups limit, account, and isolate resource usage:

```
/sys/fs/cgroup/
├── cgroup.controllers     # Available: cpu memory io pids
├── cgroup.subtree_control # Active for children
├── myapp/
│   ├── cpu.max            # "100000 100000" = 100% of 1 CPU
│   ├── memory.max         # Bytes limit (OOM kill if exceeded)
│   ├── memory.current     # Current usage
│   ├── io.max             # BPS/IOPS limits per device
│   ├── pids.max           # Max number of processes
│   └── cgroup.procs       # PIDs in this cgroup
```

---

## 11. Performance Analysis and Troubleshooting

### 11.1 Key Tools

| Tool | What it shows |
|------|---------------|
| `top` / `htop` | Per-process CPU, memory, state |
| `vmstat 1` | System-wide memory, swap, CPU, I/O |
| `pidstat -t 1` | Per-thread CPU breakdown |
| `perf stat` | Hardware counters (IPC, cache misses, TLB misses) |
| `perf record / perf report` | CPU profiling with flame graphs |
| `strace -c` | Syscall frequency and time |
| `/proc/<pid>/status` | VmRSS, VmSize, Threads, voluntary/involuntary ctx switches |
| `/proc/<pid>/smaps_rollup` | Detailed memory breakdown (PSS, USS) |

### 11.2 Common Troubleshooting Scenarios

**Scenario 1: High context switch rate**
```bash
# Check system-wide
vmstat 1
# cs column: context switches per second
# Normal: 1,000-50,000/s.  Problem: >200,000/s

# Per-process
pidstat -w 1
# cswch/s: voluntary (I/O wait)
# nvcswch/s: involuntary (preemption — too many threads competing)

# Root cause: usually too many threads or high lock contention
```

**Scenario 2: Process stuck in D state (uninterruptible sleep)**
```bash
# Find D-state processes
ps aux | awk '$8 ~ /D/'

# Check what it's waiting for
cat /proc/<pid>/wchan
# Common: "io_schedule" (waiting for disk I/O)
# Common: "wait_on_page_bit" (page fault from slow storage)

# Check I/O
iostat -x 1
# If await > 100 ms: disk is saturated
```

**Scenario 3: OOM killer invoked**
```bash
# Check dmesg for OOM events
dmesg | grep -i "out of memory"
dmesg | grep -i "killed process"

# The kernel logs:
# - Total RAM and swap
# - Per-process RSS and OOM score
# - Which process was killed and why

# Adjust OOM score for critical processes
echo -1000 > /proc/<pid>/oom_score_adj  # Never kill (use sparingly)
echo 1000 > /proc/<pid>/oom_score_adj   # Kill first
```

**Scenario 4: Memory leak detection**
```bash
# Track RSS growth over time
while true; do
    grep VmRSS /proc/<pid>/status
    sleep 5
done

# Use pmap for detailed mapping
pmap -x <pid> | sort -k2 -n -r | head -20

# Valgrind (development)
valgrind --leak-check=full --show-leak-kinds=all ./my_app

# AddressSanitizer (compile-time, faster than Valgrind)
gcc -fsanitize=address -g my_app.c -o my_app
```

### 11.3 perf: Hardware Performance Counters

```bash
# Count hardware events
perf stat -e cycles,instructions,cache-misses,dTLB-load-misses ./my_app

# Example output:
#   2,500,000,000  cycles
#   5,000,000,000  instructions  # 2.0 IPC (good)
#       1,200,000  cache-misses  # 0.05% miss rate (good)
#         500,000  dTLB-load-misses  # check if high

# Profile with sampling
perf record -g -F 99 -p <pid> -- sleep 30
perf report   # interactive TUI

# Generate flame graph
perf script | stackcollapse-perf.pl | flamegraph.pl > flame.svg
```

---

## 12. Q&A — Common Interview and Design Questions

**Q1: What happens when you type `./program` and press Enter?**

1. Shell calls `fork()` → child process created (CoW address space).
2. Child calls `execve("./program", ...)`:
   a. Kernel parses ELF header, maps segments.
   b. Sets up stack with argv/envp.
   c. If dynamically linked: maps `ld-linux.so`, which resolves shared libraries.
   d. Jumps to `_start` → `__libc_start_main` → `main()`.
3. Parent calls `waitpid()` to wait for child.
4. Child returns from `main()` → `exit_group()` syscall → kernel tears down process.

**Q2: Why does Redis disable Transparent Huge Pages?**

THP's background compaction thread (`khugepaged`) can stall memory allocations for up to hundreds of milliseconds while it coalesces 4 KB pages into 2 MB pages. For a single-threaded, latency-sensitive workload like Redis, a 100 ms stall is catastrophic. Explicit huge pages (hugetlbfs) or simply 4 KB pages are preferred.

**Q3: When would you choose processes over threads?**

- Isolation requirements (untrusted code, crash containment)
- Different privilege levels needed
- Language runtimes that do not support threads (e.g., classic PHP-FPM model)
- When `fork()` + CoW gives you cheap snapshots (e.g., Redis BGSAVE)

**Q4: Why is `CLOSE_WAIT` accumulation dangerous?**

Each socket in `CLOSE_WAIT` means the application received a FIN from the peer but has not called `close()`. This leaks file descriptors. At the default limit of 1024 fds (or common 65536), the process eventually cannot accept new connections or open files.

Fix: the application has a bug — it is not closing sockets after the remote end disconnects. Look for missing `defer conn.Close()` (Go), missing `finally { socket.close(); }` (Java), or exception paths that skip cleanup.

**Q5: Explain Copy-on-Write.**

After `fork()`, parent and child share the same physical pages, marked read-only in both page tables. On a write:
1. MMU raises a page fault (write to read-only page).
2. Kernel checks if it is a CoW page (reference count > 1).
3. Kernel allocates a new page, copies the content, maps it writable in the faulting process.
4. Decrements the reference count on the original page.
5. If refcount drops to 1, the remaining owner can be remapped writable without copying.

This is why `fork()` is fast even for processes with large RSS — only modified pages are actually copied.

**Q6: What is the difference between `vfork()` and `fork()`?**

`vfork()` creates a child that shares the parent's address space entirely (no CoW). The parent is suspended until the child calls `exec()` or `_exit()`. It is faster but extremely dangerous — any memory modification in the child corrupts the parent. Modern `fork()` with CoW has made `vfork()` mostly unnecessary, though the kernel still supports it for the marginal performance gain in fork-exec patterns.

---

## 13. Hands-On Exercises

### Exercise 1: Process Tree Observer

Write a program that:
1. Forks 3 child processes.
2. Each child forks 2 grandchildren.
3. Each process prints its PID, PPID, and depth.
4. Parent waits for all descendants.
5. Verify no zombies remain with `ps`.

### Exercise 2: Context Switch Benchmark

Using the pipe ping-pong pattern from Section 4.2:
1. Measure context switch time with default scheduling.
2. Change both processes to `SCHED_FIFO` and re-measure.
3. Pin both to the same CPU core (`taskset -c 0`) and re-measure.
4. Pin to different cores and re-measure.
5. Explain the differences.

### Exercise 3: Memory Mapping Investigation

1. Write a program that `mmap`s a 1 GB file with `MAP_PRIVATE`.
2. Read every page (touch every 4096th byte) and measure time.
3. Write to every page and measure time (triggers CoW).
4. Compare RSS before and after reads, and after writes using `/proc/self/status`.
5. Try again with `MAP_POPULATE` and compare page fault counts via `perf stat`.

### Exercise 4: Shared Memory IPC

1. Create a producer process that writes incrementing integers to shared memory.
2. Create a consumer process that reads and validates the sequence.
3. Add synchronization with a POSIX semaphore.
4. Measure throughput (messages/sec) and compare with pipe-based IPC.

### Exercise 5: OOM Behavior

1. Set up a cgroup with 100 MB memory limit.
2. Write a program that allocates memory in a loop.
3. Observe when the OOM killer triggers (check `dmesg`).
4. Set `memory.oom.group = 1` and observe the difference.
5. Experiment with `oom_score_adj` values.

### Exercise 6: Namespace Exploration

```bash
# Create a PID namespace and observe isolation
unshare --pid --fork --mount-proc bash
# Inside: ps aux shows only bash and ps
# Outside: the processes are visible with their host PIDs

# Create a network namespace
ip netns add test
ip netns exec test ip link
# Only loopback exists — fully isolated network stack
```

### Exercise 7: Scheduler Analysis with perf

```bash
# Record scheduling events
perf sched record -- sleep 10

# Analyze latencies
perf sched latency
# Shows per-task max/avg scheduling latency

# Visualize scheduling timeline
perf sched timehist
# Shows context switches with timestamps

# Map scheduling to CPUs
perf sched map
```

### Exercise 8: Allocator Comparison

1. Write a benchmark that performs 10M allocations of random sizes (8-4096 bytes) followed by random frees.
2. Run with default glibc malloc.
3. Run with jemalloc via `LD_PRELOAD`.
4. Run with tcmalloc via `LD_PRELOAD`.
5. Compare: wall time, peak RSS, and fragmentation (RSS vs actual live data).

### Exercise 9: TLB Performance Impact

```c
/* C: measuring TLB impact with different page sizes */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>

#define SIZE (1UL << 30)  /* 1 GB */

static double measure_access(char *p, size_t size, size_t stride) {
    struct timespec start, end;
    volatile char sink;

    clock_gettime(CLOCK_MONOTONIC, &start);
    for (size_t i = 0; i < size; i += stride)
        sink = p[i];
    clock_gettime(CLOCK_MONOTONIC, &end);

    (void)sink;
    return (end.tv_sec - start.tv_sec) * 1e9 +
           (end.tv_nsec - start.tv_nsec);
}

int main(void) {
    /* Regular 4 KB pages */
    char *p4k = mmap(NULL, SIZE, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE,
                     -1, 0);
    memset(p4k, 1, SIZE);

    /* Huge 2 MB pages */
    char *p2m = mmap(NULL, SIZE, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE |
                     MAP_HUGETLB,
                     -1, 0);
    if (p2m != MAP_FAILED)
        memset(p2m, 1, SIZE);

    /* Sequential access: stride = 4096 (one access per page) */
    double t4k = measure_access(p4k, SIZE, 4096);
    printf("4 KB pages, stride 4096: %.2f ms\n", t4k / 1e6);

    if (p2m != MAP_FAILED) {
        double t2m = measure_access(p2m, SIZE, 4096);
        printf("2 MB pages, stride 4096: %.2f ms\n", t2m / 1e6);
        printf("Speedup: %.2fx\n", t4k / t2m);
        munmap(p2m, SIZE);
    } else {
        printf("Huge pages not available (need to reserve)\n");
    }

    munmap(p4k, SIZE);
    return 0;
}
```

Tasks:
1. Compile and run. How much faster are huge pages?
2. Use `perf stat -e dTLB-load-misses` to compare TLB miss counts.
3. Try stride = 64 (within-page access). Does the difference shrink?
4. Calculate: how many TLB entries are needed for 1 GB with 4 KB vs 2 MB pages?

### Exercise 10: Implementing a Simple Memory Allocator

Write a basic bump allocator in C:

```c
/* C: skeleton for a bump allocator */
#include <stddef.h>
#include <sys/mman.h>

#define POOL_SIZE (1 << 20)  /* 1 MB */

typedef struct {
    char *base;
    size_t offset;
    size_t capacity;
} BumpAllocator;

/* Initialize: mmap a pool */
int bump_init(BumpAllocator *a) {
    a->base = mmap(NULL, POOL_SIZE, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (a->base == (void *)-1) return -1;
    a->offset = 0;
    a->capacity = POOL_SIZE;
    return 0;
}

/* Allocate: advance the bump pointer */
void *bump_alloc(BumpAllocator *a, size_t size) {
    /* Align to 8 bytes */
    size = (size + 7) & ~7UL;
    if (a->offset + size > a->capacity) return NULL;
    void *ptr = a->base + a->offset;
    a->offset += size;
    return ptr;
}

/* Reset: free everything at once */
void bump_reset(BumpAllocator *a) {
    a->offset = 0;
}

/* Destroy */
void bump_destroy(BumpAllocator *a) {
    munmap(a->base, a->capacity);
}
```

Tasks:
1. Complete the implementation with proper alignment handling.
2. Add a `bump_free()` that only works if freeing the most recent allocation.
3. Benchmark against `malloc`/`free` for 1M allocations of 64-byte objects.
4. Explain why this allocator cannot support arbitrary `free()` without a free list.
5. Implement a simple free-list allocator that supports arbitrary frees.

### Exercise 11: Process Isolation Lab

1. Create a minimal container using raw syscalls:
   ```bash
   # Create all namespaces
   unshare --pid --net --mount --uts --ipc --fork bash

   # Inside the new namespace:
   hostname "container"
   mount -t proc proc /proc
   ps aux  # only sees processes in this PID namespace
   hostname  # shows "container"
   ```
2. Add a cgroup memory limit:
   ```bash
   mkdir /sys/fs/cgroup/mycontainer
   echo 50M > /sys/fs/cgroup/mycontainer/memory.max
   echo $$ > /sys/fs/cgroup/mycontainer/cgroup.procs
   # Now this shell and children are limited to 50 MB
   ```
3. Write a C program that exceeds the memory limit and observe the OOM kill.
4. Add a seccomp filter that blocks `unlink` and verify files cannot be deleted.

### Exercise 12: NUMA Experiment

1. On a multi-socket system (or use `numactl --hardware` to check):
   ```bash
   # Benchmark local vs remote NUMA access
   numactl --cpunodebind=0 --membind=0 ./membench   # local
   numactl --cpunodebind=0 --membind=1 ./membench   # remote
   ```
2. Write `membench` as a simple program that reads 1 GB sequentially.
3. Compare throughput and latency.
4. Use `perf stat -e node-loads,node-load-misses` to verify NUMA locality.

### Exercise 13: Signal Handler Debugging

```c
/* C: intentionally buggy signal handler — find the bugs */
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void handler(int sig) {
    printf("Caught signal %d\n", sig);      /* BUG 1 */
    char *buf = malloc(256);                 /* BUG 2 */
    snprintf(buf, 256, "Signal: %s\n", strsignal(sig));
    free(buf);                               /* BUG 3 */
}

int main(void) {
    signal(SIGSEGV, handler);                /* BUG 4 */
    /* Trigger SIGSEGV */
    *(volatile int *)NULL = 42;
    return 0;
}
```

Tasks:
1. Identify all four bugs and explain why each is dangerous.
2. Rewrite the handler to be async-signal-safe.
3. What happens if the SIGSEGV handler returns? (Hint: infinite loop.)
4. How should you properly handle SIGSEGV? (`_exit`, `raise(SIGABRT)`, etc.)

---

## 14. Deep Dive: Page Fault Handling

### 14.1 Types of Page Faults

| Type | Cause | Kernel action | Cost |
|------|-------|---------------|------|
| Minor (soft) | Page in page cache but not mapped | Map existing page | ~1-10 μs |
| Major (hard) | Page not in memory at all | Read from disk, then map | ~1-10 ms (HDD), ~50-200 μs (SSD) |
| Invalid | Access to unmapped address | Send SIGSEGV | Process dies |
| Protection | Write to read-only page | CoW copy or SIGSEGV | ~1-10 μs (CoW) |

### 14.2 Page Fault Walk-Through

```
1. CPU instruction accesses virtual address VA
2. MMU walks page table → PTE not present (P bit = 0)
3. CPU raises #PF exception (vector 14)
4. Pushes error code on kernel stack:
   Bit 0: 0=not-present, 1=protection violation
   Bit 1: 0=read, 1=write
   Bit 2: 0=kernel, 1=user
5. Kernel handler: do_page_fault() → handle_mm_fault()
   ├── Find VMA containing the faulting address
   ├── If no VMA: SIGSEGV (invalid access)
   ├── If VMA found, check permissions
   ├── If anonymous page (heap/stack):
   │   ├── Allocate zero page
   │   └── Map into page table
   ├── If file-backed page:
   │   ├── Check page cache
   │   ├── If found: minor fault (just map it)
   │   └── If not found: major fault
   │       ├── Schedule I/O to read page from disk
   │       ├── Sleep until I/O completes
   │       └── Map page into page table
   └── If CoW page (write to shared page):
       ├── Allocate new page
       ├── Copy contents
       ├── Map new page writable
       └── Decrement refcount on old page
6. Return from exception → instruction retries → succeeds
```

### 14.3 Demand Paging in Practice

When a process calls `mmap()` or even `malloc()` (which calls `mmap` for large allocations), the kernel does NOT allocate physical pages. It only creates VMAs. Physical pages are allocated on first access.

```c
/* C: demonstrating demand paging */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

int main(void) {
    size_t size = 1UL << 30; /* 1 GB */

    printf("Before mmap: check /proc/%d/status\n", getpid());
    sleep(2);

    /* mmap 1 GB — no physical memory used yet */
    char *p = mmap(NULL, size, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) { perror("mmap"); return 1; }

    printf("After mmap (VmSize increased, VmRSS unchanged)\n");
    sleep(2);

    /* Touch every page → triggers page faults */
    for (size_t i = 0; i < size; i += 4096)
        p[i] = 1;

    printf("After touching all pages (VmRSS ≈ 1 GB)\n");
    sleep(2);

    /* Advise kernel we no longer need the pages */
    madvise(p, size, MADV_DONTNEED);
    printf("After MADV_DONTNEED (VmRSS drops back)\n");
    sleep(2);

    munmap(p, size);
    return 0;
}
```

### 14.4 Memory Overcommit

Linux allows processes to request more virtual memory than physical RAM + swap. This is **overcommit**.

```
/proc/sys/vm/overcommit_memory:
  0 = heuristic (default): allow reasonable overcommit
  1 = always allow: never refuse mmap/malloc
  2 = strict: limit to swap + (RAM * overcommit_ratio/100)

/proc/sys/vm/overcommit_ratio:
  Default 50 → allowed = swap + 50% of RAM
```

**Why it exists:** After `fork()`, both parent and child nominally "own" the entire address space (due to CoW). Without overcommit, forking a 10 GB process would require 10 GB of free memory even though the child will immediately `exec()`.

**The risk:** If all processes try to use their committed memory simultaneously and there is not enough RAM + swap, the OOM killer activates.

---

## 15. Deep Dive: The Page Cache

### 15.1 What Is the Page Cache?

The page cache is the kernel's primary mechanism for caching file data in RAM. When you `read()` a file, the data goes through the page cache. Subsequent reads of the same data hit RAM instead of disk.

```
User Process          Kernel              Disk
    │                   │                   │
    │  read(fd, buf, n) │                   │
    │──────────────────►│                   │
    │                   │ Check page cache  │
    │                   │──┐                │
    │                   │  │ Cache hit?      │
    │                   │◄─┘                │
    │                   │     YES            │
    │  data ◄───────────│                   │
    │                   │     NO             │
    │                   │  Read from disk    │
    │                   │──────────────────►│
    │                   │  data ◄────────────│
    │                   │  Store in cache    │
    │  data ◄───────────│                   │
```

### 15.2 Page Cache Internals

- Pages are indexed by `(inode, offset)` pair in a **radix tree** (now called **XArray** since Linux 4.20).
- The same physical page can be mapped into multiple processes simultaneously.
- `free` command's "buff/cache" column shows page cache usage.

```bash
# Drop caches for benchmarking
sync
echo 3 > /proc/sys/vm/drop_caches
# 1 = page cache, 2 = dentries/inodes, 3 = both

# Monitor page cache hit rate
perf stat -e cache-references,cache-misses -a -- sleep 10

# Per-process page cache usage
fincore /path/to/file  # shows cached pages
vmtouch /path/to/file  # shows and manipulates cached pages
```

### 15.3 Readahead

The kernel detects sequential read patterns and prefetches pages ahead of the application.

- Default readahead window: 128 KB (`/sys/block/<dev>/queue/read_ahead_kb`).
- Adaptive: grows up to 256 KB for sustained sequential reads.
- `posix_fadvise(fd, off, len, POSIX_FADV_SEQUENTIAL)` hints the kernel to read ahead aggressively.
- `POSIX_FADV_RANDOM` disables readahead for random-access patterns.

---

## 16. Deep Dive: NUMA Architecture

### 16.1 NUMA Topology

```
  ┌─────────────────────┐     ┌─────────────────────┐
  │      Node 0          │     │      Node 1          │
  │                      │     │                      │
  │  ┌───┐ ┌───┐ ┌───┐  │     │  ┌───┐ ┌───┐ ┌───┐  │
  │  │C0 │ │C1 │ │C2 │  │     │  │C4 │ │C5 │ │C6 │  │
  │  └─┬─┘ └─┬─┘ └─┬─┘  │     │  └─┬─┘ └─┬─┘ └─┬─┘  │
  │    └──────┼──────┘    │     │    └──────┼──────┘    │
  │           │           │     │           │           │
  │    ┌──────┴──────┐    │     │    ┌──────┴──────┐    │
  │    │  L3 Cache   │    │     │    │  L3 Cache   │    │
  │    └──────┬──────┘    │     │    └──────┬──────┘    │
  │           │           │     │           │           │
  │    ┌──────┴──────┐    │     │    ┌──────┴──────┐    │
  │    │  Memory     │    │     │    │  Memory     │    │
  │    │  Controller │    │     │    │  Controller │    │
  │    └──────┬──────┘    │     │    └──────┬──────┘    │
  │           │           │     │           │           │
  │    ┌──────┴──────┐    │     │    ┌──────┴──────┐    │
  │    │ DDR4/5 DIMMs│    │     │    │ DDR4/5 DIMMs│    │
  │    │ (Local RAM) │    │     │    │ (Local RAM) │    │
  │    └─────────────┘    │     │    └─────────────┘    │
  └───────────┬───────────┘     └───────────┬───────────┘
              │         Interconnect         │
              │  (QPI / UPI / Infinity Fabric)│
              └──────────────────────────────┘
```

### 16.2 NUMA Latency Impact

| Access pattern | Latency | Bandwidth |
|---------------|---------|-----------|
| Local NUMA node | ~70-100 ns | Full bandwidth |
| Remote NUMA node (1 hop) | ~130-200 ns | ~60-70% of local |
| Remote NUMA node (2 hops) | ~200-300 ns | ~40-50% of local |

### 16.3 NUMA-Aware Programming

```bash
# Check NUMA topology
numactl --hardware
# Shows nodes, CPUs per node, and inter-node distances

# Bind process to a node
numactl --membind=0 --cpunodebind=0 ./my_app

# NUMA allocation policies
numactl --interleave=all ./my_app  # spread pages across all nodes
numactl --preferred=0 ./my_app    # prefer node 0, fallback to others
numactl --localalloc ./my_app     # always allocate on local node
```

```c
/* C: NUMA-aware allocation with libnuma */
#include <numa.h>
#include <stdio.h>

int main(void) {
    if (numa_available() < 0) {
        fprintf(stderr, "NUMA not available\n");
        return 1;
    }
    printf("NUMA nodes: %d\n", numa_max_node() + 1);
    printf("Preferred node: %d\n", numa_preferred());

    /* Allocate 1 GB on NUMA node 0 */
    size_t size = 1UL << 30;
    void *p = numa_alloc_onnode(size, 0);
    if (!p) { perror("numa_alloc_onnode"); return 1; }

    /* Use the memory... */
    memset(p, 0, size);

    numa_free(p, size);
    return 0;
}
```

### 16.4 NUMA Pitfalls in Production

**Problem: Remote memory access after migration.** The scheduler may migrate a thread to a different NUMA node for load balancing, but its memory stays on the original node. All accesses become remote.

**Mitigations:**
- `numactl --localalloc` to force local allocation
- `mbind()` syscall for fine-grained per-VMA policy
- `migrate_pages()` to move pages after thread migration
- Automatic NUMA balancing (`/proc/sys/kernel/numa_balancing = 1`): kernel periodically unmaps pages, detects remote accesses via page faults, and migrates hot pages

---

## 17. Deep Dive: Kernel Preemption Models

### 17.1 Preemption Configurations

| Config | Behavior | Use case |
|--------|----------|----------|
| `PREEMPT_NONE` | Kernel never preempted; only at explicit points | Throughput servers |
| `PREEMPT_VOLUNTARY` | Preemption at might_sleep() points | General desktop/server |
| `PREEMPT` | Full preemption (except in critical sections) | Low-latency, desktop |
| `PREEMPT_RT` | Hard real-time; converts spinlocks to rt_mutexes | Robotics, audio, industrial |

### 17.2 Priority Inversion

When a high-priority task waits for a lock held by a low-priority task:

```
Time →

High-prio T1:   RUN ──► BLOCKED (waiting for lock L)
                                    │
Med-prio T2:          RUN ──────────┼──► RUN (preempts T3!)
                                    │
Low-prio T3:    RUN (holds L) ──────┼──► BLOCKED (T2 preempts)
                                    
T1 is delayed by T2 even though T2 has nothing to do with lock L.
This is UNBOUNDED priority inversion.
```

**Solution: Priority Inheritance Protocol (PIP)**
- When T1 blocks on lock L held by T3, T3 temporarily inherits T1's priority.
- T3 runs at high priority, completes the critical section, releases L.
- T1 immediately gets the lock and runs.
- POSIX: `PTHREAD_PRIO_INHERIT` mutex attribute.

### 17.3 The Mars Pathfinder Bug (1997)

The most famous priority inversion incident. On the Sojourner rover:
- Low-priority "information bus" task held a mutex.
- Medium-priority "communications" task preempted it.
- High-priority "bus management" task could not acquire the mutex → system reset.
- Fixed by enabling priority inheritance on the mutex.

---

## 18. Deep Dive: Process Credentials and Capabilities

### 18.1 Traditional Unix Model

Each process has:
- **Real UID/GID (ruid, rgid):** Who you actually are.
- **Effective UID/GID (euid, egid):** What permissions you have now.
- **Saved UID/GID (suid, sgid):** Backup for privilege dropping.
- **Filesystem UID/GID (fsuid, fsgid):** Used only for file access (Linux-specific).

### 18.2 Capabilities (Fine-Grained Privileges)

Instead of all-or-nothing root, Linux capabilities split root power:

| Capability | Grants |
|------------|--------|
| `CAP_NET_BIND_SERVICE` | Bind to ports < 1024 |
| `CAP_NET_RAW` | Use raw sockets (ping) |
| `CAP_SYS_PTRACE` | Trace any process |
| `CAP_SYS_ADMIN` | Catch-all admin (mount, ioctl, etc.) |
| `CAP_DAC_OVERRIDE` | Bypass file permission checks |
| `CAP_SETUID` | Set arbitrary UIDs |
| `CAP_NET_ADMIN` | Configure network interfaces |

```bash
# Set capability on a binary (instead of setuid root)
setcap cap_net_bind_service=ep /usr/local/bin/my_server

# Check capabilities
getcap /usr/local/bin/my_server

# Drop all capabilities in a namespace (container)
unshare --map-root-user bash
# Inside: UID 0 but with limited capabilities
```

---

## 19. Performance Benchmarks Reference

### 19.1 Operation Latency Reference Table

| Operation | Typical latency |
|-----------|----------------|
| L1 cache hit | ~1 ns |
| L2 cache hit | ~4-7 ns |
| L3 cache hit | ~10-20 ns |
| DRAM access | ~60-100 ns |
| TLB miss (page walk) | ~30-100 ns |
| Context switch (threads, same process) | ~1-2 μs |
| Context switch (processes) | ~3-5 μs |
| Context switch (with KPTI) | ~5-10 μs |
| System call (getpid, minimal) | ~100-200 ns |
| System call (read, small) | ~1-5 μs |
| fork() | ~50-200 μs |
| pthread_create() | ~10-30 μs |
| Goroutine creation | ~0.3-1 μs |
| Page fault (minor) | ~1-10 μs |
| Page fault (major, SSD) | ~50-200 μs |
| Page fault (major, HDD) | ~5-10 ms |
| Mutex lock (uncontended) | ~10-25 ns |
| Mutex lock (contended, futex) | ~1-10 μs |

### 19.2 Capacity Reference

| Resource | Typical limit |
|----------|--------------|
| Max PIDs | 4,194,304 (`/proc/sys/kernel/pid_max`) |
| Max file descriptors (process) | 1,024 soft / 1,048,576 hard |
| Max threads (system) | `/proc/sys/kernel/threads-max` (typically ~30,000-250,000) |
| Stack size (thread) | 8 MB default |
| Virtual address space (user) | 128 TB (48-bit), 64 PB (57-bit LA57) |
| Page cache | All free RAM (dynamic) |
| Max cgroup depth | 31 levels (cgroup v2) |

---

## 20. Further Reading

- **Linux Kernel Source:** `kernel/sched/fair.c` (CFS/EEVDF), `mm/mmap.c`, `mm/memory.c` (page faults), `kernel/fork.c`
- **"Understanding the Linux Kernel"** by Bovet & Cesati
- **"Linux Kernel Development"** by Robert Love
- **"Systems Performance: Enterprise and the Cloud"** by Brendan Gregg
- **LWN.net:** Definitive source for kernel development articles
- **man pages:** `clone(2)`, `mmap(2)`, `sched_setscheduler(2)`, `cgroups(7)`, `namespaces(7)`, `capabilities(7)`
- **perf wiki:** https://perf.wiki.kernel.org/
- **kernel.org documentation:** https://www.kernel.org/doc/html/latest/

---

## 21. Advanced: Swap and Memory Reclaim

### 21.1 How Swap Works

When physical memory is under pressure, the kernel must evict pages. Pages fall into two categories:

| Page type | Eviction method |
|-----------|-----------------|
| File-backed (page cache) | Drop the page; re-read from disk if needed |
| Anonymous (heap, stack, mmap anon) | Write to swap space, then unmap |

**Swap areas:**
```bash
# Check swap configuration
swapon --show
# NAME       TYPE       SIZE   USED  PRIO
# /swap.img  file       8G     1.2G  -2

# Add a swap file
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

### 21.2 Swappiness

`/proc/sys/vm/swappiness` (0-200, default 60) controls the kernel's bias:
- **0:** Never swap anonymous pages (only reclaim page cache). Use for latency-sensitive workloads (databases).
- **60:** Default balance.
- **100:** Equal preference for swapping anonymous and reclaiming page cache.
- **>100:** Prefer swapping anonymous pages over dropping page cache.

### 21.3 Memory Reclaim Path

```
Allocation request → check watermarks
         │
         ▼
    ┌──────────┐
    │ WMARK_LOW │ ── below? → wake kswapd (background reclaim)
    └──────────┘
         │
    ┌───────────┐
    │ WMARK_MIN  │ ── below? → direct reclaim (synchronous, stalls allocator)
    └───────────┘
         │
    ┌───────────┐
    │ No memory  │ ── → OOM killer
    └───────────┘

kswapd targets:
1. Scan LRU lists (active/inactive, anon/file)
2. Reclaim pages until WMARK_HIGH reached
3. Use two-list LRU:
   Active list: recently accessed pages
   Inactive list: candidates for eviction
   Pages promoted active→inactive via "second chance" (accessed bit)
```

### 21.4 zswap and zram

**zswap:** Compressed cache in front of swap. Pages are compressed in RAM before being written to disk swap. Reduces swap I/O at the cost of CPU.

**zram:** Compressed block device in RAM. No disk backing at all. Used in Android and memory-constrained systems.

```bash
# Enable zswap
echo 1 > /sys/module/zswap/parameters/enabled
echo lz4 > /sys/module/zswap/parameters/compressor
echo 20 > /sys/module/zswap/parameters/max_pool_percent

# Check zswap stats
grep -r . /sys/kernel/debug/zswap/
```

---

## 22. Advanced: seccomp and System Call Filtering

### 22.1 What Is seccomp?

**seccomp** (Secure Computing Mode) restricts which system calls a process can make. It is the foundation of container and sandbox security.

| Mode | Behavior |
|------|----------|
| `SECCOMP_MODE_STRICT` | Only `read`, `write`, `_exit`, `sigreturn` allowed |
| `SECCOMP_MODE_FILTER` | BPF program decides per-syscall: allow, deny, trace, log |

### 22.2 seccomp-bpf Example

```c
/* C: restrict a process to only read/write/exit */
#include <stdio.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <sys/syscall.h>
#include <stddef.h>

int main(void) {
    /* BPF filter: allow read, write, exit_group; kill on anything else */
    struct sock_filter filter[] = {
        /* Load syscall number */
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS,
                 offsetof(struct seccomp_data, nr)),
        /* Allow read (0) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_read, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
        /* Allow write (1) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_write, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
        /* Allow exit_group (231) */
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_exit_group, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
        /* Kill on anything else */
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL),
    };

    struct sock_fprog prog = {
        .len = sizeof(filter) / sizeof(filter[0]),
        .filter = filter,
    };

    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog);

    /* This write succeeds */
    write(STDOUT_FILENO, "sandboxed!\n", 11);

    /* This would trigger SIGKILL:
       open("/etc/passwd", O_RDONLY); */

    return 0;
}
```

### 22.3 seccomp in Production

- **Docker:** applies a default seccomp profile that blocks ~44 dangerous syscalls.
- **Chrome/Chromium:** renderer processes are seccomp-sandboxed.
- **systemd:** `SystemCallFilter=` directive in unit files.

---

## 23. Advanced: ptrace and Process Tracing

### 23.1 ptrace Mechanics

`ptrace()` is the system call behind `strace`, `gdb`, and most debuggers.

```
Tracer (debugger)              Tracee (target)
     │                              │
     │  ptrace(PTRACE_ATTACH, pid)  │
     │─────────────────────────────►│
     │                              │ SIGSTOP → stops
     │                              │
     │  waitpid(pid)                │
     │◄─────────────────────────────│ status = stopped
     │                              │
     │  ptrace(PTRACE_PEEKDATA)     │ read tracee memory
     │  ptrace(PTRACE_GETREGS)      │ read tracee registers
     │  ptrace(PTRACE_SYSCALL)      │ resume; stop at next syscall
     │                              │
     │  waitpid(pid)                │
     │◄─────────────────────────────│ stopped at syscall entry
     │  ptrace(PTRACE_GETREGS)      │ read RAX = syscall number
     │  ptrace(PTRACE_SYSCALL)      │ resume; stop at syscall exit
     │                              │
     │  waitpid(pid)                │
     │◄─────────────────────────────│ stopped at syscall exit
     │  ptrace(PTRACE_GETREGS)      │ read RAX = return value
```

### 23.2 strace in Practice

```bash
# Trace all syscalls of a command
strace -f -e trace=network curl https://example.com 2>&1 | head -50
# -f: follow forks
# -e trace=network: only network-related syscalls

# Count syscalls and time
strace -c -p <pid>
# Attaches and accumulates stats until Ctrl+C

# Trace file operations of a running process
strace -p <pid> -e trace=openat,read,write,close

# Common debugging patterns:
# "Why does my app hang?" → strace shows it blocked on futex() or read()
# "Why is startup slow?" → strace -T shows time per syscall
# "What config files does it read?" → strace -e openat
```

---

## 24. Summary Cheat Sheet

```
┌─────────────────────────────────────────────────────────────┐
│                    OS INTERNALS CHEAT SHEET                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  PROCESS CREATION                                           │
│    fork()  → CoW clone       clone() → configurable        │
│    exec()  → replace image   vfork() → shared (dangerous)  │
│                                                             │
│  SCHEDULING (Linux)                                         │
│    SCHED_DEADLINE > SCHED_FIFO > SCHED_RR > SCHED_NORMAL   │
│    CFS: vruntime + RB-tree    EEVDF: virtual deadline       │
│    Per-CPU runqueues + work stealing                        │
│                                                             │
│  MEMORY                                                     │
│    Virtual: PML4→PDPT→PD→PT→Page (4-level walk)            │
│    TLB: caches translations; PCID avoids flushes            │
│    Huge pages: 2MB/1GB; THP can cause latency spikes        │
│    Allocators: buddy(kernel) + slab(kernel) + malloc(user)  │
│                                                             │
│  IPC (fastest → most isolated)                              │
│    Shared mem → pipe → Unix socket → TCP → message queue    │
│                                                             │
│  ISOLATION                                                  │
│    Namespaces: PID, NET, MNT, USER, UTS, IPC, CGROUP, TIME │
│    cgroups v2: cpu.max, memory.max, io.max, pids.max        │
│    seccomp-bpf: syscall filtering                           │
│    Capabilities: fine-grained privilege (not all-or-nothing) │
│                                                             │
│  KEY TOOLS                                                  │
│    perf: HW counters, profiling, sched analysis             │
│    strace: syscall tracing     ftrace: kernel tracing       │
│    vmstat/pidstat: system/process stats                      │
│    /proc/*/status: per-process memory and context switches   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 25. Further Reading

- **Linux Kernel Source:** `kernel/sched/fair.c` (CFS/EEVDF), `mm/mmap.c`, `mm/memory.c` (page faults), `kernel/fork.c`
- **"Understanding the Linux Kernel"** by Bovet & Cesati
- **"Linux Kernel Development"** by Robert Love
- **"Systems Performance: Enterprise and the Cloud"** by Brendan Gregg
- **"The Linux Programming Interface"** by Michael Kerrisk — the definitive POSIX/Linux API reference
- **LWN.net:** Definitive source for kernel development articles
- **man pages:** `clone(2)`, `mmap(2)`, `sched_setscheduler(2)`, `cgroups(7)`, `namespaces(7)`, `capabilities(7)`, `seccomp(2)`, `proc(5)`
- **perf wiki:** https://perf.wiki.kernel.org/
- **kernel.org documentation:** https://www.kernel.org/doc/html/latest/
- **Intel SDM (Software Developer Manual):** authoritative x86_64 architecture reference
- **OSDev Wiki:** https://wiki.osdev.org/ — low-level x86 hardware documentation
- **Kernel Newbies:** https://kernelnewbies.org/ — changelogs per kernel version
- **ftrace documentation:** `Documentation/trace/ftrace.rst` in kernel source tree
- **Address Sanitizer docs:** https://clang.llvm.org/docs/AddressSanitizer.html
- **LKML (Linux Kernel Mailing List):** primary discussion forum for kernel development and patches
- **Valgrind manual:** https://valgrind.org/docs/manual/manual.html
- **glibc malloc internals:** `malloc/malloc.c` in glibc source; see also MallocInternals wiki page

---

## Exercises

### Exercise 1 — Process State Observation

Observe real process states using `/proc` and `ps`.

1. Open two terminals.
2. In terminal A, run: `sleep 300 &` then `cat` (no arguments — it blocks on stdin).
3. In terminal B, run: `ps -eo pid,stat,wchan,comm | grep -E 'sleep|cat'`
4. Identify the **S** (interruptible sleep) state for both processes.
5. Send `SIGSTOP` to the `cat` process: `kill -STOP $(pgrep -x cat)`
6. Re-run the `ps` command — confirm the state changed to **T** (stopped).
7. Resume with `kill -CONT $(pgrep -x cat)` and confirm it returns to **S**.
8. Create a zombie: write a small C program that `fork()`s a child that immediately `_exit(0)` while the parent `sleep(60)`s without calling `wait()`. Compile, run, and confirm the **Z** state with `ps`.

**Expected output:** You should see states `S`, `T`, and `Z` in the `STAT` column.

### Exercise 2 — Virtual Memory Layout Inspection

Explore the virtual address space of a running process.

1. Run: `cat /proc/self/maps` — examine the output columns (address range, permissions, offset, device, inode, pathname).
2. Identify the segments: `[heap]`, `[stack]`, `[vdso]`, `[vvar]`, and the main executable mapping.
3. Write a C program that allocates 1 MB with `malloc()`, 1 MB with `mmap(MAP_ANONYMOUS)`, and prints its own PID then sleeps.
4. While it sleeps, run: `cat /proc/<pid>/maps` and `cat /proc/<pid>/smaps_rollup`
5. Compare `VmRSS`, `VmSize`, `RssAnon`, and `RssShmem` in `/proc/<pid>/status`.
6. Touch the malloc'd memory with `memset()`, re-check `/proc/<pid>/status` — confirm RSS increased (demand paging).

**Expected output:** RSS grows only after pages are faulted in, demonstrating lazy allocation.

### Exercise 3 — Scheduler Behaviour with `chrt` and `perf sched`

Observe CFS/EEVDF scheduling decisions in real time.

1. Launch two CPU-bound processes pinned to the same core:
   ```bash
   taskset -c 0 stress-ng --cpu 1 --timeout 30 &
   taskset -c 0 stress-ng --cpu 1 --timeout 30 &
   ```
2. Run: `perf sched record -- sleep 10` (requires `perf` installed and `CAP_PERFMON` or root).
3. After recording: `perf sched latency` — examine per-task average and max scheduling latency.
4. Run: `perf sched map` — visualize which task ran on the CPU at each timeslice.
5. Now set one process to `SCHED_FIFO` priority 50: `sudo chrt -f -p 50 <pid>`.
6. Re-run the `perf sched record` cycle — note how the FIFO task dominates the core.

**Expected output:** CFS/EEVDF fairly interleaves the two CPU-bound tasks; `SCHED_FIFO` causes starvation of the lower-priority task.

### Exercise 4 — cgroups v2 Memory Limits

Apply memory pressure with cgroups v2 and observe the OOM killer.

1. Ensure cgroups v2 is mounted: `mount | grep cgroup2`
2. Create a cgroup:
   ```bash
   sudo mkdir /sys/fs/cgroup/exercise
   echo "+memory" | sudo tee /sys/fs/cgroup/exercise/cgroup.subtree_control
   sudo mkdir /sys/fs/cgroup/exercise/limited
   ```
3. Set a 50 MB memory limit:
   ```bash
   echo 52428800 | sudo tee /sys/fs/cgroup/exercise/limited/memory.max
   ```
4. Move your shell into the cgroup: `echo $$ | sudo tee /sys/fs/cgroup/exercise/limited/cgroup.procs`
5. Run a program that allocates more than 50 MB (e.g., `stress-ng --vm 1 --vm-bytes 100M --timeout 10`).
6. Check `dmesg | tail` for OOM-killer messages.
7. Inspect `memory.current`, `memory.events` (look for the `oom_kill` counter).
8. Clean up: exit the shell, `sudo rmdir /sys/fs/cgroup/exercise/limited /sys/fs/cgroup/exercise`.

**Expected output:** The kernel OOM-kills the stress process when it exceeds the 50 MB limit.

### Exercise 5 — Namespace Isolation Hands-On

Create a PID + mount namespace and observe isolation.

1. Enter a new PID and mount namespace:
   ```bash
   sudo unshare --pid --mount --fork --mount-proc bash
   ```
2. Inside the namespace, run: `ps aux` — only the `bash` and `ps` processes are visible.
3. Run: `echo $$` — the shell is PID 1 inside the namespace.
4. Mount a tmpfs: `mount -t tmpfs none /tmp/ns-test` — this mount is invisible from outside.
5. From the host (another terminal), run: `ls /tmp/ns-test` — the directory is empty or does not exist.
6. Inside the namespace, run `readlink /proc/self/ns/pid` and compare with the host value to confirm different namespace inodes.
7. Exit the namespace. Verify the tmpfs mount is gone: `mount | grep ns-test`.

**Expected output:** Complete PID and mount isolation — the namespace sees only its own processes and mounts.

---

## Readings and References

### Official documentation
- **Linux Kernel — Memory Management** — Subsystem documentation covering page allocators, slab, vmalloc, and memory policies. <https://docs.kernel.org/mm/index.html> (retrieved: 2026-05-29)
- **Linux Kernel — Memory Management (Admin Guide)** — Practical admin-facing guide to memory concepts, hugepages, KSM, and NUMA. <https://docs.kernel.org/admin-guide/mm/index.html> (retrieved: 2026-05-29)
- **Linux Kernel — EEVDF Scheduler** — Official documentation for the Earliest Eligible Virtual Deadline First scheduler (kernel 6.6+). <https://docs.kernel.org/scheduler/sched-eevdf.html> (retrieved: 2026-05-29)
- **Linux Kernel — Control Group v2** — Authoritative reference for cgroups v2 hierarchy, controllers, delegation, and threading. <https://docs.kernel.org/admin-guide/cgroup-v2.html> (retrieved: 2026-05-29)
- **Linux Kernel — Memory Allocation Guide** — Core API guide for kmalloc, vmalloc, GFP flags, and allocation contexts. <https://docs.kernel.org/core-api/memory-allocation.html> (retrieved: 2026-05-29)
- **Kernel Newbies** — Per-release changelogs documenting scheduler, memory, and process subsystem changes. <https://kernelnewbies.org/> (retrieved: 2026-05-29)

### Books
- Stoakes, L., *The Linux Memory Manager*, No Starch Press, 2025. (1 300 pages; the most current deep-dive into Linux mm internals by a kernel mm maintainer)
- Gregg, B., *Systems Performance: Enterprise and the Cloud*, 2nd ed., Addison-Wesley, 2020. (covers perf, BPF, scheduling, memory analysis)
- Kerrisk, M., *The Linux Programming Interface*, No Starch Press, 2010. (definitive POSIX/Linux API reference — clone, mmap, namespaces, cgroups)
- Bovet, D. & Cesati, M., *Understanding the Linux Kernel*, 3rd ed., O'Reilly, 2005. (process management, memory management, scheduling internals)
- Love, R., *Linux Kernel Development*, 3rd ed., Addison-Wesley, 2010. (concise overview of scheduler, process, and mm subsystems)

### Papers and articles
- **"An EEVDF CPU scheduler for Linux"** — LWN article by Jonathan Corbet introducing the EEVDF patch series. <https://lwn.net/Articles/925371/> (retrieved: 2026-05-29)
- **"Completing the EEVDF scheduler"** — LWN follow-up on deferred dequeue, lag decay, and latency-nice integration. <https://lwn.net/Articles/969062/> (retrieved: 2026-05-29)
- **"Index of Further Kernel Documentation"** — Kernel.org curated list of recommended kernel books and tutorials. <https://docs.kernel.org/6.16/process/kernel-docs.html> (retrieved: 2026-05-29)

---

## Cross-References

| Module | Relationship |
|---|---|
| [01.1.a — CPU & Kernel Boundary](01_a_CPU_Kernel_Boundary.md) | Deepens ring transitions, syscall mechanics, and VDSO acceleration introduced here |
| [01.1.b — Scheduler Data Structures](01_b_Scheduler_Data_Structures.md) | Details the red-black tree, run-queue, and EEVDF internals behind CFS/EEVDF covered in sections 5-7 |
| [01.1.c — Memory Management Algorithms](01_c_Memory_Management_Algorithms.md) | Expands buddy allocator, slab/SLUB, and page reclaim algorithms from section 8-12 |
| [01.1.d — File Systems & Storage](01_d_File_Systems_Storage.md) | Connects page cache, writeback, and mmap I/O to the virtual memory concepts here |
| [02 — Networking & TCP/IP Deep Dive](02_Networking_TCP_IP_Deep_Dive.md) | Socket buffers (sk_buff) share slab allocation paths; network namespaces extend namespace isolation |
| [03 — Advanced Data Structures & Algorithms](03_Advanced_Data_Structures_Algorithms.md) | Red-black trees, radix trees, and hash tables underpin scheduler queues and page table walks |

---

## Glossary

| Term | Definition |
|---|---|
| **task_struct** | The kernel data structure (~6-8 KB) representing a single thread of execution; every process and kernel thread has one |
| **fork()** | System call that creates a new process by duplicating the calling process; returns twice (parent gets child PID, child gets 0) |
| **clone()** | Flexible Linux system call for creating processes or threads with fine-grained control over shared resources (address space, FDs, PID namespace) |
| **Virtual Memory** | Abstraction giving each process the illusion of a private, contiguous address space; backed by page tables mapping virtual pages to physical frames |
| **Page Table** | Hierarchical structure (PGD → PUD → PMD → PTE on x86_64) translating virtual addresses to physical frame numbers |
| **TLB** | Translation Lookaside Buffer — a hardware cache of recent virtual-to-physical page translations, avoiding costly page-table walks |
| **CFS** | Completely Fair Scheduler — the default Linux CPU scheduler (until kernel 6.6) using a virtual-runtime red-black tree |
| **EEVDF** | Earliest Eligible Virtual Deadline First — CFS replacement (kernel 6.6+) that assigns virtual deadlines to improve latency fairness |
| **Slab Allocator** | Kernel memory allocator that caches frequently used object sizes in per-type pools to reduce fragmentation and allocation overhead |
| **Buddy Allocator** | Physical page frame allocator that manages free memory in power-of-two blocks, splitting and coalescing to satisfy requests |
| **cgroup** | Control group — kernel mechanism for organising processes into hierarchies and applying resource limits (CPU, memory, I/O) |
| **Namespace** | Kernel feature providing per-process views of global resources (PID, network, mount, user, UTS, IPC, cgroup, time) for isolation |
| **OOM Killer** | Out-Of-Memory killer — kernel subsystem that selects and terminates processes when physical memory and swap are exhausted |
| **Capability** | Fine-grained privilege unit replacing the all-or-nothing root model; e.g., `CAP_NET_RAW` grants raw socket access without full root |
| **Demand Paging** | Memory management strategy where physical pages are allocated only on first access (page fault), not at mapping time |
