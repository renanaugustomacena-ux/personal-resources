---
corso: "SWE Masterclass"
fase: "5 — DevOps & Cloud Native"
modulo: "5.2"
titolo: "Kubernetes Architecture Deep Dive"
versione: "Kubernetes 1.31–1.32, Gateway API 1.2, containerd 1.7.x"
livello: "Advanced"
prerequisiti:
  - "Container fundamentals (namespaces, cgroups, OCI images) — Module 5.1"
  - "Linux networking (iptables/nftables, DNS, TCP/IP)"
  - "YAML fluency and basic REST API concepts"
  - "Experience deploying at least one containerised application"
obiettivi:
  - "Trace a Pod creation from kubectl apply through API Server, etcd, Scheduler, and kubelet"
  - "Deploy a production-grade workload with liveness/readiness/startup probes, resource requests/limits, and PodDisruptionBudgets"
  - "Debug CrashLoopBackOff, ImagePullBackOff, and scheduling failures systematically"
  - "Design RBAC policies and NetworkPolicies that enforce least-privilege per namespace"
  - "Evaluate Gateway API vs classic Ingress and configure TLS-terminated HTTP routing"
tag: [kubernetes, k8s, control-plane, etcd, scheduler, cri, cni, gateway-api, operators, rbac]
---

# Module 5.2: Kubernetes Architecture Deep Dive

> ### Learning Objectives
>
> By the end of this module you will be able to:
> - Map the Kubernetes control-plane components (API Server, etcd, Scheduler, Controller Manager) and explain the role of each in the reconciliation loop.
> - Deploy workloads with production-grade health probes, resource governance, and disruption budgets, then verify correct behaviour under node drain.
> - Diagnose common Pod failure modes (CrashLoopBackOff, Pending, ImagePullBackOff) using `kubectl describe`, events, and container logs.
> - Author RBAC Roles/ClusterRoles and NetworkPolicies that enforce namespace-scoped least-privilege access.
> - Compare Gateway API and Ingress for HTTP routing and implement TLS termination with cert-manager.

> **Module 05.2** · **Last updated:** 2026-05-22

## Guiding ideas
1. **Control plane: API Server, etcd, Scheduler, Controller Manager.**
2. **Data plane: kubelet + kube-proxy on each node.**
3. **Ingress controller comparison: Nginx, Istio, Traefik, ALB, Gateway API.**
4. **Operator pattern: CRD + controller per custom resource.**
5. **Gateway API > Ingress 2025+.**
6. **Level-driven reconciliation is the core abstraction.**

**Date:** 2026-05-22
**Status:** Completed

---

## 1. Kubernetes at 30,000 Feet

Kubernetes is a declarative, eventually consistent platform for running workloads. You tell it *what* you want (desired state), and controllers *reconcile* the cluster to match. This loop runs continuously.

```
┌─────────────────────────────────────────────────────────────┐
│                     CONTROL PLANE                           │
│  ┌─────────┐  ┌───────────┐  ┌──────────┐  ┌───────────┐   │
│  │ API      │  │ etcd      │  │Scheduler │  │Controller │   │
│  │ Server   │  │ (3 or 5   │  │          │  │ Manager   │   │
│  │          │  │  nodes)   │  │          │  │           │   │
│  └────┬─────┘  └───────────┘  └──────────┘  └───────────┘   │
│       │                                                      │
│  ┌────┴──────────────────────────────────────────────────┐   │
│  │ cloud-controller-manager (provider-specific)          │   │
│  └───────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────┘
                           │ Watch/API calls
┌──────────────────────────▼──────────────────────────────────┐
│                      DATA PLANE (per node)                   │
│  ┌─────────┐  ┌──────────┐  ┌──────────────────────────┐    │
│  │ kubelet  │  │kube-proxy│  │ Container Runtime        │    │
│  │          │  │          │  │ (containerd / CRI-O)     │    │
│  └─────────┘  └──────────┘  └──────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  Pods  [  C1  ] [  C2  ] [  C3  ]                   │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. etcd: The Cluster Brain

### 2.1 What etcd Is

etcd is a distributed, strongly consistent key-value store. It is the **single source of truth** for all Kubernetes cluster state. Every object (Pod, Service, ConfigMap, Secret) is stored in etcd as a key-value pair.

**Consistency model:** etcd uses the Raft consensus protocol. Writes are committed only when a majority of nodes (quorum) acknowledge. This guarantees linearizability — every read returns the most recent write.

**Data model:**
```
/registry/pods/default/my-pod          → Pod JSON
/registry/services/specs/default/my-svc → Service JSON
/registry/secrets/default/my-secret     → Secret JSON (base64, not encrypted by default!)
```

### 2.2 MVCC and Revisions

etcd does **not** overwrite keys. Each modification creates a new revision:

```
Key: /registry/pods/default/my-pod
  Revision 100: {phase: Pending, ...}
  Revision 105: {phase: Running, ...}
  Revision 200: {phase: Succeeded, ...}
```

- **Compact:** Old revisions are garbage collected (`etcd --auto-compaction-retention=1h`).
- **Defrag:** After compaction, physical space is reclaimed via defragmentation.
- **Snapshot:** Periodic snapshots for backup (`etcdctl snapshot save backup.db`).

### 2.3 The Watch Mechanism

Controllers do not poll etcd. They **watch** for changes. The API Server establishes a watch with a revision number. etcd streams all events from that revision forward.

```
Controller → API Server: Watch(resourceVersion=500)
API Server → etcd: Watch(rev=500)

etcd streams:
  rev=501: Pod my-pod MODIFIED (phase: Running)
  rev=502: Pod new-pod ADDED
  rev=510: Pod old-pod DELETED
  ... (continuous stream)
```

**Reliability:** If the watch connection breaks, the client reconnects with the last received `resourceVersion`. etcd replays all events from that point. If the gap is too large (compacted), the client receives a `410 Gone` and must re-list (full resync).

### 2.4 etcd Performance

| Metric | Guideline |
|:-------|:----------|
| **Disk** | SSD required. etcd is fsync-heavy. NFS and spinning disks will cause leader elections and instability. |
| **IOPS** | Minimum 50 sequential write IOPS for small clusters. 500+ for large. |
| **Latency** | p99 commit latency < 25ms. Above this, leader may step down. |
| **Memory** | 2-8 GB typical. Grows with object count. |
| **DB size** | Default max 2 GB. Increase with `--quota-backend-bytes`. |
| **Object count** | etcd handles 100K+ objects. Performance degrades with very large individual objects. |

### 2.5 etcd Topology

| Topology | Nodes | Fault tolerance |
|:---------|:------|:---------------|
| **Stacked** | etcd on same nodes as control plane | Simpler, fewer machines. Node failure takes both etcd and control plane. |
| **External** | etcd on dedicated nodes | Better isolation. etcd cluster survives control plane node failure. |

Always deploy **odd** number: 3 (tolerates 1 failure), 5 (tolerates 2). Never 2 (no fault tolerance improvement over 1). Never more than 7 (write latency increases with quorum size).

### 2.6 etcd Backup and Restore

```bash
# Backup
ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$(date +%Y%m%d).db \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key

# Verify
etcdctl snapshot status /backup/etcd-20260522.db --write-table

# Restore (all etcd members must restore from same snapshot)
etcdctl snapshot restore /backup/etcd-20260522.db \
  --data-dir=/var/lib/etcd-restored \
  --name=etcd-node1 \
  --initial-cluster=etcd-node1=https://10.0.0.1:2380,...
```

### 2.7 Encryption at Rest

By default, etcd stores Secrets in plaintext (base64 is encoding, not encryption). Enable encryption:

```yaml
# /etc/kubernetes/enc/encryption-config.yaml
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
    - identity: {}  # fallback: read existing unencrypted secrets
```

Pass `--encryption-provider-config` to the API server. Better yet, use a KMS provider (AWS KMS, Azure Key Vault, GCP Cloud KMS, HashiCorp Vault) to avoid managing keys yourself.

---

## 3. API Server

The API Server is the **only** component that talks to etcd. All other components (kubelet, scheduler, controllers, kubectl) interact through the API Server.

### 3.1 Request Flow

```
kubectl apply -f pod.yaml
  │
  ▼
┌─────────────────────────────────────────────────────┐
│                    API SERVER                        │
│                                                      │
│  1. Authentication (who are you?)                    │
│     - Client certificates (X.509)                    │
│     - Bearer tokens (ServiceAccount, OIDC)           │
│     - Webhook token review                           │
│                                                      │
│  2. Authorization (are you allowed?)                 │
│     - RBAC (most common)                             │
│     - ABAC (deprecated)                              │
│     - Webhook                                        │
│     - Node authorizer                                │
│                                                      │
│  3. Admission Control (should we allow this?)        │
│     a. Mutating admission webhooks                   │
│        (inject sidecar, add labels, set defaults)    │
│     b. Object schema validation                      │
│     c. Validating admission webhooks                 │
│        (enforce policies, deny invalid configs)      │
│                                                      │
│  4. Persist to etcd                                  │
│                                                      │
│  5. Return response to client                        │
└─────────────────────────────────────────────────────┘
```

### 3.2 Authentication

Kubernetes has no "user" object. Identity is established by the authentication layer:

| Method | Use case | Identity |
|:-------|:---------|:---------|
| **X.509 client certs** | kubectl, kubelets | CN = user, O = group |
| **ServiceAccount tokens** | In-cluster pods | `system:serviceaccount:<ns>:<name>` |
| **OIDC tokens** | Human users via IdP (Keycloak, Okta, Azure AD) | JWT claims map to user/groups |
| **Webhook token review** | Custom auth backends | Delegated to external service |
| **Bootstrap tokens** | Node joining | `system:bootstrappers:*` |

**Bound ServiceAccount tokens (default since 1.24):** Tokens are time-limited (1h default), audience-bound, and object-bound. No more static, never-expiring secrets.

### 3.3 Authorization (RBAC)

Four objects:

```yaml
# Role: namespace-scoped permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: production
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]

---
# RoleBinding: binds a Role to a subject in a namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: production
  name: read-pods
subjects:
- kind: User
  name: jane
  apiGroup: rbac.authorization.k8s.io
- kind: Group
  name: devs
  apiGroup: rbac.authorization.k8s.io
- kind: ServiceAccount
  name: monitoring-agent
  namespace: monitoring
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

**ClusterRole / ClusterRoleBinding:** Same, but cluster-wide. For non-namespaced resources (Nodes, PersistentVolumes, Namespaces) and cross-namespace access.

**Principle of least privilege:**
- No wildcard `*` verbs or resources in production.
- Avoid `cluster-admin` binding for anything except break-glass accounts.
- Audit RBAC regularly with `kubectl auth can-i --as=<user> --namespace=<ns> <verb> <resource>`.

### 3.4 Admission Controllers

Two phases: mutating (modify the object) then validating (accept/reject).

**Built-in admission controllers (selected):**

| Controller | Purpose |
|:-----------|:--------|
| `NamespaceLifecycle` | Prevents operations in terminating namespaces |
| `LimitRanger` | Enforces default resource limits per namespace |
| `ServiceAccount` | Auto-mounts ServiceAccount token into pods |
| `DefaultStorageClass` | Sets default storage class on PVCs |
| `ResourceQuota` | Enforces namespace resource quotas |
| `PodSecurity` | Enforces Pod Security Standards (replaces PSP) |
| `MutatingAdmissionWebhook` | Calls external webhooks to mutate objects |
| `ValidatingAdmissionWebhook` | Calls external webhooks to validate objects |

**Webhook admission controllers:**

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: enforce-labels
webhooks:
- name: enforce-labels.example.com
  clientConfig:
    service:
      name: policy-webhook
      namespace: policy-system
      path: /validate
    caBundle: <base64-CA>
  rules:
  - apiGroups: [""]
    resources: ["pods"]
    apiVersions: ["v1"]
    operations: ["CREATE", "UPDATE"]
  failurePolicy: Fail       # Fail closed (safer)
  sideEffects: None
  timeoutSeconds: 5
```

**Policy engines (deploy as webhooks):**
- **OPA/Gatekeeper:** Rego policy language. ConstraintTemplate defines policy, Constraint applies it.
- **Kyverno:** YAML-native policies. No new language to learn. Mutate, validate, generate, verify-images.

### 3.5 Validating Admission Policies (CEL-based, v1 in 1.30)

In-process validation using Common Expression Language — no webhook latency:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: require-team-label
spec:
  matchConstraints:
    resourceRules:
    - apiGroups: [""]
      resources: ["pods"]
      apiVersions: ["v1"]
      operations: ["CREATE"]
  validations:
  - expression: "has(object.metadata.labels) && 'team' in object.metadata.labels"
    message: "All pods must have a 'team' label"
```

---

## 4. Scheduler

The scheduler watches for unscheduled Pods (`.spec.nodeName` empty) and assigns them to nodes.

### 4.1 Scheduling Pipeline

```
1. FILTER (Predicates) — eliminate infeasible nodes
   - Has enough CPU/memory (resource requests fit)?
   - Matches nodeSelector / nodeAffinity?
   - Tolerates node taints?
   - Passes pod topology spread constraints?
   - Volume zone affinity satisfied?
   - Pod anti-affinity rules respected?

2. SCORE (Priorities) — rank remaining nodes
   - LeastRequestedPriority: prefer nodes with most available resources
   - BalancedResourceAllocation: even CPU/memory ratio across nodes
   - InterPodAffinityPriority: prefer nodes matching pod affinity
   - NodeAffinityPriority: prefer nodes matching preferred affinity
   - ImageLocalityPriority: prefer nodes that already have the container image

3. BIND — update Pod.spec.nodeName in etcd
```

### 4.2 Scheduling Constraints

**nodeSelector (simple):**
```yaml
spec:
  nodeSelector:
    disktype: ssd
    gpu: nvidia-a100
```

**nodeAffinity (expressive):**
```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: topology.kubernetes.io/zone
            operator: In
            values: ["eu-west-1a", "eu-west-1b"]
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 80
        preference:
          matchExpressions:
          - key: node-type
            operator: In
            values: ["compute-optimized"]
```

**podAffinity / podAntiAffinity:**
```yaml
spec:
  affinity:
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: web
        topologyKey: kubernetes.io/hostname
        # Never schedule two "app: web" pods on the same node
```

**Topology Spread Constraints:**
```yaml
spec:
  topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app: web
    # Spread "app: web" pods evenly across zones
```

**Taints and Tolerations:**
```bash
# Taint a node — no pod schedules unless it tolerates the taint
kubectl taint nodes gpu-node nvidia.com/gpu=true:NoSchedule
```
```yaml
spec:
  tolerations:
  - key: nvidia.com/gpu
    operator: Equal
    value: "true"
    effect: NoSchedule
```

| Effect | Behavior |
|:-------|:---------|
| `NoSchedule` | New pods without toleration are not scheduled. Existing pods stay. |
| `PreferNoSchedule` | Scheduler tries to avoid but may schedule if no alternative. |
| `NoExecute` | Evicts existing pods that lack toleration. New pods not scheduled. |

### 4.3 Priority and Preemption

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: critical-workload
value: 1000000
globalDefault: false
preemptionPolicy: PreemptLowerPriority
description: "For mission-critical workloads"
```

When a high-priority pod cannot be scheduled, the scheduler evicts lower-priority pods to make room. Essential for mixed-priority clusters.

### 4.4 Scheduler Profiles and Extenders

Multiple scheduling profiles can run in a single scheduler binary. Pods specify which profile to use via `schedulerName`.

**Scheduler extenders:** Webhooks that add custom filter/score logic to the scheduling pipeline.

**Scheduling framework plugins (kube-scheduler component config):** More performant than extenders. Plugins hook into specific extension points (PreFilter, Filter, Score, Reserve, Bind).

---

## 5. Controller Manager

The controller manager runs built-in controllers. Each controller watches a specific resource type and reconciles actual state toward desired state.

### 5.1 Key Controllers

| Controller | Watches | Reconciles |
|:-----------|:--------|:-----------|
| **ReplicaSet** | ReplicaSets | Ensures correct number of pod replicas |
| **Deployment** | Deployments | Manages ReplicaSets for rollouts |
| **StatefulSet** | StatefulSets | Ordered pod creation, stable identity |
| **DaemonSet** | DaemonSets | One pod per node |
| **Job** | Jobs | Run-to-completion pods |
| **CronJob** | CronJobs | Scheduled Jobs |
| **Namespace** | Namespaces | Cleanup on deletion |
| **ServiceAccount** | ServiceAccounts | Create default SA + token |
| **Endpoints** | Services/Pods | Update endpoint lists for services |
| **EndpointSlice** | Services/Pods | Scalable endpoint management |
| **Node** | Nodes | Monitor node health, evict pods on failure |
| **PersistentVolume** | PV/PVC | Bind PVCs to PVs |
| **GarbageCollector** | All | Cascade deletion (ownerReferences) |

### 5.2 The Reconciliation Loop (SharedInformer Pattern)

```
┌──────────────────────────────────────────────────────┐
│                 Controller                            │
│                                                       │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐     │
│  │ Reflector │───>│ DeltaFIFO│───>│   Informer   │    │
│  │ (List +   │    │ Queue    │    │ (updates     │    │
│  │  Watch)   │    │          │    │  local cache)│    │
│  └──────────┘    └──────────┘    └──────┬───────┘    │
│                                          │            │
│                                    ┌─────▼──────┐    │
│                                    │  Indexer    │    │
│                                    │ (lookup by  │    │
│                                    │  field/label│    │
│                                    └─────┬──────┘    │
│                                          │            │
│  Event handlers (Add/Update/Delete)      │            │
│  push object keys to:                    │            │
│                                    ┌─────▼──────┐    │
│                                    │ WorkQueue  │    │
│                                    │ (rate-limit│    │
│                                    │  + dedup)  │    │
│                                    └─────┬──────┘    │
│                                          │            │
│                                    ┌─────▼──────┐    │
│                                    │  Worker    │    │
│                                    │ (reconcile │    │
│                                    │  loop)     │    │
│                                    └────────────┘    │
└──────────────────────────────────────────────────────┘
```

**Key design properties:**
1. **Edge-triggered notifications, level-driven reconciliation:** The event triggers processing, but the worker always reads the **latest** state from the cache, not the specific event. If 5 events arrive for the same object, the worker sees only the final state.
2. **Rate-limited retries:** On failure, the key is re-enqueued with exponential backoff.
3. **Single-writer per key:** WorkQueue deduplicates — an object key appears at most once in the queue.

### 5.3 Cloud Controller Manager

Runs provider-specific controllers that interact with cloud APIs:
- **Node controller:** Syncs node metadata (instance type, zone, addresses) from cloud.
- **Route controller:** Sets up cloud routes for pod CIDR on each node.
- **Service controller:** Creates cloud load balancers for `type: LoadBalancer` services.

Each cloud provider (AWS, Azure, GCP) ships their own `cloud-controller-manager` binary.

---

## 6. Kubelet

The kubelet is the **node agent**. It runs on every node and is responsible for running pods.

### 6.1 Responsibilities

1. Register the node with the API server.
2. Watch for pods assigned to its node.
3. Pull container images.
4. Create containers via CRI (Container Runtime Interface).
5. Run probes (liveness, readiness, startup).
6. Report pod and node status to API server.
7. Manage volumes (mount/unmount via CSI).
8. Garbage collect terminated containers and unused images.
9. Enforce resource limits (cgroups).
10. Manage pod eviction when node resources are exhausted.

### 6.2 CRI (Container Runtime Interface)

gRPC API between kubelet and the container runtime:

```
kubelet → CRI gRPC → containerd (or CRI-O) → OCI runtime (runc/crun) → container
```

Key CRI operations:
- `RunPodSandbox` — create pod-level isolation (network namespace, pause container).
- `CreateContainer` — create a container within the sandbox.
- `StartContainer` — start the container.
- `StopContainer` — stop with grace period.
- `RemoveContainer` — delete.
- `ListContainers` — enumerate.
- `ContainerStatus` — inspect.

### 6.3 Pod Lifecycle

```
                    ┌──────────┐
                    │ Pending  │
                    └────┬─────┘
                         │ Scheduled to node
                    ┌────▼─────┐
               ┌────┤ Init     │ (init containers run sequentially)
               │    │Containers│
               │    └────┬─────┘
               │         │ All init containers complete
               │    ┌────▼─────┐
               │    │ Running  │ (main containers started)
               │    └────┬─────┘
               │         │
               │    ┌────▼─────┐
               │    │Succeeded │ (all containers exit 0, restartPolicy=Never)
               │    │  or      │
               │    │ Failed   │ (any container exit non-0, restartPolicy=Never)
               │    └──────────┘
               │
               └──► Restart (restartPolicy=Always or OnFailure)
```

### 6.4 Init Containers

Run before main containers, in sequence. Use cases:
- Wait for a database to be available.
- Clone a git repo into a shared volume.
- Generate config files.
- Run database migrations.

```yaml
spec:
  initContainers:
  - name: wait-for-db
    image: busybox
    command: ['sh', '-c', 'until nc -z postgres 5432; do sleep 2; done']
  - name: migrate
    image: my-app:v1
    command: ['python', 'manage.py', 'migrate']
  containers:
  - name: app
    image: my-app:v1
```

### 6.5 Probes

| Probe | Purpose | Failure action |
|:------|:--------|:--------------|
| **Startup** | Has the container started successfully? | Keep checking until `failureThreshold`. If exceeded, kill + restart. |
| **Liveness** | Is the container alive? | Kill + restart container. |
| **Readiness** | Can the container serve traffic? | Remove from Service endpoints. Do NOT restart. |

**Probe types:**
```yaml
# HTTP probe
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 15
  timeoutSeconds: 3
  failureThreshold: 3

# TCP probe
readinessProbe:
  tcpSocket:
    port: 5432
  periodSeconds: 10

# Exec probe
livenessProbe:
  exec:
    command: ["pg_isready", "-U", "postgres"]
  periodSeconds: 30

# gRPC probe (v1.27+)
livenessProbe:
  grpc:
    port: 50051
    service: my.health.v1.Health
```

**Common mistakes:**
- Liveness probe calls a dependency (DB). DB goes down → probe fails → pod restarts → no improvement.
- No startup probe for slow-starting apps (JVM, ML model loading). Liveness kills the pod before it finishes starting.
- Readiness probe with high `failureThreshold` → pod serves traffic while unhealthy.

### 6.6 Graceful Shutdown

```
1. Pod deletion requested (kubectl delete, rolling update, scale down)
2. Pod enters "Terminating" state
3. Endpoints controller removes pod from Service endpoints
4. preStop hook runs (if defined)
5. SIGTERM sent to PID 1 in each container
6. terminationGracePeriodSeconds countdown starts (default 30s)
7. Application drains connections, flushes buffers, exits
8. If still running after grace period → SIGKILL
9. Container removed
```

**Race condition:** Steps 3 and 4-5 happen **concurrently**. The pod may receive new traffic between SIGTERM and endpoint removal. Solution: `preStop: {exec: {command: ["sleep", "5"]}}` to give kube-proxy time to update iptables rules.

---

## 7. Resource Management

### 7.1 Requests and Limits

```yaml
resources:
  requests:
    cpu: "500m"       # 0.5 cores — scheduler guarantee
    memory: "256Mi"   # 256 MiB — scheduler guarantee
  limits:
    cpu: "2000m"      # 2 cores — hard ceiling (throttled)
    memory: "1Gi"     # 1 GiB — hard ceiling (OOMKilled)
```

**CPU:** Requests affect scheduling. Limits are enforced by CFS bandwidth control. Container is throttled (not killed) when limit is hit.

**Memory:** Requests affect scheduling and OOM score. Limits are hard. Exceed → OOM kill.

### 7.2 QoS Classes

| Class | Condition | OOM score adj | Eviction priority |
|:------|:----------|:-------------|:-----------------|
| **Guaranteed** | All containers: requests == limits, for both CPU and memory | -997 | Last |
| **Burstable** | At least one container has request or limit, but not all match | 2-999 | Middle |
| **BestEffort** | No requests or limits on any container | 1000 | First |

**Production rule:** Always set requests. Set limits for memory (OOM protection). CPU limits are debatable — throttling can cause unexpected latency. Many production clusters set CPU requests but not CPU limits.

### 7.3 LimitRange

Namespace-level defaults and constraints:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: defaults
  namespace: production
spec:
  limits:
  - default:             # default limits
      cpu: "1"
      memory: "512Mi"
    defaultRequest:      # default requests
      cpu: "100m"
      memory: "128Mi"
    max:                 # maximum allowed
      cpu: "4"
      memory: "4Gi"
    min:                 # minimum allowed
      cpu: "50m"
      memory: "64Mi"
    type: Container
```

### 7.4 ResourceQuota

Namespace-level aggregate limits:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute
  namespace: team-alpha
spec:
  hard:
    requests.cpu: "20"
    requests.memory: "40Gi"
    limits.cpu: "40"
    limits.memory: "80Gi"
    pods: "100"
    persistentvolumeclaims: "20"
    services.loadbalancers: "2"
```

### 7.5 Vertical Pod Autoscaler (VPA)

Automatically adjusts pod resource requests based on observed usage:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  updatePolicy:
    updateMode: "Auto"  # Auto, Recreate, Off (recommendation only)
  resourcePolicy:
    containerPolicies:
    - containerName: app
      minAllowed:
        cpu: "50m"
        memory: "64Mi"
      maxAllowed:
        cpu: "4"
        memory: "8Gi"
```

**Caveat:** VPA in `Auto` mode **restarts** pods to apply new requests. Not suitable for workloads that cannot tolerate restarts. Use `Off` mode to get recommendations without enforcement.

---

## 8. Autoscaling

### 8.1 Horizontal Pod Autoscaler (HPA)

Adjusts the number of pod replicas based on observed metrics:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

**HPA algorithm:** `desiredReplicas = ceil(currentReplicas × (currentMetricValue / desiredMetricValue))`

**Custom metrics:** HPA can scale on custom Prometheus metrics via the `custom.metrics.k8s.io` API (Prometheus Adapter, KEDA).

### 8.2 KEDA (Kubernetes Event-Driven Autoscaling)

Extends HPA with event-driven scaling. Supports 60+ scalers:

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: queue-consumer
spec:
  scaleTargetRef:
    name: consumer-deployment
  minReplicaCount: 0       # Scale to zero!
  maxReplicaCount: 100
  triggers:
  - type: rabbitmq
    metadata:
      queueName: work-queue
      host: amqp://rabbit.default.svc:5672
      queueLength: "5"    # 1 pod per 5 messages
  - type: cron
    metadata:
      timezone: UTC
      start: "30 7 * * 1-5"    # Scale up at 7:30 weekdays
      end: "0 20 * * 1-5"      # Scale down at 20:00
      desiredReplicas: "10"
```

**Key KEDA scalers:** RabbitMQ, Kafka, SQS, Azure Queue, Redis, Prometheus, Cron, PostgreSQL, HTTP (request rate), external (custom webhook).

### 8.3 Cluster Autoscaler

Adjusts the number of **nodes** (not pods). Watches for pods that cannot be scheduled due to insufficient resources and requests new nodes from the cloud provider.

**Scale-up:** Pending pods → cluster autoscaler evaluates node groups → provisions a new node.
**Scale-down:** If a node has been underutilized (<50% request usage) for 10 minutes and all pods can be rescheduled elsewhere → node is cordoned, drained, and terminated.

**Karpenter (AWS-native alternative):** Directly provisions EC2 instances based on pending pod requirements. Faster than Cluster Autoscaler (no node groups, just-in-time provisioning). Supports consolidation (replaces underutilized instances with smaller ones).

---

## 9. Networking

### 9.1 The Kubernetes Network Model

Three rules:
1. Every Pod gets its own IP address.
2. Pods on any node can communicate with all other pods on any node without NAT.
3. Agents on a node (kubelet, kube-proxy) can communicate with all pods on that node.

### 9.2 CNI Plugins

| Plugin | Data plane | Key features |
|:-------|:-----------|:------------|
| **Calico** | iptables, eBPF, or IPVS | BGP routing, network policies, WireGuard encryption |
| **Cilium** | eBPF | High performance, L7 policies, Hubble observability, service mesh |
| **Flannel** | VXLAN, host-gw | Simple, minimal features. No network policies. |
| **Weave Net** | VXLAN | Mesh networking, encryption. Reaching end-of-life. |
| **AWS VPC CNI** | ENI-based | Pod IPs from VPC subnet. No overlay. Native AWS networking. |
| **Azure CNI** | Bridge/overlay | Pod IPs from VNet. |
| **GKE CNI** | Alias IP ranges | Pod IPs from VPC. |

### 9.3 Services

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  type: ClusterIP    # or NodePort, LoadBalancer, ExternalName
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
```

| Type | Behavior |
|:-----|:---------|
| `ClusterIP` | Virtual IP accessible only within the cluster |
| `NodePort` | Exposes on each node's IP at a static port (30000-32767) |
| `LoadBalancer` | Cloud load balancer → NodePort → Pod |
| `ExternalName` | DNS CNAME alias to external service |
| `Headless` (clusterIP: None) | No VIP; DNS returns pod IPs directly. For StatefulSets. |

### 9.4 kube-proxy Modes

| Mode | Mechanism | Performance |
|:-----|:----------|:-----------|
| **iptables** (default) | DNAT rules per Service/Endpoint | O(n) rule evaluation. Degrades at >5000 services. |
| **IPVS** | Linux kernel L4 load balancer | O(1) lookup. Hash table. Better at scale. |
| **eBPF (Cilium)** | Replaces kube-proxy entirely | Best performance. Socket-level LB. No iptables. |
| **nftables** (1.31+) | Next-gen iptables replacement | Better performance than iptables mode. |

### 9.5 EndpointSlices

Replaced Endpoints objects for scalability. Each EndpointSlice contains up to 100 endpoints. A service with 5000 pods has 50 EndpointSlices instead of one massive Endpoints object. Reduces API server load and watch traffic.

### 9.6 Network Policies

Default: all pods can talk to all pods. Network policies are additive deny rules:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}    # applies to all pods in namespace
  policyTypes:
  - Ingress
  - Egress
  # No ingress or egress rules → deny all traffic

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-web-to-api
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: web
    ports:
    - protocol: TCP
      port: 8080
```

**Requirement:** CNI plugin must support NetworkPolicy (Calico, Cilium, Weave — yes; Flannel — no).

### 9.7 Gateway API

The successor to Ingress. Provides richer routing capabilities:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: production-gateway
spec:
  gatewayClassName: istio    # or nginx, cilium, envoy, etc.
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      certificateRefs:
      - name: tls-cert
    allowedRoutes:
      namespaces:
        from: Selector
        selector:
          matchLabels:
            shared-gateway: "true"

---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: my-app
spec:
  parentRefs:
  - name: production-gateway
  hostnames:
  - "app.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api-service
      port: 80
      weight: 90
    - name: api-service-canary
      port: 80
      weight: 10    # 10% canary traffic
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: frontend-service
      port: 80
```

**Gateway API advantages over Ingress:**
- Role-oriented: Infrastructure team manages Gateway, app teams manage Routes.
- Traffic splitting (weighted backends) natively.
- Header-based routing, request mirroring.
- TCP, UDP, gRPC, TLS passthrough routes.
- Extensible via policy attachment (rate limiting, auth).

---

## 10. Storage

### 10.1 CSI (Container Storage Interface)

Plugin spec for exposing storage systems to Kubernetes:

```
kubelet → CSI gRPC → CSI Driver → Storage Backend
```

CSI operations:
- `CreateVolume` / `DeleteVolume` — provision/deprovision storage.
- `ControllerPublishVolume` / `ControllerUnpublishVolume` — attach/detach to node.
- `NodeStageVolume` / `NodeUnstageVolume` — format and mount to a staging path.
- `NodePublishVolume` / `NodeUnpublishVolume` — bind-mount to pod path.

### 10.2 PersistentVolume / PersistentVolumeClaim

```yaml
# Static provisioning
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-data
spec:
  capacity:
    storage: 100Gi
  accessModes:
  - ReadWriteMany
  nfs:
    server: nfs.example.com
    path: /exports/data

---
# Dynamic provisioning (StorageClass)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "5000"
  throughput: "250"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer   # Don't provision until pod is scheduled
allowVolumeExpansion: true
```

| Access mode | Meaning |
|:------------|:--------|
| `ReadWriteOnce` (RWO) | Single node read-write. Most block storage. |
| `ReadOnlyMany` (ROX) | Multiple nodes read-only. |
| `ReadWriteMany` (RWX) | Multiple nodes read-write. NFS, EFS, Azure Files. |
| `ReadWriteOncePod` (RWOP) | Single pod read-write (1.29+). Prevents multi-attach. |

### 10.3 Ephemeral Volumes

- **emptyDir:** Shared between containers in a pod. Deleted when pod is removed.
- **configMap / secret volumes:** Project ConfigMap/Secret data as files.
- **projected:** Combine multiple sources (SA token, configMap, secret) into one mount.
- **CSI ephemeral volumes:** Per-pod volumes managed by CSI (e.g., Secrets Store CSI for Vault).

---

## 11. Custom Resource Definitions (CRDs) and Operators

### 11.1 CRDs

Extend the Kubernetes API with custom resource types:

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: databases.example.com
spec:
  group: example.com
  versions:
  - name: v1alpha1
    served: true
    storage: true
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            properties:
              engine:
                type: string
                enum: ["postgres", "mysql", "mongodb"]
              version:
                type: string
              replicas:
                type: integer
                minimum: 1
                maximum: 7
              storage:
                type: string
            required: ["engine", "version"]
  scope: Namespaced
  names:
    plural: databases
    singular: database
    kind: Database
    shortNames: ["db"]
```

```bash
# Now you can:
kubectl apply -f my-database.yaml     # creates a Database custom resource
kubectl get databases                  # lists all databases
kubectl describe db my-postgres        # describes a specific one
```

### 11.2 Operator Pattern

An operator is a controller that manages a CRD. It encodes domain-specific operational knowledge:

```
User creates: Database CR (engine=postgres, replicas=3)
    │
    ▼
Operator detects new Database CR
    │
    ▼
Operator creates:
  - StatefulSet (3 replicas, Postgres image)
  - Service (ClusterIP for writes, headless for reads)
  - PVCs (one per replica)
  - ConfigMap (pg_hba.conf, postgresql.conf)
  - Secret (superuser password)
  - CronJob (backup schedule)
    │
    ▼
Operator continuously reconciles:
  - Monitors replication lag
  - Handles failover
  - Manages minor version upgrades
  - Resizes storage
  - Restores from backup
```

**Operator frameworks:**
- **Operator SDK (Red Hat):** Go, Ansible, or Helm-based operators.
- **Kubebuilder:** Go framework from the Kubernetes SIG.
- **KUDO:** Declarative operator framework (define lifecycle in YAML).
- **Metacontroller:** Write controllers in any language via webhooks.

**Well-known operators:**
| Operator | Manages |
|:---------|:--------|
| **CloudNativePG** | PostgreSQL clusters |
| **Strimzi** | Apache Kafka |
| **cert-manager** | TLS certificates (Let's Encrypt, Vault) |
| **external-secrets-operator** | Sync secrets from Vault/AWS SM/Azure KV |
| **Prometheus Operator** | Prometheus, Alertmanager, Grafana |
| **ArgoCD** | GitOps continuous delivery |
| **Crossplane** | Cloud infrastructure as Kubernetes CRDs |

---

## 12. Service Mesh

### 12.1 What a Service Mesh Does

Transparent infrastructure layer for service-to-service communication:
- **mTLS encryption** between pods (zero-trust networking).
- **Traffic management:** retries, timeouts, circuit breaking, rate limiting.
- **Observability:** automatic metrics, traces, access logs for every request.
- **Traffic splitting:** canary deployments, A/B testing.

### 12.2 Sidecar Architecture (Istio, Linkerd)

```
┌─────────────────────────────────┐
│ Pod                              │
│ ┌──────────┐  ┌──────────────┐  │
│ │ App      │──│ Sidecar Proxy│──│──→ Network
│ │ Container│  │ (Envoy)      │  │
│ └──────────┘  └──────────────┘  │
└─────────────────────────────────┘
```

Sidecar proxy is injected automatically by a mutating admission webhook. All traffic is intercepted via iptables redirect rules in the pod.

### 12.3 Sidecarless Architecture (Cilium Service Mesh, Istio Ambient)

**Istio Ambient Mesh:** Uses per-node **ztunnel** (zero-trust tunnel) for L4 mTLS and optionally per-service **waypoint proxies** for L7 processing. No sidecar per pod. Lower resource overhead.

**Cilium:** eBPF-based. mTLS, traffic management, and observability at the kernel level. No sidecar, no iptables.

### 12.4 Istio vs Linkerd

| Aspect | Istio | Linkerd |
|:-------|:------|:--------|
| **Proxy** | Envoy (C++) | linkerd2-proxy (Rust, purpose-built) |
| **Complexity** | High (many CRDs, complex config) | Low (opinionated, fewer knobs) |
| **Resource overhead** | Higher (Envoy is general-purpose) | Lower (lean proxy) |
| **Features** | Extensive (traffic mgmt, security, observability, extensibility) | Core features (mTLS, traffic split, retries, observability) |
| **Multi-cluster** | Yes | Yes |
| **WASM extensibility** | Yes (Envoy WASM filters) | No |
| **CNCF status** | Graduated | Graduated |

**Decision heuristic:** If you need advanced L7 traffic management, WASM extensibility, or multi-mesh federation → Istio. If you want simple, fast, low-overhead mTLS + observability → Linkerd. If you already use Cilium for CNI → Cilium service mesh (no extra components).

---

## 13. GitOps

### 13.1 GitOps Principles

1. **Declarative:** System desired state is expressed declaratively.
2. **Versioned and immutable:** Desired state is stored in Git (versioned, auditable, immutable history).
3. **Pulled automatically:** Software agents pull the desired state from Git and apply it.
4. **Continuously reconciled:** Agents detect drift and correct it.

### 13.2 ArgoCD

```
Git Repo (manifests/Helm/Kustomize)
    │
    ▼ (sync)
┌──────────┐
│ ArgoCD   │──► Kubernetes Cluster
│ Server   │    (applies manifests)
└──────────┘
    │
    ▼ (UI / CLI / API)
  Dashboard
```

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
spec:
  source:
    repoURL: https://github.com/org/k8s-manifests.git
    targetRevision: main
    path: apps/my-app/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true        # delete resources removed from Git
      selfHeal: true     # revert manual changes
    syncOptions:
    - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
```

### 13.3 Flux

Toolkit approach — multiple controllers:
- **Source Controller:** Watches Git repos, Helm repos, OCI registries.
- **Kustomize Controller:** Applies Kustomize overlays.
- **Helm Controller:** Manages HelmReleases.
- **Notification Controller:** Alerts (Slack, Teams, webhook) on sync events.
- **Image Automation Controller:** Updates Git when new container images are pushed.

### 13.4 App-of-Apps Pattern

Manage many applications with a single ArgoCD Application:

```yaml
# Root Application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: apps
spec:
  source:
    repoURL: https://github.com/org/k8s-manifests.git
    path: apps           # Directory containing Application manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
```

The `apps/` directory contains one `Application` YAML per service. Adding a new service = adding a YAML file and pushing to Git.

---

## 14. Workload Types

### 14.1 Deployment (Stateless)

Rolling update strategy:
```yaml
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1    # At most 1 pod down during rollout
      maxSurge: 2          # At most 2 extra pods during rollout
```

### 14.2 StatefulSet (Stateful)

- Pods get stable network identity: `<name>-0`, `<name>-1`, `<name>-2`.
- Pods are created in order (0 → 1 → 2) and deleted in reverse order.
- Each pod gets its own PVC (via `volumeClaimTemplates`).
- Headless Service provides DNS: `<pod-name>.<service-name>.<namespace>.svc.cluster.local`.

Used for: databases, message brokers, Elasticsearch, ZooKeeper — anything needing stable identity and persistent storage.

### 14.3 DaemonSet

One pod per node. Use for: log collectors (Fluentbit), monitoring agents (node-exporter), CNI plugins, storage drivers.

### 14.4 Job and CronJob

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-migration
spec:
  completions: 10       # 10 total tasks
  parallelism: 3        # 3 concurrent pods
  backoffLimit: 5        # Retry up to 5 times on failure
  activeDeadlineSeconds: 3600  # Kill after 1 hour
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migrator
        image: migrator:v1
```

---

## 15. Configuration and Secrets

### 15.1 ConfigMaps

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_HOST: "postgres.production.svc"
  LOG_LEVEL: "info"
  config.yaml: |
    server:
      port: 8080
      workers: 4
```

Consumed as environment variables or volume mounts. ConfigMap changes are **not** automatically propagated to running pods when used as env vars (requires restart). Volume-mounted ConfigMaps update eventually (kubelet sync period, ~60s).

### 15.2 Secrets

Base64-encoded by default (not encrypted). For real security:
- Enable etcd encryption at rest.
- Use external secrets management: **external-secrets-operator** (syncs from AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, GCP Secret Manager into K8s Secrets).
- Use **Sealed Secrets** (Bitnami) for storing encrypted secrets in Git.
- Use **Secrets Store CSI Driver** to mount secrets from Vault/cloud KMS as volumes.

### 15.3 Kustomize

Template-free configuration management. Overlays modify a base:

```
base/
  deployment.yaml
  service.yaml
  kustomization.yaml
overlays/
  production/
    kustomization.yaml    # patches, replicas, image tags
  staging/
    kustomization.yaml
```

```yaml
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
- ../../base
namePrefix: prod-
patches:
- target:
    kind: Deployment
    name: my-app
  patch: |-
    - op: replace
      path: /spec/replicas
      value: 10
images:
- name: my-app
  newTag: v2.1.0
```

### 15.4 Helm

Package manager for Kubernetes. Charts = templated manifests:

```
my-chart/
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── _helpers.tpl
│   └── tests/
│       └── test-connection.yaml
```

```bash
helm install my-release my-chart/ --values production-values.yaml --namespace production
helm upgrade my-release my-chart/ --values production-values.yaml
helm rollback my-release 3   # rollback to revision 3
helm list -n production
helm uninstall my-release -n production
```

**Helm vs Kustomize:**
- Helm: full templating, release management, dependency management, hooks. Complexity of Go templates.
- Kustomize: overlay-based, no templates, built into kubectl. Simpler but less powerful for complex charts.

---

## 16. Multi-Cluster and Federation

### 16.1 Why Multi-Cluster

- **Blast radius reduction:** Cluster failure affects only its workloads.
- **Geographical distribution:** Clusters near users.
- **Regulatory compliance:** Data residency requirements.
- **Team isolation:** Separate clusters per team/environment.

### 16.2 Multi-Cluster Patterns

| Pattern | Description |
|:--------|:-----------|
| **Replicated** | Same app deployed to multiple clusters independently. |
| **Federated** | Control plane manages workloads across clusters. |
| **Hub-spoke** | Central management cluster, workload clusters as spokes. |

**Tools:**
- **Cluster API (CAPI):** Declarative cluster lifecycle management. Create/upgrade/delete clusters via Kubernetes CRDs.
- **Rancher:** Multi-cluster management platform with UI.
- **Google GKE Fleet:** Multi-cluster management for GKE.
- **Azure Arc-enabled Kubernetes:** Manage any K8s cluster from Azure.

---

## 17. Troubleshooting Playbook

### 17.1 Pod Stuck in Pending

```bash
kubectl describe pod <name>  # Check Events section
```
| Cause | Event message | Fix |
|:------|:-------------|:----|
| Insufficient resources | "Insufficient cpu/memory" | Add nodes, adjust requests, or lower other workloads |
| No matching node | "0/5 nodes available: 5 node(s) didn't match Pod's node affinity" | Fix nodeSelector/affinity or label nodes |
| PVC not bound | "pod has unbound immediate PersistentVolumeClaims" | Check StorageClass, PV availability |
| Taints | "5 node(s) had taints that the pod didn't tolerate" | Add tolerations or remove taints |

### 17.2 Pod Stuck in CrashLoopBackOff

```bash
kubectl logs <pod> --previous   # Logs from the crashed container
kubectl describe pod <pod>      # Exit code and events
```
| Exit code | Meaning |
|:----------|:--------|
| 0 | Success (but pod restarts if restartPolicy=Always) |
| 1 | Application error |
| 137 | SIGKILL (OOMKilled or force-killed) |
| 139 | SIGSEGV (segmentation fault) |
| 143 | SIGTERM (graceful shutdown) |

### 17.3 Service Not Reaching Pods

```bash
# 1. Check endpoints
kubectl get endpoints <service-name>
# If empty: selector doesn't match pod labels, or pods aren't Ready

# 2. Check pod readiness
kubectl get pods -l app=my-app -o wide

# 3. Test from within the cluster
kubectl run debug --rm -it --image=busybox -- wget -qO- http://my-service:80

# 4. Check network policies
kubectl get networkpolicies -n <namespace>
```

### 17.4 Node NotReady

```bash
kubectl describe node <name>
# Check Conditions: MemoryPressure, DiskPressure, PIDPressure, Ready
# Check Events: kubelet communication errors

# On the node:
systemctl status kubelet
journalctl -u kubelet -f
```

---

## 18. Production Checklist

### 18.1 Control Plane

- [ ] etcd: 3 or 5 nodes, SSD storage, regular backups, encryption at rest
- [ ] API Server: HA (multiple replicas behind LB), audit logging enabled
- [ ] RBAC: least-privilege roles, no `cluster-admin` for service accounts
- [ ] Admission controllers: PodSecurity (restricted), resource quotas, network policies
- [ ] API Server audit logs shipped to SIEM

### 18.2 Workloads

- [ ] All pods have resource requests and memory limits
- [ ] All pods have liveness, readiness, and startup probes
- [ ] Pod disruption budgets for critical workloads
- [ ] Anti-affinity rules for HA (spread across nodes/zones)
- [ ] Topology spread constraints for even distribution
- [ ] Graceful shutdown implemented (handle SIGTERM, preStop hook)
- [ ] Non-root containers, read-only root filesystem

### 18.3 Networking

- [ ] Default-deny network policies per namespace
- [ ] Service mesh mTLS or CNI-level encryption
- [ ] Ingress/Gateway with TLS termination
- [ ] DNS policies tuned (ndots, search domains)

### 18.4 Observability

- [ ] Metrics: Prometheus + Grafana dashboards for all services
- [ ] Logs: structured, shipped to aggregation (Loki/ELK)
- [ ] Traces: OpenTelemetry instrumentation, Jaeger/Tempo backend
- [ ] Alerts: SLO-based burn-rate alerts, PagerDuty/Opsgenie integration

### 18.5 Security

- [ ] Image scanning in CI (Trivy)
- [ ] Image signing and admission enforcement
- [ ] Secrets not in Git (external-secrets-operator or sealed-secrets)
- [ ] RBAC audit: no unnecessary ClusterRoleBindings
- [ ] Runtime security (Falco, KubeArmor)
- [ ] Regular Kubernetes version upgrades (stay within supported versions)

---

## 19. Key Takeaways

1. **Kubernetes is a reconciliation engine.** Controllers watch desired state (etcd), compare with actual state, and act. This loop is the entire system.

2. **etcd is the critical path.** Lose etcd, lose the cluster. Backup regularly, use SSDs, encrypt at rest.

3. **The scheduler is constraint-based.** Filter → Score → Bind. Use affinity, taints, topology spread to control placement.

4. **Requests = scheduling. Limits = enforcement.** Get requests right for scheduling. Set memory limits for safety. CPU limits are optional and often harmful (throttling).

5. **Network policies are default-allow.** You must explicitly deploy default-deny policies. Without a CNI that supports them, NetworkPolicy objects are no-ops.

6. **Gateway API supersedes Ingress.** Role-based, extensible, supports traffic splitting and multiple protocols.

7. **Operators encode operational knowledge.** For stateful workloads (databases, message brokers), a well-maintained operator is almost always better than hand-crafted StatefulSets.

8. **GitOps is the deployment pattern.** ArgoCD or Flux. Git as the source of truth. No `kubectl apply` from laptops in production.

9. **Multi-cluster is the norm at scale.** Blast radius, compliance, geo-distribution all push toward multiple clusters. Invest in multi-cluster tooling early.

10. **Security is not optional.** PodSecurity standards, RBAC, network policies, image scanning, secret management, runtime detection — all required for production.

---

## 20. Pod Security Standards (PSS)

### 20.1 The Three Levels

Pod Security Standards replaced PodSecurityPolicy (removed in 1.25):

| Level | Description | Use case |
|:------|:-----------|:---------|
| **Privileged** | Unrestricted. No validation. | System-level workloads (CNI, storage drivers) |
| **Baseline** | Prevents known privilege escalations. | General workloads |
| **Restricted** | Heavily restricted. Best practices enforced. | Security-sensitive workloads |

### 20.2 Enforcement Modes

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

| Mode | Behavior |
|:-----|:---------|
| `enforce` | Reject pods that violate the policy |
| `audit` | Log violations in API server audit log |
| `warn` | Show warning to user but allow the pod |

### 20.3 Restricted Level Requirements

- Must run as non-root (`runAsNonRoot: true`)
- Must drop ALL capabilities, may add only `NET_BIND_SERVICE`
- Must not allow privilege escalation (`allowPrivilegeEscalation: false`)
- Must use a read-only root filesystem (recommended, not required in all versions)
- Seccomp profile must be set (`RuntimeDefault` or `Localhost`)
- Must not use host namespaces (`hostNetwork`, `hostPID`, `hostIPC` all false)
- Must not use `hostPath` volumes
- Must not run in privileged mode

```yaml
# Pod that passes restricted level
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: my-app:v1
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

---

## 21. Deployment Strategies in Kubernetes

### 21.1 Rolling Update (Default)

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 25%
      maxSurge: 25%
```

New pods are created, old pods are terminated. At any point, at least 75% of desired replicas are available.

### 21.2 Blue-Green

Not a native Kubernetes primitive. Implemented by:
1. Deploy new version as a separate Deployment (green).
2. Wait for health checks.
3. Switch the Service selector from blue to green.
4. Keep blue running for rollback.

```bash
# Switch traffic
kubectl patch service my-app -p '{"spec":{"selector":{"version":"green"}}}'
# Rollback
kubectl patch service my-app -p '{"spec":{"selector":{"version":"blue"}}}'
```

### 21.3 Canary

Route a percentage of traffic to the new version:
- **Gateway API:** Use `weight` in `backendRefs` (shown in Section 9.7).
- **Istio VirtualService:** Traffic splitting by weight or header.
- **Argo Rollouts:** Native canary with analysis and automatic promotion/rollback.
- **Flagger:** Progressive delivery operator (works with Istio, Linkerd, Nginx, Gateway API).

```yaml
# Argo Rollouts canary strategy
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  strategy:
    canary:
      steps:
      - setWeight: 5
      - pause: {duration: 5m}
      - setWeight: 20
      - pause: {duration: 10m}
      - setWeight: 50
      - pause: {duration: 15m}
      - setWeight: 100
      analysis:
        templates:
        - templateName: success-rate
        startingStep: 1
        args:
        - name: service-name
          value: my-app
```

### 21.4 A/B Testing

Route traffic based on headers, cookies, or user attributes:
```yaml
# Istio VirtualService
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
spec:
  http:
  - match:
    - headers:
        x-user-group:
          exact: beta-testers
    route:
    - destination:
        host: my-app-v2
  - route:
    - destination:
        host: my-app-v1
```

---

## 22. Pod Disruption Budgets (PDB)

Protect workloads during voluntary disruptions (node drain, cluster upgrade, autoscaler scale-down):

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-app-pdb
spec:
  minAvailable: 2       # at least 2 pods must remain available
  # OR: maxUnavailable: 1   # at most 1 pod can be down
  selector:
    matchLabels:
      app: my-app
```

**Interaction with cluster autoscaler:** The autoscaler respects PDBs — it will not drain a node if doing so would violate a PDB.

**Interaction with kubectl drain:** `kubectl drain` will block until pods can be evicted without violating PDBs. Use `--timeout` and `--force` carefully.

**Common mistake:** Setting `minAvailable` equal to the replica count. This makes the workload un-drainable and blocks all node maintenance.

---

## 23. Kubernetes Security Deep Dive

### 23.1 Supply Chain Security

```
Source Code → Build → Image → Registry → Deploy → Runtime
    │           │        │         │          │         │
  Git signing  SLSA     Scan     Sign      Admit    Detect
  (Sigstore)   L3+    (Trivy)  (Cosign)  (Kyverno) (Falco)
```

**SLSA (Supply-chain Levels for Software Artifacts):**
- **Level 1:** Build process documented.
- **Level 2:** Build service generates provenance.
- **Level 3:** Build platform is hardened (hermetic builds).
- **Level 4:** Full dependency review, reproducible builds.

### 23.2 Runtime Security

**Falco:** eBPF-based runtime security. Detects anomalous behavior:
- Unexpected process execution (shell in production container).
- File access to sensitive paths (`/etc/shadow`, `/proc/kcore`).
- Network connections to unexpected destinations.
- Container escape attempts (namespace manipulation, mount abuse).

```yaml
# Falco rule example
- rule: Shell in Container
  desc: Detect shell execution in a container
  condition: >
    spawned_process and container and
    (proc.name in (bash, sh, zsh, dash, ksh))
  output: >
    Shell spawned in container
    (user=%user.name container=%container.name shell=%proc.name
     parent=%proc.pname image=%container.image.repository)
  priority: WARNING
```

**KubeArmor:** eBPF + LSM (AppArmor/SELinux/BPF-LSM) based enforcement. Blocks at the kernel level rather than just detecting.

### 23.3 RBAC Audit

```bash
# Who can create pods in the default namespace?
kubectl auth can-i create pods --as=system:anonymous -n default

# List all cluster-admin bindings
kubectl get clusterrolebindings -o json | \
  jq -r '.items[] | select(.roleRef.name == "cluster-admin") | .metadata.name'

# List all service accounts with cluster-admin
kubectl get clusterrolebindings -o json | \
  jq -r '.items[] | select(.roleRef.name == "cluster-admin") |
    .subjects[]? | select(.kind == "ServiceAccount") |
    "\(.namespace)/\(.name)"'
```

**Tools:** `rbac-tool`, `kubectl-who-can`, `rakkess` — visualize and audit RBAC permissions.

---

## 24. Kubernetes Upgrade Strategy

### 24.1 Version Skew Policy

| Component | Supported skew |
|:----------|:--------------|
| **kube-apiserver** | Can differ by 1 minor version across HA instances during rolling upgrade |
| **kubelet** | Up to 3 minor versions older than API server |
| **kube-controller-manager, kube-scheduler** | Same or 1 minor version older than API server |
| **kubectl** | ±1 minor version from API server |

### 24.2 Upgrade Sequence

```
1. Read release notes, changelog, deprecation notices
2. Test in staging cluster
3. Backup etcd
4. Upgrade control plane (API server → controller-manager → scheduler)
5. Upgrade kubelets (node by node, drain → upgrade → uncordon)
6. Upgrade CNI, CSI, and add-ons to compatible versions
7. Verify all workloads healthy
8. Update kubectl
```

### 24.3 Deprecation Policy

- Alpha features: may be removed without notice.
- Beta features: available for at least 3 releases after deprecation.
- GA features: available for at least 12 months / 3 releases after deprecation.

**Always run:** `kubectl get apideprecations` or use `kubent` (kube-no-trouble) to find deprecated API versions before upgrading.

---

## 25. Kubernetes Distributions and Platforms

| Distribution | Notes |
|:-------------|:------|
| **Vanilla Kubernetes** | kubeadm-bootstrapped. Full control, full responsibility. |
| **EKS (AWS)** | Managed control plane. Node groups or Fargate. |
| **AKS (Azure)** | Managed control plane. Tight Azure integration. |
| **GKE (Google)** | Most mature managed K8s. Autopilot mode = fully managed. |
| **OpenShift (Red Hat)** | Enterprise platform. Builds on K8s + operator framework + developer tools. |
| **Rancher (SUSE)** | Multi-cluster management. RKE2 runtime. |
| **k3s** | Lightweight K8s for edge/IoT. Single binary, embedded etcd/SQLite. |
| **k0s** | Zero-friction K8s. Single binary, all components. |
| **Talos Linux** | Immutable, API-managed OS purpose-built for K8s. No SSH. |
| **kind** | Kubernetes in Docker. For testing and CI. |
| **minikube** | Local development cluster. VM or container-based. |

---

## 26. Further Reading

- **"Kubernetes in Action" by Marko Luksa** (Manning, 2nd edition) — Comprehensive learning resource.
- **"Production Kubernetes" by Rosso, Lander, Brand, Harris** (O'Reilly) — Production best practices.
- **Kubernetes Documentation:** kubernetes.io/docs — The canonical reference.
- **Kubernetes the Hard Way (Kelsey Hightower):** github.com/kelseyhightower/kubernetes-the-hard-way — Build a cluster manually to understand every component.
- **Learnk8s:** learnk8s.io — Production-focused articles and guides.
- **CNCF Landscape:** landscape.cncf.io — Overview of the cloud-native ecosystem.
- **SIG documentation:** github.com/kubernetes/community/tree/master/sig-list — Each SIG maintains design proposals and meeting notes.
- **Gateway API:** gateway-api.sigs.k8s.io — The future of Kubernetes ingress.
- **ArgoCD:** argo-cd.readthedocs.io — GitOps continuous delivery.
- **Cilium:** docs.cilium.io — eBPF-based networking, security, and observability.

---

## 27. Kubernetes API Conventions and Versioning

### 27.1 API Groups

Kubernetes API is organized into groups:

| Group | Path | Resources |
|:------|:-----|:----------|
| **Core** (legacy) | `/api/v1` | Pods, Services, ConfigMaps, Secrets, Namespaces, Nodes, PVs, PVCs |
| **apps** | `/apis/apps/v1` | Deployments, StatefulSets, DaemonSets, ReplicaSets |
| **batch** | `/apis/batch/v1` | Jobs, CronJobs |
| **networking.k8s.io** | `/apis/networking.k8s.io/v1` | Ingress, NetworkPolicy, IngressClass |
| **rbac.authorization.k8s.io** | `/apis/rbac.authorization.k8s.io/v1` | Roles, ClusterRoles, Bindings |
| **storage.k8s.io** | `/apis/storage.k8s.io/v1` | StorageClass, CSIDriver, CSINode |
| **autoscaling** | `/apis/autoscaling/v2` | HPA |
| **policy** | `/apis/policy/v1` | PodDisruptionBudget |
| **scheduling.k8s.io** | `/apis/scheduling.k8s.io/v1` | PriorityClass |
| **gateway.networking.k8s.io** | `/apis/gateway.networking.k8s.io/v1` | Gateway, HTTPRoute |
| **apiextensions.k8s.io** | `/apis/apiextensions.k8s.io/v1` | CRDs |

### 27.2 API Versioning Stages

| Stage | Stability | Persistence |
|:------|:----------|:-----------|
| `v1alpha1` | Unstable, may change or be removed | May not be migrated between versions |
| `v1beta1` | Feature complete, API may change | Migrated between versions |
| `v1` | Stable, backward compatible | Guaranteed backward compatibility |

**Feature gates:** Alpha features are disabled by default (require `--feature-gates=MyFeature=true`). Beta features are enabled by default since 1.24.

### 27.3 API Discovery and Exploration

```bash
# List all API resources
kubectl api-resources

# List versions of a resource
kubectl api-versions

# Explain a resource's fields
kubectl explain pod.spec.containers.resources

# Raw API access
kubectl get --raw /api/v1/namespaces/default/pods

# Watch events at the API level
kubectl get events --watch -A
```

### 27.4 Server-Side Apply (SSA)

Default since kubectl 1.27. The server tracks field ownership — who set which field. Enables safe multi-controller management of the same object without conflicts.

```bash
# Apply with server-side apply
kubectl apply -f deployment.yaml --server-side

# Force ownership (take over fields from another manager)
kubectl apply -f deployment.yaml --server-side --force-conflicts
```

**Why it matters:** Without SSA, two controllers modifying the same object (e.g., HPA setting replicas and a human setting labels) can overwrite each other's changes. SSA tracks ownership at the field level and reports conflicts instead of silently overwriting.

---

## 28. Kubernetes Debugging Toolkit

### 28.1 Ephemeral Debug Containers

Attach a debug container to a running pod without modifying its spec:

```bash
kubectl debug pod/my-app -it --image=busybox --target=app
# Creates an ephemeral container sharing the pod's namespaces
# You can now inspect processes, network, filesystem of the "app" container
```

Useful for distroless containers that have no shell.

### 28.2 Node Debugging

```bash
kubectl debug node/my-node -it --image=ubuntu
# Creates a pod on the node with host PID, network, and filesystem access
# Host root filesystem is mounted at /host
chroot /host
# Now you have a shell on the node itself
```

### 28.3 Network Debugging

```bash
# DNS resolution test
kubectl run dns-test --rm -it --image=busybox -- nslookup kubernetes.default

# TCP connectivity test
kubectl run net-test --rm -it --image=busybox -- nc -zv my-service 8080

# Full network debugging
kubectl run net-debug --rm -it --image=nicolaka/netshoot -- bash
# netshoot includes: tcpdump, nmap, dig, curl, iperf3, mtr, ss, ip
```

### 28.4 Resource Usage

```bash
# Top pods by CPU/memory (requires metrics-server)
kubectl top pods -A --sort-by=cpu
kubectl top nodes

# Detailed pod resource usage
kubectl describe node <node-name> | grep -A 20 "Allocated resources"
```

---

## 29. Glossary

| Term | Definition |
|:-----|:-----------|
| **Admission Controller** | Plugin that intercepts API requests after auth but before persistence |
| **CRD** | Custom Resource Definition — extends the K8s API with new resource types |
| **CNI** | Container Network Interface — plugin spec for pod networking |
| **CSI** | Container Storage Interface — plugin spec for storage |
| **CRI** | Container Runtime Interface — gRPC API between kubelet and container runtime |
| **DaemonSet** | Ensures one pod per node |
| **EndpointSlice** | Scalable representation of Service endpoints |
| **etcd** | Distributed key-value store — Kubernetes state backend |
| **HPA** | Horizontal Pod Autoscaler — scales replica count |
| **Informer** | Client-side cache + watch mechanism for efficient API interaction |
| **KEDA** | Kubernetes Event-Driven Autoscaling — extends HPA with event-based triggers |
| **kubelet** | Node agent that runs pods |
| **Operator** | Controller that manages the lifecycle of a complex application |
| **PDB** | Pod Disruption Budget — limits voluntary pod evictions |
| **PSS** | Pod Security Standards — security profiles replacing PodSecurityPolicy |
| **QoS** | Quality of Service class — determines pod eviction priority |
| **RBAC** | Role-Based Access Control — authorization model |
| **VPA** | Vertical Pod Autoscaler — adjusts resource requests |
| **Workqueue** | Rate-limited queue used by controllers to process reconciliation events |

---

## Exercises

### Exercise 1: Deploy a Production-Grade Workload with Probes

1. Write a Deployment manifest for an HTTP application that includes:
   - `startupProbe` (HTTP check, `failureThreshold: 30`, `periodSeconds: 2`) to handle slow cold starts.
   - `readinessProbe` (HTTP check, `periodSeconds: 5`) to gate traffic.
   - `livenessProbe` (HTTP check, `periodSeconds: 10`) to restart on deadlock.
   - Resource `requests` and `limits` for CPU and memory.
   - A `PodDisruptionBudget` with `minAvailable: 1`.
2. Deploy to a test cluster. Drain the node and verify the PDB prevents full eviction.
3. Simulate a deadlock (e.g., make the liveness endpoint hang) and confirm Kubernetes restarts the pod.

### Exercise 2: Debug a CrashLoopBackOff

1. Deploy a pod with an intentional failure (e.g., wrong entrypoint command or missing environment variable).
2. Run the following diagnostic sequence and document findings at each step:
   ```bash
   kubectl get pods -o wide
   kubectl describe pod <name>
   kubectl logs <name> --previous
   kubectl get events --sort-by=.lastTimestamp
   ```
3. Fix the root cause, redeploy, and verify the pod reaches `Running` state.
4. Repeat with an `ImagePullBackOff` scenario (misspelled image tag) and document the different event sequence.

### Exercise 3: RBAC Least-Privilege Design

1. Create a namespace `team-alpha`.
2. Define a `Role` that grants only `get`, `list`, `watch` on Pods and `create` on Pods/exec (for debugging).
3. Bind the role to a ServiceAccount `alpha-dev`.
4. Use `kubectl auth can-i --as=system:serviceaccount:team-alpha:alpha-dev` to verify:
   - Can list pods in `team-alpha` — expected: yes.
   - Can delete pods in `team-alpha` — expected: no.
   - Can list pods in `default` — expected: no.
5. Add a `NetworkPolicy` that allows ingress only from pods labelled `app=frontend` within the namespace.

### Exercise 4: Gateway API TLS Routing

1. Install a Gateway API implementation (e.g., Envoy Gateway or Cilium).
2. Create a `Gateway` resource with an HTTPS listener on port 443.
3. Deploy two services (`svc-a`, `svc-b`) and create `HTTPRoute` resources that route `/a/*` to `svc-a` and `/b/*` to `svc-b`.
4. Use cert-manager to issue a self-signed certificate and attach it to the Gateway listener.
5. Verify end-to-end TLS termination with `curl -k https://<gateway-ip>/a/health`.

### Exercise 5: Operator Pattern — Build a Minimal Controller

1. Use `kubebuilder init` and `kubebuilder create api` to scaffold a CRD called `EchoConfig` with fields `message` (string) and `replicas` (int).
2. Implement the reconciler so that it creates/updates a Deployment running an echo server with the specified replica count and an env var containing the message.
3. Deploy the CRD and controller to a test cluster.
4. Create an `EchoConfig` CR, verify the Deployment appears, change `replicas`, and confirm the controller reconciles.
5. Delete the CR and verify the controller cleans up the owned Deployment.

---

## Readings and References

### Books

| Title | Authors | Publisher | Year | Notes |
|:------|:--------|:----------|:-----|:------|
| *Kubernetes: Up and Running*, 3rd ed. | Brendan Burns, Joe Beda, Kelsey Hightower, Lachlan Evenson | O'Reilly Media | 2024 | Authoritative introduction covering architecture through advanced patterns |
| *Kubernetes Best Practices*, 2nd ed. | Brendan Burns, Eddie Villalba, Dave Strebel, Lachlan Evenson | O'Reilly Media | 2024 | Production blueprints: security, networking, observability, multi-cluster |
| *Programming Kubernetes* | Michael Hausenblas, Stefan Schimanski | O'Reilly Media | 2019 | Deep treatment of client-go, informers, and custom controller development |

### Online Resources

| Resource | URL | Retrieved |
|:---------|:----|:----------|
| Kubernetes Official Documentation — Architecture | https://kubernetes.io/docs/concepts/architecture/ | 2026-05-29 |
| Kubernetes API Reference (latest) | https://kubernetes.io/docs/reference/ | 2026-05-29 |
| Gateway API Specification | https://gateway-api.sigs.k8s.io/ | 2026-05-29 |
| etcd Documentation | https://etcd.io/docs/ | 2026-05-29 |
| Kubernetes Release History | https://kubernetes.io/releases/ | 2026-05-29 |
| DevOpsCube — Kubernetes Architecture Explained | https://devopscube.com/kubernetes-architecture-explained/ | 2026-05-29 |
| CNCF Landscape — Container Orchestration | https://landscape.cncf.io/ | 2026-05-29 |
| cert-manager Documentation | https://cert-manager.io/docs/ | 2026-05-29 |
| Kubebuilder Book | https://book.kubebuilder.io/ | 2026-05-29 |

### Papers and Specifications

- Burns, B., Grant, B., Oppenheimer, D., Brewer, E., & Wilkes, J. (2016). *Borg, Omega, and Kubernetes*. ACM Queue, 14(1), 70–93.
- Kubernetes SIG Architecture (2024). *Kubernetes Enhancement Proposals (KEPs)*. https://github.com/kubernetes/enhancements
- Kubernetes SIG Network (2024). *Gateway API GEPs*. https://gateway-api.sigs.k8s.io/geps/overview/

---

## Cross-References

| Module | File | Relationship |
|:-------|:-----|:-------------|
| 5.1 — Container Internals | [01_Container_Internals.md](./01_Container_Internals.md) | Kubernetes CRI pipeline delegates to OCI runtimes and relies on namespace/cgroup primitives |
| 5.3 — Site Reliability Engineering | [03_Site_Reliability_Engineering.md](./03_Site_Reliability_Engineering.md) | SRE practices (SLOs, error budgets, incident response) govern how K8s workloads are operated |
| 5.4 — Infrastructure as Code | [04_Infrastructure_as_Code.md](./04_Infrastructure_as_Code.md) | Terraform/Pulumi provision clusters; Helm/Kustomize manage K8s manifests declaratively |
| 5.5 — Observability, SLI/SLO/SLA | [05_Observability_SLI_SLO_SLA.md](./05_Observability_SLI_SLO_SLA.md) | Metrics Server, Prometheus, and tracing integrate with K8s to measure SLIs |
| 5.6 — Cloud Architecture | [06_Cloud_Architecture_AWS_Azure_GCP.md](./06_Cloud_Architecture_AWS_Azure_GCP.md) | Managed Kubernetes (EKS, GKE, AKS) abstract control-plane operations |
| Architecture & Design | [02_Architecture_Design/](../02_Architecture_Design/) | Distributed system patterns (event sourcing, CQRS, saga) deployed on Kubernetes |