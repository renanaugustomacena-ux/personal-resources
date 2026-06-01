---
corso: "SWE Masterclass"
fase: "1 — Foundations"
modulo: "01.1.c"
titolo: "Memory Management Algorithms Deep Dive"
versione: "Linux 6.x"
livello: "Advanced"
prerequisiti:
  - "Virtual memory and paging fundamentals (Module 01.1)"
  - "Pointer arithmetic and C memory model"
  - "Basic understanding of CPU caches and TLB"
obiettivi:
  - "Trace a page allocation through the buddy system split and coalesce algorithm"
  - "Compare SLAB, SLUB, and SLOB allocator design trade-offs for kernel object caching"
  - "Analyse ptmalloc chunk layout, binning strategies, and coalescing rules"
  - "Explain when brk vs mmap is chosen for user-space allocations and the consequences of each"
  - "Evaluate alternative allocators (jemalloc, tcmalloc, mimalloc) for production workloads"
tag: [memory-management, buddy-system, SLUB, SLAB, malloc, ptmalloc, jemalloc, tcmalloc, mimalloc, linux-kernel]
---

# Module 1.1.c: Memory Management Algorithms Deep Dive

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Trace a page allocation through the buddy system split and coalesce algorithm
> - Compare SLAB, SLUB, and SLOB allocator design trade-offs for kernel object caching
> - Analyse ptmalloc chunk layout, binning strategies, and coalescing rules
> - Explain when brk vs mmap is chosen for user-space allocations and the consequences of each
> - Evaluate alternative allocators (jemalloc, tcmalloc, mimalloc) for production workloads

> **Module 01.1.c** · **Last updated:** 2026-04-27

## Guiding ideas
1. **Buddy system: power-of-2 page allocation in kernel.**
2. **Slab allocator: object cache for kernel structures.**
3. **`malloc` user-space: ptmalloc, jemalloc, tcmalloc, mimalloc.**
4. **TLB (Translation Lookaside Buffer): cache page table entries.**
5. **Huge pages reduce TLB pressure; THP can hurt latency.**


**Date:** 2026-02-06
**Status:** Completed

## 1. Kernel Space Allocators (Physical Memory)

The kernel manages physical RAM. It must satisfy requests for contiguous page frames (e.g., for DMA) and small objects (e.g., `task_struct`).

### 1.1 The Buddy System (Page Allocator)
The **Buddy System** solves the problem of External Fragmentation for large, contiguous blocks.
*   **The Algorithm:**
    *   Memory is managed in lists of **Orders** (0 to 11). Order $N$ represents $2^N$ pages.
    *   **Allocation:** Request for size $S$.
        1.  Calculate minimal Order $K$ such that $2^K 	imes PageSize \ge S$.
        2.  Check list for Order $K$.
        3.  If empty, go to Order $K+1$.
        4.  **Split:** Take block of $K+1$, split into two buddies of Order $K$. Use one, add other to Order $K$ list. Recursive until found.
    *   **Deallocation (Coalescing):**
        1.  Free block $B$.
        2.  Check address of "Buddy" ($Address \oplus Size$).
        3.  If Buddy is also free, **Merge** into block of Order $K+1$.
        4.  Repeat.

### 1.2 The SLAB/SLUB/SLOB Allocators (Object Allocator)
The Buddy System is too coarse (4KB min). We need small objects (32 bytes, 128 bytes).
*   **SLAB (Legacy):**
    *   Uses caching heavily. Each object type (inode, dentry) has a specific cache.
    *   Complex metadata. Good for older hardware, bad for high-core-count scaling.
*   **SLUB (Unqueued - Default):**
    *   **Design:** Simplifies metadata. Most metadata is stored in the `struct page` of the physical frame itself, not in separate headers.
    *   **Performance:** Better CPU cache locality. Merges slabs of similar size classes.
*   **SLOB (Simple - Embedded):**
    *   Just a linked list of blocks. High fragmentation, but tiny code footprint. (Removed in Linux 6.4).

## 2. User Space Allocators (`malloc` Internals)

How does `glibc` or `dlmalloc` manage the heap provided by `brk`/`mmap`?

### 2.1 The Chunk Structure & Boundary Tags
*   **Memory Layout:**
    ```
    [ Header: Size | Flags ]
    [      User Data       ]
    [ Footer: Size         ] (Only if free, usually)
    ```
*   **Boundary Tags (Knuth's Algorithm):**
    *   **Problem:** When freeing pointer `P`, is `P - 1` free? How do we find the start of the previous block?
    *   **Solution:** The **Footer** of the *previous* block sits right before the **Header** of the *current* block.
    *   **Coalescing:**
        1.  Check `(P - 4 bytes)`. It's the previous block's footer. Get size $S_{prev}$.
        2.  Go to `P - S_{prev}` to find the previous header.
        3.  Check previous header's "Free" bit. If free, merge.
        4.  Check next block's header. If free, merge.

### 2.2 Binning Strategies
*   **Fastbins (LIFO):**
    *   Small chunks (16-80 bytes).
    *   Stored in singly-linked lists.
    *   **No Coalescing:** Speed optimization. "If I freed a 32-byte chunk, I'll likely need a 32-byte chunk soon."
*   **Smallbins (FIFO):**
    *   Chunks < 512 bytes.
    *   Doubly-linked lists.
    *   Coalescing enabled.
*   **Unsorted Bin:**
    *   The "Cache" of free chunks.
    *   When a chunk is freed, it goes here first.
    *   If `malloc` doesn't find a chunk in Fast/Small bins, it scans Unsorted. If a chunk here fits, take it. If not, move it to the correct Small/Large bin.
*   **Largebins (Sorted):**
    *   > 512 bytes.
    *   Sorted by size (Skip list or Tree) to support "Best Fit" allocation.

### 2.3 `brk` vs `mmap`
*   **`brk`:** Moves the "program break" (end of heap) up. Fast, but memory must be contiguous. Can't return memory to OS easily if "middle" is still used.
*   **`mmap`:** Allocates distinct anonymous pages. Slower syscall, but can be freed individually. Used for large allocations (> 128KB).

---

## Exercises

### Exercise 1 — Inspect buddy system state

**Setup:** A Linux system with root access.

**Steps:**
1. Read `/proc/buddyinfo`. Each line shows a NUMA node and zone with free block counts for orders 0–10.
2. Identify the zone with the most order-0 (4 KB) blocks and the zone with the most high-order (e.g., order-9, 2 MB) blocks.
3. Allocate a large contiguous block: `dd if=/dev/zero of=/dev/null bs=4M count=1` and re-read `/proc/buddyinfo`.
4. Trigger compaction: `echo 1 > /proc/sys/vm/compact_memory` and compare buddyinfo before and after.

**Expected output:** After compaction, high-order block counts should increase as fragmented low-order blocks are coalesced.

### Exercise 2 — Explore SLUB allocator caches

**Setup:** Root access.

**Steps:**
1. List all slab caches: `cat /proc/slabinfo | head -30`. Note columns: `active_objs`, `objsize`, `pagesperslab`.
2. Identify the cache for `task_struct`: `grep task_struct /proc/slabinfo`.
3. Use `slabtop -o` to see caches sorted by memory usage.
4. Read detailed per-cache stats: `cat /sys/kernel/slab/task_struct/object_size` and `/sys/kernel/slab/task_struct/slab_size`.
5. Fork 100 processes (`for i in $(seq 100); do sleep 60 & done`), re-check `task_struct` active objects count, then kill all.

**Expected output:** `active_objs` for `task_struct` increases by ~100 after forking and decreases after killing the processes.

### Exercise 3 — Trace malloc binning with ltrace

**Setup:** Install `ltrace`. Create a C program that performs allocations of 32, 256, 1024, and 256000 bytes.

**Steps:**
1. Compile: `gcc -o alloc_test alloc_test.c`
2. Trace: `ltrace -e malloc+free ./alloc_test 2>&1`
3. For each allocation size, note whether `malloc` calls `brk` or `mmap` (use `strace -e brk,mmap ./alloc_test`).
4. The 256000-byte allocation should trigger `mmap` (above the 128 KB `MMAP_THRESHOLD`); smaller ones use `brk`.
5. Free all allocations and observe whether `brk` shrinks (it often does not if middle chunks are still allocated).

**Expected output:** `strace` shows `brk` calls for small allocations and an `mmap(NULL, 262144, ...)` call for the 256 KB allocation.

### Exercise 4 — Compare allocator performance

**Setup:** Install `mimalloc` and `jemalloc` development packages. Write a multi-threaded C program that performs 1 million malloc/free cycles with random sizes (16–4096 bytes) across 8 threads.

**Steps:**
1. Compile: `gcc -O2 -pthread -o bench bench.c`
2. Run with default glibc: `time ./bench`
3. Run with jemalloc: `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so time ./bench`
4. Run with mimalloc: `LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libmimalloc.so time ./bench`
5. Compare wall-clock time, peak RSS (`/usr/bin/time -v ./bench`), and thread scalability.

**Expected output:** jemalloc and mimalloc should show lower wall time than glibc ptmalloc under high thread contention due to per-thread caching and reduced lock contention.

### Exercise 5 — Detect heap fragmentation

**Setup:** A C program that alternates allocating and freeing blocks of varying sizes to fragment the heap.

**Steps:**
1. Allocate 10000 blocks of random sizes (8–512 bytes), then free every other block.
2. Call `malloc_stats()` (glibc) or `malloc_info(0, stdout)` to dump arena state.
3. Observe: `Total (incl. mmap)` vs `In-use` — the gap is fragmentation overhead.
4. Call `malloc_trim(0)` and re-check — this should return some freed pages to the OS.
5. Compare `mallinfo2().fordblks` (free bytes in arenas) before and after `malloc_trim`.

**Expected output:** Before `malloc_trim`, the RSS stays high despite freeing half the allocations. After `malloc_trim`, RSS drops as glibc returns unused pages via `madvise(MADV_DONTNEED)`.

---

## Readings and References

### Official documentation
- **Memory Management** — Linux kernel documentation on page allocation, slab allocators, and memory zones. <https://docs.kernel.org/mm/index.html> (retrieved: 2026-05-29)
- **SLUB Allocator** — Oracle Linux blog series on SLUB internals and debugging. <https://blogs.oracle.com/linux/linux-slub-allocator-internals-and-debugging-1> (retrieved: 2026-05-29)
- **The Slab Allocator in the Linux Kernel** — Detailed walkthrough of SLAB/SLUB design. <https://hammertux.github.io/slab-allocator> (retrieved: 2026-05-29)
- **Linux Page Allocator** — Deep dive into the buddy system implementation. <https://syst3mfailure.io/linux-page-allocator/> (retrieved: 2026-05-29)

### Books
- Gorman, M., *Understanding the Linux Virtual Memory Manager*, Prentice Hall, 2004. Free online: <https://www.kernel.org/doc/gorman/>
- Bovet, D. & Cesati, M., *Understanding the Linux Kernel*, 3rd ed., O'Reilly, 2005 — Chapters 8 (Memory Management) and 12 (Slab Allocator).
- Arpaci-Dusseau, R. & Arpaci-Dusseau, A., *Operating Systems: Three Easy Pieces* (OSTEP), free online at <https://pages.cs.wisc.edu/~remzi/OSTEP/> — Chapters on free-space management and paging (retrieved: 2026-05-29).

### Papers and articles
- Bonwick, J., "The Slab Allocator: An Object-Caching Kernel Memory Allocator", USENIX Summer Technical Conference, 1994.
- Leijen, D. et al., "mimalloc: Free List Sharding in Action", Microsoft Research, 2019. <https://github.com/microsoft/mimalloc>
- Smalldatum blog, "Battle of the Mallocators", April 2025. <http://smalldatum.blogspot.com/2025/04/battle-of-mallocators.html> (retrieved: 2026-05-29)

---

## Cross-References

| Module | Relationship |
|---|---|
| [01.1 — OS Internals: Processes & Memory](01_OS_Internals_Processes_Memory.md) | Parent module introducing virtual memory, paging, and process address spaces |
| [01.1.a — CPU / Kernel Boundary](01_a_CPU_Kernel_Boundary.md) | Syscall interface for `brk`, `mmap`, `madvise` that the allocators invoke |
| [01.1.b — Scheduler Data Structures](01_b_Scheduler_Data_Structures.md) | NUMA-aware scheduling interacts with memory placement; `task_struct` allocated via SLUB |
| [01.1.d — File Systems & Storage](01_d_File_Systems_Storage.md) | Page cache and buffer management consume buddy-allocated pages; `mmap` file-backed mappings |
| [03 — Advanced Data Structures & Algorithms](03_Advanced_Data_Structures_Algorithms.md) | Free-list, red-black tree, and skip-list structures used internally by allocators |
| [04 — Compilers & Interpreters](04_Compilers_Interpreters.md) | Runtime memory layout (stack, heap, BSS) that allocators manage at the language-runtime level |

---

## Glossary

| Term | Definition |
|---|---|
| **Buddy System** | Kernel page allocator that manages memory in power-of-2 blocks (orders 0–10), using split and coalesce operations to reduce external fragmentation |
| **SLUB** | The default Linux kernel object allocator (replacing SLAB); stores metadata in `struct page`, reduces TLB thrashing via per-CPU slabs |
| **SLAB** | Original kernel object-caching allocator; maintains per-cache queues with heavy metadata overhead, superseded by SLUB |
| **SLOB** | Minimal embedded allocator using a simple linked-list; removed from the kernel in Linux 6.4 |
| **ptmalloc** | The glibc memory allocator (derived from dlmalloc); uses arenas, bins, and boundary tags for heap management |
| **Fastbin** | ptmalloc bin for small chunks (16–80 bytes) using LIFO singly-linked lists with no coalescing for speed |
| **Unsorted bin** | ptmalloc staging area where recently freed chunks land before being sorted into small or large bins |
| **Boundary tag** | Knuth's technique of storing block size in both the header and footer of a free chunk, enabling O(1) bidirectional coalescing |
| **brk** | Syscall that moves the program break (top of heap) to expand or shrink the data segment; fast but contiguous |
| **mmap** | Syscall that maps anonymous or file-backed pages into the process address space; used by allocators for large allocations (> 128 KB) |
| **jemalloc** | Arena-based allocator developed for FreeBSD; uses thread-local caches and size-class bins to minimise contention |
| **tcmalloc** | Google's thread-caching allocator; uses per-thread free lists for small objects and a central page heap for large allocations |
| **mimalloc** | Microsoft Research allocator with free-list sharding; compact design with strong multi-threaded performance |
| **External fragmentation** | Free memory exists but is scattered in small, non-contiguous blocks, preventing large allocations |
| **Internal fragmentation** | Wasted space inside allocated blocks when the requested size is smaller than the allocated block size |
