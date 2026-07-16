# Module 5.1: Container Internals (Linux Plumbing)

> **Module 05.1** · **Last updated:** 2026-05-22

## Guiding ideas
1. **Container = namespaces + cgroups + capabilities.**
2. **Namespaces: PID, UTS, IPC, NET, MNT, USER, CGROUP.**
3. **cgroups v2 unified hierarchy.**
4. **rootless containers via `userns`.**
5. **OCI runtime spec defines the container boundary.**
6. **Image layers + overlay filesystem = fast startup, shared disk.**
7. **Seccomp + capabilities = syscall-level sandboxing.**

**Date:** 2026-05-22
**Status:** Completed

---

## 1. What a Container Actually Is

Containers are not virtual machines. They are not a distinct kernel construct. A container is an ordinary Linux process (or process group) with three constraints applied:

1. **Namespaces** restrict what the process can *see*.
2. **cgroups** restrict what the process can *use*.
3. **Capabilities and seccomp** restrict what the process can *do*.

Nothing else. There is no hypervisor, no separate kernel, no hardware emulation. The container process runs directly on the host kernel and shares it with every other container and the host itself.

```
┌────────────────────────────────────────────────┐
│  Host Kernel (single, shared)                  │
│                                                │
│  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │ Container A│  │ Container B│  │ Host     │  │
│  │ ns+cgroups │  │ ns+cgroups │  │ process  │  │
│  └────────────┘  └────────────┘  └──────────┘  │
└────────────────────────────────────────────────┘
```

This shared kernel is both the strength (density, speed) and the attack surface (kernel exploit = game over for all containers on the host).

### 1.1 Historical Context

- **1979:** `chroot` (Unix V7) — change root filesystem for a process. First isolation primitive.
- **2000:** FreeBSD jails — filesystem + process + network isolation.
- **2002:** Linux namespaces begin (`CLONE_NEWNS` for mount namespace in kernel 2.4.19).
- **2006:** cgroups (originally "process containers") merged into Linux 2.6.24.
- **2008:** LXC — first userspace toolkit combining namespaces + cgroups.
- **2013:** Docker — wraps LXC (later libcontainer/runc) with image format, build system, registry.
- **2015:** OCI (Open Container Initiative) formed. Runtime spec + image spec standardized.
- **2020:** cgroups v2 unified hierarchy becomes default in major distros.
- **2024:** Rootless containers, user namespaces, and idmapped mounts reach production maturity.

---

## 2. Linux Namespaces: The Isolation Layer

A namespace wraps a global system resource in an abstraction that makes it appear to the processes within the namespace that they have their own isolated instance of the resource.

There are **eight** namespace types as of kernel 5.6+:

| Namespace | Clone flag | Isolates |
|:----------|:-----------|:---------|
| **Mount (mnt)** | `CLONE_NEWNS` | Filesystem mount points |
| **UTS** | `CLONE_NEWUTS` | Hostname and NIS domain |
| **IPC** | `CLONE_NEWIPC` | System V IPC, POSIX message queues |
| **PID** | `CLONE_NEWPID` | Process IDs |
| **Network (net)** | `CLONE_NEWNET` | Network devices, stacks, ports |
| **User** | `CLONE_NEWUSER` | User and group IDs |
| **Cgroup** | `CLONE_NEWCGROUP` | cgroup root directory |
| **Time** | `CLONE_NEWTIME` | `CLOCK_MONOTONIC` and `CLOCK_BOOTTIME` (kernel 5.6+) |

Syscalls to manipulate namespaces:

```c
// Create a new process in new namespaces
pid_t child = clone(fn, stack, CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWNET | SIGCHLD, arg);

// Move current process into an existing namespace
int fd = open("/proc/<pid>/ns/net", O_RDONLY);
setns(fd, CLONE_NEWNET);

// Create new namespace for current process
unshare(CLONE_NEWPID | CLONE_NEWNS);
```

### 2.1 PID Namespace

Each PID namespace has its own numbering starting from 1. The first process in the namespace becomes PID 1 and acts as the init process for that namespace.

**Mechanics:**
- PID 1 in a container is the init process. If it exits, all other processes in that PID namespace are killed.
- Processes in a child PID namespace are visible in the parent namespace (with a different PID).
- Processes in the parent namespace are **not** visible in the child.
- `kill()` from outside the namespace works (using the external PID). `kill()` from inside only sees local PIDs.

```
Host PID namespace:
  PID 1 (systemd)
  PID 4500 (container init)    <-- same process
  PID 4501 (container worker)

Container PID namespace:
  PID 1 (container init)       <-- same process
  PID 2 (container worker)
```

**Zombie reaping:** PID 1 must reap orphaned child processes. If your container entrypoint is a simple application (Node, Python), it likely does not handle `SIGCHLD`. Solutions:
- `tini` — a lightweight init that reaps zombies and forwards signals.
- `dumb-init` — similar role.
- `--init` flag in Docker (runs `tini` automatically).
- Using a process manager (s6, supervisord) for multi-process containers.

**Nested PID namespaces:** PID namespaces can be nested. Each level sees PIDs in its own and all descendant namespaces. Used by nested container runtimes (container-in-container).

### 2.2 Network (NET) Namespace

Each network namespace gets its own:
- Network interfaces (`eth0`, `lo`)
- IP addresses
- Routing tables
- `iptables` / `nftables` rules
- Sockets and port bindings
- `/proc/net` view

**Practical effect:** Port 80 inside container A and port 80 inside container B do not conflict — they are different network stacks.

**Connectivity patterns:**
1. **veth pairs:** Virtual ethernet cable. One end in the container namespace, one end in the host. The host end is attached to a bridge (e.g., `docker0`, `cni0`).
2. **Bridge networking:** Host Linux bridge connects all veth endpoints. Containers on the same bridge communicate at L2.
3. **Host networking:** Container shares the host's network namespace. No isolation but no NAT overhead. Used for performance-sensitive workloads.
4. **Macvlan:** Container gets its own MAC address on the physical NIC. Appears as a separate device on the network. No bridge needed.
5. **ipvlan:** Similar to macvlan but all containers share the parent's MAC address. Better for environments that restrict MAC counts (some cloud VPCs).

```
┌──────────────────────────────────────────┐
│ Host network namespace                   │
│                                          │
│  docker0 (bridge) ─── eth0 (physical)    │
│   │        │                             │
│  veth1    veth2                           │
│   │        │                             │
│ ┌─┴──┐  ┌─┴──┐                           │
│ │eth0│  │eth0│  (inside container ns)     │
│ │C1  │  │C2  │                           │
│ └────┘  └────┘                           │
└──────────────────────────────────────────┘
```

**Port mapping:** `-p 8080:80` sets up `iptables` DNAT rules on the host: traffic arriving at host:8080 is forwarded to container-ip:80.

### 2.3 Mount (MNT) Namespace

The first namespace type added to Linux (2.4.19). Each mount namespace has its own mount table — changes to mounts (mount, umount, bind-mount) are invisible to other namespaces.

**Container filesystem isolation:**
1. Container runtime creates a new mount namespace.
2. `pivot_root()` switches the root filesystem to the container's root (overlayFS merge).
3. Old root is unmounted.
4. Result: the container sees only its own filesystem tree.

**Mount propagation modes:**
| Mode | Behavior |
|:-----|:---------|
| `private` | Mounts are not shared in either direction. Default for containers. |
| `shared` | Mounts propagate both ways between namespaces. |
| `slave` | Mounts propagate host → container but not reverse. |
| `unbindable` | Cannot be bind-mounted at all. |

Docker uses `rprivate` by default. Kubernetes sometimes requires `rshared` for volume mounts that need to be visible to the kubelet.

**`/proc` and `/sys`:** Container runtimes remount `/proc` and `/sys` inside the mount namespace (often as read-only or with selective masking) to prevent the container from seeing host-level process and kernel information.

### 2.4 UTS Namespace

Isolates the hostname and NIS domain name. Each container can have its own hostname without affecting the host.

```bash
# Inside container
hostname my-app-container
# Does not change host hostname
```

Trivial but necessary for applications that log or identify by hostname. In Kubernetes, the pod's hostname is set via UTS namespace.

### 2.5 IPC Namespace

Isolates System V IPC objects (shared memory segments, semaphore sets, message queues) and POSIX message queues.

Without IPC namespace isolation, a containerized process could:
- Attach to shared memory created by another container or the host.
- Interfere with semaphores used by other processes.

**Kubernetes pod-level sharing:** Containers within the same pod can optionally share IPC namespace (via `shareProcessNamespace: true`), allowing inter-container communication through shared memory.

### 2.6 User Namespace

Maps UIDs/GIDs inside the namespace to different UIDs/GIDs outside. This is the foundation of **rootless containers**.

```
Container view:            Host view:
  root (UID 0)       →      user (UID 100000)
  app  (UID 1000)    →      user (UID 101000)
```

**Mapping configuration:** `/proc/<pid>/uid_map` and `/proc/<pid>/gid_map`:
```
# Inside NS UID  |  Outside NS UID  |  Range size
0                    100000              65536
```

**Security implications:**
- Even if a process escapes the container, it runs as an unprivileged user on the host.
- `CAP_SYS_ADMIN` inside the user namespace does NOT grant `CAP_SYS_ADMIN` on the host.
- Some operations that require root inside the namespace (mount, create network interfaces) are permitted because the user namespace owns the mount/net namespace.

**Subordinate ID ranges:** `/etc/subuid` and `/etc/subgid` define which UIDs/GIDs a host user is allowed to map:
```
renan:100000:65536
```
This grants user `renan` 65536 UIDs starting from 100000.

**idmapped mounts (kernel 5.12+):** Allow mounting a filesystem with UID/GID translation at the VFS level, without user namespaces. Useful for sharing volumes between containers running as different UIDs.

### 2.7 Cgroup Namespace

Isolates the cgroup root view. A process inside a cgroup namespace sees its own cgroup as the root (`/`), hiding the host's cgroup hierarchy.

Without cgroup namespace: a container process reads `/proc/self/cgroup` and sees its full path on the host (`/system.slice/docker-abc123.scope`). With it: the process sees `/`.

This prevents information leakage about the host's cgroup structure and prevents the container from navigating to other containers' cgroups.

### 2.8 Time Namespace (kernel 5.6+)

Allows per-namespace offsets for `CLOCK_MONOTONIC` and `CLOCK_BOOTTIME`. **Does not** affect wall-clock time (`CLOCK_REALTIME`).

**Use case:** Checkpoint/restore (CRIU). A container checkpointed and restored on a different host would see a jump in monotonic clock. Time namespace allows setting an offset so the container perceives a continuous clock.

```bash
# Check time namespace offset
cat /proc/<pid>/timens_offsets
# monotonic  <seconds> <nanoseconds>
# boottime   <seconds> <nanoseconds>
```

### 2.9 Namespace Inspection

```bash
# List all namespaces for a process
ls -la /proc/<pid>/ns/
# lrwxrwxrwx 1 root root 0 ... cgroup -> 'cgroup:[4026531835]'
# lrwxrwxrwx 1 root root 0 ... ipc -> 'ipc:[4026532262]'
# lrwxrwxrwx 1 root root 0 ... mnt -> 'mnt:[4026532260]'
# lrwxrwxrwx 1 root root 0 ... net -> 'net:[4026532264]'
# lrwxrwxrwx 1 root root 0 ... pid -> 'pid:[4026532263]'
# lrwxrwxrwx 1 root root 0 ... user -> 'user:[4026531837]'
# lrwxrwxrwx 1 root root 0 ... uts -> 'uts:[4026532261]'

# Enter a container's namespace
nsenter --target <pid> --mount --uts --ipc --net --pid -- /bin/sh

# Create a process in new namespaces (without containers)
unshare --pid --fork --mount-proc /bin/bash
# You are now PID 1 in a new PID namespace
```

---

## 3. Control Groups (cgroups): The Resource Limits Layer

Namespaces hide what a process can see. cgroups limit what it can use. cgroups organize processes into hierarchical groups and apply resource accounting and limits.

### 3.1 cgroups v1 Architecture

Multiple independent hierarchies, one per resource controller:

```
/sys/fs/cgroup/
├── cpu/
│   └── docker/
│       └── container-abc/
│           ├── cpu.shares           # relative weight (1024 default)
│           ├── cpu.cfs_quota_us     # hard limit (microseconds per period)
│           └── cpu.cfs_period_us    # period length (100000 = 100ms)
├── memory/
│   └── docker/
│       └── container-abc/
│           ├── memory.limit_in_bytes
│           ├── memory.usage_in_bytes
│           ├── memory.oom_control
│           └── memory.stat
├── blkio/
├── cpuset/
├── devices/
├── freezer/
├── net_cls/
├── net_prio/
├── pids/
└── hugetlb/
```

**Problems with v1:**
- Each controller has its own hierarchy — a process can be in different groups for CPU vs memory.
- No unified view of resource usage.
- Thread-granularity cgroup membership is a mess.
- No Pressure Stall Information (PSI) support.
- Some controllers (memory) have inconsistent semantics across kernel versions.

### 3.2 cgroups v2 Unified Hierarchy

Single hierarchy for all controllers. Every process belongs to exactly one node in the tree.

```
/sys/fs/cgroup/
├── cgroup.controllers    # available: cpu memory io pids
├── cgroup.subtree_control # enabled: cpu memory io pids
├── system.slice/
│   └── docker-abc123.scope/
│       ├── cgroup.type          # "domain" (default)
│       ├── cpu.weight           # 1-10000 (default 100, replaces shares)
│       ├── cpu.max              # "$MAX $PERIOD" (e.g., "50000 100000" = 50%)
│       ├── cpu.stat             # usage_usec, system_usec, etc.
│       ├── memory.max           # hard limit (OOM on exceed)
│       ├── memory.high          # soft limit (throttle reclaim)
│       ├── memory.current       # actual usage
│       ├── memory.stat          # detailed breakdown
│       ├── memory.pressure      # PSI metrics
│       ├── io.max               # per-device IOPS/bandwidth limits
│       ├── io.weight            # relative I/O priority
│       ├── pids.max             # max number of processes
│       └── pids.current         # current count
```

### 3.3 CPU Control

**cpu.weight (soft limit):**
- Relative priority when CPU is contended.
- Range: 1–10000 (default 100).
- If only one container wants CPU, it gets 100% regardless of weight.
- If two containers compete, CPU is divided proportional to weights.

**cpu.max (hard limit):**
- Format: `$MAX $PERIOD` in microseconds.
- `"50000 100000"` = 50ms of CPU per 100ms period = 50% of one core.
- `"max 100000"` = unlimited (default).
- CFS bandwidth control: when the quota is exhausted, all threads in the cgroup are throttled (sleeping) until the next period.

**CPU throttling is a silent performance killer:**
```bash
# Check if a container is being throttled
cat /sys/fs/cgroup/system.slice/docker-abc123.scope/cpu.stat
# nr_throttled 12453    <-- how many times throttled
# throttled_usec 89123456  <-- total time spent throttled
```

**CFS vs SCHED_DEADLINE:** Standard containers use CFS (Completely Fair Scheduler). For real-time workloads, SCHED_DEADLINE can be configured but is rarely used in container contexts.

**cpuset controller:** Pins a cgroup to specific CPU cores and NUMA nodes:
```
cpuset.cpus = 0-3       # only cores 0,1,2,3
cpuset.mems = 0         # NUMA node 0
```
Used for latency-sensitive workloads (trading systems, game servers) to avoid context-switch overhead.

### 3.4 Memory Control

**memory.max (hard limit):**
- If usage exceeds this, the OOM killer is invoked.
- The kernel selects a process in the cgroup to kill based on OOM score.
- This is the limit you set via `docker run --memory 512m` or Kubernetes `resources.limits.memory`.

**memory.high (soft limit / throttle):**
- When usage exceeds `memory.high`, the kernel aggressively reclaims memory (page cache eviction, swap-out).
- The process is not killed but is throttled (slowed by reclaim pressure).
- Use as a warning/backpressure mechanism.

**memory.low (best-effort protection):**
- Memory in this cgroup is protected from reclaim when the system is under pressure, unless there is no other reclaimable memory.
- Useful for protecting critical services.

**memory.min (hard protection):**
- Absolutely protected. The kernel will never reclaim below this amount.

**Memory accounting breakdown (memory.stat):**
```
anon 204800000           # anonymous memory (heap, stack, mmap private)
file 102400000           # page cache (file-backed)
kernel 8192000           # kernel memory (slab, page tables, etc.)
shmem 0                  # shared memory (tmpfs, SysV shm)
sock 4096                # socket buffers
```

**OOM Killer mechanics:**
1. Process allocates memory → kernel page fault handler checks cgroup limit.
2. If usage >= `memory.max`, kernel attempts reclaim (page cache, swap).
3. If reclaim fails, OOM killer is invoked.
4. Kernel selects victim based on `oom_score_adj` (container runtimes set this).
5. Victim receives SIGKILL.
6. Container runtime detects OOM via `memory.events` (`oom_kill` counter).

**Kubernetes OOMKilled:** When a container exceeds its memory limit, the OOM killer fires, the container exits with code 137 (SIGKILL), and Kubernetes reports status `OOMKilled`.

### 3.5 I/O Control

**io.max:** Per-device limits on bandwidth and IOPS:
```
# Major:Minor rbps wbps riops wiops
8:0 rbps=10485760 wbps=5242880 riops=1000 wiops=500
# Device 8:0 limited to 10MB/s read, 5MB/s write, 1000/500 IOPS
```

**io.weight:** Relative I/O priority (1-10000). Only effective under contention.

**io.latency:** Target latency for I/O operations. Kernel adjusts throttling to meet latency targets.

**Caveat:** I/O cgroup limits work reliably only for direct I/O. Buffered I/O goes through the page cache and is accounted to the memory controller, not the I/O controller. This is a common source of confusion.

### 3.6 PIDs Controller

```
pids.max = 100      # max 100 processes in this cgroup
pids.current = 23   # currently 23
```

Prevents fork bombs. A container that tries to `fork()` beyond `pids.max` gets `EAGAIN`.

### 3.7 Pressure Stall Information (PSI) — cgroups v2 Only

PSI quantifies how much time tasks in a cgroup spend waiting for resources:

```bash
cat /sys/fs/cgroup/.../cpu.pressure
# some avg10=4.50 avg60=2.30 avg300=1.15 total=298428
# full avg10=0.00 avg60=0.00 avg300=0.00 total=0

cat /sys/fs/cgroup/.../memory.pressure
# some avg10=10.20 avg60=5.40 avg300=2.10 total=1894573
# full avg10=8.50 avg60=4.20 avg300=1.80 total=1542891
```

- **some:** Percentage of time at least one task was stalled.
- **full:** Percentage of time all tasks were stalled (nobody could make progress).

PSI is superior to utilization for detecting resource saturation. 80% CPU utilization may or may not be a problem; 20% PSI `some` for CPU definitively means tasks are waiting.

---

## 4. Linux Capabilities

Traditional Unix: either you are root (UID 0, all-powerful) or you are not. Linux capabilities break root privilege into ~40 discrete capabilities.

### 4.1 Key Capabilities

| Capability | Allows | Container default |
|:-----------|:-------|:-----------------|
| `CAP_NET_BIND_SERVICE` | Bind to ports < 1024 | Granted |
| `CAP_CHOWN` | Change file ownership | Granted |
| `CAP_DAC_OVERRIDE` | Bypass file permission checks | Granted |
| `CAP_FOWNER` | Bypass permission checks on operations requiring matching file owner | Granted |
| `CAP_KILL` | Send signals to any process | Granted |
| `CAP_SETUID` / `CAP_SETGID` | Manipulate process UIDs/GIDs | Granted |
| `CAP_NET_RAW` | Use RAW and PACKET sockets | Granted (often dropped) |
| `CAP_SYS_ADMIN` | Catch-all admin capability (mount, namespace, etc.) | **Dropped** |
| `CAP_SYS_PTRACE` | Trace arbitrary processes | **Dropped** |
| `CAP_NET_ADMIN` | Network configuration (iptables, routing) | **Dropped** |
| `CAP_SYS_RAWIO` | Perform I/O port operations | **Dropped** |
| `CAP_SYS_MODULE` | Load/unload kernel modules | **Dropped** |
| `CAP_SYS_TIME` | Set system clock | **Dropped** |

### 4.2 Docker Default Capabilities

Docker drops all but a curated set of 14 capabilities. Running `--cap-drop ALL --cap-add <only-needed>` is best practice.

```bash
# Run with absolutely minimal capabilities
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE my-web-app

# Check capabilities of a running container
docker exec my-container cat /proc/1/status | grep Cap
# CapPrm: 00000000a80425fb  (permitted)
# CapEff: 00000000a80425fb  (effective)
# CapBnd: 00000000a80425fb  (bounding set)
```

**Decoding capability masks:**
```bash
capsh --decode=00000000a80425fb
```

### 4.3 Privileged Containers

`docker run --privileged` grants ALL capabilities, disables seccomp, enables device access, and uses the host's `/dev`. This is almost never necessary and should be treated as a red flag.

**Legitimate uses:** Docker-in-Docker (DinD) for CI, network debugging tools, hardware access. Even then, prefer specific capability grants over `--privileged`.

---

## 5. Seccomp: Syscall Filtering

Seccomp (Secure Computing) filters the syscalls a process can make using BPF programs. Two modes:

1. **Strict mode:** Only `read()`, `write()`, `_exit()`, `sigreturn()`. Unusable for general purpose.
2. **Filter mode (seccomp-bpf):** BPF program evaluates each syscall and decides: `ALLOW`, `KILL`, `TRAP`, `ERRNO`, `TRACE`, `LOG`.

### 5.1 Docker Default Seccomp Profile

Docker ships a default profile that blocks ~44 of ~300+ syscalls. Notable blocked syscalls:

| Syscall | Why blocked |
|:--------|:-----------|
| `reboot` | Container should not reboot the host |
| `mount` / `umount2` | Filesystem manipulation (allowed with `CAP_SYS_ADMIN`) |
| `init_module` / `delete_module` | Kernel module loading |
| `acct` | Process accounting |
| `settimeofday` / `clock_settime` | System clock manipulation |
| `swapon` / `swapoff` | Swap management |
| `pivot_root` | Change root filesystem |
| `keyctl` | Kernel keyring manipulation |
| `bpf` | BPF program loading (security-sensitive) |
| `userfaultfd` | Often used in kernel exploits |

### 5.2 Custom Seccomp Profiles

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_AARCH64"],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat",
                "mmap", "mprotect", "munmap", "brk", "rt_sigaction",
                "access", "pipe", "select", "sched_yield", "clone",
                "execve", "exit_group", "arch_prctl", "futex",
                "epoll_wait", "epoll_ctl", "socket", "connect",
                "accept", "sendto", "recvfrom", "bind", "listen"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

```bash
# Run with custom profile
docker run --security-opt seccomp=my-profile.json my-app

# Run with no seccomp (dangerous)
docker run --security-opt seccomp=unconfined my-app

# Audit mode: log denied syscalls without blocking
# Set defaultAction to SCMP_ACT_LOG and monitor /var/log/audit/
```

### 5.3 Seccomp Notify (kernel 5.9+)

`SCMP_ACT_NOTIFY` sends the syscall to a supervisor process for a policy decision. The supervisor can inspect arguments, modify them, or emulate the syscall.

**Use case:** rootless containers using `FUSE` for mounting filesystems — `mount()` syscall is intercepted by the container runtime, which performs the mount on behalf of the container.

### 5.4 Generating Seccomp Profiles

**oci-seccomp-bpf-hook:** Records syscalls made by a container during a test run and generates a profile. Run your E2E tests against the container, collect the profile, then enforce it.

```bash
# Record syscalls
docker run --annotation io.containers.trace-syscall=of:/tmp/profile.json my-app

# Or use strace
strace -f -e trace=%desc,%file,%ipc,%memory,%network,%process,%signal \
  -o /tmp/strace.out <command>
```

---

## 6. OverlayFS: The Container Filesystem

### 6.1 Architecture

OverlayFS (overlay2 driver in Docker) merges multiple directory trees into a single unified view:

```
┌─────────────────────────────────┐
│         Merged (Union View)     │  <- what the container process sees
├─────────────────────────────────┤
│  UpperDir (Read-Write Layer)    │  <- container-specific changes
├─────────────────────────────────┤
│  WorkDir (Kernel Scratchpad)    │  <- atomic operations staging
├─────────────────────────────────┤
│  LowerDir 3 (Layer 3)          │  <- e.g., app code
│  LowerDir 2 (Layer 2)          │  <- e.g., pip install
│  LowerDir 1 (Layer 1)          │  <- e.g., ubuntu:24.04
└─────────────────────────────────┘
```

**Mount command (what runc does internally):**
```bash
mount -t overlay overlay \
  -o lowerdir=/layer3:/layer2:/layer1,\
     upperdir=/container/upper,\
     workdir=/container/work \
  /container/merged
```

### 6.2 Copy-on-Write (CoW) Mechanics

| Operation | Behavior |
|:----------|:---------|
| **Read** | Kernel checks upperdir first, then lowerdirs top-down. First match wins. Zero copy for reads. |
| **Write (existing file)** | Kernel copies file from lowerdir to upperdir (`copy_up`), then modifies the upper copy. Subsequent reads go to upper. |
| **Write (new file)** | Created directly in upperdir. |
| **Delete** | Whiteout file (`c 0 0` character device) created in upperdir. Hides the lower file. |
| **Delete directory** | Opaque directory (xattr `trusted.overlay.opaque=y`) in upperdir. Hides entire lower directory. |
| **Rename** | If file is in lower, copy-up first, then rename in upper. Cross-device rename issues possible for directories. |
| **Hardlink** | Can hardlink between files in the same layer. Cross-layer hardlinks are copy-ups. |

**copy_up performance:** The first write to a large file in a lower layer is expensive — the entire file must be copied to the upper layer, even if you only modify 1 byte. This is why application log files, database files, and other frequently-written data should be on **volumes**, not the container layer.

### 6.3 Alternative Storage Drivers

| Driver | Notes |
|:-------|:------|
| **overlay2** | Default. Best performance on most kernels (4.0+). |
| **devicemapper** | Thin provisioning on block devices. Was RHEL default pre-overlay2. |
| **btrfs** | Uses Btrfs subvolumes and snapshots. Good if host is Btrfs. |
| **zfs** | Uses ZFS clones. Excellent data integrity but complex. |
| **fuse-overlayfs** | Userspace overlay for rootless containers (when kernel overlay with userns is unavailable). |
| **stargz/eStargz** | Lazy-pulling: download only the file ranges accessed. Speeds up cold start for large images. |

### 6.4 Layer Deduplication

The same image layer (identified by content-addressable digest) is stored **once** on disk regardless of how many containers use it. 1000 containers from the same image share the lower layers and each only has its own thin upper layer.

```bash
# Inspect layers of an image
docker inspect --format '{{range .RootFS.Layers}}{{println .}}{{end}}' nginx:latest
# sha256:abc123...  (base)
# sha256:def456...  (apt install)
# sha256:ghi789...  (nginx config)
```

---

## 7. OCI Specifications

The Open Container Initiative defines three specifications:

### 7.1 OCI Runtime Specification

Defines how to run a container given a filesystem bundle. The spec prescribes:

1. **config.json:** Container configuration including:
   - Root filesystem path
   - Mounts
   - Process (args, env, cwd, capabilities, user, rlimits)
   - Namespaces to create/join
   - cgroup path and resource limits
   - Seccomp profile
   - Linux-specific settings (sysctl, maskedPaths, readonlyPaths)
   - Hooks (prestart, createRuntime, createContainer, startContainer, poststart, poststop)

2. **Root filesystem:** An extracted image (directory tree).

3. **Lifecycle operations:**
   - `create` — set up namespaces, cgroups, filesystem; run `createRuntime` hooks; process is NOT started.
   - `start` — execute the container process; run `startContainer` and `poststart` hooks.
   - `kill` — send signal to container process.
   - `delete` — clean up cgroups, namespaces; run `poststop` hooks.

**Minimal config.json example:**
```json
{
  "ociVersion": "1.1.0",
  "process": {
    "terminal": false,
    "user": { "uid": 0, "gid": 0 },
    "args": ["/bin/sh", "-c", "echo hello"],
    "env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
    "cwd": "/",
    "capabilities": {
      "bounding": ["CAP_AUDIT_WRITE", "CAP_KILL", "CAP_NET_BIND_SERVICE"],
      "effective": ["CAP_AUDIT_WRITE", "CAP_KILL", "CAP_NET_BIND_SERVICE"]
    }
  },
  "root": { "path": "rootfs", "readonly": true },
  "linux": {
    "namespaces": [
      {"type": "pid"},
      {"type": "network"},
      {"type": "ipc"},
      {"type": "uts"},
      {"type": "mount"}
    ]
  }
}
```

### 7.2 OCI Image Specification

Defines the format for container images. An image consists of:

1. **Image manifest:** JSON pointing to config and layers.
2. **Image config:** JSON with creation metadata, default runtime settings (cmd, env, exposed ports), and layer diff IDs.
3. **Layers:** Gzipped tar archives of filesystem diffs. Each layer is content-addressable by SHA256 digest.
4. **Image index (manifest list):** Points to platform-specific manifests (amd64, arm64, etc.).

```
Image Index (manifest list)
├── Manifest (linux/amd64)
│   ├── Config blob (JSON)
│   └── Layer blobs (tar.gz)
├── Manifest (linux/arm64)
│   ├── Config blob (JSON)
│   └── Layer blobs (tar.gz)
```

**Content addressability:** Every blob is identified by `sha256:<digest>`. This enables global deduplication — if two images share a layer, registries and runtimes store it once.

### 7.3 OCI Distribution Specification

Defines the HTTP API for pushing/pulling images from registries. Based on Docker Registry v2 API.

Key endpoints:
```
GET  /v2/                                  # version check
GET  /v2/<name>/manifests/<reference>       # pull manifest
PUT  /v2/<name>/manifests/<reference>       # push manifest
GET  /v2/<name>/blobs/<digest>              # pull layer
POST /v2/<name>/blobs/uploads/              # initiate layer push
```

---

## 8. Container Runtimes

### 8.1 Runtime Layers

```
                    ┌─────────────┐
                    │ Container   │
                    │ Engine      │  Docker, Podman, containerd
                    │ (high-level)│
                    └──────┬──────┘
                           │ OCI Runtime Spec (config.json + rootfs)
                    ┌──────▼──────┐
                    │ OCI Runtime │  runc, crun, youki, gVisor, Kata
                    │ (low-level) │
                    └──────┬──────┘
                           │ syscalls (clone, mount, pivot_root, execve)
                    ┌──────▼──────┐
                    │ Linux Kernel│
                    └─────────────┘
```

### 8.2 runc

Reference implementation of the OCI runtime spec. Written in Go. Created by Docker, donated to OCI.

- Uses `clone()` + `execve()` to create namespaced processes.
- Sets up cgroups, capabilities, seccomp.
- Performs `pivot_root()` to switch filesystem.
- Spawns a short-lived "runc init" process that sets up the namespace environment, then `exec()`s the actual container entrypoint.

```bash
# Run a container directly with runc
mkdir bundle && cd bundle
mkdir rootfs
docker export $(docker create alpine) | tar -C rootfs -xf -
runc spec   # generates config.json
runc create mycontainer
runc start mycontainer
runc list
runc delete mycontainer
```

### 8.3 crun

Alternative OCI runtime written in C. Benefits:
- ~50x faster startup than runc (no Go runtime initialization).
- Lower memory footprint.
- Supports cgroups v2 features earlier than runc.
- Supports WASM workloads via WasmEdge/Wasmtime.
- Default runtime in Podman on newer Fedora/RHEL.

### 8.4 youki

OCI runtime written in Rust. Focus on safety and performance. Aims to be a drop-in runc replacement with memory safety guarantees.

### 8.5 gVisor (runsc)

Google's application kernel. Intercepts syscalls from the container and re-implements them in userspace:

```
┌──────────────┐
│ Container    │ application
│ process      │
└──────┬───────┘
       │ syscalls (ptrace or KVM intercept)
┌──────▼───────┐
│ Sentry       │ userspace kernel (Go)
│ (gVisor)     │
└──────┬───────┘
       │ limited syscalls
┌──────▼───────┐
│ Host Kernel  │
└──────────────┘
```

**Trade-offs:**
- **Pro:** Dramatically reduced kernel attack surface. Container sees a fake kernel.
- **Con:** Performance overhead (syscall interception), incomplete syscall compatibility (not all Linux syscalls implemented), higher memory usage.
- **Use case:** Multi-tenant untrusted workloads (Google Cloud Run uses gVisor).

### 8.6 Kata Containers

Lightweight VM per container. Each container runs in its own virtual machine with its own kernel:

```
┌──────────────┐
│ Container    │ runs inside a lightweight VM
│ process      │
├──────────────┤
│ Guest Kernel │ (stripped-down Linux / NEMU)
├──────────────┤
│ QEMU/Cloud   │
│ Hypervisor   │ or Firecracker
├──────────────┤
│ Host Kernel  │
└──────────────┘
```

**Trade-offs:**
- **Pro:** Strong isolation (separate kernel). Kernel vulnerability in the guest does not compromise host.
- **Con:** VM startup overhead (~100ms, compared to ~10ms for runc), higher memory per container.
- Compatible with the OCI runtime spec — Kubernetes sees it as a regular runtime.

### 8.7 Firecracker

Amazon's micro-VM monitor. Purpose-built for serverless (Lambda, Fargate):
- Minimal device model (no GPU, USB, PCI).
- ~125ms boot time, <5 MiB memory overhead.
- Uses KVM for hardware virtualization.
- Not OCI-compatible directly — typically fronted by containerd's Firecracker snapshotter.

---

## 9. Container Image Building

### 9.1 Dockerfile Basics and Layer Caching

Each `RUN`, `COPY`, `ADD` instruction creates a new layer. Docker caches layers and reuses them if the instruction and its inputs have not changed.

**Cache invalidation rules:**
- `RUN`: invalidated if the command string changes.
- `COPY`: invalidated if any source file's checksum changes.
- Once a cache miss occurs, all subsequent layers are rebuilt (cache is linear).

**Order matters for caching:**
```dockerfile
# BAD: copying source before installing deps busts dep cache on every code change
FROM node:22-slim
COPY . /app
RUN npm ci

# GOOD: install deps first (cached), then copy source
FROM node:22-slim
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production
COPY . .
```

### 9.2 Multi-Stage Builds

Separate build environment from runtime environment:

```dockerfile
# Stage 1: build
FROM golang:1.23 AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /app -ldflags="-s -w" .

# Stage 2: runtime
FROM scratch
COPY --from=builder /app /app
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
ENTRYPOINT ["/app"]
```

**Result:** Build image is ~1 GB (Go toolchain). Runtime image is ~5 MB (static binary + certs).

### 9.3 BuildKit

Docker's next-generation builder (default since Docker 23.0). Key features:

**Parallel stage execution:** Independent stages build concurrently.

**Cache mounts:** Persist build caches across builds without baking them into layers:
```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

RUN --mount=type=cache,target=/root/.cache/go-build \
    go build -o /app .

RUN --mount=type=cache,target=/root/.m2 \
    mvn package -DskipTests
```

**Secret mounts:** Inject secrets at build time without leaking into layers:
```dockerfile
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci
```

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc .
```

**SSH mounts:** Forward SSH agent for private repo access during build:
```dockerfile
RUN --mount=type=ssh git clone git@github.com:private/repo.git
```

**Heredocs:** Multi-line RUN without shell escapes:
```dockerfile
RUN <<EOF
apt-get update
apt-get install -y curl wget git
rm -rf /var/lib/apt/lists/*
EOF
```

### 9.4 Distroless and Minimal Base Images

| Base image | Size | Contains |
|:-----------|:-----|:---------|
| `ubuntu:24.04` | ~78 MB | Full Ubuntu userspace |
| `debian:bookworm-slim` | ~75 MB | Minimal Debian |
| `alpine:3.20` | ~7 MB | musl libc, busybox |
| `gcr.io/distroless/static` | ~2 MB | CA certs, tzdata, /etc/passwd |
| `gcr.io/distroless/cc` | ~12 MB | + libgcc, libstdc++ |
| `gcr.io/distroless/java21` | ~200 MB | + JRE |
| `scratch` | 0 MB | Empty filesystem |

**Alpine caveats:** Uses musl libc instead of glibc. Some applications (especially those using DNS resolution, locale handling, or CGo) behave differently or crash on musl. Known issues:
- DNS: musl resolver does not support `search` domain + `ndots` properly. Causes intermittent DNS failures in Kubernetes.
- Threading: musl's default thread stack size is 128 KB vs glibc's 8 MB.
- Locale: musl does not support `LC_ALL` locale categories fully.

Distroless images have no shell, no package manager — cannot exec into them for debugging. Use `debug` variants (`gcr.io/distroless/static:debug`) which include busybox.

### 9.5 Image Scanning

Scan images for known CVEs before deployment:

| Tool | Notes |
|:-----|:------|
| **Trivy** | Aqua Security. OSS. Image, filesystem, IaC, SBOM scanning. |
| **Grype** | Anchore. OSS. Fast vulnerability matching. |
| **Syft** | Anchore. Generates SBOMs (SPDX, CycloneDX). |
| **Snyk Container** | Commercial with free tier. |
| **Docker Scout** | Docker's built-in (commercial). |

```bash
# Scan with Trivy
trivy image --severity HIGH,CRITICAL nginx:latest

# Generate SBOM
syft packages nginx:latest -o spdx-json > nginx-sbom.json
```

### 9.6 Image Signing and Verification

**Cosign (Sigstore):**
```bash
# Sign
cosign sign --key cosign.key my-registry.io/my-app:v1.2.3

# Verify
cosign verify --key cosign.pub my-registry.io/my-app:v1.2.3
```

**Keyless signing (Fulcio + Rekor):** No key management — uses OIDC identity (GitHub Actions, GitLab CI) and transparency log.

**Kubernetes admission enforcement:**
- Kyverno `ClusterPolicy` with `verifyImages`
- Connaisseur
- Sigstore policy-controller

---

## 10. Rootless Containers

Running the entire container stack — runtime, networking, storage — without any root privileges.

### 10.1 How It Works

1. **User namespace:** Maps UID 0 inside the container to an unprivileged UID on the host.
2. **Networking:** Uses `slirp4netns` or `pasta` (userspace networking) instead of creating real veth pairs (which requires root).
3. **Storage:** Uses `fuse-overlayfs` or native overlay with `userns` support (kernel 5.11+).
4. **cgroups:** cgroups v2 delegation allows non-root users to manage their own cgroup subtree.

```bash
# Rootless Podman (no daemon, no root)
podman run --rm alpine id
# uid=0(root) gid=0(root)  <-- inside the container
# On host: running as UID 1000 (your user)
```

### 10.2 Rootless Networking

**slirp4netns:** Userspace TCP/IP stack that connects to the container's network namespace via TAP device. Performance overhead: ~20–30% throughput reduction vs root-mode veth.

**pasta (passt):** Newer alternative. Uses `splice()` and `sendmsg()` for near-native performance. Default in Podman 5.0+.

**Port binding:** Rootless containers cannot bind to ports < 1024 on the host (no `CAP_NET_BIND_SERVICE` on host). Use ports >= 1024 or configure `sysctl net.ipv4.ip_unprivileged_port_start=0`.

### 10.3 Rootless Docker

```bash
# Install
dockerd-rootless-setuptool.sh install

# Requires: uidmap package (newuidmap, newgidmap), /etc/subuid, /etc/subgid configured
# Socket: $XDG_RUNTIME_DIR/docker.sock
# Data: ~/.local/share/docker/
```

### 10.4 Limitations

- No `--net=host` (already have host network access, just not privileged).
- Some volume mount permissions are tricky (host files owned by your UID, container expects different UID).
- cgroups v1 resource limits require root to set. cgroups v2 delegation fixes this.
- Performance: userspace networking is slower than veth.
- Ping requires `sysctl net.ipv4.ping_group_range` to include the user's GID.

---

## 11. Container Networking Deep Dive

### 11.1 Docker Network Drivers

| Driver | Scope | Use case |
|:-------|:------|:---------|
| `bridge` | Single host | Default. Containers on same host. |
| `host` | Single host | No network isolation, native performance. |
| `none` | Single host | No networking at all. |
| `overlay` | Multi-host (Swarm) | Container-to-container across hosts. |
| `macvlan` | Single host | Containers appear as physical devices on LAN. |
| `ipvlan` | Single host | Like macvlan, shared MAC. Cloud-friendly. |

### 11.2 DNS Resolution

Docker's embedded DNS server (127.0.0.11) resolves container names within user-defined networks:

```bash
# On user-defined bridge network "mynet"
docker run --name web --network mynet nginx
docker run --network mynet alpine ping web  # resolves "web" to container IP
```

Default bridge does NOT provide automatic DNS — only user-defined networks do. This is a common gotcha.

### 11.3 iptables/nftables Rules

Docker manipulates host iptables for:
- **DNAT:** Port mapping (`-p 8080:80`).
- **MASQUERADE:** Container-to-internet traffic gets source-NAT'd to the host IP.
- **DOCKER chain:** Custom chain for container traffic rules.
- **DOCKER-ISOLATION:** Prevents inter-bridge-network traffic.

```bash
# View Docker's iptables rules
iptables -t nat -L -n -v
# Chain DOCKER (2 references)
# target    prot opt source   destination
# DNAT      tcp  --  0.0.0.0/0 0.0.0.0/0  tcp dpt:8080 to:172.17.0.2:80
```

### 11.4 Container Network Interface (CNI)

CNI is a spec and library for configuring network interfaces in Linux containers. Used by Kubernetes, Podman, CRI-O.

**CNI plugin lifecycle:**
1. Container runtime creates network namespace.
2. Runtime calls CNI plugin with `ADD` operation, passing namespace path.
3. Plugin creates veth pair, assigns IP, sets up routes.
4. Runtime calls `DEL` on container teardown.

**CNI plugin categories:**
- **Interface creation:** bridge, ptp, macvlan, ipvlan, host-device
- **IPAM:** host-local, dhcp, static
- **Meta:** flannel, calico, cilium, bandwidth, firewall, portmap, tuning

---

## 12. Container Security Hardening Checklist

### 12.1 Build-Time

- [ ] Use minimal base images (distroless, alpine, scratch).
- [ ] Run as non-root user (`USER 1000:1000` in Dockerfile).
- [ ] Do not install unnecessary packages.
- [ ] Multi-stage builds — no build tools in runtime image.
- [ ] Scan images for CVEs in CI (Trivy, Grype).
- [ ] Sign images (Cosign).
- [ ] Pin base image digests, not just tags: `FROM node:22@sha256:abc123...`
- [ ] No secrets in image layers (use BuildKit secret mounts).
- [ ] Generate and publish SBOM.

### 12.2 Runtime

- [ ] Drop all capabilities, add back only what is needed.
- [ ] Run with a seccomp profile (at minimum, the Docker default).
- [ ] Set `readOnlyRootFilesystem: true` (use tmpfs for writable paths).
- [ ] Set memory and CPU limits (prevent noisy neighbor and OOM cascades).
- [ ] No `--privileged`.
- [ ] No `--pid=host`, `--net=host`, `--ipc=host` unless justified.
- [ ] Use read-only bind mounts where possible (`:ro`).
- [ ] Set `no-new-privileges` (`--security-opt=no-new-privileges:true`).
- [ ] Apply AppArmor or SELinux profiles.

### 12.3 Orchestrator (Kubernetes)

- [ ] PodSecurityStandards (PSS) enforced: `restricted` profile.
- [ ] Network policies restrict pod-to-pod traffic (default-deny + explicit allow).
- [ ] Service mesh mTLS (Istio/Linkerd).
- [ ] Secrets management (external-secrets-operator, Vault CSI, sealed-secrets).
- [ ] RBAC with least privilege.
- [ ] Admission controllers validate security posture (Kyverno, OPA/Gatekeeper).

---

## 13. Advanced Topics

### 13.1 Checkpoint/Restore (CRIU)

CRIU (Checkpoint/Restore in Userspace) can freeze a running container, save its state to disk, and restore it later (potentially on a different host).

**Process:**
1. Freeze all processes in the container (using the freezer cgroup).
2. Dump process state: memory pages, file descriptors, sockets, timers, signals.
3. Save to a directory as image files.
4. Restore: create namespaces, restore memory, reopen files/sockets, resume.

**Use cases:**
- Live migration of containers between hosts.
- Fast startup: checkpoint a warmed-up JVM, restore instead of cold-starting.
- Forensic snapshot of a running container for analysis.

```bash
# Checkpoint (Podman supports this natively)
podman container checkpoint my-container --export=/tmp/checkpoint.tar

# Restore
podman container restore --import=/tmp/checkpoint.tar
```

### 13.2 eBPF and Containers

eBPF programs run in the kernel and can observe/modify container behavior:

- **Networking:** Cilium uses eBPF to replace iptables for pod networking and network policies. Direct kernel-to-kernel packet routing, bypassing netfilter entirely.
- **Security:** Falco (eBPF mode) monitors syscalls for anomaly detection (unexpected process execution, file access, network connections).
- **Observability:** eBPF-based tools (Pixie, Hubble, Inspektor Gadget) provide deep visibility without modifying container images.

### 13.3 WASM Containers

WebAssembly as a container alternative:
- OCI-compatible: WASM modules packaged as OCI artifacts.
- Runtimes: WasmEdge, Wasmtime, Wasmer.
- containerd `runwasi` shim enables Kubernetes to schedule WASM workloads.
- **Advantages:** ~1ms startup, ~1 MB memory overhead, language-agnostic, sandboxed by design.
- **Limitations:** No filesystem, limited syscall support (WASI preview), no native threading (yet).

### 13.4 GPU Containers

NVIDIA Container Toolkit:
- `nvidia-container-runtime` — OCI runtime wrapper that injects GPU device files and driver libraries into the container.
- `nvidia-device-plugin` for Kubernetes — exposes `nvidia.com/gpu` as a schedulable resource.
- Container must match host driver CUDA version (or use CUDA forward compatibility).

```bash
docker run --gpus all nvidia/cuda:12.4-base nvidia-smi
```

### 13.5 Windows Containers

Two isolation modes:
1. **Process isolation:** Similar to Linux containers — namespace isolation, shared kernel. Windows Server only.
2. **Hyper-V isolation:** Each container runs in a lightweight VM. Works on Windows Server and Windows 10/11.

Windows containers cannot run Linux images (different kernel). Linux containers on Windows run in a utility VM (WSL2).

---

## 14. Container Orchestration Landscape

| Tool | Scope | Notes |
|:-----|:------|:------|
| **Docker Compose** | Single host, development | YAML declarative, `docker compose up`. |
| **Kubernetes** | Multi-node, production | Industry standard. See Module 5.2. |
| **Docker Swarm** | Multi-node, simple | Built into Docker. Limited adoption. Effectively deprecated. |
| **Nomad** | Multi-node, multi-workload | HashiCorp. Supports containers, VMs, batch, Java, raw exec. Simpler than K8s. |
| **ECS** | AWS-managed | AWS proprietary. Tight integration with AWS services. Fargate for serverless. |
| **Cloud Run** | GCP serverless | Scale-to-zero. Request-based billing. Uses gVisor isolation. |
| **Azure Container Apps** | Azure serverless | Built on Kubernetes (KEDA, Dapr, Envoy). |

---

## 15. Troubleshooting Reference

### 15.1 Common Issues

**Container OOMKilled:**
```bash
# Check OOM events
dmesg | grep -i oom
cat /sys/fs/cgroup/.../memory.events  # oom_kill counter
# Fix: increase memory limit or fix memory leak in application
```

**Container cannot resolve DNS:**
```bash
# Check /etc/resolv.conf inside container
docker exec my-container cat /etc/resolv.conf
# Ensure nameserver is reachable from container network
docker exec my-container nslookup google.com
```

**Permission denied on volume mount:**
```bash
# Check UID mismatch
ls -la /host/path/
docker exec my-container id
# Fix: match UIDs or use --userns-remap
```

**Container startup slow:**
```bash
# Check image size
docker images my-app
# Check for copy-up overhead (large files in lower layers being modified)
# Use volumes for data directories
```

### 15.2 Debugging Tools

```bash
# Enter a running container's namespaces
nsenter --target $(docker inspect --format '{{.State.Pid}}' my-container) \
  --mount --uts --ipc --net --pid -- /bin/sh

# Inspect cgroup limits and usage
cat /sys/fs/cgroup/system.slice/docker-$(docker inspect --format '{{.Id}}' my-container).scope/memory.current
cat /sys/fs/cgroup/system.slice/docker-$(docker inspect --format '{{.Id}}' my-container).scope/cpu.stat

# Trace syscalls
strace -f -p $(docker inspect --format '{{.State.Pid}}' my-container)

# Inspect network namespace
ip netns exec $(docker inspect --format '{{.NetworkSettings.SandboxKey}}' my-container | xargs basename) ip addr

# Debug image layers
docker history my-app:latest
dive my-app:latest  # interactive layer explorer
```

---

## 16. Key Takeaways

1. **Containers are processes, not VMs.** They share the host kernel. The isolation boundary is enforced by namespaces (visibility), cgroups (resources), capabilities (privileges), and seccomp (syscalls).

2. **cgroups v2 is the present.** Unified hierarchy, PSI, delegation for rootless — there is no reason to use v1 on new deployments.

3. **User namespaces unlock rootless.** Root inside the container maps to nobody outside. Even container escapes land as unprivileged.

4. **OverlayFS + CoW makes containers fast to start** but slow for write-heavy workloads in the container layer. Use volumes for data.

5. **OCI standards** ensure interoperability: any OCI image runs on any OCI runtime. runc is the reference; crun is faster; gVisor and Kata provide stronger isolation.

6. **Multi-stage builds + distroless bases + BuildKit cache mounts** are non-negotiable for production images.

7. **Security is layered:** drop capabilities, apply seccomp profiles, run as non-root, scan images, sign images, enforce admission policies. No single control is sufficient.

8. **The shared kernel is the fundamental risk.** For untrusted workloads, consider gVisor (userspace kernel) or Kata (micro-VM) to reduce the attack surface.

---

## 17. AppArmor and SELinux for Containers

### 17.1 AppArmor

AppArmor is a Mandatory Access Control (MAC) system that confines programs based on file path access profiles.

**How it applies to containers:**
- Docker ships a default AppArmor profile (`docker-default`) that restricts:
  - Writing to `/proc` and `/sys` (except allowed paths).
  - Mount operations.
  - Ptrace of other processes.
  - Raw network access.
  - Access to sensitive files like `/etc/shadow`.

```bash
# Check if AppArmor is enabled
aa-status

# Run container with custom profile
docker run --security-opt apparmor=my-custom-profile my-app

# Run without AppArmor (dangerous, not recommended)
docker run --security-opt apparmor=unconfined my-app

# Generate a profile from a container's runtime behavior
aa-genprof /path/to/binary
```

**Custom profile example:**
```
#include <tunables/global>

profile docker-my-app flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Allow read access to app directory
  /app/** r,

  # Allow execution of the app binary
  /app/server ix,

  # Allow network access
  network inet stream,
  network inet dgram,
  network inet6 stream,
  network inet6 dgram,

  # Allow reading SSL certificates
  /etc/ssl/certs/** r,

  # Deny everything else by default (AppArmor deny is implicit)
  deny /proc/*/mem rwklx,
  deny /sys/** w,
}
```

### 17.2 SELinux

SELinux (Security-Enhanced Linux) labels all processes and files with security contexts and enforces access policies based on these labels.

**SELinux context format:** `user:role:type:level`

For containers:
- Default process type: `container_t` (unprivileged containers), `spc_t` (super-privileged containers).
- Default file type: `container_file_t` for container-managed files.

**Key enforcement:**
- `container_t` cannot access host files labeled `etc_t`, `var_t`, etc.
- `container_t` cannot access other containers' files (labeled with different MCS categories).
- `container_t` cannot load kernel modules, access raw devices, or modify host network.

**Multi-Category Security (MCS):**
Each container gets a unique MCS label (e.g., `s0:c123,c456`). Even if two containers have the same SELinux type (`container_t`), they cannot access each other's files because the MCS categories differ.

```bash
# Check SELinux mode
getenforce  # Enforcing, Permissive, Disabled

# View container process context
ps -eZ | grep container

# Run with custom SELinux label
docker run --security-opt label=type:my_container_t my-app

# Disable SELinux for a container (not recommended)
docker run --security-opt label=disable my-app
```

**Choosing between AppArmor and SELinux:** They are mutually exclusive at the kernel level. Ubuntu/Debian default to AppArmor. RHEL/Fedora/CentOS default to SELinux. Use whichever your distro ships.

---

## 18. Container Storage: Volumes, Bind Mounts, tmpfs

### 18.1 Storage Types

| Type | Source | Managed by | Persistence |
|:-----|:-------|:-----------|:------------|
| **Container layer** | OverlayFS upper dir | Container runtime | Destroyed with container |
| **Volume** | `/var/lib/docker/volumes/<name>` | Docker / runtime | Survives container lifecycle |
| **Bind mount** | Any host path | User | Host filesystem lifetime |
| **tmpfs mount** | RAM | Kernel | Container lifetime (never hits disk) |

### 18.2 Volume Drivers

Docker supports pluggable volume drivers for remote storage:

| Driver | Backend |
|:-------|:--------|
| `local` (default) | Host filesystem |
| `nfs` | NFS shares |
| `cifs` | SMB/CIFS shares |
| `rexray/ebs` | AWS EBS |
| `portworx` | Distributed storage |
| `longhorn` | Rancher's distributed block storage for K8s |
| `ceph/rbd` | Ceph block devices |

### 18.3 Performance Considerations

```
Read/Write speed (fastest to slowest):
1. tmpfs (RAM)                    ~6 GB/s
2. Bind mount to local SSD        ~3 GB/s (native disk speed)
3. Named volume (local driver)    ~3 GB/s (same as bind mount)
4. Container layer (overlay2)     ~2.5 GB/s (CoW overhead on write)
5. NFS volume                     ~100 MB/s (network bound)
```

**Rule:** Databases, log files, upload directories, and any write-heavy workload MUST use volumes or bind mounts, never the container layer.

### 18.4 Volume Backup and Migration

```bash
# Backup a named volume to a tar file
docker run --rm -v mydata:/data -v $(pwd):/backup alpine \
  tar czf /backup/mydata-backup.tar.gz -C /data .

# Restore
docker run --rm -v mydata:/data -v $(pwd):/backup alpine \
  tar xzf /backup/mydata-backup.tar.gz -C /data
```

---

## 19. Process Signal Handling in Containers

### 19.1 Signal Forwarding

When `docker stop` is issued:
1. Docker sends SIGTERM to PID 1 in the container.
2. Waits for the grace period (default 10s).
3. If still running, sends SIGKILL.

**Problem:** If PID 1 is a shell (`/bin/sh -c "my-app"`), the shell does NOT forward SIGTERM to child processes. The app never gets the signal and is hard-killed after the grace period.

**Solutions:**
```dockerfile
# WRONG: runs through shell, signal not forwarded
CMD my-app --start

# RIGHT: exec form, app is PID 1
CMD ["my-app", "--start"]

# RIGHT: use exec in shell form
CMD exec my-app --start

# RIGHT: use tini as init
ENTRYPOINT ["tini", "--"]
CMD ["my-app", "--start"]
```

### 19.2 Graceful Shutdown Pattern

```
SIGTERM received →
  1. Stop accepting new connections
  2. Drain existing connections (finish in-flight requests)
  3. Flush buffers (logs, queues)
  4. Close database connections
  5. Exit 0

Timeout (SIGKILL) →
  Hard kill. Data loss possible.
```

**Kubernetes preStop hook:** Adds a delay before SIGTERM to allow endpoint removal from Services:
```yaml
lifecycle:
  preStop:
    exec:
      command: ["sleep", "5"]
```

This gives kube-proxy and ingress controllers time to remove the pod from load balancing before the app starts shutting down.

---

## 20. Resource Limits: Practical Reference

### 20.1 Docker

```bash
# CPU: 2 cores max, 50% relative weight
docker run --cpus=2 --cpu-shares=512 my-app

# Memory: 512MB hard limit, 256MB reservation
docker run --memory=512m --memory-reservation=256m my-app

# PIDs: max 100 processes
docker run --pids-limit=100 my-app

# I/O: limit write speed to 10MB/s on device
docker run --device-write-bps /dev/sda:10mb my-app

# ulimits
docker run --ulimit nofile=65536:65536 --ulimit nproc=4096:4096 my-app
```

### 20.2 Kubernetes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
  - name: app
    image: my-app:v1
    resources:
      requests:
        cpu: "250m"        # 0.25 cores — scheduling guarantee
        memory: "128Mi"    # 128 MiB — scheduling guarantee
      limits:
        cpu: "1000m"       # 1 core — hard cap (throttled beyond)
        memory: "512Mi"    # 512 MiB — hard cap (OOMKilled beyond)
```

**QoS classes derived from requests/limits:**
| Class | Condition | Eviction priority |
|:------|:----------|:-----------------|
| **Guaranteed** | requests == limits for all containers | Last to be evicted |
| **Burstable** | At least one container has requests < limits | Middle |
| **BestEffort** | No requests or limits set | First to be evicted |

---

## 21. Container Logging Patterns

### 21.1 stdout/stderr (12-Factor)

The 12-Factor App methodology prescribes logging to stdout/stderr. The container runtime captures these streams.

```
Application → stdout/stderr → Container Runtime Log Driver → Aggregation
```

Docker log drivers: `json-file` (default), `journald`, `syslog`, `fluentd`, `awslogs`, `gcplogs`, `splunk`.

### 21.2 Sidecar Pattern (Kubernetes)

For applications that write logs to files:
```yaml
spec:
  containers:
  - name: app
    volumeMounts:
    - name: logs
      mountPath: /var/log/app
  - name: log-shipper
    image: fluentbit:latest
    volumeMounts:
    - name: logs
      mountPath: /var/log/app
      readOnly: true
  volumes:
  - name: logs
    emptyDir: {}
```

### 21.3 Log Rotation

Docker's `json-file` driver defaults to unlimited log size. Production must configure rotation:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "50m",
    "max-file": "5"
  }
}
```

Without this, a verbose container will fill the host disk and crash every container on the node.

---

## 22. Multi-Architecture Images

### 22.1 Building for Multiple Platforms

```bash
# Create a buildx builder
docker buildx create --name multiarch --use

# Build for amd64 and arm64, push to registry
docker buildx build --platform linux/amd64,linux/arm64 \
  -t my-registry.io/my-app:v1 --push .
```

BuildKit uses QEMU user-mode emulation for cross-architecture builds. Native builds on matching hardware are significantly faster.

### 22.2 Manifest Lists

The registry stores a manifest list (OCI image index) that maps platforms to image manifests:

```json
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.index.v1+json",
  "manifests": [
    {
      "mediaType": "application/vnd.oci.image.manifest.v1+json",
      "digest": "sha256:abc...",
      "platform": { "architecture": "amd64", "os": "linux" }
    },
    {
      "mediaType": "application/vnd.oci.image.manifest.v1+json",
      "digest": "sha256:def...",
      "platform": { "architecture": "arm64", "os": "linux" }
    }
  ]
}
```

When `docker pull my-app:v1` runs, the client sends its platform; the registry returns the matching manifest.

---

## 23. Container Internals Glossary

| Term | Definition |
|:-----|:-----------|
| **cgroup** | Control group. Kernel mechanism for resource accounting and limiting. |
| **CoW** | Copy-on-Write. Defer copying until modification. |
| **CRI** | Container Runtime Interface. Kubernetes API for container runtimes. |
| **CNI** | Container Network Interface. Plugin spec for container networking. |
| **CSI** | Container Storage Interface. Plugin spec for container storage. |
| **Namespace** | Kernel isolation boundary for a global resource. |
| **OCI** | Open Container Initiative. Standards body for container specs. |
| **Overlay** | Union filesystem merging read-only layers with a read-write upper layer. |
| **PSI** | Pressure Stall Information. cgroups v2 metric for resource contention. |
| **runc** | Reference OCI runtime. Creates containers from OCI bundles. |
| **Seccomp** | Secure Computing. BPF-based syscall filtering. |
| **veth** | Virtual Ethernet pair. Connects network namespaces. |
| **Whiteout** | Marker file in overlay upper layer that hides a lower-layer file. |
| **WASI** | WebAssembly System Interface. Syscall-like API for WASM sandboxes. |

---

## 24. Exercises

### Exercise 1: Namespace Exploration
```bash
# 1. Create a new PID + mount namespace
unshare --pid --fork --mount-proc bash
# 2. Verify: ps aux should show only your shell
# 3. Verify: hostname change inside does NOT affect host (needs --uts)
# 4. Exit and verify host state is unchanged
```

### Exercise 2: cgroup Resource Limiting (Manual)
```bash
# 1. Create a cgroup
mkdir /sys/fs/cgroup/my-test
# 2. Set memory limit to 50MB
echo 52428800 > /sys/fs/cgroup/my-test/memory.max
# 3. Set PID limit
echo 10 > /sys/fs/cgroup/my-test/pids.max
# 4. Add current shell to the cgroup
echo $$ > /sys/fs/cgroup/my-test/cgroup.procs
# 5. Try to allocate >50MB (should be killed)
# 6. Try a fork bomb (should hit pid limit)
```

### Exercise 3: Build a Container From Scratch
```bash
# Without Docker — using runc directly
mkdir -p mybundle/rootfs
# Extract a minimal rootfs (Alpine)
docker export $(docker create alpine:latest) | tar -C mybundle/rootfs -xf -
# Generate OCI config
cd mybundle && runc spec
# Edit config.json: change process.args to ["/bin/sh"]
# Create and start
runc run mycontainer
```

### Exercise 4: Seccomp Profile Audit
```bash
# 1. Run a container and record all syscalls
strace -f -c -o /tmp/syscalls.log docker run --rm my-app echo hello
# 2. Identify the minimal set of syscalls needed
# 3. Write a custom seccomp profile allowing only those
# 4. Test the container with the custom profile
# 5. Verify blocked operations fail gracefully
```

### Exercise 5: Image Layer Analysis
```bash
# 1. Build an intentionally bad Dockerfile (large layers, poor ordering)
# 2. Use `docker history` to inspect layer sizes
# 3. Use `dive` to analyze wasted space
# 4. Refactor with multi-stage, proper ordering, cache mounts
# 5. Compare final image sizes
```

---

## 25. Further Reading

- **"Container Security" by Liz Rice** (O'Reilly, 2020) — The definitive book on the Linux primitives behind containers.
- **OCI Runtime Spec:** https://github.com/opencontainers/runtime-spec
- **OCI Image Spec:** https://github.com/opencontainers/image-spec
- **cgroups v2 documentation:** kernel.org/doc/html/latest/admin-guide/cgroup-v2.html
- **man 7 namespaces** — Linux manual page covering all namespace types.
- **man 2 seccomp** — Seccomp BPF syscall reference.
- **Brendan Gregg's Linux Performance Tools:** brendangregg.com — Essential for container performance debugging.
- **Podman documentation:** docs.podman.io — Best reference for rootless container workflows.
- **BuildKit documentation:** github.com/moby/buildkit — Cache mounts, secret mounts, SSH forwarding.
- **Sigstore/Cosign:** sigstore.dev — Keyless signing and verification for container images.

---

## 26. Dockerfile Best Practices — Complete Reference

### 26.1 Instruction Ordering for Cache Efficiency

The single most impactful optimization. Order instructions from least-frequently changing to most-frequently changing:

```dockerfile
# Layer 1: Base image (changes rarely)
FROM node:22-slim AS base

# Layer 2: System dependencies (changes rarely)
RUN apt-get update && apt-get install -y --no-install-recommends \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

# Layer 3: App dependencies (changes when package.json changes)
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production

# Layer 4: Application code (changes frequently)
COPY . .

# Layer 5: Runtime config (changes rarely)
USER 1000:1000
EXPOSE 3000
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]
```

### 26.2 Reducing Layer Count and Size

```dockerfile
# BAD: 3 layers, leftover apt cache
RUN apt-get update
RUN apt-get install -y curl git
RUN apt-get clean

# GOOD: 1 layer, cache cleaned in same layer
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git \
    && rm -rf /var/lib/apt/lists/*
```

**Why same layer matters:** Each `RUN` creates a layer snapshot. Deleting files in a subsequent `RUN` creates a whiteout, but the data still exists in the previous layer. The image size does not decrease.

### 26.3 .dockerignore

```
.git
node_modules
dist
*.log
.env
.env.*
Dockerfile
docker-compose*.yml
.github
.vscode
coverage
__pycache__
*.pyc
```

Without `.dockerignore`, `COPY . .` sends the entire build context to the daemon, including `.git` (potentially hundreds of MB), `node_modules`, and secrets.

### 26.4 HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

Docker uses health check results for container lifecycle management. Kubernetes ignores `HEALTHCHECK` — use liveness/readiness probes instead.

### 26.5 ARG vs ENV

| Directive | Available at | Persists in image | Use for |
|:----------|:-------------|:-----------------|:--------|
| `ARG` | Build time only | No | Build-time config (version, registry URL) |
| `ENV` | Build + run time | Yes (in every layer after) | Runtime config (app settings, paths) |

```dockerfile
ARG NODE_VERSION=22
FROM node:${NODE_VERSION}-slim

ARG APP_VERSION
ENV APP_VERSION=${APP_VERSION}
# ARG is gone after build; ENV persists into runtime
```

### 26.6 COPY vs ADD

| Feature | `COPY` | `ADD` |
|:--------|:-------|:------|
| Copy files | Yes | Yes |
| Auto-extract tar.gz | No | Yes |
| Fetch remote URLs | No | Yes (but prefer `curl` + `RUN`) |
| Predictability | High | Low (implicit behavior) |

**Rule:** Always use `COPY`. Use `ADD` only for local tar extraction. Never use `ADD` for remote URLs — use `curl` or `wget` in a `RUN` so you can verify checksums and clean up.

### 26.7 ENTRYPOINT vs CMD

```dockerfile
# ENTRYPOINT = the executable
# CMD = default arguments
ENTRYPOINT ["python", "manage.py"]
CMD ["runserver", "0.0.0.0:8000"]

# docker run my-app                    → python manage.py runserver 0.0.0.0:8000
# docker run my-app migrate            → python manage.py migrate
# docker run my-app shell              → python manage.py shell
```

**Shell form vs exec form:**
```dockerfile
# Shell form: /bin/sh -c "my-app" — cannot receive signals properly
CMD my-app --start

# Exec form: direct exec — PID 1, receives signals
CMD ["my-app", "--start"]
```

Always use exec form for `ENTRYPOINT`. Shell form for `CMD` is acceptable only when you need shell expansion.

---

## 27. Container Internals in Production: War Stories and Patterns

### 27.1 The PID 1 Zombie Problem

**Scenario:** A Node.js container runs a child process for video encoding. The child crashes. The parent does not call `waitpid()`. The child becomes a zombie (state `Z` in `ps`). Over days, thousands of zombies accumulate. Eventually, the container hits `pids.max` and cannot fork new processes.

**Root cause:** Node.js does not act as an init system. It does not reap adopted orphans.

**Fix:** Use `tini` or `dumb-init` as PID 1. These lightweight init systems reap zombies and forward signals.

### 27.2 The OOM That Wasn't

**Scenario:** A Java container with `-Xmx=4g` and `memory.max=4g` gets OOMKilled shortly after startup, despite heap usage being only 2 GB.

**Root cause:** JVM memory includes heap + metaspace + thread stacks + native memory + code cache + GC overhead. Total JVM RSS can be 1.5–2x the heap max. The cgroup limit must account for all of it.

**Fix:** Set `memory.max` to at least `Xmx * 1.5 + 512m` for typical workloads. Or use `-XX:MaxRAMPercentage=75.0` to let the JVM auto-size heap to 75% of the cgroup limit.

### 27.3 The DNS Resolution Storm

**Scenario:** Alpine-based containers in Kubernetes experience intermittent DNS failures. Some lookups take 5+ seconds. Others fail entirely.

**Root cause:** musl libc's DNS resolver sends A and AAAA queries in parallel on the same UDP socket. Linux conntrack's race condition causes one query to be dropped. Combined with `ndots:5` default in Kubernetes (causing every short hostname to generate 5+ search domain suffixes), this amplifies the problem.

**Fix:** Options:
1. Use glibc-based images (Debian, Ubuntu).
2. Set `dnsConfig.options: [{name: ndots, value: "1"}, {name: single-request-reopen}]` in the pod spec.
3. Use `dnsPolicy: Default` (use node's DNS, not cluster DNS).
4. Deploy NodeLocal DNSCache (DaemonSet caching DNS on every node).

### 27.4 The Copy-Up Surprise

**Scenario:** A container modifies a 5 GB database file stored in the image layers. Performance drops 80% during the first modification.

**Root cause:** OverlayFS copy-up. The entire 5 GB file is copied from the lower layer to the upper layer before the first write byte can land.

**Fix:** Database files must always be on volumes, never in the image layer. This is not optional.

### 27.5 The Seccomp False Positive

**Scenario:** A Python container crashes with `EPERM` on `clone3()` syscall after upgrading the base image to a newer glibc.

**Root cause:** Newer glibc uses `clone3()` instead of `clone()`. The container's custom seccomp profile allowed `clone` but not `clone3`.

**Fix:** Update the seccomp profile. When upgrading base images, re-audit the syscall profile. Better yet, use the default Docker profile (which tracks kernel evolution) and only customize when necessary.

---

## 28. Registry Architecture and Image Distribution

### 28.1 Registry Internals

A container registry is a content-addressable blob store with a manifest index:

```
Registry
├── /v2/
│   ├── library/nginx/
│   │   ├── manifests/
│   │   │   ├── latest          → sha256:abc... (manifest list)
│   │   │   ├── sha256:abc...   → manifest list JSON
│   │   │   ├── sha256:def...   → amd64 manifest JSON
│   │   │   └── sha256:ghi...   → arm64 manifest JSON
│   │   └── blobs/
│   │       ├── sha256:111...   → config JSON
│   │       ├── sha256:222...   → layer 1 (tar.gz)
│   │       ├── sha256:333...   → layer 2 (tar.gz)
│   │       └── sha256:444...   → layer 3 (tar.gz)
```

### 28.2 Image Pull Sequence

```
1. Client → GET /v2/library/nginx/manifests/latest
   ← Registry returns manifest list (or manifest)
   
2. Client selects platform-appropriate manifest from list
   → GET /v2/library/nginx/manifests/sha256:def...
   ← Registry returns manifest JSON with layer digests

3. For each layer not already in local cache:
   → GET /v2/library/nginx/blobs/sha256:222...
   ← Registry returns tar.gz layer blob
   (Layers can be pulled in parallel)

4. Client verifies digest of each downloaded blob
5. Client extracts layers into storage driver
```

### 28.3 Registry Mirroring and Caching

**Pull-through cache:** A local registry that proxies requests to upstream:
```yaml
# Docker daemon config (/etc/docker/daemon.json)
{
  "registry-mirrors": ["https://mirror.internal.example.com"]
}
```

**Harbor:** Enterprise registry with:
- Vulnerability scanning (Trivy integration)
- Image signing (Cosign/Notary)
- Replication between registries
- RBAC and audit logging
- Quota management

**Zot:** Lightweight OCI-native registry. Supports OCI artifacts (Helm charts, WASM modules, Sigstore signatures).

### 28.4 Image Garbage Collection

Registries accumulate untagged manifests and unreferenced blobs. Garbage collection reclaims disk:

```bash
# Docker registry GC
docker exec registry bin/registry garbage-collect /etc/docker/registry/config.yml

# Harbor: scheduled GC in admin settings
# ECR: lifecycle policies (expire untagged images after N days)
```

---

## 29. Container Metrics and Performance Monitoring

### 29.1 Key Metrics to Monitor

| Metric | Source | Alert threshold |
|:-------|:------|:---------------|
| CPU usage vs limit | cgroup `cpu.stat` | >80% of limit sustained |
| CPU throttling | `nr_throttled` in `cpu.stat` | Any throttling = investigate |
| Memory usage vs limit | `memory.current` vs `memory.max` | >85% of limit |
| OOM kill count | `memory.events` `oom_kill` | Any increment = alert |
| Memory PSI | `memory.pressure` | `some avg10 > 20` |
| I/O wait | `io.stat` | High `wait_total` |
| Network rx/tx bytes | `/sys/class/net/eth0/statistics/` | Anomalous patterns |
| PID count | `pids.current` vs `pids.max` | >80% of limit |
| Container restart count | Runtime / orchestrator | Any restart = investigate |
| Image pull latency | Runtime metrics | >30s = check registry/network |

### 29.2 cAdvisor

Google's container advisor. Collects and exposes per-container resource usage metrics. Bundled into kubelet in Kubernetes. Exposes Prometheus metrics at `:8080/metrics`.

Key cAdvisor metrics:
```
container_cpu_usage_seconds_total
container_memory_usage_bytes
container_memory_working_set_bytes  # better than usage (excludes inactive cache)
container_network_receive_bytes_total
container_network_transmit_bytes_total
container_fs_reads_total
container_fs_writes_total
```

### 29.3 Performance Debugging Workflow

```
1. Alert fires (e.g., latency spike)
2. Check container CPU throttling (nr_throttled)
   → If throttled: increase CPU limit or optimize code
3. Check memory PSI (memory.pressure)
   → If pressured: increase memory or fix leak
4. Check I/O stats (io.stat)
   → If I/O-bound: move to SSD, use tmpfs for temp files, optimize queries
5. Check network (rx/tx rates, connection counts)
   → If network-bound: check DNS, connection pooling, payload sizes
6. Profile the application (pprof, async-profiler, py-spy)
   → Identify hotspots in code
```

---

## 30. Container Ecosystem: Docker vs Podman vs containerd vs CRI-O

### 30.1 Comparison Matrix

| Feature | Docker | Podman | containerd | CRI-O |
|:--------|:-------|:-------|:-----------|:------|
| **Daemon** | Yes (dockerd) | Daemonless | Yes (containerd) | Yes (crio) |
| **Rootless** | Partial | Full | Partial | Limited |
| **OCI Runtime** | runc | crun (default) | runc | runc/crun |
| **K8s CRI** | Via containerd | Via CRI-O | Native | Native |
| **Compose** | Docker Compose | podman-compose / Quadlet | nerdctl compose | No |
| **Build** | BuildKit | Buildah | nerdctl build (BuildKit) | No (use Buildah) |
| **Swarm** | Yes | No | No | No |
| **Systemd integration** | Service file | Quadlet (generate systemd units) | Service file | Service file |

### 30.2 Kubernetes CRI Pipeline

```
kubelet → CRI gRPC → containerd/CRI-O → OCI runtime (runc/crun) → container
```

Docker was removed as a direct Kubernetes runtime in v1.24 (dockershim removal). Docker images still work — they are OCI-compatible. Only the runtime interface changed.

### 30.3 Podman Quadlet

Podman integrates with systemd for production container management without a daemon:

```ini
# /etc/containers/systemd/my-app.container
[Container]
Image=my-registry.io/my-app:v1
PublishPort=8080:80
Volume=my-data:/data:Z
Environment=NODE_ENV=production

[Service]
Restart=always

[Install]
WantedBy=default.target
```

```bash
systemctl daemon-reload
systemctl start my-app
systemctl status my-app
journalctl -u my-app
```

This eliminates the single-point-of-failure daemon. Each container is an independent systemd service.
