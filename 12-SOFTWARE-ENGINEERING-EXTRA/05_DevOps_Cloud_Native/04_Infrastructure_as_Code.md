# Module 5.4: Infrastructure as Code — Terraform, Pulumi, Ansible

> **Module 05.4** · **Last updated:** 2026-04-27

## Guiding ideas
1. **Terraform/OpenTofu HCL declarativo.**
2. **Pulumi: code (TS/Go/Python) > HCL.**
3. **Crossplane: K8s-native cloud resources.**
4. **State management: remote backend mandatory; locking via DynamoDB / Azure Blob.**


**Date:** 2026-04-22
**Status:** Completed

## 1. Declarative vs Imperative IaC

| Style | You write | Engine does | Examples |
| :--- | :--- | :--- | :--- |
| **Declarative** | Desired state | Computes diff vs current, applies | Terraform, CloudFormation, Pulumi, Crossplane |
| **Imperative** | Steps to execute | Runs steps, idempotency on you | Ansible (mostly), shell, Chef recipes |

Declarative wins for cloud resources (idempotency, drift detection, planning). Imperative wins for OS-level configuration where order matters (package install, service config, file mutation).

## 2. Terraform

### 2.1 Core Model
*   **HCL2:** typed config language. `resource`, `data`, `variable`, `output`, `locals`, `module`.
*   **Providers:** plugins (`hashicorp/aws`, `hashicorp/azurerm`, `hashicorp/google`, `kubernetes`, `helm`, `tls`, ...). Version-pin in `required_providers`.
*   **State file:** JSON map of resource address → real-world ID + attributes. **Source of truth for diff**.

### 2.2 Lifecycle
```
terraform init     # download providers, init backend
terraform plan     # diff = desired - current(state)
terraform apply    # execute the diff
terraform destroy  # negate everything in state
terraform import   # bind existing resource into state without recreating
```

### 2.3 Remote State + Locking
Local state is single-user; teams must use a remote backend with locking.

*   **S3 + DynamoDB** lock table.
*   **Azure Storage** with blob lease.
*   **GCS** with object versioning.
*   **Terraform Cloud / Spacelift / Scalr** managed.

Without locking: two `apply`s race → corrupted state, orphan resources.

### 2.4 Modules & Reuse
*   **Module = directory of `.tf` files.** Inputs (`variable`), outputs (`output`).
*   Source: local path, git, Terraform Registry, OCI artifact.
*   **Don't over-modularize.** A module is justified when it's reused ≥2 times or hides genuine complexity.

### 2.5 Workspaces vs Directories
*   **Workspaces:** same code, different state file (`dev`, `stg`, `prod`). Risk: divergence happens silently.
*   **Directory-per-env (preferred):** `live/prod/`, `live/stg/` calling shared modules. Explicit, code-reviewable.

### 2.6 `count` vs `for_each`
*   `count = 3` → indexed list. Removing index 1 destroys index 2 and 3 (re-keying).
*   `for_each = toset([...])` → keyed map. Removing one key only destroys that resource. **Default to `for_each`.**

### 2.7 Auth via OIDC
GitHub Actions / GitLab CI → cloud via OIDC federation. No long-lived access keys.
*   AWS: IAM role with `sts:AssumeRoleWithWebIdentity`.
*   Azure: federated credential on app registration.
*   GCP: workload identity federation pool.

### 2.8 Drift Detection
*   `terraform plan -refresh-only` → reconcile state with reality without changes.
*   Tools: **driftctl**, Terraform Cloud drift detection, AWS Config rules.

## 3. Pulumi

*   IaC in **TypeScript / Python / Go / C# / Java**. Uses Terraform providers under the hood (`pulumi-terraform-bridge`).
*   **Stack** = isolated deployment instance (analog to Terraform workspace, but typed config).
*   State backends: Pulumi Cloud, S3, Azure Blob, self-hosted.
*   **Automation API:** drive Pulumi programmatically (e.g., per-tenant infra in a SaaS control plane).
*   Trade-off: real language → loops, abstractions, tests; also: full Turing-complete code in your infra (footgun).

## 4. Ansible

*   **Push-based, agentless** over SSH (or WinRM).
*   YAML **playbooks** → list of plays → list of tasks calling **modules**.
*   **Idempotency** is the module's responsibility (`apt`, `copy`, `template`, `lineinfile`).
*   **Inventory:** static INI/YAML or dynamic (cloud plugins).
*   **Roles:** reusable bundles (`tasks/`, `handlers/`, `templates/`, `defaults/`, `vars/`).
*   **Handlers:** triggered by `notify` after change (e.g., restart nginx).
*   **Ansible Vault:** symmetric AES-256 for secrets in repo (`ansible-vault encrypt`).
*   Strength: configuration, orchestrated rollouts, ad-hoc ops. Weakness: managing cloud resource graphs.

## 5. Cloud-Native IaC

| Tool | Cloud | Notes |
| :--- | :--- | :--- |
| **CloudFormation** | AWS | YAML/JSON, stack rollback, Change Sets. Verbose. |
| **AWS CDK** | AWS | TS/Python/Java/Go → synthesizes CFN. |
| **ARM templates** | Azure | JSON, legacy. |
| **Bicep** | Azure | DSL transpiling to ARM. Cleaner. |
| **Deployment Manager** | GCP | Deprecated for new use; prefer Terraform/Config Connector. |
| **Crossplane** | Multi (K8s) | CRDs as cloud resources; reconciled by K8s controllers. GitOps-native. |

## 6. Immutable Infrastructure

Replace, don't mutate.

*   **Packer** builds golden images (AMI, qcow2, OVA, container).
*   Deploy = launch new image, drain old. Blue/green or canary at the AMI/launch-template level.
*   Eliminates configuration drift entirely (no in-place package updates).
*   Pairs with autoscaling groups + load balancers + health checks.

## 7. Policy as Code

Guardrails before `apply`.

*   **OPA / Rego** — generic policy engine. `conftest` runs Rego against Terraform plan JSON.
*   **HashiCorp Sentinel** — Terraform Cloud/Enterprise built-in.
*   **Checkov** — static analysis (Terraform, CFN, K8s, Dockerfile). 1000+ baked checks.
*   **tfsec / Trivy IaC** — security-focused scanners.
*   **Kyverno / Gatekeeper** — runtime policy on the Kubernetes side.

Enforce: required tags, no public S3, encryption-at-rest, allowed regions, naming conventions, blast-radius limits.

## 8. GitOps for IaC

Pull-request-driven infra.

*   **Atlantis:** open-source. Webhook on PR → `terraform plan` comment → `atlantis apply` after approval.
*   **Terraform Cloud / Enterprise:** VCS-connected workspaces, Sentinel, cost estimation.
*   **Spacelift, env0, Scalr:** managed runners, drift detection, RBAC, OPA integration.

Discipline: state never edited by hand; every change goes through PR with a reviewed plan attached. The plan is the diff humans approve, not the HCL.
