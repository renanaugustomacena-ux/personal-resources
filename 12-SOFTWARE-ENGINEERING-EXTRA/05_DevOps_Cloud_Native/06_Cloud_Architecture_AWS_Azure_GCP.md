# Module 5.6: Cloud Architecture — AWS, Azure, GCP, Hybrid/Multi-cloud

> **Module 05.6** · **Last updated:** 2026-04-27

## Guiding ideas
1. **Well-Architected Framework AWS/Azure/GCP.** 6 pilastri ognuno.
2. **Multi-cloud rare; hybrid common.**
3. **OIDC > IAM key per CI/CD cross-cloud.**
4. **Reserved Instance / Savings Plan: 30-60% cost optimization.**


**Date:** 2026-04-22
**Status:** Completed

## 1. Well-Architected Framework

AWS canonicalized the model; Azure and GCP have parallels. Six pillars:

| Pillar | AWS service mapping | Azure | GCP |
| :--- | :--- | :--- | :--- |
| **Operational Excellence** | CloudWatch, Systems Manager, CloudFormation | Monitor, Automation, Bicep | Cloud Operations, Deployment Manager |
| **Security** | IAM, GuardDuty, KMS, Macie, Security Hub | Entra ID, Defender, Key Vault, Sentinel | IAM, SCC, KMS, Chronicle |
| **Reliability** | Route 53, Multi-AZ, Auto Scaling, Backup | Traffic Manager, Availability Zones, Backup | Cloud DNS, MIGs, Backup/DR |
| **Performance Efficiency** | EC2 family selection, ElastiCache, CloudFront | VM SKUs, Cache for Redis, Front Door | Compute classes, Memorystore, Cloud CDN |
| **Cost Optimization** | Cost Explorer, Savings Plans, Spot | Cost Mgmt, Reservations, Spot | Billing, CUDs, Spot VMs |
| **Sustainability** | Customer Carbon Footprint Tool | Emissions Impact Dashboard | Carbon Footprint |

Use it as a review checklist, not a manifesto.

## 2. Account / Subscription / Project Hierarchy

| Cloud | Top → Leaf |
| :--- | :--- |
| **AWS** | Organization → OU → **Account** → Region → VPC |
| **Azure** | Tenant → Management Group → **Subscription** → Resource Group → Resource |
| **GCP** | Organization → Folder → **Project** → Resource |

The **billing/blast-radius unit** is Account / Subscription / Project. Separate prod, non-prod, sandbox, audit, security tooling at this level — IAM blast radius is bounded by the unit, not by tags.

## 3. Identity & Access

### 3.1 AWS
*   **IAM** (per account): users, groups, roles, policies (JSON, deny by default).
*   **IAM Identity Center** (org-wide SSO; replaces AWS SSO).
*   **STS** for temporary creds (`AssumeRole`, OIDC web identity).
*   **SCPs** at OU/account level — guardrails that override IAM.

### 3.2 Azure
*   **Entra ID** (formerly Azure AD) — identity plane.
*   **Azure RBAC** — role assignments at scope (MG / Sub / RG / Resource), inheritance downward.
*   **Managed Identities** for workloads (system-assigned, user-assigned).
*   **Conditional Access** for human MFA/posture rules.

### 3.3 GCP
*   **Cloud IAM** — bindings of (member, role, resource).
*   **Hierarchical inheritance:** Org → Folder → Project → Resource. Deny policies are explicit.
*   **Workload Identity Federation** for OIDC into GCP.
*   **VPC Service Controls** — perimeter around services to block exfiltration.

Across all three: principle of least privilege, no static long-lived keys (use OIDC/federation), MFA mandatory for humans.

## 4. Networking

### 4.1 Building Blocks
| AWS | Azure | GCP |
| :--- | :--- | :--- |
| VPC | VNet | VPC (global!) |
| Subnet (zonal) | Subnet (regional) | Subnet (regional) |
| Internet Gateway | Public IP + Route | Cloud Router + Cloud NAT |
| NAT Gateway | Azure NAT | Cloud NAT |
| Security Group + NACL | NSG | VPC Firewall Rules |
| TGW | vWAN | Network Connectivity Center |
| VPC Peering | VNet Peering | VPC Peering |
| PrivateLink | Private Endpoint | Private Service Connect |
| Direct Connect | ExpressRoute | Cloud Interconnect |

### 4.2 Patterns
*   **Hub-and-spoke** with TGW/vWAN/NCC for many VPCs/VNets — central inspection & shared services.
*   **PrivateLink / Private Endpoint / PSC** — consume managed services without traversing the public internet.
*   **Egress control:** centralized NAT + DNS firewall + outbound proxy → block C2, enforce allowlists.
*   GCP's VPC is **global**: subnets are regional but the VPC spans regions; AWS/Azure VPC/VNet are regional — multi-region requires peering or transit.

## 5. Compute Spectrum

From most operational burden to least:

```
Bare metal → VM → Container (managed K8s) → Container (serverless) → Function → SaaS
```

| Layer | AWS | Azure | GCP |
| :--- | :--- | :--- | :--- |
| VM | EC2 | Virtual Machines | Compute Engine |
| K8s managed | EKS | AKS | GKE (Standard/Autopilot) |
| Container serverless | Fargate, App Runner | Container Apps | Cloud Run |
| Function | Lambda | Functions | Cloud Functions / Run Functions |
| Batch | AWS Batch | Batch | Batch |

Cost vs. control: serverless wins below a steady utilization threshold (~30–40%); past that, reserved VMs are cheaper.

## 6. Data Services Equivalence

| Category | AWS | Azure | GCP |
| :--- | :--- | :--- | :--- |
| Object storage | **S3** | **Blob Storage** | **GCS** |
| Block | EBS | Managed Disks | Persistent Disk / Hyperdisk |
| File | EFS, FSx | Files, NetApp Files | Filestore |
| Relational managed | RDS, Aurora | Azure SQL DB, DB for Postgres/MySQL | Cloud SQL, AlloyDB |
| Distributed SQL | — (Aurora-limited) | Cosmos DB (MongoDB API) | **Spanner** |
| Wide-column | DynamoDB | Cosmos DB (Table/Cassandra) | Bigtable |
| Document | DocumentDB | Cosmos DB (Mongo API) | Firestore |
| Cache | ElastiCache | Cache for Redis | Memorystore |
| Warehouse | Redshift | Synapse, Fabric | BigQuery |
| Streaming | Kinesis, MSK | Event Hubs | Pub/Sub |
| Search | OpenSearch | AI Search | Vertex AI Search |

Equivalence is approximate. Cosmos DB and DynamoDB share *no* consistency model; Bigtable and DynamoDB share *no* schema model. Validate before treating as drop-in.

## 7. Hybrid Cloud

*   **AWS Outposts** — AWS hardware on-prem; same APIs.
*   **Azure Arc** — projects on-prem servers/K8s into Azure RBAC, Policy, Monitor.
*   **Anthos / GKE Enterprise** — GCP control plane over K8s on-prem, AWS, Azure.
*   **Azure Stack HCI / Hub** — full Azure stack on-prem.
*   **VMware on cloud** — VMC/AVS/GCVE (lift-and-shift bridge).

Use case: latency-bound workloads, data residency, slow-migration estates.

## 8. Multi-cloud

### 8.1 The LCD Trap
"Avoid lock-in" → lowest-common-denominator code → forfeit managed services → triple the toil. Usually a net loss.

### 8.2 Honest Patterns
*   **True multi-cloud:** active across providers (rare, hard, justified for sovereignty).
*   **Cloud-portable:** Kubernetes + Postgres + S3-compatible; portable, pinned to one at a time.
*   **Best-of-breed:** primary cloud + selective service elsewhere (e.g., BigQuery from AWS shop).

Cross-cloud egress is the silent cost killer. Plan data gravity.

## 9. Landing Zones

Pre-architected, opinionated baseline for new estates.

*   **AWS Control Tower** — Org + OUs + log-archive/audit accounts + SCPs + Account Factory + CloudTrail org trail.
*   **Azure Landing Zone Accelerator** — Bicep/Terraform reference; management group hierarchy, hub VNet, policy initiatives.
*   **GCP Cloud Foundation Toolkit / Fabric** — Terraform modules: org policies, folder hierarchy, shared VPC, logging sinks.

Always deploy a landing zone *before* application accounts. Retrofitting is brutal.

## 10. FinOps Lifecycle

FinOps Foundation framing — three iterative phases:

1.  **Inform** — tagging, cost allocation, showback/chargeback dashboards, anomaly alerts.
2.  **Optimize** — rightsizing, scheduling, Savings Plans / Reservations / CUDs, Spot, storage tiering (S3 IA/Glacier, Blob Cool/Archive, GCS Nearline/Coldline).
3.  **Operate** — unit economics ($/order, $/tenant), forecast vs actual, budget owners, KPI dashboards next to perf/reliability.

Cost is a cross-cutting non-functional requirement — shared engineering responsibility, not a finance afterthought.
