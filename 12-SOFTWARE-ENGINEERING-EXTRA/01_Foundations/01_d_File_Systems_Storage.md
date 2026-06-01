---
corso: "SWE Masterclass"
fase: "1 — Foundations"
modulo: "01.1.d"
titolo: "File Systems & Storage Deep Dive"
versione: "Linux 6.x"
livello: "Advanced"
prerequisiti:
  - "Block devices and disk I/O fundamentals (Module 01.1)"
  - "Virtual memory and page cache basics"
  - "POSIX file API (open, read, write, close, fsync)"
obiettivi:
  - "Describe the VFS object model (superblock, inode, dentry, file) and how path resolution traverses the dcache"
  - "Compare ext4 extent-based addressing with legacy block-pointer indirection"
  - "Analyse ext4 journaling modes and their crash-consistency trade-offs"
  - "Contrast epoll's readiness model with io_uring's completion model for high-throughput I/O"
  - "Evaluate copy-on-write filesystem designs (btrfs, ZFS) against traditional journaling filesystems"
tag: [VFS, ext4, io_uring, epoll, btrfs, ZFS, journaling, inode, dentry, block-layer, linux-kernel]
---

# Module 1.1.d: File Systems & Storage Deep Dive

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Describe the VFS object model (superblock, inode, dentry, file) and how path resolution traverses the dcache
> - Compare ext4 extent-based addressing with legacy block-pointer indirection
> - Analyse ext4 journaling modes and their crash-consistency trade-offs
> - Contrast epoll's readiness model with io_uring's completion model for high-throughput I/O
> - Evaluate copy-on-write filesystem designs (btrfs, ZFS) against traditional journaling filesystems

> **Module 01.1.d** · **Last updated:** 2026-04-27

## Guiding ideas
1. **inode-based (ext4, XFS) vs CoW (btrfs, ZFS).**
2. **VFS (Virtual File System) abstraction layer.**
3. **Block layer + I/O scheduler (mq-deadline, none for NVMe).**
4. **fsync vs fdatasync: data integrity vs performance.**


**Date:** 2026-02-06
**Status:** Completed

## 1. The VFS (Virtual File System)
VFS is the abstraction layer that allows Linux to handle `ext4`, `NTFS`, and `/proc` transparently.

### 1.1 The Big Four Objects
1.  **Superblock:** Represents a mounted filesystem (e.g., `/dev/sda1` on `/`).
    *   Stores: Block size, Magic Number, Inode/Block usage bitmaps.
    *   *Kernel Op:* `alloc_super()`.
2.  **Inode (Index Node):** Represents a specific object (file/directory).
    *   Stores: Permissions, UID, GID, Size, Time, **Pointers to Data Blocks**.
    *   *Key:* Unique ID Number. Does **NOT** store the filename.
3.  **Dentry (Directory Entry):** Represents a path component.
    *   Links "Filename" -> "Inode".
    *   Example: Path `/home/user` has three dentries: `/`, `home`, `user`.
    *   **Dentry Cache (dcache):** Huge hash table (`d_lookup`) to speed up path resolution.
4.  **File:** Represents an open file instance (File Descriptor).
    *   Stores: Current Offset (`f_pos`), Mode (Read/Write).
    *   *Note:* Two processes can have two `File` objects pointing to the same `Inode`.

## 2. Ext4 Internals: The Standard

### 2.1 Inode Structure & Data Addressing
*   **Legacy (Ext2/3):** Block Pointers.
    *   12 Direct Pointers.
    *   1 Indirect (Points to a block of pointers).
    *   1 Doubly Indirect.
    *   1 Triply Indirect.
    *   *Problem:* Huge metadata overhead for large contiguous files.
*   **Modern (Ext4):** **Extents**.
    *   Instead of listing every block, it says: "Start at Block 5000, Length 100".
    *   Stored in a **Tree** structure inside the inode (`i_block` array).
    *   *Benefit:* CPU/Disk efficient for large files.

### 2.2 Journaling (Write-Ahead Logging)
Protects metadata integrity during crashes.
*   **Mode: `data=ordered` (Default):**
    1.  Write **Data** to main disk.
    2.  Write **Metadata** to Journal.
    3.  **Commit** Journal.
    4.  Checkpoint (Move metadata to final location).
    *   *Safety:* File content is guaranteed to be "new" or "old", never garbage.
*   **Mode: `data=writeback`:**
    *   Metadata is journaled, Data is not ordered.
    *   *Risk:* After crash, file might contain old garbage data from deleted files.
*   **Mode: `data=journal`:**
    *   Write **Data AND Metadata** to journal first.
    *   *Safety:* Maximum.
    *   *Cost:* Writes everything twice. Slow.

## 3. High-Performance I/O: `io_uring` vs `epoll`

### 3.1 The "Ready" Model: `epoll`
*   **Mechanism:** "Tell me when I can read."
*   **Flow:**
    1.  `epoll_wait()` (Sleep until ready).
    2.  Wake up.
    3.  `read()` (Syscall).
    4.  Kernel copies data to user buffer.
    5.  Return.
*   **Overhead:** Syscall per operation + Data Copy.

### 3.2 The "Completion" Model: `io_uring` (Linux 5.1+)
*   **Mechanism:** "Here is a buffer. Fill it and wake me when done."
*   **Architecture:** Two Shared Ring Buffers (mapped in User & Kernel space).
    *   **Submission Queue (SQ):** User pushes requests.
    *   **Completion Queue (CQ):** Kernel pushes results.
*   **Zero-Syscall Mode:**
    *   If `IORING_SETUP_SQPOLL` is set, a kernel thread polls the SQ.
    *   User just pushes to ring. Kernel picks it up. **Zero syscalls.**
*   **Performance:** Can reach millions of IOPS per core. Used by modern DBs (Postgres/MySQL) and Web Servers.

---

## Exercises

### Exercise 1 — Explore VFS objects with debugfs and stat

**Setup:** A Linux system with an ext4 filesystem.

**Steps:**
1. Create a test file: `echo "hello" > /tmp/vfs_test.txt`
2. Run `stat /tmp/vfs_test.txt`. Record the inode number, block count, and device ID.
3. Use `debugfs -R "stat <INODE>" /dev/sdXN` (your root device) to see the raw ext4 inode: extent tree, timestamps, link count.
4. Trace the dentry cache: `cat /proc/sys/fs/dentry-state` — fields are `nr_dentry`, `nr_unused`, `age_limit`, `want_pages`.
5. Create a hard link: `ln /tmp/vfs_test.txt /tmp/vfs_link`. Re-run `stat` on both — same inode, link count now 2.

**Expected output:** Both paths resolve to the same inode number. `debugfs` shows the extent mapping (e.g., `(0): 12345678`) and the raw inode metadata.

### Exercise 2 — Compare ext4 journaling modes

**Setup:** A spare partition or loop device for safe testing.

**Steps:**
1. Create a loop device: `dd if=/dev/zero of=/tmp/ext4_test.img bs=1M count=256 && losetup /dev/loop0 /tmp/ext4_test.img`
2. Format with ext4: `mkfs.ext4 /dev/loop0`
3. Mount with `data=ordered` (default): `mount -o data=ordered /dev/loop0 /mnt/test`
4. Write a 10 MB file and time `fsync`: `dd if=/dev/urandom of=/mnt/test/file bs=1M count=10 conv=fsync`
5. Unmount, remount with `data=journal`: `mount -o data=journal /dev/loop0 /mnt/test`. Repeat the same write.
6. Compare `fsync` latency. `data=journal` should be ~2x slower (double-write penalty).

**Expected output:** `data=journal` mode shows measurably higher write latency because both data and metadata pass through the journal.

### Exercise 3 — Observe the dentry cache under pressure

**Setup:** Root access.

**Steps:**
1. Read baseline: `cat /proc/sys/fs/dentry-state` and note `nr_dentry`.
2. Generate dentry pressure: `find / -maxdepth 5 -type f 2>/dev/null | wc -l`
3. Re-read dentry state — `nr_dentry` should have grown significantly.
4. Drop the dentry cache: `echo 2 > /proc/sys/vm/drop_caches`
5. Re-read — `nr_dentry` should have dropped sharply. Measure path resolution speed before and after: `time stat /usr/bin/ls` (first access after flush will be slower).

**Expected output:** After dropping caches, the first `stat` call takes longer because the kernel must re-walk the directory tree and re-populate the dcache.

### Exercise 4 — Benchmark epoll vs io_uring for file I/O

**Setup:** Install `fio` (Flexible I/O Tester).

**Steps:**
1. Run sequential read with `libaio` engine: `fio --name=aio --ioengine=libaio --iodepth=64 --rw=read --bs=4k --size=256M --numjobs=1 --filename=/tmp/fio_test --direct=1`
2. Run the same workload with `io_uring` engine: `fio --name=uring --ioengine=io_uring --iodepth=64 --rw=read --bs=4k --size=256M --numjobs=1 --filename=/tmp/fio_test --direct=1`
3. Compare IOPS and latency (avg, p99) from the fio output.
4. Enable SQ polling: add `--sqthread_poll=1` to the io_uring run. This eliminates submission syscalls.
5. Compare: io_uring with SQ poll should show the lowest per-I/O latency.

**Expected output:** io_uring matches or exceeds libaio on IOPS. With `sqthread_poll`, submission overhead drops to near-zero, visible as lower avg latency.

### Exercise 5 — Examine btrfs copy-on-write and snapshots

**Setup:** A spare partition or loop device (512 MB+).

**Steps:**
1. Create a btrfs filesystem: `mkfs.btrfs -f /dev/loop0 && mount /dev/loop0 /mnt/test`
2. Create a subvolume: `btrfs subvolume create /mnt/test/data`
3. Write 50 MB of data: `dd if=/dev/urandom of=/mnt/test/data/file bs=1M count=50`
4. Take a snapshot: `btrfs subvolume snapshot /mnt/test/data /mnt/test/snap1`
5. Check disk usage: `btrfs filesystem du /mnt/test/` — the snapshot shares all blocks (CoW, no extra space used yet).
6. Modify the original file: `dd if=/dev/urandom of=/mnt/test/data/file bs=1M count=10 conv=notrunc`
7. Re-check `btrfs filesystem du` — only the modified 10 MB should appear as exclusive to the original subvolume.

**Expected output:** After the snapshot, `Exclusive` usage is near zero for the snapshot. After modifying 10 MB, the original subvolume shows ~10 MB exclusive and the snapshot retains the old data without duplication.

---

## Readings and References

### Official documentation
- **VFS Overview** — Linux kernel documentation on the Virtual File System layer. <https://docs.kernel.org/filesystems/vfs.html> (retrieved: 2026-05-29)
- **ext4 General Information** — Kernel admin guide for ext4 features, mount options, and journaling modes. <https://docs.kernel.org/admin-guide/ext4.html> (retrieved: 2026-05-29)
- **BTRFS documentation** — Official btrfs docs covering CoW, snapshots, RAID, and subvolumes. <https://btrfs.readthedocs.io/en/latest/> (retrieved: 2026-05-29)
- **io_uring man page** — System call interface for asynchronous I/O. <https://man7.org/linux/man-pages/man7/io_uring.7.html> (retrieved: 2026-05-29)
- **Efficient IO with io_uring** — Jens Axboe's design document (PDF). <https://kernel.dk/io_uring.pdf> (retrieved: 2026-05-29)

### Books
- Bovet, D. & Cesati, M., *Understanding the Linux Kernel*, 3rd ed., O'Reilly, 2005 — Chapters 12 (VFS) and 14 (Block I/O).
- Love, R., *Linux Kernel Development*, 3rd ed., Addison-Wesley, 2010 — Chapter 13 (VFS).
- Arpaci-Dusseau, R. & Arpaci-Dusseau, A., *Operating Systems: Three Easy Pieces* (OSTEP), free online at <https://pages.cs.wisc.edu/~remzi/OSTEP/> — Part III: Persistence (retrieved: 2026-05-29).

### Papers and articles
- Axboe, J., "Efficient IO with io_uring", 2019. <https://kernel.dk/io_uring.pdf>
- Rodeh, O., Bacik, J. & Mason, C., "BTRFS: The Linux B-Tree Filesystem", ACM Transactions on Storage, Vol. 9, No. 3, 2013.
- Ts'o, T., Cao, M. & Dilger, A., "The ext4 filesystem: History and Development", JLS, 2009.

---

## Cross-References

| Module | Relationship |
|---|---|
| [01.1 — OS Internals: Processes & Memory](01_OS_Internals_Processes_Memory.md) | Parent module covering the page cache and process file descriptor table |
| [01.1.a — CPU / Kernel Boundary](01_a_CPU_Kernel_Boundary.md) | Syscall paths for `open`, `read`, `write`, `fsync`, `io_uring_setup` that enter the VFS layer |
| [01.1.b — Scheduler Data Structures](01_b_Scheduler_Data_Structures.md) | I/O-bound task scheduling and wakeup paths triggered by block I/O completion |
| [01.1.c — Memory Management Algorithms](01_c_Memory_Management_Algorithms.md) | Page cache pages allocated via the buddy system; `mmap` file-backed mappings bridge memory and storage |
| [02 — Networking: TCP/IP Deep Dive](02_Networking_TCP_IP_Deep_Dive.md) | `epoll` and `io_uring` are shared I/O multiplexing interfaces used for both storage and network sockets |
| [03 — Advanced Data Structures & Algorithms](03_Advanced_Data_Structures_Algorithms.md) | B-tree and extent tree structures used internally by ext4, btrfs, and XFS for on-disk indexing |

---

## Glossary

| Term | Definition |
|---|---|
| **VFS** | Virtual File System — kernel abstraction layer providing a uniform interface (`open`, `read`, `write`) across all filesystem implementations |
| **inode** | Index node — on-disk and in-memory structure storing file metadata (permissions, size, timestamps) and pointers to data blocks; does not store the filename |
| **dentry** | Directory entry — in-memory VFS object linking a filename to its inode; cached in the dcache for fast path resolution |
| **superblock** | Per-mounted-filesystem structure holding global metadata: block size, inode/block bitmaps, magic number |
| **extent** | Contiguous range of disk blocks described by (start block, length), replacing per-block pointers in ext4 for efficient large-file addressing |
| **journaling** | Write-ahead logging technique that records metadata (and optionally data) changes to a journal before committing them, ensuring crash consistency |
| **io_uring** | Linux asynchronous I/O interface (5.1+) using shared submission and completion ring buffers mapped into user space, enabling zero-syscall I/O |
| **epoll** | Linux I/O multiplexing interface that notifies user space when file descriptors become ready for I/O; readiness-based model |
| **SQPOLL** | io_uring mode where a dedicated kernel thread polls the submission queue, eliminating the `io_uring_enter` syscall for submissions |
| **Copy-on-Write (CoW)** | Filesystem design (btrfs, ZFS) that writes modified data to new blocks instead of overwriting originals, enabling efficient snapshots |
| **dcache** | Kernel hash table caching recently resolved dentries to avoid repeated directory tree traversals |
| **fsync** | POSIX call that flushes a file's data and metadata to persistent storage, guaranteeing durability after return |
