# Phase 1: Computer Science & Systems Engineering Foundations — Syllabus

> **Last updated:** 2026-05-29

This phase focuses on the low-level machinery that powers all software. A deep understanding here distinguishes a "coder" from a "software engineer".

## Module 1.1: Operating Systems Internals

**Goal:** Understand how software interacts with hardware.

| Sub-module | File | Focus |
|---|---|---|
| 1.1 | [01_OS_Internals_Processes_Memory.md](01_OS_Internals_Processes_Memory.md) | Process lifecycle, virtual memory, cgroups v2, namespaces |
| 1.1.a | [01_a_CPU_Kernel_Boundary.md](01_a_CPU_Kernel_Boundary.md) | Ring transitions, syscall mechanics, VDSO, KPTI |
| 1.1.b | [01_b_Scheduler_Data_Structures.md](01_b_Scheduler_Data_Structures.md) | CFS, EEVDF, red-black trees, sched_ext, RT scheduling |
| 1.1.c | [01_c_Memory_Management_Algorithms.md](01_c_Memory_Management_Algorithms.md) | Buddy system, SLUB/SLAB, ptmalloc, jemalloc, tcmalloc |
| 1.1.d | [01_d_File_Systems_Storage.md](01_d_File_Systems_Storage.md) | VFS, ext4/XFS/btrfs, journaling, io_uring |

*   **Kernel Architecture:** Monolithic vs. Microkernels, User Space vs. Kernel Space, System Calls.
*   **Process Management:** Processes vs. Threads, PCB (Process Control Block), Context Switching, CPU Scheduling Algorithms (CFS, EEVDF, sched_ext).
*   **Concurrency & Synchronization:** Race Conditions, Critical Sections, Mutexes, Semaphores, Monitors, Deadlocks (Prevention & Avoidance), Atomics.
*   **Memory Management:** Virtual Memory, Paging & Segmentation, TLB (Translation Lookaside Buffer), Page Faults, Swapping, Heap vs. Stack allocation, Memory Allocators (buddy, SLUB, ptmalloc, jemalloc).
*   **I/O Systems:** Interrupts, DMA (Direct Memory Access), Buffered I/O, File Descriptors, Async I/O (epoll, io_uring).
*   **File Systems:** Inodes, Journaling, VFS (Virtual File System), Hard Links vs. Soft Links, CoW (btrfs, ZFS).

## Module 1.2: Networking Deep Dive

**Goal:** Understand how systems communicate.

| Sub-module | File | Focus |
|---|---|---|
| 1.2.a | [02_Networking_TCP_IP_Deep_Dive.md](02_Networking_TCP_IP_Deep_Dive.md) | TCP state machine, CUBIC, BBR, sysctl tuning |
| 1.2.b | [02_a_Modern_Protocols_HTTP_QUIC.md](02_a_Modern_Protocols_HTTP_QUIC.md) | HTTP/2 multiplexing, HTTP/3, QUIC, TLS 1.3 |

*   **Transport Layer (Layer 4):** TCP internals (Three-way handshake, Window Scaling, Congestion Control: Reno/CUBIC/BBR, Head-of-line blocking), UDP (Use cases, QUIC).
*   **Network Layer (Layer 3):** IP addressing, Subnetting, BGP, Routing Tables, NAT.
*   **Application Layer (Layer 7):** HTTP/1.1 vs HTTP/2 (Multiplexing, HPACK) vs HTTP/3 (QUIC, QPACK), DNS (Records, Recursion), TLS 1.3 (0-RTT, PSK), WebSockets.

## Module 1.3: Advanced Data Structures & Algorithms

**Goal:** Optimize for performance and scale.

| File | Focus |
|---|---|
| [03_Advanced_Data_Structures_Algorithms.md](03_Advanced_Data_Structures_Algorithms.md) | Skip lists, B+Trees, LSM-trees, Bloom filters, HyperLogLog, Union-Find |

*   **Probabilistic Data Structures:** Bloom Filters, Count-Min Sketch, HyperLogLog.
*   **Advanced Trees:** B-Trees & B+ Trees (Database indexing), LSM Trees (Log-Structured Merge-trees), Red-Black Trees.
*   **Graph Algorithms:** Dijkstra, A*, Max Flow/Min Cut, Topological Sort.
*   **Distributed Algorithms:** Consistent Hashing, Merkle Trees, Adaptive Radix Trees.

## Module 1.4: Compilers, Interpreters & Runtimes

**Goal:** Understand how code becomes execution.

| File | Focus |
|---|---|
| [04_Compilers_Interpreters.md](04_Compilers_Interpreters.md) | Lexing → codegen pipeline, SSA/IR, LLVM, GC (ZGC, Shenandoah, Go tri-color) |

*   **Compilation Pipeline:** Lexing, Parsing, Semantic Analysis, IR (Intermediate Representation), SSA, Code Generation.
*   **Runtime Environments:** Stack Frames, Calling Conventions, ABI (Application Binary Interface).
*   **Memory Safety:** Manual management (C/C++) vs. Garbage Collection (Tracing, Mark-and-Sweep, Generational, ZGC, Shenandoah).
*   **JIT Compilation:** How V8 (TurboFan/Maglev) or JVM (C2/Graal) optimizes code at runtime (Hot spots, de-optimization, OSR).
