# Domain 31 — Detection Engineering and SOC Architecture at Scale

## Chapter 31B — Runtime Security: eBPF-Based Monitoring, Auditd at Scale, and Zero Trust Architecture

> **Scope:** eBPF architecture for security monitoring — program types (kprobes, tracepoints, LSM hooks), BPF verifier constraints, BPF maps, CO-RE · Security observability tools built on eBPF — Tetragon, Falco, Tracee, Cilium · Auditd and auditbeat — audit rule design, performance tuning, deployment at scale · Zero trust network architecture — identity-centric access control, microsegmentation, software-defined perimeters, NIST SP 800-207 · Container runtime hardening — seccomp, AppArmor, SELinux, admission controllers · Service mesh security — Istio mTLS, SPIFFE/SPIRE · Windows runtime protection — WDAC, ASR, AppLocker · Kernel LSM comparison — SELinux, AppArmor, Landlock · Supply chain runtime verification — Sigstore, Kyverno, OPA Gatekeeper · Secure boot and measured boot — UEFI Secure Boot chain, TPM-based attestation · Hardware-backed attestation — TPM 2.0, remote attestation, confidential computing (AMD SEV, Intel TDX, ARM CCA) · Integration of runtime security with SIEM/SOAR pipelines

---

## 1. eBPF Architecture for Security Monitoring

Extended Berkeley Packet Filter (eBPF) has fundamentally changed Linux security monitoring by enabling the insertion of sandboxed programs directly into the kernel's execution path without modifying kernel source code or loading kernel modules. eBPF programs execute at native speed within the kernel, providing visibility into system calls, network packets, file operations, process lifecycle events, and kernel function calls with minimal performance overhead (typically under 5% even under heavy instrumentation).

### 1.1 eBPF Program Types for Security

eBPF supports multiple program types, each attached to a different kernel hook point:

**Kprobes and kretprobes:** Kprobes attach eBPF programs to the entry point of any kernel function. Kretprobes attach to the return point. For security monitoring, kprobes on system call entry functions (e.g., `__x64_sys_execve`, `__x64_sys_openat`, `__x64_sys_connect`) provide complete visibility into process execution, file access, and network connections. Kretprobes capture return values, enabling the security tool to determine whether the operation succeeded or was denied. The practical limitation of kprobes is fragility: they are tied to specific kernel function names and internal APIs which may change between kernel versions. A kprobe attached to `do_filp_open` in kernel 5.10 may fail on kernel 6.1 if the function was renamed, refactored, or inlined by the compiler. CO-RE (§1.3) addresses this.

**Tracepoints:** Tracepoints are stable, documented instrumentation points defined by the kernel's tracing infrastructure. Unlike kprobes, tracepoints are explicitly maintained as part of the kernel's ABI, providing stability across versions. Security-relevant tracepoints include: `sched:sched_process_exec` (process execution), `syscalls:sys_enter_*` and `syscalls:sys_exit_*` (system call entry and exit for every syscall), `net:net_dev_xmit` (network packet transmission), `task:task_newtask` (new process/thread creation), and `module:module_load` (kernel module loading—critical for detecting rootkit installation).

**LSM (Linux Security Module) hooks:** eBPF LSM programs attach to Linux Security Module hook points—the same hooks used by AppArmor, SELinux, and Landlock. This is the most powerful program type for security because LSM hooks are invoked at security decision points: before a file is opened, before a process executes, before a network connection is established, before a kernel module is loaded. Unlike kprobes and tracepoints (which observe but cannot modify behavior), LSM eBPF programs can enforce security policy by returning deny decisions, enabling real-time prevention. Available since Linux kernel 5.7, eBPF LSM programs enable application whitelisting, binary authorization, and runtime policy enforcement at the kernel level without traditional LSM profile deployment.

**XDP (eXpress Data Path):** XDP programs execute at the earliest possible point in the network receive path—before the kernel's network stack processes the packet. XDP can inspect, modify, redirect, or drop packets at near-line-rate speeds. For security, XDP enables high-performance DDoS mitigation, IP blocklist enforcement, and network-level IOC matching. XDP operates at layer 2–4, processing raw Ethernet frames, effective for volumetric attack mitigation but less suitable for application-layer inspection.

### 1.2 BPF Verifier, Maps, and Ring Buffers

**The BPF verifier** validates every eBPF program before execution. It statically analyzes bytecode to ensure: the program terminates (bounded loops introduced in kernel 5.3), all memory accesses are within bounds, the program does not access arbitrary kernel memory, and the program adheres to its type's constraints. The verifier's complexity limits (1 million verified instructions as of kernel 5.15, up from 4,096 in early versions) force security tool developers to split complex logic between eBPF programs (initial filtering in kernel space) and user-space daemons (complex analysis on forwarded events). The verifier also validates all helper function calls, ensuring eBPF programs only invoke approved kernel functions appropriate to their program type.

**BPF maps** are shared data structures accessible by both eBPF programs and user-space applications. Security-relevant map types include: hash maps (IOC lookup tables with O(1) lookup among millions of entries, entirely in kernel space), ring buffers (BPF_MAP_TYPE_RINGBUF for streaming events from kernel to user space), per-CPU arrays (high-frequency counters without lock contention), and LRU hash maps (connection tracking state with automatic eviction).

### 1.3 CO-RE (Compile Once, Run Everywhere)

CO-RE solves eBPF's portability problem using BPF Type Format (BTF) metadata embedded in the kernel to perform field offset relocation at program load time. The eBPF program references fields by name (e.g., `task->pid`), and the BPF loader adjusts bytecode offsets to match the running kernel's actual structure layout. CO-RE requires: a kernel compiled with `CONFIG_DEBUG_INFO_BTF=y` (standard on most distribution kernels since ~2020), libbpf, and Clang with BTF-aware compilation.

For environments running older kernels without native BTF (RHEL 7, older Ubuntu LTS), `pahole` can generate BTF from DWARF debug information in the kernel's debug symbols package, or the eBPF program can fall back to pre-computed offset tables for known kernel versions.

### 1.4 LSM Hook Examples for Security Enforcement

**Binary authorization:** An eBPF LSM program attached to the `bprm_check_security` hook can compute the SHA-256 hash of every binary before execution and compare it against a hash allowlist stored in a BPF hash map. Binaries not in the allowlist are denied execution by returning `-EPERM`. This implements application whitelisting at the kernel level, preventing execution of unauthorized tools even if they are written to disk.

**Kernel module loading control:** An eBPF LSM program on the `kernel_module_request` and `kernel_read_file` (for module files) hooks can restrict kernel module loading to modules signed with specific keys or to a predefined allowlist of module names. This prevents BYOVD attacks and rootkit installation via kernel modules.

**File access control:** LSM hooks on `inode_permission` and `file_open` can enforce fine-grained file access policies beyond what traditional Unix permissions provide — preventing container workloads from accessing host filesystem paths through bind mounts, enforced even if the process has root privileges within its namespace.

### 1.5 Attacking eBPF: Offensive Abuse and Subversion

**eBPF-based rootkits:** An attacker with root and `CAP_BPF` (or `CAP_SYS_ADMIN` on older kernels) can load malicious eBPF programs that intercept and modify system behavior at the kernel level. A kprobe on `sys_getdents64` can filter filenames from directory listings, hiding files from `ls`. A tracepoint on `sched_process_exec` can suppress execution events from monitoring tools. The `ebpfkit` project demonstrated network-level C2 using XDP programs to intercept and respond to covert packets before they reach the TCP/IP stack, making the C2 channel invisible to application-layer monitoring.

**Advanced eBPF rootkit techniques** extend beyond simple file hiding. An eBPF kprobe on `tcp_v4_connect` can redirect network connections — when a monitoring tool attempts to connect to a threat intelligence service or SIEM, the eBPF program silently redirects the connection to a local socket that returns benign data. An eBPF program on the `sys_read` return path can modify the content read from `/proc` files (such as `/proc/net/tcp` for active network connections or `/proc/<pid>/maps` for process memory maps), hiding malicious processes and network connections.

**Detection of eBPF rootkits:**
```bash
# Enumerate all loaded BPF programs
bpftool prog list

# Show attachment points
bpftool prog show id <ID> --json | jq '.type, .tag, .name'

# Dump bytecode for analysis
bpftool prog dump xlated id <ID>

# List pinned programs
find /sys/fs/bpf/ -type f

# Monitor bpf() syscall loading
auditctl -a always,exit -F arch=b64 -S bpf -k bpf_load
```

Falco rule for eBPF rootkit detection:
```yaml
- rule: Suspicious BPF Program Load
  desc: Non-security-tool process loading eBPF programs
  condition: >
    evt.type = bpf and evt.arg.cmd = BPF_PROG_LOAD
    and not proc.name in (tetragon, falco, cilium-agent, tracee, node_exporter)
    and not proc.pname in (systemd, kubelet)
  output: >
    BPF program loaded by unexpected process
    (proc=%proc.name pid=%proc.pid user=%user.name cmd=%proc.cmdline)
  priority: CRITICAL
```

**Kernel vulnerability exploitation via eBPF:** BPF verifier bugs have been a recurring source of privilege escalation vulnerabilities. CVE-2021-3490 (ALU32 bounds tracking), CVE-2021-31440 (bounds propagation error), CVE-2022-23222 (pointer leak), and CVE-2023-2163 (verifier state pruning) are examples where crafted eBPF programs tricked the verifier into accepting code that performed out-of-bounds memory access, enabling arbitrary kernel read/write.

**Hardening:**
```bash
# Disable unprivileged BPF (default since kernel 5.16)
sysctl -w kernel.unprivileged_bpf_disabled=1

# Enable kernel lockdown
# Boot parameter: lockdown=integrity  (or lockdown=confidentiality)

# Restrict CAP_BPF
# Only grant to dedicated security tool service accounts
```

**Subverting eBPF-based security tools:** A root-level attacker can unload defensive eBPF programs via `bpf(BPF_PROG_DETACH)` or by deleting pinned files from `/sys/fs/bpf/`. The attacker can modify BPF maps used by security tools — removing entries from IOC hash maps or adding exclusions to process allowlists. More subtle subversion involves loading a higher-priority eBPF program on the same hook point that consumes events before the defensive program sees them. Detection: implement integrity checking of loaded eBPF programs by tracking their IDs and program tags, monitor for `BPF_MAP_UPDATE_ELEM` operations from non-security-tool processes.

---

## 2. eBPF Security Tools: Tetragon, Falco, Tracee, and Cilium

### 2.1 Cilium Tetragon

Tetragon (Isovalent/Cilium) is a runtime security enforcement engine built on eBPF. Its distinguishing feature is kernel-level policy enforcement: Tetragon can kill processes, deny syscalls, or send signals directly from the eBPF program without user-space round-trip latency.

**TracingPolicy for binary authorization:**
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-unauthorized-binaries
spec:
  kprobes:
  - call: "security_bprm_check"
    syscall: false
    args:
    - index: 0
      type: "linux_binprm"
    selectors:
    - matchBinaries:
      - operator: "NotIn"
        values:
        - "/usr/bin/bash"
        - "/usr/bin/python3"
        - "/usr/local/bin/app"
      matchActions:
      - action: Sigkill
```

**TracingPolicy for container escape detection:**
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-container-escape
spec:
  kprobes:
  - call: "__x64_sys_setns"
    syscall: true
    args:
    - index: 0
      type: "int"
    - index: 1
      type: "int"
    selectors:
    - matchNamespaces:
      - namespace: Pid
        operator: NotIn
        values:
        - "host_pid_ns_inum"
      matchActions:
      - action: Sigkill
        rateLimit: 0
      - action: Post
```

**TracingPolicy for privilege escalation via credential modification:**
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-priv-escalation
spec:
  kprobes:
  - call: "commit_creds"
    syscall: false
    args:
    - index: 0
      type: "cred"
    selectors:
    - matchActions:
      - action: Post
    returnArg:
      index: 0
      type: "int"
```

Tetragon provides process lineage tracking (full ancestry trees), namespace-aware monitoring (distinguishing container activity from host activity via cgroup and namespace IDs), and Kubernetes-aware enrichment (pod name, namespace, labels). Events integrate with SIEM pipelines via gRPC export or JSON log shipping.

### 2.2 Falco

Falco (Sysdig, CNCF graduated) is a runtime detection tool using eBPF (or a kernel module) for system call interception. Falco operates in detection-only mode with a rule engine evaluating system calls against security rules.

**Comprehensive Falco rules for common attacks:**

```yaml
# Reverse shell detection
- rule: Reverse Shell in Container
  desc: Detect dup/dup2 redirecting stdio to network socket
  condition: >
    evt.type in (dup, dup2, dup3) and container.id != host
    and fd.num in (0, 1, 2) and fd.type in (ipv4, ipv6)
  output: >
    Reverse shell detected (container=%container.name pod=%k8s.pod.name
    proc=%proc.name pid=%proc.pid fd.rip=%fd.rip fd.rport=%fd.rport
    user=%user.name image=%container.image.repository)
  priority: CRITICAL

# Sensitive file access
- rule: Read Sensitive File in Container
  desc: Detect access to credential/shadow files in container
  condition: >
    open_read and container.id != host
    and fd.name in (/etc/shadow, /etc/sudoers, /proc/1/environ,
      /var/run/secrets/kubernetes.io/serviceaccount/token)
    and not proc.name in (sshd, sudo, su, login)
  output: >
    Sensitive file read (file=%fd.name proc=%proc.name container=%container.name
    pod=%k8s.pod.name image=%container.image.repository)
  priority: WARNING

# Crypto miner detection (behavioral — CPU-bound + pool connection)
- rule: Outbound Connection to Mining Pool
  desc: Detect connections to common mining pool ports
  condition: >
    evt.type = connect and container.id != host
    and fd.rport in (3333, 4444, 5555, 8888, 9999, 14433, 14444)
    and fd.type = ipv4
  output: >
    Mining pool connection (proc=%proc.name port=%fd.rport ip=%fd.rip
    container=%container.name pod=%k8s.pod.name)
  priority: CRITICAL

# Container escape via nsenter
- rule: Namespace Change via setns
  desc: Detect setns calls from container attempting host namespace access
  condition: >
    evt.type = setns and container.id != host
    and not proc.name in (kubelet, containerd-shim, runc)
  output: >
    Container namespace escape attempt (proc=%proc.name pid=%proc.pid
    container=%container.name pod=%k8s.pod.name user=%user.name)
  priority: CRITICAL

# Fileless execution via memfd_create
- rule: Fileless Execution via memfd_create
  desc: Detect in-memory code execution pattern
  condition: >
    evt.type = memfd_create
    and not proc.name in (chrome, firefox, pulseaudio, pipewire)
  output: >
    memfd_create called (proc=%proc.name pid=%proc.pid user=%user.name
    container=%container.name memfd_name=%evt.arg.name)
  priority: HIGH

# Privileged container started
- rule: Privileged Container Started
  desc: Detect creation of privileged containers
  condition: >
    evt.type = container and container.privileged = true
  output: >
    Privileged container started (container=%container.name
    image=%container.image.repository pod=%k8s.pod.name)
  priority: CRITICAL

# Drift detection — new binary execution
- rule: Drift Detected — Binary Not in Original Image
  desc: Detect execution of binaries written after container start
  condition: >
    spawned_process and container.id != host
    and proc.is_exe_from_memfd = true
    or (proc.exe_ino.ctime_duration_proc_start > 0
        and not proc.name in (apt, dpkg, pip, npm, yarn))
  output: >
    Drift detected — new binary (proc=%proc.name container=%container.name
    pod=%k8s.pod.name image=%container.image.repository)
  priority: HIGH
```

**Attacking/evading Falco:** An attacker aware of Falco's user-space processing can exploit the latency between event capture and rule evaluation. Targeted evasion involves: renaming malicious binaries to match Falco's exception lists, using system calls that Falco doesn't monitor by default (Falco's default configuration does not monitor all 400+ Linux system calls), or operating at the application layer rather than the system call layer (using legitimate tools like `curl` or `python` for malicious purposes). These evasion techniques highlight the need for custom Falco rules tailored to each environment's expected behavior baseline.

### 2.3 Tracee

Tracee (Aqua Security) captures over 400 kernel events and implements signature-based detection using Rego policies (OPA) or Go modules. Tracee's strength is purpose-built detection content for container escape techniques (CVE-2022-0185 heap overflow, CVE-2022-0847 Dirty Pipe, runc CVE-2024-21626), Kubernetes attack patterns (service account token theft), and crypto-mining detection.

**Tracee deployment with targeted detection:**
```bash
# Run Tracee with specific event filters
docker run --name tracee --rm -it --pid=host --cgroupns=host \
  --privileged -v /etc/os-release:/etc/os-release-host:ro \
  -v /boot/config-$(uname -r):/boot/config-$(uname -r):ro \
  aquasec/tracee:latest \
  --events execve,setns,ptrace,memfd_create,init_module \
  --scope container \
  --output json
```

### 2.4 Cilium for Network Security

Cilium provides eBPF-based networking, observability, and security for Kubernetes.

**Identity-based L7 NetworkPolicy:**
```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: restrict-api-access
spec:
  endpointSelector:
    matchLabels:
      app: payment-service
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8443"
        protocol: TCP
      rules:
        http:
        - method: "POST"
          path: "/api/v1/charge"
        - method: "GET"
          path: "/api/v1/status"
  egress:
  - toEndpoints:
    - matchLabels:
        app: postgres
    toPorts:
    - ports:
      - port: "5432"
  - toFQDNs:
    - matchName: "api.stripe.com"
    toPorts:
    - ports:
      - port: "443"
```

**DNS-based egress restriction (anti-exfiltration):**
```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: restrict-dns-egress
spec:
  endpointSelector:
    matchLabels:
      app: backend
  egress:
  - toFQDNs:
    - matchPattern: "*.internal.corp"
    - matchName: "api.stripe.com"
  - toEndpoints:
    - matchLabels:
        io.cilium/reserved:kube-dns: ""
    toPorts:
    - ports:
      - port: "53"
        protocol: ANY
      rules:
        dns:
        - matchPattern: "*.internal.corp"
        - matchName: "api.stripe.com"
```

---

## 3. Auditd at Scale: Audit Rule Design and Deployment

The Linux Audit Framework (`auditd`) remains the standard for compliance-mandated auditing, required by STIG, CIS, and PCI-DSS baselines.

### 3.1 Audit Framework Architecture

The framework consists of: the kernel audit subsystem (intercepting system calls and generating records), `auditd` (user-space daemon writing records to log files), `auditctl` (rule management), `ausearch`/`aureport` (search and reporting), and `audispd`/`audisp-remote` (event dispatch to remote systems).

### 3.2 Security-Focused Audit Rule Design

**Comprehensive security audit rules (`/etc/audit/rules.d/security.rules`):**
```bash
# === Execution monitoring (most important single rule) ===
-a always,exit -F arch=b64 -S execve -S execveat -k exec_monitor

# === Identity/credential file integrity ===
-w /etc/passwd -p wa -k identity_file
-w /etc/shadow -p wa -k identity_file
-w /etc/group -p wa -k identity_file
-w /etc/gshadow -p wa -k identity_file
-w /etc/sudoers -p wa -k priv_escalation
-w /etc/sudoers.d/ -p wa -k priv_escalation

# === Privilege escalation syscalls ===
-a always,exit -F arch=b64 -S setuid -S setgid -S setreuid -S setregid -k priv_escalation
-a always,exit -F arch=b64 -S setresuid -S setresgid -k priv_escalation

# === Kernel module loading (rootkit detection) ===
-a always,exit -F arch=b64 -S init_module -S finit_module -S delete_module -k kernel_module

# === Process injection via ptrace ===
-a always,exit -F arch=b64 -S ptrace -k process_injection

# === Namespace manipulation (container escape) ===
-a always,exit -F arch=b64 -S unshare -k namespace_manipulation
-a always,exit -F arch=b64 -S setns -k namespace_manipulation
-a always,exit -F arch=b64 -S clone -F a0&0x7E020000 -k namespace_clone

# === Socket operations (reverse shell detection) ===
-a always,exit -F arch=b64 -S socket -F a0=2 -F a1=1 -k socket_create
-a always,exit -F arch=b64 -S connect -F a0=2 -k outbound_connect

# === Fileless execution ===
-a always,exit -F arch=b64 -S memfd_create -k fileless_exec

# === BPF program loading ===
-a always,exit -F arch=b64 -S bpf -k bpf_load

# === SSH configuration ===
-w /etc/ssh/sshd_config -p wa -k sshd_config
-w /root/.ssh/ -p wa -k ssh_keys
-w /etc/ssh/ssh_host_rsa_key -p r -k ssh_hostkey_read

# === PAM configuration ===
-w /etc/pam.d/ -p wa -k pam_config
-w /etc/security/ -p wa -k pam_security

# === Cron persistence ===
-w /etc/crontab -p wa -k cron_persistence
-w /etc/cron.d/ -p wa -k cron_persistence
-w /var/spool/cron/ -p wa -k cron_persistence

# === Systemd persistence ===
-w /etc/systemd/system/ -p wa -k systemd_persistence
-w /usr/lib/systemd/system/ -p wa -k systemd_persistence

# === LD_PRELOAD rootkits ===
-w /etc/ld.so.preload -p wa -k ld_preload
-w /etc/ld.so.conf -p wa -k ld_config

# === Kernel memory access ===
-w /proc/kcore -p r -k kernel_memory_read
-w /dev/mem -p rw -k raw_memory
-w /dev/kmem -p rw -k raw_memory

# === Make rules immutable (requires reboot to change) ===
-e 2
```

### 3.3 Auditbeat and Modern Audit Pipeline Integration

Auditbeat (Elastic) replaces the traditional `auditd` daemon by reading directly from the kernel audit subsystem's netlink socket. Auditbeat provides several advantages: structured JSON output, container metadata enrichment, direct shipping to Elasticsearch or Kafka, and combined auditd rules + file integrity monitoring + system module monitoring in a single agent.

### 3.4 Performance Tuning

```bash
# Increase backlog to prevent event drops under load
auditctl -b 8192

# Set rate limit (events per second; 0 = unlimited)
auditctl -r 0

# Async flush for high-throughput hosts
# /etc/audit/auditd.conf:
# flush = INCREMENTAL_ASYNC
# freq = 50

# Make rules immutable to prevent attacker deletion
auditctl -e 2
```

**Tiered auditing strategy:** Apply comprehensive rules (all system calls) to high-value servers (domain controllers, jump boxes, management infrastructure) and apply targeted rules (only execution, privilege escalation, and file integrity monitoring) to commodity workloads.

### 3.5 Linux Integrity Measurement Architecture (IMA)

IMA extends the audit framework by measuring (hashing) and optionally appraising (verifying signatures of) files before they are accessed. IMA operates at the VFS layer, intercepting file operations and computing SHA-256 hashes that are extended into TPM PCR 10.

**IMA appraisal mode configuration:**
```bash
# Boot parameters
ima_policy=appraise_tcb ima_appraise=enforce

# Custom IMA policy (/etc/ima/ima-policy)
# Appraise all executables
appraise func=BPRM_CHECK fowner=0 appraise_type=imasig

# Appraise all shared libraries
appraise func=MMAP_CHECK mask=MAY_EXEC appraise_type=imasig

# Appraise kernel modules
appraise func=MODULE_CHECK appraise_type=imasig

# Sign a binary for IMA
evmctl ima_sign --key /path/to/private.pem /usr/bin/myapp

# Verify IMA measurement log
cat /sys/kernel/security/integrity/ima/ascii_runtime_measurements
```

**Attacking IMA:** Attackers operating within IMA-protected environments use memory-only techniques — `memfd_create` to create file descriptors backed by anonymous memory pages, then `fexecve` to execute from the file descriptor. Since the executable never touches the filesystem, IMA has no file to measure.

Detection:
```bash
# Auditd rule for memfd_create + execution
-a always,exit -F arch=b64 -S memfd_create -k fileless_exec
-a always,exit -F arch=b64 -S execveat -F a2&0x1000 -k fileless_execveat
```

### 3.6 Attacking the Audit Subsystem

**Rule deletion:** `auditctl -D` deletes all rules instantly. Detection requires a pre-existing rule monitoring `auditctl` execution.

**Audit filter injection:** The attacker uses `auditctl` to add exclude rules that suppress their own activity:
```bash
# Attacker suppresses their backdoor from audit
auditctl -a never,exit -F exe=/tmp/.hidden/backdoor
```

Detection: monitor for `auditctl` execution with `-a never` arguments and periodically dump the active rule set (`auditctl -l`) for comparison against expected baseline. Use `-e 2` (immutable) to prevent runtime rule modifications.

**Kernel-level bypass:** An attacker with kernel code execution can patch the audit subsystem to suppress specific events. Detection requires independent eBPF monitoring or hardware-level tracing.

---

## 4. Zero Trust Architecture

Zero trust replaces perimeter-based security with continuous verification of every access request based on identity, device state, and context.

### 4.1 Core Architecture (NIST SP 800-207)

| Component | Role | Implementation Examples |
|-----------|------|------------------------|
| **Policy Engine (PE)** | Evaluates access requests against policy: identity, device trust score, threat intel, context | Azure AD Conditional Access, Google BeyondCorp Access Context Manager, Zscaler ZPA policy engine |
| **Policy Administrator (PA)** | Executes PE decisions: issues/revokes time-limited access tokens, instructs PEP | Azure AD token service, Cloudflare Access session management, SPIRE server |
| **Policy Enforcement Point (PEP)** | Gateway through which all access passes; enforces PA decisions | Zscaler connector, Cloudflare Tunnel, Istio sidecar proxy, Envoy, cloud security groups |

**Trust evaluation signals:**

| Signal | Source | Weight |
|--------|--------|--------|
| Authentication strength | IdP (FIDO2 > TOTP > SMS > password) | Critical |
| Device compliance | MDM/EDR (patch level, disk encryption, EDR health) | High |
| Network risk | IP reputation, geolocation, impossible travel | Medium |
| Behavioral baseline | UEBA (normal access patterns vs current request) | Medium |
| Threat intelligence | IOC feeds (IP, domain, hash match) | High |
| Session age | Time since last strong auth | Medium |

### 4.2 Identity-Centric Access Control

**Phishing-resistant MFA deployment:**

| MFA Method | Phishing Resistant | Bypass by Real-Time Proxy (Evilginx2) | Recommended |
|-----------|-------------------|---------------------------------------|-------------|
| FIDO2/WebAuthn (hardware key) | Yes — origin-bound | No — authenticator rejects proxy origin | Yes |
| Platform authenticator (Windows Hello, Touch ID) | Yes — origin-bound | No | Yes |
| TOTP (Google Authenticator) | No | Yes — proxy captures code in real time | No |
| Push notification (Authenticator app) | No | Yes — MFA fatigue / prompt bombing | No |
| SMS OTP | No | Yes — SIM swap, SS7 interception | No |

**Azure AD Conditional Access policy example (enforce FIDO2 for admin access):**
```json
{
  "displayName": "Require FIDO2 for Admin Roles",
  "state": "enabled",
  "conditions": {
    "users": {
      "includeRoles": [
        "62e90394-69f5-4237-9190-012177145e10",
        "194ae4cb-b126-40b2-bd5b-6091b380977d"
      ]
    },
    "applications": {
      "includeApplications": ["All"]
    }
  },
  "grantControls": {
    "operator": "OR",
    "builtInControls": [],
    "authenticationStrength": {
      "id": "00000000-0000-0000-0000-000000000004"
    }
  },
  "sessionControls": {
    "signInFrequency": {
      "value": 1,
      "type": "hours",
      "isEnabled": true
    },
    "persistentBrowser": {
      "isEnabled": true,
      "mode": "never"
    }
  }
}
```

**Continuous Access Evaluation (CAE):**
Azure AD CAE enables near-real-time token revocation. Instead of waiting for the access token's 1-hour expiration, CAE-enabled resource providers subscribe to Azure AD events (user disabled, password changed, location change) and revoke access immediately.

Attack: An attacker who steals a non-CAE token has up to 1 hour of access regardless of remediation. CAE tokens are revoked within minutes, but the attacker can still use them until the revocation event propagates. Sophisticated attackers target the gap between token theft and CAE event delivery.

Detection (KQL for token theft indicators):
```kql
SigninLogs
| where TimeGenerated > ago(1h)
| where ResultType == 0
| summarize Locations = make_set(LocationDetails.city),
    IPs = make_set(IPAddress),
    DeviceCount = dcount(DeviceDetail.deviceId)
    by UserPrincipalName, bin(TimeGenerated, 5m)
| where array_length(Locations) > 1 or array_length(IPs) > 3
| project TimeGenerated, UserPrincipalName, Locations, IPs, DeviceCount
```

**Workload identity with SPIFFE/SPIRE:**

SPIFFE (Secure Production Identity Framework for Everyone) provides cryptographic identity to workloads via X.509 SVIDs (SPIFFE Verifiable Identity Documents). SPIRE (SPIFFE Runtime Environment) is the reference implementation.

```yaml
# SPIRE server configuration (server.conf)
server {
    bind_address = "0.0.0.0"
    bind_port = "8081"
    trust_domain = "corp.example.com"
    data_dir = "/opt/spire/data/server"
    log_level = "INFO"
    ca_ttl = "24h"
    default_x509_svid_ttl = "1h"
}

plugins {
    DataStore "sql" {
        plugin_data {
            database_type = "postgres"
            connection_string = "dbname=spire host=db.internal sslmode=verify-full"
        }
    }
    NodeAttestor "k8s_psat" {
        plugin_data {
            clusters = {
                "production" = {
                    service_account_allow_list = ["spire:spire-agent"]
                }
            }
        }
    }
    KeyManager "disk" {
        plugin_data {
            keys_path = "/opt/spire/data/server/keys.json"
        }
    }
}
```

```yaml
# SPIRE registration entry — bind workload identity to Kubernetes pod
# spiffe://corp.example.com/ns/payments/sa/payment-processor
apiVersion: spire.spiffe.io/v1alpha1
kind: ClusterSPIFFEID
metadata:
  name: payment-processor
spec:
  spiffeIDTemplate: "spiffe://corp.example.com/ns/{{ .PodMeta.Namespace }}/sa/{{ .PodSpec.ServiceAccountName }}"
  podSelector:
    matchLabels:
      app: payment-processor
  namespaceSelector:
    matchLabels:
      environment: production
```

### 4.3 Microsegmentation

Microsegmentation enforces network access control at the individual workload level with default-deny policies.

**Kubernetes NetworkPolicy (default deny + explicit allow):**
```yaml
# Default deny all ingress and egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress

---
# Allow specific communication path
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-api
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api-server
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8443
```

**Calico GlobalNetworkPolicy (cluster-wide microsegmentation):**
```yaml
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: deny-public-egress
spec:
  selector: environment == 'production'
  types:
  - Egress
  egress:
  # Allow DNS
  - action: Allow
    protocol: UDP
    destination:
      ports: [53]
  # Allow internal cluster
  - action: Allow
    destination:
      selector: all()
  # Deny everything else
  - action: Deny
```

**Cilium L7 policy with HTTP inspection:**
```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-l7-policy
spec:
  endpointSelector:
    matchLabels:
      app: api-server
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8443"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/api/v1/public/.*"
        - method: "POST"
          path: "/api/v1/orders"
          headers:
          - 'X-Request-Source: frontend'
```

**Attacking microsegmentation:**

| Attack Vector | Description | Defense |
|--------------|-------------|---------|
| Tunneling through allowed paths | Attacker compromises pod A, tunnels attack traffic through permitted HTTPS to pod B | L7 inspection on permitted connections (Cilium, Istio) |
| Policy manipulation | Compromise Kubernetes API server, modify NetworkPolicies | RBAC lockdown on networking.k8s.io, audit log monitoring, admission controllers |
| DNS tunneling | Exfiltrate data via DNS queries to attacker-controlled domain | DNS-aware policies (Cilium toFQDNs), DNS query entropy analysis |
| Protocol abuse | Embed C2 in permitted protocols (HTTP headers, gRPC metadata) | Deep packet inspection, behavioral baselines on traffic patterns |
| East-west lateral movement | Pivot between pods with allowed connectivity | Network flow anomaly detection (Hubble), UEBA on pod communication patterns |

**Cloud security group microsegmentation (AWS example):**
```bash
# Create security group with minimal ingress
aws ec2 create-security-group --group-name db-tier \
  --description "Database tier - restricted access"

# Allow only app-tier on port 5432
aws ec2 authorize-security-group-ingress \
  --group-id sg-db-tier \
  --protocol tcp --port 5432 \
  --source-group sg-app-tier

# VPC Flow Logs for east-west visibility
aws ec2 create-flow-logs --resource-type VPC \
  --resource-ids vpc-123456 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/flowlogs
```

### 4.4 Container Runtime Hardening

#### 4.4.1 Seccomp profiles

Seccomp (Secure Computing Mode) restricts which system calls a process can invoke. A seccomp-bpf profile defines an allowlist/denylist of syscalls.

**Custom seccomp profile for a web application:**
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "read", "write", "close", "fstat", "lseek", "mmap", "mprotect",
        "munmap", "brk", "rt_sigaction", "rt_sigprocmask", "ioctl",
        "access", "pipe", "select", "sched_yield", "mremap", "msync",
        "mincore", "madvise", "shmget", "shmat", "shmctl",
        "dup", "dup2", "pause", "nanosleep", "getitimer",
        "alarm", "setitimer", "getpid", "sendfile",
        "socket", "connect", "accept", "sendto", "recvfrom",
        "sendmsg", "recvmsg", "shutdown", "bind", "listen",
        "getsockname", "getpeername", "socketpair", "setsockopt",
        "getsockopt", "clone", "fork", "execve", "exit",
        "wait4", "kill", "uname", "fcntl", "flock",
        "fsync", "fdatasync", "truncate", "ftruncate",
        "getdents", "getdents64", "getcwd", "chdir",
        "rename", "mkdir", "rmdir", "creat", "link",
        "unlink", "symlink", "readlink", "chmod",
        "chown", "lchown", "umask", "gettimeofday",
        "getrlimit", "getrusage", "sysinfo", "times",
        "getuid", "getgid", "geteuid", "getegid",
        "setpgid", "getppid", "getpgrp", "setsid",
        "sigaltstack", "statfs", "fstatfs",
        "arch_prctl", "clock_gettime", "clock_nanosleep",
        "exit_group", "epoll_wait", "epoll_ctl",
        "tgkill", "openat", "mkdirat", "newfstatat",
        "unlinkat", "renameat", "readlinkat",
        "faccessat", "epoll_create1", "pipe2",
        "accept4", "dup3", "prlimit64",
        "getrandom", "futex", "set_tid_address",
        "set_robust_list", "rseq", "clone3",
        "close_range", "openat2", "statx"
      ],
      "action": "SCMP_ACT_ALLOW"
    },
    {
      "names": ["ptrace"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    },
    {
      "names": ["init_module", "finit_module", "delete_module"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
```

**Kubernetes pod with seccomp:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/web-app.json
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
  - name: app
    image: gcr.io/project/app:sha256-abc123
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir:
      sizeLimit: 100Mi
```

#### 4.4.2 AppArmor profiles

```
# /etc/apparmor.d/container-web-app
#include <tunables/global>

profile container-web-app flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  # Allow reading application files
  /app/** r,
  /app/bin/* ix,

  # Allow temp writes
  /tmp/** rw,

  # Allow network
  network inet stream,
  network inet6 stream,

  # Deny sensitive paths
  deny /etc/shadow r,
  deny /etc/sudoers r,
  deny /proc/*/mem rw,
  deny /sys/kernel/** rw,

  # Deny ptrace
  deny ptrace (read, readby, trace, traceby),

  # Deny mount
  deny mount,
  deny umount,

  # Deny raw sockets
  deny network raw,
  deny network packet,
}
```

```yaml
# Kubernetes pod with AppArmor
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: localhost/container-web-app
spec:
  containers:
  - name: app
    image: gcr.io/project/app:latest
```

#### 4.4.3 Linux Security Module comparison

| Feature | SELinux | AppArmor | Landlock |
|---------|---------|----------|----------|
| Model | Type Enforcement (label-based) | Path-based | Path-based (unprivileged) |
| Policy scope | System-wide mandatory | Per-profile | Per-process (self-sandboxing) |
| Kernel support | RHEL, CentOS, Fedora default | Ubuntu, SUSE default | Kernel 5.13+ (all distros) |
| Complexity | High — type/role/domain model | Medium — path rules | Low — simple API |
| Container support | Fine-grained (label per container) | Profile per container | Per-process from container |
| Root bypass | No — MAC enforced even on root | No — MAC enforced on root | No — irreversible restriction |
| Unprivileged use | No — requires root for policy | No — requires root for profiles | Yes — process restricts itself |
| Network control | Yes (ports, connections) | Yes (basic) | Yes (since kernel 6.7) |
| Filesystem control | Label-based (fine-grained) | Path-based (glob patterns) | Path-based (hierarchy) |

**Landlock self-sandboxing (application restricting itself):**
```c
#include <linux/landlock.h>
#include <sys/syscall.h>

struct landlock_ruleset_attr ruleset_attr = {
    .handled_access_fs = LANDLOCK_ACCESS_FS_READ_FILE |
                         LANDLOCK_ACCESS_FS_WRITE_FILE |
                         LANDLOCK_ACCESS_FS_EXECUTE,
};

int ruleset_fd = syscall(SYS_landlock_create_ruleset,
                         &ruleset_attr, sizeof(ruleset_attr), 0);

// Allow read-only access to /usr
struct landlock_path_beneath_attr path_beneath = {
    .allowed_access = LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_EXECUTE,
    .parent_fd = open("/usr", O_PATH | O_CLOEXEC),
};
syscall(SYS_landlock_add_rule, ruleset_fd,
        LANDLOCK_RULE_PATH_BENEATH, &path_beneath, 0);

// Allow read-write to /tmp
path_beneath.allowed_access = LANDLOCK_ACCESS_FS_READ_FILE |
                              LANDLOCK_ACCESS_FS_WRITE_FILE;
path_beneath.parent_fd = open("/tmp", O_PATH | O_CLOEXEC);
syscall(SYS_landlock_add_rule, ruleset_fd,
        LANDLOCK_RULE_PATH_BENEATH, &path_beneath, 0);

// Enforce — irreversible
prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0);
syscall(SYS_landlock_restrict_self, ruleset_fd, 0);
// From this point, process can only access /usr (ro) and /tmp (rw)
```

### 4.5 Service Mesh Security

**Istio mTLS configuration (strict mode):**
```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: strict-mtls
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
```

**Istio AuthorizationPolicy (workload-level access control):**
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: payment-service-policy
  namespace: production
spec:
  selector:
    matchLabels:
      app: payment-service
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
        - "cluster.local/ns/production/sa/frontend"
        - "cluster.local/ns/production/sa/order-service"
    to:
    - operation:
        methods: ["POST"]
        paths: ["/api/v1/charge", "/api/v1/refund"]
    when:
    - key: request.headers[x-request-id]
      notValues: [""]

---
# Default deny all in namespace
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: production
spec:
  {}
```

**Attacking service mesh:**

| Attack | Mechanism | Mitigation |
|--------|-----------|------------|
| Sidecar bypass | Process in pod sends traffic directly, bypassing Envoy sidecar | Istio CNI plugin + `iptables` rules enforced by init container; Cilium eBPF enforcement |
| Certificate theft | Extract SVID private key from Envoy's memory or filesystem | Short-lived certificates (1h TTL), HSM-backed CA, memory protection |
| Control plane compromise | Attack Istio control plane (istiod) for policy manipulation | RBAC on istiod, mutual TLS to control plane, audit logging |
| mTLS downgrade | Permissive mode allows plaintext fallback | Enforce STRICT mode globally, alert on PERMISSIVE |

### 4.6 Windows Runtime Protection

#### 4.6.1 Windows Defender Application Control (WDAC)

WDAC enforces code integrity policies restricting which drivers and applications can run. It replaces and supersedes AppLocker for application whitelisting.

**Create and deploy a WDAC policy:**
```powershell
# Scan reference machine to create baseline policy
New-CIPolicy -Level Publisher -FilePath C:\policies\BasePolicy.xml -ScanPath C:\Windows

# Add fallback for unsigned code from specific paths
Add-CIPolicyRule -FilePath C:\policies\BasePolicy.xml \
  -Rule (New-CIPolicyRule -FilePathRule "C:\Program Files\*" -Level FilePublisher)

# Convert to binary
ConvertFrom-CIPolicy -XmlFilePath C:\policies\BasePolicy.xml \
  -BinaryFilePath C:\Windows\System32\CodeIntegrity\SIPolicy.p7b

# Deploy via GPO
# Computer Configuration → Administrative Templates → System →
#   Device Guard → Deploy Windows Defender Application Control
```

**WDAC bypass techniques and detection:**

| Bypass | Mechanism | Detection |
|--------|-----------|-----------|
| Signed LOLBIN abuse | Use Microsoft-signed binaries (MSBuild.exe, InstallUtil.exe, RegSvcs.exe) to execute arbitrary code | WDAC deny rules for known LOLBAS; Sysmon Event ID 1 for LOLBIN with unusual arguments |
| Managed installer bypass | Abuse ConfigMgr/Intune managed installer trust to install malicious software | Restrict managed installer scope, monitor installed software inventory |
| Script enforcement gap | WDAC doesn't enforce on .bat/.cmd by default | Enable script enforcement in WDAC policy (`<Script Enforcement />`) |

#### 4.6.2 Attack Surface Reduction (ASR) Rules

```powershell
# Enable ASR rules via PowerShell
# Block credential stealing from LSASS
Set-MpPreference -AttackSurfaceReductionRules_Ids 9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2 \
  -AttackSurfaceReductionRules_Actions Enabled

# Block process creation from Office macros
Set-MpPreference -AttackSurfaceReductionRules_Ids 3b576869-a4ec-4529-8536-b80a7769e899 \
  -AttackSurfaceReductionRules_Actions Enabled

# Block execution of potentially obfuscated scripts
Set-MpPreference -AttackSurfaceReductionRules_Ids 5beb7efe-fd9a-4556-801d-275e5ffc04cc \
  -AttackSurfaceReductionRules_Actions Enabled

# Block Win32 API calls from Office macros
Set-MpPreference -AttackSurfaceReductionRules_Ids 92e97fa1-2edf-4476-bdd6-9dd0b4dddc7b \
  -AttackSurfaceReductionRules_Actions Enabled

# Block untrusted/unsigned processes from USB
Set-MpPreference -AttackSurfaceReductionRules_Ids b2b3f03d-6a65-4f7b-a9c7-1c7ef74a9ba4 \
  -AttackSurfaceReductionRules_Actions Enabled

# Block persistence through WMI event subscription
Set-MpPreference -AttackSurfaceReductionRules_Ids e6db77e5-3df2-4cf1-b95a-636979351e5b \
  -AttackSurfaceReductionRules_Actions Enabled
```

| ASR Rule GUID | Purpose |
|--------------|---------|
| `9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2` | Block credential stealing from LSASS |
| `3b576869-a4ec-4529-8536-b80a7769e899` | Block process creation from Office macros |
| `5beb7efe-fd9a-4556-801d-275e5ffc04cc` | Block obfuscated scripts |
| `92e97fa1-2edf-4476-bdd6-9dd0b4dddc7b` | Block Win32 API calls from Office macros |
| `d4f940ab-401b-4efc-aadc-ad5f3c50688a` | Block child process creation from Office |
| `26190899-1602-49e8-8b27-eb1d0a1ce869` | Block Office creating executable content |
| `7674ba52-37eb-4a4f-a9a1-f0f9a1619a2c` | Block Adobe Reader child process creation |
| `b2b3f03d-6a65-4f7b-a9c7-1c7ef74a9ba4` | Block unsigned/untrusted from USB |
| `e6db77e5-3df2-4cf1-b95a-636979351e5b` | Block WMI event subscription persistence |
| `d3e037e1-3eb8-44c8-a917-57927947596d` | Block JavaScript/VBScript launching content |
| `be9ba2d9-53ea-4cdc-84e5-9b1eeee46550` | Block executable content from email/webmail |
| `01443614-cd74-433a-b99e-2ecdc07bfc25` | Block executable files unless they meet prevalence/age/trusted criteria |

#### 4.6.3 Credential Guard and HVCI

```powershell
# Enable Credential Guard via registry
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 1 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v LsaCfgFlags /t REG_DWORD /d 1 /f

# Enable HVCI (Hypervisor-protected Code Integrity)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 1 /f

# Verify status
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
  Select-Object *VirtualizationBasedSecurity*, *CredentialGuard*, *CodeIntegrity*
```

### 4.7 Supply Chain Runtime Verification

#### 4.7.1 Image signing and verification with Sigstore/cosign

```bash
# Sign container image with cosign (keyless — uses OIDC identity)
cosign sign --yes gcr.io/project/app:v1.2.3

# Sign with explicit key
cosign sign --key cosign.key gcr.io/project/app:v1.2.3

# Verify signature
cosign verify --key cosign.pub gcr.io/project/app:v1.2.3

# Verify keyless signature (checks OIDC identity)
cosign verify --certificate-identity user@example.com \
  --certificate-oidc-issuer https://accounts.google.com \
  gcr.io/project/app:v1.2.3

# Attach SBOM
cosign attach sbom --sbom sbom.spdx.json gcr.io/project/app:v1.2.3
```

#### 4.7.2 Admission controllers for runtime verification

**Kyverno policy — require signed images:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-images
spec:
  validationFailureAction: Enforce
  background: false
  webhookTimeoutSeconds: 30
  rules:
  - name: verify-image-signature
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "gcr.io/project/*"
      - "registry.internal/*"
      attestors:
      - count: 1
        entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
              -----END PUBLIC KEY-----
```

**Kyverno policy — enforce pod security baseline:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: restrict-pod-security
spec:
  validationFailureAction: Enforce
  rules:
  - name: deny-privileged
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Privileged containers are not allowed"
      pattern:
        spec:
          containers:
          - securityContext:
              privileged: "!true"
              allowPrivilegeEscalation: "!true"
          initContainers:
          - securityContext:
              privileged: "!true"
              allowPrivilegeEscalation: "!true"

  - name: require-non-root
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Containers must run as non-root"
      pattern:
        spec:
          securityContext:
            runAsNonRoot: true
          containers:
          - securityContext:
              runAsNonRoot: true

  - name: drop-all-capabilities
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Containers must drop all capabilities"
      pattern:
        spec:
          containers:
          - securityContext:
              capabilities:
                drop:
                - ALL

  - name: require-readonly-rootfs
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Root filesystem must be read-only"
      pattern:
        spec:
          containers:
          - securityContext:
              readOnlyRootFilesystem: true
```

**OPA Gatekeeper constraint — restrict image registries:**
```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sAllowedRepos
metadata:
  name: allowed-repos
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces:
    - "production"
    - "staging"
  parameters:
    repos:
    - "gcr.io/myproject/"
    - "registry.internal/"

---
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sallowedrepos
spec:
  crd:
    spec:
      names:
        kind: K8sAllowedRepos
      validation:
        openAPIV3Schema:
          type: object
          properties:
            repos:
              type: array
              items:
                type: string
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8sallowedrepos
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not startswith(container.image, input.parameters.repos[_])
        msg := sprintf("container <%v> image <%v> not from allowed registry",
                       [container.name, container.image])
      }
```

#### 4.7.3 SLSA framework levels

| SLSA Level | Requirements | Attestation |
|-----------|-------------|-------------|
| Level 1 | Build process documented | Provenance exists |
| Level 2 | Hosted build service, authenticated provenance | Signed provenance |
| Level 3 | Hardened build platform, non-falsifiable provenance | Verified via in-toto/SLSA provenance format |
| Level 4 | Two-person review, hermetic build, reproducible | Full supply chain integrity |

```bash
# Generate SLSA provenance with slsa-verifier
slsa-verifier verify-artifact myapp-v1.2.3.tar.gz \
  --provenance-path myapp-v1.2.3.intoto.jsonl \
  --source-uri github.com/org/repo \
  --source-tag v1.2.3
```

### 4.8 Behavioral Analysis and UEBA

**Impossible travel detection (KQL):**
```kql
SigninLogs
| where TimeGenerated > ago(24h)
| where ResultType == 0
| project TimeGenerated, UserPrincipalName,
    Lat = toreal(LocationDetails.geoCoordinates.latitude),
    Lon = toreal(LocationDetails.geoCoordinates.longitude),
    City = tostring(LocationDetails.city),
    IPAddress
| sort by UserPrincipalName, TimeGenerated asc
| extend PrevLat = prev(Lat), PrevLon = prev(Lon),
    PrevTime = prev(TimeGenerated), PrevUser = prev(UserPrincipalName)
| where UserPrincipalName == PrevUser
| extend DistKm = geo_distance_2points(Lon, Lat, PrevLon, PrevLat) / 1000,
    TimeDiffHours = datetime_diff('hour', TimeGenerated, PrevTime)
| where TimeDiffHours > 0
| extend RequiredSpeedKmh = DistKm / TimeDiffHours
| where RequiredSpeedKmh > 1000
| project TimeGenerated, UserPrincipalName, City, IPAddress,
    DistKm = round(DistKm, 0),
    TimeDiffHours, RequiredSpeedKmh = round(RequiredSpeedKmh, 0)
```

**Lateral movement detection (KQL):**
```kql
// Multiple logon failures followed by success from same source
SecurityEvent
| where TimeGenerated > ago(1h)
| where EventID in (4624, 4625)
| summarize
    FailCount = countif(EventID == 4625),
    SuccessCount = countif(EventID == 4624),
    TargetAccounts = make_set(TargetUserName),
    TargetHosts = make_set(WorkstationName)
    by IpAddress, bin(TimeGenerated, 10m)
| where FailCount > 5 and SuccessCount >= 1
| where array_length(TargetAccounts) > 1
| project TimeGenerated, IpAddress, FailCount, SuccessCount,
    TargetAccounts, TargetHosts
```

**Data exfiltration indicators (Falco + network):**
```yaml
# Unusual outbound data volume from container
- rule: Large Outbound Transfer from Container
  desc: Detect large data transfers from container to external
  condition: >
    evt.type in (sendto, sendmsg) and container.id != host
    and fd.type in (ipv4, ipv6)
    and not fd.rip in (rfc_1918_addresses)
    and evt.arg.res > 1048576
  output: >
    Large outbound transfer (proc=%proc.name container=%container.name
    dest=%fd.rip:%fd.rport bytes=%evt.arg.res pod=%k8s.pod.name)
  priority: WARNING
```

### 4.9 Attacking Zero Trust Architectures

Zero trust shifts the primary attack surface from network exploitation to identity compromise and trust evaluation manipulation:

| Attack Vector | Mechanism | Detection | Mitigation |
|--------------|-----------|-----------|------------|
| **IdP compromise (Golden SAML)** | Steal ADFS/Okta signing key → forge any SAML assertion | Anomalous token issuance patterns, signing key access audit | HSM-backed signing keys, IdP-specific monitoring |
| **Token theft (PRT/access token)** | Extract Primary Refresh Token from device or steal OAuth access token from browser | CAE events, token replay from different device/IP | Continuous Access Evaluation, token binding, short lifetimes |
| **Session hijacking** | Steal session cookie after authentication | Session from new IP/device without re-auth | Bind session to TLS channel, aggressive session timeouts |
| **MFA fatigue / push bombing** | Repeatedly send MFA push until user approves | High volume of denied MFA prompts followed by approval | Number matching, require FIDO2 for sensitive access |
| **Device trust spoofing** | Report fake compliance signals to MDM | Hardware-backed attestation (TPM) | Require TPM-based device health attestation, not software-reported |
| **Trusted device compromise** | Compromise an MDM-enrolled, compliant device | EDR behavioral analysis, credential monitoring | Continuous posture assessment, not point-in-time compliance |
| **OAuth consent grant abuse** | Trick admin into granting app broad API permissions | Monitor OAuth app registrations and consent grants | Restrict consent to admin-approved apps only |

### 4.10 Software-Defined Perimeters and BeyondCorp

Google's BeyondCorp model eliminates VPN-based perimeters, replacing them with an identity-aware proxy that authenticates users, verifies device posture, evaluates access policies, and establishes sessions only when all checks pass.

**Implementation comparison:**

| Product | Architecture | Identity Source | Device Posture | Network |
|---------|-------------|----------------|----------------|---------|
| Zscaler Private Access | Cloud-brokered (no direct connection) | Azure AD, Okta, SAML | CrowdStrike, Carbon Black, custom | ZTNA connector on-prem |
| Cloudflare Access | Edge-based proxy (Cloudflare tunnel) | Any OIDC/SAML IdP | Tanium, CrowdStrike, device certs | Cloudflare Tunnel daemon |
| Google BeyondCorp Enterprise | Chrome Enterprise + Access Context Manager | Google Workspace | Chrome Verified Access, MDM | Identity-Aware Proxy (IAP) |
| Azure AD Conditional Access | Cloud-native (Entra ID) | Azure AD | Intune compliance, hybrid join | Conditional Access + App Proxy |

**SDP architectural pattern:**
```
User → Identity-Aware Proxy (PEP)
    ↓ (1) AuthN (FIDO2/SSO)
    ↓ (2) Device posture check (TPM attestation + EDR health)
    ↓ (3) Policy evaluation (PE)
    ↓ (4) Session establishment (time-limited, scope-limited)
    → Application (never directly internet-accessible)
```

The SDP pattern ensures applications are never directly internet-accessible — they have no public DNS records or open inbound ports. The SDP gateway handles all external access, eliminating the internet-facing application attack surface.

---

## 5. Secure Boot, Measured Boot, and Hardware Attestation

### 5.1 UEFI Secure Boot Chain

Secure Boot ensures only cryptographically signed code executes during boot. The firmware contains trusted signing keys (Platform Key, Key Exchange Keys, `db` database of authorized signatures). Each boot component is verified before execution: firmware verifies bootloader, bootloader verifies kernel, kernel verifies modules.

**Attacking Secure Boot:**

| Attack | CVE | Mechanism |
|--------|-----|-----------|
| BlackLotus | CVE-2023-24932 | Exploited signed-but-vulnerable Windows Boot Manager; installed UEFI bootkit, disabled Secure Boot, BitLocker, HVCI, Defender |
| BootHole | CVE-2020-10713 | GRUB2 buffer overflow in config parser; pre-kernel code execution with Secure Boot |
| LogoFAIL | CVE-2023-5058+ | UEFI firmware image parser vulnerabilities; code execution during firmware phase, before Secure Boot validates OS |

**Secure Boot hardening:**
```bash
# Verify Secure Boot status (Linux)
mokutil --sb-state

# List enrolled keys
mokutil --list-enrolled

# On RHEL/CentOS — manage Machine Owner Keys
mokutil --import /path/to/key.der

# Verify kernel signing
pesign -S -i /boot/vmlinuz-$(uname -r)
```

### 5.2 Measured Boot and TPM Attestation

Measured boot records cryptographic measurements (hashes) of each boot component into TPM Platform Configuration Registers (PCRs) using hash extension: `PCR_new = SHA-256(PCR_old || hash(component))`.

| PCR | Content |
|-----|---------|
| 0 | Firmware code (UEFI ROM) |
| 1 | Firmware configuration (UEFI variables) |
| 4 | Bootloader (GRUB/Windows Boot Manager) |
| 7 | Secure Boot policy (db/dbx) |
| 8–9 | OS kernel and initramfs |
| 14 | IMA runtime integrity measurements |

**Remote attestation implementations:**

| Implementation | Platform | Integration |
|---------------|----------|-------------|
| Microsoft DHA (Device Health Attestation) | Windows | Intune/SCCM conditional access |
| Google Shielded VMs | GCP | vTPM-based boot integrity |
| Keylime (CNCF sandbox) | Linux | IMA measurement verification + TPM attestation |
| go-tpm-tools | Cross-platform | Google cloud infrastructure attestation |

```bash
# Keylime — verify remote host attestation
keylime_tenant -c add --uuid <agent-uuid> \
  --tpm_policy '{"22": ["sha256:expected_pcr_value"]}' \
  --ima_sign_verification_keys /path/to/ima-key.pub
```

**Attacking TPM attestation:** While TPM-based attestation is cryptographically robust, practical attack vectors exist:
- TOCTOU: modify boot components after measurement but before execution (requires precise timing + kernel access)
- Attestation infrastructure compromise: poison the "known-good PCR values" database
- Relay attacks: forward legitimate attestation from a clean machine while running compromised machine

### 5.3 Confidential Computing

**AMD SEV-SNP:** Encrypts each VM's memory with a unique AES-128 key managed by the AMD Secure Processor. SEV-SNP adds integrity protection (preventing hypervisor replay or modification of encrypted pages) and attestation. The hypervisor cannot read or modify VM memory despite managing resource allocation. Known attack: CacheWarp (CVE-2023-20592) exploited cache manipulation to corrupt guest memory integrity prior to firmware updates.

**Intel TDX (Trust Domain Extensions):** Creates isolated Trust Domains (TDs) with hardware-encrypted memory using the TDX Module running in SEAM (Secure Arbitration Mode) — more privileged than the hypervisor. Each TD has unique AES-128-XTS encryption keys with integrity protection.

**ARM CCA (Confidential Compute Architecture):** Uses Realms managed by a Realm Management Monitor (RMM) at R-EL2 with hardware-enforced isolation via the Granule Protection Table (GPT), classifying every physical page into Secure, Non-Secure, Root, and Realm states.

**Residual attack surface:**
- Side-channel attacks (Spectre, cache timing) can leak across isolation boundaries
- ÆPIC Leak (CVE-2022-21233) — APIC MMIO stale data leaks SGX/TDX data
- Interrupt injection by malicious hypervisor
- Attestation certificate chain validation failures

---

## 6. Integration: Runtime Security in the SIEM/SOAR Pipeline

### 6.1 Telemetry Normalization

eBPF tools (Tetragon, Falco, Tracee) each produce events in different formats. Normalization to ECS or OCSF (Domain 31A §1.2) is essential for cross-tool detection rules. Process execution events from Tetragon (protobuf/JSON) and auditd (key=value format) must both map to `process.name`, `process.pid`, `process.args`, `user.name`, `event.action` so a single Sigma rule detects behavior regardless of telemetry source.

### 6.2 Cross-Source Detection Rules

**Container escape detection combining eBPF and Kubernetes audit logs:**
Tetragon detects the `setns()` system call transitioning from a container namespace to the host namespace (kernel-level escape indicator), and the Kubernetes audit log simultaneously records the absence of any authorized `kubectl exec` session to that pod. The correlation of both indicators — kernel-level namespace transition without a corresponding Kubernetes API event — produces a high-confidence container escape alert.

**Credential theft detection combining auditd and SIEM enrichment:**
Auditd records an `execve` of a suspicious binary (matched against a Sigma rule for credential dumping tools), the SIEM pipeline enriches the event with asset inventory data (identifying the system as a production database server), and the SOAR playbook queries the zero trust policy engine to determine who has an active session to that server and whether the session was established with phishing-resistant MFA.

**Lateral movement detection combining network flow and endpoint telemetry:**
Cilium Hubble detects an unusual east-west connection between two pods that have not communicated before (network anomaly), and simultaneously Falco alerts on the destination pod executing an unexpected binary (host anomaly). Neither indicator alone is conclusive; together they indicate post-compromise lateral movement.

### 6.3 Zero Trust Telemetry for Detection

Zero trust policy engines generate rich telemetry: access grant/deny decisions with policy rationale and trust scores, authentication events with MFA method and device attestation results, and session lifecycle events. Correlating endpoint behavior (from eBPF/auditd) with access context (from the zero trust policy engine) provides higher-confidence detection than either source alone.

### 6.4 Architectural Decision Framework

| Requirement | Tool | Reason |
|-------------|------|--------|
| Container runtime enforcement (kill/deny) | Tetragon | Kernel-level enforcement, no user-space latency |
| Container runtime detection (alert) | Falco | Rich rule language, CNCF graduated, wide adoption |
| Container escape CVE detection | Tracee | Purpose-built signatures for known escape techniques |
| Network microsegmentation + L7 inspection | Cilium | eBPF-native, identity-aware, DNS-aware |
| Compliance-mandated auditing (STIG/CIS/PCI) | Auditd/Auditbeat | Required by compliance frameworks |
| Older kernels without BTF | Auditd | Works on any kernel version |
| Windows application whitelisting | WDAC | Kernel-mode enforcement, supersedes AppLocker |
| Windows exploit mitigation | ASR rules | Per-technique mitigation with Microsoft telemetry |
| Kubernetes admission control | Kyverno or OPA Gatekeeper | Policy-as-code, shift-left enforcement |
| Image signature verification | cosign + Kyverno | Keyless signing with OIDC, admission enforcement |

---

## 7. Runtime Security Detection Engineering

The single-event detection rules in §2 (Falco, Tetragon, Tracee) provide foundational alerting. Production environments require compound detection logic that correlates multiple runtime signals across time windows, reduces false positives through contextual enrichment, and bridges the gap between kernel-level telemetry and SIEM-consumable alerts. This section defines multi-event correlation rules, advanced Falco custom rules, Tetragon TracingPolicy patterns for file integrity and network monitoring, and the integration model connecting runtime events to upstream detection pipelines.

### 7.1 Compound Detection Rules

Single-event rules (e.g., "alert on setns") generate excessive noise in environments running legitimate container orchestration. Compound rules chain multiple indicators within time windows to achieve high-confidence detection with low false-positive rates.

#### 7.1.1 Container escape via nsenter with host namespace acquisition

This rule correlates three indicators: a `setns` call from within a container, followed by a mount namespace change to the host root filesystem, followed by process execution in the host PID namespace — all within a 5-second window from the same source container.

**Sigma rule (SIEM-consumable):**
```yaml
title: Container Escape - Namespace Transition to Host
id: a3f8c1d2-7e4b-4a9f-b6c3-2d1e8f9a4b5c
status: experimental
date: 2025/03/15
description: >
  Detects container escape sequence: setns to host namespace followed by
  process execution in host context. Chains basic setns detection (§2.2)
  with host-context execution verification.
references:
  - https://attack.mitre.org/techniques/T1611/
logsource:
  product: tetragon
  category: process_creation
detection:
  phase1_setns:
    event.type: 'PROCESS_KPROBE'
    function_name: '__x64_sys_setns'
    process.docker: 'true'
  phase2_host_exec:
    event.type: 'PROCESS_EXEC'
    process.ns.pid_ns|ne: process.parent.ns.pid_ns
    process.binary|startswith:
      - '/usr/bin/'
      - '/usr/sbin/'
      - '/bin/'
  timeframe: 5s
  condition: phase1_setns | near phase2_host_exec
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1611
falsepositives:
  - Legitimate nsenter usage by kubelet or containerd-shim (excluded by process ancestry check)
```

#### 7.1.2 Fileless malware execution chain (memfd_create + fexecve)

Fileless execution uses `memfd_create` to create an anonymous in-memory file descriptor, writes a payload into it, then executes via `fexecve` or `execveat` with `AT_EMPTY_PATH`. The compound rule correlates the memory file creation with subsequent execution from the same file descriptor, filtering out legitimate users (browsers, audio subsystems).

**Falco compound rule:**
```yaml
- rule: Fileless Execution Chain - memfd to execveat
  desc: >
    Correlates memfd_create with execveat(AT_EMPTY_PATH) from the same
    process within a short window. Builds on basic memfd_create detection
    (§2.2) by requiring the execution step, eliminating false positives
    from legitimate memfd usage (shared memory, JIT).
  condition: >
    (evt.type = execveat and evt.arg.flags contains AT_EMPTY_PATH
     and proc.aname[1] != chrome and proc.aname[1] != firefox
     and proc.aname[1] != pulseaudio and proc.aname[1] != pipewire
     and proc.aname[1] != containerd-shim)
    or
    (evt.type = execve and fd.typechar = 'o' and fd.name startswith '/memfd:')
  output: >
    Fileless execution detected: memfd-backed binary executed
    (proc=%proc.name pid=%proc.pid ppid=%proc.ppid user=%user.name
    container=%container.name pod=%k8s.pod.name
    exe=%proc.exepath fd=%fd.name cmdline=%proc.cmdline)
  priority: CRITICAL
  tags: [T1620, fileless, container]
```

#### 7.1.3 eBPF program loading from unprivileged or unexpected context

The basic rule in §1.5 detects any `bpf(BPF_PROG_LOAD)` call. This compound rule adds context: the loading process is not a known security tool, not running as a service account associated with security infrastructure, and is either inside a container or running from a non-standard path.

**Sigma rule:**
```yaml
title: Suspicious eBPF Program Load - Non-Security Context
id: d7e2f1a3-9c4b-4d8e-a1f5-3b6c7e8d9a0f
status: experimental
date: 2025/03/15
description: >
  eBPF program loaded by process outside known security tooling.
  Correlates bpf() syscall with process identity, container context,
  and binary path to detect offensive eBPF usage (ebpfkit, pamspy,
  eBPF-based rootkits).
logsource:
  product: linux
  category: syscall
detection:
  bpf_load:
    syscall: 'bpf'
    a0: 5  # BPF_PROG_LOAD
  filter_security_tools:
    process.executable|endswith:
      - '/tetragon'
      - '/falco'
      - '/cilium-agent'
      - '/tracee'
      - '/node_exporter'
      - '/bpftrace'
    process.parent.executable|endswith:
      - '/systemd'
      - '/kubelet'
  condition: bpf_load and not filter_security_tools
level: high
tags:
  - attack.persistence
  - attack.defense_evasion
  - attack.t1014
```

#### 7.1.4 Suspicious ptrace attachment for process injection

`ptrace(PTRACE_ATTACH)` or `ptrace(PTRACE_SEIZE)` from a process that is not a debugger and targets a process owned by a different user or running in a different container indicates process injection. This compounds ptrace detection with user context mismatch.

**Falco rule:**
```yaml
- rule: Cross-Context Ptrace Injection
  desc: >
    Detects ptrace attachment where tracer and tracee belong to different
    users or different containers. Legitimate debuggers (gdb, strace,
    lldb) are excluded only when the target is same-user same-container.
  condition: >
    evt.type in (ptrace) and evt.arg.request in (PTRACE_ATTACH, PTRACE_SEIZE)
    and (
      (user.uid != evt.arg.uid)
      or (container.id != host and proc.aname[1] != evt.arg.aname[1])
    )
    and not proc.name in (gdb, strace, ltrace, lldb)
  output: >
    Cross-context ptrace injection (tracer=%proc.name tracer_pid=%proc.pid
    tracer_user=%user.name target_pid=%evt.arg.pid
    container=%container.name pod=%k8s.pod.name)
  priority: CRITICAL
  tags: [T1055.008, process_injection]
```

#### 7.1.5 Kernel module loading outside maintenance window

Kernel module loading (`init_module`, `finit_module`) is expected only during system boot, package updates, or scheduled maintenance. Loading outside these windows with no corresponding package manager activity indicates rootkit installation or BYOVD attack.

**Sigma rule with time constraint:**
```yaml
title: Kernel Module Load Outside Maintenance Window
id: f1a2b3c4-d5e6-4f7a-8b9c-0d1e2f3a4b5c
status: experimental
date: 2025/03/15
description: >
  Kernel module loaded outside defined maintenance windows without
  preceding package manager activity. Correlates module load with
  absence of dpkg/rpm/yum execution in the prior 60 seconds.
logsource:
  product: linux
  category: syscall
detection:
  module_load:
    syscall|contains:
      - 'init_module'
      - 'finit_module'
  maintenance_window:
    # Exclude Tue/Thu 02:00-04:00 UTC maintenance windows
    event.time|re: '.*(Tue|Thu) 0[23]:.*'
  package_manager:
    process.parent.executable|endswith:
      - '/dpkg'
      - '/rpm'
      - '/yum'
      - '/dnf'
      - '/apt'
  condition: module_load and not maintenance_window and not package_manager
level: critical
tags:
  - attack.persistence
  - attack.t1547.006
falsepositives:
  - Legitimate hotpatch or livepatch operations (kpatch, kgraft)
```

#### 7.1.6 Process injection via /proc/pid/mem write

Writing to `/proc/<pid>/mem` allows direct modification of a running process's memory space — a technique used for process hollowing and code injection without ptrace. The compound rule detects `open()` on `/proc/*/mem` with write flags from a process that is not a known debugger.

**Tetragon TracingPolicy:**
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-proc-mem-injection
spec:
  kprobes:
  - call: "security_file_open"
    syscall: false
    args:
    - index: 0
      type: "file"
    - index: 1
      type: "int"
    selectors:
    - matchArgs:
      - index: 0
        operator: "Prefix"
        values:
        - "/proc/"
      - index: 0
        operator: "Postfix"
        values:
        - "/mem"
      matchBinaries:
      - operator: "NotIn"
        values:
        - "/usr/bin/gdb"
        - "/usr/bin/lldb"
        - "/usr/bin/strace"
      matchActions:
      - action: Post
      - action: NotifyEnforcer
        argError: -1  # EPERM
```

#### 7.1.7 Privileged container with host PID namespace

A container running with both `privileged: true` and `hostPID: true` has full access to host processes. This compound detection correlates the Kubernetes audit log (admission of privileged pod with hostPID) with runtime observation of the container accessing host process namespaces.

**Falco rule:**
```yaml
- rule: Privileged Container Accessing Host Processes
  desc: >
    Detects a privileged container with hostPID=true reading /proc entries
    for host PIDs (PID > 1 outside container cgroup). Correlates
    privileged container detection (§2.2) with host process enumeration.
  condition: >
    open_read and container.id != host
    and container.privileged = true
    and fd.name startswith /proc/
    and fd.name regex '/proc/[0-9]+/(status|cmdline|environ|maps|mem)'
    and not k8s.pod.name startswith "kube-"
    and not proc.name in (kubelet, containerd-shim, runc)
  output: >
    Privileged container accessing host /proc (file=%fd.name
    proc=%proc.name container=%container.name pod=%k8s.pod.name
    image=%container.image.repository namespace=%k8s.ns.name)
  priority: CRITICAL
  tags: [T1611, T1057, privileged_container]
```

#### 7.1.8 Suspicious process lineage — shell spawned from web server

A shell process (`bash`, `sh`, `dash`, `zsh`) spawned as a child of a web server process (`nginx`, `apache2`, `httpd`, `node`, `java`) inside a container strongly indicates remote code execution exploitation. This is a process-ancestry detection rule.

**Falco rule:**
```yaml
- rule: Shell Spawned from Web Server in Container
  desc: >
    Web server spawning a shell indicates RCE exploitation. Correlates
    process ancestry with container context for high-confidence alerting.
  condition: >
    spawned_process and container.id != host
    and proc.name in (bash, sh, dash, zsh, ash, csh, ksh)
    and proc.pname in (nginx, apache2, httpd, node, java, python3,
                        ruby, php-fpm, gunicorn, uwsgi, dotnet)
    and not proc.cmdline contains "healthcheck"
  output: >
    Shell spawned from web server (shell=%proc.name parent=%proc.pname
    cmdline=%proc.cmdline container=%container.name pod=%k8s.pod.name
    image=%container.image.repository user=%user.name)
  priority: CRITICAL
  tags: [T1059.004, T1190, web_rce]
```

### 7.2 Advanced Tetragon TracingPolicy for File Integrity Monitoring

Tetragon TracingPolicies can monitor file integrity at the kernel level, providing tamper-evident monitoring that operates below user-space file integrity tools (AIDE, OSSEC) and cannot be bypassed by standard rootkit techniques.

**TracingPolicy for critical file modification detection:**
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: file-integrity-critical-paths
spec:
  kprobes:
  - call: "security_file_open"
    syscall: false
    args:
    - index: 0
      type: "file"
    - index: 1
      type: "int"
    selectors:
    - matchArgs:
      - index: 0
        operator: "Prefix"
        values:
        - "/etc/passwd"
        - "/etc/shadow"
        - "/etc/sudoers"
        - "/etc/pam.d/"
        - "/etc/ssh/sshd_config"
        - "/etc/ld.so.preload"
        - "/etc/crontab"
        - "/etc/systemd/system/"
      - index: 1
        operator: "Mask"
        values:
        - "2"  # O_WRONLY or O_RDWR
      matchActions:
      - action: Post
  - call: "security_inode_rename"
    syscall: false
    args:
    - index: 0
      type: "file"
    - index: 1
      type: "file"
    selectors:
    - matchArgs:
      - index: 1
        operator: "Prefix"
        values:
        - "/etc/passwd"
        - "/etc/shadow"
        - "/etc/sudoers"
      matchActions:
      - action: Post
```

**TracingPolicy for network connection monitoring (egress to non-RFC1918):**
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: monitor-external-connections
spec:
  kprobes:
  - call: "tcp_connect"
    syscall: false
    args:
    - index: 0
      type: "sock"
    selectors:
    - matchArgs:
      - index: 0
        operator: "NotDAddr"
        values:
        - "10.0.0.0/8"
        - "172.16.0.0/12"
        - "192.168.0.0/16"
        - "127.0.0.0/8"
      matchNamespaces:
      - namespace: Pid
        operator: NotIn
        values:
        - "host_pid_ns"
      matchActions:
      - action: Post
```

### 7.3 Correlating Runtime Events with SIEM Alerts

Runtime detection events from Tetragon, Falco, and Tracee become actionable intelligence when correlated with broader SIEM telemetry. The correlation model works bidirectionally: runtime events enrich SIEM alerts with kernel-level context, and SIEM events (authentication anomalies, threat intelligence matches) trigger focused runtime monitoring.

**Correlation pattern: runtime event triggers SIEM enrichment**

When Tetragon detects a `setns` call from a container (§7.1.1), the event is forwarded to the SIEM pipeline via gRPC export. The SIEM correlates this event with:
1. Kubernetes audit logs — was there a corresponding `kubectl exec` API call to this pod?
2. Authentication logs — who authenticated to the cluster within the preceding 15 minutes?
3. Image scanning results — does the running image have known container escape CVEs?
4. Network flow data — has this pod established unexpected external connections?

If the `setns` event has no corresponding `kubectl exec` and the pod's image contains CVE-2024-21626 (runc working directory escape), the correlation engine escalates to CRITICAL with automated pod quarantine.

**Correlation pattern: SIEM alert triggers runtime focus**

When the SIEM detects impossible-travel authentication to a Kubernetes cluster, it pushes a dynamic Tetragon TracingPolicy via the Kubernetes API that enables enhanced monitoring for all pods launched by the suspicious service account — full syscall tracing, DNS query logging, and file access audit. This targeted instrumentation avoids the performance overhead of blanket monitoring.

```bash
# Dynamic TracingPolicy deployment triggered by SIEM alert
kubectl apply -f - <<'EOF'
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: siem-triggered-enhanced-monitoring
  labels:
    source: siem-correlation
    incident-id: "INC-2025-0312"
spec:
  kprobes:
  - call: "security_bprm_check"
    syscall: false
    args:
    - index: 0
      type: "linux_binprm"
    selectors:
    - matchNamespaces:
      - namespace: Pod
        operator: In
        values:
        - "suspicious-namespace"
      matchActions:
      - action: Post
  - call: "__x64_sys_connect"
    syscall: true
    args:
    - index: 0
      type: "int"
    - index: 1
      type: "sockaddr"
    selectors:
    - matchNamespaces:
      - namespace: Pod
        operator: In
        values:
        - "suspicious-namespace"
      matchActions:
      - action: Post
EOF
```

---

## 8. Zero Trust Implementation Deep Dive

Section 4 established zero trust fundamentals (NIST SP 800-207 architecture, microsegmentation, identity-centric access). This section addresses advanced implementation patterns: identity-based microsegmentation with service mesh integration, device trust enforcement at runtime, continuous verification mechanics, zero trust retrofit for legacy systems, and BeyondCorp-style access proxy architecture.

### 8.1 Identity-Based Microsegmentation with Service Mesh

Beyond the L3/L4 network policies in §4.3, identity-based microsegmentation operates at L7 using cryptographic workload identities (SPIFFE SVIDs from §4.2) to make authorization decisions based on authenticated service identity rather than IP addresses.

**Cilium cluster-mesh identity policy (cross-cluster microsegmentation):**
```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: cross-cluster-payment-policy
  namespace: payments
spec:
  endpointSelector:
    matchLabels:
      app: payment-gateway
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: order-service
        io.cilium.k8s.policy.cluster: "cluster-us-east"
    - matchLabels:
        app: order-service
        io.cilium.k8s.policy.cluster: "cluster-eu-west"
    toPorts:
    - ports:
      - port: "8443"
        protocol: TCP
      rules:
        http:
        - method: "POST"
          path: "/api/v1/process-payment"
          headers:
          - 'X-Request-ID: [a-f0-9-]{36}'
  egress:
  - toFQDNs:
    - matchName: "api.stripe.com"
    - matchName: "api.adyen.com"
    toPorts:
    - ports:
      - port: "443"
        protocol: TCP
```

**Istio RequestAuthentication with JWT validation (L7 identity enforcement):**
```yaml
apiVersion: security.istio.io/v1
kind: RequestAuthentication
metadata:
  name: jwt-auth-payment-api
  namespace: payments
spec:
  selector:
    matchLabels:
      app: payment-gateway
  jwtRules:
  - issuer: "https://auth.corp.example.com"
    jwksUri: "https://auth.corp.example.com/.well-known/jwks.json"
    audiences:
    - "payment-gateway.payments.svc.cluster.local"
    forwardOriginalToken: true
    outputPayloadToHeader: "x-jwt-payload"
---
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: payment-api-authz
  namespace: payments
spec:
  selector:
    matchLabels:
      app: payment-gateway
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
        - "cluster.local/ns/orders/sa/order-service"
        - "cluster.local/ns/refunds/sa/refund-service"
    to:
    - operation:
        methods: ["POST"]
        paths: ["/api/v1/process-payment", "/api/v1/refund"]
    when:
    - key: request.auth.claims[iss]
      values: ["https://auth.corp.example.com"]
    - key: request.auth.claims[scope]
      values: ["payment:write"]
```

### 8.2 Device Trust: Runtime Verification

Boot-time attestation (§5.2) establishes initial device trust. Runtime device trust requires continuous verification that the device remains in a compliant state throughout the session.

**Certificate-based device attestation workflow:**

1. Device generates a key pair bound to the TPM's Endorsement Key hierarchy during enrollment
2. MDM issues a device certificate signed by the organization's device CA, containing the TPM-bound public key and device identifiers
3. At authentication time, the identity-aware proxy challenges the device to prove possession of the TPM-bound private key via TLS client certificate authentication
4. The policy engine validates the certificate chain, checks the device certificate's serial number against a revocation list, and queries the MDM API for current compliance status (patch level, disk encryption, EDR agent running)

**TPM-based continuous health check (runtime verification script):**
```bash
#!/usr/bin/env bash
# Runtime device health attestation — runs periodically via systemd timer
# Reports to zero trust policy engine for continuous session evaluation

set -euo pipefail

ATTESTATION_ENDPOINT="https://zt-policy.corp.example.com/v1/device/attest"
DEVICE_ID=$(cat /etc/machine-id)

# Collect TPM PCR values (boot integrity)
PCR_VALUES=$(tpm2_pcrread sha256:0,1,4,7,8,14 -o /tmp/pcr_quote.bin 2>/dev/null)

# Generate TPM quote (signed by AIK)
tpm2_quote \
  --key-context /opt/attestation/aik.ctx \
  --pcr-list sha256:0,1,4,7,8,14 \
  --message /tmp/quote_msg.bin \
  --signature /tmp/quote_sig.bin \
  --qualification "$(date -u +%s)" 2>/dev/null

# Collect runtime health signals
HEALTH_PAYLOAD=$(jq -n \
  --arg device_id "$DEVICE_ID" \
  --arg kernel "$(uname -r)" \
  --arg secureboot "$(mokutil --sb-state 2>/dev/null | grep -c 'enabled')" \
  --arg edr_running "$(systemctl is-active falcon-sensor crowdstrike-agent 2>/dev/null || echo 'inactive')" \
  --arg disk_encrypted "$(lsblk -o NAME,TYPE,FSTYPE | grep -c 'crypt')" \
  --arg fw_active "$(systemctl is-active firewalld nftables ufw 2>/dev/null | head -1)" \
  --arg ima_violations "$(cat /sys/kernel/security/integrity/ima/violations 2>/dev/null || echo '-1')" \
  '{device_id: $device_id, kernel: $kernel, secure_boot: ($secureboot | tonumber > 0),
    edr_active: ($edr_running == "active"), disk_encrypted: ($disk_encrypted | tonumber > 0),
    firewall_active: ($fw_active == "active"), ima_violations: ($ima_violations | tonumber)}')

# Submit attestation with TPM quote
curl -s -X POST "$ATTESTATION_ENDPOINT" \
  -H "Content-Type: multipart/form-data" \
  -F "health=$HEALTH_PAYLOAD" \
  -F "quote=@/tmp/quote_msg.bin" \
  -F "signature=@/tmp/quote_sig.bin" \
  --cert /opt/attestation/device.crt \
  --key /opt/attestation/device.key \
  --cacert /opt/attestation/corp-ca.crt

rm -f /tmp/pcr_quote.bin /tmp/quote_msg.bin /tmp/quote_sig.bin
```

### 8.3 Continuous Verification and Session Risk Scoring

Zero trust mandates continuous verification — not just at authentication time. Session risk scoring evaluates ongoing signals and triggers re-authentication or session termination when risk exceeds thresholds.

**Re-authentication triggers:**

| Signal | Threshold | Action |
|--------|-----------|--------|
| IP address change (different /24) | Immediate | Step-up MFA required |
| Device posture degradation (EDR stopped) | Within 60 seconds | Session suspended, device remediation required |
| Impossible travel detected | Immediate | Session terminated, incident created |
| Sensitive resource access | Per-access | Step-up authentication (FIDO2) |
| Session age exceeds policy | Configurable (1-8 hours) | Silent re-authentication or MFA prompt |
| Behavioral anomaly (UEBA score > threshold) | Risk score > 80 | Session restricted to read-only |
| Threat intelligence match (IP/domain) | Immediate | Session terminated, SOC alert |

**Session risk scoring model:**

```
risk_score = Σ(signal_weight × signal_value) / Σ(signal_weight)

Signals:
  auth_strength:     weight=30, value=0 (FIDO2) | 0.3 (TOTP) | 0.7 (SMS) | 1.0 (password-only)
  device_compliance: weight=25, value=0 (compliant) | 0.5 (partial) | 1.0 (non-compliant)
  network_risk:      weight=15, value=0 (corporate) | 0.3 (known VPN) | 0.7 (public) | 1.0 (Tor/proxy)
  behavioral_score:  weight=20, value=[0.0-1.0] from UEBA engine
  session_age:       weight=10, value=min(hours_since_auth / max_session_hours, 1.0)

Thresholds:
  risk_score < 0.3  → full access
  risk_score 0.3-0.6 → restricted access (read-only on sensitive resources)
  risk_score 0.6-0.8 → step-up authentication required
  risk_score > 0.8   → session terminated
```

### 8.4 Zero Trust for Legacy Systems

Legacy applications that cannot natively integrate with zero trust identity providers require proxy-based enforcement and network-level segmentation as compensating controls.

**Proxy-based enforcement architecture:**

```
Legacy App (no OIDC/SAML support, listens on :8080)
   ↑
Identity-Aware Reverse Proxy (authenticates users, injects identity headers)
   ↑
Zero Trust Gateway (TLS termination, device posture check, policy evaluation)
   ↑
User (authenticates via SSO, device attested)
```

**Nginx-based identity-aware proxy for legacy applications:**
```nginx
# /etc/nginx/conf.d/legacy-app-zt.conf
# Fronts a legacy app with zero trust authentication via OAuth2 Proxy

upstream legacy_app {
    server 127.0.0.1:8080;
}

upstream oauth2_proxy {
    server 127.0.0.1:4180;
}

server {
    listen 443 ssl;
    server_name legacy.corp.example.com;

    ssl_certificate     /etc/tls/legacy-app.crt;
    ssl_certificate_key /etc/tls/legacy-app.key;
    ssl_client_certificate /etc/tls/corp-device-ca.crt;
    ssl_verify_client on;  # Enforce device certificate

    # OAuth2 Proxy handles authentication
    location /oauth2/ {
        proxy_pass http://oauth2_proxy;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        # Require authentication via OAuth2 Proxy
        auth_request /oauth2/auth;
        error_page 401 = /oauth2/sign_in;

        # Pass authenticated identity to legacy app
        auth_request_set $user  $upstream_http_x_auth_request_user;
        auth_request_set $email $upstream_http_x_auth_request_email;
        auth_request_set $groups $upstream_http_x_auth_request_groups;

        proxy_set_header X-Authenticated-User $user;
        proxy_set_header X-Authenticated-Email $email;
        proxy_set_header X-Authenticated-Groups $groups;
        proxy_set_header X-Device-CN $ssl_client_s_dn_cn;

        proxy_pass http://legacy_app;
    }
}
```

**Network-level segmentation for non-proxiable legacy systems:**

For legacy systems that cannot be fronted by a proxy (mainframes, proprietary protocols, SCADA/ICS), enforce zero trust through network-level controls: place the legacy system in an isolated VLAN, require VPN or SDP tunnel with identity + device posture verification to reach the VLAN, and log all access at the network boundary.

```bash
# iptables-based micro-perimeter for legacy mainframe (compensating control)
# Only permit access from the SDP gateway's IP after identity verification
iptables -A INPUT -s 10.250.1.5/32 -p tcp --dport 3270 -j ACCEPT  # SDP gateway
iptables -A INPUT -s 10.250.1.6/32 -p tcp --dport 3270 -j ACCEPT  # Backup SDP
iptables -A INPUT -p tcp --dport 3270 -j LOG --log-prefix "LEGACY-DENIED: "
iptables -A INPUT -p tcp --dport 3270 -j DROP
```

### 8.5 BeyondCorp Implementation Patterns

The BeyondCorp model (introduced in §4.10) requires specific architectural components for production deployment. The access proxy is the critical enforcement point — all application access flows through it, enabling centralized authentication, authorization, and audit.

**Access proxy architecture components:**

| Component | Function | Implementation |
|-----------|----------|----------------|
| Access Proxy (PEP) | TLS termination, authentication enforcement, policy evaluation | Pomerium, ORY Oathkeeper, Cloudflare Access, Google IAP |
| Identity Provider | User authentication, MFA, session management | Okta, Azure AD, Google Workspace, Keycloak |
| Device Trust Service | Collect and evaluate device posture signals | Kolide, CrowdStrike Falcon ZTA, Google Endpoint Verification |
| Policy Engine | Evaluate contextual access decisions | OPA (Rego), Cedar (AWS Verified Access), custom engines |
| Session Store | Manage short-lived session tokens with continuous evaluation | Redis with TTL, signed JWTs with short expiry |

**Context-aware access decision flow:**

```
1. User requests https://app.corp.example.com
2. Access proxy redirects to IdP for authentication (if no valid session)
3. IdP authenticates user (FIDO2 + SSO)
4. Access proxy queries Device Trust Service:
   - Is device certificate valid and unrevoked?
   - Is EDR agent running with current signatures?
   - Is OS patch level within 14-day SLA?
   - Is disk encryption enabled?
5. Access proxy evaluates OPA policy:
   - User role permits access to this application?
   - Device trust score exceeds minimum threshold?
   - Request originates from acceptable network?
   - Time-of-day and geo-location within bounds?
6. If all checks pass → issue short-lived session cookie (15-minute sliding window)
7. Continuous: re-evaluate device posture every 5 minutes, revoke on degradation
```

---

## 9. Runtime Incident Response

Runtime incident response in containerized and serverless environments demands different forensic workflows than traditional host-based IR. Containers are ephemeral — evidence vanishes when pods are deleted. eBPF enables live forensics during active attacks without service disruption. Kubernetes provides both challenges (orchestrator-level complexity) and advantages (declarative state, audit logs, network policy isolation).

### 9.1 Container Forensics Workflow

#### 9.1.1 Image layer analysis

Container images consist of layered filesystems. Forensic analysis examines each layer to identify modifications introduced by the attacker versus the base image.

```bash
# Export running container filesystem for analysis
docker export <container_id> -o /forensics/container_fs.tar

# Examine image layer history (detect added/modified layers)
docker history --no-trunc <image>:<tag>

# Diff running container against its image (find runtime modifications)
docker diff <container_id>
# Output: A = added, C = changed, D = deleted
# Example:
#   C /etc/passwd
#   A /tmp/.hidden/backdoor
#   C /usr/lib/x86_64-linux-gnu/libpam.so.0

# Extract specific layer for analysis
skopeo copy docker://<image>:<tag> dir:/forensics/image_layers
# Each layer is a separate tar in the blobs directory

# Compare layer hashes against known-good baseline
crane manifest <image>:<tag> | jq '.layers[].digest'
```

#### 9.1.2 Runtime artifact collection

Collect volatile evidence before the container is terminated. Priority order: process state, network connections, file modifications, environment variables, mounted secrets.

```bash
# Snapshot process tree inside container
kubectl exec -n <namespace> <pod> -c <container> -- ps auxf > /forensics/ps_tree.txt

# Capture network connections
kubectl exec -n <namespace> <pod> -c <container> -- cat /proc/net/tcp > /forensics/net_tcp.txt
kubectl exec -n <namespace> <pod> -c <container> -- cat /proc/net/tcp6 > /forensics/net_tcp6.txt

# Capture environment (may contain injected credentials)
kubectl exec -n <namespace> <pod> -c <container> -- env > /forensics/env_vars.txt

# Copy modified files from container
kubectl cp <namespace>/<pod>:/tmp/.hidden/ /forensics/suspicious_files/ -c <container>

# Capture container's /proc filesystem entries
for f in mounts maps cmdline status; do
  kubectl exec -n <namespace> <pod> -c <container> -- \
    cat /proc/1/$f > /forensics/proc_1_${f}.txt
done
```

#### 9.1.3 Ephemeral container evidence preservation

Kubernetes ephemeral debug containers (since v1.25 GA) attach to a running pod without restarting it, enabling forensic tool injection into a live environment.

```bash
# Attach forensic toolkit as ephemeral container
kubectl debug -n <namespace> <pod> \
  --image=registry.internal/forensics-toolkit:latest \
  --target=<container> \
  --share-processes \
  -- sleep 3600

# From inside the ephemeral container, access target's filesystem
# Target container's root filesystem is at /proc/<target_pid>/root/
ls /proc/1/root/tmp/
cat /proc/1/root/etc/passwd

# Capture memory dump of target process
cp /proc/<target_pid>/maps /forensics/
gcore -o /forensics/core_dump <target_pid>

# Snapshot container to preserve evidence before deletion
# (Requires container runtime access on the node)
crictl checkpoint --export=/forensics/checkpoint.tar <container_id>
```

### 9.2 eBPF-Based Live Forensics

eBPF enables real-time investigation of active attacks without shutting down workloads — critical when the compromised service handles production traffic and downtime has business impact.

**Live syscall tracing of compromised container:**
```bash
# Trace all syscalls from a specific container using bpftrace
# Identify the container's cgroup path first
CGROUP_PATH=$(kubectl get pod <pod> -n <namespace> -o jsonpath='{.status.containerStatuses[0].containerID}' | sed 's|containerd://||')

# Trace execve calls from the container's cgroup
bpftrace -e '
tracepoint:syscalls:sys_enter_execve
/cgroup == cgroupid("/sys/fs/cgroup/system.slice/containerd.service/kubepods/pod-xxx")/ {
    printf("exec: pid=%d comm=%s args=%s\n",
           pid, comm, str(args->filename));
}

tracepoint:syscalls:sys_enter_connect
/cgroup == cgroupid("/sys/fs/cgroup/system.slice/containerd.service/kubepods/pod-xxx")/ {
    $sa = (struct sockaddr_in *)args->uservaddr;
    printf("connect: pid=%d comm=%s addr=%s port=%d\n",
           pid, comm,
           ntop(AF_INET, $sa->sin_addr.s_addr),
           ntohs($sa->sin_port));
}
'
```

**Tetragon real-time forensic policy (full visibility on targeted pod):**
```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: forensic-full-trace
  labels:
    incident: "INC-2025-0415"
spec:
  kprobes:
  - call: "security_bprm_check"
    syscall: false
    args:
    - index: 0
      type: "linux_binprm"
    selectors:
    - matchNamespaces:
      - namespace: Pod
        operator: In
        values:
        - "compromised-namespace"
      matchActions:
      - action: Post
  - call: "security_file_open"
    syscall: false
    args:
    - index: 0
      type: "file"
    - index: 1
      type: "int"
    selectors:
    - matchNamespaces:
      - namespace: Pod
        operator: In
        values:
        - "compromised-namespace"
      matchActions:
      - action: Post
  - call: "tcp_connect"
    syscall: false
    args:
    - index: 0
      type: "sock"
    selectors:
    - matchNamespaces:
      - namespace: Pod
        operator: In
        values:
        - "compromised-namespace"
      matchActions:
      - action: Post
```

### 9.3 Kubernetes Incident Response

#### 9.3.1 Pod quarantine via network policy

Isolate a compromised pod while preserving it for forensic analysis. The quarantine policy denies all ingress and egress except to a designated forensic collection endpoint.

```yaml
# Quarantine network policy — isolate compromised pod
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: quarantine-pod
  namespace: production
spec:
  podSelector:
    matchLabels:
      security.kubernetes.io/quarantine: "true"
  policyTypes:
  - Ingress
  - Egress
  ingress: []  # Deny all ingress
  egress:
  # Allow only forensic collection endpoint
  - to:
    - ipBlock:
        cidr: 10.250.100.0/24  # Forensic VLAN
    ports:
    - protocol: TCP
      port: 9443  # Forensic artifact receiver
  # Allow DNS for log shipping
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

```bash
# Label the compromised pod for quarantine
kubectl label pod <pod-name> -n production security.kubernetes.io/quarantine=true

# Verify network isolation
kubectl exec -n production <pod-name> -- curl -s --connect-timeout 3 https://external.com && \
  echo "QUARANTINE FAILED" || echo "Quarantine effective"

# Prevent pod deletion by adding finalizer
kubectl patch pod <pod-name> -n production --type merge \
  -p '{"metadata":{"finalizers":["forensics.corp.example.com/evidence-collected"]}}'
```

#### 9.3.2 Kubernetes audit log analysis for incident timeline

```bash
# Extract audit events for the compromised namespace in the attack window
kubectl logs -n kube-system -l component=kube-apiserver --since=2h | \
  jq 'select(.objectRef.namespace == "production") |
      select(.verb | test("create|update|patch|delete")) |
      {timestamp: .requestReceivedTimestamp,
       user: .user.username,
       verb: .verb,
       resource: "\(.objectRef.resource)/\(.objectRef.name)",
       sourceIP: .sourceIPs[0]}' | \
  sort_by(.timestamp)

# Identify service account token usage (potential credential theft)
kubectl logs -n kube-system -l component=kube-apiserver --since=2h | \
  jq 'select(.user.username | startswith("system:serviceaccount:production:")) |
      {timestamp: .requestReceivedTimestamp,
       sa: .user.username,
       verb: .verb,
       resource: .objectRef.resource,
       sourceIP: .sourceIPs[0]}' | \
  sort_by(.timestamp)
```

### 9.4 Serverless Incident Response

Serverless functions present unique IR challenges: no persistent filesystem, no SSH access, execution logs may be the only evidence, and function versions can be silently replaced.

**AWS Lambda IR workflow:**
```bash
# Identify all versions and aliases of the compromised function
aws lambda list-versions-by-function --function-name compromised-func \
  --query 'Versions[].{Version:Version,SHA:CodeSha256,Modified:LastModified}' \
  --output table

# Download the function code for each version (compare for tampering)
aws lambda get-function --function-name compromised-func --qualifier 5 \
  --query 'Code.Location' --output text | xargs curl -o /forensics/func_v5.zip

# Extract execution logs for the attack window
aws logs filter-log-events \
  --log-group-name /aws/lambda/compromised-func \
  --start-time $(date -d '2025-03-12T14:00:00Z' +%s000) \
  --end-time $(date -d '2025-03-12T16:00:00Z' +%s000) \
  --filter-pattern '?ERROR ?Exception ?timeout ?denied' \
  --output json > /forensics/lambda_logs.json

# Check CloudTrail for function modifications
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=compromised-func \
  --start-time 2025-03-12T00:00:00Z \
  --end-time 2025-03-12T23:59:59Z \
  --output json > /forensics/cloudtrail_lambda.json

# Rollback to known-good version
aws lambda update-alias --function-name compromised-func \
  --name production --function-version 4

# Preserve the compromised version (prevent deletion)
aws lambda put-function-concurrency \
  --function-name "compromised-func:5" \
  --reserved-concurrent-executions 0  # Prevent invocation
```

---

## 10. Emerging Runtime Security

### 10.1 eBPF Security Concerns and Evolution

eBPF's expanding kernel surface area introduces its own security risks. The BPF verifier — the primary safety mechanism — has been a recurring source of privilege escalation vulnerabilities, and the increasing complexity of eBPF programs strains the verifier's analysis capabilities.

**BPF verifier bypass CVEs (pattern analysis):**

| CVE | Year | Mechanism | Impact |
|-----|------|-----------|--------|
| CVE-2021-3490 | 2021 | ALU32 bounds tracking error — bitwise operations on 32-bit sub-registers allowed crafting out-of-bounds pointers | Arbitrary kernel R/W, LPE |
| CVE-2021-31440 | 2021 | Bounds propagation error in verifier's abstract state — incorrect register value ranges after conditional branches | Arbitrary kernel R/W, LPE |
| CVE-2022-23222 | 2022 | Pointer leak via BTF — verifier failed to track pointer types through certain helper return values | Kernel pointer disclosure, LPE |
| CVE-2023-2163 | 2023 | Verifier state pruning — incorrect pruning of explored states led to missed safety violations | Arbitrary kernel R/W, LPE |
| CVE-2024-2193 | 2024 | GhostRace — speculative data race conditions in BPF verifier paths | Speculative type confusion |

**Mitigation evolution:**
- Kernel 5.16+: `kernel.unprivileged_bpf_disabled=1` by default
- Kernel 5.19+: fine-grained BPF token delegation (`BPF_TOKEN_CREATE`) replaces coarse `CAP_BPF`
- Kernel 6.2+: BPF arena for safe shared memory between eBPF programs and user space
- Kernel 6.6+: BPF exceptions (`bpf_throw()`) for safer error handling in eBPF programs

**Malicious eBPF program detection framework:**
```bash
# Comprehensive eBPF program audit script
# Run periodically or on-demand during incident response

echo "=== Loaded BPF Programs ==="
bpftool prog list --json | jq -r '.[] |
  "\(.id) \(.type) \(.name // "unnamed") loaded_at=\(.loaded_at) uid=\(.uid)"'

echo "=== Programs attached to LSM hooks ==="
bpftool prog list --json | jq -r '.[] | select(.type == "lsm") |
  "\(.id) \(.name) tag=\(.tag)"'

echo "=== Programs with write access to kernel memory ==="
bpftool prog list --json | jq -r '.[] |
  select(.type | test("kprobe|tracepoint|raw_tracepoint|lsm")) |
  "\(.id) \(.type) \(.name // "unnamed")"'

echo "=== BPF maps writable by non-security processes ==="
bpftool map list --json | jq -r '.[] |
  "\(.id) \(.type) \(.name // "unnamed") flags=\(.map_flags)"'

echo "=== Pinned BPF objects ==="
find /sys/fs/bpf/ -type f -exec echo "pinned: {}" \;

echo "=== BPF program load events (last hour) ==="
ausearch -k bpf_load --start recent -i 2>/dev/null || \
  journalctl -t audit --since "1 hour ago" --grep "bpf" 2>/dev/null
```

### 10.2 WebAssembly Runtime Security

WebAssembly (Wasm) is emerging as a runtime for server-side workloads, edge computing, and plugin systems. Wasm's sandboxing model provides security properties distinct from containers.

**Wasm sandbox security model:**

| Property | Container (cgroup/namespace) | Wasm (linear memory sandbox) |
|----------|------------------------------|------------------------------|
| Memory isolation | Kernel-enforced namespace separation | Linear memory bounds checking by runtime |
| Syscall access | Full Linux ABI unless restricted by seccomp | No direct syscall access — only WASI capabilities |
| Filesystem access | Bind mounts, overlay filesystem | Explicit directory pre-opens only (capability-based) |
| Network access | Full stack unless restricted by netpol | WASI socket capability must be explicitly granted |
| Startup time | 100-500ms (image pull + init) | 1-10ms (pre-compiled module instantiation) |
| Attack surface | Kernel syscall interface (~400 syscalls) | Wasm runtime API (< 50 WASI functions) |
| Escape complexity | Kernel vulnerability required (high but proven) | Runtime memory safety bug required (Wasm is memory-safe by design) |

**WASI (WebAssembly System Interface) security model:**

WASI implements capability-based security — a Wasm module has zero host access by default and must be explicitly granted capabilities at instantiation time:

```bash
# Run Wasm module with minimal WASI capabilities
wasmtime run \
  --dir /data/input::readonly \
  --dir /data/output \
  --env DATABASE_URL=postgres://... \
  --tcplisten 127.0.0.1:8080 \
  app.wasm

# No filesystem access beyond /data/input (ro) and /data/output (rw)
# No network access beyond listening on 127.0.0.1:8080
# No process spawning, no signal handling, no raw sockets
```

**Known Wasm runtime vulnerabilities:**
- Wasmtime CVE-2022-24791: use-after-free in `externref` handling allowed guest code to access freed host memory
- Wasmtime CVE-2023-26489: miscompilation in Cranelift allowed Wasm guest to read/write outside linear memory bounds
- Wasmer CVE-2024-38356: SIMD compilation bug in Singlepass compiler allowed out-of-bounds memory access

These CVEs demonstrate that Wasm's theoretical memory safety depends on the correctness of the runtime implementation — the compiler backend is the actual trust boundary.

### 10.3 Confidential Computing Runtime Attestation

Section 5.3 covered confidential computing hardware architectures (AMD SEV-SNP, Intel TDX, ARM CCA). This section addresses the runtime attestation workflows that verify workload integrity within TEEs.

**Runtime attestation workflow for confidential containers:**

```
1. Workload image is measured (hash of all layers) before loading into TEE
2. TEE hardware generates an attestation report:
   - Platform identity (CPU model, firmware version, microcode)
   - TCB (Trusted Computing Base) version
   - Measurement of loaded workload
   - Hardware-signed using platform attestation key
3. Attestation report is sent to a remote attestation service (Intel Trust Authority,
   AMD SEV attestation service, or Confidential Containers KBS)
4. Remote service validates:
   - Signature chain traces to hardware vendor root of trust
   - TCB version is current (no known vulnerabilities in firmware)
   - Workload measurement matches expected image hash
5. On success: attestation service releases encryption keys / secrets to the TEE
6. Workload decrypts sensitive data and begins processing
```

**Confidential Containers on Kubernetes (CoCo):**
```yaml
# Kubernetes RuntimeClass for confidential containers
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata-cc
handler: kata-cc
overhead:
  podFixed:
    memory: "256Mi"
    cpu: "250m"
scheduling:
  nodeSelector:
    cc.kubernetes.io/tdx-enabled: "true"
---
# Pod using confidential computing runtime
apiVersion: v1
kind: Pod
metadata:
  name: confidential-workload
  annotations:
    io.katacontainers.config.hypervisor.default_memory: "4096"
spec:
  runtimeClassName: kata-cc
  containers:
  - name: sensitive-processor
    image: registry.internal/sensitive-app:v1.2.3
    resources:
      limits:
        memory: "2Gi"
        cpu: "2"
```

### 10.4 Runtime Application Self-Protection (RASP)

RASP instruments the application runtime to detect and block attacks from within the application process itself. Unlike network-level WAFs (which inspect HTTP traffic externally) or eBPF-based monitors (which observe syscalls), RASP operates at the application layer with full visibility into application logic, data flow, and execution context.

**RASP vs. adjacent runtime controls:**

| Dimension | WAF | eBPF Monitor | RASP |
|-----------|-----|-------------|------|
| Visibility layer | HTTP request/response | Kernel syscalls | Application code paths |
| Context awareness | URL, headers, body | Process, file, network | SQL queries, deserialization, ORM calls |
| SQLi detection | Regex/signature on HTTP params | Detects unusual DB socket writes | Sees actual SQL query with tainted input markers |
| Deserialization attacks | Limited (payload in body) | Detects spawned processes | Intercepts deserialize() call with payload |
| Performance overhead | < 1ms per request (network proxy) | < 5% CPU (kernel) | 5-15% CPU (instrumentation, JIT) |
| Deployment | Network appliance/sidecar | DaemonSet, host agent | In-app agent, library, or JVM/CLR agent |
| False positive rate | High (no application context) | Medium (no app semantics) | Low (full execution context) |

**RASP tradeoffs:**
- **Overhead:** JVM-based RASP (Contrast Security, Sqreen/Datadog ASM) adds 5-15% latency due to bytecode instrumentation. This is acceptable for web applications but prohibitive for latency-sensitive microservices.
- **Language coverage:** RASP agents are language-specific (Java, .NET, Python, Node.js, Ruby, Go). Polyglot environments require multiple agents with separate policy configurations.
- **Maintenance burden:** RASP agents must be updated with the application runtime. A JVM upgrade may break the RASP agent's bytecode instrumentation. Pin RASP agent versions to tested runtime versions.
- **Recommended approach:** Use RASP as a defense-in-depth layer alongside eBPF monitoring and network-level WAF — not as a replacement for either.

### 10.5 Supply Chain Runtime Verification

Build-time supply chain controls (§4.7) verify that images are signed and provenance is documented. Runtime supply chain verification continuously validates that running workloads match their attested build artifacts and that no drift has occurred.

**In-toto layout verification at runtime:**

```bash
# Verify in-toto supply chain layout before workload admission
# Integrated with Kubernetes admission webhook

in-toto-verify \
  --layout layout.json \
  --layout-keys alice.pub bob.pub \
  --link-dir /var/attestations/links/

# Layout defines required steps:
# 1. Source code review (signed by alice)
# 2. Build (signed by CI system)
# 3. Test (signed by CI system)
# 4. Security scan (signed by scanner)
# 5. Sign (signed by bob)
# All steps must have valid signatures; any gap blocks deployment
```

**SLSA runtime enforcement with Kyverno:**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-slsa-l3-provenance
spec:
  validationFailureAction: Enforce
  background: false
  rules:
  - name: verify-slsa-provenance
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "registry.internal/*"
      attestors:
      - count: 1
        entries:
        - keyless:
            issuer: "https://token.actions.githubusercontent.com"
            subject: "https://github.com/org/repo/.github/workflows/*"
      attestations:
      - type: "https://slsa.dev/provenance/v1"
        conditions:
        - all:
          - key: "{{ buildDefinition.buildType }}"
            operator: Equals
            value: "https://slsa-framework.github.io/github-actions-buildtypes/workflow/v1"
          - key: "{{ runDetails.builder.id }}"
            operator: Equals
            value: "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@refs/tags/v2.0.0"
```

**Runtime drift detection — continuous image-to-container comparison:**

```bash
# Compare running container's filesystem against its source image
# Detect post-deployment modifications indicating compromise

CONTAINER_ID=$(crictl ps --name app -q)
IMAGE_ID=$(crictl inspect "$CONTAINER_ID" | jq -r '.info.config.image.image')

# Create diff of runtime filesystem vs image
crictl inspect "$CONTAINER_ID" | \
  jq -r '.info.runtimeSpec.root.path' | \
  xargs -I{} diff -rq {} /var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/*/fs/ \
  2>/dev/null | grep -E "^(Only in|Files .* differ)" | \
  grep -v -E '(\.pid$|\.sock$|\.log$)' > /tmp/drift_report.txt

if [ -s /tmp/drift_report.txt ]; then
  echo "[ALERT] Runtime drift detected in container $CONTAINER_ID"
  cat /tmp/drift_report.txt
fi
```

---

## Cross-References

- **Domain 2 Chapter 2A** — ELF binary internals — the formats eBPF tools inspect during execution monitoring
- **Domain 2 Chapter 2C** — Linux capabilities, namespaces, and LSMs — the kernel security primitives eBPF LSM programs hook into
- **Domain 11 Chapter 11B** — EDR evasion at the syscall level — evasion techniques that eBPF kernel-level monitoring detects where user-space hooks fail
- **Domain 14 Chapter 14A** — Active Directory attack paths — identity attacks that zero trust architecture mitigates
- **Domain 27 Chapter 27A** — EDR architecture — complementary endpoint detection alongside eBPF monitoring
- **Domain 29 Chapter 29A** — Ransomware kill chain — the attack workflow zero trust microsegmentation interrupts
- **Domain 30 Chapter 30A** — C2 framework detection — network-layer C2 indicators XDP and Cilium can block
- **Domain 30 Chapter 30B** — Credential theft mechanics — LSASS access and token manipulation eBPF LSM hooks can enforce
- **Domain 31 Chapter 31A** — SIEM/SOAR pipeline design — infrastructure consuming eBPF, auditd, and zero trust telemetry
- **Domain 7 Chapter 7A** — Container security fundamentals — base container hardening that runtime detection (§7) monitors for drift
- **Domain 13 Chapter 13A** — Incident response lifecycle — traditional IR framework that §9 adapts for container and serverless environments
- **Domain 15 Chapter 15A** — Digital forensics — forensic methodology that §9.1 applies to ephemeral container evidence
- **Domain 28 Chapter 28A** — Cloud security architecture — cloud-native zero trust patterns that §8 implements at the workload level
