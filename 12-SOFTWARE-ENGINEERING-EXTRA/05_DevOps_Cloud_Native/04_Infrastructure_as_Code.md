---
corso: "SWE Masterclass"
fase: "5 — DevOps & Cloud Native"
modulo: "5.4"
titolo: "Infrastructure as Code — Terraform, Pulumi, Ansible"
versione: "Terraform 1.9 / OpenTofu 1.8 / Pulumi 3.x / Ansible 2.17 / Crossplane 1.17"
livello: "Advanced"
prerequisiti:
  - "Linux CLI and shell scripting fundamentals"
  - "Cloud provider basics (AWS, Azure, or GCP console and IAM)"
  - "Version control with Git (branching, PRs, merge strategies)"
  - "YAML and JSON fluency"
  - "Containers and Kubernetes basics (Module 5.1–5.2)"
obiettivi:
  - "Design a multi-environment Terraform/OpenTofu project using remote state, locking, and directory-per-env layout"
  - "Author reusable Terraform modules with input validation, versioned outputs, and registry publishing"
  - "Implement drift detection pipelines that reconcile desired state with cloud reality and alert on divergence"
  - "Compare declarative (Terraform/Pulumi) vs imperative (Ansible) IaC and select the right tool per layer"
  - "Enforce Policy-as-Code guardrails (OPA, Checkov, Sentinel) in CI before any infrastructure apply"
tag: [iac, terraform, opentofu, pulumi, ansible, crossplane, gitops, policy-as-code, immutable-infrastructure, devops]
---

# Module 5.4: Infrastructure as Code — Terraform, Pulumi, Ansible

> **Learning Objectives**
> After completing this module you will be able to:
> 1. Design a multi-environment Terraform/OpenTofu project using remote state, locking, and directory-per-env layout.
> 2. Author reusable Terraform modules with input validation, versioned outputs, and registry publishing.
> 3. Implement drift detection pipelines that reconcile desired state with cloud reality and alert on divergence.
> 4. Compare declarative (Terraform/Pulumi) vs imperative (Ansible) IaC and select the right tool per layer.
> 5. Enforce Policy-as-Code guardrails (OPA, Checkov, Sentinel) in CI before any infrastructure apply.

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

## Exercises

1. **Reusable VPC Module with Registry Publishing**
   Build a Terraform module that provisions a VPC (or VNet / VPC on Azure/GCP) with configurable CIDR ranges, public/private subnets, NAT gateway, and flow logs. Publish the module to a private Terraform Registry (or use `git::` source). Consume the module from two environments (`dev/` and `prod/`) using directory-per-env layout with separate state files backed by S3 + DynamoDB locking. Validate that `terraform plan` in `prod/` is independent of `dev/` state.

2. **Drift Detection Pipeline**
   Configure a scheduled CI job (GitHub Actions or GitLab CI) that runs `terraform plan -refresh-only -detailed-exitcode` against production state every 6 hours. If exit code is 2 (drift detected), the pipeline should: (a) post the plan diff to a Slack channel, (b) open a GitHub Issue with the drifted resources and their attribute changes. Optionally integrate `driftctl` to compare all cloud resources against state and surface unmanaged (shadow) resources.

3. **Policy-as-Code Gate with OPA and Checkov**
   Write three OPA/Rego policies: (a) deny any `aws_s3_bucket` without `server_side_encryption_configuration`, (b) deny any security group with ingress `0.0.0.0/0` on port 22, (c) enforce a mandatory `Environment` tag on all resources. Run `conftest test` against `terraform show -json tfplan.binary` in CI. Additionally, run `checkov -d .` and fail the pipeline if any HIGH-severity check fails. Document the policy enforcement flow in the PR template.

4. **Pulumi Stack with Unit Tests**
   Implement an S3 bucket + CloudFront distribution using Pulumi (TypeScript or Python). Write unit tests using `pulumi.runtime.setMocks()` that verify: (a) the bucket has versioning enabled, (b) the CloudFront distribution uses HTTPS-only origin, (c) the bucket policy denies unencrypted transport. Run tests with `jest` or `pytest` and integrate into CI. Compare the developer experience with an equivalent Terraform implementation.

5. **Ansible Playbook for OS Hardening with Vault Secrets**
   Write an Ansible playbook that hardens a Linux server: disable root SSH, enforce key-only auth, install and configure `fail2ban`, enable automatic security updates, set up `auditd` rules. Store the `fail2ban` configuration values in Ansible Vault. Use a dynamic inventory plugin (AWS EC2 or Azure) to target instances by tag. Run the playbook with `--check --diff` first, then apply. Verify idempotency by running the playbook twice and confirming zero changes on the second run.

## Readings and References

### Books

*   Brikman, Y. — *Terraform: Up & Running*, 3rd ed. (O'Reilly, 2022). Covers modules, testing, multi-provider, secrets management. — [O'Reilly catalog](https://www.oreilly.com/library/view/terraform-up-and/9781098116736/) (retrieved: 2026-05-29)
*   Morris, K. — *Infrastructure as Code*, 2nd ed. (O'Reilly, 2021). Principles, patterns, and practices beyond any single tool.
*   Pulumi — *Pulumi Documentation: Infrastructure as Code*. — [pulumi.com/docs/iac](https://www.pulumi.com/docs/iac/) (retrieved: 2026-05-29)

### Official Documentation

*   HashiCorp — *Terraform Language Documentation*. — [developer.hashicorp.com/terraform/language](https://developer.hashicorp.com/terraform/language) (retrieved: 2026-05-29)
*   OpenTofu — *OpenTofu Documentation (state encryption, early eval)*. — [opentofu.org/docs](https://opentofu.org/docs/) (retrieved: 2026-05-29)
*   Ansible — *Ansible Documentation*. — [docs.ansible.com](https://docs.ansible.com/) (retrieved: 2026-05-29)

### Articles and Guides

*   DEV Community — *Infrastructure as Code Best Practices: Terraform, Pulumi, and OpenTofu in 2026*. — [dev.to](https://dev.to/muskan_8abedcc7e12/infrastructure-as-code-best-practices-terraform-pulumi-and-opentofu-in-2026-4nc1) (retrieved: 2026-05-29)
*   The New Stack — *OpenTofu Joins CNCF: New Home for Open Source IaC Project*. — [thenewstack.io](https://thenewstack.io/opentofu-joins-cncf-new-home-for-open-source-iac-project/) (retrieved: 2026-05-29)
*   Encore — *OpenTofu vs Terraform in 2026: License, Features, and Migration*. — [encore.dev](https://encore.dev/articles/opentofu-vs-terraform-2026) (retrieved: 2026-05-29)
*   Firefly — *Terraform Infrastructure as Code (IaC) Guide With Examples (2026)*. — [firefly.ai/academy](https://www.firefly.ai/academy/terraform-iac) (retrieved: 2026-05-29)

## Cross-References

| Topic | Module | Link |
| :--- | :--- | :--- |
| Container internals (cgroups, namespaces, OCI) | 5.1 | [01_Container_Internals.md](01_Container_Internals.md) |
| Kubernetes architecture and workloads | 5.2 | [02_Kubernetes_Architecture.md](02_Kubernetes_Architecture.md) |
| Site Reliability Engineering (error budgets, toil) | 5.3 | [03_Site_Reliability_Engineering.md](03_Site_Reliability_Engineering.md) |
| Observability, SLI/SLO/SLA, and burn-rate alerts | 5.5 | [05_Observability_SLI_SLO_SLA.md](05_Observability_SLI_SLO_SLA.md) |
| Cloud architecture — AWS, Azure, GCP, landing zones | 5.6 | [06_Cloud_Architecture_AWS_Azure_GCP.md](06_Cloud_Architecture_AWS_Azure_GCP.md) |
| Security, cryptography, and zero-trust models | — | [../../04_Security_Cryptography/](../../04_Security_Cryptography/) |

## Glossary

| Term | Definition |
| :--- | :--- |
| **Declarative IaC** | Infrastructure definition that specifies *desired state*; the engine computes and applies the diff. |
| **Imperative IaC** | Infrastructure definition that specifies *steps to execute*; idempotency is the author's responsibility. |
| **State file** | JSON artifact mapping each declared resource to its real-world ID and attributes; source of truth for plan diffs. |
| **Remote backend** | Server-side state storage (S3, GCS, Azure Blob, Terraform Cloud) enabling team collaboration and state locking. |
| **State locking** | Mutex mechanism (e.g., DynamoDB lease) preventing concurrent `apply` operations from corrupting state. |
| **Drift** | Divergence between the declared desired state and actual cloud resource configuration, caused by manual or out-of-band changes. |
| **Module** | Reusable directory of `.tf` files with typed inputs (`variable`) and outputs (`output`); the unit of composition in Terraform/OpenTofu. |
| **Provider** | Plugin that translates HCL resource declarations into cloud API calls (e.g., `hashicorp/aws`, `hashicorp/azurerm`). |
| **Plan** | Read-only diff output showing what Terraform/OpenTofu will create, update, or destroy before any mutation occurs. |
| **Policy as Code** | Machine-enforceable rules (OPA/Rego, Sentinel, Checkov) evaluated against IaC plans to block non-compliant deployments. |
| **Immutable infrastructure** | Pattern where servers are never patched in place; instead, a new image is built and deployed, replacing the old one entirely. |
| **GitOps (for IaC)** | Workflow where infrastructure changes are proposed via pull request, planned automatically, and applied only after human approval. |
| **OIDC federation** | Authentication pattern where CI runners exchange a short-lived JWT for cloud credentials, eliminating long-lived static keys. |
| **Idempotency** | Property ensuring that applying the same operation multiple times produces the same result as applying it once. |
| **Blast radius** | The scope of impact if a deployment or configuration change fails; minimized by isolating state per environment and account. |
