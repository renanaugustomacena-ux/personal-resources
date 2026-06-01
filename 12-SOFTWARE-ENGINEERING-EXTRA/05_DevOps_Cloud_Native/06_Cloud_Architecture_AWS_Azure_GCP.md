---
corso: "SWE Masterclass"
fase: "5 — DevOps & Cloud Native"
modulo: "5.6"
titolo: "Cloud Architecture — AWS, Azure, GCP, Hybrid/Multi-cloud"
versione: "AWS Well-Architected 2025 / Azure WAF 2025 / GCP Architecture Framework 2025 / FinOps Framework 2026"
livello: "Advanced"
prerequisiti:
  - "Cloud provider fundamentals (at least one of AWS, Azure, GCP)"
  - "Networking basics (TCP/IP, DNS, TLS, subnets, routing)"
  - "Identity and access management concepts (RBAC, OIDC, federation)"
  - "Infrastructure as Code (Module 5.4)"
  - "Containers and Kubernetes basics (Modules 5.1–5.2)"
obiettivi:
  - "Apply the six pillars of the Well-Architected Framework to evaluate and remediate a production workload"
  - "Design a multi-region, active-active architecture with global load balancing, data replication, and failover automation"
  - "Map equivalent compute, storage, networking, and identity services across AWS, Azure, and GCP for informed selection"
  - "Implement a FinOps practice covering tagging, showback, rightsizing, commitment discounts, and unit economics"
  - "Deploy a Landing Zone (Control Tower / Azure Accelerator / GCP Fabric) with account hierarchy, SCPs, and centralized logging"
tag: [cloud-architecture, aws, azure, gcp, well-architected, multi-region, hybrid-cloud, finops, landing-zone, iam, networking, cost-optimization]
---

# Module 5.6: Cloud Architecture — AWS, Azure, GCP, Hybrid/Multi-cloud

> **Learning Objectives**
> After completing this module you will be able to:
> 1. Apply the six pillars of the Well-Architected Framework to evaluate and remediate a production workload.
> 2. Design a multi-region, active-active architecture with global load balancing, data replication, and failover automation.
> 3. Map equivalent compute, storage, networking, and identity services across AWS, Azure, and GCP for informed selection.
> 4. Implement a FinOps practice covering tagging, showback, rightsizing, commitment discounts, and unit economics.
> 5. Deploy a Landing Zone (Control Tower / Azure Accelerator / GCP Fabric) with account hierarchy, SCPs, and centralized logging.

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

## Exercises

1. **Multi-Region Active-Active Web Application**
   Design and diagram (architecture diagram + data-flow) a multi-region web application on AWS (or Azure/GCP equivalent) with: (a) Route 53 latency-based routing (or Traffic Manager / Cloud DNS) across two regions, (b) Aurora Global Database (or Cosmos DB multi-region / Spanner) with write-forwarding, (c) S3 cross-region replication for static assets, (d) CloudFront (or Front Door / Cloud CDN) for edge caching, (e) automated failover runbook that promotes the secondary region within a target RTO of < 5 minutes. Document the RPO and RTO trade-offs for each data tier. Estimate monthly cost delta vs single-region.

2. **FinOps Cost Optimization Audit**
   Take an existing AWS (or Azure/GCP) account and perform a cost optimization audit: (a) enforce a tagging policy requiring `Environment`, `Team`, and `CostCenter` on all taggable resources (use AWS Config rules / Azure Policy / GCP Organization Policy), (b) generate a showback report per team using Cost Explorer (or Cost Management / Billing), (c) identify the top 5 rightsizing opportunities using AWS Compute Optimizer (or Azure Advisor / GCP Recommender), (d) calculate savings from converting the top 3 steady-state workloads to Savings Plans or Committed Use Discounts, (e) implement S3 Intelligent-Tiering (or equivalent) on buckets with mixed access patterns. Present findings as a cost-reduction proposal with projected annualized savings.

3. **Landing Zone Deployment with Terraform**
   Deploy an AWS Control Tower landing zone (or Azure Landing Zone Accelerator / GCP Cloud Foundation Toolkit) using Terraform/OpenTofu: (a) create an Organization with OUs for `Prod`, `NonProd`, `Sandbox`, and `Security`, (b) provision a log-archive account with centralized CloudTrail and Config aggregation, (c) apply SCPs that deny `s3:PutBucketPublicAccess`, deny root user actions, and restrict to allowed regions, (d) set up a hub VPC with Transit Gateway (or vWAN / NCC) for shared services. Verify that a new workload account inherits all guardrails. Document the account vending process.

4. **Well-Architected Review Simulation**
   Select a production workload (or a reference architecture) and conduct a Well-Architected Review against all six pillars. For each pillar: (a) list 3 current strengths, (b) identify 2 high-risk items (HRIs), (c) propose remediation with effort estimate. Use the AWS Well-Architected Tool (or equivalent) to generate a formal report. Prioritize HRIs by blast radius and create a remediation backlog in Jira or GitHub Issues with severity labels.

5. **Hybrid Connectivity and Private Service Access**
   Design a hybrid architecture connecting an on-premises data center to a cloud VPC: (a) provision a Direct Connect / ExpressRoute / Cloud Interconnect link with a backup VPN tunnel, (b) configure Private Link / Private Endpoint / Private Service Connect so that managed services (RDS, Azure SQL, Cloud SQL) are reachable from on-prem without traversing the public internet, (c) set up DNS resolution (Route 53 Resolver / Azure Private DNS Zones / Cloud DNS forwarding) for split-horizon between cloud and on-prem names, (d) implement egress controls via centralized NAT + DNS firewall. Test end-to-end connectivity and measure latency.

## Readings and References

### Books

*   AWS — *AWS Well-Architected Framework (official whitepaper, continuously updated)*. — [aws.amazon.com/architecture/well-architected](https://aws.amazon.com/architecture/well-architected/) (retrieved: 2026-05-29)
*   Beyer, B. et al. — *Site Reliability Engineering: How Google Runs Production Systems* (O'Reilly, 2016). Chapters on service reliability, capacity planning. — [sre.google/sre-book](https://sre.google/sre-book/table-of-contents/) (retrieved: 2026-05-29)
*   Wittig, M.; Wittig, A. — *Amazon Web Services in Action*, 3rd ed. (Manning, 2023). Covers core AWS services with hands-on examples.
*   Burns, B. — *Designing Distributed Systems* (O'Reilly, 2018). Patterns for containerized and cloud-native architectures.

### Official Documentation

*   FinOps Foundation — *FinOps Framework 2026*. — [finops.org/insights/2026-finops-framework](https://www.finops.org/insights/2026-finops-framework/) (retrieved: 2026-05-29)
*   Azure — *Well-Architected Framework*. — [learn.microsoft.com/azure/well-architected](https://learn.microsoft.com/en-us/azure/well-architected/) (retrieved: 2026-05-29)
*   GCP — *Google Cloud Architecture Framework*. — [cloud.google.com/architecture/framework](https://cloud.google.com/architecture/framework) (retrieved: 2026-05-29)

### Articles and Guides

*   Tech Insider — *AWS vs Azure vs Google Cloud 2026 [Compared]*. — [tech-insider.org](https://tech-insider.org/aws-vs-azure-vs-google-cloud-2026/) (retrieved: 2026-05-29)
*   Cloud4C — *Well Architecture Framework | Azure, AWS, GCP, OCI*. — [cloud4c.com](https://www.cloud4c.com/blogs/why-well-architected-frameworks-matter-in-cloud-adoption) (retrieved: 2026-05-29)
*   FinOps Foundation — *State of FinOps 2026 Report*. — [data.finops.org](https://data.finops.org/) (retrieved: 2026-05-29)
*   Flexera — *6 FinOps Principles for Cloud Cost Optimization (2026)*. — [flexera.com](https://www.flexera.com/blog/finops/finops-principles/) (retrieved: 2026-05-29)

## Cross-References

| Topic | Module | Link |
| :--- | :--- | :--- |
| Container internals (cgroups, namespaces, OCI) | 5.1 | [01_Container_Internals.md](01_Container_Internals.md) |
| Kubernetes architecture and workloads | 5.2 | [02_Kubernetes_Architecture.md](02_Kubernetes_Architecture.md) |
| Site Reliability Engineering (error budgets, toil, incident response) | 5.3 | [03_Site_Reliability_Engineering.md](03_Site_Reliability_Engineering.md) |
| Infrastructure as Code — Terraform, Pulumi, Ansible | 5.4 | [04_Infrastructure_as_Code.md](04_Infrastructure_as_Code.md) |
| Observability, SLI/SLO/SLA, and burn-rate alerts | 5.5 | [05_Observability_SLI_SLO_SLA.md](05_Observability_SLI_SLO_SLA.md) |
| Architecture patterns and system design | — | [../../02_Architecture_Design/](../../02_Architecture_Design/) |

## Glossary

| Term | Definition |
| :--- | :--- |
| **Well-Architected Framework** | A structured set of pillars (operational excellence, security, reliability, performance, cost, sustainability) for evaluating cloud workloads. |
| **Landing Zone** | Pre-architected, opinionated baseline (account hierarchy, networking, guardrails, logging) deployed before any application workload. |
| **SCP (Service Control Policy)** | AWS Organizations guardrail that sets maximum permission boundaries across all accounts in an OU, overriding individual IAM policies. |
| **FinOps** | A cloud financial management discipline combining engineering, finance, and business to drive unit-economic accountability for cloud spend. |
| **Savings Plan / CUD** | Commitment-based discount (AWS Savings Plans, GCP Committed Use Discounts, Azure Reservations) trading flexibility for 30–60% cost reduction. |
| **Blast-radius unit** | The organizational boundary (AWS Account / Azure Subscription / GCP Project) that limits the impact of IAM misconfigurations or runaway resources. |
| **Hub-and-spoke** | Network topology where a central hub VPC/VNet provides shared services (firewall, DNS, transit) and spoke VPCs/VNets connect to it. |
| **Private Link / Private Endpoint / PSC** | Service that exposes managed cloud resources over a private IP within the consumer's VPC, avoiding public internet traversal. |
| **OIDC Federation** | Authentication pattern where a CI/CD runner or external identity provider exchanges a JWT for short-lived cloud credentials. |
| **Data gravity** | The principle that large datasets attract compute and applications; moving data across clouds or regions incurs egress cost and latency. |
| **Rightsizing** | The practice of matching instance type, storage tier, or service SKU to actual workload utilization to eliminate waste. |
| **Multi-region active-active** | Architecture where two or more regions serve production traffic simultaneously, with data replication and automated failover. |
| **Egress** | Outbound network traffic from a cloud provider; typically metered and charged, especially cross-region and cross-cloud. |
| **Showback / Chargeback** | FinOps reporting mechanisms: showback surfaces cost per team for awareness; chargeback allocates actual cost to team budgets. |
